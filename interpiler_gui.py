"""
interpiler_gui.py — Tkinter desktop GUI for Interpiler.
Run:  python interpiler_gui.py
"""

import sys
import io
import tkinter as tk
from tkinter import scrolledtext, messagebox, font as tkfont
from interpreter_engine import parser, ASTBuilder, interpret_terminal

# ─── Palette ─────────────────────────────────────────────────────────────────
BG        = "#1e1e2e"
PANEL_BG  = "#181825"
ACCENT    = "#00ffd0"
RED       = "#f38ba8"
YELLOW    = "#f9e2af"
GREEN     = "#a6e3a1"
SUBTEXT   = "#6c7086"
FG        = "#cdd6f4"
MONO      = ("Cascadia Code", 12) if "Cascadia Code" in tkfont.families() \
            else ("Courier New", 12)


# ─── Helpers ─────────────────────────────────────────────────────────────────
KEYWORDS = {"if", "else", "while", "for", "print", "and", "or", "not"}

def highlight_syntax(text_widget: tk.Text):
    """Very lightweight keyword + number highlighter."""
    text_widget.tag_remove("kw",  "1.0", tk.END)
    text_widget.tag_remove("num", "1.0", tk.END)
    content = text_widget.get("1.0", tk.END)
    import re
    for m in re.finditer(r'\b(' + '|'.join(KEYWORDS) + r')\b', content):
        start = f"1.0 + {m.start()} chars"
        end   = f"1.0 + {m.end()} chars"
        text_widget.tag_add("kw", start, end)
    for m in re.finditer(r'\b\d+(\.\d+)?\b', content):
        start = f"1.0 + {m.start()} chars"
        end   = f"1.0 + {m.end()} chars"
        text_widget.tag_add("num", start, end)


def append_log(text_widget: tk.Text, msg: str, tag: str = "info"):
    text_widget.config(state="normal")
    text_widget.insert(tk.END, msg + "\n", tag)
    text_widget.see(tk.END)
    text_widget.config(state="disabled")


def clear_widget(text_widget: tk.Text):
    text_widget.config(state="normal")
    text_widget.delete("1.0", tk.END)
    text_widget.config(state="disabled")


# ─── Core logic ───────────────────────────────────────────────────────────────
def run_code():
    code = code_input.get("1.0", tk.END).strip()
    if not code:
        messagebox.showinfo("Interpiler", "Please enter some code first.")
        return

    clear_widget(log_box)
    clear_widget(output_box)

    append_log(log_box, "● Lexing & parsing…", "info")
    root.update_idletasks()

    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()

    try:
        tree = parser.parse(code)
        append_log(log_box, "✔ Parse tree built", "ok")
        tree = ASTBuilder().transform(tree)
        append_log(log_box, "✔ AST constructed", "ok")
        append_log(log_box, "● Running interpreter…", "info")
        root.update_idletasks()

        interpret_terminal(tree)
        sys.stdout = old_stdout

        output = buf.getvalue()
        output_box.config(state="normal")
        output_box.insert(tk.END, output or "(no output)")
        output_box.config(state="disabled")
        append_log(log_box, "✔ Execution complete", "ok")

    except Exception as e:
        sys.stdout = old_stdout
        append_log(log_box, f"✘ Error: {e}", "err")
        messagebox.showerror("Runtime Error", str(e))


def clear_all():
    code_input.delete("1.0", tk.END)
    clear_widget(output_box)
    clear_widget(log_box)


def on_key(event=None):
    root.after(200, lambda: highlight_syntax(code_input))


# ─── Build GUI ────────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Interpiler")
root.geometry("1000x620")
root.configure(bg=BG)
root.resizable(True, True)

# Top bar
top_bar = tk.Frame(root, bg=PANEL_BG, height=44)
top_bar.pack(fill="x")
tk.Label(top_bar, text="  INTERPILER", bg=PANEL_BG, fg=ACCENT,
         font=("Arial", 13, "bold")).pack(side="left", pady=8)
tk.Label(top_bar, text="— hybrid compiler & interpreter",
         bg=PANEL_BG, fg=SUBTEXT, font=("Arial", 10)).pack(side="left")

# Main area
main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=10, pady=(6, 10))
main.columnconfigure(0, weight=3)
main.columnconfigure(1, weight=2)
main.rowconfigure(1, weight=1)

# Left: editor
tk.Label(main, text="Source Code", bg=BG, fg=ACCENT,
         font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0,3))
code_input = scrolledtext.ScrolledText(
    main, font=MONO, bg=PANEL_BG, fg=FG,
    insertbackground=ACCENT, relief="flat",
    selectbackground="#313244", padx=10, pady=8
)
code_input.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
code_input.tag_configure("kw",  foreground="#89b4fa")
code_input.tag_configure("num", foreground="#fab387")
code_input.bind("<KeyRelease>", on_key)

# Handle Tab
def on_tab(e):
    code_input.insert(tk.INSERT, "    ")
    return "break"
code_input.bind("<Tab>", on_tab)

# Right panel
right = tk.Frame(main, bg=BG)
right.grid(row=1, column=1, sticky="nsew")
right.rowconfigure(1, weight=1)
right.rowconfigure(3, weight=2)

tk.Label(right, text="Compiler / Interpreter Log", bg=BG, fg=ACCENT,
         font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0,3))
log_box = tk.Text(right, font=("Arial", 10), bg=PANEL_BG, fg=SUBTEXT,
                  state="disabled", relief="flat", padx=8, pady=6)
log_box.grid(row=1, column=0, sticky="nsew")
log_box.tag_configure("ok",   foreground=GREEN)
log_box.tag_configure("err",  foreground=RED)
log_box.tag_configure("info", foreground=YELLOW)

tk.Label(right, text="Output", bg=BG, fg=ACCENT,
         font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(10,3))
output_box = tk.Text(right, font=MONO, bg=PANEL_BG, fg=GREEN,
                     state="disabled", relief="flat", padx=8, pady=6)
output_box.grid(row=3, column=0, sticky="nsew")

# Buttons
btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(fill="x", padx=10, pady=(0, 10))

tk.Button(btn_frame, text="▶  Run", command=run_code,
          bg=ACCENT, fg="#000", font=("Arial", 10, "bold"),
          relief="flat", padx=16, pady=6,
          activebackground="#00d4ac").pack(side="left", padx=(0,8))

tk.Button(btn_frame, text="✕  Clear", command=clear_all,
          bg=RED, fg="#fff", font=("Arial", 10, "bold"),
          relief="flat", padx=16, pady=6,
          activebackground="#e06c75").pack(side="left")

tk.Label(btn_frame,
         text="Supports: variables · print · if/else · while · for · strings · % operator",
         bg=BG, fg=SUBTEXT, font=("Arial", 9)).pack(side="right")

root.mainloop()
