/*
 * mod-dungeon-bosses, Gnomeregan D5: Crowd Pummeler 9-60 (6229) in the glass window, normal and heroic. Build spec:
 * SP 1226-1437 (CP1-CP8, Build spec 1388), rulings 31-36 and 65 under the window ruling (handoff section 10: he floats
 * in the green glass window at kPummelerSpot, about 4.8 yd under the pocket floor, scale 5); handoff section 3.5 row D5
 * and rules 1-38 (rule 33 the window), sections 3.6, 3.8 (the pocket and its frame), 3.9 row 7 and G, section 7
 * #23 A, #27 A (reach 10), #28 A (the frame), #29 A (the death line), #36 A to #38 A. Replaces SmartAI 6229 (dropped by
 * rev_skeleton_gnomeregan.sql: Arcing Smash, Trample and Crowd Pummel on timers). Bound by apps/dbc-tools
 * source/npcs/gnomeregan/crowd_pummeler.py; numbers in CrowdPummelerLogic.h, health in GnomereganRework.h Health; the
 * combination is the ComboMachine (CrowdPummelerMachine.{h,cpp}) on the pocket frame; the texts and his chest's
 * templates are data/sql/updates/pending_db_world/rev_crowd_pummeler_gnomeregan.sql. The instance places the chest at
 * slot 4's DONE (S0 Q1); nothing here touches loot.
 *
 *   The window      gravity off, rooted by SetControlled (never a root aura: mask 1972), rotation locked
 *                   (DisableRotate, the Kologarn pattern boss_kologarn.cpp:169-170), no combat movement; display 6774
 *                   at scale 5 by SetDisplayId(id, scale) in one call; the combat reach and bounding radius of
 *                   WindowReach() re-set whenever the engine rewrote them (every tick: a scale aura, a morph, a
 *                   display change all go through Creature::SetObjectScale); put back on his spot if he drifts; at
 *                   death no fall (UNIT_FLAG_DISABLE_MOVE on the killing blow keeps MotionMaster::MoveFall out, then
 *                   gravity off again on the spot). Damage from outside the pocket box is 0 and a pull from outside it
 *                   evades at once; the arena leash (PummelerArena: the pocket plus his spot) resets him 10 s after
 *                   the group leaves.
 *   CP1-CP7         every 18 s after the last punch (first at 10 s) a combination: emote line 0, a 1 s call flash per
 *                   punch in order, then each punch's live marker (1.5 s; heroic 0.8 s) and strike 2 s apart (heroic
 *                   1.2 s); no melee and no Trample while it runs. Normal: 2, 3, 4 punches by round, the bell at 66%
 *                   and 33%. Heroic: 3, +1 each combination, +1 per punch that landed, no cap; Uppercut and Clinch;
 *                   the One-Two from the fourth punch. Each punch 40% / 60% plus Weakened, the tank included; Crowd
 *                   Pummel knocks back 7.5 yd south, Uppercut knocks up. The pose: a cast bar over each live marker
 *                   (SV 90752's punch precast) and the AttackUnarmed emote at the strike.
 *   CP8 Trample     8% / 12% to everyone on the near side (12 yd from the frame origin) every 10 s from 6 s, and at
 *                   once when no player has been in his melee reach for 1.5 s; the ground slam ring on the frame
 *                   stalker.
 *   Bots and pets   the ranged band 19 to 26 yd past the hunters' too-close line (R-1-B M1); players' melee pets
 *                   chase him without PetAI's angle to his back, the glass (R-1-B M2, KeepPetsOffTheGlass).
 *
 * Every firing logs one INFO line "gnomer-build pummeler <mechanic> ..."; `.dbtest gnomer pummeler info | state |
 * window | combo [length] | trample | round <2|3>` (the README's rows).
 *
 * Mirrored stock code (AGENTS.md credit rule): none. The window's movement calls follow boss_kologarn.cpp (a pattern,
 * not copied code); the stock SmartAI rows are replaced, not ported.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CrowdPummelerLogic.h"
#include "CrowdPummelerMachine.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameTime.h"
#include "GnomereganKit.h"
#include "GnomereganRework.h"
#include "GnomereganTestCommand.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "PassiveAI.h"
#include "Pet.h"
#include "PetAI.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <cmath>
#include <memory>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace GnomereganRework;
using namespace GnomerPummeler;
using BossMechanics::MechanicHandle;

namespace
{
    char const* const kBossKey = "pummeler";
    uint8 constexpr kSchoolPhysical = 0;            // SPELL_SCHOOL_NORMAL
    // Damage refused from outside the pocket: one line per this long.
    uint32 constexpr kFilterLogMs = 5000;

    void PummelerLog(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossKey, mechanic, detail);
    }

    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    bool InThePocket(WorldObject const* o)
    {
        return o && FromThePocket(o->GetPositionX(), o->GetPositionY(), o->GetPositionZ());
    }

    Position SpotPosition()
    {
        return Position(kPummelerSpot.x, kPummelerSpot.y, kPummelerSpot.z, kPummelerSpot.o);
    }

    GnomereganMachines::Punch ToMachine(PunchRoll const& roll)
    {
        GnomereganMachines::Punch p;
        p.shape = static_cast<GnomereganMachines::PunchShape>(roll.shape);
        if (roll.paired)
            p.paired = static_cast<GnomereganMachines::PunchShape>(*roll.paired);
        return p;
    }

    std::string ChainText(std::vector<PunchRoll> const& chain)
    {
        std::string out;
        for (PunchRoll const& p : chain)
        {
            if (!out.empty())
                out += ",";
            out += ShapeName(p.shape);
            if (p.paired)
                out += std::string("+") + ShapeName(*p.paired);
        }
        return out;
    }

    // CP4 and CP5's riders, inside the punch's resolve (no registration here, rule 11): Crowd Pummel knocks the
    // player 7.5 yd due south (along the frame, from a point just north of them: never into the glass); Uppercut
    // straight up.
    void Knock(Player* player, GnomereganMachines::PunchShape shape)
    {
        if (!player || !player->IsAlive())
            return;
        if (shape == GnomereganMachines::PunchShape::Near)
        {
            float const facing = kPummelerFrameOrigin.o;
            player->KnockbackFrom(player->GetPositionX() - std::cos(facing), player->GetPositionY() - std::sin(facing),
                Tune::kPummelKnockSpeedXY, Tune::kPummelKnockSpeedZ);
        }
        else if (shape == GnomereganMachines::PunchShape::Lane)
            player->KnockbackFrom(player->GetPositionX(), player->GetPositionY(), 0.f, Tune::kUppercutKnockSpeedZ);
    }

    // The pocket frame for the machine (section 7 #28 A), its numbers from Tune (normal or heroic).
    GnomereganMachines::ComboSpec PocketComboSpec(bool heroic)
    {
        GnomereganMachines::ComboSpec spec;
        Point3 const& o = kPummelerFrameOrigin;
        spec.frame.origin = Position(o.x, o.y, o.z, o.o);
        spec.frame.halfReachYd = Tune::kHalfReachYd;
        spec.frame.nearRadiusYd = Tune::kNearRadiusYd;
        spec.frame.farOuterYd = Tune::kFarOuterYd;
        spec.frame.laneWidthYd = Tune::kLaneWidthYd;
        spec.frame.laneLengthYd = Tune::kLaneLengthYd;
        spec.frame.floor = PocketArena();
        spec.callFlashMs = Tune::kCallMs;
        spec.windUpMs = 0;
        spec.markerMs = Tune::kLiveMs.Get(heroic);
        spec.gapMs = Tune::kApartMs.Get(heroic);
        spec.drawAllAtOnce = false;
        spec.pct.fill(Tune::kPunchPct.Get(heroic));
        spec.weakened = true;
        spec.callEmoteGroup = EMOTE_COMBINATION;
        return spec;
    }

    GnomereganMachines::ComboExtras PocketComboExtras(bool heroic)
    {
        GnomereganMachines::ComboExtras extras;
        // By PunchShape: LeftHalf, RightHalf, Near, Far, Lane.
        extras.spellIds = { SPELL_LEFT_HOOK, SPELL_RIGHT_HOOK, SPELL_CROWD_PUMMEL, SPELL_CLINCH, SPELL_UPPERCUT };
        extras.tags = { TAG_LEFT_HOOK, TAG_RIGHT_HOOK, TAG_CROWD_PUMMEL, TAG_CLINCH, TAG_UPPERCUT };
        extras.names = kShapeNames;
        extras.school = kSchoolPhysical;
        extras.rider = SPELL_SEEING_STARS;
        extras.callColor = BossMechanics::Color::Yellow;
        uint32 const bar = heroic ? uint32(SPELL_PUNCH_BAR_H) : uint32(SPELL_PUNCH_BAR);
        // The pose over each live marker (the bar is as long as the marker; it never stops anything).
        extras.onLive = [bar](Creature* owner, uint32 /*index*/, GnomereganMachines::Punch const& /*punch*/,
            uint32 /*untilStrikeMs*/)
        {
            if (owner && owner->IsAlive() && !owner->HasUnitState(UNIT_STATE_CASTING))
                owner->CastSpell(owner, bar, false);
        };
        extras.onStrike = [](Creature* owner, uint32 /*index*/, GnomereganMachines::Punch const& /*punch*/)
        {
            if (owner && owner->IsAlive())
                owner->HandleEmoteCommand(kPunchEmote);
        };
        extras.onHit = [](Player* player, GnomereganMachines::PunchShape shape) { Knock(player, shape); };
        return extras;
    }
}

// The frame stalker 301115: the invisible point at the frame origin the Trample ring plays on (he floats under the
// floor, so a ring at his own feet would be under it). Inert.
struct npc_gnomer_pummeler_frame : public NullCreatureAI
{
    explicit npc_gnomer_pummeler_frame(Creature* creature) : NullCreatureAI(creature) { }
};

// Crowd Pummeler 9-60 6229
struct boss_crowd_pummeler_rework : public BossAI
{
    explicit boss_crowd_pummeler_rework(Creature* creature)
        : BossAI(creature, BOSS_CROWD_PUMMELER), _arena(PummelerArena(), LeashOptions(kBossKey)) { }

    void Reset() override
    {
        _Reset();
        Cleanup("reset");
        me->RemoveUnitFlag(UNIT_FLAG_DISABLE_MOVE);
        me->SetCombatMovement(false);
        me->SetHomePosition(SpotPosition());
        // Rule 4: the display and its scale in one call (the scale survives a scale aura's end and a morph's end:
        // RecalculateObjectScale starts from it). The reach follows (rule 33).
        me->SetDisplayId(kDisplayPummeler, Tune::kWindowScale);
        HoldTheWindow("reset");
    }

    // Damage only from the pocket (row D5: the lower room 44 yd down and the corridors deal nothing), and no fall at
    // death: the killing blow sets UNIT_FLAG_DISABLE_MOVE before Unit::Kill, so Creature::setDeathState's MoveFall
    // returns at once (MotionMaster.cpp MoveFall).
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*school*/) override
    {
        if (attacker && attacker != me && !InThePocket(attacker))
        {
            if (damage && _now >= _filterLogAt)
            {
                _filterLogAt = _now + kFilterLogMs;
                PummelerLog("damage-filtered", Acore::StringFormat("attacker={} at=({:.1f}, {:.1f}, {:.1f}) damage={}",
                    attacker->GetName(), attacker->GetPositionX(), attacker->GetPositionY(), attacker->GetPositionZ(),
                    damage));
            }
            damage = 0;
            return;
        }
        if (damage >= me->GetHealth())
            me->SetUnitFlag(UNIT_FLAG_DISABLE_MOVE);
    }

    // Never a victim under the pocket floor (LESSONS A.2 #12): the lower room sees him but is never his fight.
    bool CanAIAttack(Unit const* target) const override
    {
        return target && VictimAllowed(target->GetPositionZ());
    }

    void JustEngagedWith(Unit* who) override
    {
        // Pull only from the pocket (row D5).
        if (!InThePocket(who))
        {
            PummelerLog("pull-refused", Acore::StringFormat("who={} at=({:.1f}, {:.1f}, {:.1f})",
                who ? who->GetName() : "-", who ? who->GetPositionX() : 0.f, who ? who->GetPositionY() : 0.f,
                who ? who->GetPositionZ() : 0.f));
            EnterEvadeMode(EVADE_REASON_OTHER);
            return;
        }
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup("pull");    // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        _comboAt = Tune::kComboFirstMs;
        _trampleAt = Tune::kTrampleFirstMs;
        _trampleNotBefore = Tune::kTrampleFirstMs;  // nor the "nobody in reach" one while the group walks in
        _round = 1;

        GnomereganMachines::MachineOwner owner;
        owner.owner = me;
        owner.logKey = kBossKey;
        owner.heroic = _heroic;
        _combo = GnomereganMachines::MakeComboMachine(owner, PocketComboSpec(_heroic), PocketComboExtras(_heroic));

        OnBossPull(me, kBossKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_CROWD_PUMMELER;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        SummonFrameStalker();
        PummelerLog("engage", Acore::StringFormat("heroic={} who={} reach={:.2f} scale={:.2f} melee_floor={:.1f} "
            "hunter_too_close={:.1f}", _heroic ? 1 : 0, who ? who->GetName() : "-", me->GetCombatReach(),
            me->GetObjectScale(), MeleeFloorReach(me->GetCombatReach()), HunterTooCloseFloor(me->GetCombatReach())));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        PummelerLog("evade", Acore::StringFormat("reason={} combos={} landed={}", uint32(why), _combos, _landed));
        Cleanup("evade");
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        PummelerLog("death", Acore::StringFormat("heroic={} combos={} landed={} round={}", _heroic ? 1 : 0, _combos,
            _landed, _round));
        Cleanup("death");
        Talk(EMOTE_DEATH);
        BossAI::JustDied(killer);   // slot 4 DONE: the instance places the chest (S0 Q1); never loot here (rule 1)
        KeepTheBody();
    }

    // The frame stalker stays out of BossAI's zone-in-combat (an inert helper); Cleanup despawns it.
    void JustSummoned(Creature* summon) override
    {
        if (summon && summon->GetEntry() == NPC_FRAME_STALKER)
        {
            _stalker = summon->GetGUID();
            summon->SetReactState(REACT_PASSIVE);
            return;
        }
        BossAI::JustSummoned(summon);
    }

    void DoAction(int32 action) override
    {
        if (!_engaged)
            return;
        switch (action)
        {
            case ACTION_TEST_COMBO:
                _comboAt = _now;
                break;
            case ACTION_TEST_TRAMPLE:
                _trampleAt = _now;
                _trampleNotBefore = _now;
                break;
            case ACTION_TEST_ROUND_TWO:
                Bell(2, "test");
                break;
            case ACTION_TEST_FINAL_ROUND:
                Bell(3, "test");
                break;
            default:
                break;
        }
    }

    void SetData(uint32 id, uint32 value) override
    {
        if (id == DATA_TEST_COMBO_LENGTH)
            _testLength = value;
    }

    uint32 GetData(uint32 id) const override
    {
        switch (id)
        {
            case DATA_TEST_ENGAGED:
                return _engaged ? 1 : 0;
            case DATA_TEST_COMBO_LENGTH:
                return _lastLength;
            case DATA_TEST_COMBOS:
                return _combos;
            case DATA_TEST_LANDED:
                return _landed;
            case DATA_TEST_ROUND:
                return _round;
            default:
                return 0;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        GnomereganRework::NoAssist(me);     // rule 29, LESSONS L1: every tick, before UpdateVictim
        HoldTheWindow(nullptr);             // rule 33: every tick, in and out of combat
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        // The fight clock and the machine move every tick, cast bar or not (L8).
        _now += diff;
        KeepPetsOffTheGlass();      // before the combination's early return: pets chase through it too
        if (_combo)
            _combo->Update(diff);
        CheckRounds();
        if (_comboRunning)
        {
            if (_combo && _combo->Running())
                return;     // CP1: no melee and no Trample while it runs
            EndCombination();
        }
        if (_now >= _comboAt && StartCombination())
            return;
        CheckReach(diff);
        if (_now >= _trampleAt && _now >= _trampleNotBefore)
            Trample("timer");
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- `.dbtest gnomer pummeler` ---------------------------------------------------------------------------------

    std::string TestState() const
    {
        return Acore::StringFormat("engaged={} heroic={} now={}ms round={} combos={} landed={} next_combo={}ms "
            "next_trample={}ms last_length={} pet_chase_fixes={} machine: {}", _engaged ? 1 : 0, _heroic ? 1 : 0, _now,
            _round, _combos, _landed, _comboAt > _now ? _comboAt - _now : 0, _trampleAt > _now ? _trampleAt - _now : 0,
            _lastLength, _petChaseFixes, _combo ? _combo->Describe() : std::string("none"));
    }

    std::string TestFire(int32 action, uint32 length)
    {
        if (!_engaged)
            return "Pull him first (the mechanics run in combat only).";
        if (action == ACTION_TEST_COMBO && _comboRunning)
            return "A combination is running.";
        if ((action == ACTION_TEST_ROUND_TWO || action == ACTION_TEST_FINAL_ROUND) && _heroic)
            return "Heroic has no rounds.";
        if (action == ACTION_TEST_COMBO)
            _testLength = length;
        DoAction(action);
        return {};
    }

private:
    // ---- the window (section 10, rule 33) --------------------------------------------------------------------------

    // Gravity off, the root, the rotation lock and the reach, re-asserted whenever something undid them (an evade's
    // home move clears unit states; Creature::SetObjectScale rewrites the reach); back on his spot if he drifted.
    // `why` (non-null at Reset) logs every time; a tick logs only what it fixed.
    void HoldTheWindow(char const* why)
    {
        if (!me->IsAlive())
            return;
        std::string fixed;
        if (!me->HasUnitMovementFlag(MOVEMENTFLAG_DISABLE_GRAVITY))
        {
            me->SetDisableGravity(true);
            fixed += " gravity";
        }
        if (!me->HasUnitState(UNIT_STATE_ROOT))
        {
            me->SetControlled(true, UNIT_STATE_ROOT);
            fixed += " root";
        }
        if (!me->HasUnitFlag(UNIT_FLAG_POSSESSED))
        {
            me->DisableRotate(true);
            fixed += " rotate";
        }
        float const reach = WindowReach(me->GetObjectScale());
        if (ReachNeedsReset(me->GetCombatReach(), reach) || ReachNeedsReset(me->GetBoundaryRadius(), reach))
        {
            float const was = me->GetCombatReach();
            me->SetFloatValue(UNIT_FIELD_COMBATREACH, reach);
            me->SetFloatValue(UNIT_FIELD_BOUNDINGRADIUS, reach);
            fixed += Acore::StringFormat(" reach {:.2f}->{:.2f}", was, reach);
        }
        uint64 const nowMs = uint64(GameTime::GetGameTimeMS().count());
        if (me->IsInWorld() && me->GetExactDist(kPummelerSpot.x, kPummelerSpot.y, kPummelerSpot.z) > Tune::kSpotDriftYd
            && nowMs >= _replacedAtMs + Tune::kReplaceEveryMs)
        {
            _replacedAtMs = nowMs;
            Position const spot = SpotPosition();
            fixed += Acore::StringFormat(" spot (drifted {:.1f} yd)", me->GetExactDist(&spot));
            me->NearTeleportTo(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), spot.GetOrientation());
        }
        // A fix the engine undoes every tick (a heroic copy without its movement row: Creature::UpdateMovementFlags
        // turns gravity back on) logs once per kReplaceEveryMs, with the count since the last line.
        if (!why && !fixed.empty())
        {
            ++_windowFixes;
            if (nowMs < _windowLogAtMs + Tune::kReplaceEveryMs)
                return;
        }
        if (why || !fixed.empty())
        {
            _windowLogAtMs = nowMs;
            PummelerLog("window", Acore::StringFormat("why={} fixed={} fixes={} scale={:.2f} reach={:.2f}",
                why ? why : "tick", fixed.empty() ? " none" : fixed, _windowFixes, me->GetObjectScale(),
                me->GetCombatReach()));
            _windowFixes = 0;
        }
    }

    // At death the body stays in the glass (section 10: gravity stays off; the floor under him is 44 yd down). A kill
    // that skipped DamageTaken (a GM .die, an instakill) has a fall spline under way that has not moved him yet: stop
    // it on the spot and put him back on his spot every time (R-1-B n1), so the client never plays the 44 yd drop.
    void KeepTheBody()
    {
        me->GetMotionMaster()->Clear();
        me->StopMovingOnCurrentPos();
        me->SetDisableGravity(true);
        Position const spot = SpotPosition();
        if (me->IsInWorld())
            me->NearTeleportTo(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), spot.GetOrientation());
        PummelerLog("body", Acore::StringFormat("z={:.2f} gravity_off={}", me->GetPositionZ(),
            me->HasUnitMovementFlag(MOVEMENTFLAG_DISABLE_GRAVITY) ? 1 : 0));
    }

    // ---- CP1-CP7 the Combo -----------------------------------------------------------------------------------------

    bool StartCombination()
    {
        if (!_combo || _combo->Running())
            return false;
        uint32 length = _heroic ? HeroicLength(_combos, _landed) : NormalLength(_round);
        if (_testLength)
        {
            length = _testLength;
            _testLength = 0;
        }
        std::vector<PunchRoll> const rolls = RollChain(_heroic, length,
            [](uint32 n) { return n ? urand(0, n - 1) : 0u; });
        std::vector<GnomereganMachines::Punch> chain;
        chain.reserve(rolls.size());
        for (PunchRoll const& roll : rolls)
            chain.push_back(ToMachine(roll));
        me->InterruptNonMeleeSpells(false);
        uint32 const lengthMs = _combo->Call(chain);
        if (!lengthMs)
        {
            _comboAt = _now + 1000;     // refused (the owner was not ready): look again in a second
            PummelerLog("combo-refused", Acore::StringFormat("length={}", rolls.size()));
            return false;
        }
        _comboRunning = true;
        _lastLength = uint32(rolls.size());
        PummelerLog("combo", Acore::StringFormat("n={} length={} chain={} last_strike={}ms heroic={} round={} "
            "landed_so_far={}", _combos + 1, rolls.size(), ChainText(rolls), lengthMs, _heroic ? 1 : 0, _round,
            _landed));
        return true;
    }

    void EndCombination()
    {
        _comboRunning = false;
        ++_combos;
        uint32 const landed = _combo ? _combo->Landed() : 0;
        _landed += landed;
        _comboAt = _now + Tune::kComboAfterMs;
        _trampleNotBefore = _now + Tune::kTrampleAfterComboMs;
        PummelerLog("combo-end", Acore::StringFormat("n={} landed={} landed_total={} next_length={} next_in={}ms",
            _combos, landed, _landed, _heroic ? HeroicLength(_combos, _landed) : NormalLength(_round),
            Tune::kComboAfterMs));
    }

    // Normal: the bell at 66% and 33% (the next combination is a punch longer).
    void CheckRounds()
    {
        if (_heroic)
            return;
        uint32 const round = RoundFor(me->GetHealthPct());
        if (round > _round)
            Bell(round, "health");
    }

    void Bell(uint32 round, char const* why)
    {
        if (round <= _round)
            return;
        _round = round;
        me->PlayDirectSound(kBellSound);
        Talk(round >= 3 ? EMOTE_FINAL_ROUND : EMOTE_ROUND_TWO);
        PummelerLog("bell", Acore::StringFormat("round={} why={} health={:.0f}% next_length={}", round, why,
            me->GetHealthPct(), NormalLength(round)));
    }

    // ---- CP8 Trample -----------------------------------------------------------------------------------------------

    // No player (on his threat list, in the pocket) in his melee reach for kTrampleNoReachMs: Trample at once (at
    // most every kTrampleMinGapMs, never in the 2 s after a combination). Players only (R-1-B m3, SP CP8 "backing off
    // is not a rest"): a pet left in reach while the group stands back never keeps it away.
    void CheckReach(uint32 diff)
    {
        bool anyone = false;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (CountsAsPlayer(player) && InThePocket(player) && me->IsWithinMeleeRange(player))
            {
                anyone = true;
                break;
            }
        }
        _noReachMs = anyone ? 0 : _noReachMs + diff;
        if (_noReachMs >= Tune::kTrampleNoReachMs && _now >= _lastTrampleAt + Tune::kTrampleMinGapMs
            && _now >= _trampleNotBefore)
            Trample("no-reach");
    }

    void Trample(char const* why)
    {
        GuidSet targets;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (CountsAsPlayer(player) && InThePocket(player) && InTrample(DungeonKit::PlaneOf(player)))
                targets.insert(player->GetGUID());
        }
        if (Creature* stalker = Stalker())
            stalker->CastSpell(stalker, SPELL_TRAMPLE_LOOK, true);
        if (!targets.empty())
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = Tune::kTramplePct.Get(_heroic);
            spec.tankPct = spec.pct;            // mechanics include the tank (rule 17)
            spec.school = kSchoolPhysical;
            spec.spellId = SPELL_TRAMPLE;
            spec.weakened = false;              // SP CP8: no penalty (a healer pulse)
            spec.tag = TAG_TRAMPLE;
            Track(DungeonKit::RegistryHit(me, targets, spec));
        }
        _trampleAt = _now + Tune::kTrampleEveryMs;
        _lastTrampleAt = _now;
        _noReachMs = 0;
        PummelerLog("trample", Acore::StringFormat("why={} hit={} pct={:.0f} next_in={}ms", why, targets.size(),
            Tune::kTramplePct.Get(_heroic), Tune::kTrampleEveryMs));
    }

    // ---- the bots and the pets ------------------------------------------------------------------------------------

    // The bots' boss data (SP "Boss data": no kill order, no kicks, no dispels). R-1-B M1: ranged damage dealers and
    // healers hold the band past the hunters' too-close line and inside the pocket (2D from his origin).
    void Describe()
    {
        BossMechanics::Descriptor d;
        // RF-1 Minor-4: the blind corner is clipped out of the band (BM keeps ranged bots off it).
        d.rangeBands.emplace_back(Tune::kRangedBandMinYd, Tune::kRangedBandMaxYd)
            .KeepOut(Tune::kBlindCornerX, Tune::kBlindCornerY, Tune::kBlindCornerYd);
        Mechanic::Describe(me, std::move(d));
    }

    // R-1-B M2 (a script-side mitigation; the root cause is core's pet chase, left alone): a melee pet sent at him
    // chases to his back (PetAI::StartChase's ChaseAngle(pi)), the glass over the lower room; no path reaches it and
    // the chase's failure makes the pet AttackStop. Each tick, every player's pet whose victim he is and whose active
    // motion is a chase gets the same chase without the angle (ChaseRange(0, 0) as PetAI's melee chase), which paths
    // to his center on the pocket side and stops in his reach: once per new chase, again when its spline heads off
    // the pocket, and again every Tune::kPetChaseRetryMs while it is out of reach. RF-1 Minor-3: a chase is "new"
    // unless this sweep saw the pet chasing him on every tick since its fix (never the generator's address).
    // Imps and water elementals keep their own (ranged, no angle). A chase that fails before his tick (the pet
    // updated first) still stops the pet: the playtest line stays.
    void KeepPetsOffTheGlass()
    {
        if (!me->IsInWorld())
            return;
        _petChases.Begin();
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            Pet* pet = player ? player->GetPet() : nullptr;
            if (!pet || !pet->IsInWorld() || !pet->IsAlive() || pet->GetVictim() != me)
                continue;
            uint32 const entry = pet->GetEntry();
            if (entry == ENTRY_IMP || entry == ENTRY_WATER_ELEMENTAL || entry == ENTRY_WATER_ELEMENTAL_PERM)
                continue;
            MotionMaster* motion = pet->GetMotionMaster();
            if (motion->GetCurrentMovementGeneratorType() != CHASE_MOTION_TYPE
                || motion->GetMotionSlotType(MOTION_SLOT_ACTIVE) != CHASE_MOTION_TYPE)
                continue;
            uint32 fixedAt = 0;
            bool const tracked = _petChases.Seen(pet->GetGUID(), fixedAt);
            bool aimsOffPocket = false;
            if (pet->movespline->Initialized() && !pet->movespline->Finalized())
            {
                G3D::Vector3 const dest = pet->movespline->FinalDestination();
                aimsOffPocket = !FromThePocket(dest.x, dest.y, dest.z);
            }
            if (!PetChaseNeedsFix(tracked, me->IsWithinMeleeRange(pet), aimsOffPocket, _now - fixedAt))
                continue;
            motion->MoveChase(me, ChaseRange(0.f, 0.f));
            _petChases.Fixed(pet->GetGUID(), _now);
            ++_petChaseFixes;
            if (!tracked || aimsOffPocket)
                PummelerLog("pet-chase", Acore::StringFormat(
                    "pet={} owner={} at=({:.1f}, {:.1f}, {:.1f}) new={} off_pocket={} fixes={}", pet->GetName(),
                    player->GetName(), pet->GetPositionX(), pet->GetPositionY(), pet->GetPositionZ(), tracked ? 0 : 1,
                    aimsOffPocket ? 1 : 0, _petChaseFixes));
        }
        _petChases.End();
    }

    // ---- helpers ---------------------------------------------------------------------------------------------------

    void SummonFrameStalker()
    {
        Point3 const& o = kPummelerFrameOrigin;
        me->SummonCreature(NPC_FRAME_STALKER, Position(o.x, o.y, o.z, o.o), TEMPSUMMON_MANUAL_DESPAWN);
    }

    Creature* Stalker() const
    {
        return _stalker.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*me, _stalker);
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // RB-1: every registry handle, the machine (its shapes, markers and books), the stalker, the stars on players,
    // the pose bar, the clocks and the per-pull counters; one place for reset, evade, pull and death.
    void Cleanup(char const* why)
    {
        bool const was = _engaged;
        if (_combo)
            _combo->Clear();
        _combo.reset();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (Creature* stalker = Stalker())
            stalker->DespawnOrUnsummon();
        _stalker.Clear();
        if (me->IsInWorld())
            for (auto const& ref : me->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource())
                    player->RemoveAurasDueToSpell(SPELL_SEEING_STARS);
        if (me->IsAlive())
            me->InterruptNonMeleeSpells(false);
        _now = 0;
        _comboAt = 0;
        _trampleAt = 0;
        _trampleNotBefore = 0;
        _lastTrampleAt = 0;
        _noReachMs = 0;
        _filterLogAt = 0;
        _combos = 0;
        _landed = 0;
        _round = 1;
        _testLength = 0;
        _comboRunning = false;
        _engaged = false;
        _petChases.Clear();
        _petChaseFixes = 0;
        _arena.Reset();
        if (was)
            PummelerLog("cleanup", why);
    }

    DungeonKit::ArenaGuard _arena;
    std::unique_ptr<GnomereganMachines::ComboMachine> _combo;
    PetChaseTracker<ObjectGuid> _petChases;     // the pets whose chase is fixed, and when (fight clock)
    std::vector<MechanicHandle> _live;
    ObjectGuid _stalker;
    uint64 _replacedAtMs = 0;       // the last re-placement on his spot (wall clock: it runs out of combat too)
    uint64 _windowLogAtMs = 0;      // the last `window` line
    uint32 _windowFixes = 0;        // tick fixes since it
    uint32 _now = 0;
    uint32 _comboAt = 0;
    uint32 _trampleAt = 0;
    uint32 _trampleNotBefore = 0;
    uint32 _lastTrampleAt = 0;
    uint32 _noReachMs = 0;
    uint32 _filterLogAt = 0;
    uint32 _combos = 0;
    uint32 _landed = 0;
    uint32 _round = 1;
    uint32 _testLength = 0;
    uint32 _lastLength = 0;
    uint32 _petChaseFixes = 0;
    bool _comboRunning = false;
    bool _heroic = false;
    bool _engaged = false;
};

namespace
{
    boss_crowd_pummeler_rework* PummelerAI(ChatHandler* handler)
    {
        Creature* boss = GnomerTest::FindBoss(handler, NPC_CROWD_PUMMELER);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_crowd_pummeler_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, int32 action, uint32 length, char const* what)
    {
        boss_crowd_pummeler_rework* ai = PummelerAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(action, length);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Crowd Pummeler: {}.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return GnomerTest::ShowBossInfo(handler, NPC_CROWD_PUMMELER, BOSS_CROWD_PUMMELER);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_crowd_pummeler_rework* ai = PummelerAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Crowd Pummeler: {}", ai->TestState());
        return true;
    }

    // The window's live numbers (rule 33; the playtest's row G reads them): his spot, gravity, root, rotation lock,
    // scale, the reach and the floor distances it gives.
    bool HandleWindow(ChatHandler* handler)
    {
        Creature* boss = GnomerTest::FindBoss(handler, NPC_CROWD_PUMMELER);
        if (!boss)
            return false;
        float const reach = boss->GetCombatReach();
        handler->PSendSysMessage("Crowd Pummeler: at ({:.2f}, {:.2f}, {:.2f}) o {:.2f}, {:.2f} yd off his spot; "
            "gravity_off={} rooted={} rotate_locked={} alive={}; scale {:.2f}, reach {:.2f} (want {:.2f}), bounding "
            "{:.2f}; melee reaches {:.1f} yd of floor, hunters too close inside {:.1f} yd.", boss->GetPositionX(),
            boss->GetPositionY(), boss->GetPositionZ(), boss->GetOrientation(),
            boss->GetExactDist(kPummelerSpot.x, kPummelerSpot.y, kPummelerSpot.z),
            boss->HasUnitMovementFlag(MOVEMENTFLAG_DISABLE_GRAVITY) ? 1 : 0,
            boss->HasUnitState(UNIT_STATE_ROOT) ? 1 : 0,
            boss->HasUnitFlag(UNIT_FLAG_POSSESSED) ? 1 : 0, boss->IsAlive() ? 1 : 0, boss->GetObjectScale(), reach,
            WindowReach(boss->GetObjectScale()), boss->GetBoundaryRadius(), MeleeFloorReach(reach),
            HunterTooCloseFloor(reach));
        if (Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr)
            handler->PSendSysMessage("You: in the pocket box {}, in his melee reach {}, {:.1f} yd of floor from him.",
                InThePocket(gm) ? "yes" : "no", boss->IsWithinMeleeRange(gm) ? "yes" : "no",
                gm->GetExactDist2d(kPummelerSpot.x, kPummelerSpot.y));
        return true;
    }

    // `.dbtest gnomer pummeler combo [length]` (0 or none: the fight's own length).
    bool HandleCombo(ChatHandler* handler, Optional<uint32> length)
    {
        return Fire(handler, ACTION_TEST_COMBO, length.value_or(0), "a combination (CP1) now");
    }

    bool HandleTrample(ChatHandler* handler)
    {
        return Fire(handler, ACTION_TEST_TRAMPLE, 0, "Trample (CP8) now");
    }

    // `.dbtest gnomer pummeler round <2|3>` (normal).
    bool HandleRound(ChatHandler* handler, uint32 round)
    {
        return Fire(handler, round >= 3 ? ACTION_TEST_FINAL_ROUND : ACTION_TEST_ROUND_TWO, 0, "the bell");
    }

    ChatCommandTable const& PummelerTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "window",  HandleWindow,  SEC_GAMEMASTER, Console::No },
            { "combo",   HandleCombo,   SEC_GAMEMASTER, Console::No },
            { "trample", HandleTrample, SEC_GAMEMASTER, Console::No },
            { "round",   HandleRound,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_crowd_pummeler_rework()
{
    RegisterDungeonReworkCreatureAI(boss_crowd_pummeler_rework, GnomereganRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_pummeler_frame, GnomereganRework::kInstanceScriptName);
    GnomerTest::RegisterBoss("pummeler", PummelerTestCommands());
}
