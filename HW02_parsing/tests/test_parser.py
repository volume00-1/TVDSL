import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lexer import LexError
from parser import parse

TESTS = ROOT / "tests"


class ParserTests(unittest.TestCase):
    def assert_matches_expected_tree(self, source_path: pathlib.Path):
        source = source_path.read_text(encoding="utf-8")
        expected_path = TESTS / "expected" / f"{source_path.stem}.json"

        tree, errors = parse(source)
        actual = tree.to_dict()
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        self.assertEqual(actual, expected)
        return errors

    def test_valid_fixtures(self):
        for source_path in sorted((TESTS / "valid").glob("*.funny")):
            with self.subTest(fixture=source_path.name):
                errors = self.assert_matches_expected_tree(source_path)
                self.assertEqual(errors, [])

    def test_invalid_fixtures(self):
        for source_path in sorted((TESTS / "invalid").glob("*.funny")):
            with self.subTest(fixture=source_path.name):
                errors = self.assert_matches_expected_tree(source_path)
                self.assertGreater(len(errors), 0)

    def test_missing_semicolon_reports_position(self):
        source_path = TESTS / "invalid" / "missing_semi.funny"
        errors = self.assert_matches_expected_tree(source_path)
        self.assertIn(":", str(errors[0]))

    def test_panic_mode_collects_multiple_errors(self):
        source_path = TESTS / "invalid" / "panic_multiple_errors.funny"
        errors = self.assert_matches_expected_tree(source_path)
        self.assertGreaterEqual(len(errors), 2)

    def test_panic_mode_recovers_at_declaration_boundary(self):
        source_path = TESTS / "invalid" / "panic_declaration_boundary.funny"
        errors = self.assert_matches_expected_tree(source_path)
        self.assertEqual(len(errors), 1)

    def test_bad_character(self):
        with self.assertRaises(LexError):
            parse("function f(x: int) returns y: int { y = x @; }")


if __name__ == "__main__":
    unittest.main()
