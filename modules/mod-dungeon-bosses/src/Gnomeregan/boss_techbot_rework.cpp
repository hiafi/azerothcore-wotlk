/*
 * mod-dungeon-bosses, Gnomeregan D1: Techbot (301105, slot 2, encounter 379 / heroic 1108), normal and heroic, with
 * his Dupe Bugs (301106) and the after-images (301107). Build spec: SP 525-583 (TB1-TB9), design SP 375-524 (rulings
 * 9-13, 51, 54, 61); handoff section 3.5 row D1 and its kick and dispel table, sections 3.6, 3.8, 3.9 rows 1-2,
 * section 7 #13 A, #14 A, #36-#38 A. A new entry copying the outside Techbot 6231 (which stays stock on map 0, section
 * 7 #14 A); the S0 rev spawns him at ruling 61's spot and drops nothing of his (he had no stock script inside).
 * Numbers and ids: TechbotLogic.h; health: GnomereganRework.h Health; data: apps/dbc-tools
 * source/npcs/gnomeregan/techbot.py; texts: data/sql/updates/pending_db_world/rev_techbot_gnomeregan.sql.
 *
 *   TB1 Lag Spike     normal, first at 8 s, then every 15 s, through Patch: a random player on the dish (tank
 *                     included) lags (emote line 1, the lag look); an after-image of them (their look, aura 247, the
 *                     ghost) stays where they stood inside a 5 yd circle for 2 s: 40% and Weakened.
 *   TB2 Dupe Bugs     one at the boss every 10 s (heroic 8 s), 3 yd from him and from each other bug; normal at most 8
 *                     alive, Duplication bars in flight counted (a rise at the cap is skipped); heroic no cap but a
 *                     technical ceiling of 64 (DQ3). They take the tank first, then the nearest player.
 *   TB3 Duplication   the Duplicator machine (TechbotMachine.cpp): normal once at 9 s of life (3 s bar), heroic every
 *                     7 s of life (2 s bar), Nature, kickable; a stun or kick stops it (the reward). The copy rises at
 *                     the source's current health (ruling 51); a normal copy never duplicates (DQ1).
 *   TB4 Patch         every 45 s (heroic 35 s) from 45 s (35 s): yell line 2, an 8 s (6 s) Arcane bar he casts
 *                     instead of attacking; done: every living bug is deleted, he heals 3% (4%) of his health per bug
 *                     and (heroic) gains a Version stack per bug (+5% damage done, no cap); yell line 3 or 4. A kick
 *                     ends it: no heal, the bugs stay, Safe Mode ends. Bots kick it only while a bug lives.
 *   TB5 Safe Mode     +25% damage taken while the bar runs (the aura, removed at the bar's end, however it ends).
 *   TB6 Rubber Band   heroic, replaces TB1 (first at 8 s, then every 15 s): two random players (emote line 6) run out
 *                     (a 6 yd RunOut, telegraph only) for 2 s; at 2 s each one's save point is set where they stand
 *                     (the after-image and the light pillar, a 6 yd circle on everyone else bursting at the snap) and a
 *                     5 yd spike lands under them 1.5 s later; a second spike at 3.5 s; at 5 s (once the second spike
 *                     has resolved) they snap back to the save point. Spikes 60% + Weakened, the burst 60%.
 *   TB7 bug echoes    heroic: on each spike wave every living bug repeats it at its own feet (4 yd, 2 s, 40%).
 *   TB8 Battle Net    heroic, first at 20 s, then every 25 s: a net thrown at a random player, an 8 yd circle with a
 *                     1.5 s warning: 20%, Weakened and a 4 s Magic root (bots dispel it).
 *   TB9 Shutdown      he dies (section 7 #13 A), dressed as a shutdown: yell line 5, the sparks stay on the body (a
 *                     death-persistent aura), the bugs and after-images go; loot, credit, lockout and DC work as for
 *                     any boss (BossAI writes slot 2 DONE; the instance credits encounter 379).
 *   Chatter           one of the 13 stock help desk lines (group 0) every 15 s in combat.
 *
 * Damage is a percent of the reference row through the registry (the tank row on the tank, rule 17), scaled by his
 * Version stacks on heroic (his hits ignore caster modifiers, so the script scales them). Every random pick stands on
 * the dish (DishArena, rule 5); every bot shape keeps TechbotFloorBounds(). One INFO line per firing: "gnomer-build
 * techbot <mechanic> ...". `.dbtest gnomer techbot info|state|lag|bug|patch|net`.
 *
 * Nothing is mirrored from another core or the stock scripts (the stock Techbot is SmartAI rows only).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GnomereganKit.h"
#include "GnomereganRework.h"
#include "GnomereganTestCommand.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MechanicRegistry.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TechbotLogic.h"
#include "TechbotMachine.h"
#include "TemporarySummon.h"
#include <array>
#include <memory>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace GnomereganRework;
using namespace GnomerTechbot;
using BossMechanics::MechanicHandle;

namespace
{
    char const* const kKey = "techbot";
    uint8 constexpr kSchoolFire = 2;        // SPELL_SCHOOL_FIRE
    uint8 constexpr kSchoolNature = 3;      // SPELL_SCHOOL_NATURE
    uint8 constexpr kSchoolArcane = 6;      // SPELL_SCHOOL_ARCANE
    uint32 constexpr kLagEchoData = 1;      // SetData on an after-image: its landing look after this many ms

    // The auras the fight puts on players; every cleanup strips them from every player on the map (RB-1).
    std::array<uint32, 3> constexpr kPlayerAuras{ { SPELL_LAG, SPELL_RUBBER_BAND, SPELL_BATTLE_NET_ROOT } };
    // His own while he fights (the shutdown's sparks stay on the body: only a reset or an evade strips them).
    std::array<uint32, 2> constexpr kOwnAuras{ { SPELL_SAFE_MODE, SPELL_VERSION } };

    void TbLog(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kKey, mechanic, detail);
    }

    bool OnDish(WorldObject const* o)
    {
        return o && DishArena().Contains(DungeonKit::PlaneOf(o), o->GetPositionZ());
    }
}

// Techbot 301105
struct boss_techbot_rework : public BossAI
{
    explicit boss_techbot_rework(Creature* creature)
        : BossAI(creature, BOSS_TECHBOT), _arena(DishArena(), LeashOptions(kKey)), _bounds(TechbotFloorBounds())
    {
    }

    void Reset() override
    {
        Cleanup("reset");
        BossAI::Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup("pull");    // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        _lagAt = _heroic ? Tune::kBandFirstMs : Tune::kLagFirstMs;
        _bugAt = Tune::kBugFirstMs.Get(_heroic);
        _patchAt = Tune::kPatchFirstMs.Get(_heroic);
        _netAt = Tune::kNetFirstMs;
        _chatAt = Tune::kChatterEveryMs;
        _reassertAt = Tune::kReassertMs;

        GnomereganMachines::DuplicatorSpec spec = GnomereganMachines::TechbotBugSpec(_heroic);
        spec.onCopy = [this](Creature* source, Creature* copy) { OnBugCopy(source, copy); };
        GnomereganMachines::MachineOwner owner;
        owner.owner = me;
        owner.logKey = kKey;
        owner.heroic = _heroic;
        _dup = GnomereganMachines::MakeDuplicator(owner, std::move(spec));

        OnBossPull(me, kKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_TECHBOT;
        Mechanic::BeginEncounter(me, options);
        Describe();
        Mechanic::NoteNextCastIn(me, PatchSpell(_heroic), Milliseconds(_patchAt));
        _arena.Engage(me);
        TbLog("engage", Acore::StringFormat("heroic={} who={} lag_first={} bug_first={} patch_first={}",
            _heroic ? 1 : 0, who ? who->GetName() : "-", _lagAt, _bugAt, _patchAt));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        TbLog("evade", Acore::StringFormat("reason={} bugs={} version={}", uint32(why), Bugs(), _version));
        Cleanup("evade");
        BossAI::EnterEvadeMode(why);
    }

    // TB9: the sparks go on at the killing blow, while he still lives (the aura persists through death; a dead unit
    // takes no new aura).
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (_engaged && damage >= me->GetHealth() && !me->HasAura(SPELL_SHUTDOWN))
            me->CastSpell(me, SPELL_SHUTDOWN, true);
    }

    void JustDied(Unit* killer) override
    {
        TbLog("shutdown", Acore::StringFormat("bugs={} version={} patches={} kicked={} spikes={} killer={}", Bugs(),
            _version, _patches, _patchesKicked, _spikes, killer ? killer->GetName() : "-"));
        Cleanup("death", true);
        Talk(YELL_SHUTDOWN);
        BossAI::JustDied(killer);   // slot 2 DONE and saved; the instance credits the encounter; summons despawn
    }

    // Bugs (TB2, and the machine's copies through this same owner) and after-images.
    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        if (summon->GetEntry() != NPC_DUPE_BUG)
        {
            summons.Summon(summon);     // an after-image: listed for the cleanup, never put in combat
            return;
        }
        BossAI::JustSummoned(summon);
        Mechanic::TrackUnit(me, summon);
        if (Unit* target = ArrivalTarget(summon))
            if (summon->IsAIEnabled && summon->AI())
            {
                summon->AI()->AttackStart(target);
                summon->GetThreatMgr().AddThreat(target, 10.f);
            }
    }

    // TB4: the download completed.
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell && (spell->Id == SPELL_PATCH || spell->Id == SPELL_PATCH_H) && _patchRunning)
            ResolvePatch();
    }

    // TB4: a kick (the reward, never required) or anything else that stopped the bar.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || (spell->Id != SPELL_PATCH && spell->Id != SPELL_PATCH_H) || !_patchRunning)
            return;
        ++_patchesKicked;
        EndSafeMode();
        TbLog("patch-stopped", Acore::StringFormat("bugs={} (no heal, the bugs stay)", Bugs()));
    }

    void DoAction(int32 action) override
    {
        if (!_engaged)
            return;
        switch (action)
        {
            case ACTION_TEST_LAG:
                _lagAt = _now;
                break;
            case ACTION_TEST_BUG:
                _bugAt = _now;
                break;
            case ACTION_TEST_PATCH:
                _patchAt = _now;
                break;
            case ACTION_TEST_NET:
                _netAt = _now;
                break;
            default:
                break;
        }
    }

    uint32 GetData(uint32 id) const override
    {
        switch (id)
        {
            case DATA_TEST_ENGAGED:
                return _engaged ? 1 : 0;
            case DATA_TEST_BUGS:
                return Bugs();
            case DATA_TEST_VERSION:
                return _version;
            case DATA_TEST_PATCHES:
                return _patches;
            case DATA_TEST_SPIKES:
                return _spikes;
            default:
                return 0;
        }
    }

    std::string State() const
    {
        return Acore::StringFormat("engaged={} heroic={} now={} bugs={} version={} patches={} kicked={} spikes={} "
            "bands={} lag_in={} bug_in={} patch_in={} net_in={} | {}", _engaged ? 1 : 0, _heroic ? 1 : 0, _now, Bugs(),
            _version, _patches, _patchesKicked, _spikes, _bands.size(), In(_lagAt), In(_bugAt), In(_patchAt),
            In(_netAt), _dup ? _dup->Describe() : std::string("no machine"));
    }

    void UpdateAI(uint32 diff) override
    {
        GnomereganRework::NoAssist(me);     // rule 29, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        // The fight clock moves every tick, cast bar or not (L8); every mechanic but Patch runs through the bar.
        _now += diff;
        if (_dup)
            _dup->Update(diff);
        UpdateBands();
        CheckPatchBar();
        if (_now >= _reassertAt)
        {
            _reassertAt = _now + Tune::kReassertMs;
            ApplyVersion();
        }
        if (_now >= _bugAt)
            RiseBug();
        if (_now >= _lagAt)
        {
            if (RubberBandOn(_heroic))
                StartRubberBand();
            else
                LagSpike();
        }
        if (BattleNetOn(_heroic) && _now >= _netAt)
            BattleNet();
        if (_now >= _chatAt)
        {
            _chatAt = _now + Tune::kChatterEveryMs;
            Talk(SAY_CHATTER);
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_now >= _patchAt && StartPatch())
            return;
        DoMeleeAttackIfReady();
    }

private:
    struct Band
    {
        ObjectGuid player;
        std::string name;
        Position save;
        bool saved = false;
    };

    struct BandWave
    {
        uint32 start = 0;
        BandProgress progress;
        std::vector<Band> carriers;
    };

    int64 In(uint32 due) const
    {
        return int64(due) - int64(_now);
    }

    uint32 Bugs() const
    {
        return _dup ? _dup->Alive() : 0;
    }

    float Pct(float pct) const
    {
        return VersionOn(_heroic) ? ScaledPct(pct, _version) : pct;
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // Rule 19: an arriving bug takes the tank (his victim when it is a player), else the nearest player on the dish.
    Unit* ArrivalTarget(Creature* summon) const
    {
        if (Unit* victim = me->GetVictim())
            if (victim->IsPlayer() && victim->IsAlive())
                return victim;
        Player* nearest = nullptr;
        float best = 1.0e9f;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !OnDish(player))
                continue;
            float const d = player->GetExactDist2d(summon);
            if (d < best)
            {
                best = d;
                nearest = player;
            }
        }
        return nearest;
    }

    // Rule 5 and section 7 #36 A: random players on his threat list (tank included) who stand on the dish.
    std::vector<Player*> PickOnDish(uint32 count, GuidSet const& exclude = {}) const
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = Tune::kPickRangeYd;
        DungeonKit::ExcludeGuids(rule, exclude);
        std::vector<Player*> out;
        for (Player* player : DungeonKit::PickPlayers(me, rule, Tune::kPickPool))
        {
            if (!OnDish(player))
                continue;
            out.push_back(player);
            if (out.size() >= count)
                break;
        }
        return out;
    }

    // Every living player on the map but `owner` (the save point's eligible set: everyone else).
    GuidSet EveryoneBut(ObjectGuid owner) const
    {
        GuidSet out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsAlive() && !player->IsGameMaster() && player->GetGUID() != owner)
                out.insert(player->GetGUID());
        }
        return out;
    }

    // An after-image of `player` at `at` (aura 247 cast by them: their look and gear, and the ghost), living
    // `lifeMs`; with `landingMs` it shows the spike's landing look then.
    Creature* AfterImage(Player* player, Position const& at, uint32 lifeMs, uint32 landingMs)
    {
        TempSummon* echo = me->SummonCreature(NPC_LAG_ECHO, at, TEMPSUMMON_TIMED_DESPAWN, lifeMs);
        if (!echo)
            return nullptr;
        if (player)
            player->CastSpell(echo, SPELL_AFTER_IMAGE, true);
        if (landingMs && echo->IsAIEnabled && echo->AI())
            echo->AI()->SetData(kLagEchoData, landingMs);
        return echo;
    }

    // ---- TB1 Lag Spike (normal) -----------------------------------------------------------------------------------

    void LagSpike()
    {
        _lagAt = NextDue(_lagAt, Tune::kLagEveryMs, _now);
        std::vector<Player*> const picked = PickOnDish(1);
        if (picked.empty())
        {
            TbLog("lag-none", "nobody on the dish");
            return;
        }
        Player* target = picked.front();
        Position const at = target->GetPosition();
        Talk(EMOTE_LAG, target);
        target->CastSpell(target, SPELL_LAG, true);
        AfterImage(target, at, Tune::kLagWarnMs + Tune::kEchoDespawnPadMs,
            Tune::kLagWarnMs - Tune::kLandingLookLeadMs);
        Track(Mechanic::Circle(me, at, Tune::kLagRadiusYd, Milliseconds(Tune::kLagWarnMs))
            .Damage(Pct(Tune::kLagPct)).TankDamage(Pct(Tune::kLagPct)).Weakened().Spell(SPELL_LAG_SPIKE)
            .School(kSchoolFire).Within(_bounds).Tag(TAG_LAG_SPIKE));
        ++_spikes;
        TbLog("lag-spike", Acore::StringFormat("target={} x={:.1f} y={:.1f} pct={:.0f} next_in={}", target->GetName(),
            at.GetPositionX(), at.GetPositionY(), Pct(Tune::kLagPct), In(_lagAt)));
    }

    // ---- TB2 Dupe Bugs ---------------------------------------------------------------------------------------------

    void RiseBug()
    {
        _bugAt = NextDue(_bugAt, Tune::kBugEveryMs.Get(_heroic), _now);
        if (!_dup)
            return;
        uint32 const alive = _dup->Alive();
        uint32 const casting = uint32(_dup->Casting().size());     // copies on their way (R-1-A m1)
        if (!BugMayRise(alive, _heroic, casting))
        {
            // Normal: the cap of 8; heroic: the technical ceiling (DQ3), not a design cap.
            TbLog(_heroic ? "bug-ceiling" : "bug-capped", Acore::StringFormat("alive={} casting={} limit={}", alive,
                casting, BugLimit(_heroic)));
            return;
        }
        std::vector<Vec2> others;
        for (ObjectGuid const& guid : _dup->Units())
            if (Creature* bug = ObjectAccessor::GetCreature(*me, guid))
                others.push_back(DungeonKit::PlaneOf(bug));
        float const z = me->GetPositionZ();
        Vec2 const p = RisePoint(DungeonKit::PlaneOf(me), me->GetOrientation(), others,
            [z](Vec2 q) { return DishArena().Contains(q, z); });
        float floorZ = me->GetMap()->GetHeight(me->GetPhaseMask(), p.x, p.y, z + 2.f);
        if (floorZ < z - 3.f || floorZ > z + 3.f)
            floorZ = z;
        TempSummon* bug = me->SummonCreature(NPC_DUPE_BUG, Position(p.x, p.y, floorZ, me->GetOrientation()),
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, Tune::kBugCorpseMs);
        if (!bug)
        {
            TbLog("bug-refused");
            return;
        }
        _dup->Track(bug);
        bug->CastSpell(bug, SPELL_BUG_SPAWN, true);
        TbLog("bug", Acore::StringFormat("alive={} x={:.1f} y={:.1f} next_in={}", alive + 1, p.x, p.y, In(_bugAt)));
    }

    // TB3: a copy rose (the machine set its health); the look.
    void OnBugCopy(Creature* source, Creature* copy)
    {
        if (!copy)
            return;
        copy->CastSpell(copy, SPELL_BUG_SPAWN, true);
        if (source && source->GetVictim() && copy->IsAIEnabled && copy->AI() && !copy->GetVictim())
            copy->AI()->AttackStart(source->GetVictim());
    }

    // ---- TB4 Patch, TB5 Safe Mode, Version -------------------------------------------------------------------------

    bool StartPatch()
    {
        uint32 const spell = PatchSpell(_heroic);
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, spell, false);
        if (result != SPELL_CAST_OK)
        {
            _patchAt = _now + Tune::kPatchRetryMs;      // rule 15: an Arcane lock or a silence, look again
            TbLog("patch-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        _patchAt = NextDue(_patchAt, Tune::kPatchEveryMs.Get(_heroic), _now);
        _patchRunning = true;
        Talk(YELL_PATCH);
        me->AddAura(SPELL_SAFE_MODE, me);
        me->CastSpell(me, SPELL_SAFE_MODE_START, true);
        Mechanic::NoteNextCastIn(me, spell, Milliseconds(_patchAt - _now));
        TbLog("patch", Acore::StringFormat("cast={} bugs={} next_in={}", Tune::kPatchCastMs.Get(_heroic), Bugs(),
            In(_patchAt)));
        return true;
    }

    void ResolvePatch()
    {
        EndSafeMode();
        ++_patches;
        uint32 deleted = 0;
        if (_dup)
            for (ObjectGuid const& guid : _dup->Units())
            {
                if (Creature* bug = ObjectAccessor::GetCreature(*me, guid))
                    bug->DespawnOrUnsummon(Milliseconds(1));
                _dup->Forget(guid);
                ++deleted;
            }
        uint32 const heal = PatchHeal(me->GetMaxHealth(), deleted, _heroic);
        if (heal)
            me->ModifyHealth(int32(heal));
        if (VersionOn(_heroic))
        {
            _version += deleted;
            ApplyVersion();
        }
        me->CastSpell(me, SPELL_PATCH_DONE, true);
        Talk(deleted ? YELL_PATCH_FIXED : YELL_PATCH_CLEAN);
        TbLog("patch-done", Acore::StringFormat("deleted={} heal={} health={:.0f}% version={}", deleted, heal,
            me->GetHealthPct(), _version));
    }

    // R-1-B mn-3 (ZF): the bar ended with neither callback (AzerothCore calls OnSpellFailed only from an interrupt):
    // Safe Mode goes. OnSpellCast runs inside the spell's own update, before this tick.
    void CheckPatchBar()
    {
        if (!_patchRunning || me->FindCurrentSpellBySpellId(PatchSpell(_heroic)))
            return;
        TbLog("patch-lost", "the bar ended without landing");
        EndSafeMode();
    }

    void EndSafeMode()
    {
        _patchRunning = false;
        me->RemoveAurasDueToSpell(SPELL_SAFE_MODE);
    }

    // Rule 25: the Version amount is set by script and reasserted every second and on every change.
    void ApplyVersion()
    {
        if (!VersionOn(_heroic) || !_version)
            return;
        Aura* aura = me->GetAura(SPELL_VERSION, me->GetGUID());
        if (!aura)
            aura = me->AddAura(SPELL_VERSION, me);
        if (!aura)
            return;
        uint8 const shown = uint8(VersionShownStacks(_version));
        if (aura->GetStackAmount() != shown)
            aura->SetStackAmount(shown);
        if (AuraEffect* effect = aura->GetEffect(EFFECT_0))
            if (effect->GetAmount() != VersionAuraAmount(_version))
                effect->ChangeAmount(VersionAuraAmount(_version));
    }

    // ---- TB6 Rubber Band, TB7 bug echoes (heroic) ------------------------------------------------------------------

    void StartRubberBand()
    {
        _lagAt = NextDue(_lagAt, Tune::kBandEveryMs, _now);
        std::vector<Player*> const picked = PickOnDish(Tune::kBandCarriers);
        if (picked.empty())
        {
            TbLog("band-none", "nobody on the dish");
            return;
        }
        BandWave wave;
        wave.start = _now;
        std::string names;
        for (Player* player : picked)
        {
            Band band;
            band.player = player->GetGUID();
            band.name = player->GetName();
            wave.carriers.push_back(band);
            Talk(EMOTE_RUBBER_BAND, player);
            player->CastSpell(player, SPELL_RUBBER_BAND, true);
            // The carrier runs the save point out of the group (telegraph only: the drill's pct=0 RunOut).
            Track(Mechanic::RunOut(me, player, Tune::kBandRunOutYd, Milliseconds(Tune::kBandSaveMs))
                .Within(_bounds).Tag(TAG_RUBBER_RUN_OUT));
            names += (names.empty() ? "" : ",") + band.name;
        }
        _bands.push_back(std::move(wave));
        TbLog("rubber-band", Acore::StringFormat("carriers={} next_in={}", names, In(_lagAt)));
    }

    void UpdateBands()
    {
        for (auto it = _bands.begin(); it != _bands.end();)
        {
            BandWave& wave = *it;
            BandStep const step = DueBandStep(wave.progress, _now - wave.start);
            switch (step)
            {
                case BandStep::Save:
                    for (Band& band : wave.carriers)
                        SavePoint(band);
                    EchoWave(1);
                    break;
                case BandStep::SpikeTwo:
                    for (Band& band : wave.carriers)
                        if (Player* player = CarrierOnDish(band))
                            Spike(player, 2);
                    EchoWave(2);
                    break;
                case BandStep::Snap:
                    for (Band& band : wave.carriers)
                        Snap(band);
                    break;
                default:
                    break;
            }
            MarkBandStep(wave.progress, step);
            if (step == BandStep::Done)
                it = _bands.erase(it);
            else
                ++it;
        }
    }

    Player* CarrierOnDish(Band const& band) const
    {
        Player* player = ObjectAccessor::GetPlayer(*me, band.player);
        return player && player->IsAlive() && player->IsInWorld() && player->GetMap() == me->GetMap()
            && OnDish(player) ? player : nullptr;
    }

    // At 2 s: the save point where the carrier stands (the after-image under the light pillar, the 6 yd burst on
    // everyone else at the snap) and the first spike under them.
    void SavePoint(Band& band)
    {
        Player* player = CarrierOnDish(band);
        if (!player)
        {
            TbLog("band-lost", Acore::StringFormat("carrier={} (dead or off the dish at the save)", band.name));
            return;
        }
        band.save = player->GetPosition();
        band.saved = true;
        if (Creature* image = AfterImage(player, band.save, Tune::kBandBurstWarnMs + Tune::kEchoDespawnPadMs, 0))
            image->CastSpell(image, SPELL_SAVE_POINT, true);
        BossMechanics::Eligibility others;
        others.carriers = EveryoneBut(band.player);
        // An empty set is "everyone" to the registry: with the owner the last one alive there is nobody to burst.
        if (!others.carriers.empty())
            Track(Mechanic::Circle(me, band.save, Tune::kSavePointYd, Milliseconds(Tune::kBandBurstWarnMs))
                .Eligible(others).Damage(Pct(Tune::kSavePointPct)).TankDamage(Pct(Tune::kSavePointPct))
                .Spell(SPELL_SAVE_POINT_BURST).School(kSchoolArcane).Within(_bounds).Tag(TAG_SAVE_POINT));
        Spike(player, 1);
        TbLog("save-point", Acore::StringFormat("carrier={} x={:.1f} y={:.1f} others={} pct={:.0f}", band.name,
            band.save.GetPositionX(), band.save.GetPositionY(), others.carriers.size(), Pct(Tune::kSavePointPct)));
    }

    void Spike(Player* player, uint32 which)
    {
        Position const at = player->GetPosition();
        Track(Mechanic::Circle(me, at, Tune::kBandSpikeYd, Milliseconds(Tune::kBandSpikeWarnMs))
            .Damage(Pct(Tune::kBandSpikePct)).TankDamage(Pct(Tune::kBandSpikePct)).Weakened()
            .Spell(SPELL_RUBBER_SPIKE).School(kSchoolArcane).Within(_bounds).Tag(TAG_RUBBER_SPIKE));
        ++_spikes;
        TbLog("rubber-spike", Acore::StringFormat("carrier={} spike={} x={:.1f} y={:.1f}", player->GetName(), which,
            at.GetPositionX(), at.GetPositionY()));
    }

    // TB7: every living bug on the dish repeats the spike at its feet (one circle per bug per wave).
    void EchoWave(uint32 which)
    {
        if (!_dup)
            return;
        uint32 echoes = 0;
        for (ObjectGuid const& guid : _dup->Units())
        {
            Creature* bug = ObjectAccessor::GetCreature(*me, guid);
            if (!bug || !bug->IsAlive() || !OnDish(bug))
                continue;
            Track(Mechanic::Circle(me, bug->GetPosition(), Tune::kEchoRadiusYd, Milliseconds(Tune::kEchoWarnMs))
                .Damage(Pct(Tune::kEchoPct)).TankDamage(Pct(Tune::kEchoPct)).Weakened().Spell(SPELL_BUG_ECHO)
                .School(kSchoolFire).Within(_bounds).Tag(TAG_BUG_ECHO));
            ++echoes;
        }
        if (echoes)
            TbLog("bug-echo", Acore::StringFormat("wave={} circles={}", which, echoes));
    }

    // At 5 s (after the second spike): the carrier snaps back to the save point.
    void Snap(Band const& band)
    {
        Player* player = ObjectAccessor::GetPlayer(*me, band.player);
        if (player)
            player->RemoveAurasDueToSpell(SPELL_RUBBER_BAND);
        if (!band.saved || !player || !player->IsAlive() || !player->IsInWorld() || player->GetMap() != me->GetMap())
            return;
        player->NearTeleportTo(band.save.GetPositionX(), band.save.GetPositionY(), band.save.GetPositionZ(),
            player->GetOrientation());
        me->CastSpell(player, SPELL_SNAP_BACK, true);
        TbLog("snap", Acore::StringFormat("carrier={} x={:.1f} y={:.1f}", band.name, band.save.GetPositionX(),
            band.save.GetPositionY()));
    }

    // ---- TB8 Battle Net (heroic) -----------------------------------------------------------------------------------

    void BattleNet()
    {
        _netAt = NextDue(_netAt, Tune::kNetEveryMs, _now);
        std::vector<Player*> const picked = PickOnDish(1);
        if (picked.empty())
            return;
        Player* target = picked.front();
        Position const at = target->GetPosition();
        me->CastSpell(target, SPELL_BATTLE_NET_THROW, true);
        Track(Mechanic::Circle(me, at, Tune::kNetRadiusYd, Milliseconds(Tune::kNetWarnMs))
            .Damage(Pct(Tune::kNetPct)).TankDamage(Pct(Tune::kNetPct)).Weakened().Rider(SPELL_BATTLE_NET_ROOT)
            .Spell(SPELL_BATTLE_NET).School(kSchoolNature).Within(_bounds).Tag(TAG_BATTLE_NET));
        TbLog("battle-net", Acore::StringFormat("target={} x={:.1f} y={:.1f} next_in={}", target->GetName(),
            at.GetPositionX(), at.GetPositionY(), In(_netAt)));
    }

    // ---- the descriptor and the cleanup ----------------------------------------------------------------------------

    // Boss data (SP "Bots"): a bug casting Duplication first, then the other bugs, then him (the kick table:
    // Duplication kicked, Patch kicked only while a bug lives and never otherwise); heroic: Battle Net dispelled.
    void Describe()
    {
        using BossMechanics::Condition;
        using BossMechanics::DispelEntry;
        using BossMechanics::InterruptEntry;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        uint32 const dup = DuplicationSpell(_heroic);
        uint32 const patch = PatchSpell(_heroic);
        Milliseconds const every(Tune::kPatchEveryMs.Get(_heroic));
        Condition const bugNear = Condition::NearUnit(NPC_DUPE_BUG, Tune::kPatchBugRangeYd);
        d.interrupts.emplace_back(NPC_DUPE_BUG, dup, kKickDuplication);
        d.interrupts.emplace_back(NPC_TECHBOT, patch, kKickPatch, every, bugNear);
        d.interrupts.emplace_back(NPC_TECHBOT, patch, kNeverKick, every, Condition::Not(bugNear));
        // Captures nothing (BM: a Custom condition may run on a bot's stale copy): the ids are constants.
        d.targets.push_back(TargetEntry(NPC_DUPE_BUG, kKillCastingBug, Who::Dps, Condition::Custom(
            [](Unit const* unit)
            {
                return unit->FindCurrentSpellBySpellId(SPELL_DUPLICATION)
                    || unit->FindCurrentSpellBySpellId(SPELL_DUPLICATION_H);
            })).AoeOk());
        d.targets.push_back(TargetEntry(NPC_DUPE_BUG, kKillBug, Who::Dps).AoeOk());
        if (BattleNetOn(_heroic))
            d.dispels.push_back(DispelEntry(SPELL_BATTLE_NET_ROOT, kDispelNet));
        Mechanic::Describe(me, std::move(d));
    }

    // RB-1: everything the pull made, in one place: the registry handles, the machine and its bugs, every summon (the
    // after-images), the Rubber Bands, his auras and the players' auras, the clocks.
    void Cleanup(char const* why, bool death = false)
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_dup)
            _dup->Clear();
        summons.DespawnAll();
        _bands.clear();
        for (uint32 spell : kOwnAuras)
            me->RemoveAurasDueToSpell(spell);
        if (!death)
            me->RemoveAurasDueToSpell(SPELL_SHUTDOWN);
        if (me->IsInWorld())
            for (auto const& ref : me->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource())
                    for (uint32 spell : kPlayerAuras)
                        player->RemoveAurasDueToSpell(spell);
        if (_engaged)
            TbLog("cleanup", Acore::StringFormat("why={}", why));
        _patchRunning = false;
        _engaged = false;
        _now = 0;
        _lagAt = 0;
        _bugAt = 0;
        _patchAt = 0;
        _netAt = 0;
        _chatAt = 0;
        _reassertAt = 0;
        _version = 0;
        _patches = 0;
        _patchesKicked = 0;
        _spikes = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    BossMechanics::SpotBounds _bounds;
    std::vector<MechanicHandle> _live;
    std::unique_ptr<GnomereganMachines::Duplicator> _dup;
    std::vector<BandWave> _bands;
    bool _heroic = false;
    bool _engaged = false;
    bool _patchRunning = false;
    uint32 _now = 0;
    uint32 _lagAt = 0;
    uint32 _bugAt = 0;
    uint32 _patchAt = 0;
    uint32 _netAt = 0;
    uint32 _chatAt = 0;
    uint32 _reassertAt = 0;
    uint32 _version = 0;
    uint32 _patches = 0;
    uint32 _patchesKicked = 0;
    uint32 _spikes = 0;
};

// Dupe Bug 301106: melee only; Duplication is the machine's (it casts the bar through this unit).
struct npc_gnomer_dupe_bug : public ScriptedAI
{
    explicit npc_gnomer_dupe_bug(Creature* creature) : ScriptedAI(creature) { }

    void UpdateAI(uint32 /*diff*/) override
    {
        GnomereganRework::NoAssist(me);
        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }
};

// The after-image 301107: a passive helper wearing a player's look (aura 247); with SetData(1, ms) it shows the
// spike's landing look after that many ms. Gone by its summon timer.
struct npc_gnomer_lag_echo : public ScriptedAI
{
    explicit npc_gnomer_lag_echo(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void SetData(uint32 id, uint32 value) override
    {
        if (id == kLagEchoData)
            _landingIn = value ? value : 1;
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void UpdateAI(uint32 diff) override
    {
        if (!_landingIn)
            return;
        if (_landingIn > diff)
        {
            _landingIn -= diff;
            return;
        }
        _landingIn = 0;
        me->CastSpell(me, SPELL_LAG_SPIKE_LANDING, true);
    }

private:
    uint32 _landingIn = 0;
};

namespace
{
    boss_techbot_rework* TechbotAI(ChatHandler* handler)
    {
        Creature* boss = GnomerTest::FindBoss(handler, NPC_TECHBOT);
        if (!boss)
            return nullptr;
        auto* ai = dynamic_cast<boss_techbot_rework*>(boss->AI());
        if (!ai)
            handler->SendErrorMessage("Techbot does not run boss_techbot_rework.");
        return ai;
    }

    bool Fire(ChatHandler* handler, int32 action, char const* what)
    {
        boss_techbot_rework* ai = TechbotAI(handler);
        if (!ai)
            return false;
        if (!ai->GetData(DATA_TEST_ENGAGED))
        {
            handler->SendErrorMessage("Techbot is not fighting: pull him first.");
            return false;
        }
        ai->DoAction(action);
        handler->PSendSysMessage("techbot {}: due now", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return GnomerTest::ShowBossInfo(handler, NPC_TECHBOT, BOSS_TECHBOT);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_techbot_rework* ai = TechbotAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("techbot {}", ai->State());
        return true;
    }

    bool HandleLag(ChatHandler* handler) { return Fire(handler, ACTION_TEST_LAG, "lag spike / rubber band"); }
    bool HandleBug(ChatHandler* handler) { return Fire(handler, ACTION_TEST_BUG, "dupe bug"); }
    bool HandlePatch(ChatHandler* handler) { return Fire(handler, ACTION_TEST_PATCH, "patch"); }
    bool HandleNet(ChatHandler* handler) { return Fire(handler, ACTION_TEST_NET, "battle net (heroic)"); }

    ChatCommandTable const& TechbotTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",  HandleInfo,  SEC_GAMEMASTER, Console::No },
            { "state", HandleState, SEC_GAMEMASTER, Console::No },
            { "lag",   HandleLag,   SEC_GAMEMASTER, Console::No },
            { "bug",   HandleBug,   SEC_GAMEMASTER, Console::No },
            { "patch", HandlePatch, SEC_GAMEMASTER, Console::No },
            { "net",   HandleNet,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_techbot_rework()
{
    RegisterDungeonReworkCreatureAI(boss_techbot_rework, GnomereganRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_dupe_bug, GnomereganRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_lag_echo, GnomereganRework::kInstanceScriptName);
    GnomerTest::RegisterBoss("techbot", TechbotTestCommands());
}
