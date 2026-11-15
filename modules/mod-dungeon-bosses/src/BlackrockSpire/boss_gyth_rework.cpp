/*
 * mod-dungeon-bosses, Blackrock Spire B12:
 * Gyth (10339), Rend's drake (one encounter with Warchief Rend Blackhand: boss_rend_blackhand_rework.cpp).
 * STUB written by WP-S0 (the Blackrock Spire skeleton); WP-B12 owns this file from now on. Wave 2 (Upper Blackrock
 * Spire): the AI registers only once wave 2 flips kWave2Bound / BIND_WAVE_2; its `.dbtest brs gyth` table registers
 * now.
 *
 * What the stub does: a melee BossAI on BOSS_GYTH, the flex pull, the registry encounter, the arena leash
 * (RendGythArena), a death log line and `.dbtest brs gyth info`.
 *
 * TODO(WP-B12): see boss_rend_blackhand_rework.cpp; spell ids in RendGythLogic.h (kSpellsRendGyth). He is summoned
 * behind the drake portcullis (kGythSummon) and hovers at kGythHoverGround; RG9 Rend's Mark, RG10 riderless Gyth,
 * RG16 Corrosive Acid at 10 players (the TS swap; heroic the tanks trade Gyth and Rend). Stock Corrosive Acid Breath
 * 16359, Knock Away 10101, Chromatic Protection kept. The stock boss_gyth (FAIL writes for Rend, the Rend dismount)
 * stays registered, unbound by the DT file once wave 2 binds.
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "RendGythLogic.h"
#include "ScriptedCreature.h"

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;

namespace
{
    char const* const kGythLogName = "gyth";
}

struct boss_gyth_rework : public BossAI
{
    explicit boss_gyth_rework(Creature* creature)
        : BossAI(creature, BOSS_GYTH), _arena(RendGythArena(), LeashOptions(kGythLogName)) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
        _players = 0;
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _players = OnBossPull(me, kGythLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GYTH;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
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
        DungeonKit::LogMechanic(kLogDungeon, kGythLogName, "death");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;

        events.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
    uint8 _players = 0;
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_GYTH, BOSS_GYTH);
    }

    ChatCommandTable const& GythTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_gyth_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_gyth_rework, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("gyth", GythTestCommands());
}
