import { Api } from './api.js';

let openSuiteDialog = null;
let suiteExecutionActive = false;

function parseSteps(content) {
  return String(content ?? '')
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const checkbox = line.match(/^(?:[-*+]\s*)?\[([ xX])\]\s*(.*)$/);
      const plainListItem = line.match(/^(?:\d+[.)]\s+|[-*+]\s+)(.*)$/);
      return {
        id: index + 1,
        enabled: checkbox ? checkbox[1].toLowerCase() === 'x' : true,
        text: (checkbox ? checkbox[2] : plainListItem ? plainListItem[1] : line).trim()
      };
    })
    .filter(step => step.text);
}

function serializeSteps(steps) {
  return steps.map(step => `- [${step.enabled ? 'x' : ' '}] ${step.text}`).join('\n') + '\n';
}

export function openTestSuiteRunner({
  filePath,
  agentId,
  model,
  agents,
  models,
  onRunningChange = () => {},
  onChatMessage = () => {},
  onToolEvent = () => {}
}) {
  if (openSuiteDialog) {
    openSuiteDialog.focus();
    return;
  }

  const overlay = document.createElement('div');
  overlay.className = 'suite-dialog-overlay';
  overlay.innerHTML = `
    <section class="card suite-dialog" role="dialog" aria-modal="true"
      aria-labelledby="suite-dialog-title" tabindex="-1">
      <header class="suite-dialog-header">
        <div>
          <h2 id="suite-dialog-title">Test Suite Runner</h2>
          <p class="text-muted small" data-suite-source></p>
        </div>
        <button class="btn btn-sm btn-ghost" type="button" data-suite-close
          aria-label="Close Test Suite Runner" title="Close">×</button>
      </header>
      <div class="suite-dialog-config">
        <label>Agent
          <select class="form-select" data-suite-agent></select>
        </label>
        <label>Model
          <select class="form-select" data-suite-model></select>
        </label>
      </div>
      <div class="suite-dialog-steps-heading">
        <h3>Test steps</h3>
        <button class="btn btn-sm" type="button" data-suite-add>+ Add Step</button>
      </div>
      <ol class="suite-step-list" data-suite-steps aria-label="Test steps"></ol>
      <section class="suite-output-section" aria-label="Test execution output">
        <div class="suite-output-heading">
          <h3>Execution output</h3>
          <span class="text-muted small" data-suite-progress>Ready</span>
        </div>
        <p class="text-muted small suite-evaluation-note">
          Tool results and agent responses are shown as evidence. A successful tool call does not by itself prove the task is complete.
        </p>
        <div class="suite-output" data-suite-output role="log" aria-live="polite"></div>
      </section>
      <footer class="suite-dialog-footer">
        <button class="btn btn-primary" type="button" data-suite-run>Run Test Suite</button>
        <div class="suite-dialog-footer-secondary">
          <button class="btn btn-sm" type="button" data-suite-stop disabled>Stop</button>
          <button class="btn btn-sm" type="button" data-suite-save>Save</button>
          <button class="btn btn-sm" type="button" data-suite-close>Close</button>
        </div>
      </footer>
    </section>`;

  const dialog = overlay.querySelector('.suite-dialog');
  const sourceLabel = overlay.querySelector('[data-suite-source]');
  const agentSelect = overlay.querySelector('[data-suite-agent]');
  const modelSelect = overlay.querySelector('[data-suite-model]');
  const stepList = overlay.querySelector('[data-suite-steps]');
  const output = overlay.querySelector('[data-suite-output]');
  const progress = overlay.querySelector('[data-suite-progress]');
  const runButton = overlay.querySelector('[data-suite-run]');
  const stopButton = overlay.querySelector('[data-suite-stop]');
  const saveButton = overlay.querySelector('[data-suite-save]');
  const addButton = overlay.querySelector('[data-suite-add]');
  let steps = [];
  let nextId = 1;
  let running = false;
  let loadingSource = Boolean(filePath);
  let stopRequested = false;
  let sourceLoaded = !filePath;
  let dirty = false;
  let closed = false;
  let closeAfterRun = false;

  sourceLabel.textContent = filePath ? `Suite file: ${filePath}` : 'Choose a To-Do file in Chat & Test Controls to save this suite.';
  agentSelect.replaceChildren(...agents.map(agent => {
    const option = document.createElement('option');
    option.value = agent.id;
    option.textContent = `${agent.name} (${agent.mode})`;
    option.selected = agent.id === agentId;
    return option;
  }));
  modelSelect.replaceChildren(...models.map(name => {
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name;
    option.selected = name === model;
    return option;
  }));
  if (model && !models.includes(model)) {
    const option = document.createElement('option');
    option.value = model;
    option.textContent = model;
    option.selected = true;
    modelSelect.appendChild(option);
  }

  function setStatus(message, type = '') {
    progress.textContent = message;
    progress.className = `small${type ? ` text-${type}` : ' text-muted'}`;
  }

  function updateControls() {
    const canEdit = !running && !loadingSource;
    stepList.querySelectorAll('input, button').forEach(control => {
      control.disabled = !canEdit || control.dataset.unavailable === 'true';
    });
    addButton.disabled = !canEdit;
    agentSelect.disabled = !canEdit;
    modelSelect.disabled = !canEdit || !models.length;
    runButton.disabled = running || suiteExecutionActive || loadingSource ||
      !agentSelect.value || !modelSelect.value ||
      !steps.some(step => step.enabled && step.text.trim());
    stopButton.disabled = !running || stopRequested;
    saveButton.disabled = running || loadingSource || !filePath || !sourceLoaded;
  }

  function renderSteps(focusId = null) {
    stepList.replaceChildren();
    steps.forEach((step, index) => {
      const item = document.createElement('li');
      item.className = 'suite-step';
      item.dataset.stepId = String(step.id);

      const enabled = document.createElement('input');
      enabled.type = 'checkbox';
      enabled.checked = step.enabled;
      enabled.setAttribute('aria-label', `Enable step ${index + 1}`);
      enabled.addEventListener('change', () => {
        step.enabled = enabled.checked;
        dirty = true;
        updateControls();
      });

      const instruction = document.createElement('input');
      instruction.type = 'text';
      instruction.className = 'form-input';
      instruction.value = step.text;
      instruction.placeholder = `Step ${index + 1} instruction`;
      instruction.setAttribute('aria-label', `Step ${index + 1} instruction`);
      instruction.addEventListener('input', () => {
        step.text = instruction.value;
        dirty = true;
        updateControls();
      });

      const actions = document.createElement('div');
      actions.className = 'suite-step-actions';
      [
        { action: 'up', label: 'Move up', icon: '↑', disabled: index === 0 },
        { action: 'down', label: 'Move down', icon: '↓', disabled: index === steps.length - 1 },
        { action: 'remove', label: 'Remove step', icon: '×', disabled: false }
      ].forEach(control => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-sm btn-ghost suite-step-action';
        button.textContent = control.icon;
        button.title = control.label;
        button.setAttribute('aria-label', control.label);
        button.disabled = control.disabled;
        button.dataset.unavailable = String(control.disabled);
        button.addEventListener('click', () => {
          if (control.action === 'remove') {
            steps = steps.filter(itemStep => itemStep.id !== step.id);
          } else {
            const nextIndex = control.action === 'up' ? index - 1 : index + 1;
            [steps[index], steps[nextIndex]] = [steps[nextIndex], steps[index]];
          }
          dirty = true;
          renderSteps();
        });
        actions.appendChild(button);
      });

      item.append(enabled, instruction, actions);
      stepList.appendChild(item);
    });
    updateControls();
    if (focusId != null) {
      stepList.querySelector(`[data-step-id="${focusId}"] input[type="text"]`)?.focus();
    }
  }

  function appendOutput(title, body, status = 'info') {
    const entry = document.createElement('article');
    entry.className = `suite-result suite-result-${status}`;
    const heading = document.createElement('div');
    heading.className = 'suite-result-heading';
    const label = document.createElement('strong');
    label.textContent = title;
    const badge = document.createElement('span');
    badge.className = `badge ${status === 'failed' ? 'badge-warning' : status === 'completed' ? 'badge-success' : 'badge-accent'}`;
    badge.textContent = status === 'info' ? 'RUNNING' : status.toUpperCase();
    heading.append(label, badge);
    const text = document.createElement('pre');
    text.textContent = body;
    entry.append(heading, text);
    output.appendChild(entry);
    output.scrollTop = output.scrollHeight;
    return { entry, text };
  }

  async function runSuite() {
    if (running || suiteExecutionActive) return;
    const enabledSteps = steps.filter(step => step.enabled && step.text.trim());
    if (!enabledSteps.length) {
      setStatus('Enable or add at least one step.', 'danger');
      return;
    }
    if (!agentSelect.value || !modelSelect.value) {
      setStatus('Select an agent and installed model.', 'danger');
      return;
    }

    running = true;
    suiteExecutionActive = true;
    stopRequested = false;
    output.replaceChildren();
    onRunningChange(true);
    updateControls();
    const selectedAgent = agentSelect.value;
    const selectedModel = modelSelect.value;
    const sessionId = `chat-${selectedAgent}`;
    appendOutput(
      'Suite started',
      `${enabledSteps.length} enabled step(s) · Agent: ${selectedAgent} · Model: ${selectedModel}`,
      'info'
    );
    onChatMessage('user', `Starting execution of ${enabledSteps.length} test step(s).`);

    let completed = 0;
    let failed = 0;
    let toolCallsSucceeded = 0;
    let toolCallsFailed = 0;
    try {
      for (let index = 0; index < enabledSteps.length; index += 1) {
        if (stopRequested) break;
        const step = enabledSteps[index];
        setStatus(`Step ${index + 1} of ${enabledSteps.length}`);
        const stepOutput = appendOutput(
          `Step ${index + 1}: ${step.text}`,
          'Waiting for agent response…',
          'info'
        );
        onChatMessage('user', `Task ${index + 1}: ${step.text}`);
        try {
          let reply = '';
          const stepToolEvents = [];
          const result = await Api.streamMessage(
            step.text,
            selectedAgent,
            selectedModel,
            sessionId,
            'workspace',
            async event => {
              if (event.type === 'token') {
                reply += event.text;
                stepOutput.text.textContent = reply;
                output.scrollTop = output.scrollHeight;
              } else if (event.type === 'tool_event') {
                const tool = event.event || {};
                stepToolEvents.push(tool);
                const succeeded = tool.status === 'success';
                const resultText = tool.error || tool.result || 'No result was returned.';
                const details = [
                  `Status: ${tool.status || 'unknown'}`,
                  tool.args ? `Arguments: ${JSON.stringify(tool.args)}` : '',
                  `Result: ${resultText}`,
                  tool.result_truncated ? '(Result preview truncated.)' : ''
                ].filter(Boolean).join('\n');
                appendOutput(
                  `Step ${index + 1} · ${tool.tool || 'Tool'}`,
                  details,
                  succeeded ? 'completed' : 'failed'
                );
                if (succeeded) toolCallsSucceeded += 1;
                else toolCallsFailed += 1;
                onToolEvent(tool);
              }
            }
          );
          reply = result.reply || reply;
          if (!reply.trim()) throw new Error('The agent returned an empty response.');
          onChatMessage('assistant', reply);
          const statusBadge = stepOutput.entry.querySelector('.suite-result-heading .badge');
          statusBadge.textContent = stepToolEvents.length
            ? stepToolEvents.some(tool => tool.status !== 'success')
              ? 'RESPONSE · TOOL ERROR'
              : 'RESPONSE · TOOLS OK'
            : 'RESPONSE · NO TOOL CALLS';
          statusBadge.className = `badge ${
            stepToolEvents.some(tool => tool.status !== 'success')
              ? 'badge-warning'
              : 'badge-accent'
          }`;
          stepOutput.text.textContent = reply;
          completed += 1;
        } catch (error) {
          failed += 1;
          stepOutput.entry.querySelector('.suite-result-heading .badge').textContent = 'FAILED';
          stepOutput.entry.querySelector('.suite-result-heading .badge').className = 'badge badge-warning';
          stepOutput.text.textContent = stepOutput.text.textContent
            ? `${stepOutput.text.textContent}\n\nRequest failed: ${error.message}`
            : error.message;
          onChatMessage('system', `Test step ${index + 1} failed: ${error.message}`);
        }
        if (stopRequested) break;
      }
      const stopped = stopRequested;
      setStatus(
        stopped
          ? `Stopped · ${completed} responses · ${failed} request failures`
          : `Finished · ${completed} responses · ${failed} request failures`,
        failed || toolCallsFailed ? 'danger' : 'success'
      );
      appendOutput(
        stopped ? 'Suite stopped' : 'Suite finished',
        `${completed} response(s) received · ${toolCallsSucceeded} successful tool call(s) · `
          + `${toolCallsFailed} tool error(s) · ${failed} request failure(s). `
          + 'Review the tool results and agent responses to decide whether each task succeeded.'
          + (stopped ? ' · Remaining steps were not run.' : ''),
        failed || toolCallsFailed ? 'failed' : stopped ? 'stopped' : 'completed'
      );
    } finally {
      running = false;
      suiteExecutionActive = false;
      stopRequested = false;
      onRunningChange(false);
      updateControls();
      if (closeAfterRun) {
        closed = true;
        openSuiteDialog = null;
        overlay.remove();
      }
    }
  }

  async function saveSuite() {
    if (!filePath || !sourceLoaded || running) return;
    saveButton.disabled = true;
    setStatus('Saving suite…');
    try {
      await Api.writeFile(filePath, serializeSteps(steps));
      dirty = false;
      setStatus(`Saved to ${filePath}.`, 'success');
    } catch (error) {
      setStatus(`Could not save suite: ${error.message}`, 'danger');
    } finally {
      updateControls();
    }
  }

  function closeDialog() {
    if (running) {
      if (closeAfterRun) return;
      if (!confirm('A step is still running. Stop after its response finishes and close the runner?')) return;
      stopRequested = true;
      closeAfterRun = true;
      setStatus('Stop requested; waiting for the current response before stopping.');
      updateControls();
      return;
    }
    if (dirty && !confirm('Close without saving your test suite changes?')) {
      return;
    }
    closed = true;
    openSuiteDialog = null;
    overlay.remove();
  }

  addButton.addEventListener('click', () => {
    const step = { id: nextId++, enabled: true, text: '' };
    steps.push(step);
    dirty = true;
    renderSteps(step.id);
  });
  runButton.addEventListener('click', runSuite);
  stopButton.addEventListener('click', () => {
    if (!running || stopRequested) return;
    stopRequested = true;
    stopButton.disabled = true;
    setStatus('Stop requested; the current response will finish before stopping.');
  });
  saveButton.addEventListener('click', saveSuite);
  overlay.querySelectorAll('[data-suite-close]').forEach(button => {
    button.addEventListener('click', closeDialog);
  });
  overlay.addEventListener('click', event => {
    if (event.target === overlay) closeDialog();
  });
  const onKeyDown = event => {
    if (event.key === 'Escape' && !closed) closeDialog();
  };
  overlay.addEventListener('keydown', onKeyDown);

  document.body.appendChild(overlay);
  openSuiteDialog = dialog;
  dialog.querySelector('[data-suite-close]').focus();
  renderSteps();
  if (filePath) {
    setStatus('Loading selected test list…');
    Api.readFile(filePath).then(file => {
      if (closed) return;
      steps = parseSteps(file.content);
      nextId = steps.reduce((maximum, step) => Math.max(maximum, step.id), 0) + 1;
      loadingSource = false;
      sourceLoaded = true;
      renderSteps();
      setStatus(`${steps.length} step(s) loaded.`, 'success');
    }).catch(error => {
      if (closed) return;
      loadingSource = false;
      sourceLoaded = false;
      setStatus(`Could not load ${filePath}: ${error.message}`, 'danger');
      appendOutput('Could not load suite file', error.message, 'failed');
      updateControls();
    });
  } else {
    setStatus('Add steps, or select a To-Do file in Chat & Test Controls to load and save a suite.');
  }
}
