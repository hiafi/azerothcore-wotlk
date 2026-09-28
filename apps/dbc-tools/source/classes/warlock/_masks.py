"""
Warlock - named SpellFamilyFlags (SpellClassMask_{1,2,3} / EffectSpellClassMask{A,B,C}_{1,2,3})
constants, plus `spell_proc` PROC_FLAG_*/PROC_SPELL_*/PROC_HIT_*/PROC_ATTR_* constants, shared
across the Affliction/Destruction/Demonology rework passes.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from ._masks import CORRUPTION, ...`.

Bit values below are the raw SpellFamilyFlags dword contents (already the "final" masked value a
row's SpellClassMask_N / EffectSpellClassMaskX_N column would carry), not bit positions. Sourced
from the existing stock warlock rows (re-verified against the dumps this session) and
.agents/plans/warlock-rework/warlock-rework.PLAN.md §4.4 / SHARED.md §3 (dword-3 custom-spell bit
allocation, one named constant per row; created in the Affliction pass's WP-0, extended - never
retyped - by Destruction/Demonology).

Created by Affliction WP-0 (AFFLICTION.md §3 item 2, PLAN §5/§6 item 3). Holds every stock
constant every spec file needs plus every custom bit (including Destruction's and Demonology's,
where already named - placeholders elsewhere, renamed by that pass), so later passes only import.
"""

# --- dword 1 (SpellClassMask_1 / EffectSpellClassMaskX_1) ---
SHADOW_BOLT = 0x1
CORRUPTION = 0x2
IMMOLATE = 0x4
DRAIN_LIFE = 0x8
DRAIN_MANA = 0x10
RAIN_OF_FIRE = 0x20
HELLFIRE = 0x40
SHADOWBURN = 0x80
SEARING_PAIN = 0x100
NPC_ONLY_D1_BIT9 = 0x200  # reclaimable - no player spell uses it
BANE_OF_AGONY = 0x400  # was Curse of Agony; 980 only
ENSLAVE_DEMON = 0x800
IMP_FIREBOLT = 0x1000
LASH_OF_PAIN = 0x2000
DRAIN_SOUL = 0x4000
CURSE_OF_WEAKNESS = 0x8000
HEALTHSTONE = 0x10000
SPELLSTONE = 0x20000
LIFE_TAP = 0x40000
DEATH_COIL = 0x80000
CREATE_STONE = 0x100000
FIRESTONE_ENCHANT = 0x200000
CURSE_OF_EXHAUSTION = 0x400000
BLOOD_PACT_FIRE_SHIELD = 0x800000
HEALTH_FUNNEL = 0x1000000
PET_ABILITIES = 0x2000000
TAMED_PET_PASSIVE = 0x1C000000
SUMMON_DEMON = 0x20000000
SOOTHING_KISS_SEDUCTION = 0x40000000
CURSE_OF_TONGUES_D1 = 0x80000000  # shared with Dark Pact and the Shadow Embrace debuffs - never
# use this to mean Curse of Tongues; the real Curse of Tongues bit lives on dword 3 (0x800).

# --- dword 2 (SpellClassMask_2 / EffectSpellClassMaskX_2) ---
NPC_SIPHON_LIFE = 0x1
CURSE_OF_DOOM = 0x2
SEED_OF_CORRUPTION_DOT = 0x4  # new, B16 rebit - Seed DoT 27243 only
HOWL_OF_TERROR = 0x8
SEED_OF_CORRUPTION = 0x10  # detonation 27285 + NPC 43991 only, after B16 (DoT moved off this bit)
DEMON_ARMOR = 0x20
INCINERATE = 0x40
SOUL_FIRE = 0x80
UNSTABLE_AFFLICTION = 0x100
CURSE_OF_THE_ELEMENTS = 0x200
FEAR = 0x400
SHADOWFURY = 0x1000
SEED_DETONATION = 0x8000
SHADOWFLAME = 0x10000
CHAOS_BOLT = 0x20000
HAUNT = 0x40000
DEMONIC_PACT_AURA = 0x100000
SHADOW_BITE = 0x400000
CONFLAGRATE = 0x800000
EMPOWERED_IMP_PASSIVE = 0x1000000
FEL_INTELLIGENCE = 0x2000000
USE_SOULSTONE = 0x4000000
BANISH = 0x8000000
FEL_ARMOR = 0x20000000
RITUAL_OF_SOULS = 0x80000000

# Reserve (free, PLAN §4.4) - not yet assigned to any spec:
D2_RESERVE_11 = 0x800  # SHARED §3: pencilled for Wild Imp Fel Firebolt 200824 - round-2 resolved
# to the scripted fallback instead (no family bit used); kept as a named reserve, not consumed.
D2_RESERVE_19 = 0x80000
D2_RESERVE_21 = 0x200000

# --- dword 3 (SpellClassMask_3 / EffectSpellClassMaskX_3) ---
INFERNO_EFFECT = 0x1
SHADOWFLAME_DOT = 0x2
UNENDING_BREATH = 0x4
DEMONIC_FRENZY = 0x8
DEMON_SKIN = 0x10
DEMONIC_CIRCLE = 0x20
WARLOCK_UTILITY = 0x40
FEL_DOMINATION = 0x80
PANDEMIC_DAMAGE = 0x100  # reclaimable once stock Pandemic 58691 is fully retired
DEVOUR_MAGIC = 0x400
CURSE_OF_TONGUES = 0x800
DEMONIC_EMPOWERMENT = 0x1000
METAMORPHOSIS = 0x2000
SOUL_LINK_AURA = 0x4000
DARK_PACT = 0x8000

# Affliction's own d3 bits 16-21 (this pass, AFFLICTION.md §2.6):
PHANTOM_SINGULARITY = 0x00010000  # bit 16 - 200730 (damage) only, the debuff 200729 carries no bit
TAINTED_SOUL = 0x00020000  # bit 17 - 200722
GRIM_REACH_BOLT = 0x00040000  # bit 18 - 200725
AGONIZING_PAIN = 0x00080000  # bit 19 - 200728
SPELL_LOCK = 0x00100000  # bit 20 - demon-only: stock pet spells Spell Lock 19244/19647
PHANTOM_SINGULARITY_CAST = 0x00200000  # bit 21 - 200729 (the castable debuff), so Reach extends it

# Demonology's d3 bits 22-27 (DEMONOLOGY.md §2.4) and Destruction's d3 bits 28-31 + d3 bit 9 -
# named here so those passes only import (PLAN §4.4).
HAND_OF_GULDAN = 0x00400000  # bit 22 - 200820, 200821
BANE_OF_DOOM = 0x00800000  # bit 23 - 200825
UNENDING_RESOLVE = 0x01000000  # bit 24 - 200826
SUMMON_DOOMGUARD = 0x02000000  # bit 25 - 200831
SUMMON_INFERNAL = 0x04000000  # bit 26 - 200833
DEMONIC_LEAP = 0x08000000  # bit 27 - 54786 (SpellClassSet 0 -> 5)
DESTRUCTION_D3_BIT_9 = 0x200  # spare (§2.4)
MOLTEN_BOLT = 0x10000000  # bit 28 (DESTRUCTION §2.4) - 200985; Emberstorm/Devastation/"Destruction
# spells" SpellMods reach it
HAVOC = 0x20000000  # bit 29 (DESTRUCTION §2.4) - 200974; only needed so Demonology's Metamorphosis
# mask (54879 aura 275) could re-enable it - that mask is now the full mask (DEMONOLOGY §11 Q2), so
# this bit is no longer load-bearing but kept, harmless
CHAOS_RIFT = 0x40000000  # bit 30 (DESTRUCTION §2.4) - 200978; same reason as HAVOC
DESTRUCTION_D3_BIT_31 = 0x80000000  # spare (§2.4)

# --- Composites (Affliction; each a (dword1, dword2, dword3) tuple for family_mask=) ---
AFFLICTION_DOTS = (0x402, 0x100, PHANTOM_SINGULARITY)  # Corruption, Bane of Agony, UA, PS -
# exactly the four DoTs Soul Siphon/Compounding Darkness count (spec §3)
SHADOW_PERIODIC = (0x440A, 0x104, PHANTOM_SINGULARITY)  # Corruption, Drain Life, Bane, Drain
# Soul; Seed DoT, UA; PS - Haunt eff3, Shadow Embrace debuffs, Soulburn: Haunt
SHADOW_MASTERY_DIRECT = (0x80091, 0x51110, 0xF0000)  # SB, Drain Mana, Shadowburn, Death Coil;
# Seed det, UA, Shadowfury, Shadowflame, Haunt; PS/TS/GR/AP bolts
SHADOW_MASTERY_DOT = (0x440A, 0x106, 0)  # + Curse of Doom, Seed DoT, UA
WARLOCK_SHADOW_DAMAGE = (0x8448B, 0x59116, 0xF0000)  # Grim Reach debuff 200724, Death's Embrace eff2
REACH_SPELLS = (0x845AF, 0x8611C6, 0x40E00000)  # every warlock damaging spell with a target range
# (§11 Q17, user): d1 SB, Corruption, Immolate, Drain Life, Rain of Fire, Shadowburn, Searing Pain,
# Bane of Agony, Drain Soul, Death Coil; d2 Curse of Doom, Seed DoT, Incinerate, Soul Fire, UA,
# Shadowfury, Chaos Bolt, Haunt, Conflagrate; d3 Phantom Singularity (cast), Hand of Gul'dan, Bane
# of Doom, Chaos Rift.
AFFLICTION_THREAT = (0x8048C41A, 0x4071E, 0xF0000)  # Siphon Power eff2
NIGHTFALL_TRIGGER = (0x400A, SHADOWFLAME, SHADOWFLAME_DOT)  # = (0x400A, 0x10000, 0x2)
SHADOW_TRANCE_CONSUMERS = (SHADOW_BOLT, SEED_OF_CORRUPTION_DOT, 0)  # = (0x1, 0x4, 0)
EVERLASTING_TRIGGER = (0x4009, 0x40008, 0)  # SB, DL, DS; Haunt, Howl
CORRUPTION_UA = (0x2, 0x100, 0)  # Malediction, Empowered Corruption (d1 part), EA eff2
SIPHON_LIFE_DOT = (0x2, 0x104, 0)
LINGERING_AGONY = (0x400, 0x100, 0)
IMPROVED_CURSES_EXH_TONGUES = (0x400000, 0, CURSE_OF_TONGUES)
FELHUNTER_UTILITY = (0, 0, SPELL_LOCK | DEVOUR_MAGIC)  # = (0, 0, 0x100400)

# --- Composites (Destruction, DESTRUCTION.md §2.5; literals given there, tuples are (d1, d2, d3)) ---
DESTRUCTION_SPELLS = (0x1E5, 0x8310C0, 0x10000002)  # SB, Immolate, RoF, Hellfire, Shadowburn,
# Searing Pain; Incinerate, Soul Fire, Shadowfury, Shadowflame, Chaos Bolt(+copies), Conflagrate;
# Shadowflame DoT, Molten Bolt
DESTRUCTION_CAST_SPELLS = (0x165, 0x200C0, 0)  # cast/channel: SB, Immolate, RoF, Hellfire, SP;
# Incinerate, Soul Fire, Chaos Bolt
EMBERSTORM_DAMAGE = (0x1E4, 0x200C0, 0x10000001)  # Immolate, RoF, Hellfire(5857), Shadowburn, SP;
# Incinerate, Soul Fire, Chaos Bolt; Inferno Effect 22703, Molten Bolt. No Conflagrate (scripted, G1)
EMBERSTORM_DOT = (0x4, 0, 0x2)  # Immolate DoT, Shadowflame DoT. No Hellfire (d1 0x40 = self dmg 1949)
# HAND_OF_GULDAN (d3 0x00400000) and SUMMON_INFERNAL (d3 0x04000000) are Demonology's (S3) own
# named constants (DEMONOLOGY.md §2.4), already folded as literals into CATACLYSM_SPELLS/
# BANE_SPELLS below by Destruction (DESTRUCTION.md Review log item 13) - Demonology's WP-0 does not
# re-derive either composite.
CATACLYSM_SPELLS = (0x60, 0x1000, 0x04400001)  # RoF, Hellfire; Shadowfury; Inferno Effect 22703;
# Demonology's Hand of Gul'dan (d3 0x00400000) and Summon Infernal (d3 0x04000000)
BANE_SPELLS = (0x5, 0x300C0, 0x00400002)  # SB, Immolate; Incinerate, Soul Fire, Shadowflame,
# Chaos Bolt; Shadowflame DoT; Hand of Gul'dan
SHADOW_AND_FLAME_SPELLS = (0x81, 0x310C0, 0x2)  # SB, Shadowburn; Incinerate, Soul Fire, Shadowfury,
# Shadowflame, Chaos Bolt; Shadowflame DoT
SOUL_LEECH_SPELLS = (0x185, 0x8200C0, 0)  # SB, Immolate (direct), Shadowburn, SP; Incinerate,
# Soul Fire, Chaos Bolt, Conflagrate
FNB_IMMOLATE_BONUS = (0x100, 0x200C0, 0)  # Immolate eff2 aura-271 scope: SP; Incinerate, Soul Fire,
# Chaos Bolt(+copies)
REACH_DESTRUCTION_ADD = (0x125, 0x200C0, 0)  # OR-ed into 200707/200708's mask (already inside
# Affliction's REACH_SPELLS - no-op, kept as documentation, DESTRUCTION.md §0.1.9)
WARLOCK_PLAYER_DAMAGE = (0x1E5, 0x8310C0, 0x2)  # = DESTRUCTION_SPELLS minus MOLTEN_BOLT (d3 bit 28
# cleared - warlock-cast triggered bolts mid-cast must never eat 200991's charge, §7.9). 200991's
# scope (player-cast spells only, never a demon bit). WP-A must OR in Affliction's own damage-spell
# composite when it builds 200991 (DESTRUCTION.md §2.5); Demonology (S3) widens this further with
# its own player-nuke bits. This literal is Destruction's own scope only - not yet widened.
INSTANT_CAST_HELPER = (0, 0x20080, 0)  # 200713's scope: Soul Fire d2 0x80, Chaos Bolt d2 0x20000

# WP-A's OR-term decision for WARLOCK_PLAYER_DAMAGE (DESTRUCTION.md §2.5's open call, WP brief):
# ORs in REACH_SPELLS - "every warlock damaging spell with a target range" (AFFLICTION §11 Q17,
# user) - rather than a narrower Affliction-only composite (AFFLICTION_DOTS/SHADOW_PERIODIC/
# SHADOW_MASTERY_DIRECT all miss some direct-cast Affliction spell; none is a true "every Affliction
# damage spell" set). REACH_SPELLS already spans every tree's damaging casts (its own d3 already
# reserves Demonology's Hand of Gul'dan/Bane of Doom/Chaos Rift bits), so this also picks up
# Demonology's player nukes for free once S3 lands, matching DESTRUCTION.md §2.5's third OR-term
# ("Demo player nukes, S3") without Destruction needing to hardcode anything Demonology-specific.
# Computed (not hand-computed hex) to avoid a transcription error - see the classmask-scoping gotcha
# in apps/dbc-tools/README.md. MOLTEN_BOLT is not reintroduced (REACH_SPELLS's d3 has no bit 28).
WARLOCK_PLAYER_DAMAGE_FULL = tuple(a | b for a, b in zip(WARLOCK_PLAYER_DAMAGE, REACH_SPELLS))

# --- Composites (Demonology, DEMONOLOGY.md §3.3) ---
# Metamorphosis 54879 eff2 aura 275, mask letter C (dbc-tools' A/B/C = eff0/1/2 gotcha) - superseded
# 2026-09-27 (user, §11 Q2 "It should be every warlock spell"): the full mask, not a Fire/Shadow
# list. Safe because aura 275 only admits spells that carry a family-5 bit - Dark Apotheosis 200835
# has none, so its own StancesNot still refuses it in Metamorphosis (§11 Q22).
META_ALLOWED = (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)

# Dark Apotheosis passive 200836 eff1 aura 275, mask letter B (= eff1) - every warlock bit except
# Metamorphosis 47241 (d3 0x2000) and Demonic Leap (DEMONIC_LEAP) - a truly full mask would let
# those two skip CheckShapeshift and swap form mid-DA / work outside Metamorphosis (§5.2).
DA_ALLOWED = (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF & ~(0x2000 | DEMONIC_LEAP))

# --- spell_proc constants (priest/druid precedent; values verified against SpellMgr.h:111-280) ---
PROC_FLAG_KILL = 0x2
PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x10000
PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG = 0x20000  # DESTRUCTION §8 -30299 Nether Protection
PROC_FLAG_DONE_PERIODIC = 0x40000
PROC_FLAG_TAKEN_PERIODIC = 0x80000  # DESTRUCTION §8 -30299 Nether Protection
PROC_SPELL_TYPE_DAMAGE = 1
PROC_SPELL_TYPE_MASK_ALL = 7
PROC_SPELL_PHASE_CAST = 1
PROC_SPELL_PHASE_HIT = 2
PROC_HIT_CRITICAL = 2
PROC_ATTR_REQ_EXP_OR_HONOR = 0x1
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2
PROC_ATTR_REQ_SPELLMOD = 0x8
