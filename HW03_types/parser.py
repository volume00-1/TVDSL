"""Recursive-descent LL(1) parser for Funny with panic mode."""
from dataclasses import dataclass
from lexer import Token, tokenize
import ast_nodes as ast

class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"{message} в позиции {token.line}:{token.column}")
        self.token = token

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens, self.i = tokens, 0
        self.errors = []

    @property
    def current(self) -> Token:
        return self.tokens[self.i]

    def accept(self, kind: str) -> Token | None:
        if self.current.kind == kind:
            token = self.current
            self.i += 1
            return token
        return None

    def expect(self, kind: str) -> Token | None:
        token = self.accept(kind)
        if token is None:
            self.error(f"ожидался {kind}, получен {self.current.kind}")
            return None
        return token

    def error(self, message: str):
        self.errors.append(ParseError(message, self.current))

    def sync_stmt(self):
        while True:
            t = self.current.kind
            if t == 'EOF':
                return
            if t == 'SEMICOLON':
                self.i += 1
                return
            if t in ('RBRACE', 'LBRACE', 'IF', 'WHILE', 'ASSERT', 'ASSUME'):
                return
            self.i += 1

    def sync_decl(self):
        while self.current.kind not in ("EOF", "FUNCTION"):
            self.i += 1

    def parse(self) -> ast.Module:
        declarations = []
        while self.current.kind != "EOF":
            start_i = self.i
            try:
                decl = self.decl()
                if decl:
                    declarations.append(decl)
            except ParseError as e:
                self.errors.append(e)
                if self.i == start_i:
                    self.i += 1
                self.sync_decl()
        
        if not declarations and not self.errors:
            self.error("модуль не может быть пустым")
        
        return ast.Module(declarations)

    def decl(self):
        func_token = self.accept("FUNCTION")
        if not func_token:
            self.error("ожидалось ключевое слово 'function'")
            self.sync_decl()
            return None
        
        name_token = self.expect("IDENT")
        if not name_token:
            self.sync_decl()
            return None
        
        name = name_token.text
        
        if not self.expect("LPAREN"):
            self.sync_decl()
            return None
        
        params = self.var_defs("RPAREN")
        
        if not self.expect("RPAREN"):
            self.sync_decl()
            return None
        
        if self.accept("ARROW"):
            predicate = self.predicate()
            return ast.Formula(name, params, predicate)
        
        requires = self.predicate() if self.accept("REQUIRES") else None
        
        if not self.expect("RETURNS"):
            self.sync_decl()
            return None
        
        returns = self.var_defs("REQUIRES", "ENSURES", "USES", "LBRACE")
        ensures = self.predicate() if self.accept("ENSURES") else None
        uses = self.var_defs("LBRACE") if self.accept("USES") else []
        self.accept("SEMICOLON")
        
        if not self.expect("LBRACE"):
            self.sync_decl()
            return None
        
        body = self.block_after_open()
        return ast.Function(name, params, returns, requires, ensures, uses, body)

    def var_defs(self, *stops: str) -> list[ast.VarDef]:
        if self.current.kind in stops:
            return []
        
        result = []
        var_def = self.var_def()
        if var_def:
            result.append(var_def)
        
        while self.accept("COMMA"):
            var_def = self.var_def()
            if var_def:
                result.append(var_def)
            else:
                break
        
        return result

    def var_def(self) -> ast.VarDef | None:
        name_token = self.expect("IDENT")
        if not name_token:
            return None
        
        name = name_token.text
        
        if not self.expect("COLON"):
            return None
        
        if not self.expect("INT_TYPE"):
            return None
        
        if self.accept("LBRACKET"):
            if not self.expect("RBRACKET"):
                return None
            return ast.VarDef(name, "int[]")
        
        return ast.VarDef(name, "int")

    def statement(self) -> ast.Node | None:
        kind = self.current.kind
        
        if kind == "LBRACE":
            self.i += 1
            return self.block_after_open()
        
        if kind == "IF":
            return self.parse_if()
        
        if kind == "WHILE":
            return self.parse_while()
        
        if kind in ("ASSERT", "ASSUME"):
            return self.parse_assert_assume()

        if kind == "USES":
            return self.parse_uses()

        if kind == "IDENT":
            return self.assignment()
        
        self.error(f"неожиданный токен {self.current.kind}")
        self.sync_stmt()
        return None

    def parse_if(self) -> ast.If | None:
        self.i += 1
        
        if not self.expect("LPAREN"):
            self.sync_stmt()
            return None
        
        condition = self.predicate()
        
        if not self.expect("RPAREN"):
            self.sync_stmt()
            return None
        
        then_branch = self.statement()
        otherwise = self.statement() if self.accept("ELSE") else None
        
        return ast.If(condition, then_branch, otherwise)

    def parse_while(self) -> ast.While | None:
        self.i += 1
        
        if not self.expect("LPAREN"):
            self.sync_stmt()
            return None
        
        condition = self.predicate()
        
        if not self.expect("RPAREN"):
            self.sync_stmt()
            return None
        
        invariant = self.predicate() if self.accept("INVARIANT") else None
        body = self.statement()
        
        return ast.While(condition, invariant, body)

    def parse_assert_assume(self) -> ast.Assert | None:
        op = self.current.text
        self.i += 1
        
        condition = self.predicate()
        
        if not self.expect("SEMICOLON"):
            self.sync_stmt()
            return None
        
        return ast.Assert(op, condition)

    def parse_uses(self) -> ast.Uses | None:
        self.i += 1
        declarations = self.var_defs("SEMICOLON", "RBRACE")
        if not self.expect("SEMICOLON"):
            self.sync_stmt()
            return None
        return ast.Uses(declarations)

    def block_after_open(self) -> ast.Block:
        statements = []
        
        while self.current.kind not in ("RBRACE", "EOF"):
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        
        if self.current.kind == "RBRACE":
            self.i += 1
        else:
            self.error("не закрыт блок '}'")
        
        return ast.Block(statements)

    def assignment(self) -> ast.Assignment | None:
        first_token = self.expect("IDENT")
        if not first_token:
            self.sync_stmt()
            return None
        
        first = ast.Name(first_token.text)
        
        if self.accept("LBRACKET"):
            index = self.expr()
            if not self.expect("RBRACKET"):
                self.sync_stmt()
                return None
            if not self.expect("ASSIGN"):
                self.sync_stmt()
                return None
            value = self.expr()
            if not self.expect("SEMICOLON"):
                self.sync_stmt()
                return None
            return ast.Assignment([ast.ArrayAccess(first, index)], value, True)
        
        if self.accept("ASSIGN"):
            value = self.expr()
            if not self.expect("SEMICOLON"):
                self.sync_stmt()
                return None
            return ast.Assignment([first], value)
        
        targets = [first]
        while self.accept("COMMA"):
            name_token = self.expect("IDENT")
            if name_token:
                targets.append(ast.Name(name_token.text))
            else:
                break
        
        if not self.expect("ASSIGN"):
            self.sync_stmt()
            return None
        
        value = self.call()
        if not self.expect("SEMICOLON"):
            self.sync_stmt()
            return None
        
        return ast.Assignment(targets, value)

    def predicate(self):
        return self.implies()

    def implies(self):
        left = self.or_expr()
        if self.accept("ARROW"):
            return ast.BinaryOp("->", left, self.implies())
        return left

    def or_expr(self):
        value = self.and_expr()
        while self.accept("OR"):
            value = ast.BinaryOp("or", value, self.and_expr())
        return value

    def and_expr(self):
        value = self.not_expr()
        while self.accept("AND"):
            value = ast.BinaryOp("and", value, self.not_expr())
        return value

    def not_expr(self):
        if self.accept("NOT"):
            return ast.UnaryOp("not", self.not_expr())
        return self.atom()

    def atom(self):
        if self.accept("TRUE"):
            return ast.BoolLiteral(True)
        if self.accept("FALSE"):
            return ast.BoolLiteral(False)
        
        if self.current.kind in ("FORALL", "EXISTS"):
            kind = self.current.text
            self.i += 1
            if not self.expect("LPAREN"):
                return ast.BoolLiteral(False)
            variable = self.var_def()
            if not self.expect("PIPE"):
                return ast.BoolLiteral(False)
            predicate = self.predicate()
            if not self.expect("RPAREN"):
                return ast.BoolLiteral(False)
            if variable:
                return ast.Quantifier(kind, variable, predicate)
            return ast.BoolLiteral(False)
        
        left = self.expr()
        if self.current.kind in ("EQEQ", "NE", "LE", "GE", "LT", "GT"):
            op = self.current.text
            self.i += 1
            right = self.expr()
            return ast.Compare(op, left, right)
        return left

    def expr(self):
        value = self.term()
        while self.current.kind in ("PLUS", "MINUS"):
            op = self.current.text
            self.i += 1
            right = self.term()
            value = ast.BinaryOp(op, value, right)
        return value

    def term(self):
        value = self.unary()
        while self.current.kind in ("STAR", "SLASH"):
            op = self.current.text
            self.i += 1
            right = self.unary()
            value = ast.BinaryOp(op, value, right)
        return value

    def unary(self):
        if self.accept("MINUS"):
            return ast.UnaryOp("-", self.unary())
        return self.primary()

    def primary(self):
        if token := self.accept("INT"):
            return ast.IntLiteral(int(token.text))

        if self.accept("TRUE"):
            return ast.BoolLiteral(True)
        if self.accept("FALSE"):
            return ast.BoolLiteral(False)

        if self.accept("LPAREN"):
            value = self.expr()
            if not self.expect("RPAREN"):
                return value
            return value
        
        if self.current.kind in ("IDENT", "LENGTH"):
            name = self.current.text
            self.i += 1
            
            if self.accept("LPAREN"):
                args = self.arguments_after_open()
                return ast.Call(name, args)
            
            value = ast.Name(name)
            
            if self.accept("LBRACKET"):
                index = self.expr()
                if not self.expect("RBRACKET"):
                    return value
                return ast.ArrayAccess(value, index)
            
            return value
        
        self.error("ожидалось выражение")
        return ast.IntLiteral(0)

    def call(self):
        token = self.accept("IDENT") or self.accept("LENGTH")
        if not token:
            self.error("ожидалось имя вызова")
            return ast.Call("unknown", [])
        
        name = token.text
        
        if not self.expect("LPAREN"):
            return ast.Call(name, [])
        
        args = self.arguments_after_open()
        return ast.Call(name, args)

    def arguments_after_open(self):
        args = []
        if self.current.kind != "RPAREN":
            arg = self.expr()
            args.append(arg)
            while self.accept("COMMA"):
                arg = self.expr()
                args.append(arg)
        
        if not self.expect("RPAREN"):
            return args
        
        return args

def parse(source: str) -> tuple[ast.Module, list[ParseError]]:
    tokens = tokenize(source)
    parser = Parser(tokens)
    tree = parser.parse()
    return tree, parser.errors