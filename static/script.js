'use strict';

// ── DOM ─────────────────────────────────────────────────────────────
const codeInput   = document.getElementById('codeInput');
const lineNums    = document.getElementById('lineNums');
const cursorInfo  = document.getElementById('cursorInfo');
const runBtn      = document.getElementById('runBtn');
const clearBtn    = document.getElementById('clearBtn');
const exampleBtn  = document.getElementById('exampleBtn');
const helpBtn     = document.getElementById('helpBtn');
const helpBanner  = document.getElementById('helpBanner');
const helpClose   = document.getElementById('helpClose');
const pipelineBody= document.getElementById('pipelineBody');
const outputBox   = document.getElementById('outputBox');
const errorsBox   = document.getElementById('errorsBox');
const memoryBox   = document.getElementById('memoryBox');
const astBox      = document.getElementById('astBox');
const tabs        = document.querySelectorAll('.tab');

// ── Pipeline educational descriptions (fallback if backend doesn't provide) ──
const STAGE_EDU = {
  "Lexer":       "The <strong>Lexer</strong> reads your text character by character and groups them into meaningful chunks called <em>tokens</em> — like words and punctuation in a sentence.",
  "Parser":      "The <strong>Parser</strong> checks if your tokens follow the grammar rules — like checking if a sentence has a subject and verb. It builds a <em>Parse Tree</em> showing the structure.",
  "AST Builder": "The <strong>AST Builder</strong> cleans up the Parse Tree into a simpler <em>Abstract Syntax Tree</em> — a tree of actions your program needs to perform.",
  "Interpreter": "The <strong>Interpreter</strong> walks through the AST node by node and actually <em>executes</em> each instruction, storing variables in memory and producing output.",
};

// ── Example code ─────────────────────────────────────────────────────
const EXAMPLE = `x = 1
total = 0

for (i = 1; i <= 5; i = i + 1) {
    total = total + i
}

print total

if (total > 10) {
    print total
} else {
    print 0
}`;

// ── Line numbers ──────────────────────────────────────────────────────
function updateLineNums() {
  const count = codeInput.value.split('\n').length;
  lineNums.textContent = Array.from({length: count}, (_, i) => i + 1).join('\n');
  lineNums.scrollTop = codeInput.scrollTop;
}
codeInput.addEventListener('input',  updateLineNums);
codeInput.addEventListener('scroll', () => { lineNums.scrollTop = codeInput.scrollTop; });

// ── Cursor pos ────────────────────────────────────────────────────────
function updateCursor() {
  const txt  = codeInput.value.substring(0, codeInput.selectionStart);
  const line = txt.split('\n').length;
  const col  = txt.split('\n').pop().length + 1;
  cursorInfo.textContent = `Ln ${line}, Col ${col}`;
}
codeInput.addEventListener('keyup',   updateCursor);
codeInput.addEventListener('mouseup', updateCursor);

// ── Tab key ───────────────────────────────────────────────────────────
codeInput.addEventListener('keydown', e => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const s = codeInput.selectionStart;
    codeInput.value = codeInput.value.slice(0, s) + '    ' + codeInput.value.slice(codeInput.selectionEnd);
    codeInput.selectionStart = codeInput.selectionEnd = s + 4;
    updateLineNums();
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); runCode(); }
});

// ── Tab switcher ──────────────────────────────────────────────────────
tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
  });
});

function switchTab(name) {
  tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.tab-panel').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${name}`);
  });
}

// ── Pipeline renderer (updated to show dynamic educational messages) ──
function renderPipeline(steps) {
  pipelineBody.innerHTML = '';
  steps.forEach((step, idx) => {
    // Connector line between steps
    if (idx > 0) {
      const conn = document.createElement('div');
      conn.className = 'step-connector' + (
        steps[idx-1].status === 'ok' ? ' done' :
        steps[idx-1].status === 'error' ? ' error' : ''
      );
      pipelineBody.appendChild(conn);
    }

    const card = document.createElement('div');
    card.className = `step-card status-${step.status}`;

    const tagClass = step.status === 'ok' ? 'tag-ok' :
                     step.status === 'error' ? 'tag-error' : 'tag-running';
    const tagLabel = step.status === 'ok' ? '✔ Done' :
                     step.status === 'error' ? '✘ Failed' : '⟳ Running';

    // Use educational message from backend if available, otherwise use fallback
    let eduMessage = '';
    if (step.educational) {
      eduMessage = `<div class="step-edu">💡 ${escapeHtml(step.educational)}</div>`;
    } else if (STAGE_EDU[step.phase]) {
      eduMessage = `<div class="step-edu">${STAGE_EDU[step.phase]}</div>`;
    }

    // Add extra context for errors
    let errorContext = '';
    if (step.status === 'error' && step.detail) {
      errorContext = `<div class="step-error-hint" style="margin-top:8px;padding:6px 10px;background:rgba(240,84,106,0.1);border-radius:6px;font-size:11px;color:var(--red);">
                        ⚠️ ${escapeHtml(step.detail.substring(0, 150))}
                      </div>`;
    }

    card.innerHTML = `
      <div class="step-head">
        <span class="step-icon">${escapeHtml(step.icon)}</span>
        <span class="step-phase">${escapeHtml(step.phase)}</span>
        <span class="step-status-tag ${tagClass}">${tagLabel}</span>
      </div>
      <div class="step-detail">${escapeHtml(step.detail)}</div>
      ${eduMessage}
      ${errorContext}
    `;
    pipelineBody.appendChild(card);
  });
}

// ── Errors & suggestions renderer (updated) ─────────────────────────
function renderErrors(errors, suggestions) {
  errorsBox.innerHTML = '';
  let count = 0;

  errors.forEach(err => {
    count++;
    const card = document.createElement('div');
    card.className = 'error-card is-error';
    card.innerHTML = `
      <div class="error-label label-error">❌ Error — ${escapeHtml(err.phase)}</div>
      <div class="error-friendly">${escapeHtml(err.friendly)}</div>
      <details>
        <summary class="error-phase" style="cursor:pointer;font-size:11px;color:var(--fg-dim)">Show raw error</summary>
        <div class="error-raw">${escapeHtml(err.raw)}</div>
      </details>
    `;
    errorsBox.appendChild(card);
  });

  suggestions.forEach(s => {
    count++;
    const card = document.createElement('div');
    card.className = 'error-card is-tip';
    card.innerHTML = `
      <div class="error-label label-tip">💡 Tip — ${escapeHtml(s.tag)}</div>
      <div class="error-friendly">${escapeHtml(s.msg)}</div>
    `;
    errorsBox.appendChild(card);
  });

  if (count === 0) {
    errorsBox.innerHTML = '<span class="placeholder-text" style="color:var(--green)">✔ No errors found! Great job.</span>';
  }
}

// ── Memory renderer ───────────────────────────────────────────────────
function renderMemory(symtable) {
  memoryBox.innerHTML = '';
  const keys = Object.keys(symtable);
  if (keys.length === 0) {
    memoryBox.innerHTML = '<span class="mem-empty">No variables were created.</span>';
    return;
  }
  keys.forEach(k => {
    const row = document.createElement('div');
    row.className = 'memory-row';
    row.innerHTML = `<span class="mem-name">${escapeHtml(k)}</span><span class="mem-val">${escapeHtml(String(symtable[k]))}</span>`;
    memoryBox.appendChild(row);
  });
}

// ── AST renderer (improved) ─────────────────────────────────────────
function astToText(node, indent = 0) {
  const pad = '  '.repeat(indent);
  if (!node) return '';
  if (node.type === 'node') {
    const children = (node.children || []).map(c => astToText(c, indent + 1)).join('');
    return `${pad}[${node.name}]\n${children}`;
  }
  if (node.type === 'token')   return `${pad}${node.name}: ${node.value}\n`;
  if (node.type === 'literal') return `${pad}${node.value}\n`;
  if (node.type === 'tuple') {
    const children = (node.children || []).map(c => astToText(c, indent + 1)).join('');
    return `${pad}(${node.op})\n${children}`;
  }
  return '';
}

// ── Main run (updated with better error handling) ────────────────────
async function runCode() {
  const code = codeInput.value.trim();
  if (!code) {
    pipelineBody.innerHTML = '<div class="pipeline-idle"><div class="idle-icon">⚠️</div><p>Please write some code first!</p></div>';
    return;
  }

  runBtn.disabled = true;
  pipelineBody.innerHTML = '<div class="pipeline-idle"><div class="idle-icon" style="animation:spin 1s linear infinite;display:inline-block">⚙️</div><p>Processing…</p></div>';
  outputBox.textContent = '// Running…';
  outputBox.classList.remove('has-error');

  try {
    const res  = await fetch('/interpret', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({code})
    });
    const data = await res.json();

    // Pipeline - render with dynamic educational messages
    if (data.steps && data.steps.length) {
      renderPipeline(data.steps);
    } else {
      pipelineBody.innerHTML = '<div class="pipeline-idle"><div class="idle-icon">🔍</div><p>No pipeline steps returned from server.</p></div>';
    }

    // Output
    const hasError = data.errors && data.errors.length > 0;
    if (hasError && !data.output) {
      outputBox.textContent = '// Program did not produce output due to errors.\n// Check the "Errors & Tips" tab.';
      outputBox.classList.add('has-error');
      switchTab('errors');
    } else {
      outputBox.textContent = data.output || '// (no output)';
      outputBox.classList.remove('has-error');
      // Only switch to output tab if there are no errors
      if (!hasError) switchTab('output');
    }

    // Errors & tips
    renderErrors(data.errors || [], data.suggestions || []);

    // Memory
    renderMemory(data.symbol_table || {});

    // AST
    if (data.ast) {
      astBox.textContent = astToText(data.ast);
    } else {
      astBox.innerHTML = '<span class="placeholder-text">AST not available (likely a parse error).</span>';
    }

    // Auto-switch to errors tab if there are errors
    if (hasError && data.errors.length > 0) switchTab('errors');

  } catch (err) {
    console.error('Fetch error:', err);
    pipelineBody.innerHTML = `<div class="pipeline-idle"><div class="idle-icon">❌</div><p>Could not reach the server: ${escapeHtml(err.message)}</p></div>`;
    outputBox.textContent = 'Network error. Make sure the Flask server is running.';
    outputBox.classList.add('has-error');
  } finally {
    runBtn.disabled = false;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ── Button wiring ─────────────────────────────────────────────────────
runBtn.addEventListener('click', runCode);

clearBtn.addEventListener('click', () => {
  codeInput.value = '';
  updateLineNums(); 
  updateCursor();
  pipelineBody.innerHTML = '<div class="pipeline-idle"><div class="idle-icon">🔍</div><p>Run your code to see how it flows through the compiler and interpreter — step by step.</p></div>';
  outputBox.textContent = '// Your program output appears here';
  outputBox.classList.remove('has-error');
  errorsBox.innerHTML = '<span class="placeholder-text">No errors yet — run your code!</span>';
  memoryBox.innerHTML = '<span class="placeholder-text">Variable values will appear here after running.</span>';
  astBox.innerHTML = '<span class="placeholder-text">AST will appear here after running.</span>';
});

exampleBtn.addEventListener('click', () => {
  codeInput.value = EXAMPLE;
  updateLineNums(); 
  updateCursor();
  codeInput.focus();
});

helpBtn.addEventListener('click', () => helpBanner.classList.toggle('hidden'));
helpClose.addEventListener('click', () => helpBanner.classList.add('hidden'));

// ── Init ──────────────────────────────────────────────────────────────
updateLineNums();
updateCursor();

// Spin animation for loading
const style = document.createElement('style');
style.textContent = '@keyframes spin{to{transform:rotate(360deg)}}';
document.head.appendChild(style);

// Optional: Add keyboard shortcut hint
console.log('Interpiler ready! Press Ctrl+Enter to run code.');