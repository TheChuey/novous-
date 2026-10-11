import { attachCodeBuilderEditor } from './codebuilder_editor.js';

const DEMO_CODE = `print("Hello from Novous CodeBuilder!")
for i in range(3):
    print(f"count={i}")
`;

export async function setupCodeBuilderPage(rootId = 'codebuilder-editor') {
  const root = document.getElementById(rootId);
  const output = document.getElementById('codebuilder-output');
  const diagnostics = document.getElementById('diagnostics');
  const runButton = document.getElementById('run-code');
  const demoButton = document.getElementById('load-demo');
  const clearButton = document.getElementById('clear-console');
  const status = document.getElementById('codebuilder-status');
  const agentList = document.getElementById('codebuilder-agent-list');
  const agentStatus = document.getElementById('codebuilder-agent-status');
  const agentRefresh = document.getElementById('codebuilder-agent-refresh');
  const sidebar = document.getElementById('codebuilder-sidebar');
  const sidebarToggle = document.getElementById('codebuilder-sidebar-toggle');
  const modelSelect = document.getElementById('codebuilder-model');
  const chatForm = document.getElementById('codebuilder-chat-form');
  const chatInput = document.getElementById('codebuilder-chat-input');
  const chatMessages = document.getElementById('codebuilder-chat-messages');
  const chatStatus = document.getElementById('codebuilder-chat-status');
  const chatPanel = document.getElementById('codebuilder-chat-panel');
  const chatExpand = document.getElementById('codebuilder-chat-expand');

  if (!root || !output || !diagnostics || !runButton || !demoButton || !clearButton ||
      !agentList || !agentStatus || !agentRefresh || !sidebar || !sidebarToggle ||
      !modelSelect || !chatForm || !chatInput || !chatMessages || !chatStatus ||
      !chatPanel || !chatExpand) {
    console.error('CodeBuilder could not start because a required page element is missing.');
    return null;
  }

  const editor = await attachCodeBuilderEditor(root, DEMO_CODE);
  let agents = [];
  let selectedAgent = null;
  let defaultModel = 'qwen2.5-coder:latest';
  let chatPending = false;

  const renderDiagnostics = (items = []) => {
    diagnostics.replaceChildren();
    if (!items.length) {
      const empty = document.createElement('p');
      empty.className = 'text-muted';
      empty.textContent = 'No diagnostics reported.';
      diagnostics.appendChild(empty);
      return;
    }

    items.forEach(item => {
      const entry = document.createElement('button');
      entry.type = 'button';
      entry.className = 'diagnostic-item';
      entry.dataset.severity = item.severity || 'error';
      entry.textContent = `${item.severity || 'error'}${item.line ? ` · line ${item.line}` : ''} · ${item.message}`;
      if (item.line) {
        entry.addEventListener('click', () => editor.revealLine(item.line));
      }
      diagnostics.appendChild(entry);
    });
  };

  const runCode = async () => {
    runButton.disabled = true;
    runButton.textContent = 'Running…';
    output.textContent = 'Running Python code…';
    status.textContent = 'Running';
    diagnostics.replaceChildren();
    editor.setDiagnostics([]);

    try {
      const response = await fetch('/api/codebuilder/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: editor.getValue(), timeout_seconds: 5.0 })
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Execution failed.');
      }

      const stdout = payload.stdout || '';
      const stderr = payload.stderr || '';
      output.textContent = [stdout, stderr].filter(Boolean).join('\n').trim()
        || 'Execution completed with no output.';
      renderDiagnostics(payload.diagnostics || []);
      editor.setDiagnostics(payload.diagnostics || []);
      status.textContent = payload.status === 'SUCCESS' ? 'Finished' : 'Finished with errors';
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      output.textContent = `Error: ${message}`;
      renderDiagnostics([{ severity: 'error', message }]);
      status.textContent = 'Request failed';
      return null;
    } finally {
      runButton.disabled = false;
      runButton.textContent = '▶ Run Python';
      editor.focus();
    }
  };

  const sendCodeToEditor = (code, source = 'chat') => {
    if (typeof code !== 'string' || !code.trim()) return false;
    editor.setValue(code);
    editor.setDiagnostics([]);
    renderDiagnostics([]);
    status.textContent = source === 'agent'
      ? 'Code received from agent'
      : 'Code sent to editor';
    editor.focus();
    return true;
  };

  const handleCodeBuilderToolEvents = async (events = []) => {
    for (const event of events) {
      if (event.status !== 'success') continue;
      if (event.tool === 'send_code_to_editor') {
        const code = event.args?.code;
        if (sendCodeToEditor(code, 'agent')) {
          appendChatMessage('system', 'The agent placed its code in the Monaco editor.');
        }
      } else if (event.tool === 'run_code_in_editor') {
        appendChatMessage('system', 'The agent requested a run of the current editor code.');
        const result = await runCode();
        if (!result) {
          appendChatMessage('system', 'The editor code could not be run. See Run Output for details.');
        } else {
          appendChatMessage(
            'system',
            result.status === 'SUCCESS'
              ? 'Editor code ran successfully. See Run Output.'
              : 'Editor code ran with errors. See Run Output and Problems.'
          );
        }
      }
    }
  };

  const appendAssistantMessage = (message, content) => {
    content = String(content ?? '');
    const codeBlockPattern = /```([^\r\n`]*)\r?\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    const appendText = text => {
      if (!text) return;
      const paragraph = document.createElement('div');
      paragraph.className = 'codebuilder-chat-text';
      paragraph.textContent = text;
      message.appendChild(paragraph);
    };

    while ((match = codeBlockPattern.exec(content)) !== null) {
      appendText(content.slice(lastIndex, match.index));

      const language = match[1].trim().split(/\s+/, 1)[0].toLowerCase();
      const code = match[2];
      const isPython = !language || ['py', 'python', 'python3'].includes(language);
      const block = document.createElement('section');
      block.className = 'codebuilder-code-block';

      const heading = document.createElement('div');
      heading.className = 'codebuilder-code-heading';
      const languageLabel = document.createElement('span');
      languageLabel.textContent = isPython ? 'Python' : language;
      heading.appendChild(languageLabel);

      if (isPython) {
        const sendButton = document.createElement('button');
        sendButton.type = 'button';
        sendButton.className = 'btn btn-sm codebuilder-send-code';
        sendButton.textContent = 'Send to editor';
        sendButton.addEventListener('click', () => {
          if (sendCodeToEditor(code)) {
            sendButton.textContent = 'Sent to editor';
            sendButton.disabled = true;
          }
        });
        heading.appendChild(sendButton);
      }

      const pre = document.createElement('pre');
      const codeElement = document.createElement('code');
      codeElement.className = isPython ? 'language-python' : `language-${language || 'text'}`;
      codeElement.textContent = code;
      pre.appendChild(codeElement);
      block.append(heading, pre);
      message.appendChild(block);
      lastIndex = codeBlockPattern.lastIndex;
    }

    appendText(content.slice(lastIndex));
  };

  const appendChatMessage = (role, content) => {
    const message = document.createElement('div');
    message.className = `codebuilder-chat-message ${role}`;
    if (role === 'assistant') {
      appendAssistantMessage(message, content);
    } else {
      message.textContent = content;
    }
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  };

  const updateChatControls = () => {
    const sendButton = chatForm.querySelector('button[type="submit"]');
    chatInput.disabled = chatPending;
    sendButton.disabled = chatPending || !selectedAgent || !modelSelect.value || modelSelect.disabled;
  };

  const renderAgents = () => {
    agentList.replaceChildren();
    if (!agents.length) {
      const empty = document.createElement('p');
      empty.className = 'text-muted small';
      empty.textContent = 'No agents found in the workspace agents folder.';
      agentList.appendChild(empty);
      selectedAgent = null;
      updateChatControls();
      return;
    }

    agents.forEach(agent => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'codebuilder-agent-item';
      button.classList.toggle('selected', selectedAgent?.id === agent.id);
      button.title = agent.description || agent.name;
      button.setAttribute('aria-pressed', String(selectedAgent?.id === agent.id));
      button.disabled = chatPending;

      const name = document.createElement('span');
      name.className = 'codebuilder-agent-name';
      name.textContent = agent.name;
      const mode = document.createElement('span');
      mode.className = 'codebuilder-agent-mode';
      mode.textContent = agent.mode || 'agent';
      button.append(name, mode);
      button.addEventListener('click', () => selectAgent(agent));
      agentList.appendChild(button);
    });

    updateChatControls();
  };

  const selectAgent = (agent) => {
    selectedAgent = agent;
    renderAgents();
    const preferredModel = agent.model || defaultModel;
    if ([...modelSelect.options].some(option => option.value === preferredModel)) {
      modelSelect.value = preferredModel;
    }
    chatMessages.replaceChildren();
    appendChatMessage('system', `Chatting with ${agent.name}.`);
    chatStatus.textContent = `Agent: ${agent.name}`;
  };

  const loadAgents = async () => {
    agentRefresh.disabled = true;
    agentStatus.textContent = 'Loading agents…';
    try {
      const data = await fetch('/api/codebuilder/agents').then(async response => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || 'Could not load agents.');
        return payload;
      });
      agents = data.agents || [];
      agentStatus.textContent = `${agents.length} agent${agents.length === 1 ? '' : 's'}`;
      const selectedId = selectedAgent?.id;
      selectedAgent = agents.find(agent => agent.id === selectedId) || agents[0] || null;
      renderAgents();
      if (selectedAgent) selectAgent(selectedAgent);
    } catch (error) {
      agentStatus.textContent = 'Could not load agents.';
      const message = document.createElement('p');
      message.className = 'text-danger small';
      message.textContent = error instanceof Error ? error.message : String(error);
      agentList.replaceChildren(message);
    } finally {
      agentRefresh.disabled = false;
    }
  };

  const loadModels = async () => {
    modelSelect.replaceChildren();
    const loadingOption = document.createElement('option');
    loadingOption.textContent = 'Loading models…';
    loadingOption.value = '';
    modelSelect.appendChild(loadingOption);
    modelSelect.disabled = true;
    try {
      const response = await fetch('/api/models');
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Could not load models.');
      const models = (payload.models || []).slice().sort();
      defaultModel = payload.default || defaultModel;
      modelSelect.replaceChildren();

      const availableModels = models.length ? models : [defaultModel];
      availableModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = models.length ? model : `${model} (not detected)`;
        modelSelect.appendChild(option);
      });
      modelSelect.disabled = models.length === 0;
      if (models.length) {
        const preferredModel = selectedAgent?.model || defaultModel;
        modelSelect.value = models.includes(preferredModel) ? preferredModel : models[0];
      }
      if (!models.length) {
        chatStatus.textContent = payload.error || 'No installed models detected.';
      }
      updateChatControls();
    } catch (error) {
      modelSelect.replaceChildren();
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'Could not load models';
      modelSelect.appendChild(option);
      modelSelect.disabled = true;
      chatStatus.textContent = error instanceof Error ? error.message : String(error);
      updateChatControls();
    }
  };

  demoButton.addEventListener('click', () => {
    editor.setValue(DEMO_CODE);
    editor.setDiagnostics([]);
    status.textContent = 'Demo loaded';
    editor.focus();
  });
  clearButton.addEventListener('click', () => {
    output.textContent = 'Console cleared.';
    renderDiagnostics([]);
    editor.setDiagnostics([]);
    status.textContent = 'Ready';
  });
  runButton.addEventListener('click', runCode);
  editor.setRunHandler(runCode);
  agentRefresh.addEventListener('click', loadAgents);
  sidebarToggle.addEventListener('click', () => {
    const collapsed = sidebar.classList.toggle('collapsed');
    sidebar.closest('.codebuilder-shell').classList.toggle('sidebar-collapsed', collapsed);
    sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
    sidebarToggle.setAttribute('aria-label', collapsed ? 'Expand agent sidebar' : 'Collapse agent sidebar');
  });
  chatExpand.addEventListener('click', () => {
    const expanded = chatPanel.classList.toggle('expanded');
    chatExpand.setAttribute('aria-expanded', String(expanded));
    chatExpand.setAttribute(
      'aria-label',
      expanded ? 'Shrink chat panel' : 'Expand chat panel'
    );
    chatExpand.title = expanded ? 'Shrink chat panel' : 'Expand chat panel';
    chatExpand.textContent = expanded ? '⌄' : '⌃';
  });
  chatForm.addEventListener('submit', async event => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message || chatPending) return;
    if (!selectedAgent) {
      chatStatus.textContent = 'Select an agent before sending a message.';
      return;
    }
    if (!modelSelect.value) {
      chatStatus.textContent = 'Select an installed model before sending a message.';
      return;
    }

    appendChatMessage('user', message);
    chatInput.value = '';
    chatPending = true;
    chatStatus.textContent = `Waiting for ${selectedAgent.name}…`;
    updateChatControls();
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          agent_id: selectedAgent.id,
          model: modelSelect.value,
          session_id: `codebuilder-${selectedAgent.id}`,
          environment: 'codebuilder',
        })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'The agent request failed.');
      await handleCodeBuilderToolEvents(payload.tool_events || []);
      appendChatMessage('assistant', payload.reply || 'The agent returned an empty response.');
      chatStatus.textContent = `${selectedAgent.name} · ${payload.model || modelSelect.value}`;
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      appendChatMessage('system', `Request failed: ${messageText}`);
      chatStatus.textContent = 'Request failed';
    } finally {
      chatPending = false;
      updateChatControls();
      chatInput.focus();
    }
  });
  chatInput.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      chatForm.requestSubmit();
    }
  });

  renderDiagnostics([]);
  status.textContent = 'Ready';
  updateChatControls();
  Promise.all([loadAgents(), loadModels()]);

  return { editor, runCode, loadAgents };
}

export function renderCodeBuilderView(container) {
  if (!container) return;
  container.innerHTML = `
    <div class="codebuilder-shell">
      <div class="codebuilder-toolbar">
        <div class="codebuilder-file-label">
          <span class="codebuilder-python-icon">Py</span>
          <span>Untitled Python File</span>
          <span class="badge badge-success">Python</span>
        </div>
        <div class="codebuilder-toolbar-actions">
          <button id="load-demo" class="btn btn-sm" type="button" title="Load the sample Python program">Sample</button>
          <button id="clear-console" class="btn btn-sm" type="button" title="Clear console and diagnostics">Clear Output</button>
          <button id="run-code" class="btn btn-sm btn-primary" type="button" title="Run Python (Ctrl+Enter)">▶ Run Python</button>
        </div>
      </div>

      <main class="codebuilder-layout">
        <aside id="codebuilder-sidebar" class="codebuilder-sidebar" aria-label="Workspace agents">
          <div class="codebuilder-sidebar-heading">
            <button id="codebuilder-sidebar-toggle" class="btn btn-sm codebuilder-sidebar-toggle"
                    type="button" aria-label="Collapse agent sidebar" aria-expanded="true" title="Collapse sidebar">‹</button>
            <div class="codebuilder-sidebar-title">
              <h2>Agents</h2>
              <span id="codebuilder-agent-status" class="text-muted small">Loading…</span>
            </div>
            <button id="codebuilder-agent-refresh" class="btn btn-sm codebuilder-agent-refresh"
                    type="button" title="Refresh agents" aria-label="Refresh agents">↻</button>
          </div>
          <div id="codebuilder-agent-list" class="codebuilder-agent-list"></div>
        </aside>

        <section class="codebuilder-editor-panel" aria-label="Python editor">
          <div id="codebuilder-editor" class="editor-surface"></div>
          <div class="codebuilder-statusbar">
            <span id="codebuilder-status">Loading editor…</span>
            <span>Python</span>
            <span>UTF-8</span>
            <span>Spaces: 4</span>
          </div>
        </section>

        <aside class="codebuilder-console-panel" aria-label="Run output and diagnostics">
          <div class="codebuilder-console-heading">
            <h2>Run Output</h2>
            <span class="codebuilder-console-subtitle">Console &amp; Problems</span>
          </div>
          <section class="codebuilder-output-section">
            <h3>Console</h3>
            <pre id="codebuilder-output" class="console-output">Ready. Run your Python code to see output here.</pre>
          </section>
          <section class="codebuilder-problems-section">
            <h3>Problems</h3>
            <div id="diagnostics" class="diagnostics-list"></div>
          </section>
        </aside>
      </main>

      <section id="codebuilder-chat-panel" class="codebuilder-chat-panel" aria-label="Chat with an agent">
        <div class="codebuilder-chat-heading">
          <h2>Ask an Agent</h2>
          <span id="codebuilder-chat-status" class="text-muted small">Select an agent to start.</span>
          <button id="codebuilder-chat-expand" class="btn btn-sm codebuilder-chat-expand"
                  type="button" aria-label="Expand chat panel" aria-expanded="false"
                  title="Expand chat panel">⌃</button>
        </div>
        <div id="codebuilder-chat-messages" class="codebuilder-chat-messages" aria-live="polite">
          <div class="codebuilder-chat-message system">Messages with your selected agent appear here.</div>
        </div>
        <form id="codebuilder-chat-form" class="codebuilder-chat-form">
          <label class="codebuilder-model-picker">
            <span class="text-muted small">Model</span>
            <select id="codebuilder-model" class="form-select" aria-label="Choose model">
              <option value="">Loading models…</option>
            </select>
          </label>
          <textarea id="codebuilder-chat-input" class="form-input" rows="2"
                    placeholder="Ask the selected agent about your Python code…"
                    aria-label="Message to agent"></textarea>
          <button class="btn btn-primary" type="submit" disabled>Send</button>
        </form>
      </section>
    </div>
  `;

  setupCodeBuilderPage();
}

if (typeof window !== 'undefined' && document.readyState !== 'loading') {
  const root = document.getElementById('codebuilder-editor');
  if (root) setupCodeBuilderPage();
}
