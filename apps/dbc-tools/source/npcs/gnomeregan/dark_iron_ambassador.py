"""
Gnomeregan build WP-H (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.6, s7 #41 A): the Dark Iron
Ambassador (6228, ruling 5), the rare of the Alert hall's end, a level 28 elite paladin (class base health 732).

Normal: HealthModifier 57.4 (ceil(732 x 57.4) = 42,017, about 70% of a boss as built; the header's
`Health::kDarkIronAmbassador`, stock 5 = 3,660) and DamageModifier 3.0 (stock 7.5: his stock swings are a quarter of a
tank's health; as Zul'Farrak's rares). The heroic copy is source/world/dungeons/gnomeregan.py's override: 260,000 at
the rare tier's melee.

`creature_template_columns()` owns only these two columns of the stock row (never its name, flags, loot or SmartAI);
one call per entry, so a later WP that needs another column of 6228 (L-1's loot ids) asks for it here.
"""

from lib.dsl.registry import creature_template_columns

creature_template_columns(6228, HealthModifier=57.4, DamageModifier=3.0)
