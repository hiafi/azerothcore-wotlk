/*
 * mod-dungeon-bosses, Blackrock Spire B2: Shadow Hunter Vosh'gajin (9236), "Voodoo Dolls". Build spec SP 964-1021
 * (docs/dungeons/blackrock-spire-rework.md, rulings 24-28), handoff section 3.4 rows VG and 3.5 row B2. Replaces her
 * SmartAI (the Hex 16097 and Curse of Blood 16098 rows are dropped by the S0 SQL rev; the Shadow Priests 43550 and
 * 43551 by this WP's rev): the creature template is bound by apps/dbc-tools source/npcs/blackrock_spire/voshgajin.py.
 * She casts nothing herself; the fight is the Voodoo Doll 300703 (display 25017, rooted on her dais, not selectable).
 * Pure rules: VoshgajinLogic.h.
 *
 *   VG1  Bind          8 s, then every 25 s (heroic 20 s): a random non-tank (two at 6 or more, one doll each) is
 *                      bound to a doll: emote line 1, Puppet Strings from the doll to them (the channel 210060)
 *   VG2  Bound         the Curse (210061) on each: a pin (5% of the row) every 2 s, a pin look per tick; 18 s or until
 *                      the last torment has landed. A Curse dispel stops the pins, the strings stay
 *   VG6  Torments      each binding runs Voodoo Flames, Needle and Squeeze once each in a random order in three slots
 *                      (4 / 10 / 16 s; heroic 3 / 8 / 13 s); a tell is 3 s on the doll (it swells x2 and shows its
 *                      state look), and the hit lands when the tell ends. Both dolls show the same tell. Heroic from
 *                      50%: the first slot is the Needle with Flames or Squeeze, the second slot the third alone
 *   VG3  Voodoo Flames a hidden registry RunOut on the Bound player (8 yd, 30% Fire + Weakened on the others, heroic
 *                      35%); on its resolve the Bound player takes 10% and a persistent 5 yd patch burns for 20 s
 *                      (10% a second, one Weakened per player per patch)
 *   VG4  Needle        a hidden registry Line from the doll to the Bound player (4 yd, live anchors): 40% Physical
 *                      (heroic 50%) on everyone but the Bound ones (eligibility: no Bound stacks), no Weakened; the
 *                      Bound player takes 10% and a needle flies down the string
 *   VG5  Squeeze       a hidden registry Donut 5-25 yd round the Bound player: 25% Shadow (heroic 30%) + Weakened +
 *                      the 2 s hex on everyone inside
 *   VG7  Hex of Agony  heroic: 15 s, then every 20 s a random non-tank (two at 6 or more) carries Hex of Agony 8 s
 *                      (4% a second, Magic): dispelled it is gone, expired it bursts 8 yd (40% Shadow + the 2 s hex,
 *                      a registry RunOut on the carrier)
 *   VG8  Reset         evade, wipe or death: strings, Bound, hexes, tells and mechanics removed, dolls despawned
 *   Arena              BlackrockSpireRework::LeashOptions on VoshgajinArena() (no grips; holds at the edge)
 *
 * No torment draws a ground marker (ruling 25, NoTelegraph): the doll's tell is the warning. The patch is the one
 * lingering hazard and keeps its registry marker. Every timer runs on the AI's own clock, never on BossAI's scheduler.
 * Every firing logs one INFO line "brs voshgajin <mechanic> ..." (module.dungeonbosses). Lambdas the registry keeps
 * capture guids only.
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "VoshgajinLogic.h"
#include <algorithm>
#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsVoshgajin;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "voshgajin";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // Everyone not on a doll's strings (the Needle's line: the bound player is never on his own string). Keyed on
    // Puppet Strings (kNeedleSkipAura), which stays for the whole binding, not on the Bound curse: a dispelled Bound
    // player is still at the line's far end (R-1-A M2).
    BossMechanics::Eligibility WithoutBound()
    {
        BossMechanics::Eligibility e;
        e.auraSpell = kNeedleSkipAura;
        e.minStacks = 0;
        e.maxStacks = 0;
        return e;
    }
}

struct boss_shadow_hunter_voshgajin_rework : public BossAI
{
private:
    struct BoundPlayer
    {
        ObjectGuid player;
        ObjectGuid doll;
        Position lastPos;
        uint64 nextPinMs = 0;
        bool gone = false;                      // the player died: the strings are cut
        std::vector<MechanicHandle> live;       // the torment mechanics registered on this player
    };

    struct Binding
    {
        bool active = false;
        bool heroic = false;
        bool twin = false;
        Schedule schedule;
        uint8 nextStep = 0;
        uint64 startMs = 0;
        uint32 holdMs = 0;
        std::vector<BoundPlayer> bound;
    };

    struct HexCarrier
    {
        ObjectGuid player;
        MechanicHandle burst;
        uint64 endMs = 0;
        uint64 nextSkullMs = 0;
    };

    static uint32 constexpr kRetryMs = 1000;
    static uint32 constexpr kHexDoneAfterMs = 1500;     // the burst resolves by itself this long after the expiry
    static uint32 constexpr kHexSkullGuardMs = 500;     // no skull look this close to the end

public:
    explicit boss_shadow_hunter_voshgajin_rework(Creature* creature)
        : BossAI(creature, BOSS_VOSHGAJIN),
          _arena(VoshgajinArena(), LeashOptions(kBossLogName)) { }

    void Reset() override
    {
        _Reset();
        Cleanup();
        _arena.Reset();
        _players = 0;
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _players = OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_VOSHGAJIN;
        Mechanic::BeginEncounter(me, options);

        bool const heroic = IsHeroicMap(me);
        _bindPlannedMs = kBindFirstMs;
        _nextBindMs = kBindFirstMs;
        _nextHexMs = heroic ? kHexOfAgony.first : 0;
        _hexPlannedMs = _nextHexMs;
        SummonDolls();
        Describe(heroic);
        _arena.Engage(me);
        Talk(YELL_VG_PULL);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} players={} dolls={}", heroic ? 1 : 0, _players, _dolls.size()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        _arena.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        Cleanup();
        _arena.Reset();
        Talk(YELL_VG_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar (she has none).
        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off her arena, or nobody on it for 10 s: evading

        bool const heroic = IsHeroicMap(me);
        UpdateTwinYell(heroic);
        UpdateBinding(heroic);
        if (heroic)
            UpdateHexOfAgony();

        events.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The players and the dolls
    // ----------------------------------------------------------------------------------------------------------------

    Player* PlayerOf(ObjectGuid guid) const
    {
        return guid ? ObjectAccessor::GetPlayer(*me, guid) : nullptr;
    }

    Creature* DollOf(ObjectGuid guid) const
    {
        return guid ? ObjectAccessor::GetCreature(*me, guid) : nullptr;
    }

    // The dolls on her dais: one, and a second at 6 or more players (SP ruling 26). They stand there the whole fight.
    void SummonDolls()
    {
        uint8 const wanted = kBindCount.At(_players);
        for (uint8 i = 0; i < wanted && i < kDollSpots.size(); ++i)
            _dolls.push_back(SummonDoll(i));
    }

    ObjectGuid SummonDoll(uint8 index)
    {
        Point4 const& spot = kDollSpots[index];
        Creature* doll = me->SummonCreature(NPC_BRS_VOODOO_DOLL, Position(spot.x, spot.y, spot.z, spot.o),
            TEMPSUMMON_MANUAL_DESPAWN);
        if (!doll)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "doll-fail", Acore::StringFormat("index={}", index));
            return ObjectGuid::Empty;
        }
        doll->SetReactState(REACT_PASSIVE);
        return doll->GetGUID();
    }

    // Doll `index`, summoned again when it is gone (a despawn, a test run out of combat).
    Creature* EnsureDoll(uint8 index)
    {
        if (index >= kDollSpots.size())
            return nullptr;
        while (_dolls.size() <= index)
            _dolls.push_back(ObjectGuid::Empty);
        Creature* doll = DollOf(_dolls[index]);
        if (doll && doll->IsAlive())
            return doll;
        _dolls[index] = SummonDoll(index);
        return DollOf(_dolls[index]);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VG1 Bind, VG2 Bound
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateTwinYell(bool heroic)
    {
        if (_twinYelled || !TwinOn(heroic, me->GetHealthPct()))
            return;
        _twinYelled = true;
        Talk(YELL_VG_TWIN);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "twin-begins",
            Acore::StringFormat("health={:.1f}", me->GetHealthPct()));
    }

    void UpdateBinding(bool heroic)
    {
        if (_binding.active)
        {
            uint64 const elapsed = _clockMs - _binding.startMs;
            while (_binding.nextStep < _binding.schedule.count
                && elapsed >= _binding.schedule.steps[_binding.nextStep].atMs)
                RunStep(_binding.schedule.steps[_binding.nextStep++], heroic);
            UpdatePins();
            if (elapsed >= _binding.holdMs)
                EndBinding("hold");
            else if (!AnyBoundAlive())
                EndBinding("bound-died");
        }
        if (!_binding.active && _clockMs >= _nextBindMs)
        {
            if (StartBinding(heroic, {}))
            {
                _bindPlannedMs = NextBindMs(_bindPlannedMs, heroic, _clockMs);
                _nextBindMs = _bindPlannedMs;
            }
            else
                _nextBindMs = _clockMs + kRetryMs;
        }
    }

    // `twinOverride`: a test forces the twin form on or off; otherwise heroic and under 50% health. False when nobody
    // can be bound (tried again in a second).
    bool StartBinding(bool heroic, std::optional<bool> twinOverride)
    {
        if (_binding.active)
            EndBinding("replaced");
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;        // a tank-only group is still bound
        std::vector<Player*> const picks = DungeonKit::PickPlayers(me, rule, kBindCount.At(_players));
        if (picks.empty())
            return false;

        bool const twin = twinOverride ? *twinOverride : TwinOn(heroic, me->GetHealthPct());
        Schedule const schedule = BuildSchedule(heroic, twin, urand(0, kOrderCount - 1), urand(0, 1));
        uint32 const holdMs = BindHoldMs(schedule);
        Binding binding;
        binding.active = true;
        binding.heroic = heroic;
        binding.twin = twin;
        binding.schedule = schedule;
        binding.startMs = _clockMs;
        binding.holdMs = holdMs;

        std::string detail;
        for (std::size_t i = 0; i < picks.size(); ++i)
        {
            Player* player = picks[i];
            Creature* doll = EnsureDoll(static_cast<uint8>(i));
            if (!doll)
                continue;
            if (Aura* aura = me->AddAura(SPELL_VG_BOUND, player))
            {
                aura->SetMaxDuration(static_cast<int32>(holdMs));
                aura->SetDuration(static_cast<int32>(holdMs));
            }
            doll->CastSpell(player, SPELL_VG_BIND, true);
            Talk(EMOTE_VG_BIND, player);
            BoundPlayer bound;
            bound.player = player->GetGUID();
            bound.doll = doll->GetGUID();
            bound.lastPos = player->GetPosition();
            bound.nextPinMs = _clockMs + kPinEveryMs;
            binding.bound.push_back(std::move(bound));
            detail += Acore::StringFormat(" {}@doll{}", player->GetName(), i + 1);
        }
        if (binding.bound.empty())
            return false;

        std::string order;
        for (std::uint8_t i = 0; i < schedule.count; ++i)
        {
            Step const& step = schedule.steps[i];
            order += Acore::StringFormat("{}{}s:{}", i ? " " : "", step.atMs / 1000, TormentName(step.torments[0]));
            if (step.count > 1)
                order += Acore::StringFormat("+{}", TormentName(step.torments[1]));
        }
        _binding = std::move(binding);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bind",
            Acore::StringFormat("heroic={} twin={} hold={}ms order=[{}] bound{}", heroic ? 1 : 0, twin ? 1 : 0, holdMs,
                order, detail));
        return true;
    }

    bool AnyBoundAlive() const
    {
        for (BoundPlayer const& bound : _binding.bound)
        {
            Player* player = PlayerOf(bound.player);
            if (player && player->IsAlive())
                return true;
        }
        return false;
    }

    // A pin look on each Bound player every 2 s while the Curse is on them (the damage is the aura's own tick); the
    // last position of each is kept for a torment that lands after the player fell.
    void UpdatePins()
    {
        for (BoundPlayer& bound : _binding.bound)
        {
            Player* player = PlayerOf(bound.player);
            if (!player || !player->IsAlive())
            {
                if (!bound.gone)
                {
                    bound.gone = true;
                    for (MechanicHandle const& handle : bound.live)
                        Mechanic::Cancel(me, handle);
                    bound.live.clear();
                    if (Creature* doll = DollOf(bound.doll))
                        doll->InterruptNonMeleeSpells(false, SPELL_VG_BIND);
                }
                continue;
            }
            bound.lastPos = player->GetPosition();
            if (_clockMs < bound.nextPinMs)
                continue;
            bound.nextPinMs += kPinEveryMs;
            if (player->HasAura(SPELL_VG_BOUND))
                if (Creature* doll = DollOf(bound.doll))
                    doll->CastSpell(player, SPELL_VG_PIN, true);
        }
    }

    // The strings end, Bound comes off (a Curse not yet dispelled), the mechanics still pending go.
    void EndBinding(char const* why)
    {
        if (!_binding.active)
            return;
        std::string detail;
        for (BoundPlayer& bound : _binding.bound)
        {
            for (MechanicHandle const& handle : bound.live)
                Mechanic::Cancel(me, handle);
            bound.live.clear();
            if (Creature* doll = DollOf(bound.doll))
                doll->InterruptNonMeleeSpells(false, SPELL_VG_BIND);
            if (Player* player = PlayerOf(bound.player))
            {
                detail += Acore::StringFormat(" {}:{}", player->GetName(), player->HasAura(SPELL_VG_BOUND) ? "bound" :
                    "cured");
                player->RemoveAurasDueToSpell(SPELL_VG_BOUND);
            }
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bind-end",
            Acore::StringFormat("why={} at={}ms{}", why, _clockMs - _binding.startMs, detail));
        _binding = Binding();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VG6 The torments: a tell on the dolls, the registry mechanic beside it
    // ----------------------------------------------------------------------------------------------------------------

    void RunStep(Step const& step, bool heroic)
    {
        std::vector<BoundPlayer*> alive;
        for (BoundPlayer& bound : _binding.bound)
        {
            Player* player = PlayerOf(bound.player);
            if (player && player->IsAlive())
                alive.push_back(&bound);
        }
        if (alive.empty())
            return;

        // Both dolls show the same tell, one swell and one state look per torment of the step.
        for (BoundPlayer const& bound : _binding.bound)
            if (Creature* doll = DollOf(bound.doll))
                ShowTell(doll, step);
        std::string detail;
        for (std::uint8_t i = 0; i < step.count; ++i)
        {
            Torment const torment = step.torments[i];
            for (BoundPlayer* bound : alive)
                if (Player* player = PlayerOf(bound->player))
                    FireTorment(torment, *bound, player, heroic);
            detail += Acore::StringFormat("{}{}", i ? "+" : "", TormentName(torment));
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "torment",
            Acore::StringFormat("heroic={} at={}ms tells={} bound={}", heroic ? 1 : 0, step.atMs, detail,
                alive.size()));
    }

    static uint32 TellSpellOf(Torment torment)
    {
        switch (torment)
        {
            case Torment::Flames:   return SPELL_VG_FLAMES_TELL;
            case Torment::Needle:   return SPELL_VG_NEEDLE_TELL;
            case Torment::Squeeze:  return SPELL_VG_SQUEEZE_TELL;
        }
        return 0;
    }

    void ShowTell(Creature* doll, Step const& step)
    {
        doll->CastSpell(doll, SPELL_VG_DOLL_SWELL, true);
        for (std::uint8_t i = 0; i < step.count; ++i)
            doll->CastSpell(doll, TellSpellOf(step.torments[i]), true);
    }

    void FireTorment(Torment torment, BoundPlayer& bound, Player* player, bool heroic)
    {
        MechanicHandle handle;
        switch (torment)
        {
            case Torment::Flames:
                handle = RegisterFlames(player, heroic);
                break;
            case Torment::Needle:
                handle = RegisterNeedle(bound, player, heroic);
                break;
            case Torment::Squeeze:
                handle = RegisterSqueeze(player, heroic);
                break;
        }
        if (handle)
            bound.live.push_back(handle);
        Track(handle);
    }

    // VG3: the burst is a hidden RunOut on the Bound player (the others in 8 yd), the patch and the Bound player's own
    // 10% follow when it resolves.
    MechanicHandle RegisterFlames(Player* player, bool heroic)
    {
        float const pct = kFlamesPct(heroic);
        MechanicRef ref = Mechanic::RunOut(me, player, kFlamesRadius, Ms(kTellMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_VG_FLAMES_HIT).Weakened().NoTelegraph()
            .Tag(TAG_VG_FLAMES);
        ref.OnResolve(OnVosh([gen = _generation, guid = player->GetGUID()](boss_shadow_hunter_voshgajin_rework& ai,
            BossMechanics::ResolveResult const& result)
        {
            if (gen == ai._generation)
                ai.FlamesLanded(guid, result.hits.size());
        }));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flames",
            Acore::StringFormat("heroic={} pct={:.0f} radius={:.0f} bound={}", heroic ? 1 : 0, pct, kFlamesRadius,
                player->GetName()));
        return ref.Handle();
    }

    void FlamesLanded(ObjectGuid boundGuid, std::size_t hits)
    {
        Player* player = PlayerOf(boundGuid);
        bool const alive = player && player->IsAlive();
        Position at;
        if (alive)
            at = player->GetPosition();
        else if (BoundPlayer const* bound = FindBound(boundGuid))
            at = bound->lastPos;
        else
            return;
        PlacePatch(at);
        if (alive)
            HitBound(player, kFlamesBoundPct, SPELL_SCHOOL_FIRE, SPELL_VG_FLAMES_HIT);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flames-landed",
            Acore::StringFormat("hits={} patch=({:.1f}, {:.1f}) boundHit={}", hits, at.GetPositionX(),
                at.GetPositionY(), alive ? 1 : 0));
    }

    // The patch where the burst went off: 5 yd, 20 s, 10% a second after a 1 s grace, one Weakened per player. It is
    // the one lingering hazard of the fight, so it keeps its registry marker (outline only until it burns).
    void PlacePatch(Position const& at)
    {
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(at, kPatchRadius), Ms(kPatchTickMs));
        ref.Persistent(Ms(kPatchMs), Ms(kPatchTickMs)).Damage(kPatchPct).TankDamage(kPatchPct)
            .School(SPELL_SCHOOL_FIRE).Spell(SPELL_VG_PATCH_HIT).WeakenedOncePerPlayer().NoFillTimer()
            .Tag(TAG_VG_PATCH);
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "patch",
            Acore::StringFormat("at=({:.1f}, {:.1f}) r={:.0f} life={}ms pct={:.0f}", at.GetPositionX(),
                at.GetPositionY(), kPatchRadius, kPatchMs, kPatchPct));
    }

    // The Bound player's own hit (a RunOut measured from her, one target), no Weakened.
    void HitBound(Player* player, float pct, uint8 school, uint32 spellId)
    {
        GuidSet targets;
        targets.insert(player->GetGUID());
        DungeonKit::RegistryHitSpec spec;
        spec.pct = pct;
        spec.tankPct = pct;
        spec.school = school;
        spec.spellId = spellId;
        spec.weakened = false;
        spec.tag = TAG_VG_BOUND_HIT;
        Track(DungeonKit::RegistryHit(me, targets, spec));
    }

    // VG4: the doll's line to the Bound player with both ends live; nobody carrying Bound is on it.
    MechanicHandle RegisterNeedle(BoundPlayer const& bound, Player* player, bool heroic)
    {
        Creature* doll = DollOf(bound.doll);
        if (!doll)
            return {};
        float const pct = kNeedlePct(heroic);
        MechanicRef ref = Mechanic::Line(me, BossMechanics::Anchor(doll), BossMechanics::Anchor(player), kNeedleWidth,
            Ms(kTellMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_VG_NEEDLE_HIT)
            .Eligible(WithoutBound()).NoTelegraph().Tag(TAG_VG_NEEDLE);
        ref.OnResolve(OnVosh([gen = _generation, guid = player->GetGUID(), dollGuid = bound.doll](
            boss_shadow_hunter_voshgajin_rework& ai, BossMechanics::ResolveResult const& result)
        {
            if (gen == ai._generation)
                ai.NeedleLanded(guid, dollGuid, result.hits.size());
        }));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "needle",
            Acore::StringFormat("heroic={} pct={:.0f} width={:.0f} bound={} length={:.1f}", heroic ? 1 : 0, pct,
                kNeedleWidth, player->GetName(), doll->GetExactDist(player)));
        return ref.Handle();
    }

    void NeedleLanded(ObjectGuid boundGuid, ObjectGuid dollGuid, std::size_t hits)
    {
        Player* player = PlayerOf(boundGuid);
        bool const alive = player && player->IsAlive();
        if (alive)
        {
            if (Creature* doll = DollOf(dollGuid))
                doll->CastSpell(player, SPELL_VG_NEEDLE_FLIGHT, true);
            HitBound(player, kNeedleBoundPct, SPELL_SCHOOL_NORMAL, SPELL_VG_NEEDLE_HIT);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "needle-landed",
            Acore::StringFormat("hits={} boundHit={}", hits, alive ? 1 : 0));
    }

    // VG5: a donut round the Bound player; everyone inside is hexed for 2 s as well.
    MechanicHandle RegisterSqueeze(Player* player, bool heroic)
    {
        float const pct = kSqueezePct(heroic);
        MechanicRef ref = Mechanic::Donut(me, player, kSqueezeInner, kSqueezeOuter, Ms(kTellMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_VG_SQUEEZE_HIT).Weakened()
            .Rider(SPELL_VG_HEXED).NoTelegraph().Tag(TAG_VG_SQUEEZE);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "squeeze",
            Acore::StringFormat("heroic={} pct={:.0f} donut={:.0f}-{:.0f} bound={}", heroic ? 1 : 0, pct,
                kSqueezeInner, kSqueezeOuter, player->GetName()));
        return ref.Handle();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VG7 Hex of Agony (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateHexOfAgony()
    {
        for (auto it = _hexes.begin(); it != _hexes.end();)
        {
            Player* player = PlayerOf(it->player);
            bool const alive = player && player->IsAlive();
            bool const hexed = alive && player->HasAura(SPELL_VG_HEX_OF_AGONY);
            bool drop = false;
            if (!alive)
            {
                // The burst needs its carrier.
                Mechanic::Cancel(me, it->burst);
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hex-of-agony-ended", "why=carrier-died");
                drop = true;
            }
            else if (!hexed)
            {
                if (_clockMs + kHexDispelledBeforeMs < it->endMs)
                {
                    Mechanic::Cancel(me, it->burst);
                    DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hex-of-agony-ended",
                        Acore::StringFormat("why=dispelled carrier={} left={}ms", player->GetName(),
                            it->endMs - _clockMs));
                    drop = true;
                }
                else if (_clockMs > it->endMs + kHexDoneAfterMs)
                    drop = true;    // it ran out and the burst resolved by itself
            }
            else if (_clockMs >= it->nextSkullMs && _clockMs + kHexSkullGuardMs < it->endMs)
            {
                it->nextSkullMs += kHexSkullEveryMs;
                me->CastSpell(player, SPELL_VG_HEX_SKULL, true);
            }
            it = drop ? _hexes.erase(it) : it + 1;
        }
        if (_clockMs >= _nextHexMs)
        {
            if (StartHexOfAgony())
            {
                _hexPlannedMs += kHexOfAgony.every;
                _nextHexMs = std::max<uint64>(_hexPlannedMs, _clockMs + 1);
            }
            else
                _nextHexMs = _clockMs + kRetryMs;
        }
    }

    // False when nobody can carry it (tried again in a second).
    bool StartHexOfAgony()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        for (HexCarrier const& hex : _hexes)
            rule.exclude.push_back(hex.player.GetRawValue());
        std::vector<Player*> const picks = DungeonKit::PickPlayers(me, rule, kHexOfAgonyCount.At(_players));
        if (picks.empty())
            return false;
        std::string detail;
        for (Player* player : picks)
        {
            Aura* aura = me->AddAura(SPELL_VG_HEX_OF_AGONY, player);
            if (!aura)
                continue;
            aura->SetMaxDuration(static_cast<int32>(kHexOfAgonyMs));
            aura->SetDuration(static_cast<int32>(kHexOfAgonyMs));
            me->CastSpell(player, SPELL_VG_HEX_SKULL, true);
            MechanicRef ref = Mechanic::RunOut(me, player, kHexBurstRadius, Ms(kHexOfAgonyMs));
            ref.Damage(kHexBurstPct).TankDamage(kHexBurstPct).School(SPELL_SCHOOL_SHADOW)
                .Spell(SPELL_VG_HEX_BURST_HIT).Rider(SPELL_VG_HEXED).Tag(TAG_VG_HEX_BURST);
            ref.OnResolve(OnVosh([gen = _generation, guid = player->GetGUID()](
                boss_shadow_hunter_voshgajin_rework& ai, BossMechanics::ResolveResult const& result)
            {
                if (gen == ai._generation && !result.fizzled)
                    DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hex-burst",
                        Acore::StringFormat("hits={}", result.hits.size()));
            }));
            HexCarrier hex;
            hex.player = player->GetGUID();
            hex.burst = ref.Handle();
            hex.endMs = _clockMs + kHexOfAgonyMs;
            hex.nextSkullMs = _clockMs + kHexSkullEveryMs;
            Track(hex.burst);
            _hexes.push_back(hex);
            detail += Acore::StringFormat(" {}", player->GetName());
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hex-of-agony",
            Acore::StringFormat("pct={:.0f}/s burst={:.0f}% r={:.0f} carriers{}", kHexOfAgonyPct, kHexBurstPct,
                kHexBurstRadius, detail));
        return !_hexes.empty();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SP): kill order the boss only (the doll is not attackable); no interrupts; dispels Hex of Agony
    // (heroic, Magic, expected) and Bound (Curse, a reward)
    // ----------------------------------------------------------------------------------------------------------------

    void Describe(bool heroic)
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_VOSHGAJIN, 1, BossMechanics::Who::Any);
        d.dispels.emplace_back(SPELL_VG_BOUND, 1);
        if (heroic)
            d.dispels.emplace_back(SPELL_VG_HEX_OF_AGONY, 3, false, Ms(4000));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs voshgajin` entry points (`heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    bool HeroicMap() const { return IsHeroicMap(me); }

    // An empty string when fired; otherwise why not.
    std::string TestBind(bool heroic, std::optional<bool> twin)
    {
        if (!me->IsEngaged())
            return "Vosh'gajin must be in combat (the bind picks among the players in the fight; a GM is skipped).";
        if (!StartBinding(heroic, twin))
            return "Nobody in the fight can be bound (a GM does not count).";
        return {};
    }

    // The torment `which` now, on the binding that runs (the tell on the dolls included).
    std::string TestTorment(Torment which, bool heroic)
    {
        if (!_binding.active)
            return "No binding is running; fire `bind` first.";
        Step step;
        step.atMs = static_cast<uint32>(_clockMs - _binding.startMs);
        step.torments[0] = which;
        step.count = 1;
        RunStep(step, heroic);
        return {};
    }

    std::string TestHexOfAgony()
    {
        if (!me->IsEngaged())
            return "Vosh'gajin must be in combat (Hex of Agony picks among the players in the fight).";
        if (!StartHexOfAgony())
            return "Nobody in the fight can carry it (a GM does not count).";
        return {};
    }

    std::string TestState() const
    {
        std::string binding = "none";
        if (_binding.active)
        {
            std::string who;
            for (BoundPlayer const& bound : _binding.bound)
                if (Player* player = PlayerOf(bound.player))
                    who += Acore::StringFormat(" {}{}", player->GetName(), player->IsAlive() ? "" : "(dead)");
            binding = Acore::StringFormat("{}s of {}s, step {}/{}, twin={}, bound{}",
                (_clockMs - _binding.startMs) / 1000, _binding.holdMs / 1000, _binding.nextStep,
                _binding.schedule.count, _binding.twin ? 1 : 0, who);
        }
        return Acore::StringFormat("clock={}s players={} binding=[{}] nextBind={}s hexes={} nextHex={}s dolls={} "
            "patches/mechanics tracked={}", _clockMs / 1000, _players, binding, _nextBindMs / 1000, _hexes.size(),
            _nextHexMs / 1000, _dolls.size(), _live.size());
    }

private:
    BoundPlayer const* FindBound(ObjectGuid guid) const
    {
        for (BoundPlayer const& bound : _binding.bound)
            if (bound.player == guid)
                return &bound;
        return nullptr;
    }

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnVosh(Fn fn)
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
            if (auto* ai = dynamic_cast<boss_shadow_hunter_voshgajin_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // The pull's state: nothing pending, no Bound, hex or tell on anyone, the dolls gone (Reset, evade, death, a new
    // pull). The flex count stays (Reset zeroes it).
    void Cleanup()
    {
        ++_generation;      // a resolve callback of an older pull stops
        EndBinding("cleanup");
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _hexes.clear();
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                {
                    player->RemoveAurasDueToSpell(SPELL_VG_BOUND);
                    player->RemoveAurasDueToSpell(SPELL_VG_HEX_OF_AGONY);
                    player->RemoveAurasDueToSpell(SPELL_VG_HEXED);
                }
        for (ObjectGuid const& guid : _dolls)
            if (Creature* doll = DollOf(guid))
                doll->DespawnOrUnsummon();
        _dolls.clear();
        _clockMs = 0;
        _nextBindMs = 0;
        _bindPlannedMs = 0;
        _nextHexMs = 0;
        _hexPlannedMs = 0;
        _twinYelled = false;
        _binding = Binding();
    }

    DungeonKit::ArenaGuard _arena;
    Binding _binding;
    std::vector<HexCarrier> _hexes;
    std::vector<ObjectGuid> _dolls;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _nextBindMs = 0;
    uint64 _bindPlannedMs = 0;                  // the planned start of the next binding (start to start)
    uint64 _nextHexMs = 0;
    uint64 _hexPlannedMs = 0;
    uint32 _generation = 0;
    uint8 _players = 0;                         // the flex count held at the pull (5..10)
    bool _twinYelled = false;
};

// The Voodoo Doll 300703: stands on the dais, carries the swell, the tells and the strings; the boss summons and
// despawns it. Nothing else.
struct npc_brs_voodoo_doll : public NullCreatureAI
{
    explicit npc_brs_voodoo_doll(Creature* creature) : NullCreatureAI(creature) { }
};

namespace
{
    boss_shadow_hunter_voshgajin_rework* FindVoshgajinAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_VOSHGAJIN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_shadow_hunter_voshgajin_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Vosh'gajin is not running boss_shadow_hunter_voshgajin_rework (check "
                "the ScriptName).");
        return ai;
    }

    bool Finish(ChatHandler* handler, std::string const& error, char const* what, bool heroic)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Vosh'gajin: {} fired ({}).", what, heroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_VOSHGAJIN, BOSS_VOSHGAJIN);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_shadow_hunter_voshgajin_rework* ai = FindVoshgajinAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Vosh'gajin: {}", ai->TestState());
        return true;
    }

    // `.dbtest brs voshgajin bind [heroic [twin]]`: the optional 1 / 0 force the heroic and the twin forms.
    bool HandleBind(ChatHandler* handler, Optional<uint32> heroicArg, Optional<uint32> twinArg)
    {
        boss_shadow_hunter_voshgajin_rework* ai = FindVoshgajinAI(handler);
        if (!ai)
            return false;
        bool const heroic = heroicArg ? *heroicArg != 0 : ai->HeroicMap();
        std::optional<bool> twin;
        if (twinArg)
            twin = *twinArg != 0;
        return Finish(handler, ai->TestBind(heroic, twin), "the bind (VG1; torments follow at their slots)", heroic);
    }

    bool FireTorment(ChatHandler* handler, Torment which, Optional<uint32> heroicArg, char const* what)
    {
        boss_shadow_hunter_voshgajin_rework* ai = FindVoshgajinAI(handler);
        if (!ai)
            return false;
        bool const heroic = heroicArg ? *heroicArg != 0 : ai->HeroicMap();
        return Finish(handler, ai->TestTorment(which, heroic), what, heroic);
    }

    bool HandleFlames(ChatHandler* handler, Optional<uint32> heroic)
    {
        return FireTorment(handler, Torment::Flames, heroic, "Voodoo Flames now (VG3; needs a binding)");
    }

    bool HandleNeedle(ChatHandler* handler, Optional<uint32> heroic)
    {
        return FireTorment(handler, Torment::Needle, heroic, "the Needle now (VG4; needs a binding)");
    }

    bool HandleSqueeze(ChatHandler* handler, Optional<uint32> heroic)
    {
        return FireTorment(handler, Torment::Squeeze, heroic, "the Squeeze now (VG5; needs a binding)");
    }

    bool HandleHexOfAgony(ChatHandler* handler)
    {
        boss_shadow_hunter_voshgajin_rework* ai = FindVoshgajinAI(handler);
        if (!ai)
            return false;
        return Finish(handler, ai->TestHexOfAgony(), "Hex of Agony (VG7)", true);
    }

    ChatCommandTable const& VoshgajinTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,        SEC_GAMEMASTER, Console::No },
            { "bind",       HandleBind,         SEC_GAMEMASTER, Console::No },
            { "flames",     HandleFlames,       SEC_GAMEMASTER, Console::No },
            { "needle",     HandleNeedle,       SEC_GAMEMASTER, Console::No },
            { "squeeze",    HandleSqueeze,      SEC_GAMEMASTER, Console::No },
            { "hexofagony", HandleHexOfAgony,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_shadow_hunter_voshgajin_rework()
{
    RegisterDungeonReworkCreatureAI(boss_shadow_hunter_voshgajin_rework, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_voodoo_doll, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("voshgajin", VoshgajinTestCommands());
}
