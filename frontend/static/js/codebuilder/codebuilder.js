import { attachCodeBuilderEditor, loadMonaco } from './codebuilder_editor.js';
import { offerInstallForRun, confirmReset, dialog as pickerDialog } from '../sandbox_ui.js';
import { renderTree } from '../tree.js';
import { mountTerminal, TERMINAL_CHANNEL } from '../terminal.js?v=2';
import { setupFileControls } from './files_ui.js';
import { Api } from '../api.js';

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

const PREFS_KEY = 'novous2.codebuilder.';
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
  const runTimeout = document.getElementById('codebuilder-run-timeout');
  const currentTimeout = () => Number(runTimeout && runTimeout.value) || 10;
  const SERVER_CODE_PATTERN = /\b(?:app|application|server|socketio)\.run\s*\(|\bserve_forever\s*\(|\buvicorn\.run\s*\(|\bwaitress\.serve\s*\(|\bhttp\.server\b/;
  const serverMode = () => (!!runTimeout && runTimeout.value === 'server') ||
    SERVER_CODE_PATTERN.test(editor.getValue());
  const stopButton = document.getElementById('stop-run');
  let activeRunId = null;
  stopButton.addEventListener('click', async () => {
    if (!activeRunId) return;
    stopButton.disabled = true;
    try { await fetch(`/api/codebuilder/execute/${activeRunId}/cancel`, { method: 'POST' }); } catch { /* stream end reports it */ }
  });
  if (runTimeout) {
    const saved = readPref('codebuilder.runTimeout');
    if (saved && [...runTimeout.options].some(o => o.value === saved)) runTimeout.value = saved;
    runTimeout.addEventListener('change', () => writePref('codebuilder.runTimeout', runTimeout.value));
  }
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

  // The harness diagnostic can be a shortened form; prefer the exception line the console actually printed.
  const EXCEPTION_LINE = /^(?:[A-Za-z_][\w.]*\.)?[A-Z]\w*(?:Error|Exception|Exit|Interrupt)\b.*$/;
  const consoleErrorLine = () => {
    const lines = output.textContent.split('\n').map(line => line.trimEnd()).filter(Boolean);
    for (let i = lines.length - 1; i >= 0; i -= 1) {
      if (EXCEPTION_LINE.test(lines[i].trim())) return lines[i].trim();
    }
    return '';
  };
  const consoleErrorLineNumber = () => {
    let line = null;
    for (const match of output.textContent.matchAll(/File "[^"]*tool_test[^"]*", line (\d+)|File "<[^>]*>", line (\d+)|File "[^"]*", line (\d+)/g)) {
      line = Number(match[1] || match[2] || match[3]);
    }
    return line;
  };

  let lastRunCode = '';
  let lastFailure = null;
  const fixButton = document.getElementById('codebuilder-fix-with-agent');

  const buildFixPrompt = () => {
    const failure = lastFailure;
    const consoleText = output.textContent.trim();
    const trimmed = consoleText.length > 6000 ? `[earlier output omitted]\n${consoleText.slice(-6000)}` : consoleText;
    const location = failure.line ? ` (line ${failure.line})` : '';
    return [
      'My Python code failed when I ran it. Please fix it.',
      '',
      `Error${location}:`,
      failure.message,
      '',
      'Full console output:',
      '```',
      trimmed || '(no console output)',
      '```',
      '',
      'Code that was run:',
      '```python',
      lastRunCode.replace(/\s+$/, ''),
      '```',
      '',
      'Instructions:',
      '1. Find the root cause of the error above using the traceback; do not guess at unrelated problems.',
      '2. Change only what is needed to fix it. Keep the existing function names, signatures and behavior.',
      '3. Reply with the complete corrected code in a single ```python block.',
      '4. Add one or two sentences on what was wrong and what you changed.',
      '5. If you can, put the corrected code in the editor and run it to confirm the error is gone.'
    ].join('\n');
  };

  const renderDiagnostics = (items = []) => {
    diagnostics.replaceChildren();
    lastFailure = null;
    if (fixButton) fixButton.disabled = true;
    if (!items.length) {
      const empty = document.createElement('p');
      empty.className = 'text-muted';
      empty.textContent = 'No diagnostics reported.';
      diagnostics.appendChild(empty);
      return;
    }

    const exceptionLine = consoleErrorLine();
    const tracebackLine = consoleErrorLineNumber();
    items.forEach((item, index) => {
      const isError = (item.severity || 'error') === 'error';
      const message = isError && index === 0 && exceptionLine && !/^SyntaxError/.test(item.message || '')
        ? exceptionLine
        : item.message;
      const line = item.line || (isError && index === 0 ? tracebackLine : null);
      const entry = document.createElement('button');
      entry.type = 'button';
      entry.className = 'diagnostic-item';
      entry.dataset.severity = item.severity || 'error';
      entry.textContent = `${item.severity || 'error'}${line ? ` · line ${line}` : ''} · ${message}`;
      entry.title = message;
      if (line) {
        entry.addEventListener('click', () => editor.revealLine(line));
      }
      diagnostics.appendChild(entry);
      if (!lastFailure && isError) lastFailure = { message, line };
    });
    if (fixButton) fixButton.disabled = !lastFailure;
  };

  const copyConsoleButton = document.getElementById('codebuilder-copy-console');
  let openTerminalWith = () => {};
  // ---- Terminal tab (docked) with pop-out ----
  const consolePanel = root.closest('.codebuilder-shell')?.querySelector('.codebuilder-console-panel');
  const terminalSection = consolePanel?.querySelector('.codebuilder-terminal-section');
  const terminalMount = document.getElementById('codebuilder-terminal-mount');
  const terminalPopped = document.getElementById('codebuilder-terminal-popped');
  const terminalBringBack = document.getElementById('codebuilder-terminal-bring-back');
  if (consolePanel && terminalSection && terminalMount) {
    const channel = 'BroadcastChannel' in window ? new BroadcastChannel(TERMINAL_CHANNEL) : null;
    let popupWindow = null;
    let isPoppedOut = false;
    let terminal = null;

    const showTab = (tab) => {
      const showTerminal = tab === 'terminal';
      consolePanel.classList.toggle('show-terminal', showTerminal);
      terminalSection.hidden = !showTerminal;
      consolePanel.querySelectorAll('[data-console-tab]').forEach(button => {
        button.classList.toggle('active', button.dataset.consoleTab === tab);
      });
      if (showTerminal && !terminal && !isPoppedOut) {
        terminal = mountTerminal(terminalMount, { popOut: openPopOut, compact: true });
      }
      if (showTerminal) terminal?.focus();
    };

    const setPoppedOut = (value) => {
      isPoppedOut = value;
      terminalPopped.hidden = !value;
      terminalMount.hidden = value;
      if (value && terminal) {
        terminal.destroy();
        terminal = null;
      } else if (!value && !terminalSection.hidden && !terminal) {
        terminal = mountTerminal(terminalMount, { popOut: openPopOut, compact: true });
      }
    };

    function openPopOut() {
      popupWindow = window.open('/terminal', 'novous2-terminal', 'width=900,height=600');
      if (!popupWindow) {
        status.textContent = 'The browser blocked the pop-up window. Allow pop-ups for this site.';
        return;
      }
      setPoppedOut(true);
      popupWindow.focus();
    }

    consolePanel.querySelectorAll('[data-console-tab]').forEach(button => {
      button.addEventListener('click', () => showTab(button.dataset.consoleTab));
    });
    openTerminalWith = (command) => {
      if (isPoppedOut) {
        status.textContent = `Terminal is in its own window. Run: ${command}`;
        return;
      }
      showTab('terminal');
      terminal?.setInput(command);
    };
    terminalBringBack?.addEventListener('click', () => {
      channel?.postMessage({ type: 'close-popout' });
      try { popupWindow?.close(); } catch { /* already closed */ }
      setPoppedOut(false);
    });
    if (channel) {
      channel.onmessage = (event) => {
        if (event.data?.type === 'popout-open') setPoppedOut(true);
        if (event.data?.type === 'popout-closed') setPoppedOut(false);
      };
      channel.postMessage({ type: 'ping' });
    }
  }
  copyConsoleButton?.addEventListener('click', async () => {
    const text = output.textContent;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const area = document.createElement('textarea');
      area.value = text;
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      area.remove();
    }
    copyConsoleButton.textContent = 'Copied';
    setTimeout(() => { copyConsoleButton.textContent = 'Copy'; }, 1500);
  });

  fixButton?.addEventListener('click', () => {
    if (!lastFailure) return;
    chatInput.value = buildFixPrompt();
    chatInput.dispatchEvent(new Event('input', { bubbles: true }));
    chatInput.focus();
    chatInput.scrollTop = 0;
    status.textContent = 'Error and code copied to the agent message box';
  });

  const streamRiskyRun = async () => {
    const timeoutSeconds = currentTimeout();
    const response = await fetch('/api/codebuilder/execute/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: editor.getValue(),
        timeout_seconds: timeoutSeconds,
        keep_running: serverMode(),
        mode: 'risky'
      })
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
    let servingUrl = null;
    let stoppedByUser = false;

    const ingest = (event) => {
      switch (event.type) {
        case 'start':
          activeRunId = event.run_id;
          stopButton.hidden = false;
          stopButton.disabled = false;
          break;
        case 'stdout':
          output.textContent += event.text;
          streamedText += event.text;
          if (!servingUrl) {
            const match = streamedText.match(/https?:\/\/(?:127\.0\.0\.1|localhost|0\.0\.0\.0):\d+/);
            if (match) {
              servingUrl = match[0].replace('0.0.0.0', '127.0.0.1');
              status.textContent = `Serving at ${servingUrl} — press Stop to end`;
            }
          }
          break;
        case 'stderr':
          output.textContent += event.text;
          streamedText += event.text;
          if (!servingUrl) {
            const match = streamedText.match(/https?:\/\/(?:127\.0\.0\.1|localhost|0\.0\.0\.0):\d+/);
            if (match) {
              servingUrl = match[0].replace('0.0.0.0', '127.0.0.1');
              status.textContent = `Serving at ${servingUrl} — press Stop to end`;
            }
          }
          break;
        case 'truncated':
          output.textContent += '\n[Earlier output truncated]\n';
          break;
        case 'syntax_error':
          syntaxError = { line: event.line, message: event.message };
          break;
        case 'done':
          stoppedByUser = stoppedByUser || /Cancelled: run stopped/.test(streamedText);
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
    } else if (stoppedByUser) {
      renderDiagnostics([]);
      editor.setDiagnostics([]);
      status.textContent = 'Stopped';
      runStatus = 'SUCCESS';
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

  const runCodeOnce = async () => {
    const mode = serverMode() ? 'risky' : currentRunMode();
    lastRunCode = editor.getValue();
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
        body: JSON.stringify({ code: editor.getValue(), timeout_seconds: currentTimeout(), mode: 'safe' })
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
      activeRunId = null;
      stopButton.hidden = true;
      runButton.disabled = false;
      runButton.textContent = '▶ Run Python';
      editor.focus();
    }
  };

  const runCode = async () => {
    const result = await runCodeOnce();
    if (result && result.status !== 'SUCCESS' &&
        await offerInstallForRun(editor.getValue(), output.textContent)) {
      return runCodeOnce();
    }
    return result;
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

  // Code handed over from the Tool Function Testing Workbench.
  try {
    const incoming = localStorage.getItem('novous2.codebuilder.incoming');
    if (incoming) {
      localStorage.removeItem('novous2.codebuilder.incoming');
      if (sendCodeToEditor(incoming)) status.textContent = 'Code received from Tool Workbench';
    }
  } catch { /* storage unavailable */ }

  const handleCodeBuilderToolEvents = async (events = []) => {
    for (const event of events) {
      if (event.status !== 'success') continue;
      if (['write_file', 'create_file', 'delete_file'].includes(event.tool)) {
        window.dispatchEvent(new CustomEvent('novous:fs-changed'));
      }
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

  // Memory mode: the chat transcript is saved to a file the user picks.
  let memoryPath = null;
  let transcript = [];

  const notifyFilesChanged = () => window.dispatchEvent(new CustomEvent('novous:fs-changed'));

  const writeMemory = async () => {
    if (!memoryPath) return;
    const body = transcript
      .map(entry => `[${entry.role}]\n${entry.text}`)
      .join('\n\n');
    try {
      await Api.writeManagedFile(memoryPath, `${body}\n`);
      notifyFilesChanged();
    } catch (error) {
      appendChatMessage('system', `Memory mode stopped: could not write ${memoryPath} (${error.message}).`);
      memoryPath = null;
      renderAgents();
    }
  };

  // Opens the file manager: click a folder (or an existing file) and name the memory file.
  const pickMemoryLocation = () => new Promise(resolve => {
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15);
    let folder = '';
    let settled = false;
    const finish = (value, close) => {
      if (settled) return;
      settled = true;
      close();
      resolve(value);
    };

    pickerDialog('Memory mode — choose where to save', (modal, close) => {
      modal.classList.add('is-resizable');
      const hint = document.createElement('p');
      hint.className = 'text-muted small';
      hint.textContent = 'Pick a folder in the file manager and name the file. The chat is saved after every reply.';

      const treeHost = document.createElement('div');
      treeHost.className = 'codebuilder-open-tree';

      const target = document.createElement('p');
      target.className = 'small codebuilder-memory-target';
      const nameInput = document.createElement('input');
      nameInput.className = 'form-input';
      nameInput.type = 'text';
      nameInput.value = `chat_memory_${stamp}.txt`;
      nameInput.setAttribute('aria-label', 'Memory file name');
      const error = document.createElement('p');
      error.className = 'text-danger small';

      const refreshTarget = () => {
        target.textContent = `Save to: ${folder || '(workspace root)'}/${nameInput.value.trim()}`;
      };
      nameInput.addEventListener('input', refreshTarget);
      refreshTarget();

      const actions = document.createElement('div');
      actions.className = 'question-dialog-actions';
      const cancel = document.createElement('button');
      cancel.type = 'button';
      cancel.className = 'btn';
      cancel.textContent = 'Cancel';
      const start = document.createElement('button');
      start.type = 'button';
      start.className = 'btn btn-primary';
      start.textContent = 'Start';
      actions.append(cancel, start);
      modal.append(hint, treeHost, target, nameInput, error, actions);

      renderTree(treeHost, {
        manageRoots: true,
        onSelectDirectory: path => { folder = path; refreshTarget(); },
        onSelect: path => {
          const slash = path.lastIndexOf('/');
          folder = slash >= 0 ? path.slice(0, slash) : '';
          nameInput.value = path.slice(slash + 1);
          refreshTarget();
        }
      });

      cancel.addEventListener('click', () => finish(null, close));
      const submit = () => {
        const name = nameInput.value.trim();
        if (!name || name === '.' || name === '..' || /[\\/]/.test(name)) {
          error.textContent = 'Enter a file name without folder separators.';
          return;
        }
        finish([folder, name].filter(Boolean).join('/'), close);
      };
      start.addEventListener('click', submit);
      nameInput.addEventListener('keydown', event => { if (event.key === 'Enter') submit(); });
    });
  });

  const toggleMemory = async () => {
    if (memoryPath) {
      memoryPath = null;
      appendChatMessage('system', 'Memory mode off.');
      renderAgents();
      return;
    }
    const path = await pickMemoryLocation();
    if (!path) return;
    memoryPath = path;
    transcript = [];
    appendChatMessage('system', `Memory mode on. Saving this chat to ${path}.`);
    renderAgents();
    await writeMemory();
  };

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
    memory: [
      'M4 6c0-1.1 3.6-2 8-2s8 .9 8 2-3.6 2-8 2-8-.9-8-2Z',
      'M4 6v6c0 1.1 3.6 2 8 2s8-.9 8-2V6',
      'M4 12v6c0 1.1 3.6 2 8 2s8-.9 8-2v-6',
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

    const picker = document.createElement('select');
    picker.className = 'form-select codebuilder-agent-select';
    picker.id = 'codebuilder-agent-select';
    picker.setAttribute('aria-label', 'Choose agent');
    picker.disabled = chatPending || !agents.length;
    agents.forEach(agent => {
      const toolCount = (agent.tools || []).length;
      const option = new Option(`${agent.name} (${toolCount} tool${toolCount === 1 ? '' : 's'})`, agent.id);
      option.disabled = !hasAgentFunctions(agent);
      option.title = (agent.tools || []).join(', ') || 'No tools';
      picker.add(option);
    });
    if (selectedAgent) picker.value = selectedAgent.id;
    picker.addEventListener('change', () => {
      const chosen = agents.find(agent => agent.id === picker.value);
      if (chosen && chosen.id !== selectedAgent?.id) selectAgent(chosen);
    });
    agentList.appendChild(picker);

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

    const memoryTile = buildAgentTile(
      'Memory',
      'memory',
      memoryPath
        ? `Memory mode on — saving to ${memoryPath}. Click to turn off.`
        : 'Save this chat to a text file you choose',
      toggleMemory,
      Boolean(memoryPath)
    );
    memoryTile.setAttribute('aria-label', 'Memory mode');
    agentList.appendChild(memoryTile);

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
  document.getElementById('reset-sandbox')?.addEventListener('click', async () => {
    try {
      const result = await confirmReset();
      if (result) status.textContent = result.output;
    } catch (err) {
      status.textContent = `Reset failed: ${err.message}`;
    }
  });
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
  const fileControls = setupFileControls({
    editor,
    status,
    label: document.getElementById('codebuilder-filename'),
    buttons: {
      save: document.getElementById('save-file'),
      saveAs: document.getElementById('save-file-as'),
      open: document.getElementById('open-file'),
      runTerminal: document.getElementById('run-in-terminal')
    },
    openTerminalWith: (command) => openTerminalWith(command)
  });
  editor.onChange(() => {
    fileControls.refreshLabel();
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
    if (memoryPath) transcript.push({ role: 'user', text: message });
    chatInput.value = '';
    chatPending = true;
    chatStatus.textContent = `Waiting for ${selectedAgent.name}…`;
    updateChatControls();
    try {
      const response = await fetch('/api/chat/stream', {
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
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || 'The agent request failed.');
      }

      const bubble = document.createElement('div');
      bubble.className = 'codebuilder-chat-message assistant';
      chatMessages.appendChild(bubble);

      let text = '';
      let liveCode = null;
      let paintQueued = false;
      let donePayload = null;
      let failure = null;

      // Newest ```python fence in the streamed text; an unclosed fence counts as in progress.
      const latestCode = () => {
        let found = null;
        for (const match of text.matchAll(/```([\w+-]*)[^\n]*\n([\s\S]*?)(```|$)/g)) {
          if (['', 'python', 'py'].includes(match[1].toLowerCase())) found = match[2];
        }
        return found;
      };
      const paint = () => {
        paintQueued = false;
        bubble.textContent = text;
        chatMessages.scrollTop = chatMessages.scrollHeight;
        const code = latestCode();
        if (code !== null && code !== liveCode) {
          liveCode = code;
          editor.setValue(code);
          status.textContent = 'Agent is writing code…';
        }
      };
      const schedulePaint = () => {
        if (!paintQueued) { paintQueued = true; requestAnimationFrame(paint); }
      };

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const handleEvent = async item => {
        if (item.type === 'token') {
          text += item.text;
          schedulePaint();
        } else if (item.type === 'tool_event') {
          await handleCodeBuilderToolEvents([item.event]);
        } else if (item.type === 'done') {
          donePayload = item;
        } else if (item.type === 'error') {
          failure = item.detail || 'The agent request failed.';
        }
      };
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split('\n\n');
        buffer = frames.pop();
        for (const frame of frames) {
          const line = frame.split('\n').find(l => l.startsWith('data: '));
          if (line) await handleEvent(JSON.parse(line.slice(6)));
        }
      }

      paint();
      if (failure) {
        bubble.remove();
        throw new Error(failure);
      }
      const reply = donePayload?.reply || text || 'The agent returned an empty response.';
      bubble.textContent = '';
      appendAssistantMessage(bubble, reply);
      if (liveCode !== null) sendCodeToEditor(liveCode, 'agent');
      if (memoryPath) {
        transcript.push({ role: 'assistant', text: reply });
        await writeMemory();
      }
      chatStatus.textContent = `${selectedAgent.name} · ${donePayload?.model || modelSelect.value}`;
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
          <label class="codebuilder-run-mode">
            <select id="codebuilder-run-timeout" aria-label="Time limit for a run">
              <option value="10">Limit: 10 sec</option>
              <option value="120">Limit: 2 min</option>
              <option value="240">Limit: 4 min</option>
              <option value="480">Limit: 8 min</option>
              <option value="server">Server: no limit (Stop)</option>
            </select>
          </label>
          <button id="load-demo" class="btn btn-sm" type="button" title="Load the sample Python program">Sample</button>
          <button id="open-file" class="btn btn-sm" type="button" title="Open a file from the file manager">Open…</button>
          <button id="save-file" class="btn btn-sm" type="button" title="Save (Ctrl+S)">Save</button>
          <button id="save-file-as" class="btn btn-sm" type="button" title="Save as a new file">Save As…</button>
          <button id="run-in-terminal" class="btn btn-sm" type="button" title="Save, then prepare the command in the Terminal tab">Run in Terminal</button>
          <button id="clear-console" class="btn btn-sm" type="button" title="Clear console and diagnostics">Clear Output</button>
          <button id="reset-sandbox" class="btn btn-sm" type="button" title="Remove all packages installed for testing">Reset Environment</button>
          <button id="stop-run" class="btn btn-sm" type="button" title="Stop the running program" hidden>■ Stop</button>
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
            <span id="codebuilder-filename" class="codebuilder-filename">Untitled</span>
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
          <div class="codebuilder-console-tabs" role="tablist">
            <button type="button" class="btn btn-sm active" data-console-tab="console" role="tab">Console</button>
            <button type="button" class="btn btn-sm" data-console-tab="terminal" role="tab">Terminal</button>
          </div>
          <section class="codebuilder-output-section">
            <h3>Console</h3>
            <button id="codebuilder-copy-console" class="btn btn-sm" type="button"
                    title="Copy the console output">Copy</button>
            <pre id="codebuilder-output" class="console-output">Ready. Run your Python code to see output here.</pre>
          </section>
          <section class="codebuilder-problems-section">
            <h3>Problems</h3>
            <button id="codebuilder-fix-with-agent" class="btn btn-sm btn-primary" type="button" disabled
                    title="Copy the error, console output and code into the agent message box">Fix with Agent</button>
            <div id="diagnostics" class="diagnostics-list"></div>
          </section>
          <section class="codebuilder-terminal-section" hidden>
            <div id="codebuilder-terminal-mount" class="codebuilder-terminal-mount"></div>
            <div id="codebuilder-terminal-popped" class="codebuilder-terminal-popped" hidden>
              <p>The terminal is open in a separate window.</p>
              <button id="codebuilder-terminal-bring-back" class="btn btn-sm btn-primary" type="button">Bring back</button>
            </div>
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
