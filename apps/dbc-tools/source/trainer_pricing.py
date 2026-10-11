"""Class-trainer price policy: the price of a trainer spell is a function of its learn level
(`ReqLevel`) alone. `lib/trainer_pricing.py` applies it to every live trainer in
`PRICED_TRAINER_IDS` on every `generate.py` run. Nothing is read from the old price, so the pass
is idempotent and retunable: edit a number here and regenerate.
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
