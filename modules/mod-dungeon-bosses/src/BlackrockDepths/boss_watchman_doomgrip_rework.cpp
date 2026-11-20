/*
 * mod-dungeon-bosses, Blackrock Depths D9: the Vault, "Security Breach": Watchman Doomgrip (9476), the four Vault
 * Sentinels (300793, the event's Warbringer Constructs re-entered) and the Secret Safe (161495). Build spec SP 640-687
 * (docs/dungeons/blackrock-depths-2-shadowforge-city.md "The Vault", rulings 42-45 and 88), handoff section 3.4 row
 * D9, section 3.5 row D9, section 3.7 "The Vault", section 7 #17. Replaces Doomgrip's SmartAI (the rows are dropped by
 * the S0 SQL rev); the creature templates are bound by apps/dbc-tools source/npcs/blackrock_depths/vault.py, the
 * re-entered spawns, the texts and the Safe's script by rev_vault_blackrock_depths.sql. Pure rules: VaultLogic.h.
 *
 * The INSTANCE owns the event's state (slot BOSS_VAULT = TYPE_VAULT): the Dark Coffer's gossip starts it once
 * Stilgiss and Verek are DONE (IN_PROGRESS: it summons Doomgrip and wakes the constructs, stock), all warders dead
 * makes it DONE (the Secret Door opens, the Safe unlocks), a wipe (DATA_VAULT_RESET, or its idle watch) re-stones
 * them and despawns him; the opened coffer's gossip starts it again (the Dark Keeper Key is not used up by opening
 * the coffer: the instance takes one when the Vault completes, HANDOFF section 10; nothing here touches the key).
 * Three scripts here play the fight on top:
 *
 *   go_brd_vault_secret_safe  the event's clock, on the Secret Safe (it never dies, so the clock outlives Doomgrip):
 *                  VA1 the lockdown (a force field at the doorway; nobody may stand in the corridor past it while
 *                  the event runs: put back in the room), VA2 the wakes (5 s, then every 20 s, heroic 15 s, in a
 *                  random order; at once when nothing awake is left), VA8 the seals (75, 90, 110 s, Doomgrip's
 *                  emotes, said from his corpse too) and at the end the finishing time (DATA_VAULT_CLOCK, saved).
 *                  It also fills the Safe when it is opened (brd_vault_safe_loot below)
 *   npc_brd_vault_sentinel  stone until its turn (the instance wakes all four at the alarm: it turns itself back), then
 *                  awake: passive (it never attacks or moves: rooted, fear-immune, put back on its post after a grip
 *                  or a knockback, R-1-B B1), in combat with the room, VA3 its security field (a
 *                  persistent registry Zone on itself, 5% / 8% a second, the tank too; heroic +1 yd every 10 s to
 *                  9 yd) with its disc on a stalker, and VA4 its beam to Doomgrip
 *   boss_watchman_doomgrip_rework  the tank's: VA4 Security Link (-25% damage taken per awake sentinel, 75% at most),
 *                  VA5 Intruder Sweep (8 s, then every 15 s, heroic 12 s: a 2 s bar and a 90 degree, 10 yd cone
 *                  locked where he faces at its start, 25% / 40% + Weakened, the tank included), VA6 Sunder Armor (the
 *                  stock beat, -5% armor a stack, 5 stacks), VA7 Watchman's Draught at 60% and 30% (heals 5%, +20%
 *                  damage for 15 s, Magic: the purge list). Kill order: sentinels, then him (the descriptor)
 *   brd_vault_safe_loot  the Safe's loot (section 7 #17): the Cinder of the Firelord always, one gear item of
 *                  Doomgrip's list never his (he reports his at his death), the Vault Treasure Bags the clock left
 *                  (70620 normal, 70623 heroic), added to whatever the Safe's own table rolled after anything of
 *                  those it rolled is taken out; the engine then rolls them for the group (the chest's groupLootRules)
 *
 * Every firing logs one INFO line "brd doomgrip <mechanic> ..." or "brd vault <mechanic> ..." (module.dungeonbosses).
 * No lambda is kept by the registry. The looks on stalkers (the force field, the field discs) use the shared stalker
 * NPC_BRD_STALKER and are only looks: the fight plays without them while the stalker is not declared.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureTextMgr.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "LootMgr.h"
#include "Map.h"
#include "MiscScript.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "VaultLogic.h"
#include <algorithm>
#include <cmath>
#include <list>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdVault;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossKey = "doomgrip";
    char const* const kVaultKey = "vault";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    void LogVault(char const* key, char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, key, mechanic, detail);
    }

    // The room's floor for the bots' planned spots: inside the rim's smallest radius.
    BossMechanics::SpotBounds RoomBounds()
    {
        BossMechanics::SpotBounds bounds;
        bounds.Circle(Position(kVaultCenter.x, kVaultCenter.y, -50.f, 0.f), kRoomBoundsYd, kRoomZMin, kRoomZMax);
        return bounds;
    }

    uint32 VaultState(WorldObject const* o)
    {
        InstanceScript* instance = o ? o->GetInstanceScript() : nullptr;
        return instance ? uint32(instance->GetBossState(BOSS_VAULT)) : uint32(NOT_STARTED);
    }

    // A sentinel's dormant state (R-2-A MA-2): not selectable, set by the instance's freeze and by Dormant, cleared
    // only by Wake. Never the Stoned aura, which is look only.
    bool IsStone(Unit const* u)
    {
        return u && u->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
    }

    // Doomgrip, alive or a corpse, while he is on the map (the instance keeps his guid until he leaves it).
    Creature* DoomgripOf(WorldObject const* o)
    {
        InstanceScript* instance = o ? o->GetInstanceScript() : nullptr;
        if (!instance || !o->FindMap())
            return nullptr;
        ObjectGuid const guid = instance->GetGuidData(kGuidDoomgrip);
        return guid ? o->FindMap()->GetCreature(guid) : nullptr;
    }

    // One of Doomgrip's lines from wherever he is (alive or a corpse): the clock's emotes outlive him.
    void DoomgripSays(WorldObject const* o, uint8 group)
    {
        if (Creature* doomgrip = DoomgripOf(o))
            if (doomgrip->IsInWorld())
                sCreatureTextMgr->SendChat(doomgrip, group);
    }

    GameObject* SecretSafeOf(WorldObject const* o)
    {
        InstanceScript* instance = o ? o->GetInstanceScript() : nullptr;
        if (!instance || !o->FindMap())
            return nullptr;
        ObjectGuid const guid = instance->GetGuidData(GO_SECRET_SAFE);
        return guid ? o->FindMap()->GetGameObject(guid) : nullptr;
    }

    // The four event sentinels, alive or dead (the Black Vault's other constructs are trash of another entry). By
    // entry alone (R-1-B B1 / m1): a sentinel moved off its post still counts for the link and the wake order.
    std::vector<Creature*> SentinelsNear(WorldObject const* o)
    {
        std::list<Creature*> found;
        o->GetCreatureListWithEntryInGrid(found, NPC_BRD_VAULT_SENTINEL, kSentinelSearchYd);
        std::vector<Creature*> out(found.begin(), found.end());
        std::sort(out.begin(), out.end(), [](Creature const* a, Creature const* b)
        {
            return a->GetGUID() < b->GetGUID();
        });
        return out;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The Vault Sentinels (300793)
// ---------------------------------------------------------------------------------------------------------------------

struct npc_brd_vault_sentinel : public ScriptedAI
{
    explicit npc_brd_vault_sentinel(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        ScriptedAI::Reset();
        Cleanup("reset");
        me->SetReactState(REACT_PASSIVE);
        me->SetCombatMovement(false);
        me->SetControlled(true, UNIT_STATE_ROOT);   // it never moves (R-1-B B1; ReturnToPost undoes a grip)
    }

    // Never by sight, never at anyone: the field is its whole kit.
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void AttackStart(Unit* /*who*/) override { }

    void DoAction(int32 action) override
    {
        if (action == ACTION_SENTINEL_WAKE)
            Wake();
        else if (action == ACTION_SENTINEL_DORMANT)
            Dormant("controller");
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        bool const wasAwake = _awake;
        Cleanup("evade");
        ScriptedAI::EnterEvadeMode(why);
        // Nobody left to fight it: a wipe ends the attempt (the instance re-stones the four, Doomgrip goes).
        if (wasAwake && VaultState(me) == IN_PROGRESS)
            if (InstanceScript* instance = me->GetInstanceScript())
                instance->SetData(DATA_VAULT_RESET, 1);
    }

    void JustDied(Unit* killer) override
    {
        ScriptedAI::JustDied(killer);
        LogVault(kVaultKey, "sentinel-death", Acore::StringFormat("guid={} lived={}s radius={:.0f} killer={}",
            me->GetSpawnId(), _aliveMs / 1000, _radius, killer ? killer->GetName() : "none"));
        Cleanup("death");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!_awake)
        {
            // The instance wakes every construct when the alarm trips (stock); a sentinel stays stone until the
            // clock's turn comes.
            if (SentinelNeedsStone(VaultState(me) == IN_PROGRESS, IsStone(me), me->IsInEvadeMode()))
                Dormant("alarm");
            return;
        }
        if (SentinelReStoned(_awake, IsStone(me)))
        {
            Cleanup("re-stoned");   // the instance froze it back (a reset)
            return;
        }
        if (me->IsEngaged() && !UpdateVictim())
            return;                 // passive: in combat with the room, or evading with nobody left
        _aliveMs += diff;
        ReturnToPost(diff);
        UpdateField();
        UpdateBeam(diff);
    }

    bool Awake() const { return _awake; }
    float Radius() const { return _radius; }
    uint64 AliveMs() const { return _aliveMs; }

private:
    // VA2: the controller's turn. It wakes where it stood (the posts are the construct spots, handoff section 3.8).
    void Wake()
    {
        if (_awake || !me->IsAlive())
            return;
        _awake = true;
        _aliveMs = 0;
        _beamCheckMs = 0;
        _heroic = IsHeroicMap(me);
        me->RemoveAurasDueToSpell(SPELL_VA_STONED);
        me->SetImmuneToPC(false);
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetReactState(REACT_PASSIVE);
        me->CastSpell(me, SPELL_VA_SENTINEL_WAKES, true);
        DoZoneInCombat(me, kAlarmZoneYd);
        if (Creature* look = me->SummonCreature(NPC_BRD_STALKER, me->GetPosition(), TEMPSUMMON_MANUAL_DESPAWN))
        {
            look->SetReactState(REACT_PASSIVE);
            _look = look->GetGUID();
        }
        SetField(FieldRadius(_heroic, 0), kFieldWarnMs);
        Beam();
        LogVault(kVaultKey, "sentinel-awake", Acore::StringFormat("guid={} heroic={} radius={:.0f} pct={:.0f}/s "
            "combat={} look={}", me->GetSpawnId(), _heroic ? 1 : 0, _radius, kFieldPct(_heroic),
            me->IsInCombat() ? 1 : 0, _look ? 1 : 0));
    }

    // Back to stone (the instance's dormant state, FreezeVaultConstruct): not selectable, immune, passive. The state is
    // the flag (IsStone); the Stoned copy is its look only (R-2-A MA-2).
    void Dormant(char const* why)
    {
        bool const changed = _awake || !IsStone(me);
        Cleanup(why);
        if (me->IsInCombat())
        {
            me->CombatStop(true);
            me->GetThreatMgr().ClearAllThreat();
        }
        if (!me->HasAura(SPELL_VA_STONED))
            me->CastSpell(me, SPELL_VA_STONED, true);
        me->SetImmuneToPC(true);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetReactState(REACT_PASSIVE);
        if (changed)
            LogVault(kVaultKey, "sentinel-dormant", Acore::StringFormat("guid={} why={}", me->GetSpawnId(), why));
    }

    // VA3: the field, a persistent registry Zone on itself (the tank too, ruling 88), and its disc on the stalker.
    void SetField(float radius, uint32 warnMs)
    {
        float const pct = kFieldPct(_heroic);
        BossMechanics::ZoneSpec const shape = kFieldHoleYd > 0.f
            ? BossMechanics::Shapes::Donut(me, kFieldHoleYd, radius) : BossMechanics::Shapes::Circle(me, radius);
        MechanicRef ref = Mechanic::Zone(me, shape, Ms(warnMs));
        ref.Persistent(Ms(kFieldLifeMs), Ms(kFieldTickMs)).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_ARCANE)
            .Spell(SPELL_VA_FIELD_HIT).Within(RoomBounds()).Tag(TAG_VA_FIELD);
        _field = ref.Handle();
        _radius = radius;
        if (Creature* look = ObjectAccessor::GetCreature(*me, _look))
        {
            for (uint32 rung : { SPELL_VA_FIELD_6, SPELL_VA_FIELD_7, SPELL_VA_FIELD_8, SPELL_VA_FIELD_9 })
                look->RemoveAurasDueToSpell(rung);
            look->CastSpell(look, FieldLookFor(radius), true);
        }
    }

    // Heroic: +1 yd every 10 s it lives, to 9 yd. The grown field registers with a 1 s warning; the old one ticks till
    // the new one is live (the registry cannot resize a zone: re-register per step, handoff section 3.4).
    void UpdateField()
    {
        if (_oldField && _aliveMs >= _oldFieldEndMs)
        {
            Mechanic::Cancel(me, _oldField);
            _oldField = {};
        }
        if (!_heroic)
            return;
        float const radius = FieldRadius(true, _aliveMs);
        if (radius <= _radius)
            return;
        if (_oldField)
            Mechanic::Cancel(me, _oldField);
        _oldField = _field;
        _oldFieldEndMs = _aliveMs + kFieldOverlapMs;
        float const before = _radius;
        SetField(radius, kFieldOverlapMs);
        LogVault(kVaultKey, "field-grows", Acore::StringFormat("guid={} radius={:.0f}->{:.0f} lived={}s",
            me->GetSpawnId(), before, radius, _aliveMs / 1000));
    }

    // R-1-B B1: it never moves. A grip or a knockback (effects its immunity set cannot stop) is undone: once it has
    // landed it goes back to its post (its spawn), so its field, its disc and the instance's warder count stay put.
    void ReturnToPost(uint32 diff)
    {
        _postCheckMs += diff;
        if (_postCheckMs < kPostCheckMs)
            return;
        _postCheckMs = 0;
        if (me->GetMotionMaster()->GetCurrentMovementGeneratorType() == EFFECT_MOTION_TYPE)
            return;     // still in the air
        Position post = me->GetHomePosition();
        float const off = me->GetExactDist2d(post);
        if (!OffPost(off))
            return;
        me->GetMotionMaster()->Clear(false);
        me->NearTeleportTo(post);
        me->SetControlled(true, UNIT_STATE_ROOT);
        LogVault(kVaultKey, "sentinel-returned", Acore::StringFormat("guid={} off={:.1f}", me->GetSpawnId(), off));
    }

    // VA4: the beam to Doomgrip (a look: the link's reduction is his aura, counted by him).
    void UpdateBeam(uint32 diff)
    {
        _beamCheckMs += diff;
        if (_beamCheckMs < kBeamCheckMs)
            return;
        _beamCheckMs = 0;
        Beam();
    }

    void Beam()
    {
        Creature* doomgrip = DoomgripOf(me);
        if (!doomgrip || !doomgrip->IsAlive() || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        me->CastSpell(doomgrip, SPELL_VA_LINK_BEAM, true);
    }

    // Rule 6: the field, the beam, the disc and the wake look go with every end (reset, evade, death, back to stone).
    void Cleanup(char const* /*why*/)
    {
        if (_field)
            Mechanic::Cancel(me, _field);
        if (_oldField)
            Mechanic::Cancel(me, _oldField);
        _field = {};
        _oldField = {};
        if (Creature* look = ObjectAccessor::GetCreature(*me, _look))
            look->DespawnOrUnsummon();
        _look.Clear();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            me->InterruptNonMeleeSpells(true);
        me->RemoveAurasDueToSpell(SPELL_VA_SENTINEL_WAKES);
        _awake = false;
        _aliveMs = 0;
        _beamCheckMs = 0;
        _postCheckMs = 0;
        _oldFieldEndMs = 0;
        _radius = 0.f;
    }

    MechanicHandle _field;
    MechanicHandle _oldField;
    ObjectGuid _look;
    uint64 _aliveMs = 0;
    uint64 _oldFieldEndMs = 0;
    uint32 _beamCheckMs = 0;
    uint32 _postCheckMs = 0;
    float _radius = 0.f;
    bool _awake = false;
    bool _heroic = false;
};

namespace
{
    npc_brd_vault_sentinel* SentinelAI(Creature* c)
    {
        return c && c->IsAIEnabled ? dynamic_cast<npc_brd_vault_sentinel*>(c->AI()) : nullptr;
    }

    // Awake and standing: what Doomgrip's link counts and what keeps the room's fight going.
    uint32 AwakeSentinels(WorldObject const* o)
    {
        uint32 n = 0;
        for (Creature* c : SentinelsNear(o))
            if (npc_brd_vault_sentinel* ai = SentinelAI(c))
                if (c->IsAlive() && !c->isDying() && ai->Awake())
                    ++n;
        return n;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Watchman Doomgrip (9476): a ScriptedAI on the slot's registry encounter (the instance writes BOSS_VAULT)
// ---------------------------------------------------------------------------------------------------------------------

struct boss_watchman_doomgrip_rework : public ScriptedAI
{
    explicit boss_watchman_doomgrip_rework(Creature* creature)
        : ScriptedAI(creature), _arena(BlackVaultArena(), LeashOptions(kBossKey)) { }

    void Reset() override
    {
        ScriptedAI::Reset();
        Cleanup();
        _arena.Reset();
        _alarmed = false;
        _alarmRetryMs = 0;
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;

        Cleanup();
        OnBossPull(me, kBossKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_VAULT;
        Mechanic::BeginEncounter(me, options);

        _heroic = IsHeroicMap(me);
        _alarmed = true;
        DoZoneInCombat(me, kAlarmZoneYd);
        _arena.Engage(me);
        _sweepPlannedMs = kSweepFirstMs;
        _nextSunderMs = kSunderFirstMs;
        Describe();
        Talk(YELL_VA_ALARM);
        LogVault(kBossKey, "engage", Acore::StringFormat("heroic={} sweep={}s every={}s sentinels-awake={}",
            _heroic ? 1 : 0, kSweepFirstMs / 1000, kSweepEveryMs(_heroic) / 1000, AwakeSentinels(me)));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
        // A wipe ends the Vault attempt (the instance re-stones the sentinels and despawns Doomgrip).
        if (InstanceScript* instance = me->GetInstanceScript())
            instance->SetData(DATA_VAULT_RESET, 1);
    }

    void JustDied(Unit* killer) override
    {
        ScriptedAI::JustDied(killer);
        Talk(YELL_VA_DEATH);
        // His loot is filled before JustDied (Unit::Kill): the gear item he dropped is the one the Safe must not hold.
        uint32 gear = 0;
        for (LootItem const& item : me->loot.items)
            if (GearIndexOf(item.itemid))
            {
                gear = item.itemid;
                break;
            }
        if (gear)
        {
            if (InstanceScript* instance = me->GetInstanceScript())
                instance->SetData(kDataVaultDoomgripItem, gear);
            if (GameObject* safe = SecretSafeOf(me))
                if (safe->AI())
                    safe->AI()->SetData(DATA_SAFE_DOOMGRIP_GEAR, gear);
        }
        Cleanup();
        _arena.Reset();
        LogVault(kBossKey, "death", Acore::StringFormat("killer={} gear={} sentinels-awake={}",
            killer ? killer->GetName() : "none", gear, AwakeSentinels(me)));
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsInCombat())
        {
            // Summoned by the alarm at the doorway: he runs in on whoever opened the coffer (the stock yell at his
            // pull).
            if (!_alarmed && !me->IsInEvadeMode() && me->IsAlive() && VaultState(me) == IN_PROGRESS)
            {
                _alarmRetryMs = _alarmRetryMs > diff ? _alarmRetryMs - diff : 0;
                if (!_alarmRetryMs)
                {
                    _alarmRetryMs = kRetryMs;
                    DoZoneInCombat(me, kAlarmZoneYd);
                }
            }
            return;
        }
        if (!UpdateVictim())
            return;

        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off the room, or nobody in it for 10 s: evading

        UpdateLink(diff);
        if (std::optional<uint8> const due = DraughtDue(me->GetHealthPct(), _drunk))
            Drink(*due, "health");
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_clockMs >= _sweepPlannedMs)
        {
            StartSweep();
            return;
        }
        if (_clockMs >= _nextSunderMs)
            Sunder();
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VA4 Security Link: -25% damage taken per awake sentinel, 75% at most (the aura's stacks)
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateLink(uint32 diff)
    {
        _linkCheckMs += diff;
        if (_linkCheckMs < kLinkCheckMs)
            return;
        _linkCheckMs = 0;
        uint32 const awake = AwakeSentinels(me);
        uint8 const stacks = LinkStacks(awake);
        if (stacks == _linkStacks)
            return;
        if (stacks)
            me->SetAuraStack(SPELL_VA_SECURITY_LINK, me, stacks);
        else
            me->RemoveAurasDueToSpell(SPELL_VA_SECURITY_LINK);
        LogVault(kBossKey, "link", Acore::StringFormat("awake={} stacks={}->{} taken=-{}%", awake, _linkStacks, stacks,
            LinkTakenReductionPct(stacks)));
        _linkStacks = stacks;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VA5 Intruder Sweep: the cone is locked where he faces his victim at the bar's start; the tank steps out too
    // ----------------------------------------------------------------------------------------------------------------

    void StartSweep()
    {
        _sweepPlannedMs = NextDue(_sweepPlannedMs, kSweepEveryMs(_heroic), _clockMs);
        float const pct = kSweepPct(_heroic);
        Position apex = me->GetPosition();
        if (Unit* victim = me->GetVictim())
            apex.SetOrientation(me->GetAngle(victim));
        me->SetFacingTo(apex.GetOrientation());
        DungeonKit::CastBar(me, SPELL_VA_SWEEP_CAST);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(apex, kSweepAngleDeg, kSweepLengthYd),
            Ms(kSweepWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_VA_SWEEP_HIT).Weakened()
            .Within(RoomBounds()).Tag(TAG_VA_SWEEP);
        Track(ref.Handle());
        LogVault(kBossKey, "sweep", Acore::StringFormat("heroic={} pct={:.0f} facing={:.2f} next={}s", _heroic ? 1 : 0,
            pct, apex.GetOrientation(), _sweepPlannedMs / 1000));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VA6 Sunder Armor (his victim, in reach), VA7 Watchman's Draught
    // ----------------------------------------------------------------------------------------------------------------

    void Sunder()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim)
            || me->CastSpell(victim, SPELL_VA_SUNDER_ARMOR, false) != SPELL_CAST_OK)
        {
            _nextSunderMs = _clockMs + kRetryMs;
            return;
        }
        _nextSunderMs = _clockMs + urand(kSunderEveryMinMs, kSunderEveryMaxMs);
        Aura const* sunder = victim->GetAura(SPELL_VA_SUNDER_ARMOR, me->GetGUID());
        LogVault(kBossKey, "sunder", Acore::StringFormat("target={} stacks={}", victim->GetName(),
            sunder ? sunder->GetStackAmount() : 0));
    }

    void Drink(uint8 index, char const* why)
    {
        _drunk = static_cast<uint8>(_drunk | (1u << index));
        me->CastSpell(me, SPELL_VA_WATCHMANS_DRAUGHT, true);
        LogVault(kBossKey, "draught", Acore::StringFormat("why={} at={:.0f}% health={:.1f}", why, kDraughtAtPct[index],
            me->GetHealthPct()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SP "Boss data"): sentinels first (damage dealers; the tank keeps him), a stone one is ignored, the
    // Draught is the purge
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_BRD_VAULT_SENTINEL, 1, BossMechanics::Who::Dps);
        d.ignores.emplace_back(NPC_BRD_VAULT_SENTINEL, BossMechanics::Condition::Custom([](Unit const* u)
        {
            return IsStone(u);
        }));
        d.purges.emplace_back(NPC_DOOMGRIP, SPELL_VA_WATCHMANS_DRAUGHT, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd vault <mechanic>` entry points
    // ----------------------------------------------------------------------------------------------------------------

    std::string TestSweep()
    {
        if (!me->IsInCombat())
            return "Doomgrip must be in combat.";
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return "He is casting.";
        StartSweep();
        return {};
    }

    std::string TestDraught()
    {
        if (!me->IsInCombat())
            return "Doomgrip must be in combat.";
        Drink(_drunk & 1 ? 1 : 0, "test");
        return {};
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} link={} sweep={}s sunder={}s drunk={:02b} engaged={}",
            _clockMs / 1000, _heroic ? 1 : 0, _linkStacks, _sweepPlannedMs / 1000, _nextSunderMs / 1000, _drunk,
            me->IsEngaged() ? 1 : 0);
    }

private:
    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 32)
            _live.erase(_live.begin(), _live.begin() + 16);
    }

    // Rule 6: nothing pending, the link off him, his Sunder off the players (reset, evade, death, a new pull).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        me->RemoveAurasDueToSpell(SPELL_VA_SECURITY_LINK);
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    player->RemoveAurasDueToSpell(SPELL_VA_SUNDER_ARMOR, me->GetGUID());
        _clockMs = 0;
        _sweepPlannedMs = 0;
        _nextSunderMs = 0;
        _linkCheckMs = 0;
        _linkStacks = 0;
        _drunk = 0;
    }

    DungeonKit::ArenaGuard _arena;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;                // ms since the pull
    uint64 _sweepPlannedMs = 0;         // the planned start of the next sweep (start to start)
    uint64 _nextSunderMs = 0;
    uint32 _linkCheckMs = 0;
    uint32 _alarmRetryMs = 0;
    uint8 _linkStacks = 0;
    uint8 _drunk = 0;                   // bit 0: the 60% draught, bit 1: the 30% one
    bool _heroic = false;
    bool _alarmed = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// The Secret Safe (161495): the event's clock (VA1, VA2, VA8) and the Safe's contents
// ---------------------------------------------------------------------------------------------------------------------

struct go_brd_vault_secret_safe : public GameObjectAI
{
    explicit go_brd_vault_secret_safe(GameObject* go) : GameObjectAI(go), _lockdown(LockdownOptions()) { }

    void UpdateAI(uint32 diff) override
    {
        uint32 const state = VaultState(me);
        if (!_running)
        {
            if (state == IN_PROGRESS)
                Start();
            return;
        }
        if (state == DONE)
        {
            Finish("done");
            return;
        }
        if (state != IN_PROGRESS)
        {
            Stop("reset");
            return;
        }
        _clockMs += diff;
        _lockdown.Update(me, diff);
        UpdateWakes();
        UpdateSeals();
    }

    void SetData(uint32 id, uint32 value) override
    {
        if (id == DATA_SAFE_DOOMGRIP_GEAR)
            _doomgripGear = value;
    }

    uint32 GetData(uint32 id) const override
    {
        return id == DATA_SAFE_DOOMGRIP_GEAR ? _doomgripGear : 0;
    }

    // The Safe is being opened (brd_vault_safe_loot): its table rolled `loot`; the script's set replaces anything of
    // it the table holds (section 7 #17: the Cinder always, one gear item never Doomgrip's, the bags the clock left).
    void FillSafe(Loot& loot, Player const* opener)
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return;
        if (_running && instance->GetBossState(BOSS_VAULT) == DONE)
            Finish("opened");       // opened in the same tick the last warder fell
        uint32 const clock = instance->GetData(DATA_VAULT_CLOCK);
        bool const heroic = IsHeroicMap(me);
        uint32 const doomgripItem = _doomgripGear ? _doomgripGear : instance->GetData(kDataVaultDoomgripItem);
        uint32 const stripped = StripManaged(loot);
        SafeItems const items = SafeItemsFor(clock, heroic, doomgripItem, urand(0, 0xFFFF));
        std::string list;
        for (std::size_t i = 0; i < items.count; ++i)
        {
            loot.AddItem(LootStoreItem(items.items[i], 0, 100.f, false, LOOT_MODE_DEFAULT, 0, 1, 1));
            list += Acore::StringFormat("{}{}", i ? "," : "", items.items[i]);
        }
        LogVault(kVaultKey, "safe-filled", Acore::StringFormat("clock={}s heroic={} items=[{}] doomgrip-gear={} "
            "stripped={} opener={}", clock, heroic ? 1 : 0, list, doomgripItem, stripped,
            opener ? opener->GetName() : "none"));
    }

    // `.dbtest brd vault` entry points.
    std::string TestWake()
    {
        if (!_running)
            return "The Vault is not running (open the Dark Coffer, or `.dbtest brd instance vault`).";
        if (!WakeNext(true))
            return "No stone sentinel left to wake.";
        return {};
    }

    std::string TestSkip(uint32 seconds)
    {
        if (!_running)
            return "The Vault is not running.";
        _clockMs += uint64(seconds) * 1000;
        return {};
    }

    std::string TestState() const
    {
        VaultSafe const now = VaultSafeFor(_running ? FinishedSeconds(_clockMs) : 0);
        return Acore::StringFormat("running={} clock={}s heroic={} woken={}/{} sealed={:03b} lockdown={} "
            "safe-if-done-now: gear={} bags={} doomgrip-gear={}", _running ? 1 : 0, _clockMs / 1000,
            _heroic ? 1 : 0, _woken, _order.size(), _sealed, _fence ? 1 : 0, now.gear ? 1 : 0, now.bags,
            _doomgripGear);
    }

private:
    static DungeonKit::ConfineOptions LockdownOptions()
    {
        DungeonKit::ConfineOptions options;
        options.logPrefix = "brd vault lockdown";
        return options;
    }

    // The alarm (the instance went IN_PROGRESS: the Dark Coffer opened): the clock starts, the four go back to stone
    // in a fresh order, the doorway seals.
    void Start()
    {
        _running = true;
        _clockMs = 0;
        _woken = 0;
        _sealed = 0;
        _doomgripGear = 0;
        _heroic = IsHeroicMap(me);
        _order.clear();
        std::vector<Creature*> const sentinels = SentinelsNear(me);
        std::array<uint8, kSentinelCount> const order = WakeOrder(urand(0, 0x7FFFFFFF));
        for (uint8 i : order)
            if (i < sentinels.size())
                _order.push_back(sentinels[i]->GetGUID());
        for (Creature* sentinel : sentinels)
            if (sentinel->IsAlive())
                if (npc_brd_vault_sentinel* ai = SentinelAI(sentinel))
                    ai->DoAction(ACTION_SENTINEL_DORMANT);
        SealDoorway();
        LogVault(kVaultKey, "alarm", Acore::StringFormat("heroic={} sentinels={} wakes={}s+{}s seals={}/{}/{}s "
            "lockdown={}", _heroic ? 1 : 0, _order.size(), kWakeFirstMs / 1000, kWakeEveryMs(_heroic) / 1000,
            kSealAtS[0], kSealAtS[1], kSealAtS[2], _doorLook ? 1 : 0));
    }

    // The last warder fell (the instance went DONE): the finishing time is stored (the Safe reads it), the doorway
    // opens.
    void Finish(char const* why)
    {
        _running = false;
        uint32 const seconds = FinishedSeconds(_clockMs);
        if (InstanceScript* instance = me->GetInstanceScript())
            if (!instance->GetData(DATA_VAULT_CLOCK))
                instance->SetData(DATA_VAULT_CLOCK, seconds);
        OpenDoorway();
        VaultSafe const safe = VaultSafeFor(seconds);
        LogVault(kVaultKey, "done", Acore::StringFormat("why={} clock={}s cinder={} gear={} bags={} woken={}", why,
            seconds, safe.cinder ? 1 : 0, safe.gear ? 1 : 0, safe.bags, _woken));
    }

    // A wipe (the instance went back to NOT_STARTED): the doorway opens; the instance re-stones the four.
    void Stop(char const* why)
    {
        _running = false;
        OpenDoorway();
        LogVault(kVaultKey, "reset", Acore::StringFormat("why={} clock={}s woken={}", why, _clockMs / 1000, _woken));
        _clockMs = 0;
        _woken = 0;
        _sealed = 0;
        _order.clear();
    }

    // ---- VA1 Lockdown ----------------------------------------------------------------------------------------------

    void SealDoorway()
    {
        OpenDoorway();
        DungeonKit::Arena const strip(DungeonKit::ArenaRegion::Polygon(FencePolygon(), kFenceZMin, kFenceZMax));
        Position const putOut(kDoomgripSummon.x, kDoomgripSummon.y, kDoomgripSummon.z, kDoomgripSummon.o);
        _fence = _lockdown.KeepOut(strip, putOut);
        Vec2 const door = DoorwayCenter();
        float const facing = std::atan2(kDoorwayOut.y, kDoorwayOut.x);
        if (Creature* look = me->SummonCreature(NPC_BRD_STALKER, Position(door.x, door.y, kDoorwayZ, facing),
            TEMPSUMMON_MANUAL_DESPAWN))
        {
            look->SetReactState(REACT_PASSIVE);
            look->CastSpell(look, SPELL_VA_LOCKDOWN, true);
            _doorLook = look->GetGUID();
        }
    }

    void OpenDoorway()
    {
        _lockdown.Clear();
        _fence = 0;
        if (Map* map = me->FindMap())
            if (Creature* look = map->GetCreature(_doorLook))
                look->DespawnOrUnsummon();
        _doorLook.Clear();
    }

    // ---- VA2 The wakes ---------------------------------------------------------------------------------------------

    bool AnythingAwakeAlive() const
    {
        if (Creature* doomgrip = DoomgripOf(me))
            if (doomgrip->IsAlive())
                return true;
        return AwakeSentinels(me) > 0;
    }

    void UpdateWakes()
    {
        if (_woken >= kSentinelCount)
            return;
        bool const early = _clockMs < WakeDueMs(_woken, _heroic);
        // The room search only matters between the first wake's time and the next one's.
        bool const awake = !early || _clockMs < kWakeFirstMs || AnythingAwakeAlive();
        if (WakeNow(_woken, _clockMs, _heroic, awake))
            WakeNext(early);
    }

    // The next sentinel of the order still standing in stone wakes (a dead one, its respawn pending, is skipped till
    // it stands).
    bool WakeNext(bool early)
    {
        Map* map = me->FindMap();
        if (!map)
            return false;
        for (std::size_t i = _woken; i < _order.size(); ++i)
        {
            Creature* sentinel = map->GetCreature(_order[i]);
            npc_brd_vault_sentinel* ai = SentinelAI(sentinel);
            if (!sentinel || !sentinel->IsAlive() || !ai || ai->Awake())
                continue;
            std::swap(_order[_woken], _order[i]);
            ai->DoAction(ACTION_SENTINEL_WAKE);
            ++_woken;
            DoomgripSays(me, EMOTE_VA_SENTINEL);
            LogVault(kVaultKey, "sentinel-wakes", Acore::StringFormat("n={} at={}s early={} guid={}", _woken,
                _clockMs / 1000, early ? 1 : 0, sentinel->GetSpawnId()));
            return true;
        }
        return false;
    }

    // ---- VA8 The seals ---------------------------------------------------------------------------------------------

    void UpdateSeals()
    {
        uint8 const passed = SealsPassed(_clockMs);
        for (std::size_t i = 0; i < kSealAtS.size(); ++i)
        {
            uint8 const bit = static_cast<uint8>(1u << i);
            if (!(passed & bit) || (_sealed & bit))
                continue;
            _sealed = static_cast<uint8>(_sealed | bit);
            DoomgripSays(me, kSealText[i]);
            VaultSafe const left = VaultSafeFor(FinishedSeconds(_clockMs));
            LogVault(kVaultKey, "seal", Acore::StringFormat("n={} at={}s gear={} bags={}", i + 1, kSealAtS[i],
                left.gear ? 1 : 0, left.bags));
        }
    }

    // Takes out what the Safe's table rolled of the script's items (STAGE-D9-REPORT: the table needs a row for the
    // engine to fill it at all). Counted items are uncounted the way Loot::AddItem counted them.
    static uint32 StripManaged(Loot& loot)
    {
        uint32 removed = 0;
        std::vector<LootItem> kept;
        kept.reserve(loot.items.size());
        for (LootItem const& item : loot.items)
        {
            if (!IsSafeManagedItem(item.itemid))
            {
                kept.push_back(item);
                continue;
            }
            ++removed;
            ItemTemplate const* proto = sObjectMgr->GetItemTemplate(item.itemid);
            if (!item.needs_quest && item.conditions.empty() && proto && !proto->HasFlag(ITEM_FLAG_MULTI_DROP)
                && loot.unlootedCount)
                --loot.unlootedCount;
        }
        for (std::size_t i = 0; i < kept.size(); ++i)
            kept[i].itemIndex = static_cast<uint32>(i);
        loot.items = std::move(kept);
        return removed;
    }

    DungeonKit::Confinement _lockdown;
    std::vector<ObjectGuid> _order;     // the four in their wake order (the first `_woken` are awake or dead)
    ObjectGuid _doorLook;
    uint64 _clockMs = 0;                // ms since the alarm
    uint32 _fence = 0;
    uint32 _doomgripGear = 0;           // the gear item Doomgrip dropped (his JustDied)
    std::size_t _woken = 0;
    uint8 _sealed = 0;                  // bit i: seal i announced
    bool _running = false;
    bool _heroic = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// The Safe's loot: the engine fills it from the chest's table when it is opened, this adds the script's set before the
// group's rights and rolls are worked out (Loot::FillLoot runs the hook between the two).
// ---------------------------------------------------------------------------------------------------------------------

class brd_vault_safe_loot : public MiscScript
{
public:
    brd_vault_safe_loot() : MiscScript("brd_vault_safe_loot", { MISCHOOK_ON_AFTER_LOOT_TEMPLATE_PROCESS }) { }

    void OnAfterLootTemplateProcess(Loot* loot, LootTemplate const* /*tab*/, LootStore const& store, Player* owner,
        bool /*personal*/, bool /*noEmptyError*/, uint16 /*lootMode*/) override
    {
        if (!loot || !owner || &store != &LootTemplates_Gameobject || owner->GetMapId() != kMapBlackrockDepths)
            return;
        GameObject* safe = SecretSafeOf(owner);
        if (!safe || &safe->loot != loot)
            return;
        if (auto* ai = dynamic_cast<go_brd_vault_secret_safe*>(safe->AI()))
            ai->FillSafe(*loot, owner);
    }
};

namespace
{
    boss_watchman_doomgrip_rework* FindDoomgripAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_DOOMGRIP);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_watchman_doomgrip_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Watchman Doomgrip is not running boss_watchman_doomgrip_rework (check the "
                "ScriptName).");
        return ai;
    }

    go_brd_vault_secret_safe* FindSafeAI(ChatHandler* handler)
    {
        Player* player = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!player || player->GetMapId() != kMapBlackrockDepths)
        {
            handler->SendErrorMessage("{}", "Only inside Blackrock Depths.");
            return nullptr;
        }
        GameObject* safe = SecretSafeOf(player);
        auto* ai = safe ? dynamic_cast<go_brd_vault_secret_safe*>(safe->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Secret Safe is not loaded or not running go_brd_vault_secret_safe "
                "(check the gameobject_template ScriptName).");
        return ai;
    }

    bool Finish(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Vault: {} fired.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_DOOMGRIP, BOSS_VAULT);
    }

    bool HandleState(ChatHandler* handler)
    {
        go_brd_vault_secret_safe* safe = FindSafeAI(handler);
        if (!safe)
            return false;
        handler->PSendSysMessage("Vault: {}", safe->TestState());
        if (Player* player = handler->GetSession()->GetPlayer())
        {
            handler->PSendSysMessage("Vault: sentinels awake {}", AwakeSentinels(player));
            if (Creature* doomgrip = DoomgripOf(player))
                if (auto* ai = doomgrip->IsAIEnabled ? dynamic_cast<boss_watchman_doomgrip_rework*>(doomgrip->AI())
                    : nullptr)
                    handler->PSendSysMessage("Doomgrip: {}", ai->TestState());
        }
        return true;
    }

    bool HandleWake(ChatHandler* handler)
    {
        go_brd_vault_secret_safe* safe = FindSafeAI(handler);
        return safe && Finish(handler, safe->TestWake(), "the next sentinel wakes (VA2)");
    }

    // `.dbtest brd vault skip <s>`: the clock jumps ahead (the wakes and the seals catch up at once).
    bool HandleSkip(ChatHandler* handler, uint32 seconds)
    {
        go_brd_vault_secret_safe* safe = FindSafeAI(handler);
        return safe && Finish(handler, safe->TestSkip(seconds), "the clock skip (VA2, VA8)");
    }

    bool HandleSweep(ChatHandler* handler)
    {
        boss_watchman_doomgrip_rework* ai = FindDoomgripAI(handler);
        return ai && Finish(handler, ai->TestSweep(), "Intruder Sweep now (VA5)");
    }

    bool HandleDraught(ChatHandler* handler)
    {
        boss_watchman_doomgrip_rework* ai = FindDoomgripAI(handler);
        return ai && Finish(handler, ai->TestDraught(), "Watchman's Draught now (VA7)");
    }

    // `.dbtest brd vault safe [s]`: what the Safe holds for a finishing time (default: the stored one).
    bool HandleSafe(ChatHandler* handler, Optional<uint32> seconds)
    {
        go_brd_vault_secret_safe* safe = FindSafeAI(handler);
        if (!safe)
            return false;
        Player* player = handler->GetSession()->GetPlayer();
        InstanceScript* instance = player->GetInstanceScript();
        uint32 const clock = seconds ? *seconds : (instance ? instance->GetData(DATA_VAULT_CLOCK) : 0);
        uint32 const his = safe->GetData(DATA_SAFE_DOOMGRIP_GEAR);
        SafeItems const items = SafeItemsFor(clock, IsHeroicMap(player), his, urand(0, 0xFFFF));
        std::string list;
        for (std::size_t i = 0; i < items.count; ++i)
            list += Acore::StringFormat("{}{}", i ? ", " : "", items.items[i]);
        handler->PSendSysMessage("Vault: finishing time {}s -> the Safe holds [{}] (Doomgrip's gear {}; the gear pick "
            "is rolled again when it is opened)", clock, list, his);
        return true;
    }

    ChatCommandTable const& VaultTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,    SEC_GAMEMASTER, Console::No },
            { "wake",       HandleWake,     SEC_GAMEMASTER, Console::No },
            { "skip",       HandleSkip,     SEC_GAMEMASTER, Console::No },
            { "sweep",      HandleSweep,    SEC_GAMEMASTER, Console::No },
            { "draught",    HandleDraught,  SEC_GAMEMASTER, Console::No },
            { "safe",       HandleSafe,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_watchman_doomgrip_rework()
{
    RegisterDungeonReworkCreatureAI(boss_watchman_doomgrip_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_vault_sentinel, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_brd_vault_secret_safe, BlackrockDepthsRework::kInstanceScriptName);
    new brd_vault_safe_loot();
    BrdTest::RegisterBoss("vault", VaultTestCommands());
}
