"""
Shaman - trainer rows, untrains and creature-spell clean-up for the shared rework (SH0a).

The first block removes the P0 spike's hand-written `creature_template_spell` rows (the spike files are gone;
creatures 300298 / 300299 stay inert). Later blocks (A5) add the trainer 210 rows and untrains.
"""

from lib.dsl.registry import remove_creature_spell, trained_by, untrain


remove_creature_spell(300298, 0)
remove_creature_spell(300299, 0)


# SH0a (A5): trainer 210 rows. Bare ids; race masks stay on the SkillLineAbility rows.
trained_by(2645, 210, 16)  # Ghost Wolf
trained_by(674, 210, 20)  # Dual Wield
trained_by(974, 210, 25)  # Earth Shield
trained_by(51514, 210, 28)  # Hex
trained_by(51886, 210, 36)  # Cleanse Spirit
trained_by(51505, 210, 42)  # Lava Burst
trained_by(2825, 210, 60)  # Bloodlust
trained_by(32182, 210, 60)  # Heroism

# Totem ranks / old totems folded into the new kit: no longer taught (H4: starter trainer 211 only loses 8071).
untrain(8071, [210, 211])
for _spell_id in (8075, 8227, 8181, 8184, 5675, 10595, 8512, 6495, 526, 66842, 66843, 66844):
    untrain(_spell_id, [210])
