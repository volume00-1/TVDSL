"""Тесты для семантического анализатора HW3."""
import json
import pathlib
import unittest
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lexer import LexError, tokenize
from parser import Parser
from semantic_analyzer import SemanticAnalyzer

TESTS = ROOT / "tests" / "semantic"


class SemanticTests(unittest.TestCase):
    """Тесты семантического анализатора."""

    def _analyze(self, source: str):
        """Вспомогательный метод: лексер + парсер + семантический анализ."""
        tokens = tokenize(source)
        parser = Parser(tokens)
        ast_tree = parser.parse()
        analyzer = SemanticAnalyzer()
        errors = analyzer.analyze(ast_tree)
        return ast_tree, errors

    # --- Позитивные тесты (ошибок быть не должно) ---

    def test_valid_simple_function(self):
        """Простая функция без ошибок."""
        source = """
function max(a: int, b: int)
    returns r: int
{
    if (a > b) {
        r = a;
    } else {
        r = b;
    }
}
"""
        tree, errors = self._analyze(source)
        self.assertEqual(len(errors), 0, f"Ожидалось 0 ошибок, получено: {errors}")

    def test_valid_array_operations(self):
        """Операции с массивами."""
        source = """
function process(arr: int[], size: int)
    returns res: int
{
    uses i: int;
    i = 0;
    while (i < size) {
        arr[i] = arr[i] + 1;
        i = i + 1;
    }
    res = arr[0];
}
"""
        tree, errors = self._analyze(source)
        self.assertEqual(len(errors), 0, f"Ожидалось 0 ошибок, получено: {errors}")

    def test_valid_function_call(self):
        """Вызов функции с правильными аргументами."""
        source = """
function add(a: int, b: int)
    returns r: int
{
    r = a + b;
}

function main()
    returns result: int
{
    result = add(5, 3);
}
"""
        tree, errors = self._analyze(source)
        self.assertEqual(len(errors), 0, f"Ожидалось 0 ошибок, получено: {errors}")

    def test_valid_logical_operations(self):
        """Логические операции в условиях."""
        source = """
function check(x: int, y: int)
    returns r: int
{
    if (x > 0 and y < 10) {
        r = 1;
    } else {
        r = 0;
    }
}
"""
        tree, errors = self._analyze(source)
        self.assertEqual(len(errors), 0, f"Ожидалось 0 ошибок, получено: {errors}")

    # --- Негативные тесты (ошибки должны быть) ---

    def test_undeclared_variable(self):
        """Использование необъявленной переменной."""
        source = """
function bad()
    returns r: int
{
    r = x;
}
"""
        tree, errors = self._analyze(source)
        self.assertGreater(len(errors), 0, "Ожидалась ошибка: необъявленная переменная")
        self.assertTrue(any("x" in err for err in errors), "Ошибка должна упоминать 'x'")

    def test_type_mismatch_assignment(self):
        """Несовпадение типов при присваивании."""
        source = """
function bad(a: int[])
    returns r: int
{
    r = a;
}
"""
        tree, errors = self._analyze(source)
        self.assertGreater(len(errors), 0, "Ожидалась ошибка: несовпадение типов")

    def test_wrong_argument_count(self):
        """Неверное количество аргументов при вызове функции."""
        source = """
function add(a: int, b: int)
    returns r: int
{
    r = a + b;
}

function bad()
    returns result: int
{
    result = add(5);
}
"""
        tree, errors = self._analyze(source)
        self.assertGreater(len(errors), 0, "Ожидалась ошибка: неверное количество аргументов")

    def test_wrong_argument_type(self):
        """Неверный тип аргумента при вызове функции."""
        source = """
function add(a: int, b: int)
    returns r: int
{
    r = a + b;
}

function bad(arr: int[])
    returns result: int
{
    result = add(arr, 5);
}
"""
        tree, errors = self._analyze(source)
        self.assertGreater(len(errors), 0, "Ожидалась ошибка: неверный тип аргумента")

    def test_array_index_on_non_array(self):
        """Индексация не-массива."""
        source = """
function bad(x: int)
    returns r: int
{
    r = x[0];
}
"""
        tree, errors = self._analyze(source)
        self.assertGreater(len(errors), 0, "Ожидалась ошибка: индексация не-массива")

    def test_non_bool_condition(self):
        """Небулево условие в if."""
        source = """
function bad(x: int)
    returns r: int
{
    if (x) {
        r = 1;
    } else {
        r = 0;
    }
}
"""
        tree, errors = self._analyze(source)
        self.assertGreater(len(errors), 0, "Ожидалась ошибка: небулево условие")

    def test_arithmetic_on_bool(self):
        """Арифметика с булевыми значениями."""
        source = """
function bad()
    returns r: int
{
    r = true + 1;
}
"""
        tree, errors = self._analyze(source)
        self.assertGreater(len(errors), 0, "Ожидалась ошибка: арифметика с bool")

    def test_undeclared_function_call(self):
        """Вызов необъявленной функции."""
        source = """
function bad()
    returns r: int
{
    r = foo(5);
}
"""
        tree, errors = self._analyze(source)
        self.assertGreater(len(errors), 0, "Ожидалась ошибка: вызов необъявленной функции")
        self.assertTrue(any("foo" in err for err in errors), "Ошибка должна упоминать 'foo'")

    def test_multiple_errors(self):
        """Программа с несколькими ошибками."""
        source = """
function bad()
    returns r: int
{
    r = x + y;
    z = 5;
}
"""
        tree, errors = self._analyze(source)
        self.assertGreater(len(errors), 1, "Ожидалось несколько ошибок")


class AnnotationTests(unittest.TestCase):
    """Проверка, что AST аннотируется типами."""

    def _analyze(self, source: str):
        tokens = tokenize(source)
        parser = Parser(tokens)
        ast_tree = parser.parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast_tree)
        return ast_tree

    def test_name_node_annotated(self):
        """Узел Name должен получить поле type."""
        source = """
function f(x: int)
    returns r: int
{
    r = x;
}
"""
        tree = self._analyze(source)
        # Находим узел Name в дереве
        func = tree.declarations[0]
        body = func.body
        assignment = body.statements[0]
        value = assignment.value  # Это Name("x")
        
        self.assertEqual(value.type, "int", "Узел Name должен быть аннотирован типом 'int'")

    def test_binaryop_annotated(self):
        """Узел BinaryOp должен получить поле type."""
        source = """
function f(a: int, b: int)
    returns r: int
{
    r = a + b;
}
"""
        tree = self._analyze(source)
        func = tree.declarations[0]
        body = func.body
        assignment = body.statements[0]
        value = assignment.value  # Это BinaryOp("+", ...)
        
        self.assertEqual(value.type, "int", "BinaryOp должен быть аннотирован типом 'int'")


if __name__ == "__main__":
    unittest.main()