import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

export function renderPromptCreationView(container) {
  container.innerHTML = `
    <div class="testing-layout">
      <section class="card testing-builder">
        <div class="card-head">
          <h3>Prompt Creation & Assembly</h3>
          <div class="toolbar-row" style="margin:0;">
            <button type="button" class="btn btn-sm" id="tb-toggle-cat-form">+ Category</button>
            <button type="button" class="btn btn-sm" id="tb-toggle-part-form">+ Part</button>
            <button type="button" class="btn btn-sm btn-primary" id="tb-assemble">Assemble</button>
          </div>
        </div>

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

        <textarea id="tb-preview" class="prompt-preview" readonly placeholder="Assembled prompt preview will appear here…"></textarea>
        <div class="toolbar-row">
          <span id="tb-stats" class="text-muted small"></span>
          <span class="spacer"></span>
          <select id="tb-publish-agent" class="form-select" style="max-width: 180px;">
            <option value="">Select agent…</option>
          </select>
          <button type="button" class="btn btn-sm" id="tb-copy">Copy</button>
          <button type="button" class="btn btn-sm btn-primary" id="tb-publish">Save to Agent</button>
        </div>
        <p id="tb-msg" class="small hidden"></p>
      </section>

      <section class="card">
        <div class="card-head">
          <h3>Available Core Engine Tools</h3>
          <button type="button" class="btn btn-sm" id="btn-refresh-tools">Refresh Tools</button>
        </div>
        <p class="text-muted small">Tools retrieved from <code>core_engine/interface.py</code> for prompt reference.</p>
        <button type="button" class="btn btn-sm btn-primary" id="btn-add-tools-to-prompt">
          Add Selected Tools to Prompt
        </button>
        <div id="tools-list-container" style="overflow-y: auto; max-height: 500px;" class="mt-2">
          <p class="text-muted">Loading available tools...</p>
        </div>
      </section>
    </div>`;

  const catBox = container.querySelector('#tb-categories');
  const preview = container.querySelector('#tb-preview');
  const stats = container.querySelector('#tb-stats');
  const msg = container.querySelector('#tb-msg');
  const toolsContainer = container.querySelector('#tools-list-container');
  const publishAgentSel = container.querySelector('#tb-publish-agent');

  const catForm = container.querySelector('#tb-cat-form');
  const partForm = container.querySelector('#tb-part-form');
  const partCatSelect = container.querySelector('#part-cat-select');

  let manifest = { categories: [] };
  let availableTools = [];
  let promptBase = '';
  let promptPartCount = 0;
  const promptTools = new Map();

  function showMsg(text, isError = false) {
    msg.textContent = text;
    msg.className = `small ${isError ? 'text-danger' : 'text-success'}`;
  }

  async function loadCoreTools() {
    try {
      toolsContainer.innerHTML = '<p class="text-muted">Fetching tools from core_engine...</p>';
      const res = await Api.getTools();
      availableTools = res.tools || [];

      if (!availableTools.length) {
        toolsContainer.innerHTML = '<p class="text-muted">No tools currently registered in core engine.</p>';
        return;
      }

      toolsContainer.innerHTML = availableTools.map((t, index) => `
        <div class="category-block mt-2">
          <div class="category-head">
            <label class="checkbox-row" style="margin:0;">
              <input type="checkbox" value="${index}" data-tool>
              <strong>🛠️ ${esc(t.name)}</strong>
            </label>
            <span class="badge badge-accent">${esc(t.provider)}</span>
          </div>
          <p class="text-muted small mt-2"><code>${esc(t.signature)}</code></p>
          <p class="small text-light">${esc(Array.isArray(t.description) ? t.description.join(' ') : t.description)}</p>
        </div>
      `).join('');
    } catch (err) {
      toolsContainer.innerHTML = `<p class="text-danger">Failed to retrieve tools: ${esc(err.message)}</p>`;
    }
  }

  function updatePromptPreview() {
    const toolSection = [...promptTools.values()].map(tool => {
      const description = Array.isArray(tool.description)
        ? tool.description.join(' ')
        : tool.description;
      return [
        `### ${tool.name}`,
        `- Provider: ${tool.provider}`,
        `- Signature: ${tool.signature}`,
        description ? `- Description: ${description}` : ''
      ].filter(Boolean).join('\n');
    }).join('\n\n');

    preview.value = [promptBase, toolSection ? `## Available Tools\n\n${toolSection}` : '']
      .filter(Boolean)
      .join('\n\n');
    stats.textContent = `${promptPartCount} parts · ${preview.value.length} chars`;
  }

  async function loadPromptAgents() {
    try {
      const [workspaceData, codeBuilderData] = await Promise.all([
        Api.getAgents(),
        Api.getCodeBuilderAgents()
      ]);
      const agents = [
        ...(workspaceData.agents || []).map(agent => ({ ...agent, environment: 'workspace' })),
        ...(codeBuilderData.agents || []).map(agent => ({ ...agent, environment: 'codebuilder' }))
      ];
      publishAgentSel.innerHTML = agents.length
        ? agents.map(a => `<option value="${esc(a.environment)}:${esc(a.id)}">${esc(a.name)} (${esc(a.id)}) — ${a.environment === 'codebuilder' ? 'CodeBuilder' : 'Workspace'}</option>`).join('')
        : '<option value="">No agents found</option>';
    } catch (err) {
      publishAgentSel.innerHTML = `<option value="">${esc(err.message)}</option>`;
    }
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

  loadCoreTools();
  loadManifest();
  loadPromptAgents();

  container.querySelector('#btn-refresh-tools').addEventListener('click', loadCoreTools);

  container.querySelector('#btn-add-tools-to-prompt').addEventListener('click', () => {
    const selected = [...toolsContainer.querySelectorAll('[data-tool]:checked')];
    if (!selected.length) return showMsg('Select at least one core engine tool.', true);

    selected.forEach(input => {
      const tool = availableTools[Number(input.value)];
      if (tool) promptTools.set(tool.name, tool);
    });
    updatePromptPreview();
    showMsg(`${selected.length} selected tool${selected.length === 1 ? '' : 's'} added to the prompt.`);
  });

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

  partForm.querySelectorAll('input, textarea').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        submitPart();
      }
    });
  });

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
      promptBase = res.prompt;
      promptPartCount = res.part_count;
      updatePromptPreview();
      showMsg('Prompt assembled.');
    } catch (err) {
      showMsg(err.message, true);
    }
  });

  container.querySelector('#tb-copy').addEventListener('click', async () => {
    if (!preview.value) return;
    try {
      await navigator.clipboard.writeText(preview.value);
      showMsg('Copied to clipboard.');
    } catch (_) {
      preview.select();
      document.execCommand('copy');
      showMsg('Copied.');
    }
  });

  container.querySelector('#tb-publish').addEventListener('click', async () => {
    const [environment, agentId] = publishAgentSel.value.split(':', 2);
    if (!environment || !agentId) return showMsg('Select an agent to publish first.', true);
    if (!preview.value.trim()) return showMsg('Assemble a prompt before saving it to an agent.', true);
    try {
      const res = await Api.publishAgent(agentId, 'snapshot', preview.value, environment);
      showMsg(`Saved to ${res.path} and ${res.metadata_path} (headers ${res.header_report.verdict}; snapshot ${res.snapshot}).`);
    } catch (err) {
      showMsg(err.message, true);
    }
  });
}
