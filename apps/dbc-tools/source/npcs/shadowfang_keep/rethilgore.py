"""
Shadowfang Keep build WP-S1: Rethilgore, the Cell Keeper (.agents/plans/shadowfang-keep-build/
shadowfang-keep-build.HANDOFF.md s3.5 rows RG1-RG6, s3.6 row S1; build spec docs/dungeons/shadowfang-keep-rework.md
SK 310-353 (normal and heroic), SK 191-309 (design)). WP-S1 owns this file (its spells: kSpellsRethilgore
205910-205929 in modules/mod-dungeon-bosses src/ShadowfangKeep/ShadowfangKeepRework.h only; RethilgoreLogic.h
`RethilgoreSpells` names the same ids; creatures 300500-300502).

- 3914 Rethilgore: bound to boss_rethilgore_rework (SmartAI off; WP-S1's core rev drops the stock rows), normal 12.1k
  (HealthModifier 25, handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Heroic 265,524 is WP-H's override in
  source/world/dungeons/shadowfang_keep.py.
- 300500 Cell Door (RG2): the invisible stand-in on a jailed cell's door line, attackable from both sides, never moves
  or attacks (npc_sfk_cell_door, DungeonKit::BreakableDoorAI); 720 on normal (HealthModifier on the level 20 warrior
  base 484; the script sets it exactly), 12,000 on heroic (its heroic template 310057, WP-H's `_KIT_ADD_HEROIC`). No
  armor (ArmorModifier 0) so the build spec's "6 s of two DPS players" holds; no XP, no loot, no avoidance.
- 300501 Soul Fragment (RG5) and 300502 Tainted Fragment (RG6, heroic): the wisp looks (npc_sfk_soul_fragment,
  passive), not selectable. Triggers: no heroic template.

Spells (visual ids from WP-V's source/npcs/shadowfang_keep/_visuals.py; stock spells are never cast, their visuals are
copied):

  205910  Lock-Up            RG1: the leap's look on the grabbed player, DUMMY (Charge 52577's SV 11546: trail, dust,
                             a blood burst on the target); he casts it, triggered, as he jumps onto the target
  205911  Lock-Up            RG1: the 1.5 s cast bar (no effect, not interruptible), with emote line 1
  205912  Lock-Up            RG1: the throw's flash at both ends (Shadow Port 7136's SV 3303), the jailed player casts
                             it on itself before and after the teleport
  205913  Soul Drain         RG4: the channel on the prisoner (stock Soul Drain 7295's SV 680; its soul beam shows only
                             on a channel). A look and the prisoner's debuff only: the ticks are 205914. Not
                             interruptible (no interrupt or channel interrupt flags, PreventionType 0), not dispellable
                             (Dispel 0, NO_IMMUNITIES), ALLOW_ACTION_DURING_CHANNEL (he keeps meleeing and casting),
                             ignores LoS (through the bars)
  205914  Soul Drain         RG4: the 2 s tick, Shadow, 5% of the reference non-tank row (set at launch by
                             spell_sfk_rethilgore_soul_drain); ignores caster modifiers, ignores LoS, always hits,
                             cannot crit; impact Mind Blast's SV 3057 (a shadow burst on the prisoner)
  205915  Soul Fragment      RG5: a caught fragment heals its owner 5% of the reference non-tank row (the script passes
                             the value; cast by the owner on itself, so no caster bonus: DefenseType 0, ignores caster
                             modifiers); Flash Heal's SV 3077
  205916  Soul Fragment      RG5: the streak, a missile from a fragment to its owner (caught) or to Rethilgore (missed);
                             Akama Soul Retrieve 40854's SV 9253 and speed 10. DUMMY, no effect
  205917  Soul Feast         RG5: a missed fragment heals Rethilgore 5% of his max health (the script passes the value)
  205918  Cell Key           RG3: the carrier's buff (one key at most, the pickup takes keyless players only); used up
                             at a jailed cell's door. Gone on death, at the fight's end (the script) or after 10 min
  205919  Tainted Fragment   RG6 heroic: the registry Mine's resolve copy, Shadow (25% + 1 Weakened on the toucher);
                             impact SV 3057
  205920-205929 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import cast_bar, self_visual
from lib.dsl.registry import (
    creature_model,
    creature_template,
    creature_template_columns,
    scripted_by,
    spell,
)

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
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_SOUL_WISP,
    DISPLAY_TAINTED_WISP,
    RG_CELL_TELEPORT_FLASH,
    RG_FRAGMENT_STREAK,
    RG_LOCK_UP_LEAP,
    RG_SOUL_DRAIN_CHANNEL,
)

creature_template_columns(3914, **boss_columns('boss_rethilgore_rework', 25))

# --- creatures (300500-300502) ----------------------------------------------------------------------------------------

# CreatureFlagsExtra: NO_PARRY | NO_BLOCK | NO_XP | NO_CRIT | NO_DODGE | IMMUNITY_KNOCKBACK (a door).
_DOOR_FLAGS_EXTRA = 0x4 | 0x10 | 0x40 | 0x20000 | 0x800000 | 0x40000000
_WARRIOR_BASE_HEALTH_20 = 484       # creature_classlevelstats, level 20 warrior, exp 0 (SK "Tuning model")
_DOOR_HEALTH_NORMAL = 720

cell_door_300500 = creature_template(
    300500, 'Cell Door', **{**KIT_CREATURE, 'minlevel': 20, 'maxlevel': 20, 'rank': 1, 'unit_class': 1, 'type': 10,
                            'HealthModifier': round(_DOOR_HEALTH_NORMAL / _WARRIOR_BASE_HEALTH_20, 4),
                            'DamageModifier': 0.0, 'ArmorModifier': 0.0, 'ExperienceModifier': 0.0,
                            'RegenHealth': 0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0,
                            'maxgold': 0, 'detection_range': 0.0, 'flags_extra': _DOOR_FLAGS_EXTRA,
                            'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
                            'difficulty_entry_1': 310057, 'ScriptName': 'npc_sfk_cell_door'},
)
creature_model(300500, display_id=DISPLAY_INVISIBLE_STALKER)

soul_fragment_300501 = creature_template(
    300501, 'Soul Fragment', **{**KIT_HELPER, 'minlevel': 20, 'maxlevel': 20, 'rank': 0, 'unit_class': 1, 'type': 10,
                                'ScriptName': 'npc_sfk_soul_fragment'},
)
creature_model(300501, display_id=DISPLAY_SOUL_WISP)

tainted_fragment_300502 = creature_template(
    300502, 'Tainted Fragment', **{**KIT_HELPER, 'minlevel': 20, 'maxlevel': 20, 'rank': 0, 'unit_class': 1,
                                   'type': 10, 'ScriptName': 'npc_sfk_soul_fragment'},
)
creature_model(300502, display_id=DISPLAY_TAINTED_WISP, scale=1.0)

# --- spells (205910-205929) -------------------------------------------------------------------------------------------

_TARGET_UNIT_TARGET_ENEMY = 6

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000
_ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x00000001

# Stock icons (Spell.dbc 3.3.5).
_ICON_CHARGE = 457          # Charge 52577
_ICON_SOUL_DRAIN = 546      # Soul Drain 7295
_ICON_PICK_LOCK = 106       # Pick Lock 1804 (Spell_Nature_MoonKey)
_ICON_SHADOW_PORT = 207     # Shadow Port 7136

# Stock visuals not in WP-V's table (impacts and heals).
_SV_SHADOW_IMPACT = 3057    # Mind Blast 8092: a shadow burst on the target
_SV_SOUL_RETURN = 3077      # Flash Heal 2061: the soul comes home
_STREAK_SPEED = 10.0        # Akama Soul Retrieve 40854's missile speed

_REF_FLAT_NOTE = ('Shadowfang Keep: the damage is set at launch by spell_sfk_rethilgore_soul_drain '
                  '(OnEffectLaunchTarget SetEffectValue = DungeonKit::RefFlat, a percent of the reference health row)')
_SCRIPT_VALUE_NOTE = ('Shadowfang Keep: a script value, not a scaled spell: boss_rethilgore_rework passes the amount '
                      '(CastCustomSpell base points) from the reference row or his max health')

lock_up_leap_205910 = spell(
    id=205910, name='Lock-Up', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CHARGE,
    notes='Shadowfang Keep WP-S1, RG1: the leap. Rethilgore casts it (triggered) on the player he grabs as he jumps '
          'onto them (DungeonKit::JumpTo); the throw into a cell follows his landing. DUMMY, no effect, no threat; '
          'ignores LoS, always hits. Stock Charge 52577\'s SpellVisual 11546 (charge trail and dust, a blood burst on '
          'the target; its stun swirl plays only with an aura, and there is none: the grab is a teleport).',
    raw_overrides=kit_raw('Grabs an enemy and throws it into a cell.', instant=True, InterruptFlags=0,
                          PreventionType=0, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_ALWAYS_HIT,
                          SpellVisualID_1=RG_LOCK_UP_LEAP),
)

lock_up_cast_205911 = cast_bar(
    205911, 'Lock-Up', 1500, 'More meat for the cells.',
    'Shadowfang Keep WP-S1, RG1: the 1.5 s warning before the leap, with the emote "%s lunges for $n!" (type 41). No '
    'effect, not interruptible: the script owns the leap and the throw on its own timer.',
    icon=_ICON_CHARGE,
)

cell_throw_flash_205912 = self_visual(
    205912, 'Lock-Up', RG_CELL_TELEPORT_FLASH,
    'Shadowfang Keep WP-S1, RG1: the throw into the cell is a teleport (not crowd control); the jailed player casts '
    'this on itself (triggered) before and after it, a flash at both ends (Shadow Port 7136\'s SpellVisual 3303).',
    icon=_ICON_SHADOW_PORT, school=School.SHADOW,
)

soul_drain_205913 = spell(
    id=205913, name='Soul Drain', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=60000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_SOUL_DRAIN,
    notes='Shadowfang Keep WP-S1, RG4: the channel. Rethilgore channels it (triggered) on the jailed player through '
          'the bars, 1 s after the throw, until the prisoner is freed (the script interrupts it then, and recasts it '
          'if it ever drops while the prisoner is still jailed). A look and a debuff only: the 2 s ticks are 205914 '
          '(the script\'s own timer). Stock Soul Drain 7295\'s SpellVisual 680: its soul beam (chain 8, SoulBeam.blp) '
          'shows only on a channel (handoff s3.10 correction 9). Not interruptible (InterruptFlags, '
          'ChannelInterruptFlags and AuraInterruptFlags 0, PreventionType 0: a kick does nothing), not dispellable '
          '(Dispel 0, NO_IMMUNITIES), ALLOW_ACTION_DURING_CHANNEL (he keeps meleeing and casting while he drains), '
          'NO_THREAT, ignores LoS, always hits.',
    raw_overrides=kit_raw('Drains the soul of a caged enemy.',
                          'Rethilgore drains your soul. Break out of the cell!', instant=True, InterruptFlags=0,
                          AuraInterruptFlags=0, ChannelInterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_IS_CHANNELED | _ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_ALWAYS_HIT,
                          AttributesEx5=_ATTR5_ALLOW_ACTION_DURING_CHANNEL, SpellVisualID_1=RG_SOUL_DRAIN_CHANNEL),
)

soul_drain_tick_205914 = spell(
    id=205914, name='Soul Drain', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_REF_FLAT_NOTE)],
    spell_icon_id=_ICON_SOUL_DRAIN,
    notes='Shadowfang Keep WP-S1, RG4: the Soul Drain tick, every 2 s on the jailed player: 5% Shadow of the reference '
          'non-tank row (normal 65, heroic 206), set at launch so the target\'s defensives count. Rethilgore casts it, '
          'triggered, while he channels 205913. The resolve attribute set (no active defense, no redirection or '
          'reflection, no threat, ignores LoS, cannot crit, NOT_A_PROC, always hits, ignores caster modifiers), '
          'DefenseType 1. Impact: Mind Blast 8092\'s SpellVisual 3057 (a shadow burst on the prisoner). No Weakened '
          '(damage over time, ruling 17).',
    raw_overrides=kit_raw('Drains the soul of a caged enemy.', instant=True,
                          Attributes=_ATTR0_NO_ACTIVE_DEFENSE,
                          AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          DefenseType=1, SpellVisualID_1=_SV_SHADOW_IMPACT),
)
scripted_by(soul_drain_tick_205914, 'spell_sfk_rethilgore_soul_drain')

soul_return_205915 = spell(
    id=205915, name='Soul Fragment', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_VALUE_NOTE)],
    spell_icon_id=_ICON_SOUL_DRAIN,
    notes='Shadowfang Keep WP-S1, RG5: a Soul Fragment caught by anyone returns to its owner (the jailed player): '
          'the owner casts this on itself (triggered) with the amount the script passes, 5% of the reference non-tank '
          'row (normal 65, heroic 206). DefenseType 0 and IGNORE_CASTER_MODIFIERS: no spell power or done bonus on a '
          'script value. Flash Heal 2061\'s SpellVisual 3077 on the owner as the streak 205916 arrives.',
    raw_overrides=kit_raw('Your soul returns to you.', instant=True, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=_SV_SOUL_RETURN),
)

soul_streak_205916 = spell(
    id=205916, name='Soul Fragment', school=School.SHADOW, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SOUL_DRAIN,
    notes='Shadowfang Keep WP-S1, RG5: the fragment\'s flight. A short-lived wisp at the fragment\'s point casts it '
          '(triggered) on the owner (caught) or on Rethilgore (missed). Akama Soul Retrieve 40854\'s SpellVisual 9253 '
          '(soulshatter missile, shadow hit) and its speed 10. DUMMY with no handler, no threat, ignores LoS.',
    raw_overrides=kit_raw('A soul fragment streaks home.', instant=True, Speed=_STREAK_SPEED,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=_ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=RG_FRAGMENT_STREAK),
)

soul_feast_205917 = spell(
    id=205917, name='Soul Feast', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_VALUE_NOTE)],
    spell_icon_id=_ICON_SOUL_DRAIN,
    notes='Shadowfang Keep WP-S1, RG5: a Soul Fragment nobody caught in 6 s streaks to Rethilgore (205916) and heals '
          'him 5% of his max health: he casts this on himself (triggered) with the amount the script passes. '
          'DefenseType 0 and IGNORE_CASTER_MODIFIERS: the bare value (healing taken effects still apply).',
    raw_overrides=kit_raw('Feasts on a lost soul.', instant=True, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)

cell_key_205918 = spell(
    id=205918, name='Cell Key', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=600000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_PICK_LOCK,
    notes='Shadowfang Keep WP-S1, RG3: the Cell Key carrier\'s buff. A player who walks over a key Rethilgore dropped '
          '(at 66% and 33%) casts it on itself (triggered); the key pickup takes only players without it (one key at '
          'most). Walking up to the jailed cell\'s door uses it up and opens the door (a carrier-only pickup), and a '
          'carrier thrown into a cell opens their own door at once. A visible buff (not passive), not dispellable; '
          'gone on death, when the fight ends (the script) or after 10 min.',
    raw_overrides=kit_raw('Carry a Cell Key.', 'Carrying a Cell Key. Walk up to a locked cell to open it.',
                          instant=True, AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

tainted_fragment_205919 = resolve_copy(
    205919, 'Tainted Fragment', School.SHADOW, 'A tainted soul bursts.',
    'Shadowfang Keep WP-S1, RG6 heroic: a Tainted Fragment popped by a touch (a registry Mine: 1.5 yd, arms in 0.5 s, '
    'no grace, 40 s), 25% Shadow + 1 Weakened on the toucher (heroic 1,030). Impact: Mind Blast 8092\'s '
    'SpellVisual 3057.',
    icon=_ICON_SOUL_DRAIN, visual=_SV_SHADOW_IMPACT,
)
