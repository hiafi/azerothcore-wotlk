"""
Shaman Enhancement - tooltip variable entries 1217-1219 (S3a A3; S3-NOTES section 6, S3a-WP-BRIEF item 19).

Own module with NO sibling imports on purpose (the shaman_resto_tooltips.py precedent): shaman_spells, shaman_trigger_spells and
shaman_enhancement all need these entries and import them from here, so no import cycle. Unconditional Enhancement-tree % talents
only, bare talent rank ids. Effect numbers are 1-based and match A2's rank rows: Improved Lightning Shield / Static Shock effect 1 =
the orb damage SpellMod, Elemental Weapons / Improved Windfury / Spirit Weapons effect 1 = the damage SpellMod, Guardian Totems
effect 3 = the Living Earth absorb SpellMod. Variable names are at most 12 chars (talent_mult adds <name>1 / <name>2).
"""

from lib.dsl.registry import product, talent_mult, tooltip_vars

# 1217: Lightning Shield 324 (the orb number, 26364's pot_text): `{pot1*mult}`.
shaman_lshield_1217 = tooltip_vars(
    1217, "Lightning Shield orb: Improved Lightning Shield, Static Shock",
    ils=talent_mult([16261, 16290, 51881], effect=1),
    ssh=talent_mult([51525, 51526, 51527], effect=1),
    mult=product('ils', 'ssh'),
)
# 1218: Flametongue 8024 / Frostbrand 8033 hit numbers read `{pot1*mult}` (Elemental Weapons); Windfury 8232 reads `{pot1*wf}`
# (Elemental Weapons x Improved Windfury x Spirit Weapons).
shaman_imbuehits_1218 = tooltip_vars(
    1218, "Imbue hits: mult = Elemental Weapons (Flametongue, Frostbrand); wf = Elemental Weapons, Improved Windfury, Spirit Weapons (Windfury)",
    mult=talent_mult([16266, 29079, 29080], effect=1),
    iwf=talent_mult([29192, 29193], effect=1),
    spw=talent_mult([16268, 202373, 202374], effect=1),
    wf=product('mult', 'iwf', 'spw'),
)
# 1219: Living Earth 202361: `{pot1*gt}` (Guardian Totems, effect 3).
shaman_livearth_1219 = tooltip_vars(
    1219, "Living Earth absorb: Guardian Totems (effect 3)",
    gt=talent_mult([16258, 16293], effect=3),
)
