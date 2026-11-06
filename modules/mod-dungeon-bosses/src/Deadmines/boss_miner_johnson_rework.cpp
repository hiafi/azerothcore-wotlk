/*
 * mod-dungeon-bosses, Deadmines: Miner Johnson and the Working Miners (WP-B2). Build spec: DM 'Miner Johnson' Build
 * spec MJ1-MJ5; handoff section 3.4 (MJ rows), 3.5 (B2), 7 #3, #9, #13-#15.
 *
 *   MJ1 Payday       registry Soak (2 yd, 1 body, non-tank) 3 yd in front of a random digging Working Miner; 1 pouch
 *                    (2.5 s) normal, 2 pouches on different miners (2 s) heroic; first 8 s, every 20 s; stops (emote
 *                    line 2) when nobody digs. Marker: the encounter's get-in blue circle plus the gold glint
 *                    (spell 205231, SV 737) on the miner; the pouch missile (205230) lands as the Soak resolves.
 *   MJ2 Pocketed     caught: the eligible player nearest the spot casts 205232 on himself (+15% damage, 15 s).
 *   MJ3 Paid miner   missed: that miner emotes (line 0), becomes selectable and fights (stock Pierce Armor 6016).
 *   MJ4 Pierce Armor stock 12097 on the tank, 1-7 s then every 20-25 s, the aura cut to 10 s (ShortenAura).
 *   MJ5 Gold Fever   heroic, below 30%: 205233 (+30% attack speed, SV 47) and the gold tint 205234 (SV 11903).
 *
 * The crew is summoned by Johnson (never spawned, never in the instance's ObjectData: cpp-scripts.md), so the
 * instance's 40% roll (DATA_JOHNSON_ROLL, handoff section 7 #15) takes them too; Johnson re-checks the roll when he
 * respawns (a respawn does not pass the instance's OnCreatureCreate in respawn compatibility mode).
 */

#include "Chat.h"
#include "DeadminesKit.h"
#include "DeadminesTestCommand.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MinerJohnsonLogic.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "TemporarySummon.h"
#include <array>
#include <vector>

using namespace Acore::ChatCommands;
using namespace DeadminesRework;
using namespace MinerJohnson;

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    // Working Miner AI ids (DoAction / GetData).
    enum WorkingMinerIds : int32
    {
        ACTION_MINER_PAY    = 1,
        DATA_MINER_PAID     = 1,
    };

    Position ToEnginePos(Pose const& p)
    {
        return Position(p.x, p.y, p.z, p.o);
    }

    // The floor under a frame point near `z` (the Soak's anchor); `z` when the map has no height there.
    Position FloorPosition(Map const* map, uint32 phaseMask, Vec2 p, float z)
    {
        float floor = map ? map->GetHeight(phaseMask, p.x, p.y, z + 2.f) : INVALID_HEIGHT;
        if (floor <= INVALID_HEIGHT || std::fabs(floor - z) > 5.f)
            floor = z;
        return Position(p.x, p.y, floor, 0.f);
    }

    bool IsPaid(Creature const* miner)
    {
        return miner && miner->IsAIEnabled && miner->AI() && miner->AI()->GetData(DATA_MINER_PAID) != 0;
    }
}

// Miner Johnson 3586
struct boss_miner_johnson_rework : public BossAI
{
    explicit boss_miner_johnson_rework(Creature* creature) : BossAI(creature, BOSS_MINER_JOHNSON) { }

    void Reset() override
    {
        _Reset();
        if (!me->IsAlive() || me->IsEngaged())
            return;
        for (CrewSlot& slot : _crew)
            slot = {};
        _nobodyLeftSaid = false;
        // The crew comes once the instance's roll settled (an absent Johnson despawns 500 ms after his create).
        me->m_Events.AddEventAtOffset([this]() { SetUpCrew(false); }, Milliseconds(kCrewSetupDelayMs));
    }

    void JustRespawned() override
    {
        // K report section 1.3: a respawn does not pass OnCreatureCreate (compatibility mode), so the saved roll is
        // checked here too.
        if (IsRolledAbsent())
        {
            LOG_INFO(kLog, "dm-pilot johnson roll absent on respawn: despawned");
            me->DespawnOrUnsummon(500ms);
            return;
        }
        Reset();
    }

    void JustSummoned(Creature* summon) override
    {
        // Not BossAI's: a digging miner must not be zoned into the fight.
        summons.Summon(summon);
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        BossAI::SummonedCreatureDespawn(summon);
        ForgetMiner(summon->GetGUID());
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        ForgetMiner(summon->GetGUID());
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _JustEngagedWith();
        Talk(SAY_JOHNSON_AGGRO);

        BossMechanics::EncounterOptions options;
        options.getIn = BossMechanics::Color::Blue;     // handoff section 7 #13: Payday in the get-in blue
        options.bossStateId = BOSS_MINER_JOHNSON;
        Mechanic::BeginEncounter(me, options);
        DescribeEncounter();
        for (CrewSlot const& slot : _crew)
            if (Creature* miner = me->GetMap()->GetCreature(slot.guid))
                Mechanic::TrackUnit(me, miner);

        if (kGoldFeverBelowPct(DeadminesKit::IsHeroicMap(me)))
            ScheduleHealthCheckEvent(kGoldFeverBelowPct(DeadminesKit::IsHeroicMap(me)), [this]() { GoldFever(); });
    }

    void ScheduleTasks() override
    {
        scheduler.Schedule(Milliseconds(kPaydayFirstMs), [this](TaskContext context)
        {
            if (Payday())
                context.Repeat(Milliseconds(kPaydayEveryMs));
        });
        scheduler.Schedule(randtime(Milliseconds(kPierceFirstMinMs), Milliseconds(kPierceFirstMaxMs)),
            [this](TaskContext context)
        {
            DoCastVictim(SPELL_PIERCE_ARMOR);
            context.Repeat(randtime(Milliseconds(kPierceEveryMinMs), Milliseconds(kPierceEveryMaxMs)));
        });
    }

    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        // MJ4 (handoff section 7 #3): the stock spell, so DD scales it on heroic; only the aura is cut.
        if (spell->Id == SPELL_PIERCE_ARMOR
            && DeadminesKit::ShortenAura(target, SPELL_PIERCE_ARMOR, me->GetGUID(), Milliseconds(kPierceDurationMs)))
            LOG_INFO(kLog, "dm-pilot johnson pierce-armor on {} ({} ms)", target->GetName(), kPierceDurationMs);
    }

    void JustDied(Unit* /*killer*/) override
    {
        // Paid miners fight on (kill order: miners first); the digging crew goes with him.
        for (CrewSlot const& slot : _crew)
            if (Creature* miner = me->GetMap()->GetCreature(slot.guid))
                if (miner->IsAlive() && IsPaid(miner))
                    summons.Despawn(miner);
        _JustDied();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The crew
    // ----------------------------------------------------------------------------------------------------------------

    bool IsRolledAbsent() const
    {
        return instance && instance->GetBossState(BOSS_MINER_JOHNSON) != DONE
            && instance->GetData(DATA_JOHNSON_ROLL) == DeadminesKit::JohnsonRoll::Absent;
    }

    // Summons the four Working Miners at the stock miners' spots. `force` (the .dmtest command) replaces a live crew.
    // Returns the number summoned.
    uint32 SetUpCrew(bool force)
    {
        if (!me->IsAlive() || IsRolledAbsent() || (me->IsInCombat() && !force))
            return 0;
        if (!force && std::any_of(_crew.begin(), _crew.end(), [](CrewSlot const& s) { return !s.guid.IsEmpty(); }))
            return 0;

        for (CrewSlot const& slot : _crew)
            if (Creature* miner = me->GetMap()->GetCreature(slot.guid))
            {
                summons.Despawn(miner);
                miner->DespawnOrUnsummon();
            }

        uint32 count = 0;
        for (std::size_t i = 0; i < kCrewSize; ++i)
        {
            _crew[i] = {};
            if (TempSummon* miner = me->SummonCreature(NPC_DM_WORKING_MINER, ToEnginePos(kCrew[i]),
                TEMPSUMMON_CORPSE_TIMED_DESPAWN, kMinerCorpseMs))
            {
                _crew[i].guid = miner->GetGUID();
                ++count;
            }
        }
        LOG_DEBUG(kLog, "dm-pilot johnson crew: {} working miners summoned", count);
        return count;
    }

    void ForgetMiner(ObjectGuid guid)
    {
        for (CrewSlot& slot : _crew)
            if (slot.guid == guid)
                slot.pending = false;
    }

    // Crew slots whose miner is alive, unpaid and has no pouch in the air.
    std::vector<std::size_t> DiggingSlots() const
    {
        std::vector<std::size_t> slots;
        for (std::size_t i = 0; i < kCrewSize; ++i)
        {
            Creature* miner = me->GetMap()->GetCreature(_crew[i].guid);
            if (miner && miner->IsAlive() && !IsPaid(miner) && !_crew[i].pending)
                slots.push_back(i);
        }
        return slots;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MJ1 Payday
    // ----------------------------------------------------------------------------------------------------------------

    // One Payday. False once nobody is left digging (Payday stops; the emote plays once).
    bool Payday()
    {
        std::vector<std::size_t> const digging = DiggingSlots();
        bool const heroic = DeadminesKit::IsHeroicMap(me);
        std::size_t const pouches = PouchCount(heroic, digging.size());
        if (!pouches)
        {
            if (!_nobodyLeftSaid)
            {
                _nobodyLeftSaid = true;
                Talk(EMOTE_JOHNSON_NO_CREW);
                LOG_INFO(kLog, "dm-pilot johnson payday-stops: nobody left digging");
            }
            return false;
        }

        Talk(EMOTE_JOHNSON_PAYDAY);
        std::vector<std::size_t> const picks = PickDistinct(digging.size(), pouches,
            [](uint32 n) { return urand(0, n - 1); });
        for (std::size_t pick : picks)
            ThrowPouch(digging[pick], Milliseconds(kPouchFlightMs(heroic)));
        LOG_INFO(kLog, "dm-pilot johnson payday: {} pouch(es), {} ms flight, {} digging", picks.size(),
            kPouchFlightMs(heroic), digging.size());
        return true;
    }

    void ThrowPouch(std::size_t slot, Milliseconds flight)
    {
        Creature* miner = me->GetMap()->GetCreature(_crew[slot].guid);
        if (!miner)
            return;

        Position const spot = FloorPosition(me->GetMap(), me->GetPhaseMask(), CrewSpot(slot), kCrew[slot].z);
        _crew[slot].pending = true;
        miner->CastSpell(miner, SPELL_PAYDAY_GLINT, true);

        BossMechanics::Eligibility nonTank;
        nonTank.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        Map* map = me->GetMap();
        ObjectGuid const johnsonGuid = me->GetGUID();
        ObjectGuid const minerGuid = miner->GetGUID();
        Mechanic::Soak(me, spot, kSoakRadius, kSoakBodies, flight).Eligible(nonTank).Tag(TAG_PAYDAY)
            .OnResolve([map, johnsonGuid, minerGuid, spot](BossMechanics::ResolveResult const& result)
        {
            // Guids only (STAGE-M5-R m-4): resolve Johnson now; he settles the pouch.
            if (result.fizzled || !map)
                return;
            Creature* johnson = map->GetCreature(johnsonGuid);
            if (!johnson || !johnson->IsAlive())
                return;
            if (auto* ai = dynamic_cast<boss_miner_johnson_rework*>(johnson->AI()))
                ai->ResolvePouch(minerGuid, spot, result.hits);
        });

        // The missile leaves late enough to land as the Soak resolves.
        uint32 const delay = LaunchDelayMs(static_cast<uint32>(flight.count()), me->GetExactDist2d(&spot));
        me->m_Events.AddEventAtOffset([this, spot]()
        {
            if (me->IsAlive())
                me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_PAY_POUCH, true);
        }, Milliseconds(delay));
    }

    // MJ2 / MJ3: the Soak resolved with `hits` (eligible players inside).
    void ResolvePouch(ObjectGuid minerGuid, Position const& spot, std::vector<ObjectGuid> const& hits)
    {
        for (CrewSlot& slot : _crew)
            if (slot.guid == minerGuid)
                slot.pending = false;

        std::vector<Player*> players;
        std::vector<float> distances;
        for (ObjectGuid const& guid : hits)
            if (Player* player = ObjectAccessor::GetPlayer(me->GetMap(), guid))
                if (player->IsAlive())
                {
                    players.push_back(player);
                    distances.push_back(player->GetExactDist2d(&spot));
                }

        int const catcher = PickCatcher(distances);
        if (catcher >= 0)
        {
            Player* player = players[catcher];
            player->CastSpell(player, SPELL_POCKETED, true);
            LOG_INFO(kLog, "dm-pilot johnson pocketed: {} caught the pouch ({} in the circle)", player->GetName(),
                players.size());
            return;
        }

        Creature* miner = me->GetMap()->GetCreature(minerGuid);
        if (miner && miner->IsAlive() && !IsPaid(miner))
            PayMiner(miner);
    }

    void PayMiner(Creature* miner)
    {
        miner->AI()->DoAction(ACTION_MINER_PAY);
        if (me->IsInCombat())
            Mechanic::TrackUnit(me, miner);
        LOG_INFO(kLog, "dm-pilot johnson paid-miner: a Working Miner pockets his pay and joins");
    }

    // .dmtest: pays the first digging miner now (MJ3).
    bool PayFirstDigging()
    {
        std::vector<std::size_t> const digging = DiggingSlots();
        if (digging.empty())
            return false;
        if (Creature* miner = me->GetMap()->GetCreature(_crew[digging.front()].guid))
            PayMiner(miner);
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MJ5 Gold Fever and the descriptor
    // ----------------------------------------------------------------------------------------------------------------

    void GoldFever()
    {
        DoCastSelf(SPELL_GOLD_FEVER, true);
        DoCastSelf(SPELL_GOLD_FEVER_TINT, true);
        LOG_INFO(kLog, "dm-pilot johnson gold-fever at {:.0f}% health", me->GetHealthPct());
    }

    // Boss data (DM Build spec): kill order paid miners, then Johnson; no interrupt or dispel list. A digging miner
    // is ignored (unselectable, immune) so it never counts for AoE.
    void DescribeEncounter()
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_DM_WORKING_MINER, 1);
        d.ignores.emplace_back(NPC_DM_WORKING_MINER, BossMechanics::Condition::Custom([](Unit const* unit)
        {
            return unit->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        }));
        Mechanic::Describe(me, std::move(d));
    }

private:
    struct CrewSlot
    {
        ObjectGuid guid;
        bool pending = false;   // a pouch is in the air toward this miner
    };

    std::array<CrewSlot, kCrewSize> _crew{};
    bool _nobodyLeftSaid = false;
};

// boss-kit Working Miner 300422 (x4), summoned by Johnson. Digs (emote 233), unselectable and passive until paid.
struct npc_dm_working_miner : public ScriptedAI
{
    explicit npc_dm_working_miner(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        scheduler.CancelAll();
        if (!_paid)
            SetDigging(true);
    }

    void IsSummonedBy(WorldObject* summoner) override
    {
        if (summoner)
            _johnson = summoner->GetGUID();
    }

    uint32 GetData(uint32 id) const override
    {
        return id == DATA_MINER_PAID && _paid ? 1 : 0;
    }

    void DoAction(int32 action) override
    {
        if (action != ACTION_MINER_PAY || _paid || !me->IsAlive())
            return;

        // MJ3: he pockets the pay and joins the fight.
        _paid = true;
        SetDigging(false);
        Talk(EMOTE_WORKING_MINER_PAID);

        Creature* johnson = me->GetMap()->GetCreature(_johnson);
        Unit* target = johnson && johnson->IsAlive() ? johnson->GetVictim() : nullptr;
        if (target)
            AttackStart(target);
        DoZoneInCombat();

        scheduler.Schedule(randtime(Milliseconds(kMinerPierceFirstMinMs), Milliseconds(kMinerPierceFirstMaxMs)),
            [this](TaskContext context)
        {
            DoCastVictim(SPELL_PIERCE_ARMOR_MINER);
            context.Repeat(randtime(Milliseconds(kMinerPierceEveryMinMs), Milliseconds(kMinerPierceEveryMaxMs)));
        });
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        // A paid miner never goes back to digging: Johnson's reset summons a fresh crew.
        if (_paid)
        {
            me->DespawnOrUnsummon();
            return;
        }
        CreatureAI::EnterEvadeMode(why);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!_paid || !UpdateVictim())
            return;

        scheduler.Update(diff, [this]() { DoMeleeAttackIfReady(); });
    }

private:
    void SetDigging(bool digging)
    {
        // Build spec: unselectable and passive with emote 233 until paid (a design rule of this boss kit; the stock
        // miner 598 digs with the same template emote).
        me->SetReactState(digging ? REACT_PASSIVE : REACT_AGGRESSIVE);
        me->SetImmuneToAll(digging);
        me->SetEmoteState(digging ? EMOTE_STATE_WORK_MINING : EMOTE_ONESHOT_NONE);
        if (digging)
            me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        else
            me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
    }

    ObjectGuid _johnson;
    bool _paid = false;
};

namespace
{
    boss_miner_johnson_rework* JohnsonAI(Creature* johnson)
    {
        return johnson ? dynamic_cast<boss_miner_johnson_rework*>(johnson->AI()) : nullptr;
    }

    boss_miner_johnson_rework* FindJohnson(ChatHandler* handler)
    {
        Creature* johnson = DeadminesTest::FindBoss(handler, NPC_MINER_JOHNSON);
        boss_miner_johnson_rework* ai = JohnsonAI(johnson);
        if (johnson && !ai)
            handler->SendErrorMessage("Miner Johnson does not run boss_miner_johnson_rework.");
        return ai;
    }

    // `.dmtest johnson info`
    bool HandleInfo(ChatHandler* handler)
    {
        return DeadminesTest::ShowBossInfo(handler, NPC_MINER_JOHNSON, BOSS_MINER_JOHNSON);
    }

    // `.dmtest johnson payday`: one Payday now (MJ1; 2 pouches on heroic).
    bool HandlePayday(ChatHandler* handler)
    {
        boss_miner_johnson_rework* ai = FindJohnson(handler);
        if (!ai)
            return false;
        if (!ai->Payday())
            handler->SendSysMessage("Payday: nobody left digging (`.dmtest johnson crew` brings the crew back).");
        else
            handler->SendSysMessage("Payday thrown: stand in the blue circle to catch it, or let it land.");
        return true;
    }

    // `.dmtest johnson pay`: the first digging miner pockets his pay and joins (MJ3).
    bool HandlePay(ChatHandler* handler)
    {
        boss_miner_johnson_rework* ai = FindJohnson(handler);
        if (!ai)
            return false;
        if (!ai->PayFirstDigging())
            handler->SendErrorMessage("Nobody is left digging.");
        return true;
    }

    // `.dmtest johnson pierce`: Johnson casts Pierce Armor (12097, cut to 10 s) on the GM (MJ4).
    bool HandlePierce(ChatHandler* handler)
    {
        Creature* johnson = DeadminesTest::FindBoss(handler, NPC_MINER_JOHNSON);
        if (!johnson)
            return false;
        johnson->CastSpell(handler->GetPlayer(), SPELL_PIERCE_ARMOR, true);
        handler->SendSysMessage("Pierce Armor cast on you: the aura should last 10 s.");
        return true;
    }

    // `.dmtest johnson goldfever`: Gold Fever now (MJ5, heroic's below-30% buff).
    bool HandleGoldFever(ChatHandler* handler)
    {
        boss_miner_johnson_rework* ai = FindJohnson(handler);
        if (!ai)
            return false;
        ai->GoldFever();
        return true;
    }

    // `.dmtest johnson pocketed`: the catcher's buff on the GM (MJ2).
    bool HandlePocketed(ChatHandler* handler)
    {
        if (!DeadminesTest::RequireDeadmines(handler))
            return false;
        Player* gm = handler->GetPlayer();
        gm->CastSpell(gm, SPELL_POCKETED, true);
        return true;
    }

    // `.dmtest johnson crew`: a fresh crew of four digging Working Miners.
    bool HandleCrew(ChatHandler* handler)
    {
        boss_miner_johnson_rework* ai = FindJohnson(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("{} Working Miners summoned.", ai->SetUpCrew(true));
        return true;
    }

    // `.dmtest johnson present`: rolls Johnson present for this instance and brings him back if the roll despawned
    // him. Needs the instance to accept SetData(DATA_JOHNSON_ROLL) (WP-B2's request to the orchestrator).
    bool HandlePresent(ChatHandler* handler)
    {
        if (!DeadminesTest::RequireDeadmines(handler))
            return false;
        Player* gm = handler->GetPlayer();
        InstanceScript* instance = gm->GetInstanceScript();
        if (!instance)
        {
            handler->SendErrorMessage("No instance script on this map.");
            return false;
        }
        instance->SetData(DATA_JOHNSON_ROLL, DeadminesKit::JohnsonRoll::Present);
        if (instance->GetData(DATA_JOHNSON_ROLL) != DeadminesKit::JohnsonRoll::Present)
        {
            handler->SendErrorMessage("The instance script does not take SetData(DATA_JOHNSON_ROLL) yet.");
            return false;
        }
        Creature* johnson = instance->GetCreature(DATA_MINER_JOHNSON_GUID);
        if (johnson && johnson->IsAlive())
            handler->SendSysMessage("Miner Johnson is present.");
        else if (johnson)
            johnson->Respawn(true);
        else
            gm->GetMap()->ForceCreatureRespawn(kJohnsonSpawnId);
        handler->SendSysMessage("Johnson's roll is now present for this instance.");
        return true;
    }

    ChatCommandTable const& MinerJohnsonTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "payday",    HandlePayday,    SEC_GAMEMASTER, Console::No },
            { "pay",       HandlePay,       SEC_GAMEMASTER, Console::No },
            { "pierce",    HandlePierce,    SEC_GAMEMASTER, Console::No },
            { "goldfever", HandleGoldFever, SEC_GAMEMASTER, Console::No },
            { "pocketed",  HandlePocketed,  SEC_GAMEMASTER, Console::No },
            { "crew",      HandleCrew,      SEC_GAMEMASTER, Console::No },
            { "present",   HandlePresent,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_miner_johnson_rework()
{
    RegisterDeadminesReworkCreatureAI(boss_miner_johnson_rework);
    RegisterDeadminesReworkCreatureAI(npc_dm_working_miner);
    DeadminesTest::RegisterBoss("johnson", MinerJohnsonTestCommands());
}
