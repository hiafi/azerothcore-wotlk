/*
 * mod-dungeon-bosses, Uldaman: the hard mode item effects of Archaedas, The Makers' Lights (after the Gnomeregan
 * precedent GnomereganHardModeItemsLogic.h). The ids mirror apps/dbc-tools/source/items/uldaman_hard_mode_effects.py
 * and source/npcs/uldaman/hard_mode_items.py (the `uldaman_items` reservation: spells 214680-214719, creatures
 * 301200-301204). The engine glue is hard_mode_items.cpp. The dungeon build adds its own files to this folder later:
 * every name here carries the item (WAKING_STONE, CHOKER, DISK), never a boss mechanic's name.
 *
 * Pure: no engine headers (the generated ItemSpellCopies.h is pure too), so the host test
 * (tests/uldaman_hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: the march's length and path width, the trample's
 * damage and knockback, Two Lights' rating, duration and stacks, the recording's length and the replay's share and
 * ticks. Only the path geometry, the march's end, the knockback rule, the Choker's school memory and the Disk's record
 * and replay split are script numbers.
 */

#ifndef MOD_DUNGEON_BOSSES_ULDAMAN_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_ULDAMAN_HARD_MODE_ITEMS_LOGIC_H

#include "ItemSpellCopies.h"
#include <array>
#include <cstdint>

namespace UldamanHardModeItems
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // ids.yaml reservation `uldaman_items` (the Uldaman gear stage); the copies of the scaled effects mint from the
    // `item_spell_copy` block, never from here.
    IdSlice constexpr kSpellsUldamanItems{ 214680, 214719 };
    IdSlice constexpr kSpellsDeclared{ 214680, 214686 };
    IdSlice constexpr kCreaturesUldamanItems{ 301200, 301204 };

    enum UldamanHardModeItemSpells : std::uint32_t
    {
        SPELL_WAKING_STONE              = 214680,   // Waking Stone, Use: the march aura
                                                    // (spell_uldaman_item_waking_stone)
        SPELL_WAKING_STONE_TRAMPLE      = 214681,   // the trample (potency, scaled per tier;
                                                    // spell_uldaman_item_earthen_trample)
        SPELL_CHOKER                    = 214682,   // Lightbound Choker, Equip: the proc aura
                                                    // (spell_uldaman_item_lightbound_choker)
        SPELL_CHOKER_TWO_LIGHTS         = 214683,   // Two Lights (a rating, scaled per tier)
        SPELL_DISK_RECORDING            = 214684,   // Fragment of the Disks, Use: the recording (its share scaled
                                                    // per tier; spell_uldaman_item_fragment_of_the_disks)
        SPELL_DISK_REPLAY               = 214685,   // the replay on the wearer (one spell for every tier;
                                                    // spell_uldaman_item_disk_replay)
        SPELL_DISK_REPLAY_HEAL          = 214686,   // one replayed heal (one spell for every tier)
        // 214687-214719 spare
    };

    enum UldamanHardModeItemCreatures : std::uint32_t
    {
        NPC_WAKING_STONE_EARTHEN        = 301200,   // Waking Earthen, the Waking Stone's marcher, look only;
                                                    // 301201-301204 spare
    };

    // Every spell this file declares, a base id or one of its tier copies (the generated table).
    constexpr bool IsItemSpell(std::uint32_t spellId)
    {
        if (kSpellsDeclared.Contains(spellId))
            return true;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
            if (copy.copy == spellId)
                return kSpellsDeclared.Contains(copy.base);
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Waking Stone

    // The earthen appears this far ahead of the wearer (look only) and marches to the first obstacle or the data's
    // length (effect 1's amount) ahead along the wearer's facing, at its speed_run (8 yd per sec).
    float constexpr kEarthenStartDistance = 1.0f;
    // It has arrived within this much of its end point (2D): the march ends early.
    float constexpr kArrivedYards = 1.0f;
    // A step's path reaches this far up or down (a floor above or below is not trampled).
    float constexpr kPathHeight = 5.0f;
    // The grid search around the earthen reaches the step, the path width and this much more (a big enemy's reach).
    float constexpr kSearchMargin = 6.0f;
    // The earthen's own despawn timer is the march's duration plus this tail: the march sends it away, the timer only
    // catches a march that never ended on its map (the wearer left it).
    std::uint32_t constexpr kEarthenTailMs = 1000;

    struct PathPoint
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
    };

    // The squared 2D distance from `p` to the step from `from` to `to` (a zero-length step is a point).
    constexpr float MarchPathDistSq(PathPoint const& from, PathPoint const& to, PathPoint const& p)
    {
        float const dx = to.x - from.x;
        float const dy = to.y - from.y;
        float const lengthSq = dx * dx + dy * dy;
        float t = 0.0f;
        if (lengthSq > 0.0f)
        {
            t = ((p.x - from.x) * dx + (p.y - from.y) * dy) / lengthSq;
            t = t < 0.0f ? 0.0f : (t > 1.0f ? 1.0f : t);
        }
        float const cx = from.x + t * dx - p.x;
        float const cy = from.y + t * dy - p.y;
        return cx * cx + cy * cy;
    }

    // An enemy at `p` with combat reach `reach` stands in the step's path: within the half width plus its reach of the
    // step (2D), and within kPathHeight of the step's end in height.
    constexpr bool OnMarchPath(PathPoint const& from, PathPoint const& to, PathPoint const& p, float reach,
        float halfWidth)
    {
        float const dz = p.z - to.z;
        if (dz > kPathHeight || dz < -kPathHeight)
            return false;
        float const within = halfWidth + (reach > 0.0f ? reach : 0.0f);
        return MarchPathDistSq(from, to, p) <= within * within;
    }

    // What the march does on a tick. It ends when there is nobody to trample for (the wearer is dead or left the map)
    // or no earthen (it timed out or was removed); it sweeps its last step and ends when it arrived; else it sweeps
    // its last step and walks on.
    enum class MarchStep : std::uint8_t
    {
        Walk,
        Arrived,
        Gone,
    };

    constexpr MarchStep StepMarch(bool wearerHere, bool earthenHere, float distanceToEnd)
    {
        if (!wearerHere || !earthenHere)
            return MarchStep::Gone;
        return distanceToEnd <= kArrivedYards ? MarchStep::Arrived : MarchStep::Walk;
    }

    // The enemies a march has trampled (one hit per enemy per march), by raw guid. A march reaches a few packs at most;
    // a full list tramples nobody new.
    std::uint32_t constexpr kMaxTrampled = 40;

    struct TrampleList
    {
        std::array<std::uint64_t, kMaxTrampled> guids{};
        std::uint32_t count = 0;
    };

    constexpr bool WasTrampled(TrampleList const& list, std::uint64_t guid)
    {
        for (std::uint32_t i = 0; i < list.count && i < kMaxTrampled; ++i)
            if (list.guids[i] == guid)
                return true;
        return false;
    }

    // True when `guid` is trampled now (the first time this march, and the list has room).
    constexpr bool MarkTrampled(TrampleList& list, std::uint64_t guid)
    {
        if (guid == 0 || WasTrampled(list, guid) || list.count >= kMaxTrampled)
            return false;
        list.guids[list.count] = guid;
        ++list.count;
        return true;
    }

    // The trample's knockback: never on a boss. The engine already refuses world bosses, instance_encounters bosses,
    // knockback-immune creatures, giants, vehicles and rooted units (Spell::EffectKnockBack); the script adds what the
    // engine does not see as a boss: a creature that binds the instance or runs a BossAI script (Olaf and Eric, whose
    // encounter credits Baelog only, and the dungeon build's new bosses).
    struct KnockbackTarget
    {
        bool creature = false;
        bool worldBoss = false;
        bool dungeonBoss = false;
        bool immune = false;
        bool bindsInstance = false;
        bool bossScript = false;
    };

    constexpr bool CanKnockBack(KnockbackTarget const& target)
    {
        if (!target.creature)
            return true;    // a player (PvP): knocked back
        return !target.worldBoss && !target.dungeonBoss && !target.immune && !target.bindsInstance
            && !target.bossScript;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Lightbound Choker

    // SpellMgr.h ProcFlags, the cast phase events 214682's spell_proc row passes: melee, ranged, magic and none class
    // spells, helpful or harmful (no auto attack). The host test keeps this header free of SpellMgr.h; the .cpp asserts
    // the values.
    std::uint32_t constexpr kOwnCastFlags = 0x10u | 0x100u | 0x400u | 0x1000u | 0x4000u | 0x10000u;

    // A cast that can light the Choker: the wearer cast it themselves (the cast phase event already skips triggered
    // casts), not an item's Use, not an auto repeat (Auto Shot, Shoot, Throw), not passive, and it deals damage or
    // heals by its data (read by the .cpp: damage, weapon damage, leech and heal effects, periodic damage, leech and
    // heal auras, one level of triggered spell). Periodic ticks raise no cast phase event.
    constexpr bool CountsForLights(bool triggered, bool fromItem, bool autoRepeat, bool passive, bool damagesOrHeals)
    {
        return !triggered && !fromItem && !autoRepeat && !passive && damagesOrHeals;
    }

    // The Choker's memory: the school mask of the last spell that counted. A multi-school spell's school is its whole
    // mask (Frostfire Bolt, Fire and Frost, is its own school).
    struct LightsMemory
    {
        std::uint32_t lastSchool = 0;
    };

    enum class LightsStep : std::uint8_t
    {
        None,       // no school (nothing changes)
        First,      // the first counting spell since the Choker was put on: it only sets the school
        Same,       // the same school as the last
        Different,  // another school: Two Lights
    };

    constexpr LightsStep NoteSchool(LightsMemory& memory, std::uint32_t schoolMask)
    {
        if (schoolMask == 0)
            return LightsStep::None;
        std::uint32_t const last = memory.lastSchool;
        memory.lastSchool = schoolMask;
        if (last == 0)
            return LightsStep::First;
        return last == schoolMask ? LightsStep::Same : LightsStep::Different;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Fragment of the Disks

    // SpellMgr.h ProcFlags, the events 214684's spell_proc row passes: helpful magic and none class spells and periodic
    // ticks (landed heals).
    std::uint32_t constexpr kHealFlags = 0x4000u | 0x400u | 0x40000u;

    // The healing the Disk records, per target (the healed unit's raw guid): the effective healing before the target's
    // own healing taken modifiers, so the replay (a heal of its own) takes them once. A full record keeps its targets
    // and adds no new one.
    std::uint32_t constexpr kMaxRecorded = 40;

    struct DiskEntry
    {
        std::uint64_t guid = 0;
        std::uint32_t amount = 0;
    };

    struct DiskRecord
    {
        std::array<DiskEntry, kMaxRecorded> entries{};
        std::uint32_t count = 0;
    };

    // Adds `amount` to the target's entry (a new entry while there is room). False when nothing was recorded.
    constexpr bool Record(DiskRecord& record, std::uint64_t guid, std::uint32_t amount)
    {
        if (guid == 0 || amount == 0)
            return false;
        for (std::uint32_t i = 0; i < record.count && i < kMaxRecorded; ++i)
        {
            if (record.entries[i].guid != guid)
                continue;
            std::uint64_t const sum = std::uint64_t(record.entries[i].amount) + amount;
            record.entries[i].amount = sum > 0xFFFFFFFFu ? 0xFFFFFFFFu : std::uint32_t(sum);
            return true;
        }
        if (record.count >= kMaxRecorded)
            return false;
        record.entries[record.count] = DiskEntry{ guid, amount };
        ++record.count;
        return true;
    }

    // The healed amount before the target's healing taken modifiers: `probeTaken` is what kTakenProbe points of the
    // same heal become on the target (Unit::SpellHealingBonusTaken; the Sergeant's Whistle's method). A probe of 0
    // cannot be undone: the amount as it landed.
    std::uint32_t constexpr kTakenProbe = 1000000;

    constexpr std::uint32_t UndoTakenMods(std::uint32_t landed, std::uint32_t probeTaken)
    {
        std::uint64_t amount = landed;
        if (probeTaken != 0)
            amount = (amount * kTakenProbe + probeTaken / 2) / probeTaken;
        return amount > 0xFFFFFFFFu ? 0xFFFFFFFFu : std::uint32_t(amount);
    }

    // The replay of one target: `sharePct` percent of what was recorded.
    constexpr std::uint32_t ReplayShare(std::uint32_t recorded, std::int32_t sharePct)
    {
        if (sharePct <= 0)
            return 0;
        std::uint64_t const amount = std::uint64_t(recorded) * std::uint64_t(sharePct) / 100u;
        return amount > 0x7FFFFFFFu ? 0x7FFFFFFFu : std::uint32_t(amount);
    }

    // Tick `tick` (1-based) of `ticks` heals an even part of `total`; the last tick takes the rounding rest, so the
    // ticks add up to `total` exactly. A tick outside 1..ticks heals nothing.
    constexpr std::uint32_t ReplayTickAmount(std::uint32_t total, std::uint32_t ticks, std::uint32_t tick)
    {
        if (ticks == 0 || tick == 0 || tick > ticks)
            return 0;
        std::uint32_t const each = total / ticks;
        return tick == ticks ? total - each * (ticks - 1) : each;
    }
}

#endif
