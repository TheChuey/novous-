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
}
