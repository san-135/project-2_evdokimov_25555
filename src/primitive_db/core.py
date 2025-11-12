from typing import Any, Dict, List, Tuple

ALLOWED_TYPES: Dict[str, type] = {"int": int, "str": str, "bool": bool}


def normalize_columns(columns: List[str]) -> List[Tuple[str, str]]:
    """
    Преобразовать список строк "столбец:тип" в пары (имя, тип).
    """
    result: List[Tuple[str, str]] = []
    for col in columns:
        if ":" not in col:
            raise ValueError(f"Некорректный формат столбца: {col}")
        name, typ = col.split(":", 1)
        name = name.strip()
        typ = typ.strip()
        if not name or not typ:
            raise ValueError(f"Некорректный столбец: {col}")
        result.append((name, typ))
    return result


def validate_types(columns: List[Tuple[str, str]]) -> None:
    """
    Проверка типов столбцов на вхождение в ALLOWED_TYPES.
    """
    for _, typ in columns:
        if typ not in ALLOWED_TYPES:
            raise ValueError(f"Некорректный тип: {typ}")


def create_table(
    metadata: Dict[str, Any],
    table_name: str,
    columns: List[str],
) -> Dict[str, Any]:
    """
    Создать таблицу: добавить ID:int, проверить существование, проверять типы, 
    обновить metadata и вернуть словарь.
    """
    metadata.setdefault("tables", {})
    if table_name in metadata["tables"]:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    parsed = normalize_columns(columns)
    validate_types(parsed)

    parsed_with_id = [("ID", "int")] + parsed
    table_structure = [{"name": n, "type": t} for n, t in parsed_with_id]

    metadata["tables"][table_name] = {"structure": table_structure}

    cols_str = ", ".join(f"{n}:{t}" for n, t in parsed_with_id)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_str}')
    return metadata


def drop_table(metadata: Dict[str, Any], table_name: str) -> Dict[str, Any]:
    """
    Удалить таблицу: проверить существование и обновить metadata.
    """
    tables = metadata.get("tables", {})
    if table_name not in tables:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del tables[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata: Dict[str, Any]) -> List[str]:
    """
    Вернуть список имён всех таблиц.
    """
    return list(metadata.get("tables", {}).keys())


def help() -> None:
    print(
        "Функции:\n"
        "<command> create_table <имя_таблицы> <столбец1:тип> "
        "<столбец2:тип> .. - создать таблицу\n"
        "<command> list_tables - показать список всех таблиц\n"
        "<command> drop_table <имя_таблицы> - удалить таблицу\n"
        "<command> exit - выход из программы\n"
        "<command> help - справочная информация"
    )
