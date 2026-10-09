import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

export function renderTestingView(container) {
  container.innerHTML = `
    <div class="card testing-runner">
      <div class="card-head">
        <h3>Prompt Header Evaluation Battery</h3>
        <button type="button" class="btn btn-sm btn-primary" id="ht-run">Run Header Tests</button>
      </div>
      <div class="form-row">
        <select id="ht-agent" class="form-select">
          <option value="">Loading workspace agents…</option>
        </select>
      </div>
      <div id="ht-results" class="ht-results mt-3">
        <p class="text-muted">Select an agent profile to run section-header verification (role, purpose, boundaries, output format).</p>
      </div>
    </div>`;

  const agentSel = container.querySelector('#ht-agent');
  const results = container.querySelector('#ht-results');

  Api.getAgents().then(data => {
    const agents = data.agents || [];
    agentSel.innerHTML = agents.length
      ? agents.map(a => `<option value="${esc(a.id)}">${esc(a.name)} (${esc(a.id)})</option>`).join('')
      : '<option value="">No agents found</option>';
  }).catch(err => {
    agentSel.innerHTML = `<option value="">Error: ${esc(err.message)}</option>`;
  });

  function renderReport(report) {
    const header = `
      <div class="ht-summary ${report.passed ? 'pass' : 'fail'}">
        <strong>Verdict: ${esc(report.verdict)}</strong>
        <span>Overall Score: ${esc(report.overall_score)} (${esc(report.headers_passed)}/${esc(report.headers_total)} headers passed)</span>
      </div>`;

    const rows = (report.results || []).map(r => `
      <div class="ht-header ${r.passed ? 'pass' : 'fail'}">
        <div class="ht-header-head">
          <span class="ht-hash">## ${esc(r.header)}</span>
          <span class="badge ${r.passed ? 'badge-success' : 'badge-danger'}">${esc(Number(r.score || 0).toFixed(2))}</span>
        </div>
        ${((r.questions || []).map(q => `
          <div class="ht-question">
            <span class="ht-q-status ${q.passed ? 'pass' : 'fail'}">${q.passed ? '✓' : '✗'}</span>
            <div>
              <div>${esc(q.question)}</div>
              <div class="text-muted small">${esc(q.evidence)} · score ${esc(q.score)}</div>
            </div>
          </div>`).join(''))}
      </div>`).join('');

    const extras = report.extra_headers?.length
      ? `<p class="text-muted small">Extra headers: ${esc(report.extra_headers.join(', '))}</p>`
      : '';

    return header + rows + extras;
  }

  container.querySelector('#ht-run').addEventListener('click', async () => {
    if (!agentSel.value) return;
    results.innerHTML = '<p class="text-muted">Executing header battery evaluation...</p>';
    try {
      const report = await Api.runHeaderTests(agentSel.value);
      results.innerHTML = renderReport(report);
    } catch (err) {
      results.innerHTML = `<p class="text-danger">Error: ${esc(err.message)}</p>`;
    }
  });

  renderToolWorkbench(container);
}

function renderToolWorkbench(container) {
  container.insertAdjacentHTML('beforeend', `
    <section class="card tool-workbench mt-3" aria-labelledby="tool-workbench-title">
      <div class="card-head">
        <div>
          <h3 id="tool-workbench-title">Tool Function Testing Workbench</h3>
          <p class="text-muted small">Tests run on this computer using the local Python interpreter. Only run code you trust: tested code can access files, network, and resources available to your user account. Each run has a 5-second timeout.</p>
        </div>
        <button type="button" class="btn btn-sm" id="tw-reset">Reset</button>
      </div>
      <div class="tool-workbench-grid">
        <label class="tool-workbench-field">
          <span>LLM model</span>
          <span class="tool-workbench-model">
            <select id="tw-model" class="form-select" aria-label="LLM model">
              <option value="">Loading models…</option>
            </select>
            <button type="button" class="btn btn-sm" id="tw-refresh-models">Refresh</button>
          </span>
        </label>
        <label class="tool-workbench-field tool-workbench-wide">
          <span>Function code</span>
          <textarea id="tw-code" class="tool-workbench-editor" rows="12" spellcheck="false"></textarea>
        </label>
        <label class="tool-workbench-field">
          <span>Function input (JSON)</span>
          <textarea id="tw-input" class="tool-workbench-editor" rows="5" spellcheck="false"></textarea>
        </label>
        <label class="tool-workbench-field">
          <span>Prompt for LLM tool calling</span>
          <textarea id="tw-prompt" class="form-input" rows="5"></textarea>
        </label>
      </div>
      <div class="tool-workbench-actions">
        <button type="button" class="btn btn-primary" id="tw-run">Run Code Test</button>
        <button type="button" class="btn" id="tw-run-llm">Test Tool with LLM</button>
        <button type="button" class="btn" id="tw-save" disabled>Save Test Report (.md)</button>
        <button type="button" class="btn" id="tw-promote" disabled
                title="Run a successful test before adding a tool">Add Passed Tool to Library</button>
        <span id="tw-status" class="text-muted small" role="status">Ready</span>
      </div>
      <label class="tool-workbench-field">
        <span>Test output</span>
        <pre id="tw-output" class="tool-workbench-output" aria-live="polite">Run a test to see its result.</pre>
      </label>
      <div class="tool-workbench-library">
        <h4>Registered Tool Library</h4>
        <div id="tw-library" class="text-muted small">Loading tools…</div>
      </div>
      <p class="text-muted small">Promoted code is trusted application code and will run in the Novous backend when an agent invokes it.</p>
    </section>`);

  const codeField = container.querySelector('#tw-code');
  const inputField = container.querySelector('#tw-input');
  const promptField = container.querySelector('#tw-prompt');
  const modelSelect = container.querySelector('#tw-model');
  const runButton = container.querySelector('#tw-run');
  const llmButton = container.querySelector('#tw-run-llm');
  const saveButton = container.querySelector('#tw-save');
  const promoteButton = container.querySelector('#tw-promote');
  const output = container.querySelector('#tw-output');
  const status = container.querySelector('#tw-status');
  const library = container.querySelector('#tw-library');

  const defaultCode = `def calculate_shipping(weight_kg: float, distance_km: float) -> dict:
    """Calculate shipping fee from package weight and distance."""
    base_rate = 5.0
    cost = base_rate + (weight_kg * 1.5) + (distance_km * 0.05)
    return {
        "weight_kg": weight_kg,
        "distance_km": distance_km,
        "shipping_cost": round(cost, 2)
    }`;
  const defaultInput = `{
  "weight_kg": 4.5,
  "distance_km": 120.0
}`;
  const defaultPrompt = 'Calculate shipping for a 4.5kg package traveling 120km using the shipping tool.';
  let lastPassed = null;
  let lastTestReport = null;
  let busy = false;

  codeField.value = defaultCode;
  inputField.value = defaultInput;
  promptField.value = defaultPrompt;

  function enableTabIndent(field) {
    field.addEventListener('keydown', event => {
      if (event.key !== 'Tab') return;
      event.preventDefault();
      const start = field.selectionStart;
      const end = field.selectionEnd;
      field.value = field.value.slice(0, start) + '    ' + field.value.slice(end);
      field.selectionStart = field.selectionEnd = start + 4;
    });
  }

  function createTestReport(result, context = {}) {
    return {
      tested_at: new Date().toISOString(),
      execution_mode: context.execution_mode || 'local-python',
      model_used: context.model_used || null,
      function_code: context.function_code ?? codeField.value,
      function_input: context.function_input ?? inputField.value,
      prompt: context.prompt ?? '',
      test_output: result
    };
  }

  function markdownCodeBlock(value, language = '') {
    const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    const longestFence = Math.max(2, ...((text.match(/`+/g) || []).map(run => run.length)));
    const fence = '`'.repeat(longestFence + 1);
    return `${fence}${language}\n${text}\n${fence}`;
  }

  function renderTestReport(report) {
    const testOutput = report.test_output || {};
    const execution = testOutput.tool_execution_result || testOutput;
    const passed = testOutput.status === 'SUCCESS';
    const fields = [
      `- **Result:** ${passed ? 'PASS' : 'FAIL'}`,
      `- **Tested at (UTC):** ${report.tested_at}`,
      `- **Execution mode:** ${report.execution_mode}`,
      `- **LLM used:** ${report.model_used || 'No — direct local Python test'}`,
      `- **Function:** ${execution.function_name || 'Not identified'}`,
      `- **Error code:** ${testOutput.error_code || execution.error_code || 'None'}`
    ];
    const sections = [
      '# Tool Function Test Report',
      '',
      ...fields,
      '',
      '## LLM Prompt',
      '',
      report.prompt ? markdownCodeBlock(report.prompt, 'text') : '_No LLM prompt was used._',
      '',
      '## Function Input',
      '',
      markdownCodeBlock(report.function_input, 'json'),
      '',
      '## Function Code',
      '',
      markdownCodeBlock(report.function_code, 'python'),
      '',
      '## Result',
      '',
      `**Status:** ${testOutput.status || 'ERROR'}`,
      ''
    ];

    if (execution.output !== undefined) {
      sections.push('### Function output', '', markdownCodeBlock(execution.output, 'json'), '');
    }
    if (testOutput.llm_text_response) {
      sections.push('### LLM response', '', markdownCodeBlock(testOutput.llm_text_response, 'text'), '');
    }
    if (testOutput.tool_calls_detected?.length) {
      sections.push(
        '### LLM tool calls',
        '',
        markdownCodeBlock(testOutput.tool_calls_detected, 'json'),
        ''
      );
    }
    if (testOutput.message) {
      sections.push('### Failure details', '', markdownCodeBlock(testOutput.message, 'text'), '');
    }
    for (const [label, value] of [
      ['Standard error', execution.stderr],
      ['Standard output', execution.stdout],
      ['Exit code', execution.exit_code]
    ]) {
      if (value !== undefined && value !== null && value !== '') {
        sections.push(`### ${label}`, '', markdownCodeBlock(value, 'text'), '');
      }
    }
    sections.push(
      '## Machine-readable JSON',
      '',
      'The complete report data is included below for reuse or automated processing.',
      '',
      markdownCodeBlock(report, 'json'),
      ''
    );
    return sections.join('\n');
  }

  function parseFunctionInput() {
    const parsed = JSON.parse(inputField.value || '{}');
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
      throw new Error('Function input must be a JSON object.');
    }
    return parsed;
  }

  function updatePromotion() {
    const unchangedSincePass = lastPassed &&
      lastPassed.code === codeField.value &&
      lastPassed.input === inputField.value;
    let hasValidInput = true;
    try {
      parseFunctionInput();
    } catch (_) {
      hasValidInput = false;
    }
    promoteButton.disabled = busy || !unchangedSincePass || !hasValidInput;
  }

  function showResult(result, reportContext) {
    output.textContent = JSON.stringify(result, null, 2);
    lastTestReport = createTestReport(result, reportContext);
    saveButton.disabled = false;
    const passed = result.status === 'SUCCESS';
    status.textContent = passed ? 'Test passed' : 'Test failed';
    status.className = passed ? 'text-success small' : 'text-danger small';
    lastPassed = passed
      ? { code: codeField.value, input: inputField.value }
      : null;
    updatePromotion();
  }

  async function loadModels() {
    modelSelect.replaceChildren(new Option('Loading models…', ''));
    try {
      const data = await Api.getModels();
      const models = data.models || [];
      modelSelect.replaceChildren();
      if (!models.length) {
        modelSelect.appendChild(new Option(data.error || 'No models found', ''));
        return;
      }
      models.forEach(model => modelSelect.appendChild(new Option(model, model)));
      modelSelect.value = models.includes(data.default) ? data.default : models[0];
    } catch (err) {
      modelSelect.replaceChildren(new Option(`Could not load models: ${err.message}`, ''));
    }
  }

  async function loadToolLibrary() {
    try {
      const data = await Api.getTools();
      const tools = data.tools || [];
      library.innerHTML = tools.length
        ? tools.map(tool => `<div class="tool-workbench-library-item"><code>${esc(tool.name)}</code> <span>${esc(tool.signature)}</span></div>`).join('')
        : 'No tools registered.';
    } catch (err) {
      library.textContent = `Could not load tools: ${err.message}`;
    }
  }

  async function runTest(useLlm) {
    let functionInput;
    if (!useLlm) {
      try {
        functionInput = parseFunctionInput();
      } catch (err) {
        lastPassed = null;
        output.textContent = JSON.stringify({
          status: 'ERROR',
          error_code: 'ERR_INVALID_JSON_INPUT',
          message: err.message
        }, null, 2);
        lastTestReport = createTestReport({
          status: 'ERROR',
          error_code: 'ERR_INVALID_JSON_INPUT',
          message: err.message
        });
        saveButton.disabled = false;
        status.textContent = 'Test failed';
        status.className = 'text-danger small';
        updatePromotion();
        return;
      }
    }
    if (useLlm && !modelSelect.value) {
      status.textContent = 'Select an installed model first.';
      status.className = 'text-danger small';
      return;
    }

    let reportInput;
    try {
      reportInput = parseFunctionInput();
    } catch (_) {
      reportInput = inputField.value;
    }
    const reportContext = {
      execution_mode: useLlm ? 'local-llm-tool-call' : 'local-python',
      model_used: useLlm ? modelSelect.value : null,
      function_code: codeField.value,
      function_input: reportInput,
      prompt: useLlm ? promptField.value : ''
    };
    busy = true;
    lastPassed = null;
    updatePromotion();
    runButton.disabled = true;
    llmButton.disabled = true;
    status.textContent = useLlm ? 'Requesting local model tool call…' : 'Running with local Python…';
    status.className = 'text-muted small';
    output.textContent = 'Test in progress…';
    try {
      const result = useLlm
        ? await Api.testToolWithLlm(modelSelect.value, codeField.value, promptField.value)
        : await Api.executeToolTest(codeField.value, functionInput);
      showResult(result, reportContext);
    } catch (err) {
      const result = {
        status: 'ERROR',
        error_code: 'ERR_TOOL_TEST_FAILED',
        message: err.message
      };
      output.textContent = JSON.stringify(result, null, 2);
      lastTestReport = createTestReport(result, reportContext);
      saveButton.disabled = false;
      status.textContent = 'Test failed';
      status.className = 'text-danger small';
    } finally {
      busy = false;
      runButton.disabled = false;
      llmButton.disabled = false;
      updatePromotion();
    }
  }

  runButton.addEventListener('click', () => runTest(false));
  llmButton.addEventListener('click', () => runTest(true));
  container.querySelector('#tw-refresh-models').addEventListener('click', loadModels);
  enableTabIndent(codeField);
  enableTabIndent(inputField);
  codeField.addEventListener('input', () => {
    lastPassed = null;
    updatePromotion();
  });
  inputField.addEventListener('input', () => {
    lastPassed = null;
    updatePromotion();
  });
  saveButton.addEventListener('click', async () => {
    if (!lastTestReport) return;
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    try {
      const saved = await Api.saveMarkdown(
        renderTestReport(lastTestReport),
        `novous-tool-test-${stamp}.md`
      );
      if (saved.locationChosen) {
        alert(`Test results saved as ${saved.filename}.`);
      } else {
        alert(`Test results download started: ${saved.filename}`);
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        alert(`Could not save test results: ${err.message}`);
      }
    }
  });
  promoteButton.addEventListener('click', async () => {
    if (!lastPassed || !confirm(
      'Add this tested function to the tool library? Promoted code runs as trusted code in the Novous backend.'
    )) return;

    try {
      busy = true;
      runButton.disabled = true;
      llmButton.disabled = true;
      updatePromotion();
      status.textContent = 'Verifying test and adding tool…';
      const result = await Api.promoteTestedTool(codeField.value, parseFunctionInput());
      output.textContent = JSON.stringify(result, null, 2);
      status.textContent = `Added ${result.promoted.name} to the tool library`;
      status.className = 'text-success small';
      lastPassed = null;
      await loadToolLibrary();
    } catch (err) {
      output.textContent = JSON.stringify({
        status: 'ERROR',
        error_code: 'ERR_TOOL_PROMOTION_FAILED',
        message: err.message
      }, null, 2);
      status.textContent = 'Could not add tool';
      status.className = 'text-danger small';
    } finally {
      busy = false;
      runButton.disabled = false;
      llmButton.disabled = false;
      updatePromotion();
    }
  });

  container.querySelector('#tw-reset').addEventListener('click', () => {
    codeField.value = defaultCode;
    inputField.value = defaultInput;
    promptField.value = defaultPrompt;
    output.textContent = 'Run a test to see its result.';
    status.textContent = 'Ready';
    status.className = 'text-muted small';
    lastPassed = null;
    lastTestReport = null;
    saveButton.disabled = true;
    updatePromotion();
  });

  loadModels();
  loadToolLibrary();
}
