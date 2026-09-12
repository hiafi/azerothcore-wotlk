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

#ifndef MODULE_DPSSIM_SIMACTOR_H
#define MODULE_DPSSIM_SIMACTOR_H

#include "Define.h"
#include <map>
#include <string>
#include <vector>

class Player;
class WorldSession;

// A real, socketless Player built entirely in-memory - the mechanism the Phase 0
// headless-Player-construction spike confirmed (see the plan doc): core AzerothCore, no
// mod-playerbots dependency, touches zero SQL writes (the read-only in-memory PlayerInfo/
// PlayerLevelInfo/PlayerClassLevelInfo tables ObjectMgr already caches at boot are the only DB
// data consulted, via the same GiveLevel()/Player::Create() path a real login uses). Once
// created, it ticks through the normal Map::Update()/Unit::Update() path exactly like any other
// player on the map - no special pump loop needed.
class SimActor
{
public:
    struct Config
    {
        std::string Name = "SimActor";
        uint8 Race = 0;   // set by DpsSim.cpp/SimDaemon to a valid race/class combo (RACE_TROLL)
        uint8 Class = 0;  // (CLASS_MAGE) - kept unset here so a caller can't forget to pick one
        uint8 Gender = 0; // GENDER_MALE
        uint8 Level = 80;
        // Flat spell power added on top of the level/race baseline (Intellect/Spirit already
        // contribute automatically - see Unit::SpellBaseDamageBonusDone's "Custom: 0.5 point of
        // spellpower per point of Intellect and Spirit"). 0 models an unbuffed, ungeared actor.
        int32 SpellPower = 0;

        // Real item ids to equip, in listed order, via Player::StoreNewItemInBestSlots() - see
        // SimProfile.h's Profile::GearItemIds for the full doc comment (this struct just carries
        // whatever RunConfig::GearItemIds already holds). Applied before CombatRatings below.
        std::vector<uint32> GearItemIds;

        // Synthetic combat-rating top-ups, keyed by CombatRating (Unit.h) - see SimProfile.h's
        // Profile::CombatRatings for the full doc comment. Applied via Player::ApplyRatingMod()
        // after GearItemIds, so these layer on top of whatever gear already contributed rather
        // than replacing it.
        std::map<uint8, int32> CombatRatings;

        // Synthetic core-stat top-ups (Strength/Agility/Stamina/Intellect/Spirit), keyed by Stats
        // (SharedDefines.h) - see SimProfile.h's Profile::Stats for the full doc comment. Applied
        // via Player::HandleStatFlatModifier()/UpdateStatBuffMod().
        std::map<uint8, float> Stats;

        // Flat attack power on top of gear/level/race - see SimProfile.h's Profile::AttackPower
        // for the full doc comment. Applied via Player::HandleStatFlatModifier() against both the
        // melee and ranged attack-power UnitMods.
        int32 AttackPower = 0;
    };

    ~SimActor();

    // Builds the socketless WorldSession + Player, levels it to Config.Level, applies the
    // synthetic stat block, and adds it live to its starting map. Returns false (logging why) on
    // any failure - the caller should abort the sim run rather than proceed with a half-built
    // actor. Safe to call at most once per instance.
    bool Create(Config const& config);

    [[nodiscard]] Player* GetPlayer() const { return _player; }

private:
    WorldSession* _session = nullptr;
    Player* _player = nullptr;
};

#endif
