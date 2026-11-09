"""
Stratholme build, WP-V (wave 1: the Service Entrance, S9-S15): the visual ids the boss files use, one place (not loaded
on its own: the leading underscore keeps the package loader from treating it as a declaration file; boss files import
it with `from ._visuals import ...`, like `_common.py` and scholomance/_visuals.py). Created by V-1; V-2 appended the
wave 2 constants (FlameZone, HolyZone, the Carrion fan, the lie judgment, the Main Gate picks; the last section of each
list below). A boss WP asks for a change in its report.

Source: .agents/plans/stratholme-build/stratholme-build.VISUALS-REPORT.md (ids, kits, mesh bounds and textures read;
nothing rendered, so every look is unconfirmed until seen in game), the top pick of each wave 1 row (handoff s3.10, s7
#21), with the look corrections of s3.10 applied: the constants below are the corrected ids, never the build spec's
originals where the spec's pick draws nothing or something else.

Two kinds of constant:

- MINTED (client patch-M, by apps/dbc-tools/patch_stratholme_vfx_models.py, ids.yaml reservation `stratholme`,
  spellvisual 90500-90549): the `SV_*` names in the first section (wave 1 90500-90506, wave 2 90507-90514). They
  must equal the patch script's constants of the same name (lib/test_stratholme_vfx.py pins it).
  All sit on stock models; no model or texture ships.
- STOCK: ids that already exist in the 3.3.5 client (SpellVisual.dbc, CreatureDisplayInfo.dbc,
  GameObjectDisplayInfo.dbc, SoundEntries.dbc) or, for SV_ACID_POOL / SV_ACID_POOL_STATE, in patch-M since the Deadmines
  work (shipped). Nothing ships for them and no id is minted. The test checks they exist in the working-copy DBCs.

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A StateKit look (marked STATE) plays on
every unit that carries the aura, so only put it on an aura (a stalker aura for a ground patch). A PersistentArea look
(marked AREA) is for a spell with a dynamic object (the area aura). A ChannelKit look shows only on a channeled spell.
An impact kit plays once. Names are `<boss code>_<what>`; boss codes: BT Barthilas, BA Baroness Anastari, NE
Nerub'enkan, MK Maleki, RG Ramstein, BR Baron Rivendare, HM the hard mode (Ysida, Risen); wave 2: UF The Unforgiven,
FO Hearthsinger Forresten, TM Timmy the Cruel, ML Malor the Zealous, WI Cannon Master Willey, GF Archivist Galford, DA
Dathrohan, BZ Balnazzar (and the Grand Lie's shared looks).
"""

# --- Minted (patch-M) -------------------------------------------------------------------------------------------------

# Nerub'enkan NE3 web patch: stock Web_State (SVEN 595, a 2.3 yd ground web quad) at a fixed scale (AreaEffectSize 0),
# 4.3 for a 5 yd radius (normal) and 6.0 for 7 yd (heroic). The AREA look is for an area aura spell (a dynamic object),
# the STATE look for a stalker aura (the patch unit, 300583: one stalker per patch). A flat web decal, no plague tint.
SV_WEB_PATCH_5_AREA = 90500
SV_WEB_PATCH_5_STATE = 90501
SV_WEB_PATCH_7_AREA = 90502
SV_WEB_PATCH_7_STATE = 90503
# Ramstein RG3 gut puddle (6 yd radius, 12 yd across): the Deadmines goo_flow_state pool (47.8 yd at scale 1) at 0.25.
# The shipped Fish Stew rows (SV_ACID_POOL, 4 yd radius) stay the fallback if the size does not matter.
SV_GUT_PUDDLE_AREA = 90504
SV_GUT_PUDDLE_STATE = 90505
# Baroness BA1 Keened skull: CurseofWeakness_Head (SVEN 311) as a StateKit on the unit, so it lasts the whole keen
# instead of Curse of Doom's 3 s impact kit. An aura look: put it on the Keened aura. No sound (kit 311's curse sound
# is a one-shot).
SV_KEENED_SKULL_STATE = 90506

# Wave 2 (V-2). The zone glows are one flat quad each (a spawn anim, then a loop), sized by a fixed scale: STATE looks
# for a stalker's aura (one stalker per ring or puddle; put the SV in the aura spell's SpellVisualID_1). The visible
# disc reaches about 0.8 of the half quad, so each ring is a glow just past the hitbox, not an exact hit shape (draw
# the hit with the telegraph kit). Unconfirmed in game: the scales are first guesses.
SV_FLAMEZONE_10_STATE = 90507       # FlameZone orange disc, 10 yd radius: the Unforgiven's firelight ring (UF)
SV_FLAMEZONE_8_STATE = 90508        # FlameZone orange disc, 8 yd radius: Forresten's hearth glow (FO)
SV_HOLYZONE_4_STATE = 90509         # HolyZone gold disc, 4 yd radius: a Galford holy-fire puddle (GF)
SV_HOLYZONE_5_STATE = 90510         # 5 yd
SV_HOLYZONE_6_STATE = 90511         # 6 yd
SV_HOLYZONE_8_STATE = 90512         # 8 yd; also Dathrohan's true-ground glow if the telegraph is not enough (DA)
# Carrion Swarm fan, 30 yd long and about 58 degrees wide at the apex on the caster, in a PrecastKit so it plays through
# the 2.5 s cast (the stock SV 9099 plays the 40 yd fan when the cast ends). Put it on BZ1's cast spell. The model
# follows the caster's facing; the script turns Balnazzar to the target every update, so the fan tracks. No stun
# swirl state (the stock SV 9099 has one). The 60 degree hit cone is wider than the drawn fan by about 2 degrees.
SV_CARRION_FAN = 90513
# The lie judgment (Judgement of Darkness): shadow hands on the cast, a red judgement flash on the target (the gold one
# of the true judgment, SV 5651, reads as a heal), and the stock shadow chest impact as the target impact.
SV_LIE_JUDGMENT = 90514

# --- Stock displays, sizes and sounds ---------------------------------------------------------------------------------

# Nerub'enkan (S11)
DISPLAY_WEB_COCOON = 16213          # Cocoon.mdx, 3.3 x 3.0 x 2.8 yd at scale 1: template scale about 0.8 for a player
WEB_COCOON_SIZE = 0.8
DISPLAY_INVISIBLE_STALKER = 11686   # the web patch stalker 300583 and every "aura on a stalker" (not display 411)

# Maleki (S12)
DISPLAY_ICE_TOMB = 30890            # the quest ice block: 9.6 x 9.5 x 5.8 yd at scale 1, no collision box,
ICE_TOMB_SIZE = 0.35                # display scale 1.5; rescale in creature_template_model to 0.3-0.4

# Ramstein (S13): the crawlers (Half-Digested Corpse 300586), Zombie.mdx
DISPLAY_CRAWLER = 1201              # ZombieSkinGreen (runner-up 1200 ZombieSkinBlack)
DISPLAY_CRAWLER_ALT = 1200

# Baron Rivendare (S14, S15)
DISPLAY_BARON_DEATHCHARGER = 10718  # RidingUndeadWarHorse (the mount)
GODI_BONE_PILE = 6328               # S14 bone pile (gameobject 301207): Blasted Lands spine and skull, 0.9 yd
GODI_BONE_PILE_ALT = 6329           # the same family, 0.7 yd
GODI_BONE_PILE_SKELETON = 4093      # HumanMaleDeathSkeleton: a lying skeleton (2.2 x 1.8 x 0.4 yd), third choice
# DISPLAY 293 (stock Pile of Bones 177604) is a troll skull pile: never wired (the test pins it stays out).
GODI_TROLL_SKULL_PILE_DO_NOT_USE = 293
DISPLAY_YSIDA_RISEN = 25355         # S15 Ysida, Risen: Death Knight Initiate outfit on the human female (ext. 17199)
DISPLAY_YSIDA_RISEN_ALT = 15967     # Ysida now (Argent Dawn crusader, keeps her face), plus the Hysteria aura

# Keening sound (Baroness BA1): played with a direct sound call by SoundEntries id on the doomed player or the boss
SOUND_KEENING = 1171                # BansheeDeath (a drawn-out wail); not heard yet, listen before keeping it
SOUND_KEENING_ALT = 1168            # BansheeAggro; 1172 PreAggro; 8451 ShriekCast; 17274 GhostsSpell

# --- Spells whose SpellVisual stands in for the cast (a copy of the stock visual id is all a spell needs) -------------

# Barthilas (S9): Infection and Contagion are green clouds; the cough, the grain and the fever are the rest
BT_INFECTION = 1712                 # Disease Cloud 12627: GreenGhost_state (green flame wisps), STATE
BT_CONTAGION = 761                  # Plague Cloud 3256: nature hands, chest ring, green fog burst
BT_NOXIOUS_FOG = 10395              # Noxious Cloud 21070: PersistentArea GreenRadiationFog (grain pile, cough
                                    # puddle, on a stalker), plus a green burst; the fog's radius is unmeasured
BT_GRAIN_SACK = 12216               # Vendor - Throw Sack To Player 56122: TrollDungeonSacks missile, ~0.65 yd at x0.6
BT_GRAIN_SACK_ALT = 15743           # Sack01_01 missile at x0.45 (no spell uses it)
BT_GRAIN_SACK_ALT_2 = 12674         # Throw Blight Barrel 59460: green plague barrel missile + acid pool
BT_FEVER = 47                       # Unholy Frenzy 8699: glowing hands STATE, the lasting buff look (Fever stacks)
BT_FEVER_ALT = 11514                # Hysteria 49016: DeathKnight_Hysteria STATE (Ysida takes it in the hard mode)
BT_FURIOUS_ANGER_FLASH = 2817       # Furious Anger 16791: a 1.5 s roar flash, only as the Bedlam cast flash (RISKY)

# Baroness Anastari (S10)
BA_KEEN_SKULL_FLASH = 5019          # Curse of Doom 603: purple skull over the head, an IMPACT kit (3 s)
BA_DEATH_KNELL = 45                 # Shadow Burst 28447: shadow nova ring on the chest + impact
BA_WAIL = 4341                      # Wail of Souls 17631: skull-spirit ribbon missile + shadow impact
BA_WAIL_ALT = 7945                  # Soul Scream 32421: shout ring + purple confusion marks over the head
BA_TERRIFIED = 4801                 # Howl of Terror 17928: Fear_State_Head + fear_state_base (a skull and frost-rune
                                    # ring at the feet), STATE. NOT Terrify 7399 (SV 736: a color tint only)
BA_VISAGE = 7945                    # Horrifying Visage cone cast: the Soul Scream shout look
BA_BANSHEE_SHRIEK = 569             # Banshee Shriek 16838: a 0.9 yd white ring + sound 3113 (a shout, not a veil lift)

# Nerub'enkan (S11)
NE_VENOM_SPIT = 4199                # Venom Spit 16552: breath hands, GooBolt missile, green burst (the glob NE2)
NE_STUCK = 684                      # Web 745: the ground web at the feet + the web missile (Stuck, 2 s)
NE_STUCK_ALT = 7298                 # Entangle: the webspin cocoon around the target
NE_WEB_WRAP = 7610                  # Web Wrap 28622: the webspin egg on the player (1.7 x 1.8 x 2.2 yd)
NE_WEB_PATCH_VENOM_SPRAY = 12013    # Venom Web Spray 54706: Web_State 2.3 yd + a plague state (a stalker aura)
NE_SKITTER_LEAP = 11441             # Heroic Leap 54506: a 6.9 yd ground crack at the landing + stun stars
NE_POISON_CLOUD = 139               # Poison Cloud 3815: green puffs on the chest, STATE (RISKY: no ground cloud)
NE_PLAGUE_FOG = 761                 # S11's Plague Fog look
NE_RAISE_SCARAB = 634               # S11's Raise Scarab look

# Maleki (S12)
MK_ICY_DEATH_CAST = 12328           # Chains of Ice 45524: ice hands, 3 yd chain mesh, path of frost
MK_ICY_DEATH_STATE = 8141           # Unstable Affliction 30108: shadow hands + a chest rot STATE (reads as a curse)
MK_SHATTER = 17                     # Frost Nova 122
MK_SIPHON_BEAM = 12655              # Drain Life 17238: chain 719 HealBeam_Desaturated, a gray-white wave (drain light)
MK_EYE_OF_BLIZZARD = 8787           # Blizzard 26607: Blizzard_Impact_Base as a PersistentAreaKit, 6.1 x 6.2 x 31 yd of
                                    # falling ice; put it on 4 or 5 stalkers over the plaza (the eye is a telegraph)
MK_ICE_TOMB_CAST = 4340             # Ice Tomb 16869: ice hands/head/base + ice barrier STATE + missile
MK_ICE_TOMB_SHELL = 4325            # Ice Block 45438: the icebarrier_state shell on a player (3.9 yd mesh)
MK_FROSTBITE_SEED = 8339            # Seed of Corruption 27243: shadow hands + chest state + a blood bolt (the spread)

# Ramstein (S13)
RG_CANNIBALIZE = 5724               # Cannibalize 20578: channel, star particles at the base, 2.8 s
RG_GORE = 39                        # Gore 4102: a hit flash + sound
RG_EXPOSE_WEAKNESS = 603            # Expose Weakness 7140: shadow hands + shadow burst + tint
RG_TRAMPLE = 2355                   # War Stomp 45: a 6.9 yd ground crack + stun stars; the telegraph ring shows the
                                    # 10-18 yd radius
# the gut puddle: SV_GUT_PUDDLE_AREA / _STATE above, or the shipped Fish Stew rows below

# Baron Rivendare (S14, S15)
BR_DEATH_AND_DECAY = 9735           # Death and Decay 49936: hands + a PersistentArea rune quad 7.6 yd (21.7 s
                                    # loop); about 1.6 times for 6 yd, untested whether the client stretches it
BR_EXECUTION_BEAM = 7785            # Shadow Sear 30735: chain 10 Beam_Purple (0.25 wide) + a purple chest glow, CHANNEL
BR_EXECUTION_BEAM_ALT = 8428        # Netherbeam 36089: chain 24 Beam_Purple, 0.5 wide (thicker)
BR_CHARGE = 3783                    # Charge 22911: chest trail + dust puff at the start, stun stars (the Deathcharger)
BR_CONDEMNED = 11095                # Unholy Blight 50536: DeathKnight_UnholyBlight_State mist (no stack tint), STATE
BR_PRICE_OF_DEFIANCE = 47           # Unholy Frenzy 8699: glowing hands STATE + a roar flash on the Baron
BR_PRICE_OF_DEFIANCE_ALT = 11514    # Hysteria 49016, if Ysida does not use it
HM_YSIDA_RISEN_AURA = 11514         # Hysteria 49016: DeathKnight_Hysteria, a persistent blood frenzy STATE on Ysida

# --- Wave 2: the Main Gate (stock ids; the top pick of each row, handoff s3.10 gaps 4, 5, 8, 13, 14 and Added A-F) ----

# The Unforgiven (S1)
UF_ACCUSED_ARROW = 10201            # Target Indicator (Cosmetic) 46901: a lasting red arrow over the head, STATE
UF_ACCUSED_FLASH = 11826            # Wrongfully Accused 51703: a 2.6 s ring of flame rays, IMPACT (the apply flash)
UF_ACCUSED_MARK_ALT = 7262          # Mark of Shame 6767: CatMark over the head + Hunter's Mark on the chest, STATE
UF_SOUL_FREED = 4501                # Soul Freed 17370: icy star burst + icebarrier_state (3.9 yd mesh; check the size)
UF_HAUNTING_PHANTOMS = 335          # Haunting Phantoms 16336: hands + a rising spirit
UF_FROST_NOVA = 17                  # Frost Nova 14907 (same as MK_SHATTER)
UF_GHOST_VISUAL = 886               # Ghost Visual 9617: four flame-wisp emitters, a faint haze, STATE
UF_BUILDING_FIRE = 6821             # Building Fire 21650: a 0.7 s body-sized flame, IMPACT: only a landing flash
UF_FLAME_PATCH = 8313               # Flame Patch Periodic 35380: a ring of flames + fire reflect state, STATE
# The firelight ring is SV_FLAMEZONE_10_STATE above. The house fire is a temporary gameobject:
GODI_HOUSE_FIRE = 4452              # StratholmeFireSmokeEmberM (particle-only; size by the gameobject scale)
GODI_HOUSE_FIRE_ALT = 4251          # StratholmeFireSmokeEmberS (stock "Small Chapel Fire")
GODI_HOUSE_FIRE_ALT_2 = 398         # UndeadFireLarge (stock "Consecrated Earth": a plain flame)
DISPLAY_SPECTRAL_FOOTMAN = 30978    # Footman 300600: human male ext. 20681, scale 1.4, alpha 184 (about 2.8 yd tall)
DISPLAYS_SPECTRAL_CITIZEN = (10483, 10484, 10485, 10486)   # phantom 10387: human male and female ghosts, alpha 128
SOUND_FOOTMAN_MARCH = 7054          # HornOfAwakening, optional march horn on the rank

# Hearthsinger Forresten (S2)
FO_DROWSY = 87                      # Sleep 12098: hands + Sleep_State_Head (green Zs), STATE; alt 4999 Hibernate
FO_DROWSY_ALT = 4999
FO_SIREN_SONG = 371                 # Siren's Song 25678: green hands, bubbles and a gold ribbon
FO_BLACK_ROT = 717                  # Black Rot 16448: a green puff on the chest + a tint
FO_LISTENING_MUSIC = 11381          # Listening to Music 50493: gold heal stars, 1.9 s (a stand-in: no music notes)
FO_LULLABY_HEARTS = 2576            # Enchanting Lullaby: RED HEARTS, kept out of the boss (the test pins it unused)
DISPLAYS_FORRESTEN_RATS = (1141, 1418, 2176)   # Rat.mdx, black, brown and white skins
EMOTE_STATE_DANCE = 10              # the Jig: no SpellVisual (Piccolo SV 4682 is a sound only, never wired)
# The hearth glow is SV_FLAMEZONE_8_STATE above.

# Timmy the Cruel (S3)
TM_FREEZE = 2335                    # Freeze 5276: ice hands + icebarrier_state, STATE
TM_THUNDER_CLAP = 145               # Thunder Clap 6343: a 6.9 yd ground crack + a slow
TM_TRIP = 413                       # Trip 101: shake, thud sound, stun stars
TM_JUMP_ROPE = 9275                 # Wrangling Rope 40856: chain 190 RopeBeam, 0.17 wide, channel only (the top pick)
TM_JUMP_ROPE_ALT = 9759             # Rope Beam 43368: chain 267, 0.08 wide (thin)
TM_JUMP_ROPE_ALT_2 = 11270          # Freya's Vines 51354: chain 526, 0.38 wide + an Entangling Roots state at the end
TM_SWEEP_BURST = 9612               # Smash 42669: warrior_shockwave_area dust ring at the caster's feet
TM_SWEEP_BURST_ALT = 10703          # Shockwave 46968: the same model as a world effect
DISPLAY_TIMMY_PLAYMATE = 571        # Ghoul.mdx, GhoulSkinWhite, display scale 1.5
EMOTE_ONESHOT_EMERGE = 449          # Emotes row 449 (anim 224, falls back to Birth on the ghoul)

# Malor the Zealous (S4)
ML_BLAZE_BEAM = 11500               # WotLK Prologue Light Beam 52407: chain 568 HealBeam, 0.35 wide, gold (NOT 11274)
ML_BLAZE_BEAM_ALT = 8407            # Blade's Edge Multi Gold Beam 35960: chain 2, 0.25 wide
ML_BLAZE_BEAM_ALT_2 = 10165         # Spirit Shackle 45581: Beam_ChainGold, 0.17 wide
ML_ZEAL = 211                       # Zeal 8191 (shared with Inner Fire): hands + a crown rune
ML_HOLY_FIRE = 3400                 # Holy Fire 14914: gold hands + burst + an orange plume (one-shot)
ML_TAINTED_MIND = 339               # Tainted Mind 16567: shadow hands + a rune ring + a chest state
ML_JUDGMENT = 5651                  # Judgement of Light 20271 (the HIT, not 20267's heal sparkle SV 5560)
ML_LAY_ON_HANDS = 132               # Lay on Hands 10310
ML_SMASH_BURST = 9612               # the visible piece of Ground Smash (SV 2643 is a shake): Smash 42669; alt 145

# Cannon Master Willey (S5)
WI_AIM_ARROW = 5646                 # Tag: Arrow 20374: a red arrow STATE over the head (lasts the aim)
WI_MUZZLE_BLAST = 612               # Southsea Cannon Fire 6252: Bomb_ExplosionA at the breath attach + a fire head
WI_MUZZLE_BLAST_ALT = 10032         # Cannon Assault 44939: a muzzle blast + Canon_Impact_Dust at the target
WI_MUZZLE_BLAST_ALT_2 = 30          # Cannon Fire 17278: Bomb_ExplosionA, instant area
WI_BALL_IN_FLIGHT = 11537           # Cannonball 52539: Boulder_Missile x1.5 + a muzzle blast + a fire burst
WI_MERCY_GLOW = 14914               # Holy Zone Visual 70571: HolyZone gold disc, 3.3 yd at scale 1, STATE (stock row)
WI_ZEAL_GLOW = 15672                # Combustion Periodic 74629: FlameZone orange disc, 3.7 yd at scale 1, STATE
WI_SHOOT_GUN = 10208                # the rifle volley's stock Shoot Gun look (S5 shared-file request)
GODI_CANNON = 245                   # G_Cannon01 (Mercy and Zeal), fire anim 153; NOT the invisible 1287
GODI_CANNONBALL = 153               # CatapultBall01, a 2.5 yd ball at scale 1: gameobject 301202, size about 0.4-0.5
GODI_CANNONBALL_PILE = 4177         # DeadMineCannonBallStack, a 1.8 yd pile (the second choice)
GODI_INVISIBLE_TRAP_DO_NOT_USE = 1287    # SpellObject_InvisibleTrap: the stock cannonball 176211's display

# Archivist Galford (S6)
GF_HOLY_FIRE = 3400                 # Holy Fire 14914 on the target (as ML_HOLY_FIRE)
GF_PYROBLAST = 2253                 # Pyroblast: fire hands + a molten impact + PyroBlast_Missile
GF_FIRE_NOVA = 963                  # Fire Nova: fire hands + FireNova_Area ring + FireNova_State
GF_FIRE_WALL = 9701                 # Fire Wall 43113: Missile_Wave_Fire 6.0 x 6.1 x 3.8 yd, STATE (4 stalkers per wall)
GF_BURNING_WINDS = 4486             # a fire twister STATE (5 x 4 x 6.9 yd); RISKY on a carrier with no aura, test it
GF_KINDLED = 46                     # Immolate 348: Immolate_State_Base on the target, STATE (Combustion SV 7634 is a
                                    # one-shot); alt UF_FLAME_PATCH
GF_COMBUSTION_FLASH = 7634          # Combustion 11129: fire ribbons on the chest, IMPACT (re-cast every 2 s, or skip)
GF_CONSECRATION = 5600              # Consecration 20116 as a dynamic object (untested whether it scales to the radius)
# The puddles are SV_HOLYZONE_4/5/6/8_STATE above (Holy Ground SV 7667 is a one-shot, never wired).

# Dathrohan / Balnazzar (S7, S8) and the Grand Lie
DA_TRUE_GROUND = 5600               # Consecration 26573 as the true ground (a PersistentArea 23 yd gold quad)
DA_LIE_GROUND = 8506                # Desecration 36473 (a 16 x 17 yd bone crack) on the same spot, with DA_TRUE_GROUND
DA_LIE_GROUND_ALT = 9735            # Death and Decay under SV 5600 (violet runes)
DA_TRUE_JUDGMENT = 5651             # Judgement of Light 20271 (holy hands + the gold flash)
DA_TRUE_JUDGMENT_ALT = 90040        # Light's Hammer impact (shipped, Paladin): a holy area burst
DA_HOLY_WRATH = 126                 # Holy Wrath 2812: gold hands, a missile, a gold burst, stun stars
DA_METEOR = 4859                    # Inferno 31299: infernal_impact_base, a falling rock + a crater (2.5 s): start it
                                    # 2.5 s before the damage lands
DA_IMMOLATION = 8313                # Flame Patch Periodic 35380: a ring of flames on the Infernal, STATE; alt 2519
DA_IMMOLATION_ALT = 2519            # Immolation 20153: a one-shot chest puff per tick (31304 itself has SV 0)
DA_SLEEP = 7320                     # Sleep 31298: green Zs + banish ribbons + a fog burst; alt 87
DA_SLEEP_ALT = 87
DA_HOLY_WATER = 1243                # Holy Water 17291: a gold boomerang + green Zs state (odd as a blast; RISKY)
DISPLAY_INFERNAL = 7029             # Infernal.mdx, InfernalSkin, display scale 2.0
BZ_SWARM_CLOUD = 7620               # Locust Swarm 28786: GiantInsectSwarm_State_Chest on a stalker (insects, not bats)
BZ_VAMPIRIC_HEAL = 9310             # Blood Siphon 41068: red-drop chain 195 from the victim to Balnazzar (1 s cast)
BZ_VAMPIRIC_HEAL_ALT = 3582         # Vampiric Embrace 15286: hands + a SoothingKiss head impact, no beam
BZ_VAMPIRIC_HEAL_ALT_2 = 7301       # Blood Funnel 24617: red-drop channel chain 13 + a blood bolt on the chest
# The Carrion fan is SV_CARRION_FAN and the lie judgment SV_LIE_JUDGMENT above. The half-room glow (a 180 degree cone,
# Color(Yellow)) and the donut are telegraph kit pieces (BM Cone / Donut), no id here.

# --- Shipped elsewhere, in patch-M already (Deadmines, SV 90340-90344) ------------------------------------------------

SV_ACID_POOL = 90342                # Fish Stew goo puddle, area aura, 4 yd radius (8 yd across)
SV_ACID_POOL_STATE = 90343          # the same as a stalker aura

# Every stock SpellVisual id above (the SpellVisual existence check).
STOCK_SPELL_VISUALS = tuple(sorted({
    BT_INFECTION, BT_CONTAGION, BT_NOXIOUS_FOG, BT_GRAIN_SACK, BT_GRAIN_SACK_ALT, BT_GRAIN_SACK_ALT_2, BT_FEVER,
    BT_FEVER_ALT, BT_FURIOUS_ANGER_FLASH,
    BA_KEEN_SKULL_FLASH, BA_DEATH_KNELL, BA_WAIL, BA_WAIL_ALT, BA_TERRIFIED, BA_VISAGE, BA_BANSHEE_SHRIEK,
    NE_VENOM_SPIT, NE_STUCK, NE_STUCK_ALT, NE_WEB_WRAP, NE_WEB_PATCH_VENOM_SPRAY, NE_SKITTER_LEAP, NE_POISON_CLOUD,
    NE_PLAGUE_FOG, NE_RAISE_SCARAB,
    MK_ICY_DEATH_CAST, MK_ICY_DEATH_STATE, MK_SHATTER, MK_SIPHON_BEAM, MK_EYE_OF_BLIZZARD, MK_ICE_TOMB_CAST,
    MK_ICE_TOMB_SHELL, MK_FROSTBITE_SEED,
    RG_CANNIBALIZE, RG_GORE, RG_EXPOSE_WEAKNESS, RG_TRAMPLE,
    BR_DEATH_AND_DECAY, BR_EXECUTION_BEAM, BR_EXECUTION_BEAM_ALT, BR_CHARGE, BR_CONDEMNED, BR_PRICE_OF_DEFIANCE,
    BR_PRICE_OF_DEFIANCE_ALT, HM_YSIDA_RISEN_AURA,
    # wave 2
    UF_ACCUSED_ARROW, UF_ACCUSED_FLASH, UF_ACCUSED_MARK_ALT, UF_SOUL_FREED, UF_HAUNTING_PHANTOMS, UF_FROST_NOVA,
    UF_GHOST_VISUAL, UF_BUILDING_FIRE, UF_FLAME_PATCH,
    FO_DROWSY, FO_DROWSY_ALT, FO_SIREN_SONG, FO_BLACK_ROT, FO_LISTENING_MUSIC,
    TM_FREEZE, TM_THUNDER_CLAP, TM_TRIP, TM_JUMP_ROPE, TM_JUMP_ROPE_ALT, TM_JUMP_ROPE_ALT_2, TM_SWEEP_BURST,
    TM_SWEEP_BURST_ALT,
    ML_BLAZE_BEAM, ML_BLAZE_BEAM_ALT, ML_BLAZE_BEAM_ALT_2, ML_ZEAL, ML_HOLY_FIRE, ML_TAINTED_MIND, ML_JUDGMENT,
    ML_LAY_ON_HANDS, ML_SMASH_BURST,
    WI_AIM_ARROW, WI_MUZZLE_BLAST, WI_MUZZLE_BLAST_ALT, WI_MUZZLE_BLAST_ALT_2, WI_BALL_IN_FLIGHT, WI_MERCY_GLOW,
    WI_ZEAL_GLOW,
    GF_HOLY_FIRE, GF_PYROBLAST, GF_FIRE_NOVA, GF_FIRE_WALL, GF_BURNING_WINDS, GF_KINDLED, GF_COMBUSTION_FLASH,
    GF_CONSECRATION,
    DA_TRUE_GROUND, DA_LIE_GROUND, DA_LIE_GROUND_ALT, DA_TRUE_JUDGMENT, DA_HOLY_WRATH, DA_METEOR, DA_IMMOLATION,
    DA_IMMOLATION_ALT, DA_SLEEP, DA_SLEEP_ALT, DA_HOLY_WATER,
    BZ_SWARM_CLOUD, BZ_VAMPIRIC_HEAL, BZ_VAMPIRIC_HEAL_ALT, BZ_VAMPIRIC_HEAL_ALT_2,
}))

# Minted by this work (checked against the patch script's rows, not the stock DBCs)
MINTED_SPELL_VISUALS = (
    SV_WEB_PATCH_5_AREA, SV_WEB_PATCH_5_STATE, SV_WEB_PATCH_7_AREA, SV_WEB_PATCH_7_STATE, SV_GUT_PUDDLE_AREA,
    SV_GUT_PUDDLE_STATE, SV_KEENED_SKULL_STATE,
    SV_FLAMEZONE_10_STATE, SV_FLAMEZONE_8_STATE, SV_HOLYZONE_4_STATE, SV_HOLYZONE_5_STATE, SV_HOLYZONE_6_STATE,
    SV_HOLYZONE_8_STATE, SV_CARRION_FAN, SV_LIE_JUDGMENT,
)
# Stock-client-absent but already shipped in patch-M (Deadmines)
# (DA_TRUE_JUDGMENT_ALT 90040 is the Paladin work's Light's Hammer impact, shipped in patch-M.)
MINTED_ELSEWHERE_SPELL_VISUALS = (SV_ACID_POOL, SV_ACID_POOL_STATE, DA_TRUE_JUDGMENT_ALT)

STOCK_CREATURE_DISPLAYS = tuple(sorted({
    DISPLAY_WEB_COCOON, DISPLAY_INVISIBLE_STALKER, DISPLAY_ICE_TOMB, DISPLAY_CRAWLER, DISPLAY_CRAWLER_ALT,
    DISPLAY_BARON_DEATHCHARGER, DISPLAY_YSIDA_RISEN, DISPLAY_YSIDA_RISEN_ALT,
    DISPLAY_SPECTRAL_FOOTMAN, *DISPLAYS_SPECTRAL_CITIZEN, *DISPLAYS_FORRESTEN_RATS, DISPLAY_TIMMY_PLAYMATE,
    DISPLAY_INFERNAL,
}))
STOCK_GAMEOBJECT_DISPLAYS = tuple(sorted({
    GODI_BONE_PILE, GODI_BONE_PILE_ALT, GODI_BONE_PILE_SKELETON,
    GODI_HOUSE_FIRE, GODI_HOUSE_FIRE_ALT, GODI_HOUSE_FIRE_ALT_2, GODI_CANNON, GODI_CANNONBALL, GODI_CANNONBALL_PILE,
}))
STOCK_SOUND_ENTRIES = tuple(sorted({SOUND_KEENING, SOUND_KEENING_ALT, SOUND_FOOTMAN_MARCH}))
