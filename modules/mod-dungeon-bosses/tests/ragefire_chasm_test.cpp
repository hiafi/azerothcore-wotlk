// Host tests for the Ragefire Chasm skeleton (WP-S0): RagefireChasmRework.h (boss states, data ids, slices, the save
// string, the gate and hard mode rules, the measured points, the polygons and the tuning tables). Points are the
// handoff's section 3.8 / NAVMESH-REPORT values; DB positions are exact.
#include "RagefireChasmRework.h"
#include "check.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <set>
#include <span>
#include <string>

using namespace RagefireChasmRework;

namespace
{
    std::uint32_t constexpr kNot = DungeonKit::State::NotStarted;
    std::uint32_t constexpr kRun = DungeonKit::State::InProgress;
    std::uint32_t constexpr kFail = DungeonKit::State::Fail;
    std::uint32_t constexpr kDone = DungeonKit::State::Done;

    bool Near(float a, float b, float tolerance)
    {
        return std::fabs(a - b) <= tolerance;
    }

    bool In(Arena const& arena, Point3 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    template <std::size_t N>
    float Area(std::array<Vec2, N> const& poly)
    {
        float twice = 0.f;
        for (std::size_t i = 0; i < N; ++i)
            twice += poly[i].x * poly[(i + 1) % N].y - poly[(i + 1) % N].x * poly[i].y;
        return std::fabs(twice) * 0.5f;
    }

    // Every vertex of `inner` lies in `outer`, at least `clear` yd from its edges where `counts(vertex)`.
    template <std::size_t N, class Counts>
    bool Inside(std::array<Vec2, N> const& inner, std::span<Vec2 const> outer, float clear, Counts&& counts)
    {
        for (Vec2 const p : inner)
        {
            if (!counts(p))
                continue;
            if (!DungeonKit::PointInPolygon(outer, p))
                return false;
            auto const edge = DungeonKit::NearestEdge(outer, p);
            if (!edge || edge->distance < clear)
                return false;
        }
        return true;
    }

    // A live run of the instance's SetBossState order (instance_ragefire_chasm_rework.cpp): the base stores a first
    // write onto TO_BE_DECIDED and returns false; the switch runs on every other change.
    struct Model
    {
        std::array<std::uint32_t, kBossCount> raw{ { DungeonKit::State::ToBeDecided, DungeonKit::State::ToBeDecided,
            DungeonKit::State::ToBeDecided, DungeonKit::State::ToBeDecided, DungeonKit::State::ToBeDecided } };
        std::uint32_t hardMode = 0;
        bool heroic = true;
        int yells = 0;
        int saves = 0;
        bool dormant = false;

        BossStates States() const
        {
            BossStates s{};
            for (std::size_t i = 0; i < kBossCount; ++i)
                s[i] = raw[i] == DungeonKit::State::ToBeDecided ? kNot : raw[i];
            return s;
        }

        void Refresh() { dormant = TaragamanDormant(States()); }

        bool Set(std::uint32_t id, std::uint32_t state)
        {
            if (raw[id] == DungeonKit::State::ToBeDecided)
            {
                raw[id] = state;
                return false;
            }
            if (raw[id] == state)
                return false;
            raw[id] = state;
            ++saves;
            if (id < kGateBossCount)
            {
                if (GateOpensOn(id, state, States()))
                    ++yells;
                Refresh();
            }
            else if (id == BOSS_TARAGAMAN)
            {
                if (state == kDone)
                {
                    if (hardMode)
                    {
                        Set(BOSS_STARVING, kDone);
                        ++saves;
                    }
                }
                else if (state != kRun)
                    Refresh();
            }
            return true;
        }

        void Arm(std::uint32_t value)
        {
            if (!HardModeChangeAllowed(heroic, States()[BOSS_TARAGAMAN], value) || value == hardMode)
                return;
            hardMode = value;
            ++saves;
        }

        // The instance's SettleDeadLieutenant: a lieutenant created dead (his respawn still ahead) settles his slot
        // through the base write (no switch, so no yell), then the gate is applied again.
        void CreateDead(std::uint32_t id)
        {
            if (!DeadLoadSettles(id, States()[id]))
                return;
            if (raw[id] != DungeonKit::State::ToBeDecided)
                ++saves;
            raw[id] = kDone;
            Refresh();
        }

        // The first Update after a Load.
        void Settle()
        {
            for (std::uint32_t i = 0; i < kBossCount; ++i)
                if (raw[i] == DungeonKit::State::ToBeDecided)
                    Set(i, kNot);
        }

        std::string Save() const
        {
            RfcSave s;
            s.states = States();
            s.hardMode = hardMode;
            return FormatRfcSave(s);
        }

        // A cold load of `in`, the creature create included.
        static Model Reload(std::string const& in, bool heroic)
        {
            Model m;
            m.heroic = heroic;
            RfcSave s;
            if (ParseRfcSave(in, s))
            {
                for (std::uint32_t i = 0; i < kBossCount; ++i)
                    m.Set(i, s.states[i]);
                m.hardMode = s.hardMode;
            }
            m.Settle();
            m.Refresh();
            return m;
        }
    };

    void TestIds()
    {
        CHECK(kMapRagefireChasm == 389);
        CHECK(std::string(kInstanceScriptName) == "instance_ragefire_chasm");
        CHECK(std::string(kTestCommand) == "dbtest rfc");
        CHECK(std::string(kLogDungeon) == "rfc");

        // Slots 0 to 2 are the gate's, 3 is gated, 4 the hard mode kill; the order is the kill order (ruling 2).
        CHECK(kBossCount == 5 && kGateBossCount == 3);
        CHECK(BOSS_OGGLEFLINT == 0 && BOSS_JERGOSH == 1 && BOSS_BAZZALAN == 2 && BOSS_TARAGAMAN == 3);
        CHECK(BOSS_STARVING == 4);
        for (char const* name : kBossNames)
            CHECK(name && *name);

        std::set<std::uint32_t> const data{ DATA_HARD_MODE, DATA_HARD_MODE_KILLED, DATA_GATE_OPEN,
            DATA_TARAGAMAN_DORMANT };
        CHECK(data.size() == 4);
        // Data ids never collide with the guid keys of the four bosses.
        for (std::uint32_t const id : data)
            CHECK(id < kGuidBossBase);
        std::set<std::int32_t> const actions{ ACTION_RFC_GATE_OPENED, ACTION_RFC_HARD_MODE_ARMED,
            ACTION_RFC_HARD_MODE_CLEARED };
        CHECK(actions.size() == 3);

        for (std::uint32_t const boss : { NPC_OGGLEFLINT, NPC_JERGOSH, NPC_BAZZALAN, NPC_TARAGAMAN })
            CHECK(IsRfcBossEntry(boss));
        for (std::uint32_t const other : { std::uint32_t(NPC_EARTHBORER), std::uint32_t(NPC_RFC_BORER),
                 std::uint32_t(NPC_RFC_BLOOD_GLOBULE), std::uint32_t(NPC_ZELEMAR), 0u })
            CHECK(!IsRfcBossEntry(other));

        // The slices tile the reservation in order, the spare at the end; the gear's block is not ours.
        std::uint32_t next = kSpellsReservation.first;
        for (IdSlice const& slice : kSpellSlices)
        {
            CHECK(slice.first == next && slice.first <= slice.last);
            next = slice.last + 1;
        }
        CHECK(kSpellsSpare.first == next && kSpellsSpare.last == kSpellsReservation.last);
        CHECK(kSpellsReservation.first == 213540 && kSpellsReservation.last == 213799);
        CHECK(!kSpellsReservation.Contains(213539) && !kSpellsReservation.Contains(213500));
        for (std::uint32_t const entry : { NPC_RFC_BORER, NPC_RFC_SOUL_WISP, NPC_RFC_BLOOD_GLOBULE, NPC_RFC_STALKER,
                 NPC_RFC_ENTRANCE_ORC })
            CHECK(kCreaturesReservation.Contains(entry));
        for (std::uint32_t const entry : { GO_RFC_BLOOD_SHRINE, GO_RFC_POUR_SPOT, GO_RFC_SEARING_SPIKE })
            CHECK(kGameObjectsReservation.Contains(entry));
        CHECK(!kGameObjectsReservation.Contains(GO_BLOOD_FILLED_ORB));

        // creature_text groups are 0-based and contiguous per boss (section 3.5 rule 32).
        CHECK(EMOTE_OGGLEFLINT_HUNT == 0 && EMOTE_OGGLEFLINT_BEATING == 2);
        CHECK(YELL_JERGOSH_AGGRO == 0 && EMOTE_JERGOSH_EATEN == 3);
        CHECK(YELL_BAZZALAN_AGGRO == 0 && EMOTE_BAZZALAN_SHADOWSTEP == 5);
        CHECK(YELL_TARAGAMAN_GATE == 0 && YELL_TARAGAMAN_POURED == 9);
    }

    void TestSave()
    {
        RfcSave s;
        s.states = { { kDone, kNot, kDone, kFail, kNot } };
        s.hardMode = 1;
        std::string const text = FormatRfcSave(s);
        CHECK(text == "R F C 3 0 3 2 0 1");

        RfcSave r;
        CHECK(ParseRfcSave(text, r));
        // A FAIL or IN_PROGRESS slot cannot survive a reload.
        CHECK((r.states == BossStates{ { kDone, kNot, kDone, kNot, kNot } }));
        CHECK(r.hardMode == 1);

        // A full round trip of a cleared hard mode run.
        s.states = { { kDone, kDone, kDone, kDone, kDone } };
        CHECK(ParseRfcSave(FormatRfcSave(s), r));
        CHECK(r.states == s.states && r.hardMode == 1);

        // Sanitized: the flag to 0 / 1; a kill slot without Taragaman DONE is dropped.
        CHECK(ParseRfcSave("R F C 3 3 3 0 3 7", r));
        CHECK(r.hardMode == 1 && r.states[BOSS_STARVING] == kNot);
        CHECK(ParseRfcSave("R F C 3 3 3 1 0 0", r));
        CHECK(r.states[BOSS_TARAGAMAN] == kNot);
        // A short tail (an older build) leaves the rest at 0.
        CHECK(ParseRfcSave("R F C 3 3", r));
        CHECK(r.states[BOSS_OGGLEFLINT] == kDone && r.states[BOSS_BAZZALAN] == kNot && r.hardMode == 0);

        // Foreign or empty strings are ignored, and leave a clean save.
        for (char const* bad : { "", "S K 3 3 3", "D E 3 3 3 3 3 1", "R F 3 3 3 3 3 1", "R F C", "3 3 3" })
        {
            CHECK(!ParseRfcSave(bad, r));
            CHECK(r.hardMode == 0 && r.states == BossStates{});
        }
    }

    void TestGateRules()
    {
        // 0, 1, 2 and 3 lieutenants done, in every combination: the gate needs all three, in any order.
        for (std::uint32_t mask = 0; mask < 8; ++mask)
        {
            BossStates s{};
            for (std::uint32_t i = 0; i < kGateBossCount; ++i)
                s[i] = mask & (1u << i) ? kDone : kNot;
            CHECK(GateOpen(s) == (mask == 7));
            CHECK(TaragamanDormant(s) == (mask != 7));
            // Taragaman's own slot never opens or closes it, and a fighting or dead Taragaman is never put to sleep.
            for (std::uint32_t const own : { kNot, kRun, kFail, kDone })
            {
                s[BOSS_TARAGAMAN] = own;
                CHECK(GateOpen(s) == (mask == 7));
                CHECK(TaragamanDormant(s) == (mask != 7 && own != kRun && own != kDone));
            }
        }
        // Only a DONE counts.
        for (std::uint32_t const state : { kNot, kRun, kFail, DungeonKit::State::Special })
            CHECK(!GateOpen({ { kDone, kDone, state, kNot, kNot } }));

        // The yell: the live change that completes the three, and nothing else.
        BossStates const open{ { kDone, kDone, kDone, kNot, kNot } };
        for (std::uint32_t id = 0; id < kGateBossCount; ++id)
        {
            CHECK(GateOpensOn(id, kDone, open));
            CHECK(!GateOpensOn(id, kNot, open));
            CHECK(!GateOpensOn(id, kRun, open));
        }
        CHECK(!GateOpensOn(BOSS_TARAGAMAN, kDone, open));
        CHECK(!GateOpensOn(BOSS_STARVING, kDone, open));
        CHECK(!GateOpensOn(BOSS_OGGLEFLINT, kDone, { { kDone, kDone, kNot, kNot, kNot } }));
    }

    void TestGateRuns()
    {
        // A fresh instance: every slot's first write (BossAI::_Reset or the settle) is stored without the switch.
        Model m;
        m.Settle();
        m.Refresh();
        CHECK(m.dormant && m.yells == 0 && m.saves == 0);

        // Any kill order; wipes in between; the third kill opens it once.
        m.Set(BOSS_BAZZALAN, kRun);
        m.Set(BOSS_BAZZALAN, kNot);
        m.Set(BOSS_BAZZALAN, kRun);
        m.Set(BOSS_BAZZALAN, kDone);
        CHECK(m.dormant && m.yells == 0);
        m.Set(BOSS_OGGLEFLINT, kDone);
        CHECK(m.dormant && m.yells == 0);
        std::string const twoDone = m.Save();
        m.Set(BOSS_JERGOSH, kRun);
        m.Set(BOSS_JERGOSH, kDone);
        CHECK(!m.dormant && m.yells == 1);

        // A wipe on Taragaman never closes it again; his kill does nothing to it.
        m.Set(BOSS_TARAGAMAN, kRun);
        m.Set(BOSS_TARAGAMAN, kNot);
        CHECK(!m.dormant && m.yells == 1);
        std::string const open = m.Save();
        m.Set(BOSS_TARAGAMAN, kRun);
        m.Set(BOSS_TARAGAMAN, kDone);
        CHECK(!m.dormant && m.yells == 1);

        // Reloads: 2 of 3 keeps it closed, 3 of 3 opens it without a yell, and the third kill after a reload yells.
        Model r = Model::Reload(twoDone, true);
        CHECK(r.dormant && r.yells == 0);
        r.Set(BOSS_JERGOSH, kDone);
        CHECK(!r.dormant && r.yells == 1);
        r = Model::Reload(open, true);
        CHECK(!r.dormant && r.yells == 0 && GateOpen(r.States()));
        // Dead Taragaman, reloaded.
        r = Model::Reload(m.Save(), true);
        CHECK(!r.dormant && r.yells == 0 && r.States()[BOSS_TARAGAMAN] == kDone);
        // No save at all.
        r = Model::Reload("", true);
        CHECK(r.dormant);

        // Lieutenants that load dead with no slot of theirs saved (an instance from before the rework): one dead keeps
        // the gate closed and the other two kills open it with the yell; all three dead open it without one.
        CHECK(DeadLoadSettles(BOSS_OGGLEFLINT, kNot) && !DeadLoadSettles(BOSS_OGGLEFLINT, kDone));
        CHECK(!DeadLoadSettles(BOSS_TARAGAMAN, kNot) && !DeadLoadSettles(BOSS_STARVING, kNot));
        Model old;
        old.CreateDead(BOSS_JERGOSH);
        old.Settle();
        CHECK(old.dormant && old.States()[BOSS_JERGOSH] == kDone);
        old.Set(BOSS_OGGLEFLINT, kDone);
        old.Set(BOSS_BAZZALAN, kDone);
        CHECK(!old.dormant && old.yells == 1);
        for (bool const settledFirst : { false, true })
        {
            Model all;
            if (settledFirst)
                all.Settle();
            for (std::uint32_t id = 0; id < kGateBossCount; ++id)
                all.CreateDead(id);
            all.Settle();
            CHECK(!all.dormant && all.yells == 0 && GateOpen(all.States()));
            CHECK(all.States()[BOSS_TARAGAMAN] == kNot);
            CHECK(Model::Reload(all.Save(), true).yells == 0 && GateOpen(Model::Reload(all.Save(), true).States()));
        }
        // A GM's respawn of one of them closes it again.
        old.Set(BOSS_JERGOSH, kNot);
        CHECK(old.dormant);

        // A lieutenant's slot written back (a GM's respawn): closed again out of combat, never mid fight.
        r = Model::Reload(open, true);
        r.Set(BOSS_OGGLEFLINT, kNot);
        CHECK(r.dormant);
        r = Model::Reload(open, true);
        r.Set(BOSS_TARAGAMAN, kRun);
        r.Set(BOSS_OGGLEFLINT, kNot);
        CHECK(!r.dormant);
        r.Set(BOSS_TARAGAMAN, kNot);        // he resets: the gate is closed for him now
        CHECK(r.dormant);
    }

    void TestHardMode()
    {
        // Armed on heroic only, before he is engaged or dead, at any gate state; cleared under the same clock.
        for (std::uint32_t const state : { kNot, kFail })
        {
            CHECK(HardModeChangeAllowed(true, state, 1));
            CHECK(!HardModeChangeAllowed(false, state, 1));
            CHECK(HardModeChangeAllowed(true, state, 0));
            CHECK(HardModeChangeAllowed(false, state, 0));
        }
        for (std::uint32_t const state : { kRun, kDone })
            for (std::uint32_t const value : { 0u, 1u })
            {
                CHECK(!HardModeChangeAllowed(true, state, value));
                CHECK(!HardModeChangeAllowed(false, state, value));
            }

        // The loot bit rides the flag until he is dead.
        CHECK(HardModeLootLit(1, kNot) && HardModeLootLit(1, kRun) && HardModeLootLit(1, kFail));
        CHECK(!HardModeLootLit(1, kDone) && !HardModeLootLit(0, kRun));

        // Normal: refused, no kill slot.
        Model n;
        n.heroic = false;
        n.Settle();
        n.Arm(1);
        CHECK(n.hardMode == 0);

        // Heroic, the gate closed: the flag holds through wipes and reloads, and the kill records slot 4 with a save of
        // its own.
        Model m;
        m.Settle();
        m.Arm(1);
        CHECK(m.hardMode == 1);
        m = Model::Reload(m.Save(), true);
        CHECK(m.hardMode == 1 && m.dormant);
        for (std::uint32_t id = 0; id < kGateBossCount; ++id)
            m.Set(id, kDone);
        m.Set(BOSS_TARAGAMAN, kRun);
        m.Arm(0);                           // refused mid fight
        CHECK(m.hardMode == 1);
        m.Set(BOSS_TARAGAMAN, kNot);        // a wipe
        CHECK(m.hardMode == 1);
        m.Set(BOSS_TARAGAMAN, kRun);
        int const saves = m.saves;
        m.Set(BOSS_TARAGAMAN, kDone);
        CHECK(m.States()[BOSS_STARVING] == kDone);
        CHECK(m.saves >= saves + 2);
        m.Arm(0);                           // inert once he is dead
        CHECK(m.hardMode == 1);
        m = Model::Reload(m.Save(), true);
        CHECK(m.States()[BOSS_STARVING] == kDone && m.States()[BOSS_TARAGAMAN] == kDone && m.hardMode == 1);

        // An unarmed heroic kill leaves slot 4 alone.
        Model p;
        p.Settle();
        p.Set(BOSS_TARAGAMAN, kRun);
        p.Set(BOSS_TARAGAMAN, kDone);
        CHECK(p.States()[BOSS_STARVING] == kNot);
    }

    void TestArenas()
    {
        // Spawns and the spots of each room.
        CHECK(In(OggleflintArena(), kOggleflintSpawn) && In(DenFloor(), kOggleflintSpawn));
        CHECK(In(OggleflintArena(), kDenTankSpot) && In(DenFloor(), kDenTankSpot));
        CHECK(In(OggleflintArena(), kDenNeck) && !In(DenFloor(), kDenNeck));
        CHECK(In(JergoshArena(), kJergoshSpawn) && In(JergoshArena(), kOfferingSpot));
        CHECK(In(JergoshArena(), kBloodShrine) && In(JergoshArena(), kOrb));
        CHECK(!In(JergoshArena(), { -306.5f, 218.5f, -24.f }));                 // the strip's end: outside
        CHECK(In(BazzalanArena(), kBazzalanSpawn) && In(BazzalanArena(), kRidgeSafeDisc));
        CHECK(!In(BazzalanArena(), kRidgeNeck) && In(RidgeFloor(), kRidgeNeck));
        CHECK(In(TaragamanArena(), kTaragamanSpawn) && In(TaragamanArena(), kHub));
        for (std::uint32_t slot = 0; slot < kBossCount; ++slot)
            CHECK(!ArenaFor(slot).Empty());
        CHECK(ArenaFor(kBossCount).Empty());

        // The other rooms, the levels above and below, and the drops are outside.
        CHECK(!In(OggleflintArena(), { -157.f, 24.f, -21.3f }));                // the jump-in ledges
        CHECK(!In(OggleflintArena(), { -145.f, 20.f, -18.f }));
        CHECK(!In(OggleflintArena(), kCheckpoint));
        CHECK(!In(TaragamanArena(), { -245.f, 150.f, kLavaZ }));
        CHECK(!In(PlateauFloor(), { -258.f, 150.f, -25.f }));                   // the bank trails' height
        CHECK(!In(TaragamanArena(), kJergoshSpawn) && !In(JergoshArena(), kTaragamanSpawn));
        CHECK(!In(BazzalanArena(), { -380.f, 162.f, -18.f }));                  // the hall's neck below the east rim
        for (Point3 const& p : { kFinderStart, kEntranceOrc })
            for (std::uint32_t slot = 0; slot < kBossCount; ++slot)
                CHECK(!In(ArenaFor(slot), p));

        // A player knocked up (the eruption, Uppercut's 6.3 yd peak) stays inside his arena's z band.
        CHECK(OggleflintArena().Contains(kOggleflintSpawn.XY(), kOggleflintSpawn.z + 8.f));
        CHECK(TaragamanArena().Contains(kHub.XY(), kHub.z + 8.f));
        CHECK(PlateauFloor().Contains(kHub.XY(), kHub.z + 8.f));

        // Sizes (NAVMESH-REPORT): the den 527 sq yd, the plateau 1,686 (2 yd arena at most 1,040), the ridge 1,674.
        CHECK(Near(Area(kDenFloorPolygon), 524.f, 12.f));
        CHECK(Area(kPlateauArenaPolygon) > 950.f && Area(kPlateauArenaPolygon) < 1045.f);
        CHECK(Area(kPlateauFloorPolygon) > 1680.f && Area(kPlateauFloorPolygon) < 1960.f);
        CHECK(Near(Area(kRidgeFloorPolygon), 1730.f, 80.f));
        CHECK(Area(kRidgeArenaPolygon) > 775.f && Area(kRidgeArenaPolygon) < 950.f);
        CHECK(Area(kHallArenaPolygon) > 2940.f && Area(kHallArenaPolygon) < 3300.f);

        // Bazzalan's arena stays 4 yd inside the ridge's rims (its north cut at y 184 is open floor), the plateau's 2
        // yd inside its edges (the arm ends, cut on floor at z -22.5, are no edges). The floor polygons reach 0.5 to
        // 0.75 yd past the mesh and are simplified, hence 3.9; on the mesh raster the arenas measure 4.08 and 2.0.
        CHECK(Inside(kRidgeArenaPolygon, kRidgeFloorPolygon, 3.9f, [](Vec2 p) { return p.y < 183.5f; }));
        CHECK(Inside(kPlateauArenaPolygon, kPlateauFloorPolygon, 2.0f, [](Vec2 p)
        {
            return DungeonKit::Distance(p, kHub.XY()) < 30.f;
        }));
        CHECK(Inside(kDenFloorPolygon, kDenArenaPolygon, 0.f, [](Vec2) { return true; }));

        // Clamped landings: a point inside stays; one off the floor comes back onto it.
        std::span<Vec2 const> const plateau(kPlateauArenaPolygon);
        Vec2 const kept = ClampInto(plateau, kHub.XY());
        CHECK(Near(kept.x, kHub.x, 0.001f) && Near(kept.y, kHub.y, 0.001f));
        for (Vec2 const off : { Vec2{ -239.f, 132.f }, Vec2{ -290.f, 150.f }, Vec2{ -245.f, 200.f },
                 Vec2{ -200.f, 150.f }, Vec2{ -300.f, 95.f } })
        {
            Vec2 const p = ClampInto(plateau, off);
            auto const edge = DungeonKit::NearestEdge(plateau, p);
            CHECK(edge && (DungeonKit::PointInPolygon(plateau, p) || edge->distance < 0.01f));
        }
        std::span<Vec2 const> const den(kDenFloorPolygon);
        CHECK(DungeonKit::PointInPolygon(den, ClampInto(den, kDenNeck.XY())));
        std::span<Vec2 const> const ridge(kRidgeArenaPolygon);
        CHECK(DungeonKit::PointInPolygon(ridge, ClampInto(ridge, { -415.f, 160.f })));

        // Rim distance: none off the ridge, 12 yd or more at the spawn and the safe disc, small at the east rim.
        CHECK(RimDistance(kBazzalanSpawn.XY()) > 11.5f);
        CHECK(RimDistance(kRidgeSafeDisc.XY()) > 13.5f);
        CHECK(RimDistance({ -366.8f, 146.f }) < Bazzalan::kRimSkipYd);
        CHECK(RimDistance({ -320.f, 146.f }) == 0.f);
        for (Vec2 const p : kRidgeArenaPolygon)
            CHECK(p.y > 183.5f || RimDistance(p) >= Bazzalan::kRimSkipYd);
    }

    void TestPlateauSpots()
    {
        // The spikes: 10 yd from the hub, on the arena; the hide spots behind them too (nothing over lava); and two
        // neighbouring hide spots are apart.
        for (std::size_t i = 0; i < kSpikePointCount; ++i)
        {
            Point3 const& spike = kSpikePoints[i];
            CHECK(In(TaragamanArena(), spike));
            CHECK(Near(DungeonKit::Distance(spike.XY(), kHub.XY()), 10.f, 0.1f));
            Vec2 const hide = SpikeHideSpot(i, Taragaman::kSpikeHideYd);
            CHECK(Near(DungeonKit::Distance(hide, kHub.XY()), 15.f, 0.2f));
            CHECK(TaragamanArena().Contains(hide, spike.z));
            for (std::size_t j = 0; j < i; ++j)
                CHECK(DungeonKit::Distance(hide, SpikeHideSpot(j, Taragaman::kSpikeHideYd)) > 12.f);
        }

        // Globules: on the plateau's floor, 12.8 s or less from him at their speed (section 7 #22 A: 7 to 13 s).
        for (Point3 const& start : kGlobuleStarts)
        {
            CHECK(In(PlateauFloor(), start));
            float const seconds = DungeonKit::Distance(start.XY(), kHub.XY()) / Taragaman::kGlobuleSpeed;
            CHECK(seconds > 7.f && seconds < 13.3f);
        }

        // The drifting ring (section 7 #25 A): its disc reaches 18 yd at most, well short of the arm ends.
        CHECK(Taragaman::kDriftClampYd + Taragaman::kFelstormRadius.hardMode <= 18.f);

        // The pour spot is at the plateau's -x foot, the lava cell beside it below; the shrine by the Orb, out of its
        // own use range (two objects 2 yd or more apart).
        CHECK(PlateauFloor().Contains(kPourSpot.XY(), kPourSpot.z));
        CHECK(DungeonKit::Distance(kPourSpot.XY(), kPourLava.XY()) < 2.f && kPourLava.z < kPourSpot.z - 3.f);
        CHECK(DungeonKit::Distance(kBloodShrine.XY(), kOrb.XY()) > 2.f);

        // The wisp's goal (section 7 #21 A): 50 yd, about 16.5 s.
        float const drift = DungeonKit::Distance(kJergoshSpawn.XY(), kOfferingSpot.XY()) / Jergosh::kWispSpeed;
        CHECK(drift > 15.5f && drift < 17.5f);

        // The checkpoint is on the return route, never on the plateau and over 30 yd from every boss arena's spawn.
        for (Point3 const& spawn : { kOggleflintSpawn, kJergoshSpawn, kBazzalanSpawn, kTaragamanSpawn })
            CHECK(DungeonKit::Distance(kCheckpoint.XY(), spawn.XY()) > 30.f);
    }

    void TestTuning()
    {
        // Health (section 3.6): HealthModifier on the level 16 class bases 356 (warrior) and 307 (mage); level 60
        // 3,052 and 2,136.
        CHECK(Oggleflint::kHealth.normal == 60 * 356 && Oggleflint::kHealth.heroic == 104 * 3052);
        CHECK(Jergosh::kHealth.normal == 70 * 307 && Jergosh::kHealth.heroic == 157 * 2136);
        CHECK(Bazzalan::kHealth.normal == 65 * 356 && Bazzalan::kHealth.heroic == 109 * 3052);
        CHECK(Taragaman::kHealth.normal == (684 * 356 + 9) / 10);     // 68.4: the engine rounds up
        CHECK(Taragaman::kHealth.heroic == 137 * 3052);
        CHECK(Taragaman::kHealth.hardMode == 267 * 3052);

        CHECK(ModeFor(false, false) == Mode::Normal && ModeFor(false, true) == Mode::Normal);
        CHECK(ModeFor(true, false) == Mode::Heroic && ModeFor(true, true) == Mode::HardMode);
        CHECK(Taragaman::kNovaPct(Mode::Normal) == 50.f && Taragaman::kNovaPct(Mode::HardMode) == 90.f);

        // Rupture: 40% over six ticks on normal.
        CHECK(Near(Bazzalan::RuptureTickPct(false) * 6.f, 40.f, 0.001f));
        CHECK(Bazzalan::RuptureTickPct(true) == 2.f);

        // Ruling 15: no Gorged cap off normal.
        CHECK(Taragaman::kGorgedCap.normal == 3 && !Taragaman::kGorgedCap.heroic && !Taragaman::kGorgedCap.hardMode);

        // Ruling 16 (a hard mode matches or exceeds heroic on every value): percents and healing up or equal, warnings,
        // cadences and gaps down or equal.
        CHECK(Taragaman::kFeastBitePct.hardMode >= Taragaman::kFeastBitePct.heroic);
        CHECK(Taragaman::kFeastEveryMs.hardMode <= Taragaman::kFeastEveryMs.heroic);
        CHECK(Taragaman::kFeastFirstMs.hardMode <= Taragaman::kFeastFirstMs.heroic);
        CHECK(Taragaman::kFeastMarkMs.hardMode <= Taragaman::kFeastMarkMs.heroic);
        CHECK(Taragaman::kDevourTickPct.hardMode >= Taragaman::kDevourTickPct.heroic);
        CHECK(Taragaman::kFelstormFirstMs.hardMode <= Taragaman::kFelstormFirstMs.heroic);
        CHECK(Taragaman::kFelstormEveryMs.hardMode <= Taragaman::kFelstormEveryMs.heroic);
        CHECK(Taragaman::kFelstormSpinMs.hardMode >= Taragaman::kFelstormSpinMs.heroic);
        CHECK(Taragaman::kFelstormRadius.hardMode >= Taragaman::kFelstormRadius.heroic);
        CHECK(Taragaman::kFelstormTickPct.hardMode >= Taragaman::kFelstormTickPct.heroic);
        CHECK(Taragaman::kPulsePct.hardMode >= Taragaman::kPulsePct.heroic);
        CHECK(Taragaman::kSpotRadius.hardMode >= Taragaman::kSpotRadius.heroic);
        CHECK(Taragaman::kSpotWarnMs.hardMode <= Taragaman::kSpotWarnMs.heroic);
        CHECK(Taragaman::kSpotPct.hardMode >= Taragaman::kSpotPct.heroic);
        CHECK(Taragaman::kNovaFirstMs.hardMode <= Taragaman::kNovaFirstMs.heroic);
        CHECK(Taragaman::kNovaEveryMs.hardMode <= Taragaman::kNovaEveryMs.heroic);
        CHECK(Taragaman::kNovaCastMs.hardMode <= Taragaman::kNovaCastMs.heroic);
        CHECK(Taragaman::kNovaPct.hardMode >= Taragaman::kNovaPct.heroic);
        CHECK(Taragaman::kNovaSpikes.hardMode <= Taragaman::kNovaSpikes.heroic);
        CHECK(Taragaman::kComboEveryMs <= Taragaman::kFelstormEveryMs.heroic);      // section 7 #27 A
        // ... and the combo still fits its cycle: cast, spin, gap, Nova, the Feast hold.
        CHECK(Taragaman::kFelstormCastMs + Taragaman::kFelstormSpinMs.hardMode + Taragaman::kComboNovaAfterSpinMs
            + Taragaman::kNovaCastMs.hardMode + Taragaman::kFeastAfterSetPieceMs < Taragaman::kComboEveryMs);
        // A spot's ten marks fit the spin, and its offset keeps the player inside or at the edge.
        CHECK(Taragaman::kSpotCount * Taragaman::kSpotEveryMs <= Taragaman::kFelstormSpinMs.heroic);
        CHECK(Taragaman::kSpotOffsetMax.heroic <= Taragaman::kSpotRadius.heroic);
        CHECK(Taragaman::kSpotOffsetMax.hardMode <= Taragaman::kSpotRadius.hardMode);
        // Heroic lethality (ruling 11): a full spin inside the ring is 100%.
        CHECK(Taragaman::kFelstormTickPct.heroic * float(Taragaman::kFelstormSpinMs.heroic
            / Taragaman::kFelstormTickMs) == 100.f);

        // Ruling 15 and the beats of the other three.
        CHECK(Oggleflint::kExtraBorerEveryMs == 40000);
        CHECK(Oggleflint::kChaseSpeed.heroic < 7.f);            // slower than a run
        CHECK(Jergosh::kImmolateDurationMs / Jergosh::kImmolateTickMs == 7);
        CHECK(Bazzalan::kComboMax * Bazzalan::kStrikeEveryMs.heroic + Bazzalan::kFinisherCastMs <= 12000);
    }
}

int main()
{
    // Hit counters: players only.
    struct Guid
    {
        bool player;
        bool IsPlayer() const { return player; }
    };
    CHECK(PlayerHits(std::array<Guid, 0>{}) == 0);
    CHECK(PlayerHits(std::array<Guid, 1>{ { { false } } }) == 0);
    CHECK(PlayerHits(std::array<Guid, 3>{ { { true }, { false }, { true } } }) == 2);
    TestIds();
    TestSave();
    TestGateRules();
    TestGateRuns();
    TestHardMode();
    TestArenas();
    TestPlateauSpots();
    TestTuning();
    return Report("ragefire_chasm_test");
}
