"""
Blackrock Spire build WP-B6: Quartermaster Zigris (9736), "a quartermaster who fights out of his own stores"
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows ZG, s3.5 row B6, s3.6; build spec
docs/dungeons/blackrock-spire-rework.md SP 1690-1903, ZG1-ZG8, rulings 40-43). WP-B6 owns this file (its spells:
kSpellsZigris 210180-210209 in modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h only;
ZigrisLogic.h names the same ids).

- 9736 Quartermaster Zigris: boss_quartermaster_zigris_rework (SmartAI off: the stock boss is C++ only, there are no
  rows to drop), normal HealthModifier 47.281 (140k at 5 players on the level 59 warrior base 2,961), stun immune
  (1972), INSTANCE_BIND, the stock DamageModifier 3.5 (the live 5 is a mod-progression leftover; WP-T tunes melee).
  Heroic health 185k and the tier's melee are WP-H's heroic template (source/world/dungeons/blackrock_spire.py). The
  stock Stun Bomb 16497, Hooked Net 15609 and healing potion 15504 are no longer cast (the script is new); Shoot 16496
  stays. His loot (two potions, the Blackrock Bracer of quest 8994) is untouched.
- 300707 Clockwork Sheep (ZG6, heroic only): the Explosive Sheep, 3,000 health (HealthModifier 0.98296:
  ceil(3,052 x 0.98296) = 3,000 on the level 60 warrior base), display 3886 (the SheepRobo skin, not the engineering
  2675), passive and harmless to touch: Zigris drives it with the kit Chaser and blows it up. npc_brs_clockwork_sheep
  (a NullCreatureAI). Its heroic template is WP-H's `_KIT_ADD_HEROIC` (3,000 as well; difficulty_entry_1 310290, the
  third wave 1 kit add of heroic_ids.lock's order).
- The Supply Crate 301252, Net Trap 301253 and Powder Keg 301254 gameobjects, the crates' spawns and his six texts are
  the core SQL rev rev_quartermaster_zigris_blackrock_spire.sql (dbc-tools has no gameobject_template declaration).
- The generic stalker 300713 (the keg's fuse and the mortar's look source) is the orchestrator's: a Shared-file request
  in the B6 report.

Spells (looks from ._visuals, WP-V-1's ZG_* picks; every look unconfirmed until seen in game). The registry hits go
through dungeon copies of the mod-boss-mechanics resolve spell; the rest are riders, auras and looks:

  210180  Net Trap          ZG1 a sprung trap's hit: resolve copy, Physical, 20% / 25% + Weakened
  210181  Netted            ZG1 the 2 s root of a sprung trap (the registry's rider), Hooked Net's net look
  210182  Powder Keg        ZG4 the keg's hit: resolve copy, Fire, 30% / 40% + Weakened
  210183  Knocked Senseless ZG4 the 2 s stun of the keg (the registry's rider)
  210184  Lit Fuse          ZG4 / ZG6 the fire spiral on the keg's stalker and on the sheep (a state aura)
  210185  Blast             ZG4 / ZG6 the explosion at a point (look only: the ring and the burst)
  210186  Mortar Shell      ZG5 a shell's hit: resolve copy, Fire, 25% / 30% + Weakened
  210187  Mortar Shell      ZG5 the shell in flight to a point (look only, Speed 22)
  210188  Smoke Bomb        ZG2 the smoke at his feet (look only)
  210189  Fall Back         ZG2 the leap's animation (look only)
  210190  Explosive Sheep   ZG6 the sheep's hit: resolve copy, Fire, 35% + Weakened
  210191  Wind-Up           ZG6 the wind-up as a sheep is released (look only)
  210192-210209 spare
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import self_visual
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_CLOCKWORK_SHEEP,
    ZG_DISENGAGE,
    ZG_KEG_BLAST,
    ZG_KEG_FUSE,
    ZG_MORTAR_SHELL,
    ZG_NET,
    ZG_SHEEP_WINDUP,
    ZG_SMOKE_BOMB,
)

_B6 = 'Blackrock Spire build WP-B6 (Quartermaster Zigris)'

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000      # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_MECHANIC_ROOT = 7
_MECHANIC_STUN = 12

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004

_ICON_GENERIC = 1       # generic (no stock gadget icon id read)

SHELL_MISSILE_SPEED = 22.0          # ZigrisLogic.h kShellMissileSpeed
SHEEP_HEALTH_MODIFIER = 0.98296     # ceil(3,052 x 0.98296) = 3,000 (the level 60 warrior base)
SHEEP_HEROIC_ENTRY = 310290         # heroic_ids.lock: the third wave 1 kit add (H's prediction)

# --- The boss and the sheep ------------------------------------------------------------------------------------------

creature_template_columns(9736, **boss_columns(
    'boss_quartermaster_zigris_rework', 47.281, damage_modifier=3.5,
))

clockwork_sheep_300707 = creature_template(
    300707, 'Clockwork Sheep', **{
        **KIT_CREATURE, 'type': 9, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': SHEEP_HEALTH_MODIFIER, 'DamageModifier': 0.0, 'BaseAttackTime': 2000,
        'ExperienceModifier': 0.0, 'RegenHealth': 0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0,
        'maxgold': 0, 'ScriptName': 'npc_brs_clockwork_sheep', 'difficulty_entry_1': SHEEP_HEROIC_ENTRY,
    },
)
creature_model(300707, display_id=DISPLAY_CLOCKWORK_SHEEP)

# --- ZG1 Net Traps ---------------------------------------------------------------------------------------------------

net_trap_210180 = resolve_copy(
    210180, 'Net Trap', School.NORMAL, 'A trap snaps shut.',
    f'{_B6} ZG1 Net Traps: a sprung trap (a registry Mine, 3 yd) hits whoever sprang it, 20% (heroic 25%) of the '
    'non-tank row + Weakened, and roots them 2 s (Netted 210181, the registry rider). Copy of the resolve spell '
    '205001 (Physical). Nothing of its own to see: the trap object closes and the net look is on the root.',
    icon=_ICON_GENERIC,
)

netted_210181 = spell(
    id=210181, name='Netted', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_ROOT,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, base_points=0,
                    mechanic=_MECHANIC_ROOT, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_B6} ZG1: the 2 s root of a sprung Net Trap (MOD_ROOT, root mechanic: freedom effects and root immunity '
          'are class tools against it, and Weakened rides the hit beside it). Dispel none (like the stock Hooked Net). '
          "Hooked Net 13608's SpellVisual 3519 (the net missile and the lasting net on the ground, ZG_NET). "
          'AuraInterruptFlags CHANGE_MAP (it never outlives the instance). The duration is ZigrisLogic.h kNettedMs.',
    raw_overrides=kit_raw('Caught in a net. Lasts $d.', 'Rooted by a net.', instant=True, SpellVisualID_1=ZG_NET,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- ZG2 Fall Back ---------------------------------------------------------------------------------------------------

smoke_bomb_210188 = self_visual(
    210188, 'Smoke Bomb', ZG_SMOKE_BOMB,
    f'{_B6} ZG2 Fall Back: the smoke bomb at his feet as he falls back, cast by him on himself (triggered). Smoke Bomb '
    "7964's SpellVisual 804 (ZG_SMOKE_BOMB). Look only.",
    icon=_ICON_GENERIC,
)

leap_210189 = self_visual(
    210189, 'Fall Back', ZG_DISENGAGE,
    f"{_B6} ZG2 Fall Back: the leap's animation as he goes (Disengage 781's SpellVisual 12305, ZG_DISENGAGE: the "
    "animation only, the move is the script's JumpTo). Look only.",
    icon=_ICON_GENERIC,
)

# --- ZG4 Powder Keg --------------------------------------------------------------------------------------------------

keg_blast_210182 = resolve_copy(
    210182, 'Powder Keg', School.FIRE, 'A powder keg blows.',
    f'{_B6} ZG4 Powder Keg: the 10 yd blast after the 4 s fuse, 30% (heroic 40%) of the non-tank row + Weakened + a '
    '2 s stun (Knocked Senseless 210183, the registry rider). Copy of the resolve spell 205003 (Fire). The ring and '
    'burst are Blast 210185 at the keg.',
    icon=_ICON_GENERIC,
)

keg_stun_210183 = spell(
    id=210183, name='Knocked Senseless', school=School.FIRE, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_STUN, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_B6} ZG4: the 2 s stun of a Powder Keg blast (MOD_STUN, stun mechanic: stun immunity and the stun-'
          'breaking trinkets answer it, and Weakened rides the hit beside it). Dispel none. AuraInterruptFlags '
          'CHANGE_MAP. The duration is ZigrisLogic.h kKegStunMs. No look of its own (the stock stun swirl).',
    raw_overrides=kit_raw('Knocked senseless. Lasts $d.', 'Stunned by a blast.', instant=True,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

fuse_210184 = spell(
    id=210184, name='Lit Fuse', school=School.FIRE, dispel=0, mechanic=0,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_B6} ZG4 / ZG6: the lit fuse. The stalker at a keg casts it on itself (triggered) as the keg is rolled '
          'out and the sheep casts it on itself as it is released: a hidden DUMMY aura whose StateKit is the Explosive '
          "Sheep detonation state's fire spiral (SpellVisual 791, ZG_KEG_FUSE; WP-V's alternate is Throw Dynamite 148, "
          'which leaks a stun swirl). Not passive (a passive aura is never sent to the client, so its state visual '
          'would not show). The stalker despawns at the blast; the sheep drops it when it blows up.',
    raw_overrides=kit_raw(SpellVisualID_1=ZG_KEG_FUSE, AttributesEx4=ATTR4_NO_CAST_LOG, CastingTimeIndex=1),
)

blast_look_210185 = spell(
    id=210185, name='Blast', school=School.FIRE, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_B6} ZG4 / ZG6: the explosion at a point, cast by him (triggered) where a keg blows or a sheep goes up. '
          "Goblin Sapper Charge 13241's SpellVisual 2899 (ZG_KEG_BLAST: a fire nova ring, the explosion and a shake) "
          'at the point (unchecked whether a dest-only spell plays it). The registry dealt the damage. Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=ZG_KEG_BLAST, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- ZG5 Mortar ------------------------------------------------------------------------------------------------------

mortar_shell_210186 = resolve_copy(
    210186, 'Mortar Shell', School.FIRE, 'A mortar shell lands.',
    f"{_B6} ZG5 Mortar: a shell's 5 yd hit 2 s after it is marked, 25% (heroic 30%) of the non-tank row + Weakened. "
    'Copy of the resolve spell 205003 (Fire). The shell in flight is Mortar Shell 210187.',
    icon=_ICON_GENERIC,
)

mortar_look_210187 = spell(
    id=210187, name='Mortar Shell', school=School.FIRE, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_GENERIC,
    notes=f"{_B6} ZG5: the shell in flight, cast by the mortar's stalker on the second crate (triggered) at a point, "
          "timed to land as the marked circle resolves (ZigrisLogic.h ShellLaunchDelayMs). Big Bronze Bomb 4067's "
          'SpellVisual 3819 (ZG_MORTAR_SHELL: a bronze bomb in flight and Bomb_ExplosionA on landing) at 22 yd/s, so a '
          'throw from the crate to the far corner of the ledge (about 41 yd) flies for just under 2 s; the look '
          'is unconfirmed. The registry dealt the damage. Look only.',
    raw_overrides=kit_raw(instant=True, Speed=SHELL_MISSILE_SPEED, SpellVisualID_1=ZG_MORTAR_SHELL,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- ZG6 Explosive Sheep ---------------------------------------------------------------------------------------------

sheep_blast_210190 = resolve_copy(
    210190, 'Explosive Sheep', School.FIRE, 'A clockwork sheep explodes.',
    f'{_B6} ZG6 Explosive Sheep (heroic): the 8 yd blast when the sheep reaches its target, runs out its 10 s or walks '
    'over a Net Trap, 35% of the non-tank row + Weakened to everyone inside. Copy of the resolve spell 205003 (Fire). '
    'The explosion is Blast 210185 at the sheep.',
    icon=_ICON_GENERIC,
)

sheep_windup_210191 = self_visual(
    210191, 'Wind-Up', ZG_SHEEP_WINDUP,
    f"{_B6} ZG6: the wind-up as a sheep is released, cast by the sheep on itself (triggered). Explosive Sheep 4074's "
    'SpellVisual 88 (ZG_SHEEP_WINDUP: its sound and animation). Look only.',
    icon=_ICON_GENERIC,
)
