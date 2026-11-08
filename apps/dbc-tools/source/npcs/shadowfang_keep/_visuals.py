"""
Shadowfang Keep build, WP-V: the visual ids the boss files use, one place (not loaded on its own: the leading underscore
keeps the package loader from treating it as a declaration file; boss files import it with
`from ._visuals import ...`, like `_common.py`). Owned by WP-V; a boss WP asks for a change in its report.

Source: .agents/plans/shadowfang-keep-build/shadowfang-keep-build.VISUALS-REPORT.md (every look is unconfirmed until
seen in game), the top pick of each row (handoff s3.10, s7 #16), with the nine look corrections of s3.10 applied: the
constants below are the corrected ids, never SK's originals.

Two kinds of constant:

- MINTED (client patch-M, by apps/dbc-tools/patch_shadowfang_keep_vfx_models.py, ids.yaml reservation
  `shadowfang_keep`): `SV_SHADOW_LIGHTNING` and `GODI_CELL_KEY`. They must equal the patch script's constants of the
  same name (lib/test_shadowfang_keep_vfx.py pins it).
- STOCK: ids that already exist in the 3.3.5 client (SpellVisual.dbc, CreatureDisplayInfo.dbc,
  GameObjectDisplayInfo.dbc, SoundEntries.dbc). Nothing ships for them; the patch script's dry run checks they exist.

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A StateKit look (the `STATE` ones)
plays on every unit that carries the aura, so only put it on an aura. A look whose chain rides a ChannelKit (Soul Drain)
shows only on a channeled spell. Names are `<boss code>_<what>`; the boss codes are the handoff's (RG Rethilgore,
RC Razorclaw, BS Silverlaine, SP Springvale, OD Odo, DC Deathsworn Captain, FN Fenrus, NA Nandos, AR Arugal).
"""

# --- Minted (patch-M) -------------------------------------------------------------------------------------------------

# Fenrus FN8, Shadow Lightning (3 yd strike circle): Ascension purple_leishen_lightningcall_projected.m2 as an
# ImpactKit BaseEffect, the slot of stock kit 318's model (a purple bolt from the sky, a projected crack on the
# floor), stock thunder sound. Put it on the instant damage spell that hits the player; the bolt plays at the target's
# feet.
SV_SHADOW_LIGHTNING = 90400

# Rethilgore RG3, the Cell Key (gameobject_template 301100, K's SQL rev): Ascension 6hu_barracks_keyring01.m2, an iron
# jail key ring lying flat, 0.38 x 0.58 x 0.14 yd at size 1, so set the template size to CELL_KEY_SIZE.
GODI_CELL_KEY = 90030
CELL_KEY_SIZE = 2.75

# --- Stock displays, sounds and sizes ---------------------------------------------------------------------------------

# no model: the Cell Door stand-in (correction 1; NOT 411, a gameobject display), the ward stalker 300515, the strike
# / visual stalker 300516, every "aura on a stalker"
DISPLAY_INVISIBLE_STALKER = 11686
DISPLAY_SOUL_WISP = 1825            # RG5 Soul Fragment: the blue-white "Restless Soul" wisp, 1.45 yd
# RG6 Tainted Fragment: the same wisp with green particles; set the scale to 1.0 in creature_template_model so it
# matches the normal fragment
DISPLAY_TAINTED_WISP = 24465
DISPLAY_ECHO_RETHILGORE = 524       # BS echoes of Rethilgore and Razorclaw (worgen, brown, 1.15): the stock displays
DISPLAY_ECHO_ODO = 522              # BS Echo of Odo (worgen, black, 1.3)
DISPLAY_GLUTTON_WORGEN = 202        # AR6 Turned: the Glutton transform (spell 3857) display

GODI_ALARM_BELL = 4052              # OD3: G_BellShip.mdx, 3.4 x 7.2 x 4.4 yd at size 1 (K's 301101 row: size 0.55)
ALARM_BELL_SIZE = 0.55
GODI_BLOOD_POOL = 4211              # RC4 Offal Slick dressing: "Blood of Heroes", 4.75 x 5.25 yd at size 1
OFFAL_POOL_SIZE = 0.6               # 0.5-0.7 per pool, 2-3 pools inside the cone, despawned with the zone

# OD3 toll: BellTollKharazhan (runner-up 6595), played by the script with PlayDirectSound / PlayDistanceSound (GODI
# 4052 carries no sound)
SOUND_BELL_TOLL = 9154

# --- Spells whose SpellVisual stands in for the cast (a copy of the stock visual id is all a spell needs) -------------

# Auras with a stock look that a custom aura spell can copy the SpellVisual of; the id of the stock spell that shows it.
SPELL_GHOST_VISUAL = 9617           # BS echoes: aura on the echo, SV 886

# --- Per boss: SpellVisual per spell ---------------------------------------------------------------------------------

# Rethilgore
# RG1: Charge 52577, on the leap spell with MoveJump (skip its stun swirl: the grab is a teleport). Chain: trail +
# dust, blood burst on the grabbed player
RG_LOCK_UP_LEAP = 11546
RG_CELL_TELEPORT_FLASH = 3303       # RG1: Shadow Port, a flash at both ends of the throw into the cell
# RG4: Soul Drain beam (chain 8, SoulBeam.blp): ONLY on a channeled spell (correction 9)
RG_SOUL_DRAIN_CHANNEL = 680
# RG5: Akama Soul Retrieve, an unclaimed fragment streaks to Rethilgore (cast by the fragment on him)
RG_FRAGMENT_STREAK = 9253
RG_KEY_SPARKLE = 12528              # RG3: Treasure Sparkle, StateKit on an invisible stalker beside the key ring

# Razorclaw
# RC1: Scourge Hook 50335 (correction 8; NOT Hookshot 12058, an instant grab). Give the hook spell a 1-2 s cast so the
# iron chain shows over the line warning. Same for the Echo of Razorclaw
RC_MEAT_HOOK = 11055
RC_BUTCHERS_CUT = 110               # RC3: Rend Flesh, a blood claw arc (4.5 yd at scale 1; the cone marker is the size)

# Baron Silverlaine
# BS1-BS5: Ghost Visual aura (spell 9617) on displays 524 / 522: pale blue tint, 50% alpha, ghost particles. One aura
# makes any model spectral
BS_ECHO_GHOST = 886
BS_ECHO_ARRIVAL = 4490              # BS echo arrival flash: Spirit Particles (Spawn) 37119
BS_ACCURSED_VEIL = 561              # BS6: Veil of Shadow, verified right (shadow hands, cripple state)

# Commander Springvale
# SP1: Hammer of Wrath 24239, a holy hammer thrown at the player (give the spell a speed so it lands at the ring's
# end). Runner-up SV 322 (stun swirl only for the stun)
SP_HAMMER_LANDING = 7250
# SP5: Holy Fire 14914, on the per-player damage spell so every player gets the burst
SP_SEARING_LIGHT = 3400
SP_CONSECRATION = 5600              # SP3: Consecration 32773, verified (persistent ground, scales to 8 yd)
SP_HOLY_LIGHT = 2936                # SP4: verified
SP_DIVINE_SHIELD = 154              # SP6/SP7 Oath: verified, the golden bubble
SP_RISE_UNHOLY = 14312              # SP6: Raise Dead 67705 for the guardsmen (dark rise, skull spirits)
SP_RISE_HOLY = 41                   # SP6: Redeeming the Soul 23254, the holy rise if "of the Light" must rise in light
SP_WRATH_OF_GOD = 12986             # SP8: Holy Wrath 28883, verified

# Odo the Blindwatcher
OD_HOWLING_RAGE = 754               # verified: roar, red body (also Nandos)
OD_MAUL = 577                       # OD2: Maul 54459, claw swipe + blood
OD_FRENZY = 870                     # Frenzy 23537, enrage flash
OD_BELL_RING_FLASH = 8124           # OD3/OD4: Sonic Boom 33666, a shockwave when the bell rings
OD_DEAFENED = 875                   # Sonic Burst 8281: Deafened on Odo (StateKit on his mouth)
# cracked bell: Small White Smoke Flare 43452 on a stalker at the bell (no cracked bell model exists; runner-up SV
# 8410, thin steam)
OD_CRACKED_BELL_SMOKE = 9774

# Deathsworn Captain
DC_CHARGE = 3783                    # DC1/DC2: Charge 32323 (trail + dust; its stun swirl plays only if an aura applies)
DC_CLEAVE = 219                     # DC3: Cleave 15496, white arc (3.4 yd)
DC_ENRAGE = 5440                    # Enrage 28371

# Fenrus the Devourer
# FN1: Lightning Cloud 6535, CallLightning_Impact, an 11 yd sky bolt (correction 2; NOT Lightning Strike 27983 / SV
# 6941, a blue ball at the feet). Blue is right (Nature)
FN_LIGHTNING = 986
FN_SHADOW_LIGHTNING = SV_SHADOW_LIGHTNING  # FN8 (minted above)
FN_SHADOW_LIGHTNING_FALLBACK = 7732  # no-patch fallback: Shadowfury 30283, purple blast with dark streaks
# FN3: Shadow Burst 28447, a pure shadow nova (correction 7; NOT Shadow Nova 30852 / SV 7966, an orange ring). Runner-
# up SV 12835, Shadow Crash 60835
FN_VOID_PULSE = 45
FN_SHADOWFORM = 3619                # FN5: verified, dark purple translucent wolf
# FN6: Shadow Pounce 52327, a shadow puff at departure; the landing is the Bait circle
FN_SHADOW_LEAP_DEPARTURE = 8262

# Wolf Master Nandos
NA_TERRIFYING_HOWL = 247            # NA3: verified, the fear shout
# NA4: Acid Breath 12533, a breath on the cone (correction 6; NOT Acid Spit SV 854, a missile that hits one target)
NA_ACID_SLAVER = 2619
# Nandos / wolf lunge: Rip 1079, a blood claw arc (correction 5; NOT SV 11612, Frost Strike). Runner-up SV 2275,
# Ravage 6785
NA_LUNGE = 3941
NA_HOWLING_RAGE = OD_HOWLING_RAGE   # NA5 +15% damage: roar, red body
# NA6: Hunter's Mark 1130, the red arrow over the head (plus the Stack disc). Runner-up SV 14339, Marked For Death
NA_MARK_THE_PREY = 3239
# NA7: Blood Mirror 70445, a StateKit chain from the aura's CASTER to its holder: each living wolf casts the aura on
# Nandos (4 beams), remove it on the wolf's death. Runner-up SV 12156, Obedience Chains
NA_PACK_BOND = 14876

# Archmage Arugal
AR_THUNDERSHOCK = 145               # AR2: verified, thunderclap cast flash (the 8 yd ring is the Zone marker)
AR_VOID_BOLT = 758                  # AR3: verified, shadow bolt
AR_CURSE = 760                      # AR4: Arugal's Curse, purple-tinted victim (also the 80+ stack tint below)
AR_SHADOW_PORT = 3303               # AR5: verified (teleport flash, orange fog is the stock Arugal look)
AR_ECLIPSE = 11567                  # AR9 Moonrise: Eclipse (Lunar) 48518, a moon disc flash once on apply
AR_STARFALL_STATE = 11571           # AR9: Starfall 48505 StateKit on Arugal for a lasting look
AR_MOONFIRE_COLUMN = 1263           # a moonlight column on a target (Moonfire Visual 36704)
# AR7: Rune of Power aura 61974 (correction 3; NOT 61973 / SV 13072, hands only): an 11 yd blue rune, StateKit on the
# ward stalker 300515 (the Ulduar wiring)
AR_WARD_RUNE = 13069
# AR7: the prisoner's casting hands as the ward goes down (Rune of Power 61973's SV 13072: hands only, so never the
# rune), and the cleanse sparkle on each player inside when it pulses (Remove Curse 475's SV 186). S9's two stock looks.
AR_WARD_HANDS = 13072
AR_WARD_CLEANSE = 186
# AR7: Sprinkle Holy Water 57806 (correction 4; NOT Throw Vial A 68799 / SV 14495, a blood spurt): a silver vial
# thrown (the spell needs speed ~15), splash, blue moonbeam
AR_VIAL_THROW = 12483
# AR7: Zul'Aman Spirit Effect 42466, white fog on the ward stalker. Runner-up SV 14902
AR_VIAL_CLOUD = 9554
# Moonlit room: Beam (Blue) 32840 on 3-5 stalkers around the room's edge (40 yd shafts)
AR_MOONLIT_BEAM = 7990
AR_CURSE_50 = 11338                 # Worgen's Curse at 50+ stacks: Lycanthropy 49170, purple wisps
AR_CURSE_80 = AR_CURSE              # at 80+: the body tint (SV 760 State)
AR_TURNED_TRANSFORM = 7199          # at 100 (Turned): Worgen Transform 47457, morph burst (+ AR_TURNED_CHARM)
AR_TURNED_CHARM = 7597              # Worgen's Command 53070, the charm glow

# Every stock SpellVisual id above, for the patch script's dry-run existence check.
STOCK_SPELL_VISUALS = (
    RG_LOCK_UP_LEAP, RG_CELL_TELEPORT_FLASH, RG_SOUL_DRAIN_CHANNEL, RG_FRAGMENT_STREAK, RG_KEY_SPARKLE,
    RC_MEAT_HOOK, RC_BUTCHERS_CUT,
    BS_ECHO_GHOST, BS_ECHO_ARRIVAL, BS_ACCURSED_VEIL,
    SP_HAMMER_LANDING, SP_SEARING_LIGHT, SP_CONSECRATION, SP_HOLY_LIGHT, SP_DIVINE_SHIELD, SP_RISE_UNHOLY,
    SP_RISE_HOLY, SP_WRATH_OF_GOD,
    OD_HOWLING_RAGE, OD_MAUL, OD_FRENZY, OD_BELL_RING_FLASH, OD_DEAFENED, OD_CRACKED_BELL_SMOKE,
    DC_CHARGE, DC_CLEAVE, DC_ENRAGE,
    FN_LIGHTNING, FN_SHADOW_LIGHTNING_FALLBACK, FN_VOID_PULSE, FN_SHADOWFORM, FN_SHADOW_LEAP_DEPARTURE,
    NA_TERRIFYING_HOWL, NA_ACID_SLAVER, NA_LUNGE, NA_MARK_THE_PREY, NA_PACK_BOND,
    AR_THUNDERSHOCK, AR_VOID_BOLT, AR_CURSE, AR_SHADOW_PORT, AR_ECLIPSE, AR_STARFALL_STATE, AR_MOONFIRE_COLUMN,
    AR_WARD_RUNE, AR_WARD_HANDS, AR_WARD_CLEANSE, AR_VIAL_THROW, AR_VIAL_CLOUD, AR_MOONLIT_BEAM, AR_CURSE_50,
    AR_TURNED_TRANSFORM, AR_TURNED_CHARM,
)
STOCK_CREATURE_DISPLAYS = (DISPLAY_INVISIBLE_STALKER, DISPLAY_SOUL_WISP, DISPLAY_TAINTED_WISP, DISPLAY_ECHO_RETHILGORE,
                           DISPLAY_ECHO_ODO, DISPLAY_GLUTTON_WORGEN)
STOCK_GAMEOBJECT_DISPLAYS = (GODI_ALARM_BELL, GODI_BLOOD_POOL)
