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

#include "KillCredit.h"
#include "DeathKnightMechanics.h"
#include "GameTime.h"
#include "Log.h"
#include "MageMechanics.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "PriestMechanics.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"
#include <string>

namespace
{
    // DataMap keys are std::string const&: a file-scope string keeps RecordHit from building one per hit.
    std::string const HIT_LOG_KEY = "kc_hit_log";
}

namespace KillCredit
{
    void RecordHit(Unit* attacker, Unit* victim, DamageEffectType damagetype, SpellInfo const* spellProto,
        Spell const* damageSpell)
    {
        // Direct damage from an ability only (shared warrior doc "Kill credit"): white swings are DIRECT_DAMAGE with no
        // spellProto, periodic ticks DOT, the share-damage recursion NODAMAGE. Triggered spells (Heroic Leap's landing,
        // Sweeping copies, Seal procs) and fully absorbed hits count (KC-D2). Cheapest checks first: this runs on every
        // DealDamage in the world.
        if (damagetype != SPELL_DIRECT_DAMAGE || !spellProto || !attacker || !victim || attacker == victim)
            return;

        // Creature deaths only; player and player-pet deaths keep stock behaviour (KC-D3), so they never get a record.
        if (!victim->IsCreature() || victim->IsCharmedOwnedByPlayerOrPlayer())
            return;

        // Damage shields (Thorns, Retribution Aura) hit through DealDamage as SPELL_DIRECT_DAMAGE too, but they are a
        // reaction to being swung at, not a strike.
        if (spellProto->HasAura(SPELL_AURA_DAMAGE_SHIELD))
            return;

        // The same for damage that a "when you are hit" proc aura casts as a plain spell (Damage Shield 59653, Holy
        // Shield, Lightning Shield): the spell carries the aura that triggered it (Spell::prepare ->
        // TriggeredByAuraSpellData::Init), and that aura procs on taken hits only. Auras without a spell_proc row use
        // the DBC flags.
        if (damageSpell)
        {
            if (SpellInfo const* trigger = damageSpell->GetTriggeredByAuraSpellInfo())
            {
                SpellProcEntry const* proc = sSpellMgr->GetSpellProcEntry(trigger->Id);
                uint32 const procFlags = proc ? proc->ProcFlags : trigger->ProcFlags;
                if ((procFlags & TAKEN_HIT_PROC_FLAG_MASK) && !(procFlags & DONE_HIT_PROC_FLAG_MASK))
                    return;
            }
        }

        // Pets, guardians, totems, minions, charmed units and vehicles credit their player (KC-D4); a creature with no
        // player behind it records nothing.
        Player* player = attacker->GetCharmerOrOwnerPlayerOrPlayerItself();
        if (!player)
            return;

        // Only the player's own hits carry a spell id: the C++ kill hooks read the spell (KC-D5).
        victim->CustomData.GetDefault<HitLog>(HIT_LOG_KEY)->Record(player->GetGUID(),
            attacker == player ? spellProto->Id : 0, GameTime::GetGameTimeMS());
    }

    void OnKill(Unit* killer, Unit* victim, SpellInfo const* killingSpell)
    {
        if (!victim)
            return;

        HitLog const* log = victim->CustomData.Get<HitLog>(HIT_LOG_KEY);
        if (!log)
            return;

        // Player-owned deaths keep stock behaviour (KC-D3); the unit may have been charmed after it was struck.
        if (victim->IsCharmedOwnedByPlayerOrPlayer())
        {
            victim->CustomData.Erase(HIT_LOG_KEY);
            return;
        }

        // Copy out, then erase before anything fires: a kill proc can damage or kill again, and a creature that
        // respawns (same object) must start with a clean log.
        std::vector<Assist> const assists = log->Collect(GameTime::GetGameTimeMS());
        victim->CustomData.Erase(HIT_LOG_KEY);

        // Who the stock block in Unit::Kill already gave PROC_FLAG_KILL: the killer, and the owner of a pet or totem
        // killer (guardians are not forwarded there). Each death runs at most one kill proc pass per player.
        Unit* stockOwner = nullptr;
        if (killer && (killer->IsPet() || killer->IsTotem()))
            stockOwner = killer->GetOwner();

        for (Assist const& assist : assists)
        {
            // Alive, in world, on the victim's map; no range, group or tap requirement (KC-D6).
            Player* player = ObjectAccessor::GetPlayer(*victim, assist.player);
            if (!player || !player->IsAlive())
                continue;

            // Kill procs, the pet-forward call shape. PROC_ATTR_REQ_EXP_OR_HONOR is checked per actor, so per
            // assister. Every PROC_FLAG_KILL aura fires (KC-D11). No ScriptMgr kill hook, reward, quest credit or
            // achievement is called here: quests, mod-playerbots and other modules listen there and would count the
            // kill twice.
            if (player != killer && player != stockOwner)
            {
                LOG_DEBUG("entities.unit.killcredit", "KillCredit: {} assisted the kill of {}",
                    player->GetGUID().ToString(), victim->GetGUID().ToString());
                Unit::ProcSkillsAndAuras(player, victim, PROC_FLAG_KILL, PROC_FLAG_NONE, PROC_EX_NONE, 0, BASE_ATTACK,
                    nullptr, nullptr, -1, nullptr);
            }

            // C++ kill hooks: only the player's own recorded spell (KC-D5). Frost Channeling and Rune of Unending
            // Thirst never credit a pet's or guardian's blow, and a pet hit carries no spell of the player's. The
            // killer itself is included (its earlier SW:D or Frostbolt when a DoT or swing landed the blow), but not
            // for the spell Unit::Kill already passes to the hooks (once per spell).
            if (!assist.ownSpellId)
                continue;

            if (player == killer && killingSpell && killingSpell->Id == assist.ownSpellId)
                continue;

            // Unit::Kill runs Mage::OnKill with the killing spell for the killer; when that is Frost it already pays
            // Frost Channeling, so the killer's older Frost spell must not pay it a second time (a Frost DoT tick
            // kill after an Ice Lance). Add the same "does stock already pay this" guard to any future hook.
            bool const stockPaysFrost = player == killer && killingSpell
                && (killingSpell->GetSchoolMask() & SPELL_SCHOOL_MASK_FROST);

            SpellInfo const* ownSpell = sSpellMgr->GetSpellInfo(assist.ownSpellId);
            if (!ownSpell)
                continue;

            if (!stockPaysFrost)
                Mage::OnKill(player, victim, ownSpell);
            // KC-D10: a non-killing SW:D took its backlash already; the assist is a kill for Deathspeaker as for
            // every other kill effect.
            Priest::OnKill(player, victim, ownSpell);
            // KC-D9: assists count for the rune. The killer's own blow reaches it through OnPlayerCreatureKill.
            if (player != killer)
                DeathKnight::OnRuneKillingBlow(player, victim);
        }
    }
}
