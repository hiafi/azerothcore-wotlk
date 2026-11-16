"""
Blackrock Spire build WP-B15: General Drakkisath's hard mode, the General's Army (heroic only)
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.7, s3.5 row B15, s3.6, s3.8 NM 13; build spec
docs/dungeons/blackrock-spire-rework.md SP 3990-4082 rows DR10-DR19, design SP 3828-3937, rulings 69-72). WP-B15 owns
this file (its spells: kSpellsGeneralsArmy 210560-210619 of modules/mod-dungeon-bosses
src/BlackrockSpire/BlackrockSpireRework.h; DrakkisathHardModeLogic.h names the same ids; creatures 300736-300741). The
engine side is src/BlackrockSpire/drakkisath_hard_mode.cpp on B14's hooks (DrakkisathFight.h). The core SQL rev
rev_drakkisath_hard_mode_blackrock_spire.sql writes the herald's spawn, gossip and `conditions`, the squads' weapons,
Drakkisath's line 9 and the herald's line 0 (the insult's Nefarius lines 18-19 are B12's rev).

Creatures (all hard mode only; the squads are summoned on heroic, so their normal rows only exist for the heroic
copies; health is set by the script at the summon, x the flex ladder):

- 300736 Rage Talon Dragonspawn (squad copy of 9096, display 2554, level 60): 17,000 at 5 (HealthModifier 5.570118 on
  the level 60 warrior base 3,052), npc_brs_army_soldier; heroic copy 310297 (WP-H's predicted lock line).
- 300737 Rage Talon Captain (copy of 10371, display 8310): 23,000 (7.536042); heroic 310298.
- 300738 Rage Talon Fire Tongue (copy of 10372, display 8309): 13,000 (4.259502); heroic 310299.
- 300739 Rage Talon Dragon Guard (copy of 10366, display 9753): 21,000 (6.880734); heroic 310300.
- 300740 Black Dragonkin Herald (DR11): npc_brs_generals_herald, V-2's DISPLAY_BLACK_DRAKONID, faction 35 (it never
  fights), gossip menu 300740 (npcflag 1: the heroic rollout's "npc" role, no heroic template), civilian, no XP.
- 300741 Challenge Ring (DR17): npc_brs_challenge_ring, the invisible stalker the kit's LethalRing summons on the ring's
  centre and the ring's look (210561) plays on.

Spells (looks from ._visuals, WP-V-2's DR_* and SV_RING_OF_FIRE_* picks; every look unconfirmed until seen in game):

  210560  Ring of Fire         DR17 the ring's strike: an outright kill (INSTAKILL + spell_dungeon_lethal_strike)
  210561  Ring of Fire         DR17 the ring's look: a 12 yd dynamic object on the carrier (Ring of Flame 35831's
                               PersistentArea SV 8386, the stock pick; its scaling to 12 yd is untested)
  210562  Ring of Fire         DR17 the fallback look: V-2's minted fixed-size ring state SV 90616 on the carrier
  210563  The Champion's       DR18 his 12 s duel bar (Physical, not interruptible: the script ends it early)
          Challenge
  210564  Champion's Challenge DR17 the challenger's 12 s mark (DUMMY debuff)
  210565  Blackblade Sweep     DR18 resolve copy, Physical: 40%, Weakened
  210566  Overhead Cleave      DR18 resolve copy, Physical: 50% (its own penalty, no Weakened)
  210567  Fire Blast           DR18 resolve copy, Fire: 30%, Weakened (also phase 1's answer to a distant attacker)
  210568  Ring of Flame        DR18 resolve copy, Fire: 40%, Weakened (the donut, 4 to 12 yd)
  210569  Thunderclap          DR18 resolve copy, Physical: 40%, Weakened (8 yd on him)
  210570  Fire Blast           DR18 his hands as the circles land (Fire Blast 2136's SV 143)
  210571  Ring of Flame        DR18 his breath as the donut lands (Conflagration 16805's SV 4326)
  210572  Finesse              DR18 +15% damage done a stack, up to 6, on the challenger (Adrenaline Rush's glow)
  210573  Humbled              DR18 won: +30% damage taken for 10 s, on him (Demoralizing Shout's ring)
  210574  Trophy               DR17 / DR18 lost or unanswered: +10% damage done a stack for the fight, on him
  210575  Cleaving Charge      DR13 the Dragonspawn's 1.5 s wind-up (Physical)
  210576  Cleaving Charge      DR13 resolve copy, Physical: 35%, Weakened
  210577  Cleaving Charge      DR13 the swing (Wide Swipe 6749's SV 399)
  210578  Captain's Command    DR13 +25% damage done, 2 s, refreshed every second on soldiers within 10 yd
  210579  Captain's Command    DR13 Battle Shout 6673's ring on the Captain, every 5 s
  210580  Scattering Flame     DR14 resolve copy, Fire: 30%, Weakened to everyone else in a mark's 6 yd
  210581  Scattering Flame     DR14 the 3 s mark on a player (DUMMY debuff)
  210582  Fireball Volley      DR14 the Fire Tongue's 2 s cast (Fire, interruptible; landed: its SpellScript)
  210583  Fireball Volley      DR14 resolve copy, Fire: 20% to everyone, no Weakened
  210584  Shield Wall          DR15 the Dragon Guard's shield (DUMMY; the script halves damage from the front)
  210585  Shield Charge        DR15 the 2 s wind-up, the shield lowered (Physical)
  210586  Shield Charge        DR15 resolve copy, Physical: 30%, Weakened (the script knocks the hit 5 yd aside)
  210587-210619 spare.

Tooltips are number-free where the number is a reference percent (Systems.md s10).
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
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_BLACKROCK,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    cast_bar,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_BLACK_DRAKONID,
    DISPLAY_INVISIBLE_STALKER,
    DR_CAPTAIN_COMMAND,
    DR_CHALLENGE_CIRCLE,
    DR_CONFLAGRATION,
    DR_FINESSE,
    DR_FIREBALL_VOLLEY,
    DR_HUMBLED,
    DR_RING_OF_FIRE,
    DR_SWEEP,
    SV_RING_OF_FIRE_STATE,
)

_B15 = 'Blackrock Spire build WP-B15 (General Drakkisath\'s hard mode, the General\'s Army)'
_VOLLEY_SCRIPT = 'spell_brs_army_fireball_volley'
_LETHAL_STRIKE = 'spell_dungeon_lethal_strike'

# --- shared bits -----------------------------------------------------------------------------------------------------

_TARGET_DEST_CASTER = 18
_EFFECT_INSTAKILL = 1               # SPELL_EFFECT_INSTAKILL (SharedDefines.h; not in lib/dsl's EffectType subset)
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): nothing outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15
_SCHOOL_MASK_ALL = 127
_TYPE_DRAGONKIN = 2
_FACTION_FRIENDLY = 35              # the herald: neutral to everyone, never in the fight
_NPCFLAG_GOSSIP = 0x1
_FLAGS_EXTRA_CIVILIAN_NO_XP = 0x2 | 0x40

# Icons (the working-copy Spell.dbc).
_ICON_RING_OF_FLAME = 11            # Ring of Flame 35831
_ICON_FIRE_BLAST = 12               # Fire Blast 2136
_ICON_FLAMESTRIKE = 37              # Flamestrike 16419
_ICON_FIREBALL_VOLLEY = 185         # Fireball Volley 15285
_ICON_THUNDERCLAP = 199             # Thunderclap 15548
_ICON_ADRENALINE_RUSH = 235         # Adrenaline Rush 13750
_ICON_SHIELD_WALL = 281             # Shield Wall 871
_ICON_DEMORALIZING_SHOUT = 282      # Demoralizing Shout 1160
_ICON_WIDE_SWIPE = 371              # Wide Swipe 6749
_ICON_BATTLE_SHOUT = 456            # Battle Shout 6673
_ICON_CHARGE = 457                  # Charge 100
_ICON_CONFLAGRATION = 937           # Conflagration 16805

# DrakkisathHardModeLogic.h: the numbers the declarations carry (lib/test_blackrock_spire_drakkisath_hard_mode.py pins
# them against the header).
_CHALLENGE_MS = 12000               # kChallengeMs
_RING_RADIUS = 12.0                 # kRingRadius
_FINESSE_PCT = 15                   # kFinessePctPerStack
_FINESSE_MAX = 6                    # kFinesseMax
_FINESSE_MS = 13000                 # kFinesseMs
_HUMBLED_PCT = 30                   # kHumbledPct
_HUMBLED_MS = 10000                 # kHumbledMs
_TROPHY_PCT = 10                    # kTrophyPctPerStack
_TROPHY_MAX = 255                   # kTrophyMax
_CLEAVING_CHARGE_CAST_MS = 1500     # kCleavingChargeCastMs
_COMMAND_PCT = 25                   # kCommandPct
_COMMAND_MS = 2000                  # kCommandAuraMs
_SCATTERING_WARN_MS = 3000          # kScatteringWarnMs
_VOLLEY_CAST_MS = 2000              # kVolleyCastMs
_SHIELD_CHARGE_CAST_MS = 2000       # kShieldChargeCastMs

# Fixed level 60 for exact health at 5 players (creature_classlevelstats, exp 0: warrior 3,052).
_DRAGONSPAWN_HEALTH_MODIFIER = 5.570118     # 17,000
_CAPTAIN_HEALTH_MODIFIER = 7.536042         # 23,000
_FIRE_TONGUE_HEALTH_MODIFIER = 4.259502     # 13,000
_DRAGON_GUARD_HEALTH_MODIFIER = 6.880734    # 21,000
# WP-H's predicted heroic lock lines (lib/test_blackrock_spire_heroic.py KIT_HEROIC_ID): the wave 2 kit adds in entry
# order after 300731 and 300733.
_HEROIC_ENTRY = {300736: 310297, 300737: 310298, 300738: 310299, 300739: 310300}

# --- 300736-300739 the squads (Rage Talon copies: the stock units are trash elsewhere in the Spire) -----------------

_KIT_DRAGONKIN = kit_creature(faction=FACTION_BLACKROCK, type=_TYPE_DRAGONKIN)
assert KIT_CREATURE['faction'] == FACTION_BLACKROCK


def _soldier(entry: int, health_modifier: float, damage_modifier: float) -> dict:
    """A squad soldier's columns: level 60 elite dragonkin, the stock copy's speeds and melee, npc_brs_army_soldier."""
    return {
        **_KIT_DRAGONKIN, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'unit_class': 1, 'unit_flags': 0,
        'speed_walk': 0.888888, 'speed_run': 1.42857, 'HealthModifier': health_modifier,
        'DamageModifier': damage_modifier, 'BaseAttackTime': 2000, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
        'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_brs_army_soldier', 'difficulty_entry_1': _HEROIC_ENTRY[entry],
    }


# One literal creature_template(<entry>, ...) call each: WP-H's blackrock_spire.py finds the declared kit adds by it.
rage_talon_dragonspawn_300736 = creature_template(
    300736, 'Rage Talon Dragonspawn', **_soldier(300736, _DRAGONSPAWN_HEALTH_MODIFIER, 5.0))
creature_model(300736, display_id=2554)
rage_talon_captain_300737 = creature_template(
    300737, 'Rage Talon Captain', **_soldier(300737, _CAPTAIN_HEALTH_MODIFIER, 6.0))
creature_model(300737, display_id=8310)
rage_talon_fire_tongue_300738 = creature_template(
    300738, 'Rage Talon Fire Tongue', **_soldier(300738, _FIRE_TONGUE_HEALTH_MODIFIER, 6.0))
creature_model(300738, display_id=8309)
rage_talon_dragon_guard_300739 = creature_template(
    300739, 'Rage Talon Dragon Guard', **_soldier(300739, _DRAGON_GUARD_HEALTH_MODIFIER, 6.0))
creature_model(300739, display_id=9753)

# --- 300740 the herald, 300741 the ring's carrier --------------------------------------------------------------------

black_dragonkin_herald_300740 = creature_template(
    300740, 'Black Dragonkin Herald', **{
        **_KIT_DRAGONKIN, 'subname': 'Voice of Lord Victor', 'faction': _FACTION_FRIENDLY, 'minlevel': 60,
        'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'unit_flags': 0, 'HealthModifier': 1.0, 'DamageModifier': 0.0,
        'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'npcflag': _NPCFLAG_GOSSIP, 'gossip_menu_id': 300740, 'flags_extra': _FLAGS_EXTRA_CIVILIAN_NO_XP,
        'ScriptName': 'npc_brs_generals_herald',
    },
)
creature_model(300740, display_id=DISPLAY_BLACK_DRAKONID)

challenge_ring_300741 = creature_template(
    300741, 'Challenge Ring', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                 'ScriptName': 'npc_brs_challenge_ring'},
)
creature_model(300741, display_id=DISPLAY_INVISIBLE_STALKER)

# --- shared builders -------------------------------------------------------------------------------------------------


def _aura(spell_id: int, name: str, *, aura: AuraType, points: int, duration_ms: int, target: int, debuff: bool,
          icon: int, desc: str, aura_desc: str, notes: str, stacks: int = 0, visual: int = 0,
          excluded: str | None = None, school: School = School.NORMAL):
    """An aura the script applies (triggered): not dispellable, dropped on a map change."""
    raw = kit_raw(desc, aura_desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                  AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP)
    if stacks:
        raw['CumulativeAura'] = stacks
    if visual:
        raw['SpellVisualID_1'] = visual
    effect = dict(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=points, die_sides=0,
                  implicit_target_a=target)
    if aura != AuraType.DUMMY:
        effect['misc_value'] = _SCHOOL_MASK_ALL
    if excluded:
        effect['potency_excluded'] = excluded
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0,
        attributes=(ATTR0_AURA_IS_DEBUFF if debuff else 0) | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(**effect)], spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _hit(spell_id: int, name: str, school: School, desc: str, notes: str, icon: int):
    return resolve_copy(spell_id, name, school, desc, notes, icon=icon)


# --- DR17 the ring ---------------------------------------------------------------------------------------------------

ring_strike_210560 = spell(
    id=210560, name='Ring of Fire', school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    attributes=ATTR0_NO_ACTIVE_DEFENSE | ATTR0_NO_IMMUNITIES,
    effects=[Effect(type=_EFFECT_INSTAKILL, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_RING_OF_FLAME,
    notes=f'{_B15}, DR17: the Champion\'s Challenge ring\'s strike (the kit\'s LethalRing killSpell): an outright kill '
          'of whoever stands in the 12 yd band or crosses it while it is armed (1.5 s after the close, 10.5 s; the '
          'arena-wall precedent, user ruling F-2). SPELL_EFFECT_INSTAKILL (no absorb or reduction applies) and '
          'spell_dungeon_lethal_strike kills a survivor after the hit; NO_IMMUNITIES, ALWAYS_HIT, ignores caster '
          'modifiers, no LoS, cannot crit, no threat, not reflected or redirected (the Stratholme 206400 shape). Pets '
          'are pushed out and never struck, the challenger dies stepping out (the defaults pending the user). Fire '
          'Blast 2136\'s SV 143 on the victim.',
    raw_overrides=kit_raw('Stepping through the ring of fire is death.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          SpellVisualID_1=DR_CHALLENGE_CIRCLE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(ring_strike_210560, _LETHAL_STRIKE)

ring_look_210561 = spell(
    id=210561, name='Ring of Fire', school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_CHALLENGE_MS,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                    implicit_target_a=_TARGET_DEST_CASTER, radius_yards=_RING_RADIUS)],
    spell_icon_id=_ICON_RING_OF_FLAME,
    notes=f'{_B15}, DR17: the ring\'s look, visual only (kRingLookSpell). The carrier 300741 the kit summons on the '
          'ring\'s centre casts it on itself: a dynamic object of 12 yd for 12 s with Ring of Flame 35831\'s '
          'PersistentArea FlameCircleEffect (SV 8386, V-2\'s stock pick: stock draws it at 7 yd; whether the client '
          'scales it to the 12 yd radius is untested, the fallback is 210562). Its DUMMY aura reaches nobody harmful: '
          'the registry\'s lethal Donut owns the strike.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=DR_RING_OF_FIRE, InterruptFlags=0, PreventionType=0,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

ring_look_alt_210562 = spell(
    id=210562, name='Ring of Fire', school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_CHALLENGE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_RING_OF_FLAME,
    notes=f'{_B15}, DR17: the fallback ring look (kRingLookSpell, if the stock ring does not scale to 12 yd): a 12 s '
          'DUMMY aura on the carrier with V-2\'s minted fixed-size Flame Circle state (SV 90616, the stock model at '
          'scale 5.14).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=SV_RING_OF_FIRE_STATE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- DR18 the Challenge ----------------------------------------------------------------------------------------------

challenge_bar_210563 = cast_bar(
    210563, 'The Champion\'s Challenge', _CHALLENGE_MS, 'Drakkisath duels his challenger.',
    f'{_B15}, DR18: his 12 s duel bar while the ring stands (the cast queue\'s hold). DUMMY on the caster, not '
    'interruptible, Physical (his kickable Flamestrike is Fire: a kick never locks it). The script stops it when the '
    'duel ends early (a win, a dead challenger): B14 ends the hold with it.',
    icon=_ICON_RING_OF_FLAME,
)

challenger_210564 = _aura(
    210564, 'Champion\'s Challenge', aura=AuraType.DUMMY, points=0, duration_ms=_CHALLENGE_MS,
    target=TARGET_UNIT_TARGET_ANY, debuff=True, icon=_ICON_CHARGE,
    desc='You answered the Champion\'s Call.', aura_desc='Dueling General Drakkisath inside the ring of fire.',
    notes=f'{_B15}, DR17: the challenger\'s mark for the duel (the first player into the Call\'s circle who is not his '
          'tank). DUMMY: the tell. Removed when the Challenge ends.',
)

sweep_210565 = _hit(
    210565, 'Blackblade Sweep', School.NORMAL, 'Drakkisath sweeps the Blackblade at his challenger.',
    f'{_B15}, DR18: a blow, 180 degrees and 10 yd in front of him at the challenger (the challenger only): 40% of the '
    'reference row (x his Trophies) and 1 Weakened. Copy of the resolve spell 205001 (Physical), no look (B14\'s '
    '210537 swing).', _ICON_WIDE_SWIPE,
)

overhead_cleave_210566 = _hit(
    210566, 'Overhead Cleave', School.NORMAL, 'Drakkisath brings the Blackblade down on his challenger.',
    f'{_B15}, DR18: a blow, a 60 degree cone 15 yd at the challenger: 50% (its own penalty: no Weakened). Copy of the '
    'resolve spell 205001 (Physical), no look (B14\'s 210537 swing).', _ICON_WIDE_SWIPE,
)

fire_blast_210567 = _hit(
    210567, 'Fire Blast', School.FIRE, 'Flame bursts under the challenger.',
    f'{_B15}, DR18: a blow, three 4 yd circles at and beside the challenger: 30% each and 1 Weakened. Also phase 1\'s '
    'answer (wave 2 lesson 2): a 4 yd circle at the feet of anyone who hurts him from beyond 10 yd while he is rooted '
    'in his alcove (every 6 s per attacker). Copy of the resolve spell 205001 (Fire), no look (210570).',
    _ICON_FIRE_BLAST,
)

ring_of_flame_210568 = _hit(
    210568, 'Ring of Flame', School.FIRE, 'A ring of flame erupts around Drakkisath.',
    f'{_B15}, DR18: a blow, a donut 4 to 12 yd from him (get in close): 40% and 1 Weakened. Copy of the resolve spell '
    '205001 (Fire), no look (210571).', _ICON_RING_OF_FLAME,
)

thunderclap_210569 = _hit(
    210569, 'Thunderclap', School.NORMAL, 'Drakkisath strikes the ground at his feet.',
    f'{_B15}, DR18: a blow, an 8 yd circle on him (get out): 40% and 1 Weakened. Copy of the resolve spell 205001 '
    '(Physical), no look (B14\'s 210529 clap).', _ICON_THUNDERCLAP,
)

fire_blast_look_210570 = self_visual(
    210570, 'Fire Blast', DR_CHALLENGE_CIRCLE,
    f'{_B15}, DR18: his hands as the Fire Blast circles (and phase 1\'s answer) land, cast on himself (triggered). '
    'Fire Blast 2136\'s SV 143 (hands and a chest flash; the circles are the registry\'s markers).',
    icon=_ICON_FIRE_BLAST, school=School.FIRE,
)

ring_of_flame_look_210571 = self_visual(
    210571, 'Ring of Flame', DR_CONFLAGRATION,
    f'{_B15}, DR18: his breath as the donut lands, cast on himself (triggered). Conflagration 16805\'s SV 4326 (the '
    'retired spell\'s look, kept: dragon breath and a fire impact).',
    icon=_ICON_CONFLAGRATION, school=School.FIRE,
)

finesse_210572 = _aura(
    210572, 'Finesse', aura=AuraType.MOD_DAMAGE_PERCENT_DONE, points=_FINESSE_PCT, duration_ms=_FINESSE_MS,
    target=TARGET_UNIT_TARGET_ANY, debuff=False, icon=_ICON_ADRENALINE_RUSH, stacks=_FINESSE_MAX, visual=DR_FINESSE,
    desc='Each blow you avoid sharpens your strikes.', aura_desc='Damage done increased by $s1% for each stack.',
    excluded='Finesse: a flat +15% damage done per stack, not a damage or heal value',
    notes=f'{_B15}, DR18: each blow the challenger avoids adds a stack (DungeonKit::AddStacks, CumulativeAura 6): '
          '+15% damage done, every school, until the Challenge ends (the script removes it; 13 s as a safety). '
          'Adrenaline Rush 13750\'s lasting glow (SV 8996).',
)

humbled_210573 = _aura(
    210573, 'Humbled', aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, points=_HUMBLED_PCT, duration_ms=_HUMBLED_MS,
    target=TARGET_UNIT_CASTER, debuff=True, icon=_ICON_DEMORALIZING_SHOUT, visual=DR_HUMBLED,
    desc='Beaten in single combat.', aura_desc='Damage taken increased by $s1%.',
    excluded='Humbled: a flat +30% damage taken, not a damage or heal value',
    notes=f'{_B15}, DR18: the Challenge won (18,000 damage by the challenger inside the ring at every size, ruling '
          '72): he staggers, +30% damage taken for 10 s (line 6). He casts it on himself (triggered). Demoralizing '
          'Shout 1160\'s ring and squiggle (SV 210).',
)

trophy_210574 = _aura(
    210574, 'Trophy', aura=AuraType.MOD_DAMAGE_PERCENT_DONE, points=_TROPHY_PCT, duration_ms=-1,
    target=TARGET_UNIT_CASTER, debuff=False, icon=_ICON_RING_OF_FLAME, stacks=_TROPHY_MAX,
    desc='Another trophy for the black flight.', aura_desc='Damage done increased by $s1% for each trophy.',
    excluded='Trophy: a flat +10% damage done per stack, not a damage or heal value',
    notes=f'{_B15}, DR17 / DR18: a Challenge lost (time up, or the challenger died: line 7) or a Call unanswered (line '
          '5): +10% damage done per stack for the rest of the fight, no cap (CumulativeAura 255). The aura raises his '
          'melee; his spells and registry hits ignore caster modifiers, so B14\'s DamageDealt hands them to the hard '
          'mode (OnDamageDealt, TrophyDamage): B14\'s kit and the blows grow alike (R-2). The squads own their own '
          'hits. Removed when the pull ends. No look: the buff icon.',
)

# --- DR13 Vanguard ---------------------------------------------------------------------------------------------------

cleaving_charge_bar_210575 = cast_bar(
    210575, 'Cleaving Charge', _CLEAVING_CHARGE_CAST_MS, 'The dragonspawn rears back to cleave.',
    f'{_B15}, DR13: the Dragonspawn\'s 1.5 s wind-up, 4 s after it reaches the hall, then every 8 s. DUMMY on the '
    'caster, not interruptible, Physical. The registry\'s 90 degree, 8 yd cone in front of it owns the hit.',
    icon=_ICON_WIDE_SWIPE,
)

cleaving_charge_210576 = _hit(
    210576, 'Cleaving Charge', School.NORMAL, 'The dragonspawn cleaves everything before it.',
    f'{_B15}, DR13: a 90 degree, 8 yd cone in front of the Dragonspawn (a Frontal: its fixated player aims it and is '
    'spared): 35% (x1.25 within 10 yd of a Captain) and 1 Weakened. Copy of the resolve spell 205001 (Physical), no '
    'look (210577).', _ICON_WIDE_SWIPE,
)

cleaving_charge_look_210577 = self_visual(
    210577, 'Cleaving Charge', DR_SWEEP,
    f'{_B15}, DR13: the Dragonspawn\'s swing as the cone resolves, cast on itself (triggered). Wide Swipe 6749\'s SV '
    '399 (a self DUMMY applies no aura, so its StunSwirl state never shows).',
    icon=_ICON_WIDE_SWIPE,
)

command_210578 = _aura(
    210578, 'Captain\'s Command', aura=AuraType.MOD_DAMAGE_PERCENT_DONE, points=_COMMAND_PCT, duration_ms=_COMMAND_MS,
    target=TARGET_UNIT_TARGET_ANY, debuff=False, icon=_ICON_BATTLE_SHOUT,
    desc='A Rage Talon Captain drives his soldiers on.', aura_desc='Damage done increased by $s1%.',
    excluded='Captain\'s Command: a flat +25% damage done, not a damage or heal value',
    notes=f'{_B15}, DR13: the Captain casts it (triggered) every second on every other living squad soldier within '
          '10 yd: +25% damage done for 2 s (their melee and stock strikes; the script also raises their registry '
          'hits by 25% while they carry it). Kill the Captain first (the boss data).',
)

command_look_210579 = self_visual(
    210579, 'Captain\'s Command', DR_CAPTAIN_COMMAND,
    f'{_B15}, DR13: the Captain\'s shout ring, cast on himself (triggered) every 5 s. Battle Shout 6673\'s SV 246.',
    icon=_ICON_BATTLE_SHOUT,
)

# --- DR14 Fire Line --------------------------------------------------------------------------------------------------

scattering_flame_210580 = _hit(
    210580, 'Scattering Flame', School.FIRE, 'The flame on an ally bursts.',
    f'{_B15}, DR14: each Fire Tongue marks 2 / 4 players (5 / 6 or more) every 10 s; 3 s later each mark bursts on '
    'everyone else within 6 yd of it (a registry Spread): 30% (x1.25 commanded) and 1 Weakened. Copy of the resolve '
    'spell 205001 (Fire), no look.', _ICON_FLAMESTRIKE,
)

scattering_mark_210581 = _aura(
    210581, 'Scattering Flame', aura=AuraType.DUMMY, points=0, duration_ms=_SCATTERING_WARN_MS,
    target=TARGET_UNIT_TARGET_ANY, debuff=True, icon=_ICON_FLAMESTRIKE, school=School.FIRE,
    desc='A flame clings to you, about to burst.', aura_desc='Bursting soon: stand apart from your allies.',
    notes=f'{_B15}, DR14: the 3 s mark the Fire Tongue casts (triggered) on each marked player (the registry draws the '
          '6 yd circle; this is the debuff tell).',
)

fireball_volley_210582 = spell(
    id=210582, name='Fireball Volley', school=School.FIRE, cast_time_ms=_VOLLEY_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FIREBALL_VOLLEY,
    notes=f'{_B15}, DR14: the Fire Tongue\'s expected interrupt (the descriptor\'s list, priority 2, below his '
          'Flamestrike), 8 s after it reaches the hall, then every 12 s. DUMMY on the caster, 2 s, interruptible and '
          'silence-preventable (InterruptFlags 15, PreventionType silence; the squads have no immunity set). Landed '
          '(spell_brs_army_fireball_volley, AfterCast; a kicked cast never gets there): 210583 on everyone. Fireball '
          'Volley 15285\'s SV 2437 (the missiles and impacts). Fire: the Fire Tongue\'s own school lockout only.',
    raw_overrides=kit_raw('The Fire Tongue hurls fire at everyone. Interrupt it!',
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=DR_FIREBALL_VOLLEY),
)
scripted_by(fireball_volley_210582, _VOLLEY_SCRIPT)

volley_hit_210583 = _hit(
    210583, 'Fireball Volley', School.FIRE, 'Fireballs rain on the group.',
    f'{_B15}, DR14: the landed volley, on every player of the fight (DungeonKit::RegistryHit): 20% (x1.25 commanded), '
    'group damage, no Weakened. Copy of the resolve spell 205001 (Fire), no look (the cast\'s own).',
    _ICON_FIREBALL_VOLLEY,
)

# --- DR15 Shield Wall ------------------------------------------------------------------------------------------------

shield_front_210584 = _aura(
    210584, 'Shield Wall', aura=AuraType.DUMMY, points=0, duration_ms=-1, target=TARGET_UNIT_CASTER, debuff=False,
    icon=_ICON_SHIELD_WALL, desc='Shields forward.', aura_desc='Takes half damage from the front. Strike it from the '
    'side or behind.',
    notes=f'{_B15}, DR15: on every squad Dragon Guard from its summon (AddAura): the tell. The script halves damage '
          'from attackers in its front 180 degrees (ShieldFrontDamage in the soldier\'s DamageTaken).',
)

shield_charge_bar_210585 = cast_bar(
    210585, 'Shield Charge', _SHIELD_CHARGE_CAST_MS, 'The Dragon Guard lowers its shield to charge.',
    f'{_B15}, DR15: the 2 s wind-up of one Shield Wall Dragon Guard in turn, every 10 s from 5 s after the squad '
    'reaches the hall, facing a random player. DUMMY on the caster, not interruptible, Physical. The registry\'s 4 yd, '
    '25 yd lane owns the hit; the Guard then charges along it.',
    icon=_ICON_CHARGE,
)

shield_charge_210586 = _hit(
    210586, 'Shield Charge', School.NORMAL, 'A Dragon Guard charges through the line.',
    f'{_B15}, DR15: the lane\'s hit, 4 yd wide and 25 yd long from the Guard: 30% (x1.25 commanded) and 1 Weakened; '
    'the script knocks everyone hit 5 yd aside (away from the lane\'s axis). Copy of the resolve spell 205001 '
    '(Physical), no look (the charge).', _ICON_CHARGE,
)
