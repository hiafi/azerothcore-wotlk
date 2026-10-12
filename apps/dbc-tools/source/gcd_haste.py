"""GCD-haste policy (`.agents/plans/melee-haste-gcd/melee-haste-gcd.PLAN.md`, stage T1).

Haste shortens a spell's 1.5s GCD in the core, but not a melee strike's, a ranged shot's or an
"ability"-flagged utility spell's. `lib/gcd_haste.py` finds those spells in the merged spell data on every
`generate.py` run and emits one hidden passive aura per class family whose SPELLMOD_GLOBAL_COOLDOWN
classmasks cover them. This file holds the human decisions; the masks are computed, never written here.
"""

# SpellFamilyName -> aura spell ID, allocated from `ids.yaml`'s `spell` block (200000-209999).
# 201560-201566 is a contiguous run above everything in use: the highest live custom spell is 201472 and
# the Paladin rework reserved up to 201559. One per family that ends up with GCD-haste bits. Priest (6),
# Rogue (8) and Mage (3) have none today (Dispersion is excluded below, Rogue's GCD is already 1.0s, Mage
# has no melee/ranged GCD abilities), so they get no ID; a family that gains bits later stops the run until
# it is given the next free ID here (201567+ is free).
FAMILY_AURA_IDS = {
    4: 201560,   # Warrior
    10: 201561,  # Paladin
    9: 201562,   # Hunter
    7: 201563,   # Druid
    11: 201564,  # Shaman
    15: 201565,  # Death Knight
    5: 201566,   # Warlock
}

# {spell_id: "reason"}: abilities deliberately left unhasted. Dropping a spell here also drops its bits
# from the mask, which is how a conflict (a bit shared with an ability the core already hastes) is resolved.
EXCLUDE: dict[int, str] = {
    13491: "Pummel monster-style copy (Warrior family, 10s, 100 mana) with no SkillLineAbility or trainer row; "
           "the player Pummel is a different spell. All-zero SpellClassMask, so no mod could target it anyway",
    59671: "Challenging Howl (Demonology skill line): all-zero SpellClassMask, so no spell mod can target it; "
           "stays on the full 1.5s",
    3674: "Black Arrow: shares Hunter bit 7 with the traps (Freezing/Immolation/Frost/Explosive/Snake Trap, "
          "Freezing Arrow), which the core already hastes; stays unhasted rather than double-dipping the traps",
    47585: "Dispersion: its only bit (Priest bit 74) is shared with ~20 spells the core already hastes "
           "(Power Word: Shield, Renew, Mind Flay, ...); stays on the full 1.5s",
}

# {spell_id: "reason"}: spells the data lists as player-learnable that no player can actually cast any more
# (ranks and spells a rework untrained). Dropped from BOTH sides of the check (not a candidate, and not a
# spell the core hastes), so a retired spell's bit neither widens the mask nor blocks the live spell that
# took it over.
NOT_CASTABLE: dict[int, str] = {
    53407: "Judgement of Justice: retired by the Paladin rework (untrained); its bit is shared with the new "
           "Judgement 201060, which the core already hastes",
    20271: "Judgement of Light: retired by the Paladin rework (untrained, script unbound), replaced by "
           "Judgement 201060",
    53408: "Judgement of Wisdom: retired by the Paladin rework (untrained, script unbound), replaced by "
           "Judgement 201060",
    20154: "Seal of Righteousness rank 2: superseded rank, retired by the Paladin rework (B1.1, script unbound)",
    53736: "Seal of Corruption: retired by the Paladin rework (B1.3, script unbound, spell row untouched)",
    19888: "Frost Resistance Aura: retired by the Prot rework (untrained, deleted from character_spell)",
    19891: "Fire Resistance Aura: retired by the Prot rework (untrained, deleted from character_spell)",
}

# Periodic-dummy amplitude (ms) of effect 2, the tick T2's AuraScript recomputes the haste amount on.
TICK_MS = 500

# Amount (percent) of the mod effects. This is a T1 TEST VALUE, so the Warrior aura can be `.learn`ed to
# check that the client honours a pct GCD mod on a melee ability. T2's CalcAmount hook overrides it at
# runtime, and T2 will set it back to 0.
PLACEHOLDER_PCT = -33

# Pet skill lines (CreatureFamily.dbc skillLine[0]/[1], all 40 families). A SkillLineAbility row on one is a
# pet ability: the pet casts it, and the player's spell mods never apply, so it is not a candidate.
PET_SKILL_LINES = (
    188, 189, 203, 204, 205, 207, 208, 209, 210, 211, 212, 213, 214, 215, 217, 218, 236, 251, 270,
    653, 654, 655, 656, 758, 761, 763, 764, 765, 766, 767, 768, 775, 780, 781, 782, 783, 784, 785,
    786, 787, 788,
)


# Only FLAG rewrites are mirrored here, because only SpellFamilyFlags move a spell mod's match. Other
# SpellInfoCorrections.cpp changes were checked and do not alter candidacy: Shattering Throw 64382 has
# IS_ABILITY stripped at load (:5088-5092), but it stays a Warrior candidate because its DmgClass is MELEE,
# which the core's haste branch skips regardless of the attribute.
#
# Spells whose SpellFamilyFlags `SpellInfoCorrections.cpp` rewrites at server load. The client keeps the
# Spell.dbc flags, so the two disagree for these; the generator takes both views into account. Mirrors the
# C++ by hand (we do not edit it): re-check this list when that file changes. Each value is the
# (dword 1, dword 2, dword 3) AFTER the rewrite, None meaning "left as in the DBC row".
SERVER_FLAG_FIXES = {
    # Ebon Plague (DK): SpellFamilyFlags[2] = 0x10                          (SpellInfoCorrections.cpp:356)
    51735: (None, None, 0x10), 51734: (None, None, 0x10), 51726: (None, None, 0x10),
    # Improved Devotion Aura / Improved Concentration Aura / Sanctified Retribution (Paladin): [0] = 0, [2] = ...
    63510: (0, None, 0x4000000),                                           # :491
    63514: (0, None, 0x2000000),                                           # :497
    63531: (0, None, 0x8000000),                                           # :503
    # flag96(...) assignments, which replace all three dwords
    59638: (0x20, 0, 0),         # Mirror Image Frostbolt (Mage)           :1142
    33778: (0, 0x10, 0),         # Lifebloom final bloom (Druid)           :1256
    31930: (0x200, 0, 0),        # Judgements of the Wise (Paladin)        :5230
}


def _server_flag_rule(row):
    """Rewrites that depend on the row's own flags, so they cannot be a plain table. Returns the corrected
    `(d0, d1, d2)` or None when the rule does not apply."""
    d0, d1, d2 = (int(row.get(f"SpellClassMask_{n}", 0)) & 0xFFFFFFFF for n in (1, 2, 3))
    # Icy Touch: FamilyFlags extended with the "unused" 0x40 for Sigil of the Frozen Conscience  (:5340)
    if int(row.get("SpellClassSet", 0)) == 15 and int(row.get("SpellIconID", 0)) == 2721 and d0 & 0x2:
        return (d0 | 0x40, d1, d2)
    return None


SERVER_FLAG_RULES = (_server_flag_rule,)
