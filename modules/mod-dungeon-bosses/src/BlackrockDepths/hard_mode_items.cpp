/*
 * mod-dungeon-bosses, Blackrock Depths: the hard mode item effects of the Ring of Law Encore, Lord Incendius, Golem
 * Lord Argelmach and Emperor Dagran Thaurissan (wave 2 dungeon items; designer text: docs/dungeons/
 * blackrock-depths-rework.md ## Loot, "Hard mode lists"). The spells are
 * apps/dbc-tools/source/items/blackrock_depths_hard_mode_effects.py; every damage and healing number comes from
 * potency or from the spell data, so nothing here sizes a hit. The scaled effects (scale="budget") carry their own
 * copies on every tier above 71, bound to the same scripts, so a script never casts a family spell by its base id:
 * ItemSpellCopies::Resolve (the generated ItemSpellCopies.h) gives the copy in the tier of the spell or aura it runs
 * for, and the base id on the 71 tier. Lefty's Shiv, the Black Anvil Bulwark and the Fist of the Lake Lord are spell
 * data alone (PROC_TRIGGER_SPELL auras).
 *
 *   BrdExecutionerDamage (UnitScript)      206830 Theldren's Executioner (Equip). The wearer's auto attacks and
 *                                          melee-class spell hits on a target below the aura's threshold (effect 2)
 *                                          grow by its percent (effect 1).
 *   spell_brd_korvs_spirit_fetish          206833 Korv's Spirit Fetish (Equip). On a landed direct heal (spell_proc:
 *                                          20%) the most injured other group member within the aura's radius of the
 *                                          healed target gets 206834 for the aura's amount in percent of the heal.
 *   spell_brd_scepter_of_the_molten_lake   206839 Scepter of the Molten Lake (Equip). On a proc the Lava Spawn
 *                                          (300655) appears beside the wearer and follows it; the wearer gets the
 *                                          tier's 206840.
 *   spell_brd_lava_spawn                   206840 Lava Spawn (the buff). Every 2 sec the Spawn faces the wearer's
 *                                          target (selected, else attacked) and plays its cast, and the wearer's
 *                                          triggered 206841 (the tier's) hits it; the Spawn leaves with the buff.
 *   spell_brd_prototype_power_core         206842 Prototype Power Core (Use). Every 2 sec each orb (the aura's amount)
 *                                          strikes an enemy in combat within the radius with the tier's 206843,
 *                                          different enemies while there are enough.
 *   spell_brd_golemwrights_mending_rod     206844 Golemwright's Mending Rod (Equip). On a proc the Mending Servo
 *                                          (300656) deploys at the healed target; the healer gets the tier's 206845.
 *   spell_brd_mending_servo                206845 Mending Servo (the buff). Every 2 sec the most injured group member
 *                                          within the radius of the Servo gets the tier's 206846 from the healer; the
 *                                          Servo leaves with the buff.
 *   spell_brd_electrons_lethal_coil        206847 Electron's Lethal Coil (Equip). A landed hit on a target the wearer
 *                                          charged removes the charge and the tier's 206849 hits every other enemy in
 *                                          combat within the radius of it; any other hit rolls the aura's chance to
 *                                          charge the target with the tier's 206848.
 *   spell_brd_volcanic_heartstone          206850 Volcanic Heartstone (Use). When the stone ends any way but death the
 *                                          wearer casts the tier's 206851.
 *   spell_brd_orb_of_the_sorcerer_thane    206852 Orb of the Sorcerer-Thane (Equip). On a proc the target and every
 *                                          other enemy in combat on the line from the wearer to it (the aura's radius
 *                                          is half the beam's width) take the tier's 206853.
 *
 * Area effects a script aims pick enemies already in combat only (a bonus never pulls a pack; the Haunted set's rule).
 * Every effect logs one DEBUG line, "brd-items <effect> ...", in module.dungeonbosses.
 */

#include "BlackrockDepthsHardModeItemsLogic.h"
#include "CellImpl.h"
#include "Containers.h"
#include "Creature.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "ItemSpellCopies.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <list>
#include <vector>

using namespace BlackrockDepthsHardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    // The spell `baseId` for the tier of the spell or aura `spellInfo` (itself one of the declared spells or a copy).
    uint32 TierSpell(SpellInfo const* spellInfo, uint32 baseId)
    {
        return ItemSpellCopies::Resolve(spellInfo->Id, baseId);
    }

    // Every living enemy of `attacker` within `radius` yards of `center`.
    std::list<Unit*> EnemiesNear(WorldObject* center, Unit* attacker, float radius)
    {
        std::list<Unit*> found;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(center, attacker, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(center, found, check);
        Cell::VisitObjects(center, searcher, radius);
        found.remove_if([attacker](Unit* unit) { return !unit->IsAlive() || !attacker->IsValidAttackTarget(unit); });
        return found;
    }

    // The same, in combat only: a bonus never pulls a pack.
    std::list<Unit*> EngagedEnemiesNear(WorldObject* center, Unit* attacker, float radius)
    {
        std::list<Unit*> found = EnemiesNear(center, attacker, radius);
        found.remove_if([](Unit* unit) { return !unit->IsInCombat(); });
        return found;
    }

    // The looks of `entry` that `wearer` summoned (normally one: the proc's cooldown outlasts it).
    std::list<Creature*> OwnLooks(Unit* wearer, uint32 entry)
    {
        std::list<Creature*> found;
        wearer->GetCreatureListWithEntryInGrid(found, entry, kLookSearchRange);
        uint64 const wearerGuid = wearer->GetGUID().GetRawValue();
        found.remove_if([wearerGuid](Creature* creature)
        {
            TempSummon const* summon = creature->ToTempSummon();
            return !creature->IsAlive() || !summon || !IsOwnLook(summon->GetSummonerGUID().GetRawValue(), wearerGuid);
        });
        return found;
    }

    void DismissOwnLooks(Unit* wearer, uint32 entry)
    {
        for (Creature* look : OwnLooks(wearer, entry))
            look->DespawnOrUnsummon();
    }

    // A summoned look the players never touch: passive, never attacks.
    void Calm(TempSummon* look)
    {
        look->SetReactState(REACT_PASSIVE);
        look->AttackStop();
    }

    // The wearer's group members (the wearer alone without a group) for a heal pick.
    std::vector<Player*> GroupMembers(Player* wearer)
    {
        std::vector<Player*> members;
        if (Group* group = wearer->GetGroup())
        {
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
                if (Player* member = ref->GetSource())
                    members.push_back(member);
        }
        else
            members.push_back(wearer);
        return members;
    }

    // The injured member with the lowest health fraction within `radius` of `center`, `skip` left out.
    Player* MostInjured(Player* wearer, WorldObject const* center, float radius, Unit const* skip)
    {
        Player* pick = nullptr;
        for (Player* member : GroupMembers(wearer))
        {
            if (member == skip || !member->IsInWorld() || !member->IsAlive() || member->GetMap() != center->GetMap())
                continue;
            if (!center->IsWithinDistInMap(member, radius))
                continue;
            if (!IsInjured(member->GetHealth(), member->GetMaxHealth()))
                continue;
            if (!pick || LowerHealthFraction(member->GetHealth(), member->GetMaxHealth(), pick->GetHealth(),
                    pick->GetMaxHealth()))
                pick = member;
        }
        return pick;
    }

    bool IsHittableEnemy(Unit* wearer, Unit* victim)
    {
        return wearer && victim && victim != wearer && victim->IsAlive() && wearer->IsValidAttackTarget(victim);
    }
}

// 206830 Theldren's Executioner: melee hits on a target below the threshold grow by the aura's percent.
class BrdExecutionerDamage : public UnitScript
{
public:
    BrdExecutionerDamage() : UnitScript("BrdExecutionerDamage", true, { UNITHOOK_MODIFY_MELEE_DAMAGE,
        UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN }) { }

    // Auto attacks.
    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        damage = Executed(target, attacker, damage);
    }

    // Melee-class spells (strikes); every other spell is left alone.
    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        if (damage <= 0 || !spellInfo || spellInfo->DmgClass != SPELL_DAMAGE_CLASS_MELEE)
            return;
        damage = int32(std::min<uint32>(Executed(target, attacker, uint32(damage)), 0x7FFFFFFFu));
    }

private:
    static uint32 Executed(Unit* target, Unit* attacker, uint32 damage)
    {
        if (!target || !attacker || !damage || !attacker->IsPlayer())
            return damage;
        AuraEffect const* bonus = attacker->GetAuraEffect(SPELL_THELDRENS_EXECUTIONER, EFFECT_0);
        AuraEffect const* threshold = attacker->GetAuraEffect(SPELL_THELDRENS_EXECUTIONER, EFFECT_1);
        if (!bonus || !threshold)
            return damage;
        if (!BelowHealthPct(target->GetHealth(), target->GetMaxHealth(), threshold->GetAmount()))
            return damage;
        return GrownDamage(damage, bonus->GetAmount());
    }
};

// 206833 Korv's Spirit Fetish: a landed direct heal chains half its amount to the most injured other member nearby.
class spell_brd_korvs_spirit_fetish : public AuraScript
{
    PrepareAuraScript(spell_brd_korvs_spirit_fetish);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_SPIRIT_CHAIN });
    }

    // A direct heal that landed (spell_proc: heal type, hit phase); the ticks of a heal over time are periodic events,
    // which the proc flags leave out.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo const* heal = eventInfo.GetHealInfo();
        return heal && heal->GetSpellInfo() && heal->GetHeal() > 0 && eventInfo.GetActionTarget()
            && GetTarget()->IsPlayer();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Player* healer = GetTarget()->ToPlayer();
        Unit* healed = eventInfo.GetActionTarget();
        HealInfo const* heal = eventInfo.GetHealInfo();
        if (!healer || !healed || !heal)
            return;

        int32 const amount = ShareOfHeal(heal->GetHeal(), aurEff->GetAmount());
        if (amount <= 0)
            return;

        float const radius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(healer);
        Player* chained = MostInjured(healer, healed, radius, healed);
        if (!chained)
            return;

        // Triggered by this aura: the chain never procs the Fetish again (and SUPPRESS_CASTER_PROCS).
        healer->CastCustomSpell(chained, SPELL_SPIRIT_CHAIN, &amount, nullptr, nullptr, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "brd-items fetish {} healed {} for {}: chained {} to {}", healer->GetGUID().ToString(),
            healed->GetGUID().ToString(), heal->GetHeal(), amount, chained->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_brd_korvs_spirit_fetish::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_brd_korvs_spirit_fetish::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 206839 Scepter of the Molten Lake: a damaging spell may call the Lava Spawn.
class spell_brd_scepter_of_the_molten_lake : public AuraScript
{
    PrepareAuraScript(spell_brd_scepter_of_the_molten_lake);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_LAVA_SPAWN) });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return IsHittableEnemy(GetTarget(), eventInfo.GetActionTarget());
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        if (!wearer->IsAlive())
            return;

        // One Spawn at a time (the proc's cooldown outlasts it; a leftover from a refreshed buff is dismissed).
        DismissOwnLooks(wearer, NPC_LAVA_SPAWN);
        Position const beside = wearer->GetFirstCollisionPosition(kSpawnFollowDistance, kSpawnFollowAngle);
        if (TempSummon* spawn = wearer->SummonCreature(NPC_LAVA_SPAWN, beside, TEMPSUMMON_TIMED_DESPAWN, kLookStayMs))
        {
            Calm(spawn);
            spawn->GetMotionMaster()->MoveFollow(wearer, kSpawnFollowDistance, kSpawnFollowAngle);
        }

        // This tier's buff (the declared one on the 71 tier, the tier's copy above it).
        uint32 const buffId = TierSpell(GetSpellInfo(), SPELL_LAVA_SPAWN);
        wearer->CastSpell(wearer, buffId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "brd-items scepter {} ({}) called a Lava Spawn: buff {}", wearer->GetGUID().ToString(),
            GetId(), buffId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_brd_scepter_of_the_molten_lake::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_brd_scepter_of_the_molten_lake::HandleProc, EFFECT_0,
            SPELL_AURA_DUMMY);
    }
};

// 206840 Lava Spawn: every 2 sec the Spawn hurls at the wearer's target; it leaves with the buff.
class spell_brd_lava_spawn : public AuraScript
{
    PrepareAuraScript(spell_brd_lava_spawn);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_MOLTEN_HURL) });
    }

    // The wearer's target: the selected enemy, else the one it attacks. Engaged enemies within reach only, so a
    // selected but untouched pack is never pulled.
    static Unit* HurlTarget(Unit* wearer)
    {
        auto usable = [wearer](Unit* unit)
        {
            return IsHittableEnemy(wearer, unit) && unit->IsInCombat() && wearer->IsWithinDistInMap(unit, kHurlRange);
        };
        if (Player* player = wearer->ToPlayer())
            if (Unit* selected = player->GetSelectedUnit(); usable(selected))
                return selected;
        Unit* victim = wearer->GetVictim();
        return usable(victim) ? victim : nullptr;
    }

    void HandleHurl(AuraEffect const* aurEff)
    {
        Unit* wearer = GetTarget();
        if (!wearer->IsAlive())
            return;

        std::list<Creature*> spawns = OwnLooks(wearer, NPC_LAVA_SPAWN);
        Unit* target = HurlTarget(wearer);
        if (spawns.empty() || !target)
            return;

        Creature* spawn = spawns.front();
        spawn->SetFacingToObject(target);
        spawn->HandleEmoteCommand(EMOTE_ONESHOT_SPELL_CAST_OMNI);
        uint32 const hurlId = TierSpell(GetSpellInfo(), SPELL_MOLTEN_HURL);
        wearer->CastSpell(target, hurlId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "brd-items lava spawn {} ({}) hurled at {}: {}", wearer->GetGUID().ToString(), GetId(),
            target->GetGUID().ToString(), hurlId);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        DismissOwnLooks(GetTarget(), NPC_LAVA_SPAWN);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_brd_lava_spawn::HandleHurl, EFFECT_0, SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_brd_lava_spawn::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 206842 Prototype Power Core: every 2 sec each orb strikes a nearby engaged enemy.
class spell_brd_prototype_power_core : public AuraScript
{
    PrepareAuraScript(spell_brd_prototype_power_core);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_ARCANE_ORB_STRIKE) });
    }

    void HandleOrbs(AuraEffect const* aurEff)
    {
        Unit* wearer = GetTarget();
        if (!wearer->IsAlive())
            return;

        float const radius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(wearer);
        std::list<Unit*> const near = EngagedEnemiesNear(wearer, wearer, radius);
        std::vector<Unit*> enemies(near.begin(), near.end());
        Acore::Containers::RandomShuffle(enemies);

        uint32 const strikeId = TierSpell(GetSpellInfo(), SPELL_ARCANE_ORB_STRIKE);
        int32 const orbs = aurEff->GetAmount();
        for (int32 orb = 0; orb < orbs; ++orb)
        {
            int32 const index = OrbTargetIndex(uint32(orb), uint32(enemies.size()));
            if (index < 0)
                return;
            wearer->CastSpell(enemies[index], strikeId, true, nullptr, aurEff);
        }
        LOG_DEBUG(kLog, "brd-items power core {} ({}): {} orbs on {} enemies, strike {}", wearer->GetGUID().ToString(),
            GetId(), orbs, enemies.size(), strikeId);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_brd_prototype_power_core::HandleOrbs, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 206844 Golemwright's Mending Rod: a heal may deploy the Mending Servo at the healed target.
class spell_brd_golemwrights_mending_rod : public AuraScript
{
    PrepareAuraScript(spell_brd_golemwrights_mending_rod);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_MENDING_SERVO) });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo const* heal = eventInfo.GetHealInfo();
        return heal && heal->GetHeal() > 0 && eventInfo.GetActionTarget() && GetTarget()->IsPlayer();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* healer = GetTarget();
        Unit* healed = eventInfo.GetActionTarget();
        if (!healer->IsAlive() || !healed)
            return;

        DismissOwnLooks(healer, NPC_MENDING_SERVO);
        if (TempSummon* servo = healer->SummonCreature(NPC_MENDING_SERVO, healed->GetPosition(),
            TEMPSUMMON_TIMED_DESPAWN, kLookStayMs))
        {
            Calm(servo);
            servo->SetControlled(true, UNIT_STATE_ROOT);
        }

        uint32 const buffId = TierSpell(GetSpellInfo(), SPELL_MENDING_SERVO);
        healer->CastSpell(healer, buffId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "brd-items mending rod {} ({}) deployed a Servo at {}: buff {}", healer->GetGUID().ToString(),
            GetId(), healed->GetGUID().ToString(), buffId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_brd_golemwrights_mending_rod::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_brd_golemwrights_mending_rod::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 206845 Mending Servo: every 2 sec the most injured member near the Servo is mended; the Servo leaves with the buff.
class spell_brd_mending_servo : public AuraScript
{
    PrepareAuraScript(spell_brd_mending_servo);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_SERVO_MEND) });
    }

    void HandleMend(AuraEffect const* aurEff)
    {
        Player* healer = GetTarget()->ToPlayer();
        if (!healer || !healer->IsAlive())
            return;

        std::list<Creature*> servos = OwnLooks(healer, NPC_MENDING_SERVO);
        if (servos.empty())
            return;

        Creature* servo = servos.front();
        float const radius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(healer);
        Player* patient = MostInjured(healer, servo, radius, nullptr);
        if (!patient)
            return;

        servo->SetFacingToObject(patient);
        servo->HandleEmoteCommand(EMOTE_ONESHOT_SPELL_CAST_OMNI);
        uint32 const mendId = TierSpell(GetSpellInfo(), SPELL_SERVO_MEND);
        healer->CastSpell(patient, mendId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "brd-items servo {} ({}) mended {}: {}", healer->GetGUID().ToString(), GetId(),
            patient->GetGUID().ToString(), mendId);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        DismissOwnLooks(GetTarget(), NPC_MENDING_SERVO);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_brd_mending_servo::HandleMend, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_brd_mending_servo::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 206847 Electron's Lethal Coil: charge a target, then the next hit on it arcs to the enemies around it.
class spell_brd_electrons_lethal_coil : public AuraScript
{
    PrepareAuraScript(spell_brd_electrons_lethal_coil);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_LETHAL_ATTRACTION),
            TierSpell(spellInfo, SPELL_LETHAL_ARC) });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return IsHittableEnemy(GetTarget(), eventInfo.GetActionTarget());
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        if (!wearer || !victim)
            return;

        uint32 const attractionId = TierSpell(GetSpellInfo(), SPELL_LETHAL_ATTRACTION);
        if (victim->HasAura(attractionId, wearer->GetGUID()))
        {
            // The charge was put on by an earlier hit (this handler charges only after this check): detonate it.
            victim->RemoveAurasDueToSpell(attractionId, wearer->GetGUID());
            uint32 const arcId = TierSpell(GetSpellInfo(), SPELL_LETHAL_ARC);
            float const radius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(wearer);
            uint32 arcs = 0;
            for (Unit* enemy : EngagedEnemiesNear(victim, wearer, radius))
            {
                if (enemy == victim)
                    continue;
                wearer->CastSpell(enemy, arcId, true, nullptr, aurEff);
                ++arcs;
            }
            LOG_DEBUG(kLog, "brd-items coil {} ({}) detonated on {}: {} arcs of {}", wearer->GetGUID().ToString(),
                GetId(), victim->GetGUID().ToString(), arcs, arcId);
            return;
        }

        if (!roll_chance_i(aurEff->GetAmount()))
            return;
        wearer->CastSpell(victim, attractionId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "brd-items coil {} ({}) charged {}", wearer->GetGUID().ToString(), GetId(),
            victim->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_brd_electrons_lethal_coil::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_brd_electrons_lethal_coil::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 206850 Volcanic Heartstone: when the stone ends (not by death) it bursts.
class spell_brd_volcanic_heartstone : public AuraScript
{
    PrepareAuraScript(spell_brd_volcanic_heartstone);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_HEARTSTONE_ERUPTION) });
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* wearer = GetTarget();
        AuraApplication const* application = GetTargetApplication();
        if (!wearer || !wearer->IsAlive() || !application || application->GetRemoveMode() == AURA_REMOVE_BY_DEATH)
            return;

        uint32 const eruptionId = TierSpell(GetSpellInfo(), SPELL_HEARTSTONE_ERUPTION);
        wearer->CastSpell(wearer, eruptionId, true);
        LOG_DEBUG(kLog, "brd-items heartstone {} ({}) burst: {}", wearer->GetGUID().ToString(), GetId(), eruptionId);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_brd_volcanic_heartstone::HandleRemove, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_EFFECT_HANDLE_REAL);
    }
};

// 206852 Orb of the Sorcerer-Thane: a shadow beam hits the target and every engaged enemy on the line to it.
class spell_brd_orb_of_the_sorcerer_thane : public AuraScript
{
    PrepareAuraScript(spell_brd_orb_of_the_sorcerer_thane);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_SHADOW_BEAM) });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return IsHittableEnemy(GetTarget(), eventInfo.GetActionTarget());
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        if (!wearer || !victim)
            return;

        uint32 const beamId = TierSpell(GetSpellInfo(), SPELL_SHADOW_BEAM);
        float const halfWidth = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(wearer);
        float const reach = wearer->GetExactDist2d(victim) + halfWidth;
        uint32 hits = 1;
        wearer->CastSpell(victim, beamId, true, nullptr, aurEff);
        for (Unit* enemy : EngagedEnemiesNear(wearer, wearer, reach))
        {
            if (enemy == victim || !OnBeam(enemy->GetPositionX(), enemy->GetPositionY(), wearer->GetPositionX(),
                    wearer->GetPositionY(), victim->GetPositionX(), victim->GetPositionY(), halfWidth))
                continue;
            wearer->CastSpell(enemy, beamId, true, nullptr, aurEff);
            ++hits;
        }
        LOG_DEBUG(kLog, "brd-items orb {} ({}) beamed at {}: {} hit, {}", wearer->GetGUID().ToString(), GetId(),
            victim->GetGUID().ToString(), hits, beamId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_brd_orb_of_the_sorcerer_thane::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_brd_orb_of_the_sorcerer_thane::HandleProc, EFFECT_0,
            SPELL_AURA_DUMMY);
    }
};

void AddSC_brd_hard_mode_items()
{
    new BrdExecutionerDamage();
    RegisterSpellScript(spell_brd_korvs_spirit_fetish);
    RegisterSpellScript(spell_brd_scepter_of_the_molten_lake);
    RegisterSpellScript(spell_brd_lava_spawn);
    RegisterSpellScript(spell_brd_prototype_power_core);
    RegisterSpellScript(spell_brd_golemwrights_mending_rod);
    RegisterSpellScript(spell_brd_mending_servo);
    RegisterSpellScript(spell_brd_electrons_lethal_coil);
    RegisterSpellScript(spell_brd_volcanic_heartstone);
    RegisterSpellScript(spell_brd_orb_of_the_sorcerer_thane);
}
