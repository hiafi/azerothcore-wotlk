"""
Blackrock Depths build WP-IT: the use spells of the two event items that act on the world
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.3, s3.7, s7 #15). The items are
source/items/blackrock_depths_event_items.py (the table), source/items.csv (Item.dbc rows 70620-70623) and
data/sql/updates/pending_db_world/rev_event_items_blackrock_depths.sql (item_template). WP-IT owns this file.

The event items' slice of the `blackrock_depths` spell reservation is 211260-211269 (HANDOFF s3.3); this file takes
211260-211261, 211262-211269 are spare. The Vault Treasure Bag opens by its item flag (no spell).

  211260  Cinder of the Firelord  item 70621's use: a DUMMY on the user. Consumed on a successful cast
                                  (spellcharges -1); a refused cast (CheckCast) is never consumed. Scripted by
                                  spell_brd_cinder_of_the_firelord (the D12 Lord of the Lake WP).
  211261  Guzzler Rope            item 70622's use: a DUMMY on the user. Consumed on a successful cast. Scripted by
                                  spell_brd_guzzler_rope (the D10 Fineous WP).

Both are self-cast DUMMY spells with no cast time, no cooldown, no cost, no visual of their own (the toss and the rope's
unfurl are V-2 / boss WP visuals; the scripts cast their own). The script's CheckCast is what makes them work only where
the design says; the exact checks are the WP reports' (STAGE-IT-REPORT.md "Use-spell checks").
"""

from lib.dsl import RANGE_SELF, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT, TARGET_UNIT_CASTER, kit_raw
from lib.dsl.registry import scripted_by, spell

_ICON_FIRE = 12             # Burning Brand 29618 / Fire Blast 2136 (a fire glyph; the item's icon is the ember)
_ICON_ROPE = 1              # generic (no stock rope spell icon read)

cinder_211260 = spell(
    id=211260, name='Cinder of the Firelord', school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FIRE,
    notes='BRD IT, item 70621\'s use (HANDOFF s3.7 D12, s7 #15; S2 "Lord Incendius" Hard mode, rulings 81-84): a DUMMY '
          'on the user so nothing starts a fight before the script does. spell_brd_cinder_of_the_firelord (D12) '
          'checks in CheckCast and refuses with a notification and no consume: map 230 and the heroic difficulty; '
          'Lord Incendius (9017) alive, out of combat and not already in the hard mode; the caster out of combat; the '
          'caster within the causeway toss range of him (D12 picks the number and the spot list from the geometry '
          'ruling #14 = A). The success path (AfterCast / OnEffectHitTarget) sets the instance\'s `cinder used` flag '
          '(saved, never burnt by a wipe), arms the hard mode loot bit and starts his yell and rise. The item is '
          'consumed on the cast (spellcharges -1); the flag outlives it. Bots never use it (no strategy names item '
          '70621).',
    raw_overrides=kit_raw('Cast the Cinder into the lava at Lord Incendius\'s island. What sleeps there wakes angry.',
                          instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT),
)
scripted_by(cinder_211260, 'spell_brd_cinder_of_the_firelord')

rope_211261 = spell(
    id=211261, name='Guzzler Rope', school=School.NORMAL, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_ROPE,
    notes='BRD IT, item 70622\'s use (HANDOFF s3.3 D10; S2 "Fineous Darkvire", ruling 67, hub gap 31): a DUMMY on the '
          'user. spell_brd_guzzler_rope (D10) checks in CheckCast and refuses with a notification and no consume: map '
          '230; the caster within the climb spot\'s radius (893.5, -267.1, -71.9, behind Lord Incendius; D10 picks '
          'the radius from the navmesh); the rope not already hung (the instance\'s saved `rope hung` flag). The '
          'success path summons the hanging rope GO 301282 at the spot for the rest of the instance and saves the '
          'flag. Usable out of combat only is the script\'s call (a rope hung mid-fight is harmless); any player '
          'may use it, whoever looted it. The item is consumed on the cast.',
    raw_overrides=kit_raw('Hang the rope here. It must be tied off at the right spot, on the ledge behind Lord '
                          'Incendius.', instant=True, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT),
)
scripted_by(rope_211261, 'spell_brd_guzzler_rope')
