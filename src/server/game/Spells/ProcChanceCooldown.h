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

#ifndef PROC_CHANCE_COOLDOWN_H
#define PROC_CHANCE_COOLDOWN_H

#include "Define.h"
#include "Duration.h"

class Aura;
class Unit;

/**
 * Custom: gear-scaling GS2 (docs/Systems.md section 5, "Proc Chance shortens internal cooldowns"): a class proc's
 * internal cooldown is ICD / (1 + Proc Chance), the same shape as Cooldown Haste. One formula and one eligibility rule
 * for both paths: spell_proc rows (Aura::AddProcCooldown, behind the same gate as Aura::CalcProcChance: a player
 * caster, no cast item) and the scripts that keep their own ICD next to their own roll (ScaleFor, ScaleMarkerAura).
 * Items, non-class enchants and Cooldown Haste never come here.
 */
namespace ProcChanceCooldown
{
    // Eligibility (user ruling 2026-11-27): only a proc with a chance roll scales, i.e. a listed chance under 100%
    // (the chance Proc Chance already multiplies; a spell_proc row's Chance, or the base chance a script rolls).
    // A 100% proc keeps its fixed ICD (capstones and spreads among them), and so does an aura that spends charges or
    // stacks on its procs (there the ICD meters the spending: Bone Shield, Lightning Shield).
    inline bool IsScaledProc(float listedChancePct, bool spendsCharges = false)
    {
        return !spendsCharges && listedChancePct < 100.0f;
    }

    // The pure formula. procChancePct is the stat in percent (Player::GetProcChancePercentage); 0 or less keeps
    // the listed ICD.
    inline uint32 Scale(uint32 icdMs, float procChancePct)
    {
        if (!icdMs || procChancePct <= 0.0f)
            return icdMs;

        return uint32(float(icdMs) / (1.0f + procChancePct / 100.0f));
    }

    inline Milliseconds Scale(Milliseconds icd, float procChancePct)
    {
        if (icd <= Milliseconds::zero())
            return icd;

        return Milliseconds(Scale(uint32(icd.count()), procChancePct));
    }

    // The Proc Chance that reaches `unit`'s scripted procs: the player's own, or the owning player's for a pet,
    // guardian or totem (Systems.md section 5: pet-side scripted procs roll the owner's Proc Chance); 0 otherwise.
    float GetProcChancePct(Unit const* unit);

    // A script-kept ICD for `unit`'s proc whose roll has the base chance `listedChancePct` (before Proc Chance);
    // unchanged unless IsScaledProc.
    uint32 ScaleFor(Unit const* unit, uint32 icdMs, float listedChancePct);

    // A script-kept ICD held as a hidden self-aura (the marker's DBC duration is the listed ICD): shortens the
    // just-applied marker's duration for its caster's Proc Chance, if IsScaledProc(listedChancePct). A null aura is
    // ignored.
    void ScaleMarkerAura(Aura* marker, float listedChancePct);
}

#endif
