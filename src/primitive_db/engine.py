from typing import Any, Dict, List, Optional, Tuple

from prettytable import PrettyTable

from src.decorators import create_cacher
from .core import (
    _get_schema,
    create_table,
    drop_table,
    help,
    list_tables,
)
from .core import delete as core_delete
from .core import insert as core_insert
from .core import select as core_select
from .core import update as core_update
from .parser import parse_command
from .utils import (
    META_PATH,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def _print_table(schema: List[Dict[str, str]], rows: List[Dict[str, Any]]) -> None:
    headers = [c["name"] for c in schema]
    t = PrettyTable()
    t.field_names = headers
    for r in rows:
        t.add_row([r.get(h) for h in headers])
    print(t)


def run():
    metadata: Dict[str, Any] = load_metadata(META_PATH)
    # Кэшер
    select_cache = create_cacher()

    print("База данных запущена. Введите help для справки.")

    while True:
        try:
            user_input = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        try:
            com = parse_command(user_input)
        except ValueError:
            print(ValueError)
            continue


        ctype = com["cmd"]
        match ctype:

            case "exit":
                break
                
            case "help":
                help()

            case "create_table":
                table = com["table"]
                columns = com["columns"]
                metadata = create_table(metadata, table, columns)
                save_metadata(META_PATH, metadata)



            case "drop_table":
                table = com["table"]
                metadata = drop_table(metadata, table)
                save_metadata(META_PATH, metadata)
                # Сброс кэша
                select_cache = create_cacher()

            case "list_tables":
                names = list_tables(metadata)
                print("tables - " + (", ".join(names) if names else ""))

            case "insert":
                table = com["table"]
                values = com["values"]
                if "tables" not in metadata or table not in metadata["tables"]:
                    print(f'Ошибка: Таблица "{table}" не существует.')
                    continue
                rows = load_table_data(table)
                # Правильно передаем аргументы
                rows = core_insert(metadata, table, rows, values)
                save_table_data(table, rows)
                select_cache = create_cacher()
                if rows:
                    new_id = rows[-1]["ID"]
                    print(f'Запись с ID={new_id} добавлена в таблицу "{table}".')

            case "select":
                table = com["table"]
                where = com.get("where")
                if "tables" not in metadata or table not in metadata["tables"]:
                    print(f'Ошибка: Таблица "{table}" не существует.')
                    continue

                rows = load_table_data(table)
                schema = _get_schema(metadata, table)

                # Ключ кэша: (table, where-как-кортеж)
                where_key: Optional[Tuple[Tuple[str, Any], ...]] = None
                if where:
                    where_key = tuple(sorted(where.items()))

                key = (table, where_key)

                def _value():
                    return core_select(rows, where)

                result = select_cache(key, _value)
                if result:
                    _print_table(schema, result)
                else:
                    print("Нет данных по заданному запросу.")

            case "update":
                table = com["table"]
                set_clause = com["set"]
                where = com["where"]
                if "tables" not in metadata or table not in metadata["tables"]:
                    print(f'Ошибка: Таблица "{table}" не существует.')
                    continue
                rows = load_table_data(table)
                changed = core_update(metadata, table, rows, set_clause, where)
                save_table_data(table, rows)
                # Сброс кэша после изменения данных
                select_cache = create_cacher()
                if changed == 1 and "ID" in where:
                    print(f'Запись с ID={where["ID"]} в таблице "{table}" '
                            'успешно обновлена.')
                else:
                    print(f"Обновлено записей: {changed}.")

            case "delete":
                table = com["table"]
                where = com["where"]
                rows = load_table_data(table)
                deleted = core_delete(rows, where)
                save_table_data(table, rows)
                # Сброс кэша после изменения данных
                select_cache = create_cacher()
                if deleted == 1 and "ID" in where:
                    print(f'Запись с ID={where["ID"]} успешно удалена '
                            'из таблицы "{table}".')
                else:
                    print(f"Удалено записей: {deleted}.")

            case "info":
                table = com["table"]
                if "tables" not in metadata or table not in metadata["tables"]:
                    print(f'Ошибка: Таблица "{table}" не существует.')
                    continue
                schema = _get_schema(metadata, table)
                rows = load_table_data(table)
                cols = ", ".join(f'{c["name"]}:{c["type"]}' for c in schema)
                print(f"Таблица: {table}")
                print(f"Столбцы: {cols}")
                print(f"Количество записей: {len(rows)}")

            case _:
                print(f"Функция {com} неизвестна. Попробуйте снова.")


    print("Выход из программы.")