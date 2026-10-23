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

#ifndef __SHAMANMECHANICS_H
#define __SHAMANMECHANICS_H

#include "Define.h"
#include "Generated/ShamanData.h"
#include "SharedDefines.h"
#include <cstdint>
#include <initializer_list>
#include <span>

class Creature;
class Player;
class SpellInfo;
class Unit;

/*
 * Shaman-specific "doesn't fit a SpellScript/AuraScript" hooks (shaman-rework SH0). Append-only: SH0a holds
 * only the SH0a block; later stages add their declarations together with their bodies and never retype an
 * existing signature. Spell ids come from ShamanData:: (DSL-declared); this header is the only place that
 * includes Generated/ShamanData.h.
 */
namespace Shaman
{
    // ---- SH0a ----
    // The player that owns `unit`: itself, or the owner/charmer of a pet, guardian or totem. nullptr otherwise.
    Player* GetOwningPlayer(Unit* unit);
    Player const* GetOwningPlayer(Unit const* unit);

    // CORE-AUDIT-A A12: every owner-side proc's CheckProc guard. True when `actor` is the shaman itself (not a
    // totem, guardian or pet acting for it).
    bool IsOwnAction(Unit const* shaman, Unit const* actor);

    // Proc Chance for scripted rolls: chance * (1 + owner Proc Chance / 100). Pets/guardians resolve to their owner.
    float GetProcChanceMultiplier(Unit const* unit);
    bool  RollProcChance(Unit const* unit, float baseChancePct);

    // Spell id of the imbue aura (Rockbiter, Flametongue, Frostbrand, Windfury, Earthliving) currently on `unit`;
    // 0 if none.
    uint32 GetActiveImbue(Unit const* unit);

    // True while the player knows a Maelstrom Weapon talent rank (S3: GetTalentRank over the three ranks).
    bool HasMaelstromWeaponTalent(Player const* player);

    // Imbue weapon glow (P0 section 5): writes the temp half of PLAYER_VISIBLE_ITEM_n_ENCHANTMENT.
    uint16 GetImbueGlowEnchant(Player const* player);         // visible enchant id of the active imbue, 0 if none
    void   ApplyImbueGlow(Player* player);                    // both weapon slots, from the active imbue
    void   RestoreImbueGlow(Player* player);                  // re-runs SetVisibleItemSlot for both weapon slots
    void   WriteImbueGlow(Player* player, uint8 slot);        // single slot, called from the visible-slot hook

    // Stoneskin (only while Rockbiter is up; cap Shaman STONESKIN_MAX).
    void AddStoneskin(Player* shaman, uint32 stacks);
    // B15: a landed hit of `landedDamage` on `victim` (after armor and every reduction, Stoneskin's included)
    // removes the same percent of current stacks as the hit is of max health before Stoneskin's reduction.
    // S3: nothing erodes during Earthen Ascendance; Toughness rank 3 halves the loss (TOUGHNESS_ERODE_PCT) while the
    // victim is below TOUGHNESS_THRESHOLD_PCT health before the hit.
    void ErodeStoneskin(Player* victim, uint32 landedDamage);
    // Out-of-combat 2 min timer: started on leave, cancelled on re-enter.
    void OnCombatChange(Player* player, bool inCombat);

    // Attunement amounts are per caster level: RecalculateAmountOfEffects on the attunement and its child (B11).
    void RefreshAttunements(Player* player);

    // Grants/keeps the passive 58059 (Reincarnation without the Ankh reagent): HunterNoAmmoGrant shape.
    void EnsureReincarnationAura(Player* player);

    // Logout cleanup; each later section adds its own Clear* call here.
    void ClearState(Player* player);

    // ---- SH0b ----
    // Elementals (Earth 2062, Fire 2894, Water, Storm): a totem in the element's slot whose passive summons the
    // guardian (CORE-AUDIT-A A5). The block keeps no per-player state, so ClearState needs no SH0b call.

    // The shared lockout before Cooldown Haste: ELEMENTAL_LOCKOUT_MS, or CONDUIT_LOCKOUT_MS while the player knows
    // Elemental's Conduit of the Elements (S1).
    uint32 GetElementalLockoutBaseMs(Player const* player);

    // A14: after a non-triggered cast of an elemental summon (the caller skips triggered casts), locks the other
    // three for base / (1 + max(0, Cooldown Haste) / 100). Deferred 1 ms (after SMSG_SPELL_GO and the cast spell's
    // own haste correction); never shortens a longer cooldown; clear-then-set resend so the buttons grey.
    void ApplyElementalLockout(Player* player, uint32 castSpellId);

    // True for the four elemental summon spells.
    bool IsElementalSummonSpell(uint32 spellId);

    // Guardian JustDied: unsummons the owner's totem in this elemental's slot when that totem is this elemental's
    // totem entry, so the slot empties (the cooldown keeps running). Any other occupant, or an NPC owner's stock
    // totem, is left alone.
    void OnElementalDied(Creature* guardian);

    // H1: adds the owner-stat aura (202279) to `guardian` if missing, then sets its MOD_DAMAGE_DONE amount to the
    // owner's spell power in the guardian's own bolt school (Frost for Water, Nature for Storm; no other school's
    // bonus is added) and its MOD_HEALING_DONE amount to the owner's healing power (live, nothing else). Called
    // at IsSummonedBy and from the aura script's periodic refresh; never from the aura's own amount calculation.
    void RefreshElementalAuras(Player* owner, Unit* guardian);

    // ---- S1 ----
    // Elemental spec (docs/reworks/shaman-elemental-rework.md). No per-player state: every function reads the
    // shaman's own talents, auras and totem slots, so a non-shaman with the talents gets do-nothing (Q21).

    // GetActiveElementals bits, one per elemental whose player-side totem (300270-300273) holds its slot.
    enum ElementalMask : uint8
    {
        ELEMENTAL_MASK_EARTH = 0x1,
        ELEMENTAL_MASK_FIRE  = 0x2,
        ELEMENTAL_MASK_WATER = 0x4,
        ELEMENTAL_MASK_STORM = 0x8
    };

    // 1-based rank of the highest rank id the player has (talent in the active spec, or its passive aura); 0 if
    // none. Pass the talent's rank ids in rank order. Never reads HasSpell.
    uint8 GetTalentRank(Player const* player, std::span<uint32 const> rankIds);
    uint8 GetTalentRank(Player const* player, std::initializer_list<uint32> rankIds);

    // ElementalMask bits of the elementals currently active for `player` (0 for nullptr).
    uint8 GetActiveElementals(Player const* player);

    // Called from the AllCreatureScript add/remove hook of the four elemental totems. Both reconcile the whole
    // Elemental state against the totem slots, so the order of a replacement (new totem added before the old one
    // leaves the world) never matters: Empowerment buffs on/off (Power of the Elements), Gathering Flames cleared
    // when no Fire Elemental is active, the Elemental Warding capstone health aura, the Empowerment amount, and
    // (one tick later, after the totem's passive summoned it) the guardian auras added by the owner (L5). `totem`
    // may be nullptr and `totemEntry` 0: a plain reconcile (login, map change, talent change).
    // A non-null Earth Elemental `totem` is a real summon: with the Booming Echoes capstone it grants
    // ECHO_EARTH_ELEMENTAL_GRANT Echo.
    void OnElementalAdded(Player* player, Creature* totem);
    void OnElementalRemoved(Player* player, uint32 totemEntry);

    // Sets the live Empowerment amount (EMPOWERMENT_PCT, plus the live Mastery with Conduit of the Elements) on
    // the player's Empowerment buffs and on the guardian-side Empowerment; changes an effect only when it moved.
    void RefreshEmpowerment(Player* player);

    // True for the three Lightning Overload copies (Lightning Bolt, Chain Lightning, Lava Burst).
    bool IsOverloadCopy(uint32 spellId);

    // Booming Echoes: adds `stacks` Echo (cap ECHO_MAX) and refreshes it to ECHO_DURATION_MS.
    void AddEcho(Player* player, uint8 stacks);

    // Call of the Elements: every active elemental totem (and its guardian) gains `ms`; the totem bar is retimed.
    // Call it before summoning the inactive elementals, so the new ones are not extended.
    void ExtendElementals(Player* player, uint32 ms);

    // Thunderstorm rank 2 (usable while stunned) is known exactly while Thunderstorm and Call of Thunder rank 3
    // are known; learns or removes it to match.
    void SyncThunderstormRank(Player* player);

    // Lava Flows talent rank (1-3) -> its haste buff id; 0 for any other rank.
    uint32 LavaFlowsHasteSpell(uint8 rank);

    // ---- S2 ----
    // Restoration spec (docs/reworks/shaman-restoration-rework.md). Per-player state (the Cloudburst store and the
    // Improved Chain Heal count) lives in the player's CustomData and is dropped by ClearState; everything else is
    // read from the shaman's own talents, auras and totem slots, so a non-shaman with a talent gets do-nothing.

    // Totemic Resonance's healing totems: Healing Stream (stock 3527), Healing Tide, Earthen Wall, Undulating
    // Currents, Cloudburst, Spirit Link and the Water Elemental's totem.
    bool IsHealingTotemEntry(uint32 entry);

    // Called from the AllCreatureScript add/remove hook for every player-owned totem (A15; the elemental totems also
    // keep OnElementalAdded/OnElementalRemoved). Added: Totemic Resonance recount, the Totemic Focus capstone
    // placement heal (cast by the totem 1 ms later), and the Cloudburst placement record plus its store buff.
    // Removed: Totemic Resonance recount and, for the recorded Cloudburst totem, the release (discarded when the
    // shaman is dead). Both run with the slot already holding the new totem or cleared.
    // S3 (added): Guardian Totems rank 2 capstone, any totem created by a shaman-family spell (elementals included):
    // GUARDIAN_TOTEMS_ARMOR for GUARDIAN_TOTEMS_ARMOR_DURATION_MS, refreshed.
    void OnPlayerTotemAdded(Player* player, Creature* totem);
    void OnPlayerTotemRemoved(Player* player, Creature* totem);

    // Puts the Totemic Resonance aura in line with the slots: removed without the talent or without a counted totem,
    // otherwise stacks = counted totems and the healing-done amount = GetTotemicResonancePct (rounded). Changes an
    // effect only when it moved, so it is also the periodic refresh for the live Mastery part (TR_REFRESH_MS).
    void RecountTotemicResonance(Player* player);

    // Live Totemic Resonance bonus in percent: count x (TR_PCT_PER_COUNT + TR_MASTERY_COEFF_PCT% of Mastery); 0
    // without the talent. Used as an explicit multiplier where the aura cannot reach (absorbs, the Water Bolt heal).
    float GetTotemicResonancePct(Player const* player);

    // Earthen Wall absorb for `owner`'s totem: the effect's base plus the owner's healing power times the generated
    // coefficient (and level penalty), times (1 + Totemic Resonance). Earthen Bulwark takes its share of this.
    // S3: times (1 + Earth's Grasp %), the percent read from the owner's rank's first DUMMY effect.
    uint32 GetEarthenWallAbsorb(Player const* owner, SpellInfo const* shield, uint8 effIndex);

    // Tidal Waves charges: a grant raises the charges to `amount` (cap TIDAL_WAVES_MAX), never lowers them, and
    // refreshes the duration to TIDAL_WAVES_DURATION_MS.
    void GrantTidalWaves(Player* player, uint8 amount);
    // Drops one charge; true when one was consumed. With the Improved Chain Heal capstone every consumed charge counts
    // toward its buff (ICH_CHARGES_NEEDED); charges consumed while the buff is up do not count.
    bool ConsumeTidalWaves(Player* player);
    uint8 GetTidalWavesCharges(Player const* player);

    // Cloudburst: stores CLOUDBURST_STORE_PCT of `effectiveHeal` while a Cloudburst totem placed by the player stands.
    void AddCloudburstStore(Player* player, uint32 effectiveHeal);
    // Ends the active Cloudburst (no-op when none): drops the store buff, unsummons the totem if it still holds the
    // Air slot, splits the store evenly among the injured players within CLOUDBURST_RADIUS_YD of the totem (cast by
    // the player, CLOUDBURST_RELEASE) unless `discard`, and sets the castable's cooldown to
    // max(0, CLOUDBURST_COOLDOWN_MS / (1 + Cooldown Haste) - time since placement), 1 ms later.
    void ReleaseCloudburst(Player* player, bool discard);
    // Logout, before the save: adds the remaining Cloudburst cooldown of a placement still recorded (the totem's removal
    // runs after the Player is gone), so the saved cooldown survives a relog. No-op without an active Cloudburst.
    // S3 (D9): first drops the bank and the Enhancement auras (charges, singles, Elemental and Earthen Ascendance, the
    // Unleashed Rage clause), so the save carries none of them.
    void OnPlayerBeforeLogout(Player* player);

    // Lengthens the active Tidal Force caster aura by `ms` (no cap).
    void ExtendTidalForce(Player* player, uint32 ms);

    // Counted healing totems (Totemic Resonance's count source), capped at TR_MAX_COUNT; 0 for nullptr.
    uint8 GetRestorationTotemCount(Player const* player);

    // ---- S3 ----
    // Enhancement spec (docs/reworks/shaman-enhancement-rework.md). Per-player state (the imbue-swap stash, the
    // charges banked during an Ascendance, the out-of-combat timer generations) lives in the player's CustomData and
    // is dropped by ClearState; charges, singles and the Ascendances are auras on the shaman (D9: dropped on death and
    // logout). Rank reads go through GetTalentRank, so a non-shaman with a talent gets do-nothing.

    // The element an imbue builds: Flametongue Fire, Frostbrand Frost, Windfury Wind, Rockbiter Earth; None otherwise
    // (Earthliving, 0, any other id).
    enum class EnhElement : uint8 { Fire, Frost, Wind, Earth, None };
    EnhElement GetImbueElement(uint32 imbueId);

    // Stacks of the element's charge buff (Fire/Frost/Wind Charge, Earth Charge); 0 for None or nullptr.
    uint8 GetCharge(Player const* player, EnhElement element);

    // Elemental Charge grant of `amount` to the element of the active imbue (Earth Charge under Rockbiter; Earthliving
    // or no imbue: nothing), capped at CHARGE_CAP_ELEMENT / CHARGE_CAP_EARTH. Needs the Elemental Charge talent. While
    // Elemental Ascendance or Earthen Ascendance is up nothing builds, except Shamanistic Rage's grant
    // (`fromShamanisticRage`), which is banked and added to the active imbue's element when the Ascendance ends. A
    // grant out of combat arms the 2 min out-of-combat timer (in combat it starts on leaving combat). Callers apply the
    // once-per-cast / per-hit / triggered rules; this function does not filter sources.
    void AddCharge(Player* player, uint8 amount, bool fromShamanisticRage);

    // spell_sha_imbue's two calls (0-verify item l: group 1251 evicts the old imbue in AfterEffectRemove, the new
    // one is applied after it in the same call stack):
    //   HandleRemove(old): OnImbueChanged(player, old, 0)  - stashes `old` with the current server tick;
    //   HandleApply(new):  OnImbueChanged(player, 0, new)  - consumes a stash from this tick as the swap old -> new.
    // A direct OnImbueChanged(player, old, new) is the swap itself. A remove with no apply in the same tick
    // (right-click, expiry) transforms nothing and keeps the charges (2 min rule); a later apply of another imbue then
    // resets the other elements' charges without a transform. Swap from Flametongue/Frostbrand/Windfury at
    // CHARGE_CAP_ELEMENT to another of the three: that element's Burst, then its single Ascendance (GrantAscendance);
    // to Rockbiter or Earthliving, or below the cap: the charges reset. Earth Charge is never touched by a swap. Same
    // imbue: nothing.
    void OnImbueChanged(Player* player, uint32 oldImbue, uint32 newImbue);

    // The element's Burst (Flame/Storm/Wind), cast by the player (triggered): unit target = the selected attackable
    // enemy, else the victim; destination = that unit, else the shaman. spell_sha_enh_burst filters the targets.
    void CastElementalBurst(Player* player, EnhElement element);

    // With the Ascendance talent: grants the element's single Ascendance unless it is already held or Elemental
    // Ascendance is up; holding all three then consumes them and grants Elemental Ascendance for ASC_DURATION_EA_MS
    // (and refreshes the Unleashed Rage clause). Fire/Frost/Wind only.
    void GrantAscendance(Player* player, EnhElement element);

    // The one-shot cosmetic burst at the shaman's feet when an Ascendance is gained (playtest P2): Fire Nova, Frost Nova,
    // Thunderstorm's lightning burst or War Stomp's ring by element (Earth: Elemental Ascendance and Earthen Ascendance).
    // A triggered self-cast of a DUMMY helper with a stock visual: no damage, threat, aura or procs. GrantAscendance
    // calls it; Living Earth calls it for Earthen Ascendance.
    void CastAscendanceVisual(Player* player, EnhElement element);

    // Live Mastery amounts (Ascendance talent's capstone; integer percent, rounded to MASTERY_ROUND_PCT): every
    // SPELLMOD_DAMAGE / SPELLMOD_DOT percent effect of the singles takes base + Mastery, of Elemental Ascendance base +
    // 2 x Mastery (speed effects are left alone); Stoneskin's MOD_DAMAGE_PERCENT_TAKEN takes GetStoneskinAmount.
    // Changes an effect only when it moved. Also adds banked charges once no Ascendance holds them. Call on apply, from
    // a periodic refresh and after a stat change (RefreshEmpowerment precedent).
    void RefreshAscendance(Player* player);

    // Spends `amount` Earth Charge when at least that many are held (banked charges are added first when free); false
    // and nothing spent otherwise.
    bool SpendEarthCharge(Player* player, uint8 amount);
    bool IsEarthenAscendant(Player const* player);

    // The Unleashed Rage damage clause (UNLEASHED_RAGE_CLAUSE, amount UR_R1..UR_R3 by rank) on while Shamanistic Rage
    // or Elemental Ascendance is up, off otherwise. The rank is read from the talent map only (the ranks are raid
    // area auras, so party members carry the rank ids). Call from both auras' apply and remove (also adds banked
    // charges once no Ascendance holds them).
    void UpdateUnleashedRage(Player* player);

    // Out-of-combat timers of the charges (EC_OOC_MS) and the singles (ASC_OOC_MS): armed on leave, cancelled on entry.
    void OnEnhCombatChange(Player* player, bool inCombat);

    // Frost Spirit: every Frost Spirit of the player casts FROST_SPIRIT_COPY at `target` for FROST_COPY_PCT% of
    // `landedDamage` (the Stormstrike's landed main- and off-hand damage, summed by the caller; cleave hits excluded).
    void OnStormstrikeLanded(Player* player, Unit* target, uint32 landedDamage);

    // Total MOD_DAMAGE_PERCENT_TAKEN amount (negative) of `stacks` Stoneskin stacks: the 202206 row's per-stack value
    // x stacks, x (1 + Mastery) with the Ascendance talent, rounded once (integer percent). AddStoneskin and
    // ErodeStoneskin write it after every stack change (the engine's stack recalculation multiplies the per-stack
    // amount after the calc hooks, so a per-stack hook cannot carry the Mastery fraction).
    int32 GetStoneskinAmount(Player const* player, uint8 stacks);

    // Rockbiter applied/removed (spell_sha_imbue, Rockbiter only, after OnImbueChanged): Spirit Guard's parry child
    // (rank 1/2/3 %) and the Improved Lightning Shield threat child follow Rockbiter and the talents. Skipped while the
    // player is not in world (login aura load: OnPlayerLogin reconciles through OnEnhTalentsChanged).
    void OnRockbiterChanged(Player* player, bool applied);

    // Talent learn/reset, spec swap, login and map change: the two Rockbiter children, the Unleashed Rage clause and
    // the live amounts; without Elemental Charge the charges (and the bank) go, without Ascendance the singles,
    // Elemental Ascendance and Earthen Ascendance go. (Re)starts the 1 s live-Mastery refresh, which runs while the
    // Ascendance talent is known and a single, Elemental Ascendance or Stoneskin is up.
    void OnEnhTalentsChanged(Player* player);

    // Death (hooks only): drops the banked charges and the swap stash (the auras are already gone, D9) and re-checks
    // the Unleashed Rage clause.
    void OnEnhPlayerDied(Player* player);
}

#endif
