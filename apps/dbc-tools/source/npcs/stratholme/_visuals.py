"""
Stratholme build, WP-V (wave 1: the Service Entrance, S9-S15): the visual ids the boss files use, one place (not loaded
on its own: the leading underscore keeps the package loader from treating it as a declaration file; boss files import
it with `from ._visuals import ...`, like `_common.py` and scholomance/_visuals.py). Created by V-1; V-2 appends the
wave 2 constants (FlameZone, HolyZone, the Carrion fan, the lie judgment, the Main Gate picks). A boss WP asks for a
change in its report.

Source: .agents/plans/stratholme-build/stratholme-build.VISUALS-REPORT.md (ids, kits, mesh bounds and textures read;
nothing rendered, so every look is unconfirmed until seen in game), the top pick of each wave 1 row (handoff s3.10, s7
#21), with the look corrections of s3.10 applied: the constants below are the corrected ids, never the build spec's
originals where the spec's pick draws nothing or something else.

Two kinds of constant:

- MINTED (client patch-M, by apps/dbc-tools/patch_stratholme_vfx_models.py, ids.yaml reservation `stratholme`,
  spellvisual 90500-90549): the `SV_*` names in the first section. They must equal the patch script's constants of the
  same name (lib/test_stratholme_vfx.py pins it). All sit on stock models; no model or texture ships.
- STOCK: ids that already exist in the 3.3.5 client (SpellVisual.dbc, CreatureDisplayInfo.dbc,
  GameObjectDisplayInfo.dbc, SoundEntries.dbc) or, for SV_ACID_POOL / SV_ACID_POOL_STATE, in patch-M since the Deadmines
  work (shipped). Nothing ships for them and no id is minted. The test checks they exist in the working-copy DBCs.

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A StateKit look (marked STATE) plays on
every unit that carries the aura, so only put it on an aura (a stalker aura for a ground patch). A PersistentArea look
(marked AREA) is for a spell with a dynamic object (the area aura). A ChannelKit look shows only on a channeled spell.
An impact kit plays once. Names are `<boss code>_<what>`; boss codes: BT Barthilas, BA Baroness Anastari, NE
Nerub'enkan, MK Maleki, RG Ramstein, BR Baron Rivendare, HM the hard mode (Ysida, Risen).
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

# --- Shipped elsewhere, in patch-M already (Deadmines, SV 90340-90344) ------------------------------------------------

SV_ACID_POOL = 90342                # Fish Stew goo puddle, area aura, 4 yd radius (8 yd across)
SV_ACID_POOL_STATE = 90343          # the same as a stalker aura

# Every stock SpellVisual id above (the SpellVisual existence check).
STOCK_SPELL_VISUALS = tuple(sorted({
    BT_INFECTION, BT_CONTAGION, BT_NOXIOUS_FOG, BT_GRAIN_SACK, BT_GRAIN_SACK_ALT, BT_GRAIN_SACK_ALT_2, BT_FEVER,
    BT_FEVER_ALT, BT_FURIOUS_ANGER_FLASH,
    BA_KEEN_SKULL_FLASH, BA_DEATH_KNELL, BA_WAIL, BA_WAIL_ALT, BA_TERRIFIED, BA_VISAGE, BA_BANSHEE_SHRIEK,
    NE_VENOM_SPIT, NE_STUCK, NE_STUCK_ALT, NE_WEB_WRAP, NE_WEB_PATCH_VENOM_SPRAY, NE_SKITTER_LEAP, NE_POISON_CLOUD,
    MK_ICY_DEATH_CAST, MK_ICY_DEATH_STATE, MK_SHATTER, MK_SIPHON_BEAM, MK_EYE_OF_BLIZZARD, MK_ICE_TOMB_CAST,
    MK_ICE_TOMB_SHELL, MK_FROSTBITE_SEED,
    RG_CANNIBALIZE, RG_GORE, RG_EXPOSE_WEAKNESS, RG_TRAMPLE,
    BR_DEATH_AND_DECAY, BR_EXECUTION_BEAM, BR_EXECUTION_BEAM_ALT, BR_CHARGE, BR_CONDEMNED, BR_PRICE_OF_DEFIANCE,
    BR_PRICE_OF_DEFIANCE_ALT, HM_YSIDA_RISEN_AURA,
}))
# Minted by this work (checked against the patch script's rows, not the stock DBCs)
MINTED_SPELL_VISUALS = (
    SV_WEB_PATCH_5_AREA, SV_WEB_PATCH_5_STATE, SV_WEB_PATCH_7_AREA, SV_WEB_PATCH_7_STATE, SV_GUT_PUDDLE_AREA,
    SV_GUT_PUDDLE_STATE, SV_KEENED_SKULL_STATE,
)
# Stock-client-absent but already shipped in patch-M (Deadmines)
MINTED_ELSEWHERE_SPELL_VISUALS = (SV_ACID_POOL, SV_ACID_POOL_STATE)

STOCK_CREATURE_DISPLAYS = tuple(sorted({
    DISPLAY_WEB_COCOON, DISPLAY_INVISIBLE_STALKER, DISPLAY_ICE_TOMB, DISPLAY_CRAWLER, DISPLAY_CRAWLER_ALT,
    DISPLAY_BARON_DEATHCHARGER, DISPLAY_YSIDA_RISEN, DISPLAY_YSIDA_RISEN_ALT,
}))
STOCK_GAMEOBJECT_DISPLAYS = tuple(sorted({GODI_BONE_PILE, GODI_BONE_PILE_ALT, GODI_BONE_PILE_SKELETON}))
STOCK_SOUND_ENTRIES = tuple(sorted({SOUND_KEENING, SOUND_KEENING_ALT}))
