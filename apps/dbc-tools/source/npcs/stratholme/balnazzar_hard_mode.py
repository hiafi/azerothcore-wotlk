"""
Stratholme build WP-S8: Balnazzar's hard mode, the Grand Lie (heroic only)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.7, s3.5 row S8, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 1920-1999 (Hard mode), ST 2107-2120 (the HM rows)). WP-S8 owns this file (its
spells: kSpellsGrandLie 206575-206604 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only;
GrandLieLogic.h names the same ids; its creature: 300609). The engine side is src/Stratholme/balnazzar_hard_mode.cpp, a
GrandLie on S7's AI (DathrohanFight.h). The relics' use spells (206585-206588) are here too (the boss's slice; every
source/items spell must sit in an item reservation); their items are source/items/stratholme_relics.py (the table),
source/items.csv (the Item.dbc rows) and WP-S8's SQL rev (data/sql/updates/pending_db_world/
rev_balnazzar_hard_mode_stratholme.sql: the item_template rows, the gameobjects, their spawns and the texts).

- 300609 Moving swarm (HM5): an invisible, unselectable stalker (KIT_HELPER) wearing the swarm cloud (206582); the
  script walks it in straight lines at 3 yd/s and owns its zone (a persistent 2.5 yd registry circle on it, 206583).
  Summoned by Balnazzar for 30 s (his summon list: S7's cleanup despawns it). Hard mode only, so no heroic template
  (handoff s7 #15; source/world/dungeons/stratholme.py leaves it out).

Spells. The registry-owned hits go through dungeon copies of the mod-boss-mechanics resolve spell (the percent of the
heroic reference row; the combat log names the mechanic); the true Mark's share carries a base point the script
computes (DungeonKit::SplitShares). The rest are a mark, a look and a cast bar:

  206575  The Light Cleaves      HM1 true: the claimed half is struck, 50% to the non-tanks (Holy)
  206576  The Blade Cleaves      HM1 lie: the other half is struck, 50% to the non-tanks (Shadow)
  206577  The Light Burns        HM2 true: the 10 yd circle on him, 50% (Holy)
  206578  None Near Live         HM2 lie: everything 10 to 40 yd from him, 50% (Shadow)
  206579  Burden                 HM3 the mark on the called non-tank until the call lands (the claimed stack's tell)
  206580  Burden                 HM3 true: one share of the 100% split (Holy, base point 0 from the script)
  206581  Burden                 HM3 lie: each non-tank bursts on every other non-tank within 7 yd, 50% (Shadow)
  206582  Carrion Cloud          HM5 the swarm's cloud on its stalker (Locust Swarm's insect state)
  206583  Carrion Cloud          HM5 the swarm's 1 s tick, 10% and Weakened on everyone inside (Shadow)
  206584  Dread Slumber          HM8 act 3: the 3 s cast bar, not interruptible (yell 16); the sleeps are S7's 206566
  206585  Letter of Proof        the Letter's use: read it to Dathrohan (spell_strat_grand_lie_letter)
  206586  Blessed Holy Water     HM9 the throw at a spot within 10 yd: its 5 yd splash disperses swarms
  206587  Scarlet Standard       HM9 a 6 yd ring for 5 s at the user's feet; its aura is the ward
  206588  Faith of the Medallion HM9 a 30 yd pulse: a 4 s sleep immunity, and it wakes sleepers
  206589-206604 spare.

Every twin is 50% (the true Mark 100% split) of the heroic non-tank row, the tank exempt, no Weakened (over 30%: the
build spec's Penalty column is empty). Tooltips are number-free (ST checklist item 8).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT, RESOLVE_RAW, TARGET_UNIT_TARGET_ENEMY
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BA_DEATH_KNELL,
    BZ_SWARM_CLOUD,
    DA_HOLY_WATER,
    DA_HOLY_WRATH,
    DA_SLEEP,
    DA_TRUE_GROUND,
    DA_TRUE_JUDGMENT,
    DA_TRUE_JUDGMENT_ALT,
    DISPLAY_INVISIBLE_STALKER,
    SV_LIE_JUDGMENT,
)

_HM = 'Stratholme build WP-S8 (the Grand Lie, Balnazzar\'s hard mode)'
_SCRIPT_SHARE = 'Stratholme: a share of the true Burden, the script\'s base point (DungeonKit::SplitShares)'

_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_SV_CARRION_SWARM = 7835                    # Carrion Swarm 31306's own look (the impact on each player hit)

# GrandLieLogic.h numbers mirrored here (lib/test_stratholme_grand_lie.py pins both sides).
_CALL_LAND_MS = 4000                        # kCallLandMs: the mark lasts at most a call's warning
_SLUMBER_CAST_MS = 3000                     # kSlumberCastMs

_ICON_CARRION_SWARM = 116                   # Carrion Swarm 31306
_ICON_HOLY_WRATH = 158                      # Holy Wrath 2812
_ICON_DESECRATION = 140                     # Desecration 36473
_ICON_JUDGEMENT = 205                       # Judgement of Light 20271
_ICON_JUDGEMENT_DARK = 1980                 # Judgement of Darkness 34112
_ICON_SLEEP = 44                            # Sleep 31298

# The hits whose damage the script sets carry the resolve attribute set (no active defense, redirection, reflection or
# threat; ignore line of sight; cannot crit; not a proc; always hit; ignore caster modifiers).
_SCRIPT_HIT_RAW = {k: v for k, v in RESOLVE_RAW.items() if k != 'CastingTimeIndex'}

# --- 300609 Moving swarm ---------------------------------------------------------------------------------------------

moving_swarm_300609 = creature_template(
    300609, 'Carrion Swarm', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                'ScriptName': 'npc_st_moving_swarm'},
)
creature_model(300609, display_id=DISPLAY_INVISIBLE_STALKER)

# --- HM1 The Cleave --------------------------------------------------------------------------------------------------

cleave_light_206575 = resolve_copy(
    206575, 'The Light Cleaves', School.HOLY, 'The Light strikes half of the chamber.',
    f'{_HM}, HM1 true (yell 10 "The Light cleaves the unworthy!"): the half the marker shows is struck when the call '
    'lands, 4 s after its first yell: 50% of the heroic non-tank row to every non-tank in it (the tank exempt), no '
    'Weakened (over 30%). A 180 degree registry cone from the brazier on the measured frame (StratholmeRework.h '
    'kDathrohanHalves, the split line through the brazier), registered NoTelegraph (the bots read it); the claim is a '
    'Decoy half-room cone drawn alike for truth and lie. The struck half is the one with more swarms. Copy of the '
    'resolve spell 205001 (Holy). Holy Wrath 2812\'s SV 126 (V-2 DA_HOLY_WRATH) on every player hit.',
    icon=_ICON_HOLY_WRATH, visual=DA_HOLY_WRATH,
)

cleave_blade_206576 = resolve_copy(
    206576, 'The Blade Cleaves', School.SHADOW, 'The dreadlord\'s blade strikes half of the chamber.',
    f'{_HM}, HM1 lie (yell 11 "My blade cleaves the unworthy!"): the half the marker does NOT show is struck: 50% to '
    'every non-tank in it, no Weakened. As 206575 otherwise (the struck half has more swarms; the marker shows the '
    'other). Copy of the resolve spell 205001 (Shadow). Carrion Swarm 31306\'s SV 7835 on every player hit.',
    icon=_ICON_CARRION_SWARM, visual=_SV_CARRION_SWARM,
)

# --- HM2 The Ring ----------------------------------------------------------------------------------------------------

ring_light_206577 = resolve_copy(
    206577, 'The Light Burns', School.HOLY, 'The Light burns all who stand near him.',
    f'{_HM}, HM2 true (yell 12 "The Light burns all who stand near!"): the 10 yd circle on him is struck when the call '
    'lands: 50% to every non-tank inside (get out), no Weakened. A registry circle on him, NoTelegraph; the claim is a '
    'Decoy 10 yd circle (red) drawn alike for truth and lie. Copy of the resolve spell 205001 (Holy). Holy Wrath\'s SV '
    '126 on every player hit.',
    icon=_ICON_HOLY_WRATH, visual=DA_HOLY_WRATH,
)

ring_dark_206578 = resolve_copy(
    206578, 'None Near Live', School.SHADOW, 'Shadow strikes everyone who stands away from him.',
    f'{_HM}, HM2 lie (yell 13 "None who stand near me will live!"): everything 10 to 40 yd from him is struck (get '
    'in): 50% to every non-tank in the donut, no Weakened. A registry donut on him, NoTelegraph (the claim is the '
    '10 yd circle). Copy of the resolve spell 205001 (Shadow). Shadow Burst 28447\'s SV 45 on every player hit.',
    icon=_ICON_DESECRATION, visual=BA_DEATH_KNELL,
)

# --- HM3 The Mark ----------------------------------------------------------------------------------------------------

mark_206579 = spell(
    id=206579, name='Burden', school=School.HOLY, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_CALL_LAND_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_JUDGEMENT,
    notes=f'{_HM}, HM3: the mark on a random non-tank (yell 14 "$n, share the Light\'s burden!" true, yell 15 "$n, '
          'share my burden!" lie), cast by him (triggered) at the piece\'s yell and cut to the call\'s landing (2-4 s, '
          'DungeonKit::ShortenAura). A DUMMY aura: the tell only, alike for truth and lie (the perfect mask); the '
          'registry Stack (true) or Spread (lie) owns the answer. Dispel none, NO_IMMUNITIES, CHANGE_MAP. Judgement of '
          'Light 20271\'s SV 5651 (V-2 DA_TRUE_JUDGMENT).',
    raw_overrides=kit_raw('The dreadlord names a burden to share.', 'A burden is coming for you. Listen to his words.',
                          CastingTimeIndex=1, SpellVisualID_1=DA_TRUE_JUDGMENT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

mark_share_206580 = spell(
    id=206580, name='Burden', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_SHARE)],
    spell_icon_id=_ICON_JUDGEMENT,
    notes=f'{_HM}, HM3 true: one share of the burden, cast (triggered) on each non-tank inside the 6 yd stack on the '
          'marked player when the call lands (the marked player always shares): 100% of the heroic non-tank row split '
          'evenly (DungeonKit::SplitShares, the base point; DieSides 0: exact). No Weakened on a share. Each share '
          'heals Balnazzar (HM10). The resolve attribute set. SV 5651 on every share.',
    raw_overrides=kit_raw('The Light\'s burden, shared.', **{**_SCRIPT_HIT_RAW, 'SpellVisualID_1': DA_TRUE_JUDGMENT}),
)

mark_burst_206581 = resolve_copy(
    206581, 'Burden', School.SHADOW, 'Every bearer bursts with shadow.',
    f'{_HM}, HM3 lie: every non-tank bursts when the call lands: 50% to every other non-tank within 7 yd, no Weakened, '
    'through the registry (a Spread on every non-tank, NoTelegraph; the claim is the stack marker). Copy of the '
    'resolve spell 205001 (Shadow). V-2\'s SV 90514 (the lie judgment) on every player hit.',
    icon=_ICON_JUDGEMENT_DARK, visual=SV_LIE_JUDGMENT,
)

# --- HM5 The moving swarms -------------------------------------------------------------------------------------------

swarm_cloud_206582 = spell(
    id=206582, name='Carrion Cloud', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_CARRION_SWARM,
    notes=f'{_HM}, HM5: the swarm\'s cloud, cast on itself by the moving swarm (300609) as it crawls out of the wall. '
          'A DUMMY aura: the look only (the registry circle on it owns the ticks, 206583). Locust Swarm 28786\'s SV '
          '7620 (V-2 BZ_SWARM_CLOUD: GiantInsectSwarm_State_Chest; insects, not bats: ST gap 14). Unconfirmed in game.',
    raw_overrides=kit_raw('A cloud of carrion feeders.', instant=True, SpellVisualID_1=BZ_SWARM_CLOUD,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

swarm_bite_206583 = resolve_copy(
    206583, 'Carrion Cloud', School.SHADOW, 'The swarm devours everyone inside it.',
    f'{_HM}, HM5: a moving swarm\'s 1 s tick: 10% of the heroic row (non-tank, the tank row on the tank) and a '
    'Weakened stack every second on everyone inside its 5 yd cloud (a persistent registry circle of 2.5 yd anchored on '
    'the stalker, its first tick a second after it appears: Galford\'s grace). The Standard\'s ward (206587) spares '
    'its holders (eligibility maxStacks 0). Each tick heals Balnazzar (HM10). Copy of the resolve spell 205001 '
    '(Shadow). Carrion Swarm 31306\'s SV 7835 on every player hit.',
    icon=_ICON_CARRION_SWARM, visual=_SV_CARRION_SWARM,
)

# --- HM8 Dread Slumber -----------------------------------------------------------------------------------------------

dread_slumber_206584 = cast_bar(
    206584, 'Dread Slumber', _SLUMBER_CAST_MS, 'Lulls every enemy into a nightmare. It cannot be stopped.',
    f'{_HM}, HM8 act 3 (replacing Sleep): the 3 s cast bar (yell 16 "Sleep, and dream of your failure."), every 30 s, '
    'its cast starting 1 s before a call lands so it lands 2 s after; the next call\'s first yell 3 s later. Not '
    'interruptible (cast_bar). At its end every player without the Medallion\'s ward (206588) sleeps 5 s with S7\'s '
    'Sleep aura 206566 (Magic: the dispel list), then takes Nightmare 206567 (30% over 6 s). Sleep 31298\'s SV 7320 '
    '(V-2 DA_SLEEP) as the precast.',
    icon=_ICON_SLEEP, visual=DA_SLEEP, school=School.SHADOW,
)

# --- HM9 the Letter of Proof and the relics' use spells (their items: source/items/stratholme_relics.py) ----------

_HM9 = f'{_HM}, HM9'

_TARGET_DEST_CASTER = 18
_TARGET_SRC_CASTER = 22
_TARGET_DEST_DYNOBJ_ALLY = 29
_TARGET_UNIT_SRC_AREA_ALLY = 31
_TARGET_DEST_DEST = 87
_MECHANIC_SLEEP = 10

_ICON_HOLY_WATER = 70               # Spell_Holy_HolyBolt (the stock Holy Water 17291 has the generic icon 1)
_ICON_BANNER = 1703                 # INV_BannerPVP_01, the red battle standard
_ICON_MEDALLION = 315               # INV_Jewelry_Talisman_01
_ICON_LETTER = 2030                 # INV_Letter_04

# GrandLieLogic.h numbers mirrored here (lib/test_stratholme_grand_lie.py pins both sides).
_HOLY_WATER_RANGE_YD = 10.0         # kHolyWaterRangeYd
_HOLY_WATER_SPLASH_YD = 5.0         # kHolyWaterSplashYd
_STANDARD_RADIUS_YD = 6.0           # kStandardRadiusYd
_STANDARD_MS = 5000                 # kStandardMs
_MEDALLION_RADIUS_YD = 30.0         # kMedallionRadiusYd
_MEDALLION_WARD_MS = 4000           # kMedallionWardMs

letter_206585 = spell(
    id=206585, name='Letter of Proof', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_LETTER,
    notes=f'{_HM9}: the Letter of Proof\'s use. A DUMMY on the reader (never a hostile hit, so nothing starts the '
          'fight before the script does); spell_strat_grand_lie_letter checks Dathrohan within 30 yd and in sight, out '
          'of combat, heroic, wave 2 bound (else a notification, SPELL_FAILED_DONT_REPORT), then lights '
          'DATA_GRAND_LIE: he says line 8, and 2.5 s later yells line 9, the mask burns away (S7 Unmask, no stun) and '
          'he attacks the reader. The item is not consumed (handoff s7 #10).',
    raw_overrides=kit_raw('Show the Grand Crusader the letter Saidan Dathrohan wrote as the dreadlord took him. It '
                          'tears the mask away: a far harder fight.', instant=True, AttributesEx=ATTR1_NO_THREAT),
)
scripted_by(letter_206585, 'spell_strat_grand_lie_letter')

holy_water_206586 = spell(
    id=206586, name='Blessed Holy Water', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=_HOLY_WATER_RANGE_YD, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST, radius_yards=_HOLY_WATER_SPLASH_YD)],
    spell_icon_id=_ICON_HOLY_WATER,
    notes=f'{_HM9}: Blessed Holy Water\'s throw at a spot within 10 yd (TARGET_DEST_DEST: the ground circle, its 5 yd '
          'radius the splash). A DUMMY at the destination: spell_strat_grand_lie_holy_water (OnEffectHit) disperses '
          'every moving swarm (300609) within 5 yd of it, their registry zones with them. Speed 20 (the flask flies). '
          'Stratholme Holy Water 17291\'s SV 1243 (V-2 DA_HOLY_WATER, risky as a blast). The stock 13180 stays (it '
          'only hurts undead). The item\'s 3 min cooldown is per copy.',
    raw_overrides=kit_raw('Throw the blessed water at a spot. A swarm caught in its splash disperses.', instant=True,
                          SpellVisualID_1=DA_HOLY_WATER, Speed=20.0, AttributesEx=ATTR1_NO_THREAT),
)
scripted_by(holy_water_206586, 'spell_strat_grand_lie_holy_water')

standard_206587 = spell(
    id=206587, name='Scarlet Standard', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_STANDARD_MS,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                    implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY,
                    radius_yards=_STANDARD_RADIUS_YD)],
    spell_icon_id=_ICON_BANNER,
    notes=f'{_HM9}: the Scarlet Standard raised: a 6 yd ring of light at the user\'s feet for 5 s (TARGET_DEST_CASTER '
          '/ TARGET_DEST_DYNOBJ_ALLY, a persistent area aura): every ally inside carries this spell\'s DUMMY aura, the '
          'ward. The Carrion Swarm cones (S7 CarrionSpec::wardAura) and the moving swarms (eligibility maxStacks 0 on '
          'this aura) never hit a warded player, the cone\'s target included; leaving the ring drops it. Consecration '
          '26573\'s SV 5600 (V-2 DA_TRUE_GROUND; the hard mode has no Sacred Ground to confuse it with). '
          'spell_strat_grand_lie_standard (AfterCast) registers a 5 s Stack on the ring for the bots while the hard '
          'mode runs and the ring is in the chamber (F-2 MIN-1, ST 2017). The item\'s 20 s cooldown is per copy.',
    raw_overrides=kit_raw('Raise the Scarlet Standard. The swarms pass over allies within its ring of light.',
                          'Under the Scarlet Standard: the swarms pass you over.', instant=True,
                          SpellVisualID_1=DA_TRUE_GROUND, AttributesEx=ATTR1_NO_THREAT),
)

scripted_by(standard_206587, 'spell_strat_grand_lie_standard')

medallion_206588 = spell(
    id=206588, name='Faith of the Medallion', school=School.HOLY, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_MEDALLION_WARD_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=_MECHANIC_SLEEP,
                    implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ALLY,
                    radius_yards=_MEDALLION_RADIUS_YD)],
    spell_icon_id=_ICON_MEDALLION,
    notes=f'{_HM9}: the Medallion raised: a 30 yd pulse on every ally (TARGET_SRC_CASTER / TARGET_UNIT_SRC_AREA_ALLY): '
          'a 4 s immunity to the Sleep mechanic (Balnazzar\'s Sleep and Dread Slumber both land S7\'s 206566, mechanic '
          'Sleep, so a warded player is immune and Dread Slumber skips them), and spell_strat_grand_lie_medallion '
          '(OnEffectHitTarget) wakes a sleeper it reaches as a dispel would (Nightmare still follows, S7\'s rule). '
          'Raised during Dread Slumber\'s 3 s cast it wards everyone. Light\'s Hammer\'s shipped impact SV 90040 (V-2 '
          'DA_TRUE_JUDGMENT_ALT, a holy area burst). The item\'s 25 s cooldown is per copy.',
    raw_overrides=kit_raw('A pulse of faith wakes every sleeping ally nearby and wards them from sleep.',
                          'Warded from sleep.', instant=True, SpellVisualID_1=DA_TRUE_JUDGMENT_ALT,
                          AttributesEx=ATTR1_NO_THREAT),
)
scripted_by(medallion_206588, 'spell_strat_grand_lie_medallion')
