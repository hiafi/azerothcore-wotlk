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
    // raid member would get" (ResolveEffectMask()); "id:01" picks effect indexes 0 and 1 explicitly.
    struct AuraSpec
    {
        uint32 SpellId = 0;
        uint8 EffectMask = 0;
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
    };

    // The defaults of DpsSim.RaidBuffs / RaidDebuffs / RaidPullBuffs (dpssim.conf.dist documents each id)
    extern char const* const DEFAULT_RAID_BUFFS;
    extern char const* const DEFAULT_RAID_DEBUFFS;
    extern char const* const DEFAULT_RAID_PULL_BUFFS;

    char const* SetName(Set set);
    // "self_only" or "full_raid" (case-insensitive)
    bool ParseSet(std::string const& text, Set& out, std::string& error);
    // "24932, 25898:0, 202210:01": comma-separated spell ids, each optionally followed by ':' and the effect indexes
    // (0-2) to apply. Blank entries are skipped. Pure parsing: the ids are checked by Validate().
    bool ParseAuraList(std::string const& text, std::vector<AuraSpec>& out, std::string& error);
    // Every spell exists and its chosen effects hold an aura; a 0 mask is resolved to ResolveEffectMask(). Needs the
    // spell store, so call it after the world loaded.
    bool Validate(std::vector<AuraSpec>& specs, std::string& error);
    // The effects a raid member gets from the spell: every aura effect except a plain APPLY_AURA on the caster itself
    // (the caster's own perk, e.g. Abomination's Might's +1% Strength on the death knight)
    uint8 ResolveEffectMask(uint32 spellId);
    // "24932 Leader of the Pack [0,1,2]" per entry, for the run log
    std::string Describe(std::vector<AuraSpec> const& specs);

    // Puts every missing buff on the actor and its pet and every missing debuff on the dummies, pinned. Returns how
    // many auras it added (0 once everything is up). `initial` logs what did not land (immunity, a stronger aura of
    // the same group); the per-second refresh stays quiet.
    uint32 ApplyPinned(Config const& config, Player* actor, std::vector<Creature*> const& dummies, bool initial);
    // Bloodlust and Sated: once at the pull, on the actor and its pet, with their own duration
    void ApplyPullBuffs(Config const& config, Player* actor);
}

#endif
