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
 * Rogue rework - ScriptMgr handlers (rogue-rework RG0a, S1, S2, S3). Bodies: RogueMechanics.
 * One RoguePlayerScript and one RogueUnitScript for every spec: S2 / S3 append their hooks here, never fork them.
 */

#include "Item.h"
#include "ItemTemplate.h"
#include "Player.h"
#include "PlayerScript.h"
#include "RogueMechanics.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "Unit.h"
#include "UnitScript.h"
#include <algorithm>

class RoguePlayerScript : public PlayerScript
{
public:
    RoguePlayerScript() : PlayerScript("RoguePlayerScript",
        { PLAYERHOOK_ON_LOGIN, PLAYERHOOK_ON_SPELL_CAST, PLAYERHOOK_ON_AFTER_SET_VISIBLE_ITEM_SLOT,
          PLAYERHOOK_ON_TALENTS_RESET, PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED, PLAYERHOOK_ON_PLAYER_IS_CLASS }) { }

    // The energy-haste grant lives here although druids get it too: energy is a rogue resource (PLAN 1D.14) and
    // Rogue::IsEnergyUser is the one place that decides who regenerates energy faster with haste.
    // U26: a login talent reset (AT_LOGIN_RESET_TALENTS, CharacterHandler) has already run and the poison auras are
    // loaded, so Master Poisoner's second Lethal slot is trimmed at once when the capstone is gone.
    // S2 (R16): Master of Subtlety / Mark of the Master Assassin are infinite while Hidden and saved with the
    // character; re-evaluate them against the loaded stealth auras (no apply hook fires for a buff saved while Hidden).
    void OnPlayerLogin(Player* player) override
    {
        Rogue::EnsureEnergyHaste(player);

        if (Rogue::HasAnyPoison(player))
            Rogue::EnforceLethalSlots(player, 0);

        Rogue::UpdateHiddenBuffs(player);
    }

    // mod-playerbots' Randomize strips auras (and may clear spells) while a bot is in the world.
    // S1: the one cast-start dispatcher (Rogue::OnSpellCast, before effects, combo points not yet spent); S2 / S3
    // append to it in RogueMechanics, never add a second one here.
    void OnPlayerSpellCast(Player* player, Spell* spell, bool /*skipCheck*/) override
    {
        if (!player || !spell || spell->IsTriggered())
            return;

        SpellInfo const* spellInfo = spell->GetSpellInfo();

        // The recast's own triggered cast re-enters this hook before the aura exists, so only real casts re-grant.
        if (spellInfo->Id != RogueData::SPELL_ENERGY_HASTE)
            Rogue::EnsureEnergyHaste(player);

        // Every dispatcher branch (finishers, Mutilate, Kingsbane, Fan of Knives) is a Rogue-family spell.
        if (spellInfo->SpellFamilyName == SPELLFAMILY_ROGUE)
            Rogue::OnSpellCast(player, spell);
    }

    // U26 (S1a R2): Player::resetTalents calls this as its first statement, before Master Poisoner 58410 is removed,
    // so the trim waits one update. The event list dies with the Player, so capturing it is safe.
    void OnPlayerTalentsReset(Player* player, bool /*noCost*/) override
    {
        ScheduleLethalSlotTrim(player);
    }

    // Dual-spec swap: same rule as a reset.
    void OnPlayerAfterSpecSlotChanged(Player* player, uint8 /*newSlot*/) override
    {
        ScheduleLethalSlotTrim(player);
    }

    // Poison glow (shaman imbue-glow clone): SetVisibleItemSlot (equip, swap, enchant, login inventory load) just
    // rewrote the slot's real enchant visuals; write the glow back over the temp half while a poison is up.
    void OnPlayerAfterSetVisibleItemSlot(Player* player, uint8 slot, Item* item) override
    {
        if (slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND)
            return;

        if (!player || !item || item->GetTemplate()->Class != ITEM_CLASS_WEAPON)
            return;

        if (Rogue::HasAnyPoison(player))
            Rogue::WritePoisonGlow(player, slot);
    }

    // S3 (U69): Riposte lights on a dodge. Unit.cpp's proc-flag aura states skip AURA_STATE_DEFENSE on a dodge for
    // IsClass(CLASS_ROGUE, CLASS_CONTEXT_ABILITY_REACTIVE), the only reader of that pair; answering false makes a
    // rogue's dodge set it (and the reactive timer) like a parry. A non-rogue already answers false, so no class test.
    // Player::IsClass asks this for every class check on a player: compare the two enums and nothing else.
    Optional<bool> OnPlayerIsClass(Player const* /*player*/, Classes playerClass, ClassContext context) override
    {
        if (playerClass == CLASS_ROGUE && context == CLASS_CONTEXT_ABILITY_REACTIVE)
            return false;

        return std::nullopt;
    }

private:
    static void ScheduleLethalSlotTrim(Player* player)
    {
        if (!player || !Rogue::HasAnyPoison(player))
            return;

        player->m_Events.AddEventAtOffset([player]() { Rogue::EnforceLethalSlots(player, 0); }, 1ms);
    }
};

// S1 (Assassination): Overkill, Remorseless Attacks, Zoldyck Recipe, Dashing Scoundrel and the dual-strike / Fan of
// Knives records. Every hook here runs for every unit in the world, so each handler rejects on the spell id or the
// Rogue spell family and a player owner before any call out (a Rogue-family spell is the class check: it also covers
// a Classless character using rogue abilities). The enable list names exactly the hooks overridden (an empty list
// would enable every UnitHook).
// S3 (Combat): the Blade Flurry copier (U59), Blade Twisting / the builder stamp's landed flag, Prey on the Weak on
// auto attacks (U60). The three melee hooks fire for every swing on the server (bots and creatures included): each
// rejects on the damage, then IsPlayer(), then at most one aura lookup, with no allocation before them.
class RogueUnitScript : public UnitScript
{
public:
    RogueUnitScript() : UnitScript("RogueUnitScript", true,
        { UNITHOOK_ON_AURA_APPLY, UNITHOOK_ON_AURA_REMOVE, UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN,
          UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK, UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL,
          UNITHOOK_ON_PERIODIC_DAMAGE_FINAL, UNITHOOK_ON_MELEE_DAMAGE_FINAL, UNITHOOK_MODIFY_MELEE_DAMAGE,
          UNITHOOK_ON_BEFORE_ROLL_MELEE_OUTCOME_AGAINST }) { }

    // Overkill: true Stealth or Vanish's aura only. S2: the Hidden state (Stealth, Vanish's aura, Shadowed 51713)
    // drives Master of Subtlety / Mark of the Master Assassin; Shadowed also clears Lingering Shadow. Also fires on a
    // refresh (Unit::_AddAura, ModStackAmount): every call below is idempotent.
    void OnAuraApply(Unit* unit, Aura* aura) override
    {
        if (!unit || !aura || !unit->IsPlayer())
            return;

        // S3a-REVIEW L8: the per-swing Prey on the Weak hooks read the held rank from a cache kept here.
        if (IsPreyRankAura(aura->GetId()))
        {
            Rogue::UpdatePreyRankCache(unit->ToPlayer());
            return;
        }

        if (!IsHiddenAura(aura->GetId()))
            return;

        Player* rogue = unit->ToPlayer();
        if (aura->GetId() == RogueData::SPELL_SHADOW_DANCE)
            Rogue::OnShadowedApplied(rogue);
        else
            Rogue::UpdateOverkill(rogue);

        Rogue::UpdateHiddenBuffs(rogue);
    }

    // Unit::_UnapplyAura calls this after the application is gone, so UpdateOverkill sees whether the other stealth
    // aura remains (an attack removes both in one sweep, mode DEFAULT; the rogue's death, mode DEATH).
    // Remorseless Attacks: RemoveAllAurasOnDeath unapplies each of a rogue's bleeds on the victim with mode DEATH.
    // S2: Shadowed's removal hands the mode on (OnShadowedRemoved skips death and logout, 0-verify item 8); the Hidden
    // buffs follow every 1784 / 11327 / 51713 removal (UpdateHiddenBuffs returns for a dead rogue).
    void OnAuraRemove(Unit* unit, AuraApplication* aurApp, AuraRemoveMode mode) override
    {
        if (!unit || !aurApp)
            return;

        Aura const* aura = aurApp->GetBase();
        uint32 const spellId = aura->GetId();
        if (IsPreyRankAura(spellId))
        {
            if (Player* rogue = unit->ToPlayer())
                Rogue::UpdatePreyRankCache(rogue);

            return;
        }

        if (IsHiddenAura(spellId))
        {
            if (!unit->IsPlayer())
                return;

            Player* rogue = unit->ToPlayer();
            if (spellId == RogueData::SPELL_SHADOW_DANCE)
                Rogue::OnShadowedRemoved(rogue, mode);
            else
                Rogue::UpdateOverkill(rogue);

            Rogue::UpdateHiddenBuffs(rogue);
            return;
        }

        if (mode != AURA_REMOVE_BY_DEATH || !aura->GetCasterGUID().IsPlayer())
            return;

        SpellInfo const* spellInfo = aura->GetSpellInfo();
        if (spellInfo->SpellFamilyName == SPELLFAMILY_ROGUE && Rogue::IsRogueBleed(spellInfo))
            Rogue::OnBleedVictimDied(unit, aura);
    }

    // Zoldyck Recipe (direct hits). Unit::CalculateSpellDamageTaken calls this for every direct spell hit, before armor
    // and crit. Not gated on IGNORE_CASTER_MODIFIERS on purpose: the health clause is live on Doomblade's stored tick
    // (doc), which carries that attribute.
    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        if (damage <= 0 || !IsPlayerRogueSpell(attacker, spellInfo))
            return;

        float const multiplier = Rogue::GetHealthClauseMultiplier(attacker, target, spellInfo);
        if (multiplier != 1.0f)
            damage = int32(float(damage) * multiplier);
    }

    // Zoldyck Recipe (ticks), live health per tick. The attacker is null when the caster is gone; the periodic heal
    // path also lands here (GetHealthClauseMultiplier answers 1.0f for anything but a rogue bleed or poison).
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage,
        SpellInfo const* spellInfo) override
    {
        if (!damage || !IsPlayerRogueSpell(attacker, spellInfo))
            return;

        float const multiplier = Rogue::GetHealthClauseMultiplier(attacker, target, spellInfo);
        if (multiplier != 1.0f)
            damage = uint32(float(damage) * multiplier);
    }

    // Dual-strike hands and Fan of Knives (post-mitigation, pre-absorb, with isCrit): the hands' hits land inside the
    // parent's launch phase, before its AfterCast resolves them once. Dashing Scoundrel: a direct poison crit.
    // S2 Honor Among Thieves: a finisher's crit (Eviscerate, Deadly Throw, Death from Above's two hits); the crit flag
    // is reliable here (before absorb, 0-verify item 4) and OnFinisherCrit matches it against the cast's stamp.
    // S3: every rogue hit goes to OnCombatStrikeHit (Blade Twisting, the U54 (b) landed flag; it rejects by id), and
    // a damaging hit with Blade Flurry up to the copier (its exclusions, the copy 203991 included, are inside).
    void OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo,
        bool isCrit) override
    {
        if (!target || !IsPlayerRogueSpell(attacker, spellInfo))
            return;

        Player* rogue = attacker->ToPlayer();
        if (IsRecordedStrike(spellInfo->Id))
            Rogue::RecordStrikeHit(rogue, target, spellInfo, uint32(std::max(damage, 0)), isCrit);

        if (isCrit && Rogue::IsRoguePoisonDamage(spellInfo))
            Rogue::OnRogueDamageCrit(rogue, spellInfo, false);

        if (isCrit && IsHonorAmongThievesFinisher(spellInfo->Id))
            Rogue::OnFinisherCrit(rogue, target, spellInfo);

        Rogue::OnCombatStrikeHit(rogue, target, spellInfo, uint32(std::max(damage, 0)));

        if (damage > 0 && rogue->HasAura(RogueData::SPELL_BLADE_FLURRY))
            Rogue::OnBladeFlurryDamage(rogue, target, uint32(damage), spellInfo);
    }

    // S3 Blade Flurry (U59) on auto attacks: both hands and extra attacks land here once per swing (Unit.cpp
    // CalculateMeleeDamage, pre-absorb total, 0 on a miss / dodge / parry). spellInfo null = an auto attack.
    void OnMeleeDamageFinal(Unit* target, Unit* attacker, uint32 damage, bool /*isCrit*/) override
    {
        if (!damage || !target || !attacker || !attacker->IsPlayer() ||
            !attacker->HasAura(RogueData::SPELL_BLADE_FLURRY))
            return;

        Rogue::OnBladeFlurryDamage(attacker->ToPlayer(), target, damage, nullptr);
    }

    // S3 Prey on the Weak (U60), the < 35% damage clause on auto attacks: per damage slot, before armor and the
    // outcome roll. GetAutoAttackHealthMultiplier tests health before any rank lookup.
    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        if (!damage || !target || !attacker || !attacker->IsPlayer())
            return;

        float const multiplier = Rogue::GetAutoAttackHealthMultiplier(attacker, target);
        if (multiplier != 1.0f)
            damage = uint32(float(damage) * multiplier);
    }

    // S3 Prey on the Weak (U60), the > 90% crit clause on auto attacks between casts (crit_chance in 1/100 %; net of
    // the 204003 debuff GetUnitCriticalChance already counts).
    void OnBeforeRollMeleeOutcomeAgainst(Unit const* attacker, Unit const* victim, WeaponAttackType /*attType*/,
        int32& /*attackerMaxSkillValueForLevel*/, int32& /*victimMaxSkillValueForLevel*/,
        int32& /*attackerWeaponSkill*/, int32& /*victimDefenseSkill*/, int32& crit_chance, int32& /*miss_chance*/,
        int32& /*dodge_chance*/, int32& /*parry_chance*/, int32& /*block_chance*/) override
    {
        if (!attacker || !victim || !attacker->IsPlayer())
            return;

        Rogue::ModifyPreyAutoCrit(attacker, victim, crit_chance);
    }

    // Dashing Scoundrel: a poison tick crit (Deadly Poison, Kingsbane, Shattering Vial).
    void OnPeriodicDamageFinal(Unit* /*target*/, Unit* attacker, uint32 /*damage*/, SpellInfo const* spellInfo,
        bool isCrit) override
    {
        if (!isCrit || !IsPlayerRogueSpell(attacker, spellInfo) || !Rogue::IsRoguePoisonDamage(spellInfo))
            return;

        Rogue::OnRogueDamageCrit(attacker->ToPlayer(), spellInfo, true);
    }

private:
    // Fan of Knives' off-hand strike (spell_linked_spell 51723 -> 52874), not declared in RogueData.
    static constexpr uint32 SPELL_FAN_OF_KNIVES_OFF_HAND = 52874;

    // Hidden = Stealth 1784 | Vanish's aura 11327 | Shadowed 51713 (S2-HANDOFF section 7). Overkill reads the first
    // two only (inside UpdateOverkill).
    static bool IsHiddenAura(uint32 spellId)
    {
        return spellId == RogueData::SPELL_STEALTH || spellId == RogueData::SPELL_VANISH_11327 ||
            spellId == RogueData::SPELL_SHADOW_DANCE;
    }

    // Prey on the Weak's ranks (S3a-REVIEW L8: Rogue::UpdatePreyRankCache).
    static bool IsPreyRankAura(uint32 spellId)
    {
        return spellId == RogueData::SPELL_PREY_ON_THE_WEAK || spellId == RogueData::SPELL_PREY_ON_THE_WEAK_51686 ||
            spellId == RogueData::SPELL_PREY_ON_THE_WEAK_51687;
    }

    // The finisher hits whose crit can trigger Honor Among Thieves (Death from Above's area and landing hits belong to
    // its cast 204148; Between the Eyes since S3).
    static bool IsHonorAmongThievesFinisher(uint32 spellId)
    {
        switch (spellId)
        {
            case RogueData::SPELL_EVISCERATE:
            case RogueData::SPELL_DEADLY_THROW:
            case RogueData::SPELL_DEATH_FROM_ABOVE_AREA:
            case RogueData::SPELL_DEATH_FROM_ABOVE_LANDING:
            case RogueData::SPELL_BETWEEN_THE_EYES:
                return true;
            default:
                return false;
        }
    }

    static bool IsPlayerRogueSpell(Unit const* attacker, SpellInfo const* spellInfo)
    {
        return spellInfo && spellInfo->SpellFamilyName == SPELLFAMILY_ROGUE && attacker && attacker->IsPlayer();
    }

    static bool IsRecordedStrike(uint32 spellId)
    {
        switch (spellId)
        {
            case RogueData::SPELL_MUTILATE_MH:
            case RogueData::SPELL_MUTILATE_OH:
            case RogueData::SPELL_KINGSBANE_MH:
            case RogueData::SPELL_KINGSBANE_OH:
            case RogueData::SPELL_FAN_OF_KNIVES:
            case SPELL_FAN_OF_KNIVES_OFF_HAND:
                return true;
            default:
                return false;
        }
    }
};

void AddSC_rogue_hooks()
{
    new RoguePlayerScript();
    new RogueUnitScript();
}
