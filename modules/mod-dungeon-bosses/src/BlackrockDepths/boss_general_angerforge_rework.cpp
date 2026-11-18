/*
 * mod-dungeon-bosses, Blackrock Depths D14: General Angerforge (9033) and his squads, "the field commander whose army
 * keeps arriving" (ruling 52). Build spec S3 "General Angerforge" (docs/dungeons/blackrock-depths-3-manufactory.md,
 * AF1-AF6; rulings 52, 53, 88), handoff sections 3.4 (rows D14), 3.5 (row D14), 3.6, 3.8 (NM: the hall and the four
 * mole spots, gap 26), 3.10. The stock script (boss_general_angerforge, ScriptedAI) stays registered in core and is
 * unbound by data once wave 2 binds (apps/dbc-tools source/npcs/blackrock_depths/angerforge.py); this BossAI replaces
 * it: Hamstring and the 21% reinforcement call are retired. Pure rules: AngerforgeLogic.h. Wave 2: the AIs register
 * only once kWave2Bound flips (an unbound registered name logs "not assigned" at boot); the `.dbtest brd angerforge`
 * table registers now.
 *
 *   AF1  Mighty Blow      stock 14099 (a copy in the slice): the tank hit and its knockback, 8 s, then every 18 s
 *   AF2  Cleave           stock 20691 (a copy): a frontal swing on up to five, so melee stand behind him; 16 s,
 *                         then every 9 s
 *   AF3  Deploy Mole Machine  10 s, then every 30 s (heroic 25 s): yell 1 and a 2 s rumble at one of four fixed spots
 *                         on the hall's edge (never the same twice), then the machine (GO 301289) comes up, drops the
 *                         squad and goes down 3 s later. Normal: an Officer and 2 Reservists; every other squad
 *                         swaps a Reservist for a Medic. Heroic: an Officer, 2 Reservists and a Medic. No drill
 *                         starts while 2 Officers live. A player within 6 yd of the spot keeps the machine (and its
 *                         collision) away; the squad still lands. The drill deals no damage
 *   AF4  Commanding Aura  each Officer shields every other add within 15 yd (never Angerforge): 50% less damage and
 *                         casts that cannot be interrupted (no kick, no silence); the shield is a short aura the
 *                         Officer re-applies every second, so it ends with him
 *   AF5  Medic Heal       a 3 s cast on Angerforge for 5% of his health, 6 s after it lands, then every 12 s; the Medic
 *                         also keeps Mind Blast. Interruptible unless an Officer shields it
 *   AF6  Fireburst Grenade  15 s, then every 20 s (heroic 15 s): 2 (heroic 3) players, never the tank, are marked for
 *                         5 s; at detonation each marked player takes 15% / 25%, everyone else within 8 yd of a marked
 *                         player takes 25% / 40% and a Weakened (Spread, tag 1)
 *        The pull         the four stock Reservists (8901) at his side join the fight and are in the kill order
 *
 * Kill order: Officer, Medic, Reservist, Angerforge. Interrupt list: the Medic's Heal, held while it is shielded. Every
 * timer runs on the AI's own clock. Every firing logs one INFO line "brd angerforge <mechanic> ..."
 * (module.dungeonbosses).
 */

#include "AngerforgeLogic.h"
#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <list>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdAngerforge;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "angerforge";

    float constexpr kGroundBandYd = 6.f;            // a ground probe further off than this is taken as a hole
    // The Officers' orange 15 yd ring (V-1: a kit ring on a unit anchor, lasting); a decoy, so it judges nothing.
    bool constexpr kDrawCommandingRing = true;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogAf(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > kGroundBandYd)
            return refZ;
        return h;
    }

    // The boss that summoned `me` (a squad member), when it is still there.
    Creature* BossOf(Creature const* me)
    {
        if (TempSummon const* summon = me->ToTempSummon())
            if (Unit* summoner = summon->GetSummonerUnit())
                return summoner->ToCreature();
        return nullptr;
    }

    // The test commands' forced mechanics (`.dbtest brd angerforge ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        Squad,
        Grenade,
        Blow,
        Cleave,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// Squad Officer 300830: melee, and Commanding Aura (AF4). Every second it shields the other adds within 15 yd.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_squad_officer : public ScriptedAI
{
    explicit npc_brd_squad_officer(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _pulseInMs = 0;
        _shoutInMs = 0;
    }

    // The aura itself (a lasting self aura: the name and the tooltip players read on the Officer).
    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        me->CastSpell(me, SPELL_AF_COMMANDING_AURA, true);
    }

    void JustDied(Unit* /*killer*/) override
    {
        RemoveShields();
        me->RemoveAurasDueToSpell(SPELL_AF_COMMANDING_AURA);
    }

    void UpdateAI(uint32 diff) override
    {
        // The shield stands before the squad's first swing: it pulses out of combat too.
        if (_pulseInMs <= diff)
        {
            Pulse();
            _pulseInMs = kCommandingPulseMs;
        }
        else
            _pulseInMs -= diff;
        if (_shoutInMs <= diff)
        {
            me->CastSpell(me, SPELL_AF_COMMANDING_SHOUT, true);
            _shoutInMs = kCommandingShoutEveryMs;
        }
        else
            _shoutInMs -= diff;

        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

private:
    // Every other add of the squad (and the stock Reservists) within 15 yd, never Angerforge.
    void Pulse()
    {
        if (!me->IsAlive())
            return;
        std::list<Creature*> near;
        me->GetCreatureListWithEntryInGrid(near, ShieldedEntries(), kCommandingRadiusYd);
        for (Creature* add : near)
            if (add && add->IsAlive() && ShieldReaches(add->GetEntry(), add == me, me->GetExactDist2d(add)))
                me->CastSpell(add, SPELL_AF_COMMANDED, true);
    }

    // The shield this Officer gave goes with it (another Officer's re-applies within its next pulse).
    void RemoveShields()
    {
        std::list<Creature*> near;
        me->GetCreatureListWithEntryInGrid(near, ShieldedEntries(), 2.f * kCommandingRadiusYd);
        for (Creature* add : near)
            if (add)
                add->RemoveAurasDueToSpell(SPELL_AF_COMMANDED, me->GetGUID());
    }

    static std::vector<uint32> const& ShieldedEntries()
    {
        static std::vector<uint32> const entries{ NPC_BRD_SQUAD_OFFICER, NPC_BRD_SQUAD_RESERVIST,
            NPC_BRD_SQUAD_MEDIC, NPC_ANVILRAGE_RESERVIST };
        return entries;
    }

    uint32 _pulseInMs = 0;
    uint32 _shoutInMs = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Squad Medic 300832: the Heal on Angerforge (AF5) and the stock Mind Blast. It stands off and casts.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_squad_medic : public ScriptedAI
{
    explicit npc_brd_squad_medic(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _followsBoss = false;
        _healAtMs = _clockMs + kHealFirstMs;
        _blastAtMs = _clockMs + urand(kMindBlastMinMs, kMindBlastMaxMs);
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _healAtMs = _clockMs + kHealFirstMs;
        _blastAtMs = _clockMs + urand(kMindBlastMinMs, kMindBlastMaxMs);
    }

    void AttackStart(Unit* who) override
    {
        _followsBoss = false;
        AttackStartCaster(who, kMedicRangeYd);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        KeepHealRange();
        if (_clockMs >= _healAtMs)
            TryHeal();
        else if (_clockMs >= _blastAtMs)
            TryBlast();
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

private:
    // R-2-A MI-1: it stands off its victim, which may be far from Angerforge; past kMedicLeashYd of him (or out of his
    // sight) it follows him at kMedicRangeYd instead, so the heal stays in range. A new victim (AttackStart) hands it
    // back to the usual stand-off, and this check pulls it in again when needed.
    void KeepHealRange()
    {
        if (_clockMs < _rangeCheckAtMs)
            return;
        _rangeCheckAtMs = _clockMs + kRetryMs;
        Creature* boss = BossOf(me);
        if (_followsBoss || !boss || !boss->IsAlive())
            return;
        if (!MedicMustCloseIn(me->GetExactDist2d(boss), me->IsWithinLOSInMap(boss)))
            return;
        me->GetMotionMaster()->MoveChase(boss, kMedicRangeYd);
        _followsBoss = true;
        LogAf("medic-closes-in", Acore::StringFormat("medic={} distance={:.0f}", me->GetGUID().GetCounter(),
            me->GetExactDist2d(boss)));
    }

    // AF5: the 3 s bar on Angerforge (not while he misses less than a heal is worth; then it looks again next second).
    void TryHeal()
    {
        Creature* boss = BossOf(me);
        if (!boss || !boss->IsAlive() || !HealWanted(boss->GetHealthPct()))
        {
            _healAtMs = _clockMs + kCapRetryMs;
            return;
        }
        if (me->CastSpell(boss, SPELL_AF_HEAL, false) == SPELL_CAST_OK)
        {
            _healAtMs = _clockMs + kHealEveryMs;
            LogAf("heal", Acore::StringFormat("medic={} boss={:.0f}% shielded={}", me->GetGUID().GetCounter(),
                boss->GetHealthPct(), me->HasAura(SPELL_AF_COMMANDED) ? 1 : 0));
        }
        else
            _healAtMs = _clockMs + kRetryMs;
    }

    void TryBlast()
    {
        Unit* victim = me->GetVictim();
        if (victim && me->CastSpell(victim, SPELL_STOCK_MIND_BLAST, false) == SPELL_CAST_OK)
            _blastAtMs = _clockMs + urand(kMindBlastMinMs, kMindBlastMaxMs);
        else
            _blastAtMs = _clockMs + kRetryMs;
    }

    uint64 _clockMs = 0;
    uint64 _healAtMs = 0;
    uint64 _blastAtMs = 0;
    uint64 _rangeCheckAtMs = 0;
    bool _followsBoss = false;      // chasing Angerforge (KeepHealRange) rather than standing off its victim
};

// ---------------------------------------------------------------------------------------------------------------------
// General Angerforge 9033
// ---------------------------------------------------------------------------------------------------------------------
struct boss_general_angerforge_rework : public BossAI
{
    explicit boss_general_angerforge_rework(Creature* creature)
        : BossAI(creature, BOSS_ANGERFORGE), _arena(AngerforgeArena(), LeashOptions(kBoss)) { }

    // One drop in progress (AF3).
    struct Drop
    {
        enum class Phase : uint8
        {
            None,
            Rumble,     // the yell and the dirt burst
            Machine,    // the machine stands and the squad fights
        };

        Phase phase = Phase::None;
        uint32 spot = kNoSpot;
        uint64 nextAtMs = 0;        // Rumble: the landing; Machine: the retreat
        ObjectGuid machine;
        SquadPlan plan;
    };

    // One Officer's ring (a decoy circle on a unit anchor).
    struct Ring
    {
        MechanicHandle handle;
        uint64 renewAtMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();       // despawns the squads (BossAI summons)
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        StartFight(who);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogAf("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(SAY_AF_DEATH);
        Cleanup();
        BossAI::JustDied(killer);   // the squads despawn with him
        LogAf("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : std::string("none")));
    }

    void JustSummoned(Creature* summon) override
    {
        BossAI::JustSummoned(summon);   // into his fight when he is in one
        if (!summon || !_fighting)
            return;
        Mechanic::TrackUnit(me, summon);
        if (summon->GetEntry() == NPC_BRD_SQUAD_OFFICER)
            DrawRing(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        if (!summon)
            return;
        if (summon->GetEntry() == NPC_BRD_SQUAD_OFFICER)
        {
            DropRing(summon->GetGUID());
            LogAf("officer-down", Acore::StringFormat("officer={} left={}", summon->GetGUID().GetCounter(),
                AliveOfficers()));
        }
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        if (summon && summon->GetEntry() == NPC_BRD_SQUAD_OFFICER)
            DropRing(summon->GetGUID());
        BossAI::SummonedCreatureDespawn(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // The machine, the bomb's flight and the rings also run out of combat (`.dbtest` on an idle boss).
        UpdateDrop();
        UpdateGrenadeLook();
        if (_fighting)
            UpdateRings();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_fighting)
            return;

        RunTimers();
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pull
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight(Unit* who)
    {
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ANGERFORGE;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        Talk(SAY_AF_PULL);
        _fighting = true;
        _squads = 0;
        _lastSpot = kNoSpot;
        _blowAtMs = _clockMs + kMightyBlowFirstMs;
        _cleaveAtMs = _clockMs + kCleaveFirstMs;
        _squadAtMs = _clockMs + NextSquadDelayMs(0, _heroic);
        _grenadeAtMs = _clockMs + kGrenadeFirstMs;
        uint32 const stock = PullStockReservists(who);
        for (ObjectGuid const& guid : summons)
            if (Creature* add = ObjectAccessor::GetCreature(*me, guid))
                Mechanic::TrackUnit(me, add);
        Describe();
        LogAf("engage", Acore::StringFormat("heroic={} reservists={}", _heroic ? 1 : 0, stock));
    }

    // The four stock Reservists (8901) at his side join the pull and the kill order. Returns how many.
    uint32 PullStockReservists(Unit* who)
    {
        std::list<Creature*> list;
        me->GetCreatureListWithEntryInGrid(list, NPC_ANVILRAGE_RESERVIST, kStockReservistRadiusYd);
        uint32 pulled = 0;
        for (Creature* reservist : list)
        {
            if (!reservist || !reservist->IsAlive())
                continue;
            if (who && reservist->IsAIEnabled && !reservist->IsInCombat())
                reservist->AI()->AttackStart(who);
            Mechanic::TrackUnit(me, reservist);
            _stock.push_back(reservist->GetGUID());
            ++pulled;
        }
        return pulled;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timers
    // ----------------------------------------------------------------------------------------------------------------

    void RunTimers()
    {
        // AF1, AF2: swings at the victim in melee reach (a retry while he is not).
        if (_clockMs >= _blowAtMs)
            _blowAtMs = _clockMs + (Swing(SPELL_AF_MIGHTY_BLOW, "mighty-blow", kMightyBlowPct(_heroic))
                ? kMightyBlowEveryMs : kRetryMs);
        if (_clockMs >= _cleaveAtMs)
            _cleaveAtMs = _clockMs + (Swing(SPELL_AF_CLEAVE, "cleave", kCleavePct(_heroic)) ? kCleaveEveryMs
                : kRetryMs);
        // AF3: held back (and not restarted) while two Officers live.
        if (_clockMs >= _squadAtMs)
        {
            if (!TryDrop())
                _squadAtMs = _clockMs + kCapRetryMs;
        }
        // AF6
        if (_clockMs >= _grenadeAtMs)
            _grenadeAtMs = _clockMs + (ThrowGrenades() ? kGrenadeEveryMs(_heroic) : kRetryMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AF1 Mighty Blow, AF2 Cleave
    // ----------------------------------------------------------------------------------------------------------------

    // The victim of a swing: his own (in melee reach), else (a test out of combat) the GM.
    Unit* SwingTarget()
    {
        if (Unit* victim = me->GetVictim())
            return me->IsWithinMeleeRange(victim) ? victim : nullptr;
        if (!me->IsEngaged() && !_testPlayer.IsEmpty())
            return ObjectAccessor::GetPlayer(*me, _testPlayer);
        return nullptr;
    }

    bool Swing(uint32 spell, char const* what, float pct)
    {
        Unit* target = SwingTarget();
        if (!target)
            return false;
        me->CastSpell(target, spell, true);
        LogAf(what, Acore::StringFormat("target={} pct={:.0f}", target->GetName(), pct));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AF3 Deploy Mole Machine
    // ----------------------------------------------------------------------------------------------------------------

    uint32 AliveOfficers()
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : summons)
            if (Creature* c = ObjectAccessor::GetCreature(*me, guid))
                if (c->GetEntry() == NPC_BRD_SQUAD_OFFICER && c->IsAlive())
                    ++n;
        return n;
    }

    // The timer's drop. False: a drill is still on its way or the cap holds it (the timer then tries again at once,
    // and is not restarted).
    bool TryDrop()
    {
        if (_drop.phase != Drop::Phase::None || !DropAllowed(AliveOfficers()))
            return false;
        StartDrop(NextSpot(_lastSpot, urand(0, kSpotRolls - 1)));
        _squadAtMs = _clockMs + NextSquadDelayMs(_squads, _heroic);
        return true;
    }

    void StartDrop(uint32 spotIndex)
    {
        Point3 const& spot = kMoleSpots[spotIndex % kMoleSpotCount];
        _drop = Drop();
        _drop.phase = Drop::Phase::Rumble;
        _drop.spot = spotIndex % kMoleSpotCount;
        _drop.plan = SquadFor(_squads, _heroic);
        _drop.nextAtMs = _clockMs + kRumbleMs;
        _lastSpot = _drop.spot;
        ++_squads;
        Talk(SAY_AF_REINFORCE);
        me->CastSpell(spot.x, spot.y, spot.z, SPELL_AF_MOLE_DEPLOY_LOOK, true);
        LogAf("drill", Acore::StringFormat("squad={} spot=M{} at=({:.1f}, {:.1f}) officers={} reservists={} medics={} "
            "heroic={}", _squads, _drop.spot + 1, spot.x, spot.y, _drop.plan.officers, _drop.plan.reservists,
            _drop.plan.medics, _heroic ? 1 : 0));
    }

    void UpdateDrop()
    {
        if (_drop.phase == Drop::Phase::None || _clockMs < _drop.nextAtMs)
            return;
        if (_drop.phase == Drop::Phase::Rumble)
            Land();
        else
            Retreat();
    }

    // The nearest player to a spot on the plane (alive, not a GM), 1,000 yd when none.
    float NearestPlayerYd(Point3 const& spot)
    {
        float best = 1000.f;
        if (Map* map = me->GetMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    if (player->IsAlive() && !player->IsGameMaster())
                        best = std::min(best, player->GetExactDist2d(spot.x, spot.y));
        return best;
    }

    // The machine comes up (unless a player stands on it) and the squad lands around it, facing the hall.
    void Land()
    {
        Point3 const& spot = kMoleSpots[_drop.spot];
        float const toward = DungeonKit::BearingTo(spot.XY(), DungeonKit::PlaneOf(me));
        float const nearest = NearestPlayerYd(spot);
        bool machine = false;
        if (MachineMayStand(nearest))
        {
            if (GameObject* go = me->SummonGameObject(GO_BRD_MOLE_MACHINE, spot.x, spot.y, spot.z, toward, 0.f, 0.f,
                0.f, 0.f, kMachineBackstopSec))
            {
                _drop.machine = go->GetGUID();
                machine = true;
            }
        }

        std::array<uint32, kSquadMaxSize> const entries = SquadEntries(_drop.plan);
        uint32 landed = 0;
        for (uint32 i = 0; i < _drop.plan.Total() && i < kSquadMaxSize; ++i)
        {
            Vec2 const at = SlotPoint(spot.XY(), toward, i);
            float const z = GroundZ(me, at.x, at.y, spot.z);
            if (me->SummonCreature(entries[i], at.x, at.y, z, toward + DungeonKit::kPi, TEMPSUMMON_MANUAL_DESPAWN))
                ++landed;
        }
        _drop.phase = Drop::Phase::Machine;
        _drop.nextAtMs = _clockMs + kMachineWaitMs;
        LogAf("squad", Acore::StringFormat("spot=M{} landed={} machine={} nearest-player={:.1f}yd officers-up={}",
            _drop.spot + 1, landed, machine ? 1 : 0, nearest, AliveOfficers()));
    }

    // The machine goes down again (its look), the object goes with it.
    void Retreat()
    {
        Point3 const& spot = kMoleSpots[_drop.spot];
        if (!_drop.machine.IsEmpty())
        {
            me->CastSpell(spot.x, spot.y, spot.z, SPELL_AF_MOLE_RETREAT_LOOK, true);
            DeleteMachine();
        }
        LogAf("retreat", Acore::StringFormat("spot=M{}", _drop.spot + 1));
        _drop = Drop();
    }

    void DeleteMachine()
    {
        if (_drop.machine.IsEmpty())
            return;
        if (Map* map = me->GetMap())
            if (GameObject* go = map->GetGameObject(_drop.machine))
                go->Delete();
        _drop.machine.Clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AF4 the Officers' ring
    // ----------------------------------------------------------------------------------------------------------------

    void DrawRing(Creature* officer)
    {
        if (!kDrawCommandingRing || !officer)
            return;
        DropRing(officer->GetGUID());
        MechanicRef ref = Mechanic::Circle(me, officer, kCommandingRadiusYd, Ms(kCommandingRingMs));
        ref.Decoy().NoFillTimer().Color(BossMechanics::Color::Orange).Tag(TAG_AF_COMMANDING_RING);
        if (!ref.IsValid())
            return;
        // Renewed 2 s before it would pop (a decoy's end is harmless, but the ring should not blink).
        _rings[officer->GetGUID()] = Ring{ ref.Handle(), _clockMs + kCommandingRingMs - 2000 };
    }

    void DropRing(ObjectGuid const& officer)
    {
        auto it = _rings.find(officer);
        if (it == _rings.end())
            return;
        Mechanic::Cancel(me, it->second.handle);
        _rings.erase(it);
    }

    void UpdateRings()
    {
        std::vector<ObjectGuid> due;
        for (auto const& [guid, ring] : _rings)
            if (_clockMs >= ring.renewAtMs)
                due.push_back(guid);
        for (ObjectGuid const& guid : due)
        {
            Creature* officer = ObjectAccessor::GetCreature(*me, guid);
            if (officer && officer->IsAlive())
                DrawRing(officer);
            else
                DropRing(guid);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AF6 Fireburst Grenade
    // ----------------------------------------------------------------------------------------------------------------

    // 2 (heroic 3) players, not the tank (kGrenadeMarksTank), each marked for 5 s; false when nobody is there to mark.
    bool ThrowGrenades()
    {
        std::vector<Player*> picks;
        if (me->IsEngaged())
        {
            picks = DungeonKit::PickPlayers(me, GrenadePickRule(), kGrenadeCount(_heroic));
            if (picks.empty())  // a tank alone in the fight is still marked
                picks = DungeonKit::PickPlayers(me, GrenadeTankAloneRule(), 1);
        }
        else if (Player* gm = _testPlayer.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _testPlayer))
            picks.push_back(gm);
        if (picks.empty())
            return false;

        GuidSet carriers;
        std::string names;
        for (Player* carrier : picks)
        {
            carriers.insert(carrier->GetGUID());
            me->CastSpell(carrier, SPELL_AF_GRENADE_MARK, true);
            Talk(EMOTE_AF_GRENADE, carrier);
            names += (names.empty() ? "" : ",") + carrier->GetName();
        }
        float const pct = kGrenadeOthersPct(_heroic);
        MechanicRef ref = Mechanic::Spread(me, kGrenadeRadius, Ms(kGrenadeWarnMs));
        ref.Targets(carriers).Damage(pct).TankDamage(pct).Weakened().School(SPELL_SCHOOL_FIRE)
            .Spell(SPELL_AF_GRENADE).Tag(TAG_AF_GRENADE);
        ref.OnResolve(OnAngerforge([carriers](boss_general_angerforge_rework& ai, BossMechanics::ResolveResult const&)
        {
            ai.GrenadesDetonate(carriers);
        }));
        Track(ref.Handle());
        _grenade.carriers = carriers;
        _grenade.lookAtMs = _clockMs + kGrenadeWarnMs - kGrenadeLookLeadMs;
        LogAf("grenade", Acore::StringFormat("marked={} carriers={} radius={:.0f} others={:.0f}% marked-hit={:.0f}% "
            "heroic={}", carriers.size(), names, kGrenadeRadius, pct, kGrenadeMarkedPct(_heroic), _heroic ? 1 : 0));
        return true;
    }

    // The bomb's flight: a throw at each carrier just before it lands.
    void UpdateGrenadeLook()
    {
        if (_grenade.carriers.empty() || !_grenade.lookAtMs || _clockMs < _grenade.lookAtMs)
            return;
        _grenade.lookAtMs = 0;
        for (ObjectGuid const& guid : _grenade.carriers)
            if (Player* carrier = ObjectAccessor::GetPlayer(*me, guid))
                if (carrier->IsAlive())
                    me->CastSpell(carrier, SPELL_AF_GRENADE_LOOK, true);
    }

    // The detonation: each carrier's own hit (15% / 25%, the tank's row on the tank); the ring hit the others.
    void GrenadesDetonate(GuidSet const& carriers)
    {
        uint32 hit = 0;
        for (ObjectGuid const& guid : carriers)
        {
            Player* carrier = ObjectAccessor::GetPlayer(*me, guid);
            if (!carrier)
                continue;
            carrier->RemoveAurasDueToSpell(SPELL_AF_GRENADE_MARK, me->GetGUID());
            if (!carrier->IsAlive() || carrier->GetMap() != me->GetMap())
                continue;
            me->CastSpell(carrier, SPELL_AF_GRENADE_MARKED, true);
            ++hit;
        }
        _grenade = GrenadeState();
        LogAf("grenade-detonated", Acore::StringFormat("carriers={} hit={} marked-hit={:.0f}%", carriers.size(), hit,
            kGrenadeMarkedPct(_heroic)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The descriptor, state
    // ----------------------------------------------------------------------------------------------------------------

    // Interrupt list: the Medic's Heal (a reward on normal, expected on heroic), held while the Medic carries the
    // Officer's shield; the same hold on any shielded add keeps stock kicks off it. Kill order: Officer, Medic,
    // Reservist (the squad's and the four stock ones, cleaved), Angerforge.
    void Describe()
    {
        BossMechanics::Descriptor d;
        uint8 const priority = _heroic ? kHealKickPriorityHeroic : kHealKickPriorityNormal;
        d.interrupts.emplace_back(NPC_BRD_SQUAD_MEDIC, SPELL_AF_HEAL, priority, Ms(kHealEveryMs),
            BossMechanics::Condition::Not(BossMechanics::Condition::HasAura(SPELL_AF_COMMANDED)));
        d.holds.push_back(BossMechanics::HoldEntry::Interrupts(0, SPELL_AF_COMMANDED));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_SQUAD_OFFICER, kOfficerPriority,
            BossMechanics::Who::Dps));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_SQUAD_MEDIC, kMedicPriority, BossMechanics::Who::Dps));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_SQUAD_RESERVIST, kReservistPriority,
            BossMechanics::Who::Dps).AoeOk());
        d.targets.push_back(BossMechanics::TargetEntry(NPC_ANVILRAGE_RESERVIST, kReservistPriority,
            BossMechanics::Who::Dps).AoeOk());
        Mechanic::Describe(me, std::move(d));
    }

    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnAngerforge(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_general_angerforge_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    static boss_general_angerforge_rework* From(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_general_angerforge_rework*>(boss->AI());
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 48)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 24);
    }

    // Nothing pending, no machine, no ring, no mark, every aura of the fight gone (Reset, evade, death).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (auto const& [guid, ring] : _rings)
            Mechanic::Cancel(me, ring.handle);
        _rings.clear();
        DeleteMachine();
        _drop = Drop();
        _grenade = GrenadeState();
        for (ObjectGuid const& guid : _stock)
            if (Creature* reservist = ObjectAccessor::GetCreature(*me, guid))
                reservist->RemoveAurasDueToSpell(SPELL_AF_COMMANDED);
        _stock.clear();
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_AF_GRENADE_MARK);
        _fighting = false;
        _blowAtMs = 0;
        _cleaveAtMs = 0;
        _squadAtMs = 0;
        _grenadeAtMs = 0;
        _arena.Reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd angerforge` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    // An empty string when fired; otherwise why not. `gm` stands in for the group out of combat.
    std::string TestFire(TestKind kind, Player* gm, uint32 spot = 0)
    {
        _testPlayer = gm ? gm->GetGUID() : ObjectGuid::Empty;
        switch (kind)
        {
            case TestKind::Squad:
                if (_drop.phase != Drop::Phase::None)
                    return "A drill is already on its way; try again in a few seconds.";
                // `spot` 1-4 names the machine; 0 picks as the timer does. The cap is ignored (a forced drop).
                if (spot >= 1 && spot <= kMoleSpotCount)
                    StartDrop(spot - 1);
                else
                    StartDrop(NextSpot(_lastSpot, urand(0, kSpotRolls - 1)));
                break;
            case TestKind::Grenade:
                if (!ThrowGrenades())
                    return "Nobody to mark (stand in the room out of combat, or bring the group).";
                break;
            case TestKind::Blow:
                if (!Swing(SPELL_AF_MIGHTY_BLOW, "mighty-blow", kMightyBlowPct(_heroic)))
                    return "No victim in melee reach (out of combat the GM stands in: be in reach).";
                break;
            case TestKind::Cleave:
                if (!Swing(SPELL_AF_CLEAVE, "cleave", kCleavePct(_heroic)))
                    return "No victim in melee reach (out of combat the GM stands in: be in reach).";
                break;
            case TestKind::Clear:
                summons.DespawnAll();
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brd angerforge heroic <0|1>`: the heroic form on a normal map (and back) until the end of the next pull.
    // Only the script's side switches (timers, counts, radii, the percents it hands the registry): the percent spells'
    // own scripts (spell_dungeon_refflat_damage) read the map, so on a normal map they still deal the normal percents.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
        if (_fighting)
            Describe();
    }

    std::string TestState()
    {
        auto left = [this](uint64 at) -> std::string
        {
            return at ? std::to_string(at > _clockMs ? (at - _clockMs) / 1000 : 0) + "s" : "-";
        };
        char const* phase = _drop.phase == Drop::Phase::None ? "idle"
            : (_drop.phase == Drop::Phase::Rumble ? "rumble" : "machine");
        return Acore::StringFormat("angerforge heroic={} fighting={} squads={} officers={} drop={} (spot M{}) blow={} "
            "cleave={} squad={} grenade={} carriers={} rings={} stock-reservists={}", _heroic ? 1 : 0,
            _fighting ? 1 : 0, _squads, AliveOfficers(), phase, _drop.spot < kMoleSpotCount ? _drop.spot + 1 : 0,
            left(_blowAtMs), left(_cleaveAtMs), left(_squadAtMs), left(_grenadeAtMs), _grenade.carriers.size(),
            _rings.size(), _stock.size());
    }

private:
    struct GrenadeState
    {
        GuidSet carriers;
        uint64 lookAtMs = 0;
    };

    DungeonKit::ArenaGuard _arena;
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
    uint64 _clockMs = 0;            // the AI's own clock
    uint64 _blowAtMs = 0;           // AF1
    uint64 _cleaveAtMs = 0;         // AF2
    uint64 _squadAtMs = 0;          // AF3
    uint64 _grenadeAtMs = 0;        // AF6
    uint32 _squads = 0;             // drops started this pull
    uint32 _lastSpot = kNoSpot;
    Drop _drop;
    GrenadeState _grenade;
    std::unordered_map<ObjectGuid, Ring> _rings;
    std::vector<ObjectGuid> _stock;
    std::vector<MechanicHandle> _live;
    ObjectGuid _testPlayer;
};

namespace
{
    boss_general_angerforge_rework* AngerforgeAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_ANGERFORGE);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_general_angerforge_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok, uint32 spot = 0)
    {
        boss_general_angerforge_rework* ai = AngerforgeAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(kind, handler->GetPlayer(), spot);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    // `.dbtest brd angerforge info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_ANGERFORGE, BOSS_ANGERFORGE);
    }

    // `.dbtest brd angerforge state`: his clocks, the drill and the squad.
    bool HandleState(ChatHandler* handler)
    {
        boss_general_angerforge_rework* ai = AngerforgeAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest brd angerforge squad [1-4]`: AF3 now (the yell, a 2 s rumble, the machine and the squad) at M1-M4.
    bool HandleSquad(ChatHandler* handler, Optional<uint32> spot)
    {
        return Fire(handler, TestKind::Squad, "Deploy Mole Machine: the rumble, then the machine and the squad.",
            spot ? *spot : 0);
    }

    // `.dbtest brd angerforge grenade`: AF6 now (out of combat: on you).
    bool HandleGrenade(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Grenade, "Fireburst Grenade: the mark, 5 s, then the detonation.");
    }

    // `.dbtest brd angerforge blow`: AF1 now on his victim (out of combat: on you).
    bool HandleBlow(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Blow, "Mighty Blow.");
    }

    // `.dbtest brd angerforge cleave`: AF2 now.
    bool HandleCleave(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Cleave, "Cleave.");
    }

    // `.dbtest brd angerforge clear`: the squads, the machine, the rings and the marks go.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared.");
    }

    // `.dbtest brd angerforge heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_general_angerforge_rework* ai = AngerforgeAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossGeneralAngerforgeTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "squad",   HandleSquad,   SEC_GAMEMASTER, Console::No },
            { "grenade", HandleGrenade, SEC_GAMEMASTER, Console::No },
            { "blow",    HandleBlow,    SEC_GAMEMASTER, Console::No },
            { "cleave",  HandleCleave,  SEC_GAMEMASTER, Console::No },
            { "clear",   HandleClear,   SEC_GAMEMASTER, Console::No },
            { "heroic",  HandleHeroic,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_general_angerforge_rework()
{
    // One `if` per name: tests/lib/test_blackrock_depths_kit.py reads the gate off each registration line.
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_general_angerforge_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brd_squad_officer, BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brd_squad_medic, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("angerforge", BossGeneralAngerforgeTestCommands());
}
