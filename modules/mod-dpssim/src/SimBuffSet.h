/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef MODULE_DPSSIM_SIMBUFFSET_H
#define MODULE_DPSSIM_SIMBUFFSET_H

#include "Define.h"
#include <map>
#include <string>
#include <vector>

class Creature;
class Player;

// Named buff sets (design doc docs/dps-sim-module.md 5.2, ruling 12; plan
// .agents/plans/hunter-pet-families/hunter-pet-families.PLAN.md 6). `self_only` is the actor's own buffs and nothing
// else (every run before this existed). `full_raid` adds a raid's buffs on the actor and its pet, a raid's debuffs on
// every dummy and Bloodlust at the pull, all applied by the sim (Unit::AddAura, the actor as the caster), not cast by
// anyone. Each member sits in the same spell_group as the hunter pet family effect of its category, so a family's own
// cast is suppressed by the group rule and adds nothing to its number (hunter-pet-families BRAINSTORM ruling 7).
namespace SimBuffSet
{
    enum class Set : uint8
    {
        SelfOnly,
        FullRaid
    };

    // One list entry: a spell id and the effects of it to apply. EffectMask 0 in a parsed entry means "the effects a
    // raid member would get" (ResolveEffectMask()); "id:01" picks effect indexes 0 and 1 explicitly. "id:0@3" also
    // sets the amount of every applied effect to 3 (for a spell whose rank chain is not in spell_ranks, so only its
    // first rank is in the spell_group, but whose first rank has a smaller amount than the raid's).
    struct AuraSpec
    {
        uint32 SpellId = 0;
        uint8 EffectMask = 0;
        bool HasAmount = false;
        int32 Amount = 0;
    };

    // What a run has already logged (the log lines are once per run, not once per iteration). Mutable because the
    // config is handed around const.
    struct RunState
    {
        bool InitialLogged = false;
        bool CoverageLogged = false;
    };

    struct Config
    {
        Set BuffSet = Set::SelfOnly;
        // On the actor and its pet after the pre-pull buff phase, pinned (no expiry) and put back every second
        std::vector<AuraSpec> Buffs;
        // On every dummy at the pull, pinned and put back every second
        std::vector<AuraSpec> Debuffs;
        // On the actor and its pet at the pull, with their own duration, never put back (Bloodlust and Sated)
        std::vector<AuraSpec> PullBuffs;
        mutable RunState State;
    };

    // Initial: the pull. Refresh: the once-a-second pass that puts back what went missing.
    enum class Phase : uint8
    {
        Initial,
        Refresh
    };

    // What one iteration's refresh passes did, by "<spell id> <name> on the <who>": what they put back, and what they
    // failed to put back (with the member of its spell group that is in the way). LogRefresh() prints it.
    struct RefreshLog
    {
        std::map<std::string, uint32> PutBack;
        std::map<std::string, uint32> Failed;
    };

    // The defaults of DpsSim.RaidBuffs / RaidDebuffs / RaidPullBuffs (dpssim.conf.dist documents each id)
    extern char const* const DEFAULT_RAID_BUFFS;
    extern char const* const DEFAULT_RAID_DEBUFFS;
    extern char const* const DEFAULT_RAID_PULL_BUFFS;

    char const* SetName(Set set);
    // "self_only" or "full_raid" (case-insensitive)
    bool ParseSet(std::string const& text, Set& out, std::string& error);
    // "24932, 25898:0, 202210:01, 21183:0@3": comma-separated spell ids, each optionally followed by ':' and the effect
    // indexes (0-2) to apply, and then by '@' and the amount to give them. Blank entries are skipped. Pure parsing: the
    // ids are checked by Validate().
    bool ParseAuraList(std::string const& text, std::vector<AuraSpec>& out, std::string& error);
    // Every spell exists and its chosen effects hold an aura; a 0 mask is resolved to ResolveEffectMask(). Needs the
    // spell store, so call it after the world loaded.
    bool Validate(std::vector<AuraSpec>& specs, std::string& error);
    // The effects a raid member gets from the spell: every aura effect except a plain APPLY_AURA on the caster itself
    // (the caster's own perk, e.g. Abomination's Might's +1% Strength on the death knight)
    uint8 ResolveEffectMask(uint32 spellId);
    // "24932 Leader of the Pack [0,1,2]" per entry, for the run log
    std::string Describe(std::vector<AuraSpec> const& specs);

    // Puts every missing buff on the actor and its pet and every missing debuff on every dummy, pinned. Returns how
    // many auras it added (0 once everything is up). Phase::Initial logs the amounts that landed (the first dummy's)
    // and every failure (immunity, or the group member that is in the way); Phase::Refresh counts into `refresh`.
    uint32 ApplyPinned(Config const& config, Player* actor, std::vector<Creature*> const& dummies, Phase phase,
        RefreshLog* refresh = nullptr);
    // Logs once which buffs the actor and its pet, and which debuffs each dummy, do not carry (HasAura; passive auras
    // included), and for each of the pet's whether the actor's own aura reached it (an area aura propagated) or it
    // carries a copy added directly. Call it before the first refresh pass, a sim second after the pull, when the
    // area auras have updated, so the direct copies of the refresh cannot hide a gap.
    void LogCoverage(Config const& config, Player* actor, std::vector<Creature*> const& dummies);
    // Logs what an iteration's refresh passes put back and failed to put back (nothing when nothing went missing)
    void LogRefresh(RefreshLog const& refresh);
    // Bloodlust and Sated: once at the pull, on the actor and its pet, with their own duration
    void ApplyPullBuffs(Config const& config, Player* actor, Phase phase);
}

#endif
