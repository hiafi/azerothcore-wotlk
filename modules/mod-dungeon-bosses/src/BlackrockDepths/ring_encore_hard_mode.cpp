/*
 * mod-dungeon-bosses, Blackrock Depths D6: the Ring of Law's hard mode, the Encore (heroic only). Theldren's arena
 * team, "the reigning arena team, who fight like players" (rulings 19, 21, 28-30, 91): npc_brd_encore_theldren 16059,
 * npc_brd_encore_korv 16053, npc_brd_encore_lefty 16049, npc_brd_encore_volida 16058, npc_brd_encore_malgen 16052,
 * Korv's totems npc_brd_encore_totem 300789-300791 and the banner go_brd_encore_banner 301280. Build spec S1 "Hard
 * mode: the Encore", "Theldren and his team" and the Ring's Build spec rows EN1-EN16
 * (docs/dungeons/blackrock-depths-1-detention-block.md), handoff sections 3.5 (row D6), 3.6, 3.7 (D6), 3.8, 3.10,
 * section 7 #15 / #16. Replaces the five members' stock SmartAI (dropped by rev_ring_encore_blackrock_depths.sql) and
 * the stock banner path (item 21986 / spell 27517 / GO 181058: Grimstone keys on the saved flags, never on the
 * object). Pure rules: RingEncoreLogic.h.
 *
 * Grimstone (npc_grimstone_rework.cpp, D4) runs it through RingOfLawFight.h's EncoreScript, one per attempt:
 *   EN1  the banner      at Favor 10 on heroic the crowd throws it in (D4: emote 10, DATA_BANNER_THROWN, saved); this
 *                        file places it (GO 301280, a goober: the stock 181058 is GENERIC, type 5, and cannot be
 *                        clicked) and puts it back at every attempt start while it is thrown and not burned. A
 *                        player's click burns it: DATA_BANNER_BURNED (saved), Grimstone line 11, the banner burns and
 *                        is gone. The flags survive a wipe (section 7 #15).
 *   the leap             the title holder dies with the banner burned on heroic: Grimstone's 15 s beat and line 12,
 *                        then Start(): the five appear on the gallery over the east gate (corpse-timed summons:
 *                        their corpses keep their loot, KT-D1) and leap down to the floor; Theldren yells his stock
 *                        group 0 and carries the hard mode loot bit (rule 1: at his summon; S0 section 5 item 6).
 *   the end              every member is a held body (KT-D1 HeldBody: one fall each, Korv none) until Korv brings it
 *                        back (EN5) or nobody can: once every member is down, or Korv is dead with bodies lying, the
 *                        bodies are finished (Theldren last). All five dead: RingFrame::EncoreWon (D4: the stock Arena
 *                        Spoils chest, credit 16166 for quest 9015, the Ring's credit; the instance records slot 20).
 *   the wipe             Grimstone's watch: Stop(false) removes every aura of the Encore, he despawns the team, the
 *                        totems and the traps; the banner flags stay, so the next attempt plays the Encore again.
 *
 *   EN2  Executioner's Charge   12 s: a 1.5 s mark on the lowest-health player (the tank too), the charge: 25% and
 *                               -50% healing 6 s, Execute 40% below 30%; a 3 s hold on the charged player that a
 *                               taunt ends (ruling 91)
 *   EN3  Intimidating Roar      18 s (12 s below 30%): 2.5 s, 8 yd round him, the tank too: 35%, fear 2 s, Weakened;
 *                               Champion's Pride below 30% (+25% attack speed). Mortal Strike, Battle Shout, Hamstring
 *                               stock
 *   EN4  Chain Heal             8 s: a 2 s kickable cast, three teammates for 12% (interrupt expected)
 *   EN5  Ancestral Spirit       a body: a 5 s kickable cast (top kick), back at 50%, once per teammate
 *   EN6  totems                 Healing Stream 25 s (2% a second within 20 yd, until killed), Searing 20 s (3% every
 *                               2 s within 20 yd, 20 s), Earthbind 25 s (-50% within 10 yd, 20 s); one hit each
 *   EN7  Earth Shield           30 s on Theldren: Magic, 6 charges, 2% a hit
 *   EN8  Shadowstep             15 s: behind the healer, a 2 s Kidney Shot, the healer his top threat (not a fixate)
 *   EN9  Vicious Wound          each Sinister Strike: a stack (cap 5), 1% a second a stack, no dispel, ends above 90%
 *   EN10 Evasion                at 50% and 25%, 8 s
 *   EN11 Blizzard               12 s: 8 yd at a random player's spot, 2 s, then 6 s of 4% a second and a slow
 *   EN12 Frost Nova             2+ players within 10 yd: a 1.5 s kickable cast, 10 yd: 20%, root 2 s, Weakened; Blink
 *   EN13 Ice Barrier            30 s: 10% of her health, Magic
 *   EN14 Piercing Shot          15 s: a 3 s kickable cast, a 3 yd line through a random player to the wall: 40%
 *   EN15 Snap Trap              3 s with a player in melee: a 3 yd trap at his feet (60 s, cap 3), a 15 yd Disengage:
 *                               20%, freeze 2 s, Weakened
 *   EN16 Multi-Shot             10 s: a 2 s 30 yd cone toward a random player: 25%, Weakened
 *
 * The members never call Mechanic::Describe (the Ring keeps one descriptor, on Grimstone): their kicks, purges,
 * dispels and kill order go to RingFrame::SetUnitDescriptor. Every dodgeable registry hit feeds Crowd Favor
 * (BrdRingOfLaw::Judged / JudgedPersistent; a sprung trap through FavorHit). Every firing logs one INFO line
 * "brd <member> <mechanic> ..." (module.dungeonbosses); `.dbtest brd encore ...` fires them on demand.
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
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RingEncoreLogic.h"
#include "RingOfLawFight.h"
#include "RingOfLawLogic.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <list>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdEncore;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using BossMechanics::ResolveResult;
using BrdRingOfLaw::RingFrame;
using DungeonKit::BodyState;
using DungeonKit::IsHeroicMap;

namespace
{
    uint32 constexpr POINT_LEAP = 0x454E0001;
    uint32 constexpr POINT_CHARGE = 0x454E0002;
    uint32 constexpr POINT_BODY = 0x454E0003;
    // Snap Trap's object: Blackrock Spire's Net Trap (301253, GENERIC, display 7529 G_BearTrap: V-1's GODI_SNAP_TRAP),
    // reused as is (D5 reuses BRS's Stuck Axe 301250 the same way).
    uint32 constexpr GO_SNAP_TRAP = 301253;
    float constexpr kGroundBandYd = 6.f;
    float constexpr kNoFrameRangeYd = 60.f;     // a member with no frame (`.dbtest brd encore spawn`): its fight range
    float constexpr kGravity = 19.291105f;      // Movement::gravity (JumpTo's arc)

    // Every player aura the Encore applies (rule 6: a member's death, fall or evade removes its own; Stop() all).
    std::array<uint32, 14> constexpr kEncorePlayerAuras{ {
        SPELL_TH_CHARGE_MARK, SPELL_TH_WOUNDED, SPELL_TH_ROAR_FEAR, SPELL_KO_EARTHBIND, SPELL_LE_KIDNEY_SHOT,
        SPELL_LE_VICIOUS_WOUND, SPELL_VL_BLIZZARD_SLOW, SPELL_VL_FROST_NOVA_ROOT, SPELL_MA_SNAP_TRAP_FREEZE,
        SPELL_STOCK_MORTAL_STRIKE, SPELL_STOCK_HAMSTRING, SPELL_STOCK_FROST_SHOCK, SPELL_STOCK_FROSTBOLT,
        SPELL_STOCK_CONE_OF_COLD,
    } };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogEn(char const* key, char const* mechanic, std::string const& detail = {})
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

    void RemoveEncoreAuras(InstanceScript* instance)
    {
        if (!instance)
            return;
        for (uint32 spell : kEncorePlayerAuras)
            instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    // Every player the member fights: the frame's floor players, else (no frame: a test spawn) every live player in
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

    // A random player the member fights within `range` (the tank too, ruling 88).
    Player* AnyPlayer(Creature* me, float range = 100.f)
    {
        std::vector<Player*> players;
        for (Player* p : FightPlayers(me))
            if (me->GetExactDist2d(p) <= range)
                players.push_back(p);
        return players.empty() ? nullptr : players[urand(0, uint32(players.size() - 1))];
    }

    Player* NearestPlayer(Creature* me)
    {
        Player* best = nullptr;
        for (Player* p : FightPlayers(me))
            if (!best || me->GetExactDist2d(p) < me->GetExactDist2d(best))
                best = p;
        return best;
    }

    // The arena guard of a member: D4's floor polygon, no grips, never a chase off it, no leash (the Ring's wipe watch
    // ends an attempt; D5's ChampionGuard).
    DungeonKit::ArenaGuardOptions MemberGuard(char const* key)
    {
        DungeonKit::ArenaGuardOptions o = LeashOptions(key);
        o.evadeWhenBossOff = false;
        o.evadeNoTargetInsideMs = 0;
        return o;
    }

    DungeonKit::HeldBodySpec BodySpec(Member m)
    {
        DungeonKit::HeldBodySpec spec;
        spec.holds = HoldsOf(m);
        spec.revivePct = kRevivePct;
        spec.dungeon = kLogDungeon;
        spec.boss = MemberKey(m);
        return spec;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The common member: the leap, the pull, the held body, the frame, the descriptor, the cleanup, the arena guard
// ---------------------------------------------------------------------------------------------------------------------
class EncoreMemberAI : public ScriptedAI
{
public:
    EncoreMemberAI(Creature* creature, Member which)
        : ScriptedAI(creature), _member(which), _key(MemberKey(which)), _summons(creature),
        _arena(BrdRingOfLaw::RingFloorArena(), MemberGuard(MemberKey(which))), _body(BodySpec(which)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        Cleanup();
        _arena.Reset();
        _body.Reset(me);
        _engaged = false;
        _fighting = false;
        OnReset();
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        if (_engaged)
            return;
        _engaged = true;
        RingFrame* frame = BrdRingOfLaw::FrameOf(me);
        _framed = frame != nullptr;
        OnBossPull(me, _key, true);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RING_OF_LAW;
        Mechanic::BeginEncounter(me, options);
        if (_framed)
            _arena.Engage(me);
        if (frame)
            frame->SetUnitDescriptor(me->GetGUID(), DescriptorFill());
        if (_phase == Phase::Fighting)
            BeginFight();
        Log("engage", Acore::StringFormat("framed={} health={} leaping={}", _framed ? 1 : 0, me->GetMaxHealth(),
            _phase == Phase::Leaping ? 1 : 0));
    }

    void AttackStart(Unit* who) override
    {
        if (!who || _phase == Phase::Leaping || _body.Fallen())
            return;
        if (Range() > 0.f)
            AttackStartCaster(who, Range());
        else
            ScriptedAI::AttackStart(who);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == EFFECT_MOTION_TYPE && id == POINT_LEAP && _phase == Phase::Leaping)
        {
            Land("landed");
            return;
        }
        OnMovementInform(type, id);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (!damage)
            return;
        OnDamageTaken(attacker, damage);
        bool const wasFallen = _body.Fallen();
        _body.Intercept(me, damage);
        if (!wasFallen && _body.Fallen())
            Fell();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_body.Fallen() || _phase == Phase::Leaping)
            return;     // a body never evades; a leap lands first
        if (BackOnTheFloor())
            return;
        Log("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        ClearDescriptor();
        _engaged = false;
        _fighting = false;
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        Cleanup();
        ClearDescriptor();
        _summons.DespawnAll();
        OnDeath();
        Log("death", Acore::StringFormat("lootmode={} revives={}", me->GetLootMode(), _body.Revives()));
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
        RunLater();
        _body.Update(me, diff);
        if (_body.Fallen() || !me->IsAlive())
            return;
        if (_phase == Phase::Leaping)
        {
            if (!_landBy)
                Land("no leap");    // not the Encore's (a GM's summon): on its spot at once
            else if (_clockMs >= _landBy)
            {
                me->GetMotionMaster()->Clear();
                me->NearTeleportTo(_landing.GetPositionX(), _landing.GetPositionY(), _landing.GetPositionZ(),
                    _landing.GetOrientation());
                Land("timeout");
            }
            return;
        }
        UpdateAlways(diff);
        if (HoldsVictim())
        {
            if (_fighting)
                UpdateFight();
            return;
        }
        if (!UpdateVictim())
            return;
        if (_framed && !_arena.Update(me, diff))
            return;
        if (!_fighting)
            return;
        UpdateFight();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Encore's calls (EncoreRun) and the test commands
    // ----------------------------------------------------------------------------------------------------------------

    // From the gallery to `landing` (the Encore's Start): passive in the air, the fight starts on the floor.
    void Leap(Position const& landing)
    {
        _phase = Phase::Leaping;
        _landing = landing;
        _landBy = _clockMs + kLeapTimeoutMs;
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->GetMotionMaster()->Clear();
        float const dist = me->GetExactDist2d(landing.GetPositionX(), landing.GetPositionY());
        float const speedZ = std::max(8.f, dist / kLeapSpeedXY * 0.5f * kGravity);
        me->GetMotionMaster()->MoveJump(landing.GetPositionX(), landing.GetPositionY(), landing.GetPositionZ(),
            kLeapSpeedXY, speedZ, POINT_LEAP);
        Log("leap", Acore::StringFormat("to=({:.1f}, {:.1f}, {:.1f}) dist={:.1f}", landing.GetPositionX(),
            landing.GetPositionY(), landing.GetPositionZ(), dist));
    }

    // On the floor: the fight starts (the landing, a jump's timeout, a resummon, a test spawn).
    void Land(char const* why)
    {
        _phase = Phase::Fighting;
        me->SetReactState(REACT_AGGRESSIVE);
        me->SetHomePosition(me->GetPosition());
        BackOnTheFloor();
        BeginFight();
        Log("land", Acore::StringFormat("why={}", why));
    }

    // EN5 landed on this body.
    bool Revive()
    {
        if (!_body.Revive(me, kRevivePct))
            return false;
        me->CastSpell(me, SPELL_KO_SPIRIT_LOOK, true);
        BackOnTheFloor();
        BeginFight();
        return true;
    }

    // The real death of a body (the Encore's end).
    bool Finish(Unit* killer)
    {
        return _body.Finish(me, killer);
    }

    // `.dbtest brd encore fall <member>`: the next lethal hit, now.
    bool ForceFall()
    {
        uint32 damage = me->GetHealth();
        bool const wasFallen = _body.Fallen();
        if (!_body.Intercept(me, damage) || wasFallen)
            return false;
        me->SetHealth(1);
        Fell();
        return true;
    }

    bool Fallen() const { return _body.Fallen(); }
    bool Revived() const { return _body.Revives() > 0; }
    BodyState State() const { return me->IsAlive() ? _body.State() : BodyState::Dead; }
    Member Which() const { return _member; }

    // `.dbtest brd encore <member> <mechanic>`: forced firings (the member must be fighting). "" on success.
    std::string TestFire(uint8 which)
    {
        if (!_fighting || !me->IsEngaged() || _body.Fallen())
            return "The member is not fighting (pull it first: `.gm off`).";
        if (me->HasUnitState(UNIT_STATE_CASTING) || !Free())
            return "The member is busy (a cast, a charge, a move): try again in a moment.";
        return Fire(which);
    }

    std::string TestState() const
    {
        return Acore::StringFormat("{} phase={} framed={} fighting={} body={} revives={} lootmode={} health={:.0f}% | "
            "{}", _key, _phase == Phase::Leaping ? "leaping" : "fighting", _framed ? 1 : 0, _fighting ? 1 : 0,
            uint32(_body.State()), _body.Revives(), me->GetLootMode(), me->GetHealthPct(), State2());
    }

protected:
    enum class Phase : uint8
    {
        Fighting,
        Leaping,
    };

    // Per member: its clocks on the pull, its firings, its state.
    virtual void OnReset() { }
    virtual void StartFight() = 0;
    virtual void UpdateFight() = 0;
    virtual void UpdateAlways(uint32 /*diff*/) { }
    virtual bool HoldsVictim() const { return false; }
    virtual bool Free() const { return true; }
    virtual std::string Fire(uint8 which) = 0;
    virtual std::string State2() const { return {}; }
    virtual void ExtraCleanup() { }
    virtual void OnDamageTaken(Unit* /*attacker*/, uint32& /*damage*/) { }
    virtual void OnMovementInform(uint32 /*type*/, uint32 /*id*/) { }
    virtual void OnDeath() { }
    virtual float Range() const { return 0.f; }
    // The member's entries for the Ring's one descriptor (values only: nothing that dies with the unit).
    virtual std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const { return {}; }
    // The player auras this member applies (removed on its death, fall, evade).
    virtual std::vector<uint32> PlayerAuras() const { return {}; }

    uint64 Now() const { return _clockMs; }
    char const* Key() const { return _key; }
    bool Framed() const { return _framed; }

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        LogEn(_key, mechanic, detail);
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 64)
            _live.erase(_live.begin(), _live.begin() + 32);
    }

    // Runs `fn` `ms` from now on this AI's clock (dropped by the cleanup); capture nothing that dies with the unit.
    void Later(uint32 ms, std::function<void()> fn)
    {
        _later.emplace_back(_clockMs + ms, std::move(fn));
    }

    void Melee()
    {
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // Back into the fight after a charge, a blink, a jump.
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
            AttackStart(target);
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

    SummonList& Summons() { return _summons; }

private:
    // The players on the floor at 0 threat, an attack on the top one (or a random one): the members never walk off
    // while the Ring runs (D5's BackOnTheFloor).
    bool BackOnTheFloor()
    {
        std::vector<Player*> const players = FightPlayers(me);
        if (players.empty())
            return false;
        for (Player* player : players)
            me->AddThreat(player, 0.f);
        Unit* target = me->GetThreatMgr().GetCurrentVictim();
        if (!target || !target->IsAlive())
            target = players[urand(0, uint32(players.size() - 1))];
        AttackStart(target);
        return me->IsEngaged();
    }

    void BeginFight()
    {
        _fighting = true;
        StartFight();
    }

    // The lethal hit was held: a body (KT-D1). Every zone and aura of this member goes; Korv may bring it back.
    void Fell()
    {
        Cleanup();
        Log("fall", Acore::StringFormat("revives={} korv-can={}", _body.Revives(), _member == Member::Korv ? 0 : 1));
    }

    void ClearDescriptor()
    {
        if (RingFrame* frame = BrdRingOfLaw::FrameOf(me))
            frame->ClearUnitDescriptor(me->GetGUID());
    }

    void RunLater()
    {
        if (_later.empty())
            return;
        std::vector<std::function<void()>> due;
        for (auto it = _later.begin(); it != _later.end();)
        {
            if (it->first <= _clockMs)
            {
                due.push_back(std::move(it->second));
                it = _later.erase(it);
            }
            else
                ++it;
        }
        for (auto& fn : due)
            if (fn)
                fn();
    }

    // Rule 6: every zone, aura and look of the member goes.
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _later.clear();
        ExtraCleanup();
        if (InstanceScript* instance = me->GetInstanceScript())
            for (uint32 spell : PlayerAuras())
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        if (!_body.Fallen())
            me->SetReactState(REACT_AGGRESSIVE);
    }

    Member _member;
    char const* _key;
    SummonList _summons;
    DungeonKit::ArenaGuard _arena;
    DungeonKit::HeldBody _body;
    std::vector<MechanicHandle> _live;
    std::vector<std::pair<uint64, std::function<void()>>> _later;
    // A member starts in the air (R-1-RING MN-2): Grimstone's JustSummoned engages it inside SummonCreature, before
    // the Encore's Leap(); the fight (BeginFight, the chase) waits for Land(). Land()/Leap() run in the same call.
    Phase _phase = Phase::Leaping;
    Position _landing;
    uint64 _landBy = 0;
    uint64 _clockMs = 0;
    bool _engaged = false;
    bool _fighting = false;
    bool _framed = false;
};

namespace
{
    EncoreMemberAI* MemberAI(Creature* creature)
    {
        return creature && creature->IsAIEnabled ? dynamic_cast<EncoreMemberAI*>(creature->AI()) : nullptr;
    }

    bool IsBody(Creature* creature)
    {
        EncoreMemberAI* ai = MemberAI(creature);
        return ai && ai->Fallen();
    }

    // The live team members within `range` of `from` (the Encore's own, or a test spawn's).
    std::vector<Creature*> TeamAround(WorldObject const* from, float range)
    {
        std::vector<Creature*> out;
        for (uint32 entry : kTeamEntries)
        {
            std::list<Creature*> found;
            from->GetCreatureListWithEntryInGrid(found, entry, range);
            for (Creature* c : found)
                if (c->IsAlive() && MemberAI(c))
                    out.push_back(c);
        }
        return out;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Theldren 16059: EN2 Executioner's Charge, EN3 Intimidating Roar, Champion's Pride; Mortal Strike, Battle Shout,
// Hamstring kept
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_encore_theldren : public EncoreMemberAI
{
    explicit npc_brd_encore_theldren(Creature* creature) : EncoreMemberAI(creature, Member::Theldren) { }

    enum class Charge : uint8
    {
        None,
        Warn,       // the 1.5 s bar and mark
        Run,        // on his way
        Stick,      // the hold on the charged player (a taunt ends it)
    };

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        if (spell->Id == SPELL_TH_ROAR_BAR && _roar)
        {
            Mechanic::Cancel(me, _roar);
            _roar = MechanicHandle();
            Log("roar-stopped");
        }
        else if (spell->Id == SPELL_TH_CHARGE_BAR && _charge == Charge::Warn)
        {
            EndCharge("stopped");      // rule 13
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_TH_ROAR_BAR)
            _roar = MechanicHandle();      // landed: the registry resolves it
    }

protected:
    void OnReset() override
    {
        _charge = Charge::None;
        _pride = false;
    }

    void StartFight() override
    {
        _charge = Charge::None;
        _chargeAt = Now() + FirstOf(kChargeEveryMs);
        _roarAt = Now() + FirstOf(kRoarEveryMs);
        _msAt = Now() + urand(kMortalStrikeFirstMinMs, kMortalStrikeFirstMaxMs);
        _hamAt = Now() + urand(kHamstringFirstMinMs, kHamstringFirstMaxMs);
        if (!me->HasAura(SPELL_STOCK_BATTLE_SHOUT))
            me->CastSpell(me, SPELL_STOCK_BATTLE_SHOUT, true);
    }

    // EN7: each hit he takes with Earth Shield on heals him 2% and spends a charge.
    void OnDamageTaken(Unit* /*attacker*/, uint32& damage) override
    {
        Aura* shield = me->GetAura(SPELL_KO_EARTH_SHIELD);
        if (!shield || Fallen() || damage >= me->GetHealth())
            return;
        int32 const heal = int32(me->CountPctFromMaxHealth(kEarthShieldPct));
        me->CastCustomSpell(SPELL_KO_EARTH_SHIELD_HEAL, SPELLVALUE_BASE_POINT0, heal, me, true);
        shield->DropCharge();
    }

    void OnMovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_CHARGE && _charge == Charge::Run)
            ChargeLands("arrived");
    }

    void OnDeath() override
    {
        Talk(SAY_TH_DEATH);
    }

    bool Free() const override
    {
        return _charge == Charge::None || _charge == Charge::Stick;
    }

    bool HoldsVictim() const override
    {
        return _charge == Charge::Warn || _charge == Charge::Run || _charge == Charge::Stick;
    }

    void UpdateAlways(uint32 /*diff*/) override
    {
        if (!_pride && PrideActive(me->GetHealthPct()))
        {
            _pride = true;
            me->CastSpell(me, SPELL_TH_CHAMPIONS_PRIDE, true);
            _roarAt = std::min<uint64>(_roarAt, Now() + kRoarPrideEveryMs);
            Log("champions-pride", Acore::StringFormat("health={:.0f}%", me->GetHealthPct()));
        }
        switch (_charge)
        {
            case Charge::Warn:
                if (Now() >= _chargeStepAt)
                    StartCharge();
                break;
            case Charge::Run:
                if (Now() >= _chargeStepAt)
                    ChargeLands("timeout");
                break;
            case Charge::Stick:
            {
                // A taunt (or the charged player gone) ends the hold at once (ruling 91).
                Player* target = ObjectAccessor::GetPlayer(*me, _chargeTarget);
                if (Now() >= _chargeStepAt || !target || !target->IsAlive()
                    || me->HasAuraType(SPELL_AURA_MOD_TAUNT))
                    EndCharge(me->HasAuraType(SPELL_AURA_MOD_TAUNT) ? "taunted" : "turned back");
                break;
            }
            default:
                break;
        }
    }

    void UpdateFight() override
    {
        if (_charge == Charge::Warn || _charge == Charge::Run)
            return;
        if (_charge == Charge::Stick)
        {
            Player* target = ObjectAccessor::GetPlayer(*me, _chargeTarget);
            if (target && me->GetVictim() != target)
                me->Attack(target, true);
            Melee();
            return;
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (Now() >= _chargeAt)
        {
            _chargeAt = Now() + kChargeEveryMs;
            if (ExecutionersCharge())
                return;
        }
        if (Now() >= _roarAt)
        {
            _roarAt = Now() + RoarEveryMs(_pride);
            IntimidatingRoar();
            return;
        }
        if (Now() >= _msAt)
        {
            _msAt = Now() + urand(kMortalStrikeMinMs, kMortalStrikeMaxMs);
            DoCastVictim(SPELL_STOCK_MORTAL_STRIKE);
            return;
        }
        if (Now() >= _hamAt)
        {
            _hamAt = Now() + urand(kHamstringMinMs, kHamstringMaxMs);
            DoCastVictim(SPELL_STOCK_HAMSTRING);
            return;
        }
        Melee();
    }

    std::string Fire(uint8 which) override
    {
        if (which == 0)
            return ExecutionersCharge() ? std::string() : std::string("No player to charge.");
        IntimidatingRoar();
        return {};
    }

    std::string State2() const override
    {
        return Acore::StringFormat("charge={} pride={} shield={} next charge={}ms roar={}ms", uint32(_charge),
            _pride ? 1 : 0, me->HasAura(SPELL_KO_EARTH_SHIELD) ? 1 : 0, _chargeAt > Now() ? _chargeAt - Now() : 0,
            _roarAt > Now() ? _roarAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        _charge = Charge::None;     // the base restores the react state (a body stays passive)
        _chargeTarget.Clear();
        _roar = MechanicHandle();
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        return [](BossMechanics::Descriptor& d)
        {
            d.purges.emplace_back(NPC_THELDREN, SPELL_KO_EARTH_SHIELD, 2);     // EN7: the purge list
        };
    }

    std::vector<uint32> PlayerAuras() const override
    {
        return { SPELL_TH_CHARGE_MARK, SPELL_TH_WOUNDED, SPELL_TH_ROAR_FEAR, SPELL_STOCK_MORTAL_STRIKE,
            SPELL_STOCK_HAMSTRING };
    }

private:
    // EN2: the lowest-health player (the tank too): the mark and the 1.5 s bar, then the charge.
    bool ExecutionersCharge()
    {
        std::vector<Player*> const players = FightPlayers(me);
        std::vector<Candidate> c;
        for (Player* p : players)
            c.push_back({ p->GetGUID().GetRawValue(), p->GetHealthPct(), me->GetExactDist2d(p) });
        std::optional<std::size_t> const pick = LowestHealth(c);
        if (!pick)
            return false;
        Player* target = players[*pick];
        Hold();
        me->SetFacingToObject(target);
        me->CastSpell(target, SPELL_TH_CHARGE_MARK, true);
        DungeonKit::CastBar(me, SPELL_TH_CHARGE_BAR);
        _chargeTarget = target->GetGUID();
        _charge = Charge::Warn;
        _chargeStepAt = Now() + kChargeWarnMs;
        Log("executioners-charge", Acore::StringFormat("target={} health={:.0f}%", target->GetName(),
            target->GetHealthPct()));
        return true;
    }

    void StartCharge()
    {
        Player* target = ObjectAccessor::GetPlayer(*me, _chargeTarget);
        if (!target || !target->IsAlive())
        {
            EndCharge("target gone");
            return;
        }
        _charge = Charge::Run;
        _chargeStepAt = Now() + kChargeTimeoutMs;
        me->GetMotionMaster()->MoveCharge(target->GetPositionX(), target->GetPositionY(), target->GetPositionZ(),
            kChargeSpeed, POINT_CHARGE);
    }

    // The landing: 25% and -50% healing; Execute below 30%. Then the hold on the charged player.
    void ChargeLands(char const* why)
    {
        Player* target = ObjectAccessor::GetPlayer(*me, _chargeTarget);
        if (!target || !target->IsAlive() || me->GetExactDist2d(target) > 8.f)
        {
            Log("charge-missed", Acore::StringFormat("why={}", why));
            EndCharge("missed");
            return;
        }
        me->CastCustomSpell(SPELL_TH_CHARGE_HIT, SPELLVALUE_BASE_POINT0,
            int32(DungeonKit::RefFlatOn(me, target, kChargePct)), target, true);
        me->CastSpell(target, SPELL_TH_WOUNDED, true);
        bool const execute = target->IsAlive() && ExecuteFollows(target->GetHealthPct());
        if (execute)
            me->CastCustomSpell(SPELL_TH_EXECUTE, SPELLVALUE_BASE_POINT0,
                int32(DungeonKit::RefFlatOn(me, target, kExecutePct)), target, true);
        Log("charge-hit", Acore::StringFormat("target={} execute={} why={}", target->GetName(), execute ? 1 : 0,
            why));
        _charge = Charge::Stick;
        _chargeStepAt = Now() + kChargeStickMs;
        me->SetReactState(REACT_AGGRESSIVE);
        if (target->IsAlive())
        {
            me->GetMotionMaster()->Clear();
            me->Attack(target, true);
            me->GetMotionMaster()->MoveChase(target);
        }
    }

    void EndCharge(char const* why)
    {
        bool const was = _charge != Charge::None;
        _charge = Charge::None;
        _chargeTarget.Clear();
        if (was)
            Log("charge-end", Acore::StringFormat("why={}", why));
        BackToFight();
    }

    // EN3: the 2.5 s bar and an 8 yd ring on him, the tank too.
    void IntimidatingRoar()
    {
        DungeonKit::CastBar(me, SPELL_TH_ROAR_BAR);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(me), kRoarRadius, Ms(kRoarWarnMs));
        ref.Damage(kRoarPct).TankDamage(kRoarPct)
            .Weakened().Spell(SPELL_TH_ROAR).Rider(SPELL_TH_ROAR_FEAR).Tag(TAG_TH_ROAR);
        BrdRingOfLaw::Judged(ref, me, "intimidating-roar");
        _roar = ref.Handle();
        Track(_roar);
        Log("intimidating-roar", Acore::StringFormat("pride={}", _pride ? 1 : 0));
    }

    Charge _charge = Charge::None;
    ObjectGuid _chargeTarget;
    uint64 _chargeStepAt = 0;
    MechanicHandle _roar;
    bool _pride = false;
    uint64 _chargeAt = 0;
    uint64 _roarAt = 0;
    uint64 _msAt = 0;
    uint64 _hamAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Korv 16053: EN4 Chain Heal, EN5 Ancestral Spirit, EN6 the totems, EN7 Earth Shield; Frost Shock and Purge kept
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_encore_korv : public EncoreMemberAI
{
    explicit npc_brd_encore_korv(Creature* creature) : EncoreMemberAI(creature, Member::Korv) { }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        if (spell->Id == SPELL_KO_CHAIN_HEAL)
            ChainHealLands();
        else if (spell->Id == SPELL_KO_ANCESTRAL_SPIRIT)
            SpiritLands();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        if (spell->Id == SPELL_KO_CHAIN_HEAL)
        {
            _chainPicks.clear();
            Log("chain-heal-stopped");
        }
        else if (spell->Id == SPELL_KO_ANCESTRAL_SPIRIT)
        {
            _spiritTarget.Clear();
            _spiritRetryAt = Now() + kSpiritRetryMs;
            Log("ancestral-spirit-stopped");
        }
    }

protected:
    float Range() const override { return kKorvRangeYd; }

    void StartFight() override
    {
        _chainAt = Now() + FirstOf(kChainHealEveryMs);
        _spiritRetryAt = 0;
        _toBody = false;
        for (std::size_t k = 0; k < kTotemKinds; ++k)
            _totemAt[k] = Now() + FirstOf(kTotemEveryMs[k]);
        _shieldAt = Now() + 1000;       // his first shield on the landing
        _shockAt = Now() + urand(kFrostShockFirstMinMs, kFrostShockFirstMaxMs);
        _purgeAt = Now() + kPurgeFirstMs;
        Mechanic::NoteNextCastIn(me, SPELL_KO_CHAIN_HEAL, Ms(FirstOf(kChainHealEveryMs)));
    }

    void OnMovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_BODY && _toBody)
        {
            _toBody = false;
            BackToFight();
        }
    }

    bool Free() const override { return !_toBody; }

    void UpdateAlways(uint32 /*diff*/) override
    {
        // A walk to a body that never arrives (a root, a stun, no path) gives up.
        if (_toBody && Now() >= _toBodyUntil)
        {
            _toBody = false;
            _spiritRetryAt = Now() + kSpiritRetryMs;
            BackToFight();
            Log("ancestral-spirit-walk-timeout");
        }
    }

    void UpdateFight() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING) || _toBody)
            return;
        // EN5 first: a body lies.
        if (Now() >= _spiritRetryAt && AncestralSpirit())
            return;
        if (Now() >= _chainAt)
        {
            if (ChainHeal())
            {
                _chainAt = Now() + kChainHealEveryMs;
                Mechanic::NoteNextCastIn(me, SPELL_KO_CHAIN_HEAL, Ms(kChainHealEveryMs));
                return;
            }
            _chainAt = Now() + kChainHealRetryMs;
        }
        for (std::size_t k = 0; k < kTotemKinds; ++k)
            if (Now() >= _totemAt[k])
            {
                _totemAt[k] = Now() + kTotemEveryMs[k];
                DropTotem(static_cast<TotemKind>(k));
            }
        if (Now() >= _shieldAt)
        {
            _shieldAt = Now() + kEarthShieldEveryMs;
            EarthShield();
        }
        if (Now() >= _shockAt)
        {
            _shockAt = Now() + urand(kFrostShockMinMs, kFrostShockMaxMs);
            DoCastVictim(SPELL_STOCK_FROST_SHOCK);
            return;
        }
        if (Now() >= _purgeAt)
        {
            _purgeAt = Now() + kPurgeEveryMs;
            if (Player* target = AnyPlayer(me, 30.f))
            {
                DoCast(target, SPELL_STOCK_PURGE);
                return;
            }
        }
        Melee();
    }

    std::string Fire(uint8 which) override
    {
        switch (which)
        {
            case 0:
                return ChainHeal() ? std::string() : std::string("Nobody hurt.");
            case 1:
                return AncestralSpirit() ? std::string() : std::string("No body to bring back.");
            case 2:
                for (std::size_t k = 0; k < kTotemKinds; ++k)
                    DropTotem(static_cast<TotemKind>(k));
                return {};
            default:
                return EarthShield() ? std::string() : std::string("No Theldren to shield.");
        }
    }

    std::string State2() const override
    {
        return Acore::StringFormat("totems={}/{}/{} next chain={}ms shield={}ms spirit-retry={}ms",
            _totems[0] ? 1 : 0, _totems[1] ? 1 : 0, _totems[2] ? 1 : 0, _chainAt > Now() ? _chainAt - Now() : 0,
            _shieldAt > Now() ? _shieldAt - Now() : 0, _spiritRetryAt > Now() ? _spiritRetryAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        _chainPicks.clear();
        _spiritTarget.Clear();
        _toBody = false;
        // His totems go with him (a dead or fallen shaman's totems would heal on; the kill order names them).
        for (ObjectGuid& guid : _totems)
        {
            if (Creature* totem = ObjectAccessor::GetCreature(*me, guid))
                totem->DespawnOrUnsummon();
            guid.Clear();
        }
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        return [](BossMechanics::Descriptor& d)
        {
            d.interrupts.emplace_back(NPC_KORV, SPELL_KO_ANCESTRAL_SPIRIT, 3);      // EN5: above all
            d.interrupts.emplace_back(NPC_KORV, SPELL_KO_CHAIN_HEAL, 2, Ms(kChainHealEveryMs));   // EN4: expected
            for (uint32 entry : kTotemEntries)
                d.targets.emplace_back(entry, 2);                                    // EN6: on sight
        };
    }

    std::vector<uint32> PlayerAuras() const override
    {
        return { SPELL_KO_EARTHBIND, SPELL_STOCK_FROST_SHOCK };
    }

private:
    std::vector<Mate> Mates(std::vector<Creature*>& units)
    {
        units = TeamAround(me, 100.f);
        std::vector<Mate> mates;
        for (Creature* c : units)
        {
            EncoreMemberAI* ai = MemberAI(c);
            mates.push_back({ c->GetGUID().GetRawValue(), c->GetHealthPct(), ai && ai->Fallen(),
                ai && ai->Revived(), me->GetExactDist2d(c) });
        }
        return mates;
    }

    // EN4: the 2 s kickable cast; the three lowest standing teammates are picked as it starts.
    bool ChainHeal()
    {
        std::vector<Creature*> units;
        std::vector<Mate> const mates = Mates(units);
        std::vector<std::size_t> const picks = ChainHealPicks(mates);
        if (picks.empty())
            return false;
        _chainPicks.clear();
        std::string names;
        for (std::size_t i : picks)
        {
            _chainPicks.push_back(units[i]->GetGUID());
            names += (names.empty() ? "" : ",") + units[i]->GetName();
        }
        me->CastSpell(me, SPELL_KO_CHAIN_HEAL, false);
        Log("chain-heal", Acore::StringFormat("targets={}", names));
        return true;
    }

    void ChainHealLands()
    {
        uint32 healed = 0;
        for (ObjectGuid const& guid : _chainPicks)
        {
            Creature* mate = ObjectAccessor::GetCreature(*me, guid);
            if (!mate || !mate->IsAlive() || IsBody(mate))
                continue;
            int32 const heal = int32(mate->CountPctFromMaxHealth(kChainHealPct));
            me->CastCustomSpell(SPELL_KO_CHAIN_HEAL_HIT, SPELLVALUE_BASE_POINT0, heal, mate, true);
            ++healed;
        }
        _chainPicks.clear();
        Log("chain-heal-landed", Acore::StringFormat("healed={}", healed));
    }

    // EN5: a body never brought back: in range, the 5 s kickable cast; else he walks to it first.
    bool AncestralSpirit()
    {
        std::vector<Creature*> units;
        std::vector<Mate> const mates = Mates(units);
        std::optional<std::size_t> const pick = SpiritPick(mates);
        if (!pick)
            return false;
        Creature* body = units[*pick];
        if (me->GetExactDist2d(body) > kSpiritRangeYd || !me->IsWithinLOSInMap(body))
        {
            _toBody = true;
            _toBodyUntil = Now() + kSpiritWalkMs;
            me->AttackStop();
            me->GetMotionMaster()->Clear();
            Position const near = body->GetNearPosition(5.f, body->GetAngle(me));
            me->GetMotionMaster()->MovePoint(POINT_BODY, near.GetPositionX(), near.GetPositionY(),
                near.GetPositionZ());
            Log("ancestral-spirit-walk", Acore::StringFormat("body={}", body->GetName()));
            return true;
        }
        _spiritTarget = body->GetGUID();
        me->SetFacingToObject(body);
        me->CastSpell(body, SPELL_KO_ANCESTRAL_SPIRIT, false);
        Log("ancestral-spirit", Acore::StringFormat("body={}", body->GetName()));
        return true;
    }

    void SpiritLands()
    {
        Creature* body = ObjectAccessor::GetCreature(*me, _spiritTarget);
        _spiritTarget.Clear();
        EncoreMemberAI* ai = MemberAI(body);
        bool const revived = ai && ai->Revive();
        Log("ancestral-spirit-landed", Acore::StringFormat("body={} revived={}", body ? body->GetName() : "-",
            revived ? 1 : 0));
    }

    // EN6: one of each kind at a time, at his feet.
    void DropTotem(TotemKind kind)
    {
        std::size_t const k = static_cast<std::size_t>(kind);
        if (Creature* old = ObjectAccessor::GetCreature(*me, _totems[k]))
            if (old->IsAlive())
                return;
        float const o = me->GetOrientation() + (float(k) - 1.f) * 1.2f;
        Position const at = Spot(me, DungeonKit::Advance(DungeonKit::PlaneOf(me), o, kTotemOffsetYd),
            me->GetPositionZ(), me->GetOrientation());
        uint32 const life = kTotemLifeMs[k];
        Creature* totem = me->SummonCreature(kTotemEntries[k], at.GetPositionX(), at.GetPositionY(),
            at.GetPositionZ(), at.GetOrientation(), life ? TEMPSUMMON_TIMED_OR_DEAD_DESPAWN : TEMPSUMMON_DEAD_DESPAWN,
            life);
        if (!totem)
        {
            Log("totem-refused", TotemName(kind));
            return;
        }
        _totems[k] = totem->GetGUID();
        if (RingFrame* frame = BrdRingOfLaw::FrameOf(me))
            frame->JoinRing(totem);
        Log("totem", Acore::StringFormat("kind={} life={}ms", TotemName(kind), life));
    }

    // EN7: on Theldren standing, renewed to 6 charges.
    bool EarthShield()
    {
        Creature* theldren = me->FindNearestCreature(NPC_THELDREN, 100.f);
        if (!theldren || IsBody(theldren))
            return false;
        me->CastSpell(theldren, SPELL_KO_EARTH_SHIELD, true);
        if (Aura* shield = theldren->GetAura(SPELL_KO_EARTH_SHIELD))
            shield->SetCharges(uint8(kEarthShieldCharges));
        Log("earth-shield", Acore::StringFormat("on={}", theldren->HasAura(SPELL_KO_EARTH_SHIELD) ? 1 : 0));
        return true;
    }

    std::vector<ObjectGuid> _chainPicks;
    ObjectGuid _spiritTarget;
    bool _toBody = false;
    uint64 _toBodyUntil = 0;
    std::array<ObjectGuid, kTotemKinds> _totems{};
    std::array<uint64, kTotemKinds> _totemAt{};
    uint64 _chainAt = 0;
    uint64 _spiritRetryAt = 0;
    uint64 _shieldAt = 0;
    uint64 _shockAt = 0;
    uint64 _purgeAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Lefty 16049: EN8 Shadowstep, EN9 Vicious Wound, EN10 Evasion; Sinister Strike and Eviscerate kept
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_encore_lefty : public EncoreMemberAI
{
    explicit npc_brd_encore_lefty(Creature* creature) : EncoreMemberAI(creature, Member::Lefty) { }

    // EN9: a Sinister Strike that lands is a stack.
    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (!spell || spell->Id != SPELL_STOCK_SINISTER_STRIKE || !target || !target->IsPlayer())
            return;
        uint32 const stacks = DungeonKit::AddStacks(target, SPELL_LE_VICIOUS_WOUND, 1, me, kWoundCap);
        _wounded.insert(target->GetGUID());
        Log("vicious-wound", Acore::StringFormat("target={} stacks={}", target->GetName(), stacks));
    }

protected:
    void OnReset() override
    {
        _evasions = 0;
    }

    void StartFight() override
    {
        _stepAt = Now() + FirstOf(kShadowstepEveryMs);
        _sinisterAt = Now() + urand(kSinisterStrikeMinMs, kSinisterStrikeMaxMs);
        _evisAt = Now() + urand(kEviscerateFirstMinMs, kEviscerateFirstMaxMs);
        _woundTickAt = Now() + kWoundTickMs;
        if (Player* healer = Healer())
            Dive(healer);
    }

    void UpdateAlways(uint32 /*diff*/) override
    {
        // EN10.
        if (uint32 const due = EvasionsDue(me->GetHealthPct(), _evasions))
        {
            _evasions += due;
            me->CastSpell(me, SPELL_LE_EVASION, true);
            Log("evasion", Acore::StringFormat("health={:.0f}% used={}", me->GetHealthPct(), _evasions));
        }
        // EN9 ticks.
        if (Now() >= _woundTickAt)
        {
            _woundTickAt = Now() + kWoundTickMs;
            WoundTicks();
        }
    }

    void UpdateFight() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (Now() >= _stepAt)
        {
            _stepAt = Now() + kShadowstepEveryMs;
            if (Shadowstep())
                return;
        }
        if (Now() >= _sinisterAt)
        {
            _sinisterAt = Now() + urand(kSinisterStrikeMinMs, kSinisterStrikeMaxMs);
            DoCastVictim(SPELL_STOCK_SINISTER_STRIKE);
            return;
        }
        if (Now() >= _evisAt)
        {
            _evisAt = Now() + urand(kEviscerateMinMs, kEviscerateMaxMs);
            DoCastVictim(SPELL_STOCK_EVISCERATE);
            return;
        }
        Melee();
    }

    std::string Fire(uint8 which) override
    {
        if (which == 0)
            return Shadowstep() ? std::string() : std::string("No player to step to.");
        me->CastSpell(me, SPELL_LE_EVASION, true);
        return {};
    }

    std::string State2() const override
    {
        return Acore::StringFormat("evasions={} wounded={} next step={}ms", _evasions, _wounded.size(),
            _stepAt > Now() ? _stepAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        _wounded.clear();
        me->RemoveAurasDueToSpell(SPELL_LE_EVASION);
    }

    std::vector<uint32> PlayerAuras() const override
    {
        return { SPELL_LE_VICIOUS_WOUND, SPELL_LE_KIDNEY_SHOT };
    }

private:
    // The group's healer (the registry's role provider), else a random player he is not on.
    Player* Healer()
    {
        std::vector<Player*> const players = FightPlayers(me);
        for (Player* p : players)
            if (BossMechanics::GetRoleProvider().Get(me, p) == BossMechanics::Role::Healer)
                return p;
        std::vector<Player*> others;
        for (Player* p : players)
            if (p != me->GetVictim())
                others.push_back(p);
        if (others.empty())
            return players.empty() ? nullptr : players.front();
        return others[urand(0, uint32(others.size() - 1))];
    }

    // The healer becomes his top threat (+10%): not a fixate, a taunt takes him off.
    void Dive(Player* healer)
    {
        ThreatManager& threat = me->GetThreatMgr();
        Unit* top = threat.GetCurrentVictim();
        float const topThreat = top ? threat.GetThreat(top) : 0.f;
        me->AddThreat(healer, 0.f);
        threat.MatchUnitThreatToHighestThreat(healer);
        threat.AddThreat(healer, std::max(100.f, topThreat * kDiveThreatPct / 100.f), nullptr, true, true);
        AttackStart(healer);
    }

    // EN8: behind the healer, the 2 s Kidney Shot, the healer his top threat.
    bool Shadowstep()
    {
        Player* healer = Healer();
        if (!healer)
            return false;
        Vec2 const behind = DungeonKit::Advance(DungeonKit::PlaneOf(healer),
            healer->GetOrientation() + DungeonKit::kPi, kShadowstepBehindYd);
        Position const to = Spot(me, behind, healer->GetPositionZ(), healer->GetOrientation());
        me->CastSpell(me, SPELL_LE_SHADOWSTEP_LOOK, true);
        me->NearTeleportTo(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), to.GetOrientation());
        me->CastSpell(healer, SPELL_LE_KIDNEY_SHOT, true);
        Dive(healer);
        Log("shadowstep", Acore::StringFormat("healer={}", healer->GetName()));
        return true;
    }

    // EN9: 1% a second a stack; healed above 90% it ends.
    void WoundTicks()
    {
        for (auto it = _wounded.begin(); it != _wounded.end();)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, *it);
            uint32 const stacks = player ? DungeonKit::Stacks(player, SPELL_LE_VICIOUS_WOUND, me->GetGUID()) : 0;
            if (!player || !player->IsAlive() || !stacks)
            {
                it = _wounded.erase(it);
                continue;
            }
            if (WoundEnds(player->GetHealthPct()))
            {
                player->RemoveAurasDueToSpell(SPELL_LE_VICIOUS_WOUND, me->GetGUID());
                Log("vicious-wound-healed", Acore::StringFormat("target={}", player->GetName()));
                it = _wounded.erase(it);
                continue;
            }
            me->CastCustomSpell(SPELL_LE_VICIOUS_WOUND_TICK, SPELLVALUE_BASE_POINT0,
                int32(DungeonKit::RefFlatOn(me, player, WoundTickPct(stacks))), player, true);
            ++it;
        }
    }

    std::unordered_set<ObjectGuid> _wounded;
    uint32 _evasions = 0;
    uint64 _stepAt = 0;
    uint64 _sinisterAt = 0;
    uint64 _evisAt = 0;
    uint64 _woundTickAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Volida 16058: EN11 Blizzard, EN12 Frost Nova and Blink, EN13 Ice Barrier; Frostbolt and Cone of Cold kept
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_encore_volida : public EncoreMemberAI
{
    explicit npc_brd_encore_volida(Creature* creature) : EncoreMemberAI(creature, Member::Volida) { }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_VL_FROST_NOVA_CAST && _nova)
        {
            Mechanic::Cancel(me, _nova);
            _nova = MechanicHandle();
            _novaReadyAt = Now() + kNovaRetryMs;
            Log("frost-nova-stopped");
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (!spell || spell->Id != SPELL_VL_FROST_NOVA_CAST)
            return;
        _nova = MechanicHandle();      // landed: the registry resolves it at her spot
        _novaReadyAt = Now() + kNovaEveryMs;
        Later(kBlinkAfterMs, [this]() { Blink(); });
    }

protected:
    float Range() const override { return kVolidaRangeYd; }

    void StartFight() override
    {
        _blizzardAt = Now() + FirstOf(kBlizzardEveryMs);
        _novaReadyAt = Now();
        _barrierAt = Now() + FirstOf(kIceBarrierEveryMs);
        _boltAt = Now() + kFrostboltFirstMs;
        _coneAt = Now() + urand(kConeFirstMinMs, kConeFirstMaxMs);
        Mechanic::NoteNextCastIn(me, SPELL_VL_FROST_NOVA_CAST, Ms(kNovaEveryMs));
    }

    void UpdateFight() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (Now() >= _novaReadyAt && NovaWanted(PlayersWithin(kNovaRadius)))
        {
            FrostNova();
            return;
        }
        if (Now() >= _blizzardAt)
        {
            _blizzardAt = Now() + kBlizzardEveryMs;
            if (Blizzard())
                return;
        }
        if (Now() >= _barrierAt)
        {
            _barrierAt = Now() + kIceBarrierEveryMs;
            IceBarrier();
        }
        Unit* victim = me->GetVictim();
        if (Now() >= _coneAt && victim && me->GetExactDist2d(victim) <= kConeRangeYd)
        {
            _coneAt = Now() + kConeEveryMs;
            DoCastVictim(SPELL_STOCK_CONE_OF_COLD);
            return;
        }
        if (Now() >= _boltAt)
        {
            _boltAt = Now() + kFrostboltEveryMs;
            DoCastVictim(SPELL_STOCK_FROSTBOLT);
            return;
        }
        Melee();
    }

    std::string Fire(uint8 which) override
    {
        switch (which)
        {
            case 0:
                return Blizzard() ? std::string() : std::string("No player to target.");
            case 1:
                FrostNova();
                return {};
            default:
                IceBarrier();
                return {};
        }
    }

    std::string State2() const override
    {
        return Acore::StringFormat("barrier={} next blizzard={}ms nova-ready={}ms", me->HasAura(SPELL_VL_ICE_BARRIER)
            ? 1 : 0, _blizzardAt > Now() ? _blizzardAt - Now() : 0, _novaReadyAt > Now() ? _novaReadyAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        _nova = MechanicHandle();
        me->RemoveAurasDueToSpell(SPELL_VL_ICE_BARRIER);
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        return [](BossMechanics::Descriptor& d)
        {
            d.interrupts.emplace_back(NPC_VOLIDA, SPELL_VL_FROST_NOVA_CAST, 2);     // EN12
            d.interrupts.emplace_back(NPC_VOLIDA, SPELL_STOCK_FROSTBOLT, 1);        // a reward
            d.purges.emplace_back(NPC_VOLIDA, SPELL_VL_ICE_BARRIER, 2);             // EN13
            d.dispels.emplace_back(SPELL_VL_FROST_NOVA_ROOT, 1);
        };
    }

    std::vector<uint32> PlayerAuras() const override
    {
        return { SPELL_VL_BLIZZARD_SLOW, SPELL_VL_FROST_NOVA_ROOT, SPELL_STOCK_FROSTBOLT, SPELL_STOCK_CONE_OF_COLD };
    }

private:
    uint32 PlayersWithin(float yd)
    {
        uint32 n = 0;
        for (Player* p : FightPlayers(me))
            if (me->GetExactDist2d(p) <= yd)
                ++n;
        return n;
    }

    // EN11: a 2 s marker at a random player's spot, then 6 s of 4% a second and the slow.
    bool Blizzard()
    {
        Player* target = AnyPlayer(me);
        if (!target)
            return false;
        Position const spot = Spot(me, DungeonKit::PlaneOf(target), target->GetPositionZ());
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(spot), kBlizzardRadius, Ms(kBlizzardWarnMs));
        ref.Persistent(Ms(kBlizzardMs), Ms(kBlizzardTickMs)).Damage(kBlizzardPct).TankDamage(kBlizzardPct)
            .Spell(SPELL_VL_BLIZZARD)
            .Rider(SPELL_VL_BLIZZARD_SLOW).Tag(TAG_VL_BLIZZARD);
        BrdRingOfLaw::JudgedPersistent(ref, me, "blizzard");
        Track(ref.Handle());
        // The storm's look on a stalker from the marker's end.
        if (Creature* stalker = me->SummonCreature(NPC_BRD_STALKER, spot.GetPositionX(), spot.GetPositionY(),
            spot.GetPositionZ(), 0.f, TEMPSUMMON_TIMED_DESPAWN, kBlizzardWarnMs + kBlizzardMs + 500))
        {
            ObjectGuid const guid = stalker->GetGUID();
            Later(kBlizzardWarnMs, [this, guid]()
            {
                if (Creature* s = ObjectAccessor::GetCreature(*me, guid))
                    s->CastSpell(s, SPELL_VL_BLIZZARD_LOOK, true);
            });
        }
        Log("blizzard", Acore::StringFormat("target={}", target->GetName()));
        return true;
    }

    // EN12: the 1.5 s kickable cast; the ring at her spot (she blinks once it resolves).
    void FrostNova()
    {
        Position const at(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), 0.f);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(at), kNovaRadius, Ms(kNovaCastMs));
        ref.Damage(kNovaPct).TankDamage(kNovaPct).Weakened().Spell(SPELL_VL_FROST_NOVA).Rider(SPELL_VL_FROST_NOVA_ROOT)
            .Tag(TAG_VL_FROST_NOVA);
        BrdRingOfLaw::Judged(ref, me, "frost-nova");
        _nova = ref.Handle();
        Track(_nova);
        _novaReadyAt = Now() + kNovaRetryMs;
        me->CastSpell(me, SPELL_VL_FROST_NOVA_CAST, false);
        Log("frost-nova", Acore::StringFormat("within={}", PlayersWithin(kNovaRadius)));
    }

    // Away from the nearest player, on the floor.
    void Blink()
    {
        if (Fallen() || !me->IsAlive())
            return;
        Player* nearest = NearestPlayer(me);
        if (!nearest)
            return;
        std::optional<Vec2> const to = AwayFrom(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(nearest), kBlinkYd);
        if (!to)
        {
            Log("blink-none", "no floor");
            return;
        }
        Position const dest = Spot(me, *to, me->GetPositionZ(), me->GetOrientation());
        me->CastSpell(me, SPELL_VL_BLINK_LOOK, true);
        me->NearTeleportTo(dest.GetPositionX(), dest.GetPositionY(), dest.GetPositionZ(), me->GetOrientation());
        Log("blink", Acore::StringFormat("to=({:.1f}, {:.1f})", dest.GetPositionX(), dest.GetPositionY()));
    }

    // EN13: 10% of her health.
    void IceBarrier()
    {
        me->RemoveAurasDueToSpell(SPELL_VL_ICE_BARRIER);
        int32 const amount = int32(me->CountPctFromMaxHealth(kIceBarrierPct));
        me->CastCustomSpell(SPELL_VL_ICE_BARRIER, SPELLVALUE_BASE_POINT0, amount, me, true);
        Log("ice-barrier", Acore::StringFormat("absorb={}", amount));
    }

    MechanicHandle _nova;
    uint64 _blizzardAt = 0;
    uint64 _novaReadyAt = 0;
    uint64 _barrierAt = 0;
    uint64 _boltAt = 0;
    uint64 _coneAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Malgen Longspear 16052: EN14 Piercing Shot, EN15 Snap Trap and Disengage, EN16 Multi-Shot; his Shoot between them
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_encore_malgen : public EncoreMemberAI
{
    explicit npc_brd_encore_malgen(Creature* creature) : EncoreMemberAI(creature, Member::Malgen) { }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_MA_PIERCING_SHOT_CAST && _pierce)
        {
            Mechanic::Cancel(me, _pierce);
            _pierce = MechanicHandle();
            Log("piercing-shot-stopped");
        }
        else if (spell && spell->Id == SPELL_MA_MULTI_SHOT_BAR && _multi)
        {
            Mechanic::Cancel(me, _multi);
            _multi = MechanicHandle();
            Log("multi-shot-stopped");
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_MA_PIERCING_SHOT_CAST)
            _pierce = MechanicHandle();
        else if (spell && spell->Id == SPELL_MA_MULTI_SHOT_BAR)
            _multi = MechanicHandle();
    }

protected:
    float Range() const override { return kMalgenRangeYd; }

    void StartFight() override
    {
        _pierceAt = Now() + FirstOf(kPiercingEveryMs);
        _multiAt = Now() + FirstOf(kMultiShotEveryMs);
        _shootAt = Now() + kShootEveryMs;
        _meleeMs = 0;
        Mechanic::NoteNextCastIn(me, SPELL_MA_PIERCING_SHOT_CAST, Ms(FirstOf(kPiercingEveryMs)));
    }

    void UpdateAlways(uint32 diff) override
    {
        bool inMelee = false;
        for (Player* p : FightPlayers(me))
            inMelee = inMelee || me->GetExactDist2d(p) <= kTrapMeleeYd;
        _meleeMs = MeleeClock(_meleeMs, diff, inMelee);
    }

    void UpdateFight() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (TrapDue(_meleeMs, Now(), _lastTrapAt))
        {
            SnapTrap();
            return;
        }
        if (Now() >= _pierceAt)
        {
            _pierceAt = Now() + kPiercingEveryMs;
            Mechanic::NoteNextCastIn(me, SPELL_MA_PIERCING_SHOT_CAST, Ms(kPiercingEveryMs));
            if (PiercingShot())
                return;
        }
        if (Now() >= _multiAt)
        {
            _multiAt = Now() + kMultiShotEveryMs;
            if (MultiShot())
                return;
        }
        Unit* victim = me->GetVictim();
        if (Now() >= _shootAt && victim && me->GetExactDist2d(victim) >= kShootMinYd && me->IsWithinLOSInMap(victim))
        {
            _shootAt = Now() + kShootEveryMs;
            me->SetFacingToObject(victim);
            me->CastCustomSpell(SPELL_MA_SHOOT, SPELLVALUE_BASE_POINT0,
                int32(DungeonKit::RefFlatOn(me, victim, kShootPct)), victim, true);
            return;
        }
        Melee();
    }

    std::string Fire(uint8 which) override
    {
        switch (which)
        {
            case 0:
                return PiercingShot() ? std::string() : std::string("No player, or no wall behind one.");
            case 1:
                SnapTrap();
                return {};
            default:
                return MultiShot() ? std::string() : std::string("No player to shoot.");
        }
    }

    std::string State2() const override
    {
        return Acore::StringFormat("traps={} melee={}ms next pierce={}ms multi={}ms", _traps.size(), _meleeMs,
            _pierceAt > Now() ? _pierceAt - Now() : 0, _multiAt > Now() ? _multiAt - Now() : 0);
    }

    void ExtraCleanup() override
    {
        _pierce = MechanicHandle();
        _multi = MechanicHandle();
        for (ObjectGuid const& guid : _traps)
            if (GameObject* go = me->GetMap() ? me->GetMap()->GetGameObject(guid) : nullptr)
                go->DespawnOrUnsummon();
        _traps.clear();
    }

    std::function<void(BossMechanics::Descriptor&)> DescriptorFill() const override
    {
        return [](BossMechanics::Descriptor& d)
        {
            d.interrupts.emplace_back(NPC_MALGEN_LONGSPEAR, SPELL_MA_PIERCING_SHOT_CAST, 1, Ms(kPiercingEveryMs));
            d.dispels.emplace_back(SPELL_MA_SNAP_TRAP_FREEZE, 1);
        };
    }

    std::vector<uint32> PlayerAuras() const override
    {
        return { SPELL_MA_SNAP_TRAP_FREEZE };
    }

private:
    // EN14: the 3 s kickable cast; a 3 yd line from him through a random player to the wall.
    bool PiercingShot()
    {
        Player* target = AnyPlayer(me);
        if (!target)
            return false;
        Vec2 const from = DungeonKit::PlaneOf(me);
        std::optional<Vec2> const end = BrdRingOfLaw::WallEnd(from, DungeonKit::PlaneOf(target), kPiercingWallInset);
        if (!end || DungeonKit::Distance(from, *end) < 2.f)
        {
            Log("piercing-shot-none", "off the floor");
            return false;
        }
        float const facing = DungeonKit::BearingTo(from, *end);
        Position const start = Spot(me, from, me->GetPositionZ(), facing);
        Position const stop = Spot(me, *end, me->GetPositionZ(), facing);
        me->StopMoving();
        me->SetFacingTo(facing);
        MechanicRef ref = Mechanic::Line(me, BossMechanics::Anchor(start), BossMechanics::Anchor(stop),
            kPiercingWidth, Ms(kPiercingCastMs));
        ref.Damage(kPiercingPct).TankDamage(kPiercingPct)
            .Weakened().Spell(SPELL_MA_PIERCING_SHOT).Tag(TAG_MA_PIERCING_SHOT);
        BrdRingOfLaw::Judged(ref, me, "piercing-shot");
        _pierce = ref.Handle();
        Track(_pierce);
        me->CastSpell(me, SPELL_MA_PIERCING_SHOT_CAST, false);
        Log("piercing-shot", Acore::StringFormat("target={} length={:.1f}", target->GetName(),
            DungeonKit::Distance(from, *end)));
        return true;
    }

    // EN16: the 2 s bar, a 30 yd cone toward a random player.
    bool MultiShot()
    {
        Player* target = AnyPlayer(me, kMultiShotLength);
        if (!target)
            return false;
        float const facing = DungeonKit::BearingTo(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(target));
        Position const apex(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), facing);
        me->StopMoving();
        me->SetFacingTo(facing);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(BossMechanics::Anchor(apex),
            kMultiShotAngleDeg, kMultiShotLength), Ms(kMultiShotWarnMs));
        ref.Damage(kMultiShotPct).TankDamage(kMultiShotPct)
            .Weakened().Spell(SPELL_MA_MULTI_SHOT).Tag(TAG_MA_MULTI_SHOT);
        BrdRingOfLaw::Judged(ref, me, "multi-shot");
        _multi = ref.Handle();
        Track(_multi);
        DungeonKit::CastBar(me, SPELL_MA_MULTI_SHOT_BAR);
        Log("multi-shot", Acore::StringFormat("target={}", target->GetName()));
        return true;
    }

    // EN15: a trap at his feet (the registry's Mine: arming, the hit, the cap, the 60 s), then the Disengage.
    void SnapTrap()
    {
        _lastTrapAt = Now();
        _meleeMs = 0;
        Position const pos(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), 0.f);
        ObjectGuid goGuid;
        if (GameObject* go = me->SummonGameObject(GO_SNAP_TRAP, pos.GetPositionX(), pos.GetPositionY(),
            pos.GetPositionZ(), frand(0.f, DungeonKit::kTwoPi), 0.f, 0.f, 0.f, 0.f, kTrapLifeMs / 1000 + 5))
            goGuid = go->GetGUID();
        MechanicRef ref = Mechanic::Mine(me, pos, kTrapRadius, Ms(kTrapArmMs), Ms(kTrapGraceMs));
        ref.Lifetime(Ms(kTrapLifeMs)).Cap(kTrapCapGroup, kTrapCap).Damage(kTrapPct).TankDamage(kTrapPct).Weakened()
            .Spell(SPELL_MA_SNAP_TRAP).Rider(SPELL_MA_SNAP_TRAP_FREEZE).Tag(TAG_MA_SNAP_TRAP);
        // A sprung trap: -1 Favor per player caught (a trap that snaps shut unsprung is not judged).
        Map* map = me->GetMap();
        uint32 const instanceId = map ? map->GetInstanceId() : 0;
        ObjectGuid const owner = me->GetGUID();
        ref.OnResolve([map, instanceId, goGuid, owner](ResolveResult const& r)
        {
            if (!map || map->GetInstanceId() != instanceId)
                return;
            if (GameObject* go = map->GetGameObject(goGuid))
                go->DespawnOrUnsummon();
            if (r.fizzled)
                return;
            Creature* malgen = map->GetCreature(owner);
            RingFrame* frame = malgen ? BrdRingOfLaw::FrameOf(malgen) : nullptr;
            for (ObjectGuid const& hit : r.hits)
                if (frame && hit.IsPlayer())
                    frame->FavorHit(hit, "snap-trap");
            LogEn("malgen", "snap-trap-sprung", Acore::StringFormat("hits={}", r.hits.size()));
        });
        Track(ref.Handle());
        if (goGuid)
        {
            _traps.push_back(goGuid);
            if (_traps.size() > kTrapCap * 2)
                _traps.erase(_traps.begin());
        }
        Log("snap-trap", Acore::StringFormat("at=({:.1f}, {:.1f})", pos.GetPositionX(), pos.GetPositionY()));
        Disengage();
    }

    // 15 yd away from the nearest player, on the floor.
    void Disengage()
    {
        Player* nearest = NearestPlayer(me);
        if (!nearest)
            return;
        std::optional<Vec2> const to = AwayFrom(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(nearest),
            kDisengageYd);
        if (!to)
        {
            Log("disengage-none", "no floor");
            return;
        }
        Position const dest = Spot(me, *to, me->GetPositionZ(), me->GetOrientation());
        me->CastSpell(me, SPELL_MA_DISENGAGE_LOOK, true);
        DungeonKit::JumpTo(me, dest, kDisengageSpeedXY);
        Log("disengage", Acore::StringFormat("to=({:.1f}, {:.1f})", dest.GetPositionX(), dest.GetPositionY()));
    }

    MechanicHandle _pierce;
    MechanicHandle _multi;
    std::vector<ObjectGuid> _traps;
    uint32 _meleeMs = 0;
    uint64 _lastTrapAt = 0;
    uint64 _pierceAt = 0;
    uint64 _multiAt = 0;
    uint64 _shootAt = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Korv's totems 300789-300791 (EN6): one hit each (the script sets 1 health), rooted, passive
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_encore_totem : public ScriptedAI
{
    explicit npc_brd_encore_totem(Creature* creature)
        : ScriptedAI(creature), _kind(TotemOf(creature->GetEntry()).value_or(TotemKind::Searing)) { }

    void Reset() override
    {
        me->SetMaxHealth(kTotemHealth);
        me->SetHealth(kTotemHealth);
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
        _tickMs = 1000;
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    void UpdateAI(uint32 diff) override
    {
        if (_tickMs > diff)
        {
            _tickMs -= diff;
            return;
        }
        switch (_kind)
        {
            case TotemKind::HealingStream:
                _tickMs = kHealingStreamTickMs;
                HealingStream();
                break;
            case TotemKind::Searing:
                _tickMs = kSearingTickMs;
                Searing();
                break;
            case TotemKind::Earthbind:
                _tickMs = kEarthbindTickMs;
                Earthbind();
                break;
        }
    }

private:
    void HealingStream()
    {
        for (Creature* mate : TeamAround(me, kHealingStreamRangeYd))
            if (!IsBody(mate) && mate->GetHealthPct() < 100.f)
                me->CastCustomSpell(SPELL_KO_HEALING_STREAM, SPELLVALUE_BASE_POINT0,
                    int32(mate->CountPctFromMaxHealth(kHealingStreamPct)), mate, true);
    }

    void Searing()
    {
        std::vector<Player*> near;
        for (Player* p : FightPlayers(me))
            if (me->GetExactDist2d(p) <= kSearingRangeYd && me->IsWithinLOSInMap(p))
                near.push_back(p);
        if (near.empty())
            return;
        Player* target = near[urand(0, uint32(near.size() - 1))];
        me->CastCustomSpell(SPELL_KO_SEARING_BOLT, SPELLVALUE_BASE_POINT0,
            int32(DungeonKit::RefFlatOn(me, target, kSearingPct)), target, true);
    }

    void Earthbind()
    {
        for (Player* p : FightPlayers(me))
            if (me->GetExactDist2d(p) <= kEarthbindRangeYd)
                me->CastSpell(p, SPELL_KO_EARTHBIND, true);
    }

    TotemKind _kind;
    uint32 _tickMs = 1000;
};

// ---------------------------------------------------------------------------------------------------------------------
// EN1 the banner (301280, a goober with the stock banner's display): the click burns it
// ---------------------------------------------------------------------------------------------------------------------
struct go_brd_encore_banner : public GameObjectAI
{
    explicit go_brd_encore_banner(GameObject* go) : GameObjectAI(go) { }

    void InitializeAI() override
    {
        // A reload with the banner burned: never clickable again.
        if (InstanceScript* instance = me->GetInstanceScript())
            if (instance->GetData(DATA_BANNER_BURNED))
                me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        // Handled either way (true): the click never reaches GameObject::Use's goober branch.
        if (reportUse || !player)
            return true;
        Burn(player);
        return true;
    }

    void UpdateAI(uint32 diff) override
    {
        if (!_goneInMs)
            return;
        if (_goneInMs > diff)
        {
            _goneInMs -= diff;
            return;
        }
        _goneInMs = 0;
        me->DespawnOrUnsummon();
    }

private:
    void Burn(Player* player)
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance || _goneInMs || !player->IsAlive())
            return;
        if (!instance->GetData(DATA_BANNER_BURNED))
            instance->SetData(DATA_BANNER_BURNED, 1);   // the instance refuses it off heroic or once the Ring is won
        if (!instance->GetData(DATA_BANNER_BURNED))
        {
            LogEn("encore", "banner-refused", Acore::StringFormat("by={} heroic={} thrown={}", player->GetName(),
                IsHeroicMap(me) ? 1 : 0, instance->GetData(DATA_BANNER_THROWN)));
            return;
        }
        me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        player->CastSpell(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), SPELL_EN_BANNER_BURN, true);
        if (RingFrame* frame = BrdRingOfLaw::FrameOf(me))
            frame->GrimstoneSay(BrdRingOfLaw::SAY_GRIM_BANNER_BURNED, player);
        _goneInMs = kBannerBurnMs;
        LogEn("encore", "armed", Acore::StringFormat("by={} banner burned: the Encore follows the title holder",
            player->GetName()));
    }

    uint32 _goneInMs = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// The Encore's per-attempt script on Grimstone's hooks (RingOfLawFight.h EncoreScript)
// ---------------------------------------------------------------------------------------------------------------------
class EncoreRun;

namespace
{
    // The live run per instance (`.dbtest brd encore state`): set by the run, cleared in its destructor. Instance
    // maps update on several threads at once: every access holds RunsLock().
    std::unordered_map<uint32, EncoreRun*>& Runs()
    {
        static std::unordered_map<uint32, EncoreRun*> runs;
        return runs;
    }

    std::mutex& RunsLock()
    {
        static std::mutex lock;
        return lock;
    }

    // Places the banner at its spot unless one stands there (the summoner owns it: Grimstone, or a GM's test).
    GameObject* PlaceBanner(WorldObject* summoner, char const* why)
    {
        if (GameObject* banner = summoner->FindNearestGameObject(GO_BRD_ENCORE_BANNER, kBannerSearchYd))
            return banner;
        float const z = GroundZ(summoner, kBannerSpot.x, kBannerSpot.y, kBannerSpot.z);
        GameObject* banner = summoner->SummonGameObject(GO_BRD_ENCORE_BANNER, kBannerSpot.x, kBannerSpot.y, z,
            kBannerO, 0.f, 0.f, std::sin(kBannerO / 2.f), std::cos(kBannerO / 2.f), kBannerBackstopSec);
        LogEn("encore", "banner", Acore::StringFormat("why={} placed={}", why, banner ? 1 : 0));
        return banner;
    }
}

class EncoreRun : public BrdRingOfLaw::EncoreScript
{
public:
    EncoreRun() = default;

    ~EncoreRun() override
    {
        if (_instanceId)
        {
            std::lock_guard<std::mutex> guard(RunsLock());
            auto it = Runs().find(_instanceId);
            if (it != Runs().end() && it->second == this)
                Runs().erase(it);
        }
    }

    void OnBannerThrown(Creature* grimstone) override
    {
        Bind(grimstone);
        PlaceBanner(grimstone, "thrown");
    }

    void OnAttemptStart(Creature* grimstone) override
    {
        Bind(grimstone);
        InstanceScript* instance = grimstone->GetInstanceScript();
        if (instance && instance->GetData(DATA_BANNER_THROWN) && !instance->GetData(DATA_BANNER_BURNED))
            PlaceBanner(grimstone, "attempt");
    }

    bool Start(Creature* grimstone, RingFrame& /*frame*/) override
    {
        Bind(grimstone);
        if (!IsHeroicMap(grimstone))
            return false;
        for (std::size_t i = 0; i < kTeamSize; ++i)
            Summon(grimstone, i, true);
        _running = _guids[IndexOf(Member::Theldren)] != ObjectGuid::Empty;
        LogEn("encore", "start", Acore::StringFormat("summoned={} health={}", Count(), TeamHealth()));
        return _running;
    }

    void Update(Creature* grimstone, RingFrame& frame, uint32 diff) override
    {
        if (!_running || _won)
            return;
        _watchMs += diff;
        if (_watchMs < kWatchMs)
            return;
        uint32 const step = _watchMs;
        _watchMs = 0;

        std::array<BodyState, kTeamSize> team{};
        for (std::size_t i = 0; i < kTeamSize; ++i)
        {
            Creature* c = ObjectAccessor::GetCreature(*grimstone, _guids[i]);
            if (c && c->IsInWorld())
            {
                _lostMs[i] = 0;
                EncoreMemberAI* ai = MemberAI(c);
                team[i] = !c->IsAlive() ? BodyState::Dead : ai ? ai->State() : BodyState::Up;
            }
            else if (_seen[i] == BodyState::Dead)
                team[i] = BodyState::Dead;      // a corpse gone with its timer
            else
            {
                team[i] = BodyState::Up;
                _lostMs[i] += step;
                if (_lostMs[i] >= kMemberLostMs)
                {
                    _lostMs[i] = 0;
                    LogEn("encore", "member-lost", Acore::StringFormat("member={}: summoned again",
                        MemberKey(static_cast<Member>(i))));
                    Summon(grimstone, i, false);
                }
            }
            if (team[i] != _seen[i])
                LogEn("encore", "member-state", Acore::StringFormat("member={} {} -> {}",
                    MemberKey(static_cast<Member>(i)), uint32(_seen[i]), uint32(team[i])));
            _seen[i] = team[i];
        }

        switch (Judge(team))
        {
            case Verdict::FinishBodies:
                FinishBodies(grimstone);
                break;
            case Verdict::Won:
            {
                _won = true;
                LogEn("encore", "won", "all five down");
                frame.EncoreWon();      // D4: DATA_ENCORE_WON, the chest, credit 16166, the Ring's credit; Stop(true)
                return;
            }
            default:
                break;
        }
    }

    void Stop(Creature* grimstone, bool won) override
    {
        bool const wasRunning = _running;
        _running = false;
        RemoveEncoreAuras(grimstone->GetInstanceScript());
        if (!won)
            for (ObjectGuid const& guid : _guids)
                if (Creature* c = ObjectAccessor::GetCreature(*grimstone, guid))
                    c->DespawnOrUnsummon();
        // The credit: a thrown banner left unburned goes with the Ring (Grimstone outlives the win; R-1-RING N-1).
        if (won)
            if (GameObject* banner = grimstone->FindNearestGameObject(GO_BRD_ENCORE_BANNER, kBannerSearchYd))
                banner->DespawnOrUnsummon();
        if (wasRunning)
            LogEn("encore", won ? "stop-won" : "stop-wipe", Acore::StringFormat("members={}", Count()));
    }

    std::string State(WorldObject const* probe) const
    {
        std::string out = Acore::StringFormat("Encore run: running={} won={} |", _running ? 1 : 0, _won ? 1 : 0);
        for (std::size_t i = 0; i < kTeamSize; ++i)
        {
            Creature* c = probe ? ObjectAccessor::GetCreature(*probe, _guids[i]) : nullptr;
            out += Acore::StringFormat(" {}={}{}", MemberKey(static_cast<Member>(i)), uint32(_seen[i]),
                c ? Acore::StringFormat("({:.0f}%)", c->GetHealthPct()) : std::string());
        }
        return out;
    }

private:
    void Bind(Creature* grimstone)
    {
        if (_instanceId || !grimstone->GetMap())
            return;
        _instanceId = grimstone->GetMap()->GetInstanceId();
        std::lock_guard<std::mutex> guard(RunsLock());
        Runs()[_instanceId] = this;
    }

    uint32 Count() const
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : _guids)
            if (guid)
                ++n;
        return n;
    }

    // A member on the gallery (leaping down), or straight at its landing (summoned again).
    void Summon(Creature* grimstone, std::size_t i, bool leap)
    {
        Member const m = static_cast<Member>(i);
        Vec2 const land = LandingOf(i);
        Position const landing = Spot(grimstone, land, kRingCenter.z,
            DungeonKit::BearingTo(land, kRingCenter.XY()));
        Point3 const g = kGallery[i];
        float const o = DungeonKit::BearingTo(g.XY(), kRingCenter.XY());
        Position const from = leap ? Position(g.x, g.y, g.z, o) : landing;
        // Grimstone summons them (his JustSummoned tracks and engages them on the Ring's encounter; his wipe despawns
        // them), corpse-timed (KT-D1) so the corpses keep their loot.
        Creature* c = grimstone->SummonCreature(EntryOf(m), from.GetPositionX(), from.GetPositionY(),
            from.GetPositionZ(), from.GetOrientation(), TEMPSUMMON_CORPSE_TIMED_DESPAWN, kCorpseMs);
        if (!c)
        {
            LogEn("encore", "summon-refused", MemberKey(m));
            return;
        }
        _guids[i] = c->GetGUID();
        _seen[i] = BodyState::Up;
        _lostMs[i] = 0;
        if (m == Member::Theldren)
        {
            // Rule 1 / S0 section 5 item 6: the hard mode loot bit at his summon (the instance never sees him).
            DungeonKit::SetHardModeLoot(c, true);
            if (leap && c->IsAIEnabled)
                c->AI()->Talk(SAY_TH_LEAP);
        }
        if (EncoreMemberAI* ai = MemberAI(c))
        {
            if (leap)
                ai->Leap(landing);
            else
                ai->Land("summoned again");
        }
    }

    // Every body finished, Theldren last (his corpse carries the hard mode list).
    void FinishBodies(Creature* grimstone)
    {
        for (Member m : kFinishOrder)
        {
            Creature* c = ObjectAccessor::GetCreature(*grimstone, _guids[IndexOf(m)]);
            EncoreMemberAI* ai = MemberAI(c);
            if (!c || !c->IsAlive() || !ai || !ai->Fallen())
                continue;
            Player* killer = c->GetLootRecipient();
            ai->Finish(killer);
            LogEn("encore", "finish", Acore::StringFormat("member={} killer={}", MemberKey(m),
                killer ? killer->GetName() : "-"));
        }
    }

    std::array<ObjectGuid, kTeamSize> _guids{};
    std::array<BodyState, kTeamSize> _seen{};
    std::array<uint32, kTeamSize> _lostMs{};
    uint32 _instanceId = 0;
    uint32 _watchMs = 0;
    bool _running = false;
    bool _won = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest brd encore`
// ---------------------------------------------------------------------------------------------------------------------
namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowHardModeInfo(handler, "encore", DATA_BANNER_BURNED, BOSS_ENCORE);
    }

    Player* GmPlayer(ChatHandler* handler)
    {
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!gm)
            handler->SendErrorMessage("No player.");
        return gm;
    }

    // `.dbtest brd encore state`: the flags, the live run, every member near the GM.
    bool HandleState(ChatHandler* handler)
    {
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* gm = GmPlayer(handler);
        if (!gm)
            return false;
        InstanceScript* instance = gm->GetInstanceScript();
        handler->PSendSysMessage("Encore: heroic {} thrown {} burned {} slot {} favor {}", IsHeroicMap(gm) ? 1 : 0,
            instance ? instance->GetData(DATA_BANNER_THROWN) : 0, instance ? instance->GetData(DATA_BANNER_BURNED) : 0,
            instance ? uint32(instance->GetBossState(BOSS_ENCORE)) : 0,
            instance ? instance->GetData(DATA_RING_FAVOR) : 0);
        {
            std::lock_guard<std::mutex> guard(RunsLock());
            auto it = Runs().find(gm->GetMap()->GetInstanceId());
            if (it != Runs().end() && it->second)
                handler->PSendSysMessage("{}", it->second->State(gm));
            else
                handler->PSendSysMessage("No Encore run (no attempt, or no banner thrown this attempt).");
        }
        for (Creature* c : TeamAround(gm, 200.f))
            if (EncoreMemberAI* ai = MemberAI(c))
                handler->PSendSysMessage("{}", ai->TestState());
        return true;
    }

    // `.dbtest brd encore banner`: the crowd's banner at its spot now (the GM summons it when Grimstone is absent).
    bool HandleBanner(ChatHandler* handler)
    {
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* gm = GmPlayer(handler);
        if (!gm)
            return false;
        InstanceScript* instance = gm->GetInstanceScript();
        if (instance)
            instance->SetData(DATA_BANNER_THROWN, 1);
        Creature* grimstone = instance ? gm->GetMap()->GetCreature(instance->GetGuidData(kGuidGrimstone)) : nullptr;
        GameObject* banner = PlaceBanner(grimstone ? static_cast<WorldObject*>(grimstone) : gm, "test");
        handler->PSendSysMessage("Banner {} (thrown flag {}).", banner ? "placed" : "refused",
            instance ? instance->GetData(DATA_BANNER_THROWN) : 0);
        return true;
    }

    // `.dbtest brd encore burn`: both flags (the instance refuses them off heroic or once the Ring is won).
    bool HandleBurn(ChatHandler* handler)
    {
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* gm = GmPlayer(handler);
        InstanceScript* instance = gm ? gm->GetInstanceScript() : nullptr;
        if (!instance)
            return false;
        instance->SetData(DATA_BANNER_THROWN, 1);
        instance->SetData(DATA_BANNER_BURNED, 1);
        handler->PSendSysMessage("Banner thrown {} burned {}.", instance->GetData(DATA_BANNER_THROWN),
            instance->GetData(DATA_BANNER_BURNED));
        return true;
    }

    // `.dbtest brd encore spawn`: the five around the GM, no frame, on the floor (no leap); Theldren with the loot bit.
    bool HandleSpawn(ChatHandler* handler)
    {
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* gm = GmPlayer(handler);
        if (!gm)
            return false;
        for (std::size_t i = 0; i < kTeamSize; ++i)
        {
            float const o = gm->GetOrientation() + (float(i) - 2.f) * 0.5f;
            Position const at = Spot(gm, DungeonKit::Advance(DungeonKit::PlaneOf(gm), o, 8.f), gm->GetPositionZ(),
                o + DungeonKit::kPi);
            Creature* c = gm->SummonCreature(kTeamEntries[i], at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(),
                at.GetOrientation(), TEMPSUMMON_CORPSE_TIMED_DESPAWN, kCorpseMs);
            if (!c)
                continue;
            if (i == IndexOf(Member::Theldren))
                DungeonKit::SetHardModeLoot(c, true);
            if (EncoreMemberAI* ai = MemberAI(c))
                ai->Land("test spawn");
        }
        handler->PSendSysMessage("The Encore's five are up (`.gm off` to fight them).");
        return true;
    }

    template <uint32 Entry, uint8 Which>
    bool HandleFire(ChatHandler* handler)
    {
        Creature* member = BrdTest::FindBoss(handler, Entry);
        EncoreMemberAI* ai = MemberAI(member);
        if (!ai)
        {
            handler->SendErrorMessage("No Encore member AI there.");
            return false;
        }
        std::string const error = ai->TestFire(Which);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Fired.");
        return true;
    }

    template <uint32 Entry>
    bool HandleFall(ChatHandler* handler)
    {
        Creature* member = BrdTest::FindBoss(handler, Entry);
        EncoreMemberAI* ai = MemberAI(member);
        if (!ai || !ai->ForceFall())
        {
            handler->SendErrorMessage("No standing member with a fall left there.");
            return false;
        }
        handler->PSendSysMessage("Fallen: a body Korv can bring back (or the Encore's watch finishes it).");
        return true;
    }

    ChatCommandTable const& TheldrenCommands()
    {
        static ChatCommandTable const commands =
        {
            { "charge", HandleFire<NPC_THELDREN, 0>, SEC_GAMEMASTER, Console::No },
            { "roar", HandleFire<NPC_THELDREN, 1>, SEC_GAMEMASTER, Console::No },
            { "fall", HandleFall<NPC_THELDREN>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& KorvCommands()
    {
        static ChatCommandTable const commands =
        {
            { "chainheal", HandleFire<NPC_KORV, 0>, SEC_GAMEMASTER, Console::No },
            { "spirit", HandleFire<NPC_KORV, 1>, SEC_GAMEMASTER, Console::No },
            { "totems", HandleFire<NPC_KORV, 2>, SEC_GAMEMASTER, Console::No },
            { "shield", HandleFire<NPC_KORV, 3>, SEC_GAMEMASTER, Console::No },
            { "fall", HandleFall<NPC_KORV>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& LeftyCommands()
    {
        static ChatCommandTable const commands =
        {
            { "step", HandleFire<NPC_LEFTY, 0>, SEC_GAMEMASTER, Console::No },
            { "evasion", HandleFire<NPC_LEFTY, 1>, SEC_GAMEMASTER, Console::No },
            { "fall", HandleFall<NPC_LEFTY>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& VolidaCommands()
    {
        static ChatCommandTable const commands =
        {
            { "blizzard", HandleFire<NPC_VOLIDA, 0>, SEC_GAMEMASTER, Console::No },
            { "nova", HandleFire<NPC_VOLIDA, 1>, SEC_GAMEMASTER, Console::No },
            { "barrier", HandleFire<NPC_VOLIDA, 2>, SEC_GAMEMASTER, Console::No },
            { "fall", HandleFall<NPC_VOLIDA>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& MalgenCommands()
    {
        static ChatCommandTable const commands =
        {
            { "piercing", HandleFire<NPC_MALGEN_LONGSPEAR, 0>, SEC_GAMEMASTER, Console::No },
            { "trap", HandleFire<NPC_MALGEN_LONGSPEAR, 1>, SEC_GAMEMASTER, Console::No },
            { "multishot", HandleFire<NPC_MALGEN_LONGSPEAR, 2>, SEC_GAMEMASTER, Console::No },
            { "fall", HandleFall<NPC_MALGEN_LONGSPEAR>, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    // `.dbtest brd encore <info|state|banner|burn|spawn>` and `.dbtest brd encore <member> <mechanic|fall>`.
    ChatCommandTable const& EncoreTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
            { "state", HandleState, SEC_GAMEMASTER, Console::No },
            { "banner", HandleBanner, SEC_GAMEMASTER, Console::No },
            { "burn", HandleBurn, SEC_GAMEMASTER, Console::No },
            { "spawn", HandleSpawn, SEC_GAMEMASTER, Console::No },
            { "theldren", TheldrenCommands() },
            { "korv", KorvCommands() },
            { "lefty", LeftyCommands() },
            { "volida", VolidaCommands() },
            { "malgen", MalgenCommands() },
        };
        return commands;
    }
}

void AddSC_brd_ring_encore_hard_mode()
{
    RegisterDungeonReworkCreatureAI(npc_brd_encore_theldren, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_encore_korv, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_encore_lefty, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_encore_volida, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_encore_malgen, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_encore_totem, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_brd_encore_banner, BlackrockDepthsRework::kInstanceScriptName);
    BrdRingOfLaw::RegisterEncore([]() { return std::make_unique<EncoreRun>(); });
    BrdTest::RegisterBoss("encore", EncoreTestCommands());
}
