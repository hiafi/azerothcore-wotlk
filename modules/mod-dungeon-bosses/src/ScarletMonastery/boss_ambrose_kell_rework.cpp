/*
 * mod-dungeon-bosses, Scarlet Monastery D6: Ambrose Kell, the Antiquarian (300910), "Trophies of the Purge". Build
 * spec: docs/dungeons/scarlet-monastery-2-library.md "Ambrose Kell, the Antiquarian" (AN1-AN5c, Build spec), handoff
 * section 3.5 row D6, 3.6, 3.8, 7 #25 A. A new boss (no stock script to replace). Pure rules: KellLogic.h.
 *
 *   AN1 The Collection  six relic cases stand in the hall's bays (a pedestal and its relic, summoned by him). At 10 s
 *                       (heroic 8 s), then every 20 s (15 s) he turns to the sealed case nearest him and casts Unseal
 *                       (2 s, an emote naming the relic); the relic shatters and wakes for the rest of the fight. The
 *                       tank chooses which wakes next by where it holds him; bots hold him where pulled
 *   AN2 Plague Cask     an 8 yd cloud round the bay's mouth, 6% (10%) Nature a second, lingering (a persistent Zone)
 *   AN3 Kirin Tor Staff 2 s after the wake, every 8 s: three lines (4 x 40 yd) out of the case at random angles, a 2 s
 *                       marker, 35% (45%) Arcane and Weakened
 *   AN4 Necromancer's   2 s after the wake, every 12 s: a Gallery Skeleton climbs out of the case and goes for the
 *       Skull           tank (else the nearest player). Normal: the skull waits while 4 stand; heroic: no cap
 *   Gilded Cane         5 s, then every 10 s: his swing on his victim, 20% (30%) of the tank row
 *   AN5 Trophy Powers   (heroic) the first time a relic type wakes he takes its owner's power (a look change, a yell):
 *                       a cask: Plague Flask every 12 s (a 4 yd marker at a random player, 2 s flight, 40% Nature and
 *                       Weakened, then a 15 s pool of 8% a second); a staff: Arcane Torrent every 15 s (a 3 s
 *                       interruptible cast; missed, 40% Arcane to everyone); a skull: Bone Curse every 15 s (a Magic
 *                       debuff on a random player for 8 s; undispelled, 25% Physical on them and a skeleton rises)
 *
 * A wipe despawns the skeletons, clouds and pools, and reseals all six cases (the objects are rebuilt) and resets him;
 * the encounter completes on his death and the living skeletons collapse with him (the cases go too). The cases are
 * objects HE summons (no database spawn): they exist while he stands in the hall, a woken relic is deleted at the
 * shatter, a reset rebuilds all six. Every percent hit is a percent of the reference row (his spells ignore caster
 * modifiers): the registry's Zones and the kit's spell_dungeon_refflat_damage on the Cane, the Torrent and the burst.
 * Boss data: kill order Gallery Skeletons, then Kell; interrupt list: Arcane Torrent (heroic, expected); dispel list:
 * Bone Curse (heroic, expected, Magic); no purges. Every firing logs one INFO line "sm kell <mechanic> ..."
 * (module.dungeonbosses); `.dbtest sm kell ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "KellLogic.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include <array>
#include <bit>
#include <cmath>
#include <functional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmKell;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "kell";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // The long hall: every spot the bots plan for the cloud, the lines and the flask stays on its floor (rule 12).
    BossMechanics::SpotBounds HallBounds()
    {
        return BossMechanics::SpotBounds().Rect(213.f, -349.f, 277.f, -301.f, 15.f, 25.f);
    }

    char const* RelicName(Relic relic)
    {
        return relic == Relic::Cask ? "cask" : relic == Relic::Staff ? "staff" : "skull";
    }
}

// Ambrose Kell 300910
struct boss_ambrose_kell_rework : public BossAI
{
    explicit boss_ambrose_kell_rework(Creature* creature)
        : BossAI(creature, BOSS_KELL), _arena(KellArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        if (!_casesBuilt)
            BuildCases();       // pulled in the tick he was created
        _heroic = IsHeroicMap(me);
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_KELL;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_PULL);

        _unsealClock.Start(_clockMs, kUnsealBeat(_heroic).firstMs);
        _caneClock.Start(_clockMs, kCaneBeat(_heroic).firstMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        // "Living skeletons collapse with him": before BossAI's _JustDied, whose DespawnAll would make them vanish.
        // They leave the summon list and their corpses go on their own corpse timer.
        CollapseSkeletons();
        BossAI::JustDied(killer);
        Talk(SAY_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("woken={} trophy={} skeletons-raised={} interrupts={} curses={} flasks={} killer={}",
                std::popcount(_wokenMask), std::popcount(_trophyMask), _skeletonsRaised, _interrupts, _curses, _flasks,
                killer ? killer->GetName() : "none"));
        Cleanup(true);
    }

    // The summons are his (they go with his reset and death) but never zone into his fight on their own: the helpers
    // are not attackable, the skeletons are sent at a target by RaiseSkeleton.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // AN5b: a kick or a silence stopped the Torrent. His own stops (an evade, his death, a reset) are not interrupts:
    // Cleanup drops the cast's state before the engine interrupts it.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_AN_ARCANE_TORRENT && _torrent.active)
            TorrentInterrupted();
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!_casesBuilt)
            BuildCases();
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        UpdateUnseal();
        UpdateCases();
        UpdateHeroic();
        UpdateTorrent();
        if (_caneClock.Due(_clockMs))
        {
            _caneClock.Fired(_clockMs, kCaneBeat(_heroic).everyMs);
            CastCane();
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The cases (AN1)
    // ----------------------------------------------------------------------------------------------------------------

    // The six pedestals, their relics and a trigger on each (the helper that plays the case's looks and fires its
    // lines and skeletons): built when he stands in the hall, out of combat, and again after every reset.
    void BuildCases()
    {
        if (_casesBuilt || !me->IsInWorld() || !me->IsAlive())
            return;
        _casesBuilt = true;
        uint32 objects = 0;
        for (uint32 i = 0; i < kCaseCount; ++i)
        {
            CaseSpot const& c = kCases[i];
            CaseState& state = _cases[i];
            float const facing = CaseFacing(c);
            if (GameObject* pedestal = SummonCaseObject(GO_SM_RELIC_PEDESTAL, kPedestalDisplay, c.spot.x, c.spot.y,
                c.spot.z, facing))
            {
                state.pedestal = pedestal->GetGUID();
                ++objects;
            }
            if (GameObject* relic = SummonCaseObject(RelicEntry(c.relic), RelicDisplay(c.relic), c.spot.x, c.spot.y,
                c.spot.z + kPedestalHeightYd, facing))
            {
                state.relic = relic->GetGUID();
                ++objects;
            }
            if (TempSummon* trigger = me->SummonCreature(NPC_SM_RELIC_TRIGGER,
                Position(c.spot.x, c.spot.y, c.spot.z, facing), TEMPSUMMON_MANUAL_DESPAWN))
                state.trigger = trigger->GetGUID();
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cases", Acore::StringFormat("objects={}", objects));
    }

    uint32 RelicEntry(Relic relic) const
    {
        return relic == Relic::Cask ? GO_SM_RELIC_CASK : relic == Relic::Staff ? GO_SM_RELIC_STAFF
            : GO_SM_RELIC_SKULL;
    }

    // A generic (no click) object turned to `facing`; one C++ constant decides the look (the template's display equals
    // it, tested).
    GameObject* SummonCaseObject(uint32 entry, uint32 display, float x, float y, float z, float facing)
    {
        float const half = facing * 0.5f;
        GameObject* go = me->SummonGameObject(entry, x, y, z, facing, 0.f, 0.f, std::sin(half), std::cos(half), 0);
        if (!go)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "case-refused",
                Acore::StringFormat("entry={} at=({:.1f}, {:.1f}, {:.1f})", entry, x, y, z));
            return nullptr;
        }
        if (!go->GetGOInfo() || go->GetGOInfo()->displayId != display)
            go->SetDisplayId(display);
        return go;
    }

    Creature* TriggerOf(uint32 index) const
    {
        return index < kCaseCount && _cases[index].trigger ? ObjectAccessor::GetCreature(*me, _cases[index].trigger)
            : nullptr;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AN1 Unseal
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateUnseal()
    {
        if (_unseal.active)
        {
            if (_clockMs >= _unseal.endMs)
            {
                uint32 const index = _unseal.index;
                _unseal = UnsealState();
                Wake(index, "unseal");
            }
            return;
        }
        if (_unsealClock.Due(_clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
            StartUnseal();
    }

    // The sealed case nearest him now: a 2 s cast with an emote naming the relic; it wakes when the cast ends.
    bool StartUnseal()
    {
        int const index = NearestSealed(_wokenMask, { me->GetPositionX(), me->GetPositionY() });
        if (index < 0)
        {
            _unsealClock.Stop();    // every case is awake
            return false;
        }
        _unsealClock.Fired(_clockMs, kUnsealBeat(_heroic).everyMs);
        me->StopMoving();
        DungeonKit::CastBar(me, SPELL_AN_UNSEAL_CAST, nullptr, UnsealEmote(kCases[index].relic));
        _unseal.active = true;
        _unseal.index = static_cast<uint32>(index);
        _unseal.endMs = _clockMs + kUnsealCastMs;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "unseal",
            Acore::StringFormat("case={} relic={} woken={}", index, RelicName(kCases[index].relic),
                std::popcount(_wokenMask)));
        return true;
    }

    // The case wakes: the shatter on its trigger, the relic gone, its curse running for the rest of the fight.
    void Wake(uint32 index, char const* why)
    {
        if (index >= kCaseCount || (_wokenMask & (1u << index)))
            return;
        CaseSpot const& c = kCases[index];
        CaseState& state = _cases[index];
        _wokenMask |= 1u << index;
        if (Creature* trigger = TriggerOf(index))
            trigger->CastSpell(trigger, SPELL_AN_UNSEAL_SHATTER, true);
        if (GameObject* relic = state.relic ? me->GetMap()->GetGameObject(state.relic) : nullptr)
            relic->Delete();
        state.relic = ObjectGuid::Empty;
        switch (c.relic)
        {
            case Relic::Cask:
                StartCloud(index);
                break;
            case Relic::Staff:
                state.staffClock.Start(_clockMs, kStaffBeat(_heroic).firstMs);
                break;
            case Relic::Skull:
                state.skullClock.Start(_clockMs, kSkullBeat(_heroic).firstMs);
                break;
        }
        if (_heroic)
            GrantTrophy(c.relic);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "wake",
            Acore::StringFormat("case={} relic={} why={} woken={}", index, RelicName(c.relic), why,
                std::popcount(_wokenMask)));
    }

    // The woken cases' own beats: a staff's lines, a skull's skeleton.
    void UpdateCases()
    {
        for (uint32 i = 0; i < kCaseCount; ++i)
        {
            if (!(_wokenMask & (1u << i)))
                continue;
            CaseState& state = _cases[i];
            if (state.staffClock.Due(_clockMs))
            {
                state.staffClock.Fired(_clockMs, kStaffBeat(_heroic).everyMs);
                FireStaff(i);
            }
            if (state.skullClock.Due(_clockMs))
            {
                if (RaiseFromSkull(i))
                    state.skullClock.Fired(_clockMs, kSkullBeat(_heroic).everyMs);
                else
                    state.skullClock.Start(_clockMs, kSkullRetryMs);    // at the cap: the skull waits
            }
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AN2 Plague Cask
    // ----------------------------------------------------------------------------------------------------------------

    // A persistent 8 yd Zone round the bay's mouth for the rest of the fight (lingering: no Weakened), and a trigger
    // there carrying the cloud's look.
    void StartCloud(uint32 index)
    {
        CaseSpot const& c = kCases[index];
        Vec2 const center = CloudCenter(c);
        Position const at(center.x, center.y, c.spot.z, 0.f);
        float const pct = kCloudPct(_heroic);
        MechanicRef ref = Mechanic::Circle(me, at, kCloudRadiusYd, Ms(kCloudTickMs));
        ref.Persistent(Ms(kCloudLifeMs), Ms(kCloudTickMs)).Damage(pct).TankDamage(pct)
            .School(SPELL_SCHOOL_NATURE).Spell(SPELL_AN_PLAGUE_CLOUD).NoFillTimer().Within(HallBounds())
            .Tag(TAG_AN_CLOUD);
        if (ref.IsValid())
            Track(ref.Handle());
        if (TempSummon* look = me->SummonCreature(NPC_SM_RELIC_TRIGGER, at, TEMPSUMMON_MANUAL_DESPAWN))
            look->CastSpell(look, SPELL_AN_PLAGUE_CLOUD_LOOK, true);
        ++_clouds;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cloud",
            Acore::StringFormat("case={} at=({:.1f}, {:.1f}) pct={:.0f} clouds={}", index, center.x, center.y, pct,
                _clouds));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AN3 Kirin Tor Staff
    // ----------------------------------------------------------------------------------------------------------------

    // Three lines out of the case at random angles into the hall: a 2 s marker, then 35% (45%) Arcane and Weakened to
    // anyone on one, the tank included. The trigger throws a missile along each (a look only).
    void FireStaff(uint32 index)
    {
        CaseSpot const& c = kCases[index];
        std::array<float, kLinesPerStaff> const bearings = LineBearings(c, []() { return frand(0.f, 1.f); });
        float const pct = kLinePct(_heroic);
        Creature* trigger = TriggerOf(index);
        for (float const bearing : bearings)
        {
            Position const from(c.spot.x, c.spot.y, c.spot.z, bearing);
            MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::LineFacing(from, bearing, kLineLengthYd,
                kLineWidthYd), Ms(kLineWarnMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_ARCANE).Spell(SPELL_AN_ARCANE_LINE).Weakened()
                .Within(HallBounds()).Tag(TAG_AN_STAFF_LINE);
            if (ref.IsValid())
                Track(ref.Handle());
            if (trigger)
            {
                DungeonKit::Vec2 const end = DungeonKit::Advance({ c.spot.x, c.spot.y }, bearing, kLineLengthYd);
                trigger->CastSpell(end.x, end.y, c.spot.z, SPELL_AN_ARCANE_LINE_LOOK, true);
            }
        }
        ++_lineVolleys;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "lines",
            Acore::StringFormat("case={} pct={:.0f} bearings=({:.0f}, {:.0f}, {:.0f}) volleys={}", index, pct,
                bearings[0] * 180.f / DungeonKit::kPi, bearings[1] * 180.f / DungeonKit::kPi,
                bearings[2] * 180.f / DungeonKit::kPi, _lineVolleys));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AN4 Necromancer's Skull
    // ----------------------------------------------------------------------------------------------------------------

    uint32 LiveSkeletons() const
    {
        uint32 live = 0;
        for (ObjectGuid const& guid : summons)
            if (Creature const* summon = ObjectAccessor::GetCreature(*me, guid))
                if (summon->GetEntry() == NPC_SM_GALLERY_SKELETON && summon->IsAlive())
                    ++live;
        return live;
    }

    // The skull's Gallery Skeleton: false while the cap holds it back (normal: 4 alive; heroic: never).
    bool RaiseFromSkull(uint32 index)
    {
        if (!SkeletonMayRise(LiveSkeletons(), _heroic))
        {
            if (!_capLogged)
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "skeleton-capped",
                    Acore::StringFormat("case={} live={}", index, LiveSkeletons()));
            _capLogged = true;
            return false;
        }
        _capLogged = false;
        CaseSpot const& c = kCases[index];
        if (Creature* trigger = TriggerOf(index))
            trigger->CastSpell(trigger, SPELL_AN_RAISE_SKELETON_LOOK, true);
        RaiseSkeleton(Position(c.spot.x, c.spot.y, c.spot.z, CaseFacing(c)), "skull");
        return true;
    }

    // A skeleton at `at`: it goes for the tank when the tank is near, else for the nearest player (rule 19: bots
    // attack on arrival with the tank first). Everyone in the fight is on its threat list at 0 (rule 11).
    Creature* RaiseSkeleton(Position const& at, char const* source)
    {
        TempSummon* skeleton = me->SummonCreature(NPC_SM_GALLERY_SKELETON, at, TEMPSUMMON_CORPSE_TIMED_DESPAWN,
            kSkeletonCorpseMs);
        if (!skeleton)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "skeleton-refused", source);
            return nullptr;
        }
        ++_skeletonsRaised;
        if (me->IsEngaged())
            DoZoneInCombat(skeleton);
        Unit* victim = me->GetVictim();
        Player* tank = victim ? victim->ToPlayer() : nullptr;
        bool const haveTank = CountsAsPlayer(tank);
        bool const seeksTank = SkeletonSeeksTank(haveTank,
            haveTank ? tank->GetExactDist2d(at.GetPositionX(), at.GetPositionY()) : 0.f);
        Player* target = seeksTank ? tank : NearestPlayerTo(at);
        // Everyone is on its list at 0 (rule 11): the opening threat makes its first pick stick (rule 19).
        if (target && skeleton->IsAIEnabled)
        {
            skeleton->GetThreatMgr().AddThreat(target, kSkeletonOpeningThreat);
            skeleton->AI()->AttackStart(target);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "skeleton",
            Acore::StringFormat("source={} at=({:.1f}, {:.1f}) target={} tank={} live={} raised={}", source,
                at.GetPositionX(), at.GetPositionY(), target ? target->GetName() : std::string("none"),
                seeksTank ? 1 : 0, LiveSkeletons(), _skeletonsRaised));
        return skeleton;
    }

    // The living player in his map closest to `at` (the skeleton's target when the tank is far or missing).
    Player* NearestPlayerTo(Position const& at) const
    {
        Player* best = nullptr;
        float bestDist = 0.f;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!CountsAsPlayer(player))
                continue;
            float const dist = player->GetExactDist2d(at.GetPositionX(), at.GetPositionY());
            if (!best || dist < bestDist)
            {
                best = player;
                bestDist = dist;
            }
        }
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Gilded Cane
    // ----------------------------------------------------------------------------------------------------------------

    bool CastCane()
    {
        Unit* victim = me->GetVictim();
        Player* tank = victim ? victim->ToPlayer() : nullptr;
        if (!CountsAsPlayer(tank))
            return false;
        me->CastSpell(tank, SPELL_AN_GILDED_CANE, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cane",
            Acore::StringFormat("tank={} pct={:.0f}", tank->GetName(), kCanePct(_heroic)));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AN5 Trophy Powers (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // The first time a relic type wakes he takes its owner's power for the rest of the fight: his look changes (an
    // aura), he yells, and the power's beat starts. A second case of the type adds nothing.
    void GrantTrophy(Relic relic)
    {
        uint32 const bit = 1u << static_cast<uint32>(relic);
        if (_trophyMask & bit)
            return;
        _trophyMask |= bit;
        me->CastSpell(me, TrophySpell(relic), true);
        Talk(SAY_TROPHY);
        switch (relic)
        {
            case Relic::Cask:
                _flaskClock.Start(_clockMs, kFlaskEveryMs);
                break;
            case Relic::Staff:
                _torrentClock.Start(_clockMs, kTorrentEveryMs);
                break;
            case Relic::Skull:
                _curseClock.Start(_clockMs, kCurseEveryMs);
                break;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "trophy",
            Acore::StringFormat("relic={} trophies={}", RelicName(relic), std::popcount(_trophyMask)));
    }

    void UpdateHeroic()
    {
        if (!_heroic)
            return;
        if (_flaskClock.Due(_clockMs))
        {
            _flaskClock.Fired(_clockMs, kFlaskEveryMs);
            ThrowFlask(nullptr);
        }
        if (_curseClock.Due(_clockMs))
        {
            _curseClock.Fired(_clockMs, kCurseEveryMs);
            CastCurse(nullptr);
        }
        // The Torrent is a cast: it waits for any cast in progress (an Unseal bar) and stays due.
        // A refused cast (a silence, an Arcane lockout) retries on kTorrentRetryMs, not every map tick.
        if (_torrentClock.Due(_clockMs) && !me->HasUnitState(UNIT_STATE_CASTING) && !_unseal.active)
            _torrentClock.Fired(_clockMs, StartTorrent() ? kTorrentEveryMs : kTorrentRetryMs);
    }

    // AN5a: a 4 yd marker at a random player's spot (the tank included), a 2 s flight (the vial's look), 40% Nature and
    // Weakened where it lands; then a 15 s pool of 8% a second.
    bool ThrowFlask(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;   // the tank included (AN5a)
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!CountsAsPlayer(target))
            return false;
        Position const spot(target->GetPositionX(), target->GetPositionY(), target->GetPositionZ(), 0.f);
        me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_AN_PLAGUE_FLASK_THROW, true);
        MechanicRef ref = Mechanic::Circle(me, spot, kFlaskRadiusYd, Ms(kFlaskFlightMs));
        ref.Damage(kFlaskPct).TankDamage(kFlaskPct).School(SPELL_SCHOOL_NATURE).Spell(SPELL_AN_PLAGUE_FLASK).Weakened()
            .Within(HallBounds()).Tag(TAG_AN_FLASK)
            .OnResolve(OnKell([spot](boss_ambrose_kell_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.FlaskLands(spot, r);
            }));
        if (ref.IsValid())
            Track(ref.Handle());
        ++_flasks;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flask",
            Acore::StringFormat("target={} tank={} at=({:.1f}, {:.1f}) pct={:.0f}", target->GetName(),
                target == me->GetVictim() ? 1 : 0, spot.GetPositionX(), spot.GetPositionY(), kFlaskPct));
        return true;
    }

    // The vial lands: a lasting pool of 8% a second for 15 s, its look on a trigger there.
    void FlaskLands(Position const& spot, BossMechanics::ResolveResult const& result)
    {
        if (result.fizzled || !me->IsAlive() || !me->IsEngaged())
            return;
        MechanicRef ref = Mechanic::Circle(me, spot, kFlaskRadiusYd, Ms(kPoolTickMs));
        ref.Persistent(Ms(kPoolMs), Ms(kPoolTickMs)).Damage(kPoolPct).TankDamage(kPoolPct)
            .School(SPELL_SCHOOL_NATURE).Spell(SPELL_AN_PLAGUE_FLASK_POOL).NoFillTimer().Within(HallBounds())
            .Tag(TAG_AN_FLASK_POOL);
        if (ref.IsValid())
            Track(ref.Handle());
        if (TempSummon* look = me->SummonCreature(NPC_SM_RELIC_TRIGGER, spot, TEMPSUMMON_TIMED_DESPAWN,
            kPoolMs + 1000))
            look->CastSpell(look, SPELL_AN_PLAGUE_FLASK_POOL_LOOK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flask-pool",
            Acore::StringFormat("at=({:.1f}, {:.1f}) hits={} pct={:.0f}", spot.GetPositionX(), spot.GetPositionY(),
                result.hits.size(), kPoolPct));
    }

    // AN5b: a 3 s interruptible cast (an emote); missed, 40% Arcane to every player by the spell's own effect.
    bool StartTorrent()
    {
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, SPELL_AN_ARCANE_TORRENT, false);
        if (result != SPELL_CAST_OK)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "torrent-failed",
                Acore::StringFormat("result={} retry={}ms", static_cast<uint32>(result), kTorrentRetryMs));
            return false;
        }
        Talk(EMOTE_TORRENT);        // only for a cast that started (a refused one retries; no emote spam)
        _torrent = TorrentState();
        _torrent.active = true;
        _torrent.startedMs = _clockMs;
        Mechanic::NoteNextCastIn(me, SPELL_AN_ARCANE_TORRENT, Ms(kTorrentEveryMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "torrent",
            Acore::StringFormat("pct={:.0f} cast={}ms", kTorrentPct, kTorrentCastMs));
        return true;
    }

    // The cast ended without a hook (it went off, or he lost it): the state goes.
    void UpdateTorrent()
    {
        if (!_torrent.active || me->FindCurrentSpellBySpellId(SPELL_AN_ARCANE_TORRENT))
            return;
        if (_clockMs < _torrent.startedMs + kTorrentStartGraceMs)
            return;     // the cast has not taken yet
        _torrent = TorrentState();
        ++_torrents;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "torrent-landed", Acore::StringFormat("torrents={}",
            _torrents));
    }

    void TorrentInterrupted()
    {
        _torrent = TorrentState();
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        ++_interrupts;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "torrent-interrupted",
            Acore::StringFormat("interrupts={}", _interrupts));
    }

    // AN5c: a Magic debuff on a random player (the tank included) for 8 s, one at a time per player. Undispelled it
    // expires into a burst (BoneCurseExpired). The dispel list names it.
    bool CastCurse(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;   // the tank included (AN5c)
            for (Player* player : FightPlayers())
                if (player->HasAura(SPELL_AN_BONE_CURSE))
                    rule.exclude.push_back(player->GetGUID().GetRawValue());
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!CountsAsPlayer(target))
            return false;
        me->CastSpell(target, SPELL_AN_BONE_CURSE, true);
        ++_curses;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "curse",
            Acore::StringFormat("target={} tank={} curses={}", target->GetName(), target == me->GetVictim() ? 1 : 0,
                _curses));
        return true;
    }

    // The curse ran out undispelled (spell_sm_kell_bone_curse): 25% Physical on the cursed player and a Gallery
    // Skeleton rises from them (a lasting setback, an add).
    void BoneCurseExpired(Unit* target)
    {
        Player* player = target ? target->ToPlayer() : nullptr;
        if (!CountsAsPlayer(player) || !me->IsAlive() || !me->IsEngaged())
            return;
        me->CastSpell(player, SPELL_AN_BONE_BURST, true);
        RaiseSkeleton(Position(player->GetPositionX(), player->GetPositionY(), player->GetPositionZ(),
            player->GetOrientation()), "curse");
        ++_bursts;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "curse-burst",
            Acore::StringFormat("target={} pct={:.0f} bursts={}", player->GetName(), kBurstPct, _bursts));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (LIB "Boss data")
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order: the Gallery Skeletons, then Kell. Interrupt list: Arcane Torrent (heroic, expected). Dispel list:
    // Bone Curse (heroic, expected, Magic). Purge list: none. The Torrent and the curse exist on heroic only.
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_SM_GALLERY_SKELETON, 1);
        if (_heroic)
        {
            d.interrupts.emplace_back(NPC_SM_KELL, SPELL_AN_ARCANE_TORRENT, 3, Ms(kTorrentEveryMs));
            d.dispels.push_back(BossMechanics::DispelEntry(SPELL_AN_BONE_CURSE, 2));
        }
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm kell` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Unseal,
        Wake,
        Cloud,
        Lines,
        Skeleton,
        Cane,
        Flask,
        Torrent,
        Curse,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM), `n` a case number
    // (1 to 6, 0 = the nearest sealed / the first of its kind).
    std::string TestFire(TestMechanic mechanic, Player* who, uint32 n)
    {
        if (!me->IsEngaged())
            return "Kell must be in combat (the picks read his threat list, the mechanics his encounter).";
        if (n > kCaseCount)
            return "A case number is 1 to 6.";
        switch (mechanic)
        {
            case TestMechanic::Unseal:
                if (_unseal.active || me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting already.";
                if (!StartUnseal())
                    return "Every case is awake.";
                break;
            case TestMechanic::Wake:
            {
                int const index = n ? static_cast<int>(n) - 1 : NearestSealed(_wokenMask,
                    { me->GetPositionX(), me->GetPositionY() });
                if (index < 0 || (_wokenMask & (1u << index)))
                    return "That case is awake already.";
                Wake(static_cast<uint32>(index), "test");
                break;
            }
            case TestMechanic::Cloud:
                StartCloud(n ? n - 1 : CaseOf(Relic::Cask));
                break;
            case TestMechanic::Lines:
                FireStaff(n ? n - 1 : CaseOf(Relic::Staff));
                break;
            case TestMechanic::Skeleton:
            {
                if (!who)
                    return "No player to raise a skeleton under.";
                RaiseSkeleton(Position(who->GetPositionX(), who->GetPositionY(), who->GetPositionZ(), 0.f), "test");
                break;
            }
            case TestMechanic::Cane:
                if (!CastCane())
                    return "Nobody tanks him.";
                break;
            case TestMechanic::Flask:
                if (!ThrowFlask(CountsAsPlayer(who) ? who : nullptr))
                    return "No player to throw at.";
                break;
            case TestMechanic::Torrent:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting already.";
                if (!StartTorrent())
                    return "The Torrent did not start (see the log).";
                break;
            case TestMechanic::Curse:
                if (!CastCurse(CountsAsPlayer(who) ? who : nullptr))
                    return "No player to curse.";
                break;
        }
        return {};
    }

    uint32 CaseOf(Relic relic) const
    {
        for (uint32 i = 0; i < kCaseCount; ++i)
            if (kCases[i].relic == relic)
                return i;
        return 0;
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} woken={:#04x} trophy={:#03x} skeletons={} (raised {}) "
            "clouds={} volleys={} flasks={} curses={} bursts={} torrents={} interrupts={} unseal={} cases={} "
            "live-handles={}",
            _clockMs / 1000, _heroic ? 1 : 0, _wokenMask, _trophyMask, LiveSkeletons(), _skeletonsRaised, _clouds,
            _lineVolleys, _flasks, _curses, _bursts, _torrents, _interrupts, _unseal.active ? 1 : 0,
            _casesBuilt ? 1 : 0, _live.size());
    }

private:
    struct CaseState
    {
        ObjectGuid pedestal;
        ObjectGuid relic;
        ObjectGuid trigger;
        BeatClock staffClock;
        BeatClock skullClock;
    };

    struct UnsealState
    {
        bool active = false;
        uint32 index = 0;
        uint64 endMs = 0;
    };

    struct TorrentState
    {
        bool active = false;
        uint64 startedMs = 0;
    };

    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (!CountsAsPlayer(player) || !player->IsInMap(me))
                continue;
            out.push_back(player);
        }
        return out;
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnKell(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_ambrose_kell_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    static boss_ambrose_kell_rework* From(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_ambrose_kell_rework*>(boss->AI());
    }

    // A mechanic of the fight (a cloud, a line, a flask, a pool): kept to cancel it on a reset. Never truncated: the
    // casks' clouds are among the first handles and live all fight, so dropping the oldest would drop them. A handle
    // is a few bytes and Cancel on a resolved one is a no-op, so the whole pull's list is cheap.
    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // "Living skeletons collapse with him": every Gallery Skeleton leaves the summon list (so no DespawnAll takes it)
    // and the living ones die on the floor; the corpses go on their own corpse timer.
    void CollapseSkeletons()
    {
        std::vector<ObjectGuid> skeletons;
        for (ObjectGuid const& guid : summons)
            if (Creature* summon = ObjectAccessor::GetCreature(*me, guid))
                if (summon->GetEntry() == NPC_SM_GALLERY_SKELETON)
                    skeletons.push_back(guid);
        for (ObjectGuid const& guid : skeletons)
            if (Creature* skeleton = ObjectAccessor::GetCreature(*me, guid))
            {
                summons.Despawn(skeleton);
                if (skeleton->IsAlive())
                    skeleton->KillSelf();
            }
    }

    // The pull's state: nothing registered, no summon, no object, no aura of his on anyone (Reset, evade, death, a new
    // pull). `dead`: his death keeps the skeletons for a moment (they collapse with him) and takes the cases away.
    void Cleanup(bool dead)
    {
        _torrent = TorrentState();      // before the engine interrupts a cast, so it never reads as a kick
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (dead)
        {
            CollapseSkeletons();        // already done by JustDied; a no-op then
            summons.DespawnEntry(NPC_SM_RELIC_TRIGGER);
        }
        else
            summons.DespawnAll();
        DeleteCaseObjects();
        _casesBuilt = false;
        _clockMs = 0;
        _unseal = UnsealState();
        _unsealClock.Stop();
        _caneClock.Stop();
        _flaskClock.Stop();
        _torrentClock.Stop();
        _curseClock.Stop();
        _wokenMask = 0;
        _trophyMask = 0;
        _clouds = 0;
        _lineVolleys = 0;
        _skeletonsRaised = 0;
        _flasks = 0;
        _curses = 0;
        _bursts = 0;
        _torrents = 0;
        _interrupts = 0;
        _capLogged = false;
        _arena.Reset();
        for (uint32 const spell : { uint32(SPELL_AN_TROPHY_CASK), uint32(SPELL_AN_TROPHY_STAFF),
            uint32(SPELL_AN_TROPHY_SKULL) })
            me->RemoveAurasDueToSpell(spell);
        if (instance)
            for (uint32 const spell : { uint32(SPELL_AN_BONE_CURSE) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    // Every pedestal and relic this fight's hall stands: gone (a reset builds them again). The triggers are summons
    // (DespawnAll above).
    void DeleteCaseObjects()
    {
        Map* map = me->FindMap();
        for (CaseState& state : _cases)
        {
            for (ObjectGuid const& guid : { state.pedestal, state.relic })
                if (guid && map)
                    if (GameObject* go = map->GetGameObject(guid))
                        go->Delete();
            state = CaseState();
        }
    }

    DungeonKit::ArenaGuard _arena;
    std::array<CaseState, kCaseCount> _cases;
    BeatClock _unsealClock;
    BeatClock _caneClock;
    BeatClock _flaskClock;
    BeatClock _torrentClock;
    BeatClock _curseClock;
    UnsealState _unseal;
    TorrentState _torrent;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint32 _wokenMask = 0;          // bit i = case i is awake
    uint32 _trophyMask = 0;         // bit r = relic type r's Trophy Power taken (heroic)
    uint32 _clouds = 0;
    uint32 _lineVolleys = 0;
    uint32 _skeletonsRaised = 0;
    uint32 _flasks = 0;
    uint32 _curses = 0;
    uint32 _bursts = 0;
    uint32 _torrents = 0;
    uint32 _interrupts = 0;
    bool _casesBuilt = false;
    bool _capLogged = false;
    bool _heroic = false;
};

namespace
{
    boss_ambrose_kell_rework* KellAIOf(Unit* unit)
    {
        Creature* boss = unit ? unit->ToCreature() : nullptr;
        if (!boss || !boss->IsAIEnabled || boss->GetEntry() != NPC_SM_KELL)
            return nullptr;
        return dynamic_cast<boss_ambrose_kell_rework*>(boss->AI());
    }

    boss_ambrose_kell_rework* FindKellAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_SM_KELL);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_ambrose_kell_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Kell is not running boss_ambrose_kell_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_ambrose_kell_rework::TestMechanic mechanic, char const* what, uint32 n = 0)
    {
        boss_ambrose_kell_rework* ai = FindKellAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who, n);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Kell: {} fired ({}).", what, ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_SM_KELL, BOSS_KELL);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_ambrose_kell_rework* ai = FindKellAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Kell: {}", ai->TestState());
        return true;
    }

    bool HandleUnseal(ChatHandler* handler)
    {
        return Fire(handler, boss_ambrose_kell_rework::TestMechanic::Unseal,
            "Unseal (AN1: a 2 s cast on the sealed case nearest him, then it wakes)");
    }

    bool HandleWake(ChatHandler* handler, Optional<uint32> number)
    {
        return Fire(handler, boss_ambrose_kell_rework::TestMechanic::Wake,
            "a case woken at once (AN1; no cast; 1 to 6, none = the nearest sealed)", number.value_or(0));
    }

    bool HandleCloud(ChatHandler* handler, Optional<uint32> number)
    {
        return Fire(handler, boss_ambrose_kell_rework::TestMechanic::Cloud,
            "a Plague Cask cloud (AN2: 8 yd, for the fight; a case number 1 to 6, none = the first cask)",
            number.value_or(0));
    }

    bool HandleLines(ChatHandler* handler, Optional<uint32> number)
    {
        return Fire(handler, boss_ambrose_kell_rework::TestMechanic::Lines,
            "a staff's three lines (AN3: 4 x 40 yd, a 2 s marker; a case number 1 to 6, none = the first staff)",
            number.value_or(0));
    }

    bool HandleSkeleton(ChatHandler* handler)
    {
        return Fire(handler, boss_ambrose_kell_rework::TestMechanic::Skeleton,
            "a Gallery Skeleton under the selected player (AN4, any difficulty, past the cap)");
    }

    bool HandleCane(ChatHandler* handler)
    {
        return Fire(handler, boss_ambrose_kell_rework::TestMechanic::Cane, "Gilded Cane (the tank hit)");
    }

    bool HandleFlask(ChatHandler* handler)
    {
        return Fire(handler, boss_ambrose_kell_rework::TestMechanic::Flask,
            "Plague Flask (AN5a: the selected player's spot, any difficulty)");
    }

    bool HandleTorrent(ChatHandler* handler)
    {
        return Fire(handler, boss_ambrose_kell_rework::TestMechanic::Torrent,
            "Arcane Torrent (AN5b: a 3 s cast, kick it)");
    }

    bool HandleCurse(ChatHandler* handler)
    {
        return Fire(handler, boss_ambrose_kell_rework::TestMechanic::Curse,
            "Bone Curse on the selected player (AN5c: dispel it inside 8 s)");
    }

    // `.dbtest sm kell <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BossAmbroseKellTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "unseal",   HandleUnseal,   SEC_GAMEMASTER, Console::No },
            { "wake",     HandleWake,     SEC_GAMEMASTER, Console::No },
            { "cloud",    HandleCloud,    SEC_GAMEMASTER, Console::No },
            { "lines",    HandleLines,    SEC_GAMEMASTER, Console::No },
            { "skeleton", HandleSkeleton, SEC_GAMEMASTER, Console::No },
            { "cane",     HandleCane,     SEC_GAMEMASTER, Console::No },
            { "flask",    HandleFlask,    SEC_GAMEMASTER, Console::No },
            { "torrent",  HandleTorrent,  SEC_GAMEMASTER, Console::No },
            { "curse",    HandleCurse,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// AN5c Bone Curse: a Magic debuff, 8 s. Expiring undispelled, it tells Kell's AI (a burst and a skeleton); a dispel, a
// death, a reset or leaving the map remove it by another mode and nothing happens.
class spell_sm_kell_bone_curse : public AuraScript
{
    PrepareAuraScript(spell_sm_kell_bone_curse);

    void AfterRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        AuraApplication const* app = GetTargetApplication();
        if (!app || app->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;
        if (boss_ambrose_kell_rework* ai = KellAIOf(GetCaster()))
            ai->BoneCurseExpired(GetTarget());
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_sm_kell_bone_curse::AfterRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_boss_ambrose_kell_rework()
{
    if (SmKell::kBound)
        RegisterDungeonReworkCreatureAI(boss_ambrose_kell_rework, ScarletMonasteryRework::kInstanceScriptName);
    RegisterSpellScript(spell_sm_kell_bone_curse);
    SmTest::RegisterBoss("kell", BossAmbroseKellTestCommands());
}
