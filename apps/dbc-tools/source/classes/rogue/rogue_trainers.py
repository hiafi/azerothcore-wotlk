"""
Rogue RG0a - trainer rows (trainer 206 only), the 2842 untrain, and the retired poison items.

The six poison auras are learned from the class trainer; the 29 stock poison items no longer grant a poison.
"""

from lib.dsl.registry import item_template, trained_by, untrain
from .rogue_shared import (anesthetic_poison_203706, crippling_poison_203704, deadly_poison_203702,
                           instant_poison_203701, mind_numbing_poison_203705, wound_poison_203703)
from .rogue_shared import (enforcer_stance_203720, insult_203722, shiv_203725, shroud_of_concealment_203724)

ROGUE_TRAINER = 206

trained_by(instant_poison_203701, ROGUE_TRAINER, req_level=20)
trained_by(crippling_poison_203704, ROGUE_TRAINER, req_level=20)
trained_by(mind_numbing_poison_203705, ROGUE_TRAINER, req_level=24)
trained_by(deadly_poison_203702, ROGUE_TRAINER, req_level=30)
trained_by(wound_poison_203703, ROGUE_TRAINER, req_level=32)
trained_by(anesthetic_poison_203706, ROGUE_TRAINER, req_level=40)
# Envenom, Cloak of Shadows, Tricks of the Trade: stock spells, referenced by id.
trained_by(32645, ROGUE_TRAINER, req_level=42)
trained_by(31224, ROGUE_TRAINER, req_level=46)
trained_by(57934, ROGUE_TRAINER, req_level=56)

# RG0b: Enforcer Stance, Insult, Ghostly Strike (stock 14278, talent retired), Fan of Knives (stock 51723), Shroud,
# stock 26679 (Deadly Throw), Shiv.
trained_by(enforcer_stance_203720, ROGUE_TRAINER, req_level=10)
trained_by(insult_203722, ROGUE_TRAINER, req_level=10)
trained_by(14278, ROGUE_TRAINER, req_level=10)
trained_by(51723, ROGUE_TRAINER, req_level=24)
trained_by(shroud_of_concealment_203724, ROGUE_TRAINER, req_level=28)
trained_by(26679, ROGUE_TRAINER, req_level=36)
trained_by(shiv_203725, ROGUE_TRAINER, req_level=50)

# Stock Poisons-skill grant is retired.
untrain(2842, [9, 10, 206, 207])

POISON_ITEMS = (
    6947, 6949, 6950, 8926, 8927, 8928, 21927, 43230, 43231,  # Instant
    2892, 2893, 8984, 8985, 20844, 22053, 22054, 43232, 43233,  # Deadly
    10918, 10920, 10921, 10922, 22055, 43234, 43235,  # Wound
    3775, 5237, 21835, 43237,  # Crippling, Mind-numbing, Anesthetic
)
for _entry in POISON_ITEMS:
    item_template(_entry, spellid_1=0, spellcharges_1=0,
                  description="No longer used: rogues learn their poisons from a trainer.")
