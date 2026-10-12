# HW2: Парсер языка Funny

Реализация LL(1)-парсера для языка Funny с построением абстрактного синтаксического дерева (AST) и режимом восстановления после ошибок (panic mode).

## Описание

Проект реализует синтаксический анализатор языка Funny, который:

1. Принимает текст программы на языке Funny
2. Разбивает его на токены (лексический анализ)
3. Проверяет синтаксическую корректность (синтаксический анализ)
4. Строит абстрактное синтаксическое дерево (AST)
5. Выводит AST в формате JSON или список ошибок с позициями

Язык Funny предназначен для верификации императивных программ. Он поддерживает функции с предусловиями и постусловиями, циклы с инвариантами, кванторы и формулы.

## Требования

- Python 3.10 или новее
- Никаких внешних библиотек не требуется

## Быстрый старт

### Запуск парсера

```bash
python main.py examples/max_function.funny
```

### Анализ из стандартного ввода

```bash
echo 'function f(x: int) returns y: int { y = x; }' | python main.py
```

### Вывод в файл

```bash
python main.py examples/max_function.funny > output.json
```

### Запуск тестов

```bash
python -m unittest test_parser.py -v
```

## Структура проекта

```
HW02_parsing/
├── main.py              # Точка входа
├── lexer.py             # Лексический анализатор
├── parser.py            # Синтаксический анализатор (LL(1), рекурсивный спуск)
├── ast_nodes.py         # Классы узлов AST
├── grammar.txt          # Грамматика языка Funny в EBNF
├── test_parser.py       # Набор тестов (13 тестов)
├── README.md            # Этот файл
├── tests/
│   ├── valid/           # Корректные программы
│   │   ├── simple.funny
│   │   ├── with_invariant.funny
│   │   ├── complex_expr.funny
│   │   └── with_formula.funny
│   └── invalid/         # Программы с ошибками
│       ├── missing_semi.funny
│       ├── missing_brace.funny
│       ├── invalid_expr.funny
│       ├── missing_paren.funny
│       ├── unclosed_paren.funny
│       ├── extra_token.funny
│       └── empty.funny
── examples/
    └── max_function.funny
```

## Поддерживаемые конструкции

### Объявления

- Функции: `function name(params) requires pred returns vars ensures pred uses vars { body }`
- Формулы: `function name(params) => predicate`

### Операторы

- Присваивание: `x = expr;`, `a[i] = expr;`, `x, y = f();`
- Условный: `if (cond) stmt [else stmt]`
- Цикл: `while (cond) [invariant pred] stmt`
- Блок: `{ stmt* }`
- Утверждения: `assert pred;`, `assume pred;`

### Выражения

- Арифметика: `+`, `-`, `*`, `/`, унарный `-`
- Сравнения: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Вызовы функций: `f(args)`
- Обращение к массиву: `a[i]`
- Скобки: `(expr)`

### Предикаты

- Булевы константы: `true`, `false`
- Логические операции: `and`, `or`, `not`, `->` (импликация)
- Кванторы: `forall x: int | pred`, `exists x: int | pred`
- Ссылки на формулы: `formula(args)`

## Грамматика

Полная грамматика языка Funny в формате EBNF находится в файле `grammar.txt`.

Основные правила:

```
module      = decl { decl } ;
decl        = IDENT "(" [ varDefs ] ")" declRest ;
declRest    = "=>" predicate
            | [ "requires" predicate ] "returns" varDefs
              [ "ensures" predicate ] [ "uses" varDefs ] statement ;

statement   = assignment | conditional | loop | block | assertion ;
assignment  = IDENT "=" expr ";"
            | IDENT "[" expr "]" "=" expr ";"
            | IDENT "," IDENT { "," IDENT } "=" call ";" ;

expr        = term { ("+" | "-") term } ;
term        = unary { ("*" | "/") unary } ;
unary       = "-" unary | primary ;
primary     = INT | IDENT | IDENT "[" expr "]" | call | "(" expr ")" ;

predicate   = implies ;
implies     = or [ "->" implies ] ;
or          = and { "or" and } ;
and         = not { "and" not } ;
not         = "not" not | atom ;
atom        = "true" | "false" | expr cmp expr | "(" implies ")"
            | quantifier | formulaRef ;
```

Приоритеты операторов:

- Арифметика: унарный `-` > `*`, `/` > `+`, `-` (все левоассоциативны)
- Булевы: `not` > `and` > `or` > `->` (and/or левоассоциативны, `->` правоассоциативна)
- `else` относится к ближайшему `if`

## Формат AST

Каждый узел AST имеет поле `type`, указывающее его тип. Пример вывода для программы:

```funny
function max(a: int, b: int)
    returns r: int
{
    if (a > b) { r = a; } else { r = b; }
}
```

Результат в JSON:

```json
{
  "type": "Module",
  "declarations": [
    {
      "type": "Function",
      "name": "max",
      "params": [
        {"type": "VarDef", "name": "a", "type": "int"},
        {"type": "VarDef", "name": "b", "type": "int"}
      ],
      "returns": [
        {"type": "VarDef", "name": "r", "type": "int"}
      ],
      "requires": null,
      "ensures": null,
      "uses": [],
      "body": {
        "type": "Block",
        "statements": [
          {
            "type": "If",
            "condition": {
              "type": "Compare",
              "op": ">",
              "left": {"type": "Name", "name": "a"},
              "right": {"type": "Name", "name": "b"}
            },
            "then_branch": {
              "type": "Block",
              "statements": [
                {
                  "type": "Assignment",
                  "targets": [{"type": "Name", "name": "r"}],
                  "value": {"type": "Name", "name": "a"}
                }
              ]
            },
            "else_branch": {
              "type": "Block",
              "statements": [
                {
                  "type": "Assignment",
                  "targets": [{"type": "Name", "name": "r"}],
                  "value": {"type": "Name", "name": "b"}
                }
              ]
            }
          }
        ]
      }
    }
  ]
}
```

### Типы узлов AST

**Модуль:**
- `Module` — корневой узел программы (список объявлений)

**Объявления:**
- `Function` — объявление функции
- `Formula` — объявление формулы
- `VarDef` — определение переменной (имя и тип)

**Операторы:**
- `Block` — блок операторов
- `If` — условный оператор
- `While` — цикл while
- `Assert` — утверждение (assert/assume)
- `Assignment` — присваивание

**Выражения:**
- `IntLiteral` — целое число
- `BoolLiteral` — булева константа
- `Name` — имя переменной
- `BinaryOp` — бинарная операция (+, -, *, /, and, or, ->)
- `UnaryOp` — унарная операция (not, -)
- `Compare` — сравнение (==, !=, <, >, <=, >=)
- `Call` — вызов функции
- `ArrayAccess` — обращение к элементу массива
- `Quantifier` — квантор (forall, exists)

## Алгоритмы

### Лексический анализ

Лексер использует регулярные выражения для разбиения текста на токены. Поддерживает:

- Ключевые слова языка (function, returns, if, while, assert, assume и др.)
- Идентификаторы и числа
- Операторы и разделители (==, !=, <=, >=, =>, ->, +, -, *, /, =, <, >, (, ), [, ], {, }, ,, ;, :, |)
- Пробелы и комментарии (пропускаются)
- Позиции токенов (строка, колонка) для сообщений об ошибках

### Синтаксический анализ

Рекурсивный спуск (LL(1)):

- Каждое правило грамматики реализовано как отдельный метод парсера
- Односимвольное предпросмотр (lookahead = 1)
- Метод `expect()` проверяет и съедает ожидаемый токен
- Метод `accept()` пытается съесть токен, возвращает None если не совпал

### Обработка ошибок (Panic Mode)

При обнаружении синтаксической ошибки парсер:

1. Записывает ошибку с позицией (строка:колонка) в список
2. Вызывает метод синхронизации (`sync_stmt()` или `sync_decl()`)
3. Пропускает токены до безопасной точки:
   - Внутри блока: до `;`, `}`, или начала нового оператора (if, while, assert, assume)
   - На уровне модуля: до следующего ключевого слова `function`
4. Продолжает анализ для поиска следующих ошибок

Это позволяет найти все ошибки в программе за один проход, а не только первую.

## Тестирование

Проект включает 13 тестов, покрывающих:

**Корректные программы (4 теста):**
- Простая функция с if-else
- Цикл while с инвариантом
- Сложные арифметические выражения с приоритетами
- Функция с предусловием и постусловием

**Программы с ошибками (8 тестов):**
- Пустой ввод
- Пропущенные точки с запятой
- Незакрытые скобки и блоки
- Некорректные выражения
- Лишние токены
- Пустой файл

**Лексические ошибки (1 тест):**
- Недопустимые символы

**Panic mode (1 тест):**
- Программа с несколькими ошибками — проверка, что парсер находит все ошибки, а не падает на первой

## Обработка ошибок

Парсер выводит ошибки в формате:

```
Ошибка: ожидался SEMICOLON, получен RBRACE в позиции 3:1
```

Код возврата:

- `0` — ошибок нет, AST выведен в stdout
- `1` — есть ошибки, выведены в stderr

## Примеры программ

### Функция с инвариантом цикла

```funny
function binary_search(a: int[], n: int, target: int)
    returns result: int
{
    result = -1;
    low = 0;
    high = n - 1;
    while (low <= high)
        invariant 0 <= low and high < n
    {
        mid = (low + high) / 2;
        if (a[mid] == target) {
            result = mid;
        } else {
            if (a[mid] < target) {
                low = mid + 1;
            } else {
                high = mid - 1;
            }
        }
    }
}
```

### Формула с квантором

```funny
function all_positive(a: int[], n: int)
    returns b: int
{
    assert forall i: int | i >= 0 and i < n -> a[i] > 0;
    b = 1;
}
```

## Отклонения от funny.ru.md

В процессе реализации были зафиксированы следующие отличия от документации `funny.ru.md`:

1. **Ключевое слово `function` для формул.** 
   В `funny.ru.md` формула начинается сразу с идентификатора (`formula = identifier "(" ...`). 
   В нашей реализации формулы начинаются со слова `function` (`function identifier "(" ... "=>" predicate`), чтобы унифицировать парсинг объявлений на верхнем уровне и избежать конфликта FIRST-множеств с вызовами функций в выражениях.

2. **Обязательность типа для локальных переменных.** 
   В `funny.ru.md` локальные переменные могут опускать тип (`localVarDef = identifier [ ":" variableType ]`), предполагая вывод типов. 
   В нашей реализации парсер требует явного указания типа (`identifier ":" variableType`), так как вывод типов не входит в задачи синтаксического анализатора (это задача семантического этапа).

3. **Токенизация `=>` и `->`.**
   В лексере явно выделены токены `FAT_ARROW` (`=>`) для тела формулы и `ARROW` (`->`) для логической импликации, чтобы парсер мог однозначно различать их на этапе LL(1)-разбора.

## Ссылки

- Документация языка Funny: `funny.ru.md`
- Грамматика: `grammar.txt`
- Примеры программ: папка `examples/`
- Тесты: папка `tests/`

---

Проект выполнен в рамках курса "Теория языков и методов трансляции"