"""
interpreter.py — Core engine used by app.py.

parse_and_run_code(code) → { output, steps, errors, suggestions, symbol_table }
"""

import re
import io
import contextlib
from interpreter_engine import parser, ASTBuilder, interpret_terminal


# ── Comment removal function ──────────────────────────────────────────────
def remove_comments(code: str) -> str:
    """
    Remove // and /* */ comments without touching string contents.
    Works character by character so 'x = "hello // world"' is safe.
    """
    result = []
    i = 0
    n = len(code)
    in_string = False
    string_char = ''

    while i < n:
        ch = code[i]

        # Track string boundaries
        if not in_string and ch in ('"', "'"):
            in_string = True
            string_char = ch
            result.append(ch)
            i += 1
            continue

        if in_string:
            if ch == '\\' and i + 1 < n:          # escaped char inside string
                result.append(ch)
                result.append(code[i + 1])
                i += 2
                continue
            if ch == string_char:
                in_string = False
            result.append(ch)
            i += 1
            continue

        # Block comment  /* ... */
        if ch == '/' and i + 1 < n and code[i + 1] == '*':
            i += 2
            while i < n - 1:
                if code[i] == '*' and code[i + 1] == '/':
                    i += 2
                    break
                i += 1
            continue

        # Line comment  // ...
        if ch == '/' and i + 1 < n and code[i + 1] == '/':
            while i < n and code[i] != '\n':
                i += 1
            continue

        result.append(ch)
        i += 1

    return ''.join(result)


# ── Analysis functions ────────────────────────────────────────────────────
def analyze_lexer_details(code: str) -> dict:
    """Analyze what tokens are in the user's code."""
    lines = code.split('\n')
    
    # Count different token types
    token_counts = {
        'keywords': 0,
        'variables': 0,
        'numbers': 0,
        'strings': 0,
        'operators': 0,
        'comparisons': 0
    }
    
    # Keywords in your language
    keywords = {'if', 'else', 'while', 'for', 'print', 'and', 'or', 'not'}
    
    # Simple scanning
    for line in lines:
        words = re.findall(r'\b\w+\b', line)
        for word in words:
            if word in keywords:
                token_counts['keywords'] += 1
            elif word.isdigit() or re.fullmatch(r'\d+(\.\d+)?', word):
                token_counts['numbers'] += 1
            elif word.isidentifier() and not word[0].isdigit():
                # Only count as variable if it's not a keyword and looks like a name
                token_counts['variables'] += 1
        
        # Find strings
        strings = re.findall(r'"[^"]*"', line)
        token_counts['strings'] += len(strings)
        
        # Find operators
        operators = re.findall(r'[+\-*/%=<>!&|]+', line)
        token_counts['operators'] += len(operators)
        
        # Find comparisons
        comparisons = re.findall(r'[<>]=?|==|!=', line)
        token_counts['comparisons'] += len(comparisons)
    
    # Generate dynamic description
    details = []
    if token_counts['variables'] > 0:
        details.append(f"{token_counts['variables']} variable(s)")
    if token_counts['numbers'] > 0:
        details.append(f"{token_counts['numbers']} number(s)")
    if token_counts['strings'] > 0:
        details.append(f"{token_counts['strings']} string(s)")
    if token_counts['keywords'] > 0:
        details.append(f"{token_counts['keywords']} keyword(s)")
    if token_counts['operators'] > 0:
        details.append(f"{token_counts['operators']} operator(s)")
    
    return {
        'counts': token_counts,
        'summary': f"Found {', '.join(details)}" if details else "No tokens found",
        'total_tokens': sum(token_counts.values())
    }


def analyze_parser_details(code: str) -> dict:
    """Analyze what statements/structures are in the code."""
    structures = {
        'assignments': 0,
        'print_statements': 0,
        'if_statements': 0,
        'while_loops': 0,
        'for_loops': 0,
        'expressions': 0
    }
    
    # Simple keyword counting (more reliable)
    structures['assignments'] = len(re.findall(r'^\s*\w+\s*=', code, re.MULTILINE))
    structures['print_statements'] = len(re.findall(r'\bprint\s', code))
    structures['if_statements'] = len(re.findall(r'\bif\s*\(', code))
    structures['while_loops'] = len(re.findall(r'\bwhile\s*\(', code))
    structures['for_loops'] = len(re.findall(r'\bfor\s*\(', code))
    
    # Count operations (rough estimate)
    structures['expressions'] = len(re.findall(r'[+\-*/]', code)) - len(re.findall(r'[<>]=?|==|!=', code))
    
    # Build description
    structure_names = {
        'assignments': 'assignment',
        'print_statements': 'print statement',
        'if_statements': 'if statement',
        'while_loops': 'while loop',
        'for_loops': 'for loop',
        'expressions': 'expression'
    }
    
    structures_found = []
    for key, count in structures.items():
        if count > 0:
            name = structure_names[key]
            if count > 1:
                name += 's'
            structures_found.append(f"{count} {name}")
    
    if structures_found:
        summary = "Found " + ", ".join(structures_found)
    else:
        summary = "No structures found"
    
    return {
        'structures': structures,
        'summary': summary
    }


def analyze_ast_details(ast) -> dict:
    """Analyze the AST structure."""
    if not ast:
        return {'summary': 'AST could not be built', 'node_count': 0}
    
    def count_nodes(node):
        if isinstance(node, dict):
            count = 1
            for child in node.get('children', []):
                count += count_nodes(child)
            return count
        return 1
    
    node_count = count_nodes(ast)
    
    return {
        'node_count': node_count,
        'summary': f"Built AST with {node_count} node(s) representing your program's logic"
    }


def analyze_execution_details(symbol_table: dict, output: str) -> dict:
    """Analyze what happened during execution."""
    details = []
    
    if symbol_table:
        var_count = len(symbol_table)
        details.append(f"Created {var_count} variable(s)")
        
        # Show variable values
        var_details = []
        for var, val in list(symbol_table.items())[:3]:
            var_details.append(f"{var}={val}")
        if var_details:
            details.append(f"Variables: {', '.join(var_details)}")
            if len(symbol_table) > 3:
                details.append(f"... and {len(symbol_table)-3} more")
    
    if output:
        output_lines = output.split('\n')
        details.append(f"Generated {len(output_lines)} line(s) of output")
        
        # Show first output line
        if output_lines and output_lines[0]:
            details.append(f"First output: \"{output_lines[0]}\"")
    
    if not symbol_table and not output:
        details.append("No variables created or output generated")
    
    return {
        'summary': ' | '.join(details),
        'var_count': len(symbol_table),
        'output_lines': len(output.split('\n')) if output else 0
    }


# ── Common beginner mistakes & smart suggestions ──────────────────────────────
SUGGESTIONS = [
    # Missing parentheses around if/while condition
    (r'\bif\s+[^(\s]',           'if-no-paren',  "Use parentheses around the condition: `if (x > 0) { ... }`"),
    (r'\bwhile\s+[^(\s]',        'while-no-paren',"Use parentheses around the condition: `while (x < 10) { ... }`"),
    # print with parens like Python
    (r'\bprint\s*\(',            'print-paren',  "Don't use parentheses with print: use `print x` not `print(x)`"),
    # == vs = confusion inside if condition
    (r'if\s*\(\s*\w+\s*=[^=]',  'if-assign',    "Inside `if`, use `==` for comparison, not `=`. Example: `if (x == 5)`"),
    # Missing braces after if — only fires when no { appears at all on that line
    (r'\bif\s*\([^)]*\)\s*[^{{\n]','if-no-brace',"Use curly braces `{ }` for the if-body: `if (cond) { print x }`"),
    # Semicolons in for loop
    (r'\bfor\s*\([^;]*\)',       'for-no-semi',  "A for loop needs semicolons: `for (i=0; i<5; i=i+1) { ... }`"),
]


def analyse_code(code: str) -> list[dict]:
    """Return beginner-friendly suggestions based on pattern matching."""
    hints = []
    seen = set()
    for pattern, tag, msg in SUGGESTIONS:
        if re.search(pattern, code) and tag not in seen:
            hints.append({"tag": tag, "msg": msg})
            seen.add(tag)
    return hints


def tree_to_dict(node) -> dict:
    """Convert a Lark Tree / Token to a JSON-serialisable dict for the frontend."""
    from lark import Tree, Token
    if isinstance(node, Tree):
        return {
            "type": "node",
            "name": node.data,
            "children": [tree_to_dict(c) for c in node.children]
        }
    elif isinstance(node, Token):
        return {"type": "token", "name": node.type, "value": str(node)}
    elif isinstance(node, tuple):
        return {"type": "tuple", "op": str(node[0]),
                "children": [tree_to_dict(x) for x in node[1:]]}
    else:
        return {"type": "literal", "value": str(node)}


# ── Main parse and run function ──────────────────────────────────────────
def parse_and_run_code(code: str) -> dict:
    # Remove comments before processing
    code = remove_comments(code)
    
    steps = []
    errors = []
    output = ""
    ast_json = None
    symbol_table = {}

    # ── Pre-run suggestions (pattern-based) ──────────────────────────────────
    suggestions = analyse_code(code)

    # ── STEP 1: Lexer (Dynamic analysis) ─────────────────────────────────────
    lexer_info = analyze_lexer_details(code)
    steps.append({
        "phase": "Lexer",
        "icon": "🔡",
        "status": "running",
        "detail": f"🔍 Scanning your code... {lexer_info['summary']}",
        "educational": f"The lexer breaks down your code into tokens. {lexer_info['summary'].replace('Found', 'We found')}."
    })

    # ── STEP 2: Parser (Dynamic analysis) ───────────────────────────────────
    parser_info = analyze_parser_details(code)
    steps.append({
        "phase": "Parser",
        "icon": "🌳",
        "status": "running",
        "detail": f"📝 Checking grammar rules... {parser_info['summary']}",
        "educational": f"The parser verifies your code follows the language grammar. {parser_info['summary']}"
    })

    try:
        parse_tree = parser.parse(code)
        steps[-1]["status"] = "ok"
        steps[-1]["detail"] = f"✅ Grammar valid! {parser_info['summary']}"
        steps[-1]["educational"] = f"Your code passed all grammar checks. The parser built a tree showing: {parser_info['summary']}"
        
        steps[0]["status"] = "ok"
        steps[0]["detail"] = f"✅ Tokenization complete! {lexer_info['summary']}"
        steps[0]["educational"] = f"We broke your code into {lexer_info['total_tokens']} tokens. {lexer_info['summary']} are now ready for parsing."
        
    except Exception as e:
        err_msg = str(e)
        steps[-1]["status"] = "error"
        steps[-1]["detail"] = f"❌ Parse failed: {err_msg[:100]}"
        steps[-1]["educational"] = f"The parser encountered an error at {_extract_error_location(err_msg, code)}. This usually means the grammar rules were violated."

        steps[0]["status"] = "ok"
        
        friendly = _friendly_parse_error(err_msg, code)
        errors.append({"phase": "Parser", "raw": err_msg, "friendly": friendly})
        return {
            "output": "", "steps": steps, "errors": errors,
            "suggestions": suggestions, "symbol_table": {}, "ast": None
        }

    # ── STEP 3: AST Builder ──────────────────────────────────────────────────
    steps.append({
        "phase": "AST Builder",
        "icon": "🏗️",
        "status": "running",
        "detail": "🔨 Transforming parse tree into Abstract Syntax Tree...",
        "educational": "The AST simplifies the parse tree by removing unnecessary details, keeping only what's needed for execution."
    })
    
    try:
        ast = ASTBuilder().transform(parse_tree)
        ast_json = tree_to_dict(ast)
        ast_info = analyze_ast_details(ast_json)
        
        steps[-1]["status"] = "ok"
        steps[-1]["detail"] = f"✅ {ast_info['summary']}"
        steps[-1]["educational"] = f"The AST contains {ast_info['node_count']} nodes. Each node represents an action: variable assignment, arithmetic operation, loop, or conditional."
        
    except Exception as e:
        steps[-1]["status"] = "error"
        steps[-1]["detail"] = f"❌ AST error: {str(e)[:100]}"
        steps[-1]["educational"] = "Failed to build the AST. This usually means the parse tree had unexpected structure."
        errors.append({"phase": "AST Builder", "raw": str(e), "friendly": str(e)})
        return {
            "output": "", "steps": steps, "errors": errors,
            "suggestions": suggestions, "symbol_table": {}, "ast": None
        }

    # ── STEP 4: Interpreter ─────────────────────────────────────────────────
    steps.append({
        "phase": "Interpreter",
        "icon": "⚙️",
        "status": "running",
        "detail": "🏃 Executing your program...",
        "educational": "The interpreter walks through the AST and performs each action, managing variables in memory."
    })
    
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            interpret_terminal(ast)
        output = buf.getvalue().rstrip()
        from interpreter_engine import symbol_table_i
        symbol_table = dict(symbol_table_i)
        
        exec_info = analyze_execution_details(symbol_table, output)
        
        steps[-1]["status"] = "ok"
        steps[-1]["detail"] = f"✅ Execution complete! {exec_info['summary']}"
        steps[-1]["educational"] = f"The interpreter successfully executed all statements. {exec_info['summary']}"
        
    except ZeroDivisionError as e:
        steps[-1]["status"] = "error"
        steps[-1]["detail"] = "❌ Runtime error: Division by zero"
        steps[-1]["educational"] = "The interpreter tried to divide a number by zero, which is mathematically undefined. Check for divisions where the denominator might become zero."
        errors.append({"phase": "Interpreter", "raw": str(e),
                       "friendly": "You divided by zero. Make sure the divisor is never 0."})
    except Exception as e:
        steps[-1]["status"] = "error"
        steps[-1]["detail"] = f"❌ Runtime error: {str(e)[:100]}"
        
        # Specific educational messages for common errors
        if "'NoneType'" in str(e) or "undefined" in str(e).lower():
            steps[-1]["educational"] = "A variable was used before it was assigned a value. Make sure to initialize variables before using them."
        elif "TypeError" in str(e):
            steps[-1]["educational"] = "You tried to perform an operation on incompatible types (e.g., adding a number to a string incorrectly)."
        else:
            steps[-1]["educational"] = f"Runtime error: {str(e)[:200]}. Check your logic and variable values."
            
        errors.append({"phase": "Interpreter", "raw": str(e),
                       "friendly": _friendly_runtime_error(str(e))})

    return {
        "output": output,
        "steps": steps,
        "errors": errors,
        "suggestions": suggestions,
        "symbol_table": {k: v for k, v in symbol_table.items()},
        "ast": ast_json
    }


# ── Helper functions ──────────────────────────────────────────────────────
def _extract_error_location(error_msg: str, code: str) -> str:
    """Extract line/column from error message."""
    line_match = re.search(r'line (\d+)', error_msg)
    if line_match:
        line_num = int(line_match.group(1))
        lines = code.split('\n')
        if line_num <= len(lines):
            return f"line {line_num}: \"{lines[line_num-1][:50]}\""
    return "an unexpected location"


def _friendly_parse_error(raw: str, code: str) -> str:
    lines = code.splitlines()
    # Lark puts line/col in the message
    line_match = re.search(r'line (\d+)', raw)
    col_match  = re.search(r'col(?:umn)? (\d+)', raw)
    hint = ""
    if line_match:
        ln = int(line_match.group(1))
        bad_line = lines[ln - 1].strip() if ln <= len(lines) else ""
        hint = f' (line {ln}: `{bad_line}`)'

    if 'Unexpected token' in raw or 'Expected' in raw:
        return (f"Syntax error{hint}. "
                "Something unexpected was found — check for missing `{{`, `}}`, `;`, or `()` around conditions.")
    if 'EOF' in raw:
        return "Your code ended unexpectedly — you may have forgotten a closing `}` brace."
    return f"Syntax error{hint}: {raw[:120]}"


def _friendly_runtime_error(raw: str) -> str:
    if 'not defined' in raw.lower() or 'KeyError' in raw:
        return "You used a variable that hasn't been assigned a value yet. Assign it first: `x = 0`."
    return raw[:200]