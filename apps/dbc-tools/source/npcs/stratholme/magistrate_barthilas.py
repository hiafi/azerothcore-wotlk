"""
Stratholme build WP-S9: Magistrate Barthilas (10435), "The Epidemic"
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows BT, s3.5 row S9, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 2355-2407). WP-S9 owns this file (its spells: kSpellsBarthilas 206605-206624 in
modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; BarthilasLogic.h names the same ids).

- 10435 Magistrate Barthilas: boss_magistrate_barthilas_rework (SmartAI off; WP-S9's SQL rev drops the 19 stock rows:
  Furious Anger 16791 becomes Fever, Crowd Pummel 10887 leaves his kit, his run to the Slaughterhouse is gone; Mighty
  Blow 14099, Draining Blow 16793 and the Transformation 16794 look move into the C++), normal HealthModifier 62.696
  (180k on the level 58 warrior base 2,871), stun immune (1972; the orchestrator's ruling, handoff s7 #3: ST's -273
  differs only by its silence immunity, and Bedlam must stay kickable), INSTANCE_BIND. DamageModifier 3.5: the stock
  value (WP-S0's skeleton), now his own; WP-T tunes it. Heroic health 235k and the tier's melee are WP-H's heroic
  template (source/world/dungeons/stratholme.py).
- 300580 Plagued Grain: the grain pile / cough puddle stalker (BT5, BT10). Invisible (11686), not selectable or
  attackable, a trigger (NullCreatureAI). Summoned on a pile or puddle for its life (30 s / 45 s / 20 s) and casts the
  fog (206611) there; the script despawns it when the oldest pile dries up, and the boss's summon list on a wipe or
  his death. No heroic template (handoff s7 #15).
- 300581 Quarantine Ward: the ward stalker (BT6), two per Quarantine: the anchor of each ward's registry Stack (the
  telegraph kit's disc draws it: green Sick Ward, yellow Well Ward). Invisible, a trigger; despawned at the purge. No
  heroic template.

Spells. The cough, the grain and the purge deal their damage through dungeon copies of the mod-boss-mechanics resolve
spell (the registry's percent of the reference row; the combat log names the mechanic). Infection's ticks are the
kit's generic percent spell (spell_dungeon_refflat_periodic: the percent in hundredths in the effect's value). The
rest are auras, a kickable cast and looks:

  206605  Infection        BT1 Disease, 10 s, 4% of the reference row every 2 s (20% in all; tank row on the tank),
                           the green cloud; its expiry is the cough (spell_st_barthilas_infection), any other removal
                           (a dispel, a Sick Ward cure, a death) none
  206606  Cough            BT3 the cough's hit: resolve copy (Nature), 30% / 40% + Weakened, 8 yd around the carrier
  206607  Cough            BT3 the look on the carrier as it coughs (Plague Cloud's SV 761)
  206608  Recovered        BT3 10 s after a cough: cannot catch Infection (a buff, read by the script)
  206609  Plagued Grain    BT4 the thrown sack: a no-effect missile at the marker (Throw Sack's SV 12216, 20 yd/s)
  206610  Plagued Grain    BT4 the landing's hit: resolve copy (Nature), 30% + Weakened, 6 yd
  206611  Plagued Grain    BT5 / BT10 the fog on a pile or puddle (an area aura at the stalker; SV 10395)
  206612  Purge            BT7 the purge's hit outside both wards: resolve copy (Nature), 40%, no Weakened
  206613  Fever            BT8 his stacking buff: +5% damage (heroic +6%, spell_st_barthilas_fever) and +3% attack
                           speed a stack, no cap (CumulativeAura 255), the fight; stock Furious Anger's SV
  206614  Bedlam           BT9 heroic: the 3 s kickable cast (InterruptFlags 15, PreventionType silence)
  206615-206624 spare

Visual ids are WP-V's (._visuals), all stock; every look is unconfirmed until seen in game.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BT_CONTAGION,
    BT_FEVER,
    BT_FURIOUS_ANGER_FLASH,
    BT_GRAIN_SACK,
    BT_INFECTION,
    BT_NOXIOUS_FOG,
    DISPLAY_INVISIBLE_STALKER,
)

_BT = 'Stratholme build WP-S9 (Magistrate Barthilas)'

_DISPEL_DISEASE = 3
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127
_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_INTERRUPT_FLAGS_STANDARD = 15      # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): leaving Stratholme drops it.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_FLAGS_EXTRA_NO_XP = 0x40
_FLAGS_EXTRA_TRIGGER = 0x80

_ICON_PLAGUE_CLOUD = 1614   # Plague Cloud 3256
_ICON_DISEASE_CLOUD = 263   # Disease Cloud 12627, Noxious Cloud 21070
_ICON_CURE_DISEASE = 330    # Cure Disease 528
_ICON_SACK = 1359           # Vendor - Throw Sack To Player 56122
_ICON_FURIOUS_ANGER = 95    # Furious Anger 16791

_SCRIPT_DAMAGE = ('a percent of the reference row (hundredths in the value) through the kit\'s '
                  'spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')


def _stalker() -> dict:
    return {**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
            'flags_extra': _FLAGS_EXTRA_NO_XP | _FLAGS_EXTRA_TRIGGER, 'ScriptName': ''}


creature_template_columns(10435, **boss_columns(
    'boss_magistrate_barthilas_rework', 62.696, damage_modifier=3.5,
))

# --- Boss-kit creatures (stalkers: no heroic template, handoff s7 #15) -----------------------------------------------

grain_pile_300580 = creature_template(300580, 'Plagued Grain', **_stalker())
creature_model(300580, display_id=DISPLAY_INVISIBLE_STALKER)
ward_300581 = creature_template(300581, 'Quarantine Ward', **_stalker())
creature_model(300581, display_id=DISPLAY_INVISIBLE_STALKER)

# --- BT1 Infection, BT3 the cough ----------------------------------------------------------------------------------

infection_206605 = spell(
    id=206605, name='Infection', school=School.NATURE, dispel=_DISPEL_DISEASE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=400, die_sides=0,
                    amplitude=2000, implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_DAMAGE)],
    spell_icon_id=_ICON_PLAGUE_CLOUD,
    notes=f'{_BT} BT1: he coughs on a random player, the tank included (heroic: two), 8 s in and every 15 s; a '
          'healthy player 1 s (heroic 0.5 s) within 5 yd of a carrier catches a fresh one (BT2), as does 0.5 s in a '
          'pile or puddle and the purge (BT7). Applied by the boss (Unit::AddAura). 10 s; every 2 s 4% of the '
          'reference row (base point 400 = 4.00% in hundredths, heroic the same: EffectMiscValueB 0), the tank row '
          'on the tank, through spell_dungeon_refflat_periodic; ignores caster modifiers. Disease: a dispel ends it '
          'with no cough (the reward). Its expiry is the cough (spell_st_barthilas_infection tells the boss: the '
          'carrier Recovers, heroic leaves a puddle; the registry RunOut registered with it deals the hit). Disease '
          "Cloud 12627's SV 1712 (green flame wisps) and Plague Cloud's icon. Leaving Stratholme drops it "
          '(CHANGE_MAP).',
    raw_overrides=kit_raw('Infected with the plague. Coughs on everyone nearby when it ends.',
                          'Taking Nature damage. Stay away from others: it spreads, and the cough when it ends hits '
                          'everyone nearby.', instant=True, DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, SpellVisualID_1=BT_INFECTION),
)
scripted_by(infection_206605, 'spell_dungeon_refflat_periodic', 'spell_st_barthilas_infection')

resolve_copy(
    206606, 'Cough', School.NATURE, 'A plagued cough sprays everyone nearby.',
    f'{_BT} BT3: the cough as an infection ends, 8 yd around the carrier (a registry RunOut registered with the '
    'infection, warning the infection\'s 10 s): 30% (heroic 40%) of the non-tank row + 1 Weakened (handoff s7 #17: '
    'Weakened on heroic too) to every other player inside; each hit gives him a Fever stack. A dispel, a Sick Ward '
    "cure or the carrier's death cancels it. Resolve copy (Nature). Plague Cloud 3256's SV 761 (a green fog burst) on "
    'every player hit.',
    icon=_ICON_PLAGUE_CLOUD, visual=BT_CONTAGION,
)
self_visual(
    206607, 'Cough', BT_CONTAGION,
    f'{_BT} BT3: the carrier coughs (cast by the carrier on itself, triggered, as its infection expires). Plague '
    "Cloud 3256's SV 761. Look only.",
    icon=_ICON_PLAGUE_CLOUD, school=School.NATURE,
)
spell(
    id=206608, name='Recovered', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CURE_DISEASE,
    notes=f'{_BT} BT3: 10 s after a cough the carrier cannot catch Infection again (the script reads it: contagion, '
          'piles, puddles and wards pass over them; he coughs on them only when nobody else is left), so it never '
          'loops on one player. A buff, not dispellable (Dispel none), applied by the boss (Unit::AddAura); Bedlam '
          'infects through it. No look. Leaving Stratholme drops it (CHANGE_MAP).',
    raw_overrides=kit_raw('Recovering from the plague.', 'Cannot catch Infection.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- BT4 Plagued Grain, BT5 the pile, BT10 the cough puddle -----------------------------------------------------------

spell(
    id=206609, name='Plagued Grain', school=School.NATURE, attributes=ATTR0_DO_NOT_LOG, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_SACK,
    notes=f'{_BT} BT4: the thrown sack, a no-effect missile he casts at the marker (triggered; gap 16). Vendor - Throw '
          "Sack To Player 56122's SV 12216 (a sack missile). Speed 20 yd/s = BarthilasLogic.h kGrainSackSpeed: the "
          'script launches it so it lands as the marker resolves.',
    raw_overrides=kit_raw('Hurls a sack of plagued grain.', SpellVisualID_1=BT_GRAIN_SACK, Speed=20.0,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          CastingTimeIndex=1),
)
resolve_copy(
    206610, 'Plagued Grain', School.NATURE, 'A sack of plagued grain bursts.',
    f'{_BT} BT4: the landing, 6 yd at a random player\'s spot (2 s marker): 30% of the non-tank row + 1 Weakened, '
    "through the registry. Resolve copy (Nature). Plague Cloud's SV 761 on every player hit; the pile's fog shows "
    'where it landed.',
    icon=_ICON_SACK, visual=BT_CONTAGION,
)
spell(
    id=206611, name='Plagued Grain', school=School.NATURE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=45000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                    implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=5.0)],
    spell_icon_id=_ICON_DISEASE_CLOUD,
    notes=f'{_BT} BT5 / BT10: the fog on a grain pile (5 yd, 30 s / heroic 45 s) or a heroic cough puddle (4 yd, 20 '
          's), visual only. The pile stalker 300580 casts it (triggered) at its own spot (CastSpell(x, y, z)): a '
          "dynamic object with Noxious Cloud 21070's SV 10395 (GreenRadiationFog; its size is unmeasured). Its DUMMY "
          'aura does nothing. The stalker\'s despawn (its life, the pile cap, the wipe) takes the fog with it; the '
          'kit\'s PuddleField owns the union, the markers and the 0.5 s catch.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=BT_NOXIOUS_FOG, Targets=_TARGET_FLAG_DEST_LOCATION,
                          InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- BT7 the purge ----------------------------------------------------------------------------------------------------

resolve_copy(
    206612, 'Purge', School.NATURE, 'The quarantine purges everyone outside the wards.',
    f'{_BT} BT7: as the wards close (5 s, heroic 4 s after the Quarantine yell), every player outside both wards '
    'takes 40% of the non-tank row, no Weakened (ST BT7 lists none; over 30%), through the kit\'s RegistryHit. Resolve '
    "copy (Nature). Plague Cloud's SV 761 on every player hit.",
    icon=_ICON_DISEASE_CLOUD, visual=BT_CONTAGION,
)

# --- BT8 Fever --------------------------------------------------------------------------------------------------------

fever_206613 = spell(
    id=206613, name='Fever', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=5,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Fever: a flat +5% / +6% damage done per stack, not a damage or heal value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=3, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FURIOUS_ANGER,
    notes=f'{_BT} BT8: his stacking buff, the fight\'s enrage (stock Furious Anger 16791 changed): +5% damage done '
          '(heroic +6%: spell_st_barthilas_fever sets the per-stack value) and +3% attack speed per stack, no cap '
          '(CumulativeAura 255, the aura counter\'s limit). +1 every 20 s, +1 for every player who catches Infection '
          'from someone else (a carrier, a pile, a puddle or a ward), +1 for every player a cough hits; heroic Bedlam '
          '+5 (DungeonKit::AddStacks). His melee and stock blows only: the reference-sized hits ignore caster '
          "modifiers. Not dispellable. Unholy Frenzy 8699's SV 47 (glowing hands) and Furious Anger's icon.",
    raw_overrides=kit_raw('Fevered: damage and attack speed increased.', 'Damage and attack speed increased.',
                          instant=True, CumulativeAura=255, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=BT_FEVER),
)
scripted_by(fever_206613, 'spell_st_barthilas_fever')

# --- BT9 Bedlam (heroic) ----------------------------------------------------------------------------------------------

spell(
    id=206614, name='Bedlam', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=3000, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FURIOUS_ANGER,
    notes=f'{_BT} BT9 heroic: "The city will fall into bedlam!" (yell line 3), 35 s in and every 30 s, between '
          'Quarantines: a 3 s cast, kickable (InterruptFlags 15, PreventionType silence; his interrupt list, priority '
          '3: expected). Finished (the boss AI\'s OnSpellCast), every player not already sick is Infected at once, '
          'so their coughs land together at 40%, and he gains 5 Fever. School Nature: a kick locks out nothing else '
          "he casts. Furious Anger 16791's SV 2817 (a roar flash; RISKY, gap 16) and icon.",
    raw_overrides=kit_raw('The city will fall into bedlam.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=BT_FURIOUS_ANGER_FLASH),
)
