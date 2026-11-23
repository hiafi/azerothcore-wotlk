/*
 * mod-dungeon-bosses, Scarlet Monastery D8: Arcanist Doan (6487), "Burn in Righteous Fire", the Library's end boss.
 * Build spec: docs/dungeons/scarlet-monastery-2-library.md "Arcanist Doan" (DN0-DN4, Build spec), handoff section
 * 3.5 row D8, 3.6, 3.8 (the chamber), 7 #22 A (the seal). Replaces his stock SmartAI (7 rows, dropped by S0's rev):
 * Silence 8988 and Polymorph 13323 are gone, Arcane Explosion 9433 and Arcane Bubble 9438 / Detonation 9435 are
 * reworked as below. Pure rules: DoanLogic.h. The hard mode (the Kel'Thuzad Heresy, D8H) fights on this AI through
 * DoanFight.h; this file never needs an edit for it.
 *
 *   DN0 The Sealed       3 s after the pull an arcane barrier (301319, the Razorfen forcefield, about 4 yd) shuts the
 *       Chamber          1.5-2.8 yd doorway to the outer hall with an emote; every living group member outside the
 *                        chamber, in the Library, within 60 yd of the entry spot is moved inside (KT-SM SealedArena,
 *                        section 7 #22 A). It opens on his death, a wipe or an evade
 *   DN1 Burn in          20 s, then every 35 s (heroic 30 s): he yells, seals himself in the Arcane Bubble (immune),
 *       Righteous Fire   raises 3 Arcane Anchors (heroic 4) on fixed spots 15 yd out, each beaming into the bubble, and
 *                        starts Detonation, a 10 s bar (heroic 14 s, its own bar spell 212687: HANDOFF s10 D;
 *                        anchors 1.2k / 5k). Every anchor broken first: the bubble shatters and he is
 *                        Overloaded for 10 s (+50% damage taken, no casts). The bar completes: 75% (heroic 130%,
 *                        lethal) Fire to every player in the chamber, two Scorched patches (5 yd, 6% / 10% a second,
 *                        the rest of the fight) and one more anchor next time (normal caps 5 anchors, 4 patches)
 *   DN2 Arcane           8 s, then every 12 s, never while bubbled or Overloaded: a 2 s bar, then 10 yd round him, 30%
 *       Explosion        (heroic 45%) Arcane and Weakened, the tank included
 *   DN3 Mark of          15 s, then every 20 s, never while bubbled or Overloaded: 2 (heroic 3) players, never the
 *       Righteous Fire   tank, marked 5 s; each bursts for 8 yd where they stand: 15% (20%) on them, 35% (45%) and
 *                        Weakened on anyone else inside. The bots carry it to the wall (G1 wall-mark row: the drop
 *                        rule Edge + Away). Heroic: a 3 yd pool forms 1 s after each burst, 30 s, 10% a second
 *   DN4 Righteous        heroic: 10 s, then every 15 s, never while bubbled or Overloaded: a 2.5 s cast, an expected
 *       Flamestrike      interrupt; missed, 40% Fire to every player
 *
 * A wipe despawns the anchors, the patches' and pools' looks (their zones are cancelled), opens the seal and resets
 * him; the encounter completes on his death (the instance stands the Library -> Armory portal P2 on DONE). Every
 * percent hit is a percent of the reference row (the tank row on the tank) through the registry, Flamestrike through
 * the kit's spell_dungeon_refflat_damage. Boss data: kill order the Arcane Anchors (priority 1, everyone, the tank
 * too: he is free while Doan is bubbled); Doan ignored while the bubble is up; interrupt list Righteous Flamestrike
 * (heroic, expected); no dispels or purges. Every firing logs one INFO line "sm doan <mechanic> ..."
 * (module.dungeonbosses); `.dbtest sm doan ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DoanFight.h"
#include "DoanLogic.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "DungeonKitWings.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmDoan;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "doan";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // The chamber's floor outline at its floor height (the bots' drop room).
    std::vector<Position> ChamberPolygon()
    {
        std::vector<Position> room;
        room.reserve(kChamberOutline.size());
        for (Vec2 const& p : kChamberOutline)
            room.emplace_back(p.x, p.y, kChamberCenter.z);
        return room;
    }

    // Every spot the bots plan for the fight's zones and carried Marks stays on the chamber's floor (rule 12).
    BossMechanics::SpotBounds ChamberBounds()
    {
        return BossMechanics::SpotBounds().Polygon(ChamberPolygon(), kChamberZMin, kChamberZMax);
    }

    // The floor under a point (an anchor stands on it); falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + 2.f);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > 4.f) ? z : floor;
    }

    // DN0: the seal's spec (KT-SM SealedArena, section 7 #22 A): closes 3 s after the pull with the emote, the seal
    // object summoned across the doorway, stragglers in the Library within 60 yd of the entry moved inside.
    DungeonKit::SealedArenaSpec SealSpec()
    {
        DungeonKit::SealedArenaSpec spec;
        spec.arena = DoanArena();
        spec.entry = Position(kSealEntry.x, kSealEntry.y, kSealEntry.z, kSealEntryFacing);
        spec.sameWing = [](Creature const* boss, Player const* player)
        {
            return WingOf(DungeonKit::PlaneOf(player)) == WingOf(DungeonKit::PlaneOf(boss));
        };
        spec.emoteGroup = EMOTE_SEAL;
        spec.sealEntry = GO_SM_CHAMBER_SEAL;
        spec.sealAt = Position(kSealSpot.x, kSealSpot.y, kSealSpot.z, kSealFacing);
        spec.dungeon = kLogDungeon;
        spec.boss = kBossLogName;
        return spec;
    }

    // D8H's factory (DoanFight.h), set once from AddSC_sm_doan_hard_mode whatever the AddSC order.
    DoanHardModeFactory& HardModeFactory()
    {
        static DoanHardModeFactory factory;
        return factory;
    }

    DoanIdleHook& IdleHook()
    {
        static DoanIdleHook hook;
        return hook;
    }
}

void SmDoan::RegisterDoanHardMode(DoanHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

void SmDoan::RegisterDoanIdleHook(DoanIdleHook hook)
{
    IdleHook() = std::move(hook);
}

std::unique_ptr<DoanHardMode> SmDoan::CreateDoanHardMode(Creature* doan)
{
    DoanHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(doan) : nullptr;
}

// Arcanist Doan 6487
struct boss_arcanist_doan_rework : public BossAI, public DoanFight
{
    explicit boss_arcanist_doan_rework(Creature* creature)
        : BossAI(creature, BOSS_DOAN), _arena(DoanArena(), LeashOptions(kBossLogName)), _seal(SealSpec()) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false, "reset");
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _heroic = IsHeroicMap(me);
        _hardModeLit = _heroic && instance && instance->GetData(DATA_HARD_MODE_DOAN) != 0;
        _engaged = true;
        _clockMs = 0;
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_DOAN;
        Mechanic::BeginEncounter(me, options);
        if (_hardModeLit)
            _hardMode = CreateDoanHardMode(me);
        Describe();
        _arena.Engage(me);
        _seal.Engage(me);
        Talk(SAY_AGGRO);

        _bubbleClock.Start(_clockMs, kBubbleBeat(_heroic).firstMs);
        _explosionClock.Start(_clockMs, kExplosionBeat(_heroic).firstMs);
        _markClock.Start(_clockMs, kMarkBeat(_heroic).firstMs);
        if (_heroic)
            _flameClock.Start(_clockMs, kFlamestrikeBeat.firstMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} hardmode={} handler={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0,
                _hardModeLit ? 1 : 0, _hardMode ? 1 : 0, me->GetPositionX(), me->GetPositionY(),
                me->GetPositionZ()));
        if (_hardMode)
            _hardMode->OnEngage(*this);
        // The rule-23 pull line last: a hard mode pull logs the health its OnEngage set (the Heresy's 400k).
        OnBossPull(me, kBossLogName, _hardModeLit);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup(false, "evade");
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("bubbles={} broken={} missed={} patches={} marks={} pools={} flamestrikes={} "
                "interrupts={} hardmode={} killer={}", _bubblesStarted, _bubblesBroken, _bubblesMissed,
                _patches.size(), _marks, _pools, _flamestrikes, _interrupts, _hardMode ? 1 : 0,
                killer ? killer->GetName() : "none"));
        Cleanup(true, "death");
    }

    // The summons are his (they go with his reset and death); only the anchors join his fight (RaiseAnchors).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
        BossAI::DamageTaken(attacker, damage, type, mask);
    }

    // DN4: a kick or a silence stopped Flamestrike. His own stops (an evade, his death, a reset, the bubble) are not
    // interrupts: Cleanup and StartBubble drop the cast's state before the engine interrupts it.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_DN_FLAMESTRIKE && _flame.active)
            FlamestrikeInterrupted();
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // D8H, out of combat: the Heresy's red aura while the flag is lit (a cold load, a respawn).
        if (!me->IsEngaged() && me->IsAlive() && !me->IsInEvadeMode())
            if (DoanIdleHook const& hook = IdleHook())
                hook(me);
        _seal.Update(me, diff);     // DN0: before UpdateVictim (the kit's order)
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (_hardMode)
            _hardMode->OnUpdate(*this, diff);
        UpdateBubble();
        UpdateOverloaded();
        UpdateFlamestrike();
        UpdatePoolList();

        bool const held = BeatsHeld(_bubble.active, Overloaded());
        bool const casting = me->HasUnitState(UNIT_STATE_CASTING);
        // DN1 waits for a cast in progress (an Explosion or a Flamestrike bar, at most 2.5 s) and never overlaps the
        // Overloaded window.
        if (!_bubble.active && !Overloaded() && !casting && _bubbleClock.Due(_clockMs))
        {
            _bubbleClock.Fired(_clockMs, BubbleEveryMs());
            StartBubble();
        }
        else if (!held)
        {
            if (_markClock.Due(_clockMs))
            {
                _markClock.Fired(_clockMs, MarkEveryMs());
                CastMarks(nullptr);
            }
            if (!me->HasUnitState(UNIT_STATE_CASTING) && _explosionClock.Due(_clockMs))
            {
                _explosionClock.Fired(_clockMs, kExplosionBeat(_heroic).everyMs);
                StartExplosion();
            }
            // A refused cast (a silence, a Fire lockout) retries on kFlamestrikeRetryMs, not every map tick.
            if (_heroic && !me->HasUnitState(UNIT_STATE_CASTING) && _flameClock.Due(_clockMs))
                _flameClock.Fired(_clockMs, StartFlamestrike() ? kFlamestrikeBeat.everyMs : kFlamestrikeRetryMs);
        }
        if (me->HasUnitState(UNIT_STATE_CASTING) || _bubble.active)
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DN1 Burn in Righteous Fire
    // ----------------------------------------------------------------------------------------------------------------

    uint32 BubbleEveryMs() const
    {
        if (_hardMode)
            if (std::optional<uint32> const every = _hardMode->BubbleEveryMs(*this))
                return *every;
        return kBubbleBeat(_heroic).everyMs;
    }

    // The yell, the bubble, the anchors on their spots and the Detonation bar (10 s; heroic 14 s).
    void StartBubble()
    {
        if (_flame.active)
        {
            _flame = CastState();       // never read as a kick
            me->InterruptNonMeleeSpells(false);
        }
        me->StopMoving();
        Talk(SAY_BUBBLE);
        _bubble = BubbleState();
        _bubble.active = true;
        _bubble.index = ++_bubblesStarted;
        _bubble.castMs = DetonationCastMs();
        _bubble.endMs = _clockMs + _bubble.castMs;
        me->CastSpell(me, SPELL_DN_ARCANE_BUBBLE, true);
        uint32 const count = AnchorCount(_heroic, _bubblesMissed, _pendingAnchors);
        _pendingAnchors = 0;
        RaiseAnchors(count);
        DungeonKit::CastBar(me, DetonationBarSpell());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bubble",
            Acore::StringFormat("index={} anchors={} raised={} missed-before={} cast={}ms", _bubble.index, count,
                _bubble.anchors.size(), _bubblesMissed, _bubble.castMs));
        if (_hardMode)
            _hardMode->OnBubbleStart(*this, _bubble.index);
    }

    // `count` anchors on the first spots, each in the fight (at 0 threat, rule 11) and beaming into the bubble.
    void RaiseAnchors(uint32 count)
    {
        _bubble.anchorsRaised = 0;
        for (uint32 i = 0; i < count && i < kAnchorSpotCount; ++i)
        {
            Point3 const& spot = kAnchorSpots[i];
            float const facing = std::atan2(me->GetPositionY() - spot.y, me->GetPositionX() - spot.x);
            Position const at(spot.x, spot.y, FloorZ(me, spot.x, spot.y, spot.z), facing);
            TempSummon* anchor = me->SummonCreature(NPC_SM_ARCANE_ANCHOR, at, TEMPSUMMON_CORPSE_TIMED_DESPAWN,
                kAnchorCorpseMs);
            if (!anchor)
            {
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "anchor-refused",
                    Acore::StringFormat("spot={} at=({:.1f}, {:.1f})", i, spot.x, spot.y));
                continue;
            }
            ++_bubble.anchorsRaised;
            _bubble.anchors.push_back(anchor->GetGUID());
            DoZoneInCombat(anchor);
            anchor->CastSpell(me, SPELL_DN_ANCHOR_BEAM, true);
            if (_hardMode)
                _hardMode->OnAnchorRaised(*this, anchor);
        }
    }

    uint32 AnchorsStanding() const
    {
        uint32 standing = 0;
        for (ObjectGuid const& guid : _bubble.anchors)
            if (Creature const* anchor = ObjectAccessor::GetCreature(*me, guid))
                if (anchor->IsAlive())
                    ++standing;
        return standing;
    }

    void UpdateBubble()
    {
        if (!_bubble.active)
            return;
        if (BubbleBroken(static_cast<uint32>(_bubble.anchors.size()), AnchorsStanding()))
            BreakBubble("anchors");
        else if (_clockMs >= _bubble.endMs)
            Detonate();
    }

    // Every anchor broken before the bar ended: the bubble shatters, Detonation fails, Overloaded for 10 s.
    void BreakBubble(char const* why)
    {
        uint32 const index = _bubble.index;
        uint64 const tookMs = _clockMs + _bubble.castMs - _bubble.endMs;
        EndBubble();
        me->InterruptNonMeleeSpells(false);
        me->CastSpell(me, SPELL_DN_OVERLOADED, true);
        _overloadedUntilMs = _clockMs + kOverloadedMs;
        ++_bubblesBroken;
        Talk(EMOTE_OVERLOADED);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "overloaded",
            Acore::StringFormat("index={} why={} took={}ms broken={}", index, why, tookMs, _bubblesBroken));
        if (_hardMode)
            _hardMode->OnBubbleEnd(*this, index, true);
    }

    // The bar completed with an anchor standing: the blast on every player in the chamber, two Scorched patches, one
    // more anchor next time.
    void Detonate()
    {
        uint32 const index = _bubble.index;
        uint32 const standing = AnchorsStanding();
        EndBubble();
        ++_bubblesMissed;
        float const pct = DetonationPct();
        GuidSet targets;
        for (Player* player : ChamberPlayers())
            targets.insert(player->GetGUID());
        DungeonKit::RegistryHitSpec spec;
        spec.pct = pct;
        spec.tankPct = pct;
        spec.school = SPELL_SCHOOL_FIRE;
        spec.spellId = SPELL_DN_DETONATION;
        spec.weakened = false;
        spec.rider = RiderFor(DoanHit::Detonation);
        spec.tag = TAG_DN_DETONATION;
        if (!targets.empty())
            Track(DungeonKit::RegistryHit(me, targets, spec));
        uint32 const lay = PatchesToLay(_heroic, static_cast<uint32>(_patches.size()));
        for (uint32 i = 0; i < lay; ++i)
            LayScorched();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "detonation",
            Acore::StringFormat("index={} anchors-standing={} pct={:.0f} hit={} patches={} missed={}", index,
                standing, pct, targets.size(), _patches.size(), _bubblesMissed));
        if (_hardMode)
            _hardMode->OnBubbleEnd(*this, index, false);
    }

    // DN1's length (the script's clock) and the bar spell that shows it: D8's 10 s (heroic 14 s, HANDOFF s10 D)
    // unless the hard mode names both.
    uint32 DetonationCastMs() const
    {
        if (_hardMode)
            if (std::optional<uint32> const ms = _hardMode->DetonationCastMs(*this))
                return *ms;
        return DetonationCastMsFor(_heroic);
    }

    uint32 DetonationBarSpell() const
    {
        if (_hardMode)
            if (uint32 const spell = _hardMode->DetonationBarSpell(*this))
                return spell;
        return DetonationBarSpellFor(_heroic);
    }

    float DetonationPct() const
    {
        if (_hardMode)
            if (std::optional<float> const pct = _hardMode->DetonationPct(*this))
                return *pct;
        return kDetonationPct(_heroic);
    }

    // The bubble's end either way: its aura off, his anchors gone (dead ones too; the hard mode's own units are its).
    void EndBubble()
    {
        me->RemoveAurasDueToSpell(SPELL_DN_ARCANE_BUBBLE);
        for (ObjectGuid const& guid : _bubble.anchors)
            if (Creature* anchor = ObjectAccessor::GetCreature(*me, guid))
                if (anchor->GetEntry() == NPC_SM_ARCANE_ANCHOR)
                    anchor->DespawnOrUnsummon();
        _bubble.active = false;
        _bubble.anchors.clear();
    }

    void UpdateOverloaded()
    {
        if (_overloadedUntilMs && _clockMs >= _overloadedUntilMs)
        {
            _overloadedUntilMs = 0;
            me->RemoveAurasDueToSpell(SPELL_DN_OVERLOADED);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "overloaded-end");
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DN1a Scorched
    // ----------------------------------------------------------------------------------------------------------------

    // A 5 yd patch for the rest of the fight on a random floor spot of the chamber, off the anchor spots and the other
    // patches, and a stalker there carrying its look.
    bool LayScorched()
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = kChamberCenter.XY();
        rules.minRange = kScorchedMinRangeYd;
        rules.maxRange = kScorchedMaxRangeYd;
        for (Point3 const& spot : kAnchorSpots)
            rules.avoid.push_back({ spot.XY(), kScorchedRadiusYd + kScorchedAnchorMarginYd });
        rules.minFromAway = kScorchedApartYd;
        for (Position const& p : _patches)
            rules.awayFrom.push_back({ p.GetPositionX(), p.GetPositionY() });
        DungeonKit::FloorProbe probe;
        probe.z = kChamberCenter.z;
        probe.zBand = 3.f;
        DungeonKit::Arena const arena = DoanArena();
        std::optional<Position> const spot = DungeonKit::PickFloorSpot(me, &arena, rules, probe);
        if (!spot)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "scorched-refused", "no floor spot");
            return false;
        }
        float const pct = kScorchedPct(_heroic);
        MechanicRef ref = Mechanic::Circle(me, *spot, kScorchedRadiusYd, Ms(kScorchedTickMs));
        ref.Persistent(Ms(kLingerForeverMs), Ms(kScorchedTickMs)).Damage(pct).TankDamage(pct)
            .School(SPELL_SCHOOL_FIRE).Spell(SPELL_DN_SCORCHED).NoFillTimer().Within(ChamberBounds())
            .Tag(TAG_DN_SCORCHED);
        if (uint32 const rider = RiderFor(DoanHit::Scorched))
            ref.Rider(rider);
        if (ref.IsValid())
            Track(ref.Handle());
        if (TempSummon* look = me->SummonCreature(NPC_SM_STALKER, *spot, TEMPSUMMON_MANUAL_DESPAWN))
            look->CastSpell(look, SPELL_DN_SCORCHED_LOOK, true);
        _patches.push_back(*spot);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "scorched",
            Acore::StringFormat("at=({:.1f}, {:.1f}) pct={:.0f} patches={}", spot->GetPositionX(),
                spot->GetPositionY(), pct, _patches.size()));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DN2 Arcane Explosion
    // ----------------------------------------------------------------------------------------------------------------

    // A 2 s bar, then 10 yd round him: 30% (heroic 45%) Arcane and Weakened, the tank included.
    void StartExplosion()
    {
        me->StopMoving();
        DungeonKit::CastBar(me, SPELL_DN_EXPLOSION_CAST);
        float const pct = kExplosionPct(_heroic);
        uint32 const gen = _generation;
        MechanicRef ref = Mechanic::Circle(me, me, kExplosionRadiusYd, Ms(kExplosionCastMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_ARCANE).Spell(SPELL_DN_ARCANE_EXPLOSION).Weakened()
            .Within(ChamberBounds()).Tag(TAG_DN_EXPLOSION)
            .OnResolve(OnDoan([gen](boss_arcanist_doan_rework& ai, BossMechanics::ResolveResult const& r)
            {
                if (ai._generation == gen)
                    ai.ExplosionLanded(r);
            }));
        if (uint32 const rider = RiderFor(DoanHit::Explosion))
            ref.Rider(rider);
        if (ref.IsValid())
            Track(ref.Handle());
        ++_explosions;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "explosion",
            Acore::StringFormat("pct={:.0f} r={:.0f} cast={}ms explosions={}", pct, kExplosionRadiusYd,
                kExplosionCastMs, _explosions));
    }

    void ExplosionLanded(BossMechanics::ResolveResult const& result)
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        me->CastSpell(me, SPELL_DN_EXPLOSION_LOOK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "explosion-lands",
            Acore::StringFormat("hits={} fizzled={}", result.hits.size(), result.fizzled ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DN3 Mark of Righteous Fire (and DN3a the heroic pools)
    // ----------------------------------------------------------------------------------------------------------------

    uint32 MarkEveryMs() const
    {
        if (_hardMode)
            if (std::optional<uint32> const every = _hardMode->MarkEveryMs(*this))
                return *every;
        return kMarkBeat(_heroic).everyMs;
    }

    // The bots carry a Mark to the chamber's wall, away from the group, off the patches and the burning pools.
    BossMechanics::DropSpotRule MarkDropRule() const
    {
        BossMechanics::DropSpotRule rule;
        rule.Room(ChamberPolygon()).Edge().Away().Within(ChamberBounds());
        for (Position const& p : _patches)
            rule.Avoid(p, kScorchedRadiusYd + 1.f);
        for (PoolSpot const& pool : _poolList)
            rule.Avoid(pool.at, kPoolRadiusYd + 1.f);
        return rule;
    }

    // `forced`: the GM test's pick (one Mark on that player). Returns how many were marked.
    uint32 CastMarks(Player* forced)
    {
        std::vector<Player*> targets;
        if (forced)
            targets.push_back(forced);
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;            // never the tank (an 8 yd spread would push the melee off him)
            rule.tankIfAlone = false;
            targets = DungeonKit::PickPlayers(me, rule, kMarkCount(_heroic));
        }
        std::string who;
        uint32 marked = 0;
        for (Player* target : targets)
        {
            if (!CountsAsPlayer(target))
                continue;
            DungeonKit::ImpactSpec impact;
            impact.pct = kMarkOthersPct(_heroic);
            impact.tankPct = kMarkOthersPct(_heroic);
            impact.school = SPELL_SCHOOL_FIRE;
            impact.spellId = SPELL_DN_MARK_BURST;
            impact.weakened = true;
            impact.tag = TAG_DN_MARK;
            Map* map = me->GetMap();
            ObjectGuid const bossGuid = me->GetGUID();
            ObjectGuid const targetGuid = target->GetGUID();
            uint32 const gen = _generation;
            MechanicRef ref = DungeonKit::FollowThenLand(me, target, kMarkRadiusYd, Ms(kMarkMs), impact,
                [map, bossGuid, targetGuid, gen](Creature* /*owner*/, Position const& spot,
                    BossMechanics::ResolveResult const& result)
                {
                    if (result.fizzled)
                        return;
                    if (boss_arcanist_doan_rework* ai = From(map, bossGuid))
                        if (ai->_generation == gen)
                            ai->MarkLanded(targetGuid, spot, result);
                });
            if (!ref.IsValid())
            {
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mark-refused", target->GetName());
                continue;
            }
            ref.DropSpot(MarkDropRule());
            if (uint32 const rider = RiderFor(DoanHit::MarkBurst))
                ref.Rider(rider);
            Track(ref.Handle());
            me->CastSpell(target, SPELL_DN_MARK, true);
            ++marked;
            who += (who.empty() ? "" : ",") + target->GetName();
        }
        if (marked)
            ++_marks;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, marked ? "mark" : "mark-skipped",
            Acore::StringFormat("targets=[{}] count={} pct={:.0f}/{:.0f} marks={}", who, marked,
                kMarkOthersPct(_heroic), kMarkSelfPct(_heroic), _marks));
        return marked;
    }

    // The burst where the marked player stands: their own share, the look and (heroic) the pool 1 s later.
    void MarkLanded(ObjectGuid targetGuid, Position const& spot, BossMechanics::ResolveResult const& result)
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        bool selfHit = false;
        if (Player* target = ObjectAccessor::GetPlayer(*me, targetGuid))
            if (CountsAsPlayer(target))
            {
                DungeonKit::RegistryHitSpec spec;
                spec.pct = kMarkSelfPct(_heroic);
                spec.school = SPELL_SCHOOL_FIRE;
                spec.spellId = SPELL_DN_MARK_SELF;
                spec.weakened = false;
                spec.rider = RiderFor(DoanHit::MarkSelf);
                spec.tag = TAG_DN_MARK;
                Track(DungeonKit::RegistryHit(me, GuidSet{ targetGuid }, spec));
                selfHit = true;
            }
        if (TempSummon* look = me->SummonCreature(NPC_SM_STALKER, spot, TEMPSUMMON_TIMED_DESPAWN, kBurstLookMs))
            look->CastSpell(look, SPELL_DN_MARK_BURST_LOOK, true);
        bool const pool = _heroic;
        if (pool)
            LayPool(spot);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mark-lands",
            Acore::StringFormat("at=({:.1f}, {:.1f}) others={} self={} pool={}", spot.GetPositionX(),
                spot.GetPositionY(), result.hits.size(), selfHit ? 1 : 0, pool ? 1 : 0));
    }

    uint32 PoolLifeMs() const
    {
        if (_hardMode)
            if (std::optional<uint32> const life = _hardMode->PoolLifeMs(*this))
                return *life ? *life : kLingerForeverMs;
        return kPoolLifeMs;
    }

    // DN3a: a 3 yd pool forming 1 s after the burst, 10% Fire a second for 30 s (the hard mode: the rest of the fight).
    void LayPool(Position const& spot)
    {
        uint32 const life = PoolLifeMs();
        MechanicRef ref = Mechanic::Circle(me, spot, kPoolRadiusYd, Ms(kPoolFormMs));
        ref.Persistent(Ms(life), Ms(kPoolTickMs)).Damage(kPoolPct).TankDamage(kPoolPct).School(SPELL_SCHOOL_FIRE)
            .Spell(SPELL_DN_POOL).NoFillTimer().Within(ChamberBounds()).Tag(TAG_DN_POOL);
        if (uint32 const rider = RiderFor(DoanHit::Pool))
            ref.Rider(rider);
        if (ref.IsValid())
            Track(ref.Handle());
        bool const forever = life >= kLingerForeverMs;
        TempSummon* look = forever ? me->SummonCreature(NPC_SM_STALKER, spot, TEMPSUMMON_MANUAL_DESPAWN)
            : me->SummonCreature(NPC_SM_STALKER, spot, TEMPSUMMON_TIMED_DESPAWN, kPoolFormMs + life + kLookTailMs);
        if (look)
            look->CastSpell(look, SPELL_DN_POOL_LOOK, true);
        PoolSpot entry;
        entry.at = spot;
        entry.untilMs = forever ? 0 : _clockMs + kPoolFormMs + life;
        _poolList.push_back(entry);
        ++_pools;
    }

    // Pools whose life is over leave the drop rule's avoid list.
    void UpdatePoolList()
    {
        _poolList.erase(std::remove_if(_poolList.begin(), _poolList.end(), [this](PoolSpot const& p)
        {
            return p.untilMs && _clockMs >= p.untilMs;
        }), _poolList.end());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DN4 Righteous Flamestrike (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // A 2.5 s interruptible cast; missed, 40% Fire to every player by the spell's own effect.
    bool StartFlamestrike()
    {
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, SPELL_DN_FLAMESTRIKE, false);
        if (result != SPELL_CAST_OK)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flamestrike-failed",
                Acore::StringFormat("result={} retry={}ms", static_cast<uint32>(result), kFlamestrikeRetryMs));
            return false;
        }
        _flame = CastState();
        _flame.active = true;
        _flame.startedMs = _clockMs;
        Mechanic::NoteNextCastIn(me, SPELL_DN_FLAMESTRIKE, Ms(kFlamestrikeBeat.everyMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flamestrike",
            Acore::StringFormat("pct={:.0f} cast={}ms", kFlamestrikePct, kFlamestrikeCastMs));
        return true;
    }

    // The cast ended without a hook (it went off, or he lost it): it landed on every player.
    void UpdateFlamestrike()
    {
        if (!_flame.active || me->FindCurrentSpellBySpellId(SPELL_DN_FLAMESTRIKE))
            return;
        if (_clockMs < _flame.startedMs + kCastStartGraceMs)
            return;     // the cast has not taken yet
        _flame = CastState();
        ++_flamestrikes;
        uint32 riders = 0;
        if (uint32 const rider = RiderFor(DoanHit::Flamestrike))
            for (Player* player : FightPlayers())
            {
                me->CastSpell(player, rider, true);
                ++riders;
            }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flamestrike-landed",
            Acore::StringFormat("flamestrikes={} riders={}", _flamestrikes, riders));
    }

    void FlamestrikeInterrupted()
    {
        _flame = CastState();
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        ++_interrupts;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flamestrike-interrupted",
            Acore::StringFormat("interrupts={}", _interrupts));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (LIB "Boss data")
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order: the Arcane Anchors (everyone: the tank is free while he is bubbled). Doan himself is ignored while
    // the bubble is up (immune), and the look stalkers always. Interrupt list: Righteous Flamestrike (heroic,
    // expected). Dispel and purge lists: none (Icy Death is D8H's, added through DescribeExtra).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_SM_ARCANE_ANCHOR, 1, BossMechanics::Who::Any);
        d.ignores.emplace_back(NPC_DOAN, BossMechanics::Condition::HasAura(SPELL_DN_ARCANE_BUBBLE));
        d.ignores.emplace_back(NPC_SM_STALKER);
        if (_heroic)
            d.interrupts.emplace_back(NPC_DOAN, SPELL_DN_FLAMESTRIKE, 3, Ms(kFlamestrikeBeat.everyMs));
        if (_hardMode)
            _hardMode->DescribeExtra(*this, d);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DoanFight (the hard mode's view of the pull, DoanFight.h)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Doan() override { return me; }
    bool Heroic() const override { return _heroic; }
    DoanHardMode* ActiveHardMode() override { return _hardMode.get(); }

    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() override
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

    uint64 ClockMs() const override { return _clockMs; }
    uint32 BubblesStarted() const override { return _bubblesStarted; }
    uint32 BubblesBroken() const override { return _bubblesBroken; }
    uint32 BubblesMissed() const override { return _bubblesMissed; }
    bool BubbleActive() const override { return _bubble.active; }
    bool Overloaded() const override { return _overloadedUntilMs != 0; }

    std::vector<ObjectGuid> LiveAnchors() const override
    {
        std::vector<ObjectGuid> out;
        for (ObjectGuid const& guid : _bubble.anchors)
            if (Creature const* anchor = ObjectAccessor::GetCreature(*me, guid))
                if (anchor->IsAlive())
                    out.push_back(guid);
        return out;
    }

    bool AddBubbleAnchor(Creature* unit) override
    {
        if (!_bubble.active || !unit || !unit->IsAlive()
            || std::find(_bubble.anchors.begin(), _bubble.anchors.end(), unit->GetGUID()) != _bubble.anchors.end())
            return false;
        _bubble.anchors.push_back(unit->GetGUID());
        Log("bubble-anchor-added", Acore::StringFormat("entry={} anchors={}", unit->GetEntry(),
            _bubble.anchors.size()));
        return true;
    }

    void AddNextBubbleAnchors(uint32 n, char const* why) override
    {
        _pendingAnchors += n;
        Log("anchors-next", Acore::StringFormat("added={} pending={} why={}", n, _pendingAnchors, why ? why : "?"));
    }

    Position AnchorSpot(uint32 index) const override
    {
        Point3 const& spot = kAnchorSpots[index < kAnchorSpotCount ? index : kAnchorSpotCount - 1];
        return Position(spot.x, spot.y, spot.z, 0.f);
    }

    uint32 AnchorsRaised() const override { return _bubble.anchorsRaised; }

    Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs) override
    {
        return despawnMs ? me->SummonCreature(entry, at, TEMPSUMMON_TIMED_DESPAWN, despawnMs)
            : me->SummonCreature(entry, at, TEMPSUMMON_MANUAL_DESPAWN);
    }

    // A mechanic of the fight (an Explosion, a Mark, a patch, a pool, a hit): kept to cancel it on a reset. Never
    // truncated: Scorched patches and the hard mode's pools (PoolLifeMs 0) live all fight and are among the early
    // handles, so dropping the oldest would drop them. A handle is a few bytes and Cancel on a resolved one is a no-op.
    void Track(MechanicHandle handle) override
    {
        if (handle)
            _live.push_back(handle);
    }

    void Log(char const* mechanic, std::string const& detail) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    uint32 RiderFor(DoanHit hit) const
    {
        return _hardMode ? _hardMode->RiderFor(*this, hit) : 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm doan` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Bubble,
        Break,
        Detonate,
        Scorched,
        Explosion,
        Mark,
        Flamestrike,
        Seal,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM).
    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!me->IsEngaged())
            return "Doan must be in combat (the picks read his threat list, the mechanics his encounter).";
        switch (mechanic)
        {
            case TestMechanic::Bubble:
                if (_bubble.active || Overloaded())
                    return "The bubble or Overloaded is up already.";
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    me->InterruptNonMeleeSpells(false);
                _flame = CastState();
                StartBubble();
                break;
            case TestMechanic::Break:
                if (!_bubble.active)
                    return "No bubble is up.";
                for (ObjectGuid const& guid : _bubble.anchors)
                    if (Creature* anchor = ObjectAccessor::GetCreature(*me, guid))
                        if (anchor->IsAlive())
                            anchor->KillSelf();
                break;
            case TestMechanic::Detonate:
                if (!_bubble.active)
                    return "No bubble is up.";
                _bubble.endMs = _clockMs;
                break;
            case TestMechanic::Scorched:
                if (!LayScorched())
                    return "No floor spot for a patch.";
                break;
            case TestMechanic::Explosion:
                if (me->HasUnitState(UNIT_STATE_CASTING) || _bubble.active)
                    return "He is casting already.";
                StartExplosion();
                break;
            case TestMechanic::Mark:
                if (!CastMarks(CountsAsPlayer(who) ? who : nullptr))
                    return "No player to mark.";
                break;
            case TestMechanic::Flamestrike:
                if (me->HasUnitState(UNIT_STATE_CASTING) || _bubble.active)
                    return "He is casting already.";
                if (!StartFlamestrike())
                    return "Flamestrike did not start (see the log).";
                break;
            case TestMechanic::Seal:
                if (!_seal.IsSealed())
                    return "The seal is not closed (it closes 3 s after the pull).";
                _seal.PullIn(me);
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} hardmode={} handler={} bubble={} (index {}, anchors {} of {}, "
            "ends in {}ms) overloaded={} started={} broken={} missed={} pending-anchors={} patches={} pools={} "
            "marks={} explosions={} flamestrikes={} interrupts={} seal={} live-handles={}",
            _clockMs / 1000, _heroic ? 1 : 0, _hardModeLit ? 1 : 0, _hardMode ? 1 : 0, _bubble.active ? 1 : 0,
            _bubble.index, AnchorsStanding(), _bubble.anchors.size(),
            _bubble.active && _bubble.endMs > _clockMs ? _bubble.endMs - _clockMs : 0, Overloaded() ? 1 : 0,
            _bubblesStarted, _bubblesBroken, _bubblesMissed, _pendingAnchors, _patches.size(), _poolList.size(),
            _marks, _explosions, _flamestrikes, _interrupts,
            _seal.IsSealed() ? "sealed" : _seal.IsClosing() ? "closing" : "open", _live.size());
    }

private:
    struct BubbleState
    {
        bool active = false;
        uint32 index = 0;
        uint64 endMs = 0;
        uint32 castMs = kDetonationCastMs;  // this bubble's Detonation length (DetonationCastMs)
        uint32 anchorsRaised = 0;           // D8's own anchors this bubble
        std::vector<ObjectGuid> anchors;    // every unit the bubble waits for (D8's and the hard mode's)
    };

    struct CastState
    {
        bool active = false;
        uint64 startedMs = 0;
    };

    struct PoolSpot
    {
        Position at;
        uint64 untilMs = 0;                 // 0: the rest of the fight
    };

    static constexpr uint32 kAnchorCorpseMs = 3000;

    // The players inside the chamber now (Detonation's targets: "every player in the sealed chamber").
    std::vector<Player*> ChamberPlayers() const
    {
        std::vector<Player*> out;
        Arena const arena = DoanArena();
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!CountsAsPlayer(player))
                continue;
            if (arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                out.push_back(player);
        }
        return out;
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnDoan(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_arcanist_doan_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    static boss_arcanist_doan_rework* From(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_arcanist_doan_rework*>(boss->AI());
    }

    // The pull's state: nothing registered, no summon, no aura of his on him or anyone, the seal open (Reset, evade,
    // death). The hard mode undoes its own changes in OnEnd first.
    void Cleanup(bool dead, char const* why)
    {
        ++_generation;
        _flame = CastState();       // before the engine interrupts a cast, so it never reads as a kick
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, dead);
            _hardMode.reset();
        }
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        summons.DespawnAll();
        _bubble = BubbleState();
        _overloadedUntilMs = 0;
        for (uint32 const spell : { uint32(SPELL_DN_ARCANE_BUBBLE), uint32(SPELL_DN_OVERLOADED) })
            me->RemoveAurasDueToSpell(spell);
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_DN_MARK);
        _seal.Release(me, why);
        _arena.Reset();
        _bubbleClock.Stop();
        _explosionClock.Stop();
        _markClock.Stop();
        _flameClock.Stop();
        _patches.clear();
        _poolList.clear();
        _clockMs = 0;
        _bubblesStarted = 0;
        _bubblesBroken = 0;
        _bubblesMissed = 0;
        _pendingAnchors = 0;
        _marks = 0;
        _pools = 0;
        _explosions = 0;
        _flamestrikes = 0;
        _interrupts = 0;
        _engaged = false;
        _hardModeLit = false;
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::SealedArena _seal;
    std::unique_ptr<DoanHardMode> _hardMode;
    BeatClock _bubbleClock;
    BeatClock _explosionClock;
    BeatClock _markClock;
    BeatClock _flameClock;
    BubbleState _bubble;
    CastState _flame;
    std::vector<Position> _patches;
    std::vector<PoolSpot> _poolList;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;                // ms since the pull: every timer of the fight
    uint64 _overloadedUntilMs = 0;      // 0: not Overloaded
    uint32 _generation = 0;             // bumped by every cleanup: a stale callback does nothing
    uint32 _bubblesStarted = 0;
    uint32 _bubblesBroken = 0;
    uint32 _bubblesMissed = 0;
    uint32 _pendingAnchors = 0;         // the hard mode's extra anchors for the next bubble
    uint32 _marks = 0;
    uint32 _pools = 0;
    uint32 _explosions = 0;
    uint32 _flamestrikes = 0;
    uint32 _interrupts = 0;
    bool _heroic = false;
    bool _hardModeLit = false;
    bool _engaged = false;
};

// Arcane Anchor 300919 (DN1): a kill target that stands on its spot, never moves or attacks, and channels its beam
// into Doan's bubble while it stands (re-cast when the channel drops). Doan despawns it when the bubble ends; it
// never evades on its own (its fight is his).
struct npc_sm_arcane_anchor : public ScriptedAI
{
    explicit npc_sm_arcane_anchor(Creature* creature) : ScriptedAI(creature) { }

    void InitializeAI() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetCombatMovement(false);
        ScriptedAI::InitializeAI();
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        _beamCheckMs = kBeamCheckMs;
    }

    void AttackStart(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsAlive())
            return;
        if (_beamCheckMs > diff)
        {
            _beamCheckMs -= diff;
            return;
        }
        _beamCheckMs = kBeamCheckMs;
        if (me->GetCurrentSpell(CURRENT_CHANNELED_SPELL))
            return;
        TempSummon* summon = me->ToTempSummon();
        Unit* doan = summon ? summon->GetSummonerUnit() : nullptr;
        if (doan && doan->IsAlive() && doan->HasAura(SPELL_DN_ARCANE_BUBBLE))
            me->CastSpell(doan, SPELL_DN_ANCHOR_BEAM, true);
    }

private:
    static constexpr uint32 kBeamCheckMs = 1000;
    uint32 _beamCheckMs = kBeamCheckMs;
};

namespace
{
    boss_arcanist_doan_rework* FindDoanAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_DOAN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_arcanist_doan_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Doan is not running boss_arcanist_doan_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_arcanist_doan_rework::TestMechanic mechanic, char const* what)
    {
        boss_arcanist_doan_rework* ai = FindDoanAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Doan: {} fired ({}).", what, ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_DOAN, BOSS_DOAN);
    }

    // Handoff section 3.7: `.dbtest sm doan hardmode` arms the hard mode past its trigger (GM).
    bool HandleHardMode(ChatHandler* handler)
    {
        return SmTest::ArmHardMode(handler, BOSS_HERESY);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_arcanist_doan_rework* ai = FindDoanAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Doan: {}", ai->TestState());
        return true;
    }

    bool HandleBubble(ChatHandler* handler)
    {
        return Fire(handler, boss_arcanist_doan_rework::TestMechanic::Bubble,
            "the bubble (DN1: the anchors and the 10 s Detonation bar)");
    }

    bool HandleBreak(ChatHandler* handler)
    {
        return Fire(handler, boss_arcanist_doan_rework::TestMechanic::Break,
            "every anchor of the bubble killed (DN1: Overloaded follows)");
    }

    bool HandleDetonate(ChatHandler* handler)
    {
        return Fire(handler, boss_arcanist_doan_rework::TestMechanic::Detonate,
            "Detonation completed now (DN1: the blast, two patches, one more anchor next time)");
    }

    bool HandleScorched(ChatHandler* handler)
    {
        return Fire(handler, boss_arcanist_doan_rework::TestMechanic::Scorched,
            "a Scorched patch (DN1a: 5 yd, the rest of the fight)");
    }

    bool HandleExplosion(ChatHandler* handler)
    {
        return Fire(handler, boss_arcanist_doan_rework::TestMechanic::Explosion,
            "Arcane Explosion (DN2: a 2 s bar, 10 yd round him)");
    }

    bool HandleMark(ChatHandler* handler)
    {
        return Fire(handler, boss_arcanist_doan_rework::TestMechanic::Mark,
            "a Mark of Righteous Fire on the selected player (DN3: 5 s, 8 yd; heroic a pool)");
    }

    bool HandleFlamestrike(ChatHandler* handler)
    {
        return Fire(handler, boss_arcanist_doan_rework::TestMechanic::Flamestrike,
            "Righteous Flamestrike (DN4: a 2.5 s cast, kick it; any difficulty)");
    }

    bool HandleSeal(ChatHandler* handler)
    {
        return Fire(handler, boss_arcanist_doan_rework::TestMechanic::Seal,
            "the seal's pull-in (DN0: stragglers within 60 yd moved inside)");
    }

    // `.dbtest sm doan <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BossArcanistDoanTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",        HandleInfo,        SEC_GAMEMASTER, Console::No },
            { "hardmode",    HandleHardMode,    SEC_GAMEMASTER, Console::No },
            { "state",       HandleState,       SEC_GAMEMASTER, Console::No },
            { "bubble",      HandleBubble,      SEC_GAMEMASTER, Console::No },
            { "break",       HandleBreak,       SEC_GAMEMASTER, Console::No },
            { "detonate",    HandleDetonate,    SEC_GAMEMASTER, Console::No },
            { "scorched",    HandleScorched,    SEC_GAMEMASTER, Console::No },
            { "explosion",   HandleExplosion,   SEC_GAMEMASTER, Console::No },
            { "mark",        HandleMark,        SEC_GAMEMASTER, Console::No },
            { "flamestrike", HandleFlamestrike, SEC_GAMEMASTER, Console::No },
            { "seal",        HandleSeal,        SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_arcanist_doan_rework()
{
    RegisterDungeonReworkCreatureAI(boss_arcanist_doan_rework, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sm_arcane_anchor, ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("doan", BossArcanistDoanTestCommands());
}
