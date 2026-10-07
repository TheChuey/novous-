/* Chat popup module */
import API from './api.js';
import Session from './session.js';
import { assignAgentColors } from './agentColors.js';
import { initTopbar } from './topbar.js';

const log = document.getElementById('chatLog');
const form = document.getElementById('chatForm');
const input = document.getElementById('chatInput');
const sendBtn = document.getElementById('chatSend');
const status = document.getElementById('chatStatus');
const agentSelect = document.getElementById('agentSelect');
const modelSelect = document.getElementById('modelSelect');
const agentChip = document.getElementById('activeAgentChip');
const agentName = document.getElementById('activeAgentName');
const savedChatsList = document.getElementById('savedChatsList');

/* Agent id requested by the home page card, e.g. /chat?agent=rag_assistant */
const requestedAgent = new URLSearchParams(window.location.search).get('agent');

let agentColorById = new Map();
let currentThread = [];
let activeSessionId = null;
let selectedSkill = null;

const skillSelect = document.getElementById('skillSelect');
const skillNameInput = document.getElementById('skillName');
const skillContentInput = document.getElementById('skillContent');
const saveSkillButton = document.getElementById('saveSkill');

function appendLine(role, text, meta = '', labelText = null) {
  const line = document.createElement('div');
  line.className = 'msg ' + role;
  const label = document.createElement('span');
  label.className = 'msg-label';
  label.textContent = labelText
    || (role === 'user' ? 'You' : role === 'event' ? 'Event' : 'System');
  const body = document.createElement('span');
  body.className = 'msg-body';
  body.textContent = text;
  line.appendChild(label);
  line.appendChild(body);
  if (meta) {
    const ts = document.createElement('span');
    ts.className = 'msg-meta';
    ts.textContent = meta;
    line.appendChild(ts);
  }
  /* Every real message gets a copy button; the handler is the global
     copyMsg() in chat.html, shared with the saved-session rows. */
  const actions = document.createElement('span');
  actions.className = 'msg-actions';
  const copyBtn = document.createElement('button');
  copyBtn.type = 'button';
  copyBtn.className = 'btn-msg-action';
  copyBtn.title = 'Copy this message';
  copyBtn.innerHTML = '<i data-lucide="copy" style="width:13px;"></i> Copy';
  copyBtn.addEventListener('click', () => copyText(body.textContent, 'Message copied to clipboard'));
  actions.appendChild(copyBtn);
  line.appendChild(actions);
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
  if (window.lucide) window.lucide.createIcons();
}

/* Clipboard write with a textarea fallback, because the async
   clipboard API is unavailable on http:// origins. */
function copyText(text, message) {
  const area = document.createElement('textarea');
  area.value = text;
  document.body.appendChild(area);
  area.select();
  try {
    document.execCommand('copy');
    showToast(message);
  } catch (e) {
    showToast('Copy failed - select the text manually');
  } finally {
    document.body.removeChild(area);
  }
}

function appendTools(tools) {
  if (!tools || !tools.length) return;
  const detail = document.createElement('details');
  detail.className = 'msg event';
  const summary = document.createElement('summary');
  summary.className = 'msg-label';
  summary.textContent = 'Tools used: ' + tools.map(t => t.tool || '').filter(Boolean).join(', ');
  detail.appendChild(summary);
  const body = document.createElement('div');
  body.className = 'msg-body';
  body.textContent = tools.map(t => {
    const args = t.args ? JSON.stringify(t.args).slice(0, 400) : '';
    const ok = t.op_ok ? 'ok' : (t.status || '?');
    return `› ${t.tool} (${ok}) ${args}`;
  }).join('\n');
  detail.appendChild(body);
  log.appendChild(detail);
  log.scrollTop = log.scrollHeight;
}

function setStatus(text) {
  if (status) status.textContent = text;
}

// ---- Agent / model selector population ----

function activeAgentId() {
  return agentSelect && agentSelect.value ? agentSelect.value : null;
}

function agentLabel(id) {
  if (!id) return 'No agent selected';
  const opt = agentSelect ? agentSelect.querySelector(`option[value="${CSS.escape(id)}"]`) : null;
  return opt ? opt.textContent : id;
}

function paintAgentChip() {
  const id = activeAgentId();
  if (!agentChip || !agentName) return;
  if (!id) {
    agentChip.hidden = true;
    return;
  }
  const color = agentColorById.get(id) || '#4fc3f7';
  agentChip.style.setProperty('--agent-color', color);
  agentName.textContent = agentLabel(id);
  agentChip.hidden = false;
  if (input) {
    input.placeholder = `Message ${agentLabel(id)}...`;
  }
}

async function populateAgents() {
  try {
    const data = await API.agents();
    const agents = data.agents || [];
    agentColorById = assignAgentColors(agents);
    const savedAgent = localStorage.getItem('pmAgent');
    agentSelect.innerHTML = '';
    for (const a of agents) {
      const opt = document.createElement('option');
      opt.value = a.id;
      opt.textContent = a.source === 'workspace' ? `${a.name} (ws)` : a.name;
      if (a.id === savedAgent) opt.selected = true;
      agentSelect.appendChild(opt);
    }
    /* An explicit ?agent= from a home card outranks the saved choice. */
    const preferred = agents.some(a => a.id === requestedAgent) ? requestedAgent : savedAgent;
    if (preferred) agentSelect.value = preferred;
    if (!agentSelect.value && agents.length) agentSelect.value = agents[0].id;
    if (agentSelect.value) localStorage.setItem('pmAgent', agentSelect.value);
    paintAgentChip();
  } catch (e) {
    console.warn('Failed to load agents', e);
  }
}

async function populateModels() {
  try {
    const data = await API.models();
    const models = data.models || [];
    const savedModel = localStorage.getItem('pmModel') || '';
    modelSelect.innerHTML = '';
    const empty = document.createElement('option');
    empty.value = '';
    empty.textContent = 'default model';
    modelSelect.appendChild(empty);
    for (const m of models) {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.name;
      modelSelect.appendChild(opt);
    }
    if (savedModel) modelSelect.value = savedModel;
  } catch (e) {
    console.warn('Failed to load models', e);
  }
}

async function populateSelectors() {
  await populateAgents();
  await populateModels();

  agentSelect.addEventListener('change', async () => {
    localStorage.setItem('pmAgent', agentSelect.value);
    paintAgentChip();
    currentThread = [];
    activeSessionId = null;
    showEmptyChat();
    await renderSavedChats();
  });

  modelSelect.addEventListener('change', () => {
    localStorage.setItem('pmModel', modelSelect.value);
  });
}

async function refreshAgents() {
  await populateAgents();
}

function showEmptyChat() {
  log.innerHTML = '';
  appendLine('system', `No unsaved messages with ${agentLabel(activeAgentId())}. Open a saved session or start a new chat.`);
}

async function sendMessage() {
  const userMessage = input.value.trim();
  if (!userMessage) return;
  const skillContent = selectedSkill ? skillContentInput.value.trim() : '';
  const skillName = selectedSkill ? skillNameInput.value.trim() || selectedSkill.name : '';
  const message = skillContent
    ? `Skill: ${skillName}\n\n${skillContent}\n\nUser message:\n${userMessage}`
    : userMessage;
  const agentId = activeAgentId();
  input.value = '';
  const ts = new Date().toISOString();
  currentThread.push({ ts, sender: 'user', message, agent: agentId });
  appendLine('user', message, new Date(ts).toLocaleTimeString());
  setStatus('Running agent…');
  sendBtn.disabled = true;
  try {
    const result = await API.chatSend(
      message,
      agentId,
      modelSelect ? modelSelect.value || null : null,
      currentThread.slice(-41, -1).map((entry) => ({
        role: entry.sender === 'user' ? 'user' : 'assistant',
        content: entry.message
      }))
    );
    const who = agentLabel(result.agent_id || agentId);
    const reply = result.reply || '(empty reply)';
    const replyTs = new Date().toISOString();
    currentThread.push({ ts: replyTs, sender: 'agent', message: reply, agent: result.agent_id || agentId });
    appendLine('system', reply, new Date(replyTs).toLocaleTimeString(), who);
    appendTools(result.tool_events || []);
    setStatus(`${who} · ${result.model || 'model'} replied.`);
  } catch (error) {
    setStatus('Send failed: ' + error.message);
  } finally {
    sendBtn.disabled = false;
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  sendMessage();
});

sendBtn.addEventListener('click', sendMessage);

Session.onEvent = (msg) => {
  if (msg.type === 'event' && msg.event) {
    const ev = msg.event;
    const what = ev.type || 'event';
    const path = ev.path || '';
    appendLine('event', what + (path ? ': ' + path : ''));
  }
};

/* The agent must be resolved before history loads, otherwise the
   first paint would show the previous agent's thread. */
initTopbar({ page: 'chat' });
populateSelectors()
  .then(() => {
    showEmptyChat();
    renderSavedChats();
    loadSkills();
  })
  .catch((e) => setStatus('Failed to start: ' + e.message));
Session.connect();

// ---- New agent scaffold + wipe chat (exposed for inline handlers) ----

async function scaffoldNewAgent() {
  const name = prompt('New agent id / folder name (e.g. "doc_writer"):');
  if (!name) return;
  if (!/^[A-Za-z0-9_\-]+$/.test(name)) {
    alert('Use only letters, numbers, underscore or dash.');
    return;
  }
  const rel = `workspace/agents/${name}`;
  const json = JSON.stringify({
    id: name,
    name: name.replace(/[_-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    description: 'A custom agent scaffolded from the AI Agent Creator.',
    mode: 'agent',
    model: '',
    tools: ['map_files', 'read_file', 'write_text_file']
  }, null, 2);
  const md =
    `# ${name}\n` +
    `\n## role\n` +
    `\nYou are ${name}, a helpful Project Manager agent.\n` +
    `\n## purpose\n` +
    `\nDescribe what this agent accomplishes and when it is used.\n` +
    `\n## boundaries\n` +
    `\nState what this agent will not do.\n` +
    `\n## output format\n` +
    `\nDescribe the shape of the reply the agent must produce.\n`;
  try {
    await API.fileCreate(`${rel}/agent.json`, json);
    await API.fileCreate(`${rel}/agent.md`, md);
    localStorage.setItem('pmAgent', name);
    await refreshAgents();
    window.open(`/editor?path=${encodeURIComponent(`${rel}/agent.json`)}&root=workspace`, '_blank');
    setStatus(`Created ${rel}/agent.json + agent.md`);
    showToast(`Agent '${name}' created`);
  } catch (e) {
    alert('Failed to scaffold agent: ' + e.message);
  }
}

async function wipeChat() {
  const who = agentLabel(activeAgentId());
  if (!confirm(`Clear the unsaved chat with ${who}? Saved session files will remain.`)) return;
  currentThread = [];
  activeSessionId = null;
  showEmptyChat();
  setStatus('Unsaved chat cleared');
  showToast('Unsaved chat cleared');
}

/* ================================================================
   SAVED CHAT SESSIONS
   ================================================================
   A session text file under workspace/data/chat_sessions/<agent_id>/
   is the only persistent source for its conversation. */

function sessionText(record) {
  const lines = [
    `# ${record.title || 'Chat session'}`,
    '',
    `Agent: ${record.agent_id}`,
    `Saved: ${record.created || ''}`,
    ''
  ];
  for (const entry of record.entries || []) {
    const who = entry.sender === 'user' ? 'You' : (entry.agent || 'Agent');
    const ts = entry.ts ? new Date(entry.ts).toLocaleString() : '';
    lines.push(`## ${who}${ts ? ' - ' + ts : ''}`, '', entry.message || '', '');
  }
  return lines.join('\n');
}

function sessionStamp(created) {
  if (!created) return '';
  const when = new Date(created);
  if (isNaN(when.getTime())) return created;
  return when.toLocaleString();
}

function rowAction(icon, title, handler) {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'btn-row-action';
  btn.title = title;
  btn.setAttribute('aria-label', title);
  btn.innerHTML = `<i data-lucide="${icon}" style="width:13px;"></i>`;
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    handler();
  });
  return btn;
}

function sessionRow(session) {
  const agentId = activeAgentId();
  const item = document.createElement('div');
  item.className = 'saved-chat-item';
  item.title = 'Open this saved session';

  const info = document.createElement('div');
  info.className = 'saved-chat-info';
  const title = document.createElement('div');
  title.className = 'saved-chat-title';
  title.textContent = session.title || session.id;
  const meta = document.createElement('div');
  meta.className = 'saved-chat-date';
  const count = session.entry_count === 1 ? '1 message' : `${session.entry_count} messages`;
  meta.textContent = `${count} · ${sessionStamp(session.created)}`;
  info.appendChild(title);
  info.appendChild(meta);

  const actions = document.createElement('div');
  actions.className = 'saved-chat-actions';

  actions.appendChild(rowAction('message-square', 'Open in chat', () => {
    openSavedSession(session.id, agentId);
  }));

  actions.appendChild(rowAction('copy', 'Copy transcript', () => {
    copySavedSession(session.id, agentId);
  }));

  /* An anchor, not a button: the endpoint answers with a
     Content-Disposition attachment, so a plain link hands the file
     to the browser's own download handling and can also be
     right-clicked into "Save as". */
  const download = document.createElement('a');
  download.className = 'btn-row-action';
  download.href = API.chatSessionExportUrl(session.id, agentId, 'txt');
  download.download = '';
  download.title = 'Download text session';
  download.setAttribute('aria-label', 'Download to disk');
  download.innerHTML = '<i data-lucide="download" style="width:13px;"></i>';
  download.addEventListener('click', (e) => e.stopPropagation());
  actions.appendChild(download);

  actions.appendChild(rowAction('trash-2', 'Delete this saved session', () => {
    deleteSavedSession(session, agentId);
  }));

  item.appendChild(info);
  item.appendChild(actions);
  item.addEventListener('click', () => openSavedSession(session.id, agentId));
  return item;
}

function emptySessionRow(text) {
  const item = document.createElement('div');
  item.className = 'saved-chat-empty';
  item.textContent = text;
  return item;
}

async function renderSavedChats() {
  if (!savedChatsList) return;
  const agentId = activeAgentId();
  savedChatsList.innerHTML = '';
  if (!agentId) {
    savedChatsList.appendChild(emptySessionRow('Select an agent to see its saved sessions.'));
    return;
  }
  try {
    const data = await API.chatSessions(agentId);
    const sessions = data.sessions || [];
    if (!sessions.length) {
      savedChatsList.appendChild(
        emptySessionRow(`No saved sessions for ${agentLabel(agentId)} yet. Use Save Session to keep a copy of this thread.`)
      );
      return;
    }
    for (const session of sessions) {
      savedChatsList.appendChild(sessionRow(session));
    }
    if (window.lucide) window.lucide.createIcons();
  } catch (e) {
    savedChatsList.appendChild(emptySessionRow('Could not load saved sessions: ' + e.message));
  }
}

async function saveCurrentChat() {
  const agentId = activeAgentId();
  if (!agentId) {
    showToast('Select an agent first');
    return;
  }
  if (!currentThread.length) {
    showToast('There is no conversation to save');
    return;
  }
  const suggested = currentThread.find((entry) => entry.sender === 'user')?.message || '';
  const title = prompt(
    `Save the current ${agentLabel(agentId)} thread as a named session:`,
    suggested ? suggested.slice(0, 60) : ''
  );
  if (title === null) return;
  try {
    const res = await API.chatSessionSave(agentId, title.trim() || null, currentThread);
    await renderSavedChats();
    const saved = res.session || {};
    activeSessionId = saved.id || null;
    showToast(`Saved "${saved.title || saved.id}" (${saved.entry_count || 0} messages)`);
  } catch (e) {
    alert('Failed to save the session: ' + e.message);
  }
}

function showSession(record) {
  log.innerHTML = '';
  const entries = record.entries || [];
  currentThread = entries.map((entry) => ({ ...entry }));
  activeSessionId = record.id || null;
  if (!entries.length) {
    appendLine('system', 'This saved session has no messages.');
    return;
  }
  for (const entry of entries) {
    const ts = entry.ts ? new Date(entry.ts).toLocaleTimeString() : '';
    const who = entry.agent ? agentLabel(entry.agent) : null;
    appendLine(entry.sender === 'user' ? 'user' : 'system', entry.message, ts, who);
  }
  setStatus(`Loaded saved session: ${record.title || record.id}`);
}

async function openSavedSession(sessionId, agentId) {
  try {
    const record = await API.chatSession(sessionId, agentId);
    showSession(record);
    showToast(`Loaded "${record.title || sessionId}"`);
  } catch (e) {
    alert('Failed to open the session: ' + e.message);
  }
}

async function copySavedSession(sessionId, agentId) {
  try {
    const record = await API.chatSession(sessionId, agentId);
    copyText(sessionText(record), 'Session copied to clipboard');
  } catch (e) {
    alert('Failed to copy the session: ' + e.message);
  }
}

async function deleteSavedSession(session, agentId) {
  const label = session.title || session.id;
  const deletingActive = activeSessionId === session.id;
  const warning = deletingActive
    ? ' The open in-memory conversation will also be cleared.'
    : '';
  if (!confirm(`Delete the only saved text file for "${label}"?${warning}`)) return;
  try {
    await API.chatSessionDelete(session.id, agentId);
    if (deletingActive) {
      currentThread = [];
      activeSessionId = null;
      showEmptyChat();
    }
    await renderSavedChats();
    showToast('Saved session deleted');
  } catch (e) {
    alert('Failed to delete the session: ' + e.message);
  }
}

async function loadSkills(selectedPath = '') {
  if (!skillSelect) return;
  try {
    const data = await API.project(null, ['workspace']);
    const workspace = (data.filesystem || []).find((root) => root.name === 'workspace');
    const skillsFolder = (workspace?.children || []).find((node) => node.name === 'skills');
    const files = (skillsFolder?.children || [])
      .filter((node) => node.type !== 'directory' && /\.md$/i.test(node.name))
      .sort((a, b) => a.name.localeCompare(b.name));

    skillSelect.replaceChildren(new Option('Select a skill', ''));
    for (const file of files) {
      skillSelect.add(new Option(file.name.replace(/\.md$/i, ''), file.path));
    }
    if (selectedPath) skillSelect.value = selectedPath;
    if (!files.length) {
      selectedSkill = null;
      skillSelect.value = '';
    }
  } catch (error) {
    skillSelect.replaceChildren(new Option('Could not load skills', ''));
    setStatus('Failed to load skills: ' + error.message);
  }
}

if (skillSelect) {
  skillSelect.addEventListener('change', async () => {
    const path = skillSelect.value;
    selectedSkill = null;
    if (!path) return;
    try {
      const skill = await API.fileRead(path);
      const name = skillSelect.selectedOptions[0].textContent;
      skillNameInput.value = name;
      skillContentInput.value = skill.content || '';
      selectedSkill = { name, content: skill.content || '' };
      showToast(`Skill "${name}" will be sent with your next message`);
    } catch (error) {
      setStatus('Failed to open skill: ' + error.message);
    }
  });
}

document.getElementById('newSkill')?.addEventListener('click', () => {
  skillSelect.value = '';
  skillNameInput.value = '';
  skillContentInput.value = '';
  selectedSkill = null;
  skillNameInput.focus();
});

saveSkillButton?.addEventListener('click', async () => {
  const enteredName = skillNameInput.value.trim().replace(/\.md$/i, '');
  const content = skillContentInput.value.trim();
  const fileName = enteredName.replace(/[^A-Za-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '');
  if (!fileName) {
    showToast('Enter a skill name using letters, numbers, dashes, or underscores');
    skillNameInput.focus();
    return;
  }
  if (!content) {
    showToast('Enter the skill instructions first');
    skillContentInput.focus();
    return;
  }

  const path = `workspace/skills/${fileName}.md`;
  const alreadyExists = Array.from(skillSelect.options).some((option) => option.value === path);
  if (alreadyExists && !confirm(`Replace the saved skill "${fileName}"?`)) return;

  saveSkillButton.disabled = true;
  try {
    if (alreadyExists) {
      await API.fileWrite(path, content + '\n');
    } else {
      await API.fileCreate(path, content + '\n');
    }
    await loadSkills(path);
    selectedSkill = { name: fileName, content };
    showToast(`Saved skill "${fileName}"`);
  } catch (error) {
    setStatus('Failed to save skill: ' + error.message);
    alert('Failed to save skill: ' + error.message);
  } finally {
    saveSkillButton.disabled = false;
  }
});

window.scaffoldNewAgent = scaffoldNewAgent;
window.wipeChat = wipeChat;
window.saveCurrentChat = saveCurrentChat;
