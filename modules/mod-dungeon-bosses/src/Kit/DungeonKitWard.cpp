/*
 * mod-dungeon-bosses, the shared dungeon kit: Ward of the Living (DungeonKitWard.h, Scarlet Monastery WP-KT-SM).
 */

#include "DungeonKitWard.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "ObjectAccessor.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"
#include <algorithm>
#include <list>
#include <utility>

namespace DungeonKit
{
    void WardOfTheLiving::Start(Creature* boss, WardSpec spec)
    {
        Stop(boss);
        _spec = std::move(spec);
        _rule = WardRule{ _spec.pctPerAdd, _spec.capPct };
        _active = boss != nullptr;
        if (_active)
            Count(boss);
    }

    void WardOfTheLiving::Link(Creature* boss, Creature* add)
    {
        if (!_active || !boss || !add)
            return;
        ObjectGuid const guid = add->GetGUID();
        if (std::find(_manual.begin(), _manual.end(), guid) == _manual.end())
            _manual.push_back(guid);
        Count(boss);
    }

    void WardOfTheLiving::Update(Creature* boss, uint32 diff)
    {
        if (!_active || !boss)
            return;
        _checkMs += diff;
        if (_checkMs < _spec.checkMs)
            return;
        _checkMs = 0;
        Count(boss);
    }

    void WardOfTheLiving::Count(Creature* boss)
    {
        std::vector<ObjectGuid> living;
        auto consider = [&living, boss](Creature* add)
        {
            if (add && add != boss && add->IsAlive() && add->IsInWorld() && add->IsInMap(boss)
                && std::find(living.begin(), living.end(), add->GetGUID()) == living.end())
                living.push_back(add->GetGUID());
        };
        std::erase_if(_manual, [boss](ObjectGuid const& g)
        {
            Creature* add = ObjectAccessor::GetCreature(*boss, g);
            return !add || !add->IsAlive();
        });
        for (ObjectGuid const& g : _manual)
            consider(ObjectAccessor::GetCreature(*boss, g));
        for (uint32 entry : _spec.addEntries)
        {
            std::list<Creature*> found;
            GetCreatureListWithEntryInGrid(found, boss, entry, _spec.searchYd);
            for (Creature* add : found)
                consider(add);
        }

        for (ObjectGuid const& g : _linked)
            if (std::find(living.begin(), living.end(), g) == living.end() && _spec.onUnlink)
                _spec.onUnlink(boss, g);
        for (ObjectGuid const& g : living)
            if (std::find(_linked.begin(), _linked.end(), g) == _linked.end() && _spec.onLink)
                if (Creature* add = ObjectAccessor::GetCreature(*boss, g))
                    _spec.onLink(boss, add);
        _linked = std::move(living);

        uint32 const stacks = _rule.Stacks(Living());
        // The worn count, not the last one set: a dispel or a purge of the ward is put back at the next check.
        uint32 const have = _spec.aura ? Stacks(boss, _spec.aura) : _stacks;
        if (stacks == have && stacks == _stacks)
            return;
        if (_spec.aura && stacks != have)
            AddStacks(boss, _spec.aura, static_cast<int32>(stacks) - static_cast<int32>(have), boss,
                std::max<uint32>(1, _rule.Stacks(1000)));
        if (stacks == _stacks)
            return;
        LogMechanic(_spec.dungeon, _spec.boss, "ward",
            Acore::StringFormat("living={} stacks={}->{} reduction={:.0f}%", Living(), _stacks, stacks,
                ReductionPct()));
        _stacks = stacks;
    }

    void WardOfTheLiving::Stop(Creature* boss)
    {
        if (boss)
        {
            if (_spec.onUnlink)
                for (ObjectGuid const& g : _linked)
                    _spec.onUnlink(boss, g);
            if (_spec.aura && _stacks)
                boss->RemoveAurasDueToSpell(_spec.aura);
        }
        _manual.clear();
        _linked.clear();
        _stacks = 0;
        _checkMs = 0;
        _active = false;
    }

    void WardOfTheLiving::Mitigate(uint32& damage) const
    {
        if (_active && !_spec.auraCarriesReduction)
            damage = _rule.Scale(damage, Living());
    }
}
