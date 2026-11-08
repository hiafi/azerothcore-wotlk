/*
 * mod-dungeon-bosses, Shadowfang Keep: Commander Springvale and his three Risen Guardsmen (WP-S4). Build spec: SK
 * 754-812 (build spec), SK 625-753 (design), SP1-SP10; handoff section 3.5 rows SP and section 3.6 row S4. Replaces
 * the stock SmartAI 4278 (Hammer of Justice 5588, Holy Light 1026, Divine Shield 33581 are gone; the aggro and death
 * yells are kept here). User ruling (handoff section 10, section 7 #20): the Oath is damage taken -90%, not
 * immunity; he stays attackable and keeps his threat.
 *
 * Springvale (normal and heroic):
 *   SP1 Hammer of Judgement  every 18 s from 8 s on a random non-tank: emote 2, a registry RunOut (8 yd, 3 s ring);
 *                            the others within 8 yd take 25% Holy + Weakened + a 1.5 s stun (205967); the marked
 *                            player takes 10% (205966, the thrown hammer, RefFlat). Normal: also during the Oath.
 *   SP2 Ricochet (H)         a Hammer landing on a marked player standing in a live Consecration bounces once to the
 *                            nearest other player, the tank included: a 2 s ring, the same landing; never twice.
 *   SP3 Consecration         every 20 s from 12 s under him (not during the Oath): DungeonKit::Linger, 8 yd, 1 s
 *                            ticks of 5% Holy, 10 s normal / 40 s heroic; the holy ground look 205971 / 205972.
 *   SP4 Holy Light           below 60%, every 10 s (not during the Oath): 2.5 s interruptible, heals 5% of his health.
 *   SP5 Searing Light (H)    every Holy Light that finishes (his or the Guardsman of the Light's): 15% Holy to every
 *                            player (RefFlat).
 *   SP6 Unbreakable Oath     once at 30%: yell 3, damage taken -90% (205975), no melee, Holy Light or Consecration;
 *                            the three guardsmen rise at the hall's three points (2 s look, then they act). Each one
 *                            killed cracks it (205976 stacks); the third shatters it. Normal: 30 s cap, then the
 *                            shield drops on its own (no Oathbroken) and any standing guardsman fights on.
 *   SP7 Oathbroken           on the shatter: damage taken +25% for 6 s.
 *   SP8 Wrath of God (H)     with the Oath: a 30 s cast that cannot be kicked (yell 4, emote 5 at 10 s left); the
 *                            shatter interrupts it; finished, it kills every player (205979).
 * The guardsmen (300506 Light, 300507 Hammer, 300508 Altar): melee only on normal; on heroic the Light casts Holy
 * Light every 10 s on the most wounded of Springvale and the guardsmen (+ Searing Light), the Hammer throws Hammer of
 * Judgement 4 s after rising then every 12 s (emote 0), the Altar consecrates under itself at once and every 15 s.
 * Descriptor: kill order Light (3), Hammer (2), Altar (1), then Springvale; the DPS always, the tank too while the
 * Oath holds (phase 1), so the bots kill the guardsmen before Wrath of God (acceptance #5); interrupts Holy Light
 * (the Light's first); Wrath of God listed as do-not-kick.
 *
 * Timers run on `_timers` (no validator), so a cast bar never pauses them (the Pilot's lesson R1 S-2); one-shot
 * follow-ups (the thrown hammer) ride m_Events. The Oath's clock is SpringvaleLogic.h's OathTimeline, advanced every
 * tick. Every firing logs one line, "sfk springvale <mechanic> ...", and `.sfktest springvale <mechanic>` fires one
 * on demand (see SpringvaleTestCommands below).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameTime.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "SpringvaleLogic.h"
#include "StringFormat.h"
#include <algorithm>
#include <list>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;
using namespace Springvale;

namespace
{
    float constexpr kAddSearchRange = 80.f;

    void LogSv(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, "springvale", mechanic, detail);
    }

    // Every player of the fight: alive, in the world, not a GM, within kRoomRange of `center`.
    std::vector<Player*> RoomPlayers(WorldObject* center)
    {
        std::vector<Player*> out;
        for (auto const& ref : center->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p || !p->IsInWorld() || !p->IsAlive() || p->IsGameMaster() || p->GetDistance(center) > kRoomRange)
                continue;
            out.push_back(p);
        }
        return out;
    }

    std::vector<uint32> GuardsmanEntries()
    {
        std::vector<uint32> entries;
        for (GuardsmanInfo const& g : kGuardsmen)
            entries.push_back(g.entry);
        return entries;
    }

    Creature* FindSpringvale(WorldObject* near)
    {
        InstanceScript* instance = near->GetInstanceScript();
        Creature* boss = instance ? instance->GetCreature(DATA_SPRINGVALE_GUID) : nullptr;
        return boss && boss->IsAlive() ? boss : nullptr;
    }

    char const* EndName(OathEnd end)
    {
        switch (end)
        {
            case OathEnd::Shattered:
                return "shattered";
            case OathEnd::CapExpired:
                return "cap";
            case OathEnd::WrathLanded:
                return "wrath";
            default:
                return "none";
        }
    }
}

// Commander Springvale 4278
struct boss_commander_springvale_rework : public BossAI
{
    explicit boss_commander_springvale_rework(Creature* creature) : BossAI(creature, BOSS_SPRINGVALE) { }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        Talk(YELL_SPRINGVALE_AGGRO);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_SPRINGVALE;
        Mechanic::BeginEncounter(me, options);
        DescribeEncounter();
        _arena.Engage(me);
        ScheduleFight();
        LogSv("engage", Acore::StringFormat("heroic={} players={} health={}", DungeonKit::IsHeroicMap(me) ? 1 : 0,
            RoomPlayers(me).size(), me->GetMaxHealth()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        _EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        Cleanup();
        _JustDied();
        Talk(YELL_SPRINGVALE_DEATH);
        LogSv("died");
    }

    // The guardsmen act only after their rise (npc_sfk_risen_guardsman zones itself in): no zone-in here.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
        Mechanic::TrackUnit(me, summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        if (GuardsmanOf(summon->GetEntry()))
            GuardsmanDied(summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (_oath.Used() || !me->IsInCombat())
            return;
        // The Oath cannot be skipped: a hit that would kill him before it leaves him at 1 health, also between the
        // crossing hit and the UpdateAI that starts it (R1 N-2).
        if (damage >= me->GetHealth())
            damage = me->GetHealth() - 1;
        if (_oathPending)
            return;
        float const after = 100.f * float(me->GetHealth() - damage) / float(std::max<uint32>(me->GetMaxHealth(), 1));
        if (OathTriggers(after, false))
            _oathPending = true;
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell->Id == SPELL_SV_HOLY_LIGHT)
            HolyLightLanded(me);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell->Id == SPELL_SV_HOLY_LIGHT)
            LogSv("holy-light-interrupted", "caster=springvale");
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.sfktest` mechanic's timers and the Oath's clock.
        _timers.Update(diff);
        AdvanceOath(diff);

        if (!UpdateVictim())
            return;

        if (_oathPending)
        {
            _oathPending = false;
            StartOath();
        }

        if (!_arena.Update(me, diff))
            return;

        if (!BossMelees(_oath.Active()) || me->HasUnitState(UNIT_STATE_CASTING))
            return;

        DoMeleeAttackIfReady();
    }

    // ---- mechanics (also called by the guardsmen and `.sfktest`) ---------------------------------------------------

    // SP1: `source` (Springvale or the Guardsman of the Hammer) marks a random non-tank of its own threat list
    // (`forced`: that player). False when nobody qualifies.
    bool ThrowHammer(Creature* source, Player* forced = nullptr)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            rule.maxRange = kRoomRange;
            target = DungeonKit::PickPlayer(source, rule);
        }
        if (!target)
            return false;
        if (source == me)
            Talk(EMOTE_SPRINGVALE_HAMMER, target);
        else if (source->IsAIEnabled)
            source->AI()->Talk(EMOTE_GUARDSMAN_HAMMER, target);
        Hammer(source, target, false);
        return true;
    }

    // SP3: a pool under `at`; its look is cast by Springvale so it stays when an Altar guardsman dies.
    void Consecrate(Position const& at, char const* by)
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        DungeonKit::LingerSpec linger;
        linger.duration = kConsecrationDuration(heroic);
        linger.tick = kConsecrationTick;
        linger.pct = kConsecrationPct(heroic);
        linger.school = SPELL_SCHOOL_HOLY;
        linger.spellId = SPELL_SV_CONSECRATION;
        linger.slow = false;
        linger.tag = TAG_CONSECRATION;
        BossMechanics::MechanicHandle const pool = DungeonKit::Linger(me,
            BossMechanics::Shapes::Circle(at, kConsecrationYd), linger);
        _pools.Add(pool.id, NowMs() + linger.duration.count());
        me->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(),
            heroic ? SPELL_SV_CONSECRATION_GROUND_H : SPELL_SV_CONSECRATION_GROUND, true);
        LogSv("consecration", Acore::StringFormat("by={} id={} duration_ms={} pools={}", by, pool.id,
            linger.duration.count(), _pools.Size()));
    }

    // SP4: his own heal.
    bool HolyLight()
    {
        if (me->CastSpell(me, SPELL_SV_HOLY_LIGHT, false) != SPELL_CAST_OK)
            return false;
        Mechanic::NoteNextCastIn(me, SPELL_SV_HOLY_LIGHT, kHolyLightEvery + kHolyLightCast);
        LogSv("holy-light", Acore::StringFormat("caster=springvale health_pct={:.1f}", me->GetHealthPct()));
        return true;
    }

    // SP5: a Holy Light finished (his or the Guardsman of the Light's).
    void HolyLightLanded(Creature* caster)
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        LogSv("holy-light-landed", Acore::StringFormat("caster={} searing={}", caster == me ? "springvale" : "light",
            heroic ? 1 : 0));
        if (heroic)
            SearingLight(caster);
    }

    void SearingLight(Creature* caster)
    {
        caster->CastSpell(caster, SPELL_SV_SEARING_LIGHT, true);
        LogSv("searing-light", Acore::StringFormat("pct={} players={}", kSearingLightPct(true),
            RoomPlayers(caster).size()));
    }

    // SP6: the Oath (and on heroic SP8).
    void StartOath()
    {
        if (_oath.Active())
            return;
        bool const heroic = DungeonKit::IsHeroicMap(me);
        me->InterruptNonMeleeSpells(false);
        _oath.Start(heroic);
        Talk(YELL_SPRINGVALE_OATH);
        me->CastSpell(me, SPELL_SV_UNBREAKABLE_OATH, true);
        SummonGuardsmen();
        Mechanic::SetPhase(me, PHASE_OATH);
        if (heroic)
        {
            me->CastSpell(me, SPELL_SV_WRATH_OF_GOD, false);
            Talk(YELL_SPRINGVALE_WRATH_OF_GOD, kGuardsmanRise);
        }
        LogSv("oath", Acore::StringFormat("heroic={} health_pct={:.1f} limit_ms={}", heroic ? 1 : 0, me->GetHealthPct(),
            _oath.Limit().count()));
    }

    // `.sfktest springvale crack`: one guardsman dies (the Light first).
    bool KillOneGuardsman(Unit* killer)
    {
        for (GuardsmanInfo const& g : kGuardsmen)
            if (Creature* guardsman = me->FindNearestCreature(g.entry, kAddSearchRange, true))
            {
                Unit::Kill(killer, guardsman);
                return true;
            }
        return false;
    }

    Creature* Self() const { return me; }

    // Live state for `.sfktest springvale info`.
    std::string State()
    {
        return Acore::StringFormat("Oath used={} active={} cracks={} left_ms={} pools={}", _oath.Used() ? 1 : 0,
            _oath.Active() ? 1 : 0, _oath.Cracks(), _oath.Left().count(), _pools.Live(NowMs()).size());
    }

    // SP1 / SP2: one ring on `target`, thrown by `source`. The registry's RunOut owns the others' hit; the marked
    // player's own 10% is the thrown hammer, launched so it lands as the ring ends.
    void Hammer(Creature* source, Player* target, bool ricochet)
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        Ms const warn = ricochet ? kRicochetWarn : kHammerWarn;
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        ObjectGuid const sourceGuid = source->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();
        {
            BossMechanics::MechanicRef ref = Mechanic::RunOut(me, target, kHammerYd, warn);
            ref.Damage(kHammerOthersPct(heroic)).Spell(ricochet ? SPELL_SV_RICOCHET : SPELL_SV_HAMMER).Weakened()
                .Rider(SPELL_SV_HAMMER_STUN).Tag(ricochet ? TAG_RICOCHET : TAG_HAMMER);
            ref.OnResolve([map, bossGuid, sourceGuid, targetGuid, ricochet](BossMechanics::ResolveResult const& r)
            {
                Creature* boss = map->GetCreature(bossGuid);
                auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_commander_springvale_rework*>(boss->AI())
                    : nullptr;
                if (ai)
                    ai->HammerLanded(sourceGuid, targetGuid, ricochet, r.hits.size());
            });
        }   // the ref commits here

        Ms const launch = HammerLaunchDelay(warn, source->GetExactDist2d(target));
        me->m_Events.AddEventAtOffset([this, sourceGuid, targetGuid, ricochet]()
        {
            LaunchHammer(sourceGuid, targetGuid, ricochet);
        }, launch);
        LogSv(ricochet ? "ricochet" : "hammer", Acore::StringFormat("source={} target={} warn_ms={} launch_ms={}",
            source == me ? "springvale" : "guardsman", target->GetName(), warn.count(), launch.count()));
    }

private:
    static int64 NowMs()
    {
        return static_cast<int64>(GameTime::GetGameTimeMS().count());
    }

    void Cleanup()
    {
        _timers.CancelAll();
        _oath.Reset();
        _oathPending = false;
        _pools.Clear();
        _arena.Reset();
        me->RemoveAurasDueToSpell(SPELL_SV_UNBREAKABLE_OATH);
        me->RemoveAurasDueToSpell(SPELL_SV_CRACKED_OATH);
        me->RemoveAurasDueToSpell(SPELL_SV_OATHBROKEN);
        me->RemoveAllDynObjects();
    }

    void ScheduleFight()
    {
        _timers.CancelAll();
        _timers.Schedule(kHammerFirst, [this](TaskContext ctx)
        {
            if (!me->IsInCombat() || !BossHammerAllowed(DungeonKit::IsHeroicMap(me), _oath.Active()))
            {
                ctx.Repeat(kCheckEvery);
                return;
            }
            ThrowHammer(me);
            ctx.Repeat(kHammerEvery);
        });
        _timers.Schedule(kConsecrationFirst, [this](TaskContext ctx)
        {
            if (!me->IsInCombat() || !BossConsecrationAllowed(_oath.Active()))
            {
                ctx.Repeat(kCheckEvery);
                return;
            }
            Consecrate(me->GetPosition(), "springvale");
            ctx.Repeat(kConsecrationEvery);
        });
        _timers.Schedule(kCheckEvery, [this](TaskContext ctx)
        {
            if (!me->IsInCombat() || me->HasUnitState(UNIT_STATE_CASTING)
                || !BossHolyLightAllowed(me->GetHealthPct(), _oath.Active()) || !HolyLight())
            {
                ctx.Repeat(kCheckEvery);
                return;
            }
            ctx.Repeat(kHolyLightEvery + kHolyLightCast);
        });
    }

    void AdvanceOath(uint32 diff)
    {
        if (!_oath.Active())
            return;
        OathStep const step = _oath.Advance(Ms(diff));
        if (step.prayerEmote)
        {
            Talk(EMOTE_SPRINGVALE_PRAYER_ENDS);
            LogSv("wrath-of-god-emote", Acore::StringFormat("left_ms={}", kWrathOfGodEmoteLeft.count()));
        }
        if (step.end == OathEnd::CapExpired)
        {
            EndOath(step.end);
            LogSv("oath-cap", Acore::StringFormat("cracks={} guardsmen_left={}", _oath.Cracks(), LiveGuardsmen()));
        }
        else if (step.end == OathEnd::WrathLanded)
        {
            EndOath(step.end);
            WrathOfGod();
        }
    }

    void SummonGuardsmen()
    {
        for (GuardsmanInfo const& g : kGuardsmen)
        {
            Point3 const& p = kGuardsmanRisePoints[g.risePoint];
            Position const at(p.x, p.y, p.z, DungeonKit::BearingTo({ p.x, p.y }, DungeonKit::PlaneOf(me)));
            if (!me->SummonCreature(g.entry, at, TEMPSUMMON_CORPSE_TIMED_DESPAWN, kGuardsmanCorpseMs))
                LogSv("guardsman-summon-failed", Acore::StringFormat("entry={}", g.entry));
        }
    }

    uint32 LiveGuardsmen() const
    {
        std::list<Creature*> adds;
        me->GetCreatureListWithEntryInGrid(adds, GuardsmanEntries(), kAddSearchRange);
        uint32 alive = 0;
        for (Creature* add : adds)
            if (add->IsAlive())
                ++alive;
        return alive;
    }

    void GuardsmanDied(Creature* guardsman)
    {
        bool const wasActive = _oath.Active();
        OathEnd const end = _oath.GuardsmanDied();
        LogSv("guardsman-died", Acore::StringFormat("entry={} oath_active={} cracks={}", guardsman->GetEntry(),
            wasActive ? 1 : 0, _oath.Cracks()));
        if (!wasActive)
            return;
        if (end == OathEnd::Shattered)
        {
            EndOath(end);
            me->InterruptNonMeleeSpells(false);     // Wrath of God (heroic)
            me->CastSpell(me, SPELL_SV_OATHBROKEN, true);
            LogSv("oathbroken", Acore::StringFormat("duration_ms={} at_ms={}", kOathbroken.count(),
                _oath.Elapsed().count()));
            return;
        }
        DungeonKit::AddStacks(me, SPELL_SV_CRACKED_OATH, 1, me, kGuardsmanCount);
    }

    // Any end of the Oath: the shield and its cracks go, the descriptor's phase returns.
    void EndOath(OathEnd end)
    {
        me->RemoveAurasDueToSpell(SPELL_SV_UNBREAKABLE_OATH);
        me->RemoveAurasDueToSpell(SPELL_SV_CRACKED_OATH);
        Mechanic::SetPhase(me, PHASE_FIGHT);
        LogSv("oath-end", Acore::StringFormat("how={} at_ms={}", EndName(end), _oath.Elapsed().count()));
    }

    // SP8: the 30 s cast finished.
    void WrathOfGod()
    {
        std::vector<Player*> const players = RoomPlayers(me);
        for (Player* p : players)
            me->CastSpell(p, SPELL_SV_WRATH_OF_GOD_KILL, true);
        LogSv("wrath-of-god", Acore::StringFormat("killed={} guardsmen_left={}", players.size(), LiveGuardsmen()));
    }

    void LaunchHammer(ObjectGuid sourceGuid, ObjectGuid targetGuid, bool ricochet)
    {
        if (!me->IsAlive())
            return;
        Creature* source = me->GetMap()->GetCreature(sourceGuid);
        if (!source || !source->IsAlive())
            source = me;
        Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
        if (!target || !target->IsAlive())
            return;
        source->CastSpell(target, ricochet ? SPELL_SV_RICOCHET_MARKED : SPELL_SV_HAMMER_MARKED, true);
    }

    // SP2: the ring resolved. A first Hammer whose marked player stands in a live Consecration bounces (heroic).
    void HammerLanded(ObjectGuid sourceGuid, ObjectGuid targetGuid, bool ricochet, std::size_t othersHit)
    {
        Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
        bool inPool = false;
        if (target && target->IsAlive())
            for (uint32 id : _pools.Live(NowMs()))
                if (Mechanic::ContainsPoint(me, BossMechanics::MechanicHandle{ id }, target->GetPosition()))
                {
                    inPool = true;
                    break;
                }
        LogSv(ricochet ? "ricochet-landed" : "hammer-landed", Acore::StringFormat("others_hit={} in_consecration={}",
            othersHit, inPool ? 1 : 0));
        if (!target || !Ricochets(DungeonKit::IsHeroicMap(me), ricochet, inPool))
            return;

        std::vector<Player*> const players = RoomPlayers(me);
        std::vector<PlayerSpot> spots;
        for (Player* p : players)
            spots.push_back({ p->GetGUID().GetRawValue(), DungeonKit::PlaneOf(p), p->IsAlive() });
        std::optional<std::size_t> const next = NearestOther(spots, targetGuid.GetRawValue(),
            DungeonKit::PlaneOf(target));
        if (!next)
            return;
        Creature* source = me->GetMap()->GetCreature(sourceGuid);
        if (!source || !source->IsAlive())
            source = me;
        Hammer(source, players[*next], true);
    }

    // Kill order Light, Hammer, Altar, then Springvale (SK Boss data). The DPS always; the tank too while the Oath
    // holds (he does not melee then), so on heroic every bot is on the guardsmen before Wrath of God. Interrupts:
    // the Guardsman of the Light's Holy Light first (heroic: it heals the boss or a guardsman and sears), then his.
    // Wrath of God cannot be kicked (InterruptFlags 0): listed at priority 0 so no bot tries.
    void DescribeEncounter()
    {
        BossMechanics::Descriptor d;
        for (GuardsmanInfo const& g : kGuardsmen)
        {
            d.targets.emplace_back(g.entry, g.killPriority, BossMechanics::Who::Dps);
            d.targets.emplace_back(g.entry, g.killPriority, BossMechanics::Who::Tank,
                BossMechanics::Condition::Phase(PHASE_OATH));
        }
        d.interrupts.emplace_back(NPC_SFK_GUARDSMAN_LIGHT, SPELL_SV_HOLY_LIGHT, 2, kGuardsmanHolyLightEvery);
        d.interrupts.emplace_back(NPC_SPRINGVALE, SPELL_SV_HOLY_LIGHT, 1, kHolyLightEvery);
        d.interrupts.emplace_back(NPC_SPRINGVALE, SPELL_SV_WRATH_OF_GOD, 0);
        d.phase = PHASE_FIGHT;
        Mechanic::Describe(me, std::move(d));
    }

    static DungeonKit::ArenaGuardOptions ArenaOptions()
    {
        DungeonKit::ArenaGuardOptions o;
        // A unit in combat with another live boss is left to that boss: no two guards grip it to and fro (R2 S-2).
        o.skipGrip = DungeonKit::SkipEngagedWithOtherBoss(ShadowfangKeepRework::IsSfkBossEntry);
        o.logPrefix = "sfk springvale";
        o.offArenaReason = "off-hall";
        return o;
    }

    TaskScheduler _timers;
    OathTimeline _oath;
    PoolLedger _pools;
    bool _oathPending = false;
    DungeonKit::ArenaGuard _arena{ SpringvaleArena(), ArenaOptions() };
};

// The Risen Guardsmen 300506-300508 (summoned by Springvale's Oath): a 2 s rise (not attackable, the rise look), then
// they zone in. Normal: melee only. Heroic: the Light heals, the Hammer throws, the Altar consecrates (SP9, SP1, SP3).
struct npc_sfk_risen_guardsman : public ScriptedAI
{
    explicit npc_sfk_risen_guardsman(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _timers.CancelAll();
        if (!_risen)
        {
            me->SetImmuneToAll(true);
            me->SetReactState(REACT_PASSIVE);
        }
    }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        me->CastSpell(me, SPELL_SV_GUARDSMAN_RISE, true);
        _timers.Schedule(kGuardsmanRise, [this](TaskContext)
        {
            Rise();
        });
    }

    void JustDied(Unit* /*killer*/) override
    {
        _timers.CancelAll();
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell->Id != SPELL_SV_HOLY_LIGHT)
            return;
        if (Creature* boss = FindSpringvale(me))
            if (auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_commander_springvale_rework*>(boss->AI()) : nullptr)
                ai->HolyLightLanded(me);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_SV_HOLY_LIGHT)
            LogSv("holy-light-interrupted", "caster=light");
    }

    void UpdateAI(uint32 diff) override
    {
        _timers.Update(diff);
        if (!_risen || !UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    void Rise()
    {
        if (!me->IsAlive())
            return;
        _risen = true;
        me->SetImmuneToAll(false);
        me->SetReactState(REACT_AGGRESSIVE);
        DoZoneInCombat();
        std::optional<GuardsmanInfo> const info = GuardsmanOf(me->GetEntry());
        bool const heroic = DungeonKit::IsHeroicMap(me);
        LogSv("guardsman-rise", Acore::StringFormat("entry={} heroic={}", me->GetEntry(), heroic ? 1 : 0));
        if (!info || !heroic)
            return;
        switch (info->kind)
        {
            case Guardsman::Light:
                Mechanic::NoteNextCastIn(me, SPELL_SV_HOLY_LIGHT, kGuardsmanHolyLightFirst);
                _timers.Schedule(kGuardsmanHolyLightFirst, [this](TaskContext ctx)
                {
                    if (me->HasUnitState(UNIT_STATE_CASTING) || !HolyLight())
                    {
                        ctx.Repeat(kBusyRetry);
                        return;
                    }
                    Mechanic::NoteNextCastIn(me, SPELL_SV_HOLY_LIGHT, kGuardsmanHolyLightEvery);
                    ctx.Repeat(kGuardsmanHolyLightEvery + kHolyLightCast);
                });
                break;
            case Guardsman::Hammer:
                _timers.Schedule(kGuardsmanHammerFirst, [this](TaskContext ctx)
                {
                    boss_commander_springvale_rework* boss = Boss();
                    if (!boss || !boss->ThrowHammer(me))
                    {
                        ctx.Repeat(kBusyRetry);
                        return;
                    }
                    ctx.Repeat(kGuardsmanHammerEvery);
                });
                break;
            case Guardsman::Altar:
                _timers.Schedule(kAltarConsecrationFirst, [this](TaskContext ctx)
                {
                    if (boss_commander_springvale_rework* boss = Boss())
                        boss->Consecrate(me->GetPosition(), "altar");
                    ctx.Repeat(kAltarConsecrationEvery);
                });
                break;
        }
    }

    boss_commander_springvale_rework* Boss()
    {
        Creature* boss = FindSpringvale(me);
        return boss && boss->IsAIEnabled ? dynamic_cast<boss_commander_springvale_rework*>(boss->AI()) : nullptr;
    }

    // SP9: the most wounded of Springvale and the guardsmen (SpringvaleLogic.h PickHolyLightTarget).
    bool HolyLight()
    {
        std::vector<Creature*> units;
        if (Creature* boss = FindSpringvale(me))
            units.push_back(boss);
        std::list<Creature*> adds;
        me->GetCreatureListWithEntryInGrid(adds, GuardsmanEntries(), kAddSearchRange);
        units.insert(units.end(), adds.begin(), adds.end());
        std::vector<HealCandidate> candidates;
        for (Creature* u : units)
            candidates.push_back({ u->GetGUID().GetRawValue(), u->GetHealthPct(), u->IsAlive() });
        std::optional<std::size_t> const pick = PickHolyLightTarget(candidates);
        if (!pick || me->CastSpell(units[*pick], SPELL_SV_HOLY_LIGHT, false) != SPELL_CAST_OK)
            return false;
        LogSv("holy-light", Acore::StringFormat("caster=light target={} health_pct={:.1f}", units[*pick]->GetEntry(),
            units[*pick]->GetHealthPct()));
        return true;
    }

    TaskScheduler _timers;
    bool _risen = false;
};

// 205966 / 205969 the marked player's own Hammer (10%), cast at one target: a percent of the reference row
// (DungeonKit::RefFlat; IGNORE_CASTER_MODIFIERS, so the number is exact before mitigation).
class spell_sfk_springvale_hammer_marked : public SpellScript
{
    PrepareSpellScript(spell_sfk_springvale_hammer_marked);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlat(caster,
            kHammerMarkedPct(DungeonKit::IsHeroicMap(caster)))));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_sfk_springvale_hammer_marked::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// 205974 Searing Light (heroic): players only, 15% of the reference row each.
class spell_sfk_springvale_searing_light : public SpellScript
{
    PrepareSpellScript(spell_sfk_springvale_searing_light);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if([](WorldObject const* target) { return !target->IsPlayer(); });
    }

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlat(caster,
            kSearingLightPct(DungeonKit::IsHeroicMap(caster)))));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sfk_springvale_searing_light::FilterTargets,
            EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY);
        OnEffectLaunchTarget += SpellEffectFn(spell_sfk_springvale_searing_light::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    // `.sfktest springvale <mechanic>`: the GM (`.gm off` to be hit) is the target; Springvale is the selected one or
    // the nearest within 200 yd.
    boss_commander_springvale_rework* FindAI(ChatHandler* handler)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_SPRINGVALE);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_commander_springvale_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("Commander Springvale does not run boss_commander_springvale_rework.");
        return ai;
    }

    Creature* Me(boss_commander_springvale_rework* ai)
    {
        return ai->Self();
    }

    bool HandleInfo(ChatHandler* handler)
    {
        if (!SfkTest::ShowBossInfo(handler, NPC_SPRINGVALE, BOSS_SPRINGVALE))
            return false;
        if (boss_commander_springvale_rework* ai = FindAI(handler))
            handler->SendSysMessage(ai->State());
        return true;
    }

    bool HandleHammer(ChatHandler* handler)
    {
        boss_commander_springvale_rework* ai = FindAI(handler);
        if (!ai)
            return false;
        ai->ThrowHammer(Me(ai), handler->GetPlayer());
        handler->SendSysMessage("Hammer of Judgement on you: 8 yd ring, lands in 3 s (heroic: bounces once if you "
            "stand in a Consecration).");
        return true;
    }

    bool HandleRicochet(ChatHandler* handler)
    {
        boss_commander_springvale_rework* ai = FindAI(handler);
        if (!ai)
            return false;
        ai->Hammer(Me(ai), handler->GetPlayer(), true);
        handler->SendSysMessage("Ricochet on you: 8 yd ring, lands in 2 s, never bounces.");
        return true;
    }

    bool HandleConsecration(ChatHandler* handler)
    {
        boss_commander_springvale_rework* ai = FindAI(handler);
        if (!ai)
            return false;
        ai->Consecrate(Me(ai)->GetPosition(), "springvale");
        return true;
    }

    bool HandlePool(ChatHandler* handler)
    {
        boss_commander_springvale_rework* ai = FindAI(handler);
        if (!ai)
            return false;
        ai->Consecrate(handler->GetPlayer()->GetPosition(), "test");
        handler->SendSysMessage("Consecration at your feet (normal 10 s, heroic 40 s).");
        return true;
    }

    bool HandleHolyLight(ChatHandler* handler)
    {
        boss_commander_springvale_rework* ai = FindAI(handler);
        if (!ai)
            return false;
        if (!ai->HolyLight())
            handler->SendErrorMessage("Holy Light did not cast.");
        return true;
    }

    bool HandleSearing(ChatHandler* handler)
    {
        boss_commander_springvale_rework* ai = FindAI(handler);
        if (!ai)
            return false;
        ai->SearingLight(Me(ai));
        return true;
    }

    bool HandleOath(ChatHandler* handler)
    {
        boss_commander_springvale_rework* ai = FindAI(handler);
        if (!ai)
            return false;
        ai->StartOath();
        handler->SendSysMessage("Unbreakable Oath: the guardsmen rise (heroic: Wrath of God, 30 s).");
        return true;
    }

    bool HandleCrack(ChatHandler* handler)
    {
        boss_commander_springvale_rework* ai = FindAI(handler);
        if (!ai)
            return false;
        if (!ai->KillOneGuardsman(handler->GetPlayer()))
            handler->SendErrorMessage("No guardsman alive.");
        return true;
    }

    ChatCommandTable const& SpringvaleTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",         HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "hammer",       HandleHammer,       SEC_GAMEMASTER, Console::No },
            { "ricochet",     HandleRicochet,     SEC_GAMEMASTER, Console::No },
            { "consecration", HandleConsecration, SEC_GAMEMASTER, Console::No },
            { "pool",         HandlePool,         SEC_GAMEMASTER, Console::No },
            { "holylight",    HandleHolyLight,    SEC_GAMEMASTER, Console::No },
            { "searing",      HandleSearing,      SEC_GAMEMASTER, Console::No },
            { "oath",         HandleOath,         SEC_GAMEMASTER, Console::No },
            { "crack",        HandleCrack,        SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_commander_springvale_rework()
{
    RegisterDungeonReworkCreatureAI(boss_commander_springvale_rework, ShadowfangKeepRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sfk_risen_guardsman, ShadowfangKeepRework::kInstanceScriptName);
    RegisterSpellScript(spell_sfk_springvale_hammer_marked);
    RegisterSpellScript(spell_sfk_springvale_searing_light);
    SfkTest::RegisterBoss("springvale", SpringvaleTestCommands());
}
