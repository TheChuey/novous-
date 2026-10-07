/* Agent creation and current workspace-agent selection for the editor. */
import API from './api.js';

const state = {
  jsonPath: null,   // run-agent target (workspace-relative)
  mdPath: null,
  ctx: null
};

const $ = (id) => document.getElementById(id);

export function initAgentsPanel(ctx) {
  state.ctx = ctx;

  // + Agent scaffold
  $('agentCreateBtn')?.addEventListener('click', scaffoldAgent);

  // Single-agent runs happen on the dashboard; the open definition is
  // saved first and passed as a selection hint when available.
  $('runAgentBtn')?.addEventListener('click', async () => {
    if (state.jsonPath && state.ctx?.isDirty()) await state.ctx.saveFile();
    const agentId = state.jsonPath
      ? state.jsonPath.split('/')[1]
      : null;
    window.location.href = agentId
      ? `/?agent=${encodeURIComponent(agentId)}`
      : '/';
  });

  $('pipelineBtn')?.addEventListener('click', () => {
    window.location.href = '/?panel=orchestrator';
  });

  updateRunTarget();
}

/* ------------------------------------------------------------
   Current agent selection for the dashboard runner
   ------------------------------------------------------------ */
function updateRunTarget() {
  const cf = state.ctx ? state.ctx.getCurrentFile() : null;
  if (!cf) {
    state.jsonPath = state.mdPath = null;
    return;
  }
  const m = /^workspace\/agents\/([^/]+)\/(agent\.json|agent\.md)$/.exec(cf);
  if (m) {
    /* The agent-run API takes workspace-relative paths, so these
       stay unprefixed even though the open file is root-qualified. */
    state.jsonPath = `agents/${m[1]}/agent.json`;
    state.mdPath = `agents/${m[1]}/agent.md`;
  } else {
    state.jsonPath = state.mdPath = null;
  }
}

/* ------------------------------------------------------------
   Scaffold a new workspace agent
   ------------------------------------------------------------ */
async function scaffoldAgent() {
  const name = prompt('Agent id / folder name (e.g. "doc_writer"):');
  if (!name) return;
  if (!/^[A-Za-z0-9_\-]+$/.test(name)) {
    alert('Use only letters, numbers, underscore or dash.');
    return;
  }
  /* The tree/editor use root-qualified paths; the agent-run API
     uses workspace-relative ones. */
  const rel = `agents/${name}`;
  const full = `workspace/${rel}`;
  const json = JSON.stringify({
    id: name,
    name: name.replace(/[_-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    description: 'A custom agent scaffolded from the editor.',
    mode: 'agent',
    model: '',
    tools: ['map_files', 'read_file', 'write_text_file']
  }, null, 2);
  const md =
    `# ${name}\n` +
    `\n## role\n` +
    `\nYou are ${name}, a helpful Project Manager agent.\n` +
    `\n## purpose\n` +
    `\nDescribe what this agent accomplishes and when it is used.\n` +
    `\n## boundaries\n` +
    `\nState what this agent will not do.\n` +
    `\n## output format\n` +
    `\nDescribe the shape of the reply the agent must produce.\n`;
  try {
    await API.fileCreate(`${full}/agent.json`, json);
    await API.fileCreate(`${full}/agent.md`, md);
    if (state.ctx) {
      await state.ctx.refreshTree();
      await state.ctx.openFile(`${full}/agent.json`);
    }
  } catch (e) {
    alert('Failed to scaffold agent: ' + e.message);
  }
}

export { updateRunTarget };