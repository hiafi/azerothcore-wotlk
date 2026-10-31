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

#ifndef __KILLCREDIT_H
#define __KILLCREDIT_H

#include "DataMap.h"
#include "Define.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include <algorithm>
#include <vector>

class Spell;
class SpellInfo;
class Unit;
enum DamageEffectType : uint8;

/*
 * Kill credit window (warrior-rework KC; docs/reworks/warrior-shared-rework.md "Kill credit",
 * .agents/plans/kill-credit-window/kill-credit-window.PLAN.md). A player who struck a creature with direct damage from
 * an ability (or whose pet/guardian did) within the last 2 s before it dies counts as having killed it for class
 * effects only: their PROC_FLAG_KILL auras fire, and the C++ kill hooks (Frost Channeling, Deathspeaker, Rune of
 * Unending Thirst) run for their own recorded spell. Quests, loot, XP, honor, reputation, achievements and every
 * ScriptMgr kill hook keep crediting exactly as stock.
 *
 * The record is a per-victim HitLog in WorldObject::CustomData, not an aura: no aura slot, no packet, no cast per hit,
 * map-thread local (it belongs to the victim) and freed with the creature.
 */
namespace KillCredit
{
    // "window 2 sec [fixed]" (shared warrior doc, KC-D1).
    constexpr Milliseconds WINDOW{2000};

    struct Assist
    {
        ObjectGuid player;
        Milliseconds lastHit;       // newest hit by the player or anything the player controls
        uint32 ownSpellId;          // newest direct spell the player cast itself, 0 = none
        Milliseconds ownSpellAt;
    };

    // Pure per-victim record with no game calls, so src/test can exercise it without the game library (KC-D12).
    // One entry per player (KC-D7); a handful of players at most, so a flat vector beats a map.
    class HitLog : public DataMap::Base
    {
    public:
        // ownSpellId 0 = a pet's, guardian's or other controlled unit's hit: it refreshes lastHit and keeps the
        // player's own spell. Entries whose lastHit left the window are pruned first.
        void Record(ObjectGuid player, uint32 ownSpellId, Milliseconds now)
        {
            _entries.erase(std::remove_if(_entries.begin(), _entries.end(),
                [now](Assist const& entry) { return now - entry.lastHit > WINDOW; }), _entries.end());

            for (Assist& entry : _entries)
            {
                if (entry.player != player)
                    continue;

                entry.lastHit = now;
                if (ownSpellId)
                {
                    entry.ownSpellId = ownSpellId;
                    entry.ownSpellAt = now;
                }
                return;
            }

            _entries.push_back({ player, now, ownSpellId, ownSpellId ? now : Milliseconds::zero() });
        }

        // Entries with now - lastHit <= WINDOW; an entry's ownSpellId is 0 unless now - ownSpellAt <= WINDOW too.
        std::vector<Assist> Collect(Milliseconds now) const
        {
            std::vector<Assist> result;
            for (Assist const& entry : _entries)
            {
                if (now - entry.lastHit > WINDOW)
                    continue;

                Assist assist = entry;
                if (assist.ownSpellId && now - assist.ownSpellAt > WINDOW)
                    assist.ownSpellId = 0;

                result.push_back(assist);
            }
            return result;
        }

        bool Empty() const { return _entries.empty(); }
        std::size_t Size() const { return _entries.size(); }

    private:
        std::vector<Assist> _entries;
    };

    // Unit::DealDamage, after sScriptMgr->OnDamage: records direct ability hits on creatures (KC-D2, D3, D4).
    void RecordHit(Unit* attacker, Unit* victim, DamageEffectType damagetype, SpellInfo const* spellProto,
        Spell const* damageSpell);

    // Unit::Kill, after the stock KILL/KILLED proc block: pays the assisters (KC-D5, D6, D8, D9, D10).
    void OnKill(Unit* killer, Unit* victim, SpellInfo const* killingSpell);
}

#endif
