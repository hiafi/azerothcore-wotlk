"""
Blackrock Depths build WP-D24: Emperor Dagran Thaurissan's hard mode, the Avatar of Ragnaros (heroic, Dagran first)
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.6, s3.7 row D24, s3.10, s7 #15 and #19;
build spec docs/dungeons/blackrock-depths-4-imperial-seat.md "Hard mode" and "Build spec" EM11-EM13, rulings 77-81,
88). WP-D24 owns this file (its spells: kSpellsAvatar 211660-211709 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h only; EmperorHardModeLogic.h names the same ids). The engine side is
src/BlackrockDepths/emperor_hard_mode.cpp, on D23's hooks (EmperorFight.h).

No creature or object of its own: the Avatar is Dagran (9019, heroic 310344) with display 11121 at a creature scale
set by the script (0.15, _visuals.py AVATAR_SCALE_RANGE), 260,000 health set by the script, rooted on the throne; Moira
(8929) is caged by D23 (211630 / 211631). The stones are the shared generic stalker 300796 with a state aura. The
texts are D23's (9019 groups 11 and 12, rev_emperor_blackrock_depths.sql); no SQL rev of its own (no text, spawn or
SmartAI row to write). The hard mode loot list and the Dark Keeper Key at 100% are L-2's (the loot bit rides the kill).

Spells (looks from ._visuals, V-2's EM_ picks; every look unconfirmed until seen in game):

  211660  Magma Clap          EM12 the 3 s bar (Fire, not interruptible: no kickable school is touched, rule 5)
  211661  Magma Clap          EM12 a player's hit: exact from the script, 70% within 10 yd falling to 15% at 40 yd
                              (the tank row on the tank); Magma Blast 20565's impact (SV 5721)
  211662  Magma Clap          look: the Fire Nova ring at his feet as it lands (SV 6899)
  211663  Volcanic Blast      EM13 the 5 s mark on the marked player: the orange rune ring (SV 90613); a marker, not
                              dispellable (rule 11)
  211664  Volcanic Blast      EM13 a share of the 80%: exact from the script (the kit's SplitShares); Lava Burst's
                              missile and impact (SV 11565)
  211665  Volcanic Stone      EM13 the stone's tick: 8% a second for 30 s (resolve copy, Fire)
  211666  Volcanic Stone      look: the 5 yd lava pool on a stalker for 30 s (SV 90607)
  211667  Ragnaros Awakens    look: Pillar of Fire at the throne as he jumps there (SV 9727)
  211668  Ragnaros Awakens    look: Massive Eruption at the throne as the Avatar rises (SV 889)
  211669  Magma Blast         rule 10: his victim out of his reach 3 s (outside the two casts' windows and walk backs):
                              every 2 s, 20% of its row (SV 5721)
  211670-211709 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    EM_FIRESTORM,
    EM_MAGMA_CLAP_HIT,
    EM_MAGMA_CLAP_RING,
    EM_RAGNAROS_AWAKENS,
    EM_VOLCANIC_BLAST,
    EM_VOLCANIC_BLAST_MARK,
    EM_VOLCANIC_STONE,
)

_D24 = 'Blackrock Depths build WP-D24 (the Emperor\'s hard mode, the Avatar of Ragnaros)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')
_SCRIPT_EXACT = 'Blackrock Depths: an exact amount from the script (CastCustomSpell base point 0)'

# --- constants (EmperorHardModeLogic.h; lib/test_blackrock_depths_emperor_hard_mode.py pins each against the header) --

CLAP_CAST_MS = 3000                 # kClapCastMs
BLAST_MARK_MS = 5000                # kBlastMarkMs
STONE_MS = 30000                    # kStoneMs
MAGMA_BLAST = (2000, 2000)          # kMagmaBlastPct 20 (hundredths; heroic only: both columns hold it)

_DEFENSE_MAGIC = 1
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

# Stock icons (client Spell.dbc SpellIconID of the named spell, read 2026-11-17)
_ICON_MAGMA_BLAST = 678             # Magma Blast 20565
_ICON_FIRE_NOVA = 33                # Fire Nova 23462
_ICON_LAVA_BURST = 3064             # Lava Burst 51505
_ICON_WRATH_OF_RAGNAROS = 816       # Wrath of Ragnaros 20566
_ICON_ERUPTION = 1137               # Massive Eruption 20483

# The scripted hits: no redirection or reflection, no crit, always hits, ignores the caster's modifiers.
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
    AttributesEx2=ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
)


def _exact_hit(spell_id: int, name: str, visual: int, icon: int, desc: str, notes: str):
    """A triggered single-target Fire hit of an exact amount from the script (CastCustomSpell base point 0; the script
    picks the percent of the target's row): ignores the caster's modifiers, cannot crit, always hits."""
    return spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_EXACT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, SpellVisualID_1=visual, DefenseType=_DEFENSE_MAGIC,
                              **{**_HIT_ATTRS, 'AttributesEx2': ATTR2_CANT_CRIT | ATTR2_IGNORE_LINE_OF_SIGHT}),
    )


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, icon: int):
    """A look-only Fire spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG),
    triggered."""
    return spell(
        id=spell_id, name=name, school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- EM12 Magma Clap --------------------------------------------------------------------------------------------------

magma_clap_cast_211660 = cast_bar(
    211660, 'Magma Clap', CLAP_CAST_MS, 'The Avatar brings his hands together. Get away from him!',
    f'{_D24}, EM12: the 3 s bar (boss emote 11, D23\'s text), 10 s after the rise, then every 20 s. No effect: the '
    'registry\'s 30 yd RunOut from him (tag 31) is the bots\' telegraph and the script deals the falloff (211661) as '
    'it ends. Not interruptible (cast_bar); Fire: the fight\'s only kickable cast (Moira\'s Shadow Mind Blast) is '
    'caged away by then (rule 5).',
    icon=_ICON_MAGMA_BLAST, school=School.FIRE,
)

magma_clap_211661 = _exact_hit(
    211661, 'Magma Clap', EM_MAGMA_CLAP_HIT, _ICON_MAGMA_BLAST, 'Magma surges from the Avatar.',
    f'{_D24}, EM12: as the bar ends, everyone of the fight (the tank too: he is rooted, so the tank runs out and walks '
    'back): 70% of the target\'s row within 10 yd of him, falling linearly to 15% at 40 yd and beyond (the tank row on '
    'the tank). Exact from the script (DungeonKit::RefFlatOn), no Weakened (the spec names none). Magma Blast 20565\'s '
    'impact (SV 5721). Ignores LoS (the dais).',
)

magma_clap_ring_211662 = self_visual(
    211662, 'Magma Clap', EM_MAGMA_CLAP_RING,
    f'{_D24}, EM12: the ring at his feet as the clap lands (Fire Nova 23462\'s SV 6899). Look only.',
    icon=_ICON_FIRE_NOVA, school=School.FIRE,
)

# --- EM13 Volcanic Blast and the Volcanic Stone -----------------------------------------------------------------------

volcanic_mark_211663 = spell(
    id=211663, name='Volcanic Blast', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=BLAST_MARK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_LAVA_BURST,
    notes=f'{_D24}, EM13: the mark, 15 s after the rise, then every 25 s, on a random player of the fight (the tank '
          'too, ruling 88; boss emote 12 names them). 5 s; the registry\'s 8 yd Stack on them (tag 32) is the bots\' '
          'call to gather. A marker, not dispellable (Dispel none, rule 11); removed as the blast lands, at the end of '
          'the fight and on a map change. The orange rune ring under the bearer (SV 90613, Blackrock Spire\'s).',
    raw_overrides=kit_raw('Marks the target for a Volcanic Blast. Allies within 8 yards share the blast.',
                          'Marked for a Volcanic Blast: stand with your allies!', instant=True,
                          SpellVisualID_1=EM_VOLCANIC_BLAST_MARK, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)

volcanic_blast_211664 = _exact_hit(
    211664, 'Volcanic Blast', EM_VOLCANIC_BLAST, _ICON_LAVA_BURST,
    'A volcanic blast, shared by those who stand together.',
    f'{_D24}, EM13: the mark\'s 5 s end: 80% of the reference row split evenly among everyone within 8 yd of the '
    'marked player, the marked player included (3 or more: about 27% each; alone: 80%). Exact from the script (the '
    'kit\'s SplitShares, the non-tank row: the Balnazzar mark precedent). Lava Burst 51505\'s missile and impact (SV '
    '11565; NEVER Eruption SV 5043, which draws nothing).',
)

volcanic_stone_211665 = resolve_copy(
    211665, 'Volcanic Stone', School.FIRE, 'The molten stone burns.',
    f'{_D24}, EM13: the stone the blast leaves where the mark stood: a 5 yd persistent Zone for 30 s (registry tag '
    '33), 8% of the row a second, no Weakened, no slow rider. At most 2 stand at once (30 s stones every 25 s). A copy '
    'of the mod-boss-mechanics resolve spell with the Fire school.',
    icon=_ICON_LAVA_BURST,
)

volcanic_stone_look_211666 = spell(
    id=211666, name='Volcanic Stone', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_LAVA_BURST,
    notes=f'{_D24}, EM13: the stone\'s look: the shared generic stalker (300796) at the stone casts it on itself and '
          'despawns 30 s later (the stone\'s life; Dagran\'s cleanup despawns it with the fight): the shipped 5 yd '
          'lava pool state (SV 90607, Blackrock Spire\'s ladder), under the registry\'s 5 yd marker. Look only.',
    raw_overrides=kit_raw(SpellVisualID_1=EM_VOLCANIC_STONE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, CastingTimeIndex=1),
)

# --- EM11 Ragnaros Awakens (the transition's looks) -------------------------------------------------------------------

awakens_pillar_211667 = _look_at_point(
    211667, 'Ragnaros Awakens', EM_RAGNAROS_AWAKENS,
    f'{_D24}, EM11: Dagran casts it at the throne as the knockback throws everyone back and he jumps there (yell 10 is '
    'D23\'s): Pillar of Fire\'s flame spiral (SV 9727; the spec\'s Wrath of Ragnaros SV 143 is a chest flash, VR). '
    'Look only.',
    _ICON_WRATH_OF_RAGNAROS,
)

awakens_eruption_211668 = _look_at_point(
    211668, 'Ragnaros Awakens', EM_FIRESTORM,
    f'{_D24}, EM11: Dagran casts it at the throne 3 s later as the display becomes the Avatar (CDI 11121): Massive '
    'Eruption 20483\'s SV 889. Look only.',
    _ICON_ERUPTION,
)

# --- rule 10: Magma Blast ---------------------------------------------------------------------------------------------

magma_blast_211669 = spell(
    id=211669, name='Magma Blast', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=MAGMA_BLAST[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_MAGMA_BLAST,
    notes=f'{_D24}, rule 10 (no free damage window): the rooted Avatar answers his victim standing out of his reach '
          'for 3 s (outside the Magma Clap\'s cast and the Volcanic Blast\'s mark, and the 5 s walk back after each): '
          'every 2 s, 20% of the target\'s row (the tank row on the tank), as Ragnaros\'s own Magma Blast 20565 and '
          'the Roccor precedent (designer question). Both hundredths columns hold 20% (heroic only). Ignores his '
          'modifiers. Magma Blast 20565\'s SV 5721.',
    raw_overrides=kit_raw('Hurls magma at a foe out of the Avatar\'s reach.', instant=True,
                          SpellVisualID_1=EM_MAGMA_CLAP_HIT, EffectMiscValueB_1=MAGMA_BLAST[1],
                          DefenseType=_DEFENSE_MAGIC, **_HIT_ATTRS),
)
scripted_by(magma_blast_211669, 'spell_dungeon_refflat_damage')
