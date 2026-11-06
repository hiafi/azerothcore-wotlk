// Minimal test harness for the standalone mod-dungeon-bosses tests (no gtest; host compilers only).
#ifndef MOD_DUNGEON_BOSSES_TEST_CHECK_H
#define MOD_DUNGEON_BOSSES_TEST_CHECK_H

#include <cstdio>

static int g_checks = 0;
static int g_failures = 0;

#define CHECK(cond) \
    do \
    { \
        ++g_checks; \
        if (!(cond)) \
        { \
            ++g_failures; \
            std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        } \
    } while (0)

inline int Report(char const* name)
{
    std::printf("%s: %d checks, %d failures\n", name, g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}

#endif
