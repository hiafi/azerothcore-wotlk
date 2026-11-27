// Host tests for UldamanHardModeItemsLogic.h (the Uldaman gear stage): the ids sit in the `uldaman_items` reservation
// and clear the item spell copy ranges and the neighbors, the Waking Stone's path, march steps, one trample per enemy
// and knockback rule, the Lightbound Choker's school memory and what counts, the Fragment of the Disks' record, taken
// modifier undo, share and replay split. The generated ItemSpellCopies.h lookup gives each tier's own copies (the
// trample, Two Lights) and leaves the Disk's replay and heal shared.
#include "../src/Uldaman/UldamanHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cstdint>
#include <initializer_list>

using namespace UldamanHardModeItems;

namespace
{
    void TestIds()
    {
        CHECK(kSpellsUldamanItems.first == 214680u);
        CHECK(kSpellsUldamanItems.last == 214719u);
        CHECK(kSpellsUldamanItems.Contains(kSpellsDeclared.first));
        CHECK(kSpellsUldamanItems.Contains(kSpellsDeclared.last));
        std::uint32_t expected = kSpellsDeclared.first;
        for (std::uint32_t id : { SPELL_WAKING_STONE, SPELL_WAKING_STONE_TRAMPLE, SPELL_CHOKER, SPELL_CHOKER_TWO_LIGHTS,
                 SPELL_DISK_RECORDING, SPELL_DISK_REPLAY, SPELL_DISK_REPLAY_HEAL })
        {
            CHECK(id == expected);                          // contiguous, in declaration order
            ++expected;
            CHECK(kSpellsDeclared.Contains(id));
            CHECK(IsItemSpell(id));
            CHECK(!(id >= 205410u && id <= 205599u));       // the item spell copy block
            CHECK(!(id >= 219000u && id <= 219399u));       // ... and its second range
            CHECK(id > 214679u && id < 214720u);            // the Uldaman build reserves from 214720
        }
        CHECK(expected == kSpellsDeclared.last + 1);
        CHECK(kCreaturesUldamanItems.first == 301200u);
        CHECK(kCreaturesUldamanItems.last == 301204u);
        CHECK(kCreaturesUldamanItems.Contains(NPC_WAKING_STONE_EARTHEN));
        CHECK(NPC_WAKING_STONE_EARTHEN > 301199u);          // after the Gnomeregan build's creatures
        for (std::uint32_t id : { 0u, 214679u, 214687u, 214719u, 214240u, 205410u })
            CHECK(!IsItemSpell(id));                        // spare, the neighbors, another item's copy
    }

    // Holds before the write run (no copies yet: every lookup gives the base) and after it (81, 91 and 101 each carry
    // their own).
    void TestCopies()
    {
        CHECK(ItemSpellCopies::Resolve(SPELL_WAKING_STONE, SPELL_WAKING_STONE_TRAMPLE) == SPELL_WAKING_STONE_TRAMPLE);
        CHECK(ItemSpellCopies::Resolve(SPELL_CHOKER, SPELL_CHOKER_TWO_LIGHTS) == SPELL_CHOKER_TWO_LIGHTS);
        CHECK(ItemSpellCopies::Resolve(SPELL_DISK_RECORDING, SPELL_DISK_REPLAY) == SPELL_DISK_REPLAY);
        CHECK(ItemSpellCopies::Resolve(SPELL_DISK_RECORDING, SPELL_DISK_REPLAY_HEAL) == SPELL_DISK_REPLAY_HEAL);
        std::uint32_t stones = 0;
        std::uint32_t chokers = 0;
        std::uint32_t disks = 0;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
        {
            CHECK(copy.base != SPELL_DISK_REPLAY);          // shared: no number
            CHECK(copy.base != SPELL_DISK_REPLAY_HEAL);
            if (kSpellsDeclared.Contains(copy.base))
                CHECK(IsItemSpell(copy.copy));
            if (copy.base == SPELL_WAKING_STONE)
            {
                ++stones;
                std::uint32_t const trample = ItemSpellCopies::Resolve(copy.copy, SPELL_WAKING_STONE_TRAMPLE);
                CHECK(trample != SPELL_WAKING_STONE_TRAMPLE);
                CHECK(ItemSpellCopies::GroupOf(trample) == copy.group);
            }
            if (copy.base == SPELL_CHOKER)
            {
                ++chokers;
                std::uint32_t const lights = ItemSpellCopies::Resolve(copy.copy, SPELL_CHOKER_TWO_LIGHTS);
                CHECK(lights != SPELL_CHOKER_TWO_LIGHTS);
                CHECK(ItemSpellCopies::GroupOf(lights) == copy.group);
            }
            if (copy.base == SPELL_DISK_RECORDING)
            {
                ++disks;
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_DISK_REPLAY) == SPELL_DISK_REPLAY);
            }
        }
        CHECK(stones == 0u || stones == 3u);
        CHECK(chokers == stones);
        CHECK(disks == stones);
    }

    void TestPath()
    {
        PathPoint const a{ 0.0f, 0.0f, 0.0f };
        PathPoint const b{ 2.0f, 0.0f, 0.0f };
        CHECK(MarchPathDistSq(a, b, PathPoint{ 1.0f, 3.0f, 0.0f }) == 9.0f);    // beside the step
        CHECK(MarchPathDistSq(a, b, PathPoint{ -3.0f, 0.0f, 0.0f }) == 9.0f);   // behind its start
        CHECK(MarchPathDistSq(a, b, PathPoint{ 5.0f, 4.0f, 0.0f }) == 25.0f);   // past its end
        CHECK(MarchPathDistSq(a, a, PathPoint{ 3.0f, 4.0f, 0.0f }) == 25.0f);   // a step of no length is a point

        // 3 yd half width, plus the enemy's reach
        CHECK(OnMarchPath(a, b, PathPoint{ 1.0f, 3.0f, 0.0f }, 0.0f, 3.0f));
        CHECK(!OnMarchPath(a, b, PathPoint{ 1.0f, 3.5f, 0.0f }, 0.0f, 3.0f));
        CHECK(OnMarchPath(a, b, PathPoint{ 1.0f, 3.5f, 0.0f }, 1.0f, 3.0f));      // a big enemy's edge is in the path
        CHECK(!OnMarchPath(a, b, PathPoint{ 1.0f, 3.5f, 0.0f }, -1.0f, 3.0f));    // a negative reach counts as none
        // a floor above or below is not trampled
        CHECK(OnMarchPath(a, b, PathPoint{ 1.0f, 0.0f, kPathHeight }, 0.0f, 3.0f));
        CHECK(!OnMarchPath(a, b, PathPoint{ 1.0f, 0.0f, kPathHeight + 0.5f }, 0.0f, 3.0f));
        CHECK(!OnMarchPath(a, b, PathPoint{ 1.0f, 0.0f, -kPathHeight - 0.5f }, 0.0f, 3.0f));

        // a 2 yd step (8 yd/s, 0.25 sec ticks) inside the 3 yd half width: consecutive steps leave no gap
        CHECK(kSearchMargin >= 5.0f);
        CHECK(kEarthenStartDistance > 0.0f && kEarthenStartDistance < 3.0f);
        CHECK(kArrivedYards > 0.0f && kArrivedYards < 2.0f);
    }

    void TestMarch()
    {
        CHECK(StepMarch(true, true, 10.0f) == MarchStep::Walk);
        CHECK(StepMarch(true, true, kArrivedYards) == MarchStep::Arrived);
        CHECK(StepMarch(true, true, 0.0f) == MarchStep::Arrived);
        CHECK(StepMarch(false, true, 10.0f) == MarchStep::Gone);       // the wearer died or left
        CHECK(StepMarch(true, false, 10.0f) == MarchStep::Gone);       // the earthen is gone
        CHECK(StepMarch(false, false, 0.0f) == MarchStep::Gone);
        // the earthen outlives its 4 sec march only by the tail, inside the 2 min cooldown
        CHECK(kEarthenTailMs > 0u && 4000u + kEarthenTailMs < 120000u);

        TrampleList list;
        CHECK(!WasTrampled(list, 7));
        CHECK(MarkTrampled(list, 7));
        CHECK(WasTrampled(list, 7));
        CHECK(!MarkTrampled(list, 7));                                 // once per march
        CHECK(MarkTrampled(list, 8));
        CHECK(!MarkTrampled(list, 0));                                 // no guid
        CHECK(list.count == 2u);
        TrampleList full;
        for (std::uint64_t guid = 1; guid <= kMaxTrampled; ++guid)
            CHECK(MarkTrampled(full, guid));
        CHECK(!MarkTrampled(full, 1000));                              // a full list tramples nobody new
        CHECK(full.count == kMaxTrampled);
    }

    void TestKnockback()
    {
        CHECK(CanKnockBack(KnockbackTarget{}));                        // a player
        KnockbackTarget trash;
        trash.creature = true;
        CHECK(CanKnockBack(trash));
        for (int sign = 0; sign < 5; ++sign)
        {
            KnockbackTarget boss = trash;
            boss.worldBoss = sign == 0;
            boss.dungeonBoss = sign == 1;
            boss.immune = sign == 2;
            boss.bindsInstance = sign == 3;
            boss.bossScript = sign == 4;                               // Olaf, Eric, the build's new bosses
            CHECK(!CanKnockBack(boss));
        }
    }

    void TestChoker()
    {
        CHECK(kOwnCastFlags == 0x15510u);
        CHECK(!(kOwnCastFlags & 0x4u));                                // no melee auto attack
        CHECK(!(kOwnCastFlags & 0x40u));                               // no ranged auto attack
        CHECK(!(kOwnCastFlags & 0x40000u));                            // no periodic tick

        CHECK(CountsForLights(false, false, false, false, true));
        CHECK(!CountsForLights(true, false, false, false, true));      // triggered
        CHECK(!CountsForLights(false, true, false, false, true));      // an item's Use
        CHECK(!CountsForLights(false, false, true, false, true));      // Auto Shot, Shoot, Throw
        CHECK(!CountsForLights(false, false, false, true, true));      // passive
        CHECK(!CountsForLights(false, false, false, false, false));    // a buff, a form, a mount

        std::uint32_t const holy = 0x2u;
        std::uint32_t const fire = 0x4u;
        std::uint32_t const frost = 0x10u;
        std::uint32_t const shadow = 0x20u;
        LightsMemory memory;
        CHECK(NoteSchool(memory, holy) == LightsStep::First);          // the first spell only sets the school
        CHECK(NoteSchool(memory, holy) == LightsStep::Same);
        CHECK(NoteSchool(memory, shadow) == LightsStep::Different);
        CHECK(NoteSchool(memory, holy) == LightsStep::Different);
        CHECK(NoteSchool(memory, 0) == LightsStep::None);              // no school: nothing changes
        CHECK(memory.lastSchool == holy);
        // a multi-school spell is its own school
        CHECK(NoteSchool(memory, fire | frost) == LightsStep::Different);
        CHECK(NoteSchool(memory, fire) == LightsStep::Different);
        CHECK(NoteSchool(memory, fire | frost) == LightsStep::Different);
        CHECK(NoteSchool(memory, fire | frost) == LightsStep::Same);
        memory = LightsMemory{};                                       // put on again
        CHECK(NoteSchool(memory, fire) == LightsStep::First);
    }

    void TestDisk()
    {
        CHECK(kHealFlags == 0x44400u);
        CHECK(!(kHealFlags & 0x11000u));                               // no harmful spell

        DiskRecord record;
        CHECK(Record(record, 11, 500));
        CHECK(Record(record, 12, 300));
        CHECK(Record(record, 11, 250));                                // the same target adds up
        CHECK(!Record(record, 13, 0));                                 // nothing healed
        CHECK(!Record(record, 0, 100));                                // no guid
        CHECK(record.count == 2u);
        CHECK(record.entries[0].guid == 11u && record.entries[0].amount == 750u);
        CHECK(record.entries[1].guid == 12u && record.entries[1].amount == 300u);
        CHECK(Record(record, 12, 0xFFFFFFFFu));
        CHECK(record.entries[1].amount == 0xFFFFFFFFu);                // saturates

        DiskRecord full;
        for (std::uint64_t guid = 1; guid <= kMaxRecorded; ++guid)
            CHECK(Record(full, guid, 10));
        CHECK(!Record(full, 1000, 10));                                // a full record adds no new target
        CHECK(Record(full, 1, 10));                                    // ... but keeps adding to its own
        CHECK(full.entries[0].amount == 20u);

        // the target's healing taken modifiers undone: +20% (probe 1,200,000) and -50% (probe 500,000)
        CHECK(UndoTakenMods(600, kTakenProbe) == 600u);
        CHECK(UndoTakenMods(600, 1200000) == 500u);
        CHECK(UndoTakenMods(500, 500000) == 1000u);
        CHECK(UndoTakenMods(600, 0) == 600u);                          // a probe of 0: as it landed

        CHECK(ReplayShare(1000, 50) == 500u);                          // half
        CHECK(ReplayShare(1000, 63) == 630u);                          // the 101 tier's share
        CHECK(ReplayShare(1000, 0) == 0u);
        CHECK(ReplayShare(1000, -5) == 0u);
        CHECK(ReplayShare(0xFFFFFFFFu, 100) == 0x7FFFFFFFu);           // fits a spell value

        // six ticks add up to the share exactly; the last takes the rest
        std::uint32_t sum = 0;
        for (std::uint32_t tick = 1; tick <= 6; ++tick)
            sum += ReplayTickAmount(1003, 6, tick);
        CHECK(sum == 1003u);
        CHECK(ReplayTickAmount(1003, 6, 1) == 167u);
        CHECK(ReplayTickAmount(1003, 6, 6) == 168u);
        CHECK(ReplayTickAmount(1003, 6, 0) == 0u);
        CHECK(ReplayTickAmount(1003, 6, 7) == 0u);                     // past the last tick
        CHECK(ReplayTickAmount(1003, 0, 1) == 0u);
        CHECK(ReplayTickAmount(5, 6, 1) == 0u);                        // a small share heals on the last tick
        CHECK(ReplayTickAmount(5, 6, 6) == 5u);
    }
}

int main()
{
    TestIds();
    TestCopies();
    TestPath();
    TestMarch();
    TestKnockback();
    TestChoker();
    TestDisk();
    return Report("uldaman_hard_mode_items_test");
}
