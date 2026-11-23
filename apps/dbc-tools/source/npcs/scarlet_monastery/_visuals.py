"""
Scarlet Monastery build, WP V (both waves, D1-D14, written in one pass because both waves deploy together): the visual
ids the boss files use, one place (not loaded on its own: the leading underscore keeps the package loader from treating
it as a declaration file; boss files import it with `from ._visuals import ...`, like `_common.py` and
blackrock_depths/_visuals.py). A boss WP asks for a change in its report; nobody else edits this file.

Source: .agents/plans/scarlet-monastery-build/scarlet-monastery-build.VISUALS-REPORT.md ("Per-boss id list" and Part 1;
ids, kits, mesh bounds and textures read, nothing rendered, so every look is unconfirmed until seen in game) and the top
pick of each row (handoff s3.10, user ruling 2026-11-20 on s7 #34: every top pick approved, the WRONG doc looks
replaced, the Ascension pillar model ships in patch-M). The constants below are the corrected ids, never the build
spec's originals where the spec's pick draws nothing or something else (lib/test_scarlet_monastery_vfx.py pins the wrong
ones out).

Four kinds of constant:

- MINTED (client patch-M, by apps/dbc-tools/patch_scarlet_monastery_vfx_models.py, ids.yaml reservation
  `scarlet_monastery`, spellvisual 90550-90599, creaturedisplayinfo 90800-90829): the `SV_*` names in the first
  section and the minted `DISPLAY_*` ones. They must equal the patch script's constants (the test pins it). One
  Ascension model ships into patch-M (`--extract` pulls it). 90565-90599 stay spare for the tuning round.
- SHIPPED (already in patch-M or the working copy): the Blackrock Depths / Spire, Stratholme and Deadmines rows. Nothing
  ships for them; the dry run checks they exist in the working-copy DBCs. Their names here start with `SHIPPED_`.
- STOCK: ids that already exist in the 3.3.5 client. Nothing ships and no id is minted.
- TELEGRAPH MARKERS (kit displays 91000-93999) are not named here: the boss files use the mod-boss-mechanics registry
  kinds and `Color(...)`, never a display id.

Prefixes tell the table of an id: `SV_` / `SHIPPED_` / `<boss code>_` are SpellVisual ids, `DISPLAY_` creature displays,
`GODI_` gameobject displays, `ITEM_` item entries, `IDI_` item displays (the weapon model an item shows).

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A STATE look plays on every unit that
carries the aura (so only put it on an aura, a stalker aura for a ground patch). An AREA look is for a spell with a
dynamic object (an area aura). An impact kit plays once, so a lasting effect re-casts it every 2-3 s or uses the
lasting twin named here. Boss codes (the spec's mechanic id prefixes): VI Vishas, IR Ironspine, CV the Council
(Azshir and the Fallen Champion), TH Thalnos, RH the risen heroes (Thalnos's hard mode), LK Loksey, AN Kell, LB Hollis
Grey, DN Doan, HM the hard modes (Doan's Heresy: ICY_DEATH / FISSURE / RAISE; Herod's Call to Arms: PRAYER_PILLAR /
KNEEL / BEAM / HALL / RED_AURA; Whitemane's Truth: FEAR / TELEPORT / WARD / CURSE / LIGHT / VERDICT / SPIRIT), AR Crell,
MA Halden, HB Herod, GD Thorne, LS the Last Stand, WM Whitemane.

Ids that must NOT be wired are listed in the test (WRONG_SPELL_VISUALS and friends): Grave Rot SV 118, Soul Drain,
Arcane Channeling, Blood Link, Summon Spirits, Battle Standard, Throw Axe 40563 / Axe Volley, Whirlwind 8989,
the Ashbringer aura, Beam of Light, Heated Hammer, Molten Armor, Scalding Steam, Flame Patch and every other pick the
report marks WRONG; CDI 21955 is a Rabbit.
"""

# --- Minted (patch-M) -------------------------------------------------------------------------------------------------

# Grave Rot pool rungs (IR, W1): the stock `goo_flow_state` as a STATE on a stalker, key = radius in yd. 6 yd is the
# shipped Strat rung (SHIPPED_GUT_PUDDLE_STATE). The boss swaps the stalker's aura as the pool grows (7 -> 10 yd in
# heroic); the Eye's pools use the 7 yd rung; a part crumbling to rot uses the 7 yd rung at the part's spot.
SV_GRAVE_ROT = {7: 90550, 8: 90551, 9: 90552, 10: 90553}
# The hard mode red aura (TH, the answered stones, the blood rite on the wall, Herod): the stock
# `deathknight_plaguestrikestatered` blood state at its own scale, as a STATE on the base.
SV_RED_AURA = 90554
# Held seal glows on the Fallen Champion (CV, optional): STATE rows from the three stock impact models. Whether the
# client loops an impact model is untested: the fallback is the one-shot SV re-cast every 3 s (the BRD rule).
SV_SEAL_COMMAND = 90555
SV_SEAL_RIGHTEOUSNESS = 90556
SV_SEAL_JUSTICE = 90557
# Emerald Dream mist, 6 / 9 / 12 yd (LB, +3 yd per page): the stock `LargeGreenRadiationFog` (particles, tune the scale
# in game). The boss swaps the rung per page. Key = radius in yd.
SV_DREAM_MIST = {6: 90558, 9: 90559, 12: 90560}
# Plague Cask persistent cloud, 8 yd (AN, optional: the stock Disease Cloud SV 7184 is the first pick).
SV_PLAGUE_CLOUD = 90561
# Herod's Consecrated Hall (HM, the whole floor): the stock `holyzone` at hall radius 25.5 yd / 3.2.
SV_CONSECRATED_HALL = 90562
# Holy light pillars (Ascension `lightsjudgement_impact`, 2.9 yd wide at scale 1): Herod's prayer (3 yd) and Whitemane's
# Penance / the father's light (6 yd). The stock Beam of Light SV 12479 is a 135 x 135 x 315 yd model: never wired.
SV_PILLAR_3 = 90563
SV_PILLAR_6 = 90564

# Minted creature displays (CreatureModelData + CreatureDisplayInfo rows of the patch script, each with its
# creature_model_info row in the same SQL). The spectres are the base display at alpha 128 / 140.
DISPLAY_SPECTRE_GALVAR = 90800       # copy of 25917, alpha 128
DISPLAY_SPECTRE_FAIRBELL = 90801     # copy of 25842 (Valroth), alpha 128
DISPLAY_SPECTRE_VOSS = 90802         # copy of 10339 (Isillien), alpha 128
DISPLAY_SPECTRE_GOODCHILDE = 90803   # copy of 25841 (Rodrick), alpha 128
DISPLAY_SPECTRE_ALEXANDROS = 90804   # copy of 16139 (mounted Mograine rider, x1.5), alpha 140
DISPLAY_CURSED_BOOK_OPEN = 90805     # optional: the stock open book `BookLargeOpen02` (0.9 x 1.1 yd); creature scale 3
DISPLAY_RALLYING_BANNER_CRIMSON = 90806    # optional: `CrimsonBanner01` (0.3 x 3.2 x 4.6 yd)
DISPLAY_RAVAGER = 90807              # optional, untested as a creature model: `Axe_2H_War_C_01`; stock GODI 8494 first

# Scale hints set on the creature, not in the DBC (floats on purpose: not ids).
CURSED_BOOK_SCALE_RANGE = (3.0, 4.0)       # CDI 28103 is 0.5 x 0.3 x 0.2 yd; 3 to 4 reads as a 2 yd book
GRAVE_ROT_SCALE_NOTE = 0.25                # goo_flow_state scale for the 6 yd rung; r yd = 0.25 * r / 6
FIST_SCALE_RANGE = (2.5, 3.0)              # CDI 26687 is a 0.4 x 1.0 x 0.2 yd forearm bone
EYE_SCALE_RANGE = (2.5, 3.0)               # CDI 2421 is a 0.5 yd eyeball
SPIDERLING_SCALE = 0.5                     # CDI 9756
PUP_SCALE = 0.7                            # CDI 2709 hound x0.85, pups at 0.7
SEEDLING_SCALE_RANGE = (0.5, 1.0)          # CDI 14392 sprout then bud
BRAMBLE_SCALE = 0.7                        # CDI 12347 (x1.75 model, 2.6 x 5.0 x 2.7 yd) rooted
PORTAL_GO_SIZE = 0.45                      # GODI 4711 is 8.8 yd tall: about 4 yd
HALL_RADIUS = 25.5                         # Herod's pit + ledge ring (NAVMESH-REPORT); SV_CONSECRATED_HALL = r / 3.2

# --- Shipped (patch-M and the working copy) ---------------------------------------------------------------------------

# Blackrock Spire: the lava pool ladder (Ascension `magmazone`), STATE on a stalker, key = radius in yd.
SHIPPED_LAVA_POOL = {4: 90606, 5: 90607, 6: 90608, 7: 90609, 8: 90610, 9: 90611, 10: 90612}
LAVA_POOL_RADII = tuple(sorted(SHIPPED_LAVA_POOL))
SHIPPED_SHADOW_POOL_6_STATE = 90605     # Ascension shadow quad, 6 yd (AREA twin 90604)
SHIPPED_ORANGE_RING = 90613             # Odyn orange rune ring, 3.8 yd under the bearer (a mark)
SHIPPED_YELLOW_RING = 90614
SHIPPED_HELD_TORCH = 90603              # StateKit `TorchSpell` in the right hand, lasting
# Blackrock Depths: the purple ring, the 6 yd web patch STATE, the red portal anchor.
SHIPPED_PURPLE_RING = 90657
SHIPPED_WEB_PATCH_6_STATE = 90659
SHIPPED_PORTAL_ANCHOR = 90658
# Stratholme: web patches, the lasting keening skull, the fire zones, the gold holy zones (key = radius in yd), the 6 yd
# gut puddle.
SHIPPED_KEENING_SKULL = 90506           # a lasting head state (Curse of Weakness head)
SHIPPED_FIRE_ZONE_8 = 90508
SHIPPED_HOLY_ZONE = {4: 90509, 5: 90510, 6: 90511, 8: 90512}
HOLY_ZONE_RADII = tuple(sorted(SHIPPED_HOLY_ZONE))
SHIPPED_GUT_PUDDLE_STATE = 90505        # goo_flow_state x0.25, 6 yd (AREA twin 90504): Ironspine's 6 yd rung
# Deadmines: the green goo puddle (4 yd).
SHIPPED_GOO_PUDDLE_STATE = 90343        # State (a stalker aura)
# The Paladin rework: the falling hammer over the target and its burst (Execution Sentence).
SHIPPED_EXECUTION_SENTENCE = 90044
SHIPPED_EXECUTION_SENTENCE_BURST = 90045

# ===== Wave 1: Graveyard (D1-D4) =====

# Interrogator Vishas (D1)
VI_INTERROGATION_CAST = 11627       # Interrogation 52805: the cast animation only (its impact is a gray ash puff)
VI_CONFESSION_MARK = SHIPPED_KEENING_SKULL    # the lasting mark over the carrier's head (+ the red 8 yd ring marker)
VI_BRANDING_IRON = 1946             # Burning Brand 29618: fire hands + a lasting Immolate base state (the 15 yd cone
                                    # is the marker)
VI_BRANDING_IRON_ALT = 10800        # Branding Iron Hit 48614: one-shot head impact
VI_TORMENT = 788                    # Drain Soul 32862: a `Beam_Purple` channel to the soaked one (NEVER SV 9364)
VI_TORMENT_ALT = 277                # Mind Flay 16568: a ManaBeam chain
VI_PAIN = 71                        # unchanged stock Shadow Word: Pain
ITEM_VISHAS_WEAPON = 5532           # "Monster - Hot Iron Poker": his stock weapon, equipped at the 70% yell
IDI_VISHAS_WEAPON = 8078            # Knife_1H_HotPoker_A_01
ITEM_VISHAS_STARTING_TORCH = 1906   # "Monster - Torch": the alternate before 70% (the default is unarmed)
DISPLAY_VISHAS = 2044

# Ironspine (D2)
IR_GRAVE_ROT = SHIPPED_GUT_PUDDLE_STATE      # the 6 yd rung; 7-10 yd are SV_GRAVE_ROT (see `grave_rot_rung`)
IR_FIST_LANDING = 8083              # Ground Slam 33525: ThunderClap ring (6.9 yd) + shake, one-shot
IR_CRUSH_HELD = 15325               # Ribcage 69065: the impaled pose on the prisoner (State, anim 132, no model)
IR_GLARE = 9205                     # Eyebeam 40620: a Beam_Red channel from the Eye (NEVER SV 7434, no beam)
IR_REASSEMBLED = 2737               # Bone Armor 11445: lasting
IR_REASSEMBLED_ALT = 4362           # Bone Shards
IR_SHATTER = IR_REASSEMBLED_ALT     # the Shatter burst (D2 wired the alias's value; boss files may import either name)
DISPLAY_IRONSPINE = 5231            # stock skeleton, x1.15
DISPLAY_IRONSPINE_FIST = 26687      # SC_BoneArm_01: stand animation only (the hop is a script jump arc)
DISPLAY_IRONSPINE_FIST_ALT = 9786   # SkeletonNaked at creature scale 0.4 (has a walk)
DISPLAY_IRONSPINE_RIBCAGE = 31124   # BoneGuardSpike (a spike, not a ribcage)
DISPLAY_IRONSPINE_EYE = 2421        # EyeOfKilrog

# The Council: Azshir and the Fallen Champion (D3)
CV_HOLY_SHOCK = 135
CV_HOLY_LIGHT = 2936
CV_HOLY_WRATH = 126                 # Holy Wrath 52836: RighteousFury chest + stun swirl (10 yd circle = marker)
CV_EXORCISM = 324
CV_SEAL_COMMAND = 7992              # the one-shot impact: re-cast every 3 s unless SV_SEAL_COMMAND loops
CV_SEAL_RIGHTEOUSNESS = 7986
CV_SEAL_JUSTICE = 9504
CV_RIGHTEOUSNESS_BURST = 5600       # Consecration PersistentArea at 6 yd, or the shipped holy zone below
CV_RIGHTEOUSNESS_BURST_ALT = SHIPPED_HOLY_ZONE[6]
CV_JUSTICE_MARK = 322               # Hammer of Justice 5589: fist cast + stun swirl, NOT a thrown hammer
CV_JUSTICE_HAMMER = SHIPPED_EXECUTION_SENTENCE    # the falling hammer on the target
CV_AVENGERS_SHIELD = 7886
CV_EXECUTION_SENTENCE = SHIPPED_EXECUTION_SENTENCE
CV_EXECUTION_SENTENCE_BURST = SHIPPED_EXECUTION_SENTENCE_BURST
CV_ROOM_WAVE = 3643                 # Holy Nova
CV_VIGIL_CHANNEL = 10980            # Penance 47540: the ChannelKit hands + anim 124 only (no beam, no mark)
CV_VIGIL_RING = SHIPPED_HOLY_ZONE[5]    # the ring under the grave
CV_VIGIL_RISE = 1443                # Scarlet Resurrection: the rise
CV_GRIEF = 6943                     # BeastRageState head + BloodLust hands, lasting; per-stack growth = creature scale
CV_JUDGEMENT = 5651
DISPLAY_AZSHIR = 5534               # HumanMale x1.2, alpha 126 (the ghost)
DISPLAY_FALLEN_CHAMPION = 5230

# Bloodmage Thalnos and the Desecration hard mode (D4)
TH_BLOOD_RITUAL = 9585              # shadow-purple hands (RISKY: the red alternate is below)
TH_BLOOD_RITUAL_ALT = 15283         # Blood Nova hands: red
TH_BLOOD_BOLT = 9308
TH_BLOOD_LANCE = 15253              # blood_rain_impact ground impact (the line is the marker)
TH_FLAME_SPIKE = 10383              # cast hands; the 20 s pool is SHIPPED_LAVA_POOL[4] under the 4 yd marker
TH_FLAME_SPIKE_POOL = SHIPPED_LAVA_POOL[4]
TH_BOILING_BLOOD = 15286            # lasting on the carrier (5 s)
TH_BOILING_BLOOD_ERUPTION = 9312    # BloodyExplosion
TH_BLOOD_NOVA = 15283
TH_BLOOD_NOVA_RING = 9312
TH_BLOOD_BRAND = 14871              # MarkofBlood head + a red base state, lasting 12 s
TH_TELEPORT = 7934                  # Mass Teleport
TH_RAISE = 4582                     # Raise Dead 17473: the heroes rising (NEVER SV 8116, two hand glows)
TH_BLOOD_PACT_TETHER = 7270         # Blood Siphon 24322: a Beam_RedDrops channel hero -> Thalnos (NEVER SV 15256)
TH_BLOOD_PACT_TETHER_ALT = 7301     # Blood Funnel
TH_HARD_MODE_AURA = SV_RED_AURA
TH_STONE_STIR = SHIPPED_HOLY_ZONE[4]    # a stone's faint glow (a stalker casts it; removed on the verdict)
TH_STONE_ANSWERED = SV_RED_AURA
TH_RITE_BLOOD = SV_RED_AURA         # the blood rite on the stair-head wall (a stalker casts it)
RH_CHARGE = 867
RH_REPENT = 5539
RH_GREATER_HEAL = 57
RH_PWS = 784                        # HolyDivineShield_State bubble, lasting
RH_WHIRLWIND = 7428                 # Whirlwind 26083: Cyclone_State x0.75 (NEVER SV 6664, a dust cloud)
DISPLAY_RALLYING_BANNER = 14541     # BattleStandard_Alliance (3.8 x 3.8 x 7.1 yd with its rune ring)
DISPLAY_GALVAR_BASE = 25917         # the risen heroes' stock displays (the spectres copy them at alpha 128)
DISPLAY_FAIRBELL_BASE = 25842
DISPLAY_VOSS_BASE = 10339
DISPLAY_GOODCHILDE_BASE = 25841
DISPLAY_RISEN_GALVAR = DISPLAY_SPECTRE_GALVAR
DISPLAY_RISEN_FAIRBELL = DISPLAY_SPECTRE_FAIRBELL
DISPLAY_RISEN_VOSS = DISPLAY_SPECTRE_VOSS
DISPLAY_RISEN_GOODCHILDE = DISPLAY_SPECTRE_GOODCHILDE
DISPLAY_PHANTASM = 4629             # Shade (the wrong-answer phantasm)
DISPLAY_THALNOS = 11396             # SkeletonMage x1.3
GODI_GRAVESTONE = 499               # TombStone02 (the four stones may differ: the alternates below)
GODI_GRAVESTONE_ALTS = (193, 2452, 19)
GODI_BLOOD_RITE = 15                # WantedPosterScroll01 (hangs on a wall)
GODI_BLOOD_RITE_ALT = 4672          # TaurenWallScroll02Blue; 4211 `BloodOfHeroes` is a floor blood pool

# ===== Wave 1: Library (D5-D8) =====

# Houndmaster Loksey (D5)
LK_WHISTLE = 8839                   # cast anim 81 + sound 3980 only
LK_SCENT = 15364                    # the one-shot flash; the lasting mark is the ring below
LK_SCENT_RING = SHIPPED_ORANGE_RING
LK_SCENT_RING_ALT = SHIPPED_PURPLE_RING
LK_LEAP_LANDING = 9006
LK_WHIPPED_FRENZY = 8147
LK_CORRECTION = 219
LK_FETCH = 10809                    # a thrown red yarn ball; there is no stick model
LK_LEAP_TRAIL = 29                  # Leap 47482: ChargeTrail + dust, the dog's take-off (the BRD GR_SIC_LEAP look)
DISPLAY_LOKSEY = 2040
DISPLAY_TRACKING_HOUND = 2709       # Hyena (red skin, x0.85); pups at creature scale PUP_SCALE

# Ambrose Kell (D6)
AN_SHATTER = 7984
AN_PLAGUE_CLOUD = 7184              # Disease Cloud 24063: a PersistentAreaKit (untested stretch to the radius)
AN_PLAGUE_CLOUD_ALT = SV_PLAGUE_CLOUD
AN_STAFF_LINE = 9947
AN_SKELETON = 2596
AN_PLAGUE_FLASK = 9705
AN_PLAGUE_FLASK_POOL = SHIPPED_GOO_PUDDLE_STATE
AN_ARCANE_TORRENT = 7346
AN_BONE_CURSE = 2737                # lasting 8 s
AN_BONE_CURSE_BURST = 4362
AN_TROPHY_CASK = 9705               # the trophy look changes (heroic): the flask's state base
AN_TROPHY_STAFF = 9937              # arcanepower_state_chest
AN_TROPHY_SKULL = 2737
DISPLAY_KELL = 2524                 # Scarlet Sorcerer
DISPLAY_KELL_SKELETON = 9786        # SkeletonNaked, black skin
DISPLAY_KELL_SKELETON_ALT = 7550    # white skin
GODI_RELIC_PEDESTAL = 7695          # BattlemasterPedestal (NEVER the Karazhan Pedestal 7273: 5.2 yd tall)
GODI_RELIC_CASK = 288               # Barrel02
GODI_RELIC_STAFF = 1708             # BrambleStaff
GODI_RELIC_STAFF_ALT = 2455         # HumanStaff02
GODI_RELIC_SKULL = 217              # BattleGladeSkullHumanDark
GODI_RELIC_SKULL_ALT = 226          # BlastedLandsSkull02

# Lector Hollis Grey (D7)
LB_OPEN_BOOK = 8355                 # Pet Book Graphic 35720: a bookmedium04 state over the book
LB_WEB = SHIPPED_WEB_PATCH_6_STATE  # the patch (exact 6 yd)
LB_WEB_SPRAY = 7613
LB_WEB_HATCH = 3999
LB_METEOR = 4859                    # Archimonde's Return 1122: an infernal falls (8 yd marker underneath)
LB_IMMOLATION = 2519                # Immolation 20153: the Infernal's fire chest impact (no state; re-cast per tick)
LB_AXES = 3962                      # Throw Axe 16075: missile_axe_copper in flight (NEVER SV 9766 / 9220)
LB_STOMP = 2355
LB_STOMP_RINGS = 8083
LB_MIST = 10122                     # stock blue-green fallback; the emerald rungs are SV_DREAM_MIST
LB_SLEEP = 3859
LB_GRUNT_CHARGE = 867
LB_REBUKE = 128
LB_BURNING_BOOK = SHIPPED_LAVA_POOL[5]
LB_WARD = 968                       # Arcane Bubble ManaShield_State
LB_WARD_ALT = 11817                 # Divine Protection chest state
DISPLAY_CURSED_BOOK = 28103         # Book_Human_01 (NEVER the doc's 21955, a Rabbit); scale CURSED_BOOK_SCALE_RANGE
DISPLAY_HOLLIS_GREY = 2492          # Scarlet Abbot
DISPLAY_TROLL_AXE_THROWER = 29716   # Ghostly Troll Celebrant (alpha 128)
DISPLAY_TROLL_AXE_THROWER_ALT = 29234
DISPLAY_GHOST_ORC_GRUNT = 17459     # Agitated Orc Spirit (alpha 128)
DISPLAY_GHOST_ORC_GRUNT_ALT = 18051
DISPLAY_INFERNAL = 169
DISPLAY_SPIDERLING = 9756           # MineSpider (crystal skin, x0.5): creature scale SPIDERLING_SCALE

# Arcanist Doan and the Kel'Thuzad Heresy (D8)
DN_BUBBLE = 968
DN_ANCHOR_BEAM = 8795               # Magic Barrier 38112: a ManaBeam channel anchor -> Doan (NEVER SV 6742)
DN_ANCHOR_BEAM_ALT = 8492           # Arcane Glare (Beam_Purple)
DN_DETONATION = 1585                # fire-themed (RISKY: the damage is Fire)
DN_EXPLOSION = 965
DN_OVERLOADED = 9937                # Arcane Power state
DN_MARK = 10692                     # Living Bomb 44457: the lasting state on the carrier
DN_MARK_BURST = 10693               # Living Bomb 44461: the burst (the doc names 44457)
DN_SCORCHED = SHIPPED_LAVA_POOL[5]
DN_POOL = SHIPPED_LAVA_POOL[4]      # the Righteous Fire pool (3 yd real: the smallest shipped rung is 4 yd)
DN_FLAMESTRIKE = 10383
HM_ICY_DEATH = 2837                 # Frostbite 12494: a lasting frost state (the doc's SV 13 is a missile)
HM_ICY_DEATH_ALT = 675
HM_FISSURE = 12678                  # a 5.2 yd model at x3.5 (about 18 yd): oversize for the 6 yd fissure
HM_FISSURE_ALT = SHIPPED_SHADOW_POOL_6_STATE    # the exact 6 yd look
HM_RAISE = 4582
DISPLAY_DOAN = 5266
DISPLAY_DOAN_ANCHOR = 24813         # ScryingOrb (alternates 26753 / 22506)
DISPLAY_DOAN_ANCHOR_ALT = 26753
DISPLAY_DOAN_ANCHOR_ALT_2 = 22506
DISPLAY_PHYLACTERY_SHARD = 24889    # Lichcontainer01
DISPLAY_RISEN_PURGED = 23887        # Scourged Scarlet Footman (male; 23888 the female)
DISPLAY_RISEN_PURGED_ALT = 23888
GODI_CHAMBER_BARRIER = 523          # RazorfenForceField01 (0.6 x 9.5 x 9.2 yd, scale by the GO template size)
GODI_EVIDENCE_BOOK = 255            # G_Book01 (a built-in glow)
GODI_EVIDENCE_SCROLL = 210          # G_Scroll01

# ===== Wave 2: Armory (D9-D11) =====

# Forgemaster Gideon Crell (D9)
AR_SPARKS = 380
AR_SLAG = SHIPPED_LAVA_POOL[4]      # the 3 yd pool is 1 yd over on the smallest shipped rung
AR_SLAG_BURST = 963                 # Fire Nova
AR_ANVIL_STRIKE = 11517
AR_STEAM = 8657                     # Scalding Water 37284: steam.mdx State on a stalker (NEVER SV 10373)
AR_STEAM_ALT = 8437
AR_CLEAVE = 219
AR_DASH = 867
AR_PLATE = 1946                     # Burning Brand state: the Red-Hot Plate glow (SV 7757 / 289 are one-shot)
AR_RIVET = 67                       # Fireball (NEVER SV 7671, the silver holy hammer)
DISPLAY_CRELL = 3278                # Godric Rothgar, Armorer (alternates 3275 / 2522)
DISPLAY_CRELL_ALT = 3275
DISPLAY_CRELL_ALT_2 = 2522
DISPLAY_SCARLET_TRAINEE = 2467      # unarmed (2478 the other gender)
DISPLAY_SCARLET_TRAINEE_ALT = 2478
GODI_FORGE = 7044                   # OM_Forge_01 (NEVER 197, a brazier)
GODI_FORGE_ALT = 233
GODI_ANVIL = 273
GODI_TROUGH = 216                   # Cauldron (no trough model exists in the client)
GODI_TROUGH_ALT = 239
GODI_TROUGH_ALT_2 = 3012

# Drillmaster Corin Halden (D10)
MA_CHARGE = 867
MA_SPEARS = 13365                   # equip the recruits with a spear item: the animation needs a polearm
MA_JAVELIN = 11993
MA_CLOSE_RANKS = 345                # an impact: re-cast while the ring turns
DISPLAY_HALDEN = 2514               # Scarlet Myrmidon
DISPLAY_DRILL_RECRUIT = 2522        # Scarlet Soldier

# Herod and the Call to Arms hard mode (D11)
HB_CYCLONE = 7428                   # Whirlwind 26083 (NEVER SV 6664, a dust cloud)
HB_THROW = 3962                     # Throw Axe 16075 (NEVER SV 9220: no axe in flight)
HB_BLADE = 8618                     # Fury of the Ashbringer 43225: a flying Sword_2H_Ashbringer (NEVER SV 7582)
HB_CLEAVE = 219
HB_ZEAL = 211                       # one-shot per stack
HB_FRENZY = 870                     # Frenzy 8269: a glow on Herod's Frenzy (SpellVisualID_1 of 212993)
HB_FLOOR_SPIN = 6044
HB_RAVAGER_GLOW = 11876             # beacon_of_light_impact: one-shot, replay every 4 s
HM_PRAYER_PILLAR = SV_PILLAR_3
HM_KNEEL = 14427                    # State kit with animation 115 (no model)
HM_BEAM = 11500                     # stock Light Beam 52407 (HealBeam chain, used in Strat) between stalkers
HM_HALL = SV_CONSECRATED_HALL       # NEVER SV 14914 (an 8.2 yd quad) or SV 5600
HM_RED_AURA = SV_RED_AURA
ITEM_HEROD_BLADE = 39802            # Crusader's Greatblade, his off-state weapon at the rising
IDI_HEROD_BLADE = 50331             # Sword_2H_Northrend_B_02Blue
DISPLAY_HEROD = 2041
DISPLAY_GARRISON_TRAINEE = DISPLAY_SCARLET_TRAINEE
ITEM_TRAINEE_MACE = 2813            # the death swarm's weapon (stock entry 6575)
GODI_PLANTED_RAVAGER = 8494         # ORCAXE02 (a stuck orc axe, no collision) scaled by the GO size
GODI_RAVAGER_RACK = 130             # GeneralWeaponrack01
GODI_RAVAGER_SWORDS = (669, 670)    # HumanSword01 / 02 on the wall

# ===== Wave 2: Cathedral (D12-D14) =====

# Brother Aldous Thorne (D12)
GD_SEED = 10713                     # DruidMorph impact on the carrier (one-shot)
GD_BLOOM = 11568
GD_BRIAR = 38                       # EntanglingRoots_State, lasting
GD_BRIAR_ALT = 201
GD_SWEEP = 219
GD_HOLY_WATER = 12483
GD_BLESSED_GROUND = SHIPPED_HOLY_ZONE[8]    # 8 yd (NEVER Consecration SV 5600: the Last Stand's look)
GD_POLLEN = 8529                    # RISKY: arcane violet, not a yellow pollen
GD_POLLEN_ALT = SHIPPED_HOLY_ZONE[4]    # a gold pulse reads better
GD_BLESS_CAST = 563
DISPLAY_THORNE = 2502               # Scarlet Chaplain, MALE (the doc's 2501 is the female)
ITEM_THORNE_SCYTHE = 20536          # Soul Harvester (NEVER 13163 / 5749: a greatsword and a war axe)
IDI_THORNE_SCYTHE = 33087           # Stave_2H_Scythe_C_03
DISPLAY_SEEDLING = 14392            # Thornling (Lasher x0.2): creature scale SEEDLING_SCALE_RANGE
DISPLAY_BLESSED_BRAMBLE = 12347     # Barbed Lasher x1.75: creature scale BRAMBLE_SCALE
DISPLAY_CHAPLAIN_FEMALE = 2501

# The Last Stand: Mograine and the companies (D13)
LS_DEVOTION = 199                   # RighteousnessAura_Base state (lasting)
LS_DEVOTION_APPLY = 160
LS_CONSECRATION = 11182             # shares one ground model with SV 5600: wired only for the Monks
LS_CONSECRATION_ALT = SHIPPED_HOLY_ZONE[6]
LS_FIREBALL = 67
LS_FLAME = 10383
LS_FLAME_POOL = SHIPPED_LAVA_POOL[5]
LS_GREATER_HEAL = 135
LS_HAMMER = 7250                    # Hammer of Wrath 24275: the thrown silver hammer (SV 322 on the victims)
LS_HAMMER_STUN = 322
LS_DIVINE_STORM = 12006
LS_CHARGE = 867
ITEM_CAPTAIN_SWORD = 1899
ITEM_CAPTAIN_SHIELD = 1984
DISPLAY_CAPTAIN = 2460              # Scarlet Champion (2461 the other gender), as Scarlet Soldier 4286
DISPLAY_CAPTAIN_ALT = 2461
DISPLAY_CAPTAIN_ALT_2 = 2462        # Scarlet Defender, already sword + kite shield
DISPLAY_COMPANY_CHAPLAIN = 2501
DISPLAY_COMPANY_CHAPLAIN_ALT = 2502
DISPLAY_COMPANY_MONK = 2603
DISPLAY_COMPANY_MONK_ALT = 2604
DISPLAY_COMPANY_WIZARD = 2526
DISPLAY_COMPANY_WIZARD_ALT = 2525
DISPLAY_COMPANY_ABBOT = 2492
DISPLAY_MOGRAINE = 2042

# Whitemane (D14)
WM_DEEP_SLEEP = 87
WM_RESURRECTION = 1443
WM_LAY_ON_HANDS = 132
WM_CHARGE = 867
WM_PENANCE_RING = SHIPPED_YELLOW_RING   # the mark under each marked player (SV 10980 is hands only)
WM_PENANCE_RING_ALT = SHIPPED_PURPLE_RING
WM_PENANCE_CHANNEL = 10980          # hands on Whitemane
WM_PENANCE_PILLAR = SV_PILLAR_6
WM_HEAL = 135
WM_PWS = 784
WM_BODY_SHIELD = 154                # Divine Shield state on Mograine (distinct from the PWS bubble)
WM_VIGIL_FLAME = SHIPPED_HELD_TORCH     # the vigil candle: a held torch on the carrier
WM_VIGIL_FLAME_PASS = 3400          # Holy Fire on each pass
WM_SEARED = 1946
WM_SEARED_ALT = 235
WM_SMITE = 128
WM_KNEEL = HM_KNEEL
HM_FEAR = 247
HM_TELEPORT = 9226
HM_WARD = 11817                     # Inquisitor's Ward: Divine Protection (PWS 784 is already the pair's shield)
HM_WARD_ALT = 968
HM_CURSE = 876
HM_CURSE_MARK = 14871               # the red state for the 12 s mark
HM_LIGHT = 5651
HM_LIGHT_PILLAR = SV_PILLAR_6
HM_VERDICT = 8618                   # Fury of the Ashbringer: the flying blade along the line (the line is the marker)
HM_VERDICT_IMPACT = 7160            # Holy Wrath 23979
HM_SPIRIT_GLOW = 7880               # avengingwrath_state_chest
HM_DIVINE_STORM = LS_DIVINE_STORM
ITEM_ALEXANDROS_BLADE = 22709       # equipment of the spirit (IDI 35112 Sword_2H_AshbringerCorrupt)
IDI_ALEXANDROS_BLADE = 35112
DISPLAY_FAIRBANKS = 2605
DISPLAY_WHITEMANE = 2043
GODI_LAST_STAND_CHEST = 1387        # the Chest of The Seven's (the Last Stand's chests, GO 301330 / 301331)
GODI_VIGIL_TORCH = 442              # G_TorchLever (GO 97701)
GODI_SECRET_DOOR = 441              # MonasterySecretDoor (GO 97700)

# ===== Portals, doors, shared looks =====

DISPLAY_INVISIBLE_STALKER = 11686   # the invisible stalker skin every kit helper wears (BRD / BRS / Strat precedent)

GODI_WING_PORTAL = 4711             # InstancePortal_Red (the dungeon-entrance swirl), GO size PORTAL_GO_SIZE, x4
GODI_WING_PORTAL_ALT = 672          # blue (6450 green, 7148 purple)
GODI_WING_PORTAL_ALT_2 = 6450
GODI_WING_PORTAL_ALT_3 = 7148
WING_PORTAL_SWIRL = SHIPPED_PORTAL_ANCHOR   # beside the GO if the plain one reads weak (a stalker casts it)
GODI_CHAPEL_DOOR = 1207             # ScarletCathedralDoor, no change
GODI_BOSS_DOOR = 443                # MonasteryBossDoor, no change


def lava_pool_rung(radius: float) -> int:
    """The shipped lava pool SpellVisual for a real radius: the smallest rung at or above it (10 is the top)."""
    return SHIPPED_LAVA_POOL[min((r for r in LAVA_POOL_RADII if r >= radius), default=LAVA_POOL_RADII[-1])]


def holy_zone_rung(radius: float) -> int:
    """The shipped gold holy zone for a real radius: the smallest rung at or above it (8 is the top)."""
    return SHIPPED_HOLY_ZONE[min((r for r in HOLY_ZONE_RADII if r >= radius), default=HOLY_ZONE_RADII[-1])]


def grave_rot_rung(radius: float) -> int:
    """The Grave Rot pool SpellVisual for a real radius: the smallest rung at or above it (6 is the shipped Strat gut
    puddle, 7-10 are minted; 10 is the top)."""
    rungs = {6: SHIPPED_GUT_PUDDLE_STATE, **SV_GRAVE_ROT}
    return rungs[min((r for r in rungs if r >= radius), default=max(rungs))]


def dream_mist_rung(radius: float) -> int:
    """The Emerald Dream mist SpellVisual for a real radius: the smallest rung at or above it (12 is the top)."""
    return SV_DREAM_MIST[min((r for r in SV_DREAM_MIST if r >= radius), default=max(SV_DREAM_MIST))]


# Every minted SpellVisual (checked against the patch script's rows, not the stock DBCs)
MINTED_SPELL_VISUALS = (
    *SV_GRAVE_ROT.values(), SV_RED_AURA, SV_SEAL_COMMAND, SV_SEAL_RIGHTEOUSNESS, SV_SEAL_JUSTICE,
    *SV_DREAM_MIST.values(), SV_PLAGUE_CLOUD, SV_CONSECRATED_HALL, SV_PILLAR_3, SV_PILLAR_6,
)
# Minted creature displays (CreatureDisplayInfo rows of the patch script; 90805-90807 also CreatureModelData)
MINTED_CREATURE_DISPLAYS = (
    DISPLAY_SPECTRE_GALVAR, DISPLAY_SPECTRE_FAIRBELL, DISPLAY_SPECTRE_VOSS, DISPLAY_SPECTRE_GOODCHILDE,
    DISPLAY_SPECTRE_ALEXANDROS, DISPLAY_CURSED_BOOK_OPEN, DISPLAY_RALLYING_BANNER_CRIMSON, DISPLAY_RAVAGER,
)
# Not in the stock client but already shipped (checked against the working-copy SpellVisual.dbc)
SHIPPED_SPELL_VISUALS = tuple(sorted({
    *SHIPPED_LAVA_POOL.values(), SHIPPED_SHADOW_POOL_6_STATE, SHIPPED_ORANGE_RING, SHIPPED_YELLOW_RING,
    SHIPPED_HELD_TORCH, SHIPPED_PURPLE_RING, SHIPPED_WEB_PATCH_6_STATE, SHIPPED_PORTAL_ANCHOR, SHIPPED_KEENING_SKULL,
    SHIPPED_FIRE_ZONE_8, *SHIPPED_HOLY_ZONE.values(), SHIPPED_GUT_PUDDLE_STATE, SHIPPED_GOO_PUDDLE_STATE,
    SHIPPED_EXECUTION_SENTENCE, SHIPPED_EXECUTION_SENTENCE_BURST,
}))


def _spell_visuals() -> set[int]:
    """Every SpellVisual id named above by a boss-code constant (any int constant whose prefix is a boss code)."""
    codes = ("VI_", "IR_", "CV_", "TH_", "RH_", "LK_", "AN_", "LB_", "DN_", "HM_", "AR_", "MA_", "HB_", "GD_", "LS_",
             "WM_")
    values = set()
    for name, value in globals().items():
        if name.startswith(codes) and type(value) is int:
            values.add(value)
    return values


# Every stock SpellVisual id above (the SpellVisual existence check): the boss-code constants minus the minted and
# shipped ones they alias.
STOCK_SPELL_VISUALS = tuple(sorted(_spell_visuals() - set(MINTED_SPELL_VISUALS) - set(SHIPPED_SPELL_VISUALS)))

STOCK_CREATURE_DISPLAYS = tuple(sorted({
    value for name, value in globals().items()
    if name.startswith("DISPLAY_") and type(value) is int and value not in MINTED_CREATURE_DISPLAYS
}))
STOCK_GAMEOBJECT_DISPLAYS = tuple(sorted({
    *(value for name, value in globals().items() if name.startswith("GODI_") and type(value) is int),
    *GODI_GRAVESTONE_ALTS, *GODI_RAVAGER_SWORDS,
}))
