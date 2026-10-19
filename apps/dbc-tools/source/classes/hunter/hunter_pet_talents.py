"""
The three hunter pet talent tabs (409 Tenacity, 410 Ferocity, 411 Cunning) and their reworked tree
(hunter-rework PET.md section 7, SHARED C7.1): 11 talents per tab at identical (tier, column) positions,
26 points each, no prerequisites, Flags 0 and CategoryMask 0.

  (tier, column)  talent               ranks
  (0,0) Great Stamina        3    (0,1) Natural Armor   2    (0,2) Spider's Bite   3
  (1,0) Blood of the Rhino   2    (1,1) Pet Barding     2    (1,2) Boar's Speed    3
  (2,0) Lionhearted          2    (2,1) Great Resistance 3
  (3,0) Grace of the Mantis  2    (3,1) Mobility        2
  (4,0) Bloodthirsty         2

33 stock rows are kept (22 move cells, 11 are repurposed from cut stock rows, PET 7.2); the other 30 stock
rows are declared only through `retire_talent()` (PET 7.3), which moves them to the holding tab and clears
their ranks. One declaration per id: a retired id is never also a `talent()`. The repurposed ids avoid
mod-playerbots' Dash/Dive filter ids (2109, 2111, 2119, 2201, 2203, 2207, 2208, 2219; 2207 is kept as
Cunning Mobility with its CategoryMask cleared).

Rank ids are bare ints in a plain `talent(...)`, not `granted_by_talent`, which would add SkillLineAbility
rows. The rank spells themselves are edited in hunter_pet.py.
"""

from lib.dsl.registry import retire_talent, tab, talent


tenacity_409_tab = tab(
    id=409,
    name='Tenacity',
    pet_talent_mask=2,
    spell_icon_id=1559,
    raw_overrides={'Name_Lang_Mask': 16712190, 'BackgroundFile': 'HunterPetTenacity'},
)


ferocity_410_tab = tab(
    id=410,
    name='Ferocity',
    pet_talent_mask=1,
    spell_icon_id=496,
    raw_overrides={'Name_Lang_Mask': 16712190, 'BackgroundFile': 'HunterPetFerocity'},
)


cunning_411_tab = tab(
    id=411,
    name='Cunning',
    pet_talent_mask=4,
    spell_icon_id=2223,
    raw_overrides={'Name_Lang_Mask': 16712190, 'BackgroundFile': 'HunterPetCunning'},
)



# Mob
talent_2106 = talent(
    id=2106,
    tab_id=ferocity_410_tab.id,
    tier=3,
    column=1,
    rank_spell_ids=[53483, 53485],
)


# BotR
talent_2107 = talent(
    id=2107,
    tab_id=ferocity_410_tab.id,
    tier=1,
    column=0,
    rank_spell_ids=[53481, 53482],
)


# GS
talent_2112 = talent(
    id=2112,
    tab_id=ferocity_410_tab.id,
    tier=0,
    column=0,
    rank_spell_ids=[61686, 61687, 61688],
)


# NA
talent_2113 = talent(
    id=2113,
    tab_id=ferocity_410_tab.id,
    tier=0,
    column=1,
    rank_spell_ids=[61689, 61690],
)


# SB
talent_2114 = talent(
    id=2114,
    tab_id=tenacity_409_tab.id,
    tier=0,
    column=2,
    rank_spell_ids=[53203, 53204, 53205],
)


# GS
talent_2116 = talent(
    id=2116,
    tab_id=tenacity_409_tab.id,
    tier=0,
    column=0,
    rank_spell_ids=[61686, 61687, 61688],
)


# NA
talent_2117 = talent(
    id=2117,
    tab_id=tenacity_409_tab.id,
    tier=0,
    column=1,
    rank_spell_ids=[61689, 61690],
)


# SB
talent_2118 = talent(
    id=2118,
    tab_id=cunning_411_tab.id,
    tier=0,
    column=2,
    rank_spell_ids=[53203, 53204, 53205],
)


# GS
talent_2120 = talent(
    id=2120,
    tab_id=cunning_411_tab.id,
    tier=0,
    column=0,
    rank_spell_ids=[61686, 61687, 61688],
)


# NA
talent_2121 = talent(
    id=2121,
    tab_id=cunning_411_tab.id,
    tier=0,
    column=1,
    rank_spell_ids=[61689, 61690],
)


# PB
talent_2122 = talent(
    id=2122,
    tab_id=tenacity_409_tab.id,
    tier=1,
    column=1,
    rank_spell_ids=[53175, 53176],
)


# PB
talent_2124 = talent(
    id=2124,
    tab_id=ferocity_410_tab.id,
    tier=1,
    column=1,
    rank_spell_ids=[53175, 53176],
)


# GotM
talent_2125 = talent(
    id=2125,
    tab_id=ferocity_410_tab.id,
    tier=3,
    column=0,
    rank_spell_ids=[53450, 53451],
)


# BT
talent_2126 = talent(
    id=2126,
    tab_id=tenacity_409_tab.id,
    tier=4,
    column=0,
    rank_spell_ids=[53186, 53187],
)


# PB
talent_2127 = talent(
    id=2127,
    tab_id=cunning_411_tab.id,
    tier=1,
    column=1,
    rank_spell_ids=[53175, 53176],
)


# BT
talent_2128 = talent(
    id=2128,
    tab_id=ferocity_410_tab.id,
    tier=4,
    column=0,
    rank_spell_ids=[53186, 53187],
)


# SB
talent_2129 = talent(
    id=2129,
    tab_id=ferocity_410_tab.id,
    tier=0,
    column=2,
    rank_spell_ids=[53203, 53204, 53205],
)


# BS
talent_2151 = talent(
    id=2151,
    tab_id=ferocity_410_tab.id,
    tier=1,
    column=2,
    rank_spell_ids=[19596, 201750, 201751],
)


# LH
talent_2152 = talent(
    id=2152,
    tab_id=ferocity_410_tab.id,
    tier=2,
    column=0,
    rank_spell_ids=[53409, 53411],
)


# GR
talent_2154 = talent(
    id=2154,
    tab_id=ferocity_410_tab.id,
    tier=2,
    column=1,
    rank_spell_ids=[53427, 53429, 53430],
)


# BS
talent_2160 = talent(
    id=2160,
    tab_id=tenacity_409_tab.id,
    tier=1,
    column=2,
    rank_spell_ids=[19596, 201750, 201751],
)


# GR
talent_2161 = talent(
    id=2161,
    tab_id=tenacity_409_tab.id,
    tier=2,
    column=1,
    rank_spell_ids=[53427, 53429, 53430],
)


# LH
talent_2162 = talent(
    id=2162,
    tab_id=tenacity_409_tab.id,
    tier=2,
    column=0,
    rank_spell_ids=[53409, 53411],
)


# GotM
talent_2163 = talent(
    id=2163,
    tab_id=tenacity_409_tab.id,
    tier=3,
    column=0,
    rank_spell_ids=[53450, 53451],
)


# BS
talent_2165 = talent(
    id=2165,
    tab_id=cunning_411_tab.id,
    tier=1,
    column=2,
    rank_spell_ids=[19596, 201750, 201751],
)


# BT
talent_2166 = talent(
    id=2166,
    tab_id=cunning_411_tab.id,
    tier=4,
    column=0,
    rank_spell_ids=[53186, 53187],
)


# LH
talent_2167 = talent(
    id=2167,
    tab_id=cunning_411_tab.id,
    tier=2,
    column=0,
    rank_spell_ids=[53409, 53411],
)


# GR
talent_2168 = talent(
    id=2168,
    tab_id=cunning_411_tab.id,
    tier=2,
    column=1,
    rank_spell_ids=[53427, 53429, 53430],
)


# BotR
talent_2173 = talent(
    id=2173,
    tab_id=tenacity_409_tab.id,
    tier=1,
    column=0,
    rank_spell_ids=[53481, 53482],
)


# BotR
talent_2182 = talent(
    id=2182,
    tab_id=cunning_411_tab.id,
    tier=1,
    column=0,
    rank_spell_ids=[53481, 53482],
)


# Mob
talent_2207 = talent(
    id=2207,
    tab_id=cunning_411_tab.id,
    tier=3,
    column=1,
    rank_spell_ids=[53483, 53485],
)


# Mob
talent_2237 = talent(
    id=2237,
    tab_id=tenacity_409_tab.id,
    tier=3,
    column=1,
    rank_spell_ids=[53483, 53485],
)


# GotM
talent_2257 = talent(
    id=2257,
    tab_id=cunning_411_tab.id,
    tier=3,
    column=0,
    rank_spell_ids=[53450, 53451],
)


# Retired stock rows (PET 7.3): moved to the holding tab 60800 with their ranks cleared.
retire_talent(2110)
retire_talent(2123)
retire_talent(2277)
retire_talent(2171)
retire_talent(2170)
retire_talent(2172)
retire_talent(2169)
retire_talent(2258)
retire_talent(2255)
retire_talent(2109)
retire_talent(2203)
retire_talent(2111)
retire_talent(2219)
retire_talent(2156)
retire_talent(2155)
retire_talent(2153)
retire_talent(2157)
retire_talent(2254)
retire_talent(2253)
retire_talent(2119)
retire_talent(2201)
retire_talent(2208)
retire_talent(2206)
retire_talent(2177)
retire_talent(2183)
retire_talent(2181)
retire_talent(2184)
retire_talent(2175)
retire_talent(2256)
retire_talent(2278)
