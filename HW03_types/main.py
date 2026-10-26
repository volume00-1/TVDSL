"""Точка входа для HW3: лексер + парсер + семантический анализ."""
import argparse
import json
import sys
from lexer import tokenize, LexError
from parser import Parser, ParseError
from semantic_analyzer import SemanticAnalyzer


def main() -> int:
    cli = argparse.ArgumentParser(description="Семантический анализатор языка Funny")
    cli.add_argument("file", nargs="?", help="Файл с программой на Funny; stdin если не указан")
    cli.add_argument("--no-semantic", action="store_true", help="Только парсинг, без семантического анализа")
    args = cli.parse_args()
    
    source = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    
    try:
        tokens = tokenize(source)
        parser = Parser(tokens)
        ast_tree = parser.parse()
        
        if parser.errors:
            for err in parser.errors:
                print(f"Синтаксическая ошибка: {err}", file=sys.stderr)
            return 1
        
        if not args.no_semantic:
            analyzer = SemanticAnalyzer()
            semantic_errors = analyzer.analyze(ast_tree)
            
            if semantic_errors:
                for err in semantic_errors:
                    print(f"Семантическая ошибка: {err}", file=sys.stderr)
                return 1
        
        print(json.dumps(ast_tree.to_dict(), ensure_ascii=False, indent=2))
        return 0
        
    except LexError as error:
        print(f"Лексическая ошибка: {error}", file=sys.stderr)
        return 1
    except ParseError as error:
        print(f"Синтаксическая ошибка: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Неожиданная ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())