/*
 * mod-dungeon-bosses, Deadmines: VanCleef's hard mode, Burn It Down (WP-B9). Build spec: DM 'Hard mode: Burn It Down'
 * and Build spec VC10-VC13; handoff sections 3.4 (VC10-VC13), 3.7, 3.8, 3.10 gap 6, 6 (solver cost).
 *
 *   The keg      go_dm_powder_keg (301000, heroic only, spawnMask 2, at the sterncastle face): a use is accepted on
 *                heroic, with VanCleef alive, visible and out of combat, the encounter open and the hard mode unlit;
 *                otherwise the keg is not selectable (polled each second) and a click is refused with a notice. A
 *                use sets DATA_HARD_MODE 1 (saved by the instance), pulls VanCleef onto the user and lights the fuse
 *                (DoAction ACTION_HARD_MODE_LIT -> OnLit): 500k health, yell 7, the 3:00 clock aura on the players.
 *   VC10 Fire front   a stripe 2.73 yd deep across the deck (rail to rail) every 10 s from 5 s, the first at the keg,
 *                each just bow-ward of the last; 2 s marker, 30% Fire + 1 Weakened on landing. The deck behind the
 *                front burns 10% Fire per second: one merged rectangle (sterncastle face to the front), replaced at
 *                each landing (handoff section 6: one persistent zone for all 18 stripes; the old one is cancelled
 *                500 ms later so no tick is lost). The side walkways aft of the sterncastle face burn as one zone of
 *                their own from the first landing (else they are a safe spot the front never reaches).
 *   VC11 Powder below every 10 s from 10 s: a 6 yd blast on a random deck cell ahead of the front, never within 6 yd
 *                of a player (skipped when none), 2 s sparking marker, 40% Fire + 1 Weakened, then 15 s of burning
 *                planks at 10% Fire per second.
 *   VC12 Mainmast    at 2:00, yell 8 and a 4 s creak: a 6 yd line across the deck just ahead of the front, 60%
 *                Physical; then the burning mast (gameobject 301002, display 90020, lying across the deck: no fall
 *                animation exists, it appears fallen as the creak ends) and its wall, 10% Fire per second, clipped to
 *                the part still ahead of the front (never two burns on one spot).
 *   VC13 Explosion   yell 9 at 2:45; at 3:00 every player on the ship dies and VanCleef evades (Reset ->
 *                OnReset: 340k, DATA_HARD_MODE 0, the keg usable again). A wipe resets the same way.
 *
 * The run's state lives in boss_edwin_vancleef_rework (HardMode::State); the boss file calls HardMode::Script from
 * the hooks WP-B8 left. Every mechanic firing logs one INFO line, "dm-pilot hardmode <mechanic> ...", in
 * module.dungeonbosses. `.dmtest hardmode <sub>` fires one on demand.
 */

#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DeadminesKit.h"
#include "DeadminesTestCommand.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "HardModeLogic.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "Pet.h"
#include "Player.h"
#include "Random.h"
#include "TemporarySummon.h"
#include "VanCleefLogic.h"
#include "WorldSession.h"
#include <algorithm>
#include <list>
#include <optional>
#include <vector>

using namespace Acore::ChatCommands;
using namespace DeadminesRework;
using namespace HardMode;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";
    constexpr uint32 kKegPollMs = 1000;
    constexpr float kCleanupRangeYd = 150.f;    // the ship is about 111 yd long: covers it from anywhere on board
    // The mast model (HF_BurningShip_Mast.M2) stands upright with its origin at its middle: pitched 90 degrees about
    // the map x axis (the keel) it lies across the deck (WP-V report).
    constexpr float kMastQuatX = 0.70710678f;
    constexpr float kMastQuatW = 0.70710678f;
    constexpr float kMastLift = 1.f;            // its centre above the deck
    // Where the explosion looks go off (along the centreline).
    constexpr std::array<float, 3> kExplosionX{ -62.f, -80.f, -98.f };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // Time left until the explosion, plus a margin, for everything that burns "for the rest of the fight".
    uint32 RemainingMs(State const& state)
    {
        return (state.elapsedMs < kTimerMs ? kTimerMs - state.elapsedMs : 0) + 1000;
    }

    Position AtDeck(Vec2 p)
    {
        return Position(p.x, p.y, DeckZ(p.x));
    }

    // A deck point at its ground height (from the slope estimate).
    Position AtGround(Creature const* probe, Vec2 p)
    {
        float z = DeckZ(p.x) + 2.f;
        probe->UpdateAllowedPositionZ(p.x, p.y, z);
        return Position(p.x, p.y, z);
    }

    // An invisible stalker (300429) for a look, owned by nobody (never zoned into combat, never on a threat list);
    // it despawns by itself after `lifeMs`, and OnReset / OnDied sweep the ship for leftovers.
    Creature* SummonStalker(Creature* owner, Position const& at, uint32 lifeMs)
    {
        Map* map = owner ? owner->GetMap() : nullptr;
        if (!map)
            return nullptr;
        return map->SummonCreature(NPC_DM_POWDER_STALKER, at, nullptr, lifeMs);
    }

    // The players the fight is about: alive, not a GM, on this map.
    std::vector<Player*> FightPlayers(Map* map)
    {
        std::vector<Player*> out;
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsAlive() && player->IsInWorld() && !player->IsGameMaster())
                out.push_back(player);
        }
        return out;
    }

    // Create health is the base the engine rebuilds max health from (Creature::SelectLevel, UpdateMaxHealth), so a
    // stat refresh keeps the new number.
    void SetBossHealth(Creature* boss, uint32 health)
    {
        boss->SetCreateHealth(health);
        boss->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        boss->UpdateMaxHealth();
        boss->SetHealth(boss->GetMaxHealth());
    }

    GameObject* FindKeg(WorldObject* from)
    {
        InstanceScript* instance = from ? from->GetInstanceScript() : nullptr;
        return instance ? instance->GetGameObject(DATA_POWDER_KEG_GUID) : nullptr;
    }

    // Everything the run left on the ship: stalkers, the mast, the clock auras.
    void SweepShip(Creature* boss)
    {
        std::list<Creature*> stalkers;
        boss->GetCreatureListWithEntryInGrid(stalkers, NPC_DM_POWDER_STALKER, kCleanupRangeYd);
        for (Creature* stalker : stalkers)
            stalker->DespawnOrUnsummon();
        std::list<GameObject*> masts;
        boss->GetGameObjectListWithEntryInGrid(masts, GO_DM_MAINMAST, kCleanupRangeYd);
        for (GameObject* mast : masts)
            mast->DespawnOrUnsummon();
        if (Map* map = boss->GetMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    player->RemoveAurasDueToSpell(SPELL_DM_HARD_MODE_TIMER);
    }

    // One burning look per point, for `lifeMs`.
    void BurningLooks(Creature* boss, float x, uint32 lifeMs)
    {
        for (float y : kBurningLookY)
            if (Creature* stalker = SummonStalker(boss, AtGround(boss, { x, y }), lifeMs))
                stalker->CastSpell(stalker, SPELL_BURNING_LOOK, true);
    }

    DeadminesKit::LingerSpec BurnSpec(uint32 durationMs, uint32 tag)
    {
        DeadminesKit::LingerSpec burn;
        burn.duration = Ms(durationMs);
        burn.tick = Ms(kBurnTickMs);
        burn.pct = kBurnPct;
        burn.school = SPELL_SCHOOL_FIRE;
        burn.spellId = SPELL_BURNING_DECK_TICK;
        burn.slow = true;                       // the shared "Standing in it hurts" rider of every lingering zone
        burn.tag = tag;
        return burn;
    }

    BossMechanics::ZoneSpec StripShape(Strip const& s)
    {
        return BossMechanics::Shapes::LineFacing(AtDeck(s.from), s.facing, s.length, s.width);
    }

    void CancelHandle(Creature* boss, uint32& id)
    {
        if (id)
            Mechanic::Cancel(boss, BossMechanics::MechanicHandle{ id });
        id = 0;
    }

    // A replaced zone is not cancelled at once: creature AI runs before the registry's tick, so its pass due at this
    // landing would be dropped, and the new zone's first pass is one tick away (a 2 s gap). Update cancels it
    // kRetireDelayMs later, after that pass and before the new zone's first.
    void Retire(Creature* boss, State& state, uint32& live, uint32& retired)
    {
        CancelHandle(boss, retired);    // one left from an earlier landing: its overlap is long over
        retired = live;
        live = 0;
        if (retired)
            state.retireAtMs = state.elapsedMs + kRetireDelayMs;
    }

    void CancelBurns(Creature* boss, State& state)
    {
        CancelHandle(boss, state.burntDeckHandle);
        CancelHandle(boss, state.wallHandle);
        CancelHandle(boss, state.walkwayHandle);
        CancelHandle(boss, state.retiredDeckHandle);
        CancelHandle(boss, state.retiredWallHandle);
        state.retireAtMs = 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC10 Fire front
    // ----------------------------------------------------------------------------------------------------------------
    BossMechanics::MechanicHandle FrontStripe(Creature* boss, uint32 k)
    {
        Strip const s = StripeRect(k);
        BossMechanics::MechanicHandle const h = Mechanic::Line(boss, AtDeck(s.from), s.facing, s.length, s.width,
            Ms(kFrontWarnMs)).Damage(kFrontPct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_FIRE_FRONT_HIT).Weakened()
            .Tag(TAG_FIRE_FRONT);
        LOG_INFO(kLog, "dm-pilot hardmode fire-front stripe={} x={:.1f}..{:.1f} depth={:.2f} warn={}ms registered={}",
            k, s.xHi, s.xLo, s.width, kFrontWarnMs, h.IsValid());
        return h;
    }

    // The burning wall: only the part ahead of the front. Re-registered when the front eats into it.
    void RefreshWall(Creature* boss, State& state)
    {
        if (!state.mastDown)
            return;
        float const front = FrontX(state.stripesLanded);
        if (state.wallHandle && front >= state.mast.xHi)
            return;     // the front has not reached it: unchanged
        Retire(boss, state, state.wallHandle, state.retiredWallHandle);
        std::optional<Strip> const wall = WallAhead(state.mast, front);
        if (!wall)
        {
            LOG_INFO(kLog, "dm-pilot hardmode mainmast wall burnt-over front-x={:.1f}", front);
            return;
        }
        state.wallHandle = DeadminesKit::Linger(boss, StripShape(*wall), BurnSpec(RemainingMs(state), TAG_MAINMAST))
            .Id();
        LOG_INFO(kLog, "dm-pilot hardmode mainmast wall x={:.1f}..{:.1f} registered={}", wall->xHi, wall->xLo,
            state.wallHandle != 0);
    }

    // The burning deck: one rectangle from the sterncastle face to the front, replacing the last one.
    void RefreshBurntDeck(Creature* boss, State& state)
    {
        std::optional<Strip> const deck = BurntDeck(state.stripesLanded);
        if (!deck)
            return;
        Retire(boss, state, state.burntDeckHandle, state.retiredDeckHandle);
        state.burntDeckHandle = DeadminesKit::Linger(boss, StripShape(*deck),
            BurnSpec(RemainingMs(state), TAG_FIRE_FRONT)).Id();
    }

    // The aft walkways beside the sterncastle: one zone for the rest of the fight from stripe 0's landing.
    void BurnAftWalkways(Creature* boss, State& state)
    {
        if (state.walkwayHandle)
            return;
        Strip const walkways = AftWalkways();
        state.walkwayHandle = DeadminesKit::Linger(boss, StripShape(walkways),
            BurnSpec(RemainingMs(state), TAG_FIRE_FRONT)).Id();
        LOG_INFO(kLog, "dm-pilot hardmode aft-walkways burning x={:.1f}..{:.1f} registered={}", walkways.xHi,
            walkways.xLo, state.walkwayHandle != 0);
    }

    void FrontLanded(Creature* boss, State& state, uint32 k)
    {
        state.stripesLanded = std::max(state.stripesLanded, k + 1);
        RefreshBurntDeck(boss, state);
        RefreshWall(boss, state);
        if (k == 0)
            BurnAftWalkways(boss, state);
        BurningLooks(boss, StripeRect(k).CenterX(), RemainingMs(state));
        LOG_INFO(kLog, "dm-pilot hardmode fire-front landed stripes={} front-x={:.1f} burning={:.1f}yd registered={}",
            state.stripesLanded, FrontX(state.stripesLanded), kFrontStartX - FrontX(state.stripesLanded),
            state.burntDeckHandle != 0);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC11 Powder below
    // ----------------------------------------------------------------------------------------------------------------

    // One blast at `spot`: the registry blast and its burning planks, the stalker's sparks, then its blast look.
    void PowderAt(Creature* boss, Vec2 spot, uint32 index)
    {
        Position const at = AtGround(boss, spot);
        DeadminesKit::ImpactSpec blast;
        blast.shape = BossMechanics::Shapes::Circle(at, kPowderRadius);
        blast.warn = Ms(kPowderWarnMs);
        blast.pct = kPowderPct;
        blast.school = SPELL_SCHOOL_FIRE;
        blast.spellId = SPELL_POWDER_BLAST_HIT;
        blast.weakened = true;
        blast.tag = TAG_POWDER;
        BossMechanics::MechanicHandle const h =
            DeadminesKit::ImpactThenLinger(boss, blast, BurnSpec(kPowderBurnMs, TAG_POWDER));

        if (Creature* stalker = SummonStalker(boss, at, kPowderWarnMs + kPowderBurnMs + 500))
        {
            stalker->CastSpell(stalker, SPELL_POWDER_SPARKS, true);
            // The stalker's own event queue dies with it, so the capture cannot dangle.
            stalker->m_Events.AddEventAtOffset([stalker]()
            {
                stalker->RemoveAurasDueToSpell(SPELL_POWDER_SPARKS);
                stalker->CastSpell(stalker, SPELL_POWDER_BLAST_VISUAL, true);
                stalker->CastSpell(stalker, SPELL_BURNING_LOOK, true);
            }, Ms(kPowderWarnMs));
        }
        LOG_INFO(kLog, "dm-pilot hardmode powder blast={} at={:.1f},{:.1f} warn={}ms burn={}ms registered={}", index,
            at.GetPositionX(), at.GetPositionY(), kPowderWarnMs, kPowderBurnMs, h.IsValid());
    }

    void Powder(Creature* boss, State const& state, uint32 index)
    {
        std::vector<Vec2> players;
        for (Player* player : FightPlayers(boss->GetMap()))
            if (OnShip(player->GetPositionX(), player->GetPositionY(), player->GetPositionZ()))
                players.push_back({ player->GetPositionX(), player->GetPositionY() });
        std::optional<Strip> const blocked = state.mastFalling ? std::optional<Strip>(state.mast) : std::nullopt;
        std::optional<Vec2> const spot = PickPowderSpot(state.stripesLanded, players, blocked,
            [](uint32 n) { return n ? urand(0, n - 1) : 0u; });
        if (!spot)
        {
            LOG_INFO(kLog, "dm-pilot hardmode powder blast={} skipped (no deck ahead of the front 6 yd from players) "
                "players={} stripes={}", index, players.size(), state.stripesLanded);
            return;
        }
        PowderAt(boss, *spot, index);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC12 The mainmast
    // ----------------------------------------------------------------------------------------------------------------
    BossMechanics::MechanicHandle MastFall(Creature* boss, Strip const& mast)
    {
        if (boss->IsAIEnabled && boss->AI())
            boss->AI()->Talk(YELL_VANCLEEF_MAST);
        BossMechanics::MechanicHandle const h = Mechanic::Zone(boss, StripShape(mast), Ms(kMastWarnMs))
            .Damage(kMastPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_MAINMAST_HIT).Tag(TAG_MAINMAST);
        LOG_INFO(kLog, "dm-pilot hardmode mainmast warn x={:.1f}..{:.1f} creak={}ms registered={}", mast.xHi,
            mast.xLo, kMastWarnMs, h.IsValid());
        return h;
    }

    // The mast lies across the deck, burning (no fall animation exists: it appears as the creak ends).
    void MastDown(Creature* boss, Strip const& mast, uint32 lifeMs)
    {
        Position const at = AtGround(boss, { mast.CenterX(), DeadminesRework::kDeckSternCenter.y });
        GameObject* go = boss->SummonGameObject(GO_DM_MAINMAST, at.GetPositionX(), at.GetPositionY(),
            at.GetPositionZ() + kMastLift, 0.f, kMastQuatX, 0.f, 0.f, kMastQuatW, std::max<uint32>(1, lifeMs / 1000));
        for (float y : kBurningLookY)
        {
            if (Creature* stalker = SummonStalker(boss, AtGround(boss, { mast.CenterX(), y }), lifeMs))
            {
                stalker->CastSpell(stalker, SPELL_MAINMAST_CRASH, true);
                stalker->CastSpell(stalker, SPELL_BURNING_LOOK, true);
            }
        }
        LOG_INFO(kLog, "dm-pilot hardmode mainmast down at={:.1f},{:.1f} object={}", at.GetPositionX(),
            at.GetPositionY(), go != nullptr);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC13 The ship blows
    // ----------------------------------------------------------------------------------------------------------------
    // The evade (here, or already inside the kill loop when the last engaged player dies) runs Reset -> OnReset, which
    // clears `state` and sweeps every stalker off the ship: so the elapsed time is read first and the explosion looks
    // are summoned after the evade (their own 5 s life cleans them up).
    void Explode(Creature* boss, State const* state)
    {
        uint32 const elapsed = state ? state->elapsedMs : 0;
        uint32 killed = 0;
        for (Player* player : FightPlayers(boss->GetMap()))
        {
            if (!OnShip(player->GetPositionX(), player->GetPositionY(), player->GetPositionZ()))
                continue;
            if (Pet* pet = player->GetPet())
                if (pet->IsAlive())
                    Unit::Kill(nullptr, pet);
            // No killer: VanCleef's "And stay down!" (KilledUnit) is not said once per body.
            Unit::Kill(nullptr, player);
            ++killed;
        }
        if (boss->IsAlive() && boss->IsAIEnabled && boss->AI())
            boss->AI()->EnterEvadeMode(CreatureAI::EVADE_REASON_OTHER);

        uint32 looks = 0;
        for (float x : kExplosionX)
        {
            if (Creature* stalker = SummonStalker(boss, AtGround(boss, { x, DeadminesRework::kDeckSternCenter.y }),
                5000))
            {
                stalker->CastSpell(stalker, SPELL_SHIP_EXPLOSION, true);
                ++looks;
            }
        }
        LOG_INFO(kLog, "dm-pilot hardmode explosion killed={} elapsed={}ms looks={}", killed, elapsed, looks);
    }

    // The keg's rule, from the live objects.
    KegRefusal KegCheck(WorldObject const* keg, Creature** outBoss)
    {
        KegInputs in;
        in.heroic = DeadminesKit::IsHeroicMap(keg);
        InstanceScript* instance = keg->GetInstanceScript();
        Creature* boss = instance ? instance->GetCreature(DATA_VANCLEEF_GUID) : nullptr;
        if (outBoss)
            *outBoss = boss;
        in.hardModeLit = instance && instance->GetData(DATA_HARD_MODE);
        in.vanCleefFound = boss != nullptr;
        if (boss)
        {
            in.vanCleefAlive = boss->IsAlive();
            in.vanCleefVisible = boss->IsVisible() && !boss->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            in.vanCleefInCombat = boss->IsInCombat() || boss->IsInEvadeMode();
            EncounterState const state = instance->GetBossState(BOSS_EDWIN_VANCLEEF);
            in.encounterOpen = state == NOT_STARTED || state == FAIL || state == TO_BE_DECIDED;
        }
        return KegUse(in);
    }

    char const* KegNotice(KegRefusal r)
    {
        switch (r)
        {
            case KegRefusal::NotHeroic:
                return "The powder is damp.";
            case KegRefusal::AlreadyLit:
                return "The fuse is already burning.";
            case KegRefusal::NoVanCleef:
            case KegRefusal::VanCleefHidden:
                return "VanCleef is not here to see it.";
            case KegRefusal::VanCleefInCombat:
            case KegRefusal::EncounterClosed:
                return "Not while VanCleef is fighting.";
            default:
                return "";
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// HardMode::Script (declared in HardModeLogic.h; StateOf is defined in boss_edwin_vancleef_rework.cpp)
// ---------------------------------------------------------------------------------------------------------------------
namespace HardMode::Script
{
    void OnLit(Creature* vanCleef, State& state)
    {
        if (!vanCleef || state.lit)
            return;
        state = State{};
        state.lit = true;
        state.baseCreateHealth = vanCleef->GetCreateHealth();
        SetBossHealth(vanCleef, kFuseHealth);
        if (vanCleef->IsAIEnabled && vanCleef->AI())
            vanCleef->AI()->Talk(YELL_VANCLEEF_FUSE);
        uint32 clocks = 0;
        for (Player* player : FightPlayers(vanCleef->GetMap()))
            if (vanCleef->AddAura(SPELL_DM_HARD_MODE_TIMER, player))
                ++clocks;
        LOG_INFO(kLog, "dm-pilot hardmode lit health={} was={} timer={}ms clocks={}", vanCleef->GetMaxHealth(),
            state.baseCreateHealth, kTimerMs, clocks);
    }

    bool Update(Creature* vanCleef, State& state, std::uint32_t diff)
    {
        if (!vanCleef || !state.lit || state.elapsedMs >= kTimerMs)
            return false;
        std::uint32_t const prev = state.elapsedMs;
        state.elapsedMs = std::min<std::uint32_t>(prev + diff, kTimerMs);
        if (state.retireAtMs && state.elapsedMs >= state.retireAtMs)
        {
            CancelHandle(vanCleef, state.retiredDeckHandle);
            CancelHandle(vanCleef, state.retiredWallHandle);
            state.retireAtMs = 0;
        }
        for (Beat const& beat : BeatsBetween(prev, state.elapsedMs))
        {
            switch (beat.kind)
            {
                case BeatKind::FrontMarker:
                    FrontStripe(vanCleef, beat.index);
                    break;
                case BeatKind::FrontLanded:
                    FrontLanded(vanCleef, state, beat.index);
                    break;
                case BeatKind::Powder:
                    Powder(vanCleef, state, beat.index);
                    break;
                case BeatKind::MastWarn:
                    state.mast = MastRect(state.stripesLanded);
                    state.mastFalling = true;
                    MastFall(vanCleef, state.mast);
                    break;
                case BeatKind::MastLanded:
                    state.mastDown = true;
                    MastDown(vanCleef, state.mast, RemainingMs(state));
                    RefreshWall(vanCleef, state);
                    break;
                case BeatKind::OffMyShip:
                    if (vanCleef->IsAIEnabled && vanCleef->AI())
                        vanCleef->AI()->Talk(YELL_VANCLEEF_OFF_MY_SHIP);
                    LOG_INFO(kLog, "dm-pilot hardmode off-my-ship elapsed={}ms", state.elapsedMs);
                    break;
                case BeatKind::Explosion:
                    // Evades him: Reset -> OnReset clears `state`. Nothing may touch it after this.
                    Explode(vanCleef, &state);
                    return true;
            }
        }
        return false;
    }

    void OnReset(Creature* vanCleef, State& state)
    {
        if (!vanCleef)
            return;
        InstanceScript* instance = vanCleef->GetInstanceScript();
        // The instance clears it on VanCleef's NOT_STARTED / FAIL already; this covers a reset without that change.
        if (instance && instance->GetData(DATA_HARD_MODE))
            instance->SetData(DATA_HARD_MODE, 0);
        if (!state.lit)
        {
            state = State{};
            return;
        }
        if (state.baseCreateHealth)
            SetBossHealth(vanCleef, state.baseCreateHealth);
        CancelBurns(vanCleef, state);
        SweepShip(vanCleef);
        if (GameObject* keg = FindKeg(vanCleef))
            keg->SetGoState(GO_STATE_READY);    // the keg's poll makes it selectable again
        LOG_INFO(kLog, "dm-pilot hardmode reset elapsed={}ms stripes={} health={}", state.elapsedMs,
            state.stripesLanded, vanCleef->GetMaxHealth());
        state = State{};
    }

    void OnDied(Creature* vanCleef, State& state)
    {
        if (!vanCleef || !state.lit)
            return;
        CancelBurns(vanCleef, state);
        SweepShip(vanCleef);
        LOG_INFO(kLog, "dm-pilot hardmode killed elapsed={}ms stripes={}", state.elapsedMs, state.stripesLanded);
        state.lit = false;
    }

    bool Light(Creature* vanCleef, Player* who)
    {
        State* state = vanCleef ? StateOf(vanCleef) : nullptr;
        InstanceScript* instance = vanCleef ? vanCleef->GetInstanceScript() : nullptr;
        if (!state || state->lit || !instance || !vanCleef->IsAlive())
            return false;
        // First the flag (saved by the instance), so the engage reads the hard mode plan (no gun lanes).
        instance->SetData(DATA_HARD_MODE, 1);
        if (who)
        {
            vanCleef->EngageWithTarget(who);
            vanCleef->AI()->AttackStart(who);
        }
        vanCleef->AI()->DoAction(VanCleef::ACTION_HARD_MODE_LIT);
        return true;
    }
}

// powder keg gameobject 301000 (heroic only, spawnMask 2): lights the fuse. Bots never use it (no bot action targets a
// GOOBER without loot; see the WP-B9 report); while it cannot be used it is not selectable.
struct go_dm_powder_keg : public GameObjectAI
{
    explicit go_dm_powder_keg(GameObject* go) : GameObjectAI(go) { }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kKegPollMs;
        bool const usable = KegCheck(me, nullptr) == KegRefusal::None;
        bool const flagged = me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (usable && flagged)
            me->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else if (!usable && !flagged)
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        // The use itself only (a report-use follows some clicks); the engine never handles this goober.
        if (reportUse || !player)
            return true;
        Creature* boss = nullptr;
        KegRefusal const why = KegCheck(me, &boss);
        if (why != KegRefusal::None)
        {
            LOG_INFO(kLog, "dm-pilot hardmode keg refused by={} reason={}", player->GetName(), KegRefusalName(why));
            ChatHandler(player->GetSession()).SendNotification(KegNotice(why));
            return true;
        }
        if (!HardMode::Script::Light(boss, player))
            return true;
        me->SetGoState(GO_STATE_ACTIVE);
        me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        LOG_INFO(kLog, "dm-pilot hardmode keg lit by={}", player->GetName());
        return true;
    }

private:
    uint32 _pollMs = 0;
};

namespace
{
    // `.dmtest hardmode <sub>`: VanCleef is the selected one, else the nearest within 200 yd; the GM is the player
    // (`.gm off` to be hit). The hard mode's own spells and zones land on any difficulty here; the numbers are the
    // map's reference row (heroic is the real one).
    Creature* FindVanCleef(ChatHandler* handler, State** state)
    {
        Creature* boss = DeadminesTest::FindBoss(handler, NPC_EDWIN_VANCLEEF);
        if (!boss)
            return nullptr;
        *state = HardMode::Script::StateOf(boss);
        if (!*state)
        {
            handler->SendErrorMessage("Edwin VanCleef does not run boss_edwin_vancleef_rework.");
            return nullptr;
        }
        return boss;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        if (!DeadminesTest::ShowBossInfo(handler, NPC_EDWIN_VANCLEEF, BOSS_BURN_IT_DOWN))
            return false;
        State* state = nullptr;
        if (Creature* boss = FindVanCleef(handler, &state))
        {
            handler->PSendSysMessage("Hard mode: lit {} elapsed {} ms, stripes {}, front x {:.1f}, mast {}, health {}.",
                state->lit, state->elapsedMs, state->stripesLanded, FrontX(state->stripesLanded),
                state->mastDown ? "down" : (state->mastFalling ? "falling" : "standing"), boss->GetMaxHealth());
        }
        return true;
    }

    bool HandleKeg(ChatHandler* handler)
    {
        if (!DeadminesTest::RequireDeadmines(handler))
            return false;
        GameObject* keg = FindKeg(handler->GetPlayer());
        if (!keg)
        {
            handler->SendErrorMessage("No powder keg (it is spawned on heroic only).");
            return false;
        }
        KegRefusal const why = KegCheck(keg, nullptr);
        handler->PSendSysMessage("Powder keg at {:.1f}, {:.1f}, {:.1f}: {} (go state {}).", keg->GetPositionX(),
            keg->GetPositionY(), keg->GetPositionZ(), KegRefusalName(why), uint32(keg->GetGoState()));
        return true;
    }

    // Lights the fuse as if the GM used the keg, skipping the keg's rule (any difficulty, hidden or not).
    bool HandleLight(ChatHandler* handler)
    {
        State* state = nullptr;
        Creature* boss = FindVanCleef(handler, &state);
        if (!boss)
            return false;
        if (!HardMode::Script::Light(boss, handler->GetPlayer()))
        {
            handler->SendErrorMessage("Not lit (already lit, or he is dead).");
            return false;
        }
        if (GameObject* keg = FindKeg(boss))
        {
            keg->SetGoState(GO_STATE_ACTIVE);
            keg->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        }
        handler->SendSysMessage("Burn It Down lit: 500k, the 3:00 clock runs (fire front at 5 s, powder at 10 s).");
        return true;
    }

    // Jumps the clock to `seconds` without firing the beats in between (the next landing burns every stripe up to it;
    // a jump past 2:04 skips the mast).
    bool HandleSkip(ChatHandler* handler, uint32 seconds)
    {
        State* state = nullptr;
        if (!FindVanCleef(handler, &state))
            return false;
        if (!state->lit)
        {
            handler->SendErrorMessage("The hard mode is not lit (.dmtest hardmode light).");
            return false;
        }
        uint32 const target = std::min<uint32>(seconds * 1000, kTimerMs - 1);
        if (target <= state->elapsedMs)
        {
            handler->SendErrorMessage("The clock is already past that.");
            return false;
        }
        state->elapsedMs = target;
        handler->PSendSysMessage("Clock at {} ms.", target);
        return true;
    }

    // One stripe k (default 0) at its real place, with its own 20 s burn (not the merged deck).
    bool HandleFront(ChatHandler* handler, Optional<uint32> stripe)
    {
        State* state = nullptr;
        Creature* boss = FindVanCleef(handler, &state);
        if (!boss)
            return false;
        uint32 const k = std::min<uint32>(stripe.value_or(0), kStripeCount - 1);
        Strip const s = StripeRect(k);
        DeadminesKit::ImpactSpec hit;
        hit.shape = StripShape(s);
        hit.warn = Ms(kFrontWarnMs);
        hit.pct = kFrontPct;
        hit.school = SPELL_SCHOOL_FIRE;
        hit.spellId = SPELL_FIRE_FRONT_HIT;
        hit.weakened = true;
        hit.tag = TAG_FIRE_FRONT;
        BossMechanics::MechanicHandle const h = DeadminesKit::ImpactThenLinger(boss, hit, BurnSpec(20000,
            TAG_FIRE_FRONT));
        LOG_INFO(kLog, "dm-pilot hardmode fire-front stripe={} x={:.1f}..{:.1f} (dmtest) registered={}", k, s.xHi,
            s.xLo, h.IsValid());
        handler->PSendSysMessage("Fire front stripe {}: x {:.1f} to {:.1f}, rail to rail, 2 s, then 20 s burning.", k,
            s.xHi, s.xLo);
        return true;
    }

    // One blast by the placement rule (you are the only player it avoids).
    bool HandlePowder(ChatHandler* handler)
    {
        State* state = nullptr;
        Creature* boss = FindVanCleef(handler, &state);
        if (!boss)
            return false;
        Player* gm = handler->GetPlayer();
        std::vector<Vec2> const players{ { gm->GetPositionX(), gm->GetPositionY() } };
        std::optional<Vec2> const spot = PickPowderSpot(state->stripesLanded, players, std::nullopt,
            [](uint32 n) { return n ? urand(0, n - 1) : 0u; });
        if (!spot)
        {
            handler->SendErrorMessage("Skipped: no deck cell ahead of the front 6 yd from you.");
            return false;
        }
        PowderAt(boss, *spot, 0);
        handler->PSendSysMessage("Powder blast at {:.1f}, {:.1f}: 6 yd, 2 s sparks, then 15 s burning.", spot->x,
            spot->y);
        return true;
    }

    // The mast at the 2:00 spot (or for the current front when lit), its 4 s creak, then the mast and a 30 s wall.
    bool HandleMast(ChatHandler* handler)
    {
        State* state = nullptr;
        Creature* boss = FindVanCleef(handler, &state);
        if (!boss)
            return false;
        Strip const mast = MastRect(state->lit ? state->stripesLanded : StripesLandedBy(kMastMs));
        MastFall(boss, mast);
        // VanCleef's own event queue dies with him, so the capture cannot dangle.
        boss->m_Events.AddEventAtOffset([boss, mast]()
        {
            MastDown(boss, mast, 30000);
            DeadminesKit::Linger(boss, StripShape(mast), BurnSpec(30000, TAG_MAINMAST));
        }, Ms(kMastWarnMs));
        handler->PSendSysMessage("Mainmast: x {:.1f} to {:.1f}, 4 s creak, then the mast and 30 s of burning wall.",
            mast.xHi, mast.xLo);
        return true;
    }

    // The 3:00 explosion now: kills every player on the ship (a GM in .gm on survives) and resets him.
    bool HandleExplode(ChatHandler* handler)
    {
        State* state = nullptr;
        Creature* boss = FindVanCleef(handler, &state);
        if (!boss)
            return false;
        Explode(boss, state);
        handler->SendSysMessage("The ship blew.");
        return true;
    }

    bool HandleReset(ChatHandler* handler)
    {
        State* state = nullptr;
        Creature* boss = FindVanCleef(handler, &state);
        if (!boss)
            return false;
        if (boss->IsAIEnabled && boss->AI())
            boss->AI()->EnterEvadeMode(CreatureAI::EVADE_REASON_OTHER);
        handler->SendSysMessage("VanCleef reset (340k, the keg usable again).");
        return true;
    }

    ChatCommandTable const& HardModeTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "keg",     HandleKeg,     SEC_GAMEMASTER, Console::No },
            { "light",   HandleLight,   SEC_GAMEMASTER, Console::No },
            { "skip",    HandleSkip,    SEC_GAMEMASTER, Console::No },
            { "front",   HandleFront,   SEC_GAMEMASTER, Console::No },
            { "powder",  HandlePowder,  SEC_GAMEMASTER, Console::No },
            { "mast",    HandleMast,    SEC_GAMEMASTER, Console::No },
            { "explode", HandleExplode, SEC_GAMEMASTER, Console::No },
            { "reset",   HandleReset,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_vancleef_hard_mode()
{
    RegisterDeadminesReworkGameObjectAI(go_dm_powder_keg);
    DeadminesTest::RegisterBoss("hardmode", HardModeTestCommands());
}
