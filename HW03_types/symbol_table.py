"""Таблицы символов для семантического анализа языка Funny."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Symbol:
    """Информация об одном имени (переменная, функция, параметр)."""
    name: str           # имя (например, "x", "max")
    type: str           # тип ("int", "int[]", "bool", "function")
    role: str           # роль: "parameter", "return", "local", "function", "formula"
    line: int = 0       # строка объявления (для сообщений об ошибках)
    column: int = 0     # колонка объявления
    # Для функций:
    param_types: list = field(default_factory=list)  # типы параметров
    return_types: list = field(default_factory=list) # типы возвращаемых значений


class Scope:
    """Одна область видимости (например, тело функции)."""
    
    def __init__(self, name: str = "", parent: Optional['Scope'] = None):
        self.name = name              # имя области (например, "function max")
        self.parent = parent          # родительская область (для вложенности)
        self.symbols: dict[str, Symbol] = {}  # имена → символы
    
    def add(self, symbol: Symbol) -> bool:
        """Добавить символ. Возвращает True если успешно, False если имя уже занято."""
        if symbol.name in self.symbols:
            return False  # повторное объявление
        self.symbols[symbol.name] = symbol
        return True
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """Найти символ в текущей области. Возвращает None если не найдено."""
        return self.symbols.get(name)
    
    def lookup_in_chain(self, name: str) -> Optional[Symbol]:
        """Найти символ в текущей области и всех родительских (вплоть до глобальной)."""
        scope = self
        while scope is not None:
            symbol = scope.lookup(name)
            if symbol is not None:
                return symbol
            scope = scope.parent
        return None


class SymbolTable:
    """Управляет стеком областей видимости."""
    
    def __init__(self):
        # Создаём глобальную область (модуль)
        self.global_scope = Scope(name="module")
        self.current_scope = self.global_scope
        self.errors: list[str] = []  # список ошибок
    
    def enter_scope(self, name: str = ""):
        """Войти в новую область видимости (например, тело функции)."""
        new_scope = Scope(name=name, parent=self.current_scope)
        self.current_scope = new_scope
    
    def exit_scope(self):
        """Выйти из текущей области видимости (вернуться к родительской)."""
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent
    
    def add_symbol(self, symbol: Symbol) -> bool:
        """Добавить символ в текущую область. Возвращает True если успешно."""
        if not self.current_scope.add(symbol):
            # Имя уже занято в этой области
            existing = self.current_scope.lookup(symbol.name)
            self.errors.append(
                f"строка {symbol.line}, колонка {symbol.column}: "
                f"повторное объявление '{symbol.name}' "
                f"(ранее объявлено в строке {existing.line}, колонке {existing.column})"
            )
            return False
        return True
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """Найти символ в текущей области и всех родительских."""
        return self.current_scope.lookup_in_chain(name)
    
    def error(self, message: str):
        """Добавить ошибку."""
        self.errors.append(message)