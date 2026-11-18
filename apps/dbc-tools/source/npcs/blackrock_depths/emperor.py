"""
Blackrock Depths build WP-D23: Emperor Dagran Thaurissan (9019), Princess Moira Bronzebeard (8929) and the High
Priestess of Thaurissan (10076); the Imperial Guard 300843 and the Twilight's Hammer Ambassador 300844
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 / s3.5 row D23, s3.6, s3.8, s3.10, s7 #19;
build spec docs/dungeons/blackrock-depths-4-imperial-seat.md "Emperor Dagran Thaurissan" EM1-EM10, rulings 77-80, 88,
90, 91). WP-D23 owns this file (its spells: kSpellsEmperor 211610-211659 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h only; EmperorLogic.h names the same ids). The engine side is
src/BlackrockDepths/boss_emperor_dagran_thaurissan_rework.cpp (Dagran, the guard, the Ambassador) and
boss_moira_bronzebeard_rework.cpp (Moira and the Priestess, one AI); the texts are
data/sql/updates/pending_db_world/rev_emperor_blackrock_depths.sql. The hard mode (the Avatar of Ragnaros) is D24's
emperor_hard_mode.py, on D23's hooks (EmperorFight.h).

Wave 2: the wave switch (_common.py BIND_WAVE_2) holds back what rebinds a STOCK unit (the three bosses' columns) and
the two adds' ScriptName (an unbound name logs "not assigned" at boot). The new entries, their models and the spells
are declared either way: nothing spawns them until the C++ binds.

- 9019 Dagran: boss_emperor_dagran_thaurissan_rework, SmartAI off (he has none: live SELECT 2026-11-17), 160k normal
  (HealthModifier 59.281 on the level 56 warrior base 2,699), the kit's stun set 1972 (the stock -251 immunity to every
  school but Physical belonged to the retired Avatar of Flame), INSTANCE_BIND, DamageModifier 3.5 (the stock base
  value; the live 7.25 is a leftover). Heroic 220k is WP-H's override.
- 8929 Moira / 10076 the High Priestess: boss_moira_bronzebeard_rework on both, 50k normal (27.322 on the level 55 mage
  base 1,830), 1972, no INSTANCE_BIND (no credit of their own), DamageModifier 3.5 / 7.5 (stock). Heroic 70k is WP-H's.
  Their shared lootid 8929 is emptied into Dagran's list by L-2 (not here).
- 300843 Imperial Guard: level 55 elite warrior (rank 1), 8,000 health (3.060443 on the warrior base 2,614), the
  Anvilrage Guardsman look (CDI 8750, VR gap 37), DamageModifier 2.5 (this WP's default, gap 36: about 4% of the level
  56 tank row a swing; designer question), no loot, no XP, C++ npc_brd_imperial_guard. Heroic 12k: difficulty_entry_1
  310417 (WP-H's lock line).
- 300844 Twilight's Hammer Ambassador: level 55 elite paladin (rank 1), 10,000 health (4.782400 on the paladin base
  2,091), the human male look (CDI 8778), DamageModifier 1.0 (it never swings: it channels), no loot, no XP, C++
  npc_brd_twilight_ambassador. Heroic only (the normal row is never summoned); heroic 10k: difficulty_entry_1 310418.
  Its own entry: the room's ten stock 8915 Ambassadors stay trash.

Spells (looks from ._visuals, WP-V-2's EM_ / MO_ picks, or the copied stock spell's own SpellVisual where V-2 named
none: shared-file request in the report; every look unconfirmed until seen in game):

  211610  Hand of Thaurissan     EM1 the copy of 17492: 30 yd, 12% / 15% Fire and a 2 s stun (was 5 s), any player
  211611  Shadow Word: Nemesis   EM2 Moira's 8 s channel into Dagran (the gold beam, SV 11500), not interruptible
  211612  Radiant Burn           EM2 a blocker's tick: 5% / 8% Holy
  211613  Shadow Word: Nemesis   EM2 an open tick's heal on each of them (1.5% of their health, exact from the script)
  211614  Mind Blast             EM4 the copy of 15587: Moira's 1.5 s cast, 10% / 12% Shadow, interruptible
  211615  Shadow Word: Necrosis  EM5 (H) 6% a second for 10 s, Shadow, Magic (the dispel is expected)
  211616  Twilight Tether        EM6 (H) the Ambassador's channel into Dagran (SV 12480)
  211617  Twilight Burn          EM6 (H) a tether blocker's tick: 3% Shadow
  211618  Twilight Tether        EM6 (H) an open tether tick's heal on Dagran (0.5%, exact)
  211619  Flamestrike            EM7 (H) a circle's hit: 6 yd, 45% + Weakened (resolve copy, Fire)
  211620  Flamestrike            EM7 (H) the burning ground's tick: 8% a second for 4 s (resolve copy, Fire)
  211621  Flamestrike            look: Dagran's casting hands as a round lands (SV 10383)
  211622  Flamestrike            look: the 6 yd burning ground, a stalker's aura for 4 s (SV 90608)
  211623  Avatar of Flame        EM8 the enrage: +25% damage done, +60% size (no immunity any more)
  211624  Flames                 EM8 the proc on his melee hits: 4% / 5% Fire on his victim
  211625  Firestorm              EM9 a circle's hit: 6 yd, 25% / 40% + Weakened (resolve copy, Fire)
  211626  Firestorm              look: Massive Eruption at a circle (SV 889)
  211627  Hammer Slam            EM10 the 1.5 s wind-up bar (Physical; the Volcanic Hammer look, SV 395)
  211628  Hammer Slam            EM10 the cone's hit: 40% / 60%, no Weakened (resolve copy, Physical)
  211629  Hammer Slam            look: the ground crack in the cone (SV 8083)
  211630  Fire Cage              the hard mode's cage at Moira's base (SV 90652, minted by V-2)
  211631  Fire Cage              ... and its flame whirl (Fire Shield's CycloneFire state, SV 8581)
  211632-211659 spare.

Retired (rule 15: copies in the slice, never the shared ids): the stock Hand of Thaurissan 17492 (its spell_dbc
override stays for anyone else), Avatar of Flame 15636 (its immunity is gone), Mind Blast 15587; Moira's Heal 15586 and
Renew 8362, the Priestess's Shadow Word: Pain 15654 and Shadow Bolt 15537 are no longer cast.
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
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    EM_AVATAR_OF_FLAME,
    EM_FLAMES,
    EM_HAND_OF_THAURISSAN,
    MO_MIND_BLAST,
    MO_NECROSIS,
    DISPLAY_IMPERIAL_GUARD,
    DISPLAY_TWILIGHT_AMBASSADOR,
    EM_FIRESTORM,
    EM_FLAMESTRIKE_BURN,
    EM_FLAMESTRIKE_CAST,
    EM_HAMMER_SLAM_CRACK,
    EM_HAMMER_SLAM_WINDUP,
    EM_NEMESIS_BEAM,
    EM_RADIANT_BURN,
    EM_TWILIGHT_TETHER,
    MO_FIRE_CAGE,
    MO_FIRE_CAGE_WHIRL,
)

_D23 = 'Blackrock Depths build WP-D23 (Emperor Dagran Thaurissan and Princess Moira)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage / spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')
_SCRIPT_EXACT = 'Blackrock Depths: an exact amount from the script (CastCustomSpell base point 0)'

# --- the bosses (held back until wave 2 binds: _common.py BIND_WAVE_2) ----------------------------------------------

DAGRAN_COLUMNS = boss_columns('boss_emperor_dagran_thaurissan_rework', 59.281, damage_modifier=3.5)
MOIRA_COLUMNS = boss_columns('boss_moira_bronzebeard_rework', 27.322, damage_modifier=3.5, instance_bind=False)
PRIESTESS_COLUMNS = boss_columns('boss_moira_bronzebeard_rework', 27.322, damage_modifier=7.5,
                                 instance_bind=False)

if BIND_WAVE_2:
    creature_template_columns(9019, **DAGRAN_COLUMNS)
    creature_template_columns(8929, **MOIRA_COLUMNS)
    creature_template_columns(10076, **PRIESTESS_COLUMNS)

# --- constants (EmperorLogic.h; lib/test_blackrock_depths_emperor.py pins each against the header) --------------------

HAND = (1200, 1500)                 # kHandPct 12 / 15 (hundredths)
HAND_STUN_MS = 2000                 # kHandStunMs
HAND_RANGE = 30.0                   # kHandRangeYd
NEMESIS_CHANNEL_MS = 8000           # kNemesisChannelMs
RADIANT_BURN = (500, 800)           # kRadiantBurnPct 5 / 8
MIND_BLAST = (1000, 1200)           # kMindBlastPct 10 / 12
MIND_BLAST_CAST_MS = 1500           # kMindBlastCastMs
MIND_BLAST_RANGE = 30.0             # kMindBlastRangeYd
NECROSIS_TICK = (600, 600)          # kNecrosisTickPct 6 (heroic only: both columns hold the heroic value)
NECROSIS_TICK_MS = 1000             # kNecrosisTickMs
NECROSIS_MS = 10000                 # kNecrosisMs
TETHER_CHANNEL_MS = 60000           # re-cast by the Ambassador when it ends or breaks
TETHER_RANGE = 40.0                 # the channel's reach (the AI walks again past kTetherRangeYd 35)
TETHER_BURN = (300, 300)            # kTetherBurnPct 3 (heroic only)
FLAMES = (400, 500)                 # kFlamesPct 4 / 5
ENRAGE_DAMAGE_PCT = 25              # kEnrageDamagePct
ENRAGE_SCALE_PCT = 60               # kEnrageScalePct
HAMMER_SLAM_CAST_MS = 1500          # kHammerSlamCastMs

LEVEL = 55                          # the adds: the section's level (Dagran 56, Moira 55)
WARRIOR_55_BASE = 2614              # creature_classlevelstats basehp0, class 1 level 55 (live 2026-11-17)
PALADIN_55_BASE = 2091              # class 2 level 55
GUARD_HEALTH, AMBASSADOR_HEALTH = 8_000, 10_000     # kGuardHealth (normal), kAmbassadorHealth
GUARD_DAMAGE_MODIFIER, AMBASSADOR_DAMAGE_MODIFIER = 2.5, 1.0
GUARD, AMBASSADOR = 300843, 300844
GUARD_HEROIC, AMBASSADOR_HEROIC = 310417, 310418    # WP-H's lock lines (STAGE-H-REPORT s3)

# The scripts the C++ registers (boss_emperor_dagran_thaurissan_rework.cpp AddSC_): bound by data only once wave 2 is.
ADD_SCRIPTS = {GUARD: 'npc_brd_imperial_guard', AMBASSADOR: 'npc_brd_twilight_ambassador'}

_FLAGS_EXTRA_NO_XP = 0x40
_ATTR1_IS_CHANNELED = 0x00000004
_INTERRUPT_FLAGS_KICKABLE = 15
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_DISPEL_MAGIC = 1
_MECHANIC_STUN = 12
_SCHOOL_MASK_ALL = 127
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_HAND = 12                     # Hand of Thaurissan 17492
_ICON_HOLY_FIRE = 156               # Holy Fire 15261
_ICON_MIND_BLAST = 95               # Mind Blast 15587
_ICON_SHADOW_WORD_PAIN = 234        # Shadow Word: Pain 15654
_ICON_TWILIGHT = 2901               # Twilight Channel 57797
_ICON_FLAMESTRIKE = 37              # Flamestrike 2120
_ICON_AVATAR = 937                  # Avatar of Flame 15636
_ICON_FLAMES = 18                   # Flames 15643
_ICON_ERUPTION = 1137               # Massive Eruption 20483
_ICON_HAMMER = 140                  # Volcanic Hammer 16984

# The scripted hits: no redirection or reflection, no crit, always hits, ignores the caster's modifiers (a percent of
# the reference row).
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
    AttributesEx2=ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
)


def _health_modifier(target: int, base: int) -> float:
    """The HealthModifier that makes ceil(base x modifier) = target: the exact quotient cut to six digits from below
    (a rounded-up one would ceil to target + 1)."""
    return math.floor(target / base * 1_000_000) / 1_000_000


def _hit(spell_id: int, name: str, school: School, pct: tuple, notes: str, *, icon: int, visual: int = 0,
         desc: str = ''):
    """A triggered single-target hit whose damage is a percent of the target's reference row (normal hundredths in
    the effect, heroic in EffectMiscValueB), on the kit's spell_dungeon_refflat_damage."""
    raw = kit_raw(desc, instant=True, EffectMiscValueB_1=pct[1], DefenseType=_DEFENSE_MAGIC, **_HIT_ATTRS)
    if visual:
        raw['SpellVisualID_1'] = visual
    s = spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct[0] - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )
    scripted_by(s, 'spell_dungeon_refflat_damage')
    return s


def _heal(spell_id: int, name: str, school: School, icon: int, desc: str, notes: str):
    """An exact heal from the script (CastCustomSpell base point 0, triggered) on the named ally (Dagran, or Moira on
    herself). Ignores the caster's modifiers; a healing reduction on the target (Mortal Strike) cuts it."""
    return spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                        potency_excluded=_SCRIPT_EXACT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _channel(spell_id: int, name: str, school: School, duration_ms: int, range_yards: float, visual: int, icon: int,
             desc: str, aura_desc: str, notes: str):
    """A channel into an ally that does nothing itself (a DUMMY aura on the target and the beam between the two): the
    AI judges the ticks. Not interruptible, damage never breaks it (InterruptFlags 0, ChannelInterruptFlags 0)."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=range_yards, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1, InterruptFlags=0, ChannelInterruptFlags=0,
                              PreventionType=0, SpellVisualID_1=visual,
                              AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, icon: int, school: School = School.FIRE):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), triggered."""
    return spell(
        id=spell_id, name=name, school=school, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _state_aura(spell_id: int, name: str, visual: int, duration_ms: int, notes: str, icon: int):
    """A hidden DUMMY aura a unit casts on itself for its look (a state kit needs an aura to play; not passive: a
    passive aura is never sent to the client). `duration_ms` -1: until removed (or the stalker goes)."""
    return spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              CastingTimeIndex=1),
    )


# --- the adds: 300843 Imperial Guard, 300844 Twilight's Hammer Ambassador ---------------------------------------------
# The entries are written as numbers: source/world/dungeons/blackrock_depths.py finds the declared kit adds by the
# pattern `creature_template(<entry>, ...)` (WP-H) and gives them their heroic health.

imperial_guard_300843 = creature_template(300843, 'Imperial Guard', **{
    **KIT_CREATURE, 'minlevel': LEVEL, 'maxlevel': LEVEL, 'rank': 1, 'unit_class': 1, 'unit_flags': 0,
    'HealthModifier': _health_modifier(GUARD_HEALTH, WARRIOR_55_BASE), 'DamageModifier': GUARD_DAMAGE_MODIFIER,
    'BaseAttackTime': 2000, 'speed_run': 1.14286, 'detection_range': 20.0, 'CreatureImmunitiesId': 0,
    'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'ScriptName': ADD_SCRIPTS[GUARD] if BIND_WAVE_2 else '', 'difficulty_entry_1': GUARD_HEROIC,
})
creature_model(GUARD, display_id=DISPLAY_IMPERIAL_GUARD)

twilight_ambassador_300844 = creature_template(300844, 'Twilight\'s Hammer Ambassador', **{
    **KIT_CREATURE, 'minlevel': LEVEL, 'maxlevel': LEVEL, 'rank': 1, 'unit_class': 2, 'unit_flags': 0,
    'HealthModifier': _health_modifier(AMBASSADOR_HEALTH, PALADIN_55_BASE),
    'DamageModifier': AMBASSADOR_DAMAGE_MODIFIER, 'BaseAttackTime': 2000, 'speed_run': 1.14286,
    'detection_range': 0.0, 'CreatureImmunitiesId': 0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
    'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'ScriptName': ADD_SCRIPTS[AMBASSADOR] if BIND_WAVE_2 else '', 'difficulty_entry_1': AMBASSADOR_HEROIC,
})
creature_model(AMBASSADOR, display_id=DISPLAY_TWILIGHT_AMBASSADOR)

# --- EM1 Hand of Thaurissan -------------------------------------------------------------------------------------------

hand_of_thaurissan_211610 = spell(
    id=211610, name='Hand of Thaurissan', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=HAND_RANGE, duration_ms=HAND_STUN_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=HAND[0] - 1, die_sides=1,
               implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0, die_sides=0,
               implicit_target_a=TARGET_UNIT_TARGET_ENEMY, mechanic=_MECHANIC_STUN),
    ],
    spell_icon_id=_ICON_HAND,
    notes=f'{_D23}, EM1: the stock Hand of Thaurissan 17492 (OVERRIDE in spell_dbc: 30 yd, 240 Fire and a 5 s stun) '
          'kept and rescaled (rule 15: a copy in the slice, never the shared id): the stun drops to 2 s (ruling 78), '
          'the target is any player in 30 yd and in his sight, the tank included (rulings 88, 90: the healer watches '
          'for it). He casts it at 4 s, then every 12-15 s, in the court and the enrage. The hit is "stock rescaled" '
          '(gap 36): 12% (heroic 15%) of the target\'s reference row, the tank row on the tank (hundredths 1200, '
          'EffectMiscValueB 1500; designer question). Cannot crit, always hits, ignores his modifiers (the enrage\'s '
          '+25% too). The stock SV 143. The stun is removed from every player when the fight ends.',
    raw_overrides=kit_raw('Strikes the target with fire and stuns it for $d.', 'Stunned.', instant=True,
                          SpellVisualID_1=EM_HAND_OF_THAURISSAN, EffectMiscValueB_1=HAND[1],
                          DefenseType=_DEFENSE_MAGIC, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, **_HIT_ATTRS),
)
scripted_by(hand_of_thaurissan_211610, 'spell_dungeon_refflat_damage')

# --- EM2 Shadow Word: Nemesis (Moira) ---------------------------------------------------------------------------------

nemesis_211611 = _channel(
    211611, 'Shadow Word: Nemesis', School.HOLY, NEMESIS_CHANNEL_MS, 100.0, EM_NEMESIS_BEAM, _ICON_HOLY_FIRE,
    'Channels holy fire into the Emperor, healing both. Anyone standing in the beam burns instead.',
    'Fed by Moira\'s holy fire.',
    f'{_D23}, EM2: Moira\'s channel into Dagran, first at 12 s, then every 25 s (heroic 20 s), 8 s (emote line 1), not '
    'interruptible (InterruptFlags 0, ChannelInterruptFlags 0; she is stun immune, 1972). Nothing in the spell does '
    'anything: a DUMMY aura on him and the beam (WotLK Prologue Light Beam 52407\'s SV 11500, the gold HealBeam chain; '
    'NEVER Holy Channeling SV 11274 or Penance SV 10980, which draw no beam). His AI judges a tick a second: every '
    'player on the 2 yd line between them takes Radiant Burn (211612); nobody on it, both heal 1.5% of their health '
    '(211613). Holy school: a kick on her Shadow Mind Blast locks Shadow, never this must-play channel (rule 5). '
    'Ignores LoS.',
)

radiant_burn_211612 = _hit(
    211612, 'Radiant Burn', School.HOLY, RADIANT_BURN,
    f'{_D23}, EM2: a Nemesis tick on every player standing in the beam (Moira casts it, triggered): 5% (heroic 8%) of '
    'the target\'s row, Holy, no Weakened (the spec: blocking is the job, the burn its cost; blockers may swap). Holy '
    'Fire 15261\'s damage flash (SV 3400).',
    icon=_ICON_HOLY_FIRE, visual=EM_RADIANT_BURN, desc='Holy fire burns the one who blocks the beam.',
)

nemesis_heal_211613 = _heal(
    211613, 'Shadow Word: Nemesis', School.HOLY, _ICON_HOLY_FIRE, 'Moira\'s holy fire mends them.',
    f'{_D23}, EM2: an open Nemesis tick (nobody in the beam): Moira casts it on Dagran and on herself, exact from the '
    'script, 1.5% of each one\'s maximum health (160k: 2,400; Moira 50k: 750); 8 open ticks heal 12% (S4 "Failing '
    'path"). No look of its own (the beam is the look).',
)

# --- EM4 Mind Blast (Moira) -------------------------------------------------------------------------------------------

mind_blast_211614 = spell(
    id=211614, name='Mind Blast', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=MIND_BLAST_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=MIND_BLAST_RANGE,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=MIND_BLAST[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_MIND_BLAST,
    notes=f'{_D23}, EM4: the stock Mind Blast 15587 (1.5 s, 139-161 Shadow) kept and rescaled (rule 15: a copy): '
          'Moira\'s cast on her target (her victim) in 30 yd, 8 s in, then every 14-18 s (stock). "Stock rescaled" '
          '(gap 36): 10% (heroic 12%) of the target\'s row, the tank row on a tank (designer question). Interruptible '
          '(InterruptFlags 15, PreventionType silence): the descriptor\'s interrupt list, a reward. Ignores her '
          'modifiers. The stock SV 3057.',
    raw_overrides=kit_raw('Blasts the target for Shadow damage.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                          SpellVisualID_1=MO_MIND_BLAST, EffectMiscValueB_1=MIND_BLAST[1],
                          AttributesEx=ATTR1_NO_REDIRECTION, AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(mind_blast_211614, 'spell_dungeon_refflat_damage')

# --- EM5 Shadow Word: Necrosis (Moira, heroic) ------------------------------------------------------------------------

necrosis_211615 = spell(
    id=211615, name='Shadow Word: Necrosis', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=NECROSIS_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=NECROSIS_TICK[0],
                    die_sides=0, amplitude=NECROSIS_TICK_MS, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_SHADOW_WORD_PAIN,
    notes=f'{_D23}, EM5 (heroic): Moira casts it (triggered, so a Nemesis channel goes on) on the player Dagran\'s AI '
          'names, 8 s in, then every 15 s, in the court: any player, the tank included (ruling 88). 6% of the '
          'target\'s row a second for 10 s (60% undispelled), Shadow, Magic: the dispel list (priority 2, expected). '
          'Both hundredths columns hold 6% (heroic only). Ignores her modifiers; leaves with the map. Shadow Word: '
          'Pain 15654\'s SV 71.',
    raw_overrides=kit_raw('Shadow damage every $t1 sec.', 'Taking Shadow damage every $t1 sec.', instant=True,
                          InterruptFlags=0, DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=NECROSIS_TICK[1],
                          SpellVisualID_1=MO_NECROSIS, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(necrosis_211615, 'spell_dungeon_refflat_periodic')

# --- EM6 the Twilight Tether (the Ambassador, heroic) -----------------------------------------------------------------

twilight_tether_211616 = _channel(
    211616, 'Twilight Tether', School.SHADOW, TETHER_CHANNEL_MS, TETHER_RANGE, EM_TWILIGHT_TETHER, _ICON_TWILIGHT,
    'Channels twilight into the Emperor, healing him. Anyone standing in the beam burns instead.',
    'Fed by the Twilight\'s Hammer.',
    f'{_D23}, EM6 (heroic, from 70%): a Twilight\'s Hammer Ambassador channels it into Dagran from its stand (20 yd '
    'from him) until it dies, re-cast when it ends or breaks. A DUMMY aura and the thin dark beam (Twilight Channel '
    '57797\'s SV 12480). Its AI judges a tick a second: a player on the 2 yd line takes Twilight Burn (211617); '
    'nobody, Dagran heals 0.5% of his health (211618). Killing the Ambassador is the answer (kill order first).',
)

twilight_burn_211617 = _hit(
    211617, 'Twilight Burn', School.SHADOW, TETHER_BURN,
    f'{_D23}, EM6 (heroic): a tether tick on every player standing in the Ambassador\'s beam (the Ambassador casts it, '
    'triggered): 3% of the target\'s row, Shadow, no Weakened. Both hundredths columns hold 3% (heroic only). No look '
    'of its own (the beam is the look).',
    icon=_ICON_TWILIGHT, desc='Twilight burns the one who blocks the tether.',
)

tether_heal_211618 = _heal(
    211618, 'Twilight Tether', School.SHADOW, _ICON_TWILIGHT, 'Twilight mends the Emperor.',
    f'{_D23}, EM6 (heroic): an open tether tick: the Ambassador casts it on Dagran, exact from the script, 0.5% of his '
    'maximum health (heroic 220k: 1,100).',
)

# --- EM7 Flamestrike (heroic) -----------------------------------------------------------------------------------------

flamestrike_211619 = resolve_copy(
    211619, 'Flamestrike', School.FIRE, 'Fire falls from above.',
    f'{_D23}, EM7 (heroic, from 40% of Dagran\'s health): every 12 s a 6 yd circle under every player (the tank too) '
    'and at 3 random floor spots of the room, a 2 s ring, then 45% of the row and 1 Weakened (registry tag 1), the '
    'tank row on the tank. A copy of the mod-boss-mechanics resolve spell with the Fire school.',
    icon=_ICON_FLAMESTRIKE,
)

flamestrike_burn_211620 = resolve_copy(
    211620, 'Flamestrike', School.FIRE, 'The ground burns.',
    f'{_D23}, EM7 (heroic): a tick of a circle\'s burning ground, a second after the impact, for 4 s: 8% of the row '
    'each (registry tag 2; no Weakened, no slow rider). A copy of the mod-boss-mechanics resolve spell with the Fire '
    'school.',
    icon=_ICON_FLAMESTRIKE,
)

flamestrike_look_211621 = self_visual(
    211621, 'Flamestrike', EM_FLAMESTRIKE_CAST,
    f'{_D23}, EM7 (heroic): Dagran\'s casting hands as a round of circles is placed (Flamestrike 2120\'s SV 10383; its '
    '23 yd PersistentArea is not the burn). Look only.',
    icon=_ICON_FLAMESTRIKE, school=School.FIRE,
)

flamestrike_ground_211622 = _state_aura(
    211622, 'Flamestrike', EM_FLAMESTRIKE_BURN, -1,
    f'{_D23}, EM7 (heroic): the burning ground\'s look: a stalker (300796) at a circle casts it on itself as the '
    'impact lands and despawns 4 s later (the burn\'s life): the shipped 6 yd lava pool state (SV 90608, Blackrock '
    'Spire\'s ladder), under the registry\'s 6 yd marker. Look only.',
    _ICON_FLAMESTRIKE,
)

# --- EM8 Avatar of Flame (the enrage) ---------------------------------------------------------------------------------

avatar_of_flame_211623 = spell(
    id=211623, name='Avatar of Flame', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=ENRAGE_DAMAGE_PCT,
               die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Avatar of Flame: a flat +25% damage done, not a damage or heal value'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SCALE, base_points=ENRAGE_SCALE_PCT, die_sides=0,
               implicit_target_a=TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_AVATAR,
    notes=f'{_D23}, EM8: the standard enrage (ruling 78), cast on himself (triggered) when Moira dies, for the rest of '
          'the fight (yell line 9): the stock Avatar of Flame 15636 without its immunity (aura 39 every school but '
          'Physical is gone): +25% damage done (his melee; the reference-sized hits ignore caster modifiers), +60% '
          'size (the stock look); the Flames proc (211624) is his AI\'s, on each melee hit. Not dispellable, not '
          'purgeable; removed on his evade and reset. The stock SV 46.',
    raw_overrides=kit_raw('The Emperor burns with the fury of Ragnaros.', 'Damage done increased by $s1%.',
                          instant=True, SpellVisualID_1=EM_AVATAR_OF_FLAME, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

flames_211624 = _hit(
    211624, 'Flames', School.FIRE, FLAMES,
    f'{_D23}, EM8: the Avatar of Flame proc: each of his melee hits while enraged (his AI\'s DamageDealt), a Fire hit '
    'on his victim: "stock rescaled" (the stock Flames 15643 dealt 170-230), 4% (heroic 5%) of the row, the tank row '
    'on the tank (designer question). Flames 15643\'s SV 2519.',
    icon=_ICON_FLAMES, visual=EM_FLAMES, desc='Fire burns the Emperor\'s target.',
)

# --- EM9 Firestorm, EM10 Hammer Slam (the enrage) ---------------------------------------------------------------------

firestorm_211625 = resolve_copy(
    211625, 'Firestorm', School.FIRE, 'The ground erupts.',
    f'{_D23}, EM9: from 5 s after the enrage, every 12 s (heroic 10 s; in the hard mode\'s Avatar phase it continues '
    'on heroic values): 3 (heroic 4) 6 yd circles under random players (the tank too), a 2 s marker, then 25% (heroic '
    '40%) of the row and 1 Weakened (registry tag 3), the tank row on the tank. A copy of the mod-boss-mechanics '
    'resolve spell with the Fire school.',
    icon=_ICON_ERUPTION,
)

firestorm_look_211626 = _look_at_point(
    211626, 'Firestorm', EM_FIRESTORM,
    f'{_D23}, EM9: the eruption at a circle as it lands (Dagran casts it, triggered): Massive Eruption 20483\'s SV 889 '
    '(NEVER Volcanic Geyser SV 9466, blue fire). Look only.',
    icon=_ICON_ERUPTION,
)

hammer_slam_cast_211627 = cast_bar(
    211627, 'Hammer Slam', HAMMER_SLAM_CAST_MS, 'The Emperor raises his hammer.',
    f'{_D23}, EM10: the 1.5 s wind-up (boss emote 13), from 8 s after the enrage, every 15 s. No effect: the '
    'registry\'s 10 yd frontal cone (211628) owns the hit. Not interruptible (cast_bar). Physical: he has no kickable '
    'cast, and Moira\'s kickable Mind Blast is Shadow (rule 5). Volcanic Hammer 16984\'s SV 395 (the hammer in hand).',
    icon=_ICON_HAMMER, visual=EM_HAMMER_SLAM_WINDUP, school=School.NORMAL,
)

hammer_slam_211628 = resolve_copy(
    211628, 'Hammer Slam', School.NORMAL, 'The hammer crushes everything in front of the Emperor.',
    f'{_D23}, EM10: the cone\'s hit as the wind-up ends: 10 yd, 90 degrees in front of him (the angle is unset in the '
    'spec: designer question), the tank exempt (a Frontal), everyone else in it 40% (heroic 60%) of the row, no '
    'Weakened on any difficulty (the heroic hit is over 50%: its own penalty; wrap-up fix). Registry tag 4. A copy of '
    'the mod-boss-mechanics resolve spell with the Physical school.',
    icon=_ICON_HAMMER,
)

hammer_slam_look_211629 = _look_at_point(
    211629, 'Hammer Slam', EM_HAMMER_SLAM_CRACK,
    f'{_D23}, EM10: the ground crack in the cone as it lands (Dagran casts it, triggered, 5 yd in front of him): the '
    'Ground Slam crack SV 8083. Look only.',
    icon=_ICON_HAMMER, school=School.NORMAL,
)

# --- the fire cage on Moira (the hard mode's transition, EmperorFight.h step 2) ---------------------------------------

moira_cage_211630 = _state_aura(
    211630, 'Fire Cage', MO_FIRE_CAGE, -1,
    f'{_D23}, the hard mode (D24, Ragnaros Awakens, heroic): Moira casts it on herself (triggered) as Dagran rises, '
    'and it stays until the cage breaks (his death, an evade, a wipe): the ring of fire at her base, V-2\'s minted row '
    'SV 90652 (the stock FlameCircleEffect at 0.64). She is not selectable, passive and idle meanwhile (the '
    'designer\'s exception, ruling 77). Look only.',
    _ICON_AVATAR,
)

moira_cage_whirl_211631 = _state_aura(
    211631, 'Fire Cage', MO_FIRE_CAGE_WHIRL, -1,
    f'{_D23}, the hard mode: the cage\'s flame whirl beside the ring (Fire Shield 35265\'s CycloneFire state, SV '
    '8581), cast with 211630 and removed with it. Look only.',
    _ICON_AVATAR,
)
