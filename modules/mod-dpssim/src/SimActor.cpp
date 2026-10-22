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

#include "SimActor.h"
#include "DatabaseEnv.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "World.h"
#include "WorldSession.h"
#include <atomic>

namespace
{
    std::atomic<uint32> s_nextSimGuidOffset{0};
    std::atomic<uint32> s_saveAttempts{0};
}

uint32 SimActor::GetSaveAttempts()
{
    return s_saveAttempts.load();
}

void SimActor::NoteSaveAttempt(ObjectGuid guid)
{
    ++s_saveAttempts;
    LOG_ERROR("server.dpssim", "mod-dpssim: Player::SaveToDB() entered for sim actor {} - a save path the sim "
        "was meant to rule out is live (rows land in the throwaway sim characters DB); find the caller.",
        guid.ToString());
}

SimActor::~SimActor()
{
    // WorldSession::LogoutPlayer() is the one correct teardown path for a live Player - it runs
    // the full script-hook chain (OnPlayerBeforeLogout et al - real modules like mod-dungeon-clear
    // depend on this firing before the Player disappears), CleanupsBeforeDelete(), and
    // Map::RemovePlayerFromMap(), and it deletes _player itself (see its "pointer already
    // deleted" comment before SetPlayer(nullptr)).
    //
    // Do NOT also delete _player here: an earlier version of this destructor did exactly that,
    // then called `delete _session`, whose own destructor unconditionally calls LogoutPlayer(true)
    // again on the (now-dangling) _player pointer - script hooks like DcSpectator::Stop() dereference
    // it and it crashes. Calling LogoutPlayer(false) ourselves first (save=false, since this actor
    // was never in the characters table - see Create()'s "zero SQL" construction) leaves _session's
    // own _player null, so ~WorldSession()'s internal LogoutPlayer(true) call becomes a no-op guard
    // hit rather than a second teardown.
    //
    // redirecting=true (LogoutPlayer's second param) skips its `if (!redirecting)` block -
    // SendFriendStatus/RemovePlayerSocial (via sSocialMgr) and the OnPlayerLogout hook. Required,
    // not just an optimization: SendFriendStatus dereferences player->GetSocial(), which is only
    // ever populated by a real DB login's _LoadSocialList() (Player::m_social defaults to
    // nullptr - see Player.cpp) - this synthetic actor never runs that, so without redirecting=true
    // SocialMgr::GetFriendInfo() null-derefs and crashes. OnPlayerBeforeLogout (the hook
    // DcSpectator::Stop needs) fires unconditionally earlier in LogoutPlayer, before this guard -
    // skipping the redirecting-guarded block does not skip that.
    if (_session && _session->GetPlayer())
        _session->LogoutPlayer(false, true);

    delete _session;
}

bool SimActor::Create(Config const& config)
{
    // Nothing may persist this actor. Player::Update() autosaves every PlayerSaveInterval ms of Update time (the
    // sim feeds it sim time, so a 10-iteration batch crosses the default 15 minutes) and the actor has no
    // `characters` row, so the save wrote its child tables (talents, spells, actions, ...) as orphans under a guid
    // the live server later handed to a real character. Player's constructor snapshots both values, so set them
    // before `new Player`. 0 disables the autosave timer (`if (m_nextSave)`) and the additional-save timer.
    sWorld->setIntConfig(CONFIG_INTERVAL_SAVE, 0);
    sWorld->setIntConfig(CONFIG_ADDITIONAL_SAVES, 0);

    _guidLow = SIM_GUID_BASE + s_nextSimGuidOffset++;

    // accountId 0, no name, no socket: a null socket makes the session headless, which
    // WorldSession's constructor special-cases (no LoginDatabase touch, m_Address = "headless") -
    // see the Phase 0 spike write-up in the plan doc.
    _session = new WorldSession(0, "", 0x0, nullptr, SEC_PLAYER, EXPANSION_WRATH_OF_THE_LICH_KING,
        time_t(0), LOCALE_enUS, 0, false, false, 0);

    CharacterCreateInfo createInfo(config.Name, config.Race, config.Class, config.Gender,
        /*skin*/0, /*face*/0, /*hairStyle*/0, /*hairColor*/0, /*facialHair*/0);

    _player = new Player(_session);
    _player->GetMotionMaster()->Initialize();
    if (!_player->Create(_guidLow, &createInfo))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimActor::Create() - Player::Create() failed (race {}, class {}) - check the race/class combo is valid.",
            config.Race, config.Class);
        delete _player;
        _player = nullptr;
        delete _session;
        _session = nullptr;
        return false;
    }

    _session->SetPlayer(_player);
    _player->setCinematic(2);
    _player->SetAtLoginFlag(AT_LOGIN_NONE);

    // GiveLevel() takes the character from its level-1 creation baseline to Config.Level using
    // the same PlayerLevelInfo/PlayerClassLevelInfo tables a real level-up uses, ending with a
    // full UpdateAllStats()/SetFullHealth()/full-mana call already built in.
    _player->GiveLevel(config.Level);
    _player->InitTalentForLevel();

    // Gear first, then synthetic stat top-ups, then bake everything in with one final
    // UpdateAllStats() - see SimProfile.h's Profile::GearItemIds/SpellPower/CombatRatings for why
    // this ordering (gear before synthetic top-ups, so a profile can layer a top-up on top of a
    // real gear baseline rather than one silently overwriting the other's contribution).
    //
    // A profile that lists gear replaces the whole starter outfit Player::Create() equipped (a paladin's
    // starter two-hander 2361 once blocked the profile's axe). Clearing it first lets each profile item take
    // the first free slot in order - main hand before off-hand, ring 1 before ring 2 - with no starter item
    // in the way. The starter items are new and not yet in world, so destroying them sends nothing.
    if (!config.GearItemIds.empty())
        for (uint8 slot = EQUIPMENT_SLOT_START; slot < EQUIPMENT_SLOT_END; ++slot)
            if (_player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot))
                _player->DestroyItem(INVENTORY_SLOT_BAG_0, slot, true);

    for (uint32 const itemId : config.GearItemIds)
    {
        ItemTemplate const* proto = sObjectMgr->GetItemTemplate(itemId);
        if (!proto)
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimActor::Create() - gear item {} does not exist.", itemId);
            continue;
        }

        // A profile names the gear it wants worn, so grant the item's skill first (2026-10-05, RetPaladinSim):
        // a fresh paladin has no Two-Handed Axes, and gets Plate only from the level-40 trainer, which runs
        // later (SimBot::Create()). Weapons go to the level cap, since a lower skill also raises the target's
        // block/dodge/parry chance; armor proficiencies are fixed-value skills, granted the core's own way.
        if (uint32 const skill = proto->GetSkill())
        {
            if (proto->Class == ITEM_CLASS_WEAPON)
            {
                uint16 const maxValue = _player->GetMaxSkillValueForLevel();
                uint16 const step = _player->GetSkillValue(skill) ? _player->GetSkillStep(skill) : 1;
                _player->SetSkill(skill, step, maxValue, maxValue);
            }
            else if (!_player->HasSkill(skill))
                _player->LearnDefaultSkill(skill, 0);
        }

        // Equip explicitly rather than StoreNewItemInBestSlots(): that call drops an unequippable item into
        // the bags and still returns true, which once left a Ret profile swinging unarmed with no error.
        // Dual Wield and Titan's Grip are learned later (SimBot::Create()), so a second weapon only fits
        // here for a class that starts with Dual Wield (rogue, death knight); otherwise it is logged below.
        uint16 dest = 0;
        InventoryResult const result = _player->CanEquipNewItem(NULL_SLOT, dest, itemId, false);
        if (result != EQUIP_ERR_OK)
        {
            LOG_ERROR("server.dpssim",
                "mod-dpssim: SimActor::Create() - could not equip item {} (InventoryResult {}; or its slot is "
                "already filled by an earlier item in GearItemIds).", itemId, uint32(result));
            continue;
        }

        _player->EquipNewItem(dest, itemId, true);
        // Same follow-up StoreNewItemInBestSlots() did: a two-hander displaces an off-hand listed earlier
        _player->AutoUnequipOffhandIfNeed();
    }

    for (auto const& [combatRating, value] : config.CombatRatings)
    {
        if (value != 0)
            _player->ApplyRatingMod(CombatRating(combatRating), value, true);
    }

    for (auto const& [stat, value] : config.Stats)
    {
        if (value != 0.0f)
        {
            // Same two-call sequence a real item's ITEM_MOD_STRENGTH/AGILITY/STAMINA/INTELLECT/
            // SPIRIT stat uses (Player::_ApplyItemBonuses()) - HandleStatFlatModifier() bumps the
            // base value the UpdateAllStats() call below rebuilds from; UpdateStatBuffMod()
            // refreshes the buff-mod field HandleStatFlatModifier() doesn't touch itself.
            // UNIT_MOD_STAT_STRENGTH..SPIRIT are contiguous in Stats enum order (Unit.h's own
            // comment on the enum says as much), so offsetting from UNIT_MOD_STAT_STRENGTH by the
            // Stats index reaches the right UnitMods without a second lookup table.
            _player->HandleStatFlatModifier(UnitMods(UNIT_MOD_STAT_STRENGTH + stat), BASE_VALUE, value, true);
            _player->UpdateStatBuffMod(Stats(stat));
        }
    }

    if (config.AttackPower != 0)
    {
        // A real item's single ITEM_MOD_ATTACK_POWER stat bumps both at once
        // (Player::_ApplyItemBonuses()'s own case) - mirrored here rather than picking one.
        _player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER, TOTAL_VALUE, float(config.AttackPower), true);
        _player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER_RANGED, TOTAL_VALUE, float(config.AttackPower), true);
    }

    if (config.SpellPower != 0)
    {
        // ApplySpellPowerBonus() only bumps the internal m_baseSpellPower accumulator - the
        // UpdateAllStats() call below is what actually bakes it into the damage formula
        // (Unit::SpellBaseDamageBonusDone() reads m_baseSpellPower fresh each time it's called
        // from UpdateSpellDamageAndHealingBonus()).
        _player->ApplySpellPowerBonus(config.SpellPower, true);
    }

    // A real login turns stat recalculation on once the character is loaded (PlayerStorage.cpp, LoadFromDB). The sim
    // builds its character with Player::Create() and never goes through that, so without this every later stat
    // change (%-stat and attack power talents, buffs, forms, stances, stat procs) would be silently dropped:
    // Unit::UpdateUnitMod() only recalculates while CanModifyStats() is true.
    _player->SetCanModifyStats(true);
    _player->UpdateAllStats();
    _player->SetFullHealth();
    _player->SetPower(POWER_MANA, _player->GetMaxPower(POWER_MANA));

    if (config.HasPosition)
        _player->Relocate(config.PositionX, config.PositionY, config.PositionZ, config.PositionO);

    ObjectAccessor::AddObject(_player);
    if (!_player->GetMap()->AddPlayerToMap(_player))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimActor::Create() - AddPlayerToMap() failed.");
        return false;
    }

    // The resulting melee attack power and main-hand item, so a profile's AttackPower top-up can be
    // calibrated against an in-game character sheet. Logged before SimBot::Create() spends talents, so a
    // talent that raises Strength or attack power isn't in this figure yet.
    Item const* mainHand = _player->GetItemByPos(INVENTORY_SLOT_BAG_0, EQUIPMENT_SLOT_MAINHAND);
    LOG_INFO("server.dpssim",
        "mod-dpssim: SimActor created - '{}' (race {}, class {}, level {}), map {}, spellPower {}, attackPower {}, "
        "{} gear item(s), {} synthetic rating(s), {} synthetic stat(s); total melee attack power {}, main hand {}.",
        config.Name, config.Race, config.Class, config.Level, _player->GetMapId(),
        config.SpellPower, config.AttackPower, config.GearItemIds.size(),
        config.CombatRatings.size(), config.Stats.size(),
        _player->GetTotalAttackPowerValue(BASE_ATTACK), mainHand ? mainHand->GetEntry() : 0);

    // The actor's character sheet, so a profile's flat Stats / SpellPower / ratings can be calibrated against real
    // gear: run the same profile with its GearItemIds and without them and subtract. Spell power is the flat part
    // (gear and SpellPower); the Intellect/2 + Spirit/2 part comes on top of it, see
    // Unit::SpellBaseHealingBonusDone().
    auto const rating = [this](CombatRating cr) { return _player->GetUInt32Value(PLAYER_FIELD_COMBAT_RATING_1 + cr); };
    LOG_INFO("server.dpssim",
        "mod-dpssim: SimActor sheet - '{}': Strength {}, Agility {}, Stamina {}, Intellect {}, Spirit {}, flat spell "
        "power {}, healing power {}, armor {}; ratings: crit {}, haste {}, mastery {}, versatility {}, cooldown haste "
        "{}, proc chance {}; max health {}, max mana {}.",
        config.Name, uint32(_player->GetStat(STAT_STRENGTH)), uint32(_player->GetStat(STAT_AGILITY)),
        uint32(_player->GetStat(STAT_STAMINA)), uint32(_player->GetStat(STAT_INTELLECT)),
        uint32(_player->GetStat(STAT_SPIRIT)), _player->GetBaseSpellPowerBonus(),
        _player->SpellBaseHealingBonusDone(SPELL_SCHOOL_MASK_ALL), _player->GetArmor(), rating(CR_CRIT_SPELL),
        rating(CR_HASTE_SPELL), rating(CR_MASTERY), rating(CR_VERSATILITY), rating(CR_COOLDOWN_HASTE),
        rating(CR_PROC_CHANCE), _player->GetMaxHealth(), _player->GetMaxPower(POWER_MANA));
    return true;
}
