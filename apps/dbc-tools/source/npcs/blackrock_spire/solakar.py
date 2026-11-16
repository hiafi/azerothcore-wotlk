"""
Blackrock Spire build WP-B11: Solakar Flamewreath (10264), "The Stolen Flame", a hot potato
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows SK, s3.5 row B11, s3.6, s3.8 NM 10;
build spec docs/dungeons/blackrock-spire-rework.md SP 3037-3110, design SP 2791-3036, rulings 55-58). WP-B11 owns this
file (its spells: kSpellsSolakar 210390-210429 of modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h;
SolakarLogic.h names the same ids; creature 300731). Item 13371's toss is
source/world/blackrock_spire_father_flame.py (an item_template() edit needs the live item rows, which the boss
package's other loaders do not pass). The engine side is src/BlackrockSpire/boss_solakar_flamewreath_rework.cpp and the
instance's Solakar event; the texts, the pair's dropped
SmartAI rows and Father Flame's ScriptName are the core SQL rev rev_solakar_flamewreath_blackrock_spire.sql.

- 10264 Solakar Flamewreath: bound to boss_solakar_flamewreath_rework (the stock C++ boss_solakar_flamewreath stays
  registered, unbound by this data: its War Stomp 16727 is retired), normal 175k at 5 players (HealthModifier 57.339
  on the level 60 warrior class base 3,052; the flex scaler multiplies it at the pull), stun immune (1972),
  INSTANCE_BIND, DamageModifier 3.5 (the stock value). Heroic 220k is WP-H's.
- 10258 Rookery Guardian (SK3; boss-kit only, summoned by the instance's event): npc_brs_rookery_guardian (SmartAI off:
  the rev drops its three rows; Strike 15580 and Sunder Armor 15572 keep their SmartAI timers in C++, the "start
  attacking" row is the AI's zone-in), level 60 (stock 58-59), 30,000 at 5 players (HealthModifier 9.82962), the base
  SQL DamageModifier 7.5. Heroic 38,000 is WP-H's.
- 10683 Rookery Hatcher (SK2): npc_brs_rookery_hatcher (the stock C++ npc_rookery_hatcher and its SmartAI retired: no
  timed Hatch Rookery Egg 15746, no uncapped whelps), level 60, 25,000 at 5 players (HealthModifier 8.191349),
  DamageModifier 7.5. Stunnable, snareable, rootable (SP: stops are a reward). Heroic 32,000 is WP-H's.
- 300731 Flame whelp (SK6): a copy of the stock Rookery Whelp 10161 (display 397; the stock whelp stays with the egg
  traps), a dragonkin of faction 16, level 60, 3,000 at 5 players (HealthModifier 0.982962; heroic 4,000 is WP-H's
  override, difficulty_entry_1 310295: the first wave 2 kit add of heroic_ids.lock's order), a light bite
  (DamageModifier 1.0, the Broodling's), no loot, no XP. npc_brs_flame_whelp: hatched by the flame (at most 6 alive, 12
  at 6 or more); on heroic it chases the holder.
- Item 13371 Father Flame (SK5): gains its on-use toss (210391) in source/world/blackrock_spire_father_flame.py.

Spells (looks from ._visuals, WP-V-2's SK_* picks and SV_TORCH_HELD; every look unconfirmed until seen in game):

  210390  Father Flame       SK4 the holder aura: the torch in hand (SV_TORCH_HELD), no cancel, no dispel
  210391  Toss Father Flame  SK5 item 13371's on-use: a friendly player within 30 yd, Torch Toss's missile (33 yd/s)
  210392  Searing Heat       SK4 the holder's burn, self-cast every second, its flat amount set by the script
  210393  Scorched Hands     SK5 the thrower cannot catch (15 / 25 s normal, 10 / 25 s heroic; the script sets it)
  210394  Father Flame       SK6 the catch's flare (look, Torch Toss (land))
  210395  Hatch              SK6 a hatching egg's burst on the new whelp (look)
  210396  Hatch Rookery Egg  SK2 the Hatcher at its clutch (look, the stock hatch cast)
  210397  Father Flame       SK2 the flame the Hatcher carries (SV_TORCH_HELD)
  210398  Flamewreath        SK8 normal: +20% damage done a stack, 3 stacks
  210399  Flamewreath        SK8 heroic: +25% a stack
  210400  Wreathed in Flame  SK8 the enrage's marker on him
  210401  Wreathed in Flame  SK8 the enrage's 10% every 2 s (the script's percent spell)
  210402  The Warden's Hunt  SK9 the 1.5 s roar (a cast bar, Bellowing Roar's look)
  210403  The Warden's Hunt  SK9 the 8 s hunt on him (the bots' tell)
  210404  Hunted             SK9 the hunted holder (debuff)
  210405  War Stomp          SK10 the 2 s bar
  210406  War Stomp          SK10 the hit (resolve copy, Physical): 25%, Weakened, the stun rider
  210407  War Stomp          SK3 / SK10 the stomp (look, the stock War Stomp)
  210408  War Stomp          SK10 the 2 s stun rider
  210409  Ground Stomp       SK3 the Guardian's 2 s bar
  210410  Ground Stomp       SK3 the hit (resolve copy, Physical): 20%, Weakened
  210411  Throw Spear        SK11 heroic: the spear in flight (Throw Spear 54617's missile)
  210412  Spear Wound        SK11 heroic: the bleed, 1% a second for 12 s, then it tears
  210413  Spear Wound        SK11 heroic: the tear, 40% (the script's percent spell)
  210414  Cauterize          SK11 heroic: the wound seared shut (look)
  210415-210429 spare.

Tooltips are number-free where the number is a reference percent (Systems.md s10).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
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
    FACTION_SPIRE_MONSTER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_FLAME_WHELP,
    SK_EGG_HATCH_BURST,
    SK_EGG_HATCH_CAST,
    SK_FLAME_WREATH,
    SK_HUNT_ROAR,
    SK_SPEAR_CLEANSE,
    SK_SPEAR_THROW,
    SK_SPEAR_WOUND,
    SK_SPEAR_WOUND_ALT,
    SK_TORCH_CATCH,
    SK_TORCH_TOSS,
    SK_WAR_STOMP,
    SV_TORCH_HELD,
    VG_FIRE_BLAST_IMPACT,
)

_B11 = 'Blackrock Spire build WP-B11 (Solakar Flamewreath)'
_PERCENT_EXCLUDED = ('Blackrock Spire: a percent of reference health, set by the B11 script (DungeonKit::RefFlatOn: '
                     'the flat amount, or hundredths read by spell_brs_solakar_ref_pct)')

# --- shared bits -----------------------------------------------------------------------------------------------------

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_TARGET_ALLY = 21
_MECHANIC_STUN = 12
_MECHANIC_BLEED = 15
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_SCHOOL_MASK_ALL = 127
# SPELL_ATTR0_NO_AURA_CANCEL (SharedDefines.h): the holder cannot right-click the flame away.
_ATTR0_NO_AURA_CANCEL = 0x80000000
# SPELL_ATTR3_SUPPRESS_CASTER_PROCS: the holder's own burn procs nothing of theirs.
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
# SPELL_ATTR5_ALLOW_WHILE_STUNNED: a stunned holder (War Stomp) can still throw (SP: "a holder always has time").
_ATTR5_ALLOW_WHILE_STUNNED = 0x00000008
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): nothing outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# Icons (the working-copy Spell.dbc).
_ICON_TORCH_TOSS = 1887             # Torch Toss 45732
_ICON_FLAME_WREATH = 937            # Flame Wreath 29947
_ICON_HATCH = 2316                  # Hatch Rookery Egg 15746
_ICON_ROAR = 11                     # Bellowing Roar 18431
_ICON_WAR_STOMP = 50                # War Stomp 16727
_ICON_THROW_SPEAR = 370             # Throw Spear 54617
_ICON_DEEP_WOUND = 243              # Deep Wound 43104
_ICON_CAUTERIZE = 1930              # Cauterize 60211

# Numbers (SolakarLogic.h).
_FLAMEWREATH_PCT = 20               # kFlamewreathPctPerStack normal
_FLAMEWREATH_PCT_HEROIC = 25        # ... heroic
_FLAMEWREATH_CAP = 3                # kFlamewreathCap
_TOSS_RANGE = 30.0                  # kTossRangeYd
_TOSS_SPEED = 33.0                  # kTossSpeed: 0.75 s at 25 yd
_TOSS_COOLDOWN_MS = 1000            # one toss in flight at a time (the flight is under a second)
_SCORCHED_MAX_MS = 25000            # ScorchedHandsMs at 6 or more (the script shortens it at 5)
_HUNT_ROAR_MS = 1500                # kHuntRoarMs
_HUNT_CHASE_MS = 8000               # kHuntChaseMs
_STOMP_CAST_MS = 2000               # kStompCastMs
_WAR_STOMP_STUN_MS = 2000           # kWarStompStunMs
_SPEAR_WOUND_MS = 12000             # kSpearWoundMs
_SPEAR_SPEED = 18.0                 # Throw Spear 54617's own

# The hits whose damage the script sets: no threat, ignore line of sight, no crit, always hit, ignore caster
# modifiers (a percent of the reference row; Flamewreath is the script's multiplier), no cast log.
_SCRIPT_HIT_RAW = dict(
    CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
    AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
)

# --- the bindings (wave 2) -------------------------------------------------------------------------------------------

_GUARDIAN_HEALTH_MODIFIER = 9.82962     # 3,052 x 9.82962 = 30,000 at level 60
_HATCHER_HEALTH_MODIFIER = 8.191349     # 25,000
_WHELP_HEALTH_MODIFIER = 0.982962       # 3,000
FLAME_WHELP_HEROIC_ENTRY = 310295       # heroic_ids.lock: the first wave 2 kit add (test_blackrock_spire_heroic)

if BIND_WAVE_2:
    creature_template_columns(10264, **boss_columns(
        'boss_solakar_flamewreath_rework', 57.339, damage_modifier=3.5,
    ))
    creature_template_columns(
        10258, ScriptName='npc_brs_rookery_guardian', AIName='', minlevel=60, maxlevel=60,
        HealthModifier=_GUARDIAN_HEALTH_MODIFIER, DamageModifier=7.5,
    )
    creature_template_columns(
        10683, ScriptName='npc_brs_rookery_hatcher', AIName='', minlevel=60, maxlevel=60,
        HealthModifier=_HATCHER_HEALTH_MODIFIER, DamageModifier=7.5,
    )

# --- 300731 Flame whelp ----------------------------------------------------------------------------------------------

_KIT_DRAGONKIN = kit_creature(faction=FACTION_SPIRE_MONSTER, type=2)

flame_whelp_300731 = creature_template(
    300731, 'Flame Whelp', **{
        **_KIT_DRAGONKIN, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': _WHELP_HEALTH_MODIFIER, 'DamageModifier': 1.0, 'BaseAttackTime': 2000,
        'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'ScriptName': 'npc_brs_flame_whelp', 'difficulty_entry_1': FLAME_WHELP_HEROIC_ENTRY,
    },
)
creature_model(300731, display_id=DISPLAY_FLAME_WHELP)

# --- SK4 / SK5 the flame in hand -------------------------------------------------------------------------------------

father_flame_210390 = spell(
    id=210390, name='Father Flame', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES | _ATTR0_NO_AURA_CANCEL, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_TORCH_TOSS,
    notes=f'{_B11}, SK4: the holder aura (the holder is whoever has it; mod-boss-mechanics\' PassEntry reads it). '
          'Taking Father Flame (go_brs_father_flame) puts it and item 13371 on the taker; a toss (210391) moves both '
          'on landing; the script ticks Searing Heat (210392) every second it is held, rising, and drops the flame on '
          'the floor when its holder dies or leaves. A debuff with no dispel and no cancel; dropped on a map change. '
          'V-2\'s held torch (SV_TORCH_HELD 90603, a weapon-slot state; fallback SK_HELD_FLAME_ALT 8581).',
    raw_overrides=kit_raw('Father Flame burns in your hand, hotter every second. Use Father Flame on an ally to throw '
                          'it.', 'Holding Father Flame: it burns hotter every second. Throw it to an ally.',
                          CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, SpellVisualID_1=SV_TORCH_HELD),
)

toss_210391 = spell(
    id=210391, name='Toss Father Flame', school=School.FIRE, cast_time_ms=0, cooldown_ms=_TOSS_COOLDOWN_MS,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_TOSS_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_TORCH_TOSS,
    notes=f'{_B11}, SK5: item 13371\'s on-use (spelltrigger 0). Only the holder can use it (CasterAuraSpell 210390); a '
          'friendly player within 30 yd who may catch (spell_brs_solakar_flame_toss CheckCast: alive, not the thrower, '
          'not Scorched, heroic: a wounded player may while Scorched). The flame flies at 33 yd/s (0.75 s at 25 yd, '
          'Torch Toss 45732\'s missile, SV 10211); on landing the script moves the aura and the item to the catcher, '
          'puts Scorched Hands on the thrower and hatches the eggs within 4 yd of the catcher. Usable while stunned '
          '(a holder always has time to throw). A 1 s cooldown: one flame in the air. Bots throw it by '
          'PlayerbotAI::ImbueItem (PassEntry::WithItem).',
    raw_overrides=kit_raw('Throw Father Flame to an ally. The flame burns whoever holds it; you cannot catch it again '
                          'for a while.', instant=True, Speed=_TOSS_SPEED, SpellVisualID_1=SK_TORCH_TOSS,
                          CasterAuraSpell=210390, InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AttributesEx5=_ATTR5_ALLOW_WHILE_STUNNED),
)
scripted_by(toss_210391, 'spell_brs_solakar_flame_toss')

searing_heat_210392 = spell(
    id=210392, name='Searing Heat', school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=1, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_PERCENT_EXCLUDED)],
    spell_icon_id=_ICON_FLAME_WREATH,
    notes=f'{_B11}, SK4: the burn, cast by the holder on themself (triggered) every second they hold the flame, its '
          'amount the base points the script passes: the holder\'s reference row x the heat table (first second 1% / '
          '2% at 6 or more, rising 0.5% / 1% a second; heroic 1% + 1%, 2% + 1.5%), never stopping until a toss '
          '(ruling 57). Self-cast so the hidden Solakar of the opening stays out of combat. Ignores caster modifiers, '
          'suppresses the holder\'s own procs. Vosh\'gajin\'s Fire Blast impact (SV 143) on each tick.',
    raw_overrides=kit_raw('The flame burns.', **{**_SCRIPT_HIT_RAW, 'AttributesEx3': ATTR3_ALWAYS_HIT
                          | ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_SUPPRESS_CASTER_PROCS},
                          SpellVisualID_1=VG_FIRE_BLAST_IMPACT),
)

scorched_hands_210393 = spell(
    id=210393, name='Scorched Hands', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_SCORCHED_MAX_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FLAME_WREATH,
    notes=f'{_B11}, SK5: on the thrower when the flame lands: they cannot catch it (the toss\'s CheckCast, the floor '
          'pickup\'s eligibility, PassEntry::CatchWhen). 25 s here (6 or more players); the script cuts it to 15 s '
          '(normal) or 10 s (heroic) at 5 players (ScorchedHandsMs). Heroic: a wounded player still catches. Not '
          'dispellable; dropped on a map change and with the fight.',
    raw_overrides=kit_raw('Your hands are scorched: you cannot catch Father Flame.', 'Cannot catch Father Flame.',
                          CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

catch_flare_210394 = self_visual(
    210394, 'Father Flame', SK_TORCH_CATCH,
    f'{_B11}, SK6: the catch, cast by the catcher on themself (triggered) as the flame lands. Torch Toss (land) '
    '46054\'s SV 10302 (a base fire flash). The eggs within 4 yd hatch beside it (the script).',
    icon=_ICON_TORCH_TOSS, school=School.FIRE,
)

hatch_burst_210395 = self_visual(
    210395, 'Hatch', SK_EGG_HATCH_BURST,
    f'{_B11}, SK6: a flame whelp\'s first breath, cast by the new whelp on itself where its egg stood. Emberseer '
    'Growing 16049\'s SV 3947 (V-2: a smoke puff at the egg).',
    icon=_ICON_HATCH, school=School.FIRE,
)

hatcher_hatch_210396 = self_visual(
    210396, 'Hatch Rookery Egg', SK_EGG_HATCH_CAST,
    f'{_B11}, SK2: the Hatcher at its clutch, cast on itself as every egg within 6 yd hatches. Hatch Rookery Egg '
    '15746\'s SV 4204 (the stock cast\'s hands).',
    icon=_ICON_HATCH, school=School.FIRE,
)

stolen_flame_210397 = spell(
    id=210397, name='Father Flame', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_TORCH_TOSS,
    notes=f'{_B11}, SK2: the flame the Hatcher snatched, on it while it runs for a clutch (the torch in hand, '
          'SV_TORCH_HELD). Removed when it drops the flame (killed, stunned, at the clutch). Not the holder aura: the '
          'pass sees players only.',
    raw_overrides=kit_raw('Carrying Father Flame.', 'Carrying Father Flame.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=SV_TORCH_HELD),
)

# --- SK8 Flamewreath, Wreathed in Flame ------------------------------------------------------------------------------


def _flamewreath(spell_id: int, pct: int, which: str):
    return spell(
        id=spell_id, name='Flamewreath', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=pct,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=f'Flamewreath: a flat +{pct}% damage done per stack, not a damage value')],
        spell_icon_id=_ICON_FLAME_WREATH,
        notes=f'{_B11}, SK8 ({which}): a stack on him for each Reclaim and each torn Spear Wound, cap 3 '
              f'(DungeonKit::AddStacks, him as caster): +{pct}% damage done a stack, every school (his melee); the '
              'custom percent hits ignore caster modifiers, so the script multiplies War Stomp, the spear\'s bleed and '
              'the tear itself (WreathMult). A Reclaim or a tear at 3 stacks is the enrage (210400). Flame Wreath '
              '29947\'s state (SV 4101: one flame at his base). Removed on his death, evade and reset.',
        raw_overrides=kit_raw('The warden burns hotter.', 'Damage done increased.', instant=True,
                              CumulativeAura=_FLAMEWREATH_CAP, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=SK_FLAME_WREATH),
    )


flamewreath_210398 = _flamewreath(210398, _FLAMEWREATH_PCT, 'normal')
flamewreath_heroic_210399 = _flamewreath(210399, _FLAMEWREATH_PCT_HEROIC, 'heroic')

wreathed_210400 = spell(
    id=210400, name='Wreathed in Flame', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FLAME_WREATH,
    notes=f'{_B11}, SK8: the enrage, on him from the fourth Reclaim or torn wound at 3 Flamewreath stacks (line 3) to '
          'the end: the script casts 210401 at everyone every 2 s. A marker (the buff icon); his Flamewreath state '
          'is the look.',
    raw_overrides=kit_raw('Wreathed in flame: the Rookery burns.', 'Burning everyone every 2 sec.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)


def _percent_hit(spell_id: int, name: str, school: School, desc: str, visual: int, icon: int, notes: str):
    """A hit whose percent of the reference row the script passes in hundredths (raised by Flamewreath);
    spell_brs_solakar_ref_pct turns it into the flat amount at launch."""
    s = spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=1,
                        implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_PERCENT_EXCLUDED)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, **_SCRIPT_HIT_RAW, SpellVisualID_1=visual),
    )
    scripted_by(s, 'spell_brs_solakar_ref_pct')
    return s


wreathed_tick_210401 = _percent_hit(
    210401, 'Wreathed in Flame', School.FIRE, 'The Rookery burns.', VG_FIRE_BLAST_IMPACT, _ICON_FLAME_WREATH,
    f'{_B11}, SK8: the enrage\'s tick, 10% of the reference row (1000 hundredths, a fixed percent: Flamewreath is at '
    'its cap) on every player in the Rookery every 2 s, unavoidable. Cast by him (triggered).',
)

# --- SK9 the Warden's Hunt -------------------------------------------------------------------------------------------

hunt_roar_210402 = cast_bar(
    210402, 'The Warden\'s Hunt', _HUNT_ROAR_MS, 'Solakar roars and turns on the flame.',
    f'{_B11}, SK9: the 1.5 s roar before a Hunt (emote line 1), 10 s after he arrives, then every 25 s (heroic 20 s), '
    'never during War Stomp. DUMMY on the caster, not interruptible (he has no kick on the list). Bellowing Roar '
    '18431\'s SV 4939 (sound, anim, shake). The bots\' holder throws as it starts with him within 15 yd '
    '(PassTrigger::Casting).',
    icon=_ICON_ROAR, visual=SK_HUNT_ROAR,
)

hunt_210403 = spell(
    id=210403, name='The Warden\'s Hunt', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_HUNT_CHASE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_ROAR,
    notes=f'{_B11}, SK9: on him for the 8 s chase after the roar (the kit\'s Chaser at his stock 10 yd/s, taunt '
          'immune, fixed on the holder; each toss stops him 1 s). The bots\' tell: PassTrigger::UnitNear(10264, 15 '
          'yd, HasAura(210403)) throws. Removed when the Hunt ends (time, a Reclaim, the flame dropped).',
    raw_overrides=kit_raw('Hunting Father Flame.', 'Hunting Father Flame.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

hunted_210404 = spell(
    id=210404, name='Hunted', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_HUNT_CHASE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ROAR,
    notes=f'{_B11}, SK9: on the hunted holder (the script sets its length to what is left of the Hunt) and moved to '
          'each new holder; the red ring around them is a registry decoy circle (drawn, never resolves). Removed '
          'with the Hunt. Dropped on a map change.',
    raw_overrides=kit_raw('Solakar hunts you: throw Father Flame!', 'Solakar is hunting you.', CastingTimeIndex=1,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- SK10 War Stomp and SK3 Ground Stomp -----------------------------------------------------------------------------

war_stomp_bar_210405 = cast_bar(
    210405, 'War Stomp', _STOMP_CAST_MS, 'Solakar rears up to stomp.',
    f'{_B11}, SK10: the 2 s wind-up, 15 s after he arrives, then every 20 s, never during a Hunt (a stomp due in one '
    'waits for its end plus a second). DUMMY on the caster, not interruptible, Physical. The registry\'s 8 yd circle '
    'on him owns the hit (210406).',
    icon=_ICON_WAR_STOMP,
)

war_stomp_210406 = resolve_copy(
    210406, 'War Stomp', School.NORMAL, 'Solakar stomps, stunning everyone near him.',
    f'{_B11}, SK10: the stomp\'s hit, an 8 yd circle on him: 25% of the reference row (the tank its own row; '
    'Flamewreath raises it, the script\'s Damage) to everyone inside, the tank too (ruling 51), 1 Weakened and the 2 s '
    'stun 210408. Copy of the resolve spell 205001 (Physical), no look (210407 shows the stomp).',
    icon=_ICON_WAR_STOMP,
)

stomp_look_210407 = self_visual(
    210407, 'War Stomp', SK_WAR_STOMP,
    f'{_B11}, SK3 / SK10: the stomp, cast on himself (and by the Guardian on itself) as the circle resolves. War Stomp '
    '16727\'s SV 2355 (a 6.9 yd crack; a self DUMMY applies no aura, so its StunSwirl state never shows).',
    icon=_ICON_WAR_STOMP,
)

war_stomp_stun_210408 = spell(
    id=210408, name='War Stomp', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_WAR_STOMP_STUN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_STUN, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_WAR_STOMP,
    notes=f'{_B11}, SK10: the 2 s stun of War Stomp (the registry rider; stock 5 s, rule flag 1). MOD_STUN, stun '
          'mechanic: stun immunity and the stun-breaking trinkets answer it. Dispel none. The toss stays usable '
          'while stunned. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Stunned.', 'Stunned.', CastingTimeIndex=1, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

ground_stomp_bar_210409 = cast_bar(
    210409, 'Ground Stomp', _STOMP_CAST_MS, 'The Rookery Guardian rears up to stomp.',
    f'{_B11}, SK3: the Guardian\'s 2 s wind-up, 6 s after it is summoned, then every 12 s: the same bar and circle as '
    'his War Stomp, without the stun (it previews his). DUMMY on the caster, not interruptible, Physical.',
    icon=_ICON_WAR_STOMP,
)

ground_stomp_210410 = resolve_copy(
    210410, 'Ground Stomp', School.NORMAL, 'The Rookery Guardian stomps.',
    f'{_B11}, SK3: the Guardian\'s hit, an 8 yd circle on it: 20% of the reference row (the tank its own row) and 1 '
    'Weakened, no stun. Copy of the resolve spell 205001 (Physical); the look is 210407 cast by the Guardian.',
    icon=_ICON_WAR_STOMP,
)

# --- SK11 Spear Wound (heroic) ---------------------------------------------------------------------------------------

spear_throw_210411 = spell(
    id=210411, name='Throw Spear', school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_THROW_SPEAR,
    notes=f'{_B11}, SK11 (heroic): the spear in flight, cast by him (triggered) at 1 player (2 at 6 or more), never '
          'the holder, the tank included, halfway between Hunts. Throw Spear 54617\'s HumanSpear01 missile (SV '
          '11993; never 8855 / 10724) at its stock 18 yd/s; on landing spell_brs_solakar_spear_throw has him put the '
          'wound (210412) on the target.',
    raw_overrides=kit_raw('Solakar hurls his spear.', instant=True, Speed=_SPEAR_SPEED, SpellVisualID_1=SK_SPEAR_THROW,
                          InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(spear_throw_210411, 'spell_brs_solakar_spear_throw')

spear_wound_210412 = spell(
    id=210412, name='Spear Wound', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_BLEED,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_SPEAR_WOUND_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=0, die_sides=1,
                    amplitude=1000, mechanic=_MECHANIC_BLEED, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_PERCENT_EXCLUDED)],
    spell_icon_id=_ICON_DEEP_WOUND,
    notes=f'{_B11}, SK11 (heroic): the bleed, 1% of the reference row a second (raised by his Flamewreath stacks at '
          'the throw; spell_brs_solakar_spear_wound sets the amount) for 12 s. Holding Father Flame 2 s in all sears '
          'it shut (the script removes it: no tear); untouched, it runs out and tears (210413, +1 Flamewreath). No '
          'dispel (only the flame cleans it). Bite 17253\'s lasting blood state (SV 376, V-2\'s SK_SPEAR_WOUND).',
    raw_overrides=kit_raw('Bleeding. Hold Father Flame to sear the wound shut.', 'Bleeding. Hold Father Flame to sear '
                          'the wound shut.', CastingTimeIndex=1, DefenseType=_DEFENSE_MELEE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP,
                          SpellVisualID_1=SK_SPEAR_WOUND),
)
scripted_by(spear_wound_210412, 'spell_brs_solakar_spear_wound')

spear_tear_210413 = _percent_hit(
    210413, 'Spear Wound', School.NORMAL, 'The wound tears open.', SK_SPEAR_WOUND_ALT, _ICON_DEEP_WOUND,
    f'{_B11}, SK11 (heroic): the torn wound, 40% of the reference row (raised by Flamewreath; 4000 hundredths and up) '
    'to the wounded player, then the spear comes back to him bloodied (line 4) and he gains a Flamewreath stack. Deep '
    'Wound 43104\'s puff (SV 121).',
)

cauterize_210414 = self_visual(
    210414, 'Cauterize', SK_SPEAR_CLEANSE,
    f'{_B11}, SK11 (heroic): the wound seared shut after 2 s of holding the flame, cast by the healed player on '
    'themself. Cauterize 60211\'s SV 12765 (fire hands, a flame burst, a ring at the base).',
    icon=_ICON_CAUTERIZE, school=School.FIRE,
)
