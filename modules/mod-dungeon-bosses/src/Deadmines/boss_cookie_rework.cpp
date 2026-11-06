/*
 * mod-dungeon-bosses, Deadmines: Cookie (WP-B6). Build spec: DM 'Cookie' Build spec CK1-CK6, with the handoff's
 * corrections (deadmines-pilot.HANDOFF.md section 3.4 rows CK, section 8 #7: Fish Stew is a RunOut per drop plus a
 * lingering puddle). Replaces SmartAI 645 (two rows: Acid Splash and Cookie's Cooking, both kept here with the stock
 * timers); his patrol (creature_addon path 793440) is data and stays.
 *
 *   CK1 Acid Splash       stock 6306 on himself, 1-7 s then every 20-25 s (DD scales it on heroic); dispel list
 *   CK2 Cookie's Cooking  2 s interruptible self-heal (205333 5% / 205334 8%), then a Seasoned stack (cap 3 / 10);
 *                         interrupt list
 *   CK3 Taste Test        every 15 s from 6 s: a random non-tank eats a dish (heroic: two eaters, two different
 *                         dishes; Cookie::PickCourse); emote groups 0 / 2 / 3, a debuff naming the dish
 *   CK4 Chowder           registry cone 60 / 8 yd anchored on the eater, turning with them, 3 breaths 2 s apart,
 *                         25% Fire + Weakened; heroic rider Pepper Burn (30% over 6 s, Magic, dispel list)
 *   CK5 Fish Stew         per drop: RunOut 4 yd on the eater (2 s), then a 4 yd puddle there through DeadminesKit::
 *                         Linger, 10% / 15% Nature per second + the Standing in It slow, 30 s / 60 s
 *   CK6 Gut Bomb          RunOut 8 yd on the eater, 5 s / 4 s: 30% Nature + Weakened to the others; the eater takes
 *                         15% (205331); heroic knocks the others 6 yd away from the eater (OnHit)
 *
 * Seasoned (+10% damage done per stack) reaches the dishes through the script: their damage ignores caster
 * modifiers (the registry's rule), so every dish percent is multiplied by Cookie::SeasonedFactor.
 *
 * Every mechanic logs one INFO line in `scripts.dm`, prefix "dm-pilot cookie <mechanic>" (acceptance section 1 #4).
 */

#include "CookieLogic.h"
#include "DeadminesKit.h"
#include "DeadminesTestCommand.h"
#include "Chat.h"
#include "Creature.h"
#include "DynamicObject.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>
#include <list>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace DeadminesRework;
using namespace Cookie;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    enum CookieEvents : uint32
    {
        EVENT_ACID_SPLASH = 1,
        EVENT_COOKING,
    };

    uint32 SeasonedStacks(Unit const* cookie)
    {
        Aura const* aura = cookie ? cookie->GetAura(SPELL_SEASONED) : nullptr;
        return aura ? aura->GetStackAmount() : 0;
    }

    // A dish's percent with Cookie's Seasoned stacks applied (the dish damage ignores caster modifiers).
    float DishPct(Unit const* cookie, float pct)
    {
        return SeasonedPct(pct, SeasonedStacks(cookie));
    }

    char const* DifficultyName(bool heroic)
    {
        return heroic ? "heroic" : "normal";
    }

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }
}

// Cookie 645
struct boss_cookie_rework : public BossAI
{
    explicit boss_cookie_rework(Creature* creature) : BossAI(creature, BOSS_COOKIE) { }

    void Reset() override
    {
        BossAI::Reset();
        EndKitchen();
        me->RemoveAurasDueToSpell(SPELL_SEASONED);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        bool const heroic = DeadminesKit::IsHeroicMap(me);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_COOKIE;
        Mechanic::BeginEncounter(me, options);
        Describe(heroic);

        Talk(YELL_AGGRO);
        events.ScheduleEvent(EVENT_ACID_SPLASH, Ms(kAcidSplashFirstMinMs), Ms(kAcidSplashFirstMaxMs));
        ScheduleCooking(randtime(Ms(kCookingFirstMinMs), Ms(kCookingFirstMaxMs)));

        _lastKey = Dish::None;
        _kitchen.Schedule(Ms(kFeedFirstMs), [this](TaskContext context)
        {
            ServeCourse(nullptr);
            context.Repeat(Ms(kFeedEveryMs));
        });
        LOG_INFO(kLog, "dm-pilot cookie engage ({}), {} health", DifficultyName(heroic), me->GetMaxHealth());
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        EndKitchen();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        EndKitchen();
        BossAI::JustDied(killer);
        LOG_INFO(kLog, "dm-pilot cookie died ({}), Seasoned {}", DifficultyName(DeadminesKit::IsHeroicMap(me)),
            SeasonedStacks(me));
    }

    void UpdateAI(uint32 diff) override
    {
        // The dishes run on their own scheduler: a feed is instant and lands on time even while he casts, and a
        // `.dmtest cookie` dish runs out of combat too.
        _kitchen.Update(diff);
        BossAI::UpdateAI(diff);
    }

    void ExecuteEvent(uint32 eventId) override
    {
        switch (eventId)
        {
            case EVENT_ACID_SPLASH:
                CastAcidSplash();
                events.Repeat(Ms(kAcidSplashEveryMinMs), Ms(kAcidSplashEveryMaxMs));
                break;
            case EVENT_COOKING:
                StartCooking();
                ScheduleCooking(randtime(Ms(kCookingEveryMinMs), Ms(kCookingEveryMaxMs)));
                break;
            default:
                break;
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell->Id == SPELL_COOKIES_COOKING_NORMAL || spell->Id == SPELL_COOKIES_COOKING_HEROIC)
            CookingDone();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell->Id == SPELL_COOKIES_COOKING_NORMAL || spell->Id == SPELL_COOKIES_COOKING_HEROIC)
            LOG_INFO(kLog, "dm-pilot cookie cooking interrupted, Seasoned stays {}", SeasonedStacks(me));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CK1, CK2
    // ----------------------------------------------------------------------------------------------------------------

    void CastAcidSplash()
    {
        DoCastSelf(SPELL_ACID_SPLASH);
        LOG_INFO(kLog, "dm-pilot cookie acid-splash");
    }

    void StartCooking()
    {
        uint32 const spellId = kCookingSpell(DeadminesKit::IsHeroicMap(me));
        DoCastSelf(spellId);
        LOG_INFO(kLog, "dm-pilot cookie cooking cast {} (Seasoned {})", spellId, SeasonedStacks(me));
    }

    // A completed cast healed (the spell's HEAL_PCT): add a Seasoned stack below the cap (ruling 31).
    void CookingDone()
    {
        bool const heroic = DeadminesKit::IsHeroicMap(me);
        uint32 const stacks = SeasonedStacks(me);
        if (AddsSeasonedStack(stacks, heroic))
            me->CastSpell(me, SPELL_SEASONED, true);
        LOG_INFO(kLog, "dm-pilot cookie cooking completed ({}), Seasoned {} -> {} (cap {})", DifficultyName(heroic),
            stacks, SeasonedStacks(me), kSeasonedCap(heroic));
    }

    // `.dmtest cookie seasoned <n>`: sets the stacks (0 removes them); returns the stacks he has now.
    uint32 SetSeasoned(uint32 stacks)
    {
        me->RemoveAurasDueToSpell(SPELL_SEASONED);
        if (stacks)
        {
            me->CastSpell(me, SPELL_SEASONED, true);
            if (Aura* aura = me->GetAura(SPELL_SEASONED))
                aura->SetStackAmount(static_cast<uint8>(std::min<uint32>(stacks, kSeasonedCap(true))));
        }
        LOG_INFO(kLog, "dm-pilot cookie seasoned set to {}", SeasonedStacks(me));
        return SeasonedStacks(me);
    }

    void ScheduleCooking(Milliseconds in)
    {
        events.ScheduleEvent(EVENT_COOKING, in);
        Mechanic::NoteNextCastIn(me, kCookingSpell(DeadminesKit::IsHeroicMap(me)), in);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CK3 Taste Test
    // ----------------------------------------------------------------------------------------------------------------

    // One course on random non-tanks (Cookie::PickCourse). `fallback` (the `.dmtest` GM's pick) eats when nobody else
    // can: out of combat, or a party of the tank alone.
    void ServeCourse(Player* fallback)
    {
        bool const heroic = DeadminesKit::IsHeroicMap(me);
        std::list<Unit*> pool;
        SelectTargetList(pool, 40, SelectTargetMethod::Random, 0, 0.f, true, false);
        std::vector<Player*> eaters;
        for (Unit* unit : pool)
            if (Player* player = unit->ToPlayer())
                if (player->IsAlive() && !player->IsGameMaster())
                    eaters.push_back(player);
        if (eaters.empty())
        {
            Unit* victim = me->GetVictim();
            if (Player* tank = victim ? victim->ToPlayer() : nullptr)
                eaters.push_back(tank);
            else if (fallback)
                eaters.push_back(fallback);
        }
        uint8 const count = EatersFor(heroic, eaters.size());
        if (!count)
            return;
        Course const course = PickCourse(heroic, _lastKey, rand32());
        _lastKey = course.key;
        for (uint8 i = 0; i < count; ++i)
            Serve(course.dishes[i], eaters[i]);
    }

    void Serve(Dish dish, Player* eater)
    {
        if (!eater || dish == Dish::None)
            return;
        bool const heroic = DeadminesKit::IsHeroicMap(me);
        Talk(FeedTextGroup(dish), eater);
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellMod(SPELLVALUE_AURA_DURATION, static_cast<int32>(DishDebuffMs(dish, heroic)));
        me->CastSpell(eater, DishDebuffSpell(dish), args);
        LOG_INFO(kLog, "dm-pilot cookie taste-test {} on {} ({}, Seasoned {})", DishName(dish), eater->GetName(),
            DifficultyName(heroic), SeasonedStacks(me));
        switch (dish)
        {
            case Dish::Chowder:
                Chowder(eater, heroic);
                break;
            case Dish::Stew:
                Stew(eater, heroic);
                break;
            case Dish::GutBomb:
                GutBomb(eater, heroic);
                break;
            default:
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CK4 Fire Pepper Chowder: one persistent cone on the eater, a pass per breath
    // ----------------------------------------------------------------------------------------------------------------

    void Chowder(Player* eater, bool heroic)
    {
        float const pct = DishPct(me, kChowderPct(heroic));
        Map* map = me->GetMap();
        ObjectGuid const eaterGuid = eater->GetGUID();
        BossMechanics::ZoneSpec const cone = BossMechanics::Shapes::Cone(eater, kChowderAngleDeg, kChowderLengthYd);
        BossMechanics::MechanicRef ref = Mechanic::Zone(me, cone, Ms(kDishLeadMs));
        ref.FollowFacing().Persistent(Ms(kChowderPersistMs), Ms(kChowderBreathEveryMs)).Damage(pct)
            .School(SPELL_SCHOOL_FIRE).Spell(SPELL_CHOWDER_BREATH).Weakened().Tag(kTagChowder);
        if (heroic)
            ref.Rider(SPELL_PEPPER_BURN);
        ref.OnResolve([map, eaterGuid, pct, heroic](BossMechanics::ResolveResult const& result)
        {
            Player* e = ObjectAccessor::GetPlayer(map, eaterGuid);
            if (e && e->IsAlive())
                e->CastSpell(e, SPELL_CHOWDER_BREATH_VISUAL, true);
            LOG_INFO(kLog, "dm-pilot cookie chowder breath {}/{} ({:.1f}%{}): {} hit", result.pass + 1,
                kChowderBreaths, pct, heroic ? " + pepper burn" : "", result.hits.size());
        });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CK5 Week-Old Fish Stew: a RunOut 4 yd before each drop, a lingering puddle at each
    // ----------------------------------------------------------------------------------------------------------------

    void Stew(Player* eater, bool heroic)
    {
        ObjectGuid const eaterGuid = eater->GetGUID();
        StewDrop(eaterGuid, 0, heroic);
        for (uint32 drop = 1; drop < kStewDrops; ++drop)
            _kitchen.Schedule(Ms(drop * kStewDropEveryMs), [this, eaterGuid, drop, heroic](TaskContext /*context*/)
            {
                StewDrop(eaterGuid, drop, heroic);
            });
    }

    // Drop `drop` (0-based): the RunOut ring now, the puddle where the eater stands when it resolves.
    void StewDrop(ObjectGuid eaterGuid, uint32 drop, bool heroic)
    {
        Player* eater = ObjectAccessor::GetPlayer(me->GetMap(), eaterGuid);
        if (!eater || !eater->IsAlive())
            return;
        float const pct = DishPct(me, kStewPct(heroic));
        Map* map = me->GetMap();
        ObjectGuid const cookieGuid = me->GetGUID();
        BossMechanics::MechanicRef ref = Mechanic::RunOut(me, eater, kStewRunOutYd, Ms(kStewDropEveryMs));
        ref.Tag(kTagStewRunOut);
        ref.OnResolve([map, cookieGuid, eaterGuid, drop, pct, heroic](BossMechanics::ResolveResult const& result)
        {
            Creature* cookie = map->GetCreature(cookieGuid);
            Player* e = ObjectAccessor::GetPlayer(map, eaterGuid);
            if (!cookie || !e || !e->IsAlive())
                return;
            e->CastSpell(e, SPELL_STEW_VOMIT_VISUAL, true);
            e->CastSpell(e, kStewPuddleVisual(heroic), true);
            DeadminesKit::LingerSpec linger;
            linger.duration = Milliseconds(kStewPuddleMs(heroic));
            linger.tick = Milliseconds(kStewTickMs);
            linger.pct = pct;
            linger.school = SPELL_SCHOOL_NATURE;
            linger.spellId = SPELL_STEW_PUDDLE;
            linger.slow = true;
            linger.color = BossMechanics::Color::Green;
            linger.tag = kTagStewPuddle;
            DeadminesKit::Linger(cookie, BossMechanics::Shapes::Circle(e->GetPosition(), kStewPuddleYd), linger);
            LOG_INFO(kLog, "dm-pilot cookie stew puddle {}/{} ({:.1f}%/s for {} s) at {:.1f} {:.1f}; {} near the eater",
                drop + 1, kStewDrops, pct, kStewPuddleMs(heroic) / 1000, e->GetPositionX(), e->GetPositionY(),
                result.hits.size());
        });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CK6 Gut Bomb
    // ----------------------------------------------------------------------------------------------------------------

    void GutBomb(Player* eater, bool heroic)
    {
        float const pct = DishPct(me, kGutBombPct);
        Map* map = me->GetMap();
        ObjectGuid const cookieGuid = me->GetGUID();
        ObjectGuid const eaterGuid = eater->GetGUID();
        BossMechanics::MechanicRef ref = Mechanic::RunOut(me, eater, kGutBombYd, Ms(kGutBombDelayMs(heroic)));
        ref.Damage(pct).School(SPELL_SCHOOL_NATURE).Spell(SPELL_GUT_BOMB_BELCH).Weakened().Tag(kTagGutBomb);
        if (heroic)
        {
            // A Rider would knock away from the owner (Cookie): knock away from the eater instead.
            float const speedXY = KnockbackSpeedXY(kGutBombKnockbackYd, kGutBombKnockbackSpeedZ);
            ref.OnHit([eaterGuid, speedXY](Unit* hit)
            {
                Unit* e = hit ? ObjectAccessor::GetUnit(*hit, eaterGuid) : nullptr;
                if (!e || e == hit || !hit->IsAlive())
                    return;
                hit->KnockbackFrom(e->GetPositionX(), e->GetPositionY(), speedXY, kGutBombKnockbackSpeedZ);
            });
        }
        ref.OnResolve([map, cookieGuid, eaterGuid, pct, heroic](BossMechanics::ResolveResult const& result)
        {
            Creature* cookie = map->GetCreature(cookieGuid);
            Player* e = ObjectAccessor::GetPlayer(map, eaterGuid);
            if (!cookie || !e || !e->IsAlive())
                return;
            e->CastSpell(e, SPELL_GUT_BOMB_VISUAL, true);
            cookie->CastSpell(e, SPELL_GUT_BOMB_EATER, true);
            LOG_INFO(kLog, "dm-pilot cookie gutbomb belch ({:.1f}%{}): {} others hit", pct,
                heroic ? " + knockback" : "", result.hits.size());
        });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Descriptor and cleanup
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order Cookie; interrupt Cookie's Cooking (expected on heroic); dispel Acid Splash (Poison) and, on heroic,
    // the Pepper Burn (Magic, expected). No purges: Seasoned is not dispellable (the counter is the interrupt).
    void Describe(bool heroic)
    {
        BossMechanics::Descriptor d;
        d.interrupts.push_back({ NPC_COOKIE, kCookingSpell(heroic), static_cast<uint8>(heroic ? 2 : 1),
            Ms((kCookingEveryMinMs + kCookingEveryMaxMs) / 2) });
        d.dispels.push_back({ SPELL_ACID_SPLASH, 1 });
        if (heroic)
            d.dispels.push_back({ SPELL_PEPPER_BURN, 2 });
        d.targets.push_back({ NPC_COOKIE, 1 });
        Mechanic::Describe(me, std::move(d));
    }

    // Stops the dishes and removes the eaters' puddle visuals (the registry drops the zones with the encounter).
    void EndKitchen()
    {
        _kitchen.CancelAll();
        _lastKey = Dish::None;
        if (!me->IsInWorld())
            return;
        me->GetMap()->DoForAllPlayers([](Player* player)
        {
            for (uint32 spellId : { SPELL_STEW_PUDDLE_VISUAL_NORMAL, SPELL_STEW_PUDDLE_VISUAL_HEROIC })
                for (uint8 guard = 0; guard < 16; ++guard)
                {
                    DynamicObject* puddle = player->GetDynObject(spellId);
                    if (!puddle || !puddle->IsInWorld())
                        break;
                    puddle->Remove();
                }
        });
    }

    TaskScheduler _kitchen;
    Dish _lastKey = Dish::None;
};

// 205331 Gut Bomb, the eater's own belch: 15% of reference health, Seasoned included (unavoidable, no Weakened).
class spell_dm_cookie_gut_bomb_eater : public SpellScript
{
    PrepareSpellScript(spell_dm_cookie_gut_bomb_eater);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        SetEffectValue(static_cast<int32>(DeadminesKit::RefFlat(caster, DishPct(caster, kGutBombEaterPct))));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_dm_cookie_gut_bomb_eater::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// 205323 Pepper Burn (heroic chowder rider): each 1 s tick is 5% of reference health, Seasoned included.
class spell_dm_cookie_pepper_burn : public AuraScript
{
    PrepareAuraScript(spell_dm_cookie_pepper_burn);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        Unit* caster = GetCaster();
        amount = static_cast<int32>(DeadminesKit::RefFlat(caster, DishPct(caster, kPepperBurnPctPerTick)));
        canBeRecalculated = false;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dm_cookie_pepper_burn::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

namespace
{
    // `.dmtest cookie ...`: the boss in reach and its rework AI (nullptr with an error when either is missing).
    boss_cookie_rework* FindCookie(ChatHandler* handler)
    {
        Creature* boss = DeadminesTest::FindBoss(handler, NPC_COOKIE);
        if (!boss)
            return nullptr;
        auto* ai = dynamic_cast<boss_cookie_rework*>(boss->AI());
        if (!ai)
            handler->SendErrorMessage("Cookie is not running boss_cookie_rework (instance script not bound?).");
        return ai;
    }

    // The eater for a test dish: the GM's selected player, else the GM.
    Player* TestEater(ChatHandler* handler)
    {
        return handler->getSelectedPlayerOrSelf();
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return DeadminesTest::ShowBossInfo(handler, NPC_COOKIE, BOSS_COOKIE);
    }

    // `.dmtest cookie feed`: one real course (random dish order, random non-tanks; the selected player or the GM when
    // nobody else can eat).
    bool HandleFeed(ChatHandler* handler)
    {
        boss_cookie_rework* ai = FindCookie(handler);
        if (!ai)
            return false;
        ai->ServeCourse(TestEater(handler));
        handler->SendSysMessage("Cookie serves a course.");
        return true;
    }

    bool ServeTest(ChatHandler* handler, Dish dish)
    {
        boss_cookie_rework* ai = FindCookie(handler);
        Player* eater = TestEater(handler);
        if (!ai || !eater)
            return false;
        ai->Serve(dish, eater);
        handler->PSendSysMessage("Cookie feeds {} the {}.", eater->GetName(), DishName(dish));
        return true;
    }

    bool HandleChowder(ChatHandler* handler)
    {
        return ServeTest(handler, Dish::Chowder);
    }

    bool HandleStew(ChatHandler* handler)
    {
        return ServeTest(handler, Dish::Stew);
    }

    bool HandleGutBomb(ChatHandler* handler)
    {
        return ServeTest(handler, Dish::GutBomb);
    }

    bool HandleCooking(ChatHandler* handler)
    {
        boss_cookie_rework* ai = FindCookie(handler);
        if (!ai)
            return false;
        ai->StartCooking();
        return true;
    }

    bool HandleSplash(ChatHandler* handler)
    {
        boss_cookie_rework* ai = FindCookie(handler);
        if (!ai)
            return false;
        ai->CastAcidSplash();
        return true;
    }

    bool HandleSeasoned(ChatHandler* handler, uint32 stacks)
    {
        boss_cookie_rework* ai = FindCookie(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Cookie: Seasoned {}.", ai->SetSeasoned(stacks));
        return true;
    }

    ChatCommandTable const& CookieTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
            { "feed", HandleFeed, SEC_GAMEMASTER, Console::No },
            { "chowder", HandleChowder, SEC_GAMEMASTER, Console::No },
            { "stew", HandleStew, SEC_GAMEMASTER, Console::No },
            { "gutbomb", HandleGutBomb, SEC_GAMEMASTER, Console::No },
            { "cooking", HandleCooking, SEC_GAMEMASTER, Console::No },
            { "splash", HandleSplash, SEC_GAMEMASTER, Console::No },
            { "seasoned", HandleSeasoned, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_cookie_rework()
{
    RegisterDeadminesReworkCreatureAI(boss_cookie_rework);
    RegisterSpellScript(spell_dm_cookie_gut_bomb_eater);
    RegisterSpellScript(spell_dm_cookie_pepper_burn);
    DeadminesTest::RegisterBoss("cookie", CookieTestCommands());
}
