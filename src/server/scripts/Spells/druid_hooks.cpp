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
 * Druid rework - every ScriptMgr hook (as opposed to a SpellScript/AuraScript bound to one spell
 * id) the three passes need, in one file (.agents/plans/druid-rework/druid-rework.CORE-AUDIT.md's
 * top summary): UnitScript (ModifySpellDamageTaken, ModifyMeleeDamage,
 * ModifyPeriodicDamageAurasTick, OnAuraApply, OnAuraRemove), GlobalScript
 * (OnSpellHealingBonusTakenNegativeModifiers), AllSpellScript (CanPrepare, OnSpellPrepare),
 * PlayerScript (OnPlayerAfterUpdateMaxHealth). These run on every damage/heal event for every
 * class server-wide - every handler here MUST check for a druid caster/target first before doing
 * anything (CORE-AUDIT's own warning, repeated in PLAN §11 "Risks").
 *
 * Created empty by the Balance pass's WP-0 (PLAN §5.1); WP-B adds Balance's own row (CORE-AUDIT
 * row 9, B6's Moonkin heal-cancel AllSpellScript::OnSpellPrepare, only if the in-game check says
 * the client doesn't already auto-unshift - PLAN §6 item 8). Resto (rows 11-21) and Feral (rows
 * 22-35) extend this same file with their own handlers in their own passes.
 */

#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "UnitDefines.h"

/*
 * B6 - "Casting any healing spell cancels Moonkin Form" (PLAN §1B row B6, CORE-AUDIT row 9,
 * BALANCE.md §0.5/§11.5). The user's own rule for this row is to verify in game whether the
 * 3.3.5a client already auto-unshifts Moonkin Form on a blocked heal cast before building a
 * server-side fallback; this pass has no build/deploy/playtest access, so that in-game check
 * could not be performed. Built anyway per the WP-B brief's explicit instruction (the "likely
 * yes" default from PLAN's own B6 row is stated there as not being sufficient on its own) -
 * CORE-AUDIT row 9 recommends shipping this AllSpellScript::OnSpellPrepare fallback regardless,
 * and it can be ripped out later by whoever runs that check if the client turns out to already
 * handle it. Report this explicitly to WP-C/the user so that decision gets made.
 *
 * CORE-AUDIT row 9's own evidence: for an instant-cast heal, OnSpellPrepare fires *after*
 * Spell::prepare() has already called cast(true) (Spell.cpp:3809-3816), so removing Moonkin Form
 * here cannot stop that particular cast's heal from landing while still shapeshifted - the heal
 * itself has already resolved. What this still buys: the form drops immediately afterwards (so a
 * follow-up heal, or anything else gated on "not in Moonkin", works correctly), and for any heal
 * with a real cast time the form drops before the cast bar completes. WP-A's own job (not this
 * file's) is dropping/adjusting the Moonkin StancesNot bit on the druid heal spells themselves
 * (PLAN §11.5) so they're castable at all while shapeshifted for this hook to have anything to
 * remove.
 */
class DruidMoonkinHealCancel : public AllSpellScript
{
public:
    DruidMoonkinHealCancel() : AllSpellScript("DruidMoonkinHealCancel", { ALLSPELLHOOK_ON_PREPARE }) { }

    void OnSpellPrepare(Spell* spell, Unit* caster, SpellInfo const* spellInfo) override
    {
        if (!caster || !spellInfo || !spell)
            return;

        // Every druid/heal event server-wide reaches this hook (CORE-AUDIT's own warning,
        // PLAN §11 "Risks") - gate on a druid player in Moonkin Form before doing anything else.
        Player* player = caster->ToPlayer();
        if (!player || player->getClass() != CLASS_DRUID)
            return;

        if (player->GetShapeshiftForm() != FORM_MOONKIN)
            return;

        // "Non-triggered heal": a real player cast (not a proc/DoT-tick trigger) of a druid spell
        // that either heals directly (Healing Touch, Regrowth's direct part, Swiftmend, ...) or
        // applies a periodic heal (Rejuvenation, Lifebloom, Wild Growth, Tranquility, ...).
        if (spell->IsTriggered())
            return;

        if (spellInfo->SpellFamilyName != SPELLFAMILY_DRUID)
            return;

        if (!spellInfo->HasEffect(SPELL_EFFECT_HEAL) && !spellInfo->HasAura(SPELL_AURA_PERIODIC_HEAL))
            return;

        player->RemoveAurasByType(SPELL_AURA_MOD_SHAPESHIFT);
    }
};

void AddSC_druid_hooks()
{
    new DruidMoonkinHealCancel();
}
