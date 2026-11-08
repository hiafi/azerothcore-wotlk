// Host tests for Commander Springvale (WP-S4): SpringvaleLogic.h. Handoff section 5: the Oath's 30 s cap (normal),
// Wrath of God's kill timing (heroic), the third guardsman's shatter, the Hammer's single ricochet, plus the spell
// slice, the kill order, the gates and the picks.
#include "SpringvaleLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <set>

using namespace ShadowfangKeepRework;
using namespace Springvale;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Springvale::kSlice.first));
        CHECK(kSpellsReservation.Contains(Springvale::kSlice.last));
        CHECK(Springvale::kSlice.first <= Springvale::kSlice.last);
        CHECK(SpringvaleArena().Contains(kSpringvaleSpawn.XY(), kSpringvaleSpawn.z));
        for (Point3 const& p : kGuardsmanRisePoints)
            CHECK(SpringvaleArena().Contains(p.XY(), p.z));
    }

    void TestSpellIds()
    {
        std::set<std::uint32_t> ids;
        for (std::uint32_t id : { SPELL_SV_HAMMER, SPELL_SV_HAMMER_MARKED, SPELL_SV_HAMMER_STUN, SPELL_SV_RICOCHET,
            SPELL_SV_RICOCHET_MARKED, SPELL_SV_CONSECRATION, SPELL_SV_CONSECRATION_GROUND,
            SPELL_SV_CONSECRATION_GROUND_H, SPELL_SV_HOLY_LIGHT, SPELL_SV_SEARING_LIGHT, SPELL_SV_UNBREAKABLE_OATH,
            SPELL_SV_CRACKED_OATH, SPELL_SV_OATHBROKEN, SPELL_SV_WRATH_OF_GOD, SPELL_SV_WRATH_OF_GOD_KILL,
            SPELL_SV_GUARDSMAN_RISE })
        {
            CHECK(Springvale::kSlice.Contains(id));
            ids.insert(id);
        }
        CHECK(ids.size() == 16);
    }

    // SK Boss data: Light, then Hammer, then Altar, then Springvale (priority 0); one entry per guardsman, distinct
    // rise points, the reserved entries.
    void TestKillOrder()
    {
        CHECK(kGuardsmen[0].kind == Guardsman::Light);
        CHECK(kGuardsmen[1].kind == Guardsman::Hammer);
        CHECK(kGuardsmen[2].kind == Guardsman::Altar);
        CHECK(kGuardsmen[0].killPriority > kGuardsmen[1].killPriority);
        CHECK(kGuardsmen[1].killPriority > kGuardsmen[2].killPriority);
        CHECK(kGuardsmen[2].killPriority > 0);
        std::set<std::size_t> points;
        for (GuardsmanInfo const& g : kGuardsmen)
        {
            CHECK(kCreaturesReservation.Contains(g.entry));
            CHECK(g.risePoint < kGuardsmanRisePoints.size());
            points.insert(g.risePoint);
            CHECK(GuardsmanOf(g.entry).has_value());
            CHECK(GuardsmanOf(g.entry)->kind == g.kind);
        }
        CHECK(points.size() == kGuardsmanCount);
        CHECK(GuardsmanOf(NPC_SFK_GUARDSMAN_LIGHT)->kind == Guardsman::Light);
        CHECK(!GuardsmanOf(NPC_SPRINGVALE).has_value());
    }

    void TestNumbers()
    {
        CHECK(kHammerOthersPct(false) == 25.f && kHammerOthersPct(true) == 25.f);
        CHECK(kHammerMarkedPct(false) == 10.f && kHammerMarkedPct(true) == 10.f);
        CHECK(kConsecrationPct(false) == 5.f && kConsecrationPct(true) == 5.f);
        CHECK(kSearingLightPct(true) == 15.f);
        CHECK(kConsecrationDuration(false) == Ms(10000));
        CHECK(kConsecrationDuration(true) == Ms(40000));
        CHECK(kOathDamageTakenPct == -90.f);
        CHECK(kOathbrokenDamageTakenPct == 25.f);
        // Heroic floor during the Oath (SK): his last two pools plus the Altar's two in 30 s.
        CHECK(kAltarConsecrationFirst + kAltarConsecrationEvery < kWrathOfGodCast - kGuardsmanRise);
        CHECK(kAltarConsecrationFirst + 2 * kAltarConsecrationEvery >= kWrathOfGodCast - kGuardsmanRise);
        // One normal pool at a time: 10 s on the floor, one every 20 s.
        CHECK(kConsecrationDuration(false) < kConsecrationEvery);
        // The stun stays inside the 2 s rule.
        CHECK(kHammerStun <= Ms(2000));
    }

    void TestGates()
    {
        CHECK(OathTriggers(30.f, false));
        CHECK(OathTriggers(12.f, false));
        CHECK(!OathTriggers(30.5f, false));
        CHECK(!OathTriggers(10.f, true));

        CHECK(BossHammerAllowed(false, false));
        CHECK(BossHammerAllowed(true, false));
        CHECK(BossHammerAllowed(false, true));      // normal: he keeps throwing Hammers during the Oath
        CHECK(!BossHammerAllowed(true, true));      // heroic: only Wrath of God
        CHECK(BossConsecrationAllowed(false));
        CHECK(!BossConsecrationAllowed(true));
        CHECK(BossHolyLightAllowed(59.f, false));
        CHECK(!BossHolyLightAllowed(60.f, false));
        CHECK(!BossHolyLightAllowed(20.f, true));
        CHECK(BossMelees(false));
        CHECK(!BossMelees(true));
    }

    // Handoff section 5: the Hammer ricochets once, never twice; only on heroic and only off a Consecration.
    void TestRicochet()
    {
        CHECK(Ricochets(true, false, true));
        CHECK(!Ricochets(true, true, true));        // a bounced hammer never bounces again
        CHECK(!Ricochets(true, false, false));
        CHECK(!Ricochets(false, false, true));

        // A chain where every landing is in a pool: the first bounces, the bounce does not.
        bool bounced = false;
        int bounces = 0;
        for (int landing = 0; landing < 4; ++landing)
        {
            if (!Ricochets(true, bounced, true))
                break;
            ++bounces;
            bounced = true;
        }
        CHECK(bounces == 1);
    }

    void TestNearestOther()
    {
        std::vector<PlayerSpot> players{
            { 1, { 0.f, 0.f }, true },      // the marked player
            { 2, { 5.f, 0.f }, true },      // the tank (included)
            { 3, { 2.f, 0.f }, false },     // dead
            { 4, { 9.f, 0.f }, true },
        };
        std::optional<std::size_t> pick = NearestOther(players, 1, { 0.f, 0.f });
        CHECK(pick && players[*pick].id == 2);
        players[1].alive = false;
        pick = NearestOther(players, 1, { 0.f, 0.f });
        CHECK(pick && players[*pick].id == 4);
        CHECK(!NearestOther({ { 1, { 0.f, 0.f }, true } }, 1, { 0.f, 0.f }).has_value());
        CHECK(!NearestOther({}, 1, { 0.f, 0.f }).has_value());
    }

    void TestHolyLightTarget()
    {
        std::vector<HealCandidate> c{
            { 10, 25.f, true },     // Springvale
            { 11, 100.f, true },    // an unhurt guardsman
            { 12, 20.f, false },    // a dead one
            { 13, 60.f, true },
        };
        std::optional<std::size_t> pick = PickHolyLightTarget(c);
        CHECK(pick && c[*pick].id == 10);
        c[3].healthPct = 15.f;
        pick = PickHolyLightTarget(c);
        CHECK(pick && c[*pick].id == 13);
        CHECK(!PickHolyLightTarget({ { 1, 100.f, true }, { 2, 50.f, false } }).has_value());
    }

    void TestLaunchDelay()
    {
        CHECK(HammerLaunchDelay(Ms(3000), 20.f, 20.f) == Ms(2000));
        CHECK(HammerLaunchDelay(Ms(3000), 0.f, 20.f) == Ms(3000));
        CHECK(HammerLaunchDelay(Ms(2000), 60.f, 20.f) == Ms(0));    // too far: thrown at once
        CHECK(HammerLaunchDelay(Ms(3000), -1.f, 20.f) == Ms(3000));
        CHECK(HammerLaunchDelay(Ms(3000), 10.f, 0.f) == Ms(3000));
    }

    void TestPoolLedger()
    {
        PoolLedger pools;
        pools.Add(0, 5000);         // a refused registration is never stored
        CHECK(pools.Size() == 0);
        pools.Add(7, 10000);
        pools.Add(8, 40000);
        std::vector<std::uint32_t> live = pools.Live(9999);
        CHECK(live.size() == 2);
        live = pools.Live(10000);
        CHECK(live.size() == 1 && live[0] == 8);
        CHECK(pools.Live(40000).empty());
        pools.Add(9, 1);
        pools.Clear();
        CHECK(pools.Size() == 0);
    }

    // Handoff section 5: the Oath's 30 s cap on normal.
    void TestOathCapNormal()
    {
        OathTimeline oath;
        CHECK(!oath.Used());
        CHECK(!oath.Active());
        oath.Start(false);
        CHECK(oath.Used() && oath.Active() && !oath.Heroic());
        for (int i = 0; i < 299; ++i)
        {
            OathStep const step = oath.Advance(Ms(100));
            CHECK(!step.prayerEmote);
            CHECK(step.end == OathEnd::None);
        }
        CHECK(oath.Left() == Ms(100));
        CHECK(oath.Advance(Ms(100)).end == OathEnd::CapExpired);
        CHECK(!oath.Active());
        CHECK(oath.Elapsed() == kOathCap);
        // After the cap the remaining guardsmen fight on: their deaths change nothing.
        CHECK(oath.GuardsmanDied() == OathEnd::None);
        CHECK(oath.Advance(Ms(5000)).end == OathEnd::None);
        CHECK(oath.Used());
    }

    // Handoff section 5: Wrath of God kills at 30 s on heroic, the emote at 10 s left, once.
    void TestWrathTimingHeroic()
    {
        OathTimeline oath;
        oath.Start(true);
        int emotes = 0;
        OathEnd end = OathEnd::None;
        Ms at{ 0 };
        Ms emoteAt{ 0 };
        while (end == OathEnd::None && at < Ms(60000))
        {
            OathStep const step = oath.Advance(Ms(50));
            at += Ms(50);
            if (step.prayerEmote)
            {
                ++emotes;
                emoteAt = at;
            }
            end = step.end;
        }
        CHECK(end == OathEnd::WrathLanded);
        CHECK(at == kWrathOfGodCast);
        CHECK(emotes == 1);
        CHECK(emoteAt == kWrathOfGodCast - kWrathOfGodEmoteLeft);
        CHECK(!oath.Active());
    }

    // The third guardsman shatters it (Oathbroken; on heroic Wrath of God never lands); two do not.
    void TestShatter()
    {
        for (bool heroic : { false, true })
        {
            OathTimeline oath;
            oath.Start(heroic);
            oath.Advance(Ms(10000));
            CHECK(oath.GuardsmanDied() == OathEnd::None);
            CHECK(oath.Cracks() == 1);
            CHECK(oath.GuardsmanDied() == OathEnd::None);
            CHECK(oath.Cracks() == 2);
            CHECK(oath.Active());
            oath.Advance(Ms(10000));
            CHECK(oath.GuardsmanDied() == OathEnd::Shattered);
            CHECK(!oath.Active());
            CHECK(oath.Cracks() == 3);
            // Nothing lands later: the clock stops with the shield.
            CHECK(oath.Advance(Ms(30000)).end == OathEnd::None);
            CHECK(oath.GuardsmanDied() == OathEnd::None);
        }

        // A kill on the last tick before the cast ends still saves the group; at the end it is too late.
        OathTimeline late;
        late.Start(true);
        late.GuardsmanDied();
        late.GuardsmanDied();
        CHECK(late.Advance(kWrathOfGodCast - Ms(1)).end == OathEnd::None);
        CHECK(late.GuardsmanDied() == OathEnd::Shattered);

        OathTimeline tooLate;
        tooLate.Start(true);
        tooLate.GuardsmanDied();
        tooLate.GuardsmanDied();
        CHECK(tooLate.Advance(kWrathOfGodCast).end == OathEnd::WrathLanded);
        CHECK(tooLate.GuardsmanDied() == OathEnd::None);

        // Reset clears the once-only flag (a wipe).
        tooLate.Reset();
        CHECK(!tooLate.Used());
        CHECK(OathTriggers(25.f, tooLate.Used()));
    }

    // SK's heroic DPS check (approved): 3 x 15k guardsmen inside 28 s is under half of the full group's 3,700 DPS.
    void TestHeroicWindow()
    {
        Ms const window = kWrathOfGodCast - kGuardsmanRise;
        CHECK(window == Ms(28000));
        float const neededDps = 45000.f / 28.f;
        CHECK(neededDps < 3700.f * 0.45f);
    }
}

int main()
{
    TestSliceAndArena();
    TestSpellIds();
    TestKillOrder();
    TestNumbers();
    TestGates();
    TestRicochet();
    TestNearestOther();
    TestHolyLightTarget();
    TestLaunchDelay();
    TestPoolLedger();
    TestOathCapNormal();
    TestWrathTimingHeroic();
    TestShatter();
    TestHeroicWindow();
    return Report("sfk_springvale_test");
}
