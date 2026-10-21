import { Api } from './api.js';
import { createIcon } from './icons.js';
import { buildTestPanel } from './test_panel.js';
import { renderTree } from './tree.js';

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
      <aside class="chat-file-sidebar">
        <div class="chat-file-header">
          <h3>Workspace Files</h3>
          <span class="text-muted small">Open a file in the editor</span>
        </div>
        <div id="chat-file-tree" class="tree-pane"></div>
      </aside>

      <section class="chat-main">
        <div id="chat-messages" class="messages-scroll">
          <div class="message system-msg">Select an agent and send a message to start reasoning.</div>
        </div>
        <form id="chat-form" class="chat-input-bar">
          <input type="text" id="chat-input" placeholder="Type a message or instruction..." autocomplete="off" required />
          <button type="submit" class="btn btn-primary" disabled>Send</button>
        </form>
        <div class="chat-quick-actions">
          <button type="button" class="btn btn-sm" id="chat-reset-quick" disabled>Reset session</button>
          <button type="button" class="btn btn-sm" disabled title="Coming soon">Action 2</button>
          <button type="button" class="btn btn-sm" disabled title="Coming soon">Action 3</button>
          <button type="button" class="btn btn-sm" disabled title="Coming soon">Action 4</button>
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
    </div>`;

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

  let agents = [];
  let installedModels = [];
  let currentModel = 'qwen2.5-coder:latest';
  let isSending = false;
  let isResetting = false;
  let isSavingLog = false;

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
    saveLogButton.disabled = !hasAgent || isSavingLog;
    resetButton.disabled = !hasAgent || isResetting;
    quickResetButton.disabled = resetButton.disabled;
    const wipeButton = container.querySelector('[data-test-function="wipeChat"]');
    if (wipeButton) wipeButton.disabled = !hasAgent || isResetting;
    sendButton.disabled = !hasAgent || modelSelect.disabled || !chatInput.value.trim() || isSending;
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

  Api.getAgents().then(data => {
    agents = data.agents || [];
    agentSelect.innerHTML = agents.length
      ? agents.map(a => `<option value="${esc(a.id)}">${esc(a.name)} (${esc(a.mode)})</option>`).join('')
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
    const select = container.querySelector('#todo-file-select');
    if (!button) return;
    const hasAgent = agents.some(agent => agent.id === agentSelect.value);
    button.disabled = todoFilesLoading || todoRunInProgress || !hasAgent ||
      modelSelect.disabled || !select?.value;
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

    todoRunInProgress = true;
    syncTodoRunButton();

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
            appendToolBadge(event.tool, event.status, event.args, event.display)
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
      todoRunInProgress = false;
      syncTodoRunButton();
    }
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
    runTestSuite: runTodoSequence
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
      const res = await Api.sendMessage(text, agentId, currentModel, sessionId);
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
    if (display) appendTreeView(badgeDiv, args || {}, display);
    messagesBox.appendChild(badgeDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
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
