/*
 * mod-dungeon-bosses, Scarlet Monastery D12: Brother Aldous Thorne <Keeper of the Blessed Grain>, the Gardener
 * (300946), "The Gardener of the Cloister", the Cathedral's first boss (teaching). Build spec:
 * docs/dungeons/scarlet-monastery-4-cathedral.md "Brother Aldous Thorne, the Gardener" (GD1-GD3, Build spec), handoff
 * section 3.5 row D12, 3.6, 3.8, 7 #32 A. A new boss (no stock script to replace). Pure rules: ThorneLogic.h. Wave 2:
 * the AI (and the bramble's) registers only once kWave2Bound flips (W2-SETUP); `.dbtest sm thorne` registers now.
 *
 *   GD1  Sow            at 6 s, then every 20 s (1 s after a Prune lands): Blessed Grain on 2 (heroic 3) random
 *                       players, never the tank (a 5 s debuff), and the furrow, a 3 yd circle 5 yd along his facing,
 *                       inside the Prune's cone. As the debuff ends each carrier's seed is planted where they stand
 *   GD1a Prune          every 10 s from 5 s: a 2 s wind-up (the cone marker), then a 120 degree sweep 8 yd ahead; the
 *                       tank 15% (25%) of the tank row, anyone else 30% (45%) Physical and Weakened
 *   GD1b Cut            every seedling inside the sweep is cut away
 *   GD1c Bloom          a seedling no sweep cut blooms 15 s (heroic 10 s) after it was planted (so two sweeps can reach
 *                       it on normal, one on heroic): a 2 s marker, 6 yd, 20% (30%) Holy and Weakened
 *   GD1d Briar          (normal) the bloom leaves a 4 yd briar for the fight, 10% Nature a second, slowed 50% inside;
 *                       at most six, a seventh withers the oldest
 *   GD1e Bramble        (heroic) the bloom grows a rooted 8k Blessed Bramble with a 5 yd briar (15% a second,
 *                       slowed) until it dies
 *   GD1f Pollen         (heroic) every bramble pulses Blessed Pollen to everyone every 2 s: 1%, then 1% more a pulse,
 *                       up to 20%
 *   GD2  Holy Water     at 17 s, then every 20 s: a 2.5 s cast, he stands still; 10 yd (12) round him, 30% (45%) Holy
 *                       and Weakened
 *   GD2a Blessed ground (heroic) 8 yd where he stood, 8 s; he heals 1% of his health a second while he stands in it
 *                       (the tank alone is told to leave it, which drags him off)
 *   GD3  Bless          (heroic) Bless the Harvest at 9 s, then every 20 s: a 2.5 s interruptible cast; missed, every
 *                       standing seedling blooms at once
 *
 * The bot tank holds his facing while a seed is out (SM-BM F6: HoldTankFacing), so the sweep lands on the furrow; it
 * still steps out of Holy Water and drags him off the blessed ground. A wipe resets him to his spot and removes every
 * seedling, briar, bramble and the blessed ground; the encounter completes on his death and the brambles go with him.
 * Every percent hit is a percent of the reference row (his spells ignore caster modifiers): the registry's shapes, the
 * kit's spell_dungeon_refflat_damage on the sweep's tank hit, and DungeonKit::RefFlatOn (with Thorne as the owner) for
 * the pollen. Boss data: kill order Blessed Brambles, then Thorne; interrupt list: Bless the Harvest (heroic,
 * expected); no dispels, no purges. Every firing logs one INFO line "sm thorne <mechanic> ..." (module.dungeonbosses);
 * `.dbtest sm thorne ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThorneLogic.h"
#include "ThreatManager.h"
#include <algorithm>
#include <functional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmThorne;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "thorne";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    Position At(Vec2 p, float z = kGardenFloorZ, float o = 0.f)
    {
        return Position(p.x, p.y, z, o);
    }

    // The dry floor south of the pond: every spot the bots plan for the furrow, a sweep, a bloom, a briar, Holy Water
    // or the blessed ground stays on it (rule 12).
    BossMechanics::SpotBounds DryBounds()
    {
        std::vector<Position> points{
            Position(kDryFloor.minX, kDryFloor.minY, kGardenFloorZ),
            Position(kDryFloor.maxX, kDryFloor.minY, kGardenFloorZ),
            Position(kDryFloor.maxX, kDryFloor.maxY, kGardenFloorZ),
            Position(kDryFloor.minX, kDryFloor.maxY, kGardenFloorZ),
        };
        return BossMechanics::SpotBounds().Polygon(std::move(points), kDryZMin, kDryZMax);
    }
}

// Brother Aldous Thorne 300946
struct boss_gardener_rework : public BossAI
{
private:
    struct SowState
    {
        bool active = false;
        uint64 plantAtMs = 0;
        Vec2 furrow;
        uint32 cycle = 0;
        std::vector<ObjectGuid> carriers;
        MechanicHandle handle;
    };

    struct Seedling
    {
        uint32 id = 0;
        ObjectGuid guid;                // the sprout (none when the template is missing: the seed still counts)
        Vec2 spot;
        float z = kGardenFloorZ;
        uint64 plantedMs = 0;
        uint32 cycle = 0;
        bool budded = false;
        bool marked = false;            // the bloom's marker has started (or the registry refused it)
        MechanicHandle bloom;           // the bloom's marker
    };

    struct Briar
    {
        Vec2 spot;
        MechanicHandle handle;
        ObjectGuid look;
    };

    struct Bramble
    {
        ObjectGuid guid;
        Vec2 spot;
        MechanicHandle briar;
        uint64 grownMs = 0;
        uint64 nextPulseMs = 0;
        uint32 pulses = 0;
    };

    struct GroundState
    {
        bool active = false;
        Vec2 center;
        MechanicHandle handle;
        ObjectGuid look;
        uint64 untilMs = 0;
        uint64 nextTickMs = 0;
        uint32 ticks = 0;
    };

    struct BlessState
    {
        bool active = false;
        uint64 startedMs = 0;
    };

public:
    explicit boss_gardener_rework(Creature* creature)
        : BossAI(creature, BOSS_THORNE), _arena(GardenArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _heroic = IsHeroicMap(me);
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_THORNE;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_PULL);

        _pruneClock.Start(_clockMs, kPruneFirstMs - kPruneWarnMs);
        _sowClock.Start(_clockMs, kSowFirstMs);
        _holyClock.Start(_clockMs, kHolyWaterFirstMs);
        if (_heroic)
            _blessClock.Start(_clockMs, kBlessFirstMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) facing={:.2f}", _heroic ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), me->GetOrientation()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        Talk(SAY_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("cycles={} prunes={} cuts={} blooms={} briars={} brambles={} bramble-kills={} "
                "holy-waters={} ground-heals={} healed={} blesses={} bless-kicked={} killer={}", _cycle, _prunes, _cuts,
                _blooms, _briarsTotal, _bramblesTotal, _brambleKills, _holyWaters, _groundHeals, _groundHealed,
                _blesses, _blessKicked, killer ? killer->GetName() : "none"));
        Cleanup(true);
    }

    void KilledUnit(Unit* victim) override
    {
        if (victim && victim->IsPlayer())
            Talk(SAY_KILL);
    }

    // The summons are his: the seedlings, briars and look stalkers never fight; a bramble joins the fight at once
    // (every player on its threat list at 0, rule 11) and counts as one of his units for the bots.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
        if (summon->GetEntry() != NPC_SM_BLESSED_BRAMBLE)
            return;
        if (me->IsEngaged())
            DoZoneInCombat(summon);
        Mechanic::TrackUnit(me, summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        if (summon && summon->GetEntry() == NPC_SM_BLESSED_BRAMBLE)
            BrambleDied(summon, killer);
    }

    // GD3: a kick or a silence stopped Bless the Harvest. His own stops (an evade, his death) are not interrupts:
    // Cleanup drops the cast's state first.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_GD_BLESS_THE_HARVEST && _bless.active)
            BlessEnded(false, "interrupted");
    }

    // GD3: Bless the Harvest went off.
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell && spell->Id == SPELL_GD_BLESS_THE_HARVEST && _bless.active)
            BlessEnded(true, "landed");
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        UpdateBless();
        UpdateSow();
        UpdateSeedlings();
        UpdateBrambles();
        UpdateBlessedGround();

        bool const casting = me->HasUnitState(UNIT_STATE_CASTING);
        if (_pruneClock.Due(_clockMs))
        {
            _pruneClock.Fired(_clockMs, kPruneEveryMs);
            PruneWindUp();
        }
        if (_sowClock.Due(_clockMs))
        {
            _sowClock.Fired(_clockMs, kCycleMs);
            Sow(nullptr);
        }
        if (!casting && _holyClock.Due(_clockMs))
        {
            _holyClock.Fired(_clockMs, kCycleMs);
            HolyWater();
        }
        else if (!casting && _heroic && _blessClock.Due(_clockMs))
        {
            _blessClock.Fired(_clockMs, kCycleMs);
            StartBless();
        }
        UpdateFacingHold();

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GD1 Sow
    // ----------------------------------------------------------------------------------------------------------------

    // Blessed Grain on 2 (heroic 3) random players, never the tank (`only`, a test: just that player); the furrow
    // 5 yd along his facing, a registry Spot for each carrier (released as the debuff ends). The bot tank holds his
    // facing (the Spot's own hold, then UpdateFacingHold while a seed stands).
    bool Sow(Player* only)
    {
        std::vector<Player*> carriers;
        if (only)
            carriers.push_back(only);
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = kSowTankExempt;
            rule.tankIfAlone = false;
            carriers = DungeonKit::PickPlayers(me, rule, kCarriers(_heroic));
        }
        if (carriers.empty())
            return false;
        if (_sow.active)
            Plant();    // a test Sow on top of a live one: the earlier seeds go in now

        ++_cycle;
        Vec2 const furrow = FurrowSpot(DungeonKit::PlaneOf(me), me->GetOrientation());
        float const z = me->GetPositionZ();
        std::unordered_map<ObjectGuid, Position> spots;
        _sow = SowState();
        _sow.active = true;
        _sow.plantAtMs = _clockMs + kSowDebuffMs;
        _sow.furrow = furrow;
        _sow.cycle = _cycle;
        std::string names;
        for (Player* carrier : carriers)
        {
            me->CastSpell(carrier, SPELL_GD_BLESSED_GRAIN, true);
            spots.emplace(carrier->GetGUID(), At(furrow, z));
            _sow.carriers.push_back(carrier->GetGUID());
            names += names.empty() ? carrier->GetName() : "," + carrier->GetName();
        }
        Talk(SAY_SOW);
        MechanicRef ref = Mechanic::Spot(me, spots, Ms(kSowDebuffMs), kFurrowRadiusYd);
        ref.HoldTankFacing().Within(DryBounds()).Tag(TAG_GD_SOW);
        _sow.handle = ref.Handle();
        UpdateFacingHold();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sow",
            Acore::StringFormat("cycle={} carriers={} [{}] furrow=({:.1f}, {:.1f}) facing={:.2f}", _cycle,
                carriers.size(), names, furrow.x, furrow.y, me->GetOrientation()));
        return true;
    }

    void UpdateSow()
    {
        if (_sow.active && _clockMs >= _sow.plantAtMs)
            Plant();
    }

    // The debuff ends: each carrier's seed goes into the ground where they stand (a carrier who died plants where
    // they fell; one who left the map plants nothing).
    void Plant()
    {
        SowState const sow = _sow;
        _sow = SowState();
        uint32 planted = 0;
        uint32 inFurrow = 0;
        for (ObjectGuid const& guid : sow.carriers)
        {
            Player* carrier = ObjectAccessor::GetPlayer(*me, guid);
            if (!carrier || !carrier->IsInMap(me))
                continue;
            carrier->RemoveAurasDueToSpell(SPELL_GD_BLESSED_GRAIN);
            Vec2 const spot = DungeonKit::PlaneOf(carrier);
            if (DungeonKit::Distance(spot, sow.furrow) <= kFurrowRadiusYd)
                ++inFurrow;
            PlantSeed(spot, carrier->GetPositionZ(), sow.cycle);
            ++planted;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "plant",
            Acore::StringFormat("cycle={} planted={} in-furrow={} standing={}", _cycle, planted, inFurrow,
                _seedlings.size()));
    }

    // A seedling at `spot`: it sprouts now, buds at half its time and blooms unless a sweep cuts it first.
    void PlantSeed(Vec2 spot, float z, uint32 cycle)
    {
        Seedling seed;
        seed.id = ++_seedIds;
        seed.spot = spot;
        seed.z = z;
        seed.plantedMs = _clockMs;
        seed.cycle = cycle;
        if (sObjectMgr->GetCreatureTemplate(NPC_SM_SEEDLING))
        {
            uint32 const life = kBloomAfterMs(_heroic) + 5000;
            if (TempSummon* sprout = me->SummonCreature(NPC_SM_SEEDLING, At(spot, z, frand(0.f, 6.28f)),
                TEMPSUMMON_TIMED_DESPAWN, life))
            {
                sprout->SetObjectScale(kSeedlingSproutScale);
                sprout->CastSpell(sprout, SPELL_GD_PLANT_LOOK, true);
                seed.guid = sprout->GetGUID();
            }
        }
        _seedlings.push_back(seed);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GD1a Prune, GD1b Cut
    // ----------------------------------------------------------------------------------------------------------------

    // The wind-up: the 120 degree cone 8 yd ahead of him, marked 2 s; others 30% (45%) and Weakened through the
    // registry (the tank exempt), the tank his own hit at the resolve when still in front of him.
    bool PruneWindUp()
    {
        float const pct = kPrunePct(_heroic);
        MechanicRef ref = Mechanic::Cone(me, me, kPruneAngleDeg, kPruneLengthYd, Ms(kPruneWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_GD_PRUNE).Weakened().Within(DryBounds())
            .Tag(TAG_GD_PRUNE)
            .OnResolve(OnThorne([](boss_gardener_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.PruneLands(r);
            }));
        if (!ref.IsValid())
            return false;
        Track(ref.Handle());
        ++_prunes;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "prune",
            Acore::StringFormat("n={} pct={:.0f} tank-pct={:.0f} seedlings={}", _prunes, pct, kPruneTankPct(_heroic),
                _seedlings.size()));
        return true;
    }

    void PruneLands(BossMechanics::ResolveResult const& result)
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        me->CastSpell(me, SPELL_GD_PRUNE_LOOK, true);
        Vec2 const from = DungeonKit::PlaneOf(me);
        float const facing = me->GetOrientation();
        Unit* victim = me->GetVictim();
        bool tankHit = false;
        if (victim && CutBy(from, facing, DungeonKit::PlaneOf(victim), me->GetCombatReach()))
        {
            me->CastSpell(victim, SPELL_GD_PRUNE_TANK, true);
            tankHit = true;
        }
        uint32 cut = 0;
        for (std::size_t i = 0; i < _seedlings.size();)
        {
            if (CutBy(from, facing, _seedlings[i].spot, me->GetCombatReach()))
            {
                Cut(i);
                ++cut;
            }
            else
                ++i;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "prune-lands",
            Acore::StringFormat("hits={} tank={} cut={} left={} facing={:.2f}", result.hits.size(), tankHit ? 1 : 0,
                cut, _seedlings.size(), facing));
    }

    // GD1b: the seedling `index` is cut away (its bloom, if marked, is cancelled).
    void Cut(std::size_t index)
    {
        Seedling const seed = _seedlings[index];
        _seedlings.erase(_seedlings.begin() + static_cast<std::ptrdiff_t>(index));
        if (seed.bloom)
            Mechanic::Cancel(me, seed.bloom);
        if (Creature* sprout = seed.guid ? ObjectAccessor::GetCreature(*me, seed.guid) : nullptr)
            sprout->DespawnOrUnsummon();
        ++_cuts;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GD1c Bloom, GD1d Briar, GD1e Blessed Bramble, GD1f Blessed Pollen
    // ----------------------------------------------------------------------------------------------------------------

    // Each standing seedling buds at half its time and starts its bloom's 2 s marker 2 s before it blooms (a marker
    // the registry refused blooms without a hit at its time).
    void UpdateSeedlings()
    {
        std::vector<uint32> unmarked;
        for (Seedling& seed : _seedlings)
        {
            uint64 const age = _clockMs - seed.plantedMs;
            if (!seed.budded && age >= BudAtMs(_heroic))
            {
                seed.budded = true;
                if (Creature* sprout = seed.guid ? ObjectAccessor::GetCreature(*me, seed.guid) : nullptr)
                {
                    sprout->SetObjectScale(kSeedlingBudScale);
                    sprout->CastSpell(sprout, SPELL_GD_PLANT_LOOK, true);
                }
            }
            if (!seed.marked && age >= BloomMarkerAtMs(_heroic))
                StartBloom(seed);
            if (seed.marked && !seed.bloom && age >= kBloomAfterMs(_heroic))
                unmarked.push_back(seed.id);
        }
        for (uint32 const id : unmarked)
            Bloomed(id, BossMechanics::ResolveResult());
    }

    // The bud opens: 6 yd round the seedling, a 2 s marker, 20% (30%) Holy and Weakened.
    void StartBloom(Seedling& seed)
    {
        float const pct = kBloomPct(_heroic);
        uint32 const id = seed.id;
        MechanicRef ref = Mechanic::Circle(me, At(seed.spot, seed.z), kBloomRadiusYd, Ms(kBloomWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_HOLY).Spell(SPELL_GD_BLOOM).Weakened()
            .Within(DryBounds()).Tag(TAG_GD_BLOOM)
            .OnResolve(OnThorne([id](boss_gardener_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.Bloomed(id, r);
            }));
        seed.marked = true;
        seed.bloom = ref.Handle();
    }

    void Bloomed(uint32 id, BossMechanics::ResolveResult const& result)
    {
        auto it = std::find_if(_seedlings.begin(), _seedlings.end(), [id](Seedling const& s) { return s.id == id; });
        if (it == _seedlings.end())
            return;     // cut meanwhile
        Seedling const seed = *it;
        _seedlings.erase(it);
        if (Creature* sprout = seed.guid ? ObjectAccessor::GetCreature(*me, seed.guid) : nullptr)
            sprout->DespawnOrUnsummon();
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        ++_blooms;
        me->CastSpell(seed.spot.x, seed.spot.y, seed.z, SPELL_GD_BLOOM_LOOK, true);
        if (seed.cycle != _bloomEmoteCycle)
        {
            _bloomEmoteCycle = seed.cycle;
            Talk(EMOTE_BLOOM);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bloom",
            Acore::StringFormat("cycle={} at=({:.1f}, {:.1f}) hits={} pct={:.0f} age={}ms", seed.cycle, seed.spot.x,
                seed.spot.y, result.hits.size(), kBloomPct(_heroic), _clockMs - seed.plantedMs));
        if (_heroic)
            GrowBramble(seed.spot, seed.z);
        else
            AddBriar(seed.spot, seed.z);
    }

    // GD1d (normal): a 4 yd briar for the fight, 10% Nature a second and the 50% slow (the ticks' rider), no Weakened.
    // A seventh withers the oldest.
    void AddBriar(Vec2 spot, float z)
    {
        for (std::size_t n = BriarsToWither(_briars.size()); n > 0 && !_briars.empty(); --n)
            WitherBriar(0, "cap");
        MechanicRef ref = Mechanic::Circle(me, At(spot, z), kBriarRadiusYd, Ms(kBriarTickMs));
        ref.Persistent(Ms(kBriarLastMs), Ms(kBriarTickMs)).Damage(kBriarPct).TankDamage(kBriarPct)
            .School(SPELL_SCHOOL_NATURE).Spell(SPELL_GD_BRIAR).Rider(SPELL_GD_BRIAR_SLOW).NoFillTimer()
            .Within(DryBounds()).Tag(TAG_GD_BRIAR);
        Briar briar;
        briar.spot = spot;
        briar.handle = ref.Handle();
        if (sObjectMgr->GetCreatureTemplate(NPC_SM_BRIAR))
            if (TempSummon* look = me->SummonCreature(NPC_SM_BRIAR, At(spot, z), TEMPSUMMON_TIMED_DESPAWN,
                kBriarLastMs))
            {
                look->CastSpell(look, SPELL_GD_BRIAR_LOOK, true);
                briar.look = look->GetGUID();
            }
        _briars.push_back(briar);
        ++_briarsTotal;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "briar",
            Acore::StringFormat("at=({:.1f}, {:.1f}) standing={} pct={:.0f}", spot.x, spot.y, _briars.size(),
                kBriarPct));
    }

    void WitherBriar(std::size_t index, char const* why)
    {
        Briar const briar = _briars[index];
        _briars.erase(_briars.begin() + static_cast<std::ptrdiff_t>(index));
        if (briar.handle)
            Mechanic::Cancel(me, briar.handle);
        if (Creature* look = briar.look ? ObjectAccessor::GetCreature(*me, briar.look) : nullptr)
            look->DespawnOrUnsummon();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "briar-wither",
            Acore::StringFormat("why={} at=({:.1f}, {:.1f}) standing={}", why, briar.spot.x, briar.spot.y,
                _briars.size()));
    }

    // GD1e (heroic): a rooted Blessed Bramble at the bloom, its 5 yd briar (15% a second, the slow) until it dies; its
    // pollen from 2 s on.
    bool GrowBramble(Vec2 spot, float z)
    {
        if (!sObjectMgr->GetCreatureTemplate(NPC_SM_BLESSED_BRAMBLE))
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bramble-failed", "no template 300949");
            return false;
        }
        TempSummon* bramble = me->SummonCreature(NPC_SM_BLESSED_BRAMBLE, At(spot, z, frand(0.f, 6.28f)),
            TEMPSUMMON_MANUAL_DESPAWN);
        if (!bramble)
            return false;
        bramble->SetReactState(REACT_PASSIVE);
        bramble->SetControlled(true, UNIT_STATE_ROOT);
        bramble->CastSpell(bramble, SPELL_GD_BRIAR_LOOK, true);
        bramble->CastSpell(bramble, SPELL_GD_POLLEN_LOOK, true);
        MechanicRef ref = Mechanic::Circle(me, At(spot, z), kBrambleBriarRadiusYd, Ms(kBriarTickMs));
        ref.Persistent(Ms(kBriarLastMs), Ms(kBriarTickMs)).Damage(kBrambleBriarPct).TankDamage(kBrambleBriarPct)
            .School(SPELL_SCHOOL_NATURE).Spell(SPELL_GD_BRAMBLE_BRIAR).Rider(SPELL_GD_BRIAR_SLOW).NoFillTimer()
            .Within(DryBounds()).Tag(TAG_GD_BRAMBLE_BRIAR);
        Bramble state;
        state.guid = bramble->GetGUID();
        state.spot = spot;
        state.briar = ref.Handle();
        state.grownMs = _clockMs;
        state.nextPulseMs = _clockMs + kPollenFirstMs;
        _brambles.push_back(state);
        ++_bramblesTotal;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bramble",
            Acore::StringFormat("at=({:.1f}, {:.1f}) standing={} health={}", spot.x, spot.y, _brambles.size(),
                bramble->GetMaxHealth()));
        return true;
    }

    // GD1f: every 2 s each living bramble pulses Blessed Pollen to every player: 1%, 2%, ... up to 20% of the
    // reference row (Thorne the owner). Stunned or crowd controlled, it still pulses (a triggered cast).
    void UpdateBrambles()
    {
        for (Bramble& state : _brambles)
        {
            if (_clockMs < state.nextPulseMs)
                continue;
            state.nextPulseMs += kPollenEveryMs;
            Creature* bramble = ObjectAccessor::GetCreature(*me, state.guid);
            if (!bramble || !bramble->IsAlive())
                continue;
            ++state.pulses;
            float const pct = PollenPct(state.pulses);
            uint32 hit = 0;
            for (Player* player : FightPlayers())
            {
                int32 const bp = static_cast<int32>(DungeonKit::RefFlatOn(me, player, pct));
                if (bp <= 0)
                    continue;
                bramble->CastCustomSpell(player, SPELL_GD_POLLEN, &bp, nullptr, nullptr, true);
                ++hit;
            }
            if (state.pulses == 1 || state.pulses % 5 == 0)
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pollen",
                    Acore::StringFormat("pulse={} pct={:.0f} players={} alive={}s", state.pulses, pct, hit,
                        (_clockMs - state.grownMs) / 1000));
        }
    }

    void BrambleDied(Creature* bramble, Unit* killer)
    {
        auto it = std::find_if(_brambles.begin(), _brambles.end(),
            [bramble](Bramble const& b) { return b.guid == bramble->GetGUID(); });
        if (it == _brambles.end())
            return;
        Bramble const state = *it;
        _brambles.erase(it);
        if (state.briar)
            Mechanic::Cancel(me, state.briar);
        bramble->RemoveAurasDueToSpell(SPELL_GD_BRIAR_LOOK);
        bramble->RemoveAurasDueToSpell(SPELL_GD_POLLEN_LOOK);
        bramble->DespawnOrUnsummon(Seconds(5));
        ++_brambleKills;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bramble-dies",
            Acore::StringFormat("pulses={} alive={}s dealt={:.0f}% standing={} killer={}", state.pulses,
                (_clockMs - state.grownMs) / 1000, PollenTotalPct(state.pulses), _brambles.size(),
                killer ? killer->GetName() : "none"));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GD2 Holy Water, GD2a Blessed ground
    // ----------------------------------------------------------------------------------------------------------------

    // He raises the aspergillum: a 2.5 s bar (not interruptible), he stands still and keeps his facing; the ring round
    // where he stands, 10 yd (12), 30% (45%) Holy and Weakened, the tank row on the tank.
    bool HolyWater()
    {
        me->StopMoving();
        Vec2 const at = DungeonKit::PlaneOf(me);
        float const z = me->GetPositionZ();
        DungeonKit::CastBar(me, SPELL_GD_HOLY_WATER_CAST, nullptr, EMOTE_HOLY_WATER);
        float const pct = kHolyWaterPct(_heroic);
        float const radius = kHolyWaterRadiusYd(_heroic);
        MechanicRef ref = Mechanic::Circle(me, At(at, z), radius, Ms(kHolyWaterCastMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_HOLY).Spell(SPELL_GD_HOLY_WATER).Weakened()
            .Within(DryBounds()).Tag(TAG_GD_HOLY_WATER)
            .OnResolve(OnThorne([at, z](boss_gardener_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.HolyWaterLands(at, z, r);
            }));
        if (!ref.IsValid())
            return false;
        Track(ref.Handle());
        ++_holyWaters;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-water",
            Acore::StringFormat("n={} at=({:.1f}, {:.1f}) radius={:.0f} pct={:.0f}", _holyWaters, at.x, at.y, radius,
                pct));
        return true;
    }

    void HolyWaterLands(Vec2 at, float z, BossMechanics::ResolveResult const& result)
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-water-lands",
            Acore::StringFormat("hits={} ground={}", result.hits.size(), _heroic ? 1 : 0));
        if (_heroic)
            BlessedGround(at, z);
    }

    // GD2a (heroic): 8 yd where he stood, 8 s: no damage, the tank alone told to leave it (G1/G2 F14: the drag), his
    // heal while he stands in it.
    void BlessedGround(Vec2 at, float z)
    {
        EndBlessedGround("replaced", false);
        BossMechanics::Eligibility tankOnly;
        tankOnly.roles = BossMechanics::Role::Tank;
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(BossMechanics::Anchor(At(at, z)),
            kBlessedGroundRadiusYd), Ms(kBlessedGroundTickMs));
        ref.Persistent(Ms(kBlessedGroundMs), Ms(kBlessedGroundTickMs)).Damage(0.f).Eligible(tankOnly).NoFillTimer()
            .Within(DryBounds()).Tag(TAG_GD_BLESSED_GROUND);
        _ground = GroundState();
        _ground.active = true;
        _ground.center = at;
        _ground.handle = ref.Handle();
        _ground.untilMs = _clockMs + kBlessedGroundMs;
        _ground.nextTickMs = _clockMs + kBlessedGroundTickMs;
        if (sObjectMgr->GetCreatureTemplate(NPC_SM_STALKER_WAVE2))
            if (TempSummon* look = me->SummonCreature(NPC_SM_STALKER_WAVE2, At(at, z), TEMPSUMMON_TIMED_DESPAWN,
                kBlessedGroundMs))
            {
                look->CastSpell(look, SPELL_GD_BLESSED_GROUND_LOOK, true);
                _ground.look = look->GetGUID();
            }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "blessed-ground",
            Acore::StringFormat("at=({:.1f}, {:.1f}) radius={:.0f} for={}ms", at.x, at.y, kBlessedGroundRadiusYd,
                kBlessedGroundMs));
    }

    void UpdateBlessedGround()
    {
        if (!_ground.active)
            return;
        if (_clockMs >= _ground.untilMs)
        {
            EndBlessedGround("expired");
            return;
        }
        if (_clockMs < _ground.nextTickMs)
            return;
        _ground.nextTickMs += kBlessedGroundTickMs;
        if (DungeonKit::Distance(DungeonKit::PlaneOf(me), _ground.center) > kBlessedGroundRadiusYd
            || me->GetHealth() >= me->GetMaxHealth())
            return;
        int32 const bp = static_cast<int32>(BlessedGroundHeal(me->GetMaxHealth()));
        me->CastCustomSpell(me, SPELL_GD_BLESSED_GROUND_HEAL, &bp, nullptr, nullptr, true);
        ++_ground.ticks;
        ++_groundHeals;
        _groundHealed += static_cast<uint32>(bp);
    }

    void EndBlessedGround(char const* why, bool log = true)
    {
        if (!_ground.active)
            return;
        GroundState const ground = _ground;
        _ground = GroundState();
        if (ground.handle)
            Mechanic::Cancel(me, ground.handle);
        if (Creature* look = ground.look ? ObjectAccessor::GetCreature(*me, ground.look) : nullptr)
            look->DespawnOrUnsummon();
        if (log)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "blessed-ground-end",
                Acore::StringFormat("why={} heals={}", why, ground.ticks));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GD3 Bless the Harvest (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    bool StartBless()
    {
        me->StopMoving();
        Talk(SAY_BLESS);
        SpellCastResult const result = me->CastSpell(me, SPELL_GD_BLESS_THE_HARVEST, false);
        if (result != SPELL_CAST_OK)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bless-failed",
                Acore::StringFormat("result={}", static_cast<uint32>(result)));
            return false;
        }
        _bless.active = true;
        _bless.startedMs = _clockMs;
        ++_blesses;
        Mechanic::NoteNextCastIn(me, SPELL_GD_BLESS_THE_HARVEST, Ms(kCycleMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bless",
            Acore::StringFormat("n={} cast={}ms seedlings={}", _blesses, kBlessCastMs, _seedlings.size()));
        return true;
    }

    // The cast ended without a hook (it went off, or he lost it): a cast that ran its time landed.
    void UpdateBless()
    {
        if (!_bless.active || me->FindCurrentSpellBySpellId(SPELL_GD_BLESS_THE_HARVEST))
            return;
        if (_clockMs < _bless.startedMs + kCastStartGraceMs)
            return;     // the cast has not taken yet
        BlessEnded(_clockMs >= _bless.startedMs + kBlessCastMs, "no-hook");
    }

    // Kicked: nothing. Missed: every standing seedling blooms at once (its 2 s marker from now).
    void BlessEnded(bool landed, char const* how)
    {
        _bless = BlessState();
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        uint32 blooming = 0;
        if (landed)
        {
            for (Seedling& seed : _seedlings)
                if (!seed.marked)
                {
                    StartBloom(seed);
                    ++blooming;
                }
        }
        else
            ++_blessKicked;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, landed ? "bless-landed" : "bless-interrupted",
            Acore::StringFormat("how={} blooming={} kicked={}/{}", how, blooming, _blessKicked, _blesses));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The tank's facing hold (SM-BM F6)
    // ----------------------------------------------------------------------------------------------------------------

    // While the carriers walk to the furrow and while any seedling stands, the bot tank does not walk round him to
    // re-face him (Holy Water's step-out and the blessed ground's drag still move it).
    void UpdateFacingHold()
    {
        bool const want = me->IsAlive() && me->IsEngaged() && (_sow.active || !_seedlings.empty());
        if (want == _holding)
            return;
        _holding = want;
        if (want)
            Mechanic::HoldTankFacing(me, me, Ms(0));
        else
            Mechanic::ReleaseTankFacing(me, me);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (CATH "Boss data")
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order: the Blessed Brambles, then Thorne (the tank stays on him). Interrupt list: Bless the Harvest (heroic,
    // expected). No dispels, no purges. The seedlings, briars and look stalkers are ignored.
    void Describe()
    {
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.ignores.emplace_back(NPC_SM_SEEDLING);
        d.ignores.emplace_back(NPC_SM_BRIAR);
        d.ignores.emplace_back(NPC_SM_STALKER_WAVE2);
        d.targets.push_back(TargetEntry(NPC_SM_BLESSED_BRAMBLE, 1, Who::Dps));
        d.targets.push_back(TargetEntry(NPC_SM_BLESSED_BRAMBLE, -1, Who::Tank));
        d.targets.push_back(TargetEntry(NPC_SM_THORNE, 0, Who::Any));
        if (_heroic)
            d.interrupts.emplace_back(NPC_SM_THORNE, SPELL_GD_BLESS_THE_HARVEST, 3, Ms(kCycleMs));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm thorne` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Prune,
        Sow,
        Seed,
        Bloom,
        Briar,
        Bramble,
        HolyWater,
        Ground,
        Bless,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM).
    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!me->IsEngaged())
            return "Thorne must be in combat (the picks read his threat list, the mechanics his encounter).";
        bool const busy = me->HasUnitState(UNIT_STATE_CASTING);
        Player* player = CountsAsPlayer(who) ? who : nullptr;
        switch (mechanic)
        {
            case TestMechanic::Prune:
                if (!PruneWindUp())
                    return "The registry refused the sweep.";
                break;
            case TestMechanic::Sow:
                if (!Sow(nullptr))
                    return "Nobody to carry the grain.";
                break;
            case TestMechanic::Seed:
                if (!player)
                    return "Select a living player (not a game master in GM mode).";
                PlantSeed(DungeonKit::PlaneOf(player), player->GetPositionZ(), _cycle);
                break;
            case TestMechanic::Bloom:
            {
                uint32 n = 0;
                for (Seedling& seed : _seedlings)
                    if (!seed.marked)
                    {
                        StartBloom(seed);
                        ++n;
                    }
                if (!n)
                    return "No seedling waits to bloom (plant one with `seed`).";
                break;
            }
            case TestMechanic::Briar:
                if (!player)
                    return "Select a living player (not a game master in GM mode).";
                AddBriar(DungeonKit::PlaneOf(player), player->GetPositionZ());
                break;
            case TestMechanic::Bramble:
                if (!player)
                    return "Select a living player (not a game master in GM mode).";
                if (!GrowBramble(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                    return "No bramble (the template 300949 is missing or the summon failed).";
                break;
            case TestMechanic::HolyWater:
                if (busy)
                    return "He is casting.";
                if (!HolyWater())
                    return "The registry refused the ring.";
                break;
            case TestMechanic::Ground:
                BlessedGround(DungeonKit::PlaneOf(me), me->GetPositionZ());
                break;
            case TestMechanic::Bless:
                if (busy || _bless.active)
                    return "He is casting.";
                if (!StartBless())
                    return "Bless the Harvest did not start (see the log).";
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} cycle={} sow={} seedlings={} briars={} brambles={} ground={} "
            "bless={} hold={} prunes={} cuts={} blooms={} bramble-kills={} holy-waters={} ground-heals={} blesses={} "
            "kicked={} live-handles={} next: prune={}s sow={}s holy={}s bless={}s",
            _clockMs / 1000, _heroic ? 1 : 0, _cycle, _sow.active ? 1 : 0, _seedlings.size(), _briars.size(),
            _brambles.size(), _ground.active ? 1 : 0, _bless.active ? 1 : 0, _holding ? 1 : 0, _prunes, _cuts, _blooms,
            _brambleKills, _holyWaters, _groundHeals, _blesses, _blessKicked, _live.size(), _pruneClock.DueMs() / 1000,
            _sowClock.DueMs() / 1000, _holyClock.DueMs() / 1000, _blessClock.On() ? _blessClock.DueMs() / 1000 : 0);
    }

private:
    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (!CountsAsPlayer(player) || !player->IsInMap(me))
                continue;
            out.push_back(player);
        }
        return out;
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnThorne(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_gardener_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    static boss_gardener_rework* From(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_gardener_rework*>(boss->AI());
    }

    // Reset, evade and death (RB-1): every handle cancelled, every seedling, briar, bramble and look gone, the
    // carriers' grain off, the facing hold released, every clock stopped and every count zeroed.
    void Cleanup(bool dead)
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_sow.handle)
            Mechanic::Cancel(me, _sow.handle);
        for (ObjectGuid const& guid : _sow.carriers)
            if (Player* carrier = ObjectAccessor::GetPlayer(*me, guid))
                carrier->RemoveAurasDueToSpell(SPELL_GD_BLESSED_GRAIN);
        _sow = SowState();
        for (Seedling const& seed : _seedlings)
            if (seed.bloom)
                Mechanic::Cancel(me, seed.bloom);
        _seedlings.clear();
        for (Briar const& briar : _briars)
            if (briar.handle)
                Mechanic::Cancel(me, briar.handle);
        _briars.clear();
        for (Bramble const& bramble : _brambles)
            if (bramble.briar)
                Mechanic::Cancel(me, bramble.briar);
        _brambles.clear();
        EndBlessedGround(dead ? "death" : "reset", false);
        if (_holding)
            Mechanic::ReleaseTankFacing(me, me);
        _holding = false;
        summons.DespawnAll();
        _bless = BlessState();
        _pruneClock.Stop();
        _sowClock.Stop();
        _holyClock.Stop();
        _blessClock.Stop();
        _arena.Reset();
        _clockMs = 0;
        _cycle = 0;
        _seedIds = 0;
        _bloomEmoteCycle = 0;
        _prunes = 0;
        _cuts = 0;
        _blooms = 0;
        _briarsTotal = 0;
        _bramblesTotal = 0;
        _brambleKills = 0;
        _holyWaters = 0;
        _groundHeals = 0;
        _groundHealed = 0;
        _blesses = 0;
        _blessKicked = 0;
    }

    DungeonKit::ArenaGuard _arena;
    Clock _pruneClock;
    Clock _sowClock;
    Clock _holyClock;
    Clock _blessClock;
    SowState _sow;
    BlessState _bless;
    GroundState _ground;
    std::vector<Seedling> _seedlings;
    std::vector<Briar> _briars;
    std::vector<Bramble> _brambles;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint32 _cycle = 0;
    uint32 _seedIds = 0;
    uint32 _bloomEmoteCycle = 0;
    uint32 _prunes = 0;
    uint32 _cuts = 0;
    uint32 _blooms = 0;
    uint32 _briarsTotal = 0;
    uint32 _bramblesTotal = 0;
    uint32 _brambleKills = 0;
    uint32 _holyWaters = 0;
    uint32 _groundHeals = 0;
    uint32 _groundHealed = 0;
    uint32 _blesses = 0;
    uint32 _blessKicked = 0;
    bool _holding = false;
    bool _heroic = false;
};

// The Blessed Bramble 300949 (heroic, GD1e): rooted, never swings, never chases. Its briar and its pollen are Thorne's
// (his AI owns their timers and registry handles); it only stays put. Stuns and crowd control work on it and stop
// nothing. When its fight is over (Thorne out of combat or gone) it withers instead of evading to full health.
struct npc_sm_blessed_bramble : public ScriptedAI
{
    explicit npc_sm_blessed_bramble(Creature* creature) : ScriptedAI(creature) { }

    void InitializeAI() override
    {
        ScriptedAI::InitializeAI();
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }

    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        Unit* summoner = me->IsSummon() ? me->ToTempSummon()->GetSummonerUnit() : nullptr;
        if (!summoner || !summoner->IsAlive() || !summoner->IsInCombat())
            me->DespawnOrUnsummon();
    }
};

namespace
{
    boss_gardener_rework* FindThorneAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_SM_THORNE);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_gardener_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Thorne is not running boss_gardener_rework (wave 2 unbound, or check "
                "the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_gardener_rework::TestMechanic mechanic, char const* what)
    {
        boss_gardener_rework* ai = FindThorneAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Thorne: {} fired ({}).", what, ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    using Mech = boss_gardener_rework::TestMechanic;

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_SM_THORNE, BOSS_THORNE);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_gardener_rework* ai = FindThorneAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Thorne: {}", ai->TestState());
        return true;
    }

    bool HandlePrune(ChatHandler* handler)
    {
        return Fire(handler, Mech::Prune, "Prune (GD1a: the 2 s wind-up, then the 120 degree sweep; cuts seedlings)");
    }

    bool HandleSow(ChatHandler* handler)
    {
        return Fire(handler, Mech::Sow, "Sow (GD1: Blessed Grain on the carriers, the furrow ahead of him)");
    }

    bool HandleSeed(ChatHandler* handler)
    {
        return Fire(handler, Mech::Seed, "a seedling at the selected player (GD1: it grows and blooms unless cut)");
    }

    bool HandleBloom(ChatHandler* handler)
    {
        return Fire(handler, Mech::Bloom, "the bloom of every standing seedling (GD1c: the 2 s marker from now)");
    }

    bool HandleBriar(ChatHandler* handler)
    {
        return Fire(handler, Mech::Briar, "a briar at the selected player (GD1d, the normal patch)");
    }

    bool HandleBramble(ChatHandler* handler)
    {
        return Fire(handler, Mech::Bramble, "a Blessed Bramble at the selected player (GD1e / GD1f)");
    }

    bool HandleHolyWater(ChatHandler* handler)
    {
        return Fire(handler, Mech::HolyWater, "Holy Water (GD2: the 2.5 s cast and the ring; heroic: the ground)");
    }

    bool HandleGround(ChatHandler* handler)
    {
        return Fire(handler, Mech::Ground, "the blessed ground under him (GD2a, 8 s)");
    }

    bool HandleBless(ChatHandler* handler)
    {
        return Fire(handler, Mech::Bless, "Bless the Harvest (GD3: a 2.5 s cast, kick it)");
    }

    // `.dbtest sm thorne <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BossGardenerTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "prune",     HandlePrune,     SEC_GAMEMASTER, Console::No },
            { "sow",       HandleSow,       SEC_GAMEMASTER, Console::No },
            { "seed",      HandleSeed,      SEC_GAMEMASTER, Console::No },
            { "bloom",     HandleBloom,     SEC_GAMEMASTER, Console::No },
            { "briar",     HandleBriar,     SEC_GAMEMASTER, Console::No },
            { "bramble",   HandleBramble,   SEC_GAMEMASTER, Console::No },
            { "holywater", HandleHolyWater, SEC_GAMEMASTER, Console::No },
            { "ground",    HandleGround,    SEC_GAMEMASTER, Console::No },
            { "bless",     HandleBless,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_gardener_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_gardener_rework, ScarletMonasteryRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_sm_blessed_bramble, ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("thorne", BossGardenerTestCommands());
}
