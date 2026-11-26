"""
Gnomeregan build, WP V: the visual ids the boss files use, one place (not loaded on its own: the leading underscore
keeps the package loader from treating it as a declaration file; boss files import it with
`from ._visuals import ...`, like `_common.py` and zul_farrak/_visuals.py). A boss WP asks for a change in its report;
nobody else edits this file.

Source: .agents/plans/gnomeregan-build/gnomeregan-build.VISUALS-REPORT.md and handoff s3.10 / appendix C4 (ids, kits,
mesh bounds and textures read, nothing rendered, so every look is unconfirmed until seen in game) with the user rulings
of handoff s10 (s7 ruled as recommended: #39 A the six WRONG looks replaced by the picks, #40 A the boss bomb stays at
full size while the gear's Launched Walking Bomb stays at 0.6).

Four kinds of constant:

- MINTED (client patch-M, by apps/dbc-tools/patch_gnomeregan_vfx_models.py): `SV_*`, `DISPLAY_*` (90850-90856) and
  `SOUND_*` (90151, 90152) here. They must equal the patch script's constants (lib/test_gnomeregan_vfx.py pins it),
  all inside the reserved blocks of ids.yaml `gnomeregan`.
- SHIPPED (already in patch-M or the working copy: Deadmines / Scarlet Monastery / Zul'Farrak): nothing ships for
  them. Names start with `SHIPPED_`.
- STOCK: ids that already exist in the 3.3.5 client. Nothing ships and no id is minted.
- TELEGRAPH MARKERS (kit displays 91000-93999: the BM cones, discs, rings, Soak disc) are not named here: the boss
  files use the mod-boss-mechanics registry kinds and `Color(...)`, never a display id.

Prefixes tell the table of an id: `SV_` / `SHIPPED_` / `<boss code>_` are SpellVisual ids, `DISPLAY_` creature
displays, `GODI_` gameobject displays, `SOUND_` SoundEntries. A few boss-code names hold something that is NOT a
SpellVisual id (a creature display, a sound, a game object entry, a screen effect, an animation): see
`NOT_SPELL_VISUAL_NAMES`, `BOSS_CODE_DISPLAY_NAMES` and `BOSS_CODE_SOUND_NAMES`; the derived tuples skip them.
`*_ALT` / `*_FALLBACK` names are the VR alternates (one-constant swaps if the playtest rejects the pick; `_ALT_2` a
second one). Boss codes (the spec's mechanic id prefixes): TB Techbot, VF Viscous Fallout, EL Electrocutioner 6000,
MA the Mobile Alert System, CP Crowd Pummeler 9-60, MT Mekgineer Thermaplugg and the Whole Workshop, QN quest NPCs.

Ids that must NOT be wired are listed in the test (WRONG_*): SV 395 (the alarm is a crafting hammer), 7403 (Spotlight
summon: a point gesture), 2048 (Supercharge: a purple soul beam, no State), 74 (Goblin Land Mine: a summon puff), 354
(Remote Detonate: a sound only), 1484 (Corrosive Ooze: one puff, no missile), plus the wrong-tone 1485, 1184, 4229 and
7678. Looks that are right for one named use only (672 and 1187 only as alternates, the one-shots 2956 / 8314 / 9446 /
2074) are pinned to their names by the test.

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A STATE look plays on every unit that
carries the aura. An impact kit plays once, so a lasting effect re-casts it every 2-3 s or uses the lasting twin named
here (`TB_SAFE_MODE_STATE` for `TB_SAFE_START`, `MT_FIRE_PATCH` for `MT_FIRE_PATCH_CAST`).

Discs: `disc_scale(radius)` is the creature (object) scale of the nature disc for a radius in yards. Numerals:
`numeral_scale(glyph_height)`. Light cone: `light_cone_scale(length)`.

The boss bomb vs the gear's Launched Walking Bomb (s7 #40 A): both wear display 6977 (red). The boss bomb is a creature
of its own entry at creature scale `BOMB_SCALE` (1.0, DisplayScale 0.5 in the row = 1.5 x 1.2 x 2.2 yd); the gear's
creature 301100 (never reuse it) wears 6977 at `GEAR_LAUNCHED_BOMB_SCALE` (0.6, informational). Rules key by entry, the
boss bomb is hostile (red name plate) and carries the Hunter's Mark State (`MT_BOMB_MARK`) on its target.
"""

# --- Minted (patch-M) -------------------------------------------------------------------------------------------------

# SpellVisual ids (SpellVisual = Kit = EffectName number where they have them; the patch script has the rows).
SV_ARCING_GLOB = 90750          # copy of SV 854 (Acid Spit) with MissilePathType 2: the glob arcs like SV 8824's bomb
SV_BIG_VOLTAGE = 90751          # StateKit: LightningShield_State_Base at scale 5 on Base, sound 3256
SV_PUNCH_POSE = 90752           # copy of SV 8083 (Ground Slam) with its precast anim 118 -> 16 (AttackUnarmed)
SV_ALARM_PULSE = 90753          # InstantAreaKit: ThunderClap_Cast_Base ring + sound 5763 (the alert bot loop)

# Creature displays (CreatureModelData = CreatureDisplayInfo number, except 90851 / 90852: model 851 already exists).
DISPLAY_NATURE_DISC = 90850     # Ascension target_nature_state_projected: green swirl disc, scale radius / 4.8
DISPLAY_BOMB_RADIO = 90851      # GnomeBomBot (model 851), skin GnomeSpiderTankSkinGreen, display scale 0.5
DISPLAY_BOMB_FROST = 90852      # GnomeBomBot, skin GnomeSpiderTankSkinBlue, display scale 0.5
DISPLAY_NUMERAL_1 = 90853       # flat white numeral quad "1" (BM-style quad, projected texture)
DISPLAY_NUMERAL_2 = 90854
DISPLAY_NUMERAL_3 = 90855
DISPLAY_LIGHT_CONE = 90856      # Ascension custom_cone_white: a flat white light cone quad, optional searchlight look
MINTED_SPELL_VISUALS = (SV_ARCING_GLOB, SV_BIG_VOLTAGE, SV_PUNCH_POSE, SV_ALARM_PULSE)
MINTED_CREATURE_DISPLAYS = (DISPLAY_NATURE_DISC, DISPLAY_BOMB_RADIO, DISPLAY_BOMB_FROST, DISPLAY_NUMERAL_1,
                            DISPLAY_NUMERAL_2, DISPLAY_NUMERAL_3, DISPLAY_LIGHT_CONE)
NUMERAL_DISPLAYS = (DISPLAY_NUMERAL_1, DISPLAY_NUMERAL_2, DISPLAY_NUMERAL_3)

# SoundEntries (Ascension patch-O timer ticks, wav converted)
SOUND_GEIGER_2 = 90151          # fx_timer_tick_2click
SOUND_GEIGER_4 = 90152          # fx_timer_tick_4click
MINTED_SOUNDS = (SOUND_GEIGER_2, SOUND_GEIGER_4)

DISC_QUAD_RADIUS = 4.8          # the nature disc is a 9.6 yd quad at creature scale 1.0 (VR: 4 vertices, 9.6 x 9.6)
LIGHT_CONE_SCALE_30_YD = 0.79   # custom_cone_white.m2 is a 44.4 yd quad, apex near x 0: scale 0.79 reaches about 30 yd
NUMERAL_GLYPH_HEIGHT_PER_SCALE = 1.6   # a numeral glyph is 0.70 of the quad side; the quad side is 16/7 yd per scale


def disc_scale(radius_yards: float) -> float:
    """Creature scale of the nature disc for a radius in yards (scale = radius / 4.8)."""
    return radius_yards / DISC_QUAD_RADIUS


def light_cone_scale(length_yards: float) -> float:
    """Creature scale of the light cone display for a cone that reaches `length_yards` (0.79 for 30 yd)."""
    return LIGHT_CONE_SCALE_30_YD * length_yards / 30.0


def numeral_scale(glyph_height_yards: float) -> float:
    """Creature scale of a numeral quad whose digit is `glyph_height_yards` tall."""
    return glyph_height_yards / NUMERAL_GLYPH_HEIGHT_PER_SCALE


# Scale hints set on the creature, not in the DBC (floats on purpose: not ids).
ALERT_SCALE = 3.0               # CDI 6888 at DisplayScale 3: 3.1 x 6.5 x 5.3 yd
PUMMELER_SCALE = 5.0            # CDI 6774 at scale 5 (window ruling, s10); model info is NOT edited (shared display)
BIG_ONE_SCALE = 2.0             # CDI 19139 at DisplayScale 2: 6.0 x 4.8 x 8.8 yd
BOMB_SCALE = 1.0                # the boss Walking Bomb (CDI 6977 holds 0.5): s7 #40 A, full size
GEAR_LAUNCHED_BOMB_SCALE = 0.6  # informational: the gear's creature 301100 (never reuse its entry or scale)
MINE_SCALE_RANGE = (2.0, 3.0)   # CDI 6271 LandMine01 (0.9 yd) at object scale 2 to 3
PUDDLE_DISC_SCALE = 0.83        # the Wandering Puddle: the nature disc at about 4 yd radius (disc_scale(4.0))
LEAK_DISC_SCALE = 10.4          # the Reactor Leak: a roughly 100 yd disc (radius 50)
POOL_DISC_SCALE_RANGE = (4.0, 10.0)  # Fallout pools 4 / 5 / 7 yd, the Leaking 10 yd: disc_scale(radius)
BOMB_MODEL_INFO = (0.75, 1.0)   # radius, reach of 90851 / 90852 (set by the patch SQL)

# --- Shipped (patch-M and the working copy) ---------------------------------------------------------------------------

SHIPPED_SKULL_STATE = 90506             # Deadmines skull head State (the Locked Out alternate)
SHIPPED_FIRE_ZONE = 90508               # Deadmines / Blackrock fire zone STATE (the Flame Patch's lasting look)
SHIPPED_HOLY_ZONE = 90509               # holyzone x1.2 (the plate glow alternate); 90510-90512 are larger
SHIPPED_FOG_SMALL = 90558               # Scarlet Monastery LargeGreenRadiationFog 6 yd (vents; a pool alternate)
SHIPPED_FOG_MEDIUM = 90559              # 9 yd
SHIPPED_FOG_LARGE = 90560               # 12 yd
SHIPPED_FOG_EXTRA = 90561               # the SM row VR names for a puddle on a stalker
SHIPPED_STORM_STRIKE = 90702            # Zul'Farrak row: SV 3's InstantAreaKit only (the Justice blast alternate)

# ===== Techbot =====

DISPLAY_TECHBOT = 7288                  # GnomeBot, black skin; model info 2 / 3.44
DISPLAY_DUPE_BUG = 3233                 # Cockroach x1.5; model info 0.15 / 1.5
TB_LAG = 68                             # Slow_Impact_Base: a gray slowdown puff, lasting with the aura
TB_LINK_DEAD = 2072                     # StunSwirl_State_Head + anim 14: reads stunned
TB_LAG_SPIKE = 2917                     # FireBlast impact + Bomb_ExplosionA, one-shot; the marker carries the radius
TB_SPAWN = 2073                         # purple shadow ring (3 s); tone risky for a software bug
TB_SPAWN_ALT = 263                      # blink_impact_chest, a tight 0.8 yd puff
TB_PATCH = 2074                         # SoulFunnel + BloodyExplosion + a 6.9 yd ring; one-shot, the bar is the tell
TB_SAFE_MODE_STATE = 37                 # State tier 1: LightningShield orbs (small on a 3 yd bot)
TB_SAFE_MODE_STATE_2 = 7867             # State tier 2: arcanepower_state_chest arcs (reads on a 3 yd bot)
TB_SAFE_MODE_STATE_ALT = SV_BIG_VOLTAGE  # the minted big state (fallback = TB_SAFE_MODE_STATE_2)
TB_SAFE_MODE_STATE_FALLBACK = TB_SAFE_MODE_STATE_2
TB_SHUTDOWN = TB_SAFE_MODE_STATE_2      # TB9: the arcs on the powered-down body (Shutdown 214320, a lasting State)
TB_SAFE_START = 2956                    # Fire_ImpactDD_Chest, ONCE at the start; lasting twin TB_SAFE_MODE_STATE
TB_NET = 683                            # Battle Net: boomerang, a 2.3 yd net
TB_AFTERIMAGE_GHOST = 886               # Ghost_state particles, pale blue, on the mirror clone
TB_AFTERIMAGE_GHOST_ALT = 7964          # alpha fade 0.5 (ZR_REND's fade in Zul'Farrak)
TB_AFTERIMAGE_ALPHA = 0.5               # clone alpha hint (float)
TB_SAVE_SET = 2046                      # Teleport impact: a 4.7 x 4.7 x 33.5 yd blue light pillar, 1.5 s, sound 3226
TB_SNAP = 263                           # blink_impact_chest on the player at the snap back

# ===== Viscous Fallout =====

DISPLAY_FALLOUT = 5497                  # WaterElemental green skin x1.3; model info 0.397 / 0.3
VF_DOSE = 1712                          # GreenGhost_state, lasts the aura
VF_DOSE_BRIGHT = 6594                   # focusedcasting_state_chest glow (dose 10 and up)
VF_SICKNESS = 1725                      # Radiation Sickness: green burst + the dose glow (also MT_RADIO)
VF_VOMIT = 9446                         # acidliquidbreath one-shot (the Breath attachment on a player is unverified)
VF_POOL_DISC = DISPLAY_NATURE_DISC      # creature display, scale = disc_scale(radius); with the BM circle marker
VF_POOL_ALT_SM = SHIPPED_FOG_SMALL      # fallback: SM rows 90558 to 90561 (90558, 90559, 90560, 90561 by size)
VF_SLOUGH = 1725                        # Slough's swell: the green cast
VF_SLOUGH_PRECAST = 4202                # Nature_PreCast_Low_Hand precast (4202 is also the Volley)
VF_GLOB = SV_ARCING_GLOB                # the arcing glob
VF_GLOB_ALT = 854                       # the same missile without the arc (also the minted row's fallback)
VF_GLOB_FALLBACK = VF_GLOB_ALT
VF_VOLLEY = 4202                        # Toxic Volley
VF_CLICK = 11757                        # geiger tick: SimonGame_Visual_GameTick (SoundEntries, not a SpellVisual)
VF_CLICK_ALT = SOUND_GEIGER_2           # the Ascension 2-click timer tick (minted)
VF_CLICK_FALLBACK = VF_CLICK

# ===== Electrocutioner 6000 =====

DISPLAY_ELECTROCUTIONER = 6915          # GnomeSpiderTank black skin + pilot x1.2; model info 1.2 / 2.4
EL_CHAIN = 36                           # Chain Bolt copy: ShockLightning chain
EL_CHAIN_ALT = 97
EL_MEGAVOLT = 944                       # chain 95; the 30 yd cone is the BM marker
EL_SHOCK = 97
EL_VOLTAGE = TB_SAFE_MODE_STATE         # tier 1 (1 to 2 stacks)
EL_VOLTAGE_2 = TB_SAFE_MODE_STATE_2     # tier 2 (3 stacks and up)
EL_VOLTAGE_ALT = SV_BIG_VOLTAGE         # the minted big state
EL_VOLTAGE_FALLBACK = EL_VOLTAGE_2
EL_JUSTICE_CAST = 7569                  # Electric Justice cast: lightning hands + a blue-white tint State for 4 s
EL_JUSTICE_BLAST = 3                    # InstantArea ThunderClap ring 6.9 yd + CallLightning, sound 30
EL_JUSTICE_BLAST_ALT = SHIPPED_STORM_STRIKE  # Zul'Farrak's row: the call lightning only (no hand cast)
EL_STATIC = 7867                        # Static on a player: arcs
EL_STATIC_ALT = 37
EL_DISCHARGE = 3                        # on a stalker at the carrier

# ===== The Mobile Alert System =====

DISPLAY_ALERT = 6888                    # GnomeAlertBot at ALERT_SCALE; model info 0.6 / 0.8
DISPLAY_ASSISTANT = 6967
DISPLAY_ASSISTANT_2 = 6968
DISPLAY_DEFENDER = 6982
DISPLAY_DEFENDER_2 = 6981
MA_LOCK_PILLAR = 7402                   # MoonBeam pillar on the spotted player (an aura, infinite)
MA_CONE_LIGHT = DISPLAY_LIGHT_CONE      # optional light cone display on the turning stalker (alt to the BM cone)
MA_SPOTTED = 7851                       # Spotted beam: Beam_RedDrops from the boss to the player
MA_ALARM_PULSE = SV_ALARM_PULSE         # a ring and the loop sound
MA_ALARM_PULSE_ALT = 2074               # SV 2074's ring (also the minted row's fallback)
MA_ALARM_PULSE_FALLBACK = MA_ALARM_PULSE_ALT
MA_ALARM_VOICE = 5805                   # SoundEntries: "Warning! Warning! Intruder alert!"
MA_ALARM_LOOP = 5763                    # SoundEntries: GnomeAlertBotLoop
MA_SELF_DESTRUCT = 1463                 # Bomb_ExplosionA blast + FireNova ring; the clock is an aura carrying it
MA_NET = 683
MA_DECOR_HAZARD_LIGHT_GO = 193710       # stock GO entry (display 5332), optional decor (an entry, not a visual)
MA_DECOR_SPOTLIGHT_GO = 193709          # stock GO entry (display 2354)
GODI_DOOR = 907                         # Workshop Door GnomeregandDoor01 (anims 146 to 149)

# ===== Crowd Pummeler 9-60 =====

DISPLAY_PUMMELER = 6774                 # GnomeBot red skin x1.1 at PUMMELER_SCALE; model info 1.65 / 1.65, not edited
CP_HIT_FLASH = 906                      # Arcing Smash hit flash (hook)
CP_PUMMEL = 1023                        # Crowd Pummel
CP_UPPERCUT = 2069                      # Uppercut / Knock Away
CP_STOMP = 8083                         # Trample: Ground Slam ThunderClap ring 6.9 yd, shake 6
CP_STOMP_ALT = 672                      # a 1.1 yd crescent: only an alternate
CP_PUNCH_POSE = SV_PUNCH_POSE           # Ground Slam with the AttackUnarmed pose (anim 16)
CP_PUNCH_POSE_FALLBACK = CP_STOMP       # the ring without the pose (the boss emotes anim 16 in script)
CP_PUNCH_EMOTE_ANIM = 16                # the one punch animation GnomeBot has (an anim id, not a visual)
CP_LANDED = 1763                        # Sap stars over the head on a Weakened-type aura
CP_LANDED_ALT = 1187                    # reads as stunned: only an alternate
CP_BELL = 6555                          # SoundEntries ShaysBell via PlayDirectSound at 66%, 33% and the pull
GODI_CHEST = 3014                       # DarkIronSafe, the chest on the pocket floor
GODI_CHEST_ALT = 10                     # Chest01 at size 2

# ===== Mekgineer Thermaplugg =====

DISPLAY_THERMAPLUGG = 6980              # GnomePounder red skin + yellow pilot; model info 2 / 2.5
DISPLAY_BOMB = 6977                     # Walking Bomb: red, BOMB_SCALE
DISPLAY_BOMB_FROST_ALT = 21209          # blue GnomeBomBot at 0.35: model info is 0 / 0 live, needs a row if used
DISPLAY_BIG_ONE = 19139                 # The Big One at BIG_ONE_SCALE; model info 1.5 / 2
DISPLAY_MINE = 6271                     # LandMine01 at MINE_SCALE_RANGE; model info 1 / 1
DISPLAY_MINE_ALT = 15402                # the same at 0.5; model info 0.5 / 0.5
MT_FACE_BEAM = 944                      # ShockLightning from the boss to a face stalker
MT_FACE_BEAM_ALT = 6594
MT_FIST_FACE_GLOW = MT_FACE_BEAM_ALT    # MT24: the lit Gnome Face the fist strikes from (SV 6594 flares, gap 12)
MT_BLAST = 5619                         # Bomb_ExplosionA + MoltenBlast impact; plus MT_BLAST_FLASH
MT_BLAST_FLASH = 10693                  # the 17 yd ground flash (Sticky Bomb blast too)
MT_BLAST_ALT = 889
MT_MINE_LOB = 3819                      # the lob (bomb in hand, missile_bomb, Bomb_ExplosionA)
MT_INCENDIARY = 8824                    # arcing incendiary lob
MT_FIRE_PATCH = SHIPPED_FIRE_ZONE       # the lasting patch on a stalker
MT_FIRE_PATCH_CAST = 8314               # the one-shot cast, ONCE; lasting twin MT_FIRE_PATCH
MT_BIG_ONE = 3819
MT_KNOCK_AWAY = CP_UPPERCUT             # MT7: the stock Knock Away 10101's look (SV 2069)
MT_DETONATE = 5619                      # per-blast: bombs 5619 (354 is never wired)
MT_DETONATE_MINE = 889
MT_FROST = 17                           # Frost Nova: ice chunks + snowflakes = the root look
MT_FROST_ALT = 1744
MT_RADIO = 1725                         # green burst + the stacking Poison glow
MT_RADIO_ALT = 4202
MT_STICKY = 10692                       # Living Bomb State on the carrier
MT_STICKY_ALT = 8339
MT_STICKY_BLAST = MT_BLAST_FLASH
MT_BOMB_MARK = 3239                     # Hunter's Mark head glow on a bomb's target (s7 #40 A)
MT_LOCKED_OUT = 1845                    # Petrification: a dark gray tint State ("grayed out")
MT_LOCKED_OUT_ALT = SHIPPED_SKULL_STATE
MT_PLATE_ALT = SHIPPED_HOLY_ZONE        # the plate glow is a BM Soak disc; this holy zone is the alternate
MT_VENT_SMALL = SHIPPED_FOG_SMALL       # State on a stalker at each open face, 6 / 9 / 12 yd by a guess
MT_VENT = SHIPPED_FOG_MEDIUM
MT_VENT_LARGE = SHIPPED_FOG_LARGE
MT_VENT_ALT = SHIPPED_FOG_EXTRA
MT_DOSE = VF_DOSE                       # the hard-mode Dose, as Fallout
MT_DOSE_BRIGHT = VF_DOSE_BRIGHT
MT_MELTDOWN = 6594                      # the bright glow plus a BM circle
MT_MELTDOWN_ALT = 1725
MT_DUPLICATE = TB_SPAWN                 # Bomb Duplication, as Techbot
MT_DUPLICATE_ALT = TB_SPAWN_ALT
MT_PUDDLE = DISPLAY_NATURE_DISC         # the Wandering Puddle unit (PUDDLE_DISC_SCALE), grown in 1.5 s
MT_LEAK = DISPLAY_NATURE_DISC           # the Reactor Leak disc (LEAK_DISC_SCALE)
MT_LEAK_SCREEN_EFFECT = 282             # ScreenEffect "Icecrown - Emerald Nightmare", via aura 260 (a ScreenEffect id)
MT_LEAK_SCREEN_EFFECT_ALT = 61          # "Jungle Madness", a softer green
MT_LEAK_ALARM_SOUND = 5763              # SoundEntries loop
MT_LEAK_ALARM_SOUND_ALT = 4894          # GnomeHazardLightStandLoop
MT_LOAD_VOICE = 5808                    # "My machines are the future!" on the console schematic line
MT_NUMERAL_1 = DISPLAY_NUMERAL_1
MT_NUMERAL_2 = DISPLAY_NUMERAL_2
MT_NUMERAL_3 = DISPLAY_NUMERAL_3
MT_NUMERALS = NUMERAL_DISPLAYS          # colors of the shapes (green, yellow, red = 1, 2, 3) are the fallback
MT_GEIGER = VF_CLICK                    # the hard-mode Dose ticks
MT_GEIGER_ALT = SOUND_GEIGER_4
GODI_CONSOLE = 2091                     # G_GnomeTerminal at GO size 1.5 to 2 (the Clearance Console)
GODI_CONSOLE_ALT = 2089                 # G_GnomeMultiBox
MT_PUNCHOGRAPH_GO = 142345              # stock GO entry to spawn again on map 90 (an entry, not a visual)
MT_FIST_DISPLAY = DISPLAY_PUMMELER      # no hands-only model: the Pummeler body behind the wall (scale 5 or 3)

# ===== Quest NPCs =====

DISPLAY_EXILE = 6973                    # GnomeMale (entry 39265 pattern), faction 35; model info present
DISPLAY_EXILE_2 = 6974                  # GnomeFemale of the pair
DISPLAY_EXILE_3 = 6975
DISPLAY_EXILE_4 = 6976

# ===== Shared =====

DISPLAY_INVISIBLE_STALKER = 11686       # the stalker skin every kit helper wears (vents, face glows, cones)

# Boss-code names that do NOT hold a SpellVisual id (creature displays, sounds, entries, screen effects, animations).
BOSS_CODE_DISPLAY_NAMES = frozenset({
    "VF_POOL_DISC", "MA_CONE_LIGHT", "MT_PUDDLE", "MT_LEAK", "MT_NUMERAL_1", "MT_NUMERAL_2", "MT_NUMERAL_3",
    "MT_FIST_DISPLAY",
})
BOSS_CODE_SOUND_NAMES = frozenset({
    "VF_CLICK", "VF_CLICK_ALT", "VF_CLICK_FALLBACK", "MA_ALARM_VOICE", "MA_ALARM_LOOP", "CP_BELL",
    "MT_LEAK_ALARM_SOUND", "MT_LEAK_ALARM_SOUND_ALT", "MT_LOAD_VOICE", "MT_GEIGER", "MT_GEIGER_ALT",
})
NOT_SPELL_VISUAL_NAMES = frozenset({
    "MA_DECOR_HAZARD_LIGHT_GO", "MA_DECOR_SPOTLIGHT_GO", "MT_PUNCHOGRAPH_GO", "MT_LEAK_SCREEN_EFFECT",
    "MT_LEAK_SCREEN_EFFECT_ALT", "CP_PUNCH_EMOTE_ANIM",
}) | BOSS_CODE_DISPLAY_NAMES | BOSS_CODE_SOUND_NAMES

# Not in the stock client but already shipped (checked against the working-copy SpellVisual.dbc)
SHIPPED_SPELL_VISUALS = (SHIPPED_SKULL_STATE, SHIPPED_FIRE_ZONE, SHIPPED_HOLY_ZONE, SHIPPED_FOG_SMALL,
                         SHIPPED_FOG_MEDIUM, SHIPPED_FOG_LARGE, SHIPPED_FOG_EXTRA, SHIPPED_STORM_STRIKE)

# Stock SoundEntries ids the picks use (checked against the working-copy SoundEntries.dbc)
STOCK_SOUNDS = (11757, 5805, 5763, 6555, 5808, 4894)

_BOSS_PREFIXES = ("TB_", "VF_", "EL_", "MA_", "CP_", "MT_", "QN_")


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
