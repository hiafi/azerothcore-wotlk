-- Item variants IV0b: keep every existing itemized shield at its stock armor.
--
-- Once item_armor_curve has shield rows (previous file), ItemBudget.cpp materializes armor for every shield that has
-- an item_itemization row (175 of the 686 shields). The curve fits stock to within a few percent (mean 1.9%, worst
-- -14% on WotLK Rare shields) and gives the 5 stock shields with armor 0 a nonzero value, so this file pins each
-- affected row with an armor_delta of (stock armor - ArmorDamageModifier) - baseline_armor. The in-memory armor stays
-- exactly what item_template stores. The curve then only governs items that carry a delta of 0: the minted ladder
-- tiers and any shield authored from now on. Delete this file (before it is imported) to let the curve retune the
-- existing shields instead.
--
UPDATE `item_itemization` SET `armor_delta` = 53 WHERE `entry` = 1169; -- Blackskull Shield
UPDATE `item_itemization` SET `armor_delta` = 28 WHERE `entry` = 1203; -- Aegis of Stormwind
UPDATE `item_itemization` SET `armor_delta` = 42 WHERE `entry` = 1204; -- The Green Tower
UPDATE `item_itemization` SET `armor_delta` = 65 WHERE `entry` = 1979; -- Wall of the Dead
UPDATE `item_itemization` SET `armor_delta` = 33 WHERE `entry` = 2040; -- Troll Protector
UPDATE `item_itemization` SET `armor_delta` = 111 WHERE `entry` = 4507; -- Pit Fighter's Shield
UPDATE `item_itemization` SET `armor_delta` = 27 WHERE `entry` = 4975; -- Vigilant Buckler
UPDATE `item_itemization` SET `armor_delta` = 14 WHERE `entry` = 5443; -- Gold-plated Buckler
UPDATE `item_itemization` SET `armor_delta` = 24 WHERE `entry` = 6320; -- Commander's Crest
UPDATE `item_itemization` SET `armor_delta` = 18 WHERE `entry` = 6630; -- Seedcloud Buckler
UPDATE `item_itemization` SET `armor_delta` = 28 WHERE `entry` = 6694; -- Heart of Agamaggan
UPDATE `item_itemization` SET `armor_delta` = 27 WHERE `entry` = 6725; -- Marbled Buckler
UPDATE `item_itemization` SET `armor_delta` = 25 WHERE `entry` = 7002; -- Arctic Buckler
UPDATE `item_itemization` SET `armor_delta` = 22 WHERE `entry` = 7726; -- Aegis of the Scarlet Commander
UPDATE `item_itemization` SET `armor_delta` = 19 WHERE `entry` = 7787; -- Resplendent Guardian
UPDATE `item_itemization` SET `armor_delta` = 15 WHERE `entry` = 9403; -- Battered Viking Shield
UPDATE `item_itemization` SET `armor_delta` = 31 WHERE `entry` = 9458; -- Thermaplugg's Central Core
UPDATE `item_itemization` SET `armor_delta` = 29 WHERE `entry` = 10686; -- Aegis of Battle
UPDATE `item_itemization` SET `armor_delta` = 111 WHERE `entry` = 10767; -- Savage Boar's Guard
UPDATE `item_itemization` SET `armor_delta` = 32 WHERE `entry` = 10835; -- Crest of Supremacy
UPDATE `item_itemization` SET `armor_delta` = 24 WHERE `entry` = 11631; -- Stoneshell Guard
UPDATE `item_itemization` SET `armor_delta` = 17 WHERE `entry` = 12602; -- Draconian Deflector
UPDATE `item_itemization` SET `armor_delta` = 64 WHERE `entry` = 12997; -- Redbeard Crest
UPDATE `item_itemization` SET `armor_delta` = 19 WHERE `entry` = 13079; -- Shield of Thorsen
UPDATE `item_itemization` SET `armor_delta` = 24 WHERE `entry` = 13081; -- Skullance Shield
UPDATE `item_itemization` SET `armor_delta` = -2 WHERE `entry` = 13082; -- Mountainside Buckler
UPDATE `item_itemization` SET `armor_delta` = 12 WHERE `entry` = 13083; -- Garrett Family Crest
UPDATE `item_itemization` SET `armor_delta` = 21 WHERE `entry` = 13205; -- Rhombeard Protector
UPDATE `item_itemization` SET `armor_delta` = 14 WHERE `entry` = 13245; -- Kresh's Back
UPDATE `item_itemization` SET `armor_delta` = 17 WHERE `entry` = 14002; -- Darrowshire Strongguard
UPDATE `item_itemization` SET `armor_delta` = 12 WHERE `entry` = 14528; -- Rattlecage Buckler
UPDATE `item_itemization` SET `armor_delta` = 12 WHERE `entry` = 16998; -- Sacred Protector
UPDATE `item_itemization` SET `armor_delta` = 36 WHERE `entry` = 17718; -- Gizlock's Hypertech Buckler
UPDATE `item_itemization` SET `armor_delta` = -1549 WHERE `entry` = 18303; -- Nimble Buckler
UPDATE `item_itemization` SET `armor_delta` = -1549 WHERE `entry` = 18342; -- Quel'dorei Guard
UPDATE `item_itemization` SET `armor_delta` = 21 WHERE `entry` = 18485; -- Observer's Shield
UPDATE `item_itemization` SET `armor_delta` = 12 WHERE `entry` = 18499; -- Barrier Shield
UPDATE `item_itemization` SET `armor_delta` = -6 WHERE `entry` = 18535; -- Milli's Shield
UPDATE `item_itemization` SET `armor_delta` = 12 WHERE `entry` = 18756; -- Dreadguard's Protector
UPDATE `item_itemization` SET `armor_delta` = 11 WHERE `entry` = 19862; -- Aegis of the Blood God
UPDATE `item_itemization` SET `armor_delta` = -55 WHERE `entry` = 19915; -- Zulian Defender
UPDATE `item_itemization` SET `armor_delta` = -1779 WHERE `entry` = 20502; -- Ironbark Shield
UPDATE `item_itemization` SET `armor_delta` = 40 WHERE `entry` = 20688; -- Earthen Guard
UPDATE `item_itemization` SET `armor_delta` = 11 WHERE `entry` = 21485; -- Buru's Skull Fragment
UPDATE `item_itemization` SET `armor_delta` = 81 WHERE `entry` = 21610; -- Wormscale Blocker
UPDATE `item_itemization` SET `armor_delta` = 17 WHERE `entry` = 22336; -- Draconian Aegis of the Legion
UPDATE `item_itemization` SET `armor_delta` = 23 WHERE `entry` = 22818; -- The Plague Bearer
UPDATE `item_itemization` SET `armor_delta` = 36 WHERE `entry` = 22819; -- Shield of Condemnation
UPDATE `item_itemization` SET `armor_delta` = 78 WHERE `entry` = 23043; -- The Face of Death
UPDATE `item_itemization` SET `armor_delta` = 23 WHERE `entry` = 23075; -- Death's Bargain
UPDATE `item_itemization` SET `armor_delta` = -66 WHERE `entry` = 27449; -- Blood Knight Defender
UPDATE `item_itemization` SET `armor_delta` = -66 WHERE `entry` = 27772; -- Stormshield of Renewal
UPDATE `item_itemization` SET `armor_delta` = -7 WHERE `entry` = 27887; -- Platinum Shield of the Valorous
UPDATE `item_itemization` SET `armor_delta` = -66 WHERE `entry` = 27910; -- Silvermoon Crest Shield
UPDATE `item_itemization` SET `armor_delta` = 1 WHERE `entry` = 28166; -- Shield of the Void
UPDATE `item_itemization` SET `armor_delta` = -66 WHERE `entry` = 28316; -- Aegis of the Sunbird
UPDATE `item_itemization` SET `armor_delta` = 50 WHERE `entry` = 28606; -- Shield of Impenetrable Darkness
UPDATE `item_itemization` SET `armor_delta` = 50 WHERE `entry` = 28611; -- Dragonheart Flameshield
UPDATE `item_itemization` SET `armor_delta` = 50 WHERE `entry` = 28754; -- Triptych Shield of the Ancients
UPDATE `item_itemization` SET `armor_delta` = 60 WHERE `entry` = 29176; -- Crest of the Sha'tar
UPDATE `item_itemization` SET `armor_delta` = 38 WHERE `entry` = 29266; -- Azure-Shield of Coldarra
UPDATE `item_itemization` SET `armor_delta` = 38 WHERE `entry` = 29267; -- Light-Bearer's Faith Shield
UPDATE `item_itemization` SET `armor_delta` = 38 WHERE `entry` = 29268; -- Mazthoril Honor Shield
UPDATE `item_itemization` SET `armor_delta` = 3 WHERE `entry` = 31200; -- Shield of the Wayward Footman
UPDATE `item_itemization` SET `armor_delta` = -7 WHERE `entry` = 31292; -- Crystal Pulse Shield
UPDATE `item_itemization` SET `armor_delta` = -66 WHERE `entry` = 32652; -- Ogri'la Aegis
UPDATE `item_itemization` SET `armor_delta` = 30 WHERE `entry` = 33326; -- Bulwark of the Amani Empire
UPDATE `item_itemization` SET `armor_delta` = 30 WHERE `entry` = 33332; -- Enamelled Disc of Mojo
UPDATE `item_itemization` SET `armor_delta` = -82 WHERE `entry` = 34185; -- Sword Breaker's Bulwark
UPDATE `item_itemization` SET `armor_delta` = -82 WHERE `entry` = 34231; -- Aegis of Angelic Fortune
UPDATE `item_itemization` SET `armor_delta` = -1735 WHERE `entry` = 34415; -- Crystaline Shard Shield
UPDATE `item_itemization` SET `armor_delta` = 50 WHERE `entry` = 34675; -- Sunward Crest
UPDATE `item_itemization` SET `armor_delta` = 50 WHERE `entry` = 34676; -- Dawnforged Defender
UPDATE `item_itemization` SET `armor_delta` = -161 WHERE `entry` = 34986; -- Brutal Gladiator's Barrier
UPDATE `item_itemization` SET `armor_delta` = -161 WHERE `entry` = 35073; -- Brutal Gladiator's Redoubt
UPDATE `item_itemization` SET `armor_delta` = 363 WHERE `entry` = 35636; -- Tharon'ja's Aegis
UPDATE `item_itemization` SET `armor_delta` = 450 WHERE `entry` = 35642; -- Riot Shield
UPDATE `item_itemization` SET `armor_delta` = 779 WHERE `entry` = 37061; -- Tor's Crest
UPDATE `item_itemization` SET `armor_delta` = 779 WHERE `entry` = 37107; -- Leeka's Shield
UPDATE `item_itemization` SET `armor_delta` = 1025 WHERE `entry` = 37162; -- Bulwark of the Noble Protector
UPDATE `item_itemization` SET `armor_delta` = 1025 WHERE `entry` = 37216; -- Facade Shield of Glyphs
UPDATE `item_itemization` SET `armor_delta` = -29 WHERE `entry` = 37747; -- Beneficent Bulwark
UPDATE `item_itemization` SET `armor_delta` = 532 WHERE `entry` = 37810; -- Blade-Binding Bulwark
UPDATE `item_itemization` SET `armor_delta` = 159 WHERE `entry` = 38452; -- Bulwark of the Warchief
UPDATE `item_itemization` SET `armor_delta` = 159 WHERE `entry` = 38453; -- Shield of the Lion-hearted
UPDATE `item_itemization` SET `armor_delta` = 159 WHERE `entry` = 38462; -- Warsong Stormshield
UPDATE `item_itemization` SET `armor_delta` = 159 WHERE `entry` = 38463; -- Lordaeron's Resolve
UPDATE `item_itemization` SET `armor_delta` = 597 WHERE `entry` = 39173; -- Bulwark of the Tormented God
UPDATE `item_itemization` SET `armor_delta` = -257 WHERE `entry` = 39233; -- Aegis of Damnation
UPDATE `item_itemization` SET `armor_delta` = -257 WHERE `entry` = 39276; -- The Skull of Ruin
UPDATE `item_itemization` SET `armor_delta` = -65 WHERE `entry` = 39716; -- Shield of Assimilation
UPDATE `item_itemization` SET `armor_delta` = -65 WHERE `entry` = 40266; -- Hero's Surrender
UPDATE `item_itemization` SET `armor_delta` = -65 WHERE `entry` = 40475; -- Barricade of Eternity
UPDATE `item_itemization` SET `armor_delta` = 573 WHERE `entry` = 40670; -- Saronite Defender
UPDATE `item_itemization` SET `armor_delta` = -257 WHERE `entry` = 40700; -- Protective Barricade of the Light
UPDATE `item_itemization` SET `armor_delta` = -257 WHERE `entry` = 40701; -- Crygil's Discarded Plate Panel
UPDATE `item_itemization` SET `armor_delta` = 450 WHERE `entry` = 41113; -- Saronite Bulwark
UPDATE `item_itemization` SET `armor_delta` = 573 WHERE `entry` = 41117; -- Saronite Protector
UPDATE `item_itemization` SET `armor_delta` = -257 WHERE `entry` = 42508; -- Titansteel Shield Wall
UPDATE `item_itemization` SET `armor_delta` = 1025 WHERE `entry` = 42557; -- Savage Gladiator's Barrier
UPDATE `item_itemization` SET `armor_delta` = -257 WHERE `entry` = 42563; -- Hateful Gladiator's Barrier
UPDATE `item_itemization` SET `armor_delta` = -65 WHERE `entry` = 42564; -- Deadly Gladiator's Barrier
UPDATE `item_itemization` SET `armor_delta` = 1025 WHERE `entry` = 42568; -- Savage Gladiator's Redoubt
UPDATE `item_itemization` SET `armor_delta` = -257 WHERE `entry` = 42569; -- Hateful Gladiator's Redoubt
UPDATE `item_itemization` SET `armor_delta` = -65 WHERE `entry` = 42570; -- Deadly Gladiator's Redoubt
UPDATE `item_itemization` SET `armor_delta` = -257 WHERE `entry` = 43085; -- Royal Crest of Lordaeron
UPDATE `item_itemization` SET `armor_delta` = 485 WHERE `entry` = 44032; -- Bulwark of Redemption
UPDATE `item_itemization` SET `armor_delta` = -257 WHERE `entry` = 44313; -- Zom's Crackling Bulwark
UPDATE `item_itemization` SET `armor_delta` = -8487 WHERE `entry` = 53496; -- Barrier of the Earth Princess
