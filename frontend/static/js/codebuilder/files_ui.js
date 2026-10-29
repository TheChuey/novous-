import { dialog } from '../sandbox_ui.js';
import { renderTree } from '../tree.js';
import { Api } from '../api.js';

async function call(method, url, body) {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof payload.detail === 'string' ? payload.detail : `Request failed (${response.status}).`);
  }
  return payload;
}

const Files = {
  list: () => call('GET', '/api/codebuilder/files'),
  read: path => call('GET', `/api/codebuilder/files/read?path=${encodeURIComponent(path)}`),
  save: (folder, name, content, overwrite) =>
    call('POST', '/api/codebuilder/files/save', { folder, name, content, overwrite }),
  runCommand: (path, content) => call('POST', '/api/codebuilder/files/run-command', { path, content })
};

function button(label, className = 'btn') {
  const el = document.createElement('button');
  el.type = 'button';
  el.className = className;
  el.textContent = label;
  return el;
}

// Save, Save As, Open and Run-in-terminal for the editor. `openTerminalWith(command)` prefills the terminal.
export function setupFileControls({ editor, status, label, buttons, openTerminalWith }) {
  let currentPath = '';
  let managedPath = ''; // set when the open file came from the file manager (saved through it too)
  let savedValue = editor.getValue();

  const isDirty = () => editor.getValue() !== savedValue;
  const nameOf = path => path.split(/[\\/]/).pop();

  const refreshLabel = () => {
    if (!label) return;
    label.textContent = currentPath ? `${nameOf(currentPath)}${isDirty() ? ' ●' : ''}` : (isDirty() ? 'Unsaved ●' : 'Untitled');
    label.title = currentPath || 'Not saved to a file yet';
  };

  const markSaved = (path) => {
    currentPath = path;
    savedValue = editor.getValue();
    refreshLabel();
  };

  const writeFile = async (folder, name, overwrite = false) => {
    const result = await Files.save(folder, name, editor.getValue(), overwrite);
    if (result.saved) {
      managedPath = '';
      markSaved(result.path);
      status.textContent = `Saved ${result.path}`;
      return result;
    }
    if (result.exists && confirm(`${result.name} already exists. Replace it?`)) {
      return writeFile(folder, name, true);
    }
    return null;
  };

  const saveAs = () => new Promise(resolve => {
    Files.list().then(info => {
      dialog('Save as', (modal, close) => {
        const nameInput = document.createElement('input');
        nameInput.className = 'form-input question-dialog-input';
        nameInput.placeholder = 'file name, e.g. app.py';
        nameInput.value = currentPath ? nameOf(currentPath) : '';
        nameInput.setAttribute('aria-label', 'File name');
        const folderSelect = document.createElement('select');
        folderSelect.className = 'form-select';
        folderSelect.setAttribute('aria-label', 'Folder');
        info.folders.forEach(folder => {
          const option = document.createElement('option');
          option.value = folder;
          option.textContent = folder;
          folderSelect.appendChild(option);
        });
        folderSelect.value = currentPath
          ? currentPath.slice(0, Math.max(currentPath.lastIndexOf('\\'), currentPath.lastIndexOf('/')))
          : info.default_folder;
        if (!folderSelect.value) folderSelect.value = info.default_folder;
        const error = document.createElement('p');
        error.className = 'text-danger small';
        const actions = document.createElement('div');
        actions.className = 'question-dialog-actions';
        const cancel = button('Cancel');
        const save = button('Save', 'btn btn-primary');
        actions.append(cancel, save);
        modal.append(nameInput, folderSelect, error, actions);
        nameInput.focus();
        cancel.addEventListener('click', () => { close(); resolve(null); });
        const submit = async () => {
          if (!nameInput.value.trim()) { error.textContent = 'Enter a file name.'; return; }
          save.disabled = true;
          try {
            const result = await writeFile(folderSelect.value, nameInput.value);
            if (result) { close(); resolve(result); }
          } catch (err) {
            error.textContent = err.message;
          }
          save.disabled = false;
        };
        save.addEventListener('click', submit);
        nameInput.addEventListener('keydown', event => { if (event.key === 'Enter') submit(); });
      });
    }).catch(err => { status.textContent = err.message; resolve(null); });
  });

  const save = async () => {
    if (managedPath) {
      try {
        await Api.writeManagedFile(managedPath, editor.getValue());
        markSaved(managedPath);
        status.textContent = `Saved ${managedPath}`;
        window.dispatchEvent(new CustomEvent('novous:fs-changed'));
        return { saved: true, path: managedPath };
      } catch (err) {
        status.textContent = `Save failed: ${err.message}`;
        return null;
      }
    }
    if (!currentPath) return saveAs();
    const folder = currentPath.slice(0, Math.max(currentPath.lastIndexOf('\\'), currentPath.lastIndexOf('/')));
    try {
      return await writeFile(folder, nameOf(currentPath), true);
    } catch (err) {
      status.textContent = `Save failed: ${err.message}`;
      return null;
    }
  };

  const open = async () => {
    if (isDirty() && !confirm('Discard unsaved changes in the editor?')) return;
    dialog('Open from file manager', (modal, close) => {
      modal.classList.add('is-resizable');
      const treeHost = document.createElement('div');
      treeHost.className = 'codebuilder-open-tree';
      const actions = document.createElement('div');
      actions.className = 'question-dialog-actions';
      const cancel = button('Cancel');
      cancel.addEventListener('click', close);
      actions.appendChild(cancel);
      modal.append(treeHost, actions);

      renderTree(treeHost, {
        manageRoots: true,
        onSelect: async (path, type) => {
          if (type !== 'file') return;
          try {
            const opened = await Api.readManagedFile(path);
            editor.setValue(opened.content);
            managedPath = opened.path;
            markSaved(opened.path);
            status.textContent = `Opened ${opened.path}`;
            close();
          } catch (err) {
            status.textContent = `Could not open ${path}: ${err.message}`;
          }
        }
      });
    });
  };

  const loadManagedPath = async (path, expectedEditorValue = null) => {
    if (isDirty() && editor.getValue() !== expectedEditorValue) {
      status.textContent = 'Save or discard your unsaved editor changes before viewing an orchestration file.';
      return false;
    }
    const opened = await Api.readManagedFile(path);
    editor.setValue(opened.content);
    managedPath = opened.path;
    currentPath = '';
    markSaved(opened.path);
    window.dispatchEvent(new CustomEvent('novous:fs-changed'));
    return true;
  };

  const runInTerminal = async () => {
    const saved = await save();
    if (!saved && !currentPath) return;
    try {
      const { command } = await Files.runCommand(currentPath, editor.getValue());
      openTerminalWith?.(command);
      status.textContent = 'Press Enter in the terminal to run';
    } catch (err) {
      status.textContent = err.message;
    }
  };

  buttons.save?.addEventListener('click', save);
  buttons.saveAs?.addEventListener('click', saveAs);
  buttons.open?.addEventListener('click', open);
  buttons.runTerminal?.addEventListener('click', runInTerminal);
  editor.setSaveHandler?.(save);
  refreshLabel();

  return {
    refreshLabel,
    save,
    saveAs,
    open,
    loadManagedPath,
    isDirty,
    getCurrentPath: () => managedPath || currentPath,
  };
}
