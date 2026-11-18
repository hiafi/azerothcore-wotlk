"""
Blackrock Depths build WP-D5: the Ring of Law's six champions (9027-9032), Anub'shiah's Risen beasts (300782-300787) and
the Risen Champion (300788) (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D5; build
spec docs/dungeons/blackrock-depths-1-detention-block.md S1 "Champion: ..." sections and the Ring's Build spec rows
CH1, GO1-GO2, GZ1-GZ3, EV1-EV3, OK1-OK3, AN1-AN3, HE1-HE2). WP-D5 owns this file (its spells: kSpellsRingChampions
210870-210959 of modules/mod-dungeon-bosses src/BlackrockDepths/BlackrockDepthsRework.h; RingChampionsLogic.h names the
same ids; Grizzle's text and Hedrum's template addon are the core SQL rev rev_ring_champions_blackrock_depths.sql).
Binding these entries goes with BrdRingChampions::kBound = true in the same change (lib/test_blackrock_depths_
ring_champions.py pins the two; the champions have no SmartAI rows to drop).

- The six champions: bound to boss_ring_champions_rework.cpp's AIs (the stock boss_* BossAI scripts unbound), 90k
  normal (HealthModifier 37.959 on the warriors' 2,371, 47.443 on the paladins' 1,897), the stock DamageModifier 7.5,
  the kit's stun immunity set 1972 (stock -251: S1 "stun immune"; 1972 keeps silences and kicks working), no
  INSTANCE_BIND (the Ring's credit 230 is Grimstone's).
  Heroic 150k is WP-H's (source/world/dungeons/blackrock_depths.py).
- 300782-300787 Risen beasts (AN1): one per wave type in the stock RingMobs order (worm, stinger, screecher,
  thundersnout, creeper, beetle), the wave mob's stock display, undead, level 51, 6k (heroic 10k: WP-H's lock lines
  310393-310398), weak melee, no loot or XP; npc_brd_risen_beast.
- 300788 Risen Champion (AN1 heroic): the fallen challenger's display (set by the script at the summon; Gorosh's here),
  level 52 elite, 40k heroic (lock line 310399); npc_brd_risen_champion.

Spells (looks from ._visuals, WP-V-1's CH_* / GO_* / GZ_* / EV_* / OK_* / AN_* / HE_* picks; every look unconfirmed
until seen in game): 210870-210923 as RingChampionsLogic.h lists them (CH1 210870-210872, GO 210873-210881, GZ
210882-210891, EV 210892-210898, OK 210899-210903, AN 210904-210913, HE 210914-210923); 210924-210959 spare.

Kept stock (no rescale in S1): Mortal Strike 15708, Bloodlust 21049, Arcane Bolt 13748, Shadow Bolt 15472, Demon Armor
13787. Retired (never cast by the reworked scripts): Whirlwind 15589, Ground Tremor 6524, Frenzy 8269, Anti-Magic Shield
7121, Vicious Rend 14331, Arcane Explosion 1467, Polymorph 15534, Slow 19137, Curse of Tongues 15470, Curse of Weakness
12493, Enveloping Web 15471, Paralyzing Poison 3609, Baneful Poison 15475, Web Explosion 15474, Hate to Zero 13767,
Shadow Bolt Volley 15245. Gorosh's stuck axe is Blackrock Spire's Stuck Axe gameobject 301250 (display 8494,
GODI_STUCK_AXE), reused as is.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    TARGET_UNIT_TARGET_ENEMY,
    cast_bar,
    kit_creature,
    self_visual,
    standing_in_it,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_MONSTER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    AN_RAISE_DEAD,
    AN_WEB_PATCH,
    AN_WEB_SPIT,
    CH_TITLE_HOLDER,
    CH_TITLE_HOLDER_FLASH,
    EV_DEVOURED_MAGIC,
    EV_OPEN_WOUNDS,
    EV_SPELL_EATER,
    GO_DERVISH_DANCE,
    GO_RETURNING_AXE,
    GO_RETURNING_AXE_LINE,
    GZ_BULL_RUSH,
    GZ_DAZED,
    GZ_EARTHSHAKER_STOMP,
    GZ_KILLING_FRENZY_FLASH,
    GZ_WALL_IMPACT,
    HE_BANEFUL_BURST,
    HE_REEL_IN,
    HE_WEB_STRAND_PATCH,
    HE_WEB_STRANDS,
    OK_ARCANE_RUPTURE,
    OK_SHEEP_BOLT,
    RL_RAISED,
)

_D5 = 'Blackrock Depths build WP-D5 (the Ring of Law: the champions)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')
_SCRIPT_VALUE = 'Blackrock Depths: the script sets the hit per player (DungeonKit::RefFlatOn, CastCustomSpell)'

# --- constants (RingChampionsLogic.h; lib/test_blackrock_depths_ring_champions.py pins each against the header) -------

WARRIOR_HEALTH_MODIFIER = 37.959    # kWarriorHealthModifier: ceil(2,371 x 37.959) = 90,001
PALADIN_HEALTH_MODIFIER = 47.443    # kPaladinHealthModifier: ceil(1,897 x 47.443) = 90,000
CHAMPION_DAMAGE_MODIFIER = 7.5      # kChampionDamageModifier (stock)
# entry: (script, HealthModifier)
CHAMPIONS = {
    9027: ('boss_gorosh_the_dervish_rework', WARRIOR_HEALTH_MODIFIER),
    9028: ('boss_grizzle_rework', WARRIOR_HEALTH_MODIFIER),
    9029: ('boss_eviscerator_rework', PALADIN_HEALTH_MODIFIER),
    9030: ('boss_okthor_rework', PALADIN_HEALTH_MODIFIER),
    9031: ('boss_anubshiah_rework', PALADIN_HEALTH_MODIFIER),
    9032: ('boss_hedrum_rework', WARRIOR_HEALTH_MODIFIER),
}
RISEN_HEALTH_MODIFIER = 2.617801            # kRisenHealthModifier: ceil(2,292 x 2.617801) = 6,000
RISEN_CHAMPION_HEALTH_MODIFIER = 10.122     # kRisenChampionHealthModifier: 2,371 x 10.122 = 24,000 (never on normal)
RISEN_LEVEL = 51
RISEN_CHAMPION_LEVEL = 52
TITLE_HOLDER_PCT = 10           # kTitleHolderDamagePct
DANCE_LOOK_MS = 4000            # the whirl's look (removed by the script on arrival)
AXE_THROW_SPEED = 20.0          # kAxeThrowSpeed
AXE_RETURN_SPEED = 25.0         # kAxeReturnSpeed
AXE_CHAIN_MS = 8000             # the shown + locked lines (6 s) with a margin; the script interrupts it
RUSH_LOOK_MS = 3000
DAZED_MS = 4000                 # kDazedMs
DAZED_TAKEN_PCT = 30            # kDazedDamageTakenPct
STOMP_WARN_MS = 2500            # kStompWarnMs
STOMP_STUN_MS = 2000            # kStompStunMs
FRENZY_PCT = 10                 # kFrenzyPctPerStack
FRENZY_CAP = 50                 # kFrenzyCapHeroic (the script caps normal at 5)
SPELL_EATER_MS = 8000           # kSpellEaterMs
DEVOURED_CAP = 15               # kDevouredCap
OPEN_WOUNDS = (200, 200)        # kOpenWoundsPct 2 / 2 (hundredths), per 3 s tick
OPEN_WOUNDS_TICK_MS = 3000      # kOpenWoundsTickMs
OPEN_WOUNDS_MS = 15000          # kOpenWoundsMs
VOLLEY = (1000, 1500)           # kVolleyPct 10 / 15 (hundredths)
VOLLEY_CAST_MS = 3000           # kVolleyCastMs
VOLLEY_RADIUS = 30.0            # kVolleyRadius
RUPTURE_CAST_MS = 3000          # kRuptureCastMs
SHEEP_MS = 2000                 # kSheepPolyMs
SLOW_MS = 8000                  # kSlowMs
SLOW_MOVE_PCT = 60              # kSlowMovePct
SLOW_HASTE_PCT = 55             # kSlowHastePct
RAISE_CAST_MS = 2000            # kRaiseCastMs
WEB_ROOT_MS = 2000              # kWebRootMs
WEB_PATCH_MS = 20000            # kWebPatchMs
WEB_SLOW_PCT = 50               # kWebPatchSlowPct
WEB_SPIT_SPEED = 25.0           # kWebSpitSpeed
CURSE_MS = 15000                # kCurseMs
TONGUES_PCT = 50                # kTonguesCastPct
WEAKNESS_PCT = 20               # kWeaknessPhysicalPct
STRANDS_WARN_MS = 2000          # kStrandsWarnMs
STRANDS_ROOT_MS = 2000          # kStrandsRootMs
STRANDS_SLOW_PCT = 30           # kStrandsSlowPct
STRANDS_LIFE_MS = 30000         # kStrandsLifeMs heroic (the patches' looks; their stalkers despawn on time)
REEL_LOOK_MS = 2000
BANEFUL = (200, 200)            # kBurstPoisonPct 2 / 2 (hundredths), per 1 s tick, 8 s
BANEFUL_TICK_MS = 1000          # kBurstPoisonTickMs
BANEFUL_MS = 8000               # kBurstPoisonMs

# Risen entries in the stock RingMobs order (RingChampionsLogic.h RisenEntry; BlackrockDepthsRework.h): entry: (name,
# the wave mob's stock display (creature_template_model idx 0) [db], heroic lock line (STAGE-H-REPORT s3)).
RISEN = {
    300782: ('Risen Dredge Worm', 8182, 310393),
    300783: ('Risen Deep Stinger', 7347, 310394),
    300784: ('Risen Dark Screecher', 1955, 310395),
    300785: ('Risen Thundersnout', 8184, 310396),
    300786: ('Risen Cave Creeper', 8014, 310397),
    300787: ('Risen Borer Beetle', 7470, 310398),
}
RISEN_CHAMPION = 300788
RISEN_CHAMPION_HEROIC = 310399
DISPLAY_GOROSH = 8760           # the Risen Champion's template display (the script sets the fallen challenger's)

_FLAGS_EXTRA_NO_XP = 0x40
_CREATURE_TYPE_UNDEAD = 6
_DISPEL_MAGIC = 1
_DISPEL_CURSE = 2
_DISPEL_POISON = 4
_DISPEL_ENRAGE = 9
_MECHANIC_ROOT = 7
_MECHANIC_SNARE = 11
_MECHANIC_STUN = 12
_MECHANIC_BLEED = 15
_MECHANIC_POLYMORPH = 17
_SHEEP_ENTRY = 16372            # Polymorph 118's TRANSFORM creature (sheep)
_SCHOOL_MASK_ALL = 127
_SCHOOL_MASK_PHYSICAL = 1
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SPELL_INTERRUPT_FLAGS_KICK = 15
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_SUPPRESS_TARGET_PROCS = 0x00020000
_ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x00000001

# Stock icons (Spell.dbc SpellIconID of the named spell; unverified ones fall back to the generic icon in game)
_ICON_STRENGTH_OF_THE_CHAMPION = 566    # Strength of the Champion 16916 (Title Holder; D4's Crowd Favor)
_ICON_WHIRLWIND = 83                    # Whirlwind
_ICON_THROW_AXE = 1316                  # Throw Axe 16075
_ICON_CHARGE = 457                      # Bull Rush 4083
_ICON_DAZED = 15                        # Dazed 1604
_ICON_WAR_STOMP = 1027                  # War Stomp 45
_ICON_FRENZY = 456                      # Frenzy (Grebmar's)
_ICON_ANTI_MAGIC_SHELL = 2006           # Anti-Magic Shield 7121
_ICON_SHADOW_NOVA = 1960                # Shadow Nova 30852
_ICON_REND = 245                        # Rend (Grebmar's)
_ICON_SHADOW_BOLT_VOLLEY = 213          # Shadow Bolt Volley 15245
_ICON_ARCANE_EXPLOSION = 168            # Arcane Explosion 1467
_ICON_POLYMORPH = 136                   # Polymorph 118
_ICON_SLOW = 27                         # Slow 246
_ICON_RAISE_DEAD = 221                  # Raise Dead 17475
_ICON_WEB = 39                          # Web 745
_ICON_CURSE_OF_TONGUES = 692            # Curse of Tongues 15470
_ICON_CURSE_OF_WEAKNESS = 543           # Curse of Weakness 12493
_ICON_WEB_SPRAY = 3014                  # Web Spray 29484
_ICON_WEB_WRAP = 2747                   # Web Wrap 28622
_ICON_POISON_NOVA = 2894                # Poison Nova 55081

# --- the bindings -----------------------------------------------------------------------------------------------------

for _entry, (_script, _modifier) in CHAMPIONS.items():
    creature_template_columns(_entry, **boss_columns(_script, _modifier, damage_modifier=CHAMPION_DAMAGE_MODIFIER,
                                                     instance_bind=False))


# --- the Risen (AN1) --------------------------------------------------------------------------------------------------

def _risen_columns(script: str, level: int, rank: int, health_modifier: float, damage_modifier: float,
                   heroic: int) -> dict:
    """A Risen add: the Ring's monster faction (14, as the champions), undead, no loot or XP, its own AI."""
    return {
        **kit_creature(faction=FACTION_MONSTER, type=_CREATURE_TYPE_UNDEAD), 'minlevel': level, 'maxlevel': level,
        'rank': rank, 'unit_class': 1, 'unit_flags': 0, 'HealthModifier': health_modifier,
        'DamageModifier': damage_modifier, 'BaseAttackTime': 2000, 'detection_range': 20.0,
        'CreatureImmunitiesId': 0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': script, 'difficulty_entry_1': heroic,
    }


# The entries are written as numbers: source/world/dungeons/blackrock_depths.py finds the declared kit adds by the
# pattern `creature_template(<entry>, ...)` (WP-H) and gives them their heroic health (10k, the Risen Champion 40k).
risen_worm_300782 = creature_template(300782, 'Risen Dredge Worm', **_risen_columns(
    'npc_brd_risen_beast', RISEN_LEVEL, 0, RISEN_HEALTH_MODIFIER, 1.0, RISEN[300782][2]))
risen_stinger_300783 = creature_template(300783, 'Risen Deep Stinger', **_risen_columns(
    'npc_brd_risen_beast', RISEN_LEVEL, 0, RISEN_HEALTH_MODIFIER, 1.0, RISEN[300783][2]))
risen_screecher_300784 = creature_template(300784, 'Risen Dark Screecher', **_risen_columns(
    'npc_brd_risen_beast', RISEN_LEVEL, 0, RISEN_HEALTH_MODIFIER, 1.0, RISEN[300784][2]))
risen_thundersnout_300785 = creature_template(300785, 'Risen Thundersnout', **_risen_columns(
    'npc_brd_risen_beast', RISEN_LEVEL, 0, RISEN_HEALTH_MODIFIER, 1.0, RISEN[300785][2]))
risen_creeper_300786 = creature_template(300786, 'Risen Cave Creeper', **_risen_columns(
    'npc_brd_risen_beast', RISEN_LEVEL, 0, RISEN_HEALTH_MODIFIER, 1.0, RISEN[300786][2]))
risen_beetle_300787 = creature_template(300787, 'Risen Borer Beetle', **_risen_columns(
    'npc_brd_risen_beast', RISEN_LEVEL, 0, RISEN_HEALTH_MODIFIER, 1.0, RISEN[300787][2]))
for _entry, (_name, _display, _heroic) in RISEN.items():
    creature_model(_entry, display_id=_display)

risen_champion_300788 = creature_template(300788, 'Risen Champion', **_risen_columns(
    'npc_brd_risen_champion', RISEN_CHAMPION_LEVEL, 1, RISEN_CHAMPION_HEALTH_MODIFIER, 3.0, RISEN_CHAMPION_HEROIC))
creature_model(RISEN_CHAMPION, display_id=DISPLAY_GOROSH)


# --- helpers ----------------------------------------------------------------------------------------------------------

def _aura(spell_id: int, name: str, effects: list[dict], *, duration_ms: int, debuff: bool, icon: int, desc: str,
          aura_desc: str, notes: str, stacks: int = 0, visual: int = 0, school: School = School.NORMAL,
          mechanic: int = 0, dispel: int = 0, target: int = TARGET_UNIT_TARGET_ANY):
    """An aura the script applies (triggered); every effect an APPLY_AURA on `target`; dropped on a map change."""
    raw = kit_raw(desc, aura_desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                  AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP)
    if stacks:
        raw['CumulativeAura'] = stacks
    if visual:
        raw['SpellVisualID_1'] = visual
    built = []
    for e in effects:
        effect = dict(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=target, mechanic=mechanic)
        effect.update(e)
        built.append(Effect(**effect))
    return spell(
        id=spell_id, name=name, school=school, dispel=dispel, mechanic=mechanic,
        attributes=(ATTR0_AURA_IS_DEBUFF if debuff else 0) | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=built, spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _dummy_look(spell_id: int, name: str, visual: int, duration_ms: int, notes: str, icon: int):
    """A lasting look: a DUMMY aura the unit (or a stalker) casts on itself, no number."""
    return _aura(spell_id, name, [dict(apply_aura=AuraType.DUMMY, base_points=0)], duration_ms=duration_ms,
                 debuff=False, icon=icon, desc='', aura_desc='', notes=notes, visual=visual,
                 target=TARGET_UNIT_CASTER)


def _missile(spell_id: int, name: str, visual: int, speed: float, notes: str, icon: int):
    """A dest missile: an instant DUMMY at a point, the visual's missile flies there at `speed` (look only)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=f'{_D5}: {notes} Look only; the registry owns the hit.',
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Speed=speed,
                              Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _refflat_dot(spell_id: int, name: str, school: School, pct: tuple[int, int], tick_ms: int, duration_ms: int,
                 icon: int, desc: str, aura_desc: str, notes: str, dispel: int = 0, mechanic: int = 0,
                 visual: int = 0):
    """A DoT at `pct` hundredths of the reference row a tick (heroic in EffectMiscValueB) through
    spell_dungeon_refflat_periodic; ignores caster modifiers."""
    raw = kit_raw(desc, aura_desc, CastingTimeIndex=1, EffectMiscValueB_1=pct[1], DefenseType=_DEFENSE_MAGIC,
                  AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                  AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                  AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP)
    if visual:
        raw['SpellVisualID_1'] = visual
    s = spell(
        id=spell_id, name=name, school=school, dispel=dispel, mechanic=mechanic, attributes=ATTR0_AURA_IS_DEBUFF,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=pct[0],
                        die_sides=0, amplitude=tick_ms, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                        mechanic=mechanic, potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )
    scripted_by(s, 'spell_dungeon_refflat_periodic')
    return s


# --- CH1 Title Holder, the Risen look ---------------------------------------------------------------------------------

title_holder_210870 = _aura(
    210870, 'Title Holder', [dict(apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=TITLE_HOLDER_PCT,
                                  misc_value=_SCHOOL_MASK_ALL,
                                  potency_excluded='Title Holder: a flat +10% damage done, not a damage value')],
    duration_ms=-1, debuff=False, icon=_ICON_STRENGTH_OF_THE_CHAMPION, visual=CH_TITLE_HOLDER,
    target=TARGET_UNIT_CASTER, desc='Defending the title.', aura_desc='Defending the title. Damage done increased.',
    notes=f'{_D5}, CH1 (ruling 25): the second champion, the reigning one, casts it on itself (triggered) as '
          'Grimstone names it (DoAction ACTION_RING_TITLE_HOLDER): +10% damage done for its fight (the buff text is '
          'number-free by the spec). Berserking\'s lasting hand glow (SV 6943); the arrival flash is 210871. The same '
          'moment gives it the Molten legs token\'s loot mode (LootMode 4, RingChampionsLogic.h).',
)
title_flash_210871 = self_visual(
    210871, 'Title Holder', CH_TITLE_HOLDER_FLASH,
    f'{_D5}, CH1: the arrival flash, Strength of the Champion 16916\'s impact (SV 4345, one-shot only).',
    icon=_ICON_STRENGTH_OF_THE_CHAMPION,
)
risen_210872 = _dummy_look(
    210872, 'Risen', RL_RAISED, -1,
    f'{_D5}, AN1: the lasting purple ghost state on a Risen beast or the Risen Champion (Spirit Particles (purple) '
    '28126, SV 7566; never the Seven\'s Gather Doom look).',
    icon=_ICON_RAISE_DEAD,
)

# --- GO1 Dervish Dance, GO2 Returning Axe -----------------------------------------------------------------------------

dance_bar_210873 = cast_bar(
    210873, 'Dervish Dance', 2000, 'The Dervish picks his partner.',
    f'{_D5}, GO1: Gorosh\'s 2 s bar while the 6 yd line from him to the marked player\'s spot fills (the registry '
    'owns the hits). Not interruptible (1972: no stun; PreventionType 0).',
    icon=_ICON_WHIRLWIND,
)
dance_line_210874 = resolve_copy(
    210874, 'Dervish Dance', School.NORMAL, 'The Dervish whirls through you.',
    f'{_D5}, GO1: every 15 s (heroic 12 s) a random player, the tank included (ruling 88): a 6 yd line from him to '
    'their spot, 2 s, resolved as he whirls down it at 20 yd/s (Projectile): 20% (heroic 35%) of the reference row and '
    '1 Weakened (registry tag 18). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_WHIRLWIND,
)
dance_end_210875 = resolve_copy(
    210875, 'Dervish Dance', School.NORMAL, 'The Dervish ends his dance in a whirlwind.',
    f'{_D5}, GO1: the 8 yd Whirlwind where the line ends, as he gets there (2 s + the whirl): 25% (heroic 40%) and 1 '
    'Weakened (registry tag 19). The marked player steps off the end. Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_WHIRLWIND,
)
dance_look_210876 = _dummy_look(
    210876, 'Dervish Dance', GO_DERVISH_DANCE, DANCE_LOOK_MS,
    f'{_D5}, GO1: the lasting cyclone while he whirls down the line (Whirlwind 26083, SV 7428; never SV 227, a '
    'cleave flash). The script removes it on arrival.',
    icon=_ICON_WHIRLWIND,
)
axe_land_210877 = resolve_copy(
    210877, 'Returning Axe', School.NORMAL, 'An axe lands at your feet.',
    f'{_D5}, GO2: every 20 s an axe at a random player\'s spot (the tank too): a 3 yd circle, 2 s: 15% (heroic 25%) '
    'and 1 Weakened (registry tag 6, G1\'s `axe-return` row). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_THROW_AXE,
)
axe_return_210878 = resolve_copy(
    210878, 'Returning Axe', School.NORMAL, 'The axe flies back to the Dervish.',
    f'{_D5}, GO2: the axe sticks 6 s; its return line (4 yd, axe to Gorosh) shows the whole time (tag 7, no damage) '
    'and locks 2 s before it flies, from the axe to where he stands then (the tank moves him off the group): 20% '
    '(heroic 35%) and 1 Weakened (registry tag 8). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_THROW_AXE,
)
axe_throw_210879 = _missile(
    210879, 'Returning Axe', GO_RETURNING_AXE, AXE_THROW_SPEED,
    'GO2: the thrown axe, cast by Gorosh (triggered) at the landing spot as its warning starts: Throw Axe 16075\'s '
    'missile_axe_copper (SV 3962; never Hurl Axe SV 14843, no missile).',
    icon=_ICON_THROW_AXE,
)
axe_return_look_210880 = _missile(
    210880, 'Returning Axe', GO_RETURNING_AXE, AXE_RETURN_SPEED,
    'GO2: the axe flies home, cast by the axe\'s stalker (triggered) at Gorosh\'s spot as the locked line resolves '
    '(the same missile, caster and target swapped). The stuck axe itself is Blackrock Spire\'s gameobject 301250 '
    '(display 8494), despawned as it flies.',
    icon=_ICON_THROW_AXE,
)
axe_chain_210881 = spell(
    id=210881, name='Returning Axe', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=AXE_CHAIN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_THROW_AXE,
    notes=f'{_D5}, GO2: the return line\'s chain while the axe is stuck: channeled by the axe\'s stalker (the shared '
          '300796) at Gorosh; the channel draws the beam (Harpoon Chain 49679\'s SV 10920, Voone\'s chain precedent). '
          'IS_CHANNELED + NO_THREAT, ignores LoS, suppresses procs, always hits, ALLOW_ACTION_DURING_CHANNEL, no '
          'interrupt flags; the script interrupts it as the axe flies (8 s is the cap).',
    raw_overrides=kit_raw('', '', CastingTimeIndex=1, InterruptFlags=0, AuraInterruptFlags=0,
                          ChannelInterruptFlags=0, AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_SUPPRESS_TARGET_PROCS | ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AttributesEx5=_ATTR5_ALLOW_ACTION_DURING_CHANNEL,
                          SpellVisualID_1=GO_RETURNING_AXE_LINE),
)

# --- GZ1 Bull Rush, GZ2 Earthshaker Stomp, GZ3 Killing Frenzy ---------------------------------------------------------

rush_bar_210882 = cast_bar(
    210882, 'Bull Rush', 2000, 'Grizzle lowers his head.',
    f'{_D5}, GZ1: Grizzle\'s 2 s bar while the line from him, through the marked player, to the wall fills.',
    icon=_ICON_CHARGE,
)
rush_210883 = resolve_copy(
    210883, 'Bull Rush', School.NORMAL, 'Grizzle tramples you.',
    f'{_D5}, GZ1: every 25 s a random player, the tank included (ruling 88): a 5 yd line (S1 unset: this WP\'s '
    'default) from him through them to the arena wall (D4\'s floor polygon), 2 s, resolved as he charges down it at '
    '30 yd/s: 35% (heroic 50%) of the reference row and a knockback off the line (the script\'s OnHit); no Weakened '
    '(heroic is 50%). Registry tag 20. Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_CHARGE,
)
rush_look_210884 = _dummy_look(
    210884, 'Bull Rush', GZ_BULL_RUSH, RUSH_LOOK_MS,
    f'{_D5}, GZ1: the dust trail while he charges (Bull Rush 4083\'s Sprint dust and ribbon, SV 6); removed at the '
    'wall.',
    icon=_ICON_CHARGE,
)
dazed_210885 = _aura(
    210885, 'Dazed', [dict(apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=DAZED_TAKEN_PCT,
                           misc_value=_SCHOOL_MASK_ALL,
                           potency_excluded='Dazed: a flat +30% damage taken, not a damage value')],
    duration_ms=DAZED_MS, debuff=True, icon=_ICON_DAZED, visual=GZ_DAZED, target=TARGET_UNIT_CASTER,
    desc='Grizzle hit the wall.', aura_desc='Dazed. Damage taken increased by $s1%.',
    notes=f'{_D5}, GZ1: Grizzle hit the wall: +30% damage taken for 4 s, and the script holds him (rooted, no swing) '
          'the same 4 s and clears Killing Frenzy: the burst window. No mechanic (his immunity set 1972 holds DAZE). '
          'Dazed 1604\'s yellow stars (SV 84).',
)
wall_impact_210886 = self_visual(
    210886, 'Bull Rush', GZ_WALL_IMPACT,
    f'{_D5}, GZ1: the wall impact as he arrives (Boulder Impact 46895\'s shake and sound, SV 12714).',
    icon=_ICON_CHARGE,
)
stomp_bar_210887 = cast_bar(
    210887, 'Earthshaker Stomp', STOMP_WARN_MS, 'Grizzle rears up.',
    f'{_D5}, GZ2: the 2.5 s wind-up while the 12 yd ring on him fills (the registry owns the hit).',
    icon=_ICON_WAR_STOMP,
)
stomp_210888 = resolve_copy(
    210888, 'Earthshaker Stomp', School.NORMAL, 'The ground shakes under Grizzle.',
    f'{_D5}, GZ2: every 18 s, 12 yd round him, everyone inside, the tank too (it steps out): 25% (heroic 40%), 1 '
    'Weakened and the 2 s stun 210889 (registry tag 21). Copy of the resolve spell 205001 (Physical) with War Stomp '
    '45\'s crack (SV 2355; the marker carries the radius).',
    icon=_ICON_WAR_STOMP, visual=GZ_EARTHSHAKER_STOMP,
)
stomp_stun_210889 = _aura(
    210889, 'Earthshaker Stomp', [dict(apply_aura=AuraType.MOD_STUN, base_points=0)],
    duration_ms=STOMP_STUN_MS, debuff=True, icon=_ICON_WAR_STOMP, mechanic=_MECHANIC_STUN,
    desc='Stunned.', aura_desc='Stunned.',
    notes=f'{_D5}, GZ2: the stomp\'s 2 s stun (the registry\'s rider on every player it hits; the rule limit).',
)
killing_frenzy_210890 = _aura(
    210890, 'Killing Frenzy',
    [dict(apply_aura=AuraType.MOD_MELEE_HASTE, base_points=FRENZY_PCT,
          potency_excluded='Killing Frenzy: a flat +10% attack speed a stack, not a damage value'),
     dict(apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=FRENZY_PCT, misc_value=_SCHOOL_MASK_ALL,
          potency_excluded='Killing Frenzy: a flat +10% damage done a stack, not a damage value')],
    duration_ms=-1, debuff=False, icon=_ICON_FRENZY, stacks=FRENZY_CAP, dispel=_DISPEL_ENRAGE,
    target=TARGET_UNIT_CASTER, desc='Grizzle works himself into a frenzy.',
    aura_desc='Attack speed and damage increased by $s1% per stack.',
    notes=f'{_D5}, GZ3: every 15 s a stack (DungeonKit::AddStacks), +10% attack speed and damage each, cap 5 on '
          'normal (the script), uncapped on heroic (his soft enrage; CumulativeAura 50 is never reached). An Enrage: '
          'Tranquilizing Shot takes one stack and the script clears the rest (S1: "clears every stack", the purge '
          'list); Bull Rush\'s wall clears it too. The stock "%s goes into a killing frenzy!" on each stack; the flash '
          'is 210891.',
)
frenzy_flash_210891 = self_visual(
    210891, 'Killing Frenzy', GZ_KILLING_FRENZY_FLASH,
    f'{_D5}, GZ3: one flash per stack (Frenzy 8269\'s, SV 870).',
    icon=_ICON_FRENZY,
)

# --- EV1 Spell Eater, EV2 Open Wounds, EV3 Shadow Bolt Volley ---------------------------------------------------------

spell_eater_210892 = _aura(
    210892, 'Spell Eater', [dict(apply_aura=AuraType.DUMMY, base_points=0)],
    duration_ms=SPELL_EATER_MS, debuff=False, icon=_ICON_ANTI_MAGIC_SHELL, visual=EV_SPELL_EATER,
    dispel=_DISPEL_MAGIC, school=School.SHADOW, target=TARGET_UNIT_CASTER,
    desc='Eviscerator eats the magic thrown at him.', aura_desc='Magic damage taken is devoured.',
    notes=f'{_D5}, EV1: every 25 s, instant, 8 s: every magic hit he takes is eaten (the script\'s DamageTaken sets it '
          'to 0 and adds a Devoured stack, cap 15); at its end Devoured Magic (210894) hits every player on the floor '
          'for 2% a stack. Magic: a Purge or Spellsteal ends it with nothing released (the reward; the purge list). '
          'The bots hold magic damage on him while it is up (the DS HoldEntry). Anti-Magic Shield 7121\'s shell (SV '
          '127).',
)
devoured_210893 = _aura(
    210893, 'Devoured Magic', [dict(apply_aura=AuraType.DUMMY, base_points=0)],
    duration_ms=SPELL_EATER_MS + 2000, debuff=False, icon=_ICON_SHADOW_NOVA, stacks=DEVOURED_CAP,
    target=TARGET_UNIT_CASTER, desc='', aura_desc='Devoured magic. It will be released.',
    notes=f'{_D5}, EV1: the count on him, one stack per magic hit eaten (cap 15): what the players read. A DUMMY, no '
          'number; the script removes it at the release.',
)
devoured_magic_210894 = spell(
    id=210894, name='Devoured Magic', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_VALUE)],
    spell_icon_id=_ICON_SHADOW_NOVA,
    notes=f'{_D5}, EV1: the shell\'s release: one cast per player on the floor, its value set by the script '
          '(CastCustomSpell BasePoint0 = RefFlatOn(2% x stacks), cap 30%). Ignores caster modifiers (Title Holder).',
    raw_overrides=kit_raw('Released magic.', CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
devoured_look_210895 = self_visual(
    210895, 'Devoured Magic', EV_DEVOURED_MAGIC,
    f'{_D5}, EV1: the release\'s shadow nova at him (Shadow Nova 30852, SV 7966).',
    icon=_ICON_SHADOW_NOVA, school=School.SHADOW,
)
open_wounds_210896 = _refflat_dot(
    210896, 'Open Wounds', School.NORMAL, OPEN_WOUNDS, OPEN_WOUNDS_TICK_MS, OPEN_WOUNDS_MS, _ICON_REND,
    'Bleeding.', 'Physical damage every 3 sec. It spreads to anyone within 5 yd.',
    f'{_D5}, EV2: every 20 s (the stock Vicious Rend timer) on a random non-tank (only the current victim is spared): '
    '2% of the reference row every 3 s for 15 s; every 3 s it jumps to any player within 5 yd of a bleeder who lacks '
    'it (a registry Spread round the bleeders, tag 22; the jump keeps the bleeders\' time left). A bleed, no dispel. '
    'Bite 17253\'s lasting blood state (SV 376; never the one-puff Vicious Rend SV 372).',
    mechanic=_MECHANIC_BLEED, visual=EV_OPEN_WOUNDS,
)
open_wounds_jump_210897 = resolve_copy(
    210897, 'Open Wounds', School.NORMAL, 'The wound spreads.',
    f'{_D5}, EV2: the jump tick\'s resolve (a registry Spread, 5 yd round each bleeder, every 3 s; registry tag '
    '22): no damage; the script gives the bleed to the players it lists. One Crowd Favor judgment per bleed. Copy of '
    'the resolve spell 205001 (Physical).',
    icon=_ICON_REND,
)
volley_210898 = spell(
    id=210898, name='Shadow Bolt Volley', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=VOLLEY_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=VOLLEY[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_SRC_CASTER, implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY,
                    radius_yards=VOLLEY_RADIUS, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_SHADOW_BOLT_VOLLEY,
    notes=f'{_D5}, EV3: the stock Shadow Bolt Volley 15245 (128-172 shadow) rescaled (rule 15: a copy in the slice; '
          'S1 "stock rescaled", this WP\'s default): everyone within 30 yd, 10% (heroic 15%: EffectMiscValueB) of the '
          'reference row through spell_dungeon_refflat_damage; every 15 s (heroic 12 s), a 3 s cast, interruptible '
          '(InterruptFlags 15, silence-preventable; the Ring\'s interrupt list: a reward on normal, expected on '
          'heroic).',
    raw_overrides=kit_raw('Hurls a volley of shadow bolts.', EffectMiscValueB_1=VOLLEY[1],
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(volley_210898, 'spell_dungeon_refflat_damage')

# --- OK1 Arcane Rupture, OK2 Sheep Bolt, OK3 Slow ---------------------------------------------------------------------

rupture_bar_210899 = cast_bar(
    210899, 'Arcane Rupture', RUPTURE_CAST_MS, 'Ok\'thor gathers the arcane under the floor.',
    f'{_D5}, OK1: Ok\'thor\'s 3 s bar while the donut fills (the registry owns the hit). Physical, not Arcane (rule '
    '5: a kick of his stock Arcane Bolt locks Arcane; the bar must never be locked out).',
    icon=_ICON_ARCANE_EXPLOSION,
)
rupture_210900 = resolve_copy(
    210900, 'Arcane Rupture', School.ARCANE, 'The floor of the Ring erupts.',
    f'{_D5}, OK1: every 20 s (heroic 15 s) the whole arena erupts except 8 yd (heroic 6 yd) round him: 30% (heroic '
    '45%) and 1 Weakened (registry tag 9, heroic 10: G1\'s `rupture` rows); everyone collapses in. Copy of the resolve '
    'spell 205007 (Arcane) with Arcane Nova 44644\'s dome at him (SV 9970; risky, the donut marker is the danger).',
    icon=_ICON_ARCANE_EXPLOSION, visual=OK_ARCANE_RUPTURE,
)
sheep_bolt_210901 = resolve_copy(
    210901, 'Sheep Bolt', School.ARCANE, 'A bolt of polymorph magic.',
    f'{_D5}, OK2: 10 s after each Rupture, a 5 yd circle at a random player\'s spot (heroic 2), 2 s: 15% (heroic 25%), '
    '1 Weakened and the 2 s Polymorph 210902 (registry tag 23). Copy of the resolve spell 205007 (Arcane).',
    icon=_ICON_POLYMORPH,
)
sheep_210902 = _aura(
    210902, 'Sheep Bolt',
    [dict(apply_aura=AuraType.MOD_CONFUSE, base_points=0),
     dict(apply_aura=AuraType.TRANSFORM, base_points=0, misc_value=_SHEEP_ENTRY)],
    duration_ms=SHEEP_MS, debuff=True, icon=_ICON_POLYMORPH, visual=OK_SHEEP_BOLT, school=School.ARCANE,
    mechanic=_MECHANIC_POLYMORPH, dispel=_DISPEL_MAGIC, desc='Polymorphed.', aura_desc='Polymorphed.',
    notes=f'{_D5}, OK2: the circle\'s 2 s Polymorph (the registry\'s rider; the fix of the stock 20 s Polymorph '
          '15534): a sheep (TRANSFORM 16372, Polymorph 118\'s look, SV 12978). It does not break on damage (the '
          'resolve\'s own hit may land after the rider): a fixed 2 s. Magic.',
)
slow_210903 = _aura(
    210903, 'Slow',
    [dict(apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-SLOW_MOVE_PCT, mechanic=_MECHANIC_SNARE),
     dict(apply_aura=AuraType.MOD_MELEE_HASTE, base_points=-SLOW_HASTE_PCT,
          potency_excluded='Slow: a flat -55% attack speed, not a damage value'),
     dict(apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK, base_points=-SLOW_HASTE_PCT,
          potency_excluded='Slow: a flat -55% casting speed, not a damage value')],
    duration_ms=SLOW_MS, debuff=True, icon=_ICON_SLOW, school=School.ARCANE, dispel=_DISPEL_MAGIC,
    desc='Slowed.', aura_desc='Movement speed reduced by $s1%. Attack and casting speed reduced by $s2%.',
    notes=f'{_D5}, OK3: the stock Slow 19137 (self-area 20 yd, 20 s) made one random player, 8 s (S1): -60% movement, '
          '-55% attack and casting speed (stock values). Every 15 s. Magic: a dispel is a reward (the dispel list).',
)

# --- AN1 Raise Dead, AN2 Web Spit, AN3 the curses ---------------------------------------------------------------------

raise_dead_bar_210904 = cast_bar(
    210904, 'Raise Dead', RAISE_CAST_MS, 'Anub\'shiah calls the fallen beasts back.',
    f'{_D5}, AN1: the 2 s bar; when it ends one beast of the opener\'s type (heroic 2) rises where one died '
    '(Grimstone\'s DeathSpots), at most the wave\'s size alive. Physical, not Shadow (rule 5: his stock Shadow Bolt is '
    'the kickable Shadow).',
    icon=_ICON_RAISE_DEAD,
)
raise_dead_look_210905 = self_visual(
    210905, 'Raise Dead', AN_RAISE_DEAD,
    f'{_D5}, AN1: the shadow hands and flash as a Risen unit rises, cast by it on itself (Raise Dead 17475, SV 634).',
    icon=_ICON_RAISE_DEAD, school=School.SHADOW,
)
web_spit_210906 = resolve_copy(
    210906, 'Web Spit', School.NATURE, 'Anub\'shiah spits a web at you.',
    f'{_D5}, AN2: every 18 s a 6 yd circle at a random player\'s spot (the tank too), 2 s: 15% (heroic 25%), 1 '
    'Weakened and the 2 s root 210907 (registry tag 24); the web stays 20 s (the patch, tag 25). Copy of the resolve '
    'spell 205004 (Nature).',
    icon=_ICON_WEB,
)
web_root_210907 = _aura(
    210907, 'Web Spit', [dict(apply_aura=AuraType.MOD_ROOT, base_points=0)],
    duration_ms=WEB_ROOT_MS, debuff=True, icon=_ICON_WEB, mechanic=_MECHANIC_ROOT, school=School.NATURE,
    desc='Webbed.', aura_desc='Rooted.',
    notes=f'{_D5}, AN2: the impact\'s 2 s root (the fix of Enveloping Web 15471\'s 8 s root and silence).',
)
web_slow_210908 = standing_in_it(
    210908, f'{_D5}, AN2: the web patch\'s -50% movement (the linger\'s rider, every 1 s tick that finds you in it; '
    'it ends 2 s after you step out).', name='Web', slow_pct=WEB_SLOW_PCT,
    desc='Stuck in a web. Lasts $d.', aura_desc='Movement speed reduced by $s1%.', icon=_ICON_WEB,
)
web_patch_210909 = _dummy_look(
    210909, 'Web Spit', AN_WEB_PATCH, WEB_PATCH_MS + 500,
    f'{_D5}, AN2: the 20 s patch on a stalker (the shared 300796): the shipped Stratholme 7 yd web state (SV 90503; '
    'the safe side of the 6 yd zone).',
    icon=_ICON_WEB,
)
web_spit_look_210910 = _missile(
    210910, 'Web Spit', AN_WEB_SPIT, WEB_SPIT_SPEED,
    'AN2: the spit, cast by Anub\'shiah (triggered) at the spot as the warning starts (Web 745\'s missile and decal, '
    'SV 684).',
    icon=_ICON_WEB,
)
tongues_210911 = _aura(
    210911, 'Curse of Tongues', [dict(apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK, base_points=-TONGUES_PCT,
                                      potency_excluded='Curse of Tongues: a flat -50% casting speed')],
    duration_ms=CURSE_MS, debuff=True, icon=_ICON_CURSE_OF_TONGUES, school=School.SHADOW, dispel=_DISPEL_CURSE,
    desc='Cursed.', aura_desc='Casting speed reduced by $s1%.',
    notes=f'{_D5}, AN3: the stock Curse of Tongues 15470 (30 yd around a random target) made one random player, 15 s, '
          '-50% casting speed (the stock value). Stock timer (4.8 s, then 22-26 s). Curse: removal is a reward.',
)
weakness_210912 = _aura(
    210912, 'Curse of Weakness', [dict(apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=-WEAKNESS_PCT,
                                       misc_value=_SCHOOL_MASK_PHYSICAL,
                                       potency_excluded='Curse of Weakness: a flat -20% physical damage done')],
    duration_ms=CURSE_MS, debuff=True, icon=_ICON_CURSE_OF_WEAKNESS, school=School.SHADOW, dispel=_DISPEL_CURSE,
    desc='Cursed.', aura_desc='Physical damage done reduced by $s1%.',
    notes=f'{_D5}, AN3: the stock Curse of Weakness 12493 (-1 for 120 s: nothing) retuned: one random player, 15 s, '
          '-20% physical damage done (designer). Stock timer (2.4 s, then 10-14 s). Curse: removal is a reward.',
)
web_patch_tick_210913 = resolve_copy(
    210913, 'Web', School.NATURE, 'Stuck in a web.',
    f'{_D5}, AN2: the web patch\'s tick (a persistent 6 yd registry Zone, 20 s, every 1 s; registry tag 25): no '
    'damage, the -50% rider 210908. Copy of the resolve spell 205004 (Nature).',
    icon=_ICON_WEB,
)

# --- HE1 Web Strands, HE2 Reel In + Baneful Burst ---------------------------------------------------------------------

strands_bar_210914 = cast_bar(
    210914, 'Web Strands', STRANDS_WARN_MS, 'Hedrum sprays webs across the Ring.',
    f'{_D5}, HE1: Hedrum\'s 2 s bar while the three lines fill (Web Spray 29484\'s cast, SV 7613).',
    icon=_ICON_WEB_SPRAY, visual=HE_WEB_STRANDS, school=School.NATURE,
)
strands_210915 = resolve_copy(
    210915, 'Web Strands', School.NATURE, 'A strand of web lashes across the floor.',
    f'{_D5}, HE1: every 25 s three 4 yd lines from him to the arena wall (D4\'s floor polygon; the first at a random '
    'player, the others a third of a turn apart), 2 s: 20% (heroic 35%), 1 Weakened and the 2 s root 210916 (registry '
    'tag 26); the strands stay 20 s (heroic 30 s: two sets up at once) at -30% (tag 27). Copy of the resolve spell '
    '205004 (Nature).',
    icon=_ICON_WEB_SPRAY,
)
strands_root_210916 = _aura(
    210916, 'Web Strands', [dict(apply_aura=AuraType.MOD_ROOT, base_points=0)],
    duration_ms=STRANDS_ROOT_MS, debuff=True, icon=_ICON_WEB_SPRAY, mechanic=_MECHANIC_ROOT, school=School.NATURE,
    desc='Webbed.', aura_desc='Rooted.',
    notes=f'{_D5}, HE1: a strand\'s 2 s root (the fix of Web Explosion 15474\'s 10 s room root).',
)
strands_slow_210917 = standing_in_it(
    210917, f'{_D5}, HE1: a strand\'s -30% movement (the linger\'s rider, every 1 s tick that finds you on it).',
    name='Web Strands', slow_pct=STRANDS_SLOW_PCT, desc='Caught in a web strand. Lasts $d.',
    aura_desc='Movement speed reduced by $s1%.', icon=_ICON_WEB_SPRAY,
)
strand_patch_210918 = _dummy_look(
    210918, 'Web Strands', HE_WEB_STRAND_PATCH, STRANDS_LIFE_MS + 500,
    f'{_D5}, HE1: a 5 yd web patch every 8 yd along a strand, on stalkers (the shared 300796) for the strand\'s life '
    '(decoration: the kit line marker is the exact edge; Stratholme\'s SV 90501).',
    icon=_ICON_WEB_SPRAY,
)
reel_in_210919 = _aura(
    210919, 'Reel In', [dict(apply_aura=AuraType.DUMMY, base_points=0)],
    duration_ms=REEL_LOOK_MS, debuff=True, icon=_ICON_WEB_WRAP, visual=HE_REEL_IN, school=School.NATURE,
    desc='Reeled in.', aura_desc='Reeled in by Hedrum.',
    notes=f'{_D5}, HE2: the web wrap on the pulled player for the pull (Web Wrap 28622, SV 7610): the jump\'s look '
          '(DungeonKit::JumpTo lookSpell, cast by Hedrum). Every 20 s the farthest player (heroic two) is pulled to '
          'his feet.',
)
baneful_burst_210920 = resolve_copy(
    210920, 'Baneful Burst', School.NATURE, 'Hedrum bursts with poison.',
    f'{_D5}, HE2: 3 s after the pull lands, 10 yd round him, everyone inside, the tank too: 30% (heroic 45%), 1 '
    'Weakened and the poison 210921 (registry tag 28). Copy of the resolve spell 205004 (Nature).',
    icon=_ICON_POISON_NOVA,
)
baneful_poison_210921 = _refflat_dot(
    210921, 'Baneful Burst', School.NATURE, BANEFUL, BANEFUL_TICK_MS, BANEFUL_MS, _ICON_POISON_NOVA,
    'Poisoned by Hedrum.', 'Nature damage every 1 sec.',
    f'{_D5}, HE2: the burst\'s poison (the registry\'s rider): 2% of the reference row a second for 8 s (both '
    'difficulties). A Poison: a dispel is a reward (the dispel list).',
    dispel=_DISPEL_POISON,
)
baneful_look_210922 = self_visual(
    210922, 'Baneful Burst', HE_BANEFUL_BURST,
    f'{_D5}, HE2: the poison nova at him as the burst resolves (Poison Nova 55081, SV 12084; the 10 yd ring marker '
    'carries the radius).',
    icon=_ICON_POISON_NOVA, school=School.NATURE,
)
strand_tick_210923 = resolve_copy(
    210923, 'Web Strands', School.NATURE, 'Caught in a web strand.',
    f'{_D5}, HE1: a strand\'s tick (a persistent 4 yd registry line, 20 s / 30 s, every 1 s; registry tag 27): no '
    'damage, the -30% rider 210917. Copy of the resolve spell 205004 (Nature).',
    icon=_ICON_WEB_SPRAY,
)
