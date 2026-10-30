"""
Warrior W0a - trainer rows (trainers 200 = class trainer, 201 = starter), learn-level moves and removed spells.

W0a rows plus the W0b rows (Victory Rush, Intervene, Heroic Leap, Enraged Regeneration, Skull Banner; trainer 200 only).
Shattering Throw's linked 64380 gets no row.
"""

from lib.dsl.registry import trained_by, untrain
from .warrior_spells import (cleave_845, commanding_shout_469, heroic_throw_57755, pummel_6552, spell_reflection_23920,
                             shattering_throw_64382)

WARRIOR_TRAINER = 200
WARRIOR_STARTER_TRAINER = 201

# New trainer rows.
trained_by(commanding_shout_469, WARRIOR_TRAINER, req_level=22)
trained_by(spell_reflection_23920, WARRIOR_TRAINER, req_level=44)
trained_by(shattering_throw_64382, WARRIOR_TRAINER, req_level=52)
trained_by(heroic_throw_57755, WARRIOR_TRAINER, req_level=60)

# W0b rows (D17), trainer 200 only; the starter trainer 201 stays a 1-30 subset. Victory Rush and Intervene are stock /
# DSL-owned by bare id, Heroic Leap (204400) and Skull Banner (204405) are declared in warrior_shared.py.
trained_by(34428, WARRIOR_TRAINER, req_level=8)
trained_by(3411, WARRIOR_TRAINER, req_level=30)
trained_by(204400, WARRIOR_TRAINER, req_level=38)
trained_by(55694, WARRIOR_TRAINER, req_level=56)
trained_by(204405, WARRIOR_TRAINER, req_level=60)

# Learn-level moves (the declaration replaces the stock row). Dual Wield and Berserker Stance are referenced by bare
# id (stock / CSV-owned spells).
trained_by(674, WARRIOR_TRAINER, req_level=10)
trained_by(cleave_845, WARRIOR_TRAINER, req_level=14)
trained_by(pummel_6552, WARRIOR_TRAINER, req_level=16)
trained_by(2458, WARRIOR_TRAINER, req_level=16)
trained_by(2458, WARRIOR_STARTER_TRAINER, req_level=16)

# Retired: Mocking Blow, Retaliation, Intercept.
untrain(694, [WARRIOR_TRAINER])
untrain(20230, [WARRIOR_TRAINER])
untrain(20252, [WARRIOR_TRAINER, WARRIOR_STARTER_TRAINER])
