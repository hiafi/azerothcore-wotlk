"""
Blackrock Spire build WP-B7: Halycon (10220) and Gizrul the Slavener (10268), one encounter
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B7; build spec
docs/dungeons/blackrock-spire-rework.md SP "Halycon and Gizrul", HG1-HG11). WP-B7 owns this file (its spells:
kSpellsHalyconGizrul 210210-210249 of modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h;
HalyconGizrulLogic.h names the same ids; no creature of its own; the nine texts are the core SQL rev
rev_halycon_gizrul_blackrock_spire.sql).

- 10220 Halycon and 10268 Gizrul: both bound to boss_halycon_gizrul_rework (SmartAI off: WP-S0's SQL rev drops
  Gizrul's three stock smart_scripts rows; the stock C++ boss_halycon stays registered, unbound by this data), normal
  120k each at 5 players (Halycon HealthModifier 40.527 on the level 59 warrior class base 2,961, Gizrul 39.318 on the
  level 60 base 3,052; the flex scaler multiplies at the pull, Gizrul's own pull when he arrives), stun immune (1972:
  stun, no silence, so Call of the Pack can be silenced, handoff s7 #16), INSTANCE_BIND. DamageModifier the stock 6.5 /
  3.5 (WP-T tunes melee). Heroic 150k each and the tier's melee are WP-H's (source/world/dungeons/blackrock_spire.py).
  Gizrul has no spawn: Halycon summons him at the pull.

Spells (looks from ._visuals, WP-V-1's HG_* picks; every look unconfirmed until seen in game):

  210210  Savage Charge      HG2 a line's hit: Physical, 30% / 40% + Weakened + a Rabies rider (resolve copy)
  210211  Pack Pounce        HG3 the pounce's hit: Physical, 25% / 30% + Weakened; Maul's claw (SV 166) on the hit
  210212  Thrash             HG4 the ring's hit: Physical, 25% / 30% + Weakened (resolve copy)
  210213  Rabid Froth        HG5 the ring's hit: Nature, 20% / 25% + Weakened + a Rabies rider; Disease Cloud's
                             green gore (SV 1903) on the hit
  210214  Rabid Trail        HG9 (heroic) a trail's tick: no damage, a Rabies rider, Weakened once per trail per
                             player (resolve copy, Nature)
  210215  Rabies             HG6 the Disease: 1% / 1.5% of the reference row per stack (the kit's
                             spell_dungeon_refflat_periodic), every 3 s (every 1.5 s under Pack Fury:
                             spell_brs_hg_rabies skips every other 1.5 s tick without it), 30 s, up to 5 stacks
  210216  Call of the Pack   HG7 the 3 s interruptible howl (Nature, silence-preventable); landed: the script gives
                             Pack Fury (and heroic Bloodied Pack) to both wolves. Furious Howl's look (SV 518)
  210217  Pack Fury          HG7 +25% damage done, 15 s (the script also runs the wolves' timers 1.5 times as fast);
                             Fire Shield's lasting whirl (SV 8581, V-1's pick: Bestial Wrath's SV 7278 is a one-shot)
  210218  Bloodied Pack      HG7 heroic: +10% damage done a stack, up to 5, for the rest of the attempt
  210219  Grief              HG8 the survivor: +25% damage done (heroic 40%, the script's base point), Frothing
                             Rage's flash (SV 870)
  210220  Torn Hide          HG11 (10 players): a stack per bite of a wolf on its own target, +10% damage taken from
                             that wolf per stack (the script's DamageDealt), 15 s (10 s under Pack Fury: the script
                             sets it per bite, and holds it while the wolf cannot bite), no cap; Bite's lasting blood
                             state (SV 376)
  210221  Savage Charge      HG2 the 3 s paw (cast bar)
  210222  Thrash             HG4 the 2 s crouch (cast bar)
  210223  Rabid Froth        HG5 the 2 s head shake (cast bar)
  210224  Savage Charge      look: Feral Charge - Bear's trail (SV 5162), cast on himself as he dashes
  210225  Pack Pounce        look: Leap (SV 12500), cast by Halycon on herself as she leaps (DungeonKit::JumpTo)
  210226  Maul               look: Maul's claw (SV 166) on her landing
  210227  Thrash             look: Whirlwind's dust whirl (SV 7428) as the ring resolves
  210228  Rabid Froth        look: Disease Cloud (SV 1903) as the ring resolves
  210229  Sprint             HG1 Gizrul's run in: +100% run speed, 10 s (ruling 46)
  210230  Rabid Trail        HG9 look: one Deadmines goo puddle (SV 90342, 4 yd, 12 s); the script drops one every
                             8 yd along a trail. Its DUMMY aura reaches nobody: the registry line owns the ticks
  210231-210249 spare
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
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
    HG_FROTHING_RAGE,
    HG_FURIOUS_HOWL,
    HG_MAUL,
    HG_PACK_FURY,
    HG_PACK_POUNCE,
    HG_RABID_FROTH,
    HG_RABIES,
    HG_SAVAGE_CHARGE,
    HG_THRASH,
    HG_TORN_HIDE,
    SV_GOO_PUDDLE,
)

_B7 = 'Blackrock Spire build WP-B7 (Halycon and Gizrul)'

creature_template_columns(10220, **boss_columns(
    'boss_halycon_gizrul_rework', 40.527, damage_modifier=6.5,
))
creature_template_columns(10268, **boss_columns(
    'boss_halycon_gizrul_rework', 39.318, damage_modifier=3.5,
))

# --- shared bits -----------------------------------------------------------------------------------------------------

_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_FLAG_DEST_LOCATION = 0x40
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127
_DISPEL_DISEASE = 3
_DEFENSE_MAGIC = 1
_SCRIPT_REFFLAT = ('Blackrock Spire: a percent of reference health in hundredths per stack, set by the kit\'s '
                   'spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')

# HalyconGizrulLogic.h (lib/test_blackrock_spire_halycon_gizrul.py pins each against the header)
RABIES_TICK = 100               # kRabiesPctPerStack 1 (hundredths)
RABIES_TICK_HEROIC = 150        # 1.5
RABIES_MS = 30000               # kRabiesMs
RABIES_AMPLITUDE_MS = 1500      # kRabiesAmplitudeMs (every other tick skipped without Pack Fury)
RABIES_MAX = 5                  # kRabiesMaxStacks
CALL_CAST_MS = 3000             # kCallCastMs
PACK_FURY_MS = 15000            # kPackFuryMs
PACK_FURY_PCT = 25              # kPackFuryDamagePct
BLOODIED_PCT = 10               # kBloodiedPackDamagePct
BLOODIED_MAX = 5                # kBloodiedPackMax
GRIEF_PCT = 25                  # kGriefDamagePct normal (heroic 40 through the script's base point)
TORN_HIDE_MS = 15000            # kTornHideMs (the script sets 10 s under Pack Fury)
TORN_HIDE_MAX = 255             # kTornHideMax: "no cap"
PAW_MS = 3000                   # kPawMs
THRASH_WARN_MS = 2000           # kThrashWarnMs
FROTH_WARN_MS = 2000            # kFrothWarnMs
SPRINT_MS = 10000               # kSprintMs
SPRINT_PCT = 100                # kSprintSpeedPct
TRAIL_MS = 12000                # kTrailMs
PUDDLE_RADIUS = 4.0             # kPuddleRadius

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_FERAL_CHARGE = 1559       # Feral Charge - Bear 16979
_ICON_LEAP = 3149               # Leap 57882
_ICON_THRASH = 108              # Thrash 3391
_ICON_DISEASE_CLOUD = 263       # Disease Cloud 28362
_ICON_PLAGUE_SLIME = 233        # Plague Slime 50026
_ICON_RABIES = 203              # Rabies 3150
_ICON_FURIOUS_HOWL = 63         # Furious Howl 3149
_ICON_BESTIAL_WRATH = 1680      # Bestial Wrath 19574
_ICON_FRENZY = 95               # Frenzy 8269
_ICON_FROTHING_RAGE = 86        # Frothing Rage 66759
_ICON_HAMSTRING = 23            # Hamstring 1715 (a bleeding wound)
_ICON_SPRINT = 516              # Sprint 2983


def _damage_aura(spell_id: int, name: str, pct: int, duration_ms: int, notes: str, *, icon: int, visual: int = 0,
                 stacks: int = 0, desc: str, aura_desc: str):
    """+pct% damage done (every school) on the caster: MOD_DAMAGE_PERCENT_DONE. Not dispellable."""
    raw = kit_raw(desc, aura_desc, instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    if stacks:
        raw['CumulativeAura'] = stacks
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=pct,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=f'{name}: a flat +{pct}% damage done, not a damage or heal value')],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


# --- HG2, HG3, HG4, HG5, HG9: the hits (resolve copies) ---------------------------------------------------------------

savage_charge_210210 = resolve_copy(
    210210, 'Savage Charge', School.NORMAL, 'Gizrul tears through everything in his path.',
    f'{_B7}, HG2: a charge line\'s hit, 5 yd wide, 30 yd from him through the farthest non-tank\'s spot (or to the '
    'wall), 3 s after the warning starts (the paw); two lines 1 s apart at 6 or more. 30% (heroic 40%) of the '
    'reference row, 1 Weakened and a Rabies stack (the registry\'s rider 210215). Copy of the mod-boss-mechanics '
    'resolve spell 205001 (Physical). The dash\'s trail is 210224.',
    icon=_ICON_FERAL_CHARGE,
)

pack_pounce_210211 = resolve_copy(
    210211, 'Pack Pounce', School.NORMAL, 'Halycon pounces on the end of the charge.',
    f'{_B7}, HG3: the pounce\'s hit, an 8 yd circle at a charge line\'s far end, drawn with the line, landing 1.5 s '
    'after the charge along it ends (normal: the first line only; heroic every line). 25% (heroic 30%) of the '
    'reference row and 1 Weakened. Resolve copy (Physical); Maul 6807\'s claw (SV 166) on each player hit.',
    icon=_ICON_LEAP, visual=HG_MAUL,
)

thrash_210212 = resolve_copy(
    210212, 'Thrash', School.NORMAL, 'Halycon whirls, raking everything around her.',
    f'{_B7}, HG4: the ring\'s hit, 8 yd around Halycon after a 2 s crouch, her tank exempt (TankExempt). 25% '
    '(heroic 30%) of the reference row and 1 Weakened. Resolve copy (Physical); her whirl is 210227.',
    icon=_ICON_THRASH,
)

rabid_froth_210213 = resolve_copy(
    210213, 'Rabid Froth', School.NATURE, 'Gizrul sprays rabid slaver.',
    f'{_B7}, HG5: the ring\'s hit, 10 yd around Gizrul after a 2 s head shake, his tank exempt. 20% (heroic 25%) of '
    'the reference row, 1 Weakened and a Rabies stack (rider 210215). Resolve copy (Nature); Disease Cloud 28362\'s '
    'green gore (SV 1903) on each player hit.',
    icon=_ICON_DISEASE_CLOUD, visual=HG_RABID_FROTH,
)

rabid_trail_210214 = resolve_copy(
    210214, 'Rabid Trail', School.NATURE, 'The slaver soaks into the floor.',
    f'{_B7}, HG9 (heroic): a soaked charge line, 5 yd wide, 12 s; every 2 s a player inside gains a Rabies stack '
    '(rider 210215) and, once per trail, 1 Weakened (section 7 #25). No damage of its own (the registry\'s Damage is '
    'unset). Resolve copy (Nature), no look (the goo puddles are 210230).',
    icon=_ICON_PLAGUE_SLIME,
)

# --- HG6 Rabies -------------------------------------------------------------------------------------------------------

rabies_210215 = spell(
    id=210215, name='Rabies', school=School.NATURE, dispel=_DISPEL_DISEASE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=RABIES_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=RABIES_TICK,
                    die_sides=0, amplitude=RABIES_AMPLITUDE_MS, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_RABIES,
    notes=f'{_B7}, HG6: the Disease. A stack from Gizrul\'s bite on his target every 8 s, a Savage Charge hit, a '
          'Rabid Froth hit and (heroic) every 2 s in a Rabid Trail; 30 s, each stack refreshing it, up to 5 '
          '(CumulativeAura). 1% (heroic 1.5%: EffectMiscValueB) of the reference row per stack through '
          'spell_dungeon_refflat_periodic (the engine multiplies by the stacks), Nature, ignores caster modifiers. '
          'The aura ticks every 1.5 s; spell_brs_hg_rabies skips every other tick unless its caster wears Pack Fury '
          '(so every 3 s, every 1.5 s under the fury: "Rabies ticks twice as fast"). A Disease dispel clears every '
          'stack (spell_brs_hg_rabies, Smolderweb\'s Venom precedent): a reward, on the dispel list. The lasting '
          'poison state SV 2617 (V-1: the stock Rabies SV 631 is a 3 s impact). Removed when the attempt ends. '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Infected with rabies: Nature damage every 3 sec for each stack. Faster while the pack is '
                          'in a fury.', 'Taking Nature damage every 3 sec for each stack.', CastingTimeIndex=1,
                          CumulativeAura=RABIES_MAX, DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=RABIES_TICK_HEROIC,
                          SpellVisualID_1=HG_RABIES, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(rabies_210215, 'spell_dungeon_refflat_periodic', 'spell_brs_hg_rabies')

# --- HG7 Call of the Pack, Pack Fury, Bloodied Pack; HG8 Grief --------------------------------------------------------

call_of_the_pack_210216 = spell(
    id=210216, name='Call of the Pack', school=School.NATURE, cast_time_ms=CALL_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FURIOUS_HOWL,
    notes=f'{_B7}, HG7: the howl, Halycon\'s (a lone Gizrul\'s under Grief), first at 15 s, then every 25 s. DUMMY on '
          'the caster, 3 s (HalyconGizrulLogic.h kCallCastMs). Interruptible and silence-preventable (InterruptFlags '
          '15, PreventionType silence): the wolves\' immunity set 1972 lets a silence work (handoff s7 #16). Nature, '
          'a school none of their cast bars use (those are Physical), so a kick locks nothing else. Landed '
          '(OnSpellCast) the script gives both wolves Pack Fury (210217) and, on heroic, a Bloodied Pack stack '
          '(210218); kicked it does nothing. The interrupt list names it (priority 3 heroic, 2 normal). Furious Howl '
          '3149\'s sound and howl animation (SV 518).',
    raw_overrides=kit_raw('Halycon howls for the pack: both wolves fly into a fury.', InterruptFlags=15,
                          PreventionType=1, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=HG_FURIOUS_HOWL),
)

pack_fury_210217 = _damage_aura(
    210217, 'Pack Fury', PACK_FURY_PCT, PACK_FURY_MS,
    f'{_B7}, HG7: a landed Call of the Pack, on both wolves (each casts it on itself, triggered): +25% damage done '
    '(every school; the reference-sized hits ignore caster modifiers, so it raises their melee), 15 s. While a wolf '
    'wears it the script runs its timers 1.5 times as fast (more charges, pounces and rings; 4 s Torn Hide bites) and '
    'Rabies from it ticks twice as fast. Fire Shield 35265\'s lasting whirl (SV 8581, V-1: the Bestial Wrath flash is '
    'a one-shot).',
    icon=_ICON_BESTIAL_WRATH, visual=HG_PACK_FURY, desc='The pack is in a fury.',
    aura_desc='Damage done increased by $s1%. Moving faster between attacks.',
)

bloodied_pack_210218 = _damage_aura(
    210218, 'Bloodied Pack', BLOODIED_PCT, -1,
    f'{_B7}, HG7 heroic: every landed Call of the Pack gives both wolves a permanent stack (DungeonKit::AddStacks, '
    'CumulativeAura 5): +10% damage done a stack (their melee). Removed when the attempt ends (evade, reset, death). '
    'No look of its own (Pack Fury carries the read).',
    icon=_ICON_FRENZY, stacks=BLOODIED_MAX, desc='Every answered howl hardens the pack.',
    aura_desc='Damage done increased by $s1%.',
)

grief_210219 = _damage_aura(
    210219, 'Grief', GRIEF_PCT, -1,
    f'{_B7}, HG8: the survivor when the first wolf falls: +25% damage done (heroic 40%: the script casts it with base '
    'point 40), for the rest of the fight; the survivor also takes over the partner\'s half (a lone Gizrul howls, a '
    'lone Halycon charges). Frothing Rage 66759\'s flash (SV 870).',
    icon=_ICON_FROTHING_RAGE, visual=HG_FROTHING_RAGE, desc='Its mate is dead.',
    aura_desc='Damage done increased by $s1%.',
)

# --- HG11 Torn Hide (10 players) --------------------------------------------------------------------------------------

torn_hide_210220 = spell(
    id=210220, name='Torn Hide', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=TORN_HIDE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HAMSTRING,
    notes=f'{_B7}, HG11 (10 players only): each wolf\'s bite on its own target every 6 s (4 s under Pack Fury) adds a '
          'stack (DungeonKit::AddStacks with the wolf as caster: the bots\' taunt swap counts each wolf\'s stacks '
          'apart), no cap (CumulativeAura 255). +10% damage taken from that wolf per stack: the wolf\'s DamageDealt '
          '(the aura is a DUMMY). 15 s, 10 s under Pack Fury (the script sets it at every bite; R-1 ruling 2): the '
          'user\'s taunt rule (2026-11-15) lets a tank take a wolf back only once that wolf\'s stacks are gone, so '
          'the debuff must end before the other tank reaches the swap count (3 bites: 18 s / 12 s) and outlast one '
          'bite (6 s / 4 s). It holds (does not run down) on the wolf\'s current target while the wolf cannot bite '
          '(a charge, a pounce, the run back, a cast bar), so the gap between bites is the bite interval whatever the '
          'downtime. The bots trade wolves at 3. '
          'Not dispellable, dropped on a map change, removed with its wolf. Bite 17253\'s lasting blood state '
          '(SV 376).',
    raw_overrides=kit_raw('Damage taken from the wolf that tore it increased.', 'Damage taken from that wolf '
                          'increased by 10% per stack.', CastingTimeIndex=1, CumulativeAura=TORN_HIDE_MAX,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, SpellVisualID_1=HG_TORN_HIDE),
)

# --- the cast bars (Physical: a kick on Call of the Pack never locks them) --------------------------------------------

charge_bar_210221 = cast_bar(
    210221, 'Savage Charge', PAW_MS, 'Gizrul paws the ground.',
    f'{_B7}, HG2: the 3 s paw before the charge (emote "%s fixes his eyes on $n!"; a lone Halycon\'s too). DUMMY on '
    'the caster, not interruptible; the registry line owns the hit.',
    icon=_ICON_FERAL_CHARGE,
)

thrash_bar_210222 = cast_bar(
    210222, 'Thrash', THRASH_WARN_MS, 'Halycon crouches low.',
    f'{_B7}, HG4: the 2 s crouch (emote "%s crouches low!"), not interruptible; the registry ring owns the hit.',
    icon=_ICON_THRASH,
)

froth_bar_210223 = cast_bar(
    210223, 'Rabid Froth', FROTH_WARN_MS, 'Gizrul shakes his head, slaver flying.',
    f'{_B7}, HG5: the 2 s head shake (emote "%s froths at the mouth!"), not interruptible; the registry ring owns the '
    'hit.',
    icon=_ICON_DISEASE_CLOUD,
)

# --- the looks --------------------------------------------------------------------------------------------------------

charge_look_210224 = self_visual(
    210224, 'Savage Charge', HG_SAVAGE_CHARGE,
    f'{_B7}, HG2: the dash\'s look, cast by the charger on itself as it leaves along the line (Feral Charge - Bear '
    '16979\'s SV 5162: a trail and dust). The move is the script\'s MoveCharge.',
    icon=_ICON_FERAL_CHARGE,
)

leap_look_210225 = self_visual(
    210225, 'Pack Pounce', HG_PACK_POUNCE,
    f'{_B7}, HG3: Halycon\'s leap, cast on herself as she jumps (DungeonKit::JumpTo lookSpell; Leap 57882\'s SV 12500, '
    'a dust landing).',
    icon=_ICON_LEAP,
)

maul_look_210226 = self_visual(
    210226, 'Maul', HG_MAUL,
    f'{_B7}, HG3: her landing (Maul 6807\'s claw slash and gore, SV 166).',
    icon=_ICON_LEAP,
)

whirl_look_210227 = self_visual(
    210227, 'Thrash', HG_THRASH,
    f'{_B7}, HG4: the whirl as the ring resolves (Whirlwind 26083\'s SV 7428; small against the 8 yd ring, which the '
    'marker carries).',
    icon=_ICON_THRASH,
)

froth_look_210228 = self_visual(
    210228, 'Rabid Froth', HG_RABID_FROTH,
    f'{_B7}, HG5: the spray as the ring resolves (Disease Cloud 28362\'s SV 1903: green gore and a fog puff).',
    icon=_ICON_DISEASE_CLOUD, school=School.NATURE,
)

# --- HG1 the run in ---------------------------------------------------------------------------------------------------

sprint_210229 = spell(
    id=210229, name='Answer the Call', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=SPRINT_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_INCREASE_SPEED, base_points=SPRINT_PCT,
                    die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Answer the Call: a flat +100% run speed, not a damage or heal value')],
    spell_icon_id=_ICON_SPRINT,
    notes=f'{_B7}, HG1 (ruling 46): Gizrul answers Halycon\'s pull howl from the level above: +100% run speed for '
          '10 s (cast on himself, triggered, as he is summoned), so the 81 yd run (spawn, ramp, path 402450) takes '
          'about 4 s. Not attackable on the way (unit flags, the script\'s). No look of its own.',
    raw_overrides=kit_raw('Running to his mate.', 'Run speed increased by $s1%.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- HG9 the trail's goo ----------------------------------------------------------------------------------------------

trail_puddle_210230 = spell(
    id=210230, name='Rabid Trail', school=School.NATURE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=TRAIL_MS,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                    implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=PUDDLE_RADIUS)],
    spell_icon_id=_ICON_PLAGUE_SLIME,
    notes=f'{_B7}, HG9 (heroic): one goo puddle on a soaked charge line, visual only. The charger casts it '
          '(triggered) at points every 8 yd along the line (CastSpell(x, y, z)): a dynamic object of 4 yd for 12 s '
          'with the Deadmines green puddle (PersistentAreaKit 90342, goo_flow_state; V-1\'s SV_GOO_PUDDLE, already '
          'shipped). Its DUMMY aura reaches nobody: the registry\'s persistent line (210214) owns the ticks. The '
          'script removes them when the attempt ends.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=SV_GOO_PUDDLE, Targets=_TARGET_FLAG_DEST_LOCATION,
                          InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
