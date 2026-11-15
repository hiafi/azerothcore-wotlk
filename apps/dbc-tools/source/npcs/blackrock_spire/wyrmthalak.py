"""
Blackrock Spire build WP-B8: Overlord Wyrmthalak (9568), "Overlord of the Three Tribes", normal and heroic
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows WT, s3.5 row B8, s3.6, s3.8 NM 8;
build spec docs/dungeons/blackrock-spire-rework.md SP 2436-2521, design SP 2175-2435, rulings 47-49, 63-64). WP-B8
owns this file (its spells: kSpellsWyrmthalak 210250-210289 of modules/mod-dungeon-bosses
src/BlackrockSpire/BlackrockSpireRework.h; WyrmthalakLogic.h names the same ids; its creatures: the three champions
300708-300710, the Worg Rider 300711, the tribe thrower 300712). The engine side is
src/BlackrockSpire/boss_overlord_wyrmthalak_rework.cpp; his texts 0-9 are the core SQL rev
rev_wyrmthalak_blackrock_spire.sql (lines 7-9 are the hard mode's, WP-B9).

- 9568 Overlord Wyrmthalak: bound to boss_overlord_wyrmthalak_rework (SmartAI off; the stock C++ script
  boss_overlord_wyrmthalak stays registered, unbound by this data: Demoralizing Shout, both Knock Aways and the 51%
  summons are retired, Cleave 20691 stays), normal 200k at 5 players (HealthModifier 65.531 on the level 60 warrior
  class base 3,052; the flex scaler multiplies it at the pull), stun immune (1972), INSTANCE_BIND, DamageModifier 3.5
  (the stock value; the live 7 is a mod-progression leftover). Heroic 260k and the tier's melee are WP-H's; the hard
  mode's 400k is B9's script. His loot rows are L-1's.
- 300708-300710 the champions (WT4): Spirestone (ogre, Spirestone Warlord's display 11582), Smolderthorn (troll,
  Smolderthorn Berserker's 7803), Bloodaxe (orc, Bloodaxe Raider's 9602, mounted on the dire wolf 14334 by the
  script), each at a larger scale. Level 60 elite warriors, 25,000 at 5 players (HealthModifier 8.191349 on 3,052;
  heroic 32,000 is WP-H's `_KIT_ADD_HEROIC`; the scaler multiplies both at their pull), DamageModifier 3.5 (the stock
  pair's), melee only, stun immune (1972). npc_brs_wyrmthalak_champion. Heroic entries 310291-310293 (WP-H's predicted
  lock lines; generate.py --check prints the real ones if the wave 1 adds mint in another order).
- 300711 Bloodaxe Worg Rider (WT7): the passing effect unit (orc 9602 on the dire wolf 14334, mounted by its script
  npc_brs_bloodaxe_worg_rider), not attackable on normal and heroic (UNIT_FLAG_NON_ATTACKABLE | IMMUNE_TO_PC |
  IMMUNE_TO_NPC); the hard mode (B9, WT12) keeps some and makes them attackable 6,000 adds (HealthModifier 1.965924;
  heroic entry 310294 with 6,000, WP-H's).
- 300712 Tribe Thrower: the invisible caster in the lower hall (boulders) and on the ramp (axes), and the stalker under
  each black flame patch. KIT_HELPER, the stalker display 11686, the trigger bit (hidden: it draws no beam). No heroic
  row (a helper).

Spells (looks from ._visuals, WP-V-1's WT_* picks; every look unconfirmed until seen in game):

  210250  Black Dragonfire   WT1 the 2 s rear-up bar (Fire, not interruptible; Shadow Flame 22539's SV 6559 plays its
                             breath over the 2 s, the stock spell's own 2 s cast)
  210251  Black Dragonfire   WT1 the breath's hit (resolve copy, Fire): 35% / 45%, Weakened, non-tanks (a Frontal)
  210252  Dragonfire Burn    WT1b heroic: the burn's tick (resolve copy, Fire), 5% a second, the tank too
  210253  Black Flame        WT1b the burning ground: a DUMMY aura on a tribe thrower stalker with V-1's Ascension
                             shadow patch (SV 90601, a STATE); B9's Shadowflame Spit patches (WT16) reuse it
  210254  Tail Swipe         WT2 the swipe's hit (resolve copy, Physical): 20% / 25%, Weakened; the knockback is the
                             script's (Unit::KnockbackFrom, 10 yd away from him)
  210255  Tail Swipe         WT2 his tail sweep (Tail Sweep 15847's SV 3879, on himself)
  210256  Boulder            WT5 a boulder's landing (resolve copy, Physical): 25% / 30%, Weakened
  210257  Boulder            WT5 the boulder in flight (a DUMMY at a destination, Boulder 9483's missile SV 1506,
                             25 yd/s: the farthest ledge point in the 2.5 s warning)
  210258  Axe Volley         WT6 the axes' landing (resolve copy, Physical): 25% / 30%, Weakened, the others near a
                             marked player
  210259  Axe Volley         WT6 the 4 s mark on a player (Axe Flurry 24018's SV 7163)
  210260  Throw Axe          WT6 an axe in flight (Throw Axe 16075's missile SV 3962, 20 yd/s)
  210261  Worg Riders        WT7 a rider's lane (resolve copy, Physical): 30% / 35%, Weakened; knocked 5 yd aside by
                             the script
  210262  Worg Charge        WT7 the rider's charge (Charge 22911's SV 3783, on the rider)
  210263  Overlord's Fury    WT8 heroic: +15% damage done, +10% attack speed per stack, 3 stacks (Fire Shield SV 8581,
                             V-1's lasting pick; Bestial Wrath's SV 7278 is a one-shot flash)
  210264  Mortal Strike      WT18 10 players: 30% of the tank row (the kit's percent spell; Mortal Strike's SV 39)
  210265  Mortal Wounds      WT18 -10% healing taken per stack, 15 s, refreshed by each stack, no cap
  210266-210289 spare.

Tooltips are number-free where the number is a reference percent (Systems.md s10).
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
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
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
    DISPLAY_BLOODAXE_CHAMPION,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_SMOLDERTHORN_CHAMPION,
    DISPLAY_SPIRESTONE_CHAMPION,
    SV_SPIT_PATCH_STATE,
    WT_AXE_FLURRY,
    WT_BOULDER,
    WT_CHARGE,
    WT_OVERLORDS_FURY,
    WT_SHADOW_FLAME_BREATH,
    WT_TAIL_SWEEP,
    WT_THROW_AXE,
)

_B8 = 'Blackrock Spire build WP-B8 (Overlord Wyrmthalak)'
_SCRIPT_REFFLAT = ('Blackrock Spire: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

creature_template_columns(9568, **boss_columns(
    'boss_overlord_wyrmthalak_rework', 65.531, damage_modifier=3.5,
))

# --- shared bits -----------------------------------------------------------------------------------------------------

_FLAGS_EXTRA_NO_XP = 0x40
_FLAGS_EXTRA_TRIGGER = 0x80
# UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_IMMUNE_TO_PC | UNIT_FLAG_IMMUNE_TO_NPC: the riders pass; nobody fights them
# (the hard mode, B9, clears these on the riders it keeps).
_UNIT_FLAGS_RIDER = 0x2 | 0x100 | 0x200
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_TARGET_FLAG_UNIT = 0x2
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a debuff never outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127
_DEFENSE_MELEE = 2

# Icons of the stock spells the looks come from (Spell.dbc, the working copy).
_ICON_SHADOW_FLAME = 937            # Shadow Flame 22539
_ICON_TAIL_SWEEP = 1525             # Tail Sweep 15847
_ICON_BOULDER = 2305                # Boulder 9483
_ICON_THROW_AXE = 1529              # Throw Axe 16075
_ICON_AXE_FLURRY = 1474             # Axe Flurry 24018
_ICON_CHARGE = 457                  # Charge 22911
_ICON_FIRE_SHIELD = 31              # Fire Shield 35265
_ICON_MORTAL_STRIKE = 564           # Mortal Strike 16856
_SV_MORTAL_STRIKE = 39              # Mortal Strike 16856

# WyrmthalakLogic.h: kBreathCastMs, kBoulderMissileSpeed, kAxeMissileSpeed, kAxeWarnMs, kFury*, kMortal*.
_BREATH_CAST_MS = 2000
_BOULDER_MISSILE_SPEED = 25.0
_AXE_MISSILE_SPEED = 20.0
_AXE_MARK_MS = 4000
_FURY_DAMAGE_PCT = 15
_FURY_HASTE_PCT = 10
_FURY_MAX_STACKS = 3
_MORTAL_STRIKE = (3000, 3000)       # kMortalStrikeTankPct 30 (hundredths; RefFlatOn: the tank row on the tank)
_MORTAL_WOUNDS_MS = 15000
_MORTAL_WOUNDS_HEALING_PCT = -10
_MORTAL_WOUNDS_MAX = 255            # "no cap" (the aura's own limit)

# --- the champions, the rider, the thrower ---------------------------------------------------------------------------

# Level 60 elite warriors: ceil(3,052 x 8.191349) = 25,000 (heroic 32,000: blackrock_spire.py `_KIT_ADD_HEROIC`).
_CHAMPION_HEALTH_MODIFIER = 8.191349
_CHAMPION_SCALE = 1.25


def _champion_columns(heroic_entry: int) -> dict:
    """A champion's columns (its heroic entry: WP-H's predicted lock line). Each champion is declared with a literal
    creature_template(<entry>, ...) call: blackrock_spire.py finds the declared kit adds by that pattern."""
    return {
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': _CHAMPION_HEALTH_MODIFIER, 'DamageModifier': 3.5, 'BaseAttackTime': 2000,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0,
        'maxgold': 0, 'ScriptName': 'npc_brs_wyrmthalak_champion', 'difficulty_entry_1': heroic_entry,
    }


spirestone_champion_300708 = creature_template(300708, 'Spirestone Champion', **_champion_columns(310291))
creature_model(300708, display_id=DISPLAY_SPIRESTONE_CHAMPION, scale=_CHAMPION_SCALE)
smolderthorn_champion_300709 = creature_template(300709, 'Smolderthorn Champion', **_champion_columns(310292))
creature_model(300709, display_id=DISPLAY_SMOLDERTHORN_CHAMPION, scale=_CHAMPION_SCALE)
bloodaxe_champion_300710 = creature_template(300710, 'Bloodaxe Champion', **_champion_columns(310293))
creature_model(300710, display_id=DISPLAY_BLOODAXE_CHAMPION, scale=_CHAMPION_SCALE)

# The rider: 6,000 when the hard mode keeps it (ceil(3,052 x 1.965924) = 6,000; heroic 6,000: `_KIT_ADD_HEROIC`).
bloodaxe_worg_rider_300711 = creature_template(
    300711, 'Bloodaxe Worg Rider', **{
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'unit_flags': _UNIT_FLAGS_RIDER,
        'HealthModifier': 1.965924, 'DamageModifier': 1.0, 'BaseAttackTime': 2000,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0,
        'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_brs_bloodaxe_worg_rider',
        'difficulty_entry_1': 310294,
    },
)
creature_model(300711, display_id=DISPLAY_BLOODAXE_CHAMPION)

tribe_thrower_300712 = creature_template(
    300712, 'Tribe Thrower', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
                                'flags_extra': _FLAGS_EXTRA_NO_XP | _FLAGS_EXTRA_TRIGGER, 'ScriptName': ''},
)
creature_model(300712, display_id=DISPLAY_INVISIBLE_STALKER)

# --- WT1 Black Dragonfire, WT1b the burn -----------------------------------------------------------------------------

dragonfire_bar_210250 = cast_bar(
    210250, 'Black Dragonfire', _BREATH_CAST_MS, 'Wyrmthalak draws a breath of black flame.',
    f'{_B8}, WT1: the 2 s rear-up bar (emote line 1 "%s draws a breath of black flame!"), 8 s after the pull, then '
    'every 15 s (the cast queue). DUMMY on the caster, not interruptible (InterruptFlags 0, PreventionType 0), Fire: '
    'a school the hard mode\'s Caustic Roar (Nature, the interruptible cast) does not use. Shadow Flame 22539\'s SV '
    '6559 (its own 2 s cast: the breath) plays over the bar. The registry Frontal owns the hit.',
    icon=_ICON_SHADOW_FLAME, visual=WT_SHADOW_FLAME_BREATH, school=School.FIRE,
)

black_dragonfire_210251 = resolve_copy(
    210251, 'Black Dragonfire', School.FIRE, 'Black dragonfire scorches everyone in front of Wyrmthalak.',
    f'{_B8}, WT1: the breath\'s hit, a 60 degree, 25 yd Frontal in front of him (his victim exempt): 35% (heroic 45%) '
    'of the reference row and 1 Weakened on every other player inside. Copy of the mod-boss-mechanics resolve spell '
    '205001 (Fire). Shadow Flame 22539\'s SV 6559 (the breath and a per-unit burn state) on every unit hit.',
    icon=_ICON_SHADOW_FLAME, visual=WT_SHADOW_FLAME_BREATH,
)

dragonfire_burn_210252 = resolve_copy(
    210252, 'Dragonfire Burn', School.FIRE, 'The ground burns with black dragonfire.',
    f'{_B8}, WT1b (heroic): the breath\'s cone keeps burning for 8 s (20 yd), its first tick 3 s after it appears: 5% '
    'of the reference row a second to everyone inside, the tank too (its own row, ruling 49), no Weakened. The hard '
    'mode (B9) stretches it to 120 s on the whole cone after the Smolderthorn Champion dies. Copy of the resolve '
    'spell 205001 (Fire), no look of its own (the patches are 210253; the breath\'s kit would replay on him every '
    'tick).',
    icon=_ICON_SHADOW_FLAME,
)

black_flame_210253 = spell(
    id=210253, name='Black Flame', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHADOW_FLAME,
    notes=f'{_B8}, WT1b: the burning ground, a DUMMY aura a tribe thrower stalker 300712 casts on itself (triggered) '
          'under each of a burn\'s four patch spots (one over the open edge is skipped: no floor); the stalker '
          'despawns when the burn goes out, which ends it. V-1\'s Ascension shadow patch '
          '(mannoroth_gooflowshadow_state_projected at scale 0.5, about 8.9 yd across; SV 90601, a STATE). B9\'s '
          'Shadowflame Spit patches (WT16, "patches look like the breath burn") reuse it through '
          'WyrmthalakFight::SpawnFlamePatch. It reaches nobody: the registry burn owns the damage.',
    raw_overrides=kit_raw('Black dragonfire burns here.', 'Black dragonfire burns here.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=SV_SPIT_PATCH_STATE),
)

# --- WT2 Tail Swipe --------------------------------------------------------------------------------------------------

tail_swipe_210254 = resolve_copy(
    210254, 'Tail Swipe', School.NORMAL, 'Wyrmthalak sweeps his tail behind him.',
    f'{_B8}, WT2: the swipe\'s hit, a 120 degree, 15 yd cone behind him that stays up the whole fight (the bots keep '
    'off his back) and resolves 5 s after the pull, then every 12 s: 20% (heroic 25%) of the reference row (the tank '
    'its own row), 1 Weakened, and a 10 yd knockback away from him (the script\'s Unit::KnockbackFrom; along the '
    'ledge\'s open edge it throws a player into the lower hall). Copy of the resolve spell 205001 (Physical), no look '
    '(his sweep is 210255; the knockback shows the hit).',
    icon=_ICON_TAIL_SWEEP,
)

tail_sweep_look_210255 = self_visual(
    210255, 'Tail Swipe', WT_TAIL_SWEEP,
    f'{_B8}, WT2: his tail sweep, cast on himself (triggered) as each swipe resolves. Tail Sweep 15847\'s SV 3879 '
    '(the animation and a small splat).',
    icon=_ICON_TAIL_SWEEP,
)

# --- WT5 Boulders ----------------------------------------------------------------------------------------------------

boulder_210256 = resolve_copy(
    210256, 'Boulder', School.NORMAL, 'A boulder heaved from the hall below crushes the ground.',
    f'{_B8}, WT5 (the Spirestone\'s answer): a boulder\'s landing, a 4 yd circle at a random player\'s spot 2.5 s '
    'after its shadow appears (3 at 5 players, 6 at 6 or more): 25% (heroic 30%) of the reference row (the tank its '
    'own row), 1 Weakened. Copy of the resolve spell 205001 (Physical), no look (the missile 210257 lands on the '
    'spot).',
    icon=_ICON_BOULDER,
)

boulder_missile_210257 = spell(
    id=210257, name='Boulder', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_BOULDER,
    notes=f'{_B8}, WT5: the boulder in flight, cast by a tribe thrower 300712 in the lower hall (triggered) at the '
          'circle\'s centre, timed to land with the circle. Boulder 9483\'s Throw Rock missile (SV 1506) at 25 yd/s '
          '(the farthest ledge point is about 50 yd from the thrower: inside the 2.5 s warning). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=WT_BOULDER, Speed=_BOULDER_MISSILE_SPEED,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- WT6 Axe Volley --------------------------------------------------------------------------------------------------

axe_volley_210258 = resolve_copy(
    210258, 'Axe Volley', School.NORMAL, 'Axes rain on everyone near the marked.',
    f'{_B8}, WT6 (the Smolderthorn\'s answer): the axes land on the marked players (2 at 5 players, 4 at 6 or more, '
    'non-tanks), 4 s after the mark: every other player within 6 yd of a marked one takes 25% (heroic 30%) of the '
    'reference row (the tank its own row) and 1 Weakened (a registry RunOut). Copy of the resolve spell 205001 '
    '(Physical), no look (the axe missiles 210260 land on the marked).',
    icon=_ICON_THROW_AXE,
)

axe_mark_210259 = spell(
    id=210259, name='Axe Volley', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_AXE_MARK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_AXE_FLURRY,
    notes=f'{_B8}, WT6: the mark, cast by him (triggered) on each marked player: 4 s, the axes land when it ends. A '
          'DUMMY aura (the tell; the registry RunOut names the same players for the bots). Axe Flurry 24018\'s SV '
          '7163 (a dust whirl; RISKY, V-1). Dispel none, NO_IMMUNITIES, dropped on a map change, removed with the '
          'fight.',
    raw_overrides=kit_raw('Trolls on the ramp have marked you: move away from everyone else.',
                          'Marked by the Smolderthorn: move away from your allies.', CastingTimeIndex=1,
                          SpellVisualID_1=WT_AXE_FLURRY, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

throw_axe_210260 = spell(
    id=210260, name='Throw Axe', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_THROW_AXE,
    notes=f'{_B8}, WT6: an axe in flight, cast by a tribe thrower 300712 on the ramp (or, in the hard mode, the '
          'Smolderthorn Champion: B9\'s AxeThrower) at each marked player (triggered), timed to land with the '
          'RunOut. Throw Axe 16075\'s missile (SV 3962) at 20 yd/s. Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=WT_THROW_AXE, Speed=_AXE_MISSILE_SPEED,
                          Targets=_TARGET_FLAG_UNIT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- WT7 Worg Riders -------------------------------------------------------------------------------------------------

worg_riders_210261 = resolve_copy(
    210261, 'Worg Riders', School.NORMAL, 'Bloodaxe riders charge across the ledge.',
    f'{_B8}, WT7 (the Bloodaxe\'s answer): a rider\'s lane, 4 yd wide from the ramp head across the ledge through a '
    'random player\'s spot (2 riders at 5 players, 4 at 6 or more), 3 s of the lane marker, then the charge passes '
    'at 25 yd/s: 30% (heroic 35%) of the reference row (the tank its own row), 1 Weakened, and knocked 5 yd aside '
    '(the script). Copy of the resolve spell 205001 (Physical), no look (the rider is the look).',
    icon=_ICON_CHARGE,
)

worg_charge_210262 = self_visual(
    210262, 'Worg Charge', WT_CHARGE,
    f'{_B8}, WT7: the rider\'s charge, cast by the rider on itself (triggered) as it bursts off the ramp head. Charge '
    '22911\'s SV 3783 (a trail; V-1\'s StunSwirl note: a self-cast DUMMY applies no aura, but check in game that no '
    'stun stars show on the rider).',
    icon=_ICON_CHARGE,
)

# --- WT8 Overlord's Fury (heroic) ------------------------------------------------------------------------------------

overlords_fury_210263 = spell(
    id=210263, name='Overlord\'s Fury', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=_FURY_DAMAGE_PCT,
               die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Overlord\'s Fury: a flat +15% damage done per stack, not a damage or heal value'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=_FURY_HASTE_PCT,
               die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Overlord\'s Fury: a flat +10% attack speed per stack, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_FIRE_SHIELD,
    notes=f'{_B8}, WT8 (heroic, not the hard mode): each champion\'s death gives him a permanent stack '
          '(DungeonKit::AddStacks, CumulativeAura 3): +15% damage done (every school) and +10% attack speed. The '
          'reference-sized hits ignore caster modifiers, so it raises his melee and Cleave. Not dispellable; removed '
          'on his death, evade and reset. Fire Shield 35265\'s whirl (SV 8581, V-1\'s lasting pick).',
    raw_overrides=kit_raw('Every fallen champion feeds the Overlord\'s fury.', 'Damage done and attack speed '
                          'increased.', instant=True, CumulativeAura=_FURY_MAX_STACKS, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=WT_OVERLORDS_FURY),
)

# --- WT18 Mortal Strike and Mortal Wounds (10 players) ---------------------------------------------------------------

mortal_strike_210264 = spell(
    id=210264, name='Mortal Strike', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_MORTAL_STRIKE[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_MORTAL_STRIKE,
    notes=f'{_B8}, WT18 (10 players only, ruling 64): 8 s after the pull, then every 8 s on his victim in reach (cast '
          'by him, triggered, with 210265 after it): 30% of the tank row (3000 hundredths, both difficulties; '
          'RefFlatOn: 1,113 normal / 1,233 heroic on a tank), Physical. Always hits, cannot crit, ignores his '
          'modifiers (Overlord\'s Fury never raises it; the tank\'s own defensives count). Mortal Strike 16856\'s '
          'SV 39.',
    raw_overrides=kit_raw('A brutal strike that leaves a mortal wound.', instant=True, InterruptFlags=0,
                          PreventionType=0, DefenseType=_DEFENSE_MELEE, EffectMiscValueB_1=_MORTAL_STRIKE[1],
                          SpellVisualID_1=_SV_MORTAL_STRIKE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(mortal_strike_210264, 'spell_dungeon_refflat_damage')

mortal_wounds_210265 = spell(
    id=210265, name='Mortal Wounds', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_MORTAL_WOUNDS_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_PCT,
                    base_points=_MORTAL_WOUNDS_HEALING_PCT, die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Mortal Wounds: a flat -10% healing taken per stack, not a damage or heal value')],
    spell_icon_id=_ICON_MORTAL_STRIKE,
    notes=f'{_B8}, WT18 (10 players only): a stack with every Mortal Strike, cast by him (triggered; the caster counts '
          'for the bots\' taunt swap, which reads the stacks he put on each tank): -10% healing taken per stack, '
          '15 s, each stack refreshing it, no cap (CumulativeAura 255). The bots swap at 3 and, by the user\'s '
          'ruling, a tank taunts only once its own stacks are gone: 15 s is under two strikes (16 s), so the old '
          'tank is always clear by the new holder\'s third. Not dispellable, dropped on a map change, removed with '
          'the fight. No look (the strike is the look).',
    raw_overrides=kit_raw('Healing taken reduced.', 'Healing taken reduced.', CastingTimeIndex=1,
                          CumulativeAura=_MORTAL_WOUNDS_MAX, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
