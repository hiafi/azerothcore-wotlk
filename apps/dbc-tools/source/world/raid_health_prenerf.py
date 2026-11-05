"""
Pre-nerf TBC/WotLK raid health: dbc-tools owns `creature_template.HealthModifier` of the 244 raid creatures
mod-progression's phase 0 raised (progression-slim, user ruling: every TBC/WotLK raid boss and trash mob stays at its
pre-nerf health until its raid is reworked; nothing may revert it).

The values are the final ones phase 0 sets (apps/dbc-tools/replay/frozen/2026_09_02_mod_progression_phase_00/
phase_00-creature_template.sql) and equal the live DB, so the first run emits nothing. They are declared with
`creature_template_columns()`, which owns only this column of the stock row. If a later migration (an upstream merge,
a phase file) changes one of them, the replay sees the new value and the next generate.py run re-emits the declared
one as a column-limited UPDATE; to retire an entry deliberately (a raid rework), delete its line here and set the
new value in SQL.

Entries are the phase 0 HealthModifier edits whose live spawns are on a TBC/WotLK raid map (Karazhan, Gruul's Lair,
Magtheridon's Lair, Serpentshrine Cavern, The Eye, Hyjal Summit, Black Temple, Zul'Aman, Sunwell Plateau), grouped
by raid. Hellfire Channeler (17256) also spawns in the Blood Furnace; it is listed under Magtheridon's Lair.
"""

from lib.dsl.registry import creature_template_columns

RAID_HEALTH_PRENERF = {
    "Karazhan": (
        (15547, 9),  # Spectral Charger
        (15548, 9),  # Spectral Stallion
        (15551, 6),  # Spectral Stable Hand
        (15687, 51),  # Moroes <Tower Steward>
        (15688, 100),  # Terestian Illhoof
        (15689, 200),  # Netherspite
        (15690, 150),  # Prince Malchezaar
        (15691, 115),  # The Curator
        (16151, 50),  # Midnight
        (16171, 7),  # Coldmist Widow
        (16174, 8),  # Greater Shadowbat
        (16175, 6),  # Vampiric Shadowbat
        (16176, 6),  # Shadowbeast
        (16177, 7),  # Dreadbeast
        (16178, 4),  # Phase Hound
        (16389, 6),  # Spectral Apprentice
        (16406, 6),  # Phantom Attendant
        (16407, 6),  # Spectral Servant
        (16408, 9),  # Phantom Valet
        (16410, 8),  # Spectral Retainer
        (16411, 6),  # Spectral Chef
        (16412, 6),  # Ghostly Baker
        (16414, 8),  # Ghostly Steward
        (16415, 6),  # Skeletal Waiter
        (16424, 6),  # Spectral Sentry
        (16425, 6),  # Phantom Guardsman
        (16457, 70),  # Maiden of Virtue
        (16459, 8),  # Wanton Hostess
        (16460, 8),  # Night Mistress
        (16461, 8),  # Concubine
        (16470, 8),  # Ghostly Philanthropist
        (16471, 12),  # Skeletal Usher
        (16472, 9),  # Phantom Stagehand
        (16473, 8),  # Spectral Performer
        (16481, 10),  # Ghastly Haunt
        (16482, 10),  # Trapped Soul
        (16485, 12),  # Arcane Watchman
        (16489, 8),  # Chaotic Sentience
        (16504, 16),  # Arcane Protector
        (16524, 160),  # Shade of Aran
        (16525, 6),  # Spell Shade
        (16526, 8),  # Sorcerous Shade
        (16529, 8),  # Magical Horror
        (16530, 6),  # Mana Warp
        (16540, 6),  # Shadow Pillager
        (16544, 8),  # Ethereal Thief
        (16545, 10),  # Ethereal Spellfilcher
        (16595, 10),  # Fleshbeast
        (16596, 16),  # Greater Fleshbeast
        (17225, 175),  # Nightbane
    ),
    "Gruul's Lair": (
        (18831, 100),  # High King Maulgar <Lord of the Ogres>
        (18832, 50),  # Krosh Firehand
        (18834, 50),  # Olm the Summoner
        (18835, 50),  # Kiggler the Crazed
        (18836, 50),  # Blindeye the Seer
        (19044, 450),  # Gruul the Dragonkiller
        (19389, 40),  # Lair Brute
        (21350, 40),  # Gronn-Priest
    ),
    "Magtheridon's Lair": (
        (17256, 40),  # Hellfire Channeler
        (17257, 635),  # Magtheridon
        (18829, 32),  # Hellfire Warder
    ),
    "Serpentshrine Cavern": (
        (21212, 800),  # Lady Vashj <Coilfang Matron>
        (21213, 750),  # Morogrim Tidewalker
        (21214, 300),  # Fathom-Lord Karathress
        (21215, 500),  # Leotheras the Blind
        (21216, 450),  # Hydross the Unstable <Duke of Currents>
        (21218, 35),  # Vashj'ir Honor Guard
        (21220, 25),  # Coilfang Priestess
        (21221, 35),  # Coilfang Beast-Tamer
        (21224, 25),  # Tidewalker Depth-Seer
        (21225, 25),  # Tidewalker Warrior
        (21226, 25),  # Tidewalker Shaman
        (21227, 25),  # Tidewalker Harpooner
        (21228, 25),  # Tidewalker Hydromancer
        (21229, 25),  # Greyheart Tidecaller
        (21230, 25),  # Greyheart Nether-Mage
        (21231, 25),  # Greyheart Shield-Bearer
        (21232, 25),  # Greyheart Skulker
        (21246, 15),  # Serpentshrine Sporebat
        (21251, 75),  # Underbog Colossus
        (21298, 25),  # Coilfang Serpentguard
        (21299, 25),  # Coilfang Fathom-Witch
        (21301, 25),  # Coilfang Shatterer
        (21339, 25),  # Coilfang Hate-Screamer
        (21806, 20),  # Greyheart Spellbinder
        (21863, 15),  # Serpentshrine Lurker
        (21964, 150),  # Fathom-Guard Caribdis
        (21965, 150),  # Fathom-Guard Tidalvess
        (21966, 150),  # Fathom-Guard Sharkkis
    ),
    "Tempest Keep (The Eye)": (
        (18805, 500),  # High Astromancer Solarian
        (19514, 400),  # Al'ar <Phoenix God>
        (19516, 750),  # Void Reaver
        (19622, 600),  # Kael'thas Sunstrider <Lord of the Blood Elves>
        (20031, 25),  # Bloodwarder Legionnaire
        (20032, 40),  # Bloodwarder Vindicator
        (20033, 25),  # Astromancer
        (20034, 25),  # Star Scryer
        (20035, 40),  # Bloodwarder Marshal
        (20036, 25),  # Bloodwarder Squire
        (20037, 25),  # Tempest Falconer
        (20038, 10),  # Phoenix-Hawk Hatchling
        (20039, 75),  # Phoenix-Hawk
        (20040, 75),  # Crystalcore Devastator
        (20041, 40),  # Crystalcore Sentinel
        (20042, 25),  # Tempest-Smith
        (20043, 4),  # Apprentice Star Scryer
        (20044, 4),  # Novice Astromancer
        (20045, 40),  # Nether Scryer
        (20046, 40),  # Astromancer Lord
        (20047, 25),  # Crimson Hand Battle Mage
        (20048, 25),  # Crimson Hand Centurion
        (20049, 40),  # Crimson Hand Blood Knight
        (20050, 40),  # Crimson Hand Inquisitor
        (20052, 25),  # Crystalcore Mechanic
        (20060, 36),  # Lord Sanguinar <The Blood Hammer>
        (20062, 36),  # Grand Astromancer Capernian <Advisor to Kael'thas>
        (20063, 36),  # Master Engineer Telonicus <Advisor to Kael'thas>
        (20064, 36),  # Thaladred the Darkener <Advisor to Kael'thas>
    ),
    "Hyjal Summit": (
        (17895, 20),  # Ghoul
        (17898, 25),  # Abomination
        (17899, 22),  # Shadowy Necromancer
        (17968, 750),  # Archimonde
    ),
    "Black Temple": (
        (22841, 132),  # Shade of Akama
        (22844, 45),  # Ashtongue Battlelord
        (22845, 30),  # Ashtongue Mystic
        (22846, 30),  # Ashtongue Stormcaller
        (22847, 30),  # Ashtongue Primalist
        (22848, 15),  # Storm Fury
        (22849, 15),  # Ashtongue Feral Spirit
        (22853, 30),  # Illidari Defiler
        (22855, 60),  # Illidari Nightlord
        (22869, 30),  # Illidari Boneslicer
        (22871, 825),  # Teron Gorefiend
        (22873, 40),  # Coilskar General
        (22874, 30),  # Coilskar Harpooner
        (22875, 30),  # Coilskar Sea-Caller
        (22876, 30),  # Coilskar Soothsayer
        (22877, 30),  # Coilskar Wrangler
        (22878, 60),  # Aqueous Lord
        (22879, 30),  # Shadowmoon Reaver
        (22880, 45),  # Shadowmoon Champion
        (22881, 15),  # Aqueous Surger
        (22882, 30),  # Shadowmoon Deathshaper
        (22883, 9),  # Aqueous Spawn
        (22884, 75),  # Leviathan
        (22885, 15),  # Dragon Turtle <Coilskar Harpooner's Pet>
        (22887, 500),  # High Warlord Naj'entus
        (22898, 600),  # Supremus
        (22917, 800),  # Illidan Stormrage <The Betrayer>
        (22945, 25),  # Shadowmoon Blood Mage
        (22946, 10),  # Shadowmoon War Hound
        (22947, 750),  # Mother Shahraz
        (22948, 750),  # Gurtogg Bloodboil
        (22949, 250),  # Gathios the Shatterer
        (22950, 250),  # High Nethermancer Zerevor
        (22951, 250),  # Lady Malande
        (22952, 250),  # Veras Darkshadow
        (22953, 50),  # Wrathbone Flayer
        (22954, 75),  # Illidari Fearbringer
        (22956, 50),  # Sister of Pain
        (22957, 90),  # Priestess of Dementia
        (22959, 30),  # Spellbound Attendant
        (22960, 35),  # Dragonmaw Wyrmcaller
        (22962, 90),  # Priestess of Delight
        (22964, 50),  # Sister of Pleasure
        (22965, 25),  # Enslaved Servant
        (23018, 35),  # Shadowmoon Houndmaster
        (23028, 30),  # Bonechewer Taskmaster
        (23030, 35),  # Dragonmaw Sky Stalker
        (23047, 5),  # Shadowmoon Soldier
        (23049, 50),  # Shadowmoon Weapon Master
        (23089, 165),  # Akama
        (23172, 35),  # Hand of Gorefiend
        (23196, 90),  # Bonechewer Behemoth
        (23222, 55),  # Bonechewer Brawler
        (23232, 20),  # Mutant War Hound
        (23235, 30),  # Bonechewer Blade Fury
        (23236, 30),  # Bonechewer Shield Disciple
        (23237, 30),  # Bonechewer Blood Prophet
        (23239, 55),  # Bonechewer Combatant
        (23330, 35),  # Dragonmaw Wind Reaver
        (23337, 40),  # Illidari Centurion
        (23339, 30),  # Illidari Heartseeker
        (23374, 30),  # Ashtongue Stalker
        (23394, 90),  # Promenade Sentinel
        (23397, 40),  # Illidari Blood Lord
        (23399, 12),  # Suffering Soul Fragment
        (23400, 30),  # Illidari Archon
        (23401, 6),  # Hungering Soul Fragment
        (23402, 30),  # Illidari Battle-mage
        (23403, 25),  # Illidari Assassin
        (23421, 25),  # Ashtongue Channeler
        (23426, 1000),  # The Illidari Council
    ),
    "Zul'Aman": (
        (23542, 12),  # Amani'shi Axe Thrower
        (23574, 220),  # Akil'zon <Eagle Avatar>
        (23576, 180),  # Nalorakk <Bear Avatar>
        (23577, 80),  # Halazzi <Lynx Avatar>
        (23578, 135),  # Jan'alai <Dragonhawk Avatar>
        (23580, 15),  # Amani'shi Warbringer
        (23581, 12),  # Amani'shi Medicine Man
        (23582, 12),  # Amani'shi Tribesman
        (23584, 12),  # Amani Bear
        (23596, 12),  # Amani'shi Flame Caster
        (23597, 12),  # Amani'shi Guardian
        (23774, 15),  # Amani'shi Trainer
        (23863, 225),  # Zul'jin
        (24043, 8),  # Amani Lynx
        (24047, 4),  # Amani Crocolisk
        (24059, 12),  # Amani'shi Beast Tamer
        (24065, 12),  # Amani'shi Handler
        (24138, 4),  # Tamed Amani Crocolisk
        (24179, 10),  # Amani'shi Wind Walker
        (24180, 10),  # Amani'shi Protector
        (24239, 135),  # Hex Lord Malacrass
        (24374, 20),  # Amani'shi Berserker
        (24530, 8),  # Amani Elder Lynx
        (24549, 20),  # Amani'shi Tempest
    ),
    "Sunwell Plateau": (
        (24850, 475),  # Kalecgos
        (24882, 1384),  # Brutallus
        (25165, 475),  # Lady Sacrolash
        (25166, 475),  # Grand Warlock Alythess
        (25363, 35),  # Sunblade Cabalist
        (25367, 35),  # Sunblade Arch Mage
        (25368, 35),  # Sunblade Slayer
        (25369, 35),  # Sunblade Vindicator
        (25370, 35),  # Sunblade Dusk Priest
        (25371, 35),  # Sunblade Dawn Priest
        (25373, 35),  # Shadowsword Soulbinder
        (25483, 35),  # Shadowsword Manafiend
        (25484, 35),  # Shadowsword Assassin
        (25486, 35),  # Shadowsword Vanquisher
        (25506, 35),  # Shadowsword Lifeshaper
        (25507, 75),  # Sunblade Protector
        (25508, 100),  # Shadowsword Guardian
        (25509, 35),  # Priestess of Torment
        (25591, 35),  # Painbringer
        (25592, 40),  # Doomfire Destroyer
        (25593, 68.75),  # Apocalypse Guard
        (25595, 76),  # Chaos Gazer
        (25597, 35),  # Oblivion Mage
        (25599, 86),  # Cataclysm Hound
        (25741, 360),  # M'uru
        (25837, 35),  # Shadowsword Commander
        (25867, 20),  # Sunblade Dragonhawk
    ),
}

for _entries in RAID_HEALTH_PRENERF.values():
    for _entry, _health in _entries:
        creature_template_columns(_entry, HealthModifier=_health)
