"""
Scarlet Monastery build WP-D8H: Arcanist Doan's hard mode, the Kel'Thuzad Heresy (heroic only;
.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.7, s3.5 row D8H, s7 #27 A; build spec
docs/dungeons/scarlet-monastery-2-library.md "Hard mode: The Kel'Thuzad Heresy", HM1-HM5 and the Build spec rows).
WP-D8H owns this file; WP-S0 wrote the stub. The engine side is modules/mod-dungeon-bosses
src/ScarletMonastery/doan_hard_mode.cpp (on D8's DoanFight.h hooks), the pure rules DoanHardModeLogic.h. Doan's lines
2-3, the four evidence pages (gameobjects 301320-301323, their page_text and heroic spawns) are
data/sql/updates/pending_db_world/rev_doan_hard_mode_scarlet_monastery.sql.

- 300920 Phylactery Shard (HM3): one more anchor of every hard mode bubble, on the next free anchor spot; warded
  (immune) while another anchor stands, then a kill target. Level 60, 15.6k (the script sets 2.5 x a hard mode
  anchor: 15,625 on D8's 5k heroic anchor, HANDOFF s10 option D; the spec's 25k on the old 8k), no melee, never moves
  (npc_sm_phylactery_shard: passive, no combat movement, its beam into the bubble), immunity 1972 like the anchors, no
  loot or XP, display 24889 (Thel'zan's Phylactery 27868's Lichcontainer01, V's DISPLAY_PHYLACTERY_SHARD). Heroic
  entry 310474 once H's mint order settles (H's table: 15,625).
- 300921 Risen Purged (HM5): six rise along the chamber's south wall after his second bubble and walk to him (about
  10 s); each that reaches him is one more anchor next bubble. Level 60, 6k, undead, Scarlet Crusade (they serve
  him), passive walkers (npc_sm_risen_purged: they never stop to fight), no immunity set (a slow, a root or a stun holds
  them back), no loot or XP. Display 23887 / 23888 (the Scourged Scarlet Footman, male and female; V). Heroic entry
  310475 once H's mint order settles (6k).

Both exist only on heroic (the hard mode is heroic only): their normal rows carry the hard mode's level and health too.

Spells (kSpellsHeresy 212710-212749; DoanHardModeLogic.h names the same ids; looks from ._visuals, V's HM_* picks,
every look unconfirmed until seen in game):

  212710  Icy Death              HM1 the Curse every damaging ability of his applies (Arcane Explosion, the Mark's
                                 burst and own share, the pools, a landed Flamestrike, Shadow Fissure): 8 s, refreshed
                                 by the next hit, 60% slower, 3% of the reference row as Frost a second (the kit's
                                 spell_dungeon_refflat_periodic); a reward to remove (the bots' dispel list)
  212711  The Kel'Thuzad Heresy  the hard mode's red aura on Doan from the fourth page: holds a wipe
  212712  Phylactery Ward        HM3 the shard's immunity while another anchor of the bubble stands
  212713  Shadow Fissure         HM4 the hit: resolve copy, Shadow, 60%
  212714  Shadow Fissure         HM4 the 3 s fissure's look, an aura on a stalker (the exact 6 yd shadow pool)
  212715  Raise the Purged       HM5 a Risen Purged rising (Raise Dead's look)
  212716-212749 spare.

Tooltips are number-free where the number is a reference percent.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    MECHANIC_SNARE,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_SCARLET_CRUSADE,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_PHYLACTERY_SHARD,
    DISPLAY_RISEN_PURGED,
    DISPLAY_RISEN_PURGED_ALT,
    DN_BUBBLE,
    HM_FISSURE_ALT,
    HM_ICY_DEATH,
    HM_RAISE,
    HM_RED_AURA,
)

_D8H = 'Scarlet Monastery build WP-D8H (Doan\'s hard mode, the Kel\'Thuzad Heresy)'

# --- the creatures ---------------------------------------------------------------------------------------------------

# Their heroic entries (difficulty_entry_1 = the id in source/world/heroic_ids.lock; H's table names 310474 and 310475
# once every lower-numbered wave 1 kit unit is declared). None until then, as D8's ARCANE_ANCHOR_HEROIC: a value set
# early is a wrong interim number (lib/test_scarlet_monastery_heroic.py test_it_is_clean); generate.py --check prints
# the number the row must carry. Shared-file request in the WP-D8H report: paste 310474 / 310475 here at that point.
PHYLACTERY_SHARD_HEROIC = 310474
RISEN_PURGED_HEROIC = 310475

PHYLACTERY_SHARD = 300920
RISEN_PURGED = 300921

_CLASS_WARRIOR = 1
_CREATURE_TYPE_UNDEAD = 6
_CREATURE_TYPE_NOT_SPECIFIED = 10
_FLAGS_EXTRA_NO_XP = 0x40
_LEVEL = 60

# The hard mode's health at level 60 (the warrior base 3,052, creature_classlevelstats basehp0, live 2026-11-20):
# shard 15,625 = 5.1196 x 3,052 (2.5 x 1.25 x D8's 5k heroic anchor, HANDOFF s10 option D; revert: 25000 with D8's
# 8k), Risen Purged 6k = 1.9659 x 3,052. The script sets the shard's own number at the raise.
SHARD_HEALTH = 15625
RISEN_HEALTH = 6000
_BASE_HP_60_WARRIOR = 3052
SHARD_HEALTH_MODIFIER = round(SHARD_HEALTH / _BASE_HP_60_WARRIOR, 4)
RISEN_HEALTH_MODIFIER = round(RISEN_HEALTH / _BASE_HP_60_WARRIOR, 4)



def _heroic_entry(columns: dict, heroic_entry) -> dict:
    """`columns` with difficulty_entry_1 when the heroic entry is known (a declared full row must carry it)."""
    if heroic_entry:
        return {**columns, 'difficulty_entry_1': heroic_entry}
    return columns


_NO_LOOT = {'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'ExperienceModifier': 0.0,
            'flags_extra': _FLAGS_EXTRA_NO_XP, 'AIName': ''}

phylactery_shard_300920 = creature_template(300920, 'Phylactery Shard', **_heroic_entry({
    **KIT_CREATURE, **_NO_LOOT, 'faction': FACTION_SCARLET_CRUSADE, 'type': _CREATURE_TYPE_NOT_SPECIFIED,
    'minlevel': _LEVEL, 'maxlevel': _LEVEL, 'rank': 0, 'unit_class': _CLASS_WARRIOR, 'unit_flags': 0,
    'HealthModifier': SHARD_HEALTH_MODIFIER, 'DamageModifier': 0.0, 'BaseAttackTime': 2000,
    'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'ScriptName': 'npc_sm_phylactery_shard',
}, PHYLACTERY_SHARD_HEROIC))
creature_model(300920, display_id=DISPLAY_PHYLACTERY_SHARD)

risen_purged_300921 = creature_template(300921, 'Risen Purged', **_heroic_entry({
    **KIT_CREATURE, **_NO_LOOT, 'faction': FACTION_SCARLET_CRUSADE, 'type': _CREATURE_TYPE_UNDEAD,
    'minlevel': _LEVEL, 'maxlevel': _LEVEL, 'rank': 0, 'unit_class': _CLASS_WARRIOR, 'unit_flags': 0,
    'HealthModifier': RISEN_HEALTH_MODIFIER, 'DamageModifier': 1.0, 'BaseAttackTime': 2000,
    'CreatureImmunitiesId': 0, 'ScriptName': 'npc_sm_risen_purged',
}, RISEN_PURGED_HEROIC))
creature_model(300921, display_id=DISPLAY_RISEN_PURGED, idx=0, probability=1.0)
creature_model(300921, display_id=DISPLAY_RISEN_PURGED_ALT, idx=1, probability=1.0)

# --- constants (DoanHardModeLogic.h; lib/test_scarlet_monastery_doan_hard_mode.py pins each against the header) ------

ICY_DEATH_MS = 8000                 # kIcyDeathMs
ICY_DEATH_SLOW_PCT = 60             # kIcyDeathSlowPct
ICY_DEATH_TICK_MS = 1000            # kIcyDeathTickMs
ICY_DEATH_HUNDREDTHS = 300          # kIcyDeathHundredths: 3% a tick (heroic only: the same in both slots)

_DISPEL_CURSE = 2
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127
_AURA_SCHOOL_IMMUNITY = 39          # SPELL_AURA_SCHOOL_IMMUNITY (not in lib.dsl's AuraType)
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_ATTR1_AURA_STAYS_AFTER_COMBAT = 0x02000000  # Unit::RemoveEvadeAuras keeps it: the red aura holds a wipe

_REFFLAT_PERIODIC = 'spell_dungeon_refflat_periodic'
_SCRIPT_REFFLAT = ('Scarlet Monastery D8H: a percent of reference health in hundredths per tick, set by the kit\'s '
                   'spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn: the tank row on the tank)')

# Stock icons (Spell.dbc SpellIconID of the named spell, read 2026-11-20)
_ICON_FROSTBITE = 119               # Frostbite 12494
_ICON_CHAINS_OF_KELTHUZAD = 1540    # Chains of Kel'Thuzad 28408
_ICON_DIVINE_SHIELD = 81            # Divine Shield 642 (and Arcane Bubble 9438)
_ICON_SHADOW_FISSURE = 1468         # Shadow Fissure 27810
_ICON_RAISE_DEAD = 61               # Raise Dead 17473


def _self_aura(spell_id: int, name: str, school: School, visual: int, icon: int, desc: str, aura_desc: str, notes: str,
               *, attributes_ex: int = ATTR1_NO_THREAT):
    """A look-only DUMMY aura a unit casts on itself (triggered), no duration (removed with its caster or by script)."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1, SpellVisualID_1=visual,
                              AttributesEx=attributes_ex, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- HM1 Icy Death ---------------------------------------------------------------------------------------------------

icy_death_212710 = spell(
    id=212710, name='Icy Death', school=School.FROST, dispel=_DISPEL_CURSE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=ICY_DEATH_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED,
               base_points=-(ICY_DEATH_SLOW_PCT + 1), die_sides=1, mechanic=MECHANIC_SNARE,
               implicit_target_a=TARGET_UNIT_TARGET_ANY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
               base_points=ICY_DEATH_HUNDREDTHS - 1, die_sides=1, amplitude=ICY_DEATH_TICK_MS,
               implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT),
    ],
    spell_icon_id=_ICON_FROSTBITE,
    notes=f'{_D8H}, HM1 Icy Death (designer 2026-11-18): Doan casts it (triggered, the registry\'s rider or D8\'s '
          'Flamestrike landing) on every player hit by Arcane Explosion, a Mark\'s burst or its own share, a '
          'Righteous Fire pool tick, a landed Righteous Flamestrike or Shadow Fissure; never by Scorched or '
          'Detonation. 8 s, refreshed by the next hit (one stack). 60% slower movement (a snare on the effect, so '
          'snare immunity answers it too) and every second 3% of the reference row as Frost (300 hundredths, heroic '
          'the same in MiscValueB; spell_dungeon_refflat_periodic, the tank row on the tank; the spec\'s starting '
          'guess). A Curse (Dispel 2): removing it is a reward (shared doc section 6); on the bots\' dispel list '
          '(priority 1). Ignores his modifiers. Frostbite 12494\'s lasting frost state SV 2837 (V; the doc\'s SV 13 is '
          'a missile). Dropped on a map change; D8H clears it from every player when the pull ends.',
    raw_overrides=kit_raw('A curse of the grave: movement slowed and Frost damage over time.',
                          'Movement slowed by $s1%. Frost damage every $t2 sec.', CastingTimeIndex=1,
                          DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_2=ICY_DEATH_HUNDREDTHS,
                          SpellVisualID_1=HM_ICY_DEATH, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(icy_death_212710, _REFFLAT_PERIODIC)

# --- the trigger: the hard mode's aura on Doan -----------------------------------------------------------------------

heresy_aura_212711 = _self_aura(
    212711, 'The Kel\'Thuzad Heresy', School.SHADOW, HM_RED_AURA, _ICON_CHAINS_OF_KELTHUZAD,
    'His heresy is exposed.', 'The Kel\'Thuzad Heresy: exposed, and no longer pretending.',
    f'{_D8H}: the hard mode\'s aura on Doan, cast on himself (triggered) when the fourth evidence page is read '
    '(go_sm_evidence_page), and again at every hard mode pull. A DUMMY with no effect: the read is the hard mode red '
    'aura SV 90554 (V\'s HM_RED_AURA, the stock deathknight_plaguestrikestatered at its own scale). '
    'AURA_STAYS_AFTER_COMBAT: an evade keeps it (the flag holds through wipes); his death or a respawn clears it. '
    'After a cold load or a respawn D8\'s out-of-combat idle hook (DoanFight.h RegisterDoanIdleHook) puts it back.',
    attributes_ex=ATTR1_NO_THREAT | _ATTR1_AURA_STAYS_AFTER_COMBAT,
)

# --- HM3 the Phylactery Shard ----------------------------------------------------------------------------------------

shard_ward_212712 = spell(
    id=212712, name='Phylactery Ward', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_SCHOOL_IMMUNITY, base_points=0,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DIVINE_SHIELD,
    notes=f'{_D8H}, HM3 (evidence 2): the Phylactery Shard casts it on itself (triggered) as it rises with every hard '
          'mode bubble; the script removes it once no other anchor of the bubble stands ("it can only be damaged once '
          'the other anchors are broken"). SPELL_AURA_SCHOOL_IMMUNITY to every school (the Arcane Bubble shape). '
          'Not dispellable, no mechanic. The bots ignore the shard while it has it (the descriptor). Arcane Bubble '
          '9438\'s SpellVisual 968 (V\'s DN_BUBBLE: the same bubble the anchors feed, no new look).',
    raw_overrides=kit_raw('Warded while another anchor stands.', 'Immune while another arcane anchor stands.',
                          CastingTimeIndex=1, SpellVisualID_1=DN_BUBBLE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- HM4 Shadow Fissure ----------------------------------------------------------------------------------------------

shadow_fissure_212713 = resolve_copy(
    212713, 'Shadow Fissure', School.SHADOW, 'The floor splits and shadow erupts.',
    f'{_D8H}, HM4 Shadow Fissure (evidence 3 and 4): from the end of his first bubble, every 10 s (held while he is '
    'Overloaded), a 6 yd circle under each of 2 random players (the tank can be one) with a 3 s marker, then 60% of '
    'the reference row, the tank row on the tank (registry tag 4, a Zone circle), and Icy Death. No Weakened (own '
    'penalty: none). Copy of the mod-boss-mechanics resolve spell (Shadow).',
    icon=_ICON_SHADOW_FISSURE,
)

shadow_fissure_look_212714 = _self_aura(
    212714, 'Shadow Fissure', School.SHADOW, HM_FISSURE_ALT, _ICON_SHADOW_FISSURE, 'A fissure of shadow.',
    'A fissure of shadow.',
    f'{_D8H}, HM4: the fissure\'s look for its 3 s marker, a DUMMY aura the generic stalker (300922) at the spot casts '
    'on itself (triggered); the stalker lives 3.5 s. The shipped 6 yd shadow pool SV 90605 (V\'s HM_FISSURE_ALT, the '
    'exact size; the doc\'s Shadow Fissure SV 12678 draws about 18 yd). No effect.',
)

# --- HM5 the Risen Purged --------------------------------------------------------------------------------------------

raise_purged_212715 = self_visual(
    212715, 'Raise the Purged', HM_RAISE,
    f'{_D8H}, HM5: a Risen Purged rising on the south wall, cast on itself (triggered) the moment it is summoned, '
    'before it walks to Doan: Raise Dead 17473\'s SpellVisual 4582 (V\'s HM_RAISE). Look only.',
    icon=_ICON_RAISE_DEAD, school=School.SHADOW,
)
