"""
Gnomeregan build WP-D4: the Mobile Alert System (301110) and its kit (.agents/plans/gnomeregan-build/
gnomeregan-build.HANDOFF.md s3.5 row D4, s3.6, s3.8, s7 #21 A, #22 A, #36-#38 A; build spec
docs/dungeons/gnomeregan-rework.md "The Mobile Alert System", MA1-MA10, rulings 25-30, 66, 67). WP-D4 owns this file
(its spells: kSpellsAlertSystem 214420-214459 of modules/mod-dungeon-bosses src/Gnomeregan/GnomereganRework.h only;
MobileAlertSystemLogic.h names the same ids and holds every number; the texts and the Defender's gun are the core SQL
rev rev_mobile_alert_system_gnomeregan.sql). Heroic health and the adds' heroic templates are WP-H's
(source/world/dungeons/gnomeregan.py: 301111 and 301112 in `extra=`).

- 301110 the Mobile Alert System: WP-S0's row (a copy of the stock alarm bot 7849, SELECT 2026-11-26) at level 28
  elite, faction 63, bound to boss_mobile_alert_system_rework, SmartAI off, immunity 1972 (stun, root: he is held by
  the script), INSTANCE_BIND with both assist flags, detection range 12, DamageModifier 1.7 (he never melees), the
  normal health of s3.6 (56,000 = 65.65 on 853, the spec's 28,000 x2.0); display 6888 at scale 3 (ruling 67). No
  Stealth Detection aura (s7 #38 e). Loot: lootid 301110, its list is source/items/gnomeregan_loot.py (WP-L-1).
- 301111 Security Assistant: npc_gnomer_security_assistant, a copy of the Leprous Assistant 7603 (level 28, normal
  rank, melee; heroic Net), displays 6967 / 6968, 450 health (HealthModifier 0.5275 on 853; unscaled, LESSONS 1 #5).
- 301112 Security Defender: npc_gnomer_security_defender, a copy of the Leprous Defender 6223 (level 28 elite, ranged:
  the stock Shoot 6660 and Multi-Shot 14443), displays 6982 / 6981, 1,200 health (1.40679 on 853), its gun is the
  stock 6223 equipment row (the rev).
- 301113 the light stalker (KT-G TurningLights: one per light, summoned by the boss and kept on his spot): KIT_HELPER
  (not selectable, not attackable, no XP), NullCreatureAI, the invisible stalker 11686 (stock creature_model_info
  row). The lit cone is the BM marker (s3.10); the optional white cone display (CDI 90856) is off
  (MobileAlertSystemLogic.h kUseConeDisplay).

Spells (every registry hit is a dungeon copy of the mod-boss-mechanics resolve spell; nothing is kickable and nothing
is dispellable: the kick and dispel table's row for the Alert System):

  214420  Spotted           MA3: resolve copy, Arcane, 20% / 50% of the reference row (the tank row on the tank),
                            Weakened on normal (the registry's)
  214421  Alarm             MA8: resolve copy, Nature, 5% / 8% to everyone in his fight every 5 s
  214422  Alarm             MA8: the pulse's ring and loop sound on him (SV_ALARM_PULSE, look only)
  214423  Searchlight       MA1: the lock-on light pillar on the target, 5 s (SV 7402)
  214424  Spotted           MA3: the red beam from him to the Spotted player (SV 7851, look only)
  214425  Self-Destruct     MA7 heroic: the 120 s clock on him (SV 1463), duration set by the script
  214426  Self-Destruct     MA7 heroic: the blast at zero (SV 1463, look only)
  214427  Net               MA9 heroic: the Assistant's 3 s root (stock Net 12024 at 3 s), Physical, dispel none
  214428  Netting           MA9 heroic: on the Assistant while its net holds (the bots' first kill)
  214429-214459 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    FACTION_GNOMEREGAN_MECHANICAL,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TYPE_MECHANICAL,
    boss_columns,
    heroic_entry,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_ALERT,
    DISPLAY_ASSISTANT,
    DISPLAY_ASSISTANT_2,
    DISPLAY_DEFENDER,
    DISPLAY_DEFENDER_2,
    DISPLAY_INVISIBLE_STALKER,
    MA_ALARM_PULSE,
    MA_LOCK_PILLAR,
    MA_NET,
    MA_SELF_DESTRUCT,
    MA_SPOTTED,
)

_D4 = 'Gnomeregan build WP-D4 (the Mobile Alert System)'

# --- constants (MobileAlertSystemLogic.h; lib/test_gnomeregan_alert.py pins each against the header) ------------------

ALERT_SCALE = 3.0                   # ruling 67 (_visuals.ALERT_SCALE)
LOCK_ON_MS = 5000                   # Tune::kSearchDimMs + kSearchSweepMs
SELF_DESTRUCT_MS = 120000           # Tune::kSelfDestructMs
NET_MS = 3000                       # Tune::kNetMs
NET_RANGE = 20.0                    # Tune::kNetRangeYd (the stock Net's range)
ASSISTANT_HEALTH_MODIFIER = 0.5275  # Health::kSecurityAssistant 450 on 853
DEFENDER_HEALTH_MODIFIER = 1.40679  # Health::kSecurityDefender 1,200 on 853

_MECHANIC_ROOT = 7
_DEFENSE_RANGED = 3                 # the stock Net's DefenseType
_PREVENTION_PACIFY = 2              # the stock Net's PreventionType
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock DBC 2026-11-26)
_ICON_NET = 69                      # Net 12024
_ICON_SELF_DESTRUCT = 37            # Self Destruct 9874
_ICON_SPOTLIGHT = 51                # Spotlight 25824
_ICON_RED_BEAM = 816                # Red Beam 31513
_ICON_MOBILE_ALARM = 1              # Mobile Alarm 12900

# --- the creatures ---------------------------------------------------------------------------------------------------

boss_301110 = creature_template(
    301110, 'Mobile Alert System',
    minlevel=28, maxlevel=28, exp=0, faction=FACTION_GNOMEREGAN_MECHANICAL, npcflag=0,
    speed_walk=2.0, speed_run=0.71429, rank=1, dmgschool=0, BaseAttackTime=2000,
    RangeAttackTime=2000, BaseVariance=1, RangeVariance=1, unit_class=1, unit_flags=0, unit_flags2=2048,
    type=TYPE_MECHANICAL, type_flags=0, lootid=301110, mingold=0, maxgold=0, MovementType=0, HoverHeight=1,
    ManaModifier=1, ArmorModifier=1, ExperienceModifier=1, RegenHealth=1, movementId=94,
    **boss_columns('boss_mobile_alert_system_rework', 65.65, damage_modifier=1.7,
                   difficulty_entry_1=heroic_entry(301110)),
)
creature_model(301110, display_id=DISPLAY_ALERT, scale=ALERT_SCALE, idx=0)

# The two adds walk in from the door corridor (the boss summons them). Heroic templates: WP-H (`extra=`); each row
# names its heroic entry (_common.heroic_entry: the lock's line, else H's predicted id).
security_assistant_301111 = creature_template(301111, 'Security Assistant', **{
    **KIT_CREATURE, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1, 'unit_flags': 32768,
    'type': 7, 'speed_run': 1.14286, 'detection_range': 18.0, 'HealthModifier': ASSISTANT_HEALTH_MODIFIER,
    'DamageModifier': 1.0, 'lootid': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': 0x40,
    'difficulty_entry_1': heroic_entry(301111), 'ScriptName': 'npc_gnomer_security_assistant',
})
creature_model(301111, display_id=DISPLAY_ASSISTANT, idx=0)
creature_model(301111, display_id=DISPLAY_ASSISTANT_2, idx=1)

security_defender_301112 = creature_template(301112, 'Security Defender', **{
    **KIT_CREATURE, 'minlevel': 28, 'maxlevel': 28, 'rank': 1, 'unit_class': 1, 'unit_flags': 32832,
    'type': 7, 'speed_run': 1.14286, 'detection_range': 20.0, 'HealthModifier': DEFENDER_HEALTH_MODIFIER,
    'DamageModifier': 1.7, 'ExperienceModifier': 1.25, 'lootid': 0, 'mingold': 0, 'maxgold': 0,
    'flags_extra': 0x40, 'difficulty_entry_1': heroic_entry(301112), 'ScriptName': 'npc_gnomer_security_defender',
})
creature_model(301112, display_id=DISPLAY_DEFENDER, idx=0)
creature_model(301112, display_id=DISPLAY_DEFENDER_2, idx=1)

light_stalker_301113 = creature_template(301113, 'Searchlight', **{
    **KIT_HELPER, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1, 'type': TYPE_MECHANICAL,
    'AIName': 'NullCreatureAI', 'ScriptName': '',
})
creature_model(301113, display_id=DISPLAY_INVISIBLE_STALKER, idx=0)

# --- MA3 Spotted, MA8 Alarm: the registry's hits ---------------------------------------------------------------------

spotted_214420 = resolve_copy(
    214420, 'Spotted', School.ARCANE, 'The searchlight has found you. Intruder alert!',
    f'{_D4}, MA3: a player the light (or the cameras past 30 yd, s7 #21 A) caught, at most once per 3 s per player: '
    '20% (heroic 50%) of the reference row, the tank row on the tank, Weakened on normal (registry tags 50 / 52, the '
    'cameras 54). A Response Team follows 3 s later. Copy of the resolve spell 205001 (Arcane).',
    icon=_ICON_RED_BEAM,
)

alarm_214421 = resolve_copy(
    214421, 'Alarm', School.NATURE, 'The siren rattles everyone in the hall.',
    f'{_D4}, MA8: every 5 s, everyone in his fight, the tank included: 5% (heroic 8%) of the reference row, the tank '
    'row on the tank; no Weakened. Copy of the resolve spell 205001 (Nature).',
    icon=_ICON_MOBILE_ALARM,
)

alarm_look_214422 = self_visual(
    214422, 'Alarm', MA_ALARM_PULSE,
    f'{_D4}, MA8: the pulse\'s ring and the alert bot\'s loop sound on him (the minted SV_ALARM_PULSE: a ThunderClap '
    'ring and sound 5763; never the stock Mobile Alarm 12900\'s SV 395, a crafting hammer). Cast on himself '
    '(triggered) with every pulse. Look only.',
    icon=_ICON_MOBILE_ALARM,
)

# --- MA1 the lock-on, MA3 the beam -----------------------------------------------------------------------------------

lock_on_214423 = spell(
    id=214423, name='Searchlight', school=School.ARCANE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=LOCK_ON_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SPOTLIGHT,
    notes=f'{_D4}, MA1: on the lock-on target for the 2 s dim and the 3 s sweep (cast by him, triggered): the MoonBeam '
          'pillar SV 7402 (the VR pick; Spotlight 25824 / 25823 are a point gesture and never wired). Shown on the '
          'aura bar as a warning; no effect, not dispellable; gone on his reset, evade or death.',
    raw_overrides=kit_raw('The searchlight locks on to you.', 'Tracked by the searchlight. Step out of its sweep.',
                          instant=True, SpellVisualID_1=MA_LOCK_PILLAR, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

spotted_beam_214424 = spell(
    id=214424, name='Spotted', school=School.ARCANE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_RED_BEAM,
    notes=f'{_D4}, MA3: the red beam from him to a Spotted player (Red Beam 31513\'s SV 7851, Beam_RedDrops), cast by '
          'him (triggered) as the hit lands. Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=MA_SPOTTED, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- MA7 Self-destruct (heroic) --------------------------------------------------------------------------------------

self_destruct_214425 = spell(
    id=214425, name='Self-Destruct', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=SELF_DESTRUCT_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SELF_DESTRUCT,
    notes=f'{_D4}, MA7 heroic: the 120 s clock on him from the pull (added by the script; its duration follows the '
          'script\'s clock every second: 5 s off per Spotted). At zero he blows (214426) and everyone in combat with '
          'him or on the hall floor dies: the enrage. Self Destruct 9874\'s SV 1463 rides the aura (s3.5 row D4). '
          'No effect; not dispellable or stealable (lands through his immunities).',
    raw_overrides=kit_raw('Self-destruct sequence activated.', 'Self-destruct in progress.', instant=True,
                          SpellVisualID_1=MA_SELF_DESTRUCT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

self_destruct_blast_214426 = self_visual(
    214426, 'Self-Destruct', MA_SELF_DESTRUCT,
    f'{_D4}, MA7 heroic: the blast when the clock runs out (SV 1463: Bomb_ExplosionA and a FireNova ring), cast on '
    'himself (triggered) just before the kills. Look only.',
    icon=_ICON_SELF_DESTRUCT,
)

# --- MA9 Net (heroic Assistants) -------------------------------------------------------------------------------------

net_214427 = spell(
    id=214427, name='Net', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_ROOT, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=NET_RANGE,
    duration_ms=NET_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_NET,
    notes=f'{_D4}, MA9 heroic: the Security Assistant\'s Net (first at 6 s, then every 12 s, a random player in 20 yd; '
          'the stock Net 12024 at 3 s: Physical, root mechanic, dispel none, the kick and dispel table). The script '
          'removes it at once when its Assistant dies or is stunned (s7 #38 f); a netted player in the light is '
          'Spotted. Instant (no bar to kick). Stock SV 683.',
    raw_overrides=kit_raw('Nets the target, rooting it for $d.', 'Rooted.', instant=True, SpellVisualID_1=MA_NET,
                          DefenseType=_DEFENSE_RANGED, PreventionType=_PREVENTION_PACIFY,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

netting_214428 = spell(
    id=214428, name='Netting', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=NET_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_NET,
    notes=f'{_D4}, MA9 heroic: on an Assistant (cast on itself, triggered) while its net holds: the bots\' kill order '
          'reads it (a netting Assistant first, Condition::HasAura). Removed with its nets. Hidden, no effect.',
    raw_overrides=kit_raw(instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
