/*
 * mod-dungeon-bosses, Shadowfang Keep: Meat Hook (RC1), the engine glue shared by Razorclaw the Butcher (WP-S2) and
 * Baron Silverlaine's Echo of Razorclaw (WP-S3, BS4). Handoff section 3.3 item 3 ("MeatHook.h (S2: hook line and drag;
 * S3's echo)"). The rules (tuning, picks, the once-per-throw memory, the drag speed) are RazorclawLogic.h.
 *
 * One throw:
 *   - picks up to `tuning.lines` distinct non-tanks at least minRangeYd away (none: skipped, nothing cast);
 *   - the thrower faces the first target and casts the 2 s cast bar (205930) with its emote ($n = the first target);
 *   - one registry line per target (DungeonKit::LineStrike: width, overrun, excluded end, clipped at `clip`'s walls),
 *     dealing `pct` through 205931 with Weakened; spell_sfk_meat_hook_once keeps a unit in two lines of one throw to
 *     one hit;
 *   - every unit a line hits is dragged (DungeonKit::JumpTo, look 205932: the chain and the blood) to `frontYd` in
 *     front of the thrower, toward its victim (the tank's side, where Butcher's Cut lands), in about dragMs; with
 *     bleedPct it also gets Hung to Bleed (205933, base point 0 = RefFlat(BleedTickPct) per tick).
 *
 * What S3's echo calls (the echo is a Creature; Silverlaine's encounter can own the lines):
 *
 *     MeatHook::ThrowSpec spec;
 *     spec.tuning = Razorclaw::HookFor(false);          // BS4: one line, no bleed, on both difficulties
 *     spec.clip = &_hall;                               // a member Arena (SilverlaineArena())
 *     spec.logBoss = "silverlaine";
 *     spec.logMechanic = "echo-meat-hook";
 *     MeatHook::ThrowResult r = MeatHook::Throw(echo, spec, silverlaine);   // owner: Silverlaine's encounter
 *     ...
 *     MeatHook::Forget(silverlaine);                    // on reset / death (the lines' owner keys the memory)
 *
 * The spell script is registered once, by AddSC_boss_razorclaw_rework (MeatHook::AddSC_meat_hook); S3 needs no
 * registration of its own.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_MEAT_HOOK_H
#define MOD_DUNGEON_BOSSES_SFK_MEAT_HOOK_H

#include "BossMechanics.h"
#include "DungeonKitArena.h"
#include "ObjectGuid.h"
#include "RazorclawLogic.h"
#include <optional>
#include <vector>

class Creature;
class Unit;

namespace MeatHook
{
    struct ThrowSpec
    {
        Razorclaw::HookTuning tuning;
        uint32 castBarSpell = Razorclaw::SPELL_RC_MEAT_HOOK_CAST;   // 0: no bar (the line still warns)
        std::optional<uint8> emote;                                  // the thrower's text group, $n = first target
        DungeonKit::Arena const* clip = nullptr;                     // lines stop at these walls (used during Throw)
        bool widen = false;                                          // `.sfktest`: the tank / a lone GM may be picked
        char const* logBoss = "razorclaw";                           // "sfk <logBoss> <logMechanic> ..."
        char const* logMechanic = "meat-hook";
    };

    struct ThrowResult
    {
        std::vector<ObjectGuid> targets;
        std::vector<BossMechanics::MechanicHandle> lines;

        explicit operator bool() const { return !lines.empty(); }
    };

    // Throws one hook (one or more lines, all under one cast bar). `owner` is the registry encounter that owns the
    // lines (nullptr: the thrower). An empty result: nobody qualified (skipped) or the registry refused the lines.
    // Call it while the thrower is not casting (the cast bar would fail).
    ThrowResult Throw(Creature* thrower, ThrowSpec const& spec, Unit* owner = nullptr);

    // Drops the once-per-throw memory of the lines' owner (the `owner` given to Throw, else the thrower): its reset or
    // death. Optional: a stale entry expires with its 1 s window anyway; this only frees it.
    void Forget(Unit const* owner);

    // Registers spell_sfk_meat_hook_once (bound to 205931 by apps/dbc-tools razorclaw.py). Called once, from
    // AddSC_boss_razorclaw_rework.
    void AddSC_meat_hook();
}

#endif
