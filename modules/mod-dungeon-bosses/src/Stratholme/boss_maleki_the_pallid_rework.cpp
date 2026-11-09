/*
 * mod-dungeon-bosses, Stratholme S12:
 * Maleki the Pallid (10438).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S12 owns this file from now on. Wave 1 (the Service Entrance).
 *
 * What the stub does:
 * - a melee BossAI on BOSS_MALEKI (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (MalekiArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat maleki info`.
 *
 * TODO(WP-S12):
 * - ST 3160-3211; handoff section 3.5 row S12, section 3.6 (normal 170k, heroic 210k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: MK1 the frozen curse (the dispel condition on spacing, X1's DispelEntry::when), MK3 the
 *   staff (the Siphon run from a spot recorded at the cast), MK4 Ice Tomb (HoldInUnit; 300584, display 30890
 *   rescaled), MK5 the storm (RegistryHit), the eye (heroic, a Zone on a drifting stalker 300585; centres
 *   kMalekiEyeCenters, 11-13 yd at bearing 130-150 deg), faster Icy Death, Frostbite spread. Stock
 *   Frostbolt 17503 kept. Section 7 #18: lingering zones marked Weakened use WeakenedOncePerPlayer().
 * - Data: drop SmartAI 10438 x5. He keeps his stock flags_extra bit 0x4000000 (the stub sets it with
 *   INSTANCE_BIND). Texts per MalekiTexts (none stock). His plaza trash stands 10-11 yd from him: check it
 *   does not pull with him. His ziggurat (DATA_ZIGGURAT3) opens on his death by the instance.
 * - Host-testable logic in MalekiLogic.h (spell ids in kSpellsMaleki), one
 *   `.dbtest strat maleki <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
 *   registry calls of handoff section 3.4.
 * - Pilot lessons (handoff section 3.5): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit
 *   through LaunchTarget + SetEffectValue (tank hits too); every custom damage spell uses DungeonKit::RefFlat
 *   (DD never scales ids >= 200000); emotes are type 41; SaveToDB after a saved data change; no summoned unit in
 *   ObjectData; visuals and timers that must run during a cast never ride BossAI's paused scheduler; every hit
 *   has a visible impact; filled circles only for real threats; telegraph shapes match the room; spells that
 *   must clear on leaving carry CHANGE_MAP interrupt flags; one log category (DungeonKit::LogMechanic(
 *   kLogDungeon, ...)).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "MalekiLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "maleki";
}

struct boss_maleki_the_pallid_rework : public BossAI
{
    explicit boss_maleki_the_pallid_rework(Creature* creature)
        : BossAI(creature, BOSS_MALEKI), _arena(MalekiArena(), LeashOptions(kBossLogName)) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_MALEKI;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", DungeonKit::IsHeroicMap(me) ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _arena.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        events.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_MALEKI, BOSS_MALEKI);
    }

    ChatCommandTable const& MalekiTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_maleki_the_pallid_rework()
{
    RegisterDungeonReworkCreatureAI(boss_maleki_the_pallid_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("maleki", MalekiTestCommands());
}
