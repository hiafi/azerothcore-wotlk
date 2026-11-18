"""
Blackrock Depths build, WP V-1 (wave 1: sections 1-2, D1-D13) and V-2 (wave 2: sections 3-4, D14-D24), both written in
one pass because both waves are built before the one deploy: the visual ids the boss files use, one place (not loaded
on its own: the leading underscore keeps the package loader from treating it as a declaration file; boss files import
it with `from ._visuals import ...`, like `_common.py` and blackrock_spire/_visuals.py). A boss WP asks for a change in
its report; nobody else edits this file.

Source: .agents/plans/blackrock-depths-build/blackrock-depths-build.VISUALS-REPORT.md (ids, kits, mesh bounds and
textures read; nothing rendered, so every look is unconfirmed until seen in game) and the top pick of each row (handoff
s3.10, user ruling 2026-11-17: every top pick approved, incl. the four Ascension models), with the look corrections of
s3.10 applied: the constants below are the corrected ids, never the build spec's originals where the spec's pick draws
nothing or something else (lib/test_blackrock_depths_vfx.py pins the wrong ones out).

Four kinds of constant:

- MINTED (client patch-M, by apps/dbc-tools/patch_blackrock_depths_vfx_models.py, ids.yaml reservation
  `blackrock_depths`, spellvisual 90650-90699): the `SV_*` names in the first section, plus the two keg displays
  (CMD + CDI 90770 / 90771). They must equal the patch script's constants of the same name (the test pins it). Four
  Ascension models ship into patch-M (`--extract` pulls them). 90660-90669 stay spare for the tuning round.
- SHIPPED (already in patch-M or the working copy): the Blackrock Spire rows (SV 90600-90616), the Stratholme rows
  (90500-90512), the Deadmines goo and wood splinters (90342-90344). Nothing ships for them; the dry run checks they
  exist in the working-copy DBCs. Their names here start with `SHIPPED_`.
- STOCK: ids that already exist in the 3.3.5 client. Nothing ships and no id is minted.
- TELEGRAPH MARKERS (kit displays 91000-93999) are not named here: the boss files use the mod-boss-mechanics registry
  kinds and `Color(...)`, never a display id.

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A STATE look plays on every unit that
carries the aura (so only put it on an aura, a stalker aura for a ground patch). An AREA look is for a spell with a
dynamic object (an area aura). An impact kit plays once, so a lasting effect re-casts it every 2-3 s or uses the
lasting twin named here. Names are `<boss code>_<what>`; boss codes (the spec's mechanic id prefixes, plus a code per
named unit): GE Gerstahn, RO Roccor, GR Grebmar, RL Ring of Law frame and waves (RW the wave mobs, CH champions
generally, GO Gorosh, GZ Grizzle, EV Eviscerator, OK Ok'thor, AN Anub'shiah, HE Hedrum), EN the Encore team (TH
Theldren, KO Korv, LE Lefty, VL Volida, MA Malgen), LG Loregrain, ST Stilgiss, VE Verek, VA the Vault (Doomgrip and the
sentinels), FD Fineous, IN Incendius, BG Bael'Gar, AF Angerforge, AR Argelmach, HU Hurley, PH Phalanx, FL Flamelash, TS
the Seven, MG Magmus, EM the Emperor, MO Moira. (The boss prefix ST is never SV: `SV_` is reserved for minted ids.)

Ids that must NOT be wired are listed in the test (WRONG_SPELL_VISUALS): the spec's Eruption, Hurl Axe, Whirlwind,
Chemical Flames, Volcanic Geyser, Fire Beam, Holy Channeling, Penance, Eye Beam (as a beam), Smash and Living Bomb
looks, and every other pick the report marks WRONG; the keg display 24860 is an invisible stalker.
"""

# --- Minted (patch-M) -------------------------------------------------------------------------------------------------

# Hurley's Lager Puddle (HU, 5 yd radius, 30 s): the Ascension `Goo_flow_state_wheat_beer` (a 47.8 yd quad of tinted
# slime, amber by its name, not decoded) at scale 0.21 as a STATE on a stalker (one stalker per puddle). Burning Lager
# (H) swaps the stalker's aura for SHIPPED_LAVA_POOL[5].
SV_LAGER_PUDDLE = 90650
# Lord Incendius's Crumbled Edge (IN, gap 35): the Ascension `groundcrack_fire_state` (a 29.4 yd quad of radial lava
# cracks and glow) at 0.35, a STATE on a stalker every 10 yd along the band, under the orange 4 yd edge kit line. The
# quad is radial, not a strip: tune scale and spacing together. Fallback: SHIPPED_LAVA_POOL[4] every 6 yd.
SV_CRUMBLED_EDGE_CRACK = 90651
# Moira's fire cage (MO, gap 34): the stock FlameCircleEffect at 0.64 (a ring of fire about 1.5 yd across) as a STATE
# at her base; cast Fire Shield (MO_FIRE_CAGE_WHIRL, SV 8581) beside it for the flame whirl.
SV_MOIRA_FIRE_CAGE = 90652
# The Vault security field (VA3, 6 yd, H grows 1 yd per 10 s to 9 yd): the Ascension `target_arcane_state_centeronly`
# disc, one STATE rung per yard of radius, on a stalker at the sentinel. A stalker aura cannot resize: pick the
# smallest rung at or above the real radius (`security_field_rung`). Keyed by the rung radius in yd.
SV_SECURITY_FIELD = {6: 90653, 7: 90654, 8: 90655, 9: 90656}
SECURITY_FIELD_RADII = tuple(sorted(SV_SECURITY_FIELD))
# Purple rune ring under the bearer (the Seven's Hatred and Doom mark; the runner's alternate for Grebmar's Fetch): the
# Ascension Odyn purple brand, the BRS orange and yellow brands' sibling, a 3.8 yd ring as a BASE state.
SV_PURPLE_RING = 90657
# Flamelash's Portal Anchor (FL): the stock Creature_SpellPortalLarge_Red (12 yd tall) at 0.4 (about 4 yd tall) as a
# STATE on the anchor, one per rune spot. The stock Boss Fire Portal State (SV 9462) is the 12 yd fallback.
SV_PORTAL_ANCHOR = 90658
# Anub'shiah's Web Spit patch, 6 yd (optional): the stock Web_State at 5.2. The shipped 7 yd (SHIPPED_WEB_PATCH_7_STATE)
# and 5 yd (SHIPPED_WEB_PATCH_5_STATE) rows are the first picks and the picks wired below.
SV_WEB_PATCH_6 = 90659
# Hurley's Thunderbrew Lager Keg creature (HU): a new CreatureModelData + CreatureDisplayInfo on the stock
# `World\Goober\G_Keg.mdx` (2.7 x 2.7 x 2.6 yd, the keg object's model with its beer mist). The spec's display 24860 is
# an invisible stalker and must never be the keg. Alternate: 90771 on `BeerKeg02.mdx` (1.4 yd). The creature scale and
# combat reach are set by the boss WP (gap 29, handoff s6).
DISPLAY_LAGER_KEG = 90770
DISPLAY_LAGER_KEG_ALT = 90771

# Scales set on the creature, not in the DBC (floats on purpose: not ids).
AVATAR_SCALE_RANGE = (0.12, 0.18)           # CDI 11121 is 58 yd tall at 1.0; 7 to 10 yd tall fits the 21 yd dais
INCENDIUS_GIANT_SCALE_RANGE = (8.0, 10.0)   # CDI 1204 is 3 yd tall at 1.0; the hard mode giant reaches the island edge
KEG_NOTE_SCALE = 1.0                        # the keg displays are minted at model scale 1.0

# --- Shipped (patch-M and the working copy) ---------------------------------------------------------------------------

# Blackrock Spire (V-2 there): the lava pool ladder (Ascension `magmazone`), STATE on a stalker, key = radius in yd.
SHIPPED_LAVA_POOL = {4: 90606, 5: 90607, 6: 90608, 7: 90609, 8: 90610, 9: 90611, 10: 90612}
LAVA_POOL_RADII = tuple(sorted(SHIPPED_LAVA_POOL))
SHIPPED_SHADOW_POOL_4_STATE = 90601     # Ascension shadow quad, 4 yd (AREA twin 90600)
SHIPPED_SHADOW_POOL_6_STATE = 90605     # 6 yd (AREA twin 90604)
SHIPPED_ORANGE_RING = 90613             # Odyn orange rune ring, 3.8 yd under the bearer (a mark)
SHIPPED_YELLOW_RING = 90614
SHIPPED_HORN_BLOWN = 90602              # the stock horn cast (sound 6423, anim 81) plus the orange shock-ray burst
# Stratholme: web patches (stock Web_State scaled), the lasting keening skull, the 8 yd fire zone.
SHIPPED_WEB_PATCH_5_STATE = 90501       # 5 yd (AREA twin 90500)
SHIPPED_WEB_PATCH_7_STATE = 90503       # 7 yd (AREA twin 90502)
SHIPPED_KEENING_SKULL = 90506           # a lasting head state (Curse of Weakness head)
SHIPPED_FIRE_ZONE_8 = 90508             # flamezone, 8 yd (fallback for the lava pools)
# Deadmines: the green goo puddle (4 yd) and the table wood splinters (ImpactKit, one shot).
SHIPPED_GOO_PUDDLE = 90342              # PersistentArea (an area aura)
SHIPPED_GOO_PUDDLE_STATE = 90343        # State (a stalker aura)
SHIPPED_WOOD_SPLINTERS = 90344

# --- Spells whose SpellVisual stands in for the cast (a copy of the stock visual id is all a spell needs) -------------

# ===== Wave 1: section 1, the Detention Block (D1-D6) =====

# High Interrogator Gerstahn (D1)
GE_DOUBT_SWIRL = 7433               # Glimpse of Madness 26108: a lasting State, confused glyphs (@ # ? !) over the head
GE_DOUBT_SWIRL_BIG = 9231           # Confused State Visual (Big) 47044: the same at scale 2.0 (a raid-distance read)
GE_MIND_FLAY = 277                  # Mind Flay 16568: hand funnel + a ManaBeam channel from the boss to the player
GE_MIND_SEAR = 12121                # Mind Sear 48045: a shadow swirl at the target's feet (the doc's 277 has no ground)
GE_INTERROGATION_BURST = 247        # Intimidating Shout / Psychic Scream: a 0.9 yd ring (the red ring marker is the
                                    # circle)
GE_BROKEN = 247                     # the 2 s fear State on the aura target (the same SV, fear skulls)
GE_LINGERING_DOUBT = SHIPPED_SHADOW_POOL_6_STATE    # the 5 yd pool on a stalker (the kit disc carries the exact edge)
GE_LINGERING_DOUBT_ALT = SHIPPED_SHADOW_POOL_4_STATE
GE_SHADOW_WORD_PAIN = 71            # unchanged stock Shadow Word: Pain
GE_SHADOW_SHIELD = 2476             # Shadow Shield's stock look (D1)

# Lord Roccor (D2)
RO_RAMPAGE = 12188                  # Rampage 55771: a boulder State on the chest (RISKY; the 8 yd line marker is the
                                    # lane)
RO_UNDERFOOT_CRUSH = 10133          # Crush Under Foot 45404: anim + sound only; pair it with RO_UNDERFOOT_CRACK
RO_UNDERFOOT_CRACK = 8083           # Ground Slam 33525: a 3.5 yd crack + shake at the crushed spot
RO_LOOSED_CUE = 858                 # Ground Tremor 6524: shake + sound for the 2 s cast
RO_LOOSED_SPAWN = 12201             # Earthen Spawn 55833: a dirt burst as the stone rises (also the merge's other half)
RO_FLUNG_BOULDERS = 8904            # Boulder Volley 38783: a real boulder in flight (3 yd circle markers carry the
                                    # landing)
RO_MERGE_HEAL = 135                 # Heal 2060: the flash on Roccor when a Loosed Earth is absorbed (H)
RO_MERGE_HEAL_ALT = 344             # Ancestral Spirit 2008: Resurrection base burst
DISPLAY_INVISIBLE_STALKER = 11686   # the invisible stalker skin every kit helper uses (generic stalker 300796)
DISPLAY_LOOSED_EARTH = 1161         # ElementalEarth, brown skin, x0.85 (Roccor himself is CDI 5781)

# Houndmaster Grebmar (D3)
GR_KENNEL_HORN = 4079               # Horn of Elemental Fury 56893: sound 6423 + anim 81 (NEVER Horn of Winter SV 12396)
GR_KENNEL_HORN_BURST = SHIPPED_HORN_BLOWN   # cast from a stalker at the horn: the cast kit plus the shock-ray burst
GR_SIC_LEAP = 29                    # Leap 47482: ChargeTrail + dust (the line and circle markers carry the geometry)
GR_SNATCHED = 398                   # Snatched 50541: a lasting red hand State (the 30 s debuff)
GR_LICK_WOUNDS = 652                # Mend Pet 136: the lasting green heal glow for the 5 s cast
GR_FRENZY = 6943                    # Berserking 23505: the LASTING 15 s red hand State (not the Frenzy flash)
GR_FRENZY_FLASH = 5319              # Frenzy 19516: a one-shot head flash, ONLY as the application flash
GR_RELEASE_THE_HOUNDS = 1523        # Release the Hounds 12851: a summoning bark; the kennel row adds are the visual
GR_FETCH_RUNNER_RING = SHIPPED_ORANGE_RING   # the Fetch runner's 15 s "kill this one" ring under it
GR_FETCH_RUNNER_RING_ALT = SV_PURPLE_RING
DISPLAY_KENNEL_HOUND = 8180         # DarkHound, red skin (alternate 9019, Verek's x1.3)

# Ring of Law frame and waves (D4)
RL_THROW_BOTTLE = 9741              # Throw Bottle 43291: Bottle01 missile + an orange AcidBurn splat (3 yd marker)
RL_ROTTEN_APPLE = 12567             # Rotten Apple Toss 58509
RL_ROTTEN_BANANA = 12569            # Rotten Banana Toss 58513
RL_CROWD_GIFT = 7526                # Cascade of Roses 27571: a thrown flare that lands as lasting rose petals (gap 16)
RL_CROWD_GIFT_ALT = 7525            # Flower Shower 27569: the same petals, ground only
RL_CROWD_GIFT_ALT_2 = 11037         # Chuck Mug 50276: a thrown tankard for a "tossed beer" gift
RL_TRIAL_BURST = 889                # Massive Eruption 20483: Bomb_ExplosionA + molten chest, cast from 4 to 6 stalkers
                                    # through the wedge under the 90 degree red cone marker (NEVER Eruption SV 5043)
RL_TRIAL_BURST_ALT = 7251           # Spawn - Red Lightning 24240: a red column, 4 s, about 30 yd tall, per stalker
RL_BANNER_BURN = 8490               # Ignite Horde Siege Engine 32979: fire hands, a missile and an explosion at the
                                    # banner
RL_BANNER_BURN_ALT = 10211          # Torch Toss 45732: the 0.8 yd torch missile
RL_RAISED = 7566                    # Spirit Particles (purple) 28126: a lasting purple ghost State on a Risen beast or
                                    # Risen Champion (NEVER as Gather Doom, the Seven's look; one purple state per role)
RL_RAISED_ALT = 634                 # Raise Dead 17475: a one-shot burst
GODI_ARENA_BANNER = 6663            # ArenaFlag.mdx (1.1 x 2.4 x 5.9 yd), GO 181058
# Ring of Law wave mobs (RW)
RW_BURROW = 8691                    # Submerge 37550: anims 201 / 202, the worm sinks; add RW_BURROW_ERUPT at the 2 s
                                    # mark
RW_BURROW_ERUPT = RO_LOOSED_SPAWN   # the dirt burst under the player
RW_TAIL_STING = 7391                # Tail Sting 36659: cast anim + missile + impact anim (the cone marker is the
                                    # telegraph)
RW_SCREECH = 13637                  # Sonic Screech 64422: a readable cast puff
RW_THUNDERCLAP = 145                # Thunderclap 15548: a 6.9 yd crack + shake (the 10 yd ring marker carries the
                                    # radius)
RW_VENOM_SPIT = 10397               # Poison Cloud 23861: a lasting green fog on the dynamic object (4 yd)
RW_VENOM_SPIT_ALT = SHIPPED_GOO_PUDDLE      # the Deadmines goo AREA, 4 yd (STATE twin SHIPPED_GOO_PUDDLE_STATE)
RW_VENOM_POOL = SHIPPED_GOO_PUDDLE_STATE   # the RW5 pool's look: the same goo as a STATE on the pool's stalker (4 yd)
RW_ACID_BURST = 4339                # Spawn Bile Slime 16809: a green burst ON THE GROUND at the corpse (NEVER SV 14985)
# Ring of Law champions (CH, D5)
CH_TITLE_HOLDER = 6943              # Berserking: the lasting hand glow for the second champion's +10%
CH_TITLE_HOLDER_FLASH = 4345        # Strength of the Champion 16916: a one-shot impact, ONLY as the arrival flash
GO_DERVISH_DANCE = 7428             # Whirlwind 26083: a lasting Cyclone State while he runs (NEVER SV 227, a cleave
                                    # flash)
GO_RETURNING_AXE = 3962             # Throw Axe 16075: missile_axe_copper; the return is the same cast with caster and
                                    # target
                                    # swapped (NEVER Hurl Axe SV 14843, no missile)
GO_RETURNING_AXE_LINE = 10920       # Harpoon Chain 49679: a Beam_ChainIron for the return line
GODI_STUCK_AXE = 8494               # ORCAXE02, the stuck axe for the 6 s landing (BRS-verified)
GZ_BULL_RUSH = 6                    # Bull Rush 4083: Sprint dust + a RibbonTrail State on the chest
GZ_DAZED = 84                       # Dazed 1604: a lasting Sap-style yellow-stars State
GZ_WALL_IMPACT = 12714              # Boulder Impact 46895: shake + sound (ONLY as the wall impact, never a falling
                                    # boulder)
GZ_EARTHSHAKER_STOMP = 2355         # War Stomp 45: a 6.9 yd crack; the 12 yd ring marker carries the radius
GZ_KILLING_FRENZY_FLASH = 870       # Frenzy 8269: one flash per stack, the stack cue
GZ_KILLING_FRENZY = 6943            # Berserking: the lasting alternate
EV_SPELL_EATER = 127                # Anti-Magic Shield 7121: the shell State for 8 s
EV_DEVOURED_MAGIC = 7966            # Shadow Nova 30852: a shadow nova (+ a red FireNova ring) on the break
EV_DEVOURED_MAGIC_ALT = 11329       # Hatch Eggs 58542: a pure-shadow burst
EV_OPEN_WOUNDS = 376                # Bite 17253: a lasting blood State (NEVER the one-puff Vicious Rend SV 372)
EV_SHADOW_BOLT_VOLLEY = 2318        # Shadow Bolt Volley 15245's own look (also the Seven's Doom burst pick)
OK_ARCANE_RUPTURE = 9970            # Arcane Nova 44644: a blue dome on Ok'thor (RISKY, the donut marker is the danger)
OK_SHEEP_BOLT = 12978               # Polymorph 118
AN_RAISE_DEAD = 634                 # Raise Dead 17475: shadow hands + a flash at the corpse spot
AN_WEB_SPIT = 684                   # Web 745: the missile + a 2.3 yd web decal at the target
AN_WEB_PATCH = SHIPPED_WEB_PATCH_7_STATE    # the 6 yd, 20 s patch on a stalker (7 yd rung: the safe side)
AN_WEB_PATCH_ALT = SHIPPED_WEB_PATCH_5_STATE
AN_WEB_PATCH_6 = SV_WEB_PATCH_6     # the optional exact 6 yd row
HE_WEB_STRANDS = 7613               # Web Spray 29484: the cast; the strand is a white kit line, 4 yd wide
HE_WEB_STRAND_PATCH = SHIPPED_WEB_PATCH_5_STATE   # a 5 yd patch every 8 yd along the strand (decoration)
HE_REEL_IN = 7610                   # Web Wrap 28622
HE_BANEFUL_BURST = 12084            # Poison Nova 55081: a green nova (the 10 yd ring marker carries the radius)

# The Encore team (EN, D6; hard mode)
TH_EXECUTIONERS_CHARGE = 867        # Charge 100 (Intercept shares it)
TH_EXECUTE = 250                    # Execute 5308: blood hands + impact
TH_INTIMIDATING_ROAR = 247          # Intimidating Shout 5246 (alternate 4939, Bellowing Roar)
TH_CHAMPIONS_PRIDE = 236            # Recklessness 1719: the lasting red chest glow below 30%
KO_CHAIN_HEAL = 3659                # Chain Heal 1064
KO_ANCESTRAL_SPIRIT = 344           # Ancestral Spirit 2008: the Resurrection burst at the corpse
KO_EARTH_SHIELD = 7362              # Earth Shield 974's own look (Theldren's shield, read from the client Spell.dbc)
KO_SEARING_BOLT = 67                # the Searing Totem's Attack 3606's own look (the totem's bolt)
LE_SHADOWSTEP = 8262                # Shadowstep 36563: shadowsteps_fx + anim 54
LE_VICIOUS_WOUND = 376              # Bite: the lasting bleed State (NEVER the one-puff Garrote SV 757)
LE_EVASION = 8996                   # Adrenaline Rush 13750: the lasting twin (the stock Evasion SV 72 shows once)
LE_EVASION_ALT = 72
VL_BLIZZARD = 10386                 # Blizzard 27618 on a dynamic object (the 8 yd marker carries the radius)
VL_FROST_NOVA = 17                  # Frost Nova 122
VL_BLINK = 263                      # Blink 1953
VL_ICE_BARRIER = 4302               # Ice Barrier 11426
MA_PIERCING_SHOT = 7955             # Aimed Shot 31623: a real bolt down the kit line
MA_SNAP_TRAP_FREEZE = 4499          # Freezing Trap Effect 3355: an ice State on the victim
MA_DISENGAGE = 12305                # Disengage 781: the leap anim only (the move is server side)
MA_MULTI_SHOT = 567                 # Multi-Shot 2643
GODI_SNAP_TRAP = 7529               # G_BearTrap (open, trigger, close anims 145, 147, 148; BRS-verified)
DISPLAY_KORV_TOTEM_HEALING = 4587   # Healing Stream Totem
DISPLAY_KORV_TOTEM_SEARING = 4589   # Searing Totem (also Magma Totem and the Defiling Totem)
DISPLAY_KORV_TOTEM_EARTHBIND = 4588  # Earthbind Totem (also Stoneclaw)
DISPLAY_LEFTY = 15972
DISPLAY_MALGEN = 15975
DISPLAY_KORV = 15976
DISPLAY_VOLIDA = 15980
DISPLAY_THELDREN = 15981

# ===== Wave 1: section 2, Shadowforge City (D7-D13) =====

# Pyromancer Loregrain (D7)
LG_FIRE_TIDE = 13372                # Flame Wave 75413: a rune base + a FireNova x4 shockwave at the boss (the donut
                                    # marker)
LG_MOLTEN_SPLASH = 11565            # Lava Burst 51505: a real lob and a molten splash
LG_MOLTEN_SPLASH_PATCH = SHIPPED_LAVA_POOL[4]   # the 4 yd patch on a stalker
LG_FURY_OF_RAGNAROS = 141           # Fury of Ragnaros 15288: a glow per gain
LG_WRATH_OF_RAGNAROS = 143          # Fire Blast 16144: hands + a chest flash (plus the extra donut marker)
LG_MOLTEN_BLAST = 305               # Molten Blast copy's stock look (D7; also Searing Bolt for now)
LG_FLAME_SHOCK = 516                # Flame Shock copy's stock look (D7)
LG_FIRE_WARD = 6764                 # Fire Reflector 23097: the lasting red ribbons (NEVER the one-shot SV 290)
LG_WARD_REPEL = 3643                # Holy Nova 15237: a light ring as the spirit throws the defiler out (unconfirmed;
                                    # the alternate is Holy Wrath's SV 126)
LG_WARD_REPEL_ALT = 126
DISPLAY_DEFILING_TOTEM = 4589       # FireElementalTotem (the stock Scorching Totem; 9637 spawns nowhere)
DISPLAY_FRANCLORN_SPIRIT = 8710     # the stock dwarf, the ward anchor (the stack disc is a telegraph kit marker)

# Warder Stilgiss and Verek (D8)
ST_FROSTBOLT = 13                   # stock Frostbolt (D8)
ST_CURSE_OF_BLOOD = 876             # stock Curse of Blood (D8)
ST_OPEN_COFFER = 104                # Opening Relic Coffer 13478: anim + sound only (the door animates by script)
ST_EYE_IMPACT = 7434                # Eye Beam 26134: ONLY the chest impact on the hit player; the red 4 yd line is the
                                    # beam
ST_BLACK_STEEL_BINDINGS = 10920     # Harpoon Chain 49679: an iron chain between the pair (NEVER SV 7597)
ST_BLACK_STEEL_BINDINGS_ALT = 10165  # Spirit Shackle 45581: a thin gold chain
ST_MAGMA_BAND = 12227               # Magma Wave 55916: a fire wave projectile (the 4 to 9 yd donut marker carries the
                                    # band)
ST_WAND_IMPACT = 3400               # Holy Fire 15261: the impact on a hit (the lines are white 3 yd kit lines; NEVER SV
                                    # 12479)
ST_WAND_BEAM_ALT = 11500            # HealBeam from stalkers at the line ends
ST_BLACK_BLOOD = SHIPPED_SHADOW_POOL_4_STATE    # the 3 yd, 30 s pool: a dark patch (NEVER the green SV 8305)
DISPLAY_VEREK = 9019                # DarkHound x1.3
DISPLAY_STILGISS = 9089             # a stock dwarf x1.2

# The Vault, Watchman Doomgrip (D9)
VA_LOCKDOWN = 8225                  # Force Field Visual 34648: the Dire Maul force field State on a stalker at the door
VA_SENTINEL_WAKES = 11519           # Awaken 52875: Stoneform State x4 + exploding stone (NEVER Activate Construct SV
                                    # 13174)
VA_SENTINEL_WAKES_ALT = 5787        # Stoneform 20594
VA_SECURITY_FIELD = SV_SECURITY_FIELD   # the rung table (see `security_field_rung`)
VA_SECURITY_LINK = 13261            # Beam Link 62881: a chain from each sentinel to Doomgrip
VA_SECURITY_LINK_ALT = 8371         # Lightning Tether: a heavier chain
VA_INTRUDER_SWEEP = 2717            # Sweeping Slam 12887 (the 90 degree cone marker is the sweep)
VA_SUNDER_ARMOR = 39                # Sunder Armor 11971's own look (the Warbringer's armor shred)
VA_WATCHMANS_DRAUGHT = 101          # Thunderbrew Lager 5257: a tankard in hand, anim 61, a heal flash
DISPLAY_VAULT_SENTINEL = 8289       # GolemStone, copper x2.1 (the Warbringer Construct; Arcanoton shares it)

# Fineous Darkvire (D10)
FD_PILLAR_SPAWN_BURST = 12718       # Ground Spike 59750: the earth spike as the pillar rises
FD_COLLAPSE_DUST = 12855            # Rock Shower 60919: a dust plume at the pillar's base (also Bael'Gar's rockfall)
FD_COLLAPSE_DUST_ALT = 8216         # Cannon impact dust
FD_HOLY_LIGHT = 2936                # Holy Light (stock self-heal look, D10)
GODI_SHODDY_PILLAR = 5073           # Stalagmite01 (3.6 x 2.6 x 4.8 yd), size 1.0, spawned on the 3 s warning
GODI_SHODDY_PILLAR_ALT = 205        # LavaPillar01 (3.3 x 3.8 x 9.2 yd) at size 0.6
GODI_GUZZLER_ROPE_PICKUP = 7538     # CaveKoboldRopeCoil (1.3 x 1.2 x 0.1 yd), the stock Rope Pile
GODI_HANGING_ROPE = 7717            # Borean_Rope_01 (2.4 x 2.5 x 65.1 yd), size 0.5 = about 32 yd for the 20 yd climb
HANGING_ROPE_SIZE = 0.5
SHODDY_PILLAR_SIZE = 1.0
SHODDY_PILLAR_ALT_SIZE = 0.6

# Lord Incendius (D11, D12)
IN_FIERY_BURST = 516                # Fiery Burst 15668
IN_FIRE_STORM_CAST = 10383          # Fire Storm 13899: the cast hands and channel ONLY (its 23 yd PersistentArea is not
                                    # the patch)
IN_FIRE_STORM_PATCH = SHIPPED_LAVA_POOL[5]      # the 5 yd, 30 s patch on a stalker
IN_MAGMA_FIST = 12227               # Magma Wave 55916: the fire wave projectile along the line
IN_MAGMA_FIST_RING = 9426           # Ember Blast 34133: the FireNova ring at his feet + the chest impact on a hit
IN_LAVA_SURGE = 12456               # Lava Strike 57571: fire bursts from stalkers every 12 yd along the strip
IN_LAVA_SURGE_PATCH = SHIPPED_LAVA_POOL[6]      # (a 6 yd patch where the surge lands, if the strip leaves ground fire)
IN_REBORN_AT_THE_ANVIL = 9727       # Pillar of Fire 43541: a fire spiral at the anvil (NEVER the blue SV 3944)
IN_SHATTER_INTO_EMBERS = 889        # Massive Eruption 20483 at his death spot
IN_CRUMBLED_EDGE_CRACK = SV_CRUMBLED_EDGE_CRACK
IN_CRUMBLE_BURST = 12456            # Lava Strike from stalkers along the band (the burst as the edge goes)
IN_CINDER_TOSS = 10211              # Torch Toss 45732: a flaming object arcs into the lava (alternate 9741, Throw
                                    # Bottle)
IN_CRUSHING_FIST = 13373            # Overhead Smash 63356: a 6.9 yd crack + shake (alternate 8083)
IN_ARM_SWEEP = 13481                # S 63766: anim only; the 10 yd band marker carries the sweep
IN_FIRELORDS_BREATH = 3119          # Heat Wave 35236: FlameBreath at the Breath attach + an Immolate state on the hit
                                    # (NEVER Flame Breath SV 14506, anim only, or Petrifying Breath SV 13093, sand)
IN_CURSE = 3959                     # Curse of the Elemental Lord 26977's own look (read from the client Spell.dbc)
IN_FIRELORDS_WILL = 8581            # Fire Shield 35265: the lasting CycloneFire State on him (BRS Overlord's Fury)
IN_LAVA_SPAWN_CLIMB = 5723          # Ragnaros Emerge 20568: anim only; add IN_SHATTER_INTO_EMBERS at the edge point
DISPLAY_EMBER_OF_INCENDIUS = 1405   # FireElemental x0.6 (alternates 6537 x0.4, 8409 x0.25)
DISPLAY_EMBER_ALT = 6537
DISPLAY_INCENDIUS_GIANT = 1204      # FireElemental x1.5; the creature scale is INCENDIUS_GIANT_SCALE_RANGE
DISPLAY_LAVA_SPAWN = 2172           # FireElemental x0.75 (the Molten Core Lava Spawn; alternate 1405)

# Bael'Gar (D13)
BG_ROCKFALL = 12855                 # Rock Shower 60919 per circle (NEVER Cave In SV 8455, a faint puff)
BG_BOULDER_MISSILE = 8904           # Boulder Volley 38783 from a stalker overhead: the falling boulder
BG_BOULDER_LAND = 12714             # Boulder Impact 46895: shake + sound on landing ONLY, after the missile
BG_BOULDER_MELT = 8097              # Exploding Stone Impact at the base as the boulder melts on the Furnace
BG_MOLTEN_FURNACE = 3119            # Heat Wave 35236: a breath from his mouth + a burning State on every unit he sees
BG_FISSURE_BURST = 10917            # S 49656: the initial burst ONLY (one blob, not a line)
BG_FISSURE_LAVA = SHIPPED_LAVA_POOL[4]          # a 4 yd lava patch every 6 yd under the orange 4 yd line marker
BG_MAGMA_SPLASH = 3221              # Magma Splash 13880: the Immolate state on the tank (unchanged)
GODI_FALLEN_BOULDER = 3711          # LavaRock01 (4.8 x 5.4 x 10.2 yd; collision verified by the designer)
GODI_FALLEN_BOULDER_ALT = 5736      # LavaRock02 (8.2 x 9.3 x 8.5 yd): the fallback if the LOS check of 3711 fails
GODI_FALLEN_BOULDER_ALT_2 = 6752    # G_IceBlock
DISPLAY_BAELGAR = 12162             # MountainGiant MoltenGiant x1.75 (Magmus wears it too)

# ===== Wave 2: section 3, the Manufactory (D14-D16) =====

# General Angerforge (D14)
GODI_MOLE_MACHINE = 7510            # Beerfest_MoleMachine, GO 186763, size 0.6 (about 6.8 x 7 x 11.5 yd)
MOLE_MACHINE_SIZE = 0.6
AF_MOLE_DEPLOY = 9788               # Deploy Mole Machine 43563: a dirt burst + shake (also the Emperor's guards' door)
AF_MOLE_RETREAT = 9901              # Retreat 44204
AF_COMMANDING_SHOUT = 6506          # Commanding Shout 22440: re-cast every 5 s; the 15 yd orange kit ring is the aura
AF_COMMANDING_SHOUT_ALT = 5139      # Concentration Aura 19746
AF_IRON_GRENADE = 3819              # Iron Grenade 4068: a bomb missile + an explosion
AF_GRENADE_MARK = SHIPPED_ORANGE_RING   # the 5 s mark under each marked player
AF_MEDIC_HEAL = 135                 # Heal 15586
DISPLAY_SQUAD_RESERVIST = 8755      # x0.9
DISPLAY_SQUAD_MEDIC = 8752
DISPLAY_SQUAD_OFFICER = 8754        # Anvilrage Overseer (alternate 8749, the Captain)
DISPLAY_SQUAD_OFFICER_ALT = 8749

# Golem Lord Argelmach (D15, D16)
AR_GOLEM_WAKES = 11519              # Awaken 52875 (NEVER Activate Construct SV 13174, a fire strike)
AR_CHEMICAL_BOMB = 10395            # Noxious Cloud 21070: green GreenGhost State on the mark AND the cloud (NEVER
                                    # Living
                                    # Bomb SV 11840, a fire whirl)
AR_CHEMICAL_CLOUD = 10395
AR_CHEMICAL_CLOUD_ALT = SHIPPED_GOO_PUDDLE      # the 4 yd green goo (STATE twin SHIPPED_GOO_PUDDLE_STATE)
AR_POISON_MIST = 12084              # Poison Nova 55081 (H): a green nova at the golem
AR_LETHAL_ATTRACTION = 8371         # Lightning Tether 33628: a chain-lightning tether between the pair
AR_LIVEWIRE = 37                    # Lightning Shield 15507: the lasting electric State on the carrier (NEVER SV 11840)
AR_LIVEWIRE_ALT = 97                # Shock: an impact
AR_ARCANE_OVERCHARGE = 5441         # Mana Bomb 36846: a bomb missile + an arcane explosion on the spot after 4 s
AR_CHAIN_LIGHTNING = 36             # Chain Lightning 15305 (stock)
AR_SHOCK = 97                       # Shock 15605 (stock)
AR_LIGHTNING_SHIELD = 37            # Lightning Shield 15507 (stock)
AR_FLAMETHROWER = 3119              # Heat Wave 35236: FlameBreath + immolate on the hit (NEVER Chemical Flames SV
                                    # 10407, fel
                                    # green; Magmatron is molten orange)
AR_INCINERATION = 6899              # Fire Nova 23462: the ring (alternate AR_FLAMETHROWER)
AR_SALVAGED_CORE = 37               # Lightning Shield 15507's lasting sparks on the Salvaged Core (D16)
DISPLAY_ARCANE_ORB = 26753          # PowerSparkCreature x2.0 (the BRS shard; alternate 24813 ScryingOrb)
DISPLAY_ARCANE_ORB_ALT = 24813
DISPLAY_TOXITRON = 8177             # GolemCannonStone copper x1.5 (Phalanx wears it too)
DISPLAY_ELECTRON = 8178             # same model, obsidian x1.8
DISPLAY_ARCANOTON = 8289            # GolemStone copper x2.1 (the Vault Sentinels wear it too)
DISPLAY_MAGMATRON = 8179            # GolemStone molten x1.8
GODI_ACTIVATION_CONSOLE = 6424      # G_ControlConsoleTonk (0.6 x 0.7 x 1.5 yd; use anims 146 to 149), GO 188498
GODI_FOURTH_PEDESTAL = 3311         # DarkIronAnvil (6 x 6.1 x 2 yd plinth; match the three pedestals' height in game)
GODI_FOURTH_PEDESTAL_ALT = 7550     # DarkIronOperationTableEmpty (golem parts)
GODI_GOLEM_PEDESTAL = GODI_FOURTH_PEDESTAL   # the three golem pedestals of D15 share the fourth one's display

# ===== Wave 2: section 4, the Imperial Seat (D17-D24) =====

# Hurley Blackbreath and the Cronies (D18)
HU_KEG_MARK = SHIPPED_ORANGE_RING   # the "smash this" ring under the marked keg
HU_DRINK = 101                      # Thunderbrew Lager 5257: a tankard in hand + a heal glow
HU_LIQUID_COURAGE = 6943            # Berserking: the LASTING look (the doc's Drunken Rage SV 870 shows once per drink)
HU_LAGER_BUZZ_FLASH = 870           # Drunken Rage: one flash for the 5 s tail
HU_LAGER_PUDDLE = SV_LAGER_PUDDLE   # the 5 yd, 30 s puddle on a stalker
HU_BURNING_LAGER = SHIPPED_LAVA_POOL[5]   # Firewater (H): replaces the amber state while burning
HU_TIPSY = 3440                     # Blind 2094: the confused glyphs (NEVER Drunken Stupor SV 2816, a stun swirl)
HU_FLAME_BREATH = 7651              # Breath of Fire 12278 (the 15 yd cone marker)
HU_BOTTLE_TOSS = 9741               # Throw Bottle 43291 (alternate 11037, Chuck Mug); the 3 yd circle marker
HU_BOTTLE_TOSS_ALT = 11037

# Phalanx and the Grim Guzzler (D17, D19)
PH_THROW_OUT_GRAB = 12139           # Grabbed 55424: an InterveneTrail State on the held player
PH_THROW_OUT_FLIGHT = 12140         # Throw 55425: anim only (the flight is a server knockback)
PH_THROW_OUT_LANDING = 8083         # Ground Slam: the crack + shake under the thrown player (6 yd circle marker)
PH_LAST_CALL = 215                  # Ring Bessy's Bell 35209: the bell, then PH_THROW_OUT_LANDING for the pulse
PH_TABLE_SPLINTERS = SHIPPED_WOOD_SPLINTERS     # the table smash chips + steam (NEVER Smash SV 3948, blood + a stun
                                                # swirl)
PH_OUTRAGE = 4939                   # Bellowing Roar 18431
PH_THUNDERCLAP = 145                # Thunderclap 15588 (stock)
PH_FIREBALL_VOLLEY = 2437           # Fireball Volley 15285 (stock)
DISPLAY_ROWDY_PATRON = 8681         # Hammered Patron x1.2 (alternate 8673, Grim Patron)
DISPLAY_ROWDY_PATRON_ALT = 8673
DISPLAY_PHALANX = 8177              # GolemCannonStone copper x1.5 (the Toxitron model)

# Ambassador Flamelash (D20)
FL_PORTAL_ANCHOR = SV_PORTAL_ANCHOR  # the 4 yd tall portal STATE on each anchor
FL_PORTAL_ANCHOR_ALT = 9462         # Boss Fire Portal State 42048: the stock 12 yd tall portal
FL_KINDLING_STATE = 2638            # Ignite 12654: the lasting Immolate State on the target
FL_KINDLING_CHANNEL = 10383         # Fire Storm: the channel hands from Flamelash (NEVER Fire Beam SV 10856, blue +
                                    # grey)
FL_BURNING_TRAIL = SHIPPED_LAVA_POOL[4]         # the 4 yd, 15 s patch per step
FL_BURNING_TRAIL_ALT = SHIPPED_FIRE_ZONE_8
FL_BURNING_SPIRIT_STACK = 3321      # Burning Spirit 14744: a flash per arrival
FL_FIRE_BLAST = 2996                # Fire Blast 13342's own look (the live spell_dbc override row)
DISPLAY_BURNING_SPIRIT = 4607       # FireElemental x0.5
DISPLAY_FLAMELASH = 8329            # SalamanderMale, red

# The Seven (D21)
TS_SHADE = 7566                     # Spirit Particles (purple) 28126: the lasting shade State (NEVER also Gather Doom)
TS_SHADE_FADE = 7707                # Incorporeal 54657: the pixie-star flash on the fade
TS_GATHER_DOOM_CAST = 64            # Shadow Bolt hands for the cast
TS_GATHER_DOOM_LANDING = 71         # Shadow Word: Pain on landing
TS_FURIOUS_CHARGE = 867
TS_SEETHING_COLD = 675              # Chilled 6136: the lasting ice head State
TS_DOPEY_HAZE = 84                  # Dazed 1604: the lasting yellow stars
TS_GLOOM_RELS_RECKLESSNESS = 236    # Recklessness 1719 on Gloom'rel
TS_GLOOM_HEALING_MARK = SHIPPED_KEENING_SKULL   # the players' -50% healing: the lasting skull head State
TS_VILE_COMMUNION = 194             # Prayer of Healing 596 (re-cast at 3 s if the 6 s channel should keep showing)
TS_HATRED = SV_PURPLE_RING          # the 8 s mark under the target (NEVER Shadow Mark SV 223, a dust whirl)
TS_HATRED_ALT = SHIPPED_KEENING_SKULL
TS_DOOM_MARK = SHIPPED_KEENING_SKULL    # the 6 s mark (NEVER the 3 s Curse of Doom SV 5019 alone) ...
TS_DOOM_MARK_RING = SV_PURPLE_RING  # ... plus the purple ring
# The kit copies' own stock looks (each the stock spell's SpellVisualID_1, read from the client Spell.dbc; none is on
# the WRONG list); the_seven.py picks them up by name.
TS_FROSTBOLT = ST_FROSTBOLT         # Frostbolt 12675: SV 13
TS_CONE_OF_COLD = 1007
TS_FROST_NOVA = VL_FROST_NOVA       # Frost Nova 12674: SV 17
TS_BACKSTAB = 611                   # Backstab 15582
TS_RUPTURE = 250                    # Rupture's copy (the Execute look)
TS_GOUGE = 256                      # Gouge 12540
TS_MIND_BLAST = 3057                # Mind Blast 15587
TS_SHADOW_BOLT = TS_GATHER_DOOM_CAST    # Shadow Bolt 15232: SV 64
TS_SHADOW_BOLT_VOLLEY = EV_SHADOW_BOLT_VOLLEY   # Shadow Bolt Volley 15245: SV 2318
TS_IMMOLATE = 46                    # Immolate
TS_FURIOUS_STOMP = GZ_EARTHSHAKER_STOMP     # War Stomp 15593: SV 2355
TS_DOOM_BLAST = EV_SHADOW_BOLT_VOLLEY       # Doom's burst on the doomed: the volley's impact (V-2's pick)
DISPLAY_ANGERREL = 8686
DISPLAY_SEETHREL = 8691
DISPLAY_DOPEREL = 8688
DISPLAY_GLOOMREL = 8689
DISPLAY_VILEREL = 8692
DISPLAY_HATEREL = 8690
DISPLAY_DOOMREL = 8687

# Magmus (D22)
MG_STATUE_GLOW = 4101               # Flame Wreath 29947: an Immolate State on a statue (NEVER SV 3640, anim only)
MG_CROSSFIRE_BREATH = 3642          # Gout of Flame 15538: the stream down the 10 yd lane (and the Flame Wall's 12 yd
                                    # line)
MG_CROSSFIRE_END = 13233            # Flame Jets 62680: a burst at the lane end
MG_FIERY_BURST = 516                # Fiery Burst 15668
MG_WAR_STOMP = GZ_EARTHSHAKER_STOMP     # War Stomp 15593's own look (the same one Grizzle uses)
MG_DRIPPING_MAGMA = SHIPPED_LAVA_POOL[4]        # (H) 4 yd every 3 s while he walks
MG_DRIPPING_MAGMA_ALT = SHIPPED_FIRE_ZONE_8
DISPLAY_IRONHAND_GUARDIAN = 9189    # GolemCannonStone molten x3.0 (unselectable scenery)
DISPLAY_MAGMUS = 12162              # MountainGiant MoltenGiant x1.75 (Bael'Gar wears it too)

# Emperor Dagran Thaurissan and Princess Moira (D23, D24)
EM_NEMESIS_BEAM = 11500             # WotLK Prologue Light Beam 52407: a gold HealBeam chain from Moira to Dagran (NEVER
                                    # Holy Channeling SV 11274 or Penance SV 10980, hand glows with no beam)
EM_NEMESIS_BEAM_ALT = 8407          # Blade's Edge Multi Gold Beam 35960
EM_RADIANT_BURN = 3400              # Holy Fire 15261: the damage flash on the blocker
EM_TWILIGHT_TETHER = 12480          # Twilight Channel 57797: a thin dark beam
EM_FLAMESTRIKE_CAST = 10383         # the cast hands (the 23 yd PersistentArea is not the burn)
EM_FLAMESTRIKE_BURN = SHIPPED_LAVA_POOL[6]      # the 6 yd, 4 s burning ground; the 6 yd ring marker is the warning
EM_FIRESTORM = 889                  # Massive Eruption 20483 at each circle (NEVER Volcanic Geyser SV 9466, blue fire)
EM_FIRESTORM_ALT = 9727             # Pillar of Fire
EM_HAMMER_SLAM_WINDUP = 395         # Volcanic Hammer 16984: the hammer in hand, anim 62 (add EM_HAMMER_SLAM_CRACK)
EM_HAMMER_SLAM_CRACK = 8083         # Ground Slam crack at the cone on the hit
EM_RAGNAROS_AWAKENS = 9727          # Pillar of Fire (+ EM_FIRESTORM at the throne) as the dais swaps to the Avatar
                                    # display
EM_MAGMA_CLAP_RING = 6899           # Fire Nova 23462: the ring at his feet
EM_MAGMA_CLAP_HIT = 5721            # Magma Blast 20565: the impact on each player hit
EM_VOLCANIC_BLAST_MARK = SHIPPED_ORANGE_RING    # the 5 s mark on the marked player (NEVER Eruption SV 5043)
EM_VOLCANIC_BLAST = 11565           # Lava Burst 51505: the missile + molten impact
EM_VOLCANIC_STONE = SHIPPED_LAVA_POOL[5]        # the 5 yd, 30 s persistent stone
EM_SPAWN_BURST = AF_MOLE_DEPLOY     # a stalker's dirt burst if the guards enter through the floor
EM_HAND_OF_THAURISSAN = 143         # Hand of Thaurissan 17492's own look
EM_AVATAR_OF_FLAME = 46             # Avatar of Flame 15636's own look
EM_FLAMES = 2519                    # Flames 15643's own look
MO_MIND_BLAST = 3057                # Mind Blast 15587's own look
MO_NECROSIS = 71                    # Shadow Word: Pain 15654's own look (Necrosis)
MO_FIRE_CAGE = SV_MOIRA_FIRE_CAGE   # the ring of fire at her base ...
MO_FIRE_CAGE_WHIRL = 8581           # ... plus Fire Shield 35265: the CycloneFire State x0.5
DISPLAY_IMPERIAL_GUARD = 8750       # Anvilrage Guardsman (alternate 8749, the Captain)
DISPLAY_IMPERIAL_GUARD_ALT = 8749
DISPLAY_TWILIGHT_AMBASSADOR = 8778  # human male
DISPLAY_AVATAR_OF_RAGNAROS = 11121  # Ragnaros.mdx: the creature scale is AVATAR_SCALE_RANGE
DISPLAY_MOIRA = 8705
DISPLAY_HIGH_PRIESTESS = 9295
DISPLAY_EMPEROR = 8807


def lava_pool_rung(radius: float) -> int:
    """The shipped lava pool SpellVisual for a real radius: the smallest rung at or above it (10 is the top)."""
    return SHIPPED_LAVA_POOL[min((r for r in LAVA_POOL_RADII if r >= radius), default=LAVA_POOL_RADII[-1])]


def security_field_rung(radius: float) -> int:
    """The minted security field SpellVisual for a real radius: the smallest rung at or above it (9 is the top)."""
    return SV_SECURITY_FIELD[min((r for r in SECURITY_FIELD_RADII if r >= radius), default=SECURITY_FIELD_RADII[-1])]


# Every minted SpellVisual (checked against the patch script's rows, not the stock DBCs)
MINTED_SPELL_VISUALS = (
    SV_LAGER_PUDDLE, SV_CRUMBLED_EDGE_CRACK, SV_MOIRA_FIRE_CAGE, *SV_SECURITY_FIELD.values(), SV_PURPLE_RING,
    SV_PORTAL_ANCHOR, SV_WEB_PATCH_6,
)
# Minted creature displays (CreatureDisplayInfo + CreatureModelData rows of the patch script)
MINTED_CREATURE_DISPLAYS = (DISPLAY_LAGER_KEG, DISPLAY_LAGER_KEG_ALT)
# Not in the stock client but already shipped (checked against the working-copy SpellVisual.dbc)
SHIPPED_SPELL_VISUALS = tuple(sorted({
    *SHIPPED_LAVA_POOL.values(), SHIPPED_SHADOW_POOL_4_STATE, SHIPPED_SHADOW_POOL_6_STATE, SHIPPED_ORANGE_RING,
    SHIPPED_YELLOW_RING, SHIPPED_HORN_BLOWN, SHIPPED_WEB_PATCH_5_STATE, SHIPPED_WEB_PATCH_7_STATE,
    SHIPPED_KEENING_SKULL, SHIPPED_FIRE_ZONE_8, SHIPPED_GOO_PUDDLE, SHIPPED_GOO_PUDDLE_STATE, SHIPPED_WOOD_SPLINTERS,
}))

# Every stock SpellVisual id above (the SpellVisual existence check).
STOCK_SPELL_VISUALS = tuple(sorted({
    GE_DOUBT_SWIRL, GE_DOUBT_SWIRL_BIG, GE_MIND_FLAY, GE_MIND_SEAR, GE_INTERROGATION_BURST, GE_BROKEN,
    GE_SHADOW_WORD_PAIN, GE_SHADOW_SHIELD, FD_HOLY_LIGHT, ST_FROSTBOLT, ST_CURSE_OF_BLOOD,
    LG_MOLTEN_BLAST, LG_FLAME_SHOCK,
    RO_RAMPAGE, RO_UNDERFOOT_CRUSH, RO_UNDERFOOT_CRACK, RO_LOOSED_CUE, RO_LOOSED_SPAWN, RO_FLUNG_BOULDERS,
    RO_MERGE_HEAL, RO_MERGE_HEAL_ALT,
    GR_KENNEL_HORN, GR_SIC_LEAP, GR_SNATCHED, GR_LICK_WOUNDS, GR_FRENZY, GR_FRENZY_FLASH, GR_RELEASE_THE_HOUNDS,
    RL_THROW_BOTTLE, RL_ROTTEN_APPLE, RL_ROTTEN_BANANA, RL_CROWD_GIFT, RL_CROWD_GIFT_ALT, RL_CROWD_GIFT_ALT_2,
    RL_TRIAL_BURST, RL_TRIAL_BURST_ALT, RL_BANNER_BURN, RL_BANNER_BURN_ALT, RL_RAISED, RL_RAISED_ALT,
    RW_BURROW, RW_TAIL_STING, RW_SCREECH, RW_THUNDERCLAP, RW_VENOM_SPIT, RW_ACID_BURST,
    CH_TITLE_HOLDER, CH_TITLE_HOLDER_FLASH, GO_DERVISH_DANCE, GO_RETURNING_AXE, GO_RETURNING_AXE_LINE, GZ_BULL_RUSH,
    GZ_DAZED, GZ_WALL_IMPACT, GZ_EARTHSHAKER_STOMP, GZ_KILLING_FRENZY_FLASH, EV_SPELL_EATER, EV_DEVOURED_MAGIC,
    EV_DEVOURED_MAGIC_ALT, EV_OPEN_WOUNDS, OK_ARCANE_RUPTURE, OK_SHEEP_BOLT, AN_RAISE_DEAD, AN_WEB_SPIT,
    HE_WEB_STRANDS, HE_REEL_IN, HE_BANEFUL_BURST, EV_SHADOW_BOLT_VOLLEY,
    TH_EXECUTIONERS_CHARGE, TH_EXECUTE, TH_INTIMIDATING_ROAR, TH_CHAMPIONS_PRIDE, KO_CHAIN_HEAL, KO_ANCESTRAL_SPIRIT,
    KO_EARTH_SHIELD, KO_SEARING_BOLT,
    LE_SHADOWSTEP, LE_VICIOUS_WOUND, LE_EVASION, LE_EVASION_ALT, VL_BLIZZARD, VL_FROST_NOVA, VL_BLINK, VL_ICE_BARRIER,
    MA_PIERCING_SHOT, MA_SNAP_TRAP_FREEZE, MA_DISENGAGE, MA_MULTI_SHOT,
    LG_FIRE_TIDE, LG_MOLTEN_SPLASH, LG_FURY_OF_RAGNAROS, LG_WRATH_OF_RAGNAROS, LG_FIRE_WARD, LG_WARD_REPEL,
    LG_WARD_REPEL_ALT,
    ST_OPEN_COFFER, ST_EYE_IMPACT, ST_BLACK_STEEL_BINDINGS, ST_BLACK_STEEL_BINDINGS_ALT, ST_MAGMA_BAND,
    ST_WAND_IMPACT, ST_WAND_BEAM_ALT,
    VA_LOCKDOWN, VA_SENTINEL_WAKES, VA_SENTINEL_WAKES_ALT, VA_SECURITY_LINK, VA_SECURITY_LINK_ALT, VA_INTRUDER_SWEEP,
    VA_WATCHMANS_DRAUGHT, VA_SUNDER_ARMOR,
    FD_PILLAR_SPAWN_BURST, FD_COLLAPSE_DUST, FD_COLLAPSE_DUST_ALT,
    IN_FIERY_BURST, IN_FIRE_STORM_CAST, IN_MAGMA_FIST, IN_MAGMA_FIST_RING, IN_LAVA_SURGE, IN_REBORN_AT_THE_ANVIL,
    IN_SHATTER_INTO_EMBERS, IN_CINDER_TOSS, IN_CRUSHING_FIST, IN_ARM_SWEEP, IN_FIRELORDS_BREATH, IN_LAVA_SPAWN_CLIMB,
    IN_CURSE, IN_FIRELORDS_WILL,
    BG_ROCKFALL, BG_BOULDER_MISSILE, BG_BOULDER_LAND, BG_BOULDER_MELT, BG_MOLTEN_FURNACE, BG_FISSURE_BURST,
    BG_MAGMA_SPLASH,
    AF_MOLE_DEPLOY, AF_MOLE_RETREAT, AF_COMMANDING_SHOUT, AF_COMMANDING_SHOUT_ALT, AF_IRON_GRENADE, AF_MEDIC_HEAL,
    AR_GOLEM_WAKES, AR_CHEMICAL_BOMB, AR_POISON_MIST, AR_LETHAL_ATTRACTION, AR_LIVEWIRE, AR_LIVEWIRE_ALT,
    AR_ARCANE_OVERCHARGE, AR_CHAIN_LIGHTNING, AR_SHOCK, AR_FLAMETHROWER, AR_INCINERATION,
    HU_DRINK, HU_LIQUID_COURAGE, HU_LAGER_BUZZ_FLASH, HU_TIPSY, HU_FLAME_BREATH, HU_BOTTLE_TOSS, HU_BOTTLE_TOSS_ALT,
    PH_THROW_OUT_GRAB, PH_THROW_OUT_FLIGHT, PH_THROW_OUT_LANDING, PH_LAST_CALL, PH_OUTRAGE, PH_THUNDERCLAP,
    PH_FIREBALL_VOLLEY,
    FL_PORTAL_ANCHOR_ALT, FL_KINDLING_STATE, FL_KINDLING_CHANNEL, FL_BURNING_SPIRIT_STACK, FL_FIRE_BLAST,
    TS_SHADE, TS_SHADE_FADE, TS_GATHER_DOOM_CAST, TS_GATHER_DOOM_LANDING, TS_FURIOUS_CHARGE, TS_SEETHING_COLD,
    TS_DOPEY_HAZE, TS_GLOOM_RELS_RECKLESSNESS, TS_VILE_COMMUNION, TS_CONE_OF_COLD, TS_BACKSTAB, TS_RUPTURE, TS_GOUGE,
    TS_MIND_BLAST, TS_IMMOLATE,
    MG_STATUE_GLOW, MG_CROSSFIRE_BREATH, MG_CROSSFIRE_END, MG_FIERY_BURST,
    EM_NEMESIS_BEAM, EM_NEMESIS_BEAM_ALT, EM_RADIANT_BURN, EM_TWILIGHT_TETHER, EM_FLAMESTRIKE_CAST, EM_FIRESTORM,
    EM_FIRESTORM_ALT, EM_HAMMER_SLAM_WINDUP, EM_HAMMER_SLAM_CRACK, EM_RAGNAROS_AWAKENS, EM_MAGMA_CLAP_RING,
    EM_MAGMA_CLAP_HIT, EM_VOLCANIC_BLAST, MO_FIRE_CAGE_WHIRL, EM_HAND_OF_THAURISSAN, EM_AVATAR_OF_FLAME, EM_FLAMES,
    MO_MIND_BLAST, MO_NECROSIS,
}))

STOCK_CREATURE_DISPLAYS = tuple(sorted({
    DISPLAY_INVISIBLE_STALKER, DISPLAY_LOOSED_EARTH, DISPLAY_KENNEL_HOUND,
    DISPLAY_KORV_TOTEM_HEALING, DISPLAY_KORV_TOTEM_SEARING, DISPLAY_KORV_TOTEM_EARTHBIND, DISPLAY_LEFTY,
    DISPLAY_MALGEN, DISPLAY_KORV, DISPLAY_VOLIDA, DISPLAY_THELDREN,
    DISPLAY_DEFILING_TOTEM, DISPLAY_FRANCLORN_SPIRIT, DISPLAY_VEREK, DISPLAY_STILGISS, DISPLAY_VAULT_SENTINEL,
    DISPLAY_EMBER_OF_INCENDIUS, DISPLAY_EMBER_ALT, DISPLAY_INCENDIUS_GIANT, DISPLAY_LAVA_SPAWN, DISPLAY_BAELGAR,
    DISPLAY_SQUAD_RESERVIST, DISPLAY_SQUAD_MEDIC, DISPLAY_SQUAD_OFFICER, DISPLAY_SQUAD_OFFICER_ALT,
    DISPLAY_ARCANE_ORB, DISPLAY_ARCANE_ORB_ALT, DISPLAY_TOXITRON, DISPLAY_ELECTRON, DISPLAY_ARCANOTON,
    DISPLAY_MAGMATRON,
    DISPLAY_ROWDY_PATRON, DISPLAY_ROWDY_PATRON_ALT, DISPLAY_PHALANX, DISPLAY_BURNING_SPIRIT, DISPLAY_FLAMELASH,
    DISPLAY_ANGERREL, DISPLAY_SEETHREL, DISPLAY_DOPEREL, DISPLAY_GLOOMREL, DISPLAY_VILEREL, DISPLAY_HATEREL,
    DISPLAY_DOOMREL, DISPLAY_IRONHAND_GUARDIAN, DISPLAY_MAGMUS,
    DISPLAY_IMPERIAL_GUARD, DISPLAY_IMPERIAL_GUARD_ALT, DISPLAY_TWILIGHT_AMBASSADOR, DISPLAY_AVATAR_OF_RAGNAROS,
    DISPLAY_MOIRA, DISPLAY_HIGH_PRIESTESS, DISPLAY_EMPEROR,
}))
STOCK_GAMEOBJECT_DISPLAYS = tuple(sorted({
    GODI_ARENA_BANNER, GODI_STUCK_AXE, GODI_SNAP_TRAP, GODI_SHODDY_PILLAR, GODI_SHODDY_PILLAR_ALT,
    GODI_GUZZLER_ROPE_PICKUP, GODI_HANGING_ROPE, GODI_FALLEN_BOULDER, GODI_FALLEN_BOULDER_ALT,
    GODI_FALLEN_BOULDER_ALT_2, GODI_MOLE_MACHINE, GODI_ACTIVATION_CONSOLE, GODI_FOURTH_PEDESTAL,
    GODI_FOURTH_PEDESTAL_ALT,
}))
