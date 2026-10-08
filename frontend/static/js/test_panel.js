const TEST_FUNCTIONS = [
  { id: 'runTestSuite', label: 'Run Test Suite', icon: 'play-circle', action: null },
  { id: 'debugAgent', label: 'Debug Agent', icon: 'bug', action: null },
  { id: 'promptInspector', label: 'Prompt Inspector', icon: 'terminal', action: null },
  { id: 'outputEvaluator', label: 'Output Evaluator', icon: 'check-square', action: null },
  { id: 'benchmark', label: 'Benchmark', icon: 'gauge', action: null },
  { id: 'apiLogs', label: 'API Logs', icon: 'file-code', action: null },
  { id: 'diagnostics', label: 'Diagnostics', icon: 'activity', action: null },
  { id: 'wipeChat', label: 'Wipe Chat', icon: 'trash-2', action: null }
];

export function buildTestPanel(containerId, actions = {}) {
  const container = typeof containerId === 'string'
    ? document.getElementById(containerId)
    : containerId;

  if (!container) {
    console.error('Test panel container not found:', containerId);
    return;
  }

  container.replaceChildren();

  TEST_FUNCTIONS.forEach((test) => {
    const action = actions[test.id] || test.action;
    const button = document.createElement('button');
    const icon = document.createElement('i');
    const label = document.createElement('span');

    button.className = 'test-function';
    button.type = 'button';
    button.dataset.testFunction = test.id;
    icon.setAttribute('data-lucide', test.icon);
    label.textContent = test.label;
    button.append(icon, label);

    if (typeof action !== 'function') {
      button.classList.add('disabled');
      button.disabled = true;
      button.title = 'Not implemented yet';
    } else {
      button.title = test.label;
      button.addEventListener('click', action);
    }

    container.appendChild(button);
  });

  const todoSection = document.createElement('div');
  todoSection.className = 'todo-selector-section';

  const todoLabel = document.createElement('label');
  todoLabel.className = 'model-picker-label small text-muted';
  todoLabel.htmlFor = 'todo-file-select';
  todoLabel.textContent = 'Select To-Do File';

  const todoSelect = document.createElement('select');
  todoSelect.id = 'todo-file-select';
  todoSelect.className = 'form-select';
  todoSelect.setAttribute('aria-label', 'Select a To-Do file');

  const refreshTodoFiles = document.createElement('button');
  refreshTodoFiles.id = 'todo-file-refresh';
  refreshTodoFiles.className = 'btn btn-sm';
  refreshTodoFiles.type = 'button';
  refreshTodoFiles.textContent = 'Refresh lists';
  refreshTodoFiles.title = 'Refresh Markdown to-do lists';

  const loadingOption = document.createElement('option');
  loadingOption.value = '';
  loadingOption.textContent = 'Loading Markdown lists...';
  todoSelect.appendChild(loadingOption);

  todoSection.append(todoLabel, todoSelect, refreshTodoFiles);
  container.appendChild(todoSection);

  if (typeof globalThis.lucide?.createIcons === 'function') {
    globalThis.lucide.createIcons();
  }
}
