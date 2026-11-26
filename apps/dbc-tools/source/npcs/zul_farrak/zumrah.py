"""
Zul'Farrak build WP-D3: Witch Doctor Zum'rah (7271)
(.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D3, s3.6, s3.8, s3.9 rows 3-4, s3.10, s7 #29, #30,
#48, s10; build spec docs/dungeons/zul-farrak-rework.md "Witch Doctor Zum'rah", ZR1-ZR14, rulings 17-20, 45). WP-D3
owns this file (its spells: kSpellsZumrah 213920-213959 of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h
only; ZumrahLogic.h names the same ids and holds every number; the texts are the core SQL rev
rev_zumrah_zul_farrak.sql).

- 7271 Witch Doctor Zum'rah: boss_zumrah_rework (SmartAI off: rev_skeleton_zul_farrak.sql drops its rows), normal
  health 176,065 = 114.7 on the level 46 paladin base 1,535 (s3.6, s7 #1 A), the stock DamageModifier 2.4, stun
  immunity 1972, INSTANCE_BIND with both assist flags, detection range 12. Heroic 293,284 is WP-H's override
  (source/world/dungeons/zul_farrak.py). Faction 35 until area trigger 962 (stock, kept).
- 7786 Skeleton of Zum'rah (stock entry; Zum'rah raises four beside each Ward of Zum'rah 7785, wild, by script:
  the ward's stock 11087 / 11088 is cleared, R-1-A M1): bound to npc_zf_zumrah_skeleton (it had no script). Stock
  health, faction and immunity kept; heroic 1,526 is WP-H's.
- 301010 Empty Vessel (ZR3): npc_zf_empty_vessel, the walker's husk: faction 495 (friendly to players, hostile to the
  Skeletons), selectable (s8 #11: the husk must be selectable) but never attackable by a player; its look is the
  walker's (aura 247 from the walker, _visuals ZR_EMPTY_VESSEL_AURA). No heroic template.
- 301011 Lost Soul (ZR4): npc_zf_lost_soul, the Wisp 12432 at 1.75 (LOST_SOUL_SCALE_RANGE), not selectable, not
  attackable, in the spirit world (213924); the boss's CrawlPickups moves and removes it. No heroic template.
- 301012 Bound Dead (ZR6): npc_zf_bound_dead, the Ghostly Troll 29716 (V's model info), not selectable, not attackable,
  in the spirit world. No heroic template.
- 301013 Zul'Farrak Grave Stalker: npc_zf_grave_stalker, the invisible stalker 11686 (trigger), the look where a heroic
  circle lands (a grave in the spirit world, an echo in ours). No heroic template.

Spells (ZumrahLogic.h ZumrahSpells). Every damage is a plain effect whose amount is the script's base point
(DungeonKit::RefFlatOn, the tank row on the tank; DieSides 0) or a resolve copy; every one ignores caster modifiers,
redirection and reflection (rule 2, LESSONS L7):

  213920  Spirit Rend         ZR1 the 2 s bar, Arcane, never interruptible (rule 24: his kickable casts are Shadow)
  213921  Between Worlds      ZR2 the walker: type 11 detection 10, +40% speed, the ghost look; not dispellable
  213922  Empty Vessel        ZR3 aura 247 (the walker's look on the husk)
  213923  Spirit Tether       ZR3 the channel look husk to walker (set as a field, never cast)
  213924  Spirit World        invisibility type 11 at 1: the souls, the Bound Dead, the grave looks
  213925  Lost Soul           ZR4 the soul's lasting purple particles
  213926  Bound Dead          ZR6 the binding look (self visual)
  213927  Spirit Burst        ZR6 a freed Bound Dead; ZR12 an echo's landing (self visual)
  213928  Gathered Souls      ZR5 the walker's stack (99)
  213929  Ward of the Dead    ZR7 his stack (99): -10% damage taken a stack, the script sets the amount (ruling 45)
  213930  Shadow Bolt Volley  ZR9 the kickable 3 s cast (normal)
  213931  Shadow Bolt Volley  ZR9 the kickable 2 s cast (heroic)
  213932  Shadow Bolt Volley  ZR9 the landed hit (script base point)
  213933  Shadow Bolt         ZR10 the copy of 12739, kickable, 3 s (script base point)
  213934  Skeletal Strike     ZR8 a Skeleton's hit (script base point; Shadow, so armor never changes the percent)
  213935  Soul Burn           ZR11 heroic (script base point)
  213936  Soul Echo           ZR12 heroic (resolve copy, Shadow)
  213937  Restless Wail       ZR13 heroic (resolve copy, Shadow)
  213938  Grasping Graves     ZR14 heroic (resolve copy, Shadow)
  213939  Grasping Graves     ZR14 heroic, the grave's look (self visual)
  213940-213959 spare.

The Volley (both casts) and the Shadow Bolt are the only interruptible casts (Shadow; InterruptFlags 15, PreventionType
silence). A kick locks Shadow (LESSONS L2), never Spirit Rend (Arcane, no interrupt flags). Ward of Zum'rah 11086 stays
the stock spell (cast triggered); the ward's own passive 11087 is cleared by script. Retired as casts: Healing Wave
12491, Shadow Bolt Volley 15245, Shadow Bolt 12739 (the copies above). Looks are copied, never the stock spells.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
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
    DISPLAY_BOUND_DEAD,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_LOST_SOUL,
    LOST_SOUL_SCALE_RANGE,
    ZR_BIND,
    ZR_EMPTY_VESSEL_AURA,
    ZR_FREED,
    ZR_GATHERED,
    ZR_SHADOW_BOLT,
    ZR_VOLLEY,
    ZR_GHOST,
    ZR_GRAVE,
    ZR_INVIS_TYPE,
    ZR_LOST_SOUL_STATE,
    ZR_REND,
    ZR_TETHER,
    ZR_WAIL,
    ZR_WARD_SHIELD,
)

creature_template_columns(7271, **boss_columns(
    'boss_zumrah_rework', 114.7, damage_modifier=2.4,
))

# The stock Skeleton of Zum'rah gets its script (it had none: no SmartAI, no ScriptName; SELECT 2026-11-25).
creature_template_columns(7786, ScriptName='npc_zf_zumrah_skeleton', AIName='')

_D3 = "Zul'Farrak build WP-D3 (Witch Doctor Zum'rah)"
_SCRIPT_BP = ("Zul'Farrak Zum'rah: the script's base point (a percent of reference health, DungeonKit::RefFlatOn with "
              "the boss as the owner)")

# --- constants (ZumrahLogic.h; lib/test_zul_farrak_zumrah.py pins each) -----------------------------------------------

REND_CAST_MS = 2000             # Tune::kRendCastMs
WALK_MS = 15000                 # Tune::kWalkMs
WALK_SPEED_PCT = 40             # Tune::kWalkSpeedPct
SPIRIT_WORLD_VALUE = 1          # kSpiritWorldValue (the looks' invisibility amount)
SPIRIT_SIGHT_VALUE = 10         # kSpiritSightValue (the walker's detection amount)
VOLLEY_CAST_MS = (3000, 2000)   # Tune::kVolleyCastMs (normal, heroic)
BOLT_CAST_MS = 3000             # Tune::kBoltCastMs
WARD_PCT_PER_BOUND = 10         # Tune::kWardPctPerBound.normal (the base point; heroic and past 4: the script)
STACK_CEILING = 99              # kGatheredMaxStacks / kWardMaxStacks of boss_zumrah_rework.cpp
SOUL_SCALE = 1.75               # Tune::kSoulScale, inside LOST_SOUL_SCALE_RANGE
assert LOST_SOUL_SCALE_RANGE[0] <= SOUL_SCALE <= LOST_SOUL_SCALE_RANGE[1]

# Stock looks the copies keep (Shadow Bolt 12739's and Shadow Bolt Volley 15245's own SpellVisual).
_SV_SHADOW_BOLT = ZR_SHADOW_BOLT
_SV_VOLLEY = ZR_VOLLEY

# Stock icons (Spell.dbc SpellIconID of the named spell; read from the stock DBC 2026-11-25).
_ICON_REND = 2308               # Return to the Spirit Realm 44035
_ICON_GHOST = 143               # Ghostly 16713, Spirit Particles 28126 / 18951
_ICON_SHADOW_BOLT = 213         # Shadow Bolt 12739, Shadow Bolt Volley 15245
_ICON_SPIRIT_BURST = 87         # Spirit Burst 24050
_ICON_WARD = 2287               # Spirit Shield 40322
_ICON_WAIL = 1987               # Wailing Souls 68873
_ICON_GRAVE = 61                # Raise Dead 17475
_ICON_SKELETON = 120            # Ward of Zum'rah 11086

_AURA_MOD_INVISIBILITY = 18             # SpellAuraDefines.h SPELL_AURA_MOD_INVISIBILITY
_AURA_MOD_INVISIBILITY_DETECT = 19      # SPELL_AURA_MOD_INVISIBILITY_DETECT
_TARGET_UNIT_TARGET_ENEMY = 6
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15          # the whitemane.py recipe: movement, pushback, interrupt, auto-attack
_ATTR1_IS_CHANNELED = 0x00000004
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000  # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_SCHOOL_MASK_ALL = 127
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000  # SharedDefines.h: the cast leaves his swing timer alone
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
    AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
    AttributesEx4=ATTR4_NO_CAST_LOG,
)


def _script_hit(spell_id: int, name: str, desc: str, notes: str, *, icon: int, visual: int = 0):
    """A Shadow hit whose amount the script sets as the base point (CastSpellExtraArgs::AddSpellBP0; DieSides 0, so the
    amount is exact): triggered, always hits, cannot crit, ignores LoS and the caster's modifiers, DmgClass magic."""
    raw = kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, DefenseType=_DEFENSE_MAGIC, **_HIT_ATTRS)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_BP)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _look_aura(spell_id: int, name: str, notes: str, *, visual: int, icon: int, effect: Effect):
    """A lasting look or state the script puts on a unit (or the unit on itself): no buff icon, no log, not
    dispellable, until removed (the unit despawns)."""
    raw = kit_raw(instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=100.0, duration_ms=-1, effects=[effect], spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


# --- ZR1 to ZR3: Spirit Rend, Between Worlds, the Empty Vessel ------------------------------------------------------

spirit_rend_213920 = cast_bar(
    213920, 'Spirit Rend', REND_CAST_MS, 'Tears a spirit from its body.',
    f'{_D3}, ZR1: 15 s, then every 25 s on a fixed grid, a 2 s bar on himself with emote line 3 naming the walker '
    '(everyone in turn, the tank and the healer included). Not interruptible (InterruptFlags 0, PreventionType 0) and '
    'Arcane: a kicked Volley or Bolt (Shadow) locks that school, never this bar (rule 24). At its end the walk starts '
    '(213921, 213922). Return to the Spirit Realm 44035\'s SV 7964.',
    icon=_ICON_REND, visual=ZR_REND, school=School.ARCANE,
)

between_worlds_213921 = spell(
    id=213921, name='Between Worlds', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=WALK_MS + 500,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_INVISIBILITY_DETECT,
                    base_points=SPIRIT_SIGHT_VALUE, die_sides=0, misc_value=ZR_INVIS_TYPE,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_INCREASE_SPEED, base_points=WALK_SPEED_PCT,
                    die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GHOST,
    notes=f'{_D3}, ZR2: the walker for 15 s (the script ends the walk on its own clock and removes it; the 0.5 s more '
          'is a margin): sees the spirit world (invisibility detection type 11 at 10, over the 1 the souls, the '
          'Bound Dead, the grave looks and BM-1\'s walker-only markers carry), runs 40% faster, wears the ghost look '
          '(Ghostly 16713\'s SV 886). Keeps the full kit (ruling 19): no pacify, silence, phase or immunity (appendix '
          'B 2.3: the living side is kept off by script). A debuff so it cannot be clicked off; not dispellable; '
          'NO_IMMUNITIES, so a bubble, Ice Block or Cloak of Shadows neither refuses nor strips it (R-1-A m1: the '
          'walk would end). Leaving the map drops it (the walk ends).',
    raw_overrides=kit_raw('Tears the spirit from the body.',
                          'Walking the spirit world: gather the lost souls and free the bound dead.', instant=True,
                          SpellVisualID_1=ZR_GHOST, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

empty_vessel_213922 = spell(
    id=213922, name='Empty Vessel', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=ZR_EMPTY_VESSEL_AURA, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GHOST,
    notes=f'{_D3}, ZR3: the walker casts it on the husk 301010 at the walk\'s start (triggered): aura 247 (clone '
          'caster, the mechanism of Clone Me! 45204) gives the husk the walker\'s display and the mirror-image flag, '
          'so the client draws their look and gear. Gone with the husk at the walk\'s end.',
    raw_overrides=kit_raw(instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

spirit_tether_213923 = spell(
    id=213923, name='Spirit Tether', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=100.0, duration_ms=WALK_MS,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GHOST,
    notes=f'{_D3}, ZR3: the tether from the husk to the walker: never cast; the script sets the husk\'s channel fields '
          '(UNIT_FIELD_CHANNEL_OBJECT = the walker, UNIT_CHANNEL_SPELL = this id), so the beam follows the walker '
          'anywhere with no range check, and clears them at the walk\'s end. Spirit Walker Channel 36378\'s SV 8283.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=ZR_TETHER,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- ZR4 to ZR7: the souls, the Bound Dead, the Ward of the Dead ----------------------------------------------------

spirit_world_213924 = _look_aura(
    213924, 'Spirit World',
    f'{_D3}, ZR4 / ZR6 / ZR14 (s7 #48 A): invisibility type 11 at 1 on every Lost Soul, Bound Dead and grave look: '
    'only a walker (213921, detection 10) or a game master sees them. Type 11 is free on this server (appendix B 2.3: '
    'stock 50008 / 49962 only, no map 209 spawn).',
    visual=0, icon=_ICON_GHOST,
    effect=Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_INVISIBILITY, base_points=SPIRIT_WORLD_VALUE,
                  die_sides=0, misc_value=ZR_INVIS_TYPE, implicit_target_a=TARGET_UNIT_CASTER),
)

lost_soul_213925 = _look_aura(
    213925, 'Lost Soul',
    f'{_D3}, ZR4: the soul\'s lasting look on its wisp (Spirit Particles (purple) 28126\'s SV 7566), from its rise to '
    'its end (gathered, bound or cleaned up).',
    visual=ZR_LOST_SOUL_STATE, icon=_ICON_GHOST,
    effect=Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER),
)

bound_dead_213926 = self_visual(
    213926, 'Bound Dead', ZR_BIND,
    f'{_D3}, ZR6: a soul binds at the cauldron: the Bound Dead\'s look as it appears (Summon Voodoo Spirit 24052\'s SV '
    '7181), with emote line 4 at most every 10 s.',
    icon=_ICON_GHOST, school=School.SHADOW,
)

spirit_burst_213927 = self_visual(
    213927, 'Spirit Burst', ZR_FREED,
    f'{_D3}, ZR6: a Bound Dead freed by a walker\'s two souls (it stays 1.5 s for the look); heroic ZR12: a Soul Echo '
    'lands (on the grave stalker, in our world). Spirit Burst 24050\'s SV 7180.',
    icon=_ICON_SPIRIT_BURST, school=School.SHADOW,
)

gathered_souls_213928 = spell(
    id=213928, name='Gathered Souls', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=WALK_MS + 500,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GHOST,
    notes=f'{_D3}, ZR5: a stack on the walker for every soul touched (DungeonKit::AddStacks); two are spent freeing a '
          'Bound Dead; the rest are lost when the walk ends (the script removes it). The Bound Dead\'s Soaks read it '
          '(eligibility: 2 stacks). A debuff so it cannot be clicked off; not dispellable; NO_IMMUNITIES (a class '
          'immunity never strips the souls). Spirit Particles (green) 18951\'s SV 5101.',
    raw_overrides=kit_raw('Carrying lost souls.', 'Carrying $u lost souls. Bring two to a Bound Dead to free it.',
                          instant=True, CumulativeAura=STACK_CEILING, SpellVisualID_1=ZR_GATHERED,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

ward_of_the_dead_213929 = spell(
    id=213929, name='Ward of the Dead', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=-WARD_PCT_PER_BOUND, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_WARD,
    notes=f'{_D3}, ZR7: a stack on him for every Bound Dead standing (DungeonKit::AddStacks); after each change the '
          'script sets the effect to WardReductionPct: 10% a stack to 40% on normal (capped at 4 Bound Dead), heroic '
          '15% to 60%, then each one past four cuts 15% of what is left (ruling 45: 66% at 5, 71% at 6). Never '
          'immunity. Not dispellable; gone on his reset, evade or death. Spirit Shield 40322\'s SV 7519.',
    raw_overrides=kit_raw('Shielded by the dead he has bound.', 'Shielded by the dead he has bound.', instant=True,
                          CumulativeAura=STACK_CEILING, SpellVisualID_1=ZR_WARD_SHIELD, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- ZR9 and ZR10: Shadow Bolt Volley and Shadow Bolt ---------------------------------------------------------------


def _volley_cast(spell_id: int, cast_ms: int, which: str):
    return spell(
        id=spell_id, name='Shadow Bolt Volley', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=cast_ms,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_SHADOW_BOLT,
        notes=f'{_D3}, ZR9 ({which}): 8 s, then every 12 to 16 s (never sooner than 10 s after the last: one 10 s '
              f'interrupter), a {cast_ms // 1000} s cast on himself, never started into a Spirit Rend. Kickable '
              '(InterruptFlags 15, PreventionType silence; his immunity set 1972 holds neither): the descriptor\'s '
              'interrupt list. Landed (OnSpellCast), 213932 hits every player within 30 yd but the walker. Does not '
              'reset his swing. Shadow Bolt Volley 15245\'s SV 2318.',
        raw_overrides=kit_raw('Hurls missiles of dark magic at everyone nearby.',
                              InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                              DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=_SV_VOLLEY, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


volley_213930 = _volley_cast(213930, VOLLEY_CAST_MS[0], 'normal')
volley_heroic_213931 = _volley_cast(213931, VOLLEY_CAST_MS[1], 'heroic')

volley_hit_213932 = _script_hit(
    213932, 'Shadow Bolt Volley', 'A missile of dark magic.',
    f'{_D3}, ZR9: the landed Volley on every player within 30 yd of him but the walker: 20% (heroic 35%) of the '
    'reference row, the tank row on the tank (the script\'s base point). No Weakened (the soft penalty, SP section 6). '
    'Shadow Bolt Volley 15245\'s SV 2318.',
    icon=_ICON_SHADOW_BOLT, visual=_SV_VOLLEY,
)

shadow_bolt_213933 = spell(
    id=213933, name='Shadow Bolt', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=BOLT_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BP)],
    spell_icon_id=_ICON_SHADOW_BOLT,
    notes=f'{_D3}, ZR10: 1 s, then every 3 to 4 s where it ends before the next Rend and Volley (else skipped), a 3 s '
          'cast on his target (a random living player while the target walks or stands off the bowl): 8% of the '
          'reference row, the tank row on the tank (the script\'s base point; heroic the same percent of the heroic '
          'row, designer question 2). Kickable (InterruptFlags 15, PreventionType silence), not on the interrupt list '
          '(a kick is a reward: it also locks the Volley\'s school). 100 yd and no line of sight: he never moves. '
          'Does not reset his swing. The copy of 12739 (its SV 64 and missile speed 24).',
    raw_overrides=kit_raw('Hurls a bolt of dark magic at an enemy, inflicting Shadow damage.',
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=_SV_SHADOW_BOLT, Speed=24.0,
                          AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=(ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT
                                         | _ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- ZR8: the Skeletons ---------------------------------------------------------------------------------------------

skeletal_strike_213934 = _script_hit(
    213934, 'Skeletal Strike', 'A cold blow from the grave.',
    f'{_D3}, ZR8: a Skeleton of Zum\'rah\'s hit every 2 s in melee reach: 3% (heroic 5%) of the reference row (1.5% / '
    '2.5% a second), the tank row on the tank, with Zum\'rah as the owner of the percent. On the husk it lands on the '
    'walker (shared health). Shadow, so armor never changes the percent. No visual (the Skeleton swings).',
    icon=_ICON_SKELETON,
)

# --- ZR11 to ZR14: heroic -------------------------------------------------------------------------------------------

soul_burn_213935 = _script_hit(
    213935, 'Soul Burn', 'The gathered soul burns its bearer.',
    f'{_D3}, ZR11 (heroic): 6% of the reference row on the walker for every soul gathered (the tank row on a tank '
    'walker). The walker\'s health is shared with the husk, so the living side heals it.',
    icon=_ICON_GHOST,
)

soul_echo_213936 = resolve_copy(
    213936, 'Soul Echo', School.SHADOW, 'A gathered soul crashes into the living world.',
    f'{_D3}, ZR12 (heroic): every soul gathered drops a 5 yd Circle AoE under a random living player, the tank '
    'included, never the walker, 2 s: 35% of the reference row (the tank row on the tank) and Weakened on the living '
    'in it (Eligible: the living). Uncapped (ruling 20). Copy of the resolve spell 205006 (Shadow). Spirit Burst\'s SV '
    '7180 on every player hit; the grave stalker shows the burst where it lands.',
    icon=_ICON_SPIRIT_BURST, visual=ZR_FREED,
)

restless_wail_213937 = resolve_copy(
    213937, 'Restless Wail', School.SHADOW, 'The bound dead wail at the walker.',
    f'{_D3}, ZR13 (heroic): every Bound Dead within 15 yd of the walker, every 4 s (a second apart): a 6 yd Circle AoE '
    'on the walker\'s spot, 1.5 s: 40% (the tank row on a tank walker) and Weakened on the walker only, drawn only in '
    'the spirit world (BM-1 SeenOnlyWith 11). Copy of the resolve spell 205006 (Shadow). Wailing Souls 68873\'s SV '
    '14508 (gap 11: checked in game).',
    icon=_ICON_WAIL, visual=ZR_WAIL,
)

grasping_graves_213938 = resolve_copy(
    213938, 'Grasping Graves', School.SHADOW, 'The graves reach for the walker.',
    f'{_D3}, ZR14 (heroic): every 3 s of a walk, two graves within 20 yd of the walker (fewer in range: those, s7 #29 '
    'A): 6 yd Circle AoEs, 1.5 s: 40% (the tank row on a tank walker) and Weakened on the walker only, drawn only in '
    'the spirit world. Copy of the resolve spell 205006 (Shadow). Raise Dead 17475\'s SV 634.',
    icon=_ICON_GRAVE, visual=ZR_GRAVE,
)

grave_eruption_213939 = self_visual(
    213939, 'Grasping Graves', ZR_GRAVE,
    f'{_D3}, ZR14 (heroic): the grave\'s look as its circle lands, on the grave stalker 301013 in the spirit world '
    '(213924). Raise Dead 17475\'s SV 634.',
    icon=_ICON_GRAVE, school=School.SHADOW,
)

# --- the adds -------------------------------------------------------------------------------------------------------

# 301010 Empty Vessel: friendly to players (495 = FACTION_ESCORTEE_N_FRIEND_ACTIVE: players' group, enemy of the
# monsters; FactionTemplate.dbc 2026-11-25), so no player can attack it and the Skeletons (16) can. Selectable.
empty_vessel_301010 = creature_template(
    301010, 'Empty Vessel', **{**KIT_CREATURE, 'faction': 495, 'minlevel': 46, 'maxlevel': 46, 'rank': 0,
                               'unit_class': 1, 'type': 7, 'unit_flags': 0, 'DamageModifier': 0.0,
                               'HealthModifier': 1.0, 'lootid': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': 0x40,
                               'detection_range': 0.0, 'ScriptName': 'npc_zf_empty_vessel'},
)
creature_model(301010, display_id=DISPLAY_INVISIBLE_STALKER)

lost_soul_301011 = creature_template(
    301011, 'Lost Soul', **{**KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0, 'unit_class': 1, 'type': 6,
                            'ScriptName': 'npc_zf_lost_soul'},
)
creature_model(301011, display_id=DISPLAY_LOST_SOUL, scale=SOUL_SCALE)

bound_dead_301012 = creature_template(
    301012, 'Bound Dead', **{**KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0, 'unit_class': 1, 'type': 6,
                             'ScriptName': 'npc_zf_bound_dead'},
)
creature_model(301012, display_id=DISPLAY_BOUND_DEAD)

grave_stalker_301013 = creature_template(
    301013, "Zul'Farrak Grave Stalker", **{**KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0, 'unit_class': 1,
                                           'type': 10, 'flags_extra': 0x40 | 0x80,
                                           'ScriptName': 'npc_zf_grave_stalker'},
)
creature_model(301013, display_id=DISPLAY_INVISIBLE_STALKER)
