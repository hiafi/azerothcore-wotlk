"""
Zul'Farrak build, WP V: the visual ids the boss files use, one place (not loaded on its own: the leading underscore
keeps the package loader from treating it as a declaration file; boss files import it with
`from ._visuals import ...`, like `_common.py` and ragefire_chasm/_visuals.py). A boss WP asks for a change in its
report; nobody else edits this file.

Source: .agents/plans/zul-farrak-build/zul-farrak-build.VISUALS-REPORT.md and handoff appendix C3 (ids, kits, mesh
bounds and textures read, nothing rendered, so every look is unconfirmed until seen in game) with the user rulings of
handoff s10 (s7 ruled as recommended: every top pick approved, the WRONG doc looks replaced).

Four kinds of constant:

- MINTED (client patch-M, by apps/dbc-tools/patch_zul_farrak_vfx_models.py): `SV_*` and `DISPLAY_*_DISC` here. They
  must equal the patch script's constants (lib/test_zul_farrak_vfx.py pins it). VISUALS-REPORT's own numbering is kept
  (90700-90707 and 90830-90832), all inside the reserved blocks of ids.yaml `zul_farrak`.
- SHIPPED (already in patch-M or the working copy: Deadmines / Scarlet Monastery / Blackrock): nothing ships for them.
  Names start with `SHIPPED_`.
- STOCK: ids that already exist in the 3.3.5 client. Nothing ships and no id is minted.
- TELEGRAPH MARKERS (kit displays 91000-93999) are not named here: the boss files use the mod-boss-mechanics registry
  kinds and `Color(...)`, never a display id.

Prefixes tell the table of an id: `SV_` / `SHIPPED_` / `<boss code>_` are SpellVisual ids, `DISPLAY_` creature displays,
`GODI_` gameobject displays. A few boss-code names hold something that is NOT a SpellVisual id (a creature display, an
entry, an aura or invisibility type): `NOT_SPELL_VISUAL_NAMES` lists them, and the derived tuples skip them. `*_ALT` /
`*_FALLBACK` names are the VR alternates (one-constant swaps if the playtest rejects the pick; `_ALT_2` a second one).

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A STATE look plays on every unit that
carries the aura. An impact kit plays once, so a lasting effect re-casts it every 2-3 s or uses the lasting twin named
here (the `*_STATE` names). Boss codes (the spec's mechanic id prefixes): TK Theka, AS Antu'sul, ZR Zum'rah, PY the
Pyramid, BC Bly's crew, UK Ukorz and Ruuzlu, GZ Velratha and Gahz'rilla.

Ids that must NOT be wired are listed in the test (WRONG_*): gaze SV 3641 (no beam), swarm SV 8325 and 7621 (a 43 yd
dome), hunt SV 11778 (no model), Mojo Puddle SV 12189 and Permafrost SV 14068 as sheets, Shackle SV 68, Sacrifice
SV 107, Submerge SV 7422, Lightning Strike SV 4229, Tidal Wave SV 6779. Ground Stomp 5285, Barrel Explode 572 and the
one-shots 345 / 121 / 372 / 5100 / 99 are wired only where the test allows (an alternate, or paired with a lasting
state).

Discs: `disc_scale(radius)` is the creature (object) scale of a water, ice or storm disc for a radius in yards.
"""

# --- Minted (patch-M) -------------------------------------------------------------------------------------------------

# SpellVisual ids (SpellVisual = Kit = EffectName number where they have them; patch script has the rows).
SV_QUICKSAND_PIT = 90700        # Ascension sand trap STATE, scale 1.1 (about 12 yd across)
SV_QUICKSAND_TRAIL = 90701      # the same model, scale 0.73 (about 8 yd across)
SV_STORM_STRIKE = 90702         # copy of SV 3 with only its InstantAreaKit 9161 (call lightning), sound 30
SV_BLADESTORM = 90703           # StateKit: the RFC-shipped blades model (SVEN 90370), anim 126, sound 4354
SV_BASILISK_GAZE = 90704        # copy of SV 8311 with its channel kit's AnimID 124 -> 51 (the Basilisk lacks 124)
SV_HYDRA_DISCHARGE_POSE = 90705  # copy of SV 36, precast anim 51 -> 32 and cast anim 53 -> 32 (the Hydra lacks both)
SV_HYDRA_SPIT_POSE = 90706      # copy of SV 854, precast 51 -> 32, cast 53 -> 32 (also Call the Waters' cast)
SV_STATIC_CHARGE = 90707        # LightningShield_State_Base on Base at a large scale, sound 3256

# Creature displays (CreatureModelData = CreatureDisplayInfo number). Creature scale = radius / DISC_QUAD_RADIUS.
DISPLAY_WATER_DISC = 90830      # Ascension target_water_state_projected (second texture re-pointed): blue swirl disc
DISPLAY_ICE_DISC = 90831        # Ascension target_frost_state_projected: pale frost disc
DISPLAY_STORM_DISC = 90832      # Ascension target_lightning_state_projected: dark cloud disc (the Discharge tell)
MINTED_SPELL_VISUALS = (SV_QUICKSAND_PIT, SV_QUICKSAND_TRAIL, SV_STORM_STRIKE, SV_BLADESTORM, SV_BASILISK_GAZE,
                        SV_HYDRA_DISCHARGE_POSE, SV_HYDRA_SPIT_POSE, SV_STATIC_CHARGE)
MINTED_CREATURE_DISPLAYS = (DISPLAY_WATER_DISC, DISPLAY_ICE_DISC, DISPLAY_STORM_DISC)

DISC_QUAD_RADIUS = 4.8          # each disc is a 9.6 yd quad at creature scale 1.0 (VR: 4 vertices, 9.6 x 9.6)
DELUGE_DISC_SCALE = 8.0         # the Deluge: the water disc at about 8 (a 77 yd disc), grown in steps over 5 s
DELUGE_DISC_START_SCALE = 1.0


def disc_scale(radius_yards: float) -> float:
    """Creature scale of a disc display for a radius in yards (scale = radius / 4.8)."""
    return radius_yards / DISC_QUAD_RADIUS


# Scale hints set on the creature, not in the DBC (floats on purpose: not ids).
SWARM_SCALE_RANGE = (1.3, 2.0)          # CDI 7470 scarab swarm: object scale 1.3 to 2.0 (a scarab is 1.5 yd at 1.0)
LOST_SOUL_SCALE_RANGE = (1.5, 2.0)      # CDI 12432 Wisp
THEKA_RISEN_SCALE = 1.2                 # CDI 6697: TrollMale x1.2; model info radius 0.306 x 1.2, reach 1.5 x 1.2
BARREL_SCALE = 2.0                      # CDI 26252 PowderKegFused at object scale 2.0 (0.45 x 0.5 x 0.75 yd at 1.0)

# --- Shipped (patch-M and the working copy) ---------------------------------------------------------------------------

SHIPPED_FIRE_ZONE = 90508               # Deadmines / Blackrock fire zone STATE, 8 yd (the Pyramid's totem)

# ===== Theka =====

DISPLAY_THEKA = 6696                    # TrollMale ext 4473
DISPLAY_THEKA_RISEN = 6697              # TrollMale x1.2 ext 4476; model info set by the patch SQL
DISPLAY_SWARM = 7470                    # the scarab swarm body, SWARM_SCALE_RANGE
TK_SWARM_AURA = 10986                   # Honey Touched: swarm model at SVEN scale 0.1 (4.3 x 4.7 x 1.9 yd); not 8325
TK_SWARM_AURA_ALT = 7620                # chest particles, unit-sized
TK_SWARM_ON_THEKA = 7620                # 2.5 s on Theka (never 7621 as it is)
TK_SWARM_ON_THEKA_ALT = 10986
TK_RISE_BURST = 7443                    # BurrowEarth_Brown_Missile area kit at the rise points
TK_RISE_BURST_ALT = 12718               # Ground Spike (rock)
TK_HUNT_TRAIL = 14013                   # `burrowearth_brown_missile` STATE following the swarm
TK_HUNT_TRAIL_ALT = 14230
TK_HUNT_ERUPTION = 7443                 # (11778 has no model and is never wired)
TK_RISING = 4341
TK_PLAGUE_CAST = 1004
TK_PLAGUE_STATE = 14987                 # lasting green Corrosion state on the carrier
TK_PLAGUE_SPREAD = 3138

# ===== Antu'sul =====

DISPLAY_ANTUSUL = 7353                  # TrollMale ext 5017
DISPLAY_SERVANT = 601                   # Basilisk x0.85
AS_CALCIFY = 711
AS_PETRIFIED = 1845
AS_GAZE_BEAM = SV_BASILISK_GAZE         # the white beam with the basilisk pose
AS_GAZE_BEAM_ALT = 8311                 # the white beam without the pose copy (also the minted row's fallback)
AS_GAZE_BEAM_FALLBACK = AS_GAZE_BEAM_ALT
AS_GAZE_ALT_RED = 8491
AS_GAZE_ALT_RED_2 = 9205
AS_SHATTER = 8097
AS_SHATTERBOLT = 36
AS_SHATTERBOLT_ALT = 97
AS_SHOCKWAVE = 8083                     # Ground Slam, ThunderClap ring 6.9 yd
AS_SHOCKWAVE_ALT = 8093                 # Gruul's Shockwave (a blue arcane dome)
AS_STONEFLESH = 7627
AS_SERVANT_RISE = 7443                  # the dirt burst stands in (the Basilisk has no birth animation)
AS_SERVANT_RISE_ALT = 1266
AS_HEAL = 135

# ===== Zum'rah =====

DISPLAY_ZUMRAH = 6434                   # TrollMale ext 4231
DISPLAY_SKELETON = 200
DISPLAY_WARD = 2418
DISPLAY_LOST_SOUL = 12432               # Wisp, LOST_SOUL_SCALE_RANGE
DISPLAY_BOUND_DEAD = 29716              # Ghostly Troll Celebrant (alpha 128); model info set by the patch SQL
DISPLAY_BOUND_DEAD_ALT = 29234          # Cheerful Troll Spirit
ZR_EMPTY_VESSEL_AURA = 247              # the aura TYPE (mirror image) of the Empty Vessel: not a display id
ZR_REND = 7964
ZR_GHOST = 886                          # with 7964's fade
ZR_TETHER = 8283
ZR_LOST_SOUL_STATE = 7566
ZR_GATHERED = 5101
ZR_BIND = 7181
ZR_FREED = 7180
ZR_WARD_SHIELD = 7519
ZR_WAIL = 14508
ZR_WAIL_ALT = 7180
ZR_GRAVE = 634
ZR_SHADOW_BOLT = 64                     # Shadow Bolt 12739's own SV, kept by the copy (D3)
ZR_VOLLEY = 2318                        # Shadow Bolt Volley 15245's own SV, kept by the copy (D3)
GODI_GRAVE = 1767                       # Shallow Graves (each grave point holds two GOs: 128308 and 128403)
ZR_INVIS_TYPE = 11                      # the spirit world invisibility type (not a visual id)
ZR_INVIS_TYPE_ALT = 7
ZR_INVIS_TYPE_ALT_2 = 8
ZR_INVIS_TYPE_ALT_3 = 9

# ===== The Pyramid =====

DISPLAY_EXECUTIONER = 6440              # x1.2
DISPLAY_SEZZZIZ = 6441
DISPLAY_NEKRUM = 6690                   # x1.1
DISPLAY_BERSERKER = 6423
DISPLAY_BERSERKER_2 = 6424
DISPLAY_HEXMASTER = 6419
DISPLAY_HEXMASTER_2 = 6420
DISPLAY_WITCH_DOCTOR = 6421
DISPLAY_WITCH_DOCTOR_2 = 6422
DISPLAY_FROG = 6297                     # Hex: Frog.mdx has animations 0, 4, 5, 9, 1 only (no hop)
DISPLAY_TOTEM = 1421                    # CDI of creature 6017
PY_BEHEAD = 39
PY_CHAIN = 9275                         # Wrangling Rope: the rope beam (68 Shackle has no chain)
PY_CHAIN_ALT = 9759
PY_GRIEVOUS = 121                       # one-shot: paired with PY_GRIEVOUS_STATE for the lasting look
PY_GRIEVOUS_STATE = 15286               # BloodBoil_Impact_Chest STATE on the carrier
PY_BARREL_DISPLAY = 26252               # CDI PowderKegFused at BARREL_SCALE; model info set by the patch SQL
PY_BARREL_DISPLAY_ALT = 29775           # CDI G_Barrel
PY_BARREL_DISPLAY_ALT_2 = 25175         # CDI G_BarrelExplode x1.5; model info set by the patch SQL
PY_BARREL_BLAST = 889
PY_BARREL_BLAST_ALT = 729
PY_BARREL_BLAST_ALT_2 = 572             # a small chest puff: only ever the alternate (107 style trap)
PY_KNOCKDOWN = 522
PY_OFFERING_BUFF = 47
PY_BLOOD_OFFERING = 7270                # Blood Siphon: the red beam (107 Sacrifice is a gold glow, never wired)
PY_SCREAM = 247
PY_BLEED = 372                          # one-shot: paired with PY_BLEED_STATE
PY_BLEED_STATE = 15286
PY_CURSE = 876
PY_HEX = 2295
PY_FROG_CREATURE = 7552                 # the frog creature entry (not a visual id)
PY_FLASH_HEAL = 3077
PY_WARD = 135
PY_LAVA_TOTEM_ZONE = SHIPPED_FIRE_ZONE  # 8 yd fire zone on the totem
PY_TOTEM_CREATURE = 6017                # the totem creature entry (not a visual id)

# ===== Bly's crew =====

BC_MARK = 3239
BC_INTERVENE = 9107
BC_GUARDED = 8024                       # standing Guarded shield stand-in (no Shield Wall look exists)
BC_GUARDED_ALT = 345                    # Shield Wall: a one-shot, only the alternate
BC_REFLECT = 7962
BC_VANISH = 255
BC_SHADOWSTEP = 8262
BC_GREATER_HEAL = 57
BC_KIDNEY = 679
BC_RES = 41
BC_SOULSTONE = 99                       # one-shot: the standing glow does not exist (icon only)
BC_AVENGE = 7870
BC_POISON = 5100                        # one-shot: paired with BC_POISON_STATE
BC_POISON_STATE = 14987
BC_SEED = 8339
BC_SEED_BURST = 7180
BC_ROF = 10379                          # copy of spell 11990, effect 27: the stock persistent area
BC_GOUGE = 256

# ===== Ukorz and Ruuzlu =====

DISPLAY_UKORZ = 6439                    # TrollMale x1.2
DISPLAY_RUUZLU = 6687                   # x1.2
UK_FURY = 578
UK_ROAR = 246
UK_BLADESTORM = SV_BLADESTORM
UK_BLADESTORM_ALT = 6044                # the stock Whirlwind state (also the minted row's fallback)
UK_BLADESTORM_FALLBACK = UK_BLADESTORM_ALT
UK_STAMP = 8083                         # Ground Slam
UK_STAMP_ALT = 5285                     # Ground Stomp: knocks victims down, only an alternate
UK_PIT = SV_QUICKSAND_PIT
UK_PIT_ALT = 7437                       # stock Sand Storm (plus the marker)
UK_PIT_FALLBACK = UK_PIT_ALT
UK_TRAIL = SV_QUICKSAND_TRAIL           # fallback: the marker alone
UK_SUNK = 7437
UK_SUNK_ALT = 38
UK_EXECUTE = 250
UK_CALL = 14508
UK_CALL_ALT = 76
UK_LASH = 2357
UK_HELD = 7519                          # F-1d DQ-3 A: the heroic 30% hold (214092): Spirit Shield's rune shield STATE
UK_HELD_ALT = 711                       # Stone Skin: a grey stone tint STATE, if the shield reads as an immunity
UK_STALKER_DISPLAY = 11686              # CDI InvisibleStalker x1, as RFC's creature 300988

# ===== Velratha and Gahz'rilla =====

DISPLAY_VELRATHA = 6685                 # TrollFemale
DISPLAY_GAHZRILLA = 7271                # white Hydra x3.0; model info 7271 radius 3, reach 15 live
GZ_TIDAL_CHARM = 657
GZ_WATER_DISC = DISPLAY_WATER_DISC      # creature display, scale = disc_scale(radius)
GZ_ICE_DISC = DISPLAY_ICE_DISC
GZ_STORM_DISC = DISPLAY_STORM_DISC
GZ_FREEZE_EVENT = 1744
GZ_FREEZE_SOLID = 2336
GZ_ICICLE = 2147
GZ_STATIC_CHARGE = SV_STATIC_CHARGE
GZ_STATIC_CHARGE_ALT = 37               # a 0.3 yd orb on a 24 yd hydra: nearly invisible
GZ_STATIC_CHARGE_FALLBACK = GZ_STATIC_CHARGE_ALT
GZ_DISCHARGE = SV_HYDRA_DISCHARGE_POSE
GZ_DISCHARGE_ALT = 36
GZ_DISCHARGE_FALLBACK = GZ_DISCHARGE_ALT
GZ_CONDUCTIVE = 37
GZ_OVERCHARGE = 8647
GZ_STORM_STRIKE = SV_STORM_STRIKE
GZ_STORM_STRIKE_ALT = 3
GZ_STORM_STRIKE_FALLBACK = GZ_STORM_STRIKE_ALT
GZ_ACID_SPIT = SV_HYDRA_SPIT_POSE
GZ_ACID_SPIT_ALT = 854
GZ_ACID_SPIT_FALLBACK = GZ_ACID_SPIT_ALT
GZ_GEYSER = 7680                        # a one-shot geyser impact (no lasting geyser exists)
GZ_BLAST = 889
GZ_BLAST_ALT = 729
GZ_BLAST_ALT_2 = 572
GZ_MASS_DISPEL = 8140
GZ_SLAM = 2377
GZ_DELUGE_BURST = 6501                  # the Deluge's one-shot burst on Gahz'rilla (VISUALS 'The Deluge', D7Hb)
GODI_GONG = 1827
GODI_FLOE_ALT = 8557                    # UL_IcePlatform_01 (19.8 x 20.8 yd): the alternate to the ice disc as a floe

# ===== Shared =====

DISPLAY_INVISIBLE_STALKER = 11686       # the stalker skin every kit helper wears

# Boss-code names that do NOT hold a SpellVisual id (creature displays, entries, aura and invisibility types).
NOT_SPELL_VISUAL_NAMES = frozenset({
    "ZR_EMPTY_VESSEL_AURA", "ZR_INVIS_TYPE", "ZR_INVIS_TYPE_ALT", "ZR_INVIS_TYPE_ALT_2", "ZR_INVIS_TYPE_ALT_3",
    "PY_BARREL_DISPLAY", "PY_BARREL_DISPLAY_ALT", "PY_BARREL_DISPLAY_ALT_2", "PY_FROG_CREATURE", "PY_TOTEM_CREATURE",
    "UK_STALKER_DISPLAY", "GZ_WATER_DISC", "GZ_ICE_DISC", "GZ_STORM_DISC",
})
# Boss-code names that are creature displays (a subset of the above): checked against CreatureDisplayInfo.
BOSS_CODE_DISPLAY_NAMES = frozenset({
    "PY_BARREL_DISPLAY", "PY_BARREL_DISPLAY_ALT", "PY_BARREL_DISPLAY_ALT_2", "UK_STALKER_DISPLAY",
    "GZ_WATER_DISC", "GZ_ICE_DISC", "GZ_STORM_DISC",
})

# Not in the stock client but already shipped (checked against the working-copy SpellVisual.dbc)
SHIPPED_SPELL_VISUALS = (SHIPPED_FIRE_ZONE,)

_BOSS_PREFIXES = ("TK_", "AS_", "ZR_", "PY_", "BC_", "UK_", "GZ_")


def _spell_visuals() -> set[int]:
    """Every SpellVisual id named above by a boss-code constant (an int constant whose prefix is a boss code)."""
    values = set()
    for name, value in globals().items():
        if name.startswith(_BOSS_PREFIXES) and type(value) is int and name not in NOT_SPELL_VISUAL_NAMES:
            values.add(value)
    return values


# Every stock SpellVisual id above (the SpellVisual existence check): the boss-code constants minus minted and shipped.
STOCK_SPELL_VISUALS = tuple(sorted(_spell_visuals() - set(MINTED_SPELL_VISUALS) - set(SHIPPED_SPELL_VISUALS)))
_MINTED_DISPLAYS = set(MINTED_CREATURE_DISPLAYS)
STOCK_CREATURE_DISPLAYS = tuple(sorted((
    {value for name, value in globals().items() if name.startswith("DISPLAY_") and type(value) is int}
    | {globals()[name] for name in BOSS_CODE_DISPLAY_NAMES}) - _MINTED_DISPLAYS))
STOCK_GAMEOBJECT_DISPLAYS = tuple(sorted({
    value for name, value in globals().items() if name.startswith("GODI_") and type(value) is int
}))
