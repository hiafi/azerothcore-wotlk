"""
Gnomeregan build WP-D1: Techbot (301105), his Dupe Bugs (301106) and the after-images (301107), normal and heroic
(.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D1 and its kick and dispel table, s3.6, s3.8,
s3.9 rows 1-2, s7 #13 A, #14 A, #36-#38 A; build spec docs/dungeons/gnomeregan-rework.md SP 525-583 (TB1-TB9), design
SP 375-524, rulings 9-13, 51, 54, 61). WP-D1 owns this file (its spells: kSpellsTechbot 214300-214339 of
modules/mod-dungeon-bosses src/Gnomeregan/GnomereganRework.h only; TechbotLogic.h names the same ids and numbers, and
lib/test_gnomeregan_techbot.py diffs them). The engine side is src/Gnomeregan/boss_techbot_rework.cpp (the boss, the
bug, the after-image) and TechbotMachine.cpp (the Duplicator); the texts are
data/sql/updates/pending_db_world/rev_techbot_gnomeregan.sql.

- 301105 Techbot: a copy of the outside Techbot 6231 (SELECT 2026-11-26; 6231 on map 0 stays stock, s7 #14 A) at level
  28 elite, faction 63, bound to boss_techbot_rework with the skeleton's columns (SmartAI off, immunity 1972, both
  assist flags, detection range 12, DamageModifier 1.7 until T), normal health 60,001 = 70.34 on the level 28 warrior
  base 853 (s3.6, s7 #1 A: spec 30,000 x2.0). Heroic health and his heroic template are WP-H's; his loot (the Memory
  Core 9277 and Guts 9309, quest-required) is WP-L-1's: lootid 301105 (rev_loot_gnomeregan.sql and
  source/items/gnomeregan_loot.py). The S0 rev spawns him (guid 3011050).
- 301106 Dupe Bug: a copy of the stock 7732 (whose only user is the outside Techbot) at level 28, faction 63 (never
  494: it is hostile to Techbot's own faction, FACTS-STOCK flag 20), mechanical, not stun immune (a stun stops a
  Duplication: the reward), health 300 (HealthModifier 0.35169 on 853), melee about 3% of the tank row a swing
  (DamageModifier 1.7), the stock crawl (walk 0.4, run 0.286). No loot and no XP (an endless heroic supply). Its heroic
  template (4,000 health, H's override) is `difficulty_entry_1` = _common.heroic_entry (the lock's line, else H's
  predicted 310576).
- 301107 After-Image: the lagging player's ghost (aura 247 cast by the player: their look and gear) where they stood
  (TB1) or at the save point (TB6): a helper nobody targets (the invisible stalker skin under the clone). No heroic
  template.

Spells (214300-214339). Registry damage is a percent of the reference row through resolve copies (the combat log
names the mechanic; IGNORE_CASTER_MODIFIERS, NO_REDIRECTION, NO_REFLECTION). Tooltips are number-free.

  214300  Lag Spike           TB1 normal: resolve copy (Fire), 40%, Weakened (the 5 yd circle on the after-image)
  214301  Lag                 TB1 the lagging player's look for the 2 s warning (SV 68), a DUMMY aura
  214302  Duplication         TB3 normal: the bug's 3 s bar (Nature, kickable); it leaves a 1 s aura of itself (done)
  214303  Duplication         TB3 heroic: the 2 s bar
  214304  Patch: Backup Restore  TB4 normal: his 8 s download (Arcane, kickable)
  214305  Patch: Backup Restore  TB4 heroic: the 6 s download
  214306  Safe Mode           TB5 +25% damage taken while the bar runs (SV 37 lasting)
  214307  Safe Mode           TB5 look once at the bar's start (SV 2956)
  214308  Patch Complete      TB4 look as the patch lands (SV 2074)
  214309  Version             TB4 heroic: +5% damage done a stack, no end, no cap (the amount is the script's)
  214310  Rubber Band         TB6 heroic: the carrier's mark until the snap (SV 68)
  214311  Save Point          TB6 look: the light pillar on the after-image at the save point (SV 2046)
  214312  Rubber Band         TB6 look on the carrier at the snap back (SV 263)
  214313  Lag Spike           TB6 the chained spikes: resolve copy (Arcane), 60%, Weakened
  214314  Save Point          TB6 the burst on everyone but its owner: resolve copy (Arcane), 60%
  214315  Bug Echo            TB7 heroic: resolve copy (Fire), 40%, Weakened
  214316  Battle Net          TB8 heroic: resolve copy (Nature), 20%, Weakened
  214317  Battle Net          TB8 the rider: a 4 s root (Magic: bots dispel it)
  214318  Battle Net          TB8 look: the net thrown from him to the player (SV 683)
  214319  Dupe Bug            TB2 / TB3 look as a bug rises (SV 2073)
  214320  Shutdown            TB9 the powered-down sparks on the body, 30 s, persisting through death (SV 7867)
  214321  After-Image         TB1 / TB6 aura 247 (clone caster) cast by the player on the after-image, the ghost SV 886
  214322  Lag Spike           TB1 look where a spike lands, on the after-image (SV 2917)
  214323-214339 spare

Kept as cast (stock): none (the stock Battle Net 10852, Lag 10855, Summon Dupe Bug 10858 and Patch 10860 stay with
the outside Techbot's SmartAI). Weakened is BM's 205000 (the registry's).
"""

import math

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, Mechanic, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    FACTION_GNOMEREGAN_MECHANICAL,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TYPE_MECHANICAL,
    boss_columns,
    heroic_entry,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_DUPE_BUG,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_TECHBOT,
    TB_AFTERIMAGE_GHOST,
    TB_LAG,
    TB_LAG_SPIKE,
    TB_NET,
    TB_PATCH,
    TB_SAFE_MODE_STATE,
    TB_SHUTDOWN,
    TB_SAFE_START,
    TB_SAVE_SET,
    TB_SNAP,
    TB_SPAWN,
)

_TB = 'Gnomeregan build WP-D1 (Techbot)'

TECHBOT = 301105
DUPE_BUG = 301106
AFTER_IMAGE = 301107

# TechbotLogic.h Tune (the DT test pins each against the header).
_LAG_WARN_MS = 2000                 # kLagWarnMs
_DUP_CAST_MS = (3000, 2000)         # kDupCastMs
_PATCH_CAST_MS = (8000, 6000)       # kPatchCastMs
_SAFE_MODE_PCT = 25                 # kSafeModeTakenPct
_VERSION_STACKS = 255               # kVersionShownCap
_BAND_MARK_MS = 5500                # kBandSnapAtMs + 200: the mark outlives the snap
_NET_ROOT_MS = 4000                 # kNetRootMs
_SHUTDOWN_MS = 30000                # kShutdownSparksMs
_DONE_MARK_MS = 1000                # the Duplication bar's own aura, read by the machine at the bar's end

_SCHOOL_MASK_ALL = 127
_AURA_CLONE_CASTER = 247            # SPELL_AURA_CLONE_CASTER (the mechanism of Clone Me! 45204)
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000      # a finished cast keeps the swing timer (LESSONS L3)
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000           # the shutdown's sparks stay on the body
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000             # the aura never leaves the instance on the character
_INTERRUPT_KICKABLE = 0x0F                          # movement, pushback, interrupt, auto-attack (stock casters)
_PREVENTION_SILENCE = 1
_DISPEL_MAGIC = 1

# Stock icons (Spell.dbc).
_ICON_LAG = 656                     # Lag 10855
_ICON_DUPE = 91                     # Summon Dupe Bug 10858
_ICON_PATCH = 140                   # Patch 10860
_ICON_NET = 69                      # Battle Net 10852

# The level 28 warrior row (creature_classlevelstats, SELECT 2026-11-26): health 853.
_BASE_HP_28 = 853
_BUG_HEALTH = 300                   # GnomereganRework.h Health::kDupeBug normal
_BUG_HEALTH_MODIFIER = 0.35169      # ceil(299.99) = 300 on 853 (CreatureBaseStats rounds up)
_BUG_DAMAGE_MODIFIER = 1.7          # about 3% of the tank row a swing (TechbotLogic.h kBugMeleeTankPct)

_FLAGS_EXTRA_NO_XP = 0x40


def _look(spell_id: int, name: str, visual: int, icon: int, notes: str, *, school: School = School.NORMAL):
    """A look cast triggered on its target: an instant DUMMY, no handler, hidden from the log."""
    return spell(
        id=spell_id, name=name, school=school, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _mark(spell_id: int, name: str, duration_ms: int, visual: int, icon: int, desc: str, aura_desc: str, notes: str):
    """A DUMMY debuff the script puts on a player for its look and the bots' read: not dispellable, NO_IMMUNITIES (a
    bubble keeps it), CHANGE_MAP."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1, SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


# --- 301105 Techbot (S0's skeleton row, D1's from now on) ----------------------------------------------------------

boss_301105 = creature_template(
    TECHBOT, 'Techbot',
    minlevel=28, maxlevel=28, exp=0, faction=FACTION_GNOMEREGAN_MECHANICAL, npcflag=0,
    speed_walk=1.0, speed_run=1.14286, rank=1, dmgschool=0, BaseAttackTime=2000,
    RangeAttackTime=2000, BaseVariance=1, RangeVariance=1, unit_class=1, unit_flags=0, unit_flags2=2048,
    type=TYPE_MECHANICAL, type_flags=0, lootid=TECHBOT, mingold=0, maxgold=0, MovementType=0, HoverHeight=1,
    ManaModifier=1, ArmorModifier=1, ExperienceModifier=1, RegenHealth=1, movementId=0,
    **boss_columns('boss_techbot_rework', 70.34, damage_modifier=1.7, difficulty_entry_1=heroic_entry(TECHBOT)),
)
creature_model(TECHBOT, display_id=DISPLAY_TECHBOT, scale=1.0, idx=0)

# --- 301106 Dupe Bug, 301107 After-Image ---------------------------------------------------------------------------

_bug_columns = {
    **KIT_CREATURE, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1, 'unit_flags': 0,
    'type': TYPE_MECHANICAL, 'HealthModifier': _BUG_HEALTH_MODIFIER, 'DamageModifier': _BUG_DAMAGE_MODIFIER,
    'speed_walk': 0.4, 'speed_run': 0.285714, 'detection_range': 18.0, 'lootid': 0, 'pickpocketloot': 0,
    'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_gnomer_dupe_bug',
    'difficulty_entry_1': heroic_entry(DUPE_BUG),
}
dupe_bug_301106 = creature_template(DUPE_BUG, 'Dupe Bug', **_bug_columns)
creature_model(DUPE_BUG, display_id=DISPLAY_DUPE_BUG, scale=1.0, idx=0)

after_image_301107 = creature_template(
    AFTER_IMAGE, 'After-Image', **{**KIT_HELPER, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1,
                                   'ScriptName': 'npc_gnomer_lag_echo'},
)
creature_model(AFTER_IMAGE, display_id=DISPLAY_INVISIBLE_STALKER)

# --- TB1 Lag Spike -------------------------------------------------------------------------------------------------

lag_spike_214300 = resolve_copy(
    214300, 'Lag Spike', School.FIRE, 'The hit lands where you were.',
    f'{_TB}, TB1 (normal): every 15 s from 8 s (guess), a random player on the dish (tank included, s7 #36 A) lags: '
    'their after-image (301107) stays where they stood inside a 5 yd circle for 2 s, then 40% of the reference row '
    '(the tank row on the tank) and Weakened on everyone inside. Runs through Patch. Copy of the resolve spell 205003 '
    '(Fire). The landing look is 214322 on the after-image; this one plays on the players hit (SV 2917).',
    icon=_ICON_LAG, visual=TB_LAG_SPIKE,
)

lag_214301 = _mark(
    214301, 'Lag', _LAG_WARN_MS, TB_LAG, _ICON_LAG, 'Your connection is unstable.', 'Lagging.',
    f'{_TB}, TB1: the lagging player\'s look for the 2 s warning, cast by the player on themself (triggered) with '
    'emote line 1. Lag 10855\'s SV 68 (the gray slowdown puff). No slow, no stun (SP: the stock Link Dead goes): look '
    'only.')

# --- TB3 Duplication ------------------------------------------------------------------------------------------------


def _duplication(spell_id: int, cast_ms: int, which: str):
    return spell(
        id=spell_id, name='Duplication', school=School.NATURE, cast_time_ms=cast_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_DONE_MARK_MS,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_DUPE,
        notes=f'{_TB}, TB3 ({which}): the Dupe Bug\'s {cast_ms // 1000} s bar (the Duplicator machine casts it through '
              'the bug at its due time of life, with the bug\'s emote line 0). Nature school, kickable (InterruptFlags '
              '15, PreventionType silence): the bug\'s only cast, so a kick locks nothing else; a stun stops it too '
              '(the reward, the kick table). Completed, it leaves a 1 s DUMMY aura of itself on the bug, which the '
              'machine reads as "done" (the copy rises at the source\'s health, ruling 51). Summon Dupe Bug 10858\'s '
              'SV 2073. Keeps the swing timer.',
        raw_overrides=kit_raw('Duplicates itself.', 'Duplicated.', InterruptFlags=_INTERRUPT_KICKABLE,
                              PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=TB_SPAWN,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
    )


duplication_214302 = _duplication(214302, _DUP_CAST_MS[0], 'normal: once at 9 s of life')
duplication_h_214303 = _duplication(214303, _DUP_CAST_MS[1], 'heroic: every 7 s of life')

# --- TB4 Patch, TB5 Safe Mode, Version ------------------------------------------------------------------------------


def _patch(spell_id: int, cast_ms: int, which: str):
    return spell(
        id=spell_id, name='Patch: Backup Restore', school=School.ARCANE, cast_time_ms=cast_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_PATCH,
        notes=f'{_TB}, TB4 ({which}): Techbot\'s {cast_ms // 1000} s download, every 45 s (heroic 35 s), with yell '
              'line 2 and Safe Mode (214306). No effect: when it ends (OnSpellCast) the script deletes every living '
              'Dupe Bug, heals him 3% (heroic 4%) of his health per bug and (heroic) adds a Version stack per bug '
              '(214309). Arcane school, kickable (InterruptFlags 15, PreventionType silence): his only Arcane cast '
              '(the kick table, s7 #9 A): a kick ends it with no heal and the bugs stay. Bots kick it only while a bug '
              'lives (a priority 0 never-kick entry otherwise). Keeps his swing timer.',
        raw_overrides=kit_raw('Downloads a patch: deletes every bug and restores from backup.',
                              InterruptFlags=_INTERRUPT_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
    )


patch_214304 = _patch(214304, _PATCH_CAST_MS[0], 'normal')
patch_h_214305 = _patch(214305, _PATCH_CAST_MS[1], 'heroic')

safe_mode_214306 = spell(
    id=214306, name='Safe Mode', school=School.ARCANE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=_SAFE_MODE_PCT, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Safe Mode: a flat percent of damage taken, not a damage value')],
    spell_icon_id=_ICON_PATCH,
    notes=f'{_TB}, TB5: +25% damage taken (all schools) while the Patch bar runs (both difficulties), put on by the '
          'script at the bar\'s start and removed at its end however it ends (landed, kicked, lost). A damage-taken '
          'aura with mechanic none (rule 8: immunity 1972 never refuses it). Not dispellable or purgeable. V\'s '
          'TB_SAFE_MODE_STATE (SV 37, the lightning orbs, lasting with the aura).',
    raw_overrides=kit_raw('In safe mode: damage taken increased.', 'Safe Mode: damage taken increased.',
                          instant=True, SpellVisualID_1=TB_SAFE_MODE_STATE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

safe_mode_start_214307 = self_visual(
    214307, 'Safe Mode', TB_SAFE_START,
    f'{_TB}, TB5: the look once as the Patch bar starts, cast by Techbot on himself (triggered). V\'s TB_SAFE_START '
    '(SV 2956, one-shot; the lasting twin is 214306\'s TB_SAFE_MODE_STATE).',
    icon=_ICON_PATCH, school=School.ARCANE,
)

patch_done_214308 = self_visual(
    214308, 'Patch Complete', TB_PATCH,
    f'{_TB}, TB4: the look as a Patch lands (bugs deleted or not), cast by Techbot on himself (triggered). V\'s '
    'TB_PATCH (SV 2074, one-shot; the bar is the tell).',
    icon=_ICON_PATCH, school=School.ARCANE,
)

version_214309 = spell(
    id=214309, name='Version', school=School.ARCANE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=0,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Version: a flat percent of damage done, not a damage value')],
    spell_icon_id=_ICON_PATCH,
    notes=f'{_TB}, TB4 (heroic): one stack per bug a completed Patch deleted, for the rest of the fight, no cap '
          '(ruling 12): +5% damage done a stack. The base point is 0 and the script sets the amount to 5 x stacks '
          'with AuraEffect::ChangeAmount, reasserted every second (rule 25); CumulativeAura 255 shows the stacks. His '
          'registry hits ignore caster modifiers, so the script scales their percent by the same 5% a stack; the '
          'aura raises his melee. Not dispellable or purgeable.',
    raw_overrides=kit_raw('A newer version: more damage.', 'Damage done increased.', instant=True,
                          CumulativeAura=_VERSION_STACKS, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- TB6 Rubber Band, TB7 bug echoes (heroic) -----------------------------------------------------------------------

rubber_band_214310 = _mark(
    214310, 'Rubber Band', _BAND_MARK_MS, TB_LAG, _ICON_LAG, 'You are rubber-banding.',
    'Rubber-banding: you will snap back to your save point.',
    f'{_TB}, TB6 (heroic): the mark of each of the two carriers from the band\'s start (emote line 6) until the snap '
    'back at 5 s (removed by the script then). Look only: the RunOut, the save point, the spikes and the snap are the '
    'script\'s. Lag 10855\'s SV 68.')

save_point_214311 = self_visual(
    214311, 'Save Point', TB_SAVE_SET,
    f'{_TB}, TB6: the save point is set: the after-image at it casts this on itself (triggered). V\'s TB_SAVE_SET (SV '
    '2046, the blue light pillar, 1.5 s). The 6 yd circle is the registry\'s marker.',
    icon=_ICON_LAG, school=School.ARCANE,
)

snap_back_214312 = _look(
    214312, 'Rubber Band', TB_SNAP, _ICON_LAG,
    f'{_TB}, TB6: the carrier snaps back to the save point at 5 s (just after the second spike resolved): Techbot '
    'casts it on them (triggered) after the teleport. V\'s TB_SNAP (SV 263, blink_impact_chest).',
    school=School.ARCANE)

rubber_spike_214313 = resolve_copy(
    214313, 'Lag Spike', School.ARCANE, 'The hit lands where you were.',
    f'{_TB}, TB6 (heroic): the chained spikes under each carrier, at 2 s and 3.5 s of the band, 1.5 s each: 60% of the '
    'reference row (the tank row on the tank) and Weakened on everyone inside (5 yd), scaled by his Version stacks. '
    'Copy of the resolve spell 205007 (Arcane: the drill\'s school).',
    icon=_ICON_LAG, visual=TB_LAG_SPIKE,
)

save_point_burst_214314 = resolve_copy(
    214314, 'Save Point', School.ARCANE, 'A save point bursts as its owner snaps back to it.',
    f'{_TB}, TB6 (heroic): the save point\'s 6 yd circle, set at 2 s and bursting at the snap: 60% of the reference '
    'row (the tank row on the tank) on everyone inside but its owner (the registry\'s eligibility), no Weakened (SP: '
    'the penalty is on the spikes), scaled by his Version stacks. Copy of the resolve spell 205007 (Arcane).',
    icon=_ICON_LAG, visual=TB_LAG_SPIKE,
)

bug_echo_214315 = resolve_copy(
    214315, 'Bug Echo', School.FIRE, 'A bug repeats the lag at its own feet.',
    f'{_TB}, TB7 (heroic): on each spike wave of a Rubber Band every living Dupe Bug on the dish repeats it at its '
    'feet: a 4 yd circle, 2 s warning, 40% (guess) of the reference row (the tank row on the tank) and Weakened; '
    'overlapping circles stack. Scaled by his Version stacks. Copy of the resolve spell 205003 (Fire).',
    icon=_ICON_DUPE, visual=TB_LAG_SPIKE,
)

# --- TB8 Battle Net (heroic) ----------------------------------------------------------------------------------------

battle_net_214316 = resolve_copy(
    214316, 'Battle Net', School.NATURE, 'A net thrown at the target\'s feet.',
    f'{_TB}, TB8 (heroic): every 25 s from 20 s (guess), a net thrown at a random player on the dish (tank included): '
    'an 8 yd circle at their feet with a 1.5 s warning, then 20% of the reference row (the tank row on the tank), '
    'Weakened and the root (214317) on everyone inside. Scaled by his Version stacks. Copy of the resolve spell 205004 '
    '(Nature).',
    icon=_ICON_NET,
)

battle_net_root_214317 = spell(
    id=214317, name='Battle Net', school=School.NATURE, dispel=_DISPEL_MAGIC, mechanic=Mechanic.ROOT,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_NET_ROOT_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, base_points=0, mechanic=Mechanic.ROOT,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_NET,
    notes=f'{_TB}, TB8 (heroic): the 4 s root the net leaves on everyone in its circle: the registry\'s rider, cast by '
          'Techbot. Magic: the expected dispel (the kick and dispel table; bots dispel it, priority 2). Mechanic Root '
          'and not NO_IMMUNITIES, so a root immunity is a reward. V\'s TB_NET (SV 683, the net). AuraInterruptFlags '
          'CHANGE_MAP.',
    raw_overrides=kit_raw('Caught in a net.', 'Rooted.', CastingTimeIndex=1, SpellVisualID_1=TB_NET,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

battle_net_throw_214318 = _look(
    214318, 'Battle Net', TB_NET, _ICON_NET,
    f'{_TB}, TB8: the net thrown from Techbot to the picked player as the circle is drawn (triggered). V\'s TB_NET (SV '
    '683, the boomerang net). Look only.',
    school=School.NATURE)

# --- TB2 / TB3 the bug's rise, TB9 the shutdown, the after-image ---------------------------------------------------

bug_spawn_214319 = self_visual(
    214319, 'Dupe Bug', TB_SPAWN,
    f'{_TB}, TB2 / TB3: the look as a Dupe Bug rises at Techbot or a copy rises beside its source, cast by the bug on '
    'itself (triggered). V\'s TB_SPAWN (SV 2073; TB_SPAWN_ALT 263 if the playtest finds the purple ring wrong).',
    icon=_ICON_DUPE,
)

shutdown_214320 = spell(
    id=214320, name='Shutdown', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_SHUTDOWN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_PATCH,
    notes=f'{_TB}, TB9 (s7 #13 A: he dies, dressed as a shutdown): the sparks on the powered-down body, cast by '
          'Techbot on himself (triggered) at the killing blow while he still lives, with yell line 5 at the death. '
          'ALLOW_AURA_WHILE_DEAD keeps it on the corpse for 30 s. V\'s TB_SHUTDOWN (SV 7867, the arcane '
          'arcs; a lasting STATE). Look only.',
    raw_overrides=kit_raw('Shutting down.', 'Powered down.', instant=True, SpellVisualID_1=TB_SHUTDOWN,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=_ATTR3_ALLOW_AURA_WHILE_DEAD,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

after_image_214321 = spell(
    id=214321, name='After-Image', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_CLONE_CASTER, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LAG,
    notes=f'{_TB}, TB1 / TB6: the lagging player casts it on their after-image (301107) as it appears (triggered): '
          'aura 247 (clone caster, the Zul\'Farrak Empty Vessel 213922 precedent) gives it their display and the '
          'mirror-image flag, so the client draws their look and gear; V\'s TB_AFTERIMAGE_GHOST (SV 886, the pale '
          'ghost particles) plays on it. Gone with the after-image.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=TB_AFTERIMAGE_GHOST, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

lag_spike_landing_214322 = self_visual(
    214322, 'Lag Spike', TB_LAG_SPIKE,
    f'{_TB}, TB1: the spike landing where the player stood, cast by the after-image on itself (triggered) just before '
    'the circle resolves, whoever stands in it. V\'s TB_LAG_SPIKE (SV 2917, one-shot; the marker carries the radius).',
    icon=_ICON_LAG, school=School.FIRE,
)

# The level 28 warrior row the bug's modifier is sized on (the DT test re-derives it).
assert math.ceil(_BASE_HP_28 * _BUG_HEALTH_MODIFIER) == _BUG_HEALTH
