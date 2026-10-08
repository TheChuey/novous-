import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

/**
 * Prompt Builder & Header Test Runner Component.
 */
export function renderTestingView(container) {
  container.innerHTML = `
    <div class="testing-layout">
      <section class="card testing-builder">
        <div class="card-head">
          <h3>Prompt Builder</h3>
          <div class="toolbar-row" style="margin:0;">
            <button type="button" class="btn btn-sm" id="tb-toggle-cat-form">+ Category</button>
            <button type="button" class="btn btn-sm" id="tb-toggle-part-form">+ Part</button>
            <button type="button" class="btn btn-sm btn-primary" id="tb-assemble">Assemble</button>
          </div>
        </div>

        <!-- Add Category Form -->
        <div id="tb-cat-form" class="card bg-elev hidden" style="margin-bottom: 0.75rem; padding: 0.75rem;">
          <h4 style="margin-bottom: 0.5rem;">Add New Category</h4>
          <div class="form-row">
            <input type="text" id="cat-id-input" class="form-input" placeholder="Category ID / Slug (e.g. constraints)" required>
            <input type="text" id="cat-name-input" class="form-input" placeholder="Category Name (e.g. Constraints)" required>
          </div>
          <div class="form-row">
            <input type="text" id="cat-desc-input" class="form-input" placeholder="Description (optional)">
            <input type="text" id="cat-header-input" class="form-input" placeholder="Required Header (e.g. constraints)">
          </div>
          <div class="toolbar-row">
            <button type="button" class="btn btn-sm btn-primary" id="cat-save-btn">Save Category</button>
            <button type="button" class="btn btn-sm" id="cat-cancel-btn">Cancel</button>
          </div>
        </div>

        <!-- Add Part Form -->
        <div id="tb-part-form" class="card bg-elev hidden" style="margin-bottom: 0.75rem; padding: 0.75rem;">
          <h4 style="margin-bottom: 0.5rem;">Add New Prompt Part</h4>
          <div class="form-row">
            <select id="part-cat-select" class="form-select"></select>
            <input type="text" id="part-title-input" class="form-input" placeholder="Part Title (e.g. JSON Format)" required>
          </div>
          <div class="form-row">
            <input type="text" id="part-slug-input" class="form-input" placeholder="Slug ID (optional)">
          </div>
          <div class="form-row">
            <textarea id="part-content-input" class="form-input" style="width: 100%; height: 80px;" placeholder="Prompt part markdown content…" required></textarea>
          </div>
          <div class="toolbar-row">
            <button type="button" class="btn btn-sm btn-primary" id="part-save-btn">Save Part</button>
            <button type="button" class="btn btn-sm" id="part-cancel-btn">Cancel</button>
          </div>
        </div>

        <div id="tb-categories" class="category-grid">
          <p class="text-muted">Loading categories…</p>
        </div>

        <textarea id="tb-preview" class="prompt-preview" readonly
                  placeholder="Assembled prompt preview will appear here…"></textarea>
        <div class="toolbar-row">
          <span id="tb-stats" class="text-muted small"></span>
          <span class="spacer"></span>
          <button type="button" class="btn btn-sm" id="tb-copy">Copy</button>
          <button type="button" class="btn btn-sm btn-primary" id="tb-publish">Publish snapshot</button>
        </div>
        <p id="tb-msg" class="small hidden"></p>
      </section>

      <section class="card testing-runner">
        <div class="card-head">
          <h3>4-Question Header Tests</h3>
          <button type="button" class="btn btn-sm btn-primary" id="ht-run">Run tests</button>
        </div>
        <div class="form-row">
          <select id="ht-agent" class="form-select"><option value="">Loading agents…</option></select>
        </div>
        <div id="ht-results" class="ht-results">
          <p class="text-muted">Select an agent and run the section-header battery.</p>
        </div>
      </section>
    </div>`;

  const catBox = container.querySelector('#tb-categories');
  const preview = container.querySelector('#tb-preview');
  const stats = container.querySelector('#tb-stats');
  const msg = container.querySelector('#tb-msg');
  const agentSel = container.querySelector('#ht-agent');
  const results = container.querySelector('#ht-results');

  const catForm = container.querySelector('#tb-cat-form');
  const partForm = container.querySelector('#tb-part-form');
  const partCatSelect = container.querySelector('#part-cat-select');

  let manifest = { categories: [] };
  let agents = [];

  function showMsg(text, isError = false) {
    msg.textContent = text;
    msg.className = `small ${isError ? 'text-danger' : 'text-success'}`;
  }

  async function loadManifest() {
    try {
      const data = await Api.getPromptCategories();
      manifest = data;
      renderCategories(manifest);
      populateCategoryDropdown(manifest.categories || []);
    } catch (err) {
      catBox.innerHTML = `<p class="text-danger">${esc(err.message)}</p>`;
    }
  }

  function populateCategoryDropdown(categories) {
    partCatSelect.innerHTML = categories.length
      ? categories.map(c => `<option value="${esc(c.id)}">${esc(c.name)} (${esc(c.id)})</option>`).join('')
      : '<option value="">No categories available</option>';
  }

  function renderCategories(data) {
    const cats = data.categories || [];
    const uncategorized = data.uncategorized_parts || [];

    let html = cats.map(cat => `
      <div class="category-block">
        <div class="category-head">
          <div style="display: flex; align-items: center; gap: 0.3rem; flex-wrap: wrap;">
            <strong>${esc(cat.name)}</strong>
            ${cat.required_header ? `<span class="badge badge-accent">## ${esc(cat.required_header)}</span>` : ''}
          </div>
          <button type="button" class="btn btn-ghost btn-sm text-danger" title="Delete category '${esc(cat.name)}'" data-del-cat="${esc(cat.id)}" style="padding: 0 0.3rem;">✕</button>
        </div>
        <p class="text-muted small">${esc(cat.description || '')}</p>
        ${(cat.parts || []).map(p => `
          <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
            <label class="checkbox-row" style="flex: 1; margin: 0;">
              <input type="checkbox" value="${esc(p.id)}" data-part>
              <span>${esc(p.title)}</span>
            </label>
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Delete part" data-del-part="${esc(p.id)}" style="padding: 0 0.3rem;">✕</button>
          </div>`).join('') || '<p class="text-muted small">No parts.</p>'}
      </div>`).join('');

    if (uncategorized.length) {
      html += `
        <div class="category-block">
          <div class="category-head">
            <strong>Uncategorized</strong>
          </div>
          <p class="text-muted small">Parts without a matching category definition.</p>
          ${uncategorized.map(p => `
            <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
              <label class="checkbox-row" style="flex: 1; margin: 0;">
                <input type="checkbox" value="${esc(p.id)}" data-part>
                <span>${esc(p.title)}</span>
              </label>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Delete part" data-del-part="${esc(p.id)}" style="padding: 0 0.3rem;">✕</button>
            </div>`).join('')}
        </div>`;
    }

    catBox.innerHTML = html || '<p class="text-danger">No categories found.</p>';
  }

  loadManifest();

  // --- Toggle forms ---
  container.querySelector('#tb-toggle-cat-form').addEventListener('click', () => {
    catForm.classList.toggle('hidden');
    partForm.classList.add('hidden');
  });

  container.querySelector('#cat-cancel-btn').addEventListener('click', () => {
    catForm.classList.add('hidden');
  });

  container.querySelector('#tb-toggle-part-form').addEventListener('click', () => {
    partForm.classList.toggle('hidden');
    catForm.classList.add('hidden');
  });

  container.querySelector('#part-cancel-btn').addEventListener('click', () => {
    partForm.classList.add('hidden');
  });

  // --- Add Category ---
  async function submitCategory() {
    const id = container.querySelector('#cat-id-input').value.trim();
    const name = container.querySelector('#cat-name-input').value.trim();
    const desc = container.querySelector('#cat-desc-input').value.trim();
    const header = container.querySelector('#cat-header-input').value.trim();

    if (!id || !name) return showMsg('Category ID and Name are required.', true);

    try {
      await Api.addPromptCategory(id, name, desc, header);
      catForm.classList.add('hidden');
      container.querySelector('#cat-id-input').value = '';
      container.querySelector('#cat-name-input').value = '';
      container.querySelector('#cat-desc-input').value = '';
      container.querySelector('#cat-header-input').value = '';
      showMsg(`Category '${name}' added successfully.`);
      await loadManifest();
    } catch (err) {
      showMsg(err.message, true);
    }
  }

  container.querySelector('#cat-save-btn').addEventListener('click', submitCategory);

  catForm.querySelectorAll('input').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitCategory();
      }
    });
  });

  // --- Add Part ---
  async function submitPart() {
    const category = partCatSelect.value;
    const title = container.querySelector('#part-title-input').value.trim();
    const slug = container.querySelector('#part-slug-input').value.trim();
    const content = container.querySelector('#part-content-input').value.trim();

    if (!category || !title || !content) return showMsg('Category, Part Title, and Content are required.', true);

    try {
      await Api.addPromptPart(category, title, content, slug || null);
      partForm.classList.add('hidden');
      container.querySelector('#part-title-input').value = '';
      container.querySelector('#part-slug-input').value = '';
      container.querySelector('#part-content-input').value = '';
      showMsg(`Prompt Part '${title}' added successfully.`);
      await loadManifest();
    } catch (err) {
      showMsg(err.message, true);
    }
  }

  container.querySelector('#part-save-btn').addEventListener('click', submitPart);

  partForm.querySelectorAll('input').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitPart();
      }
    });
  });

  // --- Delete Category & Delete Part delegation ---
  catBox.addEventListener('click', async (e) => {
    const delCatBtn = e.target.closest('[data-del-cat]');
    if (delCatBtn) {
      const catId = delCatBtn.getAttribute('data-del-cat');
      if (confirm(`Are you sure you want to delete category '${catId}' and its parts?`)) {
        try {
          await Api.deletePromptCategory(catId);
          showMsg(`Category '${catId}' deleted.`);
          await loadManifest();
        } catch (err) {
          showMsg(err.message, true);
        }
      }
      return;
    }

    const delPartBtn = e.target.closest('[data-del-part]');
    if (delPartBtn) {
      const partId = delPartBtn.getAttribute('data-del-part');
      if (confirm(`Delete prompt part '${partId}'?`)) {
        try {
          await Api.deletePromptPart(partId);
          showMsg(`Prompt part '${partId}' deleted.`);
          await loadManifest();
        } catch (err) {
          showMsg(err.message, true);
        }
      }
      return;
    }
  });

  function selectedParts() {
    return [...catBox.querySelectorAll('[data-part]:checked')].map(el => el.value);
  }

  container.querySelector('#tb-assemble').addEventListener('click', async () => {
    const parts = selectedParts();
    if (!parts.length) return showMsg('Select at least one prompt part.', true);
    try {
      const res = await Api.assemblePrompt(parts);
      preview.value = res.prompt;
      stats.textContent = `${res.part_count} parts · ${res.char_count} chars`;
      showMsg('Prompt assembled.');
    } catch (err) { showMsg(err.message, true); }
  });

  container.querySelector('#tb-copy').addEventListener('click', async () => {
    if (!preview.value) return;
    try { await navigator.clipboard.writeText(preview.value); showMsg('Copied to clipboard.'); }
    catch (_) { preview.select(); document.execCommand('copy'); showMsg('Copied.'); }
  });

  container.querySelector('#tb-publish').addEventListener('click', async () => {
    const agentId = agentSel.value;
    if (!agentId) return showMsg('Select an agent to publish first.', true);
    try {
      const res = await Api.publishAgent(agentId, 'snapshot');
      showMsg(`Published: ${res.snapshot} (headers ${res.header_report.verdict})`);
    } catch (err) { showMsg(err.message, true); }
  });

  // --- Header test runner --------------------------------------------------
  Api.getAgents().then(data => {
    agents = data.agents || [];
    agentSel.innerHTML = agents.length
      ? agents.map(a => `<option value="${esc(a.id)}">${esc(a.name)}</option>`).join('')
      : '<option value="">No agents</option>';
  }).catch(err => { agentSel.innerHTML = `<option value="">${esc(err.message)}</option>`; });

  container.querySelector('#ht-run').addEventListener('click', async () => {
    if (!agentSel.value) return;
    results.innerHTML = '<p class="text-muted">Running battery…</p>';
    try {
      const report = await Api.runHeaderTests(agentSel.value);
      results.innerHTML = renderReport(report);
    } catch (err) {
      results.innerHTML = `<p class="text-danger">${esc(err.message)}</p>`;
    }
  });

  function renderReport(report) {
    const header = `
      <div class="ht-summary ${report.passed ? 'pass' : 'fail'}">
        <strong>${esc(report.verdict)}</strong>
        <span>score ${esc(report.overall_score)} · ${esc(report.headers_passed)}/${esc(report.headers_total)} headers</span>
      </div>`;
    const rows = report.results.map(r => `
      <div class="ht-header ${r.passed ? 'pass' : 'fail'}">
        <div class="ht-header-head">
          <span class="ht-hash">## ${esc(r.header)}</span>
          <span class="badge ${r.passed ? 'badge-success' : 'badge-danger'}">${esc((r.score).toFixed(2))}</span>
        </div>
        ${r.questions.map(q => `
          <div class="ht-question">
            <span class="ht-q-status ${q.passed ? 'pass' : 'fail'}">${q.passed ? '✓' : '✗'}</span>
            <div>
              <div>${esc(q.question)}</div>
              <div class="text-muted small">${esc(q.evidence)} · score ${esc(q.score)}</div>
            </div>
          </div>`).join('')}
      </div>`).join('');
    const extras = report.extra_headers?.length
      ? `<p class="text-muted small">Extra headers: ${esc(report.extra_headers.join(', '))}</p>` : '';
    return header + rows + extras;
  }
}
