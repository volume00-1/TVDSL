import json
import pathlib
import unittest
from lexer import LexError
from parser import parse

ROOT = pathlib.Path(__file__).resolve().parent.parent

class ParserTests(unittest.TestCase):
    # --- Корректные программы (ожидаем 0 ошибок) ---
    
    def test_valid_simple(self):
        source = (ROOT / "tests" / "valid" / "simple.funny").read_text()
        tree, errors = parse(source)
        self.assertEqual(len(errors), 0)
        self.assertEqual(tree.to_dict()["type"], "Module")
        json.dumps(tree.to_dict())  # Проверка, что сериализуется в JSON

    def test_valid_with_invariant(self):
        source = (ROOT / "tests" / "valid" / "with_invariant.funny").read_text()
        tree, errors = parse(source)
        self.assertEqual(len(errors), 0)

    def test_valid_complex_expr(self):
        source = (ROOT / "tests" / "valid" / "complex_expr.funny").read_text()
        tree, errors = parse(source)
        self.assertEqual(len(errors), 0)

    def test_valid_with_formula(self):
        source = (ROOT / "tests" / "valid" / "with_formula.funny").read_text()
        tree, errors = parse(source)
        self.assertEqual(len(errors), 0)

    # --- Программы с ошибками (ожидаем > 0 ошибок благодаря panic mode) ---

    def test_empty_input(self):
        tree, errors = parse("")
        self.assertGreater(len(errors), 0)

    def test_missing_semicolon(self):
        source = (ROOT / "tests" / "invalid" / "missing_semi.funny").read_text()
        tree, errors = parse(source)
        self.assertGreater(len(errors), 0)
        self.assertIn(":", str(errors[0]))  # Проверяем, что есть позиция ошибки

    def test_missing_brace(self):
        source = (ROOT / "tests" / "invalid" / "missing_brace.funny").read_text()
        tree, errors = parse(source)
        self.assertGreater(len(errors), 0)

    def test_invalid_expr(self):
        source = (ROOT / "tests" / "invalid" / "invalid_expr.funny").read_text()
        tree, errors = parse(source)
        self.assertGreater(len(errors), 0)

    def test_missing_paren(self):
        source = (ROOT / "tests" / "invalid" / "missing_paren.funny").read_text()
        tree, errors = parse(source)
        self.assertGreater(len(errors), 0)

    def test_unclosed_parenthesis(self):
        source = (ROOT / "tests" / "invalid" / "unclosed_paren.funny").read_text()
        tree, errors = parse(source)
        self.assertGreater(len(errors), 0)

    def test_extra_token(self):
        source = (ROOT / "tests" / "invalid" / "extra_token.funny").read_text()
        tree, errors = parse(source)
        self.assertGreater(len(errors), 0)

    def test_empty_fixture(self):
        source = (ROOT / "tests" / "invalid" / "empty.funny").read_text()
        tree, errors = parse(source)
        self.assertGreater(len(errors), 0)

    # --- Восстановление panic mode ---

    def test_panic_mode_recovers_after_invalid_statement(self):
        source = (ROOT / "tests" / "invalid" / "panic_invalid_statement.funny").read_text()
        tree, errors = parse(source)

        self.assertEqual(len(tree.declarations), 1)
        self.assertGreater(len(errors), 0)
        body = tree.declarations[0].body
        self.assertEqual(len(body.statements), 2)
        self.assertEqual(body.statements[1].kind, "assert")

    def test_panic_mode_collects_multiple_errors(self):
        source = (ROOT / "tests" / "invalid" / "panic_multiple_errors.funny").read_text()
        tree, errors = parse(source)

        self.assertEqual(len(tree.declarations), 1)
        self.assertGreaterEqual(len(errors), 2)

    def test_panic_mode_recovers_at_declaration_boundary(self):
        source = (ROOT / "tests" / "invalid" / "panic_declaration_boundary.funny").read_text()
        tree, errors = parse(source)

        self.assertEqual(len(errors), 1)
        self.assertEqual(len(tree.declarations), 1)
        self.assertEqual(tree.declarations[0].name, "valid")

    # --- Лексическая ошибка (всё ещё бросает исключение, так как падает лексер) ---

    def test_bad_character(self):
        with self.assertRaises(LexError):
            parse("function f(x: int) returns y: int { y = x @; }")

if __name__ == "__main__":
    unittest.main()