"""
Random Classic Heroic (lfg-classic-heroic, .agents/plans/lfg-classic-heroic/lfg-classic-heroic.PLAN.md): a Dungeon
Finder random queue for levels 60-62 over every vanilla dungeon with a heroic, and a "Classic Heroic" section under
Specific Dungeons listing each of them by name. lib/dsl/lfg.py has the helpers, lib/lfg_dungeons.py builds the rows.

A vanilla dungeon that gains a heroic (`heroic=heroic(...)` in source/world/dungeons/) joins the pool with one more
lfg_heroic() line per finder entry of its map (next free id from ids.yaml's `lfgdungeons` block). generate.py prints a
note for a heroic map whose finder entries have no line here.

The rewards (lfg_dungeon_rewards row, the two quests and the satchel's item_template and loot) are hand-written pending
world SQL; the satchel's Item.dbc row is source/items.csv 70700.

Shared file (no --scope owns it): only a full generate.py run writes these rows. A dungeon scope's heroic final boss
names its finder entry here, so a scoped run of that dungeon stops until a full run has shipped the entry.
"""

from lib.dsl.lfg import lfg_group, lfg_heroic, lfg_random

CLASSIC_HEROIC = 12

# The section lists right above Classic Dungeons: the client lists sections by OrderIndex (stock: Lich King Heroic 1,
# Lich King Normal 2, Burning Crusade Heroic 3, Burning Crusade Normal 4, Classic Dungeons 5, raids 17-21), so Classic
# Dungeons moves down to 6 and Classic Heroic takes 5.
lfg_group(CLASSIC_HEROIC, name="Classic Heroic", order_index=5, type_id=5)
lfg_group(1, order_index=6)  # Classic Dungeons

# Ruling 1: available at 60, gone at 63. Shaped like stock 260 Random Burning Crusade Heroic (Difficulty 1, Flags 3).
lfg_random(300, "Random Classic Heroic", group=CLASSIC_HEROIC, like=260, expansion=0, min_level=60, max_level=62)

# Ruling 2: every vanilla dungeon with a declared heroic. Stratholme (map 329) has two finder entries, one per wing.
lfg_heroic(301, normal=6, group=CLASSIC_HEROIC)  # Deadmines
lfg_heroic(302, normal=8, group=CLASSIC_HEROIC)  # Shadowfang Keep
lfg_heroic(303, normal=2, group=CLASSIC_HEROIC)  # Scholomance
lfg_heroic(304, normal=40, group=CLASSIC_HEROIC)  # Stratholme - Main Gate
lfg_heroic(305, normal=274, group=CLASSIC_HEROIC)  # Stratholme - Service Entrance
