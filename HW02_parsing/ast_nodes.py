"""AST Node definitions for the Funny language."""
from dataclasses import dataclass, asdict, field
from typing import Any, List, Optional

class Node:
    """Базовый класс для всех узлов AST."""
    def to_dict(self) -> dict:
        d = asdict(self)
        d['type'] = type(self).__name__
        return d

@dataclass
class Module(Node):
    declarations: List[Node]

@dataclass
class Function(Node):
    name: str
    params: List[Node]
    returns: List[Node]
    requires: Optional[Node]
    ensures: Optional[Node]
    uses: List[Node]
    body: Node

@dataclass
class Formula(Node):
    name: str
    params: List[Node]
    body: Node

@dataclass
class VarDef(Node):
    name: str
    type: str

@dataclass
class Block(Node):
    statements: List[Node]

@dataclass
class If(Node):
    condition: Node
    then_branch: Node
    else_branch: Optional[Node]

@dataclass
class While(Node):
    condition: Node
    invariant: Optional[Node]
    body: Node

@dataclass
class Assert(Node):
    kind: str
    condition: Node

@dataclass
class Assignment(Node):
    targets: List[Node]
    value: Node

@dataclass
class Name(Node):
    name: str

@dataclass
class ArrayAccess(Node):
    array: Node
    index: Node

@dataclass
class IntLiteral(Node):
    value: int

@dataclass
class BoolLiteral(Node):
    value: bool

@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

@dataclass
class BinaryOp(Node):
    op: str
    left: Node
    right: Node

@dataclass
class Compare(Node):
    op: str
    left: Node
    right: Node

@dataclass
class Call(Node):
    name: str
    args: List[Node]

@dataclass
class Quantifier(Node):
    kind: str
    variable: Node
    body: Node