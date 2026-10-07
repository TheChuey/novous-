import API from './api.js';

const state = {
  agents: [],
  queue: []
};

const $ = (id) => document.getElementById(id);

export function initOrchestrator() {
  const runButton = $('orchestratorRunBtn');
  const clearButton = $('orchestratorClearBtn');
  if (!runButton || !clearButton) return;

  runButton.addEventListener('click', runOrchestrator);
  clearButton.addEventListener('click', () => {
    state.queue = [];
    renderChecklist();
    renderQueue();
    setStatus('');
  });

  loadOrchestratorOptions();
}

function setStatus(message) {
  const status = $('orchestratorStatus');
  if (status) status.textContent = message;
}

function agentLabel(agent) {
  return agent.source === 'workspace' ? `${agent.name} (workspace)` : agent.name;
}

async function loadOrchestratorOptions() {
  const agentsHost = $('orchestratorAgents');
  const modelSelect = $('orchestratorModel');
  if (!agentsHost || !modelSelect) return;

  agentsHost.textContent = 'Loading agents...';
  try {
    const agentData = await API.agents();
    state.agents = agentData.agents || [];
    renderChecklist();
    renderQueue();
  } catch (error) {
    agentsHost.textContent = `Failed to load agents: ${error.message}`;
    setStatus(`Could not load agents: ${error.message}`);
    return;
  }

  try {
    const modelData = await API.models();
    modelSelect.replaceChildren(new Option('Default agent models', ''));
    for (const model of modelData.models || []) {
      modelSelect.add(new Option(model.name || model.id, model.id));
    }
  } catch (error) {
    modelSelect.replaceChildren(new Option('Default agent models', ''));
    setStatus(`Agents loaded; model list unavailable: ${error.message}`);
  }
}

function renderChecklist() {
  const host = $('orchestratorAgents');
  if (!host) return;
  host.replaceChildren();
  if (!state.agents.length) {
    host.textContent = 'No agents found.';
    return;
  }

  for (const agent of state.agents) {
    const key = agent.source === 'workspace' ? agent.md_path : agent.id;
    const row = document.createElement('label');
    row.className = 'agent-option';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = key || agent.id;
    checkbox.disabled = !agent.complete;
    checkbox.checked = state.queue.some((item) => item.key === key);
    checkbox.addEventListener('change', () => toggleAgent(agent, checkbox.checked));
    row.appendChild(checkbox);

    const name = document.createElement('span');
    name.textContent = agent.complete
      ? agentLabel(agent)
      : `${agentLabel(agent)} (incomplete)`;
    row.appendChild(name);
    if (!agent.complete) row.title = 'This agent needs both agent.json and agent.md.';
    host.appendChild(row);
  }
}

function toggleAgent(agent, checked) {
  const key = agent.source === 'workspace' ? agent.md_path : agent.id;
  if (checked) {
    if (!state.queue.some((item) => item.key === key)) {
      state.queue.push({
        key,
        id: agent.id,
        name: agent.name || agent.id,
        json_path: agent.json_path || null,
        md_path: agent.md_path || null
      });
    }
  } else {
    state.queue = state.queue.filter((item) => item.key !== key);
  }
  renderQueue();
}

function renderQueue() {
  const host = $('orchestratorQueue');
  if (!host) return;
  host.replaceChildren();
  if (!state.queue.length) {
    host.textContent = 'Queue empty - select agents above to add them.';
    return;
  }

  state.queue.forEach((agent, index) => {
    const row = document.createElement('div');
    row.className = 'queue-item';

    const position = document.createElement('span');
    position.className = 'qidx';
    position.textContent = `${index + 1}.`;
    row.appendChild(position);

    const name = document.createElement('span');
    name.className = 'queue-agent-name';
    name.textContent = agent.name;
    name.title = agent.id;
    row.appendChild(name);

    const addMoveButton = (label, title, action, disabled) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = label;
      button.title = title;
      button.disabled = disabled;
      button.addEventListener('click', action);
      row.appendChild(button);
    };

    addMoveButton('↑', 'Move agent up', () => moveStep(index, -1), index === 0);
    addMoveButton('↓', 'Move agent down', () => moveStep(index, 1), index === state.queue.length - 1);
    addMoveButton('×', 'Remove agent', () => {
      state.queue = state.queue.filter((item) => item.key !== agent.key);
      renderChecklist();
      renderQueue();
    }, false);
    host.appendChild(row);
  });
}

function moveStep(index, delta) {
  const target = index + delta;
  if (target < 0 || target >= state.queue.length) return;
  const [agent] = state.queue.splice(index, 1);
  state.queue.splice(target, 0, agent);
  renderQueue();
}

function renderResults(result) {
  const host = $('orchestratorResult');
  if (!host) return;
  host.replaceChildren();

  for (const [index, output] of (result.outputs || []).entries()) {
    const card = document.createElement('section');
    card.className = 'orchestrator-result-item';
    const heading = document.createElement('h3');
    heading.textContent = `Agent ${index + 1}: ${output.agent_name || 'Agent'}`;
    const body = document.createElement('p');
    body.textContent = output.output || '(No reply)';
    card.append(heading, body);
    host.appendChild(card);
  }

  const final = document.createElement('section');
  final.className = 'orchestrator-result-item';
  const heading = document.createElement('h3');
  heading.textContent = 'Final reply';
  const body = document.createElement('p');
  body.textContent = result.reply || '(No final reply)';
  final.append(heading, body);
  host.appendChild(final);
  host.hidden = false;
}

async function runOrchestrator() {
  if (!state.queue.length) {
    setStatus('Select at least one complete agent.');
    return;
  }
  const message = $('orchestratorMessage').value.trim();
  if (!message) {
    setStatus('Enter a message for the agent sequence.');
    return;
  }

  const button = $('orchestratorRunBtn');
  button.disabled = true;
  $('orchestratorResult').hidden = true;
  setStatus(`Running orchestrator with ${state.queue.length} agent(s)...`);

  const steps = state.queue.map((agent) => agent.json_path
    ? { json_path: agent.json_path, md_path: agent.md_path }
    : agent.id);

  try {
    const result = await API.pipelineRun({
      steps,
      message,
      model: $('orchestratorModel').value || null
    });
    renderResults(result);
    setStatus('Orchestrator completed.');
  } catch (error) {
    setStatus(`Orchestrator failed: ${error.message}`);
  } finally {
    button.disabled = false;
  }
}
