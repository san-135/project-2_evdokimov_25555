import shlex
from typing import List

from .core import create_table, drop_table, help, list_tables
from .utils import load_metadata, save_metadata

META_PATH = "db_meta.json"


def _print_list(items: List[str]) -> None:
    """
    Печать списка в формате:
    - item
    - item
    - ...
    """
    for name in items:
        print(f"- {name}")


def run() -> None:
    """
    Основной цикл: загрузка метаданных, чтение команд, обработка и сохранение.
    """
    metadata = load_metadata(META_PATH)
    print("База данных запущена. Введите команду. help для справки.")

    while True:
        try:
            user_input = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        try:
            tokens = shlex.split(user_input)
        except ValueError as exc:
            print(f"Некорректное значение: {exc}. Попробуйте снова.")
            continue

        cmd = tokens[0].lower()
        match cmd:
            case "exit" | "quit" | "q":
                break

            case "help":
                help()
                continue

            case "create_table":
                if len(tokens) < 3:
                    print("Некорректное значение: ожидались имя и столбцы. Попробуйте снова.")
                    continue

                table_name = tokens[1]
                columns = tokens[2:]
                try:
                    metadata = create_table(metadata, table_name, columns)
                    save_metadata(META_PATH, metadata)
                except ValueError as exc:
                    print(f"Некорректное значение: {exc}. Попробуйте снова.")
                continue

            case "drop_table":
                if len(tokens) != 2:
                    print("Некорректное значение: ожидалось имя таблицы. Попробуйте снова.")
                    continue

                table_name = tokens[1]
                metadata = drop_table(metadata, table_name)
                save_metadata(META_PATH, metadata)
                continue

            case "list_tables":
                names = list_tables(metadata)
                _print_list(names)
                continue

        print(f"Функции {cmd} нет. Попробуйте снова.")

    print("Выход из программы.")
