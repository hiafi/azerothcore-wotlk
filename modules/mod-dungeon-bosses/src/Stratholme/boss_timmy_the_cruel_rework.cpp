/*
 * mod-dungeon-bosses, Stratholme S3: Timmy the Cruel (10808), "a cruel child who wants to play". Build spec ST
 * 1035-1090 (docs/dungeons/stratholme-rework.md; design ST 886-1034), handoff section 3.4 rows TC and 3.5 row S3.
 * Replaces the stock SmartAI (10808 and its emerge actionlist 1080800; the stock gate, emerge and patrol are kept here
 * in C++): the creature template is rebound by apps/dbc-tools source/npcs/stratholme/timmy_the_cruel.py, the SmartAI
 * rows and their gate `conditions` are dropped by rev_timmy_the_cruel_stratholme.sql. Pure rules: TimmyLogic.h.
 *
 *   Emerge        buried (invisible, immune) until no Crimson Guardsman, Conjuror, Initiate or Gallant lives within
 *                 70 yd (checked every 10 s out of combat, the stock conditions); then emote state 449 for 3.5 s and
 *                 the stock patrol path 2472270
 *   TC1  Playtime Freeze Tag at 8 s, then every 40 s; a game slot every 15 s from 20 s: Guess Who, Jump Rope, Patty
 *                 Cake in turn (heroic: two at once, GW+JR, PC+GW, JR+PC; two casts play back to back, Patty Cake
 *                 first). Each game opens with a yell or an emote. Timers only, never health
 *   TC2  Tag      a 15 s round: every 3 s a random unfrozen player (tank included) is tagged: a 6 yd marker for 2 s
 *                 (a telegraph-only RunOut: the bots spread from it), then the burst
 *   TC3  Frozen   the tagged player and everyone the burst caught: -70% speed, 2% Frost a second; they still act
 *   TC4  Thaw     a 3 yd telegraph-only Soak anchored on each frozen player, for unfrozen players only (one bot claims
 *                 it); anyone eligible inside thaws them at once
 *   TC5  Shatter  the round's end (15 s, or everyone frozen at once): everyone still frozen, 30% Frost + Weakened
 *                 (RegistryHit)
 *   TC6  Patty    a 4 s channel, a clap a second over the whole square, 10% (heroic 20%) Physical; any kick ends it
 *                 (the interrupt list, top priority)
 *   TC7  Guess    3 playmates (heroic 4) burst up at the square's edges; they go for frozen players first
 *   TC8  Rope     three 2 s skips back to back, each its own cast bar; one registry Jump per skip over the whole
 *   TC9  Trip     square: whoever is on the ground when it ends is tripped (25% + Weakened, 1 s knockdown). The Jump
 *                 kind decides who was in the air (a client's jump, or a bot's hop: never a bare IsFalling test)
 *   TC10 Stock    melee, Thrash 12787 (his creature_addon aura), Ravenous Claw 17470 every 10-15 s, Enrage 8599 once
 *                 at 50% (the purge list)
 *   Arena         StratholmeRework::LeashOptions on TimmyArena() (no grips; holds at the edge)
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one). Every firing logs
 * one INFO line "strat timmy <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TimmyLogic.h"
#include <algorithm>
#include <deque>
#include <list>
#include <map>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratTimmy;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "timmy";
    float constexpr kFightRangeYd = 100.f;
    Vec2 constexpr kSquareCenter{ 3668.0f, -3176.0f };     // TimmyArena()'s center

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    bool IsFrozen(Unit const* unit)
    {
        return unit && unit->HasAura(SPELL_TC_FROZEN);
    }

    // Every living player of the fight: alive, in the world, not a GM, within reach of the square.
    std::vector<Player*> SquarePlayers(Creature const* me)
    {
        std::vector<Player*> out;
        Map* map = me->FindMap();
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsAlive() && player->IsInWorld() && !player->IsGameMaster()
                && player->GetExactDist2d(kSquareCenter.x, kSquareCenter.y) <= kFightRangeYd)
                out.push_back(player);
        }
        return out;
    }
}

// ====================================================================================================================
// Playmate 300604 (TC7): a smaller Timmy. Bursts up with his emerge emote, yells his name, then plays rough with the
// frozen players first.
// ====================================================================================================================
struct npc_st_playmate : public ScriptedAI
{
    explicit npc_st_playmate(Creature* creature) : ScriptedAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        _emergeLeftMs = kPlaymateEmergeMs;
        _focusLeftMs = 0;
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->StopMoving();
        me->SetEmoteState(static_cast<Emote>(kEmoteEmerge));
        Talk(YELL_PLAYMATE_TIMMY);
    }

    void UpdateAI(uint32 diff) override
    {
        if (_emergeLeftMs)
        {
            if (_emergeLeftMs > diff)
            {
                _emergeLeftMs -= diff;
                return;
            }
            _emergeLeftMs = 0;
            me->SetEmoteState(EMOTE_ONESHOT_NONE);
            me->SetReactState(REACT_AGGRESSIVE);
            DoZoneInCombat();
            Focus(true);
        }
        if (!UpdateVictim())
            return;
        if (_focusLeftMs <= diff)
        {
            _focusLeftMs = kPlaymateFocusMs;
            Focus(false);
        }
        else
            _focusLeftMs -= diff;
        DoMeleeAttackIfReady();
    }

private:
    // TC7: the nearest frozen player; nobody frozen: keep the victim (or, first time, a random player).
    void Focus(bool first)
    {
        std::vector<Player*> const players = SquarePlayers(me);
        std::vector<FocusCandidate> candidates;
        for (Player const* player : players)
            candidates.push_back({ player->GetGUID().GetRawValue(), IsFrozen(player), me->GetExactDist2d(player) });
        Player* pick = nullptr;
        if (std::optional<uint64> const focus = PlaymateFocus(candidates))
            pick = ObjectAccessor::GetPlayer(*me, ObjectGuid(*focus));
        else if ((first || !me->GetVictim()) && !players.empty())
            pick = players[urand(0, static_cast<uint32>(players.size()) - 1)];
        if (!pick || me->GetVictim() == pick)
            return;
        me->GetThreatMgr().ResetAllThreat();
        DoAddThreat(pick, 1000.f);
        AttackStart(pick);
    }

    uint32 _emergeLeftMs = 0;
    uint32 _focusLeftMs = 0;
};

// TC6 a clap: everyone on the square (TimmyArena), 10% (heroic 20%) of the reference row, the tank row on the tank.
class spell_st_timmy_clap : public SpellScript
{
    PrepareSpellScript(spell_st_timmy_clap);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Arena const arena = TimmyArena();
        targets.remove_if([&arena](WorldObject* o)
        {
            return !o || !arena.Contains(DungeonKit::PlaneOf(o), o->GetPositionZ());
        });
    }

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), kClapPct(IsHeroicMap(caster)))));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_st_timmy_clap::FilterTargets, EFFECT_0,
            TARGET_UNIT_SRC_AREA_ENEMY);
        OnEffectLaunchTarget += SpellEffectFn(spell_st_timmy_clap::SetDamage, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// ====================================================================================================================
// Timmy the Cruel 10808
// ====================================================================================================================
struct boss_timmy_the_cruel_rework : public BossAI
{
    explicit boss_timmy_the_cruel_rework(Creature* creature)
        : BossAI(creature, BOSS_TIMMY), _arena(TimmyArena(), LeashOptions(kBossLogName)) { }

    // The stock "On Respawn" rows: he spawns buried (invisible, immune to players and creatures) until his gate opens.
    void InitializeAI() override
    {
        BossAI::InitializeAI();
        if (me->IsAlive() && !_emerged)
            Bury();
    }

    void JustRespawned() override
    {
        _emerged = false;
        BossAI::JustRespawned();
        Bury();
    }

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
        options.bossStateId = BOSS_TIMMY;
        Mechanic::BeginEncounter(me, options);

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        _emergeLeftMs = 0;
        me->SetEmoteState(EMOTE_ONESHOT_NONE);
        if (!me->HasAura(SPELL_THRASH))
            me->AddAura(SPELL_THRASH, me);      // his creature_addon aura (a GM pull of a fresh spawn has it too)
        _nextClawMs = urand(kClawMinMs, kClawMaxMs);
        Describe();
        _arena.Engage(me);
        Talk(YELL_TIMMY_AGGRO);
        Log("engage", Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0,
            me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    // Back at his spawn after a wipe: on with the patrol (he stays up; only a respawn buries him again).
    void JustReachedHome() override
    {
        BossAI::JustReachedHome();
        if (_emerged)
            StartPatrol();
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);   // DONE; the playmates despawn
        Cleanup();
        Talk(YELL_TIMMY_DEATH);
        Log("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    void JustSummoned(Creature* summon) override
    {
        BossAI::JustSummoned(summon);
        if (summon->GetEntry() == NPC_ST_PLAYMATE)
            _playmates.push_back(summon->GetGUID());
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        ForgetPlaymate(summon->GetGUID());
        BossAI::SummonedCreatureDespawn(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        ForgetPlaymate(summon->GetGUID());
    }

    // TC6: a kick (or anything else) stopped the claps; the full channel is OnChannelFinished.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_TC_PATTY_CAKE && _patty.active)
            _patty.kicked = true;
    }

    void OnChannelFinished(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_TC_PATTY_CAKE && _patty.active)
            _patty.finished = true;
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
        {
            UpdateBuried(diff);
            return;
        }

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        FlushCancels();
        RunPlaytime();
        RunFreezeTag();
        RunCasts();
        RunStockKit();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The emerge (the stock SmartAI's gate, actionlist and path)
    // ----------------------------------------------------------------------------------------------------------------

    void Bury()
    {
        _buried = true;
        _emergeLeftMs = 0;
        _gateCheckLeftMs = kGateCheckMs;
        me->SetVisible(false);
        me->SetImmuneToAll(true);
    }

    // The stock conditions: no living Crimson Guardsman, Conjuror, Initiate or Gallant within 70 yd of him.
    bool GateOpen() const
    {
        for (uint32 entry : kGateEntries)
            if (me->FindNearestCreature(entry, kGateRangeYd, true))
                return false;
        return true;
    }

    void Emerge(char const* why)
    {
        _buried = false;
        _emerged = true;
        me->SetVisible(true);
        me->SetImmuneToAll(false);
        me->SetEmoteState(static_cast<Emote>(kEmoteEmerge));
        _emergeLeftMs = kEmergeMs;
        Log("emerge", why);
    }

    void StartPatrol()
    {
        me->LoadPath(kPatrolPath);
        me->GetMotionMaster()->MoveWaypoint(kPatrolPath, true);
    }

    // Out of combat: the gate check every 10 s while buried; the emerge's 3.5 s, then the path.
    void UpdateBuried(uint32 diff)
    {
        if (!me->IsAlive())
            return;
        if (_emergeLeftMs)
        {
            if (_emergeLeftMs > diff)
            {
                _emergeLeftMs -= diff;
                return;
            }
            _emergeLeftMs = 0;
            me->SetEmoteState(EMOTE_ONESHOT_NONE);
            StartPatrol();
            return;
        }
        if (!_buried)
            return;
        if (_gateCheckLeftMs > diff)
        {
            _gateCheckLeftMs -= diff;
            return;
        }
        _gateCheckLeftMs = kGateCheckMs;
        if (GateOpen())
            Emerge("the Crimson troops are gone");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TC1 Playtime
    // ----------------------------------------------------------------------------------------------------------------

    void RunPlaytime()
    {
        for (Playtime::Event const& event : _playtime.Advance(_clockMs))
        {
            if (event.kind == Playtime::Event::Kind::FreezeTag)
                StartRound(event.index);
            else
                StartSlot(event.index);
        }
    }

    void StartSlot(uint32 index)
    {
        SlotGames const slot = GamesOfSlot(index, _heroic);
        if (HasGame(slot, Game::GuessWho))
            GuessWho();
        for (Game game : CastOrder(slot))
        {
            _castQueue.push_back(game);
            if (game == Game::PattyCake)
                Mechanic::NoteNextCastIn(me, SPELL_TC_PATTY_CAKE, Ms(0));
        }
        Log("slot", Acore::StringFormat("#{} heroic={} games={}{}{} queued={}", index, _heroic ? 1 : 0,
            GameName(slot.games[0]), slot.count > 1 ? "+" : "", slot.count > 1 ? GameName(slot.games[1]) : "",
            _castQueue.size()));
    }

    // The casting games, one at a time.
    void RunCasts()
    {
        if (_rope.active)
            UpdateRope();
        if (_patty.active)
            UpdatePatty();
        if (_rope.active || _patty.active || _castQueue.empty() || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        Game const next = _castQueue.front();
        bool const started = next == Game::PattyCake ? StartPattyCake() : StartRope(_heroic && kHeroicDoubleDutch);
        if (started)
            _castQueue.pop_front();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TC2-TC5 Freeze Tag
    // ----------------------------------------------------------------------------------------------------------------

    void StartRound(uint32 index)
    {
        if (_round.Active())
            EndRound("a new round");
        _round.Begin(_clockMs);
        Talk(YELL_TIMMY_TAG);
        Log("freeze-tag", Acore::StringFormat("round #{} ends in {}s", index, kRoundMs / 1000));
    }

    void RunFreezeTag()
    {
        if (!_round.Active())
            return;
        if (_round.TagDue(_clockMs))
            Tag();
        uint32 alive = 0;
        uint32 frozen = 0;
        for (Player const* player : SquarePlayers(me))
        {
            ++alive;
            frozen += IsFrozen(player) ? 1 : 0;
        }
        if (_round.Over(_clockMs, alive, frozen))
            EndRound(_clockMs < _round.EndsAt() ? "gotcha: everyone is frozen" : "time");
    }

    // TC2: a random unfrozen player, the tank too: "Tag!" for 2 s and a 6 yd marker, then the burst.
    void Tag()
    {
        std::vector<TagCandidate> candidates;
        for (Player const* player : SquarePlayers(me))
            candidates.push_back({ player->GetGUID().GetRawValue(), IsFrozen(player) });
        std::optional<uint64> const pick = PickTag(candidates, [](uint32 n) { return urand(0, n - 1); });
        Player* tagged = pick ? ObjectAccessor::GetPlayer(*me, ObjectGuid(*pick)) : nullptr;
        if (!tagged)
        {
            Log("tag", "nobody left to tag");
            return;
        }
        me->AddAura(SPELL_TC_TAGGED, tagged);
        MechanicRef ref = Mechanic::RunOut(me, tagged, kTagRadius, Ms(kTagWarnMs));
        ref.Color(BossMechanics::Color::Teal).Tag(TAG_TAG);
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        ObjectGuid const taggedGuid = tagged->GetGUID();
        uint32 const gen = _generation;
        ref.OnResolve([map, bossGuid, gen, taggedGuid](BossMechanics::ResolveResult const& r)
        {
            if (boss_timmy_the_cruel_rework* ai = AIOf(map, bossGuid, gen))
                ai->Burst(taggedGuid, r.hits);
        });
        Track(_tagMarks, ref.Handle());
        Log("tag", Acore::StringFormat("#{} {} frozen={}", _round.Tags(), tagged->GetName(),
            std::count_if(candidates.begin(), candidates.end(), [](TagCandidate const& c) { return c.frozen; })));
    }

    // TC3: the burst freezes the tagged player and everyone its circle caught.
    void Burst(ObjectGuid taggedGuid, std::vector<ObjectGuid> const& inside)
    {
        if (!_round.Active())
            return;     // the round ended (Gotcha) before this marker resolved
        Player* tagged = ObjectAccessor::GetPlayer(*me, taggedGuid);
        std::optional<uint64> taggedId;
        if (tagged && tagged->IsAlive())
            taggedId = taggedGuid.GetRawValue();
        std::vector<uint64> insideIds;
        for (ObjectGuid const& guid : inside)
            insideIds.push_back(guid.GetRawValue());
        uint32 count = 0;
        for (uint64 id : BurstVictims(taggedId, insideIds))
        {
            Player* player = ObjectAccessor::GetPlayer(*me, ObjectGuid(id));
            if (!player || !player->IsAlive() || player->IsGameMaster())
                continue;
            Freeze(player);
            ++count;
        }
        Log("burst", Acore::StringFormat("tagged={} frozen={}", tagged ? tagged->GetName() : "gone", count));
    }

    // TC3 / TC4: Frozen, and the touch that thaws it (a lasting 3 yd Soak on the player for the unfrozen).
    void Freeze(Player* player)
    {
        me->AddAura(SPELL_TC_FROZEN, player);
        if (_thaws.count(player->GetGUID()))
            return;
        uint64 const left = _round.EndsAt() > _clockMs ? _round.EndsAt() - _clockMs : 0;
        MechanicRef ref = Mechanic::Soak(me, player, kThawRadius, 1, Ms(0));
        BossMechanics::Eligibility unfrozen;
        unfrozen.auraSpell = SPELL_TC_FROZEN;
        unfrozen.maxStacks = 0;
        ref.AnchorOn(player).Persistent(Ms(static_cast<uint32>(left) + 500), Ms(kThawTickMs)).Eligible(unfrozen)
            .OneClaimPerBot().Tag(TAG_THAW);
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        ObjectGuid const frozenGuid = player->GetGUID();
        uint32 const gen = _generation;
        ref.OnResolve([map, bossGuid, gen, frozenGuid](BossMechanics::ResolveResult const& r)
        {
            if (r.hits.empty())
                return;
            if (boss_timmy_the_cruel_rework* ai = AIOf(map, bossGuid, gen))
                ai->Thaw(frozenGuid, r.hits.front());
        });
        _thaws[frozenGuid] = ref.Handle();
    }

    // TC4: an unfrozen player touched them. The soak is cancelled on the next tick (never inside its own resolve).
    void Thaw(ObjectGuid frozenGuid, ObjectGuid thawerGuid)
    {
        Player* player = ObjectAccessor::GetPlayer(*me, frozenGuid);
        if (player && IsFrozen(player))
        {
            player->RemoveAurasDueToSpell(SPELL_TC_FROZEN);
            Player const* thawer = ObjectAccessor::GetPlayer(*me, thawerGuid);
            Log("thaw", Acore::StringFormat("{} by {}", player->GetName(), thawer ? thawer->GetName() : "?"));
        }
        auto it = _thaws.find(frozenGuid);
        if (it != _thaws.end())
        {
            _cancels.push_back(it->second);
            _thaws.erase(it);
        }
    }

    // TC5 Gotcha: everyone still frozen shatters (30% Frost + Weakened); the round's markers and touches go.
    void EndRound(char const* why)
    {
        GuidSet frozen;
        for (Player const* player : SquarePlayers(me))
            if (IsFrozen(player))
                frozen.insert(player->GetGUID());
        if (!frozen.empty())
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = kShatterPct;
            spec.tankPct = kShatterPct;
            spec.school = SPELL_SCHOOL_FROST;
            spec.spellId = SPELL_TC_SHATTER;
            spec.weakened = true;
            spec.tag = TAG_SHATTER;
            DungeonKit::RegistryHit(me, frozen, spec);
        }
        _round.End();
        for (MechanicHandle const& handle : _tagMarks)
            Mechanic::Cancel(me, handle);
        _tagMarks.clear();
        for (auto const& [guid, handle] : _thaws)
            Mechanic::Cancel(me, handle);
        _thaws.clear();
        ClearPlayerAuras(false);
        Log("shatter", Acore::StringFormat("{}: shattered={}", why, frozen.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TC6 Patty Cake
    // ----------------------------------------------------------------------------------------------------------------

    bool StartPattyCake()
    {
        if (me->CastSpell(me, SPELL_TC_PATTY_CAKE, false) != SPELL_CAST_OK)
            return false;
        Talk(EMOTE_TIMMY_CLAP);
        _patty = PattyState();
        _patty.active = true;
        _patty.startedMs = _clockMs;
        Log("patty-cake", Acore::StringFormat("heroic={} claps={} x {:.0f}%", _heroic ? 1 : 0, kClaps,
            kClapPct(IsHeroicMap(me))));
        return true;
    }

    void UpdatePatty()
    {
        bool const channeling = me->FindCurrentSpellBySpellId(SPELL_TC_PATTY_CAKE) != nullptr;
        if (channeling && !_patty.kicked && !_patty.finished)
            return;
        if (!_patty.kicked && !_patty.finished && _clockMs < _patty.startedMs + 250)
            return;     // the channel has not taken yet
        uint64 const ran = _clockMs - _patty.startedMs;
        Log(_patty.kicked ? "patty-cake-kicked" : "patty-cake-done", Acore::StringFormat("after {}ms (claps ~{})",
            ran, std::min<uint64>(kClaps, ran / kClapEveryMs)));
        _patty = PattyState();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TC7 Guess Who
    // ----------------------------------------------------------------------------------------------------------------

    void GuessWho()
    {
        Talk(YELL_TIMMY_TIMMIES);
        uint32 const count = PlaymatesToSummon(_heroic, static_cast<uint32>(_playmates.size()));
        std::vector<Vec2> const spots = PlaymateSpots(_heroic);
        std::vector<Position> at;
        for (uint32 i = 0; i < count; ++i)
        {
            Vec2 const& p = spots[i % spots.size()];
            float z = me->GetMapHeight(p.x, p.y, kRopeZ + 5.f);
            if (z <= INVALID_HEIGHT)
                z = me->GetPositionZ();
            at.emplace_back(p.x, p.y, z, DungeonKit::BearingTo(p, kSquareCenter));
        }
        std::vector<Creature*> const wave = DungeonKit::SummonWave(me, NPC_ST_PLAYMATE, at, summons);
        Log("guess-who", Acore::StringFormat("heroic={} playmates {} of {} summoned, alive {}", _heroic ? 1 : 0,
            wave.size(), count, _playmates.size()));
    }

    void ForgetPlaymate(ObjectGuid const& guid)
    {
        _playmates.erase(std::remove(_playmates.begin(), _playmates.end(), guid), _playmates.end());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TC8 / TC9 Jump Rope
    // ----------------------------------------------------------------------------------------------------------------

    bool StartRope(bool doubleDutch)
    {
        _rope = RopeState();
        _rope.active = true;
        _rope.skips = SkipsOf(doubleDutch);
        _rope.nextMs = _clockMs;
        Talk(YELL_TIMMY_JUMP);
        Talk(EMOTE_TIMMY_JUMP_ROPE);
        Log("jump-rope", Acore::StringFormat("skips={} double-dutch={} total={}ms", _rope.skips.size(),
            doubleDutch ? 1 : 0, RopeMs(doubleDutch)));
        UpdateRope();
        return true;
    }

    // One skip after the other: each its own cast bar, one registry Jump per cast (warn = the cast time).
    void UpdateRope()
    {
        if (_rope.index >= _rope.skips.size())
        {
            if (_clockMs >= _rope.nextMs)
                _rope = RopeState();
            return;
        }
        if (_clockMs < _rope.nextMs || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        uint32 const castMs = _rope.skips[_rope.index];
        if (me->CastSpell(me, SkipSpell(castMs), false) != SPELL_CAST_OK)
        {
            _rope.nextMs = _clockMs + 250;      // try again shortly
            return;
        }
        RegisterSweep(castMs, _rope.index);
        ++_rope.index;
        _rope.nextMs = _clockMs + castMs;
    }

    void RegisterSweep(uint32 castMs, uint32 skip)
    {
        Position const center(kSquareCenter.x, kSquareCenter.y, kRopeZ, 0.f);
        MechanicRef ref = Mechanic::Jump(me, center, kRopeRadius, Ms(castMs));
        ref.Damage(kTripPct).TankDamage(kTripPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_TC_TRIP).Weakened()
            .Rider(SPELL_TC_TRIPPED).ZTolerance(kRopeZTolerance).Color(BossMechanics::Color::Yellow)
            .Tag(TAG_JUMP_ROPE);
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        ref.OnResolve([map, bossGuid, gen, skip](BossMechanics::ResolveResult const& r)
        {
            if (boss_timmy_the_cruel_rework* ai = AIOf(map, bossGuid, gen))
                ai->Log("trip", Acore::StringFormat("skip #{} tripped={} in the air={}", skip + 1, r.hits.size(),
                    r.cleared.size()));
        });
        Track(_sweeps, ref.Handle());
        Log("skip", Acore::StringFormat("#{} cast={}ms", skip + 1, castMs));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TC10 the stock kit
    // ----------------------------------------------------------------------------------------------------------------

    void RunStockKit()
    {
        if (!_enraged && me->HealthBelowPct(static_cast<int32>(kEnrageAtPct)))
        {
            _enraged = true;
            DoCastSelf(SPELL_ENRAGE_TIMMY, true);
            Log("enrage", "50%");
        }
        if (_clockMs >= _nextClawMs && !me->HasUnitState(UNIT_STATE_CASTING) && !_rope.active && !_patty.active)
        {
            if (Unit* victim = me->GetVictim())
                if (me->CastSpell(victim, SPELL_RAVENOUS_CLAW, false) == SPELL_CAST_OK)
                    _nextClawMs = _clockMs + urand(kClawMinMs, kClawMaxMs);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST): kill order playmates, then him; Patty Cake on the interrupt list (top priority, expected on
    // heroic); Enrage on the purge list (a reward)
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_ST_PLAYMATE, 2).AoeOk());
        d.interrupts.emplace_back(NPC_TIMMY, SPELL_TC_PATTY_CAKE, 3, Ms(_heroic ? kSlotEveryMs : 3 * kSlotEveryMs));
        d.purges.emplace_back(NPC_TIMMY, SPELL_ENRAGE_TIMMY, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat timmy` entry points
    // ----------------------------------------------------------------------------------------------------------------

    std::string TestHeroic(bool heroic)
    {
        if (!me->IsEngaged())
            return "He must be in combat.";
        _heroic = heroic;
        _playtime.Reset();
        _clockMs = 0;
        Describe();
        return {};
    }

    std::string TestEmerge()
    {
        if (me->IsEngaged())
            return "He is in combat.";
        if (!_buried)
            return "He is already up.";
        Emerge("test");
        return {};
    }

    std::string TestRound()
    {
        if (!me->IsEngaged())
            return "He must be in combat (the tags pick among the players in the fight).";
        StartRound(_playtime.Rounds());
        return {};
    }

    std::string TestGotcha()
    {
        if (!_round.Active())
            return "No Freeze Tag round is running.";
        EndRound("test");
        return {};
    }

    std::string TestGame(Game game, bool doubleDutch = false)
    {
        if (!me->IsEngaged())
            return "He must be in combat.";
        if (game == Game::GuessWho)
        {
            GuessWho();
            return {};
        }
        if (_rope.active || _patty.active || me->HasUnitState(UNIT_STATE_CASTING))
            return "He is busy with another game; try again in a moment.";
        bool const started = game == Game::PattyCake ? StartPattyCake() : StartRope(doubleDutch);
        return started ? std::string() : std::string("The cast was refused.");
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} buried={} round={} (tags {}, next at {}s) slot next at {}s "
            "(#{}) queue={} rope={} patty={} playmates={} enraged={}", _clockMs / 1000, _heroic ? 1 : 0,
            _buried ? 1 : 0, _round.Active() ? "on" : "off", _round.Tags(), _playtime.NextRoundAt() / 1000,
            _playtime.NextSlotAt() / 1000, _playtime.Slots(), _castQueue.size(), _rope.active ? "on" : "off",
            _patty.active ? "on" : "off", _playmates.size(), _enraged ? 1 : 0);
    }

    void Log(char const* what, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, what, detail);
    }

private:
    struct RopeState
    {
        bool active = false;
        std::vector<uint32> skips;
        std::size_t index = 0;
        uint64 nextMs = 0;
    };

    struct PattyState
    {
        bool active = false;
        bool kicked = false;
        bool finished = false;
        uint64 startedMs = 0;
    };

    static boss_timmy_the_cruel_rework* AIOf(Map* map, ObjectGuid bossGuid, uint32 gen)
    {
        Creature* boss = map ? map->GetCreature(bossGuid) : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        auto* ai = dynamic_cast<boss_timmy_the_cruel_rework*>(boss->AI());
        return ai && ai->_generation == gen ? ai : nullptr;
    }

    // Keeps a handle for the cleanup (`list`: the round's tag markers, or the rope's sweeps).
    static void Track(std::vector<MechanicHandle>& list, MechanicHandle handle)
    {
        if (!handle)
            return;
        list.push_back(handle);
        if (list.size() > 64)           // the oldest ones resolved long ago
            list.erase(list.begin(), list.begin() + 32);
    }

    void FlushCancels()
    {
        for (MechanicHandle const& handle : _cancels)
            Mechanic::Cancel(me, handle);
        _cancels.clear();
    }

    // Frozen and "Tag!" off every player (`all`: Tripped too).
    void ClearPlayerAuras(bool all)
    {
        Map* map = me->FindMap();
        if (!map)
            return;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
            {
                player->RemoveAurasDueToSpell(SPELL_TC_FROZEN);
                player->RemoveAurasDueToSpell(SPELL_TC_TAGGED);
                if (all)
                    player->RemoveAurasDueToSpell(SPELL_TC_TRIPPED);
            }
    }

    // The pull's state: nothing pending, no playmate, no game, nobody frozen (Reset, evade, death, a new pull).
    void Cleanup()
    {
        ++_generation;      // callbacks of an older pull stop
        for (MechanicHandle const& handle : _tagMarks)
            Mechanic::Cancel(me, handle);
        _tagMarks.clear();
        for (MechanicHandle const& handle : _sweeps)
            Mechanic::Cancel(me, handle);
        _sweeps.clear();
        for (auto const& [guid, handle] : _thaws)
            Mechanic::Cancel(me, handle);
        _thaws.clear();
        FlushCancels();
        _round.End();
        _playtime.Reset();
        _castQueue.clear();
        _rope = RopeState();
        _patty = PattyState();
        summons.DespawnAll();
        _playmates.clear();
        ClearPlayerAuras(true);
        _clockMs = 0;
        _nextClawMs = 0;
        _enraged = false;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    Playtime _playtime;
    FreezeRound _round;
    std::deque<Game> _castQueue;
    RopeState _rope;
    PattyState _patty;
    std::map<ObjectGuid, MechanicHandle> _thaws;    // frozen player -> its thaw Soak
    std::vector<MechanicHandle> _tagMarks;          // the round's tag markers
    std::vector<MechanicHandle> _sweeps;            // the rope's sweeps (Jump)
    std::vector<MechanicHandle> _cancels;           // thaw Soaks to cancel next tick
    std::vector<ObjectGuid> _playmates;
    bool _heroic = false;
    bool _enraged = false;
    bool _buried = false;
    bool _emerged = false;
    uint32 _generation = 0;
    uint32 _gateCheckLeftMs = kGateCheckMs;
    uint32 _emergeLeftMs = 0;
    uint64 _clockMs = 0;                            // ms since the pull: every timer of the fight
    uint64 _nextClawMs = 0;
};

namespace
{
    boss_timmy_the_cruel_rework* FindTimmyAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_TIMMY);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_timmy_the_cruel_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Timmy is not running boss_timmy_the_cruel_rework (check the ScriptName).");
        return ai;
    }

    bool Done(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Timmy: {} fired.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_TIMMY, BOSS_TIMMY);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_timmy_the_cruel_rework* ai = FindTimmyAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Timmy: {}", ai->TestState());
        return true;
    }

    bool HandleHeroic(ChatHandler* handler, uint32 heroic)
    {
        boss_timmy_the_cruel_rework* ai = FindTimmyAI(handler);
        return ai && Done(handler, ai->TestHeroic(heroic != 0), heroic ? "heroic form (Playtime restarted)"
            : "normal form (Playtime restarted)");
    }

    bool HandleEmerge(ChatHandler* handler)
    {
        boss_timmy_the_cruel_rework* ai = FindTimmyAI(handler);
        return ai && Done(handler, ai->TestEmerge(), "the emerge (the gate skipped)");
    }

    bool HandleTag(ChatHandler* handler)
    {
        boss_timmy_the_cruel_rework* ai = FindTimmyAI(handler);
        return ai && Done(handler, ai->TestRound(), "a Freeze Tag round (TC2-TC5)");
    }

    bool HandleGotcha(ChatHandler* handler)
    {
        boss_timmy_the_cruel_rework* ai = FindTimmyAI(handler);
        return ai && Done(handler, ai->TestGotcha(), "the round's end now (TC5: the frozen shatter)");
    }

    bool HandlePatty(ChatHandler* handler)
    {
        boss_timmy_the_cruel_rework* ai = FindTimmyAI(handler);
        return ai && Done(handler, ai->TestGame(Game::PattyCake), "Patty Cake (TC6)");
    }

    bool HandleGuess(ChatHandler* handler)
    {
        boss_timmy_the_cruel_rework* ai = FindTimmyAI(handler);
        return ai && Done(handler, ai->TestGame(Game::GuessWho), "Guess Who (TC7)");
    }

    // `.dbtest strat timmy rope [1]`: Jump Rope; 1 = the heroic fallback Double Dutch.
    bool HandleRope(ChatHandler* handler, Optional<uint32> doubleDutch)
    {
        boss_timmy_the_cruel_rework* ai = FindTimmyAI(handler);
        return ai && Done(handler, ai->TestGame(Game::JumpRope, doubleDutch && *doubleDutch != 0),
            "Jump Rope (TC8, TC9)");
    }

    ChatCommandTable const& TimmyTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic, SEC_GAMEMASTER, Console::No },
            { "emerge", HandleEmerge, SEC_GAMEMASTER, Console::No },
            { "tag",    HandleTag,    SEC_GAMEMASTER, Console::No },
            { "gotcha", HandleGotcha, SEC_GAMEMASTER, Console::No },
            { "patty",  HandlePatty,  SEC_GAMEMASTER, Console::No },
            { "guess",  HandleGuess,  SEC_GAMEMASTER, Console::No },
            { "rope",   HandleRope,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_timmy_the_cruel_rework()
{
    RegisterDungeonReworkCreatureAI(boss_timmy_the_cruel_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_playmate, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_st_timmy_clap);
    StratTest::RegisterBoss("timmy", TimmyTestCommands());
}
