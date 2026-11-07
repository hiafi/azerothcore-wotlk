"""
The Shadowfang Keep item effects (item variants, wave 1): the three Archmage Arugal hard mode items (designer text:
docs/dungeons/shadowfang-keep-rework.md "Hard mode bonus list: Archmage Arugal, Face Him Alone", copied in
docs/dungeons/dungeon-loot-vanilla.md) and the Meteor Shard's kept "Chance on hit: Firebolt", rebuilt on potency.

Every damage number comes from potency (docs/potency-system.md; user rule: everything on potency, no hand coefficients
and no hand spell_bonus_data). The 71 tier of a hard mode item carries the spells declared here; every higher tier of
a `scale="budget"` item carries its own copies (stage IV10, lib/item_spell_copies.py, ids in item_spell_ids.lock).
The scripts are modules/mod-dungeon-bosses src/ShadowfangKeep/hard_mode_items.cpp (ids mirrored in
SfkHardModeItemsLogic.h). The Tome's look-alike Voidwalker is creature 300460
(source/npcs/shadowfang_keep/hard_mode_items.py; the `shadowfang_items` creature slice 300460-300464).

Ids: the `shadowfang_items` reservation 205600-205619 (source/ids.yaml).

  205600  Vial of the Worgen's Curse  Use (2 min, off the GCD): 15 sec self buff, Haste rating and +30% movement
                                      speed. Pure data. The Haste rating is the 71 tier's; the per-tier copies scale it
                                      by the tier's stat budget (a stat aura), the speed stays (a percentage).
  205601  Arugal's Shadow Tome        Equip: a passive proc aura. Direct damaging spells that land (magic class) have a
                                      10% chance, 30 sec internal cooldown, to fire spell_sfk_arugals_shadow_tome: a
                                      Voidwalker (300460) appears at the target and the wearer's triggered 205602 lands.
  205602  Arugal's Voidwalker         the Voidwalker's attacks: a 10 sec Shadow damage over time on the target, a tick
                                      every 2 sec, spell power potency (cast by the wearer, triggered). Its aura script
                                      spell_sfk_arugals_voidwalker makes the Voidwalker swing on every tick and sends it
                                      away when the debuff ends.
  205603  Ashcrombe's Locket          Use (2 min, off the GCD): removes every Curse from a friendly target within
                                      40 yd and makes it immune to Curses for 6 sec. Pure data. The Worgen's Curse is
                                      never a Curse (DispelType 0, shadowfang-keep-rework.md Arugal), so the ward never
                                      touches it.
  205604  Firebolt                    the Meteor Shard's Chance on hit (2 procs per minute, the stock rate): a Fire
                                      bolt, attack power potency. Replaces stock Firebolt 13442 (35 flat damage).
  205605-205619  spare

Proc chances, internal cooldowns, potencies, the Haste rating and the looks are proposals waiting for the designer
(STAGE-W1-SFK report, designer questions). None of the looks were checked in game.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import pot_text, procs_on, scripted_by, spell

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}

_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_TARGET_ALLY = 21

_ATTR0_PASSIVE = 0x00000040
_ATTR1_IMMUNITY_PURGES_EFFECT = 0x00008000  # applying the immunity removes every Curse already on the target

_DMG_CLASS_MAGIC = 1

_AURA_DISPEL_IMMUNITY = 41  # SPELL_AURA_DISPEL_IMMUNITY (not in lib.dsl.AuraType)
_DISPEL_CURSE = 2           # DispelType DISPEL_CURSE
_CURSES_REMOVED = 10        # "all Curse effects": the dispel effect takes up to 10 (BasePoints 9 + DieSides 1); the
                            # purging immunity removes any left over
# CombatRating mask CR_HASTE_MELEE | CR_HASTE_RANGED | CR_HASTE_SPELL (1 << 17 | 1 << 18 | 1 << 19), the stock haste
# rating auras' value (Kiss of the Spider 28866, Haste 13494).
_HASTE_RATING_MASK = 917504

# spell_proc (SpellMgr.h)
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL_OR_CRITICAL = 0x1 | 0x2

# Stock looks (none checked in game yet).
_SV_ARUGALS_CURSE = 760        # Arugal's Curse 7621: the worgen curse taking hold
_SV_REMOVE_CURSE = 186         # Remove Curse 475 / 2782
_SV_SHADOW_BOLT_IMPACT = 758   # Void Bolt 7588 (Arugal's own)
_SV_FIREBOLT = 28              # Firebolt 13442, the stock Meteor Shard proc
_ICON_ARUGALS_CURSE = 173      # Arugal's Curse 7621
_ICON_REMOVE_CURSE = 195       # Remove Curse 475
_ICON_VOID_BOLT = 213          # Void Bolt 7588
_ICON_FIREBOLT = 183           # Firebolt 13442

_VIAL_HASTE_RATING = 80        # at level 60, 10 rating = 1% haste: +8% for 15 sec (proposal)
_VIAL_SPEED_PCT = 30
_VOIDWALKER_TICK_MS = 2000
_FIREBOLT_SPEED = 19.0         # the stock Firebolt missile's


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


# --- Vial of the Worgen's Curse (trinket, Use) -----------------------------------------------------------------------

vial_of_the_worgens_curse_205600 = spell(
    id=205600, name="Vial of the Worgen's Curse", school=School.SHADOW, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_RATING, base_points=_VIAL_HASTE_RATING - 1,
               misc_value=_HASTE_RATING_MASK, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_INCREASE_SPEED, base_points=_VIAL_SPEED_PCT - 1,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_ARUGALS_CURSE,
    notes='Shadowfang Keep hard mode (Archmage Arugal, Face Him Alone) trinket, the Use: 2 min cooldown, off the GCD '
          '(StartRecoveryCategory 0), a visible 15 s self buff: Haste rating (MOD_RATING, the stock melee + ranged + '
          'spell haste mask 917504) and +30% movement speed (MOD_INCREASE_SPEED, does not stack with other speed '
          'buffs of that aura). The designer text says the Haste rating scales with the item level: the per-tier '
          'copies scale MOD_RATING amounts by the tier\'s stat budget (wave 1 integration), the speed percentage '
          'stays. Look: stock Arugal\'s Curse SV 760.',
    raw_overrides=_raw(
        'Increases your haste rating by $s1 and your movement speed by $s2% for $d.',
        'Haste rating and movement speed increased.',
        SpellVisualID_1=_SV_ARUGALS_CURSE, StartRecoveryCategory=0, StartRecoveryTime=0,
    ),
)

# --- Arugal's Shadow Tome (held in off-hand, Equip) ------------------------------------------------------------------

arugals_voidwalker_205602 = spell(
    id=205602, name="Arugal's Voidwalker", school=School.SHADOW, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, sp_potency=30.0,
                    potency_kind='periodic', amplitude=_VOIDWALKER_TICK_MS,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_VOID_BOLT,
    notes='Shadowfang Keep hard mode, Arugal\'s Shadow Tome: the Voidwalker\'s attacks, a 10 s Shadow damage over '
          'time on the target (a tick every 2 s, 5 ticks), spell power potency 30 per tick. Cast by the wearer '
          '(triggered by the Tome\'s aura, so it procs nothing) right after spell_sfk_arugals_shadow_tome summons '
          'the look-alike Voidwalker 300460; the wearer deals the damage so it uses the wearer\'s level, spell power '
          'and crit, as potency expects. spell_sfk_arugals_voidwalker swings the Voidwalker on every tick and sends '
          'it away when the debuff ends (the target died, the debuff ran out). DefenseType MAGIC, DispelType none. '
          'Look: stock Void Bolt SV 758 on the target.',
    raw_overrides=_raw('Deals {pot1.total} Shadow damage over $d.', 'Attacked by a Voidwalker.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_SHADOW_BOLT_IMPACT),
)

arugals_shadow_tome_205601 = spell(
    id=205601, name="Arugal's Shadow Tome", school=School.SHADOW, attributes=_ATTR0_PASSIVE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_VOID_BOLT,
    notes='Shadowfang Keep hard mode (Archmage Arugal, Face Him Alone) held-in-off-hand, the Equip: a passive DUMMY '
          'aura with a proc. spell_proc: done harmful magic-class spells (0x10000), damage type, hit phase, normal '
          'or critical hits only (so a damage over time\'s ticks never count: they are periodic events), 10% '
          'chance, 30 s internal cooldown (longer than the Voidwalker\'s 10 s, so one is out at a time). '
          'spell_sfk_arugals_shadow_tome summons the Voidwalker 300460 at the target and casts 205602. Item auras get '
          'no Proc Chance (Systems.md section 5).',
    raw_overrides=_raw(
        "Your damaging spells have a chance to call an Arugal's Voidwalker for $205602d, which attacks your target "
        'for ' + pot_text(arugals_voidwalker_205602, variant='total') + ' Shadow damage over that time.',
        ProcTypeMask=_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, ProcChance=10,
    ),
)
procs_on(arugals_shadow_tome_205601, proc_flags=_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG,
         spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=10.0, cooldown_ms=30000)
scripted_by(arugals_shadow_tome_205601, 'spell_sfk_arugals_shadow_tome')
scripted_by(arugals_voidwalker_205602, 'spell_sfk_arugals_voidwalker')

# --- Ashcrombe's Locket (neck, Use) ----------------------------------------------------------------------------------

ashcrombes_locket_205603 = spell(
    id=205603, name="Ashcrombe's Locket", school=School.ARCANE, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=6000,
    effects=[
        Effect(type=EffectType.DISPEL, base_points=_CURSES_REMOVED - 1, misc_value=_DISPEL_CURSE,
               implicit_target_a=_TARGET_UNIT_TARGET_ALLY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_DISPEL_IMMUNITY, misc_value=_DISPEL_CURSE,
               implicit_target_a=_TARGET_UNIT_TARGET_ALLY),
    ],
    spell_icon_id=_ICON_REMOVE_CURSE,
    notes='Shadowfang Keep hard mode (Archmage Arugal, Face Him Alone) neck, the Use: 2 min cooldown, off the GCD, a '
          'friendly target within 40 yd. Effect 1 dispels up to 10 Curses (DISPEL, DISPEL_CURSE); effect 2 is a '
          'visible 6 s Curse immunity (SPELL_AURA_DISPEL_IMMUNITY, the Glyph of Remove Curse 60803 shape) whose '
          'IMMUNITY_PURGES_EFFECT (AttributesEx 0x8000) also strips any Curse the dispel left. The Worgen\'s Curse is '
          'never a Curse (DispelType 0), so it is neither removed nor blocked: Arugal\'s build must keep it that way. '
          'No damage or healing, so no per-tier copies. Look: stock Remove Curse SV 186.',
    raw_overrides=_raw(
        'Removes all Curse effects from a friendly target and wards it against new Curses for $d. Cannot remove the '
        "Worgen's Curse.",
        'Immune to Curses.',
        AttributesEx=_ATTR1_IMMUNITY_PURGES_EFFECT, SpellVisualID_1=_SV_REMOVE_CURSE, StartRecoveryCategory=0,
        StartRecoveryTime=0,
    ),
)

# --- Meteor Shard (dagger, Chance on hit) ----------------------------------------------------------------------------

meteor_shard_firebolt_205604 = spell(
    id=205604, name='Firebolt', school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=30.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=60.0, potency_kind='direct', time_basis_ms=1500,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FIREBOLT,
    notes='Shadowfang Keep, Meteor Shard (Archmage Arugal, the kept "Chance on hit: Firebolt"): stock Firebolt 13442 '
          'dealt a flat 35 Fire damage, so it is rebuilt on potency here. Fire, DefenseType MAGIC, attack power '
          'potency 60 (an Agility dagger), T 1.5 s (an off-GCD payout). A missile (Speed 19, the stock bolt). The '
          'item rolls it at the stock 2 procs per minute (hit_spell ppm). scale="budget": 60 is the Heroic (66) '
          'number, the vanilla dungeon ladder\'s effect reference; the Normal tier (level 29 Rare) gets a copy '
          'scaled down by its stat budget, the empowered tiers copies scaled up (wave 1 integration). Look: stock '
          'SV 28.',
    raw_overrides=_raw('Blasts a target for {pot1} Fire damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       Speed=_FIREBOLT_SPEED, SpellVisualID_1=_SV_FIREBOLT),
)
