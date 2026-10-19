# Custom spells: engine and client gotchas

Rules for authoring or editing a custom spell, talent or proc (dbc-tools DSL or SpellScript) that a lint, test or
playtest only caught after a deploy. Each cost a fix cycle in a past rework. Check the list before writing a spell;
`docs/bugs-and-fixes.md` has the full write-ups.

## Cast times and the cast bar (ranged-weapon shots)

- `SpellInfo::CalcCastTime` adds **+500 ms** to every spell with `SPELL_ATTR0_USES_RANGED_SLOT` (non-autorepeat)
  **before** spell mods. The client adds it **after** mods. So:
  - DBC cast time = the cast you want − 500 ms. The tooltip then shows the shorter number; say so in the playtest guide.
  - An **instant** ranged shot uses `CastingTimeIndex 18` (−1,000,000 ms), as every stock instant shot does. Index 0 or
    1 gives a hidden 0.5 s cast.
  - A "next shot is instant" modifier on a ranged cast spell is a **flat** `SPELLMOD_CASTING_TIME` ≤ −(DBC cast + 500)
    (stored `base_points` one lower). A −100% percent mod leaves 0.5 s on the client.
  - A potency effect on a spell whose DBC cast was cut sets `time_basis_ms` to the **live** cast. Otherwise the potency
    system scales the base and coefficient down with the shorter DBC value (Steady Shot lost a third once).
- The client hides the cast bar on ranged-slot spells unless they carry `SPELL_ATTR4_FORCE_DISPLAY_CASTBAR`
  (`AttributesEx4 0x08000000`). Add `SPELL_ATTR0_TRACK_TARGET_IN_CAST_PLAYER_ONLY` (`0x00400000`) too, so the caster
  faces the target.
- The DSL's default for an instant is `CastingTimeIndex 0`, which has no row in the client's SpellCastTimes.dbc. Stock
  non-ranged instants use 1. Harmless so far, but use 1 when touching a row anyway.
- Ranged attack speed (`SPELL_AURA_MOD_RANGED_HASTE`) speeds up ranged cast times and the hasted GCD. Check class
  passives for hidden haste. Hunters had 15% from Advantaged State 34082 until the rework removed it.

## Auras the player must see

- Passive auras are never sent to the client (`Aura::CanBeSentToClient`), so a buff meant to show is **not passive**.
- `AttributesEx7 0x10000000` files a buff into the Consolidated Buffs box; clear it on anything the player should
  read at a glance.
- A purely visual marker (e.g. "your proc fired") is its own non-passive `SPELL_AURA_DUMMY` spell, applied and removed
  with the real effect.
- Aura text `$s1` / `$n` placeholders didn't render correctly in-game; keep aura texts number-free unless verified.

## Triggered casts, procs and scoping

- `EquippedItemClass 0` means "needs an item of class 0": every triggered cast fails silently with
  `SPELL_FAILED_EQUIPPED_ITEM_CLASS`. Use −1 (lint `check_custom_equipped_item_class`).
- A custom SpellMod on a spell with `SpellClassSet 0` applies to **every** spell, other classes' and pets' included
  (lint `check_family_zero_spellmods`).
- The 3.3.5 client applies SpellMod packets by bit to its own class family only; cross-class spells never see a
  client-side mod.
- A proc that must fire from a `TRIGGERED_FULL_MASK` cast needs `spell_proc.AttributesMask` 0x2. CAST plus HIT phase
  rows need a once-per-cast guard.
- A spell with a `ProcTypeMask` but no `spell_proc` row gets a **default** proc entry built from its own family and
  SpellMod masks (`SpellMgr.cpp`). Rescoping the masks silently changes what procs it.
- `SpellInfoCorrections.cpp` overwrites some stock masks and values at load. No DSL check sees it, so grep it for
  every stock spell you rework (Marked for Death's mod landed on the wrong spells this way).
- Triggered spells still run CheckCast's caster-to-target line-of-sight check. A splash or bounce that sets
  `AttributesEx2 0x4` (ignore LoS) must filter LoS itself, from the primary target.

- `Player::HasSpell` is **false for passive talent ranks**: `_addTalentAurasAndSpells` only casts their aura and
  never adds them to the spell map. Check a passive talent with `HasAura(rank)` (or `HasTalent(rank, spec)`). Deadly
  Focus's Raptor Strike mana and Trap Mastery's snake sting both silently did nothing this way.

## Cooldowns and the GCD

- Cooldown Haste corrects qualifying cooldowns (base ≥ 30 s) by resending the cooldown. The client's clear drops the
  GCD it predicted for that cast, so the correction is deferred past the spell's GCD (`Player.cpp`, CDH-GCD-FIX). Any
  new code that changes the cooldown of the spell whose GCD is running hides the GCD sweep the same way.
- `.cheat cooldown on` skips the GCD for everything; rule it out first when a GCD looks missing.

## Character state while testing

- `.maxskill` leaves crit stale until a relog; the live config uses `AlwaysMaxSkillForLevel = 1` instead.
- A character showing another class's talents or spells: check for orphan rows under its guid (the DPS sim once wrote
  them; `.agents/plans/dpssim-orphan-fix/`).
