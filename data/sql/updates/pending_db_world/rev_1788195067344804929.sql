-- Cooldown Reduction stat rework (see Player::AddSpellAndCategoryCooldowns, Player.cpp): the
-- stat is now applied as a "cooldown haste" (rec / (1 + CDR%/100)) instead of a flat percentage
-- cut (rec * (1 - CDR%/100)), so 100% CDR only halves a cooldown, 200% takes it to a third, and
-- so on - no finite amount of rating can reduce a cooldown to zero. To keep that curve feeling
-- worthwhile per point (diminishing returns bite immediately once you're doing division instead
-- of subtraction), CR_COOLDOWN_REDUCTION's `gtcombatratings_dbc` curve (id 22, rows 2200-2299) is
-- retuned from x1.0 of Crit Rating (CR_CRIT_SPELL) down to x0.5 - twice the percent per point,
-- same multiplier CR_PROC_CHANCE already uses (see rev_1787946043819236756.sql) - which is why
-- these values are identical to that migration's Proc Chance block (ids 1100-1199), just shifted
-- to the Cooldown Reduction id range.
-- `gtoctclasscombatratingscalar_dbc` needs no change: id 22's per-class scalar is already a flat
-- `1` for every class, same as every other custom stat slot.
-- Remember to also regenerate the client-facing patch-Y.mpq via
-- apps/dbc-tools/patch_gt_tables.py once this is applied (its tooltip math reads a copy of these
-- same two DBCs - see that script's docstring for why).
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2200;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2201;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2202;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2203;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2204;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2205;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2206;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2207;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2208;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2209;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.403846 WHERE `ID` = 2210;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.53846 WHERE `ID` = 2211;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.673075 WHERE `ID` = 2212;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.807695 WHERE `ID` = 2213;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.942305 WHERE `ID` = 2214;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2215;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.21154 WHERE `ID` = 2216;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.34615 WHERE `ID` = 2217;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.48077 WHERE `ID` = 2218;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.61539 WHERE `ID` = 2219;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.75 WHERE `ID` = 2220;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.88461 WHERE `ID` = 2221;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.01923 WHERE `ID` = 2222;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.15385 WHERE `ID` = 2223;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.28846 WHERE `ID` = 2224;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.42307 WHERE `ID` = 2225;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.55769 WHERE `ID` = 2226;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.69231 WHERE `ID` = 2227;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.82693 WHERE `ID` = 2228;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.96154 WHERE `ID` = 2229;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.09615 WHERE `ID` = 2230;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.23077 WHERE `ID` = 2231;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.36538 WHERE `ID` = 2232;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.5 WHERE `ID` = 2233;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.63462 WHERE `ID` = 2234;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.76923 WHERE `ID` = 2235;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.90385 WHERE `ID` = 2236;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.03846 WHERE `ID` = 2237;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.17307 WHERE `ID` = 2238;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.30769 WHERE `ID` = 2239;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.44231 WHERE `ID` = 2240;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.57693 WHERE `ID` = 2241;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.71154 WHERE `ID` = 2242;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.84616 WHERE `ID` = 2243;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.98077 WHERE `ID` = 2244;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.1154 WHERE `ID` = 2245;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.25 WHERE `ID` = 2246;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.3846 WHERE `ID` = 2247;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.51925 WHERE `ID` = 2248;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.65385 WHERE `ID` = 2249;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.78845 WHERE `ID` = 2250;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.9231 WHERE `ID` = 2251;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.0577 WHERE `ID` = 2252;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.1923 WHERE `ID` = 2253;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.3269 WHERE `ID` = 2254;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.46155 WHERE `ID` = 2255;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.59615 WHERE `ID` = 2256;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.73075 WHERE `ID` = 2257;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.8654 WHERE `ID` = 2258;
UPDATE `gtcombatratings_dbc` SET `Data` = 7 WHERE `ID` = 2259;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.2658 WHERE `ID` = 2260;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.55265 WHERE `ID` = 2261;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.863 WHERE `ID` = 2262;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.2 WHERE `ID` = 2263;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.56715 WHERE `ID` = 2264;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.96875 WHERE `ID` = 2265;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.40985 WHERE `ID` = 2266;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.89655 WHERE `ID` = 2267;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.4363 WHERE `ID` = 2268;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.0384 WHERE `ID` = 2269;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.8768 WHERE `ID` = 2270;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.779 WHERE `ID` = 2271;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.7495 WHERE `ID` = 2272;
UPDATE `gtcombatratings_dbc` SET `Data` = 14.7939 WHERE `ID` = 2273;
UPDATE `gtcombatratings_dbc` SET `Data` = 15.9175 WHERE `ID` = 2274;
UPDATE `gtcombatratings_dbc` SET `Data` = 17.1264 WHERE `ID` = 2275;
UPDATE `gtcombatratings_dbc` SET `Data` = 18.4273 WHERE `ID` = 2276;
UPDATE `gtcombatratings_dbc` SET `Data` = 19.8268 WHERE `ID` = 2277;
UPDATE `gtcombatratings_dbc` SET `Data` = 21.3327 WHERE `ID` = 2278;
UPDATE `gtcombatratings_dbc` SET `Data` = 22.953 WHERE `ID` = 2279;
UPDATE `gtcombatratings_dbc` SET `Data` = 24.6963 WHERE `ID` = 2280;
UPDATE `gtcombatratings_dbc` SET `Data` = 26.5721 WHERE `ID` = 2281;
UPDATE `gtcombatratings_dbc` SET `Data` = 28.5903 WHERE `ID` = 2282;
UPDATE `gtcombatratings_dbc` SET `Data` = 30.7618 WHERE `ID` = 2283;
UPDATE `gtcombatratings_dbc` SET `Data` = 33.0982 WHERE `ID` = 2284;
UPDATE `gtcombatratings_dbc` SET `Data` = 35.6121 WHERE `ID` = 2285;
UPDATE `gtcombatratings_dbc` SET `Data` = 38.3169 WHERE `ID` = 2286;
UPDATE `gtcombatratings_dbc` SET `Data` = 41.2272 WHERE `ID` = 2287;
UPDATE `gtcombatratings_dbc` SET `Data` = 44.3585 WHERE `ID` = 2288;
UPDATE `gtcombatratings_dbc` SET `Data` = 47.7276 WHERE `ID` = 2289;
UPDATE `gtcombatratings_dbc` SET `Data` = 51.3525 WHERE `ID` = 2290;
UPDATE `gtcombatratings_dbc` SET `Data` = 55.253 WHERE `ID` = 2291;
UPDATE `gtcombatratings_dbc` SET `Data` = 59.4495 WHERE `ID` = 2292;
UPDATE `gtcombatratings_dbc` SET `Data` = 63.965 WHERE `ID` = 2293;
UPDATE `gtcombatratings_dbc` SET `Data` = 68.8235 WHERE `ID` = 2294;
UPDATE `gtcombatratings_dbc` SET `Data` = 74.0505 WHERE `ID` = 2295;
UPDATE `gtcombatratings_dbc` SET `Data` = 79.675 WHERE `ID` = 2296;
UPDATE `gtcombatratings_dbc` SET `Data` = 85.7265 WHERE `ID` = 2297;
UPDATE `gtcombatratings_dbc` SET `Data` = 92.2375 WHERE `ID` = 2298;
UPDATE `gtcombatratings_dbc` SET `Data` = 99.243 WHERE `ID` = 2299;
