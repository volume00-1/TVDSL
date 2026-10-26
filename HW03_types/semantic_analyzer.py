"""Семантический анализатор для языка Funny."""
from ast_nodes import (
    Module, Function, Formula, VarDef, Block, If, While, Assert, Assignment,
    Name, ArrayAccess, IntLiteral, BoolLiteral, UnaryOp, BinaryOp, Compare, Call, Quantifier, Uses
)
from symbol_table import SymbolTable, Symbol


class SemanticAnalyzer:
    def __init__(self):
        self.table = SymbolTable()
        self.errors = []

    def analyze(self, module: Module):
        """Главный метод: запускает анализ всего модуля."""
        
        # ПРОХОД 1: Регистрация всех функций и формул в глобальной области
        # Это нужно, чтобы функции могли вызывать друг друга (даже если объявлены ниже)
        for decl in module.declarations:
            if isinstance(decl, Function):
                self._register_function(decl)
            elif isinstance(decl, Formula):
                self._register_formula(decl)

        # ПРОХОД 2: Анализ тел функций и формул
        for decl in module.declarations:
            if isinstance(decl, Function):
                self._analyze_function(decl)
            elif isinstance(decl, Formula):
                self._analyze_formula(decl)

        return self.errors

    # --- Вспомогательные методы для регистрации ---

    def _register_function(self, func: Function):
        param_types = [p.type for p in func.params]
        return_types = [r.type for r in func.returns]
        
        symbol = Symbol(
            name=func.name, type="function", role="function",
            param_types=param_types, return_types=return_types,
            line=0, column=0 # Позицию можно брать из токена, если сохраним в AST
        )
        self.table.add_symbol(symbol)

    def _register_formula(self, formula: Formula):
        # Формулы пока считаем как функции, возвращающие bool
        symbol = Symbol(
            name=formula.name, type="function", role="formula",
            param_types=[p.type for p in formula.params], return_types=["bool"]
        )
        self.table.add_symbol(symbol)

    # --- Анализ тел ---

    def _analyze_function(self, func: Function):
        self.table.enter_scope(f"function {func.name}")
        
        # Добавляем параметры и возвращаемые значения в локальную таблицу
        for p in func.params:
            self.table.add_symbol(Symbol(name=p.name, type=p.type, role="parameter"))
        for r in func.returns:
            self.table.add_symbol(Symbol(name=r.name, type=r.type, role="return"))
        for u in func.uses:
            self.table.add_symbol(Symbol(name=u.name, type=u.type, role="local"))

        # Анализируем тело
        self.visit(func.body)
        
        self.table.exit_scope()

    def _analyze_formula(self, formula: Formula):
        self.table.enter_scope(f"formula {formula.name}")
        for p in formula.params:
            self.table.add_symbol(Symbol(name=p.name, type=p.type, role="parameter"))
        
        self.visit(formula.body)
        self.table.exit_scope()

    # --- Посетители (Visitor Pattern) ---
    # Каждый метод возвращает тип выражения ("int", "bool", "int[]", "error")

    def visit(self, node):
        if node is None:
            return "error"
        
        method_name = f'visit_{type(node).__name__.lower()}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        # Если для узла нет специального метода, просто идем вглубь детей
        for child in node.__dict__.values():
            if isinstance(child, list):
                for item in child:
                    if hasattr(item, 'type'): # Упрощение
                        self.visit(item)
            elif hasattr(child, 'type'):
                self.visit(child)
        return "unknown"

    def visit_block(self, node: Block):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_uses(self, node: Uses):
        for declaration in node.declarations:
            self.table.add_symbol(
                Symbol(name=declaration.name, type=declaration.type, role="local")
            )

    def visit_if(self, node: If):
        cond_type = self.visit(node.condition)
        if cond_type != "bool":
            self._error(node.condition, f"условие if должно быть bool, получено {cond_type}")
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_while(self, node: While):
        cond_type = self.visit(node.condition)
        if cond_type != "bool":
            self._error(node.condition, f"условие while должно быть bool, получено {cond_type}")
        if node.invariant:
            self.visit(node.invariant)
        self.visit(node.body)

    def visit_assert(self, node: Assert):
        cond_type = self.visit(node.condition)
        if cond_type != "bool":
            self._error(node.condition, f"аргумент assert/assume должен быть bool")

    def visit_assignment(self, node: Assignment):
        value_type = self.visit(node.value)
        
        for target in node.targets:
            target_type = self.visit(target)
            
            # Проверка совместимости типов
            if target_type != "error" and value_type != "error":
                if target_type != value_type:
                    self._error(target, f"несовместимые типы при присваивании: {target_type} и {value_type}")

    def visit_name(self, node: Name):
        symbol = self.table.lookup(node.name)
        if symbol is None:
            self._error(node, f"неизвестное имя '{node.name}'")
            node.type = "error"
            return "error"
        node.type = symbol.type
        return symbol.type

    def visit_arrayaccess(self, node: ArrayAccess):
        array_type = self.visit(node.array)
        index_type = self.visit(node.index)
        
        if array_type != "int[]":
            self._error(node.array, f"индексация возможна только для массива, получено {array_type}")
        if index_type != "int":
            self._error(node.index, f"индекс должен быть int, получено {index_type}")
            
        node.type = "int" # Элемент массива int[] всегда имеет тип int
        return "int"

    def visit_intliteral(self, node: IntLiteral):
        node.type = "int"
        return "int"

    def visit_boolliteral(self, node: BoolLiteral):
        node.type = "bool"
        return "bool"

    def visit_unaryop(self, node: UnaryOp):
        operand_type = self.visit(node.operand)
        
        if node.op == "-":
            if operand_type != "int":
                self._error(node, f"унарный минус требует int, получено {operand_type}")
            node.type = "int"
        elif node.op == "not":
            if operand_type != "bool":
                self._error(node, f"not требует bool, получено {operand_type}")
            node.type = "bool"
        else:
            node.type = "error"
        return node.type

    def visit_binaryop(self, node: BinaryOp):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        if node.op in ("+", "-", "*", "/"):
            if left_type != "int" or right_type != "int":
                self._error(node, f"арифметика требует int, получено {left_type} и {right_type}")
            node.type = "int"
        elif node.op in ("and", "or", "->"):
            if left_type != "bool" or right_type != "bool":
                self._error(node, f"логика требует bool, получено {left_type} и {right_type}")
            node.type = "bool"
        else:
            node.type = "error"
        return node.type

    def visit_compare(self, node: Compare):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        if left_type != "int" or right_type != "int":
            # В Funny обычно сравнивают int. Если нужно сравнивать bool/массивы - правила меняются.
            self._error(node, f"сравнение требует int, получено {left_type} и {right_type}")
            
        node.type = "bool"
        return "bool"

    def visit_call(self, node: Call):
        symbol = self.table.lookup(node.name)
        if symbol is None:
            self._error(node, f"неизвестная функция '{node.name}'")
            node.type = "error"
            return "error"
            
        if symbol.role not in ("function", "formula"):
            self._error(node, f"'{node.name}' не является функцией")
            node.type = "error"
            return "error"

        # Проверка количества аргументов
        if len(node.args) != len(symbol.param_types):
            self._error(node, f"функция '{node.name}' ожидает {len(symbol.param_types)} аргументов, передано {len(node.args)}")
            node.type = "error"
            return "error"

        # Проверка типов аргументов
        for i, arg in enumerate(node.args):
            arg_type = self.visit(arg)
            expected = symbol.param_types[i]
            if arg_type != "error" and expected != "error" and arg_type != expected:
                self._error(arg, f"аргумент {i+1} функции '{node.name}' должен быть {expected}, получено {arg_type}")

        node.type = symbol.return_types[0] if symbol.return_types else "int"
        return node.type

    # --- Утилиты ---

    def _error(self, node, message: str):
        # Пытаемся достать позицию из узла (если мы её туда положили при парсинге)
        # В текущем AST позиции нет, поэтому пока просто текст. 
        # В идеале нужно добавить line/col в базовый класс Node.
        self.errors.append(f"Семантическая ошибка: {message}")