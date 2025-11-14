# src/primitive_db/engine.py
import shlex
from typing import Any, Dict, List

from prettytable import PrettyTable

from .core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    table_info,
    update,
)
from .core import (
    help as print_help,
)
from .parser import (
    parse_delete,
    parse_info,
    parse_insert,
    parse_select,
    parse_update,
)
from .utils import load_metadata, load_table_data, save_metadata, save_table_data

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


def _field_order(metadata: Dict[str, Any], table_name: str) -> List[str]:
    structure = metadata["tables"][table_name]["structure"]
    return [c["name"] for c in structure]


def _print_table(rows: List[Dict[str, Any]], headers: List[str]) -> None:
    table = PrettyTable()
    table.field_names = headers
    for rec in rows:
        table.add_row([rec.get(h) for h in headers])
    print(table)


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

        if not tokens:
            continue

        cmd = tokens[0].lower()

        match cmd:
            case "exit" | "quit" | "q":
                break

            case "help":
                print_help()
                continue

            case "create_table":
                if len(tokens) < 3:
                    print("Некорректное значение: ожидались имя и столбцы. "
                          "Попробуйте снова.")
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
                    print("Некорректное значение: ожидалось имя таблицы. "
                          "Попробуйте снова.")
                    continue
                table_name = tokens[1]
                metadata = drop_table(metadata, table_name)
                save_metadata(META_PATH, metadata)
                continue

            case "list_tables":
                names = list_tables(metadata)
                _print_list(names)
                continue
            case "insert":
                table_name, values = parse_insert(user_input)
                if "tables" not in metadata or table_name not in metadata["tables"]:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue
                data = load_table_data(table_name)
                data, new_id = insert(metadata, table_name, values, data)
                save_table_data(table_name, data)
                print(f'Запись с ID={new_id} успешно добавлена в таблицу '
                      '"{table_name}".')
                continue

            case "select ":
                table_name, where = parse_select(user_input)
                if "tables" not in metadata or table_name not in metadata["tables"]:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue
                data = load_table_data(table_name)
                rows = select(data, where)
                headers = _field_order(metadata, table_name)
                _print_table(rows, headers)
                continue

            case "update ":
                table_name, set_clause, where = parse_update(user_input)
                if "tables" not in metadata or table_name not in metadata["tables"]:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue
                data = load_table_data(table_name)
                data, updated_ids = update(metadata, table_name, 
                                           data, set_clause, where)
                save_table_data(table_name, data)
                if len(updated_ids) == 1:
                    print(f'Запись с ID={updated_ids[0]} в таблице "{table_name}" '
                          'успешно обновлена.')
                else:
                    print(f"Обновлено записей: {len(updated_ids)}")
                continue

            case "delete ":
                table_name, where = parse_delete(user_input)
                if "tables" not in metadata or table_name not in metadata["tables"]:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue
                data = load_table_data(table_name)
                data, deleted_ids = delete(data, where)
                save_table_data(table_name, data)
                if len(deleted_ids) == 1:
                    print(f'Запись с ID={deleted_ids[0]} успешно удалена из таблицы '
                          '"{table_name}".')
                else:
                    print(f"Удалено записей: {len(deleted_ids)}")
                continue

            case "info ":
                table_name = parse_info(user_input)
                if "tables" not in metadata or table_name not in metadata["tables"]:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue
                data = load_table_data(table_name)
                cols_str, count = table_info(metadata, table_name, data)
                print(f"Таблица: {table_name}")
                print(f"Столбцы: {cols_str}")
                print(f"Количество записей: {count}")
                continue

        print(f"Функции {cmd} нет. Попробуйте снова.")

    print("Выход из программы.")