"""
Stratholme build WP-S1: The Unforgiven (10516), normal and heroic
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows UF, s3.5 row S1, s3.6, s3.8 #1; build spec
docs/dungeons/stratholme-rework.md ST 616-676, design ST 441-615). WP-S1 owns this file (its spells: kSpellsUnforgiven
206420-206439 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; UnforgivenLogic.h names the same
ids; its creatures: 300600-300601, and the stock phantom 10387's columns). The engine side is
src/Stratholme/boss_the_unforgiven_rework.cpp; the rows dbc-tools cannot declare (SmartAI deletes, texts, the
footman's sword and shield) are data/sql/updates/pending_db_world/rev_the_unforgiven_stratholme.sql.

- 10516 The Unforgiven: boss_the_unforgiven_rework (SmartAI off: no invisibility roll, no Incorporeal Defense, no
  phantoms on aggro), the build spec's normal health (185k: HealthModifier 66.451 on the level 57 warrior class base
  2,784), stun immunity 1972 (his own set: stun immune; nothing of his is an interrupt check), INSTANCE_BIND
  (flags_extra 1), DamageModifier 3.7 (the stock value: base SQL; also the live one). Heroic 250k is WP-H's override
  (source/world/dungeons/stratholme.py).
- 10387 Vengeful Phantom (his alone, summoned only by his script): npc_st_vengeful_phantom (SmartAI off: no Frost
  Shock), level 57, HealthModifier 2.155172: ceil(2,784 x 2.155172) = 6,000 (heroic 9,000 is WP-H's override, heroic
  entry 310126). The Spectral Citizen models 10483-10486 (ST "Stock kit") replace display 146.
- 300600 Spectral Footman (the rank and the cordon): display 30978 (the Halls of Reflection Spectral Footman: a
  translucent soldier at 1.4 scale), not attackable (UNIT_FLAG_NON_ATTACKABLE | IMMUNE_TO_PC | IMMUNE_TO_NPC),
  selectable so a player can read its name. No heroic template (handoff s7 #15). Sword and shield: the SQL rev.
- 300601 House fire (the build spec's house fire stalker): an invisible trigger at a doorway (KIT_HELPER), anchor of
  the burning house and carrier of the firelight glow. No heroic template.

Spells. The March, the fire's landing and the burning patch deal their damage through dungeon copies of the
mod-boss-mechanics resolve spell (the registry's percent of the reference row; the combat log names the mechanic).
Grief, the Frost Nova copy and Haunting Memory are the kit's generic percent spells (spell_dungeon_refflat_damage /
_periodic: hundredths in the effect value, heroic in EffectMiscValueB; KT-1). Freed is an exact amount from the
script. The rest are auras and looks:

  206420  The March          UF1 the rank's hit: resolve copy (Shadow), Ghostly Strike 14278's SV 4159
  206421  House Fire         UF2 the landing: resolve copy (Fire), Building Fire 21650's SV 6821
  206422  Burning House      UF3 the patch's tick: resolve copy (Fire), SV 6821
  206423  Firelight          UF4 the glow on the fire stalker (V-2's FlameZone 10 yd disc, SV 90507)
  206424  Accused            UF5 the accused's debuff (Target Indicator 46901's lasting arrow, SV 10201)
  206425  Accused            UF5 the apply flash (Wrongfully Accused 51703's SV 11826)
  206426  Grief              UF7 a phantom reached its accused: 30% Shadow (Shadow Shock's SV 4209)
  206427  Grudge             UF8 his buff: +10% damage done per stack
  206428  Freed              UF6 the tear on him: 2% of his health, exact amount
  206429  Soul Freed         UF6 the freed phantom's look (Soul Freed 17370's SV 4501)
  206430  Bound              UF8 a bound soul pours into him (Haunting Phantoms 16336's SV 335)
  206431  Frost Nova         UF10 8% Frost in 10 yd and a 1.5 s root (Frost Nova 14907's SV 17)
  206432  Haunting Memory    UF11 heroic: Magic DoT 3% a second for 8 s (SV 335); its expiry raises a phantom
  206433  In the Firelight   UF4 on a phantom standing in firelight: the bots' kill-target key
  206434-206439 spare.

The Cordon's strike is the shared 206400 (shared.py); the Cordon itself is the kit's LethalWall. Tooltips are
number-free (ST checklist item 8, Systems.md s10).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    self_visual,
)
from lib.dsl.registry import (
    creature_model,
    creature_template,
    creature_template_columns,
    scripted_by,
    spell,
)

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_SPECTRAL_FOOTMAN,
    DISPLAYS_SPECTRAL_CITIZEN,
    SV_FLAMEZONE_10_STATE,
    UF_ACCUSED_ARROW,
    UF_ACCUSED_FLASH,
    UF_BUILDING_FIRE,
    UF_FROST_NOVA,
    UF_HAUNTING_PHANTOMS,
    UF_SOUL_FREED,
)

_UF = 'Stratholme build WP-S1 (The Unforgiven)'
_SCRIPT_REFFLAT = ('Stratholme: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')
_SCRIPT_EXACT = 'Stratholme: an exact amount from the script (CastCustomSpell base point 0)'

_FLAGS_EXTRA_NO_XP = 0x40
_FLAGS_EXTRA_TRIGGER = 0x80
# UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_IMMUNE_TO_PC | UNIT_FLAG_IMMUNE_TO_NPC: the footmen stand, march and strike;
# nobody fights them.
_UNIT_FLAGS_FOOTMAN = 0x2 | 0x100 | 0x200
_DISPEL_MAGIC = 1
_MECHANIC_ROOT = 7
_DEFENSE_MAGIC = 1
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): AC drops the aura before the logout save, after the login load and on
# a cross-map teleport, so a debuff never outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127

# Looks: V-2's UF_ picks (._visuals) and the stock ids V-2 named none for (each unconfirmed until seen in game).
SV_MARCH_HIT = 4159                 # Ghostly Strike 14278: a spectral blade strike on the target
SV_FIRE = UF_BUILDING_FIRE          # Building Fire 21650: a 0.7 s body-sized flame (the landing and each tick)
SV_FIRELIGHT = SV_FLAMEZONE_10_STATE    # V-2: FlameZone orange disc, 10 yd (STATE, on the stalker's aura)
SV_ACCUSED = UF_ACCUSED_ARROW       # Target Indicator (Cosmetic) 46901: a lasting red arrow over the head (STATE)
SV_ACCUSED_FLASH = UF_ACCUSED_FLASH     # Wrongfully Accused 51703: a 2.6 s ring of flame rays (the apply flash)
SV_GRIEF = 4209                     # Shadow Shock 16583: a shadow burst on the target
SV_SOUL_FREED = UF_SOUL_FREED       # Soul Freed 17370: icy star burst + a bubble (the stock Restless Souls look)
SV_BOUND = UF_HAUNTING_PHANTOMS     # Haunting Phantoms 16336: hands and a rising spirit
SV_FROST_NOVA = UF_FROST_NOVA       # Frost Nova 14907
SV_HAUNTING = UF_HAUNTING_PHANTOMS  # the Spectral Citizens' stock curse look, on a Magic copy

_ICON_GHOSTLY_STRIKE = 596          # Ghostly Strike 14278
_ICON_FIRE = 31                     # Immolate 348
_ICON_HAUNTING = 9                  # Haunting Phantoms 16336
_ICON_SHADOW_SHOCK = 213            # Shadow Shock 16583
_ICON_GRUDGE = 38                   # Unholy Frenzy 8699
_ICON_FREED = 1                     # Soul Freed 17370
_ICON_FROST_NOVA = 193              # Frost Nova 14907
_ICON_ACCUSED = 9

# Percents in hundredths (KT-1's generic percent spells): the shown value is EffectBasePoints + 1 as stored, the heroic
# value EffectMiscValueB. UnforgivenLogic.h holds the same numbers.
_GRIEF = (3000, 3000)               # kGriefPct 30 / 30
_FROST_NOVA = (800, 800)            # kNovaPct 8 / 8
_HAUNTING_TICK = (300, 300)         # kHauntingPct 3 (heroic only)
_GRUDGE_DAMAGE_PCT = 10             # kGrudgeDamagePct, per stack
_GRUDGE_MAX = 255                   # kGrudgeMaxStacks: uncapped in play (the aura's own limit)
_NOVA_RADIUS = 10.0                 # kNovaRadius
_NOVA_ROOT_MS = 1500                # kNovaRootMs
_HAUNTING_MS = 8000                 # kHauntingMs

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(10516, **boss_columns(
        'boss_the_unforgiven_rework', 66.451, damage_modifier=3.7,
    ))

    # --- 10387 Vengeful Phantom ---------------------------------------------------------------------------------------
    # Level 57: ceil(2,784 x 2.155172) = 6,000 (heroic 9,000: stratholme.py). The Spectral Citizen models (ST "Stock
    # kit"): human male and female ghosts at alpha 128, one at random.
    creature_template_columns(10387, ScriptName='npc_st_vengeful_phantom', AIName='', minlevel=57, maxlevel=57,
                              HealthModifier=2.155172)
    for _idx, _display in enumerate(DISPLAYS_SPECTRAL_CITIZEN):
        creature_model(10387, display_id=_display, idx=_idx)

    # --- 300600 Spectral Footman --------------------------------------------------------------------------------------
    spectral_footman_300600 = creature_template(
        300600, 'Spectral Footman', **{
            **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
            'unit_flags': _UNIT_FLAGS_FOOTMAN, 'HealthModifier': 1.0, 'DamageModifier': 0.0, 'lootid': 0,
            'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'detection_range': 0.0,
            'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_st_spectral_footman',
        },
    )
    creature_model(300600, display_id=DISPLAY_SPECTRAL_FOOTMAN)

    # --- 300601 House fire --------------------------------------------------------------------------------------------
    house_fire_300601 = creature_template(
        300601, 'House Fire', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                 'type': 10, 'flags_extra': _FLAGS_EXTRA_NO_XP | _FLAGS_EXTRA_TRIGGER,
                                 'ScriptName': ''},
    )
    creature_model(300601, display_id=DISPLAY_INVISIBLE_STALKER)


def _refflat_hit(spell_id: int, name: str, school: School, pct: tuple[int, int], icon: int, desc: str, notes: str,
                 *, visual: int = 0):
    """A hit at a percent of the reference row (the kit's spell_dungeon_refflat_damage), cast by him (triggered):
    always hits, cannot crit, ignores his modifiers (Grudge never raises it; the target's own defensives count)."""
    s = spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct[0] - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, EffectMiscValueB_1=pct[1],
                              SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(s, 'spell_dungeon_refflat_damage')
    return s


# --- UF1 The March ---------------------------------------------------------------------------------------------------

march_hit_206420 = resolve_copy(
    206420, 'The March', School.SHADOW, 'The spectral rank cuts down everyone in its path.',
    f'{_UF}, UF1: the rank\'s hit. Every 40 s from 20 s (yell line 1) a rank of Spectral Footmen 300600 forms at the '
    'mouth of one of the plaza\'s two streets (Market Row 25 yd wide, the passage 12 yd), a 3 s line marker covers the '
    'street from 5 yd past its cordon to its far end, then the rank marches it in 2 s: 40% (heroic 45%) of the row to '
    'everyone in its path, the tank too (its own row), 1 Weakened, through the registry (a projectile Line tracking '
    'the rank\'s middle footman). Heroic: the crossing rank down the other street, its marker 1.5 s after the first '
    'has passed. Copy of the resolve spell 205001 (Shadow). Ghostly Strike 14278\'s SV 4159 on every unit hit.',
    icon=_ICON_GHOSTLY_STRIKE, visual=SV_MARCH_HIT,
)

# --- UF2 / UF3 House fire --------------------------------------------------------------------------------------------

house_fire_206421 = resolve_copy(
    206421, 'House Fire', School.FIRE, 'A burning house spills flame into the street.',
    f'{_UF}, UF2: the landing. Every 25 s (heroic 20 s) from 8 s (emote line 3) a house on the plaza catches fire: a '
    '2 s, 5 yd circle marker at one of the five bays (fire spots F1-F4, F6, none burning yet; at most 3 burn), then '
    '25% of the row to everyone inside, the tank too (its own row), 1 Weakened, through the registry. Copy of the '
    'resolve spell 205001 (Fire). Building Fire 21650\'s SV 6821 (a body-sized flame) on every unit hit; the house '
    'itself burns as the stock "Big Barracks Flame" 176746 for the 60 s.',
    icon=_ICON_FIRE, visual=SV_FIRE,
)

burning_house_206422 = resolve_copy(
    206422, 'Burning House', School.FIRE, 'The burning house scorches everyone near its door.',
    f'{_UF}, UF3: the burning patch, the same 5 yd circle for 60 s after the landing (the kit\'s ImpactThenLinger): '
    '5% of the row a second to everyone inside, the tank too, no Weakened and no slow (ST). Copy of the resolve spell '
    '205001 (Fire). SV 6821 on every unit hit (a flame lick each second).',
    icon=_ICON_FIRE, visual=SV_FIRE,
)

# --- UF4 Firelight ---------------------------------------------------------------------------------------------------

firelight_206423 = spell(
    id=206423, name='Firelight', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FIRE,
    notes=f'{_UF}, UF4: the firelight around a burning house, a DUMMY aura on its stalker 300601 (the script casts it '
          'on the stalker, triggered, when the fire lands; the stalker despawns when the house stops burning, which '
          'ends it). WP-V-2\'s FlameZone orange disc at 10 yd (SV 90507, a StateKit: SV_FLAMEZONE_10_STATE). It '
          'reaches nobody: the ring from 5 to 10 yd is a telegraph-only registry Soak the accused claims, and a '
          'phantom killed within 10 yd of a burning house is freed (the script\'s rule).',
    raw_overrides=kit_raw('Firelight. Souls are freed here.', 'Firelight. Souls are freed here.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=SV_FIRELIGHT),
)

in_firelight_206433 = spell(
    id=206433, name='In the Firelight', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FIRE,
    notes=f'{_UF}, UF4 / UF5: the mark on a Vengeful Phantom standing within 10 yd of a burning house. The boss AI '
          'puts it on (Unit::AddAura) and takes it off every 250 ms from the phantom\'s position: the bots\' '
          'descriptor reads it (kill target priority 2 with AoE allowed while the phantom has it; ignored while it '
          'lacks it, so bot AoE never binds a phantom in the dark), and players see it in the phantom\'s buff row. '
          'A DUMMY aura, no look.',
    raw_overrides=kit_raw('Standing in the firelight: it can be freed.', 'Standing in the firelight.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- UF5 The Accusation ----------------------------------------------------------------------------------------------

accused_206424 = spell(
    id=206424, name='Accused', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ACCUSED,
    notes=f'{_UF}, UF5: "You! I saw you there that night!" (yell line 2). Every 35 s from 15 s (until the Last Soul) '
          'he puts it on a random non-tank (Unit::AddAura) and 3 Vengeful Phantoms (heroic 4) rise around him and '
          'drift to that player; the Last Soul and heroic Haunting Memory name accused players too. It lasts while a '
          'phantom still hunts its bearer (the AI removes it when the last one ends; no duration). A DUMMY aura: the '
          'tell, and what the bots read (the accused claims a firelight ring, the telegraph-only Soak per fire). '
          'Dispel none and NO_IMMUNITIES; dropped on a logout or a map change, removed with the fight. Target '
          'Indicator 46901\'s lasting arrow (SV 10201); the apply flash is 206425.',
    raw_overrides=kit_raw('Accused. Stand in the firelight while the phantoms are killed.',
                          'The phantoms are coming for you. Stand in the firelight.', CastingTimeIndex=1,
                          SpellVisualID_1=SV_ACCUSED, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

accused_flash_206425 = spell(
    id=206425, name='Accused', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ACCUSED,
    notes=f'{_UF}, UF5: the apply flash, cast by him (triggered) on each newly accused player: an instant DUMMY with '
          'Wrongfully Accused 51703\'s SV 11826 (a 2.6 s ring of flame rays, a one-shot kit). Does nothing else.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=SV_ACCUSED_FLASH, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- UF6 Freed, UF7 Grief, UF8 Grudge --------------------------------------------------------------------------------

grief_206426 = _refflat_hit(
    206426, 'Grief', School.SHADOW, _GRIEF, _ICON_SHADOW_SHOCK, 'The phantom\'s grief floods its accuser.',
    f'{_UF}, UF7: a Vengeful Phantom reached its accused: 30% of the reference non-tank row on that player alone '
    '(3000 hundredths, both difficulties), Shadow, no Weakened (a group failure, ST). Cast by him (triggered). Shadow '
    'Shock\'s SV 4209 (a shadow burst on the target).',
    visual=SV_GRIEF,
)

grudge_206427 = spell(
    id=206427, name='Grudge', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=_GRUDGE_DAMAGE_PCT, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Grudge: a flat +10% damage done per stack, not a damage or heal value')],
    spell_icon_id=_ICON_GRUDGE,
    notes=f'{_UF}, UF8: his stacking buff, one stack per Bound phantom (killed outside the firelight, alive for 20 s, '
          'or reaching its accused; DungeonKit::AddStacks, CumulativeAura 255: uncapped in play, the level 60 rule). '
          '+10% damage done per stack, every school: it raises his melee; the reference-sized hits ignore caster '
          'modifiers, so they stay exact. At 25% (the Last Soul) every stack rises again as a phantom; freeing one '
          'removes a stack. Not dispellable; removed on his death, evade and reset. No look (the buff icon counts it).',
    raw_overrides=kit_raw('Every soul it keeps feeds its grudge: damage done increased.', 'Damage dealt increased.',
                          instant=True, CumulativeAura=_GRUDGE_MAX, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

freed_206428 = spell(
    id=206428, name='Freed', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_EXACT)],
    spell_icon_id=_ICON_FREED,
    notes=f'{_UF}, UF6: a Vengeful Phantom killed in the firelight is freed and tears 2% of his maximum health away '
          '(3,700 on normal, 5,000 on heroic; never his last point: the tear is not a kill). Never cast: the script '
          'takes the exact amount off his health (ModifyHealth) and sends the combat log line under this spell, so no '
          'damage-taken debuff on him scales it and it cannot kill him (R-2-A A-4). The attributes stay for a stray '
          'cast: ignores his modifiers, always hits, cannot crit, no threat.',
    raw_overrides=kit_raw('A freed soul tears away part of the Unforgiven.', instant=True, InterruptFlags=0,
                          PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

soul_freed_206429 = self_visual(
    206429, 'Soul Freed', SV_SOUL_FREED,
    f'{_UF}, UF6: the freed phantom\'s look, cast by the phantom on itself (triggered) as its killing blow lands in '
    'the firelight: Soul Freed 17370\'s SV 4501 (the stock Restless Souls look: an icy star burst and a bubble).',
    icon=_ICON_FREED,
)

bound_206430 = self_visual(
    206430, 'Bound', SV_BOUND,
    f'{_UF}, UF8: a soul pours back into him, cast by him on himself (triggered) for every Bound phantom: Haunting '
    'Phantoms 16336\'s SV 335 (hands and a rising spirit).',
    icon=_ICON_HAUNTING,
)

# --- UF10 Frost Nova -------------------------------------------------------------------------------------------------

frost_nova_206431 = spell(
    id=206431, name='Frost Nova', school=School.FROST, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_NOVA_ROOT_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_FROST_NOVA[0] - 1, die_sides=1,
               implicit_target_a=TARGET_SRC_CASTER, implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY,
               radius_yards=_NOVA_RADIUS, potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, mechanic=_MECHANIC_ROOT,
               implicit_target_a=TARGET_SRC_CASTER, implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY,
               radius_yards=_NOVA_RADIUS),
    ],
    spell_icon_id=_ICON_FROST_NOVA,
    notes=f'{_UF}, UF10: a copy of his stock Frost Nova 14907 (never the stock id): every 15 to 20 s while a player '
          'stands within 10 yd of him, never in the 6 s before a March lands nor while a rank is on the floor (the '
          'AI\'s gate). 8% of the reference row (800 hundredths, both difficulties; RefFlatOn, so the tank takes the '
          'tank row) Frost to every enemy within 10 yd and a 1.5 s root (was 8 s: the loss-of-control rule); Magic, '
          'so a dispel or a root break is a reward. Unavoidable healer work: no registry shape. He casts it '
          'triggered. Frost Nova 14907\'s SV 17.',
    raw_overrides=kit_raw('A ghost\'s cold roots everyone near him in place.', 'Frozen in place.', instant=True,
                          DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=_FROST_NOVA[1], SpellVisualID_1=SV_FROST_NOVA,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(frost_nova_206431, 'spell_dungeon_refflat_damage')

# --- UF11 Haunting Memory (heroic) -----------------------------------------------------------------------------------

haunting_memory_206432 = spell(
    id=206432, name='Haunting Memory', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_HAUNTING_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=_HAUNTING_TICK[0] - 1, die_sides=1, amplitude=1000,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_HAUNTING,
    notes=f'{_UF}, UF11 (heroic): every 30 s from 12 s on 2 random non-tanks (cast by him, triggered), 8 s, 3% of the '
          'reference row a second (300 hundredths; spell_dungeon_refflat_periodic), Shadow. Magic: the bots\' dispel '
          'entry (priority 2, urgent with 3 s left), expected. If it is not dispelled before it runs out, a Vengeful '
          'Phantom rises 6 yd from that player, fixated on them (they are its accused: spell_st_unforgiven_haunting_'
          'memory reports the expiry to the boss AI; a dispel or a death removes it without one). Dropped on a map '
          'change. The Spectral Citizens\' Haunting Phantoms 16336 look (SV 335), on a Magic copy of that Curse.',
    raw_overrides=kit_raw('A memory of the Culling haunts the target. If it is not dispelled, it rises as a phantom.',
                          'Haunted: Shadow damage every second. A phantom rises when it ends.', CastingTimeIndex=1,
                          EffectMiscValueB_1=_HAUNTING_TICK[1], SpellVisualID_1=SV_HAUNTING,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(haunting_memory_206432, 'spell_dungeon_refflat_periodic', 'spell_st_unforgiven_haunting_memory')
