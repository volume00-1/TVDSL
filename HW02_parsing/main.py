import argparse
import json
import sys
from lexer import LexError
from parser import parse

def main() -> int:
    cli = argparse.ArgumentParser(description="LL(1) parser for Funny")
    cli.add_argument("file", nargs="?", help="Funny source file; stdin if omitted")
    args = cli.parse_args()
    
    source = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    
    try:
        tree, errors = parse(source)
        
        if errors:
            for err in errors:
                print(f"Ошибка: {err}", file=sys.stderr)
            return 1
        
        print(json.dumps(tree.to_dict(), ensure_ascii=False, indent=2))
        return 0
    except LexError as error:
        print(f"Лексическая ошибка: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Неожиданная ошибка: {error}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())