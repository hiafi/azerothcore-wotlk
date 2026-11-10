"""
Stratholme build: the shared spells of the reworked Stratholme (slice 206400-206419, modules/mod-dungeon-bosses
StratholmeRework.h `kSpellsShared`). Owned by the orchestrator; written for WP-KT-2 (handoff s3.3, s3.11 #15). Every
boss's own spells live in its own file of this package, inside its slice.

  206400  Crossed the Line  the lethal walls' strike (The Unforgiven's Cordon UF12, Galford's Pyre and north wall
                            GF10; the kit's DungeonKit::LethalWall): an outright kill (user ruling, F-2):
                            SPELL_EFFECT_INSTAKILL, so no absorb, shield or damage-taken reduction saves the target,
                            and the kit's spell_dungeon_lethal_strike kills whoever is still standing after the hit.
                            NO_IMMUNITIES (Divine Shield and Ice Block do not stop a wall), ALWAYS_HIT, ignores caster
                            modifiers and resistances, no LoS, no threat, not reflected or redirected.
                            TARGET_UNIT_TARGET_ENEMY: the kit casts it on each player or pet inside the wall (or across
                            it since the last tick), from the nearest striker (a footman, a Pyre stalker) or the boss,
                            with the boss as original caster.
  206401-206419 spare (Terrified and the shared cast bars of handoff s3.3, if a WP needs them).
"""

from lib.dsl import Effect, School
from lib.dsl.dungeon_kit import (
    ATTR0_NO_ACTIVE_DEFENSE,
    ATTR0_NO_IMMUNITIES,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR3_NOT_A_PROC,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_TARGET_ENEMY,
    kit_raw,
)
from lib.dsl.registry import scripted_by, spell

_SV_JUDGEMENT_OF_LIGHT = 5651   # Judgement of Light 20271's look on the target (unconfirmed in game; V may repick)
_ICON_JUDGEMENT_OF_LIGHT = 205  # Judgement of Light 20271's icon
_DEFENSE_MAGIC = 1
_EFFECT_INSTAKILL = 1           # SPELL_EFFECT_INSTAKILL (SharedDefines.h; not in lib/dsl's EffectType subset)

crossed_the_line_206400 = spell(
    id=206400, name='Crossed the Line', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    attributes=ATTR0_NO_ACTIVE_DEFENSE | ATTR0_NO_IMMUNITIES,
    effects=[Effect(type=_EFFECT_INSTAKILL, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_JUDGEMENT_OF_LIGHT,
    notes='Stratholme WP-KT-2 (handoff s3.11 #15): the lethal walls\' strike (The Unforgiven\'s Cordon UF12, '
          'Galford\'s Pyre and north wall GF10; DungeonKit::LethalWall). An outright kill (user ruling, F-2): '
          'SPELL_EFFECT_INSTAKILL (no absorb or reduction applies) and spell_dungeon_lethal_strike kills a survivor '
          'after the hit; NO_IMMUNITIES, ALWAYS_HIT, IGNORE_CASTER_MODIFIERS, NO_CAST_LOG (cannot be resisted), no '
          'LoS, cannot crit, no threat, not reflected or redirected; DefenseType magic. TARGET_UNIT_TARGET_ENEMY: the '
          'kit casts it triggered on each victim. Judgement of Light 20271\'s SV 5651 and icon 205.',
    raw_overrides=kit_raw('Crossing the line is death.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          SpellVisualID_1=_SV_JUDGEMENT_OF_LIGHT,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(crossed_the_line_206400, 'spell_dungeon_lethal_strike')
