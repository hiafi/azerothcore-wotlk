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
 * same math Spell::handle_immediate uses for the channel), and AuraEffect::CalculatePeriodic hastes the tick interval
 * with the same test (IsHasteAffectedPeriodic), so the channel keeps its base tick count. A non-channeled periodic
 * aura keeps its unhasted duration and gains ticks (b84f1011a). The full Spell::prepare -> cast pipeline is not run
 * here (no harness for it); the aura is created directly and given the duration DoSpellHitOnUnit gives it.
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

    std::vector<std::unique_ptr<SpellDurationEntry>> _durations;
};

// The Arcane Missiles case from the investigation: at every haste level the channel fires its base 5 missiles,
// over a channel (and aura) that shrinks with haste. Before the ruling 1/1.4 haste gave floor(2500 / 357) = 7.
TEST_F(ChannelHasteTicksTest, ChannelKeepsBaseTickCountUnderHaste)
{
    std::unique_ptr<SpellInfo> missiles = BuildPeriodicSpell(TEST_CHANNEL_SPELL_ID, true, true,
        SPELL_AURA_PERIODIC_TRIGGER_SPELL, MISSILES_DURATION_MS, MISSILES_AMPLITUDE_MS);

    TestPlayer* caster = CreateHastedCaster(1.0f);
    for (float haste : { 1.0f, 1.1f, 1.25f, 1.397f, 1.4f, 1.603f, 2.0f, 2.5f })
    {
        float const castSpeedMod = 1.0f / haste;
        caster->SetFloatValue(UNIT_MOD_CAST_SPEED, castSpeedMod);

        Aura* aura = Aura::TryCreate(missiles.get(), 1, caster, caster);
        ASSERT_NE(aura, nullptr);

        // Spell::DoSpellHitOnUnit for a channel's own aura.
        int32 const hasted = CalcHastedChannelDuration(caster, missiles.get(), aura->GetMaxDuration());
        aura->SetMaxDuration(hasted);
        aura->SetDuration(hasted);

        // Spell::handle_immediate's channel length: the stock ATTR5 branch.
        int32 const channelMs = int32(MISSILES_DURATION_MS * castSpeedMod);
        EXPECT_EQ(aura->GetMaxDuration(), channelMs) << "haste " << haste;

        AuraEffect const* effect = aura->GetEffect(0);
        ASSERT_NE(effect, nullptr);
        EXPECT_EQ(effect->GetAmplitude(), int32(MISSILES_AMPLITUDE_MS * castSpeedMod)) << "haste " << haste;
        EXPECT_EQ(effect->GetTotalTicks(), MISSILES_TICKS) << "haste " << haste;

        aura->Remove();
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

TEST_F(ChannelHasteTicksTest, HastedChannelDurationFollowsThePeriodicHasteTest)
{
    float const castSpeedMod = 1.0f / 1.25f;
    TestPlayer* caster = CreateHastedCaster(castSpeedMod);
    int32 const hasted = int32(3000 * castSpeedMod);

    // Stock: ATTR5 hastes the channel.
    std::unique_ptr<SpellInfo> attr5 = BuildPeriodicSpell(TEST_CHANNEL_SPELL_ID, true, true,
        SPELL_AURA_PERIODIC_TRIGGER_SPELL, 3000, 1000);
    EXPECT_TRUE(IsHasteAffectedPeriodic(caster, attr5.get()));
    EXPECT_EQ(CalcHastedChannelDuration(caster, attr5.get(), 3000), hasted);

    // Fork baseline DoT/HoT rule (no ATTR5): the interval is hasted, so the channel is hasted with it.
    for (uint32 auraType : { SPELL_AURA_PERIODIC_DAMAGE, SPELL_AURA_PERIODIC_LEECH, SPELL_AURA_PERIODIC_HEAL,
                             SPELL_AURA_OBS_MOD_HEALTH, SPELL_AURA_PERIODIC_DAMAGE_PERCENT })
    {
        std::unique_ptr<SpellInfo> dotChannel = BuildPeriodicSpell(TEST_CHANNEL_SPELL_ID, true, false, auraType,
            3000, 1000);
        EXPECT_TRUE(IsHasteAffectedPeriodic(caster, dotChannel.get())) << "aura type " << auraType;
        EXPECT_EQ(CalcHastedChannelDuration(caster, dotChannel.get(), 3000), hasted) << "aura type " << auraType;
    }

    // No ATTR5, no DoT/HoT effect (a trigger-spell channel like Froststorm Breath 201657): stock, unhasted.
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
