/*
 * mod-dungeon-bosses, Scarlet Monastery D14H: High Inquisitor Whitemane's hard mode, The Truth (heroic only). Build
 * spec: docs/dungeons/scarlet-monastery-4-cathedral.md "High Inquisitor Fairbanks", "Hard mode (approved 2026-11-19,
 * pitch B)" and "Hard mode: The Truth" (HM0-HM5, the rows, the texts); handoff section 3.7, 3.5 row D14H,
 * section 7 #21 A, #33 A, #16 A. Pure rules: WhitemaneHardModeLogic.h. It fights on D14's AI (boss_whitemane_rework)
 * through WhitemaneFight.h and on D13's risen Mograine through MograineFight.h; it edits neither.
 *
 *   HM0 the Torch     go_sm_torch replaces the Torch's SmartAI (97701, "activate the Secret Door"). On normal (and
 *                     while wave 2 is unbound) it opens the Secret Door as stock. On heroic it works only once the Last
 *                     Stand is DONE and before Whitemane is pulled (section 7 #21 A; else "The Torch will not move."
 *                     and nothing happens): the instance lights DATA_HARD_MODE_WHITEMANE (saved; the loot bit, the kill
 *                     slot), the door opens, the stock Fairbanks fears everyone within 30 yd of the door for 5 s (out
 *                     of combat: no threat), teleports out and is gone for the lockout; Whitemane's 340k. Once lit, the
 *                     Torch stays pulled and cannot be used again
 *   The vigil         the idle hook (out of combat): while lit, Fairbanks at the vigil (300956) kneels 4 yd beside her
 *                     at the vigil (after the Torch, after a wipe, after a cold load), her health 340k; a stock
 *                     Fairbanks found alive then (a cold load, a GM arming) is sent away for the lockout too
 *   The pull          the same as without (D14: damage or a hostile cast on her, or on him); 340k; the vigil Fairbanks
 *                     joins the fight (every player at 0 threat on him); Mograine rises at 280k (RisenMaxHealth)
 *   HM1 phase 1       Fairbanks fights from where he knelt: Inquisitor's Ward (the pair takes half damage while he
 *                     lives), Curse of Blood (a Curse, 4% a second for 12 s), Power Word: Shield on the lower of the
 *                     pair (10% of its health, purgeable), Heal on the lower of the pair (3 s, 15%, interruptible); To
 *                     Her Side every 20 s, the flare every 8 s, Seared 15 s (D14's tuning hooks). The bots: Fairbanks
 *                     first
 *   HM2 the Truth     at his death ("Ask him... how his father died."): the spirit of Alexandros rises over the altar
 *                     ("Renault..."), Renault kneels 3 s ("Father... But... How?", "Forgive me, father! Please..."),
 *                     her kit holds the 3 s; then "Lies! He is the Crusade's champion!"
 *   HM3 the father    every 8 s from T + 8 s: the light twice (a 6 yd circle at a random player's spot, 2.5 s: 45% Holy
 *                     and Weakened, the tank 25% and no Weakened; Renault in it 4% of his health and a 2 s kneel), then
 *                     the Verdict (a 6 yd line from the spirit through Renault to the floor's far edge, 3.5 s, Renault
 *                     held for the marker: 55% Holy; Renault 6% and a 3 s kneel; Whitemane in it 5% and her cast
 *                     breaks, a save channel starting over). To Her Side never starts under a Verdict marker
 *   HM4 Guilt         her channel 6 s, his 4 s, his Divine Storm every 10 s; To Her Side and the flare back to heroic
 *   HM5 the ending    her death (the pair's): "You are forgiven..." and the spirit fades
 *
 * Every unit of the fight comes from WhitemaneFight::Summon or JoinFight (D14's cleanup despawns it), except the
 * spirit, a map summon of its own (so it can speak over the pair and fade after her death; OnEnd despawns it). Every
 * registry handle goes to WhitemaneFight::Track. Every firing logs one INFO line "sm whitemane truth-<mechanic> ..."
 * (module.dungeonbosses); `.dbtest sm truth ...` fires one on demand.
 *
 * Upstream credit: the Torch keeps the stock SmartAI's effect (Torch 97701 "activate the Secret Door"; DB data, no
 * named author); nothing else is mirrored.
 */

#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "GameTime.h"
#include "InstanceScript.h"
#include "LastStandLogic.h"
#include "Map.h"
#include "MograineFight.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WhitemaneFight.h"
#include "WhitemaneHardModeLogic.h"
#include "WhitemaneLogic.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmTheTruth;
using BossMechanics::MechanicRef;
using SmLastStand::MograineFight;
using SmLastStand::MograineKit;
using SmWhitemane::WhitemaneFight;

namespace
{
    char const* const kBoss = "whitemane";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(static_cast<int64>(ms));
    }

    uint64 NowMs()
    {
        return static_cast<uint64>(GameTime::GetGameTimeMS().count());
    }

    // "sm whitemane truth-<mechanic> <detail>" (the fight's own log prefix: D14's Log does the same).
    void LogTt(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    Vec2 PlaneOf(WorldObject const* o)
    {
        return { o->GetPositionX(), o->GetPositionY() };
    }

    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // Create health is the base the engine rebuilds max health from (the Baron's, Ras's and Herod's hard mode pattern).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    // The health its template gives it (the heroic copy's on heroic: H's 220k for her).
    uint32 TemplateHealth(Creature* creature)
    {
        CreatureTemplate const* t = creature->GetCreatureTemplate();
        CreatureBaseStats const* stats = t ? sObjectMgr->GetCreatureBaseStats(creature->GetLevel(), t->unit_class)
            : nullptr;
        return stats ? stats->GenerateHealth(t) : creature->GetCreateHealth();
    }

    // The floor under a point; falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + 2.f);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > 4.f) ? z : floor;
    }

    // The bots' hard bounds while a mechanic of the fight is in view (D14's floor: WhitemaneLogic.h kFloorBoxes).
    BossMechanics::SpotBounds FloorBounds()
    {
        BossMechanics::SpotBounds bounds;
        float const z = kWhitemaneVigil.z;
        for (SmWhitemane::Box const& b : SmWhitemane::kFloorBoxes)
            bounds.Polygon({ Position(b.minX, b.minY, z, 0.f), Position(b.maxX, b.minY, z, 0.f),
                Position(b.maxX, b.maxY, z, 0.f), Position(b.minX, b.maxY, z, 0.f) }, SmWhitemane::kFloorZMin,
                SmWhitemane::kFloorZMax);
        return bounds;
    }

    void Notify(Player* player, char const* text)
    {
        if (player && player->GetSession() && text && *text)
            ChatHandler(player->GetSession()).SendNotification(text);
    }

    void UnitTalk(Creature* creature, uint8 group, WorldObject const* target = nullptr)
    {
        if (creature && creature->IsAIEnabled)
            creature->AI()->Talk(group, target);
    }

    // D14's AI as the hard mode sees it (nullptr when she does not run boss_whitemane_rework).
    WhitemaneFight* WhitemaneFightOf(WorldObject const* any)
    {
        InstanceScript* instance = any ? any->GetInstanceScript() : nullptr;
        Creature* her = instance ? ObjectAccessor::GetCreature(*any, instance->GetGuidData(DATA_WHITEMANE)) : nullptr;
        return her && her->IsAIEnabled ? dynamic_cast<WhitemaneFight*>(her->AI()) : nullptr;
    }

    Creature* StockFairbanks(InstanceScript* instance, WorldObject const* near)
    {
        return instance && near ? ObjectAccessor::GetCreature(*near, instance->GetGuidData(kGuidFairbanks)) : nullptr;
    }

    // He stands in the finale: alive, risen, not down (WM1a).
    bool IsUp(MograineFight* m)
    {
        Creature* c = m ? m->Mograine() : nullptr;
        return c && c->IsAlive() && m->State() == SmLastStand::MograineState::Risen && !m->IsDown();
    }

    // Risen (down included) and alive: his storm's cadence, the ward's look, the Verdict's aim.
    bool IsRisen(MograineFight* m)
    {
        Creature* c = m ? m->Mograine() : nullptr;
        return c && c->IsAlive() && m->State() == SmLastStand::MograineState::Risen;
    }

    // `pct` of `victim`'s maximum health (the father's hits on the pair are a percent of its own health: ruling 53, SYS
    // SM2). No attacker: nobody's threat; the pair's lethal rules (D14) still see it.
    uint32 DealPercent(Unit* victim, float pct)
    {
        if (!victim || !victim->IsAlive())
            return 0;
        uint32 const amount = std::max<uint32>(1, static_cast<uint32>(static_cast<float>(victim->GetMaxHealth())
            * pct / 100.f));
        Unit::DealDamage(nullptr, victim, amount, nullptr, DIRECT_DAMAGE, SPELL_SCHOOL_MASK_HOLY, nullptr, false);
        return amount;
    }

    // Renault kneels in shame: D13's Kneel plus the look (the aura's time is the kneel's).
    void ShameKneel(MograineFight* m, uint32 ms, char const* why)
    {
        if (!IsUp(m))
            return;
        m->Kneel(ms, why);
        Creature* c = m->Mograine();
        if (Aura* aura = c->AddAura(SPELL_TT_SHAME, c))
        {
            aura->SetMaxDuration(static_cast<int32>(ms));
            aura->SetDuration(static_cast<int32>(ms));
        }
    }

    // The Secret Door (instance ObjectData; the nearest one as a fallback).
    void OpenSecretDoor(InstanceScript* instance, WorldObject* near)
    {
        if (!instance)
            return;
        ObjectGuid const guid = instance->GetGuidData(GO_SECRET_DOOR);
        GameObject* door = guid ? instance->instance->GetGameObject(guid) : nullptr;
        if (!door && near)
            door = near->FindNearestGameObject(GO_SECRET_DOOR, 20.f);
        if (door)
            instance->HandleGameObject(ObjectGuid::Empty, true, door);
    }

    // The vigil Fairbanks near her (alive).
    Creature* FindVigilFairbanks(Creature* her)
    {
        return her ? her->FindNearestCreature(NPC_SM_VIGIL_FAIRBANKS, kVigilSearchYd, true) : nullptr;
    }

    // Summons the vigil Fairbanks (her summon: D14's cleanup despawns it) kneeling at `at`.
    Creature* SummonVigilFairbanks(WhitemaneFight& fight, Point4 const& at, bool look)
    {
        Creature* her = fight.Whitemane();
        Position const spot(at.x, at.y, FloorZ(her, at.x, at.y, at.z), at.o);
        Creature* fairbanks = fight.Summon(NPC_SM_VIGIL_FAIRBANKS, spot);
        if (!fairbanks)
            return nullptr;
        fairbanks->SetHomePosition(spot);
        fairbanks->SetReactState(REACT_PASSIVE);
        fairbanks->SetFacingTo(at.o);
        fairbanks->SetStandState(UNIT_STAND_STATE_KNEEL);
        if (look)
            fairbanks->CastSpell(fairbanks, SPELL_TT_TELEPORT_IN, true);
        return fairbanks;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The idle hook (WhitemaneFight.h RegisterWhitemaneIdleHook): every AI tick out of combat while she lives
    // ----------------------------------------------------------------------------------------------------------------

    // The idle hook's pace per Whitemane (lit instances only; erased at her death). Instances update on several map
    // threads: every access holds IdleReadyAtLock().
    std::unordered_map<ObjectGuid, uint64>& IdleReadyAt()
    {
        static std::unordered_map<ObjectGuid, uint64> readyAt;
        return readyAt;
    }

    std::mutex& IdleReadyAtLock()
    {
        static std::mutex lock;
        return lock;
    }

    // True when the idle hook may run now (and paces the next run).
    bool IdlePaced(ObjectGuid const& her, uint64 now)
    {
        std::lock_guard<std::mutex> guard(IdleReadyAtLock());
        uint64& readyAt = IdleReadyAt()[her];
        if (now < readyAt)
            return false;
        readyAt = now + kIdlePollMs;
        return true;
    }

    void ForgetIdlePace(ObjectGuid const& her)
    {
        std::lock_guard<std::mutex> guard(IdleReadyAtLock());
        IdleReadyAt().erase(her);
    }

    // While lit (heroic): her 340k, the stock Fairbanks gone, the vigil Fairbanks kneeling beside her at the vigil.
    // `force`: the GM test (no pace). Returns a short line of what it did (the test prints it).
    std::string IdleTruth(WhitemaneFight& fight, bool force)
    {
        Creature* her = fight.Whitemane();
        if (!her || !her->IsAlive() || her->IsEngaged() || !DungeonKit::IsHeroicMap(her))
            return "not heroic, dead or fighting";
        InstanceScript* instance = her->GetInstanceScript();
        if (!instance || !instance->GetData(DATA_HARD_MODE_WHITEMANE))
            return "the Torch is not lit";
        uint64 const now = NowMs();
        if (!force && !IdlePaced(her->GetGUID(), now))
            return {};
        if (her->GetCreateHealth() != kWhitemaneHealth)
        {
            SetCreatureHealth(her, kWhitemaneHealth);
            LogTt("truth-health", Acore::StringFormat("whitemane={}", her->GetMaxHealth()));
        }
        if (fight.State() != SmWhitemane::WhitemaneState::Vigil)
            return "she is not at her vigil yet";
        if (Creature* stock = StockFairbanks(instance, her))
            if (stock->IsAlive())
            {
                if (stock->HasAura(SPELL_TT_TELEPORT_OUT))
                    return "the stock Fairbanks is leaving";
                stock->DespawnOrUnsummon(0ms, Seconds(kLockoutRespawnSeconds));
                LogTt("truth-stock-gone", "a stock Fairbanks alive while lit (a cold load or a GM arming): sent away");
                return "the stock Fairbanks sent away";
            }
        Point4 const spot = VigilFairbanksSpot();
        Creature* fairbanks = FindVigilFairbanks(her);
        if (!fairbanks)
        {
            fairbanks = SummonVigilFairbanks(fight, spot, true);
            LogTt("truth-vigil", Acore::StringFormat("summoned={} at=({:.1f}, {:.1f})", fairbanks ? 1 : 0, spot.x,
                spot.y));
            return fairbanks ? "the vigil Fairbanks kneels beside her" : "the vigil Fairbanks could not be summoned";
        }
        if (fairbanks->IsEngaged() || fairbanks->IsInEvadeMode())
            return "the vigil Fairbanks is busy";
        if (fairbanks->GetExactDist2d(spot.x, spot.y) > kVigilPlacedYd)
        {
            if (fairbanks->movespline->Finalized())
                fairbanks->GetMotionMaster()->MovePoint(0, spot.x, spot.y, FloorZ(her, spot.x, spot.y, spot.z));
            return "the vigil Fairbanks walks back to her side";
        }
        if (fairbanks->getStandState() != UNIT_STAND_STATE_KNEEL)
        {
            fairbanks->SetFacingTo(spot.o);
            fairbanks->SetStandState(UNIT_STAND_STATE_KNEEL);
        }
        return "the vigil Fairbanks kneels beside her";
    }
}

// -------------------------------------------------------------------------------------------------------------------
// High Inquisitor Fairbanks at the vigil 300956 (HM1): kneels beside her out of combat, passive and attackable (rule
// 10: damage or a hostile cast on him pulls the pair); in the fight he stays where he knelt (he fights from range: the
// hard mode casts his kit through him) and melees only what stands in his reach. His death is the Truth (his line 0).
// -------------------------------------------------------------------------------------------------------------------

struct npc_sm_vigil_fairbanks : public ScriptedAI
{
    explicit npc_sm_vigil_fairbanks(Creature* creature) : ScriptedAI(creature) { }

    void InitializeAI() override
    {
        me->SetCombatMovement(false);
        ScriptedAI::InitializeAI();
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetVirtualItem(0, kItemFairbanksWeapon);
        if (!me->IsEngaged())
            me->SetStandState(UNIT_STAND_STATE_KNEEL);
    }

    void JustEngagedWith(Unit* who) override
    {
        me->SetStandState(UNIT_STAND_STATE_STAND);
        me->SetReactState(REACT_AGGRESSIVE);
        // Pulled first (rule 10): the pair comes with him.
        if (WhitemaneFight* fight = WhitemaneFightOf(me))
            if (fight->State() != SmWhitemane::WhitemaneState::Fight && who)
                fight->StartFight(who, "the vigil Fairbanks was attacked");
    }

    // A hostile cast that started no combat (a debuff from range) pulls him as damage does.
    void AttackedBy(Unit* attacker) override
    {
        if (me->IsEngaged() || !attacker || !attacker->GetCharmerOrOwnerPlayerOrPlayerItself())
            return;
        me->EngageWithTarget(attacker);
    }

    // He fights from where he stands (no chase).
    void AttackStart(Unit* who) override
    {
        if (who && me->HasReactState(REACT_AGGRESSIVE))
            me->Attack(who, true);
    }

    void MoveInLineOfSight(Unit* /*who*/) override { }

    // While the pair fights he stays in it (every fight player back at 0 threat: rule 11); else home to her side.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (WhitemaneFight* fight = WhitemaneFightOf(me))
            if (fight->State() == SmWhitemane::WhitemaneState::Fight && me->IsAlive() && !fight->FightPlayers().empty())
            {
                fight->JoinFight(me);
                return;
            }
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustReachedHome() override
    {
        me->SetStandState(UNIT_STAND_STATE_KNEEL);
    }

    void JustDied(Unit* killer) override
    {
        Talk(SAY_FAIRBANKS_TRUTH);
        LogTt("truth-fairbanks-died", Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_TT_HEAL)
            LogTt("truth-heal-kicked", "reward");
        else if (spell && spell->Id == SPELL_TT_CURSE)
            LogTt("truth-curse-kicked", "reward");
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }
};

// -------------------------------------------------------------------------------------------------------------------
// The spirit of Alexandros Mograine 300957 (HM2-HM5): a presence over the altar, never attackable or selectable,
// friendly; never moves, fights or evades. The hard mode speaks and casts through it.
// -------------------------------------------------------------------------------------------------------------------

struct npc_sm_alexandros_spirit : public ScriptedAI
{
    explicit npc_sm_alexandros_spirit(Creature* creature) : ScriptedAI(creature) { }

    void InitializeAI() override
    {
        Setup();
        ScriptedAI::InitializeAI();
    }

    void Reset() override
    {
        Setup();
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }

private:
    void Setup()
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetDisableGravity(true);
        me->SetVirtualItem(0, kItemAlexandrosBlade);
    }
};

// -------------------------------------------------------------------------------------------------------------------
// The hard mode for one pull (WhitemaneFight.h WhitemaneHardMode)
// -------------------------------------------------------------------------------------------------------------------

class TruthFight : public SmWhitemane::WhitemaneHardMode
{
public:
    void OnEngage(WhitemaneFight& fight) override
    {
        Creature* her = fight.Whitemane();
        SetCreatureHealth(her, kWhitemaneHealth);
        _phase = Phase::One;
        uint64 const now = fight.FightMs();
        _nextShield = now + kShieldFirstMs;
        _nextCurse = now + kCurseFirstMs;
        _nextHeal = now + kHealFirstMs;
        _nextWard = now;
        _nextMark = now + kMarkPollMs;
        Creature* fairbanks = FindVigilFairbanks(her);
        bool summoned = false;
        if (!fairbanks)
        {
            // A GM arming (`.dbtest sm whitemane hardmode`) and a quick pull: he appears beside her where she stands.
            Point4 const at{ her->GetPositionX(), her->GetPositionY() - kVigilFairbanksBesideYd, her->GetPositionZ(),
                her->GetOrientation() };
            fairbanks = SummonVigilFairbanks(fight, at, true);
            summoned = true;
        }
        if (fairbanks)
        {
            _fairbanks = fairbanks->GetGUID();
            fairbanks->SetStandState(UNIT_STAND_STATE_STAND);
            fairbanks->SetReactState(REACT_AGGRESSIVE);
            fight.JoinFight(fairbanks);
        }
        ApplyWard(fight);
        fight.Log("truth-engage", Acore::StringFormat("health={} fairbanks={} ({}) mograine-risen={} lane={}ms "
            "flame={}ms seared={}ms", her->GetMaxHealth(), fairbanks ? fairbanks->GetMaxHealth() : 0,
            fairbanks ? (summoned ? "summoned" : "at the vigil") : "missing", kMograineHealth, kLaneEveryPhaseOneMs,
            kFlameEveryPhaseOneMs, kSearedMs));
    }

    void OnUpdate(WhitemaneFight& fight, uint32 /*diff*/) override
    {
        uint64 const now = fight.FightMs();
        if (now >= _nextMark)
        {
            _nextMark = now + kMarkPollMs;
            SyncCurseMarks(fight);
        }
        switch (_phase)
        {
            case Phase::One:
                UpdatePhaseOne(fight, now);
                break;
            case Phase::Truth:
                UpdateTruth(fight, now);
                break;
            case Phase::Two:
                UpdatePhaseTwo(fight, now);
                break;
        }
    }

    // HM1 Inquisitor's Ward: half the damage to either of the pair while Fairbanks lives.
    void OnDamageTaken(WhitemaneFight& /*fight*/, SmWhitemane::PairUnit /*unit*/, Unit* /*attacker*/,
        uint32& damage) override
    {
        if (WardActive(_phase) && damage)
            damage = WardedDamage(damage);
    }

    void OnRise(WhitemaneFight& fight, bool first) override
    {
        if (_phase == Phase::One)
            ApplyWard(fight);
        else if (first)
            if (MograineFight* m = fight.MograineAI())
                m->SetCadence(MograineKit::DivineStorm, kStormEveryPhaseTwoMs, kStormEveryPhaseTwoMs);
    }

    void OnSaveStart(WhitemaneFight& fight, SmWhitemane::PairUnit fallen, uint32 windowMs) override
    {
        fight.Log("truth-save", Acore::StringFormat("phase={} fallen={} window={}ms", PhaseName(_phase),
            fallen == SmWhitemane::PairUnit::Mograine ? "mograine" : "whitemane", windowMs));
    }

    // The bots: Fairbanks first while he lives, his Heal on the interrupt list after hers, the curse a decurse, his
    // shields purges; the spirit never a target.
    void ConfigureDescriptor(WhitemaneFight& /*fight*/, BossMechanics::Descriptor& d) override
    {
        if (_phase == Phase::One)
        {
            d.targets.emplace_back(NPC_SM_VIGIL_FAIRBANKS, kFairbanksTargetPriority);
            d.interrupts.emplace_back(NPC_SM_VIGIL_FAIRBANKS, SPELL_TT_HEAL, kFairbanksHealKickPriority,
                Ms(kHealEveryMs));
        }
        d.dispels.emplace_back(SPELL_TT_CURSE, kCurseDispelPriority);
        d.purges.emplace_back(0u, SPELL_TT_SHIELD, kShieldPurgePriority);
        d.ignores.emplace_back(NPC_SM_ALEXANDROS_SPIRIT);
    }

    // Her death (the pair's: HM5), evade or reset: the ward, the curses and marks, the shame off; the spirit speaks and
    // fades (death) or goes (a wipe); her template health back on a wipe (the idle hook puts the 340k back while lit).
    void OnEnd(WhitemaneFight& fight, bool died) override
    {
        Creature* her = fight.Whitemane();
        RemoveWard(fight);
        if (Map* map = her->GetMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource())
                {
                    p->RemoveAurasDueToSpell(SPELL_TT_CURSE);
                    p->RemoveAurasDueToSpell(SPELL_TT_CURSE_MARK);
                }
        if (Creature* m = fight.Mograine())
            m->RemoveAurasDueToSpell(SPELL_TT_SHAME);
        if (Creature* spirit = Spirit(her))
        {
            if (died)
            {
                UnitTalk(spirit, SAY_SPIRIT_FORGIVEN);
                spirit->CastSpell(spirit, SPELL_TT_SPIRIT_FADE, true);
                spirit->DespawnOrUnsummon(Milliseconds(kSpiritFadeMs));
            }
            else
                spirit->DespawnOrUnsummon();
        }
        if (!died && her->IsAlive())
            SetCreatureHealth(her, TemplateHealth(her));
        if (died)
            ForgetIdlePace(her->GetGUID());
        fight.Log("truth-end", Acore::StringFormat("died={} phase={} judgments={} lights={} verdicts={} "
            "renault-hits={} whitemane-hits={}", died ? 1 : 0, PhaseName(_phase), _judgments, _lights, _verdicts,
            _renaultHits, _whitemaneHits));
        _spirit.Clear();
        _fairbanks.Clear();
        _light = {};
        _verdict = {};
    }

    // ---- tuning (D14's hooks) ----
    std::optional<uint32> SaveWindowMs(WhitemaneFight const& /*fight*/, SmWhitemane::PairUnit fallen) const override
    {
        return SaveWindowFor(_phase, fallen == SmWhitemane::PairUnit::Mograine);
    }

    std::optional<uint32> ToHerSideEveryMs(WhitemaneFight const& /*fight*/) const override
    {
        return LaneEveryFor(_phase);
    }

    // To Her Side never starts under a Verdict marker (Renault is held for it).
    bool ToHerSideAllowed(WhitemaneFight const& /*fight*/) const override { return !_verdict.active; }

    std::optional<uint32> FlameEveryMs(WhitemaneFight const& /*fight*/) const override
    {
        return FlameEveryFor(_phase);
    }

    std::optional<uint32> SearedMs(WhitemaneFight const& /*fight*/) const override { return kSearedMs; }

    std::optional<uint32> RisenMaxHealth(WhitemaneFight const& /*fight*/) const override { return kMograineHealth; }

    // ---- `.dbtest sm truth` entry points (an empty string when done; otherwise why not) ----
    std::string TestTruth(WhitemaneFight& fight, Unit* by)
    {
        if (_phase != Phase::One)
            return Acore::StringFormat("The Truth ran already (phase {}).", PhaseName(_phase));
        Creature* fairbanks = Fairbanks(fight);
        if (fairbanks && fairbanks->IsAlive())
            Unit::Kill(by ? by : fight.Whitemane(), fairbanks);
        else
            StartTruth(fight, "test");
        return {};
    }

    std::string TestJudgment(WhitemaneFight& fight, Judgment kind)
    {
        if (_phase != Phase::Two)
            return "After the Truth only (`.dbtest sm truth truth` first, then wait 3 s).";
        if (_light.active || _verdict.active)
            return "A light or a Verdict is already marked.";
        uint64 const now = fight.FightMs();
        bool const fired = kind == Judgment::Verdict ? FireVerdict(fight, now) : FireLight(fight, now);
        return fired ? std::string() : std::string("Refused (no spirit, no target or no floor: see the log).");
    }

    std::string TestKit(WhitemaneFight& fight, char const* what)
    {
        if (_phase != Phase::One || !Fairbanks(fight) || !Fairbanks(fight)->IsAlive())
            return "Fairbanks must be alive (phase 1).";
        uint64 const now = fight.FightMs();
        std::string const kit(what);
        if (kit == "curse")
            _nextCurse = now;
        else if (kit == "shield")
            _nextShield = now;
        else
            _nextHeal = now;
        return {};
    }

    std::string State(WhitemaneFight& fight)
    {
        uint64 const now = fight.FightMs();
        auto in = [now](uint64 at) -> std::string
        {
            return Acore::StringFormat("{}ms", at > now ? at - now : 0);
        };
        Creature* fairbanks = Fairbanks(fight);
        return Acore::StringFormat("phase={} fairbanks={} next: shield={} curse={} heal={} judgment={} (#{}: {}) | "
            "light={} verdict={} rooted={} | lights={} verdicts={} renault-hits={} whitemane-hits={} spirit={}",
            PhaseName(_phase), fairbanks ? (fairbanks->IsAlive() ? "alive" : "dead") : "none", in(_nextShield),
            in(_nextCurse), in(_nextHeal), in(_nextJudgment), _judgments, JudgmentName(JudgmentFor(_judgments)),
            _light.active ? 1 : 0, _verdict.active ? 1 : 0, _verdict.rooted ? 1 : 0, _lights, _verdicts,
            _renaultHits, _whitemaneHits, Spirit(fight.Whitemane()) ? "up" : "none");
    }

private:
    struct PendingLight
    {
        bool active = false;
        Position spot;
        uint64 resolveAt = 0;
    };

    struct PendingVerdict
    {
        bool active = false;
        bool rooted = false;
        bool swung = false;
        LinePath path;
        float z = 0.f;
        uint64 swingAt = 0;
        uint64 resolveAt = 0;
    };

    Creature* Fairbanks(WhitemaneFight& fight) const
    {
        return _fairbanks ? ObjectAccessor::GetCreature(*fight.Whitemane(), _fairbanks) : nullptr;
    }

    Creature* Spirit(Creature* her) const
    {
        return _spirit && her ? ObjectAccessor::GetCreature(*her, _spirit) : nullptr;
    }

    // The registry owner whose victim is the fight's tank (D14's rule): Mograine while he is risen and alive, down in
    // her save included (the role provider then finds the real tank, not her top-threat player); else her.
    static Unit* Owner(WhitemaneFight& fight)
    {
        MograineFight* m = fight.MograineAI();
        return IsRisen(m) ? static_cast<Unit*>(m->Mograine()) : static_cast<Unit*>(fight.Whitemane());
    }

    static bool InReach(Creature* caster, Unit* target)
    {
        return target && caster->IsWithinDistInMap(target, kCastRangeYd) && caster->IsWithinLOSInMap(target);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HM1 phase 1: Fairbanks
    // ----------------------------------------------------------------------------------------------------------------

    void UpdatePhaseOne(WhitemaneFight& fight, uint64 now)
    {
        Creature* fairbanks = Fairbanks(fight);
        if (!fairbanks || !fairbanks->IsAlive())
        {
            StartTruth(fight, fairbanks ? "fairbanks-died" : "fairbanks-gone");
            return;
        }
        if (now >= _nextWard)
        {
            _nextWard = now + kWardPollMs;
            ApplyWard(fight);
        }
        // HM1b: an instant (triggered) shield, even while he casts.
        if (now >= _nextShield)
        {
            Creature* lower = fight.LowerOfPair();
            if (lower && InReach(fairbanks, lower))
            {
                CastShield(fight, fairbanks, lower);
                _nextShield = now + kShieldEveryMs;
            }
            else
                _nextShield = now + kRetryMs;
        }
        if (fairbanks->HasUnitState(UNIT_STATE_CASTING))
            return;
        // HM1c first (a reward to kick), then HM1a.
        if (now >= _nextHeal)
        {
            Creature* lower = fight.LowerOfPair();
            if (lower && InReach(fairbanks, lower) && CastHeal(fight, fairbanks, lower))
            {
                _nextHeal = now + kHealEveryMs;
                Mechanic::NoteNextCastIn(fairbanks, SPELL_TT_HEAL, Ms(kHealEveryMs));
                return;
            }
            _nextHeal = now + kRetryMs;
        }
        if (now >= _nextCurse)
        {
            Player* target = PickCurseTarget(fight, fairbanks);
            _nextCurse = now + (target && CastCurse(fight, fairbanks, target) ? kCurseEveryMs : kRetryMs);
        }
    }

    void CastShield(WhitemaneFight& fight, Creature* fairbanks, Creature* target)
    {
        uint32 const amount = static_cast<uint32>(static_cast<float>(target->GetMaxHealth()) * kShieldPct / 100.f);
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(amount));
        fairbanks->CastSpell(target, SPELL_TT_SHIELD, args);
        fight.Log("truth-shield", Acore::StringFormat("on={} absorb={} ({:.0f}% of {})", target->GetName(), amount,
            kShieldPct, target->GetMaxHealth()));
    }

    bool CastHeal(WhitemaneFight& fight, Creature* fairbanks, Creature* target)
    {
        fairbanks->StopMoving();
        CastSpellExtraArgs args;
        args.AddSpellBP0(static_cast<int32>(kHealPct));
        SpellCastResult const result = fairbanks->CastSpell(target, SPELL_TT_HEAL, args);
        if (result != SPELL_CAST_OK)
        {
            fight.Log("truth-heal-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        fight.Log("truth-heal", Acore::StringFormat("on={} at={:.0f}% pct={} cast={}ms", target->GetName(),
            target->GetHealthPct(), kHealPct, kHealCastMs));
        return true;
    }

    // HM1a: a random fight player in his range and sight, the tank included.
    Player* PickCurseTarget(WhitemaneFight& fight, Creature* fairbanks)
    {
        std::vector<Player*> const players = fight.FightPlayers();
        std::vector<PlayerCandidate> candidates;
        for (Player* p : players)
            candidates.push_back({ p->GetGUID().GetRawValue(), p->IsAlive(),
                InReach(fairbanks, p) && !p->HasAura(SPELL_TT_CURSE) });
        std::optional<std::size_t> const pick = PickAny(candidates,
            [](std::uint32_t n) { return n ? urand(0, n - 1) : 0u; });
        return pick ? players[*pick] : nullptr;
    }

    bool CastCurse(WhitemaneFight& fight, Creature* fairbanks, Player* target)
    {
        // A percent of the reference row with the boss as the owner (rule 2), the tank row on the tank.
        uint32 const perTick = DungeonKit::RefFlat(fight.Whitemane(), kCursePct, fight.IsTank(target));
        fairbanks->StopMoving();
        CastSpellExtraArgs args;
        args.AddSpellBP0(static_cast<int32>(perTick));
        SpellCastResult const result = fairbanks->CastSpell(target, SPELL_TT_CURSE, args);
        if (result != SPELL_CAST_OK)
        {
            fight.Log("truth-curse-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        fight.Log("truth-curse", Acore::StringFormat("on={} tick={} ({:.0f}% a second for {}ms) tank={}",
            target->GetName(), perTick, kCursePct, kCurseMs, fight.IsTank(target) ? 1 : 0));
        return true;
    }

    // The curse's red mark (a lasting look) follows the curse: on while it lasts, gone with a decurse.
    void SyncCurseMarks(WhitemaneFight& fight)
    {
        Creature* her = fight.Whitemane();
        for (Player* p : fight.FightPlayers())
        {
            Aura* curse = p->GetAura(SPELL_TT_CURSE);
            bool const marked = p->HasAura(SPELL_TT_CURSE_MARK);
            if (curse && !marked)
            {
                if (Aura* mark = her->AddAura(SPELL_TT_CURSE_MARK, p))
                {
                    mark->SetMaxDuration(curse->GetDuration());
                    mark->SetDuration(curse->GetDuration());
                }
            }
            else if (!curse && marked)
                p->RemoveAurasDueToSpell(SPELL_TT_CURSE_MARK);
        }
    }

    // HM1 the ward's look on her and on a risen Mograine while Fairbanks lives.
    void ApplyWard(WhitemaneFight& fight)
    {
        Creature* fairbanks = Fairbanks(fight);
        if (!fairbanks || !fairbanks->IsAlive())
            return;
        Creature* her = fight.Whitemane();
        if (her->IsAlive() && !her->HasAura(SPELL_TT_WARD))
            fairbanks->AddAura(SPELL_TT_WARD, her);
        if (IsRisen(fight.MograineAI()))
            if (Creature* m = fight.Mograine(); m && !m->HasAura(SPELL_TT_WARD))
                fairbanks->AddAura(SPELL_TT_WARD, m);
    }

    void RemoveWard(WhitemaneFight& fight)
    {
        fight.Whitemane()->RemoveAurasDueToSpell(SPELL_TT_WARD);
        if (Creature* m = fight.Mograine())
            m->RemoveAurasDueToSpell(SPELL_TT_WARD);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HM2 the Truth
    // ----------------------------------------------------------------------------------------------------------------

    void StartTruth(WhitemaneFight& fight, char const* why)
    {
        uint64 const now = fight.FightMs();
        _phase = Phase::Truth;
        _truthAt = now;
        _secondLine = false;
        fight.HoldMechanics(true, "truth");
        RemoveWard(fight);
        Creature* spirit = SummonSpirit(fight);
        UnitTalk(spirit, SAY_SPIRIT_RENAULT);
        MograineFight* m = fight.MograineAI();
        _renaultSpoke = IsUp(m);
        bool kneeled = false;
        if (_renaultSpoke)
        {
            m->Say(SAY_MOGRAINE_FATHER);
            if (KneelAllowed(fight.SaveInProgress(), fight.LaneInProgress()))
            {
                ShameKneel(m, kTruthMs, "truth");
                kneeled = true;
            }
        }
        fight.RefreshDescriptor();
        fight.Log("truth-truth", Acore::StringFormat("why={} spirit={} renault-kneels={} save={} lane={}", why,
            spirit ? 1 : 0, kneeled ? 1 : 0, fight.SaveInProgress() ? 1 : 0, fight.LaneInProgress() ? 1 : 0));
    }

    // The spirit of Alexandros over the altar: a map summon (not hers), so it can speak over the pair after her death.
    Creature* SummonSpirit(WhitemaneFight& fight)
    {
        Creature* her = fight.Whitemane();
        if (Creature* spirit = Spirit(her))
            return spirit;
        Map* map = her->GetMap();
        Position const at(kSpiritSpot.x, kSpiritSpot.y, kSpiritSpot.z, kSpiritSpot.o);
        TempSummon* spirit = map ? map->SummonCreature(NPC_SM_ALEXANDROS_SPIRIT, at) : nullptr;
        if (!spirit)
        {
            fight.Log("truth-spirit-missing", "the spirit 300957 could not be summoned (no template?)");
            return nullptr;
        }
        _spirit = spirit->GetGUID();
        spirit->SetReactState(REACT_PASSIVE);
        spirit->SetDisableGravity(true);
        spirit->SetVirtualItem(0, kItemAlexandrosBlade);
        spirit->CastSpell(spirit, SPELL_TT_TELEPORT_IN, true);
        spirit->CastSpell(spirit, SPELL_TT_SPIRIT_GLOW, true);
        return spirit;
    }

    void UpdateTruth(WhitemaneFight& fight, uint64 now)
    {
        uint64 const elapsed = now - _truthAt;
        if (!_secondLine && elapsed >= kTruthSecondLineMs)
        {
            _secondLine = true;
            MograineFight* m = fight.MograineAI();
            if (_renaultSpoke && IsUp(m))
                m->Say(SAY_MOGRAINE_FORGIVE);
        }
        if (elapsed >= kTruthMs)
            EnterPhaseTwo(fight, now);
    }

    // HM3 / HM4: the father judges, the pair's cadences change.
    void EnterPhaseTwo(WhitemaneFight& fight, uint64 now)
    {
        _phase = Phase::Two;
        fight.HoldMechanics(false, "truth");
        fight.Say(SmWhitemane::SAY_WHITEMANE_LIES);
        MograineFight* m = fight.MograineAI();
        if (IsRisen(m))
            m->SetCadence(MograineKit::DivineStorm, kStormEveryPhaseTwoMs - kTruthMs, kStormEveryPhaseTwoMs);
        _nextJudgment = _truthAt + kSpiritFirstCastMs;
        _judgments = 0;
        fight.RefreshDescriptor();
        fight.Log("truth-guilt", Acore::StringFormat("her-save={}ms his-save={}ms storm={}ms first-judgment=T+{}ms "
            "(now T+{}ms)", kHerSavePhaseTwoMs, kHisSavePhaseTwoMs, kStormEveryPhaseTwoMs, kSpiritFirstCastMs,
            now - _truthAt));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HM3 the father's judgment
    // ----------------------------------------------------------------------------------------------------------------

    void UpdatePhaseTwo(WhitemaneFight& fight, uint64 now)
    {
        if (_light.active && now >= _light.resolveAt)
            ResolveLight(fight);
        if (_verdict.active)
        {
            if (!_verdict.swung && now >= _verdict.swingAt)
            {
                _verdict.swung = true;
                Swing(fight, _verdict.path, _verdict.z);
            }
            if (now >= _verdict.resolveAt)
                ResolveVerdict(fight);
        }
        if (now < _nextJudgment || _light.active || _verdict.active)
            return;
        Judgment kind = JudgmentFor(_judgments);
        if (kind == Judgment::Verdict && fight.LaneInProgress())
        {
            // Renault is charging to her side: the Verdict waits for him (it must land on him), then gives way.
            if (!_verdictWaitFrom)
                _verdictWaitFrom = std::max<uint64>(now, 1);
            if (now - _verdictWaitFrom < kVerdictLaneWaitMs)
                return;
            kind = Judgment::Light;
            fight.Log("truth-verdict-blocked", "To Her Side ran the whole wait: a light instead");
        }
        _verdictWaitFrom = 0;
        if (kind == Judgment::Verdict)
            FireVerdict(fight, now);
        else
            FireLight(fight, now);
        ++_judgments;
        _nextJudgment = std::max(_nextJudgment + kJudgmentEveryMs, now + kJudgmentGapMinMs);
    }

    // HM3 the light: two registry circles on one spot. The non-tanks take 45% and Weakened; the tank 25%, and Weakened
    // only when Renault was not in it as it fell (its job: hold Renault in it, `.Park`), drawn once.
    bool FireLight(WhitemaneFight& fight, uint64 now)
    {
        Creature* spirit = Spirit(fight.Whitemane());
        std::vector<Player*> const players = fight.FightPlayers();
        std::vector<PlayerCandidate> candidates;
        for (Player* p : players)
            candidates.push_back({ p->GetGUID().GetRawValue(), p->IsAlive(), true });
        std::optional<std::size_t> const pick = PickAny(candidates,
            [](std::uint32_t n) { return n ? urand(0, n - 1) : 0u; });
        if (!spirit || !pick)
        {
            fight.Log("truth-light-none", spirit ? "nobody to mark" : "no spirit");
            return false;
        }
        Player* target = players[*pick];
        Position const spot(target->GetPositionX(), target->GetPositionY(), target->GetPositionZ(), 0.f);
        Unit* owner = Owner(fight);
        BossMechanics::Eligibility others;
        others.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        MechanicRef light = Mechanic::Circle(owner, BossMechanics::Anchor(spot), kLightRadiusYd, Ms(kLightWarnMs));
        light.Damage(kLightPct).TankDamage(kLightTankPct).Weakened().School(SPELL_SCHOOL_HOLY)
            .Spell(SPELL_TT_LIGHT_HIT).Eligible(others).Within(FloorBounds()).Tag(TAG_TT_LIGHT);
        fight.Track(light.Handle());
        BossMechanics::Eligibility tank;
        tank.roles = BossMechanics::Role::Tank;
        MechanicRef tankLight = Mechanic::Circle(owner, BossMechanics::Anchor(spot), kLightRadiusYd,
            Ms(kLightWarnMs));
        tankLight.Damage(kLightTankPct).TankDamage(kLightTankPct).School(SPELL_SCHOOL_HOLY).Spell(SPELL_TT_LIGHT_HIT)
            .Eligible(tank).NoTelegraph().Within(FloorBounds()).Tag(TAG_TT_LIGHT_TANK);
        MograineFight* m = fight.MograineAI();
        if (IsUp(m))
            tankLight.Park(m->Mograine());
        // The failed lure: a tank in the light without Renault in it is Weakened too (no extra damage).
        Map* map = owner->GetMap();
        ObjectGuid const ownerGuid = owner->GetGUID();
        ObjectGuid const mograineGuid = m && m->Mograine() ? m->Mograine()->GetGUID() : ObjectGuid::Empty;
        tankLight.OnResolve([map, ownerGuid, mograineGuid, spot](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || result.hits.empty() || !map)
                return;
            Creature* mc = mograineGuid ? map->GetCreature(mograineGuid) : nullptr;
            bool const renault = mc && IsUp(SmLastStand::MograineFightOf(mc)) && InCircle(PlaneOf(mc),
                mc->GetPositionZ(), { spot.GetPositionX(), spot.GetPositionY() }, spot.GetPositionZ(), kLightRadiusYd);
            if (!LightWeakensTank(renault))
                return;
            Creature* source = map->GetCreature(ownerGuid);
            if (!source || !source->IsInWorld())
                return;
            GuidSet tanks;
            for (ObjectGuid const& guid : result.hits)
                if (guid.IsPlayer())
                    tanks.insert(guid);
            DungeonKit::RegistryHitSpec weaken;
            weaken.weakened = true;
            weaken.tag = TAG_TT_LIGHT_TANK;
            DungeonKit::RegistryHit(source, tanks, weaken);
            LogTt("truth-light-tank-weakened", Acore::StringFormat("tanks={}", tanks.size()));
        });
        fight.Track(tankLight.Handle());
        spirit->CastSpell(spirit, SPELL_TT_LIGHT_CAST, true);
        _light = {};
        _light.active = true;
        _light.spot = spot;
        _light.resolveAt = now + kLightWarnMs;
        ++_lights;
        fight.Log("truth-light", Acore::StringFormat("#{} on={} tank={} at=({:.1f}, {:.1f}) pct={:.0f} tank-pct={:.0f} "
            "park={}", _judgments + 1, target->GetName(), fight.IsTank(target) ? 1 : 0, spot.GetPositionX(),
            spot.GetPositionY(), kLightPct, kLightTankPct, IsUp(m) ? 1 : 0));
        return true;
    }

    // The light falls: the pillar's look; Renault in it 4% of his health and a 2 s kneel (the registry hits players).
    void ResolveLight(WhitemaneFight& fight)
    {
        Position const spot = _light.spot;
        _light = {};
        Creature* her = fight.Whitemane();
        Creature* spirit = Spirit(her);
        Creature* stalker = sObjectMgr->GetCreatureTemplate(NPC_SM_STALKER_WAVE2)
            ? fight.Summon(NPC_SM_STALKER_WAVE2, spot, 3000) : nullptr;
        if (stalker)
            stalker->CastSpell(stalker, SPELL_TT_LIGHT_PILLAR, true);
        else if (spirit)
            for (Player* p : fight.FightPlayers())
                if (InCircle(PlaneOf(p), p->GetPositionZ(), { spot.GetPositionX(), spot.GetPositionY() },
                    spot.GetPositionZ(), kLightRadiusYd))
                    spirit->CastSpell(p, SPELL_TT_LIGHT_PILLAR, true);
        MograineFight* m = fight.MograineAI();
        Creature* mc = m ? m->Mograine() : nullptr;
        bool const renault = IsUp(m) && InCircle(PlaneOf(mc), mc->GetPositionZ(),
            { spot.GetPositionX(), spot.GetPositionY() }, spot.GetPositionZ(), kLightRadiusYd);
        uint32 dealt = 0;
        bool kneeled = false;
        if (renault)
        {
            ++_renaultHits;
            dealt = DealPercent(mc, kLightRenaultPct);
            if (KneelAllowed(fight.SaveInProgress(), fight.LaneInProgress()) && IsUp(m))
            {
                ShameKneel(m, kLightKneelMs, "light");
                kneeled = true;
            }
        }
        fight.Log("truth-light-falls", Acore::StringFormat("renault={} dealt={} kneel={} pillar={}", renault ? 1 : 0,
            dealt, kneeled ? 1 : 0, stalker ? "stalker" : "players"));
    }

    // Whom the Verdict runs through: Renault (risen, down included); else her; else a random player.
    Unit* VerdictAim(WhitemaneFight& fight)
    {
        MograineFight* m = fight.MograineAI();
        if (IsRisen(m))
            return m->Mograine();
        if (fight.Whitemane()->IsAlive())
            return fight.Whitemane();
        std::vector<Player*> const players = fight.FightPlayers();
        return players.empty() ? nullptr : players[urand(0, static_cast<uint32>(players.size()) - 1)];
    }

    // HM3a: the father raises the Ashbringer; a 6 yd line from the spirit through Renault to the floor's far edge,
    // fixed now; Renault held for the 3.5 s marker (D13's HoldControl) unless a save or a charge already drives him.
    bool FireVerdict(WhitemaneFight& fight, uint64 now)
    {
        Creature* spirit = Spirit(fight.Whitemane());
        Unit* through = VerdictAim(fight);
        if (!spirit || !through)
        {
            fight.Log("truth-verdict-none", spirit ? "nobody to aim through" : "no spirit");
            return false;
        }
        LinePath const path = VerdictPathFor(PlaneOf(spirit), PlaneOf(through));
        if (path.length < 1.f)
        {
            fight.Log("truth-verdict-none", "the spirit is off the floor");
            return false;
        }
        float const z = through->GetPositionZ();
        Unit* owner = Owner(fight);
        MechanicRef verdict = Mechanic::Line(owner, BossMechanics::Anchor(Position(path.from.x, path.from.y, z,
            path.facing)), path.facing, path.length, kVerdictWidthYd, Ms(kVerdictWarnMs));
        verdict.Damage(kVerdictPct).TankDamage(kVerdictPct).School(SPELL_SCHOOL_HOLY).Spell(SPELL_TT_VERDICT_HIT)
            .Within(FloorBounds()).Tag(TAG_TT_VERDICT);
        fight.Track(verdict.Handle());
        _verdict = {};
        MograineFight* m = fight.MograineAI();
        if (IsUp(m) && KneelAllowed(fight.SaveInProgress(), fight.LaneInProgress()))
        {
            m->HoldControl(m->RisenMs() + kVerdictWarnMs + kVerdictHoldGraceMs);
            Creature* mc = m->Mograine();
            mc->InterruptNonMeleeSpells(false);
            mc->AttackStop();
            mc->StopMoving();
            mc->GetMotionMaster()->Clear();
            _verdict.rooted = true;
        }
        UnitTalk(spirit, EMOTE_SPIRIT_RAISES);
        spirit->CastSpell(spirit, SPELL_TT_VERDICT_RAISE, true);
        _verdict.active = true;
        _verdict.path = path;
        _verdict.z = z;
        _verdict.resolveAt = now + kVerdictWarnMs;
        _verdict.swingAt = _verdict.resolveAt - SwingLeadMs(path.length);
        ++_verdicts;
        fight.Log("truth-verdict", Acore::StringFormat("#{} through={} length={:.1f}yd facing={:.2f} rooted={} "
            "pct={:.0f}", _judgments + 1, through->GetName(), path.length, path.facing, _verdict.rooted ? 1 : 0,
            kVerdictPct));
        return true;
    }

    // The blade flies along the line (a missile look to its far end, timed to cross the line as it lands).
    void Swing(WhitemaneFight& fight, LinePath const& path, float z)
    {
        if (Creature* spirit = Spirit(fight.Whitemane()))
            spirit->CastSpell(path.end.x, path.end.y, z, SPELL_TT_VERDICT_SWING, true);
    }

    // The Verdict lands (the registry hits players): Renault on it 6% and a 3 s kneel; Whitemane on it 5% and her cast
    // breaks (a save channel starts over: D14's BreakCast).
    void ResolveVerdict(WhitemaneFight& fight)
    {
        PendingVerdict const v = _verdict;
        _verdict = {};
        if (!v.swung)
            Swing(fight, v.path, v.z);
        Creature* her = fight.Whitemane();
        Creature* spirit = Spirit(her);
        MograineFight* m = fight.MograineAI();
        Creature* mc = m ? m->Mograine() : nullptr;
        float const half = kVerdictWidthYd / 2.f;
        bool const save = fight.SaveInProgress();
        bool renault = false;
        bool kneeled = false;
        if (IsUp(m) && OnLine(PlaneOf(mc), v.path, half))
        {
            renault = true;
            ++_renaultHits;
            if (v.rooted && !save)
                m->HoldControl(m->RisenMs());       // released; the kneel takes him next
            if (spirit)
                spirit->CastSpell(mc, SPELL_TT_VERDICT_IMPACT, true);
            DealPercent(mc, kVerdictRenaultPct);
            if (KneelAllowed(fight.SaveInProgress(), fight.LaneInProgress()) && IsUp(m))
            {
                ShameKneel(m, kVerdictKneelMs, "verdict");
                kneeled = true;
            }
        }
        else if (v.rooted && IsUp(m) && !save)
            m->HoldControl(m->RisenMs() + 1);       // back on his victim (D14's release)
        bool whitemane = false;
        if (her->IsAlive() && VerdictTakesHer(fight.Stage()) && OnLine(PlaneOf(her), v.path, half))
        {
            whitemane = true;
            ++_whitemaneHits;
            if (spirit)
                spirit->CastSpell(her, SPELL_TT_VERDICT_IMPACT, true);
            DealPercent(her, kVerdictWhitemanePct);
            if (her->IsAlive())
                fight.BreakCast("verdict");
        }
        fight.Log("truth-verdict-lands", Acore::StringFormat("renault={} kneel={} whitemane={} save={}",
            renault ? 1 : 0, kneeled ? 1 : 0, whitemane ? 1 : 0, save ? 1 : 0));
    }

    Phase _phase = Phase::One;
    ObjectGuid _fairbanks;
    ObjectGuid _spirit;
    PendingLight _light;
    PendingVerdict _verdict;
    uint64 _nextShield = 0;
    uint64 _nextCurse = 0;
    uint64 _nextHeal = 0;
    uint64 _nextWard = 0;
    uint64 _nextMark = 0;
    uint64 _truthAt = 0;
    uint64 _nextJudgment = 0;
    uint64 _verdictWaitFrom = 0;
    uint32 _judgments = 0;
    uint32 _lights = 0;
    uint32 _verdicts = 0;
    uint32 _renaultHits = 0;
    uint32 _whitemaneHits = 0;
    bool _secondLine = false;
    bool _renaultSpoke = false;
};

// -------------------------------------------------------------------------------------------------------------------
// The Torch 97701 (HM0, section 7 #21 A): replaces its SmartAI (event 70 -> activate the Secret Door, guid 11876).
// Bound by rev_whitemane_hard_mode_scarlet_monastery.sql (ScriptName, AIName '', the SmartAI rows dropped) on every
// wave: until wave 2 binds it acts as stock on every difficulty (TorchAnswerFor).
// -------------------------------------------------------------------------------------------------------------------

struct go_sm_torch : public GameObjectAI
{
    explicit go_sm_torch(GameObject* go) : GameObjectAI(go) { }

    // Stock: the default use moves the button (true stops it). A refused or spent Torch stays put; a triggered one is
    // pulled by Sync (the default use would toggle it back).
    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return false;
        return Pull(player) != TorchAnswer::Stock;
    }

    // A use by `user` (a click or the GM test). Returns what it did.
    TorchAnswer Pull(Player* user)
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return TorchAnswer::Stock;
        bool const heroic = DungeonKit::IsHeroicMap(me);
        bool const lit = instance->GetData(DATA_HARD_MODE_WHITEMANE) != 0;
        uint32 const lastStand = static_cast<uint32>(instance->GetBossState(BOSS_LAST_STAND));
        uint32 const whitemane = static_cast<uint32>(instance->GetBossState(BOSS_WHITEMANE));
        TorchAnswer answer = TorchAnswerFor(heroic, lastStand, whitemane, lit);
        switch (answer)
        {
            case TorchAnswer::Stock:
            case TorchAnswer::AlreadyLit:
                OpenSecretDoor(instance, me);
                break;
            case TorchAnswer::Refused:
                Notify(user, kTorchRefusedText);
                break;
            case TorchAnswer::Trigger:
                instance->SetData(DATA_HARD_MODE_WHITEMANE, 1);
                if (!instance->GetData(DATA_HARD_MODE_WHITEMANE))
                {
                    answer = TorchAnswer::Refused;     // the instance's own judge said no
                    Notify(user, kTorchRefusedText);
                    break;
                }
                OpenSecretDoor(instance, me);
                StartTrigger(instance, user);
                break;
        }
        LogTt("truth-torch", Acore::StringFormat("by={} answer={} heroic={} last-stand={} whitemane={} lit={}",
            user ? user->GetName() : "none", TorchAnswerName(answer), heroic ? 1 : 0, lastStand, whitemane,
            instance->GetData(DATA_HARD_MODE_WHITEMANE)));
        return answer;
    }

    void UpdateAI(uint32 diff) override
    {
        if (_leaving)
        {
            if (_leaveMs > diff)
                _leaveMs -= diff;
            else
            {
                if (Creature* stock = ObjectAccessor::GetCreature(*me, _leaving))
                    if (stock->IsAlive())
                        stock->DespawnOrUnsummon(0ms, Seconds(kLockoutRespawnSeconds));
                _leaving.Clear();
            }
        }
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kTorchPollMs;
        Sync();
    }

private:
    // HM0: the stock Fairbanks fears the door's players (5 s, no threat), teleports out and is gone for the lockout;
    // her 340k now (the idle hook keeps it and brings the vigil Fairbanks once he is gone).
    void StartTrigger(InstanceScript* instance, Player* user)
    {
        uint32 feared = 0;
        Creature* stock = StockFairbanks(instance, me);
        if (stock && stock->IsAlive())
        {
            if (Map* map = me->GetMap())
                for (auto const& ref : map->GetPlayers())
                {
                    Player* p = ref.GetSource();
                    if (CountsAsPlayer(p) && InFearRange(PlaneOf(p), p->GetPositionZ()))
                    {
                        stock->CastSpell(p, SPELL_TT_TORCH_FEAR, true);
                        ++feared;
                    }
                }
            // The 2 s before he is gone: no stock aggro or casts on the feared players beside the open door.
            stock->SetReactState(REACT_PASSIVE);
            stock->AttackStop();
            stock->SetImmuneToPC(true);
            stock->CastSpell(stock, SPELL_TT_TELEPORT_OUT, true);
            _leaving = stock->GetGUID();
            _leaveMs = kLeaveMs;
        }
        if (Creature* her = ObjectAccessor::GetCreature(*me, instance->GetGuidData(DATA_WHITEMANE)))
            if (her->IsAlive() && !her->IsEngaged())
                SetCreatureHealth(her, kWhitemaneHealth);
        Sync();
        LogTt("truth-lit", Acore::StringFormat("by={} feared={} fairbanks={}", user ? user->GetName() : "none", feared,
            stock && stock->IsAlive() ? "leaving" : "absent"));
    }

    // Lit (heroic): the Torch stays pulled and cannot be used again (once per lockout; a reload too).
    void Sync()
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance || !DungeonKit::IsHeroicMap(me) || !instance->GetData(DATA_HARD_MODE_WHITEMANE))
            return;
        if (me->GetGoState() != GO_STATE_ACTIVE)
            me->SetGoState(GO_STATE_ACTIVE);
        if (!me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE))
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
    }

    ObjectGuid _leaving;
    uint32 _leaveMs = 0;
    uint32 _pollMs = 0;
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest sm truth`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    // Whitemane's AI as the hard mode sees it (an error and nullptr when she is not running D14's AI).
    WhitemaneFight* FindFight(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_WHITEMANE);
        if (!boss)
            return nullptr;
        auto* fight = boss->IsAIEnabled ? dynamic_cast<WhitemaneFight*>(boss->AI()) : nullptr;
        if (!fight)
            handler->SendErrorMessage("{}", "Whitemane is not running boss_whitemane_rework (check the ScriptName; "
                "wave 2 binds it).");
        return fight;
    }

    // The running pull's hard mode (an error and nullptr when there is none).
    TruthFight* FindTruth(ChatHandler* handler, WhitemaneFight*& fight)
    {
        fight = FindFight(handler);
        if (!fight)
            return nullptr;
        auto* truth = dynamic_cast<TruthFight*>(fight->ActiveHardMode());
        if (!truth)
            handler->SendErrorMessage("{}", "No Truth pull is running (heroic: the Torch, or `.dbtest sm whitemane "
                "hardmode`, then pull her at the vigil).");
        return truth;
    }

    bool Reply(ChatHandler* handler, std::string const& error, char const* done)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("{}", done);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowHardModeInfo(handler, "truth", DATA_HARD_MODE_WHITEMANE, BOSS_THE_TRUTH);
    }

    bool HandleState(ChatHandler* handler)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        Creature* stock = gm ? StockFairbanks(instance, gm) : nullptr;
        GameObject* torch = gm ? gm->FindNearestGameObject(GO_TORCH, 300.f) : nullptr;
        char const* const torchState = !torch ? "not loaded"
            : torch->AI() && dynamic_cast<go_sm_torch*>(torch->AI()) ? "go_sm_torch" : "not bound";
        handler->PSendSysMessage("truth: lit={} last-stand={} whitemane={} kill-slot={} torch={} stock-fairbanks={}",
            instance->GetData(DATA_HARD_MODE_WHITEMANE), uint32(instance->GetBossState(BOSS_LAST_STAND)),
            uint32(instance->GetBossState(BOSS_WHITEMANE)), uint32(instance->GetBossState(BOSS_THE_TRUTH)),
            torchState, stock ? (stock->IsAlive() ? "alive" : "dead") : "gone");
        Creature* boss = SmTest::FindBoss(handler, NPC_WHITEMANE);
        auto* fight = boss && boss->IsAIEnabled ? dynamic_cast<WhitemaneFight*>(boss->AI()) : nullptr;
        auto* truth = fight ? dynamic_cast<TruthFight*>(fight->ActiveHardMode()) : nullptr;
        handler->PSendSysMessage("truth pull: {}", truth ? truth->State(*fight) : std::string("none"));
        return true;
    }

    // `.dbtest sm truth torch`: the GM uses the Torch (the same judgment and effects as a click).
    bool HandleTorch(ChatHandler* handler)
    {
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!gm || !SmTest::RequireScarletMonastery(handler))
            return false;
        GameObject* go = gm->FindNearestGameObject(GO_TORCH, 300.f);
        auto* torch = go && go->AI() ? dynamic_cast<go_sm_torch*>(go->AI()) : nullptr;
        if (!torch)
        {
            handler->SendErrorMessage("{}", "The Torch (97701) is not loaded or not bound to go_sm_torch (the D14H "
                "rev).");
            return false;
        }
        TorchAnswer const answer = torch->Pull(gm);
        handler->PSendSysMessage("truth: the Torch answered {}", TorchAnswerName(answer));
        return true;
    }

    // `.dbtest sm truth vigil`: the idle hook now (lit, heroic, out of combat).
    bool HandleVigil(ChatHandler* handler)
    {
        WhitemaneFight* fight = FindFight(handler);
        if (!fight)
            return false;
        handler->PSendSysMessage("truth: {}", IdleTruth(*fight, true));
        return true;
    }

    bool HandleTruth(ChatHandler* handler)
    {
        WhitemaneFight* fight = nullptr;
        TruthFight* truth = FindTruth(handler, fight);
        return truth && Reply(handler, truth->TestTruth(*fight, handler->GetPlayer()),
            "truth: Fairbanks falls (HM2: the spirit rises, Renault kneels, the father's judgment from T + 8 s).");
    }

    bool HandleLight(ChatHandler* handler)
    {
        WhitemaneFight* fight = nullptr;
        TruthFight* truth = FindTruth(handler, fight);
        return truth && Reply(handler, truth->TestJudgment(*fight, Judgment::Light),
            "truth: the father's light (HM3: 6 yd at a random player, 2.5 s).");
    }

    bool HandleVerdict(ChatHandler* handler)
    {
        WhitemaneFight* fight = nullptr;
        TruthFight* truth = FindTruth(handler, fight);
        return truth && Reply(handler, truth->TestJudgment(*fight, Judgment::Verdict),
            "truth: the Verdict (HM3a: the line through Renault, 3.5 s).");
    }

    bool HandleCurse(ChatHandler* handler)
    {
        WhitemaneFight* fight = nullptr;
        TruthFight* truth = FindTruth(handler, fight);
        return truth && Reply(handler, truth->TestKit(*fight, "curse"), "truth: Fairbanks casts Curse of Blood next.");
    }

    bool HandleShield(ChatHandler* handler)
    {
        WhitemaneFight* fight = nullptr;
        TruthFight* truth = FindTruth(handler, fight);
        return truth && Reply(handler, truth->TestKit(*fight, "shield"),
            "truth: Fairbanks shields the lower of the pair next.");
    }

    bool HandleHeal(ChatHandler* handler)
    {
        WhitemaneFight* fight = nullptr;
        TruthFight* truth = FindTruth(handler, fight);
        return truth && Reply(handler, truth->TestKit(*fight, "heal"), "truth: Fairbanks heals the lower of the pair "
            "next (3 s).");
    }

    ChatCommandTable const& TheTruthTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "torch",   HandleTorch,   SEC_GAMEMASTER, Console::No },
            { "vigil",   HandleVigil,   SEC_GAMEMASTER, Console::No },
            { "truth",   HandleTruth,   SEC_GAMEMASTER, Console::No },
            { "light",   HandleLight,   SEC_GAMEMASTER, Console::No },
            { "verdict", HandleVerdict, SEC_GAMEMASTER, Console::No },
            { "curse",   HandleCurse,   SEC_GAMEMASTER, Console::No },
            { "shield",  HandleShield,  SEC_GAMEMASTER, Console::No },
            { "heal",    HandleHeal,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_sm_whitemane_hard_mode()
{
    // D14's statics: harmless while wave 2 is unbound (D14's AI does not run then).
    SmWhitemane::RegisterWhitemaneHardMode([](Creature* /*whitemane*/) { return std::make_unique<TruthFight>(); });
    SmWhitemane::RegisterWhitemaneIdleHook([](WhitemaneFight& fight) { IdleTruth(fight, false); });
    // The Torch on every wave (its rev binds it now; unbound it acts as stock): a ScriptName with no script is a boot
    // error, and the reverse leaves its SmartAI rows dropped with nothing behind them.
    RegisterDungeonReworkGameObjectAI(go_sm_torch, ScarletMonasteryRework::kInstanceScriptName);
    if (kWave2Bound)
    {
        RegisterDungeonReworkCreatureAI(npc_sm_vigil_fairbanks, ScarletMonasteryRework::kInstanceScriptName);
        RegisterDungeonReworkCreatureAI(npc_sm_alexandros_spirit, ScarletMonasteryRework::kInstanceScriptName);
    }
    SmTest::RegisterBoss("truth", TheTruthTestCommands());
}
