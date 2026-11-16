"""
Blackrock Spire build WP-B12: Warchief Rend Blackhand (10429) and Gyth (10339), "Let the Games Begin", normal and
heroic (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows RG, s3.5 row B12, s3.6, s3.8
NM 11; build spec docs/dungeons/blackrock-spire-rework.md "Warchief Rend Blackhand and Gyth", rulings 59-61, 63-64; the
rolling front ruling 3). WP-B12 owns this file (its spells: kSpellsRendGyth 210430-210489 of modules/mod-dungeon-bosses
src/BlackrockSpire/BlackrockSpireRework.h; RendGythLogic.h names the same ids; creatures 300732-300734). The engine side
is src/BlackrockSpire/boss_rend_blackhand_rework.cpp (the show, Rend, the Nefarius copy, the Dress Hunt whelps, the
Banner, the frost wall carrier) and boss_gyth_rework.cpp. The core SQL rev rev_rend_gyth_blackrock_spire.sql rebinds
spawn 137967 to the Nefarius copy, writes the texts and edits the Handler's SmartAI.

- 10339 Gyth: bound to boss_gyth_rework (SmartAI off; the stock boss_gyth stays registered, unbound by this data: the
  25% floor, Freeze and the random Flame Breath go), normal 140k at 5 players (HealthModifier 43.25 on the level 62
  warrior base 3,237; the flex scaler multiplies it at his pull), stun immune (1972), INSTANCE_BIND, DamageModifier 5
  (the stock sniff value). Heroic 200k is WP-H's.
- 10429 Warchief Rend Blackhand: bound to boss_rend_blackhand_rework, 160k at 5 (49.428 on 3,237), DamageModifier 6.5.
  Heroic 210k is WP-H's. His loot rows are L-2's (Head of Rend Blackhand kept, SP note 12).
- 10442 Chromatic Whelp, 10447 Chromatic Dragonspawn, 10742 Blackhand Dragon Handler (boss-kit only: the arena's
  statics and Rend's summons): the build spec's normal health at 5 players at a fixed level (whelp level 58, 4,000 =
  1.741401 x the level 58 paladin base 2,297; Dragonspawn and Handler level 60, 15,000 = 4.9148 x and 9,000 = 2.948885 x
  the level 60 warrior base 3,052). Their SmartAI stays (the rev adds the Handler's Mend Dragon on Gyth); the Dress
  Hunt whelps get the round's C++ AI on summon. Heroic health is WP-H's.
- 300732 Lord Victor Nefarius (Blackrock Spire copy of 10162): npc_brs_lord_victor_nefarius, his stock look (display
  9472, his staff by the rev's equip row), level 63, hostile but never attackable (UNIT_FLAG_NON_ATTACKABLE instead of
  the stock IMMUNE_TO_PC, so his rounds' hits reach players), civilian, no loot, no gossip. Blackwing Lair's 10162 is
  not touched. npcflag 1 as stock (the heroic rollout's "npc" role: no heroic template).
- 300733 Banner of the Dark Horde (RG12): npc_brs_banner_of_the_dark_horde, the Horde Battle Standard (display 14542 at
  0.4, V-2), level 60, 15,000 at 5 players (4.9148 x 3,052; heroic 20,000: WP-H's override on 310296, its heroic
  entry), rooted, no attacks, no XP, no loot.
- 300734 Frost wall (RG6): npc_brs_frost_wall, an untargetable carrier wearing V-2's ice wall (display 90740 at 0.5:
  about 8 yd of wall per piece, one piece per 8 yd; the kit's FrontDirector spawns and moves them).

Spells (looks from ._visuals, WP-V-2's RG_* picks; every look unconfirmed until seen in game):

  210430  Rend's Mark            RG9 the 4 s tell on the marked player (DUMMY debuff)
  210431  Flame Breath           RG9 / RG10 a breath's hit (resolve copy, Fire): 40%, Weakened
  210432  Flame Breath           RG9 / RG10 Gyth's breath look (Flame Breath 16390's SV 1483)
  210433  Flame Breath           RG10 the riderless breath's 2 s bar (Fire, not interruptible)
  210434  Freezing Sweep         RG6 the wall's hit (resolve copy, Frost): 25%, Weakened
  210435  Frozen                 RG6 the wall's rider: a 2 s stun
  210436  Freezing Breath        RG6 the breath that sends a wall (Freezing Breath 47415's SV 10569, the cast only)
  210437  Shadowflame            RG7 the circle's hit (resolve copy, Shadow): 30%, Weakened (Shadow Flame's SV 6559)
  210438  Shadowflame            RG7 a pool's burn: 30% on entering and every 2 s (the kit's percent spell)
  210439  Shadowflame            RG7 a pool's look, normal: a 6 yd dynamic object for 20 s (V-2's shadow quad)
  210440  Shadowflame            RG7 the same, heroic: 25 s
  210441  Whelp Bite             RG5 a hunting whelp's bite, normal: 3% (the kit's percent spell, Physical)
  210442  Whelp Bite             RG5 the same, heroic: 5%
  210443  Hunting                RG5 the hunting whelp's marker (the descriptor's kill priority)
  210444  Thumbs Down            RG8 the skull over the condemned, 5 s (the Keening skull, SV 90506)
  210445  Shadow Crash           RG8 a share of the split hit (Shadow; the script sets the share)
  210446  Whirlwind              RG11 the 2 s wind-up (Physical, not interruptible)
  210447  Whirlwind              RG11 the whirl's tick (resolve copy, Physical): 10% a second
  210448  Whirlwind              RG11 the 6 s whirl on Rend (Whirlwind 13736's SV 8377)
  210449  Banner of the Dark Horde  RG12 Rend's buff while a live banner stands within 10 yd (DUMMY; +25% by script)
  210450  Mortal Wounds          RG17 10 players: -10% healing taken per stack, 15 s, no cap
  210451  Impatient Host         RG4 the bored host, step 1 (on Nefarius, DUMMY)
  210452  Bored Host             RG4 the bored host, step 2
  210453-210489 spare.

Tooltips are number-free where the number is a reference percent (Systems.md s10).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    FACTION_MONSTER,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BANNER_DISPLAY_SCALE,
    DISPLAY_BATTLE_STANDARD,
    DISPLAY_ICE_WALL,
    RG_FLAME_BREATH,
    RG_FREEZING_BREATH_CAST,
    RG_SHADOW_FLAME_HIT,
    RG_THUMBS_DOWN_HIT,
    RG_THUMBS_DOWN_SKULL,
    RG_WHIRLWIND,
    SV_SHADOWFLAME_POOL_AREA,
    VG_GORE_IMPACT,
)

_B12 = 'Blackrock Spire build WP-B12 (Rend Blackhand and Gyth)'
_SCRIPT_REFFLAT = ('Blackrock Spire: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')
_REFFLAT = 'spell_dungeon_refflat_damage'

_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_FLAG_DEST_LOCATION = 0x40
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a debuff never outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_MECHANIC_STUN = 12

# Icons of the stock spells the looks come from (Spell.dbc, the working copy).
_ICON_FLAME_BREATH = 11             # Flame Breath 16390
_ICON_FREEZE = 35                   # Freeze 16350
_ICON_FREEZING_BREATH = 188         # Freezing Breath 47415
_ICON_SHADOW_FLAME = 937            # Shadow Flame 22539
_ICON_SHADOWFLAME = 3317            # Shadowflame 47960
_ICON_BITE = 1680                   # Bite 17253
_ICON_FIXATE = 71                   # Fixate 12021
_ICON_SHADOW_CRASH = 1939           # Shadow Crash 62660
_ICON_WHIRLWIND = 83                # Whirlwind 13736
_ICON_BATTLE_STANDARD = 1691        # Battle Standard 22996
_ICON_MORTAL_STRIKE = 564           # Mortal Strike 16856
_ICON_ROAR = 148                    # Intimidating Roar 16508

# RendGythLogic.h (hundredths for the percent spells).
_MARK_MS = 4000                     # kMarkWarnMs
_BREATH_CAST_MS = 2000              # kRiderlessCastMs
_FROZEN_MS = 2000                   # kFrozenMs
_POOL_MS = 20000                    # kPoolMs
_POOL_HEROIC_MS = 25000             # kPoolHeroicMs
_POOL_RADIUS = 6.0                  # kShadowflameRadius
_POOL_BURN = 3000                   # kPoolPct 30
_BITE = 300                         # kBitePct 3
_BITE_HEROIC = 500                  # kBiteHeroicPct 5
_ROUND_MS = 15000                   # kRoundMs (the whelps' life)
_THUMBS_MS = 5000                   # kThumbsWarnMs
_WHIRL_WINDUP_MS = 2000             # kWhirlWindupMs
_WHIRL_MS = 6000                    # kWhirlMs
_WOUNDS_MS = 15000                  # kWoundsMs
_WOUNDS_HEALING_PCT = -10
_WOUNDS_MAX = 255                   # "no cap" (the aura's own limit)

# Fixed levels for exact health at 5 players (creature_classlevelstats, exp 0): level 58 paladin 2,297; level 60
# warrior 3,052.
_WHELP_HEALTH_MODIFIER = 1.741401   # ceil(2,297 x 1.741401) = 4,000
_DRAGONSPAWN_HEALTH_MODIFIER = 4.9148   # ceil(3,052 x 4.9148) = 15,000
_HANDLER_HEALTH_MODIFIER = 2.948885     # ceil(3,052 x 2.948885) = 9,000
_BANNER_HEALTH_MODIFIER = 4.9148        # 15,000
_BANNER_HEROIC_ENTRY = 310296       # WP-H's predicted lock line (lib/test_blackrock_spire_heroic.py KIT_HEROIC_ID)

# Nefarius's stock look and flags (creature_template 10162, read-only SELECT 2026-11-15): display 9472, level 63,
# dragonkin, paladin class. The copy is UNIT_FLAG_NON_ATTACKABLE 0x2 | 0x40 | 0x8000 (the stock 33088 has IMMUNE_TO_PC
# 0x100 instead, which would keep his own spells off players), civilian (flags_extra 0x2), no XP (0x40).
# npcflag 1 (gossip) is the stock value: a hostile unit's gossip never opens, and the heroic rollout reads an npcflag as
# the "npc" role (no heroic template, as 10162: source/world/dungeons/blackrock_spire.py, handoff s7 #23).
_NPCFLAG_GOSSIP = 0x1
_NEFARIUS_DISPLAY = 9472
_NEFARIUS_UNIT_FLAGS = 0x2 | 0x40 | 0x8000
_FLAGS_EXTRA_CIVILIAN_NO_XP = 0x2 | 0x40
_FLAGS_EXTRA_NO_XP = 0x40
_TYPE_DRAGONKIN = 2
_TYPE_NOT_SPECIFIED = 10

# --- the bindings (wave 2) -------------------------------------------------------------------------------------------

if BIND_WAVE_2:
    creature_template_columns(10339, **boss_columns(
        'boss_gyth_rework', 43.25, damage_modifier=5,
    ))
    creature_template_columns(10429, **boss_columns(
        'boss_rend_blackhand_rework', 49.428, damage_modifier=6.5,
    ))
    creature_template_columns(10442, minlevel=58, maxlevel=58, HealthModifier=_WHELP_HEALTH_MODIFIER)
    creature_template_columns(10447, minlevel=60, maxlevel=60, HealthModifier=_DRAGONSPAWN_HEALTH_MODIFIER)
    creature_template_columns(10742, minlevel=60, maxlevel=60, HealthModifier=_HANDLER_HEALTH_MODIFIER)

# --- 300732 Lord Victor Nefarius (the Blackrock Spire copy), 300733 the Banner, 300734 the frost wall ---------------

lord_victor_nefarius_300732 = creature_template(
    300732, 'Lord Victor Nefarius', **{
        **KIT_CREATURE, 'subname': 'Lord of Blackrock', 'faction': FACTION_MONSTER, 'type': _TYPE_DRAGONKIN,
        'minlevel': 63, 'maxlevel': 63, 'rank': 3, 'unit_class': 2, 'unit_flags': _NEFARIUS_UNIT_FLAGS,
        'HealthModifier': 115.0, 'ManaModifier': 100.0, 'DamageModifier': 0.0, 'ExperienceModifier': 0.0,
        'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'gossip_menu_id': 0,
        'npcflag': _NPCFLAG_GOSSIP, 'flags_extra': _FLAGS_EXTRA_CIVILIAN_NO_XP,
        'ScriptName': 'npc_brs_lord_victor_nefarius',
    },
)
creature_model(300732, display_id=_NEFARIUS_DISPLAY)

banner_of_the_dark_horde_300733 = creature_template(
    300733, 'Banner of the Dark Horde', **{
        **KIT_CREATURE, 'type': _TYPE_NOT_SPECIFIED, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'unit_class': 1,
        'unit_flags': 0, 'HealthModifier': _BANNER_HEALTH_MODIFIER, 'DamageModifier': 0.0, 'lootid': 0,
        'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
        'ScriptName': 'npc_brs_banner_of_the_dark_horde', 'difficulty_entry_1': _BANNER_HEROIC_ENTRY,
    },
)
creature_model(300733, display_id=DISPLAY_BATTLE_STANDARD, scale=BANNER_DISPLAY_SCALE)

frost_wall_300734 = creature_template(
    300734, 'Frost Wall', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                             'speed_run': 1.14286, 'ScriptName': 'npc_brs_frost_wall'},
)
creature_model(300734, display_id=DISPLAY_ICE_WALL, scale=0.5)

# --- shared builders -------------------------------------------------------------------------------------------------


def _debuff(spell_id: int, name: str, duration_ms: int, icon: int, desc: str, aura_desc: str, notes: str, *,
            visual: int = 0, school: School = School.NORMAL):
    """A DUMMY debuff (a tell or a marker): not dispellable, dropped on a map change."""
    raw = kit_raw(desc, aura_desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                  AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _buff(spell_id: int, name: str, duration_ms: int, icon: int, desc: str, aura_desc: str, notes: str, *,
          visual: int = 0):
    """A DUMMY buff on the caster (a state or a step the script reads)."""
    raw = kit_raw(desc, aura_desc, instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _percent(spell_id: int, name: str, school: School, hundredths: int, icon: int, desc: str, notes: str, *,
             visual: int = 0, defense: int = _DEFENSE_MAGIC):
    """The kit's percent spell: `hundredths` of the reference row (the tank its own row), set at launch."""
    raw = kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, DefenseType=defense,
                  EffectMiscValueB_1=hundredths, AttributesEx=ATTR1_NO_THREAT,
                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                  AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    s = spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=hundredths - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )
    scripted_by(s, _REFFLAT)
    return s


def _pool_look(spell_id: int, duration_ms: int, notes: str):
    """A Shadowflame pool's look: a 6 yd dynamic object (V-2's shadow quad), visual only."""
    return spell(
        id=spell_id, name='Shadowflame', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=_POOL_RADIUS)],
        spell_icon_id=_ICON_SHADOWFLAME, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=SV_SHADOWFLAME_POOL_AREA,
                              Targets=_TARGET_FLAG_DEST_LOCATION, InterruptFlags=0, PreventionType=0,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- RG9 Rend's Mark, RG10 the riderless breath -----------------------------------------------------------------------

rends_mark_210430 = _debuff(
    210430, 'Rend\'s Mark', _MARK_MS, _ICON_FLAME_BREATH, 'Rend points his polearm at you: Gyth breathes on you next.',
    'Run out: Gyth breathes at you.',
    f'{_B12}, RG9: the tell on the marked player, cast by Gyth (triggered) with Rend\'s emote line 3 (act 2, 5 s after '
    'Gyth engages, then every 15 s, a non-tank). 4 s, the breath\'s warning: the registry\'s RunOut from Gyth '
    '(20 yd, a '
    'ring on the player) and the cone aimed at them own the hit (210431). DUMMY, the debuff icon is the tell.',
)

flame_breath_210431 = resolve_copy(
    210431, 'Flame Breath', School.FIRE, 'Gyth breathes fire.',
    f'{_B12}, RG9 / RG10: a breath\'s hit, 40% of the row and 1 Weakened. RG9: the marked player still within 20 yd of '
    'Gyth (a RunOut measured from him) and anyone else in the 60 degree, 20 yd cone aimed at them; RG10: '
    'anyone but his '
    'tank in the cone down his front (a Frontal). Copy of the mod-boss-mechanics resolve spell 205001 (Fire), no look '
    '(Gyth\'s breath is 210432).',
    icon=_ICON_FLAME_BREATH,
)

flame_breath_look_210432 = self_visual(
    210432, 'Flame Breath', RG_FLAME_BREATH,
    f'{_B12}, RG9 / RG10: Gyth\'s breath, cast on himself (triggered) as the cone resolves, after he turns on the '
    'marked player (RG9). Flame Breath 16390\'s SV 1483 (stock, the doc\'s pick); with Chromatic Protection: Fire '
    '16373 after it (stock).',
    icon=_ICON_FLAME_BREATH, school=School.FIRE,
)

flame_breath_bar_210433 = cast_bar(
    210433, 'Flame Breath', _BREATH_CAST_MS, 'Gyth draws breath.',
    f'{_B12}, RG10: the riderless breath\'s 2 s bar (act 3 with Gyth alive: 5 s after Rend lands, then every 15 s). '
    'DUMMY on the caster, not interruptible, Fire (Gyth has no interruptible bar). The registry\'s Frontal owns the '
    'hit. Flame Breath 16390\'s SV 1483 through the bar.',
    icon=_ICON_FLAME_BREATH, visual=RG_FLAME_BREATH, school=School.FIRE,
)

# --- RG6 Freezing Sweep ----------------------------------------------------------------------------------------------

freezing_sweep_210434 = resolve_copy(
    210434, 'Freezing Sweep', School.FROST, 'A wall of frost rolls over you.',
    f'{_B12}, RG6: the wall\'s hit (a registry rolling line front, KT-B2\'s FrontDirector: 4 yd thick, 68 yd across, '
    'from the portcullis to the way-in door at 8 yd/s, one 8 yd gap in the main strip; heroic a second wall 3 s later, '
    'its gap on the other side within 20 yd): 25% of the row (the tank its own row) and 1 Weakened, then 210435. Copy '
    'of the resolve spell 205001 (Frost), no look of its own (the ice wall pieces, 300734, are the wall).',
    icon=_ICON_FREEZE,
)

frozen_210435 = spell(
    id=210435, name='Frozen', school=School.FROST, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_FROZEN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_STUN, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FREEZE,
    notes=f'{_B12}, RG6: the wall\'s rider on every player it hits: a 2 s stun (Freeze 16350\'s 10 s cut to the 2 s '
          'limit, rule flag 1). MOD_STUN, stun mechanic: stun immunity and the stun breakers answer it. Dispel none. '
          'No look of its own (the stun state). AuraInterruptFlags CHANGE_MAP; removed with the fight.',
    raw_overrides=kit_raw('Frozen solid. Lasts $d.', 'Frozen.', instant=True, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

freezing_breath_210436 = self_visual(
    210436, 'Freezing Breath', RG_FREEZING_BREATH_CAST,
    f'{_B12}, RG6: the breath that sends a wall, cast on himself (triggered) by Gyth hovering over the portcullis end '
    '(by Nefarius with Gyth dead) as each wall launches. Freezing Breath 47415\'s SV 10569 (V-2: the cast only, never '
    'the wall), with Chromatic Protection: Frost 16392 after it on Gyth (stock).',
    icon=_ICON_FREEZING_BREATH, school=School.FROST,
)

# --- RG7 Taste in my power -------------------------------------------------------------------------------------------

shadowflame_210437 = resolve_copy(
    210437, 'Shadowflame', School.SHADOW, 'Shadowflame rains down.',
    f'{_B12}, RG7: the circle\'s hit, a 6 yd circle under every player for 3 s (a registry Spread owned by Gyth, '
    'else Rend: whoever fights the group, so the bots keep its room bounds, R-2 M-2): 30% of the row (the tank its '
    'own row) and 1 Weakened to anyone in someone else\'s. Copy of the resolve '
    'spell 205001 '
    '(Shadow), Shadow Flame 22539\'s SV 6559 on each player hit (V-2: orange, not black, RISKY).',
    icon=_ICON_SHADOW_FLAME, visual=RG_SHADOW_FLAME_HIT,
)

shadowflame_burn_210438 = _percent(
    210438, 'Shadowflame', School.SHADOW, _POOL_BURN, _ICON_SHADOWFLAME, 'The shadowflame burns.',
    f'{_B12}, RG7: a pool\'s burn, cast by Nefarius (triggered) on a player inside one of the 6 yd pools the circles '
    'leave (the kit\'s PuddleField): on entering and every 2 s inside, 30% of the row (3000 hundredths; the tank its '
    'own row), no Weakened (a lingering patch never applies it).',
)

shadowflame_pool_210439 = _pool_look(
    210439, _POOL_MS,
    f'{_B12}, RG7 (normal): a pool\'s look, visual only. Nefarius casts it (triggered) at each player\'s spot as the '
    'circles land (CastSpell(x, y, z)): a 6 yd dynamic object for 20 s with V-2\'s shadow quad (SV 90604, the '
    'Ascension mannoroth goo flow at 0.7). Its DUMMY aura reaches nobody harmful: 210438 owns the burns. The script '
    'removes them when the attempt ends.',
)

shadowflame_pool_heroic_210440 = _pool_look(
    210440, _POOL_HEROIC_MS,
    f'{_B12}, RG7 (heroic): the same pool for 25 s (gone before the next Sweep 27 s after they land, SP).',
)

# --- RG5 Kill the one in the dress -----------------------------------------------------------------------------------

whelp_bite_210441 = _percent(
    210441, 'Whelp Bite', School.NORMAL, _BITE, _ICON_BITE, 'A whelp bites.',
    f'{_B12}, RG5 (normal): a hunting whelp\'s bite on its target once it is there, every second: 3% of the row (300 '
    'hundredths), Physical, cast by the whelp (triggered). Always hits, cannot crit, ignores its modifiers. '
    'Gore\'s hit '
    'flash (SV 39).',
    visual=VG_GORE_IMPACT, defense=_DEFENSE_MELEE,
)

whelp_bite_heroic_210442 = _percent(
    210442, 'Whelp Bite', School.NORMAL, _BITE_HEROIC, _ICON_BITE, 'A whelp bites.',
    f'{_B12}, RG5 (heroic): the same bite, 5% of the row (500 hundredths).',
    visual=VG_GORE_IMPACT, defense=_DEFENSE_MELEE,
)

hunting_210443 = _buff(
    210443, 'Hunting', _ROUND_MS, _ICON_FIXATE, 'Hunting the one in the dress.', 'Hunting.',
    f'{_B12}, RG5: the hunting whelp\'s marker, cast on itself (triggered) as it is summoned for the round: the '
    'descriptor\'s kill priority (TargetEntry(10442, 6, Dps, HasAura(210443))) tells the hunters from the act '
    '1 whelps. '
    '15 s, the round (the whelps leave when it ends). DUMMY.',
)

# --- RG8 Thumbs Down (heroic) ----------------------------------------------------------------------------------------

thumbs_down_210444 = _debuff(
    210444, 'Thumbs Down', _THUMBS_MS, _ICON_SHADOW_CRASH, 'Nefarius condemns you. Gather your allies close.',
    'Condemned: share the fate.',
    f'{_B12}, RG8 (heroic): the skull over the condemned (the non-victim with the lowest health; 2 at 6 or more), cast '
    'by Nefarius (triggered) with his line 13 and boss emote 17. 5 s, the Stack\'s warning (8 yd on them); removed at '
    'the crash. The Keening skull State (SV 90506, shipped by Stratholme): a lasting head state.',
    visual=RG_THUMBS_DOWN_SKULL, school=School.SHADOW,
)

shadow_crash_210445 = spell(
    id=210445, name='Shadow Crash', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Shadow Crash: a share of a split hit the script sets (CastCustomSpell)')],
    spell_icon_id=_ICON_SHADOW_CRASH,
    notes=f'{_B12}, RG8 (heroic): a share of the crash on the condemned, cast by Nefarius (triggered) on each player '
          'within 8 yd of them 5 s after the skull (the registry Stack\'s hits): 150% of the row split evenly '
          '(DungeonKit::SplitShares; 30% each with 5, 50% with 3; a lone player takes all of it and dies). The '
          'share is '
          'the script\'s base points (CastCustomSpell). No Weakened (a split hit). Always hits, cannot crit, '
          'ignores his '
          'modifiers. Shadow Crash 62660\'s SV 13549.',
    raw_overrides=kit_raw('Nefarius\'s judgment falls.', instant=True, InterruptFlags=0, PreventionType=0,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=RG_THUMBS_DOWN_HIT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- RG11 Whirlwind --------------------------------------------------------------------------------------------------

whirlwind_bar_210446 = cast_bar(
    210446, 'Whirlwind', _WHIRL_WINDUP_MS, 'Rend readies his polearm for a whirlwind.',
    f'{_B12}, RG11: the 2 s wind-up (act 3, 15 s after he lands, then every 20 s). DUMMY on the caster, not '
    'interruptible, Physical. The registry\'s 8 yd circle on him owns the hits. Whirlwind 13736\'s SV 8377 through the '
    'bar.',
    icon=_ICON_WHIRLWIND, visual=RG_WHIRLWIND,
)

whirlwind_210447 = resolve_copy(
    210447, 'Whirlwind', School.NORMAL, 'Rend\'s polearm cuts everyone around him.',
    f'{_B12}, RG11: the whirl\'s tick, an 8 yd circle anchored on him for 6 s after the wind-up, every second: 10% of '
    'the row to everyone inside, the tank too (its own row, ruling 51). No Weakened (a lingering zone). Copy of the '
    'resolve spell 205001 (Physical), no look (210448).',
    icon=_ICON_WHIRLWIND,
)

whirlwind_look_210448 = _buff(
    210448, 'Whirlwind', _WHIRL_MS, _ICON_WHIRLWIND, 'Whirlwind.', 'Whirling.',
    f'{_B12}, RG11: the 6 s whirl on Rend, cast on himself (triggered) as the wind-up ends. Whirlwind 13736\'s SV 8377 '
    '(stock, a small dust whirl state). DUMMY (the stock whirl\'s own damage trigger is not copied).',
    visual=RG_WHIRLWIND,
)

# --- RG12 Banner of the Dark Horde -----------------------------------------------------------------------------------

banner_empower_210449 = _buff(
    210449, 'Banner of the Dark Horde', -1, _ICON_BATTLE_STANDARD, 'The banner of the Dark Horde rallies its '
    'warchief.', 'Damage done increased.',
    f'{_B12}, RG12: Rend\'s buff while a live Banner of the Dark Horde (300733) stands within 10 yd of him (the script '
    'polls every 0.5 s and applies or removes it): +25% damage done, by his DamageDealt (the aura is a DUMMY, '
    'the tell). '
    'No look of its own (the banner is the look).',
)

# --- RG17 Mortal Wounds (10 players) ---------------------------------------------------------------------------------

mortal_wounds_210450 = spell(
    id=210450, name='Mortal Wounds', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_WOUNDS_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_PCT,
                    base_points=_WOUNDS_HEALING_PCT, die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Mortal Wounds: a flat -10% healing taken per stack, not a damage or heal value')],
    spell_icon_id=_ICON_MORTAL_STRIKE,
    notes=f'{_B12}, RG17 (10 players only, rulings 63, 64): a stack with every Mortal Strike of his (stock '
          '16856, every '
          '8 s from 5 s after he lands), added by him (DungeonKit::AddStacks with him as caster: the bots\' taunt swap '
          'counts his stacks): -10% healing taken per stack, 15 s, each stack refreshing it, no cap (CumulativeAura '
          '255). The user\'s taunt rule (2026-11-15): a tank taunts only once its own stacks are gone, so it '
          'ends before '
          'the other tank reaches 3 (24 s) and outlasts one strike (8 s); it holds on his current target while he '
          'cannot strike it (the Whirlwind, out of reach). The bots swap at 3 (heroic: the tanks trade him and Gyth). '
          'Not dispellable, dropped on a map change, removed with the fight. No look (the strike is the look).',
    raw_overrides=kit_raw('Healing taken reduced.', 'Healing taken reduced.', CastingTimeIndex=1,
                          CumulativeAura=_WOUNDS_MAX, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- RG4 the bored host ----------------------------------------------------------------------------------------------

impatient_host_210451 = _buff(
    210451, 'Impatient Host', -1, _ICON_ROAR, 'The host grows impatient.', 'The rounds come faster.',
    f'{_B12}, RG4: the bored host, step 1, on Nefarius (cast on himself, triggered, with line 5): act 3 past 1:30 '
    '(heroic 1:15), the calls every 20 s (heroic 7 s). DUMMY, the tell for whoever targets him. Removed when the '
    'attempt ends.',
)

bored_host_210452 = _buff(
    210452, 'Bored Host', -1, _ICON_ROAR, 'The host is bored.', 'The rounds come two at a time.',
    f'{_B12}, RG4: the bored host, step 2, on Nefarius (with line 4): act 3 past 2:30 (heroic 2:00), two rounds per '
    'call (heroic a call every 5 s). DUMMY.',
)
