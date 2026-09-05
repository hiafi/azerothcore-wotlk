--
-- Phase 5 prep (Bucket 1): item_slot_mult had no row at all for Ranged bows/
-- guns (invtype 15), Thrown (25), or Relic (28) -- 70 items were silently
-- unconvertible. Added at the same 0.5625 "small slot" tier as the existing
-- Ranged-right/off-hand/trinket-tier entries; per-item role-based budget_mult
-- (see the Bucket 1 conversion migration) corrects individual deviation from
-- there, same treatment as the other weapon-tier invtypes.
--

DELETE FROM `item_slot_mult` WHERE `inv_type` IN (15, 25, 28);
INSERT INTO `item_slot_mult` (`inv_type`, `mult`) VALUES
(15, 0.5625),
(25, 0.5625),
(28, 0.5625);
