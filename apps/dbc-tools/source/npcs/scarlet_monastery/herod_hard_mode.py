"""
Scarlet Monastery build WP-D11H: Herod's hard mode, Call to Arms (heroic only;
.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.7, s3.5 row D11H, s7 #31 A; build spec
docs/dungeons/scarlet-monastery-3-armory.md "Hard mode: Call to Arms", HM0-HM3 and the Build spec rows). WP-D11H owns
this file; WP-S0 wrote the stub. The engine side is modules/mod-dungeon-bosses src/ScarletMonastery/herod_hard_mode.cpp
(on D11's HerodFight.h hooks), the pure rules HerodHardModeLogic.h. Herod's lines 5-8, the wall rack (gameobject
301328, a heroic spawn) and the planted axe's prop (301329) are
data/sql/updates/pending_db_world/rev_herod_hard_mode_scarlet_monastery.sql.

- 300944 Scarlet Garrison Trainee (HM2a): three squads of four march in through Herod's Door during his prayer, down
  the south side to the pillar (a scripted straight line with a jump off the ledge, s7 #31 A); each that arrives
  kneels and fades into the Light and Herod gains a stack of Zeal. Level 60, 5k, no attacks and no threat
  (npc_sm_garrison_trainee: passive marchers), no immunity set (stuns, slows, roots, knockbacks and crowd control all
  buy time: the build spec's rewards), no loot or XP. Display 2467 / 2478 (the Scarlet Trainee, V's
  DISPLAY_GARRISON_TRAINEE); the script hands it the trainee's mace. Heroic entry 310478 once H's mint order settles
  (5k: H's _KIT_ADD_HEROIC_WAVE_2).
- 300945 Ravager (planted, HM3): the axe in the floor at the pit's center from his prayer to the end: not selectable,
  never fights (KIT_HELPER), an invisible stalker (display 11686) that carries the glow, the consecrated floor's look
  and the beams' chains. The axe itself is the stock stuck-axe model, gameobject 301329 (GODI 8494, V's
  GODI_PLANTED_RAVAGER, first pick) summoned on the same spot. No heroic template (it runs on its normal entry, H's
  list of units without one).

Both exist only on heroic (the hard mode is heroic only). Wave 2: both are declared now (H's `_declared` reads the
text, not the gate); only the trainee's ScriptName waits for BIND_WAVE_2 (its C++ AI registers once kWave2Bound
flips), as Crell's.

Spells (kSpellsCallToArms 213020-213059; HerodHardModeLogic.h names the same ids; looks from ._visuals, V's HM_* / HB_*
picks, every look unconfirmed until seen in game):

  213020  Call to Arms           HM0 the hard mode's red aura on Herod from the /taunt (and every hard mode pull): holds
                                 a wipe
  213021  Prayer of the Champion HM2 unharmable (school immunity to all) while he prays; the kneel's look
  213022  Prayer of the Champion HM2 the pillar of Light on him (the Ascension pillar, 3 yd)
  213023  Zeal                   HM2b +5% damage done and +5% attack speed a stack, six at most (HANDOFF
                                 section 10 add sizing C), the rest of the fight
  213024  Into the Light         HM2a an arrived trainee fades into the Light (look)
  213025  Ravager's Beacon       HM3 the planted axe's glow (one-shot, replayed every 4 s)
  213026  Ravager's Beacon       HM3 a beam's chain from its end stalker to the axe (a channel, look only)
  213027  Ravager's Beacon       HM3 a beam step's hit: resolve copy, Holy, 45% and Weakened
  213028  Consecrated Hall       HM1 the tick on every player in the fight: 4% of the reference row every 2 s (the kit's
                                 percent script), Holy
  213029  Consecrated Hall       HM1 the consecrated floor's look on the planted axe (the hall's radius)
  213030-213059 spare.

Tooltips are number-free where the number is a reference percent.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
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
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    FACTION_SCARLET_CRUSADE,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_SCARLET_TRAINEE,
    DISPLAY_SCARLET_TRAINEE_ALT,
    HB_RAVAGER_GLOW,
    HB_ZEAL,
    HM_BEAM,
    HM_HALL,
    HM_KNEEL,
    HM_PRAYER_PILLAR,
    HM_RED_AURA,
)

_D11H = 'Scarlet Monastery build WP-D11H (Herod\'s hard mode, Call to Arms)'

# --- the creatures ---------------------------------------------------------------------------------------------------

# The trainee's heroic entry (difficulty_entry_1 = its id in source/world/heroic_ids.lock). WP-H's mint table names
# 310478 (after Crell 310476 and Halden 310477); every lower kit unit is declared, so the run mints exactly that id
# (W2-SETUP's reconcile; lib/test_scarlet_monastery_heroic.py KIT_HEROIC_ID names the same id).
GARRISON_TRAINEE_HEROIC_PLANNED = 310478
GARRISON_TRAINEE_HEROIC = GARRISON_TRAINEE_HEROIC_PLANNED

GARRISON_TRAINEE = 300944
PLANTED_RAVAGER = 300945
TRAINEE_SCRIPT = 'npc_sm_garrison_trainee'

_CLASS_WARRIOR = 1
_CREATURE_TYPE_HUMANOID = 7
_FLAGS_EXTRA_NO_XP = 0x40
_LEVEL = 60

# The garrison's health at level 60 (section 3.6: 12 x 5k; the warrior base 3,052, creature_classlevelstats basehp0,
# live 2026-11-20): 5k = 1.6383 x 3,052. No melee: they march only (rule 19 does not apply).
GARRISON_HEALTH = 5000
_BASE_HP_60_WARRIOR = 3052
GARRISON_HEALTH_MODIFIER = round(GARRISON_HEALTH / _BASE_HP_60_WARRIOR, 4)


def _heroic_entry(columns: dict, heroic_entry) -> dict:
    """`columns` with difficulty_entry_1 when the heroic entry is known (a declared full row must carry it)."""
    if heroic_entry:
        return {**columns, 'difficulty_entry_1': heroic_entry}
    return columns


_NO_LOOT = {'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'ExperienceModifier': 0.0,
            'flags_extra': _FLAGS_EXTRA_NO_XP, 'AIName': ''}

garrison_trainee_300944 = creature_template(300944, 'Scarlet Garrison Trainee', **_heroic_entry({
    **KIT_CREATURE, **_NO_LOOT, 'faction': FACTION_SCARLET_CRUSADE, 'type': _CREATURE_TYPE_HUMANOID,
    'minlevel': _LEVEL, 'maxlevel': _LEVEL, 'rank': 0, 'unit_class': _CLASS_WARRIOR, 'unit_flags': 0,
    'HealthModifier': GARRISON_HEALTH_MODIFIER, 'DamageModifier': 0.0, 'BaseAttackTime': 2000,
    'speed_walk': 1.0, 'speed_run': 1.14286, 'detection_range': 0.0, 'CreatureImmunitiesId': 0,
    'ScriptName': TRAINEE_SCRIPT if BIND_WAVE_2 else '',
}, GARRISON_TRAINEE_HEROIC))
creature_model(300944, display_id=DISPLAY_SCARLET_TRAINEE, idx=0, probability=1.0)
creature_model(300944, display_id=DISPLAY_SCARLET_TRAINEE_ALT, idx=1, probability=1.0)

planted_ravager_300945 = creature_template(300945, 'Ravager', **{
    **KIT_HELPER, 'minlevel': _LEVEL, 'maxlevel': _LEVEL, 'rank': 0, 'unit_class': _CLASS_WARRIOR,
    'ScriptName': '', 'AIName': '',
})
creature_model(300945, display_id=DISPLAY_INVISIBLE_STALKER)

# --- constants (HerodHardModeLogic.h; lib/test_scarlet_monastery_herod_hard_mode.py pins each against the header) -----

ZEAL_PCT = 5                        # kZealPct
ZEAL_MAX = 6                        # kZealMax (HANDOFF section 10 add sizing C: capped at 6)
HALL_HUNDREDTHS = 400               # kHallHundredths: 4% a tick every 2 s (heroic only: the same in both slots)
HALL_TICK_MS = 2000                 # kHallTickMs
BEAM_LOOK_MS = 60000                # the chain's channel; the kit re-casts it when it is not channeling

_DISPEL_NONE = 0
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127
_AURA_SCHOOL_IMMUNITY = 39          # SPELL_AURA_SCHOOL_IMMUNITY (not in lib.dsl's AuraType)
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR1_AURA_STAYS_AFTER_COMBAT = 0x02000000  # Unit::RemoveEvadeAuras keeps it: the red aura holds a wipe

_SCRIPT_REFFLAT = ('Scarlet Monastery D11H: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn: the tank row on the tank)')

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock client 2026-11-20)
_ICON_ZEAL = 51                     # Zeal 8191 (and Consecration 26573)
_ICON_DIVINE_SHIELD = 81            # Divine Shield 642
_ICON_BEACON = 3032                 # Beacon of Light 53563
_ICON_CONSECRATION = 51             # Consecration 26573
_ICON_TAUNT = 24                    # the Warrior's Taunt 355 (the /taunt he answers)


def _self_aura(spell_id: int, name: str, school: School, visual: int, icon: int, desc: str, aura_desc: str, notes: str,
               *, attributes_ex: int = ATTR1_NO_THREAT):
    """A look-only DUMMY aura a unit casts on itself (triggered), no duration (removed with its caster or by script)."""
    return spell(
        id=spell_id, name=name, school=school, dispel=_DISPEL_NONE, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1, SpellVisualID_1=visual,
                              AttributesEx=attributes_ex, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- HM0 The Real Challenge ------------------------------------------------------------------------------------------

red_aura_213020 = _self_aura(
    213020, 'Call to Arms', School.HOLY, HM_RED_AURA, _ICON_TAUNT,
    'The Champion of the Crusade answers the challenge.', 'Call to Arms: the Champion will face you with all of it.',
    f'{_D11H}, HM0: the hard mode\'s aura on Herod, cast on himself (triggered) when a player\'s /taunt lights the '
    'hard mode (heroic, out of combat; the instance\'s DATA_HARD_MODE_HEROD), at every hard mode pull, and by the '
    'out-of-combat idle hook while the flag is lit (a cold load, a wipe). A DUMMY with no effect: the read is the '
    'hard mode red aura SV 90554 (V\'s HM_RED_AURA, the stock deathknight_plaguestrikestatered). '
    'AURA_STAYS_AFTER_COMBAT: an evade keeps it (the flag holds through wipes); his death clears it.',
    attributes_ex=ATTR1_NO_THREAT | _ATTR1_AURA_STAYS_AFTER_COMBAT,
)

# --- HM2 The Garrison Answers ----------------------------------------------------------------------------------------

prayer_213021 = spell(
    id=213021, name='Prayer of the Champion', school=School.HOLY, dispel=_DISPEL_NONE, mechanic=0,
    attributes=ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_SCHOOL_IMMUNITY, base_points=0,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DIVINE_SHIELD,
    notes=f'{_D11H}, HM2 the Garrison Answers: at 50% he walks to the pillar 3 yd short of the pit\'s center, drives '
          'Ravager into the floor and kneels; he casts this on himself (triggered) for the 20 s prayer and the script '
          'removes it at his rising: "he cannot be harmed while he prays" (the approved free window: the garrison is '
          'there to fight). SPELL_AURA_SCHOOL_IMMUNITY to every school (the D8H shard ward shape); the AI also zeroes '
          'any damage that still reaches him (DamageTaken). His heal to full is the script\'s (his health on a '
          'straight line over the 20 s). The bots ignore him while he has it (the descriptor). The kneel\'s look: '
          'Kneel 68442\'s SV 14427 (V\'s HM_KNEEL, animation 115) plus the kneel stand state. Not dispellable.',
    raw_overrides=kit_raw('Herod prays. He cannot be harmed.', 'Praying in the Light: cannot be harmed.',
                          CastingTimeIndex=1, SpellVisualID_1=HM_KNEEL, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

pillar_213022 = _self_aura(
    213022, 'Prayer of the Champion', School.HOLY, HM_PRAYER_PILLAR, _ICON_DIVINE_SHIELD,
    'A pillar of Light.', 'A pillar of Light.',
    f'{_D11H}, HM2: the pillar of Light on Herod for his prayer (cast on himself, removed at his rising): the '
    'Ascension lightsjudgement pillar at 3 yd, SV 90563 (V\'s HM_PRAYER_PILLAR; never the stock Beam of Light SV '
    '12479, a 135 yd model). No effect.',
)

zeal_213023 = spell(
    id=213023, name='Zeal', school=School.HOLY, dispel=_DISPEL_NONE, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=ZEAL_PCT - 1,
               die_sides=1, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Zeal: a flat +5% damage done per stack, not a damage or heal value'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=ZEAL_PCT - 1,
               die_sides=1, implicit_target_a=TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_ZEAL,
    notes=f'{_D11H}, HM2b Zeal: one stack on Herod for every Garrison Trainee that reaches the pillar (it kneels and '
          'fades into the Light), six at most (HANDOFF section 10 add sizing C; DungeonKit::AddStacks, CumulativeAura '
          '6), for the rest of the fight: +5% damage done (every school) and +5% attack speed a stack (the engine '
          'multiplies by the stack count). His registry hits ignore caster modifiers, so it raises his melee only: '
          'the tank\'s and healer\'s work, a group failure capped at six. Not dispellable or stealable; removed on '
          'his death, evade and reset (D11H\'s OnEnd). Zeal 8191\'s SV 211 (V\'s HB_ZEAL), one play per stack.',
    raw_overrides=kit_raw('Zeal: damage and attack speed increased.',
                          'Damage done increased by $s1%. Attack speed increased by $s2%.', instant=True,
                          CumulativeAura=ZEAL_MAX, SpellVisualID_1=HB_ZEAL, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

fade_213024 = self_visual(
    213024, 'Into the Light', HB_RAVAGER_GLOW,
    f'{_D11H}, HM2a: a Garrison Trainee that reaches the pillar kneels and fades into the Light (cast on itself, '
    'triggered; it despawns 1.5 s later): Beacon of Light 53563\'s SV 11876 (V\'s HB_RAVAGER_GLOW, the '
    'beacon_of_light_impact). Look only.',
    icon=_ICON_BEACON, school=School.HOLY,
)

# --- HM3 Ravager's Beacon --------------------------------------------------------------------------------------------

glow_213025 = self_visual(
    213025, 'Ravager\'s Beacon', HB_RAVAGER_GLOW,
    f'{_D11H}, HM3: the planted axe blazing with Light, cast by the planted Ravager (300945) on itself every 4 s from '
    'his rising (a one-shot impact, replayed: V\'s rule for one-shot kits used as states): Beacon of Light 53563\'s SV '
    '11876 (V\'s HB_RAVAGER_GLOW). Look only.',
    icon=_ICON_BEACON, school=School.HOLY,
)

beam_look_213026 = spell(
    id=213026, name='Ravager\'s Beacon', school=School.HOLY, dispel=_DISPEL_NONE, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=BEAM_LOOK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_BEACON,
    notes=f'{_D11H}, HM3: a beam\'s look, a channel the end stalker of each beam (the wave 2 generic stalker 300958, '
          'moved to the beam\'s tip at every step by KT-SM TurningBeams) casts (triggered) on the planted Ravager, so '
          'the chain is drawn from the axe to the beam\'s end. Nothing in the spell does anything: the beam\'s hit is '
          'the registry Line of each step (213027). Not interruptible, no channel interrupt (the stalker moves), '
          'ignores LoS; the kit re-casts it when it is not channeling. The shipped Light Beam 52407\'s SV 11500 (V\'s '
          'HM_BEAM: chain 568 HealBeam, gold, the Malor precedent).',
    raw_overrides=kit_raw('A beam of Light from the planted axe.', 'Bound to Ravager\'s Beacon.', CastingTimeIndex=1,
                          InterruptFlags=0, ChannelInterruptFlags=0, PreventionType=0, SpellVisualID_1=HM_BEAM,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

beam_213027 = resolve_copy(
    213027, 'Ravager\'s Beacon', School.HOLY, 'The beam of Light sweeps the pit.',
    f'{_D11H}, HM3 Ravager\'s Beacon: two beams opposite each other from 3 yd off the planted axe to the pit\'s edge, '
    '4 yd wide, turning 30 degrees every 1.5 s (each next step marked 1.5 s ahead: KT-SM TurningBeams), the turn '
    'flipping at each Blades of Light: 45% of the reference row (heroic\'s hit: the build spec) and 1 Weakened, the '
    'tank row on the tank (registry tag 33). Copy of the mod-boss-mechanics resolve spell (Holy).',
    icon=_ICON_BEACON,
)

# --- HM1 Consecrated Hall --------------------------------------------------------------------------------------------

hall_213028 = spell(
    id=213028, name='Consecrated Hall', school=School.HOLY, dispel=_DISPEL_NONE, mechanic=0,
    attributes=ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=HALL_HUNDREDTHS - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CONSECRATION,
    notes=f'{_D11H}, HM1 Consecrated Hall: from his rising to his death the whole hall is consecrated: every 2 s Herod '
          'casts this (triggered) on every player of the fight, 4% of the reference row (2% a second; the tank row on '
          'the tank), Holy, unavoidable group damage, healer work, no Weakened. The percent in hundredths in the '
          'effect (heroic the same in EffectMiscValueB: the hard mode is heroic only); binds the kit\'s '
          'spell_dungeon_refflat_damage. Never missed (always hits, no active defense, cannot crit), ignores his '
          'modifiers (Zeal and Frenzy never raise it) and LoS. Registry: none (group damage, Green).',
    raw_overrides=kit_raw('The hall is consecrated.', instant=True, EffectMiscValueB_1=HALL_HUNDREDTHS,
                          DefenseType=_DEFENSE_MAGIC,
                          AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(hall_213028, 'spell_dungeon_refflat_damage')

hall_look_213029 = _self_aura(
    213029, 'Consecrated Hall', School.HOLY, HM_HALL, _ICON_CONSECRATION, 'The hall is consecrated.',
    'The hall is consecrated.',
    f'{_D11H}, HM1: the consecrated floor over the whole hall from his rising, an aura the planted Ravager (300945, at '
    'the pit\'s center) casts on itself: SV 90562 (V\'s HM_HALL, the stock holyzone at the hall\'s radius 25.5 yd; '
    'never SV 14914 or 5600). No effect (the ticks are 213028).',
)
