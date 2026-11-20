"""
Blackrock Depths build WP-D20: Ambassador Flamelash (9156, Burning Spirit 9178; Portal Anchor 300842), normal and
heroic (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 / s3.5 row D20, s3.6, s3.8, s3.10;
build spec docs/dungeons/blackrock-depths-4-imperial-seat.md "Ambassador Flamelash" S4 740-783, FL1-FL5, rulings 70-71
and 88). WP-D20 owns this file (its spells: kSpellsFlamelash 211490-211519 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h only; FlamelashLogic.h names the same ids; its creature: 300842). The
engine side is src/BlackrockDepths/boss_ambassador_flamelash_rework.cpp; his texts are
data/sql/updates/pending_db_world/rev_flamelash_blackrock_depths.sql.

Wave 2 (sections 3-4): the unit columns of 9156 and 9178 are held back until BIND_WAVE_2 flips (_common.py); the spells
and the Portal Anchor are declared as if bound (the spells are new ids nothing uses until then).

- 9156 Ambassador Flamelash: boss_ambassador_flamelash_rework (SmartAI off: he had none, the stock C++ boss stays
  registered, unbound), the build spec's normal health (150k = HealthModifier 57.383 on the level 55 warrior class base
  2,614), stun immunity 1972 (the stock -251 goes), INSTANCE_BIND, DamageModifier 3.5 (the stock base value; the live 5
  is a leftover). Heroic 210k is WP-H's override (source/world/dungeons/blackrock_depths.py). His loot and spawn are the
  stock rows' (L-2 adds the Dark Keeper Key).
- 9178 Burning Spirit: npc_burning_spirit_rework (the stock npc_burning_spirit stays registered, unbound), 1,500 health
  (HealthModifier 1.57068 on the L30 warrior base 955; heroic 4,500 is WP-H's override), no creature immunities (the
  stock -62 held the Fire school, disarm, sleep and knockout: the spirits are must-kill adds and lose their Fire
  immunity, handoff s7 #10; slows, roots and stuns land), standing still (the stock random MovementType goes: the boss
  marches them). No SmartAI, no loot, no spawns (summoned only by the boss script).
- 300842 Portal Anchor (FL2): a boss-kit add on a rune spot, an elemental (type 4, faction 54 like him), level 55 elite
  warrior class, 4,000 health (HealthModifier 1.5302 on 2,614; heroic 12,000 is WP-H's `extra=`, difficulty_entry_1
  310416 per STAGE-H-REPORT section 3), no melee (DamageModifier 0: it never attacks), no loot, no XP, stun immunity
  1972 (a fear or a stun would walk or freeze a stationary add; the kit's set holds both), the invisible stalker's
  display (11686): the portal look is a lasting state on it (SV 90658, V-1's FL_PORTAL_ANCHOR). In game: whether an
  invisible display can be clicked (tab and the name plate always can; the fallback is a visible model at a small
  scale).

Spells. His damage is a percent of the reference row (FlamelashLogic.h ScaledPct, +10% a Burning Spirit stack): Fire
Blast and the two Kindling ticks through spell_brd_flamelash_damage (RefFlatOn at launch), the trail patch through the
registry (a resolve copy). Every damage spell ignores caster modifiers (rule 2), so the stack aura raises only his
melee by itself:

  211490  Firelands Portal     FL2 the anchor's portal look: a lasting state (SV 90658), cast by the anchor on itself
  211491  Burning Spirit       FL3 his stack: +10% damage done and +5% size a stack, 30 s refreshed, 10 at most
  211492  Burning Spirit       FL3 the flash of an arrival, on him (look only)
  211493  Fire Blast           FL1 the copy of 13342: Fire, 20 yd, 15% (heroic 20%) of the tank row
  211494  Kindling             FL4 the 8 s channel on its target (not interruptible)
  211495  Kindled              FL4 the mark on the target for the channel: an Ignite state, 8 s
  211496  Kindling             FL4 a tick on each other player in range: 8% (heroic 12%) of the row
  211497  Kindling             FL4 a tick on the target: 3% (heroic 5%) of the row
  211498  Burning Trail        FL5 (heroic) the patch's look on a generic stalker, 15 s
  211499  Burning Trail        FL5 (heroic) the patch's hit: resolve copy, Fire, 8% of the row a second
  211500-211519 spare.

Visual ids are WP-V-1's (._visuals; every look is unconfirmed until seen in game). Fire Blast keeps the stock 13342's
look (SV 2996, ._visuals FL_FIRE_BLAST).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import (
    creature_model,
    creature_template,
    creature_template_columns,
    scripted_by,
    spell,
)

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    FACTION_DARK_IRON,
    IMMUNITY_BOSS_STUN,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    FL_FIRE_BLAST,
    DISPLAY_INVISIBLE_STALKER,
    FL_BURNING_SPIRIT_STACK,
    FL_BURNING_TRAIL,
    FL_KINDLING_CHANNEL,
    FL_KINDLING_STATE,
    FL_PORTAL_ANCHOR,
)

_D20 = 'Blackrock Depths build WP-D20 (Ambassador Flamelash)'
_SCRIPT = 'spell_brd_flamelash_damage'
_SCRIPT_PCT = ('Blackrock Depths D20: a percent of reference health times his Burning Spirit stack, set by '
               'spell_brd_flamelash_damage (FlamelashLogic.h ScaledPct, RefFlatOn)')

# Held back until wave 2 binds these units (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(9156, **boss_columns(
        'boss_ambassador_flamelash_rework', 57.383, damage_modifier=3.5,
    ))
    creature_template_columns(
        9178, ScriptName='npc_burning_spirit_rework', AIName='', HealthModifier=1.57068, MovementType=0,
        CreatureImmunitiesId=0,
    )

# heroic_ids.lock (STAGE-H-REPORT section 3): the first wave 2 kit add is 310407 (300830); the anchor is the tenth.
PORTAL_ANCHOR_HEROIC_ENTRY = 310416

# --- constants (FlamelashLogic.h; lib/test_blackrock_depths_flamelash.py pins each against the header) ---------------

FIRE_BLAST = (1500, 2000)       # kFireBlastPct 15 / 20 (hundredths)
BURN_OTHERS = (800, 1200)       # kKindlingOthersPct 8 / 12
BURN_SELF = (300, 500)          # kKindlingSelfPct 3 / 5
KINDLING_MS = 8000              # kKindlingMs
STACK_DAMAGE = 10               # kStackDamagePctPerStack
STACK_SIZE = 5                  # kStackSizePctPerStack
STACK_CAP = 10                  # kStackCap
STACK_MS = 30000                # kStackLifeMs
FIRE_BLAST_RANGE = 20.0         # kFireBlastRangeYd
ANCHOR_HEALTH_MODIFIER = 1.5302     # 4,000 on the level 55 warrior base 2,614 (was 8,000; spirit 3,000 -> 1,500: the
#                                     2026-11-19 brd-s4 bot smoke could not keep up, designer call; heroic unchanged)

_ATTR1_IS_CHANNELED = 0x00000004        # SPELL_ATTR1_IS_CHANNELED
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127

# Icons of the stock spells each one stands in for (stock Spell.dbc SpellIconID).
_ICON_FIRE_BLAST = 12               # Fire Blast 13342
_ICON_PORTAL = 37                   # Flamestrike 2120
_ICON_BURNING_SPIRIT = 16           # Fire Ward 543
_ICON_KINDLING = 678                # Flame Shock 8050
_ICON_BURN = 33                     # Fire Nova 1535

# --- 300842 Portal Anchor ---------------------------------------------------------------------------------------------

portal_anchor_300842 = creature_template(
    300842, 'Portal Anchor', **{
        **kit_creature(faction=FACTION_DARK_IRON, type=4), 'minlevel': 55, 'maxlevel': 55, 'rank': 1,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': ANCHOR_HEALTH_MODIFIER, 'DamageModifier': 0.0,
        'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
        'mingold': 0, 'maxgold': 0, 'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'ScriptName': 'npc_brd_portal_anchor_rework', 'difficulty_entry_1': PORTAL_ANCHOR_HEROIC_ENTRY,
    },
)
creature_model(300842, display_id=DISPLAY_INVISIBLE_STALKER)

# --- FL2 Firelands Portals -------------------------------------------------------------------------------------------

firelands_portal_211490 = spell(
    id=211490, name='Firelands Portal', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_PORTAL,
    notes=f'{_D20}, FL2: the anchor\'s look, a DUMMY aura the Portal Anchor 300842 casts on itself (triggered) when '
          'the boss opens it: the shipped portal state (V-1 FL_PORTAL_ANCHOR, SV 90658: the stock '
          'Creature_SpellPortalLarge_Red at 0.4, about 4 yd tall; the stock 12 yd Boss Fire Portal State SV 9462 is '
          'the alternate). Lasting; it goes with the anchor. No effect.',
    raw_overrides=kit_raw('A rift to the Firelands.', 'A rift to the Firelands. Burning Spirits pour out.',
                          CastingTimeIndex=1, SpellVisualID_1=FL_PORTAL_ANCHOR, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- FL3 Burning Spirit ----------------------------------------------------------------------------------------------

burning_spirit_211491 = spell(
    id=211491, name='Burning Spirit', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=STACK_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=STACK_DAMAGE,
               die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Burning Spirit: a flat +10% damage done per stack, not a damage or heal value'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SCALE, base_points=STACK_SIZE, die_sides=0,
               implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Burning Spirit: +5% model size per stack, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_BURNING_SPIRIT,
    notes=f'{_D20}, FL3: the stock Burning Spirit 14744 (+30 damage and +6% size a stack, 180 s, 50 stacks) '
          'rescaled: each spirit that reaches him adds a stack (DungeonKit::AddStacks on himself): +10% damage done '
          'and +5% size, 30 s refreshed by every arrival, 10 at most (CumulativeAura 10: +100% damage and +50% size '
          'at the cap). His own spells ignore caster modifiers (rule 2), so the aura raises his melee and the scripts '
          'raise Fire Blast and the Kindling ticks by the same 10% a stack (FlamelashLogic.h DamageScale). Not '
          'dispellable or stealable; removed on his death, evade and reset. No look of its own (the arrival flash is '
          '211492, the size is the tell).',
    raw_overrides=kit_raw('Each spirit that reaches him makes him stronger.',
                          'Damage done increased by $s1% and size by $s2%.', instant=True, CumulativeAura=STACK_CAP,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

arrival_look_211492 = self_visual(
    211492, 'Burning Spirit', FL_BURNING_SPIRIT_STACK,
    f'{_D20}, FL3: the flash of an arrival. He casts it on himself (triggered) as a spirit reaches him: Burning Spirit '
    '14744\'s SV 3321 (fire hands and FireWard_Impact_Chest). Look only.',
    icon=_ICON_BURNING_SPIRIT, school=School.FIRE,
)

# --- FL1 Fire Blast --------------------------------------------------------------------------------------------------

fire_blast_211493 = spell(
    id=211493, name='Fire Blast', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=FIRE_BLAST_RANGE,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=FIRE_BLAST[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_PCT)],
    spell_icon_id=_ICON_FIRE_BLAST,
    notes=f'{_D20}, FL1: the copy of the stock Fire Blast 13342 (instant, Fire, 20 yd, 165-195, every 7 s) rescaled '
          '(rule 15: a copy in the slice, never the shared override). He casts it (triggered) on his victim at 2 s '
          'then every 7 s: 15% (heroic 20%: EffectMiscValueB) of the tank row, times his Burning Spirit stack '
          '(spell_brd_flamelash_damage, at launch). The spec leaves the number to "stock rescaled" (gap 36): this '
          'WP\'s default. Not interruptible (instant). Resistible like any Fire hit; cannot crit; ignores his '
          'modifiers. Fire Blast 13342\'s look (SV 2996) once V-1 names it.',
    raw_overrides=kit_raw('Inflicts Fire damage to an enemy.', instant=True, EffectMiscValueB_1=FIRE_BLAST[1],
                          DefenseType=_DEFENSE_MAGIC, InterruptFlags=0, PreventionType=0,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          **({'SpellVisualID_1': FL_FIRE_BLAST} if FL_FIRE_BLAST else {})),
)
scripted_by(fire_blast_211493, _SCRIPT)

# --- FL4 Kindling ----------------------------------------------------------------------------------------------------

kindling_211494 = spell(
    id=211494, name='Kindling', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=KINDLING_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_KINDLING,
    notes=f'{_D20}, FL4: his 8 s channel on a random player other than the tank (emote line 2), at 15 s then every '
          '25 s (heroic 20 s). A real channel (SPELL_ATTR1_IS_CHANNELED): it holds him still (no swing) while it lasts '
          'and shows the beam. Not interruptible: ChannelInterruptFlags 0, InterruptFlags 0, PreventionType 0 (a kick '
          'and a silence do nothing), and his immunity set 1972 holds no INTERRUPT. NO_IMMUNITIES so it lands through '
          'Divine Shield (the burns do not). Range 100, ignores line of sight. The channel\'s own aura is a marker; '
          'the script ticks every second (211496 on everyone else within 8 yd, heroic 10 yd, and 211497 on the '
          'target). Fire Storm\'s channel hands (SV 10383, V-1 FL_KINDLING_CHANNEL; never Fire Beam SV 10856: blue '
          'flame and grey smoke).',
    raw_overrides=kit_raw('Channels fire into a player. Everyone near them burns.',
                          'Channeled by Flamelash. Nearby allies burn.', CastingTimeIndex=1,
                          SpellVisualID_1=FL_KINDLING_CHANNEL, ChannelInterruptFlags=0, InterruptFlags=0,
                          PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx=ATTR1_NO_THREAT | _ATTR1_IS_CHANNELED,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

kindled_211495 = spell(
    id=211495, name='Kindled', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=KINDLING_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_KINDLING,
    notes=f'{_D20}, FL4: the mark on the channel\'s target for its 8 s, cast by him (triggered) with the channel: '
          'Ignite 12654\'s lasting Immolate state (SV 2638, V-1 FL_KINDLING_STATE), and the tooltip that tells a human '
          'player to leave the group. The script removes it when the channel ends. Not dispellable, dropped on a map '
          'change. No effect.',
    raw_overrides=kit_raw('Everyone near you burns. Move away from your allies.',
                          'Allies within 8 yards (heroic 10) burn every second. Run away from the group.',
                          CastingTimeIndex=1, SpellVisualID_1=FL_KINDLING_STATE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)


def _burn(spell_id: int, pct: tuple[int, int], who: str, note: str):
    """A Kindling tick: a Fire SCHOOL_DAMAGE of `pct` hundredths of the reference row (normal in the effect, heroic in
    EffectMiscValueB), set per target at launch by spell_brd_flamelash_damage. Always hits, cannot crit, ignores line of
    sight and his modifiers; no look (the mark and the channel carry it)."""
    spell_obj = spell(
        id=spell_id, name='Kindling', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct[0] - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_PCT)],
        spell_icon_id=_ICON_BURN, notes=f'{_D20}, FL4: {note}',
        raw_overrides=kit_raw(f'Burns {who}.', instant=True, EffectMiscValueB_1=pct[1], InterruptFlags=0,
                              PreventionType=0, DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(spell_obj, _SCRIPT)
    return spell_obj


burn_others_211496 = _burn(
    211496, BURN_OTHERS, 'everyone near the target',
    'a tick of Kindling on each other player of the fight within 8 yd (heroic 10 yd) of the channel\'s target, every '
    'second of the 8 s (the script casts it, triggered, from the boss): 8% (heroic 12%: EffectMiscValueB) of the '
    'reference row, the tank row on the tank (ruling 88), times his Burning Spirit stack. No Weakened (damage over '
    'time). Ignores line of sight. No look (the mark and the channel carry it).',
)

burn_self_211497 = _burn(
    211497, BURN_SELF, 'the target',
    'a tick of Kindling on the channel\'s target, every second of the 8 s: 3% (heroic 5%) of the reference row, less '
    'than the others take (the target burns too, less), times his Burning Spirit stack. Same shape as 211496.',
)

# --- FL5 Burning Trail (heroic) --------------------------------------------------------------------------------------

burning_trail_look_211498 = spell(
    id=211498, name='Burning Trail', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_PORTAL,
    notes=f'{_D20}, FL5 (heroic): a patch\'s look, a DUMMY aura a generic stalker (300796) casts on itself (triggered) '
          'where the Kindled player stood, every 2 s of the channel: the shipped 4 yd lava pool state (SV 90606, '
          'V-1 FL_BURNING_TRAIL, Blackrock Spire\'s ladder) under the registry\'s 4 yd ring. The stalker despawns '
          'after 15 s with the patch. No effect. Fallback: the 8 yd fire zone (SV 90508, FL_BURNING_TRAIL_ALT).',
    raw_overrides=kit_raw('A trail of fire.', 'A trail of fire.', CastingTimeIndex=1,
                          SpellVisualID_1=FL_BURNING_TRAIL, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

burning_trail_211499 = resolve_copy(
    211499, 'Burning Trail', School.FIRE, 'The ground burns.',
    f'{_D20}, FL5 (heroic): the patch\'s hit, a persistent 4 yd registry circle (tag 5): 1 s of warning, then a '
    'tick a second for 14 s (15 s in all) at 8% of the reference row, the tank on its own row, times his stack at '
    'the patch\'s creation (set when it is registered). No Weakened (a lingering zone never applies it). Copy of the '
    'resolve spell 205001 (Fire).',
    icon=_ICON_PORTAL,
)
