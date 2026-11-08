/*
 * mod-dungeon-bosses, Scholomance S12: Ras Frostwhisper's hard mode, "the Torn Keepsake" (heroic only). WP-S12 owns
 * this file. Build spec: docs/dungeons/scholomance-rework.md SC 1087-1134 (Hard mode, tuning), SC 1207-1209 (RF9-RF11);
 * handoff section 3.5 row S12, section 3.6, section 10 (the user's page, book and alchemy table spots). Pure part:
 * RasHardModeLogic.h (tests/scholo_keepsake_test.cpp). Data: apps/dbc-tools source/npcs/scholomance/ras_hard_mode.py
 * (spells 206190-206197, the Ice Tomb 300535) and WP-S12's SQL rev (the gameobjects, their spawns, text group 3).
 *
 * The keepsake (instance data, instance_scholomance_rework.cpp; heroic only, spawnMask 2):
 *   go_sc_torn_page      301150 x3 at kKeepsakePages: a click collects that page (DATA_KEEPSAKE_PAGE); the page then
 *                        hides. Pages hide once Ras is dead.
 *   go_sc_keepsake_book  301151 (the empty book) and 301152 (the bound one), both spawned at kKeepsakeBook: one shows
 *                        at a time (GameObjectAI::CanBeSeen). A click on the empty book tells the count, and with all
 *                        three pages binds the keepsake (DATA_KEEPSAKE_BOUND).
 *   go_sc_alchemy_table  301154 at kHardModeTable (user ruling: the table, not the Embalming Fluid): selectable only
 *                        with the bound keepsake, while Ras neither fights nor is dead; a click lights the hard mode
 *                        (DATA_RAS_HARD_MODE) and Ras emotes (group 3, heard on the map). A wipe keeps it lit.
 *   The instance rides the hard mode loot bit (LOOT_MODE_HARD_MODE_1) on Ras while the flag is lit and he is alive;
 *   KeepsakeFight sets it again at the pull. Bots never click any of them (no DungeonEvent; handoff section 3.12).
 *
 * The fight (KeepsakeFight, a RasHardMode on S4's AI through RasFight.h; S4 makes one per heroic pull with the flag):
 *   health          the lich 400k at the pull (create health, restored on a wipe).
 *   RF3 HM tomb     a player at 20 Chill is held by S4's Entombed aura made permanent and an Ice Tomb 300535 (12k)
 *                   on them: a target-priority unit for the bots (BreakOut: the tank's and the healer's first). At
 *                   zero the tomb cracks (unselectable, a 1.5 s bar) while S4's 6 yd thaw circle warns on the player
 *                   (45%, Weakened, +3 Chill), then bursts and lets them go.
 *   RF9 transition  the lich's bar empties (a lethal guard): 3 s untargetable, the yell (group 0), healing to full
 *                   over the bar, then the human form (display 3975) on the same 400k. S4's fight clock stands still.
 *                   Tombs already standing stay. DATA_RAS_HUMAN is set so the stock quest head can drop.
 *   RF10 Siphon     10 s into phase 2, then every 30 s (waiting while he casts or a Frost Mark is live): a 2 s cast
 *                   bar and emote line 2, a registry Spread (8 yd) for the bots, then a 5 s channel. Each second:
 *                   warm players +3 Chill and he heals 1% of his bar each (at most 10% per Siphon); cold living
 *                   players +1 Chill and each backfires 1.3% of his bar on him; entombed players are neither. S4's
 *                   Chill beat stops for the channel; a due Frost Mark waits for the end.
 *   RF11 Decay      from phase 2's start, every player's Mortal Decay goes to one stack per whole 10 s (0.5% of the
 *                   heroic reference row per second per stack).
 *   cleanup         death, evade, reset: tombs gone, Decay and the drain off every player; on a wipe the display,
 *                   flags, health and DATA_RAS_HUMAN are restored.
 *
 * Every firing logs "scholo ras hm-<mechanic> ..." (the fight) or "scholo keepsake <mechanic> ..." (the gameobjects)
 * in module.dungeonbosses. `.dbtest scholo keepsake <sub>` drives it.
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RasFight.h"
#include "RasHardModeLogic.h"
#include "RasLogic.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <functional>
#include <memory>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoRasHardMode;
using BossMechanics::MechanicRef;
using ScholoRas::RasFight;
using ScholoRas::RasHardMode;

namespace
{
    char const* const kKeepsakeLog = "keepsake";
    uint32 constexpr kGoPollMs = 1000;
    // The broken tomb lets its player go a moment after the thaw circle resolves, so the circle (anchored on the
    // player, who is spared) never follows a freed player.
    uint32 constexpr kTombReleaseAfterMs = kTombCrackMs + 200;
    int8 constexpr kTombTargetPriority = 3;

    void LogKeepsake(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kKeepsakeLog, mechanic, detail);
    }

    // Create health is the base the engine rebuilds max health from (the Deadmines hard mode's SetBossHealth).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    // A center-screen line to every player in the instance (the keepsake is a group hunt).
    void NotifyMap(Map* map, std::string const& text)
    {
        if (!map)
            return;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
                if (WorldSession* session = player->GetSession())
                    ChatHandler(session).SendNotification(text);
    }

    void NotifyPlayer(Player* player, std::string const& text)
    {
        if (player && player->GetSession())
            ChatHandler(player->GetSession()).SendNotification(text);
    }

    // S4's AI as the hard mode sees it (RasFight.h), or nullptr.
    RasFight* FightOf(Creature* ras)
    {
        return ras && ras->IsAIEnabled ? dynamic_cast<RasFight*>(ras->AI()) : nullptr;
    }
}

// -------------------------------------------------------------------------------------------------------------------
// KeepsakeFight: the hard mode for one pull
// -------------------------------------------------------------------------------------------------------------------

class KeepsakeFight : public RasHardMode
{
public:
    void OnEngage(RasFight& fight) override
    {
        Creature* ras = fight.Ras();
        _baseCreateHealth = ras->GetCreateHealth();
        SetCreatureHealth(ras, kLichHealth);
        // The instance already rides the bit while the flag is lit (IN_PROGRESS re-applies it after BossAI's
        // ResetLootMode); set again here so the hard mode fight always carries it.
        DungeonKit::SetHardModeLoot(ras, true);
        _lethal.Arm();
        Mechanic::EditDescriptor(ras, [](BossMechanics::Descriptor& d)
        {
            // RF3 HM: break the tombs first, the tank's and the healer's before the others (BreakOut).
            d.targets.push_back(BossMechanics::TargetEntry(NPC_SC_ICE_TOMB, kTombTargetPriority,
                BossMechanics::Who::Dps).BreakOut());
        });
        fight.Log("hm-engage", Acore::StringFormat("health={} was_create={} loot_mode={}", ras->GetMaxHealth(),
            _baseCreateHealth, uint32(ras->GetLootMode())));
    }

    void OnUpdate(RasFight& fight, uint32 diff) override
    {
        Creature* ras = fight.Ras();
        UpdateTombs(fight, diff);

        bool const mayStart = !ras->HasUnitState(UNIT_STATE_CASTING) && !AnyFrostMark(fight);
        ClockStep const step = _clock.Advance(diff, mayStart);
        if (_clock.phase == Phase::Transition)
            ras->SetHealth(TransitionHealth(ras->GetMaxHealth(), _clock.transitionMs));
        if (step.transitionDone)
            BecomeHuman(fight);
        if (step.decayTo)
            Decay(fight, step.decayTo);
        if (step.siphonCast)
            SiphonCast(fight);
        if (step.channelStart)
            SiphonChannel(fight);
        for (uint32 i = 0; i < step.siphonTicks; ++i)
            SiphonTick(fight);
        if (step.siphonEnd)
            fight.Log("hm-siphon-end", Acore::StringFormat("healed={:.1f}% health={}", _healedPct, ras->GetHealth()));
    }

    void OnDamageTaken(RasFight& fight, Unit* /*attacker*/, uint32& damage) override
    {
        if (_clock.Mortal())
            return;
        _lethal.Intercept(fight.Ras(), damage, [this, &fight]() { StartTransition(fight); });
    }

    bool OnFreeze(RasFight& fight, Player* player) override
    {
        Creature* ras = fight.Ras();
        Creature* tomb = ras->SummonCreature(NPC_SC_ICE_TOMB, player->GetPosition(), TEMPSUMMON_MANUAL_DESPAWN);
        if (!tomb)
            return false;   // S4's 2 s tomb instead
        Aura* hold = ras->AddAura(ScholoRas::SPELL_RF_ENTOMBED, player);
        if (!hold)
        {
            tomb->DespawnOrUnsummon();
            return false;
        }
        hold->SetMaxDuration(-1);
        hold->SetDuration(-1);
        SetCreatureHealth(tomb, kTombHealth);
        tomb->SetReactState(REACT_PASSIVE);
        tomb->SetFacingTo(player->GetOrientation());
        if (tomb->IsAIEnabled)
            tomb->AI()->SetGUID(player->GetGUID(), 0);
        Mechanic::TrackUnit(ras, tomb);
        BossMechanics::Registry::GetOrCreate(ras->GetMap()).NoteHeld(ras->GetGUID(), tomb->GetGUID(),
            player->GetGUID(), 0);
        _tombs.push_back({ tomb->GetGUID(), player->GetGUID(), 0, false });
        fight.Log("hm-tomb", Acore::StringFormat("player={} tomb={} health={} phase={}", player->GetName(),
            tomb->GetGUID().ToString(), tomb->GetMaxHealth(), uint32(_clock.phase)));
        return true;
    }

    void OnEnd(RasFight& fight, bool died) override
    {
        Creature* ras = fight.Ras();
        for (Tomb const& t : _tombs)
            if (Creature* tomb = ras->GetMap()->GetCreature(t.tomb))
                tomb->DespawnOrUnsummon();
        _tombs.clear();

        InstanceScript* instance = ras->GetInstanceScript();
        if (instance)
            for (uint32 spell : { uint32(SPELL_RK_MORTAL_DECAY), uint32(SPELL_RK_SIPHONED) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);

        if (_untargetable)
        {
            ras->RemoveUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
            _untargetable = false;
        }
        if (!died)
        {
            if (ras->HasUnitState(UNIT_STATE_CASTING))
                ras->InterruptNonMeleeSpells(true);
            if (_morphed)
                ras->DeMorph();
            if (_baseCreateHealth)
                SetCreatureHealth(ras, _baseCreateHealth);
            if (_setHuman && instance)
                instance->SetData(DATA_RAS_HUMAN, _rasHumanBefore);
        }
        fight.Log("hm-end", Acore::StringFormat("died={} phase={} phase2={}ms siphons={} decay={}", died ? 1 : 0,
            uint32(_clock.phase), _clock.humanMs, _clock.siphons, _clock.decayStacks));
    }

    bool HoldsTimeline(RasFight const& /*fight*/) const override { return _clock.HoldsTimeline(); }
    bool HoldsFrostMark(RasFight const& /*fight*/) const override { return _clock.HoldsFrostMark(); }
    bool HoldsChillBeat(RasFight const& /*fight*/) const override { return _clock.HoldsChillBeat(); }

    // ---- `.dbtest scholo keepsake` ---------------------------------------------------------------------------------

    void TestTransition(RasFight& fight)
    {
        StartTransition(fight);
    }

    bool TestSiphon()
    {
        if (_clock.phase != Phase::Human || _clock.siphon != SiphonStage::Idle)
            return false;
        _clock.SiphonNow();
        return true;
    }

    bool TestDecay(RasFight& fight)
    {
        if (_clock.phase != Phase::Human)
            return false;
        ++_clock.decayStacks;
        Decay(fight, _clock.decayStacks);
        return true;
    }

    std::string TestState(RasFight& fight) const
    {
        Creature* ras = fight.Ras();
        return Acore::StringFormat("phase={} transition={}ms phase2={}ms siphon={} stage_ms={} next_siphon={}ms "
            "siphons={} healed={:.1f}% decay={} tombs={} health={}/{} guard={}", uint32(_clock.phase),
            _clock.transitionMs, _clock.humanMs, uint32(_clock.siphon), _clock.siphonMs, _clock.nextSiphonAt,
            _clock.siphons, _healedPct, _clock.decayStacks, _tombs.size(), ras->GetHealth(), ras->GetMaxHealth(),
            _lethal.Armed() ? 1 : 0);
    }

private:
    struct Tomb
    {
        ObjectGuid tomb;
        ObjectGuid player;
        uint32 crackMs = 0;
        bool cracking = false;
    };

    // ---- RF9 the transition ----------------------------------------------------------------------------------------

    void StartTransition(RasFight& fight)
    {
        if (!_clock.StartTransition())
            return;
        Creature* ras = fight.Ras();
        ras->InterruptNonMeleeSpells(false);
        ras->SetUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
        _untargetable = true;
        if (ras->IsAIEnabled)
            ras->AI()->Talk(YELL_RAS_THIS_CANNOT_BE);
        ras->CastSpell(ras, SPELL_RK_CLINGING_TO_LIFE, false);     // the 3 s bar (not triggered: it shows)
        fight.Log("hm-transition", Acore::StringFormat("health={} tombs={}", ras->GetHealth(), _tombs.size()));
    }

    void BecomeHuman(RasFight& fight)
    {
        Creature* ras = fight.Ras();
        if (Spell* bar = ras->GetCurrentSpell(CURRENT_GENERIC_SPELL))
            if (bar->GetSpellInfo()->Id == SPELL_RK_CLINGING_TO_LIFE)
                ras->InterruptSpell(CURRENT_GENERIC_SPELL, false);
        ras->SetDisplayId(kHumanDisplay);
        _morphed = true;
        ras->RemoveUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
        _untargetable = false;
        ras->SetHealth(ras->GetMaxHealth());
        _lethal.Disarm();       // the mortal can die
        // The stock quest head (13626) drops only in the human form (conditions: instance data 2 = 1).
        if (InstanceScript* instance = ras->GetInstanceScript())
        {
            _rasHumanBefore = instance->GetData(DATA_RAS_HUMAN);
            instance->SetData(DATA_RAS_HUMAN, 1);
            _setHuman = true;
        }
        fight.Log("hm-phase2", Acore::StringFormat("display={} health={} tombs={}", kHumanDisplay,
            ras->GetMaxHealth(), _tombs.size()));
    }

    // ---- RF11 Mortal Decay -----------------------------------------------------------------------------------------

    void Decay(RasFight& fight, uint32 stacks)
    {
        Creature* ras = fight.Ras();
        uint32 players = 0;
        for (Player* player : fight.FightPlayers())
        {
            uint32 const now = DungeonKit::Stacks(player, SPELL_RK_MORTAL_DECAY, ras->GetGUID());
            DungeonKit::AddStacks(player, SPELL_RK_MORTAL_DECAY, int32(stacks) - int32(now), ras, kDecayMaxStacks);
            ++players;
        }
        fight.Log("hm-decay", Acore::StringFormat("stacks={} players={} pct_per_s={:.1f}", stacks, players,
            float(stacks) * kDecayPctPerStack));
    }

    // ---- RF10 Siphon Warmth ----------------------------------------------------------------------------------------

    bool AnyFrostMark(RasFight& fight) const
    {
        for (Player* player : fight.FightPlayers())
            if (player->HasAura(ScholoRas::SPELL_RF_FROST_MARK))
                return true;
        return false;
    }

    void SiphonCast(RasFight& fight)
    {
        Creature* ras = fight.Ras();
        DungeonKit::CastBar(ras, SPELL_RK_SIPHON_CAST, nullptr, EMOTE_RAS_SIPHON_WARMTH);
        // Bots: spread 8 yd (go cold) for the bar and the channel. No damage of its own (no ledger entry): the Siphon
        // is the cost. A ring outline per player, no fill (a range cue, not a hit).
        MechanicRef ref = Mechanic::Spread(ras, kSiphonSpreadRadius, Milliseconds(kSiphonCastMs + kSiphonChannelMs));
        ref.NoFillTimer().Tag(TAG_SIPHON);
        fight.Track(ref.Handle());
        _healedPct = 0.f;
        fight.Log("hm-siphon", Acore::StringFormat("n={} phase2={}ms", _clock.siphons, _clock.humanMs));
    }

    void SiphonChannel(RasFight& fight)
    {
        Creature* ras = fight.Ras();
        if (Spell* bar = ras->GetCurrentSpell(CURRENT_GENERIC_SPELL))
            if (bar->GetSpellInfo()->Id == SPELL_RK_SIPHON_CAST)
                ras->InterruptSpell(CURRENT_GENERIC_SPELL, false);
        ras->CastSpell(ras, SPELL_RK_SIPHON_CHANNEL, false);
    }

    void SiphonTick(RasFight& fight)
    {
        Creature* ras = fight.Ras();
        std::vector<Player*> warm;
        std::vector<ObjectGuid> cold;
        for (Player* player : fight.FightPlayers())
        {
            if (fight.IsEntombed(player))
                continue;       // tombs never count as cold (nor warm)
            if (fight.IsWarm(player))
                warm.push_back(player);
            else
                cold.push_back(player->GetGUID());
        }

        float const healPct = SiphonHealPct(uint32(warm.size()), _healedPct);
        _healedPct += healPct;
        uint32 const heal = PctOf(ras->GetMaxHealth(), healPct);
        if (heal)
            ras->CastCustomSpell(SPELL_RK_SIPHON_HEAL, SPELLVALUE_BASE_POINT0, int32(heal), ras, true);
        for (Player* player : warm)
        {
            ras->CastSpell(player, SPELL_RK_SIPHONED, true);
            fight.AddChill(player, int32(kSiphonWarmChill), "siphon-warm");
        }

        uint32 const backfire = PctOf(ras->GetMaxHealth(), SiphonBackfirePct());
        for (ObjectGuid const& guid : cold)
        {
            if (Player* player = ObjectAccessor::GetPlayer(*ras, guid))
                fight.AddChill(player, int32(kSiphonColdChill), "siphon-cold");
            QueueBackfire(ras, guid, backfire);
        }
        fight.Log("hm-siphon-tick", Acore::StringFormat("warm={} cold={} heal={} backfire={}x{} health={}",
            warm.size(), cold.size(), heal, backfire, cold.size(), ras->GetHealth()));
    }

    // The backfire may kill him, and his death ends (and frees) this object: it lands from his event list on his next
    // update, never inside this object's own call.
    static void QueueBackfire(Creature* ras, ObjectGuid player, uint32 amount)
    {
        if (!amount)
            return;
        ras->m_Events.AddEventAtOffset([ras, player, amount]()
        {
            if (!ras->IsAlive() || !ras->IsInCombat())
                return;
            Player* caster = ObjectAccessor::GetPlayer(*ras, player);
            if (!caster || !caster->IsAlive() || !caster->IsInWorld())
                return;
            caster->CastCustomSpell(SPELL_RK_SIPHON_BACKFIRE, SPELLVALUE_BASE_POINT0, int32(amount), ras, true);
        }, 0ms);
    }

    // ---- RF3 HM the tombs ------------------------------------------------------------------------------------------

    void UpdateTombs(RasFight& fight, uint32 diff)
    {
        Creature* ras = fight.Ras();
        Map* map = ras->GetMap();
        for (auto it = _tombs.begin(); it != _tombs.end();)
        {
            Creature* tomb = map->GetCreature(it->tomb);
            Player* player = ObjectAccessor::GetPlayer(*ras, it->player);
            if (!player || !player->IsAlive() || !player->IsInWorld() || !fight.IsEntombed(player))
            {
                // Dead, gone, or freed some other way: the tomb has nobody to hold.
                if (tomb)
                    tomb->DespawnOrUnsummon();
                fight.Log("hm-tomb-empty", Acore::StringFormat("player={}", it->player.ToString()));
                it = _tombs.erase(it);
                continue;
            }
            if (!tomb || !tomb->IsAlive())
            {
                // Killed past the crack (an instant kill) or despawned: free them now, the burst at once.
                fight.Thaw(player, true);
                if (tomb)
                    tomb->DespawnOrUnsummon();
                fight.Log("hm-tomb-lost", Acore::StringFormat("player={}", player->GetName()));
                it = _tombs.erase(it);
                continue;
            }
            if (!it->cracking && tomb->IsAIEnabled && tomb->AI()->GetData(kTombDataCracked))
            {
                it->cracking = true;
                it->crackMs = 0;
                bool const heroic = fight.Heroic();
                MechanicRef ref = Mechanic::Circle(ras, player, ScholoRas::kThawRadius, Milliseconds(kTombCrackMs));
                ref.Damage(ScholoRas::kThawPct(heroic)).Weakened().Spell(ScholoRas::SPELL_RF_THAW)
                    .Tag(ScholoRas::TAG_THAW);
                if (uint32 const chill = ScholoRas::kThawChill(heroic))
                    ref.OnHit(ChillOnHit(ras, chill));
                fight.Track(ref.Handle());
                fight.Log("hm-tomb-crack", Acore::StringFormat("player={}", player->GetName()));
            }
            if (it->cracking)
            {
                it->crackMs += diff;
                if (it->crackMs >= kTombReleaseAfterMs)
                {
                    fight.Thaw(player, false);      // the circle above is the burst
                    tomb->DespawnOrUnsummon();
                    fight.Log("hm-tomb-break", Acore::StringFormat("player={}", player->GetName()));
                    it = _tombs.erase(it);
                    continue;
                }
            }
            ++it;
        }
    }

    // +`stacks` Chill on each player the thaw hits (captures the map and guid only, never a Unit*).
    static std::function<void(Unit*)> ChillOnHit(Creature* ras, uint32 stacks)
    {
        Map* map = ras->GetMap();
        ObjectGuid const guid = ras->GetGUID();
        return [map, guid, stacks](Unit* hit)
        {
            Player* player = hit ? hit->ToPlayer() : nullptr;
            Creature* boss = map ? map->GetCreature(guid) : nullptr;
            if (!player || !boss || !boss->IsAlive())
                return;
            if (RasFight* fight = FightOf(boss))
                fight->AddChill(player, int32(stacks), "thaw");
        };
    }

    KeepsakeClock _clock;
    DungeonKit::LethalGuard _lethal;
    std::vector<Tomb> _tombs;
    float _healedPct = 0.f;
    uint32 _baseCreateHealth = 0;
    uint32 _rasHumanBefore = 0;
    bool _untargetable = false;
    bool _morphed = false;
    bool _setHuman = false;
};

// -------------------------------------------------------------------------------------------------------------------
// Ice Tomb 300535 (npc_sc_ice_tomb): a rooted, passive 12k target holding a frozen player; at zero it cracks
// -------------------------------------------------------------------------------------------------------------------

struct npc_sc_ice_tomb : public ScriptedAI
{
    explicit npc_sc_ice_tomb(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    // It never walks home or heals: the hard mode despawns it.
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (_cracked)
        {
            damage = 0;
            return;
        }
        if (damage < me->GetHealth())
            return;
        damage = me->GetHealth() > 1 ? me->GetHealth() - 1 : 0;
        _cracked = true;
        me->SetUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
        me->CastSpell(me, SPELL_RK_THAWING, false);     // the 1.5 s bar; the hard mode lands the thaw
    }

    uint32 GetData(uint32 id) const override
    {
        return id == kTombDataCracked && _cracked ? 1 : 0;
    }

    void SetGUID(ObjectGuid const& guid, int32 /*id*/) override
    {
        _held = guid;
    }

    ObjectGuid GetGUID(int32 /*id*/) const override
    {
        return _held;
    }

private:
    ObjectGuid _held;
    bool _cracked = false;
};

// -------------------------------------------------------------------------------------------------------------------
// RF11 Mortal Decay 206196: each stack deals 0.5% of the reference row a second (the engine multiplies by the stacks)
// -------------------------------------------------------------------------------------------------------------------

class spell_sc_ras_mortal_decay : public AuraScript
{
    PrepareAuraScript(spell_sc_ras_mortal_decay);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        amount = static_cast<int32>(DungeonKit::RefFlatOn(GetCaster(), GetUnitOwner(), kDecayPctPerStack));
        canBeRecalculated = true;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sc_ras_mortal_decay::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// -------------------------------------------------------------------------------------------------------------------
// The keepsake gameobjects (heroic spawns only). Each one reads the instance data live (CanBeSeen) and polls once a
// second to refresh its visibility and selectability when the data changes.
// -------------------------------------------------------------------------------------------------------------------

struct KeepsakeGameObjectAI : public GameObjectAI
{
    explicit KeepsakeGameObjectAI(GameObject* go) : GameObjectAI(go) { }

    bool CanBeSeen(Player const* /*seer*/) override
    {
        return Shown();
    }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kGoPollMs;
        Sync();
    }

protected:
    virtual bool Shown() = 0;
    virtual bool Selectable() { return Shown(); }

    InstanceScript* Instance() const
    {
        return me->GetInstanceScript();
    }

    uint32 RasState() const
    {
        InstanceScript* instance = Instance();
        return instance ? uint32(instance->GetBossState(BOSS_RAS)) : uint32(DungeonKit::State::NotStarted);
    }

    // Visibility and the not-selectable flag follow the data.
    void Sync()
    {
        bool const shown = Shown();
        bool const selectable = shown && Selectable();
        bool const flagged = me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (selectable && flagged)
            me->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else if (!selectable && !flagged)
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (!_synced || shown != _lastShown)
        {
            _synced = true;
            _lastShown = shown;
            me->UpdateObjectVisibility(true);
        }
    }

private:
    uint32 _pollMs = 0;
    bool _synced = false;
    bool _lastShown = false;
};

// Torn page 301150 (go_sc_torn_page), three spawns at kKeepsakePages: the spawn's spot names its page.
struct go_sc_torn_page : public KeepsakeGameObjectAI
{
    explicit go_sc_torn_page(GameObject* go) : KeepsakeGameObjectAI(go) { }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        InstanceScript* instance = Instance();
        std::size_t const page = Page();
        if (!instance || !Shown())
            return true;
        instance->SetData(DATA_KEEPSAKE_PAGE, uint32(page));
        if (!(instance->GetData(DATA_KEEPSAKE_PAGE) & (1u << page)))
        {
            LogKeepsake("page-refused", Acore::StringFormat("page={} by={}", page + 1, player->GetName()));
            return true;
        }
        uint32 const found = instance->GetData(DATA_KEEPSAKE_PAGE_COUNT);
        NotifyMap(me->GetMap(), Acore::StringFormat("A torn page of Frostwhisper's keepsake ({} of {}).", found,
            kKeepsakePageCount));
        LogKeepsake("page", Acore::StringFormat("page={} by={} found={}/{}", page + 1, player->GetName(), found,
            kKeepsakePageCount));
        Sync();
        return true;
    }

protected:
    bool Shown() override
    {
        InstanceScript* instance = Instance();
        return instance && PageShows(DungeonKit::IsHeroicMap(me), instance->GetData(DATA_KEEPSAKE_PAGE), Page(),
            RasState());
    }

private:
    std::size_t Page() const
    {
        return PageAt(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ());
    }
};

// The keepsake book (go_sc_keepsake_book): 301151 empty and 301152 bound, both spawned at kKeepsakeBook; one shows.
struct go_sc_keepsake_book : public KeepsakeGameObjectAI
{
    explicit go_sc_keepsake_book(GameObject* go) : KeepsakeGameObjectAI(go) { }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        InstanceScript* instance = Instance();
        if (!instance || !Shown())
            return true;
        if (BoundBook())
        {
            NotifyPlayer(player, instance->GetData(DATA_RAS_HARD_MODE)
                ? "The keepsake calls to Ras Frostwhisper."
                : "Frostwhisper's keepsake is whole again. The alchemy apparatus down the hall awaits it.");
            return true;
        }
        uint32 const found = instance->GetData(DATA_KEEPSAKE_PAGE_COUNT);
        if (found < kKeepsakePageCount)
        {
            NotifyPlayer(player, Acore::StringFormat("Frostwhisper's keepsake: every page is torn out. Pages found: "
                "{} of {}.", found, kKeepsakePageCount));
            return true;
        }
        instance->SetData(DATA_KEEPSAKE_BOUND, 1);
        if (!instance->GetData(DATA_KEEPSAKE_BOUND))
        {
            LogKeepsake("bind-refused", Acore::StringFormat("by={} ras_state={}", player->GetName(), RasState()));
            return true;
        }
        NotifyMap(me->GetMap(), "The torn pages bind into Frostwhisper's keepsake.");
        LogKeepsake("bind", Acore::StringFormat("by={}", player->GetName()));
        Sync();
        if (GameObject* other = me->FindNearestGameObject(GO_SC_KEEPSAKE_BOOK_BOUND, 5.f))
            other->UpdateObjectVisibility(true);
        return true;
    }

protected:
    bool Shown() override
    {
        InstanceScript* instance = Instance();
        return instance && DungeonKit::IsHeroicMap(me)
            && BookShows(BoundBook(), instance->GetData(DATA_KEEPSAKE_BOUND) != 0);
    }

private:
    bool BoundBook() const
    {
        return me->GetEntry() == GO_SC_KEEPSAKE_BOOK_BOUND;
    }
};

// The alchemy table 301154 (go_sc_alchemy_table) at kHardModeTable: lights "the Torn Keepsake".
struct go_sc_alchemy_table : public KeepsakeGameObjectAI
{
    explicit go_sc_alchemy_table(GameObject* go) : KeepsakeGameObjectAI(go) { }

    void UpdateAI(uint32 diff) override
    {
        KeepsakeGameObjectAI::UpdateAI(diff);
        InstanceScript* instance = Instance();
        GOState const want = instance && instance->GetData(DATA_RAS_HARD_MODE) ? GO_STATE_ACTIVE : GO_STATE_READY;
        if (me->GetGoState() != want)
            me->SetGoState(want);
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        InstanceScript* instance = Instance();
        if (!instance)
            return true;
        TableRefusal const why = Check();
        if (why != TableRefusal::None)
        {
            NotifyPlayer(player, TableRefusalText(why));
            LogKeepsake("table-refused", Acore::StringFormat("by={} reason={}", player->GetName(), uint32(why)));
            return true;
        }
        instance->SetData(DATA_RAS_HARD_MODE, 1);
        if (!instance->GetData(DATA_RAS_HARD_MODE))
        {
            LogKeepsake("table-refused", Acore::StringFormat("by={} reason=instance", player->GetName()));
            return true;
        }
        if (Creature* ras = instance->GetCreature(DATA_RAS_GUID))
            if (ras->IsAlive() && ras->IsAIEnabled)
                ras->AI()->Talk(EMOTE_RAS_KEEPSAKE_LIT);
        me->SetGoState(GO_STATE_ACTIVE);
        LogKeepsake("hardmode-lit", Acore::StringFormat("by={}", player->GetName()));
        Sync();
        return true;
    }

protected:
    // Always there on heroic; selectable only when a click would light the hard mode.
    bool Shown() override
    {
        return DungeonKit::IsHeroicMap(me);
    }

    bool Selectable() override
    {
        return Check() == TableRefusal::None;
    }

private:
    TableRefusal Check() const
    {
        InstanceScript* instance = Instance();
        if (!instance)
            return TableRefusal::NotHeroic;
        return TableCheck(DungeonKit::IsHeroicMap(me), instance->GetData(DATA_KEEPSAKE_BOUND) != 0,
            instance->GetData(DATA_RAS_HARD_MODE) != 0, RasState());
    }
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest scholo keepsake <sub>`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    // The pull's KeepsakeFight on Ras (the selected one, else the nearest), with his RasFight; errors otherwise.
    KeepsakeFight* FindKeepsake(ChatHandler* handler, RasFight** fightOut)
    {
        Creature* ras = ScholoTest::FindBoss(handler, NPC_RAS);
        if (!ras)
            return nullptr;
        RasFight* fight = FightOf(ras);
        if (!fight)
        {
            handler->SendErrorMessage("{}", "Ras is not running boss_ras_frostwhisper_rework (check the ScriptName).");
            return nullptr;
        }
        auto* keepsake = dynamic_cast<KeepsakeFight*>(fight->ActiveHardMode());
        if (!keepsake)
        {
            handler->SendErrorMessage("{}", "No hard mode fight: light it (`.dbtest scholo keepsake light`, heroic) "
                "and pull Ras.");
            return nullptr;
        }
        *fightOut = fight;
        return keepsake;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            return false;
        handler->PSendSysMessage("The Torn Keepsake: pages {}/{} (mask {}), bound {}, hard mode {}, killed {}",
            instance->GetData(DATA_KEEPSAKE_PAGE_COUNT), kKeepsakePageCount, instance->GetData(DATA_KEEPSAKE_PAGE),
            instance->GetData(DATA_KEEPSAKE_BOUND), instance->GetData(DATA_RAS_HARD_MODE),
            instance->GetData(DATA_RAS_HARD_MODE_KILLED));
        if (Creature* ras = instance->GetCreature(DATA_RAS_GUID))
        {
            handler->PSendSysMessage("Ras: health {}/{}, loot mode {}, display {}", ras->GetHealth(),
                ras->GetMaxHealth(), uint32(ras->GetLootMode()), ras->GetDisplayId());
            if (RasFight* fight = FightOf(ras))
                if (auto* keepsake = dynamic_cast<KeepsakeFight*>(fight->ActiveHardMode()))
                    handler->PSendSysMessage("Fight: {}", keepsake->TestState(*fight));
        }
        return true;
    }

    // `light`: the three pages, the bind and the flag in one go (heroic, Ras alive and not fighting).
    bool HandleLight(ChatHandler* handler)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            return false;
        for (uint32 page = 0; page < kKeepsakePageCount; ++page)
            instance->SetData(DATA_KEEPSAKE_PAGE, page);
        instance->SetData(DATA_KEEPSAKE_BOUND, 1);
        instance->SetData(DATA_RAS_HARD_MODE, 1);
        handler->PSendSysMessage("Pages {}/{}, bound {}, hard mode {} (heroic only, Ras alive and not fighting).",
            instance->GetData(DATA_KEEPSAKE_PAGE_COUNT), kKeepsakePageCount, instance->GetData(DATA_KEEPSAKE_BOUND),
            instance->GetData(DATA_RAS_HARD_MODE));
        return true;
    }

    // `transition`: the lich's bar empties now (RF9).
    bool HandleTransition(ChatHandler* handler)
    {
        RasFight* fight = nullptr;
        KeepsakeFight* keepsake = FindKeepsake(handler, &fight);
        if (!keepsake)
            return false;
        keepsake->TestTransition(*fight);
        handler->PSendSysMessage("{}", "Ras: the transition (RF9; phase 2 in 3 s).");
        return true;
    }

    // `siphon`: Siphon Warmth now (RF10; phase 2, not during a Siphon; it still waits for a cast or a Frost Mark).
    bool HandleSiphon(ChatHandler* handler)
    {
        RasFight* fight = nullptr;
        KeepsakeFight* keepsake = FindKeepsake(handler, &fight);
        if (!keepsake)
            return false;
        if (!keepsake->TestSiphon())
        {
            handler->SendErrorMessage("{}", "Not in phase 2, or a Siphon is running.");
            return false;
        }
        handler->PSendSysMessage("{}", "Ras: Siphon Warmth is due (RF10).");
        return true;
    }

    // `decay`: one more Mortal Decay stack on everyone (RF11; phase 2).
    bool HandleDecay(ChatHandler* handler)
    {
        RasFight* fight = nullptr;
        KeepsakeFight* keepsake = FindKeepsake(handler, &fight);
        if (!keepsake)
            return false;
        if (!keepsake->TestDecay(*fight))
        {
            handler->SendErrorMessage("{}", "Not in phase 2.");
            return false;
        }
        handler->PSendSysMessage("{}", "Ras: Mortal Decay +1 stack (RF11).");
        return true;
    }

    // `tomb`: freezes the selected player (or you) into a permanent tomb (RF3 HM; `.gm off`, in the fight).
    bool HandleTomb(ChatHandler* handler)
    {
        RasFight* fight = nullptr;
        if (!FindKeepsake(handler, &fight))
            return false;
        Player* target = handler->getSelectedPlayerOrSelf();
        if (!target)
            return false;
        fight->AddChill(target, int32(ScholoRas::kChillMax), "test");
        handler->PSendSysMessage("Ras: {} frozen: {}", target->GetName(), fight->IsEntombed(target) ? "entombed" :
            "NOT entombed (dead, already entombed or not in the fight?)");
        return true;
    }

    ChatCommandTable const& KeepsakeTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "light",      HandleLight,      SEC_GAMEMASTER, Console::No },
            { "transition", HandleTransition, SEC_GAMEMASTER, Console::No },
            { "siphon",     HandleSiphon,     SEC_GAMEMASTER, Console::No },
            { "decay",      HandleDecay,      SEC_GAMEMASTER, Console::No },
            { "tomb",       HandleTomb,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_scholo_ras_hard_mode()
{
    ScholoRas::RegisterRasHardMode([](Creature* /*ras*/) { return std::make_unique<KeepsakeFight>(); });
    RegisterDungeonReworkCreatureAI(npc_sc_ice_tomb, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_sc_torn_page, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_sc_keepsake_book, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_sc_alchemy_table, ScholomanceRework::kInstanceScriptName);
    RegisterSpellScript(spell_sc_ras_mortal_decay);
    ScholoTest::RegisterBoss("keepsake", KeepsakeTestCommands());
}
