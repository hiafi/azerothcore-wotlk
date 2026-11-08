/*
 * mod-dungeon-bosses, Shadowfang Keep: Archmage Arugal and the lair prisoner (WP-S9). Build spec: SK 1576-1646 (build
 * spec), SK 1394-1575 (design), AR1-AR10; handoff section 3.5 rows AR, section 3.6 row S9, section 7 #7 and #22, and
 * the user rulings of section 10 (he keeps his stock ledge; every level of his room stays reachable by melee with
 * well-timed jumps, bots take the stairs; the wards are placed for the level he is on; all turned = the turned
 * players die and the fight resets). Replaces the SmartAI of Archmage Arugal 4275 (WP-S9's SQL rev drops all of it;
 * his lines 0-2 also serve the Fenrus fight, WP-S7).
 *
 * Arugal (normal and heroic):
 *   AR1 Worgen's Curse   every player in the fight gains stacks of a 100-stack meter: +1 every 3 s (the seep, the
 *                        fight's enrage, Dungeon ruling 12), +15 from Thundershock, +3 from a landed Void Bolt, +10
 *                        from Arugal's Curse; never dispellable. 50+ glows, 80+ is tinted.
 *   AR2 Thundershock     a 2 s cast, a registry circle of 8 yd on him: 30% Nature, a 1.5 s stun and +15 stacks on
 *                        anyone still inside (no Weakened, ruling 13). Normal 10 s, then every 10; heroic every 5.
 *   AR3 Void Bolt        a real 3 s interruptible cast on his target, back to back between his other casts, never
 *                        started unless it ends before the next Thundershock or Shadow Port: 15% / 25% Shadow
 *                        (spell_sfk_arugal_void_bolt, RefFlat), +3 stacks when it lands. The interrupt list.
 *   AR4 Arugal's Curse   instant, "Release your rage!": +10 stacks on a random non-tank within 30 yd; 15 s, then
 *                        every 25 s (heroic 20).
 *   AR5 Shadow Port      5 s, then every 20 s: a 1 s flicker, then the next of his three spots (never the same):
 *                        his spawn and the stock 7586 on the platform, the stock 7136 in the antechamber (the stock
 *                        7587 hangs over the lower floor out of reach and is dropped). He never walks (no combat
 *                        movement): the group follows him, melee by the gallery jump or the stairs.
 *   AR6 Turned           at 100 stacks a player is charmed for good and turns into a Shadowfang Glutton (206069, the
 *                        aura the bots read as a hostile teammate, WP-F1), "Another falls!"; released when Arugal
 *                        dies, evades or resets. When every living player of the fight is turned, the turned players
 *                        die and the fight resets (handoff section 7 #22).
 *   AR7 Ashcrombe's Ward the prisoner places a ward every 20 s from 20 s, on the level Arugal stands on: a 5 yd
 *                        registry Stack (bots at 20-99 stacks go in, the tank too) for 10 s; once a player has stood
 *                        in it for 3 s it pulses: every player inside loses 10 stacks, and it fades. None on hard mode
 *                        (DATA_HARD_MODE, WP-S10) or without a prisoner.
 *   AR10 Melee           stock (DamageModifier 5.7); heroic via the DD damage hook.
 * Heroic on top:
 *   AR8 Feral Power      the heroic curse (206061) also gives +2% damage and healing done per full 10 stacks, up to
 *                        +18% (a hidden aura, 206062, one stack per 10).
 *   AR9 Moonrise         at 30%: a 3 s cast with a yell and an emote; as it starts the prisoner places one last full
 *                        5 yd ward beside the group (every player eligible); then he casts nothing else, does not
 *                        melee, and the seep is +2 every second; the wards keep their 20 s timer as 3 yd Soaks for
 *                        the two players with the most stacks. Kill order: turned players first before the moon,
 *                        Arugal first during it.
 *
 * The lair prisoner (npc_sfk_lair_prisoner, 300513 Sorcerer Ashcrombe / 300514 Deathstalker Adamant): the instance
 * summons the one who opened the courtyard door by the lair door once Nandos is dead. Not attackable, ignored by
 * creatures (the pack wolves that outlive Nandos, WP-S8's note), passive. On Arugal's pull it says its line, walks to
 * the antechamber's edge and jumps the gap onto the gallery, where it places the wards; on a wipe it is back at the
 * door. Its gossip menu (body text only) takes WP-S10's heroic option through LairPrisoner.h.
 *
 * The boss cannot be kited off his room (DungeonKit::ArenaGuard on ArugalArena(): platform, gallery, antechamber, ramps
 * and lower floor); a unit gripped back lands on the level he stands on, outside his Thundershock ring. Every firing
 * logs "sfk arugal <mechanic> ..." (module.dungeonbosses); `.sfktest arugal <mechanic>` fires one on demand.
 *
 * Stock behavior mirrored from the AzerothCore world DB SmartAI 4275 (aggro line 1, kill line 3 on a 5 s cooldown,
 * line 2 with the curse cast, the stock Shadow Port spots 7136 / 7586 from spell_target_position).
 */

#include "ArenaGuard.h"
#include "ArugalLogic.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "CreatureScript.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "LairPrisoner.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "ScriptedGossip.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;
using namespace Arugal;

namespace
{
    char constexpr kBoss[] = "arugal";

    // The floor under a measured point (navmesh points carry an estimated height): searched from just above it, so a
    // ledge point never drops to the lower floor 10 yd below.
    Position FloorAt(WorldObject const* ref, Point3 const& p, float orientation = 0.f)
    {
        float z = ref->GetMapHeight(p.x, p.y, p.z + 2.f);
        if (z <= INVALID_HEIGHT || std::fabs(z - p.z) > 3.f)
            z = p.z;
        return { p.x, p.y, z, orientation };
    }

    bool IsTurned(Unit const* unit)
    {
        return unit && unit->HasAura(SPELL_ARUGAL_TURNED);
    }

    // The players of the fight: alive, not game masters, and in combat with Arugal (DoZoneInCombat on the pull),
    // turned, or in his room. The room counts a battle-rezzed or soulstoned player who has not acted yet (no combat
    // with him until then): they get the seep and count for the all-turned rule (R2 N-2).
    template <class Fn>
    void ForEachFightPlayer(Creature* me, Arena const& room, Fn&& fn)
    {
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster())
                continue;
            if (!IsTurned(player) && !me->IsInCombatWith(player)
                && !room.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                continue;
            fn(player);
        }
    }

    // His arena guard: a unit off the room lands on the level he stands on, outside his Thundershock ring.
    DungeonKit::ArenaGuardOptions ArugalArenaOptions()
    {
        DungeonKit::ArenaGuardOptions o;
        // A unit in combat with another live boss is left to that boss: no two guards grip it to and fro (R2 S-2).
        o.skipGrip = DungeonKit::SkipEngagedWithOtherBoss(ShadowfangKeepRework::IsSfkBossEntry);
        o.logPrefix = "sfk arugal arena";
        o.holdWhileVictimOff = false;       // he never walks (no combat movement): nothing to hold
        o.landingKeepsZ = true;
        o.landing = [](Creature const* boss, Unit const* /*unit*/)
        {
            Point3 const& p = kSpots[NearestSpot(DungeonKit::PlaneOf(boss))].landing;
            return Position(p.x, p.y, p.z, 0.f);
        };
        return o;
    }

    SfkLairPrisoner::GossipHooks& GossipHookStore()
    {
        static SfkLairPrisoner::GossipHooks hooks;
        return hooks;
    }
}

struct npc_sfk_lair_prisoner;

// Archmage Arugal 4275
struct boss_archmage_arugal_rework : public BossAI
{
    explicit boss_archmage_arugal_rework(Creature* creature) : BossAI(creature, BOSS_ARUGAL),
        _arena(ArugalArena(), ArugalArenaOptions())
    {
        me->SetCombatMovement(false);
    }

    void Reset() override
    {
        BossAI::Reset();
        me->SetCombatMovement(false);
        ClearFight();
        _spot = SPOT_SPAWN;
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);       // DoZoneInCombat, BOSS_ARUGAL IN_PROGRESS
        bool const heroic = DungeonKit::IsHeroicMap(me);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ARUGAL;
        Mechanic::BeginEncounter(me, options);
        Describe();
        Mechanic::SetPhase(me, kPhaseNormal);
        _arena.Engage(me);
        _timeline.Start(heroic);
        _spot = NearestSpot(DungeonKit::PlaneOf(me));
        Talk(YELL_ARUGAL_AGGRO);
        if (npc_sfk_lair_prisoner* prisoner = PrisonerAI())
            PrisonerStepIn(prisoner);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "engage", Acore::StringFormat("heroic={} hardmode={} prisoner={}",
            heroic, HardMode(), PrisonerAI() != nullptr));
    }

    void KilledUnit(Unit* victim) override
    {
        // Stock: "Another falls!" on a kill, 5 s cooldown.
        if (victim && victim->IsPlayer() && _timeline.Now() >= _killLineReady)
        {
            Talk(YELL_ARUGAL_ANOTHER_FALLS);
            _killLineReady = _timeline.Now() + Ms(5000);
        }
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (!_wiping)
            KillTurnedIfAllTurned();
        ClearFight();
        PrisonerBackToDoor();
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "evade", Acore::StringFormat("reason={} spot={}", uint32(why),
            kSpots[_spot].name));
        // Back on his ledge before the evade's walk home (a spot in the antechamber is 69 yd away on foot).
        if (_spot != SPOT_SPAWN)
        {
            Position const home = me->GetHomePosition();
            me->NearTeleportTo(home.GetPositionX(), home.GetPositionY(), home.GetPositionZ(), home.GetOrientation());
            _spot = SPOT_SPAWN;
        }
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        ClearFight();
        BossAI::JustDied(killer);   // BOSS_ARUGAL DONE (the instance lights the hard mode kill flag); summons despawn
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "died", Acore::StringFormat("spot={} moon={}", kSpots[_spot].name,
            _moonStarted));
    }

    // His summons are looks (the ward stalkers, the moonlight shafts): never zoned into combat.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (!me->IsInCombat() || damage >= me->GetHealth())
            return;
        float const after = 100.f * float(me->GetHealth() - damage) / float(std::max<uint32>(1, me->GetMaxHealth()));
        if (MoonriseDue(DungeonKit::IsHeroicMap(me), _moonStarted, after))
            _moonPending = true;
    }

    // The flicker's and the Moonrise cast's ends: the teleport and the moon follow on the next tick (never from inside
    // the spell's own cast handling). A cast that did not finish still lands: the timers are never paused.
    void OnSpellCast(SpellInfo const* spell) override
    {
        NoteCastEnd(spell->Id);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        NoteCastEnd(spell->Id);
    }

    void UpdateAI(uint32 diff) override
    {
        if (_wipePending)
        {
            _wipePending = false;
            if (KillTurnedIfAllTurned())
            {
                EnterEvadeMode(EVADE_REASON_OTHER);
                return;
            }
        }

        // Out of combat too: a `.sfktest` flicker or moon lands.
        if (_portLands)
        {
            _portLands = false;
            FinishPort();
        }
        if (_moonLands)
        {
            _moonLands = false;
            MoonRisen();
        }

        if (!UpdateVictim())
            return;

        if (!_arena.Update(me, diff))
            return;     // he left his room: evading

        // The timeline moves every tick, cast bar or not (R1 S-2).
        _timeline.Advance(Ms(diff));
        Seep();
        UpdateWard(Ms(diff));
        if (_timeline.CurseDue())
        {
            _timeline.CurseDone();
            ArugalsCurse(nullptr);
        }
        if (_moonPending && !_moonStarted)
            StartMoonrise();

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        switch (NextStep(_timeline))
        {
            case Step::ShadowPort:
                ShadowPort(std::nullopt);
                break;
            case Step::Thundershock:
                Thundershock();
                break;
            case Step::VoidBolt:
                VoidBolt();
                break;
            case Step::None:
            default:
                break;
        }

        if (me->HasUnitState(UNIT_STATE_CASTING) || _moonStarted)
            return;     // the moon: he channels, no melee
        DoMeleeAttackIfReady();
    }

    // ---- AR1 / AR6 / AR8: the Worgen's Curse ----------------------------------------------------------------------

    // Adds `delta` curse stacks to `player` (negative removes), updates Feral Power and the looks, and turns the player
    // at 100. Turned and dead players are left alone. Returns the new count.
    uint32 ChangeCurse(Player* player, int32 delta, char const* why)
    {
        if (!player || !player->IsAlive() || IsTurned(player))
            return 0;
        if (!delta)
            return CurseOf(player);
        bool const heroic = DungeonKit::IsHeroicMap(me);
        uint32 const now = DungeonKit::AddStacks(player, CurseSpell(heroic), delta, me, kCurseMax);
        SyncCurseLooks(player, now, heroic);
        if (delta >= 10 || delta <= -10)
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "curse", Acore::StringFormat("player={} delta={} now={} why={}",
                player->GetName(), delta, now, why));
        if (Turns(now))
            Turn(player);
        return now;
    }

    uint32 CurseOf(Player const* player) const
    {
        return player ? DungeonKit::Stacks(player, CurseSpell(DungeonKit::IsHeroicMap(me))) : 0;
    }

    // `.sfktest arugal curse <n>`: sets a player's meter.
    uint32 SetCurse(Player* player, uint32 stacks)
    {
        return ChangeCurse(player, int32(std::min(stacks, kCurseMax)) - int32(CurseOf(player)), "test");
    }

    // AR6: a permanent charm and the Glutton's shape, until he dies, evades or resets.
    void Turn(Player* player)
    {
        if (!player || IsTurned(player))
            return;
        player->CastSpell(player, SPELL_ARUGAL_TURNED_BURST, true);
        me->CastSpell(player, SPELL_ARUGAL_TURNED, true);
        if (!IsTurned(player))
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "turn-failed", "player=" + player->GetName());
            return;
        }
        player->RemoveAurasDueToSpell(SPELL_ARUGAL_CURSE_GLOW);
        player->RemoveAurasDueToSpell(SPELL_ARUGAL_CURSE_TINT);
        _turned.insert(player->GetGUID());
        Talk(YELL_ARUGAL_ANOTHER_FALLS);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "turned", Acore::StringFormat("player={} turned={}",
            player->GetName(), _turned.size()));
        // Handoff section 7 #22: checked on the next tick, outside whatever spell landed the last stacks.
        _wipePending = true;
    }

    // ---- AR2 / AR3 / AR4 / AR5 --------------------------------------------------------------------------------------

    // AR2: the 2 s cast and the registry ring on him; +15 stacks to everyone it hits (no Weakened, ruling 13).
    void Thundershock()
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        _timeline.ThundershockDone();
        DungeonKit::CastBar(me, SPELL_ARUGAL_THUNDERSHOCK_CAST);
        Mechanic::Circle(me, me, kThundershockRadius, kThundershockCast).Damage(kThundershockPct(heroic))
            .Spell(SPELL_ARUGAL_THUNDERSHOCK).Rider(SPELL_ARUGAL_THUNDERSHOCK_STUN).Tag(TAG_THUNDERSHOCK)
            .OnHit(OnArugalHit(kThundershockStacks, "thundershock"));
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "thundershock", Acore::StringFormat("heroic={} spot={}", heroic,
            kSpots[_spot].name));
    }

    // AR3: a real cast on his target (the interrupt list); spell_sfk_arugal_void_bolt sets the damage and the stacks.
    bool VoidBolt(Unit* forced = nullptr)
    {
        if (!forced && _timeline.Now() < _boltRetryAt)
            return false;
        Unit* target = forced ? forced : me->GetVictim();
        if (!target || me->CastSpell(target, SPELL_ARUGAL_VOID_BOLT, false) != SPELL_CAST_OK)
        {
            _boltRetryAt = _timeline.Now() + kBoltRetry;    // out of range or sight, locked out: not every tick
            return false;
        }
        return true;
    }

    // AR4: +10 on a random non-tank within 30 yd (`forced`: that player).
    bool ArugalsCurse(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            rule.maxRange = kCurseCastRange;
            DungeonKit::ExcludeGuids(rule, _turned);
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return false;
        me->CastSpell(target, SPELL_ARUGAL_ARUGALS_CURSE, true);
        Talk(YELL_ARUGAL_RELEASE_YOUR_RAGE);
        uint32 const now = ChangeCurse(target, kCurseCastStacks, "arugals-curse");
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "arugals-curse", Acore::StringFormat("target={} now={}",
            target->GetName(), now));
        return true;
    }

    // AR5: the 1 s flicker, then the next spot (OnSpellCast / OnSpellFailed: FinishPort). `forced`: that spot.
    void ShadowPort(std::optional<SpotId> forced)
    {
        _timeline.PortDone();
        _portTo = forced ? *forced : PickPortSpot(_spot, [](uint32 n) { return urand(0, n - 1); });
        _porting = true;
        if (me->CastSpell(me, SPELL_ARUGAL_SHADOW_PORT, false) != SPELL_CAST_OK)
            FinishPort();
    }

    void FinishPort()
    {
        if (!_porting)
            return;
        _porting = false;
        Spot const& to = kSpots[_portTo];
        float facing = me->GetOrientation();
        if (Unit* victim = me->GetVictim())
            facing = std::atan2(victim->GetPositionY() - to.pos.y, victim->GetPositionX() - to.pos.x);
        Position const at = FloorAt(me, to.pos, facing);
        me->NearTeleportTo(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), at.GetOrientation());
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "shadow-port", Acore::StringFormat("from={} to={} z={:.1f}",
            kSpots[_spot].name, to.name, at.GetPositionZ()));
        _spot = _portTo;
    }

    // ---- AR7: the wards --------------------------------------------------------------------------------------------

    // A ward on the level he stands on (`kind`), placed by the prisoner. None on hard mode or without a prisoner.
    bool PlaceWard(WardKind kind)
    {
        if (HardMode())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "ward-skipped", "hardmode");
            return false;
        }
        Creature* prisoner = Prisoner();
        if (!prisoner)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "ward-skipped", "no prisoner");
            return false;
        }
        EndWard("replaced");

        bool const heroic = DungeonKit::IsHeroicMap(me);
        Point3 const point = kind == WardKind::FullMoon ? WardPointNearest(_spot, GroupCenter())
            : PickWardPoint(_spot, kind, [](uint32 n) { return urand(0, n - 1); });
        Position const at = FloorAt(me, point);
        WardRule const rule = RuleFor(kind);

        BossMechanics::Eligibility who;
        who.auraSpell = CurseSpell(heroic);
        who.minStacks = rule.minStacks;
        who.maxStacks = rule.maxStacks;
        // The registry judges a Stack each second from the dwell's end (MissedStack: once per player in the ledger) and
        // a Soak once (a short soak would otherwise post a group failure every pass); the script owns the pulse.
        if (rule.soak)
        {
            BossMechanics::Ordering most;
            most.auraSpell = who.auraSpell;
            most.ascending = false;
            _wardHandle = Mechanic::Soak(me, at, rule.radius, rule.bodies, kWardDwell)
                .Persistent(kWardLife - kWardDwell, Ms(0)).Eligible(who).Order(most).Tag(TAG_WARD);
        }
        else
            _wardHandle = Mechanic::Stack(me, at, rule.radius, kWardDwell)
                .Persistent(kWardLife - kWardDwell, Ms(1000)).Eligible(who).Tag(TAG_WARD);

        bool const ashcrombe = prisoner->GetEntry() == NPC_SFK_LAIR_ASHCROMBE;
        if (Creature* stalker = me->SummonCreature(NPC_SFK_WARD_STALKER, at, TEMPSUMMON_TIMED_DESPAWN,
            uint32(kWardLife.count()) + 500))
        {
            _wardStalker = stalker->GetGUID();
            stalker->CastSpell(stalker, ashcrombe ? SPELL_ARUGAL_WARD_RUNE : SPELL_ARUGAL_WARD_SMOKE, true);
            prisoner->SetFacingToObject(stalker);
            prisoner->CastSpell(stalker, ashcrombe ? SPELL_ARUGAL_WARD_CAST_ASHCROMBE : SPELL_ARUGAL_WARD_CAST_ADAMANT,
                true);
        }
        _wardAt = at;
        _wardRadius = rule.radius;
        _wardKind = kind;
        _wardPoll = Ms(0);
        _ward.Start();
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "ward", Acore::StringFormat("kind={} x={:.1f} y={:.1f} z={:.1f} "
            "spot={} radius={}", uint32(kind), at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(),
            kSpots[_spot].name, rule.radius));
        return true;
    }

    // ---- AR9: Moonrise (heroic; `.sfktest arugal moonrise` on normal too) -------------------------------------------

    void StartMoonrise()
    {
        if (_moonStarted)
            return;
        _moonStarted = true;
        _moonPending = false;
        _timeline.BeginMoonrise();
        _porting = false;
        me->InterruptNonMeleeSpells(false);
        Talk(YELL_ARUGAL_MOONRISE);
        Talk(EMOTE_ARUGAL_MOONRISE);
        Mechanic::SetPhase(me, kPhaseMoonrise);     // the kill order: Arugal first
        PlaceWard(WardKind::FullMoon);              // "as the cast starts", beside the group, every player eligible
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "moonrise", Acore::StringFormat("health={:.1f} spot={}",
            me->GetHealthPct(), kSpots[_spot].name));
        if (me->CastSpell(me, SPELL_ARUGAL_MOONRISE_CAST, false) != SPELL_CAST_OK)
            MoonRisen();
    }

    void MoonRisen()
    {
        if (!_moonStarted || _timeline.Moon())
            return;
        _timeline.MoonRisen();
        me->CastSpell(me, SPELL_ARUGAL_MOONRISE, true);
        // The moonlit room: a shaft on each spot and over the prisoner's gallery (on the strike / visual stalker).
        if (sObjectMgr->GetCreatureTemplate(NPC_SFK_STRIKE_STALKER))
        {
            std::vector<Point3> shafts;
            for (Spot const& s : kSpots)
                shafts.push_back(s.pos);
            shafts.push_back(kPrisonerPost);
            for (Point3 const& p : shafts)
                if (Creature* shaft = me->SummonCreature(NPC_SFK_STRIKE_STALKER, FloorAt(me, p),
                    TEMPSUMMON_MANUAL_DESPAWN))
                    shaft->CastSpell(shaft, SPELL_ARUGAL_MOONLIGHT, true);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "moonrise-risen", Acore::StringFormat("health={:.1f}",
            me->GetHealthPct()));
    }

    SpotId CurrentSpot() const { return _spot; }
    Timeline const& GetTimeline() const { return _timeline; }

private:
    static constexpr Ms kBoltRetry{ 500 };

    void NoteCastEnd(uint32 spellId)
    {
        if (spellId == SPELL_ARUGAL_SHADOW_PORT && _porting)
            _portLands = true;
        else if (spellId == SPELL_ARUGAL_MOONRISE_CAST && _moonStarted)
            _moonLands = true;
    }

    // Kill order: turned players first, Arugal first during Moonrise (F1); the bots read 206069 as "turned".
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.hostilePlayerAuras = { SPELL_ARUGAL_TURNED };
        d.targets.push_back(BossMechanics::TargetEntry::HostilePlayers(1, BossMechanics::Who::Dps,
            BossMechanics::Condition::Phase(kPhaseNormal)));
        d.targets.push_back(BossMechanics::TargetEntry::HostilePlayers(-1, BossMechanics::Who::Dps,
            BossMechanics::Condition::Phase(kPhaseMoonrise)));
        d.interrupts.emplace_back(NPC_ARUGAL, SPELL_ARUGAL_VOID_BOLT, 2);
        Mechanic::Describe(me, std::move(d));
    }

    bool HardMode() const
    {
        return instance && instance->GetData(DATA_HARD_MODE) != 0;
    }

    Creature* Prisoner() const
    {
        if (!instance)
            return nullptr;
        Creature* prisoner = me->GetMap()->GetCreature(instance->GetGuidData(DATA_LAIR_PRISONER_GUID));
        return prisoner && prisoner->IsAlive() && prisoner->IsInWorld() ? prisoner : nullptr;
    }

    npc_sfk_lair_prisoner* PrisonerAI() const;
    void PrisonerStepIn(npc_sfk_lair_prisoner* prisoner);
    void PrisonerBackToDoor();

    // AR1: the seep, to every fight player who is not turned.
    void Seep()
    {
        PruneTurned();
        uint32 const stacks = _timeline.TakeSeep();
        if (!stacks)
            return;
        ForEachFightPlayer(me, _arena.GetArena(), [this, stacks](Player* player)
        {
            if (!IsTurned(player))
                ChangeCurse(player, int32(stacks), "seep");
        });
    }

    // A turned player who died or was released leaves the turned list, so after a rez Arugal's Curse may pick them
    // again (R2 N-2).
    void PruneTurned()
    {
        for (auto itr = _turned.begin(); itr != _turned.end();)
        {
            Player const* player = ObjectAccessor::GetPlayer(*me, *itr);
            if (!player || !player->IsAlive() || !IsTurned(player))
                itr = _turned.erase(itr);
            else
                ++itr;
        }
    }

    void SyncCurseLooks(Player* player, uint32 curse, bool heroic)
    {
        uint32 const feral = FeralSteps(heroic, curse);
        uint32 const had = DungeonKit::Stacks(player, SPELL_ARUGAL_FERAL_POWER);
        if (feral != had)
            DungeonKit::AddStacks(player, SPELL_ARUGAL_FERAL_POWER, int32(feral) - int32(had), me, kFeralMaxSteps);
        SetLook(player, SPELL_ARUGAL_CURSE_GLOW, ShowsGlow(curse));
        SetLook(player, SPELL_ARUGAL_CURSE_TINT, ShowsTint(curse));
    }

    static void SetLook(Player* player, uint32 spellId, bool on)
    {
        bool const has = player->HasAura(spellId);
        if (on && !has)
            player->AddAura(spellId, player);
        else if (!on && has)
            player->RemoveAurasDueToSpell(spellId);
    }

    // The ward's life: polled every 250 ms; the pulse cleanses everyone inside (turned players excepted).
    void UpdateWard(Ms diff)
    {
        if (_timeline.WardDue())
        {
            _timeline.WardDone();
            PlaceWard(_timeline.Moon() ? WardKind::Moon : WardKind::Normal);
        }
        if (!_ward.Live())
            return;
        _wardPoll += diff;
        if (_wardPoll < kWardPoll)
            return;
        Ms const step = _wardPoll;
        _wardPoll = Ms(0);

        std::vector<Player*> inside;
        std::vector<uint64> ids;
        ForEachFightPlayer(me, _arena.GetArena(), [this, &inside, &ids](Player* player)
        {
            if (IsTurned(player))
                return;
            float const d = DungeonKit::Distance(DungeonKit::PlaneOf(player),
                { _wardAt.GetPositionX(), _wardAt.GetPositionY() });
            if (InsideWard(d, player->GetPositionZ() - _wardAt.GetPositionZ(), _wardRadius))
            {
                inside.push_back(player);
                ids.push_back(player->GetGUID().GetRawValue());
            }
        });
        switch (_ward.Update(ids, step))
        {
            case WardLife::Event::Pulse:
            {
                Creature* stalker = me->GetMap()->GetCreature(_wardStalker);
                std::string names;
                for (Player* player : inside)
                {
                    uint32 const now = ChangeCurse(player, kWardCleanse, "ward");
                    if (stalker)
                        stalker->CastSpell(player, SPELL_ARUGAL_WARD_PULSE, true);
                    names += Acore::StringFormat("{}{}={}", names.empty() ? "" : ",", player->GetName(), now);
                }
                DungeonKit::LogMechanic(kLogDungeon, kBoss, "ward-pulse", Acore::StringFormat("kind={} players={} [{}]",
                    uint32(_wardKind), inside.size(), names));
                EndWard(nullptr);
                break;
            }
            case WardLife::Event::Expired:
                DungeonKit::LogMechanic(kLogDungeon, kBoss, "ward-expired", Acore::StringFormat("kind={}",
                    uint32(_wardKind)));
                EndWard(nullptr);
                break;
            case WardLife::Event::None:
            default:
                break;
        }
    }

    void EndWard(char const* why)
    {
        if (_wardHandle.IsValid())
            Mechanic::Cancel(me, _wardHandle);
        _wardHandle = {};
        if (Creature* stalker = me->GetMap()->GetCreature(_wardStalker))
            stalker->DespawnOrUnsummon(500ms);
        _wardStalker.Clear();
        if (_ward.Live() && why)
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "ward-ended", why);
        _ward.Stop();
    }

    // The centre of the fight players on his level (the Moonrise ward goes beside them).
    Vec2 GroupCenter()
    {
        float x = 0.f, y = 0.f;
        uint32 n = 0;
        ForEachFightPlayer(me, _arena.GetArena(), [this, &x, &y, &n](Player* player)
        {
            if (IsTurned(player) || std::fabs(player->GetPositionZ() - me->GetPositionZ()) > 6.f)
                return;
            x += player->GetPositionX();
            y += player->GetPositionY();
            ++n;
        });
        if (!n)
            return DungeonKit::PlaneOf(me);
        return { x / float(n), y / float(n) };
    }

    // Handoff section 7 #22: when every living player of the fight is turned, the turned players die (the caller then
    // resets the fight). True when it killed them.
    bool KillTurnedIfAllTurned()
    {
        uint32 living = 0;
        std::vector<Player*> turned;
        ForEachFightPlayer(me, _arena.GetArena(), [&living, &turned](Player* player)
        {
            ++living;
            if (IsTurned(player))
                turned.push_back(player);
        });
        if (!AllTurned(living, uint32(turned.size())))
            return false;
        _wiping = true;
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "all-turned", Acore::StringFormat("players={}", turned.size()));
        for (Player* player : turned)
        {
            player->RemoveAurasDueToSpell(SPELL_ARUGAL_TURNED);
            if (player->IsAlive())
                Unit::Kill(me, player);
        }
        _wiping = false;
        return true;
    }

    // The fight's end (death, evade, reset): every turned player is released and every curse aura removed.
    void ClearFight()
    {
        EndWard(nullptr);
        _arena.Reset();
        _timeline = Timeline{};
        _porting = false;
        _portLands = false;
        _moonLands = false;
        _boltRetryAt = Ms(0);
        _moonStarted = false;
        _moonPending = false;
        _wipePending = false;
        _killLineReady = Ms(0);
        _turned.clear();
        me->RemoveAurasDueToSpell(SPELL_ARUGAL_MOONRISE);
        if (instance)
            for (uint32 spell : { uint32(SPELL_ARUGAL_TURNED), uint32(SPELL_ARUGAL_WORGENS_CURSE),
                uint32(SPELL_ARUGAL_WORGENS_CURSE_HEROIC), uint32(SPELL_ARUGAL_FERAL_POWER),
                uint32(SPELL_ARUGAL_CURSE_GLOW), uint32(SPELL_ARUGAL_CURSE_TINT) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    // A registry OnHit that reaches this AI through the map (guids only in the lambda): the curse stacks of a hit.
    std::function<void(Unit*)> OnArugalHit(int32 stacks, char const* why)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, stacks, why](Unit* hit)
        {
            Player* player = hit ? hit->ToPlayer() : nullptr;
            Creature* arugal = map ? map->GetCreature(guid) : nullptr;
            if (!player || !arugal || !arugal->IsAlive() || !arugal->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_archmage_arugal_rework*>(arugal->AI()))
                ai->ChangeCurse(player, stacks, why);
        };
    }

    DungeonKit::ArenaGuard _arena;
    Timeline _timeline;
    SpotId _spot = SPOT_SPAWN;
    SpotId _portTo = SPOT_SPAWN;
    bool _porting = false;
    bool _portLands = false;
    bool _moonLands = false;
    Ms _boltRetryAt{ 0 };
    bool _moonStarted = false;
    bool _moonPending = false;
    bool _wipePending = false;
    bool _wiping = false;
    Ms _killLineReady{ 0 };
    GuidSet _turned;

    WardLife _ward;
    BossMechanics::MechanicHandle _wardHandle;
    ObjectGuid _wardStalker;
    Position _wardAt;
    float _wardRadius = kWardRadius;
    WardKind _wardKind = WardKind::Normal;
    Ms _wardPoll{ 0 };
};

// The lair prisoner (300513 Ashcrombe / 300514 Adamant, npc_sfk_lair_prisoner): the instance summons it at the lair
// door on Nandos's DONE (DATA_LAIR_PRISONER_GUID). Passive, not attackable, ignored by creatures (unit flags in
// archmage_arugal.py).
struct npc_sfk_lair_prisoner : public ScriptedAI
{
    enum class State : uint8
    {
        Waiting,        // by the lair door (gossip)
        SteppingIn,     // walking to the gap, then the jump
        Posted,         // on the gallery: places the wards
        Leaving,        // Face Him Alone chosen (S10)
    };

    explicit npc_sfk_lair_prisoner(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        _state = State::Waiting;
        // A reload with Face Him Alone already chosen: the prisoner is gone for this instance.
        if (InstanceScript* instance = me->GetInstanceScript(); instance && instance->GetData(DATA_HARD_MODE))
            me->DespawnOrUnsummon();
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE || id != kPrisonerPointJumpOff || _state != State::SteppingIn)
            return;
        // The gap: a jump across onto the gallery, as a player would make it.
        DungeonKit::JumpTo(me, FloorAt(me, kPrisonerPost), kPrisonerJumpSpeedXY, kPrisonerJumpMinSpeedZ);
        scheduler.Schedule(kPrisonerJumpLand, [this](TaskContext)
        {
            Posted();
        });
    }

    // Arugal's pull: the line, then the way in (a timeout puts it on the post if the path fails).
    void StepIn()
    {
        if (_state != State::Waiting)
            return;
        _state = State::SteppingIn;
        Talk(SAY_PRISONER_LAIR_PULL);
        me->RemoveNpcFlag(UNIT_NPC_FLAG_GOSSIP);
        me->GetMotionMaster()->MovePoint(kPrisonerPointJumpOff, FloorAt(me, kPrisonerJumpOff));
        scheduler.Schedule(kPrisonerStepInTimeout, [this](TaskContext)
        {
            if (_state != State::SteppingIn)
                return;
            Position const post = FloorAt(me, kPrisonerPost);
            me->NearTeleportTo(post.GetPositionX(), post.GetPositionY(), post.GetPositionZ(), 0.f);
            Posted();
        });
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "prisoner-step-in", "entry=" + std::to_string(me->GetEntry()));
    }

    // A wipe: back by the lair door, gossip again.
    void BackToDoor()
    {
        if (_state == State::Leaving)
            return;
        scheduler.CancelAll();
        _state = State::Waiting;
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        me->NearTeleportTo(kLairPrisonerWait.x, kLairPrisonerWait.y, kLairPrisonerWait.z, kLairPrisonerWaitFacing);
        me->SetNpcFlag(UNIT_NPC_FLAG_GOSSIP);
    }

    // Face Him Alone (S10): its line, then it leaves for good.
    void LeaveForHardMode()
    {
        if (_state == State::Leaving)
            return;
        _state = State::Leaving;
        scheduler.CancelAll();
        me->RemoveNpcFlag(UNIT_NPC_FLAG_GOSSIP);
        Talk(SAY_PRISONER_HARD_MODE);
        if (me->GetEntry() == NPC_SFK_LAIR_ASHCROMBE)
        {
            me->CastSpell(me, SPELL_ASHCROMBES_TELEPORT, false);
            me->DespawnOrUnsummon(3s);
        }
        else
        {
            me->GetMotionMaster()->MovePoint(kPrisonerPointLeave, kNandosOpenPoint.x, kNandosOpenPoint.y,
                kNandosOpenPoint.z);
            me->DespawnOrUnsummon(4s);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "prisoner-leaves", "entry=" + std::to_string(me->GetEntry()));
    }

    bool IsPosted() const { return _state == State::Posted; }
    State GetState() const { return _state; }

private:
    void Posted()
    {
        _state = State::Posted;
        if (InstanceScript* instance = me->GetInstanceScript())
            if (Creature* arugal = instance->GetCreature(DATA_ARUGAL_GUID))
                me->SetFacingToObject(arugal);
    }

    State _state = State::Waiting;
};

npc_sfk_lair_prisoner* boss_archmage_arugal_rework::PrisonerAI() const
{
    Creature* prisoner = Prisoner();
    return prisoner && prisoner->IsAIEnabled ? dynamic_cast<npc_sfk_lair_prisoner*>(prisoner->AI()) : nullptr;
}

void boss_archmage_arugal_rework::PrisonerStepIn(npc_sfk_lair_prisoner* prisoner)
{
    if (prisoner && !HardMode())
        prisoner->StepIn();
}

void boss_archmage_arugal_rework::PrisonerBackToDoor()
{
    if (npc_sfk_lair_prisoner* prisoner = PrisonerAI())
        prisoner->BackToDoor();
}

// The prisoner's gossip: its menu from the DB (body text), then S10's hook (LairPrisoner.h).
class npc_sfk_lair_prisoner_script : public CreatureScript
{
public:
    npc_sfk_lair_prisoner_script() : CreatureScript("npc_sfk_lair_prisoner") { }

    CreatureAI* GetAI(Creature* creature) const override
    {
        return DungeonKit::GetReworkAI<ShadowfangKeepRework::kInstanceScriptName, npc_sfk_lair_prisoner>(creature);
    }

    bool OnGossipHello(Player* player, Creature* creature) override
    {
        player->PrepareGossipMenu(creature, creature->GetGossipMenuId(), true);
        if (SfkLairPrisoner::GossipHooks const& hooks = GossipHookStore(); hooks.onHello)
            hooks.onHello(player, creature);
        player->SendPreparedGossip(creature);
        return true;
    }

    bool OnGossipSelect(Player* player, Creature* creature, uint32 sender, uint32 action) override
    {
        SfkLairPrisoner::GossipHooks const& hooks = GossipHookStore();
        return hooks.onSelect && hooks.onSelect(player, creature, sender, action);
    }
};

namespace SfkLairPrisoner
{
    void SetGossipHooks(GossipHooks hooks)
    {
        GossipHookStore() = std::move(hooks);
    }

    bool LeaveForHardMode(Creature* prisoner)
    {
        if (!IsLairPrisoner(prisoner) || !prisoner->IsAIEnabled)
            return false;
        auto* ai = dynamic_cast<npc_sfk_lair_prisoner*>(prisoner->AI());
        if (!ai)
            return false;
        ai->LeaveForHardMode();
        return true;
    }

    bool IsLairPrisoner(Creature const* creature)
    {
        return creature
            && (creature->GetEntry() == NPC_SFK_LAIR_ASHCROMBE || creature->GetEntry() == NPC_SFK_LAIR_ADAMANT);
    }
}

// AR3 Void Bolt 206066: 15% / 25% of the reference row on his target (RefFlat at launch, so the target's defensives
// count; the spell ignores caster modifiers), and +3 curse stacks when it lands.
class spell_sfk_arugal_void_bolt : public SpellScript
{
    PrepareSpellScript(spell_sfk_arugal_void_bolt);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetCaster())
        {
            float const pct = kVoidBoltPct(DungeonKit::IsHeroicMap(caster));
            SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));   // R2 N-1
        }
    }

    void AddStacks()
    {
        Player* target = GetHitUnit() ? GetHitUnit()->ToPlayer() : nullptr;
        Creature* caster = GetCaster() ? GetCaster()->ToCreature() : nullptr;
        if (!target || !caster || !caster->IsAIEnabled)
            return;
        if (auto* ai = dynamic_cast<boss_archmage_arugal_rework*>(caster->AI()))
            ai->ChangeCurse(target, kVoidBoltStacks, "void-bolt");
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_sfk_arugal_void_bolt::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterHit += SpellHitFn(spell_sfk_arugal_void_bolt::AddStacks);
    }
};

namespace
{
    boss_archmage_arugal_rework* FindArugal(ChatHandler* handler)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_ARUGAL);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_archmage_arugal_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("Archmage Arugal does not run the Shadowfang Keep rework script.");
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetPlayer();
    }

    bool HandleInfo(ChatHandler* handler)
    {
        if (!SfkTest::ShowBossInfo(handler, NPC_ARUGAL, BOSS_ARUGAL))
            return false;
        if (boss_archmage_arugal_rework* ai = FindArugal(handler))
        {
            Timeline const& t = ai->GetTimeline();
            handler->PSendSysMessage("Spot {}; fight time {} ms; next Thundershock {} / Shadow Port {} / curse {} / "
                "ward {} ms; moon {}.", kSpots[ai->CurrentSpot()].name, t.Now().count(), t.NextThundershock().count(),
                t.NextPort().count(), t.NextCurse().count(), t.NextWard().count(), t.Moon() ? "risen" : "no");
        }
        return true;
    }

    bool HandleCurse(ChatHandler* handler, Optional<uint32> stacks)
    {
        boss_archmage_arugal_rework* ai = FindArugal(handler);
        if (!ai)
            return false;
        Player* target = TestTarget(handler);
        uint32 const now = ai->SetCurse(target, stacks.value_or(20));
        handler->PSendSysMessage("Worgen's Curse on {}: {} stacks (wards from 20; 100 turns).", target->GetName(), now);
        return true;
    }

    bool HandleThundershock(ChatHandler* handler)
    {
        boss_archmage_arugal_rework* ai = FindArugal(handler);
        if (!ai)
            return false;
        ai->Thundershock();
        handler->SendSysMessage("Thundershock: 2 s cast, 8 yd around him (30%, 1.5 s stun, +15 stacks).");
        return true;
    }

    bool HandleVoidBolt(ChatHandler* handler)
    {
        boss_archmage_arugal_rework* ai = FindArugal(handler);
        if (!ai)
            return false;
        if (!ai->VoidBolt(TestTarget(handler)))
        {
            handler->SendErrorMessage("Void Bolt did not start (range 40, line of sight, casting, locked out).");
            return false;
        }
        handler->SendSysMessage("Void Bolt: 3 s cast, interruptible (15% / 25% Shadow, +3 stacks).");
        return true;
    }

    bool HandleCurseCast(ChatHandler* handler)
    {
        boss_archmage_arugal_rework* ai = FindArugal(handler);
        if (!ai)
            return false;
        if (!ai->ArugalsCurse(TestTarget(handler)))
        {
            handler->SendErrorMessage("Arugal's Curse found no target.");
            return false;
        }
        return true;
    }

    bool HandlePort(ChatHandler* handler, Optional<uint32> spot)
    {
        boss_archmage_arugal_rework* ai = FindArugal(handler);
        if (!ai)
            return false;
        std::optional<SpotId> forced;
        if (spot)
        {
            if (*spot >= kSpotCount || *spot == ai->CurrentSpot())
            {
                handler->SendErrorMessage("Spots: 0 spawn, 1 7586, 2 7136 (not the current one).");
                return false;
            }
            forced = static_cast<SpotId>(*spot);
        }
        ai->ShadowPort(forced);
        handler->SendSysMessage("Shadow Port: 1 s flicker, then the next spot.");
        return true;
    }

    bool HandleWard(ChatHandler* handler, Optional<std::string> kind)
    {
        boss_archmage_arugal_rework* ai = FindArugal(handler);
        if (!ai)
            return false;
        WardKind k = WardKind::Normal;
        if (kind && *kind == "full")
            k = WardKind::FullMoon;
        else if (kind && *kind == "moon")
            k = WardKind::Moon;
        if (!ai->PlaceWard(k))
        {
            handler->SendErrorMessage("No ward: hard mode, or no lair prisoner (kill Nandos or .sfktest instance "
                "prisoner first).");
            return false;
        }
        handler->SendSysMessage("Ward placed on his level (10 s; 3 s inside pulses -10 stacks).");
        return true;
    }

    bool HandleMoonrise(ChatHandler* handler)
    {
        boss_archmage_arugal_rework* ai = FindArugal(handler);
        if (!ai)
            return false;
        ai->StartMoonrise();
        handler->SendSysMessage("Moonrise: 3 s cast, last full ward, then +2 stacks per second (works on normal for "
            "tests).");
        return true;
    }

    bool HandleTurn(ChatHandler* handler)
    {
        boss_archmage_arugal_rework* ai = FindArugal(handler);
        if (!ai)
            return false;
        Player* target = TestTarget(handler);
        ai->Turn(target);
        handler->PSendSysMessage("Turned: {} ({}).", target->GetName(), IsTurned(target) ? "charmed" : "failed");
        return true;
    }

    // Where the GM stands against the spots and the wards of each level (the playtest's .gps checks).
    bool HandleSpots(ChatHandler* handler)
    {
        if (!SfkTest::RequireShadowfangKeep(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p = DungeonKit::PlaneOf(gm);
        for (Spot const& s : kSpots)
        {
            handler->PSendSysMessage("Spot {} ({:.1f}, {:.1f}, {:.1f}): {:.1f} yd, dz {:.1f}", s.name, s.pos.x, s.pos.y,
                s.pos.z, DungeonKit::Distance(p, s.pos.XY()), gm->GetPositionZ() - s.pos.z);
            for (std::size_t i = 0; i < s.wardCount; ++i)
                handler->PSendSysMessage("  ward {} ({:.1f}, {:.1f}): {:.1f} yd", i, s.wards[i].x, s.wards[i].y,
                    DungeonKit::Distance(p, s.wards[i].XY()));
        }
        handler->PSendSysMessage("In Arugal's room: {}", ArugalArena().Contains(p, gm->GetPositionZ()) ? "yes" : "no");
        return true;
    }

    bool HandlePrisoner(ChatHandler* handler)
    {
        if (!SfkTest::RequireShadowfangKeep(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        Creature* prisoner = instance ? instance->instance->GetCreature(instance->GetGuidData(DATA_LAIR_PRISONER_GUID))
            : nullptr;
        if (!prisoner)
        {
            handler->SendErrorMessage("No lair prisoner (it comes when Nandos dies).");
            return false;
        }
        auto* ai = prisoner->IsAIEnabled ? dynamic_cast<npc_sfk_lair_prisoner*>(prisoner->AI()) : nullptr;
        if (!ai)
        {
            handler->SendErrorMessage("The lair prisoner does not run its script.");
            return false;
        }
        if (ai->GetState() == npc_sfk_lair_prisoner::State::Waiting)
        {
            ai->StepIn();
            handler->SendSysMessage("The prisoner steps in (walk to the gap, jump onto the gallery).");
        }
        else
        {
            ai->BackToDoor();
            handler->SendSysMessage("The prisoner is back by the lair door.");
        }
        return true;
    }

    ChatCommandTable const& ArugalTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",         HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "curse",        HandleCurse,        SEC_GAMEMASTER, Console::No },
            { "thundershock", HandleThundershock, SEC_GAMEMASTER, Console::No },
            { "voidbolt",     HandleVoidBolt,     SEC_GAMEMASTER, Console::No },
            { "cursecast",    HandleCurseCast,    SEC_GAMEMASTER, Console::No },
            { "port",         HandlePort,         SEC_GAMEMASTER, Console::No },
            { "ward",         HandleWard,         SEC_GAMEMASTER, Console::No },
            { "moonrise",     HandleMoonrise,     SEC_GAMEMASTER, Console::No },
            { "turn",         HandleTurn,         SEC_GAMEMASTER, Console::No },
            { "spots",        HandleSpots,        SEC_GAMEMASTER, Console::No },
            { "prisoner",     HandlePrisoner,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_archmage_arugal_rework()
{
    RegisterDungeonReworkCreatureAI(boss_archmage_arugal_rework, ShadowfangKeepRework::kInstanceScriptName);
    new npc_sfk_lair_prisoner_script();
    RegisterSpellScript(spell_sfk_arugal_void_bolt);
    SfkTest::RegisterBoss("arugal", ArugalTestCommands());
}
