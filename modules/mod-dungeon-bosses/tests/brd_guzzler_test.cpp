// Host tests for GuzzlerLogic.h (D17: The Grim Guzzler room: patrons, Ribbly and Plugger): the ids, the build spec
// numbers (SP 93-107, 417-433, 624-641), the trigger predicates, and the bar event as a state machine (SP 109-216:
// theft, Plugger's death, the kegs, Ribbly's gossip, Rocknot's ale run, the love potion, Phalanx, the Bar Door).
#include "GuzzlerLogic.h"
#include "check.h"
#include <array>

using namespace BlackrockDepthsRework;
using namespace BrdGuzzler;

namespace
{
    void TestIdsAndTracking()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211410 && kSpellSlice.last == 211429);
        CHECK(SPELL_GZ_GOUGE == 211410 && SPELL_GZ_KICK == 211411);
        CHECK(kSpellSlice.Contains(SPELL_GZ_GOUGE) && kSpellSlice.Contains(SPELL_GZ_KICK));
        // The copies are never the stock spells (rule 15).
        CHECK(SPELL_GZ_GOUGE != SPELL_STOCK_GOUGE && SPELL_GZ_KICK != SPELL_STOCK_KICK);
        CHECK(SPELL_STOCK_GOUGE == 12540 && SPELL_STOCK_KICK == 15610);
        // Ribbly and Plugger keep tracking slots without credit (the instance writes them on their deaths).
        CHECK(IsTrackingOnlySlot(BOSS_RIBBLY) && IsTrackingOnlySlot(BOSS_PLUGGER));
        CHECK(!SlotWrittenByScript(BOSS_RIBBLY, true) && !SlotWrittenByScript(BOSS_PLUGGER, true));
        CHECK(!IsReworkBound(BOSS_RIBBLY, true) && !IsReworkBound(BOSS_PLUGGER, true));
        CHECK(BossOfEntry(NPC_RIBBLY) == BOSS_RIBBLY && BossOfEntry(NPC_PLUGGER) == BOSS_PLUGGER);
        // The room's creature ids.
        CHECK(NPC_RIBBLY == 9543 && NPC_RIBBLYS_CRONY == 10043 && NPC_PLUGGER == 9499);
        CHECK(NPC_GRIM_PATRON == 9545 && NPC_GUZZLING_PATRON == 9547 && NPC_HAMMERED_PATRON == 9554);
        // Plugger's stock text groups 0-3 are kept (no new line).
        bool plugger = false;
        for (TextRange const& range : kTextRanges)
            if (range.entry == NPC_PLUGGER)
            {
                plugger = true;
                CHECK(range.first == 0 && range.last == 3 && range.firstNew == 4);
            }
        CHECK(plugger);
    }

    void TestHealth()
    {
        // Ribbly 40k / 60k on the level 53 warrior base, Plugger 40k / 60k on the level 55 paladin base, the Cronies
        // 6k / 9k on the level 50 base (SP 417-420, 624-628; handoff 3.6).
        CHECK(kRibblyHealth(false) == 40000 && kRibblyHealth(true) == 60000);
        CHECK(kRibblyCronyHealth(false) == 6000 && kRibblyCronyHealth(true) == 9000);
        CHECK(kPluggerHealth(false) == 40000 && kPluggerHealth(true) == 60000);
        auto const near = [](std::uint32_t got, std::uint32_t want) { return got + 2 >= want && got <= want + 2; };
        CHECK(near(HealthOf(kBaseWarrior53, kRibblyHealthModifier), kRibblyHealth.normal));
        CHECK(near(HealthOf(kBasePaladin55, kPluggerHealthModifier), kPluggerHealth.normal));
        CHECK(near(HealthOf(kBaseWarrior50, kRibblyCronyHealthModifier), kRibblyCronyHealth.normal));
        // The spec's patron table: stock about 2,200 / 1,550 / 6,650 -> about 1,300 / 930 / 3,300 (ruling 65).
        CHECK(HealthOf(kBaseWarrior50, kStockGrimPatronHealthModifier) == 2215);
        CHECK(HealthOf(kBaseMage50, kStockGuzzlingPatronHealthModifier) == 1551);
        CHECK(HealthOf(kBaseWarrior50, kStockHammeredPatronHealthModifier) == 6645);
        std::uint32_t const grim = HealthOf(kBaseWarrior50, kGrimPatronHealthModifier);
        std::uint32_t const guzzling = HealthOf(kBaseMage50, kGuzzlingPatronHealthModifier);
        std::uint32_t const hammered = HealthOf(kBaseWarrior50, kHammeredPatronHealthModifier);
        CHECK(grim >= 1250 && grim <= 1350);
        CHECK(guzzling >= 900 && guzzling <= 960);
        CHECK(hammered >= 3250 && hammered <= 3350);
        // Tuned down, never up: every patron is weaker than stock, the three hit for 1.5 (stock 3.5).
        CHECK(kGrimPatronHealthModifier < kStockGrimPatronHealthModifier);
        CHECK(kGuzzlingPatronHealthModifier < kStockGuzzlingPatronHealthModifier);
        CHECK(kHammeredPatronHealthModifier < kStockHammeredPatronHealthModifier);
        CHECK(kPatronDamageModifier == 1.5f && kStockPatronDamageModifier == 3.5f);
        // A Hammered Patron stays the sturdiest of the three, as stock.
        CHECK(hammered > grim && grim > guzzling);
        // Heroic health is higher than normal for the three named units.
        CHECK(kRibblyHealth.heroic > kRibblyHealth.normal && kPluggerHealth.heroic > kPluggerHealth.normal);
        CHECK(kRibblyCronyHealth.heroic > kRibblyCronyHealth.normal);
    }

    void TestTimers()
    {
        // The three repeat windows lengthened (ruling 65 / 69) and the two durations shortened (ruling 62 / 65).
        CHECK(kShadowBoltRepeat.min == 8000 && kShadowBoltRepeat.max == 10000);
        CHECK(kShadowBoltRepeat.min > kStockShadowBoltRepeat.max);
        CHECK(kBackhandRepeat.min == 10000 && kBackhandRepeat.max == 12000);
        CHECK(kBackhandRepeat.min > kStockBackhandRepeat.max);
        CHECK(kStockShadowBoltRepeat == (Window{ 3000, 4000 }) && kStockBackhandRepeat == (Window{ 5000, 8000 }));
        CHECK(kKickRepeat == (Window{ 5000, 8000 }));
        CHECK(kGougeIncapacitateMs == 2000 && kGougeIncapacitateMs < kStockGougeIncapacitateMs);
        CHECK(kKickLockoutMs == 3000 && kKickLockoutMs < kStockKickLockoutMs);
        // The 2 s rule: the incapacitate on the tank every 10 s is 20% of the time at most.
        CHECK(kGougeIncapacitateMs * 5 <= kGougeRepeatMs);
        // Immunity: stock sets replaced by 1972 (stun immune, interruptible).
        CHECK(kBossImmunity == 1972 && kStockRibblyImmunity == -251 && kStockPluggerImmunity == -324);
    }

    void TestPredicates()
    {
        // Theft: only the Grim and Guzzling patrons within 7 yd of Plugger join; the Hammered ones never do.
        CHECK(JoinsTheft(NPC_GRIM_PATRON, 0.f) && JoinsTheft(NPC_GUZZLING_PATRON, 7.f));
        CHECK(!JoinsTheft(NPC_GRIM_PATRON, 7.1f) && !JoinsTheft(NPC_GUZZLING_PATRON, 20.f));
        CHECK(!JoinsTheft(NPC_HAMMERED_PATRON, 1.f) && !JoinsTheft(NPC_PHALANX, 1.f) && !JoinsTheft(NPC_RIBBLY, 1.f));
        // His death: all three patrons and Phalanx within 100 yd; nobody else, nobody farther.
        for (std::uint32_t entry : { NPC_GRIM_PATRON, NPC_GUZZLING_PATRON, NPC_HAMMERED_PATRON, NPC_PHALANX })
        {
            CHECK(TurnsHostileOnPluggerDeath(entry, 0.f));
            CHECK(TurnsHostileOnPluggerDeath(entry, 100.f));
            CHECK(!TurnsHostileOnPluggerDeath(entry, 100.5f));
        }
        CHECK(!TurnsHostileOnPluggerDeath(NPC_RIBBLY, 5.f) && !TurnsHostileOnPluggerDeath(NPC_RIBBLYS_CRONY, 5.f));
        CHECK(!TurnsHostileOnPluggerDeath(NPC_HURLEY, 5.f));
        // Ribbly's gossip: his Cronies within 30 yd.
        CHECK(JoinsRibblyGossip(NPC_RIBBLYS_CRONY, 0.f) && JoinsRibblyGossip(NPC_RIBBLYS_CRONY, 30.f));
        CHECK(!JoinsRibblyGossip(NPC_RIBBLYS_CRONY, 30.1f) && !JoinsRibblyGossip(NPC_GRIM_PATRON, 1.f));
        // The counts the room's rows work on.
        CHECK(kPatronCount == 68 && kHammeredPatrons == 12);
        CHECK(kLiveMugSpawns + kLiveBoarSpawns >= kTheftThreshold);
        CHECK(kTheftThreshold == 3 && kKegsToWakeHurley == 3 && kAleTurnInsForTheRun == 3);
        CHECK(kRibblyGossipMenu == 1970 && kFactionAllHostile == 14);
        // The theft trigger's patrons are a subset of the death trigger's.
        for (std::uint32_t entry : { NPC_GRIM_PATRON, NPC_GUZZLING_PATRON, NPC_HAMMERED_PATRON })
            CHECK(!JoinsTheft(entry, 5.f) || TurnsHostileOnPluggerDeath(entry, 5.f));
    }

    // The rest state: everything calm, the door shut.
    void TestRestState()
    {
        BarModel bar;
        CHECK(bar.plugger == PluggerState::Idle && bar.patrons == PatronMood::Calm);
        CHECK(bar.hurley == HurleyState::Hidden && !bar.ribblyHostile);
        CHECK(bar.phalanx == PhalanxState::Dormant && !bar.phalanxActivated);
        CHECK(bar.bar == DungeonKit::State::NotStarted && bar.lovePotion == DungeonKit::State::NotStarted);
        CHECK(bar.Door() == BarDoor::Closed);
    }

    // Path 1: the theft. The counter is Plugger's; the third loot runs the actionlist and resets it.
    void TestTheft()
    {
        BarModel bar;
        CHECK(!bar.Theft() && !bar.Theft());
        CHECK(bar.theftCount == 2 && bar.plugger == PluggerState::Idle && bar.patrons == PatronMood::Calm);
        CHECK(bar.Theft());
        CHECK(bar.theftCount == 0 && bar.plugger == PluggerState::Fighting && bar.patrons == PatronMood::NearPlugger);
        // Nothing else is touched: no Phalanx, no door, no Hurley.
        CHECK(bar.phalanx == PhalanxState::Dormant && bar.Door() == BarDoor::Closed);
        CHECK(bar.hurley == HurleyState::Hidden);
        // Eight sources (6 mugs and 2 boars live) are enough for two full counts.
        BarModel b2;
        int fired = 0;
        for (std::uint32_t i = 0; i < kLiveMugSpawns + kLiveBoarSpawns; ++i)
            fired += b2.Theft() ? 1 : 0;
        CHECK(fired == 2 && b2.theftCount == 2);
        // A dead barkeep counts nothing.
        BarModel dead;
        dead.PluggerDied();
        CHECK(!dead.Theft() && !dead.Theft() && !dead.Theft() && dead.theftCount == 0);
    }

    // Path 1 end: Plugger's death turns the whole room and wakes Phalanx through his faction.
    void TestPluggerDeath()
    {
        BarModel bar;
        bar.Theft();
        bar.Theft();
        bar.Theft();
        bar.PluggerDied();
        CHECK(bar.plugger == PluggerState::Dead && bar.patrons == PatronMood::WholeRoom);
        CHECK(bar.phalanx == PhalanxState::MovingToDoor && bar.phalanxActivated);
        // The door stays shut until Phalanx is dead (ruling 66) or a quest opens it.
        CHECK(bar.Door() == BarDoor::Closed);
        bar.PhalanxArrived();
        CHECK(bar.phalanx == PhalanxState::Active && bar.Door() == BarDoor::Closed);
        bar.PhalanxDied();
        CHECK(bar.phalanx == PhalanxState::Dead && bar.Door() == BarDoor::Open);
        // Killing him without the theft works the same: the whole room, and Phalanx.
        BarModel direct;
        direct.PluggerDied();
        CHECK(direct.patrons == PatronMood::WholeRoom && direct.phalanx == PhalanxState::MovingToDoor);
        // Phalanx already dead before Plugger: nothing comes back.
        BarModel late;
        late.PhalanxDied();
        late.PluggerDied();
        CHECK(late.phalanx == PhalanxState::Dead && late.Door() == BarDoor::Open);
    }

    // Path 2: the kegs. Two taps only advance the phases; the third wakes Hurley once.
    void TestKegs()
    {
        BarModel bar;
        CHECK(!bar.KegUsed() && !bar.KegUsed());
        CHECK(bar.hurley == HurleyState::Hidden && bar.kegsUsed == 2);
        CHECK(bar.KegUsed() && bar.hurley == HurleyState::Awake);
        CHECK(!bar.KegUsed() && bar.hurley == HurleyState::Awake);
        // Hurley changes nothing else in the bar.
        CHECK(bar.plugger == PluggerState::Idle && bar.phalanx == PhalanxState::Dormant);
        CHECK(bar.Door() == BarDoor::Closed);
    }

    // Path 3: Ribbly. The gossip is the only start.
    void TestRibbly()
    {
        BarModel bar;
        CHECK(!bar.ribblyHostile);
        bar.RibblyGossip();
        CHECK(bar.ribblyHostile && bar.plugger == PluggerState::Idle && bar.patrons == PatronMood::Calm);
    }

    // Path 4: Rocknot's ale run. Three turn-ins start the escort; its end is DONE, the door blasted, Phalanx woken.
    void TestAleRun()
    {
        BarModel bar;
        CHECK(!bar.AleTurnIn() && bar.bar == DungeonKit::State::InProgress && bar.aleTurnIns == 1);
        CHECK(!bar.AleTurnIn() && bar.aleTurnIns == 2);
        CHECK(bar.Door() == BarDoor::Closed);
        CHECK(bar.AleTurnIn() && bar.aleEscortRunning && bar.aleTurnIns == 3);
        // While he walks, a further turn-in changes nothing.
        CHECK(!bar.AleTurnIn() && bar.aleTurnIns == 3);
        bar.AleEscortEnds();
        CHECK(!bar.aleEscortRunning && bar.bar == DungeonKit::State::Done);
        CHECK(bar.Door() == BarDoor::Blasted);
        CHECK(bar.phalanx == PhalanxState::MovingToDoor && bar.phalanxActivated);
        CHECK(bar.lovePotion == DungeonKit::State::NotStarted);
        // Once DONE, more turn-ins are ignored and the run never repeats.
        CHECK(!bar.AleTurnIn() && bar.aleTurnIns == 3);
        // The end without a run does nothing.
        BarModel idle;
        idle.AleEscortEnds();
        CHECK(idle.bar == DungeonKit::State::NotStarted && idle.phalanx == PhalanxState::Dormant);
        // After the run, Phalanx dying opens the door fully (blasted -> open).
        bar.PhalanxArrived();
        bar.PhalanxDied();
        CHECK(bar.Door() == BarDoor::Open);
    }

    // Path 5: the love potion. The door opens, TYPE_BAR is DONE, Phalanx stays dormant (the stock quirk).
    void TestLovePotion()
    {
        BarModel bar;
        CHECK(bar.LovePotion());
        CHECK(bar.lovePotion == DungeonKit::State::Done && bar.bar == DungeonKit::State::Done);
        CHECK(bar.Door() == BarDoor::Open);
        CHECK(bar.phalanx == PhalanxState::Dormant && !bar.phalanxActivated);
        // It shuts the ale run out, and cannot run twice or after the run.
        CHECK(!bar.AleTurnIn() && bar.aleTurnIns == 0);
        CHECK(!bar.LovePotion());
        // Mid-run (one turn-in in) the love potion still runs; after the third or the end it does not.
        BarModel mid;
        mid.AleTurnIn();
        CHECK(mid.LovePotion() && mid.Door() == BarDoor::Open);
        BarModel walking;
        walking.AleTurnIn();
        walking.AleTurnIn();
        walking.AleTurnIn();
        CHECK(!walking.LovePotion() && walking.lovePotion == DungeonKit::State::NotStarted);
        walking.AleEscortEnds();
        CHECK(!walking.LovePotion() && walking.Door() == BarDoor::Blasted);
        // Plugger's death after the love potion still wakes Phalanx (the quirk's only way).
        bar.PluggerDied();
        CHECK(bar.phalanx == PhalanxState::MovingToDoor);
    }

    // Phalanx: one activation, whoever asks first; the saved flag; the reload.
    void TestPhalanx()
    {
        BarModel bar;
        CHECK(bar.RequestPhalanxActivation(PhalanxRequest::Gossip));
        CHECK(bar.phalanx == PhalanxState::MovingToDoor && bar.phalanxActivated);
        // A second request, from any source, is a no-op.
        CHECK(!bar.RequestPhalanxActivation(PhalanxRequest::PluggerDeath));
        CHECK(!bar.RequestPhalanxActivation(PhalanxRequest::AleRun));
        bar.PhalanxArrived();
        CHECK(bar.phalanx == PhalanxState::Active);
        CHECK(!bar.RequestPhalanxActivation(PhalanxRequest::Gossip));
        // Arriving before being asked, or twice, does nothing.
        BarModel dormant;
        dormant.PhalanxArrived();
        CHECK(dormant.phalanx == PhalanxState::Dormant);
        // The ale run's request after Plugger's is a no-op (one walk).
        BarModel both;
        both.PluggerDied();
        both.AleTurnIn();
        both.AleTurnIn();
        both.AleTurnIn();
        both.AleEscortEnds();
        CHECK(both.phalanx == PhalanxState::MovingToDoor && both.bar == DungeonKit::State::Done);
        // A reload: dead wins, then the saved activation, else dormant.
        CHECK(PhalanxAfterReload(false, false) == PhalanxState::Dormant);
        CHECK(PhalanxAfterReload(true, false) == PhalanxState::Active);
        CHECK(PhalanxAfterReload(true, true) == PhalanxState::Dead);
        CHECK(PhalanxAfterReload(false, true) == PhalanxState::Dead);
    }

    // The door follows BlackrockDepthsRework::BarDoorState exactly, for every combination of the three inputs.
    void TestDoorMatchesTheInstanceRule()
    {
        for (std::uint32_t barState : { DungeonKit::State::NotStarted, DungeonKit::State::InProgress,
                                        DungeonKit::State::Done })
            for (bool love : { false, true })
                for (bool dead : { false, true })
                {
                    BarModel bar;
                    bar.bar = barState;
                    bar.lovePotion = love ? DungeonKit::State::Done : DungeonKit::State::NotStarted;
                    bar.phalanx = dead ? PhalanxState::Dead : PhalanxState::Dormant;
                    CHECK(bar.Door() == BarDoorState(love, barState, dead));
                }
        // Love potion or Phalanx's death open it; the run alone blasts it; nothing leaves it open and then shut.
        CHECK(BarDoorState(true, DungeonKit::State::Done, false) == BarDoor::Open);
        CHECK(BarDoorState(false, DungeonKit::State::Done, true) == BarDoor::Open);
        CHECK(BarDoorState(false, DungeonKit::State::Done, false) == BarDoor::Blasted);
        CHECK(BarDoorState(false, DungeonKit::State::InProgress, false) == BarDoor::Closed);
    }

    // The triggers are independent of each other (Hurley, Ribbly and the theft never wake Phalanx or open the door).
    void TestTriggersAreIndependent()
    {
        BarModel bar;
        bar.KegUsed();
        bar.KegUsed();
        bar.KegUsed();
        bar.RibblyGossip();
        bar.Theft();
        bar.Theft();
        bar.Theft();
        CHECK(bar.hurley == HurleyState::Awake && bar.ribblyHostile && bar.plugger == PluggerState::Fighting);
        CHECK(bar.phalanx == PhalanxState::Dormant && bar.bar == DungeonKit::State::NotStarted);
        CHECK(bar.Door() == BarDoor::Closed);
    }
}

int main()
{
    TestIdsAndTracking();
    TestHealth();
    TestTimers();
    TestPredicates();
    TestRestState();
    TestTheft();
    TestPluggerDeath();
    TestKegs();
    TestRibbly();
    TestAleRun();
    TestLovePotion();
    TestPhalanx();
    TestDoorMatchesTheInstanceRule();
    TestTriggersAreIndependent();

    return Report("brd_guzzler_test");
}
