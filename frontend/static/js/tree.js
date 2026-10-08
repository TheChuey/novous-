import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

/**
 * Interactive File Tree Component.
 * @param {HTMLElement} container
 * @param {{onSelect?: (path: string, type: string) => void, selectable?: string}} options
 */
export function renderTree(container, options = {}) {
  const { onSelect, selectable = 'file' } = options;

  container.innerHTML = `
    <div class="tree-toolbar">
      <button class="btn btn-sm" data-action="refresh" title="Refresh">⟳ Refresh</button>
      <button class="btn btn-sm" data-action="new-file" title="New file">+ File</button>
      <button class="btn btn-sm" data-action="new-dir" title="New folder">+ Dir</button>
    </div>
    <div class="tree-body" role="tree"></div>`;

  const body = container.querySelector('.tree-body');

  async function load() {
    try {
      const tree = await Api.getFileTree('');
      body.innerHTML = '';
      body.appendChild(buildNode(tree, 0));
    } catch (err) {
      body.innerHTML = `<p class="text-danger">${esc(err.message)}</p>`;
    }
  }

  function buildNode(node, depth) {
    const row = document.createElement('div');
    row.className = 'tree-row';
    row.dataset.path = node.path;
    row.dataset.type = node.type;
    row.style.paddingLeft = `${depth * 14 + 6}px`;
    row.setAttribute('role', 'treeitem');

    const isDir = node.type === 'directory';
    row.innerHTML = `
      <span class="tree-icon">${isDir ? '▾' : '·'}</span>
      <span class="tree-name">${esc(node.name)}</span>`;

    const wrap = document.createElement('div');
    wrap.appendChild(row);

    row.addEventListener('click', (e) => {
      e.stopPropagation();
      if (isDir) {
        const kids = wrap.querySelector(':scope > .tree-children');
        if (kids) {
          const hidden = kids.classList.toggle('hidden');
          row.querySelector('.tree-icon').textContent = hidden ? '▸' : '▾';
        }
      } else {
        body.querySelectorAll('.tree-row.selected').forEach(r => r.classList.remove('selected'));
        row.classList.add('selected');
        if (onSelect) onSelect(node.path, node.type);
      }
    });

    if (isDir && node.children && node.children.length) {
      const kidsWrap = document.createElement('div');
      kidsWrap.className = 'tree-children';
      node.children.forEach(child => kidsWrap.appendChild(buildNode(child, depth + 1)));
      wrap.appendChild(kidsWrap);
    } else if (isDir) {
      const kidsWrap = document.createElement('div');
      kidsWrap.className = 'tree-children hidden';
      wrap.appendChild(kidsWrap);
    }
    return wrap;
  }

  container.querySelector('[data-action="refresh"]').addEventListener('click', load);

  container.querySelector('[data-action="new-file"]').addEventListener('click', async () => {
    const path = prompt('New file path (relative to workspace):');
    if (!path) return;
    try {
      await Api.createPath(path, 'file');
      load();
      if (onSelect) onSelect(path, 'file');
    } catch (err) { alert(err.message); }
  });

  container.querySelector('[data-action="new-dir"]').addEventListener('click', async () => {
    const path = prompt('New folder path (relative to workspace):');
    if (!path) return;
    try {
      await Api.createPath(path, 'directory');
      load();
    } catch (err) { alert(err.message); }
  });

  load();
  return { reload: load };
}
