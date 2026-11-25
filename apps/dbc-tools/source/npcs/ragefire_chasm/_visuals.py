"""
Ragefire Chasm build, WP V: the visual ids the boss files use, one place (not loaded on its own: the leading underscore
keeps the package loader from treating it as a declaration file; boss files import it with
`from ._visuals import ...`, like `_common.py` and scarlet_monastery/_visuals.py). A boss WP asks for a change in its
report; nobody else edits this file.

Source: .agents/plans/ragefire-chasm-build/ragefire-chasm-build.VISUALS-REPORT.md (VR: "Per-boss id list" and Part 1;
ids, kits, mesh bounds and textures read, nothing rendered, so every look is unconfirmed until seen in game) and the
top pick of each row (handoff s3.10, user ruling 2026-11-24 on s7 #37 and #19: every top pick approved, the WRONG doc
looks replaced). VR numbered its minted rows 90700-90706; the build uses its own slice, 90370-90399 (ids.yaml
reservation `ragefire_chasm`): VR 90700 = 90370, 90701 = 90371, 90703-90706 = 90373-90376. Row 90372 (the Ascension
blood lake) is NOT shipped (s7 #37): the red aura SV 90554 plays instead.

Four kinds of constant:

- MINTED (client patch-M, by apps/dbc-tools/patch_ragefire_chasm_vfx_models.py): the `SV_*` names in the first section.
  They must equal the patch script's constants (lib/test_ragefire_chasm_vfx.py pins it). Two Ascension models ship into
  patch-M for the Felstorm row (`--extract` pulls them).
- SHIPPED (already in patch-M or the working copy: Scarlet Monastery, Blackrock Depths / Spire): nothing ships for them;
  the dry run checks they exist in the working-copy DBCs. Names start with `SHIPPED_`.
- STOCK: ids that already exist in the 3.3.5 client. Nothing ships and no id is minted.
- TELEGRAPH MARKERS (kit displays 91000-93999) are not named here: the boss files use the mod-boss-mechanics registry
  kinds and `Color(...)`, never a display id.

Prefixes tell the table of an id: `SV_` / `SHIPPED_` / `<boss code>_` are SpellVisual ids, `DISPLAY_` creature
displays, `GODI_` gameobject displays, `ITEM_` item entries, `IDI_` item displays. `*_ALT` / `*_FALLBACK` names are the
VR alternates (one-constant swaps if the playtest rejects the pick).

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A STATE look plays on every unit that
carries the aura. An impact kit plays once, so a lasting effect re-casts it every 2-3 s or uses the lasting twin named
here. Boss codes (the spec's mechanic id prefixes): OG Oggleflint, JR Jergosh, BZ Bazzalan, TG Taragaman (HM = hard mode
pieces of his fight, kept under TG_).

Ids that must NOT be wired are listed in the test (WRONG_*): Borer trail SV 8719 (an animation), eruption SV 7396
(blood), Fel Flames SV 8143 (not a ground burst), Devour 8923 as the channel (it is the bite), globule CDI 17200 and
mound CDI 15294 as a model (invisible stalkers; 15294 is only the carrier).
"""

# --- Minted (patch-M) -------------------------------------------------------------------------------------------------

# Felstorm (TG): StateKit, AnimID 126 (the Felguard owns it) + the Ascension bladestorm ribbons (Base) and fel wreath
# (Chest): ONE look for the 8 / 10 yd storm; the ring marker carries the radius. Fallback: the stock Whirlwind state.
SV_FELSTORM = 90370
SV_FELSTORM_FALLBACK = 6044
# Fel spot / fel pulse eruption (TG): ImpactKit with `fel_firenova_area` (Base) + `fel_hellfire_impact_base` (Chest).
# 90372 is deliberately unused (the blood lake is not shipped, s7 #37).
SV_FEL_SPOT = 90371
SV_FEL_SPOT_FALLBACK = 9004
# Bazzalan's swings: copies of the stock spell visuals whose cast kit asks for an animation the Satyr model lacks
# (anim 57 / 126 missing) with a clip it has (17 / 54). The impact kits are the stock ones.
SV_EVISCERATE = 90373        # copy of SV 671, cast kit AnimID 57 -> 17
SV_RUPTURE = 90374           # copy of SV 250, cast kit AnimID 57 -> 17
SV_ENVENOM = 90375           # copy of SV 8144, cast kit AnimID 57 -> 17
SV_FAN_OF_KNIVES = 90376     # copy of SV 12317, cast kit AnimID 126 -> 54

# Scale hints set on the creature or the GO template, not in the DBC (floats on purpose: not ids).
BORER_ERUPT_SCALE_RANGE = (0.5, 0.7)    # CDI 11010 is a 7.7 yd Worm: 0.5 = about 3.9 yd long, pops in flat
SOUL_WISP_SCALE = 1.75                  # CDI 12432 is 0.7 x 1.4 x 1.4 yd: 1.75 reads as a 2 yd presence
SEARING_SPIKE_SIZE = 2.0                # GODI 5073, fixed yaw, both difficulties (s7 #19 A); fallback GODI 3711 at 0.8
SEARING_SPIKE_ALT_SIZE = 0.8
TITHE_SCALE_STEP = 0.04                 # Jergosh grows 4% of his scale per Tithe stack, at most 5 steps
TITHE_SCALE_MAX_STEPS = 5

# --- Shipped (patch-M and the working copy) ---------------------------------------------------------------------------

SHIPPED_RED_AURA = 90554                # Scarlet Monastery: `deathknight_plaguestrikestatered` STATE (hard mode aura)
SHIPPED_SHADOW_POOL_4 = 90601           # Blackrock Spire shadow patch STATE, 4 yd, on a stalker (the offering spot)
SHIPPED_PURPLE_RING = 90657             # Blackrock Depths purple ring, 3.8 yd (alt offering spot)

# ===== Oggleflint =====

OG_BORER_TRAIL = 14013              # `burrowearth_brown_missile` STATE on the carrier (a dirt spray following the unit)
OG_BORER_TRAIL_ALT = 14230
OG_BORER_ERUPTION = 7443            # BurrowEarth_Brown_Missile area kit cast at the Borer's own spot
OG_BORER_ERUPTION_ALT = 12718       # Ground Spike (rock)
OG_CLUB_SWING = 219                 # Cleave_Cast_Base arc + anim 57 (item 3350 is a 1H mace)
OG_CLUB_SWING_ALT = 399             # a knockdown impact (121): RISKY, never the primary
OG_BEATING_BLOW = 2643              # cast anim 16 + camera shake 7, impact anim 121 + shake 3
OG_BEATING_BLOW_ALT = 8083          # Ground Slam, ThunderClap ring 6.9 yd
DISPLAY_OGGLEFLINT = 11611          # Troglodyte, stock
DISPLAY_BORER_TUNNEL = 15294        # the invisible carrier (InvisibleStalker x2.25): NEVER shown as a model
DISPLAY_BORER_ERUPT = 11010         # `Worm.mdx` (no emerge animation), creature scale BORER_ERUPT_SCALE_RANGE

# ===== Jergosh =====

JR_IMMOLATE = 46                    # fire hands + lasting Immolate_State_Base
JR_CONFLAGRATION_BURST = 5199       # fire hands + Fire_ImpactDD_High_Chest
JR_DRAIN_SOUL = 12656               # Ghost2purple_Chain channel boss -> victim (victim state needs a dummy aura)
JR_DRAIN_SOUL_ALT = 788             # the SM Vishas pick, Beam_Purple
JR_SOUL_TEAR = 7180                 # Spirit Burst at the channel's end, when the wisp spawns
JR_SOUL_TEAR_ALT = 358              # Soul Shatter
JR_SOUL_SICK = 561                  # Cripple_State_Chest STATE on the owner (the healing-reduction curse)
JR_SOUL_SICK_ALT = 886              # Ghost_state
JR_TITHE = 11821                    # hungerforblood_state on Jergosh; stacks = creature scale (TITHE_SCALE_STEP)
JR_TITHE_ALT = 6943                 # Berserking
JR_OFFERING_SPOT = SHIPPED_SHADOW_POOL_4      # a stalker casts it at the spot
JR_OFFERING_SPOT_ALT = SHIPPED_PURPLE_RING
DISPLAY_JERGOSH = 11429             # orc male, ext 8143, stock
DISPLAY_SOUL_WISP = 12432           # `Wisp.mdx`, creature scale SOUL_WISP_SCALE

# ===== Bazzalan =====

BZ_SINISTER_STRIKE = 253            # cast anim 17 (the Satyr has it)
BZ_EVISCERATE = SV_EVISCERATE
BZ_EVISCERATE_FALLBACK = 671        # hands play, no swing animation
BZ_RUPTURE = SV_RUPTURE
BZ_RUPTURE_FALLBACK = 250
BZ_RUPTURE_STATE = 15286            # lasting twin: BloodBoil_Impact_Chest STATE on the bleeding carrier
BZ_FAN_OF_KNIVES = SV_FAN_OF_KNIVES
BZ_FAN_OF_KNIVES_FALLBACK = 12317
BZ_ENVENOM = SV_ENVENOM
BZ_ENVENOM_FALLBACK = 8144
BZ_SHADOWSTEP = 8262                # cast again at the landing
BZ_POISON = 5100
BZ_POISON_STATE = 14987             # lasting green Corrosion dot state on the tank
BZ_COMBO_FLASH = 254                # optional
DISPLAY_BAZZALAN = 2007             # Satyr; animations 57 and 126 missing

# ===== Taragaman =====

TG_FEAST_MARK = 3239
TG_LEAP = 5162                      # cast again at the landing
TG_BITE = 8923
TG_DEVOUR_CHANNEL = 7270            # Blood Siphon beam (never 8923 as a channel)
TG_DEVOUR_CHANNEL_ALT = 9006        # Pounce
TG_FELSTORM = SV_FELSTORM
TG_FELSTORM_FALLBACK = SV_FELSTORM_FALLBACK
TG_FELSTORM_ALT = 8182              # Whirlwind state without cast / impact
TG_FELSTORM_ALT_2 = 7428            # Cyclone_State 5.0 x 4.2 x 6.9 yd at 0.75, anim 126
TG_FEL_PULSE = 8092
TG_FEL_PULSE_ALT = 8425
TG_FEL_SPOT = SV_FEL_SPOT
TG_FEL_SPOT_FALLBACK = SV_FEL_SPOT_FALLBACK
TG_FEL_SPOT_ALT = 8613              # fel_firenova_area impact on the stalker
TG_SPIKE_RISE = 12718               # + TG_SPIKE_RISE_DIRT at the same spot
TG_SPIKE_RISE_DIRT = 7443
TG_NOVA = 963
TG_NOVA_CAST = 8349                 # optional lasting look during the cast
TG_HM_AURA = SHIPPED_RED_AURA       # hard mode aura (SM red aura; the blood lake row 90372 is not shipped)
TG_BLOOD_LAKE = SHIPPED_RED_AURA    # phase 2 flavor, a stalker aura at each arm end (s7 #37: 90554 instead of 90372)
TG_GLOBULE_BURST = 15253            # blood_rain_impact ground impact
TG_GLOBULE_BURST_ALT = 9312         # BloodyExplosion
TG_POUR = 15253                     # the pour at the plateau's foot
DISPLAY_TARAGAMAN = 7970
DISPLAY_BLOOD_GLOBULE = 8573        # `SlimeLesser` crimson (no client patch); never CDI 17200 (invisible stalker)
DISPLAY_BLOOD_GLOBULE_ALT = 30845
DISPLAY_BLOOD_GLOBULE_ALT_2 = 2028
GODI_SEARING_SPIKE = 5073           # GO template size SEARING_SPIKE_SIZE, fixed yaw (s7 #19 A)
GODI_SEARING_SPIKE_ALT = 3711       # Lavarock at size SEARING_SPIKE_ALT_SIZE
GODI_HM_OBJECT = 328                # the Blood Shrine
GODI_HM_OBJECT_ALT = 216
ITEM_VIAL = 23894                   # the Vial of Taragaman's Blood is a clone of this item
IDI_VIAL = 15711
IDI_VIAL_ALT = 34815

# ===== Shared =====

DISPLAY_INVISIBLE_STALKER = 11686   # the stalker skin every kit helper wears
DISPLAY_RFC_ENTRANCE_ORC = 4259     # quest NPC, faction 35
DISPLAY_RFC_ENTRANCE_ORC_ALT = 4602

# Every minted SpellVisual (checked against the patch script's rows, not the stock DBCs)
MINTED_SPELL_VISUALS = (SV_FELSTORM, SV_FEL_SPOT, SV_EVISCERATE, SV_RUPTURE, SV_ENVENOM, SV_FAN_OF_KNIVES)
# Minted creature displays: none (VR reserves 90830-90839, nothing is needed)
MINTED_CREATURE_DISPLAYS = ()
# Not in the stock client but already shipped (checked against the working-copy SpellVisual.dbc)
SHIPPED_SPELL_VISUALS = (SHIPPED_RED_AURA, SHIPPED_SHADOW_POOL_4, SHIPPED_PURPLE_RING)


def _spell_visuals() -> set[int]:
    """Every SpellVisual id named above by a boss-code constant (any int constant whose prefix is a boss code)."""
    values = set()
    for name, value in globals().items():
        if name.startswith(("OG_", "JR_", "BZ_", "TG_")) and type(value) is int:
            values.add(value)
    return values


# Every stock SpellVisual id above (the SpellVisual existence check): the boss-code constants minus minted and shipped.
STOCK_SPELL_VISUALS = tuple(sorted(_spell_visuals() - set(MINTED_SPELL_VISUALS) - set(SHIPPED_SPELL_VISUALS)))
STOCK_CREATURE_DISPLAYS = tuple(sorted({
    value for name, value in globals().items() if name.startswith("DISPLAY_") and type(value) is int
}))
STOCK_GAMEOBJECT_DISPLAYS = tuple(sorted({
    value for name, value in globals().items() if name.startswith("GODI_") and type(value) is int
}))
