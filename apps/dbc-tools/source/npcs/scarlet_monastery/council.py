"""
Scarlet Monastery build WP-D3: Azshir the Sleepless and the Fallen Champion (the council), "The Last Vigil", normal and
heroic (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D3, s3.6, s3.8 row D3,
s7 #18 A; build spec docs/dungeons/scarlet-monastery-1-graveyard.md "Azshir and the Fallen Champion rework", CV1-CV8).
WP-D3 owns this file (its spells: kSpellsCouncil 212390-212439 of modules/mod-dungeon-bosses
src/ScarletMonastery/ScarletMonasteryRework.h only; CouncilLogic.h names the same ids).

- 6488 the Fallen Champion: boss_fallen_champion_rework (SmartAI off: WP-S0's rev dropped his rows and the 90% despawn
  roll; his Cleave 19642, Strike 19644 and Rend 21949 are retired), class warrior -> paladin (unit_class 2, the base
  888 at level 32, and a mana bar), 24k = HealthModifier 27.027 on 888, DamageModifier 2.4 (the stock base value; the
  live 4.0 is a mod-progression leftover), stun immunity 1972, no INSTANCE_BIND (the instance credits the pair by
  spell 212300 once both are dead; _common.py NO_INSTANCE_BIND). Heroic 170k is WP-H's override.
- 6490 Azshir the Sleepless: boss_azshir_the_sleepless_rework (his Terrify 7399, Soul Siphon 9373 and Call of the
  Grave 5137 as a cast are retired), 18k = HealthModifier 20.27 on the paladin 888, DamageModifier 7.5 (stock; he never
  melees), 1972, no INSTANCE_BIND. Heroic 130k is WP-H's. Both spawns move to the lawn in
  rev_council_scarlet_monastery.sql (section 7 #18 A).
- No creature or object of its own.

Spells. The registry's hits are dungeon copies of the mod-boss-mechanics resolve spell (the registry's percent of the
reference row); the hits the script aims itself (Holy Shock, Judgement, the Justice shares, the shield's hits, the
Execution Sentence burst) are plain SCHOOL_DAMAGE spells whose amount is the script's base point
(DungeonKit::RefFlatOn, the tank row on the tank, times Grief on the Champion's). The rest are the bars, the seals and
the debuffs:

  212390  Holy Shock           CV2 Azshir's instant hit, 12% / 18% Holy (Holy Shock 25914's SV 135)
  212391  Holy Light           CV3 2.5 s, interruptible, heals the brother for 10% / 25% of his health (SV 2936)
  212392  Holy Wrath           CV4 the 2 s bar (Physical: a Holy Light kick never locks it)
  212393  Holy Wrath           CV4 the ring's hit (resolve copy, Holy), 35% / 45% + Weakened (SV 126)
  212394  Holy Wrath           CV4 on the Champion inside the ring: 5% of his health (script) + a 2 s pacify
  212395  Exorcism             CV5 the 2 s bar
  212396  Exorcism             CV5 the line's hit (resolve copy, Holy), 35% / 45% + Weakened (SV 324)
  212397  Judgement            CV6a the tank hit, 25% / 35% of tank health, Holy (Judgement of Light's SV 5651)
  212398  Seal of Command      CV6b the held seal (minted STATE SV 90555)
  212399  Seal of Command      CV6b the frontal cleave's hit (resolve copy, Physical), 30% / 45% + Weakened
  212400  Seal of Righteousness  CV6c the held seal (SV 90556)
  212401  Righteous Brand      CV6c the 5 s brand on a carrier (SV 7986)
  212402  Righteous Brand      CV6c the burst's hit (resolve copy, Holy), 35% / 45% + Weakened (SV 5600)
  212403  Seal of Justice      CV6d the held seal (SV 90557)
  212404  Hammer of Justice    CV6d the 5 s mark: the falling hammer over the target (shipped SV 90044)
  212405  Hammer of Justice    CV6d a share of the split (150% / 250%, script), Holy (SV 322)
  212406  Avenger's Shield     CV7 the 2 s bar
  212407  Avenger's Shield     CV7 the first hit (script) + a 2 s silence (SV 7886)
  212408  Avenger's Shield     CV7 a bounce's hit (script; Weakened by the script)
  212409  The Last Vigil       CV1 Azshir's 8 s channel (not interruptible; Penance's SV 10980)
  212410  The Last Vigil       CV1 the ring under the fallen Champion (shipped holy zone SV 90510, 5 yd)
  212411  The Last Vigil       CV1 the rise (Scarlet Resurrection's SV 1443)
  212412  Grief                CV1 +20% damage done and attack speed a stack (SV 6943)
  212413  Execution Sentence   CV8 heroic: the heal absorb, aura 301, every school (MiscValue 127), 8 s (SV 90044)
  212414  Execution Sentence   CV8 the room burst's hit (script), Holy (SV 90045)
  212415  Execution Sentence   CV8 the room wave on Azshir (Holy Nova's SV 3643)
  212416-212439 spare.

Holy Light is the only interruptible cast of the slice. Every bar Azshir must play (Holy Wrath, Exorcism) is
Physical, so a kick on Holy Light (Holy) never locks it (handoff s3.5 rule 5); his instant Holy Shock and the triggered
hits ignore the lockout. Visual ids are WP-V's (._visuals). Every look is unconfirmed until seen in game. Tooltips are
number-free where the number is a reference percent.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, ATTR2_CANT_CRIT, ATTR2_IGNORE_LINE_OF_SIGHT, ATTR3_ALWAYS_HIT
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    CV_AVENGERS_SHIELD,
    CV_EXECUTION_SENTENCE,
    CV_EXECUTION_SENTENCE_BURST,
    CV_EXORCISM,
    CV_GRIEF,
    CV_HOLY_LIGHT,
    CV_HOLY_SHOCK,
    CV_HOLY_WRATH,
    CV_JUDGEMENT,
    CV_JUSTICE_HAMMER,
    CV_JUSTICE_MARK,
    CV_RIGHTEOUSNESS_BURST,
    CV_ROOM_WAVE,
    CV_SEAL_COMMAND,
    CV_SEAL_RIGHTEOUSNESS,
    CV_VIGIL_CHANNEL,
    CV_VIGIL_RING,
    CV_VIGIL_RISE,
    SV_SEAL_COMMAND,
    SV_SEAL_JUSTICE,
    SV_SEAL_RIGHTEOUSNESS,
)

creature_template_columns(6488, **boss_columns(
    'boss_fallen_champion_rework', 27.027, damage_modifier=2.4, instance_bind=False, unit_class=2,
))
creature_template_columns(6490, **boss_columns(
    'boss_azshir_the_sleepless_rework', 20.27, damage_modifier=7.5, instance_bind=False,
))

_SD = 'Scarlet Monastery build WP-D3 (the council: Azshir the Sleepless and the Fallen Champion)'

_SCRIPT_BP = ('Scarlet Monastery council: a percent of reference health the script sets as the base point '
              '(DungeonKit::RefFlatOn, the tank row on the tank)')
_SCRIPT_BURN = 'Scarlet Monastery council: 5% of the Champion\'s own maximum health, dealt by the spell script'
_SCRIPT_HEAL = 'Scarlet Monastery council: a percent of the target\'s own maximum health (the script\'s base point)'
_SCRIPT_ABSORB = ('Scarlet Monastery council: 75% of the reference row (the tank row on the tank), set at application '
                  'by spell_sm_council_execution_sentence')

# Stock icons (Spell.dbc SpellIconID of the named spell; Execution Sentence is the Retribution rework's custom icon).
_ICON_HOLY_SHOCK = 156              # Holy Shock 25914
_ICON_HOLY_LIGHT = 70               # Holy Light 13952
_ICON_HOLY_WRATH = 158              # Holy Wrath 52836
_ICON_EXORCISM = 292                # Exorcism 17147
_ICON_JUDGEMENT = 205               # Judgement of Light 20271
_ICON_SEAL_OF_COMMAND = 561         # Seal of Command 57769
_ICON_SEAL_OF_RIGHTEOUSNESS = 25    # Seal of Righteousness 20154
_ICON_SEAL_OF_JUSTICE = 307         # Seal of Justice 20164
_ICON_HAMMER_OF_JUSTICE = 302       # Hammer of Justice 13005
_ICON_AVENGERS_SHIELD = 2172        # Avenger's Shield 31935
_ICON_PENANCE = 2818                # Penance 47540
_ICON_REDEMPTION = 121              # Redemption 7328
_ICON_BLOODLUST = 38                # Bloodlust 2825
_ICON_EXECUTION_SENTENCE = 90212    # the Retribution rework's Execution Sentence (source/classes/paladin)
_ICON_HOLY_NOVA = 1874              # Holy Nova 15237

_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_FLAG_UNIT = 0x2
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15
_ATTR1_IS_CHANNELED = 0x00000004
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_MECHANIC_SILENCE = 9
_SCHOOL_MASK_ALL = 127
_AURA_SCHOOL_HEAL_ABSORB = 301              # SpellAuraDefines.h SPELL_AURA_SCHOOL_HEAL_ABSORB (Unit::CalcHealAbsorb)

# CouncilLogic.h (lib/test_scarlet_monastery_council.py pins each against the header).
HOLY_LIGHT_CAST_MS = 2500           # kHolyLightCastMs
HOLY_LIGHT_HEAL_PCT = 10            # kHolyLightHealPct normal (heroic 25 through the script's base point)
HOLY_WRATH_CAST_MS = 2000           # kHolyWrathCastMs
EXORCISM_CAST_MS = 2000             # kExorcismCastMs
SHIELD_CAST_MS = 2000               # kShieldCastMs
SHIELD_SILENCE_MS = 2000            # kShieldSilenceMs
PACIFY_MS = 2000                    # kPacifyMs
BRAND_MS = 5000                     # kBrandMs
JUSTICE_MARK_MS = 5000              # kJusticeMarkMs
VIGIL_CHANNEL_MS = 8000             # kVigilChannelMs
VIGIL_RING_MS = 9000                # kVigilRingMs
EXECUTION_MS = 8000                 # kExecutionMs
GRIEF_PCT = 20                      # kGriefPctPerStack
GRIEF_STACKS = 255                  # the aura's ceiling; the script caps normal at 5 (kGriefMaxStacks)


def _script_hit(spell_id: int, name: str, desc: str, notes: str, *, icon: int, visual: int,
                more_effects: tuple[Effect, ...] = (), duration_ms: int = 0, aura_desc: str = '') -> object:
    """A Holy hit whose amount the script sets as the base point (CastSpellExtraArgs::AddSpellBP0): triggered, always
    hits, cannot crit, ignores LoS and the caster's modifiers (Grief is multiplied in by the script), DmgClass magic."""
    return spell(
        id=spell_id, name=name, school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_BP), *more_effects],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, InterruptFlags=0, PreventionType=0,
                              DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP
                              if more_effects else 0),
    )


def _held_seal(spell_id: int, name: str, visual: int, desc: str, notes: str, *, icon: int) -> object:
    """A seal the Champion holds (cast on himself, triggered; removed by the script at the next seal): a DUMMY buff
    with its lasting glow, not dispellable."""
    return spell(
        id=spell_id, name=name, school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, desc, instant=True, InterruptFlags=0, PreventionType=0, SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _debuff(spell_id: int, name: str, duration_ms: int, visual: int, desc: str, aura_desc: str, notes: str, *,
            icon: int) -> object:
    """A 5 s marker on a player (the Champion puts it on with AddAura): a DUMMY debuff, not dispellable, lands
    through immunities, gone on a map change."""
    return spell(
        id=spell_id, name=name, school=School.HOLY, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


# --- Azshir: CV2 Holy Shock, CV3 Holy Light ---------------------------------------------------------------------------

holy_shock_212390 = _script_hit(
    212390, 'Holy Shock', 'Azshir blasts a foe with holy energy.',
    f'{_SD}, CV2: Azshir\'s instant hit (healer work), first at 4 s, then every 7 s, on a random player, the tank '
    'included: 12% (heroic 18%) of the reference row, the tank on its own row (the script\'s base point). Triggered, '
    'so a Holy Light kick\'s lockout does not stop it. Holy Shock 25914\'s SV 135.',
    icon=_ICON_HOLY_SHOCK, visual=CV_HOLY_SHOCK,
)

holy_light_212391 = spell(
    id=212391, name='Holy Light', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=HOLY_LIGHT_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=HOLY_LIGHT_HEAL_PCT - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY, potency_excluded=_SCRIPT_HEAL)],
    spell_icon_id=_ICON_HOLY_LIGHT,
    notes=f'{_SD}, CV3: Azshir\'s heal, first at 18 s, then every 18 s, on the brother with the lower percent of '
          'health (never the Champion while he lies fallen): 10% (heroic 25%, the script\'s base point) of the '
          'target\'s own maximum health. Cast for real (not triggered: the bar shows), 2.5 s, 40 yd, interruptible and '
          'silence-preventable (InterruptFlags 15, PreventionType silence; his immunity set 1972 holds no interrupt '
          'or silence): the descriptor\'s interrupt list, priority 2 normal (a reward), 3 heroic (expected). Holy '
          'Light 13952\'s SV 2936.',
    raw_overrides=kit_raw('Heals a brother of the vigil.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC, Targets=_TARGET_FLAG_UNIT,
                          SpellVisualID_1=CV_HOLY_LIGHT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- Azshir: CV4 Holy Wrath -------------------------------------------------------------------------------------------

holy_wrath_cast_212392 = cast_bar(
    212392, 'Holy Wrath', HOLY_WRATH_CAST_MS, 'Azshir calls down holy wrath around him.',
    f'{_SD}, CV4: the 2 s bar before the ring, first at 14 s, then every 16 s. DUMMY on the caster, not '
    'interruptible, PHYSICAL on purpose: a kick on Holy Light (Holy) locks the school, and a Holy bar of his would '
    'stop then (handoff s3.5 rule 5). The registry\'s 10 yd circle on him owns the hit (212393). Holy Wrath 52836\'s '
    'SV 126 (the cast glow).',
    icon=_ICON_HOLY_WRATH, visual=CV_HOLY_WRATH,
)

holy_wrath_212393 = resolve_copy(
    212393, 'Holy Wrath', School.HOLY, 'Holy wrath burns everything near Azshir.',
    f'{_SD}, CV4: the ring\'s hit: 35% (heroic 45%) of the reference row to every player within 10 yd of Azshir, the '
    'tank on its own row, 1 Weakened. Copy of the mod-boss-mechanics resolve spell (Holy). Holy Wrath 52836\'s SV 126 '
    'on every unit hit.',
    icon=_ICON_HOLY_WRATH, visual=CV_HOLY_WRATH,
)

holy_wrath_burn_212394 = spell(
    id=212394, name='Holy Wrath', school=School.HOLY, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=PACIFY_MS,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_BURN),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_PACIFY,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HOLY_WRATH,
    notes=f'{_SD}, CV4: the Champion is undead: standing inside Azshir\'s ring at its resolve, he burns too (the '
          'tank\'s parking reward, Scholomance addition 7). Azshir casts it on him (triggered): the DUMMY deals '
          'exactly 5% of his maximum health (spell_sm_council_holy_wrath_burn, never lethal: his fall is the Last '
          'Vigil\'s) and a 2 s pacify (MOD_PACIFY, mechanic none: a scripted pacify, not a stun, so his stun '
          'immunity 1972 stays and nothing blocks it); his AI also holds his seals, Judgement and shield while '
          'pacified. Holy Wrath 52836\'s SV 126 (its stun swirl state shows the pacify).',
    raw_overrides=kit_raw('', 'Pacified by holy wrath.', instant=True, InterruptFlags=0, PreventionType=0,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=CV_HOLY_WRATH, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(holy_wrath_burn_212394, 'spell_sm_council_holy_wrath_burn')

# --- Azshir: CV5 Exorcism ---------------------------------------------------------------------------------------------

exorcism_cast_212395 = cast_bar(
    212395, 'Exorcism', EXORCISM_CAST_MS, 'Azshir gathers holy fire.',
    f'{_SD}, CV5: the 2 s bar before the line, first at 8 s, then every 12 s. DUMMY on the caster, not '
    'interruptible, Physical (rule 5, as Holy Wrath\'s). The registry\'s line owns the hit (212396). Exorcism '
    '17147\'s SV 324.',
    icon=_ICON_EXORCISM, visual=CV_EXORCISM,
)

exorcism_212396 = resolve_copy(
    212396, 'Exorcism', School.HOLY, 'Holy fire sears everything in its line.',
    f'{_SD}, CV5: the line\'s hit: a 4 yd wide, 40 yd line from Azshir through a random player\'s spot at the cast '
    'start (the tank included; normal never the player marked by Justice, heroic through the stack too), 35% (heroic '
    '45%) of the reference row, the tank on its own row, 1 Weakened. Copy of the mod-boss-mechanics resolve spell '
    '(Holy). Exorcism 17147\'s SV 324 on every unit hit.',
    icon=_ICON_EXORCISM, visual=CV_EXORCISM,
)

# --- the Champion: CV6a Judgement, CV6b-d the seals -------------------------------------------------------------------

judgement_212397 = _script_hit(
    212397, 'Judgement', 'The Fallen Champion judges his foe.',
    f'{_SD}, CV6a: the tank hit (tank and healer work), first at 10 s, then every 10 s: 25% (heroic 35%) of the tank '
    'row (the script\'s base point, times Grief), carrying the held seal\'s rider (Righteousness brands, Justice '
    'marks). Judgement of Light 20271\'s SV 5651.',
    icon=_ICON_JUDGEMENT, visual=CV_JUDGEMENT,
)

seal_of_command_212398 = _held_seal(
    212398, 'Seal of Command', SV_SEAL_COMMAND, 'His swings cleave everything in front of him.',
    f'{_SD}, CV6b: the held seal (Command, Righteousness, Justice, every 20 s / heroic 15 s, the emote line 0). While '
    'it holds, a persistent registry Frontal: a 120 degree, 8 yd cone in front of him, live 2 s after the emote, '
    'one cleave every 2 s (his swing), the tank exempt (the tank faces him away). The minted STATE SV 90555 (WP-V; '
    'fallback: the one-shot SV 7992 re-cast every 3 s if the client does not loop it).',
    icon=_ICON_SEAL_OF_COMMAND,
)

command_cleave_212399 = resolve_copy(
    212399, 'Seal of Command', School.NORMAL, 'The Fallen Champion\'s blade cleaves everything in front of him.',
    f'{_SD}, CV6b: the frontal\'s hit: 30% (heroic 45%) of the reference row to every player but his tank in the '
    'cone, 1 Weakened, every 2 s while Seal of Command holds. Copy of the mod-boss-mechanics resolve spell '
    '(Physical). Seal of Command 57769\'s SV 7992 on every unit hit.',
    icon=_ICON_SEAL_OF_COMMAND, visual=CV_SEAL_COMMAND,
)

seal_of_righteousness_212400 = _held_seal(
    212400, 'Seal of Righteousness', SV_SEAL_RIGHTEOUSNESS, 'His judgements brand his foes with holy fire.',
    f'{_SD}, CV6c: the held seal (emote line 1). Each Judgement under it brands 2 (heroic 3) random non-tank players '
    '(212401). The minted STATE SV 90556 (fallback SV 7986 re-cast).',
    icon=_ICON_SEAL_OF_RIGHTEOUSNESS,
)

righteous_brand_212401 = _debuff(
    212401, 'Righteous Brand', BRAND_MS, CV_SEAL_RIGHTEOUSNESS, 'Branded with holy fire.',
    'Branded with holy fire. Keep away from your allies.',
    f'{_SD}, CV6c: the 5 s brand on a carrier (the registry Spread\'s target): 5 s later it bursts for 35% (heroic '
    '45%) + Weakened on every other player within 6 yd (212402); the carrier takes nothing. The tank is never branded '
    '(the large-spread exemption). Seal of Righteousness 20154\'s SV 7986.',
    icon=_ICON_SEAL_OF_RIGHTEOUSNESS,
)

righteous_burst_212402 = resolve_copy(
    212402, 'Righteous Brand', School.HOLY, 'A brand of holy fire bursts.',
    f'{_SD}, CV6c: a brand\'s burst: 35% (heroic 45%) of the reference row to every other player within 6 yd of the '
    'carrier, the tank on its own row, 1 Weakened. Copy of the mod-boss-mechanics resolve spell (Holy). Consecration '
    '43429\'s SV 5600 on every unit hit (VISUALS report; the shipped 6 yd holy zone 90511 is the alternative).',
    icon=_ICON_SEAL_OF_RIGHTEOUSNESS, visual=CV_RIGHTEOUSNESS_BURST,
)

seal_of_justice_212403 = _held_seal(
    212403, 'Seal of Justice', SV_SEAL_JUSTICE, 'His judgements call down the hammer of justice.',
    f'{_SD}, CV6d: the held seal (emote line 2). Each Judgement under it marks a random player, the tank included '
    '(212404). The minted STATE SV 90557 (fallback SV 9504 re-cast).',
    icon=_ICON_SEAL_OF_JUSTICE,
)

justice_mark_212404 = _debuff(
    212404, 'Hammer of Justice', JUSTICE_MARK_MS, CV_JUSTICE_HAMMER, 'A hammer of justice hangs overhead.',
    'A hammer of justice will fall here. Gather your allies to share the blow.',
    f'{_SD}, CV6d: the 5 s mark (the registry Stack\'s anchor, 6 yd): 5 s later the hammer falls for 150% (heroic '
    '250%) of the reference row split among every player within 6 yd (212405); normal caps a share at 75%, heroic '
    'not (a lone target dies). Avenger\'s Shield waits while it is up; normal Exorcism never aims at its carrier. The '
    'shipped falling hammer SV 90044 (the Retribution rework\'s Execution Sentence state).',
    icon=_ICON_HAMMER_OF_JUSTICE,
)

justice_hammer_212405 = _script_hit(
    212405, 'Hammer of Justice', 'The hammer of justice falls.',
    f'{_SD}, CV6d: a share of the hammer: 150% (heroic 250%) of the reference row times Grief, split evenly among the '
    'players inside the 6 yd stack (DungeonKit::SplitShares, at most 75% each on normal; the marked alone when '
    'nobody stood with him), each share the script\'s base point. No Weakened (a soak). Hammer of Justice 13005\'s '
    'SV 322 on each.',
    icon=_ICON_HAMMER_OF_JUSTICE, visual=CV_JUSTICE_MARK,
)

# --- the Champion: CV7 Avenger's Shield -------------------------------------------------------------------------------

avengers_shield_cast_212406 = cast_bar(
    212406, 'Avenger\'s Shield', SHIELD_CAST_MS, 'The Fallen Champion readies his shield.',
    f'{_SD}, CV7: the 2 s bar, first at 10 s, then every 15 s (waiting while a Justice mark is up), aimed at a '
    'random player more than 10 yd from him. DUMMY on the caster, not interruptible. The registry Spread on the '
    'target (8 yd; eligible: the players more than 10 yd from him) is the telegraph; the script throws on its resolve.',
    icon=_ICON_AVENGERS_SHIELD,
)

avengers_shield_212407 = _script_hit(
    212407, 'Avenger\'s Shield', 'A hurled shield strikes and silences.',
    f'{_SD}, CV7: the first target: 20% (heroic 25%) of the reference row times Grief (the script\'s base point) and '
    'a 2 s silence (the carrier: no Weakened); the loss of control stays inside the 2 s rule. Avenger\'s Shield '
    '32674\'s SV 7886 (the missile, the impact, the head state).',
    icon=_ICON_AVENGERS_SHIELD, visual=CV_AVENGERS_SHIELD, duration_ms=SHIELD_SILENCE_MS, aura_desc='Silenced.',
    more_effects=(Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SILENCE, mechanic=_MECHANIC_SILENCE,
                         implicit_target_a=TARGET_UNIT_TARGET_ANY),),
)

avengers_shield_bounce_212408 = _script_hit(
    212408, 'Avenger\'s Shield', 'The shield bounces to a nearby foe.',
    f'{_SD}, CV7: a bounce: to the nearest player within 8 yd of the last hit, never twice, up to 3 hits (heroic 5) '
    'in all; 30% (heroic 40%) of the reference row times Grief (the script\'s base point) and 1 Weakened (the '
    'script adds it). Avenger\'s Shield 32674\'s SV 7886.',
    icon=_ICON_AVENGERS_SHIELD, visual=CV_AVENGERS_SHIELD,
)

# --- CV1 The Last Vigil -----------------------------------------------------------------------------------------------

last_vigil_212409 = spell(
    id=212409, name='The Last Vigil', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=VIGIL_CHANNEL_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_PENANCE,
    notes=f'{_SD}, CV1: Azshir\'s 8 s channel when the Champion falls while he stands (the yell line 0): not '
          'interruptible (InterruptFlags, ChannelInterruptFlags and PreventionType 0); he casts nothing else '
          'meanwhile (the window to kill him). Cast for real on himself (the channel bar shows). The script\'s timer '
          'is the truth: at 8 s, with Azshir alive, the Champion rises (40% then 20% normal, 50% heroic). Penance '
          '47540\'s SV 10980 (the ChannelKit holy hands; no beam).',
    raw_overrides=kit_raw('Azshir keeps the vigil over his fallen brother.', 'Keeping the vigil.', instant=True,
                          InterruptFlags=0, ChannelInterruptFlags=0, PreventionType=0, SpellVisualID_1=CV_VIGIL_CHANNEL,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

last_vigil_ring_212410 = spell(
    id=212410, name='The Last Vigil', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=VIGIL_RING_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_PENANCE,
    notes=f'{_SD}, CV1: the ring under the fallen Champion while Azshir channels (his AI puts it on himself with '
          'AddAura; removed at the rise, the real death or a reset). The shipped 5 yd gold holy zone SV 90510 as a '
          'STATE. No effect.',
    raw_overrides=kit_raw('', 'The vigil holds his soul.', instant=True, InterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=CV_VIGIL_RING, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

last_vigil_rise_212411 = spell(
    id=212411, name='The Last Vigil', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_REDEMPTION,
    notes=f'{_SD}, CV1: the rise\'s look, the Champion on himself (triggered) as he stands again. Scarlet '
          'Resurrection\'s SV 1443 (one-shot). No effect.',
    raw_overrides=kit_raw('The Fallen Champion rises again.', instant=True, InterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=CV_VIGIL_RISE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

grief_212412 = spell(
    id=212412, name='Grief', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=GRIEF_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Grief: a flat +20% damage done a stack, not a damage or heal value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=GRIEF_PCT,
                    die_sides=0, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BLOODLUST,
    notes=f'{_SD}, CV1: Azshir fell first: from 5 s after his death, every 5 s the Champion gains a stack '
          '(DungeonKit::AddStacks on himself): +20% damage done (every school: his melee; his script percents are '
          'multiplied by the script, as they ignore caster modifiers) and +20% attack speed a stack. Normal caps at 5 '
          '(the script), heroic has no cap (CumulativeAura 255, the aura\'s ceiling). Removed on reset, evade and '
          'death. SV 6943 (BeastRageState head + BloodLust hands, lasting).',
    raw_overrides=kit_raw('Consumed by grief.', 'Damage done and attack speed increased by $s1%.', instant=True,
                          SpellVisualID_1=CV_GRIEF, CumulativeAura=GRIEF_STACKS, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- CV8 Execution Sentence (heroic) ----------------------------------------------------------------------------------

execution_sentence_212413 = spell(
    id=212413, name='Execution Sentence', school=School.HOLY, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=EXECUTION_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_SCHOOL_HEAL_ABSORB, base_points=0, die_sides=0,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_ABSORB)],
    spell_icon_id=_ICON_EXECUTION_SENTENCE,
    notes=f'{_SD}, CV8 (heroic): a hammer of light over a random player, the tank included, first at 20 s, then '
          'every 30 s (Azshir\'s emote line 2): SPELL_AURA_SCHOOL_HEAL_ABSORB (301) absorbing the next 75% of the '
          'reference row of healing (the tank row on the tank; spell_sm_council_execution_sentence sets the amount at '
          'application). MiscValue 127: EVERY school, or a Nature heal would pass through it (WP-HEAL). Not '
          'dispellable; lands through immunities (Divine Shield and Ice Block cannot shed it). When healing strips '
          'it (Unit::CalcHealAbsorb removes it by ENEMY_SPELL) the hammer falls on the room: 10% + 5% for every '
          'second it was up (212414); at 8 s (EXPIRE) it falls on its own for 50%. Any other removal (death, the '
          'reset) is silent. No Weakened (group damage). The shipped falling hammer SV 90044.',
    raw_overrides=kit_raw('A hammer of light hangs over the target, absorbing healing.',
                          'Absorbs the next $s1 healing received. When healed away or after $d, the hammer falls on '
                          'everyone.', instant=True, InterruptFlags=0, PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                          SpellVisualID_1=CV_EXECUTION_SENTENCE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(execution_sentence_212413, 'spell_sm_council_execution_sentence')

execution_burst_212414 = _script_hit(
    212414, 'Execution Sentence', 'The hammer of light falls on everyone.',
    f'{_SD}, CV8: the room burst on every player on the lawn: 10% + 5% a second the hammer was up when healed away, '
    '50% when it ran out, of the reference row (the tank row on the tank; the script\'s base point). No Weakened. The '
    'shipped burst SV 90045.',
    icon=_ICON_EXECUTION_SENTENCE, visual=CV_EXECUTION_SENTENCE_BURST,
)

execution_wave_212415 = spell(
    id=212415, name='Execution Sentence', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_HOLY_NOVA,
    notes=f'{_SD}, CV8: the room wave\'s look on Azshir as the hammer falls (triggered, on himself). Holy Nova '
          '15237\'s SV 3643. No effect.',
    raw_overrides=kit_raw('', instant=True, InterruptFlags=0, PreventionType=0, SpellVisualID_1=CV_ROOM_WAVE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
