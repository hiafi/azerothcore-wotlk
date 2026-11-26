"""
Gnomeregan build WP-D6: Mekgineer Thermaplugg (7800), the end of section 2
(.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D6, s3.6, s3.8, s7 #30 A, #31 B, #36-#38, #40 A;
build spec docs/dungeons/gnomeregan-rework.md "Mekgineer Thermaplugg", MT1-MT14, rulings 37-42 and 64). WP-D6 owns this
file; WP-S0 wrote the skeleton.

- 7800: bound to boss_thermaplugg_rework (modules/mod-dungeon-bosses src/Gnomeregan/boss_thermaplugg_rework.cpp),
  SmartAI off (rev_skeleton_gnomeregan.sql drops the rows), normal health 80,003 = 93.79 on 853 (spec 40,000 x2.0,
  s7 #1 A), DamageModifier 1.7 (until T), immunity 1972 (stun immune; the stock taunt immunity -230 is gone, s7 #11 A),
  INSTANCE_BIND with both assist flags, detection range 12. Heroic health and its overrides are WP-H's
  (source/world/dungeons/gnomeregan.py); the hard mode's 800,000 is the script's (GnomereganRework.h Health).
- The boss kit (rule 32: every rule keys by entry; never the gear's 301100, s7 #40 A): 301120 Walking Bomb (normal
  and heroic face 01), 301121 Incendiary, 301122 Frost and 301123 Radioactive Bombs (heroic faces 02-04), 301124 The
  Big One (heroic face 06; not attackable), all npc_gnomer_walking_bomb (passive bodies the boss walks; their health is
  the script's, ThermapluggLogic.h ValuesFor: 400 / 5,000 / 7,000); the stalkers npc_gnomer_thermaplugg_stalker:
  301125 the face stalker at each alcove mouth (the beam's end), 301126 the mine body, 301127 the zone stalker (the
  plates' anchors, the fire patch's look, the blasts' looks). The bombs keep the stock bomb's faction 63 and type.
- Texts 7800 4-8 (and the stock groups re-cut to SP's table) are hand SQL:
  data/sql/updates/pending_db_world/rev_thermaplugg_gnomeregan.sql.

Spells (kSpellsThermaplugg 214490-214539; ThermapluggLogic.h names the same ids; looks from ._visuals, unconfirmed
until seen in game). Remote Detonator is the only kickable cast: Fire, PreventionType 1, InterruptFlags 15 (the kick
table: a kick locks his Fire school, and nothing else he casts needs it; his lobs, Override and Knock Away are
instant). The Frost root (Magic) and the Radioactive Poison (Poison) are dispel rewards; Locked Out, the bomb mark and
the Sticky Bomb are not dispellable and go through immunities (rule 27).

  214490  Activate Bomb          MT1 the beam between him and an opening face (the face stalker casts it)
  214491  Walking Bomb           MT3 the mark on a bomb's target
  214492  Walking Bomb Effect    MT3 the blast (resolve copy, Fire)
  214493  Walking Bomb Effect    the explosion's look
  214494  Walking Bomb Effect    the ground flash (The Big One, the Sticky Bomb)
  214495  Locked Out             MT4 30 s after a plate touch
  214496  Throw Bomb             MT5 the lob (and the Sticky Bomb's)
  214497  Land Mine              MT5 the mine's blast (resolve copy, Fire)
  214498  Land Mine              MT5 the mine body's explosion
  214499  Knock Away             MT7 the stock 10101 copy
  214500  Remote Detonator       MT14 the 3 s bar (Fire, kickable)
  214501  Incendiary Bomb        MT9 the blast (resolve copy, Fire)
  214502  Flame Patch            MT9 the patch's tick (resolve copy, Fire)
  214503  Flame Patch            MT9 the patch's look on its stalker
  214504  Flame Patch            MT9 the patch's one-shot burst
  214505  Frost Bomb             MT10 the blast (resolve copy, Frost)
  214506  Frost Bomb             MT10 the 3 s root (Magic)
  214507  Radioactive Bomb       MT11 the blast (resolve copy, Nature)
  214508  Radioactive Poison     MT11 the stacking Poison
  214509  Sticky Bomb            MT12 the bomb on its carrier, 5 s
  214510  Sticky Bomb            MT12 the blast on the others (resolve copy, Fire)
  214511  The Big One            MT13 the shared blast (resolve copy, Fire)
  214512-214539 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
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
    FACTION_GNOMEREGAN_MECHANICAL,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    heroic_entry,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BIG_ONE_SCALE,
    BOMB_SCALE,
    DISPLAY_BIG_ONE,
    DISPLAY_BOMB,
    DISPLAY_BOMB_FROST,
    DISPLAY_BOMB_RADIO,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_MINE,
    MINE_SCALE_RANGE,
    MT_BLAST,
    MT_BLAST_FLASH,
    MT_BOMB_MARK,
    MT_DETONATE_MINE,
    MT_FACE_BEAM,
    MT_FIRE_PATCH,
    MT_FIRE_PATCH_CAST,
    MT_FROST,
    MT_KNOCK_AWAY,
    MT_LOCKED_OUT,
    MT_MINE_LOB,
    MT_RADIO,
    MT_STICKY,
)

_D6 = 'Gnomeregan build WP-D6 (Mekgineer Thermaplugg)'
_RESOLVE = ('a percent of the reference row set per target by spell_boss_mechanics_resolve (DungeonKit::RegistryHit '
            'or the registry, owner Thermaplugg)')
_SCRIPT_PERIODIC = ('a percent of the reference row (hundredths in the value) through the kit\'s '
                    'spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')

creature_template_columns(7800, **boss_columns(
    'boss_thermaplugg_rework', 93.79, damage_modifier=1.7,
))

# --- constants (ThermapluggLogic.h namespace Tune; lib/test_gnomeregan_thermaplugg.py pins each) ----------------------

LOCKED_OUT_MS = 30000               # kLockedOutMs
STICKY_FUSE_MS = 5000               # kStickyFuseMs
DETONATOR_CAST_MS = 3000            # kDetonatorCastMs
FROST_ROOT_MS = 3000                # SP MT10
RADIO_POISON_MS = 12000             # kRadioPoisonMs
RADIO_POISON_HUNDREDTHS = 400       # kRadioPoisonHundredths: 4% a second a stack (guess)
RADIO_POISON_MAX_STACKS = 99        # SP: "stacking", no cap given
FIRE_PATCH_MS = 20000               # kFirePatchMs
BOMB_MARK_MS = 120000               # the script removes it when the bomb goes
MINE_SCALE = 2.5                    # inside V's MINE_SCALE_RANGE
MINE_LOB_SPEED = 20.0               # yd/s: a missile the eye can follow (no damage rides on it)

# The boss kit's combat adds with a heroic template (s4 "kit adds' difficulty_entry_1"): the five bombs, each naming
# _common.heroic_entry (the lock's line, else H's predicted 310580-310584; lib/test_gnomeregan_heroic.py pins them).
# The stalkers and the mine have none (H's no-heroic list).
_HEROIC_BOMBS = (301120, 301121, 301122, 301123, 301124)

_ATTR0_IS_ABILITY = 0x00000010
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_INTERRUPT_FLAGS_KICKABLE = 15      # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_PREVENTION_PACIFY = 2
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_DISPEL_MAGIC = 1
_DISPEL_POISON = 4
_MECHANIC_ROOT = 7
_TARGET_UNIT_TARGET_ENEMY = 6
_UNIT_FLAG_NON_ATTACKABLE = 0x2
_FLAGS_EXTRA_NO_XP = 0x40

# Stock icons (Spell.dbc SpellIconID of the named spell; server DBC 2026-11-26)
_ICON_ACTIVATE_BOMB = 320           # Activate Bomb A 11511
_ICON_BOMB = 37                     # Walking Bomb Effect 11504, The Big One 12562
_ICON_LAND_MINE = 90                # Goblin Land Mine 4100
_ICON_THROW_BOMB = 1696             # Throw Bomb 40160
_ICON_KNOCK_AWAY = 314              # Knock Away 10101
_ICON_DETONATE = 356                # Remote Detonate 6627
_ICON_FIRE_BOMB = 11                # Fire Bomb 31961
_ICON_FLAME_PATCH = 876             # Flame Patch 35383
_ICON_FROST_NOVA = 193              # Frost Nova 122
_ICON_POISON = 37                   # the stock bomb icon (Walking Bomb Effect 11504)
_ICON_LOCKED_OUT = 1642             # Petrification 17624 (its SV 1845 is the look)


def _debuff_state(spell_id: int, name: str, duration_ms: int, desc: str, aura_desc: str, notes: str, *, icon: int,
                  visual: int):
    """A DUMMY debuff the script puts on a player (Unit::AddAura): not dispellable, through immunities (rule 27: a
    bubble or Ice Block must not strip it), dropped on a map change."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


def _unit_visual(spell_id: int, name: str, visual: int, notes: str, *, icon: int, speed: float = 0.0):
    """Visual only: an instant DUMMY a unit casts (triggered) at another unit (a beam, a lob: `speed` makes it a
    missile). No effect, no log."""
    raw = kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG)
    if speed:
        raw['Speed'] = speed
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY, dispel=0, mechanic=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


# --- MT1 the faces ---------------------------------------------------------------------------------------------------

face_beam_214490 = _unit_visual(
    214490, 'Activate Bomb', MT_FACE_BEAM,
    f'{_D6}, MT1: the beam as a face opens: the face\'s stalker (301125, at the alcove mouth) casts it at him, so the '
    'lightning joins him and the face (V: SV 944, Activate Bomb A 11511\'s ShockLightning, RISKY as a beam to a GO: '
    'hence the stalker). Look only.',
    icon=_ICON_ACTIVATE_BOMB,
)

# --- MT3 the Walking Bomb ---------------------------------------------------------------------------------------------

bomb_mark_214491 = _debuff_state(
    214491, 'Walking Bomb', BOMB_MARK_MS, 'A Walking Bomb is coming for you.',
    'A Walking Bomb is walking at you. Kill it, or keep it away from your group.',
    f'{_D6}, MT3: the mark on a walking bomb\'s target (the bomb is its caster, so two bombs show two marks); it moves '
    'when the bomb takes a new target and goes with the bomb. V\'s MT_BOMB_MARK (SV 3239, Hunter\'s Mark\'s head '
    'glow, s7 #40 A). Not dispellable (rule 27).',
    icon=_ICON_BOMB, visual=MT_BOMB_MARK,
)

resolve_copy(
    214492, 'Walking Bomb Effect', School.FIRE, 'A Walking Bomb explodes.',
    f'{_D6}, MT3 and MT8: a Walking Bomb within 3 yd of its target (or killed, heroic) blows up: everyone within 8 yd, '
    'the tank included, 40% (heroic 60%, hard mode 70%) of the reference row (the tank row on the tank) and Weakened, '
    'through DungeonKit::RegistryHit (registry tag 73). Resolve copy (Fire) of the stock Walking Bomb Effect 11504.',
    icon=_ICON_BOMB,
)

blast_look_214493 = self_visual(
    214493, 'Walking Bomb Effect', MT_BLAST,
    f'{_D6}, MT3: the explosion, played by a short-lived zone stalker at the blast (a killed bomb cannot cast). V\'s '
    'MT_BLAST (SV 5619, Walking Bomb Effect 11504\'s). Look only.',
    icon=_ICON_BOMB,
)

blast_flash_214494 = self_visual(
    214494, 'Walking Bomb Effect', MT_BLAST_FLASH,
    f'{_D6}, MT12 and MT13: the 17 yd ground flash of a Sticky Bomb and of The Big One (V\'s MT_BLAST_FLASH, SV '
    '10693). Look only.',
    icon=_ICON_BOMB,
)

# --- MT4 the plates ---------------------------------------------------------------------------------------------------

locked_out_214495 = _debuff_state(
    214495, 'Locked Out', LOCKED_OUT_MS, 'Locked out of the shut-off plates.',
    'You shut a bomb chute. The plates ignore you until this ends.',
    f'{_D6}, MT4: a player who touches a glowing plate shuts its face and is Locked Out for 30 s (every mode, ruling '
    '53): the plates ignore them (DwellSoaks excludeAura, so no bot claims one either). V\'s MT_LOCKED_OUT (SV 1845, '
    'Petrification\'s dark gray tint). Not dispellable (rule 27: a cure would let one runner shut every face).',
    icon=_ICON_LOCKED_OUT, visual=MT_LOCKED_OUT,
)

# --- MT5 the mines ----------------------------------------------------------------------------------------------------

mine_lob_214496 = _unit_visual(
    214496, 'Throw Bomb', MT_MINE_LOB,
    f'{_D6}, MT5 and MT12: the lob, cast (triggered) by him at each mined player (and by face 05\'s stalker at a '
    'Sticky Bomb\'s carrier): a missile at 20 yd/s with Throw Bomb 40160\'s SV 3819. The mine itself is laid at the '
    'player\'s spot at once (it arms over 3 s). Look only.',
    icon=_ICON_THROW_BOMB, speed=MINE_LOB_SPEED,
)

resolve_copy(
    214497, 'Land Mine', School.FIRE, 'A land mine goes off.',
    f'{_D6}, MT5: an armed mine set off by a player half a second inside its 3 yd ring (or by the Remote Detonator) '
    'hits everyone in its 6 yd ring: 40% (heroic 60%, hard mode 70%) and Weakened (KT-G TwoRingMines, registry tag '
    '75). Bombs and puddles never set one off (ruling 42). Resolve copy (Fire).',
    icon=_ICON_LAND_MINE,
)

mine_look_214498 = self_visual(
    214498, 'Land Mine', MT_DETONATE_MINE,
    f'{_D6}, MT5: the mine body\'s explosion as it goes off (V\'s MT_DETONATE_MINE, SV 889). Look only.',
    icon=_ICON_LAND_MINE,
)

# --- MT7 Knock Away ---------------------------------------------------------------------------------------------------

knock_away_214499 = spell(
    id=214499, name='Knock Away', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        # the stock second effect, unchanged: 112-187 knockback, the vertical 7.5
        Effect(type=EffectType.KNOCK_BACK, base_points=112, die_sides=75, misc_value=75,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_KNOCK_AWAY,
    notes=f'{_D6}, MT7: the stock Knock Away 10101 kept as his tank hit (rule 16: a copy in the slice, never the '
          'shared id): 100% weapon damage (WEAPON_PERCENT_DAMAGE, weapon_potency 100: the potency lint takes no flat '
          'weapon bonus; the stock +30 is noise against his swing) and the stock knockback (112, 75 sides, vertical '
          '75; 7.5 yd). The stock third effect (a script effect) is dropped. Cast triggered on his target in melee '
          'reach, 3 s after the pull and every 15 s. Heroic: the template\'s melee (WP-H\'s damage). Stock look: SV '
          '2069 (V\'s MT_KNOCK_AWAY, the same id as CP_UPPERCUT).',
    raw_overrides=kit_raw('Inflicts $s1% weapon damage to an enemy and knocks it back.', instant=True,
                          DefenseType=_DEFENSE_MELEE, PreventionType=_PREVENTION_PACIFY, SpellVisualID_1=MT_KNOCK_AWAY,
                          AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
)

# --- MT14 Remote Detonator --------------------------------------------------------------------------------------------

detonator_214500 = spell(
    id=214500, name='Remote Detonator', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=DETONATOR_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DETONATE,
    notes=f'{_D6}, MT14 (heroic): every 25 s (hard mode 20 s) from 20 s, a 3 s cast with emote line 8. Kickable: '
          'InterruptFlags 15 and PreventionType 1 (a kick or a silence), on the descriptor\'s interrupt list (priority '
          '3: the expected kick). Landed (CreatureAI::OnSpellCast), every living bomb blows where it is (its own '
          'blast) and every armed mine goes off in its full 6 yd ring. FIRE school, so a kick locks Fire alone; '
          'nothing else of his needs it (the kick table). No effect of its own; no look (Remote Detonate 6627\'s SV '
          '354 is a sound only, never wired).',
    raw_overrides=kit_raw('Reaches for his detonator.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- MT9 Incendiary Bomb (face 02) ------------------------------------------------------------------------------------

resolve_copy(
    214501, 'Incendiary Bomb', School.FIRE, 'An Incendiary Bomb explodes.',
    f'{_D6}, MT9 (heroic face 02): the Walking Bomb\'s blast (60%, hard mode 70%, Weakened, 8 yd) that also leaves a '
    'fire patch. Resolve copy (Fire).',
    icon=_ICON_FIRE_BOMB,
)

resolve_copy(
    214502, 'Flame Patch', School.FIRE, 'The ground burns.',
    f'{_D6}, MT9: the fire patch an Incendiary Bomb leaves where it blows: 8 yd for 20 s, 15% of the reference row a '
    'second to everyone in it (DungeonKit::Linger, registry tag 79, no slow rider). Lingering, so no Weakened. Resolve '
    'copy (Fire).',
    icon=_ICON_FLAME_PATCH,
)

fire_patch_look_214503 = spell(
    id=214503, name='Flame Patch', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=FIRE_PATCH_MS + 1000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FLAME_PATCH,
    notes=f'{_D6}, MT9: the patch\'s lasting look, cast (triggered) by its zone stalker (301127) on itself: V\'s '
          'MT_FIRE_PATCH (the shipped fire zone, SV 90508). The stalker despawns with the patch (20 s).',
    raw_overrides=kit_raw('Burning ground.', 'Burning ground.', instant=True, SpellVisualID_1=MT_FIRE_PATCH,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

fire_patch_cast_214504 = self_visual(
    214504, 'Flame Patch', MT_FIRE_PATCH_CAST,
    f'{_D6}, MT9: the patch\'s one-shot burst as it forms (V\'s MT_FIRE_PATCH_CAST, SV 8314, wired once). Look only.',
    icon=_ICON_FLAME_PATCH,
)

# --- MT10 Frost Bomb (face 03) ----------------------------------------------------------------------------------------

resolve_copy(
    214505, 'Frost Bomb', School.FROST, 'A Frost Bomb explodes.',
    f'{_D6}, MT10 (heroic face 03): the Walking Bomb\'s blast (60%, hard mode 70%, Weakened, 8 yd) with the 3 s root '
    '(214506) on everyone hit. Resolve copy (Frost).',
    icon=_ICON_FROST_NOVA,
)

frost_root_214506 = spell(
    id=214506, name='Frost Bomb', school=School.FROST, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_ROOT,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=FROST_ROOT_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, base_points=0,
                    mechanic=_MECHANIC_ROOT, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FROST_NOVA,
    notes=f'{_D6}, MT10: the Frost Bomb\'s rider, a 3 s root on everyone its blast hits (the registry casts riders '
          'with Thermaplugg as the original caster). Magic: a dispel reward (the descriptor\'s dispel list, priority '
          '2); root mechanic, so a freedom effect breaks it too. V\'s MT_FROST (SV 17, Frost Nova\'s ice). Dropped on '
          'a map change.',
    raw_overrides=kit_raw('Frozen in place.', 'Frozen in place.', instant=True, SpellVisualID_1=MT_FROST,
                          DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- MT11 Radioactive Bomb (face 04) ----------------------------------------------------------------------------------

resolve_copy(
    214507, 'Radioactive Bomb', School.NATURE, 'A Radioactive Bomb explodes.',
    f'{_D6}, MT11 (heroic face 04): the Walking Bomb\'s blast (60%, hard mode 70%, Weakened, 8 yd) with a stack of '
    'the Radioactive Poison (214508) on everyone hit. Resolve copy (Nature).',
    icon=_ICON_POISON,
)

radio_poison_214508 = spell(
    id=214508, name='Radioactive Poison', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=RADIO_POISON_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=RADIO_POISON_HUNDREDTHS, die_sides=0, amplitude=1000,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_PERIODIC)],
    spell_icon_id=_ICON_POISON,
    notes=f'{_D6}, MT11: the Radioactive Bomb\'s rider: 12 s, every second 4% of the reference row a stack (base '
          'point 400 = 4.00% in hundredths, the same on heroic: EffectMiscValueB 0; the tank row on the tank), '
          'through spell_dungeon_refflat_periodic; each blast adds a stack and refreshes it (the engine multiplies '
          'the tick by the stacks). The numbers are the spec\'s guesses (SP MT11). Poison: a dispel reward (the '
          'descriptor\'s dispel list, priority 1). Ignores caster modifiers. V\'s MT_RADIO (SV 1725, the green burst). '
          'Dropped on a map change.',
    raw_overrides=kit_raw('Radioactive.', 'Taking Nature damage every second.', instant=True,
                          CumulativeAura=RADIO_POISON_MAX_STACKS, SpellVisualID_1=MT_RADIO, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(radio_poison_214508, 'spell_dungeon_refflat_periodic')

# --- MT12 the Sticky Bomb (face 05) -----------------------------------------------------------------------------------

sticky_214509 = _debuff_state(
    214509, 'Sticky Bomb', STICKY_FUSE_MS, 'A Sticky Bomb latches on.',
    'A bomb is stuck to you. Get away from your group before it goes off.',
    f'{_D6}, MT12 (heroic face 05): no unit: every 8 s while face 05 is open a bomb is lobbed from the face onto a '
    'random player, the tank included (emote line 6). 5 s later it goes off on everyone else within 8 yd (214510, the '
    'registry RunOut, tag 78). V\'s MT_STICKY (SV 10692, Living Bomb\'s state). Not dispellable (rule 27).',
    icon=_ICON_FIRE_BOMB, visual=MT_STICKY,
)

resolve_copy(
    214510, 'Sticky Bomb', School.FIRE, 'A Sticky Bomb goes off.',
    f'{_D6}, MT12: the Sticky Bomb\'s blast on everyone else within 8 yd of its carrier: 60% (hard mode 70%) of the '
    'reference row (the tank row on the tank), no Weakened (SP: Penalty none). The registry RunOut (tag 78). Resolve '
    'copy (Fire).',
    icon=_ICON_FIRE_BOMB,
)

# --- MT13 The Big One (face 06) ---------------------------------------------------------------------------------------

resolve_copy(
    214511, 'The Big One', School.FIRE, 'The Big One goes off.',
    f'{_D6}, MT13 (heroic face 06, ruling 40): The Big One arrives at the room\'s center and 100% of the reference row '
    'is split evenly among the players within 8 yd of it (four inside: 25% each); with nobody there, everyone in the '
    'room takes the whole 100% (designer question 1). The tank row on the tank. A shared hit: never Weakened. Resolve '
    'copy (Fire) of the stock The Big One 12562.',
    icon=_ICON_BOMB,
)


# --- the boss kit's creatures -----------------------------------------------------------------------------------------


def _bomb(entry: int, name: str, display: int, *, scale: float = BOMB_SCALE, flags: int = 0):
    """A walking bomb: the stock Walking Bomb 7915's shape (faction 63, mechanical, level 28 normal, no melee, no
    loot) under its own entry (s7 #40 A: never the gear's 301100); passive, walked by the boss. HealthModifier 0.469
    gives about 400 on 853; the script sets the mode's health anyway (400 / 5,000 / 7,000)."""
    columns = {
        **KIT_CREATURE, 'faction': FACTION_GNOMEREGAN_MECHANICAL, 'minlevel': 28, 'maxlevel': 28, 'rank': 0,
        'unit_class': 1, 'unit_flags': flags, 'HealthModifier': 0.469, 'DamageModifier': 0.0,
        'detection_range': 0.0, 'lootid': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
        'ScriptName': 'npc_gnomer_walking_bomb',
    }
    if entry in _HEROIC_BOMBS:
        columns['difficulty_entry_1'] = heroic_entry(entry)
    creature_template(entry, name, **columns)
    creature_model(entry, display_id=display, scale=scale)


_bomb(301120, 'Walking Bomb', DISPLAY_BOMB)
_bomb(301121, 'Incendiary Bomb', DISPLAY_BOMB)
_bomb(301122, 'Frost Bomb', DISPLAY_BOMB_FROST)
_bomb(301123, 'Radioactive Bomb', DISPLAY_BOMB_RADIO)
_bomb(301124, 'The Big One', DISPLAY_BIG_ONE, scale=BIG_ONE_SCALE, flags=_UNIT_FLAG_NON_ATTACKABLE)


def _stalker(entry: int, name: str, display: int, scale: float = 1.0):
    creature_template(
        entry, name, **{**KIT_HELPER, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1,
                        'ScriptName': 'npc_gnomer_thermaplugg_stalker'},
    )
    creature_model(entry, display_id=display, scale=scale)


_stalker(301125, 'Gnome Face Stalker', DISPLAY_INVISIBLE_STALKER)
_stalker(301126, 'Land Mine', DISPLAY_MINE, MINE_SCALE)
_stalker(301127, 'Thermaplugg Zone Stalker', DISPLAY_INVISIBLE_STALKER)

assert MINE_SCALE_RANGE[0] <= MINE_SCALE <= MINE_SCALE_RANGE[1]
