/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

// The gate itself
void AddSC_content_gate();

// Content scripts ported from mod-progression (registered unconditionally; modules load after core, so the
// same-named Onyxia scripts replace core's)
void AddSC_instance_onyxias_lair_progression();
void AddSC_boss_onyxia_progression();
void AddSC_go_scarab_gong();
void AddSC_go_scarab_gate();
void AddSC_spell_mark_of_kazzak();
void AddSC_spell_summon_nightbane();

// Add all
void Addmod_content_gateScripts()
{
    AddSC_content_gate();
    AddSC_instance_onyxias_lair_progression();
    AddSC_boss_onyxia_progression();
    AddSC_go_scarab_gong();
    AddSC_go_scarab_gate();
    AddSC_spell_mark_of_kazzak();
    AddSC_spell_summon_nightbane();
}
