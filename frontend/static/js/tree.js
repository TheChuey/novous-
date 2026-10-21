import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

export function renderTree(container, options = {}) {
  const { onSelect, onSelectDirectory, onBeforeDelete, onDelete, manageRoots = false } = options;
  container.innerHTML = `
    ${manageRoots ? `
    <label class="tree-root-picker">
      <span>Workspace folder</span>
      <select class="form-select" data-root-picker aria-label="Workspace folder"></select>
      <span class="tree-root-path" data-root-path></span>
    </label>` : ''}
    <div class="tree-toolbar">
      <button class="btn btn-sm btn-primary" data-action="new-file" title="Create a file here">+ File</button>
      <button class="btn btn-sm" data-action="new-dir" title="Create a folder here">+ Folder</button>
      <button class="btn btn-sm btn-ghost" data-action="refresh" title="Refresh files">↻</button>
    </div>
    <div class="tree-root-label"><span aria-hidden="true">⌂</span> <span data-root-name>Workspace</span></div>
    <div class="tree-body" role="tree" aria-label="Workspace files"></div>`;

  const body = container.querySelector('.tree-body');
  const rootName = container.querySelector('[data-root-name]');
  const rootPicker = container.querySelector('[data-root-picker]');
  const rootPath = container.querySelector('[data-root-path]');
  let selectedDirectory = '';
  const expandedPaths = new Set();
  let knownPaths = null;
  let loading = false;

  const collectPaths = (node, out = new Set()) => {
    (node.children || []).forEach(child => {
      out.add(child.path);
      if (child.type === 'directory') collectPaths(child, out);
    });
    return out;
  };

  async function load({ silent = false } = {}) {
    if (loading) return;
    loading = true;
    if (!silent) body.innerHTML = '<p class="tree-message">Loading files…</p>';
    try {
      if (manageRoots && !silent) {
        const config = await Api.getFileManagerRoots();
        rootName.textContent = config.roots.find(root => root.path === config.active_path)?.name || 'Workspace';
        rootPicker.replaceChildren(...config.roots.map(root => {
          const option = document.createElement('option');
          option.value = root.path;
          option.textContent = root.name;
          option.selected = root.path === config.active_path;
          return option;
        }));
        rootPath.textContent = config.active_path;
      }
      const tree = await Api.getManagedFileTree();
      const paths = collectPaths(tree);
      const added = knownPaths ? [...paths].filter(path => !knownPaths.has(path)) : [];
      const changed = !knownPaths || added.length > 0 || paths.size !== knownPaths.size;
      knownPaths = paths;
      if (silent && !changed) return;
      if (!manageRoots) rootName.textContent = tree.name || 'Workspace';
      body.replaceChildren(...(tree.children || []).map(child => buildNode(child, 0)));
      added.forEach(path => {
        const row = [...body.querySelectorAll('.tree-row')].find(item => item.dataset.path === path);
        if (!row) return;
        row.classList.add('tree-new');
        setTimeout(() => row.classList.remove('tree-new'), 4000);
      });
    } catch (error) {
      if (!silent) body.innerHTML = `<p class="tree-message text-danger">${esc(error.message)}</p>`;
    } finally {
      loading = false;
    }
  }

  function buildNode(node, depth) {
    const wrapper = document.createElement('div');
    const isDirectory = node.type === 'directory';
    const row = document.createElement('div');
    row.className = 'tree-row';
    row.dataset.path = node.path;
    row.dataset.type = node.type;
    row.style.paddingLeft = `${depth * 13 + 8}px`;
    row.setAttribute('role', 'treeitem');
    const expanded = isDirectory && expandedPaths.has(node.path);
    row.setAttribute('aria-expanded', String(expanded));
    row.innerHTML = `
      <button class="tree-toggle" type="button" aria-label="${isDirectory ? 'Collapse' : 'File'}"
        ${isDirectory ? '' : 'disabled'}>${isDirectory ? (expanded ? '⌄' : '›') : ''}</button>
      <span class="tree-icon ${isDirectory ? 'directory' : 'file'}" aria-hidden="true"></span>
      <span class="tree-name" title="${esc(node.name)}">${esc(node.name)}</span>
      <button class="tree-delete" type="button" title="Delete" aria-label="Delete item">×</button>`;
    wrapper.appendChild(row);

    let children;
    if (isDirectory) {
      children = document.createElement('div');
      children.className = expanded ? 'tree-children' : 'tree-children hidden';
      children.setAttribute('role', 'group');
      (node.children || []).forEach(child => children.appendChild(buildNode(child, depth + 1)));
      wrapper.appendChild(children);
    }

    row.addEventListener('click', event => {
      if (event.target.closest('.tree-delete')) return;
      if (isDirectory) {
        selectedDirectory = node.path || '';
        body.querySelectorAll('.tree-row.selected').forEach(item => item.classList.remove('selected'));
        row.classList.add('selected');
        if (onSelectDirectory) onSelectDirectory(selectedDirectory);
        if (children) {
          const collapsed = children.classList.toggle('hidden');
          if (collapsed) expandedPaths.delete(node.path);
          else expandedPaths.add(node.path);
          row.setAttribute('aria-expanded', String(!collapsed));
          row.querySelector('.tree-toggle').textContent = collapsed ? '›' : '⌄';
        }
      } else {
        body.querySelectorAll('.tree-row.selected').forEach(item => item.classList.remove('selected'));
        row.classList.add('selected');
        if (onSelect) onSelect(node.path, node.type);
        else window.dispatchEvent(new CustomEvent('novous:file-selected', {
          detail: { path: node.path }
        }));
      }
    });

    row.querySelector('.tree-delete').addEventListener('click', async event => {
      event.stopPropagation();
      const kind = isDirectory ? 'folder and everything inside it' : 'file';
      if (onBeforeDelete && !(await onBeforeDelete(node.path, node.name, isDirectory))) return;
      if (!confirm(`Delete ${kind} "${node.name}"? This cannot be undone.`)) return;
      try {
        await Api.deleteManagedPath(node.path);
        if (selectedDirectory === node.path || selectedDirectory.startsWith(`${node.path}/`)) {
          selectedDirectory = node.path.includes('/')
            ? node.path.slice(0, node.path.lastIndexOf('/'))
            : '';
        }
        await load();
        if (onDelete) onDelete(node.path);
      } catch (error) {
        alert(`Could not delete "${node.name}": ${error.message}`);
      }
    });
    return wrapper;
  }

  async function create(kind) {
    const label = kind === 'directory' ? 'folder' : 'file';
    const name = prompt(`New ${label} name:`);
    if (!name || !name.trim()) return;
    const filename = name.trim();
    if (filename === '.' || filename === '..' || /[\\/]/.test(filename)) {
      alert('Enter a name without folder separators.');
      return;
    }
    const path = [selectedDirectory, filename].filter(Boolean).join('/');
    try {
      await Api.createManagedPath(path, kind);
      await load();
      if (kind === 'file') {
        if (onSelect) onSelect(path, 'file');
        else window.dispatchEvent(new CustomEvent('novous:file-selected', {
          detail: { path }
        }));
      }
    } catch (error) {
      alert(`Could not create ${label}: ${error.message}`);
    }
  }

  container.querySelector('[data-action="refresh"]').addEventListener('click', () => load());
  if (rootPicker) {
    rootPicker.addEventListener('change', async () => {
      rootPicker.disabled = true;
      try {
        await Api.selectFileManagerRoot(rootPicker.value);
        selectedDirectory = '';
        expandedPaths.clear();
        await load();
      } catch (error) {
        alert(`Could not change workspace folder: ${error.message}`);
        await load();
      } finally {
        rootPicker.disabled = false;
      }
    });
  }
  container.querySelector('[data-action="new-file"]').addEventListener('click', () => create('file'));
  container.querySelector('[data-action="new-dir"]').addEventListener('click', () => create('directory'));

  load();

  // Pick up files written elsewhere (agent tools, memory mode): poll and listen for change events.
  const silentReload = () => {
    if (!container.isConnected) {
      clearInterval(pollTimer);
      window.removeEventListener('novous:fs-changed', silentReload);
      return;
    }
    if (!document.hidden) load({ silent: true });
  };
  const pollTimer = setInterval(silentReload, 3000);
  window.addEventListener('novous:fs-changed', silentReload);

  return { reload: load };
}
