// "Damage per level" chart on the spell edit form: for each effect slot that
// looks like a damage effect, plots the average effect value across levels
// 1-80, with extra lines for what it'd be with +500/+1000/+2000 spell power
// or attack power added.
//
// Recomputes live from the form's current (unsaved) field values via a
// single delegated 'input'/'change' listener on the <form>, so an edit shows
// up in the chart before you hit Save.
//
// Effect-value formula mirrors SpellEffectInfo::CalcValue
// (src/server/game/Spells/SpellInfo.cpp): base_points + trunc((level -
// max(BaseLevel, SpellLevel)) * points_per_level), level clamped to
// [BaseLevel, MaxLevel], plus the average of the EffectDieSides roll.
// BaseLevel/MaxLevel/SpellLevel come from the raw_overrides rows when
// present (0/uncapped otherwise, matching Spell.dbc's empty-row defaults).
//
// Coefficient formula mirrors Unit::CalculateDefaultCoefficient +
// GetCastingTimeForBonus (src/server/game/Entities/Unit/Unit.cpp) for the
// common case: cast_time_ms clamped to [1500, 7000], split between a direct
// hit and a periodic-damage aura when a spell has both (e.g. Fireball). This
// is the coefficient the engine falls back to when spell_bonus_data has no
// row for the spell — dbc-tools has no visibility into that DB table, so a
// spell with an explicit override there will show a different number
// in-game than this chart. AoE/multi-effect/leech reductions (which depend
// on the effect-target table this tool doesn't model) aren't applied either
// — see the caveat text rendered under the charts.

const SPELL_EFFECT_SCHOOL_DAMAGE = 2;
const SPELL_EFFECT_APPLY_AURA = 6;
const SPELL_AURA_PERIODIC_DAMAGE = 3;

const MAX_LEVEL = 80;
const POWER_STEPS = [0, 500, 1000, 2000];

function fieldNum(form, name, fallback) {
  const el = form.elements.namedItem(name);
  if (!el) return fallback;
  const value = parseFloat(el.value);
  return Number.isFinite(value) ? value : fallback;
}

// Pulls BaseLevel/MaxLevel/SpellLevel out of the raw_overrides key/value
// rows, if the user has set any — these aren't modeled as their own form
// fields (see SPELL_PLAIN_FIELDS in view_models.py), only reachable here.
function overrideLevelFields(form) {
  const keys = form.querySelectorAll('[name="override_key"]');
  const values = form.querySelectorAll('[name="override_value"]');
  const wanted = { BaseLevel: 0, MaxLevel: 0, SpellLevel: 0 };
  keys.forEach((keyEl, i) => {
    const key = keyEl.value.trim();
    if (!(key in wanted)) return;
    const raw = values[i] ? values[i].value.trim() : '';
    const num = parseFloat(raw);
    if (Number.isFinite(num)) wanted[key] = num;
  });
  return wanted;
}

function readEffect(form, i) {
  const prefix = `effect${i}_`;
  const typeEl = form.elements.namedItem(prefix + 'type');
  const typeRaw = typeEl ? typeEl.value.trim() : '';
  if (typeRaw === '') return null;
  return {
    type: parseInt(typeRaw, 10),
    basePoints: fieldNum(form, prefix + 'base_points', 0),
    pointsPerLevel: fieldNum(form, prefix + 'points_per_level', 0),
    dieSides: fieldNum(form, prefix + 'die_sides', 0),
    applyAura: fieldNum(form, prefix + 'apply_aura', 0),
    amplitudeMs: fieldNum(form, prefix + 'amplitude', 0),
  };
}

function classifyEffect(effect) {
  if (!effect) return null;
  if (effect.type === SPELL_EFFECT_SCHOOL_DAMAGE) return 'direct';
  if (effect.type === SPELL_EFFECT_APPLY_AURA && effect.applyAura === SPELL_AURA_PERIODIC_DAMAGE) return 'dot';
  return null;
}

function averageEffectValue(effect, level, levels) {
  let clamped = level;
  if (levels.maxLevel > 0 && clamped > levels.maxLevel) clamped = levels.maxLevel;
  if (clamped < levels.baseLevel) clamped = levels.baseLevel;
  const levelsAboveFloor = clamped - Math.max(levels.baseLevel, levels.spellLevel);

  let basePoints = effect.basePoints;
  if (effect.pointsPerLevel !== 0) {
    basePoints += Math.trunc(levelsAboveFloor * effect.pointsPerLevel);
  }

  // "roll in a range <1;EffectDieSides>" (SpellEffectInfo::CalcValue) — use
  // the roll's average rather than simulating randomness.
  const dieSides = effect.dieSides;
  let dieAverage = 0;
  if (dieSides === 1) dieAverage = 1;
  else if (dieSides > 1) dieAverage = (1 + dieSides) / 2;
  else if (dieSides < 0) dieAverage = (dieSides + 1) / 2;

  return basePoints + dieAverage;
}

// Mirrors Unit::GetCastingTimeForBonus + Unit::CalculateDefaultCoefficient's
// non-channeled, single-target path. `dotDurationMs`/`ticks` describe the
// spell's periodic-damage effect, if it has one, whether or not the effect
// we're computing a coefficient for right now is that same effect (a direct
// hit sharing a spell with a DoT gets its cast time split with it, and vice
// versa — see "Combined Spells with Both Over Time and Direct Damage").
function defaultCoefficients(castTimeMs, hasDirect, hasDot, dotDurationMs, ticks) {
  const castClamped = Math.min(Math.max(castTimeMs || 0, 1500), 7000);
  const overTimeMs = hasDot ? (dotDurationMs || 0) : 0;

  let ptOverTime = 0;
  if (overTimeMs > 0) {
    const dotPortion = overTimeMs / 15000;
    const directPortion = castClamped / 3500;
    ptOverTime = dotPortion / (dotPortion + directPortion);
  }

  const directCastTime = hasDirect ? (ptOverTime < 1 ? castClamped * (1 - ptOverTime) : 0) : 0;
  const dotCastTime = hasDot ? 3500 * ptOverTime : 0;
  const dotFactor = hasDot && dotDurationMs > 0 ? (dotDurationMs / 15000) / Math.max(ticks, 1) : 0;

  return {
    direct: directCastTime / 3500,
    dotPerTick: (dotCastTime / 3500) * dotFactor,
  };
}

function chartColor(varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
}

function buildDatasets(effect, kind, coeff) {
  const perPointCoeff = kind === 'dot' ? coeff.dotPerTick : coeff.direct;
  const colorVars = ['--chart-power-0', '--chart-power-500', '--chart-power-1000', '--chart-power-2000'];
  return POWER_STEPS.map((power, i) => ({
    label: power === 0 ? 'Base (no bonus)' : `+${power} power`,
    data: null, // filled per-level by the caller
    power,
    borderColor: chartColor(colorVars[i]),
    backgroundColor: chartColor(colorVars[i]),
    borderWidth: 2,
    pointRadius: 0,
    pointHoverRadius: 3,
    tension: 0.15,
  }));
}

function computeSeries(effect, kind, levels, coeff) {
  const datasets = buildDatasets(effect, kind, coeff);
  const perPointCoeff = kind === 'dot' ? coeff.dotPerTick : coeff.direct;
  for (let level = 1; level <= MAX_LEVEL; level++) {
    const base = averageEffectValue(effect, level, levels);
    datasets.forEach((ds) => {
      if (!ds.data) ds.data = [];
      ds.data.push(Math.round((base + perPointCoeff * ds.power) * 10) / 10);
    });
  }
  return datasets;
}

const chartInstances = {};

function renderChart(canvas, title, datasets) {
  const labels = [];
  for (let level = 1; level <= MAX_LEVEL; level++) labels.push(level);

  const existing = chartInstances[canvas.id];
  if (existing) existing.destroy();

  chartInstances[canvas.id] = new Chart(canvas, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      animation: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        title: { display: true, text: title, color: chartColor('--chart-axis') },
        legend: { labels: { color: chartColor('--chart-axis') } },
        tooltip: { enabled: true },
      },
      scales: {
        x: {
          title: { display: true, text: 'Character level', color: chartColor('--chart-axis') },
          grid: { color: chartColor('--chart-grid') },
          ticks: { color: chartColor('--chart-axis'), maxTicksLimit: 16 },
        },
        y: {
          title: { display: true, text: 'Damage', color: chartColor('--chart-axis') },
          grid: { color: chartColor('--chart-grid') },
          ticks: { color: chartColor('--chart-axis') },
          beginAtZero: true,
        },
      },
    },
  });
}

function schoolLabel(form) {
  const el = form.elements.namedItem('school');
  const opt = el && el.selectedOptions[0];
  return opt && opt.value ? opt.textContent.replace(/^\d+\s*—\s*/, '') : 'damage';
}

function updateDamageCharts(form) {
  const container = document.getElementById('damage-charts');
  const emptyMessage = document.getElementById('damage-charts-empty');
  if (!container) return;

  const effects = [1, 2, 3].map((i) => readEffect(form, i));
  const kinds = effects.map(classifyEffect);
  const qualifying = kinds.filter(Boolean).length;

  container.querySelectorAll('.damage-chart').forEach((el) => el.remove());
  emptyMessage.style.display = qualifying ? 'none' : '';
  if (!qualifying) return;

  const levels = overrideLevelFields(form);
  levels.baseLevel = levels.BaseLevel;
  levels.spellLevel = levels.SpellLevel;
  levels.maxLevel = levels.MaxLevel;

  const castTimeMs = fieldNum(form, 'cast_time_ms', 0);
  const dotIndex = kinds.findIndex((k) => k === 'dot');
  const dotEffect = dotIndex === -1 ? null : effects[dotIndex];
  const dotDurationMs = fieldNum(form, 'duration_ms', 0);
  const ticks = dotEffect && dotEffect.amplitudeMs > 0 ? Math.round(dotDurationMs / dotEffect.amplitudeMs) : 1;
  const hasDirect = kinds.includes('direct');
  const hasDot = kinds.includes('dot');

  const coeff = defaultCoefficients(castTimeMs, hasDirect, hasDot, dotDurationMs, ticks);
  const school = schoolLabel(form);

  kinds.forEach((kind, idx) => {
    if (!kind) return;
    const effect = effects[idx];
    const datasets = computeSeries(effect, kind, levels, coeff);
    const wrapper = document.createElement('div');
    wrapper.className = 'damage-chart';
    const canvas = document.createElement('canvas');
    canvas.id = `damage-chart-${idx + 1}`;
    wrapper.appendChild(canvas);
    container.appendChild(wrapper);
    const title = kind === 'dot'
      ? `Effect ${idx + 1} — ${school} damage per tick`
      : `Effect ${idx + 1} — ${school} damage (direct hit)`;
    renderChart(canvas, title, datasets);
  });
}

function initDamageCharts() {
  const form = document.getElementById('spell-form');
  if (!form || typeof Chart === 'undefined') return;
  updateDamageCharts(form);
  let pending = null;
  form.addEventListener('input', () => {
    // Coalesce bursts (typing, or a whole override row being cloned) into
    // one recompute per frame rather than one per keystroke.
    if (pending) return;
    pending = requestAnimationFrame(() => {
      pending = null;
      updateDamageCharts(form);
    });
  });
  form.addEventListener('change', () => updateDamageCharts(form));
  // Adding/removing an override row (BaseLevel/MaxLevel/SpellLevel) happens
  // via a plain button click, not an input/change event.
  form.addEventListener('click', (e) => {
    if (e.target.closest('button')) updateDamageCharts(form);
  });
}

document.addEventListener('DOMContentLoaded', initDamageCharts);
