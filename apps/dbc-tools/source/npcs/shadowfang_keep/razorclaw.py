"""
Shadowfang Keep build WP-S2: Razorclaw the Butcher (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows RC1-RC4, s3.6 row S2; build spec docs/dungeons/shadowfang-keep-rework.md SK 444-479 (build spec), SK 357-443
(design)). WP-S2 owns this file (its spells: kSpellsRazorclaw 205930-205944 in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; RazorclawLogic.h names the same ids).

- 3886 Razorclaw the Butcher: boss_razorclaw_rework (SmartAI off; WP-S2's SQL rev drops stock row 3886 Butcher Drain),
  normal HealthModifier 33 (15,972 at level 20, warrior), DamageModifier 2.0 (was 2.5; SK "Tuning": slow big hits
  kept, the 3.2 s swing stays), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Heroic health 350,980 is WP-H's override
  in source/world/dungeons/shadowfang_keep.py. No kit adds.

Spells. Meat Hook's line, Butcher's Cut's non-tank cone and the Offal Slick ticks deal their damage through dungeon
copies of the mod-boss-mechanics resolve spell (the registry's percent of the reference row; the combat log names the
mechanic). The rest are script spells whose numbers the script sets at cast (DungeonKit::RefFlat as base point 0) or
weapon damage, plus cast bars and a look:

  205930  Meat Hook          RC1 cast bar, 2 s, on the caster (the registry line owns the hit)
  205931  Meat Hook          RC1 the line's hit: resolve copy, Physical, + spell_sfk_meat_hook_once (a player standing
                             in both heroic Twin Hooks lines is hit once; Greenskin's lane-hit precedent)
  205932  Meat Hook          RC1 the chain look, cast (triggered) by the thrower on every hooked unit as it is dragged:
                             Scourge Hook 50335's SpellVisual 11055 (iron chain, throw, BloodyExplosion on the target:
                             the visible impact of the hit). Also Razorclaw's ArenaGuard grip look.
  205933  Hung to Bleed      RC1 heroic: the hooked player's bleed, 20% of the non-tank row over 8 s (4 ticks of 5%)
  205934  Tenderized         RC2: +10% melee damage taken per stack, 3 stacks, on the tank
  205935  Butcher's Cut      RC3 cast bar, 2 s, on the caster
  205936  Butcher's Cut      RC3 the cone's non-tank hit: resolve copy, Physical, Rend Flesh's SpellVisual 110
  205937  Butcher's Cut      RC3 the tank's hit: 250% weapon damage (2.5 x a swing), Rend Flesh's SpellVisual 110
  205938  Offal Slick        RC4 heroic: the slick's 1 s tick (5%), resolve copy, Physical; rider the kit's 205201 slow
  205939-205944 spare

Silverlaine's Echo of Razorclaw (WP-S3, BS4) throws the same hook: it reuses 205930-205932 by id (MeatHook.h).
"""

from lib.dsl import Effect, EffectType, School
from lib.dsl.registry import creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)

creature_template_columns(3886, **boss_columns('boss_razorclaw_rework', 33, DamageModifier=2.0))

_TARGET_UNIT_TARGET_ENEMY = 6

_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000

_AURA_PERIODIC_DAMAGE = 3
_AURA_MOD_MELEE_DAMAGE_TAKEN_PCT = 126       # SpellAuraDefines.h SPELL_AURA_MOD_MELEE_DAMAGE_TAKEN_PCT
_MECHANIC_BLEED = 15
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2

_ICON_SCOURGE_HOOK = 218        # Scourge Hook 50335
_ICON_REND_FLESH = 108          # Rend Flesh 3147
_ICON_REND = 245                # Rend 772
_ICON_MORTAL_WOUND = 138        # Mortal Wound 25646 (a stacking wound debuff)
_VISUAL_SCOURGE_HOOK = 11055    # Scourge Hook 50335 / Abomination Hook 59395 (VISUALS-REPORT s8)
_VISUAL_REND_FLESH = 110        # Rend Flesh 3147: SwipeCaster + BloodyExplosion (VISUALS-REPORT s8)
_VISUAL_REND = 372              # Rend 772

_SCRIPT_DAMAGE = 'boss spell: the script sets the damage at cast (DungeonKit::RefFlat, a percent of reference health)'

# --- RC1 Meat Hook (+ heroic Twin Hooks and Hung to Bleed) ----------------------------------------------------------
meat_hook_cast_205930 = cast_bar(
    205930, 'Meat Hook', 2000, 'Hurls a meat hook along a line. Anyone in it is dragged back and chopped.',
    'Shadowfang Keep WP-S2 (Razorclaw) RC1 Meat Hook: the 2 s cast bar while the registry line (3 yd wide, 5 yd past '
    'a non-tank at least 8 yd away, the first 4 yd excluded) warns; heroic Twin Hooks throw two lines under the same '
    'bar. No visual on the bar itself (a self-cast SV 11055 would burst blood on the caster); the chain shows on each '
    'hooked unit through 205932. Also cast by the Echo of Razorclaw (WP-S3, BS4).',
    icon=_ICON_SCOURGE_HOOK,
)

meat_hook_hit_205931 = resolve_copy(
    205931, 'Meat Hook', School.NORMAL, 'Hooked and chopped.',
    "Shadowfang Keep WP-S2 (Razorclaw) RC1 Meat Hook: the line's hit, 35% of the non-tank row (455 normal, 1,442 "
    'heroic) + 1 Weakened, through the registry. Copy of the resolve spell 205001 (Physical) plus '
    "spell_sfk_meat_hook_once: a unit an earlier line of the same throw already hit is dropped from this line's "
    'targets (SK RC1 heroic: "a player standing in both lines is hit once"). No visual (205932 is the look).',
    icon=_ICON_SCOURGE_HOOK, scripts=('spell_sfk_meat_hook_once',),
)

meat_hook_chain_205932 = spell(
    id=205932, name='Meat Hook', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SCOURGE_HOOK,
    notes='Shadowfang Keep WP-S2 (Razorclaw) RC1 Meat Hook: the look of the drag. The thrower casts it (triggered) on '
          'every unit the line hits, just before the jump to its front (DungeonKit::JumpTo lookSpell): Scourge Hook '
          "50335's SpellVisual 11055 (the throw animation, the iron chain 502 and BloodyExplosion on the target, the "
          'visible impact of the hit; on an instant the chain only flashes, VISUALS-REPORT correction 8). Also the '
          "look of Razorclaw's ArenaGuard grip. DUMMY on the target, no damage, no threat; ignores LoS, always hits, "
          'suppresses procs.',
    raw_overrides=kit_raw('Hooks an enemy and drags it to the caster.', instant=True, InterruptFlags=0,
                          PreventionType=0, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=_VISUAL_SCOURGE_HOOK),
)

hung_to_bleed_205933 = spell(
    id=205933, name='Hung to Bleed', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_BLEED,
    attributes=ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_PERIODIC_DAMAGE, base_points=65, die_sides=0,
                    amplitude=2000, mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_DAMAGE)],
    spell_icon_id=_ICON_REND,
    notes='Shadowfang Keep WP-S2 (Razorclaw) RC1 heroic Hung to Bleed: a hooked player also bleeds for 20% of the '
          'non-tank row over 8 s (4 ticks every 2 s, each 5%: 206 heroic). Cast triggered by the thrower on the '
          'hooked unit with base point 0 = DungeonKit::RefFlat(5%) per tick. Damage over time applies no Weakened '
          '(ruling 17). Bleed mechanic (armor does not apply), not dispellable (Dispel none). No active defense, '
          "no redirection or reflection, ignores LoS, cannot crit, always hits, ignores caster modifiers (R1 S-1). "
          "Rend 772's SpellVisual 372 and icon 245. Base points 65 is the tooltip's normal tick only.",
    raw_overrides=kit_raw('Bleeds for $s1 Physical damage every 2 sec.', 'Bleeding.', instant=True,
                          DefenseType=_DEFENSE_MAGIC, InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=_VISUAL_REND),
)

# --- RC2 Tenderize / RC3 Butcher's Cut -------------------------------------------------------------------------------
tenderized_205934 = spell(
    id=205934, name='Tenderized', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=20000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_MELEE_DAMAGE_TAKEN_PCT, base_points=10,
                    die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_MORTAL_WOUND,
    notes='Shadowfang Keep WP-S2 (Razorclaw) RC2 Tenderize: each of his melee hits on the tank adds a stack '
          '(DungeonKit::AddStacks from boss_razorclaw_rework::DamageDealt), +10% melee damage taken per stack '
          '(SPELL_AURA_MOD_MELEE_DAMAGE_TAKEN_PCT 126, amount x stacks), so the combat log shows the real number. At 3 '
          "stacks he casts Butcher's Cut, which clears them. 20 s, refreshed by every stack. The aura counts any "
          'melee, but in his kitchen only his own reaches the tank. Not dispellable. Mortal Wound 25646\'s icon 138.',
    raw_overrides=kit_raw('Increases melee damage taken by $s1% per application.',
                          'Melee damage taken increased by $s1%.', instant=True, CumulativeAura=3,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

butchers_cut_cast_205935 = cast_bar(
    205935, "Butcher's Cut", 2000, 'Raises his cleaver over everyone in front of him.',
    "Shadowfang Keep WP-S2 (Razorclaw) RC3 Butcher's Cut: the 2 s cast bar at 3 Tenderized stacks (the registry "
    "Frontal, 90 degrees, 10 yd, tank exempt, owns the hit). No visual on the bar (Rend Flesh's impact would burst "
    'blood on the caster); 205936 and 205937 carry the swing.',
    icon=_ICON_REND_FLESH,
)

butchers_cut_hit_205936 = resolve_copy(
    205936, "Butcher's Cut", School.NORMAL, 'Cleaved.',
    "Shadowfang Keep WP-S2 (Razorclaw) RC3 Butcher's Cut: the cone's hit on non-tanks, 40% of the non-tank row (520 "
    'normal, 1,648 heroic) + 1 Weakened, through the registry. Copy of the resolve spell 205001 (Physical). Rend '
    "Flesh 3147's SpellVisual 110 (the SwipeCaster arc at the cone's marker, BloodyExplosion on every unit hit).",
    icon=_ICON_REND_FLESH, visual=_VISUAL_REND_FLESH,
)

butchers_cut_tank_205937 = spell(
    id=205937, name="Butcher's Cut", school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=250,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_REND_FLESH,
    notes="Shadowfang Keep WP-S2 (Razorclaw) RC3 Butcher's Cut: the tank's heavy hit, 2.5 x a normal swing (SK, "
          'approved). The registry cone is tank exempt (bots read it as a Frontal; the tank gets no Weakened); when it '
          'resolves the script clears Tenderized and then casts this (triggered) on his victim if it stands in the '
          "cone (Razorclaw::InCutCone), as Mr. Smite's 205303. Weapon damage: DamageModifier 2.0 on normal and the "
          "heroic template's own weapon, so it follows WP-T's melee tuning. No active defense (the healer can plan "
          'the spike; a defensive is the reward), cannot crit, ignores LoS, always hits; Physical, so armor applies. '
          "Rend Flesh 3147's SpellVisual 110 (the claw arc, blood on the tank).",
    raw_overrides=kit_raw('Inflicts $s1% weapon damage.', instant=True, DefenseType=_DEFENSE_MELEE,
                          InterruptFlags=0, PreventionType=0, Attributes=_ATTR0_NO_ACTIVE_DEFENSE,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=_VISUAL_REND_FLESH),
)

# --- RC4 heroic Offal Slick -------------------------------------------------------------------------------------------
offal_slick_205938 = resolve_copy(
    205938, 'Offal Slick', School.NORMAL, 'Standing in it hurts.',
    "Shadowfang Keep WP-S2 (Razorclaw) RC4 heroic Offal Slick: each Butcher's Cut leaves its cone on the floor for "
    '30 s (DungeonKit::Linger, a fixed-point cone), ticking every 1 s for 5% of the non-tank row (206 heroic) and the '
    "kit's 205201 \"Standing in It\" slow; no Weakened (lingering damage never applies it, ruling 17). Copy of the "
    'resolve spell 205001 (Physical). No visual (a tick every second); the marker cone and the blood pools (GO '
    "301103, WP-S2's SQL rev) dress it.",
    icon=_ICON_REND_FLESH,
)
