// Host tests for GrandLieLogic.h (S8: Balnazzar's hard mode, the Grand Lie).
#include "DathrohanLogic.h"
#include "GrandLieLogic.h"
#include "check.h"
#include <cmath>

using namespace StratholmeRework;
using namespace StratGrandLie;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    float Dist(Vec2 a, Vec2 b)
    {
        return std::sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
    }

    // Signed distance from the split line (frame +Y side positive).
    float MiddleSide(Vec2 p)
    {
        Vec2 const c = Brazier();
        Vec2 const m = MiddleNormal();
        return (p.x - c.x) * m.x + (p.y - c.y) * m.y;
    }

    // Walks a swarm with the middle closed for `yd` of crawl (a call's 4 s is 12 yd), leg by leg, and returns the
    // smallest |side| its center reaches after `graceYd` of crawl, and whether it ever changed side.
    struct Walk
    {
        float minSide = 1000.f;
        bool flipped = false;
    };

    Walk WalkClosed(Vec2 pos, Vec2 dir, float yd, float graceYd)
    {
        Walk w;
        float const startSide = MiddleSide(pos);
        float walked = 0.f;
        for (int legs = 0; legs < 64 && walked < yd; ++legs)
        {
            SwarmLeg const leg = PlanLeg(pos, dir, true);
            float const len = std::min(leg.length, yd - walked);
            for (float t = 0.f; t <= len; t += 0.05f)
            {
                Vec2 const p{ pos.x + dir.x * t, pos.y + dir.y * t };
                float const side = MiddleSide(p);
                if (walked + t >= graceYd)
                    w.minSide = std::min(w.minSide, std::fabs(side));
                if (startSide != 0.f && side * startSide < 0.f)
                    w.flipped = true;
            }
            walked += leg.length;
            pos = leg.end;
            dir = leg.dirAfter;
        }
        return w;
    }

    // The safe floor of a call (F-2 MAJ-1): the room's floor (StratDathrohan::kBoundsRadius around the brazier) off
    // the struck half and off the Ring's struck part, on a 0.5 yd grid. `clear`: whether a spot with `clearYd` of safe
    // floor all around exists.
    struct Floor
    {
        float area = 0.f;
        bool clear = false;
    };

    Floor SafeFloor(Vec2 boss, Half struck, bool lieRing, float clearYd)
    {
        Floor f;
        float const R = StratDathrohan::kBoundsRadius;
        float const step = 0.5f;
        Vec2 const c = Brazier();
        for (float dx = -R; dx <= R; dx += step)
            for (float dy = -R; dy <= R; dy += step)
            {
                Vec2 const p{ c.x + dx, c.y + dy };
                float const fromCenter = Dist(p, c);
                if (fromCenter > R || HalfOf(p) == struck)
                    continue;
                float const fromBoss = Dist(p, boss);
                if (lieRing ? fromBoss > kRingRadius : fromBoss <= kRingRadius)
                    continue;
                f.area += step * step;
                float const side = MiddleSide(p) * (struck == Half::A ? 1.f : -1.f);    // + into the spared half
                bool const roomy = fromCenter <= R - clearYd && side >= clearYd
                    && (lieRing ? fromBoss <= kRingRadius - clearYd : fromBoss >= kRingRadius + clearYd);
                f.clear = f.clear || roomy;
            }
        return f;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation; never S7's.
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    for (std::uint32_t id : { uint32_t(SPELL_GL_CLEAVE_LIGHT), uint32_t(SPELL_GL_MEDALLION) })
    {
        CHECK(kSpellSlice.Contains(id));
        CHECK(!kSpellsDathrohan.Contains(id));
    }
    // The hard mode's kill slot is its own and fights in its boss's arena.
    CHECK(IsHardModeSlot(BOSS_GRAND_LIE));
    CHECK(!ArenaFor(BOSS_GRAND_LIE).Empty());
    // Tags and the cast id stay clear of S7's (below 20, queue ids below 100).
    CHECK(TAG_GL_CLEAVE >= 20);
    CHECK(TAG_GL_PARK != TAG_GL_STANDARD && TAG_GL_STANDARD > TAG_GL_SWARM);
    CHECK(CAST_DREAD_SLUMBER >= 100);

    // ---- Acts -------------------------------------------------------------------------------------------------------
    CHECK(ActForHealth(100.f) == Act::Lies);
    CHECK(ActForHealth(70.01f) == Act::Lies);
    CHECK(ActForHealth(70.f) == Act::LiesUponLies);
    CHECK(ActForHealth(40.01f) == Act::LiesUponLies);
    CHECK(ActForHealth(40.f) == Act::GrandLie);
    CHECK(ActForHealth(1.f) == Act::GrandLie);
    CHECK(NextAct(Act::GrandLie, 90.f) == Act::GrandLie);       // never back (a heal from Vampiric Aura)
    CHECK(NextAct(Act::Lies, 50.f) == Act::LiesUponLies);
    CHECK(NextAct(Act::Lies, 10.f) == Act::GrandLie);           // a burst through two thresholds
    CHECK(SwarmCap(Act::Lies) == 2 && SwarmCap(Act::LiesUponLies) == 3 && SwarmCap(Act::GrandLie) == 4);
    CHECK(CallEveryMs(Act::Lies) == 10000 && CallEveryMs(Act::LiesUponLies) == 12000);
    CHECK(CallEveryMs(Act::GrandLie) == 15000);
    CHECK(kHardModeHealth == 600000);

    // ---- Calls: one twin in turn, pairs, all three ------------------------------------------------------------------
    {
        std::vector<Twin> a0 = CallTwins(Act::Lies, 0), a1 = CallTwins(Act::Lies, 1), a2 = CallTwins(Act::Lies, 2);
        CHECK(a0.size() == 1 && a0[0] == Twin::Cleave);
        CHECK(a1.size() == 1 && a1[0] == Twin::Ring);
        CHECK(a2.size() == 1 && a2[0] == Twin::Mark);
        CHECK(CallTwins(Act::Lies, 3)[0] == Twin::Cleave);
        std::vector<Twin> p = CallTwins(Act::LiesUponLies, 2);
        CHECK(p.size() == 2 && p[0] == Twin::Mark && p[1] == Twin::Cleave);
        std::vector<Twin> t = CallTwins(Act::GrandLie, 1);
        CHECK(t.size() == 3 && t[0] == Twin::Ring && t[1] == Twin::Mark && t[2] == Twin::Cleave);
    }
    // Each piece yells 1 s after the last; all land 4 s after the first yell.
    for (std::uint32_t i = 0; i < 3; ++i)
        CHECK(PieceYellAt(1000, i) + PieceWarnMs(i) == 1000 + kCallLandMs);
    CHECK(PieceWarnMs(0) == 4000 && PieceWarnMs(2) == 2000);
    // True lines say "the Light" (even numbers 10, 12, 14), lies the odd ones.
    CHECK(YellOf(Twin::Cleave, true) == 10 && YellOf(Twin::Cleave, false) == 11);
    CHECK(YellOf(Twin::Ring, true) == 12 && YellOf(Twin::Ring, false) == 13);
    CHECK(YellOf(Twin::Mark, true) == 14 && YellOf(Twin::Mark, false) == 15);
    CHECK(RollTrue(0) && RollTrue(49) && !RollTrue(50) && !RollTrue(99));

    // ---- Halves -----------------------------------------------------------------------------------------------------
    // The measured half spots fall on their halves; the brazier sits on the split line.
    for (Vec2 p : kDathrohanHalfASpots)
        CHECK(HalfOf(p) == Half::A);
    for (Vec2 p : kDathrohanHalfBSpots)
        CHECK(HalfOf(p) == Half::B);
    CHECK(Near(DungeonKit::ToFrame(kDathrohanHalves, Brazier()).y, kDathrohanSplitY, 0.05f));
    // The cone facing for a half points into it: 10 yd along it lands on that half.
    for (Half h : { Half::A, Half::B })
    {
        float const f = HalfFacing(h);
        Vec2 const p{ Brazier().x + 10.f * std::cos(f), Brazier().y + 10.f * std::sin(f) };
        CHECK(HalfOf(p) == h);
        CHECK(Near(std::fabs(MiddleSide(p)), 10.f, 0.05f));     // square to the split line
    }
    CHECK(Near(BearingGap(HalfFacing(Half::A), HalfFacing(Half::B)), 3.14159f, 0.01f));
    // The struck half has more swarms; a tie goes by the roll; the claim follows the truth.
    CHECK(StruckHalf(2, 1, false) == Half::A);
    CHECK(StruckHalf(0, 3, true) == Half::B);
    CHECK(StruckHalf(1, 1, true) == Half::A && StruckHalf(1, 1, false) == Half::B);
    CHECK(ClaimedHalf(Half::A, true) == Half::A && ClaimedHalf(Half::A, false) == Half::B);
    // The cleave reaches every wall (radius 19-20 on the mesh) and the arena edge.
    CHECK(kCleaveLengthYd >= 22.f);
    CHECK(kRingOuter >= 2.f * 20.f);

    // ---- Swarms -----------------------------------------------------------------------------------------------------
    {
        // Spawns come out of the wall, never through the doorway, and crawl inward.
        for (float roll : { 0.f, 0.25f, 0.5f, 0.75f, 0.999f })
        {
            float const b = SpawnBearing(roll);
            CHECK(BearingGap(b, EntranceBearing()) >= kEntranceAvoidRad - 0.001f);
            SwarmStart const s = SwarmSpawn(b, 1.f, 3.f);
            CHECK(Near(Dist(s.at, Brazier()), kSwarmPathRadius, 0.01f));
            CHECK(Near(std::sqrt(s.dir.x * s.dir.x + s.dir.y * s.dir.y), 1.f, 0.001f));
            Vec2 const step{ s.at.x + s.dir.x, s.at.y + s.dir.y };
            CHECK(Dist(step, Brazier()) < kSwarmPathRadius);
        }
        // The doorway bearing points north-east of the brazier (x up, y down).
        float const e = EntranceBearing();
        CHECK(std::cos(e) > 0.f && std::sin(e) < 0.f);

        // A leg across the room ends on the wall and bounces back inside.
        SwarmStart const s = SwarmSpawn(0.f, 0.f, 0.f);     // from the north wall toward the brazier
        SwarmLeg const leg = PlanLeg(s.at, s.dir, false);
        CHECK(!leg.offMiddle);
        CHECK(Near(leg.length, 2.f * kSwarmPathRadius, 0.05f));
        CHECK(Near(Dist(leg.end, Brazier()), kSwarmPathRadius, 0.05f));
        Vec2 const back{ leg.end.x + leg.dirAfter.x, leg.end.y + leg.dirAfter.y };
        CHECK(Dist(back, Brazier()) < kSwarmPathRadius);
        // An oblique leg bounces like a mirror: the outgoing angle to the wall's normal equals the incoming one.
        SwarmLeg const obl = PlanLeg(Brazier(), { 0.6f, 0.8f }, false);
        Vec2 const n{ (obl.end.x - Brazier().x) / kSwarmPathRadius, (obl.end.y - Brazier().y) / kSwarmPathRadius };
        CHECK(Near(0.6f * n.x + 0.8f * n.y, -(obl.dirAfter.x * n.x + obl.dirAfter.y * n.y), 0.001f));

        // With the middle closed, a swarm heading across stops short of it and turns back to its own half.
        Vec2 const m = MiddleNormal();
        Vec2 const start{ Brazier().x + 8.f * m.x, Brazier().y + 8.f * m.y };      // 8 yd on the B side
        Vec2 const across{ -m.x, -m.y };
        SwarmLeg const closed = PlanLeg(start, across, true);
        CHECK(closed.offMiddle);
        CHECK(Near(closed.length, 8.f - kMiddleClearYd, 0.01f));      // its cloud's edge stops short (MIN-2)
        CHECK(MiddleSide(closed.end) - kSwarmRadius > 0.f);
        CHECK(MiddleSide(closed.end) > 0.f);
        CHECK(closed.dirAfter.x * m.x + closed.dirAfter.y * m.y > 0.f);
        // Open, it crosses to the far wall.
        SwarmLeg const open = PlanLeg(start, across, false);
        CHECK(!open.offMiddle && MiddleSide(open.end) < 0.f);
        // Moving away from the middle, a closed middle changes nothing.
        SwarmLeg const away = PlanLeg(start, m, true);
        CHECK(!away.offMiddle);
        // Already within its cloud's reach of the line when the middle closes (MIN-2): it turns at once, back to its
        // own side, leaving at kLeaveMinCos or faster; a swarm already leaving fast enough keeps its line.
        for (float side : { 2.f, 0.4f, -1.5f })
        {
            Vec2 const near{ Brazier().x + side * m.x, Brazier().y + side * m.y };
            float const own = side > 0.f ? 1.f : -1.f;
            for (Vec2 d : { Vec2{ -m.x * own, -m.y * own }, Vec2{ MiddleNormal().y, -MiddleNormal().x } })
            {
                SwarmLeg const turn = PlanLeg(near, d, true);
                CHECK(turn.offMiddle && turn.length == 0.f);
                CHECK((turn.dirAfter.x * m.x + turn.dirAfter.y * m.y) * own >= kLeaveMinCos - 0.001f);
            }
            SwarmLeg const leaving = PlanLeg(near, { m.x * own, m.y * own }, true);
            CHECK(!leaving.offMiddle && leaving.length > 1.f);
        }
        // On the line itself: it leaves toward the side it heads for.
        SwarmLeg const onLine = PlanLeg(Brazier(), { -m.x * 0.2f + 0.98f * m.y, -m.y * 0.2f - 0.98f * m.x }, true);
        CHECK(onLine.length == 0.f && onLine.dirAfter.x * m.x + onLine.dirAfter.y * m.y <= -kLeaveMinCos + 0.001f);
        // Walked over a call's 4 s from anywhere in the room, any heading: a swarm whose cloud starts clear of the
        // line never reaches it; one starting over it is clear of it once it has had time to leave, and never
        // changes side.
        float const leaveYd = kMiddleClearYd / kLeaveMinCos + 0.1f;
        for (float a = 0.f; a < 6.28f; a += 0.39f)
            for (float r : { 0.f, 1.f, 2.6f, 3.5f, 8.f, 16.f })
                for (float h = 0.f; h < 6.28f; h += 0.52f)
                {
                    Vec2 const at{ Brazier().x + r * std::cos(a), Brazier().y + r * std::sin(a) };
                    Vec2 const d{ std::cos(h), std::sin(h) };
                    bool const startsClear = std::fabs(MiddleSide(at)) >= kMiddleClearYd;
                    Walk const w = WalkClosed(at, d, kCallLandMs / 1000.f * kSwarmSpeed, startsClear ? 0.f : leaveYd);
                    CHECK(w.minSide >= kSwarmRadius - 0.01f);
                    CHECK(!w.flipped);
                }
        // A stray outside the circle comes back toward the brazier.
        Vec2 const stray{ Brazier().x + 25.f, Brazier().y };
        SwarmLeg const home = PlanLeg(stray, { 1.f, 0.f }, false);
        CHECK(Dist(home.end, Brazier()) <= kSwarmPathRadius + 0.05f);
        CHECK(home.end.x < stray.x);
        // The 5 yd cloud brushes the wall, never far past it (the mesh's rim is 19-20 yd).
        CHECK(kSwarmPathRadius + kSwarmRadius <= 20.f);
        CHECK(Near(kSwarmRadius * 2.f, 5.f));
    }

    // ---- The tank rule and the safe floor (F-2 MAJ-1) ---------------------------------------------------------------
    {
        // A hidden Park on the brazier while he stands off it; each zone ends inside the bots' 8 s hold cap.
        CHECK(!ShouldPark(Brazier()));
        CHECK(!ShouldPark({ Brazier().x + 2.9f, Brazier().y }));
        CHECK(ShouldPark({ Brazier().x + 3.1f, Brazier().y }));
        CHECK(kParkHoldMs < 8000 && kParkRadius <= kParkTriggerYd);
        CHECK(StratDathrohan::InBounds(Brazier()));
        // Wherever he stands in the room, every Ring / Cleave pair leaves a usable safe floor: 60+ sq yd and a spot
        // with 3 yd of safe floor all round (at the brazier: a half disc, 157 sq yd, for the donut).
        float worst = 1000.f;
        bool allClear = true;
        bool oldRuleFails = false;
        float const R = StratDathrohan::kBoundsRadius;
        for (float dx = -R; dx <= R; dx += 1.f)
            for (float dy = -R; dy <= R; dy += 1.f)
            {
                Vec2 const boss{ Brazier().x + dx, Brazier().y + dy };
                if (Dist(boss, Brazier()) > R)
                    continue;
                for (bool lieRing : { false, true })
                    for (bool moreInA : { false, true })
                    {
                        std::uint32_t const inA = moreInA ? 2 : 0;
                        std::uint32_t const inB = moreInA ? 0 : 2;
                        Half const struck = StruckHalfFor(inA, inB, true, lieRing, SideOfMiddle(boss));
                        Floor const f = SafeFloor(boss, struck, lieRing, 3.f);
                        worst = std::min(worst, f.area);
                        allClear = allClear && f.clear;
                        // The swarm rule alone (as built before F-2) can leave none.
                        if (lieRing && SafeFloor(boss, StruckHalf(inA, inB, true), true, 3.f).area < 1.f)
                            oldRuleFails = true;
                    }
            }
        CHECK(worst >= 60.f);
        CHECK(allClear);
        CHECK(oldRuleFails);
        // Parked on the brazier the donut leaves its half disc.
        CHECK(SafeFloor(Brazier(), Half::A, true, 3.f).area >= 150.f);
        // Off the middle with a lie Ring, the half he stands in is spared; near it, the swarm rule decides.
        Vec2 const m = MiddleNormal();
        Vec2 const onB{ Brazier().x + 6.f * m.x, Brazier().y + 6.f * m.y };
        CHECK(StruckHalfFor(0, 3, true, true, SideOfMiddle(onB)) == Half::A);
        CHECK(StruckHalfFor(0, 3, true, false, SideOfMiddle(onB)) == Half::B);
        CHECK(StruckHalfFor(0, 3, true, true, 0.2f) == Half::B);
        CHECK(StruckHalfFor(3, 0, false, true, -4.f) == Half::B);
        CHECK(Near(SideOfMiddle(onB), 6.f, 0.01f));
        CHECK(SideOfMiddle(onB) > 0.f && HalfOf(onB) == Half::B);
    }

    // ---- Meteor windows and Dread Slumber ---------------------------------------------------------------------------
    {
        Window const w = CallWindow(10000);
        CHECK(w.from == 10000 && w.to == 14000);
        // A meteor that would land at 12 s (started 8.5 s) is held; one landing at 14.5 s is fine.
        CHECK(MeteorBlocked(8500, w, std::nullopt));
        CHECK(!MeteorBlocked(11000, w, std::nullopt));
        CHECK(MeteorBlocked(7000, std::nullopt, w));    // lands at 10.5 s: in the next call's window
        CHECK(!MeteorBlocked(5000, std::nullopt, w));   // lands at 8.5 s
        // The slumber's cast starts 3 s after the call's first yell, so it lands 2 s after the call.
        CHECK(SlumberCastInMs() == 3000);
        CHECK(SlumberCastInMs() + kSlumberCastMs == kCallLandMs + kSlumberAfterCallMs);
        CHECK(CallCarriesSlumber(Act::GrandLie, 20000, 17000));
        CHECK(!CallCarriesSlumber(Act::GrandLie, 20001, 17000));
        CHECK(!CallCarriesSlumber(Act::LiesUponLies, 0, 17000));
        // The group that sleeps through it (5 s) wakes 2 s before the next call lands.
        std::uint32_t const landed = 0, nextYell = landed + kCallAfterSlumberMs;
        CHECK(nextYell + kCallLandMs - (landed + 5000) == 2000);
    }

    // ---- Relics -----------------------------------------------------------------------------------------------------
    CHECK(RelicItem(GO_ST_LETTER_OF_PROOF) == ITEM_ST_LETTER_OF_PROOF);
    CHECK(RelicItem(GO_ST_SCARLET_STANDARD) == ITEM_ST_SCARLET_STANDARD);
    CHECK(RelicItem(GO_ST_BLESSED_CRATE) == ITEM_ST_BLESSED_HOLY_WATER);
    CHECK(RelicItem(GO_ST_MEDALLION_LIGHT) == ITEM_ST_RELIC_OF_THE_MEDALLION);
    CHECK(RelicItem(GO_ST_BONE_PILE) == 0);
    for (std::uint32_t item : { uint32_t(ITEM_ST_LETTER_OF_PROOF), uint32_t(ITEM_ST_RELIC_OF_THE_MEDALLION) })
        CHECK(kRelicItems.Contains(item));
    CHECK(RelicBoss(GO_ST_LETTER_OF_PROOF) == BOSS_GALFORD);
    CHECK(RelicBoss(GO_ST_SCARLET_STANDARD) == BOSS_WILLEY);
    CHECK(RelicBoss(GO_ST_MEDALLION_LIGHT) == BOSS_MALOR);
    CHECK(!RelicBoss(GO_ST_BLESSED_CRATE));
    uint32_t const done = DungeonKit::State::Done, fighting = DungeonKit::State::InProgress;
    CHECK(RelicShown(GO_ST_SCARLET_STANDARD, true, true, done));
    CHECK(!RelicShown(GO_ST_SCARLET_STANDARD, true, true, fighting));
    CHECK(!RelicShown(GO_ST_SCARLET_STANDARD, false, true, done));     // heroic only
    CHECK(!RelicShown(GO_ST_SCARLET_STANDARD, true, false, done));     // wave 2 bound only
    CHECK(RelicShown(GO_ST_BLESSED_CRATE, true, true, 0));             // the crate stands from the start
    CHECK(!RelicShown(GO_ST_BLESSED_CRATE, false, true, 0));
    // The spots stand where their bosses fought: the Letter by the archive, the light by the strongbox, the
    // Standard in Willey's yard, the crate by the stock Holy Water crate.
    CHECK(Dist(kLetterSpot.XY(), kScarletArchive.XY()) < 3.f);
    CHECK(Dist(kMedallionLightSpot.XY(), kMalorsStrongbox.XY()) > 1.f);
    CHECK(Dist(kMedallionLightSpot.XY(), kMalorsStrongbox.XY()) < 2.f);
    CHECK(WilleyArena().Contains(kStandardSpot.XY(), kStandardSpot.z));
    CHECK(Dist(kBlessedCrateSpot.XY(), kCrusadersSquareCrate.XY()) < 3.f);
    CHECK(Dist(kBlessedCrateSpot.XY(), kCrusadersSquareCrate.XY()) > 1.f);
    // Cooldowns (ruling 33) and sizes (ST HM9).
    CHECK(kHolyWaterCooldownMs == 180000 && kStandardCooldownMs == 20000 && kMedallionCooldownMs == 25000);
    CHECK(kStandardRadiusYd == 6.f && kStandardMs == 5000 && kMedallionWardMs == 4000);
    CHECK(kHolyWaterSplashYd == 5.f && kHolyWaterRangeYd == 10.f && kMedallionRadiusYd == 30.f);
    // The Medallion raised at the cast's start still wards when the slumber lands.
    CHECK(kMedallionWardMs > kSlumberCastMs);

    // ---- The Letter -------------------------------------------------------------------------------------------------
    {
        LetterCheck c;
        c.heroic = true;
        c.wave2Bound = true;
        c.dathrohanHere = true;
        c.distance = 20.f;
        CHECK(CheckLetter(c) == LetterRefusal::None);
        LetterCheck n = c;
        n.heroic = false;
        CHECK(CheckLetter(n) == LetterRefusal::NotHeroic);
        n = c;
        n.wave2Bound = false;
        CHECK(CheckLetter(n) == LetterRefusal::NotBound);
        n = c;
        n.distance = 31.f;
        CHECK(CheckLetter(n) == LetterRefusal::TooFar);
        n = c;
        n.inSight = false;
        CHECK(CheckLetter(n) == LetterRefusal::TooFar);
        n = c;
        n.inCombat = true;
        CHECK(CheckLetter(n) == LetterRefusal::Fighting);
        n = c;
        n.balnazzarState = fighting;
        CHECK(CheckLetter(n) == LetterRefusal::Fighting);
        n = c;
        n.balnazzarState = done;
        n.dathrohanHere = false;
        CHECK(CheckLetter(n) == LetterRefusal::Done);
        n = c;
        n.dathrohanHere = false;
        CHECK(CheckLetter(n) == LetterRefusal::NoDathrohan);
        // The instance takes the flag in the same cases (heroic, wave 2 bound, Balnazzar neither fighting nor dead).
        CHECK(GrandLieChangeAllowed(1, true, true, DungeonKit::State::NotStarted));
        CHECK(!GrandLieChangeAllowed(1, true, true, fighting));
        CHECK(!GrandLieChangeAllowed(1, false, true, DungeonKit::State::NotStarted));
        CHECK(LetterRefusalText(LetterRefusal::TooFar)[0] != '\0');
    }

    // ---- Numbers (ST HM rows) ---------------------------------------------------------------------------------------
    CHECK(kTwinPct == 50.f && kMarkSplitPct == 100.f && kSwarmTickPct == 10.f);
    CHECK(kConeCount == 2 && kConeTargetPct == 25.f && kConeOthersPct == 50.f && kConeEveryMs == 20000);
    CHECK(kInfernalHealth == 25000 && kInfernoEveryMs == 30000 && kVampiricPct == 3.f);
    CHECK(kSwarmFirstMs == 15000 && kSwarmEveryMs == 20000 && kSwarmLifeMs == 30000 && kSwarmSpeed == 3.f);
    CHECK(kRingRadius == 10.f && kMarkStackRadius == 6.f && kMarkSpreadRadius == 7.f);

    return Report("strat_grand_lie_test");
}
