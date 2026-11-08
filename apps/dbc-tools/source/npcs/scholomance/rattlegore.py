"""
Scholomance build WP-S2: Rattlegore (11622), "Spare Parts"
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.4 rows RG, s3.5 row S2, s3.6; build spec
docs/dungeons/scholomance-rework.md SC 733-778). WP-S2 owns this file (its spells: kSpellsRattlegore 206130-206149 in
modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; RattlegoreLogic.h names the same ids).

- 11622 Rattlegore: boss_rattlegore_rework (SmartAI off; WP-S2's SQL rev drops stock rows 11622 Knock Away 10101,
  Strike 18368 and War Stomp 16727), normal HealthModifier 73.559 (185k on the level 61 paladin base 2,515), stun
  immune (1972), INSTANCE_BIND. DamageModifier 7.0: his own now (the live 7 was a mod-progression leftover; SC "hits
  extremely hard", the highest in the dungeon with the Ravenian); WP-T tunes it. Heroic health 280k and the tier's melee
  are WP-H's heroic template 310110 (source/world/dungeons/scholomance.py).
- 300531 Loose Part (the bone pile): a prop, not selectable or attackable (KIT_HELPER), Bone Spider display 27976 at
  scale 0.4 (WP-V). npc_sc_loose_part (a NullCreatureAI): boss_rattlegore_rework moves it (the crawl) and despawns it.
- 300532 Unfinished Construct: a prop, KIT_HELPER, Risen Construct 10488's display 12074 at scale 0.7 (WP-V) in the
  collapsed pose of Permanent Feign Death 29266 (WP-S2's SQL rev: creature_template_addon). Four are summoned on the
  pull at kConstructSpots; Salvage spends them. npc_sc_unfinished_construct (a NullCreatureAI).
Neither add gets a heroic template (props; handoff s3.3: they run on their normal entry).

Spells. The landing and the rings deal their damage through dungeon copies of the mod-boss-mechanics resolve spell
(the registry's percent of the reference row; the combat log names the mechanic). The rest are script spells whose
numbers the script sets (DungeonKit::RefFlat, or a percent of his health as base point 0), auras, a cast bar and looks:

  206130  Part Lands         RG1 the landing circle's hit: resolve copy, Physical, 30% / 40% + 1 Weakened
  206131  Part Flung         RG1 the bone missile to the landing point (cosmetic, to a point; Speed 20)
  206132  Grinding Bones     RG2 the soaker's tick, 5% / 6% per second on the pile (spell_sc_rattlegore_grind)
  206133  Bolted Back On     RG3 a pile home: heals him 8% / 10% of his health (base point 0 from the script)
  206134  Frenzy             RG8 +3% attack speed and +1% size per stack, 100 stacks (Risen Construct Frenzy's look)
  206135  Ossuary Eruption   RG4 the 2 s cast bar (the registry rings own the hits)
  206136  Ossuary Eruption   RG4 a ring's hit: resolve copy, Physical, 35% / 50%
  206137  Salvage            RG5 the 5 s self channel, interruptible (the descriptor's interrupt list)
  206138  Salvage            RG5 an unbroken channel: heals him 10% of his health (base point 0 from the script)
  206139  Reinforced         RG5 heroic: +15% damage dealt per stack, 4 stacks
  206140  Knock Away         RG7 stock 10101 without its third effect (the 25% threat cut of spell_gen_knock_away)
  206141  Ground to Dust     RG2 a pile ground down, a construct spent: the burst (look only)
  206142-206149 spare

Visual ids are WP-V's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import self_visual
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BONE_PILE_PART_SIZE,
    DISPLAY_BONE_PILE_PART,
    DISPLAY_UNFINISHED_CONSTRUCT,
    RG_ERUPTION_RING,
    RG_FRENZY,
    RG_GRINDING_A_PILE,
    RG_LANDING,
    RG_PART_FLUNG,
    RG_PILE_BOLTS_BACK_ON,
    RG_PILE_BOLTS_BACK_ON_ALT,
    RG_SALVAGE_CHANNEL,
    UNFINISHED_CONSTRUCT_SIZE,
)

_S2 = 'Scholomance build WP-S2 (Rattlegore)'

creature_template_columns(11622, **boss_columns('boss_rattlegore_rework', 73.559, DamageModifier=7.0))

# --- Boss-kit creatures -----------------------------------------------------------------------------------------------
loose_part_300531 = creature_template(
    300531, 'Loose Part', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                             'ScriptName': 'npc_sc_loose_part'},
)
creature_model(300531, display_id=DISPLAY_BONE_PILE_PART, scale=BONE_PILE_PART_SIZE)

unfinished_construct_300532 = creature_template(
    300532, 'Unfinished Construct', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                       'ScriptName': 'npc_sc_unfinished_construct'},
)
creature_model(300532, display_id=DISPLAY_UNFINISHED_CONSTRUCT, scale=UNFINISHED_CONSTRUCT_SIZE)

# --- Constants -------------------------------------------------------------------------------------------------------
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

_ATTR0_IS_ABILITY = 0x00000010
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_NO_IMMUNITIES = 0x20000000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_IS_SELF_CHANNELED = 0x00000040
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000

_CHANNEL_INTERRUPT_FLAG_INTERRUPT = 0x08
_PREVENTION_SILENCE = 1
_PREVENTION_PACIFY = 2
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_SCHOOL_MASK_ALL = 127

_ICON_BONE = 1          # generic
_ICON_FRENZY = 95       # Risen Construct Frenzy 8269
_ICON_WAR_STOMP = 50    # War Stomp 16727 (the stomp it replaces)
_ICON_KNOCK_AWAY = 314  # Knock Away 10101
_ICON_HEAL = 1          # generic
_SV_KNOCK_AWAY = 2069   # Knock Away 10101

_SCRIPT_DAMAGE = 'Scholomance: a percent of reference health, set by the script (DungeonKit::RefFlat)'
_SCRIPT_HEAL = 'Scholomance: a percent of his own health, base point 0 set by boss_rattlegore_rework'

# --- RG1 Part lands --------------------------------------------------------------------------------------------------
part_lands_206130 = resolve_copy(
    206130, 'Part Lands', School.NORMAL, 'A piece of the golem crashes down.',
    f'{_S2} RG1 Part lands: the landing circle\'s hit (4 yd normal, 6 yd heroic, 2 s, at a floor point 20+ yd from '
    'him), 30% / 40% of the non-tank row + 1 Weakened (ruling 21), through the registry. Copy of the resolve spell '
    "205001 (Physical). Shattered Bones 70961's SpellVisual 15031 (DustCloud_Land + bone spurs) on every unit hit: the "
    'visible impact.',
    icon=_ICON_BONE, visual=RG_LANDING,
)

part_flung_206131 = spell(
    id=206131, name='Part Flung', school=School.NORMAL, attributes=_ATTR0_DO_NOT_LOG | _ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_BONE,
    notes=f'{_S2} RG1: the bone missile to the landing point, a no-effect missile cast at a point by Rattlegore '
          "(triggered). Throw Bone Boulder 48430's SpellVisual 10772 (nightbane_bone_missile; alt 11069). Speed 20 "
          'yd/s = RattlegoreLogic.h kPartFlungSpeed: the script launches it so it lands when the circle resolves.',
    raw_overrides=kit_raw('Flings a piece of bone.', SpellVisualID_1=RG_PART_FLUNG, Speed=20.0,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          CastingTimeIndex=1),
)

# --- RG2 / RG3 Loose part ------------------------------------------------------------------------------------------
grinding_bones_206132 = spell(
    id=206132, name='Grinding Bones', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_DAMAGE)],
    attributes=_ATTR0_NO_ACTIVE_DEFENSE,
    spell_icon_id=_ICON_BONE,
    notes=f'{_S2} RG2 Loose part: the pile cuts whoever grinds it down. Each second a player stands on a pile (3 yd), '
          'the pile casts this (triggered) on every player on it: 5% (heroic 6%) of the reference row, set at launch '
          'by spell_sc_rattlegore_grind (DungeonKit::RefFlatOn: the tank row on a tank), 25% / 36% over the 5 / 6 s '
          'grind; no Weakened (healer load, SC). The resolve attribute set (no active defense, no redirection or '
          "reflection, no threat, ignores LoS, cannot crit, always hits, ignores caster modifiers). Bone Crack 52080's "
          'SpellVisual 11411 on the soaker: the visible impact.',
    raw_overrides=kit_raw('Grinds a bone pile down, and it cuts back.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=RG_GRINDING_A_PILE),
)
scripted_by(grinding_bones_206132, 'spell_sc_rattlegore_grind')


def _self_heal(spell_id: int, name: str, visual: int, notes: str, desc: str):
    """A heal on the caster whose amount is base point 0 from the script (a percent of his own health): DieSides 0 so
    the amount is exact, ignores caster modifiers, no threat."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=_SCRIPT_HEAL)],
        spell_icon_id=_ICON_HEAL, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, AttributesEx=_ATTR1_NO_THREAT,
                              AttributesEx3=_ATTR3_NOT_A_PROC | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=visual),
    )


bolted_back_on_206133 = _self_heal(
    206133, 'Bolted Back On', RG_PILE_BOLTS_BACK_ON,
    f'{_S2} RG3 Pile returns: a bone pile that reaches him bolts back on and heals him 8% (heroic 10%) of his maximum '
    'health (14,800 / 28,000), plus 5 Frenzy stacks (the script). Cast triggered on himself with base point 0. '
    "Reconstruct 10260's SpellVisual 163 (SkullBalls chest).",
    'A loose part bolts back on.',
)

# --- RG8 Frenzy ----------------------------------------------------------------------------------------------------
frenzy_206134 = spell(
    id=206134, name='Frenzy', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=3, die_sides=0,
               implicit_target_a=TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SCALE, base_points=1, die_sides=0,
               implicit_target_a=TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_FRENZY,
    notes=f'{_S2} RG8 Frenzy, his enrage (dungeon ruling 12): +1 stack every 3 s (heroic 2 s) from the pull, up to '
          '100; each break halves it, each pile home adds 5 (DungeonKit::AddStacks). Per stack +3% attack speed '
          '(SPELL_AURA_MOD_MELEE_HASTE) and +1% size (SPELL_AURA_MOD_SCALE), so the stacks read on his body: Risen '
          "Construct Frenzy 8269's look (SpellVisual 870, BeastRageCaster; icon 95) without its +50% damage. Attack "
          'speed only: it loads the tank and the healer and never scales the reference-sized hits. Until the fight '
          'ends (the script removes it on reset), not dispellable.',
    raw_overrides=kit_raw("Increases the caster's attack speed by $s1% and its size by $s2% per application.",
                          'Attack speed increased by $s1%.', instant=True, CumulativeAura=100,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=RG_FRENZY),
)

# --- RG4 Ossuary Eruption ------------------------------------------------------------------------------------------
eruption_cast_206135 = cast_bar(
    206135, 'Ossuary Eruption', 2000, 'Stomps, and bone spikes burst from the floor in rings moving outward.',
    f'{_S2} RG4 Ossuary Eruption: the 2 s stomp (emote line 1) that replaces War Stomp 16727 (its 5 s stun is gone). '
    'The registry rings own the hits: 0-6 yd as the bar ends, then 6-12 and 12.06-18 yd 1.5 s apart (heroic: back '
    'inward, 1 s apart), from the spot he stomped. No visual on the bar; 206136 carries the spikes.',
    icon=_ICON_WAR_STOMP,
)

eruption_hit_206136 = resolve_copy(
    206136, 'Ossuary Eruption', School.NORMAL, 'Bone spikes burst from the floor.',
    f'{_S2} RG4 Ossuary Eruption: a ring\'s hit, 35% (heroic 50%) of the non-tank row, no Weakened, through the '
    "registry. Copy of the resolve spell 205001 (Physical). Impale 53454's SpellVisual 11766 (Spike_Impact_Base) on "
    'every unit hit (Bone Spike Graveyard SV 15339 draws nothing, VISUALS-REPORT).',
    icon=_ICON_WAR_STOMP, visual=RG_ERUPTION_RING,
)

# --- RG5 Salvage -----------------------------------------------------------------------------------------------------
salvage_206137 = spell(
    id=206137, name='Salvage', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=5000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BONE,
    notes=f'{_S2} RG5 Salvage: from the second break, at most every 30 s, he walks to the nearest Unfinished '
          'Construct and tears bones out of it: a 5 s self channel (SPELL_ATTR1_IS_SELF_CHANNELED, like Sneed\'s '
          'Emergency Repairs 205243) with a DUMMY aura. Interruptible: ChannelInterruptFlags 0x08 (a kick) and '
          'PreventionType 1 (a silence); no pushback flag, so damage does not shorten it (boss_rattlegore_rework '
          'breaks it at 5% of his health instead). OnChannelFinished = he heals (206138; heroic +Reinforced); '
          'OnSpellFailed = stopped. The descriptor\'s interrupt list, priority 2. Reconstruct 10260\'s SpellVisual '
          '163 as the channel look (Grab Skeleton and Salvage Corpse draw nothing or a pick, VISUALS-REPORT).',
    raw_overrides=kit_raw('Tears bones out of an unfinished construct. Interrupt it, or hit him hard enough to stop '
                          'it.', 'Salvaging bones.', AttributesEx=_ATTR1_IS_SELF_CHANNELED,
                          ChannelInterruptFlags=_CHANNEL_INTERRUPT_FLAG_INTERRUPT, InterruptFlags=0,
                          PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=RG_SALVAGE_CHANNEL,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

salvage_heal_206138 = _self_heal(
    206138, 'Salvage', RG_PILE_BOLTS_BACK_ON_ALT,
    f'{_S2} RG5 Salvage: a channel nobody stopped patches him for 10% of his maximum health (18,500 normal, 28,000 '
    "heroic). Cast triggered on himself with base point 0. Animate Bones 53334's SpellVisual 11741 (the "
    "Reconstruct look 163 is the channel's).",
    'Patches himself with salvaged bones.',
)

reinforced_206139 = spell(
    id=206139, name='Reinforced', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=15,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BONE,
    notes=f'{_S2} RG5 heroic Reinforced: each Salvage nobody stopped adds a stack, +15% damage dealt each '
          '(SPELL_AURA_MOD_DAMAGE_PERCENT_DONE, every school), up to 4 (the construct cap), for the rest of the fight. '
          'It raises his melee, Strike and Knock Away; the custom hits ignore caster modifiers, so the reference-sized '
          'hits stay exact. Not dispellable.',
    raw_overrides=kit_raw('Increases damage dealt by $s1% per application.', 'Damage dealt increased by $s1%.',
                          instant=True, CumulativeAura=4, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- RG7 Knock Away (stock 10101 without the threat cut) -----------------------------------------------------------
knock_away_206140 = spell(
    id=206140, name='Knock Away', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.KNOCK_BACK, base_points=112, die_sides=75, misc_value=75,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_KNOCK_AWAY,
    notes=f'{_S2} RG7 Knock Away: stock 10101 (normal damage plus 30, the knockback 7.5 / 11.3-18.7) without its third '
          'effect, the SCRIPT_EFFECT that spell_gen_knock_away turns into a 25% threat cut (SC: a boss this '
          'hard-hitting must not turn onto a DPS). The weapon hit is 100% weapon damage (WEAPON_PERCENT_DAMAGE, '
          'weapon_potency 100: the potency lint takes no flat weapon bonus; the stock +30 is noise against his '
          "swing), so it follows the template's melee (heroic: the heroic template's). Cast triggered on his victim "
          'in melee range. Stock look: SpellVisual 2069, icon 314.',
    raw_overrides=kit_raw('Inflicts $s1% weapon damage to an enemy and knocks it back.', instant=True,
                          DefenseType=_DEFENSE_MELEE, PreventionType=_PREVENTION_PACIFY,
                          SpellVisualID_1=_SV_KNOCK_AWAY),
)

# --- RG2 / RG5 look ------------------------------------------------------------------------------------------------
ground_to_dust_206141 = self_visual(
    206141, 'Ground to Dust', RG_LANDING,
    f'{_S2} RG2 / RG5: the burst when a pile is ground down or a construct is spent, cast by the pile or the '
    "construct on itself (triggered) just before it despawns. Shattered Bones 70961's SpellVisual 15031 "
    '(DustCloud_Land + bone spurs). Look only.',
    icon=_ICON_BONE,
)
