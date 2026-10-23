/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * Shaman rework - ScriptMgr handlers (shaman-rework SH0a; docs/reworks/shaman-shared-rework.md). One class per hook
 * kind: later shaman stages extend ShamanPlayerScript and ShamanUnitScript. Every per-player hook returns early
 * unless the player is a shaman; the bodies live in ShamanMechanics.
 */

#include "AllCreatureScript.h"
#include "Creature.h"
#include "Item.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ShamanMechanics.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"
#include "UnitScript.h"

// The new Stoneskin buff (202206). 8072 (stock Stoneskin Totem buff, `stoneskin_8072`) is still declared in the DSL
// and, as the lower id, owns the short header name SPELL_STONESKIN: use the _202206 name, fail the build on a mixup.
static_assert(ShamanData::SPELL_STONESKIN_202206 == 202206,
    "ShamanData::SPELL_STONESKIN_202206 must be the SH0a Stoneskin buff");

namespace
{
    bool IsShaman(Player const* player)
    {
        return player && player->getClass() == CLASS_SHAMAN;
    }

    // Aura-based gates (SH0a review L2/m4): a hook acts on what the player owns, not on the class.
    bool HasAttunementOrRockbiter(Player const* player)
    {
        return player->HasAura(ShamanData::SPELL_EARTH_ATTUNEMENT) ||
            player->HasAura(ShamanData::SPELL_WATER_ATTUNEMENT) ||
            player->HasAura(ShamanData::SPELL_FIRE_ATTUNEMENT) ||
            player->HasAura(ShamanData::SPELL_AIR_ATTUNEMENT) ||
            player->HasAura(ShamanData::SPELL_ROCKBITER_WEAPON);
    }

    // S1: spells whose learn/unlearn can change the Thunderstorm stun rank or the Elemental auras (Thunderstorm, Call
    // of Thunder, Power of the Elements, Elemental Warding, Conduit of the Elements). Thunderstorm rank 2 itself is
    // left out: its own learn/remove comes from the sync.
    bool IsElementalSyncSpell(uint32 spellId)
    {
        switch (spellId)
        {
            case ShamanData::SPELL_THUNDERSTORM:
            case ShamanData::SPELL_CALL_OF_THUNDER:
            case ShamanData::SPELL_CALL_OF_THUNDER_RANK2:
            case ShamanData::SPELL_CALL_OF_THUNDER_RANK3:
            case ShamanData::SPELL_POWER_OF_THE_ELEMENTS:
            case ShamanData::SPELL_CONDUIT_OF_THE_ELEMENTS:
            case ShamanData::SPELL_ELEMENTAL_WARDING:
            case ShamanData::SPELL_ELEMENTAL_WARDING_28997:
            case ShamanData::SPELL_ELEMENTAL_WARDING_28998:
                return true;
            default:
                return false;
        }
    }

    // S2: spells whose learn/unlearn changes the Totemic Resonance aura (the talent's one rank).
    bool IsRestorationSyncSpell(uint32 spellId)
    {
        return spellId == ShamanData::SPELL_TOTEMIC_RESONANCE;
    }

    // S3: spells whose learn/unlearn changes the Enhancement state: Elemental Charge (charges), Ascendance (singles,
    // both Ascendances, the Mastery amounts), Spirit Guard and Improved Lightning Shield (the Rockbiter children) and
    // Unleashed Rage (the clause amount), Enhanced Elements (Mastery, so the live Ascendance and Stoneskin amounts).
    bool IsEnhancementSyncSpell(uint32 spellId)
    {
        switch (spellId)
        {
            case ShamanData::SPELL_ELEMENTAL_CHARGE:
            case ShamanData::SPELL_ASCENDANCE:
            case ShamanData::SPELL_SPIRIT_GUARD_RANK1:
            case ShamanData::SPELL_SPIRIT_GUARD_RANK2:
            case ShamanData::SPELL_SPIRIT_GUARD_RANK3:
            case ShamanData::SPELL_IMPROVED_SHIELDS:
            case ShamanData::SPELL_IMPROVED_SHIELDS_16290:
            case ShamanData::SPELL_IMPROVED_SHIELDS_51881:
            case ShamanData::SPELL_UNLEASHED_RAGE:
            case ShamanData::SPELL_UNLEASHED_RAGE_30808:
            case ShamanData::SPELL_UNLEASHED_RAGE_30809:
            case ShamanData::SPELL_ENHANCING_TOTEMS:            // Enhanced Elements ranks (stock ids reused)
            case ShamanData::SPELL_ENHANCING_TOTEMS_16295:
            case ShamanData::SPELL_ENHANCING_TOTEMS_52456:
                return true;
            default:
                return false;
        }
    }

    bool IsTalentSyncSpell(uint32 spellId)
    {
        return IsElementalSyncSpell(spellId) || IsRestorationSyncSpell(spellId) || IsEnhancementSyncSpell(spellId);
    }

    // The Thunderstorm stun rank and the Elemental auras follow the talents (no class gate: Classless reads the
    // player's own state). One tick later, so a talent reset or unlearn has finished removing every rank (the
    // reset hook fires before it, the forget hook between a spell's and its talent's removal). S2: the Totemic
    // Resonance aura too. S3: the Enhancement state (Rockbiter children, charges, Ascendances, Unleashed Rage).
    void QueueElementalTalentSync(Player* player)
    {
        if (!player)
            return;

        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid]()
        {
            Player* self = ObjectAccessor::FindPlayer(guid);
            if (!self || !self->IsInWorld())
                return;

            Shaman::SyncThunderstormRank(self);
            Shaman::OnElementalAdded(self, nullptr);
            Shaman::RecountTotemicResonance(self);
            Shaman::OnEnhTalentsChanged(self);
        }, 1ms);
    }

    // The four player-side elemental totems (300270-300273); the stock 15430/15439 stay with NPC casters.
    bool IsElementalTotemEntry(uint32 entry)
    {
        switch (entry)
        {
            case ShamanData::NPC_EARTH_ELEMENTAL_TOTEM:
            case ShamanData::NPC_FIRE_ELEMENTAL_TOTEM:
            case ShamanData::NPC_WATER_ELEMENTAL_TOTEM:
            case ShamanData::NPC_STORM_ELEMENTAL_TOTEM:
                return true;
            default:
                return false;
        }
    }
}

class ShamanPlayerScript : public PlayerScript
{
public:
    ShamanPlayerScript() : PlayerScript("ShamanPlayerScript",
        { PLAYERHOOK_ON_AFTER_SET_VISIBLE_ITEM_SLOT, PLAYERHOOK_ON_LEVEL_CHANGED, PLAYERHOOK_ON_LOGIN,
          PLAYERHOOK_ON_LEARN_SPELL, PLAYERHOOK_ON_PLAYER_ENTER_COMBAT, PLAYERHOOK_ON_PLAYER_LEAVE_COMBAT,
          PLAYERHOOK_ON_BEFORE_LOGOUT, PLAYERHOOK_ON_LOGOUT, PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED, PLAYERHOOK_ON_FORGOT_SPELL,
          PLAYERHOOK_ON_TALENTS_RESET, PLAYERHOOK_ON_PLAYER_LEARN_TALENTS, PLAYERHOOK_ON_MAP_CHANGED,
          PLAYERHOOK_ON_PLAYER_JUST_DIED }) { }

    // Imbue glow (P0 section 5): SetVisibleItemSlot (equip, swap, enchant, login inventory load) just rewrote the
    // slot's real enchant visuals; write the active imbue's glow back over the temp half. Auras load before the
    // inventory at login (_LoadAuras before _LoadInventory), so this hook is what draws the login glow. No imbue
    // up: keep the real values (a sharpening stone or poison stays visible).
    void OnPlayerAfterSetVisibleItemSlot(Player* player, uint8 slot, Item* item) override
    {
        if (slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND)
            return;

        if (!item || item->GetTemplate()->Class != ITEM_CLASS_WEAPON || !player)
            return;

        if (Shaman::GetActiveImbue(player))
            Shaman::WriteImbueGlow(player, slot);
    }

    // B11: attunement amounts come from the caster's level at aura creation; recalculate them on a level change.
    // mod-playerbots' level changes also strip auras, so the Reincarnation grant is re-checked here too.
    void OnPlayerLevelChanged(Player* player, uint8 /*oldLevel*/) override
    {
        if (!player)
            return;

        if (IsShaman(player))
            Shaman::EnsureReincarnationAura(player);

        if (!HasAttunementOrRockbiter(player))
            return;

        Shaman::RefreshAttunements(player);

        // Rockbiter's attack power scales with level and is computed at aura creation (SH0a review L1).
        if (Aura* rockbiter = player->GetAura(ShamanData::SPELL_ROCKBITER_WEAPON, player->GetGUID()))
            rockbiter->RecalculateAmountOfEffects();
    }

    // Reincarnation without the Ankh: Player.cpp's resurrect-choice gate needs 58059 (0-verify surprise 4). Spells
    // loaded from the DB never reach the learn hook, so login grants it for every shaman that knows 20608.
    // The glow: auras and inventory are both loaded by now and the visible-slot hook already drew it; re-applying
    // here is idempotent and covers any slot the load path wrote without that hook.
    void OnPlayerLogin(Player* player) override
    {
        if (!player)
            return;

        if (IsShaman(player))
            Shaman::EnsureReincarnationAura(player);

        if (Shaman::GetActiveImbue(player))
            Shaman::ApplyImbueGlow(player);

        // Stoneskin is saved with its stacks but the 2 min timer is not: re-arm it for a player who logs in out of
        // combat with Stoneskin up.
        if (player->HasAura(ShamanData::SPELL_STONESKIN_202206) && !player->IsInCombat())
            Shaman::OnCombatChange(player, false);

        // S1: the Thunderstorm stun rank follows the talents loaded from the DB.
        Shaman::SyncThunderstormRank(player);

        // S2: a Totemic Resonance aura or a Cloudburst store buff saved at logout has no totem behind it.
        Shaman::RecountTotemicResonance(player);
        Shaman::ReleaseCloudburst(player, true);
        player->RemoveAurasDueToSpell(ShamanData::SPELL_CLOUDBURST_STORE, player->GetGUID());

        // S3: the Rockbiter children (passive, never saved), the Unleashed Rage clause and the live Mastery amounts
        // follow the loaded talents and auras; the charges and Ascendances were dropped before the logout save (D9).
        Shaman::OnEnhTalentsChanged(player);

        // WP-R m9: an autosave before a crash can bring charges or singles back with no logout drop: out of combat they
        // get their 2 min timers now.
        if (!player->IsInCombat())
            Shaman::OnEnhCombatChange(player, false);
    }

    // S1: every map entry (login included, before OnPlayerLogin): the totems never follow the player (the old map
    // removes them after the player left it, so their remove hook finds no owner), and Empowerment, Gathering
    // Flames and the Warding health aura can be saved at logout: reconcile them with the (empty) slots.
    void OnPlayerMapChanged(Player* player) override
    {
        if (!player)
            return;

        Shaman::OnElementalRemoved(player, 0);

        // S2: the old map's totems are gone (their remove hook found no owner): Totemic Resonance follows the empty
        // slots, and a Cloudburst still recorded is discarded (no totem left to release around; the cooldown runs).
        // The infinite store buff can also come back from a logout save with nothing recorded: drop it.
        Shaman::RecountTotemicResonance(player);
        Shaman::ReleaseCloudburst(player, true);
        player->RemoveAurasDueToSpell(ShamanData::SPELL_CLOUDBURST_STORE, player->GetGUID());

        // WP-R m3: the plain Astral Shift buff is infinite and only removed when the control ends; a logout while
        // stunned, feared or silenced saves it. Drop it unless the player is still under such a control.
        bool const controlled = player->HasUnitState(UNIT_STATE_STUNNED | UNIT_STATE_CONFUSED | UNIT_STATE_FLEEING) ||
            player->HasAuraType(SPELL_AURA_MOD_STUN) || player->HasAuraType(SPELL_AURA_MOD_FEAR) ||
            player->HasAuraType(SPELL_AURA_MOD_SILENCE);
        if (!controlled)
            player->RemoveAurasDueToSpell(ShamanData::SPELL_ASTRAL_SHIFT_BUFF);

        // S3: the charges, singles, Ascendances and the bank travel with the player; the Elemental Spirits are
        // guardians the old map removes. Leaving a map can kill the player's pending events
        // (Unit::CleanupBeforeRemoveFromMap), so the live-Mastery loop restarts (with the rest of the reconcile) and
        // the out-of-combat timers re-arm. The Elemental Spirits timer buff goes with the wolves (S3a code review n1;
        // this hook also runs at login, where a saved copy has no wolves behind it).
        player->RemoveAurasDueToSpell(ShamanData::SPELL_ELEMENTAL_SPIRITS_TIMER, player->GetGUID());
        Shaman::OnEnhTalentsChanged(player);
        if (!player->IsInCombat())
            Shaman::OnEnhCombatChange(player, false);
    }

    // Trainer, .learn and skill-rewarded learns of Reincarnation (Player::learnSpell, after addSpell succeeded).
    // S1: Thunderstorm and the Elemental talents put in the spellbook or learned by a command.
    void OnPlayerLearnSpell(Player* player, uint32 spellID) override
    {
        if (!player)
            return;

        if (IsTalentSyncSpell(spellID))
            QueueElementalTalentSync(player);

        if (spellID != ShamanData::SPELL_REINCARNATION || !IsShaman(player))
            return;

        Shaman::EnsureReincarnationAura(player);
    }

    // S1: .unlearn and talent-rank removal (resetTalents, spec data) of the same spells.
    void OnPlayerForgotSpell(Player* player, uint32 spellID) override
    {
        if (IsTalentSyncSpell(spellID))
            QueueElementalTalentSync(player);
    }

    // S1: a talent point spent (passive ranks never reach the learn-spell hook).
    void OnPlayerLearnTalents(Player* player, uint32 /*talentId*/, uint32 /*talentRank*/, uint32 spellid) override
    {
        if (IsTalentSyncSpell(spellid))
            QueueElementalTalentSync(player);
    }

    // S1: fires before the reset removes anything; the queued sync runs after it.
    void OnPlayerTalentsReset(Player* player, bool /*noCost*/) override
    {
        QueueElementalTalentSync(player);
    }

    // Stoneskin's 2 min out-of-combat timer: cancelled on entry, armed on leave. OnPlayerLeaveCombat can fire twice
    // for one exit (CombatManager::UpdateOwnerCombatState and Unit::ClearInCombat); OnCombatChange re-arms.
    // S3: the same for the charges' and the singles' timers (both functions check what the player holds).
    void OnPlayerEnterCombat(Player* player, Unit* /*enemy*/) override
    {
        if (!player)
            return;

        if (player->HasAura(ShamanData::SPELL_STONESKIN_202206))
            Shaman::OnCombatChange(player, true);

        Shaman::OnEnhCombatChange(player, true);
    }

    void OnPlayerLeaveCombat(Player* player) override
    {
        if (!player)
            return;

        if (player->HasAura(ShamanData::SPELL_STONESKIN_202206))
            Shaman::OnCombatChange(player, false);

        Shaman::OnEnhCombatChange(player, false);
    }

    // S3 (D9): the engine already removed the charges, singles and Ascendances (not death-persistent); the bank and
    // the swap stash go too, and the Unleashed Rage clause follows. Imbues and the Rockbiter children persist.
    void OnPlayerJustDied(Player* player) override
    {
        if (player)
            Shaman::OnEnhPlayerDied(player);
    }

    // A spec-slot change can strip and re-grant auras; Reincarnation (a class gate) is re-checked (SH0a review m3).
    void OnPlayerAfterSpecSlotChanged(Player* player, uint8 /*newSlot*/) override
    {
        if (IsShaman(player))
            Shaman::EnsureReincarnationAura(player);

        // S1: the new spec's talents decide the Thunderstorm stun rank and the Elemental auras.
        QueueElementalTalentSync(player);
    }

    // S2 m1: before WorldSession::LogoutPlayer saves, so the Cloudburst cooldown reaches the character save.
    void OnPlayerBeforeLogout(Player* player) override
    {
        if (IsShaman(player))
            Shaman::OnPlayerBeforeLogout(player);
    }

    void OnPlayerLogout(Player* player) override
    {
        if (IsShaman(player))
            Shaman::ClearState(player);
    }
};

// ScriptMgr::DealDamage calls every UnitScript's DealDamage with no hook-enable check; an empty enable list would
// enable all UnitHook entries, so the list names only the hooks this class overrides (S2: OnHeal).
class ShamanUnitScript : public UnitScript
{
public:
    ShamanUnitScript() : UnitScript("ShamanUnitScript", true, { UNITHOOK_ON_HEAL }) { }

    // S2 Cloudburst (CORE-AUDIT-A A13): the totems' and the Water Elemental's heals are stored for their owner.
    // Unit::DealHeal calls this for every heal and tick with the effective (non-overheal) amount and no spell, so the
    // checks run cheapest first. Every shaman totem and Water Elemental heal is Nature (ruled 2026-10-18); absorbs and
    // Spirit Link's SetHealth never come here. The shaman's own heals are stored by the store buff's proc (B2), and the
    // release (cast by the player) is skipped by the healer check.
    void OnHeal(Unit* healer, Unit* /*receiver*/, uint32& gain) override
    {
        if (!gain || !healer || !healer->IsCreature())
            return;

        Creature* creature = healer->ToCreature();
        if (!creature->IsTotem() && creature->GetEntry() != ShamanData::NPC_WATER_ELEMENTAL_GUARDIAN)
            return;

        // S2 m2: only totems the shaman spells summon (a Freepick Lightwell is a Totem too and heals Holy).
        if (creature->IsTotem())
        {
            SpellInfo const* creator = sSpellMgr->GetSpellInfo(creature->GetUInt32Value(UNIT_CREATED_BY_SPELL));
            if (!creator || creator->SpellFamilyName != SPELLFAMILY_SHAMAN)
                return;
        }

        Player* owner = Shaman::GetOwningPlayer(healer);
        if (!owner || !owner->HasAura(ShamanData::SPELL_CLOUDBURST_STORE, owner->GetGUID()))
            return;

        Shaman::AddCloudburstStore(owner, gain);
    }

    // B15 Stoneskin erosion. Unit::DealDamage calls this first, with the amount that lands on health: armor, every
    // % reduction (Stoneskin included), block, resilience, resist and absorbs are already taken off (melee
    // CalculateMeleeDamage, spells CalculateSpellDamageTaken, DoT ticks and damage shields all run CalcAbsorbResist
    // and pass the post-absorb amount). Misses, dodges and parries never get here; a full absorb arrives as 0.
    // Runs for every hit in the world: cheapest checks first.
    uint32 DealDamage(Unit* /*attacker*/, Unit* victim, uint32 damage, DamageEffectType damagetype) override
    {
        if (!damage || !victim || !victim->IsPlayer())
            return damage;

        // SELF_DAMAGE: environmental and fall damage (Player::EnvironmentalDamage), self mana-burn style ticks.
        // NODAMAGE: SHARE_DAMAGE_PCT copies and other health-only bookkeeping.
        if (damagetype == SELF_DAMAGE || damagetype == NODAMAGE)
            return damage;

        Player* shaman = victim->ToPlayer();
        if (!shaman->HasAura(ShamanData::SPELL_STONESKIN_202206))
            return damage;

        Shaman::ErodeStoneskin(shaman, damage);
        return damage;
    }
};

// S1 (A15): the four player-side elemental totems entering and leaving the world. The add hook runs with the slot
// already set (TempSummon::InitStats, before AddToMap) and before the totem's passive summons the guardian; the remove
// hook runs for every way a totem goes (guardian death -> OnElementalDied, expiry, right-click/Recall, replacement,
// owner death or logout) with the slot already cleared or held by the replacement. The owner is resolved on the
// totem's map and may be missing (logout, teleport): then nothing happens and the next map entry reconciles (L4).
// S2 (A15): every player-owned totem (the elemental totems included) also reaches OnPlayerTotemAdded/Removed:
// Totemic Resonance, the Totemic Focus placement heal and Cloudburst. NPC-owned totems have no owning player.
class ShamanElementalTotemScript : public AllCreatureScript
{
public:
    ShamanElementalTotemScript() : AllCreatureScript("ShamanElementalTotemScript") { }

    void OnCreatureAddWorld(Creature* creature) override
    {
        if (!creature || !creature->IsTotem())
            return;

        Player* owner = Shaman::GetOwningPlayer(creature);
        if (!owner)
            return;

        if (IsElementalTotemEntry(creature->GetEntry()))
            Shaman::OnElementalAdded(owner, creature);

        Shaman::OnPlayerTotemAdded(owner, creature);
    }

    void OnCreatureRemoveWorld(Creature* creature) override
    {
        if (!creature || !creature->IsTotem())
            return;

        Player* owner = Shaman::GetOwningPlayer(creature);
        if (!owner)
            return;

        if (IsElementalTotemEntry(creature->GetEntry()))
            Shaman::OnElementalRemoved(owner, creature->GetEntry());

        Shaman::OnPlayerTotemRemoved(owner, creature);
    }
};

void AddSC_shaman_hooks()
{
    new ShamanPlayerScript();
    new ShamanUnitScript();
    new ShamanElementalTotemScript();
}
