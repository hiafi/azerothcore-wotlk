/*
 * mod-dungeon-bosses, Scholomance S1: Jandice Barov (10503). Build spec SC 546-601 (docs/dungeons/
 * scholomance-rework.md), design SC 380-545; handoff section 3.4 rows JB, section 3.5 row S1, section 3.8 (the 21 yd
 * east aisle), section 7 #12 (lanes on the real aisle). Replaces SmartAI 10503 (Curse of Blood, Banish and Summon
 * Illusions are gone; the death emote and the journal 26096 are kept here).
 *
 * The unifying rule: the journal marks real magic. Every real reflection holds it; the copies and the heroic decoys
 * do not; the real Jandice always does.
 *
 *   JB1 Blood Sigil   reflections on the floor, each bursting an 8 yd circle around itself. Normal: 3 at random
 *                     points at least 6 yd from every player, 5 s, 40%. Heroic: the 8 point grid that covers the aisle
 *                     (kJandiceSigilGrid) plus the alcove, one grid reflection empty-handed: its circle is a Decoy()
 *                     (drawn, harmless, absent from the bot view), 6 s, 60%.
 *   JB2 Shell Game    at 25 s, then every 50 s start to start: she vanishes (1 s) and stands in a ring of copies (8 /
 *                     15) 12 yd around where she stood (moved into the aisle). She does nothing while hidden; only a
 *                     direct hit finds her (area damage and old damage over time deal her nothing in the game).
 *   JB3 Shatter       a direct hit on a copy shatters it: 25% / 40% Shadow to the attacker (a pet's owner). Area
 *                     damage never touches a copy (every copy takes 0 from everything). A direct hit (JandiceLogic.h
 *                     CountsAsDirectHit, R-A B-1 and the provisional Q3 calls): from a player or a player's pet (no
 *                     totem, no guardian), on the figure the caster has selected, a melee swing or a harmful damaging
 *                     spell aimed at it (no area spell, no chain, no proc landing on another figure).
 *   JB4 Unmasked      damage taken +20% for 8 s, on the hit that ends the game (heroic: the second find; provisional
 *                     Q4 call kHeroicUnmaskAtEnd).
 *   JB5 Failed game   at 20 s / 25 s every copy still standing bursts an 8 yd circle (5 s / 6 s, 40% / 60%), then
 *                     dissolves; she fights again at once.
 *   JB6 Bloodlines    6 yd lanes tiling the aisle frame (kJandiceAisle, 55.5 x 21), a reflection at each lane's end
 *                     on one wall, plus a circle filling the alcove. Normal: across the aisle (10 lanes), one lane
 *                     unmarked and empty (safe). Heroic: either axis (4 or 10 lanes), every lane marked, one
 *                     reflection empty-handed (its lane a decoy, safe). 5 s, 50% / 70%.
 *   JB7 Shuffle (H)   every 5 s in the game, 3 pairs of figures swap places (she can be one), a 1 s thread first.
 *   JB8 Blood Price (H) every 3 s in the game, 4% Shadow on every player.
 *   JB9 Curse of Blood  2 s cast at 3 to 11 s, then every 30 s, everyone within 10 yd: physical damage taken +20%,
 *                     30 s, Curse (on the dispel list). Never in the game.
 *
 * Cast order (JandiceLogic.h JandiceClock): one outside cast every 10 s, alternating sigils and lines (8 s, 18 s), the
 * game at 25 s; after a game, sigils 6 s after it ends. A due game waits for the outside cast before it to resolve.
 *
 * Registry: every zone is on her encounter. Bots: the reflections on the ignore list, Curse of Blood on the dispel
 * list; in the game each damage dealer and tank guesses (provisional Q5 call: a random figure, then kBotFindChance
 * per second to switch to her; OnlyFor target entries per player), with no guid to follow. Arena: KS's
 * JandiceArena() with LeashOptions (no grips). Timers and looks run on _timers (never paused by a cast bar).
 *
 * Every firing logs one "scholo jandice <mechanic>" line (module.dungeonbosses, INFO). `.dbtest scholo jandice ...`
 * fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "Group.h"
#include "JandiceLogic.h"
#include "Map.h"
#include "MechanicRegistry.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TaskScheduler.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <list>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoJandice;

namespace
{
    char constexpr kBoss[] = "jandice";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogJb(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    uint32 RandomBelow(uint32 n)
    {
        return n ? urand(0, n - 1) : 0;
    }

    float Rand01()
    {
        return frand(0.f, 1.f);
    }

    // A live registry mechanic (not finished, not cancelled).
    bool Live(Map const* map, BossMechanics::MechanicHandle handle)
    {
        BossMechanics::Registry const* registry = handle ? Mechanic::Read(map) : nullptr;
        BossMechanics::ActiveMechanic const* m = registry ? registry->Find(handle.id) : nullptr;
        return m && !m->finished && !m->cancelled;
    }

    // Who struck a figure (Q3: totems and guardians never count unless kTotemsAndGuardiansCount).
    HitSource SourceOf(Unit const* unit)
    {
        if (!unit)
            return HitSource::Other;
        if (unit->IsPlayer())
            return HitSource::Player;
        if (unit->IsControlledByPlayer() && !unit->IsCharmed()
            && (unit->IsPet() || (kTotemsAndGuardiansCount && (unit->IsTotem() || unit->IsGuardian()))))
            return HitSource::Pet;
        return HitSource::Other;
    }

    // The struck figure is the caster's selection: a player's target; a pet's own victim or its owner's target.
    bool OnSelected(Unit const* caster, Unit const* struck)
    {
        if (!caster || !struck)
            return false;
        if (caster->IsPlayer())
            return caster->GetTarget() == struck->GetGUID();
        if (caster->GetVictim() == struck)
            return true;
        Unit const* owner = caster->GetCharmerOrOwnerPlayerOrPlayerItself();
        return owner && owner != caster && owner->GetTarget() == struck->GetGUID();
    }

    // A spell that deals damage: direct, weapon, drain, or over time.
    bool DealsDamage(SpellInfo const* spell)
    {
        for (SpellEffectInfo const& eff : spell->GetEffects())
        {
            switch (eff.Effect)
            {
                case SPELL_EFFECT_SCHOOL_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL:
                case SPELL_EFFECT_NORMALIZED_WEAPON_DMG:
                case SPELL_EFFECT_WEAPON_PERCENT_DAMAGE:
                case SPELL_EFFECT_HEALTH_LEECH:
                case SPELL_EFFECT_ENVIRONMENTAL_DAMAGE:
                    return true;
                case SPELL_EFFECT_APPLY_AURA:
                    if (eff.ApplyAuraName == SPELL_AURA_PERIODIC_DAMAGE
                        || eff.ApplyAuraName == SPELL_AURA_PERIODIC_LEECH
                        || eff.ApplyAuraName == SPELL_AURA_PERIODIC_DAMAGE_PERCENT)
                        return true;
                    break;
                default:
                    break;
            }
        }
        return false;
    }

    // A spell that chains to more targets (Cleave, Multi-Shot, Chain Lightning): never a direct hit.
    bool Chains(SpellInfo const* spell)
    {
        for (SpellEffectInfo const& eff : spell->GetEffects())
            if (eff.ChainTarget > 1)
                return true;
        return false;
    }

    // JB2 / JB3: a direct hit on `struck` (CountsAsDirectHit): a melee swing (`spell` null) or a spell.
    bool DirectHit(Unit const* caster, Unit const* struck, SpellInfo const* spell)
    {
        HitFacts h;
        h.source = SourceOf(caster);
        h.onSelected = OnSelected(caster, struck);
        h.melee = !spell;
        if (spell)
        {
            h.harmful = !spell->IsPositive();
            h.area = spell->IsAffectingArea();
            h.needsUnitTarget = spell->NeedsExplicitUnitTarget();
            h.chain = Chains(spell);
            h.damage = DealsDamage(spell);
        }
        return CountsAsDirectHit(h);
    }

    // A hit from the group's side that may count as a find (the spell's own check comes in SpellHit).
    bool MayFind(Unit const* caster, Unit const* struck)
    {
        return SourceOf(caster) != HitSource::Other && (!kHitsOnSelectedTargetOnly || OnSelected(caster, struck));
    }

    // A unit on the aisle floor at `at` (the floor height there, else the measured floor).
    Position FloorPosition(WorldObject const* ref, Vec2 at, float orientation)
    {
        float z = ref->GetMapHeight(at.x, at.y, kJandiceFloorZ + 2.f);
        if (z <= INVALID_HEIGHT + 1.f || std::fabs(z - kJandiceFloorZ) > 3.f)
            z = kJandiceFloorZ;
        return DungeonKit::ToPosition(at, z, orientation);
    }

    // A reflection or a copy plays `look` and goes.
    void Dissolve(Map* map, ObjectGuid guid, uint32 look)
    {
        Creature* unit = map && guid ? map->GetCreature(guid) : nullptr;
        if (!unit || !unit->IsAlive())
            return;
        unit->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE);
        unit->RemoveAurasDueToSpell(SPELL_JB_BLOOD_BEAM);
        if (look)
            unit->CastSpell(unit, look, true);
        unit->DespawnOrUnsummon(Ms(kDissolveMs));
    }
}

// Jandice Barov 10503
struct boss_jandice_barov_rework : public BossAI
{
    explicit boss_jandice_barov_rework(Creature* creature)
        : BossAI(creature, BOSS_JANDICE), _arena(JandiceArena(), LeashOptions(kBoss)) { }

    // ---------------------------------------------------------------------------------------------------------------
    // Encounter
    // ---------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_JANDICE;
        Mechanic::BeginEncounter(me, options);
        Describe();

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _arena.Engage(me);
        ScheduleCurse(urand(kCurseFirstMinMs, kCurseFirstMaxMs));
        LogJb("engage", Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", Heroic() ? 1 : 0,
            me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
        LogJb("evade");
    }

    void JustDied(Unit* killer) override
    {
        Cleanup();
        BossAI::JustDied(killer);   // despawns the copies and the reflections (her summons)
        Talk(EMOTE_JANDICE_JOURNAL);
        DoCastSelf(SPELL_SUMMON_JOURNAL, true);
        LogJb("death");
    }

    // Her copies and reflections never zone in: they only stand where she puts them.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // JB2: in the game she takes nothing but the hit that finds her (a melee swing; a spell aimed at her lands in
    // SpellHit, after its damage, so that one hit deals 0). Area damage and old damage over time deal 0 to every
    // figure alike, so neither numbers nor health bars give her away.
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (!_game.active || _dealingFind)
            return;
        if (type == DIRECT_DAMAGE && FindsCount() && DirectHit(attacker, me, nullptr))
        {
            Found(attacker, "melee");
            return;
        }
        // A spell's damage lands before SpellHit decides whether it found her: held, and dealt there if it did
        // (kSpellFindDealsDamage).
        if (type == SPELL_DIRECT_DAMAGE && damage && attacker && FindsCount() && MayFind(attacker, me))
            _heldHit = { attacker->GetGUID(), damage, mask };
        damage = 0;
    }

    void SpellHit(Unit* caster, SpellInfo const* spell) override
    {
        BossAI::SpellHit(caster, spell);
        HeldHit const held = _heldHit;
        _heldHit = HeldHit();
        if (!_game.active || !spell || !FindsCount() || !DirectHit(caster, me, spell))
            return;
        Found(caster, "spell");
        if (kSpellFindDealsDamage && caster && held.damage && held.attacker == caster->GetGUID() && me->IsAlive())
        {
            _dealingFind = true;
            Unit::DealDamage(caster, me, held.damage, nullptr, SPELL_DIRECT_DAMAGE, held.mask, spell, false);
            _dealingFind = false;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        // Looks, reflections, the curse's cadence and the game's steps run every update, also while she casts (a
        // cast bar never pauses them) and out of combat (for .dbtest).
        _timers.Update(diff);
        _heldHit = HeldHit();
        if (!me->IsEngaged())
            return;

        if (_game.active)
        {
            _clock.Update(diff, CastsLive());   // the 50 s to the next game runs on; nothing else is due in a game
            UpdateGame(diff);
            if (!me->IsInCombat())
            {
                EnterEvadeMode(EVADE_REASON_NO_HOSTILES);
                return;
            }
            _arena.Update(me, diff);
            return;
        }

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off her arena, or nobody on it for 10 s: evading

        // The clock runs only once the gates pass (R-A S-8): a cast never comes due and is dropped while she has no
        // victim, and a game is never marked started without starting.
        JandiceCast const due = _clock.Update(diff, CastsLive());
        switch (due)
        {
            case JandiceCast::BloodSigil:
                BloodSigil();
                break;
            case JandiceCast::Bloodlines:
                Bloodlines(std::nullopt);
                break;
            case JandiceCast::ShellGame:
                StartGame("timer");
                break;
            default:
                break;
        }

        if (_game.active || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---------------------------------------------------------------------------------------------------------------
    // Mechanics (public: the copies and the .dbtest subcommands call them)
    // ---------------------------------------------------------------------------------------------------------------

    // JB1: reflections draw their sigils.
    void BloodSigil()
    {
        bool const heroic = Heroic();
        uint32 const warn = kSigilWarnMs(heroic);
        float const pct = kSigilPct(heroic);
        Talk(EMOTE_JANDICE_SIGILS);
        uint32 placed = 0;
        uint32 decoys = 0;
        if (heroic)
        {
            std::size_t const decoy = RandomBelow(uint32(kJandiceSigilGrid.size()));
            for (std::size_t i = 0; i < kJandiceSigilGrid.size(); ++i)
                if (SigilAt(kJandiceSigilGrid[i], i == decoy, warn, pct, kTagBloodSigil, SPELL_JB_BLOOD_SIGIL,
                    kGridSigilRadius))
                {
                    ++placed;
                    decoys += i == decoy ? 1 : 0;
                }
            // The alcove off the aisle (6 x 14 yd) burns too: the decoy stays the only safe ground.
            if (SigilAt(kJandiceAlcoveSigil, false, warn, pct, kTagBloodSigil))
                ++placed;
        }
        else
        {
            std::vector<Vec2> const points = PickSigilPoints(kJandiceAisle, PlayerPoints(), kNormalSigils,
                kSigilMinFromPlayers, kSigilMinApart, kSigilFloorInset, Rand01);
            for (Vec2 const& at : points)
                if (SigilAt(at, false, warn, pct, kTagBloodSigil))
                    ++placed;
        }
        LogJb("blood-sigil", Acore::StringFormat("heroic={} circles={} decoys={} warn={}ms pct={:.0f}",
            heroic ? 1 : 0, placed, decoys, warn, pct));
    }

    // JB6: the lanes. `forceAlongX` (a .dbtest caller) picks the axis; else normal runs across the aisle and heroic
    // picks either axis.
    void Bloodlines(std::optional<bool> forceAlongX)
    {
        bool const heroic = Heroic();
        bool const alongX = forceAlongX ? *forceAlongX : (heroic && urand(0, 1) == 1);
        bool const farEnd = urand(0, 1) == 1;
        uint32 const warn = kLinesWarnMs(heroic);
        float const pct = kLinesPct(heroic);
        BossMechanics::Axis const axis = alongX ? BossMechanics::Axis::X : BossMechanics::Axis::Y;
        Talk(EMOTE_JANDICE_BLOODLINES);

        std::vector<LaneSlot> slots;
        {
            BossMechanics::LaneBuilder lanes = Mechanic::RoomFrame(me, DungeonKit::ToRoomFrame(kJandiceAisle,
                kJandiceFloorZ));
            // Whole lanes tile the axis (R-A S-9): 9 of 6.17 yd across, 4 of 5.25 yd along.
            lanes.ExceptOne(LaneWidthFor(alongX ? kJandiceAisle.sizeY : kJandiceAisle.sizeX, kLaneWidth), Ms(warn),
                axis);
            if (heroic)
                lanes.DecoyFree();
            lanes.Each([pct](BossMechanics::MechanicRef& lane)
            {
                lane.Damage(pct).Spell(SPELL_JB_BLOODLINES).Tag(kTagBloodlines);
            });
            for (BossMechanics::MechanicHandle const& h : lanes.Handles())
                Track(h);

            BossMechanics::Registry const* reg = BossMechanics::Registry::Get(me->GetMap());
            if (BossMechanics::LaneSet const* set = reg ? reg->FindLaneSet(lanes.Id()) : nullptr)
            {
                for (BossMechanics::LaneRect const& r : set->rects)
                    slots.push_back({ r.offset, r.width, false });
                if (!set->freeLanes.empty())
                    slots.push_back({ set->freeLanes.back().offset, set->freeLanes.back().width, true });
            }
        }   // the builder commits every lane here

        // A reflection at each lane's end on one wall: the real ones hold the journal; the free lane has none on
        // normal and an empty-handed one on heroic.
        std::vector<float> const centers = LaneMarkCenters(slots);
        float const facing = LaneFacing(kJandiceAisle, alongX, farEnd);
        std::vector<std::pair<ObjectGuid, bool>> reflections;     // guid, decoy
        for (std::size_t i = 0; i < slots.size(); ++i)
        {
            if (slots[i].free && !heroic)
                continue;
            Vec2 const at = LaneEndPoint(kJandiceAisle, alongX, centers[i], farEnd, kLaneEndInset);
            if (Creature* r = SpawnReflection(at, facing, !slots[i].free, warn))
            {
                r->CastSpell(r, SPELL_JB_BLOOD_BEAM, true);
                reflections.emplace_back(r->GetGUID(), slots[i].free);
            }
        }
        // The alcove (outside the frame) fills with blood too, so the free lane stays the only safe ground.
        bool const alcove = SigilAt(kJandiceAlcoveSigil, false, warn, pct, kTagBloodlinesAlcove,
            SPELL_JB_BLOODLINES);

        // The lanes burst together: every lane reflection dissolves then (the decoy pops harmlessly).
        Map* map = me->GetMap();
        _timers.Schedule(Ms(warn), [map, reflections](TaskContext /*ctx*/)
        {
            for (auto const& [g, decoy] : reflections)
                Dissolve(map, g, decoy ? SPELL_JB_FAKE_POP : SPELL_JB_SIGIL_BURST);
        });
        LogJb("bloodlines", Acore::StringFormat("heroic={} axis={} lanes={} wall={} reflections={} alcove={} "
            "warn={}ms pct={:.0f}", heroic ? 1 : 0, alongX ? "along" : "across", slots.size(), farEnd ? "far" : "near",
            reflections.size(), alcove ? 1 : 0, warn, pct));
    }

    // JB2: she vanishes and stands in a ring of copies. False when the game is already on.
    bool StartGame(char const* why)
    {
        if (_game.active)
            return false;
        bool const heroic = Heroic();
        _game = GameState();
        _game.active = true;
        _game.vanishing = true;
        _gameClock.Start(heroic);
        if (!_clock.InGame())
            _clock.GameStartedByHand();
        _mirrorMs = 0;

        me->InterruptNonMeleeSpells(false);
        Talk(EMOTE_JANDICE_SHELL_GAME);
        DoCastSelf(SPELL_JB_SHELL_GAME, true);
        // Nobody keeps swinging at the spot she left; the group's damage over time goes with her.
        me->RemoveAllAttackers();
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->GetMotionMaster()->Clear(false);
        me->GetMotionMaster()->MoveIdle();
        me->StopMoving();
        StripGroupAuras();
        ClearRaidIcons();

        // The ring: where she stood, moved into the aisle; her place in it is random.
        uint32 const copies = kCopies(heroic);
        Vec2 const center = RingCenter(kJandiceAisle, DungeonKit::PlaneOf(me), kRingRadius, kRingWallInset);
        std::vector<Vec2> const ring = RingPoints(kJandiceAisle, center, kRingRadius, copies + 1,
            frand(0.f, DungeonKit::kTwoPi), kRingWallInset);
        std::size_t const mine = RandomBelow(uint32(ring.size()));

        _timers.Schedule(Ms(kVanishLookMs), [this](TaskContext /*ctx*/)
        {
            if (_game.active)
                me->SetVisible(false);
        });
        _timers.Schedule(Ms(kVanishMs), [this, ring, mine, center](TaskContext /*ctx*/)
        {
            if (!_game.active)
                return;
            Position const spot = FloorPosition(me, ring[mine], DungeonKit::BearingTo(ring[mine], center));
            me->NearTeleportTo(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), spot.GetOrientation());
            me->SetVisible(true);
            DoCastSelf(SPELL_JB_REFLECTION_POOF, true);     // every copy poofs in as it appears; so does she
            for (std::size_t i = 0; i < ring.size(); ++i)
                if (i != mine)
                    SpawnCopy(ring[i], DungeonKit::BearingTo(ring[i], center));
            Mirror();
            RollGuesses("ring");
            _game.vanishing = false;
            _game.graceMs = kFindGraceMs;
            LogJb("shell-game-ring", Acore::StringFormat("copies={} center=({:.1f}, {:.1f}) her=({:.1f}, {:.1f})",
                _copies.size(), center.x, center.y, ring[mine].x, ring[mine].y));
        });
        LogJb("shell-game", Acore::StringFormat("why={} heroic={} copies={} limit={}ms", why, heroic ? 1 : 0, copies,
            _gameClock.LimitMs()));
        return true;
    }

    // JB3: a copy took a direct hit. Its attacker (a pet's owner) takes the shatter; the copy is gone.
    void CopyStruck(Creature* copy, Unit* attacker, char const* how)
    {
        if (!copy || !FindsCount())
            return;
        auto it = std::find(_copies.begin(), _copies.end(), copy->GetGUID());
        if (it == _copies.end())
            return;
        _copies.erase(it);
        Unit* victim = attacker ? attacker->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
        if (!victim)
            victim = attacker;
        copy->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE);
        copy->CastSpell(copy, SPELL_JB_SHATTER_LOOK, true);
        if (victim && victim->IsAlive())
            copy->CastSpell(victim, SPELL_JB_SHATTER, true);
        copy->DespawnOrUnsummon(Ms(kDissolveMs));
        LogJb("shatter", Acore::StringFormat("by={} how={} hit={} left={}", attacker ? attacker->GetName() : "?", how,
            victim ? victim->GetName() : "?", _copies.size()));
    }

    // JB7 (heroic): up to three pairs swap places after a 1 s thread (they run to each other's spots). With
    // `forceHer` (the shuffle after the first find) she is in the first pair, and that pair blinks as it trades places
    // instead of running, so nobody keeps her selected through it.
    void Shuffle(bool forceHer, char const* why)
    {
        if (forceHer)
        {
            // R-A S-7: she trades places now, even mid-run: a swap she was in is dropped and she stops where she is.
            std::erase_if(_pendingSwaps, [this](Swap const& swap)
            {
                return swap.a == me->GetGUID() || swap.b == me->GetGUID();
            });
            me->GetMotionMaster()->Clear(false);
            me->GetMotionMaster()->MoveIdle();
            me->StopMoving();
        }
        std::vector<Creature*> const figures = Figures(forceHer);
        std::optional<std::size_t> forced;
        if (forceHer)
            for (std::size_t i = 0; i < figures.size(); ++i)
                if (figures[i] == me)
                    forced = i;
        auto const pairs = ShufflePairs(figures.size(), kShufflePairs, forced, RandomBelow);
        std::vector<Swap> swaps;
        bool mine = false;
        for (std::size_t i = 0; i < pairs.size(); ++i)
        {
            Creature* a = figures[pairs[i].first];
            Creature* b = figures[pairs[i].second];
            a->CastSpell(b, SPELL_JB_BLOOD_THREAD, true);
            swaps.push_back({ _nextSwapId++, a->GetGUID(), b->GetGUID(), forced && i == 0 });
            mine = mine || a == me || b == me;
        }
        if (swaps.empty())
            return;
        // Paired figures sit out of new pairs until their swap lands.
        _pendingSwaps.insert(_pendingSwaps.end(), swaps.begin(), swaps.end());
        _timers.Schedule(Ms(kThreadMs), [this, swaps](TaskContext /*ctx*/)
        {
            for (Swap const& swap : swaps)
                if (_game.active && IsPending(swap.id))
                    TradePlaces(swap);
                else
                    DropPending(swap.id);
        });
        LogJb("shuffle", Acore::StringFormat("why={} pairs={} her={} figures={}", why, swaps.size(), mine ? 1 : 0,
            figures.size()));
    }

    // JB8 (heroic): 4% Shadow on every player.
    void BloodPrice()
    {
        DoCastSelf(SPELL_JB_BLOOD_PRICE, true);
        LogJb("blood-price", Acore::StringFormat("pct={:.0f}", kBloodPricePct));
    }

    // JB9: the real 2 s cast. False when it did not start.
    bool CastCurse()
    {
        if (_game.active || me->HasUnitState(UNIT_STATE_CASTING))
            return false;
        if (me->CastSpell(me, SPELL_JB_CURSE_OF_BLOOD, false) != SPELL_CAST_OK)
        {
            LogJb("curse-of-blood", "skipped=cast-failed");
            return false;
        }
        LogJb("curse-of-blood", Acore::StringFormat("cast={}ms radius={:.0f}", kCurseCastMs, kCurseRadius));
        return true;
    }

    // JB5: the hunt ran out. Every copy still standing bursts a circle, then dissolves; she fights again.
    void FailGame(char const* why)
    {
        if (!_game.active)
            return;
        bool const heroic = Heroic();
        uint32 const warn = kFailedWarnMs(heroic);
        float const pct = kFailedPct(heroic);
        EndDisguise();
        Map* map = me->GetMap();
        uint32 circles = 0;
        for (ObjectGuid const& g : _copies)
        {
            Creature* copy = map->GetCreature(g);
            if (!copy || !copy->IsAlive())
                continue;
            copy->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE);
            BossMechanics::MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(copy), kSigilRadius,
                Ms(warn));
            ref.Damage(pct).Spell(SPELL_JB_BLOOD_SIGIL).Tag(kTagFailedGame)
                .OnResolve([map, g](BossMechanics::ResolveResult const&) { Dissolve(map, g, SPELL_JB_SIGIL_BURST); });
            Track(ref.Handle());
            ++circles;
        }
        _copies.clear();
        _timers.Schedule(Ms(warn), [this](TaskContext /*ctx*/)
        {
            _clock.GameEnded();
            LogJb("shell-game-end", "after=failed");
        });
        LogJb("failed-game", Acore::StringFormat("why={} heroic={} circles={} warn={}ms pct={:.0f}", why,
            heroic ? 1 : 0, circles, warn, pct));
    }

    // Registry handles on her encounter: cancelled with her cleanup; a due game waits for them.
    void Track(BossMechanics::MechanicHandle handle)
    {
        if (!handle)
            return;
        Map const* map = me->GetMap();
        std::erase_if(_live, [map](BossMechanics::MechanicHandle const& h) { return !Live(map, h); });
        _live.push_back(handle);
    }

    bool CastsLive() const
    {
        Map const* map = me->GetMap();
        return std::any_of(_live.begin(), _live.end(),
            [map](BossMechanics::MechanicHandle const& h) { return Live(map, h); });
    }

    std::string StateText() const
    {
        return Acore::StringFormat("game {} (vanishing {}, finds {}, copies {}, {}/{} ms), next {} in {} ms, game in "
            "{} ms, live zones {}", _game.active ? 1 : 0, _game.vanishing ? 1 : 0, _game.finds, _copies.size(),
            _gameClock.ElapsedMs(), _gameClock.LimitMs(), CastName(_clock.Next()), _clock.UntilOutsideMs(),
            _clock.UntilGameMs(), CastsLive() ? 1 : 0);
    }

    bool InGame() const { return _game.active; }
    bool Engaged() const { return me->IsEngaged(); }

    // `.dbtest`: the find, as if `who` had hit her.
    void ForceFind(Unit* who)
    {
        if (FindsCount())
            Found(who, "test");
    }

    bool Heroic() const
    {
        return DungeonKit::IsHeroicMap(me);
    }

private:
    struct GameState
    {
        bool active = false;
        bool vanishing = false;
        uint32 finds = 0;
        uint32 graceMs = 0;
    };

    struct Swap
    {
        uint32 id = 0;
        ObjectGuid a;
        ObjectGuid b;
        bool blink = false;
    };

    // A spell's damage on her in the game, held until SpellHit says whether it found her.
    struct HeldHit
    {
        ObjectGuid attacker;
        uint32 damage = 0;
        SpellSchoolMask mask = SPELL_SCHOOL_MASK_NONE;
    };

    // JB7: a pair trades places: a run to each other's spots, or (blink) both gone for a moment and back swapped.
    // The pair stays out of new pairs until it has landed.
    void TradePlaces(Swap const& swap)
    {
        Map* map = me->GetMap();
        Creature* a = map->GetCreature(swap.a);
        Creature* b = map->GetCreature(swap.b);
        if (!a || !b || !a->IsAlive() || !b->IsAlive())
        {
            DropPending(swap.id);
            return;
        }
        Position const pa = a->GetPosition();
        Position const pb = b->GetPosition();
        uint32 const id = swap.id;
        if (!swap.blink)
        {
            float const speed = std::max(kSwapMinSpeed, pa.GetExactDist2d(&pb) * 1000.f / float(kSwapMs));
            a->GetMotionMaster()->MoveCharge(pb.GetPositionX(), pb.GetPositionY(), pb.GetPositionZ(), speed);
            b->GetMotionMaster()->MoveCharge(pa.GetPositionX(), pa.GetPositionY(), pa.GetPositionZ(), speed);
            _timers.Schedule(Ms(kSwapMs + kSwapLandSlackMs), [this, id](TaskContext /*ctx*/) { DropPending(id); });
            return;
        }
        for (Creature* c : { a, b })
        {
            c->CastSpell(c, SPELL_JB_REFLECTION_POOF, true);
            c->SetVisible(false);
        }
        // R-A S-6: nothing she wore before the blink gives her away after it.
        if (a == me || b == me)
        {
            StripGroupAuras();
            ClearRaidIcons();
        }
        a->NearTeleportTo(pb.GetPositionX(), pb.GetPositionY(), pb.GetPositionZ(), pb.GetOrientation());
        b->NearTeleportTo(pa.GetPositionX(), pa.GetPositionY(), pa.GetPositionZ(), pa.GetOrientation());
        _timers.Schedule(Ms(kBlinkMs), [this, map, swap](TaskContext /*ctx*/)
        {
            for (ObjectGuid const& g : { swap.a, swap.b })
                if (Creature* c = map->GetCreature(g))
                    c->SetVisible(true);
            DropPending(swap.id);
            RollGuesses("blink");   // every selection dropped with her: the bots guess again
        });
    }

    bool IsPending(uint32 id) const
    {
        return std::any_of(_pendingSwaps.begin(), _pendingSwaps.end(), [id](Swap const& s) { return s.id == id; });
    }

    bool InPendingSwap(ObjectGuid g) const
    {
        return std::any_of(_pendingSwaps.begin(), _pendingSwaps.end(),
            [g](Swap const& s) { return s.a == g || s.b == g; });
    }

    void DropPending(uint32 id)
    {
        std::erase_if(_pendingSwaps, [id](Swap const& s) { return s.id == id; });
    }

    // Harmful auras a player or pet put on her (the vanish, the heroic blink).
    void StripGroupAuras()
    {
        me->RemoveAppliedAuras([](AuraApplication const* app)
        {
            ObjectGuid const caster = app->GetBase()->GetCasterGUID();
            return !app->IsPositive() && (caster.IsPlayer() || caster.IsPet());
        });
    }

    // R-A S-6: no raid target icon stays on her through the game (hand marks, or a bot's `mark rti`).
    void ClearRaidIcons()
    {
        ObjectGuid const mine = me->GetGUID();
        std::vector<Group*> groups;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                if (Group* group = player->GetGroup())
                    if (std::find(groups.begin(), groups.end(), group) == groups.end())
                        groups.push_back(group);
        for (Group* group : groups)
            for (uint8 i = 0; i < TARGETICONCOUNT; ++i)
                if (group->GetTargetIcon(i) == mine)
                    group->SetTargetIcon(i, ObjectGuid::Empty, ObjectGuid::Empty);
    }

    // ---------------------------------------------------------------------------------------------------------------
    // Q5: the bots' guesses. Every player in the map gets one (only bots read the descriptor): a figure picked at
    // random when the ring forms and after the heroic blink, then every kBotGuessEveryMs a kBotFindChance switch to
    // her; a guess that shattered picks again. Published as OnlyFor target entries per player (damage dealers and
    // tanks; healers get none and keep healing).
    // ---------------------------------------------------------------------------------------------------------------
    ObjectGuid RandomFigure() const
    {
        std::vector<ObjectGuid> standing;
        if (me->IsAlive())
            standing.push_back(me->GetGUID());
        for (ObjectGuid const& g : _copies)
            if (Creature const* copy = me->GetMap()->GetCreature(g))
                if (copy->IsAlive())
                    standing.push_back(g);
        return standing.empty() ? ObjectGuid::Empty : standing[RandomBelow(uint32(standing.size()))];
    }

    bool Standing(ObjectGuid g) const
    {
        if (g == me->GetGUID())
            return me->IsAlive();
        if (std::find(_copies.begin(), _copies.end(), g) == _copies.end())
            return false;
        Creature const* copy = me->GetMap()->GetCreature(g);
        return copy && copy->IsAlive();
    }

    void RollGuesses(char const* why)
    {
        if (!_game.active)
            return;
        _guesses.clear();
        _guessMs = 0;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player const* player = ref.GetSource())
                if (player->IsAlive() && !player->IsGameMaster())
                    _guesses.emplace_back(player->GetGUID(), RandomFigure());
        PublishGuesses();
        LogJb("bot-guesses", Acore::StringFormat("why={} players={} chance={:.2f}/{}ms", why, _guesses.size(),
            kBotFindChance, kBotGuessEveryMs));
    }

    void UpdateGuesses(uint32 diff)
    {
        if (_guesses.empty())
            return;
        _guessMs += diff;
        if (_guessMs < kBotGuessEveryMs)
            return;
        _guessMs = 0;
        bool changed = false;
        for (auto& [player, guess] : _guesses)
        {
            switch (NextGuess(guess == me->GetGUID(), Standing(guess), Rand01(), kBotFindChance))
            {
                case GuessStep::Her:
                    changed = changed || guess != me->GetGUID();
                    guess = me->GetGUID();
                    break;
                case GuessStep::Random:
                    guess = RandomFigure();
                    changed = true;
                    break;
                default:
                    break;
            }
        }
        if (changed)
            PublishGuesses();
    }

    void PublishGuesses()
    {
        // Damage dealers and tanks hunt; healers keep healing (no entry for them).
        std::vector<BossMechanics::TargetEntry> entries;
        for (auto const& [player, guess] : _guesses)
            if (guess)
                for (BossMechanics::Who who : { BossMechanics::Who::Dps, BossMechanics::Who::Tank })
                    entries.push_back(BossMechanics::TargetEntry::ForUnit(guess.GetRawValue(), 2, who)
                        .OnlyFor(player.GetRawValue()));
        Mechanic::EditDescriptor(me, [entries = std::move(entries)](BossMechanics::Descriptor& d)
        {
            std::erase_if(d.targets, [](BossMechanics::TargetEntry const& e) { return e.bot != 0; });
            d.targets.insert(d.targets.end(), entries.begin(), entries.end());
        });
    }

    void ClearGuesses()
    {
        bool const had = !_guesses.empty();
        _guesses.clear();
        _guessMs = 0;
        if (had && me->IsInWorld())
            Mechanic::EditDescriptor(me, [](BossMechanics::Descriptor& d)
            {
                std::erase_if(d.targets, [](BossMechanics::TargetEntry const& e) { return e.bot != 0; });
            });
    }

    void Describe()
    {
        BossMechanics::Descriptor d;
        // Boss data: never the reflections (pets included, out of AoE counts); cure Curse of Blood. In the game each
        // bot has only its own guess (Q5, RollGuesses): no entry follows her guid, so bots know what players know.
        d.ignores.push_back(BossMechanics::IgnoreEntry(NPC_SC_REFLECTION));
        d.dispels.emplace_back(SPELL_JB_CURSE_OF_BLOOD, 1);
        Mechanic::Describe(me, std::move(d));
    }

    void ScheduleCurse(uint32 inMs)
    {
        _timers.Schedule(Ms(inMs), [this](TaskContext ctx)
        {
            if (!me->IsEngaged())
                return;
            bool const gameNear = !_clock.InGame() && _clock.UntilGameMs() <= kCurseQuietBeforeGameMs;
            if (gameNear || !CastCurse())
            {
                ctx.Repeat(Ms(kCurseRetryMs));
                return;
            }
            ctx.Repeat(Ms(kCurseEveryMs));
        });
    }

    // Finds and shatters count once she stands in the ring and the grace for old hits has passed.
    bool FindsCount() const
    {
        return _game.active && !_game.vanishing && _game.graceMs == 0;
    }

    void UpdateGame(uint32 diff)
    {
        if (!_game.vanishing)
            _game.graceMs = _game.graceMs > diff ? _game.graceMs - diff : 0;
        _mirrorMs += diff;
        if (_mirrorMs >= kMirrorEveryMs)
        {
            _mirrorMs = 0;
            Mirror();
        }
        UpdateGuesses(diff);
        GameTick const tick = _gameClock.Update(diff);
        for (uint32 i = 0; i < tick.prices && _game.active; ++i)
            BloodPrice();
        for (uint32 i = 0; i < tick.shuffles && _game.active; ++i)
            Shuffle(false, "timer");
        if (tick.limit)
            FailGame("limit");
    }

    // JB2 / JB4: someone found her.
    void Found(Unit* who, char const* how)
    {
        ++_game.finds;
        FindResult const result = FindOutcome(Heroic(), _game.finds);
        LogJb("found", Acore::StringFormat("by={} how={} find={} at={}ms", who ? who->GetName() : "?", how,
            _game.finds, _gameClock.ElapsedMs()));
        switch (result)
        {
            case FindResult::UnmaskAndShuffle:
            case FindResult::Shuffle:
                // Nobody keeps swinging at her: the second find has to track her through the shuffle. (Next update:
                // a melee find lands here in the middle of the attacker's own swing.)
                _game.graceMs = kFoundGraceMs;
                _timers.Schedule(Ms(0), [this](TaskContext /*ctx*/)
                {
                    me->RemoveAllAttackers();
                    me->AttackStop();
                });
                if (result == FindResult::UnmaskAndShuffle)
                    Unmask();
                Shuffle(true, "found");
                break;
            case FindResult::UnmaskAndEnd:
                Unmask();
                EndGameFound();
                break;
            case FindResult::End:
                EndGameFound();
                break;
        }
    }

    void Unmask()
    {
        DoCastSelf(SPELL_JB_UNMASKED, true);
        LogJb("unmasked", Acore::StringFormat("ms={}", kUnmaskedMs));
    }

    // The game ends with a find: the copies dissolve, she fights again.
    void EndGameFound()
    {
        Map* map = me->GetMap();
        for (ObjectGuid const& g : _copies)
            Dissolve(map, g, SPELL_JB_REFLECTION_POOF);
        _copies.clear();
        EndDisguise();
        _clock.GameEnded();
        LogJb("shell-game-end", "after=found");
    }

    // She is herself again (a find, the limit, a cleanup).
    void EndDisguise()
    {
        _game = GameState();
        _gameClock.Stop();
        _pendingSwaps.clear();
        _heldHit = HeldHit();
        ClearGuesses();
        if (!me->IsVisible())
            me->SetVisible(true);
        me->SetReactState(REACT_AGGRESSIVE);
    }

    // The figures free to pair: her and every copy standing still with no swap pending (`withHer`: her always,
    // the forced shuffle after the first find).
    std::vector<Creature*> Figures(bool withHer) const
    {
        std::vector<Creature*> out;
        auto free = [this](Creature const* c)
        {
            return c && c->IsAlive() && c->movespline->Finalized() && !InPendingSwap(c->GetGUID());
        };
        if (withHer ? me->IsAlive() : free(me))
            out.push_back(me);
        for (ObjectGuid const& g : _copies)
        {
            Creature* copy = me->GetMap()->GetCreature(g);
            if (free(copy))
                out.push_back(copy);
        }
        return out;
    }

    // Copies show her health and mana (the frames never give her away); no raid icon finds her either.
    void Mirror()
    {
        ClearRaidIcons();
        for (ObjectGuid const& g : _copies)
            if (Creature* copy = me->GetMap()->GetCreature(g))
            {
                if (copy->GetMaxHealth() != me->GetMaxHealth())
                    copy->SetMaxHealth(me->GetMaxHealth());
                copy->SetHealth(me->GetHealth());
                if (copy->GetMaxPower(POWER_MANA) != me->GetMaxPower(POWER_MANA))
                    copy->SetMaxPower(POWER_MANA, me->GetMaxPower(POWER_MANA));
                copy->SetPower(POWER_MANA, me->GetPower(POWER_MANA));
            }
    }

    std::vector<Vec2> PlayerPoints() const
    {
        std::vector<Vec2> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player const* player = ref.GetSource())
                if (player->IsAlive() && !player->IsGameMaster())
                    out.push_back(DungeonKit::PlaneOf(player));
        return out;
    }

    // A Reflection of Jandice Barov (300530): with the journal (real) or empty-handed (heroic decoy).
    Creature* SpawnReflection(Vec2 at, float facing, bool journal, uint32 warnMs)
    {
        Position const pos = FloorPosition(me, at, facing);
        TempSummon* r = me->SummonCreature(NPC_SC_REFLECTION, pos, TEMPSUMMON_TIMED_DESPAWN, warnMs + 2000);
        if (!r)
        {
            LogJb("reflection-summon-failed", Acore::StringFormat("at=({:.1f}, {:.1f})", at.x, at.y));
            return nullptr;
        }
        r->LoadEquipment(journal ? kEquipJournal : 0, true);
        r->CastSpell(r, SPELL_JB_REFLECTION_POOF, true);
        return r;
    }

    // One reflection and its 8 yd circle (`decoy`: drawn, harmless, absent from the bot view). False when the
    // reflection could not be summoned.
    bool SigilAt(Vec2 at, bool decoy, uint32 warnMs, float pct, uint32 tag, uint32 spell = SPELL_JB_BLOOD_SIGIL,
        float radius = kSigilRadius)
    {
        Creature* r = SpawnReflection(at, DungeonKit::BearingTo(at, DungeonKit::PlaneOf(me)), !decoy, warnMs);
        if (!r)
            return false;
        Map* map = me->GetMap();
        ObjectGuid const g = r->GetGUID();
        BossMechanics::MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(r), radius, Ms(warnMs));
        if (decoy)
            ref.Decoy().Tag(kTagBloodSigilDecoy)
                .OnResolve([map, g](BossMechanics::ResolveResult const&) { Dissolve(map, g, SPELL_JB_FAKE_POP); });
        else
            ref.Damage(pct).Spell(spell).Tag(tag)
                .OnResolve([map, g](BossMechanics::ResolveResult const&) { Dissolve(map, g, SPELL_JB_SIGIL_BURST); });
        Track(ref.Handle());
        return true;
    }

    // A Shell Game copy (11439): empty-handed, still, her health and mana.
    void SpawnCopy(Vec2 at, float facing)
    {
        TempSummon* copy = me->SummonCreature(NPC_ILLUSION_OF_JANDICE, FloorPosition(me, at, facing),
            TEMPSUMMON_TIMED_DESPAWN, kGameLimitMs(true) + kFailedWarnMs(true) + 5000);
        if (!copy)
        {
            LogJb("copy-summon-failed", Acore::StringFormat("at=({:.1f}, {:.1f})", at.x, at.y));
            return;
        }
        copy->LoadEquipment(0, true);
        copy->CastSpell(copy, SPELL_JB_REFLECTION_POOF, true);
        Mechanic::TrackUnit(me, copy);      // a target candidate for the bots' guesses (Q5)
        _copies.push_back(copy->GetGUID());
    }

    // The pull's state: no game, no zone, no reflection, the clock back to the start (Reset, evade, death, a pull).
    void Cleanup()
    {
        _timers.CancelAll();
        for (BossMechanics::MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        summons.DespawnAll();
        _copies.clear();
        EndDisguise();
        me->RemoveAurasDueToSpell(SPELL_JB_UNMASKED);
        if (me->IsInWorld())
            for (auto const& ref : me->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource())
                {
                    player->RemoveAurasDueToSpell(SPELL_JB_CURSE_OF_BLOOD, me->GetGUID());
                    for (Unit* controlled : player->m_Controlled)     // pets and guardians caught in the 10 yd
                        if (controlled)
                            controlled->RemoveAurasDueToSpell(SPELL_JB_CURSE_OF_BLOOD, me->GetGUID());
                }
        _clock.Start();
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    TaskScheduler _timers;                      // looks, reflections, the curse, the game's steps (never paused)
    JandiceClock _clock;
    ShellGameClock _gameClock;
    GameState _game;
    std::vector<ObjectGuid> _copies;            // the copies still standing in the game
    std::vector<BossMechanics::MechanicHandle> _live;
    uint32 _mirrorMs = 0;
    std::vector<Swap> _pendingSwaps;            // paired, not landed yet (out of new pairs)
    uint32 _nextSwapId = 1;
    std::vector<std::pair<ObjectGuid, ObjectGuid>> _guesses;    // Q5: player, the figure it guesses
    uint32 _guessMs = 0;
    HeldHit _heldHit;
    bool _dealingFind = false;                  // a spell find's held damage going through
};

namespace
{
    boss_jandice_barov_rework* JandiceAIOf(Creature* boss)
    {
        return boss && boss->IsAlive() && boss->IsAIEnabled ? dynamic_cast<boss_jandice_barov_rework*>(boss->AI())
            : nullptr;
    }
}

// The Shell Game copy: Illusion of Jandice Barov 11439, reused (hers alone). Empty-handed, still, no melee; her name,
// level, class, health and mana, so nothing but the journal tells it from her. It takes 0 from everything; a direct
// hit (a melee swing, a spell aimed at it) shatters it (the boss's CopyStruck).
struct npc_sc_shell_game_copy : public ScriptedAI
{
    explicit npc_sc_shell_game_copy(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void IsSummonedBy(WorldObject* summoner) override
    {
        _boss = summoner ? summoner->GetGUID() : ObjectGuid::Empty;
        me->SetReactState(REACT_PASSIVE);
        me->LoadEquipment(0, true);
        me->GetMotionMaster()->Clear(false);
        me->GetMotionMaster()->MoveIdle();
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // A copy never walks home: it stays where the game put it.
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->CombatStop(true);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask /*mask*/) override
    {
        damage = 0;
        if (type == DIRECT_DAMAGE && DirectHit(attacker, me, nullptr))
            Struck(attacker, "melee");
    }

    void SpellHit(Unit* caster, SpellInfo const* spell) override
    {
        if (spell && DirectHit(caster, me, spell))
            Struck(caster, "spell");
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        Creature* boss = _boss ? me->GetMap()->GetCreature(_boss) : nullptr;
        if (!boss || !boss->IsAlive())
        {
            me->DespawnOrUnsummon();
            return;
        }
        // The shatter lands here, after the attacker's own swing or spell is done with (never inside it).
        if (!_struckBy)
            return;
        Unit* attacker = ObjectAccessor::GetUnit(*me, _struckBy);
        _struckBy.Clear();
        if (boss_jandice_barov_rework* ai = JandiceAIOf(boss))
            if (attacker)
                ai->CopyStruck(me, attacker, _how);
    }

private:
    void Struck(Unit* attacker, char const* how)
    {
        if (_struckBy || !attacker)
            return;
        _struckBy = attacker->GetGUID();
        _how = how;
    }

    ObjectGuid _boss;
    ObjectGuid _struckBy;
    char const* _how = "";
};

// Reflection of Jandice Barov 300530: not selectable, no melee, still. The boss places it, draws its circle or lane
// and dissolves it.
struct npc_sc_jandice_reflection : public ScriptedAI
{
    explicit npc_sc_jandice_reflection(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

// 206112 Shatter (JB3): a percent of the reference row (the tank's row on the tank), Shadow, set at launch so the
// target's own reductions apply; the spell ignores caster modifiers.
class spell_sc_jandice_shatter : public SpellScript
{
    PrepareSpellScript(spell_sc_jandice_shatter);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(),
            kShatterPct(DungeonKit::IsHeroicMap(caster)))));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_sc_jandice_shatter::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// 206117 Blood Price (JB8, heroic): 4% of the reference non-tank row on every player within 100 yd, Shadow, set at
// launch (players only).
class spell_sc_jandice_blood_price : public SpellScript
{
    PrepareSpellScript(spell_sc_jandice_blood_price);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if([](WorldObject const* target) { return !target->IsPlayer(); });
    }

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlat(GetCaster(), kBloodPricePct)));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sc_jandice_blood_price::FilterTargets,
            EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY);
        OnEffectLaunchTarget += SpellEffectFn(spell_sc_jandice_blood_price::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    boss_jandice_barov_rework* JandiceAI(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_JANDICE);
        if (!boss)
            return nullptr;
        boss_jandice_barov_rework* ai = JandiceAIOf(boss);
        if (!ai)
            handler->SendErrorMessage("Jandice does not run boss_jandice_barov_rework (is the instance bound to "
                "{}?).", kInstanceScriptName);
        return ai;
    }

    // `.dbtest scholo jandice info`
    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_JANDICE, BOSS_JANDICE);
    }

    // `.dbtest scholo jandice state`: the game, the cadence and the live zones.
    bool HandleState(ChatHandler* handler)
    {
        boss_jandice_barov_rework* ai = JandiceAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("{}", ai->StateText());
        return true;
    }

    // `.dbtest scholo jandice sigils`: one Blood Sigil volley now (this map's difficulty).
    bool HandleSigils(ChatHandler* handler)
    {
        boss_jandice_barov_rework* ai = JandiceAI(handler);
        if (!ai)
            return false;
        ai->BloodSigil();
        return true;
    }

    // `.dbtest scholo jandice lines [along|across]`: one Bloodlines now; the axis by hand or as the fight picks it.
    bool HandleLines(ChatHandler* handler, Optional<std::string> axis)
    {
        boss_jandice_barov_rework* ai = JandiceAI(handler);
        if (!ai)
            return false;
        std::optional<bool> along;
        if (axis && *axis == "along")
            along = true;
        else if (axis && *axis == "across")
            along = false;
        else if (axis)
        {
            handler->SendErrorMessage("Axis: along or across.");
            return false;
        }
        ai->Bloodlines(along);
        return true;
    }

    // `.dbtest scholo jandice game`: the Shell Game now (pull her first: the game runs in her combat update).
    bool HandleGame(ChatHandler* handler)
    {
        boss_jandice_barov_rework* ai = JandiceAI(handler);
        if (!ai)
            return false;
        if (!ai->Engaged())
        {
            handler->SendErrorMessage("Pull Jandice first: the Shell Game runs in her combat update.");
            return false;
        }
        if (!ai->StartGame("test"))
        {
            handler->SendErrorMessage("The Shell Game is already on.");
            return false;
        }
        return true;
    }

    // `.dbtest scholo jandice find`: the find, as if the GM had hit her.
    bool HandleFind(ChatHandler* handler)
    {
        boss_jandice_barov_rework* ai = JandiceAI(handler);
        if (!ai)
            return false;
        if (!ai->InGame())
        {
            handler->SendErrorMessage("No Shell Game is on.");
            return false;
        }
        ai->ForceFind(handler->GetPlayer());
        return true;
    }

    // `.dbtest scholo jandice fail`: the game's limit now (the failed game's circles).
    bool HandleFail(ChatHandler* handler)
    {
        boss_jandice_barov_rework* ai = JandiceAI(handler);
        if (!ai)
            return false;
        if (!ai->InGame())
        {
            handler->SendErrorMessage("No Shell Game is on.");
            return false;
        }
        ai->FailGame("test");
        return true;
    }

    // `.dbtest scholo jandice shuffle`: one shuffle now (in a game, any difficulty).
    bool HandleShuffle(ChatHandler* handler)
    {
        boss_jandice_barov_rework* ai = JandiceAI(handler);
        if (!ai)
            return false;
        if (!ai->InGame())
        {
            handler->SendErrorMessage("No Shell Game is on.");
            return false;
        }
        ai->Shuffle(false, "test");
        return true;
    }

    // `.dbtest scholo jandice price`: one Blood Price tick now (any difficulty).
    bool HandlePrice(ChatHandler* handler)
    {
        boss_jandice_barov_rework* ai = JandiceAI(handler);
        if (!ai)
            return false;
        ai->BloodPrice();
        return true;
    }

    // `.dbtest scholo jandice curse`: Curse of Blood now (the real 2 s cast).
    bool HandleCurse(ChatHandler* handler)
    {
        boss_jandice_barov_rework* ai = JandiceAI(handler);
        if (!ai)
            return false;
        return ai->CastCurse();
    }

    ChatCommandTable const& JandiceTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "sigils",  HandleSigils,  SEC_GAMEMASTER, Console::No },
            { "lines",   HandleLines,   SEC_GAMEMASTER, Console::No },
            { "game",    HandleGame,    SEC_GAMEMASTER, Console::No },
            { "find",    HandleFind,    SEC_GAMEMASTER, Console::No },
            { "fail",    HandleFail,    SEC_GAMEMASTER, Console::No },
            { "shuffle", HandleShuffle, SEC_GAMEMASTER, Console::No },
            { "price",   HandlePrice,   SEC_GAMEMASTER, Console::No },
            { "curse",   HandleCurse,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_jandice_barov_rework()
{
    RegisterDungeonReworkCreatureAI(boss_jandice_barov_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_shell_game_copy, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_jandice_reflection, ScholomanceRework::kInstanceScriptName);
    RegisterSpellScript(spell_sc_jandice_shatter);
    RegisterSpellScript(spell_sc_jandice_blood_price);
    ScholoTest::RegisterBoss("jandice", JandiceTestCommands());
}
