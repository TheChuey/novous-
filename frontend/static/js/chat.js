import { Api } from './api.js';
import { buildTestPanel } from './test_panel.js';

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

  container.querySelector('#chat-reset').addEventListener('click', () => resetSession());
  buildTestPanel('testPanelButtons', { diagnostics: openDiagnostics, wipeChat });

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
    msgDiv.innerText = content;
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
