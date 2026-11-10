"""
Crafting rework C2: free gathering (`.agents/plans/crafting-rework/crafting-rework.PLAN.md`, DESIGN R1/R2).

Every character has Herbalism, Mining and Skinning plus up to two crafting professions, all at the phase cap
(`src/server/scripts/Custom/custom_professions.cpp` grants and raises them; `Custom.Professions.SkillCap`).

1. The three gathering skills leave the primary profession category (11) for the secondary one (9).
   `IsPrimaryProfessionSkill` (SpellMgr.cpp) only counts category 11, so gathering stops using one of the two
   `MaxPrimaryTradeSkill` points: the limit now covers crafting alone. The client patch row moves them under
   "Secondary Skills" in the Skills tab and drops their Unlearn button (the client offers it for category 11 only);
   the server cannot unlearn them either (`WorldSession::HandleUnlearnSkillOpcode` refuses a non-profession skill).
   Stock rows otherwise (names, icon, CanLink).

2. The gathering perks go (user 2026-11-10): Toughness (Mining), Master of Anatomy (Skinning) and Lifeblood
   (Herbalism) would otherwise come free to everyone. Each rank is a stock SkillLineAbility row with AcquireMethod 1
   (learned on skill value), which `Player::learnSkillRewardedSpells` teaches when the skill reaches the row's
   MinSkillLineRank and unlearns below it. AcquireMethod 0 takes them out of that path, so nobody learns them any more;
   characters who already know them lose them through the login cleanup in custom_professions.cpp.
"""

from lib.dsl.registry import SkillCategory, override_skill_line, override_skill_line_ability

HERBALISM = 182
MINING = 186
SKINNING = 393

for skill_id in (HERBALISM, MINING, SKINNING):
    override_skill_line(skill_id, CategoryID=SkillCategory.SECONDARY)

# SkillLineAbility rows (stock SkillLineAbility.dbc, all AcquireMethod 1) -> the perk rank they teach.
GATHERING_PERK_ROWS = {
    # Toughness (skill 186): Stamina, ranks at Mining 75/150/225/300/375/450
    17987: 53120, 17988: 53121, 17989: 53122, 17990: 53123, 17991: 53124, 17984: 53040,
    # Master of Anatomy (skill 393): critical strike rating, ranks at Skinning 75-450
    17993: 53125, 18277: 53662, 18278: 53663, 18279: 53664, 18280: 53665, 18281: 53666,
    # Lifeblood (skill 182): the self-heal, ranks at Herbalism 75-450
    19355: 55428, 19356: 55480, 19357: 55500, 19358: 55501, 19359: 55502, 19360: 55503,
}

for sla_id in GATHERING_PERK_ROWS:
    override_skill_line_ability(sla_id, acquire_method=0)
