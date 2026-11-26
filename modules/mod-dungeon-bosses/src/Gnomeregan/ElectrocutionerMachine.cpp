/*
 * mod-dungeon-bosses, Gnomeregan D3: the VoltageMeter machine (GnomereganMachines.h; how it runs:
 * ElectrocutionerMachine.h). Electrocutioner's AI owns one; D6Hb's Electrocutioner schematic (MT21, MT22) owns another
 * on Thermaplugg through MakeVoltageMeter with its own spec.
 */

#include "ElectrocutionerMachine.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "GnomereganKit.h"
#include "GnomereganRework.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "SharedDefines.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <utility>

using namespace GnomerElectro;

namespace GnomereganMachines
{
    ElectroVoltageMeter::ElectroVoltageMeter(MachineOwner const& owner, VoltageSpec spec)
        : _logKey(owner.logKey ? owner.logKey : ""), _heroic(owner.heroic), _spec(std::move(spec))
    {
        if (owner.owner)
        {
            _owner = owner.owner->GetGUID();
            _map = owner.owner->GetMap();
        }
        VoltageRules rules;
        rules.tickMs = _spec.tickEveryMs;
        rules.every = _spec.justiceEvery;
        rules.resetAfterJustice = _spec.resetAfterJustice;
        rules.pauseAfterMs = _spec.pauseAfterJusticeMs;
        rules.minGapMs = _spec.justiceMinGapMs;
        _clock = VoltageClock(rules);
    }

    Creature* ElectroVoltageMeter::Owner() const
    {
        if (!_map || _owner.IsEmpty())
            return nullptr;
        Creature* owner = _map->GetCreature(_owner);
        return owner && owner->IsInWorld() ? owner : nullptr;
    }

    float ElectroVoltageMeter::DamageMultiplier() const
    {
        return GnomerElectro::DamageMultiplier(_clock.Stacks(), _spec.damagePctPerStack);
    }

    void ElectroVoltageMeter::Log(char const* what, std::string const& detail) const
    {
        DungeonKit::LogMechanic(GnomereganRework::kLogDungeon, _logKey, "voltage",
            detail.empty() ? std::string(what) : Acore::StringFormat("{} {}", what, detail));
    }

    void ElectroVoltageMeter::Update(uint32 diff)
    {
        Creature* owner = Owner();
        if (!owner || !owner->IsAlive())
            return;
        _now += diff;

        // The landing first: the zone's resolve (recorded by the registry's callback, rule 11), or no resolve at all
        // (refused, canceled) once the bar is well past.
        if (_clock.Running())
        {
            // The hits move out first: Land() resets _landing, the only owner of the vector (F-1b B1).
            if (_landing && _landing->resolved)
                Land(owner, std::move(_landing->hits), true);
            else if (_now >= _landDeadline)
                Land(owner, {}, false);
        }

        if (_clock.Advance(diff) > 0)
            ApplyStacks(owner);

        if (_reassertLeft <= diff)
        {
            _reassertLeft = Tune::kReassertMs;
            ApplyStacks(owner);
        }
        else
            _reassertLeft -= diff;

        _retryLeft = _retryLeft > diff ? _retryLeft - diff : 0;
        if (_clock.JusticeDue() && _retryLeft == 0)
            TryStartJustice(owner);
    }

    uint32 ElectroVoltageMeter::Add(uint32 stacks, char const* why)
    {
        Creature* owner = Owner();
        if (!owner || !owner->IsAlive() || stacks == 0)
            return _clock.Stacks();
        uint32 const gained = _clock.Add(stacks);
        if (gained > 0)
            ApplyStacks(owner);
        Log("add", Acore::StringFormat("why={} asked={} gained={} stacks={} paused={} next={}", why ? why : "-", stacks,
            gained, _clock.Stacks(), _clock.PauseLeft(), _clock.NextAt()));
        return _clock.Stacks();
    }

    // Rule 25: the count on the owner is the clock's (a recalculation or a stray removal is undone within a second);
    // the brighter crackle from 3 stacks (V's tier 2).
    void ElectroVoltageMeter::ApplyStacks(Creature* owner)
    {
        uint32 const want = std::min(_clock.Stacks(), Tune::kVoltageStackLimit);
        if (_spec.auraSpellId)
        {
            uint32 const have = DungeonKit::Stacks(owner, _spec.auraSpellId, owner->GetGUID());
            if (have != want)
                DungeonKit::AddStacks(owner, _spec.auraSpellId, int32(want) - int32(have), owner,
                    Tune::kVoltageStackLimit);
        }
        bool const charged = VoltageTier(want) >= 2;
        if (charged && !owner->HasAura(SPELL_VOLTAGE_CHARGED))
            owner->AddAura(SPELL_VOLTAGE_CHARGED, owner);
        else if (!charged && owner->HasAura(SPELL_VOLTAGE_CHARGED))
            owner->RemoveAurasDueToSpell(SPELL_VOLTAGE_CHARGED);
    }

    void ElectroVoltageMeter::TryStartJustice(Creature* owner)
    {
        // A cast already running (his Chain Bolt, a Megavolt bar) finishes first: the next Update looks again.
        if (owner->HasUnitState(UNIT_STATE_CASTING))
            return;
        JusticeSpec const& j = _spec.justice;
        if (j.barSpellId)
        {
            SpellCastResult const result = owner->CastSpell(owner, j.barSpellId, false);
            if (result != SPELL_CAST_OK)
            {
                _retryLeft = Tune::kBarRetryMs;
                Log("refused", Acore::StringFormat("bar={} result={} stacks={}", j.barSpellId, uint32(result),
                    _clock.Stacks()));
                return;
            }
        }

        uint32 const index = _started++;
        _shape = JusticeShapeFor(index, j.alternate);
        float const pct = j.pct * DamageMultiplier();
        uint32 const stacksAtStart = _clock.Stacks();
        _clock.StartJustice(j.castMs);
        _landDeadline = _now + j.castMs + Tune::kJusticeLandGraceMs;

        _landing = std::make_shared<Landing>();
        std::weak_ptr<Landing> const landing = _landing;
        BossMechanics::SpotBounds const bounds = _botBounds ? *_botBounds : GnomereganRework::BoundsOf(j.floor);
        float const outer = JusticeOuterYd(j.floor, DungeonKit::PlaneOf(owner), j.safeRadius);
        {
            Milliseconds const warn(j.castMs);
            BossMechanics::MechanicRef ref = _shape == JusticeShape::Circle
                ? Mechanic::Circle(owner, owner, j.circleRadius, warn)
                : Mechanic::Donut(owner, owner, j.safeRadius, outer, warn);
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NATURE).Spell(SPELL_JUSTICE_HIT)
                .Tag(j.tag ? j.tag : (_shape == JusticeShape::Circle ? TAG_JUSTICE_CIRCLE : TAG_JUSTICE_DONUT))
                .Within(bounds)
                .OnResolve([landing](BossMechanics::ResolveResult const& result)
                {
                    // Only recorded here (rule 11: nothing is registered or cast inside the registry's callback).
                    if (std::shared_ptr<Landing> const l = landing.lock())
                        if (result.mechanicId == l->mechanicId)
                        {
                            l->resolved = true;
                            l->hits = result.hits;
                        }
                });
            _landing->mechanicId = ref.Id();
            _zone = ref.Handle();
        }

        if (owner->IsAIEnabled && owner->AI())
        {
            if (j.yellGroup)
                owner->AI()->Talk(*j.yellGroup);
            std::optional<uint8> const emote = _shape == JusticeShape::Circle ? j.circleEmoteGroup : j.donutEmoteGroup;
            if (emote)
                owner->AI()->Talk(*emote);
        }
        Log("justice-start", Acore::StringFormat("count={} shape={} stacks={} pct={:.1f} mult={:.2f} safe={:.0f} "
            "outer={:.1f} circle={:.0f} zone={} cast={}", index + 1,
            _shape == JusticeShape::Circle ? "circle" : "donut", stacksAtStart, pct, DamageMultiplier(), j.safeRadius,
            outer, j.circleRadius, _zone.id, j.castMs));
        if (_spec.onJusticeStart)
            _spec.onJusticeStart(index + 1);
    }

    void ElectroVoltageMeter::Land(Creature* owner, std::vector<ObjectGuid> hits, bool resolved)
    {
        JusticeShape const shape = _shape;
        _clock.LandJustice();
        _zone = {};
        _landing.reset();
        ApplyStacks(owner);
        BlastLook(owner, shape);

        std::vector<Player*> players;
        std::string names;
        for (ObjectGuid const& guid : hits)
            if (guid.IsPlayer())
                if (Player* player = ObjectAccessor::GetPlayer(*owner, guid))
                {
                    players.push_back(player);
                    names += " " + player->GetName();
                }
        Log("justice-land", Acore::StringFormat("count={} shape={} resolved={} hit={} stacks={} next={} pause={}:{}",
            _clock.Justices(), shape == JusticeShape::Circle ? "circle" : "donut", resolved ? 1 : 0, players.size(),
            _clock.Stacks(), _clock.NextAt(), _clock.PauseLeft(), names.empty() ? " -" : names));
        if (_spec.onJusticeLand)
            _spec.onJusticeLand(_clock.Justices(), players);
    }

    // V: SV 3 (the thunderclap ring and the called lightning) on short-lived blast stalkers: a ring of them through
    // the donut (on the floor only), one on him for the circle. Map summons, so the owner's AI never sees them.
    void ElectroVoltageMeter::BlastLook(Creature* owner, JusticeShape shape)
    {
        std::vector<Vec2> points;
        if (shape == JusticeShape::Circle)
            points.push_back(DungeonKit::PlaneOf(owner));
        else
            for (Vec2 const& p : RingPoints(DungeonKit::PlaneOf(owner), Tune::kBlastRingYd, Tune::kBlastPoints))
                if (_spec.justice.floor.Empty() || _spec.justice.floor.Contains(p, owner->GetPositionZ()))
                    points.push_back(p);
        for (Vec2 const& p : points)
        {
            Position const at(p.x, p.y, owner->GetPositionZ(), 0.f);
            if (TempSummon* stalker = owner->GetMap()->SummonCreature(GnomereganRework::NPC_BLAST_STALKER, at))
            {
                stalker->CastSpell(stalker, SPELL_JUSTICE_BLAST, true);
                stalker->DespawnOrUnsummon(Milliseconds(Tune::kBlastStalkerMs));
            }
        }
    }

    void ElectroVoltageMeter::Clear()
    {
        Creature* owner = Owner();
        if (owner)
        {
            if (_zone)
                Mechanic::Cancel(owner, _zone);
            if (_spec.auraSpellId)
                owner->RemoveAurasDueToSpell(_spec.auraSpellId);
            owner->RemoveAurasDueToSpell(SPELL_VOLTAGE_CHARGED);
        }
        bool const had = _clock.Stacks() > 0 || _clock.Running() || _clock.Justices() > 0;
        _clock.Reset();
        _zone = {};
        _landing.reset();
        _shape = JusticeShape::Donut;
        _started = 0;
        _now = 0;
        _landDeadline = 0;
        _retryLeft = 0;
        _reassertLeft = 0;
        if (had)
            Log("clear", {});
    }

    std::string ElectroVoltageMeter::Describe() const
    {
        return Acore::StringFormat("voltage stacks={} next={} to-next={} running={} paused={} gap={} justices={} "
            "mult={:.2f} zone={}", _clock.Stacks(), _clock.NextAt(), _clock.ToNext(), _clock.Running() ? 1 : 0,
            _clock.PauseLeft(), _clock.GapLeft(), _clock.Justices(), DamageMultiplier(), _zone.id);
    }

    VoltageSpec ElectrocutionerVoltageSpec(bool heroic)
    {
        VoltageSpec spec;
        spec.auraSpellId = SPELL_VOLTAGE;
        spec.tickEveryMs = Tune::kVoltageTickMs;
        spec.justiceEvery = Tune::kJusticeEvery;
        spec.resetAfterJustice = !heroic;
        spec.pauseAfterJusticeMs = Tune::kJusticePauseAfterMs(heroic);
        spec.justiceMinGapMs = Tune::kJusticeMinGapMs(heroic);
        spec.damagePctPerStack = Tune::kLightningPctPerStack(heroic);
        spec.justice.barSpellId = SPELL_JUSTICE_BAR;
        spec.justice.castMs = Tune::kJusticeCastMs;
        spec.justice.safeRadius = Tune::kJusticeSafeYd;
        spec.justice.circleRadius = Tune::kJusticeCircleYd;
        spec.justice.alternate = heroic;
        spec.justice.pct = Tune::kJusticePct;
        spec.justice.floor = JusticeFloor();     // the platform and the walkway (R-1-A M1)
        spec.justice.yellGroup = SAY_JUSTICE;
        spec.justice.donutEmoteGroup = EMOTE_JUSTICE_DONUT;
        spec.justice.circleEmoteGroup = EMOTE_JUSTICE_CIRCLE;
        return spec;
    }

    std::unique_ptr<ElectroVoltageMeter> MakeElectroVoltageMeter(MachineOwner const& owner, VoltageSpec spec)
    {
        return std::make_unique<ElectroVoltageMeter>(owner, std::move(spec));
    }

    std::unique_ptr<VoltageMeter> MakeVoltageMeter(MachineOwner const& owner, VoltageSpec spec)
    {
        return std::make_unique<ElectroVoltageMeter>(owner, std::move(spec));
    }
}
