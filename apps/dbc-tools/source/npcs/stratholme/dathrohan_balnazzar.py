"""
Stratholme build WP-S7: Grand Crusader Dathrohan (10812) and Balnazzar (10813), normal and heroic
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows DB and BZ, s3.5 row S7, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 2077-2166, design ST 1769-2076). WP-S7 owns this file (its spells:
kSpellsDathrohan 206545-206574 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; DathrohanLogic.h
names the same ids). The hard mode (S8, the Grand Lie) declares its own in balnazzar_hard_mode.py.

- 10812 Grand Crusader Dathrohan and 10813 Balnazzar: one script on both (boss_dathrohan_balnazzar_rework; the AI
  survives UpdateEntry either way), SmartAI off (the SQL rev drops 10812's eighteen rows), the build spec's normal
  health (250k: HealthModifier 96.525 on the level 62 paladin base 2,590; Balnazzar 220k: 84.942), stun immunity 1972,
  INSTANCE_BIND. DamageModifier 3.5 for Dathrohan (the stock value: base SQL; the live 8.5 is a mod-progression
  leftover) and 9 for Balnazzar (stock). Heroic 340k / 300k are WP-H's overrides (source/world/dungeons/stratholme.py).
- 300608 Infernal (BZ3): Towering Infernal 17818's display 7029, level 60 demon, rank 0 (an elite would take the
  heroic tier's health, not stratholme.py's override), 12,000 health (3,052 x 3.93185), heroic 18,000 (WP-H's
  `_KIT_ADD_HEROIC`), the hard mode's 25,000 by script. npc_st_infernal: the nearest
  player, a strike every 2 s, Immolation within 5 yd; it crumbles at 45 s. No melee of its own (DamageModifier 0).

Spells. The registry-owned hits go through dungeon copies of the mod-boss-mechanics resolve spell (the percent of the
reference row; the combat log names the mechanic); the split share, the cone target's hit, the Immolation tick and the
Vampiric heal carry a base point the script computes; the Judgment's target hit and the Infernal's strike are the kit's
percent spell (hundredths, heroic in MiscValueB); Nightmare is the kit's periodic percent spell:

  206545  Sacred Ground          DB1 the 3 s cast bar (yell 1 true / 2 lie)
  206546  Sacred Ground          DB1 the gold ground at his feet, 8 yd area look (Consecration's SV 5600), 3.5 s
  206547  Desecration            DB1 the lie's shadow under the gold, 10 yd area look (Desecration's SV 8506; normal)
  206548  Holy Wrath             DB1 true: resolve copy (Holy) on each non-tank outside the shelter, 40% / 50%
  206549  Shadow Eruption        DB1 lie: resolve copy (Shadow) on each non-tank inside 10 yd, 40% / 50%
  206550  Judgment               DB2 the gold mark, 5 s (true; the lie too on heroic)
  206551  Judgment               DB2 the lie's dark mark, 5 s (normal)
  206552  Judgment               DB2 true: one share of the burst (Holy, base point 0 from DungeonKit::SplitShares)
  206553  Judgment               DB2 lie: resolve copy (Shadow) on the other non-tanks within 8 yd, 40% / 50%
  206554  Judgment               DB2 lie: the marked player's 15% (Shadow, the kit's percent spell)
  206555  Unmasked               DB3 the mark on every non-tank as the transform stun ends, 5 s
  206556  Unmasked               DB3 resolve copy (Shadow) on the others within 8 yd, 30% + Weakened
  206557  Carrion Swarm          BZ1 the 2.5 s cast bar (V-2's 30 yd fan, SV_CARRION_FAN, follows his facing)
  206558  Carrion Swarm          BZ1 resolve copy (Shadow) on everyone in the cone but its target, 40%
  206559  Carrion Swarm          BZ1 the target's 20% (Shadow, base point 0 from the script)
  206560  Inferno                BZ2 the 3.5 s cast bar (yell 6)
  206561  Inferno                BZ2 resolve copy (Fire) in the 8 yd circle, 50%
  206562  Inferno                BZ2 the falling meteor at the spot (a dest DUMMY; SV 4859), 2.5 s before the hit
  206563  Immolation             BZ3 the ring of flames on the Infernal (SV 8313, a STATE look)
  206564  Immolation             BZ3 the 1 s tick on every player within 5 yd (Fire, base point 0 from the script)
  206565  Stoked                 BZ3 heroic: a stack on the Infernal every 5 s (the count; the script reads its age)
  206566  Sleep                  BZ4 the 2 s interruptible cast and the 5 s Magic sleep (not broken by damage)
  206567  Nightmare              BZ4 30% Shadow over 6 s after the sleep (not dispellable)
  206568  Nightmare              BZ4 heroic, a missed Sleep: resolve copy (Shadow) on every player each 2 s, 10%
  206569  Vampiric Aura          BZ5 the passive on him from the transform
  206570  Vampiric Aura          BZ5 the heal per kit hit landed (base point 0 from the script)
  206571  Infernal Strike        BZ3 the Infernal's swing every 2 s (Physical, 4% / 5%)
  206572-206574 spare.

Visual ids are WP-V-2's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_NOT_A_PROC,
    RESOLVE_RAW,
    TARGET_UNIT_TARGET_ENEMY,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    KIT_CREATURE_SCARLET,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BA_DEATH_KNELL,
    BZ_VAMPIRIC_HEAL_ALT,
    DA_HOLY_WRATH,
    DA_IMMOLATION,
    DA_IMMOLATION_ALT,
    DA_LIE_GROUND,
    DA_METEOR,
    DA_SLEEP,
    DA_TRUE_GROUND,
    DA_TRUE_JUDGMENT,
    DISPLAY_INFERNAL,
    SV_CARRION_FAN,
    SV_LIE_JUDGMENT,
)

_DB = 'Stratholme build WP-S7 (Dathrohan and Balnazzar)'

# The Infernal's heroic template (source/world/heroic_ids.lock): wave 2 mints its kit adds in entry order after wave
# 1's (300602 Gutter Rat 310192, 300604 Playmate 310193, 300608 Infernal 310194; handoff s3.3). Literal ids in the
# creature_template() call: source/world/dungeons/stratholme.py finds the declared kit adds by that text.
INFERNAL_HEROIC = 310194

_TARGET_DEST_CASTER = 18
_TARGET_DEST_DYNOBJ_ALLY = 29
_TARGET_DEST_DEST = 87
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_DISPEL_MAGIC = 1
_MECHANIC_SLEEP = 10
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000      # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_INTERRUPT_FLAGS_STANDARD = 15               # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_RANGE_SLEEP = 30.0

# DathrohanLogic.h numbers mirrored here (lib/test_stratholme_dathrohan.py pins both sides).
_SACRED_GROUND_CAST_MS = 3000                # kSacredGroundCastMs
_GROUND_LOOK_MS = 3500                       # kGroundLookMs
_SHELTER_YD = 8.0                            # kShelterRadius
_ERUPTION_YD = 10.0                          # kEruptionRadius
_JUDGMENT_MARK_MS = 5000                     # kJudgmentMarkMs
_JUDGMENT_TARGET_HUNDREDTHS = 1500           # kJudgmentTargetPct (15%, both difficulties)
_UNMASKING_MARK_MS = 5000                    # kUnmaskingMarkMs
_CARRION_CAST_MS = 2500                      # kCarrionCastMs
_INFERNO_CAST_MS = 3500                      # kInfernoCastMs
_SLEEP_CAST_MS = 2000                        # kSleepCastMs
_SLEEP_MS = 5000                             # kSleepMs
_NIGHTMARE_MS = 6000                         # kNightmareMs
_NIGHTMARE_TICK_MS = 1000                    # kNightmareTickMs
_NIGHTMARE_TICK_HUNDREDTHS = 500             # kNightmarePct / 6 ticks: 5% a second, both difficulties
_STOKE_MAX = 7                               # StokeStacks' cap ((12 - 5) / 1)
_STRIKE_NORMAL_HUNDREDTHS = 400              # kInfernalStrikePct.normal
_STRIKE_HEROIC_HUNDREDTHS = 500              # kInfernalStrikePct.heroic
_INFERNAL_HEALTH_MODIFIER = 3.93185          # 12,000 on the level 60 warrior base 3,052 (kInfernalHealth.normal)

_ICON_CONSECRATION = 51                      # Consecration 26573
_ICON_DESECRATION = 140                      # Desecration 36473
_ICON_HOLY_WRATH = 158                       # Holy Wrath 2812
_ICON_JUDGEMENT = 205                        # Judgement of Light 20271
_ICON_JUDGEMENT_DARK = 1980                  # Judgement of Darkness 34112
_ICON_CARRION_SWARM = 116                    # Carrion Swarm 31306
_ICON_INFERNO = 460                          # Inferno 31299 / Immolation 31304
_ICON_SLEEP = 44                             # Sleep 31298
_ICON_FEAR = 98                              # Fear 6215 (Nightmare)
_ICON_VAMPIRIC_AURA = 147                    # Vampiric Aura 31317
_SV_CARRION_SWARM = 7835                     # Carrion Swarm 31306's own look (the impact on each player hit)
_SV_STRIKE = 39                              # Strike 11976

_SCRIPT_BASE_POINT = 'Stratholme: a percent of reference health, set by the script (DungeonKit::RefFlat)'
_SCRIPT_SHARE = 'Stratholme: a share of the Judgment, the script\'s base point (DungeonKit::SplitShares)'
_SCRIPT_HEAL = 'Stratholme: a percent of the boss\'s maximum health, set by the script (Vampiric Aura)'
_PERCENT_SPELL = 'spell_dungeon_refflat_damage'
_PERCENT_PERIODIC = 'spell_dungeon_refflat_periodic'
_PERCENT_EXCLUDED = ('Stratholme: a percent of reference health in hundredths, set at launch by the kit\'s '
                     'spell_dungeon_refflat_* (DungeonKit::RefFlatOn)')

# The hits whose damage the script sets carry the resolve attribute set (no active defense, redirection, reflection or
# threat; ignore line of sight; cannot crit; not a proc; always hit; ignore caster modifiers).
_SCRIPT_HIT_RAW = {k: v for k, v in RESOLVE_RAW.items() if k != 'CastingTimeIndex'}

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(10812, **boss_columns(
        'boss_dathrohan_balnazzar_rework', 96.525, damage_modifier=3.5,
    ))
    creature_template_columns(10813, **boss_columns(
        'boss_dathrohan_balnazzar_rework', 84.942, damage_modifier=9,
    ))

    # --- 300608 Infernal --------------------------------------------------------------------------------------------
    infernal_300608 = creature_template(
        300608, 'Infernal', **{
            **KIT_CREATURE_SCARLET, 'type': 3, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
            'unit_flags': 0, 'HealthModifier': _INFERNAL_HEALTH_MODIFIER, 'DamageModifier': 0.0,
            'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
            'mingold': 0, 'maxgold': 0, 'speed_run': 1.0, 'ScriptName': 'npc_st_infernal',
            'difficulty_entry_1': INFERNAL_HEROIC,
        },
    )
    creature_model(300608, display_id=DISPLAY_INFERNAL)

    # --- DB1 Sacred Ground --------------------------------------------------------------------------------------------

    sacred_ground_bar_206545 = cast_bar(
        206545, 'Sacred Ground', _SACRED_GROUND_CAST_MS, 'Consecrates the ground around the Grand Crusader.',
        f'{_DB}, DB1: the 3 s cast bar, sword raised (yell 1 "Gather in the Light!" when true, yell 2 "Bow before my '
        'Might!" when a lie); he stands still while he casts. Not interruptible (cast_bar): the registry owns the '
        'answer (true: a Stack of 8 yd on him and Holy Wrath 206548 on the non-tanks outside; lie: the 10 yd circle '
        'with 206549). The ground looks 206546 / 206547 play beside it.',
        icon=_ICON_CONSECRATION, school=School.HOLY,
    )

    true_ground_206546 = spell(
        id=206546, name='Sacred Ground', school=School.HOLY, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=_GROUND_LOOK_MS,
        effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                        implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY,
                        radius_yards=_SHELTER_YD)],
        spell_icon_id=_ICON_CONSECRATION,
        notes=f'{_DB}, DB1: visual only, the gold ground at his feet for the cast (3.5 s), on every Sacred Ground: the '
              'truth\'s look, and on heroic the lie wears it too (the mask is perfect: only the yell tells). '
              'TARGET_DEST_CASTER / TARGET_DEST_DYNOBJ_ALLY with a DUMMY aura (the Baron\'s rot look\'s shape: it '
              'reaches nobody). Consecration 26573\'s SV 5600 (V-2 DA_TRUE_GROUND; unconfirmed whether the client '
              'scales it to the 8 yd radius).',
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=DA_TRUE_GROUND, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    lie_ground_206547 = spell(
        id=206547, name='Desecration', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=_GROUND_LOOK_MS,
        effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                        implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY,
                        radius_yards=_ERUPTION_YD)],
        spell_icon_id=_ICON_DESECRATION,
        notes=f'{_DB}, DB1 lie on normal: visual only, shadow under the gold (with 206546 on the same spot, V-2\'s '
              'pick): the lie looks wrong on normal. Never on heroic. Desecration 36473\'s SV 8506 (V-2 '
              'DA_LIE_GROUND, a bone crack), 3.5 s.',
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=DA_LIE_GROUND, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    holy_wrath_206548 = resolve_copy(
        206548, 'Holy Wrath', School.HOLY, 'The Light strikes those who would not gather in it.',
        f'{_DB}, DB1 true: the bolts on every non-tank outside the 8 yd shelter when the cast ends: 40% (heroic 50%) '
        'of the non-tank row, no Weakened (over 30%), through the registry (DungeonKit::RegistryHit on the players '
        'the shelter Stack did not hold). Copy of the resolve spell 205001 (Holy). Holy Wrath 2812\'s SV 126 (gold '
        'hands, a missile, a gold burst; V-2 DA_HOLY_WRATH) on every player hit.',
        icon=_ICON_HOLY_WRATH, visual=DA_HOLY_WRATH,
    )

    shadow_eruption_206549 = resolve_copy(
        206549, 'Shadow Eruption', School.SHADOW, 'Shadow erupts around the Grand Crusader.',
        f'{_DB}, DB1 lie: the eruption on every non-tank inside 10 yd of him when the cast ends: 40% (heroic 50%), '
        'no Weakened (over 30%), through the registry (a circle Zone on him, non-tanks only). Copy of the resolve '
        'spell 205001 (Shadow). Shadow Burst 28447\'s SV 45 (a shadow nova on the chest) on every player hit.',
        icon=_ICON_DESECRATION, visual=BA_DEATH_KNELL,
    )

    # --- DB2 Judgment -------------------------------------------------------------------------------------------------

    def _mark(spell_id: int, visual: int, icon: int, notes: str):
        return spell(
            id=spell_id, name='Judgment', school=School.HOLY, dispel=0, mechanic=0,
            attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
            category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_JUDGMENT_MARK_MS,
            effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                            implicit_target_a=TARGET_UNIT_TARGET_ANY)],
            spell_icon_id=icon, notes=notes,
            raw_overrides=kit_raw('The Grand Crusader passes judgment.', 'Judgment is coming for you. Listen to his '
                                  'words.', CastingTimeIndex=1, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                                  AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
        )

    judgment_mark_206550 = _mark(
        206550, DA_TRUE_JUDGMENT, _ICON_JUDGEMENT,
        f'{_DB}, DB2: the 5 s mark on a random non-tank (yell 3 "$n, share the Light\'s judgment!" true, yell 4 '
        '"$n, fear my judgment!" lie), cast by him (triggered); the true one on normal and every one on heroic (the '
        'lie wears it). A DUMMY aura: the tell only; the registry Stack (true) or RunOut (lie) owns the answer, the '
        'script removes it at the resolve. Same neutral tooltip on both marks. Dispel none, NO_IMMUNITIES, CHANGE_MAP. '
        'Judgement of Light 20271\'s SV 5651 (V-2 DA_TRUE_JUDGMENT).',
    )

    judgment_dark_mark_206551 = _mark(
        206551, SV_LIE_JUDGMENT, _ICON_JUDGEMENT_DARK,
        f'{_DB}, DB2 lie on normal: the same mark with the lie\'s dark judgement (V-2\'s minted SV 90514: shadow '
        'hands and a red judgement flash): on normal the lie looks wrong. Never on heroic.',
    )

    judgment_share_206552 = spell(
        id=206552, name='Judgment', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_SHARE)],
        spell_icon_id=_ICON_JUDGEMENT,
        notes=f'{_DB}, DB2 true: one share of the holy burst, cast (triggered) on each non-tank inside the 6 yd stack '
              'on the marked player when the mark ends (the marked player always shares): 90% (heroic 120%) of the '
              'non-tank row split evenly (alone 90%, two 45%, four 22.5%; DungeonKit::SplitShares, the base point; '
              'DieSides 0: exact). No Weakened on a share. The resolve attribute set. SV 5651 on every share.',
        raw_overrides=kit_raw('The Light\'s judgment, shared.', **{**_SCRIPT_HIT_RAW,
                                                                    'SpellVisualID_1': DA_TRUE_JUDGMENT}),
    )

    judgment_burst_206553 = resolve_copy(
        206553, 'Judgment', School.SHADOW, 'A false judgment bursts from its target.',
        f'{_DB}, DB2 lie: the burst on every other non-tank within 8 yd of the marked player when the mark ends: 40% '
        '(heroic 50%), no Weakened (over 30%), through the registry (a RunOut on the target, non-tanks only). Copy '
        'of the resolve spell 205001 (Shadow). V-2\'s SV 90514 on every player hit.',
        icon=_ICON_JUDGEMENT_DARK, visual=SV_LIE_JUDGMENT,
    )

    judgment_target_206554 = spell(
        id=206554, name='Judgment', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_JUDGMENT_TARGET_HUNDREDTHS - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_PERCENT_EXCLUDED)],
        spell_icon_id=_ICON_JUDGEMENT_DARK,
        notes=f'{_DB}, DB2 lie: the marked player\'s own hit when the mark ends: 15% of the reference row on both '
              'difficulties (the kit\'s spell_dungeon_refflat_damage: shown value 1500 hundredths, MiscValueB the '
              'same). Not avoidable, so no Weakened. The resolve attribute set. SV 90514.',
        raw_overrides=kit_raw('A false judgment.', **{**_SCRIPT_HIT_RAW, 'SpellVisualID_1': SV_LIE_JUDGMENT,
                                                      'EffectMiscValueB_1': _JUDGMENT_TARGET_HUNDREDTHS}),
    )
    scripted_by(judgment_target_206554, _PERCENT_SPELL)

    # --- DB3 The Unmasking ------------------------------------------------------------------------------------------

    unmasking_mark_206555 = spell(
        id=206555, name='Unmasked', school=School.SHADOW, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_UNMASKING_MARK_MS,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=_ICON_JUDGEMENT_DARK,
        notes=f'{_DB}, DB3: as the transform stun ends, every non-tank gets the lie\'s mark at once ("the lies come '
              'all at once"), 5 s; the registry Spread (8 yd, 30% + Weakened, 206556) owns the hit. A DUMMY aura, '
              'Dispel none, NO_IMMUNITIES, CHANGE_MAP. V-2\'s SV 90514 (the lie judgment).',
        raw_overrides=kit_raw('The lies come all at once.', 'You will burst with shadow. Stand apart from your '
                              'allies.', CastingTimeIndex=1, SpellVisualID_1=SV_LIE_JUDGMENT,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )

    unmasking_burst_206556 = resolve_copy(
        206556, 'Unmasked', School.SHADOW, 'The lies burst from everyone at once.',
        f'{_DB}, DB3: each marked non-tank bursts when the mark ends: 30% and 1 Weakened to every other non-tank '
        'within 8 yd, through the registry (a Spread). Copy of the resolve spell 205001 (Shadow). Shadow Burst\'s SV '
        '45 on every player hit.',
        icon=_ICON_JUDGEMENT_DARK, visual=BA_DEATH_KNELL,
    )

    # --- BZ1 Carrion Swarm --------------------------------------------------------------------------------------------

    carrion_bar_206557 = cast_bar(
        206557, 'Carrion Swarm', _CARRION_CAST_MS, 'A wave of carrion bats, aimed at one victim.',
        f'{_DB}, BZ1: the 2.5 s cast bar; the 60 degree, 30 yd registry cone aims at a random non-tank live (it tracks '
        'them through the cast; heroic: a second cone at another non-tank 1.5 s later, no second bar). Not '
        'interruptible (cast_bar). V-2\'s minted 30 yd fan (SV_CARRION_FAN 90513, a PrecastKit that follows his '
        'facing; the script turns him to the target every update).',
        icon=_ICON_CARRION_SWARM, visual=SV_CARRION_FAN, school=School.SHADOW,
    )

    carrion_hit_206558 = resolve_copy(
        206558, 'Carrion Swarm', School.SHADOW, 'A wave of carrion bats.',
        f'{_DB}, BZ1: the cone\'s hit on everyone in it but its target (the target is never a carrier: the registry '
        'cone\'s eligibility), the tank too (its own row): 40%, no Weakened (over 30%). Copy of the resolve spell '
        '205001 (Shadow). Carrion Swarm 31306\'s SV 7835 on every player hit.',
        icon=_ICON_CARRION_SWARM, visual=_SV_CARRION_SWARM,
    )

    carrion_target_206559 = spell(
        id=206559, name='Carrion Swarm', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BASE_POINT)],
        spell_icon_id=_ICON_CARRION_SWARM,
        notes=f'{_DB}, BZ1: the cone\'s target always takes 20% (it leads the cone and cannot dodge it, so no '
              'Weakened), cast (triggered) at the resolve with the base point the script computes (RefFlatOn, the '
              'tank row on a tank). The hard mode passes its own percent (25%). The resolve attribute set. SV 7835.',
        raw_overrides=kit_raw('The swarm finds its victim.', **{**_SCRIPT_HIT_RAW,
                                                                'SpellVisualID_1': _SV_CARRION_SWARM}),
    )

    # --- BZ2 Inferno and BZ3 the Infernal -----------------------------------------------------------------------------

    inferno_bar_206560 = cast_bar(
        206560, 'Inferno', _INFERNO_CAST_MS, 'Calls an infernal down from the sky.',
        f'{_DB}, BZ2: the 3.5 s cast bar (yell 6 "Rise, servant of the Legion!"); the 8 yd registry circle on a random '
        'non-tank\'s spot at the cast start owns the hit (206561). Not interruptible (cast_bar).',
        icon=_ICON_INFERNO, school=School.FIRE,
    )

    inferno_hit_206561 = resolve_copy(
        206561, 'Inferno', School.FIRE, 'A meteor crashes down.',
        f'{_DB}, BZ2: the meteor\'s hit on everyone in the 8 yd circle, the tank too: 50%, no Weakened (over 30%); an '
        'Infernal (300608) rises on the spot. Copy of the resolve spell 205001 (Fire). Inferno 31299\'s SV 4859 '
        '(V-2 DA_METEOR) on every player hit.',
        icon=_ICON_INFERNO, visual=DA_METEOR,
    )

    inferno_look_206562 = spell(
        id=206562, name='Inferno', school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=_ICON_INFERNO,
        notes=f'{_DB}, BZ2: visual only, the falling meteor: he casts it (triggered) at the marked spot 1 s into the '
              '3.5 s bar, so the rock falls for 2.5 s and lands with the hit (V-2: the meteor takes 2.5 s). A DUMMY '
              'on TARGET_DEST_DEST (no handler): Inferno 31299\'s own shape (a destination) and SV 4859.',
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=DA_METEOR, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    immolation_look_206563 = spell(
        id=206563, name='Immolation', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_INFERNO,
        notes=f'{_DB}, BZ3: the ring of flames the Infernal wears (cast on itself as it rises): the tell for its 5 yd '
              'burn. A DUMMY aura (npc_st_infernal ticks 206564; a telegraph-only registry circle on it steers the '
              'bots). Flame Patch Periodic 35380\'s SV 8313 (V-2 DA_IMMOLATION, a STATE look).',
        raw_overrides=kit_raw('Burns everyone nearby.', 'Burns everyone within 5 yards every second.', instant=True,
                              SpellVisualID_1=DA_IMMOLATION, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    immolation_tick_206564 = spell(
        id=206564, name='Immolation', school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BASE_POINT)],
        spell_icon_id=_ICON_INFERNO,
        notes=f'{_DB}, BZ3: the Infernal\'s 1 s tick on every player within 5 yd: 5% of the reference row; heroic and '
              'the hard mode stoke it, +1% every 5 s it lives, up to 12% at 35 s (npc_st_infernal sets the base point, '
              'RefFlatOn: the tank row on a tank). Each tick heals Balnazzar (BZ5). The resolve attribute set. '
              'Immolation 20153\'s SV 2519 (V-2 DA_IMMOLATION_ALT, a chest puff) on every tick.',
        raw_overrides=kit_raw('Burns everyone nearby.', **{**_SCRIPT_HIT_RAW,
                                                           'SpellVisualID_1': DA_IMMOLATION_ALT}),
    )

    stoked_206565 = spell(
        id=206565, name='Stoked', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_INFERNO,
        notes=f'{_DB}, BZ3 heroic (and the hard mode): the count on the Infernal, one stack every 5 s it lives, at '
              'most 7 (CumulativeAura 7: 5% + 7 = 12% at 35 s). A DUMMY aura: npc_st_infernal reads its own age, the '
              'stacks show the players how hot it burns. No look.',
        raw_overrides=kit_raw('Burns hotter the longer it lives.', 'Immolation burns hotter.', instant=True,
                              CumulativeAura=_STOKE_MAX, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    infernal_strike_206571 = spell(
        id=206571, name='Infernal Strike', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_STRIKE_NORMAL_HUNDREDTHS - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_PERCENT_EXCLUDED)],
        spell_icon_id=_ICON_INFERNO,
        notes=f'{_DB}, BZ3: the Infernal\'s swing (npc_st_infernal strikes its victim, the nearest player, in melee '
              'range every 2 s and never auto attacks): Physical, 4% normal / 5% heroic of the reference row (the tank '
              'row on a tank; the kit\'s spell_dungeon_refflat_damage: 400 hundredths, EffectMiscValueB 500). Each '
              'strike heals Balnazzar (BZ5). A melee hit (it can miss, be dodged or parried), ignores caster '
              'modifiers, cannot crit. Strike 11976\'s SV 39.',
        raw_overrides=kit_raw('Strikes an enemy.', instant=True, DefenseType=_DEFENSE_MELEE, SpellVisualID_1=_SV_STRIKE,
                              EffectMiscValueB_1=_STRIKE_HEROIC_HUNDREDTHS, AttributesEx2=ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(infernal_strike_206571, _PERCENT_SPELL)

    # --- BZ4 Sleep and Nightmare ----------------------------------------------------------------------------------

    sleep_206566 = spell(
        id=206566, name='Sleep', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_SLEEP,
        attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=_SLEEP_CAST_MS, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=_RANGE_SLEEP, duration_ms=_SLEEP_MS,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=_MECHANIC_SLEEP,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
        spell_icon_id=_ICON_SLEEP,
        notes=f'{_DB}, BZ4: a real 2 s cast on a random non-tank within 30 yd, every 20 s from 14 s into stage 2. '
              'Interruptible: InterruptFlags 15 and PreventionType 1 (a silence stops it); the descriptor\'s interrupt '
              'list, priority 2 (a reward on normal, expected on heroic). Landed: a 5 s sleep (MOD_STUN, mechanic '
              'Sleep, Magic: the dispel list, urgent) that damage does NOT break (AuraInterruptFlags CHANGE_MAP only; '
              'ruling 28: over the 2 s cap on purpose, a dispel check). spell_strat_balnazzar_sleep tells the boss: an '
              'expiry or a dispel starts Nightmare (206567); on heroic a landed Sleep also pulses (206568). '
              'Dread Slumber (S8) puts players to sleep with this aura too. Sleep 31298\'s SV 7320 (V-2 DA_SLEEP).',
        raw_overrides=kit_raw('Puts an enemy to sleep. Damage will not wake them.',
                              'Asleep. Damage will not wake you; a dispel will. Nightmare follows.',
                              InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                              DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=DA_SLEEP, AttributesEx=ATTR1_NO_THREAT,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )
    scripted_by(sleep_206566, 'spell_strat_balnazzar_sleep')

    nightmare_206567 = spell(
        id=206567, name='Nightmare', school=School.SHADOW, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_NIGHTMARE_MS,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                        base_points=_NIGHTMARE_TICK_HUNDREDTHS - 1, die_sides=1, amplitude=_NIGHTMARE_TICK_MS,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_PERCENT_EXCLUDED)],
        spell_icon_id=_ICON_FEAR,
        notes=f'{_DB}, BZ4: after the sleep ends (by time or by dispel: a dispel gets the player back sooner, it does '
              'not skip this), cast by him (triggered): 30% Shadow over 6 s, 5% of the reference row a second (the '
              'kit\'s spell_dungeon_refflat_periodic: 500 hundredths, MiscValueB the same; the tank row on a tank). '
              'Not dispellable (Dispel none, NO_IMMUNITIES). Each tick heals Balnazzar (spell_strat_balnazzar_'
              'nightmare, BZ5). CHANGE_MAP. No look of its own (the ticks show).',
        raw_overrides=kit_raw('Shadow damage over time.', 'Taking Shadow damage every $t1 sec.', CastingTimeIndex=1,
                              EffectMiscValueB_1=_NIGHTMARE_TICK_HUNDREDTHS, DefenseType=_DEFENSE_MAGIC,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )
    scripted_by(nightmare_206567, _PERCENT_PERIODIC, 'spell_strat_balnazzar_nightmare')

    nightmare_pulse_206568 = resolve_copy(
        206568, 'Nightmare', School.SHADOW, 'The sleeper\'s nightmare spills over.',
        f'{_DB}, BZ4 heroic: a Sleep that landed (missed) makes the sleeper\'s Nightmare pulse: 10% to every player of '
        'the fight each 2 s for 6 s (30% to everyone, survivable once), no Weakened, through the registry '
        '(DungeonKit::RegistryHit). Each hit heals Balnazzar (BZ5). Copy of the resolve spell 205001 (Shadow). Shadow '
        'Burst\'s SV 45 on every player hit.',
        icon=_ICON_FEAR, visual=BA_DEATH_KNELL,
    )

    # --- BZ5 Vampiric Aura --------------------------------------------------------------------------------------------

    vampiric_aura_206569 = spell(
        id=206569, name='Vampiric Aura', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_VAMPIRIC_AURA,
        notes=f'{_DB}, BZ5: on Balnazzar from the transform (the stock Vampiric Aura 31317 has no look, ST gap 14): '
              'the tell. A DUMMY aura: the script heals him per kit hit landed (206570). Removed when he reverts to '
              'Dathrohan. Not dispellable.',
        raw_overrides=kit_raw('Every blow of his kit that lands heals him.',
                              'Each hit of his swarm, his fire, his infernals and his nightmares heals him.',
                              instant=True, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    vampiric_heal_206570 = spell(
        id=206570, name='Vampiric Aura', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=_SCRIPT_HEAL)],
        spell_icon_id=_ICON_VAMPIRIC_AURA,
        notes=f'{_DB}, BZ5: the heal per kit hit landed on a player (the cones and their targets, the meteor, '
              'Immolation ticks, Infernal strikes, Nightmare ticks and pulses; never his melee or Mind Blast): 1% '
              '(heroic 2%, the hard mode 3%) of his maximum health, the base point the script computes. Ignores caster '
              'modifiers, cannot crit, no threat. Vampiric Embrace 15286\'s SV 3582 (V-2 BZ_VAMPIRIC_HEAL_ALT: the '
              'Blood Siphon chain needs a victim as caster).',
        raw_overrides=kit_raw('Heals the caster.', instant=True, SpellVisualID_1=BZ_VAMPIRIC_HEAL_ALT,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS | ATTR3_NOT_A_PROC,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )

