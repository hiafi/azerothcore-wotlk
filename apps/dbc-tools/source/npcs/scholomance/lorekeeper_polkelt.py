"""
Scholomance build WP-S7: Lorekeeper Polkelt (10901), "Chain Reaction"
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.4 rows PK, s3.5 row S7, s3.6; build spec
docs/dungeons/scholomance-rework.md SC 1979-2036). WP-S7 owns this file (its spells: kSpellsPolkelt 206250-206269 in
modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; PolkeltLogic.h names the same ids).

- 10901 Lorekeeper Polkelt: boss_lorekeeper_polkelt_rework (SmartAI off; WP-S7's SQL rev drops the four stock rows:
  Volatile Infection 18149 moves into the C++, Corrosive Acid 8245 and Noxious Catalyst 18151 leave his kit), normal
  HealthModifier 57.339 (175k on the level 60 warrior base 3,052), stun immune (1972), INSTANCE_BIND. DamageModifier
  3.5: the stock value (base SQL), now his own; WP-T tunes it. Heroic health 360k and the tier's melee are WP-H's
  heroic template 310100 (source/world/dungeons/scholomance.py).
- 300540 Unstable Specimen (PK1, a walker) and 300541 Rooted Specimen (PK1, rooted where it rises; heroic: Hardened):
  boss-kit combat adds, the stock Unstable Corpse 10480's models (10978, 10972) and run speed (0.571429), level 60
  elite warriors, 6,000 health (HealthModifier 1.9659 on 3,052: ceil = 6,000); heroic 9,000 is WP-H's
  `_KIT_ADD_HEROIC` (applied because this file declares them). No loot, no XP (flags_extra 0x40). Melee
  DamageModifier 3.5 (the stock corpse's; WP-T tunes it). Both run npc_sc_polkelt_specimen: a lethal hit never kills
  one, it drops it at 1 health into its fuse (the boss script owns the rest). Each row names its heroic entry
  (difficulty_entry_1, heroic_ids.lock; STAGE-H report s4 predicted 310116 / 310117).

Spells. The rings and the pools deal their damage through dungeon copies of the mod-boss-mechanics resolve spell (the
registry's percent of the reference row; the combat log names the mechanic). The rest are script spells whose numbers
the script sets, auras, cast bars and looks:

  206250  Specimen Burst      PK2 a kill or chained ring's hit (6 yd): resolve copy, Nature, 30% / 40% + 1 Weakened;
                              detention lesson 15% / 25% + 1 Weakened
  206251  Ripe Burst          PK4 a ripe ring's hit (12 yd): resolve copy, Nature, 40% / 55%, no Weakened
  206252  Acid Pool           PK5 a pool's 1 s tick (6 yd, 60 s): resolve copy, Nature, 8% / 12%, the kit's slow
  206253  Acid Pool           PK5 the pool on the floor (PERSISTENT_AREA_AURA at a point, 60 s, 6 yd; look only)
  206254  Raise Specimen      PK1 a specimen rises (look)
  206255  Fuse                PK2 the kill fuse: the specimen's 2 s swelling cast (look; the registry ring owns the hit)
  206256  Chained Fuse        PK2 the chained fuse: 1 s (ruling 18)
  206257  Ripe                PK4 the ripe fuse: 3 s
  206258  Specimen Burst      PK2 / PK4 the burst itself, on the specimen (look)
  206259  Catalyst Reaction   PK3 the hit on him: 1.5% of his health (base point 0 from the script)
  206260  Corroded            PK3 his own acid: +5% damage taken per stack, 20 s, refreshes, 10 stacks
  206261  Rooted              a rooted specimen: rooted, roots at its feet
  206262  Hardened            PK6 heroic rooted specimens: 90% less damage taken, bark
  206263  Noxious Catalyst    PK7 heroic: the soft enrage, a stacking Nature dot (spell_sc_polkelt_noxious_catalyst)
  206264  Ripening            PK4 the 30 s clock on a specimen (the bots read it: about to ripen)
  206265-206269 spare

Visual ids are WP-V's (._visuals) except Corrosive Acid 8245's SV 856 (Corroded) and Noxious Catalyst 18151's SV 800,
wired here by hand (stock; every look is unconfirmed until seen in game).
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
    self_visual,
    timer_aura,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_B,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    PK_ACID_POOL,
    PK_BURST,
    PK_FUSE_SWELL,
    PK_HARDENED,
    PK_RAISE,
    PK_ROOTED,
)

_PK = 'Scholomance build WP-S7 (Lorekeeper Polkelt)'

# Heroic templates of the two adds (source/world/heroic_ids.lock, minted by the wave B scoped write run in entry order
# after the Graduate's 310113; STAGE-H report s4). `generate.py --check` names the expected id if this drifts.
_HEROIC_UNSTABLE = 310116
_HEROIC_ROOTED = 310117

_DISPLAYS_UNSTABLE_CORPSE = (10978, 10972)     # creature_template_model 10480 (read-only SELECT 2026-11-08)
_SPEED_RUN_UNSTABLE_CORPSE = 0.571429          # creature_template 10480 speed_run
_SPECIMEN_HEALTH_MODIFIER = 1.9659             # ceil(3,052 x 1.9659) = 6,000 (level 60 warrior base)
_FLAGS_EXTRA_NO_XP = 0x40

_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_FLAG_DEST_LOCATION = 0x40
_SCHOOL_MASK_ALL = 127
_DEFENSE_MAGIC = 1

_ICON_DISEASE_BURST = 263   # Disease Burst 17689
_ICON_EXPLODE = 3012        # Explode 47496
_ICON_RAISE = 1             # Raise Dead 51516 (generic)
_ICON_CORROSIVE_ACID = 636  # Corrosive Acid 8245
_ICON_ROOTS = 20            # Entangling Roots 339
_ICON_HARDENED_BARK = 689   # Hardened Bark 62663
_ICON_NOXIOUS = 203         # Noxious Catalyst 18151, Volatile Infection 18149
_SV_CORROSIVE_ACID = 856    # Corrosive Acid 8245 (Spell.dbc 3.3.5): Corroded is his own acid
_SV_NOXIOUS_CATALYST = 800  # Noxious Catalyst 18151 (Spell.dbc 3.3.5): the stock name's own look

_SCRIPT_DAMAGE = 'Scholomance: a percent of reference health, set by the script (DungeonKit::RefFlat)'
_SCRIPT_HIT = 'Scholomance: 1.5% of his own health, base point 0 set by boss_lorekeeper_polkelt_rework'


def _specimen_columns(heroic_entry: int) -> dict:
    return {
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'type': 6, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': _SPECIMEN_HEALTH_MODIFIER, 'DamageModifier': 3.5, 'BaseAttackTime': 2000,
        'speed_run': _SPEED_RUN_UNSTABLE_CORPSE, 'ExperienceModifier': 1.0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
        'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'ScriptName': 'npc_sc_polkelt_specimen', 'difficulty_entry_1': heroic_entry,
    }


def _fuse(spell_id: int, name: str, cast_ms: int, notes: str, desc: str):
    return cast_bar(spell_id, name, cast_ms, desc, notes, icon=_ICON_EXPLODE, visual=PK_FUSE_SWELL,
                    school=School.NATURE)


def _declare():
    creature_template_columns(10901, **boss_columns('boss_lorekeeper_polkelt_rework', 57.339, DamageModifier=3.5))

    # --- Boss-kit creatures -----------------------------------------------------------------------------------------
    # Literal creature_template(<entry>, ...) calls: source/world/dungeons/scholomance.py finds the declared kit adds
    # by that text and gives them their heroic health (9k).
    creature_template(300540, 'Unstable Specimen', **_specimen_columns(_HEROIC_UNSTABLE))       # PK1 a walker
    creature_template(300541, 'Rooted Specimen', **_specimen_columns(_HEROIC_ROOTED))           # PK1 rooted
    for entry in (300540, 300541):
        for idx, display in enumerate(_DISPLAYS_UNSTABLE_CORPSE):
            creature_model(entry, display_id=display, idx=idx)

    # --- PK2 Fuse and burst ---------------------------------------------------------------------------------------
    resolve_copy(
        206250, 'Specimen Burst', School.NATURE, 'A specimen bursts, splashing everything around it with plague.',
        f'{_PK} PK2: a kill or chained ring\'s hit, 6 yd around the specimen: 30% (heroic 40%) of the non-tank row + 1 '
        'Weakened (ruling 21), through the registry; every ring a player stands in hits them (overlaps stack). The '
        'detention lesson uses it at 15% / 25% + Weakened (SoloLesson.h). Resolve copy (Nature). '
        "Disease Burst 17689's SpellVisual 749 (the stock room's own) on every unit hit: the visible impact.",
        icon=_ICON_DISEASE_BURST, visual=PK_BURST,
    )
    _fuse(206255, 'Fuse', 2000,
          f'{_PK} PK2: the kill fuse. A lethal hit drops a specimen at 1 health (npc_sc_polkelt_specimen) and it '
          'swells for 2 s: this cast, by the specimen on itself, not triggered, so the swell shows (Explode '
          '47496\'s SV 11259, the ghoul\'s swelling cast). Not interruptible (the kit cast bar; the specimen cannot '
          'be targeted while it burns). The registry ring (206250) owns the hit.',
          'Swells, about to burst.')
    _fuse(206256, 'Chained Fuse', 1000,
          f'{_PK} PK2: the chained fuse, 1 s (ruling 18): a specimen inside another burst\'s ring lights at once, even '
          'at full health. Same look as 206255.',
          'Lit by a burst; about to burst.')
    self_visual(
        206258, 'Specimen Burst', PK_BURST,
        f'{_PK} PK2 / PK4: the burst itself, cast by the specimen on itself (triggered) as its ring resolves, just '
        "before it despawns. Disease Burst 17689's SpellVisual 749. Look only.",
        icon=_ICON_DISEASE_BURST, school=School.NATURE,
    )
    self_visual(
        206254, 'Raise Specimen', PK_RAISE,
        f'{_PK} PK1: a specimen rises (cast by the specimen on itself, triggered, as it spawns). Raise Dead 51516\'s '
        'SpellVisual 11305. Look only.',
        icon=_ICON_RAISE, school=School.SHADOW,
    )

    # --- PK3 Catalyst Reaction ------------------------------------------------------------------------------------
    spell(
        id=206259, name='Catalyst Reaction', school=School.NATURE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=_SCRIPT_HIT)],
        spell_icon_id=_ICON_CORROSIVE_ACID,
        notes=f'{_PK} PK3: a kill or chained burst whose ring holds him reacts on its maker. He casts this on himself '
              '(triggered) with base point 0 = 1.5% of his maximum health (2,625 normal, 5,400 heroic; the script '
              'divides it by his Corroded so the hit lands at 1.5%), then gains a Corroded stack (206260). A ripe '
              'burst never reacts. Ignores caster modifiers, cannot crit, always hits, no threat. No look of its own '
              '(the burst and Corroded carry it).',
        raw_overrides=kit_raw('The catalyst reacts on its maker.', instant=True, InterruptFlags=0, PreventionType=0,
                              DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    spell(
        id=206260, name='Corroded', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=20000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=4,
                        misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded='Corroded: a flat +5% damage taken per stack, not a damage or heal value')],
        spell_icon_id=_ICON_CORROSIVE_ACID,
        notes=f'{_PK} PK3: his own Corrosive Acid (8245 leaves his kit and becomes this): +5% damage taken from every '
              'school per stack (BasePoints 4 + DieSides 1), 20 s, refreshed by each reaction, up to 10 (+50%; the '
              'heroic health of 360k assumes it is kept up). Added by the script (DungeonKit::AddStacks). Dispel none. '
              "Corrosive Acid 8245's SpellVisual 856 and icon 636.",
        raw_overrides=kit_raw('Damage taken increased by $s1%.', 'Damage taken increased by $s1%.', instant=True,
                              CumulativeAura=10, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              SpellVisualID_1=_SV_CORROSIVE_ACID),
    )

    # --- PK4 Ripe, PK5 Acid Pool ----------------------------------------------------------------------------------
    resolve_copy(
        206251, 'Ripe Burst', School.NATURE, 'A ripe specimen bursts across the hall.',
        f'{_PK} PK4: a ripe ring\'s hit, 12 yd around a specimen 30 s after it rose (3 s warning): 40% (heroic 55%) of '
        'the non-tank row, no Weakened (ruling 21: 55% heroic), through the registry. It lights every specimen in its '
        'ring and leaves an acid pool; it never reacts with him. Resolve copy (Nature). SV 749 on '
        'every unit hit.',
        icon=_ICON_DISEASE_BURST, visual=PK_BURST,
    )
    _fuse(206257, 'Ripe', 3000,
          f'{_PK} PK4: the ripe fuse, 3 s, after the specimen swelled to 150% size over its 30 s (the script\'s '
          'scale). Same look as 206255. The registry ring (206251) owns the hit.',
          'Ripe; about to burst across the hall.')
    timer_aura(
        206264, 'Ripening', 30000, 'Ripens in $d.', 'Ripens when this ends.',
        f'{_PK} PK4: the 30 s clock on every specimen of the boss fight (Unit::AddAura as it rises): players see when '
        'it ripens, and the bots\' conditional kill target reads its time left (under 3 s: kill it now). The detention '
        'lesson\'s specimens never ripen and never carry it.',
        icon=_ICON_EXPLODE, school=School.NATURE,
    )
    resolve_copy(
        206252, 'Acid Pool', School.NATURE, 'Acid eats at your feet.',
        f'{_PK} PK5: a pool\'s tick, 6 yd where a ripe specimen burst, every 1 s for 60 s: 8% (heroic 12%) of the '
        'non-tank row with the kit\'s Standing in It slow (DungeonKit::Linger); a lingering zone, so no Weakened. At '
        'most 6 / 8 pools (the user\'s ruling): the oldest dries up. Resolve copy (Nature). No '
        'impact look (a tick every second; the pool is the look).',
        icon=_ICON_CORROSIVE_ACID,
    )
    spell(
        id=206253, name='Acid Pool', school=School.NATURE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=60000,
        effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=6.0)],
        spell_icon_id=_ICON_CORROSIVE_ACID,
        notes=f'{_PK} PK5: the pool on the floor, visual only. He casts it (triggered) at the point where a ripe '
              'specimen burst (CastSpell(x, y, z)): a dynamic object of 6 yd for 60 s with the Deadmines green puddle '
              "(PersistentAreaKit 90342, goo_flow_state; WP-V's SV_ACID_POOL). Its DUMMY aura reaches nobody. The "
              'registry linger (206252) owns the ticks. boss_lorekeeper_polkelt_rework removes the oldest when the cap '
              'dries it up, and all of them when the encounter ends.',
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=PK_ACID_POOL, Targets=_TARGET_FLAG_DEST_LOCATION,
                              InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    # --- Rooted, PK6 Hardened ---------------------------------------------------------------------------------------
    spell(
        id=206261, name='Rooted', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_ROOTS,
        notes=f'{_PK} PK1: a rooted specimen (300541) is rooted where it rises (Unit::AddAura as it spawns): the roots '
              "at its feet are Entangling Roots 339's SpellVisual 38 (EntanglingRoots_State, gap 18). Mechanic none, "
              'dispel none (a purge never frees it). Until it bursts.',
        raw_overrides=kit_raw('Rooted to the floor.', 'Rooted to the floor.', instant=True,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=PK_ROOTED),
    )
    spell(
        id=206262, name='Hardened', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-91,
                        misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded='Hardened: a flat -90% damage taken, not a damage or heal value')],
        spell_icon_id=_ICON_HARDENED_BARK,
        notes=f'{_PK} PK6 heroic: a rooted specimen takes 90% less damage from every school (BasePoints -91 + DieSides '
              '1): DPS cannot kill it, only a burst lights it (the lighting ignores damage). On the bots\' ignore '
              "list. Hardened Bark 62663's SpellVisual 6662 (barkskin_state_base, gap 18). Dispel none.",
        raw_overrides=kit_raw('Damage taken reduced by 90%. Only a burst can set it off.',
                              'Damage taken reduced by 90%.', instant=True, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=PK_HARDENED),
    )

    # --- PK7 Noxious Catalyst (heroic) ----------------------------------------------------------------------------
    noxious = spell(
        id=206263, name='Noxious Catalyst', school=School.NATURE, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=30000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=0, die_sides=0,
                        amplitude=1000, implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_DAMAGE)],
        spell_icon_id=_ICON_NOXIOUS,
        notes=f'{_PK} PK7 heroic: the soft enrage (SD5), a new spell under the stock name (18151 stays out of his '
              'kit). Every 10 s from the pull every player in the fight is set to one more stack (pull time / 10 s, '
              'so a player who died and came back has the same count); each stack ticks 0.3% of the reference row per '
              'second (spell_sc_polkelt_noxious_catalyst sets the per-stack amount, the aura multiplies by the '
              'stacks): 9 stacks at the 95 s target (2.7% per second), 13 at 130 s. Uncapped (CumulativeAura 255, the '
              'aura counter\'s limit). Undispellable (dispel none), lands through immunities (NO_IMMUNITIES), ignores '
              'caster modifiers, never reflected. 30 s, refreshed with each stack, removed when the fight ends. '
              "Noxious Catalyst 18151's SpellVisual 800 and icon 203.",
        raw_overrides=kit_raw('Inflicts Nature damage every second, more with each application.',
                              'Taking Nature damage every second.', instant=True, CumulativeAura=255,
                              DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=_SV_NOXIOUS_CATALYST),
    )
    scripted_by(noxious, 'spell_sc_polkelt_noxious_catalyst')


# Held back until wave B binds this boss (_common.py BIND_WAVE_B; R-A S-11): stock until then.
if BIND_WAVE_B:
    _declare()
