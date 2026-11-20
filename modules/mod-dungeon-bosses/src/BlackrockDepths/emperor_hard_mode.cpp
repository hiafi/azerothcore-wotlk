/*
 * mod-dungeon-bosses, Blackrock Depths D24: Emperor Dagran Thaurissan's hard mode, the Avatar of Ragnaros (heroic,
 * "The Princess Saved"). Build spec: docs/dungeons/blackrock-depths-4-imperial-seat.md "Hard mode" and "Build spec"
 * (EM11-EM13; rulings 77-81, 88), handoff sections 3.6, 3.7 row D24, 3.10, 7 #15 and #19. It fights on D23's AI
 * (boss_emperor_dagran_thaurissan_rework) through EmperorFight.h: nothing arms it; on heroic, lethal damage to Dagran
 * while Moira stands in the court makes D23 ask this file's factory for one Avatar, and the steps below run on D23's
 * hooks. Pure rules and numbers: EmperorHardModeLogic.h.
 *
 *   D23 (step 1-2)    the lethal hit held at 1 health, SetData(DATA_AVATAR, 1) (the instance lights the hard mode
 *                     loot bit; refused off heroic: no branch), every court beat stopped, the guards and the
 *                     Ambassadors leave, Moira caged (not selectable, passive, in combat), yell 10
 *   OnAwaken          EM11 Ragnaros Awakens: every player of the fight is knocked back 15 yd from where he stood (a
 *                     plain knockback), he jumps to the throne (his spawn on the dais), Pillar of Fire there; the loot
 *                     bit is made sure of (the instance set it a moment ago)
 *   OnRise (3 s)      the Avatar: display 11121 at 0.15 (8.7 yd tall), combat reach 3.5 yd, rooted on the throne,
 *                     260,000 health, Massive Eruption at the throne. D23 disarms the lethal guard (his death is
 *                     real), and its Firestorm continues on heroic values 5 s later
 *   EM12 Magma Clap   10 s after the rise, then every 20 s: a 3 s Fire bar (emote 11) and a 30 yd RunOut from him
 *                     (the bots' telegraph); at its end everyone of the fight takes 70% within 10 yd, falling to 15%
 *                     at 40 yd (the tank too: he is rooted, so the tank walks back)
 *   EM13 Volcanic     15 s after the rise, then every 25 s: a random player (the tank too) marked 5 s (emote 12
 *        Blast        names them; a Stack on them for the bots); 80% split among everyone within 8 yd, then a
 *                     Volcanic Stone where the mark stood: 5 yd, 30 s, 8% a second (at most 2 stand)
 *   The clock         the two casts never overlap (one due while the other is open waits), and D23's Firestorm
 *                     waits out both (HoldBeats)
 *   Rule 10           his victim out of his reach 3 s (outside the clap's and the blast's windows and the walk back
 *                     after each): Magma Blast on it every 2 s, 20%
 *   The end           the kill: D23's JustDied (slot 18 DONE; the instance records BOSS_AVATAR and DATA_MOIRA_SAVED;
 *                     the cage breaks, Moira stands down); OnEnd(died) gives his corpse Dagran's look back and clears
 *                     the marks. A wipe or an evade: OnEnd(false) also unroots him and gives back his heroic health;
 *                     D23 cancels the registry shapes, despawns the stones, breaks the cage; the instance clears the
 *                     per-pull flag. A reload or a restart: nothing of this is saved (Moira saved is the instance's)
 *
 * Every firing logs one INFO line "brd emperor avatar-<mechanic> ..." (module.dungeonbosses, through D23's Log);
 * `.dbtest brd avatar <...>` fires them.
 */

#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitFlex.h"
#include "EmperorFight.h"
#include "EmperorHardModeLogic.h"
#include "EmperorLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "SpellDefines.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WorldSession.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdAvatar;
using BossMechanics::MechanicRef;
using BrdEmperor::EmperorFight;
using BrdEmperor::EmperorHardMode;
using BrdEmperor::Phase;

namespace
{
    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    // The floor under a point: the map's height within 6 yd of `refZ`, else `refZ`.
    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > 6.f)
            return refZ;
        return h;
    }

    // The throne: his home (the stock spawn), else the constant.
    Position ThroneOf(Creature const* boss)
    {
        Position const& home = boss->GetHomePosition();
        if (home.GetPositionX() == 0.f && home.GetPositionY() == 0.f)
            return Position(kThroneSpot.x, kThroneSpot.y, kThroneSpot.z, kThroneFacing);
        return home;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The Avatar of Ragnaros: one per hard mode attempt (D23 makes it at the lethal hit, drops it when the attempt ends).
// ---------------------------------------------------------------------------------------------------------------------
class AvatarOfRagnaros : public EmperorHardMode
{
public:
    // Step 2: the knockback, the jump to the throne, the transition's look.
    void OnAwaken(EmperorFight& fight) override
    {
        Creature* boss = fight.Dagran();
        _origDisplay = boss->GetDisplayId();
        _origHealth = boss->GetMaxHealth();     // his heroic pool (220k), given back on a wipe
        // The instance lit the loot bit at SetData(DATA_AVATAR, 1) a moment ago (rule 1: at the trigger); made sure of.
        DungeonKit::SetHardModeLoot(boss, true);

        float const fromX = boss->GetPositionX();
        float const fromY = boss->GetPositionY();
        float const speedXY = KnockbackSpeedXY(kKnockbackYd);
        uint32 thrown = 0;
        for (Player* player : fight.FightPlayers())
        {
            // Someone standing in his very spot is thrown along his facing.
            float x = fromX;
            float y = fromY;
            if (player->GetExactDist2d(fromX, fromY) < 0.5f)
            {
                x -= std::cos(boss->GetOrientation());
                y -= std::sin(boss->GetOrientation());
            }
            player->KnockbackFrom(x, y, speedXY, kKnockbackSpeedZ);
            ++thrown;
        }

        Position const throne = ThroneOf(boss);
        boss->CastSpell(throne.GetPositionX(), throne.GetPositionY(), throne.GetPositionZ(), SPELL_AV_AWAKENS_PILLAR,
            true);
        DungeonKit::JumpTo(boss, throne, kJumpSpeedXY, kJumpMinSpeedZ);
        fight.Log("avatar-awakens", Acore::StringFormat("thrown={} knock={:.0f}yd from=({:.1f}, {:.1f}) "
            "throne=({:.1f}, {:.1f}) moira-caged={}", thrown, kKnockbackYd, fromX, fromY, throne.GetPositionX(),
            throne.GetPositionY(), fight.MoiraCaged() ? 1 : 0));
    }

    // Step 3: the Avatar rises on the throne.
    void OnRise(EmperorFight& fight) override
    {
        Creature* boss = fight.Dagran();
        Position const throne = ThroneOf(boss);
        boss->GetMotionMaster()->Clear();
        boss->StopMoving();
        if (boss->GetExactDist2d(throne.GetPositionX(), throne.GetPositionY()) > kThroneSnapYd)
            boss->NearTeleportTo(throne.GetPositionX(), throne.GetPositionY(), throne.GetPositionZ(),
                throne.GetOrientation());
        boss->SetFacingTo(throne.GetOrientation());
        boss->SetDisplayId(kAvatarDisplay, kAvatarScale);
        boss->SetFloatValue(UNIT_FIELD_COMBATREACH, kAvatarReachYd);
        boss->SetControlled(true, UNIT_STATE_ROOT);
        DungeonKit::Flex::SetHealth(boss, kAvatarHealth, true);   // the kit idiom (R-2-C n3)
        boss->CastSpell(throne.GetPositionX(), throne.GetPositionY(), throne.GetPositionZ(), SPELL_AV_AWAKENS_ERUPTION,
            true);
        _risen = true;
        _clock.Rise(fight.FightMs());
        fight.Log("avatar-rises", Acore::StringFormat("health={} display={} scale={:.2f} reach={:.1f} clap={}s "
            "blast={}s", boss->GetMaxHealth(), kAvatarDisplay, kAvatarScale, kAvatarReachYd, kClapFirstMs / 1000,
            kBlastFirstMs / 1000));
    }

    void OnUpdate(EmperorFight& fight, uint32 /*diff*/) override
    {
        if (!_risen)
            return;
        uint64 const now = fight.FightMs();
        TrackMark(fight);

        if (_clapPending && now >= _clock.clapEndsAt)
            ResolveClap(fight);
        if (_blastPending && now >= _clock.blastEndsAt)
            ResolveBlast(fight);

        switch (_clock.Due(now))
        {
            case Cast::Clap:
                StartClap(fight, now);
                break;
            case Cast::Blast:
                StartBlast(fight, now, nullptr);
                break;
            default:
                break;
        }
        AnswerOutOfReach(fight, now);
    }

    // The policies stay D23's defaults: Firestorm continues (heroic values, 5 s after the rise), he swings at whoever
    // stands in his reach.

    // The Avatar phase's boss data: nothing to kick (Magma Clap is a must-play bar), nothing to dispel (the mark is a
    // marker, not dispellable); the shapes are the registry's. Nothing to add to D23's empty descriptor.
    void ConfigureDescriptor(EmperorFight& /*fight*/, BossMechanics::Descriptor& /*d*/) override { }

    // Death, evade or reset: his own look back (the corpse is Dagran's), the root and, on a wipe, his heroic health;
    // the marks off. D23 cancels the registry shapes and despawns the stones (Track / TrackSummon).
    void OnEnd(EmperorFight& fight, bool died) override
    {
        Creature* boss = fight.Dagran();
        if (_risen)
        {
            boss->SetControlled(false, UNIT_STATE_ROOT);
            if (_origDisplay)
                boss->SetDisplayId(_origDisplay);
            if (!died && _origHealth)
                DungeonKit::Flex::SetHealth(boss, _origHealth, true);
        }
        if (InstanceScript* instance = boss->GetInstanceScript())
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_AV_VOLCANIC_MARK);
        fight.Log("avatar-end", Acore::StringFormat("died={} risen={} claps={} blasts={} stones={} magma-blasts={}",
            died ? 1 : 0, _risen ? 1 : 0, _claps, _blasts, _stones, _magmaBlasts));
        _risen = false;
        _clapPending = false;
        _blastPending = false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd avatar` entry points
    // ----------------------------------------------------------------------------------------------------------------

    bool Risen() const
    {
        return _risen;
    }

    // Magma Clap now (false: a cast's window is open).
    bool TestClap(EmperorFight& fight)
    {
        uint64 const now = fight.FightMs();
        if (!_risen || _clock.ClapOpen(now) || _clock.BlastOpen(now))
            return false;
        _clock.clapAt = now;
        StartClap(fight, now);
        return true;
    }

    // Volcanic Blast now on `on` (nullptr: a random player).
    bool TestBlast(EmperorFight& fight, Player* on)
    {
        uint64 const now = fight.FightMs();
        if (!_risen || _clock.ClapOpen(now) || _clock.BlastOpen(now))
            return false;
        _clock.blastAt = now;
        return StartBlast(fight, now, on);
    }

    // A Volcanic Stone under `at` now.
    void TestStone(EmperorFight& fight, Position const& at)
    {
        PlaceStone(fight, at);
    }

    // Rule 10's answer now on `on`.
    void TestMagmaBlast(EmperorFight& fight, Unit* on)
    {
        CastMagmaBlast(fight, on);
    }

    std::string TestState(EmperorFight& fight) const
    {
        uint64 const now = fight.FightMs();
        auto left = [now](uint64 at) -> std::string
        {
            return at ? std::to_string(at > now ? (at - now) / 1000 : 0) + "s" : "-";
        };
        return Acore::StringFormat("avatar risen={} clap={}{} blast={}{} out-of-reach={} claps={} blasts={} stones={} "
            "magma-blasts={}", _risen ? 1 : 0, left(_clock.clapAt), _clapPending ? " (casting)" : "",
            left(_clock.blastAt), _blastPending ? " (marked)" : "",
            _clock.outOfReachSince ? std::to_string((now - _clock.outOfReachSince) / 1000) + "s" : "-", _claps,
            _blasts, _stones, _magmaBlasts);
    }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // EM12 Magma Clap
    // ----------------------------------------------------------------------------------------------------------------

    void StartClap(EmperorFight& fight, uint64 now)
    {
        Creature* boss = fight.Dagran();
        GuidSet everyone;
        float dz = 0.f;
        for (Player* player : fight.FightPlayers())
        {
            everyone.insert(player->GetGUID());
            dz = std::max(dz, std::fabs(player->GetPositionZ() - boss->GetPositionZ()));
        }
        if (!everyone.empty())
        {
            BossMechanics::Eligibility who;
            who.carriers = everyone;
            MechanicRef ref = Mechanic::RunOut(boss, nullptr, kClapRunOutYd, Ms(kClapCastMs));
            ref.Targets(everyone).From(BossMechanics::MeasuredFrom::Owner).Eligible(who).ZTolerance(dz + 5.f)
                .Tag(TAG_AV_MAGMA_CLAP);
            if (ref.IsValid())
                fight.Track(ref.Handle());
        }
        DungeonKit::CastBar(boss, SPELL_AV_MAGMA_CLAP_CAST, nullptr, BrdEmperor::EMOTE_EM_MAGMA_CLAP);
        _clock.ClapStarted(now);
        _clapPending = true;
        fight.HoldBeats(_clock.clapEndsAt + kBetweenCastsMs);
        fight.Log("avatar-magma-clap", Acore::StringFormat("players={} cast={}s runout={:.0f}yd near={:.0f}% "
            "far={:.0f}%", everyone.size(), kClapCastMs / 1000, kClapRunOutYd, kClapNearPct, kClapFarPct));
    }

    // The clap lands: everyone of the fight by distance from him (the tank row on the tank).
    void ResolveClap(EmperorFight& fight)
    {
        _clapPending = false;
        Creature* boss = fight.Dagran();
        boss->CastSpell(boss, SPELL_AV_MAGMA_CLAP_RING, true);
        std::string detail;
        uint32 hit = 0;
        for (Player* player : fight.FightPlayers())
        {
            float const distance = boss->GetExactDist2d(player);
            float const pct = MagmaClapPct(distance);
            uint32 const amount = DungeonKit::RefFlatOn(boss, player, pct);
            if (!amount)
                continue;
            boss->CastCustomSpell(SPELL_AV_MAGMA_CLAP, SPELLVALUE_BASE_POINT0, static_cast<int32>(amount), player,
                true);
            ++hit;
            detail += Acore::StringFormat(" {}:{:.0f}yd/{:.0f}%", player->GetName(), distance, pct);
        }
        ++_claps;
        fight.Log("avatar-magma-clap-hit", Acore::StringFormat("hit={}{}", hit, detail));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM13 Volcanic Blast, the Volcanic Stone
    // ----------------------------------------------------------------------------------------------------------------

    // A player (the tank too) marked 5 s. False: nobody to mark.
    bool StartBlast(EmperorFight& fight, uint64 now, Player* forced)
    {
        Creature* boss = fight.Dagran();
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;       // ruling 88: the tank too
            target = DungeonKit::PickPlayer(boss, rule);
        }
        if (!target)
            return false;
        boss->CastSpell(target, SPELL_AV_VOLCANIC_MARK, true);
        if (boss->IsAIEnabled)
            boss->AI()->Talk(BrdEmperor::EMOTE_EM_VOLCANIC_BLAST, target);
        MechanicRef ref = Mechanic::Stack(boss, target, kBlastRadiusYd, Ms(kBlastMarkMs));
        ref.ZTolerance(kBlastZBandYd).Tag(TAG_AV_VOLCANIC_BLAST);
        if (ref.IsValid())
            fight.Track(ref.Handle());
        _marked = target->GetGUID();
        _markAt = target->GetPosition();
        _clock.BlastStarted(now);
        _blastPending = true;
        fight.HoldBeats(_clock.blastEndsAt + kBetweenCastsMs);
        fight.Log("avatar-volcanic-blast", Acore::StringFormat("on={} mark={}s radius={:.0f}yd total={:.0f}%",
            target->GetName(), kBlastMarkMs / 1000, kBlastRadiusYd, kBlastTotalPct));
        return true;
    }

    // The mark's last known spot (the stone lands there when the marked player is gone).
    void TrackMark(EmperorFight& fight)
    {
        if (!_blastPending || !_marked)
            return;
        if (Player* marked = ObjectAccessor::GetPlayer(*fight.Dagran(), _marked))
            if (marked->IsInWorld() && marked->GetMap() == fight.Dagran()->GetMap())
                _markAt = marked->GetPosition();
    }

    // The blast lands: 80% split among everyone within 8 yd of the mark, then the stone.
    void ResolveBlast(EmperorFight& fight)
    {
        _blastPending = false;
        TrackMark(fight);
        Creature* boss = fight.Dagran();
        Player* marked = ObjectAccessor::GetPlayer(*boss, _marked);
        if (marked)
            marked->RemoveAurasDueToSpell(SPELL_AV_VOLCANIC_MARK, boss->GetGUID());

        DungeonKit::Vec2 const at{ _markAt.GetPositionX(), _markAt.GetPositionY() };
        std::vector<Unit*> takers;
        for (Player* player : fight.FightPlayers())
            if (std::fabs(player->GetPositionZ() - _markAt.GetPositionZ()) <= kBlastZBandYd
                && DungeonKit::Distance(at, DungeonKit::PlaneOf(player)) <= kBlastRadiusYd)
                takers.push_back(player);
        // The marked player always takes a share (a game master testing it too).
        if (marked && marked->IsAlive() && std::find(takers.begin(), takers.end(), marked) == takers.end())
            takers.push_back(marked);

        std::vector<std::pair<ObjectGuid, uint32>> const shares = DungeonKit::SplitShares(boss, takers,
            kBlastTotalPct);
        std::string detail;
        for (std::size_t i = 0; i < takers.size() && i < shares.size(); ++i)
        {
            detail += Acore::StringFormat(" {}:{}", takers[i]->GetName(), shares[i].second);
            if (shares[i].second)
                boss->CastCustomSpell(SPELL_AV_VOLCANIC_BLAST, SPELLVALUE_BASE_POINT0,
                    static_cast<int32>(shares[i].second), takers[i], true);
        }
        ++_blasts;
        fight.Log("avatar-volcanic-blast-hit", Acore::StringFormat("takers={} share={:.1f}%{}", takers.size(),
            BlastSharePct(takers.size()), detail));
        PlaceStone(fight, _markAt);
        _marked.Clear();
    }

    // A Volcanic Stone: the 5 yd lava pool look on a stalker for 30 s, and the registry's burning Zone under it. It
    // lands at the mark's spot, pushed out of the Avatar's melee ring (StoneSpot); a push that leaves his arena (the
    // throne wall behind him) goes in front of him instead.
    void PlaceStone(EmperorFight& fight, Position const& where)
    {
        Creature* boss = fight.Dagran();
        Vec2 const avatar{ boss->GetPositionX(), boss->GetPositionY() };
        Vec2 const mark{ where.GetPositionX(), where.GetPositionY() };
        Vec2 spot = StoneSpot(avatar, boss->GetOrientation(), mark);
        float spotZ = GroundZ(boss, spot.x, spot.y, where.GetPositionZ());
        DungeonKit::Arena const arena = EmperorArena();
        if (!arena.Contains(spot, spotZ))
        {
            spot = StoneSpot(avatar, boss->GetOrientation(), avatar);
            spotZ = GroundZ(boss, spot.x, spot.y, where.GetPositionZ());
        }
        if (spot.x != mark.x || spot.y != mark.y)
            fight.Log("avatar-volcanic-stone-pushed", Acore::StringFormat("mark=({:.1f}, {:.1f}) ring={:.1f}yd",
                mark.x, mark.y, AvatarMeleeRingYd()));
        Position const at(spot.x, spot.y, spotZ, 0.f);
        if (TempSummon* stalker = boss->SummonCreature(NPC_BRD_STALKER, at, TEMPSUMMON_TIMED_DESPAWN, kStoneMs))
        {
            stalker->CastSpell(stalker, SPELL_AV_VOLCANIC_STONE_LOOK, true);
            fight.TrackSummon(stalker);
        }
        DungeonKit::LingerSpec stone;
        stone.duration = Ms(kStoneMs);
        stone.tick = Ms(kStoneTickMs);
        stone.pct = kStonePct;
        stone.school = SPELL_SCHOOL_FIRE;
        stone.spellId = SPELL_AV_VOLCANIC_STONE;
        stone.slow = false;
        stone.tag = TAG_AV_VOLCANIC_STONE;
        MechanicRef ref = DungeonKit::Linger(boss, BossMechanics::Shapes::Circle(at, kStoneRadiusYd), stone);
        if (ref.IsValid())
            fight.Track(ref.Handle());
        ++_stones;
        fight.Log("avatar-volcanic-stone", Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) radius={:.0f}yd for={}s "
            "pct={:.0f}/s", at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), kStoneRadiusYd, kStoneMs / 1000,
            kStonePct));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rule 10: the rooted Avatar answers a victim out of his reach
    // ----------------------------------------------------------------------------------------------------------------

    void AnswerOutOfReach(EmperorFight& fight, uint64 now)
    {
        Creature* boss = fight.Dagran();
        Unit* victim = boss->GetVictim();
        if (!victim)
            return;
        bool const inReach = boss->IsWithinMeleeRange(victim);
        if (_clock.MagmaBlastDue(now, inReach, _clock.ReachGrace(now)))
            CastMagmaBlast(fight, victim);
    }

    void CastMagmaBlast(EmperorFight& fight, Unit* on)
    {
        if (!on)
            return;
        Creature* boss = fight.Dagran();
        if (boss->CastSpell(on, SPELL_AV_MAGMA_BLAST, true) != SPELL_CAST_OK)
            return;
        ++_magmaBlasts;
        fight.Log("avatar-magma-blast", Acore::StringFormat("on={} range={:.1f}yd pct={:.0f}", on->GetName(),
            boss->GetExactDist2d(on), kMagmaBlastPct));
    }

    AvatarClock _clock;
    ObjectGuid _marked;
    Position _markAt;
    uint32 _origDisplay = 0;
    uint32 _origHealth = 0;
    uint32 _claps = 0;
    uint32 _blasts = 0;
    uint32 _stones = 0;
    uint32 _magmaBlasts = 0;
    bool _risen = false;
    bool _clapPending = false;
    bool _blastPending = false;
};

namespace
{
    // The Emperor running D23's AI (the hard mode's host), or an error.
    EmperorFight* FindFight(ChatHandler* handler, Creature*& boss)
    {
        boss = BrdTest::FindBoss(handler, NPC_EMPEROR);
        if (!boss)
            return nullptr;
        auto* fight = boss->IsAIEnabled ? dynamic_cast<EmperorFight*>(boss->AI()) : nullptr;
        if (!fight)
            handler->SendErrorMessage("{}", "Emperor Dagran Thaurissan is not running "
                "boss_emperor_dagran_thaurissan_rework (wave 2 binds it).");
        return fight;
    }

    // The risen Avatar of this attempt, or an error.
    AvatarOfRagnaros* FindAvatar(ChatHandler* handler, EmperorFight*& fight)
    {
        Creature* boss = nullptr;
        fight = FindFight(handler, boss);
        if (!fight)
            return nullptr;
        auto* avatar = dynamic_cast<AvatarOfRagnaros*>(fight->ActiveHardMode());
        if (!avatar || !avatar->Risen() || fight->CurrentPhase() != Phase::Avatar)
        {
            handler->SendErrorMessage("{}", "The Avatar has not risen (on heroic, bring Dagran to 0 while Moira "
                "stands: `.dbtest brd avatar awaken`).");
            return nullptr;
        }
        return avatar;
    }

    Player* Gm(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowHardModeInfo(handler, "avatar", DATA_AVATAR, BOSS_AVATAR);
    }

    // `.dbtest brd avatar awaken`: Dagran first, now: a hit for his whole health from the GM (D23's lethal branch
    // holds it at 1 and the transition starts on his next tick). Heroic, in the court phase, Moira standing.
    bool HandleAwaken(ChatHandler* handler)
    {
        Creature* boss = nullptr;
        EmperorFight* fight = FindFight(handler, boss);
        if (!fight)
            return false;
        if (!DungeonKit::IsHeroicMap(boss))
        {
            handler->SendErrorMessage("{}", "The Avatar is heroic only: on normal, Dagran first ends the fight.");
            return false;
        }
        if (!boss->IsInCombat() || fight->CurrentPhase() != Phase::Court)
        {
            handler->SendErrorMessage("{}", "Pull him first; the branch needs the court phase (Moira standing).");
            return false;
        }
        Unit::DealDamage(Gm(handler), boss, boss->GetHealth(), nullptr, DIRECT_DAMAGE, SPELL_SCHOOL_MASK_NORMAL,
            nullptr, false, true, nullptr, true);
        handler->PSendSysMessage("avatar: Dagran took {} (alive: {}); the transition starts on his next tick.",
            boss->GetMaxHealth(), boss->IsAlive() ? "yes" : "no");
        return true;
    }

    bool HandleState(ChatHandler* handler)
    {
        EmperorFight* fight = nullptr;
        AvatarOfRagnaros* avatar = FindAvatar(handler, fight);
        if (!avatar)
            return false;
        handler->PSendSysMessage("{}", avatar->TestState(*fight));
        return true;
    }

    // `.dbtest brd avatar clap`: EM12 now.
    bool HandleClap(ChatHandler* handler)
    {
        EmperorFight* fight = nullptr;
        AvatarOfRagnaros* avatar = FindAvatar(handler, fight);
        if (!avatar)
            return false;
        bool const ok = avatar->TestClap(*fight);
        handler->PSendSysMessage("avatar: Magma Clap {}.", ok ? "starts (3 s)" : "waits (a cast's window is open)");
        return ok;
    }

    // `.dbtest brd avatar blast`: EM13 now, on the GM.
    bool HandleBlast(ChatHandler* handler)
    {
        EmperorFight* fight = nullptr;
        AvatarOfRagnaros* avatar = FindAvatar(handler, fight);
        if (!avatar)
            return false;
        bool const ok = avatar->TestBlast(*fight, Gm(handler));
        handler->PSendSysMessage("avatar: Volcanic Blast {}.", ok ? "on you (5 s)" : "waits (a cast's window is open)");
        return ok;
    }

    // `.dbtest brd avatar stone`: a Volcanic Stone under the GM.
    bool HandleStone(ChatHandler* handler)
    {
        EmperorFight* fight = nullptr;
        AvatarOfRagnaros* avatar = FindAvatar(handler, fight);
        Player* gm = Gm(handler);
        if (!avatar || !gm)
            return false;
        avatar->TestStone(*fight, gm->GetPosition());
        handler->PSendSysMessage("{}", "avatar: a Volcanic Stone under you (30 s).");
        return true;
    }

    // `.dbtest brd avatar magma`: rule 10's Magma Blast on the GM now.
    bool HandleMagma(ChatHandler* handler)
    {
        EmperorFight* fight = nullptr;
        AvatarOfRagnaros* avatar = FindAvatar(handler, fight);
        if (!avatar)
            return false;
        avatar->TestMagmaBlast(*fight, Gm(handler));
        handler->PSendSysMessage("{}", "avatar: Magma Blast at you.");
        return true;
    }

    ChatCommandTable const& AvatarTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "awaken", HandleAwaken, SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "clap",   HandleClap,   SEC_GAMEMASTER, Console::No },
            { "blast",  HandleBlast,  SEC_GAMEMASTER, Console::No },
            { "stone",  HandleStone,  SEC_GAMEMASTER, Console::No },
            { "magma",  HandleMagma,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_brd_emperor_hard_mode()
{
    // D23 asks for an Avatar only on a heroic lethal hit with Moira standing (and only once wave 2 binds him), so the
    // factory registers now: until then nothing calls it.
    BrdEmperor::RegisterEmperorHardMode([](Creature*) { return std::make_unique<AvatarOfRagnaros>(); });
    BrdTest::RegisterBoss("avatar", AvatarTestCommands());
}
