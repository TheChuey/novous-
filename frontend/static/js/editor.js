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
        <div class="event-export">
          <button class="btn btn-sm btn-primary" id="event-save-log">Save Events Log (.md)</button>
        </div>
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
  const saveLogButton = container.querySelector('#event-save-log');
  const sessionEvents = [];

  saveLogButton.addEventListener('click', async () => {
    saveLogButton.disabled = true;
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const rows = sessionEvents.map(event => {
        const escapeCell = value => String(value || '').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');
        const details = event.data && Object.keys(event.data).length
          ? JSON.stringify(event.data)
          : '';
        return `| ${escapeCell(event.type.replace(/_/g, ' '))} | ${escapeCell(event.path)} | ${escapeCell(event.session_id)} | ${escapeCell(details)} |`;
      });
      const markdown = [
        '# Novous Session Events Log',
        '',
        `Exported: ${new Date().toLocaleString()}`,
        '',
        '| Event | Path / Tool | Session | Details |',
        '| --- | --- | --- | --- |',
        ...(rows.length ? rows : ['| No events recorded | | | |']),
        ''
      ].join('\n');
      const result = await Api.saveMarkdown(markdown, `novous-session-events-${timestamp}.md`);
      alert(result.locationChosen
        ? `Events log saved as ${result.filename} in the location you selected.`
        : `Events log download started: ${result.filename}\n\nChoose the save location in your browser's download settings.`);
    } catch (err) {
      if (err.name !== 'AbortError') alert(`Failed to save events log: ${err.message}`);
    } finally {
      saveLogButton.disabled = false;
    }
  });

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
          if (!sessionEvents.length) {
            eventLog.innerHTML = `<p class="text-muted small">Connected as session ${esc(data.session_id)}</p>`;
          }
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
    const eventData = {
      type: String(data.type || 'unknown'),
      path: data.path || '',
      session_id: data.session_id || '',
      data: data.data || {}
    };
    sessionEvents.push(eventData);
    const detailText = eventData.type === 'tool_executed'
      ? `${eventData.data.status || 'unknown'}${eventData.data.origin ? ` · ${eventData.data.origin}` : ''}\nArgs: ${JSON.stringify(eventData.data.args || {})}${eventData.data.error ? `\nError: ${eventData.data.error}` : ''}`
      : '';
    const eventText = [
      eventData.type.replace(/_/g, ' '),
      eventData.path,
      eventData.session_id,
      detailText
    ].filter(Boolean).join('\n');
    const detailElement = detailText
      ? `<span class="event-details">${esc(detailText)}</span>`
      : '';
    el.innerHTML = `<span class="event-type">${esc(eventData.type.replace(/_/g, ' '))}</span>
      <span class="event-path">${esc(eventData.path)}</span>
      <span class="event-who text-muted">${esc(eventData.session_id)}</span>${detailElement}`;
    const copyButton = document.createElement('button');
    copyButton.type = 'button';
    copyButton.className = 'btn btn-sm btn-ghost event-copy-btn';
    copyButton.textContent = 'Copy';
    copyButton.setAttribute('aria-label', `Copy ${eventData.type.replace(/_/g, ' ')} event`);
    copyButton.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(eventText);
        copyButton.textContent = 'Copied!';
        setTimeout(() => { copyButton.textContent = 'Copy'; }, 2000);
      } catch (err) {
        copyButton.textContent = 'Copy failed';
      }
    });
    el.appendChild(copyButton);
    eventLog.appendChild(el);
    while (sessionEvents.length > 60) {
      sessionEvents.shift();
      const firstEvent = eventLog.querySelector('.event-item');
      if (firstEvent) firstEvent.remove();
    }
    eventLog.scrollTop = eventLog.scrollHeight;
  }

  connectWs();

  if (initialPath) openFile(initialPath);
}
