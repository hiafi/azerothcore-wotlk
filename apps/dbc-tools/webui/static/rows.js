// Clones a <template> and appends it into a container — used for the
// repeatable raw_overrides key/value rows and rank_spell_id rows across the
// spell/tab/talent forms. No framework, just the two call sites need it.
function addRow(containerId, templateId) {
  const tpl = document.getElementById(templateId);
  const container = document.getElementById(containerId);
  container.appendChild(tpl.content.cloneNode(true));
}
