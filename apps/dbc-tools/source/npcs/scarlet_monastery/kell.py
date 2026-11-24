"""
Scarlet Monastery build WP-D6: Ambrose Kell, the Antiquarian (Kell 300910, relic trigger 300911, Gallery Skeleton
300912; GOs 301315-301318) (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D6;
build spec docs/dungeons/scarlet-monastery-2-library.md "Ambrose Kell, the Antiquarian", AN1-AN5c). WP-D6 owns this
file; WP-S0 wrote the skeleton. The GO templates, his texts, his spawn and the model-info rows dbc-tools cannot declare
are data/sql/updates/pending_db_world/rev_kell_scarlet_monastery.sql.

- 300910 Ambrose Kell <Master of Antiquities>: a NEW boss, boss_ambrose_kell_rework (modules/mod-dungeon-bosses
  src/ScarletMonastery/boss_ambrose_kell_rework.cpp; SmKell::kBound is flipped with this declaration). Level 34 mage
  (unit_class 8), Scarlet Crusade (faction 67), elite (rank 1), the build spec's normal health (44k = HealthModifier
  50.749 on the level 34 mage base 867), DamageModifier 2.0 (Doan's stock 2.4 and Vishas's 2.0: a mage's melee is a
  filler, the Cane is his swing), stun immunity 1972, INSTANCE_BIND (the encounter row's credit creature: FD-SM's
  dungeon_encounter(1076, ..., credit_creature(300910))), display 2524 (Scarlet Sorcerer, designer 2026-11-18),
  SmartAI off, lootid 300910 (L-1's lists). Heroic health (240k) and the tier's melee are WP-H's overrides.
- 300911 the relic trigger: an invisible, unselectable helper (KIT_HELPER, no script). One stands on each case and
  plays its looks (the shatter, the staff's missiles, the skeleton's climb), plus one under each cloud and each flask
  pool; the boss despawns them all. Level 34 (a caster level 0 spell needs none). No heroic template (a stalker).
- 300912 Gallery Skeleton: a level 33 warrior (1.2k = HealthModifier 1.0811 on the base 1,110), undead (faction 21),
  display 9786 (SkeletonNaked, black skin), DamageModifier 1.5 (the Angerforge-officer add level: about 2% of the tank
  row a swing at 2.0 s, four alive about 9% per 2 s; rule 19), no loot, no XP, no script (the stock AI; Kell sends it
  at the tank). Its heroic template (6k, level 60) is WP-H's.
- GOs 301315 pedestal (GODI 7695), 301316 cask (288), 301317 staff (1708), 301318 skull (217): in the rev.

Spells (kSpellsKell 212570-212609; KellLogic.h names the same ids; looks from ._visuals, WP-V's AN_* picks, every look
unconfirmed until seen in game). His damage is a percent of the reference row (the tank row on the tank): the registry
lands the cloud, the lines, the flask and the pool through resolve copies; the Cane, the Torrent and the burst bind the
kit's spell_dungeon_refflat_damage (the percent rides in hundredths in the effect, EffectMiscValueB on heroic):

  212570  Unseal               AN1 the 2 s cast bar (Physical, not interruptible; emote line names the relic)
  212571  Unseal               AN1 the shatter look on the case's trigger (Crystal Shatter's SV 7984)
  212572  Plague Cask          AN2 the cloud's tick: resolve copy, Nature, 6% / 10% a second, lingering
  212573  Plague Cask          AN2 the cloud's look, an aura on a trigger (Disease Cloud's SV 7184)
  212574  Arcane Line          AN3 a staff line's hit: resolve copy, Arcane, 35% / 45% and Weakened
  212575  Arcane Line          AN3 the missile along a line (Arcane Barrage's SV 9947), a look at the line's end
  212576  Raise Gallery Skeleton   AN4 the climb-out look on the trigger (Summon Skeletons' SV 2596)
  212577  Gilded Cane          his swing on the tank: 20% / 30% Physical (kit percent script)
  212578  Plague Flask         AN5a the landing's hit: resolve copy, Nature, 40% and Weakened (heroic)
  212579  Plague Flask         AN5a the pool's tick: resolve copy, Nature, 8% a second (heroic)
  212580  Plague Flask         AN5a the vial's flight, a look at the spot (Plague Vial's SV 9705)
  212581  Plague Flask         AN5a the pool's look, an aura on a trigger (the shipped goo puddle SV 90343)
  212582  Arcane Torrent       AN5b the 3 s interruptible cast: 40% Arcane to every player (heroic)
  212583  Bone Curse           AN5c the Magic debuff, 8 s (Bone Armor's SV 2737); an undispelled expiry bursts
  212584  Bone Burst           AN5c the burst on the cursed player: 25% Physical (Bone Shards' SV 4362)
  212585-212587  Trophy Powers (heroic): Kell's look after the first cask / staff / skull
  212588-212609 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_NO_ACTIVE_DEFENSE,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_SCARLET_CRUSADE,
    FACTION_UNDEAD,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    AN_ARCANE_TORRENT,
    AN_BONE_CURSE,
    AN_BONE_CURSE_BURST,
    AN_PLAGUE_CLOUD,
    AN_PLAGUE_FLASK,
    AN_PLAGUE_FLASK_POOL,
    AN_SHATTER,
    AN_SKELETON,
    AN_STAFF_LINE,
    AN_TROPHY_CASK,
    AN_TROPHY_SKULL,
    AN_TROPHY_STAFF,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_KELL,
    DISPLAY_KELL_SKELETON,
)

_D6 = 'Scarlet Monastery build WP-D6 (Ambrose Kell)'

# --- the creatures ---------------------------------------------------------------------------------------------------

# The creatures' heroic entries (difficulty_entry_1 = their id in source/world/heroic_ids.lock, minted by H's write run:
# the declared wave 1 kit adds in entry order). None until H's table names them: generate.py --check then prints the
# number each full row must carry (lib/dungeon_heroic.py). Shared-file request in the WP-D6 report.
KELL_HEROIC = 310467
GALLERY_SKELETON_HEROIC = 310468

KELL = 300910
RELIC_TRIGGER = 300911
GALLERY_SKELETON = 300912


_CREATURE_TYPE_UNDEAD = 6
_FLAGS_EXTRA_NO_XP = 0x40
_RANK_ELITE = 1
_CLASS_WARRIOR = 1
_CLASS_MAGE = 8

# The build spec's normal health at 5 players (S0's table): 44k = 50.749 x 867 (the level 34 mage), 1.2k = 1.0811 x
# 1,110 (the level 33 warrior). creature_classlevelstats basehp0, live 2026-11-20.
KELL_HEALTH_MODIFIER = 50.749
KELL_DAMAGE_MODIFIER = 2.0
SKELETON_HEALTH_MODIFIER = 1.0811
SKELETON_DAMAGE_MODIFIER = 1.5


def _heroic_entry(columns: dict, heroic_entry) -> dict:
    """`columns` with difficulty_entry_1 when H's table names the heroic entry (a declared full row must carry it)."""
    if heroic_entry:
        return {**columns, 'difficulty_entry_1': heroic_entry}
    return columns


ambrose_kell_300910 = creature_template(300910, 'Ambrose Kell', **_heroic_entry({
    **KIT_CREATURE, 'subname': 'Master of Antiquities', 'minlevel': 34, 'maxlevel': 34, 'rank': _RANK_ELITE,
    'unit_class': _CLASS_MAGE, 'faction': FACTION_SCARLET_CRUSADE, 'type': 7, 'exp': 0,
    'HealthModifier': KELL_HEALTH_MODIFIER, 'DamageModifier': KELL_DAMAGE_MODIFIER, 'ManaModifier': 3.0,
    'ExperienceModifier': 2.0, 'BaseAttackTime': 2000, 'speed_run': 1.14286, 'detection_range': 20.0,
    'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 300910, 'mingold': 250, 'maxgold': 800,
    'flags_extra': 1, 'ScriptName': 'boss_ambrose_kell_rework', 'AIName': '',
}, KELL_HEROIC))
creature_model(300910, display_id=DISPLAY_KELL)

relic_trigger_300911 = creature_template(300911, 'Relic Trigger', **{
    **KIT_HELPER, 'minlevel': 34, 'maxlevel': 34, 'rank': 0, 'unit_class': _CLASS_WARRIOR,
})
creature_model(300911, display_id=DISPLAY_INVISIBLE_STALKER)

gallery_skeleton_300912 = creature_template(300912, 'Gallery Skeleton', **_heroic_entry({
    **KIT_CREATURE, 'faction': FACTION_UNDEAD, 'type': _CREATURE_TYPE_UNDEAD, 'minlevel': 33, 'maxlevel': 33,
    'rank': 0, 'unit_class': _CLASS_WARRIOR, 'unit_flags': 0, 'HealthModifier': SKELETON_HEALTH_MODIFIER,
    'DamageModifier': SKELETON_DAMAGE_MODIFIER, 'BaseAttackTime': 2000, 'speed_run': 1.14286,
    'detection_range': 18.0, 'CreatureImmunitiesId': 0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
    'mingold': 0, 'maxgold': 0, 'ExperienceModifier': 0.0, 'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': '',
    'AIName': '',
}, GALLERY_SKELETON_HEROIC))
creature_model(300912, display_id=DISPLAY_KELL_SKELETON)

# --- constants (KellLogic.h; lib/test_scarlet_monastery_kell.py pins each against the header) -------------------------

UNSEAL_CAST_MS = 2000               # kUnsealCastMs
CLOUD_PCT = (600, 1000)             # kCloudPct 6 / 10 (hundredths; the registry sets the damage, these are the notes)
LINE_PCT = (3500, 4500)             # kLinePct 35 / 45
CANE_PCT = (2000, 3000)             # kCanePct 20 / 30 (hundredths: normal in the effect, heroic in EffectMiscValueB)
FLASK_PCT = 4000                    # kFlaskPct 40 (heroic only)
POOL_PCT = 800                      # kPoolPct 8
TORRENT_CAST_MS = 3000              # kTorrentCastMs
TORRENT_PCT = 4000                  # kTorrentPct 40 (heroic only: the same on both)
CURSE_MS = 8000                     # kCurseMs
BURST_PCT = 2500                    # kBurstPct 25 (heroic only)

_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_DISPEL_MAGIC = 1
_PREVENTION_SILENCE = 1
_SPELL_INTERRUPT_FLAGS_KICK = 15
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100

_SCRIPT_REFFLAT = ('Scarlet Monastery D6: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn: the tank row on the tank)')

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_CRYSTAL_SHATTER = 1954        # Crystal Shatter 32589
_ICON_PLAGUE_CLOUD = 1614           # Plague Cloud 3256
_ICON_ARCANE_BARRAGE = 3376         # Arcane Barrage 44425
_ICON_SUMMON_SKELETONS = 1499       # Summon Skeletons 33977
_ICON_MACE_SMASH = 2634             # Mace Smash 48288 (the Cane)
_ICON_PLAGUE_VIAL = 11              # Plague Vial 43115
_ICON_ARCANE_TORRENT = 87           # Arcane Torrent 25046
_ICON_BONE_ARMOR = 93               # Bone Armor 11445
_ICON_BONE_SHARDS = 1590            # Bone Shards 17014

# --- AN1 Unseal -------------------------------------------------------------------------------------------------------

unseal_cast_212570 = cast_bar(
    212570, 'Unseal', UNSEAL_CAST_MS, 'Ambrose Kell unseals a case from his collection.',
    f'{_D6}, AN1 The Collection: the 2 s bar players read while he turns to the sealed case nearest him (an emote '
    'line 1 to 3 names the relic). Not interruptible: the case wakes when the bar ends whatever happens to it (the '
    'script\'s clock). Physical: a kicked Arcane Torrent (heroic) locks Arcane, never the Unseal bar (rule 5). '
    'First at 10 s (heroic 8 s), then every 20 s (15 s).',
    icon=_ICON_CRYSTAL_SHATTER,
)

unseal_shatter_212571 = self_visual(
    212571, 'Unseal', AN_SHATTER,
    f'{_D6}, AN1: the shatter, cast by the case\'s relic trigger on itself (triggered) the moment the case wakes: '
    'Crystal Shatter 32589\'s SpellVisual 7984 (shadow hands and a soul shatter). The client has no glass-case model, '
    'so the glass is implied: the shatter plays over the pedestal as its relic vanishes. Look only.',
    icon=_ICON_CRYSTAL_SHATTER,
)

# --- AN2 Plague Cask --------------------------------------------------------------------------------------------------

plague_cloud_212572 = resolve_copy(
    212572, 'Plague Cask', School.NATURE, 'A cloud of poison.',
    f'{_D6}, AN2 Plague Cask: the cloud\'s tick, a persistent 8 yd Zone round the bay\'s mouth (the case spot moved '
    '4 yd toward the aisle) from the cask\'s wake for the rest of the fight, one tick a second: 6% (heroic 10%) of '
    'the reference row, the tank row on the tank. Lingering: no Weakened (registry tag 2). Copy of the '
    'mod-boss-mechanics resolve spell 205001 (Nature).',
    icon=_ICON_PLAGUE_CLOUD,
)

plague_cloud_look_212573 = spell(
    id=212573, name='Plague Cask', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_PLAGUE_CLOUD,
    notes=f'{_D6}, AN2: the cloud\'s look, a DUMMY aura a relic trigger casts on itself (triggered), one at the '
          'cloud\'s center for the fight: Disease Cloud 24063\'s SpellVisual 7184 (a PersistentAreaKit, '
          'GreenRadiationFog; the client may not stretch it to 8 yd, VR RISKY: the registry\'s ring is the exact '
          'edge; fallback SV 90561 AN_PLAGUE_CLOUD_ALT). No effect; the trigger is a summon of Kell and goes with '
          'the fight.',
    raw_overrides=kit_raw('A cloud of poison.', 'A cloud of poison.', CastingTimeIndex=1,
                          SpellVisualID_1=AN_PLAGUE_CLOUD, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- AN3 Kirin Tor Staff ----------------------------------------------------------------------------------------------

arcane_line_212574 = resolve_copy(
    212574, 'Arcane Line', School.ARCANE, 'A line of arcane power.',
    f'{_D6}, AN3 Kirin Tor Staff: a line\'s hit, 4 yd wide and 40 yd long out of the case at a random angle into the '
    'hall, a 2 s marker, three a volley every 8 s from 2 s after the wake: 35% (heroic 45%) of the reference row and '
    '1 Weakened, the tank row on the tank (registry tag 3). Copy of the resolve spell 205001 (Arcane).',
    icon=_ICON_ARCANE_BARRAGE,
)


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, icon: int):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), triggered (the
    Baelgar / Fineous look shape)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


arcane_line_look_212575 = _look_at_point(
    212575, 'Arcane Line', AN_STAFF_LINE,
    f'{_D6}, AN3: a missile along a line, cast by the staff case\'s trigger at the line\'s far end (triggered) as the '
    'marker starts: Arcane Barrage 44425\'s SpellVisual 9947 (`mage_arcanebarrage_missile` and its impact). The '
    'marker is the registry\'s; this is the read of "power fanning out of the staff". Look only.',
    icon=_ICON_ARCANE_BARRAGE,
)

# --- AN4 Necromancer's Skull ------------------------------------------------------------------------------------------

raise_skeleton_look_212576 = self_visual(
    212576, 'Raise Gallery Skeleton', AN_SKELETON,
    f'{_D6}, AN4: a skeleton claws out of the skull case, cast by the case\'s trigger on itself (triggered) as the '
    'Gallery Skeleton is summoned there: Summon Skeletons 33977\'s SpellVisual 2596 (ritual hands and a shadow '
    'impact). The skeleton is summoned by the script (a TempSummon of Kell). Look only.',
    icon=_ICON_SUMMON_SKELETONS,
)

# --- Gilded Cane ------------------------------------------------------------------------------------------------------

gilded_cane_212577 = spell(
    id=212577, name='Gilded Cane', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=CANE_PCT[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_MACE_SMASH,
    notes=f'{_D6}, Gilded Cane: his swing on the tank, 5 s after the pull then every 10 s: 20% (heroic 30%: '
          'EffectMiscValueB) of the tank\'s row, Physical, instant, never missed (always hits, no active defense, '
          'cannot crit) and ignoring his modifiers. Cast by Kell (triggered) on his victim. Tank work, not a '
          'mechanic: no Weakened, no marker. Binds the kit\'s spell_dungeon_refflat_damage.',
    raw_overrides=kit_raw('Strikes with a gilded cane.', instant=True, EffectMiscValueB_1=CANE_PCT[1],
                          DefenseType=_DEFENSE_MELEE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(gilded_cane_212577, 'spell_dungeon_refflat_damage')

# --- AN5a Plague Flask (heroic) ---------------------------------------------------------------------------------------

plague_flask_212578 = resolve_copy(
    212578, 'Plague Flask', School.NATURE, 'A vial of plague shatters on the ground.',
    f'{_D6}, AN5a Plague Flask (heroic): the landing\'s hit, 4 yd at a random player\'s spot (the tank included) as '
    'it was when Kell threw the vial, 2 s of flight later, every 12 s from the first cask\'s wake: 40% of the '
    'reference row and 1 Weakened, the tank row on the tank (registry tag 51). Copy of the resolve spell 205001 '
    '(Nature). The pool (212579) follows.',
    icon=_ICON_PLAGUE_VIAL,
)

plague_flask_pool_212579 = resolve_copy(
    212579, 'Plague Flask', School.NATURE, 'A pool of plague.',
    f'{_D6}, AN5a: the pool\'s tick, a persistent 4 yd Zone where the vial landed for 15 s, one tick a second: 8% of '
    'the reference row (registry tag 52). Lingering: no Weakened. Copy of the resolve spell 205001 (Nature).',
    icon=_ICON_PLAGUE_VIAL,
)

plague_flask_throw_212580 = _look_at_point(
    212580, 'Plague Flask', AN_PLAGUE_FLASK,
    f'{_D6}, AN5a: the vial\'s flight, cast by Kell at the marked spot (triggered) as the 2 s marker starts: Plague '
    'Vial 43115\'s SpellVisual 9705 (nature hands, the bottle missile, a poison impact). Look only.',
    icon=_ICON_PLAGUE_VIAL,
)

plague_flask_pool_look_212581 = spell(
    id=212581, name='Plague Flask', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_PLAGUE_VIAL,
    notes=f'{_D6}, AN5a: the pool\'s look, a DUMMY aura on a relic trigger summoned at the landing for 16 s '
          '(triggered): the shipped Deadmines goo puddle state SV 90343 (4 yd, exact), under the registry\'s 4 yd '
          'ring. No effect; the trigger despawns with the pool.',
    raw_overrides=kit_raw('A pool of plague.', 'A pool of plague.', CastingTimeIndex=1,
                          SpellVisualID_1=AN_PLAGUE_FLASK_POOL, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- AN5b Arcane Torrent (heroic) -------------------------------------------------------------------------------------

arcane_torrent_212582 = spell(
    id=212582, name='Arcane Torrent', school=School.ARCANE, dispel=0, mechanic=0, attributes=0,
    cast_time_ms=TORRENT_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=TORRENT_PCT - 1, die_sides=1,
                    implicit_target_a=TARGET_SRC_CASTER, implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY,
                    radius_yards=100.0, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_ARCANE_TORRENT,
    notes=f'{_D6}, AN5b Arcane Torrent (heroic, the staff\'s Trophy Power): a 3 s cast every 15 s from the first '
          'staff\'s wake (emote line 5), an expected interrupt. NOT triggered, so the bar shows and a kick stops it: '
          'InterruptFlags 15 and PreventionType 1 (a silence); his immunity set 1972 holds no INTERRUPT or SILENCE. '
          'Missed it deals 40% (the same on both difficulties: heroic only) of the reference row, Arcane, to every '
          'player within 100 yd (the tank row on the tank, never missed, ignores line of sight and his modifiers): '
          'one miss is survivable. Binds the kit\'s spell_dungeon_refflat_damage. On the bots\' interrupt list '
          '(priority 3). Arcane: Unseal\'s bar is Physical (rule 5), so a kick on this never locks the Unseal. '
          'Arcane Torrent 25046\'s SV 7346.',
    raw_overrides=kit_raw('Kell channels the power of the staff: Arcane damage to everyone.',
                          EffectMiscValueB_1=TORRENT_PCT, DefenseType=_DEFENSE_MAGIC,
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          SpellVisualID_1=AN_ARCANE_TORRENT,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(arcane_torrent_212582, 'spell_dungeon_refflat_damage')

# --- AN5c Bone Curse (heroic) -----------------------------------------------------------------------------------------

bone_curse_212583 = spell(
    id=212583, name='Bone Curse', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=CURSE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_BONE_ARMOR,
    notes=f'{_D6}, AN5c Bone Curse (heroic, the skull\'s Trophy Power): a Magic debuff on a random player, the tank '
          'included, every 15 s from the first skull\'s wake, 8 s. An expected dispel (the bots\' dispel list, '
          'priority 2); undispelled it expires into Bone Burst (212584) and a Gallery Skeleton rises from the player '
          '(spell_sm_kell_bone_curse: AFTER_REMOVE by expiry; a dispel, a death, a reset or a map change remove it '
          'by another mode and nothing happens). A DUMMY: the read is Bone Armor 11445\'s lasting state SV 2737 on '
          'the player. Dropped on a map change; one curse at a time per player (the script excludes carriers).',
    raw_overrides=kit_raw('Bone Curse: in 8 seconds the bones burst out of you.',
                          'Cursed. If it expires, the bones burst out of you and a skeleton rises. Dispel it.',
                          CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=AN_BONE_CURSE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(bone_curse_212583, 'spell_sm_kell_bone_curse')

bone_burst_212584 = spell(
    id=212584, name='Bone Burst', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=BURST_PCT - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_BONE_SHARDS,
    notes=f'{_D6}, AN5c: the burst when Bone Curse expires undispelled, cast by Kell (triggered) on the cursed '
          'player: 25% (the same on both: heroic only) of the reference row, Physical, instant, never missed, '
          'ignoring his modifiers. Binds the kit\'s spell_dungeon_refflat_damage. The skeleton that rises from them '
          'is the script\'s. Bone Shards 17014\'s SpellVisual 4362 (`mangle_impact_demon`).',
    raw_overrides=kit_raw('The bones burst out of the cursed.', instant=True, EffectMiscValueB_1=BURST_PCT,
                          DefenseType=_DEFENSE_MELEE, SpellVisualID_1=AN_BONE_CURSE_BURST,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(bone_burst_212584, 'spell_dungeon_refflat_damage')

# --- AN5 Trophy Powers (heroic) ---------------------------------------------------------------------------------------


def _trophy(spell_id: int, name: str, visual: int, icon: int, relic: str, power: str):
    """Kell's look after the first relic of a type wakes (heroic): a lasting DUMMY aura on himself, removed with the
    fight. Look only."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'{_D6}, AN5 Trophy Powers (heroic): Kell casts it on himself (triggered) the first time a {relic} '
              f'wakes ({power}); a second case of the type adds nothing. His look changes for the rest of the fight '
              f'(SV {visual}); the yell line 4 is the tell. Not dispellable or stealable; removed on his reset, evade '
              'and death. No effect of its own: the power is the script\'s beat.',
        raw_overrides=kit_raw(f'Ambrose Kell has taken the power of the {relic}.',
                              f'The power of the {relic}.', CastingTimeIndex=1, SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


trophy_cask_212585 = _trophy(212585, 'Trophy: Plague Cask', AN_TROPHY_CASK, _ICON_PLAGUE_VIAL, 'cask',
                             'Plague Flask every 12 s')
trophy_staff_212586 = _trophy(212586, 'Trophy: Kirin Tor Staff', AN_TROPHY_STAFF, _ICON_ARCANE_TORRENT, 'staff',
                              'Arcane Torrent every 15 s')
trophy_skull_212587 = _trophy(212587, "Trophy: Necromancer's Skull", AN_TROPHY_SKULL, _ICON_BONE_ARMOR, 'skull',
                              'Bone Curse every 15 s')
