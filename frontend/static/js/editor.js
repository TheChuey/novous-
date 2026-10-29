import { Api } from './api.js';
import { attachCodeBuilderEditor } from './codebuilder/codebuilder_editor.js';
import { renderTree } from './tree.js';

const fileSelectionListeners = new WeakMap();

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

const state = {
  path: null,
  dirty: false,
  ws: null,
  editor: null,
  managedPath: false
};

/**
 * File & Agent Editor Component (Monaco editor + live session event bus).
 * @param {HTMLElement} container
 * @param {string|null} initialPath
 */
export function renderEditorView(container, initialPath = null) {
  const initialFile = typeof initialPath === 'string'
    ? { path: initialPath, managedFile: false }
    : initialPath;
  const oldSelectionListener = fileSelectionListeners.get(container);
  if (oldSelectionListener) window.removeEventListener('novous:file-selected', oldSelectionListener);
  state.editor?.dispose();
  state.path = null;
  state.dirty = false;
  state.managedPath = false;

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
        <div id="editor-monaco" class="editor-monaco"></div>
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

  container.insertAdjacentHTML('beforeend', `
    <dialog id="editor-save-dialog" class="workspace-save-dialog">
      <form id="editor-save-form">
        <h2>Save to Workspace</h2>
        <p class="text-muted">Choose a workspace folder and file name.</p>
        <label for="editor-save-directory">Folder</label>
        <select id="editor-save-directory" class="form-select"></select>
        <label for="editor-save-filename">File name</label>
        <input id="editor-save-filename" class="form-input" type="text" required>
        <p id="editor-save-error" class="text-danger hidden" role="alert"></p>
        <div class="workspace-save-actions">
          <button id="editor-save-cancel" class="btn" type="button">Cancel</button>
          <button id="editor-save-confirm" class="btn btn-primary" type="submit">Save</button>
        </div>
      </form>
    </dialog>`);

  const editorMount = container.querySelector('#editor-monaco');
  const pathLabel = container.querySelector('#editor-path');
  const dirtyBadge = container.querySelector('#editor-dirty');
  const bytesLabel = container.querySelector('#editor-bytes');
  const posLabel = container.querySelector('#editor-pos');
  const eventLog = container.querySelector('#event-log');
  const wsBadge = container.querySelector('#editor-ws');
  const saveLogButton = container.querySelector('#event-save-log');
  const saveDialog = container.querySelector('#editor-save-dialog');
  const saveDirectory = container.querySelector('#editor-save-directory');
  const saveFilename = container.querySelector('#editor-save-filename');
  const saveError = container.querySelector('#editor-save-error');
  const saveConfirm = container.querySelector('#editor-save-confirm');
  const sessionEvents = [];
  let saveDialogFiles = new Set();
  let suppressEditorChanges = false;
  let workspaceTree;
  const editorReady = attachCodeBuilderEditor(editorMount, '', 'plaintext').then(instance => {
    state.editor = instance;
    instance.onChange(() => {
      if (suppressEditorChanges) return;
      if (!state.dirty) { state.dirty = true; dirtyBadge.classList.remove('hidden'); }
      updateBytes();
    });
    if (state.path) {
      suppressEditorChanges = true;
      instance.setValue(state.content || '');
      instance.setLanguage(languageForPath(state.path));
      suppressEditorChanges = false;
    }
    instance.focus();
    updateBytes();
    return instance;
  });

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

  async function openFile(path, managedFile = false) {
    if (state.dirty && !confirm('Discard unsaved changes?')) return;
    try {
      const data = managedFile ? await Api.readManagedFile(path) : await Api.readFile(path);
      state.path = data.path;
      state.content = data.content;
      state.managedPath = managedFile;
      state.dirty = false;
      pathLabel.textContent = data.path;
      dirtyBadge.classList.add('hidden');
      await editorReady;
      suppressEditorChanges = true;
      state.editor.setLanguage(languageForPath(data.path));
      state.editor.setValue(data.content);
      state.editor.setHighlightedLines(initialFile.previewLines || []);
      suppressEditorChanges = false;
      updateBytes();
      updatePos();
      sendWs({ type: 'file_opened', path: data.path });
      appendEvent({ type: 'file_opened', path: data.path, session_id: 'you' });
      state.editor.focus();
    } catch (err) {
      suppressEditorChanges = false;
      alert(err.message);
    }
  }

  function languageForPath(path) {
    const extension = path.split('.').pop().toLowerCase();
    return ({
      c: 'c', cc: 'cpp', cpp: 'cpp', cs: 'csharp', css: 'css', go: 'go',
      h: 'cpp', htm: 'html', html: 'html', java: 'java', js: 'javascript',
      json: 'json', jsx: 'javascript', md: 'markdown', mjs: 'javascript',
      py: 'python', rb: 'ruby', rs: 'rust', sh: 'shell', sql: 'sql',
      ts: 'typescript', tsx: 'typescript', txt: 'plaintext', xml: 'xml',
      yaml: 'yaml', yml: 'yaml'
    })[extension] || 'plaintext';
  }

  workspaceTree = renderTree(container.querySelector('#editor-tree'), {
    onBeforeDelete: path => {
      const deletesOpenFile = state.path === path || state.path?.startsWith(`${path}/`);
      return !deletesOpenFile || !state.dirty ||
        confirm('This item contains the open file with unsaved changes. Delete anyway?');
    },
    onDelete: path => {
      if (state.path === path || state.path?.startsWith(`${path}/`)) {
        state.path = null;
        state.content = '';
        state.managedPath = false;
        state.editor?.setValue('');
        pathLabel.textContent = 'No file open';
        dirtyBadge.classList.add('hidden');
        state.dirty = false;
        updateBytes();
      }
    }
  });
  const onFileSelected = event => {
    const path = event.detail && event.detail.path;
    if (typeof path === 'string' && path) openFile(path, true);
  };
  fileSelectionListeners.set(container, onFileSelected);
  window.addEventListener('novous:file-selected', onFileSelected);
  editorReady.then(instance => instance.onPosition(updatePos));

  async function openSaveDialog() {
    try {
      const managedSave = state.managedPath || !state.path;
      const tree = managedSave
        ? await Api.getManagedFileTree()
        : await Api.getFileTree();
      const folders = [];
      const files = new Set();
      function collect(node) {
        if (node.type === 'directory') {
          if (node.path) folders.push(node.path);
          (node.children || []).forEach(collect);
        } else {
          files.add(node.path);
        }
      }
      collect(tree);
      folders.sort((a, b) => a.localeCompare(b));

      saveDirectory.replaceChildren();
      const rootOption = document.createElement('option');
      rootOption.value = '';
      rootOption.textContent = '/ (workspace root)';
      saveDirectory.appendChild(rootOption);
      folders.forEach(path => {
        const option = document.createElement('option');
        option.value = path;
        option.textContent = path;
        saveDirectory.appendChild(option);
      });

      const currentParts = (state.path || '').split('/');
      const currentFilename = currentParts.pop() || 'untitled.txt';
      const currentDirectory = currentParts.join('/');
      saveDirectory.value = folders.includes(currentDirectory) ? currentDirectory : '';
      saveFilename.value = currentFilename;
      saveError.textContent = '';
      saveError.classList.add('hidden');
      saveDialog.showModal();
      saveFilename.focus();
      saveFilename.select();
      saveDialogFiles = files;
    } catch (err) {
      alert(`Could not open the workspace save picker: ${err.message}`);
    }
  }

  async function saveFile() {
    if (!saveDialog.open) {
      await openSaveDialog();
      return;
    }

    const filename = saveFilename.value.trim();
    if (!filename || filename === '.' || filename === '..' || /[\\/]/.test(filename)) {
      saveError.textContent = 'Enter a file name without folder separators.';
      saveError.classList.remove('hidden');
      saveFilename.focus();
      return;
    }

    const targetPath = [saveDirectory.value, filename].filter(Boolean).join('/');
    if (saveDialogFiles.has(targetPath) && targetPath !== state.path &&
        !confirm(`"${targetPath}" already exists. Overwrite it?`)) {
      return;
    }

    saveConfirm.disabled = true;
    try {
      await editorReady;
      const content = state.editor.getValue();
      const managedSave = state.managedPath || !state.path;
      if (managedSave) await Api.writeManagedFile(targetPath, content);
      else await Api.writeFile(targetPath, content);
      state.path = targetPath;
      state.content = content;
      state.managedPath = managedSave;
      state.editor.setLanguage(languageForPath(targetPath));
      state.dirty = false;
      dirtyBadge.classList.add('hidden');
      pathLabel.textContent = targetPath;
      appendEvent({ type: 'file_saved', path: targetPath, session_id: 'you' });
      updateBytes();
      saveDialog.close();
      workspaceTree.reload();
    } catch (err) {
      saveError.textContent = `Save failed: ${err.message}`;
      saveError.classList.remove('hidden');
    } finally {
      saveConfirm.disabled = false;
    }
  }

  function updateBytes() {
    bytesLabel.textContent = `${new Blob([state.editor?.getValue() || '']).size} bytes`;
  }

  function updatePos() {
    const position = state.editor?.getPosition();
    if (position) posLabel.textContent = `Ln ${position.lineNumber}, Col ${position.column}`;
  }

  container.querySelector('#editor-save').addEventListener('click', openSaveDialog);
  container.querySelector('#editor-save-form').addEventListener('submit', (event) => {
    event.preventDefault();
    saveFile();
  });
  container.querySelector('#editor-save-cancel').addEventListener('click', () => saveDialog.close());
  container.querySelector('#editor-reload').addEventListener('click', () => {
    if (state.path) openFile(state.path, state.managedPath);
  });
  editorReady.then(instance => instance.setSaveHandler(saveFile));

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

  if (initialFile?.path) openFile(initialFile.path, initialFile.managedFile === true);
}
