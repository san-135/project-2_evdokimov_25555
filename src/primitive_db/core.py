from typing import Any, Dict, List, Tuple
import prompt


ALLOWED_TYPES = {"int": int, "str": str, "bool": bool}


def normalize_columns(columns: List) -> List[Tuple[str, str]]:
    """Преобразовать список строк вида столбец:тип в пары (имя, тип)."""

    res = []
    for c in columns:
        if ":" not in c:
            raise ValueError(f"Некорректный формат столбца: {c}")
        name, typ = c.split(":", 1)
        name = name.strip()
        typ = typ.strip()
        if not name or not typ:
            raise ValueError(f"Некорректный столбец: {c}")
        res.append((name, typ))
    return res


def validate_types(columns: List[Tuple[str, str]]) -> None:
    for _, typ in columns:
        if typ not in ALLOWED_TYPES:
            raise ValueError(f"Некорректный тип: {typ}")


def create_table(metadata: Dict[str, Any], table_name: str, 
                 columns: List[str]) -> Dict[str, Any]:
    
    if "tables" not in metadata:
        metadata["tables"] = {}

    if table_name in metadata["tables"]:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    parsed = normalize_columns(columns)
    validate_types(parsed)

    # добавляем ID:int в начало
    parsed_with_id = [("ID", "int")] + parsed

    # сохраняем структуру как список словарей
    table_structure = [{"name": n, "type": t} for n, t in parsed_with_id]

    metadata["tables"][table_name] = {
        "structure": table_structure
    }

    print(f'Таблица "{table_name}" успешно создана со столбцами: ' +
          ", ".join([f'{n}:{t}' for n, t in parsed_with_id]))
    return metadata


def drop_table(metadata: Dict[str, Any], table_name: str) -> Dict[str, Any]:
    if "tables" not in metadata or table_name not in metadata["tables"]:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata["tables"][table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata: Dict[str, Any]) -> List[str]:
    if "tables" not in metadata:
        return []
    return list(metadata["tables"].keys())


def help() -> None:
    print(
        "Функции:<command> create_table <имя_таблицы> <столбец1:тип> "
        "<столбец2:тип> .. - создать таблицу\n"
        "<command> list_tables - показать список всех таблиц\n"
        "<command> drop_table <имя_таблицы> - удалить таблицу\n"
        "<command> exit - выход из программы\n"
        "<command> help - справочная информация"
    )
