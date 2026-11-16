/*
 * mod-dungeon-bosses, Blackrock Spire B11: Solakar Flamewreath (10264), "The Stolen Flame", a hot potato (SP 2791-3111,
 * SK1-SK12, rulings 55-58; handoff section 3.4 rows SK, 3.5 row B11, 3.6, 3.8). Replaces the stock
 * boss_solakar_flamewreath (War Stomp 16727) and npc_rookery_hatcher (Hatch Rookery Egg 15746 every 6 to 8 s, uncapped
 * whelps); bound by apps/dbc-tools source/npcs/blackrock_spire/solakar.py. Pure rules: SolakarLogic.h. The pass of the
 * flame between players is mod-boss-mechanics' PassEntry (Blackrock Spire WP-PS).
 *
 *   SK1 The opening    Father Flame (go_brs_father_flame) gives its taker the flame (the holder aura and the bag
 *                      item 70610) and starts the instance's event: one Rookery Guardian and one Rookery Hatcher at the
 *                      stock spots, and Solakar, summoned hidden (invisible, passive, not attackable): his AI owns the
 *                      flame from the first second and shows himself at 30 s (ACTION_SOLAKAR_ARRIVE), line 0
 *   SK2 Snatch         the Hatcher chases the holder at its stock 10 yd/s (taunt immune; snares, roots and stuns
 *                      work; each toss stops it 1 s); reaching the holder it takes the flame (line 1) and runs to the
 *                      nearest clutch of 3+ eggs, where every egg within 6 yd hatches and the flame drops; killed or
 *                      stunned on the way it drops the flame
 *   SK3 Ground Stomp   the Guardian, 6 s then every 12 s: a 2 s bar and an 8 yd circle on it, 20% and Weakened
 *   SK4 Holding        the holder burns every second, rising (the heat table by size and difficulty); never stops
 *   SK5 The toss       item 70610 (from the bags) on an ally within 30 yd (0.75 s flight): the catcher holds, the
 *                      thrower is Scorched (R-2 ruling: nobody with full bags catches or picks it up; bots skip them)
 *                      (cannot catch; heroic: a wounded player still can)
 *   SK6 Catch flare    every egg within 4 yd of the catcher hatches into a flame whelp, at most 6 alive (12 at 6+);
 *                      past the cap the eggs wait (warm) and hatch as whelps die; heroic whelps chase the holder
 *   SK7 On the floor   a holder's death (or a dropped snatch) leaves a 4 yd pickup for 6 s (not Scorched), every egg
 *                      within 6 yd hatches; unclaimed, he leaves the tank and runs for it (it can still be taken)
 *   SK8 Reclaim        he reaches the flame (or the hunted holder): +1 Flamewreath (+20% / +25% on everything he
 *                      does, cap 3, line 2), the egg nearest each player hatches, the flame sits in its brazier 10 s
 *                      (then he runs there: another Reclaim). A Reclaim or a torn wound at 3 stacks: Wreathed in Flame
 *                      (line 3), 10% to everyone every 2 s
 *   SK9 The Hunt       10 s after he arrives, every 25 s (heroic 20 s): a 1.5 s roar (line 1), then 8 s running for
 *                      the holder (a red ring on them); each toss stops him 1 s; reaching them: a Reclaim
 *   SK10 War Stomp     15 s, every 20 s, never in a Hunt: a 2 s bar, 8 yd circle on him, 25%, Weakened, 2 s stun
 *   SK11 Spear Wound   heroic, halfway between Hunts: 1 / 2 players (never the holder) bleed 1% a second; holding the
 *                      flame 2 s in all sears it; untouched 12 s it tears: 40% and +1 Flamewreath (line 4)
 *   SK12 Reset         a wipe in the opening (nobody alive in the Rookery for 10 s) or after it (his evade): the flame,
 *                      the items, Scorched, the wounds, the whelps and the hatched eggs go, and Father Flame is ready
 *
 * Boss data: kill order the Hatcher (3), the Guardian (2), heroic flame whelps (1); the flame's pass (PassEntry). No
 * interrupts, no dispels, no tank swap. Every timer runs on the AI's own clock. Every firing logs one INFO line
 * "brs solakar <mechanic> ..." (module.dungeonbosses); `.dbtest brs solakar ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitFlex.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SolakarLogic.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <functional>
#include <list>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsSolakar;
using BossCondition = BossMechanics::Condition;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using BossMechanics::PassEntry;
using BossMechanics::PassTrigger;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "solakar";

    uint32 constexpr kPollMs = 250;
    uint32 constexpr kPointFlame = 1;       // MovePoint ids
    uint32 constexpr kPointClutch = 2;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    Vec2 XY(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }

    std::string At(Position const& p)
    {
        return Acore::StringFormat("({:.1f}, {:.1f})", p.GetPositionX(), p.GetPositionY());
    }

    // A fresh aura's length (Scorched Hands by size and difficulty).
    void SetAuraMs(Aura* aura, uint32 ms)
    {
        if (!aura)
            return;
        aura->SetMaxDuration(static_cast<int32>(ms));
        aura->SetDuration(static_cast<int32>(ms));
    }

    bool LivePlayer(Player const* p)
    {
        return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
    }

    // The flame's two halves leave a player: the aura and the item.
    void StripFlame(Player* p, bool item)
    {
        if (!p)
            return;
        p->RemoveAurasDueToSpell(SPELL_SK_FATHER_FLAME);
        p->RemoveAurasDueToSpell(SPELL_SK_HUNTED);
        if (item && p->HasItemCount(kItemFatherFlame, 1))
            p->DestroyItemCount(kItemFatherFlame, 9, true);
    }

    // Room for the flame (R-2 ruling 2026-11-15): the item already in the bags, or a free slot for it. A player
    // without room cannot be thrown to (the toss's CheckCast), pick it up (the pickups' carriers) or be picked by the
    // bots as a catcher (the pass's CatchWhen).
    bool FlameRoom(Player const* p)
    {
        if (!p)
            return false;
        if (p->HasItemCount(kItemFatherFlame, 1))
            return true;
        ItemPosCountVec dest;
        return p->CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, kItemFatherFlame, 1) == EQUIP_ERR_OK;
    }

    // The flame's two halves reach a player. False: the item could not be stored (every path checks FlameRoom first;
    // if the bags fill in between, the aura moves anyway, so the burn and the pass follow the holder: logged).
    bool GiveFlame(Player* p)
    {
        if (!p)
            return false;
        if (!p->HasAura(SPELL_SK_FATHER_FLAME))
            p->AddAura(SPELL_SK_FATHER_FLAME, p);
        if (p->HasItemCount(kItemFatherFlame, 1))
            return true;
        return p->AddItem(kItemFatherFlame, 1);
    }
}

struct boss_solakar_flamewreath_rework;

namespace
{
    // The live Solakar AI of `obj`'s instance (the instance tracks him by hand: GetGuidData(BOSS_SOLAKAR)).
    boss_solakar_flamewreath_rework* SolakarOf(WorldObject const* obj);
}

// Solakar Flamewreath 10264 (summoned by the instance's event, hidden until the 30 s mark)
struct boss_solakar_flamewreath_rework : public BossAI
{
    enum class Phase : uint8
    {
        Idle,       // not in an event (a GM spawn, or the event ended)
        Opening,    // hidden: the flame, the eggs and the pair run, he does not
        Arrived,    // shown, waiting for someone to engage
        Fight,
    };

    enum class FlameAt : uint8
    {
        None,
        Holder,
        Floor,      // a pickup on the floor (a death, a dropped snatch, the Hatcher's clutch)
        Brazier,    // the pickup at Father Flame after a Reclaim
        Snatched,   // the Hatcher carries it
    };

    explicit boss_solakar_flamewreath_rework(Creature* creature)
        : BossAI(creature, BOSS_SOLAKAR), _arena(SolakarArena(), LeashOptions(kBossLogName)), _room(SolakarArena()) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    // Summoned by the instance's event (IN_PROGRESS already): hidden before anyone can see or reach him, so the
    // opening's first tick never shows him (BeginOpening, on the first UpdateAI, does the rest).
    void InitializeAI() override
    {
        BossAI::InitializeAI();
        if (EventInProgress() && _phase == Phase::Idle)
            Hide(true);
    }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _phase = Phase::Fight;
        _players = OnBossPull(me, kBossLogName);
        _heroic = IsHeroicMap(me);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_SOLAKAR;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        _beats.Start(_heroic);
        _fightMs = 0;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} players={} flame={} whelps={}/{} eggs={} hunt@{}s stomp@{}s",
            _heroic ? 1 : 0, _players, FlameName(), WhelpsAlive(), WhelpCap(), LiveEggs(), kHuntFirstMs / 1000,
            kStompFirstMs / 1000));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        bool const wasFight = _phase == Phase::Fight || _phase == Phase::Arrived;
        BossAI::EnterEvadeMode(why);
        if (wasFight)
            Wipe("evade");
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("wreath={} enraged={} tosses={} reclaims={} hatched={} killer={}", _wreath,
            _enraged ? 1 : 0, _tosses, _reclaims, _hatched, killer ? killer->GetName() : "none"));
        GiveKeepsake();
        Cleanup(false);
        _phase = Phase::Idle;
    }

    void DoAction(int32 action) override
    {
        switch (action)
        {
            case ACTION_SOLAKAR_ARRIVE:
                Arrive();
                break;
            case ACTION_SOLAKAR_RESET:
                if (!_wiping)
                {
                    Cleanup(true);
                    _phase = Phase::Idle;
                }
                break;
            default:
                break;
        }
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == kPointFlame && _running)
            _runArrived = true;
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        // A broken roar (he cannot be interrupted, but a displacement could end it) still starts the chase on time:
        // the chase is booked on the AI's clock, not on the bar.
        if (spell && spell->Id == SPELL_SK_HUNT_ROAR)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hunt-roar-broken");
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        UpdateLater();

        if (_phase == Phase::Idle)
        {
            if (!EventInProgress() || me->IsEngaged())
                return;
            BeginOpening();
        }

        if (_phase == Phase::Opening || _phase == Phase::Arrived)
        {
            UpdateFlame(diff);
            UpdateEggs(diff);
            _pickups.Update(me, diff);
            WatchOpeningWipe(diff);
            if (_phase == Phase::Arrived && !me->IsEngaged())
                UpdateVictim();     // aggressive now: the first player in reach starts the fight
            return;
        }

        if (!UpdateVictim())
            return;

        _fightMs += diff;
        UpdateFlame(diff);
        UpdateEggs(diff);
        _pickups.Update(me, diff);
        UpdateWreathed();
        UpdateHunt(diff);
        UpdateRun();

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        RunBeats();
        if (me->HasUnitState(UNIT_STATE_CASTING) || Busy())
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SK1 the opening and the arrival
    // ----------------------------------------------------------------------------------------------------------------

    bool EventInProgress() const
    {
        return instance && instance->GetData(DATA_SOLAKAR_EVENT) == IN_PROGRESS;
    }

    void BeginOpening()
    {
        ++_generation;
        _later.clear();
        ClearEggs(false);
        ResetState();       // never Cleanup: the taker already holds the flame
        _phase = Phase::Opening;
        Hide(true);
        _heroic = IsHeroicMap(me);
        _players = std::max<uint8>(DungeonKit::Flex::Count(me), 5);    // a preview: the pull holds the real count
        Mechanic::BeginEncounter(me);
        GatherEggs();
        Describe();
        if (Player* holder = FindHolder())
            SetHolder(holder, ObjectGuid::Empty, "loot");
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "opening",
            Acore::StringFormat("heroic={} players={} holder={} eggs={} clutches={} arrive@{}s", _heroic ? 1 : 0,
            _players, HolderName(), LiveEggs(), _clutches.size(), kSolakarArriveMs / 1000));
    }

    void Hide(bool hide)
    {
        me->SetVisible(!hide);
        me->SetImmuneToAll(hide);
        if (hide)
        {
            me->SetReactState(REACT_PASSIVE);
            me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        }
        else
        {
            me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            me->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
            me->SetReactState(REACT_AGGRESSIVE);
        }
    }

    void Arrive()
    {
        if (_phase != Phase::Opening)
            return;
        _phase = Phase::Arrived;
        Hide(false);
        Talk(TEXT_ARRIVAL);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "arrive",
            Acore::StringFormat("flame={} holder={} whelps={} eggs={}", FlameName(), HolderName(), WhelpsAlive(),
            LiveEggs()));
        DoZoneInCombat(nullptr, 150.0f);
    }

    // Nobody alive in the Rookery for 10 s before the fight: the event fails (SK12).
    void WatchOpeningWipe(uint32 diff)
    {
        _wipeCheckMs += diff;
        if (_wipeCheckMs < 1000)
            return;
        uint32 const dt = _wipeCheckMs;
        _wipeCheckMs = 0;
        if (!RoomPlayers().empty())
        {
            _emptyMs = 0;
            return;
        }
        _emptyMs += dt;
        if (_emptyMs >= kOpeningWipeMs)
            Wipe("opening-empty");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SK4 / SK5 / SK6 the flame in hand
    // ----------------------------------------------------------------------------------------------------------------

    Player* FindHolder() const
    {
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource())
                    if (p->IsInWorld() && p->IsAlive() && p->HasAura(SPELL_SK_FATHER_FLAME))
                        return p;
        return nullptr;
    }

    Player* Holder() const
    {
        return _flameAt == FlameAt::Holder ? ObjectAccessor::GetPlayer(*me, _holder) : nullptr;
    }

    ObjectGuid HolderGuid() const
    {
        return _flameAt == FlameAt::Holder ? _holder : ObjectGuid::Empty;
    }

    bool HasFlameHolder() const
    {
        return _flameAt == FlameAt::Holder;
    }

    // `p` holds the flame now (the loot, a catch, a pickup). `thrower` empty: no catch flare.
    void SetHolder(Player* p, ObjectGuid thrower, char const* why)
    {
        CancelPickup();
        StopRun();
        if (!GiveFlame(p))
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flame-no-bag-space", p->GetName());
        _flameAt = FlameAt::Holder;
        _holder = p->GetGUID();
        _holderPos = p->GetPosition();
        _heatMs = 0;
        _heatTicks = 0;
        WriteFlame(FLAME_HOLDER);
        if (!thrower.IsEmpty())
        {
            p->CastSpell(p, SPELL_SK_CATCH_FLARE, true);
            HatchNear(p->GetPosition(), kCatchEggYd, "catch");
        }
        OnHolderChanged();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holder",
            Acore::StringFormat("{} {} at={} wounded={} hunt={}", why, p->GetName(), At(p->GetPosition()),
            p->HasAura(SPELL_SK_SPEAR_WOUND) ? 1 : 0, _hunting ? 1 : 0));
    }

    // The toss spell (210391) has landed on `catcher` (spell_brs_solakar_flame_toss).
    void TossLanded(Player* thrower, Player* catcher)
    {
        if (!thrower || !catcher || _flameAt != FlameAt::Holder || thrower->GetGUID() != _holder)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "toss-void",
                Acore::StringFormat("thrower={} catcher={} flame={}", thrower ? thrower->GetName() : "none",
                catcher ? catcher->GetName() : "none", FlameName()));
            return;
        }
        if (!catcher->IsAlive() || !CatchAllowed(catcher) || !FlameRoom(catcher))
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "toss-refused",
                Acore::StringFormat("{} -> {} (dead, Scorched or bags full)", thrower->GetName(), catcher->GetName()));
            return;
        }
        uint32 const held = _heatTicks;
        StripFlame(thrower, true);
        SetAuraMs(thrower->AddAura(SPELL_SK_SCORCHED_HANDS, thrower), ScorchedHandsMs(_heroic, IsBig(_players)));
        ++_tosses;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "toss",
            Acore::StringFormat("{} -> {} dist={:.1f} held={}s scorched={}s", thrower->GetName(), catcher->GetName(),
            thrower->GetDistance(catcher), held, ScorchedHandsMs(_heroic, IsBig(_players)) / 1000));
        SetHolder(catcher, thrower->GetGUID(), "catch");
    }

    bool CatchAllowed(Player const* catcher) const
    {
        return CanCatch(catcher->HasAura(SPELL_SK_SCORCHED_HANDS), catcher->HasAura(SPELL_SK_SPEAR_WOUND), _heroic);
    }

    // Every 250 ms: the holder is still there (else the flame drops where they were), the burn, the sear.
    void UpdateFlame(uint32 diff)
    {
        _flamePollMs += diff;
        if (_flamePollMs < kPollMs)
            return;
        uint32 const dt = _flamePollMs;
        _flamePollMs = 0;
        if (_flameAt != FlameAt::Holder)
            return;

        Player* holder = ObjectAccessor::GetPlayer(*me, _holder);
        if (!holder || !holder->IsInWorld() || holder->GetMap() != me->GetMap() || !holder->IsAlive()
            || !holder->HasAura(SPELL_SK_FATHER_FLAME))
        {
            char const* why = !holder || !holder->IsInWorld() || holder->GetMap() != me->GetMap() ? "holder-left"
                : !holder->IsAlive() ? "holder-died" : "holder-lost-aura";
            if (holder)
                StripFlame(holder, true);
            DropFlame(_holderPos, kFloorEggYd, why);
            return;
        }
        _holderPos = holder->GetPosition();

        _heatMs += dt;
        while (_heatMs >= kSearingHeatTickMs)
        {
            _heatMs -= kSearingHeatTickMs;
            ++_heatTicks;
            float const pct = SearingHeatPct(_heroic, IsBig(_players), _heatTicks);
            int32 const flat = static_cast<int32>(DungeonKit::RefFlatOn(me, holder, pct));
            if (flat > 0)
                holder->CastCustomSpell(SPELL_SK_SEARING_HEAT, SPELLVALUE_BASE_POINT0, flat, holder, true);
        }

        if (_heroic && holder->HasAura(SPELL_SK_SPEAR_WOUND))
        {
            uint32& seared = _searMs[holder->GetGUID()];
            seared += dt;
            if (seared >= kSearMs)
            {
                holder->RemoveAurasDueToSpell(SPELL_SK_SPEAR_WOUND);
                holder->CastSpell(holder, SPELL_SK_CAUTERIZE, true);
                _searMs.erase(holder->GetGUID());
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "spear-seared", holder->GetName());
            }
        }
    }

    // Whoever chases the flame learns of a new holder (the Hunt pauses a second; the Hatcher and heroic whelps poll).
    void OnHolderChanged()
    {
        if (!_hunting)
            return;
        Player* holder = Holder();
        if (!holder)
        {
            EndHunt("flame-dropped");
            return;
        }
        _huntChase.Stop(me);
        _huntResumeMs = _clockMs + kTossPauseMs;
        MarkHunted(holder);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SK7 / SK8 the flame off a hand
    // ----------------------------------------------------------------------------------------------------------------

    void DropFlame(Position const& at, float hatchYd, char const* why)
    {
        _flameAt = FlameAt::Floor;
        _holder.Clear();
        if (_hunting)
            EndHunt("flame-dropped");
        if (hatchYd > 0.f)
            HatchNear(at, hatchYd, why);
        AddFlamePickup(at, kFloorFlameMs, false);
        WriteFlame(FLAME_FLOOR);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "floor", Acore::StringFormat("{} at={}", why, At(at)));
    }

    // The flame lies at `at` as a 4 yd pickup for `lifeMs` (not Scorched).
    void AddFlamePickup(Position const& at, uint32 lifeMs, bool brazier)
    {
        CancelPickup();
        DungeonKit::PickupSpec spec;
        spec.radius = kPickupRadiusYd;
        spec.life = Ms(lifeMs);
        spec.who.auraSpell = SPELL_SK_SCORCHED_HANDS;
        spec.who.maxStacks = 0;
        spec.who.playersOnly = true;
        spec.who.carriers = RoomCarriers();     // R-2 ruling: not with full bags (judged at each arming, 6-10 s)
        spec.count = 1;
        spec.goEntry = GO_FLOOR_FLAME;
        spec.tag = TAG_FLOOR_FLAME;
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        spec.onPick = [map, bossGuid, gen](Player* taker)
        {
            if (boss_solakar_flamewreath_rework* ai = AIOf(map, bossGuid, gen))
                ai->PickedUp(taker);
        };
        spec.onExpire = [map, bossGuid, gen, at, brazier]()
        {
            if (boss_solakar_flamewreath_rework* ai = AIOf(map, bossGuid, gen))
                ai->PickupExpired(at, brazier);
        };
        _pickupId = _pickups.Add(me, at, std::move(spec));
        _flamePos = at;
        if (!_pickupId)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pickup-refused", At(at));
    }

    void CancelPickup()
    {
        if (_pickupId)
            _pickups.Cancel(me, _pickupId);
        _pickupId = 0;
    }

    void PickedUp(Player* taker)
    {
        _pickupId = 0;      // the pickup is gone
        if (!taker || (_flameAt != FlameAt::Floor && _flameAt != FlameAt::Brazier))
            return;
        bool const brazier = _flameAt == FlameAt::Brazier;
        if (!FlameRoom(taker))
        {
            // The bags filled since the pickup was armed: it stays where it lies, for someone with room.
            taker->SendEquipError(EQUIP_ERR_INVENTORY_FULL, nullptr, nullptr, kItemFatherFlame);
            AddFlamePickup(_flamePos, brazier ? kBrazierFlameMs : kFloorFlameMs, brazier);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pickup-bags-full", taker->GetName());
            return;
        }
        SetHolder(taker, ObjectGuid::Empty, brazier ? "brazier" : "floor");
    }

    // The players who may take a lying flame: everyone on the map with room in their bags. Nobody with room: the
    // boss's own guid, so the set is not empty (empty means everyone) and no player is eligible.
    GuidSet RoomCarriers() const
    {
        GuidSet out;
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource(); p && FlameRoom(p))
                    out.insert(p->GetGUID());
        if (out.empty())
            out.insert(me->GetGUID());
        return out;
    }

    // Unclaimed: in the fight he leaves the tank and runs for it (it stays claimable until he gets there); before he
    // is out it simply lies there.
    void PickupExpired(Position const& at, bool brazier)
    {
        _pickupId = 0;
        if (_flameAt != FlameAt::Floor && _flameAt != FlameAt::Brazier)
            return;
        AddFlamePickup(at, _phase == Phase::Fight ? kRunPickupMs : (brazier ? kBrazierFlameMs : kFloorFlameMs),
            brazier);
        if (_phase == Phase::Fight)
            RunForFlame(at, brazier ? "brazier-unclaimed" : "floor-unclaimed");
    }

    void RunForFlame(Position const& at, char const* why)
    {
        if (_hunting)
            EndHunt("run");
        _running = true;
        _runArrived = false;
        _runTo = at;
        _runStartMs = _clockMs;
        _runBudgetMs = RunBudgetMs(me->GetExactDist2d(at.GetPositionX(), at.GetPositionY()), me->GetSpeed(MOVE_RUN));
        me->InterruptNonMeleeSpells(false);
        me->SetCombatMovement(false);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(kPointFlame, at);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "run", Acore::StringFormat("{} to={}", why, At(at)));
    }

    void StopRun()
    {
        if (!_running)
            return;
        _running = false;
        _runArrived = false;
        me->SetCombatMovement(true);
        if (Unit* victim = me->GetVictim())
        {
            me->GetMotionMaster()->Clear();
            AttackStart(victim);
        }
    }

    void UpdateRun()
    {
        if (!_running)
            return;
        if (_runArrived || me->GetExactDist2d(_runTo.GetPositionX(), _runTo.GetPositionY()) <= kReclaimReachYd)
        {
            Reclaim("run");
            return;
        }
        if (RunGivesUp(_runStartMs, _runBudgetMs, _clockMs))
        {
            Reclaim("run-unreachable");     // R-2 m-5: never a free target over a flame he cannot reach
            return;
        }
        if (_runRepathMs <= _clockMs)
        {
            _runRepathMs = _clockMs + 1000;
            if (me->GetMotionMaster()->GetCurrentMovementGeneratorType() != POINT_MOTION_TYPE)
                me->GetMotionMaster()->MovePoint(kPointFlame, _runTo);
        }
    }

    bool Busy() const
    {
        return _running || _hunting;
    }

    // SK8: he has the flame (the hunted holder caught, or the floor or the brazier reached).
    void Reclaim(char const* why)
    {
        if (Player* holder = Holder())
            StripFlame(holder, true);
        CancelPickup();
        bool const wasRunning = _running;
        _running = false;
        if (_hunting)
            EndHunt("reclaim");
        if (wasRunning)
            StopRunMovement();
        _holder.Clear();
        _flameAt = FlameAt::Brazier;
        ++_reclaims;
        Talk(TEXT_RECLAIM);
        AddWreath(why);
        Stir();
        Position const brazier = DungeonKit::ToPosition(Vec2{ kFatherFlame.x, kFatherFlame.y }, kFatherFlame.z);
        AddFlamePickup(brazier, kBrazierFlameMs, true);
        WriteFlame(FLAME_BRAZIER);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "reclaim",
            Acore::StringFormat("{} n={} wreath={} enraged={}", why, _reclaims, _wreath, _enraged ? 1 : 0));
    }

    void StopRunMovement()
    {
        me->SetCombatMovement(true);
        me->GetMotionMaster()->Clear();
        if (Unit* victim = me->GetVictim())
            AttackStart(victim);
    }

    // A Reclaim or a torn wound: +1 Flamewreath, or the enrage at 3.
    void AddWreath(char const* why)
    {
        WreathStep const step = BrsSolakar::AddWreath(_wreath, _enraged);
        if (step.stacks != _wreath)
        {
            _wreath = DungeonKit::AddStacks(me, _heroic ? SPELL_SK_FLAMEWREATH_H : SPELL_SK_FLAMEWREATH, 1, me,
                kFlamewreathCap);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flamewreath",
                Acore::StringFormat("{} stacks={} mult={:.2f}", why, _wreath, WreathMult(_heroic, _wreath)));
        }
        if (step.enrage)
            Enrage(why);
    }

    void Enrage(char const* why)
    {
        _enraged = true;
        me->AddAura(SPELL_SK_WREATHED, me);
        Talk(TEXT_WREATHED);
        _nextWreathedMs = _clockMs;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "wreathed", why);
    }

    // SK8 enrage: 10% Fire to everyone every 2 s, unavoidable (a fixed percent: it is already his ceiling).
    void UpdateWreathed()
    {
        if (!_enraged || _clockMs < _nextWreathedMs)
            return;
        _nextWreathedMs = _clockMs + kWreathedTickMs;
        int32 const hundredths = static_cast<int32>(kWreathedPct * 100.f);
        for (Player* p : RoomPlayers())
            me->CastCustomSpell(SPELL_SK_WREATHED_TICK, SPELLVALUE_BASE_POINT0, hundredths, p, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SK2 the Hatcher (its AI calls these)
    // ----------------------------------------------------------------------------------------------------------------

    // The Hatcher reached `victim`: it takes the flame and runs for the nearest clutch of 3 or more eggs. Nullopt: no
    // such clutch, it drops the flame where it stands (a 6 yd hatch).
    std::optional<Position> HatcherSnatch(Creature* hatcher, Player* victim)
    {
        if (!hatcher || !victim || _flameAt != FlameAt::Holder || victim->GetGUID() != _holder)
            return std::nullopt;
        StripFlame(victim, true);
        _holder.Clear();
        _flameAt = FlameAt::Snatched;
        _hatcher = hatcher->GetGUID();
        if (_hunting)
            EndHunt("snatched");
        WriteFlame(FLAME_FLOOR);
        std::optional<Vec2> const clutch = NearestClutch(_eggXY, _live, _clutches, XY(hatcher->GetPosition()));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "snatch",
            Acore::StringFormat("from={} at={} clutch={}", victim->GetName(), At(hatcher->GetPosition()),
            clutch ? Acore::StringFormat("({:.1f}, {:.1f})", clutch->x, clutch->y) : std::string("none")));
        if (!clutch)
        {
            DropFlame(hatcher->GetPosition(), kFloorEggYd, "snatch-no-clutch");
            return std::nullopt;
        }
        Position spot = hatcher->GetPosition();
        spot.Relocate(clutch->x, clutch->y, ClutchZ(*clutch, hatcher->GetPositionZ()));
        return spot;
    }

    // The Hatcher dropped it on the way (killed or stunned): a floor pickup, a 6 yd hatch.
    void HatcherDropped(Creature* hatcher, char const* why)
    {
        if (!hatcher || _flameAt != FlameAt::Snatched || hatcher->GetGUID() != _hatcher)
            return;
        _hatcher.Clear();
        DropFlame(hatcher->GetPosition(), kFloorEggYd, why);
    }

    // The Hatcher reached its clutch: every egg within 6 yd hatches and the flame drops there.
    void HatcherAtClutch(Creature* hatcher)
    {
        if (!hatcher || _flameAt != FlameAt::Snatched || hatcher->GetGUID() != _hatcher)
            return;
        _hatcher.Clear();
        HatchNear(hatcher->GetPosition(), kHatcherClutchYd, "hatcher-clutch");
        DropFlame(hatcher->GetPosition(), 0.f, "hatcher-clutch");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SK9 the Hunt
    // ----------------------------------------------------------------------------------------------------------------

    void StartHunt()
    {
        Player* holder = Holder();
        if (!holder)
            return;
        DungeonKit::CastBar(me, SPELL_SK_HUNT_ROAR, nullptr, TEXT_HUNT);
        _hunting = true;
        _huntResumeMs = _clockMs + kHuntRoarMs;
        _huntEndMs = _clockMs + kHuntRoarMs + kHuntChaseMs;
        _huntChasing = false;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hunt",
            Acore::StringFormat("holder={} dist={:.1f} next@{}s", holder->GetName(), me->GetDistance(holder),
            _beats.NextHunt() / 1000));
    }

    void UpdateHunt(uint32 diff)
    {
        if (!_hunting)
            return;
        if (_clockMs >= _huntEndMs)
        {
            EndHunt("time");
            return;
        }
        if (_huntChase.Active())
        {
            _huntChase.Update(me, diff);
            if (!_huntCaught.IsEmpty())
            {
                ObjectGuid const caught = _huntCaught;
                _huntCaught.Clear();
                if (caught == HolderGuid())
                    Reclaim("hunt");
                else
                    _huntResumeMs = _clockMs;     // a stale target: aim again
            }
            return;
        }
        if (_clockMs < _huntResumeMs || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        Player* holder = Holder();
        if (!holder)
        {
            EndHunt("no-holder");
            return;
        }
        if (!_huntChasing)
        {
            _huntChasing = true;
            me->AddAura(SPELL_SK_HUNT, me);
        }
        ChaseHolder(holder);
    }

    void ChaseHolder(Player* holder)
    {
        DungeonKit::ChaserSpec spec;
        spec.speed = 0.f;               // his own run speed: 1.43, about 10 yd/s
        spec.honorSlows = true;
        spec.reach = kReclaimReachYd;
        spec.pauseOnControl = Ms(kTossPauseMs);
        spec.life = Ms(static_cast<uint32>(_huntEndMs > _clockMs ? _huntEndMs - _clockMs : 1));
        spec.endOnArrive = true;
        spec.tauntImmune = true;
        spec.fixate = true;
        spec.pick.nonTank = false;
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        spec.onArrive = [map, bossGuid, gen](Creature*, Unit* target)
        {
            if (boss_solakar_flamewreath_rework* ai = AIOf(map, bossGuid, gen))
                if (target)
                    ai->_huntCaught = target->GetGUID();
        };
        // A new target the kit picked (its target died): not the flame's; the next poll ends or re-aims the Hunt.
        spec.onTarget = [map, bossGuid, gen](Creature* chaser, Unit*)
        {
            if (boss_solakar_flamewreath_rework* ai = AIOf(map, bossGuid, gen))
            {
                ai->_huntChase.Stop(chaser);
                ai->_huntResumeMs = ai->_clockMs;
            }
        };
        if (_huntChase.Start(me, holder, std::move(spec), me))
            MarkHunted(holder);
    }

    // The red ring and the debuff on the hunted holder (a decoy circle: drawn, never resolves, bots never see it).
    void MarkHunted(Player* holder)
    {
        if (_huntRing)
            Mechanic::Cancel(me, _huntRing);
        _huntRing = {};
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource(); p && p != holder)
                    p->RemoveAurasDueToSpell(SPELL_SK_HUNTED);
        if (!holder || _clockMs >= _huntEndMs)
            return;
        uint32 const left = static_cast<uint32>(_huntEndMs - _clockMs);
        _huntRing = Mechanic::Circle(me, holder, 3.f, Ms(left)).Decoy().Tag(TAG_HUNT_RING);
        SetAuraMs(holder->AddAura(SPELL_SK_HUNTED, holder), left);
    }

    void EndHunt(char const* why)
    {
        if (!_hunting)
            return;
        _hunting = false;
        _huntChasing = false;
        _huntCaught.Clear();
        _huntChase.Stop(me);
        if (_huntRing)
            Mechanic::Cancel(me, _huntRing);
        _huntRing = {};
        me->RemoveAurasDueToSpell(SPELL_SK_HUNT);
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource())
                    p->RemoveAurasDueToSpell(SPELL_SK_HUNTED);
        _beats.HuntEnded(_fightMs);
        if (!_running)
        {
            me->SetCombatMovement(true);
            if (Unit* victim = me->GetVictim())
            {
                me->GetMotionMaster()->Clear();
                AttackStart(victim);
            }
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hunt-end", why);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats: the Hunt, War Stomp, Spear Wound
    // ----------------------------------------------------------------------------------------------------------------

    void RunBeats()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        Beat const beat = _beats.Next(_fightMs, !_running, HasFlameHolder());
        switch (beat)
        {
            case Beat::Hunt:
                StartHunt();
                break;
            case Beat::Stomp:
                StartWarStomp();
                break;
            case Beat::Spear:
                ThrowSpears(false);
                break;
            case Beat::None:
                if (_fightMs >= _beats.NextHunt() && !HasFlameHolder() && !_beats.InHunt(_fightMs))
                    _beats.HuntWaits(_fightMs);
                return;
        }
        _beats.Started(beat, _fightMs);
    }

    // SK10: a 2 s bar and an 8 yd circle on him, 25% (raised by Flamewreath), Weakened, a 2 s stun; the tank too.
    void StartWarStomp()
    {
        DungeonKit::CastBar(me, SPELL_SK_WAR_STOMP_BAR);
        float const pct = kWarStompPct * WreathMult(_heroic, _wreath);
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        MechanicRef ref = Mechanic::Circle(me, me, kStompRadiusYd, Ms(kStompCastMs));
        ref.Damage(pct).Weakened().Spell(SPELL_SK_WAR_STOMP).Rider(SPELL_SK_WAR_STOMP_STUN).Tag(TAG_WAR_STOMP);
        ref.OnResolve([map, bossGuid](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled)
                return;
            if (Creature* boss = map ? map->GetCreature(bossGuid) : nullptr)
                if (boss->IsAlive())
                    boss->CastSpell(boss, SPELL_SK_STOMP_LOOK, true);
        });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "war-stomp",
            Acore::StringFormat("pct={:.1f} next@{}s", pct, (_fightMs + kStompEveryMs) / 1000));
    }

    // SK11 (heroic): 1 / 2 players, never the holder, the tank too.
    uint32 ThrowSpears(bool test)
    {
        if (!_heroic && !test)
            return 0;
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = 100.f;
        if (!_holder.IsEmpty())
            rule.exclude.push_back(_holder.GetRawValue());
        std::vector<Player*> const targets = DungeonKit::PickPlayers(me, rule, kSpearTargets.At(_players));
        for (Player* t : targets)
            me->CastSpell(t, SPELL_SK_SPEAR_THROW, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "spear",
            Acore::StringFormat("targets={} next-hunt@{}s", targets.size(), _beats.NextHunt() / 1000));
        return static_cast<uint32>(targets.size());
    }

    // The spear (210411) has landed: the wound (12 s, then it tears) from him.
    void SpearHit(Unit* target)
    {
        if (!target || !target->IsAlive())
            return;
        me->AddAura(SPELL_SK_SPEAR_WOUND, target);
        _searMs.erase(target->GetGUID());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "spear-wound", target->GetName());
    }

    // The wound ran its 12 s (spell_brs_solakar_spear_wound): 40% (raised by Flamewreath) and a stack.
    void WoundTore(Unit* target)
    {
        if (!target || !target->IsAlive() || !me->IsAlive() || _phase != Phase::Fight)
            return;
        int32 const hundredths = static_cast<int32>(kSpearTearPct * WreathMult(_heroic, _wreath) * 100.f);
        me->CastCustomSpell(SPELL_SK_SPEAR_TEAR, SPELLVALUE_BASE_POINT0, hundredths, target, true);
        Talk(TEXT_SPEAR_RETURNS);
        _searMs.erase(target->GetGUID());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "spear-tear", target->GetName());
        AddWreath("spear-tear");
    }

    uint32 Wreath() const { return _wreath; }
    bool Heroic() const { return _heroic; }

    // ----------------------------------------------------------------------------------------------------------------
    // SK6 the eggs and the flame whelps
    // ----------------------------------------------------------------------------------------------------------------

    struct Egg
    {
        ObjectGuid guid;
        Position pos;
        bool hatched = false;   // hatched by the flame: kept despawned until the reset
        bool warm = false;      // waiting for room under the whelp cap
    };

    // The stock eggs (175124) on the Rookery floor, their clutches and one registry zone per clutch (no damage, no
    // marker: the bots step around them and the pass counts them, PassEntry::FewestZones).
    void GatherEggs()
    {
        ClearEggs(false);
        std::list<GameObject*> found;
        me->GetGameObjectListWithEntryInGrid(found, GO_ROOKERY_EGG, kEggSearchYd);
        std::vector<GameObject*> eggs;
        for (GameObject* go : found)
            if (_room.Contains(XY(go->GetPosition()), go->GetPositionZ()))
                eggs.push_back(go);
        std::sort(eggs.begin(), eggs.end(), [](GameObject const* a, GameObject const* b)
        {
            return a->GetSpawnId() < b->GetSpawnId();
        });
        for (GameObject* go : eggs)
        {
            _eggs.push_back({ go->GetGUID(), go->GetPosition(), false, false });
            _eggXY.push_back(XY(go->GetPosition()));
            _live.push_back(go->isSpawned());
        }
        _clutches = BuildClutches(_eggXY);
        _clutchZones.assign(_clutches.size(), MechanicHandle{});
        _clutchLive.assign(_clutches.size(), 0);
        for (std::size_t i = 0; i < _clutches.size(); ++i)
            RegisterClutch(i);
    }

    float ClutchZ(Vec2 center, float fallback) const
    {
        float z = 0.f;
        uint32 n = 0;
        for (std::size_t i = 0; i < _eggs.size(); ++i)
            if (DungeonKit::Distance(_eggXY[i], center) <= kClutchMaxYd + 1.f)
            {
                z += _eggs[i].pos.GetPositionZ();
                ++n;
            }
        return n ? z / static_cast<float>(n) : fallback;
    }

    void RegisterClutch(std::size_t i)
    {
        if (_clutchZones[i])
            Mechanic::Cancel(me, _clutchZones[i]);
        _clutchZones[i] = {};
        std::optional<Clutch> const part = LivePart(_eggXY, _live, _clutches[i]);
        _clutchLive[i] = part ? static_cast<uint32>(part->eggs.size()) : 0;
        if (!part)
            return;
        Position at;
        at.Relocate(part->center.x, part->center.y, ClutchZ(part->center, me->GetPositionZ()));
        _clutchZones[i] = Mechanic::Circle(me, at, ClutchZoneRadius(part->radius), Ms(0))
            .Persistent(Minutes(kClutchZoneMinutes), Ms(1000)).NoTelegraph().Tag(TAG_EGG_CLUTCH);
    }

    uint32 LiveEggs() const
    {
        return static_cast<uint32>(std::count(_live.begin(), _live.end(), true));
    }

    // Every second: an egg the stock trap set off (a player within 1.5 yd: a stock whelp, the egg back in 2 min) leaves
    // or rejoins its clutch's zone; the warm eggs hatch while there is room under the cap.
    void UpdateEggs(uint32 diff)
    {
        _eggPollMs += diff;
        if (_eggPollMs < kEggPollMs)
            return;
        _eggPollMs = 0;
        std::vector<bool> dirty(_clutches.size(), false);
        for (std::size_t i = 0; i < _eggs.size(); ++i)
        {
            if (_eggs[i].hatched)
                continue;
            GameObject* go = me->GetMap()->GetGameObject(_eggs[i].guid);
            bool const live = go && go->isSpawned();
            if (live != _live[i])
            {
                _live[i] = live;
                MarkDirty(i, dirty);
            }
        }
        while (!_warmQueue.empty() && WhelpsAlive() < WhelpCap())
        {
            std::size_t const i = _warmQueue.front();
            _warmQueue.erase(_warmQueue.begin());
            _eggs[i].warm = false;
            if (_live[i] && Hatch(i, "warm"))
                MarkDirty(i, dirty);
        }
        for (std::size_t c = 0; c < dirty.size(); ++c)
            if (dirty[c])
                RegisterClutch(c);
    }

    void MarkDirty(std::size_t egg, std::vector<bool>& dirty) const
    {
        for (std::size_t c = 0; c < _clutches.size(); ++c)
            if (std::find(_clutches[c].eggs.begin(), _clutches[c].eggs.end(), egg) != _clutches[c].eggs.end())
                dirty[c] = true;
    }

    uint32 WhelpCap() const
    {
        return kWhelpCap.At(_players);
    }

    uint32 WhelpsAlive() const
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : summons)
            if (Creature* c = me->GetMap()->GetCreature(guid))
                if (c->GetEntry() == NPC_BRS_FLAME_WHELP && c->IsAlive())
                    ++n;
        return n;
    }

    // One egg hatches into a flame whelp (true), or waits warm past the cap (false).
    bool Hatch(std::size_t i, char const* why)
    {
        if (!_live[i] || _eggs[i].hatched)
            return false;
        if (WhelpsAlive() >= WhelpCap())
        {
            if (!_eggs[i].warm)
            {
                _eggs[i].warm = true;
                _warmQueue.push_back(i);
            }
            return false;
        }
        if (GameObject* go = me->GetMap()->GetGameObject(_eggs[i].guid))
            go->DespawnOrUnsummon(0ms, Seconds(kEggHatchedRespawnSec));
        _eggs[i].hatched = true;
        _live[i] = false;
        ++_hatched;
        me->SummonCreature(NPC_BRS_FLAME_WHELP, _eggs[i].pos, TEMPSUMMON_CORPSE_TIMED_DESPAWN, 15000);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hatch",
            Acore::StringFormat("{} at={} whelps={}/{}", why, At(_eggs[i].pos), WhelpsAlive(), WhelpCap()));
        return true;
    }

    void HatchNear(Position const& at, float r, char const* why)
    {
        std::vector<std::size_t> const eggs = EggsWithin(_eggXY, _live, XY(at), r);
        std::vector<bool> dirty(_clutches.size(), false);
        uint32 hatched = 0;
        uint32 warm = 0;
        for (std::size_t i : eggs)
        {
            if (Hatch(i, why))
            {
                ++hatched;
                MarkDirty(i, dirty);
            }
            else
                ++warm;
        }
        for (std::size_t c = 0; c < dirty.size(); ++c)
            if (dirty[c])
                RegisterClutch(c);
        if (!eggs.empty())
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hatch-near",
                Acore::StringFormat("{} at={} r={:.0f} hatched={} warm={}", why, At(at), r, hatched, warm));
    }

    // SK8: the Rookery stirs, the egg nearest each player hatches.
    void Stir()
    {
        for (Player* p : RoomPlayers())
            if (std::optional<std::size_t> const egg = NearestEgg(_eggXY, _live, XY(p->GetPosition())))
            {
                std::vector<bool> dirty(_clutches.size(), false);
                if (Hatch(*egg, "stir"))
                    MarkDirty(*egg, dirty);
                for (std::size_t c = 0; c < dirty.size(); ++c)
                    if (dirty[c])
                        RegisterClutch(c);
            }
    }

    // The zones go; with `restore` the hatched eggs come back (a wipe: a fair retry) with their stock respawn.
    void ClearEggs(bool restore)
    {
        for (MechanicHandle& h : _clutchZones)
            if (h)
                Mechanic::Cancel(me, h);
        if (restore)
            for (Egg const& egg : _eggs)
                if (egg.hatched)
                    if (GameObject* go = me->GetMap()->GetGameObject(egg.guid))
                    {
                        if (GameObjectData const* data = go->GetGameObjectData())
                            go->SetRespawnDelay(data->spawntimesecs);
                        go->Respawn();
                    }
        _clutchZones.clear();
        _clutchLive.clear();
        _clutches.clear();
        _eggs.clear();
        _eggXY.clear();
        _live.clear();
        _warmQueue.clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data: kill order and the flame's pass (Blackrock Spire WP-PS)
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        bool const big = IsBig(_players);
        PassEntry flame = PassEntry::WithItem(SPELL_SK_FATHER_FLAME, kItemFatherFlame, kTossRangeYd);
        // R-2 ruling: nobody with full bags catches (a Custom condition, judged by the bot view on each candidate).
        BossCondition const notScorched = _heroic ? BossCondition::AnyOf({
                BossCondition::LacksAura(SPELL_SK_SCORCHED_HANDS), BossCondition::HasAura(SPELL_SK_SPEAR_WOUND) })
            : BossCondition::LacksAura(SPELL_SK_SCORCHED_HANDS);
        flame.CatchWhen(BossCondition::AllOf({ notScorched, BossCondition::Custom([](Unit const* u)
            {
                return FlameRoom(u ? u->ToPlayer() : nullptr);
            }) }));
        // R-2 m-4: hidden in the opening, he is no unit to keep away from (the engage describes again, with him).
        if (_phase != Phase::Opening)
            flame.FarFrom(NPC_SOLAKAR);
        flame.FarFrom(NPC_ROOKERY_HATCHER).KeepFrom(kCatcherKeepFromYd)
            .FewestZones(TAG_EGG_CLUTCH, kCatchEggYd)
            .When(PassTrigger::UnitNear(NPC_SOLAKAR, kThrowTriggerYd, BossCondition::HasAura(SPELL_SK_HUNT)))
            .When(PassTrigger::Casting(NPC_SOLAKAR, SPELL_SK_HUNT_ROAR, kThrowTriggerYd))
            .When(PassTrigger::UnitNear(NPC_ROOKERY_HATCHER, kThrowTriggerYd))
            .When(PassTrigger::UnitNear(NPC_SOLAKAR, kUrgentThrowYd, BossCondition::HasAura(SPELL_SK_HUNT)).Urgent())
            .When(PassTrigger::HeldFor(Ms(ThrowHoldMs(_heroic, big))))
            .Flight(Ms(kTossFlightMs))
            .ReadyCatchers(kReadyCatchers.At(_players))
            .Room(48.5f, -338.f, 107.5f, -252.5f);      // the Rookery box (handoff section 3.8, NM 10)
        if (_heroic)
            flame.Prefer(BossCondition::HasAura(SPELL_SK_SPEAR_WOUND))
                .MinHold(Ms(kSearMs), BossCondition::HasAura(SPELL_SK_SPEAR_WOUND));

        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_ROOKERY_HATCHER, static_cast<int8>(3));
        d.targets.emplace_back(NPC_ROOKERY_GUARDIAN, static_cast<int8>(2));
        if (_heroic)
        {
            BossMechanics::TargetEntry whelps(NPC_BRS_FLAME_WHELP, 1);
            whelps.AoeOk();
            d.targets.push_back(std::move(whelps));
        }
        d.passes.push_back(std::move(flame));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs solakar` entry points
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Arrive,
        Hunt,
        Stomp,
        Spear,
        Reclaim,
        Drop,
        Hatch,
        Reset,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, Player* gm)
    {
        if (mechanic == TestMechanic::Arrive)
        {
            if (_phase != Phase::Opening)
                return "Solakar is not hidden in an opening (`.dbtest brs solakar start` first).";
            Arrive();
            return {};
        }
        if (mechanic == TestMechanic::Reset)
        {
            Wipe("gm");
            return {};
        }
        if (mechanic == TestMechanic::Hatch)
        {
            if (_phase == Phase::Idle)
                return "No event: no eggs are tracked (`.dbtest brs solakar start`).";
            HatchNear(gm->GetPosition(), kHatcherClutchYd, "gm");
            return {};
        }
        if (mechanic == TestMechanic::Drop)
        {
            Player* holder = Holder();
            if (!holder)
                return "Nobody holds Father Flame.";
            Position const at = holder->GetPosition();
            StripFlame(holder, true);
            DropFlame(at, kFloorEggYd, "gm");
            return {};
        }
        if (_phase != Phase::Fight)
            return "Solakar must be in the fight (after the arrival) for this one.";
        switch (mechanic)
        {
            case TestMechanic::Hunt:
                if (!HasFlameHolder())
                    return "Nobody holds Father Flame: there is nothing to hunt.";
                if (_hunting)
                    return "He is hunting already.";
                StartHunt();
                _beats.Started(Beat::Hunt, _fightMs);
                break;
            case TestMechanic::Stomp:
                StartWarStomp();
                break;
            case TestMechanic::Spear:
                if (!ThrowSpears(true))
                    return "No player to throw the spear at (`.gm off`).";
                break;
            case TestMechanic::Reclaim:
                Reclaim("gm");
                break;
            default:
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("phase={} clock={}s fight={}s players={} heroic={} flame={} holder={} held={}s "
            "wreath={} enraged={} hunting={} running={} hunt@{}s stomp@{}s spear@{} whelps={}/{} eggs={} warm={} "
            "clutches={} tosses={} reclaims={} hatched={}", PhaseName(), _clockMs / 1000, _fightMs / 1000, _players,
            _heroic ? 1 : 0, FlameName(), HolderName(), _heatTicks, _wreath, _enraged ? 1 : 0, _hunting ? 1 : 0,
            _running ? 1 : 0, _beats.NextHunt() / 1000, _beats.NextStomp() / 1000,
            _beats.NextSpear() >= FightClock::kNever ? std::string("-") : std::to_string(_beats.NextSpear() / 1000),
            WhelpsAlive(), WhelpCap(), LiveEggs(), _warmQueue.size(), _clutches.size(), _tosses, _reclaims, _hatched);
    }

    char const* PhaseName() const
    {
        switch (_phase)
        {
            case Phase::Idle:       return "idle";
            case Phase::Opening:    return "opening";
            case Phase::Arrived:    return "arrived";
            case Phase::Fight:      return "fight";
        }
        return "?";
    }

    char const* FlameName() const
    {
        switch (_flameAt)
        {
            case FlameAt::None:     return "none";
            case FlameAt::Holder:   return "held";
            case FlameAt::Floor:    return "floor";
            case FlameAt::Brazier:  return "brazier";
            case FlameAt::Snatched: return "snatched";
        }
        return "?";
    }

    std::string HolderName() const
    {
        Player* p = Holder();
        return p ? p->GetName() : std::string("none");
    }

    // The live AI of this boss on `map`, if it is still the same pull (`gen`). Captures are the map and guids only.
    static boss_solakar_flamewreath_rework* AIOf(Map* map, ObjectGuid bossGuid, uint32 gen)
    {
        Creature* boss = map ? map->GetCreature(bossGuid) : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        auto* ai = dynamic_cast<boss_solakar_flamewreath_rework*>(boss->AI());
        return ai && ai->_generation == gen ? ai : nullptr;
    }

private:
    struct Pending
    {
        uint64 dueMs = 0;
        std::function<void()> fn;
    };

    // The living players in the Rookery (not game masters).
    std::vector<Player*> RoomPlayers() const
    {
        std::vector<Player*> out;
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource(); LivePlayer(p)
                    && _room.Contains(XY(p->GetPosition()), p->GetPositionZ()))
                    out.push_back(p);
        return out;
    }

    void WriteFlame(uint32 state)
    {
        if (instance && instance->GetData(DATA_SOLAKAR_FLAME) != state)
            instance->SetData(DATA_SOLAKAR_FLAME, state);
    }

    // The event failed (SK12): everything goes, and the instance resets the event (Father Flame ready again).
    void Wipe(char const* why)
    {
        if (_wiping)
            return;
        _wiping = true;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "wipe",
            Acore::StringFormat("{} phase={} flame={} wreath={} tosses={} reclaims={} hatched={}", why, PhaseName(),
            FlameName(), _wreath, _tosses, _reclaims, _hatched));
        Cleanup(true);
        _phase = Phase::Idle;
        if (instance)
            instance->SetData(DATA_SOLAKAR_EVENT, FAIL);     // the instance despawns the event's units, him too
        _wiping = false;
    }

    // The pull's state (a wipe, a reset, his death). The flame leaves every player (aura and item: the toss item is the
    // fight's, R-2 ruling); `wipe`: the hatched eggs come back too.
    void Cleanup(bool wipe)
    {
        ++_generation;      // callbacks of an older pull stop
        _later.clear();
        _pickups.Clear(me);
        _pickupId = 0;
        _huntChase.Stop(me);
        if (_huntRing)
            Mechanic::Cancel(me, _huntRing);
        _huntRing = {};
        ClearEggs(wipe);
        summons.DespawnAll();
        me->RemoveAurasDueToSpell(SPELL_SK_FLAMEWREATH);
        me->RemoveAurasDueToSpell(SPELL_SK_FLAMEWREATH_H);
        me->RemoveAurasDueToSpell(SPELL_SK_WREATHED);
        me->RemoveAurasDueToSpell(SPELL_SK_HUNT);
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource())
                {
                    StripFlame(p, true);
                    p->RemoveAurasDueToSpell(SPELL_SK_SCORCHED_HANDS);
                    p->RemoveAurasDueToSpell(SPELL_SK_SPEAR_WOUND);
                }
        if (_running || _hunting)
            me->SetCombatMovement(true);
        ResetState();
        if (wipe)
            WriteFlame(FLAME_NONE);
    }

    // His death: whoever holds the flame takes the stock Father Flame 13371 home, the keepsake (R-2 ruling: the toss
    // item 70610 is the fight's and goes; stock gave the chest's taker one 13371 a run). Their own copy stops it
    // (unique); the toss item's slot is freed first, so there is room.
    void GiveKeepsake()
    {
        Player* holder = Holder();
        if (!holder || holder->HasItemCount(kItemFatherFlameKeepsake, 1, true))
            return;
        StripFlame(holder, true);
        bool const given = holder->AddItem(kItemFatherFlameKeepsake, 1);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "keepsake",
            Acore::StringFormat("{} given={}", holder->GetName(), given ? 1 : 0));
    }

    // The AI's own state back to a new pull's (no world effect).
    void ResetState()
    {
        _flameAt = FlameAt::None;
        _holder.Clear();
        _hatcher.Clear();
        _huntCaught.Clear();
        _searMs.clear();
        _beats.Start(_heroic);
        _arena.Reset();
        _fightMs = 0;
        _heatMs = 0;
        _heatTicks = 0;
        _flamePollMs = 0;
        _eggPollMs = 0;
        _wipeCheckMs = 0;
        _emptyMs = 0;
        _wreath = 0;
        _enraged = false;
        _hunting = false;
        _huntChasing = false;
        _running = false;
        _runArrived = false;
        _tosses = 0;
        _reclaims = 0;
        _hatched = 0;
    }

    // `fn` after `delayMs` on the AI's own clock; a Cleanup drops what is pending.
    void Later(uint32 delayMs, std::function<void()> fn)
    {
        _later.push_back({ _clockMs + delayMs, std::move(fn) });
    }

    void UpdateLater()
    {
        if (_later.empty())
            return;
        std::vector<Pending> due;
        for (auto it = _later.begin(); it != _later.end();)
        {
            if (_clockMs >= it->dueMs)
            {
                due.push_back(std::move(*it));
                it = _later.erase(it);
            }
            else
                ++it;
        }
        for (Pending& p : due)
            p.fn();
    }

    DungeonKit::ArenaGuard _arena;
    Arena const _room;
    DungeonKit::Pickups _pickups;
    DungeonKit::Chaser _huntChase;
    FightClock _beats;
    std::vector<Pending> _later;
    std::vector<Egg> _eggs;
    std::vector<Vec2> _eggXY;
    std::vector<bool> _live;
    std::vector<Clutch> _clutches;
    std::vector<MechanicHandle> _clutchZones;
    std::vector<uint32> _clutchLive;
    std::vector<std::size_t> _warmQueue;
    std::unordered_map<ObjectGuid, uint32> _searMs;     // a wounded player's time holding the flame
    MechanicHandle _huntRing;
    ObjectGuid _holder;
    ObjectGuid _hatcher;
    ObjectGuid _huntCaught;
    Position _holderPos;
    Position _flamePos;
    Position _runTo;
    Phase _phase = Phase::Idle;
    FlameAt _flameAt = FlameAt::None;
    uint64 _clockMs = 0;            // the AI's own clock (the opening and the fight)
    uint64 _fightMs = 0;            // ms since the pull: the beats
    uint64 _huntEndMs = 0;
    uint64 _huntResumeMs = 0;
    uint64 _nextWreathedMs = 0;
    uint64 _runRepathMs = 0;
    uint64 _runStartMs = 0;
    uint64 _runBudgetMs = 0;
    uint32 _generation = 0;
    uint32 _pickupId = 0;
    uint32 _heatMs = 0;
    uint32 _heatTicks = 0;          // seconds the current holder has burned
    uint32 _flamePollMs = 0;
    uint32 _eggPollMs = 0;
    uint32 _wipeCheckMs = 0;
    uint32 _emptyMs = 0;
    uint32 _wreath = 0;             // Flamewreath stacks
    uint32 _tosses = 0;
    uint32 _reclaims = 0;
    uint32 _hatched = 0;
    uint8 _players = 5;             // the flex count (a preview in the opening, held at the pull)
    bool _heroic = false;
    bool _enraged = false;
    bool _hunting = false;          // from the roar to the end of the chase
    bool _huntChasing = false;
    bool _running = false;          // running for an unclaimed flame
    bool _runArrived = false;
    bool _wiping = false;
};

namespace
{
    boss_solakar_flamewreath_rework* SolakarOf(WorldObject const* obj)
    {
        InstanceScript* instance = obj ? obj->GetInstanceScript() : nullptr;
        if (!instance)
            return nullptr;
        Creature* boss = obj->GetMap()->GetCreature(instance->GetGuidData(BOSS_SOLAKAR));
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_solakar_flamewreath_rework*>(boss->AI());
    }

    bool Stunned(Creature const* c)
    {
        return c->HasUnitState(UNIT_STATE_STUNNED) || c->HasAuraType(SPELL_AURA_MOD_STUN);
    }
}

// Rookery Hatcher 10683 (SK2): chases the holder, snatches the flame, runs it to a clutch.
struct npc_brs_rookery_hatcher : public ScriptedAI
{
    explicit npc_brs_rookery_hatcher(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        EndCarry(false);
        _chase.Stop(me);
        _target.Clear();
        _arrived.Clear();
        _strikeMs = urand(kStrikeFirstMinMs, kStrikeFirstMaxMs);
        _sunderMs = urand(kSunderFirstMinMs, kSunderFirstMaxMs);
    }

    // The instance summons it with no summoner (no IsSummonedBy): it joins the fight as it enters the world (the stock
    // SmartAI's "on just created, start attacking").
    void InitializeAI() override
    {
        ScriptedAI::InitializeAI();
        DoZoneInCombat(nullptr, 150.0f);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _chase.Stop(me);
        if (_carrying)
            if (boss_solakar_flamewreath_rework* sol = SolakarOf(me))
                sol->HatcherDropped(me, "hatcher-killed");
        _carrying = false;
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == kPointClutch && _carrying)
            _atClutch = true;
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (_carrying)
        {
            UpdateCarry();
            return;
        }

        _pollMs += diff;
        if (_pollMs >= kPollMs)
        {
            _pollMs = 0;
            PollHolder();
        }
        if (!_arrived.IsEmpty())
        {
            ObjectGuid const victim = _arrived;
            _arrived.Clear();
            Snatch(ObjectAccessor::GetPlayer(*me, victim));
            if (_carrying)
                return;
        }
        if (_chase.Active())
        {
            _chase.Update(me, diff);
            return;     // a runner: no swing while it chases
        }

        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_strikeMs <= diff)
        {
            DoCastVictim(SPELL_STRIKE);
            _strikeMs = urand(kStrikeMinMs, kStrikeMaxMs);
        }
        else
            _strikeMs -= diff;
        if (_sunderMs <= diff)
        {
            DoCastVictim(SPELL_SUNDER_ARMOR);
            _sunderMs = urand(kSunderMinMs, kSunderMaxMs);
        }
        else
            _sunderMs -= diff;
        DoMeleeAttackIfReady();
    }

private:
    // The holder now; a new one (a toss) stops it a second, then it turns to them.
    void PollHolder()
    {
        boss_solakar_flamewreath_rework* sol = SolakarOf(me);
        ObjectGuid const holder = sol ? sol->HolderGuid() : ObjectGuid::Empty;
        if (holder != _target)
        {
            if (_chase.Active())
                _chase.Stop(me);
            if (!_target.IsEmpty() && !holder.IsEmpty())
                _resumeMs = _clockMs + kTossPauseMs;
            _target = holder;
        }
        if (_target.IsEmpty() || _chase.Active() || _clockMs < _resumeMs)
            return;
        Player* target = ObjectAccessor::GetPlayer(*me, _target);
        if (!target || !target->IsAlive())
            return;
        DungeonKit::ChaserSpec spec;
        spec.speed = 0.f;               // its stock run speed: 1.43, about 10 yd/s
        spec.honorSlows = true;
        spec.reach = kSnatchReachYd;
        spec.pauseOnControl = Ms(kTossPauseMs);
        spec.endOnArrive = true;
        spec.tauntImmune = true;
        spec.fixate = true;
        spec.pick.nonTank = false;
        Map* map = me->GetMap();
        ObjectGuid const self = me->GetGUID();
        spec.onArrive = [map, self](Creature*, Unit* victim)
        {
            Creature* hatcher = map ? map->GetCreature(self) : nullptr;
            if (!hatcher || !hatcher->IsAlive() || !victim)
                return;
            if (auto* ai = dynamic_cast<npc_brs_rookery_hatcher*>(hatcher->AI()))
                ai->_arrived = victim->GetGUID();
        };
        // The kit picked someone else (its target died): not the flame's; the next poll re-aims.
        spec.onTarget = [map, self](Creature* chaser, Unit*)
        {
            Creature* hatcher = map ? map->GetCreature(self) : nullptr;
            if (!hatcher)
                return;
            if (auto* ai = dynamic_cast<npc_brs_rookery_hatcher*>(hatcher->AI()))
            {
                ai->_chase.Stop(chaser);
                ai->_target.Clear();
            }
        };
        if (_chase.Start(me, target, std::move(spec), me))
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hatcher-chase", target->GetName());
    }

    void Snatch(Player* victim)
    {
        boss_solakar_flamewreath_rework* sol = SolakarOf(me);
        if (!sol || !victim)
            return;
        std::optional<Position> const clutch = sol->HatcherSnatch(me, victim);
        _target.Clear();
        if (!clutch)
            return;     // no clutch of 3: it dropped the flame on the spot
        _carrying = true;
        _atClutch = false;
        _clutch = *clutch;
        _repathMs = 0;
        me->AddAura(SPELL_SK_STOLEN_FLAME, me);
        Talk(TEXT_HATCHER_SNATCH);
        me->SetCombatMovement(false);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(kPointClutch, _clutch);
    }

    // Running with the flame: stunned on the way it drops it; at the clutch the eggs hatch and it drops it there.
    void UpdateCarry()
    {
        boss_solakar_flamewreath_rework* sol = SolakarOf(me);
        if (!sol)
        {
            EndCarry(true);
            return;
        }
        if (Stunned(me))
        {
            sol->HatcherDropped(me, "hatcher-stunned");
            EndCarry(true);
            return;
        }
        if (_atClutch || me->GetExactDist2d(_clutch.GetPositionX(), _clutch.GetPositionY()) <= kClutchArriveYd)
        {
            me->CastSpell(me, SPELL_SK_HATCHER_HATCH, true);
            sol->HatcherAtClutch(me);
            EndCarry(true);
            return;
        }
        if (_clockMs >= _repathMs)
        {
            _repathMs = _clockMs + 1000;
            if (me->GetMotionMaster()->GetCurrentMovementGeneratorType() != POINT_MOTION_TYPE)
                me->GetMotionMaster()->MovePoint(kPointClutch, _clutch);
        }
    }

    void EndCarry(bool resume)
    {
        if (!_carrying)
            return;
        _carrying = false;
        _atClutch = false;
        me->RemoveAurasDueToSpell(SPELL_SK_STOLEN_FLAME);
        me->SetCombatMovement(true);
        if (resume)
            if (Unit* victim = me->GetVictim())
            {
                me->GetMotionMaster()->Clear();
                AttackStart(victim);
            }
    }

    DungeonKit::Chaser _chase;
    ObjectGuid _target;
    ObjectGuid _arrived;
    Position _clutch;
    uint64 _clockMs = 0;
    uint64 _resumeMs = 0;
    uint64 _repathMs = 0;
    uint32 _pollMs = 0;
    uint32 _strikeMs = 0;
    uint32 _sunderMs = 0;
    bool _carrying = false;
    bool _atClutch = false;
};

// Rookery Guardian 10258 (SK3): Strike and Sunder Armor (its SmartAI timers) and Ground Stomp.
struct npc_brs_rookery_guardian : public ScriptedAI
{
    explicit npc_brs_rookery_guardian(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _strikeMs = urand(kStrikeFirstMinMs, kStrikeFirstMaxMs);
        _sunderMs = urand(kSunderFirstMinMs, kSunderFirstMaxMs);
        _stompMs = kGroundStompFirstMs;
    }

    // The instance summons it with no summoner (no IsSummonedBy): it joins the fight as it enters the world (the stock
    // SmartAI's "on just created, start attacking").
    void InitializeAI() override
    {
        ScriptedAI::InitializeAI();
        DoZoneInCombat(nullptr, 150.0f);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        _stompMs = _stompMs > diff ? _stompMs - diff : 0;
        _strikeMs = _strikeMs > diff ? _strikeMs - diff : 0;
        _sunderMs = _sunderMs > diff ? _sunderMs - diff : 0;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_stompMs == 0)
        {
            GroundStomp();
            _stompMs = kGroundStompEveryMs;
            return;
        }
        if (_strikeMs == 0)
        {
            DoCastVictim(SPELL_STRIKE);
            _strikeMs = urand(kStrikeMinMs, kStrikeMaxMs);
        }
        if (_sunderMs == 0)
        {
            DoCastVictim(SPELL_SUNDER_ARMOR);
            _sunderMs = urand(kSunderMinMs, kSunderMaxMs);
        }
        DoMeleeAttackIfReady();
    }

private:
    // A 2 s bar and an 8 yd circle on it: 20%, Weakened, no stun (his War Stomp, previewed). The tank too.
    void GroundStomp()
    {
        DungeonKit::CastBar(me, SPELL_SK_GROUND_STOMP_BAR);
        Map* map = me->GetMap();
        ObjectGuid const self = me->GetGUID();
        MechanicRef ref = Mechanic::Circle(me, me, kStompRadiusYd, Ms(kStompCastMs));
        ref.Damage(kGroundStompPct).Weakened().Spell(SPELL_SK_GROUND_STOMP).Tag(TAG_GROUND_STOMP);
        ref.OnResolve([map, self](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled)
                return;
            if (Creature* guardian = map ? map->GetCreature(self) : nullptr)
                if (guardian->IsAlive())
                    guardian->CastSpell(guardian, SPELL_SK_STOMP_LOOK, true);
        });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "ground-stomp", At(me->GetPosition()));
    }

    uint32 _strikeMs = 0;
    uint32 _sunderMs = 0;
    uint32 _stompMs = 0;
};

// Flame whelp 300731 (SK6): hatched by the flame; on heroic it chases the holder (SP: "the whelps want the flame").
struct npc_brs_flame_whelp : public ScriptedAI
{
    explicit npc_brs_flame_whelp(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _chase.Stop(me);
        _target.Clear();
    }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        me->CastSpell(me, SPELL_SK_HATCH_BURST, true);
        DoZoneInCombat(nullptr, 150.0f);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _chase.Stop(me);
    }

    void UpdateAI(uint32 diff) override
    {
        if (IsHeroicMap(me))
        {
            _pollMs += diff;
            if (_pollMs >= kPollMs)
            {
                _pollMs = 0;
                PollHolder();
            }
            if (_chase.Active())
                _chase.Update(me, diff);
        }
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

private:
    void PollHolder()
    {
        boss_solakar_flamewreath_rework* sol = SolakarOf(me);
        ObjectGuid const holder = sol ? sol->HolderGuid() : ObjectGuid::Empty;
        if (holder == _target && (_chase.Active() || holder.IsEmpty()))
            return;
        _chase.Stop(me);
        _target = holder;
        Player* target = holder.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, holder);
        if (!target || !target->IsAlive())
            return;
        DungeonKit::ChaserSpec spec;
        spec.speed = 0.f;
        spec.honorSlows = true;
        spec.reach = 2.f;
        spec.endOnArrive = false;       // it stays on them and bites
        spec.tauntImmune = false;       // a tank may still take a whelp off the holder
        spec.fixate = true;
        spec.pick.nonTank = false;
        _chase.Start(me, target, std::move(spec), me);
    }

    DungeonKit::Chaser _chase;
    ObjectGuid _target;
    uint32 _pollMs = 0;
};

// Father Flame 175245 (SK1): taking it gives the flame (aura and item, no loot roll) and starts the event.
struct go_brs_father_flame : public GameObjectAI
{
    explicit go_brs_father_flame(GameObject* go) : GameObjectAI(go) { }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        TakeFatherFlame(me, player);
        return true;    // never the chest's loot window
    }

    // The flame to `player` and the event started. Empty: done; otherwise why not.
    static std::string TakeFatherFlame(GameObject* go, Player* player)
    {
        InstanceScript* instance = player->GetInstanceScript();
        if (!instance || player->GetMapId() != kMapBlackrockSpire)
            return "Not in Blackrock Spire.";
        if (instance->GetBossState(BOSS_SOLAKAR) == DONE || instance->GetData(DATA_SOLAKAR_EVENT) == DONE)
            return "Solakar is dead: Father Flame is spent.";
        if (instance->GetData(DATA_SOLAKAR_EVENT) != NOT_STARTED)
            return "The Rookery is already awake.";
        if (!player->IsAlive())
            return "Dead players cannot take the flame.";
        ItemPosCountVec dest;
        if (!player->HasItemCount(kItemFatherFlame, 1)
            && player->CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, kItemFatherFlame, 1) != EQUIP_ERR_OK)
        {
            player->SendEquipError(EQUIP_ERR_INVENTORY_FULL, nullptr, nullptr, kItemFatherFlame);
            return "Bags are full.";
        }
        // A copy left over from a crash leaves everyone else first: there is one flame.
        if (Map* map = player->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource(); p && p != player)
                    StripFlame(p, true);
        GiveFlame(player);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "take", player->GetName());
        instance->SetData(DATA_SOLAKAR_EVENT, IN_PROGRESS);
        if (go)
            go->DespawnOrUnsummon(0ms, Seconds(kEggHatchedRespawnSec));     // the reset brings it back
        return {};
    }
};

// SK5: item 70610's toss (210391): only to a living player who may catch and has room in their bags (CheckCast; R-2
// ruling: "bags full" to the thrower); on landing the AI moves it.
class spell_brs_solakar_flame_toss : public SpellScript
{
    PrepareSpellScript(spell_brs_solakar_flame_toss);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        Player* catcher = target ? target->ToPlayer() : nullptr;
        if (!catcher || catcher == caster || !catcher->IsAlive())
            return SPELL_FAILED_BAD_TARGETS;
        boss_solakar_flamewreath_rework* sol = SolakarOf(caster);
        if (!sol)
            return SPELL_FAILED_NOT_READY;
        if (!sol->CatchAllowed(catcher))
            return SPELL_FAILED_TARGET_AURASTATE;
        if (!FlameRoom(catcher))
        {
            if (Player* thrower = caster ? caster->ToPlayer() : nullptr)
                ChatHandler(thrower->GetSession()).SendNotification(
                    std::string_view(Acore::StringFormat("{}'s bags are full.", catcher->GetName())));
            return SPELL_FAILED_DONT_REPORT;
        }
        return SPELL_CAST_OK;
    }

    void HandleLanding(SpellEffIndex /*effIndex*/)
    {
        Player* thrower = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Player* catcher = GetHitUnit() ? GetHitUnit()->ToPlayer() : nullptr;
        if (boss_solakar_flamewreath_rework* sol = SolakarOf(GetCaster()))
            sol->TossLanded(thrower, catcher);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_brs_solakar_flame_toss::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_brs_solakar_flame_toss::HandleLanding, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// SK8 / SK11: a percent of the reference row passed as the cast's base points, in hundredths (the script raises it by
// Flamewreath before the cast): Wreathed in Flame's tick (210401) and the torn wound (210413).
class spell_brs_solakar_ref_pct : public SpellScript
{
    PrepareSpellScript(spell_brs_solakar_ref_pct);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        float const pct = static_cast<float>(GetEffectValue()) / 100.f;
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_brs_solakar_ref_pct::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// SK11: the spear (210411) lands: the wound.
class spell_brs_solakar_spear_throw : public SpellScript
{
    PrepareSpellScript(spell_brs_solakar_spear_throw);

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        if (boss_solakar_flamewreath_rework* sol = SolakarOf(GetCaster()))
            sol->SpearHit(GetHitUnit());
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_brs_solakar_spear_throw::HandleHit, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// SK11: Spear Wound (210412) bleeds 1% a second (raised by Flamewreath at the throw); run out (not seared) it tears.
class spell_brs_solakar_spear_wound : public AuraScript
{
    PrepareAuraScript(spell_brs_solakar_spear_wound);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;
        Unit* caster = GetCaster();
        Unit* owner = GetUnitOwner();
        if (!caster || !owner)
            return;
        uint32 const stacks = DungeonKit::Stacks(caster, SPELL_SK_FLAMEWREATH)
            + DungeonKit::Stacks(caster, SPELL_SK_FLAMEWREATH_H);
        float const pct = kSpearBleedPct * WreathMult(IsHeroicMap(caster), stacks);
        amount = static_cast<int32>(DungeonKit::RefFlatOn(caster, owner, pct));
    }

    void OnRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        AuraApplication const* application = GetTargetApplication();
        if (!application || application->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;
        if (boss_solakar_flamewreath_rework* sol = SolakarOf(GetTarget()))
            sol->WoundTore(GetTarget());
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_brs_solakar_spear_wound::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
        AfterEffectRemove += AuraEffectRemoveFn(spell_brs_solakar_spear_wound::OnRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
    }
};

namespace
{
    boss_solakar_flamewreath_rework* FindSolakarAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_SOLAKAR);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_solakar_flamewreath_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}",
                "Solakar is not running boss_solakar_flamewreath_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_solakar_flamewreath_rework::TestMechanic mechanic, char const* what)
    {
        boss_solakar_flamewreath_rework* ai = FindSolakarAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(mechanic, handler->GetPlayer());
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Solakar: {} fired ({}).", what,
            ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_SOLAKAR, BOSS_SOLAKAR);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_solakar_flamewreath_rework* ai = FindSolakarAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Solakar: {}", ai->TestState());
        return true;
    }

    // `.dbtest brs solakar start`: Father Flame to the GM (as if taken from the brazier) and the event started.
    bool HandleStart(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        Player* gm = handler->GetPlayer();
        std::string const error = go_brs_father_flame::TakeFatherFlame(nullptr, gm);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Solakar: the event started, you hold Father Flame; he arrives in {} s "
            "(`.dbtest brs solakar arrive` for now).", kSolakarArriveMs / 1000);
        return true;
    }

    bool HandleArrive(ChatHandler* handler)
    {
        return Fire(handler, boss_solakar_flamewreath_rework::TestMechanic::Arrive, "the arrival (SK1)");
    }

    bool HandleHunt(ChatHandler* handler)
    {
        return Fire(handler, boss_solakar_flamewreath_rework::TestMechanic::Hunt, "the Warden's Hunt (SK9)");
    }

    bool HandleStomp(ChatHandler* handler)
    {
        return Fire(handler, boss_solakar_flamewreath_rework::TestMechanic::Stomp, "War Stomp (SK10)");
    }

    bool HandleSpear(ChatHandler* handler)
    {
        return Fire(handler, boss_solakar_flamewreath_rework::TestMechanic::Spear, "Spear Wound (SK11)");
    }

    bool HandleReclaim(ChatHandler* handler)
    {
        return Fire(handler, boss_solakar_flamewreath_rework::TestMechanic::Reclaim, "a Reclaim (SK8)");
    }

    bool HandleDrop(ChatHandler* handler)
    {
        return Fire(handler, boss_solakar_flamewreath_rework::TestMechanic::Drop, "the flame dropped (SK7)");
    }

    bool HandleHatch(ChatHandler* handler)
    {
        return Fire(handler, boss_solakar_flamewreath_rework::TestMechanic::Hatch, "a hatch within 6 yd of you (SK6)");
    }

    bool HandleReset(ChatHandler* handler)
    {
        return Fire(handler, boss_solakar_flamewreath_rework::TestMechanic::Reset, "the reset (SK12)");
    }

    // `.dbtest brs solakar <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& SolakarTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "start",   HandleStart,   SEC_GAMEMASTER, Console::No },
            { "arrive",  HandleArrive,  SEC_GAMEMASTER, Console::No },
            { "hunt",    HandleHunt,    SEC_GAMEMASTER, Console::No },
            { "stomp",   HandleStomp,   SEC_GAMEMASTER, Console::No },
            { "spear",   HandleSpear,   SEC_GAMEMASTER, Console::No },
            { "reclaim", HandleReclaim, SEC_GAMEMASTER, Console::No },
            { "drop",    HandleDrop,    SEC_GAMEMASTER, Console::No },
            { "hatch",   HandleHatch,   SEC_GAMEMASTER, Console::No },
            { "reset",   HandleReset,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_solakar_flamewreath_rework()
{
    // The AIs bind only once wave 2 does (an unbound registered name logs "not assigned" at boot); the spells are
    // declared now, so their scripts register now.
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_solakar_flamewreath_rework, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_rookery_hatcher, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_rookery_guardian, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_flame_whelp, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkGameObjectAI(go_brs_father_flame, BlackrockSpireRework::kInstanceScriptName);
    RegisterSpellScript(spell_brs_solakar_flame_toss);
    RegisterSpellScript(spell_brs_solakar_ref_pct);
    RegisterSpellScript(spell_brs_solakar_spear_throw);
    RegisterSpellScript(spell_brs_solakar_spear_wound);
    BrsTest::RegisterBoss("solakar", SolakarTestCommands());
}
