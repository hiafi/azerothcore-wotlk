/*
 * mod-dungeon-bosses, Scholomance S5: Instructor Malicia (10505), normal and heroic, her detention lesson (the Coven)
 * and her Graduate Examiner mode. Build spec: SC 1431-1488 (build spec), SC 1250-1430 (design: pitch B "Soul stacks",
 * approved 2026-10-31), MA1-MA9; handoff section 3.4 rows MA, section 3.5 row S5, sections 3.6-3.8. Replaces SmartAI
 * 10505 (Call of the Grave 12020, Renew 8362, Flash Heal 17843 and Heal 15586 retired; Corruption 18376 and Slow 13747
 * kept in C++; WP-S5's SQL rev drops the seven rows, the instance data row among them: Gandling's reveal reads the
 * boss states). Bound by apps/dbc-tools source/npcs/scholomance/instructor_malicia.py.
 *
 *   MA1 Soul             every player of the fight gets Soul 206205 at 20 stacks (the meter) and its hidden weight
 *                        206206: each stack above or below 20 is +-5% damage done, healing done and max health
 *                        (floor 10, cap 40). A player who comes back from the dead gets their last count back. Both
 *                        drop on a logout or a map change (AURA_INTERRUPT_FLAG_CHANGE_MAP, the DT file).
 *   MA2 Soul Drain       10 s, then every 20 s (normal) / 30 s (heroic): a 2 s cast (206207). Normal: one random
 *                        non-tank (two below 50% of her health), emote line 0. Heroic: every player, the tank too,
 *                        emote line 1. Each loses 4 stacks (never under 10) and that many Loose Souls land 10 to 15 yd
 *                        around them (the drain's look 206208 on each).
 *   MA3 Loose Soul       300537 (the wisp): walking through one (2 yd) gives a stack (below the cap). Fades in 8 s /
 *                        5 s and flies to her: +1 Bound Soul. Bots: a Soak per soul, lowest Soul first, nobody at the
 *                        cap, never the tank (a human tank may still take one); it never resolves.
 *   MA4 Call a Student   15 s, then every 25 s: 1 (normal) / 2 (heroic) Malicia's Shades 300536 rise 15 to 25 yd from
 *                        her (emote line 2). A shade casts the stock Shadow Bolt Volley 17228 behind a kickable 2 s
 *                        cast (206210). Killed: 4 souls where it dies. Alive 20 s: it walks into her (+4 Bound Soul).
 *   MA5 Bound Soul       206209 on her: +2% damage a stack, cap 20 (the aura for her melee and stock spells; the
 *                        Soulstorm and Shadow Nova percents are scaled by the same factor, BoundDamageScale).
 *   MA6 Soulstorm        20 s, then every 30 s: a 3.5 s cast (206211, emote line 3) and 3 waves 1 s apart of 4 yd
 *                        registry circles (1.5 s). Normal: one random non-tank plus 2 random spots a wave, and never
 *                        while a drain's souls are down. Heroic: every player plus 1 random spot. A player's marker is
 *                        centered 2 yd from them at a random bearing; random spots never within 6 yd of a player.
 *                        20% / 30% Shadow (206213); a hit destroys a Soul stack; souls under a blast are destroyed. A
 *                        falling soul (206212) lands on each marker as it resolves; the burst (206214) shows on all.
 *   MA7 Shadow Heal      below 50%, every 20 s: a 3.5 s kickable cast (206215, interrupt list): she heals 5% / 10%
 *                        and the nova (206216) hits every player for 15% / 40% Shadow.
 *   MA8 Slow             stock 13747 (Magic, dispel list): 13 to 15 s, then 20 to 35 s, with a player within 20 yd.
 *   MA9 Corruption       stock 18376 (Magic, dispel list; do-not-kick): 3 to 12 s, then 17 to 22 s, with a player
 *                        within 10 yd.
 *   Melee                DamageModifier 3.5 (the AC base value, set by the DT file); heroic is the heroic template's.
 *   Arena                MaliciaArena() with LeashOptions (no grips; holds at the edge, evades after 10 s with nobody
 *                        on it). The Coven's gate is the instance's door data on BOSS_MALICIA. Only the players on her
 *                        arena are in her fight (meters, drains, storm marks): one shut outside is left alone.
 *   Grades               GradeWatch (heroic): a Soulstorm hit costs the grade; a faded soul never does (its Soak never
 *                        resolves, so no group failure either).
 *
 * Every timer runs on the AI's own clock (MaliciaLogic.h Timeline), never on BossAI's scheduler that a cast bar pauses;
 * a beat that comes due while she casts waits for the cast to end (Call a Student and Slow are instant and do not).
 * Pending drains, waves and falling souls run on a clock that also runs out of combat (`.dbtest scholo malicia`).
 *
 * Detention (S11): CovenLesson, registered for Classroom::Coven. Examiner (S13): npc_sc_examiner_malicia, the same
 * fight at heroic values (MaliciaFight.h). Every firing logs one INFO line "scholo malicia <mechanic> ..."
 * (module.dungeonbosses); `.dbtest scholo malicia <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitLogic.h"
#include "MaliciaFight.h"
#include "MaliciaLogic.h"
#include "Map.h"
#include "MechanicWeakened.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SoloLesson.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoMalicia;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "malicia";
    char const* const kExaminerLogName = "malicia-examiner";
    char const* const kLessonLogName = "malicia-lesson";

    // How far up and down a floor point looks for the ground (her slab rises 6 yd over the floor).
    float constexpr kFloorSearchUp = 7.f;
    // A bar she could not start (a kick's school lockout, a silence): the beat tries again this soon.
    uint32 constexpr kCastRetryMs = 1000;

    // The ground under a point (souls, shades and markers stand on it); falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + kFloorSearchUp);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > kFloorSearchUp + 1.f) ? z : floor;
    }

    Position FloorPoint(WorldObject const* ref, Vec2 p, float z, float orientation = 0.f)
    {
        return Position(p.x, p.y, FloorZ(ref, p.x, p.y, z), orientation);
    }

    float Rand01()
    {
        return static_cast<float>(rand_norm());
    }

    // Heroic numbers: a heroic map, or her examiner (always heroic values, SC 3046).
    bool HeroicValues(Unit const* caster)
    {
        if (!caster)
            return false;
        if (caster->GetEntry() == NPC_SC_EXAMINER_MALICIA)
            return true;
        return DungeonKit::IsHeroicMap(caster);
    }

    // ---- MA1 the Soul meter -----------------------------------------------------------------------------------------

    // The hidden weight follows the meter: added with it, recalculated on every change (its AuraScript reads the
    // stacks), removed with it.
    void SyncWeight(Player* player)
    {
        uint32 const stacks = ScholoMalicia::SoulOf(player);
        if (!stacks)
        {
            player->RemoveAurasDueToSpell(SPELL_MA_SOUL_WEIGHT);
            return;
        }
        if (Aura* weight = player->GetAura(SPELL_MA_SOUL_WEIGHT))
        {
            if (!weight->IsRemoved())
                weight->RecalculateAmountOfEffects();
        }
        else
            player->AddAura(SPELL_MA_SOUL_WEIGHT, player);
    }

    // Exactly `stacks` (self-applied, so the meter never needs her alive); returns the new count.
    uint32 SetSoul(Player* player, uint32 stacks)
    {
        if (!player)
            return 0;
        uint32 const current = ScholoMalicia::SoulOf(player);
        uint32 const now = DungeonKit::AddStacks(player, SPELL_MA_SOUL, int32(stacks) - int32(current), nullptr,
            kSoulCap);
        SyncWeight(player);
        return now;
    }

    // `delta` stacks inside [floor, cap] (SoulAfter); nothing without a meter. Returns the new count.
    uint32 AddSoul(Player* player, int32 delta)
    {
        uint32 const current = ScholoMalicia::SoulOf(player);
        if (!current || !delta)
            return current;
        return SetSoul(player, SoulAfter(current, delta));
    }
}

uint32 ScholoMalicia::SoulOf(Player const* player)
{
    return player ? DungeonKit::Stacks(player, SPELL_MA_SOUL) : 0;
}

void ScholoMalicia::ClearSoul(Player* player)
{
    if (!player)
        return;
    player->RemoveAurasDueToSpell(SPELL_MA_SOUL);
    player->RemoveAurasDueToSpell(SPELL_MA_SOUL_WEIGHT);
}

namespace
{
    // ---------------------------------------------------------------------------------------------------------------
    // MA3 Loose Souls on the floor, owned by one unit (her, her examiner, or a detention lesson's stalker): the wisp, a
    // registry Soak per soul for the bots (it never resolves: the pickup or the fade cancels it first), the walk-in
    // pickup and the fade.
    // ---------------------------------------------------------------------------------------------------------------
    class SoulField
    {
    public:
        struct Spec
        {
            uint32 fadeMs = 8000;
            BossMechanics::Eligibility botsWho;     // the Soak's eligibility: the bots that go for it
            GuidSet takers;                         // empty: anyone with a meter below the cap may take it
            bool flyToOwner = true;                 // a faded soul flies to the owner (her); else it just goes
        };

        std::function<void(Player* taker, uint32 now)> onPick;
        std::function<void(Position const& at, bool fromDrain)> onFade;

        void Spill(Creature* owner, Position const& at, bool fromDrain, Spec const& spec)
        {
            if (!owner || !owner->IsInWorld())
                return;
            Soul soul;
            soul.at = at;
            soul.spec = spec;
            soul.fromDrain = fromDrain;
            if (TempSummon* unit = owner->SummonCreature(NPC_SC_LOOSE_SOUL, at.GetPositionX(), at.GetPositionY(),
                    at.GetPositionZ() + kSoulHoverZ, frand(0.f, DungeonKit::kTwoPi), TEMPSUMMON_TIMED_DESPAWN,
                    spec.fadeMs + kSoulFlyMs + 2000))
            {
                unit->SetReactState(REACT_PASSIVE);
                unit->SetDisableGravity(true);
                soul.unit = unit->GetGUID();
            }
            {
                MechanicRef ref = Mechanic::Soak(owner, at, kSoulRadius, 1,
                    Milliseconds(spec.fadeMs + kSoulSoakSlackMs));
                ref.Eligible(spec.botsWho).Order(BossMechanics::Ordering{ SPELL_MA_SOUL, true, uint8(kSoulCap) })
                    .NoFillTimer().Tag(TAG_LOOSE_SOUL).OneClaimPerBot();    // one soul a bot at a time (F-B5)
                soul.soak = ref.Handle();
            }
            _souls.push_back(std::move(soul));
        }

        void Update(Creature* owner, uint32 diff)
        {
            if (!owner || _souls.empty())
                return;
            _pollMs += diff;
            if (_pollMs < kSoulPollMs)
                return;
            uint32 const elapsed = _pollMs;
            _pollMs = 0;

            Map* map = owner->GetMap();
            // The stacks each player takes in this poll: a player at 39 inside two souls takes one, the other stays.
            std::unordered_map<ObjectGuid, uint32> gained;
            std::vector<std::pair<ObjectGuid, Soul>> picked;
            std::vector<Soul> faded;
            std::vector<Soul> kept;
            for (Soul& soul : _souls)
            {
                soul.ageMs += elapsed;
                if (soul.ageMs >= soul.spec.fadeMs)
                {
                    faded.push_back(soul);
                    continue;
                }
                // The taker: the lowest meter inside (ties: the lowest guid), as the bots' Soak orders it.
                Player* taker = nullptr;
                uint32 takerStacks = 0;
                for (auto const& ref : map->GetPlayers())
                {
                    Player* player = ref.GetSource();
                    if (!player || !player->IsAlive() || player->IsGameMaster())
                        continue;
                    if (!soul.spec.takers.empty() && !soul.spec.takers.count(player->GetGUID()))
                        continue;
                    if (!DungeonKit::InPickupRange(player->GetExactDist2d(soul.at),
                            player->GetPositionZ() - soul.at.GetPositionZ(), kSoulRadius, kSoulZBand))
                        continue;
                    uint32 stacks = ScholoMalicia::SoulOf(player);
                    if (stacks)
                        if (auto const it = gained.find(player->GetGUID()); it != gained.end())
                            stacks += it->second;
                    if (!CanTakeSoul(stacks))
                        continue;
                    if (!taker || stacks < takerStacks
                        || (stacks == takerStacks && player->GetGUID() < taker->GetGUID()))
                    {
                        taker = player;
                        takerStacks = stacks;
                    }
                }
                if (taker)
                {
                    ++gained[taker->GetGUID()];
                    picked.emplace_back(taker->GetGUID(), soul);
                }
                else
                    kept.push_back(soul);
            }
            _souls = std::move(kept);

            for (auto& [guid, soul] : picked)
            {
                Remove(owner, soul, false);
                if (Player* taker = ObjectAccessor::GetPlayer(*owner, guid))
                {
                    uint32 const now = AddSoul(taker, 1);
                    if (onPick)
                        onPick(taker, now);
                }
            }
            for (Soul& soul : faded)
            {
                Remove(owner, soul, soul.spec.flyToOwner);
                if (onFade)
                    onFade(soul.at, soul.fromDrain);
            }
        }

        // MA6: the souls under a blast are gone (no Bound Soul, nothing spills). Returns how many.
        uint32 DestroyWithin(Creature* owner, Position const& center, float radius)
        {
            uint32 destroyed = 0;
            std::vector<Soul> kept;
            for (Soul& soul : _souls)
            {
                bool const under = soul.at.GetExactDist2d(center) <= radius
                    && std::fabs(soul.at.GetPositionZ() - center.GetPositionZ()) <= kSoulZBand;
                if (under)
                {
                    Remove(owner, soul, false);
                    ++destroyed;
                }
                else
                    kept.push_back(soul);
            }
            _souls = std::move(kept);
            return destroyed;
        }

        void Clear(Creature* owner)
        {
            std::vector<Soul> all = std::move(_souls);
            _souls.clear();
            _pollMs = 0;
            for (Soul& soul : all)
                Remove(owner, soul, false);
        }

        std::size_t Count() const
        {
            return _souls.size();
        }

        std::size_t FromDrain() const
        {
            return std::size_t(std::count_if(_souls.begin(), _souls.end(), [](Soul const& s) { return s.fromDrain; }));
        }

        std::vector<Vec2> Points() const
        {
            std::vector<Vec2> out;
            for (Soul const& s : _souls)
                out.push_back({ s.at.GetPositionX(), s.at.GetPositionY() });
            return out;
        }

    private:
        struct Soul
        {
            Position at;
            ObjectGuid unit;
            MechanicHandle soak;
            uint32 ageMs = 0;
            Spec spec;
            bool fromDrain = false;
        };

        // The Soak goes, and the wisp: faded, it flies to the owner first; picked up or destroyed, it is gone at once.
        void Remove(Creature* owner, Soul const& soul, bool fly)
        {
            if (owner && soul.soak)
                Mechanic::Cancel(owner, soul.soak);
            Map* map = owner ? owner->GetMap() : nullptr;
            Creature* unit = (map && soul.unit) ? map->GetCreature(soul.unit) : nullptr;
            if (!unit)
                return;
            if (fly && owner->IsAlive())
            {
                unit->GetMotionMaster()->MovePoint(1, owner->GetPosition(), FORCED_MOVEMENT_NONE, kSoulFlySpeed,
                    false);
                unit->DespawnOrUnsummon(Milliseconds(kSoulFlyMs));
            }
            else
                unit->DespawnOrUnsummon();
        }

        std::vector<Soul> _souls;
        uint32 _pollMs = 0;
    };

    // Scatters `count` floor points `minYd` to `maxYd` around `center`, `apartYd` apart when they fit (then any floor
    // point of the ring, then the room's nearest point).
    std::vector<Position> ScatterAround(WorldObject const* ref, Position const& center, uint32 count, float minYd,
        float maxYd, float apartYd)
    {
        std::vector<Position> out;
        std::vector<Vec2> taken;
        Vec2 const c{ center.GetPositionX(), center.GetPositionY() };
        for (uint32 i = 0; i < count; ++i)
        {
            std::optional<Vec2> p = PickRingPoint(c, minYd, maxYd, taken, apartYd, Rand01);
            if (!p)
                p = PickRingPoint(c, minYd, maxYd, {}, 0.f, Rand01);
            Vec2 const at = p ? *p : ClampToCovenFloor(DungeonKit::Advance(c, Rand01() * DungeonKit::kTwoPi, minYd));
            taken.push_back(at);
            out.push_back(FloorPoint(ref, at, center.GetPositionZ()));
        }
        return out;
    }

    // ---------------------------------------------------------------------------------------------------------------
    // The fight (her AI and her examiner's share it)
    // ---------------------------------------------------------------------------------------------------------------
    class MaliciaFight;

    // The AIs that own a MaliciaFight (her and her examiner): the shades and the registry callbacks find it here.
    struct MaliciaFightHost
    {
        virtual ~MaliciaFightHost() = default;
        virtual MaliciaFight& Fight() = 0;
    };

    MaliciaFight* FightOf(Map* map, ObjectGuid owner);

    class MaliciaFight
    {
    public:
        // The mechanics a pull runs (the examiner switches some off).
        struct Kit
        {
            bool drain = true;          // MA1-MA3, MA5
            bool call = true;           // MA4
            bool storm = true;          // MA6
            bool heal = true;           // MA7
            bool slow = true;           // MA8
            bool corruption = true;     // MA9
        };

        MaliciaFight(Creature* me, char const* logName) : _me(me), _logName(logName) { }

        bool Engaged() const { return _engaged; }
        bool Heroic() const { return _heroic; }

        void Begin(bool heroic, Kit const& kit, bool emotes)
        {
            End(false);
            _heroic = heroic;
            _kit = kit;
            _emotes = emotes;
            _engaged = true;
            _timeline = Timeline{};
            _timeline.Start(urand(kSlowFirstMinMs, kSlowFirstMaxMs),
                urand(kCorruptionFirstMinMs, kCorruptionFirstMaxMs));
            if (!_kit.drain)
                _timeline.Disable(Beat::Drain);
            if (!_kit.call)
                _timeline.Disable(Beat::Call);
            if (!_kit.storm)
                _timeline.Disable(Beat::Soulstorm);
            if (!_kit.slow)
                _timeline.Disable(Beat::Slow);
            if (!_kit.corruption)
                _timeline.Disable(Beat::Corruption);
            Describe();
            _souls.onPick = [this](Player* taker, uint32 now)
            {
                _lastSoul[taker->GetGUID()] = now;
                Log("soul-pick", Acore::StringFormat("player={} soul={}", taker->GetName(), now));
            };
            _souls.onFade = [this](Position const& /*at*/, bool fromDrain)
            {
                uint32 const bound = AddBound(kBoundPerSoul);
                Log("soul-fade", Acore::StringFormat("from={} bound={}", fromDrain ? "drain" : "shade", bound));
            };
            SoulBeat();
        }

        // The pull's state, gone: every mechanic, the souls, the shades, every Soul meter and her Bound Soul.
        void End(bool /*died*/)
        {
            for (MechanicHandle const& handle : _live)
                Mechanic::Cancel(_me, handle);
            _live.clear();
            _souls.Clear(_me);
            Map* map = _me->GetMap();
            for (ObjectGuid const& guid : _shades)
                if (Creature* shade = map->GetCreature(guid))
                    shade->DespawnOrUnsummon();
            _shades.clear();
            _drains.clear();
            _waves.clear();
            _falls.clear();
            // Only the meters this fight gave (a detention lesson's student keeps theirs); a player who left the map
            // lost theirs already (CHANGE_MAP interrupt flag).
            for (auto const& [guid, last] : _lastSoul)
                if (Player* player = ObjectAccessor::GetPlayer(map, guid))
                    ScholoMalicia::ClearSoul(player);
            _lastSoul.clear();
            _timeline = Timeline{};
            _beatMs = 0;
            _engaged = false;
            _me->RemoveAurasDueToSpell(SPELL_MA_BOUND_SOUL);
        }

        // Every tick, in or out of combat: the souls, the drains landing, the waves and the falling souls.
        void UpdateAlways(uint32 diff)
        {
            _clockMs += diff;
            _souls.Update(_me, diff);

            for (auto it = _drains.begin(); it != _drains.end();)
            {
                if (_clockMs < it->at)
                {
                    ++it;
                    continue;
                }
                PendingDrain const drain = *it;
                it = _drains.erase(it);
                ResolveDrain(drain);
            }
            for (auto it = _waves.begin(); it != _waves.end();)
            {
                if (_clockMs < *it)
                {
                    ++it;
                    continue;
                }
                it = _waves.erase(it);
                Wave();
            }
            for (auto it = _falls.begin(); it != _falls.end();)
            {
                if (_clockMs < it->at)
                {
                    ++it;
                    continue;
                }
                Position const to = it->to;
                it = _falls.erase(it);
                _me->CastSpell(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), SPELL_MA_SOULSTORM_FALL, true);
            }
        }

        // In combat, after the victim and arena gates.
        void Update(uint32 diff)
        {
            if (!_engaged)
                return;
            _timeline.Advance(diff);
            _beatMs += diff;
            if (_beatMs >= 1000)
            {
                _beatMs = 0;
                SoulBeat();
            }
            if (_kit.heal && !_timeline.Armed(Beat::ShadowHeal) && _me->HealthBelowPct(int32(kHealBelowPct)))
                _timeline.Arm(Beat::ShadowHeal);

            // Instant: not held by her casts.
            if (_timeline.Due(Beat::Call))
                CallAStudent();
            if (_timeline.Due(Beat::Slow))
                Slow();

            if (_me->HasUnitState(UNIT_STATE_CASTING))
                return;
            if (_timeline.Due(Beat::ShadowHeal))
                ShadowHeal();
            else if (_timeline.Due(Beat::Soulstorm))
                Soulstorm(false);
            else if (_timeline.Due(Beat::Drain))
                Drain(nullptr);
            else if (_timeline.Due(Beat::Corruption))
                Corruption();
        }

        // Her summons: the shades join the fight and the encounter (the interrupt and target lists name them); the
        // souls are looks only.
        void OnSummoned(Creature* summon)
        {
            if (!summon || summon->GetEntry() != NPC_SC_MALICIAS_SHADE)
                return;
            _shades.insert(summon->GetGUID());
            Mechanic::TrackUnit(_me, summon);
            if (_me->IsInCombat() && _me->IsAIEnabled)
                _me->AI()->DoZoneInCombat(summon);
        }

        // MA4: killed, a shade spills its 4 souls where it fell.
        void OnShadeDied(Creature* shade)
        {
            _shades.erase(shade->GetGUID());
            if (!_kit.drain && _engaged)
                return;
            for (Position const& at : ScatterAround(_me, shade->GetPosition(), kShadeSouls, 0.5f, kShadeSpillMaxYd,
                kSoulsApartYd))
                _souls.Spill(_me, at, false, SoulSpec());
            Log("shade-died", Acore::StringFormat("at=({:.1f}, {:.1f}) souls={}", shade->GetPositionX(),
                shade->GetPositionY(), kShadeSouls));
        }

        // MA4: alive 20 s, a shade walked into her: +4 Bound Soul.
        void OnShadeBound(Creature* shade)
        {
            _shades.erase(shade->GetGUID());
            uint32 const bound = AddBound(kBoundPerShade);
            _me->CastSpell(_me, SPELL_MA_SOUL_DRAIN, true);
            Log("shade-bound", Acore::StringFormat("bound={}", bound));
        }

        // MA6: a blast's hit destroys a Soul stack (in place of Weakened).
        void OnBlastHit(Unit* hit)
        {
            Player* player = hit ? hit->ToPlayer() : nullptr;
            if (!player)
                return;
            uint32 const before = ScholoMalicia::SoulOf(player);
            if (uint32 const loss = BlastLoss(before))
                _lastSoul[player->GetGUID()] = AddSoul(player, -int32(loss));
            Log("soulstorm-hit", Acore::StringFormat("player={} soul={}", player->GetName(),
                ScholoMalicia::SoulOf(player)));
        }

        // MA6: the burst shows on every marker, and the souls under it are gone.
        void OnBlastResolved(Position const& at)
        {
            _me->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_MA_SOULSTORM_BURST, true);
            if (uint32 const destroyed = _souls.DestroyWithin(_me, at, kStormRadius))
                Log("soulstorm-destroy", Acore::StringFormat("souls={}", destroyed));
        }

        // The players of her fight: alive, in the Coven arena (with its Z band). DoZoneInCombat engages the whole
        // instance, so combat alone would count a player shut outside the gate (R-B S5 SF-2).
        std::vector<Player*> FightPlayers() const
        {
            std::vector<Player*> out;
            Arena const room = MaliciaArena();
            for (auto const& ref : _me->GetMap()->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInWorld())
                    continue;
                if (!room.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                    continue;
                out.push_back(player);
            }
            return out;
        }

        // A threat-list pick never takes a player outside the Coven arena.
        void ExcludeOffArena(DungeonKit::PickRule& rule) const
        {
            Arena const room = MaliciaArena();
            for (auto const& ref : _me->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource();
                    player && !room.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                    rule.exclude.push_back(player->GetGUID().GetRawValue());
        }

        // ---- `.dbtest scholo malicia` entry points ------------------------------------------------------------------

        void TestPrepare(Optional<bool> heroic = {})
        {
            if (!_engaged)
                _heroic = heroic ? *heroic : HeroicValues(_me);
        }

        void TestSoul(Player* player, uint32 stacks)
        {
            uint32 const now = SetSoul(player, std::clamp(stacks, kSoulFloor, kSoulCap));
            _lastSoul[player->GetGUID()] = now;
        }

        bool TestDrain(Player* target)
        {
            TestPrepare();
            return Drain(target);
        }

        void TestCall()
        {
            TestPrepare();
            CallAStudent();
        }

        void TestStorm(bool heroic)
        {
            TestPrepare(heroic);
            Soulstorm(true);
        }

        void TestHeal()
        {
            TestPrepare();
            ShadowHeal();
        }

        uint32 TestBound(uint32 stacks)
        {
            uint32 const current = DungeonKit::Stacks(_me, SPELL_MA_BOUND_SOUL);
            return DungeonKit::AddStacks(_me, SPELL_MA_BOUND_SOUL, int32(std::min(stacks, kBoundCap)) - int32(current),
                _me, kBoundCap);
        }

        std::string TestState() const
        {
            std::string out = Acore::StringFormat("engaged={} heroic={} t={}ms next drain/call/storm/heal/slow/corr="
                "{}/{}/{}/{}/{}/{} bound={} souls={} (drain {}) shades={}", _engaged ? 1 : 0, _heroic ? 1 : 0,
                _timeline.now, Next(Beat::Drain), Next(Beat::Call), Next(Beat::Soulstorm), Next(Beat::ShadowHeal),
                Next(Beat::Slow), Next(Beat::Corruption), DungeonKit::Stacks(_me, SPELL_MA_BOUND_SOUL), _souls.Count(),
                _souls.FromDrain(), _shades.size());
            for (Player* p : FightPlayers())
                out += Acore::StringFormat("\n  {}: soul {} ({:+}%)", p->GetName(), ScholoMalicia::SoulOf(p),
                    SoulModPct(ScholoMalicia::SoulOf(p)));
            return out;
        }

    private:
        struct PendingDrain
        {
            uint32 at = 0;
            std::vector<ObjectGuid> targets;
        };

        struct PendingFall
        {
            uint32 at = 0;
            Position to;
        };

        std::string Next(Beat b) const
        {
            uint32 const in = _timeline.In(b);
            return in == kNever ? std::string("-") : std::to_string(in);
        }

        void Log(char const* mechanic, std::string const& detail = {}) const
        {
            DungeonKit::LogMechanic(kLogDungeon, _logName, mechanic, detail);
        }

        void Talk(uint8 group, WorldObject const* target = nullptr)
        {
            if (_emotes && _me->IsAIEnabled && _me->AI())
                _me->AI()->Talk(group, target);
        }

        void Track(MechanicHandle handle)
        {
            if (handle)
                _live.push_back(handle);
        }

        SoulField::Spec SoulSpec() const
        {
            SoulField::Spec spec;
            spec.fadeMs = kSoulFadeMs(_heroic);
            // Bots: never the tank (SC Bots: "the tank never leaves her for a soul"); lowest Soul first, nobody at the
            // cap (the Soak's Order). A human tank may still walk through one.
            spec.botsWho.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
            spec.botsWho.auraSpell = SPELL_MA_SOUL;
            spec.botsWho.minStacks = 1;
            spec.botsWho.maxStacks = uint8(kSoulCap - 1);
            spec.flyToOwner = true;
            return spec;
        }

        // Boss data (build spec): her shades above her; kick Shadow Heal first, then the shades' Volley; never spend a
        // kick on Corruption; dispel Slow, then Corruption (Magic).
        void Describe()
        {
            BossMechanics::Descriptor d;
            d.targets.emplace_back(NPC_SC_MALICIAS_SHADE, 1);
            d.targets.emplace_back(_me->GetEntry(), 0);
            if (_kit.heal)
                d.interrupts.emplace_back(_me->GetEntry(), SPELL_MA_SHADOW_HEAL, 3, Milliseconds(kHealEveryMs));
            if (_kit.call)
                d.interrupts.emplace_back(NPC_SC_MALICIAS_SHADE, SPELL_MA_SHADE_VOLLEY, 2,
                    Milliseconds(kShadeVolleyEveryMs));
            if (_kit.corruption)
            {
                d.interrupts.emplace_back(_me->GetEntry(), SPELL_MA_CORRUPTION, 0);
                d.dispels.emplace_back(SPELL_MA_CORRUPTION, 1);
            }
            if (_kit.slow)
                d.dispels.emplace_back(SPELL_MA_SLOW, 2);
            Mechanic::Describe(_me, std::move(d));
        }

        // MA1: every fight player has a meter: 20 the first time, else the count they had (a death removes it).
        void SoulBeat()
        {
            if (!_kit.drain)
                return;
            for (Player* player : FightPlayers())
            {
                uint32 const current = ScholoMalicia::SoulOf(player);
                if (current)
                {
                    _lastSoul[player->GetGUID()] = current;
                    continue;
                }
                auto it = _lastSoul.find(player->GetGUID());
                uint32 const give = it != _lastSoul.end() ? it->second : kSoulStart;
                _lastSoul[player->GetGUID()] = SetSoul(player, give);
            }
        }

        uint32 AddBound(uint32 add)
        {
            uint32 const current = DungeonKit::Stacks(_me, SPELL_MA_BOUND_SOUL);
            uint32 const want = BoundAfter(current, add);
            return DungeonKit::AddStacks(_me, SPELL_MA_BOUND_SOUL, int32(want) - int32(current), _me, kBoundCap);
        }

        // ---- MA2 Soul Drain -----------------------------------------------------------------------------------------

        // False when nobody qualified. `forced`: that player (a test).
        bool Drain(Player* forced)
        {
            std::vector<Player*> targets;
            bool const all = _heroic && !forced;
            if (forced)
                targets.push_back(forced);
            else if (all)
                targets = FightPlayers();
            else
            {
                DungeonKit::PickRule rule;
                rule.nonTank = true;
                rule.tankIfAlone = false;       // never the tank on normal (SC MA2)
                ExcludeOffArena(rule);
                targets = DungeonKit::PickPlayers(_me, rule, NormalDrainTargets(_me->GetHealthPct()));
            }
            if (targets.empty())
            {
                _timeline.Retry(Beat::Drain);
                return false;
            }
            // The bar first: a refused bar (a school lockout, a silence) drains nobody and tries again shortly.
            if (_me->CastSpell(all ? static_cast<Unit*>(_me) : targets.front(), SPELL_MA_SOUL_DRAIN_CAST, false)
                != SPELL_CAST_OK)
            {
                _timeline.Retry(Beat::Drain, kCastRetryMs);
                Log("soul-drain-refused");
                return false;
            }
            _timeline.Done(Beat::Drain, kDrainEveryMs(_heroic));
            if (all)
                Talk(EMOTE_MALICIA_DRAIN_ALL);
            else
                for (Player* target : targets)
                    Talk(EMOTE_MALICIA_SOUL_DRAIN, target);
            PendingDrain drain;
            drain.at = _clockMs + kDrainCastMs;
            std::string names;
            for (Player* target : targets)
            {
                if (!ScholoMalicia::SoulOf(target))
                    _lastSoul[target->GetGUID()] = SetSoul(target, kSoulStart);    // a test target with no meter yet
                drain.targets.push_back(target->GetGUID());
                names += (names.empty() ? "" : ",") + target->GetName();
            }
            _drains.push_back(std::move(drain));
            Log("soul-drain", Acore::StringFormat("targets={} heroic={}", names, _heroic ? 1 : 0));
            return true;
        }

        // The cast ended (on the AI's clock): each target loses up to 4 stacks, and that many souls land around them.
        void ResolveDrain(PendingDrain const& drain)
        {
            SoulField::Spec const spec = SoulSpec();
            for (ObjectGuid const& guid : drain.targets)
            {
                Player* player = ObjectAccessor::GetPlayer(*_me, guid);
                if (!player || !player->IsAlive())
                    continue;
                uint32 const loss = DrainLoss(ScholoMalicia::SoulOf(player));
                _me->CastSpell(player, SPELL_MA_SOUL_DRAIN, true);
                if (!loss)
                    continue;
                _lastSoul[player->GetGUID()] = AddSoul(player, -int32(loss));
                for (Position const& at : ScatterAround(_me, player->GetPosition(), loss, kSoulSpillMinYd,
                    kSoulSpillMaxYd, kSoulsApartYd))
                    _souls.Spill(_me, at, true, spec);
                Log("soul-drain-lands", Acore::StringFormat("player={} lost={} soul={}", player->GetName(), loss,
                    ScholoMalicia::SoulOf(player)));
            }
        }

        // ---- MA4 Call a Student -------------------------------------------------------------------------------------

        void CallAStudent()
        {
            _timeline.Done(Beat::Call, kCallEveryMs);
            Vec2 const her = DungeonKit::PlaneOf(_me);
            std::vector<Vec2> picked;
            for (uint32 i = 0; i < kShadeCount(_heroic); ++i)
            {
                std::optional<Vec2> p = PickRingPoint(her, kShadeMinYd, kShadeMaxYd, picked, kShadeApartYd, Rand01);
                if (!p)
                    p = PickRingPoint(her, kShadeMinYd, kShadeMaxYd, {}, 0.f, Rand01);
                // Nothing on the ring landed on the floor: the measured rise band (x 102-112, the room's width).
                Vec2 const at = p ? *p : Vec2{ frand(kCovenShadeMinX, kCovenShadeMaxX), frand(-8.f, 6.f) };
                picked.push_back(at);
                Position const spot = FloorPoint(_me, at, _me->GetPositionZ(), DungeonKit::BearingTo(at, her));
                _me->SummonCreature(NPC_SC_MALICIAS_SHADE, spot, TEMPSUMMON_CORPSE_TIMED_DESPAWN, 5000);
            }
            Talk(EMOTE_MALICIA_CALL_A_STUDENT);
            Log("call-a-student", Acore::StringFormat("shades={} heroic={}", picked.size(), _heroic ? 1 : 0));
        }

        // ---- MA6 Soulstorm ------------------------------------------------------------------------------------------

        // `forced`: now, whatever the floor holds (a test).
        bool Soulstorm(bool forced)
        {
            if (!forced && !StormMayStart(_heroic, _souls.FromDrain()))
            {
                _timeline.Retry(Beat::Soulstorm, kStormWaitRetryMs);
                return false;
            }
            // The bar first: the waves land inside it, so a refused bar (a lockout, a silence) storms nothing yet.
            if (_me->CastSpell(_me, SPELL_MA_SOULSTORM_CAST, false) != SPELL_CAST_OK)
            {
                _timeline.Retry(Beat::Soulstorm, kCastRetryMs);
                Log("soulstorm-refused");
                return false;
            }
            _timeline.Done(Beat::Soulstorm, kStormEveryMs);
            Talk(EMOTE_MALICIA_SOULSTORM);
            for (uint32 k = 0; k < kStormWaves; ++k)
                _waves.push_back(_clockMs + k * kStormWaveGapMs);
            Log("soulstorm", Acore::StringFormat("heroic={}", _heroic ? 1 : 0));
            return true;
        }

        void Wave()
        {
            std::vector<Player*> const players = FightPlayers();
            std::vector<Player*> marked;
            if (_heroic)
                marked = players;
            else
            {
                DungeonKit::PickRule rule;
                rule.nonTank = true;
                rule.tankIfAlone = true;        // a solo tank (a test) is still marked
                ExcludeOffArena(rule);
                if (Player* p = DungeonKit::PickPlayer(_me, rule))
                    marked.push_back(p);
                else if (!players.empty())
                    marked.push_back(players[urand(0, uint32(players.size()) - 1)]);    // out of combat (a test)
            }
            std::vector<Vec2> avoid;
            for (Player* p : players)
                avoid.push_back(DungeonKit::PlaneOf(p));

            uint32 markers = 0;
            for (Player* p : marked)
            {
                Vec2 const c = OffsetMarker(DungeonKit::PlaneOf(p), Rand01() * DungeonKit::kTwoPi);
                RegisterBlast(FloorPoint(_me, c, p->GetPositionZ()));
                ++markers;
            }
            for (uint32 i = 0; i < kStormRandomSpots(_heroic); ++i)
                if (std::optional<Vec2> spot = PickRoomPoint(avoid, kStormSpotMinFromPlayerYd, Rand01))
                {
                    RegisterBlast(FloorPoint(_me, *spot, _me->GetPositionZ()));
                    ++markers;
                }
            Log("soulstorm-wave", Acore::StringFormat("markers={} players={}", markers, marked.size()));
        }

        void RegisterBlast(Position const& at)
        {
            Map* map = _me->GetMap();
            ObjectGuid const owner = _me->GetGUID();
            MechanicRef ref = Mechanic::Circle(_me, at, kStormRadius, Milliseconds(kStormWarnMs));
            float const pct = kStormPct(_heroic) * BoundDamageScale(DungeonKit::Stacks(_me, SPELL_MA_BOUND_SOUL));
            ref.Damage(pct).Spell(SPELL_MA_SOULSTORM_BLAST).Tag(TAG_SOULSTORM)
                .OnHit([map, owner](Unit* hit)
                {
                    if (MaliciaFight* fight = FightOf(map, owner))
                        fight->OnBlastHit(hit);
                })
                .OnResolve([map, owner, at](BossMechanics::ResolveResult const& /*result*/)
                {
                    if (MaliciaFight* fight = FightOf(map, owner))
                        fight->OnBlastResolved(at);
                });
            Track(ref.Handle());
            _falls.push_back({ _clockMs + FallLaunchDelayMs(_me->GetExactDist2d(at)), at });
        }

        // ---- MA7 / MA8 / MA9 ----------------------------------------------------------------------------------------

        void ShadowHeal()
        {
            SpellCastResult const result = _me->CastSpell(_me, SPELL_MA_SHADOW_HEAL, false);
            if (result != SPELL_CAST_OK)
            {
                _timeline.Retry(Beat::ShadowHeal, kCastRetryMs);    // a kick's school lockout: try again shortly
                return;
            }
            _timeline.Done(Beat::ShadowHeal, kHealEveryMs);
            Mechanic::NoteNextCastIn(_me, SPELL_MA_SHADOW_HEAL, Milliseconds(kHealEveryMs));
            Log("shadow-heal", Acore::StringFormat("health={:.0f}% heroic={}", _me->GetHealthPct(), _heroic ? 1 : 0));
        }

        bool AnyPlayerWithin(float yd) const
        {
            for (Player* p : FightPlayers())
                if (_me->GetExactDist2d(p) <= yd)
                    return true;
            return false;
        }

        void Slow()
        {
            if (!AnyPlayerWithin(kSlowRadius))
            {
                _timeline.Retry(Beat::Slow);
                return;
            }
            _me->CastSpell(_me, SPELL_MA_SLOW, true);
            _timeline.Done(Beat::Slow, urand(kSlowEveryMinMs, kSlowEveryMaxMs));
            Log("slow");
        }

        void Corruption()
        {
            if (!AnyPlayerWithin(kCorruptionRadius))
            {
                _timeline.Retry(Beat::Corruption);
                return;
            }
            if (_me->CastSpell(_me, SPELL_MA_CORRUPTION, false) != SPELL_CAST_OK)
            {
                _timeline.Retry(Beat::Corruption, kCastRetryMs);    // a Shadow lockout: try again shortly
                return;
            }
            _timeline.Done(Beat::Corruption, urand(kCorruptionEveryMinMs, kCorruptionEveryMaxMs));
            Log("corruption");
        }

        Creature* _me;
        char const* _logName;
        Timeline _timeline;
        Kit _kit;
        SoulField _souls;
        GuidSet _shades;
        std::vector<MechanicHandle> _live;
        std::vector<PendingDrain> _drains;
        std::vector<uint32> _waves;
        std::vector<PendingFall> _falls;
        std::unordered_map<ObjectGuid, uint32> _lastSoul;
        uint32 _clockMs = 0;            // never held: drains, waves and falls (out of combat too)
        uint32 _beatMs = 0;
        bool _heroic = false;
        bool _emotes = true;
        bool _engaged = false;
    };

    MaliciaFight* FightOf(Map* map, ObjectGuid owner)
    {
        Creature* creature = map ? map->GetCreature(owner) : nullptr;
        if (!creature || !creature->IsAIEnabled)
            return nullptr;
        auto* host = dynamic_cast<MaliciaFightHost*>(creature->AI());
        return host ? &host->Fight() : nullptr;
    }
}

// Instructor Malicia 10505
struct boss_instructor_malicia_rework : public BossAI, public MaliciaFightHost
{
    explicit boss_instructor_malicia_rework(Creature* creature)
        : BossAI(creature, BOSS_MALICIA), _fight(creature, kBossLogName),
        _arena(MaliciaArena(), LeashOptions(kBossLogName)) { }

    MaliciaFight& Fight() override
    {
        return _fight;
    }

    void Reset() override
    {
        _Reset();
        _fight.End(false);
        _arena.Reset();
        _grades.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);       // DoZoneInCombat, BOSS_MALICIA IN_PROGRESS (the Coven's gate shuts)
        if (!me->IsEngaged())
            return;     // BossAI evaded

        bool const heroic = DungeonKit::IsHeroicMap(me);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_MALICIA;
        Mechanic::BeginEncounter(me, options);
        _grades.Begin(me, Instructor::Malicia);
        _arena.Engage(me);
        _fight.Begin(heroic, MaliciaFight::Kit{}, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} health={} at=({:.1f}, {:.1f}, {:.1f})", heroic ? 1 : 0, me->GetMaxHealth(),
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "evade", Acore::StringFormat("reason={}", uint32(why)));
        _fight.End(false);
        _arena.Reset();
        _grades.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        _grades.AwardAtDeath(me);
        _fight.End(true);
        BossAI::JustDied(killer);
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death");
    }

    // Her summons: the shades join the fight (MaliciaFight::OnSummoned zones them in); the souls are looks.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
        _fight.OnSummoned(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.dbtest scholo malicia` drain, storm or souls.
        _fight.UpdateAlways(diff);

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off her arena, or nobody on it for 10 s: evading

        _fight.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    MaliciaFight _fight;
    DungeonKit::ArenaGuard _arena;
    GradeWatch _grades;
};

// Graduate Examiner: Malicia 300548 (S13 declares the entry): her fight at heroic values, no boss state, no grades.
struct npc_sc_examiner_malicia : public ScriptedAI, public MaliciaFightHost
{
    explicit npc_sc_examiner_malicia(Creature* creature)
        : ScriptedAI(creature), _fight(creature, kExaminerLogName),
        _arena(MaliciaArena(), LeashOptions(kExaminerLogName)) { }

    MaliciaFight& Fight() override
    {
        return _fight;
    }

    bool Configure(ExaminerOptions options)
    {
        if (me->IsInCombat())
            return false;
        _options = std::move(options);
        ApplyLook();
        return true;
    }

    void Reset() override
    {
        _fight.End(false);
        _arena.Reset();
        ApplyLook();
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        Mechanic::BeginEncounter(me);
        _arena.Engage(me);
        MaliciaFight::Kit kit;
        kit.drain = _options.soulDrain;
        kit.call = _options.callAStudent;
        kit.storm = _options.soulstorm;
        kit.heal = _options.shadowHeal;
        kit.slow = _options.slow;
        kit.corruption = _options.corruption;
        _fight.Begin(true, kit, false);
        DungeonKit::LogMechanic(kLogDungeon, kExaminerLogName, "engage",
            Acore::StringFormat("health={} drain={} call={} storm={}", me->GetMaxHealth(), kit.drain ? 1 : 0,
                kit.call ? 1 : 0, kit.storm ? 1 : 0));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _fight.End(false);
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _fight.End(true);
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kExaminerLogName, "death");
        if (_options.onDeath)
            _options.onDeath(me);
    }

    void JustSummoned(Creature* summon) override
    {
        _fight.OnSummoned(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        _fight.UpdateAlways(diff);
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;
        _fight.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    // The examiner's health (the same base and modifier path as Creature::SelectLevel) and the ghost tint.
    void ApplyLook()
    {
        if (_options.health && !me->IsInCombat())
        {
            me->SetCreateHealth(_options.health);
            me->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, float(_options.health));
            me->UpdateMaxHealth();
            me->SetHealth(me->GetMaxHealth());
        }
        if (_options.ghostTint && !me->HasAura(SPELL_EXAMINER_GHOST_VISUAL))
            me->AddAura(SPELL_EXAMINER_GHOST_VISUAL, me);
        else if (!_options.ghostTint)
            me->RemoveAurasDueToSpell(SPELL_EXAMINER_GHOST_VISUAL);
    }

    MaliciaFight _fight;
    DungeonKit::ArenaGuard _arena;
    ExaminerOptions _options;
};

bool ScholoMalicia::ConfigureExaminer(Creature* examiner, ExaminerOptions options)
{
    auto* ai = (examiner && examiner->IsAIEnabled) ? dynamic_cast<npc_sc_examiner_malicia*>(examiner->AI()) : nullptr;
    return ai && ai->Configure(std::move(options));
}

// Malicia's Shade 300536 (MA4): stands where it rose and casts the Volley (a kickable 2 s cast that triggers the stock
// 17228); after 20 s alive it walks into her and she binds it (+4 Bound Soul); killed, it spills 4 souls. Its timers
// are its own (a cast bar holds only its own Volley).
struct npc_sc_malicias_shade : public ScriptedAI
{
    explicit npc_sc_malicias_shade(Creature* creature) : ScriptedAI(creature)
    {
        me->SetCombatMovement(false);
    }

    void IsSummonedBy(WorldObject* summoner) override
    {
        if (summoner)
            _host = summoner->GetGUID();
    }

    // A reset (an evade) never restarts its 20 s.
    void Reset() override
    {
        _volleyMs = kShadeVolleyFirstMs;
    }

    // While her fight runs the shade stays (it walks in or dies); without it, it is gone.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (MaliciaFight* fight = FightOf(me->GetMap(), _host); fight && fight->Engaged())
            return;
        if (_host)
        {
            me->DespawnOrUnsummon();
            return;
        }
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        if (MaliciaFight* fight = FightOf(me->GetMap(), _host))
            fight->OnShadeDied(me);
    }

    void UpdateAI(uint32 diff) override
    {
        _aliveMs += diff;
        if (_walking)
        {
            WalkIn(diff);
            return;
        }
        if (_aliveMs >= kShadeWalkInMs && _host)
        {
            StartWalk();
            return;
        }
        if (!UpdateVictim())
            return;
        _volleyMs = _volleyMs > diff ? _volleyMs - diff : 0;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (!_volleyMs)
        {
            DoCastSelf(SPELL_MA_SHADE_VOLLEY);
            _volleyMs = kShadeVolleyEveryMs;
        }
        DoMeleeAttackIfReady();
    }

private:
    Creature* Host() const
    {
        return _host ? me->GetMap()->GetCreature(_host) : nullptr;
    }

    void StartWalk()
    {
        _walking = true;
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->SetWalk(true);
        Repath();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shade-walks-in");
    }

    void WalkIn(uint32 diff)
    {
        Creature* her = Host();
        if (!her || !her->IsAlive())
        {
            me->DespawnOrUnsummon();
            return;
        }
        if (me->GetExactDist2d(her) <= kShadeBindYd)
        {
            if (MaliciaFight* fight = FightOf(me->GetMap(), _host))
                fight->OnShadeBound(me);
            _walking = false;
            _host.Clear();      // bound: its despawn is no death
            me->DespawnOrUnsummon();
            return;
        }
        _repathMs += diff;
        if (_repathMs >= kShadeRepathMs)
            Repath();
    }

    void Repath()
    {
        _repathMs = 0;
        if (Creature* her = Host())
            me->GetMotionMaster()->MovePoint(1, her->GetPosition(), FORCED_MOVEMENT_WALK);
    }

    ObjectGuid _host;
    uint32 _aliveMs = 0;
    uint32 _volleyMs = kShadeVolleyFirstMs;
    uint32 _repathMs = 0;
    bool _walking = false;
};

namespace
{
    // ---------------------------------------------------------------------------------------------------------------
    // Detention: the Coven (SC 2965, handoff section 3.7). Drained on landing: 3 / 4 souls spill 3 to 6 yd around the
    // student (around the apse's mouth when they landed in her apse) and fade from 10 / 6 s on, one every 1.75 s (user
    // ruling 4: one hit per miss, never two at once); every soul picked up passes, each fade is a failure (the
    // lesson's failure hit, 15% / 25% and Weakened, through Soul Lost 206217, at the lesson's own heroic flag). With or
    // without her: the lesson's stalker owns the souls and their Soaks (only the student may take them). The meter is
    // the lesson's own: it goes when the lesson ends.
    // ---------------------------------------------------------------------------------------------------------------
    class CovenLesson : public TimedSoloLesson
    {
    public:
        CovenLesson() : TimedSoloLesson(Classroom::Coven) { }

    protected:
        void OnStart(Creature* owner, Player* student, bool heroic) override
        {
            ObjectGuid const studentGuid = student->GetGUID();
            _souls.onPick = [](Player* taker, uint32 now)
            {
                DungeonKit::LogMechanic(kLogDungeon, kLessonLogName, "soul-pick",
                    Acore::StringFormat("player={} soul={}", taker->GetName(), now));
            };
            _souls.onFade = [this](Position const& /*at*/, bool /*fromDrain*/)
            {
                FailStudent();
                Creature* stalker = Owner();
                Player* who = Student();
                if (stalker && who && who->IsAlive())
                    stalker->CastCustomSpell(SPELL_MA_SOUL_LOST, SPELLVALUE_BASE_POINT0, SoulLostBasePoints(Heroic()),
                        who, true);
                DungeonKit::LogMechanic(kLogDungeon, kLessonLogName, "soul-fade",
                    Acore::StringFormat("student={}", who ? who->GetName() : std::string("?")));
            };

            if (!ScholoMalicia::SoulOf(student))
                SetSoul(student, kSoulStart);
            uint32 const loss = DrainLoss(ScholoMalicia::SoulOf(student), kLessonSouls(heroic));
            owner->CastSpell(student, SPELL_MA_SOUL_DRAIN, true);
            AddSoul(student, -int32(loss));

            SoulField::Spec spec;
            spec.botsWho.carriers.insert(studentGuid);
            spec.botsWho.auraSpell = SPELL_MA_SOUL;
            spec.botsWho.minStacks = 1;
            spec.botsWho.maxStacks = uint8(kSoulCap - 1);
            spec.takers.insert(studentGuid);
            spec.flyToOwner = false;
            Vec2 const center = LessonSpillCenter(DungeonKit::PlaneOf(student));
            Position const around(center.x, center.y, student->GetPositionZ(), 0.f);
            uint32 index = 0;
            for (Position const& at : ScatterAround(owner, around, loss, kLessonSpillMinYd, kLessonSpillMaxYd,
                kLessonSoulsApartYd))
            {
                // Ruling 4: the fades (and so the misses) come one at a time, kLessonFadeStaggerMs apart.
                spec.fadeMs = LessonSoulFadeMs(heroic, index++);
                _souls.Spill(owner, at, true, spec);
            }
            DungeonKit::LogMechanic(kLogDungeon, kLessonLogName, "start",
                Acore::StringFormat("student={} souls={} fade={}ms heroic={}", student->GetName(), loss, spec.fadeMs,
                    heroic ? 1 : 0));
        }

        void OnUpdate(uint32 diff, Creature* owner, Player* /*student*/) override
        {
            _souls.Update(owner, diff);
        }

        void OnEnd(LessonEnd /*why*/, Creature* owner) override
        {
            _souls.Clear(owner);
            ScholoMalicia::ClearSoul(Student());
        }

    private:
        SoulField _souls;
    };

    // `.dbtest scholo malicia lesson`: a stand-in stalker runs the Coven lesson on one student (S11 owns the real
    // stalker 300546 and the detention cycle).
    struct npc_sc_malicia_lesson_host : public NullCreatureAI
    {
        npc_sc_malicia_lesson_host(Creature* creature, ObjectGuid student, bool heroic)
            : NullCreatureAI(creature), _student(student), _heroic(heroic) { }

        void UpdateAI(uint32 diff) override
        {
            if (!_started)
            {
                _started = true;
                Player* student = ObjectAccessor::GetPlayer(*me, _student);
                if (!student)
                {
                    me->DespawnOrUnsummon();
                    return;
                }
                _lesson.Start(me, student, _heroic);
            }
            _lesson.Update(diff);
            if (_lesson.Done() && !_reported)
            {
                _reported = true;
                DungeonKit::LogMechanic(kLogDungeon, kLessonLogName, "verdict",
                    Acore::StringFormat("passed={} failed={} failures={}", _lesson.Passed() ? 1 : 0,
                        _lesson.Failed() ? 1 : 0, _lesson.Clock().Failures()));
                me->DespawnOrUnsummon(1s);
            }
        }

    private:
        CovenLesson _lesson;
        ObjectGuid _student;
        bool _heroic = false;
        bool _started = false;
        bool _reported = false;
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// Spell and aura scripts
// ---------------------------------------------------------------------------------------------------------------------

// MA1 Soul 206205: the meter; its hidden weight goes with it.
class spell_scholo_malicia_soul : public AuraScript
{
    PrepareAuraScript(spell_scholo_malicia_soul);

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(SPELL_MA_SOUL_WEIGHT);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_scholo_malicia_soul::HandleRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// MA1 Soul 206206, the weight: damage done, healing done and max health, each (stacks - 20) x 5% of the owner's meter
// (one stack of its own, so the engine's stack multiply leaves the amount alone). Recalculated on every meter change.
class spell_scholo_malicia_soul_weight : public AuraScript
{
    PrepareAuraScript(spell_scholo_malicia_soul_weight);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        Unit* owner = GetUnitOwner();
        amount = owner ? SoulModPct(DungeonKit::Stacks(owner, SPELL_MA_SOUL)) : 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_scholo_malicia_soul_weight::CalcAmount, EFFECT_ALL,
            SPELL_AURA_ANY);
    }
};

// MA7 Shadow Heal 206215: heals her 5% / 10% of her max health (set at launch; ignores caster modifiers); its second
// effect triggers the nova.
class spell_scholo_malicia_shadow_heal : public SpellScript
{
    PrepareSpellScript(spell_scholo_malicia_shadow_heal);

    void SetHeal(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetCaster())
            SetEffectValue(static_cast<int32>(caster->CountPctFromMaxHealth(kHealSelfPct(HeroicValues(caster)))));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_scholo_malicia_shadow_heal::SetHeal, EFFECT_0, SPELL_EFFECT_HEAL);
    }
};

// MA7 Shadow Nova 206216: 15% / 40% of the reference row on every player (RefFlat at launch, so defensives count),
// raised by her Bound Soul like her melee (BoundDamageScale).
class spell_scholo_malicia_shadow_nova : public SpellScript
{
    PrepareSpellScript(spell_scholo_malicia_shadow_nova);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetCaster())
            SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(),
                kHealBurstPct(HeroicValues(caster)) * BoundDamageScale(DungeonKit::Stacks(caster,
                    SPELL_MA_BOUND_SOUL)))));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_scholo_malicia_shadow_nova::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// Detention, Soul Lost 206217: a soul faded in the Coven's lesson: the lesson's failure hit, 15% / 25% of the
// reference row (RefFlat at launch) and one Weakened stack (ruling 21; SoloLesson.h LessonFailurePct). The lesson
// passes its percent in base point 0 (SoulLostBasePoints, its own heroic flag); a plain cast falls back to the map's.
class spell_scholo_malicia_soul_lost : public SpellScript
{
    PrepareSpellScript(spell_scholo_malicia_soul_lost);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        SpellValue const* value = GetSpellValue();
        float pct = value ? SoulLostPctFromBasePoints(value->EffectBasePoints[EFFECT_0]) : 0.f;
        if (pct <= 0.f)
            pct = LessonFailurePct(DungeonKit::IsHeroicMap(caster));
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void AddWeakened()
    {
        if (Player* player = GetHitUnit() ? GetHitUnit()->ToPlayer() : nullptr)
            BossMechanics::Weakened::AddStack(player);
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_scholo_malicia_soul_lost::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterHit += SpellHitFn(spell_scholo_malicia_soul_lost::AddWeakened);
    }
};

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest scholo malicia`
// ---------------------------------------------------------------------------------------------------------------------

namespace
{
    MaliciaFight* FindFight(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_MALICIA);
        if (!boss)
            return nullptr;
        auto* host = boss->IsAIEnabled ? dynamic_cast<MaliciaFightHost*>(boss->AI()) : nullptr;
        if (!host)
        {
            handler->SendErrorMessage("{}",
                "Malicia is not running boss_instructor_malicia_rework (check the ScriptName).");
            return nullptr;
        }
        return &host->Fight();
    }

    Creature* FindMalicia(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_MALICIA);
        return (boss && boss->IsAIEnabled && dynamic_cast<MaliciaFightHost*>(boss->AI())) ? boss : nullptr;
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
        return ScholoTest::ShowBossInfo(handler, NPC_MALICIA, BOSS_MALICIA);
    }

    // `.dbtest scholo malicia state`: the clock, her Bound Soul, the souls and shades, every fight player's Soul.
    bool HandleState(ChatHandler* handler)
    {
        MaliciaFight* fight = FindFight(handler);
        if (!fight)
            return false;
        handler->PSendSysMessage("Malicia: {}", fight->TestState());
        return true;
    }

    // `.dbtest scholo malicia soul <n>`: sets the selected player's (or your) Soul meter, 10 to 40 (MA1).
    bool HandleSoul(ChatHandler* handler, uint32 stacks)
    {
        MaliciaFight* fight = FindFight(handler);
        Player* target = TestTarget(handler);
        if (!fight || !target)
            return false;
        fight->TestSoul(target, stacks);
        handler->PSendSysMessage("Malicia: {} has {} Soul ({:+}%).", target->GetName(), ScholoMalicia::SoulOf(target),
            SoulModPct(ScholoMalicia::SoulOf(target)));
        return true;
    }

    // `.dbtest scholo malicia drain`: Soul Drain on the selected player (or you); the souls land 2 s later (MA2, MA3).
    bool HandleDrain(ChatHandler* handler)
    {
        MaliciaFight* fight = FindFight(handler);
        Creature* boss = FindMalicia(handler);
        Player* target = TestTarget(handler);
        if (!fight || !boss || !target)
            return false;
        if (boss->HasUnitState(UNIT_STATE_CASTING))
        {
            handler->SendErrorMessage("{}", "Malicia is casting; try again in a moment.");
            return false;
        }
        fight->TestDrain(target);
        handler->PSendSysMessage("Malicia: Soul Drain on {} (MA2).", target->GetName());
        return true;
    }

    // `.dbtest scholo malicia shade`: Call a Student now (1 shade normal, 2 heroic; MA4).
    bool HandleShade(ChatHandler* handler)
    {
        MaliciaFight* fight = FindFight(handler);
        if (!fight)
            return false;
        fight->TestCall();
        handler->PSendSysMessage("{}", "Malicia: Call a Student (MA4).");
        return true;
    }

    // `.dbtest scholo malicia storm [0|1]`: Soulstorm now; 1 = the heroic waves (every player + 1 spot), 0 = normal;
    // default the map's (MA6). Players in GM mode are not marked.
    bool HandleStorm(ChatHandler* handler, Optional<uint32> heroic)
    {
        MaliciaFight* fight = FindFight(handler);
        Creature* boss = FindMalicia(handler);
        if (!fight || !boss)
            return false;
        if (boss->HasUnitState(UNIT_STATE_CASTING))
        {
            handler->SendErrorMessage("{}", "Malicia is casting; try again in a moment.");
            return false;
        }
        bool const isHeroic = heroic ? *heroic != 0 : DungeonKit::IsHeroicMap(boss);
        fight->TestStorm(isHeroic);
        handler->PSendSysMessage("Malicia: Soulstorm ({}) (MA6).", isHeroic ? "heroic" : "normal");
        return true;
    }

    // `.dbtest scholo malicia heal`: Shadow Heal now (kick it to test the interrupt; MA7).
    bool HandleHeal(ChatHandler* handler)
    {
        MaliciaFight* fight = FindFight(handler);
        Creature* boss = FindMalicia(handler);
        if (!fight || !boss)
            return false;
        if (boss->HasUnitState(UNIT_STATE_CASTING))
        {
            handler->SendErrorMessage("{}", "Malicia is casting; try again in a moment.");
            return false;
        }
        fight->TestHeal();
        handler->PSendSysMessage("{}", "Malicia: Shadow Heal (MA7).");
        return true;
    }

    // `.dbtest scholo malicia bound <n>`: sets her Bound Soul stacks, 0 to 20 (MA5).
    bool HandleBound(ChatHandler* handler, uint32 stacks)
    {
        MaliciaFight* fight = FindFight(handler);
        if (!fight)
            return false;
        handler->PSendSysMessage("Malicia: Bound Soul {}.", fight->TestBound(stacks));
        return true;
    }

    // `.dbtest scholo malicia lesson [0|1]`: the Coven's detention lesson on the selected player (or you), run by a
    // stand-in stalker where they stand (in the Coven); 1 = heroic. Needs another living player in the instance (a
    // lesson whose student is the last one alive ends at once, by the safety rule).
    bool HandleLesson(ChatHandler* handler, Optional<uint32> heroic)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return false;
        Player* student = TestTarget(handler);
        if (!student)
            return false;
        uint32 const entry = sObjectMgr->GetCreatureTemplate(NPC_SC_LESSON_STALKER) ? uint32(NPC_SC_LESSON_STALKER)
            : uint32(NPC_SC_BLIZZARD_ANCHOR);
        bool const isHeroic = heroic ? *heroic != 0 : DungeonKit::IsHeroicMap(student);
        TempSummon* host = student->SummonCreature(entry, student->GetPosition(), TEMPSUMMON_TIMED_DESPAWN,
            kLessonMs + 10000);
        if (!host)
        {
            handler->SendErrorMessage("{}", "Could not summon the lesson's stand-in stalker.");
            return false;
        }
        host->SetReactState(REACT_PASSIVE);
        host->AIM_Initialize(new npc_sc_malicia_lesson_host(host, student->GetGUID(), isHeroic));
        handler->PSendSysMessage("Malicia: the Coven's lesson ({}) on {}; the log has the verdict (malicia-lesson).",
            isHeroic ? "heroic" : "normal", student->GetName());
        return true;
    }

    ChatCommandTable const& MaliciaTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "soul",   HandleSoul,   SEC_GAMEMASTER, Console::No },
            { "drain",  HandleDrain,  SEC_GAMEMASTER, Console::No },
            { "shade",  HandleShade,  SEC_GAMEMASTER, Console::No },
            { "storm",  HandleStorm,  SEC_GAMEMASTER, Console::No },
            { "heal",   HandleHeal,   SEC_GAMEMASTER, Console::No },
            { "bound",  HandleBound,  SEC_GAMEMASTER, Console::No },
            { "lesson", HandleLesson, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_instructor_malicia_rework()
{
    RegisterDungeonReworkCreatureAI(boss_instructor_malicia_rework, ScholomanceRework::kInstanceScriptName);
    // The examiner's script name is MaliciaFight.h kExaminerScriptName; S13 binds the entry in wave C.
    if (kWaveCBound)
        RegisterDungeonReworkCreatureAI(npc_sc_examiner_malicia, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_malicias_shade, ScholomanceRework::kInstanceScriptName);
    RegisterSpellScript(spell_scholo_malicia_soul);
    RegisterSpellScript(spell_scholo_malicia_soul_weight);
    RegisterSpellScript(spell_scholo_malicia_shadow_heal);
    RegisterSpellScript(spell_scholo_malicia_shadow_nova);
    RegisterSpellScript(spell_scholo_malicia_soul_lost);
    RegisterSoloLesson(Classroom::Coven, [] { return std::unique_ptr<SoloLesson>(new CovenLesson()); });
    ScholoTest::RegisterBoss("malicia", MaliciaTestCommands());
}
