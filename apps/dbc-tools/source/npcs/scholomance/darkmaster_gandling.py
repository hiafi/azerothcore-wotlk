"""
Scholomance build WP-S11: Darkmaster Gandling (1853), normal and heroic, and detention
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S11, s3.6, s3.7; build spec
docs/dungeons/scholomance-rework.md SC 3034-3101, SC 2944-3023). WP-S11 owns this file (its spells: kSpellsGandling
206330-206364 of modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; GandlingLogic.h names the same
ids; its creatures: the Expelled Student 300544, the Ravenian's echo 300545, the lesson stalker 300546 and the portal
stalker 300547).

- 1853 Darkmaster Gandling: boss_darkmaster_gandling_rework (src/Scholomance/boss_darkmaster_gandling_rework.cpp), the
  stock C++ file stays untouched, SmartAI off (his 12 dormant rows go in S11's SQL rev), the build spec's normal health
  (280k: HealthModifier 111.332 on the level 61 class base 2,515), stun immunity 1972 (in place of -346, which also
  blocked interrupts; s7 #9) and flags_extra 1 (INSTANCE_BIND). He stays rank 1 (stock). DamageModifier stays the
  stock 2.3 (the AC base row's value; his melee is tuned in WP-T). Heroic health 400k and its overrides are WP-H's
  (source/world/dungeons/scholomance.py). The Risen Guardian 11598 is retired: the rework never summons it (its
  shipped heroic template 310109 stays, unused).
- 300544 Expelled Student (GD3): the Skeletal Berserker look (display 9784, creature 10391 / Curse of the Darkmaster
  18702's form), level 60 elite undead warrior, 15,000 health (warrior base 3,052 x 4.91481); heroic 25,000 is WP-H's
  `_KIT_ADD_HEROIC` (difficulty_entry_1 310119). npc_sc_expelled_student fixates its student (not tauntable) until it
  is killed; heroic +10% damage every 10 s alive (206337). DamageModifier 2.4: SC "melee about 8% per swing" = 294 of
  the normal row; the level 60 class 1 row (damage_base 33.96, attack power 252) gives about (33.96 x 1.25 + 252 /
  14) x 2 s x 2.4 = 290 a swing [estimate; WP-T checks a combat log line]. Heroic melee is the tier's (WP-H).
- 300545 The Ravenian's echo: detention only (the Vault of the Ravenian lesson, S8's RavenianVaultLesson summons it
  next to the lesson stalker, sets it passive and applies Ghost Visual 9617). The Wight display 10433, KIT_HELPER (not
  selectable or attackable), no script (S8's contract). No heroic template.
- 300546 Lesson stalker: a solo lesson's owner (SoloLesson.h), invisible (11686), KIT_HELPER with TRIGGER (no combat
  of its own: the lesson's spells hit the student without a combat reference), hostile faction 14 (STAGE-S5 "For
  S11": the lesson spells must be able to hit the student). npc_sc_lesson_stalker does nothing and never zones its
  summons into combat (F-B3). No heroic template.
- 300547 Portal stalker: a portal (Creature_SpellPortal_LargeShadow, CDI 27735 at scale 0.2) on the study's edge for
  Portal Volley and at the detention return. KIT_HELPER with TRIGGER; npc_sc_portal_stalker does nothing. No heroic
  template.

Spells (looks from WP-V's ._visuals, all stock):

  206330  Detention          GD1 his 1 s cast bar on the student (yell line 1), Open Shadow Portal's hand precast
  206331  Detention          GD1 / GD4b the portal flash on a player as they go and as they land (Teleport Visual)
  206332  Honor Roll         GD2 +100% damage and healing done for 15 s, self-applied (Power Infusion's glow)
  206333  Portal Volley      GD4 his 2 s cast bar (emote line 2)
  206334  Portal Volley      GD4 a lane's hit: resolve copy (Arcane), 30% / 40% + Weakened, the registry's
  206335  Portal Volley      GD4 a missile out of a portal at a player its lane hit (look only)
  206336  Portal Volley      GD4 heroic: a lingering lane's tick, resolve copy (Arcane), 10% + the kit slow
  206337  Expelled           GD3 heroic: the Expelled Student's growth, +10% damage done and 5% size a stack
  206338  Transfer           GD4b the linked-portal mark on both players for 2 s (Chains of Kel'Thuzad's link)
  206339  Portal Volley      GD4 a missile out of a portal down its lane as it fires (look only, at a point)
  206340-206364 spare (206365-206384 is S13's).
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_C,
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
    DISPLAY_ECHO_RAVENIAN,
    DISPLAY_EXPELLED_STUDENT,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_PORTAL,
    GD_HONOR_ROLL,
    GD_PORTAL_VOLLEY,
    GD_TRANSFER_FLASH,
    GD_TRANSFER_LINK,
    PORTAL_SIZE,
)

# Held back until wave C binds this boss (_common.py BIND_WAVE_C; R-A S-11): stock until then.
if BIND_WAVE_C:
    creature_template_columns(1853, **boss_columns('boss_darkmaster_gandling_rework', 111.332))

_GD = 'Scholomance build WP-S11 (Darkmaster Gandling)'

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_SCHOOL_MASK_ALL = 127
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a logout or a map change drops it (a same-map teleport keeps it).
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_FLAGS_EXTRA_NO_XP = 0x40
_FLAGS_EXTRA_TRIGGER = 0x80

# Stock SpellVisuals with no _visuals.py name (Spell.dbc 3.3.5).
_SV_OPEN_SHADOW_PORTAL = 11806     # Open Shadow Portal 53765: a hand precast (no portal; VISUALS-REPORT gap 16)

_ICON_POWER_INFUSION = 1872        # Power Infusion 10060
_ICON_ARCANE_MISSILES = 225        # Arcane Missiles 15790 (the stock Gandling kit)
_ICON_SHADOW = 213                 # Shadow Bolt Volley 17228

# --- 300544 Expelled Student / 300545 echo / 300546 lesson stalker / 300547 portal stalker ----------------------------

# Level 60 elite undead warrior: ceil(3,052 x 4.91481) = 15,000.
expelled_student_300544 = creature_template(
    300544, 'Expelled Student', **{
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'type': 6, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': 4.91481, 'DamageModifier': 2.4, 'BaseAttackTime': 2000, 'ExperienceModifier': 1.0,
        'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'ScriptName': 'npc_sc_expelled_student', 'difficulty_entry_1': 310119,
    },
)
creature_model(300544, display_id=DISPLAY_EXPELLED_STUDENT)

ravenians_echo_300545 = creature_template(
    300545, "The Ravenian's Echo", **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                       'type': 6, 'ScriptName': ''},
)
creature_model(300545, display_id=DISPLAY_ECHO_RAVENIAN)

lesson_stalker_300546 = creature_template(
    300546, 'Detention', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
                            'flags_extra': _FLAGS_EXTRA_NO_XP | _FLAGS_EXTRA_TRIGGER,
                            'ScriptName': 'npc_sc_lesson_stalker'},
)
creature_model(300546, display_id=DISPLAY_INVISIBLE_STALKER)

portal_stalker_300547 = creature_template(
    300547, 'Shadow Portal', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
                                'flags_extra': _FLAGS_EXTRA_NO_XP | _FLAGS_EXTRA_TRIGGER,
                                'ScriptName': 'npc_sc_portal_stalker'},
)
creature_model(300547, display_id=DISPLAY_PORTAL, scale=PORTAL_SIZE)

# --- GD1 Detention ----------------------------------------------------------------------------------------------------

detention_cast_206330 = cast_bar(
    206330, 'Detention', 1000, 'Sends a student to detention.',
    f'{_GD}, GD1: his 1 s cast bar on the student (yell line 1 "Detention, $n!"), first at 15 s, every 25 s. When it '
    'ends the AI sends the student through the portal to a classroom (never the stock Shadow Portal 17950, its Risen '
    'Guardians retired). Not interruptible (the detention is his own timer, a kick would only look as if it stopped '
    'it). Open Shadow Portal 53765\'s SV 11806 (a hand precast).',
    icon=_ICON_SHADOW, school=School.SHADOW, visual=_SV_OPEN_SHADOW_PORTAL)

portal_flash_206331 = spell(
    id=206331, name='Detention', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHADOW,
    notes=f'{_GD}, GD1 / GD4b: the portal flash a player casts on themselves (triggered, no effect) as they leave the '
          'study, land in the classroom, come back, and on both sides of a Transfer swap. Teleport Visual 41236\'s SV '
          '9343.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=GD_TRANSFER_FLASH, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GD2 Honor Roll ---------------------------------------------------------------------------------------------------

honor_roll_206332 = spell(
    id=206332, name='Honor Roll', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    duration_ms=15000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=100,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=100,
                    die_sides=0, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_POWER_INFUSION,
    notes=f'{_GD}, GD2: a passed detention. The student casts it on themselves as they land back in the study '
          '(triggered): +100% damage done (all schools) and +100% healing done for 15 s (SC "Numbers", approved: a '
          'pass pays back the 15 s away; GandlingLogic.h kHonorRollMs). Never detained again while it lasts. Not '
          'dispellable (Dispel none). Power Infusion 10060\'s SV 7553 (the body glow) and icon. AuraInterruptFlags '
          'CHANGE_MAP.',
    raw_overrides=kit_raw('Passed detention with honors.', 'Damage and healing done increased.',
                          instant=True, SpellVisualID_1=GD_HONOR_ROLL, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- GD4 Portal Volley ------------------------------------------------------------------------------------------------

volley_cast_206333 = cast_bar(
    206333, 'Portal Volley', 2000, 'Tears open portals around the room.',
    f'{_GD}, GD4: his 2 s cast bar (emote line 2), first at 10 s, every 20 s. When it ends 2 / 3 portals (300547) open '
    'on the study\'s edge (kStudyPortalPoints) and their 4 yd lanes show, each aimed through a random non-tank player '
    'to the far wall; they fire 2 s later (206334). Not interruptible (the registry owns the hit).',
    icon=_ICON_ARCANE_MISSILES, school=School.ARCANE)

volley_hit_206334 = resolve_copy(
    206334, 'Portal Volley', School.ARCANE, 'A stream of arcane missiles.',
    f'{_GD}, GD4: a lane\'s hit as it fires, 30% normal / 40% heroic of the non-tank row and one Weakened stack '
    '(ruling 21). Copy of the resolve spell 205006 (Arcane). No visual of its own: the portal casts 206335 at every '
    'player hit (a missile out of the portal, Magic_Impact_Chest on landing).',
    icon=_ICON_ARCANE_MISSILES,
)

volley_stream_206335 = spell(
    id=206335, name='Portal Volley', school=School.ARCANE, attributes=ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ARCANE_MISSILES,
    notes=f'{_GD}, GD4: the impact look of a lane hit: a missile the portal casts (triggered) at each player its lane '
          'hits, so every hit shows (Pilot PT1). No effect. SV 269 (Arcane_Missile_Lvl2 + Magic_Impact_Chest, the '
          'triggered missile of Arcane Missiles; 5143\'s SV 262 is only the channel hands). Speed 40 yd/s.',
    raw_overrides=kit_raw('A stream of arcane missiles.', instant=True, SpellVisualID_1=GD_PORTAL_VOLLEY, Speed=40.0,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

volley_linger_206336 = resolve_copy(
    206336, 'Portal Volley', School.ARCANE, 'The missiles still pour through.',
    f'{_GD}, GD4 heroic: a fired lane lingers 4 s (L11\'s heroic version, SC "Heroic"): every 1 s, 10% of the non-tank '
    'row (PROVISIONAL designer default, GandlingLogic.h kVolleyLingerPct; SC gives no number) and the kit\'s Standing '
    'in It slow on everyone still inside. A persistent zone, so no Weakened. Copy of the resolve spell 205006 '
    '(Arcane). No visual (the outline shows until the first tick).',
    icon=_ICON_ARCANE_MISSILES,
)

volley_stream_ground_206339 = spell(
    id=206339, name='Portal Volley', school=School.ARCANE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_ARCANE_MISSILES,
    notes=f'{_GD}, GD4: the stream down a lane as it fires: each portal casts it (triggered) three times 150 ms '
          'apart at its lane\'s far end, so a dodged lane still shows its missiles. No effect. SV 269, Speed 40 yd/s.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=GD_PORTAL_VOLLEY, Speed=40.0,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GD3 Expelled Student growth -------------------------------------------------------------------------------------

expelled_growth_206337 = spell(
    id=206337, name='Expelled', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=10,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SCALE, base_points=5, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHADOW,
    notes=f'{_GD}, GD3 heroic: an Expelled Student grows while it lives: npc_sc_expelled_student casts it on itself '
          '(triggered) every 10 s alive, +10% damage done and +5% size a stack (the engine multiplies by the stacks; '
          'CumulativeAura 99: uncapped in practice; SC "Expelled Students hit harder and gain 10% damage every 10 s '
          'alive"). Dispel none (killing it is the answer).',
    raw_overrides=kit_raw('Grows angrier the longer it is ignored.', 'Damage done increased.',
                          instant=True, CumulativeAura=99, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GD4b Transfer ----------------------------------------------------------------------------------------------------

transfer_mark_206338 = spell(
    id=206338, name='Transfer', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=4000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SHADOW,
    notes=f'{_GD}, GD4b (heroic): the linked-portal mark he puts on the two players about to swap (emote line 3), 2 s '
          'before the swap (the AI removes it at the swap; 4 s so a swap held past a firing lane keeps it). No effect. '
          'Chains of Kel\'Thuzad 28410\'s SV 7597 (the closest stock link look; a true beam is client CharParam only). '
          'Dispel none.',
    raw_overrides=kit_raw('Linked to another student through a portal.', 'About to trade places.', instant=True,
                          SpellVisualID_1=GD_TRANSFER_LINK, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
