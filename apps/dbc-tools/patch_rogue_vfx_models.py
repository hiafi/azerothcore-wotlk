#!/usr/bin/env python3
"""
One-off DBC content patch: Rogue rework spell visuals mined from the Ascension client backup, as new SpellVisual /
SpellVisualKit / SpellVisualEffectName / SoundEntries rows. Same shape as patch_deathknight_vfx_models.py (whose row
helpers, from patch_priest_vfx_models.py, this reuses) and docs/ascension-asset-mining.md Part 3.

ID blocks (claimed here for the rogue; T1 adds the matching ids.yaml `reservations: rogue:` rows):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: ROGUE_VISUAL_BLOCK 90250-90299 (90250-90289 budgeted for P0).
- SoundEntries: ROGUE_SOUND_BLOCK 90121-90140.

These rows are REAL: the P0 spike spells (rogue-rework P0-HANDOFF item 9) only wear them, and the reworked Kingsbane,
Poison Bomb, Pistol Shot, Grappling Hook, Blade Rush and Death from Above re-point at them. Sources (Ascension
Data/DBFilesClient/Spell.dbc, patch-S.MPQ SpellVisual*.dbc, patch-M.MPQ SoundEntries.dbc), each checked id by id and
file by file against our working copy:

- Kingsbane (277580, SV 42720) -> SV_KINGSBANE: CastKit 42721 (Special1H + a CharProc 8 flash, sound 76502 three
  spell_ro_envenom_cast oggs) and TargetImpactKit 42722 (7fx_rogue_kingsbane_state.m2 on chest and base, stock sound
  10720 Disembowel_Impact). Model, skin and both textures are custom (patch-N).
- Poison Bomb (284169, SV 42787) -> SV_POISON_BOMB: one row carries the vial and the cloud. CastKit 21882 is not in our
  DBC but every id in it is stock (AttackThrown, Nature Cast Hand 73, sound 5335 PoisonCloud), so it is minted;
  MissileModel 42789 = stock SpellVisualEffectName 5597 (the same thrown_1h_bomb_c_01, same scale); MissileMotion 13
  "Parabola" is stock; PersistentAreaKit 42788 wears the custom fill_poison_precast_01.m2 (Scale 2.0), stock sound 5335.
- Pistol Shot (276631, SV 20527) -> SV_PISTOL_SHOT: CastKit 20933 (AnimID 49 AttackRifle, a 0.3-scale
  blackfuse_explosion_impact_base flash on the LEFT weapon, sound 83342 five spell_ro_pistolshot_cast oggs; Ascension's
  effect id 90005 collides with our Priest row, so it is re-minted), ImpactKit 20934 (cfx_hunter_barrage_impactchest,
  sound 83343 ten projectile_bullet_impact oggs), MissileModel 56472 = stock 4586 (spells\\explosive_shot_missile, same
  scale). No SpellVisualKitModelAttach row exists for either kit: the visual attaches NO gun model (Combat Q1); the
  rogue plays the rifle-fire animation with whatever is in its hands.
- Grappling Hook (Ascension's rogue Grappling Hook 760056 wears SV 22087; the rope 685006 / SV 22174 is an aura on a
  summoned anchor creature) -> SV_GRAPPLING_HOOK: PrecastKit = stock 171 (ReadyThrown, identical to Ascension's but for
  one unused float) and CastKit 21971 re-minted (AttackThrown + CharProc 8 as stock kit 172, sound 71047 four
  spell_ro_grapplinghook_whoosh_cast oggs). The ROPE DOES NOT PORT: kit 22197 is CharProc 0 = SpellChainEffects id
  200462, an Ascension-only SpellChainEffects.dbc row this pipeline does not ship, and a beam needs a unit at the far
  end (Ascension summons creature 840057 at the point) while P0 Grappling Hook is a plain JUMP_DEST to a point.
- Blade Rush (805408, SV 999796) -> SV_BLADE_RUSH: CastKit 998864 (Attack1HPierce, cfx_paladin_templarsverdict_casthand
  on both hands, sound 54253 three spell_wr_ragingblow_revamp_cast oggs) and ImpactKit 998865 (CombatWound,
  CFX_Paladin_AvengersShield_Impact on the chest, sound 55694 three 1h_sword_crithit_flesh oggs). Ascension's -1 /
  0xFFFFFFFF filler in unused fields is written as the stock zero / NOFIELD.
- Death from Above (520385 / 520402 / 520404 / 520808, SVs 988-991 and 2888): these Ascension rows are NOT a rogue
  visual. They are a class-30 dragon ability (Fire school, "soar forward in a blaze of glory", NetherDragon / chromatic
  dragon roars, dragon breath). Ported as the handoff asks, as candidates for the playtest to judge:
  SV_DEATH_FROM_ABOVE_CAST from 989 (CastKit 1346: fire_fireball_impact_darker on the chest and the
  7fx_shivarracoven_whirlingsaber_impact_base ring on the ground; the NetherDragonAttack sound is swapped for stock
  3330 HeroicLeap, which fits a leap) and SV_DEATH_FROM_ABOVE_LANDING from 991's ImpactKit 1348
  (blackfuse_partsexplosion_impact_02, stock sound 17656 Halion_Fiery_Explosion, the same wav Ascension's 312611
  plays). Not ported: 991's StateKit (the root debuff's 10FX burnout model, ten Shadowlands/Dragonflight textures),
  990 (dragon breath), 988 (the same CastKit as 989) and 2888 (the fire DoT zone). No flight state kit exists, so P0
  Death from Above: In Flight wears no visual.

Assets (gitignored working copies; `--extract` pulls them from the Ascension backup, read-only, and converts the oggs):
every model + skin, every texture in each model's texture table that the stock 3.3.5a archives (common*, expansion,
lichking, patch, patch-2, patch-3) lack, flat into SPELLS/ (spells\\ paths) or at their full path under EXTRA/
(creature\\ and world\\ paths), and the sounds as 16-bit PCM .wav in SOUND/ (packed at Sound\\Spells\\).

SpellVisual is server-loaded, so `--sql-out PATH` emits its overlay. SpellVisualKit, SpellVisualEffectName and
SoundEntries are client-only.

Usage:
    python3 apps/dbc-tools/patch_rogue_vfx_models.py --extract     # once: pull the assets from the Ascension backup
    python3 apps/dbc-tools/patch_rogue_vfx_models.py --dry-run     # print rows + asset check + SQL, write nothing
    python3 apps/dbc-tools/patch_rogue_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from lib import dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, NOFIELD, _kit_row, _merge, _row, _sound_row, model_path

SPELLS_DIR = DBC_DIR.parent / "SPELLS"
SOUND_DIR = DBC_DIR.parent / "SOUND"
EXTRA_DIR = DBC_DIR.parent / "EXTRA"
ASCENSION_DATA = Path("/mnt/drive6/Permaseeds/AscensionBackup/Data")  # read-only reference backup

# Rogue blocks (T1 writes the matching ids.yaml reservation).
ROGUE_VISUAL_BLOCK = {"start": 90250, "end": 90299}
ROGUE_SOUND_BLOCK = {"start": 90121, "end": 90140}

# --- SpellVisualEffectName ---
EFFECT_KINGSBANE_CHEST = 90250        # Ascension 51746
EFFECT_KINGSBANE_BASE = 90251         # Ascension 28897 (same model, its own scale range)
EFFECT_POISON_BOMB_CLOUD = 90252      # Ascension 42790
EFFECT_PISTOL_SHOT_MUZZLE = 90253     # Ascension 90005 (re-minted: our 90005 is a Priest row)
EFFECT_PISTOL_SHOT_IMPACT = 90254     # Ascension 50529
EFFECT_BLADE_RUSH_HAND = 90255        # Ascension 546870
EFFECT_BLADE_RUSH_IMPACT = 90256      # Ascension 136140
EFFECT_DFA_CAST_CHEST = 90257         # Ascension 50894
EFFECT_DFA_CAST_GROUND = 90258        # Ascension 50252
EFFECT_DFA_LANDING_BASE = 90259       # Ascension 504440

# --- SpellVisualKit ---
KIT_KINGSBANE_CAST = 90250            # Ascension 42721
KIT_KINGSBANE_IMPACT = 90251          # Ascension 42722
KIT_POISON_BOMB_CAST = 90252          # Ascension 21882 (all-stock contents, no stock kit matches)
KIT_POISON_BOMB_CLOUD = 90253         # Ascension 42788
KIT_PISTOL_SHOT_CAST = 90254          # Ascension 20933
KIT_PISTOL_SHOT_IMPACT = 90255        # Ascension 20934
KIT_GRAPPLING_HOOK_CAST = 90256       # Ascension 21971
KIT_BLADE_RUSH_CAST = 90257           # Ascension 998864
KIT_BLADE_RUSH_IMPACT = 90258         # Ascension 998865
KIT_DFA_CAST = 90259                  # Ascension 1346
KIT_DFA_LANDING = 90260               # Ascension 1348

# --- SpellVisual (the spike spells in source/classes/rogue/rogue_p0_spike.py wear these) ---
SV_KINGSBANE = 90250                  # Ascension 42720 -> P0 Kingsbane 204385
SV_POISON_BOMB = 90251                # Ascension 42787 -> P0 Poison Bomb 204386
SV_PISTOL_SHOT = 90252                # Ascension 20527 -> P0 Pistol Shot 204387
SV_GRAPPLING_HOOK = 90253             # Ascension 22087 -> P0 Grappling Hook 204383
SV_BLADE_RUSH = 90254                 # Ascension 999796 -> P0 Blade Rush 204388
SV_DEATH_FROM_ABOVE_CAST = 90255      # Ascension 989 -> P0 Death from Above 204379
SV_DEATH_FROM_ABOVE_LANDING = 90256   # Ascension 991 (ImpactKit only) -> P0 Death from Above: Landing 204381

# --- SoundEntries ---
SOUND_KINGSBANE_CAST = 90121          # Ascension 76502
SOUND_PISTOL_SHOT_CAST = 90122        # Ascension 83342
SOUND_PISTOL_SHOT_IMPACT = 90123      # Ascension 83343
SOUND_GRAPPLING_HOOK_CAST = 90124     # Ascension 71047
SOUND_BLADE_RUSH_CAST = 90125         # Ascension 54253
SOUND_BLADE_RUSH_IMPACT = 90126       # Ascension 55694

# --- Stock ids reused as-is (identical in our working copy) ---
EFFECT_POISON_BOMB_VIAL_STOCK = 5597      # "Spell Object: Plague Bomb (New - Green)", thrown_1h_bomb_c_01
EFFECT_EXPLOSIVE_SHOT_MISSILE_STOCK = 4586
EFFECT_NATURE_CAST_HAND_STOCK = 73
KIT_READY_THROWN_STOCK = 171              # Grappling Hook precast
SOUND_DISEMBOWEL_IMPACT_STOCK = 10720
SOUND_POISON_CLOUD_STOCK = 5335
SOUND_HEROIC_LEAP_STOCK = 3330
SOUND_HALION_FIERY_EXPLOSION_STOCK = 17656
MISSILE_MOTION_PARABOLA_STOCK = 13

ANIM_COMBAT_WOUND = 9
ANIM_ATTACK_RIFLE = 49
ANIM_SPECIAL_1H = 57
ANIM_ATTACK_1H_PIERCE = 85
ANIM_ATTACK_THROWN = 107
CHAR_PROC_FLASH = 8                       # stock kit 172's proc (AttackThrown + a colour flash)
NO_ATTACHMENT = -1                        # SpellVisual's signed "none" (dbcfmt.SPELLVISUAL.signed, bug 556)

MODEL_KINGSBANE = "7fx_rogue_kingsbane_state"
MODEL_POISON_BOMB_CLOUD = "fill_poison_precast_01"
MODEL_PISTOL_SHOT_MUZZLE = "blackfuse_explosion_impact_base"
MODEL_PISTOL_SHOT_IMPACT = "cfx_hunter_barrage_impactchest"
MODEL_BLADE_RUSH_HAND = "cfx_paladin_templarsverdict_casthand"
MODEL_BLADE_RUSH_IMPACT = "cfx_paladin_avengersshield_impact"
MODEL_DFA_CAST_CHEST = "fire_fireball_impact_darker"
MODEL_DFA_CAST_GROUND = "7fx_shivarracoven_whirlingsaber_impact_base"
MODEL_DFA_LANDING = "blackfuse_partsexplosion_impact_02"

# (archive, path in the archive) -> file name in SPELLS/. Every model is M2 version 264 (loadable by 3.3.5a) with all
# sequences inline (no .anim files); the textures are exactly the non-stock entries of each model's texture table.
SPELLS_ASSETS = [
    ("patch-N", "SPELLS/7fx_rogue_kingsbane_state.m2"),
    ("patch-N", "SPELLS/7fx_rogue_kingsbane_state00.skin"),
    ("patch-N", "SPELLS/smoke_puffy_mask_verysoft.blp"),
    ("patch-N", "SPELLS/dirt_scroll_wispy_rejuv.blp"),
    ("patch-N", "SPELLS/fill_poison_precast_01.m2"),
    ("patch-N", "SPELLS/fill_poison_precast_0100.skin"),
    ("patch-N", "SPELLS/t_vfx_smokeanim02_blured.blp"),
    ("patch-N", "SPELLS/blackfuse_explosion_impact_base.m2"),
    ("patch-N", "SPELLS/blackfuse_explosion_impact_base00.skin"),
    ("patch-N", "SPELLS/t_vfx_smoke_simulation.blp"),
    ("patch-N", "SPELLS/cloud_variations_4x4.blp"),
    ("patch-N", "SPELLS/cfx_hunter_barrage_impactchest.m2"),
    ("patch-N", "SPELLS/cfx_hunter_barrage_impactchest00.skin"),
    ("patch-N", "SPELLS/weaponimpact_streak_orange.blp"),
    ("patch-N", "SPELLS/weaponimpact_trihit_gold.blp"),
    ("patch-N", "SPELLS/t_star2warm.blp"),
    ("patch-N", "SPELLS/cfx_paladin_templarsverdict_casthand.m2"),
    ("patch-N", "SPELLS/cfx_paladin_templarsverdict_casthand00.skin"),
    ("patch-N", "SPELLS/7fx_alphamask_glow_pala.blp"),
    ("patch-N", "SPELLS/fire_2x2_sharp_mod4x.blp"),
    ("patch-N", "SPELLS/7fx_arcane_wisps_paladin.blp"),
    ("patch-N", "SPELLS/7fx_energyscroll_fire_stylized.blp"),
    ("patch-N", "SPELLS/bubble_soft_distortion_03.blp"),
    ("patch-N", "SPELLS/smoke_loose_02_256_blend_contrast.blp"),
    ("patch-N", "SPELLS/wispymagic_vert_azeritemist_blue_128_greyrotate_blend.blp"),
    ("patch-N", "SPELLS/white8x8.blp"),
    ("patch-N", "SPELLS/alpha_streak_mid_big.blp"),
    ("patch-N", "SPELLS/weapontrail_paladin_templarsverdict2.blp"),
    ("patch-N", "SPELLS/ember_offset_shape_ba_128.blp"),
    ("patch-N", "SPELLS/cfx_paladin_avengersshield_impact.m2"),
    ("patch-N", "SPELLS/cfx_paladin_avengersshield_impact00.skin"),
    ("patch-N", "SPELLS/weaponimpact_streak_gold.blp"),
    ("patch-N", "SPELLS/weaponimpact_streak_holy.blp"),
    ("patch-N", "SPELLS/fire_fireball_impact_darker.m2"),
    ("patch-N", "SPELLS/fire_fireball_impact_darker00.skin"),
    ("patch-N", "SPELLS/ember_offset_streak.blp"),
    ("patch-N", "SPELLS/t_vfx_fire_anim_stylized_desat_02.blp"),
    ("patch-N", "SPELLS/fire_sharp_mod2x_a.blp"),
    ("patch-N", "SPELLS/flowerstar_blendadd.blp"),
    ("patch-N", "SPELLS/cloud_puffysofter_mod4x.blp"),
    ("patch-N", "SPELLS/cloud_puffysofter_highlights.blp"),
    ("patch-N", "SPELLS/7fx_shivarracoven_whirlingsaber_impact_base.m2"),
    ("patch-N", "SPELLS/7fx_shivarracoven_whirlingsaber_impact_base00.skin"),
    ("patch-N", "SPELLS/7fx_shivarracoven_whirlingsaber_impact_base01.skin"),
    ("patch-N", "SPELLS/7fx_desat_ghostly_fire_wrap_a.blp"),
    ("patch-N", "SPELLS/7fx_energyscroll_fire_dark_a.blp"),
    ("patch-N", "SPELLS/7fx_flash_shard_fire.blp"),
    ("patch-N", "SPELLS/7fx_alphamask_firemask_01.blp"),
    ("patch-N", "SPELLS/7fx_smoketile_fire_a2.blp"),
    ("patch-N", "SPELLS/7fx_alphamask_shockwaveholy_a.blp"),
    ("patch-N", "SPELLS/fire_blurred_mod2x_a.blp"),
    ("patch-N", "SPELLS/7fx_desat_ghostly_fire_wrapfull_a.blp"),
    ("patch-N", "SPELLS/7fx_alphamask_fire_anim_stylized_desat_03.blp"),
    ("patch-N", "SPELLS/firetornado_flames02_red.blp"),
    ("patch-N", "SPELLS/ember_offset_streak_desat2.blp"),
    ("patch-N", "SPELLS/7fx_fire_puff_fire.blp"),
    ("patch-N", "SPELLS/7fx_smoketile_a_1.blp"),
    ("patch-N", "SPELLS/blackfuse_partsexplosion_impact_02.m2"),
    ("patch-N", "SPELLS/blackfuse_partsexplosion_impact_0200.skin"),
    ("patch-N", "SPELLS/ember_offset.blp"),
    ("patch-N", "SPELLS/sha_firebeam_faint_square.blp"),
]

# Textures a model hard-codes outside spells\ that stock lacks: packed at their full path from EXTRA/.
EXTRA_ASSETS = [
    ("patch-CG", "creature/goblinbombbot/goblinbombbot256.blp"),
    ("patch-WC3", "world/dungeon/orgrimmarraid/t_vfx_fire_anim_stylized_desat_05.blp"),
]

# SoundEntries id -> (archive directory, file stems): converted .ogg -> .wav into SOUND/.
SOUND_FILES = {
    SOUND_KINGSBANE_CAST: ("sound/spells", [f"spell_ro_envenom_cast_0{i}" for i in range(1, 4)]),
    SOUND_PISTOL_SHOT_CAST: ("sound/spells", [f"spell_ro_pistolshot_cast_0{i}" for i in range(1, 6)]),
    SOUND_PISTOL_SHOT_IMPACT: ("sound/item/weapons/gun", [f"projectile_bullet_impact{i:02d}" for i in range(1, 11)]),
    SOUND_GRAPPLING_HOOK_CAST: ("sound/spells", [f"spell_ro_grapplinghook_whoosh_cast_0{i}" for i in range(1, 5)]),
    SOUND_BLADE_RUSH_CAST: ("sound/spells", [f"spell_wr_ragingblow_revamp_cast_0{i}" for i in range(1, 4)]),
    SOUND_BLADE_RUSH_IMPACT: ("sound/item/weapons/sword1h", [f"1h_sword_crithit_flesh_0{i}" for i in range(1, 4)]),
}
SOUND_ARCHIVE = "patch-O"


def _asset_paths() -> list[Path]:
    paths = [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS]
    paths += [EXTRA_DIR / p for _, p in EXTRA_ASSETS]
    paths += [SOUND_DIR / f"{stem}.wav" for _, stems in SOUND_FILES.values() for stem in stems]
    return paths


def build_effect_name_rows() -> list[dict]:
    def effect(id_, name, model, area, scale, min_scale, max_scale):
        return _row(dbcfmt.SPELLVISUALEFFECTNAME, id_, Name=f"{name} (Custom)", FileName=model_path(model),
                    AreaEffectSize=area, Scale=scale, MinAllowedScale=min_scale, MaxAllowedScale=max_scale)

    return [
        effect(EFFECT_KINGSBANE_CHEST, "Kingsbane State Chest", MODEL_KINGSBANE, 1.0, 1.0, 0.01, 100.0),
        effect(EFFECT_KINGSBANE_BASE, "Kingsbane State Base", MODEL_KINGSBANE, 0.0, 1.0, 0.5, 1.5),
        effect(EFFECT_POISON_BOMB_CLOUD, "Poison Bomb Cloud", MODEL_POISON_BOMB_CLOUD, 0.0, 2.0, 0.1, 2.0),
        effect(EFFECT_PISTOL_SHOT_MUZZLE, "Pistol Shot Muzzle Flash", MODEL_PISTOL_SHOT_MUZZLE, 1.0, 0.3, 0.01, 100.0),
        effect(EFFECT_PISTOL_SHOT_IMPACT, "Pistol Shot Impact Chest", MODEL_PISTOL_SHOT_IMPACT, 1.0, 1.0, 0.01, 100.0),
        effect(EFFECT_BLADE_RUSH_HAND, "Blade Rush Cast Hand", MODEL_BLADE_RUSH_HAND, 1.0, 0.6, 0.5, 0.7),
        effect(EFFECT_BLADE_RUSH_IMPACT, "Blade Rush Impact Chest", MODEL_BLADE_RUSH_IMPACT, 0.0, 1.0, 1.0, 1.0),
        effect(EFFECT_DFA_CAST_CHEST, "Death from Above Cast Chest", MODEL_DFA_CAST_CHEST, 1.0, 1.0, 0.01, 100.0),
        effect(EFFECT_DFA_CAST_GROUND, "Death from Above Cast Ground", MODEL_DFA_CAST_GROUND, 1.0, 1.0, 0.01, 100.0),
        effect(EFFECT_DFA_LANDING_BASE, "Death from Above Landing Base", MODEL_DFA_LANDING, 1.0, 1.0, 0.01, 1.0),
    ]


def build_kit_rows() -> list[dict]:
    flash = {"CharProc_1": CHAR_PROC_FLASH}
    return [
        _kit_row(KIT_KINGSBANE_CAST, AnimID=ANIM_SPECIAL_1H, SoundID=SOUND_KINGSBANE_CAST, **flash,
                 CharParamZero_1=1408300.0, CharParamOne_1=15.0, CharParamTwo_1=400.0, CharParamThree_1=96.0),
        _kit_row(KIT_KINGSBANE_IMPACT, AnimID=NOFIELD, ChestEffect=EFFECT_KINGSBANE_CHEST,
                 BaseEffect=EFFECT_KINGSBANE_BASE, SoundID=SOUND_DISEMBOWEL_IMPACT_STOCK),
        _kit_row(KIT_POISON_BOMB_CAST, AnimID=ANIM_ATTACK_THROWN, RightHandEffect=EFFECT_NATURE_CAST_HAND_STOCK,
                 SoundID=SOUND_POISON_CLOUD_STOCK),
        _kit_row(KIT_POISON_BOMB_CLOUD, AnimID=NOFIELD, WorldEffect=EFFECT_POISON_BOMB_CLOUD,
                 SoundID=SOUND_POISON_CLOUD_STOCK),
        _kit_row(KIT_PISTOL_SHOT_CAST, AnimID=ANIM_ATTACK_RIFLE, LeftWeaponEffect=EFFECT_PISTOL_SHOT_MUZZLE,
                 SoundID=SOUND_PISTOL_SHOT_CAST),
        _kit_row(KIT_PISTOL_SHOT_IMPACT, AnimID=NOFIELD, ChestEffect=EFFECT_PISTOL_SHOT_IMPACT,
                 SoundID=SOUND_PISTOL_SHOT_IMPACT),
        _kit_row(KIT_GRAPPLING_HOOK_CAST, AnimID=ANIM_ATTACK_THROWN, SoundID=SOUND_GRAPPLING_HOOK_CAST, **flash,
                 CharParamZero_1=16711680.0, CharParamOne_1=8.0, CharParamTwo_1=400.0, CharParamThree_1=128.0),
        _kit_row(KIT_BLADE_RUSH_CAST, AnimID=ANIM_ATTACK_1H_PIERCE, LeftHandEffect=EFFECT_BLADE_RUSH_HAND,
                 RightHandEffect=EFFECT_BLADE_RUSH_HAND, SoundID=SOUND_BLADE_RUSH_CAST),
        _kit_row(KIT_BLADE_RUSH_IMPACT, AnimID=ANIM_COMBAT_WOUND, ChestEffect=EFFECT_BLADE_RUSH_IMPACT,
                 SoundID=SOUND_BLADE_RUSH_IMPACT),
        _kit_row(KIT_DFA_CAST, AnimID=NOFIELD, ChestEffect=EFFECT_DFA_CAST_CHEST, WorldEffect=EFFECT_DFA_CAST_GROUND,
                 SoundID=SOUND_HEROIC_LEAP_STOCK),
        _kit_row(KIT_DFA_LANDING, AnimID=NOFIELD, BaseEffect=EFFECT_DFA_LANDING_BASE,
                 SoundID=SOUND_HALION_FIERY_EXPLOSION_STOCK),
    ]


def build_spellvisual_rows() -> list[dict]:
    def visual(id_, **fields):
        row = _row(dbcfmt.SPELLVISUAL, id_, MissileAttachment=NO_ATTACHMENT)
        row.update(fields)
        return row

    return [
        visual(SV_KINGSBANE, CastKit=KIT_KINGSBANE_CAST, TargetImpactKit=KIT_KINGSBANE_IMPACT),
        visual(SV_POISON_BOMB, CastKit=KIT_POISON_BOMB_CAST, HasMissile=1, MissileModel=EFFECT_POISON_BOMB_VIAL_STOCK,
               MissileMotion=MISSILE_MOTION_PARABOLA_STOCK, PersistentAreaKit=KIT_POISON_BOMB_CLOUD),
        visual(SV_PISTOL_SHOT, CastKit=KIT_PISTOL_SHOT_CAST, ImpactKit=KIT_PISTOL_SHOT_IMPACT, HasMissile=1,
               MissileModel=EFFECT_EXPLOSIVE_SHOT_MISSILE_STOCK, MissileDestinationAttachment=1, MissileAttachment=1,
               Flags=1),
        visual(SV_GRAPPLING_HOOK, PrecastKit=KIT_READY_THROWN_STOCK, CastKit=KIT_GRAPPLING_HOOK_CAST),
        visual(SV_BLADE_RUSH, CastKit=KIT_BLADE_RUSH_CAST, ImpactKit=KIT_BLADE_RUSH_IMPACT,
               MissileDestinationAttachment=1, Flags=1),
        visual(SV_DEATH_FROM_ABOVE_CAST, CastKit=KIT_DFA_CAST),
        visual(SV_DEATH_FROM_ABOVE_LANDING, ImpactKit=KIT_DFA_LANDING),
    ]


def build_sound_rows() -> list[dict]:
    def sound(id_, name, *, volume=1.0, sound_type=1, eax=0):
        _, stems = SOUND_FILES[id_]
        row = _sound_row(id_, name, stems, min_distance=8.0, cutoff=45.0, eax=eax)
        row["Volumefloat"] = volume
        row["SoundType"] = sound_type
        return row

    return [
        sound(SOUND_KINGSBANE_CAST, "Rogue Kingsbane Cast (Custom)", eax=2),
        sound(SOUND_PISTOL_SHOT_CAST, "Rogue Pistol Shot Cast (Custom)", volume=0.5, eax=2),
        sound(SOUND_PISTOL_SHOT_IMPACT, "Rogue Pistol Shot Impact (Custom)", sound_type=2),
        sound(SOUND_GRAPPLING_HOOK_CAST, "Rogue Grappling Hook Whoosh (Custom)"),
        sound(SOUND_BLADE_RUSH_CAST, "Rogue Blade Rush Cast (Custom)"),
        sound(SOUND_BLADE_RUSH_IMPACT, "Rogue Blade Rush Impact (Custom)"),
    ]


def build_pending_sql() -> str:
    """Server-side overlay for SpellVisual only (the other three tables are client-only). Range-deletes exactly the ids
    this script mints, so a rerun is idempotent."""
    rows = build_spellvisual_rows()
    return _table_block(
        dbcfmt.SPELLVISUAL, {"start": min(r["ID"] for r in rows), "end": max(r["ID"] for r in rows)}, rows, [],
    ) + "\n"


def _check_block(rows: list[dict], block: dict, what: str) -> None:
    for row in rows:
        if not block["start"] <= row["ID"] <= block["end"]:
            raise SystemExit(f"{what} id {row['ID']} is outside the rogue block {block}")


def _extract_one(archive: str, archive_path: str, dest: Path, workdir: Path) -> None:
    subprocess.run(["smpq", "-x", str(ASCENSION_DATA / f"{archive}.MPQ"), archive_path], cwd=workdir, check=True,
                   capture_output=True)
    # smpq writes the archive's own spelling (e.g. SPELLS/Fire_2x2_Sharp_Mod4x.blp); MPQ lookups ignore case.
    wanted = archive_path.lower()
    extracted = next((p for p in workdir.rglob("*") if p.is_file() and
                      p.relative_to(workdir).as_posix().lower() == wanted), None)
    if extracted is None:
        raise SystemExit(f"smpq did not extract {archive_path} from {archive}.MPQ")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(extracted), dest)


def extract_assets() -> None:
    """Pulls every asset from the Ascension backup (read-only) into the working copy; files already present are kept."""
    added = 0
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for archive, path in SPELLS_ASSETS:
            dest = SPELLS_DIR / Path(path).name
            if not dest.is_file():
                _extract_one(archive, path, dest, workdir)
                added += 1
        for archive, path in EXTRA_ASSETS:
            dest = EXTRA_DIR / path
            if not dest.is_file():
                _extract_one(archive, path, dest, workdir)
                added += 1
        for directory, stems in SOUND_FILES.values():
            for stem in stems:
                dest = SOUND_DIR / f"{stem}.wav"
                if dest.is_file():
                    continue
                ogg = workdir / f"{stem}.ogg"
                _extract_one(SOUND_ARCHIVE, f"{directory}/{stem}.ogg", ogg, workdir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(ogg), "-acodec", "pcm_s16le",
                                str(dest)], check=True)
                added += 1
    print(f"extracted {added} asset(s) into {DBC_DIR.parent} (0 means everything was already there)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sql-out", type=Path, default=None,
                        help="Write the matching server-side SQL migration to this path (see module docstring).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the rows, the asset check and the SpellVisual SQL; write nothing.")
    parser.add_argument("--extract", action="store_true",
                        help="Pull the missing assets from the Ascension backup into the working copy, then stop.")
    args = parser.parse_args()

    if args.extract:
        extract_assets()
        return

    missing = [str(p) for p in _asset_paths() if not p.is_file()]
    if missing:
        raise SystemExit(f"missing assets: {missing} - run with --extract first (see docstring)")

    effect_rows = build_effect_name_rows()
    kit_rows = build_kit_rows()
    visual_rows = build_spellvisual_rows()
    sound_rows = build_sound_rows()
    for rows, what in ((effect_rows, "SpellVisualEffectName"), (kit_rows, "SpellVisualKit"),
                       (visual_rows, "SpellVisual")):
        _check_block(rows, ROGUE_VISUAL_BLOCK, what)
    _check_block(sound_rows, ROGUE_SOUND_BLOCK, "SoundEntries")

    if args.dry_run:
        for row in effect_rows:
            print("SpellVisualEffectName:", row)
        for row in kit_rows:
            print("SpellVisualKit (non-zero fields):", {k: v for k, v in row.items() if v})
        for row in visual_rows:
            print("SpellVisual (non-zero fields):", {k: v for k, v in row.items() if v})
        for row in sound_rows:
            print("SoundEntries (non-empty fields):", {k: v for k, v in row.items() if v not in (0, 0.0, "")})
        print("assets packed by build_patch_m.py:")
        for path in _asset_paths():
            print(f"  {path.relative_to(DBC_DIR.parent)} ({path.stat().st_size} bytes)")
        print(build_pending_sql())
        return

    added = 0
    added += _merge(DBC_DIR / "SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, effect_rows)
    added += _merge(DBC_DIR / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, kit_rows)
    added += _merge(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL, visual_rows)
    added += _merge(DBC_DIR / "SoundEntries.dbc", dbcfmt.SOUNDENTRIES, sound_rows)
    print(f"added {added} row(s) across the 4 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
