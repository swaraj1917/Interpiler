# Interpiler 🎓

> **A learning tool for beginners** — write rough code, see how it runs, and understand what a compiler and interpreter actually do behind the scenes.

---

## What is Interpiler?

Interpiler is built for people **new to coding** who want to:

1. **Write code freely** — even rough or imperfect code is accepted
2. **See errors in plain English** — no cryptic messages, just friendly explanations and tips
3. **Watch the pipeline live** — see each stage (Lexer → Parser → AST Builder → Interpreter) activate in real time with a description of what it's doing
4. **Understand what's happening under the hood** — a visual step-by-step breakdown of how a compiler and interpreter process your code

It uses a simple custom language so beginners aren't overwhelmed by the complexity of real languages — just the core concepts.

---

## How It Works — The Pipeline

When you click **Run**, your code passes through 4 stages, each shown visually:

```
Your Code
   ↓
🔡 LEXER          — Breaks text into tokens (keywords, names, numbers, operators)
   ↓
🌳 PARSER         — Checks grammar, builds a Parse Tree
   ↓
🏗️ AST BUILDER    — Simplifies the tree into an Abstract Syntax Tree
   ↓
⚙️ INTERPRETER    — Walks the AST and executes each instruction
   ↓
Output + Memory snapshot
```

Each stage lights up green (✔ success) or red (✘ failed) with a plain-English explanation of what happened.

---

## Features

- ✅ **Step-by-step pipeline visualizer** — watch the Lexer, Parser, AST Builder, and Interpreter work live
- ✅ **Beginner-friendly error messages** — errors explained in plain English, not compiler jargon
- ✅ **Smart suggestions** — pattern-based tips for common beginner mistakes
- ✅ **Memory viewer** — see all your variables and their values after execution
- ✅ **AST viewer** — see the actual tree your code was turned into
- ✅ **Web IDE** — clean dark editor with line numbers, cursor tracking, Tab support
- ✅ **Desktop GUI** — Tkinter app with syntax highlighting
- ✅ **Terminal REPL** — run code directly from the terminal

---

## The Language

Interpiler uses a simple C-style language:

```
// Variables
x = 10
name = "Alice"

// Print
print x

// If / Else
if (x > 5) {
    print x
} else {
    print 0
}

// While loop
i = 0
while (i < 5) {
    i = i + 1
    print i
}

// For loop
for (i = 0; i < 5; i = i + 1) {
    print i
}

// Arithmetic: + - * / %
// Comparators: == != < <= > >=
// Logical: and or not
```

---

## Project Structure

```
interpiler/
├── app.py                  # Flask web server & API
├── interpreter.py          # Core pipeline: parse → AST → execute → feedback
├── interpreter_engine.py   # Grammar (Lark), AST builder, executor
├── interpiler_gui.py       # Tkinter desktop GUI
│
├── templates/
│   └── index.html          # Web IDE: editor + pipeline + results
│
├── static/
│   ├── style.css           # Dark educational UI theme
│   └── script.js           # Pipeline visualizer, tab switcher, editor logic
│
├── requirements.txt
└── README.md
```

---

## Getting Started

### Install

```bash
pip install -r requirements.txt
```

### Run the Web IDE

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000)

### Run the Desktop App

```bash
python interpiler_gui.py
```

### Run in Terminal

```bash
python interpreter.py
```

---

## Requirements

```
flask>=3.0
lark>=1.1
```

---

## Who Is This For?

- Students learning about **how programming languages work**
- Beginners who want to understand **what a compiler vs interpreter actually does**
- Teachers who want a visual, interactive tool to explain **the compiler pipeline**
- Anyone curious about **lexers, parsers, and ASTs** without reading a textbook

---

## License

MIT — free to use, modify, and share.