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

#include "WarriorMechanics.h"
#include "CellImpl.h"
#include "DataMap.h"
#include "EngagementMechanics.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Item.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Timer.h"
#include "Unit.h"
#include "Util.h"
#include "World.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <initializer_list>
#include <limits>
#include <list>
#include <map>
#include <mutex>
#include <unordered_map>
#include <utility>
#include <vector>

namespace Warrior
{
    namespace
    {
        // Critical Block's SpellIconID, read off its effect index 1 carrier (dbc-tools critical_block_* rows, icon
        // 2778). Keep in sync if those rows ever change icon.
        constexpr uint32 ICON_CRITICAL_BLOCK = 2778;

        // ---- S1: Protection ----
        // Revenge: SPELLFAMILY_WARRIOR, SpellFamilyFlags[0] 0x400 (6572 and the stale rank 25288).
        constexpr uint32 REVENGE_FAMILY_FLAG_0 = 0x400;

        // D5: the shield's maximum, percent of max health before the capstone's Mastery.
        constexpr float STORMS_BULWARK_CAP_PCT = 30.0f;
        // D4: Unrelenting never ends Last Stand's cooldown before 50% of its hasted length has passed.
        constexpr uint32 LAST_STAND_FLOOR_PCT = 50;
        // D11: a Revenge stamp older than this cannot feed Incite (its hits land in the cast's own launch).
        constexpr uint32 REVENGE_STAMP_MAX_AGE_MS = 1000;
        // Cooldown Haste's eligibility floor (Player.cpp CUSTOM_COOLDOWN_HASTE_MIN_BASE_COOLDOWN_MS; keep in sync).
        constexpr uint32 COOLDOWN_HASTE_MIN_BASE_MS = 30 * IN_MILLISECONDS;

        uint32 NowMs()
        {
            return uint32(GameTime::GetGameTimeMS().count());
        }

        bool IsRevenge(SpellInfo const* spellInfo)
        {
            return spellInfo->SpellFamilyName == SPELLFAMILY_WARRIOR
                && (spellInfo->SpellFamilyFlags[0] & REVENGE_FAMILY_FLAG_0);
        }

        // The highest held talent rank's DUMMY carrier value (ranks listed highest first; talent ranks are passive
        // auras on the player). 0 when no rank is held, or while the rank's effect is not a DUMMY carrier yet (the
        // pre-S1 rows carry SpellMods or proc triggers on the same index, whose amounts must never be read here).
        int32 GetRankCarrier(Unit const* unit, std::initializer_list<uint32> ranksHighestFirst, uint8 effIndex)
        {
            for (uint32 const rankId : ranksHighestFirst)
                if (AuraEffect const* effect = unit->GetAuraEffect(rankId, effIndex))
                    return effect->GetAuraType() == SPELL_AURA_DUMMY ? effect->GetAmount() : 0;

            return 0;
        }

        // Incite's once-per-cast stamp (D11): set by the dispatcher on a Revenge cast, consumed by its first crit.
        struct RevengeCastStamp : DataMap::Base
        {
            uint32 castMs = 0;
            bool pending = false;
        };

        constexpr char const* REVENGE_STAMP_KEY = "warrior_revenge_stamp";

        // The Thunder Clap script's unamplified Storm's Bulwark percent, for the echo (D6).
        struct ThunderClapBulwarkRecord : DataMap::Base
        {
            float unamplifiedPct = 0.0f;
        };

        constexpr char const* THUNDER_CLAP_BULWARK_KEY = "warrior_thunder_clap_bulwark";

        // Percent-of-damage bleeds on their target (D7): per (warrior, holder aura) the per-tick amount.
        struct PercentBleedState : DataMap::Base
        {
            std::map<std::pair<ObjectGuid, uint32>, uint32> perTick;
        };

        constexpr char const* PERCENT_BLEED_KEY = "warrior_percent_bleed";

        // Last Stand cast records for Unrelenting's floor (D4, Druid Barkskin shape): process-wide, not CustomData,
        // so a relog inside the window keeps the floor; locked because maps update on several threads.
        struct LastStandCastRecord
        {
            uint32 castMs = 0;
            uint32 hastedLengthMs = 0;
        };

        std::mutex lastStandCastLock;
        std::unordered_map<ObjectGuid, LastStandCastRecord> lastStandCastByPlayer;

        uint32 LastStandFloorEndMs(LastStandCastRecord const& record)
        {
            return record.castMs + record.hastedLengthMs * LAST_STAND_FLOOR_PCT / 100;
        }

        // The cooldown length the cast will end up with once Cooldown Haste's deferred correction has landed:
        // Player::AddSpellAndCategoryCooldowns' own math (SPELLMOD_COOLDOWN on rec / catrec, SPELL_AURA_MOD_COOLDOWN
        // on rec for own spells, then rec or catrec divided by 1 + CDH% when its base is >= 30 s). The allow / deny
        // lists there name no warrior spell; keep in sync if one is added.
        uint32 HastedCooldownLengthMs(Player* warrior, SpellInfo const* spellInfo)
        {
            int32 rec = int32(spellInfo->RecoveryTime);
            int32 catrec = int32(spellInfo->CategoryRecoveryTime);

            if (rec > 0)
                warrior->ApplySpellMod(spellInfo->Id, SPELLMOD_COOLDOWN, rec);

            if (catrec > 0 && !spellInfo->HasAttribute(SPELL_ATTR6_NO_CATEGORY_COOLDOWN_MODS))
                warrior->ApplySpellMod(spellInfo->Id, SPELLMOD_COOLDOWN, catrec);

            if (int32 const cooldownMod = warrior->GetTotalAuraModifier(SPELL_AURA_MOD_COOLDOWN))
                if (warrior->HasSpell(spellInfo->Id))
                    rec += cooldownMod * IN_MILLISECONDS;

            rec = std::max(rec, 0);
            catrec = std::max(catrec, 0);

            if (float const cdh = warrior->GetCooldownHastePercentage(); cdh > 0.0f)
            {
                float const divisor = 1.0f + cdh / 100.0f;
                if (spellInfo->RecoveryTime >= COOLDOWN_HASTE_MIN_BASE_MS)
                    rec = int32(rec / divisor);
                if (spellInfo->CategoryRecoveryTime >= COOLDOWN_HASTE_MIN_BASE_MS)
                    catrec = int32(catrec / divisor);
            }

            return uint32(rec ? rec : catrec);
        }

        // Margin past a GCD before a cooldown clear (Player.cpp GetCooldownHasteCorrectionDelay, bug log CDH-GCD-FIX).
        constexpr uint32 GCD_SAFE_MARGIN_MS = 100;

        // Sword and Board's success (one per roll): the buff and Shield Slam's reset. A trigger right after Shield
        // Slam itself (an off-GCD Spell Reflection, Shield Bash, Pummel or the echo) defers once, to Shield Slam's
        // cast start + its GCD + 100 ms; every other case grants now. The event lives on the warrior's own
        // m_Events, so it dies with the player and never outlives the pointer it captures.
        void GrantSwordAndBoard(Player* warrior, bool mayDefer)
        {
            if (!warrior->IsAlive())
                return;

            if (mayDefer)
            {
                if (uint32 const waitMs = OwnGcdRemainingMs(warrior, WarriorData::SPELL_SHIELD_SLAM))
                {
                    warrior->m_Events.AddEventAtOffset([warrior]()
                    {
                        GrantSwordAndBoard(warrior, false);
                    }, Milliseconds(waitMs));
                    return;
                }
            }

            warrior->CastSpell(warrior, WarriorData::SPELL_SWORD_AND_BOARD_BUFF, true);
            // Shield Slam is single-rank (trainers teach 23922 only), so one SMSG_CLEAR_COOLDOWN does it. Clearing
            // category 1209 instead would also reset Shield of Righteousness (53600/61411) on the classless realm.
            warrior->RemoveSpellCooldown(WarriorData::SPELL_SHIELD_SLAM, true);
        }

        // Delay past the triggering cast's GCD (Player.cpp GetCooldownHasteCorrectionDelay, bug log CDH-GCD-FIX):
        // StartRecoveryTime + 100 ms on the GCD, 1 ms off it.
        uint32 GcdSafeDelayMs(SpellInfo const* spellInfo)
        {
            if (spellInfo->StartRecoveryCategory && spellInfo->StartRecoveryTime)
                return spellInfo->StartRecoveryTime + GCD_SAFE_MARGIN_MS;

            return 1;
        }

        // ---- S2: Arms (S2 handoff D3-D25, WP brief R1-R21) ----
        // D3: Colossus Smash's damage-taken bonus before Mastery [fixed].
        constexpr float COLOSSUS_SMASH_PCT = 15.0f;
        // D3: each Mortal Strike hit cuts Colossus Smash's cooldown by this much (real time).
        constexpr Milliseconds COLOSSUS_SMASH_MORTAL_STRIKE_CUT = 2s;
        // D4: the copy's share of the main hit without Improved Sweeping Strikes (45/50% from its DUMMY carrier).
        constexpr int32 SWEEPING_STRIKES_BASE_PCT = 40;
        constexpr float SWEEPING_STRIKES_RADIUS_YD = 8.0f;
        constexpr std::size_t SWEEPING_STRIKES_MAX_TARGETS = 4;
        // D5: the stock Deep Wounds basis divides attack power by 14 per second of weapon speed.
        constexpr float DEEP_WOUNDS_AP_PER_SPEED_DIVISOR = 14.0f;
        // D6: Taste for Blood's capstone chance on a Mortal Strike hit (x the Proc Chance stat).
        constexpr float TASTE_FOR_BLOOD_CAPSTONE_PCT = 50.0f;
        // D15: Execute (5308 and every stock rank): SPELLFAMILY_WARRIOR d0 b29.
        constexpr uint32 EXECUTE_FAMILY_FLAG_0 = 0x20000000;
        // D18: Second Wind's heal doubles below this health percent [fixed].
        constexpr int32 SECOND_WIND_LOW_HEALTH_PCT = 35;
        // Finding 8: the Blood Frenzy debuff is re-cast from the bleed paths when less than this remains.
        constexpr int32 BLOOD_FRENZY_REFRESH_BELOW_MS = 7 * IN_MILLISECONDS;
        // D19: the echo waits for the off-hand hits, then needs this many distinct Whirlwind targets.
        constexpr Milliseconds SEISMIC_ECHO_DELAY = 500ms;
        constexpr std::size_t SEISMIC_MIN_TARGETS = 3;

        // CustomData keys stay within the small-string buffer: these lookups run on hot hooks.
        constexpr char const* SWEEPING_STASH_KEY = "war_sweep";
        constexpr char const* WHIRL_CRIT_KEY = "war_whirl_crit";
        constexpr char const* SEISMIC_KEY = "war_seismic";
        constexpr char const* RAGE_OVERFLOW_KEY = "war_rage_over";

        // D4: the Sweeping share of one main hit, captured in ModifySpellDamageTaken and spent by the same hit's
        // OnSpellDamageTakenFinal (one CalculateSpellDamageTaken call, so the same game-time ms).
        struct SweepingShare
        {
            int32 share = 0;
            uint32 capturedMs = 0;
        };

        struct SweepingStash : DataMap::Base
        {
            std::map<std::pair<uint32, ObjectGuid>, SweepingShare> byHit;
        };

        // R4: a Bladestorm whirl crit, stamped by OnSpellDamageTakenFinal and read by the same whirl's AfterCast.
        struct WhirlCritStamp : DataMap::Base
        {
            uint32 ms = 0;
            bool crit = false;
        };

        // D19: per-target pre-absorb Whirlwind damage (main hand + off hand) until the echo fires.
        struct SeismicState : DataMap::Base
        {
            std::map<ObjectGuid, int64> sums;
        };

        // D11: rage that overflowed but has not made a whole point yet, in power units (tenths).
        struct RageOverflowCarry : DataMap::Base
        {
            int32 remainder = 0;
        };

        // Ticks the live aura still pays at the row's cadence: ceil(remaining duration / amplitude) (the
        // Rogue::ApplyStoredBleed reading).
        uint32 GetRemainingTicks(Aura const* aura, int32 amplitude)
        {
            int32 const duration = aura->GetDuration();
            if (amplitude <= 0 || duration <= 0)
                return 0;

            return uint32((duration + amplitude - 1) / amplitude);
        }

        // D4 (arms-cpp mechanism 2): a single-target melee hit. Area, chained and proc-suppressed spells never sweep;
        // the last rule also excludes the copy, the Seismic echo, the sword strike and both bleed ticks. Execute's
        // triggered damage 20647 counts.
        bool IsSweepSource(SpellInfo const* spellInfo)
        {
            if (spellInfo->DmgClass != SPELL_DAMAGE_CLASS_MELEE
                || spellInfo->HasAttribute(SPELL_ATTR3_SUPPRESS_CASTER_PROCS) || spellInfo->IsAffectingArea())
                return false;

            switch (spellInfo->Id)
            {
                case WarriorData::SPELL_SWEEPING_STRIKES_COPY:
                case WarriorData::SPELL_BLADESTORM_WHIRL:
                case WarriorData::SPELL_WEAPON_SPECIALIZATION_STRIKE:
                case WarriorData::SPELL_HEROIC_LEAP_204401:
                    return false;
                default:
                    break;
            }

            return std::none_of(std::begin(spellInfo->Effects), std::end(spellInfo->Effects),
                [](SpellEffectInfo const& effect) { return effect.ChainTarget > 1; });
        }

        // D4: stash the share of a main hit, before Colossus Smash and Exploiter touch `damage`. The main target's
        // percent damage-taken auras (Blood Frenzy, Savage Combat, ...) are divided out: the copy's own target applies
        // its own.
        void CaptureSweepingShare(Player* warrior, Unit* target, SpellInfo const* spellInfo, int32 damage)
        {
            float const takenMultiplier = target->GetTotalAuraMultiplierByMiscMask(
                SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN, spellInfo->GetSchoolMask());
            if (takenMultiplier <= 0.0f)
                return;

            int32 sharePct = GetRankCarrier(warrior, { WarriorData::SPELL_IMPROVED_SWEEPING_STRIKES_204530,
                WarriorData::SPELL_IMPROVED_SWEEPING_STRIKES }, EFFECT_1);
            if (sharePct <= 0)
                sharePct = SWEEPING_STRIKES_BASE_PCT;

            int32 const share = int32(damage / takenMultiplier * float(sharePct) / 100.0f);
            if (share <= 0)
                return;

            uint32 const now = NowMs();
            SweepingStash* stash = warrior->CustomData.GetDefault<SweepingStash>(SWEEPING_STASH_KEY);
            // A capture whose final hook never ran (an earlier update) is stale: drop it so the map stays tiny.
            std::erase_if(stash->byHit, [now](auto const& entry) { return entry.second.capturedMs != now; });
            stash->byHit[{ spellInfo->Id, target->GetGUID() }] = { share, now };
        }

        // Removes this hit's stash entry (always, before any copy re-enters the hooks) and returns its share, 0 when
        // there is none or it is stale.
        int32 TakeSweepingShare(Player* warrior, uint32 spellId, ObjectGuid targetGuid)
        {
            SweepingStash* stash = warrior->CustomData.Get<SweepingStash>(SWEEPING_STASH_KEY);
            if (!stash)
                return 0;

            auto const itr = stash->byHit.find({ spellId, targetGuid });
            if (itr == stash->byHit.end())
                return 0;

            SweepingShare const entry = itr->second;
            stash->byHit.erase(itr);
            return entry.capturedMs == NowMs() ? entry.share : 0;
        }

        // D7 / Q16: what lets Avatar apply Colossus Smash. Any warrior-family direct damage ability hit (Thunder
        // Clap and the Heroic Leap landing included), the Sweeping copy and the Bladestorm whirl. Never the
        // proc-suppressed helpers (Seismic echo, bleed ticks, sword strike) nor the Thunder Clap echo. White swings
        // and periodic ticks never reach this hook.
        bool IsAvatarSource(SpellInfo const* spellInfo)
        {
            switch (spellInfo->Id)
            {
                case WarriorData::SPELL_SWEEPING_STRIKES_COPY:
                case WarriorData::SPELL_BLADESTORM_WHIRL:
                    return true;
                case WarriorData::SPELL_THUNDER_CLAP_ECHO:
                case WarriorData::SPELL_SEISMIC_REVERBERATION_ECHO:
                case WarriorData::SPELL_DEEP_WOUNDS_TICK:
                case WarriorData::SPELL_BLOODSTORM_TICK:
                    return false;
                default:
                    break;
            }

            return spellInfo->SpellFamilyName == SPELLFAMILY_WARRIOR
                && !spellInfo->HasAttribute(SPELL_ATTR3_SUPPRESS_CASTER_PROCS);
        }

        // R11: a talent aura's proc rolled by hand for a triggered whirl, in the native order (Aura::GetProcEffectMask,
        // CalcProcChance, PrepareProcToTrigger): the aura's proc cooldown, SPELLMOD_CHANCE_OF_SUCCESS, the Proc Chance
        // stat, the roll, then the cooldown on success only. The cooldown is the aura's own, shared with its data proc.
        bool RollTalentProcByHand(Player* warrior, Aura* aura)
        {
            if (!aura)
                return false;

            TimePoint const now = Acore::Time::SteadyNow();
            if (aura->IsProcOnCooldown(now))
                return false;

            SpellProcEntry const* procEntry = sSpellMgr->GetSpellProcEntry(aura->GetId());
            if (!procEntry)
                return false;

            float chance = procEntry->Chance;
            warrior->ApplySpellMod(aura->GetId(), SPELLMOD_CHANCE_OF_SUCCESS, chance);
            if (!RollProcChance(warrior, chance))
                return false;

            aura->AddProcCooldown(procEntry, now);
            return true;
        }

        // D19: the echo, 500 ms after a Whirlwind cast. Counts the targets now (the off-hand hits may land after the
        // cast's AfterCast) and clears the sums either way.
        void FireSeismicEcho(Player* warrior)
        {
            SeismicState* state = warrior->CustomData.Get<SeismicState>(SEISMIC_KEY);
            if (!state || state->sums.empty())
                return;

            std::map<ObjectGuid, int64> sums;
            sums.swap(state->sums);

            if (sums.size() < SEISMIC_MIN_TARGETS || !warrior->IsAlive())
                return;

            int32 const echoPct = GetRankCarrier(warrior, { WarriorData::SPELL_SEISMIC_REVERBERATION_204539,
                WarriorData::SPELL_SEISMIC_REVERBERATION }, EFFECT_0);
            if (echoPct <= 0)
                return;

            for (auto const& [guid, sum] : sums)
            {
                Unit* unit = ObjectAccessor::GetUnit(*warrior, guid);
                if (!unit || !unit->IsAlive())
                    continue;

                // A SPELLVALUE base point is the final amount (Spell::SetSpellValue).
                int64 const echo = sum * echoPct / 100;
                if (echo > 0)
                    warrior->CastCustomSpell(WarriorData::SPELL_SEISMIC_REVERBERATION_ECHO, SPELLVALUE_BASE_POINT0,
                        int32(std::min<int64>(echo, std::numeric_limits<int32>::max())), unit, TRIGGERED_FULL_MASK);
            }
        }

        // ---- S3: Fury (S3 handoff D3-D34, WP brief R1-R7, 3b) ----
        // D16: the Heroic Leap button (d2 b0) and the Rampage cast + strikes (d2 b2, _masks.RAMPAGE).
        constexpr uint32 HEROIC_LEAP_FAMILY_FLAG_2 = 0x1;
        constexpr uint32 RAMPAGE_FAMILY_FLAG_2 = 0x4;
        // D4: Death Wish raises the summed Enrage bonus by half [fixed].
        constexpr float DEATH_WISH_ENRAGE_FACTOR = 1.5f;
        // D30: Commanding Presence scales linearly with the caster's level up to this one.
        constexpr uint8 COMMANDING_PRESENCE_FULL_LEVEL = 60;
        // Power units per displayed rage point (spell costs and ModifyPower amounts are tenths).
        constexpr int32 POWER_PER_RAGE = 10;

        constexpr char const* ENRAGE_METER_KEY = "war_enr_meter";
        constexpr char const* RAMPAGE_KEY = "war_rampage";

        // D3: rage paid toward the next Enrage, in power units; the rest after a fill carries over. Dies with the
        // Player object, so it starts empty on login (the display aura is never saved either).
        struct EnrageMeter : DataMap::Base
        {
            int32 value = 0;
        };

        // D7: one Rampage sequence. The press state (OnRampageCast) and the running strike events (StartRampage);
        // `sequence` lets a stale event from an earlier sequence return at once.
        struct RampageState : DataMap::Base
        {
            uint32 sequence = 0;
            bool running = false;
            ObjectGuid target;
            float enrageSnapPct = 0.0f;
        };

        // The Enrage talent ranks (155), highest first. e0 = damage carrier, e1 = haste carrier.
        int32 GetEnrageRankCarrier(Unit const* unit, uint8 effIndex)
        {
            return GetRankCarrier(unit, { WarriorData::SPELL_ENRAGE_13048, WarriorData::SPELL_ENRAGE_13047,
                WarriorData::SPELL_ENRAGE_13046, WarriorData::SPELL_ENRAGE_13045, WarriorData::SPELL_ENRAGE },
                effIndex);
        }

        bool HasEnrageRank(Unit const* unit)
        {
            return GetEnrageRankCarrier(unit, EFFECT_0) > 0;
        }

        // The value spell_warr_enrage_fury's DoEffectCalcAmount puts on 204636's damage effect (rounded percent).
        int32 GetEnrageBonusAmount(Player const* warrior)
        {
            return int32(std::lround(GetEnrageBonusPct(warrior)));
        }

        // The meter display (P0 SetMeterStacks): one stack per ENRAGE_METER_STACK rage; SetStackAmount re-applies
        // the aura and forces a client update, so it only runs on a change; removed at 0.
        void SetEnrageMeterStacks(Player* warrior, int32 meterValue)
        {
            int32 const stackPower = int32(WarriorData::ENRAGE_METER_STACK) * POWER_PER_RAGE;
            uint8 const stacks = stackPower > 0 ? uint8(std::clamp<int32>(meterValue / stackPower, 0, 255)) : 0;
            if (!stacks)
            {
                warrior->RemoveAurasDueToSpell(WarriorData::SPELL_ENRAGE_METER);
                return;
            }

            if (Aura* aura = warrior->GetAura(WarriorData::SPELL_ENRAGE_METER))
            {
                if (aura->GetStackAmount() != stacks)
                    aura->SetStackAmount(stacks);
            }
            else if (Aura* added = warrior->AddAura(WarriorData::SPELL_ENRAGE_METER, warrior))
            {
                if (stacks > 1)
                    added->SetStackAmount(stacks);
            }
        }

        // D7: ends a Rampage sequence (last strike, target gone / dead / out of range, the warrior dead). The press
        // snapshot's crit aura goes with it.
        void StopRampage(Player* warrior, RampageState* state)
        {
            state->running = false;
            warrior->RemoveAurasDueToSpell(WarriorData::SPELL_RAMPAGE_SNAPSHOT);
        }

        // D7: strike `index` (0-3: main, off, main, off hand) of sequence `sequence`, from the warrior's m_Events (the
        // event list dies with the player). Each strike is its own triggered Spell: own crit roll, the damage hooks
        // (GetRampageStrikeMultiplier, the crit refresh), no CAST event and no procs (SUPPRESS flags in data).
        void RampageStrike(Player* warrior, uint32 sequence, std::size_t index, std::size_t count)
        {
            RampageState* state = warrior->CustomData.Get<RampageState>(RAMPAGE_KEY);
            if (!state || !state->running || state->sequence != sequence)
                return;

            // GetUnit searches the warrior's own map: a target on another map (or despawned) reads as gone.
            Unit* target = ObjectAccessor::GetUnit(*warrior, state->target);
            if (!target || !target->IsAlive() || !warrior->IsAlive() || !warrior->IsWithinMeleeRange(target))
            {
                StopRampage(warrior, state);
                return;
            }

            // B-R2: the strike rows skip the cast-time off-hand weapon check (EquippedItemClass -1), and an off-hand
            // strike without a weapon would still deal its attack power part: no off-hand weapon, no strike.
            bool const offHand = index % 2 == 1;
            if (!offHand || warrior->HasOffhandWeaponForAttack())
                warrior->CastSpell(target, offHand ? WarriorData::SPELL_RAMPAGE_STRIKE_OH
                    : WarriorData::SPELL_RAMPAGE_STRIKE_MH, TRIGGERED_FULL_MASK);

            // The strike lands inside CastSpell (instant, triggered): the sequence may have been stopped meanwhile.
            if (index + 1 >= count && state->running && state->sequence == sequence)
                StopRampage(warrior, state);
        }
    }

    void ApplyBlockDamageReduction(Unit* defender, uint32& damage)
    {
        if (Player const* player = defender->ToPlayer())
            if (AuraEffect const* aurEff = player->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_WARRIOR, ICON_CRITICAL_BLOCK, EFFECT_1))
                AddPct(damage, -int32(aurEff->GetAmount()));
    }

    // ---- W0a rage model (docs/reworks/warrior-shared-rework.md "Rage generation", W0a D11-D14), W0b spell haste ----
    //
    // Worked example (level 60, 3.6 s two-hander, non-crit white hit 450, Battle Stance aura 213 +10%, k 0.43, m 1.35):
    //   c(60) = 230.60; damage term 7.5 * 450 / 230.60 = 14.64 -> * k = 6.29
    //   speed part 3.6 * 3.5 * 1.35 = 17.01 (factor 1701 in hundredths)
    //   (6.29 + 17.01) / 2 = 11.65; stock cap 15 * 450 / 230.60 = 29.27 not hit; * 1.10 = 12.82 rage
    //   (stock, before Battle Stance: (14.64 + 12) / 2 = 13.32). Crit 900, factor doubled: (12.59 + 34.02) / 2 * 1.10
    //   = 25.63.
    //   Bloodlust (30% melee and spell haste): swing 2.77 s, cast speed 1 / 1.30, so the speed part reads
    //   2.77 * 1.30 = 3.6 s of swing again: 12.82 per swing, rage per second x1.30. An attack-speed-only 30% (Slice and
    //   Dice style, cast speed untouched): speed part 13.09 -> 10.66 per swing, rage per second x1.08. A casting slow
    //   (cast speed > 1) changes nothing. Off hand 2.6 s, hit 200, no aura: (0.43 * 6.51 + 2.275) / 2 = 2.54.

    float RageConversion(uint8 level)
    {
        // Mirrors the stock constants in Unit::RewardRage (wowwiki rage formulae), including its linear adjustment
        // above level 70. Keep the two in sync.
        float conversion = ((0.0091107836f * level * level) + 3.225598133f * level) + 4.2652911f;
        if (level > 70)
            conversion += 13.27f * (level - 70);

        return conversion;
    }

    RageConstants GetRageConstants(uint8 /*level*/)
    {
        // D13: one table keyed on level; only the level-60 bracket is set, so it applies at every level until the
        // 70/80 brackets open.
        return { WarriorData::RAGE_K_60, WarriorData::RAGE_M_60 };
    }

    uint32 RageSpeedFactor(Unit const* attacker, WeaponAttackType attType)
    {
        // D11: creatures and pets keep the stock factor (whole rage points, unhasted swing).
        if (!attacker->IsPlayer())
            return attacker->GetRageWeaponSpeedHitFactor(attType);

        // The hasted swing (the raw field, not GetAttackTime, which divides haste back out): attack speed alone
        // shortens the swing and its rage, so it only adds the damage term's share per second.
        float const hastedSwingMs = attacker->GetFloatValue(static_cast<uint16>(UNIT_FIELD_BASEATTACKTIME) + attType);

        // W0b D21: spell haste is the haste for haste-scaled resources (the rogue energy rule, GetEnergyHastePct).
        // UNIT_MOD_CAST_SPEED holds haste rating, casting-speed and combat-speed auras, never melee-only attack speed;
        // lower = faster. Scaling the swing by 1 / castSpeed gives back what spell haste took from the swing, so
        // rage per swing holds and rage per second rises with it. A net slow (castSpeed > 1) never lowers rage; no cap.
        float const castSpeed = attacker->GetFloatValue(UNIT_MOD_CAST_SPEED);
        float const spellHasteFactor = castSpeed > 0.0f ? std::max(1.0f, 1.0f / castSpeed) : 1.0f;

        float const handFactor = attType == BASE_ATTACK
            ? WarriorData::RAGE_MH_SPEED_FACTOR * GetRageConstants(attacker->GetLevel()).m
            : WarriorData::RAGE_OH_SPEED_FACTOR;

        // In hundredths (RAGE_SPEED_FIXED_POINT) so m's decimals survive the uint32 the callers carry.
        return uint32(std::lround(hastedSwingMs * spellHasteFactor / 1000.0f * handFactor
            * WarriorData::RAGE_SPEED_FIXED_POINT));
    }

    bool RewardRage(Unit* unit, uint32 damage, uint32 weaponSpeedHitFactor, bool attacker)
    {
        // Every non-player keeps the stock body.
        if (!unit->IsPlayer())
            return false;

        if (!attacker)
        {
            // S1 D18 Focused Rage: a player holding a rank gets the stock taken formula (2.5 * d / c, Berserker Rage
            // x3, RATE_POWER_RAGE_INCOME) x (1 + 5/10/15%). Everyone else (bears included) keeps the stock body.
            int32 const focusedRagePct = GetRankCarrier(unit, { WarriorData::SPELL_FOCUSED_RAGE_29792,
                WarriorData::SPELL_FOCUSED_RAGE_29790, WarriorData::SPELL_FOCUSED_RAGE }, EFFECT_0);
            if (focusedRagePct <= 0)
                return false;

            float addRage = damage / RageConversion(unit->GetLevel()) * 2.5f;
            if (unit->HasAura(WarriorData::SPELL_BERSERKER_RAGE))
                addRage *= 3.0f;

            AddPct(addRage, focusedRagePct);
            addRage *= sWorld->getRate(RATE_POWER_RAGE_INCOME);

            unit->ModifyPower(POWER_RAGE, uint32(addRage * 10));
            return true;
        }

        // D12: an attacker call with factor 0 is the fully-absorbed duplicate (Unit::DealDamage); it grants nothing.
        if (!weaponSpeedHitFactor)
            return true;

        RageConstants const constants = GetRageConstants(unit->GetLevel());
        float const conversion = RageConversion(unit->GetLevel());

        float const stockDamageTerm = damage / conversion * 7.5f;
        float const speedPart = weaponSpeedHitFactor / float(WarriorData::RAGE_SPEED_FIXED_POINT);

        float addRage = (constants.k * stockDamageTerm + speedPart) / 2.0f;
        // The stock cap (2 * 7.5 * d / c), on the undampened damage term, so it does not clip normal swings.
        addRage = std::min(addRage, stockDamageTerm * 2.0f);
        AddPct(addRage, unit->GetTotalAuraModifier(SPELL_AURA_MOD_RAGE_FROM_DAMAGE_DEALT));
        addRage *= sWorld->getRate(RATE_POWER_RAGE_INCOME);

        unit->ModifyPower(POWER_RAGE, uint32(addRage * 10));
        return true;
    }

    // ---- W0b: Charge in combat (D4) ----
    int32 ChargeCombatRage(float distanceYd)
    {
        constexpr float span = WarriorData::CHARGE_COMBAT_MAX_YD - WarriorData::CHARGE_COMBAT_MIN_YD;
        static_assert(span > 0.0f, "CHARGE_COMBAT_MAX_YD must exceed CHARGE_COMBAT_MIN_YD");

        float const t = std::clamp((distanceYd - WarriorData::CHARGE_COMBAT_MIN_YD) / span, 0.0f, 1.0f);
        // 5 to 10 rage, in power units (tenths of a rage point).
        return int32(std::lround(10.0f * (5.0f + 5.0f * t)));
    }

    // ---- S1: Protection (docs/reworks/warrior-protection-rework.md; S1-HANDOFF D3-D7, D11, D13, D18, D19) ----
    // One dispatcher and one helper per mechanic; S2 / S3 append branches here, never fork them.

    bool RollProcChance(Player const* warrior, float pct)
    {
        if (!warrior || pct <= 0.0f)
            return false;

        return roll_chance_f(std::min(pct * (1.0f + warrior->GetProcChancePercentage() / 100.0f), 100.0f));
    }

    void OnSpellCast(Player* warrior, Spell const* spell)
    {
        if (!warrior || !spell || spell->IsTriggered())
            return;

        SpellInfo const* spellInfo = spell->GetSpellInfo();
        if (!spellInfo)
            return;

        // (0) S3 D3 / R1: the Enrage meter, first, so a fill Enrages this same cast (the Rampage snapshot, Frenzied
        // Blows' Enraged check). Every rage-cost cast of any family (a Classless bear's Maul too); GetPowerCost is
        // the cost after COST mods, so free casts add nothing; Bloodrage costs health. AddRagePaid needs a rank.
        if (spellInfo->PowerType == POWER_RAGE && spell->GetPowerCost() > 0)
            AddRagePaid(warrior, spell->GetPowerCost());

        // R1: the hook lets every rage-cost cast through for the meter; every branch below keeps the S1 filter
        // (Warrior family, Bloodrage, Last Stand).
        if (spellInfo->SpellFamilyName != SPELLFAMILY_WARRIOR && spellInfo->Id != WarriorData::SPELL_BLOODRAGE
            && spellInfo->Id != WarriorData::SPELL_LAST_STAND)
            return;

        // (1) Last Stand: the cast time and the cooldown length after Cooldown Haste, for Unrelenting's floor (D4).
        if (spellInfo->Id == WarriorData::SPELL_LAST_STAND)
            RecordLastStandCast(warrior, Milliseconds(HastedCooldownLengthMs(warrior, spellInfo)));

        // (2) Revenge: Incite's once-per-cast stamp (D11); Empowered Revenge's shield while its charge is still up
        // (the charge is spent later in this cast, D15).
        if (IsRevenge(spellInfo))
        {
            RevengeCastStamp* stamp = warrior->CustomData.GetDefault<RevengeCastStamp>(REVENGE_STAMP_KEY);
            stamp->castMs = NowMs();
            stamp->pending = true;

            if (warrior->HasAura(WarriorData::SPELL_EMPOWERED_REVENGE))
                GrantStormsBulwark(warrior, 2.0f, BulwarkSource::EmpoweredRevenge);
        }

        // (3) Improved Bloodrage (D19): pressed in Defensive Stance with a rank, -2/-4% damage taken for Bloodrage's
        // 10 s; the buff's Stances field removes it when the warrior leaves the stance.
        if (spellInfo->Id == WarriorData::SPELL_BLOODRAGE && warrior->GetShapeshiftForm() == FORM_DEFENSIVESTANCE)
        {
            int32 const reductionPct = GetRankCarrier(warrior, { WarriorData::SPELL_IMPROVED_BLOODRAGE_12818,
                WarriorData::SPELL_IMPROVED_BLOODRAGE }, EFFECT_1);
            // Aura 87 amount -2/-4. A SPELLVALUE base point is the final value (Spell::SetSpellValue takes the
            // DieSides 1 back off, CalcValue adds it again).
            if (reductionPct > 0)
                warrior->CastCustomSpell(WarriorData::SPELL_IMPROVED_BLOODRAGE_BUFF, SPELLVALUE_BASE_POINT0,
                    -reductionPct, warrior, true);
        }

        // (4) Sword and Board (D13): every cast whose base cost is rage rolls once (casts made free still roll),
        // deferred past this cast's own GCD and SendSpellCooldown.
        if (spellInfo->PowerType == POWER_RAGE && spellInfo->ManaCost > 0)
            RollSwordAndBoard(warrior, GcdSafeDelayMs(spellInfo));

        // ---- S2: Arms ----
        // (5) Exploiter (D15, R7): an Execute cast puts this warrior's debuff (a stack) on the cast's explicit target.
        // A CAST-phase data proc would get a null target (0-verify B item 7). Runs before the hit, so the Execute's
        // own damage is untouched (only Mortal Strike reads the debuff).
        if (spellInfo->SpellFamilyName == SPELLFAMILY_WARRIOR
            && (spellInfo->SpellFamilyFlags[0] & EXECUTE_FAMILY_FLAG_0))
        {
            if (GetRankCarrier(warrior, { WarriorData::SPELL_EXPLOITER_204532, WarriorData::SPELL_EXPLOITER },
                EFFECT_0) > 0)
                if (Unit* target = spell->m_targets.GetUnitTarget(); target && target != warrior && target->IsAlive())
                    warrior->CastSpell(target, WarriorData::SPELL_EXPLOITER_DEBUFF, TRIGGERED_FULL_MASK);
        }

        // (6) Sweeping Strikes' Rend spread (D4): a Rend cast with the buff up also applies Rend to each Sweeping
        // target that lacks this warrior's Rend. Never refreshes. AddAura with the warrior as caster: a cast would fail
        // Rend's melee range and facing checks on targets up to 8 yd past the main one (CheckRange runs for triggered
        // casts too); the aura still takes the caster's duration / DOT / crit mods at creation and runs its AuraScript.
        if (spellInfo->Id == WarriorData::SPELL_REND && warrior->HasAura(WarriorData::SPELL_SWEEPING_STRIKES_ARMS))
        {
            if (Unit* mainTarget = spell->m_targets.GetUnitTarget(); mainTarget && mainTarget != warrior)
                for (Unit* unit : SelectSweepingTargets(warrior, mainTarget))
                    if (!unit->HasAura(WarriorData::SPELL_REND, warrior->GetGUID()))
                        warrior->AddAura(WarriorData::SPELL_REND, unit);
        }

        // ---- S3: Fury ----
        // (7) Fresh Meat (D10): the explicit target's health in the same _cast as the launch's crit roll. The fork
        // Bloodthirst script removes the charge in AfterCast (only one +100 crit mod applies per cast).
        if (spellInfo->Id == WarriorData::SPELL_BLOODTHIRST)
            ApplyFreshMeat(warrior, spell->m_targets.GetUnitTarget());
    }

    void OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo,
        bool isCrit)
    {
        // Runs for every spell hit in the world: cheapest rejects first.
        if (!spellInfo || !target || !attacker)
            return;

        Player* warrior = attacker->ToPlayer();
        if (!warrior)
            return;

        // (1) S1 D11 Incite capstone (unchanged; the warrior-family filter is IsRevenge's): the first Revenge crit
        // of a cast adds 1.5% (no refresh); one grant per cast.
        if (isCrit && IsRevenge(spellInfo) && warrior->HasAura(WarriorData::SPELL_INCITE_50687))
        {
            RevengeCastStamp* stamp = warrior->CustomData.Get<RevengeCastStamp>(REVENGE_STAMP_KEY);
            if (stamp && stamp->pending)
            {
                stamp->pending = false;
                if (NowMs() - stamp->castMs <= REVENGE_STAMP_MAX_AGE_MS)
                    GrantStormsBulwark(warrior, 1.5f, BulwarkSource::Incite);
            }
        }

        // (2) Sweeping spend (D4): only a sweep source can have a stash entry. A main hit that dealt nothing drops it.
        if (IsSweepSource(spellInfo))
        {
            if (damage > 0)
                CastSweepingCopies(warrior, target, spellInfo);
            else
                TakeSweepingShare(warrior, spellInfo->Id, target->GetGUID());
        }

        // (3) Avatar (D7): after the damage, so the applying hit is not raised by its own debuff.
        if (damage > 0 && warrior->HasAura(WarriorData::SPELL_AVATAR) && IsAvatarSource(spellInfo))
            ApplyColossusSmash(warrior, target);

        switch (spellInfo->Id)
        {
            // (4) A Sweeping copy crit starts Deep Wounds (the copy suppresses procs; the doc's one exception).
            case WarriorData::SPELL_SWEEPING_STRIKES_COPY:
                if (isCrit)
                    ApplyDeepWounds(warrior, target, BASE_ATTACK);
                break;
            // (5) A Bladestorm whirl crit (D10, Q4): Deep Wounds per critically struck target, and the stamp the
            // whirl's once-per-cast Wrecking Crew roll reads (R4).
            case WarriorData::SPELL_BLADESTORM_WHIRL:
                if (isCrit)
                {
                    ApplyDeepWounds(warrior, target, BASE_ATTACK);
                    WhirlCritStamp* stamp = warrior->CustomData.GetDefault<WhirlCritStamp>(WHIRL_CRIT_KEY);
                    stamp->ms = NowMs();
                    stamp->crit = true;
                }
                break;
            // (6) Seismic Reverberation (D19): Whirlwind's main- and off-hand hits, pre-absorb.
            case WarriorData::SPELL_WHIRLWIND:
            case WarriorData::SPELL_WHIRLWIND_44949:
                RecordWhirlwindHit(warrior, target, damage);
                break;
            // (7) Second Wind (D18) on the Deep Wounds tick (a direct spell; Rend ticks come through
            // OnPeriodicDamageFinal).
            case WarriorData::SPELL_DEEP_WOUNDS_TICK:
                if (damage > 0)
                    OnBleedTick(warrior, target, spellInfo, uint32(damage));
                break;
            // (8) S3 D7: a Rampage strike crit refreshes Flurry and Shredding Blows (the strikes roll no procs).
            case WarriorData::SPELL_RAMPAGE_STRIKE_MH:
            case WarriorData::SPELL_RAMPAGE_STRIKE_OH:
                if (isCrit)
                    RefreshCritChargeBuffs(warrior);
                break;
            default:
                break;
        }
    }

    // ---- S2: Arms (docs/reworks/warrior-arms-rework.md; S2 handoff D3-D25; WP brief R1-R21) ----

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo)
    {
        // Runs for every spell hit in the world: cheapest rejects first.
        if (damage <= 0 || !target || !attacker || !spellInfo)
            return;

        Player* warrior = attacker->ToPlayer();
        if (!warrior)
            return;

        // (1) The Sweeping share, before this hit's Colossus Smash and Exploiter (D4).
        if (IsSweepSource(spellInfo) && warrior->HasAura(WarriorData::SPELL_SWEEPING_STRIKES_ARMS))
            CaptureSweepingShare(warrior, target, spellInfo, damage);

        // (2) Colossus Smash, (3) Exploiter (Mortal Strike only), (4) S3 Merciless (D18), (5) S3 the Rampage
        // strikes' second Enrage at the press snapshot (D7, R5).
        float const multiplier = GetColossusSmashMultiplier(warrior, target, spellInfo)
            * GetExploiterMultiplier(warrior, target, spellInfo) * GetMercilessMultiplier(warrior, target, spellInfo)
            * GetRampageStrikeMultiplier(warrior, spellInfo);
        if (multiplier != 1.0f)
            damage = int32(std::lround(damage * multiplier));
    }

    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage)
    {
        if (!damage || !target || !attacker || !attacker->IsPlayer())
            return;

        // Colossus Smash, S3 Merciless (D18).
        float const multiplier = GetColossusSmashMultiplier(attacker, target, nullptr)
            * GetMercilessMultiplier(attacker, target, nullptr);
        if (multiplier != 1.0f)
            damage = uint32(std::lround(damage * multiplier));
    }

    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage, SpellInfo const* spellInfo)
    {
        // The periodic heal path calls this hook too: positive spells pass through untouched.
        if (!damage || !target || !attacker || !spellInfo || !attacker->IsPlayer() || spellInfo->IsPositive())
            return;

        // Colossus Smash, S3 Merciless (D18: per tick, at the target's health then).
        float const multiplier = GetColossusSmashMultiplier(attacker, target, spellInfo)
            * GetMercilessMultiplier(attacker, target, spellInfo);
        if (multiplier != 1.0f)
            damage = uint32(std::lround(damage * multiplier));
    }

    void OnPeriodicDamageFinal(Unit* target, Unit* attacker, uint32 damage, SpellInfo const* spellInfo,
        bool /*isCrit*/)
    {
        // Second Wind (D18) on Rend ticks; the Deep Wounds tick is a direct spell (OnSpellDamageTakenFinal).
        if (!damage || !target || !attacker || !spellInfo || spellInfo->Id != WarriorData::SPELL_REND)
            return;

        if (Player* warrior = attacker->ToPlayer())
        {
            OnBleedTick(warrior, target, spellInfo, damage);
            // Keeps the finite Blood Frenzy debuff up while Rend ticks (refreshes only when it runs low).
            UpdateBloodFrenzy(warrior, target);
        }
    }

    float GetColossusSmashMultiplier(Unit const* attacker, Unit const* target, SpellInfo const* spellInfo)
    {
        if (!attacker || !target)
            return 1.0f;

        // The button's own hit (its debuff lands before its damage) and stored shares of hits that already carried
        // the bonus (Seismic echo, Bloodstorm tick). The Thunder Clap echo is not a share and keeps it.
        if (spellInfo && (spellInfo->Id == WarriorData::SPELL_COLOSSUS_SMASH || IsStoredShare(spellInfo)))
            return 1.0f;

        // Per caster: only this attacker's own debuff counts (one instance per caster, DOT_STACKING_RULE).
        if (!target->HasAura(WarriorData::SPELL_COLOSSUS_SMASH_DEBUFF, attacker->GetGUID()))
            return 1.0f;

        // Q7: Mastery only with the Colossus Smash talent (its castable rank 204490); Avatar / Weight of the Earth
        // debuffs without it are the flat 15%.
        float pct = COLOSSUS_SMASH_PCT;
        if (Player const* warrior = attacker->ToPlayer())
            if (warrior->HasSpell(WarriorData::SPELL_COLOSSUS_SMASH))
                pct += warrior->GetMasteryPercentage();

        return 1.0f + pct / 100.0f;
    }

    void ApplyColossusSmash(Player* warrior, Unit* target)
    {
        if (!warrior || !target || target == warrior || !target->IsAlive())
            return;

        // The debuff id, never the button (150% damage and a greyed button, bug log :3267).
        warrior->CastSpell(target, WarriorData::SPELL_COLOSSUS_SMASH_DEBUFF, TRIGGERED_FULL_MASK);
    }

    float GetExploiterMultiplier(Unit const* attacker, Unit const* target, SpellInfo const* spellInfo)
    {
        if (!attacker || !target || !spellInfo || spellInfo->Id != WarriorData::SPELL_MORTAL_STRIKE)
            return 1.0f;

        Aura const* debuff = target->GetAura(WarriorData::SPELL_EXPLOITER_DEBUFF, attacker->GetGUID());
        if (!debuff)
            return 1.0f;

        int32 const pctPerStack = GetRankCarrier(attacker, { WarriorData::SPELL_EXPLOITER_204532,
            WarriorData::SPELL_EXPLOITER }, EFFECT_0);
        if (pctPerStack <= 0)
            return 1.0f;

        // Stacks add (D15): 1 + rank% x stacks / 100.
        return 1.0f + float(pctPerStack) * float(debuff->GetStackAmount()) / 100.0f;
    }

    std::vector<Unit*> SelectSweepingTargets(Player* warrior, Unit* mainTarget)
    {
        std::vector<Unit*> picked;
        if (!warrior || !mainTarget || !mainTarget->IsInWorld())
            return picked;

        // P0 shape (custom_wr_p0_spike.cpp SelectSweepTargets, PASSED): alive, attackable, already engaged with the
        // warrior or the group (never pulls), nearest to the main target first.
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(mainTarget, warrior, SWEEPING_STRIKES_RADIUS_YD);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(mainTarget, nearby, check);
        Cell::VisitObjects(mainTarget, searcher, SWEEPING_STRIKES_RADIUS_YD);

        for (Unit* unit : nearby)
            if (unit != mainTarget && unit != warrior && unit->IsAlive() && warrior->IsValidAttackTarget(unit)
                && Engagement::IsEngagedWithOwnerOrGroup(unit, warrior))
                picked.push_back(unit);

        std::sort(picked.begin(), picked.end(), [mainTarget](Unit const* a, Unit const* b)
        {
            return mainTarget->GetExactDist2dSq(a) < mainTarget->GetExactDist2dSq(b);
        });

        if (picked.size() > SWEEPING_STRIKES_MAX_TARGETS)
            picked.resize(SWEEPING_STRIKES_MAX_TARGETS);

        return picked;
    }

    void CastSweepingCopies(Player* warrior, Unit* mainTarget, SpellInfo const* spellInfo)
    {
        if (!warrior || !mainTarget || !spellInfo)
            return;

        // Erased before any copy is cast: the copies re-enter the damage hooks inside this call.
        int32 const share = TakeSweepingShare(warrior, spellInfo->Id, mainTarget->GetGUID());
        if (share <= 0)
            return;

        bool const smashCopy = spellInfo->Id == WarriorData::SPELL_COLOSSUS_SMASH;
        for (Unit* unit : SelectSweepingTargets(warrior, mainTarget))
        {
            // A SPELLVALUE base point is the final amount (Spell::SetSpellValue): the share as captured. The copy rolls
            // its own crit; its crit starts Deep Wounds in OnSpellDamageTakenFinal.
            warrior->CastCustomSpell(WarriorData::SPELL_SWEEPING_STRIKES_COPY, SPELLVALUE_BASE_POINT0, share, unit,
                TRIGGERED_FULL_MASK);

            // A copy of a Colossus Smash hit puts the debuff on its target after the copy's own damage.
            if (smashCopy)
                ApplyColossusSmash(warrior, unit);
        }
    }

    void ApplyDeepWounds(Player* warrior, Unit* target, WeaponAttackType attType)
    {
        // Players only: the stock ranks are also cast by NPCs (C6); the AuraScript returns early for them too.
        if (!warrior || !target || target == warrior || !target->IsAlive())
            return;

        // R17: rank carrier on effect 1 (bp 10/21/32, value 11/22/33%).
        int32 const rankPct = GetRankCarrier(warrior, { WarriorData::SPELL_DEEP_WOUNDS_12867,
            WarriorData::SPELL_DEEP_WOUNDS_12849, WarriorData::SPELL_DEEP_WOUNDS }, EFFECT_1);
        if (rankPct <= 0)
            return;

        // An off-hand proc reads the off-hand weapon; anything without one reads the main hand.
        if (attType != OFF_ATTACK || !warrior->HasOffhandWeaponForAttack())
            attType = BASE_ATTACK;

        // Q6 basis: the weapon's own damage range (the item's, before any percent done mod: never
        // UNIT_FIELD_MIN/MAXDAMAGE, which carry aura 79) + AP x unhasted weapon speed / 14. No Versatility.
        float const averageWeapon = (warrior->GetWeaponDamageRange(attType, MINDAMAGE)
            + warrior->GetWeaponDamageRange(attType, MAXDAMAGE)) / 2.0f;
        float const speedSeconds = warrior->GetAttackTime(attType) / 1000.0f;
        float const basis = averageWeapon
            + warrior->GetTotalAttackPowerValue(attType) * speedSeconds / DEEP_WOUNDS_AP_PER_SPEED_DIVISOR;

        // D21: Trauma's DUMMY carrier 15/30%.
        int32 const traumaPct = GetRankCarrier(warrior, { WarriorData::SPELL_TRAUMA_46855, WarriorData::SPELL_TRAUMA },
            EFFECT_0);

        float total = basis * float(rankPct) / 100.0f * (1.0f + float(std::max(traumaPct, 0)) / 100.0f);
        // S3 D34 (Q4): an application while Enraged carries the Enrage bonus (the tick ignores caster modifiers).
        if (IsEnraged(warrior))
            total *= 1.0f + GetEnrageBonusPct(warrior) / 100.0f;
        if (total < 1.0f)
            return;

        ApplyPercentBleed(warrior, target, WarriorData::SPELL_DEEP_WOUNDS_HOLDER, uint32(total), true);
        // The holder's AuraScript handles a new holder; a refresh keeps the finite Blood Frenzy debuff up here.
        UpdateBloodFrenzy(warrior, target);
    }

    void OnMortalStrikeHit(Player* warrior, Unit* target)
    {
        if (!warrior || !target)
            return;

        // (1) Colossus Smash -2 s (D3), real time, deferred past Mortal Strike's GCD and SendSpellCooldown.
        if (SpellInfo const* mortalStrike = sSpellMgr->GetSpellInfo(WarriorData::SPELL_MORTAL_STRIKE))
            ReduceCooldown(warrior, WarriorData::SPELL_COLOSSUS_SMASH, COLOSSUS_SMASH_MORTAL_STRIKE_CUT, 0ms,
                GcdSafeDelayMs(mortalStrike));

        // (2) Taste for Blood capstone (D6): 50% (x Proc Chance) for one Overpower charge.
        if (warrior->HasAura(WarriorData::SPELL_TASTE_FOR_BLOOD_56638)
            && RollProcChance(warrior, TASTE_FOR_BLOOD_CAPSTONE_PCT))
            warrior->CastSpell(warrior, WarriorData::SPELL_OVERPOWER_204403, TRIGGERED_FULL_MASK);

        // (3) Juggernaut (D13): the visible half makes this Mortal Strike apply Rend (a normal application, the Rend
        // talents apply), then it is consumed. The hidden Slam crit half (204500) is independent.
        if (warrior->HasAura(WarriorData::SPELL_JUGGERNAUT_BUFF))
        {
            if (target->IsAlive())
                warrior->CastSpell(target, WarriorData::SPELL_REND, TRIGGERED_FULL_MASK);

            warrior->RemoveAurasDueToSpell(WarriorData::SPELL_JUGGERNAUT_BUFF);
        }

        // (4) Exploiter (D15): this caster's debuff on the target is spent.
        target->RemoveAurasDueToSpell(WarriorData::SPELL_EXPLOITER_DEBUFF, warrior->GetGUID());

        // (5) Strength of Arms (D14) and (6) the Endless Rage overflow buff (D11): consumed by this hit (removal in
        // AfterHit, so this hit and its Sweeping copies, cast earlier in the same hit, carry them).
        warrior->RemoveAurasDueToSpell(WarriorData::SPELL_STRENGTH_OF_ARMS_BUFF_R1);
        warrior->RemoveAurasDueToSpell(WarriorData::SPELL_STRENGTH_OF_ARMS_BUFF_R2);
        warrior->RemoveAurasDueToSpell(WarriorData::SPELL_ENDLESS_RAGE_OVERFLOW);
    }

    uint32 OwnGcdRemainingMs(Player* warrior, uint32 spellId)
    {
        // How long until spellId's own GCD sweep has ended (+ the margin); 0 when the spell is not on cooldown or its
        // GCD is over. The client drops only the GCD stored in the cleared spell's own record, so another spell's
        // running GCD needs no wait (S1-CODE-REVIEW M1). The entry's cast start is end - maxduration: exact for a
        // spell whose base gets no Cooldown Haste correction (Shield Slam, Mortal Strike: 6 s) and whose end nothing
        // else moves. The sweep is the GCD the cast really got (S2 fix pass m3), not the unhasted StartRecoveryTime.
        if (!warrior)
            return 0;

        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
        if (!spellInfo || !spellInfo->StartRecoveryCategory || !spellInfo->StartRecoveryTime)
            return 0;

        SpellCooldowns const& cooldowns = warrior->GetSpellCooldownMap();
        auto const itr = cooldowns.find(spellId);
        if (itr == cooldowns.end() || itr->second.end < itr->second.maxduration)
            return 0;

        // The unhasted StartRecoveryTime bounds the sweep from above; the GCD the cast really got (flat GLOBAL_COOLDOWN
        // mods, spell haste: Spell::TriggerGlobalCooldown) is what the player's GCD list holds. A running GCD entry is
        // this spell's own while the bounded sweep runs: another GCD cast cannot start inside it. If the list says the
        // GCD is over, so is the sweep (the margin is dropped then).
        uint32 const castStartMs = itr->second.end - itr->second.maxduration;
        uint32 const boundEndMs = castStartMs + spellInfo->StartRecoveryTime + GCD_SAFE_MARGIN_MS;
        uint32 const now = NowMs();
        if (boundEndMs <= now)
            return 0;

        uint32 const gcdLeftMs = warrior->GetGlobalCooldownMgr().GetGlobalCooldown(spellInfo);
        return gcdLeftMs ? std::min(boundEndMs - now, gcdLeftMs + GCD_SAFE_MARGIN_MS) : 0;
    }

    void ResetMortalStrike(Player* warrior)
    {
        if (!warrior || !warrior->HasSpellCooldown(WarriorData::SPELL_MORTAL_STRIKE))
            return;

        // D9: while Mortal Strike's own GCD sweep still runs (a white crit right after it), once to its end + 100 ms;
        // never on the GCD category (S1-FIX M1). The event list dies with the player.
        if (uint32 const waitMs = OwnGcdRemainingMs(warrior, WarriorData::SPELL_MORTAL_STRIKE))
        {
            warrior->m_Events.AddEventAtOffset([warrior]()
            {
                warrior->RemoveSpellCooldown(WarriorData::SPELL_MORTAL_STRIKE, true);
            }, Milliseconds(waitMs));
            return;
        }

        warrior->RemoveSpellCooldown(WarriorData::SPELL_MORTAL_STRIKE, true);
    }

    void RollOncePerCastMeleeProcs(Player* warrior, Unit* firstTarget)
    {
        if (!warrior)
            return;

        // R4: did any of this whirl's targets crit (stamped in this update by OnSpellDamageTakenFinal)? Cleared here.
        bool anyCrit = false;
        if (WhirlCritStamp* stamp = warrior->CustomData.Get<WhirlCritStamp>(WHIRL_CRIT_KEY))
        {
            anyCrit = stamp->crit && stamp->ms == NowMs();
            stamp->crit = false;
        }

        if (!firstTarget)
            return;

        // (1) Sudden Death (D9, R11): the talent aura's own roll and proc cooldown, shared with its data proc.
        for (uint32 const rankId : { WarriorData::SPELL_SUDDEN_DEATH_29724, WarriorData::SPELL_SUDDEN_DEATH_29725,
            WarriorData::SPELL_SUDDEN_DEATH })
        {
            if (Aura* aura = warrior->GetAura(rankId))
            {
                if (RollTalentProcByHand(warrior, aura))
                    ResetMortalStrike(warrior);
                break;
            }
        }

        // (2) Wrecking Crew (D22): a crit on any target grants the held rank's buff (no proc row roll: the stock
        // row is crit-only at 100%).
        if (anyCrit)
        {
            uint32 buffId = 0;
            if (warrior->HasAura(WarriorData::SPELL_WRECKING_CREW_56612))
                buffId = WarriorData::SPELL_WRECKING_CREW_BUFF_R3;
            else if (warrior->HasAura(WarriorData::SPELL_WRECKING_CREW_56611))
                buffId = WarriorData::SPELL_WRECKING_CREW_BUFF_R2;
            else if (warrior->HasAura(WarriorData::SPELL_WRECKING_CREW))
                buffId = WarriorData::SPELL_WRECKING_CREW_BUFF_R1;

            if (buffId)
                warrior->CastSpell(warrior, buffId, TRIGGERED_FULL_MASK);
        }

        // (3) The sword strike (D17): the held sword passive's own chance and 3 s proc cooldown, main hand a sword.
        Item const* mainHand = warrior->GetWeaponForAttack(BASE_ATTACK, true);
        uint32 const mainHandSubclass = mainHand ? mainHand->GetTemplate()->SubClass : 0;
        if (mainHandSubclass != ITEM_SUBCLASS_WEAPON_SWORD && mainHandSubclass != ITEM_SUBCLASS_WEAPON_SWORD2)
            return;

        for (uint32 const passiveId : { WarriorData::SPELL_WEAPON_SPECIALIZATION_SWORD_R3,
            WarriorData::SPELL_WEAPON_SPECIALIZATION_SWORD_R2, WarriorData::SPELL_WEAPON_SPECIALIZATION_SWORD_R1 })
        {
            if (Aura* aura = warrior->GetAura(passiveId))
            {
                if (firstTarget->IsAlive() && RollTalentProcByHand(warrior, aura))
                    warrior->CastSpell(firstTarget, WarriorData::SPELL_WEAPON_SPECIALIZATION_STRIKE,
                        TRIGGERED_FULL_MASK);
                break;
            }
        }
    }

    void RecordWhirlwindHit(Player* warrior, Unit* target, int32 damage)
    {
        if (!warrior || !target || damage <= 0)
            return;

        // Only with Seismic Reverberation (D19): no stash, no event otherwise.
        if (GetRankCarrier(warrior, { WarriorData::SPELL_SEISMIC_REVERBERATION_204539,
            WarriorData::SPELL_SEISMIC_REVERBERATION }, EFFECT_0) <= 0)
            return;

        warrior->CustomData.GetDefault<SeismicState>(SEISMIC_KEY)->sums[target->GetGUID()] += damage;
    }

    void ScheduleSeismicEcho(Player* warrior)
    {
        if (!warrior || GetRankCarrier(warrior, { WarriorData::SPELL_SEISMIC_REVERBERATION_204539,
            WarriorData::SPELL_SEISMIC_REVERBERATION }, EFFECT_0) <= 0)
            return;

        // The event list dies with the player.
        warrior->m_Events.AddEventAtOffset([warrior]()
        {
            FireSeismicEcho(warrior);
        }, SEISMIC_ECHO_DELAY);
    }

    void OnRageOverflow(Unit* unit, int32 overflowPower)
    {
        // The core line runs for every unit's rage that did not fit: players holding the capstone rank only.
        if (overflowPower <= 0 || !unit)
            return;

        Player* warrior = unit->ToPlayer();
        if (!warrior || !warrior->HasAura(WarriorData::SPELL_ENDLESS_RAGE_204544))
            return;

        // Power units are tenths of a rage point; the fraction carries to the next overflow.
        RageOverflowCarry* carry = warrior->CustomData.GetDefault<RageOverflowCarry>(RAGE_OVERFLOW_KEY);
        int32 const total = carry->remainder + overflowPower;
        int32 const points = total / 10;
        carry->remainder = total % 10;
        if (points <= 0)
            return;

        // One stack per whole point (CumulativeAura caps at 20); every grant restarts the 20 s, at the cap too
        // (Aura::ModStackAmount, 0-verify B item 11).
        Aura* aura = warrior->GetAura(WarriorData::SPELL_ENDLESS_RAGE_OVERFLOW, warrior->GetGUID());
        int32 stacksToAdd = points;
        if (!aura)
        {
            warrior->CastSpell(warrior, WarriorData::SPELL_ENDLESS_RAGE_OVERFLOW, TRIGGERED_FULL_MASK);
            aura = warrior->GetAura(WarriorData::SPELL_ENDLESS_RAGE_OVERFLOW, warrior->GetGUID());
            --stacksToAdd;
        }

        if (aura && stacksToAdd > 0)
            aura->ModStackAmount(stacksToAdd);
    }

    void OnBleedTick(Player* warrior, Unit* /*target*/, SpellInfo const* tickSpell, uint32 damage)
    {
        if (!warrior || !tickSpell || !damage || !warrior->IsAlive())
            return;

        // Rend ticks and the Deep Wounds tick only (D18).
        if (tickSpell->Id != WarriorData::SPELL_REND && tickSpell->Id != WarriorData::SPELL_DEEP_WOUNDS_TICK)
            return;

        int32 const healPct = GetRankCarrier(warrior, { WarriorData::SPELL_SECOND_WIND_29838,
            WarriorData::SPELL_SECOND_WIND }, EFFECT_0);
        if (healPct <= 0)
            return;

        float heal = float(damage) * float(healPct) / 100.0f;
        if (warrior->HealthBelowPct(SECOND_WIND_LOW_HEALTH_PCT))
            heal *= 2.0f;

        // A SPELLVALUE base point is the final amount (Spell::SetSpellValue); healing modifiers still apply.
        int32 const amount = int32(std::lround(heal));
        if (amount > 0)
            warrior->CastCustomSpell(WarriorData::SPELL_SECOND_WIND_HEAL, SPELLVALUE_BASE_POINT0, amount, warrior,
                TRIGGERED_FULL_MASK);
    }

    void UpdateBloodFrenzy(Player* warrior, Unit* target)
    {
        if (!warrior || !target)
            return;

        ObjectGuid const guid = warrior->GetGUID();

        // The held rank's debuff (2/4%); none when the talent is gone (its debuffs are then removed below).
        uint32 debuffId = 0;
        if (warrior->HasAura(WarriorData::SPELL_BLOOD_FRENZY_29859))
            debuffId = WarriorData::SPELL_BLOOD_FRENZY_DEBUFF_R2;
        else if (warrior->HasAura(WarriorData::SPELL_BLOOD_FRENZY))
            debuffId = WarriorData::SPELL_BLOOD_FRENZY_DEBUFF_R1;

        // AfterEffectRemove runs once the aura has left the target's applied list, so a bleed ending reads absent.
        bool const bleeding = target->IsAlive() && (target->HasAura(WarriorData::SPELL_REND, guid)
            || target->HasAura(WarriorData::SPELL_DEEP_WOUNDS_HOLDER, guid));

        for (uint32 const id : { WarriorData::SPELL_BLOOD_FRENZY_DEBUFF_R1, WarriorData::SPELL_BLOOD_FRENZY_DEBUFF_R2 })
            if ((!bleeding || id != debuffId) && target->HasAura(id, guid))
                target->RemoveAurasDueToSpell(id, guid);

        if (!bleeding || !debuffId)
            return;

        // The debuff has a finite duration (finding 8: never orphaned when the caster is gone); re-cast while a bleed
        // is up, only when absent or running low (Rend ticks call this every tick). spell_group 1108
        // (EXCLUSIVE_HIGHEST) keeps the strongest when several warriors bleed the target.
        Aura const* debuff = target->GetAura(debuffId, guid);
        if (!debuff || (debuff->GetDuration() >= 0 && debuff->GetDuration() < BLOOD_FRENZY_REFRESH_BELOW_MS))
            warrior->CastSpell(target, debuffId, TRIGGERED_FULL_MASK);
    }

    void GrantJuggernaut(Player* warrior)
    {
        if (!warrior || !warrior->IsAlive())
            return;

        // D13: rank carrier on effect 1 (bp 49/99, value 50/100%).
        int32 const chancePct = GetRankCarrier(warrior, { WarriorData::SPELL_JUGGERNAUT_204543,
            WarriorData::SPELL_JUGGERNAUT }, EFFECT_1);
        if (chancePct <= 0 || !RollProcChance(warrior, float(chancePct)))
            return;

        // The visible half (Mortal Strike applies Rend) and the hidden one-charge Slam crit.
        warrior->CastSpell(warrior, WarriorData::SPELL_JUGGERNAUT_BUFF, TRIGGERED_FULL_MASK);
        warrior->CastSpell(warrior, WarriorData::SPELL_JUGGERNAUT_CRIT, TRIGGERED_FULL_MASK);
    }

    void GrantAngerManagementCapstone(Player* warrior)
    {
        if (warrior && warrior->IsAlive() && warrior->HasAura(WarriorData::SPELL_ANGER_MANAGEMENT_204542))
            warrior->CastSpell(warrior, WarriorData::SPELL_ANGER_MANAGEMENT_CAPSTONE, TRIGGERED_FULL_MASK);
    }

    void UpdateWeaponSpecialization(Player* warrior)
    {
        if (!warrior)
            return;

        // The nine hidden passives by weapon kind (axe/polearm, mace, sword) and learned rank (1-3).
        static constexpr std::array<std::array<uint32, 3>, 3> passives = {{
            { WarriorData::SPELL_WEAPON_SPECIALIZATION_AXE_R1, WarriorData::SPELL_WEAPON_SPECIALIZATION_AXE_R2,
              WarriorData::SPELL_WEAPON_SPECIALIZATION_AXE_R3 },
            { WarriorData::SPELL_WEAPON_SPECIALIZATION_MACE_R1, WarriorData::SPELL_WEAPON_SPECIALIZATION_MACE_R2,
              WarriorData::SPELL_WEAPON_SPECIALIZATION_MACE_R3 },
            { WarriorData::SPELL_WEAPON_SPECIALIZATION_SWORD_R1, WarriorData::SPELL_WEAPON_SPECIALIZATION_SWORD_R2,
              WarriorData::SPELL_WEAPON_SPECIALIZATION_SWORD_R3 } }};

        // The learned rank: the talent's own passive DUMMY aura (a passive talent rank lives in m_talents only, so
        // HasSpell is false for it; the aura is also there after a Classless .learn).
        uint8 rank = 0;
        if (warrior->HasAura(WarriorData::SPELL_WEAPON_SPECIALIZATION_12813))
            rank = 3;
        else if (warrior->HasAura(WarriorData::SPELL_WEAPON_SPECIALIZATION_12812))
            rank = 2;
        else if (warrior->HasAura(WarriorData::SPELL_WEAPON_SPECIALIZATION))
            rank = 1;

        // Q3: the main hand only, as equipped (a broken or disarmed weapon keeps its bonus).
        int8 kind = -1;
        if (Item const* mainHand = warrior->GetWeaponForAttack(BASE_ATTACK, false))
        {
            switch (mainHand->GetTemplate()->SubClass)
            {
                case ITEM_SUBCLASS_WEAPON_AXE:
                case ITEM_SUBCLASS_WEAPON_AXE2:
                case ITEM_SUBCLASS_WEAPON_POLEARM:
                    kind = 0;
                    break;
                case ITEM_SUBCLASS_WEAPON_MACE:
                case ITEM_SUBCLASS_WEAPON_MACE2:
                    kind = 1;
                    break;
                case ITEM_SUBCLASS_WEAPON_SWORD:
                case ITEM_SUBCLASS_WEAPON_SWORD2:
                    kind = 2;
                    break;
                default:
                    break;
            }
        }

        uint32 const wanted = rank && kind >= 0 ? passives[kind][rank - 1] : 0;

        // Exactly one (or none) of the nine stays; safe to call repeatedly. A passive aura (0xC0) is not saved and
        // survives death; the login hook re-applies it.
        for (auto const& byRank : passives)
        {
            for (uint32 const passiveId : byRank)
            {
                if (passiveId == wanted)
                {
                    if (!warrior->HasAura(passiveId))
                        warrior->AddAura(passiveId, warrior);
                }
                else if (warrior->HasAura(passiveId))
                    warrior->RemoveAurasDueToSpell(passiveId);
            }
        }
    }

    void GrantStormsBulwark(Player* warrior, float pctOfMaxHealth, BulwarkSource source)
    {
        if (!warrior || !warrior->IsAlive() || pctOfMaxHealth <= 0.0f)
            return;

        // The capstone (rank 3) scales the add and the cap by 1 + Mastery; both read now (D5).
        float const masteryFactor = warrior->HasAura(WarriorData::SPELL_STORM_S_BULWARK_200060)
            ? 1.0f + warrior->GetMasteryPercentage() / 100.0f : 1.0f;
        float const maxHealth = float(warrior->GetMaxHealth());
        int32 const add = int32(maxHealth * pctOfMaxHealth / 100.0f * masteryFactor);
        int32 const cap = int32(maxHealth * STORMS_BULWARK_CAP_PCT / 100.0f * masteryFactor);

        Aura* aura = warrior->GetAura(WarriorData::SPELL_STORM_S_BULWARK, warrior->GetGUID());
        AuraEffect* effect = aura ? aura->GetEffect(EFFECT_0) : nullptr;
        int32 const current = effect ? std::max(effect->GetAmount(), 0) : 0;

        // Never lowers: a cap that fell (max health dropped after Last Stand) does not trim the shield.
        int32 const amount = std::max(current, std::min(current + add, cap));
        if (amount <= 0)
            return;

        if (!effect)
        {
            // A new shield (15 s from the row); a SPELLVALUE base point is the final amount (SetSpellValue).
            warrior->CastCustomSpell(WarriorData::SPELL_STORM_S_BULWARK, SPELLVALUE_BASE_POINT0, amount, warrior,
                true);
            return;
        }

        if (amount != current)
            effect->SetAmount(amount);

        if (source != BulwarkSource::Incite)
            aura->RefreshDuration();
    }

    void RecordThunderClapBulwarkPct(Player* warrior, float unamplifiedPct)
    {
        if (!warrior)
            return;

        warrior->CustomData.GetDefault<ThunderClapBulwarkRecord>(THUNDER_CLAP_BULWARK_KEY)->unamplifiedPct =
            std::max(unamplifiedPct, 0.0f);
    }

    float GetRecordedThunderClapBulwarkPct(Player const* warrior)
    {
        if (!warrior)
            return 0.0f;

        ThunderClapBulwarkRecord const* record =
            warrior->CustomData.Get<ThunderClapBulwarkRecord>(THUNDER_CLAP_BULWARK_KEY);
        return record ? record->unamplifiedPct : 0.0f;
    }

    void RollSwordAndBoard(Player* warrior, uint32 deferMs)
    {
        if (!warrior)
            return;

        int32 const chancePct = GetRankCarrier(warrior, { WarriorData::SPELL_SWORD_AND_BOARD_46953,
            WarriorData::SPELL_SWORD_AND_BOARD_46952, WarriorData::SPELL_SWORD_AND_BOARD }, EFFECT_0);
        if (chancePct <= 0 || !RollProcChance(warrior, float(chancePct)))
            return;

        // Deferred (D13): the triggering cast's SendSpellCooldown would overwrite a reset of its own cooldown, a
        // clear during its GCD wipes the client's sweep (bug log CDH-GCD-FIX), and a Shield Slam in flight must not
        // eat the new charge. The event list dies with the player.
        warrior->m_Events.AddEventAtOffset([warrior]()
        {
            GrantSwordAndBoard(warrior, true);
        }, Milliseconds(std::max<uint32>(deferMs, 1)));
    }

    void ReduceCooldown(Player* warrior, uint32 spellId, Milliseconds amount, Milliseconds floorEnd, uint32 deferMs)
    {
        if (!warrior || amount <= 0ms)
            return;

        if (deferMs)
        {
            warrior->m_Events.AddEventAtOffset([warrior, spellId, amount, floorEnd]()
            {
                ReduceCooldown(warrior, spellId, amount, floorEnd, 0);
            }, Milliseconds(deferMs));
            return;
        }

        // A cut resends the entry (clear-then-set), and the client drops the GCD stored in the spell's own record: a
        // cut landing inside the spell's own GCD wipes every button's sweep (a Mortal Strike cut deferred past its
        // GCD lands just after a queued Colossus Smash, playtest 2026-10-30). Wait for that GCD's end + 100 ms.
        if (uint32 const waitMs = OwnGcdRemainingMs(warrior, spellId))
        {
            warrior->m_Events.AddEventAtOffset([warrior, spellId, amount, floorEnd]()
            {
                ReduceCooldown(warrior, spellId, amount, floorEnd, 0);
            }, Milliseconds(waitMs));
            return;
        }

        SpellCooldowns const& cooldowns = warrior->GetSpellCooldownMap();
        auto const itr = cooldowns.find(spellId);
        if (itr == cooldowns.end())
            return;

        // Never shorten a "cooldown starts on event" hold (bug log: it would show the button ready on the client).
        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
        if (!spellInfo || spellInfo->IsCooldownStartedOnEvent())
            return;

        uint32 const end = itr->second.end;
        uint32 const now = NowMs();
        if (end <= now)
            return;

        // Never past the remainder (an entry ending now is cleared by the resend) nor below the floor.
        int64 cut = std::min<int64>(amount.count(), int64(end - now));
        if (floorEnd > 0ms)
        {
            if (int64(end) <= floorEnd.count())
                return;

            cut = std::min<int64>(cut, int64(end) - floorEnd.count());
        }

        // ModifySpellCooldown resends the entry to the client (clear-then-set, PLAN A8).
        if (cut > 0)
            warrior->ModifySpellCooldown(spellId, -int32(cut));
    }

    void RecordLastStandCast(Player* warrior, Milliseconds hastedCooldownLength)
    {
        if (!warrior || hastedCooldownLength <= 0ms)
            return;

        uint32 const now = NowMs();

        std::lock_guard<std::mutex> lock(lastStandCastLock);

        // A record whose floor has passed can no longer clamp anything: the map only holds live windows.
        for (auto itr = lastStandCastByPlayer.begin(); itr != lastStandCastByPlayer.end();)
        {
            if (now >= LastStandFloorEndMs(itr->second))
                itr = lastStandCastByPlayer.erase(itr);
            else
                ++itr;
        }

        lastStandCastByPlayer[warrior->GetGUID()] = { now, uint32(hastedCooldownLength.count()) };
    }

    Milliseconds GetLastStandFloorEnd(Player const* warrior)
    {
        if (!warrior)
            return 0ms;

        std::lock_guard<std::mutex> lock(lastStandCastLock);
        auto const itr = lastStandCastByPlayer.find(warrior->GetGUID());
        return itr != lastStandCastByPlayer.end() ? Milliseconds(LastStandFloorEndMs(itr->second)) : 0ms;
    }

    void ApplyPercentBleed(Player* warrior, Unit* target, uint32 holderId, uint32 totalDamage, bool accumulate)
    {
        if (!warrior || !target || !holderId || !totalDamage || !target->IsAlive())
            return;

        SpellInfo const* holderInfo = sSpellMgr->GetSpellInfo(holderId);
        if (!holderInfo)
            return;

        int32 const amplitude = holderInfo->Effects[EFFECT_0].Amplitude;
        int32 const ticks = amplitude > 0 ? std::max<int32>(holderInfo->GetMaxDuration() / amplitude, 1) : 1;

        Aura* aura = target->GetAura(holderId, warrior->GetGUID());

        PercentBleedState* state = target->CustomData.GetDefault<PercentBleedState>(PERCENT_BLEED_KEY);
        uint32& perTick = state->perTick[{ warrior->GetGUID(), holderId }];
        if (accumulate && aura)
        {
            // S2 D5 ACCUMULATE (Rogue::ApplyStoredBleed): what the running bleed still owes plus the new share, spread
            // over a full duration. Without a running holder the stored amount is stale and counts as nothing.
            uint32 const ticksLeft = GetRemainingTicks(aura, amplitude);
            perTick = uint32((uint64(perTick) * ticksLeft + totalDamage) / uint64(ticks));
        }
        else
        {
            // REPLACE (S1 D7): the new share over a full duration; whatever the running bleed still owed is dropped.
            perTick = totalDamage / uint32(ticks);
        }

        if (!aura)
        {
            warrior->CastSpell(target, holderId, TRIGGERED_FULL_MASK);
            return;
        }

        // Full duration again, and the next tick one whole period away.
        aura->RefreshDuration();
        if (AuraEffect* effect = aura->GetEffect(EFFECT_0))
            effect->ResetPeriodic(true);
    }

    uint32 GetPercentBleedTick(Unit const* warrior, Unit const* target, uint32 holderId)
    {
        if (!warrior || !target)
            return 0;

        PercentBleedState const* state = target->CustomData.Get<PercentBleedState>(PERCENT_BLEED_KEY);
        if (!state)
            return 0;

        auto const itr = state->perTick.find({ warrior->GetGUID(), holderId });
        return itr != state->perTick.end() ? itr->second : 0;
    }

    // ---- S3: Fury (docs/reworks/warrior-fury-rework.md; S3 handoff D3-D34; WP brief R1-R7, 3b) ----

    bool IsEnraged(Unit const* unit)
    {
        return unit && unit->HasAura(WarriorData::SPELL_ENRAGE_BUFF);
    }

    void AddRagePaid(Player* warrior, int32 powerPaid)
    {
        // The dispatcher calls this for every rage-cost cast of any family: the rank test comes first. A passive
        // talent rank is an aura (never HasSpell).
        if (!warrior || powerPaid <= 0 || !HasEnrageRank(warrior))
            return;

        int32 const fillPower = int32(WarriorData::ENRAGE_METER_FILL) * POWER_PER_RAGE;
        if (fillPower <= 0)
            return;

        EnrageMeter* meter = warrior->CustomData.GetDefault<EnrageMeter>(ENRAGE_METER_KEY);
        meter->value += powerPaid;

        // Carry-over: rage past a fill stays on the meter. One Enrage per payment whatever it filled: inside Death
        // Wish a fill only refreshes the held Enrage and nothing is banked (Q18).
        if (meter->value >= fillPower)
        {
            meter->value %= fillPower;
            GrantEnrage(warrior);
        }

        SetEnrageMeterStacks(warrior, meter->value);
    }

    void ResetEnrageMeter(Player* warrior)
    {
        if (!warrior)
            return;

        warrior->CustomData.Erase(ENRAGE_METER_KEY);
        warrior->RemoveAurasDueToSpell(WarriorData::SPELL_ENRAGE_METER);
    }

    void GrantEnrage(Player* warrior)
    {
        // A cast, not AddAura: a refresh re-runs the AuraScript's amount hooks and restarts the 12 s (never stacks).
        if (warrior && warrior->IsAlive() && HasEnrageRank(warrior))
            warrior->CastSpell(warrior, WarriorData::SPELL_ENRAGE_BUFF, TRIGGERED_FULL_MASK);
    }

    float GetEnrageBonusPct(Player const* warrior)
    {
        if (!warrior)
            return 0.0f;

        // Talent 2..10 + Unshackled Fury 2/4/6 + Mastery with Unshackled Fury's capstone (rank 3).
        float pct = float(std::max(GetEnrageRankCarrier(warrior, EFFECT_0), 0));
        pct += float(std::max(GetRankCarrier(warrior, { WarriorData::SPELL_UNSHACKLED_FURY_204670,
            WarriorData::SPELL_UNSHACKLED_FURY_204669, WarriorData::SPELL_UNSHACKLED_FURY }, EFFECT_0), 0));
        if (warrior->HasAura(WarriorData::SPELL_UNSHACKLED_FURY_204670))
            pct += warrior->GetMasteryPercentage();

        // Death Wish scales the whole sum (D4).
        if (warrior->HasAura(WarriorData::SPELL_DEATH_WISH))
            pct *= DEATH_WISH_ENRAGE_FACTOR;

        return pct;
    }

    float GetEnrageHastePct(Player const* warrior)
    {
        // The talent rank's haste carrier only: neither Unshackled Fury, Mastery nor Death Wish raise it.
        return warrior ? float(std::max(GetEnrageRankCarrier(warrior, EFFECT_1), 0)) : 0.0f;
    }

    void RefreshEnrageAmount(Player* warrior)
    {
        if (!warrior)
            return;

        // CHANGE_AMOUNT re-handles the effect in place (no remove, no flicker); only when the sum moved.
        AuraEffect* effect = warrior->GetAuraEffect(WarriorData::SPELL_ENRAGE_BUFF, EFFECT_0);
        if (effect && effect->GetAmount() != GetEnrageBonusAmount(warrior))
            effect->RecalculateAmount();

        // The haste carrier only moves with a talent change; same rounded comparison as the AuraScript's.
        AuraEffect* haste = warrior->GetAuraEffect(WarriorData::SPELL_ENRAGE_BUFF, EFFECT_1);
        if (haste && haste->GetAmount() != int32(std::lround(GetEnrageHastePct(warrior))))
            haste->RecalculateAmount();
    }

    void HoldEnrage(Player* warrior)
    {
        if (!warrior)
            return;

        // D5 (P0 finding 5): back to the full duration on every Death Wish tick and at its end, whatever the meter.
        if (Aura* enrage = warrior->GetAura(WarriorData::SPELL_ENRAGE_BUFF, warrior->GetGUID()))
        {
            int32 const full = enrage->CalcMaxDuration();
            enrage->SetMaxDuration(full);
            enrage->SetDuration(full);
        }
    }

    void OnRecklessnessApply(Player* warrior)
    {
        if (!warrior || !warrior->IsAlive())
            return;

        // "Recklessness also Enrages you" (with an Enrage rank).
        GrantEnrage(warrior);

        // Merciless capstone (D18): Rampage costs no rage while Recklessness is up.
        if (warrior->HasAura(WarriorData::SPELL_MERCILESS_204658))
            warrior->AddAura(WarriorData::SPELL_MERCILESS_FREE_RAMPAGE, warrior);
    }

    void OnRecklessnessRemove(Player* warrior, uint8 removeMode)
    {
        if (!warrior)
            return;

        warrior->RemoveAurasDueToSpell(WarriorData::SPELL_MERCILESS_FREE_RAMPAGE);

        // D24: used up (DEFAULT: the last charge, incl. Rampage's DropCharge; EXPIRE: RemoveSpellMods' charge or the
        // duration's end). Never on cancel, death or an enemy dispel; never off the world (logout, map change).
        AuraRemoveMode const mode = AuraRemoveMode(removeMode);
        if (mode != AURA_REMOVE_BY_DEFAULT && mode != AURA_REMOVE_BY_EXPIRE)
            return;

        if (warrior->IsInWorld() && warrior->IsAlive() && warrior->HasAura(WarriorData::SPELL_WILL_OF_THE_BERSERKER))
            warrior->CastSpell(warrior, WarriorData::SPELL_WILL_OF_THE_BERSERKER_BUFF, TRIGGERED_FULL_MASK);
    }

    namespace
    {
        // PressChargeGuard: one spare charge on a live charged aura; returns the pre-bump count (0 = not bumped).
        uint8 BumpPressCharge(Player* warrior, uint32 spellId)
        {
            Aura* aura = warrior->GetAura(spellId, warrior->GetGUID());
            if (!aura || !aura->IsUsingCharges() || !aura->GetCharges() || aura->GetCharges() == UINT8_MAX)
                return 0;

            uint8 const before = aura->GetCharges();
            aura->SetCharges(before + 1);
            return before;
        }

        // Back to the pre-bump count when the child left the spare charge (it did not read the mod); a child that
        // spent it already left `before`. Never raises the count; the aura may be gone by now.
        void RestorePressCharge(Player* warrior, uint32 spellId, uint8 before)
        {
            if (!before)
                return;

            if (Aura* aura = warrior->GetAura(spellId, warrior->GetGUID()))
                if (aura->GetCharges() > before)
                    aura->SetCharges(before);
        }
    }

    PressChargeGuard::PressChargeGuard(Player* warrior) : _warrior(warrior)
    {
        if (!_warrior)
            return;

        _recklessnessCharges = BumpPressCharge(_warrior, WarriorData::SPELL_RECKLESSNESS);
        _bloodsurgeCharges = BumpPressCharge(_warrior, WarriorData::SPELL_BLOODSURGE_BUFF);
    }

    PressChargeGuard::~PressChargeGuard()
    {
        if (!_warrior)
            return;

        RestorePressCharge(_warrior, WarriorData::SPELL_RECKLESSNESS, _recklessnessCharges);
        RestorePressCharge(_warrior, WarriorData::SPELL_BLOODSURGE_BUFF, _bloodsurgeCharges);
    }

    bool IsStoredShare(SpellInfo const* spellInfo)
    {
        // Shares of hits that already carried every damage multiplier: never multiplied again.
        return spellInfo && (spellInfo->Id == WarriorData::SPELL_SEISMIC_REVERBERATION_ECHO
            || spellInfo->Id == WarriorData::SPELL_BLOODSTORM_TICK);
    }

    float GetMercilessMultiplier(Unit const* attacker, Unit const* target, SpellInfo const* spellInfo)
    {
        // Runs on every player hit: the stance test first (no aura lookup), then health, then the rank.
        if (!attacker || !target || attacker->GetShapeshiftForm() != FORM_BERSERKERSTANCE)
            return 1.0f;

        if (spellInfo && (spellInfo->IsPositive() || IsStoredShare(spellInfo)))
            return 1.0f;

        if (!target->HealthBelowPct(int32(WarriorData::MERCILESS_HEALTH_PCT)))
            return 1.0f;

        int32 pct = GetRankCarrier(attacker, { WarriorData::SPELL_MERCILESS_204658,
            WarriorData::SPELL_MERCILESS_204657, WarriorData::SPELL_MERCILESS }, EFFECT_0);
        if (pct <= 0)
            return 1.0f;

        if (IsEnraged(attacker))
            pct *= 2;

        return 1.0f + float(pct) / 100.0f;
    }

    void OnRampageCast(Player* warrior)
    {
        if (!warrior)
            return;

        // The press state (D7). The dispatcher's meter credit ran first, so a fill by this cast counts.
        RampageState* state = warrior->CustomData.GetDefault<RampageState>(RAMPAGE_KEY);
        state->enrageSnapPct = IsEnraged(warrior) ? float(std::lround(GetEnrageBonusPct(warrior))) : 0.0f;

        // Recklessness: exactly one charge (B-R1: the Rampage parent takes no Recklessness mod, this is its only
        // consumer) and the hidden crit snapshot for the four strikes. DEFAULT on the last charge gives Will of the
        // Berserker's buff (OnRecklessnessRemove).
        warrior->RemoveAurasDueToSpell(WarriorData::SPELL_RAMPAGE_SNAPSHOT);
        if (Aura* recklessness = warrior->GetAura(WarriorData::SPELL_RECKLESSNESS, warrior->GetGUID()))
        {
            warrior->AddAura(WarriorData::SPELL_RAMPAGE_SNAPSHOT, warrior);
            recklessness->DropCharge(AURA_REMOVE_BY_DEFAULT);
        }

        // D14: every Rampage consumes Blood Rush, also one made free by Merciless' capstone (only the first free
        // COST mod is applied, so the other would survive).
        warrior->RemoveAurasDueToSpell(WarriorData::SPELL_BLOOD_RUSH_BUFF);
    }

    void StartRampage(Player* warrior, Unit* target)
    {
        if (!warrior)
            return;

        // Will of the Berserker (D24): once per Rampage cast, real seconds; Recklessness is off the GCD (no defer).
        if (warrior->HasAura(WarriorData::SPELL_WILL_OF_THE_BERSERKER))
            ReduceCooldown(warrior, WarriorData::SPELL_RECKLESSNESS,
                Milliseconds(WarriorData::WILL_OF_THE_BERSERKER_CDR_MS));

        RampageState* state = warrior->CustomData.GetDefault<RampageState>(RAMPAGE_KEY);
        if (!target || target == warrior)
        {
            StopRampage(warrior, state);
            return;
        }

        state->running = true;
        ++state->sequence;
        state->target = target->GetGUID();

        // Main, off, main, off hand; strike 1 on the next update (outside the parent's spell-mod window).
        std::array<uint32, 4> const offsetsMs = { 0, uint32(WarriorData::RAMPAGE_STRIKE_2_MS),
            uint32(WarriorData::RAMPAGE_STRIKE_3_MS), uint32(WarriorData::RAMPAGE_STRIKE_4_MS) };
        uint32 const sequence = state->sequence;
        for (std::size_t i = 0; i < offsetsMs.size(); ++i)
        {
            std::size_t const count = offsetsMs.size();
            // The event list dies with the player, so the captured pointer never outlives it.
            warrior->m_Events.AddEventAtOffset([warrior, sequence, i, count]()
            {
                RampageStrike(warrior, sequence, i, count);
            }, Milliseconds(offsetsMs[i]));
        }
    }

    float GetRampageStrikeMultiplier(Player const* warrior, SpellInfo const* spellInfo)
    {
        if (!warrior || !spellInfo || (spellInfo->Id != WarriorData::SPELL_RAMPAGE_STRIKE_MH
            && spellInfo->Id != WarriorData::SPELL_RAMPAGE_STRIKE_OH))
            return 1.0f;

        RampageState const* state = warrior->CustomData.Get<RampageState>(RAMPAGE_KEY);
        if (!state)
            return 1.0f;

        // The strike damage already holds the live Enrage aura 79 (TOTAL_PCT): swap it for the press snapshot and
        // apply the snapshot a second time, (1 + snap)^2 / (1 + live).
        float const snap = state->enrageSnapPct / 100.0f;
        float live = 0.0f;
        if (AuraEffect const* effect = warrior->GetAuraEffect(WarriorData::SPELL_ENRAGE_BUFF, EFFECT_0))
            live = float(effect->GetAmount()) / 100.0f;

        if (snap <= 0.0f && live <= 0.0f)
            return 1.0f;

        return (1.0f + snap) * (1.0f + snap) / (1.0f + live);
    }

    void RefreshCritChargeBuffs(Player* warrior)
    {
        if (!warrior || !warrior->IsAlive())
            return;

        // The held rank's buff, cast again: a refresh restores the full charges (Aura::ModStackAmount).
        static constexpr std::array<std::pair<uint32, uint32>, 6> rankBuffs = {{
            { WarriorData::SPELL_FLURRY_12972, WarriorData::SPELL_FLURRY_BUFF_R3 },
            { WarriorData::SPELL_FLURRY_12971, WarriorData::SPELL_FLURRY_BUFF_R2 },
            { WarriorData::SPELL_FLURRY, WarriorData::SPELL_FLURRY_BUFF_R1 },
            { WarriorData::SPELL_SHREDDING_BLOWS_204675, WarriorData::SPELL_SHREDDING_BLOWS_BUFF_R3 },
            { WarriorData::SPELL_SHREDDING_BLOWS_204674, WarriorData::SPELL_SHREDDING_BLOWS_BUFF_R2 },
            { WarriorData::SPELL_SHREDDING_BLOWS, WarriorData::SPELL_SHREDDING_BLOWS_BUFF_R1 } }};

        // Highest held rank per talent (Flurry first three entries, Shredding Blows last three).
        for (std::size_t talent = 0; talent < rankBuffs.size(); talent += 3)
        {
            for (std::size_t i = talent; i < talent + 3; ++i)
            {
                if (warrior->HasAura(rankBuffs[i].first))
                {
                    warrior->CastSpell(warrior, rankBuffs[i].second, TRIGGERED_FULL_MASK);
                    break;
                }
            }
        }
    }

    float GetBloodthirstBleedMultiplier(Player const* warrior, Unit const* target)
    {
        if (!warrior || !target)
            return 1.0f;

        // Every bleed aura this warrior has on the target (Q15: any class's bleeds, e.g. a Classless Rupture).
        ObjectGuid const guid = warrior->GetGUID();
        int32 bleeds = 0;
        for (auto const& [spellId, application] : target->GetAppliedAuras())
        {
            Aura const* aura = application->GetBase();
            if (aura->GetCasterGUID() == guid
                && (aura->GetSpellInfo()->GetAllEffectsMechanicMask() & (1ULL << MECHANIC_BLEED)))
                ++bleeds;
        }

        if (!bleeds)
            return 1.0f;

        int32 const pct = std::min(bleeds * int32(WarriorData::BLOODTHIRST_BLEED_BONUS_PCT),
            int32(WarriorData::BLOODTHIRST_BLEED_BONUS_MAX_PCT));
        return 1.0f + float(pct) / 100.0f;
    }

    void OnBloodthirstHit(Player* warrior, Unit* /*target*/)
    {
        if (!warrior || !warrior->IsAlive())
            return;

        // (1) Rage (D9, D12): 10 + Improved Bloodthirst 3/6, through ModifyPower (Endless Rage sees the overflow).
        // Not an ENERGIZE effect on the caster (it would make the caster a second target).
        int32 const rage = int32(WarriorData::BLOODTHIRST_RAGE) + std::max(GetRankCarrier(warrior, {
            WarriorData::SPELL_IMPROVED_BLOODTHIRST_204667, WarriorData::SPELL_IMPROVED_BLOODTHIRST }, EFFECT_0), 0);
        if (rage > 0)
            warrior->EnergizeBySpell(warrior, WarriorData::SPELL_BLOODTHIRST, uint32(rage * POWER_PER_RAGE),
                POWER_RAGE);

        // (2) The next melee hit heals (C2: from AfterHit, so Bloodthirst's own HIT proc never eats it).
        warrior->CastSpell(warrior, WarriorData::SPELL_BLOODTHIRST_HEAL_BUFF, TRIGGERED_FULL_MASK);

        // (3) Blood Craze (D11): max health x per-mille / 1000, doubled while Enraged now. A SPELLVALUE base point
        // is the final amount; healing modifiers (Titan's Grip's -10%) still apply.
        int32 const perMille = GetRankCarrier(warrior, { WarriorData::SPELL_BLOOD_CRAZE_16492,
            WarriorData::SPELL_BLOOD_CRAZE_16489, WarriorData::SPELL_BLOOD_CRAZE }, EFFECT_0);
        if (perMille <= 0)
            return;

        float heal = float(warrior->GetMaxHealth()) * float(perMille) / 1000.0f;
        if (IsEnraged(warrior))
            heal *= 2.0f;

        int32 const amount = int32(std::lround(heal));
        if (amount > 0)
            warrior->CastCustomSpell(WarriorData::SPELL_BLOOD_CRAZE_HEAL, SPELLVALUE_BASE_POINT0, amount, warrior,
                TRIGGERED_FULL_MASK);
    }

    void ApplyFreshMeat(Player* warrior, Unit* target)
    {
        if (!warrior || !target || target == warrior || !target->IsAlive())
            return;

        // D10: the rank's health threshold carrier (90 / 80).
        int32 const thresholdPct = GetRankCarrier(warrior, { WarriorData::SPELL_FRESH_MEAT_204665,
            WarriorData::SPELL_FRESH_MEAT }, EFFECT_0);
        if (thresholdPct > 0 && target->HealthAbovePct(thresholdPct))
            warrior->AddAura(WarriorData::SPELL_FRESH_MEAT_CRIT, warrior);
    }

    float GetImprovedExecuteMultiplier(Player const* warrior, Unit const* target)
    {
        if (!warrior)
            return 1.0f;

        // D17: the rank carrier 8/16, doubled against a target below 20% at the hit.
        int32 pct = GetRankCarrier(warrior, { WarriorData::SPELL_IMPROVED_EXECUTE_20503,
            WarriorData::SPELL_IMPROVED_EXECUTE }, EFFECT_0);
        if (pct <= 0)
            return 1.0f;

        if (target && target->HealthBelowPct(int32(WarriorData::IMPROVED_EXECUTE_HEALTH_PCT)))
            pct *= 2;

        return 1.0f + float(pct) / 100.0f;
    }

    void OnExecuteHit(Player* warrior, Unit* target)
    {
        // The capstone (rank 2): one crit stack (3 max, refresh) per Execute on a target below 20%.
        if (warrior && target && warrior->IsAlive() && warrior->HasAura(WarriorData::SPELL_IMPROVED_EXECUTE_20503)
            && target->HealthBelowPct(int32(WarriorData::IMPROVED_EXECUTE_HEALTH_PCT)))
            warrior->CastSpell(warrior, WarriorData::SPELL_IMPROVED_EXECUTE_BUFF, TRIGGERED_FULL_MASK);
    }

    bool IsStrikeCast(SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return false;

        // S2's helper (spell_warrior_arms.cpp, unchanged there): a spell with a direct damage effect ...
        for (SpellEffectInfo const& effect : spellInfo->Effects)
        {
            switch (effect.Effect)
            {
                case SPELL_EFFECT_SCHOOL_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL:
                case SPELL_EFFECT_NORMALIZED_WEAPON_DMG:
                case SPELL_EFFECT_WEAPON_PERCENT_DAMAGE:
                    return true;
                default:
                    break;
            }
        }

        if (spellInfo->SpellFamilyName != SPELLFAMILY_WARRIOR)
            return false;

        // ... plus Execute (damage in 20647), the Heroic Leap button (damage in the landing) and, S3, the Rampage
        // cast (a DUMMY; the damage is in its strikes).
        return (spellInfo->SpellFamilyFlags[0] & EXECUTE_FAMILY_FLAG_0)
            || (spellInfo->SpellFamilyFlags[2] & (HEROIC_LEAP_FAMILY_FLAG_2 | RAMPAGE_FAMILY_FLAG_2));
    }

    void UpdateTitansGripPenalty(Player* warrior)
    {
        if (!warrior)
            return;

        // D31: only with a two-hander in the off hand (as equipped) and the Titan's Grip ability.
        Item const* offHand = warrior->GetItemByPos(INVENTORY_SLOT_BAG_0, EQUIPMENT_SLOT_OFFHAND);
        bool const penalised = warrior->CanTitanGrip() && offHand
            && offHand->GetTemplate()->InventoryType == INVTYPE_2HWEAPON;

        bool const present = warrior->HasAura(WarriorData::SPELL_TITANS_GRIP_PENALTY);
        if (penalised && !present)
            warrior->AddAura(WarriorData::SPELL_TITANS_GRIP_PENALTY, warrior);
        else if (!penalised && present)
            warrior->RemoveAurasDueToSpell(WarriorData::SPELL_TITANS_GRIP_PENALTY);
    }

    void UpdateTwoHandedWeaponMastery(Player* warrior)
    {
        if (!warrior)
            return;

        // D32: the gate AuraScript zeroes the three effects while an off-hand weapon is wielded; re-run it.
        for (uint32 const rankId : { WarriorData::SPELL_TWO_HANDED_WEAPON_MASTERY_204525,
            WarriorData::SPELL_TWO_HANDED_WEAPON_MASTERY })
            if (Aura* aura = warrior->GetAura(rankId))
                aura->RecalculateAmountOfEffects();
    }

    bool HasFrenziedBlowsCapstone(Player const* warrior)
    {
        return warrior && warrior->HasAura(WarriorData::SPELL_FRENZIED_BLOWS_204660);
    }

    void ReduceWhirlwindFromCleave(Player* warrior)
    {
        if (!warrior || !warrior->HasAura(WarriorData::SPELL_UNENDING_FURY_56930))
            return;

        // D21: real time, deferred past Cleave's GCD and SendSpellCooldown (Whirlwind is a GCD spell).
        if (SpellInfo const* cleave = sSpellMgr->GetSpellInfo(WarriorData::SPELL_CLEAVE))
            ReduceCooldown(warrior, WarriorData::SPELL_WHIRLWIND,
                Milliseconds(WarriorData::UNENDING_FURY_WHIRLWIND_CUT_MS), 0ms, GcdSafeDelayMs(cleave));
    }

    void OnPummelInterrupt(Player* warrior, Unit* target)
    {
        if (!warrior || !warrior->IsAlive() || !warrior->HasAura(WarriorData::SPELL_INTENSIFY_RAGE_56924))
            return;

        // D25: the silence on the interrupted caster, and the Bloodrage copy (never 2687 triggered: it would grey
        // the spellbook button for its full cooldown, bug log :3267).
        if (target && target != warrior && target->IsAlive())
            warrior->CastSpell(target, WarriorData::SPELL_INTENSIFY_RAGE_SILENCE, TRIGGERED_FULL_MASK);

        warrior->CastSpell(warrior, WarriorData::SPELL_INTENSIFY_RAGE_BLOODRAGE, TRIGGERED_FULL_MASK);
    }

    int32 GetCommandingPresenceAmount(Unit const* caster)
    {
        if (!caster)
            return 0;

        // D30: the rank markers (rank 2 full, rank 1 half).
        float rankFactor = 0.0f;
        if (caster->HasAura(WarriorData::SPELL_COMMANDING_PRESENCE_12857))
            rankFactor = 1.0f;
        else if (caster->HasAura(WarriorData::SPELL_COMMANDING_PRESENCE))
            rankFactor = 0.5f;

        if (rankFactor <= 0.0f)
            return 0;

        uint8 const level = std::min<uint8>(caster->GetLevel(), COMMANDING_PRESENCE_FULL_LEVEL);
        return int32(std::lround(float(WarriorData::COMMANDING_PRESENCE_AT_60) * float(level)
            / float(COMMANDING_PRESENCE_FULL_LEVEL) * rankFactor));
    }
}
