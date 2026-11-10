/*
 * mod-dungeon-bosses, Shadowfang Keep: Razorclaw the Butcher (WP-S2). Build spec: SK 444-479 (build spec), SK 357-443
 * (design), RC1-RC5; handoff section 3.5 rows RC and section 3.6 row S2. Replaces stock SmartAI 3886 (Butcher Drain
 * 7485, removed: WP-S2's SQL rev); bound by apps/dbc-tools source/npcs/shadowfang_keep/razorclaw.py.
 *
 *   RC1  Meat Hook       MeatHook::Throw (MeatHook.h, shared with Silverlaine's Echo of Razorclaw): a 2 s line from him
 *                        through a random non-tank 8+ yd away, 5 yd past it, clipped at the kitchen walls, the first
 *                        4 yd excluded; 35% + Weakened, then a drag to his front (look 205932). First at 8 s, then
 *                        every 15 s; skipped when nobody is 8 yd out. Heroic: Twin Hooks (two lines, two players, one
 *                        hit per player per throw) and Hung to Bleed (20% over 8 s).
 *   RC2  Tenderize       each melee hit on his victim adds a Tenderized stack (205934: +10% melee damage taken each).
 *   RC3  Butcher's Cut   at 3 stacks: the 2 s cast bar, a registry Frontal 90 degrees / 10 yd (tank exempt): 40% +
 *                        Weakened on non-tanks; the tank, if in the cone, takes 205937 (250% weapon); the stacks clear.
 *                        Never within 3 s after a hook landed, and no hook while a Cut is one swing away or running
 *                        (Razorclaw::Rhythm, on the AI's own clock, which no cast bar pauses).
 *   RC4  Offal Slick     heroic: each Cut leaves its cone on the floor 30 s (DungeonKit::Linger, a fixed-point cone,
 *                        5% a second + the kit's 205201 slow, no Weakened), dressed with three blood pools (GO 301103).
 *   RC5  Melee           DamageModifier 2.0 on the stock 3.2 s swing (DT); heroic melee is the heroic template's.
 *   Arena                DungeonKit::ArenaGuard on RazorclawArena() (the kitchen): pull grip, grip back after 1.5 s
 *                        off it (look 205932), he never chases off it and evades when he is pulled off.
 *
 * Every firing logs one INFO line "sfk razorclaw <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "Map.h"
#include "MeatHook.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RazorclawLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "StringFormat.h"
#include <functional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;
using namespace Razorclaw;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kLogBoss = "razorclaw";

    // The kitchen's arena guard: the shared kit's defaults (1.5 s grace, 3 s cooldown, 250 ms sweep), the hook's chain
    // as the grip look.
    DungeonKit::ArenaGuardOptions KitchenGuardOptions()
    {
        DungeonKit::ArenaGuardOptions o;
        // A unit in combat with another live boss is left to that boss: no two guards grip it to and fro (R2 S-2).
        o.skipGrip = DungeonKit::SkipEngagedWithOtherBoss(ShadowfangKeepRework::IsSfkBossEntry);
        DungeonKit::ApplyPlaytestPullRule(o);
        o.teleport = false;                 // the one SFK guard that still jumps: the meat hook reels them in
        o.gripSpell = SPELL_RC_MEAT_HOOK_CHAIN;
        o.logPrefix = "sfk razorclaw";
        o.offArenaReason = "off-kitchen";
        return o;
    }
}

// Razorclaw the Butcher 3886
struct boss_razorclaw_rework : public BossAI
{
    enum RazorclawEvents : uint32
    {
        EVENT_MEAT_HOOK = 1,
    };

    explicit boss_razorclaw_rework(Creature* creature) : BossAI(creature, BOSS_RAZORCLAW),
        _kitchen(RazorclawArena()), _arena(RazorclawArena(), KitchenGuardOptions()) { }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RAZORCLAW;
        Mechanic::BeginEncounter(me, options);
        // Boss data (build spec): none (no kill order, interrupts or dispels): no descriptor.

        Cleanup();      // a `.sfktest` mechanic out of combat may have left something behind
        _arena.Engage(me);
        Talk(YELL_RAZORCLAW_AGGRO);
        events.ScheduleEvent(EVENT_MEAT_HOOK, Milliseconds(kHookFirstMs));
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "engage",
            Acore::StringFormat("heroic={} hookFirst={}ms", IsHeroicMap(me) ? 1 : 0, kHookFirstMs));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        Cleanup();
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "death");
    }

    // RC2 Tenderize: a melee hit that lands on his victim adds a stack (the aura raises the next hits, not this one).
    void DamageDealt(Unit* victim, uint32& damage, DamageEffectType damageType, SpellSchoolMask /*schoolMask*/) override
    {
        if (damageType != DIRECT_DAMAGE || !damage || !victim || victim != me->GetVictim() || !me->IsEngaged())
            return;
        uint32 const stacks = DungeonKit::AddStacks(victim, SPELL_RC_TENDERIZED, 1, me, kTenderizeMaxStacks);
        if (!stacks)
            return;
        _tenderized.insert(victim->GetGUID());
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "tenderize",
            Acore::StringFormat("unit={} stacks={}", victim->GetName(), stacks));
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // pulled off the kitchen: evading

        events.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        if (TryButchersCut())
            return;

        while (uint32 const eventId = events.ExecuteEvent())
        {
            ExecuteEvent(eventId);
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }

        DoMeleeAttackIfReady();
    }

    void ExecuteEvent(uint32 eventId) override
    {
        switch (eventId)
        {
            case EVENT_MEAT_HOOK:
                if (!_rhythm.HookMayStart(_clockMs, TankStacks()))
                {
                    events.ScheduleEvent(EVENT_MEAT_HOOK, Milliseconds(kHookRetryMs));
                    break;
                }
                MeatHookNow(IsHeroicMap(me), false);
                events.ScheduleEvent(EVENT_MEAT_HOOK, Milliseconds(kHookEveryMs));
                break;
            default:
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RC1 Meat Hook (MeatHook.h)
    // ----------------------------------------------------------------------------------------------------------------

    // False when nobody qualified (skipped).
    bool MeatHookNow(bool heroic, bool widen)
    {
        MeatHook::ThrowSpec spec;
        spec.tuning = HookFor(heroic);
        spec.emote = EMOTE_RAZORCLAW_MEAT_HOOK;
        spec.clip = &_kitchen;
        spec.widen = widen;
        spec.logBoss = kLogBoss;
        MeatHook::ThrowResult const thrown = MeatHook::Throw(me, spec);
        if (!thrown)
            return false;
        for (BossMechanics::MechanicHandle const& handle : thrown.lines)
            Track(handle);
        _rhythm.HookThrown(_clockMs, spec.tuning.warnMs);
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RC3 Butcher's Cut (+ RC4 heroic Offal Slick)
    // ----------------------------------------------------------------------------------------------------------------

    uint32 TankStacks() const
    {
        Unit const* tank = me->GetVictim();
        return tank ? DungeonKit::Stacks(tank, SPELL_RC_TENDERIZED, me->GetGUID()) : 0;
    }

    bool TryButchersCut()
    {
        if (!_rhythm.CutMayStart(_clockMs, TankStacks()))
            return false;
        ButchersCut(IsHeroicMap(me));
        return true;
    }

    void ButchersCut(bool heroic)
    {
        if (Unit* victim = me->GetVictim())
            me->SetFacingToObject(victim);
        DungeonKit::CastBar(me, SPELL_RC_BUTCHERS_CUT_CAST, nullptr, EMOTE_RAZORCLAW_BUTCHERS_CUT);
        MechanicRef ref = Mechanic::Cone(me, me, kCutAngleDeg, kCutLengthYd, Milliseconds(kCutWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(kCutPct(heroic)).Weakened().Spell(SPELL_RC_BUTCHERS_CUT_HIT).Tag(TAG_BUTCHERS_CUT);
        ref.OnResolve(OnRazorclaw([heroic](boss_razorclaw_rework& ai, BossMechanics::ResolveResult const& result)
        {
            ai.ButchersCutLanded(heroic, result.hits.size());
        }));
        Track(ref.Handle());
        _rhythm.CutStarted(_clockMs, kCutWarnMs);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "butchers-cut",
            Acore::StringFormat("heroic={} stacks={} notBefore={}ms now={}ms", heroic ? 1 : 0, TankStacks(),
                _rhythm.CutNotBeforeMs(), _clockMs));
    }

    // The cone resolved (non-tanks hit by the registry): the stacks clear, then the tank's own hit if it stands in the
    // cone (cleared first, so Tenderized does not raise the Cut itself), then the heroic slick.
    void ButchersCutLanded(bool heroic, std::size_t hits)
    {
        Unit* tank = me->GetVictim();
        _rhythm.CutLanded();
        ClearTenderized();
        bool tankHit = false;
        if (tank && tank->IsAlive() && InCutCone(DungeonKit::PlaneOf(me), me->GetOrientation(),
            DungeonKit::PlaneOf(tank), me->GetCombatReach() + tank->GetCombatReach()))
        {
            me->CastSpell(tank, SPELL_RC_BUTCHERS_CUT_TANK, true);
            tankHit = true;
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "butchers-cut-landed",
            Acore::StringFormat("nonTanksHit={} tank={} tankHit={}", hits, tank ? tank->GetName() : "none",
                tankHit ? 1 : 0));
        if (kOffalSlick(heroic))
            OffalSlick();
    }

    void OffalSlick()
    {
        Position const at = me->GetPosition();
        float const facing = me->GetOrientation();
        DungeonKit::LingerSpec linger;
        linger.duration = Milliseconds(kSlickMs);
        linger.tick = Milliseconds(kSlickTickMs);
        linger.pct = kSlickPct;
        linger.spellId = SPELL_RC_OFFAL_SLICK;
        linger.tag = TAG_OFFAL_SLICK;
        Track(DungeonKit::Linger(me, BossMechanics::Shapes::Cone(Position(at.GetPositionX(), at.GetPositionY(),
            at.GetPositionZ(), facing), kCutAngleDeg, kCutLengthYd), linger).Handle());

        std::size_t pools = 0;
        for (Vec2 const& p : SlickPoolPoints(DungeonKit::PlaneOf(me), facing))
        {
            float z = me->GetMapHeight(p.x, p.y, at.GetPositionZ() + 2.f);
            if (z <= INVALID_HEIGHT + 1.f)
                z = at.GetPositionZ();
            if (GameObject* pool = me->SummonGameObject(GO_SFK_OFFAL_SLICK, p.x, p.y, z, facing, 0.f, 0.f, 0.f, 0.f,
                kSlickMs / IN_MILLISECONDS))
            {
                _pools.push_back(pool->GetGUID());
                ++pools;
            }
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "offal-slick",
            Acore::StringFormat("at=({:.1f},{:.1f}) facing={:.2f} pools={}", at.GetPositionX(), at.GetPositionY(),
                facing, pools));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.sfktest razorclaw` entry points (one mechanic on demand; `heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Hook,
        Cut,
        Slick,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return "Razorclaw is casting; try again in a moment.";
        switch (mechanic)
        {
            case TestMechanic::Hook:
                if (!MeatHookNow(heroic, true))
                    return "Nobody to hook: stand 8+ yd from him in line of sight (.gm off, alive).";
                break;
            case TestMechanic::Cut:
                ButchersCut(heroic);
                break;
            case TestMechanic::Slick:
                OffalSlick();
                break;
        }
        return {};
    }

    bool HeroicMap() const
    {
        return IsHeroicMap(me);
    }

    // One Tenderized stack on `unit` (at 3 on his victim in combat, the Cut follows).
    uint32 TestTenderize(Unit* unit)
    {
        uint32 const stacks = DungeonKit::AddStacks(unit, SPELL_RC_TENDERIZED, 1, me, kTenderizeMaxStacks);
        if (stacks)
            _tenderized.insert(unit->GetGUID());
        return stacks;
    }

    void TestGrip(Unit* unit)
    {
        _arena.Grip(me, unit, "test");
    }

    bool InArena(WorldObject const* o) const
    {
        return _arena.Contains(o);
    }

private:
    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*; STAGE-M5-R-REPORT m-4).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnRazorclaw(Fn fn)
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
            if (auto* ai = dynamic_cast<boss_razorclaw_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void Track(BossMechanics::MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    void ClearTenderized()
    {
        for (ObjectGuid const& guid : _tenderized)
            if (Unit* unit = ObjectAccessor::GetUnit(*me, guid))
                unit->RemoveAurasDueToSpell(SPELL_RC_TENDERIZED, me->GetGUID());
        _tenderized.clear();
    }

    void DespawnPools()
    {
        for (ObjectGuid const& guid : _pools)
            if (GameObject* pool = me->GetMap()->GetGameObject(guid))
                pool->Delete();
        _pools.clear();
    }

    // The pull's state: nothing pending, no slick, no stacks (Reset, evade, death, a new pull).
    void Cleanup()
    {
        for (BossMechanics::MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        DespawnPools();
        ClearTenderized();
        MeatHook::Forget(me);
        events.Reset();
        _rhythm.Reset();
        _clockMs = 0;
        _arena.Reset();
    }

    DungeonKit::Arena _kitchen;                 // the hook lines' clip (MeatHook::ThrowSpec::clip)
    DungeonKit::ArenaGuard _arena;
    Rhythm _rhythm;
    uint64 _clockMs = 0;                        // ms since the pull; Rhythm's clock
    GuidSet _tenderized;
    std::vector<ObjectGuid> _pools;
    std::vector<BossMechanics::MechanicHandle> _live;
};

namespace
{
    boss_razorclaw_rework* FindRazorclawAI(ChatHandler* handler)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_RAZORCLAW);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_razorclaw_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Razorclaw is not running boss_razorclaw_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_razorclaw_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_razorclaw_rework* ai = FindRazorclawAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Razorclaw: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_RAZORCLAW, BOSS_RAZORCLAW);
    }

    bool HandleHook(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_razorclaw_rework::TestMechanic::Hook, heroic, "Meat Hook (RC1; heroic: Twin Hooks, "
            "Hung to Bleed)");
    }

    bool HandleCut(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_razorclaw_rework::TestMechanic::Cut, heroic, "Butcher's Cut (RC3; heroic: + RC4)");
    }

    bool HandleSlick(ChatHandler* handler)
    {
        return Fire(handler, boss_razorclaw_rework::TestMechanic::Slick, {}, "Offal Slick (RC4)");
    }

    // `.sfktest razorclaw tenderize`: one Tenderized stack on the GM (RC2).
    bool HandleTenderize(ChatHandler* handler)
    {
        boss_razorclaw_rework* ai = FindRazorclawAI(handler);
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!ai || !gm)
            return false;
        handler->PSendSysMessage("Razorclaw: Tenderized on you, {} stack(s).", ai->TestTenderize(gm));
        return true;
    }

    // `.sfktest razorclaw grip`: the arena guard's grip on the GM now (and whether the GM stands in the kitchen).
    bool HandleGrip(ChatHandler* handler)
    {
        boss_razorclaw_rework* ai = FindRazorclawAI(handler);
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!ai || !gm)
            return false;
        bool const inside = ai->InArena(gm);
        ai->TestGrip(gm);
        handler->PSendSysMessage("Razorclaw: you were {} the kitchen arena; grip fired.",
            inside ? "inside" : "outside");
        return true;
    }

    // `.sfktest razorclaw <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& RazorclawTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "hook",      HandleHook,      SEC_GAMEMASTER, Console::No },
            { "cut",       HandleCut,       SEC_GAMEMASTER, Console::No },
            { "slick",     HandleSlick,     SEC_GAMEMASTER, Console::No },
            { "tenderize", HandleTenderize, SEC_GAMEMASTER, Console::No },
            { "grip",      HandleGrip,      SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_razorclaw_rework()
{
    RegisterDungeonReworkCreatureAI(boss_razorclaw_rework, ShadowfangKeepRework::kInstanceScriptName);
    MeatHook::AddSC_meat_hook();
    SfkTest::RegisterBoss("razorclaw", RazorclawTestCommands());
}
