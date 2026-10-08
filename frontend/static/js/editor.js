import { Api } from './api.js';
import { renderTree } from './tree.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

const state = {
  path: null,
  dirty: false,
  ws: null
};

/**
 * File & Agent Editor Component (textarea editor + live session event bus).
 * @param {HTMLElement} container
 * @param {string|null} initialPath
 */
export function renderEditorView(container, initialPath = null) {
  container.innerHTML = `
    <div class="editor-layout">
      <aside class="editor-sidebar">
        <h3 class="sidebar-title">Workspace</h3>
        <div id="editor-tree" class="tree-pane"></div>
      </aside>

      <section class="editor-main">
        <div class="editor-toolbar">
          <span id="editor-path" class="editor-path">No file open</span>
          <span id="editor-dirty" class="badge badge-warning hidden">Unsaved</span>
          <span class="spacer"></span>
          <span id="editor-ws" class="badge badge-success" title="Session event bus">WS ●</span>
          <button class="btn btn-sm" id="editor-reload">Reload</button>
          <button class="btn btn-sm btn-primary" id="editor-save">Save (Ctrl+S)</button>
        </div>
        <textarea id="editor-textarea" class="editor-textarea" spellcheck="false"
                  placeholder="Select a file from the tree to edit…"></textarea>
        <div class="editor-status">
          <span id="editor-pos">Ln 1, Col 1</span>
          <span class="spacer"></span>
          <span id="editor-bytes">0 bytes</span>
        </div>
      </section>

      <aside class="editor-events">
        <h3 class="sidebar-title">Session Events</h3>
        <div id="event-log" class="event-log">
          <p class="text-muted">Connecting to event bus…</p>
        </div>
      </aside>
    </div>`;

  const textarea = container.querySelector('#editor-textarea');
  const pathLabel = container.querySelector('#editor-path');
  const dirtyBadge = container.querySelector('#editor-dirty');
  const bytesLabel = container.querySelector('#editor-bytes');
  const posLabel = container.querySelector('#editor-pos');
  const eventLog = container.querySelector('#event-log');
  const wsBadge = container.querySelector('#editor-ws');

  renderTree(container.querySelector('#editor-tree'), {
    onSelect: (path) => openFile(path)
  });

  async function openFile(path) {
    if (state.dirty && !confirm('Discard unsaved changes?')) return;
    try {
      const data = await Api.readFile(path);
      state.path = data.path;
      state.dirty = false;
      textarea.value = data.content;
      pathLabel.textContent = data.path;
      dirtyBadge.classList.add('hidden');
      updateBytes();
      updatePos();
      sendWs({ type: 'file_opened', path: data.path });
      appendEvent({ type: 'file_opened', path: data.path, session_id: 'you' });
      textarea.focus();
    } catch (err) {
      alert(err.message);
    }
  }

  async function saveFile() {
    if (!state.path) return alert('No file open.');
    try {
      await Api.writeFile(state.path, textarea.value);
      state.dirty = false;
      dirtyBadge.classList.add('hidden');
      appendEvent({ type: 'file_saved', path: state.path, session_id: 'you' });
      updateBytes();
    } catch (err) {
      alert(err.message);
    }
  }

  function updateBytes() {
    bytesLabel.textContent = `${new Blob([textarea.value]).size} bytes`;
  }

  function updatePos() {
    const upto = textarea.value.slice(0, textarea.selectionStart);
    const lines = upto.split('\n');
    posLabel.textContent = `Ln ${lines.length}, Col ${lines[lines.length - 1].length + 1}`;
  }

  textarea.addEventListener('input', () => {
    if (!state.dirty) { state.dirty = true; dirtyBadge.classList.remove('hidden'); }
    updateBytes();
  });
  textarea.addEventListener('keyup', updatePos);
  textarea.addEventListener('click', updatePos);
  textarea.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') { e.preventDefault(); saveFile(); }
  });

  container.querySelector('#editor-save').addEventListener('click', saveFile);
  container.querySelector('#editor-reload').addEventListener('click', () => {
    if (state.path) openFile(state.path);
  });

  // --- WebSocket session event bus ----------------------------------------
  function connectWs() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/api/ws`);
    state.ws = ws;

    ws.onopen = () => { wsBadge.textContent = 'WS ●'; wsBadge.className = 'badge badge-success'; };
    ws.onclose = () => {
      wsBadge.textContent = 'WS ○'; wsBadge.className = 'badge badge-danger';
      eventLog.insertAdjacentHTML('beforeend',
        '<p class="text-muted small">Disconnected. Reconnecting…</p>');
      setTimeout(connectWs, 3000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.type === 'connected') {
          eventLog.innerHTML = `<p class="text-muted small">Connected as session ${esc(data.session_id)}</p>`;
        } else if (data.type !== 'pong') {
          appendEvent(data);
        }
      } catch (_) { /* non-JSON frame */ }
    };
  }

  function sendWs(payload) {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify(payload));
    }
  }

  function appendEvent(data) {
    if (eventLog.querySelector('.text-muted.small') && eventLog.children.length === 1 &&
        eventLog.textContent.includes('Disconnected')) {
      eventLog.innerHTML = '';
    }
    const el = document.createElement('div');
    el.className = `event-item ${data.type}`;
    el.innerHTML = `<span class="event-type">${esc(data.type.replace(/_/g, ' '))}</span>
      <span class="event-path">${esc(data.path || '')}</span>
      <span class="event-who text-muted">${esc(data.session_id || '')}</span>`;
    eventLog.appendChild(el);
    while (eventLog.children.length > 60) eventLog.removeChild(eventLog.firstChild);
    eventLog.scrollTop = eventLog.scrollHeight;
  }

  connectWs();

  if (initialPath) openFile(initialPath);
}
