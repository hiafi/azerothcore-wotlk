"""
Scarlet Monastery build WP-D14: High Inquisitor Whitemane, with Mograine risen ("Till Death"; 3977 (guid 39946), 3976)
(.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D14, s3.6, s3.8 row D14, s7 #33 A;
build spec docs/dungeons/scarlet-monastery-4-cathedral.md "High Inquisitor Whitemane, with Mograine risen", WM0-WM6).
WP-D14 owns this file (its spells: kSpellsWhitemane 213150-213189 of modules/mod-dungeon-bosses
src/ScarletMonastery/ScarletMonasteryRework.h only; WhitemaneLogic.h names the same ids; the texts are the core SQL rev
rev_whitemane_scarlet_monastery.sql).

- 3977 High Inquisitor Whitemane: boss_whitemane_rework (SmartAI off: W2-SETUP's rev drops rows 0-19 and the lists
  397700-397701), the build spec's normal health (50k = HealthModifier 40.783 on the level 40 paladin class base 1,226),
  stun immunity 1972, INSTANCE_BIND (her kill is the encounter's credit, row 450), the stock DamageModifier 2.2. Held
  back until wave 2 binds her (BIND_WAVE_2). Heroic 220k is WP-H's override
  (source/world/dungeons/scarlet_monastery.py).
- Mograine 3976 is D13's (last_stand.py): his finale health (45k / 200k) is set by the script at the rising.
- No creature or object of its own (the vigil Fairbanks and the spirit are D14H's).

Spells. The registry's hits are dungeon copies of the mod-boss-mechanics resolve spell (the lane, the pillars on the
others); the hits the script aims itself (Holy Smite, the marked player's pillar, the Vigil Flame's shares) are plain
SCHOOL_DAMAGE spells whose amount is the script's base point (DungeonKit::RefFlat, the tank row on the tank; DieSides 0
so the base point is the amount). Every damage spell ignores caster modifiers (rule 2):

  213150  Deep Sleep           WM1 the rising: everyone within 100 yd asleep up to 3 s, damage wakes (SV 87)
  213151  Scarlet Resurrection WM1 the 2 s raise (Physical, not interruptible: a Smite kick never locks it; SV 1443)
  213152  Scarlet Resurrection WM1a her save channel, 10 s at most (the script ends it at 10 / 8 s; Physical; SV 1443)
  213153  Scarlet Resurrection WM1 / WM1a Mograine rises (SV 1443 on him)
  213154  Lay on Hands         WM1b his save channel, 6 s at most (the script ends it at 6 / 5 s; Physical; SV 132)
  213155  Lay on Hands         WM1b she rises (SV 132 on her)
  213156  To Her Side          WM2 the lane's hit (resolve copy, Physical), 30% / 45% + Weakened, the tank too
  213157  To Her Side          WM2 his charge (Charge's SV 867)
  213158  To Her Side          WM2a heroic: his body shield, 6 s (Divine Shield's state SV 154)
  213159  Penance              WM3 the 3 s mark on a player (the yellow rune ring, shipped SV 90614)
  213160  Penance              WM3 the pillar on the others (resolve copy, Holy), 30% / 45% + Weakened
  213161  Penance              WM3 the marked player's own hit (script), 20% / 30% Holy
  213162  Penance              WM3 the pillar's look on a marked player (minted 6 yd holy pillar SV 90564)
  213163  Penance              WM3 her hands as she marks (Penance 47540's SV 10980)
  213164  Heal                 WM4 3 s on Mograine, 6% / 20% of his health (HEAL_PCT, the script's base point);
                               interruptible (SV 135)
  213165  Power Word: Shield   WM4a on Mograine, absorbs 5% of his health (the script's base point); Magic: purgeable
                               (SV 784)
  213166  Holy Smite           WM6 her 2.5 s filler, 10% / 15% Holy (script); interruptible (SV 128)
  213167  Vigil Flame          WM5 heroic: the flame on its carrier (the shipped held torch SV 90603)
  213168  Vigil Flame          WM5 a share of the flare (script), 55% each, 110% unshared or Seared, Holy
  213169  Seared               WM5a the old carrier, 19 s (the hard mode's phase 1: 15 s, set by the script)
                               (Burning Brand's state SV 1946)
  213170  Vigil Flame          WM5 the pass's look on the new carrier (Holy Fire's SV 3400)
  213171-213189 spare.

Holy Smite and Heal (Holy) are the only interruptible casts of the slice. Every bar she or Mograine must play (the
raise, both save channels) is Physical, so a kick on Smite or Heal never locks it (handoff s3.5 rule 5). Retired here:
Dominate Mind 14515, the stock Heal 12039, Power Word: Shield 22187 and Holy Smite 9481 values (the copies above), and
Deep Sleep 9256 / Scarlet Resurrection 9232 / Lay on Hands 9257 as casts (their looks only). Kept: Mograine's Crusader
Strike 14518, Retribution Aura 8990 and Divine Storm (LS5, D13's 213104-213106). Visual ids are WP-V's (._visuals;
every look is unconfirmed until seen in game).
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
from lib.dsl.registry import creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    WM_BODY_SHIELD,
    WM_CHARGE,
    WM_DEEP_SLEEP,
    WM_HEAL,
    WM_LAY_ON_HANDS,
    WM_PENANCE_CHANNEL,
    WM_PENANCE_PILLAR,
    WM_PENANCE_RING,
    WM_PWS,
    WM_RESURRECTION,
    WM_SEARED,
    WM_SMITE,
    WM_VIGIL_FLAME,
    WM_VIGIL_FLAME_PASS,
)

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(3977, **boss_columns(
        'boss_whitemane_rework', 40.783, damage_modifier=2.2,
    ))

_D14 = 'Scarlet Monastery build WP-D14 (Whitemane, with Mograine risen)'
_SCRIPT_BP = ('Scarlet Monastery Whitemane: a percent of reference health the script sets as the base point '
              '(DungeonKit::RefFlat, the tank row on the tank)')
_SCRIPT_HEAL = 'Scarlet Monastery Whitemane: a percent of the target\'s own maximum health (the script\'s base point)'
_SCRIPT_ABSORB = 'Scarlet Monastery Whitemane: 5% of Mograine\'s maximum health (the script\'s base point)'

# --- constants (WhitemaneLogic.h; lib/test_scarlet_monastery_whitemane.py pins each against the header) --------------

DEEP_SLEEP_MS = 3000                # kDeepSleepMs
DEEP_SLEEP_RADIUS = 100.0           # kDeepSleepRadiusYd
RAISE_CAST_MS = 2000                # kRaiseCastMs
HER_SAVE_MAX_MS = 10000             # kHerSaveMs normal (the longest; the script ends it sooner on heroic)
HIS_SAVE_MAX_MS = 6000              # kHisSaveMs normal
BODY_SHIELD_MS = 6000               # kBodyShieldMs
PENANCE_WARN_MS = 3000              # kPenanceWarnMs
HEAL_CAST_MS = 3000                 # kHealCastMs
HEAL_PCT = 6                        # kHealPct normal (heroic 20 through the script's base point)
SHIELD_AURA_MS = 30000              # kShieldAuraMs
SMITE_CAST_MS = 2500                # kSmiteCastMs
CAST_RANGE = 40.0                   # kCastRangeYd
FLAME_AURA_MS = 60000               # kFlameAuraMs
SEARED_MS = 19000                   # kSearedMs

# Stock icons (Spell.dbc SpellIconID of the named spell; read from the stock DBC 2026-11-20).
_ICON_DEEP_SLEEP = 44               # Deep Sleep 9256
_ICON_RESURRECTION = 121            # Scarlet Resurrection 9232
_ICON_LAY_ON_HANDS = 79             # Lay on Hands 9257
_ICON_CHARGE = 457                  # Charge 100
_ICON_SHIELD = 566                  # Power Word: Shield 22187
_ICON_PENANCE = 2818                # Penance 47540
_ICON_HEAL = 104                    # Heal 12039
_ICON_HOLY_SMITE = 237              # Holy Smite 9481
_ICON_HOLY_FIRE = 156               # Holy Fire 14914

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_SRC_CASTER = 22
_TARGET_FLAG_UNIT = 0x2
_DEFENSE_MAGIC = 1
_DISPEL_MAGIC = 1
_MECHANIC_SLEEP = 10
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15
_ATTR1_IS_CHANNELED = 0x00000004
_AURA_INTERRUPT_TAKE_DAMAGE = 0x00000002    # SpellDefines.h AURA_INTERRUPT_FLAG_TAKE_DAMAGE: any damage wakes
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_SCHOOL_MASK_ALL = 127


def _script_hit(spell_id: int, name: str, desc: str, notes: str, *, icon: int, visual: int) -> object:
    """A Holy hit whose amount the script sets as the base point (CastSpellExtraArgs::AddSpellBP0; DieSides 0, so the
    amount is exact): triggered, always hits, cannot crit, ignores LoS and the caster's modifiers, DmgClass magic."""
    return spell(
        id=spell_id, name=name, school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_BP)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                              SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _marker(spell_id: int, name: str, duration_ms: int, visual: int, desc: str, aura_desc: str, notes: str, *,
            icon: int, school: School = School.HOLY) -> object:
    """A marker on a player (the script puts it on, triggered or with AddAura): a DUMMY debuff, not dispellable, lands
    through immunities (Divine Shield and Ice Block cannot shed it), gone on a map change."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


def _channel(spell_id: int, name: str, duration_ms: int, visual: int, desc: str, aura_desc: str, notes: str, *,
             icon: int) -> object:
    """A save channel on the caster itself (the bar shows; cast for real): not interruptible (InterruptFlags,
    ChannelInterruptFlags and PreventionType 0), Physical (rule 5: a Holy kick's lockout never stops it). The script's
    timer is the truth: it ends the channel when the save's window closes (10 / 8 s hers, 6 / 5 s his)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, InterruptFlags=0, ChannelInterruptFlags=0,
                              PreventionType=0, SpellVisualID_1=visual,
                              AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _look_on(spell_id: int, name: str, visual: int, notes: str, *, icon: int) -> object:
    """Visual only, on a target: an instant DUMMY the script casts (triggered) on a player; DO_NOT_DISPLAY | DO_NOT_LOG.
    Copies a stock or minted visual, never the stock spell."""
    return spell(
        id=spell_id, name=name, school=School.HOLY, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- WM1 the rising and the saves ------------------------------------------------------------------------------------

deep_sleep_213150 = spell(
    id=213150, name='Deep Sleep', school=School.NORMAL, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_SLEEP,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=DEEP_SLEEP_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_SLEEP, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=DEEP_SLEEP_RADIUS)],
    spell_icon_id=_ICON_DEEP_SLEEP,
    notes=f'{_D14}, WM1: the rising at P + 15 s. Whitemane casts it (triggered) on herself: every enemy within 100 yd '
          'asleep up to 3 s (a scripted transition; the build spec\'s allowed loss of control), any damage wakes '
          '(AuraInterruptFlags TAKE_DAMAGE). Sleep mechanic, Magic (a dispel takes it, as the stock 9256). Deep Sleep '
          '9256\'s look (SV 87). The script removes it from everyone when the attempt ends.',
    raw_overrides=kit_raw('Puts everyone nearby into a deep sleep.', 'Asleep.', instant=True,
                          SpellVisualID_1=WM_DEEP_SLEEP, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_TAKE_DAMAGE | _AURA_INTERRUPT_CHANGE_MAP),
)

raise_213151 = cast_bar(
    213151, 'Scarlet Resurrection', RAISE_CAST_MS, 'Raises the fallen champion.',
    f'{_D14}, WM1: the 2 s raise Whitemane casts beside Mograine\'s body after Deep Sleep (her line 2, "Arise, my '
    'champion!"); when it lands (OnSpellCast) MograineFight::Rise raises him at the finale\'s health. Not '
    'interruptible (cast_bar). Physical: a kick on Holy Smite or Heal (Holy) never locks it (rule 5). Scarlet '
    'Resurrection 9232\'s look (SV 1443).',
    icon=_ICON_RESURRECTION, visual=WM_RESURRECTION, school=School.NORMAL,
)

resurrection_213152 = _channel(
    213152, 'Scarlet Resurrection', HER_SAVE_MAX_MS, WM_RESURRECTION,
    'Whitemane will not let her champion die.', 'Channeling Scarlet Resurrection.',
    f'{_D14}, WM1a: her save. Mograine fell (held at 1 health, down); she runs to his body, kneels and channels this: '
    'normal 10 s, heroic 8 s (the hard mode\'s phase 2: 6 s), ended by the script. She takes damage as normal; if it '
    'finishes he rises at 50%. Her lethal hit meanwhile: both die.',
    icon=_ICON_RESURRECTION,
)

rise_look_213153 = self_visual(
    213153, 'Scarlet Resurrection', WM_RESURRECTION,
    f'{_D14}, WM1 / WM1a: Mograine rises (the rising, each of her saves): Scarlet Resurrection 9232\'s SV 1443 on him.',
    icon=_ICON_RESURRECTION,
)

lay_on_hands_213154 = _channel(
    213154, 'Lay on Hands', HIS_SAVE_MAX_MS, WM_LAY_ON_HANDS,
    'Mograine will not let his lady die.', 'Channeling Lay on Hands.',
    f'{_D14}, WM1b: his save. Whitemane fell (a held body); Mograine says his line 12, comes to her, kneels and '
    'channels this: normal 6 s, heroic 5 s (the hard mode\'s phase 2: 4 s), ended by the script. He takes damage as '
    'normal; if it finishes she rises at 50%. His lethal hit meanwhile: both die. Lay on Hands 9257\'s SV 132.',
    icon=_ICON_LAY_ON_HANDS,
)

lay_on_hands_look_213155 = self_visual(
    213155, 'Lay on Hands', WM_LAY_ON_HANDS,
    f'{_D14}, WM1b: Whitemane rises at 50% (SV 132 on her).',
    icon=_ICON_LAY_ON_HANDS,
)

# --- WM2 To Her Side -------------------------------------------------------------------------------------------------

lane_hit_213156 = resolve_copy(
    213156, 'To Her Side', School.NORMAL, 'Mograine charges to his lady\'s side.',
    f'{_D14}, WM2: R + 20 s, every 25 s, never during a save: his line 13 ("Milady!"), a 4 yd lane from him to 3 yd '
    'beside her (registry Line, tag 1, owned by Mograine so the tank is his victim), 2 s marker, then the charge: 30% '
    '(heroic 45%) of the reference row (the tank row on the tank) and 1 Weakened. Copy of the resolve spell 205001 '
    '(Physical).',
    icon=_ICON_CHARGE,
)

charge_look_213157 = self_visual(
    213157, 'To Her Side', WM_CHARGE,
    f'{_D14}, WM2: his run as the charge leaves (Charge 100\'s SV 867); the lane is the marker.',
    icon=_ICON_CHARGE,
)

body_shield_213158 = spell(
    id=213158, name='To Her Side', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=BODY_SHIELD_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHIELD,
    notes=f'{_D14}, WM2a (heroic): for 6 s after each charge he shields her with his body: half the damage she takes '
          'goes to him (the script\'s DamageTaken; the aura is the look and the clock). Not dispellable. Divine '
          'Shield\'s state (SV 154, distinct from the Power Word: Shield bubble).',
    raw_overrides=kit_raw('Shields his lady with his body.', 'Half the damage Whitemane takes goes to Mograine.',
                          instant=True, SpellVisualID_1=WM_BODY_SHIELD, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- WM3 Penance -----------------------------------------------------------------------------------------------------

penance_mark_213159 = _marker(
    213159, 'Penance', PENANCE_WARN_MS, WM_PENANCE_RING,
    'Marked for penance.', 'A pillar of holy fire will fall on you.',
    f'{_D14}, WM3: R + 10 s, every 20 s: 2 (heroic 3) random players, never the tank (a 6 yd spread on the tank would '
    'push the melee off Mograine: the shared doc\'s spread exemption), marked 3 s (registry Spread, tag 2). The '
    'shipped yellow rune ring under each (SV 90614; Penance\'s own SV 10980 is hands only).',
    icon=_ICON_PENANCE,
)

penance_hit_213160 = resolve_copy(
    213160, 'Penance', School.HOLY, 'A pillar of holy fire falls.',
    f'{_D14}, WM3: the 6 yd pillar on each marked player hits everyone else inside: 30% (heroic 45%) of the reference '
    'row (the tank row on the tank) and 1 Weakened. Copy of the resolve spell 205002 (Holy).',
    icon=_ICON_PENANCE,
)

penance_strike_213161 = _script_hit(
    213161, 'Penance', 'The pillar of holy fire burns the penitent.',
    f'{_D14}, WM3: the marked player\'s own hit as the pillar falls (the registry Spread skips its carrier): 20% '
    '(heroic 30%) of the reference row, the tank row on the tank (the script\'s base point). No Weakened (the build '
    'spec: Weakened only on the others).',
    icon=_ICON_PENANCE, visual=0,
)

penance_pillar_213162 = _look_on(
    213162, 'Penance', WM_PENANCE_PILLAR,
    f'{_D14}, WM3: the pillar on each marked player as it falls: the minted 6 yd holy light pillar (SV 90564, '
    'Ascension lightsjudgement_impact; the stock Beam of Light SV 12479 is never wired).',
    icon=_ICON_PENANCE,
)

penance_hands_213163 = self_visual(
    213163, 'Penance', WM_PENANCE_CHANNEL,
    f'{_D14}, WM3: her hands as she marks (Penance 47540\'s SV 10980, the ChannelKit holy hands; no beam).',
    icon=_ICON_PENANCE,
)

# --- WM4 Heal, WM4a Power Word: Shield, WM6 Holy Smite ---------------------------------------------------------------

heal_213164 = spell(
    id=213164, name='Heal', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=HEAL_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=CAST_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=HEAL_PCT, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY, potency_excluded=_SCRIPT_HEAL)],
    spell_icon_id=_ICON_HEAL,
    notes=f'{_D14}, WM4: R + 5 s, every 15 s: a 3 s cast on Mograine, 6% (heroic 20%: the script\'s base point, hub '
          'ruling 54) of his maximum health. Cast for real (not triggered: the bar shows), 40 yd, interruptible and '
          'silence-preventable (InterruptFlags 15, PreventionType silence; her immunity set 1972 holds no interrupt or '
          'silence): the descriptor\'s interrupt list, priority 2 normal (a reward), 4 heroic (expected). Heal '
          '12039\'s SV 135.',
    raw_overrides=kit_raw('Heals Mograine.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC, Targets=_TARGET_FLAG_UNIT,
                          SpellVisualID_1=WM_HEAL, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

power_word_shield_213165 = spell(
    id=213165, name='Power Word: Shield', school=School.HOLY, dispel=_DISPEL_MAGIC, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=SHIELD_AURA_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, base_points=0, die_sides=0,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded=_SCRIPT_ABSORB)],
    spell_icon_id=_ICON_SHIELD,
    notes=f'{_D14}, WM4a: R + 8 s, every 20 s: Whitemane shields Mograine (triggered, instant), absorbing 5% of his '
          'maximum health (the script\'s base point), every school, 30 s or until broken. Magic: on the purge list '
          '(priority 2, a reward). Power Word: Shield 22187\'s bubble (SV 784).',
    raw_overrides=kit_raw('Shields Mograine, absorbing damage.', 'Absorbs $s1 damage.', instant=True,
                          InterruptFlags=0, PreventionType=0, SpellVisualID_1=WM_PWS, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

holy_smite_213166 = spell(
    id=213166, name='Holy Smite', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=SMITE_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=CAST_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BP)],
    spell_icon_id=_ICON_HOLY_SMITE,
    notes=f'{_D14}, WM6: her filler on her target, from P + 1 s, every 4 s when nothing else is casting (gap 20): '
          '2.5 s, 10% (heroic 15%) of the reference row, the tank row on the tank (the script\'s base point). '
          'Interruptible and silence-preventable (InterruptFlags 15, PreventionType silence): on the interrupt list '
          '(priority 1, a reward). Needs line of sight (no IGNORE_LINE_OF_SIGHT: she closes in when a pillar hides her '
          'target). Holy Smite 9481\'s SV 128.',
    raw_overrides=kit_raw('Smites an enemy with holy fire.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=WM_SMITE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- WM5 the Vigil Flame (heroic) ------------------------------------------------------------------------------------

vigil_flame_213167 = _marker(
    213167, 'Vigil Flame', FLAME_AURA_MS, WM_VIGIL_FLAME,
    'Carries the Vigil Flame.', 'Every few seconds the flame flares: share it with the nearest ally, never one who is '
    'Seared.',
    f'{_D14}, WM5 (heroic): R + 20 s a random non-tank carries the vigil candle; the script moves it at each flare (to '
    'the partner, else a fresh unseared carrier, the tank last). The registry Soak on the carrier (count 1, 6 yd, the '
    'unseared others eligible, Ordering::roleLast = the tank, tag 3) and a no-damage circle that keeps the Seared off '
    'it (tag 4) mirror G2\'s vigil-flame drill row. The shipped held torch (SV 90603).',
    icon=_ICON_HOLY_FIRE,
)

vigil_flare_213168 = _script_hit(
    213168, 'Vigil Flame', 'The Vigil Flame flares.',
    f'{_D14}, WM5 (heroic): every 10 s (the hard mode\'s phase 1: 8 s) the flare: 110% of the reference row split '
    'between the carrier and the nearest other player within 6 yd, 55% each; unshared the carrier takes 110%; a Seared '
    'player takes double their share (110%): lethal by hub ruling 50. The tank row on the tank (the script\'s base '
    'point). No Weakened (a soak).',
    icon=_ICON_HOLY_FIRE, visual=0,
)

seared_213169 = _marker(
    213169, 'Seared', SEARED_MS, WM_SEARED,
    'Seared by the Vigil Flame.', 'Seared: the Vigil Flame\'s next flares deal double to you. Keep away from its '
    'carrier.',
    f'{_D14}, WM5a (heroic): the old carrier at each pass, 19 s (the hard mode\'s phase 1: 15 s, the script sets the '
    'duration), so it fades just before the flare after next and the flame runs a loop. Doubles the bearer\'s share of '
    'a flare (the script reads the aura); the Soak\'s eligibility key (no stacks). Burning Brand\'s state (SV 1946).',
    icon=_ICON_HOLY_FIRE, school=School.FIRE,
)

flame_pass_213170 = _look_on(
    213170, 'Vigil Flame', WM_VIGIL_FLAME_PASS,
    f'{_D14}, WM5 (heroic): the pass on the new carrier (Holy Fire 14914\'s SV 3400), with her raid emote line 7 ("The '
    'Vigil Flame passes to $n!", hub ruling 54).',
    icon=_ICON_HOLY_FIRE,
)
