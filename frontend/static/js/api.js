/**
 * Novous Unified API Client Wrapper
 */
async function jsonOrThrow(res) {
  let data = null;
  try { data = await res.json(); } catch (_) { /* empty body */ }
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || res.statusText;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return data;
}

function get(url) { return fetch(url).then(jsonOrThrow); }
function send(method, url, body) {
  return fetch(url, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined
  }).then(jsonOrThrow);
}

export const Api = {
  // --- Workspace & Health ---
  async getHealth() {
    return get('/api/health');
  },

  async getProjectState() {
    return get('/api/project');
  },

  async saveProjectState(patch) {
    return send('POST', '/api/project', patch);
  },

  // --- Agents & Chat (Core Engine) ---
  async getAgents() {
    return get('/api/agents');
  },

  async createAgent(agentId, name, description, mode = 'chat', squad = '') {
    return send('POST', '/api/agents/create', {
      agent_id: agentId, name, description, mode, squad
    });
  },

  async deleteAgent(agentId) {
    return send('DELETE', `/api/agents/${encodeURIComponent(agentId)}`);
  },

  async sendMessage(message, agentId, model = 'qwen2.5-coder:latest', sessionId = null) {
    return send('POST', '/api/chat', {
      message, agent_id: agentId, model, session_id: sessionId
    });
  },

  async resetChat(sessionId) {
    return send('POST', `/api/chat/reset?session_id=${encodeURIComponent(sessionId)}`);
  },

  async getTools() {
    return get('/api/tools');
  },

  async getModels() {
    return get('/api/models');
  },

  // --- Filesystem & Editor ---
  async getFileTree(path = '') {
    return get(`/api/directory/tree?path=${encodeURIComponent(path)}`);
  },

  async readFile(path) {
    return get(`/api/file/read?path=${encodeURIComponent(path)}`);
  },

  async writeFile(path, content) {
    return send('POST', '/api/file/write', { path, content });
  },

  async createPath(path, kind = 'file') {
    return send('POST', '/api/file/create', { path, kind });
  },

  async deletePath(path, kind = 'file') {
    return send('POST', '/api/file/delete', { path, kind });
  },

  async getEditorSessions() {
    return get('/api/editor/sessions');
  },

  // --- Squads ---
  async getSquads() { return get('/api/squads'); },
  async createSquad(name, description = '') {
    return send('POST', '/api/squads/create', { name, description });
  },
  async deleteSquad(name) {
    return send('POST', '/api/squads/delete', { name });
  },

  // --- Testing & Prompt Builder ---
  async getPromptCategories() {
    return get('/api/prompt-builder/categories');
  },

  async addPromptCategory(id, name, description = '', requiredHeader = '') {
    return send('POST', '/api/prompt-builder/categories', {
      id, name, description, required_header: requiredHeader
    });
  },

  async deletePromptCategory(catId) {
    return send('DELETE', `/api/prompt-builder/categories/${encodeURIComponent(catId)}`);
  },

  async getPromptParts(category = null) {
    const q = category ? `?category=${encodeURIComponent(category)}` : '';
    return get(`/api/prompt-builder/parts${q}`);
  },

  async addPromptPart(category, title, content, id = null) {
    return send('POST', '/api/prompt-builder/parts', {
      category, title, content, id
    });
  },

  async deletePromptPart(partId) {
    return send('DELETE', `/api/prompt-builder/parts/${encodeURIComponent(partId)}`);
  },

  async assemblePrompt(parts, extraInstructions = '') {
    return send('POST', '/api/prompt-builder/assemble', {
      parts, extra_instructions: extraInstructions
    });
  },

  async runHeaderTests(agentId) {
    return send('POST', '/api/testing/run_header_tests', { agent_id: agentId });
  },

  async evaluateMarkdown(markdown, agentId = 'draft') {
    return send('POST', '/api/testing/evaluate_markdown', { markdown, agent_id: agentId });
  },

  async publishAgent(agentId, label = '') {
    return send('POST', '/api/testing/publish', { agent_id: agentId, label });
  },

  async getTestFixtures() {
    return get('/api/testing/fixtures');
  }
};
