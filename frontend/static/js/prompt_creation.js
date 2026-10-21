import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

function appendMarkdownInline(parent, text) {
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|~~[^~]+~~|\[([^\]]+)\]\(([^)\s]+)\))/g;
  let lastIndex = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    parent.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
    const token = match[0];
    let element;

    if (token.startsWith('`')) {
      element = document.createElement('code');
      element.textContent = token.slice(1, -1);
    } else if (token.startsWith('**') || token.startsWith('__')) {
      element = document.createElement('strong');
      element.textContent = token.slice(2, -2);
    } else if (token.startsWith('~~')) {
      element = document.createElement('del');
      element.textContent = token.slice(2, -2);
    } else if (token.startsWith('*') || token.startsWith('_')) {
      element = document.createElement('em');
      element.textContent = token.slice(1, -1);
    } else {
      element = document.createElement('a');
      element.textContent = match[2];
      try {
        const url = new URL(match[3], window.location.href);
        if (['http:', 'https:', 'mailto:'].includes(url.protocol)) {
          element.href = url.href;
          element.rel = 'noopener noreferrer';
        } else {
          element = document.createTextNode(match[2]);
        }
      } catch {
        element = document.createTextNode(match[2]);
      }
    }

    parent.appendChild(element);
    lastIndex = pattern.lastIndex;
  }

  parent.appendChild(document.createTextNode(text.slice(lastIndex)));
}

function appendMarkdown(parent, markdown) {
  const lines = String(markdown ?? '').replace(/\r\n?/g, '\n').split('\n');
  let paragraph = [];
  let list = null;
  let codeLines = null;
  const isTableDelimiter = line =>
    /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
  const splitTableRow = line =>
    line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim());

  const flushParagraph = () => {
    if (!paragraph.length) return;
    const block = document.createElement('p');
    paragraph.forEach((line, index) => {
      if (index) block.appendChild(document.createTextNode(' '));
      appendMarkdownInline(block, line);
    });
    parent.appendChild(block);
    paragraph = [];
  };
  const flushList = () => {
    if (list) parent.appendChild(list);
    list = null;
  };

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const fence = line.match(/^\s*```([^`]*)$/);
    if (codeLines) {
      if (fence) {
        const code = document.createElement('code');
        code.textContent = codeLines.join('\n');
        const pre = document.createElement('pre');
        pre.appendChild(code);
        parent.appendChild(pre);
        codeLines = null;
      } else {
        codeLines.push(line);
      }
      continue;
    }
    if (fence) {
      flushParagraph();
      flushList();
      codeLines = [];
      continue;
    }
    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    if (/^\s{0,3}(?:---+|___+|\*\*\*+)\s*$/.test(line)) {
      flushParagraph();
      flushList();
      parent.appendChild(document.createElement('hr'));
      continue;
    }

    if (line.includes('|') && lines[index + 1] && isTableDelimiter(lines[index + 1])) {
      flushParagraph();
      flushList();
      const headers = splitTableRow(line);
      const table = document.createElement('table');
      table.className = 'prompt-markdown-table';
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');
      headers.forEach(text => {
        const cell = document.createElement('th');
        cell.scope = 'col';
        appendMarkdownInline(cell, text);
        headerRow.appendChild(cell);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      for (index += 2; index < lines.length && lines[index].includes('|'); index += 1) {
        const row = document.createElement('tr');
        splitTableRow(lines[index]).forEach((text, cellIndex) => {
          const cell = document.createElement('td');
          if (headers[cellIndex]) appendMarkdownInline(cell, text);
          row.appendChild(cell);
        });
        tbody.appendChild(row);
      }
      table.appendChild(tbody);
      parent.appendChild(table);
      index -= 1;
      continue;
    }

    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (heading) {
      flushParagraph();
      flushList();
      const element = document.createElement(`h${heading[1].length}`);
      appendMarkdownInline(element, heading[2]);
      parent.appendChild(element);
      continue;
    }

    const item = line.match(/^\s{0,3}([-*+]|\d+[.)])\s+(.+)$/);
    if (item) {
      flushParagraph();
      const ordered = /^\d/.test(item[1]);
      if (!list || (list.tagName === 'OL') !== ordered) {
        flushList();
        list = document.createElement(ordered ? 'ol' : 'ul');
      }
      const element = document.createElement('li');
      const task = item[2].match(/^\[([ xX])\]\s+(.+)$/);
      if (task) {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = task[1].toLowerCase() === 'x';
        checkbox.disabled = true;
        checkbox.setAttribute('aria-label', checkbox.checked ? 'Completed task' : 'Incomplete task');
        element.classList.add('prompt-markdown-task');
        element.append(checkbox, document.createTextNode(' '));
        appendMarkdownInline(element, task[2]);
      } else {
        appendMarkdownInline(element, item[2]);
      }
      list.appendChild(element);
      continue;
    }

    flushList();
    const quote = line.match(/^\s{0,3}>\s?(.*)$/);
    if (quote) {
      flushParagraph();
      const blockquote = document.createElement('blockquote');
      appendMarkdownInline(blockquote, quote[1]);
      parent.appendChild(blockquote);
      continue;
    }

    paragraph.push(line.trim());
  }

  if (codeLines) {
    const code = document.createElement('code');
    code.textContent = codeLines.join('\n');
    const pre = document.createElement('pre');
    pre.appendChild(code);
    parent.appendChild(pre);
  }
  flushParagraph();
  flushList();
}

export function renderPromptCreationView(container) {
  container.innerHTML = `
    <div class="prompt-creation-flow">
      <section class="card prompt-chat-card" aria-labelledby="pc-chat-title">
        <div class="codebuilder-chat-heading">
          <h2 id="pc-chat-title">Prompt Coach Chat</h2>
          <span id="pc-chat-status" class="text-muted small">Loading agents…</span>
          <span class="prompt-chat-font-controls" role="group" aria-label="Chat text size">
            <button type="button" class="btn btn-sm" id="pc-font-smaller" title="Smaller text" aria-label="Decrease chat text size">A−</button>
            <button type="button" class="btn btn-sm" id="pc-font-larger" title="Larger text" aria-label="Increase chat text size">A+</button>
          </span>
        </div>
        <p class="text-muted small prompt-chat-note">
          Chat with an available agent to clarify and shape your prompt. Responses use cleaner Markdown formatting when possible.
        </p>
        <div id="pc-chat-messages" class="codebuilder-chat-messages" aria-live="polite">
          <div class="codebuilder-chat-message system">Describe the prompt you want to create, and we’ll work through it together.</div>
        </div>
        <form id="pc-chat-form" class="codebuilder-chat-form">
          <label class="codebuilder-model-picker">
            <span class="text-muted small">Agent</span>
            <select id="pc-chat-agent" class="form-select" aria-label="Choose prompt coach agent">
              <option value="">Loading agents…</option>
            </select>
            <span class="text-muted small">Model</span>
            <select id="pc-chat-model" class="form-select" aria-label="Choose model">
              <option value="">Loading models…</option>
            </select>
          </label>
          <textarea id="pc-chat-input" class="form-input" rows="3"
                    placeholder="What should this prompt help its agent do?"
                    aria-label="Message to prompt coach"></textarea>
          <div class="codebuilder-chat-actions">
            <button id="pc-chat-clear" class="btn btn-sm" type="button">Clear</button>
            <button class="btn btn-primary" type="submit" disabled>Send</button>
          </div>
        </form>
      </section>

      <div class="prompt-chat-resizer" role="separator" aria-label="Resize chat panel"
           aria-orientation="vertical" aria-valuemin="280" aria-valuemax="2000"
           aria-valuenow="320" tabindex="0"></div>

      <section class="card prompt-assembly-card" aria-labelledby="tb-assembly-title">
        <div class="card-head">
          <h3 id="tb-assembly-title">Prompt Creation & Assembly</h3>
          <div class="toolbar-row" style="margin:0;">
            <button type="button" class="btn btn-sm" id="tb-toggle-cat-form">+ Category</button>
            <button type="button" class="btn btn-sm" id="tb-toggle-part-form">+ Part</button>
            <button type="button" class="btn btn-sm btn-primary" id="tb-assemble">Assemble</button>
          </div>
        </div>

        <div id="tb-cat-form" class="card bg-elev hidden" style="margin-bottom: 0.75rem; padding: 0.75rem;">
          <h4 style="margin-bottom: 0.5rem;">Add New Category</h4>
          <div class="form-row">
            <input type="text" id="cat-id-input" class="form-input" placeholder="Category ID / Slug (e.g. constraints)" required>
            <input type="text" id="cat-name-input" class="form-input" placeholder="Category Name (e.g. Constraints)" required>
          </div>
          <div class="form-row">
            <input type="text" id="cat-desc-input" class="form-input" placeholder="Description (optional)">
            <input type="text" id="cat-header-input" class="form-input" placeholder="Required Header (e.g. constraints)">
          </div>
          <div class="toolbar-row">
            <button type="button" class="btn btn-sm btn-primary" id="cat-save-btn">Save Category</button>
            <button type="button" class="btn btn-sm" id="cat-cancel-btn">Cancel</button>
          </div>
        </div>

        <div id="tb-part-form" class="card bg-elev hidden" style="margin-bottom: 0.75rem; padding: 0.75rem;">
          <h4 style="margin-bottom: 0.5rem;">Add New Prompt Part</h4>
          <div class="form-row">
            <select id="part-cat-select" class="form-select"></select>
            <input type="text" id="part-title-input" class="form-input" placeholder="Part Title (e.g. JSON Format)" required>
          </div>
          <div class="form-row">
            <input type="text" id="part-slug-input" class="form-input" placeholder="Slug ID (optional)">
          </div>
          <div class="form-row">
            <textarea id="part-content-input" class="form-input" style="width: 100%; height: 80px;" placeholder="Prompt part markdown content…" required></textarea>
          </div>
          <div class="toolbar-row">
            <button type="button" class="btn btn-sm btn-primary" id="part-save-btn">Save Part</button>
            <button type="button" class="btn btn-sm" id="part-cancel-btn">Cancel</button>
          </div>
        </div>

        <div class="prompt-metadata-fields">
          <label class="prompt-component-field">
            <span>Prompt title</span>
            <input id="tb-title" class="form-input" maxlength="100"
                   placeholder="What is this prompt for?">
          </label>
          <label class="prompt-component-field">
            <span>Prompt description</span>
            <textarea id="tb-description" class="form-input" rows="3" maxlength="1000"
                      placeholder="Describe the outcome this prompt should help an agent achieve, and when it should be used."></textarea>
          </label>
        </div>

        <div id="tb-categories" class="category-grid">
          <p class="text-muted">Loading categories…</p>
        </div>

      </section>

      <section class="card prompt-tools-card" aria-labelledby="tb-tools-title">
        <div class="card-head">
          <h3 id="tb-tools-title">Available Core Engine Tools</h3>
          <button type="button" class="btn btn-sm" id="btn-refresh-tools">Refresh Tools</button>
        </div>
        <p class="text-muted small">Tools retrieved from the five file-tool modules and <code>promoted_tools.py</code> in <code>tools/</code>. Tick a tool to include it in the prompt; use ✎ to edit its description and 🧪 to test it.</p>
        <div id="tools-list-container" class="category-grid" style="overflow-y: auto; max-height: 500px;">
          <p class="text-muted">Loading available tools...</p>
        </div>
      </section>

      <section class="card prompt-result-card" aria-labelledby="tb-preview-title">
        <div class="card-head">
          <div>
            <h3 id="tb-preview-title">Assembled Prompt</h3>
            <p class="text-muted small">Review or edit the completed prompt here before testing it. Re-assembling replaces manual edits.</p>
          </div>
          <span id="tb-stats" class="text-muted small"></span>
        </div>
        <textarea id="tb-preview" class="prompt-preview"
                  placeholder="Assemble selected prompt parts to prepare the prompt for testing…"></textarea>
        <div class="toolbar-row">
          <button type="button" class="btn btn-sm" id="tb-copy">Copy</button>
          <span class="spacer"></span>
          <select id="tb-publish-agent" class="form-select prompt-publish-select">
            <option value="">Select agent…</option>
          </select>
          <button type="button" class="btn btn-sm" id="tb-publish">Save to Agent</button>
          <label class="checkbox-row" title="Run the prompt on the selected chat model and check role understanding, a known fact, and hallucination resistance">
            <input type="checkbox" id="tb-model-test" checked> <span>Model test</span>
          </label>
          <input class="form-input" id="tb-fact-q" aria-label="Fact question" value="What is the capital of France?" style="max-width: 14rem;">
          <input class="form-input" id="tb-fact-a" aria-label="Expected answer" value="Paris" style="max-width: 6rem;">
          <label class="checkbox-row" title="Also have the selected chat model review each section against a rubric">
            <input type="checkbox" id="tb-ai-review"> <span>AI rubric review</span>
          </label>
          <button type="button" class="btn btn-sm btn-primary" id="tb-test-prompt">Test Prompt</button>
        </div>
        <p id="tb-msg" class="small hidden"></p>
        <div id="tb-test-result" class="small hidden" role="status" aria-live="polite"></div>
      </section>

      <section class="card prompt-markdown-draft-card hidden" id="pc-markdown-draft-card"
               aria-labelledby="pc-markdown-draft-title">
        <div class="card-head">
          <div>
            <h3 id="pc-markdown-draft-title">Chat Markdown Draft</h3>
            <p class="text-muted small">Responses added from chat are combined here. Copy the raw Markdown when ready.</p>
          </div>
          <div class="toolbar-row prompt-markdown-draft-actions">
            <button type="button" class="btn btn-sm btn-primary" id="pc-parse-markdown">Parse draft</button>
            <button type="button" class="btn btn-sm" id="pc-copy-markdown">Copy Markdown</button>
            <button type="button" class="btn btn-sm" id="pc-clear-markdown">Clear</button>
          </div>
        </div>
        <div class="prompt-markdown-preview" id="pc-markdown-preview"></div>
        <p class="small text-muted" id="pc-markdown-status" role="status" aria-live="polite"></p>
      </section>
    </div>`;

  const catBox = container.querySelector('#tb-categories');
  const preview = container.querySelector('#tb-preview');
  const stats = container.querySelector('#tb-stats');
  const msg = container.querySelector('#tb-msg');
  const toolsContainer = container.querySelector('#tools-list-container');
  const publishAgentSel = container.querySelector('#tb-publish-agent');
  const titleField = container.querySelector('#tb-title');
  const descriptionField = container.querySelector('#tb-description');
  const chatAgentSel = container.querySelector('#pc-chat-agent');
  const chatModelSel = container.querySelector('#pc-chat-model');
  const chatInput = container.querySelector('#pc-chat-input');
  const chatMessages = container.querySelector('#pc-chat-messages');
  const chatStatus = container.querySelector('#pc-chat-status');
  const chatForm = container.querySelector('#pc-chat-form');
  const testResult = container.querySelector('#tb-test-result');
  const chatResizer = container.querySelector('.prompt-chat-resizer');
  const flow = container.querySelector('.prompt-creation-flow');
  const markdownDraftCard = container.querySelector('#pc-markdown-draft-card');
  const markdownPreview = container.querySelector('#pc-markdown-preview');
  const markdownStatus = container.querySelector('#pc-markdown-status');

  const catForm = container.querySelector('#tb-cat-form');
  const partForm = container.querySelector('#tb-part-form');
  const partCatSelect = container.querySelector('#part-cat-select');

  let manifest = { categories: [] };
  let availableTools = [];
  let promptAgents = [];
  let selectedChatAgent = null;
  let chatPending = false;
  let promptBase = '';
  let promptPartCount = 0;
  let promptRevision = 0;
  let testedPromptRevision = null;
  const promptTools = new Map();
  const chatWidthStorageKey = 'novous2.prompt-creation.chat-width';
  let markdownDraft = '';
  const stateStorageKey = 'novous2.prompt-creation.state';
  let restoredParts = [];

  function saveState() {
    try {
      sessionStorage.setItem(stateStorageKey, JSON.stringify({
        draft: markdownDraft,
        title: titleField.value,
        description: descriptionField.value,
        parts: [...catBox.querySelectorAll('[data-part]:checked')].map(input => input.value),
        tools: [...promptTools.values()]
      }));
    } catch {
      // storage unavailable; state just won't survive a reload
    }
  }

  function restoreState() {
    let saved = null;
    try {
      saved = JSON.parse(sessionStorage.getItem(stateStorageKey) || 'null');
    } catch {
      return;
    }
    if (!saved) return;
    markdownDraft = saved.draft || '';
    titleField.value = saved.title || '';
    descriptionField.value = saved.description || '';
    restoredParts = saved.parts || [];
    for (const tool of saved.tools || []) promptTools.set(tool.name, tool);
    if (markdownDraft) {
      markdownDraftCard.classList.remove('hidden');
      appendMarkdown(markdownPreview, markdownDraft);
    }
  }
  function showMsg(text, isError = false) {
    msg.textContent = text;
    msg.className = `small ${isError ? 'text-danger' : 'text-success'}`;
  }

  function markPromptChanged() {
    saveState();
    promptRevision += 1;
    if (testedPromptRevision !== null) {
      testedPromptRevision = null;
      testResult.className = 'small text-warning';
      testResult.textContent = 'Prompt changed since the last test. Run Test Prompt again for an up-to-date report.';
    }
  }

  function toolDescription(tool) {
    return tool.promptDescription ?? (
      Array.isArray(tool.description) ? tool.description.join(' ') : tool.description || ''
    );
  }

  function findPromptPart(partId) {
    for (const category of manifest.categories || []) {
      const part = (category.parts || []).find(item => item.id === partId);
      if (part) return { ...part, category: category.id };
    }
    return (manifest.uncategorized_parts || []).find(item => item.id === partId) || null;
  }

  function selectedPromptSections() {
    return [...catBox.querySelectorAll('[data-part]:checked')].map(input => {
      const part = findPromptPart(input.value);
      if (!part) return null;
      return {
        id: part.id,
        title: part.title,
        category: part.category,
        content: part.content
      };
    }).filter(Boolean);
  }


  async function loadCoreTools() {
    try {
      toolsContainer.innerHTML = '<p class="text-muted">Fetching file tools...</p>';
      const res = await Api.getToolLibrary();
      availableTools = res.tools || [];

      if (!availableTools.length) {
        toolsContainer.innerHTML = '<p class="text-muted">No file tools are currently registered.</p>';
        return;
      }

      const providers = [...new Set(availableTools.map(t => t.provider || 'tools'))];
      toolsContainer.innerHTML = providers.map(provider => `
        <div class="category-block">
          <div class="category-head">
            <strong>${esc(provider)}</strong>
          </div>
          ${availableTools.map((t, index) => ({ t, index })).filter(({ t }) => (t.provider || 'tools') === provider).map(({ t, index }) => `
            <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
              <label class="checkbox-row" style="flex: 1; margin: 0;" title="${esc(t.signature)}">
                <input type="checkbox" value="${index}" data-tool ${promptTools.has(t.name) ? 'checked' : ''}>
                <span>${esc(t.name)}</span>
              </label>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Edit tool description" data-edit-tool="${index}" style="padding: 0 0.3rem;">✎</button>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Test tool description" data-test-tool="${index}" style="padding: 0 0.3rem;">🧪</button>
            </div>`).join('')}
        </div>
      `).join('');
    } catch (err) {
      toolsContainer.innerHTML = `<p class="text-danger">Failed to retrieve tools: ${esc(err.message)}</p>`;
    }
  }

  function updatePromptPreview() {
    const toolSection = [...promptTools.values()].map(tool => {
      const description = toolDescription(tool);
      return [
        `### ${tool.name}`,
        `- Provider: ${tool.provider}`,
        `- Signature: ${tool.signature}`,
        description ? description : ''
      ].filter(Boolean).join('\n');
    }).join('\n\n');

    const title = titleField.value.trim();
    const description = descriptionField.value.trim();
    const sectionText = selectedPromptSections().map(section =>
      `## ${section.title}\n\n${section.content.trim()}`
    ).join('\n\n');
    const heading = [title ? `# ${title}` : '', description].filter(Boolean).join('\n\n');
    promptBase = [heading, sectionText].filter(Boolean).join('\n\n');
    promptPartCount = selectedPromptSections().length;
    preview.value = [promptBase, toolSection ? `## Available Tools\n\n${toolSection}` : '']
      .filter(Boolean)
      .join('\n\n');
    stats.textContent = `${promptPartCount} sections · ${promptTools.size} tools · ${preview.value.length} chars`;
  }

  preview.addEventListener('input', () => {
    stats.textContent = `${promptPartCount} sections · ${promptTools.size} tools · ${preview.value.length} chars · edited`;
  });

  async function loadPromptAgents() {
    try {
      const [workspaceData, codeBuilderData, promptData] = await Promise.all([
        Api.getAgents(),
        Api.getCodeBuilderAgents(),
        Api.getAgents('prompt-creation')
      ]);
      const label = environment => ({ codebuilder: 'CodeBuilder', 'prompt-creation': 'Prompt Creation' })[environment] || 'Workspace';
      const agents = [
        ...(workspaceData.agents || []).map(agent => ({ ...agent, environment: 'workspace' })),
        ...(codeBuilderData.agents || []).map(agent => ({ ...agent, environment: 'codebuilder' })),
        ...(promptData.agents || []).map(agent => ({ ...agent, environment: 'prompt-creation' }))
      ];
      promptAgents = agents;
      publishAgentSel.innerHTML = agents.length
        ? `<option value="">Select agent…</option>${agents.map(a => `<option value="${esc(a.environment)}:${esc(a.id)}">${esc(a.name)} (${esc(a.id)}) — ${label(a.environment)}</option>`).join('')}`
        : '<option value="">No agents found</option>';
      chatAgentSel.innerHTML = agents.length
        ? agents.map(a => `<option value="${esc(a.environment)}:${esc(a.id)}">${esc(a.name)} — ${label(a.environment)}</option>`).join('')
        : '<option value="">No agents available</option>';
      let lastAgent = null;
      try { lastAgent = localStorage.getItem('novous2.prompt-creation.lastChatAgent'); } catch { /* storage unavailable */ }
      selectedChatAgent = agents.find(agent => `${agent.environment}:${agent.id}` === lastAgent)
        || agents.find(agent => agent.environment === 'workspace') || agents[0] || null;
      if (selectedChatAgent) {
        chatAgentSel.value = `${selectedChatAgent.environment}:${selectedChatAgent.id}`;
        chatStatus.textContent = `Agent: ${selectedChatAgent.name}`;
      } else {
        chatStatus.textContent = 'No agents available.';
      }
      await loadPromptChatModels();
      updateChatControls();
    } catch (err) {
      publishAgentSel.innerHTML = `<option value="">${esc(err.message)}</option>`;
      chatAgentSel.innerHTML = `<option value="">${esc(err.message)}</option>`;
      chatStatus.textContent = 'Could not load agents.';
    }
  }

  function updateChatControls() {
    const sendButton = chatForm.querySelector('button[type="submit"]');
    sendButton.disabled = chatPending || !selectedChatAgent || !chatModelSel.value || chatModelSel.disabled;
    chatInput.disabled = chatPending;
    chatAgentSel.disabled = chatPending || !promptAgents.length;
  }

  function appendChatMessage(role, content) {
    const message = document.createElement('div');
    message.className = `codebuilder-chat-message ${role}`;
    if (role === 'assistant') {
      appendMarkdown(message, content);
      const addButton = document.createElement('button');
      addButton.type = 'button';
      addButton.className = 'btn btn-sm prompt-add-markdown';
      addButton.textContent = 'Add to draft';
      addButton.setAttribute('aria-label', 'Add this response to the Markdown draft');
      addButton.addEventListener('click', () => {
        const responseMarkdown = String(content ?? '').trim();
        if (!responseMarkdown) return;
        markdownDraft = markdownDraft
          ? `${markdownDraft.trimEnd()}\n\n---\n\n${responseMarkdown}`
          : responseMarkdown;
                markdownDraftCard.classList.remove('hidden');
                markdownPreview.replaceChildren();
                appendMarkdown(markdownPreview, markdownDraft);
        markdownStatus.textContent = 'Response added to the Markdown draft.';
        saveState();
        addButton.disabled = true;
        addButton.textContent = 'Added to draft';
        markdownDraftCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
      message.appendChild(addButton);
    } else {
      message.textContent = content;
    }
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function setChatWidth(width) {
    const availableWidth = flow.clientWidth;
    const maxWidth = Math.max(280, availableWidth - 200);
    const nextWidth = Math.round(Math.min(maxWidth, Math.max(280, width)));
    flow.style.setProperty('--prompt-chat-width', `${nextWidth}px`);
    chatResizer.setAttribute('aria-valuemax', String(maxWidth));
    chatResizer.setAttribute('aria-valuenow', String(nextWidth));
    try {
      localStorage.setItem(chatWidthStorageKey, String(nextWidth));
    } catch (error) {
      console.warn('Could not save Prompt Creation chat width.', error);
    }
  }

  let savedChatWidth = 320;
  try {
    const storedWidth = Number(localStorage.getItem(chatWidthStorageKey));
    if (Number.isFinite(storedWidth) && storedWidth >= 280) savedChatWidth = storedWidth;
  } catch (error) {
    console.warn('Could not load saved Prompt Creation chat width.', error);
  }
  setChatWidth(savedChatWidth);

  const chatFontKey = 'novous2.prompt-creation.chat-font-size';
  let chatFontSize = 14;
  try {
    const storedSize = Number(localStorage.getItem(chatFontKey));
    if (Number.isFinite(storedSize) && storedSize >= 11 && storedSize <= 32) chatFontSize = storedSize;
  } catch (error) {
    console.warn('Could not load saved chat text size.', error);
  }
  function setChatFontSize(size) {
    chatFontSize = Math.min(32, Math.max(11, size));
    flow.style.setProperty('--prompt-chat-font-size', `${chatFontSize}px`);
    try {
      localStorage.setItem(chatFontKey, String(chatFontSize));
    } catch (error) {
      console.warn('Could not save chat text size.', error);
    }
  }
  setChatFontSize(chatFontSize);
  container.querySelector('#pc-font-smaller').addEventListener('click', () => setChatFontSize(chatFontSize - 1));
  container.querySelector('#pc-font-larger').addEventListener('click', () => setChatFontSize(chatFontSize + 2));

  chatResizer.addEventListener('pointerdown', event => {
    if (window.matchMedia('(max-width: 1100px)').matches) return;
    event.preventDefault();
    chatResizer.setPointerCapture(event.pointerId);
    const onMove = moveEvent => {
      const bounds = flow.getBoundingClientRect();
      setChatWidth(moveEvent.clientX - bounds.left);
    };
    const onUp = () => {
      chatResizer.removeEventListener('pointermove', onMove);
      chatResizer.removeEventListener('pointerup', onUp);
      chatResizer.removeEventListener('pointercancel', onUp);
    };
    chatResizer.addEventListener('pointermove', onMove);
    chatResizer.addEventListener('pointerup', onUp);
    chatResizer.addEventListener('pointercancel', onUp);
  });
  chatResizer.addEventListener('keydown', event => {
    const currentWidth = Number.parseInt(
      getComputedStyle(flow).getPropertyValue('--prompt-chat-width'),
      10
    ) || 320;
    let nextWidth;
    if (event.key === 'ArrowLeft') nextWidth = currentWidth - 20;
    else if (event.key === 'ArrowRight') nextWidth = currentWidth + 20;
    else if (event.key === 'Home') nextWidth = 280;
    else if (event.key === 'End') nextWidth = flow.clientWidth;
    else return;
    event.preventDefault();
    setChatWidth(nextWidth);
  });

  container.querySelector('#pc-copy-markdown').addEventListener('click', async () => {
    if (!markdownDraft) return;
    try {
      await navigator.clipboard.writeText(markdownDraft);
      markdownStatus.textContent = 'Markdown copied to clipboard.';
    } catch (error) {
      let copied = false;
      const copyArea = document.createElement('textarea');
      try {
        copyArea.value = markdownDraft;
        copyArea.setAttribute('readonly', '');
        copyArea.style.position = 'fixed';
        copyArea.style.opacity = '0';
        document.body.appendChild(copyArea);
        copyArea.select();
        copied = document.execCommand('copy');
      } catch {
        copied = false;
      } finally {
        copyArea.remove();
      }
      if (!copied) {
        markdownStatus.textContent = `Could not copy Markdown: ${error.message}`;
        return;
      }
      markdownStatus.textContent = 'Markdown copied to clipboard.';
    }
  });

  const slugify = text => String(text).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  function cleanHeading(raw) {
    const text = String(raw).trim().replace(/[*_`]/g, '').trim();
    const cleaned = text
      .replace(/^sections?\s*\d*\s*[:.\-–—]\s*/i, '')
      .replace(/\s*[:\-–—]\s*sections?\s*$/i, '')
      .replace(/\s+section\s*$/i, '')
      .trim();
    return cleaned || text;
  }

  function parseDraft(markdown) {
    const lines = String(markdown).replace(/\r\n?/g, '\n').split('\n');
    let inCode = false;
    const items = lines.map(line => {
      if (/^\s*```/.test(line)) inCode = !inCode;
      const match = !inCode && line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
      return { line, level: match ? match[1].length : 0, text: match ? cleanHeading(match[2]) : '', inCode };
    });
    const titleIndex = items.findIndex(item => item.level === 1);
    const others = items.filter((item, index) => item.level && index !== titleIndex);
    const sectionLevel = others.some(item => item.level === 2)
      ? 2
      : (others.length ? Math.min(...others.map(item => item.level)) : 2);
    const intro = [];
    const sections = [];
    let current = null;
    items.forEach((item, index) => {
      if (index === titleIndex) return;
      if (item.level === sectionLevel) {
        current = { title: item.text, body: [] };
        sections.push(current);
      } else if (!item.inCode && /^\s*---+\s*$/.test(item.line)) {
        // separators between chat responses are not content
      } else if (current) {
        current.body.push(item.line);
      } else if (index > titleIndex) {
        intro.push(item.line);
      }
    });
    const byTitle = new Map();
    for (const section of sections) {
      const labelPattern = new RegExp(
        `^\\s*[*_\`]*${section.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[*_\`]*\\s*[:.\\-–—][*_\`]*[ \\t]*`, 'i');
      const content = section.body.join('\n').trim().replace(labelPattern, '').trim();
      if (content) byTitle.set(section.title.toLowerCase(), { title: section.title, content });
    }
    return {
      title: titleIndex >= 0 ? items[titleIndex].text : '',
      description: intro.join('\n').trim(),
      sections: [...byTitle.values()]
    };
  }

  container.querySelector('#pc-parse-markdown').addEventListener('click', async () => {
    if (!markdownDraft) return;
    const button = container.querySelector('#pc-parse-markdown');
    const parsed = parseDraft(markdownDraft);
    if (!parsed.sections.length) {
      markdownStatus.textContent = 'No "## Section" headings with content were found in the draft.';
      return;
    }
    button.disabled = true;
    markdownStatus.textContent = 'Parsing draft into category and parts…';
    try {
      if (parsed.title) titleField.value = parsed.title;
      if (parsed.description) descriptionField.value = parsed.description.slice(0, 1000);
      const categoryName = parsed.title || 'Parsed Prompt';
      const categoryId = slugify(categoryName) || 'parsed-prompt';
      try {
        await Api.addPromptCategory(categoryId, categoryName, parsed.description.slice(0, 300), '');
      } catch {
        // category already exists from an earlier parse
      }
      const used = new Set();
      const ids = [];
      for (const section of parsed.sections) {
        let slug = slugify(section.title) || 'section';
        for (let n = 2; used.has(slug); n += 1) slug = `${slugify(section.title) || 'section'}-${n}`;
        used.add(slug);
        const part = await Api.addPromptPart(categoryId, section.title, section.content, slug);
        ids.push(part.id);
      }
      await loadManifest();
      catBox.querySelectorAll('[data-part]').forEach(input => {
        input.checked = ids.includes(input.value);
      });
      markPromptChanged();
      updatePromptPreview();
      markdownStatus.textContent = `Parsed ${ids.length} sections into category "${categoryName}". The assembled prompt below is updated.`;
      preview.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      markdownStatus.textContent = `Parse failed: ${err.message}`;
    } finally {
      button.disabled = false;
    }
  });

  container.querySelector('#pc-clear-markdown').addEventListener('click', () => {
    markdownDraft = '';
    markdownPreview.replaceChildren();
    markdownDraftCard.classList.add('hidden');
    markdownStatus.textContent = '';
    saveState();
    for (const button of chatMessages.querySelectorAll('.prompt-add-markdown')) {
      button.disabled = false;
      button.textContent = 'Add to draft';
    }
  });

  async function loadPromptChatModels() {
    chatModelSel.disabled = true;
    chatModelSel.innerHTML = '<option value="">Loading models…</option>';
    try {
      const data = await Api.getModels();
      const models = (data.models || []).slice().sort();
      if (!models.length) {
        chatModelSel.innerHTML = '<option value="">No installed models</option>';
        chatStatus.textContent = data.error || 'No installed models detected.';
        updateChatControls();
        return;
      }
      chatModelSel.innerHTML = models.map(model =>
        `<option value="${esc(model)}">${esc(model)}</option>`
      ).join('');
      const preferred = selectedChatAgent?.model || data.default;
      chatModelSel.value = models.includes(preferred) ? preferred : models[0];
      chatModelSel.disabled = false;
      updateChatControls();
    } catch (err) {
      chatModelSel.innerHTML = `<option value="">${esc(err.message)}</option>`;
      chatStatus.textContent = 'Could not load models.';
      updateChatControls();
    }
  }

  async function loadManifest() {
    try {
      const data = await Api.getPromptCategories();
      const checked = new Set([...selectedParts(), ...restoredParts]);
      restoredParts = [];
      manifest = data;
      renderCategories(manifest);
      catBox.querySelectorAll('[data-part]').forEach(input => {
        input.checked = checked.has(input.value);
      });
      populateCategoryDropdown(manifest.categories || []);
      updatePromptPreview();
    } catch (err) {
      catBox.innerHTML = `<p class="text-danger">${esc(err.message)}</p>`;
    }
  }

  function populateCategoryDropdown(categories) {
    partCatSelect.innerHTML = categories.length
      ? categories.map(c => `<option value="${esc(c.id)}">${esc(c.name)} (${esc(c.id)})</option>`).join('')
      : '<option value="">No categories available</option>';
  }

  function renderCategories(data) {
    const cats = data.categories || [];
    const uncategorized = data.uncategorized_parts || [];

    let html = cats.map(cat => `
      <div class="category-block">
        <div class="category-head">
          <div style="display: flex; align-items: center; gap: 0.3rem; flex-wrap: wrap;">
            <strong>${esc(cat.name)}</strong>
            ${cat.required_header ? `<span class="badge badge-accent">## ${esc(cat.required_header)}</span>` : ''}
          </div>
          <span style="display: inline-flex; align-items: center;">
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Test category in the Prompt Header Evaluation Battery" data-test-cat="${esc(cat.id)}" style="padding: 0 0.3rem;">🧪</button>
            <button type="button" class="btn btn-ghost btn-sm text-danger" title="Delete category '${esc(cat.name)}'" data-del-cat="${esc(cat.id)}" style="padding: 0 0.3rem;">✕</button>
          </span>
        </div>
        <p class="text-muted small">${esc(cat.description || '')}</p>
        ${(cat.parts || []).map(p => `
          <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
            <label class="checkbox-row" style="flex: 1; margin: 0;">
              <input type="checkbox" value="${esc(p.id)}" data-part>
              <span>${esc(p.title)}</span>
            </label>
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Edit part" data-edit-part="${esc(p.id)}" style="padding: 0 0.3rem;">✎</button>
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Test part" data-test-part="${esc(p.id)}" style="padding: 0 0.3rem;">🧪</button>
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Delete part" data-del-part="${esc(p.id)}" style="padding: 0 0.3rem;">✕</button>
          </div>`).join('') || '<p class="text-muted small">No parts.</p>'}
      </div>`).join('');

    if (uncategorized.length) {
      html += `
        <div class="category-block">
          <div class="category-head">
            <strong>Uncategorized</strong>
          </div>
          <p class="text-muted small">Parts without a matching category definition.</p>
          ${uncategorized.map(p => `
            <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
              <label class="checkbox-row" style="flex: 1; margin: 0;">
                <input type="checkbox" value="${esc(p.id)}" data-part>
                <span>${esc(p.title)}</span>
              </label>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Edit part" data-edit-part="${esc(p.id)}" style="padding: 0 0.3rem;">✎</button>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Test part" data-test-part="${esc(p.id)}" style="padding: 0 0.3rem;">🧪</button>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Delete part" data-del-part="${esc(p.id)}" style="padding: 0 0.3rem;">✕</button>
            </div>`).join('')}
        </div>`;
    }

    catBox.innerHTML = html || '<p class="text-danger">No categories found.</p>';
  }

  restoreState();
  loadCoreTools();
  loadManifest();
  loadPromptAgents();

  chatAgentSel.addEventListener('change', () => {
    const [environment, agentId] = chatAgentSel.value.split(':', 2);
    try { localStorage.setItem('novous2.prompt-creation.lastChatAgent', chatAgentSel.value); } catch { /* storage unavailable */ }
    selectedChatAgent = promptAgents.find(agent =>
      agent.environment === environment && agent.id === agentId
    ) || null;
    chatMessages.replaceChildren();
    if (selectedChatAgent) {
      appendChatMessage('system', `Chatting with ${selectedChatAgent.name}.`);
      chatStatus.textContent = `Agent: ${selectedChatAgent.name}`;
    } else {
      chatStatus.textContent = 'Select an agent to start.';
    }
    loadPromptChatModels();
  });

  chatModelSel.addEventListener('change', updateChatControls);
  titleField.addEventListener('input', () => {
    markPromptChanged();
    updatePromptPreview();
  });
  descriptionField.addEventListener('input', () => {
    markPromptChanged();
    updatePromptPreview();
  });
  catBox.addEventListener('change', event => {
    if (!event.target.matches('[data-part]')) return;
    markPromptChanged();
    updatePromptPreview();
  });
  toolsContainer.addEventListener('change', event => {
    if (!event.target.matches('[data-tool]')) return;
    const tool = availableTools[Number(event.target.value)];
    if (!tool) return;
    if (event.target.checked) {
      if (!promptTools.has(tool.name)) promptTools.set(tool.name, { ...tool });
    } else {
      promptTools.delete(tool.name);
    }
    markPromptChanged();
    updatePromptPreview();
  });

  toolsContainer.addEventListener('click', async event => {
    const editBtn = event.target.closest('[data-edit-tool]');
    const testBtn = event.target.closest('[data-test-tool]');
    const button = editBtn || testBtn;
    if (!button) return;
    const tool = availableTools[Number(button.dataset.editTool ?? button.dataset.testTool)];
    if (!tool) return;
    if (testBtn) {
      testBtn.disabled = true;
      try {
        const source = await Api.getWorkbenchTool(tool.name);
        const params = String(tool.signature || '').replace(/^\(|\)(\s*->.*)?$/g, '').split(',')
          .map(item => item.trim()).filter(Boolean);
        const input = {};
        for (const param of params) {
          const [rawName, ...rest] = param.split(/[:=]/);
          const name = rawName.trim().replace(/^\*+/, '');
          if (!name || name === 'self') continue;
          const type = (param.split(':')[1] || '').split('=')[0].trim();
          input[name] = /int|float/.test(type) ? 0 : /bool/.test(type) ? false : /str/.test(type) || !type ? '' : null;
        }
        const entry = promptTools.get(tool.name) || tool;
        const description = toolDescription(entry).trim();
        const { switchTab } = await import('./app.js');
        switchTab('testing', {
          type: 'tool',
          name: tool.name,
          path: source.path,
          source: source.source,
          input: JSON.stringify(input, null, 2),
          prompt: `Use the ${tool.name} tool to complete this task.${description ? ` ${description}` : ''}`
        });
      } catch (err) {
        showMsg(`Could not open '${tool.name}' in the Tool Function Testing Workbench: ${err.message}`, true);
        testBtn.disabled = false;
      }
      return;
    }
    const panelClass = 'tool-edit-panel';
    const row = button.closest('.part-row');
    const existing = row.nextElementSibling;
    if (existing?.classList.contains(panelClass)) {
      existing.remove();
      return;
    }
    const current = () => promptTools.get(tool.name) || tool;
    const panel = document.createElement('div');
    panel.className = `${panelClass} card bg-elev small`;
    panel.style.cssText = 'padding: 0.5rem; margin: 0.25rem 0;';
    row.after(panel);

    panel.innerHTML = `
      <p class="text-muted small" style="margin: 0 0 0.3rem;"><code>${esc(tool.signature)}</code></p>
      <textarea class="form-input" rows="4" data-tool-desc aria-label="Tool description" style="width: 100%;">${esc(toolDescription(current()))}</textarea>
      <div class="toolbar-row" style="margin-top: 0.4rem;">
        <button type="button" class="btn btn-sm btn-primary" data-tool-save>Save</button>
        <button type="button" class="btn btn-sm" data-tool-cancel>Cancel</button>
      </div>
      <span class="text-muted small">Describe what it does and when the agent should call it. Saved descriptions apply to this prompt.</span>`;
    panel.querySelector('[data-tool-cancel]').addEventListener('click', () => panel.remove());
    panel.querySelector('[data-tool-save]').addEventListener('click', () => {
      const description = panel.querySelector('[data-tool-desc]').value;
      const entry = { ...current(), promptDescription: description };
      promptTools.set(tool.name, entry);
      row.querySelector('[data-tool]').checked = true;
      markPromptChanged();
      updatePromptPreview();
      panel.remove();
      showMsg(`Description for '${tool.name}' saved and tool added to the prompt.`);
    });
  });

  chatForm.addEventListener('submit', async event => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message || chatPending || !selectedChatAgent || !chatModelSel.value) return;

    appendChatMessage('user', message);
    chatInput.value = '';
    chatPending = true;
    chatStatus.textContent = `Waiting for ${selectedChatAgent.name}…`;
    updateChatControls();
    const sessionId = `prompt-creation-${selectedChatAgent.environment}-${selectedChatAgent.id}`;
    try {
      const response = await Api.sendMessage(
        `${message}\n\nWhen you write a prompt, reply with only the prompt as a Markdown document: one "# Title" line, a one-sentence description, then "## " headings named only for what they contain (for example "## Role", never "## Section: Role" or "## Role Section") each followed by plain-text instructions. No preamble or closing commentary.`,
        selectedChatAgent.id,
        chatModelSel.value,
        sessionId,
        selectedChatAgent.environment
      );
      appendChatMessage('assistant', response.reply || 'The agent returned an empty response.');
      chatStatus.textContent = `${selectedChatAgent.name} · ${response.model || chatModelSel.value}`;
    } catch (err) {
      appendChatMessage('system', `Request failed: ${err.message}`);
      chatStatus.textContent = 'Request failed.';
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

  container.querySelector('#pc-chat-clear').addEventListener('click', async () => {
    if (selectedChatAgent) {
      const sessionId = `prompt-creation-${selectedChatAgent.environment}-${selectedChatAgent.id}`;
      try {
        await Api.resetChat(sessionId);
      } catch (err) {
        chatStatus.textContent = `Could not clear chat: ${err.message}`;
        return;
      }
    }
    chatMessages.replaceChildren();
    appendChatMessage('system', selectedChatAgent
      ? `Chat cleared. Continue with ${selectedChatAgent.name}.`
      : 'Chat cleared.');
    chatInput.focus();
  });

  container.querySelector('#btn-refresh-tools').addEventListener('click', loadCoreTools);

  container.querySelector('#tb-toggle-cat-form').addEventListener('click', () => {
    catForm.classList.toggle('hidden');
    partForm.classList.add('hidden');
  });

  container.querySelector('#cat-cancel-btn').addEventListener('click', () => {
    catForm.classList.add('hidden');
  });

  container.querySelector('#tb-toggle-part-form').addEventListener('click', () => {
    partForm.classList.toggle('hidden');
    catForm.classList.add('hidden');
  });

  container.querySelector('#part-cancel-btn').addEventListener('click', () => {
    partForm.classList.add('hidden');
  });

  async function submitCategory() {
    const id = container.querySelector('#cat-id-input').value.trim();
    const name = container.querySelector('#cat-name-input').value.trim();
    const desc = container.querySelector('#cat-desc-input').value.trim();
    const header = container.querySelector('#cat-header-input').value.trim();

    if (!id || !name) return showMsg('Category ID and Name are required.', true);

    try {
      await Api.addPromptCategory(id, name, desc, header);
      catForm.classList.add('hidden');
      container.querySelector('#cat-id-input').value = '';
      container.querySelector('#cat-name-input').value = '';
      container.querySelector('#cat-desc-input').value = '';
      container.querySelector('#cat-header-input').value = '';
      showMsg(`Category '${name}' added successfully.`);
      await loadManifest();
    } catch (err) {
      showMsg(err.message, true);
    }
  }

  container.querySelector('#cat-save-btn').addEventListener('click', submitCategory);

  catForm.querySelectorAll('input').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitCategory();
      }
    });
  });

  async function submitPart() {
    const category = partCatSelect.value;
    const title = container.querySelector('#part-title-input').value.trim();
    const slug = container.querySelector('#part-slug-input').value.trim();
    const content = container.querySelector('#part-content-input').value.trim();

    if (!category || !title || !content) return showMsg('Category, Part Title, and Content are required.', true);

    try {
      await Api.addPromptPart(category, title, content, slug || null);
      partForm.classList.add('hidden');
      container.querySelector('#part-title-input').value = '';
      container.querySelector('#part-slug-input').value = '';
      container.querySelector('#part-content-input').value = '';
      showMsg(`Prompt Part '${title}' added successfully.`);
      await loadManifest();
    } catch (err) {
      showMsg(err.message, true);
    }
  }

  container.querySelector('#part-save-btn').addEventListener('click', submitPart);

  partForm.querySelectorAll('input, textarea').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        submitPart();
      }
    });
  });

  catBox.addEventListener('click', async (e) => {
    const testCatBtn = e.target.closest('[data-test-cat]');
    if (testCatBtn) {
      const cat = (manifest.categories || []).find(item => item.id === testCatBtn.dataset.testCat);
      if (!cat) return;
      if (!(cat.parts || []).length) return showMsg(`Category '${cat.name}' has no parts to test.`, true);
      const markdown = [
        `# ${cat.name}`,
        cat.description || '',
        ...cat.parts.map(part => `## ${part.title}\n\n${part.content.trim()}`)
      ].filter(Boolean).join('\n\n');
      const { switchTab } = await import('./app.js');
      switchTab('testing', {
        type: 'category',
        id: cat.id,
        name: cat.name,
        partCount: cat.parts.length,
        markdown
      });
      return;
    }

    const testBtn = e.target.closest('[data-test-part]');
    if (testBtn) {
      const part = findPromptPart(testBtn.getAttribute('data-test-part'));
      const row = testBtn.closest('.part-row');
      const existing = row.nextElementSibling;
      if (existing?.classList.contains('part-test-panel')) {
        existing.remove();
        return;
      }
      if (!part) return;
      const panel = document.createElement('div');
      panel.className = 'part-test-panel card bg-elev small';
      panel.style.cssText = 'padding: 0.5rem; margin: 0.25rem 0;';
      panel.textContent = 'Testing part…';
      row.after(panel);
      try {
        const result = await Api.evaluatePromptComponents(
          titleField.value,
          descriptionField.value,
          [{ id: part.id, title: part.title, category: part.category, content: part.content }],
          []
        );
        const components = (result.components || []).filter(component =>
          !['Prompt title', 'Prompt description'].includes(component.name)
        );
        panel.replaceChildren();
        const passed = components.every(component => component.passed);
        const summary = document.createElement('strong');
        summary.className = passed ? 'text-success' : 'text-danger';
        summary.textContent = passed ? 'PASS' : 'NOT PASS';
        panel.appendChild(summary);
        for (const component of components) {
          for (const check of component.checks || []) {
            const line = document.createElement('p');
            line.style.margin = '0.2rem 0 0';
            line.textContent = `${check.passed ? '✓' : '✗'} ${checkDetail(check)}`;
            panel.appendChild(line);
          }
        }
      } catch (err) {
        panel.className = 'part-test-panel card bg-elev small text-danger';
        panel.textContent = `Part test failed: ${err.message}`;
      }
      return;
    }

    const editBtn = e.target.closest('[data-edit-part]');
    if (editBtn) {
      const partId = editBtn.getAttribute('data-edit-part');
      const row = editBtn.closest('.part-row');
      const existing = row.nextElementSibling;
      if (existing?.classList.contains('part-edit-panel')) {
        existing.remove();
        return;
      }
      const part = findPromptPart(partId);
      if (!part) return;
      const panel = document.createElement('div');
      panel.className = 'part-edit-panel card bg-elev';
      panel.style.cssText = 'padding: 0.5rem; margin: 0.25rem 0;';
      panel.innerHTML = `
        <input class="form-input" data-edit-title aria-label="Part title" value="${esc(part.title)}">
        <textarea class="form-input" data-edit-content rows="8" aria-label="Part content" style="width: 100%; margin-top: 0.4rem;">${esc(part.content)}</textarea>
        <div class="toolbar-row" style="margin-top: 0.4rem;">
          <button type="button" class="btn btn-sm btn-primary" data-edit-save>Save</button>
          <button type="button" class="btn btn-sm" data-edit-cancel>Cancel</button>
        </div>`;
      row.after(panel);
      panel.querySelector('[data-edit-content]').focus();
      panel.querySelector('[data-edit-cancel]').addEventListener('click', () => panel.remove());
      panel.querySelector('[data-edit-save]').addEventListener('click', async () => {
        const title = panel.querySelector('[data-edit-title]').value.trim();
        const content = panel.querySelector('[data-edit-content]').value.trim();
        if (!title || !content) return showMsg('Part title and content are required.', true);
        try {
          const slug = partId.includes('/') ? partId.split('/').slice(1).join('/') : partId;
          await Api.addPromptPart(part.category, title, content, slug);
          await loadManifest();
          markPromptChanged();
          updatePromptPreview();
          showMsg(`Part '${title}' updated.`);
        } catch (err) {
          showMsg(err.message, true);
        }
      });
      return;
    }

    const delCatBtn = e.target.closest('[data-del-cat]');
    if (delCatBtn) {
      const catId = delCatBtn.getAttribute('data-del-cat');
      if (confirm(`Are you sure you want to delete category '${catId}' and its parts?`)) {
        try {
          await Api.deletePromptCategory(catId);
          showMsg(`Category '${catId}' deleted.`);
          await loadManifest();
        } catch (err) {
          showMsg(err.message, true);
        }
      }
      return;
    }

    const delPartBtn = e.target.closest('[data-del-part]');
    if (delPartBtn) {
      const partId = delPartBtn.getAttribute('data-del-part');
      if (confirm(`Delete prompt part '${partId}'?`)) {
        try {
          await Api.deletePromptPart(partId);
          showMsg(`Prompt part '${partId}' deleted.`);
          await loadManifest();
        } catch (err) {
          showMsg(err.message, true);
        }
      }
    }
  });

  function selectedParts() {
    return [...catBox.querySelectorAll('[data-part]:checked')].map(el => el.value);
  }

  container.querySelector('#tb-assemble').addEventListener('click', async () => {
    const parts = selectedParts();
    if (!parts.length) return showMsg('Select at least one prompt part.', true);
    try {
      await Api.assemblePrompt(parts);
      updatePromptPreview();
      showMsg('Prompt assembled.');
    } catch (err) {
      showMsg(err.message, true);
    }
  });

  container.querySelector('#tb-copy').addEventListener('click', async () => {
    if (!preview.value) return;
    try {
      await navigator.clipboard.writeText(preview.value);
      showMsg('Copied to clipboard.');
    } catch (_) {
      preview.select();
      document.execCommand('copy');
      showMsg('Copied.');
    }
  });

  container.querySelector('#tb-publish').addEventListener('click', async () => {
    const [environment, agentId] = publishAgentSel.value.split(':', 2);
    if (!environment || !agentId) return showMsg('Select an agent to publish first.', true);
    if (!preview.value.trim()) return showMsg('Assemble a prompt before saving it to an agent.', true);
    try {
      const res = await Api.publishAgent(
        agentId, 'snapshot', preview.value, environment, [...promptTools.keys()]
      );
      showMsg(`Saved to ${res.path} and ${res.metadata_path} (headers ${res.header_report.verdict}; snapshot ${res.snapshot}).`);
    } catch (err) {
      showMsg(err.message, true);
    }
  });

  function checkDetail(check) {
    const parts = [check.evidence];
    if (!check.passed) {
      if (check.rule) parts.push(`Rule: ${check.rule}`);
      if (check.observed) parts.push(`Observed: ${check.observed}`);
      if (check.fix) parts.push(`Fix: ${check.fix}`);
    }
    return parts.join(' | ');
  }

  function failureFeedback(result) {
    return (result.components || []).filter(component => !component.passed).map(component => {
      const failedChecks = (component.checks || []).filter(check => !check.passed).map(check => [
        `  - Check "${check.id}": ${check.evidence}`,
        check.rule ? `    Rule: ${check.rule}` : '',
        check.observed ? `    Observed: ${check.observed}` : '',
        check.fix ? `    Suggested fix: ${check.fix}` : ''
      ].filter(Boolean).join('\n')).join('\n');
      const text = component.tested_text ? `\n  Tested text: """${component.tested_text}"""` : '';
      return `- ${component.name}${text}\n${failedChecks}`;
    }).join('\n');
  }

  function appendTestActions(result) {
    const actions = document.createElement('div');
    actions.className = 'toolbar-row';
    actions.style.marginTop = '0.75rem';

    if (!result.passed) {
      const fixButton = document.createElement('button');
      fixButton.type = 'button';
      fixButton.className = 'btn btn-sm btn-primary';
      fixButton.textContent = 'Send failures to chat agent';
      fixButton.addEventListener('click', () => {
        if (!selectedChatAgent || !chatModelSel.value) {
          return showMsg('Choose a chat agent and model first.', true);
        }
        chatInput.value = [
          'My prompt did not pass testing. Fix only the sections or tools that failed and keep everything that passed unchanged.',
          '',
          'Failed components and checks:',
          failureFeedback(result),
          '',
          'Current prompt:',
          '',
          preview.value,
          '',
          'Return the complete revised prompt as a Markdown document with the same structure.'
        ].join('\n');
        chatForm.requestSubmit();
        markdownDraft = '';
        markdownPreview.replaceChildren();
        markdownDraftCard.classList.add('hidden');
        markdownStatus.textContent = '';
        saveState();
        chatMessages.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        showMsg('Failures sent to the chat agent. Use Add to draft, then Parse draft on its reply.');
      });
      actions.appendChild(fixButton);
    }

    {
      const createButton = document.createElement('button');
      createButton.type = 'button';
      createButton.className = result.passed ? 'btn btn-sm btn-primary' : 'btn btn-sm';
      createButton.textContent = result.passed ? 'Create agent from this prompt' : 'Create agent anyway (tests failed)';
      actions.appendChild(createButton);

      const form = document.createElement('div');
      form.className = result.passed ? 'card bg-elev' : 'card bg-elev hidden';
      form.style.cssText = 'padding: 0.75rem; margin-top: 0.5rem;';
      const defaultId = slugify(titleField.value) || 'new-agent';
      form.innerHTML = `
        <div class="form-row">
          <input class="form-input" data-new-agent-id aria-label="Agent ID" placeholder="agent-id" value="${esc(defaultId)}">
          <input class="form-input" data-new-agent-name aria-label="Agent name" placeholder="Agent name" value="${esc(titleField.value.trim())}">
        </div>
        <div class="form-row">
          <input class="form-input" data-new-agent-desc aria-label="Agent description" placeholder="Description" value="${esc(descriptionField.value.trim().split('\n')[0].slice(0, 200))}">
          <select class="form-select" data-new-agent-environment aria-label="Agent environment">
            <option value="prompt-creation" selected>Prompt Creation</option>
            <option value="workspace">Workspace</option>
            <option value="codebuilder">CodeBuilder</option>
          </select>
          <select class="form-select" data-new-agent-mode aria-label="Agent mode">
            <option value="chat"${promptTools.size ? '' : ' selected'}>Chat (no tools)</option>
            <option value="agent"${promptTools.size ? ' selected' : ''}>Agent (default tools)</option>
          </select>
        </div>
        <div class="form-row">
          <input class="form-input" data-new-agent-env-name aria-label="Custom environment name" placeholder="Custom environment name (optional)" maxlength="64">
        </div>
        <div class="toolbar-row">
          <button type="button" class="btn btn-sm btn-primary" data-new-agent-save>Create agent</button>
          <button type="button" class="btn btn-sm" data-new-agent-cancel>Cancel</button>
        </div>`;
      createButton.addEventListener('click', () => form.classList.toggle('hidden'));
      form.querySelector('[data-new-agent-cancel]').addEventListener('click', () => form.classList.add('hidden'));
      form.querySelector('[data-new-agent-save]').addEventListener('click', async event => {
        const id = slugify(form.querySelector('[data-new-agent-id]').value);
        const name = form.querySelector('[data-new-agent-name]').value.trim();
        const description = form.querySelector('[data-new-agent-desc]').value.trim();
        const mode = form.querySelector('[data-new-agent-mode]').value;
        const agentEnvironment = form.querySelector('[data-new-agent-environment]').value;
        const environmentName = form.querySelector('[data-new-agent-env-name]').value.trim();
        if (!id || !name) return showMsg('Agent ID and name are required.', true);
        const saveButton = event.currentTarget;
        saveButton.disabled = true;
        try {
          await Api.createAgent(id, name, description, mode, '', agentEnvironment, environmentName);
          await Api.publishAgent(
            id, 'prompt-creation', preview.value, agentEnvironment, [...promptTools.keys()]
          );
          showMsg(`Agent '${name}' created from the prompt (library/${id}.md)${result.passed ? '.' : ' even though tests failed.'}`);
          form.classList.add('hidden');
          await loadPromptAgents();
        } catch (err) {
          showMsg(err.message, true);
        } finally {
          saveButton.disabled = false;
        }
      });
      testResult.appendChild(actions);
      testResult.appendChild(form);
    }
    appendReportActions(result);
  }

  container.querySelector('#tb-test-prompt').addEventListener('click', async () => {
    if (!preview.value.trim()) return showMsg('Assemble a prompt before testing it.', true);
    const button = container.querySelector('#tb-test-prompt');
    const revisionBeingTested = promptRevision;
    testedPromptRevision = null;
    button.disabled = true;
    testResult.className = 'small text-muted';
    testResult.replaceChildren(document.createTextNode('Testing title, description, sections, skills, and tool descriptions…'));
    try {
      const result = await Api.evaluatePromptComponents(
        titleField.value,
        descriptionField.value,
        selectedPromptSections(),
        [...promptTools.values()].map(tool => ({
          name: tool.name,
          description: toolDescription(tool),
          signature: tool.signature
        }))
      );
      if (revisionBeingTested !== promptRevision) {
        testedPromptRevision = null;
        testResult.className = 'small text-warning';
        testResult.textContent = 'Prompt changed while tests were running. Run Test Prompt again for an up-to-date report.';
        return;
      }
      testedPromptRevision = revisionBeingTested;
      const useProbe = container.querySelector('#tb-model-test').checked;
      const useAi = container.querySelector('#tb-ai-review').checked;
      const reviewModel = chatModelSel.value;
      result.model = (useProbe || useAi) ? reviewModel : '';
      result.strengths = [];
      result.weaknesses = [];
      result.improvements = [];
      const mergeComponents = extra => {
        result.components = [...result.components, ...extra];
        result.components_total = result.components.length;
        result.components_passed = result.components.filter(item => item.passed).length;
        result.passed = result.components_passed === result.components_total;
        result.verdict = result.passed ? 'PASS' : 'FAIL';
      };
      const notes = [];
      if ((useProbe || useAi) && !reviewModel) {
        notes.push('Model tests skipped: choose a model in the chat panel.');
      } else {
        if (useProbe) {
          testResult.replaceChildren(document.createTextNode(`Structural checks done. Running model test with ${reviewModel}…`));
          try {
            const probe = await Api.probePrompt(
              reviewModel, titleField.value, descriptionField.value, preview.value,
              container.querySelector('#tb-fact-q').value, container.querySelector('#tb-fact-a').value
            );
            mergeComponents(probe.components || []);
            result.strengths = probe.strengths || [];
            result.weaknesses = probe.weaknesses || [];
            result.improvements = probe.improvements || [];
            result.model_log = probe.model_log || null;
          } catch (err) {
            notes.push(`Model test unavailable (${err.message}).`);
          }
        }
        if (useAi) {
          testResult.replaceChildren(document.createTextNode(`Running AI rubric review with ${reviewModel}…`));
          try {
            const review = await Api.judgePrompt(
              reviewModel, titleField.value, descriptionField.value, selectedPromptSections(),
              [...promptTools.values()].map(tool => ({
                name: tool.name, description: toolDescription(tool), signature: tool.signature
              }))
            );
            mergeComponents(review.components || []);
          } catch (err) {
            notes.push(`AI rubric review unavailable (${err.message}).`);
          }
        }
      }
      if (notes.length) result.ai_error = `${notes.join(' ')} Only the checks that ran are counted.`;
      for (const component of result.components) {
        if (component.passed || component.name.startsWith('Model test:')) continue;
        const fix = (component.checks || []).filter(check => !check.passed && check.fix).map(check => check.fix)[0];
        if (fix) result.improvements.push(`${component.name}: ${fix}`);
        result.weaknesses.push(`${component.name} did not pass.`);
      }
      const passedStructural = result.components.filter(item => item.passed && !item.name.startsWith('Model test:')).length;
      if (passedStructural) result.strengths.unshift(`${passedStructural} structural component(s) are complete and well formed.`);
      if (revisionBeingTested !== promptRevision) {
        testedPromptRevision = null;
        testResult.className = 'small text-warning';
        testResult.textContent = 'Prompt changed while the AI review was running. Run Test Prompt again.';
        return;
      }
      renderPromptTestResult(result);
    } catch (err) {
      testResult.className = 'small text-danger';
      testResult.textContent = `Prompt component tests could not run: ${err.message}`;
    } finally {
      button.disabled = false;
    }
  });

  function renderPromptTestResult(result) {
    testResult.className = 'small';
    testResult.replaceChildren();
    const summary = document.createElement('p');
    summary.className = result.passed ? 'text-success' : 'text-danger';
    summary.textContent = `${result.verdict}: ${result.components_passed}/${result.components_total} prompt components passed.`
      + (result.model ? ` Model: ${result.model}.` : '');
    testResult.appendChild(summary);
    if (result.model_log) {
      const logLine = document.createElement('p');
      logLine.className = 'text-muted';
      logLine.textContent = `Model log (${result.model}): ${result.model_log.passes}/${result.model_log.runs} model tests passed so far.`;
      testResult.appendChild(logLine);
    }
    for (const [label, items] of [['Strengths', result.strengths], ['Weaknesses', result.weaknesses], ['Room for improvement', result.improvements]]) {
      if (!items?.length) continue;
      const block = document.createElement('div');
      const head = document.createElement('strong');
      head.textContent = label;
      const ul = document.createElement('ul');
      for (const text of items) {
        const li = document.createElement('li');
        li.textContent = text;
        ul.appendChild(li);
      }
      block.append(head, ul);
      testResult.appendChild(block);
    }
    if (result.ai_error) {
      const note = document.createElement('p');
      note.className = 'text-warning';
      note.textContent = result.ai_error;
      testResult.appendChild(note);
    }
    const componentList = document.createElement('div');
    componentList.className = 'prompt-test-report';
    for (const component of result.components || []) {
      const row = document.createElement('div');
      row.className = `prompt-test-component ${component.passed ? 'passed' : 'failed'}`;
      const heading = document.createElement('strong');
      heading.textContent = `${component.passed ? 'PASS' : 'NOT PASS'} · ${component.name}`;
      row.appendChild(heading);
      for (const check of component.checks || []) {
        const detail = document.createElement('p');
        detail.textContent = `${check.passed ? '✓' : '✗'} ${checkDetail(check)}`;
        row.appendChild(detail);
      }
      componentList.appendChild(row);
    }
    testResult.appendChild(componentList);
    appendTestActions(result);
  }

  async function saveMarkdownFile(fileName, text) {
    if (window.showSaveFilePicker) {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: fileName,
          types: [{ description: 'Markdown', accept: { 'text/markdown': ['.md'] } }]
        });
        const writable = await handle.createWritable();
        await writable.write(text);
        await writable.close();
        return handle.name;
      } catch (err) {
        if (err.name === 'AbortError') return null;
        throw err;
      }
    }
    const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    return `${fileName} (sent to your browser's download location; this browser cannot choose a folder)`;
  }

  function buildReportMarkdown(result, title, notes) {
    const fence = text => {
      const ticks = '`'.repeat(Math.max(3, ...(String(text).match(/`+/g) || []).map(run => run.length + 1)));
      return `${ticks}markdown\n${text}\n${ticks}`;
    };
    const lines = [
      `# Prompt Test Report: ${title}`,
      '',
      `- **Date:** ${new Date().toLocaleString()}`,
      `- **Verdict:** ${result.verdict}`,
      `- **Components passed:** ${result.components_passed}/${result.components_total}`,
      `- **Model used for testing:** ${result.model || 'none (structural checks only)'}`
    ];
    if (result.model_log) {
      lines.push(`- **Model log:** ${result.model_log.passes}/${result.model_log.runs} model tests passed so far (file: test_environment/model_logs/)`);
    }
    if (result.ai_error) lines.push(`- **Note:** ${result.ai_error}`);
    if (notes) lines.push(`- **Notes:** ${notes}`);
    for (const [label, items] of [['Strengths', result.strengths], ['Weaknesses', result.weaknesses], ['Room for improvement', result.improvements]]) {
      lines.push('', `## ${label}`, '');
      if (items?.length) items.forEach(text => lines.push(`- ${text}`));
      else lines.push('- None recorded.');
    }
    const failed = (result.components || []).filter(component => !component.passed);
    lines.push('', '## Why it failed', '');
    if (!failed.length) lines.push('Nothing failed.');
    for (const component of failed) {
      lines.push(`### ${component.name}`, '');
      if (component.tested_text) lines.push('Tested text:', '', fence(component.tested_text), '');
      for (const check of (component.checks || []).filter(item => !item.passed)) {
        lines.push(`- **Check \`${check.id}\`:** ${check.evidence}`);
        if (check.rule) lines.push(`  - Rule: ${check.rule}`);
        if (check.observed) lines.push(`  - Observed: ${check.observed}`);
        if (check.fix) lines.push(`  - Suggested fix: ${check.fix}`);
      }
      lines.push('');
    }
    lines.push('## All components', '');
    for (const component of result.components || []) {
      lines.push(`- ${component.passed ? 'PASS' : 'FAIL'} — ${component.name}`);
    }
    lines.push('', '## Prompt that was tested', '', fence(preview.value), '');
    return lines.join('\n');
  }

  function appendReportActions(result) {
    const bar = document.createElement('div');
    bar.className = 'toolbar-row';
    bar.style.marginTop = '0.5rem';
    const notes = document.createElement('input');
    notes.className = 'form-input';
    notes.placeholder = 'Notes for this report (optional)';
    notes.setAttribute('aria-label', 'Report notes');
    const save = document.createElement('button');
    save.type = 'button';
    save.className = 'btn btn-sm';
    save.textContent = 'Save test report';
    save.addEventListener('click', async () => {
      save.disabled = true;
      try {
        const title = titleField.value.trim() || 'Untitled prompt';
        const markdown = buildReportMarkdown(result, title, notes.value.trim());
        const fileName = `${slugify(title) || 'prompt'}-test-report-${new Date().toISOString().slice(0, 10)}.md`;
        const where = await saveMarkdownFile(fileName, markdown);
        if (!where) return;
        let stored = '';
        try {
          await Api.saveTestReport({
            kind: 'prompt', title, model: result.model || '', subject: preview.value,
            notes: notes.value.trim(), result
          });
          stored = ' A copy was also added to Saved reports.';
        } catch {
          // the markdown file is the primary output; the history copy is optional
        }
        showMsg(`Report saved: ${where}.${stored}`);
      } catch (err) {
        showMsg(`Could not save report: ${err.message}`, true);
      } finally {
        save.disabled = false;
      }
    });
    const history = document.createElement('button');
    history.type = 'button';
    history.className = 'btn btn-sm btn-ghost';
    history.textContent = 'Saved reports';
    const list = document.createElement('div');
    list.className = 'small';
    history.addEventListener('click', async () => {
      list.replaceChildren(document.createTextNode('Loading…'));
      try {
        const { reports } = await Api.listTestReports();
        list.replaceChildren();
        if (!reports.length) list.textContent = 'No saved reports yet.';
        for (const report of reports.slice(0, 20)) {
          const item = document.createElement('button');
          item.type = 'button';
          item.className = 'btn btn-sm btn-ghost';
          item.style.display = 'block';
          item.textContent = `${report.passed ? 'PASS' : 'FAIL'} · ${report.title} · ${report.model || 'structural only'} · ${report.created_at.slice(0, 16).replace('T', ' ')}`;
          item.addEventListener('click', async () => {
            const full = await Api.getTestReport(report.id);
            renderPromptTestResult(full.result);
          });
          list.appendChild(item);
        }
      } catch (err) {
        list.textContent = `Could not load reports: ${err.message}`;
      }
    });
    bar.append(notes, save, history);
    testResult.append(bar, list);
  }
}
