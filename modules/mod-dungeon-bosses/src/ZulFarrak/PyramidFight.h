/*
 * mod-dungeon-bosses, Zul'Farrak D4a: the Pyramid's shared engine pieces, the hooks every stage plugs into (the Block,
 * D4a; the Stair and the Altar, D4b). WP-D4a owns this file; D4b reads it and asks for changes (after D4a reports, the
 * orchestrator). The interface is documented in
 * .agents/plans/zul-farrak-build/zul-farrak-build.STAGE-D4a-REPORT.md section 1. Header-only (inline). The pure half
 * (ids, numbers, the rules the host test pins) is BlockLogic.h namespace ZfBlock.
 *
 * What already exists, in the instance and ZulFarrakKit.h: the stage machine (DATA_PYRAMID_STAGE / _RUNNING, START,
 * COMPLETE, FAIL), the stage directors (RegisterPyramidStage), the Offerings count (DATA_OFFERINGS: the instance adds
 * one per crew member lost on the Block, cap 4) and the Blood Price total (DATA_BLOOD_PRICE: the instance adds 30 per
 * crew member lost on the Block on heroic; the owners write the per-second ticks), both snapshot and restored on a
 * wipe. Nothing here writes slot 5, a stage, the crew or a crew member's faction.
 *
 * What this adds:
 *   Grievous Wound      PY2 (heroic): ApplyGrievousWound(caster, target) for every wound of the encounter (the Block's
 *                       soaker, a Berserker's heroic charge, Nekrum's Gutchew); it ends at 95% health (the aura's
 *                       own tick, spell_zf_pyramid_grievous_wound, and every PyramidBuffs poll).
 *   Sandfury buffs      PY3 Offerings (normal, +10% a stack, cap 4) and PY16 Blood Price (heroic, +0.5% a stack, no
 *                       cap) on every Sandfury of the encounter, always equal to the instance's count.
 *   PyramidBuffs        one per stage director: tracks the stage's Sandfury, keeps their buff current, clears healed
 *                       wounds and, on heroic while a stage runs and any player bleeds, adds one Blood Price stack a
 *                       second (SetData(DATA_BLOOD_PRICE, total)).
 *   PyramidStage        the director base: runs a PyramidBuffs, tracks the Sandfury entries created while it runs.
 *   bots                AddWoundHealRule (BM-1's healUntil: heal a carrier on to 95%), WoundFree (a heroic Soak's
 *                       eligibility: no wound).
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_PYRAMID_FIGHT_H
#define MOD_DUNGEON_BOSSES_ZF_PYRAMID_FIGHT_H

#include "BlockLogic.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MechanicRegistry.h"
#include "ObjectGuid.h"
#include "Player.h"
#include "SezzzizLogic.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include <set>
#include <string>

namespace ZfPyramid
{
    using ZfBlock::SPELL_PY_BLOOD_PRICE;
    using ZfBlock::SPELL_PY_GRIEVOUS_LOOK;
    using ZfBlock::SPELL_PY_GRIEVOUS_WOUND;
    using ZfBlock::SPELL_PY_OFFERINGS;
    using ZfBlock::IsPyramidSandfury;

    char constexpr kLogKey[] = "pyramid";

    inline void Log(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(ZulFarrakRework::kLogDungeon, kLogKey, mechanic, detail);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The instance's Pyramid numbers
    // ----------------------------------------------------------------------------------------------------------------
    struct PyramidRead
    {
        uint32 stage = ZulFarrakRework::PYRAMID_STAGE_NONE;
        bool running = false;
        bool heroic = false;
        uint32 offerings = 0;
        uint32 bloodPrice = 0;
    };

    inline PyramidRead ReadPyramid(InstanceScript const* instance)
    {
        PyramidRead r;
        if (!instance)
            return r;
        r.stage = instance->GetData(ZulFarrakRework::DATA_PYRAMID_STAGE);
        r.running = instance->GetData(ZulFarrakRework::DATA_PYRAMID_RUNNING) != 0;
        r.heroic = instance->instance && instance->instance->IsHeroic();
        r.offerings = instance->GetData(ZulFarrakRework::DATA_OFFERINGS);
        r.bloodPrice = instance->GetData(ZulFarrakRework::DATA_BLOOD_PRICE);
        return r;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PY3 Offerings, PY16 Blood Price: the buff on one Sandfury
    // ----------------------------------------------------------------------------------------------------------------

    // Offerings (normal): exactly OfferingsStacks(n) stacks (0: none).
    inline void SetOfferings(Creature* unit, uint32 offerings)
    {
        uint32 const want = ZfBlock::OfferingsStacks(offerings);
        uint32 const now = DungeonKit::Stacks(unit, SPELL_PY_OFFERINGS, unit->GetGUID());
        if (want != now)
            DungeonKit::AddStacks(unit, SPELL_PY_OFFERINGS, int32(want) - int32(now), unit,
                ZulFarrakRework::kOfferingsCap);
    }

    // Blood Price (heroic): the stacks shown (at most 255) and the damage done of `total` stacks (0.5% each, no cap:
    // the amount is set on the aura, as Zum'rah's Ward of the Dead does, so it never depends on the counter).
    inline void SetBloodPrice(Creature* unit, uint32 total)
    {
        uint32 const shown = ZfBlock::BloodPriceShownStacks(total);
        uint32 const now = DungeonKit::Stacks(unit, SPELL_PY_BLOOD_PRICE, unit->GetGUID());
        if (shown != now)
            DungeonKit::AddStacks(unit, SPELL_PY_BLOOD_PRICE, int32(shown) - int32(now), unit,
                ZfBlock::Tune::kAuraStackLimit);
        if (!shown)
            return;
        if (Aura* aura = unit->GetAura(SPELL_PY_BLOOD_PRICE, unit->GetGUID()))
            if (AuraEffect* effect = aura->GetEffect(EFFECT_0))
            {
                int32 const want = ZfBlock::BloodPriceDamagePct(total);
                if (effect->GetAmount() != want)
                    effect->ChangeAmount(want);
            }
    }

    inline void RemoveSandfuryBuff(Creature* unit)
    {
        if (!unit)
            return;
        unit->RemoveAurasDueToSpell(SPELL_PY_OFFERINGS);
        unit->RemoveAurasDueToSpell(SPELL_PY_BLOOD_PRICE);
    }

    // The buff to the instance's count now: Offerings on normal, Blood Price on heroic (it replaces Offerings, SP
    // PY16). A dead unit is left alone.
    inline void ApplySandfuryBuff(Creature* unit, InstanceScript const* instance)
    {
        if (!unit || !unit->IsInWorld() || !unit->IsAlive() || !instance)
            return;
        PyramidRead const r = ReadPyramid(instance);
        if (r.heroic)
        {
            unit->RemoveAurasDueToSpell(SPELL_PY_OFFERINGS);
            SetBloodPrice(unit, r.bloodPrice);
        }
        else
        {
            unit->RemoveAurasDueToSpell(SPELL_PY_BLOOD_PRICE);
            SetOfferings(unit, r.offerings);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PY2 Grievous Wound
    // ----------------------------------------------------------------------------------------------------------------

    inline bool HasWound(Unit const* unit)
    {
        return unit && unit->HasAura(SPELL_PY_GRIEVOUS_WOUND);
    }

    // The look and the wound from `caster` (both triggered; the aura's tick is the kit's RefFlatOn, so the caster's
    // map gives the reference row and its death changes nothing). Heroic only: false on a normal map.
    inline bool ApplyGrievousWound(Unit* caster, Unit* target)
    {
        if (!caster || !target || !target->IsAlive() || !DungeonKit::IsHeroicMap(target))
            return false;
        caster->CastSpell(target, SPELL_PY_GRIEVOUS_LOOK, true);
        caster->CastSpell(target, SPELL_PY_GRIEVOUS_WOUND, true);
        return HasWound(target);
    }

    // The living players of `map` (no game masters) that carry a wound.
    inline uint32 CountBleeding(Map* map)
    {
        uint32 n = 0;
        if (!map)
            return 0;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
                if (player->IsAlive() && !player->IsGameMaster() && HasWound(player))
                    ++n;
        return n;
    }

    inline bool AnyPlayerBleeding(Map* map)
    {
        return CountBleeding(map) != 0;
    }

    // Every player of `map` healed to 95% or more loses the wound (the aura's own tick does it too, once a second).
    // Returns how many.
    inline uint32 ClearHealedWounds(Map* map)
    {
        uint32 n = 0;
        if (!map)
            return 0;
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || !HasWound(player) || !ZfBlock::WoundClears(player->GetHealthPct()))
                continue;
            player->RemoveAurasDueToSpell(SPELL_PY_GRIEVOUS_WOUND);
            ++n;
            Log("wound-cleared", Acore::StringFormat("player={} health={:.0f}", player->GetName(),
                player->GetHealthPct()));
        }
        return n;
    }

    // Every wound on the map gone (a wipe, the Pyramid won).
    inline void ClearWounds(InstanceScript* instance)
    {
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_PY_GRIEVOUS_WOUND);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The bots
    // ----------------------------------------------------------------------------------------------------------------

    // SP "Boss data": Grievous Wound carriers are healed until it clears (BM-1 F17: bots read a carrier as at most
    // 80% until it reaches 95%). Heroic only; add it to every descriptor a Pyramid owner registers.
    inline void AddWoundHealRule(BossMechanics::Descriptor& d, bool heroic)
    {
        if (heroic)
            d.healUntil.emplace_back(SPELL_PY_GRIEVOUS_WOUND, ZfBlock::Tune::kWoundClearPct);
    }

    // A heroic Soak's eligibility: no wound (SP "soaker rotation is Soak eligibility LacksAura(Grievous Wound)").
    inline BossMechanics::Eligibility WoundFree()
    {
        BossMechanics::Eligibility e;
        e.auraSpell = SPELL_PY_GRIEVOUS_WOUND;
        e.maxStacks = 0;
        return e;
    }

    // The Altar's boss data (SP "Boss data"), one copy for both owners that describe it: Sezz'ziz from his pull and
    // the Altar's director stalker for the whole stage (R-1-B mn-1: the descent, the idle wait, and after Sezz'ziz
    // dies while Nekrum and the adds fight on). Kicks: the Offering first (required on heroic), the Witch Doctors'
    // Flash Heal (a reward), never his Shadow Bolt (a kick there locks only Shadow, but it spends the kick the
    // Offering needs); cures: Curse of Blood and Sandfury Hex (Curse), Hexed and the Scream's fear (Magic, loss of
    // control); kill order: the Witch Doctors, the Healing Wards, the Hexmasters, the rest of his adds and the
    // fodder, then Nekrum and him; heroic: Grievous Wound carriers healed on to 95%.
    inline BossMechanics::Descriptor AltarDescriptor(bool heroic)
    {
        using namespace ZulFarrakRework;
        uint32 const offering = heroic ? uint32(ZfAltar::SPELL_BLOOD_OFFERING_H)
            : uint32(ZfAltar::SPELL_BLOOD_OFFERING);
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_SEZZZIZ, offering, uint8(heroic ? 3 : 2),
            std::chrono::milliseconds(ZfAltar::Tune::kOfferingMinMs));
        d.interrupts.emplace_back(NPC_ZF_SANDFURY_WITCH_DOCTOR, ZfStair::SPELL_FLASH_HEAL, uint8(1));
        d.interrupts.emplace_back(NPC_SEZZZIZ, ZfAltar::SPELL_SHADOW_BOLT, uint8(0));
        d.dispels.emplace_back(ZfStair::SPELL_HEXED, uint8(3), true);
        d.dispels.emplace_back(ZfAltar::SPELL_SCREAM_FEAR, uint8(2), true);
        d.dispels.emplace_back(ZfStair::SPELL_CURSE_OF_BLOOD, uint8(1));
        d.dispels.emplace_back(ZfStair::SPELL_SANDFURY_HEX, uint8(1));
        d.targets.emplace_back(NPC_ZF_SANDFURY_WITCH_DOCTOR, int8(4));
        d.targets.emplace_back(ZfStair::NPC_HEALING_WARD, int8(3));
        d.targets.emplace_back(NPC_ZF_SANDFURY_HEXMASTER, int8(2));
        d.targets.emplace_back(NPC_ZF_SANDFURY_BERSERKER, int8(1));
        d.targets.emplace_back(NPC_SANDFURY_SLAVE, int8(1));
        d.targets.emplace_back(NPC_SANDFURY_DRUDGE, int8(1));
        AddWoundHealRule(d, heroic);
        return d;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PyramidBuffs: the Sandfury watch of one stage (report section 1.2)
    // ----------------------------------------------------------------------------------------------------------------
    class PyramidBuffs
    {
    public:
        explicit PyramidBuffs(InstanceScript* instance) : _instance(instance) { }

        // The stage runs: the clocks start, every tracked unit gets its buff now.
        void Start()
        {
            _running = true;
            _pollMs = 0;
            _refreshMs = 0;
            _meter.Reset();
            _bleeding = 0;
            RefreshAll();
        }

        // The stage ended. Lost (a wipe): the buffs come off the tracked units and every wound on the map goes.
        void Stop(bool lost)
        {
            if (_bleeding)
                Log("bleed-stop", Acore::StringFormat("total={} (stage over)", ReadPyramid(_instance).bloodPrice));
            if (lost)
            {
                ForEach([](Creature* unit) { RemoveSandfuryBuff(unit); });
                ClearWounds(_instance);
            }
            _tracked.clear();
            _running = false;
            _bleeding = 0;
            _meter.Reset();
        }

        void Track(Creature* unit)
        {
            if (!unit)
                return;
            _tracked.insert(unit->GetGUID());
            if (_running)
                ApplySandfuryBuff(unit, _instance);
        }

        void Untrack(ObjectGuid const& guid) { _tracked.erase(guid); }

        void Update(uint32 diff)
        {
            if (!_running || !_instance || !_instance->instance)
                return;
            _pollMs += diff;
            if (_pollMs >= ZfBlock::Tune::kWoundPollMs)
            {
                uint32 const elapsed = _pollMs;
                _pollMs = 0;
                Poll(elapsed);
            }
            _refreshMs += diff;
            if (_refreshMs >= ZfBlock::Tune::kBuffRefreshMs)
            {
                _refreshMs = 0;
                RefreshAll();
            }
        }

        bool Running() const { return _running; }
        std::size_t Tracked() const { return _tracked.size(); }
        uint32 Bleeding() const { return _bleeding; }

        // Every tracked unit alive to the instance's count now; the dead and the gone are dropped.
        void RefreshAll()
        {
            if (!_instance || !_instance->instance)
                return;
            for (auto it = _tracked.begin(); it != _tracked.end();)
            {
                Creature* unit = _instance->instance->GetCreature(*it);
                if (!unit || !unit->IsInWorld() || !unit->IsAlive())
                {
                    it = _tracked.erase(it);
                    continue;
                }
                ApplySandfuryBuff(unit, _instance);
                ++it;
            }
        }

    private:
        template <class Fn>
        void ForEach(Fn&& fn)
        {
            if (!_instance || !_instance->instance)
                return;
            for (ObjectGuid const& guid : _tracked)
                if (Creature* unit = _instance->instance->GetCreature(guid))
                    fn(unit);
        }

        // The wounds: the healed lose theirs; on heroic while the stage runs, each full second with a carrier is a
        // Blood Price stack (one a second however many bleed).
        void Poll(uint32 elapsed)
        {
            Map* map = _instance->instance;
            ClearHealedWounds(map);
            uint32 const carriers = CountBleeding(map);
            PyramidRead const r = ReadPyramid(_instance);
            if (carriers && !_bleeding)
                Log("bleed-start", Acore::StringFormat("total={} carriers={} stage={}", r.bloodPrice, carriers,
                    r.stage));
            else if (!carriers && _bleeding)
                Log("bleed-stop", Acore::StringFormat("total={} stage={}", r.bloodPrice, r.stage));
            _bleeding = carriers;
            if (!r.heroic || !r.running)
                return;
            uint32 const stacks = _meter.Advance(elapsed, carriers != 0);
            if (!stacks)
                return;
            uint32 const total = r.bloodPrice + stacks;
            _instance->SetData(ZulFarrakRework::DATA_BLOOD_PRICE, total);
            if (ZfBlock::BloodPriceLogs(r.bloodPrice, total))
                Log("bloodprice", Acore::StringFormat("total={} damage=+{}% carriers={} stage={}", total,
                    ZfBlock::BloodPriceDamagePct(total), carriers, r.stage));
            RefreshAll();
        }

        InstanceScript* _instance;
        std::set<ObjectGuid> _tracked;
        ZfBlock::BleedMeter _meter;
        uint32 _pollMs = 0;
        uint32 _refreshMs = 0;
        uint32 _bleeding = 0;
        bool _running = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // PyramidStage: the director base (report section 1.3). A derived director calls the base in every hook it
    // overrides (PyramidStage::OnStart(restart); first, and so on).
    // ----------------------------------------------------------------------------------------------------------------
    class PyramidStage : public ZulFarrakRework::PyramidStageDirector
    {
    public:
        PyramidStage(InstanceScript* instance, uint32 stage)
            : ZulFarrakRework::PyramidStageDirector(instance), _buffs(instance), _stage(stage) { }

        void OnStart(bool /*restart*/) override { _buffs.Start(); }
        void OnUpdate(uint32 diff) override { _buffs.Update(diff); }
        void OnEnd(bool won) override { _buffs.Stop(!won); }

        // A Sandfury of the encounter made while the stage runs (the waves, Sezz'ziz's adds) is tracked at once.
        void OnCreatureCreate(Creature* creature) override
        {
            if (creature && _buffs.Running() && IsPyramidSandfury(creature->GetEntry()))
                _buffs.Track(creature);
        }

    protected:
        PyramidBuffs& Buffs() { return _buffs; }
        uint32 Stage() const { return _stage; }
        bool Heroic() const { return Instance() && Instance()->instance && Instance()->instance->IsHeroic(); }

    private:
        PyramidBuffs _buffs;
        uint32 _stage;
    };
}

#endif
