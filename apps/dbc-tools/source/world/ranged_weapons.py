"""
Every bow, gun and crossbow stops needing ammo (hunter-rework Q3, SHARED C7.3 step 5): `ammo_type` 0.

This is the client half of "no ammo". The paper-doll slot check reads `AmmoType` from the item query of the
equipped weapon and refuses to fire without a matching ammo item; the server never reads the column for
anything else (SHARED C2 grants the no-ammo aura for the server half). Item.dbc has no AmmoType field, so there
is no client patch, only the `item_template` UPDATE - and a one-time client `Cache` wipe at rollout, because the
client caches item queries.

Selected by `class` 2 and `subclass` 2 (Bow), 3 (Gun) or 18 (Crossbow) on the live rows, **never** by
`ammo_type` != 0: once the rows apply, that predicate would match nothing and the next run would report every
declaration as retired. Rows already at 0 (Thori'dal 34334, Centaur Longbow 5748, NPC and test weapons)
re-declare to an identical row and emit nothing. NPC-only weapons are included on purpose: `item_template` has no
reliable NPC-only marker, and the column is read only by a player's client, so the edit is inert for NPCs.
Thrown (16) and Wands (19) are out of scope.

The live rows come from the same overlay `item_template()` edits against (`live_item_templates()`), so a
weapon added by a later migration is picked up on the next run with no list to maintain.
"""

from lib.dsl.registry import item_template, live_item_templates

BOW, GUN, CROSSBOW = 2, 3, 18
ITEM_CLASS_WEAPON = 2

for _entry, _row in sorted(live_item_templates().items()):
    if _row["class"] == ITEM_CLASS_WEAPON and _row["subclass"] in (BOW, GUN, CROSSBOW):
        item_template(_entry, ammo_type=0)
