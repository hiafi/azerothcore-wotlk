"""
Blackrock Depths build WP-D9: the Vault, "Security Breach": Watchman Doomgrip (9476) and the Vault Sentinels (300793,
the event's four Warbringer Constructs, spawns 46608, 46610, 46611, 46612, re-entered), normal and heroic
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 / s3.5 row D9 / s3.6 / s3.7 "The Vault" /
s7 #17; build spec docs/dungeons/blackrock-depths-2-shadowforge-city.md "The Vault", Build spec, rulings 42-45, 88).
WP-D9 owns this file (its spells: kSpellsVault 211090-211119 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h only; VaultLogic.h names the same ids; its creature: 300793). The engine
side is src/BlackrockDepths/boss_watchman_doomgrip_rework.cpp (Doomgrip, the sentinels, the Secret Safe's clock and
loot); the re-entered spawns, the texts and the Safe's ScriptName are
data/sql/updates/pending_db_world/rev_vault_blackrock_depths.sql.

- 9476 Watchman Doomgrip: boss_watchman_doomgrip_rework (SmartAI off: the S0 SQL rev dropped his three rows; the stock
  Sunder Armor and Drink Healing Potion are his own copies below, the potion retired), the build spec's normal health
  (110k = HealthModifier 54.294 on the level 54 paladin class base 2,026), DamageModifier 7.5 (the stock value; about
  240 a second at the stock swing), stun immunity 1972 (the spec's "stun immune"), no INSTANCE_BIND (no Vault
  credit row). Heroic 170k is WP-H's override (310375). Never spawned: the instance summons him at the alarm.
- 300793 Vault Sentinel: a boss-kit add, the Warbringer Construct's look (display 8289; Arcanoton shares it, a playtest
  look), mechanical (type 9: the stock construct is an elemental, which Banish would take out of the fight while its
  field stays), level 52 elite warrior class, 18,000 health (HealthModifier 7.5917 on 2,371), no melee of its own (it
  never attacks: DamageModifier 1), no loot, no XP, npc_brd_vault_sentinel. Stone and unselectable until its turn
  (the instance's freeze and the script's). It never moves (R-1-B B1): immunity set 1972 (fear and the other control
  mechanics); the script roots it and puts it back on its post after a grip or a knockback. Heroic 28,000 is WP-H's
  `_KIT_ADD_HEROIC` (difficulty_entry_1 310404, STAGE-H-REPORT section 3).

Spells. The registry hits (the fields' ticks, the sweep's cone) deal their damage through dungeon copies of the
mod-boss-mechanics resolve spell. The rest are looks, the link's reduction, his two stock beats as copies and the
draught:

  211090  Lockdown             VA1 the force field at the doorway: a lasting state on a stalker (Force Field Visual
                               34648's SV 8225)
  211091  Vault Sentinel       VA2 the wake look: a 3 s state on the sentinel (Awake 52875's SV 11519)
  211092  Security Field       VA3 the field's disc, the 6 yd rung (Ascension target_arcane_state_centeronly, SV 90653)
  211093  Security Field       VA3 7 yd (SV 90654), heroic growth
  211094  Security Field       VA3 8 yd (SV 90655)
  211095  Security Field       VA3 9 yd (SV 90656)
  211096  Security Field       VA3 a field's tick: resolve copy (Arcane), 5% / 8% a second, the tank too, no Weakened
  211097  Security Link        VA4 the beam from each awake sentinel to Doomgrip (a channel; Beam Link 62881's SV 13261)
  211098  Security Link        VA4 Doomgrip's -25% damage taken a stack, 3 stacks (75%) at most
  211099  Intruder Sweep       VA5 the 2 s bar (Physical, not kickable; Sweeping Slam 12887's SV 2717)
  211100  Intruder Sweep       VA5 the cone's hit: resolve copy (Physical), 25% / 40% + Weakened, the tank too
  211101  Sunder Armor         VA6 the stock beat with a real value: -5% armor a stack, 5 stacks, 30 s
  211102  Watchman's Draught   VA7 at 60% and 30%: heals 5% of his health, +20% damage for 15 s (Magic: purge it)
  211103  Stoned               the sentinels' dormant look (R-2-A MA-2): a lasting state, Stoned 10255's SV 1845.
                               A copy because the stock aura's EffectMechanic FREEZE is in immunity set 1972, which
                               drops it; this one has no mechanic and NO_IMMUNITIES. Look only: the dormant state is
                               the sentinel's NOT_SELECTABLE (the instance's freeze and the script)
  211104-211119 spare.

Visual ids are V-1's (._visuals VA_*, SV_SECURITY_FIELD, DISPLAY_VAULT_SENTINEL); every look is unconfirmed until seen
in game. Tooltips are number-free where a number would only repeat the build spec.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    TARGET_UNIT_TARGET_ENEMY,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    FACTION_DARK_IRON,
    IMMUNITY_BOSS_STUN,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    VA_SUNDER_ARMOR,
    DISPLAY_VAULT_SENTINEL,
    SV_SECURITY_FIELD,
    VA_INTRUDER_SWEEP,
    VA_LOCKDOWN,
    VA_SECURITY_LINK,
    VA_SENTINEL_WAKES,
    VA_WATCHMANS_DRAUGHT,
    security_field_rung,
)

creature_template_columns(9476, **boss_columns(
    'boss_watchman_doomgrip_rework', 54.294, damage_modifier=7.5, instance_bind=False,
))

_VA = 'Blackrock Depths build WP-D9 (the Vault, Watchman Doomgrip)'

_TYPE_MECHANICAL = 9
_SENTINEL_HEALTH_MODIFIER = 7.5917      # ceil(2,371 x 7.5917) = 18,000 at level 52 (the build spec's "about 18,000")
VAULT_SENTINEL_HEROIC_ENTRY = 310404    # heroic_ids.lock (STAGE-H-REPORT section 3); WP-H sets its 28,000

_DISPEL_MAGIC = 1
_DEFENSE_MELEE = 2
_SCHOOL_MASK_ALL = 127
_RESISTANCE_ARMOR = 1                   # MOD_RESISTANCE_PCT's EffectMiscValue: the armor "school" mask
_ATTR1_IS_CHANNELED = 0x00000004
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a map change or a logout drops it, so nothing outlives the instance.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# Icons (the working-copy Spell.dbc).
_ICON_FORCE_FIELD = 1918                # Force Field Visual 34648
_ICON_STONE = 93                        # Awaken 52875 / Stoneform 20594
_ICON_ARCANE = 122                      # Arcane Explosion 1449
_ICON_BEAM = 3262                       # Beam Link 62881
_ICON_SWEEPING_SLAM = 166               # Sweeping Slam 12887
_ICON_SUNDER = 565                      # Sunder Armor 11971
_ICON_POTION = 104                      # Drink Healing Potion 15504
_ICON_STONED = 220                      # Stoned 10255
_SV_STONED = 1845                       # Stoned 10255's SpellVisualID_1 (client Spell.dbc, read 2026-11-17)

# Numbers (VaultLogic.h).
_WAKE_LOOK_MS = 3000                    # kWakeLookMs
_SWEEP_WARN_MS = 2000                   # kSweepWarnMs
_LINK_PCT = 25                          # kLinkPctPerSentinel
_LINK_STACKS = 3                        # kLinkMaxStacks
_SUNDER_PCT = 5                         # kSunderArmorPct
_SUNDER_STACKS = 5                      # kSunderMaxStacks
_SUNDER_MS = 30000                      # kSunderMs
_DRAUGHT_HEAL_PCT = 5                   # kDraughtHealPct
_DRAUGHT_DAMAGE_PCT = 20                # kDraughtDamagePct
_DRAUGHT_MS = 15000                     # kDraughtMs
_MELEE_RANGE = 5.0


def _state_aura(spell_id: int, name: str, visual: int, duration_ms: int, icon: int, notes: str):
    """A hidden DUMMY aura on the caster that carries a SpellVisual's state kit for `duration_ms` (-1: until removed;
    a state kit needs an aura to play; not passive: a passive aura is never sent to the client)."""
    return spell(
        id=spell_id, name=name, school=School.ARCANE, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              CastingTimeIndex=1, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


# --- 300793 Vault Sentinel -------------------------------------------------------------------------------------------

vault_sentinel_300793 = creature_template(
    300793, 'Vault Sentinel', **{
        **kit_creature(faction=FACTION_DARK_IRON, type=_TYPE_MECHANICAL), 'minlevel': 52, 'maxlevel': 52, 'rank': 1,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': _SENTINEL_HEALTH_MODIFIER, 'DamageModifier': 1.0,
        'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
        'mingold': 0, 'maxgold': 0, 'detection_range': 0.0, 'ScriptName': 'npc_brd_vault_sentinel',
        'difficulty_entry_1': VAULT_SENTINEL_HEROIC_ENTRY,
        # R-1-B B1 (orchestrator default): it never moves. The kit's set 1972 covers fear (and every other control
        # mechanic); a grip or a knockback (effects, not mechanics) is undone by the script, which roots it and puts
        # it back on its post.
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
    },
)
creature_model(300793, display_id=DISPLAY_VAULT_SENTINEL)

# --- VA1 Lockdown ----------------------------------------------------------------------------------------------------

lockdown_211090 = _state_aura(
    211090, 'Lockdown', VA_LOCKDOWN, -1, _ICON_FORCE_FIELD,
    f'{_VA}, VA1: the force field across the room\'s doorway while the Vault runs: cast by the shared stalker 300796 '
    'on itself (triggered) at the doorway, facing out; the Secret Safe\'s script despawns it when the event ends (done '
    'or wiped). Force Field Visual 34648\'s SV 8225 (the Dire Maul field; its size and facing at the 7.8 yd doorway '
    'are a playtest look). Look only: the seal is the script (nobody may stand in the corridor past the doorway; a '
    'player there is put back in the room).',
)

# --- VA2 Vault Sentinel wakes ----------------------------------------------------------------------------------------

sentinel_wakes_211091 = _state_aura(
    211091, 'Vault Sentinel', VA_SENTINEL_WAKES, _WAKE_LOOK_MS, _ICON_STONE,
    f'{_VA}, VA2: a sentinel wakes (5 s after the alarm, then every 20 s, heroic 15 s; at once when nothing awake is '
    'left): cast by it on itself (triggered), 3 s. Awaken 52875\'s SV 11519 (stoneform shell, exploding stone; never '
    'Activate Construct SV 13174). Doomgrip says emote line 1.',
)

# --- VA3 Security Field ----------------------------------------------------------------------------------------------

security_field_looks = [
    _state_aura(
        211092 + i, 'Security Field', security_field_rung(radius), -1, _ICON_ARCANE,
        f'{_VA}, VA3: the field\'s disc, the {radius} yd rung (SV {SV_SECURITY_FIELD[radius]}, the Ascension '
        '`target_arcane_state_centeronly` quad): cast by the stalker standing at an awake sentinel on itself '
        '(triggered). Normal keeps 6 yd; heroic swaps the rung as the field grows 1 yd every 10 s to 9 yd (a stalker '
        'aura cannot resize). The registry\'s ring marker carries the exact edge. Look only.',
    )
    for i, radius in enumerate(sorted(SV_SECURITY_FIELD))
]

field_hit_211096 = resolve_copy(
    211096, 'Security Field', School.ARCANE, 'The vault\'s security field burns intruders.',
    f'{_VA}, VA3: a field\'s tick: a persistent registry circle of 6 yd round each awake sentinel (heroic +1 yd every '
    '10 s it lives, 9 yd at most), 5% (heroic 8%) of the reference row a second to everyone in it, the tank on its own '
    'row (ruling 88), no Weakened. Copy of the mod-boss-mechanics resolve spell (Arcane). The field drops with its '
    'sentinel.',
    icon=_ICON_ARCANE,
)

# --- VA4 Security Link -----------------------------------------------------------------------------------------------

link_beam_211097 = spell(
    id=211097, name='Security Link', school=School.ARCANE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_BEAM,
    notes=f'{_VA}, VA4: the beam from each awake sentinel to Doomgrip, a channel the sentinel casts on him (triggered; '
          'the script casts it again every 2 s when it is not channeling). Beam Link 62881\'s SV 13261. A DUMMY aura '
          'on him, no effect: the reduction is 211098, counted by his script from the awake sentinels. Not '
          'interruptible (a kick on a sentinel must not look like it cut the link). Ignores line of sight. '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('', 'Linked to a Vault Sentinel.', CastingTimeIndex=1, InterruptFlags=0,
                          ChannelInterruptFlags=0, PreventionType=0, SpellVisualID_1=VA_SECURITY_LINK,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

security_link_211098 = spell(
    id=211098, name='Security Link', school=School.ARCANE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=-_LINK_PCT - 1, die_sides=1, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BEAM,
    notes=f'{_VA}, VA4: Doomgrip takes 25% less damage per awake sentinel, 3 stacks (75%) at most: put on him by his '
          'own script (Unit::SetAuraStack, the stacks = awake sentinels, checked every 0.5 s; removed at 0 and on his '
          'reset, evade and death). Every school. Not dispellable or purgeable: the answer is to kill the sentinels '
          '(the kill order). CumulativeAura 3.',
    raw_overrides=kit_raw('Damage taken reduced for every Vault Sentinel linked to him.',
                          'Damage taken reduced by $s1%.', CastingTimeIndex=1, CumulativeAura=_LINK_STACKS,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- VA5 Intruder Sweep ----------------------------------------------------------------------------------------------

sweep_cast_211099 = cast_bar(
    211099, 'Intruder Sweep', _SWEEP_WARN_MS, 'Watchman Doomgrip sweeps the ground before him.',
    f'{_VA}, VA5: the 2 s bar (8 s in, then every 15 s, heroic 12 s): the registry\'s 90 degree, 10 yd cone, locked '
    'where he faces his victim at the bar\'s start, owns the hit (211100). DUMMY on the caster, Physical, not '
    'interruptible (he has no kickable cast). Sweeping Slam 12887\'s SV 2717 (the slam); the cone marker is the sweep.',
    icon=_ICON_SWEEPING_SLAM, visual=VA_INTRUDER_SWEEP,
)

sweep_hit_211100 = resolve_copy(
    211100, 'Intruder Sweep', School.NORMAL, 'Watchman Doomgrip sweeps everything in front of him.',
    f'{_VA}, VA5: the cone\'s hit: 25% (heroic 40%) of the reference row to everyone in the 90 degree, 10 yd cone, the '
    'tank on its own row and included (ruling 88: he steps out of it too), 1 Weakened. Copy of the mod-boss-mechanics '
    'resolve spell (Physical).',
    icon=_ICON_SWEEPING_SLAM,
)

# --- VA6 Sunder Armor ------------------------------------------------------------------------------------------------

sunder_armor_211101 = spell(
    id=211101, name='Sunder Armor', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_MELEE_RANGE,
    duration_ms=_SUNDER_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_RESISTANCE_PCT,
                    base_points=-_SUNDER_PCT - 1, die_sides=1, misc_value=_RESISTANCE_ARMOR,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_SUNDER,
    notes=f'{_VA}, VA6: his stock Sunder Armor 11971 as his own copy with a real value (the stock base points compute '
          'to about 0): -5% armor a stack, 5 stacks, 30 s, on his victim in melee reach (the tank), 1 s in then every '
          '6 to 8 s (the stock cadence). Not dispellable. Removed from the players on his reset, evade and death. The '
          'stock look (SV 39). '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Sunders the target\'s armor, reducing it by $s1% per application.',
                          'Armor reduced by $s1%.', CastingTimeIndex=1, CumulativeAura=_SUNDER_STACKS,
                          DefenseType=_DEFENSE_MELEE, SpellVisualID_1=VA_SUNDER_ARMOR,
                          AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- VA7 Watchman's Draught ------------------------------------------------------------------------------------------

watchmans_draught_211102 = spell(
    id=211102, name='Watchman\'s Draught', school=School.NATURE, dispel=_DISPEL_MAGIC, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_DRAUGHT_MS,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=_DRAUGHT_HEAL_PCT - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Watchman\'s Draught: a percent of the caster\'s own maximum health, not a heal '
                                     'value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=_DRAUGHT_DAMAGE_PCT - 1, die_sides=1, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Watchman\'s Draught: a flat +20% damage done, not a damage value')],
    spell_icon_id=_ICON_POTION,
    notes=f'{_VA}, VA7: at 60% and 30% (once each) he drinks: heals 5% of his maximum health (HEAL_PCT) and +20% '
          'damage done for 15 s (every school; the registry hits ignore caster modifiers, so it raises his melee '
          'only), Magic: the descriptor\'s purge list (a reward). Cast by '
          'boss_watchman_doomgrip_rework on himself (triggered). Replaces the stock Drink Healing Potion 15504 '
          '(retired). Thunderbrew Lager 5257\'s SV 101 (a tankard in hand and a heal flash).',
    raw_overrides=kit_raw('Drinks a draught that heals and enrages the watchman.', 'Damage done increased by $s2%.',
                          CastingTimeIndex=1, SpellVisualID_1=VA_WATCHMANS_DRAUGHT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- The sentinels' dormant look (R-2-A MA-2) -----------------------------------------------------------------------

sentinel_stoned_211103 = _state_aura(
    211103, 'Stoned', _SV_STONED, -1, _ICON_STONED,
    f'{_VA}: the Vault Sentinels\' dormant look (R-2-A MA-2), cast on 300793 by the instance\'s freeze '
    '(FreezeVaultConstruct, BlackrockDepthsRework::kSpellVaultStoned) and by npc_brd_vault_sentinel\'s Dormant; '
    'removed by its Wake. A copy of Stoned 10255 (its SV 1845 and icon) without the stock EffectMechanic FREEZE, '
    'which the sentinel\'s immunity set 1972 drops (so the stock aura never lands), and with NO_IMMUNITIES. Look '
    'only: the dormant state is the sentinel\'s NOT_SELECTABLE flag.',
)
