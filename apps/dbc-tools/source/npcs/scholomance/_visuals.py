"""
Scholomance build, WP-V: the visual ids the boss files use, one place (not loaded on its own: the leading underscore
keeps the package loader from treating it as a declaration file; boss files import it with
`from ._visuals import ...`, like `_common.py` and shadowfang_keep/_visuals.py). Owned by WP-V; a boss WP asks for a
change in its report.

Source: .agents/plans/scholomance-build/scholomance-build.VISUALS-REPORT.md (every look is unconfirmed until seen in
game), the top pick of each row (handoff s3.10, s7 #19, #20), with the look corrections of s3.10 applied: the constants
below are the corrected ids, never the build spec's originals where the spec's pick draws nothing or something else.

Everything here is STOCK: the ids already exist in the 3.3.5 client (SpellVisual.dbc, CreatureDisplayInfo.dbc,
GameObjectDisplayInfo.dbc, SpellIcon.dbc) or, for SV_ACID_POOL, in patch-M since the Deadmines work (verified deployed
2026-11-07: live spellvisual_dbc row 90342 and the deployed patch-M both carry it). Nothing ships for the rest and no
id is minted. lib/test_scholomance_vfx.py pins the ids and checks they exist in the working-copy DBCs.

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A StateKit look (marked STATE) plays on
every unit that carries the aura, so only put it on an aura. A ChannelKit look shows only on a channeled spell. An
"AURA" constant is a stock spell id: a script casts it on the unit, or the custom aura copies its SpellVisual.
Names are `<boss code>_<what>`; boss codes: JB Jandice Barov, RG Rattlegore, MV Marduk and Vectus (and their
students), RF Ras Frostwhisper, ML Malicia, KR Krastinov, PK Polkelt, RV Ravenian (and Corvane), AX Alexei, IL Illucia,
GD Gandling.
"""

# --- Stock displays (CreatureDisplayInfo) -----------------------------------------------------------------------------

# Rattlegore (S2)
DISPLAY_BONE_PILE_PART = 27976      # loose part and pile: Bone Spider (brown); 6.0 x 4.4 yd at scale 1, so template
BONE_PILE_PART_SIZE = 0.4           # scale 0.4-0.5 (about 2.5 yd); runner-up display 16156 BoneGolem at 0.4-0.5
DISPLAY_BONE_PILE_PART_ALT = 16156
DISPLAY_UNFINISHED_CONSTRUCT = 12074  # copy of 10488's display (BoneGolem, 1.25); template scale 0.7, plus the aura
UNFINISHED_CONSTRUCT_SIZE = 0.7
DISPLAY_UNFINISHED_CONSTRUCT_ALT = 21305  # Bony Construct (1.75), the other skin scale

# Ras (S4, S12)
DISPLAY_RAS_HUMAN = 3975            # stock Boon of Life human form; HumanMale, NO extended display row: `.morph 3975`
DISPLAY_RAS_HUMAN_ALT = 11155       # robed human (male), Scholomance Necromancer (creature 10477); unconfirmed look
DISPLAY_ICE_TOMB = 30890            # tomb unit: Sindragosa's Ice Tomb (creature 36980), 9.6 x 9.5 x 5.8 yd at scale 1
ICE_TOMB_SIZE = 0.35                # template scale 0.3-0.4 to wrap one player

# Malicia (S5)
DISPLAY_LOOSE_SOUL = 1825           # §7 #20: the wisp (creature 11136 "Freed Soul"), skins Wisp / WispGlow
DISPLAY_LOOSE_SOUL_SMALL = 6197     # smaller wisp (scale 0.5, "Gnome Soul") if 1825 reads too big
DISPLAY_DARK_SHADE = 4629           # her shades (creature 11284, Shade.mdx)
# display 30233 (Bronjahm's "Corrupted Soul Fragment") is InvisibleStalker.mdx: it shows only with Purple Banish Visual
# 68862 (SV 7784) on the unit. Never wire it bare; the test pins that it stays out of the displays below.
DISPLAY_LOOSE_SOUL_INVISIBLE_DO_NOT_USE = 30233
AURA_LOOSE_SOUL_BANISH = 68862      # only if the 30233 route is ever chosen instead of the wisp

# Krastinov (S6)
DISPLAY_WORK_BENCH = 30297          # undead_alchemy_table (scale 0.7): the room's own bench model (GODI 4391)
DISPLAY_FAILED_PATIENT = 519        # Diseased Ghoul (stock, the doc's pick)

# Ravenian and Corvane (S8)
DISPLAY_CORVANE = 23277             # Necromancer (blue, scale 1.25), creature 27615
DISPLAY_CORVANE_ALT = 30993         # WightScientist (scale 3.0 baked): template scale 0.4-0.45; may read as a reuse
DISPLAY_CORVANE_FALLBACK = 11155    # Scholomance Necromancer (male), already in the instance

# Gandling (S11, S13)
DISPLAY_EXPELLED_STUDENT = 9784     # Skeletal Berserker (creature 10391; also 9786, 9787, 9788)
DISPLAY_ECHO_RAVENIAN = 10433       # the Wight (skin WightSkinWhite) + Ghost Visual aura 9617
# Portals on the room edge and the gauntlet exits: Creature_SpellPortal_LargeShadow, 12 yd tall at model scale 1
# (scale 3.0 baked), so template scale 0.15-0.25. Use as a creature display; `.morph 27735`
DISPLAY_PORTAL = 27735
PORTAL_SIZE = 0.2
DISPLAY_PORTAL_ALT = 22742          # Creature_SpellPortalLarge_Purple (creature 24925)
DISPLAY_PORTAL_ALT_2 = 23718        # MagePortal_Blank (scale 6)
DISPLAY_INVISIBLE_STALKER = 11686   # (S4) an invisible stalker: Ras's Blizzard anchor 300534 (the SFK ward stalker's)

# --- Stock GameObjectDisplayInfo (a goober / generic template's displayId) ---------

GODI_TORN_PAGE = 7752               # Ras page: UldamanScrollDebris03, 1.29 x 0.85 yd, no glow (hidden: the hunt is the
GODI_TORN_PAGE_ALT = 4851           # puzzle; the scroll pile 177667 and the glowing scroll 210 are the fallbacks)
GODI_EMPTY_BOOK = 4431              # Ras book: BookMedium07 (stock GO 176630), 0.6 x 0.45 yd: set template size 2-3
EMPTY_BOOK_SIZE = 2.5
GODI_EMPTY_BOOK_ALT = 2530          # open black book, pages gone
GODI_BONE_PILE_LANDING = 6998       # Rattlegore landing pile: OM_Bones_03, GO 193199, 2.4 x 2.8 yd
GODI_FORTUNE_PILE = 2614            # Alexei fortune: GoldPilesmall01 (GO 186634), 1.85 yd; unit stand-in is DBC-only
GODI_FORTUNE_PILE_ALT = 7343        # GoldPileLarge01, 5.7 yd; scale 0.4
GODI_DEED_SCROLL = 183              # the deed to Caer Darrow (GO 176485), beside the fortune
GODI_HONORS_PAPER = 210             # Gandling honors paper: G_Scroll01 (glow; goober GO 1761), 1.05 yd
GODI_HONORS_PAPER_ALT = 163         # plain sheet ScrollA02 (GO 179004)

# --- Passing Grade buff icons (SpellIcon ids; one themed icon per instructor) ----------------------------------------

ICON_PASSING_GRADE_MALICIA = 92         # Spell_Shadow_SoulGem (alt 2027)
ICON_PASSING_GRADE_KRASTINOV = 2741     # INV_Misc_SurgeonGlove_01 (alt 2949)
ICON_PASSING_GRADE_POLKELT = 339        # Trade_Alchemy (alt 636)
ICON_PASSING_GRADE_RAVENIAN = 221       # Spell_Shadow_AnimateDead (alt 61)
ICON_PASSING_GRADE_ALEXEI = 2319        # INV_Rod_EnchantedFelsteel (alt 3964)
ICON_PASSING_GRADE_ILLUCIA = 48         # Spell_Shadow_MindSteal (alt 2121)
PASSING_GRADE_ICONS = (ICON_PASSING_GRADE_MALICIA, ICON_PASSING_GRADE_KRASTINOV, ICON_PASSING_GRADE_POLKELT,
                       ICON_PASSING_GRADE_RAVENIAN, ICON_PASSING_GRADE_ALEXEI, ICON_PASSING_GRADE_ILLUCIA)
# Malicia's Soul Fragment stack buff 71905 has no SpellVisual (icon only, SpellIcon 1693); the optional body tint is
# Glowy (Purple) 22581, SV 6593.
ML_SOUL_STACK_TINT = 6593

# --- Stock spells whose look a script casts or a custom aura copies --------------------------------------------------

AURA_PERMANENT_FEIGN_DEATH = 29266  # RG: the Unfinished Construct's collapsed pose (display 12074)
AURA_GHOST_VISUAL = 9617            # GD: every Graduate Examiner and the Ravenian's echo (alpha 0.5, pale tint), SV 886

# --- Per boss: SpellVisual per spell ---------------------------------------------------------------------------------
# Stock spell id and name in the comment; "STATE" = a StateKit look (aura only); "(doc)" = the doc's pick.

# Jandice Barov (S1)
JB_VANISH_INTO_COPIES = 11181       # (doc) Blood Mirror (Transition Visual) 50910: head bloodbolt_chest
JB_REFLECTION_POOF = 2046           # (doc) Mirror Image 36847: the generic summon poof; copies use the display
JB_SIGIL_BURST = 9312               # (doc) Blood Nova 72379 / Blood Splash 41067: BloodyExplosion + blood bolt missile
JB_FAKE_SIGIL_POP = 255             # (doc) Vanish Visual 24222: vanish_cast_base (its state kit 312 fades the unit)
JB_COPY_SHATTERS = 11222            # (doc) Crystal Shatter Visual 51150
JB_SHUFFLE_THREAD = 14876           # (doc) Blood Mirror 70445: STATE bloodbolt_chest (a beam is unconfirmed)
JB_BLOOD_PRICE_TICK = 11117         # (doc) Blood Boil 48721: DeathKnight_BloodBoil impact
JB_BLOODLINES_BEAM = 15275          # (doc) Blood Beam Visual RHand 72304: STATE bloodbolt_chest (a beam is unconfirmed)
JB_JOURNAL_ITEM = 12866             # Item.dbc display 23323 (black glowing book, 1H slot)

# Rattlegore (S2)
RG_PART_FLUNG = 10772               # (doc) Throw Bone Boulder 48430: nightbane_bone_missile. Alt SV 11069 Bone Toss
RG_PART_FLUNG_ALT = 11069
RG_LANDING = 15031                  # (doc) Shattered Bones 70961: DustCloud_Land + bone spurs
RG_GRINDING_A_PILE = 11411          # (doc) Bone Crack 52080
RG_PILE_BOLTS_BACK_ON = 163         # (doc) Reconstruct 10260: SkullBalls chest. Alt SV 11741 Animate Bones 53334
RG_PILE_BOLTS_BACK_ON_ALT = 11741
# Eruption rings: Bone Spike Graveyard 69057 / SV 15339 draws NOTHING (the spikes are creatures); use Impale 53454
RG_ERUPTION_RING = 11766            # Spike_Impact_Base
# Salvage channel: Grab Skeleton 48232 / SV 10719 draws NOTHING (animation + sound), Salvage Corpse 56227 / SV 93 is the
# mining pick. Use the Reconstruct funnel (a channel look, ChannelKit only on a channeled spell) or Animate Bones.
RG_SALVAGE_CHANNEL = RG_PILE_BOLTS_BACK_ON
RG_FRENZY = 870                     # (doc) Risen Construct Frenzy 8269: BeastRageCaster

# Marduk and Vectus (S3)
MV_FLAMESTRIKE_DRILL = 10383        # (doc) Flamestrike 18399: Immolate_State_Base + persistent Flamestrike_Impact_Base
MV_SHADOW_BOLT_VOLLEY = 2318        # (doc) Shadow Bolt Volley 17228 (Group Exercise, Pop Quiz): shadowbolt missile
MV_EBON_SWEEP = 7684                # (doc) Shadow Cleave 29832: cleave_cast_base_purple. Alt SV 11713 Runeblade Death
MV_EBON_SWEEP_ALT = 11713
MV_WHIRLWIND = 10704                # (doc) Bladestorm 46924: STATE warrior_bladestorm
MV_KILLING_FRENZY = 870             # Vectus frenzy (Frenzy 8269)
MV_DRILL_IMPACT = 796               # (S3) impact-only kit Fire_ImpactDD_Chest: the Drill's hit on each player
MV_GROUP_EXERCISE_MARK = 3239       # (S3) Hunter's Mark 1130, the red arrow (as Nandos's Marked Prey): the marked one
MV_FIREBALL = 67                    # (S3) Fireball 9053 (missile, MoltenBlast impact): Vectus's Fireball
MV_WHIRLWIND_IMPACT = 3362          # (S3) impact-only kit DecisiveStrike_Impact_Chest: the spin's tick on each player

# Ras Frostwhisper (S4, S12)
# Chill stacks: Mystic Buffet 70127 / SV 8796 is a one-shot arcane burst and Frost Aura 28531 / SV 7606 draws NOTHING.
RF_CHILL = 675                      # Chilled 6136: Ice_Precast_Uber_Head mist (STATE)
RF_CHILL_12_STACKS = 6778           # Aura of Frost 23186: icebarrier_state, swap in from 12 stacks (STATE)
RF_CHILL_ALT = 6589                 # Glowy (Blue) 22576
# Warmth: Fire Shield 134 / SV 289 and Heat 52387 / SV 12640 are flashes only, nothing persists
RF_WARMTH = 6591                    # Glowy (Orange) 22579: body glow (STATE). Alt SV 46 Warming Flames 23040
RF_WARMTH_ALT = 46
RF_FROST_MARK = 15254               # (doc) Frost Beacon 70126: catmark_blue over the head (STATE)
RF_FROST_NOVA = 4823                # (doc) Chill Nova 18099, his own
# Blizzard: NPC Blizzard 8364 / SV 10386 has no persistent model; use Blizzard 64642 (persistent SummonGround_Blizzard,
# scale 0.8). A unit anchor needs a StateKit (DBC-only SV from SVEN 5400, not minted here).
RF_BLIZZARD = 13698
RF_BLIZZARD_ALT = 12213             # frost ground 55868, a 25 yd carpet (scale it down)
# Entombed (player): Ice Tomb 70157 / SV 3960 draws NOTHING and Ice Tomb 69675 / SV 14726 is a nova, not a block
RF_ENTOMBED = 4340                  # Ice Tomb 16869: icebarrier_state (STATE). Alt SV 7406 Frozen Prison 47543
RF_ENTOMBED_ALT = 7406
# Tomb thaw: Shatter 33671 / SV 8097 is stone chips; Ice Tomb 69675's nova + Xplosion_Frost_Impact is the burst
RF_TOMB_THAW = 14726
RF_TOMB_THAW_ALT = 4823
RF_SIPHON_WARMTH = 7607             # (doc) Life Drain 28542 (Sapphiron): chest shadow impact + snare state
RF_MORTAL_DECAY = 11624             # Blood Plague 55264: DeathKnight_PlagueStrikeState (STATE). Alt SV 11832
RF_MORTAL_DECAY_ALT = 11832

# Malicia (S5)
ML_SOUL_DRAIN = 12656               # (doc) Drain Soul Visual 60857 / Corrupt Soul 68839: SoulFunnel_Impact_Chest
ML_SOULSTORM_HANDS = 14509          # (doc) Soulstorm 68872: banish_chest_purple on both hands only (the channel look)
# Falling souls: Unleashed Souls 68939 / SV 14527 is an icy ground state with no souls. The Soulstorm missiles fit:
ML_FALLING_SOULS = 14512            # Soulstorm 68896 missile: banish_chest_purple orb
ML_FALLING_SOULS_ALT = 14513        # Soulstorm 68897
ML_SPIRIT_BURST = 7180              # (doc) Spirit Burst 24050
ML_SHADOW_MEND = 7380               # (doc) Shadow Mend 25531
ML_SHADOW_NOVA = 7951               # (doc) Shadow Nova 32711
# Bound Soul on her: Stolen Soul Visual 32395 / SV 7264 is empty. Purple Banish Visual 68862 (STATE)
ML_BOUND_SOUL = 7784

# Krastinov (S6)
KR_DRAG_ONTO_BENCH = 11055          # (doc) Scourge Hook 50335 / Abomination Hook 59395: no model, chain by
                                    # CharParam 502; blood burst on impact. Short cast so the chain shows
KR_INCISION = 10107                 # (doc) Whale Dissection 45264: BloodyExplosion impact
KR_WRENCH_FREE = 12608              # Use Wrench 58925: SpellObject_Wrench in hand (STATE; an instant needs the Kick
KR_WRENCH_FREE_IMPACT = 90          # impact too: Kick 1766, or Pummel 6552 / SV 1023)
KR_STITCHED_WOUND = 15205           # Necrotic Strike 70659: DeathKnight_PlagueStrikeState (STATE). Alt SV 11832, 15247
KR_STITCHED_WOUND_ALT = 11832
KR_GRAFT_HANDS = 47                 # Unholy Frenzy 8699: BloodLust_State_Hand on both hands (STATE). Alt SV 870 (flash)
KR_GRAFT_EYES = 9188                # Dalaran eye 61332: dalaran_eye_01 over the head (STATE). Alt SV 6039
KR_GRAFT_HEART = 10883              # Heart pulse 49163: floatingminepulse in the chest (STATE). Alt SV 7489 (Amorous)
KR_KILLING_FRENZY = 870             # his own Frenzy 8269 look (the doc: hands, his own)

# Polkelt (S7)
PK_RAISE = 11305                    # (doc) Raise Dead 51516. Alt SV 11774 Emerge 53500
PK_EMERGE = 11774
PK_FUSE_SWELL = 11259               # (doc) Explode 47496
PK_BURST = 749                      # (doc) Disease Burst 17689, the stock room's own
PK_ROOTED = 38                      # Entangling Roots 339: EntanglingRoots_State at the feet (STATE). Alt SV 838
PK_ROOTED_ALT = 838
PK_HARDENED = 6662                  # Hardened Bark 62663: barkskin_state_base (STATE). Alt SV 7425, 13148
PK_HARDENED_ALT = 7425
# Acid pool: Slime Pool 66883 / SV 14287 draws no pool and Plague Cloud 49350 / SV 9709 an orange fog. Reuse the
# Deadmines green puddle: PersistentAreaKit 90342 (goo_flow_state, scale 0.167), minted in the Deadmines work; verified
# deployed 2026-11-07 (live spellvisual_dbc row + patch-M SpellVisual / SpellVisualKit / SpellVisualEffectName rows).
SV_ACID_POOL = 90342
PK_ACID_POOL = SV_ACID_POOL
PK_CORRODED = 856                   # (S7) Corrosive Acid 8245's own: the Corroded debuff
PK_NOXIOUS_CATALYST = 800           # (S7) Noxious Catalyst 18151's own

# Ravenian and Corvane (S8)
RV_LEASH_BEAM = 9843                # (doc) Shadow Channeling 43897: RitualSummoning precast + shadow hands
RV_LEASH_BEAM_ALT = 7597            # Chains of Kel'Thuzad 28410: missile streak + enslave state
RV_MEND_CONSTRUCT = 27              # (doc) Dark Mending 16588: ShadowProtection_Chest
RV_TELEPORT_DOWN = 9343             # (doc) Teleport Visual 41236
RV_BEREAVED = 47                    # (doc) Unholy Frenzy 8699 (BloodLust_State_Hand)
RV_ORDER_TRAMPLE = 672              # (S8) Trample 15550
RV_ORDER_SWEEP = 219                # (S8) Sundering Cleave 25174 (and Cleave 20691)
RV_ORDER_SMASH = 2069               # (S8) Knock Away 10101
RV_SHADOW_BOLT = 64                 # (S8) Shadow Bolt 686 (the bolt and its missile): Corvane

# Alexei (S9)
# Fortune pickup: Coin Toss 60450 / SV 12794 is a yellow crystal missile, not a coin (the pile GODI is the visible
# object). Ill-Gotten Gains: the loot sparkle; keep apart from the Deadmines picks (SV 12528 and 47/11903).
AX_RULE_ANNOUNCEMENT = 246          # (doc) Commanding Shout 469
# Dean's Rod: Lash 6607 / SV 808 draws NOTHING; use Chastise 36863
AX_DEANS_ROD = 792
AX_ILL_GOTTEN_GAINS = 12473         # Ill-Gotten Gains 57718 loot sparkles (lootfx, scale 1.5)
AX_ILL_GOTTEN_GAINS_ALT = 11903     # AuraYellow 54273 (yellow glow column); alt 2 SV 6592 Glowy (Yellow) 22580
AX_VEIL_OF_SHADOW = 561             # (S9) Veil of Shadow 17820's own

# Illucia (S10)
IL_THE_READ = 4839                  # (doc) Mind Vision 2096: eyesofbeast_impact_head
IL_FORESIGHT_IMPACT = 13255         # (doc) Shadow Crash 62659. Alt SV 3057 Mind Blast 8092 (MindBlast_Head)
IL_FORESIGHT_IMPACT_ALT = 3057
# Memory trail: Shadow Trap 73530 / SV 15489 draws NOTHING; use Mind Sear 48045
IL_MEMORY_TRAIL = 12121             # priest_mindshear
IL_FEAR = 13757                     # (doc) Psychic Horror 64044: Fear_Impact_Chest + Fear_State_Head

# Gandling (S11, S13)
# Portals: Shadow Portal Visual 49666 / SV 10150 is the Shadowform look and Open Shadow Portal 53765 / SV 11806 a hand
# precast: neither draws a portal. The portal is the DISPLAY_PORTAL unit (or Banishment Periodic Aura 40849, SV 9142,
# the same model as a state, on a stalker).
GD_PORTAL_STATE = 9142
# The Portal Volley stream: the triggered spells 7269 / 7270, not Arcane Missiles 5143 (SV 262, channel hands only)
GD_PORTAL_VOLLEY = 269              # Arcane_Missile_Lvl2 + Magic_Impact_Chest
GD_PORTAL_VOLLEY_2 = 270            # Arcane_Missile_Lvl3
GD_PORTAL_VOLLEY_SHADOW = 2318      # shadow option: Shadow Bolt Volley's missile
# Transfer: flash at both ends; the link is the closest stock thing (a true beam is client CharParam only, unconfirmed).
# Displacement 38351 / SV 8251 is a cyclone, not a link.
GD_TRANSFER_FLASH = 9343            # Teleport Visual 41236
GD_TRANSFER_LINK = 7597             # Chains of Kel'Thuzad 28410
GD_HONOR_ROLL = 7553                # Power Infusion 10060: Priest_PowerInfusion body glow (STATE). Alt SV 6592 Glowy
GD_HONOR_ROLL_ALT = 6592
GD_HONOR_ROLL_FLASH = 7334          # Honor Points +398 24923: on-apply chest flash
GD_EXAMINER_TINT = 886              # Ghost Visual 9617 (alpha 0.5, pale tint). Alt SV 10468 Ahune's Ghost Disguise,
GD_EXAMINER_TINT_ALT = 10468        # SV 14609 Raging Spirit Visual
GD_ECHO_GHOST = 886                 # the Ravenian's echo: display DISPLAY_ECHO_RAVENIAN + this aura. Alt SV 8744

# Every stock SpellVisual id above (the SpellVisual existence check). SV_ACID_POOL is minted by the Deadmines work and
# listed in MINTED_ELSEWHERE_SPELL_VISUALS.
STOCK_SPELL_VISUALS = tuple(sorted({
    JB_VANISH_INTO_COPIES, JB_REFLECTION_POOF, JB_SIGIL_BURST, JB_FAKE_SIGIL_POP, JB_COPY_SHATTERS, JB_SHUFFLE_THREAD,
    JB_BLOOD_PRICE_TICK, JB_BLOODLINES_BEAM,
    RG_PART_FLUNG, RG_PART_FLUNG_ALT, RG_LANDING, RG_GRINDING_A_PILE, RG_PILE_BOLTS_BACK_ON, RG_PILE_BOLTS_BACK_ON_ALT,
    RG_ERUPTION_RING, RG_SALVAGE_CHANNEL, RG_FRENZY,
    MV_FLAMESTRIKE_DRILL, MV_SHADOW_BOLT_VOLLEY, MV_EBON_SWEEP, MV_EBON_SWEEP_ALT, MV_WHIRLWIND, MV_KILLING_FRENZY,
    MV_DRILL_IMPACT, MV_GROUP_EXERCISE_MARK, MV_FIREBALL, MV_WHIRLWIND_IMPACT,
    RF_CHILL, RF_CHILL_12_STACKS, RF_CHILL_ALT, RF_WARMTH, RF_WARMTH_ALT, RF_FROST_MARK, RF_FROST_NOVA, RF_BLIZZARD,
    RF_BLIZZARD_ALT, RF_ENTOMBED, RF_ENTOMBED_ALT, RF_TOMB_THAW, RF_TOMB_THAW_ALT, RF_SIPHON_WARMTH, RF_MORTAL_DECAY,
    RF_MORTAL_DECAY_ALT,
    ML_SOUL_STACK_TINT, ML_SOUL_DRAIN, ML_SOULSTORM_HANDS, ML_FALLING_SOULS, ML_FALLING_SOULS_ALT, ML_SPIRIT_BURST,
    ML_SHADOW_MEND, ML_SHADOW_NOVA, ML_BOUND_SOUL,
    KR_DRAG_ONTO_BENCH, KR_INCISION, KR_WRENCH_FREE, KR_WRENCH_FREE_IMPACT, KR_STITCHED_WOUND, KR_STITCHED_WOUND_ALT,
    KR_GRAFT_HANDS, KR_GRAFT_EYES, KR_GRAFT_HEART, KR_KILLING_FRENZY,
    PK_RAISE, PK_EMERGE, PK_FUSE_SWELL, PK_BURST, PK_ROOTED, PK_ROOTED_ALT, PK_HARDENED, PK_HARDENED_ALT,
    PK_CORRODED, PK_NOXIOUS_CATALYST,
    RV_LEASH_BEAM, RV_LEASH_BEAM_ALT, RV_MEND_CONSTRUCT, RV_TELEPORT_DOWN, RV_BEREAVED, RV_ORDER_TRAMPLE, RV_ORDER_SWEEP,
    RV_ORDER_SMASH, RV_SHADOW_BOLT,
    AX_RULE_ANNOUNCEMENT, AX_DEANS_ROD, AX_ILL_GOTTEN_GAINS, AX_ILL_GOTTEN_GAINS_ALT, AX_VEIL_OF_SHADOW,
    IL_THE_READ, IL_FORESIGHT_IMPACT, IL_FORESIGHT_IMPACT_ALT, IL_MEMORY_TRAIL, IL_FEAR,
    GD_PORTAL_STATE, GD_PORTAL_VOLLEY, GD_PORTAL_VOLLEY_2, GD_PORTAL_VOLLEY_SHADOW, GD_TRANSFER_FLASH,
    GD_TRANSFER_LINK, GD_HONOR_ROLL, GD_HONOR_ROLL_ALT, GD_HONOR_ROLL_FLASH, GD_EXAMINER_TINT, GD_EXAMINER_TINT_ALT,
    GD_ECHO_GHOST,
}))
# Stock-client-absent but already shipped in patch-M (Deadmines, SV 90340-90344): checked against the deployed patch-M.
MINTED_ELSEWHERE_SPELL_VISUALS = (SV_ACID_POOL,)

STOCK_CREATURE_DISPLAYS = tuple(sorted({
    DISPLAY_BONE_PILE_PART, DISPLAY_BONE_PILE_PART_ALT, DISPLAY_UNFINISHED_CONSTRUCT, DISPLAY_UNFINISHED_CONSTRUCT_ALT,
    DISPLAY_RAS_HUMAN, DISPLAY_RAS_HUMAN_ALT, DISPLAY_ICE_TOMB, DISPLAY_LOOSE_SOUL, DISPLAY_LOOSE_SOUL_SMALL,
    DISPLAY_DARK_SHADE, DISPLAY_WORK_BENCH, DISPLAY_FAILED_PATIENT, DISPLAY_CORVANE, DISPLAY_CORVANE_ALT,
    DISPLAY_CORVANE_FALLBACK, DISPLAY_EXPELLED_STUDENT, DISPLAY_ECHO_RAVENIAN, DISPLAY_PORTAL, DISPLAY_PORTAL_ALT,
    DISPLAY_PORTAL_ALT_2, DISPLAY_INVISIBLE_STALKER,
}))
STOCK_GAMEOBJECT_DISPLAYS = tuple(sorted({
    GODI_TORN_PAGE, GODI_TORN_PAGE_ALT, GODI_EMPTY_BOOK, GODI_EMPTY_BOOK_ALT, GODI_BONE_PILE_LANDING,
    GODI_FORTUNE_PILE, GODI_FORTUNE_PILE_ALT, GODI_DEED_SCROLL, GODI_HONORS_PAPER, GODI_HONORS_PAPER_ALT,
}))
STOCK_SPELL_ICONS = tuple(sorted(PASSING_GRADE_ICONS))
