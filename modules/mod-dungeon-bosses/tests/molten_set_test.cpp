// Host tests for MoltenSetLogic.h (dungeon sets, the Molten set bonuses): the ids sit in the `molten_set` reservation,
// ten per set, with the 3 piece, 5 piece and Heat at fixed offsets; the Heat counts; what each set's 3 piece counts
// (HeatGain: 1, 2 on a crit, Darkmantle's combo points); a gain that reaches the count erupts and resets (StepHeat);
// the cooldown hooks' Heat and the Cooldown Haste rule's list; Mending Flame; the most injured ally order.
#include "../src/DungeonSets/HauntedSetLogic.h"
#include "../src/DungeonSets/MoltenSetLogic.h"
#include "check.h"
#include <cstdint>
#include <set>

using namespace MoltenSet;

namespace
{
    std::uint32_t constexpr kAllSpells[] = {
        SPELL_STOKED_FLAME, SPELL_FLARE_UP, SPELL_STOKED_FLAME_HEAT, SPELL_STOKED_FLAME_ERUPTION,
        SPELL_CAUTERIZE, SPELL_MENDING_FLAME, SPELL_CAUTERIZE_HEAT, SPELL_CAUTERIZE_HEAL,
        SPELL_EMBER_BLOOM, SPELL_FANNED_EMBERS, SPELL_EMBER_BLOOM_HEAT, SPELL_EMBER_BLOOM_READY,
        SPELL_FANNED_EMBERS_BUFF,
        SPELL_MOLTEN_THUNDER, SPELL_THUNDERHEAD, SPELL_MOLTEN_THUNDER_HEAT, SPELL_MOLTEN_THUNDER_DAMAGE,
        SPELL_MOLTEN_THUNDER_HEAL,
        SPELL_HALLOWED_FLAME, SPELL_TENDED_FLAME, SPELL_HALLOWED_FLAME_HEAT, SPELL_HALLOWED_FLAME_HOT,
        SPELL_HALLOWED_FLAME_DOT, SPELL_TENDED_FLAME_MANA,
        SPELL_MOLTEN_EDGE, SPELL_STOKE_THE_FORGE, SPELL_MOLTEN_EDGE_HEAT, SPELL_MOLTEN_EDGE_SEAR,
        SPELL_OBSIDIAN_SHARD, SPELL_BURNING_SHARDS, SPELL_OBSIDIAN_SHARD_HEAT, SPELL_OBSIDIAN_SHARD_MELEE,
        SPELL_OBSIDIAN_SHARD_RANGED, SPELL_BURNING_SHARDS_MELEE, SPELL_BURNING_SHARDS_RANGED,
        SPELL_SLAG_BURST, SPELL_REKINDLE, SPELL_SLAG_BURST_HEAT, SPELL_SLAG_BURST_ERUPTION, SPELL_REKINDLE_BUFF,
        SPELL_SCORCHING_HIDE, SPELL_TEMPERED_HIDE, SPELL_SCORCHING_HIDE_HEAT, SPELL_SCORCHING_HIDE_ERUPTION,
        SPELL_TEMPERED_HIDE_BUFF,
        SPELL_MOLTEN_PLATE, SPELL_BANKED_COALS, SPELL_MOLTEN_PLATE_HEAT, SPELL_MOLTEN_PLATE_BUFF,
    };

    // Set k's 3 piece, 5 piece and Heat, in Archetype order.
    std::uint32_t constexpr kThree[] = { SPELL_STOKED_FLAME, SPELL_CAUTERIZE, SPELL_EMBER_BLOOM, SPELL_MOLTEN_THUNDER,
        SPELL_HALLOWED_FLAME, SPELL_MOLTEN_EDGE, SPELL_OBSIDIAN_SHARD, SPELL_SLAG_BURST, SPELL_SCORCHING_HIDE,
        SPELL_MOLTEN_PLATE };
    std::uint32_t constexpr kFive[] = { SPELL_FLARE_UP, SPELL_MENDING_FLAME, SPELL_FANNED_EMBERS, SPELL_THUNDERHEAD,
        SPELL_TENDED_FLAME, SPELL_STOKE_THE_FORGE, SPELL_BURNING_SHARDS, SPELL_REKINDLE, SPELL_TEMPERED_HIDE,
        SPELL_BANKED_COALS };
    std::uint32_t constexpr kHeat[] = { SPELL_STOKED_FLAME_HEAT, SPELL_CAUTERIZE_HEAT, SPELL_EMBER_BLOOM_HEAT,
        SPELL_MOLTEN_THUNDER_HEAT, SPELL_HALLOWED_FLAME_HEAT, SPELL_MOLTEN_EDGE_HEAT, SPELL_OBSIDIAN_SHARD_HEAT,
        SPELL_SLAG_BURST_HEAT, SPELL_SCORCHING_HIDE_HEAT, SPELL_MOLTEN_PLATE_HEAT };

    Archetype constexpr kSets[] = { Archetype::Sorcerers, Archetype::Virtuous, Archetype::Feralheart,
        Archetype::FiveThunders, Archetype::Soulforge, Archetype::Heroism, Archetype::Beastmasters,
        Archetype::Darkmantle, Archetype::Guardians, Archetype::Impenetrable };

    void TestIds()
    {
        std::set<std::uint32_t> seen;
        for (std::uint32_t id : kAllSpells)
        {
            CHECK(kSpellsMoltenSet.Contains(id));
            CHECK(seen.insert(id).second);
            // HauntedSetUnitHooks (Haunting Mark) skips both slices by id, so the two must never overlap: an
            // Obsidian Shard payout must not consume a Haunting Mark, and a Haunted payout is not a Molten one
            CHECK(!HauntedSet::kSpellsHauntedSet.Contains(id));
        }
        CHECK(HauntedSet::kSpellsHauntedSet.last < kSpellsMoltenSet.first);
        CHECK(seen.size() == 49);
        // Clear of the Blackrock Depths item block below it (206830-206899) and the spell block's end (209999).
        CHECK(kSpellsMoltenSet.first == 206900 && kSpellsMoltenSet.last == 206999);
        for (std::uint32_t k = 0; k < kArchetypeCount; ++k)
        {
            Archetype const set = kSets[k];
            CHECK(static_cast<std::uint32_t>(set) == k);
            CHECK(SpellOf(set, kOffsetThreePiece) == kThree[k]);
            CHECK(SpellOf(set, kOffsetFivePiece) == kFive[k]);
            CHECK(HeatSpellOf(set) == kHeat[k]);
            CHECK(ArchetypeOf(kThree[k]) == set && ArchetypeOf(kFive[k]) == set && ArchetypeOf(kHeat[k]) == set);
        }
        for (std::uint32_t id : kAllSpells)
            CHECK(ArchetypeOf(id) != Archetype::Count);
        CHECK(ArchetypeOf(206899) == Archetype::Count);
        CHECK(ArchetypeOf(207000) == Archetype::Count);
        CHECK(ArchetypeOf(0) == Archetype::Count);
    }

    void TestHeatCounts()
    {
        // The doc: Sorcerer's, The Five Thunders, Heroism, Darkmantle, Guardian's, Impenetrable at 10; Virtuous,
        // Feralheart, Soulforge, Beastmaster's at 8.
        CHECK(HeatCountOf(Archetype::Sorcerers) == 10);
        CHECK(HeatCountOf(Archetype::Virtuous) == 8);
        CHECK(HeatCountOf(Archetype::Feralheart) == 8);
        CHECK(HeatCountOf(Archetype::FiveThunders) == 10);
        CHECK(HeatCountOf(Archetype::Soulforge) == 8);
        CHECK(HeatCountOf(Archetype::Heroism) == 10);
        CHECK(HeatCountOf(Archetype::Beastmasters) == 8);
        CHECK(HeatCountOf(Archetype::Darkmantle) == 10);
        CHECK(HeatCountOf(Archetype::Guardians) == 10);
        CHECK(HeatCountOf(Archetype::Impenetrable) == 10);
        CHECK(HeatCountOf(Archetype::Count) == 0);
        CHECK(kCritHeat == 2);
    }

    HeatEvent Cast(bool crit, bool spell, bool melee, bool ranged)
    {
        HeatEvent e;
        e.crit = crit;
        e.spell = spell;
        e.meleeAbility = melee;
        e.rangedAbility = ranged;
        return e;
    }

    void TestHeatGain()
    {
        // Sorcerer's: direct damage spells 1 / 2; periodic damage crits 1; a direct heal or a plain tick nothing.
        HeatEvent bolt = Cast(false, true, false, false);
        bolt.directDamage = bolt.damageOrHeal = true;
        CHECK(HeatGain(Archetype::Sorcerers, bolt) == 1);
        bolt.crit = true;
        CHECK(HeatGain(Archetype::Sorcerers, bolt) == 2);
        HeatEvent tick;
        tick.periodic = tick.periodicDamage = true;
        CHECK(HeatGain(Archetype::Sorcerers, tick) == 0);
        tick.crit = true;
        CHECK(HeatGain(Archetype::Sorcerers, tick) == 1);
        HeatEvent healTick = tick;
        healTick.periodicDamage = false;  // a critical heal tick is not periodic damage
        CHECK(HeatGain(Archetype::Sorcerers, healTick) == 0);
        HeatEvent dotCast = Cast(true, true, false, false);  // a DoT cast: no direct damage
        dotCast.damageOrHeal = true;
        CHECK(HeatGain(Archetype::Sorcerers, dotCast) == 0);

        // Virtuous: direct heals only.
        HeatEvent heal = Cast(false, true, false, false);
        heal.directHeal = heal.damageOrHeal = true;
        CHECK(HeatGain(Archetype::Virtuous, heal) == 1);
        heal.crit = true;
        CHECK(HeatGain(Archetype::Virtuous, heal) == 2);
        CHECK(HeatGain(Archetype::Virtuous, bolt) == 0);
        CHECK(HeatGain(Archetype::Virtuous, dotCast) == 0);

        // Feralheart and The Five Thunders: any damage or healing spell, a DoT or HoT cast included; never a tick, a
        // buff or an ability.
        for (Archetype set : { Archetype::Feralheart, Archetype::FiveThunders })
        {
            CHECK(HeatGain(set, bolt) == 2);
            CHECK(HeatGain(set, heal) == 2);
            CHECK(HeatGain(set, dotCast) == 2);
            CHECK(HeatGain(set, tick) == 0);
            CHECK(HeatGain(set, Cast(false, true, false, false)) == 0);  // a buff
            HeatEvent strike = Cast(false, false, true, false);
            strike.directDamage = strike.damageOrHeal = true;
            CHECK(HeatGain(set, strike) == 0);
        }

        // Soulforge: Holy spells and Holy abilities.
        HeatEvent holyLight = heal;
        holyLight.holy = true;
        CHECK(HeatGain(Archetype::Soulforge, holyLight) == 2);
        CHECK(HeatGain(Archetype::Soulforge, heal) == 0);  // not Holy
        HeatEvent shieldOfRighteousness = Cast(false, false, true, false);
        shieldOfRighteousness.holy = true;
        CHECK(HeatGain(Archetype::Soulforge, shieldOfRighteousness) == 1);
        HeatEvent consecrationTick = tick;
        consecrationTick.holy = true;
        CHECK(HeatGain(Archetype::Soulforge, consecrationTick) == 0);
        // Judgement and Avenger's Shield are ranged class in the 3.3.5 data (REVIEW S5): Holy, so they count.
        HeatEvent judgement = Cast(false, false, false, true);
        judgement.holy = true;
        CHECK(HeatGain(Archetype::Soulforge, judgement) == 1);
        judgement.holy = false;  // a ranged ability that is not Holy (Shoot) does not
        CHECK(HeatGain(Archetype::Soulforge, judgement) == 0);

        // Heroism, Guardian's, Impenetrable and Beastmaster's: melee or ranged abilities (Thunder Clap, Avenger's
        // Shield, Judgement are ranged class: REVIEW S5); never a spell (class magic or none).
        HeatEvent strike = Cast(false, false, true, false);
        HeatEvent shot = Cast(true, false, false, true);
        for (Archetype set : { Archetype::Heroism, Archetype::Guardians, Archetype::Impenetrable })
        {
            CHECK(HeatGain(set, strike) == 1);
            CHECK(HeatGain(set, shot) == 2);
            CHECK(HeatGain(set, bolt) == 0);
        }
        CHECK(HeatGain(Archetype::Beastmasters, strike) == 1);
        CHECK(HeatGain(Archetype::Beastmasters, shot) == 2);
        CHECK(HeatGain(Archetype::Beastmasters, bolt) == 0);

        // Darkmantle: a finisher gives its combo points, 1 more on a crit; a builder nothing.
        HeatEvent finisher = Cast(false, false, true, false);
        finisher.finisher = true;
        finisher.comboPoints = 5;
        CHECK(HeatGain(Archetype::Darkmantle, finisher) == 5);
        finisher.crit = true;
        CHECK(HeatGain(Archetype::Darkmantle, finisher) == 6);
        finisher.comboPoints = 0;
        CHECK(HeatGain(Archetype::Darkmantle, finisher) == 0);
        CHECK(HeatGain(Archetype::Darkmantle, strike) == 0);
        HeatEvent deadlyThrow = Cast(false, false, false, true);
        deadlyThrow.finisher = true;
        deadlyThrow.comboPoints = 3;
        CHECK(HeatGain(Archetype::Darkmantle, deadlyThrow) == 3);
        HeatEvent ripTick = tick;
        ripTick.finisher = true;
        ripTick.comboPoints = 5;
        CHECK(HeatGain(Archetype::Darkmantle, ripTick) == 0);
        // Slice and Dice and Savage Roar are damage class NONE (REVIEW S4): a finisher still, so its points count.
        HeatEvent sliceAndDice = Cast(false, true, false, false);
        sliceAndDice.finisher = true;
        sliceAndDice.comboPoints = 5;
        CHECK(HeatGain(Archetype::Darkmantle, sliceAndDice) == 5);
        sliceAndDice.comboPoints = 0;
        CHECK(HeatGain(Archetype::Darkmantle, sliceAndDice) == 0);

        CHECK(HeatGain(Archetype::Count, bolt) == 0);
    }

    // Molten Thunder and Hallowed Flame (REVIEW N2): an enemy target takes the damage half, another ally the heal; a
    // heal cast on the wearer (or with no target) heals the wearer; a self-cast that does not heal (Elemental
    // Mastery off Thunderhead, a seal) strikes the wearer's in-combat enemy, the wearer's heal only when there is none.
    void TestPayoutSide()
    {
        CHECK(ChoosePayoutSide(true, false, false, true) == PayoutSide::Enemy);
        CHECK(ChoosePayoutSide(true, false, true, false) == PayoutSide::Enemy);
        CHECK(ChoosePayoutSide(false, true, true, true) == PayoutSide::Ally);
        CHECK(ChoosePayoutSide(false, true, false, true) == PayoutSide::Ally);
        CHECK(ChoosePayoutSide(false, false, true, true) == PayoutSide::Wearer);   // a self-heal
        CHECK(ChoosePayoutSide(false, false, false, true) == PayoutSide::Nearby);  // a self-cast cooldown, in combat
        CHECK(ChoosePayoutSide(false, false, false, false) == PayoutSide::Wearer); // nobody to strike
    }

    void TestStepHeat()
    {
        HeatStep s = StepHeat(0, 1, 10);
        CHECK(s.stacks == 1 && !s.erupts);
        s = StepHeat(8, 1, 10);
        CHECK(s.stacks == 9 && !s.erupts);
        s = StepHeat(9, 1, 10);  // reaches the count: erupts, resets
        CHECK(s.stacks == 0 && s.erupts);
        s = StepHeat(9, 2, 10);  // a crit past the count: the overflow is lost
        CHECK(s.stacks == 0 && s.erupts);
        s = StepHeat(6, 2, 8);
        CHECK(s.stacks == 0 && s.erupts);
        s = StepHeat(5, 2, 8);
        CHECK(s.stacks == 7 && !s.erupts);
        s = StepHeat(0, 10, 10);  // Stoke the Forge / Banked Coals: an eruption from nothing
        CHECK(s.stacks == 0 && s.erupts);
        s = StepHeat(3, 0, 10);  // no gain: nothing changes
        CHECK(s.stacks == 3 && !s.erupts);
        s = StepHeat(3, 5, 0);  // no count: never erupts
        CHECK(s.stacks == 0 && !s.erupts);
        // Ten 1-Heat casts erupt on the tenth, exactly once.
        std::uint32_t heat = 0;
        int eruptions = 0;
        for (int i = 0; i < 10; ++i)
        {
            HeatStep const step = StepHeat(heat, 1, 10);
            heat = step.stacks;
            eruptions += step.erupts ? 1 : 0;
        }
        CHECK(heat == 0 && eruptions == 1);
    }

    void TestCooldownHooks()
    {
        CHECK(CooldownHookHeat(Archetype::Sorcerers) == 10);  // Flare-up: a full eruption
        CHECK(CooldownHookHeat(Archetype::FiveThunders) == 5);
        CHECK(CooldownHookHeat(Archetype::Heroism) == 10);
        CHECK(CooldownHookHeat(Archetype::Impenetrable) == 10);
        for (Archetype set : { Archetype::Virtuous, Archetype::Feralheart, Archetype::Soulforge,
                 Archetype::Beastmasters, Archetype::Darkmantle, Archetype::Guardians })
            CHECK(CooldownHookHeat(set) == 0);
        // Stoke the Forge and Banked Coals erupt their sets outright.
        CHECK(StepHeat(0, CooldownHookHeat(Archetype::Heroism), HeatCountOf(Archetype::Heroism)).erupts);
        CHECK(StepHeat(0, CooldownHookHeat(Archetype::Impenetrable), HeatCountOf(Archetype::Impenetrable)).erupts);
        CHECK(!StepHeat(4, CooldownHookHeat(Archetype::FiveThunders), 10).erupts);
        CHECK(StepHeat(5, CooldownHookHeat(Archetype::FiveThunders), 10).erupts);

        // The hook rule: a base or category cooldown of 30 s or more, the Molten trigger list, never the deny list.
        CHECK(IsCooldownHookSpell(12292, 180000, 0));     // a 3 min cooldown
        CHECK(IsCooldownHookSpell(1, 30000, 0));          // exactly 30 s
        CHECK(!IsCooldownHookSpell(1, 29999, 0));
        CHECK(IsCooldownHookSpell(1, 0, 30000));          // a category cooldown
        CHECK(!IsCooldownHookSpell(1, 6000, 6000));
        CHECK(IsCooldownHookSpell(200333, 10000, 0));     // Starsurge, allow list
        CHECK(IsCooldownHookSpell(204148, 20000, 0));     // Death from Above, allow list
        // gear-scaling GS2: on the Cooldown Haste allow list, deliberately not on the Molten trigger list.
        CHECK(!IsCooldownHookSpell(20473, 0, 6000));      // Holy Shock
        CHECK(!IsCooldownHookSpell(60103, 6000, 0));      // Lava Lash
        CHECK(!IsCooldownHookSpell(21169, 1800000, 0));   // Reincarnation, deny list
        CHECK(!IsCooldownHookSpell(20154, 0, 0));         // a seal, deny list
        CHECK(kCooldownHookMinMs == 30000);
    }

    void TestMendingFlame()
    {
        CHECK(MendingFlamePct(4999, 10000) == 150);
        CHECK(MendingFlamePct(5000, 10000) == 100);  // "below 50%"
        CHECK(MendingFlamePct(10000, 10000) == 100);
        CHECK(MendingFlamePct(1, 10000) == 150);
        CHECK(MendingFlamePct(0, 0) == 100);
        CHECK(ScalePct(1000, 150) == 1500);
        CHECK(ScalePct(0, 150) == 0);
        CHECK(ScalePct(1000, 0) == 0);
        CHECK(ScalePct(0x7FFFFFFF, 200) == 0x7FFFFFFF);
    }

    void TestMostInjured()
    {
        CHECK(MoreInjured(500, 1000, 600, 1000));
        CHECK(!MoreInjured(600, 1000, 500, 1000));
        CHECK(MoreInjured(4000, 10000, 500, 1000));
        CHECK(!MoreInjured(500, 1000, 500, 1000));
    }

    void TestScriptNumbers()
    {
        // The tooltip literals of molten_set_bonuses.py (lib/test_molten_set.py reads them back from this header).
        CHECK(kCauterizeExtraAllies == 3);
        CHECK(kCauterizeRadius == 10.0f);
        CHECK(kMendingFlameHealthPct == 50 && kMendingFlameBonusPct == 50);
        CHECK(kEmberBloomTicks == 2);
        CHECK(kMoltenThunderRadius == 8.0f && kMoltenThunderExtraAllies == 4);
        CHECK(kThunderheadHeat == 5 && kStokeTheForgeHeat == 10 && kBankedCoalsHeat == 10);
        CHECK(kObsidianShardBounceRadius == 10.0f);
        CHECK(kRekindleComboPoints == 1);
    }
}

int main()
{
    TestIds();
    TestHeatCounts();
    TestHeatGain();
    TestPayoutSide();
    TestStepHeat();
    TestCooldownHooks();
    TestMendingFlame();
    TestMostInjured();
    TestScriptNumbers();
    return Report("molten_set_test");
}
