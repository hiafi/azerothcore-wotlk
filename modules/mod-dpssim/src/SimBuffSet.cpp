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

#include "SimBuffSet.h"
#include "Creature.h"
#include "Log.h"
#include "Pet.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "Util.h"
#include <exception>
#include <limits>
#include <sstream>

namespace SimBuffSet
{
    // Each id sits in the spell_group of the hunter pet family effect of its category (hunter-pet-families
    // DATA-INVENTORY 4.1), so that family's own cast adds nothing; dpssim.conf.dist lists the values at level 60.
    char const* const DEFAULT_RAID_BUFFS =
        "24932, 8076:01, 53137, 202210:01, 24907:0, 50172, 5677, 202211, 23948, 25898:0, 202212, 31583:1";
    char const* const DEFAULT_RAID_DEBUFFS = "8647, 54499, 60431, 1160, 6343, 11719:0, 30070";
    char const* const DEFAULT_RAID_PULL_BUFFS = "2825, 57724";

    namespace
    {
        std::string Trim(std::string const& text)
        {
            size_t const first = text.find_first_not_of(" \t");
            if (first == std::string::npos)
                return std::string();
            return text.substr(first, text.find_last_not_of(" \t") - first + 1);
        }

        std::string EffectList(uint8 mask)
        {
            std::string list;
            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if (mask & (1 << i))
                    list += (list.empty() ? "" : ",") + std::to_string(i);
            return list;
        }

        // Pinned: no expiry for the rest of the iteration (the iteration reset removes it, as every non-passive aura)
        void Pin(Aura* aura)
        {
            if (!aura || aura->IsRemoved())
                return;

            aura->SetMaxDuration(-1);
            aura->SetDuration(-1);
        }

        // The amounts the aura landed with, "52:5 189:0", for the first application's log line
        std::string Amounts(Aura const* aura)
        {
            std::string text;
            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if (AuraEffect const* effect = aura->GetEffect(i))
                    text += Acore::StringFormat("{}aura {} = {}", text.empty() ? "" : ", ",
                        uint32(effect->GetAuraType()), effect->GetAmount());
            return text;
        }

        // Adds `spec` to `target` (the actor as the caster) unless it is already there. Returns true if it added it.
        bool AddIfMissing(AuraSpec const& spec, Player* caster, Unit* target, bool pin, bool initial, char const* who)
        {
            if (!target || !target->IsAlive() || target->HasAura(spec.SpellId))
                return false;

            SpellInfo const* info = sSpellMgr->GetSpellInfo(spec.SpellId);
            Aura* aura = caster->AddAura(info, spec.EffectMask, target);
            if (!aura || aura->IsRemoved())
            {
                if (initial)
                    LOG_WARN("server.dpssim", "mod-dpssim: buff set: {} {} did not land on the {} (immune, or a "
                        "stronger aura of its spell group is up).", spec.SpellId, info->SpellName[0], who);
                return false;
            }

            if (pin)
                Pin(aura);
            if (initial)
                LOG_INFO("server.dpssim", "mod-dpssim: buff set: {} {} on the {}: {}.", spec.SpellId,
                    info->SpellName[0], who, Amounts(aura));
            return true;
        }
    }

    char const* SetName(Set set)
    {
        return set == Set::FullRaid ? "full_raid" : "self_only";
    }

    bool ParseSet(std::string const& text, Set& out, std::string& error)
    {
        std::string const value = Trim(text);
        if (StringEqualI(value, "self_only"))
            out = Set::SelfOnly;
        else if (StringEqualI(value, "full_raid"))
            out = Set::FullRaid;
        else
        {
            error = Acore::StringFormat("'{}' is not self_only or full_raid", value);
            return false;
        }

        return true;
    }

    bool ParseAuraList(std::string const& text, std::vector<AuraSpec>& out, std::string& error)
    {
        out.clear();
        std::istringstream entries(text);
        std::string entry;
        while (std::getline(entries, entry, ','))
        {
            entry = Trim(entry);
            if (entry.empty())
                continue;

            size_t const colon = entry.find(':');
            std::string const idText = Trim(entry.substr(0, colon));
            std::string const effectsText = colon == std::string::npos ? std::string() : Trim(entry.substr(colon + 1));

            AuraSpec spec;
            unsigned long id = 0;
            bool valid = !idText.empty() && idText.find_first_not_of("0123456789") == std::string::npos;
            if (valid)
            {
                try
                {
                    id = std::stoul(idText);
                }
                catch (std::exception const&)
                {
                    valid = false;
                }
            }
            if (!valid || id == 0 || id > std::numeric_limits<uint32>::max())
            {
                error = Acore::StringFormat("'{}' is not a spell id", entry);
                return false;
            }
            spec.SpellId = uint32(id);

            if (colon != std::string::npos)
            {
                if (effectsText.empty() || effectsText.find_first_not_of("012") != std::string::npos)
                {
                    error = Acore::StringFormat("'{}': the effects after ':' must be indexes 0-2, e.g. 202210:01",
                        entry);
                    return false;
                }

                for (char c : effectsText)
                    spec.EffectMask |= uint8(1 << (c - '0'));
            }

            out.push_back(spec);
        }

        return true;
    }

    uint8 ResolveEffectMask(uint32 spellId)
    {
        SpellInfo const* info = sSpellMgr->GetSpellInfo(spellId);
        if (!info)
            return 0;

        uint8 mask = 0;
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            SpellEffectInfo const& effect = info->Effects[i];
            if (!effect.IsAura())
                continue;

            // A plain aura on the caster is the caster's own perk, not something a raid member gets
            if (effect.Effect == SPELL_EFFECT_APPLY_AURA && effect.TargetA.GetTarget() == TARGET_UNIT_CASTER)
                continue;

            mask |= uint8(1 << i);
        }

        return mask;
    }

    bool Validate(std::vector<AuraSpec>& specs, std::string& error)
    {
        for (AuraSpec& spec : specs)
        {
            SpellInfo const* info = sSpellMgr->GetSpellInfo(spec.SpellId);
            if (!info)
            {
                error = Acore::StringFormat("spell {} does not exist", spec.SpellId);
                return false;
            }

            if (spec.EffectMask == 0)
            {
                spec.EffectMask = ResolveEffectMask(spec.SpellId);
                if (spec.EffectMask == 0)
                {
                    error = Acore::StringFormat("spell {} {} has no aura effect a raid member would get",
                        spec.SpellId, info->SpellName[0]);
                    return false;
                }
            }
            else
                for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                    if ((spec.EffectMask & (1 << i)) && !info->Effects[i].IsAura())
                    {
                        error = Acore::StringFormat("spell {} {}: effect {} is not an aura", spec.SpellId,
                            info->SpellName[0], i);
                        return false;
                    }
        }

        return true;
    }

    std::string Describe(std::vector<AuraSpec> const& specs)
    {
        std::string text;
        for (AuraSpec const& spec : specs)
        {
            SpellInfo const* info = sSpellMgr->GetSpellInfo(spec.SpellId);
            std::string groups;
            if (info)
            {
                // The groups the core stacks it by (the first rank's, as Unit and Aura look them up)
                SpellSpellGroupMapBounds const bounds =
                    sSpellMgr->GetSpellSpellGroupMapBounds(info->GetFirstRankSpell()->Id);
                for (auto itr = bounds.first; itr != bounds.second; ++itr)
                    groups += (groups.empty() ? "" : ",") + std::to_string(uint32(itr->second));
            }

            text += Acore::StringFormat("{}{} {} [effects {}; groups {}]", text.empty() ? "" : "; ", spec.SpellId,
                info ? info->SpellName[0] : "?", EffectList(spec.EffectMask), groups.empty() ? "none" : groups);
        }

        return text.empty() ? "none" : text;
    }

    uint32 ApplyPinned(Config const& config, Player* actor, std::vector<Creature*> const& dummies, bool initial)
    {
        if (config.BuffSet != Set::FullRaid || !actor)
            return 0;

        uint32 added = 0;
        Pet* pet = actor->GetPet();
        for (AuraSpec const& spec : config.Buffs)
        {
            // The actor first: an area aura it owns reaches the pet by itself, and then the pet needs nothing
            if (AddIfMissing(spec, actor, actor, true, initial, "actor"))
                ++added;
            if (AddIfMissing(spec, actor, pet, true, initial, "pet"))
                ++added;
        }

        for (AuraSpec const& spec : config.Debuffs)
            for (Creature* dummy : dummies)
                if (AddIfMissing(spec, actor, dummy, true, initial && dummy == dummies.front(), "dummy"))
                    ++added;

        return added;
    }

    void ApplyPullBuffs(Config const& config, Player* actor)
    {
        if (config.BuffSet != Set::FullRaid || !actor)
            return;

        for (AuraSpec const& spec : config.PullBuffs)
        {
            AddIfMissing(spec, actor, actor, false, false, "actor");
            AddIfMissing(spec, actor, actor->GetPet(), false, false, "pet");
        }
    }
}
