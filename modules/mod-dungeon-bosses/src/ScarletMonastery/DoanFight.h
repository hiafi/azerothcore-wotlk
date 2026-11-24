/*
 * mod-dungeon-bosses, Scarlet Monastery D8: Arcanist Doan's hard mode hooks (engine side). WP-D8 owns this file.
 *
 * The hard mode, the Kel'Thuzad Heresy (WP-D8H, heroic only, LIB "Hard mode", handoff section 3.7), fights on D8's
 * AI, boss_arcanist_doan_rework. D8 keeps the whole normal and heroic kit (the seal, the bubble and its anchors,
 * Detonation, Overloaded, the patches, Arcane Explosion, the Marks and their pools, Flamestrike); D8H adds Icy Death,
 * the permanent pools, the Phylactery Shard, Shadow Fissure, the Risen Purged and its numbers through two interfaces,
 * so it never edits D8's .cpp:
 *
 *   DoanHardMode  D8H's per-pull object. D8H registers a factory once, from AddSC_sm_doan_hard_mode:
 *                     SmDoan::RegisterDoanHardMode([](Creature* doan) { return std::make_unique<HeresyFight>(); });
 *                 On every pull that is heroic with DATA_HARD_MODE_DOAN lit, D8 asks the factory for one and calls
 *                 its hooks below; on any other pull none is made. (The instance owns the flag, the kill slot 15 and
 *                 the loot bit; D8 passes hardmode=1 to the pull line.)
 *   DoanFight     what D8's AI offers the hard mode during the pull (passed to every hook): the fight's players, the
 *                 bubble's state and anchors, the count of bubbles, a summon the fight cleans up, the handle list.
 *
 * Hook order: OnEngage after D8's own engage (encounter begun, descriptor set (DescribeExtra first), seal engaged,
 * clocks started); OnUpdate every AI tick in combat after the seal and the arena guard, before D8's beats;
 * OnDamageTaken before D8's own; OnBubbleStart once a bubble's own anchors stand (add the shard here, AddBubbleAnchor);
 * OnAnchorRaised for each of D8's anchors as it is summoned (the hard mode's 10k health); OnBubbleEnd when the bubble
 * breaks (`broken`) or Detonation lands; OnEnd from D8's cleanup (death, evade, reset; `died` on the death).
 * The tuning queries are read at the moment D8 needs them (a nullopt keeps D8's normal / heroic value).
 * DoanIdleHook (RegisterDoanIdleHook): every AI tick out of combat while he is alive and not evading (the red aura
 * after a cold load or a respawn, when no pull has made a DoanHardMode yet).
 *
 * Rider hits (HM1 Icy Death on DN2, DN3, DN3a, DN4): RiderFor(hit) names a spell D8 casts on every player one of its
 * hits lands on (the registry's Rider on its zones; for Flamestrike, on every fight player when the cast completes).
 *
 * Every unit the hard mode summons for the fight should come from DoanFight::Summon, so D8's cleanup despawns it on a
 * wipe, an evade and his death (RB-1). Anything else the hard mode changes on Doan (his health, auras, display) it
 * undoes in OnEnd.
 */

#ifndef MOD_DUNGEON_BOSSES_SM_DOAN_FIGHT_H
#define MOD_DUNGEON_BOSSES_SM_DOAN_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;

namespace SmDoan
{
    class DoanHardMode;

    // D8's hits a hard mode may ride (RiderFor).
    enum class DoanHit : uint8
    {
        Explosion,          // DN2 Arcane Explosion
        MarkBurst,          // DN3 the burst on the others inside 8 yd
        MarkSelf,           // DN3 the marked player's own share
        Pool,               // DN3a a Righteous Fire pool's tick
        Flamestrike,        // DN4 a completed (missed) Flamestrike, every fight player
        Scorched,           // DN1a a Scorched patch's tick
        Detonation,         // DN1 a completed Detonation
    };

    // D8's AI, as the hard mode sees it during one pull.
    class DoanFight
    {
    public:
        virtual ~DoanFight() = default;

        virtual Creature* Doan() = 0;
        virtual bool Heroic() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat): D8H's `.dbtest sm heresy` and
        // its adds reach it through Doan's AI (dynamic_cast<DoanFight*>(doan->AI())).
        virtual DoanHardMode* ActiveHardMode() = 0;

        // The players of the fight: alive, not game masters, on Doan's threat list.
        virtual std::vector<Player*> FightPlayers() = 0;
        // Milliseconds since the pull (D8's own clock).
        virtual uint64 ClockMs() const = 0;

        // DN1: bubbles started this pull (the first is 1), broken (Overloaded) and missed (Detonation landed).
        virtual uint32 BubblesStarted() const = 0;
        virtual uint32 BubblesBroken() const = 0;
        virtual uint32 BubblesMissed() const = 0;
        // DN1: the bubble is up (he is immune and casting Detonation); Overloaded is on him.
        virtual bool BubbleActive() const = 0;
        virtual bool Overloaded() const = 0;
        // DN1: the living anchors of this bubble (D8's and any AddBubbleAnchor unit), none between bubbles.
        virtual std::vector<ObjectGuid> LiveAnchors() const = 0;
        // DN1: one more unit the bubble waits for (HM3's Phylactery Shard): it breaks only when this one dies too. A
        // unit added outside a bubble, dead or already listed is refused (false). D8 does not despawn it: summon it
        // with Summon so the bubble's end and the cleanup take it away, or despawn it in OnBubbleEnd.
        virtual bool AddBubbleAnchor(Creature* unit) = 0;
        // DN1: `n` more anchors at the next bubble (HM5: each Risen Purged that reaches him). `why` goes to the log.
        virtual void AddNextBubbleAnchors(uint32 n, char const* why) = 0;
        // DN1: anchor spot `index` (DoanLogic.h kAnchorSpots, 0-11); the spots this bubble's anchors stand on are
        // AnchorsRaised() first.
        virtual Position AnchorSpot(uint32 index) const = 0;
        virtual uint32 AnchorsRaised() const = 0;

        // A summon of Doan's for the fight: despawned by D8's cleanup (wipe, evade, death). nullptr when refused.
        // `despawnMs` 0: manual despawn.
        virtual Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs = 0) = 0;
        // A registry handle cancelled with the fight (D8's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // One INFO line "sm doan <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // D8H's hard mode for one pull. Every hook has a do-nothing default.
    class DoanHardMode
    {
    public:
        virtual ~DoanHardMode() = default;

        virtual void OnEngage(DoanFight& /*fight*/) { }
        virtual void OnUpdate(DoanFight& /*fight*/, uint32 /*diff*/) { }
        virtual void OnDamageTaken(DoanFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // A bubble is up and its D8 anchors stand (`index`: 1 for the first). Raise the shard here.
        virtual void OnBubbleStart(DoanFight& /*fight*/, uint32 /*index*/) { }
        // One of D8's anchors was just summoned (before OnBubbleStart): its health, its look.
        virtual void OnAnchorRaised(DoanFight& /*fight*/, Creature* /*anchor*/) { }
        // The bubble `index` ended: `broken` (every anchor dead: Overloaded) or not (Detonation landed). D8 has
        // already despawned its own anchors. After the first: Shadow Fissure; after the second: the Risen Purged.
        virtual void OnBubbleEnd(DoanFight& /*fight*/, uint32 /*index*/, bool /*broken*/) { }
        // Death (died), evade or reset. Undo every change made to Doan here (health, auras, display).
        virtual void OnEnd(DoanFight& /*fight*/, bool /*died*/) { }

        // Extra entries for the bots' boss data (the Risen Purged ahead of Doan, the shard after the anchors, Icy
        // Death on the dispel list); D8's entries are already in `d`. Called once, at the engage.
        virtual void DescribeExtra(DoanFight& /*fight*/, BossMechanics::Descriptor& /*d*/) { }

        // A spell D8 casts (triggered) on each player `hit` lands on; 0: none.
        virtual uint32 RiderFor(DoanFight const& /*fight*/, DoanHit /*hit*/) const { return 0; }

        // Tuning (nullopt: D8's heroic value). The bubble's cadence after the first (heroic 30 s; the hard mode's
        // 35 s), the Marks' cadence after the first (heroic 20 s; 30 s), a pool's life (heroic 30 s; 0 = the rest of
        // the fight), Detonation's percent (heroic 130; 200).
        virtual std::optional<uint32> BubbleEveryMs(DoanFight const& /*fight*/) const { return std::nullopt; }
        virtual std::optional<uint32> MarkEveryMs(DoanFight const& /*fight*/) const { return std::nullopt; }
        virtual std::optional<uint32> PoolLifeMs(DoanFight const& /*fight*/) const { return std::nullopt; }
        virtual std::optional<float> DetonationPct(DoanFight const& /*fight*/) const { return std::nullopt; }
        // Detonation's length (D8's DetonationCastMsFor: 10 s, heroic 14 s): the script's clock lands the blast when it
        // runs out. The bar players see is a spell with its own DBC cast time (D8's 212671 is 10 s, 212687 the heroic
        // 14 s; a hard mode with no override gets heroic's): a hard mode that changes the
        // length also names a bar spell of that length (DetonationBarSpell; 0 keeps D8's), or the bar and the blast
        // disagree.
        virtual std::optional<uint32> DetonationCastMs(DoanFight const& /*fight*/) const { return std::nullopt; }
        virtual uint32 DetonationBarSpell(DoanFight const& /*fight*/) const { return 0; }
    };

    using DoanHardModeFactory = std::function<std::unique_ptr<DoanHardMode>(Creature* doan)>;
    // Out of combat: called every AI tick while Doan is alive, not engaged and not evading (no DoanFight then; the
    // hook reads the instance itself). D8H keeps the Heresy's red aura on him after a cold load or a respawn.
    using DoanIdleHook = std::function<void(Creature* doan)>;

    // D8H, from its AddSC_ function (once; a second call replaces the first).
    void RegisterDoanHardMode(DoanHardModeFactory factory);
    void RegisterDoanIdleHook(DoanIdleHook hook);
    // D8, on a heroic pull with DATA_HARD_MODE_DOAN lit: nullptr when nothing is registered.
    std::unique_ptr<DoanHardMode> CreateDoanHardMode(Creature* doan);
}

#endif
