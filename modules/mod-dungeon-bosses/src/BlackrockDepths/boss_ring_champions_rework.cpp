/*
 * mod-dungeon-bosses, Blackrock Depths D5: the Ring of Law's six champions (boss_gorosh_the_dervish_rework 9027,
 * boss_grizzle_rework 9028, boss_eviscerator_rework 9029, boss_okthor_rework 9030, boss_anubshiah_rework 9031,
 * boss_hedrum_rework 9032), Anub'shiah's Risen beasts (npc_brd_risen_beast 300782-300787) and the Risen Champion
 * (npc_brd_risen_champion 300788). Build spec S1 "Champion: ..." sections and the Ring's Build spec rows CH1, GO1-GO2,
 * GZ1-GZ3, EV1-EV3, OK1-OK3, AN1-AN3, HE1-HE2 (docs/dungeons/blackrock-depths-1-detention-block.md; rulings 23-25, 27,
 * 88); handoff sections 3.4-3.11 (rows D5), section 7 #16. Replaces the six stock BossAI scripts (unbound by
 * apps/dbc-tools source/npcs/blackrock_depths/ring_champions.py). Pure rules: RingChampionsLogic.h.
 *
 * Grimstone (npc_grimstone_rework.cpp, D4) summons the rolled pair behind the east gate, engages each with every player
 * on the floor and sends the second DoAction(ACTION_RING_TITLE_HOLDER) (RingOfLawFight.h). The champions never call
 * Mechanic::Describe: their kicks, dispels, purges, holds and kill order go to RingFrame::SetUnitDescriptor (the Ring
 * keeps one descriptor, on Grimstone); every dodgeable registry hit feeds Crowd Favor (BrdRingOfLaw::Judged).
 *
 *   CH1  Title Holder      the second champion: +10% damage done, the arrival flash, the Molten legs token's loot mode
 *   GO1  Dervish Dance     15 s / 12 s: a random player (the tank too); a 2 s 6 yd line from him to their spot, then he
 *                          whirls down it (resolved as he passes) and ends in an 8 yd Whirlwind; 20% / 35% line, 25% /
 *                          40% end, both Weakened
 *   GO2  Returning Axe     20 s: a 3 yd landing at a random player's spot (2 s, 15% / 25%), the axe sticks 6 s; its
 *                          return line to him shows 4 s, locks 2 s before it flies (4 yd, 20% / 35%); G1's tags 6-8
 *        stock             Mortal Strike (the tank), Bloodlust (Magic: a purge is a reward)
 *   GZ1  Bull Rush         25 s: a random player (the tank too); a 2 s 5 yd line from him through them to the wall,
 *                          the charge (35% / 50% + a knockback off the line); at the wall he is Dazed 4 s (+30% damage
 *                          taken, held) and Killing Frenzy is cleared
 *   GZ2  Earthshaker Stomp 18 s: a 2.5 s wind-up, 12 yd round him, the tank too: 25% / 40% + a 2 s stun, Weakened
 *   GZ3  Killing Frenzy    15 s: a stack (+10% attack speed and damage), cap 5 / none, the stock emote; an Enrage: one
 *                          Tranquilizing Shot clears every stack (the script removes the rest)
 *   EV1  Spell Eater       25 s: an 8 s shell; every magic hit he takes is eaten (a Devoured stack, cap 15); at its end
 *                          Devoured Magic hits every player on the floor for 2% a stack. A purge or Spellsteal ends it
 *                          with nothing released. Bots hold magic damage on him while it is up (DS HoldEntry)
 *   EV2  Open Wounds       20 s: a 15 s bleed on a random non-tank, 2% every 3 s; every 3 s it jumps to anyone within
 *                          5 yd of a bleeder (a registry Spread round the bleeders); one Favor judgment per bleed
 *   EV3  Volley            15 s / 12 s: the stock 3 s kickable Shadow Bolt Volley, rescaled (10% / 15%)
 *   OK1  Arcane Rupture    20 s / 15 s: a 3 s cast, then everything beyond 8 yd / 6 yd of him (to the farthest wall);
 *                          30% / 45%, Weakened; G1's tags 9 / 10
 *   OK2  Sheep Bolt        10 s after each Rupture: 1 / 2 circles of 5 yd at random players' spots, 2 s: 15% / 25%,
 *                          a 2 s Polymorph, Weakened
 *   OK3  Slow              15 s: one random player, 8 s, Magic; Arcane Bolt (stock) the filler
 *   AN1  Raise Dead        15 s: a 2 s bar, then one / two beasts of the opener's type rise where they died
 *                          (Grimstone's DeathSpots), at most the wave's size alive; heroic they keep their wave
 *                          mechanic; heroic, as the title holder below 50%, once: the fallen challenger as the Risen
 *                          Champion
 *   AN2  Web Spit          18 s: a 6 yd circle at a random player's spot, 2 s: 15% / 25%, root 2 s, Weakened; the web
 *                          stays 20 s (-50% movement)
 *   AN3  Curses            Tongues and Weakness, one random player each, 15 s (Curse: a dispel is a reward);
 *                          Shadow Bolt (stock, the tank: a kick is a reward) and Demon Armor (stock) kept
 *   HE1  Web Strands       25 s: three 4 yd lines from him to the wall (the first at a random player), 2 s: 20% / 35%,
 *                          root 2 s, Weakened; the strands stay 20 s / 30 s at -30%
 *   HE2  Reel In           20 s: the farthest player (heroic two) is pulled to his feet; 3 s later Baneful Burst, 10 yd
 *                          round him, the tank too: 30% / 45% + a 2%-a-second poison 8 s, Weakened
 *
 * A champion never walks off while the Ring runs (an evade puts it back on the floor players), and never chases off the
 * floor (the kit's arena guard, D4's floor polygon, no leash: Grimstone's wipe watch ends an attempt). Every firing
 * logs one INFO line "brd <champion> <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitBodies.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "RingChampionsLogic.h"
#include "RingOfLawFight.h"
#include "RingOfLawLogic.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdRingChampions;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using BossMechanics::ResolveResult;
using BrdRingOfLaw::RingFrame;
using DungeonKit::IsHeroicMap;
using DungeonKit::Vec2;

namespace
{
    uint32 constexpr POINT_DANCE = 1;
    uint32 constexpr POINT_RUSH = 2;
    uint32 constexpr GO_STUCK_AXE = 301250;     // Blackrock Spire's Stuck Axe (display 8494, GODI_STUCK_AXE), reused
    float constexpr kGroundBandYd = 6.f;

    // DoAction / GetData between Anub'shiah and his Risen beasts (heroic group signatures, as D4's beasts).
    int32 constexpr kRisenActionSignature = 0x52430001;
    uint32 constexpr kRisenDataFree = 1;

    // The test commands' forced mechanics (`.dbtest brd champions <champion> <mechanic>`).
    enum class TestKind : uint8
    {
        First,      // the champion's first signature
        Second,     // its second
        Third,      // its third (Killing Frenzy, Volley, Slow, the curses)
        Clear,
    };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogCh(char const* key, char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, key, mechanic, detail);
    }

    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > kGroundBandYd)
            return refZ;
        return h;
    }

    Position Spot(WorldObject const* probe, Vec2 p, float refZ, float o = 0.f)
    {
        return Position(p.x, p.y, GroundZ(probe, p.x, p.y, refZ), o);
    }

    // The Ring's frame from a map (a registry callback has no unit of ours to ask).
    RingFrame* FrameOfMap(Map* map, uint32 instanceId)
    {
        if (!map || map->GetInstanceId() != instanceId)
            return nullptr;
        InstanceMap* instanceMap = map->ToInstanceMap();
        InstanceScript* instance = instanceMap ? instanceMap->GetInstanceScript() : nullptr;
        Creature* grimstone = instance ? map->GetCreature(instance->GetGuidData(kGuidGrimstone)) : nullptr;
        return BrdRingOfLaw::FrameOf(grimstone);
    }

    // BrdRingOfLaw::Judged with a follow-up of our own in the same OnResolve (Judged takes the ref's only OnResolve).
    MechanicRef& JudgedThen(MechanicRef& ref, Creature* me, char const* source,
        std::function<void(Map*, ResolveResult const&)> then)
    {
        Map* map = me->GetMap();
        uint32 const instanceId = map ? map->GetInstanceId() : 0;
        ref.OnResolve([map, instanceId, source, then](ResolveResult const& r)
        {
            if (!map || map->GetInstanceId() != instanceId)
                return;
            if (RingFrame* frame = FrameOfMap(map, instanceId))
                frame->JudgeResolve(r, source);
            if (then)
                then(map, r);
        });
        return ref;
    }

    // A random player in the fight (the tank too, ruling 88).
    Player* AnyPlayer(Creature* me, float range = 100.f)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = range;
        return DungeonKit::PickPlayer(me, rule);
    }

    // Every player the champion fights: the frame's floor players, else (no frame: a test spawn) every live player in
    // range on its threat list.
    std::vector<Player*> FightPlayers(Creature* me)
    {
        if (RingFrame* frame = BrdRingOfLaw::FrameOf(me))
            return frame->FloorPlayers();
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
            if (Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr)
                if (player->IsAlive() && !player->IsGameMaster() && me->GetExactDist2d(player) <= kNoFrameRangeYd)
                    out.push_back(player);
        return out;
    }

    // A Ring unit (a champion, a Risen) that lost its target while the Ring runs: back on the floor players.
    bool BackOnTheFloor(Creature* me, ScriptedAI* ai)
    {
        RingFrame* frame = BrdRingOfLaw::FrameOf(me);
        if (!frame || !BrdRingOfLaw::FrameRuns(frame->CurrentStep()))
            return false;
        std::vector<Player*> const players = frame->FloorPlayers();
        if (players.empty())
            return false;
        for (Player* player : players)
            me->AddThreat(player, 0.f);
        ai->AttackStart(players[urand(0, uint32(players.size() - 1))]);
        return me->IsEngaged();
    }

    // The arena guard of a champion: the floor polygon (D4), no grips, never a chase off it, no leash (the Ring's wipe
    // watch ends an attempt; a champion that evaded would walk back behind the east gate).
    DungeonKit::ArenaGuardOptions ChampionGuard(char const* key)
    {
        DungeonKit::ArenaGuardOptions o = LeashOptions(key);
        o.evadeWhenBossOff = false;
        o.evadeNoTargetInsideMs = 0;
        return o;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The common champion: the pull, Title Holder, the frame, the descriptor, the cleanup, the arena guard
// ---------------------------------------------------------------------------------------------------------------------
class RingChampionAI : public ScriptedAI
{
public:
    RingChampionAI(Creature* creature, Champion which)
        : ScriptedAI(creature), _key(ChampionKey(which)), _summons(creature),
        _arena(BrdRingOfLaw::RingFloorArena(), ChampionGuard(ChampionKey(which))) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        Cleanup();
        _arena.Reset();
        _fighting = false;
        OnReset();
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        if (_fighting)
            return;
        _fighting = true;
        _heroic = _heroicForced ? _heroicSet : IsHeroicMap(me);
        RingFrame* frame = BrdRingOfLaw::FrameOf(me);
        _framed = frame != nullptr;
        if (frame)
            _order = std::max<uint8>(_order, frame->ChampionOrder(me->GetGUID()));
        OnBossPull(me, _key);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RING_OF_LAW;
        Mechanic::BeginEncounter(me, options);
        if (_framed)
            _arena.Engage(me);
        if (frame)
            frame->SetUnitDescriptor(me->GetGUID(), DescriptorFill());
        StartFight();
        LogCh(_key, "engage", Acore::StringFormat("order={} heroic={} framed={} health={}", _order, _heroic ? 1 : 0,
            _framed ? 1 : 0, me->GetMaxHealth()));
    }

    // CH1: Grimstone names the second champion right after its summon.
    void DoAction(int32 action) override
    {
        if (action == BrdRingOfLaw::ACTION_RING_TITLE_HOLDER)
            BecomeTitleHolder();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (BackOnTheFloor(me, this))
            return;
        LogCh(_key, "evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        ClearDescriptor();
        _fighting = false;
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        if (RingFrame* frame = BrdRingOfLaw::FrameOf(me))
            frame->BeastDeaths().Record(me, kChampionDeathTag);     // AN1's Risen Champion rises here
        ClearDescriptor();
        Cleanup();
        _summons.DespawnAll();
        LogCh(_key, "death", Acore::StringFormat("order={} lootmode={}", _order, me->GetLootMode()));
    }

    void JustSummoned(Creature* summon) override
    {
        if (summon->GetEntry() == NPC_BRD_STALKER)
            return;     // a look: it despawns on its own timer
        _summons.Summon(summon);
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        _summons.Despawn(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        UpdateAlways();
        if (!UpdateVictim())
            return;
        if (_framed && !_arena.Update(me, diff))
            return;
        if (!_fighting)
            return;
        UpdateFight();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The test commands
    // ----------------------------------------------------------------------------------------------------------------

    // `.dbtest brd champions <champion> <mechanic>`: forced firings (the champion must be fighting). "" on success.
    std::string TestFire(TestKind kind)
    {
        if (kind == TestKind::Clear)
        {
            Cleanup();
            OnReset();
            if (_fighting)
                StartFight();
            return {};
        }
        if (!_fighting || !me->IsEngaged())
            return "The champion is not fighting (pull it first: `.gm off`).";
        if (me->HasUnitState(UNIT_STATE_CASTING) || !Free())
            return "The champion is busy (a cast, a charge, a daze): try again in a moment.";
        return Fire(kind);
    }

    void TestHeroic(bool heroic)
    {
        _heroicForced = true;
        _heroicSet = heroic;
        _heroic = heroic;
    }

    void TestTitleHolder()
    {
        BecomeTitleHolder();
    }

    std::string TestState() const
    {
        return Acore::StringFormat("{} order={} heroic={} framed={} fighting={} title={} lootmode={} "
            "health={:.0f}% | {}", _key, _order, _heroic ? 1 : 0, _framed ? 1 : 0, _fighting ? 1 : 0,
            me->HasAura(SPELL_CH_TITLE_HOLDER) ? 1 : 0, me->GetLootMode(), me->GetHealthPct(), State());
    }

protected:
    // Per champion: its clocks on the pull, its firings, its state.
    virtual void OnReset() { }
    virtual void StartFight() = 0;
    virtual void UpdateFight() = 0;
    virtual void UpdateAlways() { }
    virtual bool Free() const { return true; }
    virtual std::string Fire(TestKind kind) = 0;
    virtual std::string State() const { return {}; }
    virtual void ExtraCleanup() { }
    // The champion's entries for the Ring's one descriptor (values only: nothing that dies with the unit).
    virtual std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const { return {}; }

    bool Heroic() const { return _heroic; }
    uint8 Order() const { return _order; }
    uint64 Now() const { return _clockMs; }
    char const* Key() const { return _key; }

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        LogCh(_key, mechanic, detail);
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 64)
            _live.erase(_live.begin(), _live.begin() + 32);
    }

    // Melee when nothing else runs.
    void Melee()
    {
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // Back into melee after a charge, a whirl or a daze.
    void BackToFight()
    {
        me->SetReactState(REACT_AGGRESSIVE);
        if (!me->IsEngaged())
            return;
        Unit* target = me->GetVictim();
        if (!target)
            target = me->SelectVictim();
        if (target)
        {
            me->GetMotionMaster()->Clear();
            ScriptedAI::AttackStart(target);
        }
    }

    // Hold still for a scripted move (no chase, no swing).
    void Hold()
    {
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->GetMotionMaster()->Clear();
        me->StopMoving();
    }

    SummonList const& Summons() const { return _summons; }

private:
    void BecomeTitleHolder()
    {
        _order = 2;
        me->CastSpell(me, SPELL_CH_TITLE_HOLDER, true);
        me->CastSpell(me, SPELL_CH_TITLE_FLASH, true);
        me->AddLootMode(kTitleHolderLootMode);     // the Molten legs token (rule 1: never in JustDied)
        Log("title-holder", Acore::StringFormat("lootmode={}", me->GetLootMode()));
    }

    void ClearDescriptor()
    {
        if (RingFrame* frame = BrdRingOfLaw::FrameOf(me))
            frame->ClearUnitDescriptor(me->GetGUID());
    }

    // Rule 6: every zone, aura and look of the fight goes (the Title Holder aura and the loot mode stay: the champion
    // keeps its title until it dies).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        ExtraCleanup();
        if (InstanceScript* instance = me->GetInstanceScript())
            for (uint32 spell : kChampionPlayerAuras)
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        me->SetReactState(REACT_AGGRESSIVE);
    }

    char const* _key;
    SummonList _summons;
    DungeonKit::ArenaGuard _arena;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;
    bool _fighting = false;
    bool _framed = false;
    bool _heroic = false;
    bool _heroicForced = false;
    bool _heroicSet = false;
    uint8 _order = 0;
};

// The champion AI of a creature (the test commands).
RingChampionAI* ChampionAI(Creature* creature)
{
    return creature && creature->IsAIEnabled ? dynamic_cast<RingChampionAI*>(creature->AI()) : nullptr;
}

// ---------------------------------------------------------------------------------------------------------------------
// Gorosh the Dervish 9027: GO1 Dervish Dance, GO2 Returning Axe; Mortal Strike and Bloodlust kept
// ---------------------------------------------------------------------------------------------------------------------
struct boss_gorosh_the_dervish_rework : public RingChampionAI
{
    explicit boss_gorosh_the_dervish_rework(Creature* creature) : RingChampionAI(creature, Champion::Gorosh) { }

    enum class Dance : uint8
    {
        None,
        Warn,       // the 2 s bar and line
        Whirl,      // down the line
    };

    // One axe at a time (20 s cadence, 8 s timeline).
    struct Axe
    {
        Position spot;
        uint64 thrownAt = 0;
        uint8 stage = 0;            // 0 none, 1 in the air, 2 stuck (shown line), 3 locked, done after the return
        ObjectGuid go;
        ObjectGuid stalker;
        MechanicHandle shown;
    };

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_DANCE && _dance == Dance::Whirl)
            EndDance("arrived");
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        // Rule 13: a bar that never finished lands nothing (no stun or silence breaks it today: 1972, no prevention).
        if (spell && spell->Id == SPELL_GO_DANCE_BAR && _dance == Dance::Warn)
        {
            Mechanic::Cancel(me, _danceLine);
            Mechanic::Cancel(me, _danceEnd);
            _dance = Dance::None;
            BackToFight();
            Log("dance-stopped");
        }
    }

protected:
    void OnReset() override
    {
        _dance = Dance::None;
    }

    void StartFight() override
    {
        _danceAt = Now() + FirstOf(kDanceEveryMs(Heroic()));
        _axeAt = Now() + FirstOf(kAxeEveryMs);
        _mortalStrikeAt = Now() + kMortalStrikeFirstMs;
        _bloodlustAt = Now() + kBloodlustFirstMs;
    }

    bool Free() const override
    {
        return _dance == Dance::None;
    }

    void UpdateAlways() override
    {
        UpdateAxe();
        if (_dance == Dance::Warn && Now() >= _danceStepAt)
            StartWhirl();
        else if (_dance == Dance::Whirl && Now() >= _danceStepAt)
            EndDance("timeout");
    }

    void UpdateFight() override
    {
        if (_dance != Dance::None || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (Now() >= _danceAt)
        {
            _danceAt = Now() + kDanceEveryMs(Heroic());
            if (DervishDance())
                return;
        }
        if (Now() >= _axeAt && !_axe.stage)
        {
            _axeAt = Now() + kAxeEveryMs;
            ReturningAxe();
        }
        if (Now() >= _mortalStrikeAt)
        {
            _mortalStrikeAt = Now() + urand(kMortalStrikeMinMs, kMortalStrikeMaxMs);
            if (Unit* victim = me->GetVictim())
            {
                DoCast(victim, SPELL_STOCK_MORTAL_STRIKE);
                return;
            }
        }
        if (Now() >= _bloodlustAt)
        {
            _bloodlustAt = Now() + urand(kBloodlustMinMs, kBloodlustMaxMs);
            DoCastSelf(SPELL_STOCK_BLOODLUST);
            Log("bloodlust");
            return;
        }
        Melee();
    }

    std::string Fire(TestKind kind) override
    {
        switch (kind)
        {
            case TestKind::First:
                return DervishDance() ? std::string() : std::string("No player to dance at.");
            case TestKind::Second:
                if (_axe.stage)
                    return "An axe is already out.";
                return ReturningAxe() ? std::string() : std::string("No player to throw at.");
            case TestKind::Third:
                DoCastSelf(SPELL_STOCK_BLOODLUST, true);
                return {};
            default:
                return {};
        }
    }

    std::string State() const override
    {
        return Acore::StringFormat("dance={} axe-stage={} next dance={}ms axe={}ms", uint32(_dance), _axe.stage,
            _danceAt > Now() ? _danceAt - Now() : 0, _axeAt > Now() ? _axeAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        me->RemoveAurasDueToSpell(SPELL_GO_DANCE_LOOK);
        _dance = Dance::None;
        ClearAxe();
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        return [](BossMechanics::Descriptor& d)
        {
            d.purges.emplace_back(NPC_GOROSH, SPELL_STOCK_BLOODLUST, 1);     // a reward
        };
    }

private:
    // GO1: the line (resolved as he passes, Projectile) and the end's Whirlwind (when he gets there).
    bool DervishDance()
    {
        Player* target = AnyPlayer(me);
        if (!target)
            return false;
        Vec2 const from = DungeonKit::PlaneOf(me);
        Vec2 const end = DanceEnd(from, DungeonKit::PlaneOf(target));
        float const length = DungeonKit::Distance(from, end);
        float const facing = DungeonKit::BearingTo(from, end);
        _danceFrom = Spot(me, from, me->GetPositionZ(), facing);
        _danceTo = Spot(me, end, target->GetPositionZ(), facing);
        _danceTravelMs = DanceTravelMs(length);
        bool const heroic = Heroic();

        Hold();
        me->SetFacingTo(facing);
        DungeonKit::CastBar(me, SPELL_GO_DANCE_BAR);
        MechanicRef line = Mechanic::Line(me, BossMechanics::Anchor(_danceFrom), BossMechanics::Anchor(_danceTo),
            kDanceWidth, Ms(kDanceWarnMs));
        line.Projectile(kDanceSpeed).Damage(kDanceLinePct(heroic)).TankDamage(kDanceLinePct(heroic))
            .Weakened().Spell(SPELL_GO_DANCE_LINE)
            .Tag(TAG_GO_DANCE_LINE);
        BrdRingOfLaw::Judged(line, me, "dervish-dance");
        _danceLine = line.Handle();
        Track(_danceLine);
        MechanicRef circle = Mechanic::Circle(me, BossMechanics::Anchor(_danceTo), kDanceEndRadius,
            Ms(kDanceWarnMs + _danceTravelMs));
        circle.Damage(kDanceEndPct(heroic)).TankDamage(kDanceEndPct(heroic))
            .Weakened().Spell(SPELL_GO_DANCE_END).Tag(TAG_GO_DANCE_END);
        BrdRingOfLaw::Judged(circle, me, "dervish-whirlwind");
        _danceEnd = circle.Handle();
        Track(_danceEnd);

        _dance = Dance::Warn;
        _danceStepAt = Now() + kDanceWarnMs;
        Log("dervish-dance", Acore::StringFormat("target={} length={:.1f} travel={}ms pct={:.0f}/{:.0f}",
            target->GetName(), length, _danceTravelMs, kDanceLinePct(heroic), kDanceEndPct(heroic)));
        return true;
    }

    void StartWhirl()
    {
        _dance = Dance::Whirl;
        _danceStepAt = Now() + _danceTravelMs + 1000;
        me->CastSpell(me, SPELL_GO_DANCE_LOOK, true);
        me->GetMotionMaster()->MoveCharge(_danceTo.GetPositionX(), _danceTo.GetPositionY(), _danceTo.GetPositionZ(),
            kDanceSpeed, POINT_DANCE);
    }

    void EndDance(char const* why)
    {
        _dance = Dance::None;
        me->RemoveAurasDueToSpell(SPELL_GO_DANCE_LOOK);
        BackToFight();
        Log("dance-end", why);
    }

    // GO2: the landing (a 3 yd circle, 2 s), then the axe in the floor.
    bool ReturningAxe()
    {
        Player* target = AnyPlayer(me);
        if (!target)
            return false;
        bool const heroic = Heroic();
        Position const spot = Spot(me, DungeonKit::PlaneOf(target), target->GetPositionZ());
        me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_GO_AXE_THROW_LOOK, true);
        MechanicRef land = Mechanic::Circle(me, BossMechanics::Anchor(spot), kAxeLandRadius, Ms(kAxeLandMs));
        land.Damage(kAxeLandPct(heroic)).TankDamage(kAxeLandPct(heroic))
            .Weakened().Spell(SPELL_GO_AXE_LAND).Tag(TAG_GO_AXE);
        BrdRingOfLaw::Judged(land, me, "returning-axe");
        Track(land.Handle());
        _axe = Axe();
        _axe.spot = spot;
        _axe.thrownAt = Now();
        _axe.stage = 1;
        Log("returning-axe", Acore::StringFormat("target={} pct={:.0f}/{:.0f}", target->GetName(),
            kAxeLandPct(heroic), kAxeReturnPct(heroic)));
        return true;
    }

    // GO2's timeline: stuck at 2 s (the axe, the chain, the shown line), locked at 6 s, flies home at 8 s.
    void UpdateAxe()
    {
        if (!_axe.stage)
            return;
        uint64 const t = Now() - _axe.thrownAt;
        if (_axe.stage == 1 && t >= kAxeLandMs)
            AxeStuck();
        else if (_axe.stage == 2 && t >= AxeLockAtMs())
            AxeLocked();
        else if (_axe.stage == 3 && t >= AxeReturnAtMs())
            AxeHome();
    }

    void AxeStuck()
    {
        _axe.stage = 2;
        Position const& p = _axe.spot;
        if (GameObject* go = me->SummonGameObject(GO_STUCK_AXE, p.GetPositionX(), p.GetPositionY(), p.GetPositionZ(),
            me->GetAngle(&p), 0.f, 0.f, 0.f, 0.f, (kAxeStuckMs + 2000) / 1000))
            _axe.go = go->GetGUID();
        if (Creature* stalker = me->SummonCreature(NPC_BRD_STALKER, p, TEMPSUMMON_TIMED_DESPAWN,
            kAxeStuckMs + 1500))
        {
            _axe.stalker = stalker->GetGUID();
            stalker->CastSpell(me, SPELL_GO_AXE_CHAIN, true);
        }
        // The shown line (G1 tag 7, no damage): from the axe to him, live in direction (Shapes::Line, its length is
        // the distance now), until the lock.
        if (me->GetExactDist2d(&p) >= kAxeMinReturnLength)
        {
            MechanicRef shown = Mechanic::Line(me, BossMechanics::Anchor(p), BossMechanics::Anchor(me),
                kAxeReturnWidth, Ms(kAxeShownMs));
            shown.Tag(TAG_GO_AXE_SHOWN);
            _axe.shown = shown.Handle();
            Track(_axe.shown);
        }
        Log("axe-stuck", Acore::StringFormat("x={:.1f} y={:.1f}", p.GetPositionX(), p.GetPositionY()));
    }

    // The lock: a point-to-point line from the axe to where he stands now; the tank moved him off the group or not.
    void AxeLocked()
    {
        _axe.stage = 3;
        Mechanic::Cancel(me, _axe.shown);
        Position const& p = _axe.spot;
        float const length = me->GetExactDist2d(&p);
        if (length < kAxeMinReturnLength)
        {
            Log("axe-lock", "on him: no line");
            return;
        }
        Position const at(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), 0.f);
        MechanicRef line = Mechanic::Line(me, BossMechanics::Anchor(p), BossMechanics::Anchor(at), kAxeReturnWidth,
            Ms(kAxeLockMs));
        line.Damage(kAxeReturnPct(Heroic())).TankDamage(kAxeReturnPct(Heroic()))
            .Weakened().Spell(SPELL_GO_AXE_RETURN).Tag(TAG_GO_AXE_RETURN);
        BrdRingOfLaw::Judged(line, me, "axe-return");
        Track(line.Handle());
        Log("axe-lock", Acore::StringFormat("length={:.1f}", length));
    }

    void AxeHome()
    {
        if (Creature* stalker = ObjectAccessor::GetCreature(*me, _axe.stalker))
        {
            stalker->InterruptNonMeleeSpells(false);
            stalker->CastSpell(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), SPELL_GO_AXE_RETURN_LOOK,
                true);
        }
        if (GameObject* go = ObjectAccessor::GetGameObject(*me, _axe.go))
            go->DespawnOrUnsummon();
        _axe = Axe();
        Log("axe-home");
    }

    void ClearAxe()
    {
        if (_axe.shown)
            Mechanic::Cancel(me, _axe.shown);
        if (GameObject* go = ObjectAccessor::GetGameObject(*me, _axe.go))
            go->DespawnOrUnsummon();
        if (Creature* stalker = ObjectAccessor::GetCreature(*me, _axe.stalker))
            stalker->DespawnOrUnsummon();
        _axe = Axe();
    }

    Dance _dance = Dance::None;
    uint64 _danceStepAt = 0;
    uint32 _danceTravelMs = 0;
    Position _danceFrom;
    Position _danceTo;
    MechanicHandle _danceLine;
    MechanicHandle _danceEnd;
    Axe _axe;
    uint64 _danceAt = 0;
    uint64 _axeAt = 0;
    uint64 _mortalStrikeAt = 0;
    uint64 _bloodlustAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Grizzle 9028: GZ1 Bull Rush, GZ2 Earthshaker Stomp, GZ3 Killing Frenzy
// ---------------------------------------------------------------------------------------------------------------------
struct boss_grizzle_rework : public RingChampionAI
{
    explicit boss_grizzle_rework(Creature* creature) : RingChampionAI(creature, Champion::Grizzle) { }

    enum class Rush : uint8
    {
        None,
        Warn,       // the 2 s bar and line
        Charge,     // on his way to the wall
        Dazed,      // 4 s at the wall
    };

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_RUSH && _rush == Rush::Charge)
            HitTheWall("arrived");
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        if (spell->Id == SPELL_GZ_STOMP_BAR && _stomp)
        {
            Mechanic::Cancel(me, _stomp);
            _stomp = MechanicHandle();
            Log("stomp-stopped");
        }
        else if (spell->Id == SPELL_GZ_RUSH_BAR && _rush == Rush::Warn)
        {
            Mechanic::Cancel(me, _rushLine);
            _rush = Rush::None;
            BackToFight();
            Log("rush-stopped");
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_GZ_STOMP_BAR)
            _stomp = MechanicHandle();      // landed: the registry resolves it
    }

protected:
    void OnReset() override
    {
        _rush = Rush::None;
        _frenzy = 0;
    }

    void StartFight() override
    {
        _rushAt = Now() + FirstOf(kRushEveryMs);
        _stompAt = Now() + FirstOf(kStompEveryMs);
        _frenzyAt = Now() + FirstOf(kFrenzyEveryMs);
        _frenzy = 0;
    }

    bool Free() const override
    {
        return _rush == Rush::None;
    }

    void UpdateAlways() override
    {
        CheckFrenzy();
        if (_rush == Rush::Warn && Now() >= _rushStepAt)
            StartCharge();
        else if (_rush == Rush::Charge && Now() >= _rushStepAt)
            HitTheWall("timeout");
        else if (_rush == Rush::Dazed && Now() >= _rushStepAt)
            EndDaze();
    }

    void UpdateFight() override
    {
        if (_rush != Rush::None || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (Now() >= _frenzyAt)
        {
            _frenzyAt = Now() + kFrenzyEveryMs;
            KillingFrenzy();
        }
        if (Now() >= _rushAt)
        {
            _rushAt = Now() + kRushEveryMs;
            if (BullRush())
                return;
        }
        if (Now() >= _stompAt)
        {
            _stompAt = Now() + kStompEveryMs;
            EarthshakerStomp();
            return;
        }
        Melee();
    }

    std::string Fire(TestKind kind) override
    {
        switch (kind)
        {
            case TestKind::First:
                return BullRush() ? std::string() : std::string("No player, or he stands off the floor.");
            case TestKind::Second:
                EarthshakerStomp();
                return {};
            case TestKind::Third:
                KillingFrenzy();
                return {};
            default:
                return {};
        }
    }

    std::string State() const override
    {
        return Acore::StringFormat("rush={} frenzy={} next rush={}ms stomp={}ms frenzy={}ms", uint32(_rush), _frenzy,
            _rushAt > Now() ? _rushAt - Now() : 0, _stompAt > Now() ? _stompAt - Now() : 0,
            _frenzyAt > Now() ? _frenzyAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        if (_rush == Rush::Dazed)
            me->SetControlled(false, UNIT_STATE_ROOT);
        _rush = Rush::None;
        _stomp = MechanicHandle();
        _frenzy = 0;
        for (uint32 spell : { uint32(SPELL_GZ_KILLING_FRENZY), uint32(SPELL_GZ_DAZED), uint32(SPELL_GZ_RUSH_LOOK) })
            me->RemoveAurasDueToSpell(spell);
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        return [](BossMechanics::Descriptor& d)
        {
            d.purges.emplace_back(NPC_GRIZZLE, SPELL_GZ_KILLING_FRENZY, 2);  // the Enrage list (Tranquilizing Shot)
        };
    }

private:
    // GZ1: through a random player to the wall; the charge resolves the line as he passes (Projectile).
    bool BullRush()
    {
        Player* target = AnyPlayer(me);
        if (!target)
            return false;
        Vec2 const from = DungeonKit::PlaneOf(me);
        std::optional<Vec2> const end = BrdRingOfLaw::WallEnd(from, DungeonKit::PlaneOf(target), kRushWallInset);
        if (!end || DungeonKit::Distance(from, *end) < 2.f)
        {
            Log("bull-rush-none", "off the floor");
            return false;
        }
        bool const heroic = Heroic();
        float const facing = DungeonKit::BearingTo(from, *end);
        Position const start = Spot(me, from, me->GetPositionZ(), facing);
        _rushTo = Spot(me, *end, me->GetPositionZ(), facing);
        float const length = DungeonKit::Distance(from, *end);

        Hold();
        me->SetFacingTo(facing);
        DungeonKit::CastBar(me, SPELL_GZ_RUSH_BAR);
        Map* map = me->GetMap();
        Vec2 const a = from;
        Vec2 const b = *end;
        MechanicRef line = Mechanic::Line(me, BossMechanics::Anchor(start), BossMechanics::Anchor(_rushTo), kRushWidth,
            Ms(kRushWarnMs));
        line.Projectile(kRushSpeed).Damage(kRushPct(heroic)).TankDamage(kRushPct(heroic))
            .Spell(SPELL_GZ_RUSH).Tag(TAG_GZ_BULL_RUSH)
            .OnHit([map, a, b](Unit* hit)
            {
                // The knockback: off the line, away from the point of it nearest the player.
                if (!hit || !hit->IsPlayer() || !hit->IsInWorld() || hit->GetMap() != map)
                    return;
                float along = 0.f;
                Vec2 const p = DungeonKit::PlaneOf(hit);
                DungeonKit::SegmentDistance(a, b, p, &along);
                Vec2 const axis = DungeonKit::Advance(a, DungeonKit::BearingTo(a, b), along);   // `along` is in yd
                hit->KnockbackFrom(axis.x, axis.y, kRushKnockXY, kRushKnockZ);
            });
        BrdRingOfLaw::Judged(line, me, "bull-rush");
        _rushLine = line.Handle();
        Track(_rushLine);
        _rush = Rush::Warn;
        _rushStepAt = Now() + kRushWarnMs;
        _rushMs = static_cast<uint32>(length / kRushSpeed * 1000.f);
        Log("bull-rush", Acore::StringFormat("target={} length={:.1f} pct={:.0f}", target->GetName(), length,
            kRushPct(heroic)));
        return true;
    }

    void StartCharge()
    {
        _rush = Rush::Charge;
        _rushStepAt = Now() + std::min<uint64>(_rushMs + 1000, kRushTimeoutMs);
        me->CastSpell(me, SPELL_GZ_RUSH_LOOK, true);
        me->GetMotionMaster()->MoveCharge(_rushTo.GetPositionX(), _rushTo.GetPositionY(), _rushTo.GetPositionZ(),
            kRushSpeed, POINT_RUSH);
    }

    // The wall: Dazed (held, +30% damage taken) and Killing Frenzy cleared: the burst window.
    void HitTheWall(char const* why)
    {
        _rush = Rush::Dazed;
        _rushStepAt = Now() + kDazedMs;
        me->RemoveAurasDueToSpell(SPELL_GZ_RUSH_LOOK);
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        me->SetControlled(true, UNIT_STATE_ROOT);
        me->CastSpell(me, SPELL_GZ_WALL_IMPACT, true);
        me->CastSpell(me, SPELL_GZ_DAZED, true);
        uint32 const cleared = _frenzy;
        _frenzy = 0;
        me->RemoveAurasDueToSpell(SPELL_GZ_KILLING_FRENZY);
        Log("dazed", Acore::StringFormat("why={} frenzy-cleared={}", why, cleared));
    }

    void EndDaze()
    {
        _rush = Rush::None;
        me->SetControlled(false, UNIT_STATE_ROOT);
        me->RemoveAurasDueToSpell(SPELL_GZ_DAZED);
        BackToFight();
    }

    // GZ2: the wind-up and a 12 yd ring on him, the tank too.
    void EarthshakerStomp()
    {
        bool const heroic = Heroic();
        DungeonKit::CastBar(me, SPELL_GZ_STOMP_BAR);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(me), kStompRadius, Ms(kStompWarnMs));
        ref.Damage(kStompPct(heroic)).TankDamage(kStompPct(heroic))
            .Weakened().Spell(SPELL_GZ_STOMP).Rider(SPELL_GZ_STOMP_STUN).Tag(TAG_GZ_STOMP);
        BrdRingOfLaw::Judged(ref, me, "earthshaker-stomp");
        _stomp = ref.Handle();
        Track(_stomp);
        Log("earthshaker-stomp", Acore::StringFormat("pct={:.0f}", kStompPct(heroic)));
    }

    // GZ3: a stack and the stock emote.
    void KillingFrenzy()
    {
        uint32 const next = NextFrenzy(_frenzy, Heroic());
        if (next == _frenzy)
            return;     // capped (normal)
        _frenzy = DungeonKit::AddStacks(me, SPELL_GZ_KILLING_FRENZY, 1, me, FrenzyCap(Heroic()));
        me->CastSpell(me, SPELL_GZ_FRENZY_FLASH, true);
        Talk(EMOTE_GZ_KILLING_FRENZY);
        Log("killing-frenzy", Acore::StringFormat("stacks={}", _frenzy));
    }

    // A Tranquilizing Shot took one stack: every stack goes (S1).
    void CheckFrenzy()
    {
        if (!_frenzy)
            return;
        uint32 const now = DungeonKit::Stacks(me, SPELL_GZ_KILLING_FRENZY);
        if (!FrenzyDispelled(_frenzy, now))
            return;
        me->RemoveAurasDueToSpell(SPELL_GZ_KILLING_FRENZY);
        Log("frenzy-removed", Acore::StringFormat("had={} left={}", _frenzy, now));
        _frenzy = 0;
    }

    Rush _rush = Rush::None;
    uint64 _rushStepAt = 0;
    uint32 _rushMs = 0;
    Position _rushTo;
    MechanicHandle _rushLine;
    MechanicHandle _stomp;
    uint32 _frenzy = 0;
    uint64 _rushAt = 0;
    uint64 _stompAt = 0;
    uint64 _frenzyAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Eviscerator 9029: EV1 Spell Eater, EV2 Open Wounds, EV3 Shadow Bolt Volley
// ---------------------------------------------------------------------------------------------------------------------
struct boss_eviscerator_rework : public RingChampionAI
{
    explicit boss_eviscerator_rework(Creature* creature) : RingChampionAI(creature, Champion::Eviscerator) { }

    // EV1: every magic hit on the shell is eaten (a Devoured stack).
    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask mask) override
    {
        if (!_eating || !damage || !(mask & SPELL_SCHOOL_MASK_MAGIC) || !me->HasAura(SPELL_EV_SPELL_EATER))
            return;
        damage = 0;
        if (_devoured < kDevouredCap)
        {
            _devoured = AddDevoured(_devoured);
            DungeonKit::AddStacks(me, SPELL_EV_DEVOURED, 1, me, kDevouredCap);
        }
    }

    // EV2: a jump tick resolved (the registry Spread round the bleeders): who stood within 5 yd catches it.
    void WoundsJump(ResolveResult const& r)
    {
        if (!_wounds)
            return;
        _woundsSpread = MechanicHandle();
        std::vector<Player*> const carriers = Bleeders();
        int32 remaining = 0;
        for (Player* carrier : carriers)
            if (Aura* aura = carrier->GetAura(SPELL_EV_OPEN_WOUNDS, me->GetGUID()))
                remaining = std::max(remaining, aura->GetDuration());
        uint32 caught = 0;
        if (remaining > 0)
            for (ObjectGuid const& guid : r.hits)
                if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                    if (player->IsAlive() && !player->HasAura(SPELL_EV_OPEN_WOUNDS, me->GetGUID()))
                    {
                        me->CastSpell(player, SPELL_EV_OPEN_WOUNDS, true);
                        if (Aura* aura = player->GetAura(SPELL_EV_OPEN_WOUNDS, me->GetGUID()))
                            aura->SetDuration(remaining);
                        _woundsCaught.insert(guid);
                        ++caught;
                    }
        if (caught)
            Log("open-wounds-jump", Acore::StringFormat("caught={} left={}ms", caught, remaining));
        if (remaining > int32(kOpenWoundsTickMs / 2))
            WoundsSpread();
        else
            EndWounds();
    }

protected:
    void StartFight() override
    {
        _eaterAt = Now() + FirstOf(kSpellEaterEveryMs);
        _woundsAt = Now() + FirstOf(kOpenWoundsEveryMs);
        _volleyAt = Now() + FirstOf(kVolleyEveryMs(Heroic()));
        Mechanic::NoteNextCastIn(me, SPELL_EV_VOLLEY, Ms(FirstOf(kVolleyEveryMs(Heroic()))));
    }

    void UpdateAlways() override
    {
        // EV1's end: the shell ran out (release) or was purged / stolen early (nothing released: the reward).
        if (_eating && !me->HasAura(SPELL_EV_SPELL_EATER))
        {
            bool const ranOut = Now() + 250 >= _eaterEndAt;
            ReleaseDevoured(ranOut);
        }
    }

    void UpdateFight() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (Now() >= _eaterAt)
        {
            _eaterAt = Now() + kSpellEaterEveryMs;
            SpellEater();
        }
        if (Now() >= _woundsAt && !_wounds)
        {
            _woundsAt = Now() + kOpenWoundsEveryMs;
            OpenWounds();
        }
        if (Now() >= _volleyAt)
        {
            uint32 const every = kVolleyEveryMs(Heroic());
            _volleyAt = Now() + every;
            Mechanic::NoteNextCastIn(me, SPELL_EV_VOLLEY, Ms(every));
            me->CastSpell(me, SPELL_EV_VOLLEY, false);
            Log("volley", Acore::StringFormat("pct={:.0f}", kVolleyPct(Heroic())));
            return;
        }
        Melee();
    }

    std::string Fire(TestKind kind) override
    {
        switch (kind)
        {
            case TestKind::First:
                if (_eating)
                    return "The shell is already up.";
                SpellEater();
                return {};
            case TestKind::Second:
                if (_wounds)
                    return "Open Wounds is already out.";
                return OpenWounds() ? std::string() : std::string("No player to cut.");
            case TestKind::Third:
                me->CastSpell(me, SPELL_EV_VOLLEY, false);
                return {};
            default:
                return {};
        }
    }

    std::string State() const override
    {
        return Acore::StringFormat("eating={} devoured={} wounds={} caught={} next eater={}ms wounds={}ms volley={}ms",
            _eating ? 1 : 0, _devoured, _wounds ? 1 : 0, _woundsCaught.size(), _eaterAt > Now() ? _eaterAt - Now() : 0,
            _woundsAt > Now() ? _woundsAt - Now() : 0, _volleyAt > Now() ? _volleyAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        _eating = false;
        _devoured = 0;
        _wounds = false;
        _woundsCaught.clear();
        _woundsSpread = MechanicHandle();
        for (uint32 spell : { uint32(SPELL_EV_SPELL_EATER), uint32(SPELL_EV_DEVOURED) })
            me->RemoveAurasDueToSpell(spell);
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        bool const heroic = Heroic();
        return [heroic](BossMechanics::Descriptor& d)
        {
            // EV1: no bot magic damage on him while the shell is up (DS HoldEntry); a purge of it is the reward.
            d.holds.push_back(BossMechanics::HoldEntry::Damage(NPC_EVISCERATOR, SPELL_EV_SPELL_EATER,
                BossMechanics::kSchoolMaskMagic));
            d.purges.emplace_back(NPC_EVISCERATOR, SPELL_EV_SPELL_EATER, 2);
            // EV3: a reward on normal, expected on heroic.
            d.interrupts.emplace_back(NPC_EVISCERATOR, SPELL_EV_VOLLEY, kVolleyKickPriority(heroic),
                Ms(kVolleyEveryMs(heroic)));
        };
    }

private:
    // EV1: the shell for 8 s.
    void SpellEater()
    {
        me->RemoveAurasDueToSpell(SPELL_EV_DEVOURED);
        me->CastSpell(me, SPELL_EV_SPELL_EATER, true);
        _eating = me->HasAura(SPELL_EV_SPELL_EATER);
        _devoured = 0;
        _eaterEndAt = Now() + kSpellEaterMs;
        Log("spell-eater", Acore::StringFormat("ok={}", _eating ? 1 : 0));
    }

    // Devoured Magic: 2% a stack on every player he fights (cap 15 stacks, 30%), RefFlatOn per player.
    void ReleaseDevoured(bool ranOut)
    {
        _eating = false;
        uint32 const stacks = _devoured;
        _devoured = 0;
        me->RemoveAurasDueToSpell(SPELL_EV_DEVOURED);
        if (!ranOut || !stacks)
        {
            Log("spell-eater-end", Acore::StringFormat("purged={} stacks={}", ranOut ? 0 : 1, stacks));
            return;
        }
        float const pct = DevouredPct(stacks);
        me->CastSpell(me, SPELL_EV_DEVOURED_LOOK, true);
        uint32 hit = 0;
        for (Player* player : FightPlayers(me))
        {
            int32 const value = int32(DungeonKit::RefFlatOn(me, player, pct));
            me->CastCustomSpell(SPELL_EV_DEVOURED_MAGIC, SPELLVALUE_BASE_POINT0, value, player, true);
            ++hit;
        }
        Log("devoured-magic", Acore::StringFormat("stacks={} pct={:.0f} players={}", stacks, pct, hit));
    }

    // EV2: the bleed on a random non-tank (only the current victim is spared, ruling 88).
    bool OpenWounds()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return false;
        me->CastSpell(target, SPELL_EV_OPEN_WOUNDS, true);
        _wounds = true;
        _woundsCaught.clear();
        WoundsSpread();
        Log("open-wounds", Acore::StringFormat("target={}", target->GetName()));
        return true;
    }

    std::vector<Player*> Bleeders()
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                if (player->IsAlive() && player->HasAura(SPELL_EV_OPEN_WOUNDS, me->GetGUID()))
                    out.push_back(player);
        return out;
    }

    // The next jump tick: a registry Spread round every bleeder (the bots step 5 yd apart from them).
    void WoundsSpread()
    {
        GuidSet carriers;
        for (Player* player : Bleeders())
            carriers.insert(player->GetGUID());
        if (carriers.empty())
        {
            EndWounds();
            return;
        }
        Map* map = me->GetMap();
        ObjectGuid const self = me->GetGUID();
        MechanicRef ref = Mechanic::Spread(me, kOpenWoundsJumpYd, Ms(kOpenWoundsTickMs));
        ref.Targets(carriers).Spell(SPELL_EV_OPEN_WOUNDS_JUMP).Tag(TAG_EV_OPEN_WOUNDS)
            .OnResolve([map, self](ResolveResult const& r)
            {
                Creature* boss = map ? map->GetCreature(self) : nullptr;
                if (auto* ai = boss && boss->IsAlive() && boss->IsAIEnabled
                    ? dynamic_cast<boss_eviscerator_rework*>(boss->AI()) : nullptr)
                    ai->WoundsJump(r);
            });
        _woundsSpread = ref.Handle();
        Track(_woundsSpread);
    }

    // One Favor judgment per bleed: +1 when it never jumped, -1 per player it caught.
    void EndWounds()
    {
        if (!_wounds)
            return;
        _wounds = false;
        ResolveResult r;
        r.tag = TAG_EV_OPEN_WOUNDS;
        r.hits.assign(_woundsCaught.begin(), _woundsCaught.end());
        r.count = uint32(r.hits.size());
        if (RingFrame* frame = BrdRingOfLaw::FrameOf(me))
            frame->JudgeResolve(r, "open-wounds");
        Log("open-wounds-end", Acore::StringFormat("caught={}", _woundsCaught.size()));
        _woundsCaught.clear();
    }

    bool _eating = false;
    uint32 _devoured = 0;
    uint64 _eaterEndAt = 0;
    bool _wounds = false;
    GuidSet _woundsCaught;
    MechanicHandle _woundsSpread;
    uint64 _eaterAt = 0;
    uint64 _woundsAt = 0;
    uint64 _volleyAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Ok'thor the Breaker 9030: OK1 Arcane Rupture, OK2 Sheep Bolt, OK3 Slow; Arcane Bolt the filler
// ---------------------------------------------------------------------------------------------------------------------
struct boss_okthor_rework : public RingChampionAI
{
    explicit boss_okthor_rework(Creature* creature) : RingChampionAI(creature, Champion::Okthor) { }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_OK_RUPTURE_BAR && _rupture)
        {
            Mechanic::Cancel(me, _rupture);
            _rupture = MechanicHandle();
            Log("rupture-stopped");
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_OK_RUPTURE_BAR)
            _rupture = MechanicHandle();
    }

protected:
    void StartFight() override
    {
        _ruptureAt = Now() + FirstOf(kRuptureEveryMs(Heroic()));
        _sheepAt = 0;
        _slowAt = Now() + FirstOf(kSlowEveryMs);
        _boltAt = Now() + kArcaneBoltFirstMs;
    }

    void UpdateFight() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (Now() >= _ruptureAt)
        {
            _ruptureAt = Now() + kRuptureEveryMs(Heroic());
            ArcaneRupture();
            return;
        }
        if (_sheepAt && Now() >= _sheepAt)
        {
            _sheepAt = 0;
            SheepBolt();
        }
        if (Now() >= _slowAt)
        {
            _slowAt = Now() + kSlowEveryMs;
            Slow();
        }
        if (Now() >= _boltAt)
        {
            _boltAt = Now() + urand(kArcaneBoltMinMs, kArcaneBoltMaxMs);
            if (Player* target = AnyPlayer(me, 40.f))
            {
                DoCast(target, SPELL_STOCK_ARCANE_BOLT);
                return;
            }
        }
        Melee();
    }

    std::string Fire(TestKind kind) override
    {
        switch (kind)
        {
            case TestKind::First:
                ArcaneRupture();
                return {};
            case TestKind::Second:
                return SheepBolt() ? std::string() : std::string("No player to sheep.");
            case TestKind::Third:
                return Slow() ? std::string() : std::string("No player to slow.");
            default:
                return {};
        }
    }

    std::string State() const override
    {
        return Acore::StringFormat("next rupture={}ms sheep={} slow={}ms", _ruptureAt > Now() ? _ruptureAt - Now() : 0,
            _sheepAt ? Acore::StringFormat("{}ms", _sheepAt > Now() ? _sheepAt - Now() : 0) : std::string("-"),
            _slowAt > Now() ? _slowAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        _rupture = MechanicHandle();
        _sheepAt = 0;
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        return [](BossMechanics::Descriptor& d)
        {
            d.dispels.emplace_back(SPELL_OK_SLOW, 1);       // a reward
        };
    }

private:
    // OK1: the 3 s bar (Physical: rule 5, Arcane Bolt is the kickable Arcane), then everything beyond the inner ring.
    void ArcaneRupture()
    {
        bool const heroic = Heroic();
        float const inner = kRuptureInner(heroic);
        float const outer = RuptureOuter(DungeonKit::PlaneOf(me));
        DungeonKit::CastBar(me, SPELL_OK_RUPTURE_BAR);
        MechanicRef ref = Mechanic::Donut(me, BossMechanics::Anchor(me), inner, outer, Ms(kRuptureCastMs));
        ref.Damage(kRupturePct(heroic)).TankDamage(kRupturePct(heroic))
            .Weakened().Spell(SPELL_OK_RUPTURE).Tag(RuptureTag(heroic));
        BrdRingOfLaw::Judged(ref, me, "arcane-rupture");
        _rupture = ref.Handle();
        Track(_rupture);
        _sheepAt = Now() + kRuptureCastMs + kSheepAfterRuptureMs;
        Log("arcane-rupture", Acore::StringFormat("inner={:.0f} outer={:.1f} pct={:.0f}", inner, outer,
            kRupturePct(heroic)));
    }

    // OK2: 1 / 2 circles at distinct random players' spots (the tank too).
    bool SheepBolt()
    {
        bool const heroic = Heroic();
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        std::vector<Player*> const targets = DungeonKit::PickPlayers(me, rule, kSheepCount(heroic));
        for (Player* target : targets)
        {
            Position const spot = Spot(me, DungeonKit::PlaneOf(target), target->GetPositionZ());
            MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(spot), kSheepRadius, Ms(kSheepWarnMs));
            ref.Damage(kSheepPct(heroic)).TankDamage(kSheepPct(heroic))
                .Weakened().Spell(SPELL_OK_SHEEP_BOLT).Rider(SPELL_OK_SHEEP)
                .Tag(TAG_OK_SHEEP_BOLT);
            BrdRingOfLaw::Judged(ref, me, "sheep-bolt");
            Track(ref.Handle());
        }
        Log("sheep-bolt", Acore::StringFormat("circles={} pct={:.0f}", targets.size(), kSheepPct(heroic)));
        return !targets.empty();
    }

    // OK3: one random player, 8 s.
    bool Slow()
    {
        Player* target = AnyPlayer(me, 40.f);
        if (!target)
            return false;
        me->CastSpell(target, SPELL_OK_SLOW, true);
        Log("slow", Acore::StringFormat("target={}", target->GetName()));
        return true;
    }

    MechanicHandle _rupture;
    uint64 _ruptureAt = 0;
    uint64 _sheepAt = 0;
    uint64 _slowAt = 0;
    uint64 _boltAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Anub'shiah 9031: AN1 Raise Dead (Risen beasts, the Risen Champion), AN2 Web Spit, AN3 the curses; Shadow Bolt and
// Demon Armor kept
// ---------------------------------------------------------------------------------------------------------------------
struct boss_anubshiah_rework : public RingChampionAI
{
    explicit boss_anubshiah_rework(Creature* creature) : RingChampionAI(creature, Champion::Anubshiah) { }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_AN_RAISE_DEAD_BAR)
            RaiseDead();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_AN_RAISE_DEAD_BAR)
            Log("raise-dead-stopped");
    }

    // AN2: the impact resolved: the web stays.
    void WebPatch(Position const& spot)
    {
        DungeonKit::LingerSpec linger;
        linger.duration = Ms(kWebPatchMs);
        linger.tick = Ms(kWebPatchTickMs);
        linger.pct = 0.f;
        linger.spellId = SPELL_AN_PATCH_TICK;
        linger.slowSpell = SPELL_AN_WEB_SLOW;
        linger.tag = TAG_AN_WEB_PATCH;
        MechanicRef ref = DungeonKit::Linger(me, BossMechanics::Shapes::Circle(BossMechanics::Anchor(spot),
            kWebSpitRadius), linger);
        Track(ref.Handle());
        if (Creature* patch = me->SummonCreature(NPC_BRD_STALKER, spot, TEMPSUMMON_TIMED_DESPAWN, kWebPatchMs))
            patch->CastSpell(patch, SPELL_AN_WEB_PATCH, true);
    }

protected:
    void StartFight() override
    {
        _raiseAt = Now() + FirstOf(kRaiseEveryMs);
        _webAt = Now() + FirstOf(kWebSpitEveryMs);
        _tonguesAt = Now() + kTonguesFirstMs;
        _weaknessAt = Now() + kWeaknessFirstMs;
        _boltAt = Now() + kShadowBoltFirstMs;
        _risenSigAt = 0;
        _championDue = false;
        _championRaised = false;
        DoCastSelf(SPELL_STOCK_DEMON_ARMOR, true);
    }

    void UpdateFight() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (!_championDue && RaisesChampion(Heroic(), Order(), me->GetHealthPct(), _championRaised))
        {
            _championDue = true;
            _raiseAt = Now();       // the next Raise Dead now, the challenger with it
        }
        if (Now() >= _raiseAt)
        {
            _raiseAt = Now() + kRaiseEveryMs;
            if (StartRaise())
                return;
        }
        if (Now() >= _webAt)
        {
            _webAt = Now() + kWebSpitEveryMs;
            WebSpit();
        }
        if (Now() >= _tonguesAt)
        {
            _tonguesAt = Now() + urand(kTonguesMinMs, kTonguesMaxMs);
            Curse(SPELL_AN_CURSE_OF_TONGUES, "curse-of-tongues");
        }
        if (Now() >= _weaknessAt)
        {
            _weaknessAt = Now() + urand(kWeaknessMinMs, kWeaknessMaxMs);
            Curse(SPELL_AN_CURSE_OF_WEAKNESS, "curse-of-weakness");
        }
        RisenSignatures();
        if (Now() >= _boltAt)
        {
            _boltAt = Now() + urand(kShadowBoltMinMs, kShadowBoltMaxMs);
            if (Unit* victim = me->GetVictim())
            {
                DoCast(victim, SPELL_STOCK_SHADOW_BOLT);
                return;
            }
        }
        Melee();
    }

    std::string Fire(TestKind kind) override
    {
        switch (kind)
        {
            case TestKind::First:
                return StartRaise() ? std::string() : std::string("Nothing to raise (no frame, no spots, or capped).");
            case TestKind::Second:
                return WebSpit() ? std::string() : std::string("No player to spit at.");
            case TestKind::Third:
                Curse(SPELL_AN_CURSE_OF_TONGUES, "curse-of-tongues");
                Curse(SPELL_AN_CURSE_OF_WEAKNESS, "curse-of-weakness");
                return {};
            default:
                return {};
        }
    }

    std::string State() const override
    {
        return Acore::StringFormat("risen={} champion-due={} raised={} next raise={}ms web={}ms", AliveRisenCount(),
            _championDue ? 1 : 0, _championRaised ? 1 : 0, _raiseAt > Now() ? _raiseAt - Now() : 0,
            _webAt > Now() ? _webAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        _championDue = false;
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        return [](BossMechanics::Descriptor& d)
        {
            d.interrupts.emplace_back(NPC_ANUBSHIAH, SPELL_STOCK_SHADOW_BOLT, 1);   // a reward
            d.interrupts.emplace_back(NPC_BRD_RISEN_SCREECHER, BrdRingOfLaw::SPELL_RW_SCREECH,
                BrdRingOfLaw::kScreechKickPriority);
            d.dispels.emplace_back(SPELL_AN_CURSE_OF_TONGUES, 1);
            d.dispels.emplace_back(SPELL_AN_CURSE_OF_WEAKNESS, 1);
            // Kill order: the Risen beasts (cleave them down); the Risen Champion is the tank's.
            for (uint32 type = 0; type < BrdRingOfLaw::kWaveTypes.size(); ++type)
                d.targets.emplace_back(RisenEntry(type), 1);
            d.targets.emplace_back(NPC_BRD_RISEN_CHAMPION, 1, BossMechanics::Who::MainTank);
        };
    }

private:
    std::vector<Creature*> AliveRisen() const
    {
        std::vector<Creature*> out;
        for (ObjectGuid const& guid : Summons())
            if (Creature* c = ObjectAccessor::GetCreature(*me, guid))
                if (c->IsAlive() && RisenWaveType(c->GetEntry()))
                    out.push_back(c);
        return out;
    }

    uint32 AliveRisenCount() const { return uint32(AliveRisen().size()); }

    uint32 Raisable(RingFrame* frame) const
    {
        uint32 const type = frame->WaveType();
        DungeonKit::DeathSpotFilter filter;
        filter.tag = type + 1;
        uint32 const spots = uint32(frame->BeastDeaths().Count(filter));
        return RaiseCount(Heroic(), BrdRingOfLaw::kWaveTypes[type].count, AliveRisenCount(), spots);
    }

    // AN1: the 2 s bar when anything can rise (OnSpellCast raises).
    bool StartRaise()
    {
        RingFrame* frame = BrdRingOfLaw::FrameOf(me);
        if (!frame)
            return false;
        if (!Raisable(frame) && !_championDue)
        {
            Log("raise-dead-none", Acore::StringFormat("risen={}", AliveRisenCount()));
            return false;
        }
        DungeonKit::CastBar(me, SPELL_AN_RAISE_DEAD_BAR);
        return true;
    }

    void RaiseDead()
    {
        RingFrame* frame = BrdRingOfLaw::FrameOf(me);
        if (!frame)
            return;
        uint32 const type = frame->WaveType();
        uint32 const n = Raisable(frame);
        DungeonKit::DeathSpotFilter filter;
        filter.tag = type + 1;
        uint32 risen = 0;
        for (DungeonKit::DeathSpotAt const& spot : frame->BeastDeaths().TakeRandom(n, filter))
            if (Creature* beast = me->SummonCreature(RisenEntry(type), spot.at, TEMPSUMMON_CORPSE_TIMED_DESPAWN,
                10000))
            {
                beast->CastSpell(beast, SPELL_CH_RISEN, true);
                beast->CastSpell(beast, SPELL_AN_RAISE_DEAD_LOOK, true);
                frame->JoinRing(beast);
                ++risen;
            }
        if (_championDue && !_championRaised)
            RaiseChampion(frame);
        Log("raise-dead", Acore::StringFormat("type={} risen={} alive={} heroic={}", type, risen, AliveRisenCount(),
            Heroic() ? 1 : 0));
    }

    // Heroic, the title holder below 50%: the fallen challenger, melee only, in its own look.
    void RaiseChampion(RingFrame* frame)
    {
        _championRaised = true;
        _championDue = false;
        DungeonKit::DeathSpotFilter filter;
        filter.tag = kChampionDeathTag;
        std::vector<DungeonKit::DeathSpotAt> const spots = frame->BeastDeaths().TakeOldest(1, filter);
        Position const at = spots.empty() ? me->GetPosition() : spots.front().at;
        uint32 const fallen = spots.empty() ? 0 : spots.front().entry;
        Creature* champion = me->SummonCreature(NPC_BRD_RISEN_CHAMPION, at, TEMPSUMMON_CORPSE_TIMED_DESPAWN, 10000);
        if (!champion)
            return;
        if (CreatureTemplate const* tmpl = fallen ? sObjectMgr->GetCreatureTemplate(fallen) : nullptr)
            if (CreatureModel const* model = tmpl->GetFirstValidModel())
            {
                champion->SetDisplayId(model->CreatureDisplayID);
                champion->SetNativeDisplayId(model->CreatureDisplayID);
            }
        int8 equipId = 1;
        if (EquipmentInfo const* equip = fallen ? sObjectMgr->GetEquipmentInfo(fallen, equipId) : nullptr)
            for (uint8 i = 0; i < MAX_EQUIPMENT_ITEMS; ++i)
                champion->SetVirtualItem(i, equip->ItemEntry[i]);
        champion->CastSpell(champion, SPELL_CH_RISEN, true);
        champion->CastSpell(champion, SPELL_AN_RAISE_DEAD_LOOK, true);
        frame->JoinRing(champion);
        Log("risen-champion", Acore::StringFormat("fallen={} spot={}", fallen, spots.empty() ? 0 : 1));
    }

    // Heroic: the Risen keep their wave's group signature (Burrow, Tail Sting, Venom Spit) on his clock, one at a time.
    void RisenSignatures()
    {
        if (!Heroic())
            return;
        RingFrame* frame = BrdRingOfLaw::FrameOf(me);
        if (!frame)
            return;
        BrdRingOfLaw::WaveKind const& w = BrdRingOfLaw::kWaveTypes[frame->WaveType()];
        if (w.perBeast || w.signature == BrdRingOfLaw::Signature::AcidBurst)
            return;
        std::vector<Creature*> free;
        for (Creature* beast : AliveRisen())
            if (beast->IsEngaged() && beast->IsAIEnabled && beast->AI()->GetData(kRisenDataFree))
                free.push_back(beast);
        if (free.empty())
        {
            _risenSigAt = 0;
            return;
        }
        if (!_risenSigAt)
        {
            _risenSigAt = Now() + w.firstMs;
            return;
        }
        if (Now() < _risenSigAt)
            return;
        _risenSigAt = Now() + w.everyMs;
        free[_risenTurn++ % free.size()]->AI()->DoAction(kRisenActionSignature);
    }

    // AN2: a 6 yd circle at a random player's spot (the tank too), then the 20 s web.
    bool WebSpit()
    {
        Player* target = AnyPlayer(me);
        if (!target)
            return false;
        bool const heroic = Heroic();
        Position const spot = Spot(me, DungeonKit::PlaneOf(target), target->GetPositionZ());
        me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_AN_WEB_SPIT_LOOK, true);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(spot), kWebSpitRadius, Ms(kWebSpitWarnMs));
        ref.Damage(kWebSpitPct(heroic)).TankDamage(kWebSpitPct(heroic))
            .Weakened().Spell(SPELL_AN_WEB_SPIT).Rider(SPELL_AN_WEB_ROOT)
            .Tag(TAG_AN_WEB_SPIT);
        ObjectGuid const self = me->GetGUID();
        JudgedThen(ref, me, "web-spit", [self, spot](Map* map, ResolveResult const&)
        {
            Creature* boss = map->GetCreature(self);
            if (auto* ai = boss && boss->IsAlive() && boss->IsAIEnabled
                ? dynamic_cast<boss_anubshiah_rework*>(boss->AI()) : nullptr)
                ai->WebPatch(spot);
        });
        Track(ref.Handle());
        Log("web-spit", Acore::StringFormat("target={} pct={:.0f}", target->GetName(), kWebSpitPct(heroic)));
        return true;
    }

    // AN3: one random player.
    void Curse(uint32 spell, char const* name)
    {
        if (Player* target = AnyPlayer(me, 40.f))
        {
            me->CastSpell(target, spell, true);
            Log(name, Acore::StringFormat("target={}", target->GetName()));
        }
    }

    uint64 _raiseAt = 0;
    uint64 _webAt = 0;
    uint64 _tonguesAt = 0;
    uint64 _weaknessAt = 0;
    uint64 _boltAt = 0;
    uint64 _risenSigAt = 0;
    uint32 _risenTurn = 0;
    bool _championDue = false;
    bool _championRaised = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// Hedrum the Creeper 9032: HE1 Web Strands, HE2 Reel In + Baneful Burst (Hate to Zero and Paralyzing Poison removed)
// ---------------------------------------------------------------------------------------------------------------------
struct boss_hedrum_rework : public RingChampionAI
{
    explicit boss_hedrum_rework(Creature* creature) : RingChampionAI(creature, Champion::Hedrum) { }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_HE_STRANDS_BAR && !_strands.empty())
        {
            for (MechanicHandle const& h : _strands)
                Mechanic::Cancel(me, h);
            _strands.clear();
            Log("strands-stopped");
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_HE_STRANDS_BAR)
            _strands.clear();
    }

    // HE1: a strand's impact resolved: the web stays along it.
    void StrandWeb(Position const& from, Position const& to)
    {
        bool const heroic = Heroic();
        DungeonKit::LingerSpec linger;
        linger.duration = Ms(kStrandsLifeMs(heroic));
        linger.tick = Ms(kStrandsTickMs);
        linger.pct = 0.f;
        linger.spellId = SPELL_HE_STRAND_TICK;
        linger.slowSpell = SPELL_HE_STRANDS_SLOW;
        linger.tag = TAG_HE_STRAND_WEB;
        MechanicRef ref = DungeonKit::Linger(me, BossMechanics::Shapes::Line(BossMechanics::Anchor(from),
            BossMechanics::Anchor(to), kStrandsWidth), linger);
        Track(ref.Handle());
        float const length = from.GetExactDist2d(&to);
        float const facing = from.GetAngle(&to);
        for (float d = kStrandPatchStep / 2.f; d < length; d += kStrandPatchStep)
        {
            Vec2 const p = DungeonKit::Advance({ from.GetPositionX(), from.GetPositionY() }, facing, d);
            if (Creature* patch = me->SummonCreature(NPC_BRD_STALKER, Spot(me, p, from.GetPositionZ()),
                TEMPSUMMON_TIMED_DESPAWN, kStrandsLifeMs(heroic)))
                patch->CastSpell(patch, SPELL_HE_STRAND_PATCH, true);
        }
    }

protected:
    void OnReset() override
    {
        me->RemoveAurasDueToSpell(SPELL_STOCK_HATE_TO_ZERO);   // a threat wipe breaks bot tanking (the rev too)
    }

    void StartFight() override
    {
        me->RemoveAurasDueToSpell(SPELL_STOCK_HATE_TO_ZERO);
        _strandsAt = Now() + FirstOf(kStrandsEveryMs);
        _reelAt = Now() + FirstOf(kReelEveryMs);
    }

    void UpdateFight() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (Now() >= _strandsAt)
        {
            _strandsAt = Now() + kStrandsEveryMs;
            if (WebStrands())
                return;
        }
        if (Now() >= _reelAt)
        {
            _reelAt = Now() + kReelEveryMs;
            ReelIn();
        }
        Melee();
    }

    std::string Fire(TestKind kind) override
    {
        switch (kind)
        {
            case TestKind::First:
                return WebStrands() ? std::string() : std::string("No strand fits (off the floor).");
            case TestKind::Second:
                return ReelIn() ? std::string() : std::string("No player to reel in.");
            default:
                return "Hedrum has no third mechanic.";
        }
    }

    std::string State() const override
    {
        return Acore::StringFormat("next strands={}ms reel={}ms", _strandsAt > Now() ? _strandsAt - Now() : 0,
            _reelAt > Now() ? _reelAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        _strands.clear();
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        return [](BossMechanics::Descriptor& d)
        {
            d.dispels.emplace_back(SPELL_HE_BANEFUL_POISON, 1);    // a reward
        };
    }

private:
    // HE1: three lines from him to the wall, the first at a random player.
    bool WebStrands()
    {
        bool const heroic = Heroic();
        Vec2 const origin = DungeonKit::PlaneOf(me);
        Player* aim = AnyPlayer(me);
        float const first = aim ? DungeonKit::BearingTo(origin, DungeonKit::PlaneOf(aim))
            : frand(0.f, DungeonKit::kTwoPi);
        Position const from = Spot(me, origin, me->GetPositionZ());
        std::vector<std::pair<Position, Position>> lines;
        for (float const bearing : StrandBearings(first))
        {
            std::optional<Vec2> const end = WallAlong(origin, bearing, 0.5f);
            if (!end || DungeonKit::Distance(origin, *end) < kStrandsMinLength)
                continue;
            lines.emplace_back(from, Spot(me, *end, me->GetPositionZ()));
        }
        if (lines.empty())
        {
            Log("strands-none", "off the floor");
            return false;
        }
        DungeonKit::CastBar(me, SPELL_HE_STRANDS_BAR);
        ObjectGuid const self = me->GetGUID();
        _strands.clear();
        for (auto const& [a, b] : lines)
        {
            MechanicRef ref = Mechanic::Line(me, BossMechanics::Anchor(a), BossMechanics::Anchor(b), kStrandsWidth,
                Ms(kStrandsWarnMs));
            ref.Damage(kStrandsPct(heroic)).TankDamage(kStrandsPct(heroic))
                .Weakened().Spell(SPELL_HE_STRANDS).Rider(SPELL_HE_STRANDS_ROOT)
                .Tag(TAG_HE_STRANDS);
            Position const pa = a;
            Position const pb = b;
            JudgedThen(ref, me, "web-strands", [self, pa, pb](Map* map, ResolveResult const&)
            {
                Creature* boss = map->GetCreature(self);
                if (auto* ai = boss && boss->IsAlive() && boss->IsAIEnabled
                    ? dynamic_cast<boss_hedrum_rework*>(boss->AI()) : nullptr)
                    ai->StrandWeb(pa, pb);
            });
            _strands.push_back(ref.Handle());
            Track(ref.Handle());
        }
        Log("web-strands", Acore::StringFormat("lines={} life={}ms pct={:.0f}", lines.size(),
            kStrandsLifeMs(heroic), kStrandsPct(heroic)));
        return true;
    }

    // HE2: the farthest player(s) to his feet, then the burst 3 s after they land.
    bool ReelIn()
    {
        bool const heroic = Heroic();
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.farthest = true;
        std::vector<Player*> const targets = DungeonKit::PickPlayers(me, rule, kReelCount(heroic));
        if (targets.empty())
            return false;
        Vec2 const at = DungeonKit::PlaneOf(me);
        float flightMs = 0.f;
        std::string names;
        for (Player* player : targets)
        {
            float const bearing = DungeonKit::BearingTo(at, DungeonKit::PlaneOf(player));
            Vec2 const land = DungeonKit::Advance(at, bearing, kReelLandYd + me->GetCombatReach());
            float const dist = DungeonKit::Distance(DungeonKit::PlaneOf(player), land);
            flightMs = std::max(flightMs, dist / kReelSpeedXY * 1000.f);
            DungeonKit::JumpTo(player, Spot(me, land, me->GetPositionZ()), kReelSpeedXY, kReelSpeedZ,
                SPELL_HE_REEL_IN, me);
            names += Acore::StringFormat(" {}", player->GetName());
        }
        uint32 const warn = kBurstWarnMs + static_cast<uint32>(flightMs);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(me), kBurstRadius, Ms(warn));
        ref.Damage(kBurstPct(heroic)).TankDamage(kBurstPct(heroic))
            .Weakened().Spell(SPELL_HE_BANEFUL_BURST).Rider(SPELL_HE_BANEFUL_POISON)
            .Tag(TAG_HE_BANEFUL_BURST);
        ObjectGuid const self = me->GetGUID();
        JudgedThen(ref, me, "baneful-burst", [self](Map* map, ResolveResult const&)
        {
            if (Creature* boss = map->GetCreature(self))
                if (boss->IsAlive())
                    boss->CastSpell(boss, SPELL_HE_BANEFUL_LOOK, true);
        });
        Track(ref.Handle());
        Log("reel-in", Acore::StringFormat("players={}{} burst={}ms pct={:.0f}", targets.size(), names, warn,
            kBurstPct(heroic)));
        return true;
    }

    std::vector<MechanicHandle> _strands;
    uint64 _strandsAt = 0;
    uint64 _reelAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Risen beasts 300782-300787 (AN1): melee adds; heroic they keep their wave mechanic (ruling 20): the group signatures
// on Anub'shiah's clock (DoAction), Screech and Thunderclap on their own, Acid Burst as a held body (KT-D1). The hits,
// looks and numbers are D4's wave mechanics (RingOfLawLogic.h RW1-RW6), so a Risen beast draws and judges the same.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_risen_beast : public ScriptedAI
{
    enum class State : uint8
    {
        Fight,
        Burrowed,       // RW1
        Stinging,       // RW2
        Clapping,       // RW4
    };

    explicit npc_brd_risen_beast(Creature* creature)
        : ScriptedAI(creature), _type(RisenWaveType(creature->GetEntry()).value_or(0)), _body(BodySpec()) { }

    void Reset() override
    {
        Cleanup();
        if (IsBeetle())
            _body.Reset(me);
    }

    uint32 GetData(uint32 id) const override
    {
        return id == kRisenDataFree && Free() ? 1 : 0;
    }

    void DoAction(int32 action) override
    {
        if (action != kRisenActionSignature || !_heroic || !Free())
            return;
        switch (Type().signature)
        {
            case BrdRingOfLaw::Signature::Burrow:
                Burrow();
                break;
            case BrdRingOfLaw::Signature::TailSting:
                TailSting();
                break;
            case BrdRingOfLaw::Signature::VenomSpit:
                VenomSpit();
                break;
            default:
                break;
        }
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _heroic = IsHeroicMap(me);
        BrdRingOfLaw::WaveKind const& w = Type();
        bool const ownClock = _heroic && w.perBeast && w.signature != BrdRingOfLaw::Signature::AcidBurst;
        _sigAtMs = ownClock ? _clockMs + w.firstMs : 0;
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (IsBeetle() && _heroic)
            _body.Intercept(me, damage);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (IsBeetle() && _body.Fallen())
            return;
        if (BackOnTheFloor(me, this))
            return;
        Cleanup();
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        Cleanup();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        if ((spell->Id == BrdRingOfLaw::SPELL_RW_TAIL_STING_BAR && _state == State::Stinging)
            || (spell->Id == BrdRingOfLaw::SPELL_RW_THUNDERCLAP_BAR && _state == State::Clapping))
        {
            if (_pending)
                Mechanic::Cancel(me, _pending);
            _pending = MechanicHandle();
            _state = State::Fight;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (IsBeetle())
        {
            _body.Update(me, diff);
            if (_burstAtMs && _clockMs >= _burstAtMs)
            {
                _burstAtMs = 0;
                me->CastSpell(me, BrdRingOfLaw::SPELL_RW_ACID_BURST_LOOK, true);
            }
            if (_body.Fallen())
                return;
        }
        if (_state == State::Burrowed)
        {
            if (_clockMs >= _stateEndMs)
                Erupt();
            return;
        }
        if (!UpdateVictim())
            return;
        if (_state != State::Fight)
        {
            if (_clockMs >= _stateEndMs)
            {
                _state = State::Fight;
                _pending = MechanicHandle();
            }
            return;
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_sigAtMs && _clockMs >= _sigAtMs)
        {
            _sigAtMs = _clockMs + Type().everyMs;
            if (Type().signature == BrdRingOfLaw::Signature::Screech)
                me->CastSpell(me, BrdRingOfLaw::SPELL_RW_SCREECH, false);
            else if (Type().signature == BrdRingOfLaw::Signature::Thunderclap)
                Thunderclap();
            return;
        }
        DoMeleeAttackIfReady();
    }

private:
    BrdRingOfLaw::WaveKind const& Type() const { return BrdRingOfLaw::kWaveTypes[_type]; }
    bool IsBeetle() const { return Type().signature == BrdRingOfLaw::Signature::AcidBurst; }

    bool Free() const
    {
        return me->IsAlive() && _state == State::Fight && !me->HasUnitState(UNIT_STATE_CASTING)
            && !(IsBeetle() && _body.Fallen());
    }

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        LogCh("anubshiah", mechanic, Acore::StringFormat("risen={}/{} {}", me->GetEntry(), me->GetGUID().GetCounter(),
            detail));
    }

    // RW1 (D4's numbers): sink, then erupt under a random player's spot 2 s later.
    void Burrow()
    {
        Player* target = AnyPlayer(me);
        if (!target)
            return;
        _spot = Position(target->GetPositionX(), target->GetPositionY(), target->GetPositionZ(), me->GetOrientation());
        me->CastSpell(me, BrdRingOfLaw::SPELL_RW_BURROW_SINK, true);
        me->AttackStop();
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        me->SetReactState(REACT_PASSIVE);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetControlled(true, UNIT_STATE_ROOT);
        _state = State::Burrowed;
        _stateEndMs = _clockMs + BrdRingOfLaw::kBurrowWarnMs;
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(_spot), BrdRingOfLaw::kBurrowRadius,
            Ms(BrdRingOfLaw::kBurrowWarnMs));
        ref.Damage(BrdRingOfLaw::kBurrowPct(_heroic)).TankDamage(BrdRingOfLaw::kBurrowPct(_heroic))
            .Weakened().Spell(BrdRingOfLaw::SPELL_RW_BURROW)
            .Tag(BrdRingOfLaw::TAG_RW_BURROW);
        BrdRingOfLaw::Judged(ref, me, "risen-burrow");
        _pending = ref.Handle();
        Log("burrow", Acore::StringFormat("target={}", target->GetName()));
    }

    void Erupt()
    {
        _state = State::Fight;
        _pending = MechanicHandle();
        me->SetControlled(false, UNIT_STATE_ROOT);
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetReactState(REACT_AGGRESSIVE);
        float const z = GroundZ(me, _spot.GetPositionX(), _spot.GetPositionY(), _spot.GetPositionZ());
        me->NearTeleportTo(_spot.GetPositionX(), _spot.GetPositionY(), z, me->GetOrientation());
        me->CastSpell(me, BrdRingOfLaw::SPELL_RW_BURROW_ERUPT, true);
        if (Unit* target = AnyPlayer(me))
            AttackStart(target);
    }

    // RW2: a 60 degree / 15 yd cone toward a random player within 15 yd, locked at the cast.
    void TailSting()
    {
        Player* target = AnyPlayer(me, BrdRingOfLaw::kTailStingRange);
        if (!target)
            return;
        float const facing = DungeonKit::BearingTo(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(target));
        me->SetFacingTo(facing);
        me->CastSpell(me, BrdRingOfLaw::SPELL_RW_TAIL_STING_BAR, false);
        _state = State::Stinging;
        _stateEndMs = _clockMs + BrdRingOfLaw::kTailStingWarnMs;
        Position const apex(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), facing);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(BossMechanics::Anchor(apex),
            BrdRingOfLaw::kTailStingAngleDeg, BrdRingOfLaw::kTailStingLength), Ms(BrdRingOfLaw::kTailStingWarnMs));
        ref.Damage(BrdRingOfLaw::kTailStingPct(_heroic)).TankDamage(BrdRingOfLaw::kTailStingPct(_heroic))
            .Weakened().Spell(BrdRingOfLaw::SPELL_RW_TAIL_STING)
            .Rider(BrdRingOfLaw::SPELL_RW_TAIL_STING_POISON).Tag(BrdRingOfLaw::TAG_RW_TAIL_STING);
        BrdRingOfLaw::Judged(ref, me, "risen-tail-sting");
        _pending = ref.Handle();
        Log("tail-sting", Acore::StringFormat("target={}", target->GetName()));
    }

    // RW5: a 4 yd pool at a random player's spot for 12 s (Grimstone owns it: it outlives the Risen).
    void VenomSpit()
    {
        Player* target = AnyPlayer(me);
        if (!target)
            return;
        RingFrame* frame = BrdRingOfLaw::FrameOf(me);
        Creature* owner = frame ? frame->Owner() : me;
        Position const spot = Spot(me, DungeonKit::PlaneOf(target), target->GetPositionZ());
        me->SetFacingToObject(target);
        MechanicRef ref = Mechanic::Circle(owner, BossMechanics::Anchor(spot), BrdRingOfLaw::kVenomSpitRadius,
            Ms(BrdRingOfLaw::kVenomSpitWarnMs));
        ref.Persistent(Ms(BrdRingOfLaw::kVenomSpitLifeMs), Ms(BrdRingOfLaw::kVenomSpitTickMs))
            .Damage(BrdRingOfLaw::kVenomSpitPct(_heroic)).TankDamage(BrdRingOfLaw::kVenomSpitPct(_heroic))
            .Spell(BrdRingOfLaw::SPELL_RW_VENOM_SPIT)
            .Tag(BrdRingOfLaw::TAG_RW_VENOM_SPIT);
        BrdRingOfLaw::JudgedPersistent(ref, me, "risen-venom-spit");
        if (ref.IsValid())
            if (Creature* pool = owner->SummonCreature(NPC_BRD_STALKER, spot, TEMPSUMMON_TIMED_DESPAWN,
                BrdRingOfLaw::kVenomSpitWarnMs + BrdRingOfLaw::kVenomSpitLifeMs))
                pool->CastSpell(pool, BrdRingOfLaw::SPELL_RW_VENOM_SPIT_POOL, true);
        Log("venom-spit", Acore::StringFormat("target={}", target->GetName()));
    }

    // RW4: the 2 s wind-up and a 10 yd ring at the Risen (the tank too).
    void Thunderclap()
    {
        me->CastSpell(me, BrdRingOfLaw::SPELL_RW_THUNDERCLAP_BAR, false);
        _state = State::Clapping;
        _stateEndMs = _clockMs + BrdRingOfLaw::kThunderclapWarnMs;
        Position const at(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), 0.f);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(at), BrdRingOfLaw::kThunderclapRadius,
            Ms(BrdRingOfLaw::kThunderclapWarnMs));
        ref.Damage(BrdRingOfLaw::kThunderclapPct(_heroic)).TankDamage(BrdRingOfLaw::kThunderclapPct(_heroic))
            .Weakened().Spell(BrdRingOfLaw::SPELL_RW_THUNDERCLAP)
            .Rider(BrdRingOfLaw::SPELL_RW_THUNDERCLAP_SLOW).Tag(BrdRingOfLaw::TAG_RW_THUNDERCLAP);
        BrdRingOfLaw::Judged(ref, me, "risen-thunderclap");
        _pending = ref.Handle();
        Log("thunderclap");
    }

    // RW6 (heroic): the fallen beetle swells 2 s, bursts at its corpse, then dies.
    static DungeonKit::HeldBodySpec BodySpec()
    {
        DungeonKit::HeldBodySpec spec;
        spec.holds = 1;
        spec.holdLimit = Ms(BrdRingOfLaw::kAcidBodyHoldMs);
        spec.look = true;
        spec.root = true;
        spec.fallAura = BrdRingOfLaw::SPELL_RW_ACID_SWELL;
        spec.dungeon = kLogDungeon;
        spec.boss = "anubshiah";
        spec.onFall = [](Creature* body)
        {
            if (auto* ai = body && body->IsAIEnabled ? dynamic_cast<npc_brd_risen_beast*>(body->AI()) : nullptr)
                ai->AcidBurst();
        };
        return spec;
    }

    void AcidBurst()
    {
        Position const spot(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), 0.f);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(spot), BrdRingOfLaw::kAcidBurstRadius,
            Ms(BrdRingOfLaw::kAcidSwellMs));
        ref.Damage(BrdRingOfLaw::kAcidBurstPct(_heroic)).TankDamage(BrdRingOfLaw::kAcidBurstPct(_heroic))
            .Weakened().Spell(BrdRingOfLaw::SPELL_RW_ACID_BURST)
            .Tag(BrdRingOfLaw::TAG_RW_ACID_BURST);
        BrdRingOfLaw::Judged(ref, me, "risen-acid-burst");
        _burstAtMs = _clockMs + BrdRingOfLaw::kAcidSwellMs;
        Log("acid-burst");
    }

    void Cleanup()
    {
        if (_pending)
            Mechanic::Cancel(me, _pending);
        _pending = MechanicHandle();
        if (_state == State::Burrowed)
        {
            me->SetControlled(false, UNIT_STATE_ROOT);
            me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        }
        me->SetReactState(REACT_AGGRESSIVE);
        _state = State::Fight;
        _sigAtMs = 0;
        _burstAtMs = 0;
    }

    uint32 _type = 0;
    bool _heroic = false;
    uint64 _clockMs = 0;
    State _state = State::Fight;
    uint64 _stateEndMs = 0;
    uint64 _sigAtMs = 0;
    uint64 _burstAtMs = 0;
    Position _spot;
    MechanicHandle _pending;
    DungeonKit::HeldBody _body;
};

// ---------------------------------------------------------------------------------------------------------------------
// Risen Champion 300788 (AN1 heroic): the fallen challenger's look (Anub'shiah sets it at the summon), melee only, the
// tank's
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_risen_champion : public ScriptedAI
{
    explicit npc_brd_risen_champion(Creature* creature) : ScriptedAI(creature) { }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (BackOnTheFloor(me, this))
            return;
        ScriptedAI::EnterEvadeMode(why);
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }
};

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest brd champions ...`
// ---------------------------------------------------------------------------------------------------------------------
namespace
{
    RingChampionAI* FindChampion(ChatHandler* handler, uint32 entry)
    {
        Creature* boss = BrdTest::FindBoss(handler, entry);
        RingChampionAI* ai = ChampionAI(boss);
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    template <uint32 Entry, TestKind Kind>
    bool HandleFire(ChatHandler* handler)
    {
        RingChampionAI* ai = FindChampion(handler, Entry);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(Kind);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage("Fired.");
        return true;
    }

    template <uint32 Entry>
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, Entry, BOSS_RING_OF_LAW);
    }

    template <uint32 Entry>
    bool HandleState(ChatHandler* handler)
    {
        RingChampionAI* ai = FindChampion(handler, Entry);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest brd champions <champion> title`: CH1 now (the Title Holder aura and the legs token's loot mode).
    template <uint32 Entry>
    bool HandleTitle(ChatHandler* handler)
    {
        RingChampionAI* ai = FindChampion(handler, Entry);
        if (!ai)
            return false;
        ai->TestTitleHolder();
        handler->SendSysMessage("Title Holder applied.");
        return true;
    }

    // `.dbtest brd champions <champion> heroic [0|1]`: the heroic form on a normal map (and back), from the next pull.
    template <uint32 Entry>
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        RingChampionAI* ai = FindChampion(handler, Entry);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set.");
        return true;
    }

    // `.dbtest brd champions spawn <0-5>`: a champion at your feet, out of the Ring (no frame: no Favor, no Raise Dead,
    // no arena guard); pull it with `.gm off`.
    bool HandleSpawn(ChatHandler* handler, uint32 index)
    {
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* player = handler->GetPlayer();
        if (!player || index >= kRingChampions.size())
        {
            handler->SendErrorMessage("Usage: .dbtest brd champions spawn <0-5> (Gorosh, Grizzle, Eviscerator, "
                "Ok'thor, Anub'shiah, Hedrum).");
            return false;
        }
        Position const at = player->GetNearPosition(8.f, 0.f);
        if (!player->SummonCreature(kRingChampions[index], at, TEMPSUMMON_CORPSE_TIMED_DESPAWN, 60000))
        {
            handler->SendErrorMessage("The summon failed.");
            return false;
        }
        handler->SendSysMessage("Summoned 8 yd in front of you.");
        return true;
    }

    ChatCommandTable const& GoroshCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo<NPC_GOROSH>, SEC_GAMEMASTER, Console::No },
            { "state", HandleState<NPC_GOROSH>, SEC_GAMEMASTER, Console::No },
            { "title", HandleTitle<NPC_GOROSH>, SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic<NPC_GOROSH>, SEC_GAMEMASTER, Console::No },
            { "clear", HandleFire<NPC_GOROSH, TestKind::Clear>, SEC_GAMEMASTER, Console::No },
            { "dance", HandleFire<NPC_GOROSH, TestKind::First>, SEC_GAMEMASTER, Console::No },
            { "axe", HandleFire<NPC_GOROSH, TestKind::Second>, SEC_GAMEMASTER, Console::No },
            { "bloodlust", HandleFire<NPC_GOROSH, TestKind::Third>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& GrizzleCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo<NPC_GRIZZLE>, SEC_GAMEMASTER, Console::No },
            { "state", HandleState<NPC_GRIZZLE>, SEC_GAMEMASTER, Console::No },
            { "title", HandleTitle<NPC_GRIZZLE>, SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic<NPC_GRIZZLE>, SEC_GAMEMASTER, Console::No },
            { "clear", HandleFire<NPC_GRIZZLE, TestKind::Clear>, SEC_GAMEMASTER, Console::No },
            { "rush", HandleFire<NPC_GRIZZLE, TestKind::First>, SEC_GAMEMASTER, Console::No },
            { "stomp", HandleFire<NPC_GRIZZLE, TestKind::Second>, SEC_GAMEMASTER, Console::No },
            { "frenzy", HandleFire<NPC_GRIZZLE, TestKind::Third>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& EvisceratorCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo<NPC_EVISCERATOR>, SEC_GAMEMASTER, Console::No },
            { "state", HandleState<NPC_EVISCERATOR>, SEC_GAMEMASTER, Console::No },
            { "title", HandleTitle<NPC_EVISCERATOR>, SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic<NPC_EVISCERATOR>, SEC_GAMEMASTER, Console::No },
            { "clear", HandleFire<NPC_EVISCERATOR, TestKind::Clear>, SEC_GAMEMASTER, Console::No },
            { "eater", HandleFire<NPC_EVISCERATOR, TestKind::First>, SEC_GAMEMASTER, Console::No },
            { "wounds", HandleFire<NPC_EVISCERATOR, TestKind::Second>, SEC_GAMEMASTER, Console::No },
            { "volley", HandleFire<NPC_EVISCERATOR, TestKind::Third>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& OkthorCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo<NPC_OKTHOR>, SEC_GAMEMASTER, Console::No },
            { "state", HandleState<NPC_OKTHOR>, SEC_GAMEMASTER, Console::No },
            { "title", HandleTitle<NPC_OKTHOR>, SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic<NPC_OKTHOR>, SEC_GAMEMASTER, Console::No },
            { "clear", HandleFire<NPC_OKTHOR, TestKind::Clear>, SEC_GAMEMASTER, Console::No },
            { "rupture", HandleFire<NPC_OKTHOR, TestKind::First>, SEC_GAMEMASTER, Console::No },
            { "sheep", HandleFire<NPC_OKTHOR, TestKind::Second>, SEC_GAMEMASTER, Console::No },
            { "slow", HandleFire<NPC_OKTHOR, TestKind::Third>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& AnubshiahCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo<NPC_ANUBSHIAH>, SEC_GAMEMASTER, Console::No },
            { "state", HandleState<NPC_ANUBSHIAH>, SEC_GAMEMASTER, Console::No },
            { "title", HandleTitle<NPC_ANUBSHIAH>, SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic<NPC_ANUBSHIAH>, SEC_GAMEMASTER, Console::No },
            { "clear", HandleFire<NPC_ANUBSHIAH, TestKind::Clear>, SEC_GAMEMASTER, Console::No },
            { "raise", HandleFire<NPC_ANUBSHIAH, TestKind::First>, SEC_GAMEMASTER, Console::No },
            { "web", HandleFire<NPC_ANUBSHIAH, TestKind::Second>, SEC_GAMEMASTER, Console::No },
            { "curses", HandleFire<NPC_ANUBSHIAH, TestKind::Third>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& HedrumCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo<NPC_HEDRUM>, SEC_GAMEMASTER, Console::No },
            { "state", HandleState<NPC_HEDRUM>, SEC_GAMEMASTER, Console::No },
            { "title", HandleTitle<NPC_HEDRUM>, SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic<NPC_HEDRUM>, SEC_GAMEMASTER, Console::No },
            { "clear", HandleFire<NPC_HEDRUM, TestKind::Clear>, SEC_GAMEMASTER, Console::No },
            { "strands", HandleFire<NPC_HEDRUM, TestKind::First>, SEC_GAMEMASTER, Console::No },
            { "reel", HandleFire<NPC_HEDRUM, TestKind::Second>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    // `.dbtest brd champions <gorosh|grizzle|eviscerator|okthor|anubshiah|hedrum> <info|state|title|heroic|clear|
    // mechanic>` and `.dbtest brd champions spawn <0-5>`.
    ChatCommandTable const& BossRingChampionsTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "gorosh", GoroshCommands() },
            { "grizzle", GrizzleCommands() },
            { "eviscerator", EvisceratorCommands() },
            { "okthor", OkthorCommands() },
            { "anubshiah", AnubshiahCommands() },
            { "hedrum", HedrumCommands() },
            { "spawn", HandleSpawn, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_ring_champions_rework()
{
    if (BrdRingChampions::kBound)
        RegisterDungeonReworkCreatureAI(boss_gorosh_the_dervish_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (BrdRingChampions::kBound)
        RegisterDungeonReworkCreatureAI(boss_grizzle_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (BrdRingChampions::kBound)
        RegisterDungeonReworkCreatureAI(boss_eviscerator_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (BrdRingChampions::kBound)
        RegisterDungeonReworkCreatureAI(boss_okthor_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (BrdRingChampions::kBound)
        RegisterDungeonReworkCreatureAI(boss_anubshiah_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (BrdRingChampions::kBound)
        RegisterDungeonReworkCreatureAI(boss_hedrum_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (BrdRingChampions::kBound)
        RegisterDungeonReworkCreatureAI(npc_brd_risen_beast, BlackrockDepthsRework::kInstanceScriptName);
    if (BrdRingChampions::kBound)
        RegisterDungeonReworkCreatureAI(npc_brd_risen_champion, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("champions", BossRingChampionsTestCommands());
}
