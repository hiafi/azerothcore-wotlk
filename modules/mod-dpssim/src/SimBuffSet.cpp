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
#include <algorithm>
#include <cstdlib>
#include <exception>
#include <iterator>
#include <limits>
#include <set>
#include <sstream>

namespace SimBuffSet
{
    // The 17 Inscription raid buff scrolls and Replenishment; the hunter pet family debuffs and Blood Frenzy
    char const* const DEFAULT_RAID_BUFFS =
        "208860, 208861, 208862, 208863, 208864, 208865, 208866, 208867, 208868, 208869, 208870, 208871, 208872, "
        "208873, 208874, 208875, 208876, 57669";
    char const* const DEFAULT_RAID_DEBUFFS = "201716, 201766, 201773, 201754, 201763, 201768, 30070";
    // Each id up to 31583 sits in the spell_group of the hunter pet family effect of its category (hunter-pet-families
    // DATA-INVENTORY 4.1), so that family's own cast adds nothing; the scrolls after it (Wild, Command, Brilliance,
    // Devotion, Battle) are the standard categories no pet family casts (raid-buff-sets retune, user ruling
    // 2026-11-26: full_raid is never weaker than standard for hunters). dpssim.conf.dist lists the values at level 60.
    char const* const DEFAULT_RAID_BUFFS_HUNTER =
        "24932, 57330:01, 53137, 202210:01, 24907:0, 50172, 25894, 208867, 23948, 25898:0, 202212, 31583:1, "
        "208861, 208863, 208864, 208865, 208868, 57669";
    char const* const DEFAULT_RAID_DEBUFFS_HUNTER = "8647, 21183:0@3, 60431, 1160, 6343, 1714:0, 30070";
    char const* const DEFAULT_RAID_PULL_BUFFS = "2825, 57724";
    // Flask of Might, Flask of Grace, Flask of Supreme Power (their target is the drinker, so the effect is explicit)
    char const* const DEFAULT_RAID_FLASKS = "208850:0, 208851:0, 17628:0";

    // standard (user rulings 2026-11-25, plan .agents/plans/raid-buff-sets/), every class, hunters too: Kings, Wild,
    // Fortitude, Command, Brilliance, Devotion, Winter's Horn, Stoneskin, Battle, Insight (spell crit), the Pack
    // (melee/ranged crit) and Flame (spell power); major armor and magic damage taken on the dummies. Left out on
    // purpose: attack power 10%, melee haste 10%, all haste 3%, damage 3%, crit taken 3%, physical taken 4%, mana
    // per 5, the minor debuffs, Replenishment and the flask.
    char const* const DEFAULT_STANDARD_BUFFS =
        "208860, 208861, 208862, 208863, 208864, 208865, 208866, 208867, 208868, 208872, 208873, 208874";
    char const* const DEFAULT_STANDARD_DEBUFFS = "201716, 201773";
    // Sated and Exhaustion, no Bloodlust: the actor's own Bloodlust or Heroism cannot be cast either
    char const* const DEFAULT_STANDARD_PULL_BUFFS = "57724, 57723";

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

        // How much weaker than the raid's an own aura may be and still count as at least as strong: the scrolls' fixed
        // amounts are rounded, so a Horn of Winter of 85 stands against the scroll's 86
        constexpr float OWN_AURA_TOLERANCE = 0.02f;

        bool Lists(std::vector<AuraSpec> const& specs, uint32 spellId)
        {
            return std::any_of(specs.begin(), specs.end(),
                [spellId](AuraSpec const& spec) { return spec.SpellId == spellId; });
        }

        // The amount `spec` would land with for an effect like this one (the same aura type, and the same stat for a
        // stat buff), 0 if it has none
        int32 SpecAmount(AuraSpec const& spec, SpellInfo const* info, Player* caster, AuraEffect const* like)
        {
            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if ((spec.EffectMask & (1 << i)) && info->Effects[i].ApplyAuraName == like->GetAuraType() &&
                    (like->GetAuraType() != SPELL_AURA_MOD_STAT || info->Effects[i].MiscValue == like->GetMiscValue()))
                    return spec.HasAmount ? spec.Amount : info->Effects[i].CalcValue(caster);

            return 0;
        }

        // OwnBuffWins: the spell of an aura on `target` that is not in the raid's lists, shares an "exclusive" or
        // "highest wins" group with `spec` and is at least as strong in every effect both have. 0 = none. Those are
        // the groups where a pinned raid aura would remove the own one and then block its recast; in a "same effect"
        // group both stay up and the highest counts.
        uint32 OwnGroupAura(Config const& config, AuraSpec const& spec, Player* caster, Unit const* target)
        {
            SpellInfo const* info = sSpellMgr->GetSpellInfo(spec.SpellId);
            for (auto const& [spellId, application] : target->GetAppliedAuras())
            {
                if (Lists(config.Buffs, spellId) || Lists(config.Debuffs, spellId))
                    continue;

                SpellGroupStackRule const rule =
                    sSpellMgr->CheckSpellGroupStackRules(info, application->GetBase()->GetSpellInfo());
                if (rule != SPELL_GROUP_STACK_RULE_EXCLUSIVE && rule != SPELL_GROUP_STACK_RULE_EXCLUSIVE_HIGHEST)
                    continue;

                bool shared = false;
                bool weaker = false;
                for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                    if (AuraEffect const* effect = application->GetBase()->GetEffect(i))
                        if (int32 const amount = SpecAmount(spec, info, caster, effect))
                        {
                            shared = true;
                            weaker = weaker || std::abs(effect->GetAmount()) * (1.0f + OWN_AURA_TOLERANCE) <
                                std::abs(amount);
                        }
                if (shared && !weaker)
                    return spellId;
            }

            return 0;
        }

        // A spell that only gives a power `target` does not have (Replenishment on a rogue)
        bool IsUselessPower(AuraSpec const& spec, SpellInfo const* info, Unit const* target)
        {
            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if (spec.EffectMask & (1 << i))
                {
                    if (info->Effects[i].ApplyAuraName != SPELL_AURA_PERIODIC_ENERGIZE)
                        return false;

                    int32 const power = info->Effects[i].MiscValue;
                    if (power < 0 || power >= int32(MAX_POWERS) || target->GetMaxPower(Powers(power)) > 0)
                        return false;
                }

            return true;
        }

        // Adds `spec` to `target` (the actor as the caster) unless it is already there. Returns true if it added it.
        // Initial: logs the amounts it landed with (when `logAmounts`) and every failure, with the group member that
        // is in the way. Refresh: counts what it put back and every failure into `refresh`.
        bool AddIfMissing(Config const& config, AuraSpec const& spec, Player* caster, Unit* target, bool pin,
            Phase phase, bool logAmounts, std::string const& who, RefreshLog* refresh)
        {
            if (!target || !target->IsAlive() || config.State.OwnKept.count({target->GetGUID(), spec.SpellId}))
                return false;

            if (target->HasAura(spec.SpellId))
            {
                // The actor's own proc of the same spell (Replenishment, Blood Frenzy) gives it back its duration
                if (pin)
                    if (Aura* own = target->GetAura(spec.SpellId, caster->GetGUID()))
                        if (own->GetOwner() == target && own->GetMaxDuration() != -1)
                            Pin(own);
                return false;
            }

            SpellInfo const* info = sSpellMgr->GetSpellInfo(spec.SpellId);
            if (IsUselessPower(spec, info, target))
                return false;

            // Immune on purpose (DpsSim.DummyImmuneAuras names the id): not added, and not retried every second
            if (target->IsImmunedToSpell(info))
            {
                if (phase == Phase::Initial)
                    LOG_INFO("server.dpssim", "mod-dpssim: buff set: {} {} skipped on the {}: it is immune to the "
                        "spell (DpsSim.DummyImmuneAuras, or its own immunity).", spec.SpellId, info->SpellName[0], who);
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
        switch (set)
        {
            case Set::Standard:
                return "standard";
            case Set::FullRaid:
                return "full_raid";
            default:
                return "self_only";
        }
    }

    bool ParseSet(std::string const& text, Set& out, std::string& error)
    {
        std::string const value = Trim(text);
        if (StringEqualI(value, "self_only") || StringEqualI(value, "self"))
            out = Set::SelfOnly;
        else if (StringEqualI(value, "standard"))
            out = Set::Standard;
        else if (StringEqualI(value, "full_raid") || StringEqualI(value, "all"))
            out = Set::FullRaid;
        else
        {
            error = Acore::StringFormat("'{}' is not self_only (self), standard or full_raid (all)", value);
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

    bool IsRaidScroll(uint32 spellId)
    {
        return spellId >= 208860 && spellId <= 208876;
    }

    uint32 DropRaidScrolls(std::vector<AuraSpec>& specs)
    {
        std::size_t const before = specs.size();
        specs.erase(std::remove_if(specs.begin(), specs.end(),
            [](AuraSpec const& spec) { return IsRaidScroll(spec.SpellId); }), specs.end());
        return uint32(before - specs.size());
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

    void BeginIteration(Config const& config, Player* actor, std::vector<Creature*> const& dummies)
    {
        if (!AddsAuras(config.BuffSet) || !actor)
            return;

        RunState& state = config.State;
        if (!state.FlaskPicked)
        {
            state.FlaskPicked = true;
            // The order of DpsSim.RaidFlasks. On a tie the earlier one.
            Stats const stats[] = {STAT_STRENGTH, STAT_AGILITY, STAT_INTELLECT};
            float highest = 0.0f;
            for (size_t i = 0; i < config.Flasks.size() && i < std::size(stats); ++i)
                if (actor->GetStat(stats[i]) > highest)
                {
                    highest = actor->GetStat(stats[i]);
                    state.FlaskId = config.Flasks[i].SpellId;
                }
            if (state.FlaskId)
                LOG_INFO("server.dpssim", "mod-dpssim: buff set: flask {} {} (Strength {:.0f}, Agility {:.0f}, "
                    "Intellect {:.0f}).", state.FlaskId, sSpellMgr->GetSpellInfo(state.FlaskId)->SpellName[0],
                    actor->GetStat(STAT_STRENGTH), actor->GetStat(STAT_AGILITY), actor->GetStat(STAT_INTELLECT));
        }

        state.OwnKept.clear();
        if (!config.OwnBuffWins)
            return;

        auto keepOwn = [&](std::vector<AuraSpec> const& specs, Unit* target, std::string const& who)
        {
            if (!target)
                return;

            for (AuraSpec const& spec : specs)
                if (uint32 const own = OwnGroupAura(config, spec, actor, target))
                {
                    state.OwnKept.insert({target->GetGUID(), spec.SpellId});
                    if (state.OwnKeptLogged.insert(spec.SpellId).second)
                        LOG_INFO("server.dpssim", "mod-dpssim: buff set: {} {} left out on the {}, its own {} {} is at "
                            "least as strong.", spec.SpellId, sSpellMgr->GetSpellInfo(spec.SpellId)->SpellName[0], who,
                            own, sSpellMgr->GetSpellInfo(own)->SpellName[0]);
                }
        };
        keepOwn(config.Buffs, actor, "actor");
        keepOwn(config.Buffs, actor->GetPet(), "pet");
        for (size_t i = 0; i < dummies.size(); ++i)
            keepOwn(config.Debuffs, dummies[i], Acore::StringFormat("dummy #{}", i));
    }

    uint32 ApplyPinned(Config const& config, Player* actor, std::vector<Creature*> const& dummies, Phase phase,
        RefreshLog* refresh)
    {
        if (!AddsAuras(config.BuffSet) || !actor)
            return 0;

        uint32 added = 0;
        Pet* pet = actor->GetPet();
        for (AuraSpec const& spec : config.Buffs)
        {
            // The actor first: an area aura it owns reaches the pet by itself, and then the pet needs nothing
            if (AddIfMissing(config, spec, actor, actor, true, phase, true, "actor", refresh))
                ++added;
            if (AddIfMissing(config, spec, actor, pet, true, phase, true, "pet", refresh))
                ++added;
        }

        // The actor only: a flask is its own
        for (AuraSpec const& spec : config.Flasks)
            if (spec.SpellId == config.State.FlaskId &&
                AddIfMissing(config, spec, actor, actor, true, phase, true, "actor", refresh))
                ++added;

        for (AuraSpec const& spec : config.Debuffs)
            for (size_t i = 0; i < dummies.size(); ++i)
                // Every dummy's failures are logged, the landed amounts of the first one only (the others are the
                // same spell on the same kind of creature)
                if (AddIfMissing(config, spec, actor, dummies[i], true, phase, i == 0,
                    Acore::StringFormat("dummy #{}", i), refresh))
                    ++added;

        return added;
    }

    void ApplyPullBuffs(Config const& config, Player* actor, Phase phase)
    {
        if (!AddsAuras(config.BuffSet) || !actor)
            return;

        for (AuraSpec const& spec : config.PullBuffs)
        {
            AddIfMissing(config, spec, actor, actor, false, phase, true, "actor", nullptr);
            AddIfMissing(config, spec, actor, actor->GetPet(), false, phase, true, "pet", nullptr);
        }
    }

    void LogCoverage(Config const& config, Player* actor, std::vector<Creature*> const& dummies)
    {
        if (!AddsAuras(config.BuffSet) || !actor)
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
            auto expected = [&](Unit const* unit)
            {
                return !config.State.OwnKept.count({unit->GetGUID(), spec.SpellId}) &&
                    !IsUselessPower(spec, sSpellMgr->GetSpellInfo(spec.SpellId), unit);
            };
            if (expected(actor) && !actor->HasAura(spec.SpellId))
                actorMissing.push_back(spec.SpellId);
            if (!pet || !expected(pet))
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
                if (!config.State.OwnKept.count({dummies[i]->GetGUID(), spec.SpellId}) &&
                    !dummies[i]->HasAura(spec.SpellId))
                    missing.push_back(spec.SpellId);
            LOG_INFO("server.dpssim", "mod-dpssim: buff set coverage, before the refresh: dummy #{} (entry {}) "
                "missing {}.", i, dummies[i]->GetEntry(), idList(missing));
        }
    }

    void LogRefresh(Set set, RefreshLog const& refresh)
    {
        uint32 putBack = 0;
        for (auto const& entry : refresh.PutBack)
            putBack += entry.second;
        if (putBack)
        {
            std::string text;
            for (auto const& [what, count] : refresh.PutBack)
                text += Acore::StringFormat("{}{} x{}", text.empty() ? "" : "; ", what, count);
            LOG_INFO("server.dpssim", "mod-dpssim: {} - {} raid aura(s) went missing during the iteration and "
                "were put back (a stronger aura of the same group that has since gone, a dispel, or the pet's own "
                "cast replacing one): {}.", SetName(set), putBack, text);
        }

        if (!refresh.Failed.empty())
        {
            std::string text;
            for (auto const& [what, count] : refresh.Failed)
                text += Acore::StringFormat("{}{} x{}", text.empty() ? "" : "; ", what, count);
            LOG_WARN("server.dpssim", "mod-dpssim: {} - raid aura(s) went missing and could not be put back "
                "(the DPS of that stretch counts the aura that blocked it, not the baseline): {}.", SetName(set), text);
        }
    }
}
