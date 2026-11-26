/*
 * mod-dungeon-bosses, the shared dungeon kit (Zul'Farrak WP-KT, handoff section 3.11, F57): a boss who fights at the
 * edge of his arena, promoted from Ragefire Chasm's RagefireChasmKit.h (Bazzalan, Taragaman) without a change of
 * behavior. Ragefire keeps its own copy (RagefireChasmRework::ArenaEdge); new dungeons use this one. The pure rules are
 * DungeonKitArenaEdgeLogic.h (NextEdgeStep and friends).
 *
 *   SelfLeash    the guard of his own arena: it keeps him on it and judges nobody else (no switch, no hold, no
 *                "nobody inside" evade)
 *   ReachLeash   the guard of the arena grown by the band he reaches (EdgeReachArena): it turns him to a target
 *                inside, holds him, and counts the nobody-inside time; never his own leash
 *   ArenaEdge    how he fights at the edge: a target on the band is fought from the edge, no chase onto it; off his
 *                arena he walks back; the engine's step back from a target inside him never takes him off
 *
 * In short (Ragefire's Bazzalan, written against the kit):
 *
 *     using namespace DungeonKit::EdgeFight;
 *     boss_x(Creature* c) : BossAI(c, BOSS_X),
 *         _arena(XArena(), SelfLeash(DungeonKit::LeashPreset("zf x arena", spec))),
 *         _reach(EdgeReachArena(XArena(), kXPolygon, zMin, zMax), ReachLeash(DungeonKit::LeashPreset("zf x arena",
 *             spec))),
 *         _edge(kXPolygon, [this](Vec2 p, float z) { return Floor(p, z); }) { }
 *     Reset / EnterEvadeMode / JustDied: _arena.Reset(); _reach.Reset(); _edge.Reset();
 *     JustEngagedWith: _arena.Engage(me); _reach.Engage(me);
 *     UpdateAI: if (!UpdateVictim()) return; _edge.HoldBackstep(me);       (every tick of the fight, bars too)
 *               if (!_arena.Update(me, diff) || !_reach.Update(me, diff)) return;
 *               if (fights freely) _edge.Update(me, _arena, _reach);
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ARENA_EDGE_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ARENA_EDGE_H

#include "ArenaGuard.h"
#include "Define.h"
#include "DungeonKitArenaEdgeLogic.h"
#include <functional>
#include <optional>
#include <span>
#include <vector>

class Creature;

namespace DungeonKit::EdgeFight
{
    // `base` (a LeashPreset, say) as the guard of his own arena: no switch, no hold, no nobody-inside evade.
    ArenaGuardOptions SelfLeash(ArenaGuardOptions base);
    // `base` as the guard of his reach arena: never his own leash; " reach" is added to the log prefix.
    ArenaGuardOptions ReachLeash(ArenaGuardOptions base);

    // A boss at the edge of his arena. HoldBackstep every tick of the fight (a bar does not stop the engine's step
    // back), Update whenever he fights freely, Reset from Reset / EnterEvadeMode / JustDied.
    class ArenaEdge
    {
    public:
        // The floor height at a point near height `z`; nothing: none there.
        using FloorFn = std::function<std::optional<float>(Vec2, float z)>;

        ArenaEdge() = default;
        // The polygon is copied.
        ArenaEdge(std::span<Vec2 const> polygon, FloorFn floor);

        void Configure(std::span<Vec2 const> polygon, FloorFn floor);

        void HoldBackstep(Creature* boss) const;
        void Update(Creature* boss, ArenaGuard const& arena, ArenaGuard const& reach);
        void Reset();

        std::span<Vec2 const> Polygon() const { return _polygon; }

    private:
        static constexpr uint32 kRepathMs = 500;
        static constexpr float kRepathYd = 1.f;
        static constexpr float kThereYd = 0.1f;

        std::vector<Vec2> _polygon;
        FloorFn _floor;
        Vec2 _spot{};               // the last walk
        uint32 _walkedAtMs = 0;     // ... and when (0: none)
        bool _held = false;         // no chase runs
    };
}

#endif
