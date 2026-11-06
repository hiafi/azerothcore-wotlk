"""Trainer price policy, applied by `lib/trainer_pricing.py` on every `generate.py` run.

Class trainers (`PRICED_TRAINER_IDS`): the price of a trainer spell is a function of its learn
level (`ReqLevel`) alone. Nothing is read from the old price, so the pass is idempotent and
retunable: edit a number here and regenerate.

Every other stock trainer (`DISCOUNTED_TRAINER_IDS`): `STOCK_TRAINER_PRICE_FACTOR` of the
hand-written price (base dump, hand-written migrations, module SQL; a price that is exactly the
discount of the one before it is the discount, not a new price, so it never compounds). A price a
`trained_by(..., money_cost=X)` declares is final and never discounted.
"""

# `(ReqLevel, copper)` anchors. Between two anchors the price is interpolated linearly in integer
# math and rounded half up to 1c below 100c, 10c from 100c to 9999c, and 1s (100c) from 1g up.
# Below the first anchor the first price applies, above the last the last one. Levels must be
# strictly increasing and prices non-decreasing and positive (checked on load).
PRICE_CURVE = (
    (1, 10), (3, 10), (4, 20), (6, 40), (8, 60), (10, 100), (12, 160), (14, 240), (16, 360),
    (18, 400), (20, 440), (22, 700), (24, 800), (25, 1200), (30, 3200), (35, 4600), (40, 6000),
    (45, 7500), (50, 12000), (55, 17000), (60, 22000), (65, 26000), (70, 50000), (75, 100000),
    (80, 144000),
)

# Trainers the pass prices: 13 is the Death Knight trainer, 18-30 the mage portal/teleport
# trainers, 200-217 the class trainers of the trainer snapshot. An allow-list on purpose: a stock
# trainer that later gets an NPC wired to it must not be repriced silently. A listed trainer with
# no live, spawned NPC (`TrainerIndex.trainer_problems()`) is skipped with a WARNING.
PRICED_TRAINER_IDS = (13, *range(18, 31), *range(200, 218))

# SpellId -> fixed copper price on every priced trainer, winning over the curve. For a spell that
# should cost something other than its level's price. Empty for now.
PRICE_OVERRIDES: dict[int, int] = {}

# Stock-trainer discount (user ruling 2026-11-05): replaces the one-off
# `UPDATE trainer_spell SET MoneyCost = MoneyCost * 0.2` that ran live on 2026-08-22 from the
# never-merged `init-server` branch (535ff98c0), so rows written after it (upstream Engineering
# recipes, later class rows) get the same discount and a rebuilt DB has it. A decimal string,
# applied with MySQL's rounding (half away from zero).
STOCK_TRAINER_PRICE_FACTOR = "0.2"

# Factors used before STOCK_TRAINER_PRICE_FACTOR. When you change the factor, add the old one here:
# a price that is exactly an old factor's discount of the price before it is then still read as a
# discount (generated output), not as a new hand-written price to discount again.
PREVIOUS_STOCK_TRAINER_PRICE_FACTORS: tuple[str, ...] = ()

# Every stock trainer id outside PRICED_TRAINER_IDS: today's (data/sql/base/db_world/trainer.sql,
# 1-126: class 1-12, 14-17 and 31-34 with no spawned NPC, riding 35-46, profession 47-124, pet
# 125-126) and any upstream adds later, up to 199 (user ruling 2026-11-06: hand-written and upstream
# prices are discounted automatically). 200 and up is this server's own trainer range (the class
# trainers 200-217 of the trainer snapshot), never discounted by accident.
DISCOUNTED_TRAINER_IDS = (*range(1, 13), *range(14, 18), *range(31, 200))

# Spells whose price is hand-set and must not be discounted: Apprentice / Journeyman Riding
# (1g / 100g, data/sql/updates/db_world/2026_09_06_00.sql) and Expert Riding (800g, mod-progression
# phase 0). Excluded by spell, not by riding trainer, because Artisan Riding 34091 and Cold Weather
# Flying 54197 on trainers 35/36 are already at 1/5 live.
DISCOUNT_EXCLUDED_SPELL_IDS = (33388, 33391, 34090)
