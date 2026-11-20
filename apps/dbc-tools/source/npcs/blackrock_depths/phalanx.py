"""
Blackrock Depths build WP-D19: Phalanx (9502; Rowdy Patron 300841 (heroic))
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 / s3.5 row D19, s3.6, s3.8, s3.10; build
spec docs/dungeons/blackrock-depths-4-imperial-seat.md "Phalanx" PH1-PH6, rulings 63-66). WP-D19 owns this file (its
spells: kSpellsPhalanx 211460-211489 of modules/mod-dungeon-bosses src/BlackrockDepths/BlackrockDepthsRework.h only;
PhalanxLogic.h names the same ids). The engine side is src/BlackrockDepths/npc_phalanx_rework.cpp; his four new texts
and the gossip option are data/sql/updates/pending_db_world/rev_phalanx_blackrock_depths.sql.

Wave 2: the wave switch (_common.py BIND_WAVE_2) holds back what rebinds a STOCK unit (Phalanx's own columns, below)
and the Rowdy Patron's ScriptName (an unbound name logs "not assigned" at boot). The new entry, its model and the spells
are declared either way: nothing spawns the patron until the C++ binds.

- 9502 Phalanx: npc_phalanx_rework (stock npc_phalanx retired; SmartAI off: he has none in the live DB), the build
  spec's normal health lowered to 145k (was 160k; 2026-11-19 bot runs: HealthModifier 55.47 on the level 55 warrior
  class base 2,614), the kit's stun immunity set 1972 (s7 #10: stock -248 lets stuns land, ruling 64 asks for -251's
  stun immunity), INSTANCE_BIND, DamageModifier
  3.5 (the stock base value; the live 7 is a leftover). His template keeps faction 35, npcflag 1 and gossip_menu_id
  2283 (the dormant state and the new gossip start need them). Heroic 230k is WP-H's override
  (source/world/dungeons/blackrock_depths.py). Display 8177 (Toxitron wears it too) is the stock one and stays.
- 300841 Rowdy Patron: the boss-kit add of PH6 (heroic only: two per smashed table), its own entry (the bar's stock
  patrons are the room's crowd), level 55, 8,000 health (heroic 8k: `difficulty_entry_1` 310415, WP-H's lock line),
  melee only (C++ npc_brd_rowdy_patron: its hits count for Phalanx's Throw Out ledger), the Hammered Patron look (CDI
  8681 at 1.2), Dark Iron faction, no loot, no XP. DamageModifier 2.0 is this WP's default (gap 36; designer question):
  about 4% of the level 55 tank row a swing; the heroic melee is WP-H's.

Spells. The registry hits (the landing circle, the thrown player, Last Call, the table smash) deal their damage
through dungeon copies of the mod-boss-mechanics resolve spell (Physical). Mighty Blow, Thunderclap and Fireball Volley
are the stock spells kept and rescaled (rule 15: copies in the slice), a percent of the reference row on the kit's
generic script (spell_dungeon_refflat_damage: the hundredths in the effect, the heroic ones in EffectMiscValueB). The
rest are looks or the hold:

  211460  Mighty Blow          PH1 stock 14099: 25% / 30% (the tank row on the tank) and the stock knockback
  211461  Thunderclap          PH2 stock 15588: 10 yd, 10% / 12%, -40% movement, -34% attack speed, 10 s, Magic
  211462  Fireball Volley      PH3 stock 15285: 20 yd, 10% / 15% (from 50% health)
  211463  Throw Out            PH4 the 1 s hold (a 1.5 s stun the throw removes; the Grabbed trail SV 12139)
  211464  Throw Out            PH4 look: his throw (Throw 55425's SV 12140), cast on the held player as they fly
  211465  Throw Out            PH4 the landing circle's hit: 6 yd, 30% / 45% + Weakened (everyone but the thrown player)
  211466  Throw Out            PH4 the thrown player's own hit: 15% / 25%, no Weakened
  211467  Ground Slam          look: the crack and shake at the landing and under him at Last Call's pulse (SV 8083)
  211468  Last Call            PH5 the 3 s bar (Ring Bessy's Bell 35209's SV 215: the bell)
  211469  Last Call            PH5 the pulse's hit: 10 / 12 yd, 25% / 40% + Weakened (the knockback is the script's)
  211470  Outrage              PH6 +15% damage done a stack, 5 at most, for the fight (Bellowing Roar's SV 4939)
  211471  Property Damage      PH6 the smasher's hit: 25% + Weakened
  211472  Property Damage      look: the wood chips at the broken table (Deadmines SV 90344 on a stalker; NEVER Smash
                               54458's SV 3948, blood and a stun swirl)
  211473-211489 spare.

Retired: the stock Mighty Blow 14099, Thunderclap 15588 and Fireball Volley 15285 are not cast by him any more (rule 15:
copies). Visual ids are V-1's (._visuals PH_*); every look is unconfirmed until seen in game.
"""

import math

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
    ATTR3_NOT_A_PROC,
    TARGET_UNIT_TARGET_ENEMY,
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
    TARGET_UNIT_CASTER,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_ROWDY_PATRON,
    PH_FIREBALL_VOLLEY,
    PH_LAST_CALL,
    PH_OUTRAGE,
    PH_TABLE_SPLINTERS,
    PH_THROW_OUT_FLIGHT,
    PH_THROW_OUT_GRAB,
    PH_THROW_OUT_LANDING,
    PH_THUNDERCLAP,
)

_D19 = 'Blackrock Depths build WP-D19 (Phalanx)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

# --- the boss (held back until wave 2 binds the section: _common.py BIND_WAVE_2) --------------------------------------

# 55.47 x the level 55 warrior base 2,614 = 145,000 (was 160,000; lowered with Volley 12 -> 10% on 2026-11-19: the
# brd-s4 bot runs lost a fight about twice the intended length).
PHALANX_COLUMNS = boss_columns('npc_phalanx_rework', 55.47, damage_modifier=3.5)
if BIND_WAVE_2:
    creature_template_columns(9502, **PHALANX_COLUMNS)

# --- constants (PhalanxLogic.h; lib/test_blackrock_depths_phalanx.py pins each against the header) --------------------

MIGHTY_BLOW = (2500, 3000)          # kMightyBlowPct 25 / 30 (hundredths)
THUNDERCLAP = (1000, 1200)          # kThunderclapPct 10 / 12
VOLLEY = (1000, 1500)               # kVolleyPct 10 / 15
THUNDERCLAP_RADIUS = 10.0           # kThunderclapRadiusYd
THUNDERCLAP_MS = 10000              # kThunderclapMs
THUNDERCLAP_SLOW = -40              # kThunderclapSlowPct
THUNDERCLAP_ATTACK_SPEED = -34      # kThunderclapAttackSpeedPct
VOLLEY_RADIUS = 20.0                # kVolleyRadiusYd
GRAB_AURA_MS = 1500                 # kGrabAuraMs (the throw removes it after kGrabMs)
LAST_CALL_CAST_MS = 3000            # kLastCallCastMs
OUTRAGE_PCT = 15                    # kOutragePctPerStack
OUTRAGE_CAP = 5                     # kOutrageCap

PATRON = 300841
PATRON_HEROIC = 310415              # WP-H's lock line (STAGE-H-REPORT s3)
PATRON_LEVEL = 55                   # the section's one number (ruling 5); heroic is WP-H's
PATRON_HEALTH = 8_000               # kPatronHealth (heroic 8k is WP-H's `extra=` row)
PATRON_DAMAGE_MODIFIER = 2.0
PATRON_SCALE = 1.2                  # the Hammered Patron look at 1.2 (V-1: DISPLAY_ROWDY_PATRON)
WARRIOR_55_BASE = 2614              # creature_classlevelstats basehp0, class 1 level 55 (live 2026-11-17)
PATRON_SCRIPT = 'npc_brd_rowdy_patron'

_FLAGS_EXTRA_NO_XP = 0x40
_MECHANIC_SNARE = 11
_DISPEL_MAGIC = 1
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_PREVENTION_SILENCE = 1
_PREVENTION_PACIFY = 2
_SCHOOL_MASK_ALL = 127
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

# Icons (the client Spell.dbc, the stock spells').
_ICON_MIGHTY_BLOW = 314             # Mighty Blow 14099
_ICON_THUNDERCLAP = 199             # Thunderclap 15588
_ICON_FIREBALL_VOLLEY = 185         # Fireball Volley 15285
_ICON_GENERIC = 1

# The scripted hits: no redirection or reflection, no crit, always hit, ignore his modifiers (a percent of the
# reference row; Outrage raises his melee, the script scales his two new mechanics).
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
    AttributesEx2=ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
    AttributesEx4=ATTR4_NO_CAST_LOG,
)


def _health_modifier(target: int, base: int) -> float:
    """The HealthModifier that makes ceil(base x modifier) = target: the exact quotient cut to six digits from below
    (a rounded-up one would ceil to target + 1)."""
    return math.floor(target / base * 1_000_000) / 1_000_000


def _pbaoe(radius: float, **more) -> dict:
    """An effect on every enemy within `radius` of the caster (TARGET_SRC_CASTER + TARGET_UNIT_SRC_AREA_ENEMY)."""
    return dict(implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
                radius_yards=radius, **more)


# --- 300841 Rowdy Patron (heroic, PH6) --------------------------------------------------------------------------------
# The entry is written as a number: source/world/dungeons/blackrock_depths.py finds the declared kit adds by the
# pattern `creature_template(<entry>, ...)` (WP-H) and gives them their heroic health.

rowdy_patron_300841 = creature_template(300841, 'Rowdy Patron', **{
    **KIT_CREATURE, 'minlevel': PATRON_LEVEL, 'maxlevel': PATRON_LEVEL, 'rank': 1, 'unit_class': 1, 'unit_flags': 0,
    'HealthModifier': _health_modifier(PATRON_HEALTH, WARRIOR_55_BASE), 'DamageModifier': PATRON_DAMAGE_MODIFIER,
    'BaseAttackTime': 2000, 'speed_run': 1.14286, 'detection_range': 20.0, 'CreatureImmunitiesId': 0,
    'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'ScriptName': PATRON_SCRIPT if BIND_WAVE_2 else '', 'difficulty_entry_1': PATRON_HEROIC,
})
creature_model(PATRON, display_id=DISPLAY_ROWDY_PATRON, scale=PATRON_SCALE)

# --- PH1 Mighty Blow, PH2 Thunderclap, PH3 Fireball Volley (the stock kit, rescaled: rule 15 copies) ------------------

mighty_blow_211460 = spell(
    id=211460, name='Mighty Blow', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=MIGHTY_BLOW[0] - 1, die_sides=1,
               implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
        # the stock second effect, unchanged: a knockback, 75-125 up (EffectBasePoints / 10), 10 yd/s out (MiscValue)
        Effect(type=EffectType.KNOCK_BACK, base_points=74, die_sides=51, misc_value=100,
               implicit_target_a=TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_MIGHTY_BLOW,
    notes=f'{_D19}, PH1: the stock Mighty Blow 14099 (+25 weapon, 75-125 damage, a knockback) kept and rescaled (rule '
          '15: a copy in the slice, never the shared id). Phalanx casts it (triggered) on his victim in melee reach, '
          '15 s after the pull and every 10 s (the stock timers): Physical, 25% (heroic 30%: EffectMiscValueB) of the '
          'reference row through spell_dungeon_refflat_damage (RefFlatOn: the tank\'s row on the tank), and the stock '
          'knockback. On heroic a tank it knocks to within about 2 yd of a table smashes it (PH6, the script). The '
          'spec leaves the number to "stock rescaled" (gap 36): this WP\'s default. Always hits, cannot crit, ignores '
          'his modifiers. No look of its own: the swing is his melee animation.',
    raw_overrides=kit_raw('Inflicts damage and knocks the target back.', instant=True, DefenseType=_DEFENSE_MELEE,
                          PreventionType=_PREVENTION_PACIFY, EffectMiscValueB_1=MIGHTY_BLOW[1], **_HIT_ATTRS),
)
scripted_by(mighty_blow_211460, 'spell_dungeon_refflat_damage')

thunderclap_211461 = spell(
    id=211461, name='Thunderclap', school=School.NATURE, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_SNARE,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=THUNDERCLAP_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=THUNDERCLAP[0] - 1, die_sides=1,
               potency_excluded=_SCRIPT_REFFLAT, **_pbaoe(THUNDERCLAP_RADIUS)),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=THUNDERCLAP_SLOW - 1,
               die_sides=1, mechanic=_MECHANIC_SNARE, **_pbaoe(THUNDERCLAP_RADIUS)),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE,
               base_points=THUNDERCLAP_ATTACK_SPEED - 1, die_sides=1, **_pbaoe(THUNDERCLAP_RADIUS)),
    ],
    spell_icon_id=_ICON_THUNDERCLAP,
    notes=f'{_D19}, PH2: the stock Thunderclap 15588 (10 yd round him, Nature damage, -40% movement and slower attacks '
          'for 10 s, Magic) kept and rescaled (rule 15: a copy). He casts it on himself (triggered) 12 s after the '
          'pull and every 10 s (the stock timers): everyone within 10 yd, the tank too, takes 10% (heroic 12%: '
          'EffectMiscValueB) of the reference row through spell_dungeon_refflat_damage, -40% movement (the stock '
          'per-level growth dropped: a flat 40%, as the spec reads) and -34% attack speed for 10 s. Magic: the boss '
          'data\'s dispel list (a reward on normal, expected on heroic: the slow makes Last Call harder to clear). '
          'Gap 36 default for the hit. Always hits, cannot crit, ignores his modifiers. The stock look (SV 145).',
    raw_overrides=kit_raw('Inflicts Nature damage to nearby enemies, increasing the time between their attacks and '
                          'slowing their movement for $d.',
                          'Time between attacks increased by 34%. Movement speed reduced by 40%.', instant=True,
                          DefenseType=_DEFENSE_MAGIC, PreventionType=_PREVENTION_SILENCE,
                          EffectMiscValueB_1=THUNDERCLAP[1], SpellVisualID_1=PH_THUNDERCLAP,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, **_HIT_ATTRS),
)
scripted_by(thunderclap_211461, 'spell_dungeon_refflat_damage')

fireball_volley_211462 = spell(
    id=211462, name='Fireball Volley', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=VOLLEY[0] - 1, die_sides=1,
                    potency_excluded=_SCRIPT_REFFLAT, **_pbaoe(VOLLEY_RADIUS))],
    spell_icon_id=_ICON_FIREBALL_VOLLEY,
    notes=f'{_D19}, PH3: the stock Fireball Volley 15285 (Fire on everyone within 20 yd) kept and rescaled (rule 15: '
          'a copy). From 50% health (stock HealthBelowPct(51)) he casts it on himself (triggered) at once and every '
          '10 s: 10% (heroic 15%: EffectMiscValueB) of the reference row on everyone within 20 yd, through '
          'spell_dungeon_refflat_damage: healer load in the second half (gap 36 default). The stock missiles (Speed '
          '24) and look (SV 2437). Always hits, cannot crit, ignores his modifiers.',
    raw_overrides=kit_raw('Inflicts Fire damage to nearby enemies.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          PreventionType=_PREVENTION_SILENCE, Speed=24.0, EffectMiscValueB_1=VOLLEY[1],
                          SpellVisualID_1=PH_FIREBALL_VOLLEY, **_HIT_ATTRS),
)
scripted_by(fireball_volley_211462, 'spell_dungeon_refflat_damage')

# --- PH4 Throw Out ----------------------------------------------------------------------------------------------------

grab_211463 = spell(
    id=211463, name='Throw Out', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=GRAB_AURA_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_D19}, PH4: the hold. Phalanx casts it (triggered) on the player he grabs (the top damage dealer of the '
          'last 10 s): a stun with no mechanic (no trinket or Freedom breaks it, NO_IMMUNITIES: a bubble does not stop '
          'the grab) for at most 1.5 s; the script removes it after 1 s, as it throws them (DungeonKit::JumpTo to the '
          'landing). The Grabbed 55424 trail on the held player (SV 12139). Not dispellable; dropped on a map change. '
          'Grab and flight total 2 s: no loss of control over 2 s.',
    raw_overrides=kit_raw('Grabbed by the collar.', 'Held by the collar.', instant=True,
                          SpellVisualID_1=PH_THROW_OUT_GRAB, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

throw_look_211464 = spell(
    id=211464, name='Throw Out', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_D19}, PH4: his throw\'s look. Phalanx casts it (triggered, through DungeonKit::JumpTo\'s look spell) on '
          'the held player as the flight starts: Throw 55425\'s SV 12140 (an animation on him; the flight itself is '
          'the server jump to the landing). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=PH_THROW_OUT_FLIGHT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

throw_out_211465 = resolve_copy(
    211465, 'Throw Out', School.NORMAL, 'A thrown body crashes down.',
    f'{_D19}, PH4: the landing circle\'s hit: 6 yd where the thrown player lands, drawn as the grab starts and landing '
    '2 s later with them: 30% (heroic 45%) of the row and 1 Weakened (registry tag 1) on everyone else inside (the '
    'thrown player is not eligible: their own hit is 211466). Outrage scales it (the script). Copy of the resolve '
    'spell 205000-205007 with the Physical school.',
)

thrown_211466 = resolve_copy(
    211466, 'Throw Out', School.NORMAL, 'Thrown across the bar.',
    f'{_D19}, PH4: the thrown player\'s own hit as they land: 15% (heroic 25%) of the row, no Weakened (being thrown '
    'is not a failure; registry tag 3, DungeonKit::RegistryHit). Outrage scales it (the script). Copy of the resolve '
    'spell with the Physical school.',
)

slam_look_211467 = spell(
    id=211467, name='Ground Slam', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_D19}, PH4 / PH5: the crack and shake (Ground Slam 33525\'s SV 8083). Phalanx casts it (triggered) at the '
          'throw\'s landing as the thrown player lands, and at his own feet as Last Call\'s pulse goes off. Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=PH_THROW_OUT_LANDING, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- PH5 Last Call ----------------------------------------------------------------------------------------------------

last_call_cast_211468 = cast_bar(
    211468, 'Last Call', LAST_CALL_CAST_MS, 'Rings the bell. Everybody out.',
    f'{_D19}, PH5: the 3 s bar (yell line 2): he stands still and rings the bell (Ring Bessy\'s Bell 35209\'s SV 215); '
    'the registry\'s 10 yd (heroic 12 yd) circle round him (211469) owns the hit. Not interruptible (the kit\'s cast '
    'bar): he has no kickable cast, so no school lockout can stop a must-play bar.',
    visual=PH_LAST_CALL,
)

last_call_211469 = resolve_copy(
    211469, 'Last Call', School.NORMAL, 'Everybody out!',
    f'{_D19}, PH5: the pulse as the bar ends: everyone within 10 yd (heroic 12 yd) of him, the tank included, takes '
    '25% (heroic 40%) of the row and 1 Weakened (registry tag 2); the script knocks each one back from where he stood '
    '(15 yd/s out, 8 up: about 12 yd; this WP\'s default) and, on heroic, watches them for a table (PH6). Outrage '
    'scales it (the script). Copy of the resolve spell with the Physical school.',
)

# --- PH6 Property Damage (heroic) -------------------------------------------------------------------------------------

outrage_211470 = spell(
    id=211470, name='Outrage', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=OUTRAGE_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Outrage: a flat +15% damage done a stack, not a damage value')],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_D19}, PH6 (heroic): every table a player smashes gives Phalanx a stack (he casts it on himself, '
          'triggered: the roar plays each time): +15% damage done a stack, 5 at most (CumulativeAura), for the fight '
          '(removed at its end). The aura raises his melee; the script multiplies the two new mechanics\' percents '
          '(Throw Out, Last Call) by the same 1 + 0.15 x stacks (the copies of his stock spells ignore caster '
          'modifiers, rule 2). Bellowing Roar 18431\'s SV 4939 (a roar and a shake). Not dispellable.',
    raw_overrides=kit_raw('Damage done increased by 15%, stacking.', 'Damage done increased by $s1%.', instant=True,
                          CumulativeAura=OUTRAGE_CAP, SpellVisualID_1=PH_OUTRAGE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

table_smash_211471 = resolve_copy(
    211471, 'Property Damage', School.NORMAL, 'Smashed through a table.',
    f'{_D19}, PH6 (heroic): a player knocked (Last Call or Mighty Blow) to within about 2 yd of a table smashes it: '
    '25% of the row and 1 Weakened (registry tag 4, DungeonKit::RegistryHit). Each of the seven tables breaks once. '
    'Copy of the resolve spell with the Physical school.',
)

table_splinters_211472 = self_visual(
    211472, 'Property Damage', PH_TABLE_SPLINTERS,
    f'{_D19}, PH6 (heroic): the wood chips and steam of a smashed table (the Deadmines Splinter Spray impact, shipped '
    'SV 90344). A generic stalker (300845) summoned on the table\'s spot for 3 s casts it on itself, so the chips fly '
    'at the table, not on Phalanx. Never Smash 54458\'s SV 3948 (blood and a stun swirl: VISUALS report). Look only.',
)
