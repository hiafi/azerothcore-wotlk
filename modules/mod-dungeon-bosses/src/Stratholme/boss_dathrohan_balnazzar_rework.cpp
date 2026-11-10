/*
 * mod-dungeon-bosses, Stratholme S7: Grand Crusader Dathrohan (10812) and Balnazzar (10813), one encounter in two
 * stages, normal and heroic. Build spec: ST 2077-2166 (build spec), ST 1769-2076 (design: pitch A "The Mask Slips",
 * pitch B "The Dreadlord", rulings 27, 28 and 31); handoff section 3.4 rows DB and BZ, section 3.5 row S7, section 3.6,
 * section 3.8 (the chamber). One script on both entries (the AI survives UpdateEntry either way). Replaces SmartAI
 * 10812 (eighteen rows: the strikes, Crusader's Hammer, the transform and its timed UpdateEntry, Shadow Shock, Mind
 * Blast, Psychic Scream, Sleep, Mind Control, the death line and summon group, the entry's revert out of combat);
 * WP-S7's SQL rev drops them. Bound by apps/dbc-tools source/npcs/stratholme/dathrohan_balnazzar.py.
 *
 * Stage 1, Dathrohan (the lie never says "the Light"; heroic: the lie wears the true looks and the claimed marker is
 * drawn for both, a Decoy, while the real answer is NoTelegraph; bots read the real one either way):
 *   DB1 Sacred Ground  first at 10 s, every 20 s (heroic 15 s): a 3 s cast. True (yell 1, gold ground): a Stack of
 *                      8 yd on him for the non-tanks; Holy Wrath strikes every non-tank outside for 40% / 50%. Lie
 *                      (yell 2, gold over shadow on normal): 40% / 50% Shadow to the non-tanks inside 10 yd.
 *   DB2 Judgment       first at 20 s, every 20 s (heroic 12 s): a 5 s mark on a random non-tank. True (yell 3): a 6 yd
 *                      Stack on them, 90% / 120% split among the non-tanks inside. Lie (yell 4): a RunOut, 40% / 50% to
 *                      the other non-tanks within 8 yd, 15% to the target.
 *   DB4 Stock kit      Crusader Strike 17281 and Holy Strike 17284 (2-7 s, then 10-20 s), melee.
 *   DB3 Unmasking      at 40%: stock 17288 (full heal, a 5 s stun on everyone), the entry becomes Balnazzar 1.5 s in
 *                      (full health, the reveal yell 5, Vampiric Aura), and as the stun ends every non-tank carries the
 *                      lie's mark: 5 s, then 30% + Weakened to every other non-tank within 8 yd (a Spread).
 * Stage 2, Balnazzar (from the stun's end):
 *   BZ1 Carrion Swarm  first at 8 s, every 15 s: a 2.5 s cast; a 60 degree, 30 yd cone from him aimed at a random
 *                      non-tank live (the registry's `to=`: the target's bot leads it; R-1-BM); the target takes 20%,
 *                      everyone else inside 40%. Heroic: a second cone at another non-tank 1.5 s after.
 *   BZ2 Inferno        first at 20 s, every 30 s: a 3.5 s cast (yell 6) on a random non-tank's spot; the meteor, 8 yd,
 *                      50% Fire; an Infernal rises there.
 *   BZ3 The Infernal   300608 (12k / 18k): the nearest player, a strike every 2 s, Immolation 5% a second within 5 yd
 *                      (heroic +1% every 5 s, to 12%); crumbles at 45 s; at most 2. Kill target over him.
 *   BZ4 Sleep          first at 14 s, every 20 s: a 2 s interruptible cast; 5 s Magic sleep, then Nightmare (30% over
 *                      6 s). Heroic: a landed Sleep also makes Nightmare pulse 10% to every player each 2 s for 6 s.
 *   BZ5 Vampiric Aura  every kit hit that lands on a player heals him 1% / 2% of his maximum health.
 *   Stock kit          Mind Blast 17287 on his victim (9-11 s, then 10-15 s; a filler that waits for the mechanics).
 *   Leash              DathrohanArena() with LeashOptions (no grips).
 *   Death              yell 7; the stock death skeletons (creature_summon_groups 10813 group 1).
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler that a cast bar pauses. The hard mode (WP-S8, the
 * Grand Lie) fights on this AI through DathrohanFight.h (GrandLie hooks; this class is its DathrohanFight). Every
 * firing logs one INFO line "strat balnazzar <mechanic> ..." (module.dungeonbosses); `.dbtest strat balnazzar
 * <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DathrohanFight.h"
#include "DathrohanLogic.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratDathrohan;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "balnazzar";

    // SetData on the Infernal: its Immolation stokes (heroic, the hard mode).
    uint32 constexpr kInfernalDataStokes = 1;
    float constexpr kFloorProbeUpYd = 2.f;
    float constexpr kFloorMaxDropYd = 4.f;

    GrandLieFactory& HardModeFactory()
    {
        static GrandLieFactory factory;
        return factory;
    }

    // The floor under a point; falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + kFloorProbeUpYd);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > kFloorMaxDropYd) ? z : floor;
    }

    // The non-tanks (the role provider's tank is exempt from DB1, DB2 and DB3).
    BossMechanics::Eligibility NonTanks()
    {
        BossMechanics::Eligibility e;
        e.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        return e;
    }

    bool IsTank(Unit const* owner, Player const* player)
    {
        return BossMechanics::GetRoleProvider().Get(owner, player) == BossMechanics::Role::Tank;
    }

    // The fight object of the boss with this guid (DathrohanFight.h), from any unit on his map.
    DathrohanFight* FightOf(WorldObject const& near, ObjectGuid boss)
    {
        Creature* creature = boss ? ObjectAccessor::GetCreature(near, boss) : nullptr;
        if (!creature || !creature->IsAlive() || !creature->IsAIEnabled)
            return nullptr;
        return dynamic_cast<DathrohanFight*>(creature->AI());
    }
}

void StratDathrohan::RegisterGrandLie(GrandLieFactory factory)
{
    HardModeFactory() = std::move(factory);
}

std::unique_ptr<GrandLie> StratDathrohan::CreateGrandLie(Creature* boss)
{
    GrandLieFactory const& factory = HardModeFactory();
    return factory ? factory(boss) : nullptr;
}

// Grand Crusader Dathrohan 10812 / Balnazzar 10813
struct boss_dathrohan_balnazzar_rework : public BossAI, public DathrohanFight
{
    explicit boss_dathrohan_balnazzar_rework(Creature* creature)
        : BossAI(creature, BOSS_BALNAZZAR), _arena(DathrohanArena(), LeashOptions(kBossLogName)),
        _queue(kCastSpacingMs) { }

    void Reset() override
    {
        _Reset();
        Cleanup(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);       // DoZoneInCombat, BOSS_BALNAZZAR IN_PROGRESS
        if (!me->IsEngaged())
            return;     // BossAI evaded

        ClearFight(false);      // a `.dbtest strat balnazzar` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_BALNAZZAR;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);

        bool const hardMode = _heroic && instance && instance->GetData(DATA_GRAND_LIE) != 0;
        if (hardMode)
            _hardMode = CreateGrandLie(me);
        bool const unmasked = me->GetEntry() == NPC_BALNAZZAR;
        if (unmasked)
            StartStageTwo();
        else
        {
            _stage = Stage::Dathrohan;
            if (!_hardMode)
                Talk(YELL_DATHROHAN_AGGRO);     // a hard mode retry pull yells only its own line (S8's OnEngage)
            StartStageOne();
        }

        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} stage={} hardmode={} handler={} at=({:.1f}, {:.1f}, {:.1f})",
                _heroic ? 1 : 0, StageName(_stage), hardMode ? 1 : 0, _hardMode ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ()));
        if (_hardMode)
            _hardMode->OnEngage(*this);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "evade", Acore::StringFormat("reason={} stage={}",
            uint32(why), StageName(_stage)));
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_BALNAZZAR_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death", Acore::StringFormat("vampiric heals={} healed={}",
            _vampiricHeals, _vampiricHealed));
        Cleanup(true);
        BossAI::JustDied(killer);           // BOSS_BALNAZZAR DONE (the instance settles the Grand Lie and its loot)
        // His revenge on the way out (stock SmartAI 10812 row 16): 25 skeletons in five packs down the hall.
        me->SummonCreatureGroup(kDeathSummonGroup);
    }

    // The Infernals join his fight; the death skeletons are stock trash (never in his summon list); the hard mode's
    // swarm stalkers are props: his summons (they go with his reset and death) but never zoned into combat.
    void JustSummoned(Creature* summon) override
    {
        if (summon->GetEntry() == kSkeletalGuardianEntry || summon->GetEntry() == kSkeletalBerserkerEntry)
            return;
        if (summon->GetEntry() == NPC_ST_SWARM)
        {
            summons.Summon(summon);
            return;
        }
        BossAI::JustSummoned(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        if (summon && summon->GetEntry() == NPC_ST_INFERNAL)
            InfernalGone(summon->GetGUID(), "died");
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        BossAI::SummonedCreatureDespawn(summon);
        if (summon && summon->GetEntry() == NPC_ST_INFERNAL)
            InfernalGone(summon->GetGUID(), "crumbled");
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
        damage = ClampMaskDamage(_stage, me->GetHealth(), damage);
        BossAI::DamageTaken(attacker, damage, type, mask);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        UpdateTransform();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        _fightMs += diff;
        if (_hardMode)
        {
            _hardMode->OnUpdate(*this, diff);
            if (!_engaged || !me->IsAlive())
                return;     // the hook ended the fight
        }

        switch (_stage)
        {
            case Stage::Dathrohan:
                if (ShouldTransform(_stage, me->GetHealthPct()))
                {
                    StartTransform(UnmaskOptions());
                    return;
                }
                if (Due(Beat::Judgment))
                {
                    if (Judgment(nullptr, std::nullopt, _heroic))
                        Done(Beat::Judgment, EveryMs(Beat::Judgment, _heroic));
                    else
                        _due[Index(Beat::Judgment)] = _fightMs + kRetryMs;
                }
                break;
            case Stage::Transform:
                return;     // the heal, the stun, the entry change: he holds
            case Stage::Balnazzar:
                UpdateStageTwo();
                break;
        }

        if (_castHeld && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            // A cast of the queue ended early (Sleep kicked): the hold ends now.
            if (_fightMs < _castHeldUntil)
                _queue.Interrupted(_fightMs);
            _castHeld = false;
        }
        if (Busy())
            return;
        RunQueue();
        if (Busy())
            return;
        if (_stage == Stage::Dathrohan)
            StockStrikes();
        DoMeleeAttackIfReady();
    }

    // ---- DathrohanFight (the hard mode's view, DathrohanFight.h) ----------------------------------------------------

    Creature* Boss() override
    {
        return me;
    }

    bool Heroic() const override
    {
        return _heroic;
    }

    Stage CurrentStage() const override
    {
        return _stage;
    }

    GrandLie* ActiveHardMode() override
    {
        return _hardMode.get();
    }

    uint64 FightMs() const override
    {
        return _fightMs;
    }

    uint64 StageTwoMs() const override
    {
        return _stage == Stage::Balnazzar && _fightMs >= _stageTwoAt ? _fightMs - _stageTwoAt : 0;
    }

    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInWorld())
                continue;
            if (!me->IsInCombatWith(player) && !_arena.Contains(player))
                continue;
            out.push_back(player);
        }
        return out;
    }

    bool Unmask(UnmaskOptions const& options) override
    {
        if (!me->IsAlive() || _stage != Stage::Dathrohan || me->GetEntry() != NPC_DATHROHAN)
            return false;
        UnmaskOptions use = options;
        if (!_engaged)
        {
            use.stun = false;       // out of combat (the Letter): the entry changes now, no stun, no marks
            use.marks = false;
        }
        StartTransform(use);
        return true;
    }

    bool CarrionSwarm(std::vector<Player*> const& forced) override
    {
        PrepareOutOfCombat();
        CarrionSpec spec = DefaultCarrion(_heroic);
        if (_hardMode)
            _hardMode->TuneCarrion(*this, spec);

        Player* first = !forced.empty() ? forced[0] : PickNonTank({});
        if (!first)
            return false;
        DungeonKit::CastBar(me, spec.barSpell, nullptr);
        _faceTarget = first->GetGUID();
        _faceUntil = _clockMs + kCarrionCastMs;
        me->SetFacingToObject(first);
        RegisterCone(first, spec);

        std::string detail = first->GetName();
        GuidSet aimed{ first->GetGUID() };
        for (uint32 i = 1; i < spec.cones; ++i)
        {
            Player* next = i < forced.size() ? forced[i] : PickNonTank(aimed);
            if (!next)
                break;
            aimed.insert(next->GetGUID());
            _pendingCones.push_back({ _clockMs + uint64(spec.secondDelayMs) * i, next->GetGUID(), spec });
            detail += Acore::StringFormat(" then {} at +{}ms", next->GetName(), spec.secondDelayMs * i);
        }
        Log("carrion-swarm", Acore::StringFormat("cones={} pct={:.0f}/{:.0f} ward={} targets={}", spec.cones,
            spec.targetPct, spec.othersPct, spec.wardAura, detail));
        return true;
    }

    bool Inferno(Player* forced) override
    {
        PrepareOutOfCombat();
        InfernoSpec spec = DefaultInferno(_heroic);
        if (_hardMode)
            _hardMode->TuneInferno(*this, spec);
        Player* target = forced ? forced : PickNonTank({});
        if (!target)
            return false;
        float const z = FloorZ(me, target->GetPositionX(), target->GetPositionY(), target->GetPositionZ());
        Position const spot(target->GetPositionX(), target->GetPositionY(), z, 0.f);

        DungeonKit::CastBar(me, SPELL_BZ_INFERNO_BAR, nullptr, YELL_BALNAZZAR_INFERNO);
        MechanicRef ref = Mechanic::Circle(me, spot, kInfernoRadius, Milliseconds(kInfernoCastMs));
        ref.Damage(spec.meteorPct).TankDamage(spec.meteorPct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_BZ_INFERNO_HIT)
            .Within(RoomBounds()).Tag(TAG_BZ_INFERNO).OnHit(VampiricOnHit("inferno"))
            .OnResolve(OnBoss([spot, spec](boss_dathrohan_balnazzar_rework& ai, BossMechanics::ResolveResult const&)
            {
                ai.RaiseInfernal(spot, spec);
            }));
        Track(ref.Handle());
        _meteors.push_back({ _clockMs + (kInfernoCastMs - kMeteorFallMs), spot });
        Log("inferno", Acore::StringFormat("target={} at=({:.1f},{:.1f}) pct={:.0f} infernal={} stokes={}",
            target->GetName(), spot.GetPositionX(), spot.GetPositionY(), spec.meteorPct, spec.infernalHealth,
            spec.stokes ? 1 : 0));
        return true;
    }

    bool SleepPlayer(Player* player, bool pulses) override
    {
        if (!player || !player->IsAlive())
            return false;
        _sleepers[player->GetGUID()] = pulses;
        return me->AddAura(SPELL_BZ_SLEEP, player) != nullptr;
    }

    std::vector<Creature*> Infernals() override
    {
        std::vector<Creature*> out;
        for (InfernalEntry const& e : _infernals)
            if (Creature* add = ObjectAccessor::GetCreature(*me, e.guid))
                if (add->IsAlive())
                    out.push_back(add);
        return out;
    }

    void VampiricHit(Unit* victim, char const* source) override
    {
        if (_stage != Stage::Balnazzar || !me->IsAlive() || !victim || !victim->IsPlayer())
            return;
        float pct = kVampiricPct(_heroic);
        if (_hardMode)
            pct = _hardMode->VampiricPct(*this, pct);
        if (pct <= 0.f)
            return;
        uint32 const heal = StratDathrohan::VampiricHeal(me->GetMaxHealth(), pct);
        me->CastCustomSpell(SPELL_BZ_VAMPIRIC_HEAL, SPELLVALUE_BASE_POINT0, static_cast<int32>(heal), me,
            TRIGGERED_FULL_MASK);
        ++_vampiricHeals;
        _vampiricHealed += heal;
        (void)source;
    }

    BossMechanics::SpotBounds RoomBounds() const override
    {
        BossMechanics::SpotBounds bounds;
        bounds.Circle(Position(kDathrohanBrazier.x, kDathrohanBrazier.y, kFloorZ, 0.f), kBoundsRadius, kBoundsZMin,
            kBoundsZMax).PathInside();
        return bounds;
    }

    void ScheduleCast(uint32 id, uint32 inMs, uint8 priority) override
    {
        if (id < kHardModeCastBase)
            return;
        _queue.Schedule(id, _fightMs + inMs, priority);
        if (std::find(_hardModeCasts.begin(), _hardModeCasts.end(), id) == _hardModeCasts.end())
            _hardModeCasts.push_back(id);
    }

    void CancelCast(uint32 id) override
    {
        _queue.Cancel(id);
    }

    void Track(MechanicHandle handle) override
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // ---- DB1 Sacred Ground ------------------------------------------------------------------------------------------

    // `heroicForm`: the heroic numbers and the perfect mask (the lie looks true; both draw the claimed shelter).
    bool SacredGround(std::optional<Truth> forced, bool heroicForm)
    {
        Truth const truth = forced ? *forced : RollTruth(urand(0, 99));
        bool const isTrue = truth == Truth::True;
        float const pct = kSacredGroundPct(heroicForm);
        DungeonKit::CastBar(me, SPELL_DB_SACRED_GROUND_BAR, nullptr,
            isTrue ? YELL_DATHROHAN_GATHER_TRUE : YELL_DATHROHAN_BOW_LIE);
        DoCastSelf(SPELL_DB_TRUE_GROUND, true);
        if (!isTrue && !heroicForm)
            DoCastSelf(SPELL_DB_LIE_GROUND, true);      // normal: the lie shows shadow under the gold

        Milliseconds const warn(kSacredGroundCastMs);
        if (isTrue)
        {
            MechanicRef ref = Mechanic::Stack(me, me, kShelterRadius, warn);
            ref.Eligible(NonTanks()).Within(RoomBounds()).Tag(TAG_DB_SACRED_GROUND)
                .OnResolve(OnBoss([pct](boss_dathrohan_balnazzar_rework& ai, BossMechanics::ResolveResult const& r)
                {
                    ai.HolyWrath(r, pct);
                }));
            if (heroicForm)
                ref.NoTelegraph();
            Track(ref.Handle());
        }
        else
        {
            MechanicRef ref = Mechanic::Circle(me, me, kEruptionRadius, warn);
            ref.Damage(pct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_DB_SHADOW_ERUPTION).Eligible(NonTanks())
                .Within(RoomBounds()).Tag(TAG_DB_SACRED_GROUND);
            if (heroicForm)
                ref.NoTelegraph();
            Track(ref.Handle());
        }
        if (heroicForm)
            DrawClaim(me, kShelterRadius, warn);
        Log("sacred-ground", Acore::StringFormat("{} heroic={} pct={:.0f}", TruthName(truth), heroicForm ? 1 : 0, pct));
        return true;
    }

    // DB1 true: the non-tanks outside the shelter at its resolve take Holy Wrath.
    void HolyWrath(BossMechanics::ResolveResult const& result, float pct)
    {
        std::vector<Candidate> players;
        for (Player* p : FightPlayers())
            players.push_back({ p->GetGUID().GetRawValue(), IsTank(me, p), p->IsAlive() });
        std::vector<uint64> sheltered;
        for (ObjectGuid const& g : result.hits)
            sheltered.push_back(g.GetRawValue());
        std::vector<uint64> const struck = HolyWrathTargets(players, sheltered);
        GuidSet targets;
        for (uint64 raw : struck)
            targets.insert(ObjectGuid(raw));
        if (!targets.empty())
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = pct;
            spec.school = SPELL_SCHOOL_HOLY;
            spec.spellId = SPELL_DB_HOLY_WRATH;
            spec.weakened = false;
            spec.tag = TAG_DB_HOLY_WRATH;
            Track(DungeonKit::RegistryHit(me, targets, spec));
        }
        Log("holy-wrath", Acore::StringFormat("sheltered={} struck={}", sheltered.size(), struck.size()));
    }

    // ---- DB2 Judgment -----------------------------------------------------------------------------------------------

    bool Judgment(Player* forced, std::optional<Truth> forcedTruth, bool heroicForm)
    {
        Player* target = forced ? forced : PickNonTank({});
        if (!target)
            return false;
        Truth const truth = forcedTruth ? *forcedTruth : RollTruth(urand(0, 99));
        bool const isTrue = truth == Truth::True;
        me->CastSpell(target, isTrue || heroicForm ? SPELL_DB_JUDGMENT_MARK : SPELL_DB_JUDGMENT_DARK_MARK, true);
        Talk(isTrue ? YELL_DATHROHAN_JUDGMENT_TRUE : YELL_DATHROHAN_JUDGMENT_LIE, target);

        Milliseconds const warn(kJudgmentMarkMs);
        ObjectGuid const targetGuid = target->GetGUID();
        if (isTrue)
        {
            float const pct = kJudgmentSharePct(heroicForm);
            MechanicRef ref = Mechanic::Stack(me, target, kJudgmentShareRadius, warn);
            ref.Eligible(NonTanks()).Within(RoomBounds()).Tag(TAG_DB_JUDGMENT)
                .OnResolve(OnBoss([targetGuid, pct](boss_dathrohan_balnazzar_rework& ai,
                    BossMechanics::ResolveResult const& r)
                {
                    ai.JudgmentShares(targetGuid, r, pct);
                }));
            if (heroicForm)
                ref.NoTelegraph();
            Track(ref.Handle());
        }
        else
        {
            float const pct = kJudgmentBurstPct(heroicForm);
            MechanicRef ref = Mechanic::RunOut(me, target, kJudgmentBurstRadius, warn);
            ref.Damage(pct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_DB_JUDGMENT_BURST).Eligible(NonTanks())
                .Within(RoomBounds()).Tag(TAG_DB_JUDGMENT)
                .OnResolve(OnBoss([targetGuid](boss_dathrohan_balnazzar_rework& ai,
                    BossMechanics::ResolveResult const&)
                {
                    ai.JudgmentOnTarget(targetGuid);
                }));
            if (heroicForm)
                ref.NoTelegraph();
            Track(ref.Handle());
        }
        if (heroicForm)
            DrawClaim(target, kJudgmentShareRadius, warn);
        Log("judgment", Acore::StringFormat("{} heroic={} target={}", TruthName(truth), heroicForm ? 1 : 0,
            target->GetName()));
        return true;
    }

    // DB2 true: the burst split evenly among the non-tanks inside the stack (and the marked player).
    void JudgmentShares(ObjectGuid targetGuid, BossMechanics::ResolveResult const& result, float pct)
    {
        Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
        if (target)
            target->RemoveAurasDueToSpell(SPELL_DB_JUDGMENT_MARK);
        std::vector<uint64> inside;
        for (ObjectGuid const& g : result.hits)
            inside.push_back(g.GetRawValue());
        Candidate marked{ targetGuid.GetRawValue(), false, target && target->IsAlive() };
        std::vector<Unit*> takers;
        for (uint64 raw : JudgmentTakers(inside, marked))
            if (Player* p = ObjectAccessor::GetPlayer(*me, ObjectGuid(raw)))
                if (p->IsAlive())
                    takers.push_back(p);
        std::vector<std::pair<ObjectGuid, uint32>> const shares = DungeonKit::SplitShares(me, takers, pct);
        std::string detail;
        for (std::size_t i = 0; i < takers.size() && i < shares.size(); ++i)
        {
            detail += Acore::StringFormat(" {}:{}", takers[i]->GetName(), shares[i].second);
            if (shares[i].second)
                me->CastCustomSpell(SPELL_DB_JUDGMENT_SHARE, SPELLVALUE_BASE_POINT0,
                    static_cast<int32>(shares[i].second), takers[i], TRIGGERED_FULL_MASK);
        }
        Log("judgment-share", Acore::StringFormat("pct={:.0f} takers={}{}", pct, takers.size(), detail));
    }

    // DB2 lie: the marked player's own 15%.
    void JudgmentOnTarget(ObjectGuid targetGuid)
    {
        Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
        if (!target)
            return;
        target->RemoveAurasDueToSpell(SPELL_DB_JUDGMENT_MARK);
        target->RemoveAurasDueToSpell(SPELL_DB_JUDGMENT_DARK_MARK);
        if (target->IsAlive())
            me->CastSpell(target, SPELL_DB_JUDGMENT_TARGET, true);
    }

    // ---- DB3 the Unmasking ------------------------------------------------------------------------------------------

    void StartTransform(UnmaskOptions const& options)
    {
        _stage = Stage::Transform;
        _transform = options;
        ClearStageOne();
        if (options.stun)
        {
            me->InterruptNonMeleeSpells(false);
            DoCastSelf(SPELL_DB_BALNAZZAR_TRANSFORM, true);     // the full heal and the 5 s stun on everyone
            _transformEntryAt = _clockMs + kTransformEntryMs;
            _transformEndAt = _clockMs + kTransformStunMs;
        }
        else
        {
            _transformEntryAt = _clockMs;
            _transformEndAt = _clockMs;
        }
        _transformEntryDone = false;
        Log("unmask", Acore::StringFormat("stun={} marks={} engaged={} health={:.1f}%", options.stun ? 1 : 0,
            options.marks ? 1 : 0, _engaged ? 1 : 0, me->GetHealthPct()));
        UpdateTransform();
    }

    void UpdateTransform()
    {
        if (_stage != Stage::Transform || !me->IsAlive())
            return;
        if (!_transformEntryDone && _clockMs >= _transformEntryAt)
        {
            _transformEntryDone = true;
            me->UpdateEntry(NPC_BALNAZZAR);         // the AI stays; Talk now reads 10813's groups
            me->SetFullHealth();
            DoCastSelf(SPELL_BZ_VAMPIRIC_AURA, true);
            if (_transform.yell)
                Talk(YELL_BALNAZZAR_TRANSFORM);
            if (_engaged)
                Describe(Stage::Balnazzar);
            Log("unmask-entry", Acore::StringFormat("max health={}", me->GetMaxHealth()));
        }
        if (_transformEntryDone && _clockMs >= _transformEndAt)
        {
            if (_transform.marks && _engaged)
                Unmasking();
            if (_engaged)
                StartStageTwo();
            else
                _stage = Stage::Balnazzar;      // the Letter out of combat: stage 2 starts at the pull
        }
    }

    // As the stun ends: every non-tank carries the lie's mark; 5 s, then 30% + Weakened to every other non-tank
    // within 8 yd.
    void Unmasking()
    {
        uint32 marked = 0;
        for (Player* p : FightPlayers())
            if (!IsTank(me, p))
            {
                me->CastSpell(p, SPELL_DB_UNMASKING_MARK, true);
                ++marked;
            }
        MechanicRef ref = Mechanic::Spread(me, kUnmaskingRadius, Milliseconds(kUnmaskingMarkMs));
        ref.Damage(kUnmaskingPct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_DB_UNMASKING_BURST).Weakened()
            .Eligible(NonTanks()).Within(RoomBounds()).Tag(TAG_DB_UNMASKING);
        Track(ref.Handle());
        Log("unmasking", Acore::StringFormat("marked={} pct={:.0f}", marked, kUnmaskingPct));
    }

    // ---- Stage 2 ----------------------------------------------------------------------------------------------------

    // BZ1: one tracking cone at `target` (the registry's `to=`; the target is not a carrier).
    void RegisterCone(Player* target, CarrionSpec const& spec)
    {
        std::vector<uint64> players;
        for (Player* p : FightPlayers())
            players.push_back(p->GetGUID().GetRawValue());
        BossMechanics::Eligibility e;
        for (uint64 raw : ConeCarriers(players, target->GetGUID().GetRawValue()))
            e.carriers.insert(ObjectGuid(raw));
        if (e.carriers.empty())
            e.carriers.insert(ObjectGuid::Empty);
        if (spec.wardAura)
        {
            e.auraSpell = spec.wardAura;
            e.maxStacks = 0;
        }
        BossMechanics::ZoneSpec zone = BossMechanics::Shapes::Cone(me, kCarrionAngleDeg, kCarrionLengthYd);
        zone.to = BossMechanics::Anchor(target);
        ObjectGuid const targetGuid = target->GetGUID();
        float const targetPct = spec.targetPct;
        uint32 const targetSpell = spec.targetSpell;
        uint32 const ward = spec.wardAura;
        MechanicRef ref = Mechanic::Zone(me, zone, Milliseconds(kCarrionCastMs));
        ref.Damage(spec.othersPct).TankDamage(spec.othersPct).School(SPELL_SCHOOL_SHADOW).Spell(spec.hitSpell)
            .Eligible(e).Within(RoomBounds()).Tag(TAG_BZ_CARRION).OnHit(VampiricOnHit("carrion-swarm"))
            .OnResolve(OnBoss([targetGuid, targetPct, targetSpell, ward](boss_dathrohan_balnazzar_rework& ai,
                BossMechanics::ResolveResult const&)
            {
                ai.CarrionOnTarget(targetGuid, targetPct, targetSpell, ward);
            }));
        Track(ref.Handle());
    }

    // BZ1: the target's own 20% (it leads the cone; not avoidable, so no Weakened).
    void CarrionOnTarget(ObjectGuid targetGuid, float pct, uint32 spellId, uint32 ward)
    {
        Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
        if (!target || !target->IsAlive() || (ward && target->HasAura(ward)))
            return;
        me->CastCustomSpell(spellId, SPELLVALUE_BASE_POINT0, static_cast<int32>(DungeonKit::RefFlatOn(me, target, pct)),
            target, TRIGGERED_FULL_MASK);
        VampiricHit(target, "carrion-target");
    }

    // BZ2 / BZ3: the meteor landed: an Infernal rises on the spot (the oldest crumbles past the cap).
    void RaiseInfernal(Position const& spot, InfernoSpec const& spec)
    {
        std::vector<Creature*> alive = Infernals();
        for (uint32 i = 0, n = InfernalsToCrumble(uint32(alive.size())); i < n && i < alive.size(); ++i)
            alive[i]->DespawnOrUnsummon();
        DungeonKit::WaveSpec wave;
        wave.entry = NPC_ST_INFERNAL;
        wave.health = spec.infernalHealth;
        wave.type = TEMPSUMMON_TIMED_DESPAWN;
        wave.despawn = Milliseconds(kInfernalLifeMs);
        bool const stokes = spec.stokes;
        wave.onSummon = [stokes](Creature* add)
        {
            if (add->IsAIEnabled)
                add->AI()->SetData(kInfernalDataStokes, stokes ? 1 : 0);
        };
        Position at = spot;
        at.SetOrientation(me->GetAngle(&spot));
        std::vector<Creature*> const risen = DungeonKit::SummonWave(me, wave, { at }, summons);
        for (Creature* add : risen)
        {
            MechanicRef ref = Mechanic::Circle(me, add, kImmolationRadius, Milliseconds(kImmolationTickMs));
            ref.Persistent(Milliseconds(kInfernalLifeMs - kImmolationTickMs), Milliseconds(kImmolationTickMs))
                .Within(RoomBounds()).Tag(TAG_BZ_IMMOLATION);
            MechanicHandle const handle = ref.Handle();
            _infernals.push_back({ add->GetGUID(), handle });
            Log("infernal", Acore::StringFormat("at=({:.1f},{:.1f}) health={} stokes={} alive={}",
                spot.GetPositionX(), spot.GetPositionY(), add->GetMaxHealth(), stokes ? 1 : 0, _infernals.size()));
        }
    }

    void InfernalGone(ObjectGuid guid, char const* why)
    {
        for (auto it = _infernals.begin(); it != _infernals.end(); ++it)
        {
            if (it->guid != guid)
                continue;
            if (it->zone)
                Mechanic::Cancel(me, it->zone);
            _infernals.erase(it);
            Log("infernal-gone", Acore::StringFormat("why={} alive={}", why, _infernals.size()));
            return;
        }
    }

    // BZ4: a 2 s cast on a random non-tank in reach (the interrupt list). False when it could not start.
    bool Sleep(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            rule.maxRange = kSleepRangeYd;
            rule.requireLos = true;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return false;
        if (me->CastSpell(target, SPELL_BZ_SLEEP, false) != SPELL_CAST_OK)
            return false;
        Mechanic::NoteNextCastIn(me, SPELL_BZ_SLEEP, Milliseconds(kSleepEveryMs));
        Log("sleep", Acore::StringFormat("target={} heroic={}", target->GetName(), _heroic ? 1 : 0));
        return true;
    }

    // BZ4: the sleep landed (a cast, or SleepPlayer). A landed cast pulses on heroic.
    void SleepLanded(Player* sleeper)
    {
        auto [it, added] = _sleepers.try_emplace(sleeper->GetGUID(), _heroic);
        Log("sleep-landed", Acore::StringFormat("sleeper={} pulses={}", sleeper->GetName(), it->second ? 1 : 0));
        (void)added;
    }

    // BZ4: the sleep ended by time or by a dispel: Nightmare (and on a heroic miss its pulses).
    void SleepEnded(Player* sleeper, bool dispelled)
    {
        bool pulses = false;
        auto it = _sleepers.find(sleeper->GetGUID());
        if (it != _sleepers.end())
        {
            pulses = it->second;
            _sleepers.erase(it);
        }
        if (!sleeper->IsAlive())
            return;
        me->CastSpell(sleeper, SPELL_BZ_NIGHTMARE, true);
        if (pulses)
            _pulses.push_back({ sleeper->GetGUID(), _clockMs + kNightmarePulseEveryMs, kNightmarePulses });
        Log("nightmare", Acore::StringFormat("sleeper={} dispelled={} pulses={}", sleeper->GetName(),
            dispelled ? 1 : 0, pulses ? 1 : 0));
    }

    // ---- `.dbtest strat balnazzar` entry points ---------------------------------------------------------------------

    bool HeroicMap() const
    {
        return DungeonKit::IsHeroicMap(me);
    }

    bool TestGround(std::optional<Truth> truth, bool heroicForm)
    {
        PrepareOutOfCombat();
        return SacredGround(truth, heroicForm);
    }

    bool TestJudgment(Player* target, std::optional<Truth> truth, bool heroicForm)
    {
        PrepareOutOfCombat();
        return Judgment(target, truth, heroicForm);
    }

    void TestUnmasking()
    {
        PrepareOutOfCombat();
        Unmasking();
    }

    bool TestSleep(Player* target)
    {
        PrepareOutOfCombat();
        return Sleep(target);
    }

    std::string TestState()
    {
        std::string out = Acore::StringFormat("entry={} stage={} engaged={} heroic={} hardmode={} t={}ms stage2={}ms "
            "infernals={} sleepers={} pulses={} vampiric heals={} healed={}", me->GetEntry(), StageName(_stage),
            _engaged ? 1 : 0, _heroic ? 1 : 0, _hardMode ? 1 : 0, _fightMs, StageTwoMs(), _infernals.size(),
            _sleepers.size(), _pulses.size(), _vampiricHeals, _vampiricHealed);
        for (std::size_t i = 0; i < kBeatCount; ++i)
        {
            Beat const b = static_cast<Beat>(i);
            uint32 const cast = CastOf(b);
            std::optional<uint64> const due = cast ? _queue.DueAt(cast) : std::optional<uint64>(_due[i]);
            if (due)
                out += Acore::StringFormat("\n  {} due {}ms", BeatName(b), *due);
        }
        return out;
    }

private:
    struct InfernalEntry
    {
        ObjectGuid guid;
        MechanicHandle zone;
    };

    struct PendingCone
    {
        uint64 at = 0;              // _clockMs
        ObjectGuid target;
        CarrionSpec spec;
    };

    struct Meteor
    {
        uint64 at = 0;              // _clockMs
        Position spot;
    };

    struct Pulse
    {
        ObjectGuid sleeper;
        uint64 nextAt = 0;          // _clockMs
        uint32 left = 0;
    };

    static std::size_t Index(Beat b)
    {
        return static_cast<std::size_t>(b);
    }

    bool Due(Beat b) const
    {
        return _fightMs >= _due[Index(b)];
    }

    void Done(Beat b, uint32 everyMs)
    {
        _due[Index(b)] = NextDue(_due[Index(b)], _fightMs, everyMs);
    }

    // A `.dbtest` mechanic out of combat reads the map's difficulty.
    void PrepareOutOfCombat()
    {
        if (!_engaged)
            _heroic = HeroicMap();
    }

    Player* PickNonTank(GuidSet const& exclude)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = exclude.empty();     // a solo tank (a test) still gets the first pick
        DungeonKit::ExcludeGuids(rule, exclude);
        return DungeonKit::PickPlayer(me, rule);
    }

    // Heroic: the claimed marker, drawn like the true answer (the get-in color), hitting nobody; bots never see it.
    void DrawClaim(Unit* anchor, float radius, Milliseconds warn)
    {
        MechanicRef claim = Mechanic::Circle(me, anchor, radius, warn);
        claim.Decoy().Color(BossMechanics::Color::Blue).Tag(TAG_DB_CLAIM);
        Track(claim.Handle());
    }

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnBoss(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_dathrohan_balnazzar_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    // BZ5 on a registry hit (the cones, the meteor).
    std::function<void(Unit*)> VampiricOnHit(char const* source)
    {
        ObjectGuid const guid = me->GetGUID();
        return [guid, source](Unit* hit)
        {
            if (!hit)
                return;
            if (DathrohanFight* fight = FightOf(*hit, guid))
                fight->VampiricHit(hit, source);
        };
    }

    void Describe(Stage stage)
    {
        // Boss data (build spec): stage 1 him; stage 2 kill the Infernal, then him; interrupt Sleep (a reward on
        // normal, expected on heroic); dispel its sleep (Magic, urgent: loss of control). Nightmare is not dispellable.
        BossMechanics::Descriptor d;
        if (stage == Stage::Balnazzar)
        {
            d.targets.emplace_back(NPC_ST_INFERNAL, 3, BossMechanics::Who::Dps);
            d.targets.emplace_back(NPC_BALNAZZAR, 1, BossMechanics::Who::Any);
            d.interrupts.emplace_back(NPC_BALNAZZAR, SPELL_BZ_SLEEP, 2, Milliseconds(kSleepEveryMs));
            d.dispels.emplace_back(SPELL_BZ_SLEEP, 2, true);
        }
        else
            d.targets.emplace_back(NPC_DATHROHAN, 1, BossMechanics::Who::Any);
        Mechanic::Describe(me, std::move(d));
    }

    void StartStageOne()
    {
        _stage = Stage::Dathrohan;
        _queue.Schedule(CAST_SACRED_GROUND, _fightMs + FirstAt(Beat::SacredGround), PriorityOf(Beat::SacredGround));
        _due[Index(Beat::Judgment)] = _fightMs + FirstAt(Beat::Judgment);
        _due[Index(Beat::CrusaderStrike)] = _fightMs + urand(kStrikeFirstMinMs, kStrikeFirstMaxMs);
        _due[Index(Beat::HolyStrike)] = _fightMs + urand(kStrikeFirstMinMs, kStrikeFirstMaxMs);
        Describe(Stage::Dathrohan);
    }

    void StartStageTwo()
    {
        _stage = Stage::Balnazzar;
        _stageTwoAt = _fightMs;
        _queue.Reset();
        for (uint32 id : _hardModeCasts)
            _queue.Cancel(id);
        _hardModeCasts.clear();
        for (Beat b : { Beat::CarrionSwarm, Beat::Inferno, Beat::Sleep })
            _queue.Schedule(CastOf(b), _fightMs + FirstAt(b), PriorityOf(b));
        _queue.Schedule(CAST_MIND_BLAST, _fightMs + urand(kMindBlastFirstMinMs, kMindBlastFirstMaxMs), 0);
        if (!me->HasAura(SPELL_BZ_VAMPIRIC_AURA))
            DoCastSelf(SPELL_BZ_VAMPIRIC_AURA, true);
        Describe(Stage::Balnazzar);
        Log("stage-two", Acore::StringFormat("heroic={} health={}", _heroic ? 1 : 0, me->GetMaxHealth()));
    }

    // Stage 1's pending mechanics and marks go when the mask comes off.
    void ClearStageOne()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _queue.Reset();
        if (instance)
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_DB_JUDGMENT_MARK);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_DB_JUDGMENT_DARK_MARK);
        }
    }

    // Stage 2's own clocks: the second cones (and his facing while a cone tracks), the meteor looks, the pulses.
    void UpdateStageTwo()
    {
        if (_faceTarget && _clockMs < _faceUntil)
        {
            if (Player* target = ObjectAccessor::GetPlayer(*me, _faceTarget))
                me->SetFacingToObject(target);      // the fan look follows his facing
        }
        else
            _faceTarget.Clear();

        for (auto it = _pendingCones.begin(); it != _pendingCones.end();)
        {
            if (_clockMs < it->at)
            {
                ++it;
                continue;
            }
            Player* target = ObjectAccessor::GetPlayer(*me, it->target);
            if (target && target->IsAlive())
                RegisterCone(target, it->spec);
            it = _pendingCones.erase(it);
        }

        for (auto it = _meteors.begin(); it != _meteors.end();)
        {
            if (_clockMs < it->at)
            {
                ++it;
                continue;
            }
            me->CastSpell(it->spot.GetPositionX(), it->spot.GetPositionY(), it->spot.GetPositionZ(),
                SPELL_BZ_INFERNO_LOOK, true);
            it = _meteors.erase(it);
        }

        for (auto it = _pulses.begin(); it != _pulses.end();)
        {
            if (_clockMs < it->nextAt)
            {
                ++it;
                continue;
            }
            NightmarePulse(it->sleeper);
            if (--it->left == 0)
                it = _pulses.erase(it);
            else
            {
                it->nextAt += kNightmarePulseEveryMs;
                ++it;
            }
        }
    }

    // BZ4 heroic: one pulse of a missed Sleep's Nightmare: 10% to every player of the fight.
    void NightmarePulse(ObjectGuid sleeper)
    {
        GuidSet targets;
        for (Player* p : FightPlayers())
            targets.insert(p->GetGUID());
        if (targets.empty())
            return;
        DungeonKit::RegistryHitSpec spec;
        spec.pct = kNightmarePulsePct;
        spec.tankPct = kNightmarePulsePct;
        spec.school = SPELL_SCHOOL_SHADOW;
        spec.spellId = SPELL_BZ_NIGHTMARE_PULSE;
        spec.weakened = false;
        spec.tag = TAG_BZ_NIGHTMARE;
        spec.onHit = VampiricOnHit("nightmare-pulse");
        Track(DungeonKit::RegistryHit(me, targets, spec));
        Player* from = ObjectAccessor::GetPlayer(*me, sleeper);
        Log("nightmare-pulse", Acore::StringFormat("sleeper={} players={}", from ? from->GetName() : "gone",
            targets.size()));
    }

    // A cast bar of his, or a cast of the queue holding him.
    bool Busy() const
    {
        return me->HasUnitState(UNIT_STATE_CASTING) || _fightMs < _holdUntil;
    }

    // The cast queue: Sacred Ground (stage 1), the cones, the meteor, Sleep and the Mind Blast filler (stage 2), and
    // the hard mode's casts; one at a time.
    void RunQueue()
    {
        uint64 const now = _fightMs;
        std::optional<uint32> const next = _queue.Next(now);
        if (!next)
            return;
        uint32 const id = *next;

        if (id >= kHardModeCastBase)
        {
            std::optional<uint32> const holdMs = _hardMode ? _hardMode->OnCast(*this, id) : std::nullopt;
            if (!holdMs)
            {
                _queue.Cancel(id);
                return;
            }
            _queue.Started(id, now, *holdMs);
            _holdUntil = now + *holdMs;
            return;
        }

        if (id == CAST_MIND_BLAST)
        {
            // The filler waits for the mechanics (R-1-B N-1): never started when one falls due within its cast time.
            for (uint32 other : { uint32(CAST_CARRION_SWARM), uint32(CAST_INFERNO), uint32(CAST_SLEEP) })
                if (std::optional<uint64> const due = _queue.DueAt(other); due && FillerWaits(now, *due))
                    return;
            for (uint32 other : _hardModeCasts)
                if (std::optional<uint64> const due = _queue.DueAt(other); due && FillerWaits(now, *due))
                    return;
            if (_hardMode && !_hardMode->AllowBeat(*this, Beat::MindBlast))
            {
                _queue.Schedule(CAST_MIND_BLAST, now + kMeleeRetryMs, 0);
                return;
            }
            Unit* victim = me->GetVictim();
            if (victim && me->CastSpell(victim, SPELL_MIND_BLAST_BALNAZZAR, false) == SPELL_CAST_OK)
            {
                _queue.Started(CAST_MIND_BLAST, now, kMindBlastCastMs, false);
                _queue.Schedule(CAST_MIND_BLAST, now + urand(kMindBlastMinMs, kMindBlastMaxMs), 0);
            }
            else
                _queue.Schedule(CAST_MIND_BLAST, now + kRetryMs, 0);
            return;
        }

        Beat const beat = BeatOfCast(id);
        uint8 const priority = PriorityOf(beat);
        if (IsStageTwoBeat(beat) && _hardMode && !_hardMode->AllowBeat(*this, beat))
        {
            _queue.Schedule(id, now + kMeleeRetryMs, priority);     // held: asked again in a second
            return;
        }
        uint64 const due = _queue.DueAt(id).value_or(now);
        bool started = false;
        switch (beat)
        {
            case Beat::SacredGround: started = SacredGround(std::nullopt, _heroic); break;
            case Beat::CarrionSwarm: started = CarrionSwarm({}); break;
            case Beat::Inferno: started = Inferno(nullptr); break;
            case Beat::Sleep: started = Sleep(nullptr); break;
            default: break;
        }
        if (!started)
        {
            _queue.Schedule(id, now + kRetryMs, priority);
            return;
        }
        uint32 every = EveryMs(beat, _heroic);
        if (_hardMode && IsStageTwoBeat(beat))
            every = _hardMode->BeatEveryMs(*this, beat, every);
        uint32 const castMs = CastMsOf(id);
        _queue.Started(id, now, castMs);
        _queue.Schedule(id, NextDue(due, now, every), priority);
        _castHeld = true;
        _castHeldUntil = now + castMs;
    }

    // DB4: Crusader Strike and Holy Strike on his victim in melee range (stage 1).
    void StockStrikes()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return;
        bool const inReach = me->IsWithinMeleeRange(victim);
        for (Beat b : { Beat::CrusaderStrike, Beat::HolyStrike })
        {
            if (!Due(b))
                continue;
            uint32 const spell = b == Beat::CrusaderStrike ? SPELL_CRUSADER_STRIKE : SPELL_HOLY_STRIKE;
            if (inReach && DoCastVictim(spell) == SPELL_CAST_OK)
                _due[Index(b)] = _fightMs + urand(kStrikeMinMs, kStrikeMaxMs);
            else
                _due[Index(b)] = _fightMs + kMeleeRetryMs;
            return;
        }
    }

    // The pull's state, gone (`revert`: back to Dathrohan, the entry's own template health).
    void ClearFight(bool revert)
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (InfernalEntry const& e : _infernals)
        {
            if (e.zone)
                Mechanic::Cancel(me, e.zone);
            if (Creature* add = ObjectAccessor::GetCreature(*me, e.guid))
                add->DespawnOrUnsummon();
        }
        _infernals.clear();
        _queue.Reset();
        _hardModeCasts.clear();
        _due.fill(0);
        _pendingCones.clear();
        _meteors.clear();
        _pulses.clear();
        _sleepers.clear();
        _faceTarget.Clear();
        _fightMs = 0;
        _stageTwoAt = 0;
        _holdUntil = 0;
        _castHeld = false;
        _castHeldUntil = 0;
        _vampiricHeals = 0;
        _vampiricHealed = 0;
        _engaged = false;
        _arena.Reset();
        if (instance)
            for (uint32 aura : { uint32(SPELL_DB_JUDGMENT_MARK), uint32(SPELL_DB_JUDGMENT_DARK_MARK),
                uint32(SPELL_DB_UNMASKING_MARK), uint32(SPELL_BZ_SLEEP), uint32(SPELL_BZ_NIGHTMARE) })
                instance->DoRemoveAurasDueToSpellOnPlayers(aura);
        if (revert && me->IsAlive())
        {
            if (me->GetEntry() == NPC_BALNAZZAR)
            {
                me->UpdateEntry(NPC_DATHROHAN);     // stock SmartAI 10812 row 17: out of combat, back to Dathrohan
                me->SetFullHealth();
            }
            me->RemoveAurasDueToSpell(SPELL_BZ_VAMPIRIC_AURA);
            _stage = Stage::Dathrohan;
        }
    }

    // Death, evade or reset: the hard mode's own end first, then the pull's state.
    void Cleanup(bool died)
    {
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, died);
            _hardMode.reset();
        }
        ClearFight(!died);
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CastQueue _queue;
    std::unique_ptr<GrandLie> _hardMode;
    std::vector<uint32> _hardModeCasts;     // the cast queue ids the hard mode has scheduled (the filler's wait)
    std::vector<MechanicHandle> _live;
    std::vector<InfernalEntry> _infernals;
    std::vector<PendingCone> _pendingCones;
    std::vector<Meteor> _meteors;
    std::vector<Pulse> _pulses;
    std::unordered_map<ObjectGuid, bool> _sleepers;     // asleep now: whether their Nightmare pulses
    std::array<uint64, kBeatCount> _due{};              // _fightMs: the beats without a cast (Judgment, the strikes)
    UnmaskOptions _transform;
    ObjectGuid _faceTarget;
    Stage _stage = Stage::Dathrohan;
    uint64 _clockMs = 0;            // ms the AI has run (in or out of combat; the transform, cones, meteors, pulses)
    uint64 _fightMs = 0;            // ms since the pull (the beats and the queue)
    uint64 _stageTwoAt = 0;         // _fightMs when stage 2 began
    uint64 _transformEntryAt = 0;   // _clockMs
    uint64 _transformEndAt = 0;     // _clockMs
    uint64 _faceUntil = 0;          // _clockMs
    uint64 _holdUntil = 0;          // _fightMs: a hard mode cast holds him until then
    uint64 _castHeldUntil = 0;      // _fightMs: the queue's own cast ends then
    uint64 _vampiricHealed = 0;
    uint32 _vampiricHeals = 0;
    bool _transformEntryDone = false;
    bool _castHeld = false;
    bool _heroic = false;
    bool _engaged = false;
};

// BZ3 the Infernal (300608): it fixes on the nearest player every second, strikes its victim every 2 s (206571, the
// kit's percent spell; no auto attack), and burns every player within 5 yd every second (206564: 5%, stoked on heroic
// and in the hard mode, +1% every 5 s to 12%; each tick and strike heals Balnazzar, BZ5). It crumbles at 45 s (the
// summon's timer). Its summoner is the boss.
struct npc_st_infernal : public ScriptedAI
{
    explicit npc_st_infernal(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _swingMs = kInfernalFirstSwingMs;
        _tickMs = kImmolationTickMs;
        _retargetMs = 0;
    }

    void SetData(uint32 type, uint32 value) override
    {
        if (type == kInfernalDataStokes)
            _stokes = value != 0;
    }

    void IsSummonedBy(WorldObject* summoner) override
    {
        if (summoner)
            _owner = summoner->GetGUID();
        DoCastSelf(SPELL_BZ_IMMOLATION_LOOK, true);
        Retarget();
    }

    void UpdateAI(uint32 diff) override
    {
        _ageMs += diff;
        _retargetMs = _retargetMs > diff ? _retargetMs - diff : 0;
        if (!_retargetMs)
        {
            Retarget();
            _retargetMs = kInfernalRetargetMs;
        }

        uint32 const stacks = StokeStacks(_stokes, _ageMs);
        if (stacks != _stacks)
        {
            DungeonKit::AddStacks(me, SPELL_BZ_STOKED, int32(stacks) - int32(_stacks), me);
            _stacks = stacks;
        }

        _tickMs = _tickMs > diff ? _tickMs - diff : 0;
        if (!_tickMs)
        {
            _tickMs = kImmolationTickMs;
            Immolate();
        }

        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING | UNIT_STATE_LOST_CONTROL))
            return;
        _swingMs = _swingMs > diff ? _swingMs - diff : 0;
        if (_swingMs)
            return;
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
            return;     // the swing waits for reach
        me->CastSpell(victim, SPELL_BZ_INFERNAL_STRIKE, true);
        _swingMs = kInfernalSwingMs;
        Vampiric(victim, "infernal-strike");
    }

private:
    // One Immolation tick on every living player within 5 yd (same floor).
    void Immolate()
    {
        if (!me->IsAlive())
            return;
        float const pct = ImmolationPct(_stokes, _ageMs);
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster())
                continue;
            if (me->GetExactDist2d(player) > kImmolationRadius
                || std::fabs(player->GetPositionZ() - me->GetPositionZ()) > kBoundsZMax - kBoundsZMin)
                continue;
            me->CastCustomSpell(SPELL_BZ_IMMOLATION_TICK, SPELLVALUE_BASE_POINT0,
                static_cast<int32>(DungeonKit::RefFlatOn(me, player, pct)), player, TRIGGERED_FULL_MASK);
            Vampiric(player, "immolation");
        }
    }

    void Vampiric(Unit* victim, char const* source)
    {
        if (DathrohanFight* fight = FightOf(*me, _owner))
            fight->VampiricHit(victim, source);
    }

    // The nearest living player within 60 yd: on its threat list, and fixed on.
    void Retarget()
    {
        Player* nearest = nullptr;
        float best = kInfernalNearestYd;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p || !p->IsAlive() || p->IsGameMaster())
                continue;
            float const d = me->GetDistance(p);
            if (d <= best)
            {
                best = d;
                nearest = p;
            }
        }
        if (!nearest)
            return;
        me->AddThreat(nearest, 0.f);
        me->GetThreatMgr().FixateTarget(nearest);
        if (me->GetVictim() != nearest)
            AttackStart(nearest);
    }

    ObjectGuid _owner;
    uint32 _ageMs = 0;
    uint32 _stacks = 0;
    uint32 _swingMs = kInfernalFirstSwingMs;
    uint32 _tickMs = kImmolationTickMs;
    uint32 _retargetMs = 0;
    bool _stokes = false;
};

// BZ4 Sleep (206566): the boss hears when it lands and when it ends. An expiry or a dispel (ENEMY_SPELL) starts
// Nightmare; the fight's cleanup (DEFAULT), a death or a map change does not.
class spell_strat_balnazzar_sleep : public AuraScript
{
    PrepareAuraScript(spell_strat_balnazzar_sleep);

    boss_dathrohan_balnazzar_rework* BossAI_() const
    {
        Unit* caster = GetCaster();
        Creature* boss = caster ? caster->ToCreature() : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_dathrohan_balnazzar_rework*>(boss->AI());
    }

    void OnApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* sleeper = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (auto* ai = BossAI_())
            if (sleeper)
                ai->SleepLanded(sleeper);
    }

    void OnRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        AuraRemoveMode const why = GetTargetApplication()->GetRemoveMode();
        if (why != AURA_REMOVE_BY_EXPIRE && why != AURA_REMOVE_BY_ENEMY_SPELL)
            return;
        Player* sleeper = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (auto* ai = BossAI_())
            if (sleeper)
                ai->SleepEnded(sleeper, why == AURA_REMOVE_BY_ENEMY_SPELL);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_strat_balnazzar_sleep::OnApply, EFFECT_0, SPELL_AURA_MOD_STUN,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_strat_balnazzar_sleep::OnRemove, EFFECT_0, SPELL_AURA_MOD_STUN,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// BZ4 Nightmare (206567): each tick that lands heals Balnazzar (BZ5). The tick's damage is the kit's
// spell_dungeon_refflat_periodic (bound beside this one).
class spell_strat_balnazzar_nightmare : public AuraScript
{
    PrepareAuraScript(spell_strat_balnazzar_nightmare);

    void OnTick(AuraEffect const* /*aurEff*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (!caster || !target)
            return;
        if (DathrohanFight* fight = FightOf(*caster, caster->GetGUID()))
            fight->VampiricHit(target, "nightmare");
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_strat_balnazzar_nightmare::OnTick, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

namespace
{
    // The boss in either form: the selected creature, else the instance's (DATA_DATHROHAN_GUID).
    boss_dathrohan_balnazzar_rework* FindBossAI(ChatHandler* handler)
    {
        if (!StratTest::RequireStratholme(handler))
            return nullptr;
        Creature* boss = handler->getSelectedCreature();
        if (!boss || (boss->GetEntry() != NPC_DATHROHAN && boss->GetEntry() != NPC_BALNAZZAR))
        {
            InstanceScript* instance = handler->GetPlayer() ? handler->GetPlayer()->GetInstanceScript() : nullptr;
            boss = instance ? instance->GetCreature(DATA_DATHROHAN_GUID) : nullptr;
        }
        auto* ai = boss && boss->IsAlive() && boss->IsAIEnabled
            ? dynamic_cast<boss_dathrohan_balnazzar_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Dathrohan / Balnazzar is not here, dead, or not running "
                "boss_dathrohan_balnazzar_rework (check the ScriptName).");
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    std::optional<Truth> ParseTruth(Optional<std::string> const& word)
    {
        if (word && *word == "true")
            return Truth::True;
        if (word && *word == "lie")
            return Truth::Lie;
        return std::nullopt;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        if (StratTest::ShowBossInfo(handler, NPC_DATHROHAN, BOSS_BALNAZZAR))
            return true;
        return StratTest::ShowBossInfo(handler, NPC_BALNAZZAR, BOSS_BALNAZZAR);
    }

    // `.dbtest strat balnazzar state`: the stage, the beats' due times, the Infernals, the sleepers, the heals.
    bool HandleState(ChatHandler* handler)
    {
        boss_dathrohan_balnazzar_rework* ai = FindBossAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Balnazzar: {}", ai->TestState());
        return true;
    }

    // `.dbtest strat balnazzar ground [true|lie] [0|1]`: Sacred Ground now (DB1); 1 = the heroic form.
    bool HandleGround(ChatHandler* handler, Optional<std::string> truth, Optional<uint32> heroic)
    {
        boss_dathrohan_balnazzar_rework* ai = FindBossAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        ai->TestGround(ParseTruth(truth), isHeroic);
        handler->PSendSysMessage("Balnazzar: Sacred Ground ({}) (DB1).", isHeroic ? "heroic" : "normal");
        return true;
    }

    // `.dbtest strat balnazzar judgment [true|lie] [0|1]`: Judgment on the selected player (or you) (DB2).
    bool HandleJudgment(ChatHandler* handler, Optional<std::string> truth, Optional<uint32> heroic)
    {
        boss_dathrohan_balnazzar_rework* ai = FindBossAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        ai->TestJudgment(target, ParseTruth(truth), isHeroic);
        handler->PSendSysMessage("Balnazzar: Judgment on {} (DB2).", target->GetName());
        return true;
    }

    // `.dbtest strat balnazzar unmask`: the mask comes off now (DB3; out of combat: the entry only, the Letter's way).
    bool HandleUnmask(ChatHandler* handler)
    {
        boss_dathrohan_balnazzar_rework* ai = FindBossAI(handler);
        if (!ai)
            return false;
        bool const done = ai->Unmask(UnmaskOptions());
        handler->PSendSysMessage("Balnazzar: {}", done ? "unmasking (DB3)." : "already unmasked.");
        return true;
    }

    // `.dbtest strat balnazzar unmasking`: the Unmasking marks now (DB3's Spread).
    bool HandleUnmasking(ChatHandler* handler)
    {
        boss_dathrohan_balnazzar_rework* ai = FindBossAI(handler);
        if (!ai)
            return false;
        ai->TestUnmasking();
        handler->PSendSysMessage("Balnazzar: the Unmasking marks (DB3).");
        return true;
    }

    // `.dbtest strat balnazzar carrion`: Carrion Swarm at the selected player (or you) (BZ1; heroic: a second cone).
    bool HandleCarrion(ChatHandler* handler)
    {
        boss_dathrohan_balnazzar_rework* ai = FindBossAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        bool const done = ai->CarrionSwarm({ target });
        handler->PSendSysMessage("Balnazzar: Carrion Swarm {} (BZ1).", done ? "cast" : "found nobody");
        return true;
    }

    // `.dbtest strat balnazzar inferno`: Inferno on the selected player's (or your) spot (BZ2, BZ3).
    bool HandleInferno(ChatHandler* handler)
    {
        boss_dathrohan_balnazzar_rework* ai = FindBossAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->Inferno(target);
        handler->PSendSysMessage("Balnazzar: Inferno on {} (BZ2).", target->GetName());
        return true;
    }

    // `.dbtest strat balnazzar sleep`: Sleep cast at the selected player (or you) (BZ4).
    bool HandleSleep(ChatHandler* handler)
    {
        boss_dathrohan_balnazzar_rework* ai = FindBossAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        bool const done = ai->TestSleep(target);
        handler->PSendSysMessage("Balnazzar: Sleep {} (BZ4).", done ? "cast" : "refused");
        return true;
    }

    ChatCommandTable const& DathrohanTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "ground",    HandleGround,    SEC_GAMEMASTER, Console::No },
            { "judgment",  HandleJudgment,  SEC_GAMEMASTER, Console::No },
            { "unmask",    HandleUnmask,    SEC_GAMEMASTER, Console::No },
            { "unmasking", HandleUnmasking, SEC_GAMEMASTER, Console::No },
            { "carrion",   HandleCarrion,   SEC_GAMEMASTER, Console::No },
            { "inferno",   HandleInferno,   SEC_GAMEMASTER, Console::No },
            { "sleep",     HandleSleep,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_dathrohan_balnazzar_rework()
{
    RegisterDungeonReworkCreatureAI(boss_dathrohan_balnazzar_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_infernal, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_strat_balnazzar_sleep);
    RegisterSpellScript(spell_strat_balnazzar_nightmare);
    StratTest::RegisterBoss("balnazzar", DathrohanTestCommands());
}
