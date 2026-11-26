/*
 * mod-dungeon-bosses, Zul'Farrak D4b: Shadowpriest Sezz'ziz (7275) and Nekrum Gutchewer (7796), the Altar (stage 3 of
 * the Pyramid), normal and heroic. Build spec: SP 1346-1432 (PY12-PY16), design SP 1180-1281 (rulings 21-23, 46);
 * handoff section 3.5 row D4b and its kick and dispel table, sections 3.6, 3.8 (the plaza), section 7 #11 A, #20 A,
 * #44 A. Replaces npc_shadowpriest_sezziz (zulfarrak.cpp; the S0 rev binds this script instead) and SmartAI 7796
 * (dropped by rev_skeleton_zul_farrak.sql: Berserker Charge on aggro and Hamstring kept below, Fevered Plague retired,
 * the death's counter on Bly had no effect). Bound by apps/dbc-tools source/npcs/zul_farrak/pyramid_stair.py; numbers
 * in SezzzizLogic.h, health in ZulFarrakRework.h Health; the Pyramid-wide pieces (Grievous Wound, Offerings, Blood
 * Price) in PyramidFight.h; the stage's director (the spawn, the idle wait, the link) in pyramid_stair_rework.cpp.
 *
 * They are stage 3 of the Pyramid, not BossAIs: the instance writes slot 5 and wins the stage when both are dead. Their
 * pull sends DATA_PYRAMID_START 3 (refused while it runs), their evade while it runs DATA_PYRAMID_FAIL 3. The crew are
 * CR's: a Blood Offering kills a crew fighter only through BlyCrew.h (rule 28).
 *
 *   PY12 Blood Offering  first at 6 s, then every 15 to 18 s: emote line 0, a 3 s cast (heroic 2 s; Fire school, the
 *                        only Fire cast he has, kickable: a kick locks nothing else) on a surviving crew fighter in
 *                        reach, else a random player (tank included), the red beam (SV 7270). Landed: the member dies
 *                        (ZfCrew::KillCrew), or the player takes 25% Shadow; he heals 15% (heroic 25%) and gains Blood
 *                        Frenzy: normal +50% damage done for 15 s, heroic +50% a stack, no end, no cap.
 *   PY13 Psychic Scream  first at 10 s, then every 22 to 30 s: a 2 s bar (Physical school: his kickable Shadow Bolt
 *                        locks Shadow, rule 24) with the 8 yd circle on him; a 2 s fear (Magic) on everyone inside.
 *   PY14 adds            first at 12 s, then every 10 to 14 s: the stock four sets in turn at the stock two points
 *                        (Zealots as Berserkers, Acolytes as Hexmasters), at most 4 alive.
 *   PY15                 Sezz'ziz: Shadow Bolt 15537 every 3 to 4 s from 30 yd; Nekrum: Berserker Charge 19471 on
 *                        aggro, Hamstring 26141 every 12 to 20 s, melee.
 *   Gutchew              heroic, Nekrum every 15 s: Grievous Wound on his target (PyramidFight.h).
 *   PY3 / PY16           Offerings (normal) and Blood Price (heroic) on both, from the instance's counts (the Altar's
 *                        director tracks them when the stage starts: they arrive with every stack collected).
 *   Arena                ZfAltar::AltarArena(): the plaza, the ramp's foot and the stair, with LeashOptions.
 *
 * Every firing logs one INFO line "zf-build altar <mechanic> ..."; `.dbtest zf stair offering|scream|adds|gutchew`
 * fire one (pyramid_stair_rework.cpp, through DoAction).
 *
 * Mirrored stock code (AGENTS.md credit rule): the add sets and points of npc_shadowpriest_sezziz (zulfarrak.cpp:
 * 048025ceb UltraNix <80540499+UltraNix@users.noreply.github.com>; the points df82d1be9 jrad7
 * <106174524+jrad7@users.noreply.github.com>, #26183), re-implemented in SezzzizLogic.h.
 */

#include "ArenaGuard.h"
#include "BlyCrew.h"
#include "BossMechanics.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MechanicRegistry.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "PyramidFight.h"
#include "ScriptedCreature.h"
#include "SezzzizLogic.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StairLogic.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <string>
#include <vector>

using namespace ZulFarrakRework;
using namespace ZfAltar;
using BossMechanics::MechanicHandle;

namespace
{
    char const* const kAltarKey = "altar";
    uint8 constexpr kSchoolShadow = 5;      // SPELL_SCHOOL_SHADOW

    void AltarLog(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kAltarKey, mechanic, detail);
    }

    bool StageThreeRunning(InstanceScript const* instance)
    {
        return instance && instance->GetData(DATA_PYRAMID_STAGE) == PYRAMID_STAGE_ALTAR
            && instance->GetData(DATA_PYRAMID_RUNNING) != 0;
    }

    // An Altar unit's pull (Sezz'ziz, Nekrum): the stage starts (refused while it runs, or out of turn).
    void StartAltar(Creature* me)
    {
        if (InstanceScript* instance = me->GetInstanceScript())
        {
            instance->SetData(DATA_PYRAMID_START, PYRAMID_STAGE_ALTAR);
            ZfPyramid::ApplySandfuryBuff(me, instance);
        }
    }

    // An Altar unit evading while the stage runs loses it (the instance's wipe: the director puts the Altar back).
    void FailAltar(Creature* me, char const* who)
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!StageThreeRunning(instance))
            return;
        AltarLog("evade-fail", who);
        instance->SetData(DATA_PYRAMID_FAIL, PYRAMID_STAGE_ALTAR);
    }

    // Rule 19: an arriving add takes the tank (his victim when it is a player), else the nearest living player.
    Unit* ArrivalTarget(Creature* me, Position const& from)
    {
        if (Unit* victim = me->GetVictim())
            if (victim->IsPlayer() && victim->IsAlive())
                return victim;
        Player* nearest = nullptr;
        float best = 1.0e9f;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster())
                continue;
            float const d = player->GetExactDist2d(from.GetPositionX(), from.GetPositionY());
            if (d < best)
            {
                best = d;
                nearest = player;
            }
        }
        return nearest;
    }
}

// Shadowpriest Sezz'ziz 7275
struct boss_sezzziz_rework : public ScriptedAI
{
    explicit boss_sezzziz_rework(Creature* creature)
        : ScriptedAI(creature), _arena(AltarArena(), LeashOptions(kAltarKey)), _bounds(BoundsOf(AltarArena()))
    {
    }

    void Reset() override
    {
        Cleanup("reset", true);
    }

    void AttackStart(Unit* who) override
    {
        AttackStartCaster(who, Tune::kCasterRangeYd);
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);

        Cleanup("pull", true);      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        _boltAt = urand(Tune::kBoltFirstMinMs, Tune::kBoltFirstMaxMs);
        _offeringAt = Tune::kOfferingFirstMs;
        _screamAt = Tune::kScreamFirstMs;
        _addsAt = Tune::kAddsFirstMs;

        OnBossPull(me, kAltarKey);
        StartAltar(me);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_PYRAMID;
        Mechanic::BeginEncounter(me, options);
        Describe();
        Mechanic::NoteNextCastIn(me, OfferingSpell(), Milliseconds(Tune::kOfferingFirstMs));
        _arena.Engage(me);
        AltarLog("engage", Acore::StringFormat("unit=sezzziz heroic={} who={} crew={}", _heroic ? 1 : 0,
            who ? who->GetName() : "-", CrewAlive()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        AltarLog("evade", Acore::StringFormat("unit=sezzziz reason={}", uint32(why)));
        Cleanup("evade", true);
        ScriptedAI::EnterEvadeMode(why);
        FailAltar(me, "sezzziz");
    }

    void JustDied(Unit* /*killer*/) override
    {
        AltarLog("death", Acore::StringFormat("unit=sezzziz offerings={} frenzy={} calls={} adds={}", _offerings,
            _frenzy, _calls, AliveAdds()));
        Cleanup("death", false);    // his adds fight on (stock: they despawn only when they die)
    }

    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        _adds.push_back(summon->GetGUID());
        Mechanic::TrackUnit(me, summon);
        if (Unit* target = ArrivalTarget(me, summon->GetPosition()))
            if (summon->IsAIEnabled && summon->AI())
                summon->AI()->AttackStart(target);
    }

    // PY12: the bar finished: the Offering lands on whoever it was cast on.
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && (spell->Id == SPELL_BLOOD_OFFERING || spell->Id == SPELL_BLOOD_OFFERING_H))
            ResolveOffering();
    }

    // A kick (the reward) or anything else that ended the bar.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell || (spell->Id != SPELL_BLOOD_OFFERING && spell->Id != SPELL_BLOOD_OFFERING_H))
            return;
        AltarLog("offering-stopped", Acore::StringFormat("target={}", _offeringName));
        Beam(nullptr);
        _offeringTarget.Clear();
    }

    void DoAction(int32 action) override
    {
        if (!_engaged)
            return;
        switch (action)
        {
            case ACTION_TEST_OFFERING:
                _offeringAt = _now;
                break;
            case ACTION_TEST_SCREAM:
                _screamAt = _now;
                break;
            case ACTION_TEST_ADDS:
                _addsAt = _now;
                break;
            default:
                break;
        }
    }

    uint32 GetData(uint32 id) const override
    {
        switch (id)
        {
            case DATA_TEST_ENGAGED:
                return _engaged ? 1 : 0;
            case DATA_TEST_ADDS:
                return AliveAdds();
            case DATA_TEST_FRENZY:
                return _frenzy;
            case DATA_TEST_OFFERINGS:
                return _offerings;
            case DATA_TEST_CALLS:
                return _calls;
            default:
                return 0;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        // The fight clock moves every tick, cast bar or not (L8).
        _now += diff;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        if (_now >= _addsAt)
            SummonAdds();
        if (_now >= _screamAt && StartScream())
            return;
        if (_now >= _offeringAt && StartOffering())
            return;
        if (_now >= _boltAt && me->GetVictim())
        {
            DoCastVictim(SPELL_SHADOW_BOLT);
            _boltAt = _now + urand(Tune::kBoltMinMs, Tune::kBoltMaxMs);
            return;
        }
        DoMeleeAttackIfReady();
    }

private:
    uint32 OfferingSpell() const
    {
        return _heroic ? uint32(SPELL_BLOOD_OFFERING_H) : uint32(SPELL_BLOOD_OFFERING);
    }

    // ---- PY12 Blood Offering --------------------------------------------------------------------------------------

    bool StartOffering()
    {
        InstanceScript* instance = me->GetInstanceScript();
        Unit* target = nullptr;
        bool crew = false;
        uint32 candidates = 0;
        if (instance)
            for (uint32 m = 0; m < kCrewCount; ++m)
            {
                if (!(kCrewFighters & CrewBit(m)))
                    continue;
                ZfCrew::BlyCrewAI* ai = ZfCrew::CrewAI(instance, m);
                if (!ai || !ai->Me()->IsAlive() || ai->Mode() != CrewMode::Ally
                    || !me->IsWithinDist(ai->Me(), Tune::kOfferingRangeYd) || !me->IsWithinLOSInMap(ai->Me()))
                    continue;
                candidates |= CrewBit(m);
            }
        if (std::optional<uint32> const m = PickOfferingCrew(candidates, urand(0, 1023)))
        {
            target = ZfCrew::CrewAI(instance, *m)->Me();
            crew = true;
        }
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;
            rule.maxRange = Tune::kOfferingRangeYd;
            rule.requireLos = true;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
        {
            _offeringAt = _now + 1000;      // nobody in reach: look again in a second
            return false;
        }
        _offeringAt = _now + urand(Tune::kOfferingMinMs, Tune::kOfferingMaxMs);
        _offeringTarget = target->GetGUID();
        _offeringCrew = crew;
        _offeringName = target->GetName();
        me->StopMoving();
        Talk(EMOTE_BLOOD_OFFERING, target);
        me->CastSpell(target, OfferingSpell(), false);
        Beam(target);
        Mechanic::NoteNextCastIn(me, OfferingSpell(), Milliseconds(_offeringAt - _now));
        AltarLog("offering", Acore::StringFormat("target={} crew={} cast={} heroic={} candidates={}", _offeringName,
            crew ? 1 : 0, Tune::kOfferingCastMs.Get(_heroic), _heroic ? 1 : 0, candidates));
        return true;
    }

    // The red beam from him to the one offered while the bar runs (SV 7270 through his channel fields, as D4a's rope;
    // never cast). nullptr: off.
    void Beam(Unit* target)
    {
        me->SetGuidValue(UNIT_FIELD_CHANNEL_OBJECT, target ? target->GetGUID() : ObjectGuid::Empty);
        me->SetUInt32Value(UNIT_CHANNEL_SPELL, target ? uint32(SPELL_BLOOD_OFFERING_BEAM) : 0u);
    }

    void ResolveOffering()
    {
        Beam(nullptr);
        Unit* target = _offeringTarget.IsEmpty() ? nullptr : ObjectAccessor::GetUnit(*me, _offeringTarget);
        _offeringTarget.Clear();
        if (!target || !target->IsAlive())
        {
            AltarLog("offering-fizzled", Acore::StringFormat("target={} (gone before the bar ended)", _offeringName));
            return;
        }
        bool landed = false;
        if (_offeringCrew)
        {
            if (Creature* member = target->ToCreature())
                landed = ZfCrew::KillCrew(member, me);
        }
        else
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = Tune::kOfferingPlayerPct;
            spec.tankPct = Tune::kOfferingPlayerPct;
            spec.school = kSchoolShadow;
            spec.spellId = SPELL_BLOOD_OFFERING_HIT;
            spec.weakened = false;      // a setback, the soft penalty (SP PY12): his heal and frenzy are the cost
            spec.tag = TAG_OFFERING_HIT;
            Track(DungeonKit::RegistryHit(me, GuidSet{ target->GetGUID() }, spec));
            landed = true;
        }
        if (!landed)
        {
            AltarLog("offering-refused", Acore::StringFormat("target={}", _offeringName));
            return;
        }
        ++_offerings;
        uint32 const heal = OfferingHeal(me->GetMaxHealth(), _heroic);
        me->ModifyHealth(int32(heal));
        Frenzy();
        AltarLog("offering-landed", Acore::StringFormat("target={} crew={} heal={} health={:.0f}% frenzy={} heroic={} "
            "crewalive={}", _offeringName, _offeringCrew ? 1 : 0, heal, me->GetHealthPct(), _frenzy, _heroic ? 1 : 0,
            CrewAlive()));
    }

    // Normal: +50% for 15 s (a refresh). Heroic: one more stack for good (+50% each, the amount set on the aura as
    // Blood Price's is, so it keeps growing past the counter's 255).
    void Frenzy()
    {
        if (!_heroic)
        {
            me->CastSpell(me, SPELL_BLOOD_FRENZY, true);
            _frenzy = 1;
            return;
        }
        ++_frenzy;
        uint32 const shown = FrenzyShownStacks(_frenzy);
        uint32 const now = DungeonKit::Stacks(me, SPELL_BLOOD_FRENZY_H, me->GetGUID());
        if (shown != now)
            DungeonKit::AddStacks(me, SPELL_BLOOD_FRENZY_H, int32(shown) - int32(now), me, Tune::kFrenzyStackLimit);
        if (Aura* aura = me->GetAura(SPELL_BLOOD_FRENZY_H, me->GetGUID()))
            if (AuraEffect* effect = aura->GetEffect(EFFECT_0))
                if (effect->GetAmount() != FrenzyDamagePct(_frenzy))
                    effect->ChangeAmount(FrenzyDamagePct(_frenzy));
    }

    // ---- PY13 Psychic Scream --------------------------------------------------------------------------------------

    bool StartScream()
    {
        _screamAt = _now + urand(Tune::kScreamMinMs, Tune::kScreamMaxMs);
        me->StopMoving();
        DungeonKit::CastBar(me, SPELL_SCREAM_BAR);
        Track(Mechanic::Circle(me, me, Tune::kScreamRadiusYd, Milliseconds(Tune::kScreamCastMs))
            .Rider(SPELL_SCREAM_FEAR).School(kSchoolShadow).Within(_bounds).Tag(TAG_SCREAM));
        AltarLog("scream", Acore::StringFormat("radius={:.0f} next_in={}", Tune::kScreamRadiusYd, _screamAt - _now));
        return true;
    }

    // ---- PY14 adds ------------------------------------------------------------------------------------------------

    void SummonAdds()
    {
        _addsAt = _now + urand(Tune::kAddsMinMs, Tune::kAddsMaxMs);
        AddSet const& set = AddSetFor(_calls++);
        uint32 const alive = AliveAdds();
        uint32 const n = AddsToSummon(set.size, alive);
        for (uint32 i = 0; i < n; ++i)
        {
            Point3 const& at = kSezzzizAddPoints[set.slots[i].point];
            me->SummonCreature(set.slots[i].entry, Position(at.x, at.y, at.z, kAltarFacing),
                TEMPSUMMON_CORPSE_TIMED_DESPAWN, ZfStair::Tune::kCorpseMs);
        }
        AltarLog("adds", Acore::StringFormat("call={} set={} summoned={} alive={} cap={}", _calls, set.size, n,
            AliveAdds(), Tune::kAddsCap));
    }

    uint32 AliveAdds() const
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : _adds)
            if (Creature* add = ObjectAccessor::GetCreature(*me, guid))
                if (add->IsAlive())
                    ++n;
        return n;
    }

    // ---- helpers ---------------------------------------------------------------------------------------------------

    uint32 CrewAlive() const
    {
        InstanceScript const* instance = me->GetInstanceScript();
        return instance ? instance->GetData(DATA_CREW_ALIVE) : 0;
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // Boss data (SP "Boss data"): kicks: the Offering first (required on heroic), the Witch Doctors' Flash Heal (a
    // reward), never his Shadow Bolt (a kick there locks only Shadow, but it spends the kick the Offering needs);
    // cures: Curse of Blood and Sandfury Hex (Curse), Hexed and the Scream's fear (Magic, loss of control); kill order:
    // the Witch Doctors, the Healing Wards, the Hexmasters, the rest of his adds and the fodder, then Nekrum and him;
    // heroic: Grievous Wound carriers healed on to 95%.
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_SEZZZIZ, OfferingSpell(), uint8(_heroic ? 3 : 2),
            std::chrono::milliseconds(Tune::kOfferingMinMs));
        d.interrupts.emplace_back(NPC_ZF_SANDFURY_WITCH_DOCTOR, ZfStair::SPELL_FLASH_HEAL, uint8(1));
        d.interrupts.emplace_back(NPC_SEZZZIZ, SPELL_SHADOW_BOLT, uint8(0));
        d.dispels.emplace_back(ZfStair::SPELL_HEXED, uint8(3), true);
        d.dispels.emplace_back(SPELL_SCREAM_FEAR, uint8(2), true);
        d.dispels.emplace_back(ZfStair::SPELL_CURSE_OF_BLOOD, uint8(1));
        d.dispels.emplace_back(ZfStair::SPELL_SANDFURY_HEX, uint8(1));
        d.targets.emplace_back(NPC_ZF_SANDFURY_WITCH_DOCTOR, int8(4));
        d.targets.emplace_back(ZfStair::NPC_HEALING_WARD, int8(3));
        d.targets.emplace_back(NPC_ZF_SANDFURY_HEXMASTER, int8(2));
        d.targets.emplace_back(NPC_ZF_SANDFURY_BERSERKER, int8(1));
        d.targets.emplace_back(NPC_SANDFURY_SLAVE, int8(1));
        d.targets.emplace_back(NPC_SANDFURY_DRUDGE, int8(1));
        ZfPyramid::AddWoundHealRule(d, _heroic);
        Mechanic::Describe(me, std::move(d));
    }

    // The pull's state, gone (RB-1): every registry handle, the clocks, the Offering in flight, the frenzy, his buff;
    // with `adds`, his adds too (a reset or an evade; at his death they fight on).
    void Cleanup(char const* why, bool adds)
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (adds)
        {
            uint32 gone = 0;
            for (ObjectGuid const& guid : _adds)
                if (Creature* add = ObjectAccessor::GetCreature(*me, guid))
                    if (add->IsAlive())
                    {
                        add->DespawnOrUnsummon(Milliseconds(1));
                        ++gone;
                    }
            _adds.clear();
            if (gone)
                AltarLog("adds-gone", Acore::StringFormat("why={} count={}", why, gone));
        }
        me->RemoveAurasDueToSpell(SPELL_BLOOD_FRENZY);
        me->RemoveAurasDueToSpell(SPELL_BLOOD_FRENZY_H);
        ZfPyramid::RemoveSandfuryBuff(me);
        Beam(nullptr);
        _offeringTarget.Clear();
        _now = 0;
        _boltAt = 0;
        _offeringAt = 0;
        _screamAt = 0;
        _addsAt = 0;
        _calls = 0;
        _frenzy = 0;
        _offerings = 0;
        _engaged = false;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    BossMechanics::SpotBounds _bounds;
    std::vector<MechanicHandle> _live;
    GuidVector _adds;
    ObjectGuid _offeringTarget;
    std::string _offeringName;
    bool _offeringCrew = false;
    uint32 _now = 0;
    uint32 _boltAt = 0;
    uint32 _offeringAt = 0;
    uint32 _screamAt = 0;
    uint32 _addsAt = 0;
    uint32 _calls = 0;
    uint32 _frenzy = 0;
    uint32 _offerings = 0;
    bool _heroic = false;
    bool _engaged = false;
};

// Nekrum Gutchewer 7796
struct boss_nekrum_rework : public ScriptedAI
{
    explicit boss_nekrum_rework(Creature* creature)
        : ScriptedAI(creature), _arena(AltarArena(), LeashOptions(kAltarKey))
    {
    }

    void Reset() override
    {
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);

        Cleanup();
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        _hamstringAt = urand(0, Tune::kHamstringFirstMaxMs);
        _gutchewAt = Tune::kGutchewEveryMs;

        OnBossPull(me, kAltarKey);
        StartAltar(me);
        _arena.Engage(me);
        // Stock (SmartAI 7796 event 0): Berserker Charge on aggro at whoever pulled him (a knockback, harmless on the
        // open plaza).
        if (who && who->IsAlive())
            me->CastSpell(who, SPELL_BERSERKER_CHARGE, false);
        AltarLog("engage", Acore::StringFormat("unit=nekrum heroic={} who={}", _heroic ? 1 : 0,
            who ? who->GetName() : "-"));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        AltarLog("evade", Acore::StringFormat("unit=nekrum reason={}", uint32(why)));
        Cleanup();
        ScriptedAI::EnterEvadeMode(why);
        FailAltar(me, "nekrum");
    }

    void JustDied(Unit* /*killer*/) override
    {
        AltarLog("death", Acore::StringFormat("unit=nekrum gutchews={}", _gutchews));
        Cleanup();
    }

    void DoAction(int32 action) override
    {
        if (action == ACTION_TEST_GUTCHEW && _engaged)
            _gutchewAt = _now;
    }

    uint32 GetData(uint32 id) const override
    {
        return id == DATA_TEST_ENGAGED ? (_engaged ? 1 : 0) : 0;
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        _now += diff;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        Unit* victim = me->GetVictim();
        // Heroic Gutchew: his bite opens a Grievous Wound on his target (PyramidFight.h; a normal map refuses).
        if (_heroic && _now >= _gutchewAt && victim)
        {
            _gutchewAt = _now + Tune::kGutchewEveryMs;
            if (victim->IsPlayer() && ZfPyramid::ApplyGrievousWound(me, victim))
            {
                ++_gutchews;
                AltarLog("gutchew", Acore::StringFormat("target={} count={}", victim->GetName(), _gutchews));
            }
        }
        if (_now >= _hamstringAt && victim)
        {
            DoCastVictim(SPELL_HAMSTRING);
            _hamstringAt = _now + urand(Tune::kHamstringMinMs, Tune::kHamstringMaxMs);
        }
        DoMeleeAttackIfReady();
    }

private:
    // RB-1: the clocks, his buff, the leash.
    void Cleanup()
    {
        ZfPyramid::RemoveSandfuryBuff(me);
        _now = 0;
        _hamstringAt = 0;
        _gutchewAt = 0;
        _gutchews = 0;
        _engaged = false;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    uint32 _now = 0;
    uint32 _hamstringAt = 0;
    uint32 _gutchewAt = 0;
    uint32 _gutchews = 0;
    bool _heroic = false;
    bool _engaged = false;
};

void AddSC_boss_sezzziz_rework()
{
    RegisterDungeonReworkCreatureAI(boss_sezzziz_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(boss_nekrum_rework, ZulFarrakRework::kInstanceScriptName);
}
