"""
Scholomance build WP-S5: Instructor Malicia (10505), normal and heroic, her detention lesson and her examiner mode
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.4 rows MA, s3.5 row S5, s3.6, s3.7; build spec
docs/dungeons/scholomance-rework.md SC 1431-1488, design SC 1250-1430). WP-S5 owns this file (its spells: kSpellsMalicia
206205-206224 of modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; MaliciaLogic.h names the same ids;
its creatures: Malicia's Shade 300536 and Loose Soul 300537).

- 10505 Instructor Malicia: boss_instructor_malicia_rework (src/Scholomance/boss_instructor_malicia_rework.cpp), SmartAI
  off (the WP-S5 SQL rev drops the seven stock rows and adds her emotes), the build spec's normal health (160k:
  HealthModifier 65.52 on the level 60 class base 2,442), DamageModifier 3.5 (the AC base value; the live 5 is the
  retired mod-progression's leftover, handoff s2.3), stun immunity 1972, INSTANCE_BIND. Heroic 250k is WP-H's override
  (source/world/dungeons/scholomance.py).
- 300536 Malicia's Shade (MA4): a copy of the Occultists' Dark Shade 11284 (display 4629) on its own entry (11284 is the
  trash's UpdateEntry form): level 60 elite undead, warrior base 3,052 x 3.9318 = 12,000 (heroic 18,000 is WP-H's
  `_KIT_ADD_HEROIC`; its row names its heroic entry, difficulty_entry_1 310114, STAGE-H report s4).
  npc_sc_malicias_shade stands where it rose and casts its Volley; after 20 s it walks into her. DamageModifier 1.0
  (it is a caster; the stock shade's 7.5 is trash tuning).
- 300537 Loose Soul (MA3): the wisp (display 1825, handoff s7 #20: display 30233 is an invisible stalker), a summoned
  look the players walk through; not selectable or attackable (KIT_HELPER), no script (the owner's AI runs the pickup).
  No heroic template (not a combat add).

Spells (Spell.dbc 3.3.5 for every stock id quoted; looks from WP-V's ._visuals, all stock):

  206205  Soul                 MA1 the meter: a DUMMY buff stacking to 40 (CumulativeAura), 20 at the pull; not
                               cancellable, never dispelled; self-applied (the player is the caster); its AuraScript
                               removes the weight with it
  206206  Soul                 MA1 the weight (hidden): damage done, healing done and max health, each (stacks - 20) x
                               5% (spell_scholo_malicia_soul_weight sets all three from the meter)
  206207  Soul Drain           MA2 the 2 s cast bar (not interruptible)
  206208  Soul Drain           MA2 the drain's look on each drained player (Drain Soul Visual 60857's SV 12656)
  206209  Bound Soul           MA5 her buff: +2% damage done a stack, 20 stacks (Purple Banish Visual 68862's SV 7784)
  206210  Shadow Bolt Volley   MA4 the shade's 2 s kickable cast; it triggers the stock Shadow Bolt Volley 17228
  206211  Soulstorm            MA6 the 3.5 s cast bar (Soulstorm 68872's SV 14509 on her hands)
  206212  Soulstorm            MA6 a falling soul: a no-effect missile at a marker (Soulstorm 68896's SV 14512)
  206213  Soulstorm            MA6 the blast: resolve copy (Shadow), Spirit Burst 24050's SV 7180 on every player hit
  206214  Spirit Burst         MA6 the burst's look at every marker as it lands (SV 7180)
  206215  Shadow Heal          MA7 the 3.5 s kickable cast: heals her (spell_scholo_malicia_shadow_heal) and triggers
                               the nova (Shadow Mend 25531's SV 7380)
  206216  Shadow Nova          MA7 the burst on every player (spell_scholo_malicia_shadow_nova, Shadow Nova 32711's
                               SV 7951)
  206217  Soul Lost            detention: a soul faded in the Coven's lesson (spell_scholo_malicia_soul_lost: 15% / 25%
                               and Weakened)
  206218-206224 spare.
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR0_NO_ACTIVE_DEFENSE,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_B,
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
    DISPLAY_DARK_SHADE,
    DISPLAY_LOOSE_SOUL,
    ML_BOUND_SOUL,
    ML_FALLING_SOULS,
    ML_SHADOW_MEND,
    ML_SHADOW_NOVA,
    ML_SOUL_DRAIN,
    ML_SOULSTORM_HANDS,
    ML_SPIRIT_BURST,
)

# Held back until wave B binds this boss (_common.py BIND_WAVE_B; R-A S-11): stock until then.
if BIND_WAVE_B:
    creature_template_columns(10505, **boss_columns('boss_instructor_malicia_rework', 65.52, DamageModifier=3.5))

_MA = 'Scholomance build WP-S5 (Instructor Malicia)'
_SCRIPT_EXCLUDED = 'Scholomance: a percent of reference health, set by the script (DungeonKit::RefFlat)'
_SCRIPT_HEAL = 'Scholomance: a percent of her own health, set by spell_scholo_malicia_shadow_heal'

_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_ATTR0_NO_AURA_CANCEL = 0x80000000
_INTERRUPT_FLAGS_STANDARD = 15     # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127
_AURA_MOD_INCREASE_HEALTH_PERCENT = 133

_ICON_SOUL_FRAGMENT = 1693         # Soul Fragment 71905
_ICON_SOUL_GEM = 2027              # Spell_Shadow_SoulGem's alternate (WP-V: Malicia's Passing Grade keeps 92)
_ICON_DRAIN_SOUL = 113             # Drain Soul Visual 60857
_ICON_SHADOW_BOLT_VOLLEY = 213     # Shadow Bolt Volley 17228
_ICON_SOULSTORM = 458              # Soulstorm 68872
_ICON_SPIRIT_BURST = 87            # Spirit Burst 24050
_ICON_SHADOW_MEND = 1942           # Shadow Mend 25531
_ICON_SHADOW_NOVA = 1988           # Shadow Nova 32711
_SV_SHADOW_BOLT_VOLLEY = 2318      # Shadow Bolt Volley 17228 (the shadow hands while the shade casts)

_STOCK_SHADOW_BOLT_VOLLEY = 17228

# --- 300536 Malicia's Shade / 300537 Loose Soul ----------------------------------------------------------------------

# Level 60 elite undead warrior base 3,052: ceil(3,052 x 3.9318) = 12,000.
malicias_shade_300536 = creature_template(
    300536, "Malicia's Shade", **{
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'type': 6, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': 3.9318, 'DamageModifier': 1.0, 'BaseAttackTime': 2000, 'ExperienceModifier': 1.0,
        'speed_walk': 1.15, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'ScriptName': 'npc_sc_malicias_shade', 'difficulty_entry_1': 310114,
    },
)
creature_model(300536, display_id=DISPLAY_DARK_SHADE)

loose_soul_300537 = creature_template(
    300537, 'Loose Soul', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
                             'ScriptName': ''},
)
creature_model(300537, display_id=DISPLAY_LOOSE_SOUL, scale=0.8)

# --- MA1 Soul --------------------------------------------------------------------------------------------------------

soul_206205 = spell(
    id=206205, name='Soul', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=_ATTR0_NO_AURA_CANCEL | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SOUL_FRAGMENT,
    notes=f'{_MA}, MA1: the meter on every player of her fight, 20 stacks at the pull (CumulativeAura 40), '
          'self-applied (DungeonKit::AddStacks with the player as the caster, so it never needs her alive: her '
          'detention lesson uses it too). Floor 10 and cap 40 are the script\'s (MaliciaLogic.h SoulAfter). Not '
          'cancellable (the weight rides it), Dispel none, NO_IMMUNITIES. spell_scholo_malicia_soul removes the '
          'weight 206206 with it. The bots\' soul Soaks order by its stacks (lowest first, nobody at 40). Number-free '
          'text (SC MA1). Soul Fragment 71905\'s icon; no body tint (a glow on every player for the whole fight would '
          'bury the markers).',
    raw_overrides=kit_raw('Your soul, pried loose and held together. The more of it you keep, the stronger you are.',
                          'Your soul. More makes you stronger; less makes you weaker.', CastingTimeIndex=1,
                          CumulativeAura=40, AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(soul_206205, 'spell_scholo_malicia_soul')

soul_weight_206206 = spell(
    id=206206, name='Soul', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | _ATTR0_NO_AURA_CANCEL | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=0,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_TARGET_ANY),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=0,
                    die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY),
             Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_INCREASE_HEALTH_PERCENT, base_points=0,
                    die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SOUL_FRAGMENT,
    notes=f'{_MA}, MA1: the meter\'s weight, hidden: damage done (all schools), healing done and max health, each '
          '(stacks - 20) x 5% of the owner\'s Soul 206205 (spell_scholo_malicia_soul_weight sets the three amounts; '
          'the script recalculates them on every meter change). One stack of its own, so the engine\'s stack multiply '
          'leaves the amount alone. 10 stacks = -50% (no player under half health), 40 = +100%. Max health keeps its '
          'percent through a change (MOD_INCREASE_HEALTH_PERCENT).',
    raw_overrides=kit_raw(instant=True, AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(soul_weight_206206, 'spell_scholo_malicia_soul_weight')

# --- MA2 Soul Drain --------------------------------------------------------------------------------------------------

soul_drain_cast_206207 = cast_bar(
    206207, 'Soul Drain', 2000, 'Tears the soul loose.',
    f'{_MA}, MA2: the 2 s cast bar, at the drained player on normal (emote line 0 names them; two below 50% of her '
    'health), at herself on heroic (every player, the tank too; emote line 1). Not interruptible (not on her interrupt '
    'list). The AI drains on its own clock when the bar ends: up to 4 stacks each (never under 10), that many Loose '
    'Souls 10 to 15 yd around them.',
    icon=_ICON_DRAIN_SOUL, school=School.SHADOW)

soul_drain_206208 = spell(
    id=206208, name='Soul Drain', school=School.SHADOW, attributes=ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DRAIN_SOUL,
    notes=f'{_MA}, MA2: the drain\'s look on each drained player as the bar ends (triggered, no effect): Drain Soul '
          'Visual 60857\'s SV 12656 (SoulFunnel_Impact_Chest). Also on her as a shade walks in (MA4, +4 Bound Soul) '
          'and on the student as a detention lesson starts.',
    raw_overrides=kit_raw('Tears the soul loose.', instant=True, SpellVisualID_1=ML_SOUL_DRAIN,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT),
)

# --- MA5 Bound Soul --------------------------------------------------------------------------------------------------

bound_soul_206209 = spell(
    id=206209, name='Bound Soul', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=2,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SOUL_GEM,
    notes=f'{_MA}, MA5: her buff, +2% damage done a stack (the engine multiplies by the stacks), 20 stacks (+40%). A '
          'faded soul gives 1, a shade that walks in 4. Her own spells ignore caster modifiers, so the AI scales '
          'Soulstorm and Shadow Nova by the same factor (MaliciaLogic.h BoundDamageScale). Dispel none (no purge in '
          'the build spec). Purple Banish Visual 68862\'s SV 7784 (banish_chest_purple, a state on the aura).',
    raw_overrides=kit_raw('Bound souls strengthen her.', 'Damage done increased by $s1%.', instant=True,
                          CumulativeAura=20, SpellVisualID_1=ML_BOUND_SOUL, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- MA4 the shades' Volley ------------------------------------------------------------------------------------------

shade_volley_206210 = spell(
    id=206210, name='Shadow Bolt Volley', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=2000, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=_STOCK_SHADOW_BOLT_VOLLEY,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHADOW_BOLT_VOLLEY,
    notes=f'{_MA}, MA4: Malicia\'s Shade\'s 2 s cast (first after 4 s, then every 8 s), kickable (InterruptFlags 15, '
          'PreventionType silence; her descriptor\'s interrupt list, priority 2). When it completes it triggers the '
          'stock Shadow Bolt Volley 17228 (instant, every enemy within 30 yd, the stock damage that '
          'mod-dungeon-difficulties scales on heroic): the stock spell is instant and could not be kicked, and the '
          'build spec puts it on the interrupt list. Shadow Bolt Volley\'s SV 2318 (shadow hands during the cast).',
    raw_overrides=kit_raw('Gathers shadow for a volley of bolts.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                          SpellVisualID_1=_SV_SHADOW_BOLT_VOLLEY),
)

# --- MA6 Soulstorm ---------------------------------------------------------------------------------------------------

soulstorm_cast_206211 = cast_bar(
    206211, 'Soulstorm', 3500, 'Unleashes a storm of souls.',
    f'{_MA}, MA6: the 3.5 s cast bar (emote line 3): three waves of 4 yd registry circles 1 s apart, each 1.5 s, all '
    'landing inside the bar. Not interruptible. Soulstorm 68872\'s SV 14509 (banish_chest_purple on both hands).',
    icon=_ICON_SOULSTORM, school=School.SHADOW, visual=ML_SOULSTORM_HANDS)

soulstorm_fall_206212 = spell(
    id=206212, name='Soulstorm', school=School.SHADOW, attributes=ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_SOULSTORM,
    notes=f'{_MA}, MA6: a falling soul, a no-effect missile she casts at a marker (triggered). Soulstorm 68896\'s SV '
          '14512 (a banish_chest_purple orb; Unleashed Souls 14527 is an icy ground state with no souls). Speed 20 '
          'yd/s = MaliciaLogic.h kStormFallSpeed: the script launches it so it lands as the marker resolves.',
    raw_overrides=kit_raw('A tormented soul falls.', SpellVisualID_1=ML_FALLING_SOULS, Speed=20.0,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          CastingTimeIndex=1),
)

soulstorm_blast_206213 = resolve_copy(
    206213, 'Soulstorm', School.SHADOW, 'A tormented soul bursts.',
    f'{_MA}, MA6: one 4 yd marker\'s blast, 20% normal / 30% heroic of the non-tank row (x her Bound Soul factor); the '
    'hit destroys one Soul stack (the registry OnHit) in place of Weakened (SC MA6), and the souls under it are '
    'destroyed. Copy of the resolve spell 205001 (Shadow). Spirit Burst 24050\'s SV 7180 on every player hit.',
    icon=_ICON_SPIRIT_BURST, visual=ML_SPIRIT_BURST,
)

soulstorm_burst_206214 = spell(
    id=206214, name='Spirit Burst', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_SPIRIT_BURST,
    notes=f'{_MA}, MA6: the burst\'s look at every marker as it resolves (her, triggered, at the point; no effect), so '
          'a dodged blast still shows. Spirit Burst 24050\'s SV 7180.',
    raw_overrides=kit_raw(SpellVisualID_1=ML_SPIRIT_BURST, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, CastingTimeIndex=1),
)

# --- MA7 Shadow Heal -------------------------------------------------------------------------------------------------

shadow_heal_206215 = spell(
    id=206215, name='Shadow Heal', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=3500, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, implicit_target_a=TARGET_UNIT_CASTER, potency_excluded=_SCRIPT_HEAL),
             Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=206216, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHADOW_MEND,
    notes=f'{_MA}, MA7: below 50%, every 20 s: a 3.5 s kickable cast (InterruptFlags 15, PreventionType silence; her '
          'interrupt list, priority 3: a reward on normal, expected on heroic). Finished, she heals 5% normal / 10% '
          'heroic of her max health (spell_scholo_malicia_shadow_heal sets the heal at launch; ignores caster '
          'modifiers, cannot crit) and the second effect triggers the nova 206216. Replaces the stock Heal 15586. '
          'Shadow Mend 25531\'s SV 7380.',
    raw_overrides=kit_raw('Mends her with shadow; dark magic bursts on every enemy.',
                          InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=ML_SHADOW_MEND, AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(shadow_heal_206215, 'spell_scholo_malicia_shadow_heal')

shadow_nova_206216 = spell(
    id=206216, name='Shadow Nova', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=60.0,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_SHADOW_NOVA,
    notes=f'{_MA}, MA7: the finished Shadow Heal\'s burst on every enemy within 60 yd (the whole Coven): 15% normal / '
          '40% heroic of the reference row (x her Bound Soul factor), set at launch by '
          'spell_scholo_malicia_shadow_nova (RefFlatOn, so the target\'s defensives count). Ignores caster modifiers '
          'and line of sight, cannot crit, always hits. Shadow Nova 32711\'s SV 7951.',
    raw_overrides=kit_raw('Dark magic bursts on every enemy.', instant=True, SpellVisualID_1=ML_SHADOW_NOVA,
                          DefenseType=_DEFENSE_MAGIC, Attributes=ATTR0_NO_ACTIVE_DEFENSE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(shadow_nova_206216, 'spell_scholo_malicia_shadow_nova')

# --- Detention: Soul Lost --------------------------------------------------------------------------------------------

soul_lost_206217 = spell(
    id=206217, name='Soul Lost', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_DRAIN_SOUL,
    notes=f'{_MA}, detention (the Coven, SC 2965): a soul faded before the student took it. The lesson\'s stalker '
          'casts it on the student (triggered): 15% normal / 25% heroic of the reference row (SoloLesson.h '
          'LessonFailurePct, RefFlatOn at launch) and one Weakened stack (ruling 21), by '
          'spell_scholo_malicia_soul_lost. Ignores caster modifiers and line of sight, cannot crit, always hits, no '
          'threat. Drain Soul Visual 60857\'s SV 12656.',
    raw_overrides=kit_raw('Your soul slips away.', instant=True, SpellVisualID_1=ML_SOUL_DRAIN,
                          DefenseType=_DEFENSE_MAGIC, Attributes=ATTR0_NO_ACTIVE_DEFENSE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(soul_lost_206217, 'spell_scholo_malicia_soul_lost')
