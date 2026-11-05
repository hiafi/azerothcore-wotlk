// Host tests for src/ContentGateRules.h: conf parsing, mode -> flags, closed set, bundles, reload diff, zones.
#include "ContentGateRules.h"
#include "check.h"

using namespace ContentGate;

namespace
{
    // A small fake Map.dbc: vanilla 5-mans (normal only), a TBC 5-man (N+H), vanilla raids (10N only; Onyxia keeps
    // its WotLK 10N and 25N MapDifficulty rows, both set to 40 players), a WotLK raid (10N/25N) and ICC (all four).
    std::map<uint32_t, MapShape> const& FakeMaps()
    {
        static std::map<uint32_t, MapShape> const maps = {
            { 36, { false, FLAG_DIFF_0 } },                                 // Deadmines (normal only today)
            { 349, { false, FLAG_DIFF_0 } },                                // Maraudon
            { 429, { false, FLAG_DIFF_0 } },                                // Dire Maul
            { 543, { false, FLAG_DIFF_0 | FLAG_DIFF_1 } },                  // Hellfire Ramparts
            { 249, { true, FLAG_DIFF_0 | FLAG_DIFF_1 } },                   // Onyxia (two 40-player rows)
            { 309, { true, FLAG_DIFF_0 } },                                 // Zul'Gurub
            { 409, { true, FLAG_DIFF_0 } },                                 // Molten Core
            { 469, { true, FLAG_DIFF_0 } },                                 // Blackwing Lair
            { 509, { true, FLAG_DIFF_0 } },                                 // Ruins of Ahn'Qiraj
            { 533, { true, FLAG_DIFF_0 | FLAG_DIFF_1 } },                   // Naxxramas
            { 631, { true, FLAG_ALL } },                                    // Icecrown Citadel
        };
        return maps;
    }

    MapLookup Lookup()
    {
        return [](uint32_t mapId) -> std::optional<MapShape>
        {
            auto const itr = FakeMaps().find(mapId);
            if (itr == FakeMaps().end())
                return std::nullopt;
            return itr->second;
        };
    }

    std::vector<std::pair<uint32_t, MapShape>> AllMaps()
    {
        return { FakeMaps().begin(), FakeMaps().end() };
    }

    std::vector<uint32_t> AllBattlegrounds()
    {
        return { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 30, 32 };
    }

    bool HasError(std::vector<std::string> const& errors, std::string const& needle)
    {
        for (std::string const& error : errors)
            if (error.find(needle) != std::string::npos)
                return true;
        return false;
    }

    void TestModeFlags()
    {
        CHECK(ModeFlag("N", false) == FLAG_DIFF_0);
        CHECK(ModeFlag("h", false) == FLAG_DIFF_1);
        CHECK(!ModeFlag("10N", false));
        CHECK(!ModeFlag("25H", false));
        CHECK(ModeFlag("N", true) == FLAG_DIFF_0);
        CHECK(ModeFlag("10n", true) == FLAG_DIFF_0);
        CHECK(ModeFlag("25N", true) == FLAG_DIFF_1);
        CHECK(ModeFlag("10H", true) == FLAG_DIFF_2);
        CHECK(ModeFlag("25H", true) == FLAG_DIFF_3);
        CHECK(!ModeFlag("H", true));                  // ambiguous for a raid
        CHECK(!ModeFlag("", true));
        CHECK(FlagsToModes(FLAG_DIFF_0 | FLAG_DIFF_1, false) == "N,H");
        CHECK(FlagsToModes(FLAG_ALL, true) == "10N,25N,10H,25H");
        CHECK(FlagsToModes(0, true).empty());
    }

    void TestParseInstances()
    {
        std::map<uint32_t, uint8_t> open;
        std::vector<std::string> errors;
        ParseInstances("36:N  349:N\t429:n 543:N,H 631:10N,25H 533:*", Lookup(), open, errors);
        CHECK(errors.empty());
        CHECK(open[36] == FLAG_DIFF_0);
        CHECK(open[349] == FLAG_DIFF_0);
        CHECK(open[429] == FLAG_DIFF_0);
        CHECK(open[543] == (FLAG_DIFF_0 | FLAG_DIFF_1));
        CHECK(open[631] == (FLAG_DIFF_0 | FLAG_DIFF_3));
        CHECK(open[533] == (FLAG_DIFF_0 | FLAG_DIFF_1));

        // Bad entries are reported and skipped; good parts of the same line still apply.
        open.clear();
        errors.clear();
        ParseInstances("36:H 999:N 349 abc:N 409:N,25N 543: 631:H", Lookup(), open, errors);
        CHECK(HasError(errors, "map 36 has no H difficulty"));
        CHECK(HasError(errors, "map 999 is not a dungeon or raid map"));
        CHECK(HasError(errors, "'349' has no ':<modes>' part"));
        CHECK(HasError(errors, "'abc:N' has a bad map id"));
        CHECK(HasError(errors, "map 409 has no 25N difficulty"));
        CHECK(HasError(errors, "'543:' lists no modes"));
        CHECK(HasError(errors, "mode 'H' is not valid for a raid"));
        CHECK(errors.size() == 7);
        CHECK(open.count(36) == 0);
        CHECK(open[409] == FLAG_DIFF_0);              // 409:N applied even though 25N failed
        CHECK(open.count(631) == 0);

        // Onyxia: `249:*` opens both raid rows; `249:N` leaves the 25-player row (a raid-25 leader) closed.
        open.clear();
        errors.clear();
        ParseInstances("249:*", Lookup(), open, errors);
        CHECK(errors.empty());
        CHECK(open[249] == (FLAG_DIFF_0 | FLAG_DIFF_1));
        open.clear();
        ParseInstances("249:N", Lookup(), open, errors);
        CHECK(open[249] == FLAG_DIFF_0);
        open.clear();
        ParseInstances("249:10N,25N", Lookup(), open, errors);
        CHECK(errors.empty());
        CHECK(open[249] == (FLAG_DIFF_0 | FLAG_DIFF_1));

        // Several conf keys accumulate.
        open.clear();
        errors.clear();
        ParseInstances("543:N", Lookup(), open, errors);
        ParseInstances("543:H", Lookup(), open, errors);
        CHECK(open[543] == (FLAG_DIFF_0 | FLAG_DIFF_1));
    }

    void TestIdListsAndConfig()
    {
        std::vector<std::string> errors;
        std::set<uint32_t> ids = ParseIdList("1 2, 3,,4\t5", "x", errors);
        CHECK(errors.empty());
        CHECK(ids == std::set<uint32_t>({ 1, 2, 3, 4, 5 }));
        ids = ParseIdList("1 two 99999999999", "x", errors);
        CHECK(errors.size() == 2);
        CHECK(ids == std::set<uint32_t>({ 1 }));

        RawConfig raw;
        raw.openInstances = { "36:N 349:N", "", "429:N" };
        raw.openBattlegrounds = "1 2 3";
        raw.openOutdoorPvP = "5 9 0";
        raw.closedEvents = "61";
        raw.openBundles = "Zul_Gurub, t05_device bad-name";
        raw.watchdogMs = 10;
        Config const cfg = ParseConfig(raw, Lookup());
        CHECK(cfg.openInstances.size() == 3);
        CHECK(cfg.openBattlegrounds == std::set<uint32_t>({ 1, 2, 3 }));
        CHECK(cfg.openOutdoorPvP == std::set<uint32_t>({ 5 }));
        CHECK(HasError(cfg.errors, "9 is not an outdoor PvP type"));
        CHECK(HasError(cfg.errors, "0 is not an outdoor PvP type"));
        CHECK(cfg.openBundles == std::set<std::string>({ "zul_gurub", "t05_device" }));
        CHECK(HasError(cfg.errors, "'bad-name' is not a valid bundle name"));
        CHECK(cfg.closedEvents == std::set<uint32_t>({ 61 }));
        CHECK(cfg.watchdogMs == 1000);               // clamped
        CHECK(!cfg.outlandOpen && !cfg.northrendOpen);
    }

    void TestOpensWith()
    {
        std::string error;
        std::optional<OpensWith> atom = ParseOpensWith("", Lookup(), error);
        CHECK(atom && atom->kind == OpensWith::Kind::None);
        atom = ParseOpensWith("map:409:N", Lookup(), error);
        CHECK(atom && atom->kind == OpensWith::Kind::Map && atom->id == 409 && atom->flag == FLAG_DIFF_0);
        atom = ParseOpensWith("MAP:631:25h", Lookup(), error);
        CHECK(atom && atom->flag == FLAG_DIFF_3);
        atom = ParseOpensWith("bg:7", Lookup(), error);
        CHECK(atom && atom->kind == OpensWith::Kind::Battleground && atom->id == 7);
        atom = ParseOpensWith("Outland", Lookup(), error);
        CHECK(atom && atom->kind == OpensWith::Kind::Outland);
        atom = ParseOpensWith("northrend", Lookup(), error);
        CHECK(atom && atom->kind == OpensWith::Kind::Northrend);

        CHECK(!ParseOpensWith("map:409:H", Lookup(), error));
        CHECK(error.find("has no mode 'H'") != std::string::npos);
        CHECK(!ParseOpensWith("map:409:25N", Lookup(), error));
        CHECK(!ParseOpensWith("map:1:N", Lookup(), error));
        CHECK(error.find("not a dungeon or raid map") != std::string::npos);
        CHECK(!ParseOpensWith("bg:x", Lookup(), error));
        CHECK(!ParseOpensWith("map:409", Lookup(), error));
        CHECK(!ParseOpensWith("tier:1", Lookup(), error));
    }

    std::vector<Bundle> DayOneBundles()
    {
        std::string error;
        auto make = [&](std::string name, uint32_t event, std::string opens,
            std::vector<std::pair<uint8_t, uint32_t>> members)
        {
            Bundle b;
            b.name = std::move(name);
            b.gameEvent = event;
            b.opensWithText = opens;
            b.opensWith = *ParseOpensWith(opens, Lookup(), error);
            b.members = std::move(members);
            return b;
        };
        return {
            make("molten_core", 200, "map:409:N", {}),
            make("onyxia", 201, "map:249:N", { { DT_QUEST, 4903 } }),
            make("maraudon", 202, "map:349:N", { { DT_QUEST, 7028 }, { DT_QUEST, 7029 } }),
            make("zul_gurub", 204, "map:309:N", { { DT_QUEST, 8181 } }),
            make("blackwing_lair", 205, "map:469:N", { { DT_LOOT, 18563 } }),
            make("t05_device", 0, "", { { DT_QUEST, 8922 }, { DT_QUEST, 8923 } }),
        };
    }

    Config DayOneConfig()
    {
        RawConfig raw;
        raw.openInstances = { "36:N 349:N 429:N" };
        raw.openBattlegrounds = "1 2 3";
        raw.closedEvents = "61";
        return ParseConfig(raw, Lookup());
    }

    void TestClosedSet()
    {
        Config const cfg = DayOneConfig();
        CHECK(cfg.errors.empty());
        std::vector<Bundle> bundles = DayOneBundles();
        ClosedSet const closed = ComputeClosedSet(cfg, AllMaps(), AllBattlegrounds(), bundles);

        CHECK(closed.maps.count(36) == 0);
        CHECK(closed.maps.count(349) == 0);
        CHECK(closed.maps.count(429) == 0);
        CHECK(closed.maps.at(543) == (FLAG_DIFF_0 | FLAG_DIFF_1));
        CHECK(closed.maps.at(409) == FLAG_DIFF_0);
        CHECK(closed.maps.at(631) == FLAG_ALL);
        CHECK(closed.maps.at(533) == (FLAG_DIFF_0 | FLAG_DIFF_1));
        CHECK(closed.ClosedDifficultyCount() == 2 + 2 + 1 + 1 + 1 + 1 + 2 + 4);
        CHECK(closed.maps.at(249) == (FLAG_DIFF_0 | FLAG_DIFF_1));

        CHECK(closed.battlegrounds == std::set<uint32_t>({ 4, 5, 6, 7, 8, 9, 10, 11, 30, 32 }));
        CHECK(closed.outdoorPvP == std::set<uint32_t>({ 1, 2, 3, 4, 5, 6, 7 }));

        // Linked events: AV/WSG/AB Call to Arms open with their BGs; EotS/SotA/IoC, arena seasons, Kalu'ak and
        // Sun's Reach stay closed; the explicit list adds 61; closed bundles add their events.
        CHECK(!closed.events.count(18) && !closed.events.count(19) && !closed.events.count(20));
        CHECK(closed.events.count(21) && closed.events.count(53) && closed.events.count(54));
        CHECK(closed.events.count(55) && closed.events.count(60) && closed.events.count(76));
        CHECK(closed.events.count(75));                                      // Arena Season 1 follows bg 6 too
        CHECK(closed.events.count(63) && closed.events.count(64));
        CHECK(closed.events.count(101) && closed.events.count(115));
        CHECK(closed.events.count(61));
        CHECK(!closed.events.count(4) && !closed.events.count(24));          // holidays stay open
        CHECK(closed.events.count(200) && closed.events.count(201) && closed.events.count(204));
        CHECK(!closed.events.count(202));                                    // maraudon is open
        CHECK(!closed.events.count(0));                                      // t05_device has no event

        CHECK(closed.openBundles == std::set<std::string>({ "maraudon" }));
        CHECK(closed.closedBundles.count("t05_device") && closed.closedBundles.count("onyxia"));
        CHECK(closed.members.count({ DT_QUEST, 4903 }));
        CHECK(!closed.members.count({ DT_QUEST, 7028 }));
        CHECK(closed.members.count({ DT_QUEST, 8922 }));
        CHECK(closed.outlandClosed && closed.northrendClosed);
    }

    void TestBundleOpening()
    {
        Config cfg = DayOneConfig();
        std::vector<Bundle> const bundles = DayOneBundles();
        // Open by atom.
        cfg.openInstances[409] = FLAG_DIFF_0;
        CHECK(IsBundleOpen(bundles[0], cfg));
        // Open by name, atom closed.
        cfg.openBundles.insert("t05_device");
        CHECK(IsBundleOpen(bundles[5], cfg));
        cfg.openBundles.insert("zul_gurub");
        CHECK(IsBundleOpen(bundles[3], cfg));
        // Heroic open alone does not open a normal atom.
        Config heroicOnly = DayOneConfig();
        heroicOnly.openInstances[543] = FLAG_DIFF_1;
        Bundle ramparts;
        ramparts.name = "ramparts";
        ramparts.opensWith = { OpensWith::Kind::Map, 543, FLAG_DIFF_0 };
        CHECK(!IsBundleOpen(ramparts, heroicOnly));
        heroicOnly.openInstances[543] |= FLAG_DIFF_0;
        CHECK(IsBundleOpen(ramparts, heroicOnly));
        // Continent atoms.
        Bundle quelDanas;
        quelDanas.name = "sunwell";
        quelDanas.opensWith = { OpensWith::Kind::Outland, 0, 0 };
        CHECK(!IsBundleOpen(quelDanas, cfg));
        cfg.outlandOpen = true;
        CHECK(IsBundleOpen(quelDanas, cfg));
    }

    void TestReloadDiff()
    {
        Config before = DayOneConfig();
        std::vector<Bundle> const bundles = DayOneBundles();
        ClosedSet const a = ComputeClosedSet(before, AllMaps(), AllBattlegrounds(), bundles);

        Config after = before;
        after.openInstances[409] = FLAG_DIFF_0;              // MC opens (A5)
        after.openInstances[249] = FLAG_DIFF_0;              // Onyxia opens (quest member)
        after.openBattlegrounds.insert(7);                   // EotS opens -> Call to Arms 21 opens
        after.openOutdoorPvP.insert(5);
        ClosedSet const b = ComputeClosedSet(after, AllMaps(), AllBattlegrounds(), bundles);
        ClosedSetDiff const diff = Diff(a, b);
        CHECK(diff.openedEvents == std::set<uint32_t>({ 21, 200, 201 }));
        CHECK(diff.closedEvents.empty());
        CHECK(diff.openedBundles == std::set<std::string>({ "molten_core", "onyxia" }));
        CHECK(diff.closedBundles.empty());
        CHECK(diff.outdoorPvPChanged);
        CHECK(diff.questMembersOpened);
        CHECK(b.maps.count(409) == 0);

        // And back again: MC closes, its event closes.
        ClosedSetDiff const back = Diff(b, a);
        CHECK(back.closedEvents == std::set<uint32_t>({ 21, 200, 201 }));
        CHECK(back.closedBundles == std::set<std::string>({ "molten_core", "onyxia" }));
        CHECK(!back.questMembersOpened);

        // No change -> empty diff.
        ClosedSetDiff const none = Diff(a, a);
        CHECK(none.openedEvents.empty() && none.closedEvents.empty() && !none.outdoorPvPChanged);
    }

    void TestZones()
    {
        for (uint32_t zone : { 3483u, 3518u, 3519u, 3520u, 3521u, 3522u, 3523u, 3540u, 3703u, 3917u, 4080u })
            CHECK(IsOutlandProperZone(zone));
        // Blood Elf and Draenei zones, cities, the seas around the isles, and anything else stay reachable.
        for (uint32_t zone : { 3430u, 3433u, 3487u, 3524u, 3525u, 3557u, 3455u, 3479u, 0u, 1519u })
            CHECK(!IsOutlandProperZone(zone));

        CHECK(ClosedContinentAt(MAP_OUTLAND, 3483, false, false) == Continent::Outland);
        CHECK(ClosedContinentAt(MAP_OUTLAND, 3430, false, false) == Continent::Allowed);
        CHECK(ClosedContinentAt(MAP_OUTLAND, 3540, false, false) == Continent::Outland);
        CHECK(ClosedContinentAt(MAP_OUTLAND, 3917, false, false) == Continent::Outland);
        CHECK(ClosedContinentAt(MAP_OUTLAND, 3483, true, false) == Continent::Allowed);
        CHECK(ClosedContinentAt(MAP_NORTHREND, 0, false, false) == Continent::Northrend);
        CHECK(ClosedContinentAt(MAP_NORTHREND, 65, false, true) == Continent::Allowed);
        CHECK(ClosedContinentAt(MAP_EASTERN_KINGDOMS, 3483, false, false) == Continent::Allowed);

        CHECK(DockForTransport(181688) && DockForTransport(181688)->map == MAP_EASTERN_KINGDOMS);
        CHECK(DockForTransport(186238) && DockForTransport(186238)->map == MAP_KALIMDOR);
        CHECK(DockForTransport(181689) && DockForTransport(190536));
        CHECK(!DockForTransport(176310));                    // Auberdine boat: not a Northrend route
        CHECK(NorthrendDocks().size() == 4);
    }

    void TestBundleNames()
    {
        CHECK(IsValidBundleName("molten_core"));
        CHECK(IsValidBundleName("t05_device"));
        CHECK(!IsValidBundleName(""));
        CHECK(!IsValidBundleName("Molten"));
        CHECK(!IsValidBundleName("a-b"));
        CHECK(!IsValidBundleName(std::string(33, 'a')));
        CHECK(IsAllowedMemberType(DT_QUEST) && IsAllowedMemberType(DT_ACHIEVEMENT_CRITERIA));
        CHECK(IsAllowedMemberType(DT_LOOT));
        CHECK(!IsAllowedMemberType(2) && !IsAllowedMemberType(9) && !IsAllowedMemberType(0));
    }

    void TestLinkedEventsUnique()
    {
        std::set<uint32_t> seen;
        for (LinkedEvent const& linked : LinkedEvents())
            CHECK(seen.insert(linked.event).second);
        CHECK(seen.size() == 10 + 6 + 15);
    }

    // S1: a bundle-block event no loaded bundle owns stays closed, whatever the conf opens.
    void TestUnownedBundleEvents()
    {
        CHECK(AllBundleEventIds().size() == BUNDLE_EVENT_LAST - BUNDLE_EVENT_FIRST + 1);
        CHECK(*AllBundleEventIds().begin() == 200 && *AllBundleEventIds().rbegin() == 255);

        // Bundle tables missing: no bundles, the whole block is closed even with every switch open.
        Config cfg = DayOneConfig();
        cfg.openInstances[409] = FLAG_DIFF_0;
        cfg.openInstances[309] = FLAG_DIFF_0;
        cfg.openBattlegrounds.insert(BG_ALL_ARENAS);
        cfg.outlandOpen = true;
        cfg.openBundles.insert("zul_gurub");
        ClosedSet const missing = ComputeClosedSet(cfg, AllMaps(), AllBattlegrounds(), {}, AllBundleEventIds());
        for (uint32_t id = BUNDLE_EVENT_FIRST; id <= BUNDLE_EVENT_LAST; ++id)
            CHECK(missing.events.count(id));
        CHECK(missing.unownedBundleEvents.size() == 56);
        CHECK(!missing.events.count(19));                                    // the rest of the conf still applies
        CHECK(missing.openBundles.empty() && missing.closedBundles.empty());

        // Tables present: only the existing block events without a bundle stay closed.
        std::vector<Bundle> const bundles = DayOneBundles();
        std::set<uint32_t> const existing = { 200, 201, 202, 203, 204, 205, 199, 256 };
        CHECK(UnownedBundleEvents(existing, bundles) == std::set<uint32_t>({ 203 }));
        ClosedSet const present = ComputeClosedSet(DayOneConfig(), AllMaps(), AllBattlegrounds(), bundles, existing);
        CHECK(present.unownedBundleEvents == std::set<uint32_t>({ 203 }));
        CHECK(present.events.count(203));
        CHECK(!present.events.count(202));                                   // maraudon's event is owned and open
        CHECK(!present.events.count(199) && !present.events.count(256));     // outside the block: untouched

        // The default (no block events) closes nothing extra.
        CHECK(ComputeClosedSet(DayOneConfig(), AllMaps(), AllBattlegrounds(), bundles).unownedBundleEvents.empty());

        // Tables appear and `.gate reload`: the block events of open bundles open again.
        ClosedSet const after = ComputeClosedSet(cfg, AllMaps(), AllBattlegrounds(), bundles, existing);
        ClosedSetDiff const diff = Diff(missing, after);
        CHECK(diff.openedEvents.count(200) && diff.openedEvents.count(204) && diff.openedEvents.count(202));
        CHECK(!diff.openedEvents.count(201) && !diff.openedEvents.count(203));
    }
}

int main()
{
    TestModeFlags();
    TestParseInstances();
    TestIdListsAndConfig();
    TestOpensWith();
    TestClosedSet();
    TestBundleOpening();
    TestReloadDiff();
    TestZones();
    TestBundleNames();
    TestLinkedEventsUnique();
    TestUnownedBundleEvents();
    return Report("rules_test");
}
