"""
Blackrock Spire build WP-B2: Shadow Hunter Vosh'gajin (9236), "Voodoo Dolls", normal and heroic
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows VG, s3.5 row B2, s3.6; build spec
docs/dungeons/blackrock-spire-rework.md SP 815-1021, rulings 24-28). WP-B2 owns this file (its spells:
kSpellsVoshgajin 210060-210089 of modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h only;
VoshgajinLogic.h names the same ids).

- 9236 Vosh'gajin: boss_shadow_hunter_voshgajin_rework (SmartAI off: the S0 SQL rev drops her Hex and Curse of Blood
  rows), the build spec's normal health (174k = HealthModifier 75.751 on the level 58 paladin class base 2,297),
  DamageModifier 3.5 (the stock value: the live 8 is a mod-progression leftover), stun immunity 1972 (SP: stun immune),
  INSTANCE_BIND. Heroic 230k is WP-H's override (source/world/dungeons/blackrock_spire.py). Hex 16097 and Curse of Blood
  16098 are retired from her kit (Squeeze's hex and Bound replace them); the two Shadow Priests 43550 and 43551 leave
  with this WP's SQL rev. Her Snakestone drop (13352 at 100%) is untouched.
- 300703 Voodoo Doll: display 25017 (ragdoll_02, scale 1), rooted on her dais, not selectable and not attackable
  (KIT_HELPER), no loot. The boss summons it (two at 6 or more players), swells it to scale 2 through each tell and
  despawns it; it runs npc_brs_voodoo_doll (NullCreatureAI). No heroic template (handoff s7 #23).

Spells. Every torment's hit is a dungeon copy of the mod-boss-mechanics resolve spell (the registry's percent of the
reference row; the combat log names the mechanic); Bound's pins and Hex of Agony are the kit's generic percent DoT
(spell_dungeon_refflat_periodic). The rest is the doll's tells and strings, the looks, and the 2 s hex:

  210060  Puppet Strings      VG1 the doll's channel on the Bound player, a DUMMY aura on them, 20 s ceiling (the script
                              cuts it at the binding's end: 18 s, or just past the last torment's landing)
  210061  Bound               VG2 the Curse: a pin every 2 s, 5% of the reference row (periodic, hundredths, heroic the
                              same), Dispel Curse (a reward: it stops the pins, the string stays), 20 s ceiling
  210062  Doll Swell          VG6 +100% size on the doll for the 3 s of a tell
  210063  Voodoo Flames       VG3 tell: the doll catches fire (3 s state look on the doll)
  210064  Needle              VG4 tell: a crystal spike rises at the doll (3 s state look on the doll)
  210065  Squeeze             VG5 tell: a shadow shell closes round the doll (3 s state look on the doll)
  210066  Voodoo Flames       VG3 the burst's hit: resolve copy (Fire), 30% / 35% Weakened, the Bound player 10%
  210067  Voodoo Flames       VG3 the patch's tick: resolve copy (Fire), 10% a second, one Weakened per player per patch
  210068  Needle              VG4 the line's hit: resolve copy (Physical), 40% / 50%, no Weakened; the Bound player 10%
  210069  Squeeze             VG5 the donut's hit: resolve copy (Shadow), 25% / 30% Weakened, with the Hexed rider
  210070  Hexed               VG5 / VG7 the 2 s hex (the stock Hex 16097's frog and confusion), mechanic Polymorph
  210071  Hex of Agony        VG7 heroic: 4% a second, 8 s, Dispel Magic (expected)
  210072  Hex of Agony        VG7 heroic: the expiry burst's hit: resolve copy (Shadow), 40% with the Hexed rider
  210073  Pin                 VG2 the pin's look (no effect), cast by the doll on the Bound player every 2 s
  210074  Needle Spine        VG4 the needle's flight from the doll to the Bound player (look)
  210075  Hex of Agony        VG7 the skull look, re-cast every 3 s over the 8 s (look)
  210076-210089 spare.

Visual ids are WP-V-1's (._visuals), the copies' stock impacts included (SV 143 Fire Blast's chest flash, 45 Shadow
Burst's, 39 Gore's, 876 Curse of Blood's state): every one exists in the working-copy SpellVisual.dbc (checked
2026-11-15). Every look is unconfirmed until seen in game. Tooltips are number-free (SP
checklist item 8).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_VOODOO_DOLL,
    VG_CURSE_OF_BLOOD_STATE,
    VG_FIRE_BLAST_IMPACT,
    VG_GORE_IMPACT,
    VG_HEX,
    VG_HEX_OF_AGONY,
    VG_NEEDLE_SPINE,
    VG_NEEDLE_TELL,
    VG_PIN,
    VG_PUPPET_STRINGS,
    VG_SHADOW_BURST_IMPACT,
    VG_SHADOW_PRISON,
    VG_VOODOO_FLAMES,
)

creature_template_columns(9236, **boss_columns(
    'boss_shadow_hunter_voshgajin_rework', 75.751, damage_modifier=3.5,
))

_VG = 'Blackrock Spire build WP-B2 (Shadow Hunter Vosh\'gajin)'

_SCRIPT_REFFLAT = ('Blackrock Spire: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')

_ATTR1_IS_CHANNELED = 0x00000004
_DEFENSE_MAGIC = 1
_MECHANIC_POLYMORPH = 17
_DISPEL_MAGIC = 1
_DISPEL_CURSE = 2
_HEX_FROG_MISC = 7552                        # Hex 16097's transform (EffectMiscValue_1)
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000      # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_BOUND_PIN = 500                             # VoshgajinLogic.h kPinPct 5 (hundredths)
_HEX_OF_AGONY_TICK = 400                     # kHexOfAgonyPct 4 (hundredths)
_BIND_CEILING_MS = 20000                     # the script ends the strings and the Curse at the binding's hold
_TELL_MS = 3000                              # kTellMs
_HEXED_MS = 2000                             # kHexedMs
_HEX_OF_AGONY_MS = 8000                      # kHexOfAgonyMs
_NEEDLE_SPEED = 24.0                         # Needle Spine 39835's missile speed

_ICON_PUPPET_STRINGS = 1958                  # Puppet Strings 62377
_ICON_CURSE_OF_BLOOD = 130                   # Curse of Blood 16098
_ICON_VOODOO_DOLL = 2543                     # Voodoo Doll 52695
_ICON_VOODOO_FLAMES = 2375                   # Voodoo Flames 54795
_ICON_NEEDLE = 285                           # Needle Spine 39835
_ICON_SHADOW_PRISON = 92                     # Shadow Prison 33071
_ICON_HEX = 3058                             # Hex 16097
_ICON_HEX_OF_AGONY = 544                     # Hex of Agony 52647
_ICON_PIN = 2679                             # Pin 50245

# --- 300703 Voodoo Doll ----------------------------------------------------------------------------------------------

voodoo_doll_300703 = creature_template(
    300703, 'Voodoo Doll', **{
        **KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 7,
        'ScriptName': 'npc_brs_voodoo_doll',
    },
)
creature_model(300703, display_id=DISPLAY_VOODOO_DOLL)

# --- VG1 Bind --------------------------------------------------------------------------------------------------------

puppet_strings_210060 = spell(
    id=210060, name='Puppet Strings', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_BIND_CEILING_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_PUPPET_STRINGS,
    notes=f'{_VG}, VG1 Bind: the Voodoo Doll\'s channel on the player it is bound to (boss emote line 1), cast by the '
          'doll (triggered) as the binding starts: Puppet Strings 62377\'s channel kit (SV 13152, a thin rope from the '
          'doll to the player). A DUMMY aura on the player and no damage (the pins are Bound\'s). The 20 s here is a '
          'ceiling: boss_shadow_hunter_voshgajin_rework interrupts the channel at the binding\'s end (18 s, or just '
          'past the last torment\'s landing: the normal third slot lands at 19 s). It stays when Bound is cured. '
          'Needle\'s line runs along it, and Needle\'s eligibility reads it (the bound player is never on his own '
          'line, cured or not). Ignores line of sight. Not dispellable.',
    raw_overrides=kit_raw('The doll\'s strings are tied to you. What is done to the doll is done to you.',
                          'Bound to a voodoo doll.', CastingTimeIndex=1, InterruptFlags=0, ChannelInterruptFlags=0,
                          PreventionType=0, SpellVisualID_1=VG_PUPPET_STRINGS,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- VG2 Bound -------------------------------------------------------------------------------------------------------

bound_210061 = spell(
    id=210061, name='Bound', school=School.SHADOW, dispel=_DISPEL_CURSE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_BIND_CEILING_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=_BOUND_PIN,
                    die_sides=0, amplitude=2000, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CURSE_OF_BLOOD,
    notes=f'{_VG}, VG2 Bound (the stock Curse of Blood 16098 reworked): the pins on the player the doll is bound to, '
          'put on by boss_shadow_hunter_voshgajin_rework (AddAura, the boss as caster; the aura\'s length is set by '
          'the script to the binding\'s hold: 18 s, or until just past the last torment\'s landing). Every 2 s 5% of '
          'the reference non-tank row (base point 500 hundredths, heroic the same: EffectMiscValueB 500), Shadow, '
          'through spell_dungeon_refflat_periodic; ignores caster modifiers. NO_IMMUNITIES (a Divine Shield or an Ice '
          'Block does not keep a player out of the doll\'s hands; the dispel still works). A Curse: the dispel list, '
          'priority 1 (a reward, SP: removing it stops the pins, the torments still come, the string stays). Needle\'s '
          'eligibility reads Puppet Strings 210060, not this (a cured player is still never on his own line). Curse '
          'of Blood\'s SV 876 '
          '(curse hands and the lasting curse state); the pin look per tick is 210073. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Cursed to take the doll\'s pins. Cure the curse to stop them.',
                          'The doll is pinned for you. Taking damage every $t1 sec.', CastingTimeIndex=1,
                          DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=_BOUND_PIN,
                          SpellVisualID_1=VG_CURSE_OF_BLOOD_STATE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(bound_210061, 'spell_dungeon_refflat_periodic')

pin_210073 = spell(
    id=210073, name='Pin', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_PIN,
    notes=f'{_VG}, VG2: the look of a pin, cast by the doll (triggered) on every player carrying Bound each 2 s, '
          'beside the Curse\'s tick (the aura\'s own tick plays no impact). Pin 50245\'s SV 5287 (the '
          'slowing-strike impact and its base state). No effect, no damage.',
    raw_overrides=kit_raw('A pin in the doll.', instant=True, InterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=VG_PIN, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- VG6 The tells ---------------------------------------------------------------------------------------------------

doll_swell_210062 = spell(
    id=210062, name='Doll Swell', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_TELL_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SCALE, base_points=100, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_VOODOO_DOLL,
    notes=f'{_VG}, VG6 (ruling 27): the Voodoo Doll swells to scale 2 (+100% size, SPELL_AURA_MOD_SCALE) for the 3 s '
          'of a tell, so it reads from anywhere in the hall. Cast by the boss script on the doll (triggered) at each '
          'tell start; it ends by itself with the tell (a second cast within the 3 s refreshes it). No look of its '
          'own.',
    raw_overrides=kit_raw('The doll swells.', 'The doll is swollen.', instant=True, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)


def _tell(spell_id: int, name: str, visual: int, icon: int, torment: str, look: str):
    """A tell: a 3 s DUMMY aura on the doll that carries a state look (ruling 28: Base effects only)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_TELL_MS,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'{_VG}, VG6 {torment}\'s tell: the doll shows {look} for the 3 s before the hit lands, cast by the boss '
              'script on the doll (triggered) with the swell (210062); the registry mechanic beside it (a hidden one, '
              'ruling 25: no ground marker) lands as it ends. A DUMMY aura on the doll, no damage. Both dolls show '
              'the same tell at 6 or more players; heroic twin torments cast two tells on the doll at once.',
        raw_overrides=kit_raw(f'The doll shows {look}.', f'The doll shows {look}.', instant=True,
                              SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


flames_tell_210063 = _tell(
    210063, 'Voodoo Flames', VG_VOODOO_FLAMES, _ICON_VOODOO_FLAMES, 'Voodoo Flames',
    'fire (Voodoo Flames 54795\'s SV 11668: the dark fire force shield state, settled by ruling 28)',
)
needle_tell_210064 = _tell(
    210064, 'Needle', VG_NEEDLE_TELL, _ICON_NEEDLE, 'Needle',
    'a crystal spike (Crystal Spike Pre-visual 50442\'s SV 11078: the ice spike state at scale 2, ruling 28)',
)
squeeze_tell_210065 = _tell(
    210065, 'Squeeze', VG_SHADOW_PRISON, _ICON_SHADOW_PRISON, 'Squeeze',
    'a shadow shell (Shadow Prison 33071\'s SV 8025: the shadow shield state, ruling 28)',
)

# --- VG3 Voodoo Flames -----------------------------------------------------------------------------------------------

flames_hit_210066 = resolve_copy(
    210066, 'Voodoo Flames', School.FIRE, 'Fire from the doll\'s burning.',
    f'{_VG}, VG3: the burst\'s hit: 30% (heroic 35%) of the row on everyone else within 8 yd of the Bound player (a '
    'hidden RunOut, the tank on its own row), 1 Weakened; the Bound player takes the same spell at 10% through the '
    'script (a RegistryHit, no Weakened). Copy of the resolve spell 205001 (Fire). Fire Blast 2136\'s SV 143 (a '
    'chest flash) on every unit hit: the visible impact (the doll\'s own look is the tell, 210063).',
    icon=_ICON_VOODOO_FLAMES, visual=VG_FIRE_BLAST_IMPACT,
)

patch_hit_210067 = resolve_copy(
    210067, 'Voodoo Flames', School.FIRE, 'The doll\'s fire burns on the ground.',
    f'{_VG}, VG3: the patch\'s tick: 10% of the row each second on everyone inside the 5 yd patch for 20 s (a '
    'persistent registry circle, the first tick a second after the burst), one Weakened per player per patch '
    '(WeakenedOncePerPlayer). Copy of the resolve spell 205001 (Fire). Fire Blast\'s SV 143 on every unit hit. The '
    'patch keeps its registry marker (the one lingering hazard of the fight).',
    icon=_ICON_VOODOO_FLAMES, visual=VG_FIRE_BLAST_IMPACT,
)

# --- VG4 Needle ------------------------------------------------------------------------------------------------------

needle_hit_210068 = resolve_copy(
    210068, 'Needle', School.NORMAL, 'A needle through the doll\'s string.',
    f'{_VG}, VG4: the line\'s hit: 40% (heroic 50%) of the row on everyone within 2 yd of the line from the doll to '
    'the Bound player (4 yd wide, both ends live), the tank on its own row, no Weakened (the hit is the penalty); '
    'nobody carrying Bound is eligible, the Bound player takes the same spell at 10% through the script (a '
    'RegistryHit). Copy of the resolve spell 205000 (Physical). Gore 4102\'s SV 39 (a hit flash and a sound) on '
    'every unit hit: the visible impact.',
    icon=_ICON_NEEDLE, visual=VG_GORE_IMPACT,
)

needle_flight_210074 = spell(
    id=210074, name='Needle Spine', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_NEEDLE,
    notes=f'{_VG}, VG4: the needle\'s flight down the string, cast by the doll (triggered) at the Bound player when '
          'the line resolves: Needle Spine 39835\'s SV 9061 (the naga shell missile, cast kit 7681 and impact kit '
          '7682) at its missile speed 24. No effect, no damage (the hits are the line\'s and the script\'s).',
    raw_overrides=kit_raw('A needle flies down the string.', instant=True, InterruptFlags=0, PreventionType=0,
                          Speed=_NEEDLE_SPEED, SpellVisualID_1=VG_NEEDLE_SPINE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- VG5 Squeeze and the hex -----------------------------------------------------------------------------------------

squeeze_hit_210069 = resolve_copy(
    210069, 'Squeeze', School.SHADOW, 'The doll is squeezed, and so are you.',
    f'{_VG}, VG5: the donut\'s hit: 25% (heroic 30%) of the row on everyone 5 to 25 yd from the Bound player (a '
    'hidden Donut), the tank on its own row, 1 Weakened, with the 2 s Hexed rider (210070). Copy of the resolve '
    'spell 205001 (Shadow). Shadow Burst 28447\'s SV 45 (a shadow burst on the chest) on every unit hit.',
    icon=_ICON_SHADOW_PRISON, visual=VG_SHADOW_BURST_IMPACT,
)

hexed_210070 = spell(
    id=210070, name='Hexed', school=School.SHADOW, dispel=0, mechanic=_MECHANIC_POLYMORPH,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_HEXED_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.TRANSFORM, base_points=0, die_sides=0,
               misc_value=_HEX_FROG_MISC, implicit_target_a=TARGET_UNIT_TARGET_ANY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_CONFUSE, base_points=0, die_sides=0,
               implicit_target_a=TARGET_UNIT_TARGET_ANY),
    ],
    spell_icon_id=_ICON_HEX,
    notes=f'{_VG}, VG5 / VG7: the one 2 s hex (the shared limit on loss of control; the stock Hex 16097 is 10 s) the '
          'Squeeze (210069) and the Hex of Agony burst (210072) apply as the registry\'s rider, cast by the boss on '
          'every unit hit: the stock Hex\'s two effects (Transform 7552, Confuse), mechanic Polymorph, so the player '
          'cannot attack or cast. Not dispellable (2 s is not worth a cure) and not NO_IMMUNITIES (a break is a '
          'reward). Hex 16097\'s SV 2295 (the polymorph impact and its sound). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Hexed: cannot attack or cast for $d.', 'Hexed.', CastingTimeIndex=1,
                          SpellVisualID_1=VG_HEX, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- VG7 Hex of Agony (heroic) ---------------------------------------------------------------------------------------

hex_of_agony_210071 = spell(
    id=210071, name='Hex of Agony', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_HEX_OF_AGONY_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=_HEX_OF_AGONY_TICK,
                    die_sides=0, amplitude=1000, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_HEX_OF_AGONY,
    notes=f'{_VG}, VG7 (heroic): on a random non-tank (two at 6 or more) every 20 s from 15 s, put on by the boss '
          'script (AddAura, the boss as caster): 4% of the reference non-tank row a second for 8 s (base point 400 '
          'hundredths, the tank row on the tank), Shadow, through spell_dungeon_refflat_periodic; ignores caster '
          'modifiers. A Magic dispel is the answer (the dispel list, priority 3, urgent 4 s before it ends): a '
          'dispelled hex is gone (the script cancels the burst); expired, it bursts 8 yd (210072) with the Hexed '
          'rider. Hex of Agony 52647\'s SV 10061 (the skull impact, a 3 s look: 210075 re-casts it every 3 s). '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Damage every second. When it ends, it bursts and hexes those near you.',
                          'Taking Shadow damage every $t1 sec. When it ends, it bursts.', CastingTimeIndex=1,
                          DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=_HEX_OF_AGONY_TICK,
                          SpellVisualID_1=VG_HEX_OF_AGONY, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(hex_of_agony_210071, 'spell_dungeon_refflat_periodic')

hex_burst_210072 = resolve_copy(
    210072, 'Hex of Agony', School.SHADOW, 'The hex bursts and the agony spreads.',
    f'{_VG}, VG7 (heroic): the burst when a Hex of Agony runs out (a registry RunOut on the carrier registered with '
    'the aura, cancelled when it is dispelled or the carrier dies): 40% of the heroic row on everyone within 8 yd of '
    'the carrier, the tank on its own row, no Weakened, with the Hexed rider. Copy of the resolve spell 205001 '
    '(Shadow). Shadow Burst 28447\'s SV 45 on every unit hit.',
    icon=_ICON_HEX_OF_AGONY, visual=VG_SHADOW_BURST_IMPACT,
)

hex_skull_210075 = spell(
    id=210075, name='Hex of Agony', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HEX_OF_AGONY,
    notes=f'{_VG}, VG7 (heroic): the skull look of Hex of Agony, cast by the boss (triggered) on every carrier every '
          '3 s over the 8 s (Hex of Agony 52647\'s skull is a 3 s impact kit: the 8 s aura shows it once, so the '
          'script re-casts it; VISUALS-REPORT RISKY). No effect, no damage.',
    raw_overrides=kit_raw('The skull of agony.', instant=True, InterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=VG_HEX_OF_AGONY, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
