# dbc-tools (`apps/dbc-tools/`)

Generates `spell_dbc`/`Talent.dbc`/`item_dbc`/etc. content from
`apps/dbc-tools/source/{spells,talents,items.csv}` via `apps/dbc-tools/generate.py`, producing a
pending SQL migration plus a client patch MPQ. Full design and workflow:
`apps/dbc-tools/README.md`. Bugs found and fixed via live-client/live-engine verification are
logged in `docs/dbc-build-pipeline.md` — read that log before assuming a surprising-looking column
or value is intentional.

## `Item.dbc` — the newest table this pipeline touches

Added to fix a real bug (see `docs/bugs-and-fixes.md`'s "blank bag icon" entry for the full
investigation): a custom `item_template` entry above **56806** (the last real client item) needs a
matching row in `item_dbc` just for the server to load it fully, but that alone does nothing the
*client* can see — the client has its own separate local `Item.dbc`, and only a real client patch
(this pipeline's normal output) teaches it about a new entry. `source/items.csv` is a flat file (no
per-class split like `spells/`, since nothing here is class-specific); the reserved ID block is
`item` in `source/ids.yaml` (70000–79999, chosen to include the one item that pre-dated this
table's use, entry 70001). If you're touching `var/extractors/dbc/Item.dbc`: it must come from
`patch-enUS-3.MPQ` specifically (the highest-numbered, most-patched locale MPQ under
`client/MPQs/enUS/`) — earlier patches (`patch-enUS.MPQ`, `patch-enUS-2.MPQ`) also contain an
`Item.dbc` but it's shadowed/stale, smaller, and not what the client actually ends up using.

## Enchant, suffix, gem and meta gem condition tables (crafting rework C1)

`lib/dsl/enchants.py` declares rows of `SpellItemEnchantment`, `ItemRandomSuffix`, `GemProperties` and
`SpellItemEnchantmentCondition` (`enchant()` / `stat_enchant()`, `suffix()`, `gem()`, `enchant_condition()`, plus
`override_*()` for a stock row). Each goes out as both halves like SkillLine: the `*_dbc` SPELL_TABLES entry (prunes
when the last declaration goes) and a merge over the stock file into patch-Z. The module declares no content; the
crafting stages C4 (suffixes), C5 (gems, metas) and C6 (enchants) do. Facts to know before touching them:

- Id blocks (`source/ids.yaml`, proposed 2026-11-10): `spellitemenchantment` 5000-5999, `itemrandomsuffix` 1000-1999,
  `gemproperties` 2000-2499, `spellitemenchantmentcondition` 1000-1099. A suffix id must stay below 32768
  (`item_instance.randomPropertyId` is a smallint holding `-id`).
- Suffix parts are enchants with amount 0: `Player::ApplyEnchantment` takes `AllocationPct * suffix factor / 10000` when
  the enchant's amount is 0. The suffix factor only exists when `item_template.RandomSuffix` is set.
- The server finds a socketed gem's color as enchant `Src_ItemID` -> gem item -> `item_template.GemProperties` ->
  `GemProperties.Type`, so a gem's enchant row must carry `src_item=<gem entry>` or the meta gem count never sees it.
  The condition table only compares the four colors META, RED, YELLOW, BLUE (a hybrid counts once per color bit); a
  six-color or per-gem rule is a script.
- Enchant-type custom stats (Mastery 22, Versatility 23, Cooldown Haste 24, Proc Chance 33) apply only with the C0 core
  fix (`PlayerStorage.cpp` ApplyEnchantment); `ItemMod` names them.
- `SpellItemEnchantmentCondition.dbc` has byte columns (64-byte unaligned record): `dbcfile` packs `b` / `X` as one
  byte.
- `generate.py` (and `--check`) runs `lib/enchant_tables.check()` before anything is written and stops on a dangling
  reference, a gem enchant with `Src_ItemID` 0 or an item that does not point back, a suffix part with a flat amount or
  an unscalable effect, and a bad `item_enchantment_template` suffix pool (live and `item()`-declared items).
- A missing stock file only matters to a run that declares something of that table (otherwise one WARNING and the pool
  check is skipped); a needed one is an ERROR naming the file and the `docker cp` command.
- Scoped runs own these tables like ItemLimitCategory (`scope.DBC_SPACES` / `TABLE_IDS`): a scoped source file's rows and
  stock-id overrides go out in both halves. The drop guard covers every row of the four overlay tables and refuses a
  client patch that reverts a deployed stock-row override this checkout never wrote.
- Stock files: `docker cp ac-worldserver:/azerothcore/env/dist/data/dbc/<name>.dbc var/extractors/dbc/` (checked
  byte-identical to the 3.3.5a client's `patch-enUS-3.MPQ` / `patch-enUS.MPQ` members, 2026-11-10).
- Suffix pools (crafting rework C4): `suffix_pool(entry, *suffixes)` declares `item_enchantment_template` rows (equal
  chances, rounded up so they sum to at least 100) in the `item_enchantment_pool` block 9000-9099, clear of the stock
  pools 61-8675 the table also holds for RandomProperty. A SPELL_TABLES entry keyed `(entry, ench)`: the prune pass only
  removes keys a past run emitted and never a base-dump key. The pool check reads the declared pools in place of their
  live rows, and also reports an item whose `RandomSuffix` names a pool with no rows. Crafted gear sizes its suffix
  from its budget, not RandPropPoints: `item_itemization.secondary_shape_id` 0 + `RandomSuffix` set makes
  `GenerateEnchSuffixFactor` return `ItemBudget::GetSuffixFactor` (2 x round(secondary budget / 2)), so a 5000/5000 pair
  splits the secondary share. Content: `source/world/crafting_suffixes.py`.
- Gems (crafting rework C5): the table is `lib/crafting_gems_data.py`, declared by `source/world/crafting_gems.py`;
  the gem items are hand-written rows from `write_gem_items.py` (rerun it after a table edit; the tests fail while stale).
- Enchants as items (crafting rework C6): the table is `lib/crafting_enchants_data.py`, declared by
  `source/world/crafting_enchants.py` (enchant, the item's on-use spell with effect 53 or the buckle's 156, the
  recipe, its SkillLineAbility and trainer row); the items are hand-written rows from `write_enchant_items.py` in the
  hand-picked block 79000-79199, carved off the top of `item_minted` (the minter only serves `item()` gear). The use
  spell's `EquippedItemClass` / `Subclass` / `InvTypes` masks decide which slot an item fits; a tinker (type 7) and a
  stat enchant share the permanent slot, the buckle has its own prismatic slot. `stock_enchant_rows()` lets a source
  file select stock rows by content: `source/world/crafting_hed_remap.py` overrides all 215 stock rows carrying Hit,
  Expertise or Defense with the rule in `lib/crafting_hed_remap.py`.
- Material squish (C6): `source/world/crafting_squish.py` re-declares stock recipes pulled verbatim with only their
  reagents changed (`_squished()` maps an old vanilla dust / essence / shard to its survivor); minted items get their
  `DisenchantID` / `RequiredDisenchantSkill` from quality and item level (`lib/disenchant.py`, hooked in
  `lib/item_emit.py` for non-stock tiers), so a full run rewrites those two columns on every minted vanilla item.
- Recipe retirement (crafting rework C7): the retired stock recipes are data in `lib/crafting_retire_data.py` (spell,
  the trainers that taught it, its recipe items, starter SkillLineAbility rows, the quests that rewarded one).
  `source/world/crafting_retire.py` untrains them, sets the starter rows to AcquireMethod 0 and neuters the recipe
  items (`item_template()`: no teach spell, Poor quality); `write_crafting_retire.py` writes the loot / vendor /
  condition removals, the `disables` rows (spells for players, quests) and the characters-DB cleanup. A profession
  recipe disabled for players can't be learned (`custom_professions.cpp`). Tests: `lib/test_crafting_retire.py`.
- Crafted sets (crafting rework C7): `lib/crafting_sets_data.py` (seven sets x 102 items), the items in
  `source/items/crafting_sets.py` (`item(..., suffix_pool=)`: no secondary shape, `RandomSuffix` = the C4 pool, the
  suffix sized from the unspent secondary budget), the recipes in `source/world/crafting_sets.py`. A recipe names the
  minted item it creates with `item_key_refs.ref(key)` in `EffectItemType_1`; generate.py swaps the placeholder for the
  entry after the item expansion (`lib/item_key_refs.py`, the lock for a scoped run). The raid recipe items, their
  per-tier reference pools (`crafting_loot_reference` block) and the tier materials are hand-written by
  `write_crafting_set_items.py` (items 78000-78799). Tests: `lib/test_crafting_sets.py`. The trade skill window
  groups the set recipes by set on the client: `write_crafting_categories.py` writes the table
  `CraftingCategories.lua` (patch-X, hiafi/wow-client-ui) that `TradeSkillCategories.lua` reads; the header names are
  `crafting_sets_data.CATEGORY_NAME`. Tests: `lib/test_crafting_categories.py`.
- Premium enchants, flasks, raid buff scrolls, boss runes, Darkmoon tarot (C7): `lib/crafting_consumables_data.py`,
  `source/world/crafting_consumables.py`, items from `write_crafting_consumable_items.py` (78800-78999); scripts in
  `custom_crafting_enchants.cpp` and `custom_crafting_runes.cpp`. Tests: `lib/test_crafting_consumables.py`.

### Item tier labels on the tooltip (item variants, IV4)

Every tier of an `item()` ladder except a `heroic_flag=True` one gets a green line directly under the item name
("Normal", "Molten Empowered", "Heroic Hard Mode", ...). The stock flag 0x8 prints "Heroic" itself, so those tiers are
left out of the table. The tooltip body is built inside Wow.exe, so the line is a FrameXML hook (UI-unlocked exe only),
shipped in `patch-X.mpq` with the other whole-file UI overrides:

- `lib/item_labels.py` writes `client/ui-overrides/Interface/FrameXML/ItemTierLabels.lua` (`ITEM_TIER_LABELS = {
  [entry] = "label", ... }`, sorted, LF, from `ItemEmission.labels`) on a full run and on `--only items`; it rewrites
  the file only when the text changed, and `--check` prints a "stale" note instead of writing. A label with `|`, a
  quote, a backslash or a line break stops the run.
- `client/ui-overrides/Interface/FrameXML/ItemTierLabel.lua` is the hand-written hook: `OnTooltipSetItem` on
  `GameTooltip`, `ItemRefTooltip` and `ShoppingTooltip1-3`, nil-guarded and under `pcall`, no globals but the table.
  The label color is the stock `GREEN_FONT_COLOR_CODE` / `GREEN_FONT_COLOR` (FrameXML `Constants.lua`), the color of
  the exe's own "Heroic" line.
  It merges the label into the line after the name (a ShoppingTooltip's name is line 2, under "Currently Equipped");
  when that line has right-hand text or a socket icon it shifts the lines down instead. `FORCE_SHIFT` at the top of the
  file forces the shifting insert if the merge looks wrong in game.
- Tiered set tooltips: ItemSet.dbc lists at most 17 ids per set (each piece's first tier), so the client's set section
  miscounts a worn Heroic or Empowered copy while the server (counting by `item_template.itemset`) grants the bonus.
  `lib/item_set_members.py` writes `ItemSetMembers.lua` (`ITEM_SET_MEMBERS = { [set id] = { bonuses = { { pieces,
  spell }, ... }, pieces = { { every tier's entry of one piece }, ... } } }`, from `SetExpansion.members` of
  lib/item_sets.py) on a full run and on `--only items`, like the label table (`--check` prints a "stale" note and
  never writes). `ItemSetTooltip.lua` (hand-written, same hook points) recounts the worn pieces from the player's
  equipment (each piece once, any tier), rewrites the "(n/m)" header and colors the piece list and bonus lines (green
  when active). Items outside the table, other units' items (inspect) and set sections it cannot match line for line
  are left alone.
- `client/ui-overrides/Interface/FrameXML/FrameXML.toc` is the stock toc (CRLF) with the four files added before
  `## add new modules above here`. `client/ui-overrides/` is its own private repo
  (hiafi/wow-client-ui, nested and ignored by this repo; its `.gitattributes` keeps the CRLF). Commit the regenerated
  `ItemTierLabels.lua` and `ItemSetMembers.lua` there after a write run.
- `apps/dbc-tools/build_patch_x.py` packs the UI files under `client/ui-overrides/Interface` (`.lua .xml .toc .blp
  .tga`; no dotfiles, swap or `.orig` files) into `patch-X.mpq` (same packer as the other `build_patch_*.py`) and
  refuses a toc that does not list an existing label file. By default it **only builds** (to
  `var/dbc-patch/patch-X.mpq`) and prints the one-client test steps; it copies into `patch-root/Data` only with
  `--deploy` (root from `lib/local_config.py` or `--deploy-root`). Then
  `docker exec patch-manifest-gen python3 /manifest_gen.py`.

A Lua error at load breaks the UI of every player, and manifest-gen ships `patch-root/Data` on a timer, so test a new
patch-X on one client (copy the built archive into that client's `Data/` by hand) before `--deploy`.
`client/ui-overrides/README.md` lists the files and what each changes.

### Boss loot: `boss_loot()` / `remove_loot_group()` (item variants IV7)

`lib/dsl/loot.py` (declarations in `source/items/<dungeon>_loot.py`), `lib/loot_tables.py` (rows, rules, rendering),
wired in `generate._loot_blocks` after the item expansion, so a full run and `--only items` both carry the loot.

- **One list = one group.** `boss_loot(lootid, items, tier=..., group=1)` owns that (Entry, GroupId) of
  `creature_loot_template`: every row Chance 0, MinCount = MaxCount = 1, so the group always yields one item
  (`LootGroup::Roll`). `DELETE ... WHERE Entry = X AND GroupId = N` + INSERT, only when the declared rows differ from
  the replayed group; a rerun after import is silent. Other groups of the Entry (cloth, food, quest items, a generic
  reference) are never touched; the run stops if a declared group's live rows hold anything that is not a declared
  item (a generic pool rolls in its own group, never instead).
- **`picks=N, reference=R`** (Sneed's two distinct items): one reference row (MaxCount N) in the group, the list in
  `reference_loot_template` R group 1 (ids.yaml `loot_reference`, 1700000-1700999). The group roll's duplicate skip
  makes the N items distinct, but only for equippable items (checked).
- **Tiers by difficulty.** A heroic creature's lootid (any entry in `source/world/heroic_ids.lock`) drops the ladder's
  first explicit-level tier (Heroic, Heroic Hard Mode), any other lootid the own-level tier (Normal). The heroic row's
  `lootid` must be its own entry: set it in the dungeon file's heroic `overrides` columns (an ERROR on a full run, a
  WARNING under `--only items`, which renders no creature row).
- **Hard mode** (`loot_mode=2`, `LOOT_MODE_HARD_MODE_1`): a group next to a default list on the same Entry; it rolls
  only when the boss script added the bit with `AddLootMode` before the kill (`Unit::Kill` fills the loot with
  `GetLootMode()` before `JustDied`). Deadmines: `instance_deadmines_rework.cpp` `ApplyHardModeLoot()` follows
  `DATA_HARD_MODE`.
- **Heroic copies.** A heroic lootid with a declared list also gets every other group of its normal boss's lootid
  (cloth, food, quest items, a world loot reference) copied unchanged into the same GroupId
  (`loot_tables.derive_heroic_copies`, derived from the replayed normal rows each run, so a rerun is silent). A copy
  on a GroupId a heroic declaration owns is an ERROR; a stale heroic group is a WARNING, never pruned.
- `remove_loot_group(lootid, group=, why=)` deletes a stock group whose items all moved to another list.
- `remove_loot_rows(lootid, items=(), group=0, references=(), why=)` deletes single rows of a group, not the whole
  group: plain item rows by `item_template` entry (`items=`) and grouped or ungrouped reference rows by their
  `reference_loot_template` Entry (`references=`). Other rows of the group stay. Use it for a stock Tier 0 drop, a cut
  piece, or a stock pool in a boss's ungrouped rows; a pool that no row references afterwards goes with
  `remove_reference_pool()`.
- `loot_chance(lootid, item, chance, group, loot_mode=, reference=)` declares one explicit-chance row, for a drop that
  is not a list item (a rare mount, a novelty item). The rows of one group are rolled in turn on a single roll, so the
  group yields **at most one drop**, and a row whose `loot_mode` bit is not set on the kill is skipped. Three rules:
  - A hard mode extra chance of an item must **share the base row's group** (same Entry, same GroupId). A group of its
    own rolls independently, so the item can drop twice on one kill. Same group: one roll, one drop.
  - A second row of the same item in that group needs `reference=R`: the table's key is (Entry, Item, Reference,
    GroupId), so a plain duplicate would collide. The second row is a grouped reference row into a one-item pool R
    (MinCount = MaxCount = 1, the pool row at Chance 100 with the same loot mode).
  - Pattern for "1% normal, 2% heroic, 10% hard mode, never two" (Deathcharger's Reins): normal lootid group G holds
    the item at 1%; the heroic lootid group G holds the item at 2% (LootMode 1) plus a grouped reference row at 8%
    (LootMode 2). A hard mode kill has both loot-mode bits, so both rows survive the filter and one roll takes
    2% + 8% = 10%; a plain heroic kill keeps only the 2% row.
- Replay note: the replayed loot rows omit columns an INSERT left out; `loot_tables.load_live` fills the schema
  defaults so a declared row compares equal to the live one.

### Item variants: ids, defaults and the deployed Item.dbc guard

- **Tier steps.** Every `tier()` takes an explicit `step=` (`item_budget_variant.tier`): 0 Normal, 1 Heroic, 2.. the
  empowered tiers, the same number for the same step on every ladder (a hard mode ladder starts at 1). Steps strictly
  increase along a ladder; a ladder's base tier has no variant row.
- **Weapon-tier defaults.** On a weapon, shield or held-in-off-hand slot, `budget_mult` and the DPS adjustment default
  per tier to the median of live itemized items of the same role, InventoryType, Quality and item level bucket (1-59,
  60-100, 101-200, 201-300: the stock conversion's per-(role, slot) correction), widening to any quality, then any
  level, below 3 samples; else 1.0 and 0. Role from the shapes (Dodge/Parry/Block/Defense secondary = tank,
  Int/Spirit/SP lead = caster, else physical) or `weapon_role=`. Declared `budget_mult=` / `extra_dps=` win. The sample
  leaves out the custom item blocks and every entry an item owns, so the generator's own rows never feed back.
  Each cell is frozen the first time a declaration asks for it: `source/items/item_role_cells.lock` (append-only,
  commit it with the SQL) records the cell's `budget_mult` and DPS fraction (or `none`, the plain default), and later
  runs read the line instead of the live median. So declaring a new `base=` weapon (which leaves the sample) never
  retunes an earlier item of the same cell; retune one item through its declaration, never by editing a line.
- **Durability.** A minted tier's `MaxDurability` is the median of live items with the same class, subclass, slot and
  quality within 5 item levels (widening to 10, 20, any), else the donor's (`base=` / `like=`). Prices and
  disenchanting are not derived yet.
- **Retired tiers keep their label.** A retired lock line may end with the tier's label (`... <sheath> Molten
  Empowered`); the label table keeps it so owned copies keep their line. The retire suggestion fills it in from the
  current `ItemTierLabels.lua`.
- **Lock merge conflicts.** Two branches that minted from the same high-water mark give the same ids to different
  (key, tier)s, so keeping both sides' lines is refused (`entry N is already on line M`), and each side's rev SQL
  already carries those ids. Keep the merged (or deployed) side's lines, drop the other side's minted lines, delete
  its not-yet-imported `rev_*.sql` that carries them, then re-run generate on the merged tree to re-mint. If both sides
  were imported, stop: a human retires one set. One item branch at a time.
- **Deployed Item.dbc guard** (`--allow-item-drop`). Before writing anything, a full run and `--only items` read the
  deployed `patch-Z.mpq`'s `Item.dbc` and stop when it holds ids in the custom item block (70000-79999) that this run's
  build lacks: shipping it would blank-icon those items on every client and the `item_dbc` block would drop their
  server rows. This is the cross-checkout trap: once minted items are deployed, a full run from a checkout without
  `source/items/` would remove them. Merge the item branch into every dbc-tools checkout first; `--allow-item-drop`
  writes anyway; `--check` only warns. `--only items` also WARNs when another member of the deployed archive differs
  from this checkout's last full build (`var/dbc-patch/DBFilesClient/`), i.e. a stale or foreign base.

### Item effect spells that scale with the tier: `scale="budget"` (item variants IV10)

`use_spell(spell, scale="budget")` (also `equip_spell` / `hit_spell`; pass the declared `spell(...)` object) gives
every tier but the ladder's effect reference tier its own copy of the spell and of every source/items spell it reaches
(an effect's `trigger_spell`, a `$<id>` token or a `pot_text()` in its texts, a `linked_spell()` it triggers).
`lib/item_spell_copies.py`:

- **Reference tier**: `ladder(..., effect_reference="<tier>")` (default: the first tier). It keeps the declared spells,
  so the declared numbers are that tier's. `vanilla_dungeon` uses `heroic` (66 Epic): the Normal tier, at each item's
  own stock level, gets a copy with a ratio below 1, the empowered tiers ratios above 1. `vanilla_hard_mode` uses
  `heroic_hm` (71). Declare an effect's numbers for the reference tier.
- **Ratio** = `item_budget_curve[ilvl].budget x item_quality_mult x item_slot_mult` of the tier over the reference
  tier's, rounded to 4 decimals (`budget_mult`, set discount and socket cost left out: constant or not an effect's
  business). The hard mode ladder 71 / 81 / 91 / 101 Epic: 1.0 / 1.0545 / 1.1091 / 1.2545 (curve 55 / 58 / 61 / 69).
- **Copy** = the declaration with `sp_potency` / `ap_potency` / `base_potency` / the combo-point potencies times the
  ratio, and the amount (BasePoints + 1) of every stat-like aura without potency times the ratio, rounded
  (`STAT_AURAS`: MOD_DAMAGE_DONE 13, MOD_RESISTANCE 22 (armor), MOD_STAT 29, MOD_INCREASE_HEALTH 34, SCHOOL_ABSORB 69
  and MANA_SHIELD 97 without potency, MOD_BASE_RESISTANCE 83, MOD_POWER_REGEN 85, MOD_ATTACK_POWER 99,
  MOD_RESISTANCE_EXCLUSIVE 101, MOD_RANGED_ATTACK_POWER 124, MOD_HEALING_DONE 135, MOD_SHIELD_BLOCKVALUE 158,
  MOD_RATING 189); every family id inside it remapped to the same tier's copy (trigger spells, `$<id>` tokens,
  `pot_text` expressions, linked spells); its `spell_proc`, `spell_script_names`, `spell_custom_attr` rows copied;
  potency rows from its own `to_entry()`. Everything else (durations, cooldowns, radius, proc chance, percentages such
  as damage taken %, speed %, an effect with `potency_excluded`) is unchanged. A family damage or heal effect without
  potency, a `weapon_potency` effect or a hand `bonus_coefficients()` row is an ERROR. The tier's item row names its
  copies (`ResolvedTier.spells`); the reference tier keeps the declared ids. Show aura amounts with `$s1` in the
  texts (a typed number would not follow the copy).
- **Families and equal potency**: two spells with the same potency print the same `pot_text()` expression. The
  registry records which spell each `pot_text()` call was for and `spell()` keeps the ones its texts contain
  (`_pot_text_refs`), so a family follows exactly the named spell; only a text built outside the registry falls back to
  matching expressions (and then pulls in every spell with that expression). Build a description's `pot_text()` in
  the `spell(...)` call (or just before it), not in a shared string reused by several spells.
- **Ids**: `source/items/item_spell_ids.lock` (`<spell id> <key> <tier> <base spell id> [retired <date>]`), minted
  from the `item_spell_copy` block (205410-205599, inside the `items` spell reservation), same append-only, retire
  and merge rules as `item_ids.lock`; a full run writes it, `--check` lists the lines.
- **C++**: the copies run the same scripts, so a script casting another family spell must cast its tier's copy. A full
  run writes `modules/mod-dungeon-bosses/src/Generated/ItemSpellCopies.h` (pure; `ItemSpellCopies::Resolve(cast or
  aura id, base id)`); `--check` errors on a stale one.
- **`--only items`** cannot ship spell rows: it stops (`--check` warns) while a copy is neither live nor in a pending
  rev, its lock line is unwritten or the header is stale. Run a full generate for a new or retuned copy.

### Unique-equipped across tiers: `ItemLimitCategory` (item variants IV10 follow-up 1)

Every tier of an item with an effect (`spells=` with a spell, scaled or not, or `keep_spells=True` on a stock row that
has one) shares one `ItemLimitCategory` with an equip limit of 1 (`lib/item_limits.py`); plain stat items stay
unrestricted. `item(..., unique_equip=False)` turns it off, `True` forces it; `ItemLimitCategory` is not a column you
pass. One row per item: `itemlimitcategory_dbc` (a SPELL_TABLES entry, prune when empty) for the server, which zeroes
an item's unknown category at boot, plus `ItemLimitCategory.dbc` in patch-Z for the client's "Unique-Equipped: <name>
(1)" line (Name = the item's name, Quantity 1, Flags 1 = equip mode). Ids: `source/items/item_limit_ids.lock`
(`<id> <item key> [retired <date> [<name>]]`) from the `item_limit_category` block (1000-1999; stock ends at 85), a lock
because an entry-based derivation fails for `base=` items and a key hash can collide; a retired line keeps emitting its
row. The base file `var/extractors/dbc/ItemLimitCategory.dbc` is not in the client extract: copy it from
`ac-worldserver:/azerothcore/env/dist/data/dbc/` (a full run stops without it). `--only items` refuses while a
category row is not live.

### Dungeon sets: `item_set()` / `set_token()` / `set_vendor()` (Haunted set track)

`lib/dsl/sets.py` (declarations in `source/items/haunted_set.py`), `lib/item_sets.py` (rows, checks, rendering), wired
in `generate._item_set_expansion` right after `item_emit.build` (so the tokens join the minted rows, the label table
and the Item.dbc merge before they are used) and in the full run's SQL and patch-Z blocks.

- **Item sets** (`ItemSet.dbc`, server overlay `itemset_dbc`). `item_set(set_id, items=(item keys), bonuses=((3,
  spell), (5, spell)), name=)`: a stock id (181-189) keeps its stock name and item list and loses its stock bonuses; a
  new id comes from ids.yaml `item_set` and needs `name=`. The server counts worn pieces by `item_template.itemset`
  (`AddItemsSetItem`), so every tier of a piece must carry the set's id (checked on the built rows): a `base=` piece
  keeps the stock row's, a new one passes `itemset=`. Every tier also pays the budget's set discount (0.9). The row's
  item list is each piece's first tier; whether the client marks a worn Heroic or Empowered piece in the tooltip list
  is a playtest check (the bonus lines follow the server count).
- **Tokens.** `set_token(key, name=, slots=(InventoryTypes), ladder=, like=<stock class 15 token>, entries={tier:
  entry}, costs={tier: ItemExtendedCost id}, ilvl=/quality=/required_level= for the first tier)`: one `item_template`
  row per non-deferred ladder tier, copied whole from `like=`, the tier's level and quality, the Heroic flag on a
  `heroic_flag` tier and the tier label on the others; one `ItemExtendedCost` row per tier (one token). Explicit ids
  (`item_set_token` 70500-70599 inside the `item` block, `item_extended_cost` 3000-3199); a shipped id never moves.
- **Vendors.** `set_vendor(entry, sets=, tokens=, tiers=)`: `npc_vendor` rows for the given ladder tiers (all when
  None) of every piece of the sets, priced by the token of the piece's slot at the same tier, ordered tier, token
  order, set (Haunted: 16 vendors, four per armor type: Normal & Heroic, then one per empowered tier). A list sends
  at most 150 items
  (`MAX_VENDOR_ITEMS`, a warning) and keeps at most 255 rows (`VendorItemData::GetItemCount` is a uint8, an error).
  The vendor creature is a `creature_template()` declaration with npcflag 128; its spawn is hand SQL.
- **Tables.** `itemset_dbc`, `itemextendedcost_dbc` and `npc_vendor` are declared tables with their own index
  (`item_sets.SET_TABLES`, `load_index`, `render_blocks`): DELETE + INSERT of the rows that differ from live, a prune of
  rows an earlier run emitted that nothing declares (circuit breaker on), silent on a rerun. `--check` prints how many
  differ from live; `--only items` ships the token rows and warns while a set, cost or vendor row is not live.
- **Client files.** A full run merges the rows into `ItemSet.dbc` and `ItemExtendedCost.dbc` in patch-Z; their stock
  files are not in the client extract: copy them from the worldserver (`docker cp
  ac-worldserver:/azerothcore/env/dist/data/dbc/ItemSet.dbc var/extractors/dbc/`, the same for ItemExtendedCost.dbc).
  A full write run stops without them; `--check` warns.
- **Not wired yet:** `boss_loot()` resolves `item()` keys only, so a token cannot be put on a boss list until the loot
  resolver also accepts `set_token()` keys (the dungeons' loot stage).

## Watch out: a full write run is global; dungeon and class work writes with `--scope`

A plain `generate.py` write run regenerates the pending SQL for *every* table at once and rewrites whole reserved
blocks (`DELETE FROM spell_dbc WHERE ID BETWEEN 200101 AND 209999` plus a full re-insert), and its patch-Z is built
from every source row. Anything the checkout lacks is wiped: on 2026-11-07 the wave 1 items branch's revs, written
before #96 went live, would have deleted #96's spells 205282 / 205304 / 205348 from the DB and the client. Anything
the checkout has in flight (another class's unpromoted edits) is swept into the same file.

**Rule.** Dungeon and class work writes with `generate.py --scope <name>` (below). A full run is for shared changes
only (source/spells/*.csv, world files, the ids/ladder plumbing, a pool like `items`), and is done last, right before
the merge or deploy, on a tree rebased onto the latest base (memory `feedback_write-run-before-merge`). Every write
run, full or scoped, runs the drop guard first (below).

`--check --class NAME` is a read-only scope flag; see "generate.py speed" below. `--only items` (below) is the older
table-kind scope: every item table, all owners; `--scope items` is the same run.

### Scoped write runs: `generate.py --scope <name>[,<name>...]`

Plan: `.agents/plans/dbc-tools-scoped-generate/`. Code: `lib/scope.py` (ownership, the SQL narrowing, the client
repack), `source/scopes.yaml` (the scopes), `generate.py` (`_scope_ownership`, `_scope_sql`,
`_install_scoped_patch`). Tests: `lib/test_scope.py`, `lib/test_generate_scope_flag.py`.

```
python3 apps/dbc-tools/generate.py --scope shadowfang_keep
python3 apps/dbc-tools/generate.py --scope deadmines,haunted_set
python3 apps/dbc-tools/generate.py --scope warrior --deployed-patch /path/to/patch-Z.mpq   # test base, no deploy
```

- **What it does.** Everything is loaded, built and linted exactly as in a full run (same derived rows, same errors),
  then the output is narrowed to the rows the scope owns. Reserved DBC blocks (spell, talent, talent tab, skill line
  ability, item) DELETE only the scope's reservation ranges, split around every id another scope declared; the
  scope's rows outside those ranges (a stock spell it edits, a hard mode effect in the `items` pool, a per-tier copy)
  go out as `DELETE ... IN` + INSERT. Every other statement (keyed tables, prune and removal passes, creature, item,
  loot, set and dungeon blocks) keeps only its owned rows: an INSERT loses the others' tuples, a DELETE / UPDATE its
  others' list items. The header names the scope. A rerun after the rev is written is silent.
- **Scopes** (`source/scopes.yaml`). By convention scope N owns the reservation N and the sources `classes/N`,
  `npcs/N`, `npcs/N_*.py`, `world/N`, `world/dungeons/N.py`, `items/N.py`, `items/N_*.py`; the file lists extra
  reservations (`shadowfang_keep` also owns `shadowfang_items`) and sources (`bossmechanics` is
  `npcs/boss_mechanics.py`). `pools:` names reservations nobody owns (`items`: the effect spell copies belong to the
  dungeon whose item minted them). `lib/test_scope.py` fails when a reservation has no scope or pool, or a source
  file matches two scopes. A new dungeon's WP-0 adds its reservation (and a scope line if the names differ).
- **Ownership.** A scoped run records which file's top-level code declared each DSL entry (`registry.declared_in`,
  kept beside the entries, never in them; a helper in `items/ladders.py` or `_common.py` counts for its caller). An id
  is owned by the scope whose file declared it or whose declaration it derives from (an item's tier entries, effect
  spell copies and limit category; a set's tokens and costs; a vendor; a loot group and its reference; a dungeon's
  creatures, their heroic copies and its encounters, map difficulty and access row, and every creature and gameobject
  spawn on its map; a class's GCD-haste aura via its family), else by
  the scope whose reservation range holds it, else by nobody (only a full run writes it). A keyed row
  (`spell_script_names`, a loot group, `trainer_spell`) is owned by the scope that declared that exact key, else by
  the owner of its id column (`spell_proc.SpellId`, `creature_template_model.CreatureID`, ...;
  `scope.TABLE_IDS`). Spawn rows (`creature`, `gameobject`) go by guid, so a heroic spawnMask UPDATE
  (`id IN (...) AND guid IN (...)`) is split by its guid list. `smart_scripts` goes by `(entryorguid, source_type)`:
  the scripts of a dungeon's creatures and gameobjects and of the spawn guids on its map (negative `entryorguid`)
  are the dungeon's; otherwise source_type 0 is the creature's (or creature spawn's) owner, 1 the gameobject's.
- **Client.** The deployed patch-Z (`DEPLOY_ROOT/Data/patch-Z.mpq`, or `--deployed-patch`) is the base, as for
  `--only items`: in each DBC the full run would ship, the scope's ids take the full build's row (or go when the
  build has none) and every other row stays as deployed; members it does not touch stay byte for byte. The shared
  secondary rows (cast time, duration, range, radius) a scope spell names are added when the base lacks them; in
  the SQL they go out as a plain INSERT (no DELETE), so if two branches minted the same id, the second import fails
  loudly instead of silently overwriting the first branch's row.
  Refused up front with no deployed archive. `--deployed-patch` never deploys.
- **What stops it** (exit 1, no SQL or patch written): a statement shape the narrowing cannot read or split (an
  AND-group with several lists none of which is the owner column); an id owned by the run's scope and another one; a
  scope spell that triggers (`EffectTriggerSpell_N`) or summons (`SPELL_EFFECT_SUMMON` MiscValue), or a scope
  `spell_linked_spell` / `creature_template_spell` row that names, a spell or creature of another owner that the run
  would write as new or changed (ship that owner first: a shared spell must be in its own scope or a full run); a
  shared secondary row whose id holds a different row live or in the base archive (another checkout minted it); a
  new lock line (`heroic_ids.lock`, `item_ids.lock`, `item_spell_ids.lock`, `item_limit_ids.lock`) of another owner;
  a change to `ItemSpellCopies.h`, `ItemTierLabels.lua` or `ItemSetMembers.lua` outside the scope's entries (one
  file for every scope: when every changed entry is the scope's, the whole new file is written). A missing Lua table
  (no `client/` in a worktree) is left alone with a note. Generated class headers are written for the scope's
  classes only; `item_role_cells.lock` (shared, append-only, frozen from live medians) is written as in a full run.
  `--scope` is refused with `--check`, `--class` and `--only`.
- **What it leaves out** is printed: `note: scope: left out N changed row(s) of other owners (warrior: 4) in
  spell_dbc, spell_script_names; ...`. Those rows wait for their own scope or a full run.
- **Limits.** A row whose id nobody owns (CSV spells, world files, superseded-rank SkillLineAbility overrides,
  CreatureSpellData) is never written by a scoped run. A declaration removed from a scope with no reservation (a
  stock spell edit, a class without a slice) is no longer owned, so its old row stays live until a full run. The
  prune comment above a narrowed statement still counts the full run's rows (a note line says so). The reference
  check covers trigger, summon, linked-spell and creature-spell references, not Talent / SkillLineAbility spell
  columns, ItemSet bonus spells or `item_template.spellid_N`: an item effect spell must be live (or in the same
  scope) before the item rows that name it ship. The potency sheets and the scope's generated class headers are
  written before the checks (they only mirror this checkout's source).

### The drop guard (every write run): `--allow-drop`

Code: `lib/drop_guard.py`; tests `lib/test_drop_guard.py`. After the SQL and the client files are built and before
any SQL or patch is written, every write run (full, `--scope`, `--only items` / `--scope items`) checks:

- **Live DB: drops.** The rendered SQL is read back (the same statement reader): for `spell_dbc`, `talent_dbc`,
  `talenttab_dbc`, `skilllineability_dbc`, `item_dbc`, `spellitemenchantment_dbc`, `itemrandomsuffix_dbc`,
  `gemproperties_dbc`, `spellitemenchantmentcondition_dbc`, `item_template`, `itemset_dbc`, `itemextendedcost_dbc`,
  `creature_template` and `creature_template_model`, a live id in the custom blocks that a DELETE covers (range,
  list or key tuple) and no INSERT puts back is a drop.
- **Live DB: rewrites.** A live custom row the SQL re-inserts with other content (an older copy of a row another
  branch changed, a creature upsert that blanks a ScriptName) is refused when no INSERT of this checkout ever wrote
  the live content of that row and no UPDATE of it names the id: the run would revert another branch's change.
- **Deployed patch-Z.** In every DBC of the deployed archive the guard knows (Spell, Talent, TalentTab,
  SkillLineAbility, ItemSet, ItemExtendedCost, MapDifficulty, DungeonEncounter, ItemLimitCategory, SpellRuneCost,
  SpellCategory, SkillLine, SpellItemEnchantment, ItemRandomSuffix, GemProperties, SpellItemEnchantmentCondition,
  SpellDescriptionVariables, the four secondary DBCs; Item.dbc in repack runs), a custom id
  the deployed file holds and this run's archive lacks is a drop. A full run replaces the archive, so a DBC it does not
  build loses every row, and a deployed DBC member the guard has no definition for is reported by name; a repack
  (`--scope`, `--only items`) leaves the members it does not replace alone. A full run leaves Item.dbc to the
  stricter `--allow-item-drop` guard.
- **Only foreign changes stop the run.** A dropped id that some SQL file of this checkout INSERTed (a row's first
  value right after `VALUES` or `),`: base dump, merged and pending updates, custom and module SQL) is this
  checkout's own removal and only gets a note. Anything else is `ERROR: drop guard: ...`, no SQL or patch written.
  The fix is to merge or rebase onto the branch that shipped the rows and regenerate; `--allow-drop` writes anyway.
  A client-only table (SpellDescriptionVariables) has no SQL history, so any removal of a deployed row needs
  `--allow-drop`. `--check` renders no SQL, so the guard does not run there.
- **Inputs, read-only.** Live ids and rows come from SELECTs through `$DBC_TOOLS_MYSQL` (as for `replay_diff.py`),
  else `LIVE_DB_MYSQL` in this checkout's `lib/local_config.py` (see `local_config.py.example`), else, in a git
  worktree (no `local_config.py`), the main checkout's (`git rev-parse --git-common-dir`). The deployed archive is
  `--deployed-patch`, else `$DBC_TOOLS_DEPLOYED_PATCH`, else this checkout's `DEPLOY_ROOT/Data/patch-Z.mpq`, else the
  main checkout's. The main checkout's settings are read by the guard only and never make a run deploy;
  `--deployed-patch` / `$DBC_TOOLS_DEPLOYED_PATCH` also never deploy, and they are the repack base of `--scope` and
  `--only items` in a worktree. A half with no input is skipped with a note; when both are skipped the run prints a
  `WARNING`. A configured DB command that fails stops the run.
- **What it does not see.** The guard judges the run being made against what is live and deployed *now*. A rev
  written before another branch's rows went live (the first of the two 2026-11-07 wave 1 revs) passes every
  write-time check and does the damage at db-import; so does any rev written by a checkout that could not see the
  live DB. That is `check_pending.py`'s job (below). The 2026-11-07 revs were caught by a human review, not by this
  guard, which did not exist yet; the second of them (written after #96 went live) is the kind it now refuses.

### Before db-import: `check_pending.py`

```
python3 apps/dbc-tools/check_pending.py [--pending-dir DIR] [--allow-drop]
```

Read-only (SELECTs through the same DB command). It takes the second-pass files (pending revs, custom and module SQL)
the live `updates` table has not applied yet and reads back what they would do, together, in apply order, to the
guarded custom rows: a live row deleted and not re-inserted, or re-inserted with other content. Each is refused when
no SQL file of this checkout wrote that row (or its live content, or an UPDATE of it), or when the file that wrote
the live row is a second-pass file named *after* the rev: the rev predates the row, so it comes from a stale branch
(the 2026-11-07 case: the wave 1 rev `rev_1794030639...` would have deleted #96's spells, written by the later-named
`rev_1794036373...`). Everything else is this checkout's own change (a note). Exit 0 ok, 1 refused (do not import:
regenerate the rev on a tree with the other branch merged), 2 no DB command or a DB error. Run it right before every
`ac-db-import` (the dbc-deploy skill). Limit: a rev written by a stale checkout *after* the other branch's row went
live, deleting it, has the later name and reads as a deliberate removal; the write-time guard refuses that run when
it can see the live DB.

### `generate.py --only items` (item variants IV3)

For an item-only change while other classes' spell, talent or creature edits sit unpromoted in the tree. Everything
is still loaded (the item DSL needs the live state), but the run hands over to `generate._run_only_items` right after
the item expansion, so nothing else is rendered:

- **SQL** (one `rev_*.sql`): the `item_template` edits of stock entries and every `item_template()` declaration, the
  minted `item_template` rows, `item_itemization`, `item_budget_variant` and the `item_dbc` reserved block; plus the new
  `item_ids.lock` lines and the tier label Lua (IV4). No spell, talent, creature, dungeon, trainer or prune blocks, no
  generated headers, no potency sheets. A rerun after db-import prints `SQL: nothing to emit`.
- **Client**: patch-Z is one archive for every DBC, so building it from source would ship the in-flight spell rows
  without their SQL. `--only items` instead repacks the **deployed** `DEPLOY_ROOT/Data/patch-Z.mpq`
  (`lib/patch_repack.py`, `smpq`): every member stays byte for byte, only `DBFilesClient\Item.dbc` is replaced by
  the same file a full run builds (stock rows plus every `items.csv` and minted row). It prints the base archive's
  path, date and file list, and verifies the new archive (same members, every other file identical) before it writes
  anything. Output: the local `var/dbc-patch/patch-Z.mpq`, the loose `Item.dbc` copy (and `env/dist/data/dbc/`), and
  the deployed archive (replaced atomically). When the deployed `Item.dbc` already equals the build, nothing is
  repacked.
- **Refused up front** (before any loading), exit 1: no `lib/local_config.py` (no `DEPLOY_ROOT`), no
  `Data/patch-Z.mpq` under it, or no `smpq`. There is deliberately no fallback to `var/dbc-patch/`.
- **`--check --only items`** runs the item checks and lints only (about 13 s), not the spell lints or the header gate;
  a missing deployed patch-Z is a WARNING there ("a write run would refuse"). It cannot be combined with `--class`.
- The deployed archive keeps whatever its other files held: a spell change still needs a normal full run to reach the
  client. Run a full generate when the in-flight work is ready to ship.

## generate.py speed: the SQL corpus, the disk cache, `--check --class`, the equivalence harness

Plan and review notes: `.agents/plans/dbc-tools-generate-speed/` (local).

- **Where the time went.** Not the DSL (1.4 s): replaying ~1,300 SQL files (`db_world` 229 MB, pending 56 MB, the base
  dumps) in pure Python, once per table per loader. The fixes keep every loader's answer and printed warnings exactly
  (measured on a host at load ~20: full run ~450-680 s -> ~165 s cold and ~37 s warm; `--check` ~220-330 s -> ~19 s; `--check --class X` ~9 s).
- **`lib/sqlcorpus.py`** owns the files for a run. `generate.py` activates it; with no corpus active (tests, the other
  tools) `read_text`/`mentions`/`checkpointed` are plain reads and plain replays. It gives each file once: its text
  (`SqlText`, a `str`), its statement-head index (`INSERT`/`DELETE`/`UPDATE .. SET`/`SET @v`, scanned once and shared
  by every table's replay through `sql_dump._next_statement`/`_next_match`; a search that starts inside a head-looking
  string of a skipped statement goes back to the regex), and whether it mentions a table.
- **`sql_dump` fast paths**, each with its reference kept: a plain-literal tuple is read by a regex and `_TokenValues`
  (`_read_tuples(fast=False)` is the character parser it is tested against); `_KeyIndex` finds the rows a
  composite-key `UPDATE ... WHERE` can touch by key instead of testing all 30k `creature_template` rows per statement
  (an assignment to a key column, a `DELETE` or an unpinned `WHERE` falls back to the scan); `_fill_defaults` no
  longer probes 234 columns per row. `lib/test_sql_dump_fast.py` runs every pair on random and edge inputs.
  `lib/dbcfile.py` reads and packs with one `struct.Struct` per table (`lib/test_dbcfile_fast.py` keeps the old code).
- **The disk cache** (`Corpus.checkpointed`): a loader's replay of the base dump plus the promoted `db_world` files is
  pickled to `var/dbc-tools-cache/<code version>/snap-*.bin` with the ordered `(path, content hash)` list it was built
  from, the loader code version and the parameters. It is used only when that list is a prefix of today's: files
  appended since extend it, anything else (edited, removed, inserted-before-the-end file, new code, a truncated or
  garbled snapshot) rebuilds from scratch. `pending_db_world` and module SQL change every run and are replayed on top
  each time; whatever a replay printed (stdout, stderr) is stored and printed again. Files are compared by content
  hash (sha256), not mtime. Code version = `generate.CACHE_CODE_FILES` plus `item_lib/*.py`: edit a loader or parser
  and the next run is cold (the previous version's directory is kept, older ones are deleted). `--rebuild-cache`
  ignores the cache and rewrites it, `--no-cache` skips the disk (the in-process memo stays). Tests:
  `lib/test_sqlcorpus_cache.py`.
- **A new cached loader** = a `step(state, path)` function plus `sqlcorpus.checkpointed(kind, params, stable, init,
  step)`, then replay the volatile (pending, module) files on the returned state yourself. `params` must name
  everything the replay depends on besides the files (columns, key columns, flags). A projection
  (`load_table_rows(project=...)`) keeps a 150k-row dump out of the snapshot. `load_live_item_template_rows` calls
  item-tools' overlay, which replays with this `sql_dump` through `sqlcorpus.checkpointed` (`item_lib/replay.py`):
  change `item_lib/` and re-run the harness.
- **`--check --class NAME`** (`generate._run_scoped_check`) loads `source/classes/NAME` only and runs the same lint
  block (`_check_report`) over it, with the live state the DSL helpers need behind `lib/lazy.py`. It leaves out what
  is not one class's: the CSV/YAML sources (except their ids, so a CSV-declared stock spell is not called undeclared),
  `source/npcs`, `source/world`, cross-class duplicate ids, the shared holding-tab check, the potency sheets, and the
  GCD-haste messages that do not start with the class's family name (the `EXCLUDE[..]`/policy ones are
  `source/gcd_haste.py`'s, not the class's). `--class` with anything but `--check`, a missing, unknown or repeated
  name, all exit 2 before loading (`lib/test_generate_class_flag.py`). When you add a lint to `_check_report` that
  scans stock rows the class did not declare, scope it (see `undeclared_scan_class_set`) or the scoped run will report
  other classes' stock spells.
- **Equivalence harness** `apps/dbc-tools/bench/equivalence.py` (read its docstring): runs `generate.py` from two code
  refs in throwaway sandboxes (copy of the code, symlinked frozen inputs, copied pending dir, hardlinked `db_world`,
  no `local_config.py`, so nothing is deployed and nothing is written outside `var/dbc-tools-equiv/`) and diffs the
  pending SQL, headers, potency sheets, every loose `.dbc`, the files inside the MPQ (smpq stamps times, so archive
  bytes always differ) and stdout. Scenarios: `check`, `full`, `full2`, `mutate-full` (edits a pending file),
  `promote-full` (adds the newest rev to `db_world`), `check-injected` + `check-class-X` (`scoped` subcommand). Run it
  before and after any change to a loader.

## Watch out: never delete an earlier generated `pending_db_world/rev_*.sql`

`generate.py` emits **delta** rows for `trainer_spell`, `spell_script_names`, `spell_bonus_data`
and `spell_proc`: `lib/trainer_state.py` scans `base/` + `updates/db_world/` + **`pending_db_world/`**
and anything already present there is "live" and skipped (`lib/spell_tables.py`'s
`rows_to_emit`). Since dbc-replay-fix the DBC tables' reserved blocks are skipped too when a pending
file already holds their content (the run prints `note:   <Table>: not re-emitted because its content
is in pending file(s) ...; they must ship` and names them). So generated pending files are meant to
**accumulate**: each new one carries only what the previous files don't already have.

Deleting an earlier generated file *after* running `generate.py` silently drops every
row it alone carried — the new file skipped them as live, and now nothing has them.
Git will often show this as a rename (`R old.sql -> new.sql`) because the DBC blocks are near-
identical, which hides that the small itemised blocks vanished. This shipped once (Priest Holy pass
deleting the Disc pass's file: 10 Disc spells lost their script bindings, procs and trainer rows —
`docs/bugs-and-fixes.md`). If you genuinely want one consolidated file, delete the old one
**before** running `generate.py`, never after; and treat an `R` on a `rev_*.sql` in `git status` as
a red flag to diff the `spell_script_names`/`spell_proc` blocks.

## SQL lint: generated output

`python3 apps/codestyle/codestyle-sql.py` lints every `pending_db_*/*.sql`, so generated files must
pass it. Cause of the old failures (hundreds per file, e.g. 145 backtick hits in each, 759 in the
Item.dbc one): spell `Description`/`AuraDescription` strings with embedded line breaks were written as
literal multi-line strings. The linter works line by line, so every continuation line was read as
SQL ("Missing backticks around (cloth)"), a tooltip line ending in a space tripped the trailing-
whitespace check, and a row whose string continued on the next line was judged the final row
("Missing semicolon"). The linter is right to be line-based; the fix is in the generator.
`sql_out._sql_literal` now writes `\n`/`\r` inside a string as the escape (MySQL decodes it to the
same bytes), so a row is one physical line. `sql_dump._read_value` decodes MySQL escapes, so it reads
both the new files and the older literal-multi-line ones. Rule for any new emitter: never put a raw
line break inside a quoted SQL literal. Already-committed `rev_*.sql` files keep the old form and
still fail the linter (never delete them, see above); only a file generated after this change is clean.

## Trainer pricing

A trainer spell's price is a function of its learn level (`ReqLevel`) alone. `source/trainer_pricing.py`
holds three things and `lib/trainer_pricing.py` applies them on every `generate.py` run:

- **`PRICE_CURVE`**: `(ReqLevel, copper)` anchors (10c at levels 1-3, 20c at 4, 1s at 10, 12s at 25,
  60s at 40, 2g 20s at 60, 14g 40s at 80). Between anchors the price is interpolated linearly in
  integer math and rounded half up to 1c below 100c, 10c up to 9999c, and 1s from 1g. Outside the
  anchors it is clamped (below level 1 is 10c, above 80 is the last anchor). The curve is validated on
  load: levels strictly increasing, prices non-decreasing, > 0 and on their own rounding step (a multiple of
  10 from 100c, of 100 from 10000c), else `PricingPolicyError`.
- **`PRICED_TRAINER_IDS`**: an explicit allow-list (13 Death Knight, 18-30 mage portals, 200-217 class
  trainers). A stock trainer that later gets an NPC wired to it is *not* repriced silently. A listed
  trainer with no live spawned NPC (`TrainerIndex.trainer_problems()`) gets a `WARNING` and is skipped.
- **`PRICE_OVERRIDES`**: `{SpellId: copper}`, a fixed price on every priced trainer that beats the curve.
  Empty.

**Rows in scope** are the true live `trainer_spell` rows of the priced trainers (a replay over every
file, generated ones included) plus `trained_by()` declarations. A declaration supplies every column
except `MoneyCost`: **`money_cost` is ignored on a listed and live trainer** (it is still honoured on a trainer
outside the allow-list, and on a listed one with no live NPC, which is skipped with a WARNING). Keys retired by `untrain()` are excluded. Only rows that differ from live are
emitted, so a rerun emits no `trainer_spell` rows. Nothing is read from the old price, so nothing can
compound; retune by editing the curve and regenerating.

**Stock-trainer discount.** Every other stock trainer, `DISCOUNTED_TRAINER_IDS` (1-12, 14-17, 31-199: dead
class trainers, riding, profession, pet, and any trainer upstream adds below the server's own range at 200),
sells at `STOCK_TRAINER_PRICE_FACTOR` (`"0.2"`) of its *hand-written* price, rounded half away from zero as MySQL
stores `MoneyCost * 0.2`. A hand-written or upstream price written later is discounted automatically (user ruling
2026-11-06). The base is `trainer_pricing.replay_hand_written_trainer_spells()`: the replay of every file, generated
ones included, followed statement by statement (`apply_composite_key_statements(after_statement=...)`). A key's
first price is its base; a later price replaces it unless it is exactly the discount of the base or of the price
right before it (`Policy.is_discount_of`, which also knows `PREVIOUS_STOCK_TRAINER_PRICE_FACTORS`): that is a
discount, generated or the 2026-08-22 one. Provenance comes from the values, not from which file a statement sits
in, so a squash can neither compound the discount (a generated block under a hand-written header) nor hide a newer
hand-written price (a hand-written change inside a generated file). A hand-written price that is exactly 1/5 of the
one before it reads as a discount; the row keeps that price either way. **A declared price is final**: a
`trained_by(..., money_cost=X)` row on a discounted trainer is emitted at `X`, never discounted (ruling
2026-11-06). Spells in `DISCOUNT_EXCLUDED_SPELL_IDS` (Apprentice / Journeyman / Expert Riding, hand-set by
`2026_09_06_00`) keep their price. It replaces the one-off `UPDATE trainer_spell SET MoneyCost = MoneyCost * 0.2`
that ran live on 2026-08-22 from the unmerged `init-server` branch (535ff98c0): the first run after it emits the
discounted rows, most of them already at that price live. When you change the factor, add the old one to
`PREVIOUS_STOCK_TRAINER_PRICE_FACTORS`.

**The replay must be faithful**, because its output drives writes. `sql_dump.apply_composite_key_statements`
applies `(TrainerId, SpellId) IN (...)`, single-column `=`/`IN`, AND-ed point, `BETWEEN` and OR-of-AND
DELETEs and UPDATEs (`parse_where_predicate`), honours every UPDATE condition (key or not), evaluates
`SET col = col | n` style expressions, and for `trainer_spell` fills omitted INSERT columns with 0 at INSERT
time. A statement it cannot apply prints `WARNING: trainer_state.py: <file>: cannot replay ...`, including
`UPDATE ... AS alias` and an unquoted table name (the statement scanner cannot see those, so a separate scan,
`trainer_state.invisible_statements`, reports them). `TRUNCATE` and `INSERT IGNORE` are replayed since
dbc-replay-fix; `INSERT ... SELECT` / `INSERT ... SET` into the table warn like any other unreadable statement.
Treat any such WARNING as a bug in the replay or the SQL: the pass may re-insert a row that SQL removed. Not
detected: a statement that merely mentions the table inside a larger construct (a subquery of another table's
statement).

The same replay serves `creature_template`/`creature_template_model` (`lib/spell_tables.py`), where the
widened WHERE/expression support corrects stock values to live; those callers do not warn.

## The prune pass: removing a `scripted_by()` / `procs_on()` from source

Deleting a declaration from `source/classes/*` does **not**, on its own, delete the row. The delta
emitter above only ever speaks about rows it still declares, so before the prune pass existed a
removed binding stayed live in the world DB forever — costing a `Scriptname '<x>' ... not found`
boot error per orphaned `spell_script_names` row, and a proc chance nothing handles per orphaned
`spell_proc` row. Found via Shadow Reach's capstone rework (2026-09-23).

`lib/spell_tables.py`'s `render_prune_blocks()` now closes it: it emits a bare `DELETE` for any key
a **previous generated run** emitted that the source no longer declares, and `generate.py` prints
one line per removal.

Provenance is the whole design. A row is the tool's to delete only if a marker-bearing file
emitted it — `GENERATED_MARKER`, the `-- Generated by apps/dbc-tools/generate.py` first line every
`generate.py` output carries. The base dump, hand-written migrations and module SQL are excluded by
construction. Pruning "every row belonging to a spell id we manage" was considered and **rejected**:
the DSL declares plenty of *stock* spells just to edit a tooltip, and stock AzerothCore ships
`spell_script_names`/`spell_proc` rows for many of them (Penance 47540 → `spell_pri_penance`), so
that model deletes stock bindings and re-creates the "spells go inert" bug in
`docs/bugs-and-fixes.md`.

Two refusals, both of which print rather than act:

- **Stock overlap.** The orphaned key also exists in `data/sql/base/db_world/<table>.sql`, meaning a
  past run *overrode* a stock row instead of adding one — `DELETE` would leave a hole where
  AzerothCore has a row. Reachable only for the single-key tables; three such rows exist today
  (`spell_proc` `-14531`, `-45234`, `-47516`, the negative "this spell and all its ranks" ids).
- **Circuit breaker.** A table with emitted history but zero declarations this run means the source
  failed to load, not that everything was retired; the table's prune is skipped wholesale.

`--no-prune` disables the pass. Design notes:
`.agents/plans/dbc-tools-prune-pass/dbc-tools-prune-pass.PLAN.md`.

The emitted set is a **replay**, not a union: `sql_dump.read_table_statements` walks each generated
file's INSERTs and DELETEs in file order. That matters because the prune writes its own DELETEs into
these same files — a union would re-report every already-pruned row on every later run, and would
write a migration file even when nothing changed.

Note this interacts with the rule above: the prune reads *generated files still on disk*, so
deleting an earlier `rev_*.sql` also erases the tool's memory that those rows were ever emitted.

## Stale overlay rows: a DBC row returned to stock (`lib/stale_overlay.py`)

The DBC tables' new/edited/unchanged split (`resolve.resolve_rows`) compares against
`state.load_existing_rows`, which is promoted state only (`db_world/`). A row an earlier run wrote into a
**pending** file is invisible to it, so a declaration edited back to its stock values before that file was
promoted read as "unchanged" and emitted nothing — no INSERT and no DELETE — and the earlier overlay row
stayed live (Shockwave's talent 1872 move, fixed by hand on 2026-10-30; the same pass found
`skilllineability_dbc` 17659 still superseded by the retired Thunderstorm 202594 after the shaman removal,
and `spell_dbc` 5405 still carrying the Frost Mage rework's old edit).

`generate.py` now replays each of `spell_dbc`, `talent_dbc`, `talenttab_dbc`, `skilllineability_dbc` and
`item_dbc` as the server loads it (base dump, then promoted, pending and module migrations) and records
which ids a generated file wrote last (same `GENERATED_MARKER` provenance as the prune pass; a later
hand-written or module INSERT/UPDATE/DELETE of the id makes it not ours). Then, per table:

- out of the reserved block, declared at stock values, a generated overlay row live → bare
  `DELETE ... IN (id)` (joins the edited-id DELETE, no INSERT); prints `stale overlay: ... deleting`.
- out of the block, **no longer declared**, stock DBC has the id → the same delete. A custom id with no
  stock row is only reported (`note: stale overlay: ... left live`), since a delete would drop the row.
- declared, live generated row differs but the declaration is not stock (or the base dump has the id) →
  re-emitted as an edit.
- an edit `resolve_rows` already found whose declared row equals stock is not re-inserted (`not
  re-inserting`): a delete if a generated row is live, nothing if no overlay row is live (the replay in
  `load_existing_rows` treats a DELETE as also removing the DBC row, which is how such an id reads as edited).
- a reserved block whose live rows differ from this run's rows (a pending-only row since dropped) is
  re-emitted even if promoted state matches.

Not covered: the four secondary tables (durations, ranges, radii, cast times); an orphan reserved row there
is unreferenced and harmless. The replay is ~45 s cold, cached like the other loaders after that.
Tests: `lib/test_stale_overlay.py`.

## Frozen replay inputs: mod-progression's applied phase 0 (progression-slim PS1)

mod-progression applied `src/phase_00/sql/` once (2026-09-02 19:54, 42 `phase_00-*` rows in `acore_world.updates`)
and never a later phase: `Progression.Reset` never ran in Docker (`AC_UPDATES_ENABLE_DATABASES=0`). The module is
retired and dbc-tools reads no module phase files any more (`progression_phase*`, `load_phase_table_rows` and the
phase warnings of `render_removal_blocks` are gone; the plain typo guard stays). Things that are not obvious:

- **Where it lives.** `apps/dbc-tools/replay/frozen/2026_09_02_mod_progression_phase_00/`: the 42 files byte for byte
  (hiafi/mod-progression 8c765a1), `MANIFEST` (SHA1 = the `updates` hashes, in apply order), `SLOT`
  (`after = 2026_08_21_01.sql`, `before = 2026_08_22_00.sql`, read from the `updates` timestamps: every promoted file
  up to `after` ran before it, every one from `before` on after it), `ALLOWED_DIFFS`, and a `.gitattributes` /
  `.editorconfig` that stop git and editors from touching the bytes. `lib/test_frozen_replay.py` checks the hashes.
- **Where it is spliced.** `lib/frozen_replay.splice` puts the files right after `after` in the sorted promoted list.
  Readers: `trainer_state._migration_files_mentioning` (every table replay, `stale_overlay`, `spell_tables`) and
  `state._promoted_paths` (the DBC-table state, so `map_dbc` 249 and `mapdifficulty_dbc` 26 / 323 are visible). A list
  without either anchor (a test's temp dir) is left alone; a promoted file named inside the slot is an error.
  `_split_stable` counts frozen files as stable, so the disk cache keeps them in the cached prefix.
- **Also in the item overlay** since item-tools-replay: `apps/item-tools/item_lib/replay.py` splices the slot into
  its own (recursive) file list. `item_template()` emits column-limited UPDATEs either way.
- **Read normalised.** `sqlcorpus.read_text` returns a frozen file through `frozen_replay.normalise`: `-- comments`
  inside `IN (...)` lists and between INSERT tuples stripped, `SET @a := 1, @b := 2;` split, backticked column names
  in the schema's letter case. The shared parsers skip or misapply all three (an UPDATE guard on a column the row
  does not hold counts as satisfied: phase 0 writes `` `entry` `` for `creature_loot_template.Entry`, so its emblem
  swap hit every Emblem of Triumph row). Without it the replay lost ~1,000 `creature_template` cells of phase 0.
  Pending files with commented `IN` lists (the progression-slim cutover SQL) are still skipped with a WARNING (in
  `apps/item-tools`' overlay too, which shares the parser).
- **Replay vs live.** `replay_diff.py` (logic in `lib/replay_diff.py`) replays each table phase 0 writes over the files
  the live `updates` table lists and compares the cells phase 0 changed with the live DB (read-only). It applies the
  same three fixes to every file, re-keys a row whose key column an UPDATE changed, and models `TRUNCATE`. Result at
  PS1 (2026-11-05): 40,285 footprint cells on 5,353 rows match except the four `spell_dbc` cells in `ALLOWED_DIFFS`.
  Not checked: statements the replay cannot apply at all, listed per table in its output. Run time ~15 min
  (`smart_scripts` and `spell_dbc` dominate). `replay_diff.py --whole` is the wider check, see "What the SQL replay
  reads" below.

## What the SQL replay reads, the skip log, and the whole-table check (dbc-replay-fix)

Plan and report: `.agents/plans/dbc-replay-fix/` (local). Every loader replays with `lib/sql_dump.py`
(`apply_statements` for a one-column key, `apply_composite_key_statements` otherwise; `read_table_rows` is the union
reader). Since 2026-11-05 they read:

- **Files in DBUpdater's order** (`trainer_state.update_files`, verified against
  `src/server/database/Updater/UpdateFetcher.cpp`): every include directory goes into one set ordered by bare file
  name, subdirectories included, applied in two passes. Pass 1 is `data/sql/updates/db_world/**` with the frozen
  phase 0 spliced in at its slot (mod-progression applied it itself, outside DBUpdater). Pass 2 is
  `pending_db_world/**`, `data/sql/custom/db_world/**` and every module's `data/sql/db-world/**` *together*, by bare
  name: a module file named `2016_...` runs before a pending `rev_...`. Two files with one name raise
  `DuplicateUpdateName`, as DBUpdater refuses to start. `data/sql/archive/` is older than the base dumps and is not
  read. Every loader, `state.load_applied_rows` and item-tools share this one list. Live ran files in the order they
  appeared, not this order; the whole-table check shows where the two would differ. Spell 200100 belongs to
  mod-transmog's `2016_11_17_transmog_npc.sql` and is a `foreign` hole in the spell block (see "Foreign ids" below).
- **Session variables** (`_apply_set`, `_Expr`): `SET @x := <expr>[, @y := ...];` where the value is an integer or
  float literal, a quoted string, `NULL`, or an expression over earlier variables (`@CGUID * 10`, `-(@A + 3)`,
  `0x10 | 0x20`). Precedence is MySQL's (`unary - + ~`, `*`, `+ -`, `&`, `|`); names are case-insensitive and each file
  starts a fresh session (DBUpdater runs one client per file). A `SET` from a subquery or `IF()` leaves the variable
  unresolved; a statement using it is skipped with that reason. The union readers use the value in effect at each
  statement (`_VariableTimeline`).
- **Expressions wherever a value goes**: VALUES (`(@GUID+15)`, `-@GUID`, `@ENTRY*100+1`), SET clauses, and WHERE
  predicates, where `_prepare_statement` evaluates each arithmetic run holding a variable (keeping an `IN (...)` list's
  own parentheses and a binary operator after a column). An UPDATE value may read the row's columns
  (`` `flags` & ~(1 | 2) ``, `_RowExpr`), a column assigned twice in one SET is applied left to right (`_Chain`).
- **Double-quoted strings** everywhere, `-- ` / `#` / `/* */` comments inside a statement, a `;` inside a string, and
  a statement head inside a line comment or a `/* ... */` block is not a statement (`_head_in_comment`;
  `/*! ... */` is MySQL's executable comment and is not a comment).
- **Keys as MySQL holds them**: an UPDATE that assigns a key column moves the row to its new key, so a later INSERT
  of the old key is a new row (S1 of the review; two rows on one key make MySQL refuse the statement, recorded as
  skipped). With the table's integer columns (`parse_create_table_int_columns`, passed by every loader that has a
  base dump) a key written as `'5'` is the integer 5 and a non-integer number an UPDATE writes is rounded half away
  from zero (`SET MoneyCost = MoneyCost * 0.2` stores 2469, not 2469.4). `NULL`, `TRUE` and `FALSE` read in any
  letter case.
- **`INSERT ... ON DUPLICATE KEY UPDATE`**: a new key's row is inserted as written; an existing row gets only the
  clause's assignments (`` `c` = VALUES(`c`) `` or an expression over the row), the other columns stay.
- **WHERE** (`parse_where_predicate`): OR of AND chains of `= != <> < > <= >=` against numbers or quoted strings
  (strings compare case-insensitively), `[NOT] IN (...)`, `BETWEEN` (bounds may carry an exponent), `IS [NOT] NULL`,
  `(col & n) != 0`, on key or non-key columns (core-dd's id-only spawn DELETEs). A condition on a column the row does
  not hold is judged on the schema default (`defaults`, from the base dump's `CREATE TABLE`); without one it fails
  for a DELETE and for an UPDATE that names no key column. An UPDATE with no WHERE touches every row. Every
  condition of an UPDATE is honoured in both replays (a guard `AND col = <old>` that fails leaves the row, as in
  MySQL); `= NULL` is never true. In the keyed replay the `=` / `IN` / `BETWEEN` fast paths read row ids only on the
  index column; the same shape on another column is a filter.
- **Expressions on a column the INSERT left out** read its schema default; without one the assignment is recorded
  as skipped. An expression on a column the table no longer has (an UPDATE of `mechanic_immune_mask` before upstream
  dropped it) is not replayed at all.
- **Schema statements**: `INSERT ... VALUE` (singular, mod-transmog) reads like `VALUES`, `INSERT IGNORE` keeps an
  existing key's row, `TRUNCATE` empties the table, `ALTER TABLE` `CHANGE`/`RENAME`/`DROP`/`ADD` columns rename or
  drop them in every row and move the positional INSERT layout for the rest of that file (`creature.id1` -> `id`, 2026_06_16_00). Column names are matched case-insensitively against
  the loader's column list (`_ColumnCase`). An INSERT that leaves out a key column takes its schema default
  (Brewfest Reveler's `smart_scripts` rows omit `link`).

**The skip log.** A statement the replay cannot apply is still skipped, never guessed at, but never silently: it
is recorded in `sqlcorpus.SKIPS` (table, file, offset, reason, statement start). A cached replay stores its skips in
the snapshot and records them again on a hit, so a warm run reports what a cold one does. `generate.py --check` (whole
tree) and the full run end with `WARNING: replay: N SQL statement(s) could not be replayed ...` and one line per
table with the commonest reasons. Statements the head scanner cannot see at all (unquoted table name, `UPDATE`
with an alias) are recorded by `trainer_state._record_invisible` for every `load_replayed_table_rows` /
`load_keyed_table_rows` table, which now list files with a bare-word mention of the table too.

**The whole-table check.** `replay_diff.py --whole [--tables a,b] [--json FILE]` replays every table in
`lib/replay_diff.REPLAYED_TABLES` over the files the live `updates` table lists and compares every row (on the
primary key, read from the row's values) and every live column with the live DB, read-only. DBC-backed tables are
checked with both replay functions and get the `live_secondary_rows.sql` seed `state.py` adds, then
`apps/dbc-tools/source/live_orphan_rows.sql`: the live-only `spell_dbc` (2,273), `talent_dbc` (220) and
`talenttab_dbc` (30) rows and 4,926 `spell_dbc` index remaps from deleted pending migrations, as `INSERT IGNORE` and
UPDATEs guarded by the value they replace, so they never override a file. Only the check reads it: in `state.py`'s
state the remaps would make a full run re-emit ~3,800 stock spells and the 200000 block pointing back at the stock
indices (tested), and every orphan id is already there from the client DBC. Explained differences live in
`apps/dbc-tools/replay/ALLOWED_TABLE_DIFFS` (TSV `table`, `key`, `column`, `reason`; key `*` = any key; column `*`,
`*missing` (live only) or `*extra` (replay only) for a row on one side). It exits 1 on an unexplained difference, a
stale entry or a duplicate replayed key (two replayed rows on one key: the live table cannot hold that, so the replay
is wrong). About 15-20 minutes. At dbc-replay-fix: 0 unexplained over 49 table checks;
`smart_scripts` 53,890 = 53,890 rows, 0 cell differences. Known limit of the orphan seed: it runs after every file,
not at the slot its rows were written, so a later file that DELETEs a seeded id would see it come back from the
`INSERT IGNORE` and the check would show a false `*extra`. Drop the id from the seed then; never allow-list it.

Not read (recorded as skips): subqueries, function calls (`SIN()`, `COALESCE()`, `UNIX_TIMESTAMP()`), `/`, `DIV` and
`%`, `INSERT ... SELECT` and `INSERT ... SET` (a statement head of their own, kind `X`, that every replay and the
union reader record), `DELETE ... LIMIT`, `UPDATE` with a join or an alias (recorded by `_record_invisible`),
`PREPARE`/`EXECUTE`. One function is read: `ABS(`col` - n) < tolerance` in a WHERE, item-tools' float guard
(1,953 `item_template` UPDATEs). A plain `INSERT` of a key that already exists replaces the row (MySQL would refuse
the file); the loaders depend on that for stock rows the client DBC seeds and the live table does not hold.

**item-tools replays with this parser** (item-tools-replay): `apps/item-tools/item_lib/replay.py` runs
`apply_composite_key_statements` for every table item-tools reads (`item_template`, the itemization tables, the
dungeon browser's `creature` / `creature_template` / loot / instance tables) over its own file list (this tool's
order, plus `db_world/`/`pending_db_world/` subdirectories), records skips in `sqlcorpus.SKIPS`, and has its own
whole-table check, `apps/item-tools/replay_check.py`, built on `lib/replay_diff.py` with its own allow list
(`apps/item-tools/replay/ALLOWED_TABLE_DIFFS`). Its file list is `trainer_state.update_files` too. Its private copy of
the parser is gone. Report:
`.agents/plans/dbc-replay-fix/item-tools-replay.REPORT.md` (local).

### Unchanged reserved blocks are judged against pending revs too (dbc-replay-fix follow-up)

`_drop_unchanged_blocks` used to compare a reserved block only with `state.load_existing_rows` (promoted files), so
every block whose current version sat in an unpromoted `pending_db_world` rev was re-emitted, and a no-change full run
always wrote a rev (spell 200000-209999 plus the stock-id edits, skilllineability 30400-30999, item 70000-79999). A
block promoted state calls changed is now also checked against `state.load_applied_rows` (promoted state plus
DBUpdater's second pass: pending, custom and module SQL together by bare name) and dropped when it equals that.
`load_existing_rows` itself stays promoted-only. The rev a run writes is written after the check, so it never counts;
a row removed from source, a stale overlay delete or an edit the pending revs do not hold still emits. Module SQL is in
the applied state in its DBUpdater slot (a module file named `2016_...` sorts before a pending `rev_...`).

### Foreign ids: another owner's id inside a reserved block (spell 200100, mod-transmog)

`source/ids.yaml`'s spell block has `foreign: {200100: "mod-transmog (...)"}`. The stock mod-transmog module inserts
its Ethereal Warpweaver pet summon at 200100 (`2016_11_17_transmog_npc.sql`, conf `Transmogrification.PetSpellId`), and
the module stays stock, so the id is a permanent hole in our block (`lib/source.py`'s `foreign_ids`):

- the block DELETE is split around it: `BETWEEN 200000 AND 200099` and `BETWEEN 200101 AND 209999`
  (`sql_out.block_ranges`), both on `sql_dump`'s fast range path; a row or edit on the id raises in `sql_out`;
- `source.in_range`, `resolve.reserved_range_changed`, `stale_overlay.find_stale`, generate.py's `_block_ids` (the
  applied-state watch list) and `ids.next_free_id` leave it out, so its row never makes a block look changed, stale
  or prunable;
- declaring it (DSL, CSV or a GCD-haste aura) is `ERROR: spell 200100 (...) uses an id owned by mod-transmog ...` in
  a full run, `--check` and `--check --class`.

Lasting Flame rank 2 sat on 200100 until 2026-11-06 and moved to 205100, the first id of the new
`reservations: mage` spell slice (205100-205199). The earlier generated revs left Lasting Flame at 200100, so a
hand-written pending migration copies the module's DELETE + INSERT back over it; it sorts after every pending rev
that writes 200100, so live and a rebuilt DB (pass 1, then the module file, then the pending revs) both end with the
module's row. Pinned in `lib/test_foreign_ids.py`. Add a hole the same way when another stock module claims an id
in one of our blocks: never edit the module.

**Every pending file on disk counts** (db-import applies every one in the working tree, committed or not). So a block
dropped this way depends on files that must ship: the run names them (`note:   Spell: not re-emitted because its
content is in pending file(s) rev_..., ...; they must ship`). `state.load_applied_rows(watch=...)` records, per
watched id, the second-pass files that changed its row (`AppliedRows.sources`). Never delete, squash away or
regenerate a named file without its content, or that content is lost until someone reruns generate.py.

## WP-T: five more declared tables, and declared removals

`.agents/plans/druid-rework/druid-rework.WP-T-HANDOFF.md` (PLAN B11/§5.0) added five more world-DB
tables a `source/classes/*.py` file can declare - `spell_linked_spell`, `spell_group` +
`spell_group_stack_rules`, `spell_custom_attr`, `spellshapeshiftform_dbc` (`lib/dsl/registry.py`'s
`linked_spell`/`spell_group`/`spell_group_rule`/`custom_attr`/`shapeshift_form`) - so the druid
rework ships with **no hand-written `pending_db_world` file at all**. All five slot into the same
`lib/spell_tables.py` `SPELL_TABLES` machinery the original three (`spell_script_names`/
`spell_bonus_data`/`spell_proc`) already used: diff against live, DELETE-then-INSERT the rest,
silent on an unchanged rerun, and - since they're in `SPELL_TABLES` - automatically covered by the
prune pass above if a class file stops declaring one. Usage: `apps/dbc-tools/README.md`'s
"Declaring more world-DB tables" section.

Two design notes worth knowing before extending this further:

- **`spell_group`'s real SQL column is itself called `id`.** Every other declared table's dedup
  key (`load_classes_dir`'s cross-file duplicate check, keyed on `entry["id"]`) is a synthetic
  string that never collides with a real column name. `spell_group` is keyed on `(id, spell_id)`
  with `id` being the real group id column, so two different members of the *same* group would
  otherwise look like the same declaration twice. `entry["_dedup_id"]` is the escape hatch -
  `load_classes_dir` checks it before falling back to `entry["id"]` - see `spell_group()`'s and
  `load_classes_dir()`'s own docstrings. `leave_spell_group()` needs the same treatment.
- **`shapeshift_form()` needs a real extracted `SpellShapeshiftForm.dbc`.** Unlike the other four
  (plain world-DB tables with no DBC counterpart at all), this one builds a *full override row* -
  every column starts at the stock value and only the named ones change - so it has to read the
  stock row from somewhere. `var/extractors/dbc/SpellShapeshiftForm.dbc` didn't exist before this
  package; it was extracted the same way `Item.dbc` was (`patch-enUS-3.MPQ`, this doc's "Item.dbc"
  section above) - `smpq -x <mpq> DBFilesClient/SpellShapeshiftForm.dbc`, then flattened into
  `var/extractors/dbc/` (not left under a `DBFilesClient/` subdirectory - `state.BASE_DBC_DIR`
  expects the flat layout). 35 fields, 140-byte records, confirmed against `DBCStructure.h`'s
  `SpellShapeshiftFormEntry` and the file's own header. `Name_Lang_*` is `'x'` in `DBCfmt.h` (the
  AC struct never reads a form's name) but is real string-table-offset data in the file - marked
  `read_as_string` in `lib/dbcfmt.py`, same as `TalentTab`'s own name column, or a raw offset like
  `53` gets written straight into the `varchar(100)` SQL column instead of `'Bear Form'`.

**Declared removals** (`unbind_script`/`unlink_spell`/`leave_spell_group`/`untrain`) are a
separate mechanism from the prune pass above, for the case the prune pass explicitly can't cover:
retiring a row this tool never emitted itself (stock Blizzard data, or an older hand-written
migration) - the prune pass's whole notion of provenance is "did a *generated file* emit this",
and a stock row was never one. Provenance for a removal instead means "has a generated file's own
DELETE already covered this exact key" (`spell_tables.load_removed_keys` - a plain accumulation of
every matching-shape DELETE a past run has emitted for the table, not a replay against INSERTs the
way `load_generated_table_rows` is, since a removal never has an INSERT side to net against - the
declare-and-remove conflict check enforces that). A removal whose key doesn't exist anywhere (base
dump, migrations, module SQL) still gets emitted - the DELETE is a harmless no-op either way - but
prints a `WARNING:`, almost always a typo.

## T1: creature_template/creature_template_model

`.agents/plans/warlock-rework/warlock-rework.T1-HANDOFF.md` added two more declared tables -
`creature_template`/`creature_template_model` (`lib/dsl/registry.py`'s `creature_template()`/
`creature_model()`) - for a rework's own NPC (a talent's summoned add), so those also no longer
need a hand-written migration (the precedent this replaces, Tentacle of Madness, is
`data/sql/updates/db_world/2026_09_23_12.sql`). Usage: `apps/dbc-tools/README.md`'s "Declaring a
creature (T1)" section.

Two things make this pair different from every WP-T table above, both stemming from
`creature_template` being on the SQL linter's do-not-delete list (`apps/codestyle/codestyle-sql.py`'s
`not_delete`):

- **Upsert, never DELETE-then-INSERT.** `creature_template` is rendered with a new
  `lib/sql_out.py` function, `render_upsert_block` - `INSERT ... ON DUPLICATE KEY UPDATE <every
  non-key column> = VALUES(<column>);`, no DELETE ever. Reading one back (so a live upsert reads
  as "already declared" and a rerun stays silent) needed `lib/sql_dump.py`'s core tuple reader
  (`_read_tuples`, shared by `read_table_rows` and `read_table_statements`) to stop treating
  `ON DUPLICATE KEY UPDATE ...;` after a VALUES list as unparseable - previously
  `trainer_state.load_table_rows('creature_template')` silently skipped any such file (see that
  function's own docstring, which documented this as a known gap before T1 closed it).
  `creature_template_model` (keyed on `CreatureID, Idx`) is narrow enough to keep the ordinary
  `render_generic_table_block` DELETE-then-INSERT path every other table here uses - only
  `creature_template` itself needs the upsert.
- **Never pruned.** Both tables are deliberately kept out of `SPELL_TABLES`/`render_prune_blocks`
  entirely - a separate `CREATURE_TABLES` tuple plus `load_creature_table_index()`/
  `render_creature_blocks()`/`render_creature_retirement_report()` in `lib/spell_tables.py` handle
  them instead. `creature_template` can't be DELETEd at all, and pruning only the model row would
  leave a creature with no visible model - so a declaration dropped from source is only ever
  reported (`render_creature_retirement_report` reuses `SpellTableIndex.rows_to_prune`'s orphan
  computation, it just never turns the result into SQL), never deleted automatically.

`creature_template`'s column list and per-column schema `DEFAULT`s are parsed from its own
`CREATE TABLE` (`sql_dump.parse_create_table_columns`/`parse_create_table_defaults`) rather than
hand-transcribed - the table is ~55 columns wide, and `parse_create_table_columns`'s own docstring
already explains why hand-transcribing a table that wide is its own source of bugs.
`creature_template()` builds a **full** row from that: an explicit `**columns` value, else (for an
entry that already exists) that column's *current live value* - see "Overriding an existing entry"
below - else a handful of documented overrides for columns where `ObjectMgr::CheckCreatureTemplate`
rejects or silently rewrites the schema's own DEFAULT at boot (`unit_class` 0 is invalid, becomes 1;
`BaseAttackTime`/`RangeAttackTime` 0 becomes `BASE_ATTACK_TIME`), else the real schema default.
`creature_template_model` is narrow (6 columns) and stays a hand-typed column tuple like every
other table above.

The SQL linter needed one narrow exception for the upsert shape to pass at all -
`insert_delete_safety_check` (`apps/codestyle/codestyle-sql.py`) normally demands a `DELETE`
immediately before every `INSERT`, which an upsert into a `not_delete` table can never have. The
exception (marked `# Custom:`) only fires when the `INSERT` targets a `not_delete` table **and**
its own statement carries `ON DUPLICATE KEY UPDATE` before the terminating `;` - a plain `INSERT`
anywhere still needs its `DELETE` exactly as before.

`source/ids.yaml`'s `creature` block is `300000-300999` - four live custom `creature_template`
entries already sat in it before this block existed (300001 Frozen Orb, 300002 Meteor Missile,
300100 Divine Star, 300102 Tentacle of Madness), and the warlock-rework plan (§4.5) pre-reserved
300140-300179 inside it for the Affliction/Demonology/Destruction passes that use this helper next.

### Test and tool NPCs (dpssim MT0)

`source/ids.yaml` has a second creature block, `npc_tools` (900000-900099), accepted by
`_validate_creature_entry` alongside `creature`. The training dummies (900001-900009) and healing
dummy (900011/13/14) are declared in `source/npcs/training_dummies.py`; `generate.py` loads
`source/npcs/` with the same `load_classes_dir` and merges it into the class registry
(`_merge_npc_declarations`). 900010 and 900012 stay hand-written.

`lib/sql_dump.py` now reads `REPLACE INTO` like `INSERT INTO`. It had to: 900001-900006, 900010
(`2026_09_01_00.sql`) and 900012 were created with `REPLACE INTO`, so the reader never saw them and a declaration could not
compare as live. MySQL's semantics (delete the same-key row, then insert; omitted columns are not kept) already
hold at every replay site because each stores `rows[key] = row`, never `.update()`; the plain-union
readers have no old row to drop. The same work fixed column lists wrapped over several lines (the
hand-written REPLACEs do this): the first name on each line kept its newline, so `name`,
`DamageModifier` and `HealthModifier` read as absent. The same fix also corrects
`trainer_spell.ReqAbility2` in `2026_09_27_00.sql`; every value of that column is 0, so it can only
remove false diffs.

The old replay gap `UPDATE ... WHERE entry IN (...) AND ScriptName = '...'` (`2026_09_29_03.sql`) is closed by
dbc-replay-fix: `parse_where_predicate` reads quoted literals.

### Three correctness fixes from code review (2026-09-28)

All three were found by checking T1's first commit against this repo's *actual* migration
history, not just re-reading the code - creature_template/creature_template_model turned out to
have real precedent the original three declared spell tables never did (a hand-written `UPDATE`
after the original `INSERT`, and a partial-column-list `INSERT`), which the design hadn't
accounted for:

- **Live state must replay `UPDATE`/`DELETE`, not just union every `INSERT`.** Frozen Orb 300001's
  `flags_extra` was inserted as `194` and later hand-fixed to `66` via a plain `UPDATE ... WHERE
  entry = 300001 AND flags_extra = 194` (`data/sql/updates/db_world/2026_09_01_01.sql`) - its
  `CreatureDisplayID` went through several such revisions too. `trainer_state.load_table_rows`
  (every other declared table's live-state reader) only unions `INSERT`s, so it kept reporting
  `194` as live forever; a re-declaration matching that stale value would have compared as
  unchanged and silently never applied the real fix. `lib/spell_tables.py`'s `load_creature_table_index`
  uses `trainer_state.load_replayed_table_rows` instead - single or composite key
  (`sql_dump.apply_statements`/`apply_composite_key_statements`), including a new AND-guarded
  `UPDATE` shape (`` `col` = n AND `other` = v ``, the exact idiom this repo's hand-written creature
  fixes use) that `sql_dump.py`'s existing replay machinery didn't recognize before.
- **Overriding an existing entry must not wipe columns it doesn't mention.** `creature_template()`
  originally always built from schema defaults, even for an already-existing `entry` -
  `_validate_creature_entry` explicitly allows overriding any live entry in the block, so
  re-declaring Tentacle of Madness to fix just its `ScriptName` would have silently reset its
  faction, levels, flags and every modifier. Fixed the same way `shapeshift_form()` already
  handles its own full-row override: start from the entry's current live row
  (`existing_creature_rows`, now full rows keyed by entry, not just a bare id set) and only
  overwrite what's explicitly passed.
- **A missing column's implicit value isn't 0 for every table.** `spell_tables._same_row` assumed
  a column absent from a live row defaults to `0`/`NULL` - true for the original spell tables, but
  wrong for `creature_template` (`minlevel`/`speed_run`/`RegenHealth`/... default to 1 or more).
  Real precedent: three module SQL files (`mod-transmog`, `mod-mythic-plus` x2) `INSERT
  creature_template` with a partial column list omitting exactly this kind of column. `TableSpec`
  gained a `defaults` field (`CREATURE_TEMPLATE_DEFAULTS`/`CREATURE_TEMPLATE_MODEL_DEFAULTS`) that
  `_same_row` checks before falling back to the old 0/`None` guess; every other table's `TableSpec`
  leaves it empty and is unaffected.

## `creature_template_columns()`: one owned column of a stock creature (progression-slim PS1 WP-P)

`creature_template()` builds and upserts a full row, which on a stock entry would own its name, flags and loot too.
`creature_template_columns(entry, **columns)` (`lib/dsl/registry.py`) owns only the named columns: the row goes to
`Registry.creature_template_edits` (a separate list, so the full-row lints and `header_gen` never see a stock
creature), `spell_tables.render_creature_blocks` compares just `_update_columns` (`_same_row`) against the replayed
live row and renders a column-limited `UPDATE` (`sql_out.render_update_block`, the `item_template()` shape) after the
full-row upserts. Live equals declared: no output. A later SQL file that changes the column: the next run re-emits the
declared value (this is the drift guard). Never pruned. `source/world/raid_health_prenerf.py` declares the 244 pre-nerf
TBC/WotLK raid `HealthModifier` values phase 0 set (every TBC/WotLK raid boss and trash mob keeps them until its raid is
reworked). `source/world/*.py` is loaded with `existing_creature_rows`/`creature_columns` for this.

Meeting a future dungeon-creature extraction (`dungeon(...)`): a dungeon creature that is also in the list (Hellfire
Channeler 17256 spawns in Magtheridon's Lair and the Blood Furnace) is the only overlap today. If the extraction
declares it as a full `creature_template()` row, built from live it carries the same `HealthModifier`, so the two agree
(`spell_tables.check_creature_edit_conflicts` stops generate.py on a disagreement, so the pre-nerf value cannot be lost
silently); the edit's UPDATE is rendered after the upsert and wins a tie. Otherwise they are independent.

## Paladin T1: `spell_category()` and `remove_spell_proc()`

`spell_category(id, flags)` declares a `spellcategory_dbc` row (a `SPELL_TABLES` entry, so diff/prune
like `custom_attr`); ids come from `ids.yaml`'s `spellcategory` block (1300-1319, widened by Warrior T1; stock max
1253).
The same declared rows also go into the client patch: `generate.py` merges them over the stock
`var/extractors/dbc/SpellCategory.dbc` (`dbcfmt.SPELLCATEGORY`, fmt `ni`, not in `ALL_TABLES`/
`SECONDARY_TABLES` so the SQL is not emitted twice) into patch-Z.mpq, and stops with an error if
categories are declared but that stock file is missing (extract it from the highest-numbered
`patch-enUS*` MPQ that holds it, flattened, like `Item.dbc` above). The server blocks category siblings
(same `SpellFamilyName`) but sends them to the client only for spells with
`SPELL_ATTR0_CU_FORCE_SEND_CATEGORY_COOLDOWNS` (`custom_attr` 0x10000000; core sets it only for Aimed
Shot); the client's sweep comes from its `Spell.dbc` `Category`/`CategoryRecoveryTime` plus the shipped
row. An in-game `.cooldown` plus visual sweep check on a sibling remains advisable.
`lint.check_undeclared_spell_categories` makes `generate.py` error on a spell using a block
category nobody declared (the server would silently drop the cooldown).

`remove_spell_proc(spell)` is a `REMOVAL_TABLES` entry on `spell_proc` (negative ids = whole rank
chain). Trap: `SpellMgr` builds a default row per spell id only when the spell has a trigger aura AND
non-zero DBC `ProcTypeMask`; an explicit row with ProcFlags 0 inherits them too. So -31871 (flags 0)
and Redoubt 20128/20131/20132 are disabled by the removal alone, but a trigger-aura spell with flags
needs `ProcTypeMask` zeroed on every rank. `lint.check_removed_proc_flags` warns per rank (a negative
id expands over the Talent.dbc rank chain: DSL talent ranks first, else existing `SpellRank_1..9`),
conservatively ignoring the trigger-aura condition. Both new checks run on a full `generate.py` run
only, not `--check`.
`lint.check_removed_proc_flags` warns while `abs(id)`'s `ProcTypeMask` is non-zero (other ranks of a
negative id are not checked).

## Dungeon finder exclusions: `lfg_exclude()`

`lfg_exclude(map_id, name)` (`source/world/lfg.py`; usage in `apps/dbc-tools/README.md`) declares a
`disables` row of sourceType 8, a `SPELL_TABLES` entry keyed on `(sourceType, entry)`. Things that are
not obvious:

- **`flags` must be 1.** `LFGMgr::IsDungeonDisabled` calls `DisableMgr::IsDisabledFor(DISABLE_TYPE_LFG_MAP,
  map, nullptr)`: no unit and flags 0, so the difficulty checked is always normal and a row without
  `DUNGEON_STATUSFLAG_NORMAL` never matches. The same call means heroic cannot be excluded separately.
- **No collision with the frozen phase 0.** mod-progression's applied phase 0 (a frozen replay input since
  progression-slim, see "Frozen replay inputs") wrote `disables` sourceTypes 1-5, 9 and 10 (maps are sourceType 2,
  which closes the instance itself), and the base dump has no sourceType 8 rows.
- **The prune circuit breaker is off for this table** (`TableSpec.prune_when_empty`): an empty
  `lfg.py` is a normal state, and with the breaker on, removing the last exclusion would never DELETE it.
- **`lint.check_lfg_exclusions` reads stock `LFGDungeons.dbc`** (`dbcfmt.LFGDUNGEONS`, read-only, not in
  `ALL_TABLES`). It errors on a map without a TypeID 1/2/5 entry, which includes continent maps (random
  entries have MapID 0), and DisableMgr rejects a continent map with flags anyway. With the file missing
  it errors only when something is declared.

## Dungeon finder entries: `lfg_group()` / `lfg_random()` / `lfg_heroic()` (lfg-classic-heroic)

`lib/dsl/lfg.py` (declarations in `source/world/lfg_classic_heroic.py`), `lib/lfg_dungeons.py` (rows), wired in
generate.py right after `dungeon_heroic.expand()`; its ERRORs and notes ride on the dungeon expansion, so the full
run and `--check` report them alike. Usage in `apps/dbc-tools/README.md`. Things that are not obvious:

- **A random draws from its own group.** `LFGMgr::LoadLFGDungeons` files every non-random row under its `Group_Id`
  and `GetDungeonsByRandom` returns the random's group, so a heroic random needs a group of its own (one random per
  group, checked) and every pooled dungeon a heroic row (Difficulty 1, TypeID 5) in it.
- **The final boss link.** `lib/dungeon_heroic.py` copies each normal encounter's credit with
  `lastEncounterDungeon` 0 and keeps the normal row's value as `_normal_lfg` (bookkeeping, never rendered);
  `lfg_heroic(normal=N)` sets the heroic row whose `_normal_lfg` is N to the heroic finder id. Without it
  `Map::UpdateEncounterState` never calls `LFGMgr::FinishDungeon` and the run never rewards. `ObjectMgr::
  LoadInstanceEncounters` skips the **whole encounter row** when the finder id is not loaded, so the heroic boss
  would lose its kill credit: a `--scope` run of a dungeon stops (`scope.reference_errors`, space `lfgdungeons`)
  while its final boss names a finder entry that is not live yet. The declarations are in a shared world file (no
  scope owns them), so only a full run ships the finder rows.
- **Client files.** The client takes names, the Specific Dungeons list and its section headers from its own
  `LFGDungeons.dbc` and `LFGDungeonGroup.dbc`, so both merge into patch-Z. `LFGDungeons.dbc` now reads
  `TextureFilename` and the Description locales as strings (they were raw offsets while the file was read-only).
  Stock row order: LFGDungeons by (TypeID, ID), LFGDungeonGroup by (OrderIndex, ID); `pack_client_dbc` keeps both
  (round-trip test). `LFGDungeonGroup.dbc` is not in the client extract: copy it from the
  `azerothcore-wotlk_ac-client-data` volume (`/dbc/`); a declared group with the file missing is an ERROR, not a
  silent "patch: SKIPPING".
- **Section order.** The finder lists sections by `OrderIndex`, lowest first (stock 1-5: Lich King Heroic ... Classic
  Dungeons; raids 17-21). Classic Heroic takes 5 and `lfg_group(1, order_index=6)` moves Classic Dungeons below it (a
  client-only edit of a stock row). A shared OrderIndex is a WARNING.
- **Level window.** The heroic rows take the random's window (60-62). mod-content-gate's `RandomQueueWindow` leaves a
  heroic random's window as is (only the highest open expansion's *normal* random runs to the cap); a content-gate
  difficulty gate (`36:N` without `H`) closes the heroic map, which `LFGMgr::IsDungeonDisabled(map, difficulty)` also
  reads, so the finder entry locks with it. mod-playerbots' `JoinLFG` uses LFGMgr's window, but its
  `IsExpansionOutleveled` keeps classic (ExpansionLevel 0) entries from bots above 60 unless
  `RandomBotJoinLfgOutleveledExpansion` is on.
- **Rewards are hand SQL** (`rev_lfg_classic_heroic_rewards.sql`): `lfg_dungeon_rewards` (300, 62), quests
  90000 / 90001 (ids.yaml `quest`, record only) and the satchel 70700 (`items.csv` row for Item.dbc / item_dbc,
  item_template and item_loot_template in the rev).

## Dungeon difficulties: `dungeon()` / `heroic()`, MapDifficulty and `dungeon_access_template`

`lib/dsl/dungeon.py` (usage in `apps/dbc-tools/README.md`), declarations in `source/world/dungeons/` (loaded as one
package by the `source/world/` pass). Things that are not obvious:

- **Two halves, one declaration.** `mapdifficulty_dbc` and `dungeon_access_template` are `SPELL_TABLES` entries
  (`prune_when_empty`); `generate.py` merges the same MapDifficulty rows over the stock file into patch-Z
  (`dungeon_checks.map_difficulty_client_rows`). The server needs its row or `GetDownscaledMapDifficultyData` turns a
  heroic request into normal; the client needs its row for the refusal text and the Raid Info difficulty name.
- **Stock `MapDifficulty.dbc` is ordered by (MapID, Difficulty), not ID**, so `dbcfile.pack_client_dbc` keeps that
  order (a new heroic row lands right after its map's normal row); an empty merge is byte-identical.
- **`dbcfmt.MAPDIFFICULTY.fmt` is DBCfmt.h's with the leading `d` written `n`** (dbcfile's index char); the 15
  non-enUS message locales and `Difficultystring` are `x` in DBCfmt.h but string offsets (`read_as_string`).
- **One row per (map, difficulty).** `sMapDifficultyMap` keeps the last row the store visits and
  `LoadAccessRequirements` the last loaded, so `dungeon_checks.check_dungeons` stops on a pair a stock or live row
  already holds under another id (mod-progression's Onyxia 26 / 323 are such live rows).
- **`dungeons`** is a bookkeeping merge key (one entry per map, `heroic` as a dict) that E2's encounter, spawnMask,
  `difficulty_entry_1` and heroic-template emitters read; it emits nothing itself.

### E2 (WP-T2): derived rows, `lib/dungeon_heroic.py` and `lib/spawn_state.py`

- **Derived, not declared.** `dungeon_heroic.expand()` runs once in `generate.py` right after the source loads (before
  the `--check` return and every render) and appends rows to `dsl_classes`: `dungeon_encounters`,
  `instance_encounters`, the `heroic_template_*` / `heroic_onkill_reputations` lists (new SPELL_TABLES entries,
  `prune_when_empty`), and heroic copies inside the existing `creature_template_spells` / `creature_template_models`
  lists (one owner per table, or each prune pass would delete the other's rows). Derived rows carry `_dungeon_heroic`
  so a second `expand()` replaces them. Its ERRORs reach both paths through `dungeon_checks.errors_for_run(...,
  expansion=)`.
- **Kill credit stays the normal entry.** A heroic creature's `GetEntry()` is the normal entry (`Creature::InitEntry`),
  so heroic `instance_encounters` rows copy the normal `creditEntry`; the table has no difficulty column (each row is
  filed under its DungeonEncounter row's (MapID, Difficulty)).
- **DungeonEncounter.dbc is ordered by (MapID, signed OrderIndex, ID)** (`OrderIndex` -1000 rows exist, so it is in
  `signed`); `pack_client_dbc` keeps it, and a heroic copy lands right after its normal row.
- **`difficulty_entry_1` rides `creature_template_edits`** (the `creature_template_columns()` path): a one-column
  UPDATE diffed against the replayed live row, merged into an existing edit of the same entry. Never pruned.
- **The spawn replay** (`spawn_state.load_spawn_state`, cached like the other loaders, `spawn_state.py` is in
  `CACHE_CODE_FILES`) fixes three gaps the generic replay has on `creature` / `gameobject`: the `id1` -> `id` rename
  (2026_06_16_00), double-quoted string literals (upstream's sniffed spawn files; `sql_dump` skipped those INSERTs
  whole: 10 Deadmines doors and levers), and DELETE / UPDATE whose WHERE has no `guid` (applied in file order). Checked
  against the live DB on 2026-11-05: no difference on the 19 vanilla dungeon maps (14 non-dungeon creature spawns
  still missing elsewhere). `sql_dump` itself still drops double-quoted INSERTs for every other table.
- **`heroic_entries`** on the `dungeons` entry (normal -> heroic) is the heroic template generator's hand-off; empty,
  the per-creature emitters do nothing.

### E2 (WP-G): the creature lists and `lib/heroic_templates.py`

- **Two halves per file.** `extract_dungeon_creatures.py` (live DB, SELECTs only; logic in `lib/dungeon_extract.py`)
  owns the `CREATURES` block between the markers and nothing else; `extra=` / `roles=` / `skip=` / `heroic=` live
  outside it and survive a rerun. A file with zero or two blocks is refused, never rewritten.
- **The generator runs inside `dungeon_heroic.expand()`** (step 3, before T2's `difficulty_entry_1` edits and
  side-table copies read `heroic_entries`), only for a heroic whose entry carries `creatures` (every `dungeon()` call
  does; T2's hand-built test entries do not). Its rows join `creature_templates` marked `_dungeon_heroic`, so a second
  `expand()` replaces them and the full-row upsert path renders them.
- **The lock file is the only source file generate.py writes** (`source/world/heroic_ids.lock`, after the SQL, full
  run only). New creatures take the next id after the highest in the file; gaps are never reused. Assignment is
  deterministic, so `--check` reports the same ids the full run writes.
- **Damage math is swing independent**: the tier's melee is per hit at 2.0 sec and scales with BaseAttackTime, so
  DamageModifier = melee / (2 x (1.25 x damage_base + attackpower / 14 x BaseVariance)) (creature_classlevelstats at
  the tier level, `Creature::CalculateMinMaxDamage`). HealthModifier is the 4-decimal value whose
  ceil(basehp0 x float(mod)) lands on the target (the plain rounded quotient is often one point high).
- **The SmartAI widening is a pinned UPDATE, not a block rewrite.** Each row is matched on its full key plus its
  current `event_flags` and gets `| 4`. The repo rule is to rewrite whole `smart_scripts` blocks, but the dbc-tools
  replay of `smart_scripts` misses 241 live rows and differs on 9 `event_flags` cells (2026-11-05; Scarlet Monastery
  4294-4303 and 4540 among them), so a DELETE + INSERT built from it could drop live rows. Deadmines has no
  normal-only rows; BRS and BRD hold most of them.
- **A creature declared this run counts as live** (Deadmines Pilot WP-K, `dungeon_heroic.with_declared_templates`):
  a boss-kit add declared with `creature_template()` (e.g. `source/npcs/deadmines/`) and listed in a dungeon's `extra=`
  gets its heroic template, `overrides`, lock line and side-table copies (its declared `creature_model()` rows) in the
  same run, not only after its upsert reached the SQL on disk. Its full row must name the heroic entry itself
  (`difficulty_entry_1` = its `heroic_ids.lock` id; `--check` prints the id in the "declares the full row" ERROR), and
  it gets no one-column `difficulty_entry_1` edit.
- **SpellDifficulty.dbc** (`dbcfmt.SPELLDIFFICULTY`, read-only, not in ALL_TABLES) feeds an informational note only;
  without the file the check is skipped with a note (the shared checkout has no copy yet).

## Superseded ranks: generated `SkillLineAbility` and `CreatureSpellData` overrides

Pets learn from `SkillLineAbility`, not trainers: `SpellMgr::LoadPetLevelupSpellMap` takes every row on a
creature family's skill lines with `AcquireMethod` 2 (`SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN`; 1 is
`..._ON_SKILL_VALUE`). The single-rank conversion removed the chains from `spell_ranks`, so a pet learned
every superseded rank as its own spell (an Imp with Firebolt 3110 and 7799..47964). `generate.py` now
overrides each stock row whose `Spell` is a superseded rank (a base `spell_ranks` chain member other
than the DSL spell tagged "single-rank bootstrap") and whose `AcquireMethod` is 2: the stock row with
`AcquireMethod` 0 (`lib/superseded_ranks.py`). A declared `skill_line_ability` with the same ID wins and
prints a `WARNING`. When added (2026-10-11) the rule covered 553 rows, all on pet-family skill lines
(warlock demons and hunter pets).

That alone is not enough, because pets have a second source: **default spells**. `LoadPetDefaultSpells`
reads the `CreatureSpellData` record named by `creature_template.PetSpellDataId` (a tamed beast keeps
the wild beast's entry), and `LoadPetDefaultSpells_helper` drops only the spells in the family's level-up
set. Stock records name ranked family spells (Ghost Saber: Claw 16829), so once the overrides above
removed those ranks from the level-up set they came back as defaults. The boot log showed it as
`Loaded Addition Spells For 803 Pet Spell Data Entries` (112 in stock). So the same rule also writes
`creaturespelldata_dbc`: each stock record that names a superseded rank, with that `Spells_N` replaced
by the survivor (`Availability_N` stays stock). The survivor is in the level-up set, so the helper drops
it again and the default lists are exactly stock's. That covers 714 of 802 records and 42 ranks. Things
that are not obvious:

- **Server-only.** The rows never go into patch-Z. The server never sends `PetSpellDataId` to the client,
  and it alone sends a pet's spells (`Player::PetSpellInitialize`).
- **The stock file is `var/extractors/dbc/CreatureSpellData.dbc`.** Only `patch-enUS.MPQ` carries it. If
  it is missing, the run prints a `WARNING` and emits nothing for the table.
- **The block is a delta.** Only records that `state.load_existing_rows` (stock plus promoted `db_world/`)
  doesn't already hold are emitted, through `render_generic_table_block`. The `SkillLineAbility` rows
  still go through resolve, because the client patch needs them.
- **Before promotion:** every run lists the 553 IDs in its "editing N existing ... skill line
  abilitie(s)" line and re-emits both blocks. That is expected; strip them if an earlier pending file
  already carries them byte-identically.
- **After promotion:** a run is silent. The overrides read back as live, `generate.py` counts them in a
  separate `note: superseded ranks: N SkillLineAbility override(s) already live` line (not as "unchanged
  copies"), and the `creaturespelldata_dbc` block is empty.
- **When a WARNING appears.** It appears only if a promoted migration left an overridden row as neither
  stock nor the override. Read it; the override is built from stock and replaces that change.

Existing pets keep whatever they already learned, so a rank-chain collapse also needs a characters-DB
cleanup. For this one, that is `pending_db_characters/rev_1791713091186211987.sql`. See
`docs/bugs-and-fixes.md` ("Pets learn every superseded rank..."). Plan:
`.agents/plans/pet-stale-ranks/pet-stale-ranks.PLAN.md`.

## Hunter T1: editing stock talents, pet spells and items

Added for the hunter rework (`.agents/plans/hunter-rework/`, SHARED Part C7). The README's "Editing stock
talents, pet spells and items" section has the call syntax; this is what to know when something misbehaves.

- **`acquire_method` / `superseded_by` on `skill_line_ability()`.** Typed, emitted only when not `None`, so a
  row without them is built byte-for-byte as before. `raw_overrides` is applied last and still wins.
  `lib.dsl.AcquireMethod` is the enum.
- **`retire_talent(id)`** appends a talent entry on holding tab **60800** (`RETIRED_TAB_ID`) and a
  `retired_talents` bookkeeping row (so retiring twice is a `DuplicateIdError`). It needs the live Talent rows,
  which `generate.py` passes to every `load_classes_dir` call as `live_data` (`spell_tables.dsl_live_data`). The
  tool scripts that load `source/classes/` themselves (`pull_dsl.py`, `potency_report.py`, `pull_talents.py
  --dsl`) pass `spell_tables.load_dsl_live_data()`; a new one has to as well, or a class file calling
  `retire_talent()`/`item_template()` raises `RuntimeError`. The holding tab is checked after all sources merge
  (`check_retired_talent_tab`), because a call cannot see a sibling file's `tab()` at import time.
- **Talent.dbc order.** `order_talent_rows` keys each row on its *final* TabID now. A moved or retired row leaves
  its stock block (which stays where it was) and joins the new one; a tab absent from the stock file gets a block
  after every stock block. Rows the stock file had keep their stock relative order inside a block, then new
  rows in the order given. `lib/test_client_dbc_roundtrip.py` still proves an untouched stock file repacks
  byte-identically.
- **`check_talent_tab_refs`** is an ERROR (the run stops before anything is written) on both populations: the
  server's live-plus-built rows and the client's stock-plus-built rows.
- **`retire_pet_spell`** is resolved in `lib/superseded_ranks.py` (`retired_skilllineability_overrides`,
  `spell_data_strips`, and the `strips=` argument of `creaturespelldata_overrides`) and wired in `generate.py`
  next to the superseded-rank pass, whose rows it shares (`rank_override_ids`). The `CreatureSpellData` strip
  zeroes the slot and its `Availability_N`; a record some other family's creature also names is left alone and
  reported, since a record cannot be split. Needs `var/extractors/dbc/CreatureFamily.dbc` (not in any client
  MPQ - the server's DBC dir has it, like `CreatureSpellData.dbc` above; `dbcfmt.CREATUREFAMILY` reads it,
  byte-identical round trip): a declared retirement without it is an ERROR, the family lint's rule (d) a WARNING.
  A superseded rank counts as the spell for the strip (a record naming only Bite rank 4 is stripped when the
  survivor is retired). `shared_lines=True` retires a shared-line (270) row for every family while the strip
  stays scoped to `families`; a retirement that matches nothing is a WARNING.
- **`item_template()`** uses `spell_tables.ITEM_TABLES` (a sibling of `CREATURE_TABLES`): upsert only, never
  pruned (`render_item_retirement_report` lists a dropped declaration), unchanged rows emit nothing. Two
  differences from `creature_template`: the live rows come from `apps/item-tools`' overlay (it recurses into
  `itemization_templates_v2/`; `trainer_state` does not; same `sql_dump` parser), and the statement is a column-limited
  `UPDATE ... SET <declared columns> WHERE entry IN (...)` (`sql_out.render_update_block` reads each row's
  `_update_columns`; rows with the same assignments share one statement). Reason: SQL the overlay does not read
  (the frozen phase 0's mount price and level columns, the progression-slim cutover SQL that resets them) writes
  other columns of these same rows, and a full-row update from a replayed copy would revert them. An UPDATE, not a multi-row `INSERT ... ON DUPLICATE KEY UPDATE`, because the overlay
  reads only the first tuple of an INSERT (T-FIX T1-1). A rerun after the migration applied emits nothing
  (`test_item_template.RoundTripTest`).
- **Item lints.** `check_item_dbc_consistency` (WARNING) and `check_ranged_ammo_type` (WARNING) run in the full
  run, not under `--check`. The 33 quiver `items.csv` rows are stock-id edits: they appear in the "editing N
  existing ... item(s)" line, in an `item_dbc` `DELETE ... WHERE ID IN (...)` plus INSERT, and in patch-Z's
  `Item.dbc`. The ranged-weapon edit has no DBC half: `AmmoType` lives only in `item_template`, the client reads
  it from the item query, so the client's `Cache` folder must be wiped once after rollout.
- **Family-bit lint** (`check_hunter_family_rules`) takes the built custom spell rows, the declared `spell_proc`
  rows, the SkillLineAbility rows (stock plus built) and the pet skill lines (270 plus `CreatureFamily.dbc`'s).
  Rule (c) inspects every effect mask whatever its aura (an effect mask only exists to be read), which is
  broader than the SpellMod-only scoping lint, and every declared `spell_proc` row whatever its spell id
  (SpellFamilyName 9 or 0; 0 matches any family). Rule (a) exempts an "Aspect of ..." name only for a spell
  with a SkillLineAbility row, so a same-named triggered aura still warns; the rule set's `exempt_ids` is the
  explicit escape hatch. Since shaman T1 the function is `check_family_bit_rules` (the old name is an alias) and
  runs under `--check` too, on the declared population; the full run still judges only the new or edited spells.
  Without `CreatureFamily.dbc` the full run prints a WARNING when custom class-set-9 spells exist.
- **TalentTab.dbc in patch-Z.** The retired tab 60800 (`order_index` 3, ClassMask 0, PetTalentMask 0) makes
  `TalentTab.dbc` ship for the first time. The first full run prints two WARNINGs (`TalentTab.dbc ships in the
  client patch ...  60800 (new)` and `TalentTab.dbc is new in the client patch ...`): accept them once and check
  every class's talent frame and the three pet tabs in game. Later runs, once the previous build already carried
  the file, print a `note:` instead when the only TalentTab rows are new inert ones (`lint.check_client_patch`'s
  `notes`); any edited stock row or a tab with a class or pet mask still warns. `CharacterDatabaseCleaner` keeps
  `character_talent` rows on a valid tab, so the characters SQL that retires a talent deletes them itself.
- **Cost.** Loading the item overlay and the Talent rows adds about 30 s to `generate.py` and to `--check`.

## Shaman T1: creature spell slots, spell lints and id blocks

Added for the shaman rework (`.agents/plans/shaman-rework/`, T1). The README's "Shaman T1" section has the syntax and
the lint table; this is what to know when something misbehaves.

- **`creature_spell()` / `remove_creature_spell()`** are `SPELL_TABLES` / `REMOVAL_TABLES` entries for
  `creature_template_spell` (key `(CreatureID, Index)`), so the whole prune / removal / provenance machinery applies
  unchanged. A totem's guardian summon must be on Index 0 (`Totem::GetSpell()` reads `m_spells[0]` when the totem is
  removed). The `TableSpec` defaults (`Index` 0, `Spell` and `VerifiedBuild` NULL) matter only for a hand-written
  INSERT that omitted a column; such a row reads back with NULL and re-emits once. `lib/test_creature_spell.py`
  renders, reads the output back through the readers the diff uses (`sql_dump.read_table_rows`,
  `load_generated_table_rows`, `load_removed_keys`) and checks that the rerun is empty (hunter T1-1).
- **Lint wiring.** `generate._t1_content_warnings` is the one function both the `--check` block and the full run
  call, so a `--check` session sees what the full run prints (hunter T1-10). It takes the built rows of every declared
  entry (`--check` builds them already for the family-zero lint) and a base spell dict: stock rows under `--check`,
  the promoted-aware live rows in the full run. `--check` only knows the declared SkillLineAbility rows. A new lint
  goes into that function and into `test_shaman_t1_lints.RealPopulationTest`, which fails when a lint fires on the
  declared population and no allow set covers it.
- **Allow sets** (`HIDDEN_LEARNED_ALLOW`, `GROUND_HASTE_ALLOW`, `SPELL_PROC_ALLOW`, `SHADOWED_PROC_ALLOW`,
  `TRAINER_SPELL_LEVEL_ALLOW`) hold the existing hits with a reason each; a new hit is fixed in the source, not added.
  `SHADOWED_PROC_ALLOW` is the priest rework's known live bug (12 per-rank rows dropped as `duplicate entry` by stock
  chain rows); its input is the *replayed* `spell_proc` table (`_proc_shadow_inputs`), because the union reader would
  keep a chain row a later migration deleted (-47580) and report false shadows.
- **`check_totem_tools` widening** also walks the base Spell rows (stock under `--check`, live in the full run), so the
  opt-in covers the 117 stock family-11 tool spells, not only the 42 the source declares.
- **LEARN carriers.** `check_hidden_learned_spells` follows LEARN_SPELL (effect 36) targets of learned spells and
  treats a spell whose every effect is effect 36 as a deliberate hidden carrier, so the warlock 59672-pattern talent
  ranks need no allow entry.
- **`lint.TOOL_FREE_CLASS_SETS`** is the SH0 hook for `check_totem_tools`. The 42 stock family-11 spells with a
  non-zero tool column all carry only `RequiredTotemCategoryID_1` (TotemCategory 2 Earth, 3 Air, 4 Fire, 5 Water).
- **Family-bit rules** are data (`FamilyBitRules`); a zero mask turns its rule into a no-op, and the message wording
  (`protected_label`, `reader_label`, ...) comes from the rule row.
- **`ids.yaml` reservations.** The `reservations:` key is a mapping of owner -> table -> `{start, end}` (an owner is a
  class, or a non-class project such as `healsim`; see "Death Knight T1"). Every reader
  of `ids.yaml` indexes it by table name and none iterates it, so it is invisible to them; do not add a reader that
  iterates the file's top level without skipping `reservations`.
- **`--check` count line.** `note: ... (DSL) contributed ...` leaves out tables with nothing declared, so adding a
  table to `SPELL_TABLES` does not change the line until something declares into it.

## Death Knight T1: rune costs, creation data, the class row and `--check` additions

Added for the Death Knight rework (`.agents/plans/death-knight-rework/`, T1). The README's "Death Knight T1" section
has the syntax; this is what to know when something misbehaves.

- **`DBCStructure.h:1843` is wrong.** The comment `0=blood, 1=frost, 2=unholy` on `SpellRuneCostEntry::RuneCost[3]`
  describes the wrong order: the array is indexed by `RuneType` (`RUNE_BLOOD` 0, `RUNE_UNHOLY` 1, `RUNE_FROST` 2,
  Player.h), so the DBC columns are `ID, Blood, Unholy, Frost, RunicPower`. Core files stay stock (merge-guard), so
  the trap is documented in `lib/dbcfmt.py`'s `SPELLRUNECOST` comment and in `spell_rune_cost()`'s docstring, not
  fixed. `RunicPower` is stored x10, and rune cost and RP gain only apply to a `PowerType` 5 spell.
- **`SpellRuneCost.dbc` is a client table too.** `SPELLRUNECOST` is deliberately not in `ALL_TABLES` /
  `SECONDARY_TABLES` (the SQL would go out twice, as for `SPELLCATEGORY`): the server half is the
  `spellrunecost_dbc` entry of `SPELL_TABLES`, the client half is `generate._spell_rune_cost_rows`, merged over
  `var/extractors/dbc/SpellRuneCost.dbc` into patch-Z. Both stock files (`SpellRuneCost.dbc`, `ChrClasses.dbc`) are
  copied from the worldserver's DBC directory (read-only `docker cp`); `var/` is gitignored.
- **The creation tables use the union reader.** `playercreateinfo_action` / `_cast_spell` / `_skills` are ordinary
  `SPELL_TABLES` entries read with `trainer_state.load_table_rows` (union of INSERTs). The three cases that looked
  like traps converge with it, so no `load_replayed_table_rows` switch was needed: a DK override of a stock key
  (later file wins in `SpellTableIndex`), a removal of a row a hand file already deleted (`load_removed_keys` only
  counts generated files, so the extra DELETE is emitted once and then recorded), and an undeclared key a hand
  `UPDATE` changed (never in `rows_to_emit` or the prune orphans). **Gotcha:** the reader does not replay a
  hand-written DELETE or UPDATE, so a declaration equal to a hand-deleted row's original INSERT reads as unchanged
  and is not re-emitted (`creation_cast(48266, 32, ...)`, `spell_threat(8056, ...)` render nothing while the DB has
  no row); change a value or re-add it by hand (`ReaderTrapTest.test_iv`). Not fixed: switching these tables to
  `load_replayed_table_rows` would also have to change `render_removal_blocks`' live keys, or removing a
  hand-deleted row (DK0a's 48266) prints a spurious "doesn't exist anywhere" WARNING.
  `playercreateinfo_cast_spell` has no primary key,
  so its key-exact DELETE removes every duplicate of (raceMask, classMask, spell). All three load once at boot and
  only affect new characters. `creation_skill` rejects `rank >= 16` (`MAX_SKILL_STEP`, the loader skips those rows).
- **`chrclasses_dbc` and `spellrunecost_dbc` have `prune_when_empty=True`**, like `disables`: with the breaker on,
  retiring the last `chr_class()` / `spell_rune_cost()` would leave the overlay row for good.
- **`override_skill_line_ability()` edits the stock row** (`dsl_live_data(skilllineability_stock_rows=...)`), so a
  dropped keyword restores the stock value; a row only a migration added falls back to the live row.
- **`chr_class()` replaces the whole row.** `chrclasses_dbc` has `ChrClassesEntryfmt` read for only four columns, but
  the overlay row carries all 60; the female / male / neutral names and `Filename` are `x` in the fmt yet are string
  offsets in the file, so they are in `read_as_string` (the `SPELLSHAPESHIFTFORM` lesson). The stock file's repacked
  string table is 10 bytes shorter than the original (shared strings): the server never reads this file back, and
  `lib/test_chr_class.py` checks the row-level round trip instead of the bytes.
- **`dsl_live_data` keywords.** `skilllineability_rows` and `chrclasses_rows` are keyword arguments defaulting to
  `None`, and either may be a zero-argument callable that `registry._require_live` calls on first use and caches in
  the bundle. Every older caller (`pull_dsl.py`, `potency_report.py`, `pull_talents.py --dsl`, the tests) is
  untouched; do not turn them into eager loads, the SkillLineAbility replay is about 13 s.
- **`--check` has an ERROR path for rune costs and a dry run for GCD haste.** `generate._rune_cost_errors` feeds
  both the full run's error list and `--check`'s `check_errors` (so it exits 1 for them).
  `_gcd_haste_check_warnings` runs the full run's computation over stock Spell / Talent / TalentTab /
  SkillLineAbility rows with the declared rows laid over them and prints WARNINGs only (promoted migrations are not
  replayed, so it cannot flip the exit code). It must pass the superseded-rank map the full run computes: with
  `superseded={}` the stock rows still list the collapsed ranks as learnable and the tree printed six Paladin /
  Hunter lines (a promoted-aware variant printed the same six). If it ever prints a line on the committed tree, fix
  the data or the policy; do not add an allow list.
- **`reservations:` holds non-class owners.** `healsim` reserves 202900-202909 so the overlap test catches a class
  slice that swallows the healing sim's spells (the T0 collision: DK's first block was 202900-203599). Reserve a new
  project's ids under its own name the same way.
- **`override_skill_line_ability()`** appends the entry `skill_line_ability()` would build (typed columns plus
  `raw_overrides` for the rest). `lib/superseded_ranks.py` treats it as a declared row (a "declared row wins"
  collision), and `resolve.resolve_rows` classifies it like any row outside the reserved block: edited when it
  differs from the live row, unchanged copy when it does not.

## Rogue T1: a SpellDuration with a minimum and a maximum, the rogue id slices and family-bit rules

Added for the Rogue rework (`.agents/plans/rogue-rework/`, T1; tooling only, no rogue content). The README's "Rogue T1"
section has the syntax.

- **`spell(duration_ms=4000, max_duration_ms=24000)`** mints or reuses a `SpellDuration` row whose `Duration` and
  `MaxDuration` differ (`ReuseContext.duration_index(duration_ms, max_duration_ms=None)`; the one-argument call is
  unchanged and still only finds `Duration == MaxDuration` rows). The core scales the aura between the two by the
  caster's combo points (`WorldObject::CalcSpellDuration`, Object.cpp:3377-3394: `min + (max - min) * cp / 5`, only
  for a caster with combo points, `min != -1` and `min != max`). The model raises for a max with no positive
  `duration_ms`, a max equal to (a no-op) or below the minimum, and a negative max. A stock row with the pair is
  reused (185 is 6000/21000), never duplicated.
- **Who reads `duration_ms` as the minimum.** The client's `$d` tooltip token shows `Duration` only, and the periodic
  tick count behind a potency `.total` tooltip (`lib/dsl/model.py`, `round(duration_ms / amplitude)`) uses it too. A
  spell with a range therefore shows its minimum-duration total; the stage that declares one (Rupture) owns the
  per-tick number and the tooltip wording. `lint.check_raw_override_typed_mismatch` compares `duration_ms` with the raw
  row's `Duration` column, which is the minimum, so it stays consistent. A declared max together with a raw
  `DurationIndex` override raises (the raw index is applied last and would win).
- **Combo points at aura creation.** `CalcSpellDuration` scales by whatever combo points the caster holds when the
  aura is created, finisher or not (it never checks `NeedsComboPoints`), and the finisher's points are only cleared
  in the finish phase (`Spell.cpp:4414`). A non-finisher with a ranged row scales by the points it finds and spends
  none; a helper triggered after the finisher consumed its points (an `AfterHit` script cast, a stored-bleed tick
  spell) sees 0 points and always gets the minimum. Put the range on the aura the finisher's own cast creates.
- **Pull stays lossless.** `reverse.py` diffs the rebuilt row against the real one and keeps any difference (a ranged
  `DurationIndex`) in `raw_overrides`.
- **`ROGUE_FAMILY_RULES`** (`SpellClassSet` 8) is in `FAMILY_BIT_RULES`, so both `--check` and the full run judge it:
  no custom (>= 200000) rogue-family spell may carry d0 b11 (Stealth's removal strips every family-8 aura on it), d0 b22
  (the Stealth hardcode drives the Master of Subtlety / Overkill tails) or d0 b25 (Hemorrhage's combo point and dagger
  bonus). The bits that depend on a spell's role are not expressible in the table; RG0 and the spec stages pin them with
  targeted tests: d0 b16 only on Deadly Poison, d0 b20 only on Rupture, d0 b17 only on a spell that should take the
  Eviscerate AP term, d0 b26 / d1 b18 on a new weapon strike, d1 b1 / b2 / b3, the DR bits d0 b3 / b10 / b24, the
  Preparation lists, d0 b0 while Throw shares it, and d1 b19 as the poison group.
- **Ids.** `reservations: rogue` has the PLAN s4 slices (spell 203700-204399 and so on; the P0 spike's 204370-204399,
  1295, 30838-30839 and 300368-300369 are never reused). `spellicon` is widened to 90499 and `spell_group` to 1399.
  `gameobjectdisplayinfo`, `summonproperties` and `spellcategory` are not reserved (not needed); the first stage that
  needs one adds its slice. `lib/test_id_blocks.py::scanned_used_ids` skips the `*_STOCK` constants in
  `patch_rogue_vfx_models.py` (they are stock ids below 90000) and a test pins every other rogue VFX constant to the
  rogue slices (spellvisual 90250-90299, soundentries 90121-90140). The spellvisual block filled up with the rogue;
  Warrior T1 widened it to 90399 (see "Warrior T1" below).

## Warrior T1: id blocks, family bits and the capstone test

Tooling for the warrior rework (`.agents/plans/warrior-rework/warrior-rework.T1-HANDOFF.md`), data-neutral: no declared
row changed, so there is nothing to generate or deploy.

- **Ids.** `reservations: warrior` has the PLAN s4 slices (spell 204400-204899 and so on). The P0 spike's 204869-204899
  (31 ids, not the 30 the PLAN first said), spell_group 1305 and creatures 300388-300389 are never reused; talents
  60488-60489 and SkillLineAbility 30868-30869 were reserved for it but never declared (also never reuse).
  `spellvisual` is widened to 90399 and `spellcategory` to 1319 (the warrior takes 90300-90339 and 1313-1319). The
  September Protection ids (spells 200028-200066 minus the mage's two, talents 60003-60006) are outside the reservation
  on purpose: `lib/test_id_blocks.py::WARRIOR_LEGACY` pins them exactly, so a new id outside the slices fails and a
  retired legacy id tells the stage to shrink the set. The spellcategory lint (`check_undeclared_spell_categories`) runs
  only in the full run, not `--check`: after touching the block call it directly on the declared population.
- **Family bits.** `source/classes/warrior/_masks.py` (append-only) and `lint.WARRIOR_FAMILY_RULES` (carriers banned on
  a custom family-4 spell: d0 b0 / b1 / b17 / b24, d1 b5 / b6, d2 b31; readers banned: d2 b31). The d0 b23 stance bit is
  not banned (the rage-keep block keys on icon 139 and A112 831, not the bit). Role bits are targeted tests of the
  warrior stages; the comment block above the rule row lists them with their causes.
- **Capstone tooltips.** `lib/test_capstone_format.py` (`rank_problems`, `load_class_talents`, `capstone_problems`,
  `EXPECTED_CAPSTONES`) and `source/classes/warrior/_tooltips.py::_desc`. Every spec stage lists its capstone talents by
  name (derived from the doc's Tooltip lines when it has no "Capstones" line) and adds them to `EXPECTED_CAPSTONES`. The
  checker is reusable: `capstone_problems("rogue", names)` works for any class whose package loads (druid and warlock
  need `SpellShapeshiftForm.dbc`). Adding a class key is enough: `ExpectedCapstonesTest` runs every key.

## Watch out: one client DBC, one patch archive

Six scripts each own a patch letter: `generate.py` → `patch-Z.mpq` (Spell/Talent/Item/…),
`build_patch_m.py` → `patch-M.mpq` (SpellVisual*/CreatureDisplayInfo/CreatureModelData/
GameObjectDisplayInfo/SoundEntries + `SPELLS/` models and `SOUND/` sounds), `build_patch_i.py` →
`patch-I.mpq` (`SpellIcon.dbc` + `Interface/Icons/*.blp`), `patch_gt_tables.py` → `patch-Y.mpq` (GT
tables), `build_patch_f.py` → `patch-F.mpq` (Bear/Cat Form model assets only — its
CreatureModelData/CreatureDisplayInfo rows, IDs 90100–90299, are written to the shared working copy
and ship in patch-M; see `docs/shapeshift-appearances.md`), `build_patch_w.py` → `patch-W.mpq`
(`WorldMapArea`/`DungeonMap`/`DungeonMapChunk` + `Interface/WorldMap/` tiles: the vanilla dungeon maps, see
below). The client loads lettered patches
alphabetically and the **highest letter wins per file**, so a DBC packed into two archives is silently served from
whichever has the later letter — usually a stale copy. That's exactly what blanked every custom
`SpellIcon` row minted after patch-M's last rebuild (patch-M was sweeping the shared
`var/model-visual-dbc/DBFilesClient/` dir wholesale; `docs/bugs-and-fixes.md`). `build_patch_m.py`
now has a `NOT_OURS` skip-set — extend it, don't remove it, if another script starts keeping its
working copy in that directory. Diagnostic when a client ignores a DBC row the plumbing says is
right: `for p in <patch-root>/Data/patch-*.mpq; do smpq -l $p | grep -i <table>.dbc; done`.

## Vanilla dungeon maps (`build_patch_w.py`)

The stock 3.3.5a client has no world map for any vanilla dungeon or raid. `build_patch_w.py` builds `patch-W.mpq`
with the Cataclysm-era maps the Ascension backup backported (rows from its `patch-M.MPQ`, tiles from its
`patch-A.MPQ`) for the 25 maps in `VANILLA_MAPS`. It is self-contained: it reads the stock client and the backup
directly, keeps no working copy, and is safe to rerun (same input, same archive). Client-only: the server's
`WorldMapArea.dbc` and `worldmaparea_dbc` stay stock.

- **Ids** (`source/ids.yaml`): WorldMapArea keeps the rows' own 680-766 (Sunken Temple 2021 → 687); DungeonMap
  floors are renumbered from 1000 and DungeonMapChunk rows from 10000, because Ascension's ids collide with stock.
- **Row order is kept.** Stock `DungeonMap.dbc` and `DungeonMapChunk.dbc` are not id-sorted; the merge keeps stock
  rows in file order and appends, and the build stops unless each stock file repacks byte for byte.
- **Floor switching** comes from `DungeonMapChunk`: each row ties a WMO group of the dungeon to a floor. Ascension's
  group ids match stock (`WMOAreaTable.dbc` knows all but a few Onyxia/BWL groups, Wailing Caverns' match the stock
  orphan rows).
- **Floor names**: none shipped. `WorldMapFrame.lua` reads `DUNGEON_FLOOR_<AREANAME><floor>` and falls back to
  "Level N"; names would go in a patch-X FrameXML file.
- `--preview DIR` writes one stitched PNG per floor for a look at the art without a client.

## Mined spell visuals and sounds (`patch_{mage,priest,druid}_vfx_models.py`)

These scripts sit outside `generate.py` and write rows straight into the working-copy DBCs in
`var/model-visual-dbc/DBFilesClient/`. `build_patch_m.py` then ships the rows. Each spell's DSL
source only points `SpellVisualID_1` at the minted `SpellVisual` row. The full mining procedure
and the custom ID ranges in use are in `docs/ascension-asset-mining.md` Part 3. Two traps:

- **A kit's `SoundID` must exist in our `SoundEntries.dbc`.** A sound ID copied from Ascension is
  silently ignored. Mint a row with `_sound_row()` (`patch_priest_vfx_models.py`) and put the
  `.wav` in `var/model-visual-dbc/SOUND/`.
- **A model needs all its textures.** Read the `.m2`'s texture table and ship every texture stock
  doesn't have, or the model renders as nothing.

After running one of these scripts, run `build_patch_m.py`. Also apply the `--sql-out` migration if
the script changed `SpellVisual`, which the server loads.

## Boss mechanics markers (M1)

`patch_bossmechanics_markers.py` makes the 1,332 telegraph displays (`CreatureModelData` +
`CreatureDisplayInfo` ids 91000-91833, 92000-92856 and 93000-93856, one pair per display; owner
`bossmechanics` reserves 91000-93999 in `apps/dbc-tools/source/ids.yaml`) that the
`mod-boss-mechanics` stalker wears: flat,
alpha-blended floor shapes a creature scales to any size with `SetDisplayId(display, scale)`. It is a
sibling of the `patch_*_vfx_models.py` scripts, kept under another name so `lib/test_id_blocks.py`'s
scan of those scripts stays as it is.

- **Two layers per telegraph** (telegraph-fill fix): an **outline** (rim 230 + interior 50, static,
  the full hitbox) and a **fill** (rim 230 + interior 90) the module grows into it over the warning.
- **Ids (colors fix, line-fill fix):** every shape in nine colors (`COLORS`: red, yellow, blue,
  purple, orange, green, teal, white, black = c 0-8), one 100-id block per color: id = 91000 + 100c
  + offset + step, offsets disc 0, ring 1, rim-only timer ring 2 (a donut's timer), fill donut 3+j,
  outline donut 10+j, fill cone 17+j, outline cone 25+j, dashed ring 33 (an armed mine; 34 per
  color, 91833 the last, +34..+99 spare). The line ladders have their own blocks: fill line 92000 +
  100c + i, outline line 93000 + 100c + i (i 0..56). Before the line-fill fix the lines sat at
  +33..+98 of the 91000 blocks; the block-wide DELETE / DBC merge clears those rows and round 3's
  line-direction probe 91996. `display_id()` and
  `mod-boss-mechanics/src/BossMechanicsIds.h` `MarkerDisplay()` compute the same numbers (both
  tested). The markers used 90500-90699 before; that slice is unreserved again, and the cleanup of
  it only deletes rows that are ours by name (`SPELLS\bm_*` models, `bm_*` textures), in the DBC
  merge and in the SQL.
- **Tinting, not per-color textures:** the textures are white; each model's M2Color track (color
  0, the one the skin batch's color index points at) holds the color, and the client multiplies the
  texture by it (the batch is unlit, render flag 0x01; blend mode 2 is `src * a + dst * (1 - a)`, so
  black is drawable: it darkens the floor). 36 textures serve all 1,332 displays. The source's color
  track has one key list (Stand) with interpolation none; markers only ever play Stand, so it is left
  at one list. RGB values: `COLOR_RGB` (blue brightened to 30, 140, 255 after the playtest).
- **Source model:** Ascension's `SPELLS\red_circle_filled.M2` + `00.skin`, a 4-vertex quad.
  `--extract <patch-N.MPQ>` runs `smpq -x` for them and the model's own texture into `--src` (default
  `var/bossmech-src/`), which must be new or empty. Run Python on that data with `-I`; scripts stay outside the directory.
- **Model patch (`lib/m2_patch.py`):** byte-level, nothing re-serialised. Vertices become a flat
  quad: x, y in [-8/7, 8/7], or a line model x in [-8k/7, 8k/7], y in [-4/7, 4/7], z = 0, the source's UVs
  kept. (m2_patch also takes eight vertices, two quads with their own UVs in an appended vertex array
  and a rebuilt skin; that was M1-FIX-LINE-FILL's line model, which drew only part of each line in
  game, so no display uses it since round 4b; it stays, tested.) `line_aspect`: k =
  2^((i-8)/4) for i 0..7, 1/4 to 0.84, and 2^((i-8)/8) for i 8..56, 1 to 64; longer lines are
  abutting pieces of aspect 64 plus one rounded-up rest. The extra 1/7 is the
  texture's transparent margin, so scale is still exactly radius / width in yards. Bounding box,
  sphere, animation bounds and skin submesh follow. Blend mode 4 (additive) becomes 2 (alpha); flags
  0x15 stay. The skin batch keeps its flags 0x14, which include 0x04, the **projected-texture** bit:
  Ascension's `red_circle_filled_noproject.M2` differs from the source only in that skin byte (0x10)
  and its quad height. Projection drapes the marker over sloped ground, so it stays on; its cost is
  the border rule under "Edge texels". Texture flags stay 0 (clamp in both directions; 0x1 / 0x2
  would wrap X / Y). The source
  fades in over 534 ms on Stand, out on Decay (159), and is half transparent, so the color alpha and
  transparency tracks are cut to one opaque key per animation (Hold, 158, has none and borrows it):
  a marker is fully drawn the moment it appears, whatever the warning time.
- **Texture binding: hard-coded path (type 0), one model copy per display.** The first build used
  one shared model per shape with a type-11 skin texture and `TextureVariation_1`, and drew **green
  boxes**: the source's replaceable-texture lookup (header 0x68) is `[0]`, so the client has no slot
  for skin type 11 and the texture stays empty. Stock creature models carry a lookup with entry 11
  (Skunk.m2: `[-1] * 11 + [0]`). `--skins` brings the shared layout back and appends that lookup;
  type 0 stays the default because it is how this model already worked in Ascension's client.
- **Textures (`lib/blp_write.py`):** generated, flat white with the shape in the alpha
  channel, **DXT5** BLP2 (compression 2, alpha depth 8, alpha type 7, full mip chain to 1x1, 2x2
  and 1x1 one padded block each): header, zeroed palette block and mip offsets are byte for byte
  those of Ascension's `red_circle_filled_editeda_circle_solid_red.blp` (tested). Disc, ring and
  timer ring 512 px, the rest 256 px. The color block is trivial (c0 = c1, indices 0); the alpha
  encoder tries both DXT5 modes per block. `--texture-format palette` keeps the first build's palette
  format (alpha depth 8). No Pillow in the venv, and the system Pillow's BLP writer has no alpha
  or mips, so tests decode with `read_blp` / `decode_dxt5`.
- **Projected textures need clear borders at every mip (hard rule).** The skin batch's 0x04 bit
  makes the client project the texture onto the ground triangles (terrain, WMO floor) around the
  model, and with clamp addressing every border texel repeats over all of that ground past the
  quad. So every border texel (both edge rows, both edge columns) of every marker texture must
  decode to exactly 0 at **every** mip level, down to 1 x 1. Two bugs came from breaking it: the
  first build's discs touched the texture edge at N/E/S/W and drew straight "lines at the
  cardinals"; and the line textures kept their last row (the far end) as body and drew a rimless,
  pointed strip several yards past the end of every line, its outline made of ADT triangle edges (45-degree
  diagonals, notches), its length set by the ground triangles, not the line
  (`dungeon-mechanics.M1-LINE-RENDER-FORENSICS.md`, probes 93990-93999). Every shape now stops 1/16
  of the side short of every edge (the geometry grows by 8/7 to compensate) and
  `encode_blp(clear_cols=True, clear_rows=True)` zeroes the edge texels at every level after
  filtering. `EdgeTexelTest` decodes all 36 shipped textures and enforces it.
- **Line layout (round 4b + the line-projection fix):** the client draws a creature model centred
  on its bounds (round-3 check L1: an off-centre x in [0, 8] model was drawn centred on the unit),
  so a line model stays symmetric about its origin: one quad x in [-k', k'], k' = 8k/7
  (`LINE_QUAD_K`), with the source quad's UVs (v grows with +X). The texture body is rows v in
  [1/2, 15/16) (`LINE_END`), with all four borders clear like every other shape, so the line runs
  exactly x in [0, k] x 1 (times scale = width), forward from the marker: v = 1/2 at x = 0 and
  v = 15/16 at x = 8k/7 x 7/8 = k. Both ends are texel edges, soft by half a texel of the active
  mip (0.02 yd for a 6 x 6 cell at mip 0). The width is unchanged (columns 1/16 in, y in
  [-4/7, 4/7]). The module needs no change: it places each piece's origin at its start and steps
  by `LineAspect(step) * width` (`MechanicMath.h`). Until the fix the quad was x in [-k, k] and the
  body ran to the last row, which projection smeared past the far end (probe 93999 confirmed the
  fix in game: 6 yd ahead, 0 behind, width 6, drapes over slopes). M1-FIX-LINE-FILL's two-quad
  model drew only the far end of each line; read again, that was the same smear (forensics 3.4).
  `LineVisibleRegionTest` maps the model UVs to world space and samples the decoded textures
  bilinearly at every step and mip: the visible region is exactly [0, k] x width.
- **Dashed ring (line-fill fix):** `dashed_alpha`, the outline rim (2.5% of the radius, alpha 230)
  cut into `DASH_COUNT` 20 dashes at 50% duty, one centred on +X, interior clear, 512 px; the
  module swaps an armed mine's outline to it and drops its fill.
- **Diagnostic displays 91990-91995**, only with `--diagnostics` (all red discs; view with
  `.morph target <id>` on yourself, `.modify scale <n>` to size, `.morph reset`): 91990 untouched
  source model + Ascension's own texture, 91991 our model + palette BLP, 91992 type 11 with the fixed
  lookup + DXT5, 91993 type 0 + DXT5 (= 91000), 91994 our model + Ascension texture, 91995 the first
  build's type 11 binding (expected green). They lived at 90620-90625, then 90690-90695.
- **Line-render probes 93990-93999**, only with `--probes` (red, `bm_probe_<id>` model, skin and
  texture each; client DBCs and files only, never in `--sql-out`, since `.morph` takes any display
  id): they split the line overshoot between texture, geometry and the projection bit. The table,
  the expected drawings and the in-game results (2026-11-03) are `PROBES` in the script; the
  checklist is in `dungeon-mechanics.M1-LINE-RENDER-FORENSICS.md`. Kept for future diagnosis: the
  default run builds none and removes any left in the working copy. `/console projectedTextures 0`
  did not stop the smear in game, so it is no way to test projection; use probe 93997 (batch flags
  0x10) instead.
- **Output:** model, skin and `.blp` files (all prefixed `bm_`) into `var/model-visual-dbc/SPELLS/`
  (1,332 models + 1,332 skins + 36 textures, 6.5 MB), the two DBCs merged in
  `var/model-visual-dbc/DBFilesClient/` (rows of 91000-93999 the run does not write, and our old rows
  in 90500-90699, are removed), and `--sql-out` writes the `creaturemodeldata_dbc` /
  `creaturedisplayinfo_dbc` rows as one pending file (`DELETE ... BETWEEN 90500 AND 90699 AND <ours by
  name>`, `DELETE ... BETWEEN 91000 AND 93999`, then the INSERTs). A rerun replaces its rows and drops stale
  `bm_` files (for example after switching `--skins`). Then run `build_patch_m.py` to pack them.
  `--var <dir>` points the whole thing at another working copy, and `--dry-run` writes nothing.
  Diagnostics 91990/91994 need the source texture in `--src`.
- **Server side:** the module sets display and scale before the marker enters the map (its own
  TempSummon create, not `Map::SummonCreature`), because the client blends every scale change in and
  a marker resized after its create packet visibly grew from 1 yd. The fill timer is that blend on
  purpose: the module resizes the fill every step, paced so its leading edge moves at most
  `BossMechanics.Telegraph.FillStepYd` (0.4 yd) per step, between 50 ms and
  `BossMechanics.Telegraph.FillStepMs` (round 4b: the blend is shorter than a 150 ms step, so a
  32 yd line fill stepped every 150 ms moved in visible jumps).
- **Tests:** `lib/test_bossmechanics_markers.py`. The M2 tests skip when `var/bossmech-src/` is
  missing; the real-file header comparison and diagnostic file checks also need the source texture.
  The Pillow header check needs the system `python3` (the venv has no Pillow).

## Load-bearing gotcha: `EffectSpellClassMask{A,B,C}_{1,2,3}`

Every other per-effect `spell_dbc` column uses `_1/_2/_3` as the **effect index**
(`EffectBasePoints_2` = Effect_2's base points). This one is the exception: the **letter** is the
effect index (A=Effect_1, B=Effect_2, C=Effect_3) and the **number** is which of that effect's 3
`SpellFamilyFlags` dwords holds the bit. Writing `EffectSpellClassMaskA_2` when you mean "scope
Effect_2's modifier" silently scopes Effect_1 instead and leaves Effect_2's real classmask
all-zero — which the engine reads as "matches every spell in the family," not "matches nothing."

This shipped for real twice in the Frost Mage rework — first Permafrost and Chilled to the Bone,
then (same day, after only documenting the gotcha) Empowered Frostbolt again, on a different
`SpellModOp` — see `docs/dbc-build-pipeline.md`'s "Bug 3" for both. Docs alone didn't stop the
recurrence, so `generate.py` now runs `lib/lint.py`'s `check_classmask_scoping` automatically after
every spell build and prints a `WARNING:` line for any hand-authored row where a SpellMod effect
that needs a classmask ends up with an all-zero one. **Don't ignore that warning** — it means an
`EffectSpellClassMask*` override is almost certainly on the wrong letter. If you're adding or
auditing one yourself, double-check the letter/number against `lib/dbcfmt.py`'s comment on the
`SPELL` table before trusting it. The lint exempts an effect only when its aura, misc value and the
row's nine `EffectSpellClassMask*` values equal the stock client `Spell.dbc` row (real Blizzard bytes).
A "pulled from existing data" note proves nothing: Improved Blizzard and Arcane Flows kept it after
hand edits, which hid two wildcard SpellMods until 2026-10-06. When you edit a pulled row, replace
the note with what you changed. The lint only sees rows `generate.py` emits (new or edited), not
unchanged reference copies.

## GCD-haste auras (melee-haste-gcd T1)

`source/gcd_haste.py` (policy) + `lib/gcd_haste.py` (applied on every `generate.py` run, call site next to the
superseded-ranks pass) emit one hidden passive per class family, `Haste: Global Cooldown`, whose FLAT
`SPELLMOD_GLOBAL_COOLDOWN` (aura 107, ms; the server ignores pct GCD mods) classmasks cover the 1.5s GCD spells the core's haste branch skips (DmgClass
MELEE/RANGED, `USES_RANGED_SLOT`, `IS_ABILITY`). Plan: `.agents/plans/melee-haste-gcd/`.

- Masks are computed from the merged spell data, never typed. Effect 0 = melee-haste mask (`EffectSpellClassMaskA_n`),
  effect 1 = ranged-haste mask (`..B_n`), effect 2 = PERIODIC_DUMMY. An empty mask is left as *no effect*: an
  all-zero classmask matches every spell in the family.
- A bit shared with a spell the core already hastes stops the run (`ERROR: gcd haste: ...`). Resolve it in
  `source/gcd_haste.py` with a reason: `EXCLUDE` (leave a live ability unhasted) or `NOT_CASTABLE` (a retired
  spell the data still lists as learnable; dropped from both sides).
- "Learnable" = SkillLineAbility row off the pet skill lines, rank of a non-pet-tab talent, or a DSL spell that
  `looks_player_castable` accepts *and* is not a pet spell; minus superseded ranks. The DSL carries stock pet
  spells as reference copies, so the heuristic alone would pull Hunter pet abilities in.
- The server rewrites some `SpellFamilyFlags` at load (`SpellInfoCorrections.cpp`); `SERVER_FLAG_FIXES`/
  `SERVER_FLAG_RULES` mirror them by hand and the check runs under both views. Re-check when that file changes.
  Only flag rewrites are mirrored: other corrections were checked and do not change candidacy (e.g. Shattering
  Throw 64382 loses `IS_ABILITY` at load but stays a candidate, its DmgClass being MELEE).
- `NOT_CASTABLE` ids are left out of the check on the premise that no player can learn them. `generate.py`
  enforces it: a live `trainer_spell` row of a reachable trainer, or a `trained_by()` declaration, stops the run
  (`ERROR: gcd haste: ...`). A superseded rank that a reachable trainer still teaches (Swift Flight Form 40120)
  stays learnable, so it is covered like any other candidate. A stale `EXCLUDE` id prints a
  `WARNING: gcd haste: ...`.
- A new family aura ID comes from `FAMILY_AURA_IDS` (201560-201566 in use); a family with bits and no ID errors.
- A new aura is a *new* spell in the reserved block, so it does not appear in the "editing N existing spell(s)" line.
