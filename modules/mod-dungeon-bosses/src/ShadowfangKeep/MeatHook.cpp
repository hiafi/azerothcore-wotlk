/*
 * mod-dungeon-bosses, Shadowfang Keep: Meat Hook (RC1), shared by Razorclaw (WP-S2) and the Echo of Razorclaw (WP-S3).
 * See MeatHook.h. The once-per-throw SpellScript follows the Deadmines Pilot's spell_dm_greenskin_lane_hit
 * (boss_captain_greenskin_rework.cpp).
 */

#include "MeatHook.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameTime.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ShadowfangKeepRework.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include <mutex>
#include <string>

namespace
{
    // The once-per-throw memory of every thrower on every map (map threads run in parallel: one lock).
    std::mutex sThrowLock;
    Razorclaw::HookVolleyMemory sThrows;

    uint64 NowMs()
    {
        return static_cast<uint64>(GameTime::GetGameTimeMS().count());
    }

    uint32 RandomBelow(uint32 n)
    {
        return n ? urand(0, n - 1) : 0;
    }

    // The players a throw may pick from: alive, in the world on the thrower's map, not game masters, within maxRangeYd,
    // in combat (unless `widen`). The tank is the registry's role provider's (the encounter owner's victim, or a tank
    // spec), as the bots read it.
    void Candidates(Creature* thrower, Unit const* roleOwner, MeatHook::ThrowSpec const& spec,
        std::vector<Player*>& players, std::vector<DungeonKit::PickCandidate>& candidates)
    {
        BossMechanics::RoleProvider const& roles = BossMechanics::GetRoleProvider();
        Map::PlayerList const& list = thrower->GetMap()->GetPlayers();
        for (Map::PlayerList::const_iterator itr = list.begin(); itr != list.end(); ++itr)
        {
            Player* player = itr->GetSource();
            if (!player || !player->IsInWorld() || !player->IsAlive() || player->IsGameMaster())
                continue;
            if (!spec.widen && !player->IsInCombat())
                continue;
            float const distance = thrower->GetExactDist2d(player);
            if (distance > spec.tuning.maxRangeYd)
                continue;
            DungeonKit::PickCandidate c;
            c.id = player->GetGUID().GetRawValue();
            c.distance = distance;
            c.tank = roles.Get(roleOwner, player) == BossMechanics::Role::Tank;
            c.inLos = thrower->IsWithinLOSInMap(player);
            players.push_back(player);
            candidates.push_back(c);
        }
    }

    // A unit a line hit: the chain look and the drag to the thrower's front (toward its victim, the Cut's side), then
    // the heroic bleed.
    void Drag(Creature* thrower, Unit* hit, Razorclaw::HookTuning const& tuning, char const* logBoss,
        char const* logMechanic)
    {
        Unit const* victim = thrower->GetVictim();
        float const facing = victim && victim != hit ? thrower->GetAngle(victim) : thrower->GetOrientation();
        DungeonKit::Vec2 const front = DungeonKit::Advance(DungeonKit::PlaneOf(thrower), facing, tuning.frontYd);
        float z = thrower->GetMapHeight(front.x, front.y, thrower->GetPositionZ() + 2.f);
        if (z <= INVALID_HEIGHT + 1.f)
            z = thrower->GetPositionZ();
        float const distance = hit->GetExactDist2d(front.x, front.y);
        float const speedXY = Razorclaw::DragSpeedXY(distance, tuning);
        DungeonKit::JumpTo(hit, Position(front.x, front.y, z + 0.1f, facing + DungeonKit::kPi), speedXY,
            Razorclaw::kDragMinSpeedZ, Razorclaw::SPELL_RC_MEAT_HOOK_CHAIN, thrower);

        int32 bleedTick = 0;
        if (tuning.bleedPct > 0.f)
        {
            bleedTick = static_cast<int32>(DungeonKit::RefFlat(thrower, Razorclaw::BleedTickPct(tuning)));
            thrower->CastCustomSpell(Razorclaw::SPELL_RC_HUNG_TO_BLEED, SPELLVALUE_BASE_POINT0, bleedTick, hit,
                TRIGGERED_FULL_MASK);
        }
        DungeonKit::LogMechanic(ShadowfangKeepRework::kLogDungeon, logBoss, logMechanic,
            Acore::StringFormat("hooked unit={} drag={:.1f}yd speed={:.1f} bleedTick={}", hit->GetName(), distance,
                speedXY, bleedTick));
    }
}

namespace MeatHook
{
    ThrowResult Throw(Creature* thrower, ThrowSpec const& spec, Unit* owner)
    {
        ThrowResult out;
        if (!thrower || !thrower->IsInWorld() || !thrower->IsAlive() || !spec.tuning.lines)
            return out;
        Unit* encounter = owner ? owner : thrower;

        std::vector<Player*> players;
        std::vector<DungeonKit::PickCandidate> candidates;
        Candidates(thrower, encounter, spec, players, candidates);
        std::vector<std::size_t> const picks = Razorclaw::PickHookTargets(candidates, spec.tuning, spec.widen,
            RandomBelow);
        if (picks.empty())
        {
            DungeonKit::LogMechanic(ShadowfangKeepRework::kLogDungeon, spec.logBoss, spec.logMechanic,
                Acore::StringFormat("skipped (no non-tank {:.0f}+ yd away)", spec.tuning.minRangeYd));
            return out;
        }

        Player* first = players[picks.front()];
        thrower->SetFacingToObject(first);
        if (spec.castBarSpell)
            DungeonKit::CastBar(thrower, spec.castBarSpell, nullptr, spec.emote, first);

        // Capture the map and guids only (a lambda the registry keeps must not hold a Unit*; STAGE-M5-R-REPORT m-4).
        Map* map = thrower->GetMap();
        ObjectGuid const throwerGuid = thrower->GetGUID();
        Razorclaw::HookTuning const tuning = spec.tuning;
        char const* const logBoss = spec.logBoss;
        char const* const logMechanic = spec.logMechanic;

        std::string names;
        for (std::size_t const i : picks)
        {
            Player* target = players[i];
            DungeonKit::LineStrikeSpec line;
            line.width = tuning.widthYd;
            line.overrun = tuning.overrunYd;
            line.excludeSourceEnd = tuning.excludeYd;
            line.warn = Milliseconds(tuning.warnMs);
            line.pct = tuning.pct;
            line.spellId = Razorclaw::SPELL_RC_MEAT_HOOK_HIT;
            line.weakened = true;
            line.tag = tuning.tag;
            line.clip = spec.clip;
            line.onHit = [map, throwerGuid, tuning, logBoss, logMechanic](Unit* hit)
            {
                if (!map || !hit || !hit->IsInWorld() || !hit->IsAlive())
                    return;
                Creature* source = map->GetCreature(throwerGuid);
                if (!source || !source->IsAlive())
                    return;
                Drag(source, hit, tuning, logBoss, logMechanic);
            };
            DungeonKit::LineStrikeResult const r = DungeonKit::LineStrike(encounter, thrower->GetPosition(),
                target->GetPosition(), line);
            if (!r.handle)
                continue;
            out.targets.push_back(target->GetGUID());
            out.lines.push_back(r.handle);
            if (!names.empty())
                names += ',';
            names += Acore::StringFormat("{}({:.1f}yd{})", target->GetName(), r.length, r.clipped ? " clipped" : "");
        }
        DungeonKit::LogMechanic(ShadowfangKeepRework::kLogDungeon, spec.logBoss, spec.logMechanic,
            Acore::StringFormat("lines={} targets={} pct={:.0f} bleed={:.0f}", out.lines.size(), names, tuning.pct,
                tuning.bleedPct));
        return out;
    }

    void Forget(Unit const* owner)
    {
        if (!owner)
            return;
        std::lock_guard<std::mutex> guard(sThrowLock);
        sThrows.Forget(owner->GetGUID().GetRawValue());
    }
}

// 205931 Meat Hook (with spell_boss_mechanics_resolve): a unit an earlier line of the same throw already hit is dropped
// from this line's targets (SK RC1 heroic Twin Hooks: "a player standing in both lines is hit once"; one drag, one
// Weakened). The registry casts every line of a throw on one tick, each hitting inside its CastSpell call, with the
// lines' owner as the original caster; the memory is keyed by that owner (Razorclaw, or whoever owns the echo's lines).
class spell_sfk_meat_hook_once : public SpellScript
{
    PrepareSpellScript(spell_sfk_meat_hook_once);

    uint64 ThrowerKey()
    {
        Unit* owner = GetOriginalCaster();
        return owner ? owner->GetGUID().GetRawValue() : 0;
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        uint64 const thrower = ThrowerKey();
        if (!thrower)
            return;
        uint64 const now = NowMs();
        std::lock_guard<std::mutex> guard(sThrowLock);
        targets.remove_if([thrower, now](WorldObject* obj)
        {
            return obj && sThrows.AlreadyHit(thrower, obj->GetGUID().GetRawValue(), now);
        });
    }

    void RecordHit()
    {
        uint64 const thrower = ThrowerKey();
        Unit* target = GetHitUnit();
        if (!thrower || !target)
            return;
        std::lock_guard<std::mutex> guard(sThrowLock);
        sThrows.Record(thrower, target->GetGUID().GetRawValue(), NowMs());
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sfk_meat_hook_once::FilterTargets, EFFECT_0,
            TARGET_UNIT_SRC_AREA_ENEMY);
        AfterHit += SpellHitFn(spell_sfk_meat_hook_once::RecordHit);
    }
};

namespace MeatHook
{
    void AddSC_meat_hook()
    {
        RegisterSpellScript(spell_sfk_meat_hook_once);
    }
}
