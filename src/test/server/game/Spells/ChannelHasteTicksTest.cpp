/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "IntegrationTestFixture.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfoTestHelper.h"
#include "gtest/gtest.h"
#include <memory>
#include <vector>

#ifndef TEST_F
#define TEST_F(fixture, name) void fixture##_##name()
#endif

/*
 * Channels: stock hasted duration, fixed ticks; DoTs keep the Cata behavior, b84f1011a (gear scaling, user ruling
 * 2026-11-27, .agents/plans/gear-scaling/gear-scaling.CHANNEL-HASTE-REPORT.md).
 *
 * A channel's own aura gets the hasted channel length (Spell::DoSpellHitOnUnit calls CalcHastedChannelDuration, the
 * stock test Spell::handle_immediate hastes the channel with), and AuraEffect::CalculatePeriodic hastes the tick
 * interval with the same test (IsHasteAffectedPeriodic), so the channel keeps its base tick count. A non-channeled
 * periodic aura keeps its unhasted duration and gains ticks (b84f1011a). The full Spell::prepare -> cast pipeline is
 * not run here (no harness for it): the aura is created directly, given the duration DoSpellHitOnUnit gives it
 * (the same CalcHastedChannelDuration call), and driven through Aura::Update and AuraEffect::Update the way
 * Aura::UpdateOwner does, in uneven steps, counting the ticks that fire. merge_guard.py watches the one call site
 * this test cannot reach.
 */

namespace
{
constexpr uint32 TEST_CHANNEL_SPELL_ID = 900301;
constexpr uint32 TEST_DOT_SPELL_ID = 900302;

// Arcane Missiles under Missile Barrage: 2500 ms channel, 500 ms missiles, 5 missiles.
constexpr int32 MISSILES_DURATION_MS = 2500;
constexpr int32 MISSILES_AMPLITUDE_MS = 500;
constexpr int32 MISSILES_TICKS = 5;

class ChannelHasteTicksTest : public IntegrationTestFixture
{
protected:
    std::unique_ptr<SpellInfo> BuildPeriodicSpell(uint32 id, bool channeled, bool hasteAttr, uint32 auraType,
                                                  int32 durationMs, int32 amplitudeMs)
    {
        std::unique_ptr<SpellInfo> info = SpellInfoBuilder()
            .WithId(id)
            .WithAttributesEx(channeled ? SPELL_ATTR1_IS_CHANNELED : 0)
            .WithEffect(0, SPELL_EFFECT_APPLY_AURA, auraType)
            .WithEffectImplicitTargets(0, TARGET_UNIT_CASTER)
            .BuildUnique();

        info->AttributesEx5 = hasteAttr ? SPELL_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC : 0;
        info->Effects[0].Amplitude = amplitudeMs;

        auto entry = std::make_unique<SpellDurationEntry>();
        entry->ID = id;
        entry->Duration[0] = durationMs;
        entry->Duration[1] = 0;
        entry->Duration[2] = durationMs;
        info->DurationEntry = entry.get();
        _durations.push_back(std::move(entry));

        return info;
    }

    TestPlayer* CreateHastedCaster(float castSpeedMod)
    {
        TestPlayer* caster = CreateTestPlayer();
        caster->SetFloatValue(UNIT_MOD_CAST_SPEED, castSpeedMod);
        return caster;
    }

    // Mirrors Spell::DoSpellHitOnUnit for a channel's own aura: the hasted channel length.
    static void ApplyChannelDuration(Aura* aura, Unit* caster, SpellInfo const* info)
    {
        int32 const hasted = CalcHastedChannelDuration(caster, info, aura->GetMaxDuration());
        aura->SetMaxDuration(hasted);
        aura->SetDuration(hasted);
    }

    struct TickRun
    {
        int32 ticks = 0;            // ticks fired up to the update that expired the aura
        int32 expiredAtMs = 0;      // elapsed time at the update that expired the aura (-1: never expired)
        int32 ticksAfterExpiry = 0; // ticks fired by 5 more half-second updates after the aura expired
    };

    // Aura::UpdateOwner minus the target map (nothing is applied, so no tick handler runs): Aura::Update, then
    // AuraEffect::Update, in uneven steps so a tick never lines up with an update.
    static TickRun RunAuraToExpiry(Aura* aura, Unit* caster)
    {
        static constexpr uint32 STEPS_MS[] = { 47, 113, 31, 89 };
        AuraEffect* effect = aura->GetEffect(0);

        TickRun run;
        run.expiredAtMs = -1;
        int32 elapsed = 0;
        for (size_t i = 0; i < 4000 && !aura->IsExpired(); ++i)
        {
            uint32 const diff = STEPS_MS[i % 4];
            aura->Update(diff, caster);
            effect->Update(diff, caster);
            elapsed += int32(diff);
        }

        if (aura->IsExpired())
            run.expiredAtMs = elapsed;
        run.ticks = int32(effect->GetTickNumber());

        for (int i = 0; i < 5; ++i)
        {
            aura->Update(500, caster);
            effect->Update(500, caster);
        }
        run.ticksAfterExpiry = int32(effect->GetTickNumber()) - run.ticks;
        return run;
    }

    std::vector<std::unique_ptr<SpellDurationEntry>> _durations;
};

// The Arcane Missiles case from the investigation: at every haste level the channel fires its base 5 missiles,
// over an aura that expires at the hasted channel length. Before the ruling 1/1.4 haste gave floor(2500 / 357) = 7.
// The aura is driven in uneven steps and the ticks that fire are counted, so it fails if the hasted length and the
// hasted interval stop agreeing (CalcHastedChannelDuration vs CalculatePeriodic): extra ticks, or expiry at the
// unhasted length. The Spell::DoSpellHitOnUnit call that applies the length is not reachable from here.
TEST_F(ChannelHasteTicksTest, ChannelKeepsBaseTickCountUnderHaste)
{
    std::unique_ptr<SpellInfo> missiles = BuildPeriodicSpell(TEST_CHANNEL_SPELL_ID, true, true,
        SPELL_AURA_PERIODIC_DUMMY, MISSILES_DURATION_MS, MISSILES_AMPLITUDE_MS);

    TestPlayer* caster = CreateHastedCaster(1.0f);
    for (float haste : { 1.0f, 1.1f, 1.25f, 1.397f, 1.4f, 1.603f, 2.0f, 2.5f })
    {
        float const castSpeedMod = 1.0f / haste;
        caster->SetFloatValue(UNIT_MOD_CAST_SPEED, castSpeedMod);

        Aura* aura = Aura::TryCreate(missiles.get(), 1, caster, caster);
        ASSERT_NE(aura, nullptr);
        ApplyChannelDuration(aura, caster, missiles.get());

        // Spell::handle_immediate's channel length: the stock ATTR5 branch (float math; the aura's is double, so at
        // most 1 ms apart).
        int32 const channelMs = int32(MISSILES_DURATION_MS * castSpeedMod);
        EXPECT_NEAR(aura->GetMaxDuration(), channelMs, 1) << "haste " << haste;

        AuraEffect const* effect = aura->GetEffect(0);
        ASSERT_NE(effect, nullptr);
        EXPECT_NEAR(effect->GetAmplitude(), int32(MISSILES_AMPLITUDE_MS * castSpeedMod), 1) << "haste " << haste;

        TickRun const run = RunAuraToExpiry(aura, caster);
        EXPECT_EQ(run.ticks, MISSILES_TICKS) << "haste " << haste;
        // Expired within the last update step of the hasted length (the longest step is 113 ms), not at 2500 ms.
        EXPECT_GE(run.expiredAtMs, aura->GetMaxDuration()) << "haste " << haste;
        EXPECT_LT(run.expiredAtMs, aura->GetMaxDuration() + 113) << "haste " << haste;
        EXPECT_EQ(run.ticksAfterExpiry, 0) << "haste " << haste;

        aura->Remove();
    }
}

// A float rounding edge: with the multiply done in float, a cast speed such as 0.779999971 made int32(500 * m) round
// up to a whole number while int32(2500 * m) did not, dropping a tick (1949 / 390 = 4). Both multiplications are in
// double now. Sweeps the whole haste range 1.0-2.5 (and the known bad float) over several duration / interval pairs.
TEST_F(ChannelHasteTicksTest, ChannelTickCountHoldsAcrossFloatHasteSweep)
{
    struct Pair { int32 durationMs; int32 amplitudeMs; };
    static constexpr Pair PAIRS[] = { { 2500, 500 }, { 3000, 1000 }, { 5000, 1000 }, { 15000, 3000 } };

    TestPlayer* caster = CreateHastedCaster(1.0f);
    uint32 id = TEST_CHANNEL_SPELL_ID + 100;
    for (Pair const& pair : PAIRS)
    {
        std::unique_ptr<SpellInfo> channel = BuildPeriodicSpell(id++, true, true, SPELL_AURA_PERIODIC_DUMMY,
            pair.durationMs, pair.amplitudeMs);
        int32 const baseTicks = pair.durationMs / pair.amplitudeMs;

        std::vector<float> castSpeeds = { 0.779999971f };
        for (int step = 0; step <= 750; ++step)
            castSpeeds.push_back(1.0f / (1.0f + 0.002f * float(step)));

        for (float const castSpeedMod : castSpeeds)
        {
            caster->SetFloatValue(UNIT_MOD_CAST_SPEED, castSpeedMod);

            Aura* aura = Aura::TryCreate(channel.get(), 1, caster, caster);
            ASSERT_NE(aura, nullptr);
            ApplyChannelDuration(aura, caster, channel.get());

            AuraEffect const* effect = aura->GetEffect(0);
            ASSERT_NE(effect, nullptr);
            EXPECT_EQ(effect->GetTotalTicks(), baseTicks)
                << pair.durationMs << "/" << pair.amplitudeMs << " cast speed " << castSpeedMod;

            aura->Remove();
        }
    }
}

// b84f1011a kept: the same periodic aura on a non-channeled spell keeps its duration and gains ticks.
TEST_F(ChannelHasteTicksTest, NonChanneledPeriodicStillGainsTicks)
{
    std::unique_ptr<SpellInfo> dot = BuildPeriodicSpell(TEST_DOT_SPELL_ID, false, true,
        SPELL_AURA_PERIODIC_TRIGGER_SPELL, MISSILES_DURATION_MS, MISSILES_AMPLITUDE_MS);

    float const castSpeedMod = 1.0f / 1.4f;
    TestPlayer* caster = CreateHastedCaster(castSpeedMod);
    Aura* aura = Aura::TryCreate(dot.get(), 1, caster, caster);
    ASSERT_NE(aura, nullptr);

    EXPECT_EQ(aura->GetMaxDuration(), MISSILES_DURATION_MS);
    AuraEffect const* effect = aura->GetEffect(0);
    ASSERT_NE(effect, nullptr);
    int32 const amplitude = int32(MISSILES_AMPLITUDE_MS * castSpeedMod); // 357
    EXPECT_EQ(effect->GetAmplitude(), amplitude);
    EXPECT_EQ(effect->GetTotalTicks(), MISSILES_DURATION_MS / amplitude); // 7

    aura->Remove();
}

TEST_F(ChannelHasteTicksTest, HastedChannelDurationFollowsStockHasteTest)
{
    float const castSpeedMod = 1.0f / 1.25f;
    TestPlayer* caster = CreateHastedCaster(castSpeedMod);
    int32 const hasted = int32(3000 * castSpeedMod);

    // Stock: ATTR5 hastes the channel.
    std::unique_ptr<SpellInfo> attr5 = BuildPeriodicSpell(TEST_CHANNEL_SPELL_ID, true, true,
        SPELL_AURA_PERIODIC_TRIGGER_SPELL, 3000, 1000);
    EXPECT_TRUE(IsHasteAffectedPeriodic(caster, attr5.get()));
    EXPECT_EQ(CalcHastedChannelDuration(caster, attr5.get(), 3000), hasted);

    // The fork's baseline DoT/HoT rule (no ATTR5) skips channels: a channel with a DoT/HoT effect is hasted exactly
    // as in stock (neither its interval nor its length), pet and NPC channels (Pin, bandages, Drain Life) included.
    for (uint32 auraType : { SPELL_AURA_PERIODIC_DAMAGE, SPELL_AURA_PERIODIC_LEECH, SPELL_AURA_PERIODIC_HEAL,
                             SPELL_AURA_OBS_MOD_HEALTH, SPELL_AURA_PERIODIC_DAMAGE_PERCENT })
    {
        std::unique_ptr<SpellInfo> dotChannel = BuildPeriodicSpell(TEST_CHANNEL_SPELL_ID, true, false, auraType,
            3000, 1000);
        EXPECT_FALSE(IsHasteAffectedPeriodic(caster, dotChannel.get())) << "aura type " << auraType;
        EXPECT_EQ(CalcHastedChannelDuration(caster, dotChannel.get(), 3000), 3000) << "aura type " << auraType;

        // The same effect on a non-channeled spell keeps b84f1011a: the interval is hasted.
        std::unique_ptr<SpellInfo> dot = BuildPeriodicSpell(TEST_DOT_SPELL_ID, false, false, auraType, 3000, 1000);
        EXPECT_TRUE(IsHasteAffectedPeriodic(caster, dot.get())) << "aura type " << auraType;
    }

    // No ATTR5, no DoT/HoT effect (a trigger-spell channel like Froststorm Breath 201657): unhasted.
    std::unique_ptr<SpellInfo> plain = BuildPeriodicSpell(TEST_CHANNEL_SPELL_ID, true, false,
        SPELL_AURA_PERIODIC_TRIGGER_SPELL, 3000, 1000);
    EXPECT_FALSE(IsHasteAffectedPeriodic(caster, plain.get()));
    EXPECT_EQ(CalcHastedChannelDuration(caster, plain.get(), 3000), 3000);

    // Infinite or empty durations and a missing caster are left alone.
    EXPECT_EQ(CalcHastedChannelDuration(caster, attr5.get(), -1), -1);
    EXPECT_EQ(CalcHastedChannelDuration(caster, attr5.get(), 0), 0);
    EXPECT_FALSE(IsHasteAffectedPeriodic(nullptr, attr5.get()));
    EXPECT_EQ(CalcHastedChannelDuration(nullptr, attr5.get(), 3000), 3000);
}

// A channel's last tick carries no leftover-fraction bonus; a DoT's still does (b84f1011a). 2500 ms / 1000 ms leaves
// 500 ms, worth x1.5 on a DoT's last tick. SetLoadedState's load path puts the tick counter on the last tick.
TEST_F(ChannelHasteTicksTest, ChannelFinalTickHasNoLeftoverBonus)
{
    TestPlayer* caster = CreateHastedCaster(1.0f);
    int32 amounts[MAX_SPELL_EFFECTS] = { 0, 0, 0 };

    std::unique_ptr<SpellInfo> channel = BuildPeriodicSpell(TEST_CHANNEL_SPELL_ID, true, false,
        SPELL_AURA_PERIODIC_TRIGGER_SPELL, 2500, 1000);
    Aura* channelAura = Aura::TryCreate(channel.get(), 1, caster, caster);
    ASSERT_NE(channelAura, nullptr);
    channelAura->SetLoadedState(2500, 2500, 0, 1, 0, amounts);
    AuraEffect const* channelEffect = channelAura->GetEffect(0);
    ASSERT_NE(channelEffect, nullptr);
    ASSERT_EQ(int32(channelEffect->GetTickNumber()), channelEffect->GetTotalTicks());
    EXPECT_FLOAT_EQ(channelEffect->GetFinalTickBonusMultiplier(), 1.0f);
    channelAura->Remove();

    std::unique_ptr<SpellInfo> dot = BuildPeriodicSpell(TEST_DOT_SPELL_ID, false, false,
        SPELL_AURA_PERIODIC_TRIGGER_SPELL, 2500, 1000);
    Aura* dotAura = Aura::TryCreate(dot.get(), 1, caster, caster);
    ASSERT_NE(dotAura, nullptr);
    dotAura->SetLoadedState(2500, 2500, 0, 1, 0, amounts);
    AuraEffect const* dotEffect = dotAura->GetEffect(0);
    ASSERT_NE(dotEffect, nullptr);
    ASSERT_EQ(int32(dotEffect->GetTickNumber()), dotEffect->GetTotalTicks());
    EXPECT_FLOAT_EQ(dotEffect->GetFinalTickBonusMultiplier(), 1.5f);
    dotAura->Remove();
}
}
