"""
Blackrock Depths build WP-D2: Lord Roccor (9025; Loosed Earth 300780), normal and heroic
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 rows D2, s3.5 row D2, s3.6, s3.8, s3.9,
s3.10; build spec docs/dungeons/blackrock-depths-1-detention-block.md S1 230-410). WP-D2 owns this file (its spells:
kSpellsRoccor 210750-210779 of modules/mod-dungeon-bosses src/BlackrockDepths/BlackrockDepthsRework.h only;
RoccorLogic.h names the same ids; its creature: 300780). The engine side is
src/BlackrockDepths/boss_lord_roccor_rework.cpp; his road (waypoint path 473040) and texts are
data/sql/updates/pending_db_world/rev_roccor_blackrock_depths.sql.

- 9025 Lord Roccor: boss_lord_roccor_rework (SmartAI off: the S0 SQL rev drops his three stock rows), the build spec's
  normal health (110k: HealthModifier 47.993 on the level 51 warrior class base 2,292), stun immunity 1972 (the build
  spec's "stun immune"; stock -248 left him stunnable), INSTANCE_BIND (flags_extra 1), DamageModifier 3.5 (the stock
  value), and speed_walk 0.6 (1.5 yd/s, the build spec's Restless March; stock 1.556). Heroic 190k is WP-H's override
  (source/world/dungeons/blackrock_depths.py); the script walks him at 1.5 yd/s itself in combat and the waypoint path
  carries the speed out of combat, so the heroic row's speed_walk does not matter. He keeps his loot (lootid 9025).
  Retired: Ground Tremor 6524 (the 2 s AoE stun: the Loosed Earth cue now); Flame Shock 13729 and Earth Shock 13728 are
  replaced by the rescaled copies below (rule 15: a copy in the slice, never an edit of the stock spell).
- 300780 Loosed Earth (RO4): a boss-kit add, an earth elemental (type 4, faction 91 like Roccor), level 51 elite
  warrior class, 7,000 health (HealthModifier 3.0541 on 2,292), DamageModifier 3.9 (about 8% of the level 52
  reference row a swing: a 2.0 s swing of about 256 against Roccor's 228 at 3.5), no loot, no XP, stunnable (section 8
  #4: no shared-doc rule; built stunnable), the Lesser Rock Elemental's display 1161. npc_brd_loosed_earth. Heroic
  12,000 is WP-H's `_KIT_ADD_HEROIC` (difficulty_entry_1 310391, the first wave 1 kit add of heroic_ids.lock's order,
  STAGE-H-REPORT section 3).

Spells. The registry hits (Rampage's lane, Flung Boulders' circles) deal their damage through dungeon copies of the
mod-boss-mechanics resolve spell. Flame Shock, Earth Shock and Hurl Stone are percents of the reference row on the
kit's generic scripts (spell_dungeon_refflat_damage / _periodic: the hundredths in the effect, the heroic ones in
EffectMiscValueB). Underfoot's damage is the script's (10% of the Dark Iron's own health, Unit::DealDamage with no
combat, no spell); its two spells are looks. The merge heal's amount is the script's (CastCustomSpell, 3% of his
health). The rest are cast bars and looks:

  210750  Rampage            RO3 the 2.5 s rear-up (cast bar, emote line 1; not kickable)
  210751  Rampage            RO3 the lane's hit: resolve copy, Physical, 40% / 60%, the tank too, no Weakened
  210752  Rampage            RO3 the surge's look on him (1.5 s state aura: the boulder on the chest)
  210753  Ground Tremor      RO4 the 2 s cue (cast bar, emote line 2; not kickable; the stock shake and sound)
  210754  Loosed Earth       RO4 the add's rise (3 s state aura on itself: the dirt burst)
  210755  Return to Stone    RO4 the add crumbles (45 s) or merges (heroic): 1.5 s state aura on itself
  210756  Earthen Merge      heroic: the heal on him, 3% of his health a merge (script amount)
  210757  Underfoot          RO2 the crush look on him (Crush Under Foot's animation and sound)
  210758  Underfoot          RO2 the crack under a crushed Dark Iron (cast by it on itself; Ground Slam's crack)
  210759  Flung Boulders     RO5 heroic: a circle's hit: resolve copy, Physical, 25% + Weakened
  210760  Flung Boulders     RO5 the boulder in flight to a circle (Boulder Volley's missile, to the spot)
  210761  Flame Shock        RO6 his victim: 6% + 2% every 3 s for 12 s (heroic 8% + 3%), Fire, Magic
  210762  Earth Shock        RO7 a random player: 10% / 15% Nature and the stock 2 s school lockout
  210763  Hurl Stone         rule 10: a stone at his victim out of reach for 3 s, every 2 s, 15% / 20% Physical
  210764-210779 spare

Visual ids are V-1's (._visuals RO_*, DISPLAY_LOOSED_EARTH); every look is unconfirmed until seen in game.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
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
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_ELEMENTAL,
    TARGET_UNIT_CASTER,
    boss_columns,
    cast_bar,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_LOOSED_EARTH,
    RO_FLUNG_BOULDERS,
    RO_LOOSED_CUE,
    RO_LOOSED_SPAWN,
    RO_MERGE_HEAL,
    RO_RAMPAGE,
    RO_UNDERFOOT_CRACK,
    RO_UNDERFOOT_CRUSH,
)

creature_template_columns(9025, **boss_columns(
    'boss_lord_roccor_rework', 47.993, damage_modifier=3.5, speed_walk=0.6,
))

_RO = 'Blackrock Depths build WP-D2 (Lord Roccor)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage / spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')

_TARGET_DEST_DEST = 18
_MECHANIC_INTERRUPT = 26
_DISPEL_MAGIC = 1
_DEFENSE_NONE = 0
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a map change or a logout drops it, so nothing outlives the instance.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# Icons (the working-copy Spell.dbc).
_ICON_RAMPAGE = 965                 # Earthen - Boulder Rush (Charge) 55771
_ICON_GROUND_TREMOR = 66            # Ground Tremor 6524
_ICON_FLAME_SHOCK = 678             # Flame Shock 13729
_ICON_EARTH_SHOCK = 687             # Earth Shock 13728
_ICON_BOULDER = 2305                # Boulder Volley 38783
_ICON_GROUND_SLAM = 2144            # Ground Slam 33525

# The stock looks of the two kept shocks (their own SpellVisual ids, copied).
_SV_FLAME_SHOCK = 516
_SV_EARTH_SHOCK = 97

# Numbers (RoccorLogic.h).
_RAMPAGE_WARN_MS = 2500             # kRampageWarnMs
_SURGE_LOOK_MS = 1500               # kSurgeLookMs
_TREMOR_CAST_MS = 2000              # kTremorCastMs
_RISE_LOOK_MS = 3000                # Earthen Spawn Effect 55833's 3 s
_RETURN_LOOK_MS = 1500              # kLoosedFadeMs
_FLAME_SHOCK = (600, 800)           # kFlameShockPct, hundredths
_FLAME_SHOCK_TICK = (200, 300)      # kFlameShockTickPct, hundredths
_FLAME_SHOCK_MS = 12000             # kFlameShockMs
_FLAME_SHOCK_TICK_MS = 3000         # kFlameShockTickMs
_EARTH_SHOCK = (1000, 1500)         # kEarthShockPct, hundredths
_EARTH_SHOCK_LOCKOUT_MS = 2000      # kEarthShockLockoutMs
_SHOCK_RANGE = 20.0                 # kShockRangeYd
_HURL = (1500, 2000)                # kHurlPct, hundredths
_HURL_RANGE = 40.0                  # kHurlRangeYd
_BOULDER_SPEED = 30.0               # Boulder Volley 38783's own
_LOOSED_HEALTH_MODIFIER = 3.0541    # ceil(2,292 x 3.0541) = 7,000 at level 51 (kLoosedHealth normal)
_LOOSED_DAMAGE_MODIFIER = 3.9
LOOSED_EARTH_HEROIC_ENTRY = 310391  # heroic_ids.lock: the first wave 1 kit add (STAGE-H-REPORT section 3)

# The scripted hits: no threat, no crit, always hit, ignore the caster's modifiers (a percent of the reference row).
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
    AttributesEx2=ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
)


def _state_aura(spell_id: int, name: str, visual: int, duration_ms: int, icon: int, notes: str):
    """A hidden DUMMY aura on the caster that carries a SpellVisual's state kit for `duration_ms` (a state kit needs an
    aura to play; not passive: a passive aura is never sent to the client)."""
    return spell(
        id=spell_id, name=name, school=School.NATURE, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              CastingTimeIndex=1),
    )


# --- 300780 Loosed Earth ----------------------------------------------------------------------------------------------

loosed_earth_300780 = creature_template(
    300780, 'Loosed Earth', **{
        **kit_creature(faction=FACTION_ELEMENTAL, type=4), 'minlevel': 51, 'maxlevel': 51, 'rank': 1,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': _LOOSED_HEALTH_MODIFIER,
        'DamageModifier': _LOOSED_DAMAGE_MODIFIER, 'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0,
        'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_brd_loosed_earth',
        'difficulty_entry_1': LOOSED_EARTH_HEROIC_ENTRY,
    },
)
creature_model(300780, display_id=DISPLAY_LOOSED_EARTH)

# --- RO3 Rampage ------------------------------------------------------------------------------------------------------

rampage_cast_210750 = cast_bar(
    210750, 'Rampage', _RAMPAGE_WARN_MS, 'Rears up to Rampage down the road.',
    f'{_RO}, RO3: the rear-up, every 20 s (heroic 15 s) from 12 s: he stops on his road and rears up for 2.5 s (emote '
    'line 1) while the 20 x 8 yd lane shows ahead along the road (clipped at its end; turned round with under 10 yd '
    'left). Not kickable (cast_bar): the registry lane owns the hit (210751). Boulder Rush 55771\'s SV 12188 (the dust '
    'base on the cast; RISKY, the line marker carries the lane).',
    icon=_ICON_RAMPAGE, visual=RO_RAMPAGE,
)

rampage_210751 = resolve_copy(
    210751, 'Rampage', School.NORMAL, 'Roccor Rampages down the road.',
    f'{_RO}, RO3: the lane\'s hit when the rear-up ends: 40% (heroic 60%) of the row, the tank too (its own row), '
    'through the registry; no Weakened (the heroic hit is over 50%, shared doc section 4). Copy of the resolve spell '
    '205001 (Physical). The Dark Irons in the lane die (the script) and, on heroic, a Loosed Earth in it merges back '
    'into him (210756). No look of its own (the surge is the look).',
    icon=_ICON_RAMPAGE,
)

rampage_surge_210752 = _state_aura(
    210752, 'Rampage', RO_RAMPAGE, _SURGE_LOOK_MS, _ICON_RAMPAGE,
    f'{_RO}, RO3: the surge\'s look: cast by Roccor on himself (triggered) as he charges to the lane\'s end (24 yd/s, '
    'under a second), 1.5 s. Boulder Rush 55771\'s SV 12188 as a state (a boulder on the chest; never seen on a '
    'walking boss, RISKY). Look only.',
)

# --- RO4 Loosed Earth -------------------------------------------------------------------------------------------------

ground_tremor_210753 = cast_bar(
    210753, 'Ground Tremor', _TREMOR_CAST_MS, 'The ground heaves, and the stone stands up.',
    f'{_RO}, RO4: the Loosed Earth cue, every 25 s (heroic 20 s) from 18 s: he stops for a 2 s cast (emote line 2), '
    'then 2 (heroic 3) Loosed Earth 300780 rise at his feet (at most two waves alive). Not kickable (cast_bar). The '
    'stock Ground Tremor 6524\'s SV 858 (cast animation, sound and camera shake); its 2 s AoE stun is retired.',
    icon=_ICON_GROUND_TREMOR, visual=RO_LOOSED_CUE,
)

loosed_earth_rise_210754 = _state_aura(
    210754, 'Loosed Earth', RO_LOOSED_SPAWN, _RISE_LOOK_MS, _ICON_GROUND_TREMOR,
    f'{_RO}, RO4: the rise: each Loosed Earth casts it on itself (triggered) as it is summoned, 3 s. Earthen Spawn '
    'Effect 55833\'s SV 12201 (a dirt burst). Look only.',
)

return_to_stone_210755 = _state_aura(
    210755, 'Return to Stone', RO_LOOSED_SPAWN, _RETURN_LOOK_MS, _ICON_GROUND_TREMOR,
    f'{_RO}, RO4: a Loosed Earth returns to stone, 45 s after it rose or (heroic) when the Rampage lane catches it '
    '(the merge): it casts this on itself (triggered), turns passive and unselectable and despawns 1.5 s later. '
    'Earthen Spawn Effect\'s SV 12201 again (the dirt burst, read as the stone sinking back). Look only.',
)

earthen_merge_210756 = spell(
    id=210756, name='Earthen Merge', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Earthen Merge: 3% of the boss\'s health, the amount set by the boss script '
                                     '(CastCustomSpell), not a spell power value')],
    spell_icon_id=_ICON_GROUND_TREMOR,
    notes=f'{_RO}, heroic ("the mountain takes back its own"): a Loosed Earth caught in the Rampage lane merges back '
          'into Roccor: he casts this on himself (triggered) for 3% of his maximum health (5,700 on 190k), the amount '
          'set by the script. Cannot crit, ignores his modifiers, no threat. Heal 2060\'s SV 135 (the Heal_Low_Base '
          'flash on him); the add\'s own dirt burst is 210755.',
    raw_overrides=kit_raw('The stone returns to the mountain.', instant=True, SpellVisualID_1=RO_MERGE_HEAL,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)

# --- RO2 Underfoot ----------------------------------------------------------------------------------------------------

underfoot_210757 = self_visual(
    210757, 'Underfoot', RO_UNDERFOOT_CRUSH,
    f'{_RO}, RO2: Underfoot\'s look on Roccor: he casts it on himself (triggered) on a tick that crushes a Dark Iron, '
    'at most every 3 s. Crush Under Foot 45404\'s SV 10133 (the stomp animation and sound; it draws nothing). The '
    'damage is the script\'s: every second, each Anvilrage Guardsman 8891, Footman 8892, Fireguard 8909 or Bloodhound '
    '8921 within 6 yd of him takes 10% of its health (no threat, no combat; dead in 10 s).',
    icon=_ICON_GROUND_TREMOR,
)

underfoot_crack_210758 = self_visual(
    210758, 'Underfoot', RO_UNDERFOOT_CRACK,
    f'{_RO}, RO2 / RO3: the crack under a crushed Dark Iron: the Dark Iron casts it on itself (triggered) on an '
    'Underfoot tick (at most every 3 s) and when the Rampage lane kills it. Ground Slam 33525\'s SV 8083 (a 6.9 yd '
    'crack at the feet and a camera shake: hence the 3 s gate).',
    icon=_ICON_GROUND_SLAM,
)

# --- RO5 Flung Boulders (heroic) --------------------------------------------------------------------------------------

flung_boulders_210759 = resolve_copy(
    210759, 'Flung Boulders', School.NORMAL, 'A boulder crashes down.',
    f'{_RO}, RO5 heroic: every 5 s from 10 s, 3 circles of 3 yd at random floor points within 8 yd of him (the rocks '
    'his steps throw up; the floor probe keeps them off the wall side), a 2 s ground marker, then 25% of the row + '
    'Weakened, the tank too, through the registry. Copy of the resolve spell 205001 (Physical). The boulder in flight '
    'is 210760.',
    icon=_ICON_BOULDER,
)

flung_boulder_look_210760 = spell(
    id=210760, name='Flung Boulders', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=40.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_BOULDER,
    notes=f'{_RO}, RO5 heroic: the boulder in flight: Roccor casts it (triggered) at a circle\'s centre 0.4 s before '
          'the circle lands, so the rock comes down with the hit. Boulder Volley 38783\'s SV 8904 (the AerieBoulder '
          'missile, about 2.2 yd, and its impact) at its own 30 yd/s. Look only (the circle deals the damage).',
    raw_overrides=kit_raw(instant=True, Speed=_BOULDER_SPEED, SpellVisualID_1=RO_FLUNG_BOULDERS,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- RO6 Flame Shock, RO7 Earth Shock ---------------------------------------------------------------------------------

flame_shock_210761 = spell(
    id=210761, name='Flame Shock', school=School.FIRE, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=_SHOCK_RANGE, duration_ms=_FLAME_SHOCK_MS,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_FLAME_SHOCK[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=_FLAME_SHOCK_TICK[0] - 1, die_sides=1, amplitude=_FLAME_SHOCK_TICK_MS,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_FLAME_SHOCK,
    notes=f'{_RO}, RO6: the stock Flame Shock 13729 (48 fire + 13 every 3 s) rescaled (rule 15: a copy in the slice). '
          'On his victim in 20 yd, from 8 s, then every 8-18 s (the stock timers): 6% of the row (heroic 8%), then '
          '2% (heroic 3%) every 3 s for 12 s, the tank row on a tank (the kit\'s refflat scripts: hundredths 600 / '
          '200, EffectMiscValueB 800 / 300 on heroic). Magic: the dispel is a reward (the descriptor\'s dispel list). '
          'Cannot crit, always hits, ignores his modifiers. The stock SV 516. Dropped on a map change; removed from '
          'everyone when the fight ends.',
    raw_overrides=kit_raw('Instantly sears the target with fire, then burns it every 3 sec.',
                          'Burning every 3 sec.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          InterruptFlags=0, PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=_SV_FLAME_SHOCK,
                          EffectMiscValueB_1=_FLAME_SHOCK[1], EffectMiscValueB_2=_FLAME_SHOCK_TICK[1],
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, **_HIT_ATTRS),
)
scripted_by(flame_shock_210761, 'spell_dungeon_refflat_damage', 'spell_dungeon_refflat_periodic')

earth_shock_210762 = spell(
    id=210762, name='Earth Shock', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_SHOCK_RANGE,
    duration_ms=_EARTH_SHOCK_LOCKOUT_MS,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_EARTH_SHOCK[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
             Effect(type=EffectType.INTERRUPT_CAST, mechanic=_MECHANIC_INTERRUPT,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_EARTH_SHOCK,
    notes=f'{_RO}, RO7: the stock Earth Shock 13728 (110-120 nature plus the interrupt) rescaled (rule 15). On a '
          'random player in 20 yd and line of sight, the tank too (ruling 88), from 7 s, then every 12 s (the stock '
          'timers): 10% of the row (heroic 15%; hundredths 1000, EffectMiscValueB 1500), the tank row on a tank, plus '
          'the stock interrupt: a cast in progress is stopped and its school locked for 2 s (the spell\'s duration). '
          'A school lockout, not a loss of control. Cannot crit, always hits, ignores his modifiers. The stock SV 97.',
    raw_overrides=kit_raw('Instantly shocks the target with concussive force, interrupting spellcasting.',
                          instant=True, DefenseType=_DEFENSE_MAGIC, InterruptFlags=0,
                          PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=_SV_EARTH_SHOCK,
                          EffectMiscValueB_1=_EARTH_SHOCK[1], **_HIT_ATTRS),
)
scripted_by(earth_shock_210762, 'spell_dungeon_refflat_damage')

# --- Rule 10: Hurl Stone ----------------------------------------------------------------------------------------------

hurl_stone_210763 = spell(
    id=210763, name='Hurl Stone', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_HURL_RANGE,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_HURL[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_BOULDER,
    notes=f'{_RO}, handoff rule 10 (no free damage window; designer question 2): he never chases, so when his victim '
          'has been out of his melee reach for 3 s (a tank who stopped walking with him) he hurls a stone at it every '
          '2 s while it stays out: 15% of the row (heroic 20%; hundredths 1500, EffectMiscValueB 2000), the tank row '
          'on a tank. Physical, DefenseType none (no dodge or parry), always hits, cannot crit, ignores his '
          'modifiers. Boulder Volley 38783\'s SV 8904 at 30 yd/s.',
    raw_overrides=kit_raw('Hurls a stone at an enemy out of reach.', instant=True, DefenseType=_DEFENSE_NONE,
                          InterruptFlags=0, PreventionType=0, Speed=_BOULDER_SPEED,
                          SpellVisualID_1=RO_FLUNG_BOULDERS, EffectMiscValueB_1=_HURL[1], **_HIT_ATTRS),
)
scripted_by(hurl_stone_210763, 'spell_dungeon_refflat_damage')
