// Filters the subclass <select> (webui/templates/item_form.html) down to
// options matching the class <select>'s value - subclass IDs are only
// meaningful within their class (Weapon subclass 7 is "Sword (1H)",
// Armor subclass 7 is "Libram"). Deliberately only runs on the class
// field's own `change` event, never on page load: on load, an
// out-of-range historical value (see webui/app.py's SUBCLASS_PAIRS
// comment) must stay selected and visible exactly as-is, not get
// silently snapped to the first visible option before the user has
// touched anything.
function filterSubclassOptions() {
  const classSelect = document.getElementById('field-class');
  const subclassSelect = document.getElementById('field-subclass');
  if (!classSelect || !subclassSelect) return;
  const classId = classSelect.value;
  for (const opt of subclassSelect.options) {
    opt.hidden = opt.dataset.class !== undefined && opt.dataset.class !== classId;
  }
  const firstVisible = Array.from(subclassSelect.options).find((o) => !o.hidden);
  if (firstVisible) subclassSelect.value = firstVisible.value;
}

// Filters the secondary-shape <select> (webui/templates/item_form.html,
// itemization section) down to shapes whose rule actually passes against the
// currently-selected primary shape's own stat set - mirrors
// ItemBudget.cpp's SecondaryShapeRulesSatisfied() / lib.shapes.rules_satisfied().
// Every secondary shape's <option> carries its own rule as
// data-requires/data-forbids (comma-separated stat_type lists, empty string
// for "none"); every primary shape's <option> carries its own stat set as
// data-stats. Runs on the primary <select>'s `change` event only, same
// posture as filterSubclassOptions() above - the value loaded from the
// database is already known-valid (every real item_itemization row is
// migration-validated), so there's nothing to preserve on page load here
// the way an out-of-range historical subclass value is.
function parseStatList(raw) {
  return raw ? raw.split(',').map(Number) : [];
}

function rulesSatisfied(requires, forbids, primaryStats) {
  if (forbids.some((st) => primaryStats.includes(st))) return false;
  if (requires.length === 0) return true;
  return requires.some((st) => primaryStats.includes(st));
}

function filterSecondaryOptions() {
  const primarySelect = document.getElementById('field-primary-shape');
  const secondarySelect = document.getElementById('field-secondary-shape');
  if (!primarySelect || !secondarySelect) return;
  const primaryOption = primarySelect.options[primarySelect.selectedIndex];
  const primaryStats = parseStatList(primaryOption ? primaryOption.dataset.stats : '');

  for (const opt of secondarySelect.options) {
    const requires = parseStatList(opt.dataset.requires);
    const forbids = parseStatList(opt.dataset.forbids);
    opt.hidden = !rulesSatisfied(requires, forbids, primaryStats);
  }
  const selected = secondarySelect.options[secondarySelect.selectedIndex];
  if (!selected || selected.hidden) {
    const firstVisible = Array.from(secondarySelect.options).find((o) => !o.hidden);
    if (firstVisible) secondarySelect.value = firstVisible.value;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const classSelect = document.getElementById('field-class');
  if (classSelect) classSelect.addEventListener('change', filterSubclassOptions);

  const primarySelect = document.getElementById('field-primary-shape');
  if (primarySelect) primarySelect.addEventListener('change', filterSecondaryOptions);
});
