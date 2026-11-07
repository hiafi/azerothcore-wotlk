# mod-dungeon-bosses: build-time checks (included inline by modules/CMakeLists.txt after the module targets exist; the
# include runs for a disabled module too, so every check is skipped unless this module is enabled).
#
# Hard dependency: the boss scripts include mod-boss-mechanics' BossMechanics.h through the modules target's
# PUBLIC_INCLUDES, so mod-boss-mechanics must be present and enabled. Without it the build would fail later with a
# missing-header error deep in a boss file; stop at configure time with a clear message instead.
if ("mod-dungeon-bosses" IN_LIST MODULE_LIST__)
  if (NOT EXISTS "${CMAKE_SOURCE_DIR}/modules/mod-boss-mechanics/src/BossMechanics.h")
    message(FATAL_ERROR
      "mod-dungeon-bosses needs mod-boss-mechanics (modules/mod-boss-mechanics/src/BossMechanics.h not found). "
      "Clone it into modules/ or disable mod-dungeon-bosses with -DDISABLED_AC_MODULES=\"mod-dungeon-bosses\".")
  endif()
  # The Deadmines kit calls Mechanic::RefFlat (mod-boss-mechanics feat/pilot-support, cab8a12). An older checkout has
  # the header but not the function, which would fail late with a compile error in DeadminesKit.cpp.
  file(STRINGS "${CMAKE_SOURCE_DIR}/modules/mod-boss-mechanics/src/BossMechanics.h" _dbRefFlat
    REGEX "uint32 RefFlat\\(")
  if (NOT _dbRefFlat)
    message(FATAL_ERROR
      "mod-dungeon-bosses needs a mod-boss-mechanics with Mechanic::RefFlat (BossMechanics.h has none). Update "
      "modules/mod-boss-mechanics (merge its feat/pilot-support), or disable mod-dungeon-bosses.")
  endif()
  unset(_dbRefFlat)
  if (NOT "mod-boss-mechanics" IN_LIST MODULE_LIST__)
    message(FATAL_ERROR
      "mod-dungeon-bosses needs mod-boss-mechanics enabled, but it is disabled (DISABLED_AC_MODULES or "
      "MODULE_MOD_BOSS_MECHANICS). Enable it, or disable mod-dungeon-bosses too.")
  endif()
endif()
