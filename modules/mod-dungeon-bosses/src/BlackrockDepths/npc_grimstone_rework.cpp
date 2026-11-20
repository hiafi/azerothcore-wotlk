/*
 * mod-dungeon-bosses, Blackrock Depths D4: the Ring of Law's frame, High Justice Grimstone (10096), "Entertain the
 * crowd, or feed it" (rulings 17-20, 25, 26). Build spec S1 "Ring of Law" (docs/dungeons/blackrock-depths-1-detention-
 * block.md: the frame, How it runs, Waves, Build spec RL1-RL6), handoff sections 3.4 / 3.5 (rows D4), 3.6, 3.8 (NM: the
 * floor is not round, RingOfLawLogic.h RingFloor), 3.10, section 7 #16. Replaces the stock npc_grimstone escort
 * (blackrock_depths.cpp, last upstream commit 60bac7405; its timeline, gates, credit and Arena Spoils chest are the
 * base of this one): bound by apps/dbc-tools source/npcs/blackrock_depths/ring_of_law.py. Pure rules: RingOfLawLogic.h;
 * the hooks the champions (D5) and the Encore (D6) use: RingOfLawFight.h (this file implements them).
 *
 * The instance keeps the stock protocol (section 3.5 of STAGE-S0-REPORT): at_ring_of_law (AT 1526) sends
 * SetData(TYPE_RING_OF_LAW, IN_PROGRESS), the instance summons him at kGrimstoneSummon; FAIL despawns him, stamps the
 * 2 min block and sets the slot back to NOT_STARTED; DONE stands the spectators down and opens the north gate.
 *
 *   The run      ~20 s entry: line 4, the entrance gate (161523) shuts, he walks to the ring center, line 0, the
 *                Sentence (lines 6-8), the walk to his waiting corner, line 1, the south gate (161525) opens: ONE wave
 *                of the rolled type at the stock count (npc_ring_beast_rework). The wave dies: line 5, 10 s, the east
 *                gate (161522) opens, the challenger (line 2). It dies: line 9, 5 s, the title holder
 *                (DoAction(ACTION_RING_TITLE_HOLDER)). It dies: the credit (line 3), or with the banner burned on
 *                heroic a 15 s beat, line 12 and D6's Encore, then the Arena Spoils chest, credit 16166 and the credit.
 *   RL1 Favor    0-10 from 5 each attempt (DATA_RING_FAVOR), a buff with its stacks on every player: +1 per dodgeable
 *                registry mechanic resolved with nobody hit, +2 for the wave dead within 30 s, -1 per player hit, -3
 *                per death (losses x2 under Trial by the Crowd). Emote 13 reaching 8, emote 14 dropping to 2; at 10 on
 *                heroic the banner (emote 10, DATA_BANNER_THROWN, D6 places it).
 *   RL2 Gift     Favor 8-10: every 15 s a spectator tosses roses at a random player on the floor: 10% of reference
 *                health healed and +10% damage done for 10 s. At 10 everyone has Roar of the Crowd (+10%).
 *   RL3 Jeers    Favor 0-2 (the Crowd: always): every 8 s three 3 yd circles at random players' spots, 1.5 s, 10% / 20%
 *                + Weakened, a bottle or rotten fruit thrown from the gallery; one volley judged as one mechanic.
 *   RL4 Fire     Sentence: from the challenger's entry every 30 s a 90 degree wedge from the ring center to the wall
 *                (3 s, his cast bar), 30% / 45% + Weakened, eruptions on stalkers; the next wedge a quarter clockwise.
 *   RL5 Beasts   Sentence: in the champion fights a beast of the wave's type every 20 s through the south gate, at
 *                most 3 alive (no opening debuff, no +2).
 *   RL6 Crowd    Sentence: every Favor loss doubled, the jeers at every Favor level.
 *   The wave     the group signatures (Burrow, Tail Sting, Venom Spit: one beast at a time on his clock); each beast's
 *                own clock runs Screech, Thunderclap and the stock casts; Acid Burst is the beetle's own.
 *   Wipe         no living player on the floor for 3 s: every Ring unit, zone and aura goes, the gates go back (the
 *                entrance open, the others shut), Favor 5, TYPE_RING_OF_LAW FAIL (the instance's 2 min block; both
 *                champions again on the next attempt, the rolls and the banner flags kept).
 *
 * Every timer runs on the AI's own clock. Every firing logs one INFO line "brd ring <mechanic> ..."
 * (module.dungeonbosses). He never fights: not attackable, passive, his combat dropped every second (he is the
 * registry owner of the frame's zones, the BRS Nefarius-copy precedent).
 */

#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitBodies.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RingChampionsLogic.h"
#include "RingOfLawFight.h"
#include "RingOfLawLogic.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <list>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdRingOfLaw;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "ring";

    uint32 constexpr POINT_CENTER = 1;
    uint32 constexpr POINT_CORNER = 2;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogRing(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    uint32 PlayersHit(BossMechanics::ResolveResult const& r)
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : r.hits)
            if (guid.IsPlayer())
                ++n;
        return n;
    }

    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > 6.f)
            return refZ;
        return h;
    }

    BrdRingOfLaw::EncoreFactory& EncoreFactoryRef()
    {
        static BrdRingOfLaw::EncoreFactory factory;
        return factory;
    }

    // The test commands' forced mechanics (`.dbtest brd ring ...`).
    enum class TestKind : uint8
    {
        Jeer,
        Gift,
        Fire,
        Beast,
        Signature,
        Next,
        Win,
        Wipe,
    };
}

void BrdRingOfLaw::RegisterEncore(EncoreFactory factory)
{
    EncoreFactoryRef() = std::move(factory);
}

struct npc_grimstone_rework : public ScriptedAI, public RingFrame
{
    explicit npc_grimstone_rework(Creature* creature)
        : ScriptedAI(creature), instance(creature->GetInstanceScript()), summons(creature) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->SetReactState(REACT_PASSIVE);
    }

    // He never fights and never walks home: an attempt ends only through the wipe or the credit.
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE)
            return;
        if (id == POINT_CENTER && _step == Step::Entry)
            EnterStep(Step::Sentence);
        else if (id == POINT_CORNER && _step == Step::ToCorner)
            AtCorner();
    }

    void JustSummoned(Creature* summon) override
    {
        if (summon->GetEntry() == NPC_BRD_STALKER)
            return;     // a look (eruptions, pools): not a Ring unit
        summons.Summon(summon);
        // A wave beast learns its place before it engages (the opener's first one lays the opening debuff).
        if (WaveIndexOf(summon->GetEntry()) && summon->IsAIEnabled && summon->AI())
            summon->AI()->SetData(kBeastDataSlot, _pendingSlot);
        if (_pendingChampion)
        {
            _champion = summon->GetGUID();
            _championGuids[_pendingChampion - 1] = summon->GetGUID();
            _championMissingMs = 0;
        }
        Mechanic::TrackUnit(me, summon);
        EngageRing(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        ObjectGuid const guid = summon->GetGUID();
        if (std::optional<uint32> const type = WaveIndexOf(summon->GetEntry()))
            _deaths.Record(summon, *type + 1);
        _unitFills.erase(guid);

        if (_openers.erase(guid) && _openers.empty() && _step == Step::Opener && _waveSpawned)
            OpenerCleared();
        _beastAdds.erase(guid);

        if (guid == _champion && (_step == Step::Challenger || _step == Step::TitleHolder))
        {
            _champion.Clear();
            ChampionDied(summon);
        }
        Describe();
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        summons.Despawn(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        _stepMs += diff;

        if (_step == Step::Idle)
        {
            if (!_begun)
                TryBegin();
            return;
        }
        if (_over)
            return;

        if (_syncMs <= diff)
        {
            _syncMs = kSyncMs;
            Sync();
            if (_over)
                return;
        }
        else
            _syncMs -= diff;

        if (WipeWatched(_step))
        {
            if (FloorPlayers().empty())
            {
                _noPlayerMs += diff;
                if (_noPlayerMs >= kWipeGraceMs)
                {
                    Wipe("nobody alive on the floor");
                    return;
                }
            }
            else
                _noPlayerMs = 0;
        }

        RunStep(diff);
        if (_over)
            return;
        RunFrame();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RingFrame (RingOfLawFight.h)
    // ----------------------------------------------------------------------------------------------------------------

    Step CurrentStep() const override { return _step; }
    bool Heroic() const override { return _heroic; }
    Sentence ActiveSentence() const override { return _sentence; }
    uint32 WaveType() const override { return _wave; }
    Creature* Owner() override { return me; }
    uint32 Favor() const override { return _favor; }
    DungeonKit::DeathSpots& BeastDeaths() override { return _deaths; }

    uint8 ChampionOrder(ObjectGuid champion) const override
    {
        if (champion.IsEmpty())
            return 0;
        for (uint8 i = 0; i < 2; ++i)
            if (_championGuids[i] == champion)
                return i + 1;
        return 0;
    }

    std::vector<Player*> FloorPlayers() const override
    {
        std::vector<Player*> out;
        Map* map = me->GetMap();
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsInWorld() || !player->IsAlive() || player->IsGameMaster())
                continue;
            if (OnFloor(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                out.push_back(player);
        }
        return out;
    }

    void JudgeResolve(BossMechanics::ResolveResult const& result, char const* source) override
    {
        if (!FrameRuns(_step) || _over)
            return;
        uint32 const hits = PlayersHit(result);
        SetFavor(AfterResolve(_favor, hits, _sentence),
            Acore::StringFormat("{} {}", source, hits ? Acore::StringFormat("hit={}", hits) : std::string("clean")));
    }

    void FavorHit(ObjectGuid player, char const* source) override
    {
        if (!FrameRuns(_step) || _over || !player.IsPlayer())
            return;
        SetFavor(AfterLoss(_favor, kFavorPerHit, _sentence), Acore::StringFormat("{} hit=1", source));
    }

    void JoinRing(Creature* unit) override
    {
        if (!unit || _over)
            return;
        _joined.insert(unit->GetGUID());
        Mechanic::TrackUnit(me, unit);
        EngageRing(unit);
    }

    void SetUnitDescriptor(ObjectGuid unit, std::function<void(BossMechanics::Descriptor&)> fill) override
    {
        _unitFills[unit] = std::move(fill);
        Describe();
    }

    void ClearUnitDescriptor(ObjectGuid unit) override
    {
        if (_unitFills.erase(unit))
            Describe();
    }

    void GrimstoneSay(uint8 group, WorldObject const* target = nullptr) override
    {
        Talk(group, target);
    }

    void EncoreWon() override
    {
        if (_step != Step::Encore || _over)
            return;
        // D4 request 2: the instance records the Encore's kill (BOSS_ENCORE) only on this, before the Ring's credit.
        instance->SetData(DATA_ENCORE_WON, 1);
        // Stock (npc_grimstone phase 9): a player summons the chest, so it outlives the summoner, then it is unowned;
        // every player on the map gets the Theldren kill credit (quest 9015).
        if (Player* player = me->SelectNearestPlayer(100.f))
            if (GameObject* go = player->SummonGameObject(GO_ARENA_SPOILS, kArenaSpoilsSpot.x, kArenaSpoilsSpot.y,
                kArenaSpoilsSpot.z, kArenaSpoilsO, 0.f, 0.f, 0.f, 0.f, kArenaSpoilsDespawnSec))
                go->SetOwnerGUID(ObjectGuid::Empty);
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                player->KilledMonsterCredit(NPC_THELDREN_KILL_CREDIT);
        LogRing("encore-won", "spoils=1 credit=16166");
        Win("encore");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Internal hooks (the lambdas and the test commands)
    // ----------------------------------------------------------------------------------------------------------------

    void JudgeVolley(uint32 id, uint32 hits)
    {
        auto it = _volleys.find(id);
        if (it == _volleys.end())
            return;
        if (hits)
            SetFavor(AfterLoss(_favor, static_cast<int32>(hits) * kFavorPerHit, _sentence),
                Acore::StringFormat("jeer hit={}", hits));
        if (it->second.Resolve(hits))
            SetFavor(AfterGain(_favor, kFavorClean), "jeers clean");
        if (it->second.resolved >= it->second.expected)
            _volleys.erase(it);
    }

    // `.dbtest brd ring ...`: forced firings. Returns an error ("" on success).
    std::string TestFire(TestKind kind)
    {
        if (_step == Step::Idle || _over)
            return "No attempt is running (`.dbtest brd ring start`).";
        switch (kind)
        {
            case TestKind::Jeer:
                Jeer();
                return {};
            case TestKind::Gift:
                Gift();
                return {};
            case TestKind::Fire:
                TrialByFire();
                return {};
            case TestKind::Beast:
                return SpawnBeastAdd() ? std::string() : std::string("No beast came (the cap, or no floor player).");
            case TestKind::Signature:
                return GroupSignature() ? std::string() : std::string("No free beast of a group signature type.");
            case TestKind::Next:
                return SkipStep();
            case TestKind::Win:
                Win("test");
                return {};
            case TestKind::Wipe:
                Wipe("test");
                return {};
        }
        return {};
    }

    void TestFavor(uint32 favor)
    {
        SetFavor(ClampFavor(static_cast<int32>(favor)), "test");
    }

    std::string TestState() const
    {
        return Acore::StringFormat("Ring: step {} ({} ms) favor {} sentence {} wave {} ({}) champions {} then {} "
            "heroic {} encore {} | openers {} adds {} joined {} | timers gift {} jeer {} fire {} beasts {} sig {} | "
            "deaths {} wedge #{}", StepName(_step), _stepMs, _favor, SentenceName(_sentence), _wave,
            kWaveTypes[_wave].entry, kRingChampions[_first], kRingChampions[_second], _heroic ? 1 : 0,
            _encore ? (_encoreLit ? "lit" : "registered") : "none", _openers.size(), _beastAdds.size(),
            _joined.size(), Due(_giftAtMs), Due(_jeerAtMs), Due(_fireAtMs), Due(_beastsAtMs), Due(_sigAtMs),
            _deaths.Count(), _fireCount);
    }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // The attempt
    // ----------------------------------------------------------------------------------------------------------------

    void TryBegin()
    {
        _begun = true;
        if (!instance || instance->GetData(TYPE_RING_OF_LAW) != IN_PROGRESS)
        {
            LogRing("idle", "no attempt (the slot is not IN_PROGRESS): he stands by");
            return;
        }
        _heroic = IsHeroicMap(me);
        _sentence = SentenceOf(instance->GetData(DATA_RING_SENTENCE));
        _wave = std::min<uint32>(instance->GetData(DATA_RING_WAVE), kRingWaveTypes - 1);
        _first = std::min<uint32>(instance->GetData(DATA_RING_FIRST), kRingChampionCount - 1);
        _second = std::min<uint32>(instance->GetData(DATA_RING_SECOND), kRingChampionCount - 1);
        _favor = kFavorStart;
        instance->SetData(DATA_RING_FAVOR, _favor);
        me->SetWalk(true);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RING_OF_LAW;
        Mechanic::BeginEncounter(me, options);

        if (EncoreFactoryRef())
            _encore = EncoreFactoryRef()();
        if (_encore && instance->GetData(DATA_BANNER_THROWN))
            _encore->OnAttemptStart(me);

        LogRing("start", Acore::StringFormat("heroic={} sentence={} wave={} champions={}/{} favor={} encore={}",
            _heroic ? 1 : 0, SentenceName(_sentence), kWaveTypes[_wave].entry, kRingChampions[_first],
            kRingChampions[_second], _favor, _encore ? 1 : 0));
        EnterStep(Step::Entry);
        Describe();
    }

    void EnterStep(Step step)
    {
        _step = step;
        _stepMs = 0;
        _beat = 0;
        switch (step)
        {
            case Step::Sentence:
                me->GetMotionMaster()->Clear();
                Talk(SAY_GRIM_RING_CENTER);
                break;
            case Step::Gap:
                Talk(SAY_GRIM_GAP);
                break;
            case Step::Interlude:
                Talk(SAY_GRIM_SECOND_CHAMPION);
                break;
            default:
                break;
        }
        // User ruling 2026-11-17: from the beat on, a wipe puts the banner out (the instance's FAIL clears
        // DATA_BANNER_BURNED while DATA_ENCORE_RUNNING is set; the banner stays thrown, OnAttemptStart re-places it
        // clickable and the next attempt is the normal champion finish). The instance clears the flag on FAIL / DONE.
        if (WipeUnlightsBanner(step))
            instance->SetData(DATA_ENCORE_RUNNING, 1);
        LogRing("step", StepName(step));
    }

    void RunStep(uint32 diff)
    {
        switch (_step)
        {
            case Step::Entry:
                if (_beat == 0 && _stepMs >= kEntryFirstBeatMs)
                {
                    _beat = 1;
                    Talk(SAY_GRIM_SENTENCED);
                    Gate(DATA_ARENA4, false);
                    me->GetMotionMaster()->MovePoint(POINT_CENTER, kGrimstoneCenter.x, kGrimstoneCenter.y,
                        kGrimstoneCenter.z);
                }
                else if (_stepMs >= kEntryFirstBeatMs + kWalkTimeoutMs)
                    EnterStep(Step::Sentence);
                break;
            case Step::Sentence:
                if (_beat == 0 && _stepMs >= kSentenceDelayMs)
                {
                    _beat = 1;
                    Talk(SentenceText(_sentence));
                    LogRing("sentence", SentenceName(_sentence));
                    SyncFavorAuras();
                }
                else if (_beat == 1 && _stepMs >= kSentenceDelayMs + kToCornerDelayMs)
                {
                    EnterStep(Step::ToCorner);
                    me->GetMotionMaster()->MovePoint(POINT_CORNER, kGrimstoneCorner.x, kGrimstoneCorner.y,
                        kGrimstoneCorner.z);
                }
                break;
            case Step::ToCorner:
                if (_stepMs >= kWalkTimeoutMs)
                    AtCorner();
                break;
            case Step::Opener:
                if (!_waveSpawned && _stepMs >= kWaveDelayMs)
                    SpawnWave();
                else if (_waveSpawned && _southGateOpen && (_stepMs >= kWaveDelayMs + kSouthGateCloseMs
                    || OpenersInside()))
                    Gate(DATA_ARENA1, false);
                break;
            case Step::Gap:
                if (_beat == 0 && _stepMs + kEastGateLeadMs >= kGapMs)
                {
                    _beat = 1;
                    Gate(DATA_ARENA2, true);
                }
                if (_stepMs >= kGapMs)
                    SummonChampion(1);
                break;
            case Step::Interlude:
                if (_stepMs >= kInterludeMs)
                    SummonChampion(2);
                break;
            case Step::Challenger:
            case Step::TitleHolder:
                WatchChampion(diff);
                break;
            case Step::EncoreBeat:
                if (_stepMs >= kEncoreBeatMs)
                {
                    Talk(SAY_GRIM_ENCORE);
                    EnterStep(Step::Encore);
                    if (_encore && _encore->Start(me, *this))
                        LogRing("encore", "the leap");
                    else
                    {
                        LogRing("encore-refused", "the Encore's script could not start: credited without it");
                        Win("no encore");
                    }
                }
                break;
            case Step::Encore:
                if (_encore)
                    _encore->Update(me, *this, diff);
                break;
            default:
                break;
        }
        // The Beasts adds' gate (champion steps).
        if (_beastsGateCloseAtMs && _clockMs >= _beastsGateCloseAtMs)
        {
            _beastsGateCloseAtMs = 0;
            if (_step != Step::Opener)
                Gate(DATA_ARENA1, false);
        }
    }

    void AtCorner()
    {
        Gate(DATA_ARENA4, false);
        me->GetMotionMaster()->Clear();
        me->SetFacingTo(kChampionSpawnO);
        Talk(SAY_GRIM_WAVE);
        Gate(DATA_ARENA1, true);
        EnterStep(Step::Opener);
    }

    // The opener: one wave of the rolled type at the stock count, behind the south gate.
    void SpawnWave()
    {
        _waveSpawned = true;
        _waveSpawnedAtMs = _clockMs;
        WaveKind const& w = kWaveTypes[_wave];
        for (uint32 i = 0; i < w.count; ++i)
        {
            Point3 const p = WaveSpawn(i);
            _pendingSlot = i + 1;
            if (Creature* beast = me->SummonCreature(w.entry, p.x, p.y, p.z, kWaveSpawnO, TEMPSUMMON_DEAD_DESPAWN, 0))
                _openers.insert(beast->GetGUID());
        }
        _pendingSlot = 0;
        _sigAtMs = w.perBeast || w.signature == Signature::AcidBurst ? 0 : _clockMs + w.firstMs;
        _jeerArmed = false;
        _giftArmed = false;
        LogRing("wave", Acore::StringFormat("entry={} count={} spawned={} signature={}", w.entry, w.count,
            _openers.size(), SignatureName(w.signature)));
    }

    bool OpenersInside()
    {
        for (ObjectGuid const& guid : _openers)
            if (Creature* beast = ObjectAccessor::GetCreature(*me, guid))
                if (beast->IsAlive() && !WellInside(DungeonKit::PlaneOf(beast), kGateClearYd))
                    return false;
        return true;
    }

    void OpenerCleared()
    {
        uint32 const took = _clockMs - _waveSpawnedAtMs;
        if (took <= kWaveFavorWindowMs)
            SetFavor(AfterGain(_favor, kFavorWave), Acore::StringFormat("wave in {} ms", took));
        // Each type's stock opening debuff ends when the wave dies (S1 frame step 1).
        instance->DoRemoveAurasDueToSpellOnPlayers(kWaveTypes[_wave].openingDebuff);
        Gate(DATA_ARENA1, false);
        LogRing("wave-cleared", Acore::StringFormat("ms={} bonus={}", took, took <= kWaveFavorWindowMs ? 1 : 0));
        EnterStep(Step::Gap);
    }

    void SummonChampion(uint8 order)
    {
        uint32 const entry = kRingChampions[order == 1 ? _first : _second];
        // The step first: the champion's own pull (inside the summon) already sees its fight.
        if (order == 1)
        {
            Talk(SAY_GRIM_FIRST_CHAMPION);
            if (_step != Step::Challenger)
            {
                EnterStep(Step::Challenger);
                StartChampionFrame();
            }
        }
        else if (_step != Step::TitleHolder)
            EnterStep(Step::TitleHolder);
        _pendingChampion = order;
        Creature* champion = me->SummonCreature(entry, kRingChampionSummon.x, kRingChampionSummon.y,
            kRingChampionSummon.z, kRingChampionSummon.o, TEMPSUMMON_DEAD_DESPAWN, 0);
        _pendingChampion = 0;
        if (!champion)
        {
            LogRing("champion-refused", Acore::StringFormat("order={} entry={}", order, entry));
            return;
        }
        if (order == 2 && champion->IsAIEnabled && champion->AI())
            champion->AI()->DoAction(ACTION_RING_TITLE_HOLDER);
        LogRing("champion", Acore::StringFormat("order={} entry={} guid={}", order, entry,
            champion->GetGUID().GetCounter()));
    }

    // The Sentences' champion clocks start with the challenger's entry.
    void StartChampionFrame()
    {
        if (_sentence == Sentence::Fire)
        {
            _fireQuadrant = urand(0, 3);
            _fireCount = 0;
            _fireAtMs = _clockMs + kTrialFireFirstMs;
        }
        if (_sentence == Sentence::Beasts)
            _beastsAtMs = _clockMs + kBeastsFirstMs;
    }

    // A champion that is gone without dying (a despawn, a lost summon) for 5 s comes again.
    void WatchChampion(uint32 diff)
    {
        Creature* champion = _champion ? ObjectAccessor::GetCreature(*me, _champion) : nullptr;
        if (champion && champion->IsInWorld())
        {
            _championMissingMs = 0;
            return;
        }
        _championMissingMs += diff;
        if (_championMissingMs < kChampionLostMs)
            return;
        _championMissingMs = 0;
        uint8 const order = _step == Step::Challenger ? 1 : 2;
        LogRing("champion-lost", Acore::StringFormat("order={}: summoned again", order));
        SummonChampion(order);
    }

    void ChampionDied(Creature* champion)
    {
        uint8 const order = ChampionOrder(champion->GetGUID());
        LogRing("champion-died", Acore::StringFormat("order={} entry={}", order, champion->GetEntry()));
        if (_step == Step::Challenger)
        {
            EnterStep(Step::Interlude);
            return;
        }
        _encoreLit = _heroic && _encore && instance->GetData(DATA_BANNER_BURNED) != 0;
        Step const next = AfterKill(_step, _encoreLit);
        if (next == Step::EncoreBeat)
            EnterStep(Step::EncoreBeat);
        else
            Win("title holder");
    }

    // The run is won: the credit (stock: the encounter's kill credit, then TYPE_RING_OF_LAW DONE; the instance opens
    // the north gate, stands the spectators down and records the Encore's kill when the banner burned on heroic).
    void Win(char const* why)
    {
        if (_over)
            return;
        _over = true;
        _step = Step::Done;
        Talk(SAY_GRIM_WON);
        if (_encore)
            _encore->Stop(me, true);
        EndFrame(false);
        Gate(DATA_ARENA2, false);
        Gate(DATA_ARENA1, false);
        Gate(DATA_ARENA4, true);
        me->GetMap()->UpdateEncounterState(ENCOUNTER_CREDIT_KILL_CREATURE, NPC_GRIMSTONE, me);
        LogRing("won", Acore::StringFormat("why={} favor={} sentence={}", why, _favor, SentenceName(_sentence)));
        instance->SetData(TYPE_RING_OF_LAW, DONE);
        me->GetMotionMaster()->MovePoint(POINT_CORNER, kGrimstoneCorner.x, kGrimstoneCorner.y, kGrimstoneCorner.z);
    }

    // A wipe: everything of the attempt goes; the instance despawns him (FAIL: the stock 2 min block).
    void Wipe(char const* why)
    {
        if (_over)
            return;
        _over = true;
        LogRing("wipe", Acore::StringFormat("why={} step={} favor={}", why, StepName(_step), _favor));
        if (_encore)
            _encore->Stop(me, false);
        EndFrame(true);
        Gate(DATA_ARENA4, true);
        Gate(DATA_ARENA3, false);
        Gate(DATA_ARENA2, false);
        Gate(DATA_ARENA1, false);
        instance->SetData(DATA_RING_FAVOR, kFavorStart);
        instance->SetData(TYPE_RING_OF_LAW, FAIL);     // last: the instance despawns him
    }

    // Every zone, aura and unit of the attempt goes (rule 6). A wipe takes the corpses too; the credit leaves the
    // champions' corpses for their loot.
    void EndFrame(bool wipe)
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _volleys.clear();
        for (ObjectGuid const& guid : _joined)
            if (Creature* unit = ObjectAccessor::GetCreature(*me, guid))
                if (wipe || unit->IsAlive())
                    unit->DespawnOrUnsummon();
        _joined.clear();
        if (wipe)
            summons.DespawnAll();
        else
        {
            GuidSet const units(summons.begin(), summons.end());
            for (ObjectGuid const& guid : units)
                if (Creature* unit = ObjectAccessor::GetCreature(*me, guid))
                    if (unit->IsAlive())
                        unit->DespawnOrUnsummon();
        }
        _openers.clear();
        _beastAdds.clear();
        _unitFills.clear();
        _deaths.Clear();
        for (uint32 const spell : { uint32(SPELL_RL_CROWD_FAVOR), uint32(SPELL_RL_ROAR_OF_THE_CROWD),
            uint32(SPELL_RL_CROWD_GIFT), uint32(SPELL_RW_TAIL_STING_POISON), uint32(SPELL_RW_WORM_POISON),
            uint32(SPELL_RW_THUNDERCLAP_SLOW), kWaveTypes[_wave].openingDebuff })
            instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        // D5's player auras: a wipe despawns a living champion (no death, no evade, so no Cleanup of its own).
        for (uint32 const spell : BrdRingChampions::kChampionPlayerAuras)
            instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        me->InterruptNonMeleeSpells(false);
    }

    std::string SkipStep()
    {
        switch (_step)
        {
            case Step::Entry:
            case Step::Sentence:
            case Step::ToCorner:
                AtCorner();
                return {};
            case Step::Opener:
            {
                if (!_waveSpawned)
                    SpawnWave();
                GuidSet const openers(_openers.begin(), _openers.end());
                for (ObjectGuid const& guid : openers)
                    if (Creature* beast = ObjectAccessor::GetCreature(*me, guid))
                        if (beast->IsAlive())
                            me->Kill(me, beast);
                return {};
            }
            case Step::Gap:
            case Step::Interlude:
            case Step::EncoreBeat:
                _stepMs = 60000;
                return {};
            case Step::Challenger:
            case Step::TitleHolder:
                if (Creature* champion = ObjectAccessor::GetCreature(*me, _champion))
                    if (champion->IsAlive())
                    {
                        me->Kill(me, champion);
                        return {};
                    }
                return "No champion to skip.";
            default:
                return "Nothing to skip in this step.";
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The frame: Favor, its buff, the deaths, the gift, the jeers, the Sentences, the group signatures
    // ----------------------------------------------------------------------------------------------------------------

    void Sync()
    {
        // He never fights (he owns the frame's zones: their hits put him in combat).
        if (me->IsInCombat())
            me->CombatStop(false);

        if (_step >= Step::Sentence)
            SyncFavorAuras();

        // RL1 deaths: -3 each (x2 under the Crowd), for a player who died near the ring during the attempt.
        if (FrameRuns(_step))
        {
            std::unordered_set<ObjectGuid> alive;
            for (auto const& ref : me->GetMap()->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (!player || player->IsGameMaster()
                    || player->GetDistance2d(kRingCenter.x, kRingCenter.y) > kRingSpectatorRadius)
                    continue;
                if (player->IsAlive())
                    alive.insert(player->GetGUID());
                else if (_alive.count(player->GetGUID()))
                    SetFavor(AfterLoss(_favor, kFavorPerDeath, _sentence),
                        Acore::StringFormat("death player={}", player->GetName()));
            }
            _alive = std::move(alive);
        }
    }

    void SyncFavorAuras()
    {
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsInWorld() || !player->IsAlive())
                continue;
            int32 const delta = static_cast<int32>(_favor)
                - static_cast<int32>(DungeonKit::Stacks(player, SPELL_RL_CROWD_FAVOR));
            if (delta)
                DungeonKit::AddStacks(player, SPELL_RL_CROWD_FAVOR, delta, nullptr, kFavorMax);
            bool const roar = RoarOfTheCrowd(_favor);
            if (roar && !player->HasAura(SPELL_RL_ROAR_OF_THE_CROWD))
                player->CastSpell(player, SPELL_RL_ROAR_OF_THE_CROWD, true);
            else if (!roar)
                player->RemoveAurasDueToSpell(SPELL_RL_ROAR_OF_THE_CROWD);
        }
    }

    void SetFavor(uint32 after, std::string const& why)
    {
        uint32 const before = _favor;
        _favor = after;
        if (instance)
            instance->SetData(DATA_RING_FAVOR, _favor);
        if (before == after)
        {
            LogRing("favor", Acore::StringFormat("{} -> {} ({})", before, after, why));
            return;
        }
        switch (CueFor(before, after))
        {
            case FavorCue::Roar:
                Talk(EMOTE_GRIM_ROAR);
                break;
            case FavorCue::Jeer:
                Talk(EMOTE_GRIM_JEER);
                break;
            default:
                break;
        }
        LogRing("favor", Acore::StringFormat("{} -> {} ({})", before, after, why));
        if (ThrowsBanner(_favor, _heroic, instance && instance->GetData(DATA_BANNER_THROWN) != 0))
        {
            instance->SetData(DATA_BANNER_THROWN, 1);
            if (instance->GetData(DATA_BANNER_THROWN))
            {
                Talk(EMOTE_GRIM_BANNER);
                LogRing("banner-thrown", _encore ? "encore=1" : "encore=0 (no D6 script: nothing placed)");
                if (_encore)
                    _encore->OnBannerThrown(me);
            }
        }
        if (_step >= Step::Sentence && !_over)
            SyncFavorAuras();
    }

    void RunFrame()
    {
        if (!FrameRuns(_step) || (_step == Step::Opener && !_waveSpawned))
            return;

        // RL2 the gift (Favor 8-10).
        if (Roars(_favor))
        {
            if (!_giftArmed)
            {
                _giftArmed = true;
                _giftAtMs = _clockMs + kGiftFirstMs;
            }
            else if (_clockMs >= _giftAtMs)
            {
                _giftAtMs = _clockMs + kGiftEveryMs;
                Gift();
            }
        }
        else
            _giftArmed = false;

        // RL3 the jeers (Favor 0-2; the Crowd: always).
        if (Jeers(_favor, _sentence))
        {
            if (!_jeerArmed)
            {
                _jeerArmed = true;
                _jeerAtMs = _clockMs + kJeerFirstMs;
            }
            else if (_clockMs >= _jeerAtMs)
            {
                _jeerAtMs = _clockMs + kJeerEveryMs;
                Jeer();
            }
        }
        else
            _jeerArmed = false;

        // RL4 Trial by Fire.
        if (_sentence == Sentence::Fire && FireRuns(_step) && _fireAtMs && _clockMs >= _fireAtMs)
        {
            _fireAtMs = _clockMs + kTrialFireEveryMs;
            TrialByFire();
        }

        // RL5 Trial by Beasts.
        if (_sentence == Sentence::Beasts && ChampionFights(_step) && _beastsAtMs && _clockMs >= _beastsAtMs)
        {
            _beastsAtMs = _clockMs + kBeastsEveryMs;
            SpawnBeastAdd();
        }

        // The wave's group signature (one beast at a time).
        if (_sigAtMs && _clockMs >= _sigAtMs)
            _sigAtMs = _clockMs + (GroupSignature() ? kWaveTypes[_wave].everyMs : 1000);
    }

    // RL2: a random player on the floor gets the gift; a spectator tosses the roses.
    void Gift()
    {
        std::vector<Player*> const players = FloorPlayers();
        if (players.empty())
            return;
        Player* player = players[urand(0, uint32(players.size() - 1))];
        uint32 const heal = DungeonKit::RefFlat(me, kGiftHealPct);
        Throw(SPELL_RL_GIFT_TOSS, player->GetPosition());
        player->CastSpell(player, SPELL_RL_CROWD_GIFT, true);
        if (SpellInfo const* info = sSpellMgr->GetSpellInfo(SPELL_RL_CROWD_GIFT))
        {
            HealInfo healInfo(player, player, heal, info, info->GetSchoolMask());
            player->HealBySpell(healInfo);
        }
        LogRing("gift", Acore::StringFormat("player={} heal={} favor={}", player->GetName(), heal, _favor));
    }

    // RL3: three circles at random players' spots (distinct players while there are enough), one volley.
    void Jeer()
    {
        std::vector<Player*> players = FloorPlayers();
        if (players.empty())
            return;
        Acore::Containers::RandomShuffle(players);
        uint32 const id = ++_volleyId;
        VolleyJudge& judge = _volleys[id];
        Map* map = me->GetMap();
        ObjectGuid const self = me->GetGUID();
        uint32 made = 0;
        for (uint32 i = 0; i < kJeerCount; ++i)
        {
            Player* player = players[i % players.size()];
            Position const spot(player->GetPositionX(), player->GetPositionY(), player->GetPositionZ(), 0.f);
            MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(spot), kJeerRadius, Ms(kJeerWarnMs));
            ref.Damage(kJeerPct(_heroic)).TankDamage(kJeerPct(_heroic)).Weakened().Spell(SPELL_RL_JEER).Tag(TAG_RL_JEER)
                .OnResolve([map, self, id](BossMechanics::ResolveResult const& r)
                {
                    if (npc_grimstone_rework* ai = AIOf(map, self))
                        ai->JudgeVolley(id, PlayersHit(r));
                });
            if (!ref.IsValid())
                continue;
            Track(ref.Handle());
            ++made;
            uint32 const looks[] = { SPELL_RL_JEER_BOTTLE, SPELL_RL_JEER_APPLE, SPELL_RL_JEER_BANANA };
            Throw(looks[urand(0, 2)], spot);
        }
        judge.expected = made;
        if (!made)
            _volleys.erase(id);
        LogRing("jeer", Acore::StringFormat("circles={} pct={:.0f} favor={}", made, kJeerPct(_heroic), _favor));
    }

    // RL4: the next wedge from the ring center, to the wall within it; eruptions on stalkers as it resolves.
    void TrialByFire()
    {
        float const facing = WedgeFacing(_fireQuadrant, _fireCount++);
        float const length = WedgeLength(facing);
        Position const apex(kRingCenter.x, kRingCenter.y, kRingCenter.z, facing);
        me->CastSpell(me, SPELL_RL_TRIAL_BY_FIRE_BAR, false);
        Map* map = me->GetMap();
        ObjectGuid const self = me->GetGUID();
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(BossMechanics::Anchor(apex),
            kTrialFireAngleDeg, length), Ms(kTrialFireWarnMs));
        ref.Damage(kTrialFirePct(_heroic)).TankDamage(kTrialFirePct(_heroic))
            .Weakened().Spell(SPELL_RL_TRIAL_BY_FIRE).Tag(TAG_RL_TRIAL_FIRE)
            .OnResolve([map, self, facing, length](BossMechanics::ResolveResult const& r)
            {
                if (npc_grimstone_rework* ai = AIOf(map, self))
                {
                    ai->JudgeResolve(r, "trial-by-fire");
                    ai->Eruptions(facing, length);
                }
            });
        Track(ref.Handle());
        LogRing("trial-by-fire", Acore::StringFormat("ok={} facing={:.0f} length={:.1f} pct={:.0f}",
            ref.IsValid() ? 1 : 0, Degrees(facing), length, kTrialFirePct(_heroic)));
    }

    // RL5: a beast of the wave's type through the south gate, at most 3 alive.
    bool SpawnBeastAdd()
    {
        for (auto it = _beastAdds.begin(); it != _beastAdds.end();)
        {
            Creature* beast = ObjectAccessor::GetCreature(*me, *it);
            it = beast && beast->IsAlive() ? std::next(it) : _beastAdds.erase(it);
        }
        if (_beastAdds.size() >= kBeastsCap || FloorPlayers().empty())
            return false;
        WaveKind const& w = kWaveTypes[_wave];
        Point3 const p = WaveSpawn(0);
        Gate(DATA_ARENA1, true);
        _beastsGateCloseAtMs = _clockMs + kBeastsGateMs;
        _pendingSlot = 0;
        Creature* beast = me->SummonCreature(w.entry, p.x, p.y, p.z, kWaveSpawnO, TEMPSUMMON_DEAD_DESPAWN, 0);
        if (!beast)
            return false;
        _beastAdds.insert(beast->GetGUID());
        if (!_sigAtMs && !w.perBeast && w.signature != Signature::AcidBurst)
            _sigAtMs = _clockMs + w.firstMs;
        LogRing("trial-by-beasts", Acore::StringFormat("entry={} alive={}", w.entry, _beastAdds.size()));
        return true;
    }

    // A group signature (Burrow, Tail Sting, Venom Spit) on a free beast of the wave's type: true when one went.
    bool GroupSignature()
    {
        WaveKind const& w = kWaveTypes[_wave];
        if (w.perBeast || w.signature == Signature::AcidBurst)
            return false;
        std::vector<Creature*> free;
        for (ObjectGuid const& guid : summons)
            if (Creature* beast = ObjectAccessor::GetCreature(*me, guid))
                if (beast->GetEntry() == w.entry && beast->IsAlive() && beast->IsEngaged() && beast->IsAIEnabled
                    && beast->AI() && beast->AI()->GetData(kBeastDataFree) != 0)
                    free.push_back(beast);
        if (free.empty())
            return false;
        // Round robin through the free beasts.
        Creature* beast = free[_sigTurn++ % free.size()];
        beast->AI()->DoAction(kBeastActionSignature);
        return true;
    }

    // RL4's look: eruptions on short-lived stalkers through the wedge.
    void Eruptions(float facing, float length)
    {
        for (Vec2 const& p : WedgeBurstSpots(facing, length))
            if (Creature* stalker = me->SummonCreature(NPC_BRD_STALKER, p.x, p.y, GroundZ(me, p.x, p.y, kRingCenter.z),
                0.f, TEMPSUMMON_TIMED_DESPAWN, kTrialBurstMs))
                stalker->CastSpell(stalker, SPELL_RL_TRIAL_BURST, true);
    }

    // A crowd missile from the gallery (a random spectator; Grimstone when none is left) to `at`.
    void Throw(uint32 spellId, Position const& at)
    {
        std::list<Creature*> crowd;
        me->GetCreatureListWithEntryInGrid(crowd, std::vector<uint32>{ NPC_ARENA_SPECTATOR, NPC_SHADOWFORGE_PEASANT,
            NPC_SHADOWFORGE_CITIZEN }, kThrowerSearchYd);
        std::vector<Creature*> throwers;
        for (Creature* c : crowd)
            if (c->IsAlive() && c->GetPositionZ() > kGalleryMinZ && !c->IsInCombat())
                throwers.push_back(c);
        Unit* thrower = throwers.empty() ? static_cast<Unit*>(me) : throwers[urand(0, uint32(throwers.size() - 1))];
        thrower->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), spellId, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Ring units, the descriptor, gates
    // ----------------------------------------------------------------------------------------------------------------

    // Every player on the floor at 0 threat (rule 11: a one-entry add evades) and an attack on one of them.
    void EngageRing(Creature* unit)
    {
        std::vector<Player*> const players = FloorPlayers();
        if (players.empty() || !unit->IsAlive())
            return;
        for (Player* player : players)
            unit->AddThreat(player, 0.f);
        if (unit->IsAIEnabled && unit->AI())
            unit->AI()->AttackStart(players[urand(0, uint32(players.size() - 1))]);
    }

    // The Ring's one descriptor: the wave mobs' kicks and dispels, then every unit's own entries (D5 / D6).
    void Describe()
    {
        if (_step == Step::Idle || _over)
            return;
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_DARK_SCREECHER, SPELL_RW_SCREECH, kScreechKickPriority,
            Ms(kWaveTypes[2].everyMs));
        d.interrupts.emplace_back(NPC_THUNDERSNOUT, SPELL_RW_LIZARD_BOLT, kStockKickPriority);
        d.interrupts.emplace_back(NPC_DREDGE_WORM, SPELL_RW_WORM_VENOM_SPIT, kStockKickPriority);
        d.interrupts.emplace_back(NPC_CAVE_CREEPER, SPELL_STOCK_CREEPER_VENOM, kStockKickPriority);
        d.dispels.emplace_back(SPELL_RW_TAIL_STING_POISON, kPoisonDispelPriority);
        d.dispels.emplace_back(SPELL_RW_WORM_POISON, kPoisonDispelPriority);
        for (auto const& [unit, fill] : _unitFills)
            if (fill)
                fill(d);
        Mechanic::Describe(me, std::move(d));
    }

    void Gate(uint32 data, bool open)
    {
        if (!instance)
            return;
        instance->HandleGameObject(instance->GetGuidData(data), open);
        if (data == DATA_ARENA1)
            _southGateOpen = open;
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    std::string Due(uint32 at) const
    {
        return at ? Acore::StringFormat("{}", at > _clockMs ? at - _clockMs : 0) : std::string("-");
    }

    static npc_grimstone_rework* AIOf(Map* map, ObjectGuid guid)
    {
        Creature* grimstone = map ? map->GetCreature(guid) : nullptr;
        return grimstone && grimstone->IsAIEnabled ? dynamic_cast<npc_grimstone_rework*>(grimstone->AI()) : nullptr;
    }

    InstanceScript* instance;
    SummonList summons;
    std::unique_ptr<EncoreScript> _encore;

    Step _step = Step::Idle;
    uint32 _stepMs = 0;
    uint32 _clockMs = 0;
    uint32 _beat = 0;
    uint32 _syncMs = 0;
    uint32 _noPlayerMs = 0;
    bool _begun = false;
    bool _over = false;

    bool _heroic = false;
    Sentence _sentence = Sentence::Fire;
    uint32 _wave = 0;
    uint32 _first = 0;
    uint32 _second = 1;
    uint32 _favor = kFavorStart;
    bool _encoreLit = false;

    bool _waveSpawned = false;
    uint32 _waveSpawnedAtMs = 0;
    bool _southGateOpen = false;
    uint32 _beastsGateCloseAtMs = 0;
    GuidSet _openers;
    GuidSet _beastAdds;
    GuidSet _joined;
    std::unordered_set<ObjectGuid> _alive;
    DungeonKit::DeathSpots _deaths;

    uint8 _pendingChampion = 0;
    uint32 _pendingSlot = 0;
    ObjectGuid _champion;
    ObjectGuid _championGuids[2];
    uint32 _championMissingMs = 0;

    bool _giftArmed = false;
    uint32 _giftAtMs = 0;
    bool _jeerArmed = false;
    uint32 _jeerAtMs = 0;
    uint32 _fireAtMs = 0;
    uint32 _fireQuadrant = 0;
    uint32 _fireCount = 0;
    uint32 _beastsAtMs = 0;
    uint32 _sigAtMs = 0;
    uint32 _sigTurn = 0;

    uint32 _volleyId = 0;
    std::map<uint32, VolleyJudge> _volleys;
    std::vector<MechanicHandle> _live;
    std::unordered_map<ObjectGuid, std::function<void(BossMechanics::Descriptor&)>> _unitFills;
};

// ---------------------------------------------------------------------------------------------------------------------
// RingOfLawFight.h: the lookups and the Favor judges
// ---------------------------------------------------------------------------------------------------------------------

BrdRingOfLaw::RingFrame* BrdRingOfLaw::FrameOf(WorldObject const* any)
{
    if (!any || !any->IsInWorld())
        return nullptr;
    InstanceScript* instance = any->GetInstanceScript();
    Map* map = any->GetMap();
    if (!instance || !map || map->GetId() != kMapBlackrockDepths)
        return nullptr;
    Creature* grimstone = map->GetCreature(instance->GetGuidData(kGuidGrimstone));
    if (!grimstone || !grimstone->IsAlive() || !grimstone->IsAIEnabled)
        return nullptr;
    RingFrame* frame = dynamic_cast<RingFrame*>(grimstone->AI());
    return frame && frame->CurrentStep() != Step::Idle ? frame : nullptr;
}

BossMechanics::MechanicRef& BrdRingOfLaw::Judged(BossMechanics::MechanicRef& ref, WorldObject const* any,
    char const* source)
{
    Map* map = any ? any->GetMap() : nullptr;
    uint32 const instanceId = map ? map->GetInstanceId() : 0;
    ref.OnResolve([map, instanceId, source](BossMechanics::ResolveResult const& r)
    {
        if (!map || map->GetInstanceId() != instanceId)
            return;
        InstanceScript* instance = map->ToInstanceMap() ? map->ToInstanceMap()->GetInstanceScript() : nullptr;
        Creature* grimstone = instance ? map->GetCreature(instance->GetGuidData(kGuidGrimstone)) : nullptr;
        if (RingFrame* frame = FrameOf(grimstone))
            frame->JudgeResolve(r, source);
    });
    return ref;
}

BossMechanics::MechanicRef& BrdRingOfLaw::JudgedPersistent(BossMechanics::MechanicRef& ref, WorldObject const* any,
    char const* source)
{
    Map* map = any ? any->GetMap() : nullptr;
    uint32 const instanceId = map ? map->GetInstanceId() : 0;
    auto seen = std::make_shared<std::unordered_set<ObjectGuid>>();
    auto first = std::make_shared<bool>(true);
    ref.OnResolve([map, instanceId, source, seen, first](BossMechanics::ResolveResult const& r)
    {
        if (!map || map->GetInstanceId() != instanceId)
            return;
        InstanceScript* instance = map->ToInstanceMap() ? map->ToInstanceMap()->GetInstanceScript() : nullptr;
        Creature* grimstone = instance ? map->GetCreature(instance->GetGuidData(kGuidGrimstone)) : nullptr;
        RingFrame* frame = FrameOf(grimstone);
        bool const landing = *first;
        *first = false;
        for (ObjectGuid const& guid : r.hits)
            if (guid.IsPlayer() && seen->insert(guid).second && frame && !landing)
                frame->FavorHit(guid, source);
        if (landing && frame)
            frame->JudgeResolve(r, source);
    });
    return ref;
}

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest brd ring ...`
// ---------------------------------------------------------------------------------------------------------------------

namespace
{
    npc_grimstone_rework* GrimstoneAI(ChatHandler* handler)
    {
        Creature* grimstone = BrdTest::FindBoss(handler, NPC_GRIMSTONE);
        auto* ai = grimstone && grimstone->IsAIEnabled ? dynamic_cast<npc_grimstone_rework*>(grimstone->AI())
            : nullptr;
        if (!ai && grimstone)
            handler->SendErrorMessage("{} does not run the reworked script.", grimstone->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        npc_grimstone_rework* ai = GrimstoneAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(kind);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    // `.dbtest brd ring info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_GRIMSTONE, BOSS_RING_OF_LAW);
    }

    // `.dbtest brd ring state`: the step, Favor, the rolls, the clocks.
    bool HandleState(ChatHandler* handler)
    {
        npc_grimstone_rework* ai = GrimstoneAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest brd ring start`: the area trigger's start (the instance summons Grimstone). Turn GM mode off first: a
    // floor with no living non-GM player is a wipe.
    bool HandleStart(ChatHandler* handler)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        if (instance->GetData(TYPE_RING_OF_LAW) == IN_PROGRESS || instance->GetData(TYPE_RING_OF_LAW) == DONE)
        {
            handler->SendErrorMessage("The Ring is already running or done (`.dbtest brd instance boss 3 0` resets "
                "the slot).");
            return false;
        }
        instance->SetData(TYPE_RING_OF_LAW, IN_PROGRESS);
        handler->SendSysMessage("The Ring of Law starts (Grimstone comes in). GM mode must be off on the floor.");
        return true;
    }

    // `.dbtest brd ring favor <0-10>`
    bool HandleFavor(ChatHandler* handler, uint32 favor)
    {
        npc_grimstone_rework* ai = GrimstoneAI(handler);
        if (!ai)
            return false;
        ai->TestFavor(favor);
        handler->PSendSysMessage("Favor set to {}.", std::min(favor, kFavorMax));
        return true;
    }

    bool HandleJeer(ChatHandler* handler) { return Fire(handler, TestKind::Jeer, "A volley of jeers (1.5 s)."); }
    bool HandleGift(ChatHandler* handler) { return Fire(handler, TestKind::Gift, "The crowd's gift."); }
    bool HandleFire(ChatHandler* handler) { return Fire(handler, TestKind::Fire, "Trial by Fire: the next wedge."); }
    bool HandleBeast(ChatHandler* handler) { return Fire(handler, TestKind::Beast, "A beast through the gate."); }
    bool HandleSig(ChatHandler* handler) { return Fire(handler, TestKind::Signature, "The wave's signature."); }
    bool HandleNext(ChatHandler* handler) { return Fire(handler, TestKind::Next, "Skipped to the next step."); }
    bool HandleWin(ChatHandler* handler) { return Fire(handler, TestKind::Win, "The Ring is won (credit)."); }
    bool HandleWipe(ChatHandler* handler) { return Fire(handler, TestKind::Wipe, "The attempt wiped."); }

    ChatCommandTable const& NpcGrimstoneTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,    SEC_GAMEMASTER, Console::No },
            { "start",  HandleStart,    SEC_GAMEMASTER, Console::No },
            { "favor",  HandleFavor,    SEC_GAMEMASTER, Console::No },
            { "jeer",   HandleJeer,     SEC_GAMEMASTER, Console::No },
            { "gift",   HandleGift,     SEC_GAMEMASTER, Console::No },
            { "fire",   HandleFire,     SEC_GAMEMASTER, Console::No },
            { "beast",  HandleBeast,    SEC_GAMEMASTER, Console::No },
            { "sig",    HandleSig,      SEC_GAMEMASTER, Console::No },
            { "next",   HandleNext,     SEC_GAMEMASTER, Console::No },
            { "win",    HandleWin,      SEC_GAMEMASTER, Console::No },
            { "wipe",   HandleWipe,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_npc_grimstone_rework()
{
    if (BrdRingOfLaw::kBound)
        RegisterDungeonReworkCreatureAI(npc_grimstone_rework, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("ring", NpcGrimstoneTestCommands());
}
