/*
 * mod-dungeon-bosses, Gnomeregan D2: the DoseField machine (GnomereganMachines.h; what it does: the header
 * ViscousFalloutMachine.h). The arithmetic is GnomerFallout::DoseLedger (ViscousFalloutLogic.h); this file applies it
 * to players: the aura, the reassert, the polls and the callbacks.
 */

#include "ViscousFalloutMachine.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "GnomereganRework.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "StringFormat.h"
#include <algorithm>
#include <deque>
#include <string>
#include <utility>

namespace GnomereganMachines
{
    namespace
    {
        using GnomerFallout::DoseEvents;

        class FalloutDoseField final : public DoseField
        {
        public:
            FalloutDoseField(MachineOwner const& owner, DoseSpec spec)
                : _logKey(owner.logKey ? owner.logKey : ""), _heroic(owner.heroic), _spec(std::move(spec)),
                _ledger(DoseRulesOf(_spec))
            {
                // The owner's map, kept (R-1-A m3: never sMapMgr from the map thread; the machine lives in an AI or
                // a package on that map, so the map outlives it).
                if (owner.owner)
                {
                    _owner = owner.owner->GetGUID();
                    _map = owner.owner->GetMap();
                }
            }

            void Update(uint32 diff) override
            {
                Creature* owner = Owner();
                if (!owner)
                    return;
                Map* map = owner->GetMap();
                _pollMs += diff;
                _reassertMs += diff;
                if (_pollMs >= GnomerFallout::Tune::kPollMs)
                {
                    uint32 const elapsed = _pollMs;
                    _pollMs = 0;
                    for (uint64 const raw : _ledger.Known())
                    {
                        Player* player = ObjectAccessor::GetPlayer(map, ObjectGuid(raw));
                        if (!player || !player->IsInWorld())
                        {
                            _ledger.Forget(raw);
                            _pending.erase(std::remove_if(_pending.begin(), _pending.end(),
                                [raw](Pending const& p) { return p.player == raw; }), _pending.end());
                            continue;
                        }
                        if (!player->IsAlive())
                        {
                            if (_ledger.Dose(raw) || _ledger.CapPending(raw))
                            {
                                Queue(raw, _ledger.Set(raw, 0));
                                Apply(owner, player);
                                Log("death", player, "");
                            }
                            continue;
                        }
                        bool const drains = !_spec.drains || _spec.drains(player);
                        DoseEvents const events = _ledger.Tick(raw, elapsed, drains);
                        if (events.drained)
                            Apply(owner, player);
                        Queue(raw, events);
                    }
                }
                Flush(owner);
                if (_reassertMs >= GnomerFallout::Tune::kReassertMs)
                {
                    _reassertMs = 0;
                    for (auto const& [raw, dose] : _ledger.Carriers())
                        if (Player* player = ObjectAccessor::GetPlayer(map, ObjectGuid(raw)))
                            if (player->IsAlive())
                                Apply(owner, player);
                }
            }

            void Clear() override
            {
                if (Map* map = OwnerMap())
                    for (uint64 const raw : _ledger.Known())
                        if (Player* player = ObjectAccessor::GetPlayer(map, ObjectGuid(raw)))
                            if (_spec.auraSpellId)
                                player->RemoveAurasDueToSpell(_spec.auraSpellId, _owner);
                _ledger.Clear();
                _pending.clear();
                _pollMs = 0;
                _reassertMs = 0;
            }

            std::string Describe() const override
            {
                auto const carriers = _ledger.Carriers();
                std::string top;
                for (std::size_t i = 0; i < carriers.size() && i < 5; ++i)
                    top += Acore::StringFormat("{}{}:{}", i ? " " : "", ObjectGuid(carriers[i].first).GetCounter(),
                        carriers[i].second);
                GnomerFallout::DoseRules const& r = _ledger.Rules();
                return Acore::StringFormat("dose aura={} carriers={} top=[{}] cap={} drain={} leak={} meltdown={} "
                    "pending={}", _spec.auraSpellId, carriers.size(), top, r.capAt, r.drainEveryMs, r.leakAt,
                    r.meltdownAt, _pending.size());
            }

            uint32 Add(Player* player, int32 doses, char const* why) override
            {
                if (!player || !doses)
                    return player ? _ledger.Dose(player->GetGUID().GetRawValue()) : 0;
                uint64 const raw = player->GetGUID().GetRawValue();
                Queue(raw, _ledger.Add(raw, doses));
                if (Creature* owner = Owner())
                    Apply(owner, player);
                (void)why;
                return _ledger.Dose(raw);
            }

            void Set(Player* player, uint32 dose, char const* why) override
            {
                if (!player)
                    return;
                uint64 const raw = player->GetGUID().GetRawValue();
                Queue(raw, _ledger.Set(raw, dose));
                if (Creature* owner = Owner())
                    Apply(owner, player);
                Log("set", player, Acore::StringFormat("why={}", why ? why : "-"));
            }

            uint32 Halve(Player* player, char const* why) override
            {
                if (!player)
                    return 0;
                uint64 const raw = player->GetGUID().GetRawValue();
                uint32 const before = _ledger.Dose(raw);
                uint32 shed = 0;
                Queue(raw, _ledger.Halve(raw, shed));
                if (Creature* owner = Owner())
                    Apply(owner, player);
                Log("halve", player, Acore::StringFormat("from={} shed={} why={}", before, shed, why ? why : "-"));
                return _ledger.Dose(raw);
            }

            uint32 Dose(ObjectGuid player) const override
            {
                return _ledger.Dose(player.GetRawValue());
            }

            std::vector<std::pair<ObjectGuid, uint32>> Carriers() const override
            {
                std::vector<std::pair<ObjectGuid, uint32>> out;
                for (auto const& [raw, dose] : _ledger.Carriers())
                    out.emplace_back(ObjectGuid(raw), dose);
                return out;
            }

        private:
            struct Pending
            {
                uint64 player = 0;
                DoseEvents events;
            };

            Map* OwnerMap() const
            {
                return _owner.IsEmpty() ? nullptr : _map;
            }

            Creature* Owner() const
            {
                Map* map = OwnerMap();
                return map ? map->GetCreature(_owner) : nullptr;
            }

            void Queue(uint64 raw, DoseEvents const& events)
            {
                if (events.cap || events.meltdown || events.leakEmote || events.meltdownEmote || events.leakDrop)
                    _pending.push_back({ raw, events });
            }

            // The aura's stack count = the dose (0 removes it), cast by the owner.
            void Apply(Creature* owner, Player* player)
            {
                if (!_spec.auraSpellId || !owner || !player)
                    return;
                uint32 const want = GnomerFallout::ShownStacks(_ledger.Dose(player->GetGUID().GetRawValue()));
                uint32 const have = DungeonKit::Stacks(player, _spec.auraSpellId, owner->GetGUID());
                if (want == have)
                    return;
                if (!want)
                {
                    player->RemoveAurasDueToSpell(_spec.auraSpellId, owner->GetGUID());
                    return;
                }
                DungeonKit::AddStacks(player, _spec.auraSpellId, int32(want) - int32(have), owner,
                    GnomerFallout::Tune::kAuraStackLimit);
            }

            // Every queued event, from Update only (never from inside a registry callback, rule 11). A callback may
            // add dose (a Sickness pulse, a Leaking pool under a player): those events wait for the next Update.
            void Flush(Creature* owner)
            {
                if (_pending.empty())
                    return;
                std::deque<Pending> now;
                now.swap(_pending);
                Map* map = owner->GetMap();
                for (Pending const& p : now)
                {
                    Player* player = ObjectAccessor::GetPlayer(map, ObjectGuid(p.player));
                    if (!player || !player->IsInWorld())
                        continue;
                    DoseEvents const& e = p.events;
                    if (e.cap)
                    {
                        Log("cap", player, Acore::StringFormat("at={}", _ledger.Rules().capAt));
                        if (_spec.onCap && player->IsAlive())
                            _spec.onCap(player);
                        Queue(p.player, _ledger.ResolveCap(p.player));
                        Apply(owner, player);
                    }
                    if (e.leakEmote && _spec.leakEmoteGroup && owner->IsAIEnabled)
                        owner->AI()->Talk(*_spec.leakEmoteGroup, player);
                    if (e.meltdownEmote && _spec.meltdownEmoteGroup && owner->IsAIEnabled)
                        owner->AI()->Talk(*_spec.meltdownEmoteGroup, player);
                    if (e.meltdown)
                    {
                        Log(e.meltdown > 0 ? "meltdown-on" : "meltdown-off", player, "");
                        if (_spec.onMeltdown)
                            _spec.onMeltdown(player, e.meltdown > 0);
                    }
                    if (e.leakDrop && player->IsAlive())
                    {
                        Log("leak", player, Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f})", player->GetPositionX(),
                            player->GetPositionY(), player->GetPositionZ()));
                        if (_spec.onLeak)
                            _spec.onLeak(player, player->GetPosition());
                    }
                }
            }

            void Log(char const* what, Player const* player, std::string const& detail)
            {
                uint64 const raw = player ? player->GetGUID().GetRawValue() : 0;
                DungeonKit::LogMechanic(GnomereganRework::kLogDungeon, _logKey, "dose", Acore::StringFormat(
                    "{} player={} dose={} heroic={}{}{}", what, player ? player->GetName() : "-", _ledger.Dose(raw),
                    _heroic ? 1 : 0, detail.empty() ? "" : " ", detail));
            }

            ObjectGuid _owner;
            Map* _map = nullptr;
            char const* _logKey;
            bool _heroic;
            DoseSpec _spec;
            GnomerFallout::DoseLedger _ledger;
            std::deque<Pending> _pending;
            uint32 _pollMs = 0;
            uint32 _reassertMs = 0;
        };
    }

    std::unique_ptr<DoseField> MakeDoseField(MachineOwner const& owner, DoseSpec spec)
    {
        return std::make_unique<FalloutDoseField>(owner, std::move(spec));
    }
}
