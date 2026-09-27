"""
Druid - named SpellFamilyFlags (SpellClassMask_{1,2,3} / EffectSpellClassMask{A,B,C}_{1,2,3})
constants, shared across the Balance/Feral/Resto rework passes.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from ._masks import STARSURGE, ...`.

Bit values below are the raw SpellFamilyFlags dword contents (already the "final" masked value a
row's SpellClassMask_N / EffectSpellClassMaskX_N column would carry), not bit positions. Sourced
from the existing stock druid rows in druid_spells.py/druid_trigger_spells.py (dword 1/2/3 stock
bits) and .agents/plans/druid-rework/druid-rework.PLAN.md §4.4 (dword 3 custom-spell bits, one
named constant per row of that table; created in the Balance pass's WP-0, extended - never
retyped - by later passes).

Created by Balance WP-0 (druid-rework.BALANCE.md §3 item 2, PLAN §4.4/§6 item 2). Holds every
stock constant the three spec files list plus every custom bit (including Feral's and Resto's),
so later passes only import.
"""

# --- dword 1 (SpellClassMask_1 / EffectSpellClassMaskX_1) ---
WRATH = 0x1  # 5176
MOONFIRE = 0x2  # 8921
STARFIRE = 0x4  # 2912, and also the Balance cleave 200337 (shares this bit deliberately)
REJUVENATION = 0x10  # 774
HEALING_TOUCH = 0x20  # 5185
REGROWTH = 0x40  # 8936
TRANQUILITY = 0x80  # 740, tick 44203
THORNS = 0x100  # 467
ENTANGLING_ROOTS = 0x200  # 339, 19975
FAERIE_FIRE = 0x400  # 770
INSECT_SWARM = 0x200000  # 5570, and the Balance Swarming Rot copy 200352
HURRICANE = 0x400000  # 16914, tick 42231

# --- dword 2 (SpellClassMask_2 / EffectSpellClassMaskX_2) ---
SWIFTMEND = 0x2  # 18562
LIFEBLOOM = 0x10  # 33763
CYCLONE = 0x20  # 33786
FORCE_OF_NATURE = 0x200  # 33831
INNERVATE = 0x1000  # 29166
MOONKIN_FORM = 0x2000  # 24858
BARKSKIN = 0x40000  # 22812
STARFALL = 0x800000  # 48505, 50288, 50294
TYPHOON = 0x1000000  # 50516, 61391
NOURISH = 0x2000000  # 50464 - RETIRED (druid-rework.PLAN.md §3 item 6 / BALANCE §0.10):
# the stock Nourish clauses stay in core and key on this bit. Never reassign it.
WILD_GROWTH = 0x4000000  # 48438
NATURAL_ALACRITY = 0x80000  # stock Nature's Swiftness 17116, reused baseline (RESTO §0.1/§2.4) - no new bit

# --- dword 3 (SpellClassMask_3 / EffectSpellClassMaskX_3) ---
STARFALL_TARGETING = 0x100  # 50286
ECLIPSE_BUFF = 0x4000  # 48517/48518

# PLAN §4.4 - one named constant per row, in bit order. Balance's own three bits:
STARSURGE = 0x00400000  # bit 22 - Starsurge 200333
MASS_ENTANGLEMENT = 0x00800000  # bit 23 - Mass Entanglement 200334
FURY_OF_ELUNE = 0x01000000  # bit 24 - Fury of Elune beam 200338 + splash 200339 (cast 200336 carries no bit)

# Feral's bits (owned by the Feral pass; named here now so later passes only import, PLAN §4.4).
IRONFUR = 0x02000000  # bit 25 - Ironfur 200420
PULVERIZE = 0x04000000  # bit 26 - Pulverize 200421 + Savage Bite 200439 (shared, FERAL-ADDENDUM §3.3
# user decision: Savage Bite reuses Pulverize's bit instead of the last dword-1 reserve bit, so it
# also gets Nurturing Instinct's buff (already in NURTURING_INSTINCT_DAMAGE below) and Splintering
# Blows (druid_trigger_spells.py). Any future PULVERIZE-scoped SpellMod reaches Savage Bite too.)
THRASH = 0x08000000  # bit 27 - Thrash 200423
UPHEAVAL = 0x00020000  # bit 17 - Upheaval 200422 (reclaimed from the orphaned Improved Barkskin
# passive 66530 - strip it from 66530 when the Feral pass lands)

# Resto's bits (owned by the Resto pass; named here now so later passes only import, PLAN §4.4).
BLOOM = 0x10000000  # bit 28 - Bloom 200560 + Bloom jump 200561
CENARION_WARD = 0x20000000  # bit 29 - Cenarion Ward 200562 and its released HoT 200563 (shared)
CENARION_WARD_HOT = CENARION_WARD  # alias (RESTO §0.1): the ward and its released heal share one bit
CULTIVATION = 0x40000000  # bit 30 - Cultivation 200567
YSERAS_GIFT = 0x80000000  # bit 31 - Ysera's Gift heal 200569
# Germination (200568) gets NO new bit - it deliberately shares REJUVENATION's bit (dword 1 0x10)
# so every Rejuvenation SpellMod applies to it too; code tells it apart from 774 by spell id, not
# by mask (RESTO §0.1/§2.4).
# Flourish (200564) gets NO bit at all - no SpellMod ever needs to scope to it (RESTO §0.1).

# Every free druid dword-3 bit is now allocated (PLAN §4.4). Dword 1 bit 26 (0x4000000, NPC-only
# 9033) is the only remaining reserve, a last resort.

# --- Composite (dword1, dword2, dword3) tuples (BALANCE §3 item 2) ---

# Every druid magic-damage spell: Wrath, Moonfire, Starfire, Thorns, Entangling Roots, Insect
# Swarm, Hurricane, Starfall, Typhoon, Starsurge, Fury of Elune.
DRUID_SPELL_DAMAGE = (0x600307, 0x1800000, STARSURGE | FURY_OF_ELUNE)

# Nature's Grace's own (-16880) trigger family mask. Stock 16880 already uses (0x67, 0x3800002).
NG_TRIGGER = (0x67, 0x3800002, STARSURGE)

# Genesis's DoT scope: Moonfire, Rejuvenation, Regrowth, Entangling Roots, Insect Swarm (dword 1);
# Lifebloom, Wild Growth (dword 2); Resto's new HoTs, included now per PLAN §0.10 so Resto never
# re-edits Genesis (Cenarion Ward's released HoT and Cultivation - Bloom/Ysera's Gift are direct
# heals, not DoTs/HoTs, so they stay out of this composite).
GENESIS_DOT = (0x200252, 0x4000010, CENARION_WARD | CULTIVATION)

# Genesis's damage-tick scope: Tranquility tick 44203, Hurricane tick 42231.
GENESIS_TICKS = (0x400080, 0, 0)

# Moonglow's re-scoped cost reduction: Wrath, Starfire, Healing Touch, Regrowth (dword 1);
# Swiftmend (dword 2); Starsurge (dword 3).
MOONGLOW_SPELLS = (0x65, 0x2, STARSURGE)

# Nature's Reach's range scope: Wrath, Starfire, Entangling Roots, Hurricane (dword 1); Cyclone
# (dword 2); Mass Entanglement (dword 3).
NATURES_REACH = (0x400205, 0x20, MASS_ENTANGLEMENT)

# Earth and Moon's proc trigger family scope: Wrath, Moonfire (dword 1); Starsurge (dword 3).
EM_TRIGGER = (0x5, 0, STARSURGE)

# Resto composites (RESTO §0.1/§2.4; WP-0 item 2). Third element ORs in the dword-3 bit(s).
# Identical to stock Natural Shapeshifter's own A-mask scope (all four forms).
SHAPESHIFT_FORMS = (0xE0000000, 0x0001E000, 0)
# The SPELLMOD_DAMAGE side of Resto's healing bucket: direct Nature heals, Classic list.
DIRECT_NATURE_HEAL = (HEALING_TOUCH | REGROWTH, SWIFTMEND, BLOOM)
# The full "direct heal" SPELLMOD_DAMAGE scope (Gift of Nature, Natural Alacrity/Shapeshifter buffs).
HEAL_DIRECT = (HEALING_TOUCH | REGROWTH | TRANQUILITY, SWIFTMEND | LIFEBLOOM, BLOOM | YSERAS_GIFT)
# The SPELLMOD_DOT side of the same bucket.
HEAL_DOT = (REJUVENATION | REGROWTH, LIFEBLOOM | WILD_GROWTH, CENARION_WARD_HOT | CULTIVATION)
# Core-HoT cost scope (Deep Roots capstone reads this list directly in C++, not as a SpellMod mask,
# but Tree of Life's -20% HoT cost SpellMod (5420 eff1) is scoped to this).
CORE_HOT_CAST = (REJUVENATION | REGROWTH, LIFEBLOOM | WILD_GROWTH, CENARION_WARD)
# Empowered Rejuvenation's BONUS_MULTIPLIER scope: Rejuvenation/Germination (shared bit), Lifebloom,
# Wild Growth, Cenarion Ward's released heal. Regrowth is excluded - handled in C++ (RESTO §8 (5,1)).
EMP_REJUV_COEFF = (REJUVENATION, LIFEBLOOM | WILD_GROWTH, CENARION_WARD_HOT)

# --- Proc constants (BALANCE §3 item 2; per-file convention like priest's own DSL files) ---
PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x4  # RESTO §0.3 item 7 (Omen of Clarity)
PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK = 0x8
PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x10  # RESTO §0.3 item 7
PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS = 0x20
PROC_FLAG_DONE_RANGED_AUTO_ATTACK = 0x40  # RESTO §0.3 item 7
PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS = 0x100  # RESTO §0.3 item 7
PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x1000  # RESTO §0.3 item 7
PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x4000
PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x10000
PROC_FLAG_DONE_PERIODIC = 0x40000
PROC_FLAG_TAKEN_DAMAGE = 0x100000  # RESTO §6 (Cenarion Ward release: melee + spell + periodic damage taken)
PROC_SPELL_TYPE_DAMAGE = 1
PROC_SPELL_TYPE_HEAL = 2
PROC_SPELL_PHASE_CAST = 1
PROC_SPELL_PHASE_HIT = 2
PROC_HIT_NORMAL = 1
PROC_HIT_CRITICAL = 2
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2

# --- Feral stock bits (druid-rework FERAL §3a; added by the Feral pass's WP-0, checked against the
# stock Spell.dbc rows 2026-09-24). Every value is the raw SpellFamilyFlags dword content. ---

# dword 1
DEMORALIZING_ROAR = 0x8  # 99
MAUL = 0x800  # 6807
RAKE = 0x1000  # 1822
BASH = 0x2000  # 5211
SHRED = 0x8000  # 5221
RAVAGE = 0x10000  # 6785
POUNCE = 0x20000  # 9005 (its bleed 9007 has no SpellFamily at all - no SpellMod reaches it)
ENRAGE = 0x80000  # 5229
RIP_FEROCIOUS_BITE = 0x800000  # 1079 AND 22568 share this bit - target Rip alone with RIP (dword 3)
BEAR_FORM = 0x40000000  # 5487, 9634
CAT_FORM = 0x80000000  # 768

# dword 2
FERAL_CHARGE_BEAR_D2 = 0x1  # 16979 (also dword 3 FERAL_CHARGE_BEAR_D3)
MANGLE_BEAR = 0x40  # 33878
MAIM = 0x80  # 22570
LACERATE = 0x100  # 33745
MANGLE_CAT = 0x400  # 33876
SWIPE_BEAR = 0x100000  # 779
SAVAGE_ROAR = 0x10000000  # 52610
COWER = 0x20000000  # 8998
FRENZIED_REGENERATION = 0x40000000  # 22842

# dword 3
CHALLENGING_ROAR = 0x1  # 5209
BEAR_FORM_PASSIVE = 0x2  # 1178, 9635 (and the orphaned Improved Barkskin passive 66530)
FERAL_CHARGE_BEAR_D3 = 0x10  # 16979
FERAL_CHARGE_CAT = 0x20  # 49376
BERSERK = 0x40  # 50334
SURVIVAL_INSTINCTS = 0x80  # 61336
SWIPE_CAT = 0x400  # 62078
TIGERS_FURY = 0x800  # 5217
CLAW = 0x40000  # 1082
RIP = 0x200000  # 1079 only

# --- Feral composites (druid-rework FERAL §7 with WP-BRIEF §3; added by the Feral pass's WP-A) ---

# The feral bleeds a SpellMod can reach: Rake (direct + bleed), Lacerate, Rip (its Rip-only dword 3
# bit - dword 1 0x800000 is shared with Ferocious Bite), Thrash. Pounce's bleed 9007 has no family.
# Infected Wounds eff1 (DOT) and Primal Gore eff0 (CRIT_DAMAGE_BONUS).
FERAL_BLEEDS = (RAKE, LACERATE, RIP | THRASH)

# Berserk 50334 eff0's -50% cost scope (FERAL §7 (10,1)): the stock cat scope plus Maul, Demoralizing
# Roar, Mangle (Bear), Lacerate, Swipe (Bear), Feral Charge (Bear) and the four new bear abilities.
BERSERK_COST = (
    RIP_FEROCIOUS_BITE | POUNCE | RAVAGE | SHRED | RAKE | MAUL | DEMORALIZING_ROAR,
    SAVAGE_ROAR | COWER | SWIPE_BEAR | MANGLE_CAT | LACERATE | MAIM | MANGLE_BEAR | FERAL_CHARGE_BEAR_D2,
    CLAW | SWIPE_CAT | FERAL_CHARGE_CAT | CHALLENGING_ROAR | IRONFUR | PULVERIZE | UPHEAVAL | THRASH,
)

# Nurturing Instinct's empowered buff 200430 (FERAL §7 (4,3)): "any feral damage ability" -
# eff0 DAMAGE on the direct hits, eff1 DOT on the bleeds.
NURTURING_INSTINCT_DAMAGE = (
    RIP_FEROCIOUS_BITE | POUNCE | RAVAGE | SHRED | RAKE | MAUL,
    SWIPE_BEAR | MANGLE_CAT | LACERATE | MAIM | MANGLE_BEAR,
    CLAW | SWIPE_CAT | PULVERIZE | UPHEAVAL | THRASH,
)
NURTURING_INSTINCT_DOT = (RIP_FEROCIOUS_BITE | RAKE, LACERATE, RIP | THRASH)

# Infected Wounds' proc trigger scope (procs_on(-48483), FERAL §7 (7,3)): Shred, Maul, Swipe (both), Mangle (both).
INFECTED_WOUNDS_TRIGGER = (SHRED | MAUL, SWIPE_BEAR | MANGLE_CAT | MANGLE_BEAR, SWIPE_CAT)
