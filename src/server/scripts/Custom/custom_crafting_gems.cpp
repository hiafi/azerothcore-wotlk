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

// Custom: crafting rework C5, meta gems (.agents/plans/crafting-rework/crafting-rework.C5-RESEARCH.md, rulings
// 2026-11-11). Each meta gem's enchant casts a passive equip aura (apps/dbc-tools/source/world/crafting_gems.py,
// spells 207150-207159) that scales with the gems socketed in the player's equipped items:
//
// - Kaleidoscopic: 10% on a damaging or healing hit, ICD 45 s (spell_proc), one roll per cast: 15 s of +6 rating per
//   gem, the stat set by the gem's own color (six colors; a hybrid counts as its hybrid color only).
// - Purist's: +1% Strength, Agility, Intellect and Spirit per two pure red gems.
// - Relentless: +1% critical strike damage per yellow gem (hybrids count), aura 163 on all schools. The engine adds
//   aura 163 to spell crits and melee crits but not to ranged auto attacks (Unit::CalculateMeleeDamage only reads it
//   in its melee branch), so Auto Shot crits don't gain it; ranged abilities do.
// - Bulwark: 15% when hit, ICD 30 s: absorbs 1% of max health per blue gem (hybrids count) for 10 s.
// - Wellspring: a critical heal, ICD 6 s: restores 0.1% of max mana per blue gem (hybrids count).
//
// The meta gem itself never counts. The proc metas count gems when they fire. Purist and Relentless hold a standing
// amount, recalculated once on the player's next update whenever a socket enchant is applied or removed (equip,
// unequip, socketing, login): OnPlayerCanApplyEnchantment sees every one of those.

#include "Chat.h"
#include "CommandScript.h"
#include "DBCStores.h"
#include "GameTime.h"
#include "Item.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"

using namespace Acore::ChatCommands;

namespace CraftingGems
{
    enum Spells : uint32
    {
        SPELL_KALEIDOSCOPE        = 207150,
        SPELL_KALEIDOSCOPE_BUFF_A = 207151, // Haste, Crit, Mastery
        SPELL_KALEIDOSCOPE_BUFF_B = 207152, // Versatility, Proc Chance, Cooldown Haste
        SPELL_PURIST_A            = 207153,
        SPELL_PURIST_B            = 207154,
        SPELL_RELENTLESS          = 207155,
        SPELL_BULWARK             = 207156,
        SPELL_BULWARK_SHIELD      = 207157,
        SPELL_WELLSPRING          = 207158,
        SPELL_WELLSPRING_MANA     = 207159,
    };

    constexpr int32 KALEIDOSCOPE_RATING_PER_GEM = 6;
    constexpr uint32 PURIST_GEMS_PER_PERCENT = 2;
    constexpr int32 BULWARK_HEALTH_PCT_PER_GEM = 1;   // percent of max health
    constexpr int32 WELLSPRING_MANA_PERMILLE_PER_GEM = 1; // per mille (0.1%) of max mana

    // Gem colors (GemProperties.Type, ItemTemplate.h SocketColor).
    constexpr uint32 COLOR_ORANGE = SOCKET_COLOR_RED | SOCKET_COLOR_YELLOW;
    constexpr uint32 COLOR_PURPLE = SOCKET_COLOR_RED | SOCKET_COLOR_BLUE;
    constexpr uint32 COLOR_GREEN  = SOCKET_COLOR_YELLOW | SOCKET_COLOR_BLUE;

    struct GemCounts
    {
        uint32 byType[16] = {}; // exact GemProperties.Type (Kaleidoscope's six colors)
        uint32 red = 0;         // hybrids count for both of their colors (R35)
        uint32 yellow = 0;
        uint32 blue = 0;

        uint32 Pure(uint32 color) const { return byType[color]; }
    };

    // Counts the gems socketed in the player's equipped items. Meta gems are skipped.
    GemCounts CountGems(Player const* player)
    {
        GemCounts counts;
        for (uint8 slot = EQUIPMENT_SLOT_START; slot < EQUIPMENT_SLOT_END; ++slot)
        {
            Item* item = player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot);
            if (!item || item->IsBroken())
                continue; // a broken item's enchants (gems included) are off

            for (uint32 enchantSlot = SOCK_ENCHANTMENT_SLOT; enchantSlot < SOCK_ENCHANTMENT_SLOT + MAX_GEM_SOCKETS;
                 ++enchantSlot)
            {
                uint32 enchantId = item->GetEnchantmentId(EnchantmentSlot(enchantSlot));
                if (!enchantId)
                    continue;

                SpellItemEnchantmentEntry const* enchant = sSpellItemEnchantmentStore.LookupEntry(enchantId);
                if (!enchant || !enchant->GemID)
                    continue;

                ItemTemplate const* gemProto = sObjectMgr->GetItemTemplate(enchant->GemID);
                if (!gemProto || !gemProto->GemProperties)
                    continue;

                GemPropertiesEntry const* gem = sGemPropertiesStore.LookupEntry(gemProto->GemProperties);
                if (!gem || (gem->color & SOCKET_COLOR_META) || gem->color >= 16)
                    continue;

                ++counts.byType[gem->color];
                if (gem->color & SOCKET_COLOR_RED)
                    ++counts.red;
                if (gem->color & SOCKET_COLOR_YELLOW)
                    ++counts.yellow;
                if (gem->color & SOCKET_COLOR_BLUE)
                    ++counts.blue;
            }
        }
        return counts;
    }

    int32 PuristPercent(GemCounts const& counts)
    {
        return int32(counts.Pure(SOCKET_COLOR_RED) / PURIST_GEMS_PER_PERCENT);
    }

    // One recount per update, however many socket enchants change in between (a login applies dozens).
    struct RecountState : public DataMap::Base
    {
        bool pending = false;
    };
    constexpr char const* RecountStateKey = "CraftingGems.Recount";

    void RecalculateStanding(Player* player)
    {
        for (uint32 spellId : { SPELL_PURIST_A, SPELL_PURIST_B, SPELL_RELENTLESS })
        {
            Aura* aura = player->GetAura(spellId);
            if (!aura)
                continue;

            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if (AuraEffect* effect = aura->GetEffect(i))
                    effect->RecalculateAmount();
        }
    }

    void ScheduleRecount(Player* player)
    {
        RecountState* state = player->CustomData.GetDefault<RecountState>(RecountStateKey);
        if (state->pending)
            return;

        state->pending = true;
        player->m_Events.AddEventAtOffset([player]()
        {
            player->CustomData.GetDefault<RecountState>(RecountStateKey)->pending = false;
            if (player->IsInWorld())
                RecalculateStanding(player);
        }, 0ms);
    }
}

using namespace CraftingGems;

// Kaleidoscopic Azerothian Diamond (207150).
class spell_gem_kaleidoscope : public AuraScript
{
    PrepareAuraScript(spell_gem_kaleidoscope);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_KALEIDOSCOPE_BUFF_A, SPELL_KALEIDOSCOPE_BUFF_B });
    }

    // A cast rolls once (Systems section 5): the engine procs once per target hit, so a multi-target cast is let
    // through only for its first target. Triggered spells roll nothing.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo* damage = eventInfo.GetDamageInfo();
        HealInfo* heal = eventInfo.GetHealInfo();
        if (!(damage && damage->GetDamage()) && !(heal && heal->GetHeal()))
            return false;

        Spell const* spell = eventInfo.GetProcSpell();
        if (!spell)
            return true; // auto attack

        // Auto Shot and wand Shoot are autorepeat casts the engine sends fully triggered: they count as auto attacks.
        if (spell->IsTriggered() && !spell->GetSpellInfo()->IsAutoRepeatRangedSpell())
            return false;

        uint32 const now = GameTime::GetGameTimeMS().count();
        if (spell == _lastSpell && now - _lastSpellTime < 1000)
            return false;

        _lastSpell = spell;
        _lastSpellTime = now;
        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        GemCounts const counts = CountGems(player);
        int32 haste = int32(counts.Pure(SOCKET_COLOR_RED)) * KALEIDOSCOPE_RATING_PER_GEM;
        int32 crit = int32(counts.Pure(SOCKET_COLOR_YELLOW)) * KALEIDOSCOPE_RATING_PER_GEM;
        int32 mastery = int32(counts.Pure(SOCKET_COLOR_BLUE)) * KALEIDOSCOPE_RATING_PER_GEM;
        int32 versatility = int32(counts.Pure(COLOR_ORANGE)) * KALEIDOSCOPE_RATING_PER_GEM;
        int32 procChance = int32(counts.Pure(COLOR_GREEN)) * KALEIDOSCOPE_RATING_PER_GEM;
        int32 cooldownHaste = int32(counts.Pure(COLOR_PURPLE)) * KALEIDOSCOPE_RATING_PER_GEM;

        if (haste || crit || mastery)
            player->CastCustomSpell(player, SPELL_KALEIDOSCOPE_BUFF_A, &haste, &crit, &mastery, true, nullptr, aurEff);
        if (versatility || procChance || cooldownHaste)
            player->CastCustomSpell(player, SPELL_KALEIDOSCOPE_BUFF_B, &versatility, &procChance, &cooldownHaste,
                true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_gem_kaleidoscope::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_gem_kaleidoscope::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    Spell const* _lastSpell = nullptr;
    uint32 _lastSpellTime = 0;
};

// Purist's Azerothian Diamond (207153 Strength/Agility/Intellect, 207154 Spirit).
class spell_gem_purist : public AuraScript
{
    PrepareAuraScript(spell_gem_purist);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        amount = 0;
        if (Player* player = GetUnitOwner()->ToPlayer())
            amount = PuristPercent(CountGems(player));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_gem_purist::CalcAmount, EFFECT_ALL,
            SPELL_AURA_MOD_TOTAL_STAT_PERCENTAGE);
    }
};

// Relentless Azerothian Diamond (207155).
class spell_gem_relentless : public AuraScript
{
    PrepareAuraScript(spell_gem_relentless);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        amount = 0;
        if (Player* player = GetUnitOwner()->ToPlayer())
            amount = int32(CountGems(player).yellow);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_gem_relentless::CalcAmount, EFFECT_0,
            SPELL_AURA_MOD_CRIT_DAMAGE_BONUS);
    }
};

// Bulwark Azerothian Diamond (207156).
class spell_gem_bulwark : public AuraScript
{
    PrepareAuraScript(spell_gem_bulwark);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_BULWARK_SHIELD });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo* damage = eventInfo.GetDamageInfo();
        return damage && damage->GetDamage();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        int32 absorb = int32(CalculatePct(player->GetMaxHealth(),
            int32(CountGems(player).blue) * BULWARK_HEALTH_PCT_PER_GEM));
        if (absorb > 0)
            player->CastCustomSpell(player, SPELL_BULWARK_SHIELD, &absorb, nullptr, nullptr, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_gem_bulwark::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_gem_bulwark::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// Wellspring Azerothian Diamond (207158).
class spell_gem_wellspring : public AuraScript
{
    PrepareAuraScript(spell_gem_wellspring);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WELLSPRING_MANA });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo* heal = eventInfo.GetHealInfo();
        return heal && heal->GetHeal();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Player* player = GetTarget()->ToPlayer();
        if (!player || !player->GetMaxPower(POWER_MANA))
            return;

        int32 mana = int32(uint64(player->GetMaxPower(POWER_MANA)) * CountGems(player).blue *
            WELLSPRING_MANA_PERMILLE_PER_GEM / 1000);
        if (mana > 0)
            player->CastCustomSpell(player, SPELL_WELLSPRING_MANA, &mana, nullptr, nullptr, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_gem_wellspring::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_gem_wellspring::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

class Custom_CraftingGemsPlayer : public PlayerScript
{
public:
    Custom_CraftingGemsPlayer() : PlayerScript("Custom_CraftingGemsPlayer",
        { PLAYERHOOK_CAN_APPLY_ENCHANTMENT, PLAYERHOOK_ON_LOGIN }) { }

    bool OnPlayerCanApplyEnchantment(Player* player, Item* /*item*/, EnchantmentSlot slot, bool /*apply*/,
        bool /*apply_dur*/, bool /*ignore_condition*/) override
    {
        if (slot >= SOCK_ENCHANTMENT_SLOT && slot < SOCK_ENCHANTMENT_SLOT + MAX_GEM_SOCKETS)
            ScheduleRecount(player);
        return true;
    }

    void OnPlayerLogin(Player* player) override
    {
        ScheduleRecount(player);
    }
};

class Custom_CraftingGemsCommands : public CommandScript
{
public:
    Custom_CraftingGemsCommands() : CommandScript("Custom_CraftingGemsCommands") { }

    ChatCommandTable GetCommands() const override
    {
        static ChatCommandTable gemsCommandTable =
        {
            { "count", HandleCountCommand, SEC_GAMEMASTER, Console::No },
        };
        static ChatCommandTable commandTable =
        {
            { "gems", gemsCommandTable },
        };
        return commandTable;
    }

    // .gems count: the selected player's (or your own) gem counts and what each meta gem would give right now.
    static bool HandleCountCommand(ChatHandler* handler)
    {
        Player* player = handler->getSelectedPlayerOrSelf();
        if (!player)
            return false;

        GemCounts const counts = CountGems(player);
        handler->PSendSysMessage("Gems on {} (meta gem not counted):", player->GetName());
        handler->PSendSysMessage("  red {}, yellow {}, blue {} (hybrids count for both colors)", counts.red,
            counts.yellow, counts.blue);
        handler->PSendSysMessage("  pure red {}, pure yellow {}, pure blue {}, orange {}, purple {}, green {}",
            counts.Pure(SOCKET_COLOR_RED), counts.Pure(SOCKET_COLOR_YELLOW), counts.Pure(SOCKET_COLOR_BLUE),
            counts.Pure(COLOR_ORANGE), counts.Pure(COLOR_PURPLE), counts.Pure(COLOR_GREEN));
        handler->PSendSysMessage("  Kaleidoscopic: +{} Haste, +{} Crit, +{} Mastery, +{} Versatility, +{} Proc Chance, "
            "+{} Cooldown Haste rating for 15 sec",
            counts.Pure(SOCKET_COLOR_RED) * KALEIDOSCOPE_RATING_PER_GEM,
            counts.Pure(SOCKET_COLOR_YELLOW) * KALEIDOSCOPE_RATING_PER_GEM,
            counts.Pure(SOCKET_COLOR_BLUE) * KALEIDOSCOPE_RATING_PER_GEM,
            counts.Pure(COLOR_ORANGE) * KALEIDOSCOPE_RATING_PER_GEM,
            counts.Pure(COLOR_GREEN) * KALEIDOSCOPE_RATING_PER_GEM,
            counts.Pure(COLOR_PURPLE) * KALEIDOSCOPE_RATING_PER_GEM);
        handler->PSendSysMessage("  Purist's: +{}% primary stats; Relentless: +{}% crit damage", PuristPercent(counts),
            counts.yellow);
        handler->PSendSysMessage("  Bulwark: absorb {} ({}% max health); Wellspring: {} mana per proc",
            CalculatePct(player->GetMaxHealth(), int32(counts.blue) * BULWARK_HEALTH_PCT_PER_GEM),
            int32(counts.blue) * BULWARK_HEALTH_PCT_PER_GEM,
            uint64(player->GetMaxPower(POWER_MANA)) * counts.blue * WELLSPRING_MANA_PERMILLE_PER_GEM / 1000);

        for (uint32 spellId : { SPELL_PURIST_A, SPELL_PURIST_B, SPELL_RELENTLESS })
            if (Aura const* aura = player->GetAura(spellId))
                if (AuraEffect const* effect = aura->GetEffect(EFFECT_0))
                    handler->PSendSysMessage("  active aura {}: effect 0 amount {}", spellId, effect->GetAmount());

        return true;
    }
};

void AddSC_custom_crafting_gems()
{
    RegisterSpellScript(spell_gem_kaleidoscope);
    RegisterSpellScript(spell_gem_purist);
    RegisterSpellScript(spell_gem_relentless);
    RegisterSpellScript(spell_gem_bulwark);
    RegisterSpellScript(spell_gem_wellspring);
    new Custom_CraftingGemsPlayer();
    new Custom_CraftingGemsCommands();
}
