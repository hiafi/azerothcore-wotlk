"""
The Ragefire Chasm boss list items (wave 4 dungeon items, after the Deadmines, Shadowfang Keep and Scarlet Monastery
precedents): the 25 approved list items of the four bosses (docs/dungeons/ragefire-chasm-rework.md ## Loot "Final
list", approved 2026-11-21, ruling 13; copied in docs/dungeons/dungeon-loot-vanilla.md "### Ragefire Chasm"). Out of
scope here: the 3 Taragaman the Hungerer, Starving hard mode items (ragefire_chasm_hard_mode.py), the quest items
(Taragaman the Hungerer's Heart 14540, Maur's satchel) and the loot tables (ragefire_chasm_loot.py).

Ragefire Chasm is a leveling dungeon (levels 13-18). Every stock rare of the dungeon is item level 18, required level
13, Rare (live item_template, 2026-11-24), so every Normal tier takes that: a stock item keeps its stock row (`base=`:
the stock id is the Normal tier) and every new item takes item level 18 with the default required level 13. Heroic is
66 Epic with the Heroic flag, then the three empowered steps (ladders.py `VANILLA_DUNGEON`). New items copy a stock look
(`like=`, look only) and are Bind on Pickup.

Bosses: Oggleflint 6 items, Jergosh the Invoker 6, Bazzalan 6, Taragaman the Hungerer 7 (25 in all). The six stock
entries are Robe of Evocation 14150, Cavedweller Bracers 14147, Chanting Blade 14151 (Jergosh), Crystalline Cuffs
14148, Subterranean Cape 14149 and Cursed Felblade 14145 (Taragaman); the other 19 are new.

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed (the doc's order of secondaries does not matter to an Even shape). The ring carries secondaries
only (`primary=None`, share 0). Tunneler's Hide Cap, the dungeon's Leather Tank head, takes a quarter more Stamina
(`extra_stamina=0.25`, the Deadmines Smelting Pants pick). Relics: Libram of the Hungerer (paladin) and Idol of the
Corrupted Grove (druid) are stats only, like the earlier dungeons' relics. No new item shape is needed: Parry/
Versatility (Any) and Dodge/Versatility exist, and the three-secondary Crit/Haste/Mastery exists.

**Kept stock effect**: Cursed Felblade's Chance on hit, Cripple 18381 (ppm 1.2, no charges), is the stock row's only
spell slot and is kept (`keep_spells=True`, the Ravager precedent); it is the same on every tier (a stock spell cannot
scale) and the item pays 0.7 of the budget for it (itemization-changes.md section 3). Every other stock entry has no
spell slot (verified live 2026-11-24: spellid_1..5 all 0 on 14147, 14148, 14149, 14150, 14151), so nothing is absorbed.
Crystalline Cuffs' Spell Power and Intellect lines are stat slots, not spells: they fold into the shape budget.

**Stat changes of the stock entries** (the shape replaces the stock stats): Robe of Evocation Intellect, Crit, Mastery
(stock Intellect, Crit); Cavedweller Bracers Intellect, Haste, Versatility (stock Strength, Stamina: the dead primary
fixed); Chanting Blade Intellect, Haste (stock Agility); Crystalline Cuffs Spirit, Crit, Haste (stock Spirit,
Intellect, Spell Power); Subterranean Cape Strength, Crit, Versatility (stock Agility, Strength); Cursed Felblade
Strength, Parry (stock none). None of the six changes class, subclass or slot, so no column override is needed.

**Caster main-hand cell.** Chanting Blade (Intellect, Haste: a caster dagger) declares the 60-100 physical role cell
(0.445) on every tier, like the earlier dungeons' caster main-hands (blackrock_depths.py, scarlet_monastery.py; the
Blackrock gear review's S2 and the level 60 stat curve's ruling that a weapon with spell power takes the physical
budget): its stock level is below 60, so without it the Normal tier would read the 1-59 caster cell (0.685) and the
Heroic tier the 60-100 one (0.507), two different curves for one item. The check passes either way (designer
question). The staff is a two-hander and keeps its own caster cell, as Illusionary Rod does.

**Sockets.** The doc names no per-item pick, so every pick is a designer question (STAGE-RF-LIST report). The shared
rule (boss-rework-systems.md section 2; deadmines.py): about one standalone armor piece or weapon per boss carries 1,
a two-hander 2, trinkets and jewelry never, Normal tiers none (ladders.py). The first socket is red on damage and
healing gear and blue on tank gear. The socket bonus is a stock +4 rating (2874 Crit, 3267 Haste, 3359 Parry): no
enchant exists for Mastery, Versatility, Cooldown Haste or Proc Chance, so a first secondary of those takes Haste or
Crit. Picks, one per boss:

    Oggleflint             Chieftain's Rockplate Pauldrons (tank)  blue   +4 Parry
    Jergosh the Invoker    Searing Blade Ritual Leggings           red    +4 Haste
    Bazzalan               Cleft of Shadow Grips                   red    +4 Crit
    Taragaman              Hungerer's Legplates                    red    +4 Crit

Stock resistances and random properties: none of the six stock items carries one, so nothing is cleared.
"""

from lib.dsl.items import Socket, item

from .ladders import VANILLA_DUNGEON

# Socket bonus enchants (stock SpellItemEnchantment ids, +4 each; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_PARRY_4 = 3359

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does
LEVEL = 18  # every stock rare of the dungeon: item level 18, required level 13 (the default for a new item)
EXTRA_STAMINA = 0.25  # "extra Stamina" on a tank piece: a quarter more than the tier's baseline

# Weapon-tier role cell (scarlet_monastery.py, the Blackrock gear review's S2): a caster main-hand below level 60 would
# take the 1-59 cell on its Normal tier and the 60-100 cell from Heroic up, a 2.4x step (the ladder check refuses over
# 1.5x). The 60-100 cell is declared on every tier instead, so the step is the budget curve's alone.
# physical InventoryType 13 ilvl 60-100: caster weapons take the physical budget (level60-stat-curve 1.8)
CASTER_MAIN_HAND_MULT = 0.445

R, B = Socket.RED, Socket.BLUE

# ---------------------------------------------------------------------------------------------------------------------
# Oggleflint (item level 18)

item("rfc_chieftains_rockplate_pauldrons", name="Chieftain's Rockplate Pauldrons", like=8144, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Parry/Versatility (Any)",
     sockets=(B,), socket_bonus=BONUS_PARRY_4)
item("rfc_borer_chased_treads", name="Borer-chased Treads", like=6350, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Haste")
# The dungeon's Leather Tank head: Agility, Dodge, Versatility and a quarter more Stamina.
item("rfc_tunnelers_hide_cap", name="Tunneler's Hide Cap", like=7413, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Dodge/Versatility", extra_stamina=EXTRA_STAMINA)
item("rfc_oggleflints_skullthumper", name="Oggleflint's Skullthumper", like=1440, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit (Solo)")
item("rfc_ring_of_the_cleft", name="Ring of the Cleft", like=20821, ilvl=LEVEL, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Haste", primary_share=0)
item("rfc_eye_of_the_earthborer", name="Eye of the Earthborer", like=5079, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# Jergosh the Invoker (item level 18)

item("rfc_robe_of_evocation", base=14150, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Mastery")
# Mail Intellect: the stock row's Strength was a dead primary.
item("rfc_cavedweller_bracers", base=14147, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Versatility")
# The stock row is Agility: the caster dagger takes Intellect, the Agility dagger moves to Bazzalan (Satyr's Kris).
item("rfc_chanting_blade", base=14151, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)", budget_mult=CASTER_MAIN_HAND_MULT)
item("rfc_searing_blade_ritual_leggings", name="Searing Blade Ritual Leggings", like=15017, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Mastery",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
# The Spirit staff: Spirit is the healer's stat on cloth (Spirit, Haste, Crit, Mastery: a three-secondary standout).
item("rfc_invokers_staff_of_embers", name="Invoker's Staff of Embers", like=890, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Crit/Haste/Mastery")
item("rfc_shard_of_the_blood_filled_orb", name="Shard of the Blood Filled Orb", like=12805, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Haste/Versatility")

# ---------------------------------------------------------------------------------------------------------------------
# Bazzalan (item level 18)

item("rfc_cleft_of_shadow_grips", name="Cleft of Shadow Grips", like=4940, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Haste",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("rfc_satyrs_kris", name="Satyr's Kris", like=15443, ilvl=LEVEL, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")
item("rfc_satyrhide_mantle", name="Satyrhide Mantle", like=14587, ilvl=LEVEL, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility")
item("rfc_felhoof_kilt", name="Felhoof Kilt", like=3305, ilvl=LEVEL, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Mastery")
item("rfc_shadowstep_slippers", name="Shadowstep Slippers", like=14364, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Haste")
item("rfc_idol_of_the_corrupted_grove", name="Idol of the Corrupted Grove", like=22397, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Haste")

# ---------------------------------------------------------------------------------------------------------------------
# Taragaman the Hungerer (item level 18)

# The stock Spell Power and Intellect lines fold into the shape budget: Spirit, Crit, Haste.
item("rfc_crystalline_cuffs", base=14148, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Haste")
item("rfc_subterranean_cape", base=14149, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Versatility")
# Keeps Cripple on hit (18381, ppm 1.2): a tank effect on the Strength / Parry sword.
item("rfc_cursed_felblade", base=14145, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry (Solo)")
item("rfc_hungerers_legplates", name="Hungerer's Legplates", like=14900, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit/Haste/Mastery",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("rfc_crested_helm_of_the_beast", name="Crested Helm of the Beast", like=9394, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Versatility")
item("rfc_libram_of_the_hungerer", name="Libram of the Hungerer", like=23203, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit/Mastery")
item("rfc_searing_blade_talisman", name="Searing Blade Talisman", like=21120, ilvl=LEVEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Haste")
