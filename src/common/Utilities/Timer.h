/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef ACORE_TIMER_H
#define ACORE_TIMER_H

#include "Common.h"
#include "Duration.h"
#include <atomic>

enum class TimeFormat : uint8
{
    FullText,  // 1 Days 2 Hours 3 Minutes 4 Seconds 5 Milliseconds
    ShortText, // 1d 2h 3m 4s 5ms
    Numeric    // 1:2:3:4:5
};

enum class TimeOutput : uint8
{
    Days,         // 1d
    Hours,        // 1d 2h
    Minutes,      // 1d 2h 3m
    Seconds,      // 1d 2h 3m 4s
    Milliseconds, // 1d 2h 3m 4s 5ms
    Microseconds  // 1d 2h 3m 4s 5ms 6us
};

namespace Acore::Time
{
    template <class T>
    AC_COMMON_API uint32 TimeStringTo(std::string_view timeString);

    template<class T>
    AC_COMMON_API std::string ToTimeString(uint64 durationTime, TimeOutput timeOutput = TimeOutput::Seconds, TimeFormat timeFormat = TimeFormat::ShortText);

    template<class T>
    AC_COMMON_API std::string ToTimeString(std::string_view durationTime, TimeOutput timeOutput = TimeOutput::Seconds, TimeFormat timeFormat = TimeFormat::ShortText);

    AC_COMMON_API std::string ToTimeString(Microseconds durationTime, TimeOutput timeOutput = TimeOutput::Seconds, TimeFormat timeFormat = TimeFormat::ShortText);

    AC_COMMON_API time_t LocalTimeToUTCTime(time_t time);
    AC_COMMON_API time_t GetLocalHourTimestamp(time_t time, uint8 hour, bool onlyAfterTime = true);
    AC_COMMON_API std::tm TimeBreakdown(time_t t = 0);
    AC_COMMON_API std::string TimeToTimestampStr(Seconds time = 0s, std::string_view fmt = {});
    AC_COMMON_API std::string TimeToHumanReadable(Seconds time = 0s, std::string_view fmt = {});

    AC_COMMON_API time_t GetNextTimeWithDayAndHour(int8 dayOfWeek, int8 hour); // int8 dayOfWeek: 0 (sunday) to 6 (saturday)
    AC_COMMON_API time_t GetNextTimeWithMonthAndHour(int8 month, int8 hour); // int8 month: 0 (january) to 11 (december)

    AC_COMMON_API uint32 GetSeconds(Seconds time = 0s);      // seconds after the minute - [0, 60]
    AC_COMMON_API uint32 GetMinutes(Seconds time = 0s);      // minutes after the hour - [0, 59]
    AC_COMMON_API uint32 GetHours(Seconds time = 0s);        // hours since midnight - [0, 23]
    AC_COMMON_API uint32 GetDayInWeek(Seconds time = 0s);    // days since Sunday - [0, 6]
    AC_COMMON_API uint32 GetDayInMonth(Seconds time = 0s);   // day of the month - [1, 31]
    AC_COMMON_API uint32 GetDayInYear(Seconds time = 0s);    // days since January 1 - [0, 365]
    AC_COMMON_API uint32 GetMonth(Seconds time = 0s);        // months since January - [0, 11]
    AC_COMMON_API uint32 GetYear(Seconds time = 0s);         // years since 1900
}

AC_COMMON_API struct tm* localtime_r(time_t const* time, struct tm* result);

inline TimePoint GetApplicationStartTime()
{
    using namespace std::chrono;

    static const TimePoint ApplicationStartTime = steady_clock::now();

    return ApplicationStartTime;
}

namespace Acore::Time
{
    // Sim-clock override for modules/mod-dpssim (see .agents/plans/dps-sim-module/
    // dps-sim-module.PLAN.md, "Critical finding: getMSTime() is a second, unfakeable wall-clock
    // dependency"). Normally GetTimeMS()/getMSTime() read steady_clock::now() live, on every
    // call, with no injection point - fine for a real-time server, fatal for a sim daemon that
    // drives Map::Update() with its own (possibly accelerated) diff instead of running
    // World::Update() at real pace: spell cooldown/GCD *storage* goes through
    // GameTime::GetGameTimeMS() (itself refreshed from GetTimeMS() below, see GameTime.cpp), but
    // *expiry checks* read getMSTime() directly (Player::HasSpellCooldown and friends) - without
    // this override the two decorrelate within seconds of an accelerated sim run and every
    // cooldown/the GCD reads as already-expired. Inactive (`< 0`) by default: zero behavior
    // change for the normal server. Only the sim daemon's own tick loop should ever call
    // SetSimClockOverride(); nothing else in the codebase should touch this.
    inline std::atomic<int64> SimClockOverrideMs{-1};

    inline void SetSimClockOverride(Milliseconds ms)
    {
        SimClockOverrideMs.store(ms.count(), std::memory_order_relaxed);
    }

    inline void ClearSimClockOverride()
    {
        SimClockOverrideMs.store(-1, std::memory_order_relaxed);
    }

    inline bool IsSimClockOverrideActive()
    {
        return SimClockOverrideMs.load(std::memory_order_relaxed) >= 0;
    }
}

inline Milliseconds GetTimeMS()
{
    using namespace std::chrono;

    if (int64 const simOverride = Acore::Time::SimClockOverrideMs.load(std::memory_order_relaxed); simOverride >= 0)
    {
        return Milliseconds(simOverride);
    }

    return duration_cast<milliseconds>(steady_clock::now() - GetApplicationStartTime());
}

inline Milliseconds GetMSTimeDiff(Milliseconds oldMSTime, Milliseconds newMSTime)
{
    if (oldMSTime > newMSTime)
    {
        return oldMSTime - newMSTime;
    }
    else
    {
        return newMSTime - oldMSTime;
    }
}

inline uint32 getMSTime()
{
    // Delegates to GetTimeMS() (rather than reading steady_clock::now() independently, as this
    // used to) so the two can never drift apart - and so the sim-clock override above covers
    // both with one patch.
    return uint32(GetTimeMS().count());
}

inline uint32 getMSTimeDiff(uint32 oldMSTime, uint32 newMSTime)
{
    // getMSTime() have limited data range and this is case when it overflow in this tick
    if (oldMSTime > newMSTime)
    {
        return (0xFFFFFFFF - oldMSTime) + newMSTime;
    }
    else
    {
        return newMSTime - oldMSTime;
    }
}

inline uint32 getMSTimeDiff(uint32 oldMSTime, TimePoint newTime)
{
    using namespace std::chrono;

    uint32 newMSTime = uint32(duration_cast<milliseconds>(newTime - GetApplicationStartTime()).count());
    return getMSTimeDiff(oldMSTime, newMSTime);
}

inline uint32 GetMSTimeDiffToNow(uint32 oldMSTime)
{
    return getMSTimeDiff(oldMSTime, getMSTime());
}

inline Milliseconds GetMSTimeDiffToNow(Milliseconds oldMSTime)
{
    return GetMSTimeDiff(oldMSTime, GetTimeMS());
}

inline Seconds GetEpochTime()
{
    using namespace std::chrono;
    return duration_cast<Seconds>(system_clock::now().time_since_epoch());
}

struct IntervalTimer
{
public:
    IntervalTimer() = default;

    void Update(time_t diff)
    {
        _current += diff;
        if (_current < 0)
        {
            _current = 0;
        }
    }

    bool Passed()
    {
        return _current >= _interval;
    }

    void Reset()
    {
        if (_current >= _interval)
        {
            _current %= _interval;
        }
    }

    void SetCurrent(time_t current)
    {
        _current = current;
    }

    void SetInterval(time_t interval)
    {
        _interval = interval;
    }

    [[nodiscard]] time_t GetInterval() const
    {
        return _interval;
    }

    [[nodiscard]] time_t GetCurrent() const
    {
        return _current;
    }

private:
    time_t _interval{0};
    time_t _current{0};
};

struct TimeTracker
{
public:
    TimeTracker(time_t expiry)
        : i_expiryTime(expiry)
    {
    }

    void Update(time_t diff)
    {
        i_expiryTime -= diff;
    }

    [[nodiscard]] bool Passed() const
    {
        return i_expiryTime <= 0;
    }

    void Reset(time_t interval)
    {
        i_expiryTime = interval;
    }

    [[nodiscard]] time_t GetExpiry() const
    {
        return i_expiryTime;
    }

private:
    time_t i_expiryTime;
};

struct TimeTrackerSmall
{
public:
    TimeTrackerSmall(int32 expiry = 0)
        : i_expiryTime(expiry)
    {
    }

    void Update(int32 diff)
    {
        i_expiryTime -= diff;
    }

    [[nodiscard]] bool Passed() const
    {
        return i_expiryTime <= 0;
    }

    void Reset(int32 interval)
    {
        i_expiryTime = interval;
    }

    [[nodiscard]] int32 GetExpiry() const
    {
        return i_expiryTime;
    }

private:
    int32 i_expiryTime;
};

struct PeriodicTimer
{
public:
    PeriodicTimer(int32 period, int32 start_time)
        : i_period(period), i_expireTime(start_time)
    {
    }

    bool Update(const uint32 diff)
    {
        if ((i_expireTime -= diff) > 0)
        {
            return false;
        }

        i_expireTime += i_period > int32(diff) ? i_period : diff;
        return true;
    }

    void SetPeriodic(int32 period, int32 start_time)
    {
        i_expireTime = start_time;
        i_period = period;
    }

    // Tracker interface
    void TUpdate(int32 diff) { i_expireTime -= diff; }
    [[nodiscard]] bool TPassed() const { return i_expireTime <= 0; }
    void TReset(int32 diff, int32 period)  { i_expireTime += period > diff ? period : diff; }

private:
    int32 i_period;
    int32 i_expireTime;
};

#endif
