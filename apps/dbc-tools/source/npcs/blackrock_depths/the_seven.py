"""
Blackrock Depths build WP-D21: The Seven (9034-9040)
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 / s3.5 row D21, s3.6, s3.10, s7 #18;
build spec docs/dungeons/blackrock-depths-4-imperial-seat.md "The Seven" TS1-TS10, rulings 72-74, 88, 90, 91). WP-D21
owns this file (its spells: kSpellsTheSeven 211520-211579 of modules/mod-dungeon-bosses src/BlackrockDepths/
BlackrockDepthsRework.h only; TheSevenLogic.h names the same ids). The engine side is src/BlackrockDepths/
boss_the_seven_rework.cpp (one AI on all seven); their texts and the SmartAI drop are
data/sql/updates/pending_db_world/rev_the_seven_blackrock_depths.sql.

- The seven ghosts: boss_the_seven_rework on every entry (stock boss_gloomrel / boss_doomrel retired: Gloom'rel's gossip
  1945 and Doom'rel's 1947 / 1950 are handled by the new script), SmartAI off (the rev drops the rows of 9034, 9035,
  9036, 9038, 9040; 9037 and 9039 had none), the kit's stun immunity set 1972 (s7 #10; the stock -251 set is the
  spec's text, designer question), INSTANCE_BIND (flags_extra 1) on Anger'rel 9035 alone (credit 243; the other six
  flags_extra 0), DamageModifier 3.5 (the stock base value; Gloom'rel's
  live 5.6 is a leftover). Health: one shared pool of 320k (s3.6). Every ghost's template carries the WHOLE pool as its
  own max health (HealthModifier = 320,000 / its class base at its level, creature_classlevelstats basehp0), so the
  kit's SharedHealthPool mirrors the pool's percent onto seven frames that all read the pool's number (KT-D2 "absolute
  numbers on frames"). Heroic 450k each is WP-H's override (source/world/dungeons/blackrock_depths.py, `_boss(450_000)`
  behind wave 2). The bindings are held back until wave 2 binds (_common.py BIND_WAVE_2); the spells are declared
  regardless (inert until a script casts them).

Spells. Registry hits (the charge lines, Hatred, Doom's blast on the others) deal their damage through dungeon copies of
the mod-boss-mechanics resolve spell. Script hits are a percent of the reference row on the kit's generic scripts
(spell_dungeon_refflat_damage / _periodic: the hundredths in the effect, the heroic ones in EffectMiscValueB). The mood
bars are Physical no-effect casts (rule 5: no interrupt school lockout stops a must-play bar):

  211520  Incorporeal          TS1 a shade: -90% damage taken, the lasting purple ghost state (TS_SHADE)
  211521  Incorporeal          look: the pixie-star flash as a ghost fades (TS_SHADE_FADE)
  211522  Gather Doom          TS2 the 3 s interruptible cast (Shadow), normal
  211523  Gather Doom          TS2 the 2 s interruptible cast (Shadow), heroic
  211524  Gathered Doom        TS2 the energy on the ghost, a stack per landed cast (3 max)
  211525  Furious Charge       TS3 the 3 s mood bar (Anger'rel)
  211526  Furious Charge       look: the charge trail (TS_FURIOUS_CHARGE)
  211527  Furious Charge       TS3 a charge line's hit: 30% / 45% + Weakened (resolve copy, Physical)
  211528  Furious Stomp        look: the harmless stomp when nobody stands beyond 10 yd
  211529  Seething Cold        TS4 the 3 s mood bar (Seeth'rel)
  211530  Seething Cold        TS4 a loner's tick: 6% / 10% Frost and -30% speed for 1.5 s
  211531  Dopey Haze           TS5 the 3 s mood bar (Dope'rel)
  211532  Dopey Haze           TS5 the 6 s haze on every player (the look; moving makes you stumble)
  211533  Stumble              TS5 a stumble: 15% / 25% Physical (+ Weakened, by the script)
  211534  Gloom                TS6 the 3 s mood bar (Gloom'rel)
  211535  Gloom                TS6 every player: -50% healing received, 12 s
  211536  Recklessness         TS6 Gloom'rel: +50% damage done, 12 s
  211537  Vile Communion       TS7 the 3 s mood bar (Vile'rel)
  211538  Vile Communion       TS7 the 6 s channel (Holy), kickable: the script heals the pool a sixth a second
  211539  Vile Communion       look: the healing hands again at 3 s
  211540  Hatred               TS8 the 3 s mood bar (Hate'rel)
  211541  Hatred               TS8 the 8 s mark on every player (the purple ring)
  211542  Hatred               TS8 a tick on a player within 6 yd of another: 5% / 8% (resolve copy, Shadow)
  211543  Doom                 TS9 the 3 s mood bar (Doom'rel)
  211544  Doom                 TS9 the 6 s mark on the doomed (the skull; the debuff players read)
  211545  Doom                 TS9 the 6 s mark's ring under the doomed (hidden aura, the look)
  211546  Doom                 TS9 the blast on the others within 10 yd: 30% / 45% + Weakened (resolve copy, Shadow)
  211547  Doom                 TS9 the blast on the doomed: 20% / 30% (Shadow)
  211548  Frostbolt            Seeth'rel (stock 12675 rescaled): 3 s, 6% / 8% and -50% speed 4 s
  211549  Cone of Cold         Seeth'rel (stock 15244 rescaled): a 10 yd cone, 8% / 10% and -50% speed 8 s
  211550  Frost Nova           Seeth'rel TS10 (stock 12674): 10 yd round him, 6% / 8% and a 2 s root (was 8 s)
  211551  Backstab             Dope'rel (stock 15582, on DD's double-use list: a copy): 12% / 15%, from behind
  211552  Rupture              Dope'rel (stock 15583 rescaled): a bleed, 2% / 3% every 2 s for 10 s
  211553  Gouge                Dope'rel TS10 (stock 12540): 3% / 4% and a 2 s incapacitate (was 4 s), any player
  211554  Mind Blast           Vile'rel (stock 15587 rescaled): 1.5 s, 8% / 10%
  211555  Shadow Bolt          Hate'rel (stock 15232, on DD's double-use list: a copy): 3 s, 12% / 15%
  211556  Shadow Bolt Volley   Doom'rel (stock 15245 rescaled): 3 s, everyone within 30 yd, 8% / 10%
  211557  Immolate             Doom'rel (stock 12742 rescaled): 2 s, 8% / 10% and 2% / 3% every 3 s for 21 s
  211558-211579 spare.

Kept as they are (weapon strikes ride the ghost's DamageModifier, buffs deal no damage; none is on DD's double-use
list): Strike 15580, Sunder Armor 11971, Shield Block 12169, Shield Wall 15062, Frost Armor 12544, Sinister Strike
15581, Evasion 15087, Power Word: Shield 11974, Demon Armor 13787. Retired (rulings 73, 91): Frost Ward 15044,
Hate'rel's Strike, Prayer of Healing 15585, Heal 15586, Curse of Weakness 12493, Summon Voidwalkers 15092-15094, the
stock Gouge 12540 / Frost Nova 12674 (copies above). The "stock rescaled" percents are this WP's defaults (gap 36,
designer question 2). Visual ids are V-1 / V-2's (._visuals TS_*); a kept stock spell's copy keeps its stock look
through the visual constant named in `_STOCK_LOOKS` once _visuals.py has it (shared-file request), else none.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from . import _visuals
from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    TARGET_UNIT_CASTER,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    GZ_EARTHSHAKER_STOMP,
    ST_FROSTBOLT,
    TS_DOOM_MARK,
    TS_DOOM_MARK_RING,
    TS_DOPEY_HAZE,
    TS_FURIOUS_CHARGE,
    TS_GATHER_DOOM_CAST,
    TS_GATHER_DOOM_LANDING,
    TS_GLOOM_HEALING_MARK,
    TS_GLOOM_RELS_RECKLESSNESS,
    TS_HATRED,
    TS_SEETHING_COLD,
    TS_SHADE,
    TS_SHADE_FADE,
    TS_VILE_COMMUNION,
    VL_FROST_NOVA,
)

_D21 = 'Blackrock Depths build WP-D21 (The Seven)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')
_SCRIPT_REFFLAT_TICK = ('Blackrock Depths: a percent of reference health in hundredths, set per tick by the kit\'s '
                        'spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')

# --- the bindings (held back until wave 2 binds the section: _common.py BIND_WAVE_2) ---------------------------------

# The shared pool on every frame (TheSevenLogic.h kPoolHealth, PoolHealthModifier): 320,000 / the class base at the
# ghost's level (creature_classlevelstats basehp0, live 2026-11-17: level 55 warrior 2,614, level 55 paladin 2,091,
# level 56 warrior 2,699, level 56 paladin 2,159), rounded to 3 decimals (within 2 health of 320,000).
POOL_HEALTH = (320_000, 450_000)    # kPoolHealth; the heroic value is WP-H's override, pinned by the test
GHOSTS = {
    # entry: (name, level, unit_class, class base)
    9035: ("Anger'rel", 55, 1, 2614),
    9038: ("Seeth'rel", 56, 2, 2159),
    9040: ("Dope'rel", 56, 1, 2699),
    9037: ("Gloom'rel", 56, 1, 2699),
    9036: ("Vile'rel", 56, 2, 2159),
    9034: ("Hate'rel", 55, 2, 2091),
    9039: ("Doom'rel", 56, 2, 2159),
}
ROTATION = (9035, 9038, 9040, 9037, 9036, 9034, 9039)   # BlackrockDepthsRework.h kTheSeven (the stock release order)
CREDIT_GHOST = 9035   # Anger'rel: instance_encounters 243 credits her; only she carries INSTANCE_BIND (_common.py)
DAMAGE_MODIFIER = 3.5


def pool_health_modifier(base: int) -> float:
    """TheSevenLogic.h PoolHealthModifier, rounded as the boss files do."""
    return round(POOL_HEALTH[0] / base, 3)


GHOST_COLUMNS = {entry: boss_columns('boss_the_seven_rework', pool_health_modifier(base),
                                     damage_modifier=DAMAGE_MODIFIER, instance_bind=entry == CREDIT_GHOST)
                 for entry, (_name, _level, _cls, base) in GHOSTS.items()}

if BIND_WAVE_2:
    for _entry in ROTATION:
        creature_template_columns(_entry, **GHOST_COLUMNS[_entry])

# --- constants (TheSevenLogic.h; lib/test_blackrock_depths_the_seven.py pins each against the header) -----------------

GATHER_CAST_MS = (3000, 2000)       # kGatherCastMs
MOOD_CAST_MS = 3000                 # kMoodCastMs
TURN_MS = 40_000                    # kTurnMs (the energy aura lasts a turn)
SHADE_DAMAGE_TAKEN_PCT = -90        # kShadeDamageTakenPct
COLD_PCT = (600, 1000)              # kColdPct 6 / 10 (hundredths)
COLD_SLOW_MS = 1500                 # kColdSlowMs
COLD_SLOW_PCT = 30                  # kColdSlowPct
HAZE_MS = 6000                      # kHazeLifeMs
STUMBLE_PCT = (1500, 2500)          # kStumblePct
GLOOM_MS = 12_000                   # kGloomMs
GLOOM_HEALING_PCT = -50             # kGloomHealingPct
RECKLESSNESS_PCT = 50               # kRecklessnessPct
VILE_CHANNEL_MS = 6000              # kVileChannelMs
HATRED_MS = 8000                    # kHatredLifeMs
DOOM_MARK_MS = 6000                 # kDoomMarkMs
DOOM_SELF_PCT = (2000, 3000)        # kDoomSelfPct
FROSTBOLT_PCT = (600, 800)          # kFrostboltPct
CONE_OF_COLD_PCT = (800, 1000)      # kConeOfColdPct
FROST_NOVA_PCT = (600, 800)         # kFrostNovaPct
FROST_NOVA_ROOT_MS = 2000           # kFrostNovaRootMs
FROST_NOVA_RADIUS = 10.0            # kFrostNovaRadiusYd
BACKSTAB_PCT = (1200, 1500)         # kBackstabPct
RUPTURE_PCT = (200, 300)            # kRupturePct
GOUGE_PCT = (300, 400)              # kGougePct
GOUGE_MS = 2000                     # kGougeMs
MIND_BLAST_PCT = (800, 1000)        # kMindBlastPct
SHADOW_BOLT_PCT = (1200, 1500)      # kShadowBoltPct
VOLLEY_PCT = (800, 1000)            # kVolleyPct
VOLLEY_RADIUS = 30.0                # kVolleyRadiusYd
IMMOLATE_PCT = (800, 1000)          # kImmolatePct
IMMOLATE_TICK_PCT = (200, 300)      # kImmolateTickPct

_TARGET_UNIT_CONE_ENEMY_24 = 24
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_MECHANIC_ROOT = 7
_MECHANIC_SNARE = 11
_MECHANIC_KNOCKOUT = 14
_MECHANIC_BLEED = 15
_DISPEL_MAGIC = 1
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_PREVENTION_SILENCE = 1
_PREVENTION_PACIFY = 2
_INTERRUPT_FLAGS_KICKABLE = 15
_CHANNEL_INTERRUPT_KICK = 0x08              # CHANNEL_INTERRUPT_FLAG_INTERRUPT: a kick stops the channel
_ATTR1_IS_SELF_CHANNELED = 0x00000040       # the Timmy Patty Cake precedent (Evocation's flag)
_AURA_INTERRUPT_DAMAGE = 0x00000002         # Gouge breaks on damage (stock 12540)
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_SCHOOL_MASK_ALL = 127

# Icons (the client Spell.dbc, the stock spells', read 2026-11-17).
_ICON_INCORPOREAL = 178             # Incorporeal 54657
_ICON_SHADOW_BOLT = 213             # Shadow Bolt 15232 (Gather Doom)
_ICON_CHARGE = 457                  # Charge 100
_ICON_WAR_STOMP = 50                # War Stomp 15593
_ICON_FROST = 181                   # Chilled 6136 / Frost Armor 12544
_ICON_DAZED = 15                    # Dazed 1604
_ICON_RECKLESSNESS = 138            # Recklessness 1719
_ICON_CURSE = 543                   # Curse of Weakness 1108 (Gloom's lasting skull)
_ICON_PRAYER = 540                  # Prayer of Healing 596
_ICON_SHADOW_MARK = 178             # Shadow Mark 27825
_ICON_DOOM = 91                     # Curse of Doom 603
_ICON_FROSTBOLT = 188               # Frostbolt 12675
_ICON_CONE_OF_COLD = 35             # Cone of Cold 15244
_ICON_FROST_NOVA = 193              # Frost Nova 12674
_ICON_BACKSTAB = 243                # Backstab 15582
_ICON_RUPTURE = 500                 # Rupture 15583
_ICON_GOUGE = 245                   # Gouge 12540
_ICON_MIND_BLAST = 95               # Mind Blast 15587
_ICON_IMMOLATE = 31                 # Immolate 12742

# The kept kits' copies keep their stock look (rule 15: a copy, the same picture). The ids are V-2's to name in
# _visuals.py (shared-file request in the WP report: TS_CONE_OF_COLD 1007, TS_BACKSTAB 611, TS_RUPTURE 250,
# TS_GOUGE 256, TS_MIND_BLAST 3057, TS_SHADOW_BOLT_VOLLEY 2318, TS_IMMOLATE 46, TS_DOOM_BLAST, TS_FURIOUS_STOMP);
# until a name exists the copy borrows the named fallback (the same stock id under another boss's name) or has no
# look. No raw visual id lives in this file (rule 4).
_STOCK_LOOKS = {
    'TS_FROSTBOLT': ST_FROSTBOLT,                   # Frostbolt 12675's SV 13 (D8's name for it)
    'TS_CONE_OF_COLD': 0,
    'TS_FROST_NOVA': VL_FROST_NOVA,                 # Frost Nova's SV 17 (D6's name for it)
    'TS_BACKSTAB': 0,
    'TS_RUPTURE': 0,
    'TS_GOUGE': 0,
    'TS_MIND_BLAST': 0,
    'TS_SHADOW_BOLT': TS_GATHER_DOOM_CAST,          # Shadow Bolt 15232's SV 64 (the Gather Doom hands are the same)
    'TS_SHADOW_BOLT_VOLLEY': 0,
    'TS_IMMOLATE': 0,
    'TS_DOOM_BLAST': 0,
    'TS_FURIOUS_STOMP': GZ_EARTHSHAKER_STOMP,       # War Stomp's SV 2355 (D5's name for it)
}


def _look(name: str) -> int:
    """The visual `name` from _visuals.py once V-2 adds it, else the fallback above."""
    return getattr(_visuals, name, _STOCK_LOOKS[name])


# The scripted hit: no redirection or reflection, no crit, always hits, ignores the caster's modifiers (a percent of
# the reference row).
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
    AttributesEx2=ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
)


def _raw(desc: str = '', aura_desc: str = '', *, visual: int = 0, **more) -> dict:
    """kit_raw with the visual set only when there is one."""
    if visual:
        more['SpellVisualID_1'] = visual
    return kit_raw(desc, aura_desc, **more)


def _mood_bar(spell_id: int, name: str, desc: str, notes: str, icon: int):
    """A ghost's 3 s mood bar: Physical (rule 5: an interrupt's school lockout never stops it), not interruptible
    (InterruptFlags 0), no effect: the script runs the mood when it ends (OnSpellCast)."""
    return cast_bar(spell_id, name, MOOD_CAST_MS, desc, f'{_D21}: {notes}', icon=icon, school=School.NORMAL)


def _room_aura(spell_id: int, name: str, duration_ms: int, aura: int, base_points: int, visual: int, desc: str,
               aura_desc: str, notes: str, icon: int, misc_value: int = 0):
    """A debuff the ghost casts (triggered) on every enemy within 100 yd of it (the tomb is about 95 x 120 yd: the
    whole room from any post)."""
    return spell(
        id=spell_id, name=name, school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points,
                        die_sides=1 if base_points else 0, misc_value=misc_value,
                        implicit_target_a=TARGET_SRC_CASTER, implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY,
                        radius_yards=100.0)],
        spell_icon_id=icon, notes=f'{_D21}: {notes}',
        raw_overrides=_raw(desc, aura_desc, visual=visual, instant=True, AttributesEx=ATTR1_NO_THREAT,
                           AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                           AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


def _mark(spell_id: int, name: str, duration_ms: int, visual: int, desc: str, aura_desc: str, notes: str, icon: int,
          hidden: bool = False):
    """A DUMMY debuff the ghost puts (triggered) on one player: the look and the name players read."""
    attributes = ATTR0_AURA_IS_DEBUFF | (ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG if hidden else 0)
    return spell(
        id=spell_id, name=name, school=School.SHADOW, dispel=0, mechanic=0, attributes=attributes, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
        spell_icon_id=icon, notes=f'{_D21}: {notes}',
        raw_overrides=_raw(desc, aura_desc, visual=visual, instant=True, AttributesEx=ATTR1_NO_THREAT,
                           AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                           AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


def _self_aura(spell_id: int, name: str, duration_ms: int, aura: int, base_points: int, visual: int, desc: str,
               aura_desc: str, notes: str, icon: int, misc_value: int = 0, stacks: int = 0, school=School.SHADOW):
    """A buff a ghost casts (triggered) on itself."""
    raw = _raw(desc, aura_desc, visual=visual, instant=True, AttributesEx=ATTR1_NO_THREAT,
               AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP)
    if stacks:
        raw['CumulativeAura'] = stacks
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points,
                        die_sides=1 if base_points else 0, misc_value=misc_value,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=f'{_D21}: {notes}', raw_overrides=raw,
    )


def _refflat_hit(spell_id: int, name: str, school: School, pct: tuple, notes: str, icon: int, *, desc: str,
                 cast_ms: int = 0, range_yards: float = 100.0, visual: int = 0, rider: Effect | None = None,
                 kickable: bool = False, defense: int = _DEFENSE_MAGIC, area: tuple | None = None,
                 dispel: int = 0, aura_desc: str = '', duration_ms: int = 0, aura_flags: int = 0,
                 mechanic: int = 0):
    """A hit worth `pct` hundredths of the reference row (normal, heroic in EffectMiscValueB) on the kit's
    spell_dungeon_refflat_damage; `rider` a second effect (a slow, a root, a stun); `area` (implicit_target_a,
    implicit_target_b, radius) for a cone or a nova; `kickable` a kickable cast (InterruptFlags 15, silence)."""
    target_a, target_b, radius = area if area else (TARGET_UNIT_TARGET_ENEMY, 0, None)
    effects = [Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct[0] - 1, die_sides=1,
                      implicit_target_a=target_a, implicit_target_b=target_b, radius_yards=radius,
                      potency_excluded=_SCRIPT_REFFLAT)]
    if rider:
        effects.append(rider)
    more = dict(_HIT_ATTRS, EffectMiscValueB_1=pct[1], DefenseType=defense)
    if kickable:
        more.update(InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE)
    else:
        more.update(InterruptFlags=0, PreventionType=_PREVENTION_PACIFY if defense == _DEFENSE_MELEE else 0)
    if aura_flags:
        more['AuraInterruptFlags'] = aura_flags
    s = spell(
        id=spell_id, name=name, school=school, dispel=dispel, mechanic=mechanic,
        attributes=ATTR0_AURA_IS_DEBUFF if rider else 0, cast_time_ms=cast_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=range_yards, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon, notes=f'{_D21}: {notes}',
        raw_overrides=_raw(desc, aura_desc, visual=visual, instant=cast_ms == 0, AttributesEx4=ATTR4_NO_CAST_LOG,
                           **more),
    )
    scripted_by(s, 'spell_dungeon_refflat_damage')
    return s


def _slow(pct: int, mechanic: int = _MECHANIC_SNARE) -> Effect:
    """A -pct% movement rider on the hit's target."""
    return Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-(pct + 1),
                  die_sides=1, mechanic=mechanic, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)


# --- TS1 the rotation, TS2 Gather Doom --------------------------------------------------------------------------------

incorporeal_211520 = _self_aura(
    211520, 'Incorporeal', -1, AuraType.MOD_DAMAGE_PERCENT_TAKEN, SHADE_DAMAGE_TAKEN_PCT - 1, TS_SHADE,
    'A shade of the Seven: takes 90% less damage.', 'Incorporeal: damage taken reduced by 90%.',
    'TS1: a shade (the five ghosts not corporeal) carries it until it rises: -90% damage taken, every school '
    f'(MiscValue {_SCHOOL_MASK_ALL}); the hit that still lands comes off the shared pool. The script makes the shade '
    'passive at its post (no attacks, no casts) and the bots\' kill order skips any unit with it (the descriptor\'s '
    'TargetEntry LacksAura and an Attacks hold). Spirit Particles (purple) 28126\'s SV 7566 (a lasting purple ghost '
    'state, VR: the shade look; Gather Doom has its own). Not dispellable, not stealable.',
    _ICON_INCORPOREAL, misc_value=_SCHOOL_MASK_ALL,
)

fade_look_211521 = self_visual(
    211521, 'Incorporeal', TS_SHADE_FADE,
    f'{_D21}, TS1: the flash as a ghost fades back to its post: Incorporeal 54657\'s SV 7707 (the pixie stars, a '
    'one-shot impact). Look only.',
    icon=_ICON_INCORPOREAL,
)


def _gather_doom(spell_id: int, cast_ms: int, heroic: bool):
    which = 'heroic: 2 s every 6 s' if heroic else 'normal: 3 s every 8 s'
    return spell(
        id=spell_id, name='Gather Doom', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=cast_ms,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_SHADOW_BOLT,
        notes=f'{_D21}, TS2 ({which}; the first 3 s after the ghost rises): a corporeal ghost gathers doom. No effect: '
              'when the cast lands (OnSpellCast) the script adds a stack of Gathered Doom (211524); three landed '
              'casts fill the energy and the ghost casts its mood. Interruptible (InterruptFlags 15, PreventionType '
              'silence): a kick or a silence stops that cast\'s energy. The descriptor\'s interrupt list after Vile '
              'Communion, by the ghost\'s rank (Vile\'rel, Doom\'rel, Anger\'rel, Dope\'rel, Hate\'rel, Seeth\'rel, '
              'Gloom\'rel). Shadow school; the mood bars are Physical (rule 5). Shades never cast it. The Shadow Bolt '
              'hands (SV 64, VR\'s pick: Gather Doom\'s own look, not the shades\' purple state).',
        raw_overrides=_raw('Gathers doom. Three gatherings unleash the ghost\'s mood.', visual=TS_GATHER_DOOM_CAST,
                           InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                           DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                           AttributesEx4=ATTR4_NO_CAST_LOG),
    )


gather_doom_211522 = _gather_doom(211522, GATHER_CAST_MS[0], heroic=False)
gather_doom_heroic_211523 = _gather_doom(211523, GATHER_CAST_MS[1], heroic=True)

gathered_doom_211524 = _self_aura(
    211524, 'Gathered Doom', TURN_MS, AuraType.DUMMY, 0, TS_GATHER_DOOM_LANDING,
    'Doom gathers. At three the ghost unleashes its mood.', 'Doom gathers: at 3 stacks the ghost unleashes its mood.',
    'TS2: the energy players read on a corporeal ghost: a stack per landed Gather Doom (DungeonKit::AddStacks, '
    'CumulativeAura 3), removed when the mood bar starts or the ghost fades (a new turn starts empty). Shadow Word: '
    'Pain\'s SV 71 (the chest impact, VR\'s landing look) plays as each stack lands.',
    _ICON_SHADOW_BOLT, stacks=3,
)

# --- TS3 Furious Charge (Anger'rel) -----------------------------------------------------------------------------------

furious_charge_cast_211525 = _mood_bar(
    211525, 'Furious Charge', 'Anger\'rel is about to charge whoever stands far from him.',
    'TS3: Anger\'rel\'s mood bar (3 s). As it starts, the registry\'s 10 yd Stack round him (tag 32, 9 s from the '
    'bar\'s end) tells the bots to collapse on him; when it ends, the 9 s of charges begin.', _ICON_CHARGE)

furious_charge_look_211526 = spell(
    id=211526, name='Furious Charge', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_CHARGE,
    notes=f'{_D21}, TS3: the charge\'s look, cast (triggered) by Anger\'rel at the line\'s end as he charges: '
          'Charge 100\'s SV 867 (ChargeTrail and the landing dust). Look only: the registry\'s line owns the hit.',
    raw_overrides=_raw(visual=TS_FURIOUS_CHARGE, instant=True, Targets=_TARGET_FLAG_DEST_LOCATION,
                       AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                       AttributesEx4=ATTR4_NO_CAST_LOG),
)

furious_charge_211527 = resolve_copy(
    211527, 'Furious Charge', School.NORMAL, 'Anger\'rel tramples everyone in his path.',
    f'{_D21}, TS3: a charge line\'s hit. For 9 s after his bar, every 3 s Anger\'rel charges the farthest player more '
    'than 10 yd away: a 3 yd line from him to 2 yd past them (shown 1 s), 30% (heroic 45%) of the row and 1 Weakened '
    'on the target and anyone in it (registry tag 31). Nobody beyond 10 yd: a harmless stomp. Copy of the resolve '
    'spell 205001 (Physical).',
    icon=_ICON_CHARGE,
)

furious_stomp_211528 = self_visual(
    211528, 'Furious Stomp', _look('TS_FURIOUS_STOMP'),
    f'{_D21}, TS3: Anger\'rel stomps (harmlessly) when nobody stands beyond 10 yd at a charge: War Stomp\'s SV 2355 '
    '(until V-2 names TS_FURIOUS_STOMP). Look only.',
    icon=_ICON_WAR_STOMP,
)

# --- TS4 Seething Cold (Seeth'rel) ------------------------------------------------------------------------------------

seething_cold_cast_211529 = _mood_bar(
    211529, 'Seething Cold', 'Seeth\'rel draws the cold of the tomb. Huddle together!',
    'TS4: Seeth\'rel\'s mood bar (3 s). As it starts, the registry\'s anchorless Stack (6 yd, Cluster(2): each '
    'player needs 2 others within 6 yd; G2\'s `loner` row, tag 22) for 10 s from the bar\'s end.', _ICON_FROST)

seething_cold_211530 = _refflat_hit(
    211530, 'Seething Cold', School.FROST, COLD_PCT,
    'TS4: a loner\'s tick. For 10 s after the bar, every second Seeth\'rel casts it (triggered) on each player not '
    'within 6 yd of 2 others (TheSevenLogic.h Loners, the registry\'s Cluster(2) rule): 6% (heroic 10%) of the row '
    f'(hundredths {COLD_PCT[0]}, EffectMiscValueB {COLD_PCT[1]}) and -30% speed for 1.5 s (re-applied by every '
    'tick, so it ends just after the player joins two others). Chilled 6136\'s SV 675 (the ice head state) on the '
    'slow. Cannot crit, always hits, ignores his modifiers.',
    _ICON_FROST, desc='Frost damage and movement slowed by $s2%.', aura_desc='Movement slowed by $s2%.',
    visual=TS_SEETHING_COLD, rider=_slow(COLD_SLOW_PCT), duration_ms=COLD_SLOW_MS,
)

# --- TS5 Dopey Haze (Dope'rel) ----------------------------------------------------------------------------------------

dopey_haze_cast_211531 = _mood_bar(
    211531, 'Dopey Haze', 'Dope\'rel\'s haze is coming. Hold still!',
    'TS5: Dope\'rel\'s mood bar (3 s). As it starts, the registry\'s HoldStill on everyone (6 s window from the bar\'s '
    'end, tolerance 0.5 yd, tag 33): the bots stop where they stand.', _ICON_DAZED)

dopey_haze_211532 = _room_aura(
    211532, 'Dopey Haze', HAZE_MS, AuraType.DUMMY, 0, TS_DOPEY_HAZE,
    'Moving makes you stumble.', 'Dopey: moving makes you stumble.',
    'TS5: the haze on every player for the 6 s after the bar (the look and the name; the script judges the movement): '
    'Dazed 1604\'s SV 84 (the yellow stars state). Not dispellable.', _ICON_DAZED,
)

stumble_211533 = _refflat_hit(
    211533, 'Stumble', School.NORMAL, STUMBLE_PCT,
    'TS5: a stumble. Each second of the haze, a player who moved more than 0.5 yd since the last second takes it '
    f'(triggered, from Dope\'rel): 15% (heroic 25%) of the row (hundredths {STUMBLE_PCT[0]}, EffectMiscValueB '
    f'{STUMBLE_PCT[1]}) and 1 Weakened (the script, BossMechanics::Weakened). Cannot crit, always hits.',
    _ICON_DAZED, desc='You stumble.',
)

# --- TS6 Gloom (Gloom'rel) --------------------------------------------------------------------------------------------

gloom_cast_211534 = _mood_bar(
    211534, 'Gloom', 'Gloom\'rel\'s despair fills the tomb.',
    'TS6: Gloom\'rel\'s mood bar (3 s); at its end Gloom (211535) on every player and Recklessness (211536) on him.',
    _ICON_CURSE)

gloom_211535 = _room_aura(
    211535, 'Gloom', GLOOM_MS, AuraType.MOD_HEALING_PCT, GLOOM_HEALING_PCT - 1, TS_GLOOM_HEALING_MARK,
    'Healing received reduced by 50%.', 'Healing received reduced by 50%.',
    'TS6: every player for 12 s: healing received -50% (MOD_HEALING_PCT). The tank and healer load of the mood. The '
    'lasting keening skull (SV 90506, shipped; VR: SV 7374 marks nobody). Not dispellable.', _ICON_CURSE,
)

recklessness_211536 = _self_aura(
    211536, 'Recklessness', GLOOM_MS, AuraType.MOD_DAMAGE_PERCENT_DONE, RECKLESSNESS_PCT - 1,
    TS_GLOOM_RELS_RECKLESSNESS, 'Damage done increased by 50%.', 'Damage done increased by 50%.',
    'TS6: Gloom\'rel for 12 s: +50% damage done, every school (MiscValue 127). Recklessness 1719\'s SV 236. Not '
    'purgeable (the stock Recklessness is an Enrage; this one is a mood).', _ICON_RECKLESSNESS,
    misc_value=_SCHOOL_MASK_ALL, school=School.NORMAL,
)

# --- TS7 Vile Communion (Vile'rel) ------------------------------------------------------------------------------------

vile_communion_cast_211537 = _mood_bar(
    211537, 'Vile Communion', 'Vile\'rel calls on his brothers.',
    'TS7: Vile\'rel\'s mood bar (3 s, not interruptible); at its end the channel (211538), which is.', _ICON_PRAYER)

vile_communion_211538 = spell(
    id=211538, name='Vile Communion', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=VILE_CHANNEL_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_PRAYER,
    notes=f'{_D21}, TS7: Vile\'rel\'s 6 s self channel (SPELL_ATTR1_IS_SELF_CHANNELED, the Patty Cake precedent): the '
          'script heals the shared pool a sixth of 5% (heroic 8%) a second while it lasts (SharedHealthPool '
          'RestorePct). Kickable: ChannelInterruptFlags 0x08 and PreventionType silence; any interrupt stops the rest. '
          'The descriptor\'s interrupt list, first (priority 9; a reward on normal, expected on heroic). Holy school: '
          'no Gather Doom kick locks it out. Prayer of Healing 596\'s SV 194 (cast again at 3 s, 211539).',
    raw_overrides=_raw('Heals the Seven.', 'Channeling.', visual=TS_VILE_COMMUNION, CastingTimeIndex=1,
                       AttributesEx=_ATTR1_IS_SELF_CHANNELED | ATTR1_NO_THREAT,
                       ChannelInterruptFlags=_CHANNEL_INTERRUPT_KICK, InterruptFlags=0,
                       PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                       AttributesEx4=ATTR4_NO_CAST_LOG),
)

vile_communion_look_211539 = self_visual(
    211539, 'Vile Communion', TS_VILE_COMMUNION,
    f'{_D21}, TS7: the healing hands again 3 s into the channel (VR: the cast kit is one flash on a 6 s channel): '
    'Prayer of Healing 596\'s SV 194. Look only.',
    icon=_ICON_PRAYER,
)

# --- TS8 Hatred (Hate'rel) --------------------------------------------------------------------------------------------

hatred_cast_211540 = _mood_bar(
    211540, 'Hatred', 'Hate\'rel\'s hatred spreads. Get away from each other!',
    'TS8: Hate\'rel\'s mood bar (3 s). As it starts, the first of eight registry Spreads (6 yd, a second apart, tag '
    '34); the mark (211541) on every player at its end.', _ICON_SHADOW_MARK)

hatred_mark_211541 = _room_aura(
    211541, 'Hatred', HATRED_MS, AuraType.DUMMY, 0, TS_HATRED,
    'Players within 6 yards of another player suffer Shadow damage every second.',
    'Hatred: stay 6 yards from everyone.',
    'TS8: every player for the 8 s of Hatred (the look and the name; the registry\'s Spreads judge and hit): the '
    'purple rune ring under each (SV 90657, minted; VR: Shadow Mark\'s SV 223 is a dust whirl). Not dispellable.',
    _ICON_SHADOW_MARK,
)

hatred_211542 = resolve_copy(
    211542, 'Hatred', School.SHADOW, 'Hatred burns those who stand together.',
    f'{_D21}, TS8: a tick of Hatred: for 8 s after the bar, every second each player within 6 yd of another player '
    'takes 5% (heroic 8%) of the row (a registry Spread a second, tag 34; the tank too, ruling 88). Copy of the '
    'resolve spell 205006 (Shadow).',
    icon=_ICON_SHADOW_MARK,
)

# --- TS9 Doom (Doom'rel) ----------------------------------------------------------------------------------------------

doom_cast_211543 = _mood_bar(
    211543, 'Doom', 'Doom\'rel seals someone\'s doom.',
    'TS9: Doom\'rel\'s mood bar (3 s); at its end 1 (heroic 2) random players, the tank included (ruling 88), are '
    'marked for 6 s.', _ICON_DOOM)

doom_211544 = _mark(
    211544, 'Doom', DOOM_MARK_MS, TS_DOOM_MARK,
    'Doomed: in 6 seconds a blast hits everyone within 10 yards.', 'Doomed: run away from everyone.',
    'TS9: the 6 s mark on a doomed player (the registry\'s RunOut, 10 yd, tag 35, is the job): the lasting keening '
    'skull (SV 90506, shipped; VR: Curse of Doom\'s SV 5019 shows only once). Not dispellable.', _ICON_DOOM,
)

doom_ring_211545 = _mark(
    211545, 'Doom', DOOM_MARK_MS, TS_DOOM_MARK_RING, '', '',
    'TS9: the doomed player\'s purple rune ring for the 6 s (SV 90657, minted), a hidden aura beside the skull.',
    _ICON_DOOM, hidden=True,
)

doom_blast_211546 = resolve_copy(
    211546, 'Doom', School.SHADOW, 'Doom bursts from the doomed.',
    f'{_D21}, TS9: the blast on the others: 6 s after the mark, everyone within 10 yd of a doomed player takes 30% '
    '(heroic 45%) of the row and 1 Weakened (the registry\'s RunOut, tag 35). Copy of the resolve spell 205006 '
    '(Shadow).',
    icon=_ICON_DOOM,
)

doom_blast_self_211547 = _refflat_hit(
    211547, 'Doom', School.SHADOW, DOOM_SELF_PCT,
    'TS9: the blast on the doomed player, as the RunOut resolves (triggered, from Doom\'rel): 20% (heroic 30%) of the '
    f'row (hundredths {DOOM_SELF_PCT[0]}, EffectMiscValueB {DOOM_SELF_PCT[1]}). Cannot crit, always hits. Its look '
    'waits for V-2\'s TS_DOOM_BLAST (shared-file request).',
    _ICON_DOOM, desc='Doom bursts from you.', visual=_look('TS_DOOM_BLAST'),
)

# --- the kept kits' copies (rule 15) ----------------------------------------------------------------------------------

frostbolt_211548 = _refflat_hit(
    211548, 'Frostbolt', School.FROST, FROSTBOLT_PCT,
    'Seeth\'rel\'s Frostbolt: the stock 12675 (3 s, 143-193 Frost and -50% speed for 4 s) rescaled (rule 15: a copy). '
    f'On his victim, the stock 3.4-4.8 s cadence: 6% (heroic 8%) of the row (gap 36, designer question 2) and the '
    'stock slow. Kickable as the stock one, but "never kick" on the descriptor (the bots keep their kicks for Gather '
    'Doom). The slow is Magic.',
    _ICON_FROSTBOLT, desc='Frost damage and movement slowed by $s2% for $d.', aura_desc='Movement slowed by $s2%.',
    cast_ms=3000, range_yards=40.0, visual=_look('TS_FROSTBOLT'), rider=_slow(50), kickable=True,
    dispel=_DISPEL_MAGIC, duration_ms=4000,
)

cone_of_cold_211549 = _refflat_hit(
    211549, 'Cone of Cold', School.FROST, CONE_OF_COLD_PCT,
    'Seeth\'rel\'s Cone of Cold: the stock 15244 (a 53 degree, 10 yd cone, 132-168 Frost, -50% speed 8 s) rescaled '
    '(rule 15). At 9-14 s after his rise, then every 19-24 s: 8% (heroic 10%) of the row and the stock slow.',
    _ICON_CONE_OF_COLD, desc='Frost damage in a cone and movement slowed by $s2% for $d.',
    aura_desc='Movement slowed by $s2%.', visual=_look('TS_CONE_OF_COLD'),
    rider=Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-51, die_sides=1,
                 mechanic=_MECHANIC_SNARE, implicit_target_a=_TARGET_UNIT_CONE_ENEMY_24, radius_yards=10.0),
    area=(_TARGET_UNIT_CONE_ENEMY_24, 0, 10.0), range_yards=RANGE_SELF, dispel=_DISPEL_MAGIC, duration_ms=8000,
)

frost_nova_211550 = _refflat_hit(
    211550, 'Frost Nova', School.FROST, FROST_NOVA_PCT,
    'Seeth\'rel\'s Frost Nova, TS10: the stock 12674 (98-112 Frost and an 8 s root within 10 yd) with the root cut to '
    '2 s (ruling 73, the 2 s rule). At 12-16 s after his rise, then every 20-23 s: 6% (heroic 8%) of the row and the '
    '2 s root on everyone within 10 yd (the tank too). The root is Magic: the descriptor\'s dispel list (a reward).',
    _ICON_FROST_NOVA, desc='Frost damage and roots enemies within $a1 yards for $d.', aura_desc='Frozen in place.',
    visual=_look('TS_FROST_NOVA'),
    rider=Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, base_points=0, die_sides=0,
                 mechanic=_MECHANIC_ROOT, implicit_target_a=TARGET_SRC_CASTER,
                 implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=FROST_NOVA_RADIUS),
    area=(TARGET_SRC_CASTER, TARGET_UNIT_SRC_AREA_ENEMY, FROST_NOVA_RADIUS), range_yards=RANGE_SELF,
    dispel=_DISPEL_MAGIC, duration_ms=FROST_NOVA_ROOT_MS,
)

backstab_211551 = _refflat_hit(
    211551, 'Backstab', School.NORMAL, BACKSTAB_PCT,
    'Dope\'rel\'s Backstab: the stock 15582 (weapon + 30, from behind) is on DD\'s double-use list (rule 15: a copy, '
    'handoff s2.3). Cast only from behind his victim (the script checks), 3-7 s after his rise, then every 5-9 s: 12% '
    '(heroic 15%) of the row. Cannot crit, always hits, ignores his modifiers.',
    _ICON_BACKSTAB, desc='Stabs the target from behind.', visual=_look('TS_BACKSTAB'), range_yards=5.0,
    defense=_DEFENSE_MELEE,
)

rupture_211552 = spell(
    id=211552, name='Rupture', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_BLEED,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=5.0, duration_ms=10_000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=RUPTURE_PCT[0] - 1,
                    die_sides=1, amplitude=2000, mechanic=_MECHANIC_BLEED,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT_TICK)],
    spell_icon_id=_ICON_RUPTURE,
    notes=f'{_D21}: Dope\'rel\'s Rupture: the stock 15583 (30 every 2 s for 10 s, a bleed) rescaled (rule 15). On his '
          'victim 2-4 s after his rise, then every 14-16 s: 2% (heroic 3%) of the row a tick (hundredths '
          f'{RUPTURE_PCT[0]}, EffectMiscValueB {RUPTURE_PCT[1]}), five ticks.',
    raw_overrides=_raw('Bleeds the target.', 'Bleeding.', visual=_look('TS_RUPTURE'), instant=True,
                       EffectMiscValueB_1=RUPTURE_PCT[1], DefenseType=_DEFENSE_MELEE,
                       PreventionType=_PREVENTION_PACIFY, AttributesEx4=ATTR4_NO_CAST_LOG, **_HIT_ATTRS),
)
scripted_by(rupture_211552, 'spell_dungeon_refflat_periodic')

gouge_211553 = _refflat_hit(
    211553, 'Gouge', School.NORMAL, GOUGE_PCT,
    'Dope\'rel\'s Gouge, TS10: the stock 12540 (20 damage and a 4 s incapacitate on a random non-tank) with the '
    'incapacitate cut to 2 s, on any player, the tank included (ruling 90). 8-10 s after his rise, then every 9-15 s: '
    '3% (heroic 4%) of the row and a 2 s incapacitate (MOD_STUN, Knockout) that breaks on damage (stock).',
    _ICON_GOUGE, desc='Incapacitates the target for $d.', aura_desc='Incapacitated.', visual=_look('TS_GOUGE'),
    rider=Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0, die_sides=0,
                 mechanic=_MECHANIC_KNOCKOUT, implicit_target_a=TARGET_UNIT_TARGET_ENEMY),
    range_yards=5.0, defense=_DEFENSE_MELEE, duration_ms=GOUGE_MS, aura_flags=_AURA_INTERRUPT_DAMAGE,
    mechanic=_MECHANIC_KNOCKOUT,
)

mind_blast_211554 = _refflat_hit(
    211554, 'Mind Blast', School.SHADOW, MIND_BLAST_PCT,
    'Vile\'rel\'s Mind Blast: the stock 15587 (1.5 s, 139-161 Shadow) rescaled (rule 15). On his victim, the stock '
    '3.4-4.8 s cadence: 8% (heroic 10%) of the row. Kickable, "never kick" on the descriptor.',
    _ICON_MIND_BLAST, desc='Shadow damage.', cast_ms=1500, range_yards=30.0, visual=_look('TS_MIND_BLAST'),
    kickable=True,
)

shadow_bolt_211555 = _refflat_hit(
    211555, 'Shadow Bolt', School.SHADOW, SHADOW_BOLT_PCT,
    'Hate\'rel\'s Shadow Bolt: the stock 15232 (3 s, 192-258 Shadow) is on DD\'s double-use list (rule 15: a copy). On '
    'his victim every 8-10 s (was 3.4-4.8 s, ruling 73) and on a random player 14-17 s after his rise, then every '
    '15-20 s (the dead self-targeted row is gone): 12% (heroic 15%) of the row. Kickable, "never kick" on the '
    'descriptor.',
    _ICON_SHADOW_BOLT, desc='Shadow damage.', cast_ms=3000, range_yards=40.0, visual=_look('TS_SHADOW_BOLT'),
    kickable=True,
)

shadow_bolt_volley_211556 = _refflat_hit(
    211556, 'Shadow Bolt Volley', School.SHADOW, VOLLEY_PCT,
    'Doom\'rel\'s Shadow Bolt Volley: the stock 15245 (3 s, 128-172 Shadow on everyone within 30 yd) rescaled (rule '
    '15). 10 s after his rise, then every 12 s: 8% (heroic 10%) of the row on everyone within 30 yd (a group pulse, '
    'the BRS convention). Kickable, "never kick" on the descriptor.',
    _ICON_SHADOW_BOLT, desc='Shadow damage to enemies within $a1 yards.', cast_ms=3000,
    visual=_look('TS_SHADOW_BOLT_VOLLEY'), kickable=True,
    area=(TARGET_SRC_CASTER, TARGET_UNIT_SRC_AREA_ENEMY, VOLLEY_RADIUS), range_yards=RANGE_SELF,
)

immolate_211557 = spell(
    id=211557, name='Immolate', school=School.FIRE, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=2000, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=30.0, duration_ms=21_000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=IMMOLATE_TICK_PCT[0] - 1,
               die_sides=1, amplitude=3000, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
               potency_excluded=_SCRIPT_REFFLAT_TICK),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=IMMOLATE_PCT[0] - 1, die_sides=1,
               implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
    ],
    spell_icon_id=_ICON_IMMOLATE,
    notes=f'{_D21}: Doom\'rel\'s Immolate: the stock 12742 (2 s, 96 Fire and 28 every 3 s for 21 s) rescaled '
          '(rule 15), and the stock rescheduling bug fixed (S4 "Notes": one cast every 25 s, not a retry every '
          'second). On a random player 18 s after his rise, then every 25 s: 8% (heroic 10%) of the row and 2% '
          f'(heroic 3%) every 3 s (hundredths {IMMOLATE_PCT[0]} / {IMMOLATE_TICK_PCT[0]}, EffectMiscValueB '
          f'{IMMOLATE_PCT[1]} / {IMMOLATE_TICK_PCT[1]}). Magic (dispellable, not on the list). Kickable, "never '
          'kick" on the descriptor.',
    raw_overrides=_raw('Burns the target.', 'Burning.', visual=_look('TS_IMMOLATE'),
                       InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                       DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=IMMOLATE_TICK_PCT[1],
                       EffectMiscValueB_2=IMMOLATE_PCT[1], AttributesEx4=ATTR4_NO_CAST_LOG, **_HIT_ATTRS),
)
scripted_by(immolate_211557, 'spell_dungeon_refflat_damage', 'spell_dungeon_refflat_periodic')
