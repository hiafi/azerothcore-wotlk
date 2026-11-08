"""
Scholomance build WP-S9: Lord Alexei Barov (10504), "the Code of Conduct"
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.4 rows AB, s3.5 row S9, s3.6; build spec
docs/dungeons/scholomance-rework.md SC 2460-2533, design SC 2275-2459). WP-S9 owns this file (its spells: kSpellsAlexei
206290-206314 of modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; AlexeiLogic.h names the same ids).

- 10504 Lord Alexei Barov: boss_lord_alexei_barov_rework (SmartAI off; WP-S9's SQL rev drops the four stock rows and
  his formation), the build spec's normal health (160k: HealthModifier 52.425 on the level 60 warrior base 3,052),
  DamageModifier 6.0 (the live 6 was a mod-progression leftover; his own now, WP-T tunes it), stun immunity 1972,
  INSTANCE_BIND. Heroic 250k and the tier's melee are WP-H's heroic template 310094 (source/world/dungeons/
  scholomance.py). His Graduate Examiner (300553, S13's template) gets its own script, npc_sc_examiner_alexei.
- 300543 The Barov Fortune: an invisible, unselectable prop (KIT_HELPER, the Blizzard anchor's shape) the rule book
  summons under each gold pile for the window: the summoner of the pile's look, the stock "Gold Coins" chest 186634
  (GODI 2614 GoldPilesmall01, VISUALS-REPORT gap 13 rank 1), made not selectable so it never opens.
  npc_sc_barov_fortune (a NullCreatureAI; it also runs `.dbtest`'s test lesson). No heroic template (a prop).

Spells. Every rule is a registry mechanic; the two whose kind deals damage (the Out of bounds zone, the Keep your
distance spread) resolve through dungeon copies of the mod-boss-mechanics resolve spell with no damage, so a break
reaches the failure ledger under the rule's own name. The Dean's Rod is the punishment (a script spell: the damage is
its base point, a percent of the reference row from DungeonKit::RefFlatOn). The rest are auras and a look:

  206290  No Running in the Halls!  AB2 the rule's icon on everyone in the vault until the window closes (DUMMY)
  206291  Assembly!                 AB3
  206292  Keep Your Distance!       AB4
  206293  Go to the Corner!         AB5 (Out of bounds)
  206294  Line Up!                  AB6 heroic
  206295  To Your Desks!            AB7 heroic
  206296  Code of Conduct           AB1 the announcement's look on him (Commanding Shout 469's SV 246)
  206297  Out of Bounds             AB5 the forbidden third's tick: resolve copy (Shadow), no damage
  206298  Keep Your Distance        AB4 the spread's hit at the close: resolve copy (Shadow), no damage
  206299  Demerit                   AB9 the stacking debuff, 5 stacks, for the fight
  206300  Dean's Rod                AB9 the punishment, Shadow, base point = the damage (Chastise 36863's SV 792)
  206301  Ill-Gotten Gains          AB10 the fortune's buff: +40% damage and healing done for 15 s (SV 12473)
  206302  Veil of Shadow            AB11 the tank-only copy of 17820: 1.5 s, healing taken -50% for 10 s, Curse
  206303-206314 spare

Visual ids are WP-V's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, DispelType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    RESOLVE_RAW,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, custom_attr, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_B,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    AX_DEANS_ROD,
    AX_ILL_GOTTEN_GAINS,
    AX_RULE_ANNOUNCEMENT,
    DISPLAY_INVISIBLE_STALKER,
)

_S9 = 'Scholomance build WP-S9 (Lord Alexei Barov)'
_SCRIPT_EXCLUDED = 'Scholomance: a percent of reference health, set by the script (DungeonKit::RefFlatOn)'

_SCHOOL_MASK_ALL = 127
_INTERRUPT_FLAGS_STANDARD = 15     # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_SV_VEIL_OF_SHADOW = 561           # Veil of Shadow 17820's own
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000     # SharedDefines.h: the aura persists through death
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000      # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_CU_AURA_CANNOT_BE_SAVED = 0x01000000        # SpellInfo.h SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED

_ICON_NO_RUNNING = 180             # Chains of Ice 45524 (feet held)
_ICON_ASSEMBLY = 456               # Battle Shout 6673 (gather)
_ICON_KEEP_DISTANCE = 148          # Intimidating Shout 5246 (scatter)
_ICON_OUT_OF_BOUNDS = 1499         # Blink 1953 (go elsewhere)
_ICON_LINE_UP = 515                # Sweeping Strikes 12328
_ICON_DESKS = 3147                 # Path of Frost 3714
_ICON_ANNOUNCE = 1934              # Commanding Shout 469
_ICON_DEMERIT = 1502               # Runed Golden Rod 13628
_ICON_DEANS_ROD = 243              # Chastise 36863
_ICON_ILL_GOTTEN_GAINS = 3450      # Coin Toss 60450
_ICON_VEIL_OF_SHADOW = 173         # Veil of Shadow 17820

# Held back until wave B binds this boss (_common.py BIND_WAVE_B; R-A S-11): stock until then.
if BIND_WAVE_B:
    creature_template_columns(10504, **boss_columns('boss_lord_alexei_barov_rework', 52.425, DamageModifier=6.0))

    # --- 300543 The Barov Fortune ------------------------------------------------------------------------------------
    barov_fortune_300543 = creature_template(
        300543, 'The Barov Fortune',
        **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
           'flags_extra': 0x40 | 0x80, 'ScriptName': 'npc_sc_barov_fortune'},
    )
    creature_model(300543, display_id=DISPLAY_INVISIBLE_STALKER)

    # --- AB1-AB7 the rules' icons ------------------------------------------------------------------------------------

    def _rule_icon(spell_id: int, name: str, icon: int, rule: str, desc: str, aura_desc: str):
        return spell(
            id=spell_id, name=name, school=School.SHADOW, dispel=0, mechanic=0,
            attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
            category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=12000,
            effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                            implicit_target_a=TARGET_UNIT_TARGET_ANY)],
            spell_icon_id=icon,
            notes=f'{_S9}, {rule}: the rule\'s icon on everyone in the vault from his yell to the window\'s close '
                  '(AlexeiLogic.h: 9 s normal, 10 s heroic; the solo lesson 7-9 s). Alexei adds it (Unit::AddAura) and '
                  'sets its duration; the rule book removes it at the close. A DUMMY debuff: the registry mechanic '
                  'beside it judges the rule. Dispel none, NO_IMMUNITIES.',
            raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1, AttributesEx4=ATTR4_NO_CAST_LOG),
        )

    rule_no_running_206290 = _rule_icon(
        206290, 'No Running in the Halls!', _ICON_NO_RUNNING, 'AB2 No running',
        'Stand still until the window closes.',
        'Do not move more than a yard until the window closes. Turning and casting are fine.')
    rule_assembly_206291 = _rule_icon(
        206291, 'Assembly!', _ICON_ASSEMBLY, 'AB3 Assembly',
        'Gather in threes when the window closes.',
        'Be within 6 yards of at least two others when the window closes.')
    rule_keep_distance_206292 = _rule_icon(
        206292, 'Keep Your Distance!', _ICON_KEEP_DISTANCE, 'AB4 Keep your distance',
        'Spread out before the window closes.',
        'Nobody may be within 8 yards of you when the window closes.')
    rule_out_of_bounds_206293 = _rule_icon(
        206293, 'Go to the Corner!', _ICON_OUT_OF_BOUNDS, 'AB5 Out of bounds',
        'A third of the vault is out of bounds.',
        'Stay out of the marked third of the vault until the window closes.')
    rule_line_up_206294 = _rule_icon(
        206294, 'Line Up!', _ICON_LINE_UP, 'AB6 Line up (heroic)',
        'Line up in the marked lane.',
        'Be inside the marked lane when the window closes.')
    rule_desks_206295 = _rule_icon(
        206295, 'To Your Desks!', _ICON_DESKS, 'AB7 To your desks (heroic)',
        'Every student has a desk.',
        'Be on your own desk when the window closes.')

    code_of_conduct_206296 = self_visual(
        206296, 'Code of Conduct', AX_RULE_ANNOUNCEMENT,
        f'{_S9}, AB1: the look on Alexei as he announces a rule (cast on himself, triggered, with the yell). '
        "Commanding Shout 469's SpellVisual 246 (the shout state).",
        icon=_ICON_ANNOUNCE, school=School.SHADOW)

    # --- AB4 / AB5 the rules the registry resolves as damage kinds ---------------------------------------------------

    out_of_bounds_206297 = resolve_copy(
        206297, 'Out of Bounds', School.SHADOW, 'You are out of bounds.',
        f'{_S9}, AB5 Out of bounds: the forbidden third\'s tick, every second of the 6 s window, on everyone inside '
        '(a 30 x 19.5 yd rectangle across the vault). No damage (the registry mechanic has none): the hit puts the '
        'break in the failure ledger under this name, and the Dean\'s Rod (206300) is the punishment and the impact. '
        'One Demerit per player per announcement, however many ticks catch them. Copy of the resolve spell 205001 '
        '(Shadow).',
        icon=_ICON_OUT_OF_BOUNDS)

    keep_your_distance_206298 = resolve_copy(
        206298, 'Keep Your Distance', School.SHADOW, 'Too close to another student.',
        f'{_S9}, AB4 Keep your distance: the 8 yd spread at the window\'s close on everyone within 8 yd of another '
        'player. No damage (as 206297): the ledger entry; the Dean\'s Rod is the punishment. Copy of the resolve '
        'spell 205001 (Shadow).',
        icon=_ICON_KEEP_DISTANCE)

    # --- AB9 Demerit and the Dean's Rod ------------------------------------------------------------------------------

    demerit_206299 = spell(
        id=206299, name='Demerit', school=School.SHADOW, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=_ICON_DEMERIT,
        notes=f'{_S9}, AB9: one stack per break (one per player per announcement: a broken rule, either rule of a '
              'heroic pair, or a fortune taken), cap 5 (CumulativeAura), for the fight (removed on his death, evade '
              'and reset). Alexei adds it (DungeonKit::AddStacks, caster Alexei); the Dean\'s Rod reads the stacks '
              'held before the new one. Dispel none, NO_IMMUNITIES. It lasts the fight and nothing past it (R-B '
              'N9-1): persists through death (a battle resurrection keeps the ladder), leaves with the map '
              '(AuraInterruptFlags CHANGE_MAP: a hearth or a release out of the instance) and is never saved '
              '(CU_AURA_CANNOT_BE_SAVED: a logout keeps no stale stacks).',
        raw_overrides=kit_raw('Stacks up to $u times. Each Demerit makes the Dean\'s Rod hit harder.',
                              'The Dean\'s Rod hits harder for each Demerit.', CastingTimeIndex=1, CumulativeAura=5,
                              AttributesEx3=_ATTR3_ALLOW_AURA_WHILE_DEAD, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )
    custom_attr(demerit_206299, _CU_AURA_CANNOT_BE_SAVED)

    deans_rod_206300 = spell(
        id=206300, name='Dean\'s Rod', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_EXCLUDED)],
        spell_icon_id=_ICON_DEANS_ROD,
        notes=f'{_S9}, AB9 the Dean\'s Rod: on the spot, on every Demerit, cast by Alexei (triggered, any range, no '
              'LoS): the base plus 50% of the base per Demerit already held, capped at the 5th: normal 20, 30, 40, 50, '
              '60%; heroic 30, 45, 60, 75, 90% (ruling 19) of the reference row (the tank\'s row on a tank), + 1 '
              'Weakened (ruling 21, the script). The damage is base point 0 (CastCustomSpell, DieSides 0, from '
              'DungeonKit::RefFlatOn), so the target\'s own reductions apply; ignores caster modifiers, cannot crit. '
              'The detention lesson\'s failure hit uses it too (15% / 25%, cast by the lesson\'s owner). Chastise '
              '36863\'s SV 792 on the target (Lash 6607\'s SV 808 draws nothing, VISUALS-REPORT).',
        raw_overrides=kit_raw('The dean punishes a broken rule.', SpellVisualID_1=AX_DEANS_ROD, **RESOLVE_RAW),
    )

    # --- AB10 the Barov fortune --------------------------------------------------------------------------------------

    ill_gotten_gains_206301 = spell(
        id=206301, name='Ill-Gotten Gains', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=15000,
        effects=[
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=39,
                   misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER),
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=39,
                   misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER),
        ],
        spell_icon_id=_ICON_ILL_GOTTEN_GAINS,
        notes=f'{_S9}, AB10: the fortune\'s buff, cast by the taker on themselves (triggered) as they walk over a gold '
              'pile: +40% damage done (every school) and +40% healing done (BasePoints 39 + DieSides 1) for 15 s; the '
              'Demerit comes with it (the script). A damage dealer near 1,000 DPS gains about 6,000 damage (SC). '
              'Ill-Gotten Gains 57718\'s loot sparkles, SV 12473 (Harpoon Loot Sparkles; apart from the Deadmines '
              'Pocketed / Gold Fever looks).',
        raw_overrides=kit_raw('Damage and healing done increased by $s1% for $d.',
                              'Damage and healing done increased by $s1%.', CastingTimeIndex=1,
                              SpellVisualID_1=AX_ILL_GOTTEN_GAINS, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    # --- AB11 Veil of Shadow -----------------------------------------------------------------------------------------

    veil_of_shadow_206302 = spell(
        id=206302, name='Veil of Shadow', school=School.SHADOW, dispel=DispelType.CURSE, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=1500, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=30.0, duration_ms=10000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_PCT, base_points=-51,
                        misc_value=126, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                        potency_excluded='Veil of Shadow: a flat -50% healing taken, not a damage or heal value')],
        spell_icon_id=_ICON_VEIL_OF_SHADOW,
        notes=f'{_S9}, AB11: the stock Veil of Shadow 17820 on the tank only (never the stock id: stock hits everyone '
              'within 8 yd, the whole Assembly, for -75% 15 s). A 1.5 s cast on his victim at 5-12 s, then every '
              '15-25 s, never during a rule; healing taken -50% for 10 s (BasePoints -51 + DieSides 1). Curse '
              '(DispelType 2); interruptible as the stock spell (InterruptFlags 15, PreventionType silence). On the '
              'descriptor\'s interrupt and dispel lists: both are rewards. Stock look, SV 561, icon 173.',
        raw_overrides=kit_raw('Reduces healing effects on an enemy by $s1% for $d.',
                              'Healing effects reduced by $s1%.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                              PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                              AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, SpellVisualID_1=_SV_VEIL_OF_SHADOW),
    )
