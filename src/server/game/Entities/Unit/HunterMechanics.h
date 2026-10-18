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

#ifndef __HUNTERMECHANICS_H
#define __HUNTERMECHANICS_H

#include "Define.h"
#include "Generated/HunterData.h"
#include "SharedDefines.h"
#include <array>
#include <cstdint>
#include <vector>

class AuraEffect;
class Guardian;
class ObjectGuid;
class Pet;
class Player;
class ProcEventInfo;
class Spell;
class SpellInfo;
class Unit;

/*
 * Hunter-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors WarlockMechanics.h's shape
 * (.agents/plans/hunter-rework/hunter-rework.SHARED.md §A5, §C4). Append-only: each later stage adds its
 * declarations together with their bodies and never retypes an existing signature. Stage T2 holds only the
 * T2 block; H0 adds the HunterData:: aliases (DSL-declared ids) and the H0 block.
 */
namespace Hunter
{
    // ---- T2 ----
    constexpr uint32 SPELL_REQUIRES_NO_AMMO = 46699;      // stock Thori'dal aura, granted to every player

    // Q5: two hunter stings (SPELL_SPECIFIC_STING) never exclude each other. Called from the one core line in
    // SpellInfo::IsAuraExclusiveBySpecificPerCasterWith. True when both a and b are hunter stings.
    bool StingsStack(SpellInfo const* a, SpellInfo const* b);

    // The player that owns `unit`: itself, or the owner/charmer of a pet, guardian or totem. nullptr otherwise.
    Player* GetOwningPlayer(Unit* unit);
    Player const* GetOwningPlayer(Unit const* unit);

    // Proc Chance for scripted rolls (PLAN §2): chance * (1 + owner Proc Chance / 100). A pet or guardian resolves
    // to its owner (warlock GetOwnerProcChanceMultiplier precedent). Non-player chains use multiplier 1.
    float GetProcChanceMultiplier(Unit const* unit);
    bool  RollProcChance(Unit const* unit, float baseChancePct);

    // Real-seconds, client-visible cooldown cut (Player::ModifySpellCooldown, druid A8); never scaled by
    // Cooldown Haste. No-op when the spell has no running cooldown.
    void  ReduceSpellCooldown(Player* player, uint32 spellId, uint32 ms);

    // Q32: worldserver.conf `Custom.Realm.Classless` (default 0), read once (function-local static).
    bool  IsClasslessRealm();

    // Grants 46699 silently (addSpell on an unknown spell, CastSpell when known but the aura is gone).
    void  EnsureNoAmmoAura(Player* player);

    // Logout cleanup; each later section adds its own Clear*State call here. Removal paths use find-only map
    // access (paladin CR5).
    void  ClearState(Player* player);

    // ---- H0 ----
    // DSL-declared ids the H0 code uses (stock ids the DSL never declares stay hand literals).
    constexpr uint32 SPELL_AUTO_SHOT = HunterData::SPELL_AUTO_SHOT;
    constexpr uint32 SPELL_QUICK_SHOTS = HunterData::SPELL_QUICK_SHOTS;
    constexpr uint32 SPELL_ASPECT_OF_THE_BEAST = HunterData::SPELL_ASPECT_OF_THE_BEAST;
    constexpr uint32 SPELL_ASPECT_OF_THE_MONKEY = HunterData::SPELL_ASPECT_OF_THE_MONKEY;
    constexpr uint32 SPELL_ASPECT_OF_THE_HAWK = HunterData::SPELL_ASPECT_OF_THE_HAWK;
    constexpr uint32 SPELL_ASPECT_OF_THE_VIPER = HunterData::SPELL_ASPECT_OF_THE_VIPER;
    constexpr uint32 SPELL_ASPECT_OF_THE_DRAGONHAWK = HunterData::SPELL_ASPECT_OF_THE_DRAGONHAWK;
    constexpr uint32 SPELL_KILL_COMMAND = HunterData::SPELL_KILL_COMMAND;
    constexpr uint32 SPELL_GLAIVE_TOSS = HunterData::SPELL_GLAIVE_TOSS;
    constexpr uint32 SPELL_ASPECT_OF_THE_DRAGONHAWK_EXPLOSION = HunterData::SPELL_ASPECT_OF_THE_DRAGONHAWK_EXPLOSION;
    constexpr uint32 SPELL_ASPECT_OF_THE_VIPER_POISON = HunterData::SPELL_ASPECT_OF_THE_VIPER_POISON;
    constexpr uint32 SPELL_ASPECT_OF_THE_BEAST_PET_BUFF = HunterData::SPELL_ASPECT_OF_THE_BEAST_PET_BUFF;
    constexpr uint32 SPELL_ASPECT_OF_THE_BEAST_MARKER = HunterData::SPELL_ASPECT_OF_THE_BEAST_MARKER;
    constexpr uint32 SPELL_ASPECT_OF_THE_MONKEY_VERSATILITY = HunterData::SPELL_ASPECT_OF_THE_MONKEY_VERSATILITY;
    constexpr uint32 SPELL_ASPECT_OF_THE_MONKEY_PET = HunterData::SPELL_ASPECT_OF_THE_MONKEY_PET;

    // Q14: does this spell roll the hunter's aspect procs? Hunter family, DmgClass RANGED, not passive, not a pet
    // ability (d1 b28), at least one damage effect (SCHOOL_DAMAGE, WEAPON_DAMAGE[_NOSCHOOL], NORMALIZED_WEAPON_DMG,
    // WEAPON_PERCENT_DAMAGE, or a PERIODIC_DAMAGE aura), and not Kill Command (34026 and PET.md's strike id).
    // Auto Shot is handled by the HIT branch of the aspect CheckProc, not here.
    bool  IsAspectRollSource(SpellInfo const* spellInfo);

    // The unit a proc should act on: the action target, or, in the CAST phase (no action target), the proc
    // spell's explicit unit target.
    Unit* GetProcTarget(ProcEventInfo& eventInfo);

    // REVIEW-MM-SV V1: a direct Fire hit from a spell that carries SUPPRESS_CASTER_PROCS raises no proc at all, the
    // victim's TAKEN procs included (Spell.cpp:2706, :2969-2974), so SV's Tarred proc can't see it. Every such spell
    // that must still count as a "direct Fire hit" calls this from its AfterHit. H0 declares it with an EMPTY body and
    // calls it from 201601's script (§B6.4); S3 fills the body and calls it from its own suppressed blasts.
    // Contract (SURVIVAL §0.23, binding on H0 and S3):
    //  - Callers: Tarred 202048's OnEffectProc (the unsuppressed sources: the 53301 hit, the 202045 impact, the 202051
    //    first blast, the 13812 blast) and the AfterHit of every suppressed Fire source (201601 from H0; 202052, 202053,
    //    202054 from S3). An AfterHit caller passes GetCaster(), GetHitUnit(), GetSpellInfo() and calls only when
    //    GetHitDamage() > 0 (no stack from a full absorb or an immune hit).
    //  - Body (S3): hunter = GetOwningPlayer(attacker); return unless hunter, target alive, target has Tarred 202048
    //    from hunter, spellInfo's school mask has FIRE, the spell is not periodic-only, and spellInfo->Id is not one
    //    of {53352, 202055, 202057, 202050} (blasts, blast splash, ground fire, Burning Tar). Then AddBurningTar.
    //  - Never twice for one hit: a spell either raises the Tarred proc (no SUPPRESS_CASTER_PROCS) or calls this from
    //    AfterHit (it has the attribute), never both. WP-B keeps the list in a comment next to the body.
    void  OnDirectFireHit(Unit* attacker, Unit* target, SpellInfo const* spellInfo);

    // Shot mana (§B2, S1b PT-6): the percent of BASE mana stored in the shot's EFFECT_1 DUMMY (tenths of a percent),
    // read with CalcValue(caster) so SPELLMOD_EFFECT2 / ALL_EFFECTS talents apply. A shot without an EFFECT_1 reads 0.
    // S3 (user ruling 6): Raptor Strike reads Deadly Focus rank 2's eff2 marker (a whole percent), 0 without it.
    float GetShotManaPct(Unit const* caster, SpellInfo const* shot);
    // EnergizeBySpell(player, shot->Id, base mana (GetCreateMana, the class/level base) * pct * multiplier,
    // POWER_MANA). Every caller shares that base: Arcane Shot, Raptor Strike, and later MM's free Arcane Shot and
    // Lethal Shots capstone.
    void  RestoreShotMana(Player* player, SpellInfo const* shot, float multiplier = 1.0f);

    // ---- H0-P (PET.md §8.4 defines the bodies and the rest of the pet section) ----
    constexpr uint32 SPELL_BLOODTHIRSTY_54131 = HunterData::SPELL_BLOODTHIRSTY_54131;
    constexpr uint32 SPELL_WEB_PULL = HunterData::SPELL_WEB_PULL; // appears once web_pull_201718 is generated

    // H0-P2: DSL-declared ids (hunter_pet.py, hunter_spells.py)
    constexpr uint32 SPELL_HUNTER_PET_VERSATILITY = HunterData::SPELL_HUNTER_PET_VERSATILITY;    // 201700
    constexpr uint32 SPELL_HUNTER_PET_CRIT_HASTE = HunterData::SPELL_HUNTER_PET_CRIT_HASTE;      // 201701
    constexpr uint32 SPELL_HUNTER_PET_DAMAGE_HOOK = HunterData::SPELL_HUNTER_PET_DAMAGE_HOOK;    // 201702
    constexpr uint32 SPELL_KILL_COMMAND_TELEPORT = HunterData::SPELL_KILL_COMMAND_TELEPORT;      // 201704
    constexpr uint32 SPELL_KILL_COMMAND_STRIKE = HunterData::SPELL_KILL_COMMAND_STRIKE;          // 201705
    constexpr uint32 SPELL_FEROCITY_KIT = HunterData::SPELL_FEROCITY_KIT;                        // 201706
    constexpr uint32 SPELL_TENACITY_KIT = HunterData::SPELL_TENACITY_KIT;                        // 201707
    constexpr uint32 SPELL_HUNTER_PET_AUTOCAST_MARKER = HunterData::SPELL_HUNTER_PET_AUTOCAST_MARKER; // 201703
    constexpr uint32 SPELL_HUNTER_PET_UTILITY_MARKER = HunterData::SPELL_HUNTER_PET_UTILITY_MARKER; // 201752
    constexpr uint32 SPELL_CUNNING_KIT = HunterData::SPELL_CUNNING_KIT;                          // 201708
    constexpr uint32 SPELL_BITE = HunterData::SPELL_BITE;
    constexpr uint32 SPELL_CLAW = HunterData::SPELL_CLAW;
    constexpr uint32 SPELL_SMACK = HunterData::SPELL_SMACK;
    constexpr uint32 SPELL_VENOM_SPIT = HunterData::SPELL_VENOM_SPIT;
    constexpr uint32 SPELL_CUNNING_SPIT = HunterData::SPELL_CUNNING_SPIT;
    constexpr uint32 SPELL_FURIOUS_HOWL = HunterData::SPELL_FURIOUS_HOWL;
    constexpr uint32 SPELL_ROAR_OF_COURAGE = HunterData::SPELL_ROAR_OF_COURAGE;
    constexpr uint32 SPELL_TEAR_ARMOR = HunterData::SPELL_TEAR_ARMOR;
    constexpr uint32 SPELL_MENACING_ROAR = HunterData::SPELL_MENACING_ROAR;
    constexpr uint32 SPELL_GROWL = HunterData::SPELL_GROWL;
    constexpr uint32 SPELL_DASH = HunterData::SPELL_DASH;
    constexpr uint32 SPELL_LAST_STAND = HunterData::SPELL_LAST_STAND;
    constexpr uint32 SPELL_BULLHEADED = HunterData::SPELL_BULLHEADED;
    constexpr uint32 SPELL_BESTIAL_WRATH = HunterData::SPELL_BESTIAL_WRATH;
    // Stock ids the DSL never declares (no HunterData:: name): hand literals.
    constexpr uint32 SPELL_COWER = 1742;                   // stock Cower, pulled onto the Ferocity lines (PET 4.4)
    constexpr uint32 SPELL_HUNTER_PET_SCALING_01 = 34902;  // stock Hunter Pet Scaling 01, rebound by H0-P2 (PET 5.3)
    constexpr uint32 SPELL_KILL_COMMAND_PET = 58914;       // stock Kill Command pet aura, left inert (PET 6.1)

    // PET.md 8.4. The ids alias HunterData:: from the generated header; GetPassthroughKind reads
    // HunterData::STAMPEDE_ENTRY_MIN/MAX.
    enum class PetType : uint8 { Ferocity = 0, Tenacity = 1, Cunning = 2, None = 0xFF };
    enum class PassthroughKind : uint8 { None, Pet, StampedeBeast };

    struct PetKit { uint32 basic; uint32 utility; uint32 commandI; uint32 commandII; };

    PetType GetPetType(Unit const* petOrGuardian);            // CreatureFamilyEntry::petTalentType
    PetKit const& GetPetKit(uint32 creatureFamily);           // PET 4.2 + 4.9; unknown family -> its type's default
    uint32 GetCommandSpell(Unit const* pet, uint8 slot);      // slot 0 = Command I, 1 = Command II (BM S1)
    bool HasActivePet(Player const* owner);                   // pet exists, alive, in world (MM Lone Survivor)
    SpellCastResult CheckPetCanAct(Player* owner, Unit* target, SpellInfo const* petSpell);
        // null petSpell = Kill Command (no pet reach); else the commanded spell's range + pet LoS (a melee-range
        // spell is measured as the pet's own triggered cast measures it, Spell::CheckRange, S1a-5)
    void ApplyPetKit(Player* owner, Pet* pet);                // 201706-201708 swap
    void ApplyPetTypeStats(Guardian* guardian);               // swing, base, white scale (PET 5.6)
    PassthroughKind GetPassthroughKind(Player const* owner, Unit const* unit);
    void RefreshPetPassthrough(Player* owner, Unit* unit);    // add-if-missing + recalc of every effect, 201700-201702
    void RefreshAllPassthrough(Player* owner);                // m_Controlled walk
    int32 ComputePetPassthroughAmount(Player* owner, Unit* target, uint32 spellId, uint8 effIndex);
    float GetPetDamageDonePct(Pet const* pet);                // excl. 19574, 201700, 201702 (Stampede copy)
    float GetPetCritBonusPct(Pet const* pet);                 // pet aura 52 + 290, excl. 201701

    // Harness-approved additions (H0-P2 D6, D12). Both are idempotent and cheap; the 34902 tick (EFFECT_0 only) and
    // OnPetAddToWorld call them.
    // Pins POWER_HAPPINESS and POWER_FOCUS at max (PET 4.7); refreshes white damage if the happiness state changed.
    void PinPetPowers(Pet* pet);
    // Seats the default pet bar (basic, utility, Growl, Cower/Dash) once per pet (while it lacks marker 201703) when
    // the basic is on no bar slot, and turns autocast on once for the basic and once for the buff/debuff utility,
    // each tracked by its own hidden marker spell (201703, 201752) in pet_spell. S1b PT-5: also keeps the two
    // passive "Command I/II: <ability>" display spells of the pet's kit in its spellbook (commanded id +
    // HunterData::COMMAND_DISPLAY_OFFSET) and removes the other 14. Needs a live, loaded pet.
    void SeatDefaultPetBar(Pet* pet);

    // Aspect of the Monkey (SHARED B6.6): puts 201605 on a pet that lacks it while its owner carries the aspect.
    // Idempotent; called from the pet-added hook and from the 34902 tick (a fresh tame never reaches the hook).
    void ReapplyPetMonkeyAura(Player* owner, Pet* pet);

    // ---- S1a (Beast Mastery, BEAST-MASTERY.md §8.4; S1b appends GetStampedeEntry, ApplyBmPetAuras,
    //      OnPhoenixPlumePetDeath) ----
    // Stock ids the BM code uses (no HunterData:: name for the Tamed Pet Passive channels): hand literals.
    constexpr uint32 SPELL_TAMED_PET_PASSIVE_8875 = 8875;     // stock Tamed Pet Passive (pet talent channel)
    constexpr uint32 SPELL_TAMED_PET_PASSIVE_19581 = 19581;   // stock Tamed Pet Passive (pet talent channel)
    constexpr uint32 SPELL_TAMED_PET_PASSIVE_19591 = 19591;   // stock Tamed Pet Passive (pet talent channel)
    constexpr uint32 SPELL_TAMED_PET_PASSIVE_34667 = 34667;   // stock Tamed Pet Passive (pet talent channel)
    constexpr uint32 SPELL_COBRA_SHOT_TRANSFORM = HunterData::SPELL_COBRA_SHOT_TRANSFORM;  // 201811
    constexpr uint32 SPELL_COBRA_SHOT_RANK3 = HunterData::SPELL_COBRA_SHOT_201851;         // 201851

    float GetBeastMasteryPetMasteryPct(Player const* owner);     // Mastery % with The Beast Within 3/3 (201857), else 0
    bool  IsBeastCleaveExcluded(SpellInfo const* spellInfo);     // 201725/6/9, 201736, 201804/5/7
    void  RefreshSteadyShotTransforms(Player* player);           // 201811 re-add when 201851 is known (C6)
    void  RecalculatePetTalentChannels(Player* player);          // pet auras 8875, 19581, 19591, 34667 (§0.14)
    void  OnBeastMasteryTalentsChanged(Player* player);          // the two above, then RefreshAllPassthrough once
    void  CommandPetAttack(Pet* pet, Unit* target);              // A13
    void  CollectBmSplashTargets(Player* hunter, Unit* source, Unit* center, float radius, uint32 maxTargets,
                                 std::vector<Unit*>& out);       // A13, §0.4 filter
    // ---- S1b ----
    uint32 GetStampedeEntry(uint32 creatureFamily);      // 1/2/11/4/3 -> 300200..300204, else by type 300205..300207
    void   ApplyBmPetAuras(Player* owner, Pet* pet);     // 201809 add-if-missing (owner as caster); kind Pet only
    void   OnPhoenixPlumePetDeath(Unit* unit);           // HunterUnitScript::OnUnitDeath body (§4.10)

    // ---- S2 (Marksmanship, MARKSMANSHIP.md §4.8 as amended by S2a-HANDOFF A20) ----
    enum class Mark : uint8 { Sniper = 0, Viper = 1, Falcon = 2, Max = 3 };

    // Tunables (one place each: the const() rows of hunter_mm_spells.py, X10). Spell values live in the DBC; these
    // are the script-only numbers.
    constexpr uint8  MARK_MAX_STACKS = HunterData::MARK_MAX_STACKS;
    constexpr uint8  MARK_GAIN = HunterData::MARK_GAIN;
    constexpr uint8  MARK_FAVORED_GAIN = HunterData::MARK_FAVORED_GAIN;   // total (cast 1 + favored 2), §0.4 R2-13
    constexpr uint8  KEEN_EYE_GAIN = HunterData::KEEN_EYE_GAIN;
    constexpr int32  SNIPER_CRIT_CHANCE = HunterData::SNIPER_CRIT_CHANCE;   // flat points
    constexpr int32  SNIPER_CRIT_DAMAGE_PER_STACK = HunterData::SNIPER_CRIT_DAMAGE_PER_STACK;   // pct of the crit bonus
    constexpr int32  CHIMERA_SNIPER_CRIT_CHANCE = HunterData::CHIMERA_SNIPER_CRIT_CHANCE;
    constexpr int32  CHIMERA_SNIPER_CRIT_DAMAGE = HunterData::CHIMERA_SNIPER_CRIT_DAMAGE;
    constexpr int32  MARK_FALCON_HASTE_PER_STACK = HunterData::MARK_FALCON_HASTE_PER_STACK;
    constexpr uint32 QUICKENING_MS_PER_STACK = HunterData::QUICKENING_MS_PER_STACK;
    constexpr float  PACK_RADIUS = HunterData::PACK_RADIUS_YD;            // ricochet, bounce
    constexpr uint8  PACK_MAX_TARGETS = HunterData::PACK_MAX_TARGETS;
    constexpr uint8  MULTI_SHOT_TARGET_CAP = HunterData::MULTI_SHOT_TARGET_CAP;   // primary + 4 chain targets
    constexpr uint32 DEADEYE_CDR_MS = HunterData::DEADEYE_CDR_MS;
    constexpr uint32 FOCUSED_AIM_CDR_MS = HunterData::FOCUSED_AIM_CDR_MS;
    constexpr float  RAPID_KILLING_HEALTH_PCT = HunterData::RAPID_KILLING_HEALTH_PCT;
    constexpr int32  RAIN_OF_ARROWS_FIRE_PCT = HunterData::RAIN_OF_ARROWS_FIRE_PCT;   // S2b (Volley tick Fire! roll)
    constexpr int32  PACK_SHOT_DAMAGE_PCT = HunterData::PACK_SHOT_DAMAGE_PCT;   // S2b ricochet / bounce, % of Aimed
    constexpr uint32 BARRAGE_ICD_MS = HunterData::BARRAGE_ICD_MS;               // S2b half Volley ICD (spell_proc)
    // S2b Combat Experience capstone: Intellect = this percent of Agility.
    constexpr int32  COMBAT_EXPERIENCE_CAPSTONE_PCT = HunterData::COMBAT_EXPERIENCE_CAPSTONE_PCT;

    uint32 GetMarkSpellId(Mark mark);                                          // 0 for Mark::Max
    bool   GetMarkForSpell(uint32 spellId, Mark& out);                         // false unless 201920-201922
    bool   HasMark(Player const* player, Unit const* target, Mark mark);       // the player's mark aura is on target
    uint8  GetMarkStacks(Player const* player, Unit const* target, Mark mark); // 0 when absent
    void   AddMarkStacks(Player* player, Unit* target, Mark mark, uint8 amount);  // cap, show max(1,n), Falcon; guarded
    void   SetMarkStacks(Player* player, Unit* target, Mark mark, uint8 stacks);  // copies, re-press reset; guarded
    void   OnMarkApplied(Player* player, Unit* target, Mark mark);   // REAL apply only -> counter 0; no stack write
    void   OnMarkRemoved(Player* player, Unit* target, Mark mark);   // REAL remove only; find-only
    // Convergence centre (§5.2 step 9, S2b): set just before the synchronous CastSpell of 201932, cleared right after.
    void   SetConvergenceCentre(Player* player, ObjectGuid centre);
    ObjectGuid GetConvergenceCentre(Player const* player);

    // Per-cast snapshot (M14): lives in the SpellScript instance, never in HunterMechanics state.
    struct MarkSnapshot
    {
        std::array<bool, 3>  present{};
        std::array<uint8, 3> stacks{};
        uint8 Count() const;           // marks present
        bool  Has(Mark mark) const;
        uint8 Stacks(Mark mark) const; // 0 when absent
    };
    MarkSnapshot ReadMarks(Player const* player, Unit const* target);
    void   ConsumeMarks(Player* player, Unit* target, MarkSnapshot const& snapshot);   // removes the snapshot's auras

    void   OnHunterSpellCast(Player* player, Spell* spell);   // §4.3, called from HunterPlayerScript
    // §5.10, Arcane/Multi-Shot OnCast. The caller skips triggered casts (the signature carries no Spell).
    void   RollKeenEye(Player* player, Unit* target);
    void   RefreshFalconHaste(Player* player);                // §4.5
    void   SetSniperCritHelper(Player* player, uint32 helperId, int32 critChance, int32 critDamagePct);
    float  GetSniperPayoffMultiplier(Player const* player);   // §4.7
    float  GetTriangulationMultiplier(Player const* player, uint8 marksConsumed);   // 1.0 without a rank
    float  GetRapidKillingExecutePct(Player const* player);   // §6 row (2,3): known rank's eff0, 0 without a rank
    // §10.4 / S2b B8: Rapid Killing's execute clause, from HunterUnitScript::ModifySpellDamageTaken (every spell hit).
    void   ApplyMarksmanshipTakenMods(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo);
    // §10.3 / §10.4 / S2b B7: 201950 up without a live hunter pet, at the rank's Classic or Classless value.
    void   RefreshLoneSurvivor(Player* player);
    void   NoteTripleConsume(Player* player);
    uint32 GetLastTripleConsumeMs(Player const* player);      // GameTime ms, 0 = never; B0b reads it (Readiness rule)
    void   ClearMarksmanshipState(Player* player);            // called from Hunter::ClearState

    // ---- S2 / S3 append their own sections (mark state, Burning Tar bank) ----

    // ---- S3 (Survival, SURVIVAL.md §10 as frozen by S3a-HANDOFF A17; S3b adds no signature) ----
    // Hand literals for stock ids the DSL may name differently; the rest alias HunterData::.
    constexpr uint32 SPELL_LOCK_AND_LOAD_BUFF   = 56453;
    constexpr uint32 SPELL_LOCK_AND_LOAD_MARKER = 67544;
    constexpr uint32 CATEGORY_ARCANE_EXPLOSIVE  = 1173;
    constexpr uint32 CATEGORY_FIRE_TRAPS        = 1250;
    constexpr uint32 SPELL_REPLENISHMENT        = 57669;   // stock, undeclared (Hunting Party's buff, 0-verify §7)

    // DSL-declared ids (hunter_sv_spells.py, hunter_sv_ranks.py, hunter_trigger_spells.py, hunter_spells.py).
    constexpr uint32 SPELL_RAPTOR_STRIKE = HunterData::SPELL_RAPTOR_STRIKE;                          // 2973
    constexpr uint32 SPELL_EXPLOSIVE_SHOT = HunterData::SPELL_EXPLOSIVE_SHOT;                        // 53301
    constexpr uint32 SPELL_EXPLOSIVE_SHOT_BLAST = HunterData::SPELL_EXPLOSIVE_SHOT_53352;            // 53352
    constexpr uint32 SPELL_TARRED = HunterData::SPELL_TARRED;                                        // 202048
    constexpr uint32 SPELL_BURNING_TAR = HunterData::SPELL_BURNING_TAR;                              // 202050
    constexpr uint32 SPELL_CLUSTER_BOMBS = HunterData::SPELL_CLUSTER_BOMBS;                          // 202051
    constexpr uint32 SPELL_CLUSTER_BOMBS_BLAST = HunterData::SPELL_CLUSTER_BOMBS_BLAST;              // 202052
    constexpr uint32 SPELL_SHRAPNEL_HIT = HunterData::SPELL_SHRAPNEL_HIT;                            // 202053
    constexpr uint32 SPELL_EXPLOSIVE_SHOT_SPLASH = HunterData::SPELL_EXPLOSIVE_SHOT_SPLASH;          // 202054
    constexpr uint32 SPELL_EXPLOSIVE_SHOT_BLAST_SPLASH = HunterData::SPELL_EXPLOSIVE_SHOT_BLAST_SPLASH; // 202055
    constexpr uint32 SPELL_EXPLOSIVE_TRAP_FIRE = HunterData::SPELL_EXPLOSIVE_TRAP_FIRE;              // 202057
    constexpr uint32 SPELL_POINT_OF_NO_ESCAPE_MARKER = HunterData::SPELL_POINT_OF_NO_ESCAPE_MARKER;  // 202058
    constexpr uint32 SPELL_TNT_MASTERY = HunterData::SPELL_TNT_MASTERY;                              // 202062
    constexpr uint32 SPELL_FAVORED_PREY_BEAST = HunterData::SPELL_FAVORED_PREY_BEAST;                // 202063
    constexpr uint32 SPELL_FAVORED_PREY_DRAGONKIN = HunterData::SPELL_FAVORED_PREY_DRAGONKIN;        // 202064
    constexpr uint32 SPELL_FAVORED_PREY_DEMON = HunterData::SPELL_FAVORED_PREY_DEMON;                // 202065
    constexpr uint32 SPELL_FAVORED_PREY_ELEMENTAL = HunterData::SPELL_FAVORED_PREY_ELEMENTAL;        // 202066
    constexpr uint32 SPELL_FAVORED_PREY_GIANT = HunterData::SPELL_FAVORED_PREY_GIANT;                // 202067
    constexpr uint32 SPELL_FAVORED_PREY_UNDEAD = HunterData::SPELL_FAVORED_PREY_UNDEAD;              // 202068
    constexpr uint32 SPELL_FAVORED_PREY_HUMANOID = HunterData::SPELL_FAVORED_PREY_HUMANOID;          // 202069
    constexpr uint32 SPELL_FAVORED_PREY_CRITTER = HunterData::SPELL_FAVORED_PREY_CRITTER;            // 202070
    constexpr uint32 SPELL_FAVORED_PREY_MECHANICAL = HunterData::SPELL_FAVORED_PREY_MECHANICAL;      // 202071
    constexpr uint32 SPELL_FAVORED_PREY_NOT_SPECIFIED = HunterData::SPELL_FAVORED_PREY_NOT_SPECIFIED; // 202072
    // Talent rank spells the mechanics read (each a passive aura on the hunter).
    constexpr uint32 SPELL_DEADLY_FOCUS_R2 = HunterData::SPELL_DEADLY_FOCUS_202081;                  // 202081
    constexpr uint32 SPELL_SHRAPNEL_R1 = HunterData::SPELL_SHRAPNEL;                                 // 202098
    constexpr uint32 SPELL_SHRAPNEL_R2 = HunterData::SPELL_SHRAPNEL_202099;                          // 202099
    constexpr uint32 SPELL_POINT_OF_NO_ESCAPE_R1 = HunterData::SPELL_POINT_OF_NO_ESCAPE;             // 53298
    constexpr uint32 SPELL_POINT_OF_NO_ESCAPE_R2 = HunterData::SPELL_POINT_OF_NO_ESCAPE_53299;       // 53299
    constexpr uint32 SPELL_POINT_OF_NO_ESCAPE_R3 = HunterData::SPELL_POINT_OF_NO_ESCAPE_202106;      // 202106
    constexpr uint32 SPELL_LOCK_AND_LOAD_R1 = HunterData::SPELL_LOCK_AND_LOAD;                       // 56342
    constexpr uint32 SPELL_LOCK_AND_LOAD_R2 = HunterData::SPELL_LOCK_AND_LOAD_56343;                 // 56343
    constexpr uint32 SPELL_LOCK_AND_LOAD_R3 = HunterData::SPELL_LOCK_AND_LOAD_56344;                 // 56344

    // Tunables (one place each: the const() rows of hunter_sv_spells.py, X10).
    constexpr float  SHRAPNEL_RADIUS_YD = HunterData::SHRAPNEL_RADIUS_YD;
    constexpr uint8  CLUSTER_BOMBS_FOLLOWUP_COUNT = HunterData::CLUSTER_BOMBS_FOLLOWUP_COUNT;
    constexpr uint32 CLUSTER_BOMBS_FOLLOWUP_MS = HunterData::CLUSTER_BOMBS_FOLLOWUP_MS;           // first offset
    constexpr uint32 CLUSTER_BOMBS_FOLLOWUP_LAST_MS = HunterData::CLUSTER_BOMBS_FOLLOWUP_LAST_MS; // last offset
    constexpr float  CLUSTER_BOMBS_SCATTER_YD = HunterData::CLUSTER_BOMBS_SCATTER_YD;
    constexpr float  IGT_SLOW_MIN_DISTANCE_YD = HunterData::IGT_SLOW_MIN_DISTANCE_YD;
    constexpr uint32 SNAKE_STING_REFRESH_MS = HunterData::SNAKE_STING_REFRESH_MS;
    constexpr uint32 THRILL_MM_CUT_FACTOR = HunterData::THRILL_MM_CUT_FACTOR;
    constexpr int32  THRILL_MANA_REFUND_PCT = HunterData::THRILL_MANA_REFUND_PCT;                 // text only

    // Burning Tar bank (C18; Mage::AddIgniteDamage shape). Key = (caster GUID, target GUID); find-only on removal.
    void   AddBurningTar(Player* hunter, Unit* target);                         // chunk, cast/refresh, stack display
    // §5.10 weights; empties the bank on the last tick.
    uint32 TakeBurningTarTick(Unit* caster, Unit* target, AuraEffect const* eff);
    uint32 GetBurningTarRemaining(Unit const* caster, Unit const* target);      // bots / sims / logging
    uint32 GetBurningTarStacks(Unit const* caster, Unit const* target);
    void   ClearBurningTar(ObjectGuid casterGuid, ObjectGuid targetGuid);
    void   ClearBurningTarForCaster(ObjectGuid casterGuid);                     // called from ClearState (logout)

    // Lock and Load (C49): one trigger path for the row, the tick script and Chain Reaction.
    bool   TryLockAndLoad(Player* hunter, float baseChancePct);  // false while 67544 is up, else RollProcChance
    void   TriggerLockAndLoad(Player* hunter);                   // 56453, 67544, reset category 1173; r3: CB -2 s

    void   TryShrapnel(Player* hunter, Unit* primary);           // §5.7
    // Explosive Shot recast carry (V3): a done-final amount per remaining blast, keyed (caster GUID, target GUID).
    void   SetExplosiveShotCarry(Unit* caster, Unit* target, uint32 perBlast);
    uint32 GetExplosiveShotCarry(Unit const* caster, Unit const* target);   // 0 when none
    void   ClearExplosiveShotCarry(Unit const* caster, Unit const* target);
    void   ClearExplosiveShotCarryForCaster(ObjectGuid casterGuid);         // called from ClearState (logout)
    // Aura 168 product; the only signature (V-m4).
    float  GetCreatureTypeDoneFactor(Unit const* caster, Unit const* target, SpellInfo const* spellInfo);
    float  GetPointOfNoEscapePct(Player const* hunter);          // rank 53298/53299/202106 eff0, 0 without the talent
    void   UpdatePointOfNoEscape(Unit* caster, Unit* target);    // add/extend/remove 202058 (duration = longest source)
    bool   IsOncePerRangedCast(ProcEventInfo& eventInfo);        // §7.2
    uint32 GetFavoredPreyBuff(uint32 creatureType);              // 0 for totem / non-combat pet / gas cloud
    void   ReduceCategoryCooldown(Player* player, uint32 category, uint32 ms); // §0.19
    // S3 supplies the body of the H0 section's OnDirectFireHit (contract there and in SURVIVAL §0.23); it calls
    // AddBurningTar.
}

#endif
