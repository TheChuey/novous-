import { Api } from './api.js';
import { buildTestPanel } from './test_panel.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Interactive Chat Console Component: agent selection, message history,
 * and tool execution badges.
 */
export function renderChatView(container) {
  container.innerHTML = `
    <div class="chat-layout">
      <aside class="chat-sidebar">
        <h3>Agents Workspace</h3>
        <select id="chat-agent-select" class="form-select">
          <option value="">Loading agents...</option>
        </select>
        <div id="agent-meta-card" class="card mt-3">
          <p class="text-muted">Select an agent to begin chatting.</p>
        </div>
        <div class="chat-sidebar-actions">
          <label class="checkbox-row">
            <input type="checkbox" id="chat-use-tools" checked>
            <span>Attach tools (agent mode)</span>
          </label>
          <button class="btn btn-sm btn-primary" id="chat-save-log">Save Session Log (.md)</button>
          <label class="model-picker">
            <span class="model-picker-label">Model <span id="model-count" class="text-muted small"></span></span>
            <select id="chat-model-select" class="form-select"><option value="">Detecting models…</option></select>
          </label>
          <button class="btn btn-sm" id="chat-reset">Reset session</button>
        </div>
        <div id="chat-session-info" class="text-muted small mt-3"></div>
      </aside>

      <section class="chat-main">
        <div id="chat-messages" class="messages-scroll">
          <div class="message system-msg">Select an agent and send a message to start reasoning.</div>
        </div>
        <form id="chat-form" class="chat-input-bar">
          <input type="text" id="chat-input" placeholder="Type a message or instruction..." autocomplete="off" required />
          <button type="submit" class="btn btn-primary">Send</button>
        </form>
      </section>

      <aside class="test-panel">
        <div class="test-panel-header">
          <span class="test-panel-title">Test</span>
        </div>
        <div class="test-panel-content">
          <div id="testPanelButtons" class="test-grid"></div>
        </div>
      </aside>
    </div>`;

  const agentSelect = container.querySelector('#chat-agent-select');
  const metaCard = container.querySelector('#agent-meta-card');
  const messagesBox = container.querySelector('#chat-messages');
  const chatForm = container.querySelector('#chat-form');
  const chatInput = container.querySelector('#chat-input');
  const toolsToggle = container.querySelector('#chat-use-tools');
  const sessionInfo = container.querySelector('#chat-session-info');
  const modelSelect = container.querySelector('#chat-model-select');
  const modelCount = container.querySelector('#model-count');

  let agents = [];
  let installedModels = [];
  let currentModel = 'qwen2.5-coder:latest';

  Api.getModels().then(data => {
    installedModels = (data.models || []).sort();
    if (!installedModels.length) {
      modelCount.textContent = '(none installed)';
      modelSelect.innerHTML = '<option value="">No models found — run: ollama pull</option>';
      modelSelect.disabled = true;
      return;
    }
    modelCount.textContent = `(${installedModels.length} installed)`;
    modelSelect.innerHTML = installedModels
      .map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('');
    modelSelect.disabled = false;
    syncModelSelect();
  }).catch(err => {
    modelCount.textContent = '(error)';
    modelSelect.innerHTML = `<option value="">Model list unavailable: ${esc(err.message)}</option>`;
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
  });

  Api.getAgents().then(data => {
    agents = data.agents || [];
    agentSelect.innerHTML = agents.length
      ? agents.map(a => `<option value="${esc(a.id)}">${esc(a.name)} (${esc(a.mode)})</option>`).join('')
      : '<option value="">No agents found</option>';
    if (agents.length > 0) { updateAgentMeta(agents[0].id); syncModelSelect(); }
  }).catch(err => {
    agentSelect.innerHTML = `<option value="">Error: ${esc(err.message)}</option>`;
  });

  agentSelect.addEventListener('change', (e) => { updateAgentMeta(e.target.value); syncModelSelect(); });

  function updateAgentMeta(id) {
    const agent = agents.find(a => a.id === id);
    if (!agent) return;
    if (agent.model) currentModel = agent.model;
    metaCard.innerHTML = `
      <h4>${esc(agent.name)}</h4>
      <p><span class="badge ${agent.mode === 'agent' ? 'badge-accent' : 'badge-success'}">${esc((agent.mode || '').toUpperCase())}</span></p>
      <p>${esc(agent.description || 'No description provided.')}</p>
      <p class="text-muted small">Model: ${esc(currentModel)}<br>
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

    try {
      await Api.resetChat(`chat-${agentId}`);
      messagesBox.innerHTML = `<div class="message system-msg">${esc(message)}</div>`;
    } catch (err) {
      appendMessage('system', 'Reset failed: ' + err.message);
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
  async function loadTodoFiles(silent = false) {
    const select = container.querySelector('#todo-file-select');
    if (!select || todoFilesLoading) return;
    todoFilesLoading = true;

    try {
      const tree = await Api.getFileTree();
      const workspaceEntries = tree.children || [];
      const normalizedNames = new Set(['todo list', 'do due list']);
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
    }
  }

  async function runTodoSequence() {
    const select = container.querySelector('#todo-file-select');
    const selectedPath = select?.value;
    const agentId = agentSelect.value;

    if (!selectedPath) {
      appendMessage('system', 'Please select a file from the To-Do dropdown first.');
      return;
    }
    if (!agentId) {
      appendMessage('system', 'Please select an agent before running To-Do items.');
      return;
    }

    const runButton = container.querySelector('[data-test-function="runTestSuite"]');
    if (runButton) runButton.disabled = true;

    try {
      const fileData = await Api.readFile(selectedPath);
      const lines = String(fileData.content ?? '')
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(Boolean);

      appendMessage('user', `Starting execution of To-Do items from: ${selectedPath.split('/').pop()}`);
      if (!lines.length) {
        appendMessage('system', 'The selected file contains no nonblank task lines.');
        return;
      }

      const sessionId = `chat-${agentId}`;
      const model = currentModel;
      await delay(1500);

      for (let index = 0; index < lines.length; index += 1) {
        const line = lines[index];
        appendMessage('user', `Task ${index + 1}: ${line}`);
        const thinkingId = appendMessage('assistant', 'Thinking...', true);
        try {
          const response = await Api.sendMessage(line, agentId, model, sessionId);
          removeMessage(thinkingId);
          (response.tool_events || []).forEach(event =>
            appendToolBadge(event.tool, event.status, event.args)
          );
          appendMessage('assistant', response.reply);
        } catch (err) {
          removeMessage(thinkingId);
          throw err;
        }

        if (index < lines.length - 1) await delay(1000);
      }
    } catch (err) {
      appendMessage('system', `Error reading or running To-Do file: ${err.message}`);
    } finally {
      if (runButton) runButton.disabled = false;
    }
  }

  container.querySelector('#chat-reset').addEventListener('click', () => resetSession());
  container.querySelector('#chat-save-log').addEventListener('click', async () => {
    const agentId = agentSelect.value;
    if (!agentId) {
      alert('Select an agent before saving the session log.');
      return;
    }

    try {
      const res = await Api.exportSession(`chat-${agentId}`);
      alert(res.locationChosen
        ? `Session log saved as ${res.filename} in the location you selected.`
        : `Session log download started: ${res.filename}\n\nChoose the save location in your browser's download settings.`);
    } catch (err) {
      if (err.name !== 'AbortError') alert(`Failed to save session: ${err.message}`);
    }
  });
  buildTestPanel('testPanelButtons', {
    diagnostics: openDiagnostics,
    wipeChat,
    runTestSuite: runTodoSequence
  });
  loadTodoFiles();
  container.querySelector('#todo-file-refresh')
    ?.addEventListener('click', () => loadTodoFiles());
  const todoRefreshInterval = setInterval(() => {
    if (!container.isConnected) {
      clearInterval(todoRefreshInterval);
      return;
    }
    loadTodoFiles(true);
  }, 5000);

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    const agentId = agentSelect.value;
    if (!text || !agentId) return;

    appendMessage('user', text);
    chatInput.value = '';

    const thinkingId = appendMessage('assistant', 'Thinking...', true);

    try {
      const sessionId = `chat-${agentId}`;
      const res = await Api.sendMessage(text, agentId, currentModel, sessionId);
      removeMessage(thinkingId);

      if (res.tool_events && res.tool_events.length > 0) {
        res.tool_events.forEach(evt => appendToolBadge(evt.tool, evt.status, evt.args));
      }

      appendMessage('assistant', res.reply);
    } catch (err) {
      removeMessage(thinkingId);
      appendMessage('system', 'Error communicating with engine: ' + err.message);
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
      copyButton.type = 'button';
      copyButton.className = 'btn btn-sm btn-ghost msg-copy-btn';
      copyButton.innerText = 'Copy';
      copyButton.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(content);
          copyButton.innerText = 'Copied!';
          setTimeout(() => { copyButton.innerText = 'Copy'; }, 2000);
        } catch (err) {
          copyButton.innerText = 'Copy failed';
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

  function appendToolBadge(toolName, status, args) {
    const badgeDiv = document.createElement('div');
    badgeDiv.className = `tool-badge ${status}`;
    const argText = args ? JSON.stringify(args) : '';
    badgeDiv.innerHTML = `🛠️ <strong>${esc(toolName)}</strong> executed (${esc(status)})
      ${argText ? `<span class="text-muted small"> ${esc(argText.slice(0, 120))}</span>` : ''}`;
    messagesBox.appendChild(badgeDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }
}
