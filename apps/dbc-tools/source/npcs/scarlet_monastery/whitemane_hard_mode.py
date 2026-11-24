"""
Scarlet Monastery build WP-D14H: High Inquisitor Whitemane's hard mode, The Truth (heroic only;
.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.7, s3.5 row D14H, s7 #21 A, #33 A, #16 A;
build spec docs/dungeons/scarlet-monastery-4-cathedral.md "High Inquisitor Fairbanks", "Hard mode: The Truth", HM0-HM5).
WP-D14H owns this file; WP-S0 wrote the stub. The engine side is modules/mod-dungeon-bosses
src/ScarletMonastery/whitemane_hard_mode.cpp (on D14's WhitemaneFight.h hooks and D13's MograineFight.h), the pure rules
WhitemaneHardModeLogic.h. The texts (the vigil Fairbanks 0, the spirit 0-2, Whitemane 6) and the Torch's binding
(gameobject_template 97701: go_sm_torch, its SmartAI rows dropped) are
data/sql/updates/pending_db_world/rev_whitemane_hard_mode_scarlet_monastery.sql.

- 300956 High Inquisitor Fairbanks, at the vigil (HM1): kneels 4 yd beside Whitemane at her vigil once the Torch is
  pulled (the stock Fairbanks 4542 teleports out and is gone for the lockout; he stays the Ashbringer quest NPC),
  passive until the pair is pulled, then fights from where he knelt: Inquisitor's Ward, Curse of Blood, Power Word:
  Shield and Heal (the hard mode casts them through him). Level 60 elite, paladin class, 130k (= 53.2351 x the level 60
  paladin base 2,442, creature_classlevelstats basehp0, live 2026-11-20), the stock Fairbanks's display 2605 (V's
  DISPLAY_FAIRBANKS), stun immune (1972). No loot, no instance bind (no encounter of his own: H's _HEROIC_EXTRA). He
  exists on heroic only: H's heroic copy (130k, _boss) runs there, heroic entry 310487.
- 300957 Highlord Mograine, The Ashbringer: the spirit of Alexandros Mograine (HM2-HM5), a presence over the altar
  platform from Fairbanks's death to the pair's (a map summon of the hard mode): not selectable, not attackable,
  friendly (faction 35), never fights; the father's light and the Verdict are cast "by" him (the registry's owner is the
  pair, so the tank row is the tank's). The specter of Alexandros (V's minted CDI 90804, a copy of Highlord Mograine
  16062's 16139 at alpha 140), his Corrupted Ashbringer (item 22709, set by the script). No heroic template (H's list of
  units without one); Highlord Mograine 16062 stays for the Ashbringer event (section 7 #16 A: both new units are left
  out of its friendly sweep by S0's AshbringerSweeps).

Wave 2: both creatures are declared now (H's `_declared` reads the text, not the gate); only their ScriptNames wait for
BIND_WAVE_2 (their C++ AIs register once kWave2Bound flips: the Crell / Garrison Trainee pattern). The Torch's script is
bound on every wave (it acts as stock until wave 2 binds: TorchAnswerFor).

Spells (kSpellsTheTruth 213190-213239; WhitemaneHardModeLogic.h names the same ids; looks from ._visuals, V's HM_* picks
for the Truth plus WM_PWS / WM_HEAL / WM_KNEEL, every look unconfirmed until seen in game):

  213190  Inquisitor's Terror    HM0 the stock Fairbanks fears everyone within 30 yd of the Secret Door for 5 s (out of
                                 combat: no threat; Psychic Scream's SV 247)
  213191  Teleport               HM0 he leaves (a 3 s look aura, SV 9226; the idle hook reads it as "leaving")
  213192  Teleport               HM0 the vigil Fairbanks appears beside her (and the spirit rises): SV 9226
  213193  Inquisitor's Ward      HM1 the ward's look on the pair (the halving is the script's; Divine Protection
                                 SV 11817)
  213194  Curse of Blood         HM1a 2 s cast, a Curse: 4% of the reference row a second for 12 s (the script's base
                                 point, the tank row on the tank), Physical; Curse of Blood's SV 876
  213195  Curse of Blood         HM1a the red mark while the curse lasts (the lasting state SV 14871; the script moves
                                 it)
  213196  Power Word: Shield     HM1b on the lower of the pair, 10% of its health (the script's base point); purgeable
  213197  Heal                   HM1c 3 s on the lower of the pair, 15% of its health; interruptible
  213198  The Ashbringer         HM2 the spirit's glow (Avenging Wrath's state SV 7880)
  213199  The Father's Light     HM3 the spirit marks the spot (Judgement of Light's SV 5651)
  213200  The Father's Light     HM3 the light's hit (resolve copy, Holy): 45% + Weakened, the tank 25% (no Weakened)
  213201  The Father's Light     HM3 the falling-light pillar (the minted 6 yd pillar SV 90564)
  213202  The Verdict            HM3a the spirit raises the Ashbringer (Fury of the Ashbringer's SV 8618)
  213203  The Verdict            HM3a the blade's swing along the line (a missile look at the line's far end, SV 8618)
  213204  The Verdict            HM3a the line's hit (resolve copy, Holy): 55%, tank included, no Weakened
  213205  The Verdict            HM3a the impact on Renault and Whitemane (Holy Wrath's SV 7160)
  213206  Shame                  HM2 / HM3 Renault kneels in shame (Kneel's SV 14427 with D13's kneel)
  213207  The Ashbringer         HM5 the spirit fades (SV 9226)
  213208-213239 spare.

The father's hits on the pair (4% / 6% of Renault's health, 5% of hers) are script damage on their own maximum health
(SYS SM2: no spell). Heal is the only interruptible cast he must lose (the curse can be kicked too: a reward);
nothing in this slice is a must-play bar. Retired here: Dispel Magic 15090 and the stock values of 8282, 11647 and
12039 on this unit (the stock Fairbanks keeps his own).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    FACTION_SCARLET_CRUSADE,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_FAIRBANKS,
    DISPLAY_SPECTRE_ALEXANDROS,
    HM_CURSE,
    HM_CURSE_MARK,
    HM_FEAR,
    HM_LIGHT,
    HM_LIGHT_PILLAR,
    HM_SPIRIT_GLOW,
    HM_TELEPORT,
    HM_VERDICT,
    HM_VERDICT_IMPACT,
    HM_WARD,
    WM_HEAL,
    WM_KNEEL,
    WM_PWS,
)

_D14H = 'Scarlet Monastery build WP-D14H (Whitemane\'s hard mode, The Truth)'

# --- the creatures ---------------------------------------------------------------------------------------------------

# The vigil Fairbanks's heroic entry (difficulty_entry_1 = its id in source/world/heroic_ids.lock): WP-H's mint table
# names 310487, the last of the 30 kit units. It holds only once every lower kit unit is declared; this file declares
# the last of them, so the run mints exactly 310487 for it (lib/test_scarlet_monastery_heroic.py names the same id).
FAIRBANKS_HEROIC_PLANNED = 310487
FAIRBANKS_HEROIC = FAIRBANKS_HEROIC_PLANNED

VIGIL_FAIRBANKS = 300956
ALEXANDROS_SPIRIT = 300957
FAIRBANKS_SCRIPT = 'npc_sm_vigil_fairbanks'
SPIRIT_SCRIPT = 'npc_sm_alexandros_spirit'

_CLASS_WARRIOR = 1
_CLASS_PALADIN = 2
_CREATURE_TYPE_UNDEAD = 6
_RANK_ELITE = 1
_FACTION_FRIENDLY = 35              # the spirit: friendly to everyone, never in the fight
_LEVEL = 60

# The vigil Fairbanks's health (handoff s3.6: 130k at 5 players; the paladin base at level 60 is 2,442,
# creature_classlevelstats basehp0, live 2026-11-20): 130k = 53.2351 x 2,442.
FAIRBANKS_HEALTH = 130000
_BASE_HP_60_PALADIN = 2442
FAIRBANKS_HEALTH_MODIFIER = round(FAIRBANKS_HEALTH / _BASE_HP_60_PALADIN, 4)


def _heroic_entry(columns: dict, heroic_entry) -> dict:
    """`columns` with difficulty_entry_1 when the heroic entry is known (a declared full row must carry it)."""
    if heroic_entry:
        return {**columns, 'difficulty_entry_1': heroic_entry}
    return columns


vigil_fairbanks_300956 = creature_template(300956, 'High Inquisitor Fairbanks', **_heroic_entry({
    **KIT_CREATURE, 'faction': FACTION_SCARLET_CRUSADE, 'minlevel': _LEVEL, 'maxlevel': _LEVEL, 'rank': _RANK_ELITE,
    'unit_class': _CLASS_PALADIN, 'unit_flags': 0, 'HealthModifier': FAIRBANKS_HEALTH_MODIFIER, 'DamageModifier': 1.0,
    'BaseAttackTime': 2000, 'detection_range': 0.0, 'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'flags_extra': 0,
    'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'AIName': '',
    'ScriptName': FAIRBANKS_SCRIPT if BIND_WAVE_2 else '',
}, FAIRBANKS_HEROIC))
creature_model(300956, display_id=DISPLAY_FAIRBANKS)

alexandros_spirit_300957 = creature_template(300957, 'Highlord Mograine', **{
    **KIT_HELPER, 'subname': 'The Ashbringer', 'faction': _FACTION_FRIENDLY, 'type': _CREATURE_TYPE_UNDEAD,
    'minlevel': _LEVEL, 'maxlevel': _LEVEL, 'rank': 0, 'unit_class': _CLASS_WARRIOR, 'AIName': '',
    'ScriptName': SPIRIT_SCRIPT if BIND_WAVE_2 else '',
})
creature_model(300957, display_id=DISPLAY_SPECTRE_ALEXANDROS)

# --- constants (WhitemaneHardModeLogic.h; lib/test_scarlet_monastery_whitemane_hard_mode.py pins each) ----------------

FEAR_MS = 5000                      # kFearMs
LEAVE_LOOK_MS = 3000                # kLeaveLookMs
CURSE_CAST_MS = 2000                # kCurseCastMs
CURSE_TICK_MS = 1000                # kCurseTickMs
CURSE_MS = 12000                    # kCurseMs
SHIELD_AURA_MS = 30000              # kShieldAuraMs
HEAL_CAST_MS = 3000                 # kHealCastMs
HEAL_PCT = 15                       # kHealPct
CAST_RANGE = 40.0                   # kCastRangeYd
SHAME_MAX_MS = 3000                 # kVerdictKneelMs (the light's 2 s and the Truth's 3 s are set by the script)
SWING_SPEED = 60.0                  # kSwingSpeedYd

_DISPEL_MAGIC = 1
_DISPEL_CURSE = 2
_MECHANIC_FEAR = 5
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_DEST_DEST = 87
_TARGET_FLAG_UNIT = 0x2
_TARGET_FLAG_DEST_LOCATION = 0x40
_SCHOOL_MASK_ALL = 127
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map

_SCRIPT_BP = ('Scarlet Monastery the Truth: a percent of reference health per tick the script sets as the base point '
              '(DungeonKit::RefFlat with Whitemane the owner, the tank row on the tank)')
_SCRIPT_HEAL = 'Scarlet Monastery the Truth: a percent of the target\'s own maximum health (the script\'s base point)'
_SCRIPT_ABSORB = 'Scarlet Monastery the Truth: 10% of the target\'s maximum health (the script\'s base point)'

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock client 2026-11-20)
_ICON_PSYCHIC_SCREAM = 1488         # Psychic Scream 8122
_ICON_GENERIC = 1                   # Teleport Visual Only 41232, Kneel 68442
_ICON_DIVINE_PROTECTION = 73        # Divine Protection 498
_ICON_CURSE_OF_BLOOD = 130          # Curse of Blood 8282
_ICON_SHIELD = 566                  # Power Word: Shield 11647
_ICON_HEAL = 104                    # Heal 12039
_ICON_AVENGING_WRATH = 2168         # Avenging Wrath 31884
_ICON_JUDGEMENT_OF_LIGHT = 205      # Judgement of Light 20271
_ICON_ASHBRINGER = 108              # Fury of the Ashbringer 43225
_ICON_HOLY_WRATH = 548              # Holy Wrath 23979


def _self_aura(spell_id: int, name: str, duration_ms: int, visual: int, icon: int, desc: str, aura_desc: str,
               notes: str, *, school: School = School.HOLY, target: int = TARGET_UNIT_CASTER):
    """A look-only DUMMY aura (the script casts it triggered or puts it on with AddAura): no effect, not dispellable,
    lands through immunities, gone on a map change. `duration_ms` -1: until the script removes it."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF if target == TARGET_UNIT_CASTER else 100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=target)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


def _look_on(spell_id: int, name: str, visual: int, notes: str, *, icon: int) -> object:
    """Visual only, on a target: an instant DUMMY the script casts (triggered) on a unit; DO_NOT_DISPLAY | DO_NOT_LOG.
    Copies a stock or minted visual, never the stock spell."""
    return spell(
        id=spell_id, name=name, school=School.HOLY, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- HM0 the Torch ---------------------------------------------------------------------------------------------------

terror_213190 = spell(
    id=213190, name='Inquisitor\'s Terror', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_FEAR,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=FEAR_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_FEAR, base_points=0,
                    mechanic=_MECHANIC_FEAR, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_PSYCHIC_SCREAM,
    notes=f'{_D14H}, HM0 the trigger: on heroic, the Torch pulled (the Last Stand DONE, Whitemane not pulled: s7 '
          '#21 A), the stock Fairbanks 4542 casts it (triggered) on every player within 30 yd of the Secret Door: 5 s, '
          'an out-of-combat scripted transition (SM1); NO_THREAT, so nobody is put in combat (it engages no one), then '
          'he teleports out. Mechanic Fear, Magic (a fear break or a dispel is fine). Psychic Scream 8122\'s look (SV '
          '247, V\'s HM_FEAR).',
    raw_overrides=kit_raw('Fairbanks drives everyone back in terror.', 'Fleeing in terror.', CastingTimeIndex=1,
                          SpellVisualID_1=HM_FEAR, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

teleport_out_213191 = _self_aura(
    213191, 'Teleport', LEAVE_LOOK_MS, HM_TELEPORT, _ICON_GENERIC, 'Fairbanks teleports away.', 'Leaving.',
    f'{_D14H}, HM0: the stock Fairbanks casts it on himself (triggered) right after his fear; 2 s later the Torch\'s '
    'script despawns him for the lockout (a week\'s respawn). 3 s, so it outlasts the despawn: the idle hook reads it '
    'as "leaving" and never takes him for a respawned Fairbanks. Teleport Visual Only 41232\'s SV 9226 (V\'s '
    'HM_TELEPORT).',
    school=School.ARCANE,
)

teleport_in_213192 = self_visual(
    213192, 'Teleport', HM_TELEPORT,
    f'{_D14H}, HM0 / HM2: the vigil Fairbanks appears kneeling beside Whitemane (the idle hook summons him once the '
    'stock one is gone), and the spirit of Alexandros rises over the altar: SV 9226 (V\'s HM_TELEPORT).',
    icon=_ICON_GENERIC, school=School.ARCANE,
)

# --- HM1 Fairbanks at the vigil --------------------------------------------------------------------------------------

ward_213193 = _self_aura(
    213193, 'Inquisitor\'s Ward', -1, HM_WARD, _ICON_DIVINE_PROTECTION,
    'Fairbanks wards the High Inquisitor and her champion.',
    'Damage taken reduced by 50% while High Inquisitor Fairbanks lives.',
    f'{_D14H}, HM1 Inquisitor\'s Ward: while the vigil Fairbanks lives, Whitemane and Mograine take 50% less damage '
    '(the halving is the script\'s, D14\'s OnDamageTaken hook, so a DUMMY here: the look and the tooltip). Fairbanks '
    'puts it on both (AddAura, kept up every second in phase 1); the Truth (his death) removes it. Not dispellable or '
    'purgeable: killing him is the answer (target priority). Divine Protection\'s SV 11817 (V\'s HM_WARD; the Power '
    'Word: Shield bubble is the pair\'s shield).',
    target=TARGET_UNIT_TARGET_ANY,
)

curse_213194 = spell(
    id=213194, name='Curse of Blood', school=School.NORMAL, dispel=_DISPEL_CURSE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=CURSE_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=CAST_RANGE, duration_ms=CURSE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=0, die_sides=0,
                    amplitude=CURSE_TICK_MS, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_BP)],
    spell_icon_id=_ICON_CURSE_OF_BLOOD,
    notes=f'{_D14H}, HM1a Curse of Blood (the stock 8282 reworked on this unit): from P + 5 s, every 15 s, a 2 s cast '
          'on a random player in his range and sight, the tank included: every second for 12 s 4% of the reference row '
          '(48% if left), Physical, the tank row on the tank (the script\'s base point: DungeonKit::RefFlat with '
          'Whitemane the owner, rule 2). A Curse (Dispel 2): removing it is a reward, on the bots\' dispel list '
          '(priority 2). Interruptible (a reward too; not on the interrupt list). Ignores his modifiers. Curse of '
          'Blood\'s SV 876 (V\'s HM_CURSE); the lasting red mark is 213195.',
    raw_overrides=kit_raw('Curses an enemy, draining its blood.', 'Losing $s1 health every $t1 sec.',
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, Targets=_TARGET_FLAG_UNIT, SpellVisualID_1=HM_CURSE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

curse_mark_213195 = spell(
    id=213195, name='Curse of Blood', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=CURSE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CURSE_OF_BLOOD,
    notes=f'{_D14H}, HM1a: the curse\'s lasting red mark (V: the stock Curse of Blood look is one-shot, its lasting '
          'twin is SV 14871, HM_CURSE_MARK). The script keeps it on a player exactly while 213194 is (it adds it with '
          'the curse\'s time left and takes it off within half a second of a decurse). No effect, not dispellable (the '
          'curse is).',
    raw_overrides=kit_raw('A curse of blood.', 'Cursed: decurse to end it.', instant=True,
                          SpellVisualID_1=HM_CURSE_MARK, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

shield_213196 = spell(
    id=213196, name='Power Word: Shield', school=School.HOLY, dispel=_DISPEL_MAGIC, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=CAST_RANGE,
    duration_ms=SHIELD_AURA_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, base_points=0, die_sides=0,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded=_SCRIPT_ABSORB)],
    spell_icon_id=_ICON_SHIELD,
    notes=f'{_D14H}, HM1b Power Word: Shield (the stock 11647 reworked on this unit): from P + 3 s, every 12 s, the '
          'vigil Fairbanks shields the lower of the pair (percent of health), triggered and instant: absorbs 10% of '
          'its maximum health (the script\'s base point), every school, 30 s or until broken. Magic: on the purge list '
          '(priority 2, a reward). The Power Word: Shield bubble (SV 784, V\'s WM_PWS).',
    raw_overrides=kit_raw('Shields an ally, absorbing damage.', 'Absorbs $s1 damage.', instant=True,
                          InterruptFlags=0, PreventionType=0, SpellVisualID_1=WM_PWS, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

heal_213197 = spell(
    id=213197, name='Heal', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=HEAL_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=CAST_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=HEAL_PCT, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY, potency_excluded=_SCRIPT_HEAL)],
    spell_icon_id=_ICON_HEAL,
    notes=f'{_D14H}, HM1c Heal (the stock 12039 reworked on this unit): from P + 10 s, every 20 s, a 3 s cast on the '
          'lower of the pair (in his range and sight), 15% of its maximum health. Cast for real (the bar shows), '
          'interruptible and silence-preventable (InterruptFlags 15, PreventionType silence; his immunity set 1972 '
          'holds no interrupt or silence): on the interrupt list after Whitemane\'s heroic Heal, before Holy Smite '
          '(priority 3, a reward). Heal 12039\'s SV 135 (V\'s WM_HEAL).',
    raw_overrides=kit_raw('Heals an ally.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC, Targets=_TARGET_FLAG_UNIT,
                          SpellVisualID_1=WM_HEAL, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- HM2 the Truth, HM3 the father's judgment, HM5 the ending -------------------------------------------------------

spirit_glow_213198 = _self_aura(
    213198, 'The Ashbringer', -1, HM_SPIRIT_GLOW, _ICON_AVENGING_WRATH, 'The Ashbringer\'s light.',
    'The spirit of Alexandros Mograine.',
    f'{_D14H}, HM2: the spirit of Alexandros Mograine glows over the altar from his rising (Fairbanks\'s death) to the '
    'pair\'s death (cast on himself, triggered): Avenging Wrath 31884\'s state SV 7880 (V\'s HM_SPIRIT_GLOW). No '
    'effect.',
)

light_cast_213199 = self_visual(
    213199, 'The Father\'s Light', HM_LIGHT,
    f'{_D14H}, HM3: the spirit marks the light (the 6 yd circle at a random player\'s spot): Judgement of Light '
    '20271\'s SV 5651 (V\'s HM_LIGHT). Look only; the circle is the registry\'s marker.',
    icon=_ICON_JUDGEMENT_OF_LIGHT, school=School.HOLY,
)

light_hit_213200 = resolve_copy(
    213200, 'The Father\'s Light', School.HOLY, 'The Ashbringer\'s light falls.',
    f'{_D14H}, HM3 the light (two casts in three, every 8 s from T + 8 s): a 6 yd circle at a random player\'s spot, '
    'the tank included, 2.5 s marker; two registry circles on one spot, owned by Mograine while he stands (else '
    'Whitemane): the non-tanks take 45% of the reference row and 1 Weakened (tag 21); the tank 25% and no Weakened '
    '(tag 22, not drawn twice, `.Park(Mograine)`: the tank holds Renault in it). Renault in it: 4% of his health and a '
    '2 s kneel (the script). Copy of the resolve spell 205002 (Holy).',
    icon=_ICON_JUDGEMENT_OF_LIGHT,
)

light_pillar_213201 = _look_on(
    213201, 'The Father\'s Light', HM_LIGHT_PILLAR,
    f'{_D14H}, HM3: the falling-light pillar as the light lands, on a wave 2 stalker at the spot (300958, once its '
    'template exists) or else on each player inside: the minted 6 yd holy pillar SV 90564 (V\'s HM_LIGHT_PILLAR; never '
    'the stock Beam of Light SV 12479).',
    icon=_ICON_JUDGEMENT_OF_LIGHT,
)

verdict_raise_213202 = self_visual(
    213202, 'The Verdict', HM_VERDICT,
    f'{_D14H}, HM3a: the spirit raises the Ashbringer as the Verdict\'s 3.5 s marker appears (with his raid emote line '
    '2): Fury of the Ashbringer 43225\'s SV 8618 (V\'s HM_VERDICT; never the empty wielder aura SV 7582).',
    icon=_ICON_ASHBRINGER, school=School.HOLY,
)

verdict_swing_213203 = spell(
    id=213203, name='The Verdict', school=School.HOLY, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=150.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_ASHBRINGER,
    notes=f'{_D14H}, HM3a: the swing, a no-effect missile the spirit casts (triggered) at the line\'s far end, '
          'launched so the flying blade crosses the line as it lands (WhitemaneHardModeLogic.h SwingLeadMs: Speed 60 '
          'yd/s = kSwingSpeedYd). Fury of the Ashbringer 43225\'s flying Ashbringer (SV 8618, V\'s HM_VERDICT).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=HM_VERDICT, Speed=SWING_SPEED,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

verdict_hit_213204 = resolve_copy(
    213204, 'The Verdict', School.HOLY, 'The Ashbringer passes judgment.',
    f'{_D14H}, HM3a the Verdict (every third cast, every 24 s; ruling 52): a 6 yd line from the spirit through Renault '
    'to the floor\'s far edge (the nave\'s west wall about 94 yd off, an arm about 60 yd: s7 #33 A), fixed as the '
    '3.5 s marker appears, Renault held for it (D13\'s HoldControl): 55% of the reference row, the tank included (the '
    'tank row), no Weakened (50% or more). Renault on it 6% of his health and a 3 s kneel; Whitemane on it 5% of hers '
    'and her cast breaks (a save channel starts over). Registry tag 23, owned by Mograine while he stands. Copy of the '
    'resolve spell 205002 (Holy).',
    icon=_ICON_ASHBRINGER,
)

verdict_impact_213205 = _look_on(
    213205, 'The Verdict', HM_VERDICT_IMPACT,
    f'{_D14H}, HM3a: the Verdict lands on Renault or Whitemane (the spirit casts it on each it struck): Holy Wrath '
    '23979\'s SV 7160 (V\'s HM_VERDICT_IMPACT).',
    icon=_ICON_HOLY_WRATH,
)

shame_213206 = _self_aura(
    213206, 'Shame', SHAME_MAX_MS, WM_KNEEL, _ICON_GENERIC, 'Kneels in shame.', 'Kneeling in shame before his father.',
    f'{_D14H}, HM2 / HM3: Renault kneels in shame (the Truth 3 s, the light 2 s, the Verdict 3 s): D13\'s Kneel stops '
    'his attacks and his kit; this aura is its look and its clock on him (AddAura, the script sets 2 s or 3 s): '
    'Kneel 68442\'s SV 14427 (V\'s WM_KNEEL / HM_KNEEL). No effect, not dispellable.',
    school=School.NORMAL,
)

spirit_fade_213207 = self_visual(
    213207, 'The Ashbringer', HM_TELEPORT,
    f'{_D14H}, HM5 the ending: when the pair dies the spirit says "You are forgiven..." and fades (cast on himself, '
    'then despawned 4 s later): SV 9226 (V\'s HM_TELEPORT).',
    icon=_ICON_AVENGING_WRATH, school=School.HOLY,
)
