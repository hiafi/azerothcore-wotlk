/*
 * mod-dungeon-bosses, Scarlet Monastery: the hard mode item effects of Bloodmage Thalnos, Arcanist Doan, Herod and High
 * Inquisitor Whitemane (designer text: docs/dungeons/scarlet-monastery-rework.md ## Loot, "Hard mode lists"). The
 * spells are apps/dbc-tools/source/items/scarlet_monastery_hard_mode_effects.py; every damage, healing and absorb
 * number comes from potency or from the spell data, so nothing here sizes a hit. The scaled effects (scale="budget")
 * carry their own copies on every tier above 71, bound to the same scripts, so a script never casts a family spell by
 * its base id: ItemSpellCopies::Resolve (the generated ItemSpellCopies.h) gives the copy in the tier of the spell or
 * aura it runs for, and the base id on the 71 tier. The Shard of the Phylactery, the Garrison Bulwark and Treads of
 * Denial are spell data alone. Area payouts hit every enemy in reach, in combat or not (designer ruling B8, 2026-11-20:
 * every area here is short, 5 to 8 yd; only a long reach of about 30 yd would keep an in-combat filter).
 *
 *   spell_sm_pureblood_rallying_standard  212000 Pureblood's Rallying Standard (Use, and its tier copies). Plants
 *                                         Galvar's banner (300880) at the wearer's feet; at once and every second,
 *                                         each party member within the aura's radius of the banner gets the tier's
 *                                         212001 (Rallied), unless they carry another wearer's 212002 (Recently
 *                                         Rallied, one spell for every tier); one without any 212002 gets it from
 *                                         this wearer first. The banner and the Rallied buffs leave with the aura.
 *   spell_sm_one_roll_per_cast            212003, 212005, 212008, 212010, 212012, 212016 (the cast-triggered
 *                                         PROC_TRIGGER_SPELL auras and their tier copies). The proc check lets each
 *                                         cast reach the spell_proc roll once: an area spell's later targets are
 *                                         refused (Systems.md section 5, "A cast rolls once").
 *   spell_sm_fathers_verdict              212018 Father's Verdict (Equip). On a proc (one roll per cast) the tier's
 *                                         212019 hits the target, then the nearest other enemies within the aura's
 *                                         radius in the wearer's front half (in combat or not), up to the aura's
 *                                         amount.
 *   spell_sm_inquisitors_rosary           212022 Inquisitor's Rosary (Equip). A landed direct heal on another player
 *                                         who was below the aura's amount in percent health before it (one roll per
 *                                         cast) puts 212023 on the healer and on the healed player.
 *
 * Every effect logs one DEBUG line, "sm-items <effect> ...", in module.dungeonbosses.
 */

#include "Creature.h"
#include "GameTime.h"
#include "Group.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "CellImpl.h"
#include "ItemSpellCopies.h"
#include "Log.h"
#include "Player.h"
#include "ScarletMonasteryHardModeItemsLogic.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <list>
#include <vector>

using namespace ScarletMonasteryHardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    // The spell `baseId` for the tier of the spell or aura `spellInfo` (itself one of the declared spells or a copy).
    uint32 TierSpell(SpellInfo const* spellInfo, uint32 baseId)
    {
        return ItemSpellCopies::Resolve(spellInfo->Id, baseId);
    }

    // Every living enemy `attacker` may hit within `radius` yards of `center`, in combat or not (designer ruling B8,
    // 2026-11-20: a short-range area hits everyone in it).
    std::list<Unit*> EnemiesNear(WorldObject* center, Unit* attacker, float radius)
    {
        std::list<Unit*> found;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(center, attacker, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(center, found, check);
        Cell::VisitObjects(center, searcher, radius);
        found.remove_if([attacker](Unit* unit)
        {
            return !unit->IsAlive() || !attacker->IsValidAttackTarget(unit);
        });
        return found;
    }

    // The banners `wearer` planted (normally one: the Use's cooldown outlasts it).
    std::list<Creature*> OwnBanners(Unit* wearer)
    {
        std::list<Creature*> found;
        wearer->GetCreatureListWithEntryInGrid(found, NPC_RALLYING_STANDARD, kLookSearchRange);
        uint64 const wearerGuid = wearer->GetGUID().GetRawValue();
        found.remove_if([wearerGuid](Creature* creature)
        {
            TempSummon const* summon = creature->ToTempSummon();
            return !creature->IsAlive() || !summon || !IsOwnLook(summon->GetSummonerGUID().GetRawValue(), wearerGuid);
        });
        return found;
    }

    void DismissOwnBanners(Unit* wearer)
    {
        for (Creature* banner : OwnBanners(wearer))
            banner->DespawnOrUnsummon();
    }

    // The wearer's party (its subgroup; the wearer alone without a group), on the wearer's map only.
    std::vector<Player*> PartyMembers(Player* wearer)
    {
        std::vector<Player*> members;
        if (Group* group = wearer->GetGroup())
        {
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
            {
                Player* member = ref->GetSource();
                if (member && member->IsInWorld() && member->GetMap() == wearer->GetMap()
                    && wearer->IsInSameGroupWith(member))
                    members.push_back(member);
            }
        }
        else
            members.push_back(wearer);
        return members;
    }

    bool IsHittableEnemy(Unit* wearer, Unit* victim)
    {
        return wearer && victim && victim != wearer && victim->IsAlive() && wearer->IsValidAttackTarget(victim);
    }

    // One roll per cast: true the first time a cast reaches the check, false for its later targets. An event without
    // a spell (an auto attack) always rolls.
    bool FirstRollOfCast(CastStamp& rolled, ProcEventInfo& eventInfo)
    {
        Spell const* spell = eventInfo.GetProcSpell();
        if (!spell)
            return true;
        CastStamp const now{ spell, spell->GetSpellInfo()->Id, spell->m_cast_count,
            CastMoment(spell->GetDelayStart(), static_cast<std::uint64_t>(GameTime::GetGameTimeMS().count())) };
        if (SameCast(rolled, now))
            return false;
        rolled = now;
        return true;
    }
}

// 212000 Pureblood's Rallying Standard (and its tier copies): plant the banner; rally the party near it every second
// with the tier's Rallied (its percent grows with the tier). Recently Rallied is one spell for every tier, so any
// standard's lockout blocks every other.
class spell_sm_pureblood_rallying_standard : public AuraScript
{
    PrepareAuraScript(spell_sm_pureblood_rallying_standard);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_RALLIED), SPELL_RECENTLY_RALLIED });
    }

    void HandleApply(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        Unit* wearer = GetTarget();
        if (!wearer->IsAlive())
            return;

        DismissOwnBanners(wearer);
        if (TempSummon* banner = wearer->SummonCreature(NPC_RALLYING_STANDARD, wearer->GetPosition(),
            TEMPSUMMON_TIMED_DESPAWN, kStandardStayMs))
        {
            banner->SetReactState(REACT_PASSIVE);
            banner->AttackStop();
            banner->SetControlled(true, UNIT_STATE_ROOT);
        }
        LOG_DEBUG(kLog, "sm-items standard {} planted a banner", wearer->GetGUID().ToString());
        Rally(aurEff);
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Rally(aurEff);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* wearer = GetTarget();
        DismissOwnBanners(wearer);
        uint32 const ralliedId = TierSpell(GetSpellInfo(), SPELL_RALLIED);
        if (Player* player = wearer->ToPlayer())
            for (Player* member : PartyMembers(player))
                member->RemoveAurasDueToSpell(ralliedId, wearer->GetGUID());
    }

    void Rally(AuraEffect const* /*aurEff*/)
    {
        Player* wearer = GetTarget()->ToPlayer();
        if (!wearer || !wearer->IsAlive())
            return;

        std::list<Creature*> banners = OwnBanners(wearer);
        if (banners.empty())
            return;

        Creature* banner = banners.front();
        uint32 const ralliedId = TierSpell(GetSpellInfo(), SPELL_RALLIED);
        float const radius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(wearer);
        uint64 const wearerGuid = wearer->GetGUID().GetRawValue();
        uint32 rallied = 0;
        for (Player* member : PartyMembers(wearer))
        {
            if (!member->IsAlive() || !banner->IsWithinDistInMap(member, radius))
                continue;

            // Any wearer's lockout: the one this player got first decides which standard may rally them.
            Aura const* lockout = member->GetAura(SPELL_RECENTLY_RALLIED);
            if (!CanRally(lockout != nullptr, lockout ? lockout->GetCasterGUID().GetRawValue() : 0, wearerGuid))
                continue;

            if (!lockout)
                wearer->AddAura(SPELL_RECENTLY_RALLIED, member);
            wearer->AddAura(ralliedId, member);
            ++rallied;
        }
        LOG_DEBUG(kLog, "sm-items standard {} rallied {}", wearer->GetGUID().ToString(), rallied);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_sm_pureblood_rallying_standard::HandleApply, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sm_pureblood_rallying_standard::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sm_pureblood_rallying_standard::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 212003, 212005, 212008, 212010, 212012, 212016: one roll per cast. The engine runs this check before it rolls the
// spell_proc chance, so refusing a cast's later targets leaves exactly one roll per cast; the PROC_TRIGGER_SPELL aura's
// own default action casts the payout.
class spell_sm_one_roll_per_cast : public AuraScript
{
    PrepareAuraScript(spell_sm_one_roll_per_cast);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* target = eventInfo.GetActionTarget();
        if (!target || !target->IsAlive())
            return false;
        return FirstRollOfCast(_rolled, eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sm_one_roll_per_cast::CheckProc);
    }

    CastStamp _rolled;
};

// 212018 Father's Verdict: a Holy cleave on the target and the nearest other enemies in front (in combat or not).
class spell_sm_fathers_verdict : public AuraScript
{
    PrepareAuraScript(spell_sm_fathers_verdict);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_VERDICT) });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!IsHittableEnemy(GetTarget(), eventInfo.GetActionTarget()))
            return false;
        return FirstRollOfCast(_rolled, eventInfo);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        if (!wearer || !victim || !wearer->IsAlive())
            return;

        uint32 const verdictId = TierSpell(GetSpellInfo(), SPELL_VERDICT);
        wearer->CastSpell(victim, verdictId, true, nullptr, aurEff);

        float const radius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(wearer);
        std::vector<Unit*> others;
        for (Unit* enemy : EnemiesNear(wearer, wearer, radius))
            if (enemy != victim && wearer->HasInArc(kVerdictArc, enemy))
                others.push_back(enemy);
        std::sort(others.begin(), others.end(), [wearer](Unit const* a, Unit const* b)
        {
            return wearer->GetExactDist2dSq(a) < wearer->GetExactDist2dSq(b);
        });

        uint32 const extra = VerdictExtraTargets(aurEff->GetAmount(), uint32(others.size()));
        for (uint32 i = 0; i < extra; ++i)
            wearer->CastSpell(others[i], verdictId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "sm-items verdict {} ({}) on {}: {} more, {}", wearer->GetGUID().ToString(), GetId(),
            victim->GetGUID().ToString(), extra, verdictId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sm_fathers_verdict::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_sm_fathers_verdict::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    CastStamp _rolled;
};

// 212022 Inquisitor's Rosary: a heal on an ally below the threshold may raise the Versatility of both.
class spell_sm_inquisitors_rosary : public AuraScript
{
    PrepareAuraScript(spell_sm_inquisitors_rosary);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_INQUISITORS_RESOLVE });
    }

    // A landed direct heal (spell_proc: heal type, hit phase) on another living player who was below the threshold
    // before it; the check runs before the roll, so only those heals roll, once per cast.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo const* heal = eventInfo.GetHealInfo();
        Unit* healed = eventInfo.GetActionTarget();
        AuraEffect const* threshold = GetEffect(EFFECT_0);
        if (!heal || !heal->GetSpellInfo() || !healed || !threshold || !GetTarget()->IsPlayer())
            return false;
        if (!healed->IsPlayer() || healed == GetTarget() || !healed->IsAlive())
            return false;
        if (!BelowThresholdBeforeHeal(healed->GetHealth(), heal->GetEffectiveHeal(), healed->GetMaxHealth(),
                threshold->GetAmount()))
            return false;
        return FirstRollOfCast(_rolled, eventInfo);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* healer = GetTarget();
        Unit* healed = eventInfo.GetActionTarget();
        if (!healer->IsAlive() || !healed)
            return;

        healer->CastSpell(healer, SPELL_INQUISITORS_RESOLVE, true, nullptr, aurEff);
        healer->CastSpell(healed, SPELL_INQUISITORS_RESOLVE, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "sm-items rosary {} healed {}: Inquisitor's Resolve on both", healer->GetGUID().ToString(),
            healed->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sm_inquisitors_rosary::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_sm_inquisitors_rosary::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    CastStamp _rolled;
};

void AddSC_sm_hard_mode_items()
{
    RegisterSpellScript(spell_sm_pureblood_rallying_standard);
    RegisterSpellScript(spell_sm_one_roll_per_cast);
    RegisterSpellScript(spell_sm_fathers_verdict);
    RegisterSpellScript(spell_sm_inquisitors_rosary);
}
