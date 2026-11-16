"""
Blackrock Spire build, WP-V-1 (wave 1: the Lower Spire, B1-B9): the visual ids the boss files use, one place (not
loaded on its own: the leading underscore keeps the package loader from treating it as a declaration file; boss files
import it with `from ._visuals import ...`, like `_common.py` and stratholme/_visuals.py). Created by V-1; V-2 appended
the wave 2 constants (the Upper Spire: Emberseer, Solakar, Rend and Gyth, the Beast, Drakkisath) at the end of each
section; no wave 1 value was changed. A boss WP asks for a change in its report.

Source: .agents/plans/blackrock-spire-build/blackrock-spire-build.VISUALS-REPORT.md (ids, kits, mesh bounds and
textures read; nothing rendered, so every look is unconfirmed until seen in game), the top pick of each wave 1 row
(handoff s3.10, s7 #27), with the look corrections of s3.10 applied: the constants below are the corrected ids, never
the build spec's originals where the spec's pick draws nothing or something else (the test pins the wrong ones out).

Three kinds of constant:

- MINTED (client patch-M, by apps/dbc-tools/patch_blackrock_spire_vfx_models.py, ids.yaml reservation
  `blackrock_spire`, spellvisual 90600-90649): the `SV_*` names in the first section. They must equal the patch
  script's constants of the same name (lib/test_blackrock_spire_vfx.py pins it). The two Wyrmthalak looks sit on
  Ascension models that ship into patch-M (`--extract` pulls them); wave 1 mints no GameObjectDisplayInfo,
  CreatureDisplayInfo or CreatureModelData row. Wave 2 (V-2) mints SV 90603-90616 (the held torch, the 6 yd shadowflame
  pool, the Beast's magma pool ladder, Drakkisath's two brands, the 12 yd ring of fire) and one creature display,
  the ice wall (90740); 90040-90049 stay free.
- SHIPPED (already in patch-M or the working copy): the telegraph kit displays (91000-93999) and the Deadmines goo
  puddle SV 90342/90343. Nothing ships for them; the test checks they exist in the working-copy DBCs.
- STOCK: ids that already exist in the 3.3.5 client. Nothing ships and no id is minted.

How to wire a SpellVisual: put the id in the custom spell's `SpellVisualID_1`. A STATE look plays on every unit that
carries the aura (so only put it on an aura, a stalker aura for a ground patch). An AREA look is for a spell with a
dynamic object (an area aura). An impact kit plays once, so a lasting effect re-casts it every 2-3 s or uses the
lasting twin named here. Names are `<boss code>_<what>`; boss codes: OM Omokk, VG Vosh'gajin, VO Voone, SW Smolderweb,
UR Urok, ZG Zigris, HG Halycon and Gizrul, WT Wyrmthalak (HM the hard mode: the horn, the champions' looks).
"""

# --- Minted (patch-M) -------------------------------------------------------------------------------------------------

# Wyrmthalak WT16 Shadowflame Spit patch (4 yd radius, 40 s): the Ascension `mannoroth_gooflowshadow_state_projected`
# (a 17.8 yd square purple quad, `defile1` + two radial blends) as a fixed-scale State on a stalker (one stalker per
# patch) or a PersistentArea for an area aura. The disc inside the quad is a guess: tune the one scale number.
SV_SPIT_PATCH_AREA = 90600
SV_SPIT_PATCH_STATE = 90601
# Wyrmthalak HM war horn blown: the stock Horn of Elemental Fury cast (sound 6423, anim 81, SV 4079) plus the Ascension
# `ogre_warhorn_impact_base` orange shock-ray burst as an impact on the caster. Cast it from a stalker at the horn
# (self-target); it has no missile.
SV_HORN_BLOWN = 90602

# --- Minted by V-2 (wave 2, the Upper Spire; every look unconfirmed until seen in game) --------------------------

# Solakar's held flame (SK4): a StateKit with the stock Torch (SVEN 3032, TorchSpell.mdx) in the RIGHT WEAPON slot, on
# the holder while the aura lasts. NEVER the stock Torch 55049 (SV 12075: flames at the feet, see the wrong list).
# Unconfirmed: whether a weapon-slot state shows on a player with a weapon equipped; the fallback is SK_HELD_FLAME_ALT.
SV_TORCH_HELD = 90603
# Rend and Gyth RG7 "Taste in my power" pool (6 yd radius, 20 s normal / 25 s heroic): the same Ascension shadow quad
# as WT16's spit patch at scale 0.7 (12.5 yd across). AREA is for an area aura's dynamic object, STATE for a stalker
# aura (one stalker per pool).
SV_SHADOWFLAME_POOL_AREA = 90604
SV_SHADOWFLAME_POOL_STATE = 90605
# The Beast's Molten Blood pool (BE3): the Ascension `magmazone` lava quad as a STATE on a stalker, minted at 1 yd rungs
# from 4 to 10 yd of visible radius (N 5 yd, H 4.5 yd, plus 0.5 yd per Heat stack with no cap: pick the smallest rung
# at or above the real radius, 10 is the top; a pool past 10 yd keeps the 10 look). Keyed by the rung radius in yd.
SV_MAGMA_POOL_STATE = {4: 90606, 5: 90607, 6: 90608, 7: 90609, 8: 90610, 9: 90611, 10: 90612}
MAGMA_POOL_RADII = tuple(sorted(SV_MAGMA_POOL_STATE))
# Drakkisath's brands (DR2, DR3): the Ascension Odyn runic brand states, a 3.8 yd rune ring under the bearer (a Base
# state with its own spawn anim). Orange is the Searing Brand (spread out), yellow the Collapsing Brand (pair up).
SV_BRAND_SEARING = 90613
SV_BRAND_COLLAPSING = 90614
# Drakkisath's ring of fire (DR17, 12 yd radius): the stock Flame Circle model (Ring of Flame 35831 uses it at scale 3
# for a 7 yd radius) at scale 5.14 with a fixed size. The STOCK pick is DR_RING_OF_FIRE (8386) with the dynamic object
# radius set to 12; use these only if the client does not scale the stock ring to the radius (needs eyes in game).
SV_RING_OF_FIRE_AREA = 90615
SV_RING_OF_FIRE_STATE = 90616
# Rend and Gyth RG6 frost wall: the Ascension `frostwhisper_icewall_base` as a creature display (CMD + CDI 90740, model
# scale 0.6: about 16 yd wide, 2.1 yd thick, 8 yd tall; the model's long axis is its local Y, so a creature facing the
# way the wall travels shows the wall across the path). One piece per creature: two pieces with an 8 yd gap. The
# creature stays an invisible hitbox carrier in function; the kit line is the real 4 yd band.
DISPLAY_ICE_WALL = 90740
ICE_WALL_YARDS_WIDE = 16.1

# --- Shipped (patch-M and the working copy) ---------------------------------------------------------------------------

# Omokk's crowd band (gap 6): the telegraph kit's red line at ladder step i = 48 (aspect 32, so a 64 yd piece for the
# 62 yd edge), fill layer and outline layer. The color index is red 0 (the get-out default), purple 3 is the rank 2.
OM_BAND_FILL_RED = 92048
OM_BAND_OUTLINE_RED = 93048
OM_BAND_FILL_PURPLE = 92348
OM_BAND_OUTLINE_PURPLE = 93348
# Halycon and Gizrul's Rabid Trail puddles (gap 14): the Deadmines Fish Stew goo, 4 yd radius, one every 8 yd along the
# lane (the 5 yd wide green kit line is the hitbox and fill and needs no id here).
SV_GOO_PUDDLE = 90342               # PersistentArea (an area aura)
SV_GOO_PUDDLE_STATE = 90343         # State (a stalker aura)

# --- Spells whose SpellVisual stands in for the cast (a copy of the stock visual id is all a spell needs) -------------

# Highlord Omokk (B1)
OM_CROWD_SHOVE = 1023               # Crowd Pummel 10887: a kick ring on the chest + sound; the knockback is the read
OM_HAYMAKER = 208                   # Haymaker 50084: anim + sound + shake only, no model (RISKY: the line marker and
                                    # the shake carry it)
OM_HAYMAKER_FLASH = 9766            # Axe Volley's Decisive Strike flash, ONLY as an optional hit flash on Haymaker's
                                    # victims; never as Voone's axe rain (no missile, see the wrong-looks list)
OM_PELTING = {39154: 8943, 39147: 8944, 39148: 8945, 39149: 8947, 39146: 8949, 39155: 8950}
                                    # the six real bottle spells -> SV (acid, tar, blood, frosty, orange juice, grape)
OM_FRENZY = 870                     # Frenzy 8269 (also Fixate, Rage, Frothing Rage): a roar flash, a stack is a flash
OM_THROW_ROCK = 1506                # Throw Rock 36645 (Boulder_Missile; Wyrmthalak's Boulders use it too)
OM_MOJO_MADNESS = 7306              # Mojo Madness 43712: yellow-orange hands + a 1.9 s burst (RISKY for the 15 s
                                    # Frenzy: re-cast every 3 s or pair it with OM_FRENZY)
OM_GROUND_SLAM = 8083               # Ground Slam 33525: a 3.5 yd radius crack + shake; the circle marker is the hit
OM_BELLY_FLOP = 12882               # Belly Flop 61115: the same at half size
OM_SHOULDER_CHARGE = 3783           # Shoulder Charge 31994 / Charge 22911: trail + dust; a StunSwirl state on an
                                    # aura target (a copy that applies an aura needs its own SV row: V-2 or a fix)

# Shadow Hunter Vosh'gajin (B2): the tells are settled (ruling 28); ids kept here for the boss file
VG_PUPPET_STRINGS = 13152           # Puppet Strings 62377: RopeBeam channel (thin)
VG_PIN = 5287                       # Pin 50245
VG_VOODOO_FLAMES = 11668            # Voodoo Flames 54795: fireforceshield_dark state (settled)
VG_NEEDLE_SPINE = 9061              # Needle Spine 39835
VG_NEEDLE_TELL = 11078              # Crystal Spike Pre-visual 50442: IceSpike_Impact_Base x2.0 (settled)
VG_SHADOW_PRISON = 8025             # Shadow Prison 33071 (Squeeze tell, settled)
VG_HEX = 2295                       # Hex 16097
VG_HEX_OF_AGONY = 10061             # Hex of Agony 52647: the skull is a 3 s impact; re-cast every 3 s over the 8 s
DISPLAY_VOODOO_DOLL = 25017         # ragdoll_02, the doll (settled)
# The stock impacts the resolve copies wear (voshgajin.py names them locally for now; the boss file switches to these)
VG_FIRE_BLAST_IMPACT = 143          # Fire Blast 2136: hands and a chest flash (the burst and patch hits)
VG_SHADOW_BURST_IMPACT = 45         # Shadow Burst 28447: a shadow burst on the chest (Squeeze, the hex burst)
VG_GORE_IMPACT = 39                 # Gore 4102 / Strike: a physical hit flash and a sound (the needle's hit)
VG_CURSE_OF_BLOOD_STATE = 876       # Curse of Blood 16098: the curse hands and a lasting state on the bound

# War Master Voone (B3)
VO_THROW_AXE = 3962                 # Throw Axe 16075 (missile_axe_copper); ALSO Axe Volley's rain, one per circle
VO_AXE_RAIN = 3962                  # the corrected Axe Volley 42357 look (SV 9766 has no missile)
VO_BERSERKER_CHARGE = 4259          # Berserker Charge 16636: trail + dust, no stun state
VO_BERSERKING = 6943                # Berserking 23505: red hands STATE
VO_HARPOON_CHAIN = 10920            # Skadi's Harpoon Chain 49679: iron chain channel (ruling 32; Wyrmthalak's too)
GODI_STUCK_AXE = 8494               # ORCAXE02, the stuck axe in the ground

# Mother Smolderweb (B4)
SW_MOTHERS_MILK = 854               # Mother's Milk 16468: goo missile + green burst
SW_CRYSTALLIZE = 4001               # Crystallize 16104: sparkles only, no cone (RISKY); the marker draws the cone
SW_HATCH_BURST = 4339               # Spawn Bile Slime 16809: a green gore burst on the ground, per egg and hatcher
SW_HATCH_BURST_ALT = 3999           # Hatch Spiderlings 43134: a cyan star flash (the doc's pick, runner-up)
SW_BROOD_CALL = 11329               # Hatch Eggs 58542 on her (shadow nova); SW_HATCH_BURST on each egg by a stalker
SW_VENOM = 2617                     # Venom Sting 5416: a LASTING poison state on the chest (Widow's Bite, Venom,
                                    # Rabies, Corrosive Poison); one state shows no stack count
GODI_SMOLDERWEB_EGG = 364           # SpiderEggSack04 (ruling 36)

# Urok Doomhowl (B5)
UR_SHARD_FLASH = 12205              # Power Spark 55845: a spark burst when the shard reaches Urok
UR_WILD_BOLT_MISSILE = 9947         # Arcane Barrage 44425: the missile (Arcane Bomb's SV 12302 has none)
UR_WILD_BOLT_MISSILE_ALT = 268      # Arcane Missile 7268
UR_WILD_BOLT_LANDING = 965          # Arcane Explosion 1449: the blue dome on landing
UR_OVERCHARGE_HIT = 8340            # Mana Bomb Explosion 35513: the nova for the 40% hit
UR_OVERCHARGE_CAST = 12303          # Arcane Overload 56432: the bubble on Urok through the 3 s cast
UR_DOOMHOWL = 247                   # Intimidating Roar 16508 / Terrifying Roar 14100: a ring + fear skulls on auras
UR_UNSTABLE_MAGIC = 969             # Unstable Magic 29900: a 2.5 s rune (RISKY for the 6 s fuse: re-cast every 2.5 s)
DISPLAY_POWER_SPARK = 26753         # the shard (Eye of Eternity Power Spark creature, display scale 2.0): unit_flags
                                    # not selectable; it floats (collision height 0)
DISPLAY_POWER_CRYSTAL = 17856       # runner-up: a blue crystal, no walk anim

# Quartermaster Zigris (B6)
ZG_NET = 3519                       # Hooked Net 13608: net missile + a lasting Net_State on the ground
ZG_MORTAR_SHELL = 3819              # Big Bronze Bomb 4067: a bronze bomb in flight + Bomb_ExplosionA on landing
ZG_MORTAR_SHELL_ALT = 8824          # Fire Bomb 31961
ZG_KEG_FUSE = 791                   # the Explosive Sheep detonation state: a fire spiral on a stalker at the keg
ZG_KEG_FUSE_ALT = 148               # Throw Dynamite 7978 from a stalker (RISKY: StunSwirl state on a unit it hits)
ZG_KEG_BLAST = 2899                 # Goblin Sapper Charge 13241: FireNova ring + Bomb_ExplosionA, shake
ZG_SMOKE_BOMB = 804                 # Smoke Bomb 7964: Fall Back smoke
ZG_DISENGAGE = 12305                # Disengage 781: the leap anim only (RISKY: the move is server side)
ZG_SHEEP_WINDUP = 88                # spell 4074: sound + anim 123; the blast is ZG_KEG_BLAST
ZG_SHEEP_FUSE = 791
GODI_SUPPLY_CRATE = 5271            # OrcCrate06
GODI_POWDER_KEG = 457               # Orcbarrel01
GODI_NET_TRAP = 7529                # G_BearTrap (open, trigger, close anims 145, 147, 148)
DISPLAY_CLOCKWORK_SHEEP = 3886      # Sheep with the SheepRobo skin

# Halycon and Gizrul (B7)
HG_SAVAGE_CHARGE = 5162             # Feral Charge - Bear 16979
HG_PACK_POUNCE = 12500              # Leap 57882
HG_MAUL = 166                       # Maul 6807: claw slash + gore
HG_THRASH = 7428                    # Whirlwind 26083: a small Cyclone_State (the ring marker carries the 8 yd)
HG_RABID_FROTH = 1903               # Disease Cloud 28362: green gore + ghost-flame state + a fog puff
HG_FURIOUS_HOWL = 518               # Furious Howl 3149: sound + anim
HG_FROTHING_RAGE = 870              # Frothing Rage 66759 (the Frenzy SV)
HG_PACK_FURY = 8581                 # Fire Shield 35265: CycloneFire_State, the LASTING 15 s look (the stock Bestial
                                    # Wrath SV 7278 is a one-shot head flash, never wired for a lasting buff)
HG_TORN_HIDE = 376                  # Bite 17253: a lasting blood state on the chest, re-cast per stack optional
HG_TORN_HIDE_ALT = 556              # Hamstring 1715: a 0.7 s blood puff, re-cast each stack
HG_RABID_TRAIL_ALT = 12431          # Plague Slime 50026: a smoke patch per cast (the runner-up; the goo is the pick)
HG_RABIES = 2617                    # the lasting poison state again (the stock Rabies SV 631 is a 3 s impact)

# Overlord Wyrmthalak (B8, B9)
WT_SHADOW_FLAME_BREATH = 6559       # Shadow Flame 22539: orange breath + a per-unit burn state (reads orange, RISKY)
WT_TAIL_SWEEP = 3879                # Tail Sweep 15847: anim + a small splat
WT_BOULDER = 1506                   # Boulder 9483 (the Throw Rock missile)
WT_AXE_FLURRY = 7163                # Axe Flurry 24018: a dust whirl channel (RISKY); alt WT_AXE_FLURRY_ALT
WT_AXE_FLURRY_ALT = 7428            # Whirlwind blade ribbons
WT_THROW_AXE = 3962                 # Throw Axe 16075
WT_CHARGE = 3783                    # Charge 22911: the worg riders (StunSwirl note as OM_SHOULDER_CHARGE)
WT_SHARD_FLASH = 12205              # Power Spark 55845 (the shard again, display DISPLAY_POWER_SPARK)
WT_HARPOON_CHAIN = 10920            # Skadi's Harpoon Chain 49679: axe and spear chains
WT_SPEAR_THROW = 11993              # Throw Spear 54617: the HumanSpear01 missile (Impale 48261's SV 10724 has none)
WT_CORROSIVE_POISON = 835           # Corrosive Poison 3396: one flash (RISKY); the lasting state is SW_VENOM
WT_CAUSTIC_ROAR = 4939              # Bellowing Roar 18431: sound + shake + a head fear impact
WT_SPIT_LANDING = 6700              # Shadow Flame 22972: an InstantArea dust + red glow burst at each circle
WT_SPIT_MISSILE = 64                # Shadow Bolt 686: purple hands and a dark bolt (cast from the breath point)
WT_HORN_CAST = 4079                 # Horn of Elemental Fury 56893: sound 6423 + anim 81 (SV_HORN_BLOWN adds a burst)
WT_OVERLORDS_FURY = 8581            # Fire Shield again: the permanent look on Wyrmthalak (the Bestial Wrath SV 7278
                                    # is a one-shot)
# Displays
DISPLAY_INVISIBLE_STALKER = 11686   # the mod-boss-mechanics stalker skin every kit helper wears (as Stratholme)
DISPLAY_SPIRESTONE_CHAMPION = 11582  # ogre, display scale 2.8, yellow skin (Spirestone Warlord's)
DISPLAY_SMOLDERTHORN_CHAMPION = 7803  # TrollDire black skin at 1.2 (Smolderthorn Berserker's)
DISPLAY_BLOODAXE_CHAMPION = 9602    # orc male at 1.2 (Bloodaxe Raider's)
DISPLAY_RIDING_DIRE_WOLF = 14334    # PvPRidingDireWolf, the Bloodaxe rider's mount (creature_template_addon.mount)
DISPLAY_RIDING_DIRE_WOLF_ALT = 2326  # RidingDireWolf, reddish brown (the Warsong Outrider's mount)
GODI_WAR_HORN = 7352                # elventowerSilithusHorn: 17.9 x 11.9 x 13.1 yd at size 1; stock uses size 0.35;
WAR_HORN_SIZE = 0.12                # "a horn on a post" is 0.1-0.15 in the gameobject template (unconfirmed in game)
GODI_WAR_HORN_ALT = 2371            # MargolReaverHorn, a small dwarven horn (1.4 x 1.4 x 1.8 yd)

# --- Wave 2: the Upper Spire (V-2) ------------------------------------------------------------------------------------

# Pyroguard Emberseer (B10)
EM_RING_LAUNCH = 13372              # Flame Wave 75413 (EM3): rune base + hands, a FireNova x4 shockwave; cast on a
                                    # stalker at the apex (RISKY, plausible launch flash)
EM_FIRE_NOVA = 6899                 # Fire Nova 23462: the ring burst, the runner-up launch look and the erupting posts
EM_SMOLDER = 10775                  # Smoldering Flames 48454 (EM6 post smolder): a lasting Base state on a stalker
EM_SMOLDER_ALT = 9112               # Immolation 40148: embers and smoke state (also DR_SEARED_FLESH)
EM_FLARE_COLUMN = 9727              # Pillar of Fire 43541 (EM6 flare column): a 6 s ONE-SHOT, re-cast at 5 s
EM_FLARE_COLUMN_ALT = 7251          # Spawn - Red Lightning 24240: red columns, 4 s, about 30 yd tall (re-cast at 3 s)
EM_SEARING_BOND = 1946              # Burning Brand 29618 (EM7 holder): StateKit 235, a LASTING flame state
EM_SEARING_BOND_ALT = 945           # Searing Pain 5676: a 1.1 s impact, re-cast every second (the doc's pick)
EM_SEARED = 6764                    # Fire Reflector 23097 (the 40 s Seared debuff): lasting red ribbons on the chest
EM_ENCAGE = 3943                    # Encage Emberseer 15281: the post beam (ManaBeam from the caster's left hand: the
                                    # post stalker's attach is unchecked) and the state on the target
EM_GROWING = 3947                   # Emberseer Growing 16049: a glow star and smoke puff at the base
EM_SUPERNOVA = 3944                 # Emberseer Full Strength 16047: a blue arcane dome + fire ring (off-tone, stock)
EM_PYROBLAST = 2253                 # Pyroblast 17274: the stock missile and molten impact

# Solakar Flamewreath (B11)
SK_HELD_FLAME_ALT = 8581            # Fire Shield 35265: a flame whirl at the holder's base (fallback if SV_TORCH_HELD
                                    # shows nothing); NEVER 12075 Torch 55049 (flames at the feet, see the wrong list)
SK_TORCH_TOSS = 10211               # Torch Toss 45732 (SK5): the 0.8 yd torch missile with a flame
SK_TORCH_CATCH = 10302              # Torch Toss (land) 46054 (SK6): a base fire flash on the catcher (1.9 s)
SK_EGG_HATCH_CAST = 4204            # Hatch Rookery Egg 15746: the Hatchers' own cast (caster hands only; nothing shows
                                    # at an egg that hatches from a catch, use SK_EGG_HATCH_BURST there)
SK_EGG_HATCH_BURST = 3947           # Emberseer Growing 16049: a smoke puff at the egg (the green SW_HATCH_BURST is the
                                    # spider look); cast from a stalker at each egg
SK_FLAME_WREATH = 4101              # Flame Wreath 29947 (SK8): one flame state at his base; a stack is the buff icon
SK_HUNT_ROAR = 4939                 # Bellowing Roar 18431 (SK9): sound + anim 74 + shake (= WT_CAUSTIC_ROAR)
SK_WAR_STOMP = 2355                 # War Stomp 16727 (both stomps): a 6.9 yd crack; StunSwirl leaks on auras
SK_SPEAR_THROW = 11993              # Throw Spear 54617 (SK11): the HumanSpear01 missile (never 8855 / 10724)
SK_SPEAR_THROW_ALT = 12689          # Throw Harpoon 59633: a heavy harpoon missile
SK_SPEAR_WOUND = 376                # Bite 17253: a lasting blood state on the wounded (the Torn Hide look)
SK_SPEAR_WOUND_ALT = 121            # Deep Wound 43104: a 0.7 s puff, re-cast every second
SK_SPEAR_CLEANSE = 12765            # Cauterize 60211: fire hands, a flame burst and a dispel ring at the base
DISPLAY_FLAME_WHELP = 397           # DragonWhelp black skin at 1.5 (the Rookery Whelp; the flame whelp copy keeps it)

# Warchief Rend Blackhand and Gyth (B12)
RG_FLAME_BREATH = 1483              # Flame Breath 16390 (Mark of Rend cone, riderless breath)
RG_WHIRLWIND = 8377                 # Whirlwind 13736 (RG11): a small dust whirl state
RG_SHADOW_FLAME_HIT = 6559          # Shadow Flame 22539 (RG7 hit, as Wyrmthalak): orange, not black (RISKY)
RG_SHADOWFLAME_RAIN = 6700          # Shadow Flame 22972: a dust + red glow burst at each circle (= WT_SPIT_LANDING)
RG_SHADOWFLAME_RAIN_ALT = 11247     # Shadowflame 47960: a chest impact (the doc's pick, a small state)
RG_FREEZING_BREATH_CAST = 10569     # Freezing Breath 47415: ONLY Gyth's breath cast, never the wall (it is a breath)
RG_FROST_WALL_SPIKE = 11078         # fallback wall: a row of 8-10 stalkers at 4.5 yd each wearing the Vosh needle tell
RG_THUMBS_DOWN_SKULL = 90506        # Keening skull State (shipped, Stratholme): a lasting head state
RG_THUMBS_DOWN_SKULL_ALT = 10061    # Hex of Agony 52647: a 3 s skull (re-cast every 3 s)
RG_THUMBS_DOWN_HIT = 13549          # Shadow Crash 62660: hand glows + a dark missile on the landing
RG_REND_MOUNTS = 653                # Rend Mounts 16167: a nature precast + a smoke puff (the model swap is the aura)
DISPLAY_BATTLE_STANDARD = 14542     # BattleStandard_Horde.mdx (4.4 x 4.4 x 11.2 yd at scale 1), our Skull Banner's
BANNER_DISPLAY_SCALE = 0.4          # creature scale for the Banner of the Dark Horde (a 4.5 yd tall flag; a guess)
GODI_HORDE_BANNER = 5111            # HordeBanner03: the fallback plant visual, not attackable

# The Beast (B13)
BE_ROAR = 247                       # Terrifying Roar 14100 (Dread): a small ring + fear skulls on aura targets
BE_MAGMA_SPLIT = 4321               # Flamebreak 16785: fire hands, a FireNova ring, an InstantArea fire spiral (the
                                    # spiral's width at the radius is unconfirmed)
BE_HEAT = 8581                      # Fire Shield 35265: the CycloneFire_State flame whirl, the LASTING Heat look
BE_HEAT_ALT = 3946                  # Emberseer Growing 16048: the same state (the stock growth aura)
BE_HEAT_STACK_FLASH = 1465          # Lava Shield 21858: a 1.5 s chest flash, ONLY as the flash at each new stack
GODI_FLAME_CIRCLE = 410             # FlameCircle.mdx (5.5 x 5.6 yd ring of flame sprites): the fallback pool object
                                    # (gameobject `size` about 1.8 for 5 yd)

# General Drakkisath (B14, B15)
DR_SEARING_BRAND_ALT = 1946         # Burning Brand 29618: lasting flame licks (stock runner-up)
DR_COLLAPSING_BRAND_ALT = 6764      # Fire Reflector 23097: lasting red ribbons (stock twin)
DR_COLLAPSING_FLASH = 3479          # Mark of Flames 15128: a 3 s ribbon IMPACT only; never as the 12 s brand look
DR_THUNDERCLAP = 145                # Thunderclap 15548: a 6.9 yd ground crack + blue hands + a slow state
DR_FLAMESTRIKE = 10383              # Flamestrike 16419 (the 5 yd patches): a PersistentArea fire spiral
DR_SWEEP = 399                      # Wide Swipe 6749 (Sweeps, Cleaving Charge): anim + sound + shake, no model; a
                                    # StunSwirl state leaks on aura targets (a copy that applies an aura needs a row)
DR_SWEEP_ALT = 166                  # Maul 6807: a claw slash model at the base
DR_CHALLENGE_CIRCLE = 143           # Fire Blast 2136: hands + a chest flash (the circle marker is the ground)
DR_FIREBALL_VOLLEY = 2437           # Fireball Volley 15285 (Fire Tongues): Fireball missile + impact
DR_CONFLAGRATION = 4326             # Conflagration 16805: dragon breath + fire impact (retired, look kept)
DR_RING_OF_FIRE = 8386              # Ring of Flame 35831: PersistentArea FlameCircleEffect x3 (radius 7 in stock): set
                                    # the dynamic object radius to 12 (the scaling is untested; fall back to the
                                    # minted SV_RING_OF_FIRE_AREA / STATE)
DR_RING_OF_FIRE_ALT = 10398         # Flame Wreath 29946: the same model at x1.35 (radius 3 in stock)
DR_FINESSE = 8996                   # Adrenaline Rush 13750: a lasting base glow on the challenger
DR_FINESSE_ALT = 72                 # Evasion 5277
DR_HUMBLED = 210                    # Demoralizing Shout 1160: a base ring + a squiggle over the head
EMOTE_STATE_KNEEL = 68              # the server kneel emote state on the boss with DR_HUMBLED (SharedDefines.h)
DR_CAPTAIN_COMMAND = 246            # Battle Shout 6673: a ring at the Captain; re-cast every 5 s (the 10 yd is the kit)
DR_CAPTAIN_COMMAND_ALT = 5139       # Concentration Aura 19746
DR_SEARED_FLESH = 9112              # Immolation 40148: charred embers and smoke on the tank (lasting)
DISPLAY_BLACK_DRAKONID = 14885      # DragonFootSoldier black skin: the herald (DR11)
DISPLAY_DEATH_TALON_HATCHER = 12892  # DragonSpawnCaster black skin at 1.75: the herald runner-up

# Every stock SpellVisual id above (the SpellVisual existence check).
STOCK_SPELL_VISUALS = tuple(sorted({
    OM_CROWD_SHOVE, OM_HAYMAKER, OM_HAYMAKER_FLASH, *OM_PELTING.values(), OM_FRENZY, OM_THROW_ROCK, OM_MOJO_MADNESS,
    OM_GROUND_SLAM, OM_BELLY_FLOP, OM_SHOULDER_CHARGE,
    VG_PUPPET_STRINGS, VG_PIN, VG_VOODOO_FLAMES, VG_NEEDLE_SPINE, VG_NEEDLE_TELL, VG_SHADOW_PRISON, VG_HEX,
    VG_HEX_OF_AGONY, VG_FIRE_BLAST_IMPACT, VG_SHADOW_BURST_IMPACT, VG_GORE_IMPACT, VG_CURSE_OF_BLOOD_STATE,
    VO_THROW_AXE, VO_BERSERKER_CHARGE, VO_BERSERKING, VO_HARPOON_CHAIN,
    SW_MOTHERS_MILK, SW_CRYSTALLIZE, SW_HATCH_BURST, SW_HATCH_BURST_ALT, SW_BROOD_CALL, SW_VENOM,
    UR_SHARD_FLASH, UR_WILD_BOLT_MISSILE, UR_WILD_BOLT_MISSILE_ALT, UR_WILD_BOLT_LANDING, UR_OVERCHARGE_HIT,
    UR_OVERCHARGE_CAST, UR_DOOMHOWL, UR_UNSTABLE_MAGIC,
    ZG_NET, ZG_MORTAR_SHELL, ZG_MORTAR_SHELL_ALT, ZG_KEG_FUSE, ZG_KEG_FUSE_ALT, ZG_KEG_BLAST, ZG_SMOKE_BOMB,
    ZG_DISENGAGE, ZG_SHEEP_WINDUP,
    HG_SAVAGE_CHARGE, HG_PACK_POUNCE, HG_MAUL, HG_THRASH, HG_RABID_FROTH, HG_FURIOUS_HOWL, HG_FROTHING_RAGE,
    HG_PACK_FURY, HG_TORN_HIDE, HG_TORN_HIDE_ALT, HG_RABID_TRAIL_ALT, HG_RABIES,
    WT_SHADOW_FLAME_BREATH, WT_TAIL_SWEEP, WT_BOULDER, WT_AXE_FLURRY, WT_AXE_FLURRY_ALT, WT_THROW_AXE, WT_CHARGE,
    WT_SHARD_FLASH, WT_HARPOON_CHAIN, WT_SPEAR_THROW, WT_CORROSIVE_POISON, WT_CAUSTIC_ROAR, WT_SPIT_LANDING,
    WT_SPIT_MISSILE, WT_HORN_CAST, WT_OVERLORDS_FURY,
    EM_RING_LAUNCH, EM_FIRE_NOVA, EM_SMOLDER, EM_SMOLDER_ALT, EM_FLARE_COLUMN, EM_FLARE_COLUMN_ALT, EM_SEARING_BOND,
    EM_SEARING_BOND_ALT, EM_SEARED, EM_ENCAGE, EM_GROWING, EM_SUPERNOVA, EM_PYROBLAST,
    SK_HELD_FLAME_ALT, SK_TORCH_TOSS, SK_TORCH_CATCH, SK_EGG_HATCH_CAST, SK_EGG_HATCH_BURST, SK_FLAME_WREATH,
    SK_HUNT_ROAR, SK_WAR_STOMP, SK_SPEAR_THROW, SK_SPEAR_THROW_ALT, SK_SPEAR_WOUND, SK_SPEAR_WOUND_ALT,
    SK_SPEAR_CLEANSE,
    RG_FLAME_BREATH, RG_WHIRLWIND, RG_SHADOW_FLAME_HIT, RG_SHADOWFLAME_RAIN, RG_SHADOWFLAME_RAIN_ALT,
    RG_FREEZING_BREATH_CAST, RG_FROST_WALL_SPIKE, RG_THUMBS_DOWN_SKULL_ALT, RG_THUMBS_DOWN_HIT, RG_REND_MOUNTS,
    BE_ROAR, BE_MAGMA_SPLIT, BE_HEAT, BE_HEAT_ALT, BE_HEAT_STACK_FLASH,
    DR_SEARING_BRAND_ALT, DR_COLLAPSING_BRAND_ALT, DR_COLLAPSING_FLASH, DR_THUNDERCLAP, DR_FLAMESTRIKE, DR_SWEEP,
    DR_SWEEP_ALT, DR_CHALLENGE_CIRCLE, DR_FIREBALL_VOLLEY, DR_CONFLAGRATION, DR_RING_OF_FIRE, DR_RING_OF_FIRE_ALT,
    DR_FINESSE, DR_FINESSE_ALT, DR_HUMBLED, DR_CAPTAIN_COMMAND, DR_CAPTAIN_COMMAND_ALT, DR_SEARED_FLESH,
}))

# Minted by this work (checked against the patch script's rows, not the stock DBCs)
MINTED_SPELL_VISUALS = (
    SV_SPIT_PATCH_AREA, SV_SPIT_PATCH_STATE, SV_HORN_BLOWN,
    SV_TORCH_HELD, SV_SHADOWFLAME_POOL_AREA, SV_SHADOWFLAME_POOL_STATE, *SV_MAGMA_POOL_STATE.values(),
    SV_BRAND_SEARING, SV_BRAND_COLLAPSING, SV_RING_OF_FIRE_AREA, SV_RING_OF_FIRE_STATE,
)
# Minted creature displays (CreatureDisplayInfo + CreatureModelData rows of the patch script)
MINTED_CREATURE_DISPLAYS = (DISPLAY_ICE_WALL,)
# Not in the stock client but already shipped (the Deadmines goo rows, Stratholme's keening skull)
MINTED_ELSEWHERE_SPELL_VISUALS = (SV_GOO_PUDDLE, SV_GOO_PUDDLE_STATE, RG_THUMBS_DOWN_SKULL)
# Shipped telegraph kit displays (CreatureDisplayInfo ids in the working copy)
SHIPPED_CREATURE_DISPLAYS = (OM_BAND_FILL_RED, OM_BAND_OUTLINE_RED, OM_BAND_FILL_PURPLE, OM_BAND_OUTLINE_PURPLE)

STOCK_CREATURE_DISPLAYS = tuple(sorted({
    DISPLAY_VOODOO_DOLL, DISPLAY_POWER_SPARK, DISPLAY_POWER_CRYSTAL, DISPLAY_CLOCKWORK_SHEEP,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_SPIRESTONE_CHAMPION, DISPLAY_SMOLDERTHORN_CHAMPION, DISPLAY_BLOODAXE_CHAMPION,
    DISPLAY_RIDING_DIRE_WOLF, DISPLAY_RIDING_DIRE_WOLF_ALT,
    DISPLAY_FLAME_WHELP, DISPLAY_BATTLE_STANDARD, DISPLAY_BLACK_DRAKONID, DISPLAY_DEATH_TALON_HATCHER,
}))
STOCK_GAMEOBJECT_DISPLAYS = tuple(sorted({
    GODI_STUCK_AXE, GODI_SMOLDERWEB_EGG, GODI_SUPPLY_CRATE, GODI_POWDER_KEG, GODI_NET_TRAP, GODI_WAR_HORN,
    GODI_WAR_HORN_ALT, GODI_HORDE_BANNER, GODI_FLAME_CIRCLE,
}))
# The sounds the picks use are inside the stock kits (6423 is Horn of Elemental Fury's); none is wired by id here.
STOCK_SOUND_ENTRIES = (6423,)
