"""
The three Ragefire Chasm hard mode item effects (designer text: docs/dungeons/ragefire-chasm-rework.md ## Loot, "Hard
mode: Taragaman the Hungerer, Starving", approved 2026-11-21, ruling 13): Taragaman's Fang, Heart of the Starving and
Felstorm Greatblade. After the Scarlet Monastery precedent (scarlet_monastery_hard_mode_effects.py).

Every damage number comes from potency (user rule: everything on potency); the Fang's heal and Bloodward are shares of
another hit or heal, sized by their scripts (no potency of their own). All three items are scale="budget"
(ragefire_chasm_hard_mode.py): every tier above the hard mode ladder's 71 carries its own copies of the Fang and its
bite, of the Heart (its share, `scale_amount=True`, the Scarlet Monastery review m5 precedent) and of the Greatblade,
its Felstorm and its spin (lib/item_spell_copies.py), so a script casts its tier's copy (ItemSpellCopies::Resolve). Feed
and Bloodward stay one spell for every tier: their amounts are set by the scripts, so no tooltip names their ids. The
scripts are modules/mod-dungeon-bosses src/RagefireChasm/hard_mode_items.cpp (ids mirrored in
RagefireChasmHardModeItemsLogic.h).

Ids: the `ragefire_chasm_items` reservation 213500-213539 (source/ids.yaml); this file takes 213500-213507.

  213500  Taragaman's Fang        Use (2 min, off the GCD): the leap, a CHARGE to an enemy within 25 yd (the engine
                                  checks line of sight and a walkable path; the script skips it for a wearer in melee
                                  range) and a DUMMY hit delayed by the distance. spell_rfc_taragamans_fang bites
                                  (213501) once the wearer has arrived, never from where the leap started.
  213501  Hungering Bite          Physical, one enemy, attack power potency 250, melee class (armor, melee crit), no
                                  dodge, parry or block. spell_rfc_hungering_bite heals the wearer (213502) for the
                                  damage dealt: after armor, absorbs and the crit, overkill left out.
  213502  Feed                    the heal on the wearer, sized by the script. No potency, no caster bonuses, no crit.
  213503  Heart of the Starving   Equip: a passive proc aura, effect 1 DUMMY amount 30 = the health threshold in
                                  percent, effect 2 DUMMY amount 40 = the share of the heal in percent (grows with the
                                  tier: 40 / 42 / 44 / 50). Landed direct heals, 100%, 20 sec internal cooldown.
                                  spell_rfc_heart_of_the_starving passes a heal on any living target (the healer
                                  included) whose health before the heal was below the threshold, and casts 213504,
                                  unless the target still has a larger one.
  213504  Bloodward               absorbs all schools for 6 sec, sized by the script (the share of the heal's amount).
  213505  Felstorm Greatblade     Equip: PROC_TRIGGER_SPELL. Landed melee hits (auto attacks and melee-class
                                  abilities), 15%, 6 sec internal cooldown, one roll per cast
                                  (spell_rfc_one_roll_per_cast); cast 213506 on the wearer.
  213506  Felstorm                3 sec, a PERIODIC_TRIGGER_SPELL every 1 sec: three spins of 213507. Data only.
  213507  Felstorm (the spin)     Physical, every enemy within 8 yd of the wearer, in combat or not, attack power
                                  potency 35, melee class. Data only.
  213508-213539  spare

No in-combat filter (designer 2026-11-24, Scarlet Monastery ruling B8): an area of about 10 yd hits every enemy in it,
in combat or not. The dungeon doc's "that are in combat" (2026-11-21) is superseded.

Chances, internal cooldowns, potencies and the share are proposals waiting for the designer (STAGE-RF-HM report). None
of the looks were checked in game; they are the ones the dungeon doc gives the boss's own Feast, bite and Felstorm.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import pot_text, procs_on, scripted_by, spell

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}

# Implicit targets (SharedDefines.h Targets)
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_SRC_CASTER = 22

_ATTR0_PASSIVE = 0x00000040
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

_DMG_CLASS_MELEE = 2
_SCHOOL_MASK_ALL = 127

# spell_proc (SpellMgr.h)
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x00000004
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL_OR_CRITICAL = 0x1 | 0x2

_MELEE_HITS = _PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
_HELPFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS

# Stock looks and icons, read from Spell.dbc by name (none checked in game yet).
_SV_FERAL_CHARGE = 5162         # Feral Charge - Bear 16979 (the Taragaman section's Feast leap)
_SV_DEVOUR = 8923               # Devour 38895 (the Taragaman section's Feast bite)
_ICON_BITE = 1680               # Bite 17253
_SV_DIVINE_AEGIS = 10895        # Divine Aegis 47753
_ICON_MARK_OF_BLOOD = 2285      # Mark of Blood 49005
_SV_BLADESTORM = 6044           # Bladestorm 9632 (the Taragaman section's Felstorm spin)
_ICON_WHIRLWIND = 83            # Whirlwind 1680

# An off-GCD payout's time basis (the Deadmines items' precedent).
_PROC_PAYOUT_MS = 1500

_FANG_RANGE = 25.0
# The engine's own charge speed (MotionMaster.h SPEED_CHARGE), yards a second. The spline is slower: MoveSplineInit caps
# it at 28 (the script waits for the landing).
_FANG_SPEED = 42.0
_FELSTORM_RADIUS = 8.0
_BLOODWARD_MS = 6000


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


def _equip_aura(spell_id: int, name: str, school: int, effects: list, desc: str, icon: int, notes: str, *,
                proc_type_mask: int, proc_chance: int) -> object:
    """A passive Equip aura on the wearer (an item's equip spell)."""
    return spell(
        id=spell_id, name=name, school=school, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes=notes,
        raw_overrides=_raw(desc, ProcTypeMask=proc_type_mask, ProcChance=proc_chance),
    )


# =====================================================================================================================
# Hard mode: Taragaman the Hungerer, Starving

# --- Taragaman's Fang (trinket, Use) ---------------------------------------------------------------------------------

hungering_bite_213501 = spell(
    id=213501, name='Hungering Bite', school=School.NORMAL, attributes=_ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=250.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_BITE,
    notes='Ragefire Chasm hard mode, Taragaman\'s Fang: the bite, cast by the wearer (triggered) from '
          'spell_rfc_taragamans_fang once the leap has landed. Physical, DefenseType MELEE (melee crit, armor), '
          'attack power potency 250, T 1.5 s (an off-GCD payout). NO_ACTIVE_DEFENSE: no dodge, parry or block. '
          'spell_rfc_hungering_bite casts 213502 on the wearer for the damage dealt. SUPPRESS_CASTER_PROCS. Look: '
          'stock Devour SV 8923 (the boss\'s Feast bite).',
    raw_overrides=_raw('Bites the target for {pot1} Physical damage, healing you for the damage dealt.',
                       spell_level=1, DefenseType=_DMG_CLASS_MELEE, SpellVisualID_1=_SV_DEVOUR,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)
scripted_by(hungering_bite_213501, 'spell_rfc_hungering_bite')

feed_213502 = spell(
    id=213502, name='Feed', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=_TARGET_UNIT_CASTER,
                    potency_excluded='the damage the bite dealt, set by spell_rfc_hungering_bite (custom base '
                                     'points)')],
    spell_icon_id=_ICON_BITE,
    notes='Ragefire Chasm hard mode, Taragaman\'s Fang: the heal, cast by the wearer on itself (triggered) from '
          'spell_rfc_hungering_bite with its amount set to the damage the bite dealt. No potency: a share of another '
          'hit, so one spell for every tier. DefenseType 0, CANT_CRIT and IGNORE_CASTER_MODIFIERS: the bite already '
          'had the wearer\'s bonuses and crit (the Spirit Chain 206834 precedent). SUPPRESS_CASTER_PROCS.',
    raw_overrides=_raw('Heals you.', spell_level=1, AttributesEx2=_ATTR2_CANT_CRIT,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_IGNORE_CASTER_MODIFIERS),
)

taragamans_fang_213500 = spell(
    id=213500, name="Taragaman's Fang", school=School.NORMAL, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_FANG_RANGE, duration_ms=0,
    effects=[
        Effect(type=EffectType.CHARGE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_BITE,
    notes='Ragefire Chasm hard mode, Taragaman\'s Fang (Taragaman the Hungerer, Starving, trinket), the Use: 2 min '
          'cooldown, off the GCD, 25 yd, no minimum range. Effect 1 CHARGE (Spell::CheckCast refuses a rooted wearer, '
          'a target out of line of sight and a target with no walkable path; EffectCharge moves at launch), effect 2 a '
          'DUMMY hit that Speed 42 (the charge speed, what SpellInfoCorrections gives every family-0 charge) delays to '
          'distance / 42; the leap itself runs at 28 yd a second (MoveSplineInit::Launch caps a ground spline), so '
          'spell_rfc_taragamans_fang waits and bites with the tier\'s 213501 as soon as the wearer stops charging and '
          'is at the target. A wearer in melee range is not moved: the script prevents the CHARGE at launch, because '
          'the engine does not shorten a path that starts inside the target\'s combat reach and would carry the wearer '
          'to its center; the bite comes with the hit. DefenseType 0 and no damage effect: the leap itself cannot be '
          'missed or avoided. SUPPRESS_CASTER_PROCS. A negative spell, so the bots\' "use trinket" action skips '
          'it; the mod-playerbots leap trinket action presses it (designer 2026-11-24). Look: stock Feral '
          'Charge - Bear SV 5162 (the boss\'s Feast leap).',
    raw_overrides=_raw(
        'Leap to an enemy within 25 yd and bite it for ' + pot_text(hungering_bite_213501) + ' Physical damage, '
        'healing you for the damage dealt.',
        Speed=_FANG_SPEED, SpellVisualID_1=_SV_FERAL_CHARGE, StartRecoveryCategory=0, StartRecoveryTime=0,
        AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)
scripted_by(taragamans_fang_213500, 'spell_rfc_taragamans_fang')

# --- Heart of the Starving (trinket, Equip) --------------------------------------------------------------------------

bloodward_213504 = spell(
    id=213504, name='Bloodward', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_BLOODWARD_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, base_points=0,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='a share of the heal that triggered it, set by spell_rfc_heart_of_the_starving '
                                     '(custom base points)')],
    spell_icon_id=_ICON_MARK_OF_BLOOD,
    notes='Ragefire Chasm hard mode, Heart of the Starving: the shield, cast by the healer (triggered) from '
          'spell_rfc_heart_of_the_starving on the healed target with its amount set to the Heart aura\'s share of the '
          'heal. Absorbs all schools for 6 s. No potency: a share of a heal that already had the healer\'s bonuses and '
          'crit (the engine adds none to an absorb), so one spell for every tier. IGNORE_LINE_OF_SIGHT: a bounced heal '
          'may land out of the healer\'s sight. SUPPRESS_CASTER_PROCS. Two healers\' Bloodwards do not stack: a new '
          'one lands only when it absorbs at least what the one on the target has left (the Heart\'s check; a '
          'provisional default, 2026-11-24). Look: stock Divine Aegis SV 10895.',
    raw_overrides=_raw('Absorbs damage for $d.', 'Bloodward: absorbs damage.', spell_level=1,
                       SpellVisualID_1=_SV_DIVINE_AEGIS, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

heart_of_the_starving_213503 = _equip_aura(
    213503, 'Heart of the Starving', School.SHADOW,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=29,
            implicit_target_a=_TARGET_UNIT_CASTER),
     Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=39,
            implicit_target_a=_TARGET_UNIT_CASTER, scale_amount=True)],
    'Your direct heals on anyone below $s1% health (you included) also give them Bloodward, absorbing $s2% of the '
    'heal\'s amount for 6 sec. 20 sec cooldown.',
    _ICON_MARK_OF_BLOOD,
    'Ragefire Chasm hard mode, Heart of the Starving (Taragaman the Hungerer, Starving, trinket), the Equip: a passive '
    'aura with a proc. Effect 1 DUMMY amount 30 (BasePoints 29 + DieSides 1) = the health threshold in percent; effect '
    '2 DUMMY amount 40 = the share of the heal in percent, growing with the tier (scale_amount; the Scarlet Monastery '
    'review m5 precedent). spell_proc: done positive magic and none class spells (0x4400), heal type, hit phase '
    '(direct heals: a heal over time\'s ticks are periodic and would spend the cooldown on a sliver), normal or '
    'critical, 100%, 20 s internal cooldown. spell_rfc_heart_of_the_starving\'s check (run before the cooldown starts) '
    'passes a heal on any living target the heal hits, the healer included, whose health before the heal was below the '
    'threshold (the C4 reading, 2026-11-20); an area heal\'s second low target meets the cooldown. A heal whose '
    'Bloodward would be smaller than what one on the target (any healer\'s) has left is refused and spends nothing '
    '(provisional default, 2026-11-24: two healers\' Bloodwards do not stack). The text types the '
    '6 sec so that Bloodward stays one spell for every tier (no $213504d: the tier copies would copy it).',
    proc_type_mask=_HELPFUL_SPELLS, proc_chance=100,
)
procs_on(heart_of_the_starving_213503, proc_flags=_HELPFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=100.0,
         cooldown_ms=20000)
scripted_by(heart_of_the_starving_213503, 'spell_rfc_heart_of_the_starving')

# --- Felstorm Greatblade (two-hand sword, Equip) ---------------------------------------------------------------------

felstorm_spin_213507 = spell(
    id=213507, name='Felstorm', school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=35.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=_FELSTORM_RADIUS)],
    spell_icon_id=_ICON_WHIRLWIND,
    notes='Ragefire Chasm hard mode, Felstorm Greatblade: one second of the spin, cast by the wearer (triggered by '
          '213506\'s tick). Physical, every enemy within 8 yd of the wearer (TARGET_SRC_CASTER / '
          'TARGET_UNIT_SRC_AREA_ENEMY), in combat or not. DefenseType MELEE (melee crit, armor), '
          'attack power potency 35, T 1.5 s: 105 over the three spins on each '
          'enemy. SUPPRESS_CASTER_PROCS. No look of its own.',
    raw_overrides=_raw('Deals {pot1} Physical damage to enemies within $a1 yd.', spell_level=1,
                       DefenseType=_DMG_CLASS_MELEE, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

felstorm_213506 = spell(
    id=213506, name='Felstorm', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=3000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, base_points=0,
                    amplitude=1000, trigger_spell=felstorm_spin_213507.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_WHIRLWIND,
    notes='Ragefire Chasm hard mode, Felstorm Greatblade: the 3 s Felstorm on the wearer, cast by the wearer '
          '(triggered by 213505). A PERIODIC_TRIGGER_SPELL every 1 s: 213507 at 1, 2 and 3 s. Not a channel: the '
          'wearer keeps fighting. SUPPRESS_CASTER_PROCS. Data only. Look: stock Bladestorm SV 6044 (the boss\'s '
          'Felstorm).',
    raw_overrides=_raw('Spinning: deals ' + pot_text(felstorm_spin_213507) + ' Physical damage every $t1 sec to '
                       'enemies within $213507a1 yd for $d.', 'Felstorm: spinning.',
                       SpellVisualID_1=_SV_BLADESTORM, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

felstorm_greatblade_213505 = _equip_aura(
    213505, 'Felstorm Greatblade', School.NORMAL,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
            trigger_spell=felstorm_213506.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    'Your melee hits have a chance to start a Felstorm, dealing ' + pot_text(felstorm_spin_213507)
    + ' Physical damage every $213506t1 sec for $213506d to enemies within $213507a1 yd.',
    _ICON_WHIRLWIND,
    'Ragefire Chasm hard mode, Felstorm Greatblade (Taragaman the Hungerer, Starving, two-hand sword), the Equip: a '
    'passive PROC_TRIGGER_SPELL aura that casts 213506 on the wearer. spell_proc: done melee auto attacks and '
    'melee-class spells (0x14), damage type, hit phase, normal or critical, 15%, 6 s internal cooldown (an area '
    'payout, twice the Felstorm\'s length). spell_rfc_one_roll_per_cast lets each cast roll once.',
    proc_type_mask=_MELEE_HITS, proc_chance=15,
)
procs_on(felstorm_greatblade_213505, proc_flags=_MELEE_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0,
         cooldown_ms=6000)
scripted_by(felstorm_greatblade_213505, 'spell_rfc_one_roll_per_cast')
