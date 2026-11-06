"""
Deadmines Pilot WP-B3: Sneed's Shredder and Sneed (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.4 rows
SN, s3.5 row B3; build spec docs/dungeons/deadmines-rework.md "Sneed's Shredder and Sneed"). WP-B3 owns this file (its
spells: 205240-205269 only).

- 642 Sneed's Shredder: bound to boss_sneeds_shredder_rework (SmartAI off; its patrol 792230 is creature_addon data
  and stays), normal 8.5k (HealthModifier 17.5).
- 643 Sneed: bound to boss_sneed_rework (SmartAI off), normal 5.7k (HealthModifier 11.7).
Both take the new stun immunity set (handoff s7 #5); heroic 220k / 142k are deadmines.py's overrides.

Spells (modules/mod-dungeon-bosses/src/Deadmines/SneedLogic.h `SneedSpells` names the same ids):

  205240  Saw Spin              SN1 / SN12: 2 s cast bar (Shredder, then Sneed's Salvaged Saw), SV 12050 (Sawblade)
  205241  Splinter Spray        SN2: 2 s cast bar, SV 11064 (Steam Blast 50375: the steam hands as it charges)
  205242  Runaway               SN3: 2 s cast bar, SV 10109 (Electrical Overload)
  205243  Emergency Repairs     SN7 normal: 6 s self channel, interruptible (kick or silence), SV 10040 (Self Repair)
  205244  Emergency Repairs     SN7 heroic: 4 s
  205245  Overload              SN9: 3 s cast bar on the wreck (sparks), SV 11347 (Overload 51743)
  205246  Self Destruct         SN9: the blast on the wreck, visual only, SV 1463 (Self Destruct 9874)
  205247  Tazer                 SN5 normal: 2 s cast, Nature, chain of 3; spell_dm_sneed_tazer sets 20/14/10%
  205248  Tazer                 SN5 heroic: chain of 4, 35/25/18/12%
  205249  Saw Boomerang         SN6: 2 s cast bar
  205250  Saw Boomerang         SN6: the blade's missile to the far end (visual), SV 8306 (Throw Saw Blade 48984)
  205251  Cluster Bomb          SN10: the lobbed bomb (missile visual), SV 3819 (Throw Bomb 40160)
  205252  Cluster Bomb          SN10 / SN11: a blast at a point (visual), SV 148 (Bomb 8858, stock dynamite)
  205253  Splinter Spray        SN2: the tank's hit, 30% of tank reference health, Physical
                                (spell_dm_sneed_splinter_tank)
  205254  Broken Down           the wreck's smoke (SV 2718, Smoke Aura Visual 12898); the descriptor reads it
  205255  Malfunction           the visual with each Haywire emote, SV 2956 (Malfunction 13319)
  205256  Saw Spin              SN1 / SN12 hit: copy of the registry resolve spell, Physical
  205257  Splinter Spray        SN2 hit (non-tanks): resolve copy, Physical, SV SPLINTER_SPRAY_SPELLVISUAL
  205258  Runaway               SN3 hit: resolve copy, Physical
  205259  Saw Boomerang         SN6 hit (each pass): resolve copy, Physical
  205260  Wreck Overload        SN9 hit: resolve copy, Fire
  205261  Cluster Bomb          SN10 / SN11 hit: resolve copy, Fire
  205262-205269 spare.

Every damage number is a percent of reference health: the registry's Damage(pct) through the resolve copies, Tazer and
the tank's Splinter Spray through DeadminesKit::RefFlat in their SpellScripts. All carry
SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (STAGE-X report): the heroic number is the heroic row, never DD-scaled (custom
ids). Removed stock spells: Terrify 7399, Distracting Pain 3603, Disarm 6713 (their SmartAI rows go in WP-B3's SQL).
Eject Sneed 5141 is not cast: the script summons Sneed itself (a corpse that stays for his loot, his threat list
copied) and plays 5141's SpellVisual 148.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    TARGET_UNIT_CASTER,
    TEXT_MASKS,
)

creature_template_columns(
    642, ScriptName='boss_sneeds_shredder_rework', AIName='', HealthModifier=17.5,
    CreatureImmunitiesId=IMMUNITY_BOSS_STUN,
)
creature_template_columns(
    643, ScriptName='boss_sneed_rework', AIName='', HealthModifier=11.7, CreatureImmunitiesId=IMMUNITY_BOSS_STUN,
)

# Splinter Spray's look (handoff s3.10 gap 2, s7 #9). The cast bar (205241) keeps Steam Blast 50375's stock
# SpellVisual 11064 (its steam hands play as the PrecastKit on the Shredder). WP-V's 90344 (Steam Blast + the Ascension
# wood-chip impact `ifx_element_wood_hit.m2` on the ImpactKit) goes on the spells that land on players: the
# non-tanks' resolve copy (205257, an instant cast per target, so the ImpactKit plays on each player hit) and the
# tank's hit (205253). WP-F, from R2 N-3: on the self-cast bar the chips played on the Shredder.
_SV_STEAM_BLAST = 11064
SPLINTER_SPRAY_SPELLVISUAL = 90344  # WP-V: Steam Blast + Ascension wood-chip impact (stock fallback 11064)

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_DEST = 87

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_IS_SELF_CHANNELED = 0x00000040
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

_INTERRUPT_FLAGS_CAST = 15          # movement | pushback | interrupt | autoattack: a kick stops the cast
_CHANNEL_INTERRUPT_FLAG_INTERRUPT = 0x08
_PREVENTION_SILENCE = 1

# Stock icons and visuals (DM "Visual sources", Spell.dbc 3.3.5). Copied, never cast.
_ICON_SAWBLADE = 2238       # Sawblade 54904
_ICON_STEAM = 1197          # Steam Blast 50375
_ICON_OVERLOAD = 122        # Electrical Overload 45336
_ICON_REPAIR = 2539         # Self Repair 44994
_ICON_SPARKS = 2120         # Overload 51743
_ICON_FIRE = 37             # Self Destruct 9874, Bomb 8858
_ICON_LIGHTNING = 165       # Chain Lightning 421
_ICON_THROW_SAW = 2949      # Throw Saw Blade 48984
_ICON_BOMB = 1696           # Throw Bomb 40160
_ICON_SMOKE = 31            # Smoke Aura Visual 12898
_ICON_MALFUNCTION = 11      # Malfunction 13319
_SV_SAWBLADE = 12050
_SV_ELECTRICAL_OVERLOAD = 10109
_SV_SELF_REPAIR = 10040
_SV_OVERLOAD = 11347
_SV_SELF_DESTRUCT = 1463
_SV_CHAIN_LIGHTNING = 36
_SV_THROW_SAW = 8306
_SV_THROW_BOMB = 3819
_SV_BOMB = 148
_SV_SMOKE = 2718
_SV_MALFUNCTION = 2956

_RESOLVE_EXCLUDED = ('mod-boss-mechanics resolve copy: the damage is set per target by spell_boss_mechanics_resolve '
                     'from the reference-health provider')
_SCRIPT_EXCLUDED = 'Deadmines: a percent of reference health, set by the SpellScript (DeadminesKit::RefFlat)'

# The resolve set (source/npcs/boss_mechanics.py): no active defense, redirection, reflection, threat, LoS or crit;
# always hits, fires the victim's procs, ignores caster modifiers. DefenseType 1 (Physical stays armor-reduced).
_RESOLVE_ATTRS = {
    'Attributes': _ATTR0_NO_ACTIVE_DEFENSE,
    'AttributesEx': _ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
    'AttributesEx2': _ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
    'AttributesEx3': _ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
    'AttributesEx4': ATTR4_NO_CAST_LOG,
    'DefenseType': 1,
}


def _raw(desc: str = '', aura_desc: str = '', **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more}


def _cast_bar(spell_id: int, name: str, school: School, cast_ms: int, visual: int, icon: int, desc: str, note: str):
    """A named no-effect cast bar (the shape of shared Preparing 205200): the registry mechanic registered beside it
    owns the hit. Not interruptible: a kick must not look as if it stopped a mechanic the registry still lands."""
    raw = _raw(desc, InterruptFlags=0, PreventionType=0, AttributesEx4=ATTR4_NO_CAST_LOG)
    raw.pop('CastingTimeIndex')
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=school, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B3: {note} A {cast_ms / 1000:g} s cast bar, DUMMY on the caster with no handler; '
              'not interruptible (InterruptFlags 0, PreventionType 0). The registry zone owns the hit.',
        raw_overrides=raw,
    )


def _self_visual(spell_id: int, name: str, school: School, visual: int, icon: int, note: str):
    return spell(
        id=spell_id, name=name, school=school, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B3: visual only. {note} Cast on itself, triggered; DUMMY with no handler, '
              'DO_NOT_DISPLAY | DO_NOT_LOG. Copies the stock visual, never the stock spell (DM implementation notes).',
        raw_overrides=_raw(SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _point_visual(spell_id: int, name: str, school: School, visual: int, icon: int, speed: float, note: str):
    raw = _raw(SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG,
               AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT)
    if speed:
        raw['Speed'] = speed
    return spell(
        id=spell_id, name=name, school=school, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B3: visual only. {note} Cast at a point (Unit::CastSpell(x, y, z), '
              'TARGET_DEST_DEST), triggered; DUMMY with no handler, DO_NOT_DISPLAY | DO_NOT_LOG, ignores LoS.'
              + (f' Speed {speed:g} yd/s (a missile from the caster).' if speed else ''),
        raw_overrides=raw,
    )


def _resolve_copy(spell_id: int, name: str, school: School, icon: int, note: str, visual: int = 0):
    s = spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                        implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                        potency_excluded=_RESOLVE_EXCLUDED)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B3: {note} A dungeon copy of the mod-boss-mechanics resolve spell (205001-205007, '
              'source/npcs/boss_mechanics.py) with its exact attribute set, so the combat log names the mechanic: '
              'bound to spell_boss_mechanics_resolve, which filters the targets to the shape and sets the damage.',
        raw_overrides={**_RESOLVE_ATTRS, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'SpellClassSet': 0,
                       'SpellLevel': 0, **({'SpellVisualID_1': visual} if visual else {})},
    )
    scripted_by(s, 'spell_boss_mechanics_resolve')
    return s


# --- Haywire SN1-SN4 (the Shredder) -----------------------------------------------------------------------------------
saw_spin_cast_205240 = _cast_bar(
    205240, 'Saw Spin', School.NORMAL, 2000, _SV_SAWBLADE, _ICON_SAWBLADE,
    'The saws spin out of control. Get away.',
    'SN1 (the Shredder) and SN12 (Sneed\'s Salvaged Saw): the 8 yd circle on the caster. SV 12050 (Sawblade 54904).')

splinter_spray_cast_205241 = _cast_bar(
    205241, 'Splinter Spray', School.NORMAL, 2000, _SV_STEAM_BLAST, _ICON_STEAM,
    'Spews splinters in front. Stay out of the front.',
    'SN2: the 90 degree, 10 yd frontal. SV 11064 (Steam Blast 50375); the wood chips (SV 90344) are on the hits.')

runaway_cast_205242 = _cast_bar(
    205242, 'Runaway', School.NORMAL, 2000, _SV_ELECTRICAL_OVERLOAD, _ICON_OVERLOAD,
    'Lurches out of control along a line. Get out of the line.',
    'SN3: the 4 yd line through a random non-tank to 30 yd; the Shredder charges along it after it resolves. SV 10109 '
    '(Electrical Overload 45336).')

malfunction_visual_205255 = _self_visual(
    205255, 'Malfunction', School.NORMAL, _SV_MALFUNCTION, _ICON_MALFUNCTION,
    'With every Haywire emote (SN1-SN4), on the Shredder: SV 2956 (Malfunction 13319).')

saw_spin_hit_205256 = _resolve_copy(
    205256, 'Saw Spin', School.NORMAL, _ICON_SAWBLADE,
    'SN1 / SN12: 40% Physical + Weakened inside the 8 yd circle, the tank included.')

splinter_spray_hit_205257 = _resolve_copy(
    205257, 'Splinter Spray', School.NORMAL, _ICON_STEAM,
    'SN2: 30% Physical + Weakened on non-tanks in the cone (TankExempt frontal; a second tank-role player in it takes '
    '30% of the tank row). SV SPLINTER_SPRAY_SPELLVISUAL (90344: the wood chips on each player hit).',
    visual=SPLINTER_SPRAY_SPELLVISUAL)

runaway_hit_205258 = _resolve_copy(
    205258, 'Runaway', School.NORMAL, _ICON_OVERLOAD,
    'SN3: 35% Physical + Weakened in the line.')

splinter_spray_tank_205253 = spell(
    id=205253, name='Splinter Spray', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=30.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                     potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_STEAM,
    notes='Deadmines Pilot WP-B3: SN2, the tank\'s hit. The registry frontal skips the Shredder\'s victim '
          '(TankExempt), '
          'so the Shredder casts this on its victim (triggered) when the spray resolves with the tank in the cone; '
          'spell_dm_sneed_splinter_tank sets RefFlat(caster, 30%, tank row). Physical, armor applies ("before '
          'armor"), unavoidable, no Weakened. The resolve set\'s attributes. SV SPLINTER_SPRAY_SPELLVISUAL.',
    raw_overrides=_raw('Spews splinters at the target for 30% of the tank reference health as Physical damage.',
                       SpellVisualID_1=SPLINTER_SPRAY_SPELLVISUAL, **_RESOLVE_ATTRS),
)
scripted_by(splinter_spray_tank_205253, 'spell_dm_sneed_splinter_tank')

# --- Back in the Saddle SN7 (Sneed) and the wreck --------------------------------------------------------------------


def _repairs(spell_id: int, duration_ms: int, label: str):
    return spell(
        id=spell_id, name='Emergency Repairs', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_REPAIR,
        notes=f'Deadmines Pilot WP-B3: SN7 {label}, Sneed repairs the wreck: a {duration_ms // 1000} s self channel '
              '(SPELL_ATTR1_IS_SELF_CHANNELED, like Evocation 12051) with a DUMMY aura. Interruptible: '
              'ChannelInterruptFlags 0x08 (a kick) and PreventionType 1 (a silence); no pushback flag, so damage does '
              'not shorten it (boss_sneed_rework breaks it at 10% of his health instead). OnChannelFinished = the '
              'Shredder reboots; OnSpellFailed = stopped. SV 10040 (Self Repair 44994). On the descriptor\'s interrupt '
              'list, priority 2 (above Tazer).',
        raw_overrides=_raw('Repairs the Shredder. Interrupt it, or hit Sneed hard enough to knock him off the wreck.',
                           'Repairing the Shredder.', AttributesEx=_ATTR1_IS_SELF_CHANNELED,
                           ChannelInterruptFlags=_CHANNEL_INTERRUPT_FLAG_INTERRUPT, InterruptFlags=0,
                           PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=_SV_SELF_REPAIR,
                           AttributesEx4=ATTR4_NO_CAST_LOG),
    )


emergency_repairs_205243 = _repairs(205243, 6000, 'normal')
emergency_repairs_fast_205244 = _repairs(205244, 4000, 'heroic')

broken_down_205254 = spell(
    id=205254, name='Broken Down', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SMOKE,
    notes='Deadmines Pilot WP-B3: the wreck\'s state. The Shredder casts it on itself at each breakdown and drops it '
          'on a reboot or reset; smoke SV 2718 (Smoke Aura Visual 12898). The boss descriptor ignores the Shredder '
          'while it has this aura (and targets it only without). DUMMY, not passive (shown), Dispel none.',
    raw_overrides=_raw('Broken down.', 'Broken down. Sneed wants it back.', SpellVisualID_1=_SV_SMOKE,
                       AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- Wreck Overload SN9 -----------------------------------------------------------------------------------------------
overload_sparks_205245 = _cast_bar(
    205245, 'Overload', School.FIRE, 3000, _SV_OVERLOAD, _ICON_SPARKS,
    'The wreck is about to blow. Get away from it.',
    'SN9: the 3 s sparks on the wreck before the 10 yd blast. SV 11347 (Overload 51743).')

overload_blast_205246 = _self_visual(
    205246, 'Self Destruct', School.FIRE, _SV_SELF_DESTRUCT, _ICON_FIRE,
    'SN9: the blast on the wreck when the registry circle resolves, SV 1463 (Self Destruct 9874).')

wreck_overload_hit_205260 = _resolve_copy(
    205260, 'Wreck Overload', School.FIRE, _ICON_SPARKS,
    'SN9: 60% Fire to anyone within 10 yd of the wreck, no Weakened (ruling 30); Sneed is never hit (players only).')

# --- Tazer SN5 --------------------------------------------------------------------------------------------------------


def _tazer(spell_id: int, targets: int, pcts: str, label: str):
    return spell(
        id=spell_id, name='Tazer', school=School.NATURE, cast_time_ms=2000, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                        chain_targets=targets, potency_excluded=_SCRIPT_EXCLUDED)],
        spell_icon_id=_ICON_LIGHTNING,
        notes=f'Deadmines Pilot WP-B3: SN5 {label}. Sneed\'s 2 s cast at a random non-tank: Nature, chains to the '
              f'nearest player per jump (stock Chain Lightning 421\'s chain), {targets} targets; '
              f'spell_dm_sneed_tazer sets each hit to RefFlat(Sneed, {pcts}% by jump order). EffectChainAmplitude '
              '1.0 (the script sets every jump). Interruptible (InterruptFlags 15, PreventionType 1): on the '
              'descriptor\'s interrupt list below Emergency Repairs. Unavoidable, no Weakened. ALWAYS_HIT, '
              'CANT_CRIT, NO_REFLECTION, IGNORE_CASTER_MODIFIERS. SV 36 (Chain Lightning).',
        raw_overrides=_raw(f'Hurls a jolt at an enemy that jumps to up to {targets - 1} more nearby enemies.',
                           InterruptFlags=_INTERRUPT_FLAGS_CAST, PreventionType=_PREVENTION_SILENCE, DefenseType=1,
                           AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION, AttributesEx2=_ATTR2_CANT_CRIT,
                           AttributesEx3=_ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
                           EffectChainAmplitude_1=1.0, SpellVisualID_1=_SV_CHAIN_LIGHTNING,
                           CastingTimeIndex=5),
    )


tazer_205247 = _tazer(205247, 3, '20/14/10', 'normal')
tazer_heroic_205248 = _tazer(205248, 4, '35/25/18/12', 'heroic')
scripted_by(tazer_205247, 'spell_dm_sneed_tazer')
scripted_by(tazer_heroic_205248, 'spell_dm_sneed_tazer')

# --- Saw Boomerang SN6 ------------------------------------------------------------------------------------------------
saw_boomerang_cast_205249 = _cast_bar(
    205249, 'Saw Boomerang', School.NORMAL, 2000, 0, _ICON_THROW_SAW,
    'Throws a saw blade out along a line and back. Get out of the line and stay out until it returns.',
    'SN6: the 3 yd line through a random non-tank to 25 yd, out and back.')

saw_boomerang_throw_205250 = _point_visual(
    205250, 'Saw Boomerang', School.NORMAL, _SV_THROW_SAW, _ICON_THROW_SAW, 20.0,
    'SN6: the blade flying to the line\'s far end as the registry projectile leaves, SV 8306 (Throw Saw Blade 48984).')

saw_boomerang_hit_205259 = _resolve_copy(
    205259, 'Saw Boomerang', School.NORMAL, _ICON_THROW_SAW,
    'SN6: 25% Physical + Weakened per pass (out, then back).')

# --- Cluster Bomb SN10, SN11 (heroic) ---------------------------------------------------------------------------------
cluster_bomb_lob_205251 = _point_visual(
    205251, 'Cluster Bomb', School.FIRE, _SV_THROW_BOMB, _ICON_BOMB, 14.0,
    'SN10: the bomb lobbed at a random non-tank\'s spot, SV 3819 (Throw Bomb 40160).')

cluster_bomb_blast_205252 = _point_visual(
    205252, 'Cluster Bomb', School.FIRE, _SV_BOMB, _ICON_FIRE, 0.0,
    'SN10 / SN11: one blast where a bomb or bomblet lands, SV 148 (Bomb 8858, stock dynamite).')

cluster_bomb_hit_205261 = _resolve_copy(
    205261, 'Cluster Bomb', School.FIRE, _ICON_BOMB,
    'SN10 / SN11: 30% Fire + Weakened in the 5 yd bomb circle and in each 4 yd bomblet circle.')
