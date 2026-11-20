/*
 * mod-dungeon-bosses, the shared dungeon kit: a damage meter over a sliding window (DungeonKitLedger.h, Blackrock
 * Depths WP-KT-D2).
 */

#include "DungeonKitLedger.h"
#include "GameTime.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Unit.h"
#include <algorithm>

namespace DungeonKit
{
    namespace
    {
        uint64 NowMs()
        {
            return static_cast<uint64>(GameTime::GetGameTimeMS().count());
        }
    }

    DamageLedger::DamageLedger(Milliseconds window)
        : _tally(static_cast<uint32>(std::max<int64>(1, window.count())))
    {
    }

    bool DamageLedger::Record(Unit const* attacker, uint32 damage)
    {
        if (!attacker || !damage)
            return false;
        Player* player = attacker->GetCharmerOrOwnerPlayerOrPlayerItself();
        if (!player)
            return false;
        Record(player->GetGUID(), damage);
        return true;
    }

    void DamageLedger::Record(ObjectGuid player, uint32 damage)
    {
        if (player)
            _tally.Record(player.GetRawValue(), damage, NowMs());
    }

    Player* DamageLedger::Top(WorldObject const* ref, std::initializer_list<ObjectGuid> exclude,
        std::function<bool(Player*)> const& eligible)
    {
        return Top(ref, std::vector<ObjectGuid>(exclude), eligible);
    }

    Player* DamageLedger::Top(WorldObject const* ref, std::vector<ObjectGuid> const& exclude,
        std::function<bool(Player*)> const& eligible)
    {
        if (!ref)
            return nullptr;
        Player* found = nullptr;
        _tally.TopIf(NowMs(), [&](uint64 raw)
        {
            ObjectGuid const guid(raw);
            if (std::find(exclude.begin(), exclude.end(), guid) != exclude.end())
                return false;
            Player* player = ObjectAccessor::GetPlayer(*ref, guid);
            if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInMap(ref))
                return false;
            if (eligible && !eligible(player))
                return false;
            found = player;
            return true;
        });
        return found;
    }

    uint64 DamageLedger::Total(ObjectGuid player)
    {
        return _tally.Total(player.GetRawValue(), NowMs());
    }

    std::vector<std::pair<ObjectGuid, uint64>> DamageLedger::Ranking()
    {
        std::vector<std::pair<ObjectGuid, uint64>> out;
        for (TallyStanding const& s : _tally.Ranking(NowMs()))
            out.emplace_back(ObjectGuid(s.who), s.total);
        return out;
    }
}
