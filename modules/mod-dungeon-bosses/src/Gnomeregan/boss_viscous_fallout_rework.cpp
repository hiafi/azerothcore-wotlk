/*
 * mod-dungeon-bosses, Gnomeregan D2: Viscous Fallout (7079), normal and heroic. Build spec: SP 748-801 (VF1-VF9),
 * design SP 585-747, rulings 14-20; handoff section 3.5 row D2 and rules 1-38, sections 3.6, 3.8 (area C), 3.9 rows
 * 3-4, section 7 #19 A, #36-#38 A, section 10 (STAGE-S0 Q8: he faces 3.95 at area C; Q10: the one halving rule, stated
 * in ViscousFalloutLogic.h). Replaces SmartAI 7079 (dropped by rev_skeleton_gnomeregan.sql: Toxic Volley 21687,
 * Radiation Cloud 10341 once, Corrosive Ooze 9459 on a random player). His addon's Corrosive Ooze proc 9460 is dropped,
 * his Frost immunity 7940 kept (rev_viscous_fallout_gnomeregan.sql). Bound by apps/dbc-tools source/npcs/gnomeregan/
 * viscous_fallout.py; numbers in ViscousFalloutLogic.h, health in GnomereganRework.h Health.
 *
 *   VF1 Irradiated   the dose, through the DoseField machine (ViscousFalloutMachine.cpp): 3% damage and healing done a
 *                    stack; normal drains 1 per 3 s out of every armed pool; heroic never drains.
 *   VF2 Sickness     normal, at 10: 40% plus Weakened, 20% to allies within 8 yd, a 2 s stun, dose to 0; emote line 1.
 *   VF3 Toxic Volley every 15 s (heroic 12 s): every player in the fight within 45 yd, 10% (heroic +3% per dose), 2
 *                    dose (Saturated +2), a Poison rider (dispel reward); a 4 yd pool under each, armed after 1.5 s,
 *                    20 s (heroic 30 s).
 *   VF4 Slough       with each Volley: a 7 yd pool under him, a 2 s swell (its warning), for the fight; emote line 0;
 *                    heroic grows 1 yd per 10 s, no cap.
 *   Pools            8% a second and 1 dose a second to anyone in any armed pool (once however many overlap). The
 *                    script judges them (PoolSet); the bots see telegraph-only lasting rings (tags 20, 22, 24) and the
 *                    tank drags him out of them (BM's drag-out, L47); each wears the nature disc (pool stalker 301130).
 *   VF5 Saturated    judged every 0.5 s on armed pools: +50% damage (his melee by the aura, his script hits by
 *                    Tune::kSaturatedScalesHits), +2 dose on the Volley; heroic +1 dose to everyone per 2 s.
 *   VF6 Ooze         every 10 s from 5 s: a glob lobbed at a random player (heroic two), tank included; a 5 yd circle
 *                    where they stood, 2 s; 40% / 60% plus Weakened and 3 / 5 dose; a 5 yd pool for 30 s.
 *   VF7 Leaking      heroic, at 10 dose and up: a 4 yd pool at the carrier's feet every 10 s, the fight; line 3 once.
 *   VF8 Meltdown     heroic, at 20 dose and up: 5% a second to the carrier and to everyone within 6 yd (a lasting 6 yd
 *                    registry Spread on the carrier hits the others; the carrier's own tick is the script's); line 4.
 *   VF9 Half-Life    heroic, every 30 s from 30 s: a 3 s bar (not interruptible), 10 yd round him; everyone inside at
 *                    its end (the bar's own completion, OnSpellCast: a slowed cast resolves when it ends) loses half
 *                    the dose (rounded up), he heals 0.5% per dose shed; line 2. Bots: a Stack for 8 dose and up, a
 *                    keep-out for the rest.
 *   Arena            CaveArena() with LeashOptions; every shape `.Within(FalloutFloorBounds())`.
 *
 * Every firing logs one INFO line "gnomer-build fallout <mechanic> ..."; `.dbtest gnomer fallout <subcommand>` fires
 * one. Mirrored stock code: none.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GnomereganKit.h"
#include "GnomereganRework.h"
#include "GnomereganTestCommand.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MechanicRegistry.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include "Util.h"
#include "ViscousFalloutLogic.h"
#include "ViscousFalloutMachine.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace GnomereganRework;
using namespace GnomerFallout;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossKey = "fallout";
    uint8 constexpr kSchoolNature = 3;      // SPELL_SCHOOL_NATURE (rule 2: per-stack damage is Nature, never Physical)

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    bool Alive(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }
}

// Viscous Fallout 7079
struct boss_viscous_fallout_rework : public BossAI
{
    explicit boss_viscous_fallout_rework(Creature* creature)
        : BossAI(creature, BOSS_VISCOUS_FALLOUT), _arena(CaveArena(), LeashOptions(kBossKey))
    {
    }

    void Reset() override
    {
        Cleanup("reset");
        _Reset();
        // His stock Frost immunity (an addon aura): kept through every reset (the stock -232 set went to 1972).
        if (!me->HasAura(SPELL_FROST_IMMUNITY))
            me->AddAura(SPELL_FROST_IMMUNITY, me);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup("pull");        // a `.dbtest gnomer fallout` mechanic out of combat may have left something behind
        StripDose();            // a stale dose from an earlier pull (or a saved aura) never carries in
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        _now = 0;
        _dose = GnomereganMachines::MakeDoseField({ me, kBossKey, _heroic }, DoseSpecFor(_heroic));
        _beat.Start(_now, Tune::kBeatFirstMs(_heroic), Tune::kBeatEveryMs(_heroic));
        _ooze.Start(_now, Tune::kOozeFirstMs, Tune::kOozeEveryMs);
        if (_heroic)
            _halfLife.Start(_now, Tune::kHalfLifeFirstMs, Tune::kHalfLifeEveryMs);

        OnBossPull(me, kBossKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_VISCOUS_FALLOUT;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Log("engage", Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) players={}", _heroic ? 1 : 0,
            me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), FightPlayers().size()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Log("evade", Acore::StringFormat("reason={} pools={}", uint32(why), _pools.Size()));
        Cleanup("evade");
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        Log("death", Acore::StringFormat("volleys={} oozes={} halflifes={} sickness={} pools={}", _counts.volleys,
            _counts.oozes, _counts.halfLifes, _counts.sickness, _pools.Size()));
        Cleanup("death");
    }

    // Half-Life is not interruptible (InterruptFlags 0) and he is stun immune: only his death, an evade or a script's
    // InterruptNonMeleeSpells end it early (rule 15): the bar's shapes go with it.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_VF_HALF_LIFE && _halfLifeCasting)
            AbortHalfLife("bar-failed");
    }

    // VF9: the bar completed (LESSONS A.2 #5: the bar's own end, never a fixed timer; a slowed cast lands late).
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_VF_HALF_LIFE && _halfLifeCasting)
            ResolveHalfLife();
    }

    void UpdateAI(uint32 diff) override
    {
        GnomereganRework::NoAssist(me);     // rule 29, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        _now += diff;
        FlushQueued();
        UpdatePools(diff);
        UpdateSaturated(diff);
        if (_dose)
            _dose->Update(diff);
        UpdateCarriers(diff);
        UpdateLobs();
        if (!_engaged || !me->IsAlive())
            return;

        // The lost-bar fallback: neither callback came, the bar is gone and its time is up.
        if (_halfLifeCasting && _now >= _halfLifeEndsAt && !me->FindCurrentSpellBySpellId(SPELL_VF_HALF_LIFE))
            ResolveHalfLife();
        if (_beat.Due(_now))
        {
            VolleyBeat("due");
            _beat.Fired(_now);
        }
        if (_ooze.Due(_now))
        {
            Ooze("due");
            _ooze.Fired(_now);
        }
        if (_halfLife.Due(_now) && !_halfLifeCasting)
            StartHalfLife("due");

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- `.dbtest gnomer fallout` ----------------------------------------------------------------------------------

    bool Engaged() const { return _engaged && _dose; }
    bool Heroic() const { return _heroic; }

    void TestBeat() { VolleyBeat("gm"); }
    void TestOoze() { Ooze("gm"); }
    bool TestHalfLife() { return _heroic && !_halfLifeCasting && StartHalfLife("gm"); }

    uint32 TestDose(Player* player, uint32 dose)
    {
        _dose->Set(player, dose, "gm");
        return _dose->Dose(player->GetGUID());
    }

    void TestSickness(Player* player) { Sickness(player); }
    void TestLeak(Player* player) { AddPool(PoolKind::Leak, player->GetPosition(), "gm"); }
    void TestPool(PoolKind kind, Position const& at) { AddPool(kind, at, "gm"); }

    std::string TestState() const
    {
        std::string carriers;
        if (_dose)
            for (auto const& [guid, dose] : _dose->Carriers())
                carriers += Acore::StringFormat(" {}:{}", guid.GetCounter(), dose);
        return Acore::StringFormat("engaged={} heroic={} now={} beat_in={} ooze_in={} halflife_in={} casting={} "
            "saturated={} pools={} (volley {} slough {} ooze {} leak {}, area {:.0f} sq yd) meltdowns={} "
            "counts: volleys={} oozes={} halflifes={} sickness={} carriers:{}", _engaged ? 1 : 0, _heroic ? 1 : 0,
            _now, _beat.InMs(_now), _ooze.InMs(_now), _halfLife.InMs(_now), _halfLifeCasting ? 1 : 0,
            _saturated ? 1 : 0, _pools.Size(), _pools.Count(PoolKind::Volley), _pools.Count(PoolKind::Slough),
            _pools.Count(PoolKind::Ooze), _pools.Count(PoolKind::Leak), _pools.AreaSum(), _meltdown.size(),
            _counts.volleys, _counts.oozes, _counts.halfLifes, _counts.sickness, carriers.empty() ? " -" : carriers);
    }

    std::string TestMachine() const { return _dose ? _dose->Describe() : "no dose field (not engaged)"; }

private:
    struct PoolLook
    {
        MechanicHandle zone;
        MechanicHandle oldZone;         // a growing pool's previous ring, until the grown one is live
        uint64 growLiveAt = 0;
        float growTo = 0.f;
        ObjectGuid disc;
    };

    struct QueuedPool
    {
        PoolKind kind = PoolKind::Ooze;
        Position at;
    };

    struct Lob
    {
        Position at;
        uint64 castAt = 0;
    };

    struct Counts
    {
        uint32 volleys = 0;
        uint32 oozes = 0;
        uint32 halfLifes = 0;
        uint32 sickness = 0;
    };

    // ---- the machine ------------------------------------------------------------------------------------------------

    GnomereganMachines::DoseSpec DoseSpecFor(bool heroic)
    {
        GnomereganMachines::DoseSpec spec;
        spec.auraSpellId = SPELL_VF_IRRADIATED;
        // The machine is this AI's member and is cleared with it, so its callbacks may hold `this`.
        spec.drainEveryMs = Tune::kDrainEveryMs(heroic);
        spec.drains = [this](Player* player) { return !InPool(player); };
        spec.capAt = Tune::kSicknessAt(heroic);
        spec.onCap = [this](Player* player) { Sickness(player); };
        spec.leakAt = Tune::kLeakAt(heroic);
        spec.leakEveryMs = Tune::kLeakEveryMs;
        spec.onLeak = [this](Player* /*player*/, Position const& at) { AddPool(PoolKind::Leak, at, "leaking"); };
        spec.meltdownAt = Tune::kMeltdownAt(heroic);
        spec.onMeltdown = [this](Player* player, bool on) { OnMeltdown(player, on); };
        if (heroic)
        {
            spec.leakEmoteGroup = EMOTE_LEAKING;
            spec.meltdownEmoteGroup = EMOTE_MELTDOWN;
        }
        return spec;
    }

    void AddDose(Player* player, int32 doses, char const* why)
    {
        if (_dose && Alive(player))
            _dose->Add(player, doses, why);
    }

    // ---- the pools --------------------------------------------------------------------------------------------------

    bool InPool(Unit const* unit) const
    {
        return unit && _pools.Contains(_now, DungeonKit::PlaneOf(unit), unit->GetPositionZ());
    }

    uint32 AddPool(PoolKind kind, Position const& at, char const* why)
    {
        float radius = Tune::kVolleyPoolYd;
        uint32 armMs = Tune::kVolleyPoolArmMs;
        uint32 lifeMs = Tune::kVolleyPoolLifeMs(_heroic);
        uint32 growMs = 0;
        switch (kind)
        {
            case PoolKind::Volley:
                break;
            case PoolKind::Slough:
                radius = Tune::kSloughYd;
                armMs = Tune::kSloughSwellMs;
                lifeMs = 0;
                growMs = _heroic ? Tune::kSloughGrowEveryMsH : 0;
                break;
            case PoolKind::Ooze:
                radius = Tune::kOozePoolYd;
                armMs = Tune::kOozePoolArmMs;
                lifeMs = Tune::kOozePoolLifeMs;
                break;
            case PoolKind::Leak:
                radius = Tune::kLeakPoolYd;
                armMs = Tune::kLeakPoolArmMs;
                lifeMs = 0;
                break;
        }
        Vec2 const center{ at.GetPositionX(), at.GetPositionY() };
        uint32 const id = _pools.Add(_now, kind, center, at.GetPositionZ(), radius, armMs, lifeMs, growMs);
        PoolLook look;
        uint32 const lastsMs = lifeMs ? lifeMs : Tune::kWholeFightMs;
        look.zone = RegisterRing(kind, at, radius, armMs, lastsMs, false);
        look.disc = SpawnDisc(at, radius, lifeMs ? armMs + lifeMs : Tune::kWholeFightMs);
        _looks[id] = look;
        Log("pool", Acore::StringFormat("kind={} id={} at=({:.1f}, {:.1f}, {:.1f}) r={:.0f} arm={} life={} grows={} "
            "pools={} why={}", kPoolKindNames[uint8(kind)], id, at.GetPositionX(), at.GetPositionY(),
            at.GetPositionZ(), radius, armMs, lifeMs, growMs ? 1 : 0, _pools.Size(), why));
        return id;
    }

    // The bots' telegraph-only lasting ring (it draws and steers; the script judges): its warning is the arming.
    MechanicHandle RegisterRing(PoolKind kind, Position const& at, float radius, uint32 warnMs, uint32 lastsMs,
        bool outlineOnly)
    {
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(at, radius), Ms(warnMs));
        if (!ref.IsValid())
            return {};
        ref.Persistent(Ms(std::max<uint32>(lastsMs, 1)), Ms(0)).Within(FalloutFloorBounds())
            .ZTolerance(Tune::kZToleranceYd).Tag(PoolTag(kind));
        if (outlineOnly)
            ref.NoFillTimer();
        return ref.Handle();
    }

    // The nature disc at the pool (a map summon: no summon list holds it, its own life as a safety; Cleanup despawns).
    ObjectGuid SpawnDisc(Position const& at, float radius, uint32 lifeMs)
    {
        TempSummon* disc = me->GetMap()->SummonCreature(NPC_POOL_STALKER, at, nullptr, lifeMs + 1000);
        if (!disc)
            return ObjectGuid::Empty;
        disc->SetReactState(REACT_PASSIVE);
        disc->SetDisplayId(kDisplayPoolDisc, DiscScale(radius));     // one call: a display change resets the scale
        return disc->GetGUID();
    }

    void DropLook(PoolLook const& look)
    {
        if (look.zone)
            Mechanic::Cancel(me, look.zone);
        if (look.oldZone)
            Mechanic::Cancel(me, look.oldZone);
        if (!look.disc.IsEmpty())
            if (Creature* disc = me->GetMap()->GetCreature(look.disc))
                disc->DespawnOrUnsummon();
    }

    void UpdatePools(uint32 diff)
    {
        for (uint32 const id : _pools.Prune(_now))
        {
            auto it = _looks.find(id);
            if (it != _looks.end())
            {
                DropLook(it->second);
                _looks.erase(it);
            }
        }
        // VF4 heroic: each growing Slough registers its grown ring (outline until live); the old one ticks till then.
        for (uint32 const id : _pools.GrowthDue(_now))
        {
            Pool const* pool = _pools.Find(id);
            auto it = _looks.find(id);
            if (!pool || it == _looks.end())
                continue;
            PoolLook& look = it->second;
            float const to = pool->radius + Tune::kSloughGrowYdH;
            Position const at(pool->center.x, pool->center.y, pool->z);
            MechanicHandle const grown = RegisterRing(pool->kind, at, to, Tune::kSloughGrowWarnMs,
                Tune::kWholeFightMs, true);
            _pools.Grew(id, _now, Tune::kSloughGrowEveryMsH);
            if (!grown)
                continue;
            if (look.oldZone)
                Mechanic::Cancel(me, look.oldZone);
            look.oldZone = look.zone;
            look.zone = grown;
            look.growTo = to;
            look.growLiveAt = _now + Tune::kSloughGrowWarnMs;
            Log("slough-grow", Acore::StringFormat("id={} r={:.0f} live_in={}", id, to, Tune::kSloughGrowWarnMs));
        }
        for (auto& [id, look] : _looks)
        {
            if (!look.growLiveAt || _now < look.growLiveAt)
                continue;
            _pools.SetRadius(id, look.growTo);
            if (look.oldZone)
                Mechanic::Cancel(me, look.oldZone);
            look.oldZone = MechanicHandle();
            look.growLiveAt = 0;
            if (Creature* disc = look.disc.IsEmpty() ? nullptr : me->GetMap()->GetCreature(look.disc))
                disc->SetDisplayId(kDisplayPoolDisc, DiscScale(look.growTo));
        }

        _poolTickMs += diff;
        if (_poolTickMs < Tune::kPoolTickMs)
            return;
        _poolTickMs %= Tune::kPoolTickMs;
        GuidSet inside;
        std::vector<ObjectGuid> dosed;
        for (Player* player : FightPlayers())
            if (InPool(player))
            {
                inside.insert(player->GetGUID());
                dosed.push_back(player->GetGUID());
            }
        if (inside.empty())
            return;
        DungeonKit::RegistryHitSpec spec;
        spec.pct = Tune::kPoolPct;
        spec.tankPct = Tune::kPoolPct;          // rule 17: the tank in a pool takes the tank row
        spec.school = kSchoolNature;
        spec.spellId = SPELL_VF_FALLOUT_POOL;
        spec.weakened = false;                  // a lingering patch (SP VF3)
        spec.tag = TAG_VF_POOL_TICK;
        Track(DungeonKit::RegistryHit(me, inside, spec));
        for (ObjectGuid const& guid : dosed)
            AddDose(ObjectAccessor::GetPlayer(*me, guid), Tune::kPoolDose, "pool");
    }

    // Pools a registry callback asked for (the glob's), made here (rule 11: never inside the registry's resolve).
    void FlushQueued()
    {
        if (_queued.empty())
            return;
        std::vector<QueuedPool> queued;
        queued.swap(_queued);
        for (QueuedPool const& q : queued)
            AddPool(q.kind, q.at, "glob");
    }

    // ---- VF5 Saturated ----------------------------------------------------------------------------------------------

    void UpdateSaturated(uint32 diff)
    {
        _saturatedPollMs += diff;
        if (_saturatedPollMs >= Tune::kSaturatedPollMs)
        {
            _saturatedPollMs = 0;
            bool const in = InPool(me);
            if (in != _saturated)
            {
                _saturated = in;
                if (in)
                    me->AddAura(SPELL_VF_SATURATED, me);
                else
                    me->RemoveAurasDueToSpell(SPELL_VF_SATURATED);
                _saturatedPulseMs = 0;
                Log(in ? "saturated-on" : "saturated-off", Acore::StringFormat("at=({:.1f}, {:.1f}) victim={}",
                    me->GetPositionX(), me->GetPositionY(), me->GetVictim() ? me->GetVictim()->GetName() : "-"));
            }
        }
        if (!_heroic || !_saturated)
            return;
        _saturatedPulseMs += diff;
        if (_saturatedPulseMs < Tune::kSaturatedPulseEveryMsH)
            return;
        _saturatedPulseMs -= Tune::kSaturatedPulseEveryMsH;
        for (Player* player : FightPlayers())
            AddDose(player, Tune::kSaturatedPulseDoseH, "saturated");
    }

    // ---- the carriers: the glow, the geiger click, Meltdown -------------------------------------------------------

    void UpdateCarriers(uint32 diff)
    {
        if (!_dose)
            return;
        _carrierPollMs += diff;
        if (_carrierPollMs < Tune::kPollMs)
            return;
        uint32 const elapsed = _carrierPollMs;
        _carrierPollMs = 0;
        _carrierSecondMs += elapsed;

        // The geiger click, faster with the dose, to the carrier only.
        std::map<uint64, uint32> doses;
        for (auto const& [guid, dose] : _dose->Carriers())
            doses[guid.GetRawValue()] = dose;
        for (auto it = _geiger.begin(); it != _geiger.end();)
            it = doses.count(it->first) ? std::next(it) : _geiger.erase(it);
        for (auto const& [raw, dose] : doses)
        {
            uint32& clock = _geiger[raw];
            clock += elapsed;
            uint32 const every = GeigerEveryMs(dose);
            if (!every || clock < every)
                continue;
            clock = 0;
            if (Player* player = ObjectAccessor::GetPlayer(*me, ObjectGuid(raw)))
                if (Alive(player))
                    player->PlayDirectSound(kSoundGeiger, player);
        }

        if (_carrierSecondMs < Tune::kReassertMs)
            return;
        _carrierSecondMs = 0;

        // The bright glow at kGlowAt and up.
        uint32 const glowAt = Tune::kGlowAt(_heroic);
        for (auto it = _glowing.begin(); it != _glowing.end();)
        {
            auto const d = doses.find(it->GetRawValue());
            if (d != doses.end() && d->second >= glowAt)
            {
                ++it;
                continue;
            }
            if (Player* player = ObjectAccessor::GetPlayer(*me, *it))
                player->RemoveAurasDueToSpell(SPELL_VF_DOSE_GLOW, me->GetGUID());
            it = _glowing.erase(it);
        }
        for (auto const& [raw, dose] : doses)
            if (dose >= glowAt)
                if (Player* player = ObjectAccessor::GetPlayer(*me, ObjectGuid(raw)))
                    if (Alive(player) && !player->HasAura(SPELL_VF_DOSE_GLOW, me->GetGUID()))
                    {
                        me->AddAura(SPELL_VF_DOSE_GLOW, player);
                        _glowing.insert(player->GetGUID());
                    }

        // VF8: every carrier's own tick (the registry Spread hits the others), and the spreads kept in step with the
        // ledger (a carrier who left the map gets no callback; one below the line loses the spread here too).
        if (!_heroic || _meltdown.empty())
            return;
        uint32 const at = Tune::kMeltdownAt(_heroic);
        GuidSet carriers;
        for (auto it = _meltdown.begin(); it != _meltdown.end();)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, ObjectGuid(it->first));
            auto const d = doses.find(it->first);
            if (!Alive(player) || d == doses.end() || d->second < at)
            {
                EndMeltdown(it->first, it->second);
                it = _meltdown.erase(it);
                continue;
            }
            carriers.insert(player->GetGUID());
            ++it;
        }
        if (carriers.empty())
            return;
        DungeonKit::RegistryHitSpec spec;
        spec.pct = Tune::kMeltdownPct;
        spec.tankPct = Tune::kMeltdownPct;
        spec.school = kSchoolNature;
        spec.spellId = SPELL_VF_MELTDOWN;
        spec.weakened = false;
        spec.tag = TAG_VF_MELTDOWN;
        Track(DungeonKit::RegistryHit(me, carriers, spec));
    }

    void OnMeltdown(Player* player, bool on)
    {
        if (!player)
            return;
        uint64 const raw = player->GetGUID().GetRawValue();
        auto it = _meltdown.find(raw);
        if (!on)
        {
            if (it != _meltdown.end())
            {
                EndMeltdown(raw, it->second);
                _meltdown.erase(it);
            }
            return;
        }
        if (it != _meltdown.end() || !Alive(player))
            return;
        // A lasting 6 yd Spread on the carrier: the others inside take 5% a tick (carriers stack on each other); the
        // bots read it as a RunOut keyed to their own dose (SP VF8 bots).
        MechanicRef ref = Mechanic::Spread(me, Tune::kMeltdownYd, Ms(Tune::kMeltdownWarnMs));
        if (!ref.IsValid())
            return;
        ref.Targets(GuidSet{ player->GetGUID() }).Persistent(Ms(Tune::kWholeFightMs), Ms(Tune::kMeltdownTickMs))
            .Damage(Tune::kMeltdownPct).TankDamage(Tune::kMeltdownPct).School(kSchoolNature)
            .Spell(SPELL_VF_MELTDOWN).Within(FalloutFloorBounds()).Tag(TAG_VF_MELTDOWN);
        _meltdown[raw] = ref.Handle();
        me->AddAura(SPELL_VF_MELTDOWN_AURA, player);
        Log("meltdown", Acore::StringFormat("player={} dose={} carriers={}", player->GetName(),
            _dose ? _dose->Dose(player->GetGUID()) : 0, _meltdown.size()));
    }

    void EndMeltdown(uint64 raw, MechanicHandle handle)
    {
        if (handle)
            Mechanic::Cancel(me, handle);
        if (Player* player = ObjectAccessor::GetPlayer(*me, ObjectGuid(raw)))
            player->RemoveAurasDueToSpell(SPELL_VF_MELTDOWN_AURA, me->GetGUID());
    }

    // ---- VF2 Radiation Sickness (normal, the machine's cap) -------------------------------------------------------

    void Sickness(Player* player)
    {
        if (!Alive(player))
            return;
        ++_counts.sickness;
        Talk(EMOTE_SICKNESS, player);
        DungeonKit::RegistryHitSpec hit;
        hit.pct = Tune::kSicknessPct;
        hit.tankPct = Tune::kSicknessPct;
        hit.school = kSchoolNature;
        hit.spellId = SPELL_VF_SICKNESS;
        hit.weakened = true;
        hit.rider = SPELL_VF_SICKNESS_STUN;     // the 2 s stun, the vomit
        hit.tag = TAG_VF_SICKNESS;
        Track(DungeonKit::RegistryHit(me, GuidSet{ player->GetGUID() }, hit));

        GuidSet allies;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* other = ref.GetSource();
            if (other != player && Alive(other) && other->GetExactDist2d(player) <= Tune::kSicknessPulseYd
                && std::fabs(other->GetPositionZ() - player->GetPositionZ()) <= Tune::kZToleranceYd)
                allies.insert(other->GetGUID());
        }
        if (!allies.empty())
        {
            DungeonKit::RegistryHitSpec pulse;
            pulse.pct = Tune::kSicknessPulsePct;
            pulse.tankPct = Tune::kSicknessPulsePct;
            pulse.school = kSchoolNature;
            pulse.spellId = SPELL_VF_SICKNESS_PULSE;
            pulse.weakened = false;
            pulse.tag = TAG_VF_SICKNESS;
            Track(DungeonKit::RegistryHit(me, allies, pulse));
        }
        Log("sickness", Acore::StringFormat("player={} tank={} allies={}", player->GetName(),
            me->GetVictim() == player ? 1 : 0, allies.size()));
    }

    // ---- VF3 Toxic Volley and VF4 Slough (one beat, ruling 17) ------------------------------------------------------

    void VolleyBeat(char const* why)
    {
        ++_counts.volleys;
        bool const saturated = _saturated;
        std::vector<Player*> const players = FightPlayers(Tune::kVolleyRangeYd);
        std::map<uint32, GuidSet> byPct;       // hundredths of a percent -> the players hit for it
        for (Player* player : players)
        {
            uint32 const dose = _dose ? _dose->Dose(player->GetGUID()) : 0;
            byPct[uint32(std::lround(VolleyPct(_heroic, dose, saturated) * 100.f))].insert(player->GetGUID());
        }
        for (auto const& [hundredths, guids] : byPct)
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = float(hundredths) / 100.f;
            spec.tankPct = spec.pct;
            spec.school = kSchoolNature;
            spec.spellId = SPELL_VF_TOXIC_VOLLEY;
            spec.weakened = false;
            spec.rider = SPELL_VF_VOLLEY_POISON;    // the Poison: a dispel reward (kick and dispel table)
            spec.tag = TAG_VF_VOLLEY;
            Track(DungeonKit::RegistryHit(me, guids, spec));
        }
        me->CastSpell(me, SPELL_VF_VOLLEY_LOOK, true);
        int32 const doses = VolleyDose(saturated);
        for (Player* player : players)
        {
            AddDose(player, doses, "volley");
            AddPool(PoolKind::Volley, player->GetPosition(), "volley");
        }

        Talk(EMOTE_SLOUGH);
        me->CastSpell(me, SPELL_VF_SLOUGH, true);
        AddPool(PoolKind::Slough, me->GetPosition(), "slough");
        Log("volley", Acore::StringFormat("players={} saturated={} dose={} pcts={} why={}", players.size(),
            saturated ? 1 : 0, doses, byPct.size(), why));
    }

    // ---- VF6 Corrosive Ooze ---------------------------------------------------------------------------------------

    void Ooze(char const* why)
    {
        ++_counts.oozes;
        std::vector<Player*> pool = FightPlayers();
        uint32 const count = std::min<uint32>(Tune::kOozeCount(_heroic), uint32(pool.size()));
        float const pct = OozePct(_heroic, _saturated);
        int32 const doses = Tune::kOozeDose(_heroic);
        std::string names;
        for (uint32 i = 0; i < count; ++i)
        {
            // A random player, tank included (SP VF6); two different players on heroic.
            uint32 const pick = urand(0, uint32(pool.size()) - 1);
            Player* target = pool[pick];
            pool.erase(pool.begin() + pick);
            Position const at = target->GetPosition();
            MechanicRef ref = Mechanic::Circle(me, at, Tune::kOozeYd, Ms(Tune::kOozeWarnMs));
            if (!ref.IsValid())
                continue;
            ref.Damage(pct).TankDamage(pct).School(kSchoolNature).Spell(SPELL_VF_CORROSIVE_OOZE).Weakened()
                .Within(FalloutFloorBounds()).ZTolerance(Tune::kZToleranceYd).Tag(TAG_VF_OOZE);
            ref.OnHit(OnHitFallout([doses](boss_viscous_fallout_rework& ai, Unit* hit)
            {
                ai.AddDose(hit ? hit->ToPlayer() : nullptr, doses, "ooze");
            }));
            ref.OnResolve(OnResolveFallout([at](boss_viscous_fallout_rework& ai, BossMechanics::ResolveResult const&)
            {
                ai._queued.push_back({ PoolKind::Ooze, at });
            }));
            Track(ref.Handle());
            _lobs.push_back({ at, _now + GlobLaunchDelayMs(me->GetExactDist2d(at)) });
            names += " " + target->GetName();
        }
        Log("ooze", Acore::StringFormat("count={} pct={:.0f} dose={} saturated={} why={} targets:{}", count, pct,
            doses, _saturated ? 1 : 0, why, names.empty() ? " -" : names));
    }

    // The glob's missile, launched to land as the warning ends.
    void UpdateLobs()
    {
        for (auto it = _lobs.begin(); it != _lobs.end();)
        {
            if (_now < it->castAt)
            {
                ++it;
                continue;
            }
            me->CastSpell(it->at.GetPositionX(), it->at.GetPositionY(), it->at.GetPositionZ(), SPELL_VF_OOZE_LOB,
                true);
            it = _lobs.erase(it);
        }
    }

    // ---- VF9 Half-Life (heroic) -----------------------------------------------------------------------------------

    bool StartHalfLife(char const* why)
    {
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, SPELL_VF_HALF_LIFE, false);
        if (result != SPELL_CAST_OK)
        {
            // Rule 15: a refused bar is tried again in a second; nothing was drawn.
            _halfLife.Retry(_now, Tune::kHalfLifeRetryMs);
            Log("half-life-refused", Acore::StringFormat("result={} why={}", uint32(result), why));
            return false;
        }
        // RF-1 Minor-2: the shapes and the fallback run on the bar's real length (a cast slow stretches it).
        Spell const* bar = me->GetCurrentSpell(CURRENT_GENERIC_SPELL);
        uint32 const barMs = HalfLifeBarMs(bar && bar->GetSpellInfo()->Id == SPELL_VF_HALF_LIFE
            ? bar->GetCastTime() : 0);
        ++_counts.halfLifes;
        _halfLifeCasting = true;
        _halfLifeEndsAt = _now + barMs;
        _halfLife.Fired(_now);
        Talk(EMOTE_HALF_LIFE);
        // Bots: 8 dose and up stack on him, the rest keep out (the tank never: role), players only.
        BossMechanics::Eligibility hot;
        hot.auraSpell = SPELL_VF_IRRADIATED;
        hot.minStacks = Tune::kHalfLifeBotStacks;
        hot.playersOnly = true;
        MechanicRef stack = Mechanic::Stack(me, me, Tune::kHalfLifeYd, Ms(barMs));
        if (stack.IsValid())
        {
            stack.Eligible(hot).Within(FalloutFloorBounds()).ZTolerance(Tune::kZToleranceYd).Tag(TAG_VF_HALF_LIFE);
            _halfLifeStack = stack.Handle();
        }
        BossMechanics::Eligibility cool;
        cool.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        cool.auraSpell = SPELL_VF_IRRADIATED;
        cool.minStacks = 0;
        cool.maxStacks = uint8(Tune::kHalfLifeBotStacks - 1);
        cool.playersOnly = true;
        MechanicRef out = Mechanic::Circle(me, me, Tune::kHalfLifeYd, Ms(barMs));
        if (out.IsValid())
        {
            out.Eligible(cool).Within(FalloutFloorBounds()).ZTolerance(Tune::kZToleranceYd)
                .Tag(TAG_VF_HALF_LIFE_OUT);
            _halfLifeOut = out.Handle();
        }
        Log("half-life", Acore::StringFormat("ends_in={} why={}", barMs, why));
        return true;
    }

    void ResolveHalfLife()
    {
        _halfLifeCasting = false;
        _halfLifeStack = MechanicHandle();      // registered for the bar's own length: they resolve on this tick
        _halfLifeOut = MechanicHandle();
        uint32 shed = 0;
        uint32 inside = 0;
        if (_dose)
            for (Player* player : FightPlayers())
            {
                if (me->GetExactDist2d(player) > Tune::kHalfLifeYd
                    || std::fabs(player->GetPositionZ() - me->GetPositionZ()) > Tune::kZToleranceYd)
                    continue;
                ++inside;
                uint32 const before = _dose->Dose(player->GetGUID());
                shed += before - _dose->Halve(player, "half-life");
            }
        uint32 const heal = HalfLifeHeal(me->GetMaxHealth(), shed);
        if (heal)
        {
            int32 const bp = int32(std::min<uint32>(heal, uint32(std::numeric_limits<int32>::max())));
            me->CastCustomSpell(me, SPELL_VF_HALF_LIFE_HEAL, &bp, nullptr, nullptr, true);
        }
        Log("half-life-end", Acore::StringFormat("inside={} shed={} heal={}", inside, shed, heal));
    }

    void AbortHalfLife(char const* why)
    {
        _halfLifeCasting = false;
        if (_halfLifeStack)
            Mechanic::Cancel(me, _halfLifeStack);
        if (_halfLifeOut)
            Mechanic::Cancel(me, _halfLifeOut);
        _halfLifeStack = MechanicHandle();
        _halfLifeOut = MechanicHandle();
        Log("half-life-abort", why);
    }

    // ---- helpers ----------------------------------------------------------------------------------------------------

    // The players on his threat list the fight acts on: alive, in the cave (a corpse runner is never picked, rule 5),
    // within `range` of him when given. Players only (pets never take a pool or a pick).
    std::vector<Player*> FightPlayers(float range = 0.f) const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (!Alive(player) || !player->IsInMap(me) || !_arena.Contains(player))
                continue;
            if (range > 0.f && me->GetExactDist2d(player) > range)
                continue;
            out.push_back(player);
        }
        return out;
    }

    // Every player on the map loses this fight's auras (and any stale dose of an earlier pull).
    void StripDose()
    {
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
            {
                player->RemoveAurasDueToSpell(SPELL_VF_IRRADIATED);
                player->RemoveAurasDueToSpell(SPELL_VF_DOSE_GLOW);
                player->RemoveAurasDueToSpell(SPELL_VF_MELTDOWN_AURA);
            }
    }

    static boss_viscous_fallout_rework* From(Map* map, ObjectGuid guid)
    {
        Creature* boss = map ? map->GetCreature(guid) : nullptr;
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_viscous_fallout_rework*>(boss->AI());
    }

    // Registry callbacks capture the map and his guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(Unit*)> OnHitFallout(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](Unit* hit)
        {
            if (boss_viscous_fallout_rework* ai = From(map, guid))
                if (ai->_engaged)
                    fn(*ai, hit);
        };
    }

    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnResolveFallout(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_viscous_fallout_rework* ai = From(map, guid))
                if (ai->_engaged)
                    fn(*ai, result);
        };
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
        // The script's hits resolve within a tick: keep the list short.
        if (_live.size() > 256)
            _live.erase(_live.begin(), _live.begin() + 128);
    }

    void Log(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossKey, mechanic, detail);
    }

    // Boss data (SP "Boss data"): no kill order, no interrupt list; nothing must be dispelled (the Volley Poison is a
    // reward: bots cure it on their own); the tank keeps him out of lasting zones (BM's drag-out reads the rings).
    void Describe()
    {
        BossMechanics::Descriptor d;
        Mechanic::Describe(me, std::move(d));
    }

    // The pull's state, gone (RB-1): the dose (the machine clears every aura it set), the pools (rings, discs), the
    // Meltdown spreads, the Half-Life shapes, every registry handle, Saturated, the glow, the clocks and latches.
    // `_engaged` goes first: a stopped bar's OnSpellFailed then does nothing more.
    void Cleanup(char const* why)
    {
        bool const wasEngaged = _engaged;
        _engaged = false;
        if (_halfLifeCasting)
            AbortHalfLife(why);
        if (me->IsNonMeleeSpellCast(false))
            me->InterruptNonMeleeSpells(false);
        if (_dose)
        {
            _dose->Clear();
            _dose.reset();
        }
        for (auto const& [raw, handle] : _meltdown)
            EndMeltdown(raw, handle);
        _meltdown.clear();
        for (auto const& [id, look] : _looks)
            DropLook(look);
        _looks.clear();
        _pools.Clear();
        _queued.clear();
        _lobs.clear();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (ObjectGuid const& guid : _glowing)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                player->RemoveAurasDueToSpell(SPELL_VF_DOSE_GLOW);
        _glowing.clear();
        _geiger.clear();
        me->RemoveAurasDueToSpell(SPELL_VF_SATURATED);
        _saturated = false;
        _beat = GnomerFallout::Beat{};
        _ooze = GnomerFallout::Beat{};
        _halfLife = GnomerFallout::Beat{};
        _halfLifeEndsAt = 0;
        _now = 0;
        _poolTickMs = 0;
        _saturatedPollMs = 0;
        _saturatedPulseMs = 0;
        _carrierPollMs = 0;
        _carrierSecondMs = 0;
        _counts = Counts{};
        _arena.Reset();
        if (wasEngaged)
            Log("cleanup", why);
    }

    DungeonKit::ArenaGuard _arena;
    std::unique_ptr<GnomereganMachines::DoseField> _dose;
    PoolSet _pools;
    std::map<uint32, PoolLook> _looks;
    std::vector<QueuedPool> _queued;
    std::vector<Lob> _lobs;
    std::map<uint64, MechanicHandle> _meltdown;     // the carrier's raw guid -> its lasting Spread
    GuidSet _glowing;
    std::map<uint64, uint32> _geiger;
    std::vector<MechanicHandle> _live;
    GnomerFallout::Beat _beat;
    GnomerFallout::Beat _ooze;
    GnomerFallout::Beat _halfLife;
    MechanicHandle _halfLifeStack;
    MechanicHandle _halfLifeOut;
    uint64 _halfLifeEndsAt = 0;
    uint64 _now = 0;
    uint32 _poolTickMs = 0;
    uint32 _saturatedPollMs = 0;
    uint32 _saturatedPulseMs = 0;
    uint32 _carrierPollMs = 0;
    uint32 _carrierSecondMs = 0;
    Counts _counts;
    bool _saturated = false;
    bool _halfLifeCasting = false;
    bool _heroic = false;
    bool _engaged = false;
};

// The pool stalker 301130: the nature disc under a pool (its display and scale are set at the summon), inert.
struct npc_gnomer_pool_stalker : public NullCreatureAI
{
    explicit npc_gnomer_pool_stalker(Creature* creature) : NullCreatureAI(creature) { }
};

namespace
{
    boss_viscous_fallout_rework* FindFalloutAI(ChatHandler* handler, bool engaged = true)
    {
        Creature* boss = GnomerTest::FindBoss(handler, NPC_VISCOUS_FALLOUT);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_viscous_fallout_rework*>(boss->AI()) : nullptr;
        if (!ai)
        {
            handler->SendErrorMessage("{}", "Viscous Fallout is not running boss_viscous_fallout_rework.");
            return nullptr;
        }
        if (engaged && !ai->Engaged())
        {
            handler->SendErrorMessage("{}", "Viscous Fallout must be in combat.");
            return nullptr;
        }
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return GnomerTest::ShowBossInfo(handler, NPC_VISCOUS_FALLOUT, BOSS_VISCOUS_FALLOUT);
    }

    // `.dbtest gnomer fallout state`: the clocks, the pools, Saturated, the carriers and the machine.
    bool HandleState(ChatHandler* handler)
    {
        boss_viscous_fallout_rework* ai = FindFalloutAI(handler, false);
        if (!ai)
            return false;
        handler->PSendSysMessage("Viscous Fallout: {}", ai->TestState());
        handler->PSendSysMessage("Machine: {}", ai->TestMachine());
        return true;
    }

    // `.dbtest gnomer fallout volley`: Toxic Volley and Slough now (VF3, VF4).
    bool HandleVolley(ChatHandler* handler)
    {
        boss_viscous_fallout_rework* ai = FindFalloutAI(handler);
        if (!ai)
            return false;
        ai->TestBeat();
        handler->PSendSysMessage("{}", "Viscous Fallout: Toxic Volley and Slough (VF3, VF4).");
        return true;
    }

    // `.dbtest gnomer fallout ooze`: Corrosive Ooze now (VF6).
    bool HandleOoze(ChatHandler* handler)
    {
        boss_viscous_fallout_rework* ai = FindFalloutAI(handler);
        if (!ai)
            return false;
        ai->TestOoze();
        handler->PSendSysMessage("{}", "Viscous Fallout: Corrosive Ooze (VF6).");
        return true;
    }

    // `.dbtest gnomer fallout halflife`: Half-Life now (VF9, heroic).
    bool HandleHalfLife(ChatHandler* handler)
    {
        boss_viscous_fallout_rework* ai = FindFalloutAI(handler);
        if (!ai)
            return false;
        if (!ai->TestHalfLife())
        {
            handler->SendErrorMessage("{}", "Refused: Half-Life is heroic only, one is running, or the bar was "
                "refused (see the log).");
            return false;
        }
        handler->PSendSysMessage("{}", "Viscous Fallout: Half-Life (VF9).");
        return true;
    }

    // `.dbtest gnomer fallout dose <n>`: the selected player's (or your) dose set to n (VF1; at the normal cap this is
    // Radiation Sickness, at 10 / 20 on heroic Leaking / Meltdown).
    bool HandleDose(ChatHandler* handler, uint32 dose)
    {
        boss_viscous_fallout_rework* ai = FindFalloutAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        handler->PSendSysMessage("{}'s dose: {} (VF1).", target->GetName(), ai->TestDose(target, dose));
        return true;
    }

    // `.dbtest gnomer fallout sickness`: Radiation Sickness on the selected player (or you), its dose kept (VF2).
    bool HandleSickness(ChatHandler* handler)
    {
        boss_viscous_fallout_rework* ai = FindFalloutAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestSickness(target);
        handler->PSendSysMessage("Radiation Sickness on {} (VF2).", target->GetName());
        return true;
    }

    // `.dbtest gnomer fallout leak`: a Leaking pool at the selected player's (or your) feet (VF7).
    bool HandleLeak(ChatHandler* handler)
    {
        boss_viscous_fallout_rework* ai = FindFalloutAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestLeak(target);
        handler->PSendSysMessage("A Leaking pool under {} (VF7).", target->GetName());
        return true;
    }

    // `.dbtest gnomer fallout pool <volley|slough|ooze|leak>`: a pool of that kind at your feet.
    bool HandlePool(ChatHandler* handler, std::string kindName)
    {
        boss_viscous_fallout_rework* ai = FindFalloutAI(handler);
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!ai || !gm)
            return false;
        for (uint8 k = 0; k < kPoolKindNames.size(); ++k)
            if (StringEqualI(kindName, kPoolKindNames[k]))
            {
                ai->TestPool(PoolKind(k), gm->GetPosition());
                handler->PSendSysMessage("A {} pool at your feet.", kPoolKindNames[k]);
                return true;
            }
        handler->SendErrorMessage("{}", "Usage: .dbtest gnomer fallout pool <volley|slough|ooze|leak>");
        return false;
    }

    ChatCommandTable const& FalloutTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "volley",   HandleVolley,   SEC_GAMEMASTER, Console::No },
            { "ooze",     HandleOoze,     SEC_GAMEMASTER, Console::No },
            { "halflife", HandleHalfLife, SEC_GAMEMASTER, Console::No },
            { "dose",     HandleDose,     SEC_GAMEMASTER, Console::No },
            { "sickness", HandleSickness, SEC_GAMEMASTER, Console::No },
            { "leak",     HandleLeak,     SEC_GAMEMASTER, Console::No },
            { "pool",     HandlePool,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_viscous_fallout_rework()
{
    RegisterDungeonReworkCreatureAI(boss_viscous_fallout_rework, GnomereganRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_pool_stalker, GnomereganRework::kInstanceScriptName);
    GnomerTest::RegisterBoss("fallout", FalloutTestCommands());
}
