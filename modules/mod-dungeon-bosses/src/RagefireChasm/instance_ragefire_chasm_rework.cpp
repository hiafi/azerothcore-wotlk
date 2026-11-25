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

// The Ragefire Chasm build's instance script (handoff section 3.2, WP-S0), registered under the stock name
// `instance_ragefire_chasm` (section 7 #1 A): modules load after the core scripts, and a database-bound script
// registered later under the same name replaces the earlier one (ScriptRegistry::AddALScripts), so map 389's
// instance_template row is untouched and the stock InstanceMapScript (empty: no data, doors or save) is replaced at
// load. Nothing is mirrored from it.
//
// What it owns: the 5 boss states (RagefireChasmRework.h), Taragaman's gate (derived from the saved slots 0 to 2, never
// a flag of its own: section 7 #8 A), the hard mode flag with its kill slot and loot bit (section 3.2 item 4), and the
// "RFC" save string. The encounter credit and the Dungeon Finder completion stay the core's (instance_encounters
// 430-433, Map::UpdateEncounterState).

#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "GameTime.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "RagefireChasmKit.h"
#include "RagefireChasmRework.h"
#include "StringFormat.h"

using namespace RagefireChasmRework;

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");
static_assert(kMapRagefireChasm == MAP_RAGEFIRE_CHASM, "map 389");

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    // The four bosses, never summoned twice (cpp-scripts.md, the ObjectData pitfall); no summoned unit ever goes here.
    ObjectData const creatureData[] =
    {
        { NPC_OGGLEFLINT, kGuidBossBase + BOSS_OGGLEFLINT },
        { NPC_JERGOSH,    kGuidBossBase + BOSS_JERGOSH    },
        { NPC_BAZZALAN,   kGuidBossBase + BOSS_BAZZALAN   },
        { NPC_TARAGAMAN,  kGuidBossBase + BOSS_TARAGAMAN  },
        { 0,              0                               }
    };
}

class instance_ragefire_chasm_rework : public InstanceMapScript
{
public:
    instance_ragefire_chasm_rework() : InstanceMapScript(kInstanceScriptName, MAP_RAGEFIRE_CHASM) { }

    struct instance_ragefire_chasm_rework_InstanceMapScript : public InstanceScript
    {
        explicit instance_ragefire_chasm_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders(kSaveHeader);
            SetBossNumber(kBossCount);
            LoadObjectData(creatureData, nullptr);
        }

        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            switch (creature->GetEntry())
            {
                case NPC_OGGLEFLINT:
                    SettleDeadLieutenant(creature, BOSS_OGGLEFLINT);
                    break;
                case NPC_JERGOSH:
                    SettleDeadLieutenant(creature, BOSS_JERGOSH);
                    break;
                case NPC_BAZZALAN:
                    SettleDeadLieutenant(creature, BOSS_BAZZALAN);
                    break;
                default:
                    break;
            }

            if (creature->GetEntry() == NPC_TARAGAMAN)
            {
                // Every create re-derives the gate and the loot bit from the saved slots: a load stores the states
                // without running SetBossState's switch, so nothing else would (and no yell plays on a load).
                ApplyTaragamanGate(creature);
                ApplyHardModeLoot(creature);
            }
        }

        bool SetBossState(uint32 id, EncounterState state) override
        {
            // Loading, or a slot's first write (BossAI::_Reset's NOT_STARTED): the base stores it onto TO_BE_DECIDED
            // and returns false, so neither the gate's yell nor the kill slot below can fire from it.
            if (!InstanceScript::SetBossState(id, state))
                return false;

            switch (id)
            {
                case BOSS_OGGLEFLINT:
                case BOSS_JERGOSH:
                case BOSS_BAZZALAN:
                    if (GateOpensOn(id, state, States()))
                        OpenGate();
                    else
                        RefreshGate();      // a GM slot write may close it again (never on a fighting Taragaman)
                    break;
                case BOSS_TARAGAMAN:
                    if (state == DONE)
                    {
                        // His loot is already filled (Unit::Kill, before JustDied), hard mode item included, so the
                        // loot bit is left alone here. A first-time state on a slot the first Update has not settled
                        // is stored but not saved, so save explicitly or a reload loses the kill flag (RB-2).
                        if (_hardMode)
                        {
                            SetBossState(BOSS_STARVING, DONE);
                            SaveToDB();
                        }
                        break;
                    }
                    // The pull (BossAI::_Reset cleared the loot mode), a wipe, an evade.
                    ApplyHardModeLoot();
                    if (state != IN_PROGRESS)
                        RefreshGate();
                    break;
                default:
                    break;
            }
            return true;
        }

        void SetData(uint32 type, uint32 data) override
        {
            switch (type)
            {
                case DATA_HARD_MODE:
                {
                    // Starving (section 7 #17 A): heroic only, at any gate state, never once Taragaman is engaged or
                    // dead. Saved; it holds through wipes and reloads, an instance reset clears it. The pour GO (D4H)
                    // reads GetData(DATA_HARD_MODE) back to know whether its pour counted.
                    uint32 const value = data ? 1 : 0;
                    if (!HardModeChangeAllowed(instance->IsHeroic(), SlotState(BOSS_TARAGAMAN), value))
                    {
                        LOG_INFO(kLog, "rfc instance hardmode refused value={} heroic={} taragaman={}", value,
                            instance->IsHeroic() ? 1 : 0, SlotState(BOSS_TARAGAMAN));
                        break;
                    }
                    if (value == _hardMode)
                        break;
                    _hardMode = value;
                    ApplyHardModeLoot();
                    SaveToDB();
                    DungeonKit::LogMechanic(kLogDungeon, "instance", "hardmode", value ? "armed" : "cleared");
                    ActionToTaragaman(value ? ACTION_RFC_HARD_MODE_ARMED : ACTION_RFC_HARD_MODE_CLEARED);
                    break;
                }
                default:
                    break;
            }
        }

        uint32 GetData(uint32 type) const override
        {
            switch (type)
            {
                case DATA_HARD_MODE:
                    return _hardMode;
                case DATA_HARD_MODE_KILLED:
                    return GetBossState(BOSS_STARVING) == DONE ? 1 : 0;
                case DATA_GATE_OPEN:
                    return GateOpen(States()) ? 1 : 0;
                case DATA_TARAGAMAN_DORMANT:
                    return TaragamanDormant(States()) ? 1 : 0;
                default:
                    return 0;
            }
        }

        void Update(uint32 diff) override
        {
            InstanceScript::Update(diff);

            // The first Update (Load, if any, ran before it): every slot still TO_BE_DECIDED becomes NOT_STARTED, so a
            // later live write (a kill, a GM's) always runs the switch and is saved.
            if (_settled)
                return;
            _settled = true;
            for (uint32 i = 0; i < kBossCount; ++i)
                if (GetBossState(i) == TO_BE_DECIDED)
                    SetBossState(i, NOT_STARTED);
        }

        std::string GetSaveData() override
        {
            RfcSave save;
            save.states = States();
            save.hardMode = _hardMode;
            return FormatRfcSave(save);
        }

        void Load(char const* in) override
        {
            if (!in)
                return;

            RfcSave save;
            if (!ParseRfcSave(in, save))
            {
                LOG_DEBUG(kLog, "rfc instance: ignored save '{}'", in);
                return;
            }

            for (uint32 i = 0; i < kBossCount; ++i)
                SetBossState(i, EncounterState(save.states[i]));
            // After the states: the flag never fires BOSS_TARAGAMAN's DONE branch while loading.
            _hardMode = save.hardMode;
        }

    private:
        // A slot's state, TO_BE_DECIDED read as NOT_STARTED (before the first Update settles it).
        uint32 SlotState(uint32 id) const
        {
            EncounterState const state = GetBossState(id);
            return state == TO_BE_DECIDED ? uint32(NOT_STARTED) : uint32(state);
        }

        BossStates States() const
        {
            BossStates states{};
            for (uint32 i = 0; i < kBossCount; ++i)
                states[i] = SlotState(i);
            return states;
        }

        Creature* Taragaman()
        {
            return GetCreature(kGuidBossBase + BOSS_TARAGAMAN);
        }

        void RefreshGate()
        {
            ApplyTaragamanGate(Taragaman());
        }

        // A lieutenant loaded dead with his slot not DONE (DeadLoadSettles). A respawn time already past is no death:
        // he loads dead and respawns on his first update. The base write, so no gate yell plays on a load; a GM's
        // respawn writes the slot back through his Reset as always (a GM's `.instance setbossstate <slot> 0` alone does
        // not: with his corpse or respawn row still there the next map load writes DONE again; respawn him first).
        void SettleDeadLieutenant(Creature* creature, uint32 slot)
        {
            if (creature->IsAlive() || creature->GetRespawnTime() <= GameTime::GetGameTime().count()
                || !DeadLoadSettles(slot, SlotState(slot)))
                return;
            InstanceScript::SetBossState(slot, DONE);
            DungeonKit::LogMechanic(kLogDungeon, "instance", "dead-load", Acore::StringFormat("slot={} gate={}", slot,
                GateOpen(States()) ? "open" : "closed"));
            RefreshGate();
        }

        // The third lieutenant died (live): the flags clear and Taragaman yells line 0 across the zone. With his
        // creature not loaded nothing plays; his create applies the open gate.
        void OpenGate()
        {
            DungeonKit::LogMechanic(kLogDungeon, "instance", "gate", "open");
            Creature* taragaman = Taragaman();
            if (!taragaman || !taragaman->IsAlive())
                return;
            ApplyTaragamanGate(taragaman);
            if (taragaman->IsAIEnabled && taragaman->AI())
            {
                taragaman->AI()->Talk(YELL_TARAGAMAN_GATE);
                taragaman->AI()->DoAction(ACTION_RFC_GATE_OPENED);
            }
        }

        void ActionToTaragaman(int32 action)
        {
            Creature* taragaman = Taragaman();
            if (taragaman && taragaman->IsAlive() && taragaman->IsAIEnabled && taragaman->AI())
                taragaman->AI()->DoAction(action);
        }

        // Item variants IV7 (the Deadmines pattern): his heroic lootid holds the hard mode list in group 2 with
        // LootMode 2 (LOOT_MODE_HARD_MODE_1). Unit::Kill fills the loot with the creature's loot mode before JustDied,
        // so the bit rides his loot mode while the flag is lit and he is not dead; BossAI::_Reset clears it and the
        // pull sets it again.
        void ApplyHardModeLoot(Creature* taragaman = nullptr)
        {
            if (!taragaman)
                taragaman = Taragaman();
            if (!taragaman)
                return;
            DungeonKit::SetHardModeLoot(taragaman, HardModeLootLit(_hardMode, SlotState(BOSS_TARAGAMAN)));
        }

        uint32 _hardMode = 0;
        bool _settled = false;
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_ragefire_chasm_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_ragefire_chasm_rework()
{
    new instance_ragefire_chasm_rework();
}
