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

/*
 * hunter-pet-families F0 (.agents/plans/hunter-pet-families/hunter-pet-families.F0.HANDOFF.md s2): the kit table, the
 * command -> display table, the dispatcher's cast flags and the Beast Cleave rule. Only the paths that need no DBC
 * store or spell manager (a known family, a spell without a TRIGGER_SPELL effect).
 */

#include "HunterMechanics.h"
#include "SpellInfoTestHelper.h"
#include "gtest/gtest.h"

namespace
{
    constexpr uint32 FAMILY_WOLF = 1;
    constexpr uint32 FAMILY_SPIDER = 3;
    constexpr uint32 FAMILY_BOAR = 5;
    constexpr uint32 FAMILY_CARRION_BIRD = 7;
    constexpr uint32 FAMILY_FLAG2_COMMANDED_PET_SPELL = 0x400000;   // _masks.py COMMANDED_PET_SPELL, d2 b22
}

TEST(HunterPetKitTest, FinishedKitsCarryTheirSlotSpellsAndAutocastTheGroupEffect)
{
    Hunter::PetKit const& wolf = Hunter::GetPetKit(FAMILY_WOLF);
    EXPECT_EQ(wolf.basic, HunterData::SPELL_BITE);
    EXPECT_EQ(wolf.group, HunterData::SPELL_FURIOUS_HOWL);
    EXPECT_EQ(wolf.utility, HunterData::SPELL_LICK_YOUR_WOUNDS_201983);
    EXPECT_EQ(wolf.commandI, HunterData::SPELL_LUNGE_COMMAND);
    EXPECT_EQ(wolf.commandII, HunterData::SPELL_RIP_THROAT_COMMAND);
    EXPECT_TRUE(wolf.flags & Hunter::PET_KIT_GROUP_AUTOCAST);

    // Web Pull moved from slot 2 to slot 3; Sticky Webbing is the Spider's group effect
    Hunter::PetKit const& spider = Hunter::GetPetKit(FAMILY_SPIDER);
    EXPECT_EQ(spider.group, HunterData::SPELL_STICKY_WEBBING);
    EXPECT_EQ(spider.utility, HunterData::SPELL_WEB_PULL);
    EXPECT_TRUE(spider.flags & Hunter::PET_KIT_GROUP_AUTOCAST);
}

TEST(HunterPetKitTest, PlaceholderFamiliesKeepTheirButtonsWithoutCower)
{
    // Ferocity: Dash in slot 2, nothing in slot 3 (Cower left every kit); type-default commands; manual
    Hunter::PetKit const& carrionBird = Hunter::GetPetKit(FAMILY_CARRION_BIRD);
    EXPECT_EQ(carrionBird.group, HunterData::SPELL_DASH);
    EXPECT_EQ(carrionBird.utility, 0u);
    EXPECT_EQ(carrionBird.commandI, HunterData::SPELL_SAVAGE_STRIKES_COMMAND);
    EXPECT_EQ(carrionBird.flags, 0);

    // Tenacity: Last Stand in slot 2, Dash (formerly slot 4) in slot 3
    Hunter::PetKit const& boar = Hunter::GetPetKit(FAMILY_BOAR);
    EXPECT_EQ(boar.group, HunterData::SPELL_LAST_STAND);
    EXPECT_EQ(boar.utility, HunterData::SPELL_DASH);
    EXPECT_EQ(boar.commandII, HunterData::SPELL_CRUSHING_BLOW_COMMAND);
    EXPECT_EQ(boar.flags, 0);
}

TEST(HunterPetKitTest, CommandDisplayTableReplacesTheOffset)
{
    EXPECT_EQ(Hunter::GetCommandDisplaySpell(HunterData::SPELL_LUNGE_COMMAND), HunterData::SPELL_LUNGE_DISPLAY);
    EXPECT_EQ(Hunter::GetCommandDisplaySpell(HunterData::SPELL_AMBUSH_COMMAND), HunterData::SPELL_AMBUSH_DISPLAY);
    EXPECT_TRUE(Hunter::IsSlottedCommand(HunterData::SPELL_SAVAGE_STRIKES_COMMAND));   // type defaults stay listed

    // Venomous Cloud's splash is a helper, in no kit slot
    EXPECT_EQ(Hunter::GetCommandDisplaySpell(HunterData::SPELL_VENOMOUS_CLOUD_SPLASH), 0u);
    EXPECT_FALSE(Hunter::IsSlottedCommand(HunterData::SPELL_VENOMOUS_CLOUD_SPLASH));
    EXPECT_FALSE(Hunter::IsSlottedCommand(0));
}

TEST(HunterPetKitTest, InstantCommandsCastWithTheFullTriggeredMask)
{
    auto instant = SpellInfoBuilder()
        .WithEffect(EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE)
        .WithEffectImplicitTargets(EFFECT_0, TARGET_UNIT_TARGET_ENEMY)
        .BuildUnique();

    EXPECT_EQ(Hunter::GetCommandCastFlags(instant.get()), TRIGGERED_FULL_MASK);
    EXPECT_EQ(Hunter::GetCommandCastFlags(nullptr), TRIGGERED_FULL_MASK);
}

TEST(HunterPetKitTest, ChannelCommandsKeepFacingTheirTarget)
{
    for (uint32 channelAttribute : { uint32(SPELL_ATTR1_IS_CHANNELED), uint32(SPELL_ATTR1_IS_SELF_CHANNELED) })
    {
        auto channel = SpellInfoBuilder()
            .WithAttributesEx(channelAttribute)
            .WithEffect(EFFECT_0, SPELL_EFFECT_APPLY_AURA, SPELL_AURA_PERIODIC_DAMAGE)
            .WithEffectImplicitTargets(EFFECT_0, TARGET_UNIT_TARGET_ENEMY)
            .BuildUnique();

        TriggerCastFlags const flags = Hunter::GetCommandCastFlags(channel.get());
        EXPECT_FALSE(flags & TRIGGERED_IGNORE_SET_FACING);
        EXPECT_EQ(uint32(flags) | uint32(TRIGGERED_IGNORE_SET_FACING), uint32(TRIGGERED_FULL_MASK));
    }
}

TEST(HunterPetKitTest, BeastCleaveSkipsCommandHelpersButNotSlottedCommands)
{
    auto helper = SpellInfoBuilder()
        .WithId(HunterData::SPELL_VENOMOUS_CLOUD_SPLASH)
        .WithSpellFamilyName(SPELLFAMILY_HUNTER)
        .WithSpellFamilyFlags(0, 0, FAMILY_FLAG2_COMMANDED_PET_SPELL)
        .BuildUnique();
    EXPECT_TRUE(Hunter::IsBeastCleaveExcluded(helper.get()));

    auto command = SpellInfoBuilder()
        .WithId(HunterData::SPELL_RIP_THROAT_COMMAND)
        .WithSpellFamilyName(SPELLFAMILY_HUNTER)
        .WithSpellFamilyFlags(0, 0, FAMILY_FLAG2_COMMANDED_PET_SPELL)
        .WithEffect(EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE)
        .WithEffectImplicitTargets(EFFECT_0, TARGET_UNIT_TARGET_ENEMY)
        .BuildUnique();
    EXPECT_FALSE(Hunter::IsBeastCleaveExcluded(command.get()));

    auto copy = SpellInfoBuilder().WithId(HunterData::SPELL_BEAST_CLEAVE_STRIKE).BuildUnique();
    EXPECT_TRUE(Hunter::IsBeastCleaveExcluded(copy.get()));
    EXPECT_FALSE(Hunter::IsBeastCleaveExcluded(nullptr));
}
