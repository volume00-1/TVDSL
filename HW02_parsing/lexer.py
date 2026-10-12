from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    line: int
    column: int
    offset: int

KEYWORDS = {
    "function": "FUNCTION", "returns": "RETURNS", "requires": "REQUIRES",
    "ensures": "ENSURES", "uses": "USES", "while": "WHILE", "invariant": "INVARIANT",
    "if": "IF", "else": "ELSE", "assert": "ASSERT", "assume": "ASSUME",
    "length": "LENGTH", "int": "INT_TYPE", "and": "AND", "or": "OR",
    "not": "NOT", "true": "TRUE", "false": "FALSE", "forall": "FORALL",
    "exists": "EXISTS",
}

TOKEN_RE = re.compile(
    r"(?P<WS>[ \t\r\n]+)|"
    r"(?P<COMMENT>//[^\r\n]*)|"
    r"(?P<FAT_ARROW>=\>)|"
    r"(?P<ARROW>-\>)|"
    r"(?P<EQEQ>==)|(?P<NE>!=)|(?P<LE><=)|(?P<GE>>=)|"
    r"(?P<ASSIGN>=)|"
    r"(?P<INT>0|[1-9][0-9]*)|"
    r"(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)|"
    r"(?P<LPAREN>\()|(?P<RPAREN>\))|"
    r"(?P<LBRACKET>\[)|(?P<RBRACKET>\])|"
    r"(?P<LBRACE>\{)|(?P<RBRACE>\})|"
    r"(?P<COMMA>,)|(?P<SEMICOLON>;)|(?P<COLON>:)|(?P<PIPE>\|)|"
    r"(?P<PLUS>\+)|(?P<MINUS>-)|(?P<STAR>\*)|(?P<SLASH>/)|"
    r"(?P<LT><)|(?P<GT>>)"
)

class LexError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"{message} в позиции {line}:{column}")
        self.line, self.column = line, column

def tokenize(source: str) -> list[Token]:
    result: list[Token] = []
    pos, line, column = 0, 1, 1
    
    while pos < len(source):
        match = TOKEN_RE.match(source, pos)
        if not match:
            raise LexError(f"неизвестный символ {source[pos]!r}", line, column)
        
        text, kind = match.group(), match.lastgroup
        start_line, start_column = line, column
        pos = match.end()
        
        if kind not in ("WS", "COMMENT"):
            if kind == "IDENT" and text in KEYWORDS:
                kind = KEYWORDS[text]
            result.append(Token(kind, text, start_line, start_column, match.start()))
            
        newlines = text.count("\n")
        if newlines:
            line += newlines
            column = len(text.rsplit("\n", 1)[1]) + 1
        else:
            column += len(text)
            
    result.append(Token("EOF", "", line, column, len(source)))
    return result