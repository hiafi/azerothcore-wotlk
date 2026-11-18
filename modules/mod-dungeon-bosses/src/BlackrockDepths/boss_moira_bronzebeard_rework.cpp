/*
 * mod-dungeon-bosses, Blackrock Depths D23: Princess Moira Bronzebeard (8929) and the High Priestess of Thaurissan
 * (10076), one AI on both (S4: "the High Priestess swap: Keep, with Moira's new kit"). Build spec S4 "Emperor Dagran
 * Thaurissan" (docs/dungeons/blackrock-depths-4-imperial-seat.md, EM2, EM4, EM5; rulings 77-80), handoff section 7
 * #19. Replaces stock `boss_moira_bronzebeard` and `boss_high_priestess_thaurissan` (Heal, Renew, the Priestess's
 * Shadow Word: Pain and Shadow Bolt are gone). Bound by apps/dbc-tools source/npcs/blackrock_depths/emperor.py. The
 * fight's clock is Dagran's (boss_emperor_dagran_thaurissan_rework.cpp): he tells her when to channel Nemesis and on
 * whom to cast Necrosis; her own beat is Mind Blast. Pure rules: EmperorLogic.h.
 *
 *   She roots at her spot on the dais for the whole fight (section 7 #19; she never chases): Mind Blast on her target
 *   (a copy of 15587, 1.5 s, interruptible: a reward) 8 s in, then every 14-18 s, and her melee when someone stands at
 *   her. Pulling either one pulls both; either one evading sends the other home.
 *   EM2  Nemesis      on his word: her 8 s channel into him (emote 1), not interruptible; he judges the beam
 *   EM5  Necrosis     (heroic) on his word: the DoT on the player he names
 *   The enrage        her death tells him (ACTION_EM_MOIRA_DIED)
 *   The cage          the hard mode's transition (EmperorFight.h step 2): the fire cage at her base and its whirl,
 *                     not selectable, no damage taken, passive, kept in combat, nothing cast, until the cage breaks
 *                     or the fight ends
 *   The stand-down    his death: she evades, says the stock line (Moira only) and turns friendly (faction 35,
 *                     passive). The instance keeps her so on every load once he is DONE or she was saved (section
 *                     7 #19; the stock MoiraGUID bug, which left the Priestess hostile, is fixed by DATA_MOIRA)
 *
 * Her loot (lootid 8929, shared with the Priestess) is emptied into Dagran's list by L-2. Every firing logs one INFO
 * line "brd moira <mechanic> ..." (module.dungeonbosses).
 */

#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "EmperorLogic.h"
#include "InstanceScript.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdEmperor;

namespace
{
    char const* const kBoss = "moira";

    uint32 constexpr kPullZoneYd = 60;

    void LogMo(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }
}

// A ScriptedAI: the slot (BOSS_EMPEROR) and the registry encounter are Dagran's; she is a unit of his encounter.
struct boss_moira_bronzebeard_rework : public ScriptedAI
{
    explicit boss_moira_bronzebeard_rework(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        ScriptedAI::Reset();
        me->SetCombatMovement(false);       // rooted at her spot for the whole fight (section 7 #19)
        Uncage();
        _clockMs = 0;
        _mindBlastMs = 0;
        _standingDown = StandsDown();
        if (_standingDown)
        {
            // The instance made her friendly on create; keep it so after an evade (no fight, no beat).
            me->SetFaction(kFactionFriend);
            me->SetReactState(REACT_PASSIVE);
        }
    }

    void JustEngagedWith(Unit* who) override
    {
        if (_standingDown || _caged)
            return;
        _mindBlastMs = _clockMs + kMindBlastFirstMs;
        if (me->GetEntry() == NPC_PRIESTESS)
            Talk(YELL_PRIESTESS_AGGRO);     // stock (Moira has no aggro line)
        // Moira first: the whole room joins her threat list, as Dagran's pull does for her. Otherwise the puller
        // dying, vanishing or feigning death empties her list and her evade takes Dagran home mid-fight (R-2-C m3).
        // Safe while caged: the cage path never reaches UpdateVictim.
        DoZoneInCombat(me, kPullZoneYd);
        // Pulling her pulls him (his JustEngagedWith tracks her in his encounter).
        if (Creature* dagran = Dagran())
            if (dagran->IsAlive() && !dagran->IsInCombat() && dagran->IsAIEnabled)
            {
                if (who)
                    dagran->AI()->AttackStart(who);
                dagran->AI()->DoZoneInCombat(dagran, kPullZoneYd);
            }
        LogMo("engage", Acore::StringFormat("entry={} mindblast={}s", me->GetEntry(), kMindBlastFirstMs / 1000));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Uncage();
        ScriptedAI::EnterEvadeMode(why);
        // The fight is one encounter: he goes home with her.
        if (Creature* dagran = Dagran())
            if (dagran->IsAlive() && dagran->IsInCombat() && dagran->IsAIEnabled && !dagran->IsInEvadeMode())
                dagran->AI()->EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Uncage();
        // EM8: he enrages.
        if (Creature* dagran = Dagran())
            if (dagran->IsAlive() && dagran->IsAIEnabled)
                dagran->AI()->DoAction(ACTION_EM_MOIRA_DIED);
        LogMo("death", Acore::StringFormat("entry={} killer={}", me->GetEntry(),
            killer ? killer->GetName() : std::string("none")));
    }

    // Caged, nothing hurts her (an area hit would still reach a not-selectable unit): she cannot die in the hard mode.
    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (_caged)
            damage = 0;
    }

    void DoAction(int32 action) override
    {
        switch (action)
        {
            case ACTION_EM_NEMESIS:
                Nemesis();
                break;
            case ACTION_EM_CAGE:
                Cage();
                break;
            case ACTION_EM_UNCAGE:
                Uncage();
                break;
            case ACTION_EM_STOP:
                me->InterruptNonMeleeSpells(false);
                break;
            case ACTION_EM_STAND_DOWN:
                StandDown();
                break;
            default:
                break;
        }
    }

    // EM5 (heroic): Necrosis on the player Dagran names (triggered: it does not break a Nemesis channel).
    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id != GUID_EM_NECROSIS || _caged || _standingDown || !me->IsAlive())
            return;
        if (Player* target = ObjectAccessor::GetPlayer(*me, guid))
            me->CastSpell(target, SPELL_EM_NECROSIS, true);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (_caged || _standingDown)
            return;         // caged: in combat, idle (EmperorFight.h step 2); Dagran's evade or death ends it
        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_mindBlastMs && _clockMs >= _mindBlastMs)
            _mindBlastMs = MindBlast() ? _clockMs + urand(kMindBlastEveryMinMs, kMindBlastEveryMaxMs)
                : _clockMs + kRetryMs;
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Her kit
    // ----------------------------------------------------------------------------------------------------------------

    // EM4: the 1.5 s cast on her target, in 30 yd and in sight. False: nobody, or refused (her school locked).
    bool MindBlast()
    {
        Unit* target = me->GetVictim();
        if (!target || me->GetExactDist2d(target) > kMindBlastRangeYd || !me->IsWithinLOSInMap(target))
            return false;
        if (me->CastSpell(target, SPELL_EM_MIND_BLAST, false) != SPELL_CAST_OK)
            return false;
        LogMo("mind-blast", Acore::StringFormat("on={}", target->GetName()));
        return true;
    }

    // EM2: the channel into him and the emote (he registers the bots' Soak and judges the ticks).
    void Nemesis()
    {
        Creature* dagran = Dagran();
        if (_caged || _standingDown || !dagran || !dagran->IsAlive() || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (me->CastSpell(dagran, SPELL_EM_NEMESIS, false) != SPELL_CAST_OK)
            return;
        Talk(EMOTE_MOIRA_NEMESIS);
    }

    // The hard mode's cage: the fire ring at her base and its whirl (lasting auras of her own), not selectable,
    // passive, nothing cast; still in combat (her threat list stays), so the fight does not end around her.
    void Cage()
    {
        if (_caged || !me->IsAlive())
            return;
        _caged = true;
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->CastSpell(me, SPELL_EM_MOIRA_CAGE, true);
        me->CastSpell(me, SPELL_EM_MOIRA_CAGE_WHIRL, true);
        LogMo("caged");
    }

    void Uncage()
    {
        if (!_caged)
            return;
        _caged = false;
        me->RemoveAurasDueToSpell(SPELL_EM_MOIRA_CAGE);
        me->RemoveAurasDueToSpell(SPELL_EM_MOIRA_CAGE_WHIRL);
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        if (!_standingDown)
            me->SetReactState(REACT_AGGRESSIVE);
        LogMo("uncaged");
    }

    // His death (stock, the order kept: evade, the line, the faction). The instance repeats the faction on every
    // load (ApplyMoiraStandDown).
    void StandDown()
    {
        if (!me->IsAlive() || _standingDown)
            return;
        Uncage();
        me->InterruptNonMeleeSpells(false);
        _standingDown = true;
        if (me->IsInCombat())
            EnterEvadeMode(EVADE_REASON_OTHER);
        if (me->GetEntry() == NPC_MOIRA)
            Talk(EMOTE_MOIRA_STANDS_DOWN);
        me->SetFaction(kFactionFriend);
        me->SetReactState(REACT_PASSIVE);
        LogMo("stands-down", Acore::StringFormat("entry={}", me->GetEntry()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // State
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Dagran() const
    {
        InstanceScript* instance = me->GetInstanceScript();
        ObjectGuid const guid = instance ? instance->GetGuidData(DATA_EMPEROR) : ObjectGuid::Empty;
        return guid ? ObjectAccessor::GetCreature(*me, guid) : nullptr;
    }

    // Dagran is DONE, or the Avatar kill saved her (section 7 #19).
    bool StandsDown() const
    {
        InstanceScript* instance = me->GetInstanceScript();
        return instance && MoiraStandsDown(instance->GetBossState(BOSS_EMPEROR),
            instance->GetData(DATA_MOIRA_SAVED) != 0);
    }

    std::string TestState() const
    {
        return Acore::StringFormat("moira entry={} caged={} standing-down={} combat={} channeling={} mindblast={}",
            me->GetEntry(), _caged ? 1 : 0, _standingDown ? 1 : 0, me->IsInCombat() ? 1 : 0,
            me->GetCurrentSpell(CURRENT_CHANNELED_SPELL) ? 1 : 0,
            _mindBlastMs ? std::to_string(_mindBlastMs > _clockMs ? (_mindBlastMs - _clockMs) / 1000 : 0) + "s"
                : std::string("-"));
    }

private:
    uint64 _clockMs = 0;
    uint64 _mindBlastMs = 0;
    bool _caged = false;
    bool _standingDown = false;
};

namespace
{
    // The princess on the dais (Moira, or the High Priestess standing in).
    Creature* FindPrincess(ChatHandler* handler)
    {
        if (Creature* moira = BrdTest::FindBoss(handler, NPC_MOIRA))
            return moira;
        return BrdTest::FindBoss(handler, NPC_PRIESTESS);
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_MOIRA, BOSS_EMPEROR);
    }

    // `.dbtest brd moira state`: her cage, her stand-down, her Mind Blast clock.
    bool HandleState(ChatHandler* handler)
    {
        Creature* princess = FindPrincess(handler);
        auto* ai = princess && princess->IsAIEnabled ? dynamic_cast<boss_moira_bronzebeard_rework*>(princess->AI())
            : nullptr;
        if (!ai)
        {
            if (princess)
                handler->SendErrorMessage("{} does not run the reworked script.", princess->GetName());
            return false;
        }
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    ChatCommandTable const& BossMoiraBronzebeardTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",  HandleInfo,  SEC_GAMEMASTER, Console::No },
            { "state", HandleState, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_moira_bronzebeard_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_moira_bronzebeard_rework, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("moira", BossMoiraBronzebeardTestCommands());
}
