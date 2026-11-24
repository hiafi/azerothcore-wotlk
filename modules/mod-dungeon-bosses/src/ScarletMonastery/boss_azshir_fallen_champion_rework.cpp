/*
 * mod-dungeon-bosses, Scarlet Monastery D3: Azshir the Sleepless (6490) and the Fallen Champion (6488), the council,
 * "The Last Vigil", normal and heroic. Build spec: docs/dungeons/scarlet-monastery-1-graveyard.md "Azshir and the
 * Fallen Champion rework" (CV1-CV8, Build spec); handoff section 3.5 row D3, section 3.6, section 3.8 row D3, section
 * 7 #17 A (the Hallow's End objects untouched) and #18 A (the fight is on the lawn disc kCouncilLawn, Azshir 3 yd
 * behind the Champion: the grave's dais has no walk route). Replaces SmartAI 6490 and 6488 (WP-S0's rev dropped the
 * rows and the 90% despawn rolls); bound by apps/dbc-tools source/npcs/scarlet_monastery/council.py. Pure rules:
 * CouncilLogic.h.
 *
 * One encounter, one slot (BOSS_COUNCIL, 8). Both AIs are ScriptedAIs on the slot's registry encounter: the INSTANCE
 * writes DONE and sends the credit spell 212300 once both are dead (OnUnitDeath, whoever dies last); this file never
 * sends credit. It writes IN_PROGRESS at the pull and NOT_STARTED when both have reset (DC's stand-down and the
 * combat-res guard read IsEncounterInProgress).
 *
 *   Pull          either one pulls both (DoZoneInCombat in 40 yd and AttackStart on the partner); either one evading
 *                 sends the other home, and a partner who died in the failed attempt respawns (a wipe resets both)
 *   Azshir        never moves, never melees (a ghost at his post); one cast at a time through the kit's CastQueue
 *   CV2  Holy Shock       4 s, every 7 s: a random player, the tank included, 12% / 18% Holy (instant)
 *   CV5  Exorcism         8 s, every 12 s: a 2 s bar, a 4 yd x 40 yd line from him through a random player's spot
 *                         at the cast start (normal: never a Justice target), 35% / 45% + Weakened
 *   CV4  Holy Wrath       14 s, every 16 s: a 2 s bar, the 10 yd ring round him, 35% / 45% + Weakened; the Champion
 *                         inside at the resolve takes 5% of his health and a 2 s pacify (the tank's parking reward;
 *                         the registry ring carries Park(the Champion) for the bot tank)
 *   CV3  Holy Light       18 s, every 18 s: a 2.5 s interruptible heal on the brother with the lower percent of health,
 *                         10% / 25% (interrupt list: a reward on normal, expected on heroic)
 *   CV8  Execution Sentence (heroic) 20 s, every 30 s: a heal absorb (aura 301, every school) of 75% of the reference
 *                         row (the tank row on the tank) on a random player, the tank included, for 8 s; healed off it
 *                         falls on the room for 10% + 5% a second it was up, on its own at 8 s for 50%; no Weakened
 *   The Champion  melee; one seal held at a time, changed every 20 s / 15 s with an emote: Command, Righteousness,
 *                 Justice, repeat
 *   CV6a Judgement        10 s, every 10 s: the tank, 25% / 35% of tank health, carrying the seal's rider
 *   CV6b Command          while it holds: his swings cleave a 120 degree, 8 yd front (the tank exempt), 30% / 45% +
 *                         Weakened every 2 s (a persistent registry Frontal; the tank faces him away)
 *   CV6c Righteousness    each Judgement brands 2 / 3 random non-tank players; 5 s later each burst hits every other
 *                         player within 6 yd for 35% / 45% + Weakened (a registry Spread; the carrier takes nothing)
 *   CV6d Justice          each Judgement marks a random player, the tank included; 5 s later 150% / 250% split among
 *                         everyone within 6 yd (a registry Stack; normal: a share at most 75%; no Weakened)
 *   CV7  Avenger's Shield 10 s, every 15 s, waiting while a Justice mark is up: a 2 s bar at a random player more than
 *                         10 yd from him, then it bounces to the nearest player within 8 yd of each hit, 3 / 5 hits;
 *                         the first 20% / 25% + a 2 s silence, each bounce 30% / 40% + Weakened (a registry Spread on
 *                         the first target, eligible: the players more than 10 yd from him)
 *   CV1  The Last Vigil   the Champion falls while Azshir stands: he does not die (LethalGuard) but collapses
 *                         (unselectable, lying down); Azshir yells and channels 8 s (nothing else meanwhile: the window
 *                         to kill him); at the end, with Azshir alive, the Champion rises at 40% then 20% (normal) /
 *                         50% (heroic), two raises at most (heroic: the HANDOFF s10 default, kMaxRaises). Azshir
 *                         dies during the channel: the fallen Champion's death becomes real (the loot recipient as the
 *                         killer: the credit lands). Azshir dies first:
 *                         Grief on the Champion, +20% damage done and attack speed every 5 s, 5 stacks at most on
 *                         normal, no cap on heroic (multiplied into every percent of his too)
 *   Boss data     kill together by percent of health (both within 10%; Azshir alone while the Champion lies fallen);
 *                 Holy Light on the interrupt list (priority 2 normal, 3 heroic); no dispels
 *   Arena         CouncilLogic.h FightArena(): the 40 yd lawn disc cut at y 1317 (Ironspine's side),
 *                 ScarletMonasteryRework::LeashOptions (no grips);
 *                 Azshir keeps only the no-target leash (he never moves)
 *
 * Every timer runs on the AI's own clock; casts never overlap. Cross-AI news (the fall, the rise, Azshir's death) is
 * queued and handled on the receiver's next tick, never inside the sender's death or damage chain. Registry lambdas
 * capture the map and guids only. Every firing logs one INFO line "sm champion <mechanic> ..." or "sm azshir
 * <mechanic> ..." (module.dungeonbosses); `.dbtest sm council <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "CouncilLogic.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFlow.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicWeakened.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmCouncil;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kChampionKey = "champion";
    char const* const kAzshirKey = "azshir";

    // CreatureAI::GetData ids on the Champion's AI.
    uint32 constexpr DATA_CV_FALLEN = 1;    // 1 while he lies fallen (the Last Vigil)
    uint32 constexpr DATA_CV_RAISES = 2;    // raises started this attempt

    // Registry tags (one per mechanic; the bots and `.mech` read them).
    uint32 constexpr TAG_CV_WRATH = 1;
    uint32 constexpr TAG_CV_EXORCISM = 2;
    uint32 constexpr TAG_CV_COMMAND = 3;
    uint32 constexpr TAG_CV_BRAND = 4;
    uint32 constexpr TAG_CV_JUSTICE = 5;
    uint32 constexpr TAG_CV_SHIELD = 6;

    float constexpr kZBandYd = 6.f;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    Position LawnCenter()
    {
        return Position(kCouncilLawn.x, kCouncilLawn.y, kCouncilLawn.z, 0.f);
    }

    // The bots' planned spots: the lawn disc's middle 30 yd (rule 12).
    BossMechanics::SpotBounds LawnBounds()
    {
        BossMechanics::SpotBounds bounds;
        bounds.Circle(LawnCenter(), kSpotBoundsYd, kArenaZMin, kArenaZMax);
        return bounds;
    }

    Creature* CouncilUnit(WorldObject const* me, uint32 guidKey)
    {
        InstanceScript* instance = me ? me->GetInstanceScript() : nullptr;
        if (!instance)
            return nullptr;
        ObjectGuid const guid = instance->GetGuidData(guidKey);
        return guid ? ObjectAccessor::GetCreature(*me, guid) : nullptr;
    }

    Creature* ChampionOf(WorldObject const* me)
    {
        return CouncilUnit(me, kGuidBossBase + BOSS_COUNCIL);
    }

    Creature* AzshirOf(WorldObject const* me)
    {
        return CouncilUnit(me, kGuidAzshir);
    }

    // The Champion is up: alive and not lying fallen in the Last Vigil.
    bool ChampionStands(Creature* champion)
    {
        return champion && champion->IsAlive() && champion->IsAIEnabled && champion->AI()
            && champion->AI()->GetData(DATA_CV_FALLEN) == 0;
    }

    // Every living, non-GM player on the lawn disc (2D, within the floor band): the room for the room-wide hits.
    std::vector<Player*> RoomPlayers(WorldObject const* me)
    {
        std::vector<Player*> players;
        Map const* map = me ? me->FindMap() : nullptr;
        if (!map)
            return players;
        Arena const arena = FightArena();
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
                if (player->IsAlive() && player->IsInWorld() && !player->IsGameMaster()
                    && arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                    players.push_back(player);
        return players;
    }

    // A Justice mark is up on somebody (Avenger's Shield waits; normal Exorcism never aims at the marked).
    bool JusticeMarkUp(WorldObject const* me)
    {
        for (Player* player : RoomPlayers(me))
            if (player->HasAura(SPELL_CV_JUSTICE_MARK))
                return true;
        return false;
    }

    // Pulling either pulls both: the partner, alive and not fighting yet, turns on `who` and takes the players of the
    // lawn onto its threat list.
    void PullPartner(Creature* partner, Unit* who)
    {
        if (!partner || !partner->IsAlive() || partner->IsInCombat() || !partner->IsAIEnabled || !partner->AI())
            return;
        if (who)
            partner->AI()->AttackStart(who);
        partner->AI()->DoZoneInCombat(partner, kPullZoneYd);
    }

    // Either one evading sends the other home (one encounter).
    void EvadePartner(Creature* partner, CreatureAI::EvadeReason why)
    {
        if (partner && partner->IsAlive() && partner->IsInCombat() && partner->IsAIEnabled && partner->AI())
            partner->AI()->EnterEvadeMode(why);
    }

    // A wipe resets both: a partner who died in the failed attempt respawns (never once the slot is DONE).
    void RespawnFallenPartner(Creature* me, Creature* partner, char const* why)
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!partner || partner->IsAlive() || !instance || instance->GetBossState(BOSS_COUNCIL) == DONE)
            return;
        partner->Respawn(true);
        DungeonKit::LogMechanic(kLogDungeon, me->GetEntry() == NPC_AZSHIR ? kAzshirKey : kChampionKey,
            "partner-respawn", Acore::StringFormat("partner={} why={}", partner->GetEntry(), why));
    }

    // Slot 8 is IN_PROGRESS while either one fights; DONE stays the instance's (both dead).
    void MarkFightStarted(Creature* me)
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return;
        uint32 const state = instance->GetBossState(BOSS_COUNCIL);
        if (state == NOT_STARTED || state == FAIL)
            instance->SetBossState(BOSS_COUNCIL, IN_PROGRESS);
    }

    // The second reset after a wipe clears the slot (the partner still fighting keeps it).
    void MarkFightReset(Creature* me, Creature* partner)
    {
        if (partner && partner->IsAlive() && partner->IsInCombat())
            return;
        if (InstanceScript* instance = me->GetInstanceScript())
            if (instance->GetBossState(BOSS_COUNCIL) == IN_PROGRESS)
                instance->SetBossState(BOSS_COUNCIL, NOT_STARTED);
    }

    // The boss data, on whichever unit owns the encounter: kill together by percent of health while both stand,
    // Azshir alone while the Champion lies fallen; Holy Light on the interrupt list while Azshir lives.
    void DescribeOn(Creature* owner, bool heroic)
    {
        if (!owner || !owner->IsAlive() || !owner->IsInCombat())
            return;
        Creature* champion = ChampionOf(owner);
        Creature* azshir = AzshirOf(owner);
        bool const azshirAlive = azshir && azshir->IsAlive();
        bool const championStands = ChampionStands(champion);
        BossMechanics::Descriptor d;
        if (azshirAlive)
            d.interrupts.emplace_back(NPC_AZSHIR, SPELL_CV_HOLY_LIGHT, kHolyLightKickPriority(heroic),
                Ms(kHolyLightEveryMs));
        if (azshirAlive && championStands)
        {
            d.targets.push_back(BossMechanics::TargetEntry(NPC_FALLEN_CHAMPION, 1).KillTogether(NPC_AZSHIR,
                kKillTogetherPct));
            d.targets.push_back(BossMechanics::TargetEntry(NPC_AZSHIR, 1).KillTogether(NPC_FALLEN_CHAMPION,
                kKillTogetherPct));
        }
        else if (azshirAlive)
            d.targets.emplace_back(NPC_AZSHIR, 1);
        Mechanic::Describe(owner, std::move(d));
    }

    void DescribeBoth(WorldObject const* me, bool heroic)
    {
        DescribeOn(ChampionOf(me), heroic);
        DescribeOn(AzshirOf(me), heroic);
    }

    // Deals `pct` of the reference row (the tank row on the tank) to `target` with one of our percent spells.
    void CastPercent(Unit* caster, Unit* target, uint32 spellId, float pct)
    {
        if (!caster || !target)
            return;
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(DungeonKit::RefFlatOn(caster, target, pct)));
        caster->CastSpell(target, spellId, args);
    }

    std::string Names(std::vector<Player*> const& players)
    {
        std::string out;
        for (Player const* p : players)
            out += Acore::StringFormat("{}{}", out.empty() ? "" : ",", p->GetName());
        return out.empty() ? "-" : out;
    }

    // CV8: the hammer falls on the room (healed off or on its own). Azshir casts the wave and every hit.
    void ExecutionFalls(Unit* caster, Unit* carrier, uint32 msUp, bool expired)
    {
        if (!caster || !caster->IsAlive() || !caster->IsInWorld())
            return;
        float const pct = ExecutionBurstPct(msUp, expired);
        caster->CastSpell(caster, SPELL_CV_EXECUTION_WAVE, true);
        std::vector<Player*> const room = RoomPlayers(caster);
        for (Player* player : room)
            CastPercent(caster, player, SPELL_CV_EXECUTION_BURST, pct);
        DungeonKit::LogMechanic(kLogDungeon, kAzshirKey, "execution-falls", Acore::StringFormat("carrier={} up={}ms "
            "how={} pct={:.0f} hit={}", carrier ? carrier->GetName() : "-", msUp, expired ? "expired" : "healed-off",
            pct, room.size()));
    }
}

// ====================================================================================================================
// The Fallen Champion: the melee half, the seals, Avenger's Shield, the fall and the rise, Grief
// ====================================================================================================================

// A ScriptedAI on the slot's registry encounter: the instance writes BOSS_COUNCIL DONE, not this script.
struct boss_fallen_champion_rework : public ScriptedAI
{
    explicit boss_fallen_champion_rework(Creature* creature)
        : ScriptedAI(creature), _arena(FightArena(), LeashOptions(kChampionKey)) { }

    void Reset() override
    {
        ScriptedAI::Reset();
        Cleanup();
        Uncollapse(true);
        _arena.Reset();
        _lethal.Reset();
        _raises = 0;
        MarkFightReset(me, AzshirOf(me));
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        _raises = 0;
        _azshirFell = false;
        _lethal.Reset();
        OnBossPull(me, kChampionKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_COUNCIL;
        Mechanic::BeginEncounter(me, options);
        MarkFightStarted(me);

        Creature* azshir = AzshirOf(me);
        RespawnFallenPartner(me, azshir, "pull");
        PullPartner(azshir, who);
        DoZoneInCombat(me, kPullZoneYd);
        _arena.Engage(me);
        StartTimeline(_clockMs);
        DescribeBoth(me, _heroic);
        Log("engage", Acore::StringFormat("heroic={} seal-every={}s raises={} azshir={}", _heroic ? 1 : 0,
            kSealEveryMs(_heroic) / 1000, kMaxRaises(_heroic), azshir && azshir->IsAlive() ? "alive" : "dead"));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        Uncollapse(true);
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
        Creature* azshir = AzshirOf(me);
        EvadePartner(azshir, why);
        RespawnFallenPartner(me, azshir, "evade");
    }

    void JustDied(Unit* killer) override
    {
        ScriptedAI::JustDied(killer);
        Cleanup();
        _arena.Reset();
        Log("death", Acore::StringFormat("killer={} raises={} azshir-fell={}", killer ? killer->GetName() : "none",
            _raises, _azshirFell ? 1 : 0));
        DescribeOn(AzshirOf(me), _heroic);
    }

    // CV1: a lethal hit while Azshir stands (and a raise is left) leaves him at 1 health, fallen.
    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (_fallen)
        {
            damage = 0;
            return;
        }
        if (!me->IsInCombat() || !RaiseNowAllowed())
            return;
        _lethal.Intercept(me, damage, [this]() { Collapse(); });
    }

    void DoAction(int32 action) override
    {
        switch (action)
        {
            case ACTION_CV_VIGIL_RISE:
                _riseQueued = true;
                break;
            case ACTION_CV_AZSHIR_FELL:
                _azshirFellQueued = true;
                break;
            default:
                break;
        }
    }

    uint32 GetData(uint32 id) const override
    {
        switch (id)
        {
            case DATA_CV_FALLEN:    return _fallen ? 1 : 0;
            case DATA_CV_RAISES:    return _raises;
            default:                return 0;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsInCombat())
        {
            // Out of combat while lying fallen (the group died and the combat ran out): back up and home.
            if (_fallen && me->IsAlive())
            {
                Log("vigil-orphaned", "out of combat while fallen: reset");
                Uncollapse(true);
                EnterEvadeMode(EVADE_REASON_NO_HOSTILES);
            }
            return;
        }
        _clockMs += diff;

        if (_azshirFellQueued)
        {
            _azshirFellQueued = false;
            AzshirFell();
            if (!me->IsAlive())
                return;
        }
        if (_fallen)
        {
            UpdateFallen();
            return;
        }
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his lawn, or nobody on it for 10 s: evading

        UpdateGrief();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (!me->HasUnitFlag(UNIT_FLAG_PACIFIED))       // CV4's 2 s pacify: no seal, Judgement or shield either
        {
            if (_clockMs >= _nextSealMs)
                ChangeSeal();
            if (_clockMs >= _nextJudgementMs)
                Judgement();
            if (_clockMs >= _nextShieldMs && !me->HasUnitState(UNIT_STATE_CASTING))
                StartShield();
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm council ...`
    // ----------------------------------------------------------------------------------------------------------------

    std::string TestFight() const
    {
        if (!me->IsAlive() || !me->IsInCombat())
            return "The Fallen Champion is not fighting (pull him first: the mechanics aim at his threat list).";
        if (_fallen)
            return "The Fallen Champion lies fallen (the Last Vigil).";
        return {};
    }

    std::string TestSeal()
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        _nextSealMs = _clockMs;
        ChangeSeal();
        return {};
    }

    std::string TestJudgement()
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        Judgement();
        return {};
    }

    std::string TestShield()
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        if (JusticeMarkUp(me))
            return "A Justice mark is up: the shield waits for it.";
        if (!StartShield())
            return "Nobody more than 10 yd from him to throw it at.";
        return {};
    }

    std::string TestFall()
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        if (!RaiseNowAllowed())
            return "No raise now (Azshir is dead or the raises are spent): his death would be real.";
        me->SetHealth(1);
        Collapse();
        return {};
    }

    std::string TestGrief()
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        AddGrief();
        return {};
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s seal={} next-seal={}s next-judgement={}s next-shield={}s fallen={} "
            "raises={} azshir-fell={} grief={} heroic={}", _clockMs / 1000, SealName(SealAt(_sealsCalled ?
            _sealsCalled - 1 : 0)), _nextSealMs / 1000, _nextJudgementMs / 1000, _nextShieldMs / 1000, _fallen ? 1 : 0,
            _raises, _azshirFell ? 1 : 0, DungeonKit::Stacks(me, SPELL_CV_GRIEF), _heroic ? 1 : 0);
    }

    // Registry callbacks reach the AI through its guid (never a captured `this`).
    template <class Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnChampion(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* champion = map->GetCreature(guid);
            if (!champion || !champion->IsAlive() || !champion->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_fallen_champion_rework*>(champion->AI()))
                fn(*ai, result);
        };
    }

private:
    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kChampionKey, mechanic, detail);
    }

    // Every percent of his, raised by Grief.
    float Pct(NH<float> const& pct) const
    {
        return pct(_heroic) * GriefDamageFactor(DungeonKit::Stacks(me, SPELL_CV_GRIEF));
    }

    bool RaiseNowAllowed() const
    {
        Creature* azshir = AzshirOf(me);
        return !_azshirFell && azshir && azshir->IsAlive() && RaiseAllowed(_heroic, _raises);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The timeline (restarted at the rise: the seal cycle starts again with Command)
    // ----------------------------------------------------------------------------------------------------------------

    void StartTimeline(uint64 at)
    {
        _sealsCalled = 0;
        _nextSealMs = at;
        _nextJudgementMs = at + kJudgementFirstMs;
        _shieldPlannedMs = at + kShieldFirstMs;
        _nextShieldMs = _shieldPlannedMs;
    }

    // CV6: the next seal in the order, its aura and emote; Command's front for the seal's length.
    void ChangeSeal()
    {
        DropSeal();
        Seal const seal = SealAt(_sealsCalled++);
        _nextSealMs = NextDue(_nextSealMs, kSealEveryMs(_heroic), _clockMs);
        me->CastSpell(me, SealAura(seal), true);
        Talk(SealEmote(seal));
        if (seal == Seal::Command)
            RegisterCommand();
        Log("seal", Acore::StringFormat("seal={} next={}s", SealName(seal), _nextSealMs / 1000));
    }

    void DropSeal()
    {
        for (Seal s : { Seal::Command, Seal::Righteousness, Seal::Justice })
            me->RemoveAurasDueToSpell(SealAura(s));
        CancelHandle(_command);
    }

    // CV6b: his swings cleave his front while the seal holds (the tank exempt: the bot tank faces him away).
    void RegisterCommand()
    {
        uint32 const sealMs = kSealEveryMs(_heroic);
        uint32 const lifeMs = sealMs > kSealWarnMs ? sealMs - kSealWarnMs : kSwingTickMs;
        float const pct = Pct(kCommandPct);
        MechanicRef ref = Mechanic::Cone(me, me, kCommandConeDeg, kCommandLengthYd, Ms(kSealWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Persistent(Ms(lifeMs), Ms(kSwingTickMs)).Damage(pct).Weakened().School(SPELL_SCHOOL_NORMAL)
            .Spell(SPELL_CV_COMMAND_CLEAVE).Within(LawnBounds()).Tag(TAG_CV_COMMAND);
        _command = ref;
        Log("command", Acore::StringFormat("front={}deg x {}yd for {}ms pct={:.0f}", kCommandConeDeg,
            kCommandLengthYd, lifeMs, pct));
    }

    // CV6a: the tank hit, then the seal's rider.
    void Judgement()
    {
        _nextJudgementMs = NextDue(_nextJudgementMs, kJudgementEveryMs, _clockMs);
        Unit* tank = me->GetVictim();
        if (!tank)
            return;
        float const pct = Pct(kJudgementTankPct);
        CastPercent(me, tank, SPELL_CV_JUDGEMENT, pct);
        Seal const seal = SealAt(_sealsCalled ? _sealsCalled - 1 : 0);
        Log("judgement", Acore::StringFormat("tank={} pct={:.0f} seal={}", tank->GetName(), pct, SealName(seal)));
        switch (RiderOf(seal))
        {
            case Rider::Brand:
                Brands();
                break;
            case Rider::Mark:
                Mark();
                break;
            case Rider::None:
                break;
        }
    }

    // CV6c: 2 / 3 random non-tank players branded; 5 s later each burst hits the others within 6 yd.
    void Brands()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        std::vector<Player*> const picks = DungeonKit::PickPlayers(me, rule, kBrandCount(_heroic));
        if (picks.empty())
            return;
        GuidSet carriers;
        for (Player* p : picks)
        {
            carriers.insert(p->GetGUID());
            me->AddAura(SPELL_CV_RIGHTEOUS_BRAND, p);
        }
        float const pct = Pct(kRighteousnessPct);
        MechanicRef ref = Mechanic::Spread(me, kRighteousnessRadiusYd, Ms(kBrandMs));
        ref.Targets(carriers).Damage(pct).TankDamage(pct).Weakened().School(SPELL_SCHOOL_HOLY)
            .Spell(SPELL_CV_RIGHTEOUS_BURST).Within(LawnBounds()).Tag(TAG_CV_BRAND);
        _brand = ref;
        Log("brand", Acore::StringFormat("carriers={} radius={}yd pct={:.0f}", Names(picks), kRighteousnessRadiusYd,
            pct));
    }

    // CV6d: a random player, the tank included, marked; 5 s later the hammer is split among everyone within 6 yd.
    void Mark()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return;
        me->AddAura(SPELL_CV_JUSTICE_MARK, target);
        ObjectGuid const marked = target->GetGUID();
        MechanicRef ref = Mechanic::Stack(me, target, kJusticeRadiusYd, Ms(kJusticeMarkMs));
        ref.Within(LawnBounds()).Tag(TAG_CV_JUSTICE);
        ref.OnResolve(OnChampion([marked](boss_fallen_champion_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.HammerFalls(marked, r.hits);
        }));
        _justice = ref;
        Log("mark", Acore::StringFormat("target={} radius={}yd total={:.0f} cap={:.0f}", target->GetName(),
            kJusticeRadiusYd, Pct(kJusticeTotalPct), kJusticeShareCapPct(_heroic)));
    }

public:
    // CV6d's fall: the split among the players inside (the marked alone when nobody stood with him).
    void HammerFalls(ObjectGuid marked, std::vector<ObjectGuid> const& inside)
    {
        _justice = {};
        std::vector<Unit*> takers;
        for (ObjectGuid const& g : inside)
            if (Player* p = ObjectAccessor::GetPlayer(*me, g))
                if (p->IsAlive())
                    takers.push_back(p);
        Player* target = ObjectAccessor::GetPlayer(*me, marked);
        if (takers.empty() && target && target->IsAlive())
            takers.push_back(target);
        std::vector<std::pair<ObjectGuid, uint32>> const shares = DungeonKit::SplitShares(me, takers,
            Pct(kJusticeTotalPct), kJusticeShareCapPct(_heroic));
        uint32 each = 0;
        for (auto const& [guid, amount] : shares)
            if (Player* p = ObjectAccessor::GetPlayer(*me, guid))
            {
                CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
                args.AddSpellBP0(static_cast<int32>(amount));
                me->CastSpell(p, SPELL_CV_JUSTICE_HAMMER, args);
                each = amount;
            }
        if (target)
            target->RemoveAurasDueToSpell(SPELL_CV_JUSTICE_MARK);
        Log("hammer", Acore::StringFormat("marked={} inside={} share={}", target ? target->GetName() : "-",
            takers.size(), each));
    }

    // CV7's landing: the first target and the bounces, nearest first.
    void ShieldLands(ObjectGuid firstGuid)
    {
        _shield = {};
        Player* first = ObjectAccessor::GetPlayer(*me, firstGuid);
        if (!first || !first->IsAlive())
        {
            Log("shield-lost", "the target is gone");
            return;
        }
        std::vector<Player*> room = RoomPlayers(me);
        if (std::find(room.begin(), room.end(), first) == room.end())
            room.push_back(first);
        std::vector<Vec2> points;
        std::size_t firstIndex = 0;
        for (std::size_t i = 0; i < room.size(); ++i)
        {
            points.push_back(DungeonKit::PlaneOf(room[i]));
            if (room[i] == first)
                firstIndex = i;
        }
        std::vector<std::size_t> const chain = ShieldChain(points, firstIndex, kShieldBounceYd,
            kShieldHits(_heroic));
        std::vector<Player*> hit;
        for (std::size_t n = 0; n < chain.size(); ++n)
        {
            Player* p = room[chain[n]];
            hit.push_back(p);
            if (n == 0)
            {
                CastPercent(me, p, SPELL_CV_AVENGERS_SHIELD, Pct(kShieldFirstPct));
                continue;
            }
            CastPercent(me, p, SPELL_CV_AVENGERS_SHIELD_BOUNCE, Pct(kShieldBouncePct));
            BossMechanics::Weakened::AddStack(p);
        }
        Log("shield", Acore::StringFormat("chain={} hits={} first={:.0f} bounce={:.0f}", Names(hit), hit.size(),
            Pct(kShieldFirstPct), Pct(kShieldBouncePct)));
    }

private:
    // CV7: the 2 s bar at a random player more than 10 yd away (waits while a Justice mark is up). False: nobody.
    bool StartShield()
    {
        if (JusticeMarkUp(me))
        {
            _nextShieldMs = _clockMs + kRetryMs;
            return false;
        }
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.minRange = kShieldMinRangeYd;
        Player* first = DungeonKit::PickPlayer(me, rule);
        if (!first)
        {
            _nextShieldMs = _clockMs + kRetryMs;
            return false;
        }
        _shieldPlannedMs = NextDue(_shieldPlannedMs, kShieldEveryMs, _clockMs);
        _nextShieldMs = _shieldPlannedMs;

        // The bots spread from the target: the players more than 10 yd from him (the melee and the tank stay on him,
        // the large-spread exemption).
        BossMechanics::Eligibility far;
        for (Player* p : RoomPlayers(me))
            if (me->GetExactDist2d(p) > kShieldMinRangeYd)
                far.carriers.insert(p->GetGUID());
        ObjectGuid const target = first->GetGUID();
        GuidSet const carriers{ target };
        MechanicRef ref = Mechanic::Spread(me, kShieldBounceYd, Ms(kShieldCastMs));
        ref.Targets(carriers).Eligible(far).Within(LawnBounds()).Tag(TAG_CV_SHIELD);
        ref.OnResolve(OnChampion([target](boss_fallen_champion_rework& ai, BossMechanics::ResolveResult const&)
        {
            ai.ShieldLands(target);
        }));
        _shield = ref;
        me->SetFacingToObject(first);
        DungeonKit::CastBar(me, SPELL_CV_AVENGERS_SHIELD_CAST);
        Log("shield-cast", Acore::StringFormat("target={} far={} next={}s", first->GetName(), far.carriers.size(),
            _nextShieldMs / 1000));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CV1 The Last Vigil: the fall, the rise, the real death, Grief
    // ----------------------------------------------------------------------------------------------------------------

    void Collapse()
    {
        _fallen = true;
        _fallenAtMs = _clockMs;
        ++_raises;
        _riseQueued = false;
        CancelLive();
        DropSeal();
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        me->SetControlled(true, UNIT_STATE_ROOT);
        me->SetUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
        me->SetStandState(UNIT_STAND_STATE_DEAD);
        me->SetRegeneratingHealth(false);
        me->RemoveAurasDueToSpell(SPELL_CV_GRIEF);
        if (Aura* ring = me->AddAura(SPELL_CV_LAST_VIGIL_RING, me))
            ring->SetDuration(static_cast<int32>(kVigilRingMs));
        Creature* azshir = AzshirOf(me);
        if (azshir && azshir->IsAlive() && azshir->IsAIEnabled && azshir->AI())
            azshir->AI()->DoAction(ACTION_CV_VIGIL_BEGIN);
        DescribeBoth(me, _heroic);
        Log("fallen", Acore::StringFormat("raise={} rise-at={:.0f}% channel={}ms", _raises,
            RiseHealthPct(_heroic, _raises), kVigilChannelMs));
    }

    // Back on his feet: before the rise and the real kill (`wipe` false), or on a wipe (full health, aggressive).
    void Uncollapse(bool wipe)
    {
        bool const was = _fallen;
        _fallen = false;
        _riseQueued = false;
        me->RemoveUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
        me->SetStandState(UNIT_STAND_STATE_STAND);
        me->SetControlled(false, UNIT_STATE_ROOT);
        me->SetRegeneratingHealth(me->GetCreatureTemplate()->RegenHealth);
        me->RemoveAurasDueToSpell(SPELL_CV_LAST_VIGIL_RING);
        if (!wipe)
            return;
        me->SetReactState(REACT_AGGRESSIVE);
        if (was && me->IsAlive())
            me->SetFullHealth();
    }

    void UpdateFallen()
    {
        if (_riseQueued)
        {
            Rise();
            return;
        }
        if (_clockMs - _fallenAtMs < kVigilWatchdogMs)
            return;
        // No word from Azshir after his channel: settle it here.
        Creature* azshir = AzshirOf(me);
        if (azshir && azshir->IsAlive() && azshir->IsInCombat())
            Rise();
        else if (!azshir || !azshir->IsAlive())
            KillFallen("watchdog");
        else
        {
            Log("vigil-orphaned", "Azshir left the fight: both reset");
            EnterEvadeMode(EVADE_REASON_OTHER);
        }
    }

    void Rise()
    {
        Uncollapse(false);
        float const pct = RiseHealthPct(_heroic, _raises);
        me->SetHealth(std::max<uint32>(1, me->CountPctFromMaxHealth(static_cast<int32>(pct))));
        me->SetReactState(REACT_AGGRESSIVE);
        me->CastSpell(me, SPELL_CV_LAST_VIGIL_RISE, true);
        _lethal.Reset();
        DoZoneInCombat(me, kPullZoneYd);
        if (Unit* victim = SelectTarget(SelectTargetMethod::MaxThreat, 0))
            AttackStart(victim);
        StartTimeline(_clockMs);
        DescribeBoth(me, _heroic);
        Log("rise", Acore::StringFormat("raise={} health={:.0f}% next-allowed={}", _raises, pct,
            RaiseAllowed(_heroic, _raises) ? 1 : 0));
    }

    // Azshir died while he lay fallen: the death is real now (the loot recipient as the killer, so the loot and the
    // instance's credit land).
    void KillFallen(char const* why)
    {
        Player* killer = me->GetLootRecipient();
        if (!killer || !killer->IsInMap(me))
        {
            killer = nullptr;
            for (auto const& ref : me->GetMap()->GetPlayers())
                if (Player* p = ref.GetSource())
                    if (p->IsAlive() && !p->IsGameMaster())
                    {
                        killer = p;
                        break;
                    }
        }
        Log("fallen-death", Acore::StringFormat("why={} killer={}", why, killer ? killer->GetName() : "-"));
        Uncollapse(false);
        Unit::Kill(killer ? static_cast<Unit*>(killer) : static_cast<Unit*>(me), me);
    }

    void AzshirFell()
    {
        if (_azshirFell)
            return;
        _azshirFell = true;
        if (_fallen)
        {
            KillFallen("azshir-died");
            return;
        }
        _lethal.Disarm();
        Talk(EMOTE_CHAMPION_GRIEF);
        _nextGriefMs = _clockMs + kGriefEveryMs;
        DescribeBoth(me, _heroic);
        Log("grief-begins", Acore::StringFormat("every={}s cap={}", kGriefEveryMs / 1000, kGriefMaxStacks(_heroic)));
    }

    void UpdateGrief()
    {
        if (!_azshirFell || _clockMs < _nextGriefMs)
            return;
        _nextGriefMs = NextDue(_nextGriefMs, kGriefEveryMs, _clockMs);
        AddGrief();
    }

    void AddGrief()
    {
        uint32 const before = DungeonKit::Stacks(me, SPELL_CV_GRIEF);
        uint32 const now = DungeonKit::AddStacks(me, SPELL_CV_GRIEF, 1, me, kGriefMaxStacks(_heroic));
        if (now != before)
            Log("grief", Acore::StringFormat("stacks={} damage=x{:.1f}", now, GriefDamageFactor(now)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Cleanup (reset, evade, death, the fall)
    // ----------------------------------------------------------------------------------------------------------------

    void CancelHandle(MechanicHandle& handle)
    {
        if (handle)
            Mechanic::Cancel(me, handle);
        handle = {};
    }

    // The live mechanics and the debuffs they put on players.
    void CancelLive()
    {
        CancelHandle(_command);
        CancelHandle(_brand);
        CancelHandle(_justice);
        CancelHandle(_shield);
        if (InstanceScript* instance = me->GetInstanceScript())
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_CV_RIGHTEOUS_BRAND);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_CV_JUSTICE_MARK);
        }
    }

    void Cleanup()
    {
        CancelLive();
        DropSeal();
        me->RemoveAurasDueToSpell(SPELL_CV_GRIEF);
        me->RemoveAurasDueToSpell(SPELL_CV_LAST_VIGIL_RING);
        _azshirFell = false;
        _azshirFellQueued = false;
        _riseQueued = false;
        _nextGriefMs = 0;
        _clockMs = 0;
        StartTimeline(0);
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::LethalGuard _lethal;
    bool _heroic = false;
    uint64 _clockMs = 0;
    uint32 _sealsCalled = 0;
    uint64 _nextSealMs = 0;
    uint64 _nextJudgementMs = 0;
    uint64 _shieldPlannedMs = 0;
    uint64 _nextShieldMs = 0;
    MechanicHandle _command;
    MechanicHandle _brand;
    MechanicHandle _justice;
    MechanicHandle _shield;
    bool _fallen = false;
    uint64 _fallenAtMs = 0;
    uint32 _raises = 0;
    bool _riseQueued = false;
    bool _azshirFell = false;
    bool _azshirFellQueued = false;
    uint64 _nextGriefMs = 0;
};

// ====================================================================================================================
// Azshir the Sleepless: the caster half, the Last Vigil's channel, Execution Sentence (heroic)
// ====================================================================================================================

// A ScriptedAI on the slot's registry encounter: the instance writes BOSS_COUNCIL DONE, not this script.
struct boss_azshir_the_sleepless_rework : public ScriptedAI
{
    // His casts (the CastQueue's ids; `.dbtest sm council <cast>` fires one by id).
    enum QueueIds : uint32
    {
        Q_SHOCK     = 1,
        Q_EXORCISM  = 2,
        Q_WRATH     = 3,
        Q_LIGHT     = 4,
        Q_EXECUTION = 5,
    };

private:
    static uint8 constexpr kPriorityExecution = 4;
    static uint8 constexpr kPriorityZone = 3;
    static uint8 constexpr kPriorityLight = 2;
    static uint8 constexpr kPriorityShock = 1;

    // He never moves: only the no-target leash (nobody in combat with him on the lawn for 10 s: he evades).
    static DungeonKit::ArenaGuardOptions AzshirLeash()
    {
        DungeonKit::ArenaGuardOptions o = LeashOptions(kAzshirKey);
        o.holdWhileVictimOff = false;
        o.switchWhenVictimOff = false;
        o.evadeWhenBossOff = false;
        return o;
    }

public:
    explicit boss_azshir_the_sleepless_rework(Creature* creature)
        : ScriptedAI(creature), _arena(FightArena(), AzshirLeash()), _queue(kCastSpacingMs) { }

    void Reset() override
    {
        ScriptedAI::Reset();
        me->SetCombatMovement(false);
        Cleanup();
        _arena.Reset();
        MarkFightReset(me, ChampionOf(me));
    }

    // He never chases and never swings (a ghost at his post).
    void AttackStart(Unit* who) override
    {
        if (who)
            me->Attack(who, false);
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;

        Cleanup();
        _heroic = IsHeroicMap(me);
        OnBossPull(me, kAzshirKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_COUNCIL;
        Mechanic::BeginEncounter(me, options);
        MarkFightStarted(me);
        Talk(YELL_AZSHIR_AGGRO);

        Creature* champion = ChampionOf(me);
        RespawnFallenPartner(me, champion, "pull");
        PullPartner(champion, who);
        DoZoneInCombat(me, kPullZoneYd);
        _arena.Engage(me);
        ScheduleFight();
        DescribeBoth(me, _heroic);
        Log("engage", Acore::StringFormat("heroic={} execution={}", _heroic ? 1 : 0, _heroic ? "on" : "off"));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
        Creature* champion = ChampionOf(me);
        EvadePartner(champion, why);
        RespawnFallenPartner(me, champion, "evade");
    }

    void JustDied(Unit* killer) override
    {
        ScriptedAI::JustDied(killer);
        Cleanup();
        _arena.Reset();
        Creature* champion = ChampionOf(me);
        if (champion && champion->IsAlive() && champion->IsAIEnabled && champion->AI())
            champion->AI()->DoAction(ACTION_CV_AZSHIR_FELL);
        Log("death", Acore::StringFormat("killer={} champion={}", killer ? killer->GetName() : "none",
            !champion || !champion->IsAlive() ? "dead" : (ChampionStands(champion) ? "standing" : "fallen")));
    }

    void DoAction(int32 action) override
    {
        if (action == ACTION_CV_VIGIL_BEGIN)
            _vigilQueued = true;
    }

    // A Holy Light kicked or cancelled: the queue's hold ends with it (rule 13). Only Holy Light can be.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        ScriptedAI::OnSpellFailed(spell);
        if (!spell || spell->Id != SPELL_CV_HOLY_LIGHT || !me->IsInCombat())
            return;
        _queue.Interrupted(_clockMs);
        if (!_selfCancel)
            Log("holy-light-interrupted", "reward");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsInCombat())
            return;
        _clockMs += diff;

        if (_vigilQueued)
        {
            _vigilQueued = false;
            BeginVigil();
        }
        if (_vigil && _clockMs >= _vigilEndMs)
            EndVigil();
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // nobody on his lawn for 10 s: evading
        if (_vigil || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        RunQueue();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm council ...`
    // ----------------------------------------------------------------------------------------------------------------

    std::string TestFight() const
    {
        if (!me->IsAlive() || !me->IsInCombat())
            return "Azshir is not fighting (pull the council first: the mechanics aim at his threat list).";
        if (_vigil)
            return "Azshir is channeling the Last Vigil.";
        return {};
    }

    std::string TestFire(uint32 id)
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return "Azshir is casting; try again in a moment.";
        if (!Fire(id))
            return "Nobody to aim it at (a GM does not count).";
        // Fire took the cast off the queue: its next turn stays the planned one.
        _queue.Schedule(id, std::max<uint64>(PlannedOf(id), _clockMs + kRetryMs), PriorityOf(id));
        return {};
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s vigil={} shock={}s exorcism={}s wrath={}s light={}s execution={}s "
            "heroic={}", _clockMs / 1000, _vigil ? 1 : 0, _shockAt / 1000, _exorcismAt / 1000, _wrathAt / 1000,
            _lightAt / 1000, _heroic ? _executionAt / 1000 : 0, _heroic ? 1 : 0);
    }

    template <class Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnAzshir(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* azshir = map->GetCreature(guid);
            if (!azshir || !azshir->IsAlive() || !azshir->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_azshir_the_sleepless_rework*>(azshir->AI()))
                fn(*ai, result);
        };
    }

    // CV4's resolve: the Champion standing inside the ring burns for 5% of his health and is pacified 2 s.
    void WrathResolved()
    {
        Creature* champion = ChampionOf(me);
        if (!ChampionStands(champion) || me->GetExactDist2d(champion) > kHolyWrathRadiusYd
            || std::fabs(champion->GetPositionZ() - me->GetPositionZ()) > kZBandYd)
            return;
        me->CastSpell(champion, SPELL_CV_HOLY_WRATH_BURN, true);
        Log("wrath-burns-champion", Acore::StringFormat("dist={:.1f} pacify={}ms", me->GetExactDist2d(champion),
            kPacifyMs));
    }

private:
    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kAzshirKey, mechanic, detail);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The timeline
    // ----------------------------------------------------------------------------------------------------------------

    void ScheduleFight()
    {
        _clockMs = 0;
        _queue.Reset();
        _shockAt = kHolyShockFirstMs;
        _exorcismAt = kExorcismFirstMs;
        _wrathAt = kHolyWrathFirstMs;
        _lightAt = kHolyLightFirstMs;
        _executionAt = kExecutionFirstMs;
        _queue.Schedule(Q_SHOCK, _shockAt, kPriorityShock);
        _queue.Schedule(Q_EXORCISM, _exorcismAt, kPriorityZone);
        _queue.Schedule(Q_WRATH, _wrathAt, kPriorityZone);
        _queue.Schedule(Q_LIGHT, _lightAt, kPriorityLight);
        if (_heroic)
            _queue.Schedule(Q_EXECUTION, _executionAt, kPriorityExecution);
    }

    void RunQueue()
    {
        std::optional<uint32> const next = _queue.Next(_clockMs);
        if (!next)
            return;
        uint64& planned = PlannedOf(*next);
        if (!Fire(*next))
        {
            _queue.Schedule(*next, _clockMs + kRetryMs, PriorityOf(*next));     // nobody to aim at: the plan stays
            return;
        }
        planned = NextDue(planned, EveryOf(*next), _clockMs);
        _queue.Schedule(*next, planned, PriorityOf(*next));
    }

    uint64& PlannedOf(uint32 id)
    {
        switch (id)
        {
            case Q_SHOCK:       return _shockAt;
            case Q_EXORCISM:    return _exorcismAt;
            case Q_WRATH:       return _wrathAt;
            case Q_LIGHT:       return _lightAt;
            default:            return _executionAt;
        }
    }

    static uint32 EveryOf(uint32 id)
    {
        switch (id)
        {
            case Q_SHOCK:       return kHolyShockEveryMs;
            case Q_EXORCISM:    return kExorcismEveryMs;
            case Q_WRATH:       return kHolyWrathEveryMs;
            case Q_LIGHT:       return kHolyLightEveryMs;
            default:            return kExecutionEveryMs;
        }
    }

    static uint8 PriorityOf(uint32 id)
    {
        switch (id)
        {
            case Q_SHOCK:       return kPriorityShock;
            case Q_LIGHT:       return kPriorityLight;
            case Q_EXECUTION:   return kPriorityExecution;
            default:            return kPriorityZone;
        }
    }

    // One cast now; false: nobody to aim it at (or the cast was refused).
    bool Fire(uint32 id)
    {
        switch (id)
        {
            case Q_SHOCK:       return HolyShock();
            case Q_EXORCISM:    return Exorcism();
            case Q_WRATH:       return HolyWrath();
            case Q_LIGHT:       return HolyLight();
            case Q_EXECUTION:   return ExecutionSentence();
            default:            return false;
        }
    }

    // CV2: instant, a random player, the tank included.
    bool HolyShock()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return false;
        float const pct = kHolyShockPct(_heroic);
        CastPercent(me, target, SPELL_CV_HOLY_SHOCK, pct);
        _queue.Started(Q_SHOCK, _clockMs, 0);
        Log("holy-shock", Acore::StringFormat("target={} pct={:.0f}", target->GetName(), pct));
        return true;
    }

    // CV5: the 2 s bar; the 4 yd line from him through the target's spot now, 40 yd long (normal: never at the
    // player marked by Justice; heroic: through the stack too).
    bool Exorcism()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        if (!_heroic)
            for (Player* p : RoomPlayers(me))
                if (p->HasAura(SPELL_CV_JUSTICE_MARK))
                    rule.exclude.push_back(p->GetGUID().GetRawValue());
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return false;
        float const facing = LineFacing(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(target))
            .value_or(me->GetOrientation());
        Position const from = me->GetPosition();
        float const pct = kExorcismPct(_heroic);
        MechanicRef ref = Mechanic::Line(me, from, facing, kExorcismLengthYd, kExorcismWidthYd, Ms(kExorcismCastMs));
        ref.Damage(pct).TankDamage(pct).Weakened().School(SPELL_SCHOOL_HOLY).Spell(SPELL_CV_EXORCISM)
            .Within(LawnBounds()).Tag(TAG_CV_EXORCISM);
        me->SetFacingTo(facing);
        DungeonKit::CastBar(me, SPELL_CV_EXORCISM_CAST);
        _queue.Started(Q_EXORCISM, _clockMs, kExorcismCastMs);
        Log("exorcism", Acore::StringFormat("through={} facing={:.2f} pct={:.0f}", target->GetName(), facing, pct));
        return true;
    }

    // CV4: the 2 s bar; the 10 yd ring round him; the bot tank parks the Champion at its edge (the reward).
    bool HolyWrath()
    {
        Creature* champion = ChampionOf(me);
        float const pct = kHolyWrathPct(_heroic);
        MechanicRef ref = Mechanic::Circle(me, me, kHolyWrathRadiusYd, Ms(kHolyWrathCastMs));
        ref.Damage(pct).TankDamage(pct).Weakened().School(SPELL_SCHOOL_HOLY).Spell(SPELL_CV_HOLY_WRATH)
            .Within(LawnBounds()).Tag(TAG_CV_WRATH);
        if (ChampionStands(champion))
            ref.Park(champion);
        ref.OnResolve(OnAzshir([](boss_azshir_the_sleepless_rework& ai, BossMechanics::ResolveResult const&)
        {
            ai.WrathResolved();
        }));
        DungeonKit::CastBar(me, SPELL_CV_HOLY_WRATH_CAST);
        _queue.Started(Q_WRATH, _clockMs, kHolyWrathCastMs);
        Log("holy-wrath", Acore::StringFormat("radius={}yd pct={:.0f} champion-dist={:.1f}", kHolyWrathRadiusYd, pct,
            champion ? me->GetExactDist2d(champion) : -1.f));
        return true;
    }

    // CV3: the 2.5 s heal on the brother with the lower percent of health (interruptible: the cast is real).
    bool HolyLight()
    {
        Creature* champion = ChampionOf(me);
        bool const championUp = ChampionStands(champion);
        Brother const pick = HolyLightTarget(championUp ? champion->GetHealthPct() : 100.f, me->GetHealthPct(),
            championUp);
        Unit* target = pick == Brother::Champion ? static_cast<Unit*>(champion) : static_cast<Unit*>(me);
        float const pct = kHolyLightHealPct(_heroic);
        CastSpellExtraArgs args;
        args.AddSpellBP0(static_cast<int32>(pct));
        SpellCastResult const result = me->CastSpell(target, SPELL_CV_HOLY_LIGHT, args);
        if (result != SPELL_CAST_OK)
        {
            Log("holy-light-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        _queue.Started(Q_LIGHT, _clockMs, kHolyLightCastMs);
        Log("holy-light", Acore::StringFormat("target={} heal={:.0f}% champion={:.1f}% azshir={:.1f}%",
            target->GetName(), pct, championUp ? champion->GetHealthPct() : 0.f, me->GetHealthPct()));
        return true;
    }

    // CV8 (heroic): the hammer over a random player, the tank included.
    bool ExecutionSentence()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        for (Player* p : RoomPlayers(me))
            if (p->HasAura(SPELL_CV_EXECUTION_SENTENCE))
                rule.exclude.push_back(p->GetGUID().GetRawValue());
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return false;
        me->CastSpell(target, SPELL_CV_EXECUTION_SENTENCE, true);
        Talk(EMOTE_AZSHIR_EXECUTION, target);
        _queue.Started(Q_EXECUTION, _clockMs, 0);
        Log("execution", Acore::StringFormat("target={} absorb={}", target->GetName(),
            DungeonKit::RefFlatOn(me, target, kExecutionAbsorbPct)));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CV1 the channel
    // ----------------------------------------------------------------------------------------------------------------

    void BeginVigil()
    {
        Creature* champion = ChampionOf(me);
        if (!champion || !champion->IsAlive())
            return;
        _vigil = true;
        _vigilEndMs = _clockMs + kVigilChannelMs;
        _queue.SetBusy(true);
        _selfCancel = true;
        me->InterruptNonMeleeSpells(false);
        _selfCancel = false;
        Talk(YELL_AZSHIR_VIGIL);
        me->StopMoving();
        me->SetFacingToObject(champion);
        // Triggered (MN-5): a kicked Holy Light locks his Holy school and an untriggered cast would be refused
        // (Spell::CheckCast, IsSpellProhibited); a triggered channel still shows its bar (Spell::prepare).
        SpellCastResult const result = me->CastSpell(me, SPELL_CV_LAST_VIGIL, true);
        if (result != SPELL_CAST_OK)
            Log("vigil-bar-refused", Acore::StringFormat("result={}", uint32(result)));
        Log("vigil", Acore::StringFormat("channel={}ms raise={}", kVigilChannelMs,
            champion->AI() ? champion->AI()->GetData(DATA_CV_RAISES) : 0));
    }

    void EndVigil()
    {
        _vigil = false;
        _queue.SetBusy(false);
        me->RemoveAurasDueToSpell(SPELL_CV_LAST_VIGIL);
        Creature* champion = ChampionOf(me);
        if (champion && champion->IsAlive() && champion->IsAIEnabled && champion->AI())
            champion->AI()->DoAction(ACTION_CV_VIGIL_RISE);
        Log("vigil-ends", "the brother rises");
    }

    void Cleanup()
    {
        _queue.Reset();
        _vigil = false;
        _vigilQueued = false;
        _clockMs = 0;
        me->RemoveAurasDueToSpell(SPELL_CV_LAST_VIGIL);
        // Removed by default: the hammer neither falls nor counts (CV8 reads only healed-off and expired).
        if (InstanceScript* instance = me->GetInstanceScript())
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_CV_EXECUTION_SENTENCE);
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CastQueue _queue;
    bool _heroic = false;
    uint64 _clockMs = 0;
    uint64 _shockAt = 0;
    uint64 _exorcismAt = 0;
    uint64 _wrathAt = 0;
    uint64 _lightAt = 0;
    uint64 _executionAt = 0;
    bool _vigil = false;
    bool _vigilQueued = false;
    uint64 _vigilEndMs = 0;
    bool _selfCancel = false;
};

// ====================================================================================================================
// Spell scripts
// ====================================================================================================================

// CV4 212394 on the Champion: exactly 5% of his maximum health (a DUMMY dealing it itself, never lethal: his fall is
// the Last Vigil's), Holy; the pacify is the spell's own aura (2 s, not a stun: his stun immunity stays).
class spell_sm_council_holy_wrath_burn : public SpellScript
{
    PrepareSpellScript(spell_sm_council_holy_wrath_burn);

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || !target->IsAlive() || target->GetHealth() <= 1)
            return;
        uint32 const burn = std::min<uint32>(CalculatePct(target->GetMaxHealth(), kHolyWrathBurnPct),
            target->GetHealth() - 1);
        SpellNonMeleeDamage damage(caster, target, GetSpellInfo(), SPELL_SCHOOL_MASK_HOLY);
        damage.damage = burn;
        caster->SendSpellNonMeleeDamageLog(&damage);
        caster->DealSpellDamage(&damage, false);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_sm_council_holy_wrath_burn::HandleDummy, EFFECT_0,
            SPELL_EFFECT_DUMMY);
    }
};

// CV8 212413 Execution Sentence: the absorb is 75% of the reference row (the tank row on the tank), set at
// application; when healing strips it (AURA_REMOVE_BY_ENEMY_SPELL, Unit::CalcHealAbsorb) the hammer falls on the room
// for 10% + 5% a second it was up; when it runs out (EXPIRE, 8 s) for 50%. Any other removal (death, cleanup) is
// silent.
class spell_sm_council_execution_sentence : public AuraScript
{
    PrepareAuraScript(spell_sm_council_execution_sentence);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        Unit* owner = GetUnitOwner();
        if (caster && owner)
            amount = static_cast<int32>(DungeonKit::RefFlatOn(caster, owner, kExecutionAbsorbPct));
    }

    void AfterRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        AuraRemoveMode const why = GetTargetApplication() ? GetTargetApplication()->GetRemoveMode()
            : AURA_REMOVE_BY_DEFAULT;
        bool const healed = why == AURA_REMOVE_BY_ENEMY_SPELL;
        bool const expired = why == AURA_REMOVE_BY_EXPIRE;
        if (!healed && !expired)
            return;
        int32 const max = GetMaxDuration();
        int32 const left = std::max(0, GetDuration());
        uint32 const msUp = expired ? kExecutionMs : static_cast<uint32>(std::max(0, max - left));
        ExecutionFalls(GetCaster(), GetTarget(), msUp, expired);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sm_council_execution_sentence::CalcAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_HEAL_ABSORB);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sm_council_execution_sentence::AfterRemove, EFFECT_0,
            SPELL_AURA_SCHOOL_HEAL_ABSORB, AURA_EFFECT_HANDLE_REAL);
    }
};

// ====================================================================================================================
// `.dbtest sm council <mechanic>`
// ====================================================================================================================

namespace
{
    boss_fallen_champion_rework* FindChampionAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_FALLEN_CHAMPION);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_fallen_champion_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Fallen Champion is not running boss_fallen_champion_rework (check "
                "the ScriptName).");
        return ai;
    }

    boss_azshir_the_sleepless_rework* FindAzshirAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_AZSHIR);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_azshir_the_sleepless_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Azshir is not running boss_azshir_the_sleepless_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Finish(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Council: {} fired ({}).", what,
            IsHeroicMap(handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr) ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_FALLEN_CHAMPION, BOSS_COUNCIL);
    }

    bool HandleInfoAzshir(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_AZSHIR, BOSS_COUNCIL);
    }

    bool HandleState(ChatHandler* handler)
    {
        if (boss_fallen_champion_rework* champion = FindChampionAI(handler))
            handler->PSendSysMessage("Fallen Champion: {}", champion->TestState());
        if (boss_azshir_the_sleepless_rework* azshir = FindAzshirAI(handler))
            handler->PSendSysMessage("Azshir: {}", azshir->TestState());
        return true;
    }

    bool FireAzshir(ChatHandler* handler, uint32 id, char const* what)
    {
        boss_azshir_the_sleepless_rework* ai = FindAzshirAI(handler);
        return ai && Finish(handler, ai->TestFire(id), what);
    }

    bool HandleShock(ChatHandler* handler)
    {
        return FireAzshir(handler, boss_azshir_the_sleepless_rework::Q_SHOCK, "Holy Shock now (CV2)");
    }

    bool HandleExorcism(ChatHandler* handler)
    {
        return FireAzshir(handler, boss_azshir_the_sleepless_rework::Q_EXORCISM, "Exorcism now (CV5)");
    }

    bool HandleWrath(ChatHandler* handler)
    {
        return FireAzshir(handler, boss_azshir_the_sleepless_rework::Q_WRATH, "Holy Wrath now (CV4)");
    }

    bool HandleLight(ChatHandler* handler)
    {
        return FireAzshir(handler, boss_azshir_the_sleepless_rework::Q_LIGHT, "Holy Light now (CV3)");
    }

    bool HandleExecution(ChatHandler* handler)
    {
        return FireAzshir(handler, boss_azshir_the_sleepless_rework::Q_EXECUTION,
            "Execution Sentence now (CV8; heroic in the fight, any difficulty here)");
    }

    bool HandleSeal(ChatHandler* handler)
    {
        boss_fallen_champion_rework* ai = FindChampionAI(handler);
        return ai && Finish(handler, ai->TestSeal(), "the next seal now (CV6)");
    }

    bool HandleJudgement(ChatHandler* handler)
    {
        boss_fallen_champion_rework* ai = FindChampionAI(handler);
        return ai && Finish(handler, ai->TestJudgement(), "Judgement now with the seal's rider (CV6a)");
    }

    bool HandleShield(ChatHandler* handler)
    {
        boss_fallen_champion_rework* ai = FindChampionAI(handler);
        return ai && Finish(handler, ai->TestShield(), "Avenger's Shield now (CV7)");
    }

    bool HandleFall(ChatHandler* handler)
    {
        boss_fallen_champion_rework* ai = FindChampionAI(handler);
        return ai && Finish(handler, ai->TestFall(), "the Champion's fall now (CV1: Azshir channels 8 s)");
    }

    bool HandleGrief(ChatHandler* handler)
    {
        boss_fallen_champion_rework* ai = FindChampionAI(handler);
        return ai && Finish(handler, ai->TestGrief(), "one Grief stack now (CV1)");
    }

    ChatCommandTable const& CouncilTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "azshir",     HandleInfoAzshir,   SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,        SEC_GAMEMASTER, Console::No },
            { "shock",      HandleShock,        SEC_GAMEMASTER, Console::No },
            { "exorcism",   HandleExorcism,     SEC_GAMEMASTER, Console::No },
            { "wrath",      HandleWrath,        SEC_GAMEMASTER, Console::No },
            { "light",      HandleLight,        SEC_GAMEMASTER, Console::No },
            { "execution",  HandleExecution,    SEC_GAMEMASTER, Console::No },
            { "seal",       HandleSeal,         SEC_GAMEMASTER, Console::No },
            { "judgement",  HandleJudgement,    SEC_GAMEMASTER, Console::No },
            { "shield",     HandleShield,       SEC_GAMEMASTER, Console::No },
            { "fall",       HandleFall,         SEC_GAMEMASTER, Console::No },
            { "grief",      HandleGrief,        SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_azshir_fallen_champion_rework()
{
    RegisterDungeonReworkCreatureAI(boss_fallen_champion_rework, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(boss_azshir_the_sleepless_rework, ScarletMonasteryRework::kInstanceScriptName);
    RegisterSpellScript(spell_sm_council_holy_wrath_burn);
    RegisterSpellScript(spell_sm_council_execution_sentence);
    SmTest::RegisterBoss("council", CouncilTestCommands());
}
