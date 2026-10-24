"""
Death Knight - trainer rows, skill-line-ability overrides, creation data and the trainer rename for the shared
rework (DK0a, A4). Spells are owned by the other DK files; here they are referenced by bare id.
"""

from lib.dsl.registry import (
    chr_class, creation_action, creature_template, override_skill_line_ability, remove_creation_action,
    remove_creation_cast, remove_creation_skill, trained_by, untrain,
)

DK_TRAINER = 13
DK_CLASS = 6
DK_CLASS_MASK = 32
PLAYABLE_RACES = (1, 2, 3, 4, 5, 6, 7, 8, 10, 11)

# Trainer 13 rows. Death Grip 49576 @16, Death Gate 50977 @10 and Path of Frost 3714 @40 already exist; their
# SpellLevel moves belong to the spell files.
trained_by(48266, DK_TRAINER, 10)  # Blood Presence (was @1)
trained_by(203001, DK_TRAINER, 12)  # Death's Caress
trained_by(48982, DK_TRAINER, 18)  # Rune Tap
trained_by(51052, DK_TRAINER, 52)  # Anti-Magic Zone
trained_by(49143, DK_TRAINER, 10)  # Frost Strike
trained_by(49039, DK_TRAINER, 20)  # Lichborne

# Folded into the new kit: Blood Strike, Frost Presence and Unholy Presence are no longer taught.
untrain(45902, [DK_TRAINER])  # Blood Strike
untrain(48263, [DK_TRAINER])  # Frost Presence
untrain(48265, [DK_TRAINER])  # Unholy Presence

# SkillLineAbility overrides (acquire 0 = no level-1 auto-learn; trainer-taught instead).
override_skill_line_ability(16616, acquire_method=0)  # Blood Strike (live had no override)
override_skill_line_ability(16231, acquire_method=0)  # Icy Touch
override_skill_line_ability(16433, acquire_method=0)  # Death Coil
override_skill_line_ability(17101, acquire_method=0)  # Death Grip
override_skill_line_ability(17016, acquire_method=0)  # Blood Presence
override_skill_line_ability(19184, acquire_method=0)  # Journeyman Riding
override_skill_line_ability(19182, acquire_method=2, class_mask=DK_CLASS_MASK)  # Heart Strike learns at level 1
override_skill_line_ability(16782, class_mask=DK_CLASS_MASK)  # Rune Tap
override_skill_line_ability(16928, class_mask=DK_CLASS_MASK)  # Frost Strike
override_skill_line_ability(17545, skill_line=772)  # Pestilence: Unholy spellbook tab (stock Blood; user 2026-10-24)
override_skill_line_ability(17761, skill_line=770)  # Death Strike: Blood spellbook tab (stock Unholy; user 2026-10-24)
override_skill_line_ability(19183, class_mask=DK_CLASS_MASK)  # Lichborne

# Creation data: action bar 1 Heart Strike, 2 Plague Strike; the old strike/presence buttons go.
for _race in PLAYABLE_RACES:
    creation_action(_race, DK_CLASS, 1, 55050)  # Heart Strike
    creation_action(_race, DK_CLASS, 2, 45462)  # Plague Strike
    for _button in (3, 4, 5):
        remove_creation_action(_race, DK_CLASS, _button)

remove_creation_cast(48266, DK_CLASS_MASK)  # no Blood Presence cast at creation
remove_creation_skill(129, DK_CLASS_MASK)  # no First Aid
chr_class(DK_CLASS, CinematicSequenceID=0)  # race intro cinematic instead of the DK class one

# U6: the trainer no longer runeforges (every other live column is kept by the helper).
creature_template(33251, "Death Knight Trainer")
