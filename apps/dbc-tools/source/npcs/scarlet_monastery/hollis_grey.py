"""
Scarlet Monastery build WP-D7: Lector Hollis Grey <Keeper of the Index>, the Librarian (Hollis Grey 300913, Cursed Book
300914, Infernal 300915, Spiderling 300916, Spectral Troll 300917, Phantom Grunt 300918)
(.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D7, s7 #26 A; build spec
docs/dungeons/scarlet-monastery-2-library.md "Lector Hollis Grey, the Librarian", LB1-LB9). WP-D7 owns this file (its
spells: kSpellsHollisGrey 212610-212669 of modules/mod-dungeon-bosses src/ScarletMonastery/ScarletMonasteryRework.h;
HollisGreyLogic.h names the same ids and numbers, lib/test_scarlet_monastery_hollis_grey.py pins both). The spawn in
the pocket (254.8, -389.2) and the texts are the core SQL rev rev_hollis_grey_scarlet_monastery.sql.

- 300913 Lector Hollis Grey: a new boss, bound to boss_lector_hollis_grey_rework (SmHollisGrey::kBound flipped in the
  same change), level 35 mage, elite, normal 36k (HealthModifier 39.911 on the level 35 mage base 902), stun immune
  (1972), INSTANCE_BIND (FD-SM's credit_creature(300913), DungeonEncounter 1077), DamageModifier 2.4 (Arcanist Doan's,
  the hall's other level 35 mage boss), the Scarlet Abbot's display 2492. His loot is L-1's (lootid 300913). Heroic
  220k and the tier's melee are WP-H's (source/world/dungeons/scarlet_monastery.py).
- 300914 Cursed Book: the kill target (LB1), rooted and passive, hanging 1.2 yd over the floor; 3.5k (heroic 15k).
  The closed book CDI 28103 at scale 3 (never the doc's Argent Tome 21955: a Rabbit). Not a humanoid (type 10: no
  Polymorph). No loot, no XP.
- 300915 Infernal (LB3): a tanked demon, 4k (heroic 20k), Immolation 2% a 2 s within 5 yd (gap 12: this WP's
  default), DamageModifier 2.0 (about 62 a 2 s swing on a level 35 tank: 3% of the tank row; rule 19). CDI 169.
- 300916 Spiderling (LB2): AoE fodder, 500 (heroic 2.5k), DamageModifier 0.5. CDI 9756 at scale 0.5.
- 300917 Spectral Troll (LB4), 300918 Phantom Grunt (LB7): not targetable looks (KIT_HELPER), the ghostly troll CDI
  29716 and the ghost orc CDI 17459 (both stock, alpha in the display). They throw and charge; the registry owns
  the hits.

Every combat unit is level 35, his level, so a percent hit cast by a book or an Infernal reads his reference row
(rule 2); the HealthModifiers are on the level 35 bases (mage 902, warrior 1,220) and give the build spec's health.

Spells (looks from ._visuals, WP-V's LB_* picks; every look unconfirmed until seen in game):

  212610  Open the Index        LB1 normal: the 2 s bar, Arcane, not interruptible (a must-play bar)
  212611  Open the Index        LB1 heroic: the 3 s cast, Arcane, a kick (missed: the book opens on page 2)
  212612  Turning the Page      LB1a the book's page count (stacks, CumulativeAura 10); the kill order reads it
  212613  Reader's Ward         LB1b -25% damage taken a stack, 3 stacks (the kit's WardOfTheLiving holds 2 / 3)
  212614  War of the Spider     the book's story (a DUMMY buff with the open-book glow); 212615-212619 the others
  212620  Web Spray             LB2 look: the spray flying from the book to the web
  212621  Web                   LB2 the web's 50% slow, 1.5 s, the zone's rider every second inside
  212622  Web                   LB2 look: the 6 yd web patch (lasting STATE on a stalker)
  212623  Hatch Spiderlings     LB2 look: the hatch on the web
  212624  Meteor                LB3 the meteor's hit (resolve copy, Fire)
  212625  Inferno               LB3 look: the falling infernal over the spot
  212626  Immolation            LB3 the Infernal's burn, 5 yd round it (refflat)
  212627  Throw Axe             LB4 an axe line's hit (resolve copy, Physical)
  212628  Throw Axe             LB4 look: the axe in flight, troll -> player
  212629  Titan Stomp           LB5 a ring's hit (resolve copy, Physical)
  212630  War Stomp             LB5 look: the stomp (the first ring)
  212631  Ground Slam           LB5 look: each later ring
  212632  Dream Mist            LB6 look: the 6 yd mist rung (STATE); 212633 9 yd, 212634 12 yd
  212635  Drowsy                LB6 the stacking slow (movement and casting -10% a stack, 5 stacks)
  212636  Dreamless Sleep       LB6 the 2 s sleep at 5 stacks (and a missed Dreaming)
  212637  Dreaming              LB6a heroic: the 6 s Magic debuff (spell_sm_hollis_dreaming)
  212638  Phantom Charge        LB7 the charge line's hit (resolve copy, Physical)
  212639  Charge                LB7 look: the grunt's charge trail
  212640  Searing Rebuke        LB8 the 2.5 s tank hit, Holy, 20% / 30% of the tank row (refflat), a kick
  212641  Burning Book          LB9 heroic: the fire's tick (resolve copy, Fire)
  212642  Burning Book          LB9 look: the 5 yd fire (the shipped lava rung, STATE on a stalker)
  212643  Dream Mist            LB6 the mist's tick (resolve copy, Nature; no damage: the Drowsy rider)
  212644  Web                   LB2 the web's tick (resolve copy, Physical; no damage: the slow rider)
  212645-212669 spare
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
    self_visual,
    standing_in_it,
)
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    CURSED_BOOK_SCALE_RANGE,
    DISPLAY_CURSED_BOOK,
    DISPLAY_GHOST_ORC_GRUNT,
    DISPLAY_HOLLIS_GREY,
    DISPLAY_INFERNAL,
    DISPLAY_SPIDERLING,
    DISPLAY_TROLL_AXE_THROWER,
    LB_AXES,
    LB_BURNING_BOOK,
    LB_GRUNT_CHARGE,
    LB_METEOR,
    LB_OPEN_BOOK,
    LB_REBUKE,
    LB_SLEEP,
    LB_STOMP,
    LB_STOMP_RINGS,
    LB_WARD,
    LB_WEB,
    LB_WEB_HATCH,
    LB_WEB_SPRAY,
    SPIDERLING_SCALE,
    SV_DREAM_MIST,
)

_D7 = 'Scarlet Monastery build WP-D7 (Lector Hollis Grey)'
_SCRIPT_REFFLAT = ('Scarlet Monastery: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

# --- constants (HollisGreyLogic.h; lib/test_scarlet_monastery_hollis_grey.py pins each against the header) -----------

LEVEL = 35
HOLLIS_GREY = 300913
CURSED_BOOK = 300914
INFERNAL = 300915
SPIDERLING = 300916
SPECTRAL_TROLL = 300917
PHANTOM_GRUNT = 300918

# Health (handoff s3.6) on the level 35 bases: mage 902 (him), warrior 1,220 (the adds).
BOSS_HEALTH_MODIFIER = 39.911               # 902 x 39.911 = 36,000 (kBossHealth normal)
BOOK_HEALTH_MODIFIER = 2.868853             # 1,220 x 2.868853 = 3,500 (kBookHealth)
INFERNAL_HEALTH_MODIFIER = 3.278689         # 1,220 x 3.278689 = 4,000 (kInfernalHealth)
SPIDERLING_HEALTH_MODIFIER = 0.409836       # 1,220 x 0.409836 = 500 (kSpiderlingHealth)
BOSS_DAMAGE_MODIFIER = 2.4                  # Arcanist Doan's (the hall's other level 35 mage boss)
INFERNAL_DAMAGE_MODIFIER = 2.0
SPIDERLING_DAMAGE_MODIFIER = 0.5

# Heroic templates (WP-H's lock lines in source/world/heroic_ids.lock, minted when scarlet_monastery.py lists these
# entries; None until H reports them: the row then names no difficulty_entry_1 and generate.py --check says so).
HOLLIS_GREY_HEROIC = 310469
CURSED_BOOK_HEROIC = 310470
INFERNAL_HEROIC = 310471
SPIDERLING_HEROIC = 310472

OPEN_CAST_MS = (2000, 3000)                 # kOpenCastMs
PAGE_STACKS = 10                            # kMaxShownPage
WARD_PCT = 25                               # kWardPctPerBook
WARD_STACKS = 3                             # kWardCapPct heroic 75 / 25
WEB_SLOW_PCT = 50                           # kWebSlowPct
WEB_SLOW_MS = 1500                          # refreshed every 1 s tick inside (kWebTickMs)
IMMOLATION = (200, 200)                     # kImmolationPct 2 / 2 (hundredths)
IMMOLATION_RADIUS = 5.0                     # kImmolationRadiusYd
DROWSY_PCT = 10                             # kDrowsyPct
DROWSY_STACKS = 5                           # kDrowsyMaxStacks
DROWSY_MS = 30000                           # the boss takes a stack off a second outside the mist
DREAM_SLEEP_MS = 2000                       # kDreamSleepMs
DREAMING_MS = 6000                          # kDreamingMs
REBUKE = (2000, 3000)                       # kRebukePct 20 / 30 (hundredths)
REBUKE_CAST_MS = 2500                       # kRebukeCastMs
REBUKE_RANGE = 40.0

_FLAGS_EXTRA_NO_XP = 0x40
_CREATURE_TYPE_BEAST = 1
_CREATURE_TYPE_DEMON = 3
_CREATURE_TYPE_NOT_SPECIFIED = 10
_UNIT_CLASS_WARRIOR = 1
_UNIT_CLASS_MAGE = 8
_RANK_ELITE = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_SPELL_INTERRUPT_FLAGS_KICK = 15
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_DISPEL_MAGIC = 1
_MECHANIC_SLEEP = 10
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127

# Stock icons (Spell.dbc SpellIconID of the named spell).
_ICON_BOOK = 191                # Pet Book Graphic 35720
_ICON_WEB_SPRAY = 272           # Web Spray 29484
_ICON_WEB = 69                  # Web 745
_ICON_HATCH = 976               # Hatch Spiderlings 43134
_ICON_INFERNO = 460             # Inferno 1122, Immolation 20153
_ICON_AXE = 1529                # Throw Axe 16075
_ICON_WAR_STOMP = 50            # War Stomp 11876
_ICON_GROUND_SLAM = 2144        # Ground Slam 33525
_ICON_SLEEP = 44                # Dreamless Sleep 15822
_ICON_CHARGE = 457              # Charge 100
_ICON_SMITE = 237               # Holy Smite 9481
_ICON_FLAME_PATCH = 876         # Flame Patch 35383
_ICON_GENERIC = 1

_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
    AttributesEx2=ATTR2_CANT_CRIT | ATTR2_IGNORE_LINE_OF_SIGHT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
    AttributesEx4=ATTR4_NO_CAST_LOG,
)


def _heroic(entry):
    return {'difficulty_entry_1': entry} if entry else {}


# --- 300913 Lector Hollis Grey ---------------------------------------------------------------------------------------

# The entries are written as numbers: source/world/dungeons/scarlet_monastery.py finds the declared kit adds by the
# pattern `creature_template(<entry>, ...)` (WP-H) and gives them their heroic health.
hollis_grey_300913 = creature_template(300913, 'Lector Hollis Grey', **{
    **KIT_CREATURE,
    **boss_columns('boss_lector_hollis_grey_rework', BOSS_HEALTH_MODIFIER, damage_modifier=BOSS_DAMAGE_MODIFIER),
    'subname': 'Keeper of the Index', 'minlevel': LEVEL, 'maxlevel': LEVEL, 'rank': _RANK_ELITE,
    'unit_class': _UNIT_CLASS_MAGE, 'unit_flags': 0, 'ManaModifier': 3.0, 'BaseAttackTime': 2000,
    'lootid': HOLLIS_GREY, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 230, 'maxgold': 770,
    **_heroic(HOLLIS_GREY_HEROIC),
})
creature_model(HOLLIS_GREY, display_id=DISPLAY_HOLLIS_GREY)

# --- 300914 Cursed Book -----------------------------------------------------------------------------------------------

cursed_book_300914 = creature_template(300914, 'Cursed Book', **{
    **KIT_CREATURE, 'type': _CREATURE_TYPE_NOT_SPECIFIED, 'minlevel': LEVEL, 'maxlevel': LEVEL, 'rank': 0,
    'unit_class': _UNIT_CLASS_WARRIOR, 'unit_flags': 0, 'HealthModifier': BOOK_HEALTH_MODIFIER,
    'DamageModifier': 0.0, 'detection_range': 0.0, 'CreatureImmunitiesId': 0, 'lootid': 0, 'pickpocketloot': 0,
    'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'ScriptName': 'npc_sm_cursed_book', **_heroic(CURSED_BOOK_HEROIC),
})
creature_model(CURSED_BOOK, display_id=DISPLAY_CURSED_BOOK, scale=CURSED_BOOK_SCALE_RANGE[0])

# --- 300915 Infernal, 300916 Spiderling -------------------------------------------------------------------------------

infernal_300915 = creature_template(300915, 'Infernal', **{
    **KIT_CREATURE, 'type': _CREATURE_TYPE_DEMON, 'minlevel': LEVEL, 'maxlevel': LEVEL, 'rank': 0,
    'unit_class': _UNIT_CLASS_WARRIOR, 'unit_flags': 0, 'HealthModifier': INFERNAL_HEALTH_MODIFIER,
    'DamageModifier': INFERNAL_DAMAGE_MODIFIER, 'BaseAttackTime': 2000, 'CreatureImmunitiesId': 0, 'lootid': 0,
    'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'ScriptName': 'npc_sm_hollis_story_add', **_heroic(INFERNAL_HEROIC),
})
creature_model(INFERNAL, display_id=DISPLAY_INFERNAL)

spiderling_300916 = creature_template(300916, 'Spiderling', **{
    **KIT_CREATURE, 'type': _CREATURE_TYPE_BEAST, 'minlevel': LEVEL, 'maxlevel': LEVEL, 'rank': 0,
    'unit_class': _UNIT_CLASS_WARRIOR, 'unit_flags': 0, 'HealthModifier': SPIDERLING_HEALTH_MODIFIER,
    'DamageModifier': SPIDERLING_DAMAGE_MODIFIER, 'BaseAttackTime': 2000, 'speed_run': 1.14286,
    'CreatureImmunitiesId': 0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
    'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_sm_hollis_story_add', **_heroic(SPIDERLING_HEROIC),
})
creature_model(SPIDERLING, display_id=DISPLAY_SPIDERLING, scale=SPIDERLING_SCALE)

# --- 300917 Spectral Troll, 300918 Phantom Grunt (looks) --------------------------------------------------------------

spectral_troll_300917 = creature_template(300917, 'Spectral Troll', **{
    **KIT_HELPER, 'minlevel': LEVEL, 'maxlevel': LEVEL, 'type': 6, 'ScriptName': 'npc_sm_hollis_phantom',
})
creature_model(SPECTRAL_TROLL, display_id=DISPLAY_TROLL_AXE_THROWER)

phantom_grunt_300918 = creature_template(300918, 'Phantom Grunt', **{
    **KIT_HELPER, 'minlevel': LEVEL, 'maxlevel': LEVEL, 'type': 6, 'ScriptName': 'npc_sm_hollis_phantom',
})
creature_model(PHANTOM_GRUNT, display_id=DISPLAY_GHOST_ORC_GRUNT)


# --- builders ---------------------------------------------------------------------------------------------------------

def _lasting(spell_id: int, name: str, visual: int, notes: str, *, icon: int = _ICON_GENERIC, shown: bool = False,
             desc: str = '', stacks: int = 0, school: School = School.NORMAL):
    """A lasting DUMMY aura the caster puts on itself (no duration): a story on its book, a page count, a ground look
    on a stalker. `shown`: a buff players read (else DO_NOT_DISPLAY | DO_NOT_LOG). `visual`: its STATE kit (0: none)."""
    raw = kit_raw(desc, desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    if stacks:
        raw['CumulativeAura'] = stacks
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0,
        attributes=0 if shown else ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _missile(spell_id: int, name: str, visual: int, speed: float, notes: str, *, icon: int = _ICON_GENERIC):
    """A look that flies from its caster to a unit (a DUMMY on any unit, DO_NOT_DISPLAY | DO_NOT_LOG, no threat),
    triggered. Never a hit: the registry's mechanic owns it."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Speed=speed, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- LB1 Open the Index, LB1a Turning the Page, LB1b Reader's Ward ----------------------------------------------------

open_the_index_212610 = cast_bar(
    212610, 'Open the Index', OPEN_CAST_MS[0], 'Opens a forbidden book from the Index.',
    f'{_D7}, LB1 normal: the 2 s bar, 8 s after the pull, then every 20 s (none while 2 books are open; he tries '
    'again every second), with the book\'s emote (texts 1-6). A finished bar throws the book (OnSpellCast). Not '
    'interruptible (a must-play bar, InterruptFlags 0): Arcane, a school his kickable Searing Rebuke (Holy) does not '
    'use, so a kicked Rebuke never locks it (rule 5).',
    icon=_ICON_BOOK, school=School.ARCANE,
)

open_the_index_heroic_212611 = spell(
    id=212611, name='Open the Index', school=School.ARCANE, cast_time_ms=OPEN_CAST_MS[1], cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BOOK,
    notes=f'{_D7}, LB1 heroic: the 3 s cast, 6 s after the pull, then every 15 s, with the book\'s emote. An expected '
          'interrupt (the descriptor\'s list, priority 3): a kick or a silence (InterruptFlags 15, PreventionType 1; '
          'his immunity set 1972 lets both work) still throws the book, on page 1; a finished cast throws it on page 2 '
          '(OpeningPage). Arcane: a kick locks only Arcane, so the Holy Searing Rebuke stays castable and kickable.',
    raw_overrides=kit_raw('Opens a forbidden book from the Index. Interrupt it, or the book opens further along.',
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, AttributesEx4=ATTR4_NO_CAST_LOG),
)

turning_the_page_212612 = _lasting(
    212612, 'Turning the Page', 0,
    f'{_D7}, LB1a: the book\'s page count, put on the book by the boss (Aura::SetStackAmount): page 1 when opened '
    '(heroic page 2 when the cast was not kicked), +1 every 10 s it stays open (normal stops at 3). The descriptor\'s '
    'kill order reads the stacks (highest page first). CumulativeAura 10 (heroic keeps counting past it in the '
    'script; the shown count stops at 10).',
    icon=_ICON_BOOK, shown=True, desc='Its story grows with every page.', stacks=PAGE_STACKS,
)

readers_ward_212613 = spell(
    id=212613, name="Reader's Ward", school=School.ARCANE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=-WARD_PCT - 1, die_sides=1, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BOOK,
    notes=f'{_D7}, LB1b: he takes 25% less damage per open book (every school), 50% at most (heroic 75%): the kit\'s '
          'WardOfTheLiving sets the stacks to the living books (2 / 3 at most) every 0.5 s and removes it on his '
          'reset, evade and death. CumulativeAura 3. Not dispellable or purgeable: the answer is closing the books. '
          'Arcane Bubble\'s ManaShield state (SV 968).',
    raw_overrides=kit_raw('Damage taken reduced for every open book.', 'Damage taken reduced by $s1%.',
                          CastingTimeIndex=1, CumulativeAura=WARD_STACKS, SpellVisualID_1=LB_WARD,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

_STORIES = (
    (212614, 'War of the Spider', 'LB2: webs on players\' spots, Spiderlings hatching from them'),
    (212615, "Archimonde's Return", 'LB3: meteors on players\' spots, Infernals rising from them'),
    (212616, 'Arathor and the Troll Wars', 'LB4: a spectral troll throwing axes along lines'),
    (212617, 'Mythology of the Titans', 'LB5: a stomp rolling out in rings from the book'),
    (212618, 'The World Tree and the Emerald Dream', 'LB6: a sleeping mist round the book'),
    (212619, 'Aftermath of the Second War', 'LB7: phantom grunts charging along lines to the wall'),
)
for _id, _name, _what in _STORIES:
    _lasting(
        _id, _name, LB_OPEN_BOOK,
        f'{_D7}, the book\'s story ({_what}): cast by the Cursed Book on itself when he throws it, for the read and '
        'the open-book glow (Pet Book Graphic 35720\'s bookmedium04 state, SV 8355). The descriptor keeps melee off '
        'the Emerald Dream book (its mist) by this aura.',
        icon=_ICON_BOOK, shown=True, desc=f'An open forbidden book: {_name}. Destroy it to end its story.',
    )

# --- LB2 War of the Spider --------------------------------------------------------------------------------------------

web_spray_212620 = _missile(
    212620, 'Web Spray', LB_WEB_SPRAY, 40.0,
    f'{_D7}, LB2: the spray, cast by the book on the web\'s stalker as the 2 s marker goes down. Web Spray 29484\'s '
    'webspin and Web_Missile (SV 7613). Look only.',
    icon=_ICON_WEB_SPRAY,
)

web_slow_212621 = standing_in_it(
    212621, f'{_D7}, LB2: the web\'s slow, 50% movement for 1.5 s, re-applied by every 1 s tick of the web zone (the '
    'registry\'s rider), so it ends shortly after the player steps out. Snare mechanic (Hand of Freedom and the like '
    'clear it).',
    name='Web', slow_pct=WEB_SLOW_PCT, duration_ms=WEB_SLOW_MS, desc='Caught in a web. Lasts $d.',
    aura_desc='Caught in a web: movement slowed.', icon=_ICON_WEB,
)

web_patch_212622 = _lasting(
    212622, 'Web', LB_WEB,
    f'{_D7}, LB2: the 6 yd web on the ground: the shipped BRD web patch STATE (SV 90659, exact 6 yd) on a stalker at '
    'the spot, from the hatch until the web fades (the cap) or the book closes. Look only.',
    icon=_ICON_WEB,
)

hatch_212623 = self_visual(
    212623, 'Hatch Spiderlings', LB_WEB_HATCH,
    f'{_D7}, LB2: the hatch on the web as the Spiderlings come out (Hatch Spiderlings 43134\'s SV 3999).',
    icon=_ICON_HATCH,
)

# --- LB3 Archimonde's Return ------------------------------------------------------------------------------------------

meteor_212624 = resolve_copy(
    212624, 'Meteor', School.FIRE, 'An infernal falls from the sky.',
    f'{_D7}, LB3: the meteor\'s hit, 8 yd at a random player\'s spot (the tank too) after a 4 s marker: 50% (heroic '
    '60%) of the reference row, the tank\'s row on the tank. Its own penalty: no Weakened. Copy of the '
    'mod-boss-mechanics resolve spell 205001 (Fire).',
    icon=_ICON_INFERNO,
)

inferno_212625 = self_visual(
    212625, 'Inferno', LB_METEOR,
    f'{_D7}, LB3: the falling infernal, cast by a stalker at the spot 1 s before the impact (Inferno 1122\'s shadow '
    'hands and infernal_impact_base, SV 4859).',
    icon=_ICON_INFERNO, school=School.FIRE,
)

immolation_212626 = spell(
    id=212626, name='Immolation', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=IMMOLATION[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
                    radius_yards=IMMOLATION_RADIUS, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_INFERNO,
    notes=f'{_D7}, LB3: the Infernal\'s burn (the build spec\'s "Immolation aura", gap 12 for the value): every 2 s '
          'the Infernal casts it on itself (triggered): 2% (heroic 2%: EffectMiscValueB) of the reference row to every '
          'enemy within 5 yd, the tank\'s row on the tank (the healer\'s "infernal\'s aura on the tank"). Always hits, '
          'cannot crit, ignores its modifiers. No look (Immolation 20153\'s SV 2519 is not one of V\'s picks: a '
          'request in the report).',
    raw_overrides=kit_raw('Burns nearby enemies.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          EffectMiscValueB_1=IMMOLATION[1], **_HIT_ATTRS),
)
scripted_by(immolation_212626, 'spell_dungeon_refflat_damage')

# --- LB4 Arathor and the Troll Wars -----------------------------------------------------------------------------------

throw_axe_212627 = resolve_copy(
    212627, 'Throw Axe', School.NORMAL, 'A spectral axe flies down the line.',
    f'{_D7}, LB4: an axe line\'s hit, 3 yd wide and 35 yd long from the Spectral Troll through a random player (the '
    'tank too), 2 s marker: 35% (heroic 45%) of the reference row and 1 Weakened. Copy of the resolve spell 205001 '
    '(Physical).',
    icon=_ICON_AXE,
)

throw_axe_look_212628 = _missile(
    212628, 'Throw Axe', LB_AXES, 20.0,
    f'{_D7}, LB4: the axe in flight, cast by the Spectral Troll at its target 0.5 s before the line resolves (Throw '
    'Axe 16075\'s missile_axe_copper, SV 3962; never Axe Volley\'s 9766, which draws no axe). Look only.',
    icon=_ICON_AXE,
)

# --- LB5 Mythology of the Titans --------------------------------------------------------------------------------------

titan_stomp_212629 = resolve_copy(
    212629, 'Titan Stomp', School.NORMAL, 'A stone keeper\'s stomp rolls out from the book.',
    f'{_D7}, LB5: a ring\'s hit: 0-8 yd round the book, then 8-16, 16-24 (and 24-32 from page 2), 1.5 s apart, each '
    'with a 2 s marker: 35% (heroic 45%) of the reference row and 1 Weakened per ring. Copy of the resolve spell '
    '205001 (Physical).',
    icon=_ICON_WAR_STOMP,
)

war_stomp_212630 = self_visual(
    212630, 'War Stomp', LB_STOMP,
    f'{_D7}, LB5: the stomp as the first ring lands (War Stomp 11876\'s ThunderClap ring and shake, SV 2355), cast by '
    'the book.',
    icon=_ICON_WAR_STOMP,
)

ground_slam_212631 = self_visual(
    212631, 'Ground Slam', LB_STOMP_RINGS,
    f'{_D7}, LB5: each later ring as it lands (Ground Slam 33525\'s rings, SV 8083), cast by the book.',
    icon=_ICON_GROUND_SLAM,
)

# --- LB6 The World Tree and the Emerald Dream -------------------------------------------------------------------------

for _radius, _id in ((6, 212632), (9, 212633), (12, 212634)):
    _lasting(
        _id, 'Dream Mist', SV_DREAM_MIST[_radius],
        f'{_D7}, LB6: the {_radius} yd rung of the green mist (V\'s minted STATE {SV_DREAM_MIST[_radius]}, '
        '`LargeGreenRadiationFog`), worn by the book (or by a stalker for a missed Dreaming\'s mist); the kit\'s '
        'GrowingZone swaps the rung as the mist grows 3 yd a page. Look only.',
        school=School.NATURE,
    )

drowsy_212635 = spell(
    id=212635, name='Drowsy', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=DROWSY_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-DROWSY_PCT - 1,
               die_sides=1, implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded='Drowsy: a flat -10% movement a stack, not a damage or heal value'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK,
               base_points=-DROWSY_PCT - 1, die_sides=1, implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded='Drowsy: a flat -10% casting speed a stack, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_SLEEP,
    notes=f'{_D7}, LB6: a stack every second inside the mist (the mist zone\'s rider, the boss as the caster): -10% '
          'movement and casting speed a stack (this WP\'s starting guess, the spec\'s "10% per stack"), 5 stacks. The '
          'boss takes a stack off every second a player stands outside every mist and, at 5, removes it and puts the '
          '2 s sleep on (212636). No mechanic and not dispellable (the stacks fade by stepping out). CumulativeAura 5; '
          'the 30 s duration is only a backstop (the boss clears it). Dropped on a map change and when the fight ends.',
    raw_overrides=kit_raw('The dream is pulling you under.', 'Movement and casting slowed by $s1%. At 5 stacks you '
                          'fall asleep.', CastingTimeIndex=1, CumulativeAura=DROWSY_STACKS,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

dream_sleep_212636 = spell(
    id=212636, name='Dreamless Sleep', school=School.NATURE, dispel=0, mechanic=_MECHANIC_SLEEP,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=DREAM_SLEEP_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, mechanic=_MECHANIC_SLEEP)],
    spell_icon_id=_ICON_SLEEP,
    notes=f'{_D7}, LB6: the 2 s sleep (the shared doc\'s longest loss of control): at 5 Drowsy stacks, and heroic on a '
          'Dreaming that ran out. A stun with the sleep mechanic (the stock Dreamless Sleep 15822\'s shape), cast by '
          'the boss (triggered). Not dispellable (2 s). Dreamless Sleep\'s zzz head state (SV 3859).',
    raw_overrides=kit_raw('Asleep.', 'Asleep.', CastingTimeIndex=1, SpellVisualID_1=LB_SLEEP,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

dreaming_212637 = spell(
    id=212637, name='Dreaming', school=School.NATURE, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=DREAMING_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SLEEP,
    notes=f'{_D7}, LB6a (heroic): each page of the Emerald Dream book (and its opening) the boss puts this on a random '
          'player (the tank too), 6 s, Magic: an expected dispel (the descriptor\'s list, priority 2). Run out '
          '(spell_sm_hollis_dreaming, removal by expiry only), the player sleeps 2 s (212636) and a new 6 yd mist '
          'rises at their spot until the book closes. Closing the book removes it (no sleep, no mist). No look (the '
          'zzz state would read as asleep).',
    raw_overrides=kit_raw('Dreaming.', 'Dreaming. Unless dispelled, you fall asleep and a mist rises where you stand.',
                          CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(dreaming_212637, 'spell_sm_hollis_dreaming')

# --- LB7 Aftermath of the Second War ----------------------------------------------------------------------------------

phantom_charge_212638 = resolve_copy(
    212638, 'Phantom Charge', School.NORMAL, 'A phantom grunt charges through.',
    f'{_D7}, LB7: the charge line\'s hit, 6 yd wide from the book through a random player (the tank too) to the wall, '
    '3 s marker: 50% (heroic 60%) of the reference row. Its own penalty: no Weakened. Copy of the resolve spell '
    '205001 (Physical).',
    icon=_ICON_CHARGE,
)

charge_look_212639 = self_visual(
    212639, 'Charge', LB_GRUNT_CHARGE,
    f'{_D7}, LB7: the Phantom Grunt\'s charge trail as it runs its line (Charge 100\'s SV 867).',
    icon=_ICON_CHARGE,
)

# --- LB8 Searing Rebuke -----------------------------------------------------------------------------------------------

searing_rebuke_212640 = spell(
    id=212640, name='Searing Rebuke', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=REBUKE_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=REBUKE_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=REBUKE[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_SMITE,
    notes=f'{_D7}, LB8: his own: a 2.5 s cast on his target, 5 s after the pull, then every 10 s: 20% (heroic 30%: '
          'EffectMiscValueB) of the reference row, the tank\'s row on the tank, Holy. An interrupt stops it (a reward: '
          'the descriptor\'s list, priority 1; InterruptFlags 15, PreventionType 1). Always hits, cannot crit, ignores '
          'his modifiers. Holy Smite 9481\'s SV 128.',
    raw_overrides=kit_raw('Sears the heretic with holy fire.', InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=LB_REBUKE,
                          EffectMiscValueB_1=REBUKE[1], **_HIT_ATTRS),
)
scripted_by(searing_rebuke_212640, 'spell_dungeon_refflat_damage')

# --- LB9 Burning Book (heroic) ----------------------------------------------------------------------------------------

burning_book_212641 = resolve_copy(
    212641, 'Burning Book', School.FIRE, 'A destroyed book burns where it fell.',
    f'{_D7}, LB9 (heroic): the fire\'s tick, 5 yd where a book was destroyed, every second for the rest of the fight: '
    '10% of the reference row, the tank\'s row on the tank. No slow (the spec names none). Copy of the resolve spell '
    '205001 (Fire).',
    icon=_ICON_FLAME_PATCH,
)

burning_book_look_212642 = _lasting(
    212642, 'Burning Book', LB_BURNING_BOOK,
    f'{_D7}, LB9 (heroic): the 5 yd fire on the ground, the shipped BRS lava rung STATE (SV 90607) on a stalker where '
    'the book fell (Flame Patch 35383\'s SV 8314 is a one-shot). Look only.',
    icon=_ICON_FLAME_PATCH, school=School.FIRE,
)

# --- the zones' tick spells (no damage: the rider is the cost) --------------------------------------------------------

dream_mist_212643 = resolve_copy(
    212643, 'Dream Mist', School.NATURE, 'The dream seeps into you.',
    f'{_D7}, LB6: the mist\'s tick, every second, round the book (6 yd, +3 yd a page) and round a missed Dreaming\'s '
    'spot (6 yd): no damage (the registry\'s percent is 0); its rider is Drowsy (212635). Copy of the resolve spell '
    '205001 (Nature), so the combat log names the mist.',
    icon=_ICON_SLEEP,
)

web_212644 = resolve_copy(
    212644, 'Web', School.NORMAL, 'Sticky webs.',
    f'{_D7}, LB2: the web\'s tick, every second, 6 yd: no damage; its rider is the 50% slow (212621). Copy of the '
    'resolve spell 205001 (Physical), so the combat log names the web.',
    icon=_ICON_WEB,
)
