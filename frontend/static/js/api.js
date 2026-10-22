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
  async saveMarkdown(content, filename) {
    if (typeof window.showSaveFilePicker === 'function') {
      const handle = await window.showSaveFilePicker({
        suggestedName: filename,
        types: [{
          description: 'Markdown file',
          accept: { 'text/markdown': ['.md'] }
        }]
      });
      const writable = await handle.createWritable();
      await writable.write(new Blob([content], { type: 'text/markdown;charset=utf-8' }));
      await writable.close();
      return { filename, locationChosen: true };
    }

    const objectUrl = URL.createObjectURL(
      new Blob([content], { type: 'text/markdown;charset=utf-8' })
    );
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    return { filename, locationChosen: false };
  },

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
  async getAgents(environment = 'workspace') {
    return get(`/api/agents?environment=${encodeURIComponent(environment)}`);
  },

  async createAgent(agentId, name, description, mode = 'chat', squad = '', environment = 'workspace', environmentName = '') {
    return send('POST', '/api/agents/create', {
      agent_id: agentId, name, description, mode, squad, environment, environment_name: environmentName
    });
  },

  async deleteAgent(agentId, environment = 'workspace') {
    return send('DELETE', `/api/agents/${encodeURIComponent(agentId)}?environment=${encodeURIComponent(environment)}`);
  },

  async getCodeBuilderAgents() {
    return get('/api/codebuilder/agents');
  },

  async sendMessage(message, agentId, model = 'qwen2.5-coder:latest', sessionId = null, environment = 'workspace') {
    return send('POST', '/api/chat', {
      message, agent_id: agentId, model, session_id: sessionId, environment
    });
  },

  async getAgentScratchpad() {
    return get('/api/agent-memory/scratchpad');
  },

  async clearAgentScratchpad() {
    return send('DELETE', '/api/agent-memory/scratchpad');
  },

  async getRagDocuments() {
    return get('/api/rag/documents');
  },

  async addRagText(title, text) {
    return send('POST', '/api/rag/documents', { title, text });
  },

  async deleteRagDocument(path) {
    return send('POST', '/api/rag/documents/delete', { path });
  },

  async getRagConfig() {
    return get('/api/rag/config');
  },

  async setRagConfig(path) {
    return send('PUT', '/api/rag/config', { path });
  },

  async reindexRag() {
    return send('POST', '/api/rag/reindex');
  },

  async clearRagIndex() {
    return send('DELETE', '/api/rag/index');
  },

  async streamMessage(
    message,
    agentId,
    model = 'qwen2.5-coder:latest',
    sessionId = null,
    environment = 'workspace',
    onEvent = () => {},
    signal
  ) {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message, agent_id: agentId, model, session_id: sessionId, environment
      }),
      signal
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      const detail = payload.detail || payload.message || response.statusText;
      throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
    if (!response.body) throw new Error('The chat stream returned no response body.');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let completed = null;
    const consume = async frame => {
      const data = frame.split(/\r?\n/)
        .filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trimStart())
        .join('\n');
      if (!data) return;
      const event = JSON.parse(data);
      await onEvent(event);
      if (event.type === 'error') throw new Error(event.detail || 'The agent request failed.');
      if (event.type === 'done') completed = event;
    };

    try {
      for (;;) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });
        const frames = buffer.split(/\r?\n\r?\n/);
        buffer = frames.pop() || '';
        for (const frame of frames) await consume(frame);
        if (done) break;
      }
      if (buffer.trim()) await consume(buffer);
    } finally {
      reader.releaseLock();
    }
    if (!completed) throw new Error('The agent stream ended before returning a completed response.');
    return completed;
  },

  async mapFolderPage(path, maxDepth, includeFiles, offset) {
    return send('POST', '/api/tools/map-page', {
      path, max_depth: maxDepth, include_files: includeFiles, offset
    });
  },

  async resetChat(sessionId) {
    return send('POST', `/api/chat/reset?session_id=${encodeURIComponent(sessionId)}`);
  },

  async getPendingQuestions() {
    return get('/api/chat/pending-questions');
  },

  async submitAnswers(requestId, answers) {
    return send('POST', '/api/chat/submit-answers', { request_id: requestId, answers });
  },

  async exportSession(sessionId) {
    const safeSessionId = String(sessionId).replace(/[^A-Za-z0-9_.-]/g, '_');
    const suggestedName = `novous_${safeSessionId}_${new Date().toISOString().replace(/[:.]/g, '-')}.md`;
    let pickerResult = null;
    if (typeof window.showSaveFilePicker === 'function') {
      pickerResult = window.showSaveFilePicker({
        suggestedName,
        types: [{
          description: 'Markdown file',
          accept: { 'text/markdown': ['.md'] }
        }]
      }).then(handle => ({ handle }), error => ({ error }));
    }

    const res = await fetch('/api/chat/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });
    if (!res.ok) await jsonOrThrow(res);
    const blob = await res.blob();
    const disposition = res.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
    const filename = filenameMatch ? filenameMatch[1] : suggestedName;

    if (pickerResult) {
      const result = await pickerResult;
      if (result.error) throw result.error;
      const writable = await result.handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return { filename, locationChosen: true };
    }

    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    return { filename, locationChosen: false };
  },

  async getTools() {
    return get('/api/tools');
  },

  async getToolLibrary() {
    return get('/api/tools/library');
  },

  async getWorkbenchTool(toolName) {
    return get(`/api/testing/tool-workbench/tools/${encodeURIComponent(toolName)}`);
  },

  async deleteWorkbenchTool(toolName) {
    return send('DELETE', `/api/testing/tool-workbench/tools/${encodeURIComponent(toolName)}`);
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

  async readManagedFile(path) {
    return get(`/api/file-manager/read?path=${encodeURIComponent(path)}`);
  },

  async getManagedFileTree(path = '') {
    return get(`/api/file-manager/tree?path=${encodeURIComponent(path)}`);
  },

  async getFileManagerRoots() {
    return get('/api/file-manager/roots');
  },

  async selectFileManagerRoot(path) {
    return send('POST', '/api/file-manager/roots/select', { path });
  },

  async manageFileManagerRoots(action, paths) {
    return send('POST', '/api/file-manager/roots/manage', { action, paths });
  },

  async writeManagedFile(path, content) {
    return send('POST', '/api/file-manager/write', { path, content });
  },

  async createManagedPath(path, kind = 'file') {
    return send('POST', '/api/file-manager/create', { path, kind });
  },

  async deleteManagedPath(path) {
    return send('POST', '/api/file-manager/delete', { path });
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

  async evaluatePromptComponents(title, description, sections, tools) {
    return send('POST', '/api/prompt-builder/evaluate', {
      title, description, sections, tools
    });
  },

  async judgePrompt(model, title, description, sections, tools) {
    return send('POST', '/api/prompt-builder/judge', { model, title, description, sections, tools });
  },

  async probePrompt(model, title, description, prompt, factQuestion = '', factAnswer = '') {
    return send('POST', '/api/prompt-builder/probe', {
      model, title, description, prompt, fact_question: factQuestion, fact_answer: factAnswer
    });
  },

  async saveTestReport(report) {
    return send('POST', '/api/testing/reports', report);
  },

  async listTestReports() {
    return get('/api/testing/reports');
  },

  async getTestReport(id) {
    return get(`/api/testing/reports/${encodeURIComponent(id)}`);
  },

  async runHeaderTests(agentId, environment = 'workspace') {
    return send('POST', '/api/testing/run_header_tests', { agent_id: agentId, environment });
  },

  async executeToolTest(toolCode, functionInput = {}, timeoutSeconds = 5) {
    return send('POST', '/api/testing/tool-workbench/execute', {
      tool_code: toolCode, function_input: functionInput, timeout_seconds: timeoutSeconds
    });
  },

  async generateToolFunction(model, description) {
    return send('POST', '/api/testing/tool-workbench/generate-function', { model, description });
  },

  async getToolTestHarness(toolCode) {
    return send('POST', '/api/testing/tool-workbench/test-harness', { tool_code: toolCode });
  },

  async testToolWithLlm(model, toolCode, userPrompt, timeoutSeconds = 5) {
    return send('POST', '/api/testing/tool-workbench/test-with-llm', {
      model, tool_code: toolCode, user_prompt: userPrompt, timeout_seconds: timeoutSeconds
    });
  },

  async promoteTestedTool(toolCode, functionInput = {}, timeoutSeconds = 5) {
    return send('POST', '/api/testing/tool-workbench/promote', {
      tool_code: toolCode, function_input: functionInput, timeout_seconds: timeoutSeconds
    });
  },

  async evaluateMarkdown(markdown, agentId = 'draft') {
    return send('POST', '/api/testing/evaluate_markdown', { markdown, agent_id: agentId });
  },

  async publishAgent(agentId, label = '', markdown, environment = 'workspace', tools = []) {
    return send('POST', '/api/testing/publish', {
      agent_id: agentId, label, markdown, environment, tools
    });
  },

  async getTestFixtures() {
    return get('/api/testing/fixtures');
  }
};
