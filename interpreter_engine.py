from lark import Lark, Transformer, Tree, Token

grammar = r"""
    ?start: statement+

    ?statement: assignment
              | print_stmt
              | if_stmt
              | while_stmt
              | for_stmt

    block: "{" statement* "}"

    assignment: NAME "=" expr
    print_stmt: "print" expr

    if_stmt:    "if"    "(" condition ")" block ("else" block)?
    while_stmt: "while" "(" condition ")" block
    for_stmt:   "for"   "(" assignment ";" condition ";" assignment ")" block

    ?condition: condition "or"  cond_and   -> or_op
              | cond_and
    ?cond_and:  cond_and "and" cond_not    -> and_op
              | cond_not
    ?cond_not:  "not" cond_not             -> not_op
              | comparison

    ?comparison: expr COMPARATOR expr      -> compare
               | "(" condition ")"

    COMPARATOR: "<=" | "<" | ">=" | ">" | "==" | "!="

    ?expr: expr "+" term   -> add
         | expr "-" term   -> sub
         | term
    ?term: term "*"  factor -> mul
         | term "/"  factor -> div
         | term "%"  factor -> mod
         | factor
    ?factor: NUMBER         -> number
           | ESCAPED_STRING -> string
           | NAME           -> var
           | "(" expr ")"

    %import common.CNAME          -> NAME
    %import common.NUMBER
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, parser="lalr")
symbol_table_i: dict = {}


class ASTBuilder(Transformer):
    def number(self, n):
        v = n[0]
        return float(v) if '.' in str(v) else int(v)
    def string(self, s): 
        # Return tuple to mark as string literal
        return ('string', str(s[0])[1:-1])
    def var(self, v): 
        # Return tuple to mark as variable reference
        return ('var', str(v[0]))
    def add(self, i): return ('+',  i[0], i[1])
    def sub(self, i): return ('-',  i[0], i[1])
    def mul(self, i): return ('*',  i[0], i[1])
    def div(self, i): return ('/',  i[0], i[1])
    def mod(self, i): return ('%',  i[0], i[1])
    def assignment(self, i): return Tree("assignment",  i)
    def print_stmt(self, i): return Tree("print_stmt",  i)
    def block(self, i):      return Tree("block",       i)
    def if_stmt(self, i):    return Tree("if_stmt",     i)
    def while_stmt(self, i): return Tree("while_stmt",  i)
    def for_stmt(self, i):   return Tree("for_stmt",    i)
    def or_op(self,  i): return ('or',  i[0], i[1])
    def and_op(self, i): return ('and', i[0], i[1])
    def not_op(self, i): return ('not', i[0])
    def compare(self, i): return ('cmp', i[1].value, i[0], i[2])


def eval_expr(expr):
    # Numbers
    if isinstance(expr, (int, float)): 
        return expr
    
    # String literal (marked with tuple from ASTBuilder)
    if isinstance(expr, tuple) and len(expr) == 2 and expr[0] == 'string':
        return expr[1]
    
    # Variable reference (marked with tuple from ASTBuilder)
    if isinstance(expr, tuple) and len(expr) == 2 and expr[0] == 'var':
        var_name = expr[1]
        return symbol_table_i.get(var_name, 0)
    
    # Handle Tree nodes
    if isinstance(expr, Tree): 
        return eval_expr(expr.children[0])
    
    # Handle Token objects (from for loops, etc.)
    if isinstance(expr, Token): 
        return symbol_table_i.get(str(expr), 0)
    
    # Handle expression tuples (operations)
    if isinstance(expr, tuple):
        op = expr[0]
        
        # Arithmetic operations
        if op in ('+', '-', '*', '/', '%'):
            a = eval_expr(expr[1])
            b = eval_expr(expr[2])
            
            if op == '+':
                # String concatenation
                if isinstance(a, str) or isinstance(b, str):
                    return str(a) + str(b)
                return a + b
            if op == '-': 
                return a - b
            if op == '*': 
                return a * b
            if op == '/':
                if b == 0: 
                    raise ZeroDivisionError("Division by zero")
                return a / b
            if op == '%': 
                return a % b
        
        # Comparison operations
        elif op == 'cmp':
            comp = expr[1]
            a = eval_expr(expr[2])
            b = eval_expr(expr[3])
            operators = {
                '<': a < b,
                '<=': a <= b,
                '>': a > b,
                '>=': a >= b,
                '==': a == b,
                '!=': a != b
            }
            return operators[comp]
        
        # Logical operations
        elif op == 'and': 
            return eval_expr(expr[1]) and eval_expr(expr[2])
        elif op == 'or':  
            return eval_expr(expr[1]) or eval_expr(expr[2])
        elif op == 'not': 
            return not eval_expr(expr[1])
    
    raise ValueError(f"Cannot evaluate: {expr!r}")


def execute_statements(statements):
    for stmt in statements:
        if isinstance(stmt, Tree) and stmt.data == "block":
            execute_statements(stmt.children)
        else:
            execute_statement(stmt)


def execute_statement(stmt):
    if not isinstance(stmt, Tree):
        raise TypeError(f"Expected Tree, got {type(stmt)}")
    if stmt.data == "block":
        execute_statements(stmt.children)
    elif stmt.data == "assignment":
        name = stmt.children[0].value if isinstance(stmt.children[0], Token) else str(stmt.children[0])
        symbol_table_i[name] = eval_expr(stmt.children[1])
    elif stmt.data == "print_stmt":
        val = eval_expr(stmt.children[0])
        if isinstance(val, float) and val.is_integer(): print(int(val))
        else: print(val)
    elif stmt.data == "if_stmt":
        cond = eval_expr(stmt.children[0])
        true_blk  = stmt.children[1]
        false_blk = stmt.children[2] if len(stmt.children) > 2 else None
        if cond: execute_statements(true_blk.children)
        elif false_blk: execute_statements(false_blk.children)
    elif stmt.data == "while_stmt":
        cond_node, block = stmt.children[0], stmt.children[1]
        while eval_expr(cond_node):
            execute_statements(block.children)
    elif stmt.data == "for_stmt":
        init, cond_node, update, block = stmt.children
        execute_statement(init)
        while eval_expr(cond_node):
            execute_statements(block.children)
            execute_statement(update)
    else:
        raise NotImplementedError(f"Unknown statement: {stmt.data}")


def interpret_terminal(tree):
    symbol_table_i.clear()
    execute_statements(tree.children)
