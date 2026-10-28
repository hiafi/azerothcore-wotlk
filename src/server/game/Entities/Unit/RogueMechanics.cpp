/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "RogueMechanics.h"
#include "DataMap.h"
#include "GameTime.h"
#include "Group.h"
#include "GroupReference.h"
#include "Item.h"
#include "ItemTemplate.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "ObjectAccessor.h"
#include "ObjectGuid.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include "WorldSession.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <map>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * RG0a block (docs/reworks/rogue-shared-rework.md "Energy and haste", "Poisons"): energy x (1 + spell haste) for every
 * energy user, the six poisons as self auras (two slots, the roll, the once-per-cast guard, the one application
 * helper, the weapon glow). Per-player state lives in CustomData: it belongs to the player's map thread, needs no lock,
 * and dies with the object (a relog builds a new Player), so nothing can go stale across sessions.
 */
namespace
{
    // Fan of Knives main-hand spread (one HIT event per target already; the off-hand copy 52874 is triggered and never
    // reaches the guard). Local: the generated header name of the stock spell is not part of the RG0a contract.
    constexpr uint32 FAN_OF_KNIVES_SPELL_ID = 51723;
    // Triggered spells allowed to roll: the dual-strike hands (stock Mutilate 5374 / 27576, S1's Mutilate 203827 /
    // 203828 and Kingsbane 203840 / 203841), whose parent cast raises no proc of its own; rule 3d keeps the two
    // hands to one roll per aura. Every other triggered spell (Killing Spree's strikes, ...) rolls nothing (WP-R W1).
    // Stock Shiv's 5940 never reaches the guard (5938 suppresses its procs, 5940 is dropped by GetProcEffectMask);
    // RG0b's Shiv applies its Lethal poisons through ApplyLethalPoisons.
    constexpr uint32 TRIGGERED_ROLLERS[] =
    {
        5374, 27576,
        RogueData::SPELL_MUTILATE_MH, RogueData::SPELL_MUTILATE_OH,
        RogueData::SPELL_KINGSBANE_MH, RogueData::SPELL_KINGSBANE_OH,
        // S3 Deft Maneuvers' strike (C10): poisons roll once per enemy struck, like Fan of Knives (rule 3b).
        RogueData::SPELL_DEFT_MANEUVERS_STRIKE
    };

    constexpr std::array<uint32, 3> LETHAL_POISON_AURAS =
    {
        RogueData::SPELL_INSTANT_POISON_203701,
        RogueData::SPELL_DEADLY_POISON_203702,
        RogueData::SPELL_WOUND_POISON_203703
    };

    constexpr std::array<uint32, 6> POISON_AURAS =
    {
        RogueData::SPELL_INSTANT_POISON_203701,
        RogueData::SPELL_DEADLY_POISON_203702,
        RogueData::SPELL_WOUND_POISON_203703,
        RogueData::SPELL_CRIPPLING_POISON_203704,
        RogueData::SPELL_MIND_NUMBING_POISON_203705,
        RogueData::SPELL_ANESTHETIC_POISON_203706
    };

    constexpr std::array<uint8, 2> GLOW_SLOTS = { EQUIPMENT_SLOT_MAINHAND, EQUIPMENT_SLOT_OFFHAND };

    // Base chance per poison aura (shared doc "Poisons": Lethal 20% flat, Crippling 30%, Mind-numbing 50%, Anesthetic
    // 50%); 0 for anything else.
    int32 GetPoisonBaseChancePct(uint32 auraId)
    {
        switch (auraId)
        {
            case RogueData::SPELL_INSTANT_POISON_203701:
            case RogueData::SPELL_DEADLY_POISON_203702:
            case RogueData::SPELL_WOUND_POISON_203703:
                return RogueData::POISON_LETHAL_CHANCE_PCT;
            case RogueData::SPELL_CRIPPLING_POISON_203704:
                return RogueData::POISON_CRIPPLING_CHANCE_PCT;
            case RogueData::SPELL_MIND_NUMBING_POISON_203705:
                return RogueData::POISON_MIND_NUMBING_CHANCE_PCT;
            case RogueData::SPELL_ANESTHETIC_POISON_203706:
                return RogueData::POISON_ANESTHETIC_CHANCE_PCT;
            default:
                return 0;
        }
    }

    // Once-per-cast record, one entry per poison aura: the game-time ms and the target of the last spell hit that
    // rolled.
    struct PoisonCastEntry
    {
        int64 timeMs = -1;
        ObjectGuid target;
    };

    struct PoisonCastGuard : DataMap::Base
    {
        std::unordered_map<uint32, PoisonCastEntry> byAura;
    };

    constexpr char const* POISON_CAST_GUARD_KEY = "rogue_poison_cast_guard";

    int64 NowMs()
    {
        return int64(GameTime::GetGameTimeMS().count());
    }

    bool IsWeapon(Item const* item)
    {
        return item && item->GetTemplate()->Class == ITEM_CLASS_WEAPON;
    }

    // ---- S1 (Assassination) state and helpers ----

    // Stock ids S1 uses that the generated header does not declare (S1a WP-BRIEF section 2): Fan of Knives' linked
    // off-hand strike, and Quick Recovery's stock energize (reused unedited with a custom value, brief R8).
    constexpr uint32 FAN_OF_KNIVES_OFF_HAND_SPELL_ID = 52874;
    constexpr uint32 QUICK_RECOVERY_ENERGIZE_SPELL_ID = 31663;

    // _masks.POISON_GROUP: d1 b19, carried by every rogue poison payload, Envenom and S1's poison-damage rows.
    constexpr uint32 POISON_GROUP_D1 = 0x80000;

    // Per-rogue internal cooldowns of the talents that roll in C++ (Ruthlessness, Deadly Brew, Dashing Scoundrel),
    // keyed by the talent's rank 1 spell id: the game-time ms at which the talent may proc again.
    struct TalentCooldowns : DataMap::Base
    {
        std::unordered_map<uint32, int64> readyAtMs;
    };

    constexpr char const* TALENT_COOLDOWNS_KEY = "rogue_talent_cooldowns";

    bool TalentCooldownReady(Player const* rogue, uint32 key)
    {
        TalentCooldowns const* cooldowns = rogue->CustomData.Get<TalentCooldowns>(TALENT_COOLDOWNS_KEY);
        if (!cooldowns)
            return true;

        auto const itr = cooldowns->readyAtMs.find(key);
        return itr == cooldowns->readyAtMs.end() || NowMs() >= itr->second;
    }

    void StartTalentCooldown(Player* rogue, uint32 key, int32 durationMs)
    {
        rogue->CustomData.GetDefault<TalentCooldowns>(TALENT_COOLDOWNS_KEY)->readyAtMs[key] =
            NowMs() + std::max<int32>(durationMs, 0);
    }

    // Once-per-cast record of a dispatcher-stamped cast (Mutilate, Kingsbane, Fan of Knives), keyed by the parent id.
    // A dual strike's hands add up on it and the parent's AfterCast resolves and erases it; Fan of Knives marks it
    // resolved on its first crit (its hits land after its AfterCast). The next cast of the same parent restamps it.
    struct StrikeCastRecord
    {
        ObjectGuid target;
        uint32 totalDamage = 0;
        bool crit = false;
        bool resolved = false;
    };

    struct StrikeCastState : DataMap::Base
    {
        std::unordered_map<uint32, StrikeCastRecord> byParent;
    };

    constexpr char const* STRIKE_CAST_STATE_KEY = "rogue_strike_cast_state";

    // The stamped parent a recorded strike belongs to, 0 for anything else.
    uint32 GetStrikeParent(uint32 spellId)
    {
        switch (spellId)
        {
            case RogueData::SPELL_MUTILATE_MH:
            case RogueData::SPELL_MUTILATE_OH:
                return RogueData::SPELL_MUTILATE;
            case RogueData::SPELL_KINGSBANE_MH:
            case RogueData::SPELL_KINGSBANE_OH:
                return RogueData::SPELL_KINGSBANE;
            case FAN_OF_KNIVES_SPELL_ID:
            case FAN_OF_KNIVES_OFF_HAND_SPELL_ID:
                return FAN_OF_KNIVES_SPELL_ID;
            default:
                return 0;
        }
    }

    // Blindside's empowered Sinister Strike: the Spell object and the game-time ms of its BeforeCast. Both must match,
    // so a stamp left behind by a cast that never reached its AfterCast cannot empower a later Spell at the same
    // address. The pointer is compared, never dereferenced.
    struct BlindsideStamp : DataMap::Base
    {
        Spell const* spell = nullptr;
        int64 timeMs = -1;
    };

    constexpr char const* BLINDSIDE_STAMP_KEY = "rogue_blindside_stamp";

    // Stored bleeds on their target (one entry per rogue and bleed aura): the per-tick amount the aura script deals.
    struct StoredBleedState : DataMap::Base
    {
        std::map<std::pair<ObjectGuid, uint32>, uint32> perTick;
    };

    constexpr char const* STORED_BLEED_STATE_KEY = "rogue_stored_bleed";

    // The tick budget a stored bleed spreads over. S2's Hemorrhage / Akaari's Echo add their own case; the fallback is
    // the row's own duration / period.
    int32 GetStoredBleedTicks(uint32 bleedAuraId)
    {
        if (bleedAuraId == RogueData::SPELL_DOOMBLADE_BLEED)
            return std::max<int32>(RogueData::DOOMBLADE_TICKS, 1);

        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(bleedAuraId);
        int32 const amplitude = spellInfo ? spellInfo->Effects[EFFECT_0].Amplitude : 0;
        return amplitude > 0 ? std::max<int32>(spellInfo->GetMaxDuration() / amplitude, 1) : 1;
    }

    // Ticks the live aura still pays at the base cadence (the spell's own amplitude, not the live one Hunger for Blood
    // halves: its extra ticks are bonus damage, never stored damage owed): ceil(remaining duration / base amplitude).
    // Read from the duration, not GetTickNumber(): Hunger for Blood's CalculatePeriodic zeroes the tick count.
    uint32 GetRemainingTicks(Aura const* aura, int32 baseAmplitude)
    {
        int32 const duration = aura->GetDuration();
        if (baseAmplitude <= 0 || duration <= 0)
            return 0;

        return uint32((duration + baseAmplitude - 1) / baseAmplitude);
    }

    // The highest held rank (HasAura on the rank spell ids, rank 1 first; the last one held wins), nullptr if none.
    SpellInfo const* GetHeldRank(Player const* rogue, std::initializer_list<uint32> rankIds)
    {
        uint32 held = 0;
        for (uint32 const rankId : rankIds)
            if (rogue->HasAura(rankId))
                held = rankId;

        return held ? sSpellMgr->GetSpellInfo(held) : nullptr;
    }

    // Weapon strikes count too: Kingsbane's hands (WEAPON_PERCENT_DAMAGE with d1 b19) are poison damage for Zoldyck
    // Recipe and Dashing Scoundrel. The d1 b19 gate in IsRoguePoisonDamage keeps Mutilate, Sinister Strike and Fan of
    // Knives out.
    bool HasDamageEffect(SpellInfo const* spellInfo)
    {
        return std::any_of(spellInfo->Effects.begin(), spellInfo->Effects.end(), [](SpellEffectInfo const& effect)
        {
            return effect.IsEffect(SPELL_EFFECT_SCHOOL_DAMAGE) || effect.IsEffect(SPELL_EFFECT_WEAPON_DAMAGE) ||
                effect.IsEffect(SPELL_EFFECT_WEAPON_PERCENT_DAMAGE) ||
                effect.IsEffect(SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL) ||
                effect.IsEffect(SPELL_EFFECT_NORMALIZED_WEAPON_DMG) || effect.IsAura(SPELL_AURA_PERIODIC_DAMAGE);
        });
    }

    // The rogue's live hostile selection, nullptr if there is none.
    Unit* GetSelectedHostile(Player* rogue)
    {
        Unit* selected = ObjectAccessor::GetUnit(*rogue, rogue->GetTarget());
        return selected && selected->IsAlive() && rogue->IsValidAttackTarget(selected) ? selected : nullptr;
    }

    // ---- S2 (Subtlety) state and helpers ----

    // Stock ids S2 uses that the generated header does not declare (S2a WP-BRIEF section 2): Relentless Strikes'
    // energize (25 energy), and the three looks the Akaari clone copies from the rogue (the npc_pet_mage_mirror_image
    // order).
    constexpr uint32 RELENTLESS_STRIKES_ENERGIZE_SPELL_ID = 14181;
    constexpr uint32 CLONE_ME_SPELL_ID = 45204;
    constexpr uint32 COPY_WEAPON_SPELL_ID = 41054;
    constexpr uint32 COPY_OFF_HAND_SPELL_ID = 45205;

    // Death from Above's rise leg: the apex height is in the leg's end point, so a low vertical speed keeps the leg a
    // near-straight steep line (MoveJump turns speedZ into an extra arc). The dive uses 0.
    constexpr float DFA_RISE_SPEED_Z = 1.0f;
    // The slow-fall leg: a near-zero arc (about 0.01 yd at 0.5), so the short drop reads as floating, not a hop.
    constexpr float DFA_DRIFT_SPEED_Z = 0.5f;
    // A leg counts as interrupted when the rogue is farther than this from the leg's end point at the next leg (a
    // knockback, pull or teleport moved it) and no spline toward that end point is still running (events run before
    // the spline update, so on a long world tick the leg is still finishing: that is not an interruption).
    constexpr float DFA_APEX_TOLERANCE_YD = 3.0f;
    // Death from Above's rise stops this far short of a ceiling or overhang hit (S2-CODE-REVIEW M1), its slow fall
    // this far short of a wall.
    constexpr float DFA_CEILING_MARGIN_YD = 0.5f;

    // A skipped dive leaves the rogue falling from the apex: the flight aura (its safe fall) is kept alive while the
    // rogue falls, polled every DFA_FALL_POLL_MS, for at most DFA_FALL_WATCH_MS; it is never removed early.
    constexpr int32 DFA_FALL_POLL_MS = 250;
    constexpr int32 DFA_FALL_WATCH_MS = 10000;

    // Tank auras Honor Among Thieves' ally pick skips: this server's tank auras (docs/Systems.md section 2): Defensive
    // Stance, Bear Form, Dire Bear Form, Righteous Fury, Blood Presence (the DK rework's only tank presence), Dark
    // Apotheosis (the warlock tank form; its passive 200836 is aura-linked to it) and Rockbiter's tank child (applied
    // with the Rockbiter Weapon imbue). Enforcer Stance comes from the header.
    constexpr std::array<uint32, 7> HONOR_AMONG_THIEVES_TANK_AURAS = { 71, 5487, 9634, 25780, 48266, 200835, 202200 };

    // Finality: per finisher key (2098, 1943, 26679), was its buff held when the dispatcher saw the cast? Read and
    // erased by ResolveFinality after the hit.
    struct FinalityState : DataMap::Base
    {
        std::unordered_map<uint32, bool> heldAtCast;
    };

    constexpr char const* FINALITY_STATE_KEY = "rogue_finality_state";

    // Honor Among Thieves: the last stamped finisher cast (its id, its primary target, whether its crit already
    // triggered) and the ally the buff went to (kept for refreshes).
    struct HonorAmongThievesState : DataMap::Base
    {
        uint32 castSpellId = 0;
        ObjectGuid primary;
        bool triggered = true;
        ObjectGuid ally;
    };

    constexpr char const* HONOR_AMONG_THIEVES_STATE_KEY = "rogue_honor_among_thieves";

    // Hidden-state tracking for UpdateHiddenBuffs: true Stealth at the last call, and when Master of Subtlety's tail
    // after the last true-Stealth exit ends (game-time ms).
    struct HiddenState : DataMap::Base
    {
        bool trueStealthed = false;
        int64 masterOfSubtletyTailEndMs = 0;
    };

    constexpr char const* HIDDEN_STATE_KEY = "rogue_hidden_state";

    // Finality's key for a finisher id (Death from Above's landing counts as an Eviscerate), 0 for anything else.
    uint32 GetFinalityKey(uint32 spellId)
    {
        switch (spellId)
        {
            case RogueData::SPELL_EVISCERATE:
            case RogueData::SPELL_DEATH_FROM_ABOVE:
                return RogueData::SPELL_EVISCERATE;
            case RogueData::SPELL_RUPTURE:
                return RogueData::SPELL_RUPTURE;
            case RogueData::SPELL_DEADLY_THROW:
                return RogueData::SPELL_DEADLY_THROW;
            default:
                return 0;
        }
    }

    // Finality's buff for a key, 0 for anything else.
    uint32 GetFinalityBuff(uint32 key)
    {
        switch (key)
        {
            case RogueData::SPELL_EVISCERATE:
                return RogueData::SPELL_FINALITY_EVISCERATE;
            case RogueData::SPELL_RUPTURE:
                return RogueData::SPELL_FINALITY_RUPTURE;
            case RogueData::SPELL_DEADLY_THROW:
                return RogueData::SPELL_FINALITY_DEADLY_THROW;
            default:
                return 0;
        }
    }

    // True Stealth: Stealth or Vanish's aura (Shadowed is Hidden, not stealthed).
    bool IsTrueStealthed(Unit const* unit)
    {
        return unit->HasAura(RogueData::SPELL_STEALTH) || unit->HasAura(RogueData::SPELL_VANISH_11327);
    }

    void MakeAuraInfinite(Aura* aura)
    {
        if (aura->IsPermanent())
            return;

        aura->SetMaxDuration(-1);
        aura->SetDuration(-1);
    }

    void SetAuraTail(Aura* aura, int32 ms)
    {
        aura->SetMaxDuration(ms);
        aura->SetDuration(ms);
    }

    // U48: a tank by its stance / form / presence aura.
    bool IsLikelyTank(Player const* player)
    {
        if (player->HasAura(RogueData::SPELL_ENFORCER_STANCE))
            return true;

        return std::any_of(HONOR_AMONG_THIEVES_TANK_AURAS.begin(), HONOR_AMONG_THIEVES_TANK_AURAS.end(),
            [player](uint32 auraId)
        {
            return player->HasAura(auraId);
        });
    }

    // U48: a healer by its most-points tree (tab pages: priest 0 Discipline / 1 Holy, paladin 0 Holy, druid and shaman
    // 2 Restoration). GetMostPointsTalentTree returns 0 for an untalented player, so only a player with points counts.
    bool IsLikelyHealer(Player const* player)
    {
        uint8 points[3] = { 0, 0, 0 };
        player->GetTalentTreePoints(points);
        if (!points[0] && !points[1] && !points[2])
            return false;

        uint8 const tree = player->GetMostPointsTalentTree();
        switch (player->getClass())
        {
            case CLASS_PRIEST:
                return tree == 0 || tree == 1;
            case CLASS_PALADIN:
                return tree == 0;
            case CLASS_DRUID:
            case CLASS_SHAMAN:
                return tree == 2;
            default:
                return false;
        }
    }

    // A party member Honor Among Thieves may (still) buff: alive, another player, same group and subgroup (the doc's
    // "party"; in a raid, the rogue's own subgroup), same map, in range.
    bool IsHonorAmongThievesAllyInReach(Player const* rogue, Player const* ally)
    {
        return ally && ally != rogue && ally->IsAlive() && rogue->IsInSameGroupWith(ally) && ally->IsInMap(rogue) &&
            rogue->IsWithinDistInMap(ally, RogueData::HONOR_AMONG_THIEVES_ALLY_RANGE_YD);
    }

    // U48: the closest party member in reach, rogues first, then hunters, then any other damage dealer; tanks and
    // likely healers are skipped. nullptr when nobody qualifies (the rogue still gets its own buff).
    Player* SelectHonorAmongThievesAlly(Player* rogue)
    {
        Group* group = rogue->GetGroup();
        if (!group)
            return nullptr;

        Player* best = nullptr;
        uint8 bestTier = 0;
        float bestDist = 0.0f;
        for (GroupReference* itr = group->GetFirstMember(); itr; itr = itr->next())
        {
            Player* member = itr->GetSource();
            if (!IsHonorAmongThievesAllyInReach(rogue, member) || IsLikelyTank(member) || IsLikelyHealer(member))
                continue;

            uint8 const tier = member->getClass() == CLASS_ROGUE ? 1 : member->getClass() == CLASS_HUNTER ? 2 : 3;
            float const dist = rogue->GetExactDist(member);
            if (!best || tier < bestTier || (tier == bestTier && dist < bestDist))
            {
                best = member;
                bestTier = tier;
                bestDist = dist;
            }
        }

        return best;
    }

    // Death from Above's landing point: DFA_LANDING_PAST_YD past the target along from -> target, on the ground near
    // the target's z. False when it is unreachable (no ground there, or the ground is far from the target's z: a target
    // floating over a drop); x / y / z are still filled (z = the target's z when there is no ground).
    bool GetDeathFromAboveLanding(Player const* rogue, Position const& from, Unit const* target, float& x, float& y,
        float& z)
    {
        float const angle = from.GetAngle(target);
        x = target->GetPositionX() + RogueData::DFA_LANDING_PAST_YD * std::cos(angle);
        y = target->GetPositionY() + RogueData::DFA_LANDING_PAST_YD * std::sin(angle);
        z = target->GetPositionZ();

        if (rogue->GetMapHeight(x, y, z) <= INVALID_HEIGHT)
            return false;

        rogue->UpdateAllowedPositionZ(x, y, z);
        return std::fabs(z - target->GetPositionZ()) <= RogueData::DFA_UNREACHABLE_Z_YD;
    }

    // One Death from Above leg (R8): MoveJump timed to airMs over the 3D leg length (at least DFA_MIN_JUMP_YD), with
    // the two calls EffectJumpDest makes for a player. Returns the leg's measured air time (the spline's own duration;
    // the planned time if no spline was launched).
    int32 StartDeathFromAboveLeg(Player* rogue, float x, float y, float z, int32 airMs, float speedZ,
        Unit const* faceTarget)
    {
        int32 const plannedMs = std::max<int32>(airMs, 1);
        float const length = std::max(rogue->GetExactDist(x, y, z), float(RogueData::DFA_MIN_JUMP_YD));
        float const speedXY = length * 1000.0f / float(plannedMs);

        rogue->SetCanTeleport(true);
        sScriptMgr->AnticheatSetUnderACKmount(rogue);
        rogue->GetMotionMaster()->MoveJump(x, y, z, speedXY, speedZ, 0, faceTarget);

        // The controlled slot is the top one, so the spline is launched inside MoveJump.
        return rogue->movespline->Finalized() ? plannedMs : std::max<int32>(rogue->movespline->Duration(), 1);
    }

    // The rogue of a Death from Above event, re-resolved by guid: in the world, on the map and instance it leapt in.
    Player* ResolveDeathFromAboveRogue(ObjectGuid rogueGuid, uint32 mapId, uint32 instanceId)
    {
        Player* rogue = ObjectAccessor::FindPlayer(rogueGuid);
        if (!rogue || !rogue->IsInWorld() || rogue->GetMapId() != mapId || rogue->GetInstanceId() != instanceId)
            return nullptr;

        return rogue;
    }

    // A skipped dive: while the rogue falls from the apex, keep the flight aura (its safe fall) from running out; once
    // the rogue is down it expires on its own (never removed early). Stops when the aura is gone, the rogue is dead or
    // gone, or after DFA_FALL_WATCH_MS.
    void WatchDeathFromAboveFall(ObjectGuid rogueGuid, uint32 mapId, uint32 instanceId, int32 elapsedMs)
    {
        Player* rogue = ResolveDeathFromAboveRogue(rogueGuid, mapId, instanceId);
        if (!rogue || !rogue->IsAlive() || elapsedMs >= DFA_FALL_WATCH_MS)
            return;

        Aura* flight = rogue->GetAura(RogueData::SPELL_DEATH_FROM_ABOVE_FLIGHT);
        if (!flight)
            return;

        // Unit::IsFalling reads the client's falling flags (and a falling spline); Player::IsFalling hides it.
        if (rogue->Unit::IsFalling() && flight->GetDuration() >= 0 && flight->GetDuration() < 2 * DFA_FALL_POLL_MS)
        {
            flight->SetMaxDuration(std::max(flight->GetMaxDuration(), 2 * DFA_FALL_POLL_MS));
            flight->SetDuration(2 * DFA_FALL_POLL_MS);
        }

        rogue->m_Events.AddEventAtOffset([rogueGuid, mapId, instanceId, elapsedMs]()
        {
            WatchDeathFromAboveFall(rogueGuid, mapId, instanceId, elapsedMs + DFA_FALL_POLL_MS);
        }, Milliseconds(DFA_FALL_POLL_MS));
    }

    // The landing (scheduled at the dive's end, or at the planned end when the dive was skipped): a living rogue with
    // the target alive within DFA_LANDING_RANGE_YD lands the snapshotted Eviscerate. The flight aura ends here when
    // the rogue is down (the dive or the unreachable-landing placement ran, or the rogue died); after a skipped dive
    // the fall watcher keeps it until the rogue lands.
    void LandDeathFromAbove(ObjectGuid rogueGuid, ObjectGuid targetGuid, uint32 mapId, uint32 instanceId,
        int32 landingBase, bool removeFlight)
    {
        Player* rogue = ResolveDeathFromAboveRogue(rogueGuid, mapId, instanceId);
        if (!rogue)
            return;

        if (removeFlight || !rogue->IsAlive())
            rogue->RemoveAurasDueToSpell(RogueData::SPELL_DEATH_FROM_ABOVE_FLIGHT);

        if (!rogue->IsAlive())
            return;

        Unit* target = ObjectAccessor::GetUnit(*rogue, targetGuid);
        if (target && target->IsAlive() && rogue->GetExactDist2d(target) <= RogueData::DFA_LANDING_RANGE_YD)
            rogue->CastCustomSpell(target, RogueData::SPELL_DEATH_FROM_ABOVE_LANDING, &landingBase, nullptr, nullptr,
                true);
    }

    void ScheduleDeathFromAboveLanding(Player* rogue, ObjectGuid targetGuid, int32 landingBase, int32 delayMs,
        bool removeFlight)
    {
        ObjectGuid const rogueGuid = rogue->GetGUID();
        uint32 const mapId = rogue->GetMapId();
        uint32 const instanceId = rogue->GetInstanceId();
        rogue->m_Events.AddEventAtOffset([rogueGuid, targetGuid, mapId, instanceId, landingBase, removeFlight]()
        {
            LandDeathFromAbove(rogueGuid, targetGuid, mapId, instanceId, landingBase, removeFlight);
        }, Milliseconds(std::max<int32>(delayMs, 1)));
    }

    // The previous leg (rise or slow fall) still finishing: a spline is running and ends at that leg's end point (the
    // next leg's event runs before this tick's spline update, so on a long world tick the rogue is still short of it).
    // A knockback or pull ends elsewhere.
    bool IsLegStillRunning(Player const* rogue, Position const& legEnd)
    {
        if (rogue->movespline->Finalized() || !rogue->movespline->Initialized())
            return false;

        G3D::Vector3 const end = rogue->movespline->FinalDestination();
        return legEnd.GetExactDist(end.x, end.y, end.z) <= DFA_APEX_TOLERANCE_YD;
    }

    // The previous leg was interrupted: a stun, confuse or fear, or the rogue moved off that leg's end point
    // (knockback, pull, teleport) with no spline toward it still running.
    bool IsDeathFromAboveInterrupted(Player const* rogue, Position const& legEnd)
    {
        return rogue->HasUnitState(UNIT_STATE_STUNNED | UNIT_STATE_CONFUSED | UNIT_STATE_FLEEING) ||
            (rogue->GetExactDist(legEnd) > DFA_APEX_TOLERANCE_YD && !IsLegStillRunning(rogue, legEnd));
    }

    // Leg 3 (at the slow fall's measured end): dive onto the target's position now. A stun, confuse or fear, or a
    // slow fall moved off its end point (knockback, pull, teleport) skips the dive; the landing test still runs at the
    // planned end and the safe fall lasts until the rogue is down. A dead or missing target dives to the landing point
    // computed at launch
    // (S2-CODE-REVIEW M1), or falls when that point was unreachable. An unreachable landing point skips the dive too
    // and places the rogue behind the target (Shadowstep's placement); the landing runs a dive's time later, once the
    // (possibly delayed) teleport has landed.
    void DiveDeathFromAbove(ObjectGuid rogueGuid, ObjectGuid targetGuid, uint32 mapId, uint32 instanceId,
        Position const& driftEnd, Position const& launchLanding, bool launchLandingReachable, int32 landingBase)
    {
        Player* rogue = ResolveDeathFromAboveRogue(rogueGuid, mapId, instanceId);
        if (!rogue)
            return;

        if (!rogue->IsAlive())
        {
            rogue->RemoveAurasDueToSpell(RogueData::SPELL_DEATH_FROM_ABOVE_FLIGHT);
            return;
        }

        Unit* target = ObjectAccessor::GetUnit(*rogue, targetGuid);
        bool const interrupted = IsDeathFromAboveInterrupted(rogue, driftEnd);
        if (!interrupted && (!target || !target->IsAlive()) && launchLandingReachable)
        {
            int32 const diveMs = StartDeathFromAboveLeg(rogue, launchLanding.GetPositionX(),
                launchLanding.GetPositionY(), launchLanding.GetPositionZ(), RogueData::DFA_DIVE_MS, 0.0f, nullptr);
            ScheduleDeathFromAboveLanding(rogue, targetGuid, landingBase, diveMs, true);
            return;
        }

        if (interrupted || !target || !target->IsAlive())
        {
            WatchDeathFromAboveFall(rogueGuid, mapId, instanceId, 0);
            ScheduleDeathFromAboveLanding(rogue, targetGuid, landingBase, RogueData::DFA_DIVE_MS, false);
            return;
        }

        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        if (!GetDeathFromAboveLanding(rogue, rogue->GetPosition(), target, x, y, z))
        {
            // The teleport may be delayed (inside Player::Update) and a near teleport keeps the old position until the
            // client acks: test the landing range a dive's time later, not at the apex (S2a-REVIEW M1).
            rogue->CastSpell(target, RogueData::SPELL_AMBUSH_TELEPORT, TRIGGERED_FULL_MASK);
            ScheduleDeathFromAboveLanding(rogue, targetGuid, landingBase, RogueData::DFA_DIVE_MS, true);
            return;
        }

        int32 const diveMs = StartDeathFromAboveLeg(rogue, x, y, z, RogueData::DFA_DIVE_MS, 0.0f, target);
        ScheduleDeathFromAboveLanding(rogue, targetGuid, landingBase, diveMs, true);
    }

    // Leg 2 (at the rise's measured end): the slow fall. From the (ceiling-capped) apex, drift DFA_DRIFT_DROP_YD down
    // and DFA_DRIFT_FORWARD_YD toward the launch landing point over DFA_DRIFT_MS: never up, never under the floor,
    // never through a wall; then the dive from the drift's end. A dead rogue loses the flight aura; an interrupted rise
    // (the dive's rules) skips both legs: the rogue falls under the fall watcher and the landing test runs at the
    // planned end. A dead target or an unreachable landing still drifts: the dive handles them.
    void DriftDeathFromAbove(ObjectGuid rogueGuid, ObjectGuid targetGuid, uint32 mapId, uint32 instanceId,
        Position const& apex, Position const& launchLanding, bool launchLandingReachable, int32 landingBase)
    {
        Player* rogue = ResolveDeathFromAboveRogue(rogueGuid, mapId, instanceId);
        if (!rogue)
            return;

        if (!rogue->IsAlive())
        {
            rogue->RemoveAurasDueToSpell(RogueData::SPELL_DEATH_FROM_ABOVE_FLIGHT);
            return;
        }

        if (IsDeathFromAboveInterrupted(rogue, apex))
        {
            WatchDeathFromAboveFall(rogueGuid, mapId, instanceId, 0);
            ScheduleDeathFromAboveLanding(rogue, targetGuid, landingBase,
                RogueData::DFA_DRIFT_MS + RogueData::DFA_DIVE_MS, false);
            return;
        }

        // Forward toward the launch landing point, never past it.
        float const toLandingX = launchLanding.GetPositionX() - apex.GetPositionX();
        float const toLandingY = launchLanding.GetPositionY() - apex.GetPositionY();
        float const toLanding = std::sqrt(toLandingX * toLandingX + toLandingY * toLandingY);
        float const forward = std::clamp(float(RogueData::DFA_DRIFT_FORWARD_YD), 0.0f, toLanding);
        float driftX = apex.GetPositionX();
        float driftY = apex.GetPositionY();
        if (toLanding > 0.0f)
        {
            driftX += toLandingX / toLanding * forward;
            driftY += toLandingY / toLanding * forward;
        }

        // The jump spline ignores collision: stop the drift short of a wall (ray at mid-body height).
        float const halfHeight = rogue->GetCollisionHeight() * 0.5f;
        float const rayZ = apex.GetPositionZ() + halfHeight;
        float hitX = driftX;
        float hitY = driftY;
        float hitZ = rayZ;
        MapCollisionData const& collision = rogue->GetMap()->GetMapCollisionData();
        bool const hitStatic = collision.GetStaticTree().GetObjectHitPos(apex.GetPositionX(), apex.GetPositionY(),
            rayZ, hitX, hitY, hitZ, hitX, hitY, hitZ, -DFA_CEILING_MARGIN_YD);
        bool const hitDynamic = collision.GetDynamicTree().GetObjectHitPos(rogue->GetPhaseMask(), apex.GetPositionX(),
            apex.GetPositionY(), rayZ, hitX, hitY, hitZ, hitX, hitY, hitZ, -DFA_CEILING_MARGIN_YD);
        if (hitStatic || hitDynamic)
        {
            driftX = hitX;
            driftY = hitY;
        }

        // Down only, and never under the floor below the drift point (a ceiling-capped apex can sit near the ground).
        float driftZ = apex.GetPositionZ() - std::max(float(RogueData::DFA_DRIFT_DROP_YD), 0.0f);
        float const floorZ = rogue->GetMapHeight(driftX, driftY, apex.GetPositionZ());
        if (floorZ > INVALID_HEIGHT)
            driftZ = std::min(std::max(driftZ, floorZ), apex.GetPositionZ());

        Position const driftEnd(driftX, driftY, driftZ);
        Unit const* target = ObjectAccessor::GetUnit(*rogue, targetGuid);
        int32 const driftMs = StartDeathFromAboveLeg(rogue, driftX, driftY, driftZ, RogueData::DFA_DRIFT_MS,
            DFA_DRIFT_SPEED_Z, target && target->IsAlive() ? target : nullptr);

        rogue->m_Events.AddEventAtOffset([rogueGuid, targetGuid, mapId, instanceId, driftEnd, launchLanding,
            launchLandingReachable, landingBase]()
        {
            DiveDeathFromAbove(rogueGuid, targetGuid, mapId, instanceId, driftEnd, launchLanding,
                launchLandingReachable, landingBase);
        }, Milliseconds(driftMs));
    }

    // The S2 finisher clauses that count spent points (OnSpellCast decides when the points count as spent): Shadow
    // Dance's reduction, Relentless Strikes, the Executioner capstone (target below 35% at cast) and Sinister Calling.
    // Both Shadow Dance reductions apply only when Shadow Dance was already cooling at the finisher's cast
    // (danceCoolingAtCast): a Dance started after the finisher, in the same update, is never reduced
    // (S2-CODE-REVIEW L1).
    void ApplySpentFinisherClauses(Player* rogue, Unit* target, uint8 comboPoints, bool executionerBelow,
        bool danceCoolingAtCast)
    {
        if (!rogue->IsAlive())
            return;

        // Shadow Dance (every finisher, any spec: S2-HANDOFF section 7): 1 s per point off its cooldown.
        if (danceCoolingAtCast)
            Rogue::ReduceCooldown(rogue, RogueData::SPELL_SHADOW_DANCE,
                uint32(std::max<int32>(RogueData::SHADOW_DANCE_CDR_PER_CP_MS, 0)) * comboPoints);

        // Relentless Strikes: rank % per point to restore 25 energy and ignore armor for 5 s (once per cast, Death from
        // Above included).
        int32 const relentlessPct = Rogue::GetRankAmount(rogue, { RogueData::SPELL_RELENTLESS_STRIKES,
            RogueData::SPELL_RELENTLESS_STRIKES_58422, RogueData::SPELL_RELENTLESS_STRIKES_58423 }, EFFECT_0);
        if (relentlessPct > 0 && Rogue::RollProcChance(rogue, float(relentlessPct * comboPoints)))
        {
            rogue->CastSpell(rogue, RELENTLESS_STRIKES_ENERGIZE_SPELL_ID, TRIGGERED_FULL_MASK);
            rogue->CastSpell(rogue, RogueData::SPELL_RELENTLESS_STRIKES_BUFF, TRIGGERED_FULL_MASK);
        }

        // Executioner capstone: below 35% the finisher takes another 0.5 s per point off Shadow Dance.
        if (danceCoolingAtCast && executionerBelow && rogue->HasAura(RogueData::SPELL_EXECUTIONER_204143))
            Rogue::ReduceCooldown(rogue, RogueData::SPELL_SHADOW_DANCE,
                uint32(std::max<int32>(RogueData::EXECUTIONER_CDR_PER_CP_MS, 0)) * comboPoints);

        // Sinister Calling capstone: 4% per point to throw the Shadowstrike volley at the target (once per cast; lost
        // when the finisher killed it).
        if (target && target->IsAlive() && rogue->HasAura(RogueData::SPELL_SINISTER_CALLING_31218) &&
            Rogue::RollProcChance(rogue, float(RogueData::SINISTER_CALLING_PCT_PER_CP * comboPoints)))
            rogue->CastSpell(target, RogueData::SPELL_SINISTER_CALLING_VOLLEY, TRIGGERED_FULL_MASK);
    }

    // ---- S3 (Combat) state and helpers ----

    // Unit::AddComboPoints clamps at 5 silently; Anticipation (U54) stores what would go past it.
    constexpr int32 MAX_COMBO_POINTS = 5;

    // U54 (b): the last non-triggered builder cast, stamped by the dispatcher before its effects. points = the points
    // after every scripted grant so far (GainComboPoints refreshes it while the stamp is live, S3a WP-BRIEF R3), gain =
    // the cast's expected native ADD_COMBO_POINTS gain (spell mods included), landed = a damage hit of the cast (or of
    // its dual-strike hands) was seen. Resolved by its own +1 ms event, or at once by the next builder's stamp (an
    // instant strike's gain has landed by then).
    struct BuilderStamp : DataMap::Base
    {
        bool live = false;
        uint32 seq = 0;
        uint32 spellId = 0;
        uint8 points = 0;
        int32 gain = 0;
        bool landed = false;
    };

    constexpr char const* BUILDER_STAMP_KEY = "rogue_builder_stamp";

    // S3a WP-BRIEF R4: set by the spent-clause event (ApplyCombatSpentClauses, points spent), read and cleared by the
    // release event scheduled after Ruthlessness's point.
    struct AnticipationRelease : DataMap::Base
    {
        bool pending = false;
    };

    constexpr char const* ANTICIPATION_RELEASE_KEY = "rogue_anticipation_release";

    // Surprise Attacks' extra shots: was the Pistol Shot that fired them empowered (Opportunity's 50%)? Overwritten by
    // the next Pistol Shot that consumes the capstone buff, so it is never read by shots it did not schedule.
    struct SurpriseShotStamp : DataMap::Base
    {
        bool empowered = false;
    };

    constexpr char const* SURPRISE_SHOT_STAMP_KEY = "rogue_surprise_shot_stamp";

    // Hack and Slash's once-per-cast guard on abilities (R22): the game-time ms and the cast key (the dual-strike
    // parent for Mutilate / Kingsbane hands, else the spell id) of the last ability attempt that rolled.
    struct HackAndSlashGuard : DataMap::Base
    {
        int64 timeMs = -1;
        uint32 castKey = 0;
    };

    constexpr char const* HACK_AND_SLASH_GUARD_KEY = "rogue_hack_and_slash_guard";

    // S3a-REVIEW L8: Prey on the Weak's held rank (0 = none), kept by Rogue::UpdatePreyRankCache from the rank auras'
    // apply / remove hooks, so the per-swing hooks of every player gate on one lookup.
    struct PreyRankCache : DataMap::Base
    {
        uint32 rankId = 0;
    };

    constexpr char const* PREY_RANK_CACHE_KEY = "rogue_prey_rank";

    uint32 GetCachedPreyRank(Player const* rogue)
    {
        PreyRankCache const* cache = rogue->CustomData.Get<PreyRankCache>(PREY_RANK_CACHE_KEY);
        return cache ? cache->rankId : 0;
    }

    bool HasAdrenalineRush(Unit const* rogue)
    {
        return rogue->HasAura(RogueData::SPELL_ADRENALINE_RUSH) ||
            rogue->HasAura(RogueData::SPELL_ADRENALINE_RUSH_CELERITY);
    }

    bool HasAddComboPointsEffect(SpellInfo const* spellInfo)
    {
        return std::any_of(spellInfo->Effects.begin(), spellInfo->Effects.end(), [](SpellEffectInfo const& effect)
        {
            return effect.IsEffect(SPELL_EFFECT_ADD_COMBO_POINTS);
        });
    }

    // Banks a resolved builder's overflow: points (after every scripted grant) + its native gain - 5, only when the
    // builder landed (points rose, or a damage hit of the cast was seen: at 5 points nothing can rise).
    void ResolveBuilderStamp(Player* rogue, uint32 seq)
    {
        BuilderStamp* stamp = rogue->CustomData.Get<BuilderStamp>(BUILDER_STAMP_KEY);
        if (!stamp || !stamp->live || stamp->seq != seq)
            return;

        stamp->live = false;
        bool const landed = stamp->landed || rogue->GetComboPoints() > stamp->points;
        int32 const overflow = int32(stamp->points) + stamp->gain - MAX_COMBO_POINTS;
        if (landed && overflow > 0)
            Rogue::BankAnticipation(rogue, int8(std::min<int32>(overflow, MAX_COMBO_POINTS)));
    }

    // U54 (b) / R19: stamp a builder cast (the dispatcher, before its effects; no charged mod is consumed by CalcValue
    // there). A previous live stamp is resolved first. A cast with no native gain needs no stamp.
    void StampBuilder(Player* rogue, SpellInfo const* spellInfo)
    {
        int32 gain = 0;
        for (SpellEffectInfo const& effect : spellInfo->Effects)
            if (effect.IsEffect(SPELL_EFFECT_ADD_COMBO_POINTS))
                gain += effect.CalcValue(rogue);

        BuilderStamp* stamp = rogue->CustomData.GetDefault<BuilderStamp>(BUILDER_STAMP_KEY);
        ResolveBuilderStamp(rogue, stamp->seq);
        if (gain <= 0)
            return;

        stamp->live = true;
        ++stamp->seq;
        stamp->spellId = spellInfo->Id;
        stamp->points = rogue->GetComboPoints();
        stamp->gain = gain;
        stamp->landed = false;

        uint32 const seq = stamp->seq;
        rogue->m_Events.AddEventAtOffset([rogue, seq]()
        {
            ResolveBuilderStamp(rogue, seq);
        }, Milliseconds(1));
    }

    // R3: every scripted grant while a builder stamp is live moves its base, so the +1 ms event's overflow stays right
    // after Seal Fate, the second strike or Quick Draw.
    void RefreshBuilderStamp(Player* rogue)
    {
        if (BuilderStamp* stamp = rogue->CustomData.Get<BuilderStamp>(BUILDER_STAMP_KEY))
            if (stamp->live)
                stamp->points = rogue->GetComboPoints();
    }

    // R4: true once per spent finisher (clears the flag).
    bool ConsumeAnticipationRelease(Player* rogue)
    {
        AnticipationRelease* release = rogue->CustomData.Get<AnticipationRelease>(ANTICIPATION_RELEASE_KEY);
        if (!release || !release->pending)
            return false;

        release->pending = false;
        return true;
    }

    // Deadly Throw (a missile; its points clear at impact): release Anticipation once its points dropped below the
    // cast's count, polled every ANTICIPATION_POLL_MS for at most ANTICIPATION_MISSILE_WAIT_MS (a throw that missed
    // keeps its points: give up silently). The event list dies with the player.
    void PollDeadlyThrowRelease(Player* rogue, ObjectGuid targetGuid, uint8 comboPoints, int32 elapsedMs)
    {
        if (rogue->GetComboPoints() < comboPoints)
        {
            Rogue::ReleaseAnticipation(rogue, ObjectAccessor::GetUnit(*rogue, targetGuid));
            return;
        }

        int32 const stepMs = std::max<int32>(RogueData::ANTICIPATION_POLL_MS, 1);
        if (elapsedMs + stepMs > RogueData::ANTICIPATION_MISSILE_WAIT_MS)
            return;

        rogue->m_Events.AddEventAtOffset([rogue, targetGuid, comboPoints, elapsedMs, stepMs]()
        {
            PollDeadlyThrowRelease(rogue, targetGuid, comboPoints, elapsedMs + stepMs);
        }, Milliseconds(stepMs));
    }

    // Units already in combat with the rogue (its PvE and PvP combat references: the S2 IsInCombatWith convention)
    // within radius of center, alive, attackable by the rogue, never a totem, never exclude; closest to center first,
    // at most maxCount (0 = all).
    std::vector<Unit*> SelectEngagedUnits(Player* rogue, WorldObject const* center, float radius, Unit const* exclude,
        std::size_t maxCount)
    {
        std::vector<Unit*> units;
        auto const consider = [&](Unit* unit)
        {
            if (!unit || unit == exclude || unit == rogue || !unit->IsInWorld() || unit->GetMap() != rogue->GetMap() ||
                !unit->IsAlive() || unit->IsTotem() || !rogue->IsValidAttackTarget(unit) ||
                !center->IsWithinDistInMap(unit, radius))
                return;

            if (std::find(units.begin(), units.end(), unit) == units.end())
                units.push_back(unit);
        };

        for (auto const& [guid, ref] : rogue->GetCombatManager().GetPvECombatRefs())
            consider(ref->GetOther(rogue));
        for (auto const& [guid, ref] : rogue->GetCombatManager().GetPvPCombatRefs())
            consider(ref->GetOther(rogue));

        std::sort(units.begin(), units.end(), [center](Unit const* a, Unit const* b)
        {
            return center->GetExactDistSq(a) < center->GetExactDistSq(b);
        });

        if (maxCount && units.size() > maxCount)
            units.resize(maxCount);

        return units;
    }

    // Blade Flurry (U59, S3a WP-BRIEF section 8): hits that are never copied. The copy itself, hits that already strike
    // several enemies, poison damage (checked by the caller with IsRoguePoisonDamage) and stored shares.
    bool IsBladeFlurryExcluded(uint32 spellId)
    {
        switch (spellId)
        {
            case RogueData::SPELL_BLADE_FLURRY_COPY:
            case FAN_OF_KNIVES_SPELL_ID:
            case FAN_OF_KNIVES_OFF_HAND_SPELL_ID:
            case RogueData::SPELL_SECOND_VOLLEY_MAIN:
            case RogueData::SPELL_SECOND_VOLLEY_OFF:
            case RogueData::SPELL_SINISTER_CALLING_VOLLEY:
            case RogueData::SPELL_THROWING_SPECIALIZATION_COPY:
            case RogueData::SPELL_DEATH_FROM_ABOVE_AREA:
            case RogueData::SPELL_BLADE_RUSH:
            case RogueData::SPELL_DEFT_MANEUVERS_STRIKE:
            case RogueData::SPELL_IMPROVED_RIPOSTE_CLEAVE:
            case RogueData::SPELL_POISON_BOMB:
            case RogueData::SPELL_SHATTERING_VIAL_SPLASH:
            case RogueData::SPELL_DOOMBLADE_TICK:
            case RogueData::SPELL_HEMORRHAGE_TICK:
            case RogueData::SPELL_AKAARIS_ECHO_STRIKE:
                return true;
            default:
                return false;
        }
    }

    // Hack and Slash's dual-strike hands that may roll as their parent's cast (the poison allow-list's halves; Deft
    // Maneuvers' strike is a triggered area hit and rolls no Hack and Slash).
    bool IsDualStrikeHand(uint32 spellId)
    {
        switch (spellId)
        {
            case 5374:
            case 27576:
            case RogueData::SPELL_MUTILATE_MH:
            case RogueData::SPELL_MUTILATE_OH:
            case RogueData::SPELL_KINGSBANE_MH:
            case RogueData::SPELL_KINGSBANE_OH:
                return true;
            default:
                return false;
        }
    }

    // A one-handed weapon (not INVTYPE_2HWEAPON) usable in that hand.
    bool IsOneHandedWeaponIn(Player const* rogue, WeaponAttackType attType)
    {
        Item const* weapon = rogue->GetWeaponForAttack(attType, true);
        return IsWeapon(weapon) && weapon->GetTemplate()->InventoryType != INVTYPE_2HWEAPON;
    }
}

namespace Rogue
{
    // ---- RG0a: energy haste ----

    bool IsEnergyUser(Player const* player)
    {
        if (!player)
            return false;

        // The one Classless change point (PLAN 1D.14): rogues and druids (Cat Form spends energy) regenerate faster.
        return player->IsClass(CLASS_ROGUE, CLASS_CONTEXT_ABILITY) ||
            player->IsClass(CLASS_DRUID, CLASS_CONTEXT_ABILITY);
    }

    int32 GetEnergyHastePct(Unit const* unit)
    {
        if (!unit)
            return 0;

        // A rate, not a cooldown cut: energy fills 1 + h times as fast, so the regen bonus is 100 / castSpeed - 100.
        // UNIT_MOD_CAST_SPEED holds haste rating, casting-speed and combat-speed auras (the custom_haste_gcd.cpp read),
        // so melee-only attack speed (Slice and Dice) never counts. A net slow clamps to 0.
        float const castSpeed = unit->GetFloatValue(UNIT_MOD_CAST_SPEED);
        if (castSpeed <= 0.0f)
            return 0;

        int32 const maxPct = std::max<int32>(RogueData::ENERGY_HASTE_MAX_PCT, 0);
        return std::clamp<int32>(int32(std::lround(100.0f / castSpeed - 100.0f)), 0, maxPct);
    }

    void EnsureEnergyHaste(Player* player)
    {
        if (!player)
            return;

        uint32 const spellId = RogueData::SPELL_ENERGY_HASTE;
        if (!IsEnergyUser(player))
        {
            // A class change (GM, Classless) left it behind: removeSpell also drops the owned aura.
            if (player->HasSpell(spellId))
                player->removeSpell(spellId, SPEC_MASK_ALL, false);
            else if (player->HasAura(spellId))
                player->RemoveAurasDueToSpell(spellId);

            return;
        }

        if (player->HasAura(spellId))
            return;

        // The EnsureHasteGcdAura shape: teach silently (addSpell casts the passive; learnSpell would announce it), or
        // recast if known but the aura is gone (mod-playerbots Randomize strips auras).
        if (!player->HasSpell(spellId))
            player->addSpell(spellId, SPEC_MASK_ALL, true);
        else
            player->CastSpell(player, spellId, true);
    }

    void SyncEnergyHaste(Unit* owner, AuraEffect* regen)
    {
        if (!owner || !regen)
            return;

        // CHANGE_AMOUNT -> HandleModPowerRegen -> UpdateEnergyRegen writes the regen modifier the client predicts from.
        int32 const pct = GetEnergyHastePct(owner);
        if (regen->GetAmount() != pct)
            regen->ChangeAmount(pct, false);
    }

    // ---- RG0a: poisons as self auras ----

    PoisonSlot GetPoisonSlot(uint32 auraSpellId)
    {
        switch (auraSpellId)
        {
            case RogueData::SPELL_INSTANT_POISON_203701:
            case RogueData::SPELL_DEADLY_POISON_203702:
            case RogueData::SPELL_WOUND_POISON_203703:
                return PoisonSlot::Lethal;
            case RogueData::SPELL_CRIPPLING_POISON_203704:
            case RogueData::SPELL_MIND_NUMBING_POISON_203705:
            case RogueData::SPELL_ANESTHETIC_POISON_203706:
                return PoisonSlot::NonLethal;
            default:
                return PoisonSlot::None;
        }
    }

    uint8 GetLethalSlots(Player const* rogue)
    {
        // S1: Master Poisoner's capstone (rank 3, 58410) holds two Lethal poisons at once.
        if (rogue && rogue->HasAura(RogueData::SPELL_MASTER_POISONER_58410))
            return 2;

        return uint8(std::max<int32>(RogueData::POISON_LETHAL_SLOTS, 1));
    }

    void EnforceLethalSlots(Player* rogue, uint32 keptAuraId)
    {
        if (!rogue)
            return;

        uint8 const slots = GetLethalSlots(rogue);
        while (true)
        {
            uint8 held = 0;
            Aura* oldest = nullptr;
            for (uint32 const auraId : LETHAL_POISON_AURAS)
            {
                Aura* aura = rogue->GetAura(auraId, rogue->GetGUID());
                if (!aura)
                    continue;

                ++held;
                if (auraId == keptAuraId)
                    continue;

                // GetApplyTime() is in seconds, so ties are common (a two-poison macro lands in one second): the
                // array is in ascending id order and only a strictly older aura replaces the pick, so a tie keeps the
                // lowest id.
                if (!oldest || aura->GetApplyTime() < oldest->GetApplyTime())
                    oldest = aura;
            }

            if (held <= slots || !oldest)
                return;

            oldest->Remove();
        }
    }

    bool PoisonRollAllowed(Unit const* rogue, ProcEventInfo& eventInfo, uint32 auraId)
    {
        // 1. Only the rogue's own action rolls (a pet's or anyone else's hit never does).
        Unit* actor = eventInfo.GetActor();
        if (!rogue || !actor || actor != rogue)
            return false;

        // 2. A valid, living, hostile target other than the rogue: a melee-class spell with a self-targeted effect
        // (Feint, P0 M1) makes the caster a hit target of its own cast.
        Unit* target = eventInfo.GetActionTarget();
        if (!target || target == actor || !target->IsAlive() || !actor->IsValidAttackTarget(target))
            return false;

        if (Spell const* spell = eventInfo.GetProcSpell())
        {
            SpellInfo const* spellInfo = spell->GetSpellInfo();
            if (!spellInfo)
                return false;

            // 3a. U2: Sap, Gouge, Blind (and anything else that breaks on damage or suppresses weapon procs) never
            // poison. Load-bearing: the aura-proc path ignores the stock item-enchant exemption (0-verify C3).
            if (spellInfo->HasAttribute(SPELL_ATTR0_CANCELS_AUTO_ATTACK_COMBAT) ||
                spellInfo->HasAttribute(SPELL_ATTR4_SUPPRESS_WEAPON_PROCS))
                return false;

            // 3a'. Triggered casts roll nothing, except the allow-listed halves above.
            if (spell->IsTriggered() &&
                std::find(std::begin(TRIGGERED_ROLLERS), std::end(TRIGGERED_ROLLERS), spellInfo->Id) ==
                    std::end(TRIGGERED_ROLLERS))
                return false;

            // 3a''. U3: Shiv's own strike rolls no Lethal poison (its script applies every Lethal at 100% through
            // ApplyLethalPoisons); the Non-lethal poison rolls as on any ability.
            if (spellInfo->Id == RogueData::SPELL_SHIV_203725 && GetPoisonSlot(auraId) == PoisonSlot::Lethal)
                return false;

            // 3a'''. U12: Blindside's empowered Sinister Strike rolls no Lethal poison either (its script applies every
            // Lethal at 100% in AfterHit; procs run before AfterHit, so the stamp is set in BeforeCast); the
            // Non-lethal poison still rolls.
            if (spellInfo->Id == RogueData::SPELL_SINISTER_STRIKE && IsBlindsideEmpowered(rogue, spell) &&
                GetPoisonSlot(auraId) == PoisonSlot::Lethal)
                return false;

            // 3b. Fan of Knives: one HIT event per target already, every target rolls. S3: Blade Rush's area strike
            // and Deft Maneuvers' strike roll the same way (C10).
            if (spellInfo->Id == FAN_OF_KNIVES_SPELL_ID || spellInfo->Id == RogueData::SPELL_BLADE_RUSH ||
                spellInfo->Id == RogueData::SPELL_DEFT_MANEUVERS_STRIKE)
                return true;

            // 3c. A targeted cast rolls only on its own target.
            if (Unit const* castTarget = spell->m_targets.GetUnitTarget())
                if (castTarget != target)
                    return false;

            // 3d. Once per cast per aura: a second event on the same target at the same game time is the same cast
            // or a sibling of it (Mutilate's two halves). Accepted edge: the clock only advances once per world
            // update, so two different casts landing on one target in the same update roll once per aura.
            PoisonCastGuard* guard = actor->CustomData.GetDefault<PoisonCastGuard>(POISON_CAST_GUARD_KEY);
            PoisonCastEntry& entry = guard->byAura[auraId];
            int64 const now = NowMs();
            ObjectGuid const targetGuid = target->GetGUID();
            if (entry.timeMs == now && entry.target == targetGuid)
                return false;

            entry.timeMs = now;
            entry.target = targetGuid;
            return true;
        }

        // 4. Auto attack: extra attacks (Sword Specialization, Hack and Slash, ...) roll nothing.
        return actor->GetLastExtraAttackSpell() == 0;
    }

    bool RollPoison(Player* rogue, uint32 auraId, ProcEventInfo& eventInfo)
    {
        if (!rogue)
            return false;

        int32 const baseChance = GetPoisonBaseChancePct(auraId);
        if (baseChance <= 0)
            return false;

        // Points first: base + SPELLMOD_CHANCE_OF_SUCCESS mods on the aura id (Improved Poisons and later talents).
        float chance = float(baseChance);
        rogue->ApplySpellMod(auraId, SPELLMOD_CHANCE_OF_SUCCESS, chance);

        // Then the speed factor, melee auto attacks only: the hitting hand's unhasted speed / 2600 (GetAttackTime
        // divides the hasted field by m_modAttackSpeedPct), so a slow weapon does not lose poison applications.
        if (!eventInfo.GetProcSpell() && (eventInfo.GetTypeMask() & PROC_FLAG_DONE_MELEE_AUTO_ATTACK))
        {
            DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
            WeaponAttackType const attType = damageInfo ? damageInfo->GetAttackType() : BASE_ATTACK;
            int32 const referenceMs = std::max<int32>(RogueData::POISON_REFERENCE_WEAPON_SPEED_MS, 1);
            chance *= float(rogue->GetAttackTime(attType)) / float(referenceMs);
        }

        // Then Proc Chance (the native roll's multiplier never matters: spell_proc Chance 100 always passes it).
        chance *= 1.0f + rogue->GetProcChancePercentage() / 100.0f;

        // S1 Venomous Fan capstone: Fan of Knives' poison chance x 2 after Proc Chance (the cap below still holds).
        if (Spell const* procSpell = eventInfo.GetProcSpell())
            if (procSpell->GetSpellInfo()->Id == FAN_OF_KNIVES_SPELL_ID &&
                rogue->HasAura(RogueData::SPELL_VENOMOUS_FAN_203810))
                chance *= float(RogueData::VENOMOUS_FAN_POISON_MULT);

        return roll_chance_f(std::min(chance, 100.0f));
    }

    void ApplyPoison(Player* rogue, Unit* target, uint32 payloadId, AuraEffect const* triggeredBy,
        PoisonSource /*source*/)
    {
        if (!rogue || !target || !payloadId)
            return;

        // Every application casts the payload the same way, whatever the source (roll, Shiv, Blindside, Poison Bomb,
        // Deadly Brew). Every payload is 100 yd: a script cast is range-checked (C4).
        if (rogue->CastSpell(target, payloadId, TRIGGERED_FULL_MASK, nullptr, triggeredBy) != SPELL_CAST_OK)
            return;

        // S1 Kingsbane: a Lethal application on the target carrying this rogue's Kingsbane DoT counts, a refresh at
        // 5 Deadly stacks included; Envenom's buff doubles it. Only Kingsbane's own target ever carries the DoT.
        bool const lethalPayload = payloadId == RogueData::SPELL_INSTANT_POISON_8680 ||
            payloadId == RogueData::SPELL_DEADLY_POISON || payloadId == RogueData::SPELL_WOUND_POISON;
        if (lethalPayload && target->GetAura(RogueData::SPELL_KINGSBANE_DOT, rogue->GetGUID()))
            AddKingsbaneStacks(rogue, target, uint8(rogue->HasAura(RogueData::SPELL_ENVENOM) ?
                RogueData::KINGSBANE_ENVENOM_STACKS : 1));

        // S1 Deadly Brew: Instant, Deadly or Mind-numbing applies Crippling Poison (rank % x Proc Chance, internal
        // cooldown). The Crippling payload itself never re-enters either branch.
        bool const brewPayload = payloadId == RogueData::SPELL_INSTANT_POISON_8680 ||
            payloadId == RogueData::SPELL_DEADLY_POISON || payloadId == RogueData::SPELL_MIND_NUMBING_POISON;
        if (!brewPayload || !TalentCooldownReady(rogue, RogueData::SPELL_DEADLY_BREW))
            return;

        int32 const brewPct = GetRankAmount(rogue, { RogueData::SPELL_DEADLY_BREW, RogueData::SPELL_DEADLY_BREW_51626 },
            EFFECT_0);
        if (brewPct <= 0 || !RollProcChance(rogue, float(brewPct)))
            return;

        StartTalentCooldown(rogue, RogueData::SPELL_DEADLY_BREW, RogueData::DEADLY_BREW_ICD_MS);
        ApplyPoison(rogue, target, RogueData::SPELL_CRIPPLING_POISON, nullptr, PoisonSource::Talent);
    }

    void ApplyLethalPoisons(Player* rogue, Unit* target, PoisonSource source)
    {
        if (!rogue || !target || !target->IsAlive())
            return;

        // Every Lethal aura held (a second slot from S1 is covered), 100%: no roll, no Proc Chance. The payload id is
        // the aura row's effect 0 TriggerSpell, the same one the roll path casts.
        for (uint32 const auraId : LETHAL_POISON_AURAS)
        {
            Aura* aura = rogue->GetAura(auraId, rogue->GetGUID());
            if (!aura)
                continue;

            AuraEffect const* triggeredBy = aura->GetEffect(EFFECT_0);
            if (!triggeredBy)
                continue;

            ApplyPoison(rogue, target, aura->GetSpellInfo()->Effects[EFFECT_0].TriggerSpell, triggeredBy, source);
        }
    }

    bool HasAnyPoison(Player const* rogue)
    {
        if (!rogue)
            return false;

        return std::any_of(POISON_AURAS.begin(), POISON_AURAS.end(), [rogue](uint32 auraId)
        {
            return rogue->HasAura(auraId);
        });
    }

    void ApplyPoisonGlow(Player* player)
    {
        if (!player)
            return;

        for (uint8 const slot : GLOW_SLOTS)
            WritePoisonGlow(player, slot);
    }

    void WritePoisonGlow(Player* player, uint8 slot)
    {
        if (!player || (slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND))
            return;

        if (!IsWeapon(player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot)) || !HasAnyPoison(player))
            return;

        // Only the temp half of the visible-item enchant field (PlayerStorage.cpp SetVisibleItemSlot): no item or DB
        // change, the item's real enchants stay on it. A real temp enchant (stone, oil) may hide the glow (P0-RESULTS).
        player->SetUInt16Value(PLAYER_VISIBLE_ITEM_1_ENCHANTMENT + (slot * 2), 1,
            uint16(RogueData::POISON_GLOW_ENCHANT));
    }

    void RestorePoisonGlow(Player* player)
    {
        if (!player)
            return;

        // SetVisibleItemSlot rewrites the real values; the visible-slot hook then re-applies the glow while another
        // poison is still up (the removed aura is already gone when AfterEffectRemove runs).
        for (uint8 const slot : GLOW_SLOTS)
            if (Item* item = player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot))
                player->SetVisibleItemSlot(slot, item);
    }

    // ---- S1 ----
    // Assassination (docs/reworks/rogue-assassination-rework.md). Cross-spec rule (S1-HANDOFF section 7): one
    // dispatcher, one combo-point helper, one Proc Chance roll, one stored-bleed helper, one health clause; S2 / S3
    // append cases here, never fork them. Talent ranks are read with HasAura on their rank spell ids.

    bool RollProcChance(Player const* rogue, float pct)
    {
        if (!rogue || pct <= 0.0f)
            return false;

        return roll_chance_f(std::min(pct * (1.0f + rogue->GetProcChancePercentage() / 100.0f), 100.0f));
    }

    void GainComboPoints(Player* rogue, Unit* target, int8 count)
    {
        if (!rogue || !count)
            return;

        // RG0b-DIAGNOSIS: the points go where the client shows them and a targeted finisher reads them. Never an
        // area-hit unit the rogue has not selected: callers pass the strike's single target or nothing.
        if (!target || !target->IsAlive() || !rogue->IsValidAttackTarget(target))
            target = GetSelectedHostile(rogue);

        // S3 Anticipation (U54 (a)): points past 5 are banked before the core cap drops them (no-op without
        // Restless Blades). Points follow the rogue to a new target, so the held count is the base.
        if (count > 0)
        {
            int32 const overflow = int32(rogue->GetComboPoints()) + count - MAX_COMBO_POINTS;
            if (overflow > 0)
                BankAnticipation(rogue, int8(overflow));
        }

        // Nothing hostile left: park the points on the rogue (ComboPointMechanics.cpp header).
        rogue->AddComboPoints(target ? target : rogue, count);

        // R3: a live builder stamp counts this grant in its base.
        RefreshBuilderStamp(rogue);
    }

    int32 GetRankAmount(Player const* rogue, std::initializer_list<uint32> rankIds, SpellEffIndex eff)
    {
        if (!rogue)
            return 0;

        SpellInfo const* rank = GetHeldRank(rogue, rankIds);
        if (!rank)
            return 0;

        // The live aura effect (spell mods included) when the effect is an aura, else the row's value.
        if (AuraEffect const* effect = rogue->GetAuraEffect(rank->Id, eff, rogue->GetGUID()))
            return effect->GetAmount();

        return rank->Effects[eff].CalcValue();
    }

    void OnSpellCast(Player* rogue, Spell const* spell)
    {
        if (!rogue || !spell || spell->IsTriggered())
            return;

        SpellInfo const* spellInfo = spell->GetSpellInfo();
        if (!spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_ROGUE)
            return;

        // S3 Prey on the Weak (U60, R11): every damaging cast keeps this rogue's > 90% crit debuff on its explicit
        // target up to date (the rank and hostility gates are inside).
        if (Unit* explicitTarget = spell->m_targets.GetUnitTarget())
            if (explicitTarget != rogue && HasDamageEffect(spellInfo))
                UpdatePreyCritDebuff(rogue, explicitTarget);

        // The once-per-cast stamp: a fresh record, before the hands' (or the missile's) hits can reach it.
        switch (spellInfo->Id)
        {
            case RogueData::SPELL_MUTILATE:
            case RogueData::SPELL_KINGSBANE:
            case FAN_OF_KNIVES_SPELL_ID:
            {
                StrikeCastRecord& record =
                    rogue->CustomData.GetDefault<StrikeCastState>(STRIKE_CAST_STATE_KEY)->byParent[spellInfo->Id];
                record = StrikeCastRecord();
                record.target = spell->m_targets.GetUnitTargetGUID();

                // S2 Second Volley: a second Fan of Knives 300 ms later. The copy is triggered, so it never re-enters
                // the dispatcher (no third fan); the event list dies with the player.
                if (spellInfo->Id == FAN_OF_KNIVES_SPELL_ID)
                {
                    int32 const volleyPct = GetRankAmount(rogue, { RogueData::SPELL_SECOND_VOLLEY,
                        RogueData::SPELL_SECOND_VOLLEY_204137 }, EFFECT_0);
                    if (volleyPct > 0 && RollProcChance(rogue, float(volleyPct)))
                        rogue->m_Events.AddEventAtOffset([rogue]()
                        {
                            if (rogue->IsAlive())
                                rogue->CastSpell(rogue, RogueData::SPELL_SECOND_VOLLEY_MAIN, TRIGGERED_FULL_MASK);
                        }, Milliseconds(RogueData::SECOND_VOLLEY_DELAY_MS));

                    // S3 Adrenaline Rush: +1 point per cast onto the selection; Fan of Knives' own award is stamped at
                    // impact (StampFanOfKnivesGain from spell_rog_fan_of_knives), so no stamp here.
                    if (HasAdrenalineRush(rogue))
                        GainComboPoints(rogue, nullptr, int8(RogueData::ADRENALINE_RUSH_EXTRA_POINTS));
                }

                // S3 Anticipation (R19): Mutilate / Kingsbane get the U54 (b) stamp; their hands' hits set its landed
                // flag through GetStrikeParent.
                if (spellInfo->Id != FAN_OF_KNIVES_SPELL_ID)
                    StampBuilder(rogue, spellInfo);

                return;
            }
            default:
                break;
        }

        // S3 builder branch: a non-triggered cast with an ADD_COMBO_POINTS effect (Adrenaline Rush's point, Celerity,
        // the U54 (b) stamp). A builder is never Premeditation's trigger nor a finisher: fall through.
        if (HasAddComboPointsEffect(spellInfo))
            OnBuilderCast(rogue, spell);

        // S2 Premeditation (passive): Shadow Dance or Vanish adds points to the selection (parked without one); points
        // past 5 are lost by the core cap.
        if (spellInfo->Id == RogueData::SPELL_SHADOW_DANCE ||
            spellInfo->GetFirstRankSpell()->Id == RogueData::SPELL_VANISH)
        {
            int32 const points = GetRankAmount(rogue, { RogueData::SPELL_PREMEDITATION_204153 }, EFFECT_0);
            if (points > 0)
                GainComboPoints(rogue, nullptr, int8(points));

            return;
        }

        // Finisher branch. The hook runs before the finisher's effects, so the points are not spent yet.
        if (!spellInfo->NeedsComboPoints())
            return;

        uint8 const comboPoints = rogue->GetComboPoints();
        if (!comboPoints)
            return;

        Unit* target = spell->m_targets.GetUnitTarget();

        // S2 spent-point clauses (S2a-REVIEW L3): Shadow Dance's reduction, Relentless Strikes, the Executioner capstone
        // and Sinister Calling count only the points a finisher actually spends. A melee finisher spends them in its
        // own finish phase, this update, and keeps them on a miss, dodge or parry: the clauses run one update later and
        // only if the points are gone. Scheduled before Ruthlessness's +1 point (same offset, insertion order), so that
        // point never reads as kept. Deadly Throw is a missile whose points clear at impact: it keeps the cast-start
        // path (a dodged throw still counts; playtest guide). Spent = fewer points than at cast, not none: Shadow
        // Dance or Vanish in the same update adds Premeditation's points after the spend (S2-CODE-REVIEW L1); kept
        // points stay at or above the cast's count.
        bool const executionerBelow = target && target->HealthBelowPct(RogueData::EXECUTIONER_HEALTH_PCT);
        bool const danceCoolingAtCast = rogue->HasSpellCooldown(RogueData::SPELL_SHADOW_DANCE);
        // S3 (R4): the same event then runs Combat's spent clauses (Restless Blades, Hair Trigger), which mark the
        // finisher spent for the Anticipation release scheduled after Ruthlessness's point below. Deadly Throw runs
        // them at cast and releases from a poll once its points drop (its missile clears them at impact).
        uint32 const finisherId = spellInfo->Id;
        if (finisherId == RogueData::SPELL_DEADLY_THROW)
        {
            ApplySpentFinisherClauses(rogue, target, comboPoints, executionerBelow, danceCoolingAtCast);
            ApplyCombatSpentClauses(rogue, target, finisherId, comboPoints);
            // The poll releases on its own: the flag is for the melee finishers' release event only.
            ConsumeAnticipationRelease(rogue);
            if (rogue->HasAura(RogueData::SPELL_RESTLESS_BLADES))
                PollDeadlyThrowRelease(rogue, target ? target->GetGUID() : ObjectGuid::Empty, comboPoints, 0);
        }
        else
        {
            ObjectGuid const targetGuid = target ? target->GetGUID() : ObjectGuid::Empty;
            rogue->m_Events.AddEventAtOffset([rogue, targetGuid, comboPoints, executionerBelow, danceCoolingAtCast,
                finisherId]()
            {
                if (rogue->GetComboPoints() < comboPoints)
                {
                    Unit* spentTarget = ObjectAccessor::GetUnit(*rogue, targetGuid);
                    ApplySpentFinisherClauses(rogue, spentTarget, comboPoints, executionerBelow, danceCoolingAtCast);
                    ApplyCombatSpentClauses(rogue, spentTarget, finisherId, comboPoints);
                }
            }, Milliseconds(1));
        }

        // Ruthlessness (melee finishers; not Deadly Throw): +1 point after the finisher's ClearComboPoints, so one
        // update later, with the target re-resolved (the event list dies with the player).
        if (spellInfo->Id != RogueData::SPELL_DEADLY_THROW &&
            TalentCooldownReady(rogue, RogueData::SPELL_RUTHLESSNESS))
        {
            int32 const ruthlessPct = GetRankAmount(rogue, { RogueData::SPELL_RUTHLESSNESS,
                RogueData::SPELL_RUTHLESSNESS_14160, RogueData::SPELL_RUTHLESSNESS_14161 }, EFFECT_2);
            if (ruthlessPct > 0 && RollProcChance(rogue, float(ruthlessPct)))
            {
                StartTalentCooldown(rogue, RogueData::SPELL_RUTHLESSNESS, RogueData::RUTHLESSNESS_ICD_MS);
                ObjectGuid const targetGuid = target ? target->GetGUID() : ObjectGuid::Empty;
                // A finisher that misses, is dodged or parried keeps its points (Spell.cpp clears them only for a
                // hit): the point is granted only if they were spent (fewer than at cast: Premeditation may add
                // points in the same update), so it never stacks onto points that stayed.
                rogue->m_Events.AddEventAtOffset([rogue, targetGuid, comboPoints]()
                {
                    if (rogue->GetComboPoints() < comboPoints)
                        GainComboPoints(rogue, ObjectAccessor::GetUnit(*rogue, targetGuid), 1);
                }, Milliseconds(1));
            }
        }

        // S3 Anticipation release (R4): a third event at the same offset, after the spent clauses and Ruthlessness's
        // point (insertion order), so the stored points never feed the finisher that releases them nor hide its
        // spend from Ruthlessness. It runs only when the spent-clause event marked the points spent.
        if (spellInfo->Id != RogueData::SPELL_DEADLY_THROW)
        {
            ObjectGuid const releaseTargetGuid = target ? target->GetGUID() : ObjectGuid::Empty;
            rogue->m_Events.AddEventAtOffset([rogue, releaseTargetGuid]()
            {
                if (ConsumeAnticipationRelease(rogue))
                    ReleaseAnticipation(rogue, ObjectAccessor::GetUnit(*rogue, releaseTargetGuid));
            }, Milliseconds(1));
        }

        // Fleet Footed (every finisher): 10% per point to break free of movement impairing effects.
        int32 const fleetPct = GetRankAmount(rogue, { RogueData::SPELL_FLEET_FOOTED,
            RogueData::SPELL_FLEET_FOOTED_31209, RogueData::SPELL_FLEET_FOOTED_203824 }, EFFECT_1);
        if (fleetPct > 0 && RollProcChance(rogue, float(fleetPct * comboPoints)))
            rogue->RemoveMovementImpairingAuras(true);

        // S2 Finality: was this finisher's buff held at cast? ResolveFinality reads it after the hit (Death from Above
        // shares Eviscerate's key: its landing consumes or grants the Eviscerate buff).
        if (rogue->HasAura(RogueData::SPELL_FINALITY) || rogue->HasAura(RogueData::SPELL_FINALITY_204141))
            if (uint32 const finalityKey = GetFinalityKey(spellInfo->Id))
                rogue->CustomData.GetDefault<FinalityState>(FINALITY_STATE_KEY)->heldAtCast[finalityKey] =
                    rogue->HasAura(GetFinalityBuff(finalityKey));

        if (!target)
            return;

        // Shattering Vial (Envenom, Rupture): 5% per point to splash the target.
        if (spellInfo->Id == RogueData::SPELL_ENVENOM || spellInfo->Id == RogueData::SPELL_RUPTURE)
        {
            int32 const vialPct = GetRankAmount(rogue, { RogueData::SPELL_SHATTERING_VIAL }, EFFECT_0);
            if (vialPct > 0 && RollProcChance(rogue, float(vialPct * comboPoints)))
                rogue->CastSpell(target, RogueData::SPELL_SHATTERING_VIAL_SPLASH, TRIGGERED_FULL_MASK);
        }

        // Cut Throat (Envenom): rank % per point to Garrote the target from any side (brief R1).
        if (spellInfo->Id == RogueData::SPELL_ENVENOM)
        {
            int32 const cutPct = GetRankAmount(rogue, { RogueData::SPELL_CUT_THROAT,
                RogueData::SPELL_CUT_THROAT_203815 }, EFFECT_0);
            if (cutPct > 0 && RollProcChance(rogue, float(cutPct * comboPoints)))
                rogue->CastSpell(target, RogueData::SPELL_GARROTE, TRIGGERED_FULL_MASK);
        }

        // S2 Honor Among Thieves: stamp the cast whose first crit may trigger it (OnFinisherCrit).
        switch (spellInfo->Id)
        {
            case RogueData::SPELL_EVISCERATE:
            case RogueData::SPELL_DEADLY_THROW:
            case RogueData::SPELL_DEATH_FROM_ABOVE:
            case RogueData::SPELL_BETWEEN_THE_EYES:
            {
                if (!rogue->HasAura(RogueData::SPELL_HONOR_AMONG_THIEVES_51701))
                    break;

                HonorAmongThievesState* honor =
                    rogue->CustomData.GetDefault<HonorAmongThievesState>(HONOR_AMONG_THIEVES_STATE_KEY);
                honor->castSpellId = spellInfo->Id;
                honor->primary = target->GetGUID();
                honor->triggered = false;
                break;
            }
            default:
                break;
        }
    }

    bool IsRogueBleed(SpellInfo const* spellInfo)
    {
        if (!spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_ROGUE)
            return false;

        // S2's Hemorrhage bleed and tick (doc Q11) count too: Wound Poison's 271 mask and Zoldyck follow.
        switch (spellInfo->GetFirstRankSpell()->Id)
        {
            case RogueData::SPELL_RUPTURE:
            case RogueData::SPELL_GARROTE:
            case RogueData::SPELL_DOOMBLADE_BLEED:
            case RogueData::SPELL_DOOMBLADE_TICK:
            case RogueData::SPELL_HEMORRHAGE_BLEED:
            case RogueData::SPELL_HEMORRHAGE_TICK:
                return true;
            default:
                return false;
        }
    }

    bool IsRoguePoisonDamage(SpellInfo const* spellInfo)
    {
        return spellInfo && spellInfo->SpellFamilyName == SPELLFAMILY_ROGUE &&
            (spellInfo->SpellFamilyFlags[1] & POISON_GROUP_D1) && HasDamageEffect(spellInfo);
    }

    uint8 CountOwnPoisons(Player const* rogue, Unit const* target)
    {
        if (!rogue || !target)
            return 0;

        // GetAppliedAuras is a multimap ordered by spell id: count each id once (stacks per caster share it).
        uint8 count = 0;
        uint32 lastCounted = 0;
        for (auto const& [spellId, aurApp] : target->GetAppliedAuras())
        {
            Aura const* aura = aurApp->GetBase();
            if (spellId == lastCounted || aura->GetCasterGUID() != rogue->GetGUID() ||
                aura->GetSpellInfo()->Dispel != DISPEL_POISON)
                continue;

            lastCounted = spellId;
            ++count;
        }

        return count;
    }

    uint8 CountOwnBleeds(Player const* rogue, Unit const* target)
    {
        if (!rogue || !target)
            return 0;

        uint8 count = 0;
        uint32 lastCounted = 0;
        for (auto const& [spellId, aurApp] : target->GetAppliedAuras())
        {
            Aura const* aura = aurApp->GetBase();
            if (spellId == lastCounted || aura->GetCasterGUID() != rogue->GetGUID() ||
                !IsRogueBleed(aura->GetSpellInfo()))
                continue;

            lastCounted = spellId;
            ++count;
        }

        return count;
    }

    void RecordStrikeHit(Player* rogue, Unit* target, SpellInfo const* spellInfo, uint32 damage, bool crit)
    {
        if (!rogue || !target || !spellInfo)
            return;

        uint32 const parentId = GetStrikeParent(spellInfo->Id);
        if (!parentId)
            return;

        StrikeCastState* state = rogue->CustomData.Get<StrikeCastState>(STRIKE_CAST_STATE_KEY);
        if (!state)
            return;

        // No stamp (a triggered parent, or a strike from before the dispatcher stamped): nothing to resolve.
        auto const itr = state->byParent.find(parentId);
        if (itr == state->byParent.end() || itr->second.resolved)
            return;

        StrikeCastRecord& record = itr->second;
        if (parentId == FAN_OF_KNIVES_SPELL_ID)
        {
            // Fan of Knives: its first crit, on any target, resolves the cast's crit talents once. Seal Fate's
            // point goes to the selection, never to the area-hit unit (RG0b-DIAGNOSIS).
            if (!crit)
                return;

            record.resolved = true;
            RollSealFate(rogue, GetSelectedHostile(rogue));
            RollFocusedAttacks(rogue);
            return;
        }

        // Dual-strike hands: both land on the parent's target inside its launch phase, before its AfterCast.
        if (record.target != target->GetGUID())
            return;

        record.totalDamage += damage;
        record.crit = record.crit || crit;
    }

    void ResolveDualStrike(Player* rogue, Unit* target, uint32 parentSpellId)
    {
        if (!rogue)
            return;

        StrikeCastState* state = rogue->CustomData.Get<StrikeCastState>(STRIKE_CAST_STATE_KEY);
        if (!state)
            return;

        auto const itr = state->byParent.find(parentSpellId);
        if (itr == state->byParent.end())
            return;

        StrikeCastRecord const record = itr->second;
        state->byParent.erase(itr);

        if (!target)
            target = ObjectAccessor::GetUnit(*rogue, record.target);

        if (record.crit)
        {
            RollSealFate(rogue, target);
            RollFocusedAttacks(rogue);
        }

        if (parentSpellId != RogueData::SPELL_MUTILATE)
            return;

        // Doomblade: a share of the whole cast's damage (both hands) as a stored bleed, when either hand crit.
        if (record.crit && target)
        {
            int32 const doombladePct = GetRankAmount(rogue, { RogueData::SPELL_DOOMBLADE,
                RogueData::SPELL_DOOMBLADE_203804 }, EFFECT_0);
            uint32 const share = doombladePct > 0 ? uint32(uint64(record.totalDamage) * uint32(doombladePct) / 100) : 0;
            if (share)
                ApplyStoredBleed(rogue, target, RogueData::SPELL_DOOMBLADE_BLEED, share);
        }

        // Blindside: the next Sinister Strike is free and empowered.
        int32 const blindsidePct = GetRankAmount(rogue, { RogueData::SPELL_BLINDSIDE,
            RogueData::SPELL_BLINDSIDE_203806 }, EFFECT_0);
        if (blindsidePct > 0 && RollProcChance(rogue, float(blindsidePct)))
            rogue->CastSpell(rogue, RogueData::SPELL_BLINDSIDE_BUFF, TRIGGERED_FULL_MASK);

        // Quick Recovery: energy back through the stock energize (custom value, brief R8).
        int32 const recoveryPct = GetRankAmount(rogue, { RogueData::SPELL_QUICK_RECOVERY,
            RogueData::SPELL_QUICK_RECOVERY_31245 }, EFFECT_0);
        if (recoveryPct > 0 && RollProcChance(rogue, float(recoveryPct)))
        {
            int32 const energy = RogueData::QUICK_RECOVERY_ENERGY;
            rogue->CastCustomSpell(rogue, QUICK_RECOVERY_ENERGIZE_SPELL_ID, &energy, nullptr, nullptr, true);
        }
    }

    void RollSealFate(Player* rogue, Unit* target)
    {
        if (!rogue)
            return;

        // The rank's own ProcChance (33 / 66 / 100) is the chance; single strikes roll the same row natively.
        SpellInfo const* rank = GetHeldRank(rogue, { RogueData::SPELL_SEAL_FATE, RogueData::SPELL_SEAL_FATE_14190,
            RogueData::SPELL_SEAL_FATE_14193 });
        if (rank && RollProcChance(rogue, float(rank->ProcChance)))
            GainComboPoints(rogue, target, 1);
    }

    void RollFocusedAttacks(Player* rogue)
    {
        if (!rogue)
            return;

        SpellInfo const* rank = GetHeldRank(rogue, { RogueData::SPELL_FOCUSED_ATTACKS,
            RogueData::SPELL_FOCUSED_ATTACKS_51635, RogueData::SPELL_FOCUSED_ATTACKS_51636 });
        if (rank && RollProcChance(rogue, float(rank->ProcChance)))
            rogue->CastSpell(rogue, RogueData::SPELL_FOCUSED_ATTACKS_ENERGIZE, TRIGGERED_FULL_MASK);
    }

    void MarkBlindsideEmpowered(Player* rogue, Spell const* spell)
    {
        if (!rogue || !spell)
            return;

        BlindsideStamp* stamp = rogue->CustomData.GetDefault<BlindsideStamp>(BLINDSIDE_STAMP_KEY);
        stamp->spell = spell;
        stamp->timeMs = NowMs();
    }

    bool IsBlindsideEmpowered(Unit const* rogue, Spell const* spell)
    {
        if (!rogue || !spell)
            return false;

        // An instant melee strike runs BeforeCast, its procs, AfterHit and AfterCast in one update.
        BlindsideStamp const* stamp = rogue->CustomData.Get<BlindsideStamp>(BLINDSIDE_STAMP_KEY);
        return stamp && stamp->spell == spell && stamp->timeMs == NowMs();
    }

    void ClearBlindsideEmpowered(Player* rogue)
    {
        if (!rogue)
            return;

        if (BlindsideStamp* stamp = rogue->CustomData.Get<BlindsideStamp>(BLINDSIDE_STAMP_KEY))
        {
            stamp->spell = nullptr;
            stamp->timeMs = -1;
        }
    }

    void ApplyStoredBleed(Player* rogue, Unit* target, uint32 bleedAuraId, uint32 totalDamage)
    {
        if (!rogue || !target || !bleedAuraId || !target->IsAlive())
            return;

        Aura* aura = target->GetAura(bleedAuraId, rogue->GetGUID());
        AuraEffect* effect = aura ? aura->GetEffect(EFFECT_0) : nullptr;
        int32 const baseAmplitude = aura ? aura->GetSpellInfo()->Effects[EFFECT_0].Amplitude : 0;
        uint32 const ticksLeft = effect ? GetRemainingTicks(aura, baseAmplitude) : 0;

        // Roll-over: what the running bleed still owes plus the new share, spread over a full duration.
        StoredBleedState* state = target->CustomData.GetDefault<StoredBleedState>(STORED_BLEED_STATE_KEY);
        uint32& perTick = state->perTick[{ rogue->GetGUID(), bleedAuraId }];
        perTick = uint32((uint64(perTick) * ticksLeft + totalDamage) / uint64(GetStoredBleedTicks(bleedAuraId)));

        if (!aura)
        {
            rogue->CastSpell(target, bleedAuraId, TRIGGERED_FULL_MASK);
            return;
        }

        // Full duration again, and the next tick one whole period away (the amplitude keeps Hunger for Blood's cut).
        aura->RefreshDuration();
        if (effect)
            effect->ResetPeriodic(true);
    }

    uint32 GetStoredBleedTick(Unit const* rogue, Unit const* target, uint32 bleedAuraId)
    {
        if (!rogue || !target)
            return 0;

        StoredBleedState const* state = target->CustomData.Get<StoredBleedState>(STORED_BLEED_STATE_KEY);
        if (!state)
            return 0;

        auto const itr = state->perTick.find({ rogue->GetGUID(), bleedAuraId });
        return itr != state->perTick.end() ? itr->second : 0;
    }

    float GetHealthClauseMultiplier(Unit const* attacker, Unit const* target, SpellInfo const* spellInfo)
    {
        // Runs for every direct hit and tick in the world: cheapest rejects first.
        if (!attacker || !target || !spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_ROGUE)
            return 1.0f;

        // S3: stored shares take no health clause (Akaari's echo, the Blade Flurry copy: their hit already had them).
        if (spellInfo->Id == RogueData::SPELL_BLADE_FLURRY_COPY ||
            spellInfo->Id == RogueData::SPELL_AKAARIS_ECHO_STRIKE)
            return 1.0f;

        Player const* rogue = attacker->ToPlayer();
        if (!rogue)
            return 1.0f;

        float mult = 1.0f;

        // S2 Executioner (35%, every rogue damage spell, poisons included; U35): live per hit and per tick. Akaari's
        // echo is a stored share of an Ambush that already had it; HasDamageEffect keeps heals (same hook) out.
        if (spellInfo->Id != RogueData::SPELL_AKAARIS_ECHO_STRIKE &&
            target->HealthBelowPct(RogueData::EXECUTIONER_HEALTH_PCT) && HasDamageEffect(spellInfo))
        {
            int32 const executionerPct = GetRankAmount(rogue, { RogueData::SPELL_EXECUTIONER,
                RogueData::SPELL_EXECUTIONER_204143 }, EFFECT_0);
            if (executionerPct > 0)
                mult *= 1.0f + executionerPct / 100.0f;
        }

        // S1 Zoldyck Recipe (30%, poisons and bleeds): unchanged; both clauses multiply.
        if (target->HealthBelowPct(RogueData::ZOLDYCK_HEALTH_PCT) &&
            (IsRoguePoisonDamage(spellInfo) || IsRogueBleed(spellInfo)))
        {
            int32 const zoldyckPct = GetRankAmount(rogue, { RogueData::SPELL_ZOLDYCK_RECIPE,
                RogueData::SPELL_ZOLDYCK_RECIPE_203812, RogueData::SPELL_ZOLDYCK_RECIPE_203813 }, EFFECT_0);
            if (zoldyckPct > 0)
                mult *= 1.0f + zoldyckPct / 100.0f;
        }

        // S3 Prey on the Weak (35%, every rogue damage, poisons and ticks included; U60): the three clauses multiply.
        if (target->HealthBelowPct(RogueData::PREY_DAMAGE_HEALTH_PCT) && HasDamageEffect(spellInfo))
        {
            int32 const preyPct = GetRankAmount(rogue, { RogueData::SPELL_PREY_ON_THE_WEAK,
                RogueData::SPELL_PREY_ON_THE_WEAK_51686, RogueData::SPELL_PREY_ON_THE_WEAK_51687 }, EFFECT_0);
            if (preyPct > 0)
                mult *= 1.0f + preyPct / 100.0f;
        }

        return mult;
    }

    void AddKingsbaneStacks(Player* rogue, Unit* target, uint8 count)
    {
        if (!rogue || !target || !count)
            return;

        Aura* aura = target->GetAura(RogueData::SPELL_KINGSBANE_DOT, rogue->GetGUID());
        AuraEffect* dot = aura ? aura->GetEffect(EFFECT_0) : nullptr;
        if (!dot)
            return;

        uint8 const oldStacks = aura->GetCharges();
        uint8 const newStacks = uint8(std::min<int32>(oldStacks + count, RogueData::KINGSBANE_MAX_STACKS));
        if (newStacks == oldStacks)
            return;

        // The DoT script stores the first-calc amount and never recalculates (canBeRecalculated = false), so the
        // live amount is always round(base x (1 + pct x stacks)): dividing it back recovers base exactly (the
        // rounding error is under half a point), with no state of our own to keep in step.
        float const pct = RogueData::KINGSBANE_STACK_PCT / 100.0f;
        float const base = std::round(float(dot->GetAmount()) / (1.0f + pct * oldStacks));

        aura->SetCharges(newStacks);
        dot->ChangeAmount(int32(std::lround(base * (1.0f + pct * newStacks))));
    }

    void OnRogueDamageCrit(Player* rogue, SpellInfo const* spellInfo, bool /*periodic*/)
    {
        // Dashing Scoundrel: direct hits and ticks alike (Deadly Poison's included), 1 energy per second at most.
        if (!rogue || !IsRoguePoisonDamage(spellInfo) || !rogue->HasAura(RogueData::SPELL_ENVENOM))
            return;

        if (!rogue->HasAura(RogueData::SPELL_DASHING_SCOUNDREL) &&
            !rogue->HasAura(RogueData::SPELL_DASHING_SCOUNDREL_203821))
            return;

        if (!TalentCooldownReady(rogue, RogueData::SPELL_DASHING_SCOUNDREL))
            return;

        StartTalentCooldown(rogue, RogueData::SPELL_DASHING_SCOUNDREL, RogueData::DASHING_SCOUNDREL_ICD_MS);
        rogue->CastSpell(rogue, RogueData::SPELL_DASHING_SCOUNDREL_ENERGIZE, TRIGGERED_FULL_MASK);
    }

    void SetHungerForBlood(Player* rogue)
    {
        if (!rogue)
            return;

        // 51662's own ACTIVATION_TIME mask decides which DoTs speed up (Doomblade's PERIODIC_DUMMY included); an
        // empty mask would match nothing rather than everything.
        SpellInfo const* hungerInfo = sSpellMgr->GetSpellInfo(RogueData::SPELL_HUNGER_FOR_BLOOD);
        if (!hungerInfo)
            return;

        flag96 const mask = hungerInfo->Effects[EFFECT_0].SpellClassMask;
        if (!mask)
            return;

        // Every unit the rogue is engaged with (combat references) or on whose threat list it is: no range limit, so a
        // DoT on a mob that walked away is restored too (0-verify item 12).
        std::vector<Unit*> units;
        auto const addUnit = [&units](Unit* unit)
        {
            if (unit && unit->IsInWorld() && std::find(units.begin(), units.end(), unit) == units.end())
                units.push_back(unit);
        };

        for (auto const& [guid, ref] : rogue->GetCombatManager().GetPvECombatRefs())
            addUnit(ref->GetOther(rogue));
        for (auto const& [guid, ref] : rogue->GetCombatManager().GetPvPCombatRefs())
            addUnit(ref->GetOther(rogue));
        for (auto const& [guid, ref] : rogue->GetThreatMgr().GetThreatenedByMeList())
            addUnit(ref->GetOwner());

        // Re-read each matching DoT's amplitude with the mod on (apply) or gone (remove): create = false, load = false
        // zeroes the tick number and keeps a PERIODIC_DAMAGE timer (P0 check 8 / M2). Any other type (Doomblade's
        // PERIODIC_DUMMY) gets its timer reset to the new amplitude there, which can push the last tick past expiry:
        // keep its running timer, capped at the new amplitude, so no tick is lost.
        for (Unit* unit : units)
            for (AuraType const type : { SPELL_AURA_PERIODIC_DAMAGE, SPELL_AURA_PERIODIC_DUMMY })
                for (AuraEffect* dot : unit->GetAuraEffectsByType(type))
                {
                    SpellInfo const* dotInfo = dot->GetSpellInfo();
                    if (dot->GetCasterGUID() != rogue->GetGUID() || dotInfo->SpellFamilyName != SPELLFAMILY_ROGUE ||
                        !(dotInfo->SpellFamilyFlags & mask))
                        continue;

                    int32 const timer = dot->GetPeriodicTimer();
                    dot->CalculatePeriodic(rogue, false, false);
                    if (dot->GetAuraType() != SPELL_AURA_PERIODIC_DAMAGE)
                        dot->SetPeriodicTimer(std::min(timer, dot->GetAmplitude()));
                }
    }

    void UpdateOverkill(Player* rogue)
    {
        if (!rogue || !rogue->IsAlive())
            return;

        // True Stealth or Vanish's aura only (Shroud 203724 and S2's Shadowed are other ids).
        int32 const overkillPct = GetRankAmount(rogue, { RogueData::SPELL_OVERKILL, RogueData::SPELL_OVERKILL_203826 },
            EFFECT_0);
        Aura* buff = rogue->GetAura(RogueData::SPELL_OVERKILL_BUFF, rogue->GetGUID());
        if (overkillPct <= 0)
        {
            // The talent is gone (respec): drop a buff it left behind.
            if (buff)
                buff->Remove();

            return;
        }

        bool const stealthed = rogue->HasAura(RogueData::SPELL_STEALTH) ||
            rogue->HasAura(RogueData::SPELL_VANISH_11327);
        if (!stealthed)
        {
            // The 20 s tail starts once, when the last stealth aura leaves; a buff already counting down stays.
            if (buff && buff->IsPermanent())
            {
                buff->SetMaxDuration(RogueData::OVERKILL_TAIL_MS);
                buff->SetDuration(RogueData::OVERKILL_TAIL_MS);
            }

            return;
        }

        if (!buff)
        {
            rogue->CastCustomSpell(rogue, RogueData::SPELL_OVERKILL_BUFF, &overkillPct, nullptr, nullptr, true);
            buff = rogue->GetAura(RogueData::SPELL_OVERKILL_BUFF, rogue->GetGUID());
            if (!buff)
                return;
        }
        else if (AuraEffect* regen = buff->GetEffect(EFFECT_0))
        {
            if (regen->GetAmount() != overkillPct)
                regen->ChangeAmount(overkillPct);
        }

        // Infinite while stealthed (a tail from an earlier stealth becomes infinite again).
        if (!buff->IsPermanent())
        {
            buff->SetMaxDuration(-1);
            buff->SetDuration(-1);
        }
    }

    void OnBleedVictimDied(Unit* victim, Aura const* bleed)
    {
        if (!victim || !bleed)
            return;

        // Whoever killed it (no kill credit needed, doc Q17): the bleed's caster gets the buff.
        Player* rogue = ObjectAccessor::GetPlayer(*victim, bleed->GetCasterGUID());
        if (!rogue || !rogue->IsAlive())
            return;

        int32 const critPct = GetRankAmount(rogue, { RogueData::SPELL_REMORSELESS_ATTACKS,
            RogueData::SPELL_REMORSELESS_ATTACKS_14148 }, EFFECT_0);
        if (critPct <= 0)
            return;

        // One buff, refreshed by the next kill (no stacks); rank 2 also empowers poisons.
        rogue->CastCustomSpell(rogue, RogueData::SPELL_REMORSELESS_CRIT, &critPct, nullptr, nullptr, true);
        if (rogue->HasAura(RogueData::SPELL_REMORSELESS_ATTACKS_14148))
            rogue->CastSpell(rogue, RogueData::SPELL_REMORSELESS_POISON, TRIGGERED_FULL_MASK);
    }

    // ---- S2 ----
    // Subtlety (docs/reworks/rogue-subtlety-rework.md). Cross-spec rules (S2-HANDOFF section 7): S2 adds one
    // cooldown-reduction helper (ReduceCooldown; S3's Restless Blades reuses it) and one Hidden-state updater
    // (UpdateHiddenBuffs); Hidden = Stealth 1784 | Vanish's aura 11327 | Shadowed 51713 everywhere. S3 appends here.

    void ReduceCooldown(Player* rogue, uint32 spellId, uint32 ms)
    {
        if (!rogue || !ms || !rogue->HasSpellCooldown(spellId))
            return;

        // Clear-then-set on the spell's own record (bug doc 1172). Shadow Dance is off the GCD, so a finisher's GCD
        // sweep is not touched (0-verify item 6); a reduction past the remainder ends the cooldown.
        rogue->ModifySpellCooldown(spellId, -int32(ms));
    }

    bool IsHidden(Unit const* unit)
    {
        return unit && (IsTrueStealthed(unit) || unit->HasAura(RogueData::SPELL_SHADOW_DANCE));
    }

    int32 GetMasterOfSubtletyPct(Player const* rogue)
    {
        if (!rogue)
            return 0;

        int32 pct = GetRankAmount(rogue, { RogueData::SPELL_MASTER_OF_SUBTLETY_204149,
            RogueData::SPELL_MASTER_OF_SUBTLETY_204150, RogueData::SPELL_MASTER_OF_SUBTLETY_204151 }, EFFECT_0);
        if (pct <= 0)
            return 0;

        // Capstone: Mastery is added 1:1 into the bonus (not a separate multiplier).
        if (rogue->HasAura(RogueData::SPELL_MASTER_OF_SUBTLETY_204151))
            pct += int32(std::lround(rogue->GetMasteryPercentage()));

        return std::max<int32>(pct, 0);
    }

    void UpdateHiddenBuffs(Player* rogue)
    {
        if (!rogue)
            return;

        // The tail clock: a true-Stealth exit (Stealth or Vanish gone, whatever else is up) starts Master of
        // Subtlety's tail. Idempotent: the hooks run twice per sweep, the second call sees no change.
        HiddenState* state = rogue->CustomData.GetDefault<HiddenState>(HIDDEN_STATE_KEY);
        bool const trueStealthed = IsTrueStealthed(rogue);
        if (state->trueStealthed && !trueStealthed)
            state->masterOfSubtletyTailEndMs = NowMs() + RogueData::MASTER_OF_SUBTLETY_TAIL_MS;

        state->trueStealthed = trueStealthed;

        Aura* subtlety = rogue->GetAura(RogueData::SPELL_MASTER_OF_SUBTLETY_BUFF, rogue->GetGUID());
        Aura* mark = rogue->GetAura(RogueData::SPELL_MARK_OF_THE_MASTER_ASSASSIN_BUFF, rogue->GetGUID());

        // R16: a dead rogue keeps neither buff (also the login call for a buff saved while Hidden).
        if (!rogue->IsAlive())
        {
            if (subtlety)
                subtlety->Remove();

            if (mark)
                mark->Remove();

            return;
        }

        bool const hidden = trueStealthed || rogue->HasAura(RogueData::SPELL_SHADOW_DANCE);

        // Master of Subtlety: infinite while Hidden (the AuraScript computes and polls the amount); out of Hidden the
        // infinite buff runs out at the tail's end (8 s after the last true-Stealth exit) or goes at once (a Shadowed
        // end with no tail left). A buff already counting down is left alone.
        if (GetMasterOfSubtletyPct(rogue) <= 0)
        {
            if (subtlety)
                subtlety->Remove();
        }
        else if (hidden)
        {
            if (!subtlety)
                rogue->CastSpell(rogue, RogueData::SPELL_MASTER_OF_SUBTLETY_BUFF, TRIGGERED_FULL_MASK);
            else
                MakeAuraInfinite(subtlety);
        }
        else if (subtlety && subtlety->IsPermanent())
        {
            int64 const remainingMs = state->masterOfSubtletyTailEndMs - NowMs();
            if (remainingMs > 0)
                SetAuraTail(subtlety, int32(remainingMs));
            else
                subtlety->Remove();
        }

        // Mark of the Master Assassin: true Stealth only, infinite with bp = the rank; a 3 s tail on exit.
        int32 const markPct = GetRankAmount(rogue, { RogueData::SPELL_MARK_OF_THE_MASTER_ASSASSIN,
            RogueData::SPELL_MARK_OF_THE_MASTER_ASSASSIN_204147 }, EFFECT_0);
        if (markPct <= 0)
        {
            if (mark)
                mark->Remove();
        }
        else if (trueStealthed)
        {
            if (!mark)
                rogue->CastCustomSpell(rogue, RogueData::SPELL_MARK_OF_THE_MASTER_ASSASSIN_BUFF, &markPct, nullptr,
                    nullptr, true);
            else
            {
                if (AuraEffect* crit = mark->GetEffect(EFFECT_0))
                    if (crit->GetAmount() != markPct)
                        crit->ChangeAmount(markPct);

                MakeAuraInfinite(mark);
            }
        }
        else if (mark && mark->IsPermanent())
            SetAuraTail(mark, RogueData::MOMA_TAIL_MS);
    }

    void OnShadowedApplied(Player* rogue)
    {
        // Lingering Shadow: a new Shadow Dance replaces an unspent buff (idempotent: the hook also fires on a refresh).
        if (rogue)
            rogue->RemoveAurasDueToSpell(RogueData::SPELL_LINGERING_SHADOW_BUFF);
    }

    void OnShadowedRemoved(Player* rogue, AuraRemoveMode mode)
    {
        // R16: not on death, nor on a logout (auras go with mode DEFAULT while the player is still in the world).
        if (!rogue || mode == AURA_REMOVE_BY_DEATH || !rogue->IsInWorld() || !rogue->IsAlive() ||
            (rogue->GetSession() && rogue->GetSession()->PlayerLogout()))
            return;

        int32 const stacks = GetRankAmount(rogue, { RogueData::SPELL_LINGERING_SHADOW,
            RogueData::SPELL_LINGERING_SHADOW_204139 }, EFFECT_0);
        if (stacks <= 0)
            return;

        rogue->CastSpell(rogue, RogueData::SPELL_LINGERING_SHADOW_BUFF, TRIGGERED_FULL_MASK);
        if (Aura* buff = rogue->GetAura(RogueData::SPELL_LINGERING_SHADOW_BUFF, rogue->GetGUID()))
            buff->SetStackAmount(uint8(std::min<int32>(stacks, 255)));
    }

    void OnBackstabHit(Player* rogue, Unit* target)
    {
        if (!rogue)
            return;

        // Slaughter from the Shadows: rank % (Proc Chance) to take 0.5 s off Shadow Dance.
        int32 const slaughterPct = GetRankAmount(rogue, { RogueData::SPELL_SLAUGHTER_FROM_THE_SHADOWS,
            RogueData::SPELL_SLAUGHTER_FROM_THE_SHADOWS_51709, RogueData::SPELL_SLAUGHTER_FROM_THE_SHADOWS_51710 },
            EFFECT_1);
        if (slaughterPct > 0 && RollProcChance(rogue, float(slaughterPct)))
            ReduceCooldown(rogue, RogueData::SPELL_SHADOW_DANCE,
                uint32(std::max<int32>(RogueData::SLAUGHTER_CDR_MS, 0)));

        // Lingering Shadow: one extra point per Backstab while a stack is left (always; no Proc Chance).
        if (Aura* lingering = rogue->GetAura(RogueData::SPELL_LINGERING_SHADOW_BUFF, rogue->GetGUID()))
        {
            GainComboPoints(rogue, target, 1);
            lingering->ModStackAmount(-1);
        }
    }

    void OnAmbushHit(Player* rogue, Unit* target, uint32 damage)
    {
        if (!rogue || !target || !damage)
            return;

        int32 const echoPct = GetRankAmount(rogue, { RogueData::SPELL_AKAARIS_ECHO,
            RogueData::SPELL_AKAARIS_ECHO_204145 }, EFFECT_0);
        if (echoPct <= 0 || !RollProcChance(rogue, float(echoPct)))
            return;

        uint32 const sharePct = uint32(std::max<int32>(RogueData::AKAARI_ECHO_SHARE_PCT, 0));
        uint32 const share = uint32(uint64(damage) * sharePct / 100);
        if (share)
            ScheduleAkaariEcho(rogue, target, share);
    }

    void ScheduleAkaariEcho(Player* rogue, Unit* target, uint32 damage)
    {
        if (!rogue || !target || !damage)
            return;

        ObjectGuid const rogueGuid = rogue->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();
        uint32 const mapId = rogue->GetMapId();
        uint32 const instanceId = rogue->GetInstanceId();
        int32 const echoDamage = int32(std::min<uint32>(damage, uint32(std::numeric_limits<int32>::max())));
        rogue->m_Events.AddEventAtOffset([rogueGuid, targetGuid, mapId, instanceId, echoDamage]()
        {
            Player* player = ObjectAccessor::FindPlayer(rogueGuid);
            if (!player || !player->IsInWorld() || !player->IsAlive() || player->GetMapId() != mapId ||
                player->GetInstanceId() != instanceId)
                return;

            Unit* victim = ObjectAccessor::GetUnit(*player, targetGuid);
            if (!victim || !victim->IsAlive())
                return;

            // The strike first: its own melee range check is "lost out of range" (0-verify item 12), and a lost echo
            // shows no clone either.
            if (player->CastCustomSpell(victim, RogueData::SPELL_AKAARIS_ECHO_STRIKE, &echoDamage, nullptr, nullptr,
                true) != SPELL_CAST_OK)
                return;

            // The clone (P0 shape): behind the target, the rogue's look and weapons, the shadow tint, one swing.
            float const angle = victim->GetOrientation() + float(M_PI);
            float const x = victim->GetPositionX() + RogueData::AKAARI_CLONE_BEHIND_YD * std::cos(angle);
            float const y = victim->GetPositionY() + RogueData::AKAARI_CLONE_BEHIND_YD * std::sin(angle);
            float z = victim->GetPositionZ();
            victim->UpdateAllowedPositionZ(x, y, z);

            TempSummon* clone = player->SummonCreature(RogueData::NPC_AKAARI_CLONE, x, y, z, victim->GetOrientation(),
                TEMPSUMMON_TIMED_DESPAWN, uint32(std::max<int32>(RogueData::AKAARI_CLONE_DESPAWN_MS, 1)));
            if (!clone)
                return;

            clone->SetFaction(player->GetFaction());
            clone->SetReactState(REACT_PASSIVE);
            clone->SetFacingToObject(victim);
            player->CastSpell(clone, CLONE_ME_SPELL_ID, true);
            player->AddAura(COPY_WEAPON_SPELL_ID, clone);
            player->AddAura(COPY_OFF_HAND_SPELL_ID, clone);
            clone->SetSheath(SHEATH_STATE_MELEE);
            player->AddAura(RogueData::SPELL_AKAARIS_ECHO_TINT, clone);

            // The clone's own event list dies with the clone, so capturing it is safe (Mirror Image precedent).
            clone->m_Events.AddEventAtOffset([clone]()
            {
                clone->HandleEmoteCommand(EMOTE_ONESHOT_ATTACK1H);
            }, Milliseconds(RogueData::AKAARI_CLONE_SWING_DELAY_MS));
        }, Milliseconds(RogueData::AKAARI_ECHO_DELAY_MS));
    }

    void OnEviscerateHit(Player* rogue, Unit* target, uint32 damage, uint32 /*spellId*/)
    {
        if (!rogue)
            return;

        // Hemorrhage: a stored bleed of 30% of the hit (ApplyStoredBleed guards a dead target).
        if (target && damage && rogue->HasAura(RogueData::SPELL_HEMORRHAGE_204152))
        {
            int32 const sharePct = GetRankAmount(rogue, { RogueData::SPELL_HEMORRHAGE_204152 }, EFFECT_0);
            uint32 const share = sharePct > 0 ? uint32(uint64(damage) * uint32(sharePct) / 100) : 0;
            if (share)
                ApplyStoredBleed(rogue, target, RogueData::SPELL_HEMORRHAGE_BLEED, share);
        }

        // Eviscerate and Death from Above's landing share Finality's Eviscerate key.
        ResolveFinality(rogue, RogueData::SPELL_EVISCERATE);
    }

    void ResolveFinality(Player* rogue, uint32 finisherSpellId)
    {
        if (!rogue)
            return;

        int32 const rank = GetRankAmount(rogue, { RogueData::SPELL_FINALITY, RogueData::SPELL_FINALITY_204141 },
            EFFECT_0);
        if (rank <= 0)
            return;

        uint32 const key = GetFinalityKey(finisherSpellId);
        uint32 const buffId = GetFinalityBuff(key);
        FinalityState* state = rogue->CustomData.Get<FinalityState>(FINALITY_STATE_KEY);
        if (!buffId || !state)
            return;

        // No stamp: this cast was not seen by the dispatcher or is already resolved.
        auto const itr = state->heldAtCast.find(key);
        if (itr == state->heldAtCast.end())
            return;

        bool const heldAtCast = itr->second;
        state->heldAtCast.erase(itr);

        // Held at cast: this finisher used it. Not held: it grants the empowerment for the next one.
        if (heldAtCast)
            rogue->RemoveAurasDueToSpell(buffId);
        else
            rogue->CastCustomSpell(rogue, buffId, &rank, nullptr, nullptr, true);
    }

    void OnFinisherCrit(Player* rogue, Unit* target, SpellInfo const* spellInfo)
    {
        if (!rogue || !target || !spellInfo || !rogue->HasAura(RogueData::SPELL_HONOR_AMONG_THIEVES_51701))
            return;

        HonorAmongThievesState* state =
            rogue->CustomData.Get<HonorAmongThievesState>(HONOR_AMONG_THIEVES_STATE_KEY);
        if (!state || state->triggered)
            return;

        // The stamped cast's first crit: Eviscerate on its target, Deadly Throw's primary only (not the Throwing
        // Specialization copies, other ids anyway), either of Death from Above's hits.
        bool matches = false;
        switch (spellInfo->Id)
        {
            case RogueData::SPELL_EVISCERATE:
            case RogueData::SPELL_DEADLY_THROW:
            case RogueData::SPELL_BETWEEN_THE_EYES:
                matches = state->castSpellId == spellInfo->Id && state->primary == target->GetGUID();
                break;
            case RogueData::SPELL_DEATH_FROM_ABOVE_AREA:
            case RogueData::SPELL_DEATH_FROM_ABOVE_LANDING:
                matches = state->castSpellId == RogueData::SPELL_DEATH_FROM_ABOVE;
                break;
            default:
                break;
        }

        if (!matches)
            return;

        state->triggered = true;

        // A crit while the buff is up refreshes it on the same ally if that ally is still in reach; else a new pick.
        Player* ally = nullptr;
        if (!state->ally.IsEmpty() && rogue->HasAura(RogueData::SPELL_HONOR_AMONG_THIEVES_BUFF))
        {
            Player* stored = ObjectAccessor::GetPlayer(*rogue, state->ally);
            if (IsHonorAmongThievesAllyInReach(rogue, stored))
                ally = stored;
        }

        if (!ally)
            ally = SelectHonorAmongThievesAlly(rogue);

        state->ally = ally ? ally->GetGUID() : ObjectGuid::Empty;

        // AddAura: no range, facing or target-type checks (R11); another rogue's copy is replaced (R9).
        rogue->AddAura(RogueData::SPELL_HONOR_AMONG_THIEVES_BUFF, rogue);
        if (ally)
            rogue->AddAura(RogueData::SPELL_HONOR_AMONG_THIEVES_BUFF, ally);
    }

    void LaunchDeathFromAbove(Player* rogue, Unit* target, int32 landingBase)
    {
        if (!rogue || !target)
            return;

        // Root immunity, safe fall and pacify for the leap (the 2.5 s aura; removed at the landing, or kept while the
        // rogue falls after a skipped slow fall or dive).
        rogue->AddAura(RogueData::SPELL_DEATH_FROM_ABOVE_FLIGHT, rogue);

        // Leg 1 (R8): rise to an apex DFA_RISE_FRACTION of the way to the landing point, DFA_APEX_HEIGHT_YD above the
        // higher end. No gravity disable, no hover: the hang is the slow-fall leg (leg 2), then the dive (leg 3).
        Position const start = rogue->GetPosition();
        float landingX = 0.0f;
        float landingY = 0.0f;
        float landingZ = 0.0f;
        bool const landingReachable = GetDeathFromAboveLanding(rogue, start, target, landingX, landingY, landingZ);
        Position const landing(landingX, landingY, landingZ);

        float const fraction = std::clamp(float(RogueData::DFA_RISE_FRACTION), 0.0f, 1.0f);
        float apexX = start.GetPositionX() + (landingX - start.GetPositionX()) * fraction;
        float apexY = start.GetPositionY() + (landingY - start.GetPositionY()) * fraction;
        float apexZ = std::max(start.GetPositionZ(), landingZ) + RogueData::DFA_APEX_HEIGHT_YD;

        // The jump spline ignores collision: cap the rise under a ceiling or overhang (S2-CODE-REVIEW M1). Ray the
        // rogue's head from the start up to the wanted apex against static and dynamic models; on a hit, the apex is
        // the hit point lowered by the rogue's height, never below the start.
        float const height = rogue->GetCollisionHeight();
        float const fromZ = start.GetPositionZ() + height * 0.5f;
        float hitX = apexX;
        float hitY = apexY;
        float hitZ = apexZ + height;
        MapCollisionData const& collision = rogue->GetMap()->GetMapCollisionData();
        bool const hitStatic = collision.GetStaticTree().GetObjectHitPos(start.GetPositionX(), start.GetPositionY(),
            fromZ, hitX, hitY, hitZ, hitX, hitY, hitZ, -DFA_CEILING_MARGIN_YD);
        bool const hitDynamic = collision.GetDynamicTree().GetObjectHitPos(rogue->GetPhaseMask(),
            start.GetPositionX(), start.GetPositionY(), fromZ, hitX, hitY, hitZ, hitX, hitY, hitZ,
            -DFA_CEILING_MARGIN_YD);
        if (hitStatic || hitDynamic)
        {
            apexX = hitX;
            apexY = hitY;
            apexZ = std::max(start.GetPositionZ(), hitZ - height);
        }

        Position const apex(apexX, apexY, apexZ);

        int32 const riseMs = StartDeathFromAboveLeg(rogue, apex.GetPositionX(), apex.GetPositionY(),
            apex.GetPositionZ(), RogueData::DFA_RISE_MS, DFA_RISE_SPEED_Z, target);

        // Leg 2 (slow fall) at leg 1's measured end, leg 3 (dive) at leg 2's, the landing at leg 3's (every event
        // re-resolves by guid).
        ObjectGuid const rogueGuid = rogue->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();
        uint32 const mapId = rogue->GetMapId();
        uint32 const instanceId = rogue->GetInstanceId();
        rogue->m_Events.AddEventAtOffset([rogueGuid, targetGuid, mapId, instanceId, apex, landing, landingReachable,
            landingBase]()
        {
            DriftDeathFromAbove(rogueGuid, targetGuid, mapId, instanceId, apex, landing, landingReachable, landingBase);
        }, Milliseconds(riseMs));
    }

    // ---- S3 ----
    // Combat (docs/reworks/rogue-combat-rework.md; S3a WP-BRIEF). Cross-spec rules (S3-HANDOFF section 7): S3 adds one
    // Anticipation bank / release (inside the combo-point helper's path: GainComboPoints, the builder stamp, the Fan of
    // Knives award; released after any spent finisher) and one Blade Flurry copier; every roll goes through
    // RollProcChance, every point through GainComboPoints, every cooldown cut through ReduceCooldown. Health clauses:
    // Zoldyck, Executioner and Prey multiply; stored shares take none. State on CustomData, nothing file-static.

    void BankAnticipation(Player* rogue, int8 overflow)
    {
        if (!rogue || overflow <= 0 || !rogue->IsAlive() || !rogue->HasAura(RogueData::SPELL_RESTLESS_BLADES))
            return;

        // Up to ANTICIPATION_MAX_STACKS stored points; past that they are lost, but every gain refreshes the duration.
        int32 const maxStacks = std::max<int32>(RogueData::ANTICIPATION_MAX_STACKS, 1);
        Aura* stored = rogue->GetAura(RogueData::SPELL_ANTICIPATION, rogue->GetGUID());
        int32 const wanted = std::min<int32>((stored ? stored->GetStackAmount() : 0) + overflow, maxStacks);
        if (!stored)
        {
            rogue->CastSpell(rogue, RogueData::SPELL_ANTICIPATION, TRIGGERED_FULL_MASK);
            stored = rogue->GetAura(RogueData::SPELL_ANTICIPATION, rogue->GetGUID());
            if (!stored)
                return;
        }

        // ModStackAmount refreshes the timer on a gain; at the cap only the duration is refreshed.
        int32 const delta = wanted - int32(stored->GetStackAmount());
        if (delta > 0)
            stored->ModStackAmount(delta);
        else
            stored->RefreshDuration();
    }

    void ReleaseAnticipation(Player* rogue, Unit* target)
    {
        if (!rogue || !rogue->IsAlive())
            return;

        Aura* stored = rogue->GetAura(RogueData::SPELL_ANTICIPATION, rogue->GetGUID());
        if (!stored)
            return;

        // Removed first, so a release past 5 points (Ruthlessness's point already in) banks its own overflow again.
        int8 const stacks = int8(std::min<int32>(stored->GetStackAmount(), MAX_COMBO_POINTS));
        stored->Remove();
        GainComboPoints(rogue, target, stacks);
    }

    void OnBuilderCast(Player* rogue, Spell const* spell)
    {
        if (!rogue || !spell)
            return;

        SpellInfo const* spellInfo = spell->GetSpellInfo();
        if (!spellInfo)
            return;

        // U54 (b): stamp first, so the scripted grants below (Adrenaline Rush's point) move its base (R3).
        StampBuilder(rogue, spellInfo);

        Unit* target = spell->m_targets.GetUnitTarget();
        uint32 const firstRankId = spellInfo->GetFirstRankSpell()->Id;

        // Adrenaline Rush (13750 or Celerity's 203996): +1 point once per builder cast, at cast (R18: a dodged builder
        // keeps it). Fan of Knives takes the dispatcher's stamp case instead.
        switch (firstRankId)
        {
            case RogueData::SPELL_SINISTER_STRIKE:
            case RogueData::SPELL_PISTOL_SHOT:
            case RogueData::SPELL_GHOSTLY_STRIKE:
            case RogueData::SPELL_RIPOSTE:
            case RogueData::SPELL_BACKSTAB:
            case RogueData::SPELL_AMBUSH:
            case FAN_OF_KNIVES_SPELL_ID:
                if (HasAdrenalineRush(rogue))
                    GainComboPoints(rogue, target, int8(RogueData::ADRENALINE_RUSH_EXTRA_POINTS));
                break;
            default:
                break;
        }

        // Celerity (U74): Sinister Strike and Pistol Shot, once per cast (the second strike and the extra shots are
        // triggered and never reach the dispatcher).
        if (firstRankId == RogueData::SPELL_SINISTER_STRIKE || firstRankId == RogueData::SPELL_PISTOL_SHOT)
        {
            int32 const celerityPct = GetRankAmount(rogue, { RogueData::SPELL_CELERITY,
                RogueData::SPELL_CELERITY_203978 }, EFFECT_0);
            if (celerityPct > 0 && RollProcChance(rogue, float(celerityPct)))
                ApplyCelerity(rogue);
        }
    }

    void OnCombatStrikeHit(Player* rogue, Unit* target, SpellInfo const* spellInfo, uint32 /*damage*/)
    {
        if (!rogue || !target || !spellInfo)
            return;

        // U54 (b): a damage hit of the stamped builder (or of its dual-strike hands) landed: at 5 points nothing rises,
        // so this flag is what tells the stamp's event the gain was granted.
        if (BuilderStamp* stamp = rogue->CustomData.Get<BuilderStamp>(BUILDER_STAMP_KEY))
            if (stamp->live && (stamp->spellId == spellInfo->Id || GetStrikeParent(spellInfo->Id) == stamp->spellId))
                stamp->landed = true;

        // Blade Twisting: the five named casts' own ids only (copies, the second strike and the extra shots carry
        // other ids). One stack per hit, each refreshing 12 s; bp = the rank (re-set on every application).
        switch (spellInfo->GetFirstRankSpell()->Id)
        {
            case RogueData::SPELL_SINISTER_STRIKE:
            case RogueData::SPELL_PISTOL_SHOT:
            case RogueData::SPELL_GHOSTLY_STRIKE:
            case RogueData::SPELL_RIPOSTE:
            case RogueData::SPELL_BACKSTAB:
                break;
            default:
                return;
        }

        int32 const twistPct = GetRankAmount(rogue, { RogueData::SPELL_BLADE_TWISTING,
            RogueData::SPELL_BLADE_TWISTING_31126 }, EFFECT_0);
        if (twistPct > 0 && target->IsAlive())
            rogue->CastCustomSpell(target, RogueData::SPELL_BLADE_TWISTING_DEBUFF, &twistPct, nullptr, nullptr, true);
    }

    void ApplyCombatSpentClauses(Player* rogue, Unit* /*target*/, uint32 finisherSpellId, uint8 comboPoints)
    {
        if (!rogue || !comboPoints || !rogue->IsAlive())
            return;

        // R4: the points were spent; the release event (after Ruthlessness's point) reads this.
        rogue->CustomData.GetDefault<AnticipationRelease>(ANTICIPATION_RELEASE_KEY)->pending = true;

        // Restless Blades: rank ms per spent point off the running cooldowns (Killing Spree's own points skip itself),
        // Evasion and Cloak of Shadows only in Enforcer Stance.
        int32 const msPerPoint = GetRankAmount(rogue, { RogueData::SPELL_RESTLESS_BLADES }, EFFECT_0);
        if (msPerPoint > 0)
        {
            uint32 const ms = uint32(msPerPoint) * comboPoints;
            for (uint32 const spellId : { RogueData::SPELL_ADRENALINE_RUSH, RogueData::SPELL_BLADE_FLURRY,
                RogueData::SPELL_BLADE_RUSH, RogueData::SPELL_GRAPPLING_HOOK, RogueData::SPELL_SPRINT })
                ReduceCooldown(rogue, spellId, ms);

            if (finisherSpellId != RogueData::SPELL_KILLING_SPREE)
                ReduceCooldown(rogue, RogueData::SPELL_KILLING_SPREE, ms);

            if (rogue->HasAura(RogueData::SPELL_ENFORCER_STANCE))
            {
                ReduceCooldown(rogue, RogueData::SPELL_EVASION, ms);
                ReduceCooldown(rogue, RogueData::SPELL_CLOAK_OF_SHADOWS, ms);
            }
        }

        // Hair Trigger (Between the Eyes only; Combat's one finisher proc): rank % per spent point, one roll.
        if (finisherSpellId == RogueData::SPELL_BETWEEN_THE_EYES)
        {
            int32 const triggerPct = GetRankAmount(rogue, { RogueData::SPELL_HAIR_TRIGGER,
                RogueData::SPELL_HAIR_TRIGGER_203976 }, EFFECT_0);
            if (triggerPct > 0 && RollProcChance(rogue, float(triggerPct * comboPoints)))
                rogue->CastSpell(rogue, RogueData::SPELL_HAIR_TRIGGER_BUFF, TRIGGERED_FULL_MASK);
        }
    }

    void GrantOpportunity(Player* rogue)
    {
        // A cast onto the running buff adds a stack (capped by its StackAmount) and refreshes it; the companion
        // follows by its type-2 link.
        if (rogue && rogue->IsAlive())
            rogue->CastSpell(rogue, RogueData::SPELL_OPPORTUNITY_BUFF, TRIGGERED_FULL_MASK);
    }

    void OnPistolShotHit(Player* rogue, Unit* target, bool empowered)
    {
        if (!rogue)
            return;

        // An empowered shot (it spent Opportunity): Primed Powder +1 stack (refresh), Quick Draw's extra point.
        if (empowered)
        {
            rogue->CastSpell(rogue, RogueData::SPELL_PRIMED_POWDER, TRIGGERED_FULL_MASK);

            int32 const extraPoints = GetRankAmount(rogue, { RogueData::SPELL_QUICK_DRAW }, EFFECT_0);
            if (extraPoints > 0)
                GainComboPoints(rogue, target, int8(extraPoints));
        }

        // Surprise Attacks' capstone: consumed by any Pistol Shot; the extra shots carry this shot's Opportunity.
        if (!target || !rogue->HasAura(RogueData::SPELL_SURPRISE_ATTACKS_BUFF))
            return;

        rogue->RemoveAurasDueToSpell(RogueData::SPELL_SURPRISE_ATTACKS_BUFF);
        rogue->CustomData.GetDefault<SurpriseShotStamp>(SURPRISE_SHOT_STAMP_KEY)->empowered = empowered;

        ObjectGuid const targetGuid = target->GetGUID();
        int32 const delayMs = std::max<int32>(RogueData::SURPRISE_SHOT_DELAY_MS, 1);
        for (int32 shot = 1; shot <= RogueData::SURPRISE_ATTACKS_EXTRA_SHOTS; ++shot)
            rogue->m_Events.AddEventAtOffset([rogue, targetGuid]()
            {
                if (!rogue->IsAlive())
                    return;

                Unit* victim = ObjectAccessor::GetUnit(*rogue, targetGuid);
                if (victim && victim->IsAlive() && victim->IsInMap(rogue))
                    rogue->CastSpell(victim, RogueData::SPELL_PISTOL_SHOT_EXTRA, TRIGGERED_FULL_MASK);
            }, Milliseconds(delayMs * shot));
    }

    bool IsSurpriseShotEmpowered(Player const* rogue)
    {
        if (!rogue)
            return false;

        SurpriseShotStamp const* stamp = rogue->CustomData.Get<SurpriseShotStamp>(SURPRISE_SHOT_STAMP_KEY);
        return stamp && stamp->empowered;
    }

    void OnSinisterStrikeHit(Player* rogue, Unit* target)
    {
        if (!rogue)
            return;

        // Between the Eyes' marker: rank % (Proc Chance) to strike again for 1 more point and Opportunity.
        int32 const secondPct = GetRankAmount(rogue, { RogueData::SPELL_BETWEEN_THE_EYES_MARKER }, EFFECT_0);
        if (secondPct <= 0 || !RollProcChance(rogue, float(secondPct)))
            return;

        if (target && target->IsAlive())
            rogue->CastSpell(target, RogueData::SPELL_SINISTER_STRIKE_SECOND_STRIKE, TRIGGERED_FULL_MASK);

        GainComboPoints(rogue, target, 1);
        GrantOpportunity(rogue);

        // Surprise Attacks' capstone rolls when the second strike fires.
        int32 const surprisePct = GetRankAmount(rogue, { RogueData::SPELL_SURPRISE_ATTACKS_203982 }, EFFECT_1);
        if (surprisePct > 0 && RollProcChance(rogue, float(surprisePct)))
            rogue->CastSpell(rogue, RogueData::SPELL_SURPRISE_ATTACKS_BUFF, TRIGGERED_FULL_MASK);
    }

    void OnEviscerateCombatHit(Player* rogue)
    {
        if (!rogue)
            return;

        // R21: Eviscerate grants Opportunity only with the Between the Eyes talent (its marker).
        if (rogue->HasAura(RogueData::SPELL_BETWEEN_THE_EYES_MARKER))
            GrantOpportunity(rogue);

        ConsumeBladeRush(rogue);
    }

    void OnRiposteHit(Player* rogue, Unit* target)
    {
        if (!rogue)
            return;

        // R21: every Riposte hit grants Opportunity (tooltip literal).
        GrantOpportunity(rogue);

        // Improved Riposte's capstone: Riposte's damage on up to 2 more engaged enemies near the target.
        if (!target || !rogue->HasAura(RogueData::SPELL_IMPROVED_RIPOSTE_203968))
            return;

        for (Unit* unit : SelectEngagedUnits(rogue, target, RogueData::IMPROVED_RIPOSTE_RADIUS_YD, target,
            std::size_t(std::max<int32>(RogueData::IMPROVED_RIPOSTE_EXTRA_TARGETS, 0))))
            rogue->CastSpell(unit, RogueData::SPELL_IMPROVED_RIPOSTE_CLEAVE, TRIGGERED_FULL_MASK);
    }

    void OnBladeFlurryCast(Player* rogue)
    {
        if (!rogue || !rogue->IsAlive())
            return;

        // Deft Maneuvers (U72, R13): 3+ engaged enemies within range -> strike them all at the rank's weapon percent
        // and one grant of min(n, 5) points on the selection (the overflow goes to Anticipation).
        int32 const weaponPct = GetRankAmount(rogue, { RogueData::SPELL_DEFT_MANEUVERS,
            RogueData::SPELL_DEFT_MANEUVERS_203974 }, EFFECT_0);
        if (weaponPct <= 0)
            return;

        // S3a-REVIEW L4: only enemies the area strike can reach (it checks line of sight) count for the threshold and
        // the points.
        std::vector<Unit*> const engaged = SelectEngagedUnits(rogue, rogue, RogueData::DEFT_MANEUVERS_RADIUS_YD,
            nullptr, 0);
        std::size_t const enemies = std::size_t(std::count_if(engaged.begin(), engaged.end(), [rogue](Unit const* unit)
        {
            return rogue->IsWithinLOSInMap(unit);
        }));
        if (enemies < std::size_t(std::max<int32>(RogueData::DEFT_MANEUVERS_MIN_ENEMIES, 1)))
            return;

        rogue->CastCustomSpell(rogue, RogueData::SPELL_DEFT_MANEUVERS_STRIKE, &weaponPct, nullptr, nullptr, true);
        int32 const points = std::min<int32>(int32(enemies), RogueData::DEFT_MANEUVERS_MAX_POINTS);
        if (points > 0)
            GainComboPoints(rogue, nullptr, int8(points));
    }

    void OnBladeFlurryDamage(Player* rogue, Unit* target, uint32 damage, SpellInfo const* spellInfo)
    {
        // Every rogue hit and swing with Blade Flurry up lands here: cheapest rejects first, no allocation before them.
        if (!rogue || !target || !damage)
            return;

        if (spellInfo && (IsBladeFlurryExcluded(spellInfo->Id) || spellInfo->IsAffectingArea() ||
            IsRoguePoisonDamage(spellInfo)))
            return;

        if (!rogue->HasAura(RogueData::SPELL_BLADE_FLURRY))
            return;

        uint32 const pct = uint32(std::max<int32>(RogueData::BLADE_FLURRY_COPY_PCT, 0));
        int32 const copyDamage = int32(std::min<uint64>(uint64(damage) * pct / 100,
            uint64(std::numeric_limits<int32>::max())));
        if (copyDamage <= 0)
            return;

        for (Unit* unit : SelectEngagedUnits(rogue, target, RogueData::BLADE_FLURRY_RADIUS_YD, target,
            std::size_t(std::max<int32>(RogueData::BLADE_FLURRY_EXTRA_TARGETS, 0))))
            rogue->CastCustomSpell(unit, RogueData::SPELL_BLADE_FLURRY_COPY, &copyDamage, nullptr, nullptr, true);
    }

    void ApplyCelerity(Player* rogue)
    {
        if (!rogue || !rogue->IsAlive())
            return;

        // Adrenaline Rush running: its remaining time to at least CELERITY_DURATION_MS, never its cooldown. Else the
        // 4 s copy (group 1288 keeps the two exclusive), refreshed to at least that.
        int32 const minMs = std::max<int32>(RogueData::CELERITY_DURATION_MS, 1);
        Aura* rush = rogue->GetAura(RogueData::SPELL_ADRENALINE_RUSH);
        if (!rush)
            rush = rogue->GetAura(RogueData::SPELL_ADRENALINE_RUSH_CELERITY);

        if (!rush)
        {
            rogue->CastSpell(rogue, RogueData::SPELL_ADRENALINE_RUSH_CELERITY, TRIGGERED_FULL_MASK);
            return;
        }

        if (rush->IsPermanent() || rush->GetDuration() >= minMs)
            return;

        rush->SetMaxDuration(std::max(rush->GetMaxDuration(), minMs));
        rush->SetDuration(minMs);
    }

    void ConsumeBladeRush(Player* rogue)
    {
        if (rogue)
            rogue->RemoveAurasDueToSpell(RogueData::SPELL_BLADE_RUSH_BUFF);
    }

    void UpdatePreyCritDebuff(Player* rogue, Unit* target)
    {
        if (!rogue || !target)
            return;

        int32 const critPct = GetRankAmount(rogue, { RogueData::SPELL_PREY_ON_THE_WEAK,
            RogueData::SPELL_PREY_ON_THE_WEAK_51686, RogueData::SPELL_PREY_ON_THE_WEAK_51687 }, EFFECT_1);
        if (critPct <= 0 || !target->IsAlive() || !rogue->IsValidAttackTarget(target))
            return;

        // Per caster (the debuff stacks per rogue); bp = the crit rank, kept in step when the rank moved.
        Aura* debuff = target->GetAura(RogueData::SPELL_PREY_ON_THE_WEAK_CRIT, rogue->GetGUID());
        if (!target->HealthAbovePct(RogueData::PREY_CRIT_HEALTH_PCT))
        {
            if (debuff)
                debuff->Remove();

            return;
        }

        if (!debuff)
        {
            rogue->CastCustomSpell(target, RogueData::SPELL_PREY_ON_THE_WEAK_CRIT, &critPct, nullptr, nullptr, true);
            return;
        }

        if (AuraEffect* crit = debuff->GetEffect(EFFECT_0))
            if (crit->GetAmount() != critPct)
                crit->ChangeAmount(critPct);

        // S3a-REVIEW L3: the debuff has a finite duration, so each qualifying cast keeps it up on its target only.
        debuff->RefreshDuration();
    }

    float GetAutoAttackHealthMultiplier(Unit const* attacker, Unit const* target)
    {
        // Every melee damage slot of every player: the health test, then the one cached-rank lookup (L8), then the
        // rank's own aura effect.
        if (!attacker || !target || !target->HealthBelowPct(RogueData::PREY_DAMAGE_HEALTH_PCT))
            return 1.0f;

        Player const* rogue = attacker->ToPlayer();
        if (!rogue)
            return 1.0f;

        uint32 const rankId = GetCachedPreyRank(rogue);
        if (!rankId)
            return 1.0f;

        AuraEffect const* rank = rogue->GetAuraEffect(rankId, EFFECT_0, rogue->GetGUID());
        int32 const preyPct = rank ? rank->GetAmount() : 0;
        return preyPct > 0 ? 1.0f + preyPct / 100.0f : 1.0f;
    }

    void ModifyPreyAutoCrit(Unit const* attacker, Unit const* victim, int32& critChance)
    {
        // Every melee swing of every player: the one cached-rank lookup first (L8), then the victim's debuff and the
        // rank's own aura effect. A debuff left by a removed rank expires within its 5 s.
        if (!attacker || !victim)
            return;

        Player const* rogue = attacker->ToPlayer();
        if (!rogue)
            return;

        uint32 const rankId = GetCachedPreyRank(rogue);
        if (!rankId)
            return;

        // R11: net of this attacker's 204003 on the victim, which GetUnitCriticalChance already added (percent).
        bool const above = victim->HealthAbovePct(RogueData::PREY_CRIT_HEALTH_PCT);
        AuraEffect const* debuff = victim->GetAuraEffect(RogueData::SPELL_PREY_ON_THE_WEAK_CRIT, EFFECT_0,
            attacker->GetGUID());
        int32 const have = debuff ? debuff->GetAmount() : 0;
        if (!above && !have)
            return;

        AuraEffect const* rank = above ? rogue->GetAuraEffect(rankId, EFFECT_1, rogue->GetGUID()) : nullptr;
        int32 const want = rank ? rank->GetAmount() : 0;

        // critChance is in 1/100 % (Unit::RollMeleeOutcomeAgainst).
        critChance += (std::max<int32>(want, 0) - have) * 100;
    }

    bool RollHackAndSlash(Player* rogue, ProcEventInfo& eventInfo)
    {
        if (!rogue)
            return false;

        // PoisonRollAllowed rules 1-2: the rogue's own action on a valid, living, hostile target.
        Unit* actor = eventInfo.GetActor();
        Unit* target = eventInfo.GetActionTarget();
        if (actor != rogue || !target || target == actor || !target->IsAlive() || !actor->IsValidAttackTarget(target))
            return false;

        float chance = float(std::max<int32>(RogueData::HACK_AND_SLASH_CHANCE_PCT, 0));
        if (Spell const* spell = eventInfo.GetProcSpell())
        {
            SpellInfo const* spellInfo = spell->GetSpellInfo();
            if (!spellInfo)
                return false;

            // Rule 3a: no CC strike (Sap, Gouge, Blind) or weapon-proc suppressor; never a finisher (Q15).
            if (spellInfo->HasAttribute(SPELL_ATTR0_CANCELS_AUTO_ATTACK_COMBAT) ||
                spellInfo->HasAttribute(SPELL_ATTR4_SUPPRESS_WEAPON_PROCS) || spellInfo->NeedsComboPoints())
                return false;

            // Rule 3a': triggered hits roll nothing (its own strikes, copies, Deft's strike), except a dual strike's
            // hands, which roll as their parent's cast.
            if (spell->IsTriggered() && !IsDualStrikeHand(spellInfo->Id))
                return false;

            // Abilities: weapon strikes only. Pistol Shot (and its capstone extra shot) is a melee-class hit that
            // needs no weapon and lands at range: its strikes must not fire from 20 yd.
            if (spellInfo->Id == RogueData::SPELL_PISTOL_SHOT || spellInfo->Id == RogueData::SPELL_PISTOL_SHOT_EXTRA)
                return false;

            // Abilities: the main hand's weapon.
            if (!IsOneHandedWeaponIn(rogue, BASE_ATTACK))
                return false;

            // R22: once per cast (Fan of Knives' targets share the cast, Mutilate's hands their parent), not
            // PoisonRollAllowed's per-target guard. Stamped before the roll: the cast's one attempt.
            uint32 const parentId = GetStrikeParent(spellInfo->Id);
            uint32 const castKey = parentId ? parentId : spellInfo->Id;
            HackAndSlashGuard* guard = rogue->CustomData.GetDefault<HackAndSlashGuard>(HACK_AND_SLASH_GUARD_KEY);
            int64 const now = NowMs();
            if (guard->timeMs == now && guard->castKey == castKey)
                return false;

            guard->timeMs = now;
            guard->castKey = castKey;
        }
        else
        {
            // Melee auto attacks only; extra attacks roll nothing (rule 4).
            if (!(eventInfo.GetTypeMask() & PROC_FLAG_DONE_MELEE_AUTO_ATTACK) || rogue->GetLastExtraAttackSpell())
                return false;

            DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
            WeaponAttackType const attType = damageInfo ? damageInfo->GetAttackType() : BASE_ATTACK;
            if (attType == RANGED_ATTACK || !IsOneHandedWeaponIn(rogue, attType))
                return false;

            // The poisons' rule: the hitting hand's unhasted speed over the reference.
            int32 const referenceMs = std::max<int32>(RogueData::POISON_REFERENCE_WEAPON_SPEED_MS, 1);
            chance *= float(rogue->GetAttackTime(attType)) / float(referenceMs);
        }

        return RollProcChance(rogue, chance);
    }

    void CastHackAndSlash(Player* rogue, Unit* target)
    {
        if (!rogue || !target || !target->IsAlive() || !rogue->IsValidAttackTarget(target))
            return;

        // bp = the rank's weapon percent (R20: a weapon-percent effect has no level scaling, so it is exact).
        int32 const weaponPct = GetRankAmount(rogue, { RogueData::SPELL_HACK_AND_SLASH,
            RogueData::SPELL_HACK_AND_SLASH_13961, RogueData::SPELL_HACK_AND_SLASH_13962 }, EFFECT_0);
        if (weaponPct <= 0)
            return;

        rogue->CastCustomSpell(target, RogueData::SPELL_HACK_AND_SLASH_MAIN, &weaponPct, nullptr, nullptr, true);
        if (rogue->haveOffhandWeapon() && target->IsAlive())
            rogue->CastCustomSpell(target, RogueData::SPELL_HACK_AND_SLASH_OFF, &weaponPct, nullptr, nullptr, true);
    }

    void OnKickInterrupt(Player* rogue)
    {
        if (rogue && rogue->IsAlive() && rogue->HasAura(RogueData::SPELL_IMPROVED_KICK_13867))
            rogue->CastSpell(rogue, RogueData::SPELL_IMPROVED_KICK_BUFF, TRIGGERED_FULL_MASK);
    }

    // ---- S3a fix pass ----

    void StampFanOfKnivesGain(Player* rogue, int32 gain)
    {
        if (!rogue || gain <= 0)
            return;

        // S3a-REVIEW L1: called while the award is being granted (the first target's hit), so the stamp has landed.
        // Seal Fate on the cast's own crits refreshes its base (GainComboPoints -> RefreshBuilderStamp) before the
        // native gain lands in the finish phase; the +1 ms event banks what that gain lost to the cap.
        BuilderStamp* stamp = rogue->CustomData.GetDefault<BuilderStamp>(BUILDER_STAMP_KEY);
        ResolveBuilderStamp(rogue, stamp->seq);

        stamp->live = true;
        ++stamp->seq;
        stamp->spellId = FAN_OF_KNIVES_SPELL_ID;
        stamp->points = rogue->GetComboPoints();
        stamp->gain = gain;
        stamp->landed = true;

        uint32 const seq = stamp->seq;
        rogue->m_Events.AddEventAtOffset([rogue, seq]()
        {
            ResolveBuilderStamp(rogue, seq);
        }, Milliseconds(1));
    }

    void RollCastPoisons(Player* rogue, Unit* target, Spell const* spell)
    {
        if (!rogue || !target || !spell)
            return;

        // The cast's own proc event, rebuilt: PoisonRollAllowed applies the same guard rules (actor, hostile target,
        // CC / suppressor attributes, triggered casts, once per cast per aura) and RollPoison the same chance.
        for (uint32 const auraId : POISON_AURAS)
        {
            Aura* aura = rogue->GetAura(auraId, rogue->GetGUID());
            if (!aura)
                continue;

            AuraEffect const* triggeredBy = aura->GetEffect(EFFECT_0);
            if (!triggeredBy)
                continue;

            ProcEventInfo eventInfo(rogue, target, target, PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, PROC_SPELL_TYPE_DAMAGE,
                PROC_SPELL_PHASE_HIT, PROC_HIT_NORMAL, spell, nullptr, nullptr);
            if (!PoisonRollAllowed(rogue, eventInfo, auraId) || !RollPoison(rogue, auraId, eventInfo))
                continue;

            ApplyPoison(rogue, target, aura->GetSpellInfo()->Effects[EFFECT_0].TriggerSpell, triggeredBy,
                PoisonSource::Roll);
            if (!target->IsAlive())
                return;
        }
    }

    void UpdatePreyRankCache(Player* rogue)
    {
        if (!rogue)
            return;

        SpellInfo const* rank = GetHeldRank(rogue, { RogueData::SPELL_PREY_ON_THE_WEAK,
            RogueData::SPELL_PREY_ON_THE_WEAK_51686, RogueData::SPELL_PREY_ON_THE_WEAK_51687 });
        uint32 const rankId = rank ? rank->Id : 0;
        if (PreyRankCache* cache = rogue->CustomData.Get<PreyRankCache>(PREY_RANK_CACHE_KEY))
            cache->rankId = rankId;
        else if (rankId)
            rogue->CustomData.GetDefault<PreyRankCache>(PREY_RANK_CACHE_KEY)->rankId = rankId;
    }
}
