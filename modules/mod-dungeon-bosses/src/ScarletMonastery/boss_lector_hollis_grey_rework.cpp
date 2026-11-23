/*
 * mod-dungeon-bosses, Scarlet Monastery D7: Lector Hollis Grey <Keeper of the Index>, the Librarian (300913), a new
 * boss in the reading hall. Build spec LIB "Lector Hollis Grey, the Librarian" (docs/dungeons/
 * scarlet-monastery-2-library.md, LB1-LB9; hub rulings 22, 25, 26), handoff sections 3.4 (F3, F8, F9, F45), 3.5 row
 * D7, 3.6, 3.8, 3.10 and section 7 #26 A (he stands in the pocket (254.8, -389.2): the doc's spot is a 3 yd aisle).
 * The creatures, spells and the ward are declared by apps/dbc-tools source/npcs/scarlet_monastery/hollis_grey.py, his
 * spawn and texts by rev_hollis_grey_scarlet_monastery.sql. Pure rules: HollisGreyLogic.h.
 *
 * The Forbidden Shelf. On a timer he opens a cursed book from his shelf (a shuffled shelf of six, no repeat until all
 * six are read) and throws it 10 to 20 yd off, where it hangs open at chest height and pours its story into the hall
 * until the group destroys it:
 *
 *   boss_lector_hollis_grey_rework  LB1 Open the Index (a 2 s bar and the book's emote; heroic a 3 s cast and an
 *                  expected kick: missed, the book opens on page 2), LB1a every open book turns a page every 10 s
 *                  (normal stops at page 3) and its story grows, LB1b Reader's Ward (-25% damage taken per open book,
 *                  50% / 75% at most: the kit's WardOfTheLiving), LB8 Searing Rebuke on the tank (a reward kick), the
 *                  six stories LB2-LB7 (each runs on its book's clock here: every zone and hit is registered by him,
 *                  so the reference row is his and the tank is his target), LB9 heroic: a destroyed book leaves a 5 yd
 *                  fire for the rest of the fight. Normal: no new book while 2 are open
 *   npc_sm_cursed_book  a rooted, passive kill target hanging over the floor; its death closes its story (the boss's
 *                  SummonedCreatureDies): every web, mist, add and pending hit of that book goes with it
 *   npc_sm_hollis_story_add  the Infernal (LB3, Immolation every 2 s) and the Spiderlings (LB2): the nearest tank
 *                  first (rule 19), never home while he fights, gone with their book
 *   npc_sm_hollis_phantom  the Spectral Troll (LB4) and the Phantom Grunt (LB7): looks that throw and charge; the
 *                  registry owns their hits
 *   spell_sm_hollis_dreaming  LB6a heroic: a Dreaming that runs out (nobody dispelled it) tells him: a 2 s sleep and a
 *                  new 6 yd mist at the player's spot until the book closes
 *
 * Every firing logs one INFO line "sm hollis <mechanic> ..." (module.dungeonbosses). The looks on stalkers (webs,
 * fires, the falling infernal) use the shared stalker NPC_SM_STALKER and are only looks: the fight plays without them
 * while its template is not declared.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitWard.h"
#include "DungeonKitZones.h"
#include "HollisGreyLogic.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <deque>
#include <list>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmHollisGrey;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "hollis";

    int32 constexpr GUID_DREAMING_MISSED = 1;       // SetGUID id: a Dreaming ran out on this player
    uint32 constexpr POINT_GRUNT_CHARGE = 1;
    float constexpr kFloorBandYd = 3.f;             // a floor probe further off than this is a table top or a hole
    float constexpr kOpeningThreat = 10.f;          // an add's first target
    float constexpr kArrivalSearchYd = 60.f;
    float constexpr kSpiderlingScatterYd = 2.f;
    uint32 constexpr kMeteorLookLifeMs = 5000;
    uint32 constexpr kForeverMs = 3600000;          // "until the book closes" / "for the rest of the fight"

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    // `rand(n)` for the pure picks: [0, n).
    uint32 Below(uint32 n)
    {
        return n ? urand(0, n - 1) : 0;
    }

    void LogLb(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    // The floor under (x, y): the map's height near `refZ`, else the hall's floor.
    float FloorZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > kFloorBandYd)
            return kHollisGreyPocket.z;
        return h;
    }

    // The bots' planned spots stay on the hall's floor while he fights (rule 12).
    BossMechanics::SpotBounds HallBounds()
    {
        std::vector<Position> points;
        for (Vec2 const& v : kHallBounds)
            points.emplace_back(v.x, v.y, kHollisGreyPocket.z, 0.f);
        BossMechanics::SpotBounds bounds;
        bounds.Polygon(std::move(points), kHallZMin, kHallZMax);
        return bounds;
    }

    // The lines' clip (LB4 axes, LB7 charges): the hall's navmesh rectangle.
    DungeonKit::Arena HallClip()
    {
        return DungeonKit::Arena(BoxRegion(247.75f, 282.25f, -418.75f, -344.25f, 15.f, 25.f));
    }

    // An add's first target (rule 19): the nearest tank within 60 yd, else the nearest player.
    Player* ArrivalTarget(Creature* add)
    {
        std::vector<Player*> players;
        std::vector<ArrivalCandidate> candidates;
        for (auto const& ref : add->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p || !p->IsAlive() || p->IsGameMaster() || !add->IsWithinDistInMap(p, kArrivalSearchYd)
                || !add->IsValidAttackTarget(p))
                continue;
            ArrivalCandidate c;
            c.distance = add->GetDistance(p);
            c.tank = BossMechanics::GetRoleProvider().Get(add, p) == BossMechanics::Role::Tank;
            players.push_back(p);
            candidates.push_back(c);
        }
        int const pick = PickArrival(candidates);
        return pick < 0 ? nullptr : players[static_cast<std::size_t>(pick)];
    }

    Creature* SummonerOf(Creature const* me)
    {
        if (TempSummon const* summon = me->ToTempSummon())
            if (Unit* summoner = summon->GetSummonerUnit())
                return summoner->ToCreature();
        return nullptr;
    }

    bool SummonerFighting(Creature const* me)
    {
        Creature const* boss = SummonerOf(me);
        return boss && boss->IsAlive() && boss->IsEngaged();
    }

    // The test commands' forced mechanics (`.dbtest sm hollis ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        Open,
        Page,
        Rebuke,
        Close,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// Cursed Book 300914: a rooted, passive kill target over the floor. Its death is Hollis Grey's (SummonedCreatureDies).
// ---------------------------------------------------------------------------------------------------------------------
struct npc_sm_cursed_book : public ScriptedAI
{
    explicit npc_sm_cursed_book(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetCombatMovement(false);
        me->SetDisableGravity(true);
        me->SetControlled(true, UNIT_STATE_ROOT);
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_KNOCK_BACK, true);
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_KNOCK_BACK_DEST, true);
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_PULL_TOWARDS, true);
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_PULL_TOWARDS_DEST, true);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // A book stays open while he fights (no walk home, no reset of its health or its page).
    void EnterEvadeMode(EvadeReason why) override
    {
        if (SummonerFighting(me))
            return;
        ScriptedAI::EnterEvadeMode(why);
    }

    void UpdateAI(uint32 /*diff*/) override { }
};

// ---------------------------------------------------------------------------------------------------------------------
// Infernal 300915 (LB3) and Spiderling 300916 (LB2): melee adds of a story. The nearest tank first; the Infernal burns
// what stands within 5 yd every 2 s. They fade with their book (the boss despawns them).
// ---------------------------------------------------------------------------------------------------------------------
struct npc_sm_hollis_story_add : public ScriptedAI
{
    explicit npc_sm_hollis_story_add(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _immolateMs = kImmolationEveryMs;
        me->SetReactState(REACT_AGGRESSIVE);
    }

    // Into the fight on the nearest tank (else the nearest player).
    void Arrive()
    {
        if (SummonerFighting(me))
            DoZoneInCombat();
        if (Player* target = ArrivalTarget(me))
        {
            me->AddThreat(target, kOpeningThreat);
            AttackStart(target);
        }
    }

    // While he fights, an add never walks home on its own (a target lost for a moment): back into his fight.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (SummonerFighting(me))
        {
            DoZoneInCombat();
            if (me->IsEngaged())
                return;
        }
        ScriptedAI::EnterEvadeMode(why);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (me->GetEntry() == NPC_SM_INFERNAL)
        {
            if (_immolateMs <= diff)
            {
                me->CastSpell(me, SPELL_LB_IMMOLATION, true);
                _immolateMs = kImmolationEveryMs;
            }
            else
                _immolateMs -= diff;
        }
        DoMeleeAttackIfReady();
    }

private:
    uint32 _immolateMs = kImmolationEveryMs;
};

// ---------------------------------------------------------------------------------------------------------------------
// Spectral Troll 300917 (LB4) and Phantom Grunt 300918 (LB7): not targetable looks. They never fight; the boss moves
// the grunt along its line and has the troll throw its axes (looks only: the registry owns every hit).
// ---------------------------------------------------------------------------------------------------------------------
struct npc_sm_hollis_phantom : public ScriptedAI
{
    explicit npc_sm_hollis_phantom(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetCombatMovement(false);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

namespace
{
    npc_sm_hollis_story_add* StoryAddAI(Creature* creature)
    {
        if (!creature || !creature->IsAlive() || !creature->IsAIEnabled)
            return nullptr;
        return dynamic_cast<npc_sm_hollis_story_add*>(creature->AI());
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Lector Hollis Grey 300913
// ---------------------------------------------------------------------------------------------------------------------
struct boss_lector_hollis_grey_rework : public BossAI
{
    explicit boss_lector_hollis_grey_rework(Creature* creature)
        : BossAI(creature, BOSS_HOLLIS_GREY), _arena(HollisGreyArena(), LeashOptions(kBoss)), _clip(HallClip()) { }

    // LB2: one web of a War of the Spider book.
    struct Web
    {
        MechanicHandle zone;
        ObjectGuid stalker;
        Position at;
        uint64 hatchAtMs = 0;
        uint32 hatch = 0;
        bool hatched = false;
    };

    // LB3: one falling meteor.
    struct Meteor
    {
        Position at;
        uint64 lookAtMs = 0;
        uint64 landAtMs = 0;
        bool looked = false;
    };

    // LB4 / LB5: a look due later (the axe leaving the troll's hand, a ring of the stomp).
    struct LookDue
    {
        uint64 atMs = 0;
        ObjectGuid target;          // LB4: the player the axe flies at
        Position at;                // LB4: where the line was aimed
        uint32 spell = 0;
    };

    // LB7: one phantom grunt.
    struct Grunt
    {
        ObjectGuid guid;
        Position end;
        uint64 runAtMs = 0;
        uint64 fadeAtMs = 0;
        bool running = false;
    };

    // One open book and everything its story made.
    struct Book
    {
        ObjectGuid guid;
        Story story = Story::Spider;
        uint8 page = 1;
        Position floor;             // the floor under it (the stomp's and the charge's source, the heroic fire)
        uint64 openedAtMs = 0;
        uint64 nextPageAtMs = 0;
        uint64 nextAtMs = 0;        // the story's next firing
        std::vector<MechanicHandle> handles;
        std::deque<Web> webs;
        std::vector<Meteor> meteors;
        std::vector<LookDue> looks;
        std::vector<Grunt> grunts;
        std::vector<ObjectGuid> adds;           // Infernals, Spiderlings
        std::vector<ObjectGuid> stalkers;       // looks this book raised (meteor spots)
        ObjectGuid troll;
        DungeonKit::GrowingZone mist;           // LB6
        std::deque<DungeonKit::GrowingZone> dreamMists;     // LB6a heroic: the missed Dreamings' mists
        std::vector<ObjectGuid> dreamers;       // LB6a heroic: players carrying this book's Dreaming
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();       // despawns every book, add and look (BossAI summons)
        Cleanup("reset");
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        StartFight();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogLb("evade", Acore::StringFormat("reason={} books={}", uint32(why), _books.size()));
        Cleanup("evade");
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(SAY_LB_DEATH);
        Cleanup("death");
        BossAI::JustDied(killer);
        LogLb("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : std::string("none")));
    }

    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        switch (summon->GetEntry())
        {
            case NPC_SM_CURSED_BOOK:
            case NPC_SM_INFERNAL:
            case NPC_SM_SPIDERLING:
                BossAI::JustSummoned(summon);   // into his fight when he is in one
                if (me->IsEngaged())
                    Mechanic::TrackUnit(me, summon);
                break;
            default:
                summons.Summon(summon);         // looks: despawned with him, never in combat
                break;
        }
    }

    // A destroyed book closes its story (LB1): everything it made goes; heroic, it falls burning (LB9).
    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        BossAI::SummonedCreatureDies(summon, killer);
        if (!summon || summon->GetEntry() != NPC_SM_CURSED_BOOK)
            return;
        for (auto it = _books.begin(); it != _books.end(); ++it)
            if (it->guid == summon->GetGUID())
            {
                CloseBook(it, "destroyed", true);
                summon->DespawnOrUnsummon(Ms(1000));
                return;
            }
    }

    // LB1: the finished cast throws the book (heroic: nobody kicked it, page 2).
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (!spell)
            return;
        if (spell->Id == SPELL_LB_OPEN_THE_INDEX || spell->Id == SPELL_LB_OPEN_THE_INDEX_HEROIC)
            FinishOpen(false);
    }

    // LB1 heroic: a kicked Open the Index still throws the book, on page 1. LB8: a kicked Rebuke is the reward.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell)
            return;
        if (spell->Id == SPELL_LB_OPEN_THE_INDEX || spell->Id == SPELL_LB_OPEN_THE_INDEX_HEROIC)
            FinishOpen(true);
        else if (spell->Id == SPELL_LB_SEARING_REBUKE)
            LogLb("rebuke-kicked");
    }

    // LB6a heroic: a Dreaming ran out on `guid` (spell_sm_hollis_dreaming).
    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id == GUID_DREAMING_MISSED)
            DreamingMissed(guid);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // The books' stories run on their own clocks, also out of combat (`.dbtest sm hollis open` on an idle boss).
        if (me->IsAlive())
        {
            UpdateBooks(diff);
            UpdateDrowsy();
        }

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_fighting)
            return;

        _ward.Update(me, diff);
        RunTimers();
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pull
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight()
    {
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_HOLLIS_GREY;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        Talk(SAY_LB_AGGRO);
        _fighting = true;

        _shelf.Shuffle(Below);
        _openAtMs = _clockMs + kOpenFirstMs(_heroic);
        _rebukeAtMs = _clockMs + kRebukeFirstMs;
        StartWard();
        // Books thrown by a GM test before the pull join the fight.
        for (Book& b : _books)
            if (Creature* book = BookUnit(b))
            {
                DoZoneInCombat(book);
                Mechanic::TrackUnit(me, book);
                _ward.Link(me, book);
            }
        Mechanic::NoteNextCastIn(me, OpenSpell(), Ms(kOpenFirstMs(_heroic)));
        Mechanic::NoteNextCastIn(me, SPELL_LB_SEARING_REBUKE, Ms(kRebukeFirstMs));
        Describe();
        LogLb("engage", Acore::StringFormat("heroic={} first-book={} in={}ms", _heroic ? 1 : 0,
            StoryName(_shelf.Peek()), kOpenFirstMs(_heroic)));
    }

    void StartWard()
    {
        DungeonKit::WardSpec spec;
        spec.aura = SPELL_LB_READERS_WARD;
        spec.pctPerAdd = kWardPctPerBook;
        spec.capPct = kWardCapPct(_heroic);
        spec.dungeon = kLogDungeon;
        spec.boss = kBoss;
        _ward.Stop(me);
        _ward.Start(me, std::move(spec));
    }

    uint32 OpenSpell() const
    {
        return _heroic ? SPELL_LB_OPEN_THE_INDEX_HEROIC : SPELL_LB_OPEN_THE_INDEX;
    }

    void RunTimers()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_clockMs >= _openAtMs && StartOpen("timer"))
            return;
        if (_clockMs >= _rebukeAtMs)
            CastRebuke();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB1 Open the Index
    // ----------------------------------------------------------------------------------------------------------------

    // The cast and the book's emote. False when he could not start it (the cap, a refused cast): he tries again in 1 s.
    bool StartOpen(char const* why)
    {
        if (!MayOpenBook(static_cast<uint32>(_books.size()), _heroic))
        {
            if (!_capLogged)
                LogLb("open-held", Acore::StringFormat("open={} cap={}", _books.size(), kOpenBooksCapNormal));
            _capLogged = true;
            _openAtMs = _clockMs + kRetryMs;
            return false;
        }
        _capLogged = false;
        Story const story = _shelf.Peek();
        me->StopMoving();
        if (me->CastSpell(me, OpenSpell(), false) != SPELL_CAST_OK)
        {
            _openAtMs = _clockMs + kRetryMs;
            return false;
        }
        _shelf.Take(Below);
        _casting = true;
        _castStory = story;
        Talk(StoryText(story));
        _openAtMs = _clockMs + kOpenEveryMs(_heroic);
        Mechanic::NoteNextCastIn(me, OpenSpell(), Ms(kOpenEveryMs(_heroic)));
        LogLb("open-cast", Acore::StringFormat("why={} story={} cast={}ms heroic={} open={}", why, StoryName(story),
            kOpenCastMs(_heroic), _heroic ? 1 : 0, _books.size()));
        return true;
    }

    void FinishOpen(bool kicked)
    {
        if (!_casting)
            return;
        _casting = false;
        if (!me->IsAlive() || me->GetHealth() == 0)
            return;     // he died mid-cast: the book never leaves his hands
        uint8 const page = OpeningPage(_heroic, kicked);
        if (kicked)
            LogLb("open-kicked", Acore::StringFormat("story={} page={}", StoryName(_castStory), page));
        Throw(_castStory, page);
    }

    // The book flies 10 to 20 yd off and hangs open at chest height; its story starts.
    void Throw(Story story, uint8 page)
    {
        std::vector<Vec2> open;
        for (Book const& b : _books)
            open.push_back(Vec2{ b.floor.GetPositionX(), b.floor.GetPositionY() });
        Vec2 const from = DungeonKit::PlaneOf(me);
        std::optional<std::size_t> const pick = PickThrowSpot(from, kHallFloor, open, Below);
        if (!pick)
            return;
        Point3 const& spot = kHallFloor[*pick];
        float const z = FloorZ(me, spot.x, spot.y, spot.z);
        float const facing = DungeonKit::BearingTo(spot.XY(), from);
        Creature* book = me->SummonCreature(NPC_SM_CURSED_BOOK, spot.x, spot.y, z + kBookHoverYd, facing,
            TEMPSUMMON_MANUAL_DESPAWN);
        if (!book)
        {
            LogLb("open-failed", Acore::StringFormat("story={} why=no-summon", StoryName(story)));
            return;
        }
        book->SetDisableGravity(true);
        book->CastSpell(book, StorySpell(story), true);

        Book b;
        b.guid = book->GetGUID();
        b.story = story;
        b.page = page;
        b.floor = Position(spot.x, spot.y, z, facing);
        b.openedAtMs = _clockMs;
        b.nextPageAtMs = _clockMs + kPageEveryMs;
        _books.push_back(std::move(b));
        Book& added = _books.back();
        ShowPage(added);
        if (_fighting)
            _ward.Link(me, book);
        StartStory(added);
        LogLb("open", Acore::StringFormat("story={} page={} at=({:.1f}, {:.1f}) distance={:.1f} open={}",
            StoryName(story), page, spot.x, spot.y, DungeonKit::Distance(from, spot.XY()), _books.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB8 Searing Rebuke
    // ----------------------------------------------------------------------------------------------------------------

    void CastRebuke()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
        {
            _rebukeAtMs = _clockMs + kRetryMs;
            return;
        }
        me->StopMoving();
        if (me->CastSpell(victim, SPELL_LB_SEARING_REBUKE, false) != SPELL_CAST_OK)
        {
            _rebukeAtMs = _clockMs + kRetryMs;
            return;
        }
        _rebukeAtMs = _clockMs + kRebukeEveryMs;
        Mechanic::NoteNextCastIn(me, SPELL_LB_SEARING_REBUKE, Ms(kRebukeEveryMs));
        LogLb("rebuke", Acore::StringFormat("target={} pct={:.0f}", victim->GetName(), kRebukePct(_heroic)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The books: pages, stories, closing
    // ----------------------------------------------------------------------------------------------------------------

    Creature* BookUnit(Book const& b) const
    {
        Creature* book = ObjectAccessor::GetCreature(*me, b.guid);
        return book && book->IsAlive() ? book : nullptr;
    }

    // LB1a: the page count on the book (the stacks of Turning the Page; the kill order reads it).
    void ShowPage(Book const& b)
    {
        Creature* book = BookUnit(b);
        if (!book)
            return;
        Aura* aura = book->GetAura(SPELL_LB_TURNING_THE_PAGE);
        if (!aura)
            aura = book->AddAura(SPELL_LB_TURNING_THE_PAGE, book);
        if (aura)
            aura->SetStackAmount(std::min<uint8>(b.page, kMaxShownPage));
    }

    void StartStory(Book& b)
    {
        switch (b.story)
        {
            case Story::Spider:
                b.nextAtMs = _clockMs + kWebFirstMs;
                break;
            case Story::Archimonde:
                b.nextAtMs = _clockMs + kMeteorFirstMs;
                break;
            case Story::TrollWars:
                RaiseTroll(b);
                b.nextAtMs = _clockMs + kAxeFirstMs;
                break;
            case Story::Titans:
                b.nextAtMs = _clockMs + kStompFirstMs;
                break;
            case Story::Dream:
                StartMist(b);
                b.nextAtMs = 0;     // the mist grows by page, nothing on a clock
                if (_heroic)
                    Dreaming(b);
                break;
            case Story::Aftermath:
                b.nextAtMs = _clockMs + kChargeFirstMs;
                break;
        }
    }

    void UpdateBooks(uint32 diff)
    {
        for (auto it = _books.begin(); it != _books.end();)
        {
            Book& b = *it;
            if (!BookUnit(b))
            {
                CloseBook(it++, "gone", false);     // despawned without a death (a GM, a grid unload)
                continue;
            }
            // LB1a: a page every 10 s it stays open.
            if (_clockMs >= b.nextPageAtMs)
            {
                b.nextPageAtMs += kPageEveryMs;
                uint8 const next = NextPage(b.page, _heroic);
                if (next != b.page)
                    TurnPage(b, next);
            }
            if (b.nextAtMs && _clockMs >= b.nextAtMs)
                FireStory(b);
            UpdatePending(b);
            b.mist.Update(me, diff);
            for (DungeonKit::GrowingZone& z : b.dreamMists)
                z.Update(me, diff);
            ++it;
        }
    }

    void TurnPage(Book& b, uint8 page)
    {
        b.page = page;
        ShowPage(b);
        if (b.story == Story::Dream)
        {
            b.mist.GrowTo(me, MistRadius(page));
            if (_heroic)
                Dreaming(b);
        }
        LogLb("page", Acore::StringFormat("story={} page={}", StoryName(b.story), page));
    }

    void FireStory(Book& b)
    {
        switch (b.story)
        {
            case Story::Spider:
                SprayWeb(b);
                b.nextAtMs = _clockMs + kWebEveryMs;
                break;
            case Story::Archimonde:
                CallMeteors(b);
                b.nextAtMs = _clockMs + kMeteorEveryMs;
                break;
            case Story::TrollWars:
                ThrowAxes(b);
                b.nextAtMs = _clockMs + kAxeEveryMs;
                break;
            case Story::Titans:
                Stomp(b);
                b.nextAtMs = _clockMs + kStompEveryMs;
                break;
            case Story::Aftermath:
                Charge(b);
                b.nextAtMs = _clockMs + kChargeEveryMs;
                break;
            case Story::Dream:
                b.nextAtMs = 0;
                break;
        }
    }

    // Hatches, the falling infernals, the axes' and rings' looks, the grunts' runs.
    void UpdatePending(Book& b)
    {
        Creature* book = BookUnit(b);
        for (Web& w : b.webs)
            if (!w.hatched && _clockMs >= w.hatchAtMs)
                Hatch(b, w);

        for (auto it = b.meteors.begin(); it != b.meteors.end();)
        {
            if (!it->looked && _clockMs >= it->lookAtMs)
            {
                it->looked = true;
                if (TempSummon* look = me->SummonCreature(NPC_SM_STALKER, it->at, TEMPSUMMON_TIMED_DESPAWN,
                    kMeteorLookLifeMs))
                    look->CastSpell(look, SPELL_LB_INFERNO, true);
            }
            if (_clockMs >= it->landAtMs)
            {
                RaiseInfernal(b, it->at);
                it = b.meteors.erase(it);
            }
            else
                ++it;
        }

        for (auto it = b.looks.begin(); it != b.looks.end();)
        {
            if (_clockMs < it->atMs)
            {
                ++it;
                continue;
            }
            if (it->spell == SPELL_LB_THROW_AXE_LOOK)
            {
                Creature* troll = ObjectAccessor::GetCreature(*me, b.troll);
                Player* target = ObjectAccessor::GetPlayer(*me, it->target);
                if (troll && target && target->IsAlive())
                {
                    troll->SetFacingToObject(target);
                    troll->CastSpell(target, SPELL_LB_THROW_AXE_LOOK, true);
                }
            }
            else if (book)
                book->CastSpell(book, it->spell, true);
            it = b.looks.erase(it);
        }

        for (auto it = b.grunts.begin(); it != b.grunts.end();)
        {
            Creature* grunt = ObjectAccessor::GetCreature(*me, it->guid);
            if (!grunt)
            {
                it = b.grunts.erase(it);
                continue;
            }
            if (!it->running && _clockMs >= it->runAtMs)
            {
                it->running = true;
                float const dist = grunt->GetExactDist2d(it->end.GetPositionX(), it->end.GetPositionY());
                grunt->CastSpell(grunt, SPELL_LB_CHARGE_LOOK, true);
                grunt->GetMotionMaster()->MovePoint(POINT_GRUNT_CHARGE, it->end.GetPositionX(),
                    it->end.GetPositionY(), it->end.GetPositionZ(), FORCED_MOVEMENT_NONE, kChargeSpeedYd, 0.f, false);
                it->fadeAtMs = _clockMs + static_cast<uint64>(dist / kChargeSpeedYd * 1000.f) + kGruntFadeMs;
            }
            if (it->running && _clockMs >= it->fadeAtMs)
            {
                grunt->DespawnOrUnsummon();
                it = b.grunts.erase(it);
            }
            else
                ++it;
        }
    }

    // LB1: a book's story ends. `burn`: it was destroyed in the fight (heroic: a fire where it fell, LB9).
    void CloseBook(std::list<Book>::iterator it, char const* why, bool burn)
    {
        Book& b = *it;
        for (MechanicHandle const& h : b.handles)
            Mechanic::Cancel(me, h);
        b.mist.Cancel(me);
        for (DungeonKit::GrowingZone& z : b.dreamMists)
            z.Cancel(me);
        for (Web const& w : b.webs)
            Despawn(w.stalker);
        for (Grunt const& g : b.grunts)
            Despawn(g.guid);
        uint32 adds = 0;
        for (ObjectGuid const& guid : b.adds)
            if (Despawn(guid))
                ++adds;
        for (ObjectGuid const& guid : b.stalkers)
            Despawn(guid);
        Despawn(b.troll);
        for (ObjectGuid const& guid : b.dreamers)
            if (Player* p = ObjectAccessor::GetPlayer(*me, guid))
                p->RemoveAurasDueToSpell(SPELL_LB_DREAMING, me->GetGUID());
        bool const fire = burn && _heroic && _fighting;
        if (fire)
            BurningBook(b.floor);
        LogLb("close", Acore::StringFormat("why={} story={} page={} open={}s adds={} fire={}", why,
            StoryName(b.story), b.page, (_clockMs - b.openedAtMs) / 1000, adds, fire ? 1 : 0));
        _books.erase(it);
    }

    // True when it was there to despawn.
    bool Despawn(ObjectGuid const& guid)
    {
        if (guid.IsEmpty())
            return false;
        Creature* c = ObjectAccessor::GetCreature(*me, guid);
        if (!c)
            return false;
        bool const alive = c->IsAlive();
        c->DespawnOrUnsummon();
        return alive;
    }

    // A random player in his fight (the tank too); out of combat the GM of a test command.
    Player* RandomPlayer()
    {
        if (!me->IsEngaged())
            return _testPlayer.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _testPlayer);
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        return DungeonKit::PickPlayer(me, rule);
    }

    // `count` distinct random players (the tank too); out of combat the GM.
    std::vector<Player*> RandomPlayers(uint32 count)
    {
        if (!me->IsEngaged())
        {
            std::vector<Player*> out;
            if (Player* p = RandomPlayer())
                out.push_back(p);
            return out;
        }
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        return DungeonKit::PickPlayers(me, rule, count);
    }

    // An Infernal or a Spiderling of `b` comes into the fight.
    void Arrive(Creature* add)
    {
        if (npc_sm_hollis_story_add* ai = StoryAddAI(add))
            ai->Arrive();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB2 War of the Spider
    // ----------------------------------------------------------------------------------------------------------------

    void SprayWeb(Book& b)
    {
        Player* target = RandomPlayer();
        if (!target)
            return;
        Position const at = target->GetPosition();
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(at, kWebRadiusYd), Ms(kWebWarnMs));
        ref.Persistent(Ms(kForeverMs), Ms(kWebTickMs)).Rider(SPELL_LB_WEB_SLOW).Spell(SPELL_LB_WEB)
            .Within(HallBounds()).Tag(TAG_LB_WEB);
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return;
        b.handles.push_back(handle);

        Web w;
        w.zone = handle;
        w.at = at;
        w.hatchAtMs = _clockMs + kWebWarnMs;
        w.hatch = SpiderlingsPerWeb(b.page);
        if (TempSummon* stalker = me->SummonCreature(NPC_SM_STALKER, at, TEMPSUMMON_MANUAL_DESPAWN))
        {
            w.stalker = stalker->GetGUID();
            if (Creature* book = BookUnit(b))
                book->CastSpell(stalker, SPELL_LB_WEB_SPRAY, true);
        }
        b.webs.push_back(w);
        bool faded = false;
        if (WebsOverCap(static_cast<uint32>(b.webs.size()), _heroic))
        {
            Web const oldest = b.webs.front();
            b.webs.pop_front();
            Mechanic::Cancel(me, oldest.zone);
            Despawn(oldest.stalker);
            faded = true;
        }
        LogLb("web", Acore::StringFormat("target={} at=({:.1f}, {:.1f}) page={} hatch={} webs={} faded={}",
            target->GetName(), at.GetPositionX(), at.GetPositionY(), b.page, w.hatch, b.webs.size(), faded ? 1 : 0));
    }

    void Hatch(Book& b, Web& w)
    {
        w.hatched = true;
        if (Creature* stalker = ObjectAccessor::GetCreature(*me, w.stalker))
        {
            stalker->CastSpell(stalker, SPELL_LB_WEB_PATCH, true);
            stalker->CastSpell(stalker, SPELL_LB_HATCH, true);
        }
        uint32 hatched = 0;
        for (uint32 i = 0; i < w.hatch; ++i)
        {
            float const angle = frand(0.f, 2.f * float(M_PI));
            float const r = frand(0.f, kSpiderlingScatterYd);
            float const x = w.at.GetPositionX() + std::cos(angle) * r;
            float const y = w.at.GetPositionY() + std::sin(angle) * r;
            float const z = FloorZ(me, x, y, w.at.GetPositionZ());
            Creature* spider = me->SummonCreature(NPC_SM_SPIDERLING, x, y, z, angle, TEMPSUMMON_MANUAL_DESPAWN);
            if (!spider)
                continue;
            b.adds.push_back(spider->GetGUID());
            Arrive(spider);
            ++hatched;
        }
        LogLb("hatch", Acore::StringFormat("spiderlings={}", hatched));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB3 Archimonde's Return
    // ----------------------------------------------------------------------------------------------------------------

    void CallMeteors(Book& b)
    {
        float const pct = kMeteorPct(_heroic);
        std::vector<Player*> const targets = RandomPlayers(MeteorsPerFall(b.page));
        for (Player* target : targets)
        {
            Position const at = target->GetPosition();
            MechanicRef ref = Mechanic::Circle(me, at, kMeteorRadiusYd, Ms(kMeteorWarnMs));
            ref.Damage(pct).TankDamage(pct).Spell(SPELL_LB_METEOR).Within(HallBounds()).Tag(TAG_LB_METEOR);
            MechanicHandle const handle = ref.Handle();
            if (!handle)
                continue;
            b.handles.push_back(handle);
            Meteor m;
            m.at = at;
            m.lookAtMs = _clockMs + kMeteorWarnMs - kMeteorLookLeadMs;
            m.landAtMs = _clockMs + kMeteorWarnMs;
            b.meteors.push_back(m);
            LogLb("meteor", Acore::StringFormat("target={} at=({:.1f}, {:.1f}) page={} pct={:.0f}", target->GetName(),
                at.GetPositionX(), at.GetPositionY(), b.page, pct));
        }
    }

    uint32 AliveInfernals(Book const& b) const
    {
        uint32 alive = 0;
        for (ObjectGuid const& guid : b.adds)
            if (Creature* c = ObjectAccessor::GetCreature(*me, guid))
                if (c->IsAlive() && c->GetEntry() == NPC_SM_INFERNAL)
                    ++alive;
        return alive;
    }

    void RaiseInfernal(Book& b, Position const& at)
    {
        uint32 const alive = AliveInfernals(b);
        if (!InfernalMayRise(alive, _heroic))
        {
            LogLb("infernal-capped", Acore::StringFormat("alive={}", alive));
            return;
        }
        float const z = FloorZ(me, at.GetPositionX(), at.GetPositionY(), at.GetPositionZ());
        Creature* infernal = me->SummonCreature(NPC_SM_INFERNAL, at.GetPositionX(), at.GetPositionY(), z,
            at.GetOrientation(), TEMPSUMMON_MANUAL_DESPAWN);
        if (!infernal)
            return;
        b.adds.push_back(infernal->GetGUID());
        Arrive(infernal);
        LogLb("infernal", Acore::StringFormat("alive={}", alive + 1));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB4 Arathor and the Troll Wars
    // ----------------------------------------------------------------------------------------------------------------

    void RaiseTroll(Book& b)
    {
        Vec2 const bookXY{ b.floor.GetPositionX(), b.floor.GetPositionY() };
        Vec2 const at = DungeonKit::Advance(bookXY, DungeonKit::BearingTo(bookXY, DungeonKit::PlaneOf(me)),
            kTrollOffsetYd);
        float const z = FloorZ(me, at.x, at.y, b.floor.GetPositionZ());
        if (TempSummon* troll = me->SummonCreature(NPC_SM_SPECTRAL_TROLL, at.x, at.y, z,
            DungeonKit::BearingTo(at, DungeonKit::PlaneOf(me)), TEMPSUMMON_MANUAL_DESPAWN))
            b.troll = troll->GetGUID();
    }

    void ThrowAxes(Book& b)
    {
        Creature* troll = ObjectAccessor::GetCreature(*me, b.troll);
        Position const from = troll ? troll->GetPosition() : b.floor;
        float const pct = kAxePct(_heroic);
        uint32 lines = 0;
        for (Player* target : RandomPlayers(AxesPerVolley(b.page)))
        {
            Position const at = target->GetPosition();
            float const dist = from.GetExactDist2d(at.GetPositionX(), at.GetPositionY());
            DungeonKit::LineStrikeSpec spec;
            spec.width = kAxeWidthYd;
            spec.overrun = AxeOverrun(dist);
            spec.warn = Ms(kAxeWarnMs);
            spec.pct = pct;
            spec.tankPct = pct;
            spec.spellId = SPELL_LB_THROW_AXE;
            spec.weakened = true;
            spec.tag = TAG_LB_AXE;
            spec.clip = &_clip;
            DungeonKit::LineStrikeResult const res = DungeonKit::LineStrike(me, from, at, spec);
            if (!res.handle)
                continue;
            b.handles.push_back(res.handle);
            LookDue look;
            look.atMs = _clockMs + kAxeWarnMs - kAxeLookLeadMs;
            look.target = target->GetGUID();
            look.at = at;
            look.spell = SPELL_LB_THROW_AXE_LOOK;
            b.looks.push_back(look);
            ++lines;
        }
        LogLb("axes", Acore::StringFormat("page={} lines={} pct={:.0f}", b.page, lines, pct));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB5 Mythology of the Titans
    // ----------------------------------------------------------------------------------------------------------------

    void Stomp(Book& b)
    {
        float const pct = kStompPct(_heroic);
        uint8 const rings = StompRings(b.page);
        for (uint8 i = 0; i < rings; ++i)
        {
            StompRing const ring = StompRingAt(i);
            MechanicRef ref = i == 0 ? Mechanic::Circle(me, b.floor, ring.outer, Ms(ring.warnMs))
                : Mechanic::Donut(me, b.floor, ring.inner, ring.outer, Ms(ring.warnMs));
            ref.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_LB_TITAN_STOMP).Within(HallBounds())
                .Tag(TAG_LB_STOMP);
            if (MechanicHandle const handle = ref.Handle())
                b.handles.push_back(handle);
            LookDue look;
            look.atMs = _clockMs + ring.warnMs;
            look.spell = i == 0 ? SPELL_LB_WAR_STOMP : SPELL_LB_GROUND_SLAM;
            b.looks.push_back(look);
        }
        LogLb("stomp", Acore::StringFormat("page={} rings={} to={:.0f}yd pct={:.0f}", b.page, rings,
            StompRingAt(static_cast<uint8>(rings - 1)).outer, pct));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB6 The World Tree and the Emerald Dream
    // ----------------------------------------------------------------------------------------------------------------

    DungeonKit::GrowingZoneSpec MistSpec(BossMechanics::Anchor const& anchor, float radius) const
    {
        DungeonKit::GrowingZoneSpec spec;
        spec.anchor = anchor;
        spec.fromYd = radius;
        spec.toYd = radius;
        spec.warnMs = kMistWarnMs;
        spec.tickMs = kMistTickMs;
        spec.pct = 0.f;                 // no damage: the Drowsy rider is the mist's whole cost
        spec.spellId = SPELL_LB_DREAM_MIST;
        spec.rider = SPELL_LB_DROWSY;
        spec.tag = TAG_LB_MIST;
        spec.rungs = { { 6.f, SPELL_LB_DREAM_MIST_6 }, { 9.f, SPELL_LB_DREAM_MIST_9 },
            { 12.f, SPELL_LB_DREAM_MIST_12 } };
        spec.configure = [](MechanicRef& ref) { ref.Within(HallBounds()); };
        spec.dungeon = kLogDungeon;
        spec.boss = kBoss;
        spec.name = "dream-mist";
        return spec;
    }

    // The mist round the book (it follows the book's unit; the book wears the rung).
    void StartMist(Book& b)
    {
        Creature* book = BookUnit(b);
        if (!book)
            return;
        b.mist.Start(me, MistSpec(BossMechanics::Anchor(book), MistRadius(b.page)));
    }

    // LB6a heroic: the Magic debuff on a random player (an expected dispel), each page.
    void Dreaming(Book& b)
    {
        Player* target = RandomPlayer();
        if (!target)
            return;
        me->CastSpell(target, SPELL_LB_DREAMING, true);
        b.dreamers.push_back(target->GetGUID());
        LogLb("dreaming", Acore::StringFormat("target={} page={}", target->GetName(), b.page));
    }

    // A Dreaming ran out: a 2 s sleep and a new 6 yd mist at the player's spot until the book closes.
    void DreamingMissed(ObjectGuid const& guid)
    {
        for (Book& b : _books)
        {
            auto it = std::find(b.dreamers.begin(), b.dreamers.end(), guid);
            if (it == b.dreamers.end())
                continue;
            b.dreamers.erase(it);
            Player* player = ObjectAccessor::GetPlayer(*me, guid);
            if (!player || !player->IsAlive())
                return;
            me->CastSpell(player, SPELL_LB_DREAM_SLEEP, true);
            DungeonKit::GrowingZoneSpec spec = MistSpec(BossMechanics::Anchor(player->GetPosition()), kDreamingMistYd);
            spec.lookEntry = NPC_SM_STALKER;
            spec.name = "dreaming-mist";
            b.dreamMists.emplace_back();
            b.dreamMists.back().Start(me, std::move(spec));
            LogLb("dreaming-missed", Acore::StringFormat("player={} at=({:.1f}, {:.1f}) mists={}", player->GetName(),
                player->GetPositionX(), player->GetPositionY(), b.dreamMists.size()));
            return;
        }
    }

    // Drowsy: at five stacks the sleep; once a second a player outside every mist loses a stack.
    void UpdateDrowsy()
    {
        if (_clockMs < _drowsyCheckAtMs)
            return;
        _drowsyCheckAtMs = _clockMs + kDrowsyCheckMs;
        bool const decay = _clockMs >= _drowsyDecayAtMs;
        if (decay)
            _drowsyDecayAtMs = _clockMs + kDrowsyDecayMs;

        std::vector<MechanicHandle> mists;
        for (Book const& b : _books)
        {
            if (b.mist.Active())
                mists.push_back(b.mist.Handle());
            for (DungeonKit::GrowingZone const& z : b.dreamMists)
                if (z.Active())
                    mists.push_back(z.Handle());
        }

        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p)
                continue;
            Aura* aura = p->GetAura(SPELL_LB_DROWSY);
            if (!aura)
                continue;
            bool inside = false;
            for (MechanicHandle const& h : mists)
                if (Mechanic::Contains(me, h, p))
                    inside = true;
            uint8 const stacks = aura->GetStackAmount();
            DrowsyStep const step = DrowsyCheck(stacks, inside, decay);
            if (step.sleep)
            {
                p->RemoveAurasDueToSpell(SPELL_LB_DROWSY);
                me->CastSpell(p, SPELL_LB_DREAM_SLEEP, true);
                LogLb("dream-sleep", Acore::StringFormat("player={} stacks={}", p->GetName(), stacks));
            }
            else if (step.stacks == 0)
                p->RemoveAurasDueToSpell(SPELL_LB_DROWSY);
            else if (step.stacks != stacks)
                aura->SetStackAmount(step.stacks);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB7 Aftermath of the Second War
    // ----------------------------------------------------------------------------------------------------------------

    void Charge(Book& b)
    {
        float const pct = kChargePct(_heroic);
        uint32 lines = 0;
        for (Player* target : RandomPlayers(GruntsPerCharge(b.page)))
        {
            Position const at = target->GetPosition();
            DungeonKit::LineStrikeSpec spec;
            spec.width = kChargeWidthYd;
            spec.overrun = kChargeOverrunYd;
            spec.warn = Ms(kChargeWarnMs);
            spec.pct = pct;
            spec.tankPct = pct;
            spec.spellId = SPELL_LB_PHANTOM_CHARGE;
            spec.weakened = false;      // the charge is its own penalty
            spec.tag = TAG_LB_CHARGE;
            spec.clip = &_clip;
            DungeonKit::LineStrikeResult const res = DungeonKit::LineStrike(me, b.floor, at, spec);
            if (!res.handle)
                continue;
            b.handles.push_back(res.handle);
            ++lines;
            float const facing = DungeonKit::BearingTo(Vec2{ b.floor.GetPositionX(), b.floor.GetPositionY() },
                Vec2{ at.GetPositionX(), at.GetPositionY() });
            if (TempSummon* grunt = me->SummonCreature(NPC_SM_PHANTOM_GRUNT, b.floor.GetPositionX(),
                b.floor.GetPositionY(), b.floor.GetPositionZ(), facing, TEMPSUMMON_MANUAL_DESPAWN))
            {
                Grunt g;
                g.guid = grunt->GetGUID();
                g.end = res.end;
                g.runAtMs = _clockMs + kChargeWarnMs;
                b.grunts.push_back(g);
            }
        }
        LogLb("charge", Acore::StringFormat("page={} lines={} pct={:.0f}", b.page, lines, pct));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB9 Burning Book (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void BurningBook(Position const& at)
    {
        DungeonKit::LingerSpec linger;
        linger.duration = Ms(kForeverMs);
        linger.tick = Ms(kBurningBookTickMs);
        linger.pct = kBurningBookPct;
        linger.school = SPELL_SCHOOL_FIRE;
        linger.spellId = SPELL_LB_BURNING_BOOK;
        linger.slow = false;
        linger.tag = TAG_LB_BURNING_BOOK;
        MechanicRef ref = DungeonKit::Linger(me, BossMechanics::Shapes::Circle(at, kBurningBookYd), linger);
        ref.TankDamage(kBurningBookPct).Within(HallBounds());
        if (MechanicHandle const handle = ref.Handle())
            _fires.push_back(handle);
        if (TempSummon* look = me->SummonCreature(NPC_SM_STALKER, at, TEMPSUMMON_MANUAL_DESPAWN))
        {
            look->CastSpell(look, SPELL_LB_BURNING_BOOK_LOOK, true);
            _fireLooks.push_back(look->GetGUID());
        }
        LogLb("burning-book", Acore::StringFormat("at=({:.1f}, {:.1f}) fires={}", at.GetPositionX(),
            at.GetPositionY(), _fires.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The descriptor, cleanup
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order (F45): the books, the highest page first (ranged close every book; melee never the dream book, whose
    // mist they would have to stand in), then him; the stories' adds are tanked and fade with their book. Interrupt
    // list: Searing Rebuke (a reward), heroic Open the Index (expected). Dispel list: heroic Dreaming (expected).
    void Describe()
    {
        using BossMechanics::Condition;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_SM_HOLLIS_GREY, SPELL_LB_SEARING_REBUKE, kRebukeKickPriority,
            Ms(kRebukeEveryMs));
        if (_heroic)
        {
            d.interrupts.emplace_back(NPC_SM_HOLLIS_GREY, SPELL_LB_OPEN_THE_INDEX_HEROIC, kOpenKickPriorityHeroic,
                Ms(kOpenEveryMs(true)));
            d.dispels.emplace_back(SPELL_LB_DREAMING, kDreamingDispelPriority);
        }
        for (uint8 page = 1; page <= 3; ++page)
        {
            Condition const onPage = Condition::Custom([page](Unit const* u)
            {
                if (!u)
                    return false;
                uint32 const shown = u->GetAuraCount(SPELL_LB_TURNING_THE_PAGE);
                return page < 3 ? shown == page : shown >= page;
            });
            d.targets.push_back(TargetEntry(NPC_SM_CURSED_BOOK, BookPriority(page), Who::Ranged, onPage));
            d.targets.push_back(TargetEntry(NPC_SM_CURSED_BOOK, BookPriority(page), Who::Melee,
                Condition::AllOf({ onPage, Condition::LacksAura(SPELL_LB_STORY_DREAM) })));
        }
        d.targets.push_back(TargetEntry(NPC_SM_INFERNAL, kStoryAddPriority, Who::Tank));
        d.targets.push_back(TargetEntry(NPC_SM_SPIDERLING, kStoryAddPriority, Who::Tank).AoeOk());
        d.targets.push_back(TargetEntry(NPC_SM_SPIDERLING, kStoryAddPriority, Who::Dps).AoeOk());
        Mechanic::Describe(me, std::move(d));
    }

    // Every book, story, add, look, fire and pending hit gone; every aura of the fight off (Reset, evade, death).
    void Cleanup(char const* why)
    {
        while (!_books.empty())
            CloseBook(_books.begin(), why, false);
        for (MechanicHandle const& h : _fires)
            Mechanic::Cancel(me, h);
        _fires.clear();
        for (ObjectGuid const& guid : _fireLooks)
            Despawn(guid);
        _fireLooks.clear();
        _ward.Stop(me);
        me->RemoveAurasDueToSpell(SPELL_LB_READERS_WARD);
        summons.DespawnAll();
        _fighting = false;
        _casting = false;
        _capLogged = false;
        _openAtMs = 0;
        _rebukeAtMs = 0;
        if (instance)
            for (uint32 const spell : { uint32(SPELL_LB_DROWSY), uint32(SPELL_LB_DREAM_SLEEP),
                uint32(SPELL_LB_DREAMING), uint32(SPELL_LB_WEB_SLOW) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        _arena.Reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm hollis` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    // An empty string when fired; otherwise why not. `gm` stands in for the group out of combat.
    std::string TestFire(TestKind kind, Player* gm, uint32 arg)
    {
        _testPlayer = gm ? gm->GetGUID() : ObjectGuid::Empty;
        switch (kind)
        {
            case TestKind::Open:
            {
                if (arg >= 1 && arg <= kStoryCount)
                    _shelf.PutNext(static_cast<Story>(arg - 1));
                Story const story = _shelf.Take(Below);
                Talk(StoryText(story));
                Throw(story, 1);
                break;
            }
            case TestKind::Page:
                if (_books.empty())
                    return "No book is open.";
                for (Book& b : _books)
                {
                    uint8 const next = NextPage(b.page, _heroic);
                    if (next != b.page)
                        TurnPage(b, next);
                    b.nextPageAtMs = _clockMs + kPageEveryMs;
                }
                break;
            case TestKind::Rebuke:
                if (!me->IsEngaged())
                    return "Searing Rebuke needs the fight (his target).";
                CastRebuke();
                break;
            case TestKind::Close:
            {
                if (_books.empty())
                    return "No book is open.";
                // Each death closes its book (SummonedCreatureDies erases it): collect first, then kill.
                std::vector<ObjectGuid> open;
                for (Book const& b : _books)
                    open.push_back(b.guid);
                for (ObjectGuid const& guid : open)
                    if (Creature* book = ObjectAccessor::GetCreature(*me, guid))
                        if (book->IsAlive())
                            Unit::Kill(gm ? static_cast<Unit*>(gm) : static_cast<Unit*>(me), book);
                break;
            }
            case TestKind::Clear:
                Cleanup("test");
                break;
        }
        return {};
    }

    // `.dbtest sm hollis heroic`: the heroic form on a normal map (and back) until the end of the next pull.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
        if (_fighting)
        {
            StartWard();
            Describe();
        }
    }

    std::string TestState() const
    {
        auto left = [this](uint64 at) -> std::string
        {
            return at ? std::to_string(at > _clockMs ? (at - _clockMs) / 1000 : 0) + "s" : "-";
        };
        std::string books;
        for (Book const& b : _books)
        {
            Creature* book = BookUnit(b);
            books += Acore::StringFormat(" {}:p{}:{:.0f}%:webs{}:adds{}", StoryName(b.story), b.page,
                book ? book->GetHealthPct() : 0.f, b.webs.size(), b.adds.size());
        }
        return Acore::StringFormat("hollis heroic={} fighting={} next-book={} read={} open-in={} rebuke-in={} "
            "ward={:.0f}% fires={} books=[{} ]", _heroic ? 1 : 0, _fighting ? 1 : 0, StoryName(_shelf.Peek()),
            _shelf.ReadThisRound(), left(_openAtMs), left(_rebukeAtMs), _ward.ReductionPct(), _fires.size(), books);
    }

private:
    DungeonKit::ArenaGuard _arena;
    DungeonKit::Arena _clip;                // the lines' wall (LB4, LB7)
    DungeonKit::WardOfTheLiving _ward;      // LB1b
    Shelf _shelf;
    std::list<Book> _books;
    std::vector<MechanicHandle> _fires;     // LB9
    std::vector<ObjectGuid> _fireLooks;
    bool _heroic = false;
    bool _heroicForced = false;             // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
    bool _casting = false;                  // LB1: Open the Index is on his cast bar
    bool _capLogged = false;
    Story _castStory = Story::Spider;
    uint64 _clockMs = 0;                    // the AI's own clock
    uint64 _openAtMs = 0;                   // LB1
    uint64 _rebukeAtMs = 0;                 // LB8
    uint64 _drowsyCheckAtMs = 0;            // LB6
    uint64 _drowsyDecayAtMs = 0;
    ObjectGuid _testPlayer;
};

// ---------------------------------------------------------------------------------------------------------------------
// LB6a Dreaming (heroic): run out (nobody dispelled it), it tells the Librarian (his caster).
// ---------------------------------------------------------------------------------------------------------------------
class spell_sm_hollis_dreaming : public AuraScript
{
    PrepareAuraScript(spell_sm_hollis_dreaming);

    void AfterRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        AuraApplication const* app = GetTargetApplication();
        if (!app || app->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;     // dispelled, died, the book closed: no sleep, no mist
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (!caster || !target || !target->IsAlive())
            return;
        if (Creature* boss = caster->ToCreature())
            if (boss->IsAlive() && boss->IsAIEnabled && boss->AI())
                boss->AI()->SetGUID(target->GetGUID(), GUID_DREAMING_MISSED);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_sm_hollis_dreaming::AfterRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

namespace
{
    boss_lector_hollis_grey_rework* HollisAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_SM_HOLLIS_GREY);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_lector_hollis_grey_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok, uint32 arg = 0)
    {
        boss_lector_hollis_grey_rework* ai = HollisAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(kind, handler->GetPlayer(), arg);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    // `.dbtest sm hollis info`
    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_SM_HOLLIS_GREY, BOSS_HOLLIS_GREY);
    }

    // `.dbtest sm hollis state`: his clocks, the shelf, the ward and each open book.
    bool HandleState(ChatHandler* handler)
    {
        boss_lector_hollis_grey_rework* ai = HollisAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest sm hollis open [1-6]`: LB1 now, without the cast (1 spider, 2 archimonde, 3 troll wars, 4 titans,
    // 5 dream, 6 aftermath; none: the next book on his shelf). Out of combat its story aims at you.
    bool HandleOpen(ChatHandler* handler, Optional<uint32> story)
    {
        return Fire(handler, TestKind::Open, "A book is open (its story runs until it is destroyed).",
            story ? *story : 0);
    }

    // `.dbtest sm hollis page`: LB1a, every open book turns a page now.
    bool HandlePage(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Page, "Every open book turned a page.");
    }

    // `.dbtest sm hollis rebuke`: LB8 now (in combat).
    bool HandleRebuke(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Rebuke, "Searing Rebuke (2.5 s, a kick stops it).");
    }

    // `.dbtest sm hollis close`: every open book is destroyed (heroic in combat: LB9 fires).
    bool HandleClose(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Close, "Every open book is destroyed.");
    }

    // `.dbtest sm hollis clear`: every book, add, zone, fire and aura of the fight goes.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared.");
    }

    // `.dbtest sm hollis heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_lector_hollis_grey_rework* ai = HollisAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossLectorHollisGreyTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,    SEC_GAMEMASTER, Console::No },
            { "open",   HandleOpen,     SEC_GAMEMASTER, Console::No },
            { "page",   HandlePage,     SEC_GAMEMASTER, Console::No },
            { "rebuke", HandleRebuke,   SEC_GAMEMASTER, Console::No },
            { "close",  HandleClose,    SEC_GAMEMASTER, Console::No },
            { "clear",  HandleClear,    SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_lector_hollis_grey_rework()
{
    if (SmHollisGrey::kBound)
        RegisterDungeonReworkCreatureAI(boss_lector_hollis_grey_rework, ScarletMonasteryRework::kInstanceScriptName);
    if (SmHollisGrey::kBound)
        RegisterDungeonReworkCreatureAI(npc_sm_cursed_book, ScarletMonasteryRework::kInstanceScriptName);
    if (SmHollisGrey::kBound)
        RegisterDungeonReworkCreatureAI(npc_sm_hollis_story_add, ScarletMonasteryRework::kInstanceScriptName);
    if (SmHollisGrey::kBound)
        RegisterDungeonReworkCreatureAI(npc_sm_hollis_phantom, ScarletMonasteryRework::kInstanceScriptName);
    if (SmHollisGrey::kBound)
        RegisterSpellScript(spell_sm_hollis_dreaming);
    SmTest::RegisterBoss("hollis", BossLectorHollisGreyTestCommands());
}
