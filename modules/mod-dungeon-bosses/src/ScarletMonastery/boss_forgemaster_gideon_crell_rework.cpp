/*
 * mod-dungeon-bosses, Scarlet Monastery D9: Forgemaster Gideon Crell, the Armorer (300940), "Forged to Order". Build
 * spec: docs/dungeons/scarlet-monastery-3-armory.md "Forgemaster Gideon Crell, the Armorer" (AR1-AR8, Build spec),
 * handoff section 3.5 row D9, 3.6, 3.8, 7 #28 A, 7 #29 A. A new boss (no stock script to replace). Pure rules:
 * CrellLogic.h. Wave 2: the AI registers only once kWave2Bound flips (W2-SETUP); `.dbtest sm crell` registers now.
 *
 *   AR1 The Order       at 6 s, then every 30 s (heroic 25 s): a yell ("A blade..." / "Plate..."), three steps 5 s
 *                       apart (heroic 4 s), then the Issue of the piece at T+15 (T+12.5). Normal alternates the pieces,
 *                       a Blade first; heroic issues both every order
 *   AR2 Heat            10 sparks of 5 yd (heroic 16 of 4 yd) on random floor spots, a 2.5 s marker, 30% (45%) Fire
 *                       and Weakened. Heroic: each leaves a 3 yd slag pool, 10% a second, until the Quench burst (AR2a)
 *   AR3 Hammer          a 2.5 s cast; the donut from the anvil's 8 yd circle to the walls, then 2 s (1.5 s) later the
 *                       anvil circle itself: in, then out. 30% (45%) Physical and Weakened each
 *   AR4 Quench          steam 10 yd round the trough for 8 s, 8% (12%) Fire a second. Heroic: every slag pool swells
 *                       2.5 s and bursts, 5 yd, 45% Fire and Weakened (AR4a)
 *   AR5 Temper          (heroic) a 2.5 s interruptible cast before the Issue: kicked, the piece is flawed (Blade 8 s,
 *                       plate 12.5k); missed, masterwork (Blade 25 s, plate 50k)
 *   AR-Bl Forged Blade  15 s: a 90 degree cleave 8 yd in front of him every 6 s (the tank 15% (25%) of the tank row,
 *                       anyone else 30% (45%) and Weakened); a 6 yd spread lasts the window
 *   AR7 Proving Strike  2 s after the Blade's Issue (heroic: every 10 s while held) he dashes through every player in a
 *                       random order: a 3 yd line to 5 yd past each, 2 s then 1 s markers, 30% (45%) then 20% (30%)
 *   AR-Pl Red-Hot Plate absorbs 5k (heroic 25k); 20% of each absorbed hit burns its attacker back as Fire; Sunder,
 *                       Expose Armor and Faerie Fire tear off 500 (no burn)
 *   AR8 Popping Rivets  each quarter (heroic eighth) of the plate broken: a 4 yd circle near a random player, a 2 s
 *                       marker, 30% (45%) Fire and Weakened
 *   AR6 The Supply Line (heroic, set dressing) a Scarlet Recruit walks from the Armor Crate to his counter with every
 *                       order, takes a copy of the piece at the Issue and marches out toward the upper hall
 *
 * A wipe despawns the recruits and the looks, cancels every spark, slag pool, steam, line and rivet, and resets him and
 * his order count (the first order is again a Blade); the encounter completes on his death and the recruits go with
 * him. The forge, the anvil and the trough are database objects (scenery the script never touches). Every percent hit
 * is a percent of the reference row (his spells ignore caster modifiers): the registry's shapes, and the kit's
 * spell_dungeon_refflat_damage on the cleave's tank hit. Boss data: kill order Crell (the recruits are not
 * selectable); interrupt list: Temper (heroic, expected); no dispels, no purges. Every firing logs one INFO line "sm
 * crell <mechanic> ..." (module.dungeonbosses); `.dbtest sm crell ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CrellLogic.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmCrell;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "crell";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    Position At(Vec2 p, float z = kFloorZ, float o = 0.f)
    {
        return Position(p.x, p.y, z, o);
    }

    Position At(Point3 const& p, float o = 0.f)
    {
        return Position(p.x, p.y, p.z, o);
    }

    // The storeroom's floor: every spot the bots plan for a spark, a pool, the steam, a line or a rivet stays on it
    // (rule 12).
    BossMechanics::SpotBounds StoreroomBounds()
    {
        std::vector<Position> points;
        for (Vec2 const& p : kOutline)
            points.emplace_back(p.x, p.y, kFloorZ);
        return BossMechanics::SpotBounds().Polygon(std::move(points), kOutlineZMin, kOutlineZMax);
    }

    char const* QualityName(Quality quality)
    {
        return quality == Quality::Flawed ? "flawed" : quality == Quality::Masterwork ? "masterwork" : "standard";
    }

    char const* StepName(Step step)
    {
        switch (step)
        {
            case Step::Heat:    return "heat";
            case Step::Hammer:  return "hammer";
            case Step::Quench:  return "quench";
            case Step::Temper:  return "temper";
            case Step::Issue:   return "issue";
            default:            return "done";
        }
    }

    // The armor tear (AR-Pl): one of the named stock first ranks, or any spell lowering armor by a resistance aura
    // with a negative amount (a reworked Sunder still tears).
    bool TearsArmor(SpellInfo const* spell)
    {
        if (!spell)
            return false;
        SpellInfo const* first = spell->GetFirstRankSpell();
        if (IsNamedArmorTear(first ? first->Id : spell->Id))
            return true;
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            SpellEffectInfo const& effect = spell->Effects[i];
            if (effect.Effect != SPELL_EFFECT_APPLY_AURA)
                continue;
            if (effect.ApplyAuraName != SPELL_AURA_MOD_RESISTANCE
                && effect.ApplyAuraName != SPELL_AURA_MOD_RESISTANCE_PCT)
                continue;
            if ((effect.MiscValue & SPELL_SCHOOL_MASK_NORMAL) && effect.CalcValue() < 0)
                return true;
        }
        return false;
    }
}

// Forgemaster Gideon Crell 300940
struct boss_forgemaster_gideon_crell_rework : public BossAI
{
    explicit boss_forgemaster_gideon_crell_rework(Creature* creature)
        : BossAI(creature, BOSS_CRELL), _arena(StoreroomArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _heroic = IsHeroicMap(me);
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_CRELL;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_PULL);

        _orderClock.Start(_clockMs, kOrderBeat(_heroic).firstMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        Talk(SAY_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("orders={} heats={} hammers={} quenches={} chains={} cleaves={} plates={} rivets={} "
                "burned={} torn={} temper-kicked={} masterwork={} killer={}", _orderCount, _heats, _hammers, _quenches,
                _chains, _cleaves, _plates, _rivetsTotal, _burnedTotal, _tornTotal, _tempersKicked, _masterworks,
                killer ? killer->GetName() : "none"));
        Cleanup(true);
    }

    // A 5 s cooldown (Herod's stock row 7 shape): a wipe yells once, not five times.
    void KilledUnit(Unit* victim) override
    {
        if (!victim || !victim->IsPlayer() || _clockMs < _killLineReadyMs)
            return;
        _killLineReadyMs = _clockMs + kKillLineCooldownMs;
        Talk(SAY_KILL);
    }

    // The summons are his (the recruits and the look stalkers): they go with his reset and death, never into a fight.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // AR5: a kick or a silence stopped the Temper. His own stops (an evade, his death, a reset) are not interrupts:
    // Cleanup drops the cast's state before the engine interrupts it.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_AR_TEMPER && _temper.active)
            TemperEnded(Quality::Flawed, "interrupted");
    }

    // AR5: the Temper went off.
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell && spell->Id == SPELL_AR_TEMPER && _temper.active)
            TemperEnded(Quality::Masterwork, "landed");
    }

    // AR-Pl: Sunder Armor, Expose Armor and Faerie Fire (any player's armor-lowering spell) tear 500 off the plate.
    void SpellHit(Unit* caster, SpellInfo const* spell) override
    {
        BossAI::SpellHit(caster, spell);
        if (!caster || !caster->IsControlledByPlayer() || !_plate.active || !TearsArmor(spell))
            return;
        TearPlate(caster, spell->Id);
    }

    // AR-Pl: the plate broke (its absorb ran out) or was taken off.
    void OnAuraRemove(AuraApplication* aurApp, AuraRemoveMode mode) override
    {
        if (!aurApp || !aurApp->GetBase() || aurApp->GetBase()->GetId() != SPELL_AR_RED_HOT_PLATE || !_plate.active)
            return;
        _plate.active = false;
        if (mode == AURA_REMOVE_BY_ENEMY_SPELL)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "plate-broken",
                Acore::StringFormat("plate={} broken={} rivets={} burned={} torn={} after={}ms", _plate.total,
                    _plate.broken, _plate.rivets, _plate.burned, _plate.torn, _clockMs - _plate.startMs));
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!UpdateVictim())
            return;
        // The guard turns him to a target on his arena; during a dash chain he holds no target (the chain moves him).
        if (!_chain.active && !_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        UpdateTemper();
        UpdateChain();
        UpdateOrders();
        UpdateBlade();
        if (_chain.active || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR1 The Order
    // ----------------------------------------------------------------------------------------------------------------

    // A due order starts once the last one has issued; its steps then fire in turn. A cast step (the Hammer, the
    // Temper) waits while he dashes or casts; the Issue waits for the Temper's end.
    void UpdateOrders()
    {
        if (!_order.Active() && _orderClock.Due(_clockMs))
        {
            _orderClock.Fired(_clockMs, kOrderBeat(_heroic).everyMs);
            StartOrder();
        }
        if (!_order.Due(_clockMs))
            return;
        Step const step = _order.Current();
        if (StepIsCast(step) && (_chain.active || _temper.active || me->HasUnitState(UNIT_STATE_CASTING)))
            return;
        if (step == Step::Issue && _temper.active)
            return;
        _order.Fired(_clockMs);
        switch (step)
        {
            case Step::Heat:    Heat(); break;
            case Step::Hammer:  Hammer(); break;
            case Step::Quench:  Quench(); break;
            case Step::Temper:  StartTemper(); break;
            case Step::Issue:   Issue(PiecesOf(_order.Number(), _heroic)); break;
            default:            break;
        }
    }

    // The yell (heroic: both lines), the recruit (heroic), then the Heat at once.
    void StartOrder()
    {
        ++_orderCount;
        _order.Start(_clockMs, _orderCount, _heroic);
        _quality = Quality::Standard;
        me->RemoveAurasDueToSpell(SPELL_AR_FLAWED);
        me->RemoveAurasDueToSpell(SPELL_AR_MASTERWORK);
        uint8 const pieces = PiecesOf(_orderCount, _heroic);
        if (pieces & PIECE_BLADE)
            Talk(SAY_ORDER_BLADE);
        if (pieces & PIECE_PLATE)
            Talk(SAY_ORDER_PLATE);
        if (_heroic)
            SendRecruit();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "order",
            Acore::StringFormat("n={} blade={} plate={}", _orderCount, (pieces & PIECE_BLADE) ? 1 : 0,
                (pieces & PIECE_PLATE) ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR2 Heat (and AR2a Slag)
    // ----------------------------------------------------------------------------------------------------------------

    // Sparks shower the floor: circles at random floor spots (never aimed at a player), a 2.5 s marker; each one's
    // burst plays where it lands, and on heroic it leaves a slag pool there.
    void Heat()
    {
        float const radius = kSparkRadiusYd(_heroic);
        float const pct = kSparkPct(_heroic);
        std::vector<Vec2> const spots = PickSparks(kSparkCount(_heroic), []() { return frand(0.f, 1.f); });
        for (Vec2 const& spot : spots)
        {
            MechanicRef ref = Mechanic::Circle(me, At(spot), radius, Ms(kSparkWarnMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_AR_SPARK).Weakened()
                .Within(StoreroomBounds()).Tag(TAG_AR_SPARK)
                .OnResolve(OnCrell([spot](boss_forgemaster_gideon_crell_rework& ai,
                    BossMechanics::ResolveResult const&)
                {
                    ai.SparkLands(spot);
                }));
            if (ref.IsValid())
                Track(ref.Handle());
        }
        ++_heats;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "heat",
            Acore::StringFormat("order={} sparks={} radius={:.0f} pct={:.0f} slag={}", _order.Number(), spots.size(),
                radius, pct, _heroic ? 1 : 0));
    }

    void SparkLands(Vec2 spot)
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        me->CastSpell(spot.x, spot.y, kFloorZ, SPELL_AR_SPARK_LOOK, true);
        if (_heroic)
            AddSlagPool(spot);
    }

    // AR2a: a 3 yd pool of 10% a second where the spark landed, until the Quench bursts it.
    void AddSlagPool(Vec2 spot)
    {
        MechanicRef ref = Mechanic::Circle(me, At(spot), kSlagRadiusYd, Ms(kSlagTickMs));
        ref.Persistent(Ms(kSlagMaxMs), Ms(kSlagTickMs)).Damage(kSlagPct).TankDamage(kSlagPct)
            .School(SPELL_SCHOOL_FIRE).Spell(SPELL_AR_SLAG).NoFillTimer().Within(StoreroomBounds()).Tag(TAG_AR_SLAG);
        if (!ref.IsValid())
            return;
        SlagPool pool;
        pool.spot = spot;
        pool.handle = ref.Handle();
        if (Creature* look = SummonLook(At(spot), kSlagMaxMs))
        {
            look->CastSpell(look, SPELL_AR_SLAG_LOOK, true);
            pool.look = look->GetGUID();
        }
        _slag.push_back(pool);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR3 Hammer
    // ----------------------------------------------------------------------------------------------------------------

    // The 2.5 s cast; the donut from the anvil's circle to the walls lands at its end, then the anvil circle itself
    // (registered as the donut lands: the Deadmines Harpoon Sweep then Haft Slam chain).
    void Hammer()
    {
        me->StopMoving();
        DungeonKit::CastBar(me, SPELL_AR_HAMMER_CAST);
        float const pct = kHammerPct(_heroic);
        MechanicRef ref = Mechanic::Donut(me, At(kAnvil), kAnvilCircleYd, kHammerOuterYd, Ms(kHammerCastMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_AR_HAMMER_RING).Weakened()
            .Within(StoreroomBounds()).Tag(TAG_AR_HAMMER_RING)
            .OnResolve(OnCrell([](boss_forgemaster_gideon_crell_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.AnvilBursts(r);
            }));
        if (ref.IsValid())
            Track(ref.Handle());
        ++_hammers;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hammer",
            Acore::StringFormat("order={} pct={:.0f} follow-up={}ms", _order.Number(), pct,
                kHammerFollowUpMs(_heroic)));
    }

    void AnvilBursts(BossMechanics::ResolveResult const& ring)
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        me->CastSpell(kAnvil.x, kAnvil.y, kAnvil.z, SPELL_AR_ANVIL_STRIKE_LOOK, true);
        float const pct = kHammerPct(_heroic);
        MechanicRef ref = Mechanic::Circle(me, At(kAnvil), kAnvilCircleYd, Ms(kHammerFollowUpMs(_heroic)));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_AR_HAMMER_BURST).Weakened()
            .Within(StoreroomBounds()).Tag(TAG_AR_HAMMER_BURST)
            .OnResolve(OnCrell([](boss_forgemaster_gideon_crell_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.AnvilCircleLands(r);
            }));
        if (ref.IsValid())
            Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hammer-ring", Acore::StringFormat("hits={}",
            ring.hits.size()));
    }

    void AnvilCircleLands(BossMechanics::ResolveResult const& circle)
    {
        if (me->IsAlive() && me->IsEngaged())
            me->CastSpell(kAnvil.x, kAnvil.y, kAnvil.z, SPELL_AR_ANVIL_STRIKE_LOOK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "anvil-burst", Acore::StringFormat("hits={}",
            circle.hits.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR4 Quench (and AR4a Slag Burst)
    // ----------------------------------------------------------------------------------------------------------------

    // Steam rolls out of the trough for 8 s (lingering, no Weakened); the tank walks him out of it. Heroic: every slag
    // pool swells and bursts.
    void Quench()
    {
        float const pct = kSteamPct(_heroic);
        MechanicRef ref = Mechanic::Circle(me, At(kTrough), kSteamRadiusYd, Ms(kSteamWarnMs));
        ref.Persistent(Ms(kSteamMs), Ms(kSteamTickMs)).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE)
            .Spell(SPELL_AR_STEAM).NoFillTimer().Within(StoreroomBounds()).Tag(TAG_AR_STEAM);
        if (ref.IsValid())
            Track(ref.Handle());
        if (Creature* look = SummonLook(At(kTrough), kSteamWarnMs + kSteamMs))
            look->CastSpell(look, SPELL_AR_STEAM_LOOK, true);
        uint32 const pools = static_cast<uint32>(_slag.size());
        if (_heroic)
            BurstSlag();
        ++_quenches;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "quench",
            Acore::StringFormat("order={} pct={:.0f} pools={}", _order.Number(), pct, pools));
    }

    // AR4a: every pool standing now swells (a 2.5 s marker) and bursts, 5 yd; the pool goes with its burst.
    void BurstSlag()
    {
        std::vector<SlagPool> pools;
        pools.swap(_slag);
        for (SlagPool const& pool : pools)
        {
            Vec2 const spot = pool.spot;
            MechanicHandle const poolHandle = pool.handle;
            Track(poolHandle);      // a wipe or death before the burst resolves still cancels the pool (Cleanup)
            ObjectGuid const look = pool.look;
            MechanicRef ref = Mechanic::Circle(me, At(spot), kSlagBurstRadiusYd, Ms(kSlagBurstWarnMs));
            ref.Damage(kSlagBurstPct).TankDamage(kSlagBurstPct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_AR_SLAG_BURST)
                .Weakened().Within(StoreroomBounds()).Tag(TAG_AR_SLAG_BURST)
                .OnResolve(OnCrell([spot, poolHandle, look](boss_forgemaster_gideon_crell_rework& ai,
                    BossMechanics::ResolveResult const&)
                {
                    ai.SlagBursts(spot, poolHandle, look);
                }));
            if (ref.IsValid())
                Track(ref.Handle());
            else
                SlagBursts(spot, poolHandle, look);     // refused: the pool goes now
        }
        if (!pools.empty())
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "slag-swell",
                Acore::StringFormat("pools={} pct={:.0f}", pools.size(), kSlagBurstPct));
    }

    void SlagBursts(Vec2 spot, MechanicHandle poolHandle, ObjectGuid look)
    {
        Mechanic::Cancel(me, poolHandle);
        if (Creature* stalker = look ? ObjectAccessor::GetCreature(*me, look) : nullptr)
            stalker->DespawnOrUnsummon();
        if (me->IsAlive() && me->IsEngaged())
            me->CastSpell(spot.x, spot.y, kFloorZ, SPELL_AR_SLAG_BURST_LOOK, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR5 Temper (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    bool StartTemper()
    {
        me->StopMoving();
        Talk(EMOTE_TEMPER);
        SpellCastResult const result = me->CastSpell(me, SPELL_AR_TEMPER, false);
        if (result != SPELL_CAST_OK)
        {
            _quality = Quality::Standard;
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "temper-failed",
                Acore::StringFormat("result={} quality=standard", static_cast<uint32>(result)));
            return false;
        }
        _temper.active = true;
        _temper.startedMs = _clockMs;
        Mechanic::NoteNextCastIn(me, SPELL_AR_TEMPER, Ms(kOrderBeat(_heroic).everyMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "temper",
            Acore::StringFormat("order={} cast={}ms", _order.Number(), kTemperCastMs));
        return true;
    }

    // The cast ended without a hook (it went off, or he lost it): a cast that ran its time is a masterwork.
    void UpdateTemper()
    {
        if (!_temper.active || me->FindCurrentSpellBySpellId(SPELL_AR_TEMPER))
            return;
        if (_clockMs < _temper.startedMs + kCastStartGraceMs)
            return;     // the cast has not taken yet
        TemperEnded(_clockMs >= _temper.startedMs + kTemperCastMs ? Quality::Masterwork : Quality::Flawed,
            "no-hook");
    }

    void TemperEnded(Quality quality, char const* how)
    {
        _temper = TemperState();
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        _quality = quality;
        if (quality == Quality::Flawed)
        {
            ++_tempersKicked;
            me->CastSpell(me, SPELL_AR_FLAWED, true);
        }
        else if (quality == Quality::Masterwork)
        {
            ++_masterworks;
            me->CastSpell(me, SPELL_AR_MASTERWORK, true);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, quality == Quality::Flawed ? "temper-interrupted"
            : "temper-landed", Acore::StringFormat("quality={} how={} kicked={} masterwork={}", QualityName(quality),
                how, _tempersKicked, _masterworks));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Issue
    // ----------------------------------------------------------------------------------------------------------------

    void Issue(uint8 pieces)
    {
        Quality const quality = _heroic ? _quality : Quality::Standard;
        if (pieces & PIECE_BLADE)
            GiveBlade(quality);
        if (pieces & PIECE_PLATE)
            GivePlate(quality);
        if (_heroic)
            HandToRecruit(pieces);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "issue",
            Acore::StringFormat("order={} blade={} plate={} quality={} delay={}ms", _order.Number(),
                (pieces & PIECE_BLADE) ? 1 : 0, (pieces & PIECE_PLATE) ? 1 : 0, QualityName(quality),
                _order.DelayMs()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR-Bl Forged Blade, AR7 Proving Strike
    // ----------------------------------------------------------------------------------------------------------------

    // He takes up the blade for 15 s (heroic flawed 8, masterwork 25): the cleave from now, every 6 s; the first chain
    // 2 s from now (heroic: every 10 s while he holds it); a 6 yd spread for the window. A new Blade replaces the old.
    void GiveBlade(Quality quality)
    {
        uint32 const bladeMs = BladeMs(_heroic, quality);
        EndBlade("replaced", false);
        _blade.active = true;
        _blade.untilMs = _clockMs + bladeMs;
        _blade.quality = quality;
        me->CastSpell(me, SPELL_AR_FORGED_BLADE, true);
        me->SetVirtualItem(0, kItemBlade);
        _cleaveClock.Start(_clockMs, 0);
        _chainClock.Start(_clockMs, kStrikeFirstMs);
        MechanicRef spread = Mechanic::Spread(me, kBladeSpreadYd, Ms(kBladeSpreadWarnMs));
        spread.Persistent(Ms(bladeMs), Ms(kBladeSpreadTickMs)).Within(StoreroomBounds()).Tag(TAG_AR_BLADE_SPREAD);
        _blade.spread = spread.Handle();
        if (spread.IsValid())
            Track(spread.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "blade",
            Acore::StringFormat("quality={} for={}ms chains={}", QualityName(quality), bladeMs,
                ChainsIn(bladeMs, _heroic)));
    }

    // The blade goes (its time ran out, a new one replaces it, or the fight ends): his hammer back in his hand.
    void EndBlade(char const* why, bool log = true)
    {
        if (!_blade.active)
            return;
        _blade.active = false;
        _cleaveClock.Stop();
        _chainClock.Stop();
        if (_blade.spread)
            Mechanic::Cancel(me, _blade.spread);
        _blade.spread = MechanicHandle();
        me->RemoveAurasDueToSpell(SPELL_AR_FORGED_BLADE);
        me->SetVirtualItem(0, kItemSmithHammer);
        if (log)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "blade-end", why);
    }

    void UpdateBlade()
    {
        if (!_blade.active)
            return;
        if (_clockMs >= _blade.untilMs && !_chain.active)
        {
            EndBlade("expired");
            return;
        }
        bool const free = !_chain.active && !me->HasUnitState(UNIT_STATE_CASTING);
        if (free && _chainClock.Due(_clockMs) && _clockMs < _blade.untilMs)
        {
            if (_heroic)
                _chainClock.Fired(_clockMs, kStrikeEveryMs);
            else
                _chainClock.Stop();
            StartChain(nullptr);
            return;
        }
        if (free && _cleaveClock.Due(_clockMs) && _clockMs < _blade.untilMs)
        {
            _cleaveClock.Fired(_clockMs, kCleaveEveryMs);
            Cleave();
        }
    }

    // The cleave: a 90 degree cone 8 yd in front of him (a 1.5 s marker); others 30% (45%) and Weakened through the
    // registry (the tank exempt), the tank his own hit at the resolve when still in front of him.
    bool Cleave()
    {
        float const pct = kCleavePct(_heroic);
        MechanicRef ref = Mechanic::Cone(me, me, kCleaveAngleDeg, kCleaveLengthYd, Ms(kCleaveWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_AR_CLEAVE).Weakened().Within(StoreroomBounds())
            .Tag(TAG_AR_CLEAVE)
            .OnResolve(OnCrell([](boss_forgemaster_gideon_crell_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.CleaveLands(r);
            }));
        if (!ref.IsValid())
            return false;
        Track(ref.Handle());
        ++_cleaves;
        return true;
    }

    void CleaveLands(BossMechanics::ResolveResult const& result)
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        Unit* victim = me->GetVictim();
        bool tankHit = false;
        if (victim && DungeonKit::InFrontalCone(DungeonKit::PlaneOf(me), me->GetOrientation(),
            DungeonKit::PlaneOf(victim), kCleaveAngleDeg, kCleaveLengthYd, me->GetCombatReach()))
        {
            me->CastSpell(victim, SPELL_AR_CLEAVE_TANK, true);
            tankHit = true;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cleave",
            Acore::StringFormat("hits={} tank={} pct={:.0f} tank-pct={:.0f} cleaves={}", result.hits.size(),
                tankHit ? 1 : 0, kCleavePct(_heroic), kCleaveTankPct(_heroic), _cleaves));
    }

    // AR7: every player once, in a random order (the tank included); `only` (a test): just that player. He stops
    // fighting for the chain (no target, no swing) and dashes along each line as it lands.
    bool StartChain(Player* only)
    {
        std::vector<ObjectGuid> players;
        if (only)
            players.push_back(only->GetGUID());
        else
        {
            std::vector<Player*> const fight = FightPlayers();
            std::vector<std::size_t> const order = ChainOrder(fight.size(),
                [](uint32 n) { return urand(0, n - 1); });
            for (std::size_t const i : order)
                players.push_back(fight[i]->GetGUID());
        }
        if (players.empty())
            return false;
        _chain = ChainState();
        _chain.active = true;
        _chain.targets = std::move(players);
        _chain.from = DungeonKit::PlaneOf(me);
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        Talk(SAY_PROVING_STRIKE);
        ++_chains;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "strike",
            Acore::StringFormat("links={} chains={}", _chain.targets.size(), _chains));
        if (!RegisterLink())
            EndChain("no-target");
        return true;
    }

    // The next living player of the chain: a line from where he stands to 5 yd past their spot (stopping at a wall),
    // 2 s marked for the first, 1 s for the others. False when nobody is left.
    bool RegisterLink()
    {
        while (_chain.link < _chain.targets.size())
        {
            Player* target = ObjectAccessor::GetPlayer(*me, _chain.targets[_chain.link]);
            if (!CountsAsPlayer(target) || !target->IsInMap(me))
            {
                ++_chain.link;
                continue;
            }
            Vec2 const from = _chain.from;
            Vec2 const end = DashEnd(from, DungeonKit::PlaneOf(target));
            float const length = DungeonKit::Distance(from, end);
            if (length < 1.f)
            {
                ++_chain.link;     // standing on him: no line to dash along
                continue;
            }
            float const facing = DungeonKit::BearingTo(from, end);
            uint32 const link = static_cast<uint32>(_chain.link);
            uint32 const warn = StrikeWarnMs(link);
            float const pct = StrikePct(link, _heroic);
            me->SetFacingTo(facing);    // only ever called standing: never during a dash (it would cancel the charge)
            MechanicRef ref = Mechanic::Line(me, At(from, kFloorZ, facing), facing, length, kStrikeWidthYd, Ms(warn));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_AR_PROVING_STRIKE).Weakened()
                .Within(StoreroomBounds()).Tag(TAG_AR_STRIKE);
            if (ref.IsValid())
                Track(ref.Handle());
            _chain.end = end;
            _chain.resolveAtMs = _clockMs + warn;
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "strike-link",
                Acore::StringFormat("link={} target={} tank={} length={:.1f} warn={}ms pct={:.0f}", link + 1,
                    target->GetName(), target == me->GetVictim() ? 1 : 0, length, warn, pct));
            return true;
        }
        return false;
    }

    // At each line's resolve he dashes to its end (facing along it: no SetFacingTo while the charge runs, it would
    // replace the charge's spline). Once he has landed the next line is marked from where he really stands, so every
    // line starts at his feet and a long dash is never cut short. After the last he goes back to the top of his
    // threat list.
    void UpdateChain()
    {
        if (!_chain.active)
            return;
        if (_chain.dashing)
        {
            bool const moving = !me->movespline->Finalized();
            if (_clockMs < _chain.landAtMs || (moving && _clockMs < _chain.landAtMs + kDashLandGraceMs))
                return;
            _chain.dashing = false;
            Vec2 const landed = DungeonKit::PlaneOf(me);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "strike-land",
                Acore::StringFormat("link={} planned=({:.1f},{:.1f}) real=({:.1f},{:.1f}) off={:.1f}", _chain.link,
                    _chain.end.x, _chain.end.y, landed.x, landed.y, DungeonKit::Distance(landed, _chain.end)));
            _chain.from = ChainFrom(landed, _chain.end);
            if (!RegisterLink())
                EndChain("done");
            return;
        }
        if (_clockMs < _chain.resolveAtMs)
            return;
        Vec2 const end = _chain.end;
        float const length = DungeonKit::Distance(DungeonKit::PlaneOf(me), end);
        float z = kFloorZ;
        me->UpdateAllowedPositionZ(end.x, end.y, z);
        me->CastSpell(me, SPELL_AR_DASH_LOOK, true);
        me->GetMotionMaster()->MoveCharge(end.x, end.y, z, kDashSpeed, EVENT_CHARGE, nullptr, false,
            DungeonKit::BearingTo(DungeonKit::PlaneOf(me), end));
        ++_chain.link;
        _chain.dashing = true;
        _chain.landAtMs = DashLandAtMs(_clockMs, length);
    }

    void EndChain(char const* why)
    {
        if (!_chain.active)
            return;
        std::size_t const links = _chain.targets.size();
        _chain = ChainState();
        if (me->IsAlive() && me->IsEngaged())
        {
            me->SetReactState(REACT_AGGRESSIVE);
            if (Unit* victim = me->SelectVictim())
                AttackStart(victim);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "strike-end",
            Acore::StringFormat("why={} links={}", why, links));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR-Pl Red-Hot Plate, AR8 Popping Rivets
    // ----------------------------------------------------------------------------------------------------------------

    // He straps on the plate: an absorb of 5k (heroic 25k; flawed 12.5k, masterwork 50k). A new plate replaces the old
    // (its unpopped rivets are lost).
    void GivePlate(Quality quality)
    {
        uint32 const amount = PlateAbsorb(_heroic, quality);
        _plate.active = false;      // the old plate's removal is not a break
        me->RemoveAurasDueToSpell(SPELL_AR_RED_HOT_PLATE);
        _plate = PlateState();
        int32 const bp = static_cast<int32>(amount);
        me->CastCustomSpell(me, SPELL_AR_RED_HOT_PLATE, &bp, nullptr, nullptr, true);
        if (!me->HasAura(SPELL_AR_RED_HOT_PLATE))
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "plate-failed", Acore::StringFormat("amount={}",
                amount));
            return;
        }
        _plate.active = true;
        _plate.total = amount;
        _plate.startMs = _clockMs;
        me->SetVirtualItem(1, kItemPlateShield);
        ++_plates;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "plate",
            Acore::StringFormat("quality={} absorb={} rivets={} burn={:.0f}%", QualityName(quality), amount,
                RivetsFor(amount, _heroic), kBurnBackPct));
    }

    // spell_sm_crell_red_hot_plate: `absorbed` of a hit by `attacker` went into the plate (the script burned them
    // back already).
    void PlateAbsorbed(uint32 absorbed, uint32 burned)
    {
        if (!_plate.active || !me->IsAlive())
            return;
        _plate.broken += absorbed;
        _plate.burned += burned;
        _burnedTotal += burned;
        PopDueRivets();
    }

    // Sunder Armor, Expose Armor or Faerie Fire tore off 500 that burn nobody.
    void TearPlate(Unit* caster, uint32 spellId)
    {
        AuraEffect* effect = me->GetAuraEffect(SPELL_AR_RED_HOT_PLATE, EFFECT_0);
        if (!effect)
            return;
        int32 const amount = effect->GetAmount();
        uint32 const tear = std::min<uint32>(kArmorTear, static_cast<uint32>(std::max(amount, 0)));
        _plate.broken += tear;
        _plate.torn += tear;
        _tornTotal += tear;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "tear",
            Acore::StringFormat("by={} spell={} tear={} left={}", caster->GetName(), spellId, tear,
                amount - static_cast<int32>(tear)));
        if (amount <= static_cast<int32>(tear))
            me->RemoveAurasDueToSpell(SPELL_AR_RED_HOT_PLATE, ObjectGuid::Empty, 0, AURA_REMOVE_BY_ENEMY_SPELL);
        else
            effect->ChangeAmount(amount - static_cast<int32>(tear));
        PopDueRivets();
    }

    void PopDueRivets()
    {
        uint32 const due = RivetsDue(_plate.broken, _plate.total, _heroic);
        while (_plate.rivets < due)
        {
            ++_plate.rivets;
            Rivet(nullptr);
        }
    }

    // A red-hot rivet lands near a random player (the tank included): a 4 yd circle at a floor spot within 8 yd of
    // them, its flight the 2 s marker.
    bool Rivet(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!CountsAsPlayer(target))
            return false;
        Vec2 const spot = RivetSpot(DungeonKit::PlaneOf(target), []() { return frand(0.f, 1.f); });
        float const pct = kRivetPct(_heroic);
        me->CastSpell(spot.x, spot.y, kFloorZ, SPELL_AR_RIVET_LOOK, true);
        MechanicRef ref = Mechanic::Circle(me, At(spot), kRivetRadiusYd, Ms(kRivetWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_AR_RIVET).Weakened()
            .Within(StoreroomBounds()).Tag(TAG_AR_RIVET);
        if (ref.IsValid())
            Track(ref.Handle());
        ++_rivetsTotal;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "rivet",
            Acore::StringFormat("near={} tank={} at=({:.1f}, {:.1f}) pct={:.0f} n={}/{}", target->GetName(),
                target == me->GetVictim() ? 1 : 0, spot.x, spot.y, pct, _plate.rivets,
                RivetsFor(_plate.total, _heroic)));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR6 The Supply Line (heroic, set dressing)
    // ----------------------------------------------------------------------------------------------------------------

    // A recruit steps out of the Armor Crate and walks to his counter.
    bool SendRecruit()
    {
        if (!sObjectMgr->GetCreatureTemplate(NPC_SM_SCARLET_RECRUIT))
            return false;
        TempSummon* recruit = me->SummonCreature(NPC_SM_SCARLET_RECRUIT, At(kArmorCrate), TEMPSUMMON_TIMED_DESPAWN,
            kRecruitLifeMs);
        if (!recruit)
            return false;
        recruit->SetReactState(REACT_PASSIVE);
        recruit->SetWalk(true);
        recruit->GetMotionMaster()->MovePoint(1, kCounter.x, kCounter.y, kCounter.z);
        _recruit = recruit->GetGUID();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "recruit", Acore::StringFormat("order={}",
            _order.Number()));
        return true;
    }

    // At the Issue the recruit takes a copy of the piece (a sword and a shield) and marches out toward the upper hall,
    // gone once out of sight.
    void HandToRecruit(uint8 pieces)
    {
        Creature* recruit = _recruit ? ObjectAccessor::GetCreature(*me, _recruit) : nullptr;
        _recruit = ObjectGuid::Empty;
        if (!recruit || !recruit->IsAlive())
            return;
        Talk(EMOTE_HAND_OVER);
        if (pieces & PIECE_BLADE)
            recruit->SetVirtualItem(0, kItemBlade);
        if (pieces & PIECE_PLATE)
            recruit->SetVirtualItem(1, kItemPlateShield);
        recruit->SetWalk(false);
        recruit->GetMotionMaster()->MovePoint(2, kRecruitExit.x, kRecruitExit.y, kRecruitExit.z);
        float const dist = recruit->GetExactDist2d(kRecruitExit.x, kRecruitExit.y);
        float const speed = std::max(1.f, recruit->GetSpeed(MOVE_RUN));
        recruit->DespawnOrUnsummon(Milliseconds(static_cast<uint32>(dist / speed * 1000.f) + 2000));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "recruit-out", Acore::StringFormat("dist={:.0f}", dist));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ARM "Boss data")
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order: Crell (the recruits are not selectable). Interrupt list: Temper (heroic, expected). No dispels, no
    // purges. The recruits and the look stalkers are ignored.
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.ignores.emplace_back(NPC_SM_SCARLET_RECRUIT);
        d.ignores.emplace_back(NPC_SM_STALKER_WAVE2);
        if (_heroic)
            d.interrupts.emplace_back(NPC_SM_CRELL, SPELL_AR_TEMPER, 3, Ms(kOrderBeat(true).everyMs));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm crell` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Order,
        Heat,
        Hammer,
        Quench,
        Temper,
        Blade,
        Plate,
        Strike,
        Cleave,
        Rivet,
        Tear,
        Recruit,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM).
    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!me->IsEngaged())
            return "Crell must be in combat (the picks read his threat list, the mechanics his encounter).";
        bool const busy = _chain.active || _temper.active || me->HasUnitState(UNIT_STATE_CASTING);
        switch (mechanic)
        {
            case TestMechanic::Order:
                if (_order.Active())
                    return "An order is running already (wait for its Issue).";
                StartOrder();
                break;
            case TestMechanic::Heat:
                Heat();
                break;
            case TestMechanic::Hammer:
                if (busy)
                    return "He is casting or dashing.";
                Hammer();
                break;
            case TestMechanic::Quench:
                Quench();
                break;
            case TestMechanic::Temper:
                if (busy)
                    return "He is casting or dashing.";
                if (!StartTemper())
                    return "The Temper did not start (see the log).";
                break;
            case TestMechanic::Blade:
                GiveBlade(_quality);
                break;
            case TestMechanic::Plate:
                GivePlate(_quality);
                break;
            case TestMechanic::Strike:
                if (busy)
                    return "He is casting or dashing.";
                if (!StartChain(nullptr))
                    return "Nobody to dash through.";
                break;
            case TestMechanic::Cleave:
                if (!Cleave())
                    return "The registry refused the cleave.";
                break;
            case TestMechanic::Rivet:
                if (!Rivet(CountsAsPlayer(who) ? who : nullptr))
                    return "No player to land a rivet near.";
                break;
            case TestMechanic::Tear:
                if (!_plate.active)
                    return "He wears no plate.";
                TearPlate(who ? static_cast<Unit*>(who) : me, 0);
                break;
            case TestMechanic::Recruit:
                if (!SendRecruit())
                    return "No recruit (the template 300941 is missing or the summon failed).";
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} orders={} step={} quality={} blade={} (until {}s) chain={} "
            "(link {}/{}) plate={} ({}/{} broken, rivets {}) slag={} cleaves={} chains={} rivets={} burned={} torn={} "
            "kicked={} masterwork={} live-handles={}",
            _clockMs / 1000, _heroic ? 1 : 0, _orderCount, _order.Active() ? StepName(_order.Current()) : "idle",
            QualityName(_quality), _blade.active ? 1 : 0, _blade.untilMs / 1000, _chain.active ? 1 : 0, _chain.link,
            _chain.targets.size(), _plate.active ? 1 : 0, _plate.broken, _plate.total, _plate.rivets, _slag.size(),
            _cleaves, _chains, _rivetsTotal, _burnedTotal, _tornTotal, _tempersKicked, _masterworks, _live.size());
    }

private:
    struct TemperState
    {
        bool active = false;
        uint64 startedMs = 0;
    };

    struct BladeState
    {
        bool active = false;
        uint64 untilMs = 0;
        Quality quality = Quality::Standard;
        MechanicHandle spread;
    };

    struct ChainState
    {
        bool active = false;
        bool dashing = false;           // a dash is under way (the next line waits for the landing)
        std::vector<ObjectGuid> targets;
        std::size_t link = 0;
        Vec2 from;
        Vec2 end;
        uint64 resolveAtMs = 0;
        uint64 landAtMs = 0;
    };

    struct PlateState
    {
        bool active = false;
        uint32 total = 0;
        uint32 broken = 0;
        uint32 rivets = 0;
        uint32 burned = 0;
        uint32 torn = 0;
        uint64 startMs = 0;
    };

    struct SlagPool
    {
        Vec2 spot;
        MechanicHandle handle;
        ObjectGuid look;
    };

    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (!CountsAsPlayer(player) || !player->IsInMap(me))
                continue;
            out.push_back(player);
        }
        return out;
    }

    // A look stalker (the wave 2 generic stalker 300958) for `ms`; nothing when its template is missing (the fight
    // plays without its looks).
    Creature* SummonLook(Position const& at, uint32 ms)
    {
        if (!sObjectMgr->GetCreatureTemplate(NPC_SM_STALKER_WAVE2))
            return nullptr;
        return me->SummonCreature(NPC_SM_STALKER_WAVE2, at, TEMPSUMMON_TIMED_DESPAWN, ms);
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnCrell(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_forgemaster_gideon_crell_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    static boss_forgemaster_gideon_crell_rework* From(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_forgemaster_gideon_crell_rework*>(boss->AI());
    }

    // A mechanic of the fight: kept to cancel it on a reset.
    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 192)     // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 96);
    }

    // The pull's state: nothing registered, no summon, no aura of his, his hammer in his hand, his order count back to
    // zero (Reset, evade, death).
    void Cleanup(bool dead)
    {
        _temper = TemperState();        // before the engine interrupts a cast, so it never reads as a kick
        _plate.active = false;          // before the aura goes, so its removal is not a break
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (SlagPool const& pool : _slag)
            Mechanic::Cancel(me, pool.handle);
        _slag.clear();
        summons.DespawnAll();
        _recruit = ObjectGuid::Empty;
        bool const wasChain = _chain.active;
        _chain = ChainState();
        _blade = BladeState();
        _plate = PlateState();
        _order.Stop();
        _orderClock.Stop();
        _cleaveClock.Stop();
        _chainClock.Stop();
        _quality = Quality::Standard;
        _clockMs = 0;
        _killLineReadyMs = 0;
        _orderCount = 0;
        _heats = 0;
        _hammers = 0;
        _quenches = 0;
        _cleaves = 0;
        _chains = 0;
        _plates = 0;
        _rivetsTotal = 0;
        _burnedTotal = 0;
        _tornTotal = 0;
        _tempersKicked = 0;
        _masterworks = 0;
        _arena.Reset();
        for (uint32 const spell : { uint32(SPELL_AR_RED_HOT_PLATE), uint32(SPELL_AR_FORGED_BLADE),
            uint32(SPELL_AR_FLAWED), uint32(SPELL_AR_MASTERWORK) })
            me->RemoveAurasDueToSpell(spell);
        me->SetVirtualItem(0, kItemSmithHammer);
        me->SetVirtualItem(1, 0);
        if (!dead && (wasChain || !me->HasReactState(REACT_AGGRESSIVE)))
            me->SetReactState(REACT_AGGRESSIVE);
    }

    DungeonKit::ArenaGuard _arena;
    BeatClock _orderClock;
    BeatClock _cleaveClock;
    BeatClock _chainClock;
    OrderRun _order;
    TemperState _temper;
    BladeState _blade;
    ChainState _chain;
    PlateState _plate;
    std::vector<SlagPool> _slag;
    std::vector<MechanicHandle> _live;
    ObjectGuid _recruit;
    Quality _quality = Quality::Standard;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint64 _killLineReadyMs = 0;
    uint32 _orderCount = 0;
    uint32 _heats = 0;
    uint32 _hammers = 0;
    uint32 _quenches = 0;
    uint32 _cleaves = 0;
    uint32 _chains = 0;
    uint32 _plates = 0;
    uint32 _rivetsTotal = 0;
    uint32 _burnedTotal = 0;
    uint32 _tornTotal = 0;
    uint32 _tempersKicked = 0;
    uint32 _masterworks = 0;
    bool _heroic = false;
};

namespace
{
    boss_forgemaster_gideon_crell_rework* CrellAIOf(Unit* unit)
    {
        Creature* boss = unit ? unit->ToCreature() : nullptr;
        if (!boss || !boss->IsAIEnabled || boss->GetEntry() != NPC_SM_CRELL)
            return nullptr;
        return dynamic_cast<boss_forgemaster_gideon_crell_rework*>(boss->AI());
    }

    boss_forgemaster_gideon_crell_rework* FindCrellAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_SM_CRELL);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_forgemaster_gideon_crell_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Crell is not running boss_forgemaster_gideon_crell_rework (wave 2 "
                "unbound, or check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_forgemaster_gideon_crell_rework::TestMechanic mechanic, char const* what)
    {
        boss_forgemaster_gideon_crell_rework* ai = FindCrellAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Crell: {} fired ({}).", what, ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    using Mech = boss_forgemaster_gideon_crell_rework::TestMechanic;

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_SM_CRELL, BOSS_CRELL);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_forgemaster_gideon_crell_rework* ai = FindCrellAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Crell: {}", ai->TestState());
        return true;
    }

    bool HandleOrder(ChatHandler* handler)
    {
        return Fire(handler, Mech::Order, "a new order now (AR1: the yell, then Heat, Hammer, Quench, the Issue)");
    }

    bool HandleHeat(ChatHandler* handler)
    {
        return Fire(handler, Mech::Heat, "Heat (AR2: the sparks; heroic: slag pools)");
    }

    bool HandleHammer(ChatHandler* handler)
    {
        return Fire(handler, Mech::Hammer, "Hammer (AR3: a 2.5 s cast, the donut, then the anvil circle)");
    }

    bool HandleQuench(ChatHandler* handler)
    {
        return Fire(handler, Mech::Quench, "Quench (AR4: 8 s of steam at the trough; heroic: the slag bursts)");
    }

    bool HandleTemper(ChatHandler* handler)
    {
        return Fire(handler, Mech::Temper, "Temper (AR5: a 2.5 s cast, kick it)");
    }

    bool HandleBlade(ChatHandler* handler)
    {
        return Fire(handler, Mech::Blade, "the Forged Blade (AR-Bl and AR7, the current order's quality)");
    }

    bool HandlePlate(ChatHandler* handler)
    {
        return Fire(handler, Mech::Plate, "the Red-Hot Plate (AR-Pl, the current order's quality)");
    }

    bool HandleStrike(ChatHandler* handler)
    {
        return Fire(handler, Mech::Strike, "a Proving Strike chain (AR7: every player, any blade)");
    }

    bool HandleCleave(ChatHandler* handler)
    {
        return Fire(handler, Mech::Cleave, "the Blade's cleave (90 degrees, 8 yd, any blade)");
    }

    bool HandleRivet(ChatHandler* handler)
    {
        return Fire(handler, Mech::Rivet, "a rivet near the selected player (AR8)");
    }

    bool HandleTear(ChatHandler* handler)
    {
        return Fire(handler, Mech::Tear, "an armor tear of 500 on the plate (AR-Pl)");
    }

    bool HandleRecruit(ChatHandler* handler)
    {
        return Fire(handler, Mech::Recruit, "a Scarlet Recruit from the Armor Crate (AR6)");
    }

    // `.dbtest sm crell <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BossForgemasterGideonCrellTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "order",   HandleOrder,   SEC_GAMEMASTER, Console::No },
            { "heat",    HandleHeat,    SEC_GAMEMASTER, Console::No },
            { "hammer",  HandleHammer,  SEC_GAMEMASTER, Console::No },
            { "quench",  HandleQuench,  SEC_GAMEMASTER, Console::No },
            { "temper",  HandleTemper,  SEC_GAMEMASTER, Console::No },
            { "blade",   HandleBlade,   SEC_GAMEMASTER, Console::No },
            { "plate",   HandlePlate,   SEC_GAMEMASTER, Console::No },
            { "strike",  HandleStrike,  SEC_GAMEMASTER, Console::No },
            { "cleave",  HandleCleave,  SEC_GAMEMASTER, Console::No },
            { "rivet",   HandleRivet,   SEC_GAMEMASTER, Console::No },
            { "tear",    HandleTear,    SEC_GAMEMASTER, Console::No },
            { "recruit", HandleRecruit, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// AR-Pl Red-Hot Plate: an absorb on Crell (SCHOOL_ABSORB, every school, the amount set at the cast). 20% of each hit it
// absorbs burns the attacker back as Fire (players, pets and their spells alike), and the AI counts the plate broken
// for its rivets. The shape of the stock Argent Confessor Paletress's Reflective Shield (boss_argent_challenge.cpp
// spell_reflective_shield_aura: AfterEffectAbsorb, a custom-value damage spell on the attacker).
class spell_sm_crell_red_hot_plate : public AuraScript
{
    PrepareAuraScript(spell_sm_crell_red_hot_plate);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_AR_PLATE_BURN });
    }

    void AfterAbsorb(AuraEffect* /*aurEff*/, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        Unit* owner = GetTarget();
        if (!owner || !absorbAmount)
            return;
        uint32 burned = 0;
        Unit* attacker = dmgInfo.GetAttacker();
        if (attacker && attacker != owner && attacker->IsAlive() && attacker->IsInMap(owner))
        {
            int32 const burn = static_cast<int32>(BurnBack(absorbAmount));
            if (burn > 0)
            {
                owner->CastCustomSpell(attacker, SPELL_AR_PLATE_BURN, &burn, nullptr, nullptr, true);
                burned = static_cast<uint32>(burn);
            }
        }
        if (boss_forgemaster_gideon_crell_rework* ai = CrellAIOf(owner))
            ai->PlateAbsorbed(absorbAmount, burned);
    }

    void Register() override
    {
        AfterEffectAbsorb += AuraEffectAbsorbFn(spell_sm_crell_red_hot_plate::AfterAbsorb, EFFECT_0);
    }
};

void AddSC_boss_forgemaster_gideon_crell_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_forgemaster_gideon_crell_rework,
            ScarletMonasteryRework::kInstanceScriptName);
    RegisterSpellScript(spell_sm_crell_red_hot_plate);
    SmTest::RegisterBoss("crell", BossForgemasterGideonCrellTestCommands());
}
