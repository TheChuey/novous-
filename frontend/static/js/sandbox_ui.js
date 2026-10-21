// Shared UI for the isolated test environment (install missing packages, reset).

async function call(method, url, body) {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    throw new Error(typeof detail === 'string' ? detail : (detail?.message || `Request failed (${response.status})`));
  }
  return payload;
}

export const Sandbox = {
  check: (source, modules = []) => call('POST', '/api/sandbox/check', { source, modules }),
  install: packages => call('POST', '/api/sandbox/install', { packages }),
  reset: () => call('POST', '/api/sandbox/reset')
};

export function missingModulesFromOutput(text) {
  const names = [...String(text || '').matchAll(/No module named '([A-Za-z_][\w]*)/g)].map(m => m[1]);
  return [...new Set(names)];
}

export function dialog(title, buildBody) {
  const overlay = document.createElement('div');
  overlay.className = 'question-dialog-overlay';
  const modal = document.createElement('div');
  modal.className = 'card question-dialog';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  const head = document.createElement('div');
  head.className = 'question-dialog-head';
  const heading = document.createElement('h3');
  heading.textContent = title;
  head.appendChild(heading);
  modal.appendChild(head);
  overlay.appendChild(modal);
  document.body.appendChild(overlay);
  const close = () => overlay.remove();
  buildBody(modal, close);
  return close;
}

// Resolves true when packages were installed, false when cancelled or failed.
export function promptInstall(missing) {
  return new Promise(resolve => {
    dialog('Install missing packages?', (modal, close) => {
      const text = document.createElement('p');
      text.className = 'question-dialog-prompt';
      text.textContent = 'This code needs packages that are not in the test environment. ' +
        'Installing runs third-party code from PyPI. Edit the list if a package name is different.';
      const input = document.createElement('input');
      input.className = 'form-input question-dialog-input';
      input.value = missing.map(item => item.package).join(' ');
      input.setAttribute('aria-label', 'Packages to install (space separated)');
      const log = document.createElement('pre');
      log.className = 'tool-workbench-output';
      log.hidden = true;
      const actions = document.createElement('div');
      actions.className = 'question-dialog-actions';
      const cancel = document.createElement('button');
      cancel.type = 'button';
      cancel.className = 'btn';
      cancel.textContent = 'Cancel';
      const install = document.createElement('button');
      install.type = 'button';
      install.className = 'btn btn-primary';
      install.textContent = 'Install';
      actions.append(cancel, install);
      modal.append(text, input, log, actions);
      input.focus();

      cancel.addEventListener('click', () => { close(); resolve(false); });
      install.addEventListener('click', async () => {
        const packages = input.value.split(/\s+/).filter(Boolean);
        if (!packages.length) return;
        install.disabled = cancel.disabled = input.disabled = true;
        install.textContent = 'Installing…';
        log.hidden = false;
        log.textContent = `pip install ${packages.join(' ')}\n`;
        try {
          const result = await Sandbox.install(packages);
          log.textContent += result.output || '';
          if (result.ok) {
            setTimeout(() => { close(); resolve(true); }, 600);
            return;
          }
          log.textContent += '\nInstall failed.';
        } catch (err) {
          log.textContent += `\nError: ${err.message}`;
        }
        install.disabled = cancel.disabled = input.disabled = false;
        install.textContent = 'Retry';
        cancel.textContent = 'Close';
      });
    });
  });
}

// Detects missing packages for the code and the run output, then offers to install them.
// Returns true when something was installed so the caller can re-run.
export async function offerInstallForRun(source, outputText) {
  const named = missingModulesFromOutput(outputText);
  if (!named.length) return false;
  let missing;
  try {
    missing = (await Sandbox.check(source, named)).missing;
  } catch {
    missing = named.map(module => ({ module, package: module }));
  }
  if (!missing.length) return false;
  return promptInstall(missing);
}

export async function offerInstallBeforeRun(source) {
  let missing;
  try {
    missing = (await Sandbox.check(source, [])).missing;
  } catch {
    return false;
  }
  return missing.length ? promptInstall(missing) : false;
}

export async function confirmReset() {
  if (!confirm('Reset the test environment? All packages installed for testing will be removed.')) return null;
  return Sandbox.reset();
}
