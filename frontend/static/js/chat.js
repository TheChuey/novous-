import { Api } from './api.js';
import { createIcon } from './icons.js';
import { buildTestPanel } from './test_panel.js';
import { openTestSuiteRunner } from './test_suite_runner.js';
import { renderTree } from './tree.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

/**
 * Interactive Chat Console Component: agent selection, message history,
 * and tool execution badges.
 */
export function renderChatView(container) {
  container.innerHTML = `
    <div class="chat-layout">
      <aside class="chat-file-sidebar">
        <div class="chat-file-header">
          <h3>Workspace Files</h3>
          <span class="text-muted small">Open a file in the editor</span>
        </div>
        <div id="chat-file-tree" class="tree-pane"></div>
      </aside>

      <section class="chat-main">
        <div class="chat-font-controls" role="group" aria-label="Chat text size">
          <span class="text-muted small">Text size</span>
          <button type="button" class="btn btn-sm" id="chat-font-smaller"
            title="Smaller text" aria-label="Decrease chat text size">A−</button>
          <button type="button" class="btn btn-sm" id="chat-font-larger"
            title="Larger text" aria-label="Increase chat text size">A+</button>
        </div>
        <div id="chat-messages" class="messages-scroll">
          <div class="message system-msg">Select an agent and send a message to start reasoning.</div>
        </div>
        <form id="chat-form" class="chat-input-bar">
          <input type="text" id="chat-input" placeholder="Type a message or instruction..." autocomplete="off" required />
          <button type="submit" class="btn btn-primary" disabled>Send</button>
        </form>
        <div class="chat-quick-actions">
          <button type="button" class="btn btn-sm" id="chat-reset-quick" disabled>Reset session</button>
        </div>
      </section>

      <aside class="test-panel">
        <div class="test-panel-header">
          <span class="test-panel-title">Chat & Test Controls</span>
        </div>
        <div class="test-panel-content">
          <div id="testPanelButtons" class="test-grid"></div>
          <section class="chat-controls">
            <h3 class="chat-controls-title">Chat settings</h3>
            <label class="chat-field-label" for="chat-agent-select">Agent</label>
            <select id="chat-agent-select" class="form-select">
              <option value="">Loading agents...</option>
            </select>
            <div id="agent-meta-card" class="card chat-agent-meta">
              <p class="text-muted">Select an agent to begin chatting.</p>
            </div>
            <label class="checkbox-row">
              <input type="checkbox" id="chat-use-tools" checked>
              <span>Attach tools (agent mode)</span>
            </label>
            <label class="model-picker">
              <span class="model-picker-label">Model <span id="model-count" class="text-muted small"></span></span>
              <select id="chat-model-select" class="form-select" disabled><option value="">Detecting models…</option></select>
            </label>
            <div class="chat-session-buttons">
              <button class="btn btn-sm btn-primary" id="chat-save-log" disabled>Save Session Log (.md)</button>
              <button class="btn btn-sm" id="chat-reset" disabled>Reset session</button>
            </div>
            <div id="chat-session-info" class="text-muted small"></div>
          </section>
        </div>
      </aside>
    </div>
    <dialog id="chat-scratchpad-dialog" class="scratchpad-dialog">
      <div class="scratchpad-dialog-head">
        <div>
          <h2>Agent Scratchpad</h2>
          <p class="text-muted small">Recent file reads and the latest workspace map.</p>
        </div>
        <button type="button" class="btn btn-sm" data-scratchpad-close aria-label="Close">Close</button>
      </div>
      <div id="chat-scratchpad-content" class="scratchpad-content"></div>
    </dialog>
    <dialog id="chat-knowledge-catalog-dialog" class="scratchpad-dialog">
      <div class="scratchpad-dialog-head">
        <div>
          <h2>Knowledge TOC</h2>
          <p class="text-muted small">Live catalog of saved knowledge branches. Expand a branch to see its indexed documents.</p>
        </div>
        <div class="root-management-actions">
          <button type="button" class="btn btn-sm" data-catalog-refresh>Refresh</button>
          <button type="button" class="btn btn-sm" data-catalog-close aria-label="Close">Close</button>
        </div>
      </div>
      <div id="chat-knowledge-catalog-content" class="scratchpad-content" aria-live="polite"></div>
    </dialog>
    <dialog id="chat-rag-dialog" class="scratchpad-dialog">
      <div class="scratchpad-dialog-head">
        <div>
          <h2>Knowledge sources</h2>
          <p class="text-muted small">Each named branch links one folder to its own searchable index. Deleting a branch removes its saved index, not the folder or its files.</p>
        </div>
        <button type="button" class="btn btn-sm" data-rag-close aria-label="Close">Close</button>
      </div>
      <section class="scratchpad-section">
        <label class="chat-field-label" for="chat-rag-base">Choose a source</label>
        <select id="chat-rag-base" class="form-select"></select>
        <form id="chat-rag-base-form" class="rag-add-form">
          <h3>Add a folder</h3>
          <label class="small" for="chat-rag-base-name">Source name</label>
          <input id="chat-rag-base-name" class="form-input" type="text" placeholder="Business decisions" required>
          <label class="small" for="chat-rag-base-path">Folder to search</label>
          <textarea id="chat-rag-base-path" class="form-input root-path-input" rows="2" placeholder="E:\\BUSN410\\Critical Thinking Strategies\\week 1" required></textarea>
          <button type="submit" class="btn btn-sm">Save source</button>
          <button id="chat-rag-archive" type="button" class="btn btn-sm btn-danger">Archive source</button>
          <button id="chat-rag-rename" type="button" class="btn btn-sm">Rename source</button>
          <button id="chat-rag-delete" type="button" class="btn btn-sm btn-danger">Delete branch</button>
        </form>
        <p id="chat-rag-job" class="small text-muted" role="status" aria-live="polite"></p>
        <div id="chat-rag-error-actions" class="root-management-actions" hidden>
          <span class="small">Retry this file, skip just this one and ask again, or skip all remaining errors?</span>
          <button id="chat-rag-error-retry" type="button" class="btn btn-sm">Retry file</button>
          <button id="chat-rag-error-skip" type="button" class="btn btn-sm">Skip this file</button>
          <button id="chat-rag-error-skip-all" type="button" class="btn btn-sm btn-danger">Skip all errors</button>
        </div>
        <div class="root-management-actions">
          <button id="chat-rag-scan" type="button" class="btn btn-sm btn-primary">Index selected source</button>
          <button id="chat-rag-pause" type="button" class="btn btn-sm">Pause</button>
          <button id="chat-rag-resume" type="button" class="btn btn-sm">Resume</button>
        </div>
        <div class="root-management-actions">
          <label class="small" for="chat-rag-resume-at">Resume at</label>
          <input id="chat-rag-resume-at" class="form-input" type="datetime-local">
          <button id="chat-rag-schedule" type="button" class="btn btn-sm">Schedule resume</button>
        </div>
      </section>
      <div id="chat-rag-content" class="scratchpad-content"></div>
      <form id="chat-rag-form" class="rag-add-form">
        <h3>Add text to this source</h3>
        <input id="chat-rag-title" class="form-input" type="text" placeholder="Text title (same title replaces it)" required>
        <textarea id="chat-rag-text" class="form-input" rows="4" placeholder="Text to add to this source" required></textarea>
        <div class="root-management-actions">
          <button type="submit" class="btn btn-sm btn-primary">Add text</button>
          <button type="button" class="btn btn-sm" data-rag-refresh>Refresh</button>
        </div>
        <p class="small" id="chat-rag-status" role="status" aria-live="polite"></p>
      </form>
    </dialog>`;

  const agentSelect = container.querySelector('#chat-agent-select');
  const metaCard = container.querySelector('#agent-meta-card');
  const messagesBox = container.querySelector('#chat-messages');
  const chatForm = container.querySelector('#chat-form');
  const chatInput = container.querySelector('#chat-input');
  const sendButton = chatForm.querySelector('[type="submit"]');
  const saveLogButton = container.querySelector('#chat-save-log');
  const resetButton = container.querySelector('#chat-reset');
  const quickResetButton = container.querySelector('#chat-reset-quick');
  const toolsToggle = container.querySelector('#chat-use-tools');
  const sessionInfo = container.querySelector('#chat-session-info');
  const modelSelect = container.querySelector('#chat-model-select');
  const modelCount = container.querySelector('#model-count');
  const scratchpadDialog = container.querySelector('#chat-scratchpad-dialog');
  const scratchpadContent = container.querySelector('#chat-scratchpad-content');
  const chatMain = container.querySelector('.chat-main');

  function renderScratchpad(memory) {
    scratchpadContent.replaceChildren();
    const reads = Array.isArray(memory.read_history)
      ? memory.read_history
      : (memory.latest_read ? [memory.latest_read] : []);

    const readsSection = document.createElement('section');
    readsSection.className = 'scratchpad-section';
    const readsTitle = document.createElement('h3');
    readsTitle.textContent = `Recent reads (${reads.length})`;
    readsSection.appendChild(readsTitle);
    if (!reads.length) {
      const empty = document.createElement('p');
      empty.className = 'text-muted';
      empty.textContent = 'No file reads are saved.';
      readsSection.appendChild(empty);
    }
    [...reads].reverse().forEach((entry, index) => {
      const details = document.createElement('details');
      details.className = 'scratchpad-read';
      if (index === 0) details.open = true;
      const summary = document.createElement('summary');
      const timestamp = entry.updated_at ? new Date(entry.updated_at).toLocaleString() : '';
      summary.textContent = [entry.path || 'Unknown file', timestamp].filter(Boolean).join(' · ');
      const request = document.createElement('p');
      request.className = 'text-muted small';
      request.textContent = entry.request ? `Request: ${entry.request}` : 'No request context.';
      const content = document.createElement('pre');
      content.textContent = entry.content || '';
      details.append(summary, request, content);
      readsSection.appendChild(details);
    });
    scratchpadContent.appendChild(readsSection);

    const mapSection = document.createElement('section');
    mapSection.className = 'scratchpad-section';
    const mapTitle = document.createElement('h3');
    mapTitle.textContent = 'Latest workspace map';
    mapSection.appendChild(mapTitle);
    if (memory.latest_map?.tree) {
      const path = document.createElement('p');
      path.className = 'text-muted small';
      path.textContent = memory.latest_map.requested_path || 'Workspace root';
      const tree = document.createElement('div');
      tree.className = 'scratchpad-tree';
      tree.appendChild(createScratchpadTreeNode(memory.latest_map.tree, true));
      mapSection.append(path, tree);
    } else {
      const empty = document.createElement('p');
      empty.className = 'text-muted';
      empty.textContent = 'No workspace map is saved.';
      mapSection.appendChild(empty);
    }
    scratchpadContent.appendChild(mapSection);
  }

  function createScratchpadTreeNode(node, isRoot = false) {
    const list = document.createElement('ul');
    list.className = 'scratchpad-tree-list';
    (node.children || []).forEach(child => {
      const item = document.createElement('li');
      if (child.type === 'directory') {
        const details = document.createElement('details');
        const summary = document.createElement('summary');
        summary.textContent = `📁 ${child.name}`;
        details.append(summary, createScratchpadTreeNode(child));
        item.appendChild(details);
      } else {
        const openFile = document.createElement('button');
        openFile.type = 'button';
        openFile.className = 'scratchpad-file-link';
        openFile.textContent = `📄 ${child.name}`;
        openFile.title = child.path;
        openFile.addEventListener('click', () => {
          if (document.getElementById('app')) {
            window.dispatchEvent(new CustomEvent('novous:open-editor', {
              detail: { path: child.path, managedFile: true }
            }));
          } else {
            const params = new URLSearchParams({ path: child.path, managed: '1' });
            window.location.assign(`/editor?${params}`);
          }
          scratchpadDialog.close();
        });
        item.appendChild(openFile);
      }
      list.appendChild(item);
    });
    if (isRoot) {
      const root = document.createElement('details');
      root.open = true;
      const summary = document.createElement('summary');
      summary.textContent = `📁 ${node.name || 'Workspace'}`;
      root.append(summary, list);
      return root;
    }
    return list;
  }

  async function loadScratchpad() {
    scratchpadContent.textContent = 'Loading scratchpad…';
    try {
      renderScratchpad(await Api.getAgentScratchpad());
    } catch (error) {
      scratchpadContent.textContent = `Could not load scratchpad: ${error.message}`;
    }
  }

  async function openScratchpad() {
    scratchpadDialog.showModal();
    await loadScratchpad();
  }

  container.querySelector('[data-scratchpad-close]').addEventListener('click', () => {
    scratchpadDialog.close();
  });

  const knowledgeCatalogDialog = container.querySelector('#chat-knowledge-catalog-dialog');
  const knowledgeCatalogContent = container.querySelector('#chat-knowledge-catalog-content');

  async function loadKnowledgeCatalog() {
    knowledgeCatalogContent.textContent = 'Loading knowledge catalog…';
    try {
      const { bases } = await Api.getRagBases();
      knowledgeCatalogContent.replaceChildren();
      if (!bases.length) {
        const empty = document.createElement('p');
        empty.className = 'text-muted';
        empty.textContent = 'No knowledge branches have been saved yet.';
        knowledgeCatalogContent.appendChild(empty);
        return;
      }
      const list = document.createElement('div');
      list.className = 'knowledge-catalog-list';
      bases.forEach(base => {
        const branch = document.createElement('details');
        branch.className = 'knowledge-catalog-branch';
        const summary = document.createElement('summary');
        summary.textContent = base.name;
        const metadata = document.createElement('div');
        metadata.className = 'knowledge-catalog-meta small text-muted';
        metadata.textContent = `${base.active ? 'Active' : 'Archived'}${base.selected ? ' · Selected' : ''} · ${base.documents} document(s) · ${base.chunks} chunks`;
        const id = document.createElement('code');
        id.className = 'knowledge-catalog-id';
        id.textContent = `Branch ID: ${base.id}`;
        const documents = document.createElement('ul');
        documents.className = 'knowledge-catalog-documents';
        let loaded = false;
        branch.addEventListener('toggle', async () => {
          if (!branch.open || loaded) return;
          loaded = true;
          const loading = document.createElement('li');
          loading.className = 'text-muted small';
          loading.textContent = 'Loading indexed documents…';
          documents.replaceChildren(loading);
          try {
            const overview = await Api.getRagDocuments(base.id);
            documents.replaceChildren();
            if (!overview.files?.length) {
              const empty = document.createElement('li');
              empty.className = 'text-muted small';
              empty.textContent = 'No indexed documents.';
              documents.appendChild(empty);
            } else {
              overview.files.forEach(file => {
                const item = document.createElement('li');
                item.textContent = `${file.name} · ${file.chunks} chunk(s)`;
                item.title = file.path;
                documents.appendChild(item);
              });
            }
          } catch (error) {
            loaded = false;
            documents.replaceChildren();
            const failure = document.createElement('li');
            failure.className = 'text-danger small';
            failure.textContent = `Could not load documents: ${error.message}`;
            documents.appendChild(failure);
          }
        });
        branch.append(summary, metadata, id, documents);
        list.appendChild(branch);
      });
      knowledgeCatalogContent.appendChild(list);
    } catch (error) {
      knowledgeCatalogContent.textContent = `Could not load knowledge catalog: ${error.message}`;
    }
  }

  async function openKnowledgeCatalog() {
    knowledgeCatalogDialog.showModal();
    await loadKnowledgeCatalog();
  }

  container.querySelector('[data-catalog-close]')
    .addEventListener('click', () => knowledgeCatalogDialog.close());
  container.querySelector('[data-catalog-refresh]')
    .addEventListener('click', loadKnowledgeCatalog);

  const ragDialog = container.querySelector('#chat-rag-dialog');
  const ragContent = container.querySelector('#chat-rag-content');
  const ragStatus = container.querySelector('#chat-rag-status');
  const ragForm = container.querySelector('#chat-rag-form');
  const ragBaseSelect = container.querySelector('#chat-rag-base');
  const ragJobStatus = container.querySelector('#chat-rag-job');
  let activeRagBaseId = null;
  let ragBases = [];
  let viewingArchivedBase = false;
  let ragPollInterval = null;

  function showRagStatus(message, kind = 'muted') {
    ragStatus.textContent = message;
    ragStatus.className = `small text-${kind}`;
  }

  function renderRag(overview) {
    ragContent.replaceChildren();
    const summary = document.createElement('p');
    const typeText = Object.entries(overview.types || {})
      .sort((a, b) => b[1] - a[1])
      .map(([type, count]) => `${type}: ${count}`).join(', ') || 'none';
    summary.textContent = `${overview.name || 'Selected source'} — ${overview.documents} document(s), ${overview.chunks} chunks. Types: ${typeText}.`;
    const folder = document.createElement('p');
    folder.className = 'text-muted small';
    folder.textContent = `${overview.path}${overview.exists ? '' : ' (folder unavailable)'}`;
    ragContent.append(summary, folder);

    const files = overview.files || [];
    if (!files.length) {
      const empty = document.createElement('p');
      empty.className = 'text-muted';
      empty.textContent = 'No information has been indexed from this folder yet.';
      ragContent.appendChild(empty);
      return;
    }
    const list = document.createElement('ul');
    list.className = 'rag-file-list';
    files.forEach(file => {
      const item = document.createElement('li');
      const name = document.createElement('span');
      name.className = 'rag-file-name';
      name.textContent = file.name;
      name.title = file.path;
      const meta = document.createElement('span');
      meta.className = file.chunks ? 'text-muted small' : 'text-danger small';
      meta.textContent = `${file.type} · ${file.chunks} chunk(s)`;
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'btn btn-sm btn-danger';
      remove.textContent = 'Delete';
      remove.disabled = viewingArchivedBase;
      remove.addEventListener('click', async () => {
        if (!confirm(`Remove "${file.name}" from the RAG index? Files on disk are not touched.`)) return;
        try {
          await Api.deleteRagDocument(file.path, activeRagBaseId);
          showRagStatus(`Removed ${file.name}.`, 'success');
          await loadRag();
        } catch (error) {
          showRagStatus(`Could not delete: ${error.message}`, 'danger');
        }
      });
      item.append(name, meta, remove);
      list.appendChild(item);
    });
    ragContent.appendChild(list);
  }

  async function loadRag() {
    try {
      const { bases } = await Api.getRagBases();
      ragBases = bases;
      const selected = bases.find(base => base.selected && base.active);
      activeRagBaseId = selected?.id || bases.find(base => base.active)?.id || bases[0]?.id || null;
      viewingArchivedBase = Boolean(
        activeRagBaseId && !bases.find(base => base.id === activeRagBaseId)?.active
      );
      container.querySelector('#chat-rag-form [type="submit"]').disabled =
        !activeRagBaseId || viewingArchivedBase;
      ragBaseSelect.replaceChildren();
      if (!bases.length) {
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = 'No sources yet';
        ragBaseSelect.appendChild(emptyOption);
      }
      bases.forEach(base => {
        const option = document.createElement('option');
        option.value = base.id;
        option.textContent = `${base.name}${base.active ? '' : ' (archived)'}`;
        option.selected = base.id === activeRagBaseId;
        ragBaseSelect.appendChild(option);
      });
      updateRagBaseAction();
      if (activeRagBaseId) {
        renderRag(await Api.getRagDocuments(activeRagBaseId));
      } else {
        ragContent.textContent = 'No knowledge branches yet. Add a named source folder to create one.';
      }
    } catch (error) {
      ragContent.textContent = `Could not load the RAG index: ${error.message}`;
    }
    await loadRagScan();
  }

  function updateRagBaseAction() {
    const button = container.querySelector('#chat-rag-archive');
    const selected = ragBases.find(base => base.id === ragBaseSelect.value);
    const restoring = selected && !selected.active;
    button.textContent = restoring ? 'Restore source' : 'Archive source';
    button.disabled = !selected;
    container.querySelector('#chat-rag-rename').disabled = !selected;
    container.querySelector('#chat-rag-delete').disabled = !selected;
  }

  async function loadRagScan() {
    try {
      const job = await Api.getRagScan();
      const isActive = ['queued', 'running', 'pausing'].includes(job.status);
      const blocksMutation = ['queued', 'running', 'pausing', 'paused', 'awaiting_decision'].includes(job.status);
      const progress = `${job.completed || 0}/${job.discovered || 0} checked · ` +
        `${job.indexed || 0} indexed · ${job.unchanged || 0} unchanged · ` +
        `${job.skipped?.length || 0} skipped · ${job.errors?.length || 0} errors`;
      const current = job.current ? ` — ${job.current}` : '';
      const firstError = job.errors?.[0];
      const errorSummary = job.errors?.length
        ? `; ${job.errors.length} error(s), e.g. ${firstError.path || ''} — ${firstError.error || 'see server log'}`
        : '';
      const pending = job.pending_error
        ? ` Needs your choice for ${job.pending_error.path}: ${job.pending_error.error}`
        : '';
      const schedule = job.resume_at
        ? `; scheduled to resume ${new Date(job.resume_at).toLocaleString()}`
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
        unavailable: 'Folder unavailable',
        failed: 'Failed'
      }[job.status] || job.status;
      ragJobStatus.textContent = job.status === 'idle'
        ? 'Index status: Waiting to start.'
        : `${job.base_name || 'Source'}: ${state} — ${progress}${pending || errorSummary}${schedule}${current}`;
      ragJobStatus.className = `small ${
        ['completed', 'completed_with_skips', 'running', 'queued'].includes(job.status) ? 'text-success'
          : ['paused', 'pausing', 'awaiting_decision'].includes(job.status) ? 'text-warning'
            : ['failed', 'completed_with_errors', 'unavailable'].includes(job.status) ? 'text-danger'
              : 'text-muted'
      }`;
      container.querySelector('#chat-rag-pause').disabled = !isActive;
      container.querySelector('#chat-rag-resume').disabled =
        job.status !== 'paused' && job.status !== 'unavailable' && job.status !== 'failed';
      container.querySelector('#chat-rag-scan').disabled =
        !activeRagBaseId || viewingArchivedBase || isActive;
      container.querySelector('#chat-rag-schedule').disabled = job.status !== 'paused';
      const errorActions = container.querySelector('#chat-rag-error-actions');
      errorActions.hidden = job.status !== 'awaiting_decision';
      errorActions.querySelectorAll('button').forEach(button => {
        button.disabled = job.status !== 'awaiting_decision';
      });
      const selectedBase = ragBases.find(base => base.id === ragBaseSelect.value);
      container.querySelector('#chat-rag-delete').disabled =
        !selectedBase || (blocksMutation && job.base_id === selectedBase.id);
    } catch (error) {
      ragJobStatus.textContent = `Could not load indexing status: ${error.message}`;
    }
  }

  async function openRag() {
    ragDialog.showModal();
    ragContent.textContent = 'Loading RAG index…';
    showRagStatus('');
    const resumeInput = container.querySelector('#chat-rag-resume-at');
    const suggestedResume = new Date(Date.now() + 60 * 60 * 1000);
    suggestedResume.setMinutes(suggestedResume.getMinutes() - suggestedResume.getTimezoneOffset());
    resumeInput.value = suggestedResume.toISOString().slice(0, 16);
    await loadRag();
    if (ragPollInterval) clearInterval(ragPollInterval);
    ragPollInterval = setInterval(() => {
      if (ragDialog.open) {
        loadRagScan();
      } else {
        clearInterval(ragPollInterval);
        ragPollInterval = null;
      }
    }, 1500);
  }

  container.querySelector('[data-rag-close]').addEventListener('click', () => ragDialog.close());
  ragDialog.addEventListener('close', () => {
    if (ragPollInterval) clearInterval(ragPollInterval);
    ragPollInterval = null;
  });
  ragBaseSelect.addEventListener('change', async () => {
    const selected = ragBases.find(base => base.id === ragBaseSelect.value);
    if (selected && !selected.active) {
      activeRagBaseId = selected.id;
      updateRagBaseAction();
      showRagStatus(`"${selected.name}" is archived. Its index is preserved and can still be searched by agents.`, 'muted');
      viewingArchivedBase = true;
      container.querySelector('#chat-rag-form [type="submit"]').disabled = true;
      container.querySelector('#chat-rag-scan').disabled = true;
      renderRag(await Api.getRagDocuments(selected.id));
      return;
    }
    try {
      await Api.selectRagBase(ragBaseSelect.value);
      activeRagBaseId = ragBaseSelect.value;
      viewingArchivedBase = false;
      container.querySelector('#chat-rag-form [type="submit"]').disabled = false;
      await loadRag();
    } catch (error) {
      showRagStatus(`Could not select source: ${error.message}`, 'danger');
    }
  });
  container.querySelector('#chat-rag-base-form').addEventListener('submit', async event => {
    event.preventDefault();
    const name = container.querySelector('#chat-rag-base-name');
    const path = container.querySelector('#chat-rag-base-path');
    try {
      const base = await Api.addRagBase(name.value, path.value);
      name.value = '';
      path.value = '';
      activeRagBaseId = base.id;
      showRagStatus(`Added "${base.name}".`, 'success');
      await loadRag();
    } catch (error) {
      showRagStatus(`Could not save source: ${error.message}`, 'danger');
    }
  });
  container.querySelector('#chat-rag-archive').addEventListener('click', async () => {
    const selectedBase = ragBases.find(base => base.id === ragBaseSelect.value);
    if (!selectedBase) return;
    try {
      if (selectedBase.active) {
        if (!confirm(`Archive "${selectedBase.name}"? Its folder and indexed information will be kept.`)) return;
        await Api.archiveRagBase(selectedBase.id);
        showRagStatus('Source archived. Its folder and indexed information were kept.', 'success');
      } else {
        await Api.restoreRagBase(selectedBase.id);
        showRagStatus('Source restored with its saved folder and indexed information.', 'success');
      }
      await loadRag();
    } catch (error) {
      showRagStatus(`Could not update source: ${error.message}`, 'danger');
    }
  });
  container.querySelector('#chat-rag-rename').addEventListener('click', async () => {
    const selectedBase = ragBases.find(base => base.id === ragBaseSelect.value);
    if (!selectedBase) return;
    const name = prompt('New knowledge source name:', selectedBase.name);
    if (name === null || !name.trim()) return;
    try {
      await Api.renameRagBase(selectedBase.id, name);
      showRagStatus(`Renamed source to "${name.trim()}".`, 'success');
      await loadRag();
    } catch (error) {
      showRagStatus(`Could not rename source: ${error.message}`, 'danger');
    }
  });
  container.querySelector('#chat-rag-delete').addEventListener('click', async () => {
    const selectedBase = ragBases.find(base => base.id === ragBaseSelect.value);
    if (!selectedBase) return;
    if (!confirm(`Delete "${selectedBase.name}" and its indexed documents/vectors? The branch will be removed, but its folder and files will NOT be deleted.`)) return;
    try {
      const result = await Api.deleteRagBase(selectedBase.id);
      showRagStatus(`Deleted "${result.name}" and ${result.documents_removed} indexed document(s). Folder files were left untouched.`, 'success');
      await loadRag();
    } catch (error) {
      showRagStatus(`Could not delete branch: ${error.message}`, 'danger');
      await loadRagScan();
    }
  });
  container.querySelector('#chat-rag-scan').addEventListener('click', async () => {
    try {
      await Api.reindexRag();
      await loadRagScan();
    } catch (error) {
      showRagStatus(`Could not start indexing: ${error.message}`, 'danger');
      await loadRagScan();
    }
  });
  container.querySelector('#chat-rag-pause').addEventListener('click', async () => {
    try {
      await Api.pauseRagScan();
      await loadRagScan();
    } catch (error) {
      showRagStatus(`Could not pause indexing: ${error.message}`, 'danger');
    }
  });
  container.querySelector('#chat-rag-resume').addEventListener('click', async () => {
    try {
      await Api.resumeRagScan();
      await loadRagScan();
    } catch (error) {
      showRagStatus(`Could not resume indexing: ${error.message}`, 'danger');
      await loadRagScan();
    }
  });
  [
    ['#chat-rag-error-retry', 'retry'],
    ['#chat-rag-error-skip', 'skip'],
    ['#chat-rag-error-skip-all', 'skip_all']
  ].forEach(([selector, decision]) => {
    container.querySelector(selector).addEventListener('click', async event => {
      event.currentTarget.disabled = true;
      try {
        await Api.decideRagScanError(decision);
        showRagStatus(
          decision === 'retry' ? 'Retrying the failed file.'
            : decision === 'skip' ? 'Skipped this file; Novous will ask again if another file fails.'
              : 'Skipping all remaining file errors automatically.',
          'success'
        );
        await loadRagScan();
      } catch (error) {
        showRagStatus(`Could not apply scan choice: ${error.message}`, 'danger');
        await loadRagScan();
      }
    });
  });
  container.querySelector('#chat-rag-schedule').addEventListener('click', async () => {
    const value = container.querySelector('#chat-rag-resume-at').value;
    if (!value) {
      showRagStatus('Choose a time to resume indexing.', 'danger');
      return;
    }
    try {
      await Api.scheduleRagResume(new Date(value).toISOString());
      showRagStatus('Indexing will resume at the scheduled time while Novous is running.', 'success');
      await loadRagScan();
    } catch (error) {
      showRagStatus(`Could not schedule resume: ${error.message}`, 'danger');
    }
  });
  container.querySelector('[data-rag-refresh]').addEventListener('click', async () => {
    await loadRag();
    showRagStatus('Index and scan status refreshed.', 'muted');
  });
  ragForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (viewingArchivedBase) return;
    const submit = ragForm.querySelector('[type="submit"]');
    submit.disabled = true;
    showRagStatus('Embedding…');
    try {
      const title = container.querySelector('#chat-rag-title');
      const text = container.querySelector('#chat-rag-text');
      const result = await Api.addRagText(title.value, text.value, activeRagBaseId);
      showRagStatus(`Added "${title.value.trim()}" (${result.chunks} chunk(s)).`, 'success');
      title.value = '';
      text.value = '';
      await loadRag();
    } catch (error) {
      showRagStatus(`Could not add text: ${error.message}`, 'danger');
    } finally {
      submit.disabled = false;
    }
  });

  function formatScratchpadReads(memory) {
    const reads = Array.isArray(memory.read_history)
      ? memory.read_history
      : (memory.latest_read ? [memory.latest_read] : []);
    const lines = ['# Agent File Reads', '', `Exported: ${new Date().toLocaleString()}`, ''];

    if (!reads.length) {
      lines.push('No file reads are currently saved.', '');
      return lines.join('\n');
    }

    reads.forEach((entry, index) => {
      if (index > 0) lines.push('---', '');
      lines.push(`## ${entry.path || 'Unknown file'}`, '');
      if (entry.updated_at) lines.push(`- **Read at:** ${entry.updated_at}`);
      if (entry.request) lines.push(`- **Request:** ${entry.request.replace(/\r?\n/g, ' ')}`);
      lines.push('', '### Contents', '');

      const content = String(entry.content || '');
      const longestFence = Math.max(
        0,
        ...Array.from(content.matchAll(/`+/g), match => match[0].length)
      );
      const fence = '`'.repeat(Math.max(3, longestFence + 1));
      lines.push(fence, content, fence, '');
    });

    return lines.join('\n');
  }

  async function saveScratchpad(event) {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      const memory = await Api.getAgentScratchpad();
      const date = new Date().toISOString().slice(0, 10);
      await Api.saveMarkdown(
        formatScratchpadReads(memory),
        `novous-agent-reads-${date}.md`
      );
    } catch (error) {
      if (error.name === 'AbortError') return;
      appendMessage('system', `Could not save scratchpad: ${error.message}`);
    } finally {
      button.disabled = false;
    }
  }

  async function clearScratchpad(event) {
    if (!window.confirm('Clear all saved agent reads and workspace maps? This cannot be undone.')) return;
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await Api.clearAgentScratchpad();
      if (scratchpadDialog.open) renderScratchpad({});
      appendMessage('system', 'Agent scratchpad cleared.');
    } catch (error) {
      appendMessage('system', `Could not clear scratchpad: ${error.message}`);
    } finally {
      button.disabled = false;
    }
  }

  let agents = [];
  let installedModels = [];
  let currentModel = 'qwen2.5-coder:latest';
  let isSending = false;
  let isResetting = false;
  let isSavingLog = false;
  const chatFontKey = 'novous2.chat-console.font-size';
  let chatFontSize = 14;

  try {
    const storedSize = Number(localStorage.getItem(chatFontKey));
    if (Number.isFinite(storedSize) && storedSize >= 11 && storedSize <= 32) {
      chatFontSize = storedSize;
    }
  } catch (error) {
    console.warn('Could not load saved Chat Console text size.', error);
  }

  function setChatFontSize(size) {
    chatFontSize = Math.min(32, Math.max(11, size));
    chatMain.style.setProperty('--chat-console-font-size', `${chatFontSize}px`);
    try {
      localStorage.setItem(chatFontKey, String(chatFontSize));
    } catch (error) {
      console.warn('Could not save Chat Console text size.', error);
    }
  }

  setChatFontSize(chatFontSize);
  container.querySelector('#chat-font-smaller')
    .addEventListener('click', () => setChatFontSize(chatFontSize - 1));
  container.querySelector('#chat-font-larger')
    .addEventListener('click', () => setChatFontSize(chatFontSize + 2));

  container.querySelector('#chat-save-log').prepend(createIcon('save'));
  container.querySelector('#chat-reset').prepend(createIcon('reset'));
  sendButton.prepend(createIcon('send'));

  renderTree(container.querySelector('#chat-file-tree'), {
    manageRoots: true,
    onSelect: path => {
      if (document.getElementById('app')) {
        window.dispatchEvent(new CustomEvent('novous:open-editor', {
          detail: { path, managedFile: true }
        }));
      } else {
        const params = new URLSearchParams({ path, managed: '1' });
        window.location.assign(`/editor?${params}`);
      }
    }
  });

  function syncActionButtons() {
    const hasAgent = agents.some(agent => agent.id === agentSelect.value);
    saveLogButton.disabled = !hasAgent || isSavingLog || todoRunInProgress;
    resetButton.disabled = !hasAgent || isResetting || todoRunInProgress;
    quickResetButton.disabled = resetButton.disabled;
    const wipeButton = container.querySelector('[data-test-function="wipeChat"]');
    if (wipeButton) wipeButton.disabled = !hasAgent || isResetting || todoRunInProgress;
    sendButton.disabled = !hasAgent || modelSelect.disabled || !chatInput.value.trim() ||
      isSending || todoRunInProgress;
  }

  Api.getModels().then(data => {
    installedModels = (data.models || []).sort();
    if (!installedModels.length) {
      modelCount.textContent = '(none installed)';
      modelSelect.innerHTML = '<option value="">No models found — run: ollama pull</option>';
      modelSelect.disabled = true;
      syncActionButtons();
      syncTodoRunButton();
      return;
    }
    modelCount.textContent = `(${installedModels.length} installed)`;
    modelSelect.innerHTML = installedModels
      .map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('');
    modelSelect.disabled = false;
    syncModelSelect();
    syncActionButtons();
    syncTodoRunButton();
  }).catch(err => {
    modelCount.textContent = '(error)';
    modelSelect.innerHTML = `<option value="">Model list unavailable: ${esc(err.message)}</option>`;
    modelSelect.disabled = true;
    syncActionButtons();
    syncTodoRunButton();
  });

  function syncModelSelect() {
    const agent = agents.find(a => a.id === agentSelect.value);
    const stored = agent?.model || 'qwen2.5-coder:latest';
    if (installedModels.includes(stored)) {
      currentModel = stored;
      modelSelect.value = stored;
    } else if (!modelSelect.value || currentModel !== modelSelect.value) {
      currentModel = modelSelect.value || installedModels[0];
    }
  }

  modelSelect.addEventListener('change', () => {
    currentModel = modelSelect.value;
    syncActionButtons();
  });

  const agentEnvironments = ['workspace', 'codebuilder', 'prompt-creation'];
  const environmentLabels = {
    workspace: 'Workspace',
    codebuilder: 'CodeBuilder',
    'prompt-creation': 'Prompt Creation'
  };
  Promise.all(agentEnvironments.map(environment => Api.getAgents(environment))).then(results => {
    agents = results.flatMap((data, index) =>
      (data.agents || []).map(agent => ({
        ...agent,
        environment: agentEnvironments[index]
      }))
    );
    agentSelect.innerHTML = agents.length
      ? agents.map(a => `<option value="${esc(a.id)}">${esc(a.name)} (${esc(a.mode)}) · ${esc(environmentLabels[a.environment])}</option>`).join('')
      : '<option value="">No agents found</option>';
    if (agents.length > 0) {
      let last = null;
      try { last = localStorage.getItem('novous2.chat.lastAgent'); } catch { /* storage unavailable */ }
      if (last && agents.some(a => a.id === last)) agentSelect.value = last;
      updateAgentMeta(agentSelect.value);
      syncModelSelect();
    }
    syncActionButtons();
    syncTodoRunButton();
  }).catch(err => {
    agentSelect.innerHTML = `<option value="">Error: ${esc(err.message)}</option>`;
  });

  agentSelect.addEventListener('change', (e) => {
    try { localStorage.setItem('novous2.chat.lastAgent', e.target.value); } catch { /* storage unavailable */ }
    updateAgentMeta(e.target.value); syncModelSelect(); syncActionButtons(); syncTodoRunButton(); });

  chatInput.addEventListener('input', syncActionButtons);

  function updateAgentMeta(id) {
    const agent = agents.find(a => a.id === id);
    if (!agent) return;
    if (agent.model) currentModel = agent.model;
    metaCard.innerHTML = `
      <h4>${esc(agent.name)}</h4>
      <p><span class="badge ${agent.mode === 'agent' ? 'badge-accent' : 'badge-success'}">${esc((agent.mode || '').toUpperCase())}</span></p>
      <p>${esc(agent.description || 'No description provided.')}</p>
      <p class="text-muted small">Environment: ${esc(environmentLabels[agent.environment] || 'Workspace')}<br>
      Model: ${esc(currentModel)}<br>
      Tools: ${esc((agent.tools || []).join(', ') || 'none')}</p>`;
    toolsToggle.disabled = agent.mode !== 'agent';
    toolsToggle.checked = agent.mode === 'agent';
    sessionInfo.textContent = `Session: chat-${agent.id}`;
  }

  async function resetSession(message = 'Session reset. Send a message to start fresh.') {
    const agentId = agentSelect.value;
    if (!agentId) {
      appendMessage('system', 'Select an agent before resetting the chat.');
      return;
    }
    if (isResetting) return;

    isResetting = true;
    syncActionButtons();
    try {
      await Api.resetChat(`chat-${agentId}`);
      messagesBox.innerHTML = `<div class="message system-msg">${esc(message)}</div>`;
    } catch (err) {
      appendMessage('system', 'Reset failed: ' + err.message);
    } finally {
      isResetting = false;
      syncActionButtons();
    }
  }

  async function openDiagnostics() {
    try {
      const health = await Api.getHealth();
      const ollamaStatus = health.ollama?.reachable ? 'connected' : 'offline';
      const details = health.ollama?.detail ? `\nOllama details: ${health.ollama.detail}` : '';
      appendMessage(
        'system',
        `Diagnostics: API reachable\nOllama: ${ollamaStatus}\nUptime: ${health.uptime_seconds ?? 'unknown'} seconds${details}`
      );
    } catch (err) {
      appendMessage('system', `Diagnostics failed: ${err.message}`);
    }
  }

  function wipeChat() {
    return resetSession('Chat wiped. Send a message to start fresh.');
  }

  let todoFilesLoading = false;
  let todoRunInProgress = false;

  function syncTodoRunButton() {
    const button = container.querySelector('[data-test-function="runTestSuite"]');
    if (!button) return;
    const hasAgent = agents.some(agent => agent.id === agentSelect.value);
    button.disabled = todoFilesLoading || todoRunInProgress || !hasAgent ||
      modelSelect.disabled || isSending || isResetting;
  }

  async function loadTodoFiles(silent = false) {
    const select = container.querySelector('#todo-file-select');
    if (!select || todoFilesLoading) return;
    todoFilesLoading = true;
    const refreshButton = container.querySelector('#todo-file-refresh');
    if (refreshButton) refreshButton.disabled = true;

    try {
      const tree = await Api.getFileTree();
      const workspaceEntries = tree.children || [];
      const normalizedNames = new Set(['todo list', 'to due list', 'do due list']);
      const todoDirectories = workspaceEntries.filter(item =>
        item.type === 'directory' &&
        normalizedNames.has(item.name.toLowerCase().replace(/\s+/g, ' ').trim())
      );

      const files = [];
      function collectFiles(node) {
        if (node.type === 'file') {
          if (/\.(md|markdown)$/i.test(node.name) || !node.name.includes('.')) {
            files.push(node);
          }
          return;
        }
        (node.children || []).forEach(collectFiles);
      }
      workspaceEntries
        .filter(item => item.type === 'file')
        .forEach(collectFiles);
      todoDirectories.forEach(collectFiles);
      const markdownFiles = [...new Map(files.map(file => [file.path, file])).values()];
      const selectedPath = select.value;

      select.replaceChildren();
      if (!markdownFiles.length) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No Markdown or extensionless lists found in workspace or To Do List folders';
        select.appendChild(option);
        select.disabled = true;
        return;
      }

      markdownFiles.sort((a, b) => a.path.localeCompare(b.path));
      markdownFiles.forEach(file => {
        const option = document.createElement('option');
        option.value = file.path;
        option.textContent = file.path;
        option.title = file.path;
        select.appendChild(option);
      });
      if (markdownFiles.some(file => file.path === selectedPath)) {
        select.value = selectedPath;
      }
      select.disabled = false;
    } catch (err) {
      if (!silent) {
        select.replaceChildren();
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Error loading files';
        select.appendChild(option);
        select.disabled = true;
        appendMessage('system', `Could not load To-Do files: ${err.message}`);
      }
    } finally {
      todoFilesLoading = false;
      if (refreshButton) refreshButton.disabled = false;
      syncTodoRunButton();
    }
  }

  function openTodoSuite() {
    openTestSuiteRunner({
      filePath: container.querySelector('#todo-file-select')?.value || '',
      agentId: agentSelect.value,
      model: currentModel,
      agents,
      models: installedModels,
      onRunningChange: running => {
        todoRunInProgress = running;
        syncActionButtons();
        syncTodoRunButton();
      },
      onChatMessage: (role, text) => appendMessage(role, text),
      onToolEvent: event => appendToolBadge(
        event.tool,
        event.status,
        event.args,
        event.display
      )
    });
  }

  container.querySelector('#chat-reset').addEventListener('click', () => resetSession());
  quickResetButton.addEventListener('click', () => resetSession());
  container.querySelector('#chat-save-log').addEventListener('click', async () => {
    const agentId = agentSelect.value;
    if (!agentId) {
      alert('Select an agent before saving the session log.');
      return;
    }
    if (isSavingLog) return;

    isSavingLog = true;
    syncActionButtons();
    try {
      const res = await Api.exportSession(`chat-${agentId}`);
      alert(res.locationChosen
        ? `Session log saved as ${res.filename} in the location you selected.`
        : `Session log download started: ${res.filename}\n\nChoose the save location in your browser's download settings.`);
    } catch (err) {
      if (err.name !== 'AbortError') alert(`Failed to save session: ${err.message}`);
    } finally {
      isSavingLog = false;
      syncActionButtons();
    }
  });
  buildTestPanel('testPanelButtons', {
    diagnostics: openDiagnostics,
    wipeChat,
    runTestSuite: openTodoSuite,
    viewScratchpad: openScratchpad,
    viewKnowledgeCatalog: openKnowledgeCatalog,
    saveScratchpad,
    clearScratchpad,
    viewRag: openRag
  });
  loadTodoFiles();
  container.querySelector('#todo-file-refresh')
    ?.addEventListener('click', () => loadTodoFiles());
  container.querySelector('#todo-file-select')
    ?.addEventListener('change', syncTodoRunButton);
  const todoRefreshInterval = setInterval(() => {
    if (!container.isConnected) {
      clearInterval(todoRefreshInterval);
      return;
    }
    loadTodoFiles(true);
  }, 5000);

  async function pollPendingQuestions() {
    try {
      const data = await Api.getPendingQuestions();
      for (const item of (data.pending || [])) {
        if (!document.querySelector(`[data-request-id="${item.request_id}"]`)) {
          openQuestionDialogModal(item.request_id, item.questions || []);
        }
      }
    } catch (_) {
      // Quiet polling: ignore transient errors while the chat turn is in flight.
    }
  }

  const questionPollInterval = setInterval(() => {
    if (!container.isConnected) {
      clearInterval(questionPollInterval);
      return;
    }
    pollPendingQuestions();
  }, 2000);

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    const agentId = agentSelect.value;
    if (!text || !agentId) return;

    appendMessage('user', text);
    chatInput.value = '';
    isSending = true;
    syncActionButtons();

    const thinkingId = appendMessage('assistant', 'Thinking...', true);

    try {
      const sessionId = `chat-${agentId}`;
      const agent = agents.find(item => item.id === agentId);
      const res = await Api.sendMessage(
        text,
        agentId,
        currentModel,
        sessionId,
        agent?.environment || 'workspace'
      );
      removeMessage(thinkingId);

      if (res.tool_events && res.tool_events.length > 0) {
        res.tool_events.forEach(evt => appendToolBadge(evt.tool, evt.status, evt.args, evt.display));
      }

      appendMessage('assistant', res.reply);
    } catch (err) {
      removeMessage(thinkingId);
      appendMessage('system', 'Error communicating with engine: ' + err.message);
    } finally {
      isSending = false;
      syncActionButtons();
    }
  });

  function appendMessage(role, content, isTemporary = false) {
    const msgDiv = document.createElement('div');
    const id = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4);
    msgDiv.id = id;
    msgDiv.className = `message ${role}-msg ${isTemporary ? 'pulse' : ''}`;
    const body = document.createElement('div');
    body.className = 'msg-body';
    body.innerText = content;
    msgDiv.appendChild(body);

    if (!isTemporary && role !== 'system') {
      const copyButton = document.createElement('button');
      const copyLabel = document.createElement('span');
      copyButton.type = 'button';
      copyButton.className = 'btn btn-sm btn-ghost msg-copy-btn';
      copyLabel.textContent = 'Copy';
      copyButton.append(createIcon('copy'), copyLabel);
      copyButton.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(content);
          copyLabel.textContent = 'Copied!';
          setTimeout(() => { copyLabel.textContent = 'Copy'; }, 2000);
        } catch (err) {
          copyLabel.textContent = 'Copy failed';
        }
      });
      msgDiv.appendChild(copyButton);
    }

    messagesBox.appendChild(msgDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
    return id;
  }

  function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function appendToolBadge(toolName, status, args, display) {
    const badgeDiv = document.createElement('div');
    badgeDiv.className = `tool-badge ${status}`;
    const argText = args ? JSON.stringify(args) : '';
    badgeDiv.innerHTML = `🛠️ <strong>${esc(toolName)}</strong> executed (${esc(status)})
      ${argText ? `<span class="text-muted small"> ${esc(argText.slice(0, 120))}</span>` : ''}`;
    if (display && toolName === 'map_files') {
      try {
        appendMapTree(badgeDiv, JSON.parse(display));
      } catch {
        appendTreeView(badgeDiv, args || {}, display);
      }
    } else if (display) {
      appendTreeView(badgeDiv, args || {}, display);
    }
    messagesBox.appendChild(badgeDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  function appendMapTree(badgeDiv, tree) {
    badgeDiv.classList.add('has-tree');
    const panel = document.createElement('div');
    panel.className = 'chat-map-tree';
    const heading = document.createElement('div');
    heading.className = 'chat-map-heading';
    const title = document.createElement('strong');
    title.textContent = tree.name || 'Workspace';
    const count = countTreeEntries(tree);
    const meta = document.createElement('span');
    meta.className = 'text-muted small';
    meta.textContent = `${count.folders} folders · ${count.files} files`;
    heading.append(title, meta);
    panel.append(heading, createMapTreeNode(tree, true));
    badgeDiv.appendChild(panel);
  }

  function countTreeEntries(node) {
    return (node.children || []).reduce((total, child) => {
      if (child.type === 'directory') {
        total.folders += 1;
        const nested = countTreeEntries(child);
        total.folders += nested.folders;
        total.files += nested.files;
      } else {
        total.files += 1;
      }
      return total;
    }, { folders: 0, files: 0 });
  }

  function createMapTreeNode(node, isRoot = false) {
    const list = document.createElement('ul');
    list.className = 'chat-map-tree-list';
    (node.children || []).forEach(child => {
      const item = document.createElement('li');
      if (child.type === 'directory') {
        const folder = document.createElement('details');
        const summary = document.createElement('summary');
        const icon = document.createElement('span');
        icon.className = 'chat-map-icon';
        icon.setAttribute('aria-hidden', 'true');
        icon.textContent = '📁';
        const name = document.createElement('span');
        name.textContent = child.name;
        summary.append(icon, name);
        folder.append(summary, createMapTreeNode(child));
        item.appendChild(folder);
      } else {
        const openFile = document.createElement('button');
        openFile.type = 'button';
        openFile.className = 'chat-map-file';
        openFile.title = child.path || child.name;
        const icon = document.createElement('span');
        icon.className = 'chat-map-icon';
        icon.setAttribute('aria-hidden', 'true');
        icon.textContent = '📄';
        const name = document.createElement('span');
        name.textContent = child.name;
        openFile.append(icon, name);
        openFile.addEventListener('click', () => {
          if (document.getElementById('app')) {
            window.dispatchEvent(new CustomEvent('novous:open-editor', {
              detail: { path: child.path, managedFile: true }
            }));
          } else {
            const params = new URLSearchParams({ path: child.path, managed: '1' });
            window.location.assign(`/editor?${params}`);
          }
        });
        item.appendChild(openFile);
      }
      list.appendChild(item);
    });
    if (!isRoot) return list;

    const root = document.createElement('details');
    root.open = true;
    const summary = document.createElement('summary');
    const icon = document.createElement('span');
    icon.className = 'chat-map-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = '📂';
    const name = document.createElement('span');
    name.textContent = node.name || 'Workspace';
    summary.append(icon, name);
    root.append(summary, list);
    return root;
  }

  const MORE_NOTE = /\n… (\d+) more lines \(next offset (\d+)\)\s*$/;

  function appendTreeView(badgeDiv, args, display) {
    const pre = document.createElement('pre');
    pre.className = 'tree-view';
    badgeDiv.classList.add('has-tree');
    badgeDiv.appendChild(pre);

    const showPage = (text) => {
      const match = text.match(MORE_NOTE);
      pre.textContent += (pre.textContent ? '\n' : '') + text.replace(MORE_NOTE, '');
      return match ? { remaining: Number(match[1]), next: Number(match[2]) } : null;
    };

    const renderMoreControl = (more) => {
      badgeDiv.querySelector('.tree-more')?.remove();
      if (!more) return;
      const bar = document.createElement('div');
      bar.className = 'tree-more';
      const label = document.createElement('span');
      label.className = 'text-muted small';
      label.textContent = `${more.remaining} more lines. Show more?`;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn btn-sm btn-primary';
      button.textContent = 'Show more';
      button.addEventListener('click', async () => {
        button.disabled = true;
        try {
          const page = await Api.mapFolderPage(
            args.path, args.max_depth ?? 3, args.include_files ?? true, more.next
          );
          pre.textContent += '\n' + page.text;
          renderMoreControl(page.remaining
            ? { remaining: page.remaining, next: page.next_offset } : null);
        } catch (err) {
          label.textContent = `Could not load more: ${err.message}`;
          button.disabled = false;
        }
        messagesBox.scrollTop = messagesBox.scrollHeight;
      });
      bar.append(label, button);
      badgeDiv.appendChild(bar);
    };

    renderMoreControl(showPage(display));
  }
}

/**
 * Render a step-by-step Human-in-the-Loop question dialog.
 * Answers are submitted back to the server, which resumes the paused agent tool.
 */
function openQuestionDialogModal(requestId, questions) {
  let currentIndex = 0;
  const userAnswers = {};

  const overlay = document.createElement('div');
  overlay.className = 'question-dialog-overlay';
  overlay.dataset.requestId = requestId;

  const modal = document.createElement('div');
  modal.className = 'card question-dialog';
  overlay.appendChild(modal);

  const questionText = item =>
    (item && typeof item === 'object') ? String(item.question ?? '') : String(item ?? '');
  const questionId = (item, index) =>
    (item && typeof item === 'object' && item.id != null) ? String(item.id) : String(index);

  function renderQuestion() {
    const item = questions[currentIndex];
    const qText = questionText(item);
    const qId = questionId(item, currentIndex);
    const isLast = currentIndex === questions.length - 1;
    const pct = Math.round(((currentIndex + 1) / questions.length) * 100);

    modal.innerHTML = `
      <div class="question-dialog-head">
        <h3>Question ${currentIndex + 1} of ${questions.length}</h3>
        <span class="badge badge-accent">${pct}%</span>
      </div>
      <p class="question-dialog-prompt">${esc(qText)}</p>
      <textarea id="dialog-answer-input" class="form-input question-dialog-input" rows="4"
        placeholder="Type your answer here..."></textarea>
      <p class="question-dialog-error text-danger"></p>
      <div class="question-dialog-actions">
        <button type="button" id="dialog-prev-btn" class="btn btn-sm" ${currentIndex === 0 ? 'disabled' : ''}>Back</button>
        <button type="button" id="dialog-next-btn" class="btn btn-sm btn-primary">
          <span>${isLast ? 'Submit All Answers' : 'Next Question'}</span>
        </button>
      </div>`;

    modal.querySelector('#dialog-prev-btn').prepend(createIcon('reset'));
    modal.querySelector('#dialog-next-btn').prepend(createIcon(isLast ? 'check-square' : 'send'));

    const textarea = modal.querySelector('#dialog-answer-input');
    textarea.value = userAnswers[qId] ?? '';
    textarea.focus();

    modal.querySelector('#dialog-prev-btn').onclick = () => {
      userAnswers[qId] = textarea.value;
      if (currentIndex > 0) {
        currentIndex -= 1;
        renderQuestion();
      }
    };

    modal.querySelector('#dialog-next-btn').onclick = async () => {
      userAnswers[qId] = textarea.value;
      if (!isLast) {
        currentIndex += 1;
        renderQuestion();
        return;
      }

      const nextBtn = modal.querySelector('#dialog-next-btn');
      nextBtn.disabled = true;
      nextBtn.querySelector('span').textContent = 'Submitting...';
      try {
        await Api.submitAnswers(requestId, userAnswers);
        overlay.remove();
      } catch (err) {
        nextBtn.disabled = false;
        nextBtn.querySelector('span').textContent = 'Submit All Answers';
        modal.querySelector('.question-dialog-error').textContent = `Submission failed: ${err.message}`;
      }
    };
  }

  renderQuestion();
  document.body.appendChild(overlay);
}
