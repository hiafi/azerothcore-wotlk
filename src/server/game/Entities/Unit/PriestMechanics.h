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

#ifndef __PRIESTMECHANICS_H
#define __PRIESTMECHANICS_H

#include "Define.h"
#include "ObjectGuid.h"
#include "SharedDefines.h"

class Aura;
class Player;
class SpellInfo;
class Unit;
enum DamageEffectType : uint8;

/*
 * Priest-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors MageMechanics.h's shape
 * (see that file's own header comment for the general rationale: Unit.cpp/core can't depend on
 * scripts/, so this can't live next to spell_priest_new.cpp).
 */
namespace Priest
{
    // Spell ids shared across translation units - defined once here so the cross-class and core
    // call sites can't drift from the priest scripts' own copy.

    // Shared "death-prevention already used" lockout (2 min) between Spirit of Redemption (Holy
    // 4,1), Ardent Defender and Cheat Death - each checks and casts it (spell_priest_holy.cpp,
    // spell_paladin.cpp, spell_rogue.cpp).
    constexpr uint32 SPELL_CHEATED_DEATH_MARKER = 200193;

    // Echo of Light (Holy 8,3) reservoir ticks - fixed cadence, done/taken bonus snapshotted at
    // application (SpellAuraEffects.cpp's IsFixedCadencePeriodic list).
    constexpr uint32 SPELL_ECHO_OF_LIGHT_HEAL = 200218;
    constexpr uint32 SPELL_ECHO_OF_LIGHT_DAMAGE = 200219;

    // Unit::SpellPctDamageModsDone's whole (former) SPELLFAMILY_PRIEST case: Void Eruption's
    // Voidform buff (docs/reworks/priest-new-spells.md - "increases your periodic Shadow damage by
    // 10% for 10 sec"; no native WotLK AuraType computes "+X% periodic damage done", hence the live
    // marker-aura-by-icon read), plus the stock Mind Flay / Smite / Shadow Word: Death glyph
    // clauses and Twisted Faith's Mind Flay half, migrated out of Unit.cpp verbatim
    // (.agents/plans/priest-rework/priest-rework.PLAN.md sec 6.8).
    //
    // The call site now sits *outside* Unit::SpellPctDamageModsDone's per-family switch (PLAN sec
    // 6.7), so this runs for every spell family - each clause carries its own gate. Everything
    // here is currently priest-family-only and lives behind one shared family check; a later
    // cross-class clause (Holy's Divine Fury, which buffs Holy-school damage from any class) goes
    // *above* that check.
    void ApplyDoneDamagePctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, DamageEffectType damagetype, float& doneTotalMod);

    // Unit::SpellDoneCritChance's priest hook, next to Mage's own equivalent - Discipline's Inner
    // Focus (2,1) turns its charge into a guaranteed Flash Heal crit
    // (docs/reworks/priest-disc-rework.md). An absolute override, applied last, so no other
    // modifier can push it off 100.
    void ApplySpellCritChanceMods(Unit const* caster, SpellInfo const* spellProto, float& critChance);

    // Unit::SpellTakenCritChance's "Custom crit by class" SPELLFAMILY_PRIEST case - Renewed Hope's
    // Weakened-Soul crit bonus (migrated out of that function's OVERRIDE_CLASS_SCRIPTS loop, PLAN
    // sec 6.8) and Focused Power's (5,0) Prayer of Healing capstone. `victim` is the unit being
    // healed/hit, `caster` the priest.
    void ApplySpellTakenCritChanceMods(Unit const* victim, Unit const* caster, SpellInfo const* spellProto, float& critChance);

    // Spirit Shell (Discipline 10,1): "your direct healing spells no longer heal - instead they
    // create an absorption shield on the target for the amount that would have been healed."
    // Called from Spell::DoAllEffectOnTarget's heal branch with the post-crit heal amount; returns
    // true (and zeroes `heal`) when the heal was converted, so the heal itself lands for 0 and
    // Divine Aegis sees nothing to work with.
    bool TryConvertHealToSpiritShell(Unit* caster, Unit* target, SpellInfo const* spellProto, uint32& heal);

    // Holy rework (docs/reworks/priest-holy-rework.md, priest-rework.HOLY.md "Core hardcode
    // migration owed by this pass") - Test of Faith's (8,2) healing clause, migrated out of
    // Unit::SpellPctHealingModsDone's OVERRIDE_CLASS_SCRIPTS loop (`case 21: case 6935: case
    // 6918:`, one misc value per rank). One call site in that function.
    void ApplyDoneHealingPctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, float& doneTotalMod);

    // Test of Faith (8,2) capstone: "10% less magic damage taken while casting Smite, Holy Fire or
    // any Priest healing spell." `victim` is the priest taking incoming spell damage; `attacker` is
    // whoever cast the incoming spell (any class). Called from Unit::SpellDamageBonusTaken.
    void ApplySpellDamageTakenPctMods(Unit* victim, Unit* attacker, SpellInfo const* spellProto, float& takenMod);

    // Renew extension pool (docs/reworks/priest-holy-rework.md 5.3): shared by Holy Concentration
    // (6,0, spell_pri_holy_concentration_extend) and Empowered Renew's capstone (8,0,
    // spell_pri_empowered_renew_capstone), both in spell_priest_holy.cpp - a free function here
    // (rather than a member on spell_pri_renew, spell_priest.cpp) because both callers need to
    // reach the pool from a different translation unit than spell_pri_renew is defined in;
    // Aura::GetScript<T>() (a dynamic_cast) needs T's complete definition, which isn't available
    // across files without a shared header. Needs no per-instance state: "how much extension this
    // Renew has already used" is re-derived each call from the gap between the aura's current and
    // base max duration. `renew` is the caster's live Renew Aura on some target (`Unit::GetAura`);
    // `ms` is the requested extension, capped so total duration never exceeds base + 6000ms (PLAN's
    // "Total duration may never exceed 21 seconds from application", base Renew being 15 s).
    void ExtendRenewDuration(Aura* renew, int32 ms);

    /*
     * Shadow rework (docs/reworks/priest-shadow-rework.md,
     * .agents/plans/priest-rework/priest-rework.SHADOW.md "PriestMechanics additions") - the
     * Madness resource, Tentacle of Madness spawn/despawn bookkeeping and the Deathspeaker kill
     * clause. This is the first player-keyed state this file carries - PriestMechanics.cpp keeps
     * it in file-scope `unordered_map<ObjectGuid, ...>`s in an anonymous namespace, the same
     * unsynchronized-access shape `Unit.h`'s own `extraAttacksTargets` member already uses
     * (`std::unordered_map<ObjectGuid, uint32>`), safe here for the same reason: every call site
     * below fires from world update, which is single-threaded in this fork (map/instance updates
     * run on dedicated update threads, but never concurrently with each other's own player/unit
     * state - see `Map::Update`'s caller in `MapUpdater`/`World::Update`).
     */

    // Madness source, spec units (SHADOW.md "PriestMechanics additions"): 1 per player Mind Flay
    // tick, 1 per tentacle Mind Flay tick (never x3, even during Surrender - design doc sec 4.1
    // "the unit's own behaviour ... unaffected by the exclusion list"), 5 per Mind Blast cast, 25
    // flat per Void Eruption cast. PlayerMindFlay/MindBlast are x3'd by AddMadness itself while
    // Surrender to Madness (200269) is active (design doc sec 4.5); VoidEruption is never x3'd
    // (design doc sec "Void Eruption": "Madness generation is a flat 25 regardless").
    enum class MadnessSource : uint8
    {
        PlayerMindFlay,
        TentacleMindFlay,
        MindBlast,
        VoidEruption
    };

    // What summoned/attempted to summon a Tentacle of Madness - TrySummonTentacle uses this to
    // decide ICD/bypass rules (SHADOW.md "Spawn budget / ICD rules"): ShadowWordPain/MindFlay/
    // Backlash share a 3 s ICD (bypassed while Surrender to Madness is up, for ShadowWordPain and
    // MindFlay only); MindBlast and Kill always bypass it. The max-5-live-tentacles cap applies to
    // every trigger unconditionally.
    enum class TentacleTrigger : uint8
    {
        ShadowWordPain,
        MindFlay,
        Backlash,
        MindBlast,
        Kill
    };

    // Is Call of the Void known at all - AddMadness is a no-op unless this is true (SHADOW.md:
    // "All Madness calls are no-ops unless Priest::HasMadness(player)"), so every generation call
    // site can fire unconditionally without its own guard.
    bool HasMadness(Player const* player);

    // Adds Madness (no-op if !HasMadness or amount <= 0), clamping to the raised internal cap
    // (priest-rework.PLAN.md sec 1: 500, not the design doc's 450 - kept in spec units so the
    // visible/250-stack math under WotLK's uint8 aura-stack ceiling stays clean at floor(v/2)) and
    // refreshing the visible Madness aura (200271)'s stack count and its full 30 s duration -
    // refresh-on-gain, not per-stack independent expiry (design doc sec 4.3: per-stack expiry caps
    // effective Madness far below the real maximum).
    void AddMadness(Player* player, int32 amount, MadnessSource source);

    // Current internal Madness value (spec units, 0..500) for `player`, or 0 if untracked.
    int32 GetMadness(Player const* player);

    // Consumes up to `amount` (or all of it when amount < 0), clamped to what's available, and
    // returns how much was actually consumed. Drops the visible Madness aura (200271) once the
    // value reaches 0 - this is a *manual* removal (AURA_REMOVE_BY_DEFAULT), not the aura's own
    // 30 s expiry, so it deliberately does not run through spell_pri_madness's OnRemove
    // (expire-only) hook; the internal value is already authoritative here, ClearMadness is only
    // for the natural-expiry path.
    int32 ConsumeMadness(Player* player, int32 amount);

    // spell_pri_madness's OnRemove erases the tracked value for `playerGuid`. Runs on *every*
    // removal mode, not just the natural 30 s expiry: death (`RemoveAllAurasOnDeath`, removal mode
    // AURA_REMOVE_BY_DEFAULT) and a dispel would otherwise leave an invisible internal value behind
    // with no aura to show it. Harmless on the ConsumeMadness path, which erases the entry itself
    // before removing the aura, so this is only ever a second erase of an absent key.
    void ClearMadness(ObjectGuid playerGuid);

    // Drops every piece of per-player Shadow state this file keeps for `playerGuid` - the Madness
    // value plus the two spawn-bookkeeping timestamps (shared tentacle ICD, last Mind Blast spawn),
    // neither of which any aura's removal covers and so would otherwise grow without bound over a
    // long uptime. Called from the OnPlayerLogout PlayerScript in spell_priest_shadow.cpp.
    void ClearShadowPlayerState(ObjectGuid playerGuid);

    // Attempts to summon a Tentacle of Madness (200245) for `player` via `trigger`. Enforces the
    // max-5-live cap (counts `player->m_Controlled` for creature entry 300102, the same public
    // `Unit::ControlSet` idiom `spell_dk.cpp`/`spell_hunter.cpp`/`spell_item.cpp` already use to
    // find a player's own guardians) and the shared 3 s ICD for ShadowWordPain/MindFlay/Backlash
    // (bypassed for those two triggers while Surrender to Madness (200269) is active - SHADOW.md
    // "Spawn budget / ICD rules"; MindBlast and Kill always bypass it). On an actual summon for the
    // MindBlast trigger, stamps the last-Mind-Blast-spawn timestamp IsMindBlastTentacleGuaranteed
    // reads (see that function's own comment for why the timestamp lives here rather than in the
    // calling script). Returns whether a tentacle was actually summoned.
    bool TrySummonTentacle(Player* player, TentacleTrigger trigger);

    // Small addition beyond SHADOW.md's literal PriestMechanics code block, needed to keep the
    // Mind Blast 25 s "guaranteed if none summoned in that window" timestamp (SHADOW.md talent
    // table 3,0 / design doc sec 4.2) fully encapsulated in this file's own state instead of
    // leaking a second copy of it into spell_priest_shadow.cpp: `spell_pri_mind_blast_shadow` needs
    // to read "has it been >= 25 s" to decide whether to force the roll, but the timestamp itself
    // is stamped by TrySummonTentacle on an actual summon (see that function's comment) - so the
    // read side needs its own accessor. Does not mutate anything.
    bool IsMindBlastTentacleGuaranteed(Player const* player);

    // Despawns every one of `player`'s live Tentacles of Madness (Surrender to Madness ending,
    // either exit path - design doc sec 4.5 "your Tentacles of Madness are destroyed").
    void DespawnTentacles(Player* player);

    // Per-tentacle stat snapshot, captured once at summon (design doc sec 4.1 "Reads spell power,
    // haste, crit, Mastery and Versatility once at summon and holds them for its full life").
    // Native stats with a real AuraType (spell power, crit, haste) are snapshotted by
    // spell_pri_tentacle_scaling's own DoEffectCalcAmount handlers on aura 200272 (same shape as
    // spell_pri_shadowfiend_scaling) and need no entry here; Mastery/Versatility are this server's
    // own custom stats (priest-rework.PLAN.md sec 3.8/6) with no native per-Unit field or AuraType
    // to carry them on a Guardian, so they're the only two fields this struct needs.
    struct TentacleSnapshot
    {
        float mastery = 0.0f;
        float versatility = 0.0f;
    };

    // Read side, called from the tentacle's own damage path in ApplyDoneDamagePctMods.
    TentacleSnapshot const* GetTentacleSnapshot(Unit const* tentacle);

    // Write side - companion to GetTentacleSnapshot (SHADOW.md declares the struct and the read
    // accessor but the backing map obviously needs a way to be populated; called once from
    // spell_pri_tentacle_scaling::OnEffectApply).
    void SetTentacleSnapshot(ObjectGuid tentacleGuid, TentacleSnapshot const& snapshot);

    // Cleanup companion, called from spell_pri_tentacle_scaling::OnEffectRemove so the backing map
    // doesn't grow unboundedly over a long raid night as tentacles spawn and despawn.
    void ClearTentacleSnapshot(ObjectGuid tentacleGuid);

    // Deathspeaker's (4,1) kill clause (design doc sec 4.2/SHADOW.md talent table): a Shadow Word:
    // Death kill rolls a separate, ICD-exempt Tentacle of Madness chance. Call site next to
    // `Mage::OnKill` in `Unit::Kill` (`Unit.cpp` ~13958).
    void OnKill(Unit* killer, Unit* victim, SpellInfo const* spellProto);
}

#endif
