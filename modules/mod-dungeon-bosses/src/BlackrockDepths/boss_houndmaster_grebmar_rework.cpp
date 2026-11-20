/*
 * mod-dungeon-bosses, Blackrock Depths D3: Houndmaster Grebmar (9319) and his Kennel Hounds (300781), "Release the
 * hounds" (ruling 15). Build spec S1 "Houndmaster Grebmar" (docs/dungeons/blackrock-depths-1-detention-block.md,
 * GR1-GR8; rulings 16, 88), handoff sections 3.4 (rows D3), 3.5 (row D3), 3.6, 3.8 (NM: the cavern, the kennel row,
 * the Fetch exit), 3.9 (G1's `leap` row). Replaces his SmartAI (WP-S0's rev drops the three rows): Demoralizing Shout
 * retired, Pummel kept (a copy in his slice), Bloodlust moved to the 30% finale. The five stock Bloodhounds at his feet
 * are deleted by rev_grebmar_blackrock_depths.sql; this script summons four Kennel Hounds there instead. Bound by
 * apps/dbc-tools source/npcs/blackrock_depths/grebmar.py. Pure rules: GrebmarLogic.h.
 *
 *   GR1  Kennel Horn      30 s, then every 40 s: emote 5, the horn, 2 / 3 hounds bound in from the two kennel doors
 *                         on the cell row (cap 6 / 8 alive); each attacks a random player (the tank picks them up)
 *   GR2  Whistle          8 s, then every 12 s / 10 s: a 2 s interruptible whistle naming a command (yell 1-3); the
 *                         three rotate, never the same twice in a row; a kick cancels the command. Each command has
 *                         its own whistle spell in its own school (a kick locks only that one)
 *   GR3  Sic 'em          a random player (the tank too, ruling 88) is marked during the whistle; at its end their
 *                         spot locks as a 5 yd landing circle, 1.5 s, 30% / 45% + Weakened (tag 5)
 *   GR4  Leap lines       one 3 yd line from each free hound to the spot, 1.5 s, 15% / 25% + Weakened, heroic + the
 *                         hounds' Rend (tag 4); the hounds take off 0.5 s before and land on the spot
 *   GR5  Fetch            a free hound snatches a random player's weapon (the tank too): Snatched (-30% damage and
 *                         healing done, 30 s); the runner (marked, kill order first) runs to the exit; killed within
 *                         15 s the weapon comes back (Snatched removed), else it escapes (despawns) and Snatched runs a
 *                         fresh 30 s
 *   GR6  Heel             every hound but a runner runs back to a ring at his feet and channels Lick Wounds (5 s: 5%
 *                         of its health a second, +30% damage taken); finished: Frenzy (+30% attack speed, 15 s, an
 *                         Enrage); a kick, a stun, a silence or a knockback stops it (no heal left, no Frenzy)
 *   GR7  Pummel           5-7 s, then every 12-14 s: a player casting within 5 yd; 10% / 15% + a 5 s lockout
 *   GR8  Finale           at 30%: yell 4, an extra horn at once (the horn timer restarts), Bloodlust 21049 (+30%
 *                         attack speed, 30 s, Magic: purge list); heroic: every whistle after it is a double, the
 *                         second 2.5 s after the first
 *        The pack         four hounds at his feet whenever he is home and out of combat; a hound pulled pulls him,
 *                         his pull pulls them; they despawn on his death, evade or reset (BossAI summons)
 *
 * Every timer runs on the AI's own clock (a whistle's cast bar never pauses one). Every firing logs one INFO line
 * "brd grebmar <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GrebmarLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdGrebmar;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "grebmar";

    uint32 constexpr POINT_HEEL = 1;
    uint32 constexpr POINT_FETCH_EXIT = 2;
    float constexpr kGroundBandYd = 6.f;            // a ground probe further off than this is taken as a hole
    float constexpr kLeapMinSpeedZ = 6.f;
    float constexpr kLeapMinSpeedXY = 4.f;
    float constexpr kOpeningThreat = 10.f;          // a horn hound's first target
    float constexpr kGrebmarFacing = 2.31f;         // his spawn's orientation [db]

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogGr(char const* mechanic, std::string const& detail = {})
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

    // The test commands' forced mechanics (`.dbtest brd grebmar ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        SicEm,
        Fetch,
        Heel,
        Horn,
        Finale,
        Pack,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// Kennel Hound 300781: Grebmar's pack. Melee and the stock Rend while it fights; the rest is on his orders.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_kennel_hound : public ScriptedAI
{
    explicit npc_brd_kennel_hound(Creature* creature) : ScriptedAI(creature) { }

    enum class State : uint8
    {
        Fight,      // melee, Rend
        Hold,       // GR4: standing on its line's start until the take-off
        Leap,       // GR4: in the air
        Heel,       // GR6: running back to his feet
        Lick,       // GR6: channeling Lick Wounds
        Runner,     // GR5: running off with a weapon (passive)
    };

    void Reset() override
    {
        _state = State::Fight;
        _chaseAfterCc = false;
        _pendingHeel.reset();
        _line = MechanicHandle();
        me->SetReactState(REACT_AGGRESSIVE);
        me->RemoveAurasDueToSpell(SPELL_GR_FRENZY);
    }

    // A hound pulled before him pulls him (and so the pack).
    void JustEngagedWith(Unit* who) override
    {
        _rendAtMs = _clockMs + urand(kRendEveryMinMs, kRendEveryMaxMs);
        if (Creature* boss = Boss())
            if (boss->IsAlive() && !boss->IsInCombat() && boss->IsAIEnabled && who)
                boss->AI()->AttackStart(who);
    }

    // While Grebmar fights, a hound never walks home on its own (a target lost for a moment): back into his fight.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (Creature* boss = Boss())
            if (boss->IsAlive() && boss->IsEngaged())
            {
                DoZoneInCombat();
                if (me->IsEngaged())
                    return;
            }
        ScriptedAI::EnterEvadeMode(why);
    }

    // Orders move it; a new target never pulls it off one.
    void AttackStart(Unit* who) override
    {
        if (_state == State::Fight)
            ScriptedAI::AttackStart(who);
    }

    void JustDied(Unit* /*killer*/) override
    {
        // A hound that dies before its leap draws no hit: its line goes with it.
        if (_line)
            if (Creature* boss = Boss())
                Mechanic::Cancel(boss, _line);
        _line = MechanicHandle();
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE)
            return;
        if (id == POINT_HEEL && _state == State::Heel)
            StartLick("arrived");
        else if (id == POINT_FETCH_EXIT && _state == State::Runner)
            LogGr("fetch-exit", Acore::StringFormat("hound={}", me->GetGUID().GetCounter()));
    }

    void OnChannelFinished(SpellInfo const* spell) override
    {
        if (!spell || spell->Id != SPELL_GR_LICK_WOUNDS || _state != State::Lick)
            return;
        me->CastSpell(me, SPELL_GR_FRENZY, true);
        me->CastSpell(me, SPELL_GR_FRENZY_FLASH, true);
        LogGr("frenzy", Acore::StringFormat("hound={} health={:.0f}%", me->GetGUID().GetCounter(), me->GetHealthPct()));
        BackToFight();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell || spell->Id != SPELL_GR_LICK_WOUNDS || _state != State::Lick)
            return;
        LogGr("lick-stopped", Acore::StringFormat("hound={} health={:.0f}%", me->GetGUID().GetCounter(),
            me->GetHealthPct()));
        BackToFight();
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        switch (_state)
        {
            case State::Runner:
                return;     // passive: Grebmar's clock decides the escape
            case State::Hold:
                if (CrowdControlled())
                    DropLeap();     // CC'd on its line before the take-off: no leap, its line goes
                else if (_clockMs >= _takeOffMs)
                    TakeOff();
                return;
            case State::Leap:
                if (_clockMs >= _landMs)
                    Land();
                return;
            case State::Heel:
                if (_clockMs >= _heelUntilMs)
                    StartLick("timeout");
                return;
            case State::Lick:
                // A knockback or a grip moved it: the lick stops (OnSpellFailed ends it).
                if (me->GetExactDist2d(_lickFrom.GetPositionX(), _lickFrom.GetPositionY()) > kLickMovedYd)
                    me->InterruptSpell(CURRENT_CHANNELED_SPELL);
                else if (!me->GetCurrentSpell(CURRENT_CHANNELED_SPELL))
                    BackToFight();  // the channel ended without a hook (refused mid-way)
                return;
            case State::Fight:
                break;
        }

        if (!UpdateVictim())
            return;
        if (_chaseAfterCc && !CrowdControlled())
        {
            _chaseAfterCc = false;
            BackToFight();
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_clockMs >= _rendAtMs)
        {
            Unit* victim = me->GetVictim();
            if (victim && me->IsWithinMeleeRange(victim, kRendRangeYd))
            {
                me->CastSpell(victim, SPELL_GR_REND, true);
                _rendAtMs = _clockMs + urand(kRendEveryMinMs, kRendEveryMaxMs);
            }
            else
                _rendAtMs = _clockMs + kRetryMs;
        }
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Grebmar's orders
    // ----------------------------------------------------------------------------------------------------------------

    // Free for a command: alive, fighting (not holding, leaping, licking or running) and not crowd-controlled.
    bool Free() const
    {
        return HoundObeys(me->IsAlive(), _state == State::Fight, CrowdControlled());
    }

    // Feared, confused, stunned (traps, saps, incapacitates), rooted, banished or under a damage-breakable CC.
    bool CrowdControlled() const
    {
        return me->HasUnitState(UNIT_STATE_CONTROLLED | UNIT_STATE_ROOT)
            || me->HasAuraWithMechanic(1 << MECHANIC_BANISH) || me->HasBreakableByDamageCrowdControlAura();
    }

    bool IsRunner() const
    {
        return _state == State::Runner;
    }

    // GR4: hold on the line's start; take off `takeOffInMs` from now, land on `landing` `landInMs` from now.
    void HoldForLeap(Position const& landing, uint32 takeOffInMs, uint32 landInMs, MechanicHandle line)
    {
        _state = State::Hold;
        _landing = landing;
        _takeOffMs = _clockMs + takeOffInMs;
        _landMs = _clockMs + landInMs;
        _line = line;
        me->GetMotionMaster()->Clear();
        me->StopMoving();
    }

    // GR6: run to `spot` at his feet, then lick. A hound in the air finishes its leap first.
    void Heel(Position const& spot)
    {
        if (_state == State::Hold || _state == State::Leap)
        {
            _pendingHeel = spot;
            return;
        }
        if (_state != State::Fight || CrowdControlled())
            return;
        _state = State::Heel;
        _heelUntilMs = _clockMs + kHeelRunMs;
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_HEEL, spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ());
    }

    // GR5: snatch `victim`'s weapon and run for the exit (passive: the group has to chase it down).
    void Snatch(Player* victim)
    {
        _state = State::Runner;
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->InterruptNonMeleeSpells(false);
        me->CastSpell(me, SPELL_GR_FETCH_RUNNER, true);
        if (victim)
            me->CastSpell(victim, SPELL_GR_SNATCHED, true);
        me->GetMotionMaster()->Clear();
        float const z = GroundZ(me, kFetchExit.x, kFetchExit.y, kFetchExit.z);
        me->GetMotionMaster()->MovePoint(POINT_FETCH_EXIT, kFetchExit.x, kFetchExit.y, z);
    }

    // A horn hound: into the fight on `target` (a random player; the tank has to pick it up).
    void BoundIn(Unit* target)
    {
        me->CastSpell(me, SPELL_GR_KENNEL_HORN_BURST, true);
        DoZoneInCombat();
        if (target)
        {
            me->AddThreat(target, kOpeningThreat);
            AttackStart(target);
        }
    }

    char const* StateName() const
    {
        switch (_state)
        {
            case State::Fight:  return "fight";
            case State::Hold:   return "hold";
            case State::Leap:   return "leap";
            case State::Heel:   return "heel";
            case State::Lick:   return "lick";
            case State::Runner: return "runner";
        }
        return "?";
    }

private:
    Creature* Boss() const
    {
        if (TempSummon const* summon = me->ToTempSummon())
            if (Unit* summoner = summon->GetSummonerUnit())
                return summoner->ToCreature();
        return nullptr;
    }

    void DropLeap()
    {
        if (_line)
            if (Creature* boss = Boss())
                Mechanic::Cancel(boss, _line);
        _line = MechanicHandle();
        _pendingHeel.reset();
        _state = State::Fight;
        _chaseAfterCc = true;   // its hold cleared the chase: back on its victim once the CC breaks
        LogGr("leap-dropped", Acore::StringFormat("hound={} cc=1", me->GetGUID().GetCounter()));
    }

    void TakeOff()
    {
        _state = State::Leap;
        float const dist = me->GetExactDist2d(_landing.GetPositionX(), _landing.GetPositionY());
        uint64 const flightMs = _landMs > _clockMs ? _landMs - _clockMs : 1;
        float const speedXY = std::max(kLeapMinSpeedXY, dist * 1000.f / static_cast<float>(flightMs));
        DungeonKit::JumpTo(me, _landing, speedXY, kLeapMinSpeedZ, SPELL_GR_LEAP_LOOK, me);
    }

    void Land()
    {
        _line = MechanicHandle();
        _state = State::Fight;
        if (_pendingHeel)
        {
            Position const spot = *_pendingHeel;
            _pendingHeel.reset();
            Heel(spot);
            return;
        }
        BackToFight();
    }

    void StartLick(char const* why)
    {
        _state = State::Lick;
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        _lickFrom = me->GetPosition();
        if (me->CastSpell(me, SPELL_GR_LICK_WOUNDS, false) != SPELL_CAST_OK)
        {
            LogGr("lick-refused", Acore::StringFormat("hound={} why={}", me->GetGUID().GetCounter(), why));
            BackToFight();
            return;
        }
        LogGr("lick", Acore::StringFormat("hound={} why={} health={:.0f}%", me->GetGUID().GetCounter(), why,
            me->GetHealthPct()));
    }

    void BackToFight()
    {
        _state = State::Fight;
        me->SetReactState(REACT_AGGRESSIVE);
        if (!me->IsEngaged())
            return;
        Unit* target = me->GetVictim();
        if (!target)
            target = me->SelectVictim();
        if (target)
        {
            me->GetMotionMaster()->Clear();
            ScriptedAI::AttackStart(target);
            me->GetMotionMaster()->MoveChase(target);
        }
    }

    State _state = State::Fight;
    bool _chaseAfterCc = false;
    uint64 _clockMs = 0;
    uint64 _rendAtMs = 0;
    uint64 _takeOffMs = 0;
    uint64 _landMs = 0;
    uint64 _heelUntilMs = 0;
    Position _landing;
    Position _lickFrom;
    std::optional<Position> _pendingHeel;
    MechanicHandle _line;
};

namespace
{
    npc_brd_kennel_hound* HoundAI(Creature* creature)
    {
        if (!creature || !creature->IsAlive() || !creature->IsAIEnabled)
            return nullptr;
        return dynamic_cast<npc_brd_kennel_hound*>(creature->AI());
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Houndmaster Grebmar 9319
// ---------------------------------------------------------------------------------------------------------------------
struct boss_houndmaster_grebmar_rework : public BossAI
{
    explicit boss_houndmaster_grebmar_rework(Creature* creature)
        : BossAI(creature, BOSS_GREBMAR), _arena(GrebmarArena(), LeashOptions(kBoss)) { }

    // One weapon on the run (GR5).
    struct FetchRun
    {
        ObjectGuid hound;
        ObjectGuid player;
        uint64 escapeAtMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();       // despawns the pack (BossAI summons)
        Cleanup();
        _packDue = true;    // a fresh pack once he stands at home (UpdateAI)
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        StartFight();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogGr("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(SAY_GREBMAR_DEATH);
        Cleanup();
        BossAI::JustDied(killer);   // the pack despawns with him
        LogGr("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : std::string("none")));
    }

    void JustSummoned(Creature* summon) override
    {
        BossAI::JustSummoned(summon);   // into his fight when he is in one
        if (summon && summon->GetEntry() == NPC_BRD_KENNEL_HOUND && me->IsEngaged())
            Mechanic::TrackUnit(me, summon);
    }

    // GR5: the runner killed in time brings the weapon back.
    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        if (!summon)
            return;
        for (auto it = _runs.begin(); it != _runs.end(); ++it)
        {
            if (it->hound != summon->GetGUID())
                continue;
            Player* player = ObjectAccessor::GetPlayer(*me, it->player);
            if (player)
                player->RemoveAurasDueToSpell(SPELL_GR_SNATCHED, it->hound);
            LogGr("fetch-returned", Acore::StringFormat("player={} left={}ms", player ? player->GetName() : "gone",
                it->escapeAtMs > _clockMs ? it->escapeAtMs - _clockMs : 0));
            _runs.erase(it);
            return;
        }
    }

    // GR2: a whistle that ran its 2 s gives its command.
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        Command command;
        if (spell && CommandOfSpell(spell->Id, command))
            Execute(command);
    }

    // GR2: a kicked (or silenced) whistle gives nothing; the Sic 'em mark goes.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        Command command;
        if (!spell || !CommandOfSpell(spell->Id, command))
            return;
        if (command == Command::SicEm)
            ClearMark();
        LogGr("whistle-interrupted", Acore::StringFormat("command={}", CommandName(command)));
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (_packDue && me->IsAlive() && !me->IsInCombat() && !me->HasUnitState(UNIT_STATE_EVADE))
            SummonPack("home");
        // Fetch runs also run out of combat (`.dbtest` on an idle boss).
        UpdateRuns();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_fighting)
            return;

        CheckFinale();
        RunTimers();
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pull, the pack
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight()
    {
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GREBMAR;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        Talk(SAY_GREBMAR_PULL);
        _fighting = true;
        _finale = false;

        if (AliveHounds().empty())
            SummonPack("pull");
        summons.DoZoneInCombat(NPC_BRD_KENNEL_HOUND);
        for (Creature* hound : AliveHounds())
            Mechanic::TrackUnit(me, hound);

        _next = FirstCommand(urand(0, kCommandCount - 1));
        _whistleAtMs = _clockMs + kWhistleFirstMs;
        _secondWhistleAtMs = 0;
        _hornAtMs = _clockMs + kHornFirstMs;
        _pummelAtMs = _clockMs + urand(kPummelFirstMinMs, kPummelFirstMaxMs);
        Mechanic::NoteNextCastIn(me, WhistleSpell(_next), Ms(kWhistleFirstMs));
        Describe();
        LogGr("engage", Acore::StringFormat("heroic={} hounds={} first={}", _heroic ? 1 : 0, AliveHounds().size(),
            CommandName(_next)));
    }

    // Four hounds at his feet (none while some are still up).
    void SummonPack(char const* why)
    {
        _packDue = false;
        if (!AliveHounds().empty())
            return;
        uint32 count = 0;
        for (Point3 const& spot : kPackSpots)
            if (me->SummonCreature(NPC_BRD_KENNEL_HOUND, spot.x, spot.y, spot.z, kGrebmarFacing,
                TEMPSUMMON_MANUAL_DESPAWN))
                ++count;
        LogGr("pack", Acore::StringFormat("why={} hounds={}", why, count));
    }

    std::vector<Creature*> AliveHounds()
    {
        std::vector<Creature*> out;
        for (ObjectGuid const& guid : summons)
            if (Creature* c = ObjectAccessor::GetCreature(*me, guid))
                if (c->GetEntry() == NPC_BRD_KENNEL_HOUND && c->IsAlive())
                    out.push_back(c);
        return out;
    }

    // Hounds free for a command (GR3 leaps, GR5 snatches).
    std::vector<Creature*> FreeHounds()
    {
        std::vector<Creature*> out;
        for (Creature* hound : AliveHounds())
            if (npc_brd_kennel_hound* ai = HoundAI(hound))
                if (ai->Free())
                    out.push_back(hound);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timers
    // ----------------------------------------------------------------------------------------------------------------

    void RunTimers()
    {
        bool const casting = me->HasUnitState(UNIT_STATE_CASTING);

        // GR8 heroic: the second whistle of a double.
        if (_secondWhistleAtMs && _clockMs >= _secondWhistleAtMs && !casting)
        {
            if (StartWhistle(false))
                _secondWhistleAtMs = 0;
            else
                _secondWhistleAtMs = _clockMs + kRetryMs;
        }
        else if (!_secondWhistleAtMs && _clockMs >= _whistleAtMs && !casting)
        {
            if (!StartWhistle(true))
                _whistleAtMs = _clockMs + kRetryMs;
        }

        // GR1: the horn never waits (not a cast).
        if (_clockMs >= _hornAtMs)
        {
            BlowHorn("timer");
            _hornAtMs = _clockMs + kHornEveryMs;
        }

        // GR7
        if (_clockMs >= _pummelAtMs && !me->HasUnitState(UNIT_STATE_CASTING))
            _pummelAtMs = _clockMs + (TryPummel() ? urand(kPummelEveryMinMs, kPummelEveryMaxMs) : kRetryMs);
    }

    // GR8: at 30%, once.
    void CheckFinale()
    {
        if (_finale || !me->HealthBelowPct(static_cast<int32>(kFinalePct)))
            return;
        Finale("health");
    }

    void Finale(char const* why)
    {
        _finale = true;
        Talk(SAY_GREBMAR_FINALE);
        me->CastSpell(me, SPELL_GR_RELEASE_THE_HOUNDS, true);
        me->CastSpell(me, SPELL_STOCK_BLOODLUST, true);
        LogGr("finale", Acore::StringFormat("why={} health={:.0f}% double={}", why, me->GetHealthPct(),
            _heroic ? 1 : 0));
        BlowHorn("finale");
        _hornAtMs = _clockMs + kHornEveryMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GR1 Kennel Horn
    // ----------------------------------------------------------------------------------------------------------------

    void BlowHorn(char const* why)
    {
        Talk(EMOTE_GREBMAR_HORN);
        me->CastSpell(me, SPELL_GR_KENNEL_HORN, true);
        std::size_t const alive = AliveHounds().size();
        uint32 const count = HornSummons(static_cast<uint32>(alive), _heroic);
        uint32 summoned = 0;
        for (uint32 i = 0; i < count; ++i)
        {
            Point3 const door = HornEntry(_hornDoor++);
            float const facing = DungeonKit::BearingTo(door.XY(), DungeonKit::PlaneOf(me));
            Creature* hound = me->SummonCreature(NPC_BRD_KENNEL_HOUND, door.x, door.y, door.z, facing,
                TEMPSUMMON_MANUAL_DESPAWN);
            if (!hound)
                continue;
            ++summoned;
            if (npc_brd_kennel_hound* ai = HoundAI(hound))
                ai->BoundIn(RandomPlayer());
        }
        LogGr("horn", Acore::StringFormat("why={} alive={} summoned={} cap={}", why, alive, summoned,
            kPackCap(_heroic)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GR2 the whistle and its commands
    // ----------------------------------------------------------------------------------------------------------------

    // `scheduled`: the regular whistle (false: the heroic double's second). False when the cast was refused.
    bool StartWhistle(bool scheduled)
    {
        Command const command = _next;
        if (command == Command::SicEm)
            Mark();
        if (me->CastSpell(me, WhistleSpell(command), false) != SPELL_CAST_OK)
        {
            ClearMark();
            return false;
        }
        Talk(CommandText(command));
        _next = NextCommand(command, urand(0, 1));
        bool const second = scheduled && _heroic && _finale;
        if (scheduled)
        {
            _whistleAtMs = _clockMs + kWhistleEveryMs(_heroic);
            if (second)
                _secondWhistleAtMs = _clockMs + kDoubleWhistleGapMs;
        }
        uint64 const nextIn = second ? kDoubleWhistleGapMs : (_whistleAtMs > _clockMs ? _whistleAtMs - _clockMs : 0);
        Mechanic::NoteNextCastIn(me, WhistleSpell(_next), Ms(static_cast<uint32>(nextIn)));
        LogGr("whistle", Acore::StringFormat("command={} scheduled={} double={} next={}", CommandName(command),
            scheduled ? 1 : 0, second ? 1 : 0, CommandName(_next)));
        return true;
    }

    void Execute(Command command)
    {
        switch (command)
        {
            case Command::SicEm: SicEm(); break;
            case Command::Fetch: Fetch(); break;
            case Command::Heel:  Heel();  break;
        }
    }

    // GR3: the mark during the whistle, on a random player (the tank too, ruling 88).
    void Mark()
    {
        ClearMark();
        Player* target = RandomPlayer();
        if (!target)
            return;
        _marked = target->GetGUID();
        me->CastSpell(target, SPELL_GR_SIC_EM_MARK, true);
    }

    void ClearMark()
    {
        if (!_marked.IsEmpty())
            if (Player* player = ObjectAccessor::GetPlayer(*me, _marked))
                player->RemoveAurasDueToSpell(SPELL_GR_SIC_EM_MARK, me->GetGUID());
        _marked.Clear();
    }

    // GR3 / GR4: the marked player's spot locks; every free hound draws its line to it and leaps 1.5 s later.
    void SicEm()
    {
        Player* target = _marked.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _marked);
        if (!target || !target->IsAlive() || target->GetMap() != me->GetMap())
            target = RandomPlayer();
        _marked.Clear();
        if (!target)
        {
            LogGr("sic-em-none", "nobody to mark");
            return;
        }
        std::vector<Creature*> const hounds = FreeHounds();
        if (hounds.empty())
        {
            target->RemoveAurasDueToSpell(SPELL_GR_SIC_EM_MARK, me->GetGUID());
            LogGr("sic-em-none", "no free hound");
            return;
        }
        float const z = target->GetPositionZ();
        Position const spot(target->GetPositionX(), target->GetPositionY(), z, 0.f);

        MechanicRef landing = Mechanic::Circle(me, BossMechanics::Anchor(spot), kLandingRadius, Ms(kLeapMs));
        landing.Damage(kLandingPct(_heroic)).TankDamage(kLandingPct(_heroic))
            .Weakened().Spell(SPELL_GR_SIC_EM_LANDING).Tag(TAG_GR_LEAP_LANDING);
        Track(landing.Handle());

        uint32 lines = 0;
        for (Creature* hound : hounds)
        {
            npc_brd_kennel_hound* ai = HoundAI(hound);
            if (!ai)
                continue;
            Vec2 const from = DungeonKit::PlaneOf(hound);
            float const length = DungeonKit::Distance(from, Vec2{ spot.GetPositionX(), spot.GetPositionY() });
            MechanicHandle handle;
            if (DrawsLine(length))
            {
                float const facing = DungeonKit::BearingTo(from, Vec2{ spot.GetPositionX(), spot.GetPositionY() });
                BossMechanics::Anchor const start(Position(from.x, from.y, hound->GetPositionZ(), facing));
                BossMechanics::Anchor const stop(Position(spot.GetPositionX(), spot.GetPositionY(), z, facing));
                MechanicRef ref = Mechanic::Line(me, start, stop, kLeapLineWidth, Ms(kLeapMs));
                ref.Damage(kLeapLinePct(_heroic)).TankDamage(kLeapLinePct(_heroic))
                    .Weakened().Spell(SPELL_GR_SIC_EM_LEAP).Tag(TAG_GR_LEAP_LINE);
                if (_heroic)
                    ref.Rider(SPELL_GR_REND);   // heroic Leap Rend
                handle = ref.Handle();
                Track(handle);
                ++lines;
            }
            ai->HoldForLeap(spot, LeapPlan::TakeOffMs(), LeapPlan::LandMs(), handle);
        }
        LogGr("sic-em", Acore::StringFormat("target={} at=({:.1f}, {:.1f}) hounds={} lines={} landing={:.0f}% "
            "line={:.0f}% rend={}", target->GetName(), spot.GetPositionX(), spot.GetPositionY(), hounds.size(), lines,
            kLandingPct(_heroic), kLeapLinePct(_heroic), _heroic ? 1 : 0));
    }

    // GR5: a free hound runs off with a random player's weapon (the tank too).
    void Fetch()
    {
        std::vector<Creature*> const hounds = FreeHounds();
        Player* victim = RandomPlayer();
        if (hounds.empty() || !victim)
        {
            LogGr("fetch-none", hounds.empty() ? "no free hound" : "nobody to rob");
            return;
        }
        Creature* runner = hounds[urand(0, uint32(hounds.size() - 1))];
        npc_brd_kennel_hound* ai = HoundAI(runner);
        if (!ai)
            return;
        ai->Snatch(victim);
        _runs.push_back({ runner->GetGUID(), victim->GetGUID(), _clockMs + kFetchWindowMs });
        LogGr("fetch", Acore::StringFormat("hound={} player={} window={}ms", runner->GetGUID().GetCounter(),
            victim->GetName(), kFetchWindowMs));
    }

    // GR5: a runner alive after its window gets away; Snatched runs a fresh 30 s.
    void UpdateRuns()
    {
        for (auto it = _runs.begin(); it != _runs.end();)
        {
            Creature* hound = ObjectAccessor::GetCreature(*me, it->hound);
            if (!hound || !hound->IsAlive())
            {
                it = _runs.erase(it);   // killed (SummonedCreatureDies) or despawned
                continue;
            }
            if (_clockMs < it->escapeAtMs)
            {
                ++it;
                continue;
            }
            Player* player = ObjectAccessor::GetPlayer(*me, it->player);
            bool const refreshed = player && DungeonKit::ShortenAura(player, SPELL_GR_SNATCHED, it->hound,
                Ms(kSnatchedMs));
            LogGr("fetch-escaped", Acore::StringFormat("player={} snatched={}ms", player ? player->GetName() : "gone",
                refreshed ? kSnatchedMs : 0));
            hound->DespawnOrUnsummon();
            it = _runs.erase(it);
        }
    }

    // GR6: every hound but a runner or a crowd-controlled one huddles at his feet and licks its wounds.
    void Heel()
    {
        std::vector<Creature*> heeling;
        for (Creature* hound : AliveHounds())
            if (npc_brd_kennel_hound* ai = HoundAI(hound))
                if (!ai->IsRunner() && !ai->CrowdControlled())
                    heeling.push_back(hound);
        Vec2 const center = DungeonKit::PlaneOf(me);
        uint32 const n = static_cast<uint32>(heeling.size());
        for (uint32 i = 0; i < n; ++i)
        {
            Vec2 const at = HeelSpot(center, i, n);
            if (npc_brd_kennel_hound* ai = HoundAI(heeling[i]))
                ai->Heel(Position(at.x, at.y, GroundZ(me, at.x, at.y, me->GetPositionZ()), 0.f));
        }
        LogGr("heel", Acore::StringFormat("hounds={}", n));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GR7 Pummel
    // ----------------------------------------------------------------------------------------------------------------

    // A player casting within 5 yd (the stock event 105). False when nobody is.
    bool TryPummel()
    {
        Map* map = me->GetMap();
        if (!map)
            return false;
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !me->IsInCombatWith(player))
                continue;
            if (!me->IsWithinMeleeRange(player, kPummelRangeYd) || !player->IsNonMeleeSpellCast(false, false, true))
                continue;
            me->CastSpell(player, SPELL_GR_PUMMEL, true);
            LogGr("pummel", Acore::StringFormat("target={} pct={:.0f}", player->GetName(), kPummelPct(_heroic)));
            return true;
        }
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The descriptor, state
    // ----------------------------------------------------------------------------------------------------------------

    // Interrupt list: the whistles (a reward on normal, expected on heroic) and Lick Wounds (the stop list: a kick on
    // each hound). Purge list: Bloodlust on him (Magic), Frenzy on a hound (an Enrage: Tranquilizing Shot; the hounds
    // are demons, so no Soothe). Kill order: the Fetch runner, then the pack (cleave), then him.
    void Describe()
    {
        BossMechanics::Descriptor d;
        uint8 const priority = _heroic ? kWhistleKickPriorityHeroic : kWhistleKickPriorityNormal;
        for (uint8 i = 0; i < kCommandCount; ++i)
            d.interrupts.emplace_back(NPC_GREBMAR, WhistleSpell(static_cast<Command>(i)), priority,
                Ms(kWhistleEveryMs(_heroic)));
        d.interrupts.emplace_back(NPC_BRD_KENNEL_HOUND, SPELL_GR_LICK_WOUNDS, kLickKickPriority);
        d.purges.emplace_back(NPC_GREBMAR, SPELL_STOCK_BLOODLUST, 1);
        d.purges.emplace_back(NPC_BRD_KENNEL_HOUND, SPELL_GR_FRENZY, 1);
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_KENNEL_HOUND, kRunnerPriority, BossMechanics::Who::Dps,
            BossMechanics::Condition::HasAura(SPELL_GR_FETCH_RUNNER)));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_KENNEL_HOUND, kHoundPriority, BossMechanics::Who::Dps,
            BossMechanics::Condition::LacksAura(SPELL_GR_FETCH_RUNNER)).AoeOk());
        Mechanic::Describe(me, std::move(d));
    }

    // A random player in his fight (the tank too, ruling 88); out of combat the GM of a test command.
    Player* RandomPlayer()
    {
        if (!me->IsEngaged())
            return _testPlayer.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _testPlayer);
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        return DungeonKit::PickPlayer(me, rule);
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // Nothing pending, no zone, no mark, no weapon on the run, every aura of the fight gone (Reset, evade, death).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _runs.clear();
        _marked.Clear();
        _fighting = false;
        _finale = false;
        _whistleAtMs = 0;
        _secondWhistleAtMs = 0;
        _hornAtMs = 0;
        _pummelAtMs = 0;
        me->RemoveAurasDueToSpell(SPELL_STOCK_BLOODLUST);
        if (instance)
            for (uint32 const spell : { uint32(SPELL_GR_SNATCHED), uint32(SPELL_GR_SIC_EM_MARK),
                uint32(SPELL_GR_REND) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        _arena.Reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd grebmar` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    // An empty string when fired; otherwise why not. `gm` stands in for the group out of combat.
    std::string TestFire(TestKind kind, Player* gm)
    {
        _testPlayer = gm ? gm->GetGUID() : ObjectGuid::Empty;
        switch (kind)
        {
            case TestKind::SicEm:
            case TestKind::Fetch:
            case TestKind::Heel:
            {
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "Busy casting; try again in a moment.";
                _next = kind == TestKind::SicEm ? Command::SicEm : (kind == TestKind::Fetch ? Command::Fetch
                    : Command::Heel);
                if (!StartWhistle(false))
                    return "The whistle was refused.";
                break;
            }
            case TestKind::Horn:
                BlowHorn("test");
                break;
            case TestKind::Finale:
                if (_finale)
                    return "The finale already ran this pull.";
                Finale("test");
                break;
            case TestKind::Pack:
                SummonPack("test");
                break;
            case TestKind::Clear:
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brd grebmar heroic <0|1>`: the heroic form on a normal map (and back) until the end of the next pull.
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
        std::string hounds;
        for (Creature* hound : AliveHounds())
            if (npc_brd_kennel_hound* ai = HoundAI(hound))
                hounds += Acore::StringFormat(" {}:{}:{:.0f}%", hound->GetGUID().GetCounter(), ai->StateName(),
                    hound->GetHealthPct());
        return Acore::StringFormat("grebmar heroic={} fighting={} finale={} next={} whistle={} second={} horn={} "
            "pummel={} runs={} hounds=[{} ]", _heroic ? 1 : 0, _fighting ? 1 : 0, _finale ? 1 : 0, CommandName(_next),
            left(_whistleAtMs), left(_secondWhistleAtMs), left(_hornAtMs), left(_pummelAtMs), _runs.size(), hounds);
    }

private:
    DungeonKit::ArenaGuard _arena;
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
    bool _finale = false;           // GR8 ran
    bool _packDue = true;
    uint64 _clockMs = 0;            // the AI's own clock: nothing here waits for a cast bar
    uint64 _whistleAtMs = 0;        // GR2
    uint64 _secondWhistleAtMs = 0;  // GR8 heroic: the double's second
    uint64 _hornAtMs = 0;           // GR1
    uint64 _pummelAtMs = 0;         // GR7
    uint32 _hornDoor = 0;           // the next kennel door (alternates)
    Command _next = Command::SicEm;
    ObjectGuid _marked;             // GR3: the player marked during the whistle
    std::vector<FetchRun> _runs;
    std::vector<MechanicHandle> _live;
    ObjectGuid _testPlayer;
};

namespace
{
    boss_houndmaster_grebmar_rework* GrebmarAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_GREBMAR);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_houndmaster_grebmar_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        boss_houndmaster_grebmar_rework* ai = GrebmarAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(kind, handler->GetPlayer());
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    // `.dbtest brd grebmar info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_GREBMAR, BOSS_GREBMAR);
    }

    // `.dbtest brd grebmar state`: his clocks and each hound's state.
    bool HandleState(ChatHandler* handler)
    {
        boss_houndmaster_grebmar_rework* ai = GrebmarAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest brd grebmar sicem`: GR2 + GR3 / GR4 now (out of combat: on you).
    bool HandleSicEm(ChatHandler* handler)
    {
        return Fire(handler, TestKind::SicEm, "Whistle: Sic 'em! (2 s, then the landing and the lines, 1.5 s).");
    }

    // `.dbtest brd grebmar fetch`: GR2 + GR5 now (out of combat: your weapon).
    bool HandleFetch(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Fetch, "Whistle: Fetch! (2 s, then a hound runs for the exit, 15 s).");
    }

    // `.dbtest brd grebmar heel`: GR2 + GR6 now.
    bool HandleHeel(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Heel, "Whistle: Heel! (2 s, then the pack licks its wounds, 5 s).");
    }

    // `.dbtest brd grebmar horn`: GR1 now.
    bool HandleHorn(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Horn, "Kennel Horn: hounds from the kennel doors (cap 6 / 8).");
    }

    // `.dbtest brd grebmar finale`: GR8 now.
    bool HandleFinale(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Finale, "Release the hounds: a horn and Bloodlust (heroic: double whistles).");
    }

    // `.dbtest brd grebmar pack`: the four hounds at his feet (when none are up).
    bool HandlePack(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Pack, "The pack: four hounds at his feet (none while some are up).");
    }

    // `.dbtest brd grebmar clear`: every zone, mark and weapon run goes.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared.");
    }

    // `.dbtest brd grebmar heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_houndmaster_grebmar_rework* ai = GrebmarAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossHoundmasterGrebmarTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,    SEC_GAMEMASTER, Console::No },
            { "sicem",  HandleSicEm,    SEC_GAMEMASTER, Console::No },
            { "fetch",  HandleFetch,    SEC_GAMEMASTER, Console::No },
            { "heel",   HandleHeel,     SEC_GAMEMASTER, Console::No },
            { "horn",   HandleHorn,     SEC_GAMEMASTER, Console::No },
            { "finale", HandleFinale,   SEC_GAMEMASTER, Console::No },
            { "pack",   HandlePack,     SEC_GAMEMASTER, Console::No },
            { "clear",  HandleClear,    SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_houndmaster_grebmar_rework()
{
    RegisterDungeonReworkCreatureAI(boss_houndmaster_grebmar_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_kennel_hound, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("grebmar", BossHoundmasterGrebmarTestCommands());
}
