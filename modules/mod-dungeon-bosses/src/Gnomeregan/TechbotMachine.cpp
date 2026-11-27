/*
 * mod-dungeon-bosses, Gnomeregan D1: the Duplicator machine (GnomereganMachines.h; TechbotMachine.h says how it runs).
 * Owned by Techbot's AI for his Dupe Bugs (TB3) and by D6Ha's package for the hard mode's bombs (MT16).
 */

#include "TechbotMachine.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "Map.h"
#include "Random.h"
#include "Spell.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>

namespace GnomereganMachines
{
    using namespace GnomerTechbot;

    DuplicatorSpec TechbotBugSpec(bool heroic)
    {
        DupRule const rule = BugRule(heroic);
        DuplicatorSpec spec;
        spec.barSpellId = DuplicationSpell(heroic);
        spec.castMs = rule.castMs;
        spec.firstAfterMs = rule.firstAfterMs;
        spec.repeatMs = rule.repeatMs;
        spec.capAlive = rule.capAlive;
        spec.entries = { GnomereganRework::NPC_DUPE_BUG };
        spec.emoteGroup = EMOTE_DUPLICATE;
        return spec;
    }

    namespace
    {
        float constexpr kTwoPi = 6.28318530718f;

        struct Tracked
        {
            ObjectGuid guid;
            DupClock clock;
            std::int32_t lastRemainingMs = 0;
            std::uint32_t sinceSeenMs = 0;
        };

        class DuplicatorMachine final : public Duplicator
        {
        public:
            DuplicatorMachine(MachineOwner const& owner, DuplicatorSpec spec)
                : _owner(owner.owner ? owner.owner->GetGUID() : ObjectGuid::Empty),
                  _map(owner.owner ? owner.owner->GetMap() : nullptr), _logKey(owner.logKey ? owner.logKey : ""),
                  _heroic(owner.heroic), _spec(std::move(spec))
            {
                _rule.castMs = _spec.castMs;
                _rule.firstAfterMs = _spec.firstAfterMs;
                _rule.repeatMs = _spec.repeatMs;
                _rule.capAlive = _spec.capAlive;
                // R-1-A m2: a bar that applies an aura of itself is judged by that aura alone.
                SpellInfo const* bar = _spec.barSpellId ? sSpellMgr->GetSpellInfo(_spec.barSpellId) : nullptr;
                _barMarks = bar && bar->HasAnyAura();
            }

            void Update(uint32 diff) override
            {
                Creature* owner = Owner();
                if (!owner || !owner->IsInWorld())
                    return;
                std::vector<std::pair<Creature*, Creature*>> copies;    // (source, copy), set up after the loop
                uint32 alive = Alive();
                // The bars in flight: each is a copy on its way, so the cap counts it (R-1-A m1).
                uint32 casting = uint32(Casting().size());
                _inUpdate = true;       // a Track or Forget from a summon hook waits for the loop's end
                for (auto it = _units.begin(); it != _units.end();)
                {
                    Creature* unit = _map->GetCreature(it->guid);
                    if (!unit || !unit->IsAlive() || !unit->IsInWorld())
                    {
                        it = _units.erase(it);
                        continue;
                    }
                    Tracked& t = *it;
                    t.clock.lifeMs += diff;
                    if (t.clock.casting)
                    {
                        if (Spell* bar = unit->FindCurrentSpellBySpellId(_spec.barSpellId))
                        {
                            t.lastRemainingMs = bar->GetCastTimeRemaining();
                            t.sinceSeenMs = 0;
                        }
                        else
                        {
                            t.sinceSeenMs += diff;
                            bool const marked = unit->HasAura(_spec.barSpellId);
                            bool const completed = CastCompleted(marked, t.lastRemainingMs, t.sinceSeenMs, _barMarks);
                            unit->RemoveAurasDueToSpell(_spec.barSpellId);
                            OnCastEnded(t.clock, _rule, completed);
                            casting = casting ? casting - 1 : 0;
                            if (completed && !CopyFits(_rule, alive))
                                Log("copy-capped", Acore::StringFormat("source={} alive={} cap={}",
                                    unit->GetGUID().GetCounter(), alive, _rule.capAlive));
                            else if (completed)
                            {
                                if (Creature* copy = Copy(owner, unit))
                                {
                                    copies.emplace_back(unit, copy);
                                    ++alive;
                                }
                            }
                            else
                                Log("stopped", Acore::StringFormat("unit={} life={} starts={}",
                                    unit->GetGUID().GetCounter(), t.clock.lifeMs, t.clock.starts));
                        }
                    }
                    else if (DueToStart(t.clock, _rule, alive, casting))
                    {
                        Start(unit, t);
                        if (t.clock.casting)
                            ++casting;
                    }
                    ++it;
                }
                _inUpdate = false;
                for (ObjectGuid const& guid : _pendingForget)
                    Forget(guid);
                _pendingForget.clear();
                for (ObjectGuid const& guid : _pendingTrack)
                    if (Creature* unit = _map->GetCreature(guid))
                        Track(unit);
                _pendingTrack.clear();
                for (auto const& [source, copy] : copies)
                {
                    Track(copy);
                    StartCopyClock(copy->GetGUID());
                    if (_spec.onCopy)
                        _spec.onCopy(source, copy);
                }
            }

            void Clear() override
            {
                uint32 gone = 0;
                if (_map)
                    for (Tracked const& t : _units)
                        if (Creature* unit = _map->GetCreature(t.guid))
                            if (unit->IsAlive())
                            {
                                unit->DespawnOrUnsummon(Milliseconds(1));
                                ++gone;
                            }
                if (!_units.empty() || gone)
                    Log("clear", Acore::StringFormat("despawned={} copies={}", gone, _copies));
                _units.clear();
                _pendingTrack.clear();
                _pendingForget.clear();
                _copies = 0;
            }

            std::string Describe() const override
            {
                return Acore::StringFormat("duplicator alive={} casting={} copies={} cap={} first={} repeat={} cast={}",
                    Alive(), Casting().size(), _copies, _spec.capAlive, _spec.firstAfterMs, _spec.repeatMs,
                    _spec.castMs);
            }

            void Track(Creature* unit) override
            {
                if (!unit)
                    return;
                if (_inUpdate)
                {
                    _pendingTrack.push_back(unit->GetGUID());
                    return;
                }
                if (!_spec.entries.empty()
                    && std::find(_spec.entries.begin(), _spec.entries.end(), unit->GetEntry()) == _spec.entries.end())
                    return;     // another entry only counts (the contract): never duplicates
                ObjectGuid const guid = unit->GetGUID();
                if (std::any_of(_units.begin(), _units.end(), [&guid](Tracked const& t) { return t.guid == guid; }))
                    return;
                Tracked t;
                t.guid = guid;
                t.clock = StartClock(_rule);
                _units.push_back(t);
            }

            void Forget(ObjectGuid unit) override
            {
                if (_inUpdate)
                {
                    _pendingForget.push_back(unit);
                    return;
                }
                _units.erase(std::remove_if(_units.begin(), _units.end(),
                    [&unit](Tracked const& t) { return t.guid == unit; }), _units.end());
            }

            std::vector<ObjectGuid> Units() const override
            {
                std::vector<ObjectGuid> out;
                if (!_map)
                    return out;
                for (Tracked const& t : _units)
                    if (Creature* unit = _map->GetCreature(t.guid))
                        if (unit->IsAlive())
                            out.push_back(t.guid);
                return out;
            }

            uint32 Alive() const override
            {
                return uint32(Units().size());
            }

            std::vector<ObjectGuid> Casting() const override
            {
                std::vector<ObjectGuid> out;
                if (!_map)
                    return out;
                for (Tracked const& t : _units)
                    if (t.clock.casting)
                        if (Creature* unit = _map->GetCreature(t.guid))
                            if (unit->IsAlive())
                                out.push_back(t.guid);
                return out;
            }

        private:
            // DQ1: a copy's clock (TechbotLogic.h CopyClock: a once-only rule's copies never duplicate).
            void StartCopyClock(ObjectGuid guid)
            {
                for (Tracked& t : _units)
                    if (t.guid == guid)
                        t.clock = CopyClock(_rule);
            }

            Creature* Owner() const
            {
                return _map && !_owner.IsEmpty() ? _map->GetCreature(_owner) : nullptr;
            }

            void Log(char const* what, std::string const& detail) const
            {
                DungeonKit::LogMechanic(GnomereganRework::kLogDungeon, _logKey.c_str(), "duplicator",
                    Acore::StringFormat("{} {} heroic={}", what, detail, _heroic ? 1 : 0));
            }

            // Rule 15: a cast bar checks its SpellCastResult and retries in 1 s on a refusal.
            void Start(Creature* unit, Tracked& t)
            {
                unit->StopMoving();
                SpellCastResult const result = unit->CastSpell(unit, _spec.barSpellId, false);
                if (result != SPELL_CAST_OK)
                {
                    OnCastRefused(t.clock);
                    Log("refused", Acore::StringFormat("unit={} result={}", unit->GetGUID().GetCounter(),
                        uint32(result)));
                    return;
                }
                OnCastStarted(t.clock);
                t.lastRemainingMs = std::int32_t(_spec.castMs);
                t.sinceSeenMs = 0;
                if (_spec.emoteGroup && unit->IsAIEnabled && unit->AI())
                    unit->AI()->Talk(*_spec.emoteGroup);
                Log("start", Acore::StringFormat("unit={} life={} cast={} alive={}", unit->GetGUID().GetCounter(),
                    t.clock.lifeMs, _spec.castMs, Alive()));
            }

            // The copy (ruling 51): the same entry, beside the source, at the source's current health.
            Creature* Copy(Creature* owner, Creature* source)
            {
                Position const at = source->GetNearPosition(Tune::kCopyOffsetYd, frand(0.f, kTwoPi));
                Position spot(at.GetPositionX(), at.GetPositionY(), source->GetPositionZ(), source->GetOrientation());
                TempSummon* copy = owner->SummonCreature(source->GetEntry(), spot, TEMPSUMMON_CORPSE_TIMED_DESPAWN,
                    Tune::kBugCorpseMs);
                if (!copy)
                {
                    Log("copy-refused", Acore::StringFormat("source={}", source->GetGUID().GetCounter()));
                    return nullptr;
                }
                copy->SetHealth(std::min(source->GetHealth(), copy->GetMaxHealth()));
                ++_copies;
                Log("copy", Acore::StringFormat("source={} copy={} health={} alive={}", source->GetGUID().GetCounter(),
                    copy->GetGUID().GetCounter(), copy->GetHealth(), Alive() + 1));
                return copy;
            }

            ObjectGuid _owner;
            Map* _map = nullptr;
            std::string _logKey;
            bool _heroic = false;
            DuplicatorSpec _spec;
            DupRule _rule;
            std::vector<Tracked> _units;
            std::vector<ObjectGuid> _pendingTrack;
            std::vector<ObjectGuid> _pendingForget;
            bool _inUpdate = false;
            bool _barMarks = false;
            uint32 _copies = 0;
        };
    }

    std::unique_ptr<Duplicator> MakeDuplicator(MachineOwner const& owner, DuplicatorSpec spec)
    {
        return std::make_unique<DuplicatorMachine>(owner, std::move(spec));
    }
}
