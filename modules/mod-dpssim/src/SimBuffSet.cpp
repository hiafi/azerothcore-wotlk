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
#include <set>
#include <sstream>

namespace SimBuffSet
{
    // Each id sits in the spell_group of the hunter pet family effect of its category (hunter-pet-families
    // DATA-INVENTORY 4.1), so that family's own cast adds nothing; dpssim.conf.dist lists the values at level 60.
    char const* const DEFAULT_RAID_BUFFS =
        "24932, 8076:01, 53137, 202210:01, 24907:0, 50172, 5677, 202211, 23948, 25898:0, 202212, 31583:1";
    char const* const DEFAULT_RAID_DEBUFFS = "8647, 21183:0@3, 60431, 1160, 6343, 1714:0, 30070";
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

        // The spell of `target`'s auras that shares a spell group with `info`, so the one that blocks (or has just
        // been replaced by) `info`: 0 when none does. The groups are those of the first ranks, as the core stacks them.
        uint32 GroupBlocker(Unit const* target, SpellInfo const* info)
        {
            std::set<uint32> groups;
            SpellSpellGroupMapBounds const mine = sSpellMgr->GetSpellSpellGroupMapBounds(info->GetFirstRankSpell()->Id);
            for (auto itr = mine.first; itr != mine.second; ++itr)
                groups.insert(uint32(itr->second));

            for (auto const& [spellId, application] : target->GetAppliedAuras())
            {
                if (spellId == info->Id)
                    continue;

                SpellInfo const* other = application->GetBase()->GetSpellInfo();
                SpellSpellGroupMapBounds const theirs =
                    sSpellMgr->GetSpellSpellGroupMapBounds(other->GetFirstRankSpell()->Id);
                for (auto itr = theirs.first; itr != theirs.second; ++itr)
                    if (groups.count(uint32(itr->second)))
                        return spellId;
            }

            return 0;
        }

        // Adds `spec` to `target` (the actor as the caster) unless it is already there. Returns true if it added it.
        // Initial: logs the amounts it landed with (when `logAmounts`) and every failure, with the group member that
        // is in the way. Refresh: counts what it put back and every failure into `refresh`.
        bool AddIfMissing(AuraSpec const& spec, Player* caster, Unit* target, bool pin, Phase phase, bool logAmounts,
            std::string const& who, RefreshLog* refresh)
        {
            if (!target || !target->IsAlive() || target->HasAura(spec.SpellId))
                return false;

            SpellInfo const* info = sSpellMgr->GetSpellInfo(spec.SpellId);
            // Immune on purpose (DpsSim.DummyImmuneAuras names the id): not added, and not retried every second
            if (target->IsImmunedToSpell(info))
            {
                if (phase == Phase::Initial)
                    LOG_INFO("server.dpssim", "mod-dpssim: buff set: {} {} skipped on the {}: it is immune to the "
                        "spell (DpsSim.DummyImmuneAuras).", spec.SpellId, info->SpellName[0], who);
                return false;
            }

            Aura* aura = caster->AddAura(info, spec.EffectMask, target);
            if (!aura || aura->IsRemoved())
            {
                uint32 const blocker = GroupBlocker(target, info);
                std::string const reason = blocker ? Acore::StringFormat("blocked by spell {} of its group", blocker) :
                    std::string("immune, or nothing of its group is up");
                if (phase == Phase::Initial)
                    LOG_WARN("server.dpssim", "mod-dpssim: buff set: {} {} did not land on the {} ({}).", spec.SpellId,
                        info->SpellName[0], who, reason);
                else if (refresh)
                    ++refresh->Failed[Acore::StringFormat("{} {} on the {}: {}", spec.SpellId, info->SpellName[0], who,
                        reason)];
                return false;
            }

            if (spec.HasAmount)
                for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                    if (AuraEffect* effect = aura->GetEffect(i))
                    {
                        effect->SetCanBeRecalculated(false);
                        effect->ChangeAmount(spec.Amount);
                    }

            if (pin)
                Pin(aura);
            if (phase == Phase::Initial && logAmounts)
                LOG_INFO("server.dpssim", "mod-dpssim: buff set: {} {} on the {}: {}.", spec.SpellId,
                    info->SpellName[0], who, Amounts(aura));
            else if (phase == Phase::Refresh && refresh)
                ++refresh->PutBack[Acore::StringFormat("{} {} on the {}", spec.SpellId, info->SpellName[0], who)];
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

            size_t const at = entry.find('@');
            std::string const amountText = at == std::string::npos ? std::string() : Trim(entry.substr(at + 1));
            std::string const head = entry.substr(0, at);
            size_t const colon = head.find(':');
            std::string const idText = Trim(head.substr(0, colon));
            std::string const effectsText = colon == std::string::npos ? std::string() : Trim(head.substr(colon + 1));

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

            if (at != std::string::npos)
            {
                // "-3" or "3": an optional minus and digits, nothing after them, and a value an int32 holds
                bool amountValid = false;
                size_t const digitsFrom = amountText.empty() || amountText[0] != '-' ? 0 : 1;
                if (digitsFrom < amountText.size() &&
                    amountText.find_first_not_of("0123456789", digitsFrom) == std::string::npos)
                {
                    try
                    {
                        size_t used = 0;
                        long long const value = std::stoll(amountText, &used);
                        amountValid = used == amountText.size() && value >= std::numeric_limits<int32>::min() &&
                            value <= std::numeric_limits<int32>::max();
                        spec.Amount = int32(value);
                    }
                    catch (std::exception const&)
                    {
                        amountValid = false;
                    }
                }

                if (!amountValid)
                {
                    error = Acore::StringFormat("'{}': the amount after '@' must be a whole number (int32)", entry);
                    return false;
                }

                spec.HasAmount = true;
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

            text += Acore::StringFormat("{}{} {} [effects {}{}; groups {}]", text.empty() ? "" : "; ", spec.SpellId,
                info ? info->SpellName[0] : "?", EffectList(spec.EffectMask),
                spec.HasAmount ? Acore::StringFormat("; amount {}", spec.Amount) : std::string(),
                groups.empty() ? "none" : groups);
        }

        return text.empty() ? "none" : text;
    }

    uint32 ApplyPinned(Config const& config, Player* actor, std::vector<Creature*> const& dummies, Phase phase,
        RefreshLog* refresh)
    {
        if (config.BuffSet != Set::FullRaid || !actor)
            return 0;

        uint32 added = 0;
        Pet* pet = actor->GetPet();
        for (AuraSpec const& spec : config.Buffs)
        {
            // The actor first: an area aura it owns reaches the pet by itself, and then the pet needs nothing
            if (AddIfMissing(spec, actor, actor, true, phase, true, "actor", refresh))
                ++added;
            if (AddIfMissing(spec, actor, pet, true, phase, true, "pet", refresh))
                ++added;
        }

        for (AuraSpec const& spec : config.Debuffs)
            for (size_t i = 0; i < dummies.size(); ++i)
                // Every dummy's failures are logged, the landed amounts of the first one only (the others are the
                // same spell on the same kind of creature)
                if (AddIfMissing(spec, actor, dummies[i], true, phase, i == 0,
                    Acore::StringFormat("dummy #{}", i), refresh))
                    ++added;

        return added;
    }

    void ApplyPullBuffs(Config const& config, Player* actor, Phase phase)
    {
        if (config.BuffSet != Set::FullRaid || !actor)
            return;

        for (AuraSpec const& spec : config.PullBuffs)
        {
            AddIfMissing(spec, actor, actor, false, phase, true, "actor", nullptr);
            AddIfMissing(spec, actor, actor->GetPet(), false, phase, true, "pet", nullptr);
        }
    }

    void LogCoverage(Config const& config, Player* actor, std::vector<Creature*> const& dummies)
    {
        if (config.BuffSet != Set::FullRaid || !actor)
            return;

        auto idList = [](std::vector<uint32> const& ids)
        {
            std::string text;
            for (uint32 id : ids)
                text += (text.empty() ? "" : ",") + std::to_string(id);
            return text.empty() ? std::string("none") : text;
        };

        std::vector<uint32> actorMissing;
        std::vector<uint32> petMissing;
        std::vector<uint32> petPropagated;
        std::vector<uint32> petOwn;
        Pet* pet = actor->GetPet();
        for (AuraSpec const& spec : config.Buffs)
        {
            if (!actor->HasAura(spec.SpellId))
                actorMissing.push_back(spec.SpellId);
            if (!pet)
                continue;

            if (Aura* aura = pet->GetAura(spec.SpellId))
                (aura->GetOwner() == actor ? petPropagated : petOwn).push_back(spec.SpellId);
            else
                petMissing.push_back(spec.SpellId);
        }

        LOG_INFO("server.dpssim", "mod-dpssim: buff set coverage, before the refresh: actor missing {}; "
            "{}", idList(actorMissing), pet ? Acore::StringFormat("pet: missing {}; carried by the actor's own aura "
            "(area aura propagated to it) {}; its own copy (added directly) {}.", idList(petMissing),
            idList(petPropagated), idList(petOwn)) : std::string("no pet."));

        for (size_t i = 0; i < dummies.size(); ++i)
        {
            std::vector<uint32> missing;
            for (AuraSpec const& spec : config.Debuffs)
                if (!dummies[i]->HasAura(spec.SpellId))
                    missing.push_back(spec.SpellId);
            LOG_INFO("server.dpssim", "mod-dpssim: buff set coverage, before the refresh: dummy #{} (entry {}) "
                "missing {}.", i, dummies[i]->GetEntry(), idList(missing));
        }
    }

    void LogRefresh(RefreshLog const& refresh)
    {
        uint32 putBack = 0;
        for (auto const& entry : refresh.PutBack)
            putBack += entry.second;
        if (putBack)
        {
            std::string text;
            for (auto const& [what, count] : refresh.PutBack)
                text += Acore::StringFormat("{}{} x{}", text.empty() ? "" : "; ", what, count);
            LOG_INFO("server.dpssim", "mod-dpssim: full_raid - {} raid aura(s) went missing during the iteration and "
                "were put back (a stronger aura of the same group that has since gone, a dispel, or the pet's own "
                "cast replacing one): {}.", putBack, text);
        }

        if (!refresh.Failed.empty())
        {
            std::string text;
            for (auto const& [what, count] : refresh.Failed)
                text += Acore::StringFormat("{}{} x{}", text.empty() ? "" : "; ", what, count);
            LOG_WARN("server.dpssim", "mod-dpssim: full_raid - raid aura(s) went missing and could not be put back "
                "(the DPS of that stretch counts the aura that blocked it, not the baseline): {}.", text);
        }
    }
}
