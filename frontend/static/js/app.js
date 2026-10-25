import { Api } from './api.js';
import { renderTree } from './tree.js';
import { renderEditorView } from './editor.js';
import { renderChatView } from './chat.js';
import { renderPromptCreationView } from './prompt_creation.js';
import { renderTestingView } from './testing.js';
import { renderCodeBuilderView } from './codebuilder/codebuilder.js';

export const AppState = {
  activeTab: 'dashboard',
  agents: [],
  project: null,
  health: null,
  currentPath: '',
  ragScanJob: null
};

const views = {
  dashboard: renderDashboardView,
  editor: renderEditorView,
  codebuilder: renderCodeBuilderView,
  chat: renderChatView,
  'prompt-creation': renderPromptCreationView,
  testing: renderTestingView
};

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// --- Dashboard -------------------------------------------------------------
function renderDashboardView(container) {
  const project = AppState.project || {};
  const agents = AppState.agents || [];
  const squads = project.squads || [];

  container.innerHTML = `
    <div class="dashboard">
      <section class="dash-hero card">
        <div>
          <h2>${esc(project.name || 'Novous Workspace')}</h2>
          <p class="text-muted">${esc(project.description || 'Declarative Agent Factory — 4-Pillar Architecture.')}</p>
        </div>
        <div class="dash-hero-stats">
          <div class="stat"><span class="stat-num">${agents.length}</span><span class="stat-label">Agents</span></div>
          <div class="stat"><span class="stat-num">${squads.length}</span><span class="stat-label">Squads</span></div>
          <div class="stat"><span class="stat-num">${esc(project.default_model || '-')}</span><span class="stat-label">Model</span></div>
        </div>
      </section>

      <div class="dash-grid">
        <section class="card dash-agent-card">
          <div class="card-head">
            <h3>Agents</h3>
            <button class="btn btn-sm btn-primary" id="dash-new-agent">+ New Agent</button>
          </div>
          <div id="dash-agent-form" class="hidden mt-2">
            <div class="form-row">
              <input id="na-id" class="form-input" placeholder="agent-id (e.g. reviewer)">
              <input id="na-name" class="form-input" placeholder="Display name">
            </div>
            <div class="form-row">
              <input id="na-desc" class="form-input" placeholder="Description">
              <select id="na-environment" class="form-select" aria-label="Agent environment">
                <option value="workspace">Workspace</option>
                <option value="codebuilder">CodeBuilder</option>
                <option value="prompt-creation">Prompt Creation</option>
              </select>
              <select id="na-mode" class="form-select">
                <option value="chat">chat</option>
                <option value="agent">agent</option>
              </select>
              <button class="btn btn-primary" id="dash-create-agent">Create</button>
            </div>
            <div class="form-row">
              <input id="na-environment-name" class="form-input" placeholder="Custom environment name (optional)" aria-label="Custom environment name" maxlength="64">
            </div>
            <p class="text-danger hidden" id="na-error"></p>
          </div>
          <div class="agent-cards" id="dash-agent-cards">
            ${agents.length ? '' : '<p class="text-muted">No agents yet. Create your first one.</p>'}
          </div>
          <div class="card-head mt-3"><h3>Prompt Creation Agents</h3></div>
          <div class="agent-cards" id="dash-prompt-agent-cards">
            <p class="text-muted">Loading Prompt Creation agents…</p>
          </div>
          <div class="card-head mt-3"><h3>CodeBuilder Agents</h3></div>
          <div class="agent-cards" id="dash-codebuilder-agent-cards">
            <p class="text-muted">Loading CodeBuilder agents…</p>
          </div>
        </section>

        <section class="card dash-squad-card">
          <div class="card-head">
            <h3>Squads</h3>
            <button class="btn btn-sm btn-primary" id="dash-new-squad">+ New Squad</button>
          </div>
          <div class="form-row mt-2">
            <input id="sq-name" class="form-input hidden" placeholder="squad name">
            <button class="btn btn-primary hidden" id="dash-create-squad">Create</button>
          </div>
          <ul class="squad-list" id="dash-squad-list">
            ${squads.map(s => `<li class="squad-item"><strong>${esc(s.name)}</strong>
              <span class="text-muted">${esc(s.description || s.path)}</span>
              <button class="btn btn-sm btn-ghost" data-squad-delete="${esc(s.name)}">✕</button></li>`).join('')
              || '<li class="text-muted">No squads yet.</li>'}
          </ul>
        </section>

        <section class="card dash-tree-card">
          <div class="card-head">
            <div>
              <h3>Workspace Tree</h3>
              <p class="text-muted small">Choose a configured folder. Add named paths under <code>file_manager_roots</code> in <code>tools/allowed_paths.json</code>.</p>
            </div>
          </div>
          <div id="dash-tree" class="tree-pane tree-pane-sm"></div>
        </section>

        <section class="card dash-health-card">
          <div class="card-head"><h3>System Health</h3></div>
          <div id="dash-health" class="health-panel">Checking…</div>
          <div class="root-management">
            <h4>Workspace folders</h4>
            <p class="text-muted small">Paste one absolute folder path per line. Add folders to the Workspace picker or remove configured folders.</p>
            <label class="small" for="dash-root-paths">Folder paths</label>
            <textarea id="dash-root-paths" class="form-input root-path-input" rows="3"
              placeholder="E:\\Novous_notes&#10;E:\\Projects"></textarea>
            <div class="root-management-actions">
              <button class="btn btn-sm btn-primary" type="button" data-root-action="add">Add folders</button>
              <button class="btn btn-sm btn-danger" type="button" data-root-action="remove">Remove folders</button>
            </div>
            <p class="small" id="dash-root-status" role="status" aria-live="polite"></p>
            <ul class="root-path-list" id="dash-root-list" aria-label="Configured Workspace folders"></ul>
          </div>
          <div class="root-management">
            <h4>Knowledge sources</h4>
            <p class="text-muted small">Each named source connects one folder to its own index. Rename sources as needed. Deleting a branch removes its saved index and entry, but never the folder or its files.</p>
            <label class="small" for="dash-rag-name">Source name</label>
            <input id="dash-rag-name" class="form-input" type="text" placeholder="Business decisions">
            <label class="small" for="dash-rag-path">Folder to search</label>
            <textarea id="dash-rag-path" class="form-input root-path-input" rows="3"
              placeholder="E:\\BUSN410\\Critical Thinking Strategies\\week 1"></textarea>
            <div class="root-management-actions">
              <button class="btn btn-sm btn-primary" type="button" data-rag-action="add">Save knowledge source</button>
            </div>
            <ul class="root-path-list rag-base-list" id="dash-rag-bases" aria-label="Saved knowledge sources"></ul>
            <div class="root-management-actions">
              <button class="btn btn-sm" type="button" data-rag-action="read">Index selected source</button>
              <button class="btn btn-sm" type="button" data-rag-action="pause">Pause</button>
              <button class="btn btn-sm" type="button" data-rag-action="resume">Resume</button>
              <button class="btn btn-sm btn-danger" type="button" data-rag-action="clear">Clear selected source index</button>
            </div>
            <p class="small" id="dash-rag-job" role="status" aria-live="polite">Loading indexing status…</p>
            <div class="root-management-actions" id="dash-rag-error-actions" hidden>
              <span class="small" id="dash-rag-error-question"></span>
              <button class="btn btn-sm" type="button" data-rag-action="error-retry">Retry this file</button>
              <button class="btn btn-sm" type="button" data-rag-action="error-skip">Skip this file</button>
              <button class="btn btn-sm btn-danger" type="button" data-rag-action="error-skip-all">Skip all remaining errors</button>
            </div>
            <p class="small" id="dash-rag-status" role="status" aria-live="polite"></p>
          </div>
        </section>
      </div>
    </div>
  `;

  const cards = container.querySelector('#dash-agent-cards');
  const codeBuilderCards = container.querySelector('#dash-codebuilder-agent-cards');
  agents.forEach(a => {
    const el = document.createElement('div');
    el.className = 'agent-card';
    el.innerHTML = `
      <div class="agent-card-head">
        <strong>${esc(a.name)}</strong>
        <span class="badge ${a.mode === 'agent' ? 'badge-accent' : 'badge-success'}">${esc(a.mode)}</span>
      </div>
      <p class="text-muted">${esc(a.description || 'No description.')}</p>
      <div class="agent-card-actions">
        <button class="btn btn-sm" data-chat="${esc(a.id)}">Chat</button>
        <button class="btn btn-sm" data-edit="${esc(a.id)}">Edit</button>
        <button class="btn btn-sm btn-danger" data-delete="${esc(a.id)}">Delete</button>
      </div>`;
    cards.appendChild(el);
  });

  cards.addEventListener('click', async (e) => {
    const t = e.target;
    if (t.dataset.chat) { switchTab('chat', t.dataset.chat); }
    else if (t.dataset.edit) { switchTab('editor', `library/${t.dataset.edit}.md`); }
    else if (t.dataset.delete) {
      if (!confirm(`Delete agent "${t.dataset.delete}"?`)) return;
      try { await Api.deleteAgent(t.dataset.delete, 'workspace'); await refreshAgents(); renderDashboardView(container); }
      catch (err) { alert(err.message); }
    }
  });

  const promptAgentCards = container.querySelector('#dash-prompt-agent-cards');
  function renderPromptAgentCards(promptAgents) {
    promptAgentCards.replaceChildren();
    if (!promptAgents.length) {
      promptAgentCards.innerHTML = '<p class="text-muted">No Prompt Creation agents yet.</p>';
      return;
    }
    promptAgents.forEach(agent => {
      const el = document.createElement('div');
      el.className = 'agent-card';
      el.innerHTML = `
        <div class="agent-card-head">
          <strong>${esc(agent.name)}</strong>
          <span class="badge badge-accent">Prompt Creation</span>
        </div>
        <p class="text-muted">${esc(agent.description || 'No description.')}</p>
        <div class="agent-card-actions">
          <button class="btn btn-sm" data-prompt-open="${esc(agent.id)}">Open Prompt Creation</button>
          <button class="btn btn-sm" data-prompt-edit="${esc(agent.id)}">Edit</button>
          <button class="btn btn-sm btn-danger" data-prompt-delete="${esc(agent.id)}">Delete</button>
        </div>`;
      promptAgentCards.appendChild(el);
    });
  }

  Api.getAgents('prompt-creation').then(data => {
    renderPromptAgentCards(data.agents || []);
  }).catch(err => {
    promptAgentCards.innerHTML = `<p class="text-danger">Could not load Prompt Creation agents: ${esc(err.message)}</p>`;
  });

  promptAgentCards.addEventListener('click', async e => {
    const button = e.target.closest('button');
    if (!button) return;
    if (button.dataset.promptOpen) {
      switchTab('prompt-creation');
    } else if (button.dataset.promptEdit) {
      switchTab('editor', `library/${button.dataset.promptEdit}.md`);
    } else if (button.dataset.promptDelete) {
      const agentId = button.dataset.promptDelete;
      if (!confirm(`Delete Prompt Creation agent "${agentId}"?`)) return;
      try {
        await Api.deleteAgent(agentId, 'prompt-creation');
        renderPromptAgentCards((await Api.getAgents('prompt-creation')).agents || []);
      } catch (err) { alert(err.message); }
    }
  });

  function renderCodeBuilderAgentCards(codeBuilderAgents) {
    codeBuilderCards.replaceChildren();
    if (!codeBuilderAgents.length) {
      codeBuilderCards.innerHTML = '<p class="text-muted">No CodeBuilder agents yet.</p>';
      return;
    }
    codeBuilderAgents.forEach(agent => {
      const el = document.createElement('div');
      el.className = 'agent-card';
      el.innerHTML = `
        <div class="agent-card-head">
          <strong>${esc(agent.name)}</strong>
          <span class="badge badge-accent">CodeBuilder</span>
        </div>
        <p class="text-muted">${esc(agent.description || 'No description.')}</p>
        <div class="agent-card-actions">
          <a class="btn btn-sm" href="/codebuilder">Open CodeBuilder</a>
          <button class="btn btn-sm" data-codebuilder-edit="${esc(agent.id)}">Edit</button>
          <button class="btn btn-sm btn-danger" data-codebuilder-delete="${esc(agent.id)}">Delete</button>
        </div>`;
      codeBuilderCards.appendChild(el);
    });
  }

  Api.getCodeBuilderAgents().then(data => {
    renderCodeBuilderAgentCards(data.agents || []);
  }).catch(err => {
    codeBuilderCards.innerHTML = `<p class="text-danger">Could not load CodeBuilder agents: ${esc(err.message)}</p>`;
  });

  codeBuilderCards.addEventListener('click', async e => {
    const editButton = e.target.closest('[data-codebuilder-edit]');
    if (editButton) {
      switchTab('editor', `library/${editButton.dataset.codebuilderEdit}.md`);
      return;
    }

    const button = e.target.closest('[data-codebuilder-delete]');
    if (!button) return;
    const agentId = button.dataset.codebuilderDelete;
    if (!confirm(`Delete CodeBuilder agent "${agentId}"?`)) return;
    try {
      await Api.deleteAgent(agentId, 'codebuilder');
      const data = await Api.getCodeBuilderAgents();
      renderCodeBuilderAgentCards(data.agents || []);
    } catch (err) { alert(err.message); }
  });

  container.querySelector('#dash-new-agent').onclick = () =>
    container.querySelector('#dash-agent-form').classList.toggle('hidden');

  container.querySelector('#dash-create-agent').onclick = async () => {
    const id = container.querySelector('#na-id').value.trim();
    const name = container.querySelector('#na-name').value.trim();
    const desc = container.querySelector('#na-desc').value.trim();
    const mode = container.querySelector('#na-mode').value;
    const environment = container.querySelector('#na-environment').value;
    const errBox = container.querySelector('#na-error');
    errBox.classList.add('hidden');
    try {
      await Api.createAgent(id, name || id, desc, mode, '', environment,
        container.querySelector('#na-environment-name').value.trim());
      await refreshAgents();
      renderDashboardView(container);
    } catch (err) { errBox.textContent = err.message; errBox.classList.remove('hidden'); }
  };

  container.querySelector('#dash-new-squad').onclick = () => {
    container.querySelector('#sq-name').classList.toggle('hidden');
    container.querySelector('#dash-create-squad').classList.toggle('hidden');
  };
  container.querySelector('#dash-create-squad').onclick = async () => {
    const input = container.querySelector('#sq-name');
    try {
      await Api.createSquad(input.value.trim());
      await refreshProject();
      renderDashboardView(container);
    } catch (err) { alert(err.message); }
  };
  container.querySelector('#dash-squad-list').addEventListener('click', async (e) => {
    const name = e.target.dataset.squadDelete;
    if (!name) return;
    if (!confirm(`Delete squad "${name}"?`)) return;
    try { await Api.deleteSquad(name); await refreshProject(); renderDashboardView(container); }
    catch (err) { alert(err.message); }
  });

  const dashboardTree = renderTree(container.querySelector('#dash-tree'), {
    manageRoots: true,
    onSelect: path => switchTab('editor', { path, managedFile: true })
  });

  const rootPathInput = container.querySelector('#dash-root-paths');
  const rootStatus = container.querySelector('#dash-root-status');
  const rootList = container.querySelector('#dash-root-list');
  const rootActionButtons = [...container.querySelectorAll('[data-root-action]')];
  async function refreshConfiguredRoots() {
    const config = await Api.getFileManagerRoots();
    rootList.replaceChildren(...config.roots.map(root => {
      const item = document.createElement('li');
      const name = document.createElement('strong');
      const path = document.createElement('code');
      name.textContent = root.name;
      path.textContent = root.path;
      item.append(name, path);
      return item;
    }));
  }
  refreshConfiguredRoots().catch(err => {
    rootStatus.textContent = `Could not load Workspace folders: ${err.message}`;
    rootStatus.className = 'small text-danger';
  });
  rootActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
      const paths = rootPathInput.value.split(/\r?\n/).map(path => path.trim()).filter(Boolean);
      if (!paths.length) {
        rootStatus.textContent = 'Paste at least one absolute folder path.';
        rootStatus.className = 'small text-danger';
        rootPathInput.focus();
        return;
      }
      rootActionButtons.forEach(actionButton => { actionButton.disabled = true; });
      rootStatus.textContent = 'Updating Workspace folders…';
      rootStatus.className = 'small text-muted';
      try {
        const result = await Api.manageFileManagerRoots(button.dataset.rootAction, paths);
        const changed = button.dataset.rootAction === 'add' ? result.added : result.removed;
        rootStatus.textContent = `${button.dataset.rootAction === 'add' ? 'Added' : 'Removed'} ${changed.length} folder(s).`;
        rootStatus.className = 'small text-success';
        await refreshConfiguredRoots();
        await dashboardTree.reload();
      } catch (err) {
        rootStatus.textContent = `Could not update Workspace folders: ${err.message}`;
        rootStatus.className = 'small text-danger';
      } finally {
        rootActionButtons.forEach(actionButton => { actionButton.disabled = false; });
      }
    });
  });

  const ragPathInput = container.querySelector('#dash-rag-path');
  const ragNameInput = container.querySelector('#dash-rag-name');
  const ragStatus = container.querySelector('#dash-rag-status');
  const ragJobStatus = container.querySelector('#dash-rag-job');
  const ragBaseList = container.querySelector('#dash-rag-bases');
  const ragButtons = [...container.querySelectorAll('[data-rag-action]')];
  let ragBases = [];
  let selectedRagBaseId = null;

  function showRagStatus(message, kind = 'muted') {
    ragStatus.textContent = message;
    ragStatus.className = `small text-${kind}`;
  }

  function describeRag(status) {
    return `${status.documents} document(s), ${status.chunks} chunk(s).`;
  }

  function renderRagBases() {
    ragBaseList.replaceChildren();
    ragBases.forEach(base => {
      const item = document.createElement('li');
      item.className = 'rag-base-item';
      item.dataset.baseId = base.id;
      const heading = document.createElement('strong');
      heading.textContent = `${base.name}${base.active ? '' : ' (archived)'}`;
      const path = document.createElement('button');
      path.type = 'button';
      path.className = 'rag-folder-link';
      path.setAttribute('aria-label', `Open folder in File Explorer: ${base.path}`);
      path.title = base.path;
      const pathCode = document.createElement('code');
      pathCode.textContent = base.path;
      path.appendChild(pathCode);
      path.disabled = !base.exists;
      path.addEventListener('click', async () => {
        try {
          await Api.openRagBaseFolder(base.id);
          showRagStatus(`Opened folder for "${base.name}" in File Explorer.`, 'success');
        } catch (error) {
          showRagStatus(`Could not open folder: ${error.message}`, 'danger');
        }
      });
      const detail = document.createElement('span');
      detail.className = 'small text-muted';
      detail.textContent = `${base.selected ? 'Selected · ' : ''}${base.exists ? 'Folder available' : 'Folder unavailable'} · ${base.documents} document(s) · ${base.chunks} chunks`;
      const actions = document.createElement('div');
      actions.className = 'root-management-actions';
      const select = document.createElement('button');
      select.type = 'button';
      select.className = 'btn btn-sm';
      select.textContent = base.selected ? 'Selected source' : 'Select source';
      select.disabled = base.selected || !base.active;
      select.addEventListener('click', async () => {
        try {
          await Api.selectRagBase(base.id);
          selectedRagBaseId = base.id;
          await loadRagBases();
          showRagStatus(`Selected "${base.name}".`, 'success');
        } catch (error) {
          showRagStatus(`Could not select source: ${error.message}`, 'danger');
        }
      });
      actions.appendChild(select);

      const rename = document.createElement('button');
      rename.type = 'button';
      rename.className = 'btn btn-sm';
      rename.textContent = 'Rename';
      rename.addEventListener('click', async () => {
        const name = prompt('New knowledge source name:', base.name);
        if (name === null || !name.trim()) return;
        try {
          await Api.renameRagBase(base.id, name);
          await loadRagBases();
          showRagStatus(`Renamed source to "${name.trim()}".`, 'success');
        } catch (error) {
          showRagStatus(`Could not rename source: ${error.message}`, 'danger');
        }
      });
      actions.appendChild(rename);

      const archive = document.createElement('button');
      archive.type = 'button';
      archive.className = base.active ? 'btn btn-sm btn-danger' : 'btn btn-sm';
      archive.textContent = base.active ? 'Archive source (keep saved)' : 'Restore source';
      archive.addEventListener('click', async () => {
        try {
          if (base.active) {
            if (!confirm(`Archive "${base.name}"? Its name, folder, and index will be kept.`)) return;
            await Api.archiveRagBase(base.id);
            showRagStatus(`Archived "${base.name}". Its folder and index are still saved.`, 'success');
          } else {
            await Api.restoreRagBase(base.id);
            selectedRagBaseId = base.id;
            showRagStatus(`Restored "${base.name}" with its saved folder and index.`, 'success');
          }
          await loadRagBases();
        } catch (error) {
          showRagStatus(`Could not update source: ${error.message}`, 'danger');
        }
      });
      actions.appendChild(archive);

      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'btn btn-sm btn-danger';
      remove.textContent = 'Delete branch';
      remove.addEventListener('click', async () => {
        if (!confirm(`Delete "${base.name}" and its indexed documents/vectors? The saved branch will be removed, but the folder and its files will NOT be deleted.`)) return;
        try {
          const result = await Api.deleteRagBase(base.id);
          await loadRagBases();
          showRagStatus(`Deleted "${result.name}" and ${result.documents_removed} indexed document(s). Folder files were left untouched.`, 'success');
        } catch (error) {
          showRagStatus(`Could not delete branch: ${error.message}`, 'danger');
        }
      });
      remove.dataset.ragDelete = 'true';
      remove.disabled = AppState.ragScanJob?.base_id === base.id &&
        ['queued', 'running', 'pausing', 'paused'].includes(AppState.ragScanJob.status);
      actions.appendChild(remove);
      item.append(heading, path, detail, actions);
      if (base.selected) item.classList.add('rag-base-selected');
      ragBaseList.appendChild(item);
    });
    if (!ragBases.length) {
      const empty = document.createElement('li');
      empty.className = 'text-muted small';
      empty.textContent = 'No saved knowledge sources yet.';
      ragBaseList.appendChild(empty);
    }
  }

  async function loadRagBases() {
    const response = await Api.getRagBases();
    ragBases = response.bases || [];
    const current = ragBases.find(base => base.selected && base.active);
    selectedRagBaseId = current?.id || ragBases.find(base => base.active)?.id || null;
    renderRagBases();
    const selected = ragBases.find(base => base.id === selectedRagBaseId);
    if (selected) {
      showRagStatus(`Selected source: ${selected.name} — ${selected.path}${selected.exists ? '' : ' (folder unavailable)'}`);
    } else {
      showRagStatus('No knowledge sources yet. Save a named source to create the first branch.');
    }
  }

  function renderRagJob(job) {
    AppState.ragScanJob = job;
    const base = ragBases.find(entry => entry.id === job.base_id);
    const baseName = job.base_name || base?.name || 'Knowledge source';
    const progress = `${job.completed || 0}/${job.discovered || 0} file(s) checked · ` +
      `${job.indexed || 0} indexed · ${job.unchanged || 0} unchanged · ` +
      `${job.skipped?.length || 0} skipped · ${job.errors?.length || 0} errors`;
    const current = job.current ? ` — ${job.current}` : '';
    const firstError = job.errors?.[0];
    const errors = job.errors?.length
      ? `; ${job.errors.length} error(s), e.g. ${firstError.path || ''} — ${firstError.error || 'see server log'}`
      : '';
    const pending = job.pending_error
      ? `File needs your choice: ${job.pending_error.path} — ${job.pending_error.error}`
      : '';
    const schedule = job.resume_at
      ? `; scheduled resume ${new Date(job.resume_at).toLocaleString()}`
      : '';
    const state = {
      queued: 'Starting',
      running: 'Indexing',
      pausing: 'Pausing after current file',
      awaiting_decision: 'Waiting for your choice',
      paused: 'Paused',
      completed: 'Complete',
      completed_with_skips: 'Complete (files skipped by choice)',
      completed_with_errors: 'Complete with errors',
      unavailable: 'Folder unavailable'
    }[job.status] || job.status;
    ragJobStatus.textContent = job.status === 'idle'
      ? 'Index status: Waiting to start.'
      : `${baseName}: ${state} — ${progress}${pending ? ` — ${pending}` : errors}${schedule}${current}`;
    ragJobStatus.className = `small ${
      ['completed', 'completed_with_skips', 'running', 'queued'].includes(job.status) ? 'text-success'
        : ['paused', 'pausing', 'awaiting_decision'].includes(job.status) ? 'text-warning'
          : ['failed', 'completed_with_errors', 'unavailable'].includes(job.status) ? 'text-danger'
            : 'text-muted'
    }`;
    const active = ['queued', 'running', 'pausing'].includes(job.status);
    const blocksMutation = ['queued', 'running', 'pausing', 'paused', 'awaiting_decision'].includes(job.status);
    const selectedJob = !job.base_id || job.base_id === selectedRagBaseId;
    container.querySelector('[data-rag-action="read"]').disabled = active;
    container.querySelector('[data-rag-action="pause"]').disabled = !active || job.status === 'pausing';
    container.querySelector('[data-rag-action="resume"]').disabled =
      !selectedJob || !['paused', 'unavailable', 'failed'].includes(job.status);
    container.querySelector('[data-rag-action="clear"]').disabled =
      !selectedRagBaseId || blocksMutation;
    const errorActions = container.querySelector('#dash-rag-error-actions');
    errorActions.hidden = job.status !== 'awaiting_decision';
    container.querySelector('#dash-rag-error-question').textContent = job.pending_error
      ? `Retry this file, skip only it (ask again next time), or skip all remaining errors?`
      : '';
    errorActions.querySelectorAll('button').forEach(button => {
      button.disabled = job.status !== 'awaiting_decision';
    });
    ragBaseList.querySelectorAll('.rag-base-item').forEach(item => {
      const button = item.querySelector('[data-rag-delete]');
      if (button) {
        button.disabled = blocksMutation && job.base_id === item.dataset.baseId;
      }
    });
  }

  async function refreshRagJob() {
    try {
      renderRagJob(await Api.getRagScan());
    } catch (error) {
      ragJobStatus.textContent = `Could not load indexing status: ${error.message}`;
      ragJobStatus.className = 'small text-danger';
    }
  }

  loadRagBases().then(refreshRagJob).catch(error => {
    showRagStatus(`Could not load RAG settings: ${error.message}`, 'danger');
  });

  ragButtons.forEach(button => {
    button.addEventListener('click', async () => {
      const action = button.dataset.ragAction;
      if (!selectedRagBaseId) {
        showRagStatus('Save or select a knowledge source first.', 'warning');
        return;
      }
      const base = ragBases.find(item => item.id === selectedRagBaseId);
      if (action === 'clear' &&
          !confirm(`Clear only the saved index for "${base?.name}"? The saved name, folder, and files will remain.`)) return;
      if (['read', 'pause', 'resume', 'clear', 'error-retry', 'error-skip', 'error-skip-all'].includes(action)) {
        button.disabled = true;
      }
      try {
        if (action === 'add') {
          const name = ragNameInput.value.trim();
          const path = ragPathInput.value.trim();
          if (!name || !path) {
            showRagStatus('Enter a source name and the complete folder path.', 'warning');
            return;
          }
          const added = await Api.addRagBase(name, path);
          ragNameInput.value = '';
          ragPathInput.value = '';
          selectedRagBaseId = added.id;
          await loadRagBases();
          showRagStatus(`Saved source "${added.name}" for ${added.path}.`, 'success');
        } else if (action === 'read') {
          const job = await Api.reindexRag(selectedRagBaseId);
          renderRagJob(job);
          if (job.status === 'paused') {
            showRagStatus(
              `The previous scan for "${base?.name}" is still paused. Resume it to retry unfinished files.`,
              'warning'
            );
          } else if (['queued', 'running'].includes(job.status)) {
            showRagStatus(`Indexing started for "${base?.name}".`, 'success');
          } else {
            showRagStatus(`The scan was not started (status: ${job.status}).`, 'warning');
          }
        } else if (action === 'pause') {
          renderRagJob(await Api.pauseRagScan());
          showRagStatus('Indexing paused after the current file finishes.', 'success');
        } else if (action === 'resume') {
          renderRagJob(await Api.resumeRagScan());
          showRagStatus('Indexing resumed.', 'success');
        } else if (action.startsWith('error-')) {
          const decision = {
            'error-retry': 'retry',
            'error-skip': 'skip',
            'error-skip-all': 'skip_all'
          }[action];
          renderRagJob(await Api.decideRagScanError(decision));
          showRagStatus(
            decision === 'retry' ? 'Retrying the failed file.'
              : decision === 'skip' ? 'Skipped this file; Novous will ask again if another file fails.'
                : 'Skipping all remaining file errors automatically.',
            'success'
          );
        } else if (action === 'clear') {
          const result = await Api.clearRagIndex(selectedRagBaseId);
          await loadRagBases();
          showRagStatus(`Cleared ${result.removed} indexed document(s) from "${base?.name}".`, 'success');
        }
      } catch (err) {
        showRagStatus(err.message, 'danger');
      } finally {
        await refreshRagJob();
      }
    });
  });
  const ragRefreshInterval = setInterval(() => {
    if (!container.isConnected) {
      clearInterval(ragRefreshInterval);
      return;
    }
    refreshRagJob();
  }, 1500);

  const healthBox = container.querySelector('#dash-health');
  Api.getHealth().then(h => {
    AppState.health = h;
    healthBox.innerHTML = `
      <div class="health-row"><span>API</span><span class="badge badge-success">ok</span></div>
      <div class="health-row"><span>Ollama</span>
        <span class="badge ${h.ollama?.reachable ? 'badge-success' : 'badge-warning'}">
          ${h.ollama?.reachable ? 'connected' : 'offline'}</span></div>
      <p class="text-muted small">${esc(h.ollama?.detail || '')}</p>
      <p class="text-muted small">Uptime: ${esc(h.uptime_seconds)}s</p>`;
    updateHealthBadge(h);
  }).catch(() => { healthBox.innerHTML = '<p class="text-danger">API unreachable.</p>'; });
}

// --- Shared helpers --------------------------------------------------------
export async function refreshAgents() {
  const data = await Api.getAgents();
  AppState.agents = data.agents || [];
  return AppState.agents;
}

export async function refreshProject() {
  AppState.project = await Api.getProjectState();
  return AppState.project;
}

export function updateHealthBadge(health) {
  const badge = document.getElementById('health-badge');
  if (!badge || !health) return;
  const ok = health.ollama?.reachable;
  badge.className = 'badge ' + (ok ? 'badge-success' : 'badge-warning');
  badge.textContent = ok ? 'Engine Ready' : 'Ollama Offline';
}

export function switchTab(tab, payload = null) {
  AppState.activeTab = tab;
  document.querySelectorAll('.nav-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tab));
  const container = document.getElementById('view-container');
  if (!container) return;
  const renderer = views[tab];
  if (renderer) renderer(container, payload);
}

window.addEventListener('novous:open-editor', event => {
  const file = event.detail;
  if (file && typeof file.path === 'string') {
    switchTab('editor', { path: file.path, managedFile: file.managedFile === true });
  }
});

async function boot() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  try {
    await Promise.all([refreshAgents(), refreshProject()]);
  } catch (err) {
    document.getElementById('view-container').innerHTML =
      `<div class="error-panel">Failed to load workspace: ${esc(err.message)}</div>`;
    return;
  }

  try {
    const h = await Api.getHealth();
    AppState.health = h;
    updateHealthBadge(h);
  } catch (_) { /* badge stays default */ }

  const requestedTab = new URLSearchParams(window.location.search).get('tab');
  switchTab(Object.prototype.hasOwnProperty.call(views, requestedTab) ? requestedTab : 'dashboard');
}

boot();
