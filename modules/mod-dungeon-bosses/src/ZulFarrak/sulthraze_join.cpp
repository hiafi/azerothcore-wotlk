/*
 * mod-dungeon-bosses, Zul'Farrak: Call of Sul'thraze (213808), the Use on every tier of Jang'thraze (user ruling
 * 2026-11-25, option A): Jang'thraze and a Sang'thraze of the same tier join into the Sul'thraze of that tier; mixed
 * tiers are refused and nothing is used up. The spell is apps/dbc-tools/source/items/zul_farrak_effects.py (no reagent,
 * because the client would refuse the cast over a reagent of another tier), the tier rule SulthrazeJoinLogic.h.
 *
 * Who uses up what:
 *  - Jang'thraze: the engine, after the effects (Spell::handle_immediate, then Spell::TakeCastItem), by its Use slot's
 *    charges -1, as for the stock spell. TakeCastItem asks nobody whether the effect worked, so an effect that makes no
 *    sword takes the cast item off the spell first (the brewfest.cpp precedent) and Jang'thraze stays.
 *  - Sang'thraze: the effect, which looks everything up again and creates the sword in the same call. It runs on the
 *    hit phase without a target (Spell::_handle_immediate_phase), so an immune caster cannot lose the sword either.
 *
 * The other half counts where a stock reagent does: the backpack and bags first, then worn (when it can be unequipped),
 * never the bank, never an item in a trade window.
 */

#include "Bag.h"
#include "Chat.h"
#include "DatabaseEnv.h"
#include "Item.h"
#include "Log.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "SulthrazeJoinLogic.h"
#include "TradeData.h"
#include <vector>

using namespace ZulFarrakSulthraze;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    // Filled once at startup, read-only afterwards.
    JoinTable sJoinTable;

    void LoadJoinTable()
    {
        sJoinTable = JoinTable();
        if (QueryResult result = WorldDatabase.Query("SELECT entry, base_entry, tier FROM item_budget_variant "
            "WHERE base_entry IN ({}, {}, {})", kBaseBlades[0].entry, kBaseBlades[1].entry, kBaseBlades[2].entry))
        {
            do
            {
                Field* fields = result->Fetch();
                uint32 const entry = fields[0].Get<uint32>();
                uint32 const step = fields[2].Get<uint8>();
                if (!sObjectMgr->GetItemTemplate(entry) || !sJoinTable.AddVariant(entry, fields[1].Get<uint32>(), step))
                    LOG_ERROR(kLog, "zf-items sulthraze join: item_budget_variant entry {} (tier {}) is not usable",
                        entry, step);
            } while (result->NextRow());
        }
        LOG_INFO("server.loading", ">> Loaded {} Sul'thraze join tiers ({} swords)", sJoinTable.CompleteSteps(),
            sJoinTable.Size());
    }

    // Carried: worn, in the backpack or in a bag, not offered in an open trade window (Item::IsInTrade is only set
    // while a trade is being accepted) and not being disenchanted.
    bool IsCarried(Player* player, Item const* item)
    {
        if (!item || item->m_lootGenerated)
            return false;
        TradeData const* trade = player->GetTradeData();
        return !(trade && trade->HasItem(item->GetGUID()))
            && (item->IsEquipped() || Player::IsInventoryPos(item->GetBagSlot(), item->GetSlot()));
    }

    // Every carried item of the player that may be used up as the other half, in the order the stock reagent is taken:
    // backpack, bags, worn.
    std::vector<Item*> UsableItems(Player* player)
    {
        std::vector<Item*> items;
        auto add = [&items, player](Item* item)
        {
            if (IsCarried(player, item))
                items.push_back(item);
        };

        for (uint8 slot = INVENTORY_SLOT_ITEM_START; slot < INVENTORY_SLOT_ITEM_END; ++slot)
            add(player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot));
        for (uint8 bagSlot = INVENTORY_SLOT_BAG_START; bagSlot < INVENTORY_SLOT_BAG_END; ++bagSlot)
            if (Bag* bag = player->GetBagByPos(bagSlot))
                for (uint32 slot = 0; slot < bag->GetBagSize(); ++slot)
                    add(bag->GetItemByPos(slot));
        for (uint8 slot = EQUIPMENT_SLOT_START; slot < EQUIPMENT_SLOT_END; ++slot)
            if (Item* item = player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot))
                if (player->CanUnequipItem(item->GetPos(), false) == EQUIP_ERR_OK)
                    add(item);
        return items;
    }

    struct JoinPlan
    {
        Player* player = nullptr;
        JoinDecision decision;
        Item* sangthraze = nullptr;
        ItemPosCountVec dest;
        InventoryResult storeError = EQUIP_ERR_OK;

        bool Ready() const
        {
            return decision.verdict == JoinVerdict::Join && sangthraze && storeError == EQUIP_ERR_OK && !dest.empty();
        }
    };

    // Everything a join needs, looked up now. Refused (NotJangthraze) without a player, without a cast item (a learned
    // spell, a command, a script), with a cast item that is not carried any more, and for a triggered cast that would
    // leave the cast item alone.
    JoinPlan PlanJoin(Spell* spell)
    {
        JoinPlan plan;
        plan.player = spell->GetCaster() ? spell->GetCaster()->ToPlayer() : nullptr;
        Item* castItem = spell->m_CastItem;
        if (!plan.player || !castItem || spell->HasTriggeredCastFlag(TRIGGERED_IGNORE_CAST_ITEM)
            || plan.player->GetItemByGuid(castItem->GetGUID()) != castItem || !IsCarried(plan.player, castItem))
            return plan;

        std::vector<Item*> const items = UsableItems(plan.player);
        std::vector<uint32> entries;
        entries.reserve(items.size());
        for (Item const* item : items)
            entries.push_back(item->GetEntry());

        plan.decision = DecideJoin(sJoinTable, castItem->GetEntry(), entries);
        if (plan.decision.verdict != JoinVerdict::Join)
            return plan;

        for (Item* item : items)
            if (item->GetEntry() == plan.decision.sangthraze)
            {
                plan.sangthraze = item;
                break;
            }
        plan.storeError = plan.player->CanStoreNewItem(NULL_BAG, NULL_SLOT, plan.dest, plan.decision.sulthraze, 1);
        return plan;
    }

    // Tells the player why there is no join. SPELL_FAILED_REAGENTS would name the spell's reagent, and it has none.
    SpellCastResult Refuse(JoinPlan const& plan)
    {
        switch (plan.decision.verdict)
        {
            case JoinVerdict::MixedTiers:
                ChatHandler(plan.player->GetSession()).SendNotification("Jang'thraze and Sang'thraze must be of the "
                    "same tier: both Normal, both Heroic, or both of the same Empowered tier.");
                return SPELL_FAILED_DONT_REPORT;
            case JoinVerdict::NoSangthraze:
                ChatHandler(plan.player->GetSession()).SendNotification("You need a Sang'thraze the Deflector of the "
                    "same tier.");
                return SPELL_FAILED_DONT_REPORT;
            case JoinVerdict::Join:
                // As for a stock create item spell: no room, or a unique Sul'thraze of this tier already owned.
                plan.player->SendEquipError(plan.storeError == EQUIP_ERR_OK ? EQUIP_ERR_INVENTORY_FULL
                    : plan.storeError, nullptr, nullptr, plan.decision.sulthraze);
                return SPELL_FAILED_DONT_REPORT;
            case JoinVerdict::NoResult:
                LOG_ERROR(kLog, "zf-items sulthraze join: tier step {} has no Sul'thraze", plan.decision.step);
                return SPELL_FAILED_ITEM_NOT_FOUND;
            case JoinVerdict::NotJangthraze:
                break;
        }
        return SPELL_FAILED_ITEM_NOT_FOUND;
    }
}

// 213808 - Call of Sul'thraze
class spell_zf_call_of_sulthraze : public SpellScript
{
    PrepareSpellScript(spell_zf_call_of_sulthraze);

    // At the press and again when the bar ends.
    SpellCastResult CheckJoin()
    {
        JoinPlan const plan = PlanJoin(GetSpell());
        return plan.Ready() ? SPELL_CAST_OK : Refuse(plan);
    }

    void HandleJoin(SpellEffIndex /*effIndex*/)
    {
        Spell* spell = GetSpell();
        JoinPlan const plan = PlanJoin(spell);
        if (!plan.Ready())
        {
            KeepCastItem(spell);
            Refuse(plan);
            return;
        }

        Player* player = plan.player;
        Item const* jangthraze = spell->m_CastItem;
        ObjectGuid const otherGuid = plan.sangthraze->GetGUID();

        player->DestroyItem(plan.sangthraze->GetBagSlot(), plan.sangthraze->GetSlot(), true);
        Item* sword = player->StoreNewItem(plan.dest, plan.decision.sulthraze, true);
        if (!sword)
        {
            // Only an item entry without a template ends here, and CanStoreNewItem refused that above.
            KeepCastItem(spell);
            LOG_ERROR(kLog, "zf-items sulthraze join: player {} lost Sang'thraze {} and item {} was not created",
                player->GetGUID().ToString(), otherGuid.ToString(), plan.decision.sulthraze);
            return;
        }
        if (sword->GetTemplate()->HasSignature())
            sword->SetGuidValue(ITEM_FIELD_CREATOR, player->GetGUID());
        player->SendNewItem(sword, 1, true, true);
        sScriptMgr->OnPlayerCreateItem(player, sword, 1);

        LOG_INFO(kLog, "zf-items sulthraze join: player {} ({}) tier step {}: {} (entry {}) + {} (entry {}) -> {} "
            "(entry {})", player->GetName(), player->GetGUID().ToString(), plan.decision.step,
            jangthraze->GetGUID().ToString(), jangthraze->GetEntry(), otherGuid.ToString(), plan.decision.sangthraze,
            sword->GetGUID().ToString(), sword->GetEntry());
    }

    // Spell::TakeCastItem does nothing without a cast item.
    static void KeepCastItem(Spell* spell)
    {
        spell->m_CastItem = nullptr;
        spell->m_castItemGUID.Clear();
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_zf_call_of_sulthraze::CheckJoin);
        OnEffectHit += SpellEffectFn(spell_zf_call_of_sulthraze::HandleJoin, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

class SulthrazeJoinWorldScript : public WorldScript
{
public:
    SulthrazeJoinWorldScript() : WorldScript("SulthrazeJoinWorldScript", { WORLDHOOK_ON_STARTUP }) { }

    void OnStartup() override
    {
        LoadJoinTable();    // after the item templates
    }
};

void AddSC_zf_sulthraze_join()
{
    RegisterSpellScript(spell_zf_call_of_sulthraze);
    new SulthrazeJoinWorldScript();
}
