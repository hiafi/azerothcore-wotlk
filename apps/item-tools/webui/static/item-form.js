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

document.addEventListener('DOMContentLoaded', () => {
  const classSelect = document.getElementById('field-class');
  if (classSelect) classSelect.addEventListener('change', filterSubclassOptions);
});
