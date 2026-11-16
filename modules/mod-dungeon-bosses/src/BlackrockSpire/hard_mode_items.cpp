/*
 * mod-dungeon-bosses, Blackrock Spire: the Overlord Wyrmthalak and General Drakkisath hard mode item effects (wave 2
 * dungeon items; designer text: docs/dungeons/blackrock-spire-rework.md "Hard mode"). The spells are
 * apps/dbc-tools/source/items/blackrock_spire_hard_mode_effects.py. None of the effects deals damage or heals, so
 * nothing here sizes a hit, and none scales by item level (every number is a percent or a time): there are no tier
 * copies and no script resolves one. Four of the six effects are data only (a Use spell, or a PROC_TRIGGER_SPELL aura
 * onto a stacking buff or debuff): the Bloodaxe War Horn, the Shardstaff of Stolen Power, Orders of the General and
 * The Humbler have no script.
 *
 *   spell_brs_ward_of_the_three_tribes    206802 Ward of the Three Tribes (Equip). Every 0.5 s the stacks of 206803 on
 *                                         the wearer are set to the number of enemies within the aura's radius that
 *                                         are attacking the wearer (at most the aura's amount); none removes the buff.
 *   spell_brs_champions_mark              206807 Champion's Mark (the 5 s debuff the Trophy's proc puts on the enemies
 *                                         its wearer damages). When it ends because its target died, the wearer, if
 *                                         alive and still wearing the Trophy, gets 206808.
 *
 * Every effect logs one DEBUG line, "brs-items <effect> ...", in module.dungeonbosses.
 */

#include "BlackrockSpireHardModeItemsLogic.h"
#include "CellImpl.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"
#include <list>

using namespace BlackrockSpireHardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    // Every living enemy of `attacker` within `radius` yards of `center`.
    std::list<Unit*> EnemiesNear(WorldObject* center, Unit* attacker, float radius)
    {
        std::list<Unit*> found;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(center, attacker, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(center, found, check);
        Cell::VisitObjects(center, searcher, radius);
        found.remove_if([attacker](Unit* unit) { return !unit->IsAlive() || !attacker->IsValidAttackTarget(unit); });
        return found;
    }
}

// 206802 Ward of the Three Tribes: one stack of 206803 per enemy attacking the wearer within the radius.
class spell_brs_ward_of_the_three_tribes : public AuraScript
{
    PrepareAuraScript(spell_brs_ward_of_the_three_tribes);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARD_BUFF });
    }

    void HandleWatch(AuraEffect const* aurEff)
    {
        Unit* wearer = GetTarget();
        if (!wearer->IsAlive() || !wearer->IsInWorld())
        {
            wearer->RemoveAurasDueToSpell(SPELL_WARD_BUFF);
            return;
        }

        float const radius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(wearer);
        uint32 attackers = 0;
        for (Unit* enemy : EnemiesNear(wearer, wearer, radius))
            if (enemy->IsInCombat() && enemy->GetVictim() == wearer)
                ++attackers;

        uint32 const stacks = WardStacks(attackers, aurEff->GetAmount());
        if (!stacks)
        {
            wearer->RemoveAurasDueToSpell(SPELL_WARD_BUFF);
            return;
        }

        // The buff's own stack cap (CumulativeAura 5) matches the aura's amount; the helper never exceeds the amount.
        Aura* buff = wearer->GetAura(SPELL_WARD_BUFF);
        if (!buff)
            buff = wearer->AddAura(SPELL_WARD_BUFF, wearer);
        if (!buff)
            return;
        if (buff->GetStackAmount() != stacks)
            buff->SetStackAmount(uint8(stacks));
        buff->RefreshDuration();
        LOG_DEBUG(kLog, "brs-items ward {}: {} attacking, {} stacks", wearer->GetGUID().ToString(), attackers,
            stacks);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_brs_ward_of_the_three_tribes::HandleWatch, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 206807 Champion's Mark: ending because the target died gives the wearer a Trophy.
class spell_brs_champions_mark : public AuraScript
{
    PrepareAuraScript(spell_brs_champions_mark);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_CHAMPIONS_TROPHY });
    }

    void HandleRemove(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        AuraApplication const* application = GetTargetApplication();
        bool const byDeath = application && application->GetRemoveMode() == AURA_REMOVE_BY_DEATH;
        if (!byDeath)
            return;

        Unit* caster = GetCaster();
        Player* wearer = caster ? caster->ToPlayer() : nullptr;
        if (!wearer || !wearer->IsInWorld())
            return;
        if (!ChampionEarnsTrophy(byDeath, wearer->IsAlive(), wearer->HasAura(SPELL_TROPHY_OF_THE_CHAMPION)))
            return;

        // One more stack (the spell data caps it at 5) and a fresh duration.
        wearer->CastSpell(wearer, SPELL_CHAMPIONS_TROPHY, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "brs-items trophy {} earned a Trophy: {} died", wearer->GetGUID().ToString(),
            GetTarget()->GetGUID().ToString());
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_brs_champions_mark::HandleRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_brs_hard_mode_items()
{
    RegisterSpellScript(spell_brs_ward_of_the_three_tribes);
    RegisterSpellScript(spell_brs_champions_mark);
}
