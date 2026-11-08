"""
Shadowfang Keep build WP-S9: Archmage Arugal (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.5
rows AR1-AR9, s3.6 row S9, s7 #7 and #22, s10 (the user's rulings on his room); build spec
docs/dungeons/shadowfang-keep-rework.md SK 1576-1646 (build spec), SK 1394-1575 (design)). WP-S9 owns this file (its
spells: kSpellsArugal 206060-206084 in modules/mod-dungeon-bosses src/ShadowfangKeep/ShadowfangKeepRework.h only;
206085-206089 are S10's; ArugalLogic.h names the same ids).

- 4275 Archmage Arugal: bound to boss_archmage_arugal_rework (SmartAI off; WP-S9's SQL rev drops all the stock rows),
  normal 17,284 (HealthModifier 37.25 on the paladin base 464 at 21: SK's 17,280, handoff s7 #7), stun immune
  (IMMUNITY_BOSS_STUN 1972). Stock melee (DamageModifier 5.7). Heroic 405,840 is WP-H's override in
  source/world/dungeons/shadowfang_keep.py.
- 300513 Sorcerer Ashcrombe / 300514 Deathstalker Adamant, the lair prisoners (declared by WP-K, handoff s7 #9; scripted
  by npc_sfk_lair_prisoner): their gossip menus 300513 / 300514 (WP-S9's SQL rev: the SK body texts, no option; S10's
  heroic option comes through LairPrisoner.h), and not attackable (UNIT_FLAG_NON_ATTACKABLE) and ignored by creatures
  (UNIT_FLAG_IMMUNE_TO_NPC): the pack wolves can outlive Nandos by the lair door where it waits (WP-S8's note).
- 300515 Ward Stalker: the invisible stalker (display 11686) at a ward, carrying its look (the rune or the smoke) for
  the ward's 10 s. Not selectable, no XP, trigger; no script, no heroic template.

Spells (stock spells are never cast, their visuals are copied; the looks are WP-V's _visuals.py picks):

  206060  Worgen's Curse       AR1 normal: the 100-stack meter (CumulativeAura 100), a DUMMY debuff for the fight, cast
                               by Arugal (DungeonKit::AddStacks). Dispel none and NO_IMMUNITIES: nothing removes it but
                               the wards. "Turning into a worgen."
  206061  Worgen's Curse       AR1 + AR8 heroic: the same meter; the tooltip names Feral Power (206062 carries it).
  206062  Feral Power          AR8 heroic: hidden; +2% damage done (all schools) and +2% healing done per stack, one
                               stack per full 10 curse stacks, 9 at most (+18%); the script keeps it in step.
  206063  Thundershock         AR2 the 2 s cast bar (not interruptible: the registry ring owns the hit); Thundershock
                               7803's SV 145 (the thunderclap as the bar ends)
  206064  Thundershock         AR2 the registry's resolve copy (Nature): 30%, no Weakened (Dungeon ruling 13); SV 145
  206065  Thundershock         AR2 the rider: a 1.5 s stun (mechanic stun) on anyone still inside. Dispel none
  206066  Void Bolt            AR3 a real 3 s cast on his target, interruptible (InterruptFlags 15, PreventionType
                               silence; on the descriptor's interrupt list); Shadow, 15% / 25% of the reference row
                               (spell_sfk_arugal_void_bolt at launch) and +3 curse stacks when it lands. Void Bolt
                               7588's SV 758 and speed 14; ignores caster modifiers, cannot crit
  206067  Arugal's Curse       AR4 the cursed player's 3 s mark (Arugal's Curse 7621's SV 760, the purple tint): the
                               +10 stacks are the script's. Dispel none
  206068  Shadow Port          AR5 the 1 s flicker (cast bar; Shadow Port 7136's SV 3303), then the script's teleport
  206069  Turned               AR6 at 100 stacks: MOD_CHARM (max level 100) and the Shadowfang Glutton's shape (3857),
                               for as long as the charm; the aura the bots read as a turned teammate (F1). Mechanic
                               none, Dispel none, NO_IMMUNITIES: no trinket, Freedom or Remove Curse breaks it. Worgen's
                               Command 53070's SV 7597 (the charm glow). "A worgen in Arugal's service."
  206070  Turned               AR6 the morph burst on the player as it turns (Worgen Transform 47457's SV 7199)
  206071  Ashcrombe's Ward     AR7 Ashcrombe draws the circle: a look at the ward stalker (Rune of Power 61973's SV
                               13072, the casting hands)
  206072  Cleansing Vial       AR7 Adamant throws the vial at the ward (Sprinkle Holy Water 57806's SV 12483, speed 15)
  206073  Ashcrombe's Ward     AR7 the arcane rune on the ward stalker (Rune of Power 61974's SV 13069), 10 s
  206074  Cleansing Smoke      AR7 the cloud on the ward stalker (Zul'Aman Spirit Effect 42466's SV 9554), 10 s
  206075  Ashcrombe's Ward     AR7 the cleanse on each player inside when the ward pulses (Remove Curse 475's SV 186)
  206076  Moonrise             AR9 heroic: the 3 s cast bar (not interruptible); Eclipse (Lunar) 48518's SV 11567
  206077  Moonrise             AR9 heroic: the moon on Arugal for the rest of the fight (Starfall 48505's SV 11571)
  206078  Moonlight            AR9 heroic: the moonlight shafts on strike stalkers 300516 (Beam (Blue) 32840's SV 7990)
  206079  Worgen's Curse       AR1 look at 50+ stacks: hidden (Lycanthropy 49170's SV 11338, purple wisps)
  206080  Worgen's Curse       AR1 look at 80+ stacks: hidden (SV 760, the body tint)
  206081-206084 spare (206085-206089 are S10's).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    AR_CURSE,
    AR_CURSE_50,
    AR_CURSE_80,
    AR_ECLIPSE,
    AR_MOONLIT_BEAM,
    AR_SHADOW_PORT,
    AR_STARFALL_STATE,
    AR_THUNDERSHOCK,
    AR_TURNED_CHARM,
    AR_TURNED_TRANSFORM,
    AR_VIAL_CLOUD,
    AR_VIAL_THROW,
    AR_VOID_BOLT,
    AR_WARD_CLEANSE,
    AR_WARD_HANDS,
    AR_WARD_RUNE,
    DISPLAY_INVISIBLE_STALKER,
)

creature_template_columns(4275, **boss_columns('boss_archmage_arugal_rework', 37.25))

# --- The lair prisoners --------------------------------------------------------------------------------------------
# Copies of the stock cell prisoners 3850 / 3849 (read-only SELECTs 2026-11-07: levels, faction, class, flags,
# modifiers, models) without their SmartAI, loot or stock gossip menu, so the stock courtyard event never runs again.
# The instance summons the one who opened the Courtyard Door (DATA_PRISONER; else by the players' side) at the lair
# door once Nandos is dead. Friendly gossip NPCs (npcflag 1) on their own menus (WP-S9's SQL rev); no heroic template.
_UNIT_FLAG_NON_ATTACKABLE = 0x2
_UNIT_FLAG_IMMUNE_TO_NPC = 0x200
_LAIR_PRISONER_FLAGS = _UNIT_FLAG_NON_ATTACKABLE | _UNIT_FLAG_IMMUNE_TO_NPC
_LAIR_PRISONER = {
    **KIT_CREATURE, 'minlevel': 18, 'maxlevel': 18, 'rank': 1, 'npcflag': 1,
    'HealthModifier': 3.0, 'DamageModifier': 1.7, 'ExperienceModifier': 1.0, 'lootid': 0, 'pickpocketloot': 0,
    'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_sfk_lair_prisoner',
}

lair_ashcrombe_300513 = creature_template(
    300513, 'Sorcerer Ashcrombe', **{**_LAIR_PRISONER, 'faction': 12, 'unit_class': 8,
                                    'unit_flags': 32832 | _LAIR_PRISONER_FLAGS, 'ManaModifier': 2.0,
                                    'gossip_menu_id': 300513},
)
creature_model(300513, display_id=2005)

lair_adamant_300514 = creature_template(
    300514, 'Deathstalker Adamant', **{**_LAIR_PRISONER, 'faction': 68, 'unit_class': 1,
                                      'unit_flags': 37440 | _LAIR_PRISONER_FLAGS, 'gossip_menu_id': 300514},
)
creature_model(300514, display_id=2006)

# --- The ward stalker ----------------------------------------------------------------------------------------------
ward_stalker_300515 = creature_template(
    300515, 'Ward Stalker', **{**KIT_HELPER, 'minlevel': 20, 'maxlevel': 20, 'rank': 0, 'unit_class': 1, 'type': 10,
                               'flags_extra': 0x40 | 0x80, 'ScriptName': ''},
)
creature_model(300515, display_id=DISPLAY_INVISIBLE_STALKER)

# --- Spells (206060-206084) ----------------------------------------------------------------------------------------

_AR = 'Shadowfang Keep build WP-S9'
_SCRIPT_EXCLUDED = 'Shadowfang Keep: a percent of reference health, set by the script (DungeonKit::RefFlat)'

_SCHOOL_ALL = 127
_MECHANIC_STUN = 12
_TARGET_UNIT_TARGET_ENEMY = 6
_INTERRUPT_FLAGS_STANDARD = 15     # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_AURA_MOD_CHARM = 6                # SPELL_AURA_MOD_CHARM (SpellAuraDefines.h)
_ENTRY_SHADOWFANG_GLUTTON = 3857   # the stock Arugal's Curse transform (display 202)

_ICON_ARUGALS_CURSE = 173          # Arugal's Curse 7621
_ICON_THUNDERSHOCK = 320           # Thundershock 7803
_ICON_VOID_BOLT = 213              # Void Bolt 7588
_ICON_SHADOW_PORT = 207            # Shadow Port 7136
_ICON_RUNE_OF_POWER = 1954         # Rune of Power 61974
_ICON_HOLY_WATER = 2820            # Sprinkle Holy Water 57806
_ICON_ECLIPSE = 2856               # Eclipse (Lunar) 48518
_ICON_REMOVE_CURSE = 195           # Remove Curse 475



def _look_at(spell_id: int, name: str, visual: int, notes: str, *, icon: int, speed: float = 0.0,
             school: School = School.NORMAL):
    """An instant no-effect spell a unit casts on another (triggered) for the look at the target (and the missile when
    `speed` is set). DO_NOT_DISPLAY; logged, so the combat log names the ward."""
    raw = kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                  AttributesEx4=ATTR4_NO_CAST_LOG)
    if speed:
        raw['Speed'] = speed
    return spell(
        id=spell_id, name=name, school=school, attributes=ATTR0_DO_NOT_DISPLAY, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _hidden_look(spell_id: int, name: str, visual: int, notes: str, *, icon: int, duration_ms: int = -1):
    """A hidden DUMMY aura that carries a StateKit look on its holder (applied with Unit::AddAura, no cast)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- AR1 / AR8 the Worgen's Curse -----------------------------------------------------------------------------------

def _worgens_curse(spell_id: int, heroic: bool):
    aura = ('Turning into a worgen. Damage and healing done increased.' if heroic else 'Turning into a worgen.')
    desc = ('Stacks up to $u times. At $u stacks you turn into a worgen in Arugal\'s service.'
            + (' Every 10 stacks also increase your damage and healing done by 2%.' if heroic else ''))
    label = 'heroic (its tooltip names Feral Power, carried by 206062)' if heroic else 'normal'
    return spell(
        id=spell_id, name="Worgen's Curse", school=School.SHADOW, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=_ICON_ARUGALS_CURSE,
        notes=f'{_AR}, AR1 {label}: the fight\'s meter on every player, a DUMMY debuff stacking to 100 '
              '(CumulativeAura; Yogg-Saron\'s Sanity 63050 is the 100-stack precedent), for the fight (removed on his '
              'death, evade and reset, and on the player\'s death). Arugal applies and changes it '
              '(DungeonKit::AddStacks): +1 every 3 s (Moonrise +2 per s), +15 Thundershock, +3 Void Bolt, +10 '
              'Arugal\'s Curse, -10 a ward. At 100: Turned (206069). Dispel none and NO_IMMUNITIES: nothing removes '
              'it but the wards (W1\'s Ashcrombe\'s Locket relies on it). The bots\' ward eligibility reads its '
              'stacks.',
        raw_overrides=kit_raw(desc, aura, CastingTimeIndex=1, CumulativeAura=100, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


worgens_curse_206060 = _worgens_curse(206060, heroic=False)
worgens_curse_heroic_206061 = _worgens_curse(206061, heroic=True)

feral_power_206062 = spell(
    id=206062, name='Feral Power', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=1,
                    misc_value=_SCHOOL_ALL, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Feral Power: a flat +2% damage done per stack, not a damage value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Feral Power: a flat +2% healing done per stack, not a heal value')],
    spell_icon_id=_ICON_ARUGALS_CURSE,
    notes=f'{_AR}, AR8 (heroic): the Worgen\'s Curse\'s Feral Power, +2% damage done (all schools) and +2% healing '
          'done per stack; the script holds one stack per full 10 curse stacks, 9 at most (+18% at 90). Hidden '
          '(DO_NOT_DISPLAY): the curse aura\'s tooltip names it, so there is no second buff to read (SK AR8). '
          'CumulativeAura 9; the aura multiplies the per-stack amount (AuraEffect::CalculateAmount).',
    raw_overrides=kit_raw('Damage and healing done increased by $s1%.', 'Damage and healing done increased.',
                          CastingTimeIndex=1, CumulativeAura=9, AttributesEx4=ATTR4_NO_CAST_LOG),
)

curse_glow_206079 = _hidden_look(
    206079, "Worgen's Curse", AR_CURSE_50,
    f'{_AR}, AR1: the look at 50+ curse stacks (Lycanthropy 49170\'s SV 11338, purple wisps), added and removed by '
    'the script with the meter (VISUALS-REPORT gap 21).', icon=_ICON_ARUGALS_CURSE)

curse_tint_206080 = _hidden_look(
    206080, "Worgen's Curse", AR_CURSE_80,
    f'{_AR}, AR1: the look at 80+ curse stacks (Arugal\'s Curse 7621\'s SV 760, the purple body tint), added and '
    'removed by the script with the meter.', icon=_ICON_ARUGALS_CURSE)

# --- AR2 Thundershock ----------------------------------------------------------------------------------------------

thundershock_bar_206063 = cast_bar(
    206063, 'Thundershock', 2000, 'Thunder gathers around Arugal.',
    f'{_AR}, AR2: the 2 s cast bar (no effect, not interruptible: the registry Circle of 8 yd on him, registered '
    'beside it, owns the hit). Thundershock 7803\'s SV 145: the thunderclap as the bar ends.',
    icon=_ICON_THUNDERSHOCK, visual=AR_THUNDERSHOCK, school=School.NATURE)

thundershock_206064 = resolve_copy(
    206064, 'Thundershock', School.NATURE, 'Thunder around Arugal.',
    f'{_AR}, AR2: the registry resolve copy (Nature): 30% to everyone inside the 8 yd ring, no Weakened (Dungeon '
    'ruling 13: the penalty is +15 curse stacks, the registry OnHit), plus the 206065 stun rider. SV 145 on every '
    'player hit.',
    icon=_ICON_THUNDERSHOCK, visual=AR_THUNDERSHOCK)

thundershock_stun_206065 = spell(
    id=206065, name='Thundershock', school=School.NATURE, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=1500,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=_MECHANIC_STUN,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_THUNDERSHOCK,
    notes=f'{_AR}, AR2: the rider on anyone still inside the ring: a 1.5 s stun (under the shared 2 s limit), '
          'mechanic stun (stun immunities and trinkets work), Dispel none. Cast by the registry marker with Arugal as '
          'the original caster.',
    raw_overrides=kit_raw('Stunned for $d.', 'Stunned.', CastingTimeIndex=1),
)

# --- AR3 Void Bolt -------------------------------------------------------------------------------------------------

void_bolt_206066 = spell(
    id=206066, name='Void Bolt', school=School.SHADOW, cast_time_ms=3000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_VOID_BOLT,
    notes=f'{_AR}, AR3: Arugal\'s main hit on his target, a real 3 s cast cast back to back between his other casts, '
          'interruptible (InterruptFlags 15, PreventionType silence; the descriptor\'s interrupt list). Shadow: 15% '
          'of the reference row on normal, 25% on heroic, set at launch by spell_sfk_arugal_void_bolt (RefFlat, so '
          'the target\'s defensives count), which also adds +3 Worgen\'s Curse stacks when it lands. Ignores caster '
          'modifiers and cannot crit (the number is the reference). Void Bolt 7588\'s SV 758 and missile speed 14.',
    raw_overrides=kit_raw('Hurls a bolt of void energy at an enemy.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=1, SpellVisualID_1=AR_VOID_BOLT, Speed=14.0,
                          AttributesEx2=ATTR2_CANT_CRIT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(void_bolt_206066, 'spell_sfk_arugal_void_bolt')

# --- AR4 Arugal's Curse --------------------------------------------------------------------------------------------

arugals_curse_206067 = spell(
    id=206067, name="Arugal's Curse", school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=3000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ARUGALS_CURSE,
    notes=f'{_AR}, AR4: the stock cast reworked (no charm): instant on a random non-tank within 30 yd, with yell line '
          '2. A 3 s DUMMY mark for the look (Arugal\'s Curse 7621\'s SV 760, the purple tint: a StateKit, so an '
          'aura); the +10 Worgen\'s Curse stacks are the script\'s. Dispel none.',
    raw_overrides=kit_raw('Arugal releases the wolf in you.', 'Worgen\'s Curse surges.', CastingTimeIndex=1,
                          SpellVisualID_1=AR_CURSE, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT),
)

# --- AR5 Shadow Port -----------------------------------------------------------------------------------------------

shadow_port_206068 = cast_bar(
    206068, 'Shadow Port', 1000, 'Arugal fades into the shadows.',
    f'{_AR}, AR5: the 1 s shadow flicker before he vanishes (cast bar, not interruptible: the timer is not pausable, a '
    'failed flicker still ports); then the script teleports him to his next spot (his spawn, the stock 7586 or the '
    'stock 7136). Shadow Port 7136\'s SV 3303.',
    icon=_ICON_SHADOW_PORT, visual=AR_SHADOW_PORT)

# --- AR6 Turned ----------------------------------------------------------------------------------------------------

turned_206069 = spell(
    id=206069, name='Turned', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_CHARM, base_points=99,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.TRANSFORM, misc_value=_ENTRY_SHADOWFANG_GLUTTON,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ARUGALS_CURSE,
    notes=f'{_AR}, AR6: a player at 100 Worgen\'s Curse stacks is Arugal\'s for good: MOD_CHARM (BasePoints 99 + '
          'DieSides 1: targets up to level 100) and the Shadowfang Glutton\'s shape (the stock 7621\'s transform, '
          'creature 3857, display 202). One aura for both, so it lasts exactly as long as the charm (handoff F1 open '
          'item 3: the descriptor\'s hostilePlayerAuras names it; the bots attack the turned player and stop healing '
          'it). Mechanic none, Dispel none, NO_IMMUNITIES: no trinket, Blessing of Freedom or Remove Curse breaks it. '
          'Released when Arugal dies, evades or resets (the script removes it). When every living player is turned, '
          'the script kills them and the fight resets (handoff s7 #22). Worgen\'s Command 53070\'s SV 7597 (the charm '
          'glow).',
    raw_overrides=kit_raw('Turned into a worgen in Arugal\'s service.', "A worgen in Arugal's service.",
                          CastingTimeIndex=1, SpellVisualID_1=AR_TURNED_CHARM,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT),
)

turned_burst_206070 = self_visual(
    206070, 'Turned', AR_TURNED_TRANSFORM,
    f'{_AR}, AR6: the morph burst as a player turns, cast by the player on itself (triggered) just before the charm '
    '(Worgen Transform 47457\'s SV 7199).',
    icon=_ICON_ARUGALS_CURSE, school=School.SHADOW)

# --- AR7 the wards -------------------------------------------------------------------------------------------------

ward_cast_ashcrombe_206071 = _look_at(
    206071, "Ashcrombe's Ward", AR_WARD_HANDS,
    f'{_AR}, AR7: Sorcerer Ashcrombe draws the arcane circle: cast by the lair prisoner on the ward stalker '
    '(triggered) as the ward is placed (Rune of Power 61973\'s SV 13072, the casting hands).',
    icon=_ICON_RUNE_OF_POWER, school=School.ARCANE)

ward_cast_adamant_206072 = _look_at(
    206072, 'Cleansing Vial', AR_VIAL_THROW,
    f'{_AR}, AR7: Deathstalker Adamant throws an apothecary vial at the ward stalker (triggered) as the ward is placed '
    '(Sprinkle Holy Water 57806\'s SV 12483: the thrown vial and its splash, speed 15; VISUALS-REPORT correction 4).',
    icon=_ICON_HOLY_WATER, speed=15.0)

ward_rune_206073 = _hidden_look(
    206073, "Ashcrombe's Ward", AR_WARD_RUNE,
    f'{_AR}, AR7: Ashcrombe\'s ward on the ward stalker 300515 (Rune of Power 61974\'s SV 13069, the blue rune on the '
    'floor; VISUALS-REPORT correction 3), for the ward\'s 10 s. The registry Stack disc shows its real size.',
    icon=_ICON_RUNE_OF_POWER, duration_ms=10000)

ward_smoke_206074 = _hidden_look(
    206074, 'Cleansing Smoke', AR_VIAL_CLOUD,
    f'{_AR}, AR7: Adamant\'s ward on the ward stalker 300515 (Zul\'Aman Spirit Effect 42466\'s SV 9554, white fog), '
    'for the ward\'s 10 s.',
    icon=_ICON_HOLY_WATER, duration_ms=10000)

ward_pulse_206075 = _look_at(
    206075, "Ashcrombe's Ward", AR_WARD_CLEANSE,
    f'{_AR}, AR7: the ward\'s pulse on each player inside (cast by the ward stalker, triggered) as they lose 10 '
    'Worgen\'s Curse stacks (Remove Curse 475\'s SV 186, the cleanse sparkle).',
    icon=_ICON_REMOVE_CURSE, school=School.ARCANE)

# --- AR9 Moonrise (heroic) -----------------------------------------------------------------------------------------

moonrise_bar_206076 = cast_bar(
    206076, 'Moonrise', 3000, 'Arugal calls down the full moon.',
    f'{_AR}, AR9 (heroic): the 3 s cast at 30% health, with yell line 4 and emote line 5 (not interruptible: the moon '
    'rises whatever happens). Eclipse (Lunar) 48518\'s SV 11567, the moon disc flash.',
    icon=_ICON_ECLIPSE, visual=AR_ECLIPSE, school=School.ARCANE)

moonrise_206077 = spell(
    id=206077, name='Moonrise', school=School.ARCANE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_ECLIPSE,
    notes=f'{_AR}, AR9 (heroic): the moon on Arugal for the rest of the fight (Starfall 48505\'s SV 11571, a lasting '
          'StateKit). The script turns the seep to +2 stacks per second and stops his other casts. Not dispellable.',
    raw_overrides=kit_raw('The full moon is risen.', 'The full moon: the Worgen\'s Curse seeps in six times faster.',
                          CastingTimeIndex=1, SpellVisualID_1=AR_STARFALL_STATE, AttributesEx4=ATTR4_NO_CAST_LOG),
)

moonlight_206078 = _hidden_look(
    206078, 'Moonlight', AR_MOONLIT_BEAM,
    f'{_AR}, AR9 (heroic): the moonlit room, a 40 yd shaft of moonlight on each strike / visual stalker 300516 the '
    'script places on his spots and over the prisoner\'s gallery (Beam (Blue) 32840\'s SV 7990).',
    icon=_ICON_ECLIPSE)
