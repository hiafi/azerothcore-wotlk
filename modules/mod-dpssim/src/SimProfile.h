/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef MODULE_DPSSIM_SIMPROFILE_H
#define MODULE_DPSSIM_SIMPROFILE_H

#include "Define.h"
#include "SimHeal.h"
#include "SimTank.h"
#include <map>
#include <string>
#include <vector>

// A named sim build - "what to test" (class, talents, gear, synthetic stats) kept in its own
// small file instead of packed into dpssim.conf's flat keys, so the deployment can keep a
// library of them (FrostMageSim.conf, ArcaneMageSim.conf, ...) and switch between them with one
// conf key (DpsSim.Profile) instead of hand-editing PlayerbotTalents every time. Deliberately its
// own tiny format, not routed through ConfigMgr/LoadAdditionalFile: ConfigMgr is a single global
// key/value namespace loaded once at boot, and every profile would collide on the same key names
// (every profile needs its own "Class", its own "PlayerbotTalents") - this format sidesteps that
// by giving each profile file its own private namespace, loaded on demand by path instead of
// merged into the global one.
namespace SimProfile
{
    // One profile's data. Only DpsSim.RunPlayerbot reads this today (via SimDaemon::RunConfig's
    // ActorClass/PlayerbotTalents/GearItemIds/SpellPower/CombatRatings fields) - see
    // dpssim.conf.dist's DpsSim.Profile doc comment for how it overrides the flat
    // DpsSim.PlayerbotTalents key when set (gear/stats have no flat-key equivalent - they only
    // exist via a profile).
    struct Profile
    {
        // A CLASS_* value from SharedDefines.h (e.g. 8 for CLASS_MAGE). Required - Load() fails
        // if this key is missing. Any class works: SimBot's pull bootstraps combat by having each
        // dummy engage the bot (Unit::EngageWithTarget(), see SimBot::Create()) rather than a class
        // spell (the old hardcoded Frostbolt pull was replaced 2026-10-05 for RetPaladinSim).
        uint8 Class = 0;

        // Same "<arcane>-<fire>-<frost>"-style positional talent string DpsSim.PlayerbotTalents
        // takes directly (see that key's own conf doc comment for the format and how to get a
        // string that's actually correct for this deployment's talent trees via the in-game
        // "talents link" command). Empty = no talents spent.
        std::string PlayerbotTalents;

        // Real item ids to equip, applied in listed order via
        // Player::StoreNewItemInBestSlots() - the same call the core's own "give this player an
        // item, put it wherever it goes" paths use (auto-placed by the item's own template, e.g.
        // an item flagged as a wrist slot item lands on the wrist). A later item contesting an
        // already-filled slot simply fails to equip (logged as an error, not fatal to the run) -
        // list at most one item per slot. Applied before CombatRatings/SpellPower below, so a
        // profile can layer a synthetic top-up on top of a real gear baseline. Empty = no gear
        // (naked caster, aside from whatever CombatRatings/SpellPower add directly).
        std::vector<uint32> GearItemIds;

        // Flat spell power added on top of the level/race/gear baseline - same field
        // SimDaemon::RunConfig::SpellPower and SimActor::Config::SpellPower already carry
        // end-to-end via Player::ApplySpellPowerBonus(); a profile is just one more source for it.
        int32 SpellPower = 0;

        // Synthetic combat-rating injection - flat, direct Player::ApplyRatingMod() calls, no
        // item or aura needed. Keyed by this deployment's own CombatRating enum (Unit.h),
        // including its custom repurposed slots (CR_MASTERY/CR_VERSATILITY/CR_COOLDOWN_HASTE/
        // CR_PROC_CHANCE - see Unit.h's own "Custom: was ..." comments on those four). See
        // SimProfile.cpp's RATING_KEYS table for the conf key name each CombatRating maps to
        // (e.g. "HasteRating" fans out to CR_HASTE_MELEE/RANGED/SPELL together, mirroring how a
        // real item's single ITEM_MOD_HASTE_RATING stat applies to all three -
        // Player::_ApplyItemBonuses()'s own ITEM_MOD_HASTE_RATING case does exactly this fan-out).
        // Applied after GearItemIds, so these are a top-up on top of whatever gear already
        // contributed, not a replacement for it. Any CombatRating absent from this map is left
        // untouched (not reset to 0) - Load() only inserts an entry for a key actually present in
        // the file.
        std::map<uint8, int32> CombatRatings;

        // Synthetic core-stat top-ups (Strength/Agility/Stamina/Intellect/Spirit -
        // SharedDefines.h's Stats enum), keyed by that enum. Applied via
        // Player::HandleStatFlatModifier() + UpdateStatBuffMod() - the same two calls a real
        // item's ITEM_MOD_STRENGTH/AGILITY/STAMINA/INTELLECT/SPIRIT stat uses
        // (Player::_ApplyItemBonuses()'s own cases), not a raw Unit::SetStat() (which would just
        // get overwritten by the next UpdateAllStats() recompute - HandleStatFlatModifier() is
        // what actually participates in that recompute). See SimProfile.cpp's STAT_KEYS table for
        // the conf key name each Stats value maps to ("Strength", "Agility", ...). Any Stats value
        // absent from this map is left untouched (not reset to 0).
        std::map<uint8, float> Stats;

        // Flat attack power added on top of gear/level/race, applied via
        // Player::HandleStatFlatModifier() against BOTH UNIT_MOD_ATTACK_POWER and
        // UNIT_MOD_ATTACK_POWER_RANGED - mirrors exactly how a real item's single
        // ITEM_MOD_ATTACK_POWER stat applies to both at once (Player::_ApplyItemBonuses()'s own
        // case).
        int32 AttackPower = 0;

        // Dummy health drain, off by default (absent = off = today's behaviour: the dummy zeroes all damage, its health
        // never moves). `DummyHealthDrain = true` makes the dummy take real damage but never drop below 1 health, so it
        // never dies, and resets it to full health at the start of every iteration - that lets "target below 20%"-style
        // execute rows fire. `DummyMaxHealth = <n>` sets the dummy's max health, which is what those percentages are
        // measured against (0 = SimTarget::Config's default, 100,000,000 - far too large for any sim to move the
        // percentage, so set it to something a fight can actually drain, e.g. a few hundred thousand).
        bool DummyHealthDrain = false;
        uint32 DummyMaxHealth = 0;

        // The dummy's armor. 0 (absent) = no armor, as before. Copied to SimDaemon::Config::TargetArmor and from there
        // to SimTarget::Config::Armor. The profiles use 4350, about a level-62 dungeon boss (creature_classlevelstats
        // level 62 class 1 = 4,344).
        uint32 TargetArmor = 0;

        // Pre-pull buff phase, in sim ms (default 15000: a 10 s pet summon plus a few GCDs). Before every
        // iteration, the first included, the bot runs its non-combat engine - restricted to its buff, pet and
        // non-combat rotation strategies (SimBot::BeginBuffPhase()) - for this long, out of combat, so it presses
        // its aura, casts its self-buffs and summons its pet as in game, then the pull happens as always. Nothing
        // cast or applied in the phase is recorded; spell cooldowns it starts carry into the fight; resources are
        // refilled before the pull.
        // A cast still going when the phase ends is interrupted, with a warning. 0 disables the phase: the old
        // behaviour (the bot starts every iteration in combat, unbuffed). A run with no profile uses the default.
        uint32 PrePullBuffMs = 15000;

        // Whether the actor gets its class's premade glyphs, as a live random bot does: PlayerbotFactory::
        // InitGlyphs() after the talents, picking AiPlayerbot.PremadeSpecGlyph.<class>.<spec tab> by level (true by
        // default). Glyph effects then show in the sim, e.g. a Frost mage's Glyph of Eternal Water lets the pre-pull
        // phase summon the permanent Water Elemental. "false" leaves the actor unglyphed (the behaviour before
        // 2026-10-06). A run with no profile uses the default.
        bool PlayerbotGlyphs = true;

        // Hunter pet: the creature_template entry of a beast the actor tames before the first iteration (0 = no pet,
        // the behaviour of every class that has no permanent pet). A fixed entry, not a family, on purpose: the
        // factory's PlayerbotFactory::InitPet() picks a random tameable creature of the preferred families
        // (AiPlayerbot.PreferredHunterPetFamilies), and a sim needs the same pet in every iteration and every run.
        // The pet is made the way InitPet() makes it - Player::CreatePet(entry), the actor's level, autocast on for
        // every active pet spell - and then PlayerbotFactory::InitPetTalents() spends the pet's talent points from the
        // AiPlayerbot.PremadeHunterPetLink.<type>.<points> lines, exactly as for a live bot. If it is dead or gone at
        // the start of an iteration SimBot::EnsurePet() revives or re-creates it. Hunter profiles only (a profile with
        // a PetCreatureEntry and another Class fails to load). The entry must be a beast with a creature family; the
        // profiles use the stock "Tamable <family>" test entries, which exist in every database (level 1 in the
        // template, the pet takes the actor's level): Wolf 26016, Cat 26021, Raptor 26029, Bear 34025, Boar 26020,
        // Spider 26033.
        uint32 PetCreatureEntry = 0;

        // Master switch for modules/mod-dpssim/tools/stat_weights.py, added 2026-09-13: "false"
        // makes that tool refuse to run any batch at all for this profile, regardless of how many
        // TestX flags below are true - a single kill switch for "don't run stat weights against
        // this profile" without having to flip every TestX flag individually (or delete them and
        // lose the record of which stats were meant to be tested). Defaults true (absent = stat
        // weights allowed) so existing profiles that predate this key are unaffected. Same "nothing
        // in this C++ module reads it, parsed anyway to avoid unknown-key log spam" reasoning as
        // StatWeightTests below.
        bool StatWeightsEnabled = true;

        // Stat-weight testing toggles, added 2026-09-13 for modules/mod-dpssim/tools/
        // stat_weights.py: "TestStrength = true/false", one per stat/rating key this profile
        // format understands (STAT_KEYS/RATING_KEYS in SimProfile.cpp, plus "TestSpellPower"/
        // "TestAttackPower" for those two flat fields) - true means that tool includes this stat
        // in its per-stat-point DPS weight pass for this profile, false or absent means it skips
        // it. Only consulted at all when StatWeightsEnabled above is true. Nothing in this C++
        // module reads this map itself - DpsSim.cpp's normal RunPlayerbot() path ignores it
        // entirely, same as it ignores any key it has no field for. It's parsed and stored here
        // anyway (rather than left to fail as an "unknown key" LOG_ERROR - see SimProfile.cpp's
        // Load()) purely so a stat-weight profile's TestX lines don't spam the worldserver log with
        // "unknown key" errors on every ordinary DpsSim.RunPlayerbot run that happens to load the
        // same profile file. Keyed by conf key name (not by CombatRating/Stats enum, unlike
        // CombatRatings/Stats above) since some tested "stats" - SpellPower, AttackPower - aren't
        // CombatRatings or Stats at all.
        std::map<std::string, bool> StatWeightTests;

        // ---- Heal mode (plan .agents/plans/healing-sim/healing-sim.PLAN.md, section 3) ----
        // `Mode = Heal` switches SimDaemon::RunPlayerbotBatch() to the healing sim: the profile's class is the healer
        // and it heals a group of headless allies that a boss damages with real hits. Absent (or `Mode = Dps`) is
        // every existing profile, unchanged. The keys below are read only by a Heal profile.
        bool HealMode = false;

        // `HealGroup = party | raid10 | raid20` and `HealTargets = <count>*<role>:<mode>:<value>, ...` (SimHeal.h
        // documents the syntax). Kept as text here: DpsSim.HealGroup / DpsSim.HealTargets in the conf override them
        // (run-sim.sh sets those per run), so the final parse and size check happen in DpsSim.cpp. Load() checks the
        // syntax of whatever is present, and the size match when both are.
        std::string HealGroup;
        std::string HealTargets;

        // Max health of the headless allies, per role (at least 1,000). Only the BASE part of the health modifier is
        // pinned, so Fortitude, Mark of the Wild and Kings still add as in game (plan R4).
        uint32 AllyMaxHealthTank = 9000;
        uint32 AllyMaxHealthDps = 5000;

        // Max health of every PINNED target, the healer's own slot included (`PinMaxHealth`, default 30,000, at least
        // 1,000), instead of the role values above, which then only apply to drain targets. A big pool cannot be filled
        // by the heals that land between two pin hits, so a pinned target has no overheal and a percent-of-max-health
        // pin is not a tiny number. Note that heals and shields scaled by max health are scaled with it. Same BASE-only
        // pin as the allies' health.
        uint32 PinMaxHealth = 30000;

        // Positional talent string spent on the tank allies (Warriors); must make PlayerbotAI::IsTank(tank, true) true,
        // which SimHealScenario checks at the pull. The default is the Protection string of ProtWarriorSim.conf.
        std::string AllyTankTalents = "--2331303122023321020330030123030";

        // Diameter of the cluster the allies stand in, around a point 8 yd in front of the healer. At most 25.
        float AllySpreadYards = 10.0f;

        // Time between the drain pulses (`drain:` targets), in sim ms. At least 100.
        uint32 DrainPulseMs = 1000;

        // `InfiniteMana = true`: the healer's mana is set to full every step of the measured fight (not the buff
        // phase), for a pure-throughput run (plan D8). DpsSim.InfiniteMana in the conf overrides it. Heal profiles
        // only: the key is refused in a DPS profile.
        bool InfiniteMana = false;
        // Whether the profile set the key at all, for that refusal
        bool InfiniteManaSet = false;

        // ---- Tank mode (plan .agents/plans/tank-sim/tank-sim.PLAN.md, section 3) ----
        // `Mode = Tank` switches SimDaemon::RunPlayerbotBatch() to the tank sim: the DPS sim with the dummies swinging
        // at the actor. The keys below are read only by a Tank profile (the loader refuses them in any other).
        bool TankMode = false;

        // `TankScenario = dps | survive`: dps refills the actor's health after every step (it never dies), survive does
        // not (the run ends at its death). DpsSim.TankScenario in the conf overrides it.
        SimTank::Scenario TankScenario = SimTank::Scenario::Dps;

        // `TankHitDamage` (the boss, a 1-target run) and `TankPackHitDamage` (each dummy of a 2+ target run): the
        // swing's damage before armor and before the victim's damage-taken modifiers, "<min>-<max>" or a single value.
        // DpsSim.TankHitDamage / DpsSim.TankPackHitDamage override them.
        SimTank::HitRange TankHitDamage = SimTank::DEFAULT_BOSS_HIT;
        SimTank::HitRange TankPackHitDamage = SimTank::DEFAULT_PACK_HIT;

        // `TankSwingMs`: the dummies' swing interval, in sim ms (500-10000). DpsSim.TankSwingMs overrides it.
        uint32 TankSwingMs = SimTank::DEFAULT_SWING_MS;

        // `TankDummyCrit` (true/false): whether the dummies can crit (CREATURE_FLAG_EXTRA_NO_CRIT off / on). Default
        // on. There is no dummy parry-haste switch (plan T7): the PvE always-hit rule (custom_pve_always_hit.cpp) means
        // a dummy never parries the actor; the actor's own parry haste is the core's.
        bool TankDummyCrit = true;

        // Whether the profile set any Tank* key, for the refusal in a non-Tank profile
        bool TankKeySet = false;
    };

    // Loads `path` (a full file path - see dpssim.conf.dist's DpsSim.Profile doc comment for why
    // this should be absolute) into `out`. Returns false and logs exactly what's wrong (missing
    // file, malformed line, missing required key, unparseable value) without partially filling
    // `out` on failure - callers should treat a false return as "job aborted", not "use defaults".
    bool Load(std::string const& path, Profile& out);
}

#endif
