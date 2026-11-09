/*
 * mod-dungeon-bosses, Stratholme S2: Hearthsinger Forresten (10558), "a concert for the dead that you can't leave, and
 * the rats come to listen". Build spec ST 826-882 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows HF
 * and 3.5 row S2. Replaces the stock SmartAI (Incorporeal Defense, Demoralizing Shout and the 10 s Enchanting Lullaby
 * are gone; Shoot 16100 and Multi-Shot 14443 stay, in the breaks between songs): the creature template is rebound by
 * apps/dbc-tools source/npcs/stratholme/hearthsinger_forresten.py, the SmartAI rows are dropped by
 * rev_hearthsinger_forresten_stratholme.sql. Pure rules: ForrestenLogic.h.
 *
 *   HF1  The set list     Jig, Lullaby, Piper's Tune, around again, on timers (never health): the first song at 6 s,
 *                         a song 20 s (heroic 18 s), a break 6 s (heroic 4 s); yell lines 1 to 3 name the song
 *   HF2  Gutter Rats      at each song's start 6 / 6 / 3 rats pour out of the gutters (heroic 8 / 8 / 4), 1,000 health
 *                         (heroic 1,500), melee on the players; they stay until killed
 *   HF3  Plague Bite      a rat's bite adds a stack of the Disease (1% a second a stack, 10 s, 5 stacks); the stacks
 *                         are the boss's own (cast as him), so every rat's bites add up; a dispel cures it
 *   HF4  The Jig          a beat every 2 s (1 s after a missed Crescendo): a 4 yd note, a 1.5 s marker, under 2 random
 *                         players (heroic: every player) and 2 random floor spots: 20% Arcane + Weakened + a dance
 *   HF5  The Lullaby      an 8 yd hearth 10..15 yd from him (a stalker 300603 carries the glow, a registry Stack for
 *                         non-tanks); HF6 Drowsy: a non-tank outside it gains a stack every 2 s, three stacks sleep it
 *                         for 2 s and clear the stacks; the rats go for the drowsy and the sleeping first
 *   HF7  The Piper's Tune 4 s in, every rat still alive falls in behind him and streams out in a volley: one 2 yd
 *                         line per rat, a new line every 0.5 s, aimed 0..4 yd from a player taken in turn; the rat
 *                         runs the line out and back (the registry tracks it); 15% + Weakened. A second volley 2 s
 *                         after the first's last line, when 3 s of the song remain
 *   HF8  Crescendo        once a song, 5..12 s in, a 3 s interruptible cast (top priority on the interrupt list);
 *                         not interrupted: the Jig goes double time (HF9), the hearth moves with a 2 s glow (HF10),
 *                         the Piper adds a 6 yd line through each non-tank (HF11, 30% + Weakened); heroic: 4 more
 *                         rats (HF12)
 *   HF13 Shoot, Multi-Shot stock, in the breaks only
 *   Arena                 StratholmeRework::LeashOptions on ForrestenArena() (no grips; holds at the edge)
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one). Every firing logs
 * one INFO line "strat forresten <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "ForrestenLogic.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MoveSplineInit.h"
#include "PassiveAI.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <numeric>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratForresten;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "forresten";

    // Rat action ids for UnitAI::SetGUID.
    enum RatAction : int32
    {
        ACTION_RAT_FOCUS    = 1,    // the boss tells the rat which player to bite (The Lullaby)
    };

    enum RatPoints : uint32
    {
        POINT_RAT_GATHER    = 1,
    };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }

    // Healers and damage dealers (the hearth is for them; tanks are exempt from Drowsy).
    BossMechanics::Eligibility NonTank()
    {
        BossMechanics::Eligibility e;
        e.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        return e;
    }
}

// ====================================================================================================================
// Gutter Rat 300602 (HF2, HF3, HF7): a rat that bites, and in the Piper's Tune runs a line out and back.
// ====================================================================================================================
struct npc_st_gutter_rat : public ScriptedAI
{
    enum class State : uint8
    {
        Melee,          // fighting like any add
        Assembling,     // running to the gather point behind the boss (HF7)
        Staged,         // there, waiting for its line
        Armed,          // its line is on the floor; waits the marker's warning
        Running,        // running the line out and back
    };

    explicit npc_st_gutter_rat(Creature* creature) : ScriptedAI(creature) { }

    State GetState() const { return _state; }

    // HF7: leave the fight and run to `gather` (his back). Refused while armed or running.
    void Assemble(Position const& gather)
    {
        if (_state == State::Armed || _state == State::Running || !me->IsAlive())
            return;
        _state = State::Assembling;
        _gather = gather;
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->GetMotionMaster()->MovePoint(POINT_RAT_GATHER, gather.GetPositionX(), gather.GetPositionY(),
            gather.GetPositionZ());
    }

    // HF7: runs `path` (out to the wall, then back the same way) at `speed` after `delayMs` (the marker's warning).
    bool Launch(std::vector<DungeonKit::FloorPathPoint> const& out, float speed, uint32 delayMs)
    {
        if (_state != State::Staged || out.size() < 2)
            return false;
        _path.clear();
        _path.reserve(out.size() * 2);
        for (DungeonKit::FloorPathPoint const& p : out)
            _path.emplace_back(p.x, p.y, p.z);
        for (std::size_t i = out.size() - 1; i-- > 0;)
            _path.emplace_back(out[i].x, out[i].y, out[i].z);
        _speed = speed;
        _delayMs = delayMs;
        _state = State::Armed;
        _finished = false;
        return true;
    }

    // True once, after a run ended (the boss cancels the line then).
    bool TakeRunFinished()
    {
        bool const finished = _finished;
        _finished = false;
        return finished;
    }

    // Back to the fight: aggressive, on a random player of the fight.
    void Resume()
    {
        _state = State::Melee;
        me->SetReactState(REACT_AGGRESSIVE);
        me->GetMotionMaster()->Clear();
        DoZoneInCombat();
        if (Unit* target = SelectTarget(SelectTargetMethod::Random, 0, 100.f, true))
            AttackStart(target);
    }

    // The Lullaby: the boss names the player to bite (the drowsy and the sleeping first).
    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id != ACTION_RAT_FOCUS || _state != State::Melee || !me->IsAlive())
            return;
        Player* player = ObjectAccessor::GetPlayer(*me, guid);
        if (!player || !player->IsAlive() || player->IsGameMaster() || me->GetVictim() == player)
            return;
        DoAddThreat(player, 1000.f);
        AttackStart(player);
    }

    // HF3: a bite that lands adds a stack of Plague Bite; the boss is the caster, so the rats' stacks add up.
    void DamageDealt(Unit* victim, uint32& damage, DamageEffectType damageType, SpellSchoolMask /*schoolMask*/) override
    {
        if (damageType != DIRECT_DAMAGE || !damage || !victim || !victim->IsPlayer())
            return;
        Unit* caster = me;
        if (TempSummon* summon = me->ToTempSummon())
            if (Unit* boss = summon->GetSummonerUnit())
                caster = boss;
        DungeonKit::AddStacks(victim, SPELL_HF_PLAGUE_BITE, 1, caster, kBiteMaxStacks);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_state == State::Melee)
            ScriptedAI::EnterEvadeMode(why);
    }

    void UpdateAI(uint32 diff) override
    {
        switch (_state)
        {
            case State::Melee:
                if (!UpdateVictim())
                    return;
                DoMeleeAttackIfReady();
                return;
            case State::Assembling:
                if (me->GetExactDist2d(_gather.GetPositionX(), _gather.GetPositionY()) <= kRatStagedYd)
                {
                    _state = State::Staged;
                    me->StopMoving();
                }
                return;
            case State::Staged:
                return;
            case State::Armed:
                if (_delayMs > diff)
                {
                    _delayMs -= diff;
                    return;
                }
                _delayMs = 0;
                _state = State::Running;
                me->GetMotionMaster()->Clear();
                me->StopMoving();
                {
                    Movement::MoveSplineInit init(me);
                    init.MovebyPath(_path);
                    init.SetVelocity(_speed);
                    init.Launch();
                }
                return;
            case State::Running:
                if (me->movespline->Finalized())
                {
                    _finished = true;
                    Resume();
                }
                return;
        }
    }

private:
    State _state = State::Melee;
    Position _gather;
    Movement::PointsArray _path;
    float _speed = kRatRunSpeed;
    uint32 _delayMs = 0;
    bool _finished = false;
};

// Hearth stalker 300603 (HF5): invisible; carries the hearth's glow aura. The registry Stack owns the circle.
struct npc_st_hearth_stalker : public NullCreatureAI
{
    explicit npc_st_hearth_stalker(Creature* creature) : NullCreatureAI(creature) { }
};

// The 1.5 s dance of a note's hit (HF4): the player's emote state is the dance while the aura is on.
class spell_st_forresten_dance : public AuraScript
{
    PrepareAuraScript(spell_st_forresten_dance);

    void OnApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* target = GetTarget())
            target->SetEmoteState(static_cast<Emote>(kEmoteStateDance));
    }

    void OnRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* target = GetTarget())
            if (target->GetUInt32Value(UNIT_NPC_EMOTESTATE) == kEmoteStateDance)
                target->SetEmoteState(EMOTE_ONESHOT_NONE);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_st_forresten_dance::OnApply, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_st_forresten_dance::OnRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// ====================================================================================================================
// Hearthsinger Forresten 10558
// ====================================================================================================================
struct boss_hearthsinger_forresten_rework : public BossAI
{
    explicit boss_hearthsinger_forresten_rework(Creature* creature)
        : BossAI(creature, BOSS_FORRESTEN), _arena(ForrestenArena(), LeashOptions(kBossLogName)),
          _shape(ForrestenArena()) { }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_FORRESTEN;
        Mechanic::BeginEncounter(me, options);

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        _set.Reset(_heroic);
        _nextShootMs = kShootFirstMs;
        _multiShotMs = kMultiShotAtMs;
        Describe();
        _arena.Engage(me);
        Talk(YELL_FORRESTEN_AGGRO);
        Log("engage", Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0,
            me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);   // DONE; the summons (rats, the hearth) despawn
        Cleanup();
        Talk(YELL_FORRESTEN_DEATH);
        Log("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    // The rats fight on their own account (zoned into combat); the hearth stalker never does.
    void JustSummoned(Creature* summon) override
    {
        if (summon->GetEntry() == NPC_ST_GUTTER_RAT)
            BossAI::JustSummoned(summon);
        else
            summons.Summon(summon);
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        ForgetRat(summon->GetGUID());
        BossAI::SummonedCreatureDespawn(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        ForgetRat(summon->GetGUID());
    }

    // HF8: the cast finished (the chaos lands) or was stopped (the reward).
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_HF_CRESCENDO)
            CrescendoLanded();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_HF_CRESCENDO)
            Log("crescendo-interrupted", Acore::StringFormat("song={}", SongName(_set.Current())));
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        RunSetList();
        RunJig();
        RunLullaby();
        RunPiper();
        RunCrescendo();
        RunBreak();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The players of the fight
    // ----------------------------------------------------------------------------------------------------------------

    // Every living player of the fight: alive, not a GM, within the fight range of him.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        Map* map = me->FindMap();
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsAlive() && !player->IsGameMaster() && me->GetExactDist2d(player) <= kFightRangeYd)
                out.push_back(player);
        }
        return out;
    }

    bool IsTank(Player const* player) const
    {
        return player == me->GetVictim()
            || BossMechanics::GetRoleProvider().Get(me, player) == BossMechanics::Role::Tank;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HF1 The set list
    // ----------------------------------------------------------------------------------------------------------------

    void RunSetList()
    {
        for (SetList::Event const& event : _set.Advance(_clockMs))
        {
            if (event.kind == SetList::Event::Kind::SongStart)
                StartSong(event.song, event.index, event.at);
            else
                EndSong(event.song, event.index);
        }
    }

    void StartSong(Song song, uint32 index, uint64 startedAt)
    {
        _crescendoMissed = false;
        uint32 const offset = CrescendoOffsetMs(Rand01());
        _crescendoAtMs = startedAt + offset;
        Mechanic::NoteNextCastIn(me, SPELL_HF_CRESCENDO,
            Ms(static_cast<uint32>(_crescendoAtMs > _clockMs ? _crescendoAtMs - _clockMs : 0)));
        switch (song)
        {
            case Song::Jig:
                Talk(YELL_FORRESTEN_JIG);
                _jigEveryMs = kJigBeatMs(_heroic);
                _jigNextMs = startedAt + kJigFirstBeatMs;
                break;
            case Song::Lullaby:
                Talk(YELL_FORRESTEN_LULLABY);
                PlaceHearth(false);
                _drowsyNextMs = startedAt + kDrowsyTickMs;
                _focusNextMs = _clockMs + kRatFocusEveryMs;
                break;
            case Song::Piper:
                Talk(YELL_FORRESTEN_PIPER);
                _volleyNo = 0;
                _nextVolleyMs = startedAt + kVolleyFirstMs;
                break;
        }
        SummonRats(RatsAtStart(song, _heroic), SongName(song));
        Log("song", Acore::StringFormat("{} #{} heroic={} ends in {}s crescendo in {}ms rats alive {}", SongName(song),
            index, _heroic ? 1 : 0, kSongMs(_heroic) / 1000, offset, CountRats()));
    }

    void EndSong(Song song, uint32 index)
    {
        _crescendoAtMs = 0;
        _nextShootMs = _clockMs + kShootFirstMs;
        _multiShotMs = _clockMs + kMultiShotAtMs;
        _multiShotDone = false;
        switch (song)
        {
            case Song::Jig:
                break;
            case Song::Lullaby:
                RemoveHearth();
                ClearSleepers();
                break;
            case Song::Piper:
                EndVolley(true);
                _nextVolleyMs = 0;
                break;
        }
        Log("song-end", Acore::StringFormat("{} #{}", SongName(song), index));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HF2 Gutter Rats, HF3 Plague Bite
    // ----------------------------------------------------------------------------------------------------------------

    uint32 CountRats() const
    {
        return static_cast<uint32>(_rats.size());
    }

    // `want` rats out of the gutters (a random order, wrapping), each on a random player. Fewer when the cap is near.
    void SummonRats(uint32 want, char const* why)
    {
        uint32 const alive = CountRats();
        uint32 const count = alive >= kRatCap ? 0 : std::min(want, kRatCap - alive);
        if (!count)
            return;
        std::vector<uint32> order(kGutters.size());
        std::iota(order.begin(), order.end(), 0u);
        for (std::size_t i = order.size(); i > 1; --i)
            std::swap(order[i - 1], order[urand(0, static_cast<uint32>(i) - 1)]);
        Vec2 const center = ForrestenArenaCenter();
        std::vector<Position> at;
        for (uint32 i = 0; i < count; ++i)
        {
            Point3 const& gutter = kGutters[order[i % order.size()]];
            at.emplace_back(gutter.x, gutter.y, gutter.z, DungeonKit::BearingTo(gutter.XY(), center));
        }
        DungeonKit::WaveSpec spec;
        spec.entry = NPC_ST_GUTTER_RAT;
        spec.onSummon = [this](Creature* rat)
        {
            _rats.push_back({ rat->GetGUID(), false, MechanicHandle(), 0, 0 });
            DungeonKit::PickRule rule;
            rule.nonTank = false;
            if (Player* target = DungeonKit::PickPlayer(me, rule))
            {
                rat->EngageWithTarget(target);
                rat->AI()->AttackStart(target);
            }
        };
        std::vector<Creature*> const wave = DungeonKit::SummonWave(me, spec, at, summons);
        Log("rats", Acore::StringFormat("{}: {} of {} summoned, alive {}", why, wave.size(), want, CountRats()));
    }

    npc_st_gutter_rat* RatAI(Creature* rat) const
    {
        return rat && rat->IsAlive() && rat->IsAIEnabled ? dynamic_cast<npc_st_gutter_rat*>(rat->AI()) : nullptr;
    }

    void ForgetRat(ObjectGuid const& guid)
    {
        for (auto it = _rats.begin(); it != _rats.end(); ++it)
            if (it->guid == guid)
            {
                if (it->line)
                    Mechanic::Cancel(me, it->line);
                _rats.erase(it);
                return;
            }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HF4 The Jig, HF9 double time
    // ----------------------------------------------------------------------------------------------------------------

    void RunJig()
    {
        if (!_set.InSong() || _set.Current() != Song::Jig || _clockMs < _jigNextMs || _clockMs >= _set.EndMs())
            return;
        DropNotes();
        _jigNextMs += _jigEveryMs;
        if (_jigNextMs < _clockMs)
            _jigNextMs = _clockMs + _jigEveryMs;
    }

    // One beat: a note under `NoteCount` players and two random floor spots.
    void DropNotes()
    {
        std::vector<Player*> players = FightPlayers();
        uint32 const take = NoteCount(_heroic, static_cast<uint32>(players.size()));
        for (std::size_t i = players.size(); i > 1; --i)    // a shuffle: the first `take` are the chosen
            std::swap(players[i - 1], players[urand(0, static_cast<uint32>(i) - 1)]);
        players.resize(take);

        std::vector<Position> spots;
        std::vector<Vec2> away;
        for (Player const* player : players)
        {
            spots.push_back(player->GetPosition());
            away.push_back({ player->GetPositionX(), player->GetPositionY() });
        }
        for (uint32 i = 0; i < kNoteSpots; ++i)
            if (std::optional<Position> const spot = PickNoteSpot(away))
            {
                spots.push_back(*spot);
                away.push_back({ spot->GetPositionX(), spot->GetPositionY() });
            }
        for (Position const& at : spots)
            RegisterNote(at);
        Log("note", Acore::StringFormat("heroic={} every={}ms players={} spots={}", _heroic ? 1 : 0, _jigEveryMs,
            take, spots.size() - take));
    }

    void RegisterNote(Position const& at)
    {
        MechanicRef ref = Mechanic::Circle(me, at, kNoteRadius, Ms(kNoteWarnMs));
        ref.Damage(kNotePct).TankDamage(kNotePct).School(SPELL_SCHOOL_ARCANE).Spell(SPELL_HF_NOTE).Weakened()
            .Rider(SPELL_HF_DANCE).Tag(TAG_NOTE);
        Track(ref.Handle());
    }

    // A random floor spot near the arena's center, away from the notes already placed this beat.
    std::optional<Position> PickNoteSpot(std::vector<Vec2> const& away)
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = ForrestenArenaCenter();
        rules.minRange = 0.f;
        rules.maxRange = kNoteSpotMaxYd;
        rules.awayFrom = away;
        rules.minFromAway = kNoteSpotAwayYd;
        rules.tries = 16;
        rules.bestEffort = true;
        return DungeonKit::PickFloorSpot(me, &_shape, rules, MakeProbe());
    }

    DungeonKit::FloorProbe MakeProbe() const
    {
        DungeonKit::FloorProbe probe;
        probe.z = me->GetPositionZ();
        probe.zBand = 3.f;
        probe.probeUp = 3.f;
        probe.reachable = true;
        return probe;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HF5 The hearth, HF6 Drowsy, HF10 the moved hearth
    // ----------------------------------------------------------------------------------------------------------------

    // Lights the hearth (a moved one: 15..20 yd away, away from the old one, a 2 s glow before it counts).
    void PlaceHearth(bool moved)
    {
        std::optional<Vec2> old;
        if (_hearth.active)
            old = Vec2{ _hearth.at.GetPositionX(), _hearth.at.GetPositionY() };
        DungeonKit::FloorSpotRules const rules = HearthRules(DungeonKit::PlaneOf(me), moved, old);
        std::vector<Vec2> const fixed = HearthFallbacks(moved);
        Position at;
        if (std::optional<Position> const spot = DungeonKit::PickFloorSpot(me, &_shape, rules, MakeProbe(), fixed))
            at = *spot;
        else
            at = Position(fixed.front().x, fixed.front().y, me->GetPositionZ(), 0.f);
        RemoveHearth();

        uint32 const left = _set.EndMs() > _clockMs ? static_cast<uint32>(_set.EndMs() - _clockMs) : 0;
        Creature* stalker = me->SummonCreature(NPC_ST_HEARTH, at, TEMPSUMMON_TIMED_DESPAWN, left + 3000);
        if (!stalker)
            return;
        stalker->CastSpell(stalker, SPELL_HF_HEARTH_GLOW, true);
        uint32 const glow = moved ? kMovedGlowMs : 0;
        MechanicRef ref = Mechanic::Stack(me, stalker, kHearthRadius, Ms(glow));
        ref.Persistent(Ms(std::max<uint32>(left, 1000)), Ms(1000)).Eligible(NonTank()).Tag(TAG_HEARTH);
        _hearth.active = true;
        _hearth.stalker = stalker->GetGUID();
        _hearth.stack = ref.Handle();
        _hearth.at = at;
        _hearth.armedMs = _clockMs + glow;
        Log("hearth", Acore::StringFormat("moved={} at=({:.1f}, {:.1f}) dist={:.1f} glow={}ms", moved ? 1 : 0,
            at.GetPositionX(), at.GetPositionY(), me->GetExactDist2d(at.GetPositionX(), at.GetPositionY()), glow));
    }

    void RemoveHearth()
    {
        if (_hearth.stack)
            Mechanic::Cancel(me, _hearth.stack);
        if (Map* map = me->FindMap())
            if (Creature* stalker = map->GetCreature(_hearth.stalker))
                stalker->DespawnOrUnsummon();
        _hearth = Hearth();
    }

    void RunLullaby()
    {
        if (!_set.InSong() || _set.Current() != Song::Lullaby || !_hearth.active)
            return;
        if (_clockMs >= _drowsyNextMs)
        {
            DrowsyTick();
            _drowsyNextMs += kDrowsyTickMs;
            if (_drowsyNextMs < _clockMs)
                _drowsyNextMs = _clockMs + kDrowsyTickMs;
        }
        if (_clockMs >= _focusNextMs)
        {
            FocusRats();
            _focusNextMs = _clockMs + kRatFocusEveryMs;
        }
    }

    bool InsideHearth(Player const* player) const
    {
        if (!_hearth.active || _clockMs < _hearth.armedMs)
            return false;
        return InHearth(player->GetExactDist2d(_hearth.at.GetPositionX(), _hearth.at.GetPositionY()),
            player->GetPositionZ() - _hearth.at.GetPositionZ());
    }

    // HF6: every non-tank outside the hearth gains a Drowsy stack; at three, asleep for 2 s and the stacks clear.
    void DrowsyTick()
    {
        uint32 stacked = 0;
        uint32 slept = 0;
        for (Player* player : FightPlayers())
        {
            if (IsTank(player) || player->HasAura(SPELL_HF_ASLEEP) || InsideHearth(player))
                continue;
            DrowsyResult const step = DrowsyStep(DungeonKit::Stacks(player, SPELL_HF_DROWSY, me->GetGUID()));
            if (step.sleep)
            {
                player->RemoveAurasDueToSpell(SPELL_HF_DROWSY);
                me->AddAura(SPELL_HF_ASLEEP, player);
                ++slept;
            }
            else
            {
                DungeonKit::AddStacks(player, SPELL_HF_DROWSY, 1, me, kDrowsyToSleep);
                ++stacked;
            }
        }
        Log("drowsy", Acore::StringFormat("stacked {} asleep {}", stacked, slept));
    }

    // The rats go for the drowsy and the sleeping first.
    void FocusRats()
    {
        std::vector<Player*> const players = FightPlayers();
        for (RatRec const& rec : _rats)
        {
            Creature* rat = me->GetMap()->GetCreature(rec.guid);
            npc_st_gutter_rat* ai = RatAI(rat);
            if (!ai || ai->GetState() != npc_st_gutter_rat::State::Melee)
                continue;
            std::vector<FocusCandidate> candidates;
            for (Player const* player : players)
            {
                if (IsTank(player))
                    continue;
                candidates.push_back({ player->GetGUID().GetRawValue(), player->HasAura(SPELL_HF_ASLEEP),
                    DungeonKit::Stacks(player, SPELL_HF_DROWSY, me->GetGUID()), rat->GetExactDist2d(player) });
            }
            if (std::optional<uint64> const pick = LullabyFocus(candidates))
                ai->SetGUID(ObjectGuid(*pick), ACTION_RAT_FOCUS);
        }
    }

    void ClearSleepers()
    {
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    player->RemoveAurasDueToSpell(SPELL_HF_DROWSY);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HF7 The Piper's Tune: the rat volley
    // ----------------------------------------------------------------------------------------------------------------

    void RunPiper()
    {
        ReapLines();
        if (!_volley.Active() && _set.InSong() && _set.Current() == Song::Piper && _nextVolleyMs
            && _clockMs >= _nextVolleyMs)
            BeginVolley();
        if (_volley.Active())
            UpdateVolley();
    }

    // A rat that is back from its run takes its line off the floor (a line outlives its rat otherwise, and the rat is
    // already biting again). Runs every tick, volley or not: the last lines are still out when the volley ends.
    void ReapLines()
    {
        for (RatRec& rec : _rats)
        {
            if (!rec.line)
                continue;
            npc_st_gutter_rat* ai = RatAI(me->GetMap()->GetCreature(rec.guid));
            if (ai && ai->TakeRunFinished())
            {
                Mechanic::Cancel(me, rec.line);
                rec.line = MechanicHandle();
            }
        }
    }

    void BeginVolley()
    {
        ++_volleyNo;
        _nextVolleyMs = 0;
        _volley.Begin(_clockMs);
        _turn.Reset();
        for (RatRec& rec : _rats)
        {
            rec.launched = false;
            rec.assembleMs = 0;
            rec.gatherMs = 0;
        }
        Log("volley", Acore::StringFormat("#{} begins with {} rats", _volleyNo, CountRats()));
    }

    // One tick of the volley: gather the rats, launch a line every 0.5 s while one is staged, end when no rat is left
    // to launch.
    void UpdateVolley()
    {
        Position const gather = me->GetPosition();
        uint32 staged = 0;
        uint32 waiting = 0;
        npc_st_gutter_rat* next = nullptr;
        ObjectGuid nextGuid;
        for (RatRec& rec : _rats)
        {
            Creature* rat = me->GetMap()->GetCreature(rec.guid);
            npc_st_gutter_rat* ai = RatAI(rat);
            if (!ai)
                continue;
            if (rec.launched)
                continue;
            switch (ai->GetState())
            {
                case npc_st_gutter_rat::State::Melee:
                    // Not launched yet: a rat that arrived mid-volley joins the queue.
                    ai->Assemble(gather);
                    rec.assembleMs = _clockMs;
                    rec.gatherMs = _clockMs;
                    ++waiting;
                    break;
                case npc_st_gutter_rat::State::Assembling:
                    if (_clockMs - rec.assembleMs > kVolleyAssembleTimeoutMs)
                    {
                        // Never reached him (stuck, rooted): it fights on and sits this volley out.
                        rec.launched = true;
                        ai->Resume();
                        break;
                    }
                    if (_clockMs - rec.gatherMs >= 1000)
                    {
                        ai->Assemble(gather);       // he may have moved
                        rec.gatherMs = _clockMs;
                    }
                    ++waiting;
                    break;
                case npc_st_gutter_rat::State::Staged:
                    if (rat->GetExactDist2d(me) > kRatStagedYd + 4.f)
                    {
                        ai->Assemble(gather);       // he was moved away from where it waited
                        rec.assembleMs = _clockMs;
                        rec.gatherMs = _clockMs;
                        ++waiting;
                        break;
                    }
                    ++staged;
                    if (!next)
                    {
                        next = ai;
                        nextGuid = rec.guid;
                    }
                    break;
                default:
                    break;
            }
        }
        if (next && _volley.LineDue(_clockMs, staged))
            LaunchLine(nextGuid, *next);
        if (_volley.Done(staged, waiting) || !CanVolley())
            EndVolley(false);
    }

    // The volley also stops when nobody is left to aim at (a wipe: the boss evades through his own path).
    bool CanVolley() const
    {
        return me->IsAlive() && me->IsEngaged();
    }

    // One rat's line: from him toward a point 0..4 yd from the next player in turn, at most 30 yd, ending at his back
    // wall on that side; the rat runs it out and back after the marker's 2 s warning.
    void LaunchLine(ObjectGuid const& guid, npc_st_gutter_rat& ai)
    {
        std::vector<Player*> const players = FightPlayers();
        std::vector<uint64> ids;
        for (Player const* player : players)
            ids.push_back(player->GetGUID().GetRawValue());
        std::optional<uint64> const turn = _turn.Next(ids, [](uint32 n) { return urand(0, n - 1); });
        if (!turn)
            return;
        Player* target = nullptr;
        for (Player* player : players)
            if (player->GetGUID().GetRawValue() == *turn)
                target = player;
        if (!target)
            return;
        Vec2 const from = DungeonKit::PlaneOf(me);
        Vec2 const aim = AimPoint({ target->GetPositionX(), target->GetPositionY() }, Rand01(), Rand01());
        Vec2 const end = LaneEnd(from, aim, kRatLineCapYd);
        float const z = me->GetPositionZ();
        std::vector<DungeonKit::FloorPathPoint> const path = DungeonKit::FloorPathOnMap(me, from, end, z);
        if (!ai.Launch(path, kRatRunSpeed, kRatLineWarnMs))
            return;
        Position const fromPos(from.x, from.y, z, 0.f);
        Position const toPos(end.x, end.y, path.back().z, 0.f);
        MechanicRef ref = Mechanic::Line(me, fromPos, toPos, kRatLineWidth, Ms(kRatLineWarnMs));
        Creature* rat = me->GetMap()->GetCreature(guid);
        ref.Projectile(kRatLineSpeed).ProjectileUnit(rat).OutAndBack().Damage(kRatLinePct).TankDamage(kRatLinePct)
            .School(SPELL_SCHOOL_NORMAL).Spell(SPELL_HF_RAT_LINE).Weakened().Tag(TAG_RAT_LINE);
        for (RatRec& rec : _rats)
            if (rec.guid == guid)
            {
                rec.launched = true;
                rec.line = ref.Handle();
            }
        _volley.LineLaunched(_clockMs);
        Log("rat-line", Acore::StringFormat("#{} at {} len={:.1f} run={}ms", _volley.Launched(), target->GetName(),
            DungeonKit::Distance(from, end), RatRunMs(DungeonKit::Distance(from, end))));
    }

    // The volley is over; the second one is planned unless the song is almost done. `songEnded`: the song is over, the
    // rats that are still on their way go back to the fight.
    void EndVolley(bool songEnded)
    {
        if (!_volley.Active())
            return;
        uint32 const launched = _volley.Launched();
        uint64 const lastLine = _volley.LastLaunchAt();
        _volley.End();
        if (songEnded)
        {
            for (RatRec& rec : _rats)
            {
                Creature* rat = me->GetMap()->GetCreature(rec.guid);
                npc_st_gutter_rat* ai = RatAI(rat);
                if (ai && (ai->GetState() == npc_st_gutter_rat::State::Assembling
                    || ai->GetState() == npc_st_gutter_rat::State::Staged))
                    ai->Resume();
            }
        }
        else if (_volleyNo == 1 && _set.InSong())
        {
            if (std::optional<uint64> const second = SecondVolleyAt(lastLine, _set.EndMs()))
                _nextVolleyMs = *second;
        }
        Log("volley-end", Acore::StringFormat("#{} lines={} next={}", _volleyNo, launched, _nextVolleyMs));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HF8 Crescendo, HF9 / HF10 / HF11 / HF12 what a missed one does
    // ----------------------------------------------------------------------------------------------------------------

    void RunCrescendo()
    {
        if (!_crescendoAtMs || !_set.InSong() || _clockMs < _crescendoAtMs || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (StartCrescendo())
            _crescendoAtMs = 0;
        else
            _crescendoAtMs = _clockMs + 500;
    }

    bool StartCrescendo()
    {
        if (me->CastSpell(me, SPELL_HF_CRESCENDO, false) != SPELL_CAST_OK)
            return false;
        Talk(EMOTE_FORRESTEN_CRESCENDO);
        Log("crescendo", Acore::StringFormat("{} cast={}ms", SongName(_set.Current()), kCrescendoCastMs));
        return true;
    }

    // Not interrupted: the song's chaos, and on heroic four more rats.
    void CrescendoLanded()
    {
        if (!_set.InSong())
        {
            Log("crescendo-landed", "no song is playing");
            return;
        }
        _crescendoMissed = true;
        Song const song = _set.Current();
        switch (song)
        {
            case Song::Jig:
                _jigEveryMs = kJigDoubleBeatMs;
                _jigNextMs = std::min<uint64>(_jigNextMs, _clockMs + kJigDoubleBeatMs);
                break;
            case Song::Lullaby:
                PlaceHearth(true);
                break;
            case Song::Piper:
                BigLines();
                break;
        }
        if (uint32 const more = kMissedRats(_heroic))
            SummonRats(more, "missed crescendo");
        Log("crescendo-landed", Acore::StringFormat("{} heroic={}", SongName(song), _heroic ? 1 : 0));
    }

    // HF11: a 6 yd line from him through each non-tank, a 2 s marker, to the wall.
    void BigLines()
    {
        Vec2 const from = DungeonKit::PlaneOf(me);
        float const z = me->GetPositionZ();
        uint32 lines = 0;
        for (Player* player : FightPlayers())
        {
            if (IsTank(player))
                continue;
            Vec2 const end = LaneEnd(from, { player->GetPositionX(), player->GetPositionY() }, kBigLineCapYd);
            MechanicRef ref = Mechanic::Line(me, Position(from.x, from.y, z, 0.f), Position(end.x, end.y, z, 0.f),
                kBigLineWidth, Ms(kBigLineWarnMs));
            ref.Damage(kBigLinePct).TankDamage(kBigLinePct).School(SPELL_SCHOOL_NORMAL)
                .Spell(SPELL_HF_CRESCENDO_LINE).Weakened().Tag(TAG_CRESCENDO_LINE);
            Track(ref.Handle());
            ++lines;
        }
        Log("big-lines", Acore::StringFormat("{} lines, {:.0f} yd wide", lines, kBigLineWidth));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HF13 The bow, in the breaks only
    // ----------------------------------------------------------------------------------------------------------------

    void RunBreak()
    {
        if (!_set.InBreak() || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_clockMs >= _nextShootMs)
        {
            _nextShootMs = _clockMs + kShootEveryMs;
            Shoot(SPELL_SHOOT_FORRESTEN);
        }
        if (!_multiShotDone && _clockMs >= _multiShotMs)
        {
            _multiShotDone = true;
            Shoot(SPELL_MULTI_SHOT);
        }
    }

    // A 5..30 yd spell: his victim when he is not in melee reach of it, else a ranged player.
    void Shoot(uint32 spell)
    {
        Unit* target = me->GetVictim();
        if (!target || me->GetExactDist2d(target) < kShootMinYd)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.minRange = kShootMinYd;
            rule.maxRange = kShootMaxYd;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (target)
            me->CastSpell(target, spell, false);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST): kill order rats, then him; the Crescendo on the interrupt list; Plague Bite on the dispel list
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_ST_GUTTER_RAT, 2).AoeOk());
        d.interrupts.emplace_back(NPC_FORRESTEN, SPELL_HF_CRESCENDO, 3, Ms(kSongMs(_heroic) + kBreakMs(_heroic)));
        d.dispels.emplace_back(SPELL_HF_PLAGUE_BITE, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat forresten` entry points
    // ----------------------------------------------------------------------------------------------------------------

    bool HeroicMap() const { return _heroic; }

    // `.dbtest strat forresten heroic <0|1>`: the heroic form for the rest of the fight (the set list restarts).
    std::string TestHeroic(bool heroic)
    {
        if (!me->IsEngaged())
            return "He must be in combat.";
        _heroic = heroic;
        _set.Reset(heroic);
        _clockMs = 0;
        Describe();
        return {};
    }

    // An empty string when fired; otherwise why not.
    std::string TestSong(Song song)
    {
        if (!me->IsEngaged())
            return "He must be in combat (the songs pick among the players in the fight).";
        if (!_set.Force(song, _clockMs))
            return "A song is playing.";
        return {};
    }

    std::string TestRats(uint32 count)
    {
        if (!me->IsEngaged())
            return "He must be in combat.";
        SummonRats(count, "test");
        return {};
    }

    std::string TestBeat()
    {
        if (!me->IsEngaged())
            return "He must be in combat.";
        DropNotes();
        return {};
    }

    std::string TestVolley()
    {
        if (!me->IsEngaged())
            return "He must be in combat.";
        if (_volley.Active())
            return "A volley is running.";
        BeginVolley();
        return {};
    }

    std::string TestCrescendo()
    {
        if (!me->IsEngaged())
            return "He must be in combat.";
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return "He is casting; try again in a moment.";
        if (!StartCrescendo())
            return "The cast was refused (silenced, or still casting).";
        return {};
    }

    std::string TestHearth(bool moved)
    {
        if (!me->IsEngaged())
            return "He must be in combat.";
        PlaceHearth(moved);
        return {};
    }

    uint32 TestBite(Player* player, uint32 stacks)
    {
        uint32 now = 0;
        for (uint32 i = 0; i < stacks; ++i)
            now = DungeonKit::AddStacks(player, SPELL_HF_PLAGUE_BITE, 1, me, kBiteMaxStacks);
        return now;
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} song={} (next {} at {}s) rats={} hearth={} volley={}#{} "
            "crescendo at {}s", _clockMs / 1000, _heroic ? 1 : 0, _set.InSong() ? SongName(_set.Current()) : "none",
            SongName(_set.NextPlaying()), _set.NextStartMs() / 1000, CountRats(),
            _hearth.active ? "lit" : "none", _volley.Active() ? "on" : "off", _volleyNo, _crescendoAtMs / 1000);
    }

private:
    struct RatRec
    {
        ObjectGuid guid;
        bool launched = false;
        MechanicHandle line;
        uint64 assembleMs = 0;
        uint64 gatherMs = 0;
    };

    struct Hearth
    {
        bool active = false;
        ObjectGuid stalker;
        MechanicHandle stack;
        Position at;
        uint64 armedMs = 0;
    };

    static Vec2 ForrestenArenaCenter()
    {
        return { 3610.0f, -3500.0f };
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    void Log(char const* what, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, what, detail);
    }

    // The pull's state: nothing pending, no rat, no hearth, no Drowsy / sleep / dance on anyone (Reset, evade, death,
    // a new pull).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (RatRec const& rec : _rats)
            if (rec.line)
                Mechanic::Cancel(me, rec.line);
        _rats.clear();
        RemoveHearth();
        _volley.Reset();
        _turn.Reset();
        summons.DespawnAll();
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                {
                    player->RemoveAurasDueToSpell(SPELL_HF_DROWSY);
                    player->RemoveAurasDueToSpell(SPELL_HF_ASLEEP);
                    player->RemoveAurasDueToSpell(SPELL_HF_DANCE);
                    player->RemoveAurasDueToSpell(SPELL_HF_PLAGUE_BITE);
                }
        _set.Reset(false);
        _clockMs = 0;
        _crescendoAtMs = 0;
        _crescendoMissed = false;
        _jigNextMs = 0;
        _drowsyNextMs = 0;
        _focusNextMs = 0;
        _nextVolleyMs = 0;
        _volleyNo = 0;
        _nextShootMs = 0;
        _multiShotMs = 0;
        _multiShotDone = false;
        _arena.Reset();
    }

    static float constexpr kFightRangeYd = 60.f;

    DungeonKit::ArenaGuard _arena;
    DungeonKit::Arena _shape;
    SetList _set;
    Volley _volley;
    TurnOrder _turn;
    Hearth _hearth;
    std::vector<RatRec> _rats;
    std::vector<MechanicHandle> _live;
    bool _heroic = false;
    bool _crescendoMissed = false;
    bool _multiShotDone = false;
    uint32 _volleyNo = 0;
    uint32 _jigEveryMs = 2000;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _crescendoAtMs = 0;
    uint64 _jigNextMs = 0;
    uint64 _drowsyNextMs = 0;
    uint64 _focusNextMs = 0;
    uint64 _nextVolleyMs = 0;
    uint64 _nextShootMs = 0;
    uint64 _multiShotMs = 0;
};

namespace
{
    boss_hearthsinger_forresten_rework* FindForrestenAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_FORRESTEN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_hearthsinger_forresten_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Forresten is not running boss_hearthsinger_forresten_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Done(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Forresten: {} fired.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_FORRESTEN, BOSS_FORRESTEN);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Forresten: {}", ai->TestState());
        return true;
    }

    bool HandleHeroic(ChatHandler* handler, uint32 heroic)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        return ai && Done(handler, ai->TestHeroic(heroic != 0), heroic ? "heroic form (set list restarted)"
            : "normal form (set list restarted)");
    }

    bool HandleJig(ChatHandler* handler)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        return ai && Done(handler, ai->TestSong(Song::Jig), "The Jig (HF4: notes every beat)");
    }

    bool HandleLullaby(ChatHandler* handler)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        return ai && Done(handler, ai->TestSong(Song::Lullaby), "The Lullaby (HF5, HF6: the hearth and Drowsy)");
    }

    bool HandlePiper(ChatHandler* handler)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        return ai && Done(handler, ai->TestSong(Song::Piper), "The Piper's Tune (HF7: the rat volley)");
    }

    bool HandleBeat(ChatHandler* handler)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        return ai && Done(handler, ai->TestBeat(), "one beat of notes (HF4)");
    }

    bool HandleRats(ChatHandler* handler, Optional<uint32> count)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        return ai && Done(handler, ai->TestRats(count ? *count : 6), "Gutter Rats (HF2)");
    }

    bool HandleVolley(ChatHandler* handler)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        return ai && Done(handler, ai->TestVolley(), "a rat volley now (HF7)");
    }

    bool HandleCrescendo(ChatHandler* handler)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        return ai && Done(handler, ai->TestCrescendo(), "Crescendo (HF8; the song's chaos if it is not kicked)");
    }

    bool HandleHearth(ChatHandler* handler, Optional<uint32> moved)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        return ai && Done(handler, ai->TestHearth(moved && *moved != 0), "the hearth (HF5; 1 = the moved one, HF10)");
    }

    // `.dbtest strat forresten bite <n>`: n stacks of Plague Bite on the selected player (yourself when none).
    bool HandleBite(ChatHandler* handler, Optional<uint32> stacks)
    {
        boss_hearthsinger_forresten_rework* ai = FindForrestenAI(handler);
        if (!ai)
            return false;
        Player* player = handler->getSelectedPlayerOrSelf();
        if (!player)
            return false;
        uint32 const now = ai->TestBite(player, stacks ? *stacks : 1);
        handler->PSendSysMessage("Forresten: {} now has {} stack(s) of Plague Bite.", player->GetName(), now);
        return true;
    }

    ChatCommandTable const& ForrestenTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "heroic",     HandleHeroic,     SEC_GAMEMASTER, Console::No },
            { "jig",        HandleJig,        SEC_GAMEMASTER, Console::No },
            { "lullaby",    HandleLullaby,    SEC_GAMEMASTER, Console::No },
            { "piper",      HandlePiper,      SEC_GAMEMASTER, Console::No },
            { "beat",       HandleBeat,       SEC_GAMEMASTER, Console::No },
            { "rats",       HandleRats,       SEC_GAMEMASTER, Console::No },
            { "volley",     HandleVolley,     SEC_GAMEMASTER, Console::No },
            { "crescendo",  HandleCrescendo,  SEC_GAMEMASTER, Console::No },
            { "hearth",     HandleHearth,     SEC_GAMEMASTER, Console::No },
            { "bite",       HandleBite,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_hearthsinger_forresten_rework()
{
    RegisterDungeonReworkCreatureAI(boss_hearthsinger_forresten_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_gutter_rat, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_hearth_stalker, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_st_forresten_dance);
    StratTest::RegisterBoss("forresten", ForrestenTestCommands());
}
