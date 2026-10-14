"""
The three stock hunter pet talent tabs (409 Tenacity, 410 Ferocity, 411 Cunning) and their 63 talents
(20 on 409, 21 on 410, 22 on 411; Dash/Dive, Charge/Swoop and the two Mobility rows are separate rows), as
untouched reference copies of the live Talent.dbc / TalentTab.dbc rows.

generate.py treats all 66 rows as unchanged (no SQL, no patch delta) until someone edits one. H0-P owns every
edit to this file (hunter-rework PET.md section 7, X18; SHARED C7.1): the pet tree rework, `retire_talent()` calls
for removed pet talents (which must also delete the matching declaration here, one declaration per id), and
the values PET.md assigns. T1 only pulled them in so those edits start from a declared copy.

Pulled with `apps/dbc-tools/pull_talents.py --tab 409,410,411 --dsl` (rank ids stay bare ints in a plain
`talent(...)`, not `granted_by_talent`, which would add SkillLineAbility rows).
"""

from lib.dsl.registry import tab, talent


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


talent_2106 = talent(
    id=2106,
    tab_id=ferocity_410_tab.id,
    tier=2,
    column=0,
    rank_spell_ids=[61680, 61681, 52858],
)


talent_2107 = talent(
    id=2107,
    tab_id=ferocity_410_tab.id,
    tier=0,
    column=0,
    rank_spell_ids=[61682, 61683],
)


talent_2109 = talent(
    id=2109,
    tab_id=ferocity_410_tab.id,
    tier=0,
    column=1,
    rank_spell_ids=[61684],
    flags=1,
    raw_overrides={'CategoryMask_1': 42476576, 'CategoryMask_2': 201326592},
)


talent_2110 = talent(
    id=2110,
    tab_id=tenacity_409_tab.id,
    tier=2,
    column=0,
    rank_spell_ids=[61680, 61681, 52858],
)


talent_2111 = talent(
    id=2111,
    tab_id=ferocity_410_tab.id,
    tier=2,
    column=3,
    rank_spell_ids=[61685],
    flags=1,
    raw_overrides={'CategoryMask_1': 42476576, 'CategoryMask_2': 201326592},
)


talent_2112 = talent(
    id=2112,
    tab_id=ferocity_410_tab.id,
    tier=0,
    column=2,
    rank_spell_ids=[61686, 61687, 61688],
)


talent_2113 = talent(
    id=2113,
    tab_id=ferocity_410_tab.id,
    tier=0,
    column=3,
    rank_spell_ids=[61689, 61690],
)


talent_2114 = talent(
    id=2114,
    tab_id=tenacity_409_tab.id,
    tier=0,
    column=0,
    rank_spell_ids=[61682, 61683],
)


talent_2116 = talent(
    id=2116,
    tab_id=tenacity_409_tab.id,
    tier=0,
    column=2,
    rank_spell_ids=[61686, 61687, 61688],
)


talent_2117 = talent(
    id=2117,
    tab_id=tenacity_409_tab.id,
    tier=0,
    column=3,
    rank_spell_ids=[61689, 61690],
)


talent_2118 = talent(
    id=2118,
    tab_id=cunning_411_tab.id,
    tier=0,
    column=0,
    rank_spell_ids=[61682, 61683],
)


talent_2119 = talent(
    id=2119,
    tab_id=cunning_411_tab.id,
    tier=0,
    column=1,
    rank_spell_ids=[61684],
    flags=1,
    raw_overrides={'CategoryMask_1': 212992, 'CategoryMask_2': 2147483648},
)


talent_2120 = talent(
    id=2120,
    tab_id=cunning_411_tab.id,
    tier=0,
    column=2,
    rank_spell_ids=[61686, 61687, 61688],
)


talent_2121 = talent(
    id=2121,
    tab_id=cunning_411_tab.id,
    tier=0,
    column=3,
    rank_spell_ids=[61689, 61690],
)


talent_2122 = talent(
    id=2122,
    tab_id=tenacity_409_tab.id,
    tier=1,
    column=3,
    rank_spell_ids=[53175, 53176],
    depends_on={'talent_id': 2117, 'rank': 1},
)


talent_2123 = talent(
    id=2123,
    tab_id=tenacity_409_tab.id,
    tier=2,
    column=1,
    rank_spell_ids=[53178, 53179],
)


talent_2124 = talent(
    id=2124,
    tab_id=ferocity_410_tab.id,
    tier=1,
    column=0,
    rank_spell_ids=[53180, 53181],
)


talent_2125 = talent(
    id=2125,
    tab_id=ferocity_410_tab.id,
    tier=1,
    column=2,
    rank_spell_ids=[53182, 53183, 53184],
)


talent_2126 = talent(
    id=2126,
    tab_id=tenacity_409_tab.id,
    tier=1,
    column=0,
    rank_spell_ids=[53182, 53183, 53184],
)


talent_2127 = talent(
    id=2127,
    tab_id=cunning_411_tab.id,
    tier=1,
    column=3,
    rank_spell_ids=[53182, 53183, 53184],
    depends_on={'talent_id': 0, 'rank': 2},
)


talent_2128 = talent(
    id=2128,
    tab_id=ferocity_410_tab.id,
    tier=1,
    column=1,
    rank_spell_ids=[53186, 53187],
)


talent_2129 = talent(
    id=2129,
    tab_id=ferocity_410_tab.id,
    tier=3,
    column=2,
    rank_spell_ids=[53203, 53204, 53205],
    depends_on={'talent_id': 0, 'rank': 2},
)


talent_2151 = talent(
    id=2151,
    tab_id=ferocity_410_tab.id,
    tier=1,
    column=3,
    rank_spell_ids=[19596],
)


talent_2152 = talent(
    id=2152,
    tab_id=ferocity_410_tab.id,
    tier=2,
    column=2,
    rank_spell_ids=[53409, 53411],
    depends_on={'talent_id': 0, 'rank': 2},
)


talent_2153 = talent(
    id=2153,
    tab_id=ferocity_410_tab.id,
    tier=4,
    column=1,
    rank_spell_ids=[53426],
    depends_on={'talent_id': 2156, 'rank': 0},
    flags=1,
)


talent_2154 = talent(
    id=2154,
    tab_id=ferocity_410_tab.id,
    tier=3,
    column=3,
    rank_spell_ids=[53427, 53429, 53430],
)


talent_2155 = talent(
    id=2155,
    tab_id=ferocity_410_tab.id,
    tier=4,
    column=0,
    rank_spell_ids=[53401],
    flags=1,
)


talent_2156 = talent(
    id=2156,
    tab_id=ferocity_410_tab.id,
    tier=3,
    column=1,
    rank_spell_ids=[55709],
    depends_on={'talent_id': 2128, 'rank': 1},
    flags=1,
)


talent_2157 = talent(
    id=2157,
    tab_id=ferocity_410_tab.id,
    tier=4,
    column=2,
    rank_spell_ids=[53434],
    depends_on={'talent_id': 2129, 'rank': 2},
    flags=1,
)


talent_2160 = talent(
    id=2160,
    tab_id=tenacity_409_tab.id,
    tier=1,
    column=1,
    rank_spell_ids=[19596],
)


talent_2161 = talent(
    id=2161,
    tab_id=tenacity_409_tab.id,
    tier=3,
    column=3,
    rank_spell_ids=[53427, 53429, 53430],
    depends_on={'talent_id': 0, 'rank': 2},
)


talent_2162 = talent(
    id=2162,
    tab_id=tenacity_409_tab.id,
    tier=2,
    column=2,
    rank_spell_ids=[53409, 53411],
)


talent_2163 = talent(
    id=2163,
    tab_id=tenacity_409_tab.id,
    tier=3,
    column=2,
    rank_spell_ids=[53450, 53451],
)


talent_2165 = talent(
    id=2165,
    tab_id=cunning_411_tab.id,
    tier=1,
    column=0,
    rank_spell_ids=[19596],
)


talent_2166 = talent(
    id=2166,
    tab_id=cunning_411_tab.id,
    tier=2,
    column=0,
    rank_spell_ids=[61680, 61681, 52858],
)


talent_2167 = talent(
    id=2167,
    tab_id=cunning_411_tab.id,
    tier=2,
    column=1,
    rank_spell_ids=[53409, 53411],
)


talent_2168 = talent(
    id=2168,
    tab_id=cunning_411_tab.id,
    tier=3,
    column=1,
    rank_spell_ids=[53427, 53429, 53430],
)


talent_2169 = talent(
    id=2169,
    tab_id=tenacity_409_tab.id,
    tier=4,
    column=3,
    rank_spell_ids=[53476],
    flags=1,
)


talent_2170 = talent(
    id=2170,
    tab_id=tenacity_409_tab.id,
    tier=4,
    column=1,
    rank_spell_ids=[53477],
    depends_on={'talent_id': 2123, 'rank': 1},
    flags=1,
)


talent_2171 = talent(
    id=2171,
    tab_id=tenacity_409_tab.id,
    tier=4,
    column=0,
    rank_spell_ids=[53478],
    flags=1,
)


talent_2172 = talent(
    id=2172,
    tab_id=tenacity_409_tab.id,
    tier=4,
    column=2,
    rank_spell_ids=[53480],
    depends_on={'talent_id': 2163, 'rank': 1},
    flags=1,
)


talent_2173 = talent(
    id=2173,
    tab_id=tenacity_409_tab.id,
    tier=1,
    column=2,
    rank_spell_ids=[53481, 53482],
    depends_on={'talent_id': 2116, 'rank': 2},
)


talent_2175 = talent(
    id=2175,
    tab_id=cunning_411_tab.id,
    tier=4,
    column=2,
    rank_spell_ids=[53490],
    depends_on={'talent_id': 2177, 'rank': 1},
    flags=1,
)


talent_2177 = talent(
    id=2177,
    tab_id=cunning_411_tab.id,
    tier=3,
    column=2,
    rank_spell_ids=[52234, 53497],
)


talent_2181 = talent(
    id=2181,
    tab_id=cunning_411_tab.id,
    tier=4,
    column=0,
    rank_spell_ids=[53508],
    flags=1,
)


talent_2182 = talent(
    id=2182,
    tab_id=cunning_411_tab.id,
    tier=1,
    column=2,
    rank_spell_ids=[53514, 53516],
)


talent_2183 = talent(
    id=2183,
    tab_id=cunning_411_tab.id,
    tier=3,
    column=3,
    rank_spell_ids=[53511, 53512],
    depends_on={'talent_id': 2127, 'rank': 2},
)


talent_2184 = talent(
    id=2184,
    tab_id=cunning_411_tab.id,
    tier=4,
    column=1,
    rank_spell_ids=[53517],
    depends_on={'talent_id': 0, 'rank': 1},
    flags=1,
)


talent_2201 = talent(
    id=2201,
    tab_id=cunning_411_tab.id,
    tier=0,
    column=1,
    rank_spell_ids=[23145],
    flags=1,
    raw_overrides={'CategoryMask_1': 21238021},
)


talent_2203 = talent(
    id=2203,
    tab_id=ferocity_410_tab.id,
    tier=0,
    column=1,
    rank_spell_ids=[23145],
    flags=1,
    raw_overrides={'CategoryMask_1': 2064, 'CategoryMask_2': 268435456},
)


talent_2206 = talent(
    id=2206,
    tab_id=cunning_411_tab.id,
    tier=2,
    column=2,
    rank_spell_ids=[54044],
    flags=1,
)


talent_2207 = talent(
    id=2207,
    tab_id=cunning_411_tab.id,
    tier=1,
    column=1,
    rank_spell_ids=[53483, 53485],
    depends_on={'talent_id': 2119, 'rank': 0},
    raw_overrides={'CategoryMask_1': 212992, 'CategoryMask_2': 2147483648},
)


talent_2208 = talent(
    id=2208,
    tab_id=cunning_411_tab.id,
    tier=1,
    column=1,
    rank_spell_ids=[53554, 53555],
    depends_on={'talent_id': 2201, 'rank': 0},
    raw_overrides={'CategoryMask_1': 21238021},
)


talent_2219 = talent(
    id=2219,
    tab_id=ferocity_410_tab.id,
    tier=2,
    column=3,
    rank_spell_ids=[52825],
    flags=1,
    raw_overrides={'CategoryMask_1': 2064, 'CategoryMask_2': 268435456},
)


talent_2237 = talent(
    id=2237,
    tab_id=tenacity_409_tab.id,
    tier=0,
    column=1,
    rank_spell_ids=[61685],
    flags=1,
    raw_overrides={'CategoryMask_1': 3179210, 'CategoryMask_2': 1610612736},
)


talent_2253 = talent(
    id=2253,
    tab_id=ferocity_410_tab.id,
    tier=5,
    column=2,
    rank_spell_ids=[62758, 62762],
    depends_on={'talent_id': 2157, 'rank': 0},
)


talent_2254 = talent(
    id=2254,
    tab_id=ferocity_410_tab.id,
    tier=5,
    column=0,
    rank_spell_ids=[62759, 62760],
)


talent_2255 = talent(
    id=2255,
    tab_id=tenacity_409_tab.id,
    tier=5,
    column=2,
    rank_spell_ids=[62758, 62762],
    depends_on={'talent_id': 2172, 'rank': 0},
)


talent_2256 = talent(
    id=2256,
    tab_id=cunning_411_tab.id,
    tier=5,
    column=0,
    rank_spell_ids=[62758, 62762],
    depends_on={'talent_id': 2181, 'rank': 0},
)


talent_2257 = talent(
    id=2257,
    tab_id=cunning_411_tab.id,
    tier=4,
    column=3,
    rank_spell_ids=[53450, 53451],
)


talent_2258 = talent(
    id=2258,
    tab_id=tenacity_409_tab.id,
    tier=5,
    column=1,
    rank_spell_ids=[62764, 62765],
)


talent_2277 = talent(
    id=2277,
    tab_id=tenacity_409_tab.id,
    tier=2,
    column=3,
    rank_spell_ids=[63900],
    flags=1,
)


talent_2278 = talent(
    id=2278,
    tab_id=cunning_411_tab.id,
    tier=5,
    column=3,
    rank_spell_ids=[53480],
    depends_on={'talent_id': 2257, 'rank': 1},
    flags=1,
)
