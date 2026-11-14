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
 * hunter-pet-families F0 (.agents/plans/hunter-pet-families/hunter-pet-families.F0.HANDOFF.md s2), F1-F3: the kit
 * table, the command -> display table, the dispatcher's cast flags and the Beast Cleave rule. Only the paths that need
 * no DBC store or spell manager (a known family, a spell without a TRIGGER_SPELL effect).
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
    constexpr uint32 FAMILY_WORM = 42;
    constexpr uint32 FAMILY_BAT = 24;
    constexpr uint32 FAMILY_CHIMAERA = 38;
    constexpr uint32 FAMILY_CORE_HOUND = 45;
    constexpr uint32 FAMILY_SPIRIT_BEAST = 46;
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

TEST(HunterPetKitTest, FerocityKitsSinceF1)
{
    // hunter-pet-families F1: the slot 2 group effect autocasts, slot 3 is manual
    Hunter::PetKit const& carrionBird = Hunter::GetPetKit(FAMILY_CARRION_BIRD);
    EXPECT_EQ(carrionBird.group, HunterData::SPELL_DEMORALIZING_SCREECH_201754);
    EXPECT_EQ(carrionBird.utility, HunterData::SPELL_SCAVENGE);
    EXPECT_EQ(carrionBird.commandI, HunterData::SPELL_REND_FLESH_COMMAND);
    EXPECT_EQ(carrionBird.commandII, HunterData::SPELL_CARRION_FEAST_COMMAND);
    EXPECT_TRUE(carrionBird.flags & Hunter::PET_KIT_GROUP_AUTOCAST);

    // Ancient Hysteria and Eternal Guardian are manual raid cooldowns: no GROUP_AUTOCAST
    EXPECT_EQ(Hunter::GetPetKit(FAMILY_CORE_HOUND).group, HunterData::SPELL_ANCIENT_HYSTERIA);
    EXPECT_FALSE(Hunter::GetPetKit(FAMILY_CORE_HOUND).flags & Hunter::PET_KIT_GROUP_AUTOCAST);
    EXPECT_EQ(Hunter::GetPetKit(FAMILY_SPIRIT_BEAST).group, HunterData::SPELL_ETERNAL_GUARDIAN);
    EXPECT_FALSE(Hunter::GetPetKit(FAMILY_SPIRIT_BEAST).flags & Hunter::PET_KIT_GROUP_AUTOCAST);
    EXPECT_EQ(Hunter::GetCommandDisplaySpell(HunterData::SPELL_TWIN_BITE_COMMAND),
        HunterData::SPELL_TWIN_BITE_DISPLAY);
}

TEST(HunterPetKitTest, CunningKitsSinceF3)
{
    // hunter-pet-families F3: the slot 2 group effect autocasts, slot 3 is manual, the family's own commands
    Hunter::PetKit const& bat = Hunter::GetPetKit(FAMILY_BAT);
    EXPECT_EQ(bat.basic, HunterData::SPELL_CUNNING_SPIT);
    EXPECT_EQ(bat.group, HunterData::SPELL_SCREECH);
    EXPECT_EQ(bat.utility, HunterData::SPELL_SONIC_BLAST_202004);
    EXPECT_EQ(bat.commandI, HunterData::SPELL_SONIC_BITE_COMMAND);
    EXPECT_EQ(bat.commandII, HunterData::SPELL_SHRIEK_COMMAND);
    EXPECT_TRUE(bat.flags & Hunter::PET_KIT_GROUP_AUTOCAST);

    // Chimaera's Twin Bite has its own display (not the Core Hound's), Froststorm Breath's tick is a helper
    Hunter::PetKit const& chimaera = Hunter::GetPetKit(FAMILY_CHIMAERA);
    EXPECT_EQ(chimaera.commandI, HunterData::SPELL_TWIN_BITE_COMMAND_201656);
    EXPECT_EQ(Hunter::GetCommandDisplaySpell(HunterData::SPELL_TWIN_BITE_COMMAND_201656),
        HunterData::SPELL_TWIN_BITE_DISPLAY_202159);
    EXPECT_FALSE(Hunter::IsSlottedCommand(HunterData::SPELL_FROSTSTORM_BREATH_TICK));
    EXPECT_FALSE(Hunter::IsSlottedCommand(HunterData::SPELL_TWIN_BITE_SECOND_BITE_201670));
}

TEST(HunterPetKitTest, NoKitNamesARetiredPlaceholder)
{
    // hunter-pet-families F3: Dash, Last Stand and Bullheaded left every kit; every family has its own commands
    for (uint32 family : { 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 9u, 11u, 12u, 20u, 21u, 24u, 25u, 26u, 27u, 30u, 31u, 32u,
             33u, 34u, 35u, 37u, 38u, 39u, 41u, 42u, 43u, 44u, 45u, 46u })
    {
        Hunter::PetKit const& kit = Hunter::GetPetKit(family);
        for (uint32 spellId : { kit.group, kit.utility })
        {
            EXPECT_NE(spellId, HunterData::SPELL_DASH) << family;
            EXPECT_NE(spellId, HunterData::SPELL_LAST_STAND) << family;
            EXPECT_NE(spellId, HunterData::SPELL_BULLHEADED) << family;
        }

        for (uint32 command : { kit.commandI, kit.commandII })
        {
            EXPECT_NE(command, HunterData::SPELL_FEINT_STRIKE_COMMAND) << family;
            EXPECT_NE(command, HunterData::SPELL_AMBUSH_COMMAND) << family;
            EXPECT_NE(command, HunterData::SPELL_SAVAGE_STRIKES_COMMAND) << family;
            EXPECT_NE(command, HunterData::SPELL_SAVAGE_POUNCE_COMMAND) << family;
            EXPECT_NE(command, HunterData::SPELL_THRASH_COMMAND) << family;
            EXPECT_NE(command, HunterData::SPELL_CRUSHING_BLOW_COMMAND) << family;
        }
    }
}

TEST(HunterPetKitTest, TenacityKitsSinceF2)
{
    // hunter-pet-families F2: the slot 2 group effect autocasts, slot 3 is manual
    Hunter::PetKit const& boar = Hunter::GetPetKit(FAMILY_BOAR);
    EXPECT_EQ(boar.group, HunterData::SPELL_WAR_GRUNT);
    EXPECT_EQ(boar.utility, HunterData::SPELL_BOAR_CHARGE);
    EXPECT_EQ(boar.commandI, HunterData::SPELL_GORE_COMMAND);
    EXPECT_EQ(boar.commandII, HunterData::SPELL_TUSK_SWEEP_COMMAND);
    EXPECT_TRUE(boar.flags & Hunter::PET_KIT_GROUP_AUTOCAST);

    // Earthen Bulwark is a manual raid cooldown (ruling 20): no GROUP_AUTOCAST
    EXPECT_EQ(Hunter::GetPetKit(FAMILY_WORM).group, HunterData::SPELL_EARTHEN_BULWARK);
    EXPECT_FALSE(Hunter::GetPetKit(FAMILY_WORM).flags & Hunter::PET_KIT_GROUP_AUTOCAST);
    EXPECT_EQ(Hunter::GetCommandDisplaySpell(HunterData::SPELL_DEATH_ROLL_COMMAND),
        HunterData::SPELL_DEATH_ROLL_DISPLAY);

    // The command helpers are in no kit slot
    EXPECT_EQ(Hunter::GetCommandDisplaySpell(HunterData::SPELL_BURROW_ATTACK_PULSE), 0u);
    EXPECT_FALSE(Hunter::IsSlottedCommand(HunterData::SPELL_BURROW_ATTACK_PULSE));
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

    // hunter-pet-families F1: a multi-hit strike is a helper too
    auto strike = SpellInfoBuilder()
        .WithId(HunterData::SPELL_CACKLING_FRENZY_STRIKE)
        .WithSpellFamilyName(SPELLFAMILY_HUNTER)
        .WithSpellFamilyFlags(0, 0, FAMILY_FLAG2_COMMANDED_PET_SPELL)
        .WithEffect(EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE)
        .WithEffectImplicitTargets(EFFECT_0, TARGET_UNIT_TARGET_ENEMY)
        .BuildUnique();
    EXPECT_TRUE(Hunter::IsBeastCleaveExcluded(strike.get()));

    auto copy = SpellInfoBuilder().WithId(HunterData::SPELL_BEAST_CLEAVE_STRIKE).BuildUnique();
    EXPECT_TRUE(Hunter::IsBeastCleaveExcluded(copy.get()));
    EXPECT_FALSE(Hunter::IsBeastCleaveExcluded(nullptr));
}
