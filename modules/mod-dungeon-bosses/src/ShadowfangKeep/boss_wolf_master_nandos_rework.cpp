/*
 * mod-dungeon-bosses, Shadowfang Keep: Wolf Master Nandos and his pack (WP-S8). Build spec: SK 1338-1390 (build spec),
 * SK 1238-1337 (design), NA1-NA9; handoff section 3.5 rows NA and section 3.6 row S8. Replaces SmartAI 3927 (Call
 * Lupine Horror 7489 and Call Bleak Worg 7487 dropped) and the four wolves' guid SmartAI (-16238 to -16241); the
 * spawns 16238-16241 now hold the boss-kit copies 300509-300512 (npc_sfk_pack_wolf).
 *
 *   The pack      one encounter: pulling Nandos or any wolf pulls all five; Nandos fights from the pull. A wipe brings
 *                 the dead wolves back (until Nandos is DONE). His death (DONE) opens Arugal's Lair and summons the
 *                 lair prisoner (the instance).
 *   NA1           Bleak Worg: stock Wavering Will 7127 on its target, 2-10 s then every 15-20 s (dispel list)
 *   NA2           Lupine Horror: stock Summon Lupine Delusions 7132, 4-12 s then every 60 s (the delusions vanish when
 *                 hit: stock SmartAI 5097)
 *   NA4           Slavering Worg: Acid Slaver, a 2 s cast bar and a 90 degree / 8 yd Frontal (its target exempt), 35%
 *                 Nature + Weakened, 6 s then every 15 s
 *   NA5           Wolfguard Worg: Guardian Howl, a real 2 s interruptible cast healing Nandos and every living wolf 5%
 *                 (heroic: +15% damage done for 10 s), 8 s then every 20 s (interrupt list)
 *   NA6           Mark the Prey: a whistle (emote, type 41) and a 6 yd Stack ring on a random non-tank, 10 s then every
 *                 18 s while a wolf lives; 4 s later every living wolf lunges at the prey: 25% of reference health per
 *                 wolf, split among the players in the ring, at most 75% each (Physical, no Weakened)
 *   NA7           Pack Bond: Nandos takes 40% less damage, 10% less per wolf killed (one aura, amount set by the
 *                 script); each living wolf holds a beam on him (Blood Mirror SV 14876) that drops with it
 *   NA8 (heroic)  The Alpha's Inheritance: each wolf's death hands Nandos its ability from 5 s later: Wavering Will
 *                 (stock slows + a 2% Shadow DoT stack every 15 s on his tank, 5 stacks, Magic), Lupine Delusions every
 *                 20 s with NA3 (2 s after one of his delusions vanishes, a 5 yd marker and a 2 s fear there), Acid
 *                 Slaver at 20 yd every 15 s, Guardian Howl with the damage buff every 20 s
 *   Yell 0        on the last wolf's death (stock line), both difficulties
 *   NA9           melee stock (DamageModifier 3.3); heroic through DD's damage hook
 *
 * Pilot lessons: the custom damage spells ignore caster modifiers (registry resolve copies; the lunge's share is set
 * as its base point, so the target's defensives count); every timer runs on `_timers` (Nandos) or the wolves' own
 * scheduler, never on BossAI::scheduler, which the cast bar pauses; mechanic emotes are type 41; each hit has a look
 * on the player (Acid Breath impact, Rip's claw, the fear state); the boss cannot be kited off his room (ArenaGuard on
 * NandosArena()). Each firing logs `sfk nandos <mechanic> ...` (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "NandosLogic.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TaskScheduler.h"
#include <list>
#include <string>
#include <string_view>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;
using namespace Nandos;

namespace
{
    using Ms = Milliseconds;

    char constexpr kBoss[] = "nandos";

    // SetGUID ids: a pack wolf tells Nandos it died (the id carries its Wolf index).
    int32 constexpr kSetGuidWolfDied = 0x4E414400;

    // Nandos's _timers groups.
    enum NandosTimerGroups : uint32
    {
        GROUP_PREY = 1,
        GROUP_INHERIT,
    };

    Ms RandomMs(uint32 min, uint32 max)
    {
        return Ms(urand(min, max));
    }

    void LogNandos(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    Creature* FindNandos(WorldObject* from)
    {
        InstanceScript* instance = from ? from->GetInstanceScript() : nullptr;
        return instance ? instance->GetCreature(DATA_NANDOS_GUID) : nullptr;
    }

    // The registry encounter's owner for a wolf's own mechanic: Nandos while he lives, else the wolf itself.
    Unit* EncounterOwner(Creature* wolf)
    {
        if (Creature* nandos = FindNandos(wolf); nandos && nandos->IsAlive())
            return nandos;
        return wolf;
    }

    // The pack copies within kPackSearchYd of `center`, dead ones too.
    std::vector<Creature*> Pack(WorldObject* center)
    {
        std::vector<Creature*> out;
        if (!center || !center->IsInWorld())
            return out;
        std::list<Creature*> found;
        center->GetCreatureListWithEntryInGrid(found, std::vector<uint32>(kPackEntries.begin(), kPackEntries.end()),
            kPackSearchYd);
        out.assign(found.begin(), found.end());
        return out;
    }

    std::vector<Creature*> LivingPack(WorldObject* center)
    {
        std::vector<Creature*> out;
        for (Creature* wolf : Pack(center))
            if (wolf->IsAlive() && wolf->IsInWorld())
                out.push_back(wolf);
        return out;
    }

    bool Busy(Creature* creature)
    {
        return creature->HasUnitState(UNIT_STATE_CASTING);
    }

    // NA4: the cast bar on `source` (a Slavering Worg, or Nandos when inherited) and the Frontal beside it, owned by
    // `owner` (the encounter). The cone turns with the source; the source's target is exempt.
    void AcidSlaver(Unit* owner, Creature* source, bool inherited)
    {
        if (!owner || !source || !source->IsAlive())
            return;
        float const length = SlaverLength(inherited);
        char const* from = inherited ? "nandos" : "slavering";
        DungeonKit::CastBar(source, SPELL_NANDOS_ACID_SLAVER_BAR);
        Mechanic::Cone(owner, source, kSlaverAngleDeg, length, Ms(kSlaverWarnMs), BossMechanics::TankExempt::Yes)
            .Damage(kSlaverPct).School(SPELL_SCHOOL_NATURE).Spell(SPELL_NANDOS_ACID_SLAVER).Weakened()
            .Tag(inherited ? TAG_NANDOS_ACID_SLAVER_ALPHA : TAG_NANDOS_ACID_SLAVER)
            .OnResolve([from, length](BossMechanics::ResolveResult const& result)
            {
                LogNandos("acid-slaver-resolve", Acore::StringFormat("from={} yd={:.0f} hit={}", from, length,
                    result.hits.size()));
            });
        LogNandos("acid-slaver", Acore::StringFormat("from={} yd={:.0f} pct={:.0f}", from, length, kSlaverPct));
    }

    // NA5: the real interruptible cast (the spell script keeps Nandos and the pack as its targets).
    void GuardianHowl(Creature* caster)
    {
        if (!caster || !caster->IsAlive())
            return;
        bool const heroic = DungeonKit::IsHeroicMap(caster);
        uint32 const spellId = kHowlSpell(heroic);
        caster->CastSpell(caster, spellId, false);
        Mechanic::NoteNextCastIn(caster, spellId, Ms(kHowlEveryMs));
        LogNandos("guardian-howl", Acore::StringFormat("from={} heroic={}", caster->GetEntry() == NPC_NANDOS ? "nandos"
            : "wolfguard", heroic ? 1 : 0));
    }
}

// Wolf Master Nandos 3927
struct boss_wolf_master_nandos_rework : public BossAI
{
    explicit boss_wolf_master_nandos_rework(Creature* creature) : BossAI(creature, BOSS_NANDOS),
        _arena(NandosArena(), ArenaOptions()) { }

    static DungeonKit::ArenaGuardOptions ArenaOptions()
    {
        DungeonKit::ArenaGuardOptions o;
        // A unit in combat with another live boss is left to that boss: no two guards grip it to and fro (R2 S-2).
        o.skipGrip = DungeonKit::SkipEngagedWithOtherBoss(ShadowfangKeepRework::IsSfkBossEntry);
        DungeonKit::ApplyPlaytestPullRule(o);
        o.landing = [](Creature const* /*boss*/, Unit const* unit)
        {
            return DungeonKit::ToPosition(GripLanding(DungeonKit::PlaneOf(unit)), kNandosOpenPoint.z);
        };
        // The fight pulls the whole instance (DoZoneInCombat): never yank someone from Fenrus's room or the lair.
        o.maxGripYd = kGripMaxYd;
        o.logPrefix = "sfk nandos arena";
        o.offArenaReason = "off-room";
        return o;
    }

    void Reset() override
    {
        _Reset();
        EndFight();
        RespawnPack();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        bool const heroic = DungeonKit::IsHeroicMap(me);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_NANDOS;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        PullPack(who);
        BindPack();
        Describe(heroic);

        _timers.Schedule(Ms(kPreyFirstMs), GROUP_PREY, [this](TaskContext context)
        {
            if (!PreyActive(static_cast<uint32>(LivingPack(me).size())))
                return;     // no wolves left: Mark the Prey stops
            MarkThePrey(nullptr);
            context.Repeat(Ms(kPreyEveryMs));
        });
        LogNandos("engage", Acore::StringFormat("heroic={} health={} wolves={}", heroic ? 1 : 0, me->GetMaxHealth(),
            LivingPack(me).size()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        EndFight();
        EvadePack();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        EndFight();
        BossAI::JustDied(killer);
        LogNandos("died", Acore::StringFormat("wolves={}", LivingPack(me).size()));
    }

    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id >= kSetGuidWolfDied && id < kSetGuidWolfDied + static_cast<int32>(kWolfCount))
            WolfDied(guid, static_cast<Wolf>(id - kSetGuidWolfDied));
    }

    void JustSummoned(Creature* summon) override
    {
        BossAI::JustSummoned(summon);
        if (summon->GetEntry() == NPC_LUPINE_DELUSION)
            _delusions.insert(summon->GetGUID());
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        DelusionGone(summon);
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        DelusionGone(summon);
        BossAI::SummonedCreatureDespawn(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.sfktest nandos` mechanic's follow-ups. Never paused by a cast (Pilot R1 S-2).
        _timers.Update(diff);

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his room: evading
        if (me->IsActionPreventedByCasting())
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pack
    // ----------------------------------------------------------------------------------------------------------------

    // Every living wolf joins the fight and counts as a unit of the encounter.
    void PullPack(Unit* who)
    {
        Unit* target = who ? who : me->GetVictim();
        for (Creature* wolf : LivingPack(me))
        {
            Mechanic::TrackUnit(me, wolf);
            if (target && !wolf->IsInCombat() && wolf->IsAIEnabled)
                wolf->AI()->AttackStart(target);
        }
    }

    void EvadePack()
    {
        for (Creature* wolf : LivingPack(me))
            if (wolf->IsInCombat() && wolf->IsAIEnabled)
                wolf->AI()->EnterEvadeMode();
    }

    // A wipe brings back the wolves the group killed (until Nandos is DONE).
    void RespawnPack()
    {
        if (instance && instance->GetBossState(BOSS_NANDOS) == DONE)
            return;
        for (Creature* wolf : Pack(me))
            if (!wolf->IsAlive())
                wolf->Respawn(true);
    }

    // NA7 at the pull: every living wolf's beam on Nandos and his Pack Bond for that many wolves.
    void BindPack()
    {
        std::vector<Creature*> const wolves = LivingPack(me);
        for (Creature* wolf : wolves)
            wolf->CastSpell(me, SPELL_NANDOS_PACK_BOND_LINK, true);
        me->CastSpell(me, SPELL_NANDOS_PACK_BOND, true);
        UpdatePackBond(static_cast<uint32>(wolves.size()));
    }

    void UpdatePackBond(uint32 alive)
    {
        int32 const amount = PackBondAmount(alive);
        if (!amount)
        {
            me->RemoveAurasDueToSpell(SPELL_NANDOS_PACK_BOND);
            return;
        }
        if (AuraEffect* effect = me->GetAuraEffect(SPELL_NANDOS_PACK_BOND, EFFECT_0))
            effect->ChangeAmount(amount);
    }

    int32 PackBondNow() const
    {
        AuraEffect const* effect = me->GetAuraEffect(SPELL_NANDOS_PACK_BOND, EFFECT_0);
        return effect ? effect->GetAmount() : 0;
    }

    // A wolf died (its AI tells him): its beam drops, Pack Bond weakens, on heroic he inherits its ability, and the
    // last one makes him yell.
    void WolfDied(ObjectGuid wolfGuid, Wolf wolf)
    {
        me->RemoveAurasDueToSpell(SPELL_NANDOS_PACK_BOND_LINK, wolfGuid);
        if (!me->IsAlive() || !me->IsInCombat())
            return;
        uint32 const alive = static_cast<uint32>(LivingPack(me).size());
        UpdatePackBond(alive);
        LogNandos("wolf-died", Acore::StringFormat("wolf={} alive={} bond={}", WolfName(wolf), alive, PackBondNow()));
        if (DungeonKit::IsHeroicMap(me))
            Inherit(wolf);
        if (!alive)
        {
            Talk(YELL_NANDOS_PACK_DEAD);
            _timers.CancelGroup(GROUP_PREY);
            LogNandos("pack-dead");
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NA6 Mark the Prey
    // ----------------------------------------------------------------------------------------------------------------

    // `forced` (a `.sfktest` pick) is marked even with no wolf alive (the lunge then hits nobody).
    void MarkThePrey(Player* forced)
    {
        Player* prey = forced;
        if (!prey)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            rule.maxRange = kPreyPickRangeYd;
            prey = DungeonKit::PickPlayer(me, rule);
        }
        if (!prey)
            return;
        Talk(EMOTE_NANDOS_MARK_THE_PREY, prey);
        me->CastSpell(prey, SPELL_NANDOS_MARKED_PREY, true);
        Map* map = me->GetMap();
        ObjectGuid const self = me->GetGUID();
        ObjectGuid const preyGuid = prey->GetGUID();
        Mechanic::Stack(me, prey, kPreyRadiusYd, Ms(kPreyWarnMs)).Tag(TAG_NANDOS_MARK_THE_PREY)
            .OnResolve([map, self, preyGuid](BossMechanics::ResolveResult const& result)
            {
                Creature* nandos = map->GetCreature(self);
                if (!nandos || !nandos->IsAlive() || !nandos->IsAIEnabled)
                    return;
                if (auto* ai = dynamic_cast<boss_wolf_master_nandos_rework*>(nandos->AI()))
                    ai->PreyLunge(preyGuid, result.hits);
            });
        LogNandos("mark-the-prey", Acore::StringFormat("prey={} wolves={}", prey->GetName(), LivingPack(me).size()));
    }

    // The Stack resolved: every living wolf lunges at the prey; the players in the ring share 25% per wolf (75% cap).
    void PreyLunge(ObjectGuid preyGuid, std::vector<ObjectGuid> const& hits)
    {
        std::vector<Creature*> const wolves = LivingPack(me);
        std::vector<Unit*> inside;
        for (ObjectGuid const& guid : hits)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid); player && player->IsAlive())
                inside.push_back(player);
        if (wolves.empty() || inside.empty())
        {
            LogNandos("mark-the-prey-lunge", Acore::StringFormat("wolves={} inside={} (nothing)", wolves.size(),
                inside.size()));
            return;
        }

        Player* prey = ObjectAccessor::GetPlayer(*me, preyGuid);
        Position const at = prey && prey->IsAlive() ? prey->GetPosition() : inside.front()->GetPosition();
        for (Creature* wolf : wolves)
        {
            Vec2 const land = LungeLanding(DungeonKit::PlaneOf(wolf), { at.GetPositionX(), at.GetPositionY() },
                kLungeOffsetYd);
            DungeonKit::JumpTo(wolf, DungeonKit::ToPosition(land, at.GetPositionZ()), kLungeSpeedXY, kLungeMinSpeedZ);
        }

        std::vector<std::pair<ObjectGuid, uint32>> const shares = DungeonKit::SplitShares(me, inside,
            PreyTotalPct(static_cast<uint32>(wolves.size())), kPreyCapPct);
        for (std::size_t i = 0; i < shares.size(); ++i)
        {
            Unit* target = ObjectAccessor::GetUnit(*me, shares[i].first);
            if (!target || !target->IsAlive())
                continue;
            Creature* wolf = wolves[LungeWolfFor(i, wolves.size())];
            int32 const share = static_cast<int32>(shares[i].second);
            wolf->CastCustomSpell(SPELL_NANDOS_MARK_THE_PREY, SPELLVALUE_BASE_POINT0, share, target,
                TRIGGERED_FULL_MASK);
        }
        LogNandos("mark-the-prey-lunge", Acore::StringFormat("wolves={} inside={} share={} total_pct={:.0f}",
            wolves.size(), inside.size(), shares.empty() ? 0 : shares.front().second,
            PreyTotalPct(static_cast<uint32>(wolves.size()))));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NA8 The Alpha's Inheritance (heroic; `.sfktest nandos inherit` forces it on normal)
    // ----------------------------------------------------------------------------------------------------------------

    void Inherit(Wolf wolf)
    {
        if (!_inheritance.Take(wolf))
            return;
        LogNandos("inherit", Acore::StringFormat("wolf={} held={}", WolfName(wolf), _inheritance.Count()));
        uint32 const every = InheritedEveryMs(wolf);
        _timers.Schedule(Ms(kInheritFirstMs), GROUP_INHERIT, [this, wolf, every](TaskContext context)
        {
            if (Busy(me) || !me->GetVictim())
            {
                context.Repeat(Ms(kBusyRetryMs));
                return;
            }
            UseInherited(wolf);
            context.Repeat(Ms(every));
        });
    }

    void UseInherited(Wolf wolf)
    {
        switch (wolf)
        {
            case Wolf::Bleak:
                AlphaWill(me->GetVictim());
                break;
            case Wolf::Lupine:
                DoCastSelf(SPELL_SUMMON_LUPINE_DELUSIONS);
                LogNandos("alpha-delusions");
                break;
            case Wolf::Slavering:
                AcidSlaver(me, me, true);
                break;
            case Wolf::Wolfguard:
                GuardianHowl(me);
                break;
        }
    }

    // NA1 inherited: the stock slows (refreshed) and one more stack of the Shadow DoT (5 at most) on `target`.
    void AlphaWill(Unit* target)
    {
        if (!target || !target->IsAlive())
            return;
        me->CastSpell(target, SPELL_WAVERING_WILL, true);
        uint32 const stacks = DungeonKit::AddStacks(target, SPELL_NANDOS_WAVERING_WILL, 1, me, kAlphaWillMaxStacks);
        LogNandos("alpha-wavering-will", Acore::StringFormat("target={} stacks={}", target->GetName(), stacks));
    }

    // NA3: one of his own delusions left the world. Hit (not despawned at full health): the fear spot 2 s later.
    void DelusionGone(Creature* summon)
    {
        if (!summon || !_delusions.erase(summon->GetGUID()))
            return;
        if (!me->IsAlive() || (!me->IsInCombat() && !_testTerror))
            return;
        if (!VanishedByHit(summon->IsAlive(), summon->GetHealth(), summon->GetMaxHealth()))
            return;
        LupineTerror(summon->GetPosition());
    }

    void LupineTerror(Position const& spot)
    {
        Mechanic::Circle(me, spot, kTerrorRadiusYd, Ms(kTerrorWarnMs)).Spell(SPELL_NANDOS_LUPINE_TERROR_HIT)
            .Rider(SPELL_NANDOS_LUPINE_TERROR).Tag(TAG_NANDOS_LUPINE_TERROR)
            .OnResolve([](BossMechanics::ResolveResult const& result)
            {
                LogNandos("lupine-terror-resolve", Acore::StringFormat("feared={}", result.hits.size()));
            });
        LogNandos("lupine-terror", Acore::StringFormat("x={:.1f} y={:.1f}", spot.GetPositionX(), spot.GetPositionY()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Descriptor and cleanup
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order Wolfguard, Slavering, Bleak, Lupine, Nandos (SK 1368, approved), the delusions first (one hit, AoE
    // fine); interrupt Guardian Howl (the wolf's, and Nandos's inherited one on heroic); dispel Wavering Will (the
    // inherited DoT before the stock slows: clearing the DoT clears both).
    void Describe(bool heroic)
    {
        BossMechanics::Descriptor d;
        for (std::size_t i = 0; i < kWolfCount; ++i)
        {
            Wolf const wolf = static_cast<Wolf>(i);
            d.targets.emplace_back(EntryOf(wolf), KillPriority(wolf));
        }
        d.targets.push_back(BossMechanics::TargetEntry(NPC_LUPINE_DELUSION, kDelusionPriority).AoeOk());
        d.interrupts.emplace_back(NPC_SFK_PACK_WOLFGUARD_WORG, kHowlSpell(heroic), 2, Ms(kHowlEveryMs));
        d.dispels.emplace_back(SPELL_WAVERING_WILL, 1);
        if (heroic)
        {
            d.interrupts.emplace_back(NPC_NANDOS, SPELL_NANDOS_GUARDIAN_HOWL_HEROIC, 2, Ms(kHowlEveryMs));
            d.dispels.emplace_back(SPELL_NANDOS_WAVERING_WILL, 2);
        }
        Mechanic::Describe(me, std::move(d));
    }

    void EndFight()
    {
        _timers.CancelAll();
        _inheritance.Clear();
        _delusions.clear();
        _testTerror = false;
        _arena.Reset();
        me->RemoveAurasDueToSpell(SPELL_NANDOS_PACK_BOND);
        me->RemoveAurasDueToSpell(SPELL_NANDOS_PACK_BOND_LINK);
    }

    // `.sfktest nandos fear`: a Lupine Terror spot out of combat too.
    void TestTerror(Position const& spot)
    {
        _testTerror = true;
        LupineTerror(spot);
    }

    Inheritance const& Held() const { return _inheritance; }
    Creature* Self() const { return me; }

    TaskScheduler _timers;
    DungeonKit::ArenaGuard _arena;
    Inheritance _inheritance;
    GuidSet _delusions;
    bool _testTerror = false;
};

// Bleak Worg 300509, Lupine Horror 300510, Slavering Worg 300511, Wolfguard Worg 300512 (spawns 16239, 16238, 16240,
// 16241): one ability each, linked to Nandos.
struct npc_sfk_pack_wolf : public ScriptedAI
{
    explicit npc_sfk_pack_wolf(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        scheduler.CancelAll();
    }

    void JustEngagedWith(Unit* who) override
    {
        PullNandos(who);
        ScheduleAbility();
    }

    // The Lupine Horror's delusions join the fight.
    void JustSummoned(Creature* summon) override
    {
        if (me->IsInCombat())
            DoZoneInCombat(summon);
    }

    void JustDied(Unit* /*killer*/) override
    {
        scheduler.CancelAll();
        std::optional<Wolf> const wolf = WolfOf(me->GetEntry());
        Creature* nandos = FindNandos(me);
        if (wolf && nandos && nandos->IsAIEnabled)
            nandos->AI()->SetGUID(me->GetGUID(), kSetGuidWolfDied + static_cast<int32>(Index(*wolf)));
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        scheduler.Update(diff);
        if (me->IsActionPreventedByCasting())
            return;
        DoMeleeAttackIfReady();
    }

    // Pulled on its own, it pulls Nandos (who pulls the rest of the pack).
    void PullNandos(Unit* who)
    {
        Creature* nandos = FindNandos(me);
        if (nandos && nandos->IsAlive() && !nandos->IsInCombat() && who && nandos->IsAIEnabled)
            nandos->AI()->AttackStart(who);
    }

    // A timer that meets a cast in progress tries again shortly.
    template <class Fn>
    void Every(Ms first, Fn&& fire)
    {
        scheduler.Schedule(first, [this, fire](TaskContext context)
        {
            if (Busy(me))
            {
                context.Repeat(Ms(kBusyRetryMs));
                return;
            }
            context.Repeat(fire());
        });
    }

    void ScheduleAbility()
    {
        std::optional<Wolf> const wolf = WolfOf(me->GetEntry());
        if (!wolf)
            return;
        switch (*wolf)
        {
            case Wolf::Bleak:       // NA1
                Every(RandomMs(kWillFirstMinMs, kWillFirstMaxMs), [this]()
                {
                    if (Unit* victim = me->GetVictim())
                    {
                        DoCastVictim(SPELL_WAVERING_WILL);
                        LogNandos("wavering-will", Acore::StringFormat("target={}", victim->GetName()));
                    }
                    return RandomMs(kWillEveryMinMs, kWillEveryMaxMs);
                });
                break;
            case Wolf::Lupine:      // NA2
                Every(RandomMs(kDelusionsFirstMinMs, kDelusionsFirstMaxMs), [this]()
                {
                    DoCastSelf(SPELL_SUMMON_LUPINE_DELUSIONS);
                    LogNandos("delusions", "from=lupine");
                    return Ms(kDelusionsEveryMs);
                });
                break;
            case Wolf::Slavering:   // NA4
                Every(Ms(kSlaverFirstMs), [this]()
                {
                    AcidSlaver(EncounterOwner(me), me, false);
                    return Ms(kSlaverEveryMs);
                });
                break;
            case Wolf::Wolfguard:   // NA5
                Mechanic::NoteNextCastIn(me, kHowlSpell(DungeonKit::IsHeroicMap(me)), Ms(kHowlFirstMs));
                Every(Ms(kHowlFirstMs), [this]()
                {
                    GuardianHowl(me);
                    return Ms(kHowlEveryMs);
                });
                break;
        }
    }
};

// 206042 / 206043 Guardian Howl: the area-ally search keeps Nandos and the pack copies only (both effects).
class spell_sfk_nandos_guardian_howl : public SpellScript
{
    PrepareSpellScript(spell_sfk_nandos_guardian_howl);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if([](WorldObject* object)
        {
            Creature const* creature = object ? object->ToCreature() : nullptr;
            return !creature || !creature->IsAlive() || !HowlTouches(creature->GetEntry());
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sfk_nandos_guardian_howl::FilterTargets,
            EFFECT_ALL, TARGET_UNIT_SRC_AREA_ALLY);
    }
};

// 206048 Wavering Will (inherited): each stack ticks 2% of reference health as Shadow every 2 s (the aura multiplies
// the amount by its stacks). One dispel clears every stack and the stock slows Nandos put with it.
class spell_sfk_nandos_wavering_will : public AuraScript
{
    PrepareAuraScript(spell_sfk_nandos_wavering_will);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        Unit* caster = GetCaster();
        // The tank row on Nandos's tank (R2 N-1).
        amount = static_cast<int32>(DungeonKit::RefFlatOn(caster, GetUnitOwner(), kAlphaWillPctPerStack));
        canBeRecalculated = caster != nullptr;
    }

    void ClearAllStacks(DispelInfo* dispelInfo)
    {
        dispelInfo->SetRemovedCharges(GetStackAmount());
    }

    void DropSlows(DispelInfo* /*dispelInfo*/)
    {
        if (Unit* owner = GetUnitOwner())
            owner->RemoveAurasDueToSpell(SPELL_WAVERING_WILL, GetCasterGUID());
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sfk_nandos_wavering_will::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
        OnDispel += AuraDispelFn(spell_sfk_nandos_wavering_will::ClearAllStacks);
        AfterDispel += AuraDispelFn(spell_sfk_nandos_wavering_will::DropSlows);
    }
};

namespace
{
    boss_wolf_master_nandos_rework* FindNandosAI(ChatHandler* handler)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_NANDOS);
        if (!boss)
            return nullptr;
        auto* ai = dynamic_cast<boss_wolf_master_nandos_rework*>(boss->AI());
        if (!ai)
            handler->SendErrorMessage("Nandos is not running boss_wolf_master_nandos_rework (instance not bound?).");
        return ai;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_NANDOS, BOSS_NANDOS);
    }

    // `.sfktest nandos pack`: each wolf, Pack Bond and the inherited set.
    bool HandlePack(ChatHandler* handler)
    {
        boss_wolf_master_nandos_rework* ai = FindNandosAI(handler);
        if (!ai)
            return false;
        for (Creature* wolf : Pack(ai->Self()))
            handler->PSendSysMessage("{} ({}): {} {}/{}{}", wolf->GetName(), wolf->GetEntry(),
                wolf->IsAlive() ? "alive" : "dead", wolf->GetHealth(), wolf->GetMaxHealth(),
                wolf->IsInCombat() ? ", in combat" : "");
        handler->PSendSysMessage("Pack Bond {}%, inherited mask {} ({} held).", ai->PackBondNow(),
            ai->Held().Mask(), ai->Held().Count());
        return true;
    }

    // `.sfktest nandos prey`: Mark the Prey on the selected player (or the GM).
    bool HandlePrey(ChatHandler* handler)
    {
        boss_wolf_master_nandos_rework* ai = FindNandosAI(handler);
        Player* prey = handler->getSelectedPlayerOrSelf();
        if (!ai || !prey)
            return false;
        ai->MarkThePrey(prey);
        handler->PSendSysMessage("Nandos marks {}.", prey->GetName());
        return true;
    }

    // `.sfktest nandos slaver`: the Slavering Worg's 8 yd Acid Slaver; `alphaslaver`: Nandos's 20 yd one.
    bool HandleSlaver(ChatHandler* handler)
    {
        Creature* wolf = SfkTest::FindBoss(handler, NPC_SFK_PACK_SLAVERING_WORG);
        if (!wolf)
            return false;
        AcidSlaver(EncounterOwner(wolf), wolf, false);
        return true;
    }

    bool HandleAlphaSlaver(ChatHandler* handler)
    {
        boss_wolf_master_nandos_rework* ai = FindNandosAI(handler);
        if (!ai)
            return false;
        AcidSlaver(ai->Self(), ai->Self(), true);
        return true;
    }

    // `.sfktest nandos howl`: the Wolfguard Worg's Guardian Howl; `alphahowl`: Nandos's.
    bool HandleHowl(ChatHandler* handler)
    {
        Creature* wolf = SfkTest::FindBoss(handler, NPC_SFK_PACK_WOLFGUARD_WORG);
        if (!wolf)
            return false;
        GuardianHowl(wolf);
        return true;
    }

    bool HandleAlphaHowl(ChatHandler* handler)
    {
        boss_wolf_master_nandos_rework* ai = FindNandosAI(handler);
        if (!ai)
            return false;
        GuardianHowl(ai->Self());
        return true;
    }

    // `.sfktest nandos will`: one inherited Wavering Will on the selected unit (or the GM).
    bool HandleWill(ChatHandler* handler)
    {
        boss_wolf_master_nandos_rework* ai = FindNandosAI(handler);
        Unit* target = handler->getSelectedUnit();
        if (!target)
            target = handler->GetPlayer();
        if (!ai || !target)
            return false;
        ai->AlphaWill(target);
        handler->PSendSysMessage("Wavering Will on {}: {} stacks.", target->GetName(),
            DungeonKit::Stacks(target, SPELL_NANDOS_WAVERING_WILL));
        return true;
    }

    // `.sfktest nandos fear`: a Lupine Terror spot at the GM's feet.
    bool HandleFear(ChatHandler* handler)
    {
        boss_wolf_master_nandos_rework* ai = FindNandosAI(handler);
        Player* gm = handler->GetPlayer();
        if (!ai || !gm)
            return false;
        ai->TestTerror(gm->GetPosition());
        return true;
    }

    // `.sfktest nandos inherit <bleak|lupine|slavering|wolfguard>`: Nandos takes that wolf's ability now (any
    // difficulty; it fires once he has a target).
    bool HandleInherit(ChatHandler* handler, std::string_view name)
    {
        boss_wolf_master_nandos_rework* ai = FindNandosAI(handler);
        if (!ai)
            return false;
        std::optional<Wolf> const wolf = WolfByName(name);
        if (!wolf)
        {
            handler->SendErrorMessage("Use bleak, lupine, slavering or wolfguard.");
            return false;
        }
        ai->Inherit(*wolf);
        handler->PSendSysMessage("Nandos inherits the {} ability (mask {}).", WolfName(*wolf), ai->Held().Mask());
        return true;
    }

    ChatCommandTable const& NandosTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
            { "pack", HandlePack, SEC_GAMEMASTER, Console::No },
            { "prey", HandlePrey, SEC_GAMEMASTER, Console::No },
            { "slaver", HandleSlaver, SEC_GAMEMASTER, Console::No },
            { "alphaslaver", HandleAlphaSlaver, SEC_GAMEMASTER, Console::No },
            { "howl", HandleHowl, SEC_GAMEMASTER, Console::No },
            { "alphahowl", HandleAlphaHowl, SEC_GAMEMASTER, Console::No },
            { "will", HandleWill, SEC_GAMEMASTER, Console::No },
            { "fear", HandleFear, SEC_GAMEMASTER, Console::No },
            { "inherit", HandleInherit, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_wolf_master_nandos_rework()
{
    RegisterDungeonReworkCreatureAI(boss_wolf_master_nandos_rework, ShadowfangKeepRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sfk_pack_wolf, ShadowfangKeepRework::kInstanceScriptName);
    RegisterSpellScript(spell_sfk_nandos_guardian_howl);
    RegisterSpellScript(spell_sfk_nandos_wavering_will);
    SfkTest::RegisterBoss("nandos", NandosTestCommands());
}
