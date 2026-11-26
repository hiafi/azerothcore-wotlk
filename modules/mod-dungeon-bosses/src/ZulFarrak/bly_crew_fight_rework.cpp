/*
 * mod-dungeon-bosses, Zul'Farrak D5: Sergeant Bly's crew as a boss (handoff section 3.5 row D5, 3.6, 3.8, 7 #12-#19,
 * #33, #49; build spec docs/dungeons/zul-farrak-rework.md "Sergeant Bly's crew", BC1-BC13, rulings 24 and 26-30, 46).
 * The pure half is CrewFightLogic.h (namespace ZfCrewFight, host-tested by tests/zf_crewfight_test.cpp).
 *
 * The crew are CR's (BlyCrew.h): their AI, faction, movement, gossip, the default fight start (Bly's betrayal lines,
 * then SetData(DATA_CREW_FIGHT, IN_PROGRESS), the four attack the chooser) and Weegli's door are untouched. D5
 * plugs one CrewModeHandler into the Boss mode of the four fighters (their kits, the mechanics, the floors, the end)
 * and one into their Yielded mode (a yielded member raised by Murta, the Test's end). Slot 6 is the instance's: D5
 * writes it only with SetData(DATA_CREW_FIGHT, DONE) at the Test's end; the betrayal ends by deaths (the instance's
 * CrewFightOverByDeaths), a wipe by CR's evade report.
 *
 *   Bly     Shield Bash, Revenge (CR's kit), BC1 Gang Up (heroic Focus Fire, Singled Out), BC2 Bodyguard (heroic BC3
 *           Spell Reflection on the guarded)
 *   Raven   BC6 Gouge (2 s copy), Backstab, BC4 Ambush (heroic BC5 Set Up: stun, Wound Poison, Bly's Gang Up on her)
 *   Oro     Shadow Bolt, Immolate, Curse of Weakness, BC8 Rain of Fire (a registry Zone), heroic BC9 Seed of Corruption
 *           and the Soulstone on Murta (BC12)
 *   Murta   Holy Smite, Renew and Shield (CR's percents), BC7 Greater Heal, heroic BC12 Resurrection
 *   all     heroic BC13 Avenge; the Test's 30% yield (BC11); heroic betrayal falls are held bodies (DungeonKit
 *           HeldBody) until the fight is decided, so a Resurrection or the Soulstone can raise them
 *   end     the stash chest (section 7 #19 A: GO 301360 normal / 301361 heroic, gameobject loot of the same id: the
 *           crew list, the Divino-matic Rod 8548 for quest 2768 and the members' own tables; L-1 fills it), on both
 *           paths
 *
 * Mirrored stock code (AGENTS.md credit rule): none here; the crew's stock kits, gossip and walks are CR's (c9315e3ec
 * moostigre <moostigre@proton.me>, 048025ceb UltraNix <80540499+UltraNix@users.noreply.github.com>).
 */

#include "BlyCrew.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "CrewFightLogic.h"
#include "DungeonKit.h"
#include "DungeonKitBodies.h"
#include "GameObject.h"
#include "GameTime.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "ThreatManager.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include <cmath>
#include <functional>
#include <map>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfCrewFight;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using ZfCrew::BlyCrewAI;

namespace
{
    char const* const kBoss = "blyfight";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    uint64 NowMs()
    {
        return uint64(GameTime::GetGameTimeMS().count());
    }

    uint64 Rand(Window w)
    {
        return ZfCrew::InWindow(w, float(rand_norm()));
    }

    void LogBc(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // On the plaza (rule 5: a corpse runner or a player up the stair is never picked).
    bool OnPlaza(WorldObject const* o)
    {
        return o && PlazaArena().Contains(DungeonKit::PlaneOf(o), o->GetPositionZ());
    }

    // The players `me` fights: its threat list, alive, on the plaza.
    std::vector<Player*> FightPlayers(Creature* me, float maxRangeYd = 100.f)
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
            if (Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr)
                if (CountsAsPlayer(player) && OnPlaza(player) && me->IsWithinDist(player, maxRangeYd))
                    out.push_back(player);
        return out;
    }

    Player* RandomOf(std::vector<Player*> const& players)
    {
        return players.empty() ? nullptr : players[urand(0, uint32(players.size() - 1))];
    }

    char const* NameOf(uint32 member)
    {
        return member < kCrewCount ? kCrewNames[member] : "none";
    }

    std::string PlayerName(Player const* player)
    {
        return player ? player->GetName() : std::string("none");
    }
}

class CrewFightHandler;

namespace
{
    // ----------------------------------------------------------------------------------------------------------------
    // Per-instance fight state and the handler registry. Map threads update different instances at once, so the
    // containers are locked; an entry's contents are only touched by its own map's thread.
    // ----------------------------------------------------------------------------------------------------------------
    struct FightState
    {
        FightBook book;
        uint32 pull = 0;                    // bumps at every pull: callbacks of an older pull drop
        uint32 riseMask = 0;                // yielded members raised: they enter Boss on their next tick
        uint32 guardMember = kCrewCount;    // BC2: the guarded (kCrewCount: none)
        uint64 guardUntilMs = 0;
        uint32 blyShare = 0;                // BC2: Bly's third of the blocked damage, dealt on his next tick
        ObjectGuid shareAttacker;
        ObjectGuid singledOut;              // BC1 heroic: the next mark
        uint64 startedAtMs = 0;             // the pull's game time (the four enter Boss in one tick)
        bool stash = false;
    };

    using HandlerKey = std::pair<uint32, uint64>;  // instance id, creature guid (guids repeat across instances)

    std::mutex& RegistryLock()
    {
        static std::mutex lock;
        return lock;
    }

    std::map<uint32, FightState>& States()
    {
        static std::map<uint32, FightState> states;
        return states;
    }

    std::map<HandlerKey, CrewFightHandler*>& Handlers()
    {
        static std::map<HandlerKey, CrewFightHandler*> handlers;
        return handlers;
    }

    FightState& StateOf(uint32 instanceId)
    {
        std::lock_guard<std::mutex> guard(RegistryLock());
        return States()[instanceId];
    }

    HandlerKey KeyOf(Creature const* creature)
    {
        return { creature->GetInstanceId(), creature->GetGUID().GetRawValue() };
    }

    CrewFightHandler* HandlerOf(Creature const* creature)
    {
        if (!creature)
            return nullptr;
        std::lock_guard<std::mutex> guard(RegistryLock());
        auto it = Handlers().find(KeyOf(creature));
        return it == Handlers().end() ? nullptr : it->second;
    }
}

// --------------------------------------------------------------------------------------------------------------------
// The handler: one per fighter in Boss mode (the fight) and one in Yielded mode (a Resurrection, the Test's end)
// --------------------------------------------------------------------------------------------------------------------
class CrewFightHandler : public ZfCrew::CrewModeHandler
{
public:
    CrewFightHandler(BlyCrewAI& ai, CrewMode mode) : _ai(&ai), _mode(mode)
    {
        if (_mode == CrewMode::Boss)
        {
            std::lock_guard<std::mutex> guard(RegistryLock());
            Handlers()[KeyOf(ai.Me())] = this;
        }
        DungeonKit::HeldBodySpec spec;
        spec.holds = 255;               // every lethal hit while the fight runs (Murta may raise a member again)
        spec.revivePct = Tune::kRisePct;
        spec.dungeon = kLogDungeon;
        spec.boss = kBoss;
        spec.onFall = [this](Creature* /*body*/) { _fellPending = true; };
        _body = DungeonKit::HeldBody(spec);
    }

    ~CrewFightHandler() override
    {
        if (_mode != CrewMode::Boss)
            return;
        std::lock_guard<std::mutex> guard(RegistryLock());
        auto it = Handlers().find(KeyOf(_ai->Me()));
        if (it != Handlers().end() && it->second == this)
            Handlers().erase(it);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Hooks
    // ----------------------------------------------------------------------------------------------------------------
    void OnEnter(BlyCrewAI& /*ai*/, CrewMode from) override
    {
        if (_mode != CrewMode::Boss)
            return;
        FightState& s = State();
        InstanceScript* instance = _ai->Instance();
        if (!instance || instance->GetData(DATA_CREW_FIGHT) != DungeonKit::State::InProgress)
            return;     // a GM's mode outside the fight: CR's kit only
        if (from == CrewMode::Yielded)
        {
            RiseFromYield();
            return;
        }
        if (from == CrewMode::Boss)
            return;     // a create or reload mid-fight (never saved: the instance puts the crew back to Gather)
        // A new pull: the instance turns the four to Boss in one call, so the first of them in this tick opens the book
        // (a stale book from an unloaded instance is replaced too).
        if (!s.book.running || s.startedAtMs != NowMs())
        {
            StartBook(s.book, DungeonKit::IsHeroicMap(Me()), instance->GetData(DATA_CREW_PATH));
            s.startedAtMs = NowMs();
            ++s.pull;
            s.riseMask = 0;
            s.guardMember = kCrewCount;
            s.guardUntilMs = 0;
            s.blyShare = 0;
            s.shareAttacker.Clear();
            s.singledOut.Clear();
            s.stash = false;
            LogBc("pull", Acore::StringFormat("path={} heroic={} bly={} raven={} oro={} murta={}",
                s.book.path == CREW_PATH_TEST ? "test" : "betrayal", s.book.heroic ? 1 : 0, Health(CREW_BLY),
                Health(CREW_RAVEN), Health(CREW_ORO), Health(CREW_MURTA)));
        }
        if (Member() == CREW_BLY)
            OnBossPull(Me(), kBoss);
        StartMine();
    }

    void OnLeave(BlyCrewAI& /*ai*/, CrewMode to) override
    {
        bool const wipe = to == CrewMode::Gather;
        if (_mode != CrewMode::Boss)
        {
            // a yielded member leaves for the pool (the Test won) or back to the gather spot (a wipe)
            Me()->RemoveAurasDueToSpell(SPELL_BC_AVENGE);
            Me()->RemoveAurasDueToSpell(SPELL_BC_SOULSTONE);
            if (wipe)
                Me()->SetFullHealth();
            return;
        }
        CleanupMine(wipe ? "wipe" : "leave");
        if (wipe)
        {
            FightState& s = State();
            if (s.book.running)
                LogBc("wipe", Acore::StringFormat("by={} falls={} rises={} calls={} avenge={}", NameOf(Member()),
                    s.book.falls, s.book.rises, s.book.gangUpCalls, s.book.avenge));
            s.book.running = false;
            s.riseMask = 0;
            Me()->SetFullHealth();
        }
    }

    bool OnUpdate(BlyCrewAI& /*ai*/, uint32 diff) override
    {
        FightState& s = State();
        if (_mode == CrewMode::Yielded)
        {
            CheckEnd(s);
            if (s.riseMask & CrewBit(Member()))
            {
                s.riseMask &= ~CrewBit(Member());
                SetCrewMode(_ai->Instance(), Member(), CrewMode::Boss);     // OnEnter(from Yielded) of the Boss one
            }
            return true;        // nothing of CR's runs in Yielded; after a rise, not its stock kit this tick
        }
        if (!s.book.running || !_started)
            return false;       // CR's kit (a GM's Boss mode outside the fight)

        _body.Update(Me(), diff);
        if (_fellPending)
        {
            _fellPending = false;
            Fall();
            return true;
        }
        if (_yieldPending)
        {
            _yieldPending = false;
            Yield();
            return true;
        }
        CheckEnd(s);
        if (!s.book.running || _body.Fallen())
            return true;

        UpdateFixate(s);
        switch (Member())
        {
            case CREW_BLY:
                return UpdateBly(s, diff);
            case CREW_RAVEN:
                return UpdateRaven(s, diff);
            case CREW_ORO:
                return UpdateOro(s, diff);
            case CREW_MURTA:
                return UpdateMurta(s, diff);
            default:
                return false;
        }
    }

    // Before CR's floors (it skips them: D5 owns the floor in Boss mode; Weegli's never reaches here).
    bool OnDamageTaken(BlyCrewAI& /*ai*/, Unit* attacker, uint32& damage, DamageEffectType /*type*/,
        SpellSchoolMask /*school*/) override
    {
        if (_mode != CrewMode::Boss)
            return false;
        FightState& s = State();
        if (!s.book.running || !_started)
            return false;
        if (_body.Fallen())
        {
            _body.Intercept(Me(), damage);
            return true;
        }

        // BC2: the guard (75% cut while Bly stands within 5 yd; Bly's third of it on his next tick)
        if (s.guardMember == Member() && NowMs() < s.guardUntilMs && damage)
            if (Creature* bly = CrewCreature(_ai->Instance(), CREW_BLY); bly && bly->IsAlive()
                && GuardHolds(s.book.standing[CREW_BLY] == Standing::Fighting, Me()->GetExactDist2d(bly)))
            {
                GuardSplit const split = SplitGuarded(damage);
                damage = split.taken;
                s.blyShare += split.blyShare;
                if (attacker && attacker->IsPlayer())
                    s.shareAttacker = attacker->GetGUID();
            }

        if (s.book.path == CREW_PATH_TEST)
        {
            // BC11: the health floors at 30%; the yield on the next tick (never inside DealDamage).
            uint32 const floor = ZfCrew::PctOf(Me()->GetMaxHealth(), Tune::kYieldPct);
            damage = ZfCrew::FlooredDamage(Me()->GetHealth(), damage, floor);
            if (Me()->GetHealth() - damage <= floor)
                _yieldPending = true;
        }
        else if (s.book.heroic)
            _body.Intercept(Me(), damage);      // BC12: a fall is a held body until the fight is decided
        return true;
    }

    void OnSpellHit(BlyCrewAI& /*ai*/, Unit* caster, SpellInfo const* spell) override
    {
        if (!spell)
            return;
        FightState& s = State();
        if (spell->Id == SPELL_BC_RESURRECTION && s.book.running && caster && caster->GetEntry() == NPC_MURTA)
        {
            Standing const was = s.book.standing[Member()];
            if (!Rise(s.book, Member()))
                return;
            LogBc("resurrection", Acore::StringFormat("{} from={} rises={}", NameOf(Member()),
                kStandingNames[uint32(was)], s.book.rises));
            if (was == Standing::Yielded)
                s.riseMask |= CrewBit(Member());        // the Yielded handler moves it back to Boss next tick
            else if (_mode == CrewMode::Boss)
                RiseFromBody();
            return;
        }
        // BC2: a taunt on Bly ends the guard early (a reward)
        if (_mode == CrewMode::Boss && Member() == CREW_BLY && s.guardMember < kCrewCount
            && (spell->HasAura(SPELL_AURA_MOD_TAUNT) || spell->HasEffect(SPELL_EFFECT_ATTACK_ME)))
            EndGuard(s, "taunt");
    }

    void OnDied(BlyCrewAI& /*ai*/, Unit* killer) override
    {
        if (_mode != CrewMode::Boss)
            return;
        FightState& s = State();
        CleanupMine("death");
        if (s.book.running && GoOut(s.book, Member(), Standing::Dead, NowMs()))
        {
            LogBc("death", Acore::StringFormat("{} killer={} avenge={}", NameOf(Member()),
                killer ? killer->GetName() : std::string("none"), s.book.avenge));
            AvengeTheFallen(s);
        }
        // The betrayal ends by deaths: the instance's OnUnitDeath (before JustDied) made slot 6 DONE.
        if (InstanceScript* instance = _ai->Instance())
            if (instance->GetData(DATA_CREW_FIGHT) == DungeonKit::State::Done && s.book.running)
            {
                s.book.running = false;
                SpawnStash(s, "betrayal");
                LogBc("end", Acore::StringFormat("path=betrayal last={} falls={} rises={} calls={}", NameOf(Member()),
                    s.book.falls, s.book.rises, s.book.gangUpCalls));
            }
    }

    // Any one's evade evades all (FF 2.5): CR's evade reports the crew wipe after the base evade; the instance puts
    // all five back (OnLeave to Gather cleans the rest). Only the evading member's own state is undone here.
    bool OnEvade(BlyCrewAI& /*ai*/, CreatureAI::EvadeReason why) override
    {
        if (_mode == CrewMode::Boss && _started)
            LogBc("evade", Acore::StringFormat("{} reason={}", NameOf(Member()), uint32(why)));
        if (_mode == CrewMode::Boss)
            CleanupMine("evade");
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // What the test commands and the peers call
    // ----------------------------------------------------------------------------------------------------------------
    uint32 Member() const { return _ai->Member(); }
    Creature* Me() const { return _ai->Me(); }
    bool Started() const { return _started; }
    uint32 Pull() const { return _pull; }

    FightState& State() const
    {
        return StateOf(Me()->GetInstanceId());
    }

    // BC1: Raven, Oro and Murta turn on the mark until `untilMs`.
    void TurnOn(ObjectGuid mark, uint64 untilMs)
    {
        _turnTarget = mark;
        _turnUntilMs = untilMs;
    }

    // The heroic betrayal's end: the held body dies for real (`killer` a player of the fight).
    void FinishBody(Unit* killer)
    {
        if (_body.Fallen())
            _body.Finish(Me(), killer);
    }

    // BC12: the Soulstone (or a Resurrection, through OnSpellHit) raises the body.
    void RiseFromBody()
    {
        if (!_body.Fallen())
            return;
        _body.Revive(Me(), Tune::kRisePct);
        OnRisen("body");
    }

    // BC5 heroic Set Up: Bly's immediate Gang Up on the stunned player.
    void SetUpGangUp(Player* target)
    {
        if (Member() == CREW_BLY && _started && !_body.Fallen())
            GangUp(target, Tune::kSetUpWarnMs, "set-up");
    }

    std::string TestState() const
    {
        FightState const& s = State();
        std::string standing;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (CrewBit(m) & kCrewFighters)
                standing += Acore::StringFormat(" {}={}", NameOf(m), kStandingNames[uint32(s.book.standing[m])]);
        return Acore::StringFormat("running={} heroic={} path={} pull={}{} avenge={} calls={} falls={} rises={} "
            "stone={} stone-due={} guard={} singled={} stash={}", s.book.running ? 1 : 0, s.book.heroic ? 1 : 0,
            s.book.path, s.pull, standing, s.book.avenge, s.book.gangUpCalls, s.book.falls, s.book.rises,
            s.book.soulstoneUp ? 1 : 0, s.book.soulstoneDueMs ? 1 : 0, NameOf(s.guardMember),
            s.singledOut ? 1 : 0, s.stash ? 1 : 0);
    }

    enum class TestMechanic
    {
        GangUp,
        Bodyguard,
        Ambush,
        Gouge,
        Rain,
        Seed,
        GreaterHeal,
        Resurrection,
        Stash,
    };

    // `.dbtest zf blyfight <mechanic>`: fires it now from this member (empty: done, else the error).
    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        FightState& s = State();
        if (mechanic == TestMechanic::Stash)
        {
            s.stash = false;
            SpawnStash(s, "gm");
            return {};
        }
        if (!s.book.running || !_started || _body.Fallen() || !Me()->IsAlive())
            return "The crew's fight is not running on this member (.dbtest zf crew path 1, then .dbtest zf band "
                "start).";
        Player* target = CountsAsPlayer(who) ? who : nullptr;
        switch (mechanic)
        {
            case TestMechanic::GangUp:
                return GangUp(target, Tune::kGangUpWarnMs, "gm") ? std::string() : "no player to mark";
            case TestMechanic::Bodyguard:
                return Bodyguard(s) ? std::string() : "nobody to guard (Raven, Oro or Murta must fight)";
            case TestMechanic::Ambush:
                return Ambush(target) ? std::string() : "no player for the Ambush";
            case TestMechanic::Gouge:
                return Gouge(target) ? std::string() : "no player to Gouge";
            case TestMechanic::Rain:
                return Rain(target) ? std::string() : "no player for the Rain of Fire";
            case TestMechanic::Seed:
                return Seed(target) ? std::string() : "no player for the Seed";
            case TestMechanic::GreaterHeal:
                return GreaterHeal(s, true) ? std::string() : "no crew member to heal, or Murta cannot cast now";
            case TestMechanic::Resurrection:
                return Resurrect(s, true) ? std::string() : "nobody to raise, or Murta cannot cast now";
            default:
                return "unknown";
        }
    }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // Pull, cleanup, the outs
    // ----------------------------------------------------------------------------------------------------------------
    uint32 Health(uint32 member) const
    {
        Creature* crew = CrewCreature(_ai->Instance(), member);
        return crew ? crew->GetMaxHealth() : 0;
    }

    bool Heroic() const
    {
        return State().book.heroic;
    }

    // This member's part of a new pull: its beats, its encounter and the bots' boss data.
    void StartMine()
    {
        FightState& s = State();
        _pull = s.pull;
        _started = true;
        _fellPending = false;
        _yieldPending = false;
        _body.Reset(Me());
        _turnTarget.Clear();
        _stayOn.Clear();
        _fixated.Clear();
        _lastCast = LastCast::None;
        _greaterHealEver = false;
        _greaterHealAtMs = 0;
        uint64 const now = NowMs();
        bool const heroic = s.book.heroic;
        _gangUpAtMs = now + Tune::kGangUpFirstMs;
        _guardAtMs = now + Tune::kBodyguardEveryMs(heroic);
        _ambushAtMs = now + Tune::kAmbushFirstMs;
        _gougeAtMs = now + Rand(Tune::kGougeFirst);
        _backstabAtMs = now + Rand(Tune::kBackstab);
        _shadowBoltAtMs = now + Rand(Tune::kShadowBoltFirst);
        _rainAtMs = now + Rand(Tune::kRainFirst);
        _immolateAtMs = now + Rand(Tune::kImmolateFirst);
        _curseAtMs = now + Rand(Tune::kCurseFirst);
        _seedAtMs = now + Tune::kSeedFirstMs;
        _smiteAtMs = now + Rand(Tune::kSmiteFirst);
        _buffAtMs = now + Rand(Tune::kBuffCheckFirst);
        _casterCheckAtMs = now + Tune::kCasterCheckMs;
        Engage();
        // BC12 heroic: Oro's Soulstone sits on Murta from the pull.
        if (heroic && Member() == CREW_ORO)
            if (Creature* murta = CrewCreature(_ai->Instance(), CREW_MURTA); murta && murta->IsAlive())
                Me()->CastSpell(murta, SPELL_BC_SOULSTONE, true);
    }

    // The member's encounter (its mechanics end with slot 6) and the boss data every fighter carries (the bots read
    // the nearest one).
    void Engage()
    {
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_CREW;
        Mechanic::BeginEncounter(Me(), options);
        Mechanic::Describe(Me(), BuildDescriptor(Heroic()));
    }

    static BossMechanics::Descriptor BuildDescriptor(bool heroic)
    {
        using BossMechanics::Condition;
        using BossMechanics::IgnoreEntry;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        // Kill order Murta, Oro, Raven, Bly, each skipped while Guarded; heroic Murta and Oro together.
        TargetEntry murta(NPC_MURTA, Tune::kKillMurta, Who::Dps, Condition::LacksAura(SPELL_BC_GUARDED));
        if (heroic)
            murta.KillTogether(NPC_ORO, Tune::kKillTogetherPct);
        d.targets.push_back(murta);
        d.targets.emplace_back(NPC_ORO, Tune::kKillOro, Who::Dps, Condition::LacksAura(SPELL_BC_GUARDED));
        d.targets.emplace_back(NPC_RAVEN, Tune::kKillRaven, Who::Dps, Condition::LacksAura(SPELL_BC_GUARDED));
        d.targets.emplace_back(NPC_BLY, Tune::kKillBly, Who::Dps, Condition::LacksAura(SPELL_BC_GUARDED));
        d.targets.emplace_back(NPC_BLY, Tune::kTankBly, Who::Tank);
        // Ruling 30: a crew member held by crowd control that breaks on damage is left alone (FF 2.5: an ignore, so
        // no damage, no pets, no AoE count).
        for (uint32 entry : { uint32(NPC_RAVEN), uint32(NPC_ORO), uint32(NPC_MURTA) })
            d.ignores.push_back(IgnoreEntry(entry, Condition::Custom([](Unit const* unit)
            {
                return unit && unit->HasBreakableByDamageCrowdControlAura();
            })));
        // The kicks: Greater Heal (heroic Resurrection first); the steady casts are never worth a kick.
        d.interrupts.emplace_back(NPC_MURTA, heroic ? uint32(SPELL_BC_GREATER_HEAL_H) : uint32(SPELL_BC_GREATER_HEAL),
            Tune::kKickGreaterHeal, Ms(Tune::kGreaterHealEveryMs(heroic)));
        if (heroic)
            d.interrupts.emplace_back(NPC_MURTA, SPELL_BC_RESURRECTION, Tune::kKickResurrection);
        d.interrupts.emplace_back(NPC_MURTA, ZfCrew::SPELL_HOLY_SMITE, 0);
        d.interrupts.emplace_back(NPC_ORO, ZfCrew::SPELL_SHADOW_BOLT, 0);
        d.interrupts.emplace_back(NPC_ORO, ZfCrew::SPELL_IMMOLATE, 0);
        // The dispels: the Seed is the answer; the rest rewards.
        if (heroic)
        {
            d.dispels.emplace_back(SPELL_BC_SEED, Tune::kDispelSeed);
            d.dispels.emplace_back(SPELL_BC_WOUND_POISON, Tune::kDispelReward);
        }
        d.dispels.emplace_back(ZfCrew::SPELL_IMMOLATE, Tune::kDispelReward);
        d.dispels.emplace_back(ZfCrew::SPELL_CURSE_OF_WEAKNESS, Tune::kDispelReward);
        d.purges.emplace_back(0, ZfCrew::SPELL_RENEW, Tune::kPurgeReward);
        d.purges.emplace_back(0, ZfCrew::SPELL_PW_SHIELD, Tune::kPurgeReward);
        return d;
    }

    // Everything this member put out undone (RB-1): its shapes, its marks and debuffs on players, the guard, its look.
    void CleanupMine(char const* how)
    {
        FightState& s = State();
        for (MechanicHandle* h : { &_gangUp, &_ambush, &_rain })
            Drop(*h);
        for (SeedRun& seed : _seeds)
        {
            Drop(seed.runOut);
            if (Player* player = ObjectAccessor::GetPlayer(*Me(), seed.carrier))
                player->RemoveAurasDueToSpell(SPELL_BC_SEED, Me()->GetGUID());
        }
        _seeds.clear();
        if (Player* mark = ObjectAccessor::GetPlayer(*Me(), _markOn))
            mark->RemoveAurasDueToSpell(SPELL_BC_GANG_UP_MARK, Me()->GetGUID());
        _markOn.Clear();
        for (ObjectGuid const& guid : _poisoned)
            if (Player* player = ObjectAccessor::GetPlayer(*Me(), guid))
            {
                player->RemoveAurasDueToSpell(SPELL_BC_WOUND_POISON, Me()->GetGUID());
                player->RemoveAurasDueToSpell(SPELL_BC_WOUND_POISON_LOOK, Me()->GetGUID());
            }
        _poisoned.clear();
        if (Member() == CREW_BLY)
            EndGuard(s, how);
        else if (s.guardMember == Member())
        {
            Me()->RemoveAurasDueToSpell(SPELL_BC_GUARDED);
            Me()->RemoveAurasDueToSpell(SPELL_BC_REFLECT);
        }
        if (_vanished)
        {
            Me()->SetVisible(true);
            _vanished = false;
        }
        if (_fixated)
            Me()->GetThreatMgr().ClearFixate();
        _fixated.Clear();
        _turnTarget.Clear();
        _stayOn.Clear();
        Me()->RemoveAurasDueToSpell(SPELL_BC_AVENGE);
        if (Member() == CREW_MURTA)
            Me()->RemoveAurasDueToSpell(SPELL_BC_SOULSTONE);
        _body.Reset(Me());
        _fellPending = false;
        _yieldPending = false;
        _started = false;
        ++_pull;        // callbacks of this member's shapes drop
    }

    void Drop(MechanicHandle& handle)
    {
        if (handle)
            Mechanic::Cancel(Me(), handle);
        handle = MechanicHandle();
    }

    // This member is out: its beats stop, its shapes go, every fighting crew member gains Avenge (heroic).
    void GoOutNow(Standing how, char const* what)
    {
        FightState& s = State();
        uint64 const now = NowMs();
        if (!GoOut(s.book, Member(), how, now))
            return;
        // the beats in flight (keep _started: a fallen or yielded member may rise)
        for (MechanicHandle* h : { &_gangUp, &_ambush, &_rain })
            Drop(*h);
        for (SeedRun& seed : _seeds)
            Drop(seed.runOut);
        if (Member() == CREW_BLY)
            EndGuard(s, what);
        else if (s.guardMember == Member())
            EndGuard(s, "guarded-out");
        if (_vanished)
        {
            Me()->SetVisible(true);
            _vanished = false;
        }
        if (_fixated)
            Me()->GetThreatMgr().ClearFixate();
        _fixated.Clear();
        Me()->InterruptNonMeleeSpells(false);
        Mechanic::EndEncounter(Me());
        LogBc(what, Acore::StringFormat("{} health={:.0f}% avenge={} stone-due={} fighting={}", NameOf(Member()),
            Me()->GetHealthPct(), s.book.avenge, s.book.soulstoneDueMs ? 1 : 0, FightingMask(s.book)));
        AvengeTheFallen(s);
    }

    // BC12 heroic betrayal: the lethal hit left a held body.
    void Fall()
    {
        GoOutNow(Standing::Fallen, "fall");
    }

    // BC11 the Test: at 30% the member yields (Yielded: friendly, out of the fight, back to its gather spot).
    void Yield()
    {
        GoOutNow(Standing::Yielded, "yield");
        Me()->RemoveAurasDueToSpell(SPELL_BC_AVENGE);       // out of the fight (a Resurrection gives the count back)
        SetCrewMode(_ai->Instance(), Member(), CrewMode::Yielded);
    }

    // BC13 heroic: one stack on every crew member still fighting for each fall, death or yield (no cap).
    void AvengeTheFallen(FightState& s)
    {
        if (!s.book.heroic)
            return;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if ((CrewBit(m) & kCrewFighters) && s.book.standing[m] == Standing::Fighting)
                if (Creature* crew = CrewCreature(_ai->Instance(), m); crew && crew->IsAlive())
                    SyncAvenge(crew, s.book.avenge);
    }

    static void SyncAvenge(Creature* crew, uint32 stacks)
    {
        int32 const delta = int32(stacks) - int32(DungeonKit::Stacks(crew, SPELL_BC_AVENGE));
        if (delta)
            DungeonKit::AddStacks(crew, SPELL_BC_AVENGE, delta);
    }

    // A raised member (Resurrection, Soulstone): 50% health, Avenge as it stands, its encounter, back on a player.
    void OnRisen(char const* how)
    {
        FightState& s = State();
        Me()->SetHealth(ZfCrew::PctOf(Me()->GetMaxHealth(), Tune::kRisePct));
        if (s.book.heroic)
            SyncAvenge(Me(), s.book.avenge);
        if (Member() == CREW_MURTA)
            Me()->RemoveAurasDueToSpell(SPELL_BC_SOULSTONE);
        Engage();
        // the beats wait a moment after the rise
        uint64 const soon = NowMs() + Tune::kCasterCheckMs * 2;
        for (uint64* at : { &_gangUpAtMs, &_guardAtMs, &_ambushAtMs, &_gougeAtMs, &_rainAtMs, &_seedAtMs,
            &_casterCheckAtMs })
            *at = std::max(*at, soon);
        if (!Me()->GetVictim())
        {
            std::vector<Player*> players = FightPlayers(Me());
            Player* nearest = nullptr;
            for (Player* player : players)
                if (!nearest || Me()->GetExactDist(player) < Me()->GetExactDist(nearest))
                    nearest = player;
            if (!nearest)
                nearest = Me()->SelectNearestPlayer(ZfCrew::Tune::kFightTargetRangeYd);
            if (nearest)
                _ai->AttackStart(nearest);
        }
        LogBc("rise", Acore::StringFormat("{} how={} health={:.0f}% avenge={}", NameOf(Member()), how,
            Me()->GetHealthPct(), s.book.avenge));
    }

    // From Yielded back to Boss (a Resurrection, the Soulstone): CR applied faction and react state already.
    void RiseFromYield()
    {
        FightState& s = State();
        if (!s.book.running)
            return;
        _started = true;
        _pull = s.pull;
        OnRisen("yield");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The end
    // ----------------------------------------------------------------------------------------------------------------
    void CheckEnd(FightState& s)
    {
        if (!s.book.running)
            return;
        InstanceScript* instance = _ai->Instance();
        if (!instance)
            return;
        uint32 const slot = instance->GetData(DATA_CREW_FIGHT);
        if (slot != DungeonKit::State::InProgress)
        {
            s.book.running = false;
            if (slot == DungeonKit::State::Done)
                SpawnStash(s, "late");
            return;
        }
        // A fighter gone from the world or dead without its handler seeing it counts as dead.
        for (uint32 m = 0; m < kCrewCount; ++m)
            if ((CrewBit(m) & kCrewFighters) && s.book.standing[m] != Standing::Dead)
            {
                Creature* crew = CrewCreature(instance, m);
                if (!crew || !crew->IsAlive())
                    GoOut(s.book, m, Standing::Dead, NowMs());
            }
        // BC12: the Soulstone raises Murta (Oro still fights). Oro's own tick would also; any tick will do.
        if (SoulstoneDue(s.book, NowMs()))
            Soulstone(s);
        if (!Decided(s.book))
            return;
        if (s.book.path == CREW_PATH_TEST)
            EndTest(s);
        else
            EndBetrayal(s);
    }

    void Soulstone(FightState& s)
    {
        Standing const was = s.book.standing[CREW_MURTA];
        if (!Rise(s.book, CREW_MURTA))
            return;
        s.book.soulstoneUp = false;
        s.book.soulstoneRecastAtMs = NowMs() + Tune::kSoulstoneRecastMs;
        LogBc("soulstone", Acore::StringFormat("murta from={} rises={}", kStandingNames[uint32(was)],
            s.book.rises));
        Creature* murta = CrewCreature(_ai->Instance(), CREW_MURTA);
        if (murta)
            murta->RemoveAurasDueToSpell(SPELL_BC_SOULSTONE);
        if (was == Standing::Yielded)
            s.riseMask |= CrewBit(CREW_MURTA);
        else if (CrewFightHandler* handler = HandlerOf(murta))
            handler->RiseFromBody();
    }

    // BC11: the last yield. Bly's line 4, the stash, slot 6 DONE (the instance sends the five to the pool).
    void EndTest(FightState& s)
    {
        s.book.running = false;
        InstanceScript* instance = _ai->Instance();
        if (Creature* bly = CrewCreature(instance, CREW_BLY); bly && bly->IsAlive() && bly->IsAIEnabled)
            bly->AI()->Talk(ZfCrew::SAY_BLY_TEST_DONE);
        SpawnStash(s, "test");
        LogBc("end", Acore::StringFormat("path=test falls={} rises={} calls={} avenge={}", s.book.falls,
            s.book.rises, s.book.gangUpCalls, s.book.avenge));
        instance->SetData(DATA_CREW_FIGHT, DungeonKit::State::Done);
    }

    // Heroic betrayal: every fighter down and nothing left to raise one: the bodies die for real (the instance ends
    // the fight at the last death, CrewFightOverByDeaths).
    void EndBetrayal(FightState& s)
    {
        s.book.running = false;
        SpawnStash(s, "betrayal");
        LogBc("end", Acore::StringFormat("path=betrayal falls={} rises={} calls={} avenge={}", s.book.falls,
            s.book.rises, s.book.gangUpCalls, s.book.avenge));
        InstanceScript* instance = _ai->Instance();
        Unit* killer = Me()->GetLootRecipient();
        if (!killer)
            killer = RandomOf(FightPlayers(Me()));
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (CrewBit(m) & kCrewFighters)
                if (CrewFightHandler* handler = HandlerOf(CrewCreature(instance, m)))
                    handler->FinishBody(killer);
    }

    // Section 7 #19 A: the stash on the plaza, the entry of this difficulty, for a day or until looted. Summoned by
    // the map (no spawn row: the heroic rollout widens every spawn to both difficulties); not restored after a
    // reload (the SM Last Stand chest precedent).
    void SpawnStash(FightState& s, char const* how)
    {
        if (s.stash)
            return;
        s.stash = true;
        uint32 const entry = StashEntry(DungeonKit::IsHeroicMap(Me()));
        if (Me()->FindNearestGameObject(entry, 150.f, true))
        {
            LogBc("stash-standing", Acore::StringFormat("entry={}", entry));
            return;
        }
        float x = kStashSpot.x;
        float y = kStashSpot.y;
        float z = kStashSpot.z;
        Me()->UpdateGroundPositionZ(x, y, z);
        float const half = kStashSpot.o / 2.f;
        GameObject* stash = Me()->GetMap()->SummonGameObject(entry, x, y, z, kStashSpot.o, 0.f, 0.f, std::sin(half),
            std::cos(half), DAY);
        if (!stash)
        {
            LogBc("stash-missing", Acore::StringFormat("entry={} could not be summoned (no template?)", entry));
            return;
        }
        LogBc("stash", Acore::StringFormat("entry={} how={} at=({:.1f}, {:.1f}, {:.1f})", entry, how, x, y, z));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The turn on a mark (BC1) and Raven's stay (BC4)
    // ----------------------------------------------------------------------------------------------------------------
    void UpdateFixate(FightState& /*s*/)
    {
        uint64 const now = NowMs();
        Unit* want = nullptr;
        if (_turnTarget && now < _turnUntilMs)
            want = ObjectAccessor::GetPlayer(*Me(), _turnTarget);
        if (!CountsAsPlayer(want ? want->ToPlayer() : nullptr))
        {
            want = nullptr;
            if (_stayOn)
            {
                Player* stay = ObjectAccessor::GetPlayer(*Me(), _stayOn);
                if (CountsAsPlayer(stay))
                    want = stay;
                else
                    _stayOn.Clear();
            }
        }
        ObjectGuid const wantGuid = want ? want->GetGUID() : ObjectGuid::Empty;
        if (wantGuid == _fixated)
            return;
        if (want)
            Me()->GetThreatMgr().FixateTarget(want);
        else
            Me()->GetThreatMgr().ClearFixate();
        _fixated = wantGuid;
    }

    // The next time of a beat that fired now (each beat keeps its own clock; a cast in progress delays it, never
    // another beat: RB-17).
    static uint64 Next(uint64 now, uint64 periodMs)
    {
        return now + periodMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Bly: BC1 Gang Up, BC2 Bodyguard (his Shield Bash and Revenge are CR's kit)
    // ----------------------------------------------------------------------------------------------------------------
    bool UpdateBly(FightState& s, uint32 diff)
    {
        uint64 const now = NowMs();
        bool const heroic = s.book.heroic;
        if (s.blyShare)
        {
            uint32 const share = s.blyShare;
            s.blyShare = 0;
            Player* attacker = ObjectAccessor::GetPlayer(*Me(), s.shareAttacker);
            ZfCrew::DamageCrew(Me(), attacker, share);
            if (!Me()->IsAlive() || _fellPending || _yieldPending)
                return true;
        }
        if (now >= _gangUpAtMs && !Me()->HasUnitState(UNIT_STATE_CASTING))
        {
            GangUp(nullptr, Tune::kGangUpWarnMs, "timer");
            _gangUpAtMs = Next(now, Tune::kGangUpEveryMs(heroic));
        }
        if (now >= _guardAtMs && s.guardMember >= kCrewCount)
        {
            Bodyguard(s);
            _guardAtMs = Next(now, Tune::kBodyguardEveryMs(heroic));
        }
        if (s.guardMember < kCrewCount)
            return GuardTick(s, diff);
        return false;       // CR's kit: UpdateVictim, Shield Bash, Revenge, melee
    }

    // BC1: Bly yells and marks a random player (heroic: the Singled Out player first); Raven, Oro and Murta turn on
    // the mark; 4 s later (Set Up: 2 s) the strike is split among everyone within 6 yd of the mark.
    bool GangUp(Player* forced, uint32 warnMs, char const* why)
    {
        FightState& s = State();
        Player* target = forced;
        if (!target && s.book.heroic && s.singledOut)
        {
            Player* singled = ObjectAccessor::GetPlayer(*Me(), s.singledOut);
            if (CountsAsPlayer(singled) && OnPlaza(singled))
                target = singled;
        }
        s.singledOut.Clear();
        if (!target)
            target = RandomOf(FightPlayers(Me()));
        if (!target)
            return false;
        uint32 const call = s.book.gangUpCalls++;
        float const total = GangUpTotalPct(s.book.heroic, call);
        Drop(_gangUp);
        if (Player* old = ObjectAccessor::GetPlayer(*Me(), _markOn))
            old->RemoveAurasDueToSpell(SPELL_BC_GANG_UP_MARK, Me()->GetGUID());
        _markOn = target->GetGUID();
        _ai->Talk(ZfCrew::YELL_BLY_GANG_UP, target);
        Me()->CastSpell(target, SPELL_BC_GANG_UP_MARK, true);
        ObjectGuid const mark = target->GetGUID();
        MechanicRef ref = Mechanic::Stack(Me(), target, Tune::kGangUpRadiusYd, Ms(warnMs));
        ref.Within(PlazaFloorBounds()).Tag(TAG_BC_GANG_UP)
            .OnResolve(OnMine([mark, total](CrewFightHandler& h, BossMechanics::ResolveResult const& r)
            {
                h.GangUpStrike(mark, total, r);
            }));
        _gangUp = ref.Handle();
        uint64 const turnUntil = NowMs() + Tune::kGangUpTurnMs;
        for (uint32 m : { uint32(CREW_RAVEN), uint32(CREW_ORO), uint32(CREW_MURTA) })
            if (s.book.standing[m] == Standing::Fighting)
                if (CrewFightHandler* peer = HandlerOf(CrewCreature(_ai->Instance(), m)))
                    peer->TurnOn(mark, turnUntil);
        LogBc("gang-up", Acore::StringFormat("why={} mark={} tank={} call={} total={:.0f}% warn={}ms", why,
            target->GetName(), target == Me()->GetVictim() ? 1 : 0, call + 1, total, warnMs));
        return true;
    }

public:
    void GangUpStrike(ObjectGuid markGuid, float totalPct, BossMechanics::ResolveResult const& result)
    {
        FightState& s = State();
        Player* mark = ObjectAccessor::GetPlayer(*Me(), markGuid);
        if (mark)
            mark->RemoveAurasDueToSpell(SPELL_BC_GANG_UP_MARK, Me()->GetGUID());
        if (_markOn == markGuid)
            _markOn.Clear();
        _gangUp = MechanicHandle();
        std::vector<Unit*> inside;
        GuidSet insideGuids;
        for (ObjectGuid const& guid : result.hits)
            if (Player* player = ObjectAccessor::GetPlayer(*Me(), guid); CountsAsPlayer(player))
            {
                inside.push_back(player);
                insideGuids.insert(guid);
            }
        for (auto const& [guid, share] : DungeonKit::SplitShares(Me(), inside, totalPct))
            if (share)
                if (Player* player = ObjectAccessor::GetPlayer(*Me(), guid))
                    Me()->CastCustomSpell(SPELL_BC_GANG_UP_SHARE, SPELLVALUE_BASE_POINT0, int32(share), player,
                        TRIGGERED_FULL_MASK);
        // Heroic Singled Out: a player outside the stack is the next mark (the farthest from the mark).
        std::string singled = "none";
        if (s.book.heroic && mark)
        {
            std::vector<Player*> players = FightPlayers(Me());
            std::vector<bool> outside;
            std::vector<float> dist;
            for (Player* player : players)
            {
                outside.push_back(!insideGuids.count(player->GetGUID()));
                dist.push_back(player->GetExactDist2d(mark));
            }
            if (std::optional<std::size_t> const pick = PickSingledOut(outside, dist))
            {
                s.singledOut = players[*pick]->GetGUID();
                singled = players[*pick]->GetName();
            }
        }
        LogBc("gang-up-strike", Acore::StringFormat("mark={} inside={} share={:.1f}% singled-out={}",
            PlayerName(mark), inside.size(), SharePct(totalPct, inside.size()), singled));
    }

private:
    // BC2: Bly Intervenes to the fighting crew member at the lowest health percent and guards it 8 s (heroic: a
    // one-charge Spell Reflection on it, BC3).
    bool Bodyguard(FightState& s)
    {
        InstanceScript* instance = _ai->Instance();
        std::array<float, kCrewCount> pct{};
        uint32 fighting = 0;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (Creature* crew = CrewCreature(instance, m); crew && crew->IsAlive()
                && s.book.standing[m] == Standing::Fighting)
            {
                pct[m] = crew->GetHealthPct();
                fighting |= CrewBit(m);
            }
        std::optional<uint32> const pick = PickGuarded(pct, fighting);
        if (!pick)
            return false;
        Creature* guarded = CrewCreature(instance, *pick);
        if (!guarded)
            return false;
        EndGuard(s, "new");
        s.guardMember = *pick;
        s.guardUntilMs = NowMs() + Tune::kGuardedMs;
        Me()->CastSpell(guarded, SPELL_BC_INTERVENE, true);
        Me()->CastSpell(guarded, SPELL_BC_GUARDED, true);
        if (s.book.heroic)
            Me()->CastSpell(guarded, SPELL_BC_REFLECT, true);
        Me()->SetWalk(false);
        Me()->GetMotionMaster()->MoveFollow(guarded, Tune::kGuardFollowYd, float(M_PI));
        LogBc("bodyguard", Acore::StringFormat("guarded={} health={:.0f}% reflect={}", NameOf(*pick), pct[*pick],
            s.book.heroic ? 1 : 0));
        return true;
    }

    // The guard's tick: Bly stays at the guarded (follow), fights whoever is in reach, and the guard ends on time, a
    // taunt (OnSpellHit) or when either of them is out.
    bool GuardTick(FightState& s, uint32 diff)
    {
        Creature* guarded = CrewCreature(_ai->Instance(), s.guardMember);
        if (NowMs() >= s.guardUntilMs || !guarded || !guarded->IsAlive()
            || s.book.standing[s.guardMember] != Standing::Fighting)
        {
            EndGuard(s, NowMs() >= s.guardUntilMs ? "time" : "guarded-out");
            return false;
        }
        if (!_ai->UpdateCrewVictim())
            return true;
        if (Me()->GetMotionMaster()->GetCurrentMovementGeneratorType() != FOLLOW_MOTION_TYPE)
            Me()->GetMotionMaster()->MoveFollow(guarded, Tune::kGuardFollowYd, float(M_PI));
        _ai->RunKit(diff);
        return true;
    }

    void EndGuard(FightState& s, char const* how)
    {
        if (s.guardMember >= kCrewCount)
            return;
        if (Creature* guarded = CrewCreature(_ai->Instance(), s.guardMember))
        {
            guarded->RemoveAurasDueToSpell(SPELL_BC_GUARDED);
            guarded->RemoveAurasDueToSpell(SPELL_BC_REFLECT);
        }
        LogBc("bodyguard-end", Acore::StringFormat("guarded={} how={}", NameOf(s.guardMember), how));
        s.guardMember = kCrewCount;
        s.guardUntilMs = 0;
        if (Creature* bly = CrewCreature(_ai->Instance(), CREW_BLY); bly && bly->IsAlive())
            if (Unit* victim = bly->GetVictim())
                if (bly->GetMotionMaster()->GetCurrentMovementGeneratorType() == FOLLOW_MOTION_TYPE)
                    bly->GetMotionMaster()->MoveChase(victim);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Raven: BC6 Gouge, Backstab, BC4 Ambush, BC5 heroic Set Up
    // ----------------------------------------------------------------------------------------------------------------
    bool UpdateRaven(FightState& s, uint32 /*diff*/)
    {
        uint64 const now = NowMs();
        UpdatePoison();
        if (_vanished)
        {
            if (now < _vanishUntilMs)
                return true;    // gone for the Ambush's warning
            Me()->SetVisible(true);     // the strike never came back (a cancelled shape): she shows again
            _vanished = false;
            LogBc("ambush-lost", "raven shows again");
        }
        if (!_ai->UpdateCrewVictim())
            return true;
        if (now >= _ambushAtMs && !Me()->HasUnitState(UNIT_STATE_CASTING))
        {
            Ambush(nullptr);
            _ambushAtMs = Next(now, Tune::kAmbushEveryMs(s.book.heroic));
            return true;
        }
        if (Me()->HasUnitState(UNIT_STATE_CASTING))
            return true;
        if (now >= _gougeAtMs)
        {
            Gouge(nullptr);
            _gougeAtMs = Next(now, Rand(Tune::kGouge));
        }
        else if (now >= _backstabAtMs)
        {
            if (Unit* victim = Me()->GetVictim(); victim && victim->isInBack(Me()))
                Me()->CastSpell(victim, ZfCrew::SPELL_BACKSTAB, false);
            _backstabAtMs = Next(now, Rand(Tune::kBackstab));
        }
        if (!Me()->HasUnitState(UNIT_STATE_CASTING))
            _ai->DoMeleeAttackIfReady();
        return true;
    }

    // BC6: the 2 s Gouge on a random player within 5 yd (tank included), else her victim.
    bool Gouge(Player* forced)
    {
        Unit* target = forced;
        if (!target)
            target = RandomOf(FightPlayers(Me(), Tune::kGougeRangeYd));
        if (!target)
            target = Me()->GetVictim();
        if (!target)
            return false;
        Me()->CastSpell(target, SPELL_BC_GOUGE, false);
        LogBc("gouge", Acore::StringFormat("target={} tank={}", target->GetName(),
            target == Me()->GetVictim() ? 1 : 0));
        return true;
    }

    // BC4: Raven vanishes and a 3 yd circle appears under a random player (tank included); at its end she steps into
    // it and strikes (40% and Weakened), then stays on that player.
    bool Ambush(Player* forced)
    {
        FightState& s = State();
        Player* target = forced ? forced : RandomOf(FightPlayers(Me(), Tune::kAmbushRangeYd));
        if (!target)
            return false;
        Position const spot = target->GetPosition();
        uint32 const warn = Tune::kAmbushWarnMs(s.book.heroic);
        Drop(_ambush);
        Me()->InterruptNonMeleeSpells(false);
        Me()->CastSpell(Me(), SPELL_BC_VANISH, true);
        Me()->AttackStop();
        Me()->StopMoving();
        Me()->SetVisible(false);
        _vanished = true;
        _vanishUntilMs = NowMs() + warn + Tune::kCasterCheckMs * 2;
        ObjectGuid const victim = target->GetGUID();
        MechanicRef ref = Mechanic::Circle(Me(), spot, Tune::kAmbushRadiusYd, Ms(warn));
        ref.Damage(Tune::kAmbushPct).TankDamage(Tune::kAmbushPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_BC_AMBUSH)
            .Weakened().Within(PlazaFloorBounds()).Tag(TAG_BC_AMBUSH)
            .OnResolve(OnMine([victim, spot](CrewFightHandler& h, BossMechanics::ResolveResult const& r)
            {
                h.AmbushStrike(victim, spot, r);
            }));
        _ambush = ref.Handle();
        if (!_ambush)
        {
            Me()->SetVisible(true);
            _vanished = false;
            return false;
        }
        LogBc("ambush", Acore::StringFormat("target={} tank={} at=({:.1f}, {:.1f}) warn={}ms", target->GetName(),
            target == Me()->GetVictim() ? 1 : 0, spot.GetPositionX(), spot.GetPositionY(), warn));
        return true;
    }

public:
    void AmbushStrike(ObjectGuid victimGuid, Position const& spot, BossMechanics::ResolveResult const& result)
    {
        FightState& s = State();
        _ambush = MechanicHandle();
        Me()->NearTeleportTo(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), Me()->GetOrientation());
        if (_vanished)
        {
            Me()->SetVisible(true);
            _vanished = false;
        }
        Player* victim = ObjectAccessor::GetPlayer(*Me(), victimGuid);
        if (CountsAsPlayer(victim))
        {
            _stayOn = victimGuid;
            _ai->AttackStart(victim);
        }
        std::vector<Player*> hit;
        for (ObjectGuid const& guid : result.hits)
            if (Player* player = ObjectAccessor::GetPlayer(*Me(), guid); CountsAsPlayer(player))
                hit.push_back(player);
        // BC5 heroic Set Up: every hit player is stunned and poisoned; Bly calls a Gang Up on the first.
        if (s.book.heroic)
        {
            for (Player* player : hit)
            {
                Me()->CastSpell(player, SPELL_BC_KIDNEY_SHOT, true);
                Me()->CastSpell(player, SPELL_BC_WOUND_POISON, true);
                Me()->CastSpell(player, SPELL_BC_WOUND_POISON_LOOK, true);
                _poisoned.push_back(player->GetGUID());
            }
            if (!hit.empty() && s.book.standing[CREW_BLY] == Standing::Fighting)
                if (CrewFightHandler* bly = HandlerOf(CrewCreature(_ai->Instance(), CREW_BLY)))
                    bly->SetUpGangUp(hit.front());
        }
        LogBc("ambush-strike", Acore::StringFormat("victim={} hit={} set-up={}", PlayerName(victim), hit.size(),
            s.book.heroic && !hit.empty() ? 1 : 0));
    }

private:
    // Wound Poison's lasting look goes with the poison (a dispel takes both).
    void UpdatePoison()
    {
        for (auto it = _poisoned.begin(); it != _poisoned.end();)
        {
            Player* player = ObjectAccessor::GetPlayer(*Me(), *it);
            if (!player || !player->HasAura(SPELL_BC_WOUND_POISON, Me()->GetGUID()))
            {
                if (player)
                    player->RemoveAurasDueToSpell(SPELL_BC_WOUND_POISON_LOOK, Me()->GetGUID());
                it = _poisoned.erase(it);
            }
            else
                ++it;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Oro: Shadow Bolt, Immolate, Curse of Weakness, BC8 Rain of Fire, heroic BC9 Seed and the Soulstone (BC12)
    // ----------------------------------------------------------------------------------------------------------------
    bool UpdateOro(FightState& s, uint32 /*diff*/)
    {
        uint64 const now = NowMs();
        UpdateSeeds();
        // BC12: a new stone on Murta after one was used (both fighting)
        if (s.book.heroic && !s.book.soulstoneUp && s.book.soulstoneRecastAtMs && now >= s.book.soulstoneRecastAtMs
            && s.book.standing[CREW_MURTA] == Standing::Fighting)
            if (Creature* murta = CrewCreature(_ai->Instance(), CREW_MURTA); murta && murta->IsAlive())
            {
                Me()->CastSpell(murta, SPELL_BC_SOULSTONE, true);
                s.book.soulstoneUp = true;
                s.book.soulstoneRecastAtMs = 0;
                LogBc("soulstone-up", "murta");
            }
        if (!_ai->UpdateCrewVictim())
            return true;
        if (Me()->HasUnitState(UNIT_STATE_CASTING))
            return true;
        if (s.book.heroic && now >= _seedAtMs)
        {
            Seed(nullptr);
            _seedAtMs = Next(now, Tune::kSeedEveryMs);
        }
        if (now >= _rainAtMs)
        {
            Rain(nullptr);
            _rainAtMs = Next(now, Rand(Tune::kRain));
        }
        if (now >= _curseAtMs)
        {
            Me()->CastSpell(Me()->GetVictim(), ZfCrew::SPELL_CURSE_OF_WEAKNESS, false);
            _curseAtMs = Next(now, Rand(Tune::kCurse));
        }
        else if (now >= _immolateAtMs)
        {
            Me()->CastSpell(Me()->GetVictim(), ZfCrew::SPELL_IMMOLATE, false);
            _immolateAtMs = Next(now, Rand(Tune::kImmolate));
        }
        else if (now >= _shadowBoltAtMs)
        {
            Me()->CastSpell(Me()->GetVictim(), ZfCrew::SPELL_SHADOW_BOLT, false);
            _shadowBoltAtMs = Next(now, Rand(Tune::kShadowBolt));
        }
        if (!Me()->HasUnitState(UNIT_STATE_CASTING))
            _ai->DoMeleeAttackIfReady();
        return true;
    }

    // BC8: the fire falls on a random player's spot within 30 yd (tank included): 1.5 s, then ticks every 3 s for 9 s.
    bool Rain(Player* forced)
    {
        FightState& s = State();
        Player* target = forced ? forced : RandomOf(FightPlayers(Me(), Tune::kRainRangeYd));
        if (!target)
            return false;
        Position const spot = target->GetPosition();
        float const pct = Tune::kRainTickPct(s.book.heroic);
        Drop(_rain);
        Me()->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_BC_RAIN_LOOK, true);
        MechanicRef ref = Mechanic::Circle(Me(), spot, Tune::kRainRadiusYd, Ms(Tune::kRainWarnMs));
        ref.Persistent(Ms(Tune::kRainMs), Ms(Tune::kRainTickMs)).Damage(pct).TankDamage(pct)
            .School(SPELL_SCHOOL_FIRE).Spell(SPELL_BC_RAIN).Within(PlazaFloorBounds()).Tag(TAG_BC_RAIN);
        _rain = ref.Handle();
        LogBc("rain-of-fire", Acore::StringFormat("target={} tank={} pct={:.0f}", target->GetName(),
            target == Me()->GetVictim() ? 1 : 0, pct));
        return true;
    }

    // BC9 heroic: the Seed on a random player (tank included); a RunOut for the bots; undispelled after 6 s it bursts
    // on everyone within 10 yd, the carrier included.
    bool Seed(Player* forced)
    {
        Player* target = forced ? forced : RandomOf(FightPlayers(Me(), Tune::kSeedRangeYd));
        if (!target)
            return false;
        Me()->CastSpell(target, SPELL_BC_SEED, true);
        SeedRun run;
        run.carrier = target->GetGUID();
        run.burstAtMs = NowMs() + Tune::kSeedMs;
        MechanicRef ref = Mechanic::RunOut(Me(), target, Tune::kSeedRadiusYd, Ms(Tune::kSeedMs));
        ref.Within(PlazaFloorBounds()).Tag(TAG_BC_SEED);
        run.runOut = ref.Handle();
        _seeds.push_back(run);
        LogBc("seed", Acore::StringFormat("carrier={} tank={}", target->GetName(),
            target == Me()->GetVictim() ? 1 : 0));
        return true;
    }

    void UpdateSeeds()
    {
        uint64 const now = NowMs();
        for (auto it = _seeds.begin(); it != _seeds.end();)
        {
            Player* carrier = ObjectAccessor::GetPlayer(*Me(), it->carrier);
            bool const seeded = carrier && carrier->IsAlive() && carrier->HasAura(SPELL_BC_SEED, Me()->GetGUID());
            if (!seeded)
            {
                Drop(it->runOut);
                LogBc("seed-gone", Acore::StringFormat("carrier={} early={}", PlayerName(carrier),
                    now < it->burstAtMs ? 1 : 0));
                it = _seeds.erase(it);
                continue;
            }
            if (now < it->burstAtMs)
            {
                ++it;
                continue;
            }
            uint32 hits = 0;
            for (MapReference const& ref : Me()->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource(); CountsAsPlayer(player)
                    && (player == carrier || player->GetExactDist2d(carrier) <= Tune::kSeedRadiusYd))
                {
                    Me()->CastCustomSpell(SPELL_BC_SEED_BURST, SPELLVALUE_BASE_POINT0,
                        int32(DungeonKit::RefFlatOn(Me(), player, Tune::kSeedPct)), player, TRIGGERED_FULL_MASK);
                    ++hits;
                }
            carrier->RemoveAurasDueToSpell(SPELL_BC_SEED, Me()->GetGUID());
            Drop(it->runOut);
            LogBc("seed-burst", Acore::StringFormat("carrier={} hits={}", carrier->GetName(), hits));
            it = _seeds.erase(it);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Murta: Holy Smite, Renew and Shield, BC7 Greater Heal, heroic BC12 Resurrection
    // ----------------------------------------------------------------------------------------------------------------
    bool UpdateMurta(FightState& s, uint32 /*diff*/)
    {
        uint64 const now = NowMs();
        if (!_ai->UpdateCrewVictim())
            return true;
        if (Me()->HasUnitState(UNIT_STATE_CASTING))
            return true;
        if (now >= _casterCheckAtMs)
        {
            _casterCheckAtMs = now + Tune::kCasterCheckMs;
            if (GreaterHeal(s, false) || (s.book.heroic && Resurrect(s, false)))
                return true;
        }
        if (now >= _buffAtMs)
        {
            _buffAtMs = Next(now, Rand(Tune::kBuffCheck));
            if (Buff(s))
                return true;
        }
        if (now >= _smiteAtMs)
        {
            if (Me()->CastSpell(Me()->GetVictim(), ZfCrew::SPELL_HOLY_SMITE, false) == SPELL_CAST_OK)
                _lastCast = LastCast::Other;
            _smiteAtMs = Next(now, Rand(Tune::kSmite));
        }
        if (!Me()->HasUnitState(UNIT_STATE_CASTING))
            _ai->DoMeleeAttackIfReady();
        return true;
    }

    // The fighting crew within reach and their health percents.
    std::vector<Creature*> FightingCrew(FightState const& s) const
    {
        std::vector<Creature*> out;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if ((CrewBit(m) & kCrewFighters) && s.book.standing[m] == Standing::Fighting)
                if (Creature* crew = CrewCreature(_ai->Instance(), m); crew && crew->IsAlive()
                    && Me()->IsWithinDistInMap(crew, Tune::kHealRangeYd))
                    out.push_back(crew);
        return out;
    }

    // BC7: a crew member under 50% (the lowest), the cooldown over, not straight after a Resurrection.
    bool GreaterHeal(FightState& s, bool force)
    {
        std::vector<Creature*> crew = FightingCrew(s);
        Creature* lowest = nullptr;
        for (Creature* c : crew)
            if (!lowest || c->GetHealthPct() < lowest->GetHealthPct())
                lowest = c;
        if (!lowest)
            return false;
        uint64 const now = NowMs();
        bool const heroic = s.book.heroic;
        if (!force && !GreaterHealDue(lowest->GetHealthPct(), _greaterHealEver, now - _greaterHealAtMs, heroic,
            _lastCast))
            return false;
        uint32 const spell = heroic ? SPELL_BC_GREATER_HEAL_H : SPELL_BC_GREATER_HEAL;
        int32 const amount = int32(ZfCrew::PctOf(lowest->GetMaxHealth(), Tune::kGreaterHealPct(heroic)));
        if (Me()->CastCustomSpell(spell, SPELLVALUE_BASE_POINT0, amount, lowest, TRIGGERED_NONE) != SPELL_CAST_OK)
            return false;
        _lastCast = LastCast::GreaterHeal;
        _greaterHealEver = true;
        _greaterHealAtMs = now;
        Mechanic::NoteNextCastIn(Me(), spell, Ms(Tune::kGreaterHealEveryMs(heroic)));
        LogBc("greater-heal", Acore::StringFormat("target={} health={:.0f}% amount={}", lowest->GetName(),
            lowest->GetHealthPct(), amount));
        return true;
    }

    // BC12 heroic: Resurrection on the member out longest (fallen body or yielded), never straight after a Greater
    // Heal; the target's OnSpellHit raises it.
    bool Resurrect(FightState& s, bool force)
    {
        if (!force && !ResurrectionAllowed(_lastCast))
            return false;
        std::optional<uint32> const pick = PickResurrection(s.book);
        if (!pick)
            return false;
        Creature* target = CrewCreature(_ai->Instance(), *pick);
        if (!target || !target->IsAlive() || !Me()->IsWithinDistInMap(target, Tune::kHealRangeYd))
            return false;
        if (Me()->CastSpell(target, SPELL_BC_RESURRECTION, false) != SPELL_CAST_OK)
            return false;
        _lastCast = LastCast::Resurrection;
        LogBc("resurrection-cast", Acore::StringFormat("target={} {}", NameOf(*pick),
            kStandingNames[uint32(s.book.standing[*pick])]));
        return true;
    }

    // Renew and Power Word: Shield on a hurt fighting crew member (CR's percents; purge rewards).
    bool Buff(FightState& s)
    {
        std::vector<Creature*> crew = FightingCrew(s);
        std::vector<float> pcts;
        for (Creature* c : crew)
            pcts.push_back(c->GetHealthPct());
        std::optional<std::size_t> const pick = ZfCrew::PickHealTarget(pcts, ZfCrew::Tune::kRenewBelowPct);
        if (!pick)
            return false;
        Creature* target = crew[*pick];
        ZfCrew::MurtaHeal const what = ZfCrew::MurtaSpellFor(std::max(target->GetHealthPct(),
            ZfCrew::Tune::kHealBelowPct), target->HasAura(ZfCrew::SPELL_RENEW, Me()->GetGUID()),
            target->HasAura(ZfCrew::SPELL_PW_SHIELD, Me()->GetGUID()));
        uint32 spell = 0;
        float pct = 0.f;
        if (what == ZfCrew::MurtaHeal::Shield)
        {
            spell = ZfCrew::SPELL_PW_SHIELD;
            pct = ZfCrew::Tune::kShieldPct;
        }
        else if (what == ZfCrew::MurtaHeal::Renew)
        {
            spell = ZfCrew::SPELL_RENEW;
            pct = ZfCrew::Tune::kRenewTickPct;
        }
        if (!spell)
            return false;
        int32 const amount = int32(ZfCrew::PctOf(target->GetMaxHealth(), pct));
        if (Me()->CastCustomSpell(spell, SPELLVALUE_BASE_POINT0, amount, target, TRIGGERED_NONE) != SPELL_CAST_OK)
            return false;
        _lastCast = LastCast::Other;
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Callbacks: run `fn(handler, result)` on this member if this pull (and this member's part of it) still runs.
    // Captures the map and the guid only (a lambda the registry keeps must not hold a Unit*).
    // ----------------------------------------------------------------------------------------------------------------
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnMine(Fn fn)
    {
        Map* map = Me()->GetMap();
        ObjectGuid const guid = Me()->GetGUID();
        return [map, guid, fn, pull = _pull](BossMechanics::ResolveResult const& result)
        {
            Creature* crew = map ? map->GetCreature(guid) : nullptr;
            if (!crew || !crew->IsAlive())
                return;
            if (CrewFightHandler* handler = HandlerOf(crew); handler && handler->_pull == pull && handler->_started)
                fn(*handler, result);
        };
    }

    struct SeedRun
    {
        ObjectGuid carrier;
        uint64 burstAtMs = 0;
        MechanicHandle runOut;
    };

    BlyCrewAI* _ai;
    CrewMode _mode;
    DungeonKit::HeldBody _body;
    uint32 _pull = 0;
    bool _started = false;
    bool _fellPending = false;
    bool _yieldPending = false;
    bool _vanished = false;
    uint64 _vanishUntilMs = 0;
    // the turn on a mark (BC1), Raven's stay (BC4) and the fixate applied now
    ObjectGuid _turnTarget;
    uint64 _turnUntilMs = 0;
    ObjectGuid _stayOn;
    ObjectGuid _fixated;
    // Bly
    MechanicHandle _gangUp;
    ObjectGuid _markOn;
    uint64 _gangUpAtMs = 0;
    uint64 _guardAtMs = 0;
    // Raven
    MechanicHandle _ambush;
    std::vector<ObjectGuid> _poisoned;
    uint64 _ambushAtMs = 0;
    uint64 _gougeAtMs = 0;
    uint64 _backstabAtMs = 0;
    // Oro
    MechanicHandle _rain;
    std::vector<SeedRun> _seeds;
    uint64 _shadowBoltAtMs = 0;
    uint64 _rainAtMs = 0;
    uint64 _immolateAtMs = 0;
    uint64 _curseAtMs = 0;
    uint64 _seedAtMs = 0;
    // Murta
    LastCast _lastCast = LastCast::None;
    bool _greaterHealEver = false;
    uint64 _greaterHealAtMs = 0;
    uint64 _smiteAtMs = 0;
    uint64 _buffAtMs = 0;
    uint64 _casterCheckAtMs = 0;
};

// --------------------------------------------------------------------------------------------------------------------
// `.dbtest zf blyfight`
//
//   .dbtest zf blyfight info          Bly's entry, health, slot 6, combat
//   .dbtest zf blyfight state         the fight's book: who stands, Avenge, the Soulstone, the guard, the calls
//   .dbtest zf blyfight gangup        BC1 now (on the selected player, else a random one; heroic: Focus Fire's next)
//   .dbtest zf blyfight bodyguard     BC2 now (the lowest crew member; heroic with BC3)
//   .dbtest zf blyfight ambush        BC4 now (heroic BC5 Set Up on whoever it hits)
//   .dbtest zf blyfight gouge         BC6 now
//   .dbtest zf blyfight rain          BC8 now
//   .dbtest zf blyfight seed          BC9 now (any difficulty)
//   .dbtest zf blyfight heal          BC7 now on the lowest crew member (no cooldown)
//   .dbtest zf blyfight res           BC12 Murta's Resurrection now (somebody must be out)
//   .dbtest zf blyfight stash         the stash chest now (section 7 #19 A)
// The fight itself: `.dbtest zf crew path 1|2`, then `.dbtest zf band start` (CR).
// --------------------------------------------------------------------------------------------------------------------
namespace
{
    using Mech = CrewFightHandler::TestMechanic;

    CrewFightHandler* MemberHandler(ChatHandler* handler, uint32 member)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return nullptr;
        Creature* crew = CrewCreature(instance, member);
        CrewFightHandler* h = HandlerOf(crew);
        if (!h)
            handler->SendErrorMessage("{} has no crew fight handler (not in the world, or never in Boss mode: start "
                "the fight with .dbtest zf crew path 1, then .dbtest zf band start).", NameOf(member));
        return h;
    }

    bool Fire(ChatHandler* handler, uint32 member, Mech mechanic, char const* what)
    {
        CrewFightHandler* h = MemberHandler(handler, member);
        if (!h)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayer() : nullptr;
        std::string const error = h->TestFire(mechanic, who);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Bly's crew: {} fired.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_BLY, BOSS_CREW);
    }

    bool HandleState(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        ZfTest::PrintRunState(handler, instance);
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (CrewFightHandler* h = HandlerOf(CrewCreature(instance, m)))
            {
                handler->PSendSysMessage("Bly's crew: {}", h->TestState());
                return true;
            }
        handler->PSendSysMessage("Bly's crew: no fight handler yet (never pulled).");
        return true;
    }

    bool HandleGangUp(ChatHandler* handler)
    {
        return Fire(handler, CREW_BLY, Mech::GangUp, "Gang Up (BC1)");
    }

    bool HandleBodyguard(ChatHandler* handler)
    {
        return Fire(handler, CREW_BLY, Mech::Bodyguard, "Bodyguard (BC2)");
    }

    bool HandleAmbush(ChatHandler* handler)
    {
        return Fire(handler, CREW_RAVEN, Mech::Ambush, "Ambush (BC4)");
    }

    bool HandleGouge(ChatHandler* handler)
    {
        return Fire(handler, CREW_RAVEN, Mech::Gouge, "Gouge (BC6)");
    }

    bool HandleRain(ChatHandler* handler)
    {
        return Fire(handler, CREW_ORO, Mech::Rain, "Rain of Fire (BC8)");
    }

    bool HandleSeed(ChatHandler* handler)
    {
        return Fire(handler, CREW_ORO, Mech::Seed, "Seed of Corruption (BC9)");
    }

    bool HandleHeal(ChatHandler* handler)
    {
        return Fire(handler, CREW_MURTA, Mech::GreaterHeal, "Greater Heal (BC7)");
    }

    bool HandleRes(ChatHandler* handler)
    {
        return Fire(handler, CREW_MURTA, Mech::Resurrection, "Resurrection (BC12)");
    }

    bool HandleStash(ChatHandler* handler)
    {
        return Fire(handler, CREW_BLY, Mech::Stash, "the stash chest");
    }

    ChatCommandTable const& BlyfightTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "gangup",    HandleGangUp,    SEC_GAMEMASTER, Console::No },
            { "bodyguard", HandleBodyguard, SEC_GAMEMASTER, Console::No },
            { "ambush",    HandleAmbush,    SEC_GAMEMASTER, Console::No },
            { "gouge",     HandleGouge,     SEC_GAMEMASTER, Console::No },
            { "rain",      HandleRain,      SEC_GAMEMASTER, Console::No },
            { "seed",      HandleSeed,      SEC_GAMEMASTER, Console::No },
            { "heal",      HandleHeal,      SEC_GAMEMASTER, Console::No },
            { "res",       HandleRes,       SEC_GAMEMASTER, Console::No },
            { "stash",     HandleStash,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_bly_crew_fight_rework()
{
    // The four fighters' Boss and Yielded modes (Weegli never fights). Bly's gossip, the betrayal lines and the fight
    // start stay CR's default (bots take option 0 = the betrayal, DC-1).
    ZfCrew::RegisterCrewModeHandler(CrewMode::Boss,
        [](BlyCrewAI& ai) { return std::make_unique<CrewFightHandler>(ai, CrewMode::Boss); }, kCrewFighters);
    ZfCrew::RegisterCrewModeHandler(CrewMode::Yielded,
        [](BlyCrewAI& ai) { return std::make_unique<CrewFightHandler>(ai, CrewMode::Yielded); }, kCrewFighters);
    ZfTest::RegisterBoss("blyfight", BlyfightTestCommands());
}
