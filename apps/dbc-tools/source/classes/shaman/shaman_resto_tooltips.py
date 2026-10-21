"""
Shaman Restoration - tooltip variable entries 1220-1224 (S2a A4).

Own module with NO sibling imports on purpose: shaman_trigger_spells imports shaman_restoration, which needs these
entries, and shaman_totems imports shaman_trigger_spells, so defining them in shaman_totems made an import cycle
(restoration -> totems -> trigger_spells -> restoration). Every spell file imports from here.
"""

from lib.dsl.registry import product, talent_mult, tooltip_vars

# tooltip_vars 1220-1224 (S2a A4; S2-NOTES section 5): unconditional Restoration-tree % talents on the healing
# tooltips, bare rank ids (the talent file imports the spell files). Left out: Totemic Resonance (a count), Tidal
# Force, Undulation, Riptide's +25%, Nature's Blessing (healing power), cross-tree talents. All of them live here
# (not beside their spells) so shaman_spells / shaman_area_spells / shaman_elementals / the Restoration file can all
# import them without a cycle. Effect numbers are 1-based. Healing Way 29206/29205/29202 eff1 = DAMAGE (+ DOT eff2);
# Purification 16178/16210/16211 eff1 = DAMAGE (+ DOT eff2); Improved Earth Shield 51560/51561/202653 eff2 = the
# DAMAGE effect (eff1 = charges; core forces its misc, S2a-0VERIFY X2).
shaman_waves_1220 = tooltip_vars(
    1220, "Healing Wave / Lesser Healing Wave: Improved Healing Wave, Tidal Waves heal, Purification",
    ihw=talent_mult([16182, 16226, 16227], effect=1),
    twh=talent_mult([51562, 51563, 51564], effect=1),
    pur=talent_mult([16178, 16210, 16211], effect=1),
    mult=product('ihw', 'twh', 'pur'),
)
shaman_chainheal_1221 = tooltip_vars(
    1221, "Chain Heal: Healing Way, Improved Chain Heal, Purification",
    hwy=talent_mult([29206, 29205, 29202], effect=1),
    ich=talent_mult([30872, 30873], effect=1),
    pur=talent_mult([16178, 16210, 16211], effect=1),
    mult=product('hwy', 'ich', 'pur'),
)
shaman_rain_1222 = tooltip_vars(
    1222, "Healing Rain pulse (rain): Healing Way, Rainfall, Purification; Riptide and the torrent (tide): Healing Way, "
          "Torrent, Purification",
    hwy=talent_mult([29206, 29205, 29202], effect=1),
    rnf=talent_mult([202643, 202644], effect=1),
    trt=talent_mult([30864, 30865], effect=1),
    pur=talent_mult([16178, 16210, 16211], effect=1),
    rain=product('hwy', 'rnf', 'pur'),
    tide=product('hwy', 'trt', 'pur'),
)
shaman_shield_1223 = tooltip_vars(
    1223, "Earth Shield heal per charge: Healing Way, Improved Earth Shield, Purification",
    hwy=talent_mult([29206, 29205, 29202], effect=1),
    ies=talent_mult([51560, 51561, 202653], effect=2),
    pur=talent_mult([16178, 16210, 16211], effect=1),
    mult=product('hwy', 'ies', 'pur'),
)
shaman_healtotems_1224 = tooltip_vars(
    1224, "Healing Stream (hst), Undulating Currents (uct) and the Water Bolt heal (wel): Improved Healing Stream / "
          "Kindling / Tidecaller, each with Purification",
    ihs=talent_mult([29187, 29189, 29191], effect=1),
    kin=talent_mult([202650, 202651], effect=1),
    tdc=talent_mult([202648, 202649], effect=1),
    pur=talent_mult([16178, 16210, 16211], effect=1),
    hst=product('ihs', 'pur'),
    uct=product('kin', 'pur'),
    wel=product('tdc', 'pur'),
)
