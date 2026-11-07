"""
Deadmines Pilot WP-B1: Rhahk'Zor, the boss-kit Watchman and Evoker
(.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.4 rows RZ, s3.5 row B1; build spec
docs/dungeons/deadmines-rework.md "Rhahk'Zor"). WP-B1 owns this file (its spells: 205210-205229 only;
modules/mod-dungeon-bosses RhahkZorLogic.h names the same ids).

- 644 Rhahk'Zor: bound to boss_rhahk_zor_rework (SmartAI off), normal health 14.2k (HealthModifier 31.5); keeps
  his stock immunities -159 (handoff s7 #5). Heroic 320k is deadmines.py's override.
- 300420 Watchman, 300421 Evoker: elite copies of 1725 / 1729 at level 19, about 2.4k on normal (warrior base 449 x
  5.35 = 2,402; mage base 379 x 6.35 = 2,407; the build spec's "about 5.3" is the warrior base), heroic 80k
  (deadmines.py `extra=` + `overrides`). Stock loot, gold, models and flags copied; DamageModifier 1.7 (the stock
  Defias elites'). WP-B1's SQL points spawns 79165 and 79167 at them; equipment rows are in WP-K's SQL rev.

Spells (RZ ids are the build spec's). The registry's resolve copies (205210, 205213, 205216) carry the attribute set
of mod-boss-mechanics' 205001 (source/npcs/boss_mechanics.py documents every bit) and are bound to its resolve
script, so they only rename the hit in the combat log; the shape, damage and Weakened stay the registry's.

  205210  Cave In            RZ1 / RZ10 the circle impact (registry resolve copy, Physical). Also bound to
                             spell_dm_rhahkzor_cave_in: a player is hit once per wave however many circles of
                             that wave they stand in (DM RZ1 "once per player per wave").
  205211  Cave In Tremor     RZ2 the room shake: every player within 100 yd of the boss, 5% Physical
                             (spell_dm_rhahkzor_ref_flat sets DeadminesKit::RefFlat). Unavoidable: the resolve
                             attribute set (no active defense, always hit, cannot crit, ignores caster modifiers).
  205212  Cave In            RZ1 the falling rocks: a 2 s persistent area aura at each landed circle (Cave In
                             36240's SpellVisual 8455 has only a PersistentAreaKit, so the look needs a dynamic
                             object). Its DUMMY aura is hidden (DO_NOT_DISPLAY) and does nothing.
  205213  Rubble             RZ3 (heroic) the lingering patch tick (registry resolve copy, Physical).
  205214  Whirlwind          RZ4 the 2 s cast bar (no effect; not interruptible).
  205215  Whirlwind          RZ4 the 4 s spin on the boss: a DUMMY aura with Bladestorm 46924's SpellVisual 10704
                             (the script roots him and holds his swings while it lasts). Fallback look if the ogre
                             does not play it: SV 8377 (NPC Whirlwind 13736, Whirlwind_State_Base).
  205216  Whirlwind          RZ4 the spin tick (registry resolve copy, Physical).
  205217  Whirlwind          RZ4 (heroic) the knockback rider of every tick: KNOCK_BACK from the marker (centered
                             on the boss), 12 yd/s out, 5 yd/s up (about 6 yd).
  205218  Spotted            RZ10 (heroic) the 1.5 s mark on every player the Watchman calls (Hunter's Mark 1130's
                             SpellVisual 3239, copied). DUMMY only.
  205219  Fireball Volley    RZ8 (heroic) the Evoker's 3 s cast: 40% Fire to every player within 100 yd
                             (spell_dm_rhahkzor_ref_flat), interruptible (InterruptFlags 15, PreventionType silence),
                             Fireball Volley 11988's SpellVisual 2437 (missiles). Ignores caster modifiers, can crit
                             (DM RZ8: "Fire damage, so it can crit a tank").
  205220-205229 spare.

Stock spells kept (handoff s7 #3, DD scales them on heroic): Slam 6304 (stun cut to 1.5 s by the script), Shoot
6660, Flamestrike 11829, Fireball 11839, Quick Flame Ward 4979, Frost Armor 12544.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TEXT_MASKS,
)

creature_template_columns(644, ScriptName='boss_rhahk_zor_rework', AIName='', HealthModifier=31.5)

watchman_300420 = creature_template(
    300420, 'Defias Watchman', **{**KIT_CREATURE, 'minlevel': 19, 'maxlevel': 19, 'rank': 1, 'unit_class': 1,
                                  'unit_flags': 32768, 'HealthModifier': 5.35, 'DamageModifier': 1.7,
                                  'ExperienceModifier': 1.25, 'lootid': 1725, 'pickpocketloot': 1725, 'skinloot': 0,
                                  'mingold': 7, 'maxgold': 50,
                                  'difficulty_entry_1': 310025, 'ScriptName': 'npc_dm_watchman'},
)
creature_model(300420, display_id=184)

evoker_300421 = creature_template(
    300421, 'Defias Evoker', **{**KIT_CREATURE, 'minlevel': 19, 'maxlevel': 19, 'rank': 1, 'unit_class': 8,
                                'unit_flags': 32832, 'HealthModifier': 6.35, 'ManaModifier': 2.0,
                                'DamageModifier': 1.7, 'ExperienceModifier': 1.25, 'lootid': 1729,
                                'pickpocketloot': 1729, 'skinloot': 0, 'mingold': 23, 'maxgold': 162,
                                'difficulty_entry_1': 310026, 'ScriptName': 'npc_dm_evoker'},
)
creature_model(300421, display_id=2318, idx=0)
creature_model(300421, display_id=2319, idx=1)

# --- spells (205210-205229) ----------------------------------------------------------------------------------------

_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_FLAG_DEST_LOCATION = 0x40

_ATTR0_DO_NOT_DISPLAY = 0x00000080      # hidden aura (no buff icon)
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

_SV_CAVE_IN_ROCKS = 8455        # Cave In 36240 (PersistentAreaKit: Smash_Impact_Chest)
_SV_BLADESTORM = 10704          # Bladestorm 46924 (StateKit: warrior_bladestorm)
_SV_HUNTERS_MARK = 3239         # Hunter's Mark 1130 (StateKit: HuntersMark_Impact_Head)
_SV_FIREBALL_VOLLEY = 2437      # Fireball Volley 11988 (fire hands, Fireball missile)

_ICON_CAVE_IN = 132             # Cave In 36240
_ICON_WHIRLWIND = 83            # Whirlwind 1680
_ICON_HUNTERS_MARK = 538        # Hunter's Mark 1130
_ICON_FIREBALL = 185            # Fireball Volley 11988

_RESOLVE_NOTE = ('mod-boss-mechanics: the damage is set per target by the resolve SpellScript (OnEffectLaunchTarget '
                 'SetEffectValue) from the reference-health provider')
_REF_FLAT_NOTE = ('Deadmines Pilot: the damage is set per target by spell_dm_rhahkzor_ref_flat (OnEffectLaunchTarget '
                  'SetEffectValue = DeadminesKit::RefFlat, a percent of the reference health row)')

# The resolve attribute set (source/npcs/boss_mechanics.py, 205001-205007): no active defense, no redirection, no
# reflection, no threat, ignore LoS, cannot crit, NOT_A_PROC, always hit, ignore caster modifiers, DefenseType 1.
_RESOLVE_ATTRS = {
    'Attributes': _ATTR0_NO_ACTIVE_DEFENSE,
    'AttributesEx': _ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
    'AttributesEx2': _ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
    'AttributesEx3': _ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
    'AttributesEx4': ATTR4_NO_CAST_LOG,
    'DefenseType': 1,
}


def _raw(desc: str, aura_desc: str = '', instant: bool = True, **more) -> dict:
    raw = {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'Description_Lang_enUS': desc,
           'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more}
    if instant:
        raw['CastingTimeIndex'] = 1     # stock non-ranged instants (custom-spells.md)
    return raw


def _area_damage(spell_id: int, name: str, icon: int, desc: str, note: str, potency_note: str):
    """An instant Physical SCHOOL_DAMAGE on every enemy within 100 yd of the caster, its value set by a SpellScript;
    the resolve attribute set."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                        implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                        potency_excluded=potency_note)],
        spell_icon_id=icon, notes=note, raw_overrides=_raw(desc, **_RESOLVE_ATTRS),
    )


def _resolve_copy(spell_id: int, name: str, icon: int, desc: str, rz: str):
    entry = _area_damage(
        spell_id, name, icon, desc,
        f'Deadmines Pilot WP-B1, {rz}: a copy of the registry resolve spell 205001 (Physical) under its own name, '
        'bound to spell_boss_mechanics_resolve (the mechanic shape filters the 100 yd target list; the registry sets '
        'the damage). Attribute set as 205001 (boss_mechanics.py).',
        _RESOLVE_NOTE)
    scripted_by(entry, 'spell_boss_mechanics_resolve')
    return entry


cave_in_205210 = _resolve_copy(205210, 'Cave In', _ICON_CAVE_IN, 'The ceiling comes down.', 'RZ1 / RZ10')
scripted_by(cave_in_205210, 'spell_dm_rhahkzor_cave_in')

cave_in_tremor_205211 = _area_damage(
    205211, 'Cave In Tremor', _ICON_CAVE_IN, 'The whole room shakes.',
    'Deadmines Pilot WP-B1, RZ2: the room shake as each Cave In wave lands, 5% Physical to every player within '
    '100 yd of Rhahk\'Zor (players only; the value is DeadminesKit::RefFlat). Unavoidable: the resolve attribute '
    'set. Cast by the boss on himself, triggered.',
    _REF_FLAT_NOTE)
scripted_by(cave_in_tremor_205211, 'spell_dm_rhahkzor_ref_flat')

cave_in_rocks_205212 = spell(
    id=205212, name='Cave In', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=2000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                    implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=5.0)],
    spell_icon_id=_ICON_CAVE_IN,
    notes='Deadmines Pilot WP-B1, RZ1: the falling rocks at a landed Cave In circle (cast at the point by the boss, '
          'triggered). Cave In 36240\'s SpellVisual 8455 has only a PersistentAreaKit (Smash_Impact_Chest), so the '
          'look needs a dynamic object: 2 s, 5 yd like the circle. Its DUMMY aura is hidden and does nothing.',
    raw_overrides=_raw('Falling rocks.', SpellVisualID_1=_SV_CAVE_IN_ROCKS, Targets=_TARGET_FLAG_DEST_LOCATION,
                       AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                       AttributesEx4=ATTR4_NO_CAST_LOG),
)

rubble_205213 = _resolve_copy(205213, 'Rubble', _ICON_CAVE_IN, 'Standing in it hurts.', 'RZ3 (heroic)')

whirlwind_cast_205214 = spell(
    id=205214, name='Whirlwind', school=School.NORMAL, cast_time_ms=2000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_WHIRLWIND,
    notes='Deadmines Pilot WP-B1, RZ4: Rhahk\'Zor\'s 2 s Whirlwind cast bar (the shape of WP-K\'s 205200 Preparing, '
          'named for the mechanic). DUMMY on the caster, no effect; not interruptible (InterruptFlags 0, '
          'PreventionType 0): the registry circle registered beside it owns the hit.',
    raw_overrides=_raw('Gets ready to spin.', instant=False, InterruptFlags=0, PreventionType=0,
                       AttributesEx4=ATTR4_NO_CAST_LOG),
)

whirlwind_spin_205215 = spell(
    id=205215, name='Whirlwind', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=4000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_WHIRLWIND,
    notes='Deadmines Pilot WP-B1, RZ4: the 4 s spin on Rhahk\'Zor (cast on himself, triggered, as the cast bar '
          'ends). A shown DUMMY aura carrying Bladestorm 46924\'s SpellVisual 10704; the script roots him and holds '
          'his swings while it lasts; the registry circle on him owns the ticks. Fallback look: SV 8377.',
    raw_overrides=_raw('Spinning. Lasts $d.', 'Spinning.', SpellVisualID_1=_SV_BLADESTORM,
                       AttributesEx4=ATTR4_NO_CAST_LOG),
)

whirlwind_205216 = _resolve_copy(205216, 'Whirlwind', _ICON_WHIRLWIND, 'A spinning hammer.', 'RZ4')

whirlwind_knockback_205217 = spell(
    id=205217, name='Whirlwind', school=School.NORMAL, attributes=ATTR0_NO_IMMUNITIES, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.KNOCK_BACK, base_points=49, misc_value=120,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_WHIRLWIND,
    notes='Deadmines Pilot WP-B1, RZ4 (heroic): the knockback rider of every Whirlwind tick. The registry casts '
          'riders from the resolve caster (the marker on the boss) with the boss as original caster, so KNOCK_BACK '
          'throws the player away from Rhahk\'Zor: MiscValue 120 = 12 yd/s out, BasePoints 49 + DieSides 1 = 5 yd/s '
          'up, about 6 yd. TARGET_UNIT_TARGET_ANY, ignores LoS.',
    raw_overrides=_raw('Thrown back.', AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                       AttributesEx4=ATTR4_NO_CAST_LOG),
)

spotted_205218 = spell(
    id=205218, name='Spotted', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=1500,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HUNTERS_MARK,
    notes='Deadmines Pilot WP-B1, RZ10 (heroic): the Watchman\'s mark on every player he calls for the second Cave In '
          'wave, 1.5 s (the warning). A shown DUMMY debuff carrying Hunter\'s Mark 1130\'s SpellVisual 3239 '
          '(copied); NO_IMMUNITIES so it shows through Divine Shield. Dispel none. Aura text number-free.',
    raw_overrides=_raw('Spotted by the Watchman: the ceiling comes down here next. Lasts $d.',
                       'Spotted by the Watchman: the ceiling comes down here next.',
                       SpellVisualID_1=_SV_HUNTERS_MARK, AttributesEx=_ATTR1_NO_THREAT,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

fireball_volley_205219 = spell(
    id=205219, name='Fireball Volley', school=School.FIRE, cast_time_ms=3000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                    potency_excluded=_REF_FLAT_NOTE)],
    spell_icon_id=_ICON_FIREBALL,
    notes='Deadmines Pilot WP-B1, RZ8 (heroic): the Evoker\'s expected interrupt, a 3 s cast, then 40% Fire to every '
          'player within 100 yd (players only; DeadminesKit::RefFlat; ignores caster modifiers, so it is exactly the '
          'reference number; can crit). InterruptFlags 15 and PreventionType silence (the M5 interruptible stand-in '
          'pair). Fireball Volley 11988\'s SpellVisual 2437, Speed 24 as stock. Ignores LoS: "every player".',
    raw_overrides=_raw('Hurls a fireball at every enemy.', instant=False, InterruptFlags=15, PreventionType=1,
                       DefenseType=1, Speed=24.0, SpellVisualID_1=_SV_FIREBALL_VOLLEY,
                       AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(fireball_volley_205219, 'spell_dm_rhahkzor_ref_flat')
