/*
 * mod-dungeon-bosses, Ragefire Chasm: the engine glue of the Ragefire Chasm skeleton (WP-S0; handoff section 3.2). The
 * pure half is RagefireChasmRework.h; the shared kit (src/Kit/) is under all of it.
 *
 *   LeashOptions          the arena guard of every Ragefire Chasm boss: the arena leash, no grips; the boss never
 *                         chases a victim off his arena (he turns to the top-threat unit on it; nobody there: he holds
 *                         at the edge), evades when he has been off it himself for kLeashBossGraceMs, and evades when
 *                         nobody in combat with him has been on it for kLeashNoTargetMs. The Scarlet Monastery values
 *                         through the kit's DungeonKit::LeashPreset (handoff section 1 #9). Oggleflint and Jergosh
 *                         use it as it is.
 *   SelfLeash, ReachLeash the two halves of it for Bazzalan and Taragaman, who fight at their edge: the first keeps
 *                         himself on his arena and judges nobody else, the second (on the arena grown by the band he
 *                         reaches) turns, holds and counts the nobody-inside time.
 *   ArenaEdge             ... and how they do it: a target on the band is fought from the edge, no chase onto it; off
 *                         his arena he walks back; the engine's step back from a target inside him never takes him
 *                         off. The rules are RagefireChasmRework.h NextEdgeStep.
 *   OnBossPull            the pull line of a reworked boss: "rfc <boss> pull health=<max> heroic=<0|1> hardmode=<0|1>"
 *                         (section 3.5). Ragefire Chasm is not flex: no count is held.
 *   <Boss>FloorBounds     the bots' hard bounds (`.Within(...)`, section 3.5 rule 12): the boss's leash arena with its
 *                         z band, as a mod-boss-mechanics SpotBounds.
 *   ApplyTaragamanGate    the dormant state of Taragaman (section 3.2 item 3): SetImmuneToAll, REACT_PASSIVE and
 *                         UNIT_FLAG_NOT_SELECTABLE while DATA_TARAGAMAN_DORMANT is set, cleared otherwise. The
 *                         instance calls it on his create and on every slot change; his AI's Reset calls it too, so an
 *                         evade, a wipe or a respawn never restores an attackable state behind a closed gate and never
 *                         closes an open one.
 *
 * A Ragefire Chasm boss, in short (the S0 stubs already do this):
 *
 *     boss_x_rework(Creature* c) : BossAI(c, BOSS_X), _arena(XArena(), LeashOptions("x")) { }
 *     Reset:           _Reset(); _arena.Reset();                        (Taragaman: ApplyTaragamanGate(me) last)
 *     JustEngagedWith: BossAI::JustEngagedWith(who); if (!me->IsEngaged()) return;
 *                      OnBossPull(me, "x"); Mechanic::BeginEncounter(me, { bossStateId = BOSS_X }); _arena.Engage(me);
 *     UpdateAI:        me->SetAssistanceTimer(0);      (no assist calls, section 7 #12 A: the template's flag stops
 *                                                      only the first; every tick: Attack() sets the timer again)
 *                      if (!UpdateVictim()) return; if (!_arena.Update(me, diff)) return; ...
 *     EnterEvadeMode / JustDied: _arena.Reset();
 *
 * The instance (instance_ragefire_chasm_rework.cpp) owns the gate, the hard mode flag, the kill slot and the loot bit;
 * a boss reads them with GetData (RagefireChasmRework.h RfcData).
 */

#ifndef MOD_DUNGEON_BOSSES_RAGEFIRE_CHASM_KIT_H
#define MOD_DUNGEON_BOSSES_RAGEFIRE_CHASM_KIT_H

#include "ArenaGuard.h"
#include "Define.h"
#include "MechanicRegistry.h"
#include "RagefireChasmRework.h"
#include <functional>
#include <optional>
#include <span>
#include <string>
#include <utility>

class Creature;

namespace RagefireChasmRework
{
    uint32 constexpr kLeashNoTargetMs = 10000;      // evade after 10 s with no target inside
    uint32 constexpr kLeashBossGraceMs = 2000;      // the boss himself off it this long (a leap that ends outside does
                                                    // not reset him at once)
    bool constexpr kLeashSwitchToInside = true;

    // The arena guard options of a Ragefire Chasm boss; `boss` names the log prefix "rfc <boss> arena".
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss);

    // The same, split for a boss with an ArenaEdge.
    DungeonKit::ArenaGuardOptions SelfLeash(std::string const& boss);
    DungeonKit::ArenaGuardOptions ReachLeash(std::string const& boss);

    // A boss at the edge of his arena. HoldBackstep every tick of the fight (a bar does not stop the engine's step
    // back), Update whenever he fights freely.
    class ArenaEdge
    {
    public:
        // The floor height at a point near height `z`; nothing: none there.
        using FloorFn = std::function<std::optional<float>(Vec2, float z)>;

        ArenaEdge(std::span<Vec2 const> polygon, FloorFn floor) : _polygon(polygon), _floor(std::move(floor)) { }

        void HoldBackstep(Creature* boss) const;
        void Update(Creature* boss, DungeonKit::ArenaGuard const& arena, DungeonKit::ArenaGuard const& reach);
        void Reset();

    private:
        static constexpr uint32 kRepathMs = 500;
        static constexpr float kRepathYd = 1.f;
        static constexpr float kThereYd = 0.1f;

        std::span<Vec2 const> _polygon;
        FloorFn _floor;
        Vec2 _spot{};               // the last walk
        uint32 _walkedAtMs = 0;     // ... and when (0: none)
        bool _held = false;         // no chase runs
    };

    // The pull of a reworked boss, from JustEngagedWith once the boss is engaged.
    void OnBossPull(Creature* boss, char const* bossKey, bool hardMode = false);

    // The bots' bounds of a boss's mechanics.
    BossMechanics::SpotBounds BoundsOf(Arena const& arena);
    BossMechanics::SpotBounds OggleflintFloorBounds();
    BossMechanics::SpotBounds JergoshFloorBounds();
    BossMechanics::SpotBounds BazzalanFloorBounds();
    BossMechanics::SpotBounds TaragamanFloorBounds();

    // Taragaman's dormant state from the instance's DATA_TARAGAMAN_DORMANT. Idempotent; does nothing to a dead unit or
    // outside the rework instance. True when he is dormant now.
    bool ApplyTaragamanGate(Creature* taragaman);
}

#endif
