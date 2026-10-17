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
 * Hunter rework - Marksmanship spell scripts (hunter-rework.SHARED.md §A4 / §C4, MARKSMANSHIP.md §4-§8, §10.3,
 * S2a-HANDOFF A2, A5, A7, A8, A10, A12, A13, A15-A17). Ids come from HunterData:: (long names where a short stem
 * lost, L11) and the Hunter:: MM section of HunterMechanics.h; stock ids the hunter DSL never declares stay named
 * constants below. Every per-cast value (marks read, helper amounts) lives in the SpellScript instance (M14).
 */

#include "HunterMechanics.h"
#include "CellImpl.h"
#include "DynamicObject.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Log.h"
#include "ObjectGuid.h"
#include "Player.h"
#include "Position.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <initializer_list>
#include <list>
#include <vector>

namespace
{
    // Stock ids the hunter DSL never declares (no HunterData:: name)
    constexpr uint32 SPELL_PIERCING_SHOTS_BLEED = 63468;    // stock Piercing Shots bleed (spell_hunter.cpp's
                                                            // SPELL_HUNTER_PIERCING_SHOTS; S2a brief resolution 4)

    // _masks.py MARK_PRESS: d2 b27, the three mark presses (Precision's capstone ignores them, MARKSMANSHIP §8)
    constexpr uint32 FAMILY_FLAG2_MARK_PRESS = 0x8000000;

    // Stock Chimera Shot's Serpent burst: 40% of the sting's total damage (spell_hun_chimera_shot); the DSL const
    // is the one home, 53209's tooltip interpolates it (MARKSMANSHIP §5.6)
    constexpr int32 CHIMERA_SERPENT_BURST_PCT = HunterData::CHIMERA_SERPENT_BURST_PCT;

    // Precision 3/3: one Sniper's Mark stack per crit on a Sniper-marked target (MARKSMANSHIP §8)
    constexpr uint8 PRECISION_SNIPER_GAIN = 1;

    // The hunter Player behind a spell's caster (CR3), nullptr otherwise
    Player* GetHunterPlayer(Unit* unit)
    {
        Player* player = unit ? unit->ToPlayer() : nullptr;
        return player && player->getClass() == CLASS_HUNTER ? player : nullptr;
    }

    // The rank of `ranks` (listed highest first) that `player` knows, else 0. Every MM rank is a passive with aura
    // effects, so ownership is HasAura (L10).
    uint32 GetKnownRank(Player const* player, std::initializer_list<uint32> ranks)
    {
        for (uint32 rank : ranks)
            if (player->HasAura(rank))
                return rank;

        return 0;
    }

    // The spell's per-target record for `guid` (missCondition and crit, set at launch), nullptr when there is none.
    // Spell::GetUniqueTargetInfo() is public (Spell.h); the pointer is only used inside the calling hook.
    TargetInfo const* FindTargetInfo(Spell* spell, ObjectGuid const& guid)
    {
        if (!spell || guid.IsEmpty())
            return nullptr;

        for (TargetInfo const& info : *spell->GetUniqueTargetInfo())
            if (info.targetGUID == guid)
                return &info;

        return nullptr;
    }

    // True when the unit hit right now is `spell`'s target, landed (SPELL_MISS_NONE) and crit
    bool IsCritHit(Spell* spell, Unit const* target)
    {
        if (!target)
            return false;

        TargetInfo const* info = FindTargetInfo(spell, target->GetGUID());
        return info && info->missCondition == SPELL_MISS_NONE && info->crit;
    }

    // ---- S2b ----
    constexpr std::array<Hunter::Mark, 3> MM_MARKS =
        { Hunter::Mark::Sniper, Hunter::Mark::Viper, Hunter::Mark::Falcon };

    // Convergence (MARKSMANSHIP §5.10, S2a deviation 2): 201932's eff1 carries the centre's full potency (the DSL
    // allows one direct AP potency per spell), so the splash hits are scaled here; the DSL consts are the one home.
    constexpr int32 CONVERGENCE_SPLASH_PCT = HunterData::CONVERGENCE_SPLASH_PCT;
    constexpr uint8 CONVERGENCE_MAX_TARGETS = HunterData::CONVERGENCE_MAX_TARGETS;

    bool HasAnyMark(Player const* player, Unit const* target)
    {
        for (Hunter::Mark mark : MM_MARKS)
            if (Hunter::HasMark(player, target, mark))
                return true;

        return false;
    }

    // The Aimed Shot pack search (§5.2 steps 7-8, S2b B3): alive, attackable enemies within `radius` of `origin`
    // (the primary; its corpse on a killing blow, the same tick), in combat with the hunter himself (not "or pet":
    // the BM §0.4 filter of Hunter::CollectBmSplashTargets doesn't apply), never `origin`, never in `exclude`,
    // holding at least one of the hunter's marks when `requireMark`; nearest to `origin` first, at most `maxTargets`.
    // Local on purpose (no new Hunter:: signature).
    void CollectPackTargets(Player* player, Unit* origin, float radius, uint32 maxTargets, bool requireMark,
        GuidSet const& exclude, std::vector<Unit*>& out)
    {
        if (!player || !origin || !maxTargets)
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(origin, player, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(origin, nearby, check);
        Cell::VisitObjects(origin, searcher, radius);

        std::vector<Unit*> candidates;
        for (Unit* unit : nearby)
        {
            if (unit == origin || !unit->IsAlive() || exclude.count(unit->GetGUID()))
                continue;

            if (!player->IsValidAttackTarget(unit) || !unit->IsInCombatWith(player))
                continue;

            if (requireMark && !HasAnyMark(player, unit))
                continue;

            candidates.push_back(unit);
        }

        std::sort(candidates.begin(), candidates.end(), [origin](Unit const* a, Unit const* b)
        {
            return origin->GetExactDistSq(a) < origin->GetExactDistSq(b);
        });

        if (candidates.size() > maxTargets)
            candidates.resize(maxTargets);

        out.insert(out.end(), candidates.begin(), candidates.end());
    }
}

// 201920 Sniper's Mark, 201921 Viper's Mark, 201922 Falcon's Mark - the re-press (MARKSMANSHIP §4.2, S2a A2). A
// refresh is not a REAL apply, so the SpellScript half resets the counter of a mark that was already up.
class spell_hun_mark : public SpellScript
{
    PrepareSpellScript(spell_hun_mark);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_SNIPERS_MARK, HunterData::SPELL_VIPERS_MARK,
            HunterData::SPELL_FALCONS_MARK, HunterData::SPELL_FALCONS_HASTE });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    // Spell.cpp DoAllEffectOnTarget: before DoSpellHitOnUnit refreshes the aura
    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        _hadMark = false;
        if (missInfo != SPELL_MISS_NONE)
            return;

        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        _hadMark = target->HasAura(GetSpellInfo()->Id, caster->GetGUID());
    }

    // Hit only. The refresh went through ModStackAmount(+1), so the visible stack is one too high; the stack write
    // puts it back to max(1, 0) inside the inStackWrite guard (M13)
    void HandleAfterHit()
    {
        if (!_hadMark)
            return;

        _hadMark = false;

        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        Hunter::Mark mark = Hunter::Mark::Max;
        if (!player || !target || !Hunter::GetMarkForSpell(GetSpellInfo()->Id, mark))
            return;

        Hunter::SetMarkStacks(player, target, mark, 0);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_hun_mark::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_hun_mark::HandleAfterHit);
    }

private:
    bool _hadMark = false;
};

// 201920-201922 - the mark aura's state (MARKSMANSHIP §4.2). REAL only, never REAL_OR_REAPPLY: every
// Aura::SetStackAmount re-runs the effect handlers with REAPPLY | CHANGE_AMOUNT (SpellAuras.cpp:1028-1052,
// SpellAuraEffects.cpp:736-766), so a REAPPLY hook would recurse on the first stack write and reset every gain (M13).
// Every mark's eff2 is the APPLY_AURA DUMMY (bp -1).
class spell_hun_mark_aura : public AuraScript
{
    PrepareAuraScript(spell_hun_mark_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_SNIPERS_MARK, HunterData::SPELL_VIPERS_MARK,
            HunterData::SPELL_FALCONS_MARK, HunterData::SPELL_FALCONS_HASTE });
    }

    // CR3 by GUID: a mark loaded from the DB with its caster offline still loads (the hooks resolve the caster)
    bool Load() override
    {
        return GetCasterGUID().IsPlayer();
    }

    bool GetContext(Player*& player, Unit*& target, Hunter::Mark& mark) const
    {
        player = GetHunterPlayer(GetCaster());
        target = GetTarget();
        return player && target && Hunter::GetMarkForSpell(GetId(), mark);
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = nullptr;
        Unit* target = nullptr;
        Hunter::Mark mark = Hunter::Mark::Max;
        if (GetContext(player, target, mark))
            Hunter::OnMarkApplied(player, target, mark);
    }

    // A caster that left the map resolves to nullptr here; its entry lingers until logout, and every read checks the
    // aura first (R5)
    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = nullptr;
        Unit* target = nullptr;
        Hunter::Mark mark = Hunter::Mark::Max;
        if (GetContext(player, target, mark))
            Hunter::OnMarkRemoved(player, target, mark);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_hun_mark_aura::HandleApply, EFFECT_2, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_hun_mark_aura::HandleRemove, EFFECT_2, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// 19434 Aimed Shot - the single-target handler (MARKSMANSHIP §5.2 steps 1-6 and step 9's single-target part, S2a A7).
// Sniper crit helper timing (A5): crit chance is rolled in HandleLaunchPhase (after OnCast, before AfterCast); crit
// damage is applied at hit in Unit::CalculateSpellDamageTaken's RANGED branch, so each missile re-sets eff1 from its
// own snapshot in BeforeHit (two Aimed Shots in flight, R2).
class spell_hun_aimed_shot_mm : public SpellScript
{
    PrepareSpellScript(spell_hun_aimed_shot_mm);

    // The Convergence centre (§5.2 steps 6-7): the first triple-mark target, recorded for S2b's step 9
    struct ConvergenceCentre
    {
        bool set = false;
        ObjectGuid guid;
        Position position;
    };

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_AIMED_SHOT, HunterData::SPELL_VIPERS_BITE,
            HunterData::SPELL_ARCANE_SHOT_FREE, HunterData::SPELL_QUICKENING, HunterData::SPELL_EFFICIENCY_BUFF,
            HunterData::SPELL_PRECISE_SHOTS_BUFF, HunterData::SPELL_SNIPERS_MARK_AIMED_CRIT,
            HunterData::SPELL_IMPROVED_AIMED_SHOT_201968, HunterData::SPELL_DEADEYE_201971,
            HunterData::SPELL_TRIANGULATION_201978, HunterData::SPELL_EFFICIENCY, HunterData::SPELL_EFFICIENCY_19417,
            HunterData::SPELL_EFFICIENCY_19418, HunterData::SPELL_PRECISE_SHOTS_19456,
            HunterData::SPELL_MARKED_FOR_DEATH, HunterData::SPELL_MARKED_FOR_DEATH_53243,
            HunterData::SPELL_MARKED_FOR_DEATH_53244, HunterData::SPELL_SNIPERS_MARK, HunterData::SPELL_VIPERS_MARK,
            HunterData::SPELL_FALCONS_MARK, HunterData::SPELL_CONVERGENCE, HunterData::SPELL_AIMED_SHOT_RICOCHET,
            HunterData::SPELL_AIMED_SHOT_BOUNCE, HunterData::SPELL_TRICK_SHOTS_BUFF,
            HunterData::SPELL_RAIN_OF_ARROWS_BOUNCE });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    // helper 201948: eff0 crit chance (flat points), eff1 crit damage bonus (pct of the +100%)
    static void SetHelper(Player* player, int32 critChance, int32 critDamagePct)
    {
        Hunter::SetSniperCritHelper(player, HunterData::SPELL_SNIPERS_MARK_AIMED_CRIT, critChance, critDamagePct);
    }

    // Viper's Mark -> Viper's Bite with the consumed stacks, alive only (L6); 0 stacks -> nothing.
    // SPELLVALUE_AURA_STACK on a refreshed aura ADDS stacks (Spell.cpp:3262-3271), so the caster's old Bite goes
    // first. Used by the primary (step 6) and by each ricochet target (step 7).
    static void CastVipersBite(Player* player, Unit* target, uint8 stacks)
    {
        if (!stacks || !target->IsAlive() || !player->IsValidAttackTarget(target))
            return;

        target->RemoveAurasDueToSpell(HunterData::SPELL_VIPERS_BITE, player->GetGUID());
        SpellCastResult const result = player->CastCustomSpell(HunterData::SPELL_VIPERS_BITE, SPELLVALUE_AURA_STACK,
            int32(stacks), target, TRIGGERED_FULL_MASK);
        if (result != SPELL_CAST_OK)
            LOG_ERROR("scripts.hunter", "Aimed Shot: Viper's Bite {} ({} stacks) on {} failed (result {})",
                HunterData::SPELL_VIPERS_BITE, uint32(stacks), target->GetGUID().ToString(), uint32(result));
    }

    int32 GetSnapshotCritDamage() const
    {
        return Hunter::SNIPER_CRIT_DAMAGE_PER_STACK * int32(_primary.Stacks(Hunter::Mark::Sniper));
    }

    // Steps 1-2 (cast completion, before launch): read the explicit target's marks, arm the helper
    void HandleOnCast()
    {
        Player* player = GetHunterPlayer(GetCaster());
        if (!player)
            return;

        Unit* target = GetExplTargetUnit();
        _primary = target ? Hunter::ReadMarks(player, target) : Hunter::MarkSnapshot();
        _primaryGuid = target ? target->GetGUID() : ObjectGuid::Empty;

        SetHelper(player, _primary.Has(Hunter::Mark::Sniper) ? Hunter::SNIPER_CRIT_CHANCE : 0,
            GetSnapshotCritDamage());

        // Step 3 (S2b B3): the pack markers belong to this cast; removed now, so a second Aimed Shot in flight
        // can't reuse them
        _trickShots = player->HasAura(HunterData::SPELL_TRICK_SHOTS_BUFF);
        _rainOfArrows = player->HasAura(HunterData::SPELL_RAIN_OF_ARROWS_BOUNCE);
        if (_trickShots)
            player->RemoveAurasDueToSpell(HunterData::SPELL_TRICK_SHOTS_BUFF);

        if (_rainOfArrows)
            player->RemoveAurasDueToSpell(HunterData::SPELL_RAIN_OF_ARROWS_BOUNCE);
    }

    // The crit roll is done; eff1 stays armed for this missile's hit
    void HandleAfterCast()
    {
        if (Player* player = GetHunterPlayer(GetCaster()))
            SetHelper(player, 0, GetSnapshotCritDamage());
    }

    // Step 4. AfterHit only runs on a hit (Spell.cpp DoAllEffectOnTarget), so a miss resets the helper here
    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        Player* player = GetHunterPlayer(GetCaster());
        if (!player)
            return;

        if (missInfo != SPELL_MISS_NONE)
        {
            SetHelper(player, 0, 0);
            return;
        }

        SetHelper(player, 0, GetSnapshotCritDamage());
    }

    // Step 5: Triangulation and the Sniper payoff as separate multipliers (spell_warlock_destruction.cpp shape);
    // before armor and crit
    void HandleOnHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target || target->GetGUID() != _primaryGuid)
            return;

        int32 const damage = GetHitDamage();
        if (damage <= 0)
            return;

        float const triangulation = Hunter::GetTriangulationMultiplier(player, _primary.Count());
        float const sniper = _primary.Has(Hunter::Mark::Sniper) ? Hunter::GetSniperPayoffMultiplier(player) : 1.0f;
        SetHitDamage(int32(float(damage) * triangulation * sniper));
    }

    // Steps 7-8 (S2b B3, S2-HANDOFF seam 3): the Trick Shots ricochets and Rain of Arrows bounces around the primary
    // (`centre` is its position, the corpse's on a killing blow; the search measures from the unit itself, same
    // point). Ricochets add their consumed Falcon's stacks to `maxFalcon`, record a first triple-mark target in
    // `convergence` when none is set yet (Triangulation 3/3, as the primary), and set `tripleConsumed`.
    void HandlePacks(Player* player, Unit* primary, Position const& /*centre*/, uint8& maxFalcon,
        ConvergenceCentre& convergence, bool& tripleConsumed)
    {
        GuidSet exclude;   // every ricochet target; the bounce skips them

        // Step 7: per target, read its marks -> its own helper values -> the ricochet (Speed 0 + TRIGGERED_FULL_MASK:
        // launch, crit roll and hit all run inside CastSpell) -> consume exactly as step 6
        if (_trickShots)
        {
            bool const triangulation3 = player->HasAura(HunterData::SPELL_TRIANGULATION_201978);

            std::vector<Unit*> ricochets;
            CollectPackTargets(player, primary, Hunter::PACK_RADIUS, Hunter::PACK_MAX_TARGETS, true, exclude,
                ricochets);
            for (Unit* unit : ricochets)
            {
                Hunter::MarkSnapshot const marks = Hunter::ReadMarks(player, unit);
                SetHelper(player, marks.Has(Hunter::Mark::Sniper) ? Hunter::SNIPER_CRIT_CHANCE : 0,
                    Hunter::SNIPER_CRIT_DAMAGE_PER_STACK * int32(marks.Stacks(Hunter::Mark::Sniper)));

                exclude.insert(unit->GetGUID());
                SpellCastResult const result =
                    player->CastSpell(unit, HunterData::SPELL_AIMED_SHOT_RICOCHET, TRIGGERED_FULL_MASK);
                if (result != SPELL_CAST_OK)
                {
                    LOG_ERROR("scripts.hunter", "Aimed Shot: ricochet {} on {} failed (result {})",
                        HunterData::SPELL_AIMED_SHOT_RICOCHET, unit->GetGUID().ToString(), uint32(result));
                    continue;
                }

                // A ricochet that killed its target took the marks with the death: the snapshot pays (as step 6)
                Hunter::ConsumeMarks(player, unit, marks);
                CastVipersBite(player, unit, marks.Stacks(Hunter::Mark::Viper));
                maxFalcon = std::max(maxFalcon, marks.Stacks(Hunter::Mark::Falcon));

                if (marks.Count() == uint8(Hunter::Mark::Max))
                {
                    tripleConsumed = true;
                    if (!convergence.set && triangulation3)
                    {
                        convergence.set = true;
                        convergence.guid = unit->GetGUID();
                        convergence.position = unit->GetPosition();
                    }
                }
            }
        }

        // Step 8: helper 0/0, no marks read or consumed; never a ricochet target
        if (_rainOfArrows)
        {
            SetHelper(player, 0, 0);

            std::vector<Unit*> bounces;
            CollectPackTargets(player, primary, Hunter::PACK_RADIUS, Hunter::PACK_MAX_TARGETS, false, exclude,
                bounces);
            for (Unit* unit : bounces)
            {
                SpellCastResult const result =
                    player->CastSpell(unit, HunterData::SPELL_AIMED_SHOT_BOUNCE, TRIGGERED_FULL_MASK);
                if (result != SPELL_CAST_OK)
                    LOG_ERROR("scripts.hunter", "Aimed Shot: bounce {} on {} failed (result {})",
                        HunterData::SPELL_AIMED_SHOT_BOUNCE, unit->GetGUID().ToString(), uint32(result));
            }
        }
    }

    // Step 9's Convergence branch (S2b B3): once per cast, at the recorded centre's position (alive or a corpse: a
    // dead unit target would fail the cast). 201932 is Speed 0 and triggered, so it resolves inside CastSpell and
    // spell_hun_convergence reads the centre GUID before it is cleared.
    static void CastConvergence(Player* player, ConvergenceCentre const& convergence)
    {
        if (!convergence.set || !player->HasAura(HunterData::SPELL_TRIANGULATION_201978))
            return;

        SpellCastTargets targets;
        targets.SetDst(convergence.position);

        Hunter::SetConvergenceCentre(player, convergence.guid);
        SpellCastResult const result = player->CastSpell(targets,
            sSpellMgr->AssertSpellInfo(HunterData::SPELL_CONVERGENCE), nullptr, TRIGGERED_FULL_MASK);
        Hunter::SetConvergenceCentre(player, ObjectGuid::Empty);

        if (result != SPELL_CAST_OK)
            LOG_ERROR("scripts.hunter", "Aimed Shot: Convergence {} at centre {} failed (result {})",
                HunterData::SPELL_CONVERGENCE, convergence.guid.ToString(), uint32(result));
    }

    // Step 6 riders on the primary
    void HandleRiders(Player* player, Unit* target, bool alive, bool crit)
    {
        // Improved Aimed Shot 3/3: a free Arcane Shot at the target (alive only, L6)
        if (alive && player->HasAura(HunterData::SPELL_IMPROVED_AIMED_SHOT_201968) &&
            player->IsValidAttackTarget(target))
        {
            SpellCastResult const result = player->CastSpell(target, HunterData::SPELL_ARCANE_SHOT_FREE,
                TRIGGERED_FULL_MASK);
            if (result != SPELL_CAST_OK)
                LOG_ERROR("scripts.hunter", "Aimed Shot: free Arcane Shot {} on {} failed (result {})",
                    HunterData::SPELL_ARCANE_SHOT_FREE, target->GetGUID().ToString(), uint32(result));
        }

        // Efficiency: the buff takes the known rank's strength, read from the rank spell (L10), on both effects
        if (uint32 const rank = GetKnownRank(player, { HunterData::SPELL_EFFICIENCY_19418,
                HunterData::SPELL_EFFICIENCY_19417, HunterData::SPELL_EFFICIENCY }))
        {
            int32 const strength = sSpellMgr->AssertSpellInfo(rank)->Effects[EFFECT_0].CalcValue(player);
            if (strength > 0)
            {
                CustomSpellValues values;
                values.AddSpellMod(SPELLVALUE_BASE_POINT0, -strength);
                values.AddSpellMod(SPELLVALUE_BASE_POINT1, -strength);
                player->CastCustomSpell(HunterData::SPELL_EFFICIENCY_BUFF, values, player, TRIGGERED_FULL_MASK);
            }
        }

        // Precise Shots 3/3
        if (player->HasAura(HunterData::SPELL_PRECISE_SHOTS_19456))
            player->CastSpell(player, HunterData::SPELL_PRECISE_SHOTS_BUFF, TRIGGERED_FULL_MASK);

        // Deadeye 3/3: a primary crit cuts the three marks' cooldowns, real seconds, once per cast
        if (crit && player->HasAura(HunterData::SPELL_DEADEYE_201971))
        {
            for (uint32 markSpell : { HunterData::SPELL_SNIPERS_MARK, HunterData::SPELL_VIPERS_MARK,
                     HunterData::SPELL_FALCONS_MARK })
                Hunter::ReduceSpellCooldown(player, markSpell, Hunter::DEADEYE_CDR_MS);
        }
    }

    // Step 6 (consume, riders) and step 9's single-target part. Gated only on the primary's missCondition: a
    // killing blow is a hit, so everything runs on it except the casts aimed at the dead unit ("alive only").
    void HandleAfterHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        if (!player)
            return;

        Unit* target = GetHitUnit();
        TargetInfo const* info = target && target->GetGUID() == _primaryGuid ?
            FindTargetInfo(GetSpell(), _primaryGuid) : nullptr;
        if (!info || info->missCondition != SPELL_MISS_NONE)
        {
            SetHelper(player, 0, 0);
            return;
        }

        bool const crit = info->crit;
        bool const alive = target->IsAlive();
        Position const centre = target->GetPosition();   // the corpse's position on a killing blow, same tick

        // Consume (§4.4): on a dead target the auras went with the death, so this is a no-op and the snapshot pays
        Hunter::ConsumeMarks(player, target, _primary);

        // Viper's Mark -> Viper's Bite with the consumed stacks (alive only)
        CastVipersBite(player, target, _primary.Stacks(Hunter::Mark::Viper));

        // Falcon's Mark -> the highest consumed Falcon's stack (primary here; S2b's ricochets add theirs)
        uint8 maxFalcon = _primary.Stacks(Hunter::Mark::Falcon);

        // Three marks consumed: a triple consume; with Triangulation 3/3 the primary is the Convergence centre
        bool tripleConsumed = _primary.Count() == uint8(Hunter::Mark::Max);
        ConvergenceCentre convergence;
        if (tripleConsumed && player->HasAura(HunterData::SPELL_TRIANGULATION_201978))
        {
            convergence.set = true;
            convergence.guid = target->GetGUID();
            convergence.position = centre;
        }

        HandleRiders(player, target, alive, crit);

        HandlePacks(player, target, centre, maxFalcon, convergence, tripleConsumed);

        // Step 9 (once per cast): Convergence first (S2b), then Quickening
        CastConvergence(player, convergence);

        // Quickening: 1 s per stack of the highest Falcon's consumed, never shortening a running one (M-m3: a
        // SPELLVALUE_AURA_DURATION overwrites the remaining time, Spell.cpp:3309-3317)
        if (maxFalcon > 0)
        {
            int32 duration = int32(maxFalcon) * int32(Hunter::QUICKENING_MS_PER_STACK);
            if (Aura const* quickening = player->GetAura(HunterData::SPELL_QUICKENING, player->GetGUID()))
                duration = std::max(duration, quickening->GetDuration());

            player->CastCustomSpell(HunterData::SPELL_QUICKENING, SPELLVALUE_AURA_DURATION, duration, player,
                TRIGGERED_FULL_MASK);
        }

        if (tripleConsumed)
            Hunter::NoteTripleConsume(player);

        Hunter::RefreshFalconHaste(player);
        SetHelper(player, 0, 0);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_hun_aimed_shot_mm::HandleOnCast);
        AfterCast += SpellCastFn(spell_hun_aimed_shot_mm::HandleAfterCast);
        BeforeHit += BeforeSpellHitFn(spell_hun_aimed_shot_mm::HandleBeforeHit);
        OnHit += SpellHitFn(spell_hun_aimed_shot_mm::HandleOnHit);
        AfterHit += SpellHitFn(spell_hun_aimed_shot_mm::HandleAfterHit);
    }

private:
    Hunter::MarkSnapshot _primary;
    ObjectGuid _primaryGuid;
    bool _trickShots = false;     // 201943 was up at cast completion (step 3)
    bool _rainOfArrows = false;   // 201944 was up at cast completion (step 3)
};

// 53209 Chimera Shot (stock spell_hun_chimera_shot unbound) - the Serpent burst and refresh, and each mark triggers
// without being consumed (MARKSMANSHIP §5.6, S2a A8). Helper 201949 follows Aimed Shot's timing (A5).
class spell_hun_chimera_shot_mm : public SpellScript
{
    PrepareSpellScript(spell_hun_chimera_shot_mm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_CHIMERA_SHOT_SERPENT, HunterData::SPELL_SERPENT_STING,
            HunterData::SPELL_VIPERS_VENOM, HunterData::SPELL_CHIMERA_SHOT_FALCON,
            HunterData::SPELL_SNIPERS_MARK_CHIMERA_CRIT, HunterData::SPELL_VIPERS_MARK });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    static void SetHelper(Player* player, int32 critChance, int32 critDamagePct)
    {
        Hunter::SetSniperCritHelper(player, HunterData::SPELL_SNIPERS_MARK_CHIMERA_CRIT, critChance, critDamagePct);
    }

    int32 GetSnapshotCritDamage() const
    {
        return _marks.Has(Hunter::Mark::Sniper) ? Hunter::CHIMERA_SNIPER_CRIT_DAMAGE : 0;
    }

    void HandleOnCast()
    {
        Player* player = GetHunterPlayer(GetCaster());
        if (!player)
            return;

        Unit* target = GetExplTargetUnit();
        _marks = target ? Hunter::ReadMarks(player, target) : Hunter::MarkSnapshot();
        _primaryGuid = target ? target->GetGUID() : ObjectGuid::Empty;

        SetHelper(player, _marks.Has(Hunter::Mark::Sniper) ? Hunter::CHIMERA_SNIPER_CRIT_CHANCE : 0,
            GetSnapshotCritDamage());
    }

    void HandleAfterCast()
    {
        if (Player* player = GetHunterPlayer(GetCaster()))
            SetHelper(player, 0, GetSnapshotCritDamage());
    }

    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        Player* player = GetHunterPlayer(GetCaster());
        if (!player)
            return;

        SetHelper(player, 0, missInfo == SPELL_MISS_NONE ? GetSnapshotCritDamage() : 0);
    }

    // eff0 SCRIPT_EFFECT: stock's Serpent branch (spell_hunter.cpp spell_hun_chimera_shot); Viper/Scorpid dropped
    void HandleScriptEffect(SpellEffIndex /*effIndex*/)
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        Aura* sting = target->GetAura(HunterData::SPELL_SERPENT_STING, player->GetGUID());
        AuraEffect* stingEffect = sting ? sting->GetEffect(EFFECT_0) : nullptr;
        if (!stingEffect)
            return;

        // 40% of the sting's total damage, taken mods applied the way stock does (53353 ignores caster mods)
        int32 burst = stingEffect->GetAmount();
        ApplyPct(burst, stingEffect->GetTotalTicks() * CHIMERA_SERPENT_BURST_PCT);
        if (burst > 0)
            burst = int32(target->SpellDamageBonusTaken(player, sting->GetSpellInfo(), uint32(burst), DOT,
                sting->GetStackAmount()));

        // Refresh with a full re-snapshot (S2a brief resolution 7, M-m7): RefreshTimers(false) recomputes the max
        // duration, the hasted amplitude and the crit snapshot without a tick reset (SpellAuras.cpp:945-964; it
        // skips the periodic part only for a null caster, and the caster is this Player); ChangeAmount re-snapshots
        // the amount. mark = false as stock, so the amount stays recalculable.
        sting->RefreshTimers(false);
        stingEffect->ChangeAmount(stingEffect->CalculateAmount(player), false);

        if (burst > 0)
            player->CastCustomSpell(HunterData::SPELL_CHIMERA_SHOT_SERPENT, SPELLVALUE_BASE_POINT0, burst, target,
                TRIGGERED_FULL_MASK);
    }

    void HandleOnHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target || target->GetGUID() != _primaryGuid || !_marks.Has(Hunter::Mark::Sniper))
            return;

        int32 const damage = GetHitDamage();
        if (damage > 0)
            SetHitDamage(int32(float(damage) * Hunter::GetSniperPayoffMultiplier(player)));
    }

    // Hit only, killing blow included (M4)
    void HandleAfterHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        if (!player)
            return;

        Unit* target = GetHitUnit();
        TargetInfo const* info = target && target->GetGUID() == _primaryGuid ?
            FindTargetInfo(GetSpell(), _primaryGuid) : nullptr;
        if (info && info->missCondition == SPELL_MISS_NONE)
        {
            // Falcon's Mark -> Falcon's Edge on self (refreshes on a recast), dead target or not
            if (_marks.Has(Hunter::Mark::Falcon))
                player->CastSpell(player, HunterData::SPELL_CHIMERA_SHOT_FALCON, TRIGGERED_FULL_MASK);

            // Viper's Mark -> one more Viper's stack and Viper's Venom (alive only, L6)
            if (_marks.Has(Hunter::Mark::Viper) && target->IsAlive() && player->IsValidAttackTarget(target))
            {
                Hunter::AddMarkStacks(player, target, Hunter::Mark::Viper, Hunter::MARK_GAIN);
                SpellCastResult const result = player->CastSpell(target, HunterData::SPELL_VIPERS_VENOM,
                    TRIGGERED_FULL_MASK);
                if (result != SPELL_CAST_OK)
                    LOG_ERROR("scripts.hunter", "Chimera Shot: Viper's Venom {} on {} failed (result {})",
                        HunterData::SPELL_VIPERS_VENOM, target->GetGUID().ToString(), uint32(result));
            }
        }

        SetHelper(player, 0, 0);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_hun_chimera_shot_mm::HandleOnCast);
        AfterCast += SpellCastFn(spell_hun_chimera_shot_mm::HandleAfterCast);
        BeforeHit += BeforeSpellHitFn(spell_hun_chimera_shot_mm::HandleBeforeHit);
        OnEffectHitTarget += SpellEffectFn(spell_hun_chimera_shot_mm::HandleScriptEffect, EFFECT_0,
            SPELL_EFFECT_SCRIPT_EFFECT);
        OnHit += SpellHitFn(spell_hun_chimera_shot_mm::HandleOnHit);
        AfterHit += SpellHitFn(spell_hun_chimera_shot_mm::HandleAfterHit);
    }

private:
    Hunter::MarkSnapshot _marks;
    ObjectGuid _primaryGuid;
};

// 3044 Arcane Shot, 201933 Arcane Shot (free) - Keen Eye's Arcane Shot half and the Lethal Shots capstone
// (MARKSMANSHIP §5.10, §6 row (0,0), S2a A10). Additive with spell_hun_shot_mana (the first restore) and, on 3044,
// spell_hun_arcane_shot_bm.
class spell_hun_arcane_shot_mm : public SpellScript
{
    PrepareSpellScript(spell_hun_arcane_shot_mm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_LETHAL_SHOTS_19429, HunterData::SPELL_KEEN_EYE,
            HunterData::SPELL_KEEN_EYE_201973, HunterData::SPELL_KEEN_EYE_201974 });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    // Keen Eye rolls on the player's own presses only (the free shot is triggered)
    void HandleOnCast()
    {
        if (GetSpell()->IsTriggered())
            return;

        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetExplTargetUnit();
        if (player && target)
            Hunter::RollKeenEye(player, target);
    }

    // Lethal Shots 3/3: a crit restores the shot's mana once more (spell_hun_shot_mana made the first restore)
    void HandleAfterHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        if (!player || !player->HasAura(HunterData::SPELL_LETHAL_SHOTS_19429))
            return;

        if (IsCritHit(GetSpell(), GetHitUnit()))
            Hunter::RestoreShotMana(player, GetSpellInfo());
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_hun_arcane_shot_mm::HandleOnCast);
        AfterHit += SpellHitFn(spell_hun_arcane_shot_mm::HandleAfterHit);
    }
};

// 56641 Steady Shot - the Focused Aim capstone: a crit cuts Aimed Shot's cooldown, real seconds, once per Steady Shot
// (MARKSMANSHIP §5.11, S2a A12). Category 1301's cooldown is stored under 19434 itself (0-verify 7.6).
class spell_hun_steady_shot_mm : public SpellScript
{
    PrepareSpellScript(spell_hun_steady_shot_mm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_FOCUSED_AIM_53622, HunterData::SPELL_AIMED_SHOT });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    void HandleAfterHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        if (!player || !player->HasAura(HunterData::SPELL_FOCUSED_AIM_53622))
            return;

        if (IsCritHit(GetSpell(), GetHitUnit()))
            Hunter::ReduceSpellCooldown(player, HunterData::SPELL_AIMED_SHOT, Hunter::FOCUSED_AIM_CDR_MS);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_hun_steady_shot_mm::HandleAfterHit);
    }
};

// 201965 Precision rank 3 - your crit on a Sniper-marked target adds a Sniper's stack (MARKSMANSHIP §8, S2a A13).
// The spell_proc row is HIT phase with hit mask CRIT, so the action target is set; eff1 is the DUMMY carrier.
class spell_hun_precision_capstone : public AuraScript
{
    PrepareAuraScript(spell_hun_precision_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_SNIPERS_MARK });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    Player* GetHunter() const
    {
        return GetHunterPlayer(GetUnitOwner());
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetHunter();
        if (!player || eventInfo.GetActor() != player)
            return false;

        Spell const* procSpell = eventInfo.GetProcSpell();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!procSpell || !spellInfo || procSpell->IsTriggered())
            return false;

        if (spellInfo->SpellFamilyName == SPELLFAMILY_HUNTER &&
            (spellInfo->SpellFamilyFlags[2] & FAMILY_FLAG2_MARK_PRESS))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        return target && Hunter::HasMark(player, target, Hunter::Mark::Sniper);
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetHunter();
        Unit* target = eventInfo.GetActionTarget();
        if (!player || !target)
            return;

        // a stack write, never OnMarkApplied (§4.2)
        Hunter::AddMarkStacks(player, target, Hunter::Mark::Sniper, PRECISION_SNIPER_GAIN);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_precision_capstone::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_precision_capstone::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 201981 Rapid Killing rank 3 - only a creature kill grants 35098 (MARKSMANSHIP §8, S2a A15). The row's
// PROC_ATTR_REQ_EXP_OR_HONOR would also pass honor kills; the default action casts 35098.
class spell_hun_rapid_killing_capstone : public AuraScript
{
    PrepareAuraScript(spell_hun_rapid_killing_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_RAPID_KILLING_35098 });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!GetHunterPlayer(GetUnitOwner()))
            return false;

        // PROC_FLAG_KILL: actor = the killer, action target = the victim (Unit.cpp ProcSkillsAndAuras on a kill)
        Unit* victim = eventInfo.GetActionTarget();
        return victim && victim->IsCreature();
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_rapid_killing_capstone::CheckProc);
    }
};

// 201951 Marksmanship Mastery (Marked for Death 3/3, linked_spell) - eff0 (mark presses' damage) and eff1 (mark DoTs)
// follow the live Mastery %, rounded, re-set only on change (MARKSMANSHIP §7, S2a A16; spell_hun_tbw_mastery shape)
class spell_hun_mm_mastery : public AuraScript
{
    PrepareAuraScript(spell_hun_mm_mastery);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    static int32 GetMasteryAmount(Unit const* owner)
    {
        Player const* player = owner ? owner->ToPlayer() : nullptr;
        return player ? int32(std::lround(player->GetMasteryPercentage())) : 0;
    }

    // eff0 / eff1 start at the live Mastery on apply and on any engine recalculation (R-cpp S2), not at the DBC 0
    // until the first tick; a mark DoT applied in that first second snapshots the right value
    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return;

        amount = GetMasteryAmount(owner);
        canBeRecalculated = true;
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return;

        // Changing the amount re-sends the spell mod to the client, so only do it when the rounded value moved
        int32 const amount = GetMasteryAmount(owner);
        for (uint8 effIndex : { uint8(EFFECT_0), uint8(EFFECT_1) })
        {
            AuraEffect* modEffect = GetEffect(effIndex);
            if (modEffect && modEffect->GetAuraType() == SPELL_AURA_ADD_PCT_MODIFIER &&
                modEffect->GetAmount() != amount)
                modEffect->ChangeAmount(amount, false);
        }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_hun_mm_mastery::CalculateAmount, EFFECT_0,
            SPELL_AURA_ADD_PCT_MODIFIER);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_hun_mm_mastery::CalculateAmount, EFFECT_1,
            SPELL_AURA_ADD_PCT_MODIFIER);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_hun_mm_mastery::HandlePeriodic, EFFECT_2,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 53234, 53237, 53238 Piercing Shots (stock spell_hun_piercing_shots unbound from -53234) - a crit Steady or primary
// Aimed Shot bleeds the target for the rank's % of the damage over 63468's duration (MARKSMANSHIP §10.3, S2a A17).
// Stock body, but the per-tick share divides by duration / hasted amplitude (M-m6): the fork hastes periodic damage
// (SpellAuraEffects.cpp CalculatePeriodic) and pays the leftover fraction on the last tick, so the integer tick count
// would overpay.
class spell_hun_piercing_shots_mm : public AuraScript
{
    PrepareAuraScript(spell_hun_piercing_shots_mm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PIERCING_SHOTS_BLEED });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    // The "does this proc act" gate lives here, so nothing acts on a no-op (L6)
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetHunterPlayer(GetUnitOwner());
        if (!player || eventInfo.GetActor() != player)
            return false;

        Unit* target = eventInfo.GetActionTarget();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        return target && target->IsAlive() && damageInfo && damageInfo->GetDamage() > 0;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* caster = eventInfo.GetActor();
        Unit* target = eventInfo.GetActionTarget();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!caster || !target || !damageInfo || !damageInfo->GetDamage())
            return;

        SpellInfo const* bleed = sSpellMgr->AssertSpellInfo(SPELL_PIERCING_SHOTS_BLEED);
        int32 const duration = bleed->GetDuration();
        float const hastedAmplitude = float(bleed->Effects[EFFECT_0].Amplitude) *
            caster->GetFloatValue(UNIT_MOD_CAST_SPEED);
        if (duration <= 0 || hastedAmplitude <= 0.0f)
        {
            LOG_ERROR("scripts.hunter", "Piercing Shots: bleed {} has duration {} / hasted amplitude {}",
                SPELL_PIERCING_SHOTS_BLEED, duration, hastedAmplitude);
            return;
        }

        int32 const total = CalculatePct(int32(damageInfo->GetDamage()), aurEff->GetAmount());
        int32 const perTick = int32(float(total) / (float(duration) / hastedAmplitude));
        if (perTick <= 0)
            return;

        target->CastDelayedSpellWithPeriodicAmount(caster, SPELL_PIERCING_SHOTS_BLEED, SPELL_AURA_PERIODIC_DAMAGE,
            perTick);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_piercing_shots_mm::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_piercing_shots_mm::HandleProc, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// ===========================================================================================
// S2b - packs, area effects and the passives (S2b-HANDOFF B1-B9)
// ===========================================================================================

// 2643 Multi-Shot - the 5-target cap, Keen Eye's Multi-Shot half and the Trick Shots copies and marker (MARKSMANSHIP
// §5.3, S2b B1). Built eff0: NORMALIZED_WEAPON_DMG, TargetA 6 (TARGET_UNIT_TARGET_ENEMY), chain 3.
class spell_hun_multi_shot_mm : public SpellScript
{
    PrepareSpellScript(spell_hun_multi_shot_mm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_TRICK_SHOTS_BUFF, HunterData::SPELL_TRICK_SHOTS,
            HunterData::SPELL_KEEN_EYE, HunterData::SPELL_KEEN_EYE_201973, HunterData::SPELL_KEEN_EYE_201974,
            HunterData::SPELL_SNIPERS_MARK, HunterData::SPELL_VIPERS_MARK, HunterData::SPELL_FALCONS_MARK });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    // The chain list excludes the primary (Spell.cpp ~1946) and is in jump order (each candidate closest to the
    // previous jump, Spell.cpp:2276-2298); re-sort it by distance to the primary and keep the nearest
    // MULTI_SHOT_TARGET_CAP - 1, so Trick Shots +2 and BM's Pack Hunter +1/+2 never reach more than 5 (M-m2)
    void TrimChainTargets(std::list<WorldObject*>& targets)
    {
        std::size_t const maxChainTargets = std::size_t(Hunter::MULTI_SHOT_TARGET_CAP) - 1;
        if (targets.size() <= maxChainTargets)
            return;

        WorldObject const* origin = GetExplTargetUnit();
        if (!origin)
            origin = GetCaster();

        if (!origin)
            return;

        targets.sort([origin](WorldObject const* a, WorldObject const* b)
        {
            return origin->GetExactDistSq(a) < origin->GetExactDistSq(b);
        });
        targets.resize(maxChainTargets);
    }

    // Targets are already selected (Spell.cpp:4021 before :4040) and the OnPlayerSpellCast gains have landed
    // (:3956): Keen Eye first (the player's own presses only), then the copy snapshot, so its stacks are copied
    void HandleOnCast()
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* primary = GetExplTargetUnit();
        if (!player || !primary)
            return;

        if (!GetSpell()->IsTriggered())
            Hunter::RollKeenEye(player, primary);

        _primaryGuid = primary->GetGUID();
        _marks = Hunter::ReadMarks(player, primary);
        _snapshotMs = uint32(GameTime::GetGameTimeMS().count());
        for (Hunter::Mark mark : MM_MARKS)
        {
            Aura const* source = _marks.Has(mark) ?
                primary->GetAura(Hunter::GetMarkSpellId(mark), player->GetGUID()) : nullptr;
            _durations[uint8(mark)] = source ? source->GetDuration() : 0;
        }
    }

    // Per secondary unit hit (missile arrival): copy each snapshot mark the unit lacks from this hunter. AddAura makes
    // a new aura (spell_hun_mark_aura's REAL apply sets the counter to 0), then the snapshot stacks, then the source's
    // remaining time on both max duration and duration so the client timer is right (M-m5). Never overwrites an
    // existing mark, never spreads a copy further (only the primary's snapshot is copied).
    void HandleCopyMarks(SpellEffIndex /*effIndex*/)
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* unit = GetHitUnit();
        if (!player || !unit || unit->GetGUID() == _primaryGuid || !_marks.Count())
            return;

        if (!player->HasAura(HunterData::SPELL_TRICK_SHOTS) || !unit->IsAlive() || !unit->IsInCombatWith(player))
            return;

        int32 const elapsed = int32(uint32(GameTime::GetGameTimeMS().count()) - _snapshotMs);
        for (Hunter::Mark mark : MM_MARKS)
        {
            if (!_marks.Has(mark) || Hunter::HasMark(player, unit, mark))
                continue;

            // A permanent source (duration -1) keeps the copy's own duration; an expired one copies nothing
            int32 const sourceDuration = _durations[uint8(mark)];
            int32 const remaining = sourceDuration > 0 ? sourceDuration - elapsed : sourceDuration;
            if (sourceDuration > 0 && remaining <= 0)
                continue;

            Aura* copy = player->AddAura(Hunter::GetMarkSpellId(mark), unit);
            if (!copy)
                continue;

            Hunter::SetMarkStacks(player, unit, mark, _marks.Stacks(mark));
            if (remaining > 0)
            {
                copy->SetMaxDuration(remaining);
                copy->SetDuration(remaining);
            }
        }
    }

    // The Trick Shots marker for the next Aimed Shot
    void HandleAfterCast()
    {
        Player* player = GetHunterPlayer(GetCaster());
        if (player && player->HasAura(HunterData::SPELL_TRICK_SHOTS))
            player->CastSpell(player, HunterData::SPELL_TRICK_SHOTS_BUFF, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_hun_multi_shot_mm::TrimChainTargets, EFFECT_0,
            TARGET_UNIT_TARGET_ENEMY);
        OnCast += SpellCastFn(spell_hun_multi_shot_mm::HandleOnCast);
        OnEffectHitTarget += SpellEffectFn(spell_hun_multi_shot_mm::HandleCopyMarks, EFFECT_0,
            SPELL_EFFECT_NORMALIZED_WEAPON_DMG);
        AfterCast += SpellCastFn(spell_hun_multi_shot_mm::HandleAfterCast);
    }

private:
    Hunter::MarkSnapshot _marks;
    std::array<int32, 3> _durations{};   // each snapshot mark's remaining ms at OnCast, per Hunter::Mark
    uint32 _snapshotMs = 0;              // GameTime ms of the snapshot
    ObjectGuid _primaryGuid;
};

// 201934 Aimed Shot (ricochet) - Triangulation and the Sniper payoff on its own target, read live (the handler
// consumes that target's marks only after this synchronous cast returns), as separate multipliers before armor and
// crit (MARKSMANSHIP §5.3, S2b B2). Its crit chance / crit damage come from helper 201948, set by the handler.
class spell_hun_aimed_shot_ricochet : public SpellScript
{
    PrepareSpellScript(spell_hun_aimed_shot_ricochet);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_TRIANGULATION, HunterData::SPELL_TRIANGULATION_201977,
            HunterData::SPELL_TRIANGULATION_201978, HunterData::SPELL_MARKED_FOR_DEATH,
            HunterData::SPELL_MARKED_FOR_DEATH_53243, HunterData::SPELL_MARKED_FOR_DEATH_53244,
            HunterData::SPELL_SNIPERS_MARK, HunterData::SPELL_VIPERS_MARK, HunterData::SPELL_FALCONS_MARK });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    void HandleOnHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        int32 const damage = GetHitDamage();
        if (damage <= 0)
            return;

        Hunter::MarkSnapshot const marks = Hunter::ReadMarks(player, target);
        float const triangulation = Hunter::GetTriangulationMultiplier(player, marks.Count());
        float const sniper = marks.Has(Hunter::Mark::Sniper) ? Hunter::GetSniperPayoffMultiplier(player) : 1.0f;
        SetHitDamage(int32(float(damage) * triangulation * sniper));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_hun_aimed_shot_ricochet::HandleOnHit);
    }
};

// 201932 Convergence - the centre hit and the splash (MARKSMANSHIP §5.10, S2b B4). Built: eff0 and eff1 both
// SCHOOL_DAMAGE, TargetA 87 (TARGET_DEST_DEST) / TargetB 16 (TARGET_UNIT_DEST_AREA_ENEMY), radius 8. A hook bound to
// one effect each keeps the two target lists apart (Spell.cpp:1001-1013, :9083-9104), so a unit is either the centre
// (eff0) or a splash target (eff1), never both. The centre GUID comes from Hunter::GetConvergenceCentre, set by the
// Aimed Shot handler around this synchronous cast.
class spell_hun_convergence : public SpellScript
{
    PrepareSpellScript(spell_hun_convergence);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_MARKED_FOR_DEATH, HunterData::SPELL_MARKED_FOR_DEATH_53243,
            HunterData::SPELL_MARKED_FOR_DEATH_53244 });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    // Read once per cast and kept in the instance (M14); empty without a hunter caster or a recorded centre
    ObjectGuid GetCentre()
    {
        if (!_centreRead)
        {
            _centreRead = true;
            Player* player = GetHunterPlayer(GetCaster());
            _centre = player ? Hunter::GetConvergenceCentre(player) : ObjectGuid::Empty;
        }

        return _centre;
    }

    // eff0: only the centre (none when it died: a corpse is not an area target)
    void FilterCentre(std::list<WorldObject*>& targets)
    {
        ObjectGuid const centre = GetCentre();
        targets.remove_if([centre](WorldObject const* object)
        {
            return !object || centre.IsEmpty() || object->GetGUID() != centre;
        });
    }

    // eff1: never the centre, in combat with the hunter only, the nearest CONVERGENCE_MAX_TARGETS to the dest
    void FilterSplash(std::list<WorldObject*>& targets)
    {
        Player* player = GetHunterPlayer(GetCaster());
        ObjectGuid const centre = GetCentre();
        targets.remove_if([player, centre](WorldObject const* object)
        {
            Unit const* unit = object ? object->ToUnit() : nullptr;
            return !player || !unit || unit->GetGUID() == centre || !unit->IsInCombatWith(player);
        });

        std::size_t const maxTargets = CONVERGENCE_MAX_TARGETS;
        if (targets.size() <= maxTargets)
            return;

        if (WorldLocation const* dest = GetExplTargetDest())
        {
            targets.sort([dest](WorldObject const* a, WorldObject const* b)
            {
                return a->GetExactDistSq(*dest) < b->GetExactDistSq(*dest);
            });
        }

        targets.resize(maxTargets);
    }

    // The Sniper payoff always (§4.7); splash hits at CONVERGENCE_SPLASH_PCT (S2a deviation 2: eff1 carries eff0's
    // potency). Before armor and crit.
    void HandleOnHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        int32 const damage = GetHitDamage();
        if (damage <= 0)
            return;

        float multiplier = Hunter::GetSniperPayoffMultiplier(player);
        if (target->GetGUID() != GetCentre())
            multiplier *= float(CONVERGENCE_SPLASH_PCT) / 100.0f;

        SetHitDamage(int32(float(damage) * multiplier));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_hun_convergence::FilterCentre, EFFECT_0,
            TARGET_UNIT_DEST_AREA_ENEMY);
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_hun_convergence::FilterSplash, EFFECT_1,
            TARGET_UNIT_DEST_AREA_ENEMY);
        OnHit += SpellHitFn(spell_hun_convergence::HandleOnHit);
    }

private:
    bool _centreRead = false;
    ObjectGuid _centre;
};

// 1510 Volley - Rain of Arrows 2/2: a Fire! roll per tick and the bounce marker on a completed channel (MARKSMANSHIP
// §5.4, S2b B5). Additive: stock spell_hun_volley_trigger stays on -42243. Built: eff0 PERSISTENT_AREA_AURA (the
// dynobj aura, owned by the DynamicObject: Load drops it), eff1 APPLY_AURA PERIODIC_TRIGGER_SPELL on the caster ->
// 42243 every 1 s.
class spell_hun_volley_mm : public AuraScript
{
    PrepareAuraScript(spell_hun_volley_mm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_FIRE_MM_BUFF, HunterData::SPELL_RAIN_OF_ARROWS_BOUNCE,
            HunterData::SPELL_RAIN_OF_ARROWS_201980 });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    // Once per tick, not per target; no PreventDefaultAction (the tick must still fire)
    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* player = GetHunterPlayer(GetUnitOwner());
        if (!player || !player->HasAura(HunterData::SPELL_RAIN_OF_ARROWS_201980))
            return;

        if (Hunter::RollProcChance(player, float(Hunter::RAIN_OF_ARROWS_FIRE_PCT)))
            player->CastSpell(player, HunterData::SPELL_FIRE_MM_BUFF, TRIGGERED_FULL_MASK);
    }

    // A channel that runs to its end loses its caster aura by expiry (AURA_REMOVE_BY_EXPIRE, Unit.cpp:3847-3850); a
    // cancel or an interrupt is AURA_REMOVE_BY_CANCEL (Spell.cpp:3846-3852), a death BY_DEATH (MM-C1: completed only)
    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;

        Player* player = GetHunterPlayer(GetUnitOwner());
        if (player && player->HasAura(HunterData::SPELL_RAIN_OF_ARROWS_201980))
            player->CastSpell(player, HunterData::SPELL_RAIN_OF_ARROWS_BOUNCE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_hun_volley_mm::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_TRIGGER_SPELL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_hun_volley_mm::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
    }
};

// 24691 Barrage rank 3 - the half Volley at the Multi-Shot's target (MARKSMANSHIP §5.5, S2b B6). The spell_proc row
// is Multi-Shot CAST phase, 25% (DBC), 10 s cooldown, eff0 disabled; eff1 is the DUMMY carrier (trigger_spell 0).
// The CAST phase has no action target (Spell.cpp:4134-4135), so the target is Hunter::GetProcTarget (M-m1).
class spell_hun_barrage_capstone : public AuraScript
{
    PrepareAuraScript(spell_hun_barrage_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_HALF_VOLLEY });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        // Never while one is active (the proc is lost); no target -> lost
        Player* player = GetHunterPlayer(GetUnitOwner());
        if (!player || player->GetDynObject(HunterData::SPELL_HALF_VOLLEY))
            return;

        Unit* target = Hunter::GetProcTarget(eventInfo);
        if (!target)
            return;

        SpellCastTargets targets;
        targets.SetDst(*target);

        SpellCastResult const result = player->CastSpell(targets,
            sSpellMgr->AssertSpellInfo(HunterData::SPELL_HALF_VOLLEY), nullptr, TRIGGERED_FULL_MASK);
        if (result != SPELL_CAST_OK)
            LOG_ERROR("scripts.hunter", "Barrage: half Volley {} at {} failed (result {})",
                HunterData::SPELL_HALF_VOLLEY, target->GetGUID().ToString(), uint32(result));
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_hun_barrage_capstone::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 201936 Volley (half) - the C5 snapshot (MARKSMANSHIP §5.5, Q30, S2b B6; spell_warl_rain_of_fire_aura shape). Built:
// eff0 PERSISTENT_AREA_AURA (the dynobj and the snapshot source; its aura is owned by the DynamicObject, Load drops
// it), eff1 APPLY_AURA PERIODIC_DUMMY 1000 ms on the caster, unhasted (no SPELL_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC,
// no periodic damage aura: SpellAuraEffects.cpp:670-674), so 3 ticks.
class spell_hun_half_volley_aura : public AuraScript
{
    PrepareAuraScript(spell_hun_half_volley_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_HALF_VOLLEY_TICK });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    // The snapshot: eff0 through the caster's done bonuses (Barrage and Rain of Arrows reach it by d2 b30). The
    // victim must be non-null (Unit.cpp:8547, the AP path dereferences it, M-m4): the caster stands in, so the
    // victim-side done terms (Hunter's Mark's RAP attacker bonus, MOD_DAMAGE_DONE_VERSUS by creature type) are
    // judged against the hunter (accepted, SV ground-fire precedent). The dynobj exists already (dest effects run
    // first, Spell.cpp:4269); its position is kept as a fallback for a last tick racing its expiry.
    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        SpellInfo const* info = GetSpellInfo();
        int32 const base = info->Effects[EFFECT_0].CalcValue(caster);
        _snapshot = int32(caster->SpellDamageBonusDone(caster, info, uint32(std::max(0, base)), SPELL_DIRECT_DAMAGE,
            EFFECT_0));

        if (DynamicObject* dyn = caster->GetDynObject(GetId()))
        {
            _centre = dyn->GetPosition();
            _hasCentre = true;
        }
    }

    // Each tick casts the tick at the dynobj with BP0 = the snapshot (IGNORE_CASTER_MODIFIERS: no second done pass)
    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        if (!caster || _snapshot <= 0)
            return;

        SpellCastTargets targets;
        if (DynamicObject* dyn = caster->GetDynObject(GetId()))
            targets.SetDst(*dyn);
        else if (_hasCentre)
            targets.SetDst(_centre);
        else
            return;

        CustomSpellValues values;
        values.AddSpellMod(SPELLVALUE_BASE_POINT0, int32(float(_snapshot) * aurEff->GetFinalTickBonusMultiplier()));

        caster->CastSpell(targets, sSpellMgr->AssertSpellInfo(HunterData::SPELL_HALF_VOLLEY_TICK), &values,
            TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
            caster->RemoveDynObject(GetId());
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_hun_half_volley_aura::HandleApply, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_hun_half_volley_aura::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_hun_half_volley_aura::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }

private:
    int32 _snapshot = 0;
    Position _centre;
    bool _hasCentre = false;
};

// 201937 Volley (half, tick) - in-combat enemies only (MARKSMANSHIP §5.5, S2b B6). Built eff0: SCHOOL_DAMAGE,
// TargetA 87 / TargetB 16 (TARGET_UNIT_DEST_AREA_ENEMY), radius 8.
class spell_hun_half_volley_tick : public SpellScript
{
    PrepareSpellScript(spell_hun_half_volley_tick);

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        targets.remove_if([caster](WorldObject const* object)
        {
            Unit const* unit = object ? object->ToUnit() : nullptr;
            return !caster || !unit || !unit->IsInCombatWith(caster);
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_hun_half_volley_tick::FilterTargets, EFFECT_0,
            TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 19407, 19412 Lone Survivor - the 500 ms refresh of buff 201950 (MARKSMANSHIP §10.3, S2b B7). Built eff2: APPLY_AURA
// PERIODIC_DUMMY, amplitude 500. Hunter::RefreshLoneSurvivor owns the rule (no live hunter pet -> 201950 at the
// Classic or Classless value; pet -> removed); HunterPetScript / HunterUnitScript call it on summon and pet death.
class spell_hun_lone_survivor : public AuraScript
{
    PrepareAuraScript(spell_hun_lone_survivor);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_LONE_SURVIVOR_BUFF });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        if (Player* player = GetHunterPlayer(GetUnitOwner()))
            Hunter::RefreshLoneSurvivor(player);
    }

    // The rank's own aura went (unlearn, respec, rank change): the buff goes with it; a remaining rank's next tick
    // brings it back
    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* owner = GetUnitOwner())
            owner->RemoveAurasDueToSpell(HunterData::SPELL_LONE_SURVIVOR_BUFF);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_hun_lone_survivor::HandlePeriodic, EFFECT_2,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_hun_lone_survivor::HandleRemove, EFFECT_2,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 201952 Combat Experience (capstone, linked from 201982) - Intellect = COMBAT_EXPERIENCE_CAPSTONE_PCT% of Agility
// (MARKSMANSHIP §5.10, S2b B9). Built: eff0 APPLY_AURA MOD_STAT misc 3 (Intellect) bp -1, eff1 APPLY_AURA
// PERIODIC_DUMMY 1000 ms. Intellect never feeds Agility, so no loop.
class spell_hun_combat_experience_capstone : public AuraScript
{
    PrepareAuraScript(spell_hun_combat_experience_capstone);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    static int32 GetIntellectAmount(Unit const* owner)
    {
        return int32(CalculatePct(owner->GetStat(STAT_AGILITY), HunterData::COMBAT_EXPERIENCE_CAPSTONE_PCT));
    }

    // eff0 starts at the live value on apply (no 1 s zero window, spell_hun_mm_mastery precedent)
    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return;

        amount = GetIntellectAmount(owner);
        canBeRecalculated = true;
    }

    // Changing the amount re-applies the stat, so only when it moved (gear, buffs)
    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return;

        AuraEffect* stat = GetEffect(EFFECT_0);
        if (!stat || stat->GetAuraType() != SPELL_AURA_MOD_STAT)
            return;

        int32 const amount = GetIntellectAmount(owner);
        if (stat->GetAmount() != amount)
            stat->ChangeAmount(amount);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_hun_combat_experience_capstone::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_STAT);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_hun_combat_experience_capstone::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

void AddSC_hunter_marksmanship_spell_scripts()
{
    // S2a
    RegisterSpellAndAuraScriptPair(spell_hun_mark, spell_hun_mark_aura);
    RegisterSpellScript(spell_hun_aimed_shot_mm);
    RegisterSpellScript(spell_hun_chimera_shot_mm);
    RegisterSpellScript(spell_hun_arcane_shot_mm);
    RegisterSpellScript(spell_hun_steady_shot_mm);
    RegisterSpellScript(spell_hun_precision_capstone);
    RegisterSpellScript(spell_hun_rapid_killing_capstone);
    RegisterSpellScript(spell_hun_mm_mastery);
    RegisterSpellScript(spell_hun_piercing_shots_mm);

    // S2b
    RegisterSpellScript(spell_hun_multi_shot_mm);
    RegisterSpellScript(spell_hun_aimed_shot_ricochet);
    RegisterSpellScript(spell_hun_convergence);
    RegisterSpellScript(spell_hun_volley_mm);
    RegisterSpellScript(spell_hun_barrage_capstone);
    RegisterSpellScript(spell_hun_half_volley_aura);
    RegisterSpellScript(spell_hun_half_volley_tick);
    RegisterSpellScript(spell_hun_lone_survivor);
    RegisterSpellScript(spell_hun_combat_experience_capstone);
}
