import { attachCodeBuilderEditor, loadMonaco } from './codebuilder_editor.js';

const DEMO_CODE = `print("Hello from Novous CodeBuilder!")
for i in range(3):
    print(f"count={i}")
`;

const CODE_LANGUAGE_MAP = {
  py: 'python', python: 'python', python3: 'python',
  js: 'javascript', javascript: 'javascript', node: 'javascript',
  ts: 'typescript', typescript: 'typescript',
  html: 'html', css: 'css', scss: 'scss', json: 'json',
  sh: 'shell', bash: 'shell', shell: 'shell', zsh: 'shell', powershell: 'powershell',
  yaml: 'yaml', yml: 'yaml', ini: 'ini', toml: 'ini', xml: 'xml',
  md: 'markdown', markdown: 'markdown', text: 'plaintext', txt: 'plaintext',
};

async function copyTextToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch { /* fall through to legacy copy */ }
  }
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'fixed';
  area.style.top = '0';
  area.style.left = '0';
  area.style.opacity = '0';
  document.body.appendChild(area);
  area.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch { ok = false; }
  area.remove();
  return ok;
}

const PREFS_KEY = 'novous.codebuilder.';
const PANEL_CONF = {
  chat:    { var: '--chat-w',    min: 240, maxFactor: 0.45, rail: 44, default: 320 },
  console: { var: '--console-w', min: 220, maxFactor: 0.45, rail: 44, default: 300 },
  agents:  { var: '--agents-h',  min: 120, max: 340,        rail: 38, default: 220 },
};
const PANEL_LABELS = { chat: 'Chat', console: 'Console', agents: 'Agents' };
const PANEL_GLYPHS = { chat: ['«', '»'], console: ['»', '«'], agents: ['⌄', '⌃'] };
const PANEL_BUTTONS = {
  chat: '#codebuilder-chat-expand',
  console: '#codebuilder-console-collapse',
  agents: '#codebuilder-agents-toggle',
};

const readPref = key => {
  try { return localStorage.getItem(PREFS_KEY + key); } catch { return null; }
};
const writePref = (key, value) => {
  try { localStorage.setItem(PREFS_KEY + key, value); } catch { /* storage unavailable */ }
};
const readVar = (element, name) => parseFloat(
  element.style.getPropertyValue(name) || getComputedStyle(element).getPropertyValue(name)
);

const clampSize = (layout, name, value) => {
  const conf = PANEL_CONF[name];
  const max = conf.max ?? Math.max(conf.min, layout.clientWidth * conf.maxFactor);
  return Math.round(Math.min(Math.max(value, conf.min), max));
};

function restoreLayoutState(shell) {
  const layout = shell.querySelector('.codebuilder-layout');
  if (!layout) return;
  for (const name of Object.keys(PANEL_CONF)) {
    const conf = PANEL_CONF[name];
    const saved = parseFloat(readPref(name + 'Width'));
    if (Number.isFinite(saved)) layout.style.setProperty(conf.var, clampSize(layout, name, saved) + 'px');
    if (readPref(name + 'Collapsed') === '1') {
      shell.classList.add(name + '-collapsed');
      layout.style.setProperty(conf.var, conf.rail + 'px');
    }
  }
}

function refreshPanelToggle(shell, name) {
  const button = shell.querySelector(PANEL_BUTTONS[name]);
  if (!button) return;
  const collapsed = shell.classList.contains(name + '-collapsed');
  const label = PANEL_LABELS[name];
  button.textContent = collapsed ? PANEL_GLYPHS[name][1] : PANEL_GLYPHS[name][0];
  button.title = collapsed ? `Expand ${label} panel` : `Collapse ${label} panel`;
  button.setAttribute('aria-label', button.title);
  button.setAttribute('aria-expanded', String(!collapsed));
}

function setupResizers(shell) {
  const layout = shell.querySelector('.codebuilder-layout');
  if (!layout) return;
  shell.querySelectorAll('.codebuilder-resizer').forEach(resizer => {
    const name = resizer.dataset.resize;
    const conf = PANEL_CONF[name];
    if (!conf) return;
    resizer.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      event.preventDefault();
      if (shell.classList.contains(name + '-collapsed')) {
        shell.classList.remove(name + '-collapsed');
        writePref(name + 'Collapsed', '0');
        refreshPanelToggle(shell, name);
      }
      const axis = name === 'agents' ? 'clientY' : 'clientX';
      const startPos = event[axis];
      const start = clampSize(layout, name, readVar(layout, conf.var) || conf.default);
      resizer.setPointerCapture(event.pointerId);
      document.body.classList.add('is-resizing');
      resizer.classList.add('is-dragging');
      const onMove = moveEvent => {
        layout.style.setProperty(
          conf.var,
          clampSize(layout, name, start + (moveEvent[axis] - startPos)) + 'px'
        );
      };
      const onUp = () => {
        resizer.removeEventListener('pointermove', onMove);
        resizer.removeEventListener('pointerup', onUp);
        document.body.classList.remove('is-resizing');
        resizer.classList.remove('is-dragging');
        const final = readVar(layout, conf.var);
        if (Number.isFinite(final)) writePref(name + 'Width', String(final));
      };
      resizer.addEventListener('pointermove', onMove);
      resizer.addEventListener('pointerup', onUp);
    });
  });
}

const RISKY_CODE_PATTERN = /\b(?:subprocess|os\.system|os\.popen|os\.spawn|pty|commands)\b|shell\s*[:=]\s*true|\binput\s*\(|^\s*!/im;
const RUN_MODE_KEY = 'codebuilder.runMode';

export async function setupCodeBuilderPage(rootId = 'codebuilder-editor') {
  const root = document.getElementById(rootId);
  const output = document.getElementById('codebuilder-output');
  const diagnostics = document.getElementById('diagnostics');
  const runButton = document.getElementById('run-code');
  const runMode = document.getElementById('codebuilder-run-mode');
  const demoButton = document.getElementById('load-demo');
  const clearButton = document.getElementById('clear-console');
  const status = document.getElementById('codebuilder-status');
  const agentList = document.getElementById('codebuilder-agent-list');
  const agentRefresh = document.getElementById('codebuilder-agent-refresh');
  const agentsPanel = document.getElementById('codebuilder-agents-panel');
  const agentsToggle = document.getElementById('codebuilder-agents-toggle');
  const modelSelect = document.getElementById('codebuilder-model');
  const chatForm = document.getElementById('codebuilder-chat-form');
  const chatInput = document.getElementById('codebuilder-chat-input');
  const chatMessages = document.getElementById('codebuilder-chat-messages');
  const chatStatus = document.getElementById('codebuilder-chat-status');
  const chatPanel = document.getElementById('codebuilder-chat-panel');
  const chatExpand = document.getElementById('codebuilder-chat-expand');
  const chatClear = document.getElementById('codebuilder-chat-clear');
  const consoleCollapse = document.getElementById('codebuilder-console-collapse');
  const shell = agentsPanel?.closest('.codebuilder-shell') ?? root.closest('.codebuilder-shell');
  const layout = shell?.querySelector('.codebuilder-layout');

  if (!root || !output || !diagnostics || !runButton || !runMode || !demoButton || !clearButton ||
      !agentList || !agentRefresh || !agentsPanel || !agentsToggle ||
      !modelSelect || !chatForm || !chatInput || !chatMessages || !chatStatus ||
      !chatPanel || !chatExpand || !chatClear || !consoleCollapse || !shell || !layout) {
    console.error('CodeBuilder could not start because a required page element is missing.');
    return null;
  }

  restoreLayoutState(shell);
  setupResizers(shell);

  const editor = await attachCodeBuilderEditor(root, DEMO_CODE);
  let agents = [];
  let selectedAgent = null;
  let defaultModel = 'qwen2.5-coder:latest';
  let chatPending = false;
  let manualRunMode = null;
  const chatCodeEditors = new Set();

  const detectRunMode = () => (RISKY_CODE_PATTERN.test(editor.getValue()) ? 'risky' : 'safe');
  const currentRunMode = () => (manualRunMode || detectRunMode());

  const disposeChatCodeEditors = () => {
    chatCodeEditors.forEach(editor => {
      try { editor.dispose(); } catch { /* already disposed */ }
    });
    chatCodeEditors.clear();
  };

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

  const streamRiskyRun = async () => {
    const timeoutSeconds = 10;
    const response = await fetch('/api/codebuilder/execute/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: editor.getValue(), timeout_seconds: timeoutSeconds, mode: 'risky' })
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || `Stream request failed (${response.status}).`);
    }
    if (!response.body || typeof response.body.getReader !== 'function') {
      throw new Error('Live streaming is not supported by this browser.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let returnCode = 0;
    let runStatus = 'SUCCESS';
    let streamedText = '';
    let syntaxError = null;

    const ingest = (event) => {
      switch (event.type) {
        case 'stdout':
          output.textContent += event.text;
          streamedText += event.text;
          break;
        case 'stderr':
          output.textContent += event.text;
          streamedText += event.text;
          break;
        case 'truncated':
          output.textContent += '\n[Earlier output truncated]\n';
          break;
        case 'syntax_error':
          syntaxError = { line: event.line, message: event.message };
          break;
        case 'done':
          returnCode = event.return_code ?? returnCode;
          runStatus = event.status || runStatus;
          break;
        default:
          break;
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let separator = buffer.indexOf('\n\n');
      while (separator !== -1) {
        const rawEvent = buffer.slice(0, separator);
        buffer = buffer.slice(separator + 2);
        for (const line of rawEvent.split('\n')) {
          if (!line.startsWith('data: ')) continue;
          try {
            ingest(JSON.parse(line.slice(6)));
          } catch { /* ignore malformed event */ }
        }
        separator = buffer.indexOf('\n\n');
      }
    }
    const remainder = buffer.trim();
    if (remainder.startsWith('data: ')) {
      try { ingest(JSON.parse(remainder.slice(6))); } catch { /* ignore */ }
    }

    if (syntaxError) {
      renderDiagnostics([{ severity: 'error', line: syntaxError.line, message: syntaxError.message }]);
      editor.setDiagnostics([{ severity: 'error', line: syntaxError.line, message: syntaxError.message }]);
      status.textContent = 'Finished with errors';
    } else if (runStatus === 'ERROR') {
      const lastLine = [...streamedText.trim().split('\n')].filter(Boolean).pop() || '';
      const message = lastLine || `Process exited with code ${returnCode}.`;
      renderDiagnostics([{ severity: 'error', message }]);
      editor.setDiagnostics([]);
      status.textContent = 'Finished with errors';
    } else {
      renderDiagnostics([]);
      editor.setDiagnostics([]);
    }

    return {
      status: runStatus === 'SUCCESS' ? 'SUCCESS' : 'ERROR',
      stdout: streamedText,
      stderr: '',
      diagnostics: [],
    };
  };

  const runCode = async () => {
    const mode = currentRunMode();
    runButton.disabled = true;
    runButton.textContent = mode === 'risky' ? 'Running… (stream)' : 'Running…';
    output.textContent = '';
    status.textContent = 'Running';
    diagnostics.replaceChildren();
    editor.setDiagnostics([]);

    try {
      if (mode === 'risky') {
        const result = await streamRiskyRun();
        if (result && !output.textContent.trim()) {
          output.textContent = 'Execution completed with no output.';
        }
        return result;
      }

      const response = await fetch('/api/codebuilder/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: editor.getValue(), timeout_seconds: 10, mode: 'safe' })
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

  const createCopyCodeButton = (code) => {
    const copyButton = document.createElement('button');
    copyButton.type = 'button';
    copyButton.className = 'btn btn-sm codebuilder-copy-code';
    copyButton.textContent = 'Copy Code';
    copyButton.setAttribute('aria-label', 'Copy code to clipboard');
    copyButton.addEventListener('click', async () => {
      const ok = await copyTextToClipboard(code);
      copyButton.textContent = ok ? 'Copied!' : 'Copy failed';
      copyButton.disabled = ok;
      setTimeout(() => {
        copyButton.textContent = 'Copy Code';
        copyButton.disabled = false;
      }, 2000);
    });
    return copyButton;
  };

  const createSendToEditorButton = (code) => {
    const sendButton = document.createElement('button');
    sendButton.type = 'button';
    sendButton.className = 'btn btn-sm codebuilder-send-code';
    sendButton.textContent = 'Send to editor';
    sendButton.setAttribute('aria-label', 'Send code to the editor');
    sendButton.addEventListener('click', () => {
      if (sendCodeToEditor(code)) {
        sendButton.textContent = 'Sent to editor';
        sendButton.disabled = true;
      }
    });
    return sendButton;
  };

  const openChatCodeModal = (code, codeLanguage) => {
    const overlay = document.createElement('div');
    overlay.className = 'codebuilder-code-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', `Expanded ${codeLanguage} code block`);

    const panel = document.createElement('div');
    panel.className = 'codebuilder-code-modal';

    const heading = document.createElement('div');
    heading.className = 'codebuilder-code-modal-heading';
    const title = document.createElement('span');
    title.className = 'codebuilder-code-language';
    title.textContent = codeLanguage;
    heading.appendChild(title);

    const actions = document.createElement('div');
    actions.className = 'codebuilder-code-actions';
    actions.append(createCopyCodeButton(code), createSendToEditorButton(code));
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn btn-sm codebuilder-modal-close';
    closeButton.textContent = 'Close';
    closeButton.setAttribute('aria-label', 'Close expanded code block');
    actions.appendChild(closeButton);
    heading.appendChild(actions);

    const body = document.createElement('div');
    body.className = 'codebuilder-code-modal-body';

    const pre = document.createElement('pre');
    const codeElement = document.createElement('code');
    codeElement.className = `language-${codeLanguage}`;
    codeElement.textContent = code;
    pre.appendChild(codeElement);
    body.appendChild(pre);

    panel.append(heading, body);
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    let modalEditor = null;
    const close = () => {
      if (modalEditor) {
        try { modalEditor.dispose(); } catch { /* already disposed */ }
      }
      overlay.remove();
      document.body.classList.remove('codebuilder-modal-open');
      document.removeEventListener('keydown', onKey);
    };
    const onKey = event => { if (event.key === 'Escape') close(); };

    overlay.addEventListener('click', event => { if (event.target === overlay) close(); });
    closeButton.addEventListener('click', close);
    document.addEventListener('keydown', onKey);
    document.body.classList.add('codebuilder-modal-open');

    mountChatCodeEditor(body, pre, code, codeLanguage, {
      maxHeight: Math.round(window.innerHeight * 0.6),
      wordWrap: 'off',
      addToRegistry: false,
    }).then(editor => { modalEditor = editor; });
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

    const buildCodeBlock = (code, rawLanguage) => {
      const language = rawLanguage || 'python';
      const block = document.createElement('section');
      block.className = 'codebuilder-code-block';

      const heading = document.createElement('div');
      heading.className = 'codebuilder-code-heading';
      const languageLabel = document.createElement('span');
      languageLabel.className = 'codebuilder-code-language';
      languageLabel.textContent = language;
      heading.appendChild(languageLabel);

      const actions = document.createElement('div');
      actions.className = 'codebuilder-code-actions';
      actions.append(createCopyCodeButton(code), createSendToEditorButton(code));

      const expandButton = document.createElement('button');
      expandButton.type = 'button';
      expandButton.className = 'btn btn-sm codebuilder-expand-code';
      expandButton.textContent = 'Expand';
      expandButton.setAttribute('aria-label', 'Open this code block in a larger view');
      expandButton.addEventListener('click', () => openChatCodeModal(code, language));
      actions.appendChild(expandButton);
      heading.appendChild(actions);

      const body = document.createElement('div');
      body.className = 'codebuilder-chat-code';

      const pre = document.createElement('pre');
      const codeElement = document.createElement('code');
      codeElement.className = `language-${language}`;
      codeElement.textContent = code;
      pre.appendChild(codeElement);
      body.appendChild(pre);

      block.append(heading, body);
      message.appendChild(block);

      mountChatCodeEditor(body, pre, code, language, {
        maxHeight: 420,
        wordWrap: 'on',
        addToRegistry: true,
      });
    };

    while ((match = codeBlockPattern.exec(content)) !== null) {
      appendText(content.slice(lastIndex, match.index));
      let rawLanguage = match[1].trim().split(/\s+/, 1)[0].toLowerCase();
      let snippet = match[2].trimEnd();
      if (rawLanguage === 'json' || ['text', 'txt', 'plaintext', ''].includes(rawLanguage)) {
        try {
          snippet = JSON.stringify(JSON.parse(snippet), null, 2);
          rawLanguage = 'python';
        } catch { /* keep the raw snippet when it is not valid JSON */ }
      }
      buildCodeBlock(snippet, rawLanguage);
      lastIndex = codeBlockPattern.lastIndex;
    }

    appendText(content.slice(lastIndex));
  };

  const mountChatCodeEditor = (container, fallbackPre, code, rawLanguage, options = {}) => {
    const { maxHeight = 360, wordWrap = 'on', addToRegistry = true } = options;
    const language = CODE_LANGUAGE_MAP[rawLanguage] || rawLanguage || 'plaintext';
    const lineCount = code.split('\n').length;
    container.style.height = `${Math.min(maxHeight, Math.max(72, lineCount * 18 + 16))}px`;

    return loadMonaco().then(monaco => {
      if (!container.isConnected || !chatCodeEditors) return null;
      if (!monaco?.editor || typeof monaco.editor.create !== 'function') return null;
      fallbackPre.remove();
      const editor = monaco.editor.create(container, {
        value: code,
        language,
        theme: 'vs-dark',
        readOnly: true,
        automaticLayout: true,
        minimap: { enabled: false },
        folding: false,
        glyphMargin: false,
        lineDecorationsWidth: 0,
        lineNumbers: 'off',
        renderLineHighlight: 'none',
        scrollBeyondLastLine: false,
        wordWrap,
        contextmenu: false,
        fixedOverflowWidgets: true,
      });
      if (addToRegistry) chatCodeEditors.add(editor);
      return editor;
    }).catch(() => null);
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

  const FUTURE_AGENT_OPTIONS = [
    { id: 'debugAgent', label: 'Debug Agent', icon: 'bug' },
    { id: 'diagnostics', label: 'Diagnostics', icon: 'activity' },
  ];

  const hasAgentFunctions = agent => Array.isArray(agent.tools) && agent.tools.length > 0;

  const AGENT_TILE_ICONS = {
    bot: [
      'M12 8V4H8',
      'M4 8v12a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1Z',
      'M8 13v2',
      'M12 13v2',
      'M16 13v2',
    ],
    bug: [
      'm8 2 1.88 1.88',
      'M14.12 3.88 16 2',
      'M9 7.13v-1a3.003 3.003 0 1 1 6 0v1',
      'M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6',
      'M12 20v-9',
      'M6.53 9C4.6 8.8 3 7.1 3 5',
      'M6 13H2',
      'M3 21c0-2.1 1.7-3.9 3.8-4',
      'M20.97 5c0 2.1-1.6 3.8-3.5 4',
      'M22 13h-4',
      'M17.2 17c2.1.1 3.8 1.9 3.8 4',
    ],
    activity: [
      'M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2',
    ],
  };

  const buildTileIcon = (name) => {
    const iconPath = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(iconPath, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('width', '20');
    svg.setAttribute('height', '20');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    (AGENT_TILE_ICONS[name] || []).forEach(pathData => {
      const path = document.createElementNS(iconPath, 'path');
      path.setAttribute('d', pathData);
      svg.appendChild(path);
    });
    return svg;
  };

  const buildAgentTile = (label, icon, title, onClick, isSelected) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'test-function codebuilder-agent-tile';
    button.title = title;
    if (isSelected) button.classList.add('selected');
    button.setAttribute('aria-pressed', String(Boolean(isSelected)));

    const iconElement = buildTileIcon(icon);
    const labelElement = document.createElement('span');
    labelElement.textContent = label;

    if (typeof onClick === 'function') {
      button.addEventListener('click', onClick);
    } else {
      button.disabled = true;
      button.classList.add('disabled');
    }
    button.append(iconElement, labelElement);
    return button;
  };

  const renderAgents = () => {
    agentList.replaceChildren();

    agents.forEach(agent => {
      const isSelected = selectedAgent?.id === agent.id;
      const hasFunctions = hasAgentFunctions(agent);
      const tile = buildAgentTile(
        agent.name,
        'bot',
        hasFunctions
          ? (agent.description || agent.name)
          : `${agent.name} — no tools available`,
        () => selectAgent(agent),
        isSelected
      );
      tile.setAttribute('aria-label', `${agent.name} agent`);
      if (chatPending || !hasFunctions) {
        tile.disabled = true;
        tile.classList.add('disabled');
      }
      agentList.appendChild(tile);
    });

    FUTURE_AGENT_OPTIONS.forEach(option => {
      const tile = buildAgentTile(
        option.label,
        option.icon,
        `${option.label} — not implemented yet`,
        null,
        false
      );
      agentList.appendChild(tile);
    });

    if (!agents.length) {
      selectedAgent = null;
      const empty = document.createElement('p');
      empty.className = 'text-muted small';
      empty.textContent = 'No agents found in the workspace agents folder.';
      agentList.appendChild(empty);
    }

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
    disposeChatCodeEditors();
    appendChatMessage('system', `Chatting with ${agent.name}.`);
    chatStatus.textContent = `Agent: ${agent.name}`;
  };

  const loadAgents = async () => {
    agentRefresh.disabled = true;
    try {
      const data = await fetch('/api/codebuilder/agents').then(async response => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || 'Could not load agents.');
        return payload;
      });
      agents = data.agents || [];
      const selectedId = selectedAgent?.id;
      selectedAgent = agents.find(agent => agent.id === selectedId) || agents[0] || null;
      renderAgents();
      if (selectedAgent) selectAgent(selectedAgent);
    } catch (error) {
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

  const persistedRunMode = readPref(RUN_MODE_KEY);
  if (persistedRunMode === 'risky' || persistedRunMode === 'safe') {
    manualRunMode = persistedRunMode;
    runMode.value = persistedRunMode;
  }
  runMode.addEventListener('change', () => {
    manualRunMode = runMode.value;
    writePref(RUN_MODE_KEY, runMode.value);
  });
  editor.onChange(() => {
    if (manualRunMode) return;
    if (runMode.value !== detectRunMode()) runMode.value = detectRunMode();
  });
  agentRefresh.addEventListener('click', loadAgents);

  const togglePanel = (name) => {
    const conf = PANEL_CONF[name];
    const collapsed = !shell.classList.contains(name + '-collapsed');
    if (collapsed) {
      const current = readVar(layout, conf.var);
      if (Number.isFinite(current) && current > conf.rail) writePref(name + 'Width', String(current));
      shell.classList.add(name + '-collapsed');
      layout.style.setProperty(conf.var, conf.rail + 'px');
    } else {
      const saved = parseFloat(readPref(name + 'Width'));
      layout.style.setProperty(
        conf.var,
        (Number.isFinite(saved) ? clampSize(layout, name, saved) : conf.default) + 'px'
      );
      shell.classList.remove(name + '-collapsed');
    }
    writePref(name + 'Collapsed', collapsed ? '1' : '0');
    return collapsed;
  };

  chatExpand.addEventListener('click', () => { togglePanel('chat'); refreshPanelToggle(shell, 'chat'); });
  consoleCollapse.addEventListener('click', () => { togglePanel('console'); refreshPanelToggle(shell, 'console'); });
  agentsToggle.addEventListener('click', () => { togglePanel('agents'); refreshPanelToggle(shell, 'agents'); });

  refreshPanelToggle(shell, 'chat');
  refreshPanelToggle(shell, 'console');
  refreshPanelToggle(shell, 'agents');

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
  chatClear.addEventListener('click', () => {
    chatInput.value = '';
    chatMessages.replaceChildren();
    disposeChatCodeEditors();
    if (selectedAgent) {
      appendChatMessage('system', 'Chat cleared. Ask a new question.');
      chatStatus.textContent = `Agent: ${selectedAgent.name}`;
    } else {
      appendChatMessage('system', 'Chat cleared.');
      chatStatus.textContent = 'Chat cleared';
    }
    chatInput.focus();
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
          <label class="codebuilder-run-mode">
            <select id="codebuilder-run-mode" aria-label="Choose how to run Python code">
              <option value="safe">Safe (in-process)</option>
              <option value="risky">Risky (isolated, streams)</option>
            </select>
          </label>
          <button id="load-demo" class="btn btn-sm" type="button" title="Load the sample Python program">Sample</button>
          <button id="clear-console" class="btn btn-sm" type="button" title="Clear console and diagnostics">Clear Output</button>
          <button id="run-code" class="btn btn-sm btn-primary" type="button" title="Run Python (Ctrl+Enter)">▶ Run Python</button>
        </div>
      </div>

      <main class="codebuilder-layout">
        <section id="codebuilder-chat-panel" class="codebuilder-chat-panel" aria-label="Chat with an agent">
          <div class="codebuilder-chat-heading">
            <h2>Ask an Agent</h2>
            <span id="codebuilder-chat-status" class="text-muted small">Select an agent to start.</span>
            <button id="codebuilder-chat-expand" class="btn btn-sm codebuilder-chat-expand"
                    type="button" aria-label="Collapse chat panel" aria-expanded="true"
                    title="Collapse chat panel">«</button>
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
            <textarea id="codebuilder-chat-input" class="form-input" rows="4"
                      placeholder="Ask the selected agent about your Python code…"
                      aria-label="Message to agent"></textarea>
            <div class="codebuilder-chat-actions">
              <button id="codebuilder-chat-clear" class="btn btn-sm"
                      type="button" aria-label="Clear chat" title="Clear the chat conversation">Clear</button>
              <button class="btn btn-primary" type="submit" disabled>Send</button>
            </div>
          </form>
        </section>

        <div class="codebuilder-resizer" data-resize="chat" role="separator"
             aria-orientation="vertical" aria-label="Resize chat panel"></div>

        <section class="codebuilder-editor-panel" aria-label="Python editor">
          <div id="codebuilder-editor" class="editor-surface"></div>
          <div class="codebuilder-statusbar">
            <span id="codebuilder-status">Loading editor…</span>
            <span>Python</span>
            <span>UTF-8</span>
            <span>Spaces: 4</span>
          </div>
        </section>

        <div class="codebuilder-resizer" data-resize="console" role="separator"
             aria-orientation="vertical" aria-label="Resize console panel"></div>

        <aside class="codebuilder-console-panel" aria-label="Run output and diagnostics">
          <div class="codebuilder-console-heading">
            <h2>Run Output</h2>
            <span class="codebuilder-console-subtitle">Console &amp; Problems</span>
            <button id="codebuilder-console-collapse" class="btn btn-sm codebuilder-console-collapse"
                    type="button" aria-label="Collapse console panel" aria-expanded="true"
                    title="Collapse console panel">»</button>
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

        <div class="codebuilder-resizer" data-resize="agents" role="separator"
             aria-orientation="horizontal" aria-label="Resize agents panel"></div>

        <aside id="codebuilder-agents-panel" class="codebuilder-agents-panel" aria-label="Workspace agents">
          <div class="codebuilder-agents-heading">
            <button id="codebuilder-agents-toggle" class="btn btn-sm codebuilder-agents-toggle"
                    type="button" aria-label="Collapse agents panel" aria-expanded="true"
                    title="Collapse agents panel">⌄</button>
            <button id="codebuilder-agent-refresh" class="btn btn-sm codebuilder-agent-refresh"
                    type="button" title="Refresh agents" aria-label="Refresh agents">↻</button>
          </div>
          <div id="codebuilder-agent-list" class="codebuilder-agent-list"></div>
        </aside>
      </main>
    </div>
  `;

  setupCodeBuilderPage();
}

if (typeof window !== 'undefined' && document.readyState !== 'loading') {
  const root = document.getElementById('codebuilder-editor');
  if (root) setupCodeBuilderPage();
}
