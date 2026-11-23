"""
Scarlet Monastery build WP-D8: Arcanist Doan (6487, guid 40124, path 401240), the Library's end boss; the Arcane Anchor
300919; the Chamber Seal object 301319 (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5
row D8, s7 #22 A; build spec docs/dungeons/scarlet-monastery-2-library.md "Arcanist Doan", DN0-DN4). WP-D8 owns this
file; WP-S0 wrote the skeleton. The seal's object template, his new texts (groups 4-5) and the rows dbc-tools cannot
declare are data/sql/updates/pending_db_world/rev_doan_scarlet_monastery.sql. The hard mode (the Kel'Thuzad Heresy)
is WP-D8H's: doan_hard_mode.py.

- 6487 Arcanist Doan: bound to boss_arcanist_doan_rework (modules/mod-dungeon-bosses src/ScarletMonastery/
  boss_arcanist_doan_rework.cpp), SmartAI off (S0's rev drops its 7 rows), the build spec's normal health (46k =
  HealthModifier 50.998 on the level 35 mage class base 902), stun immunity 1972, INSTANCE_BIND (flags_extra 1), the
  stock DamageModifier 2.4. Heroic health (230k) and the tier's melee are WP-H's overrides. His stock spawn (guid
  40124) and patrol path 401240 stay: the patrol runs out of combat only.
- 300919 Arcane Anchor: a kill target the bubble raises on fixed spots (DoanLogic.h kAnchorSpots); level 34 warrior,
  1.2k (HealthModifier 1.0318 on the base 1,163; the spec's 1.7k cut by the HANDOFF s10 option D default, 2026-11-20,
  pending the user's confirmation), Scarlet Crusade (faction 67), no melee (DamageModifier 0), never
  moves (npc_sm_arcane_anchor: passive, no combat movement, its beam into the bubble), stun immunity 1972 (an anchor
  that could be feared would walk off its spot; banished it would hold the bubble up), no loot, no XP, display 24813
  (ScryingOrb, V's pick). Its heroic template (5k by option D, the spec's 8k; level 60) is WP-H's (`extra=`); the hard
  mode's 1.25 x (6.25k) is D8H's script.

Spells (kSpellsDoan 212670-212709; DoanLogic.h names the same ids; looks from ._visuals, WP-V's DN_* picks, every look
unconfirmed until seen in game). His damage is a percent of the reference row (the tank row on the tank): the registry
lands Detonation, the patches, the Explosion, the Marks and the pools through resolve copies; Flamestrike binds the
kit's spell_dungeon_refflat_damage (the percent in hundredths in the effect, EffectMiscValueB on heroic):

  212670  Arcane Bubble          DN1 his immunity while the anchors stand: SCHOOL_IMMUNITY (every school), the bubble
  212671  Detonation             DN1 the 10 s bar (Arcane, not interruptible: a kicked Flamestrike locks Fire)
  212672  Detonation             DN1 the blast on a miss: resolve copy, Fire, 75% / 130% (the hard mode 200%: D8H)
  212673  Arcane Anchor          DN1 an anchor's channel into the bubble (Magic Barrier's ManaBeam, never SV 6742)
  212674  Overloaded             DN1 the reward: +50% damage taken for 10 s (Arcane Power's state)
  212675  Scorched               DN1a a patch's tick: resolve copy, Fire, 6% / 10% a second
  212676  Scorched               DN1a a patch's look, an aura on a stalker (the shipped 5 yd lava rung)
  212677  Arcane Explosion       DN2 the 2 s bar (Arcane, not interruptible)
  212678  Arcane Explosion       DN2 the hit: resolve copy, Arcane, 30% / 45% and Weakened
  212679  Arcane Explosion       DN2 the nova's look on him at the resolve (the stock SV 965)
  212680  Mark of Righteous Fire DN3 the 5 s debuff on a marked player (Living Bomb's state; not dispellable)
  212681  Mark of Righteous Fire DN3 the burst on the others inside 8 yd: resolve copy, Fire, 35% / 45% and Weakened
  212682  Mark of Righteous Fire DN3 the marked player's own share: resolve copy, Fire, 15% / 20%
  212683  Mark of Righteous Fire DN3 the burst's look on a stalker at the spot (Living Bomb's burst SV 10693)
  212684  Righteous Fire         DN3a a pool's tick (heroic): resolve copy, Fire, 10% a second
  212685  Righteous Fire         DN3a a pool's look, an aura on a stalker (the shipped 4 yd lava rung; the pool is 3)
  212686  Righteous Flamestrike  DN4 the 2.5 s interruptible cast (heroic): missed, 40% Fire to every player
  212687  Detonation             DN1 heroic's 14 s bar (option D; the same look and school as 212671)
  212688-212709 spare.

The bars are Arcane and the only interruptible cast is Fire (handoff s3.5 rule 5). Tooltips are number-free.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

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
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_DOAN_ANCHOR,
    DN_ANCHOR_BEAM,
    DN_BUBBLE,
    DN_DETONATION,
    DN_EXPLOSION,
    DN_FLAMESTRIKE,
    DN_MARK,
    DN_MARK_BURST,
    DN_OVERLOADED,
    DN_POOL,
    DN_SCORCHED,
)

_D8 = 'Scarlet Monastery build WP-D8 (Arcanist Doan)'

# --- the creatures ---------------------------------------------------------------------------------------------------

creature_template_columns(6487, **boss_columns(
    'boss_arcanist_doan_rework', 50.998, damage_modifier=2.4,
))

# The anchor's heroic entry (difficulty_entry_1 = its id in source/world/heroic_ids.lock, minted by H's write run: the
# declared wave 1 kit adds in entry order). None until H's table names it: generate.py --check then prints the number
# the full row must carry (lib/dungeon_heroic.py). Shared-file request in the WP-D8 report.
ARCANE_ANCHOR_HEROIC = 310473

ARCANE_ANCHOR = 300919

_CLASS_WARRIOR = 1
_CREATURE_TYPE_NOT_SPECIFIED = 10
_FLAGS_EXTRA_NO_XP = 0x40

# The normal health at 5 players: 1.2k = 1.0318 x 1,163 (the level 34 warrior base, creature_classlevelstats basehp0,
# live 2026-11-20). HANDOFF s10 option D (orchestrator default 2026-11-20, pending the user's confirmation); revert:
# the spec's 1.7k = 1.4617 (and kAnchorHealthNormal 1700).
ANCHOR_HEALTH_MODIFIER = 1.0318


def _heroic_entry(columns: dict, heroic_entry) -> dict:
    """`columns` with difficulty_entry_1 when H's table names the heroic entry (a declared full row must carry it)."""
    if heroic_entry:
        return {**columns, 'difficulty_entry_1': heroic_entry}
    return columns


arcane_anchor_300919 = creature_template(300919, 'Arcane Anchor', **_heroic_entry({
    **KIT_CREATURE, 'faction': FACTION_SCARLET_CRUSADE, 'type': _CREATURE_TYPE_NOT_SPECIFIED, 'minlevel': 34,
    'maxlevel': 34, 'rank': 0, 'unit_class': _CLASS_WARRIOR, 'unit_flags': 0,
    'HealthModifier': ANCHOR_HEALTH_MODIFIER, 'DamageModifier': 0.0, 'BaseAttackTime': 2000,
    'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 0,
    'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'ExperienceModifier': 0.0,
    'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_sm_arcane_anchor', 'AIName': '',
}, ARCANE_ANCHOR_HEROIC))
creature_model(300919, display_id=DISPLAY_DOAN_ANCHOR)

# --- constants (DoanLogic.h; lib/test_scarlet_monastery_doan.py pins each against the header) -----------------------

DETONATION_CAST_MS = 10000          # kDetonationCastMs
DETONATION_CAST_MS_HEROIC = 14000   # kDetonationCastMsHeroic (HANDOFF s10 option D)
EXPLOSION_CAST_MS = 2000            # kExplosionCastMs
MARK_MS = 5000                      # kMarkMs
OVERLOADED_MS = 10000               # kOverloadedMs
OVERLOADED_PCT = 50                 # kOverloadedDamageTakenPct
FLAMESTRIKE_CAST_MS = 2500          # kFlamestrikeCastMs
FLAMESTRIKE_PCT = 4000              # kFlamestrikePct 40 (hundredths; heroic only: the same in both slots)

_AURA_SCHOOL_IMMUNITY = 39          # SPELL_AURA_SCHOOL_IMMUNITY (SpellAuraDefines.h; not in lib.dsl's AuraType)
_SCHOOL_MASK_ALL = 127
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_ATTR1_IS_CHANNELED = 0x00000004
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_SPELL_INTERRUPT_FLAGS_KICK = 15

_SCRIPT_REFFLAT = ('Scarlet Monastery D8: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn: the tank row on the tank)')

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_ARCANE_BUBBLE = 81            # Arcane Bubble 9438
_ICON_DETONATION = 37               # Detonation 9435 (and Flamestrike 2120)
_ICON_MAGIC_BARRIER = 182           # Magic Barrier 38112
_ICON_ARCANE_POWER = 62             # Arcane Power 12042
_ICON_FLAME_PATCH = 876             # Flame Patch 35383
_ICON_ARCANE_EXPLOSION = 122        # Arcane Explosion 9433
_ICON_MARK_OF_FLAMES = 12           # Mark of Flames 15128
_ICON_LIVING_BOMB = 3000            # Living Bomb 44457
_ICON_FLAMESTRIKE = 37              # Flamestrike 2120


def _self_aura(spell_id: int, name: str, school: School, visual: int, icon: int, desc: str, aura_desc: str, notes: str):
    """A look-only DUMMY aura a stalker (or Doan) casts on itself, no duration (removed with its caster)."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1, SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- DN1 Burn in Righteous Fire --------------------------------------------------------------------------------------

arcane_bubble_212670 = spell(
    id=212670, name='Arcane Bubble', school=School.ARCANE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_SCHOOL_IMMUNITY, base_points=0,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_ARCANE_BUBBLE,
    notes=f'{_D8}, DN1 Burn in Righteous Fire: Doan casts it on himself (triggered) at every bubble (20 s, then '
          'every 35 s; heroic 30 s) and the script removes it when the bubble breaks or Detonation lands. '
          'SPELL_AURA_SCHOOL_IMMUNITY to every school (127, the Divine Shield shape): an approved immune set piece '
          '(hub rulings 27-28), answered by the Arcane Anchors he raises with it. Not dispellable and no mechanic, so '
          'Mass Dispel and Spellsteal leave it. Arcane Bubble 9438\'s SpellVisual 968 (ManaShield_State_Base). The '
          'bots ignore him while it is up and break the anchors (the descriptor).',
    raw_overrides=kit_raw('Immune while the arcane anchors stand.', 'Immune to all damage while the anchors stand.',
                          CastingTimeIndex=1, SpellVisualID_1=DN_BUBBLE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

detonation_cast_212671 = cast_bar(
    212671, 'Detonation', DETONATION_CAST_MS, 'Arcanist Doan gathers righteous fire inside his bubble.',
    f'{_D8}, DN1: the 10 s bar players read while the bubble holds; break every Arcane Anchor before it ends. Not '
    'interruptible (he is immune anyway); the script\'s clock lands the blast when it ends, whatever happens to the '
    'bar. Arcane: a kicked Righteous Flamestrike (Fire, heroic) locks Fire, never this bar (rule 5). Detonation '
    '9435\'s SpellVisual 1585 (fire hands and FlamestrikeSmall; VR RISKY: no arcane read).',
    icon=_ICON_DETONATION, visual=DN_DETONATION, school=School.ARCANE,
)

detonation_cast_heroic_212687 = cast_bar(
    212687, 'Detonation', DETONATION_CAST_MS_HEROIC, 'Arcanist Doan gathers righteous fire inside his bubble.',
    f'{_D8}, DN1 heroic: the 14 s bar (the orchestrator\'s balance default, HANDOFF s10 option D, 2026-11-20, pending '
    'the user\'s confirmation: heroic anchors 5k with a longer bar). 212671 with a 14 s cast time: '
    'DetonationBarSpellFor(heroic) casts it and the script\'s clock (DetonationCastMsFor) lands the blast when it '
    'ends, so the bar and the blast agree. Arcane, not interruptible (rule 5). Revert: the script back on 212671; '
    'this row can stay declared, unused.',
    icon=_ICON_DETONATION, visual=DN_DETONATION, school=School.ARCANE,
)

detonation_212672 = resolve_copy(
    212672, 'Detonation', School.FIRE, 'Righteous fire fills the chamber.',
    f'{_D8}, DN1: the blast when the bar completes with an anchor standing: every player in the sealed chamber, 75% '
    '(heroic 130%: lethal on purpose, hub ruling 28; the hard mode 200% through D8H) of the reference row, the tank '
    'row on the tank (registry tag 1, a group failure: no Weakened). Then two Scorched patches and one more anchor '
    'next time. DungeonKit::RegistryHit on the chamber\'s players. Copy of the mod-boss-mechanics resolve spell 205001 '
    '(Fire).',
    icon=_ICON_DETONATION,
)

anchor_beam_212673 = spell(
    id=212673, name='Arcane Anchor', school=School.ARCANE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50.0,
    duration_ms=12000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_MAGIC_BARRIER,
    notes=f'{_D8}, DN1: an anchor\'s beam into the bubble, a channel each Arcane Anchor casts (triggered) on Doan '
          'when it rises and again whenever the channel drops while the bubble holds (npc_sm_arcane_anchor). Magic '
          'Barrier 38112\'s SpellVisual 8795 (a ManaBeam channel chain; VR: Arcane Channeling 23017\'s SV 6742 is a '
          'hand glow with no beam, never wire it). A DUMMY aura on Doan, no effect; ignores his bubble\'s immunity '
          '(NO_IMMUNITIES) and line of sight; 12 s, ended by the anchor\'s death or despawn. AuraInterruptFlags '
          'CHANGE_MAP.',
    raw_overrides=kit_raw('', 'An arcane anchor feeds the bubble.', CastingTimeIndex=1, InterruptFlags=0,
                          ChannelInterruptFlags=0, PreventionType=0, SpellVisualID_1=DN_ANCHOR_BEAM,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

overloaded_212674 = spell(
    id=212674, name='Overloaded', school=School.ARCANE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=OVERLOADED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=OVERLOADED_PCT - 1, die_sides=1, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_ARCANE_POWER,
    notes=f'{_D8}, DN1 the reward: every anchor broken before Detonation\'s bar ends shatters the bubble; Doan casts '
          'it on himself (triggered): +50% damage taken from every school for 10 s, and the script holds his casts '
          '(Arcane Explosion, the Marks, Flamestrike) meanwhile. Not dispellable or stealable (the reward stays). '
          'Arcane Power\'s lasting state SV 9937 (V; new look, gap 20). Removed with his reset, evade and death.',
    raw_overrides=kit_raw('Overloaded: damage taken increased.', 'Overloaded. Damage taken increased.',
                          CastingTimeIndex=1, SpellVisualID_1=DN_OVERLOADED, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- DN1a Scorched ---------------------------------------------------------------------------------------------------

scorched_212675 = resolve_copy(
    212675, 'Scorched', School.FIRE, 'The floor burns with righteous fire.',
    f'{_D8}, DN1a: a Scorched patch\'s tick, two 5 yd patches per completed Detonation on random floor spots of the '
    'chamber (off the anchor spots and each other), for the rest of the fight, one tick a second: 6% (heroic 10%) of '
    'the reference row, the tank row on the tank (registry tag 11). Lingering: no Weakened. Normal caps the patches '
    'at 4. Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_FLAME_PATCH,
)

scorched_look_212676 = _self_aura(
    212676, 'Scorched', School.FIRE, DN_SCORCHED, _ICON_FLAME_PATCH, 'Scorched floor.', 'Scorched floor.',
    f'{_D8}, DN1a: a patch\'s look, a DUMMY aura the generic stalker (300922) standing on it casts on itself '
    '(triggered) for the fight: the shipped 5 yd lava rung SV 90607 (the Blackrock Spire ladder; exact size, under '
    'the registry\'s ring). No effect; the stalker is Doan\'s summon and goes with the fight.',
)

# --- DN2 Arcane Explosion --------------------------------------------------------------------------------------------

explosion_cast_212677 = cast_bar(
    212677, 'Arcane Explosion', EXPLOSION_CAST_MS, 'Arcanist Doan gathers arcane power around himself.',
    f'{_D8}, DN2: the 2 s bar before the explosion (8 s after the pull, then every 12 s, never while bubbled or '
    'Overloaded): everyone steps out of 10 yd, the tank too. Not interruptible: the registry\'s circle on him owns the '
    'hit (212678). Arcane: a kicked Flamestrike (Fire) never locks it (rule 5).',
    icon=_ICON_ARCANE_EXPLOSION, school=School.ARCANE,
)

arcane_explosion_212678 = resolve_copy(
    212678, 'Arcane Explosion', School.ARCANE, 'Arcane energy bursts out of Arcanist Doan.',
    f'{_D8}, DN2: the hit, 10 yd round Doan at the end of the 2 s bar: 30% (heroic 45%) of the reference row and 1 '
    'Weakened, the tank row on the tank (registry tag 2, a Zone circle on him). Copy of the resolve spell 205001 '
    '(Arcane).',
    icon=_ICON_ARCANE_EXPLOSION,
)

explosion_look_212679 = self_visual(
    212679, 'Arcane Explosion', DN_EXPLOSION,
    f'{_D8}, DN2: the nova on Doan the moment the circle resolves, cast on himself (triggered): Arcane Explosion '
    '9433\'s SpellVisual 965 (ArcaneExplosion_Base). Look only.',
    icon=_ICON_ARCANE_EXPLOSION, school=School.ARCANE,
)

# --- DN3 Mark of Righteous Fire --------------------------------------------------------------------------------------

mark_212680 = spell(
    id=212680, name='Mark of Righteous Fire', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=MARK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_MARK_OF_FLAMES,
    notes=f'{_D8}, DN3: the mark on 2 (heroic 3) random players, never the tank (an 8 yd spread would push the melee '
          'off him: shared doc section 5), 15 s after the pull then every 20 s (the hard mode 30 s), never while '
          'bubbled or Overloaded; Doan casts it (triggered). 5 s, then the burst where they stand (the registry\'s 8 '
          'yd circle that followed them: 212681 / 212682). A DUMMY with no effect: the read is Living Bomb 44457\'s '
          'lasting state SV 10692. Not dispellable (the burst is the registry\'s, a dispel would only hide the '
          'tell). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Marked with righteous fire: in 5 seconds it bursts around you.',
                          'Marked. In a few seconds righteous fire bursts around you: get away from your allies.',
                          CastingTimeIndex=1, SpellVisualID_1=DN_MARK, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

mark_burst_212681 = resolve_copy(
    212681, 'Mark of Righteous Fire', School.FIRE, 'Righteous fire bursts out of a marked ally.',
    f'{_D8}, DN3: the burst on everyone else within 8 yd of a marked player when the 5 s mark ends: 35% (heroic 45%) '
    'of the reference row and 1 Weakened, the tank row on the tank (registry tag 3; DungeonKit::FollowThenLand, '
    'which never hits its carrier). Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_LIVING_BOMB,
)

mark_self_212682 = resolve_copy(
    212682, 'Mark of Righteous Fire', School.FIRE, 'Righteous fire bursts out of you.',
    f'{_D8}, DN3: the marked player\'s own share of the burst: 15% (heroic 20%) of the reference row, no Weakened '
    '(registry tag 3; DungeonKit::RegistryHit on the carrier at the landing). Copy of the resolve spell 205001 '
    '(Fire).',
    icon=_ICON_LIVING_BOMB,
)

mark_burst_look_212683 = self_visual(
    212683, 'Mark of Righteous Fire', DN_MARK_BURST,
    f'{_D8}, DN3: the burst\'s look, cast by a generic stalker (300922) Doan summons at the landing spot for 2 s, on '
    'itself (triggered): Living Bomb 44461\'s SpellVisual 10693 (mage_livingbomb_area; VR: the doc\'s 44457 is the '
    'state, 44461 the burst). Look only.',
    icon=_ICON_LIVING_BOMB, school=School.FIRE,
)

# --- DN3a Righteous Fire pool (heroic) -------------------------------------------------------------------------------

pool_212684 = resolve_copy(
    212684, 'Righteous Fire', School.FIRE, 'A pool of righteous fire.',
    f'{_D8}, DN3a (heroic): a pool\'s tick, 3 yd at each Mark\'s burst, forming 1 s after it (the marked player steps '
    'off), for 30 s (the hard mode: the rest of the fight, D8H), one tick a second: 10% of the reference row, the '
    'tank row on the tank (registry tag 31). Lingering: no Weakened. Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_FLAME_PATCH,
)

pool_look_212685 = _self_aura(
    212685, 'Righteous Fire', School.FIRE, DN_POOL, _ICON_FLAME_PATCH, 'A pool of righteous fire.',
    'A pool of righteous fire.',
    f'{_D8}, DN3a (heroic): a pool\'s look, a DUMMY aura the generic stalker (300922) at the pool casts on itself '
    '(triggered) while the pool lasts: the shipped 4 yd lava rung SV 90606 (VR RISKY: the smallest rung is 4 yd, the '
    'pool 3 yd; the registry\'s marker carries the exact edge). No effect.',
)

# --- DN4 Righteous Flamestrike (heroic) ------------------------------------------------------------------------------

righteous_flamestrike_212686 = spell(
    id=212686, name='Righteous Flamestrike', school=School.FIRE, dispel=0, mechanic=0, attributes=0,
    cast_time_ms=FLAMESTRIKE_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=FLAMESTRIKE_PCT - 1, die_sides=1,
                    implicit_target_a=TARGET_SRC_CASTER, implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY,
                    radius_yards=100.0, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_FLAMESTRIKE,
    notes=f'{_D8}, DN4 Righteous Flamestrike (heroic): a 2.5 s cast 10 s after the pull, then every 15 s, never '
          'while bubbled or Overloaded; an expected interrupt. NOT triggered, so the bar shows and a kick stops it: '
          'InterruptFlags 15 and PreventionType 1 (a silence); his immunity set 1972 holds no INTERRUPT or SILENCE. '
          'Missed it deals 40% (heroic only: the same in both slots) of the reference row, Fire, to every player '
          'within 100 yd (the tank row on the tank, never missed, ignores line of sight and his modifiers). Binds '
          'the kit\'s spell_dungeon_refflat_damage. On the bots\' interrupt list (priority 3). Fire: his bars are '
          'Arcane, so a kick never locks one (rule 5). Flamestrike 2120\'s SpellVisual 10383.',
    raw_overrides=kit_raw('Arcanist Doan calls down righteous fire on everyone.',
                          EffectMiscValueB_1=FLAMESTRIKE_PCT, DefenseType=_DEFENSE_MAGIC,
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          SpellVisualID_1=DN_FLAMESTRIKE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(righteous_flamestrike_212686, 'spell_dungeon_refflat_damage')
