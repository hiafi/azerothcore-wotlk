"""
Blackrock Spire build WP-B10: Pyroguard Emberseer (9816)
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B10; build spec
docs/dungeons/blackrock-spire-rework.md SP 2721-2789). WP-B10 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/BlackrockSpire/boss_pyroguard_emberseer_rework.cpp), SmartAI off, the build spec's normal health at 5 players
(9816 175k = HealthModifier 57.339 on the level 60 warrior class base 3,052, DamageModifier 3.5; the flex scaler
multiplies it at the pull), the immunity set 1973 (1972 + Fire school, section 7 #16), INSTANCE_BIND (flags_extra 1),
the stock DamageModifier (the live value is a mod-progression leftover; the boss WP states its own). Heroic health and
its overrides are WP-H's (source/world/dungeons/blackrock_spire.py). Wave 2: nothing is declared until BIND_WAVE_2
flips (_common.py).

TODO(WP-B10): spells in its slice (kSpellsEmberseer of BlackrockSpireRework.h), the boss-kit creatures named in the
header's BrsCreatures enum, the visual ids from ._visuals (WP-V-2). The SQL rev (data/sql/updates/pending_db_world/)
drops or edits the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import BIND_WAVE_2, IMMUNITY_EMBERSEER, boss_columns

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(9816, **boss_columns(
        'boss_pyroguard_emberseer_rework', 57.339, damage_modifier=3.5, CreatureImmunitiesId=IMMUNITY_EMBERSEER,
    ))
