/*
 * mod-dungeon-bosses, Zul'Farrak D7Hb: the Deluge, phase 3 of the hard mode "The Crew at the Pool" (heroic only, armed
 * by Bly's Test with all five crew at the pool). Build spec: docs/dungeons/zul-farrak-rework.md "Hard mode: the crew
 * at the pool", Phase 3 and rows GZ22-GZ24 (rulings 42, 43); handoff sections 3.5 row D7Hb, 3.7, 3.8 (the pool), 3.9
 * rows 9 and 10, 7 #36-#38, #43, #58, 10. Pure rules and every number: GahzrillaDelugeLogic.h. A package of D7's pool
 * encounter (PoolFight.h): it plugs into D7's hooks only and never touches the crew (D7Ha's).
 *
 *   The package        ZfPool::RegisterPoolHardMode(PoolPackage::Deluge): D7 makes one DelugeHardMode at Velratha's
 *                      pull of the hard mode (after D7Ha's) and drops it at the gong if the flag did not arm
 *   GZ22 The Deluge    the first hit that leaves Gahz'rilla at or under 40% (OnGahzrillaDamaged; started on the next
 *                      pool tick): emote line 1 and a roar, the phase (PoolPhase::Deluge), Icicle every 5 s, and he
 *                      walks to the pool's edge nearest the fight and fights from there (PinGahzrilla: melee in reach,
 *                      else D7's Acid Spit). Over 5 s V's water disc rises from the pool's middle (scale 1 to 8 in
 *                      0.5 s steps, a water sheet: Charged reaches whoever it covers); then a cover strip makes the
 *                      whole shore water for the rest of the fight (D7's Charged ticks on everyone off the ice, D7's
 *                      Discharge stuns them and makes them Conductive). D7's puddles are swallowed by the flood
 *   GZ23 Floes         from the Deluge on, every Icicle and Freeze Solid freezes a floe where it lands (OnFreeze,
 *                      handled: no Meltwater): 8 yd and 12 yd, ice that thaws away after 30 s; a swimmer's forms at the
 *                      nearest shore point (the pool never freezes). Ice wins over the flood (KT), so floes and the
 *                      group's frozen puddles are the only dry ground. A Call the Waters that lands (his, or D7Ha's
 *                      second head) floods the floe under each of its puddles. The bots: every ice circle is a Strict
 *                      SpotBounds circle (a Spot with no spots, owned by Gahz'rilla, tag 37), renewed on every change
 *   GZ24 Storm Strikes from the end of the rise, three a second: a 3 yd Circle AoE 0 to 10 yd from a random player in a
 *                      random direction, 1.5 s warning, 30% Nature and Weakened (registry, tag 38); the bolt is SV
 *                      90702 cast at the point by the strike stalker (301033)
 *   Not D7Hb's         the crew, Wellsprings (D7Ha stops them in this phase), Storm's Chosen, Overcharge, Twin Call,
 *                      Conductive on everyone; health 500,000 and the loot bit (D7, the instance)
 *
 * Cleanup (RB-1): OnEnd cancels the bounds and every live strike and puts Icicle back on D7's pace; D7's cleanup right
 * after takes the water (the look, the cover, the floes), the strike stalker (PoolFight::Summon) and the pin. Every
 * firing logs one INFO line "zf-build deluge <mechanic> ..." (strikes: the first and every 30th); `.dbtest zf deluge
 * <mechanic>` fires one.
 */

#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitWater.h"
#include "GahzrillaDelugeLogic.h"
#include "GahzrillaLogic.h"
#include "Map.h"
#include "PassiveAI.h"
#include "Player.h"
#include "PoolFight.h"
#include "Random.h"
#include "SharedDefines.h"
#include "StringFormat.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include <cmath>
#include <deque>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfDeluge;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::SheetState;
using ZfPool::FreezeKind;
using ZfPool::PoolFight;
using ZfPool::PoolPhase;

class DelugeHardMode;

namespace
{
    char const* const kLogKey = "deluge";
    float constexpr kFloorBandYd = 8.f;

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(static_cast<int64>(ms));
    }

    void LogDeluge(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kLogKey, mechanic, detail);
    }

    // The floor under (x, y) near `zHint`; the hint where the map has none close to it.
    float FloorZ(WorldObject const* ref, Vec2 p, float zHint)
    {
        if (!ref)
            return zHint;
        float const floor = ref->GetMapHeight(p.x, p.y, zHint + 5.f);
        return (floor > INVALID_HEIGHT + 1.f && std::fabs(floor - zHint) <= kFloorBandYd) ? floor : zHint;
    }

    Position PoolMiddleOnSurface()
    {
        return Position(kDelugeMiddle.x, kDelugeMiddle.y, ZfPool::kPoolSurfaceZ, 0.f);
    }

    // The live packages by map, for `.dbtest zf deluge` (maps update on several threads).
    std::mutex& LiveLock()
    {
        static std::mutex lock;
        return lock;
    }

    std::unordered_map<Map const*, DelugeHardMode*>& Live()
    {
        static std::unordered_map<Map const*, DelugeHardMode*> live;
        return live;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The package (PoolFight.h PoolHardMode), one per pull of the hard mode
// ---------------------------------------------------------------------------------------------------------------------

class DelugeHardMode final : public ZfPool::PoolHardMode
{
public:
    enum class Stage : uint8
    {
        Waiting,    // phases 1 and 2: nothing of the Deluge's yet
        Rising,     // GZ22: the 5 s rise (floes already form; no Storm Strikes)
        Flooded,    // the whole shore is water: floes, the flood, Storm Strikes
        Ended,
    };

    explicit DelugeHardMode(PoolFight& fight) : _arena(PoolArena()), _floorBounds(PoolFloorBounds())
    {
        if (Creature* keeper = fight.Keeper())
            _map = keeper->GetMap();
        std::lock_guard<std::mutex> guard(LiveLock());
        Live()[_map] = this;
    }

    ~DelugeHardMode() override
    {
        Unlist();
    }

    // ---- PoolHardMode ---------------------------------------------------------------------------------------------

    void OnEngage(PoolFight& fight) override
    {
        LogDeluge("armed", Acore::StringFormat("heroic={} at={}%", fight.Heroic() ? 1 : 0, Tune::kDelugeHealthPct));
    }

    void OnGongStruck(PoolFight& /*fight*/, bool armed) override
    {
        if (!armed)
            LogDeluge("dropped", "the flag did not arm at the gong");
    }

    // GZ22: the first hit that leaves him at or under 40% (started on the next pool tick, never inside his damage).
    void OnGahzrillaDamaged(PoolFight& fight, Unit* /*attacker*/, uint32& damage) override
    {
        if (_stage != Stage::Waiting || _pending || fight.Phase() != PoolPhase::Gahzrilla)
            return;
        Creature* gahzrilla = fight.Gahzrilla();
        if (!gahzrilla || !gahzrilla->GetMaxHealth())
            return;
        uint32 const health = gahzrilla->GetHealth();
        uint32 const after = health > damage ? health - damage : 0;
        float const pct = static_cast<float>(after) * 100.f / static_cast<float>(gahzrilla->GetMaxHealth());
        if (DelugeDue(pct, false))
            _pending = true;
    }

    void OnUpdate(PoolFight& fight, uint32 diff) override
    {
        if (_stage == Stage::Ended)
            return;
        if (_pending && _stage == Stage::Waiting)
        {
            _pending = false;
            Begin(fight, "health");
        }
        if (_stage == Stage::Rising)
            Rise(fight, diff);
        if (_stage == Stage::Flooded)
        {
            Flood(fight);
            for (uint32 n = _strikeClock.Advance(diff); n > 0; --n)
                Strike(fight, nullptr);
        }
        if (_stage != Stage::Waiting)
            Bounds(fight, diff);
        PruneStrikes(fight);
    }

    // GZ23: in the Deluge every freeze is a floe where it lands (handled: no Meltwater, no shore spill).
    bool OnFreeze(PoolFight& fight, FreezeKind kind, Unit* /*target*/, Position const& at,
        DungeonKit::FreezeResult& /*result*/) override
    {
        if (_stage != Stage::Rising && _stage != Stage::Flooded)
            return false;
        bool const icicle = kind == FreezeKind::Icicle;
        AddFloe(fight, at, FloeRadius(icicle), icicle ? "floe-icicle" : "floe-freeze-solid");
        return true;
    }

    void OnEnd(PoolFight& fight, bool won) override
    {
        if (_stage == Stage::Ended)
            return;
        Unit* any = fight.Keeper();
        if (Creature* gahzrilla = fight.Gahzrilla())
            any = gahzrilla;
        if (any)
        {
            if (_bounds)
                Mechanic::Cancel(any, _bounds);
            for (LiveStrike const& s : _liveStrikes)
                Mechanic::Cancel(any, s.handle);
        }
        _bounds = MechanicHandle();
        _boundsIds.clear();
        _liveStrikes.clear();
        if (Creature* gahzrilla = fight.Gahzrilla(); gahzrilla && gahzrilla->IsAlive() && _stage != Stage::Waiting)
            fight.SetIcicleEvery(0);
        _strikeClock.Stop();
        LogDeluge("end", Acore::StringFormat("won={} stage={} floes={} flooded={} strikes={} swallowed={}",
            won ? 1 : 0, StageName(), _floes, _floodedFloes, _strikes, _swallowed));
        _stage = Stage::Ended;
        Unlist();
    }

    // ---- `.dbtest zf deluge` --------------------------------------------------------------------------------------

    // GZ22 now (a GM); empty on success, else why not.
    std::string Begin(PoolFight& fight, char const* why)
    {
        if (_stage != Stage::Waiting)
            return "The Deluge has started already.";
        Creature* gahzrilla = fight.Gahzrilla();
        if (!gahzrilla || !gahzrilla->IsAlive() || fight.Phase() != PoolPhase::Gahzrilla)
            return "Gahz'rilla must be ashore and fighting.";
        Creature* keeper = fight.Keeper();
        if (!keeper)
            return "The pool's stalker is gone.";
        _stage = Stage::Rising;
        _pending = false;
        _riseMs = 0;
        _riseStep = 0;
        fight.SetPhase(PoolPhase::Deluge);
        fight.SetIcicleEvery(Tune::kIcicleEveryMs);
        if (gahzrilla->IsAIEnabled)
            gahzrilla->AI()->Talk(EMOTE_GAHZRILLA_DELUGE);
        gahzrilla->HandleEmoteCommand(EMOTE_ONESHOT_ROAR);
        // Section 7 #38 A: he fights from the pool's edge, the spot nearest where the group held him.
        Vec2 const pin = PinSpotFor(DungeonKit::PlaneOf(gahzrilla));
        float const facing = std::atan2(kDelugeMiddle.y - pin.y, kDelugeMiddle.x - pin.x) + float(M_PI);
        Position const pinAt(pin.x, pin.y, FloorZ(gahzrilla, pin, Tune::kShoreZ), facing);
        fight.PinGahzrilla(pinAt);
        _look = fight.AddSheet(PoolMiddleOnSurface(), DelugeRadiusAt(0), DelugeRules(SHEET_DELUGE, kDelugeZBandYd),
            SheetState::Water, "deluge-rise");
        fight.RefreshDescriptors();
        DungeonKit::WaterSheets const& sheets = fight.Water().Sheets();
        LogDeluge("start", Acore::StringFormat("why={} health={:.1f} discharges={} clock={}s pin=({:.1f}, {:.1f}, "
            "{:.1f}) look={} water={} ice={}", why, gahzrilla->GetHealthPct(), fight.DischargesLanded(),
            fight.GahzrillaClockMs() / 1000, pinAt.GetPositionX(), pinAt.GetPositionY(), pinAt.GetPositionZ(), _look,
            sheets.CountIn(SheetState::Water), sheets.CountIn(SheetState::Ice)));
        return {};
    }

    // One Storm Strike near `near` (nullptr: a random player). False: nobody to strike or no Gahz'rilla.
    bool Strike(PoolFight& fight, Player* near)
    {
        Creature* gahzrilla = fight.Gahzrilla();
        if (!gahzrilla || !gahzrilla->IsAlive() || !gahzrilla->IsInWorld())
            return false;
        Player* target = near;
        if (!target)
        {
            std::vector<Player*> const players = fight.FightPlayers();
            if (players.empty())
                return false;
            target = Acore::Containers::SelectRandomContainerElement(players);
        }
        Vec2 const base = DungeonKit::PlaneOf(target);
        float const baseZ = target->GetPositionZ();
        Position at = target->GetPosition();
        for (uint32 i = 0; i < Tune::kStrikeTries; ++i)
        {
            Vec2 const p = StrikePoint(base, frand(0.f, 1.f), frand(0.f, 1.f));
            float const z = FloorZ(target, p, baseZ);
            if (_arena.Contains(p, z))
            {
                at = Position(p.x, p.y, z, 0.f);
                break;
            }
        }
        Map* map = gahzrilla->GetMap();
        ObjectGuid const stalker = _stalker;
        Position const look = at;
        MechanicRef ref = Mechanic::Circle(gahzrilla, at, Tune::kStrikeRadiusYd, Ms(Tune::kStrikeWarnMs));
        ref.Damage(Tune::kStrikePct).TankDamage(Tune::kStrikePct).School(SPELL_SCHOOL_NATURE)
            .Spell(SPELL_DELUGE_STORM_STRIKE).Weakened().ZTolerance(Tune::kStrikeZBandYd).Within(_floorBounds)
            .Tag(TAG_DELUGE_STRIKE)
            .OnResolve([map, stalker, look](BossMechanics::ResolveResult const& /*r*/)
            {
                if (Creature* caster = map->GetCreature(stalker))
                    caster->CastSpell(look.GetPositionX(), look.GetPositionY(), look.GetPositionZ(),
                        SPELL_DELUGE_STORM_STRIKE_LOOK, true);
            });
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return false;
        _liveStrikes.push_back({ handle, fight.ClockMs() + Tune::kStrikeWarnMs + 1000 });
        ++_strikes;
        if (_strikes == 1 || _strikes % Tune::kStrikeLogEvery == 0)
            LogDeluge("strike", Acore::StringFormat("n={} near={} tank={} at=({:.1f}, {:.1f}, {:.1f}) live={}",
                _strikes, target->GetName(), target == gahzrilla->GetVictim() ? 1 : 0, at.GetPositionX(),
                at.GetPositionY(), at.GetPositionZ(), _liveStrikes.size()));
        return true;
    }

    // A floe of `radius` at `at` (a swimmer's at the nearest shore point). Returns its sheet id (0: refused).
    uint32 AddFloe(PoolFight& fight, Position const& at, float radius, char const* why)
    {
        Creature* keeper = fight.Keeper();
        if (!keeper)
            return 0;
        Vec2 const xy{ at.GetPositionX(), at.GetPositionY() };
        bool const swimming = PoolWater().Contains(xy, at.GetPositionZ());
        Vec2 const spot = FloeSpot(xy, swimming);
        float const z = swimming ? FloorZ(keeper, spot, Tune::kShoreZ) : at.GetPositionZ();
        uint32 const id = fight.AddSheet(Position(spot.x, spot.y, z, 0.f), radius, FloeRules(), SheetState::Ice, why);
        if (!id)
            return 0;
        ++_floes;
        if (Creature* disc = keeper->GetMap()->GetCreature(fight.Water().DiscOf(id)))
            disc->CastSpell(disc, ZfPool::SPELL_GZ_FREEZE_LOOK, true);
        LogDeluge("floe", Acore::StringFormat("why={} id={} radius={:.0f} at=({:.1f}, {:.1f}, {:.1f}) swimmer={} "
            "ice={}", why, id, radius, spot.x, spot.y, z, swimming ? 1 : 0,
            fight.Water().Sheets().CountIn(SheetState::Ice)));
        return id;
    }

    // Every floe away now (`.dbtest`). Returns how many.
    uint32 ThawFloes(PoolFight& fight)
    {
        Creature* keeper = fight.Keeper();
        if (!keeper)
            return 0;
        std::vector<uint32> ids;
        for (DungeonKit::WaterSheet const& s : fight.Water().All())
            if (!s.IsWater() && s.rules.kind == SHEET_FLOE)
                ids.push_back(s.id);
        for (uint32 const id : ids)
            fight.Water().Thaw(keeper, id);
        return static_cast<uint32>(ids.size());
    }

    std::string State(PoolFight& fight) const
    {
        DungeonKit::WaterSheets const& sheets = fight.Water().Sheets();
        return Acore::StringFormat("stage={} pending={} rise={}ms look={} cover={} floes-made={} ice-now={} "
            "water-now={} bounds={} ({} circles) strikes={} live={} flooded={} swallowed={}", StageName(),
            _pending ? 1 : 0, _riseMs, _look, _cover, _floes, sheets.CountIn(SheetState::Ice),
            sheets.CountIn(SheetState::Water), _bounds ? 1 : 0, _boundsIds.size(), _strikes, _liveStrikes.size(),
            _floodedFloes, _swallowed);
    }

    static DelugeHardMode* Find(Map const* map)
    {
        std::lock_guard<std::mutex> guard(LiveLock());
        auto it = Live().find(map);
        return it == Live().end() ? nullptr : it->second;
    }

private:
    struct LiveStrike
    {
        MechanicHandle handle;
        uint64 until = 0;       // the fight's clock after its resolve
    };

    char const* StageName() const
    {
        switch (_stage)
        {
            case Stage::Waiting:
                return "waiting";
            case Stage::Rising:
                return "rising";
            case Stage::Flooded:
                return "flooded";
            case Stage::Ended:
                return "ended";
        }
        return "?";
    }

    void Unlist()
    {
        std::lock_guard<std::mutex> guard(LiveLock());
        auto it = Live().find(_map);
        if (it != Live().end() && it->second == this)
            Live().erase(it);
    }

    // GZ22: the disc's steps, then the whole shore.
    void Rise(PoolFight& fight, uint32 diff)
    {
        Creature* keeper = fight.Keeper();
        if (!keeper)
            return;
        _riseMs += diff;
        uint32 const step = RiseStep(_riseMs);
        if (step != _riseStep)
        {
            _riseStep = step;
            fight.Water().SetRadius(keeper, _look, DelugeRadiusAtStep(step));
        }
        if (!RiseDone(_riseMs))
            return;
        _cover = fight.Water().AddStrip(keeper, Position(kCoverFrom.x, kCoverFrom.y, kCoverZ),
            Position(kCoverTo.x, kCoverTo.y, kCoverZ), kCoverHalfWidthYd,
            DelugeRules(SHEET_DELUGE_COVER, kCoverZBandYd));
        _floodFromId = MaxSheetId(fight.Water().Sheets()) + 1;
        if (Creature* stalker = fight.Summon(NPC_ZF_STRIKE_STALKER, PoolMiddleOnSurface()))
            _stalker = stalker->GetGUID();
        _stage = Stage::Flooded;
        _strikeClock.Start();
        uint32 const before = _swallowed;
        Flood(fight);
        LogDeluge("flooded", Acore::StringFormat("cover={} look-radius={:.1f} swallowed={} ice={} stalker={}", _cover,
            DelugeRadiusAtStep(kRiseSteps), _swallowed - before, fight.Water().Sheets().CountIn(SheetState::Ice),
            _stalker.IsEmpty() ? 0 : 1));
    }

    // The flood swallows D7's water puddles; a Call puddle landed since floods the ice under it.
    void Flood(PoolFight& fight)
    {
        Creature* keeper = fight.Keeper();
        if (!keeper)
            return;
        FloodPlan const plan = PlanFlood(fight.Water().Sheets(), _floodFromId);
        if (plan.swallowed.empty() && plan.flooded.empty())
            return;
        for (uint32 const id : plan.flooded)
            fight.Water().Remove(keeper, id);
        for (uint32 const id : plan.swallowed)
            fight.Water().Remove(keeper, id);
        _swallowed += static_cast<uint32>(plan.swallowed.size());
        _floodedFloes += static_cast<uint32>(plan.flooded.size());
        if (!plan.flooded.empty())
            LogDeluge("floe-flooded", Acore::StringFormat("by-call={} floes={} ice-left={}", plan.swallowed.size(),
                plan.flooded.size(), fight.Water().Sheets().CountIn(SheetState::Ice)));
    }

    // The bots' floe bounds: every ice circle, Strict, registered again when the set changes (and before it runs out).
    void Bounds(PoolFight& fight, uint32 diff)
    {
        _boundsAge += diff;
        std::vector<uint32> const ids = IceIds(fight.Water().Sheets());
        bool const changed = ids != _boundsIds;
        if (!changed && (!_bounds || _boundsAge < Tune::kFloeBoundsRefreshMs))
            return;
        Creature* gahzrilla = fight.Gahzrilla();
        if (!gahzrilla || !gahzrilla->IsAlive() || !gahzrilla->IsInWorld())
            return;
        if (_bounds)
            Mechanic::Cancel(gahzrilla, _bounds);
        _bounds = MechanicHandle();
        _boundsIds = ids;
        _boundsAge = 0;
        if (!ids.empty())
        {
            BossMechanics::SpotBounds bounds;
            for (FloeCircle const& c : FloeCircles(fight.Water().Sheets()))
                bounds.Circle(Position(c.center.x, c.center.y, c.z, 0.f), c.radius, c.z - c.zBand, c.z + c.zBand);
            bounds.Strict();
            MechanicRef ref = Mechanic::Spot(gahzrilla, {}, Ms(Tune::kFloeBoundsMs));
            ref.NoTelegraph().Within(bounds).Tag(TAG_DELUGE_FLOE);
            _bounds = ref.Handle();
        }
        if (changed)
            LogDeluge("bounds", Acore::StringFormat("circles={} registered={}", ids.size(), _bounds ? 1 : 0));
    }

    void PruneStrikes(PoolFight& fight)
    {
        uint64 const now = fight.ClockMs();
        while (!_liveStrikes.empty() && _liveStrikes.front().until <= now)
            _liveStrikes.pop_front();
    }

    Map const* _map = nullptr;
    Arena const _arena;
    BossMechanics::SpotBounds const _floorBounds;
    Stage _stage = Stage::Waiting;
    bool _pending = false;
    uint32 _riseMs = 0;
    uint32 _riseStep = 0;
    uint32 _look = 0;
    uint32 _cover = 0;
    uint32 _floodFromId = 0;
    ObjectGuid _stalker;
    StrikeClock _strikeClock;
    std::deque<LiveStrike> _liveStrikes;
    MechanicHandle _bounds;
    std::vector<uint32> _boundsIds;
    uint32 _boundsAge = 0;
    uint32 _floes = 0;
    uint32 _floodedFloes = 0;
    uint32 _swallowed = 0;
    uint32 _strikes = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// npc_zf_strike_stalker (301033): casts the Storm Strikes' bolts at their points (V: "cast by a stalker at the point")
// ---------------------------------------------------------------------------------------------------------------------

struct npc_zf_strike_stalker : public NullCreatureAI
{
    explicit npc_zf_strike_stalker(Creature* creature) : NullCreatureAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }
};

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest zf deluge <subcommand>`
// ---------------------------------------------------------------------------------------------------------------------

namespace
{
    struct GmDeluge
    {
        PoolFight* fight = nullptr;
        DelugeHardMode* deluge = nullptr;
    };

    GmDeluge FindDeluge(ChatHandler* handler)
    {
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!gm || !ZfTest::RequireZulFarrak(handler))
            return {};
        GmDeluge out;
        out.fight = ZfPool::FindPoolFight(gm->GetMap());
        if (!out.fight)
        {
            handler->SendErrorMessage("{}", "No pool encounter is running (pull Velratha first).");
            return {};
        }
        out.deluge = DelugeHardMode::Find(gm->GetMap());
        if (!out.deluge)
        {
            handler->SendErrorMessage("{}", "No Deluge on this pull: the hard mode was not armed (heroic, "
                "`.dbtest zf test hardmode 1` before Velratha's pull).");
            return {};
        }
        return out;
    }

    Player* Selected(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_GAHZRILLA, BOSS_CREW_AT_THE_POOL);
    }

    bool HandleState(ChatHandler* handler)
    {
        GmDeluge const d = FindDeluge(handler);
        if (!d.deluge)
            return false;
        handler->PSendSysMessage("The Deluge: {}", d.deluge->State(*d.fight));
        return true;
    }

    // GZ22 now, whatever his health.
    bool HandleStart(ChatHandler* handler)
    {
        GmDeluge const d = FindDeluge(handler);
        if (!d.deluge)
            return false;
        std::string const error = d.deluge->Begin(*d.fight, "gm");
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("{}", "The Deluge: started (GZ22: 5 s of rising water, then the whole shore).");
        return true;
    }

    // GZ24: one Storm Strike near the selected player (else yourself).
    bool HandleStrike(ChatHandler* handler)
    {
        GmDeluge const d = FindDeluge(handler);
        Player* who = Selected(handler);
        if (!d.deluge || !who)
            return false;
        if (!d.deluge->Strike(*d.fight, who))
        {
            handler->SendErrorMessage("{}", "No strike (Gahz'rilla must be alive; the registry refused it?).");
            return false;
        }
        handler->PSendSysMessage("The Deluge: a Storm Strike near {}.", who->GetName());
        return true;
    }

    // GZ23: a floe at the selected player's feet (8 yd, or the radius given: 12 is a Freeze Solid's).
    bool HandleFloe(ChatHandler* handler, Optional<uint32> radius)
    {
        GmDeluge const d = FindDeluge(handler);
        Player* who = Selected(handler);
        if (!d.deluge || !who)
            return false;
        float const r = radius ? float(*radius) : Tune::kIcicleFloeYd;
        uint32 const id = d.deluge->AddFloe(*d.fight, who->GetPosition(), r, "gm");
        if (!id)
        {
            handler->SendErrorMessage("{}", "The water field refused it.");
            return false;
        }
        handler->PSendSysMessage("The Deluge: floe {} ({:.0f} yd) at {}'s feet.", id, r, who->GetName());
        return true;
    }

    bool HandleThaw(ChatHandler* handler)
    {
        GmDeluge const d = FindDeluge(handler);
        if (!d.deluge)
            return false;
        handler->PSendSysMessage("The Deluge: {} floes thawed away.", d.deluge->ThawFloes(*d.fight));
        return true;
    }

    ChatCommandTable const& DelugeTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "start",  HandleStart,  SEC_GAMEMASTER, Console::No },
            { "strike", HandleStrike, SEC_GAMEMASTER, Console::No },
            { "floe",   HandleFloe,   SEC_GAMEMASTER, Console::No },
            { "thaw",   HandleThaw,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_gahzrilla_deluge()
{
    ZfPool::RegisterPoolHardMode(ZfPool::PoolPackage::Deluge, [](PoolFight& fight)
    {
        return std::make_unique<DelugeHardMode>(fight);
    });
    RegisterDungeonReworkCreatureAI(npc_zf_strike_stalker, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("deluge", DelugeTestCommands());
}
