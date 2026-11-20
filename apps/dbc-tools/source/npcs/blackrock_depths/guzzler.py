"""
Blackrock Depths build WP-D17: The Grim Guzzler room: patrons, Ribbly and Plugger (9543, 9499, 10043, 9545, 9547, 9554)
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D17 / s3.6; build spec
docs/dungeons/blackrock-depths-4-imperial-seat.md S4 66-216, 428-435, 635-641, rulings 61-69). WP-D17 owns this file;
its spells are kSpellsGuzzler 211410-211429 of modules/mod-dungeon-bosses src/BlackrockDepths/BlackrockDepthsRework.h
and GuzzlerLogic.h names the same ids. No C++ script: the room stays on SmartAI.

What the room is. Ribbly (a quest kill, ruling 61) and Plugger (the barkeep you robbed, ruling 68) are stock SmartAI
units with their credit rows dropped (WP-H), health scaled up and two stock changes each; the 68 patrons are the room's
crowd, tuned down on both difficulties (ruling 65). Every number is in GuzzlerLogic.h (`kGuzzler...`), tested in
tests/brd_guzzler_test.cpp, and lib/test_blackrock_depths_guzzler.py pins this file to it.

Creature templates (held back until wave 2 binds, `_common.py` BIND_WAVE_2: stock until then; every column is kept in
`GUZZLER_CREATURE_COLUMNS` so the test reads the declaration whatever the gate says):

  9543 Ribbly Screwspigot   40,000 (HealthModifier 16.307 on the level 53 warrior base 2,453), DamageModifier 3.5 (the
                            stock value), the stock immunity -251 (a non-boss: the spec's text; the heroic copy
                            states -251 too), no INSTANCE_BIND (credit 240 dropped; the stock flags_extra 0),
                            SmartAI kept. Heroic 60,000 is WP-H's override.
  10043 Ribbly's Crony (x3) 6,000 (HealthModifier 2.709 on the level 50 warrior base 2,215, the middle of the 48-52
                            range: 5,586 to 6,423 at the ends), DamageModifier 3.5, stock kit (Eviscerate 15692,
                            Sinister Strike 15581). Heroic 9,000 is WP-H's.
  9499 Plugger Spazzring    40,000 (HealthModifier 19.13 on the level 55 paladin base 2,091), DamageModifier 3.5, 1972
                            (stock -324 held every CC mechanic AND the interrupt: his Shadow Bolts and Immolates can
                            now be interrupted, a reward, and he is still stun immune), no INSTANCE_BIND (credit 241
                            dropped; the stock flags_extra 0), SmartAI kept.
                            Heroic 60,000 is WP-H's.
  9545 Grim Patron          HealthModifier 0.6 (about 1,300 at level 50), DamageModifier 3.5 -> 1.5
  9547 Guzzling Patron      HealthModifier 0.6 (about 930), DamageModifier 1.5
  9554 Hammered Patron      HealthModifier 1.5 (about 3,300), DamageModifier 1.5
                            The patrons run their normal rows on heroic too (STAGE-H designer question 2 default:
                            no heroic template, so DD never scales their spells).

Spells (the dungeon copies of two stock spells the spec changes; rule 15, never an edit of the stock row):

  211410  Gouge   Ribbly's stock Gouge 12540 with a 2 s incapacitate (stock 4 s): 20 Physical, a stun aura (mechanic
                  knockout), broken by any damage, the stock look. The SmartAI row 9543 id 4 casts it (the SQL rev).
  211411  Kick    the Grim Patron's stock Kick 15610 with a 3 s interrupt lockout (stock 6 s): Physical damage and the
                  interrupt. The SmartAI row 9545 id 0 casts it (the SQL rev).

The three timer changes of ruling 65 / 69 (Plugger's and the Guzzling Patron's Shadow Bolt repeat 3-4 s -> 8-10 s, the
Hammered Patron's Backhand repeat 5-8 s -> 10-12 s) are SmartAI event parameters: they stay the stock spells 12739,
20825 and 6253 (Plugger's Shadow Bolt takes the heroic version through DD's SpellDifficulty swap 12739 -> 15472, which
DD rescales; a copy would drop that), so the room declares no more spells. The SmartAI rewrites are
data/sql/updates/pending_db_world/rev_guzzler_blackrock_depths.sql. 211412-211429 are spare.
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import TARGET_UNIT_TARGET_ENEMY
from lib.dsl.registry import creature_template_columns, spell

from ._common import BIND_WAVE_2, IMMUNITY_BOSS_STUN, kit_raw

# --- creature templates (held back until wave 2) ---------------------------------------------------------------------

# GuzzlerLogic.h: kRibblyHealth / kRibblyCronyHealth / kPluggerHealth (normal 40k / 6k / 40k at 5 players), the
# patron modifiers kPatron*HealthModifier and kPatronDamageModifier. A column write: AIName stays SmartAI.
GUZZLER_CREATURE_COLUMNS = {
    9543: dict(HealthModifier=16.307, DamageModifier=3.5),
    10043: dict(HealthModifier=2.709, DamageModifier=3.5),
    9499: dict(HealthModifier=19.13, DamageModifier=3.5, CreatureImmunitiesId=IMMUNITY_BOSS_STUN),
    9545: dict(HealthModifier=0.6, DamageModifier=1.5),
    9547: dict(HealthModifier=0.6, DamageModifier=1.5),
    9554: dict(HealthModifier=1.5, DamageModifier=1.5),
}

# Held back until wave 2 binds the room (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    for _entry, _columns in GUZZLER_CREATURE_COLUMNS.items():
        creature_template_columns(_entry, **_columns)

# --- spells (211410-211429) ------------------------------------------------------------------------------------------

_SD = 'Blackrock Depths build WP-D17 (the Grim Guzzler room)'

# Stock Spell.dbc rows (the working copy, read 2026-11-17): Gouge 12540, Kick 15610.
_MECHANIC_KNOCKOUT = 14                     # Gouge's Mechanic
_MECHANIC_INTERRUPT = 26                    # Kick's interrupt effect
_ATTR_GOUGE = 0x00150010                    # IS_ABILITY | NOT_SHAPESHIFTED | DO_NOT_SHEATH | CANCELS_AUTO_ATTACK_COMBAT
_ATTR_KICK = 0x00050010                     # IS_ABILITY | NOT_SHAPESHIFTED | DO_NOT_SHEATH
_ATTR1_GOUGE = 0x00040000                   # AttributesEx of the stock Gouge
_AURA_INTERRUPT_DAMAGE = 0x2                # AuraInterruptFlags: any damage taken breaks it (stock Gouge)
_RANGE_COMBAT = 2                           # SpellRange 2 "Combat Range" (melee, 5 yd)
_DEFENSE_MELEE = 2
_PREVENTION_PACIFY = 2
_SV_GOUGE = 256                             # the stock look of Gouge 12540
_SV_KICK = 90                               # the stock look of Kick 15610
_ICON_GOUGE = 245
_ICON_KICK = 246
_GOUGE_LEVEL = 18                           # Gouge 12540's BaseLevel / SpellLevel (the damage is flat)
_KICK_LEVEL = 20                            # Kick 15610's BaseLevel / SpellLevel: the damage grows 1.5 a level above it

_GOUGE_INCAPACITATE_MS = 2000               # GuzzlerLogic.h kGougeIncapacitateMs (stock 4,000)
_KICK_LOCKOUT_MS = 3000                     # GuzzlerLogic.h kKickLockoutMs (stock 6,000)

_FLAT = ('Blackrock Depths: the stock creature spell\'s flat number, kept as it was (a creature copy, not a player '
         'spell on potency)')

gouge_211410 = spell(
    id=211410, name='Gouge', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_KNOCKOUT, attributes=_ATTR_GOUGE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=5.0,
    duration_ms=_GOUGE_INCAPACITATE_MS,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=19, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_FLAT),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_GOUGE,
    notes=f'{_SD}: Ribbly Screwspigot\'s Gouge 12540 as the dungeon\'s own copy (never an edit of the stock row, rule '
          '15), with the incapacitate cut from 4 s to 2 s (ruling 62: the 2 s rule; it lands on the tank every 10 s). '
          'Everything else is the stock row read from Spell.dbc: 20 Physical, a stun aura with the knockout mechanic, '
          'any damage taken breaks it, melee range, instant, the attribute that stops his auto attack, the stock look '
          '(SV 256, icon 245). Cast by Ribbly\'s SmartAI (9543 id 4, first at 3 s, repeat 10 s). Ribbly\'s Cronies and '
          'the heroic copy cast the same spell (a custom id, so DD leaves its flat 20 alone).',
    raw_overrides=kit_raw('Inflicts $s1 damage to an enemy and incapacitates it for up to $d. You will automatically '
                          'stop attacking. Target must be facing you. Any damage received by the stunned target will '
                          'revive it.', 'Incapacitated.', instant=True, AttributesEx=_ATTR1_GOUGE,
                          BaseLevel=_GOUGE_LEVEL, SpellLevel=_GOUGE_LEVEL,
                          AuraInterruptFlags=_AURA_INTERRUPT_DAMAGE, RangeIndex=_RANGE_COMBAT,
                          DefenseType=_DEFENSE_MELEE, PreventionType=_PREVENTION_PACIFY, SpellVisualID_1=_SV_GOUGE),
)

kick_211411 = spell(
    id=211411, name='Kick', school=School.NORMAL, dispel=0, mechanic=0, attributes=_ATTR_KICK, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=5.0,
    duration_ms=_KICK_LOCKOUT_MS,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=2, points_per_level=1.5, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_FLAT),
             Effect(type=EffectType.INTERRUPT_CAST, base_points=0, die_sides=0, mechanic=_MECHANIC_INTERRUPT,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_KICK,
    notes=f'{_SD}: the Grim Patron\'s Kick 15610 as the dungeon\'s own copy (the stock spell may be shared, ruling '
          '65), with the school lockout the interrupt leaves cut from 6 s to 3 s. Everything else is the stock row: '
          'Physical damage (3 plus 1.5 a level above 20: about 48 on a level 50 patron, the spec\'s "3 Physical" is '
          'the base number) and the interrupt effect, melee range, instant, the stock look (SV 90, icon 246). Cast by '
          'the Grim Patron\'s SmartAI (9545 id 0: an AREA_CASTING event, 25% a fire, first at 3 to 5 s, repeat 5 to '
          '8 s, within 5 yd). The 28 patrons run their normal rows on heroic too.',
    raw_overrides=kit_raw('Kicks an enemy for $s1 damage, interrupting the spell being cast for $d.', '',
                          instant=True, BaseLevel=_KICK_LEVEL, SpellLevel=_KICK_LEVEL, RangeIndex=_RANGE_COMBAT,
                          DefenseType=_DEFENSE_MELEE, PreventionType=_PREVENTION_PACIFY, SpellVisualID_1=_SV_KICK),
)
