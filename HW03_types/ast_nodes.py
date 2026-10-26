"""AST Node definitions for the Funny language with type annotations."""
from dataclasses import dataclass, field, fields
from typing import Any, List, Optional


class Node:
    """Базовый класс для всех узлов AST."""
    def to_dict(self) -> dict:
        d = {}
        for node_field in fields(self):
            value = getattr(self, node_field.name)
            if isinstance(value, Node):
                value = value.to_dict()
            elif isinstance(value, list):
                value = [
                    item.to_dict() if isinstance(item, Node) else item
                    for item in value
                ]
            d[node_field.name] = value
        if "type" in d:
            d["inferred_type"] = d["type"]
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
    type: str  # "int" или "int[]"


@dataclass
class Uses(Node):
    declarations: List[Node]


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
    kind: str  # 'assert' или 'assume'
    condition: Node


@dataclass
class Assignment(Node):
    targets: List[Node]
    value: Node
    is_array_update: bool = False  # True если a[i] = v


@dataclass
class Name(Node):
    name: str
    type: Optional[str] = None  # Аннотация типа (заполняется семантическим анализатором)


@dataclass
class ArrayAccess(Node):
    array: Node
    index: Node
    type: Optional[str] = None  # Всегда "int" если корректно


@dataclass
class IntLiteral(Node):
    value: int
    type: str = "int"  # Всегда int


@dataclass
class BoolLiteral(Node):
    value: bool
    type: str = "bool"  # Всегда bool


@dataclass
class UnaryOp(Node):
    op: str  # "-", "not"
    operand: Node
    type: Optional[str] = None  # Заполняется семантическим анализатором


@dataclass
class BinaryOp(Node):
    op: str  # "+", "-", "*", "/", "and", "or", "->"
    left: Node
    right: Node
    type: Optional[str] = None  # Заполняется семантическим анализатором


@dataclass
class Compare(Node):
    op: str  # "==", "!=", "<", ">", "<=", ">="
    left: Node
    right: Node
    type: str = "bool"  # Всегда bool


@dataclass
class Call(Node):
    name: str
    args: List[Node]
    type: Optional[str] = None  # Тип возвращаемого значения функции


@dataclass
class Quantifier(Node):
    kind: str  # "forall" или "exists"
    variable: Node
    body: Node
    type: str = "bool"  # Всегда bool