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
  let saveHandler = null;
  let changeHandler = null;
  let positionHandler = null;
  textarea.addEventListener('input', () => changeHandler?.());
  textarea.addEventListener('keyup', () => positionHandler?.());
  textarea.addEventListener('click', () => positionHandler?.());
  textarea.addEventListener('keydown', event => {
    if (event.ctrlKey || event.metaKey) {
      if (event.key === 'Enter') {
        event.preventDefault();
        runHandler?.();
      } else if (event.key.toLowerCase() === 's' && saveHandler) {
        event.preventDefault();
        saveHandler?.();
      }
    }
  });

  return {
    getValue: () => textarea.value,
    setValue: (value) => { textarea.value = value; changeHandler?.(); },
    setLanguage: () => {},
    getPosition: () => {
      const lines = textarea.value.slice(0, textarea.selectionStart).split('\n');
      return { lineNumber: lines.length, column: lines[lines.length - 1].length + 1 };
    },
    setDiagnostics: () => {},
    setHighlightedLines: (lines) => {
      if (!Array.isArray(lines) || !lines.length) return;
      const sourceLines = textarea.value.split('\n');
      const targetLine = Math.max(1, Math.min(lines[0], sourceLines.length));
      const lineStart = sourceLines.slice(0, targetLine - 1).join('\n').length
        + (targetLine > 1 ? 1 : 0);
      const lineEnd = lineStart + sourceLines[targetLine - 1].length;
      textarea.focus();
      textarea.setSelectionRange(lineStart, lineEnd);
    },
    setChangeView: () => {},
    setRunHandler: (handler) => { runHandler = handler; },
    setSaveHandler: (handler) => { saveHandler = handler; },
    onChange: (handler) => { changeHandler = handler; },
    onPosition: (handler) => { positionHandler = handler; },
    revealLine: (line) => {
      const lineStart = textarea.value.split('\n').slice(0, Math.max(0, line - 1)).join('\n').length;
      textarea.focus();
      textarea.setSelectionRange(lineStart, lineStart);
    },
    focus: () => textarea.focus(),
    setReadOnly: (readOnly) => { textarea.readOnly = !!readOnly; },
    revealEnd: () => { textarea.scrollTop = textarea.scrollHeight; },
    dispose: () => textarea.remove(),
  };
}

export async function attachCodeBuilderEditor(
  element,
  initialValue = "print('Hello from Novous CodeBuilder!')\n",
  language = 'python'
) {
  if (!element) {
    throw new Error('The CodeBuilder editor container was not found.');
  }

  try {
    const monaco = await loadMonaco();
    const editor = monaco.editor.create(element, {
      value: initialValue,
      language,
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
      glyphMargin: true,
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
    let saveHandler = null;
    let changeHandler = null;
    let positionHandler = null;
    editor.onDidChangeModelContent(() => changeHandler?.());
    editor.onDidChangeCursorPosition(() => positionHandler?.());
    editor.addAction({
      id: 'codebuilder.runPython',
      label: 'Run Python',
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
      run: () => runHandler?.(),
    });
    let saveAction = null;
    let highlightDecorations = [];

    return {
      getValue: () => editor.getValue(),
      setValue: (value) => { editor.setValue(value); },
      setLanguage: (nextLanguage) => {
        const model = editor.getModel();
        if (model) monaco.editor.setModelLanguage(model, nextLanguage);
      },
      getPosition: () => editor.getPosition(),
      focus: () => editor.focus(),
      setRunHandler: (handler) => { runHandler = handler; },
      setSaveHandler: (handler) => {
        saveAction?.dispose();
        saveHandler = handler;
        if (handler) {
          saveAction = editor.addAction({
            id: 'codebuilder.save',
            label: 'Save',
            keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS],
            run: () => saveHandler?.(),
          });
        }
      },
      onChange: (handler) => { changeHandler = handler; },
      onPosition: (handler) => { positionHandler = handler; },
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
      setHighlightedLines: (lines, kind = 'preview') => {
        const applied = kind === 'applied';
        const error = kind === 'error';
        highlightDecorations = editor.deltaDecorations(
          highlightDecorations,
          (Array.isArray(lines) ? lines : [])
            .filter(line => Number.isInteger(line) && line > 0)
            .map(line => ({
              range: new monaco.Range(line, 1, line, 1),
              options: {
                isWholeLine: true,
                className: applied
                  ? 'code-change-applied-line'
                  : error
                    ? 'code-change-error-line'
                    : 'code-change-preview-line',
                glyphMarginClassName: applied
                  ? 'code-change-applied-glyph'
                  : error
                    ? 'code-change-error-glyph'
                    : 'code-change-preview-glyph',
                overviewRuler: {
                  color: applied ? '#22c55e' : error ? '#ef4444' : '#facc15',
                  position: monaco.editor.OverviewRulerLane.Right
                }
              }
            }))
        );
        if (lines?.length) editor.revealLineInCenter(lines[0]);
      },
      setChangeView: (lines, compact = true) => {
        const model = editor.getModel();
        if (typeof editor.setHiddenAreas !== 'function' || !model) return;
        if (!compact || !Array.isArray(lines) || !lines.length) {
          editor.setHiddenAreas([]);
          return;
        }
        const visible = new Set();
        lines.forEach(line => {
          for (let current = Math.max(1, line - 2); current <= line + 2; current += 1) {
            if (current <= model.getLineCount()) visible.add(current);
          }
        });
        const hidden = [];
        let start = null;
        for (let line = 1; line <= model.getLineCount() + 1; line += 1) {
          if (line <= model.getLineCount() && !visible.has(line)) {
            if (start === null) start = line;
          } else if (start !== null) {
            hidden.push(new monaco.Range(start, 1, line - 1, 1));
            start = null;
          }
        }
        editor.setHiddenAreas(hidden);
      },
      setReadOnly: (readOnly) => editor.updateOptions({ readOnly: !!readOnly }),
      revealEnd: () => {
        const model = editor.getModel();
        if (model) editor.revealLine(model.getLineCount());
      },
      dispose: () => editor.dispose(),
    };
  } catch (error) {
    console.error('Monaco Editor could not be loaded; using the basic Python editor instead.', error);
    return createTextareaEditor(element, initialValue);
  }
}
