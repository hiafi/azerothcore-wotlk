"""
The shared dungeon kit's declaration helpers (WP-K0, .agents/plans/shadowfang-keep-build/
shadowfang-keep-build.HANDOFF.md s3.2): the constants and builders every reworked dungeon's `source/npcs/<dungeon>/`
package uses, generalized from the Deadmines Pilot's `source/npcs/deadmines/_common.py` and `shared.py` (which now
import them from here, with identical output). Import it from a declaration file like any lib module:

    from lib.dsl.dungeon_kit import IMMUNITY_BOSS_STUN, cast_bar, kit_creature, kit_helper, kit_raw, resolve_copy

A dungeon's own `_common.py` keeps what is its own (faction, creature type, a special immunity set) and builds its
creature defaults with `kit_creature(faction=..., type=...)` / `kit_helper(...)`.

Builders (each registers the spell, so call them from a declaration file while generate.py loads it):

  cast_bar(id, name, cast_ms, desc, notes, ...)     a named no-effect cast bar (DUMMY on the caster), not interruptible:
                                                    the bar players read while a registry mechanic owns the hit
  resolve_copy(id, name, school, desc, notes, ...)  a dungeon copy of the mod-boss-mechanics resolve spell
                                                    (205001-205007) with its exact attribute set, bound to
                                                    spell_boss_mechanics_resolve, so the combat log names the
                                                    mechanic
  self_visual(id, name, visual, notes, ...)         an instant no-effect spell the caster casts on itself for its look
  standing_in_it(id, notes, ...)                    the lingering zones' -30% slow rider (the kit-wide 205201's shape)
  timer_aura(id, name, duration_ms, ...)            a DUMMY debuff that shows a clock (a hard mode timer)

The two kit-wide spells (205200 "Preparing", 205201 "Standing in It") are declared once, in
source/npcs/deadmines/shared.py (their ids sit in the Deadmines block, which minted them); another dungeon uses them by
id (mod-dungeon-bosses DungeonKitIds.h) and never declares a copy.
"""

from __future__ import annotations

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import scripted_by, spell

# creature_immunities: the positive set "-229 + STUN" (mask 0x244B3E53 in the table's comment notation, MechanicsMask
# 1217821862), inserted by the Deadmines Pilot's core pending SQL. Every reworked boss uses it unless its dungeon
# rules otherwise (Rhahk'Zor kept -159).
IMMUNITY_BOSS_STUN = 1972

# Text masks every dungeon spell declaration shares (enUS + the other locales' "use enUS" mask).
TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}

# Attribute bits (SharedDefines.h names).
ATTR0_IS_ABILITY = 0x00000010
ATTR0_DO_NOT_DISPLAY = 0x00000080
ATTR0_DO_NOT_LOG = 0x00000100
ATTR0_DO_NOT_SHEATH = 0x00040000
ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
ATTR0_AURA_IS_DEBUFF = 0x04000000
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR1_NO_REDIRECTION = 0x00000008
ATTR1_NO_REFLECTION = 0x00000080
ATTR1_NO_THREAT = 0x00000400
ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
ATTR2_CANT_CRIT = 0x20000000
ATTR3_NOT_A_PROC = 0x00000200
ATTR3_ALWAYS_HIT = 0x00040000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR4_NO_CAST_LOG = 0x00000001

# Implicit targets.
TARGET_UNIT_CASTER = 1
TARGET_UNIT_TARGET_ENEMY = 6
TARGET_UNIT_SRC_AREA_ENEMY = 15
TARGET_SRC_CASTER = 22
TARGET_UNIT_TARGET_ANY = 25

MECHANIC_SNARE = 11
ICON_GENERIC = 1
ICON_SLOW = 27              # stock Slow 246

# The mod-boss-mechanics resolve spell's attribute set (source/npcs/boss_mechanics.py, 205001-205007), so a copy deals
# exactly the registry's number: no active defense, no redirection or reflection, no threat, ignores LoS, cannot crit,
# not a proc, always hits, ignores caster modifiers (the Pilot's lesson R1 S-1), DmgClass magic, instant.
RESOLVE_RAW = {
    'Attributes': ATTR0_NO_ACTIVE_DEFENSE,
    'AttributesEx': ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
    'AttributesEx2': ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
    'AttributesEx3': ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
    'AttributesEx4': ATTR4_NO_CAST_LOG,
    'CastingTimeIndex': 1,
    'DefenseType': 1,
}
RESOLVE_EXCLUDED = ('mod-boss-mechanics resolve copy: the damage is set per target by spell_boss_mechanics_resolve '
                    'from the reference-health provider')
RESOLVE_SCRIPT = 'spell_boss_mechanics_resolve'


def kit_raw(desc: str = '', aura_desc: str = '', *, instant: bool = False, **more) -> dict:
    """The raw_overrides every dungeon spell starts from: no class set, no item, level 0, the descriptions and the
    text masks; `instant` adds CastingTimeIndex 1 (stock non-ranged instants). `more` goes last (it wins)."""
    raw = {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0}
    if instant:
        raw['CastingTimeIndex'] = 1
    raw.update({'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more})
    return raw


def kit_creature(*, faction: int, type: int = 7, **more) -> dict:  # noqa: A002 - the creature_template column name
    """The creature_template columns a dungeon's new boss-kit creatures share (the Deadmines Pilot's KIT_CREATURE with
    the dungeon's faction and creature type): unit_flags2 2048, exp 0, standing still (MovementType 0: the scripts place
    and move them), no SmartAI. `more` overrides any column."""
    columns = dict(
        subname='', IconName='', exp=0, faction=faction, npcflag=0, speed_walk=1.0, speed_run=1.14286,
        speed_swim=1.0, speed_flight=1.0, detection_range=20.0, dmgschool=0, BaseAttackTime=2000,
        RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, unit_flags2=2048, dynamicflags=0, family=0,
        type=type, type_flags=0, PetSpellDataId=0, VehicleId=0, MovementType=0, HoverHeight=1.0, ManaModifier=1.0,
        ArmorModifier=1.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1,
        CreatureImmunitiesId=0, flags_extra=0, AIName='', VerifiedBuild=0,
    )
    columns.update(more)
    return columns


def kit_helper(creature: dict, **more) -> dict:
    """Summoned helpers the players never target (stalkers, markers, look-alikes): `creature`'s columns made not
    selectable and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 | UNIT_FLAG_NOT_SELECTABLE 0x02000000, the
    mod-boss-mechanics marker precedent), hostile faction 14, no loot, no XP (flags_extra 0x40), no melee. `more`
    overrides any column."""
    columns = dict(
        creature, faction=14, unit_flags=0x2 | 0x02000000, DamageModifier=0.0, HealthModifier=1.0, lootid=0,
        pickpocketloot=0, skinloot=0, mingold=0, maxgold=0, flags_extra=0x40, detection_range=0.0,
    )
    columns.update(more)
    return columns


def cast_bar(spell_id: int, name: str, cast_ms: int, desc: str, notes: str, *, icon: int = ICON_GENERIC,
             visual: int = 0, school: School = School.NORMAL):
    """A named no-effect cast (DUMMY on the caster, no handler): the bar players read while the registry mechanic
    registered beside it owns the hit. Not interruptible (InterruptFlags 0, PreventionType 0): a kick must not look as
    if it stopped a mechanic the registry still lands. `visual` (a SpellVisual id) is set only when non-zero."""
    raw = kit_raw(desc, InterruptFlags=0, PreventionType=0, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=school, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def resolve_copy(spell_id: int, name: str, school: School, desc: str, notes: str, *, icon: int = ICON_GENERIC,
                 visual: int = 0, scripts: tuple[str, ...] = (), excluded: str = RESOLVE_EXCLUDED):
    """A dungeon copy of the mod-boss-mechanics resolve spell (205001-205007): SCHOOL_DAMAGE from the caster's spot on
    every enemy in 100 yd, the resolve attribute set, bound to spell_boss_mechanics_resolve (plus `scripts`), which
    filters the targets to the shape and sets the damage per target. Pass it to the registry with `.Spell(id)` (C++
    ImpactSpec / LingerSpec / LineStrikeSpec `spellId`). `visual` (a SpellVisual id) is set only when non-zero, as for
    cast_bar."""
    raw = kit_raw(desc, **RESOLVE_RAW)
    if visual:
        raw['SpellVisualID_1'] = visual
    s = spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_SRC_CASTER,
                        implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                        potency_excluded=excluded)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=raw,
    )
    scripted_by(s, RESOLVE_SCRIPT, *scripts)
    return s


def self_visual(spell_id: int, name: str, visual: int, notes: str, *, icon: int = ICON_GENERIC,
                school: School = School.NORMAL):
    """Visual only: an instant DUMMY (no handler) the caster casts on itself, triggered; DO_NOT_DISPLAY | DO_NOT_LOG.
    Copies a stock visual, never the stock spell."""
    return spell(
        id=spell_id, name=name, school=school, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def standing_in_it(spell_id: int, notes: str, *, name: str = 'Standing in It', slow_pct: int = 30,
                   duration_ms: int = 2000, desc: str = 'Standing in it hurts. Lasts $d.',
                   aura_desc: str = 'Standing in it hurts.', icon: int = ICON_SLOW):
    """The lingering zones' slow rider: movement -slow_pct% (BasePoints -(slow_pct + 1) + DieSides 1) for
    `duration_ms`, re-applied by every tick that hits, so it ends shortly after the player steps out. AURA_IS_DEBUFF,
    snare mechanic, Dispel none; TARGET_UNIT_TARGET_ANY (the registry casts riders with the owner as original
    caster)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=MECHANIC_SNARE,
        attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED,
                        base_points=-(slow_pct + 1), mechanic=MECHANIC_SNARE,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1),
    )


def timer_aura(spell_id: int, name: str, duration_ms: int, desc: str, aura_desc: str, notes: str, *,
               icon: int = ICON_GENERIC, school: School = School.NORMAL):
    """A DUMMY debuff that shows a clock (a hard mode timer): AURA_IS_DEBUFF | NO_IMMUNITIES (it lands through Divine
    Shield), Dispel none, TARGET_UNIT_TARGET_ANY."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1),
    )
