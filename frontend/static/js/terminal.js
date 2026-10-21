const API = '/api/codebuilder/terminal';
const ANSI = /\x1b\[[0-9;?]*[A-Za-z]/g;
const URL_PATTERN = /https?:\/\/(?:localhost|127\.0\.0\.1|0\.0\.0\.0):\d+\S*/g;
const MAX_CHARS = 200000;

export const TERMINAL_CHANNEL = 'novous2-terminal';

async function post(path, body) {
  const response = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status}).`);
  return payload;
}

// Builds a terminal into `root` and attaches to the shared backend session.
// Returns { destroy, attach, detach, focus }.
export function mountTerminal(root, { popOut = null, compact = false } = {}) {
  root.innerHTML = `
    <div class="tw-terminal${compact ? ' compact' : ''}">
      <div class="tw-terminal-bar">
        <span class="tw-terminal-cwd" title="Working folder"></span>
        <span class="tw-terminal-badge" hidden>sandbox</span>
        <span class="tw-terminal-spacer"></span>
        <button type="button" class="btn btn-sm" data-act="stop" disabled>Stop</button>
        <button type="button" class="btn btn-sm" data-act="clear">Clear</button>
        <button type="button" class="btn btn-sm" data-act="copy">Copy</button>
        ${popOut ? '<button type="button" class="btn btn-sm" data-act="popout" title="Open the terminal in its own window">Pop out</button>' : ''}
      </div>
      <div class="tw-terminal-links" hidden></div>
      <pre class="tw-terminal-output" tabindex="0"></pre>
      <form class="tw-terminal-form" autocomplete="off">
        <span class="tw-terminal-prompt">&gt;</span>
        <input type="text" class="tw-terminal-input" spellcheck="false"
               placeholder="streamlit run app.py   ·   python script.py   ·   pip install package"
               aria-label="Terminal command">
      </form>
    </div>`;

  const outputEl = root.querySelector('.tw-terminal-output');
  const cwdEl = root.querySelector('.tw-terminal-cwd');
  const badge = root.querySelector('.tw-terminal-badge');
  const linksEl = root.querySelector('.tw-terminal-links');
  const form = root.querySelector('.tw-terminal-form');
  const input = root.querySelector('.tw-terminal-input');
  const stopButton = root.querySelector('[data-act="stop"]');

  let text = '';
  let offset = 0;
  let source = null;
  let retry = null;
  let running = false;
  let destroyed = false;
  const history = [];
  let historyIndex = 0;

  const renderLinks = () => {
    const urls = [...new Set(text.match(URL_PATTERN) || [])].slice(-3);
    linksEl.replaceChildren();
    linksEl.hidden = !urls.length;
    urls.forEach(url => {
      const link = document.createElement('a');
      link.href = url.replace('0.0.0.0', 'localhost');
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = `Open ${url}`;
      linksEl.appendChild(link);
    });
  };

  const append = (chunk) => {
    if (!chunk) return;
    const atBottom = outputEl.scrollHeight - outputEl.scrollTop - outputEl.clientHeight < 40;
    text += chunk.replace(ANSI, '').replace(/\r\n/g, '\n');
    if (text.length > MAX_CHARS) text = text.slice(-MAX_CHARS);
    outputEl.textContent = text;
    if (atBottom) outputEl.scrollTop = outputEl.scrollHeight;
    renderLinks();
  };

  const applyState = (state) => {
    running = !!state.running;
    cwdEl.textContent = state.cwd || '';
    badge.hidden = !state.sandbox;
    stopButton.disabled = !running;
    input.placeholder = running ? 'A command is running — press Stop to end it' : input.placeholder;
  };

  const detach = () => {
    clearTimeout(retry);
    if (source) source.close();
    source = null;
  };

  const attach = () => {
    detach();
    if (destroyed) return;
    source = new EventSource(`${API}/stream?offset=${offset}`);
    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        offset = data.offset ?? offset;
        append(data.text);
        applyState(data);
      } catch { /* ignore malformed event */ }
    };
    source.onerror = () => {
      detach();
      retry = setTimeout(attach, 1500);
    };
  };

  const runCommand = async (command) => {
    history.push(command);
    historyIndex = history.length;
    try {
      applyState(await post('/run', { command }));
    } catch (err) {
      append(`${err.message}\n`);
    }
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const command = input.value.trim();
    if (!command) return;
    input.value = '';
    runCommand(command);
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowUp' && history.length) {
      historyIndex = Math.max(0, historyIndex - 1);
      input.value = history[historyIndex];
      event.preventDefault();
    } else if (event.key === 'ArrowDown' && history.length) {
      historyIndex = Math.min(history.length, historyIndex + 1);
      input.value = history[historyIndex] ?? '';
      event.preventDefault();
    }
  });

  root.addEventListener('click', async (event) => {
    const act = event.target.closest('[data-act]')?.dataset.act;
    if (!act) return;
    if (act === 'stop') {
      await post('/stop').catch(() => {});
    } else if (act === 'clear') {
      await post('/clear').catch(() => {});
      text = '';
      outputEl.textContent = '';
      renderLinks();
    } else if (act === 'copy') {
      const button = event.target.closest('button');
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
      button.textContent = 'Copied';
      setTimeout(() => { button.textContent = 'Copy'; }, 1500);
    } else if (act === 'popout' && popOut) {
      popOut();
    }
  });

  attach();

  return {
    attach,
    detach,
    focus: () => input.focus(),
    setInput: (value) => { input.value = value; input.focus(); },
    destroy: () => { destroyed = true; detach(); }
  };
}
