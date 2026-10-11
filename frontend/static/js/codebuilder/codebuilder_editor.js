const MONACO_VS_PATH = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs';
let monacoPromise;

export function loadMonaco() {
  if (window.monaco?.editor) return Promise.resolve(window.monaco);
  if (monacoPromise) return monacoPromise;

  monacoPromise = new Promise((resolve, reject) => {
    if (typeof window.require !== 'function') {
      reject(new Error('The Monaco Editor loader is unavailable.'));
      return;
    }

    window.require.config({ paths: { vs: MONACO_VS_PATH } });
    window.require(['vs/editor/editor.main'], () => {
      if (!window.monaco?.editor) {
        reject(new Error('Monaco Editor failed to initialize.'));
        return;
      }
      resolve(window.monaco);
    }, reject);
  });
  return monacoPromise;
}

function createTextareaEditor(element, initialValue) {
  const textarea = document.createElement('textarea');
  textarea.className = 'codebuilder-textarea';
  textarea.value = initialValue;
  textarea.setAttribute('aria-label', 'Python source code');
  element.replaceChildren(textarea);
  let runHandler = null;
  let changeHandler = null;
  textarea.addEventListener('input', () => changeHandler?.());
  textarea.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      runHandler?.();
    }
  });

  return {
    getValue: () => textarea.value,
    setValue: (value) => { textarea.value = value; changeHandler?.(); },
    setDiagnostics: () => {},
    setRunHandler: (handler) => { runHandler = handler; },
    onChange: (handler) => { changeHandler = handler; },
    revealLine: (line) => {
      const lineStart = textarea.value.split('\n').slice(0, Math.max(0, line - 1)).join('\n').length;
      textarea.focus();
      textarea.setSelectionRange(lineStart, lineStart);
    },
    focus: () => textarea.focus(),
    dispose: () => textarea.remove(),
  };
}

export async function attachCodeBuilderEditor(element, initialValue = "print('Hello from Novous CodeBuilder!')\n") {
  if (!element) {
    throw new Error('The CodeBuilder editor container was not found.');
  }

  try {
    const monaco = await loadMonaco();
    const editor = monaco.editor.create(element, {
      value: initialValue,
      language: 'python',
      theme: 'vs-dark',
      automaticLayout: true,
      ariaLabel: 'Python code editor',
      accessibilitySupport: 'auto',
      bracketPairColorization: { enabled: true },
      cursorBlinking: 'smooth',
      detectIndentation: false,
      folding: true,
      fontSize: 14,
      fontFamily: "'Cascadia Code', 'Fira Code', Consolas, monospace",
      fontLigatures: true,
      formatOnPaste: true,
      guides: { bracketPairs: true, indentation: true },
      lineNumbers: 'on',
      minimap: { enabled: true, scale: 0.8 },
      padding: { top: 12, bottom: 12 },
      renderLineHighlight: 'all',
      scrollBeyondLastLine: false,
      smoothScrolling: true,
      stickyScroll: { enabled: true },
      tabSize: 4,
      insertSpaces: true,
      wordWrap: 'off',
    });
    let runHandler = null;
    let changeHandler = null;
    editor.onDidChangeModelContent(() => changeHandler?.());
    editor.addAction({
      id: 'codebuilder.runPython',
      label: 'Run Python',
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
      run: () => runHandler?.(),
    });

    return {
      getValue: () => editor.getValue(),
      setValue: (value) => { editor.setValue(value); },
      focus: () => editor.focus(),
      setRunHandler: (handler) => { runHandler = handler; },
      onChange: (handler) => { changeHandler = handler; },
      revealLine: (line) => {
        editor.revealLineInCenter(line);
        editor.setPosition({ lineNumber: line, column: 1 });
        editor.focus();
      },
      setDiagnostics: (items) => {
        const model = editor.getModel();
        if (!model) return;
        monaco.editor.setModelMarkers(model, 'codebuilder', items.map(item => ({
          severity: item.severity === 'warning'
            ? monaco.MarkerSeverity.Warning
            : item.severity === 'info'
              ? monaco.MarkerSeverity.Info
              : monaco.MarkerSeverity.Error,
          message: item.message,
          startLineNumber: item.line || 1,
          endLineNumber: item.line || 1,
          startColumn: item.column || 1,
          endColumn: (item.column || 1) + 1,
        })));
      },
      dispose: () => editor.dispose(),
    };
  } catch (error) {
    console.error('Monaco Editor could not be loaded; using the basic Python editor instead.', error);
    return createTextareaEditor(element, initialValue);
  }
}
