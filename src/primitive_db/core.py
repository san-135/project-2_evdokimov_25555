from typing import Any, Dict, List, Optional, Tuple

from src.constants import ALLOWED_TYPES
from src.decorators import confirm_action, handle_errors, log_time


def _normalize_columns(columns: List[str]) -> List[Tuple[str, str]]:
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


def _validate_types(columns: List[Tuple[str, str]]) -> None:
    """
    Проверка типов столбцов на вхождение в ALLOWED_TYPES.
    """
    for _, typ in columns:
        if typ not in ALLOWED_TYPES:
            raise ValueError(f"Некорректный тип: {typ}")


@handle_errors
def _get_schema(metadata: Dict[str, Any], table_name: str) -> List[Dict[str, str]]:
    if "tables" not in metadata or table_name not in metadata["tables"]:
        raise ValueError(f'Таблица "{table_name}" не существует')
    return metadata["tables"][table_name]["structure"]


def _type_name_to_type(type_name: str):
    if type_name not in ALLOWED_TYPES:
        raise ValueError(f"Некорректный тип: {type_name}")
    return ALLOWED_TYPES[type_name]


def _validate_value(py_value: Any, expected_type_name: str) -> None:
    py_type = _type_name_to_type(expected_type_name)
    if not isinstance(py_value, py_type):
        raise ValueError(f"Ожидался тип {expected_type_name}, "
                         "получено {type(py_value).__name__}")


def _next_id(rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 1
    return max(int(r.get("ID", 0)) for r in rows) + 1


@handle_errors
def create_table(metadata: Dict[str, Any], table_name: str, 
                 columns: List[str]) -> Dict[str, Any]:
    if "tables" not in metadata:
        metadata["tables"] = {}

    if table_name in metadata["tables"]:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    parsed = _normalize_columns(columns)
    _validate_types(parsed)

    # Добавляем ID:int в начало
    parsed_with_id = [("ID", "int")] + parsed

    # Сохраняем структуру как список словарей
    table_structure = [{"name": n, "type": t} for n, t in parsed_with_id]
    metadata["tables"][table_name] = {"structure": table_structure}

    cols_str = ", ".join(f"{n}:{t}" for n, t in parsed_with_id)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_str}')
    return metadata


@confirm_action("удаление таблицы")
@handle_errors
def drop_table(metadata: Dict[str, Any], table_name: str) -> Dict[str, Any]:
    """
    Удалить таблицу: проверить существование и обновить metadata.
    """
    if "tables" not in metadata or table_name not in metadata["tables"]:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata["tables"][table_name]
    
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


@handle_errors
def list_tables(metadata: Dict[str, Any]) -> List[str]:
    if "tables" not in metadata:
        return []
    return list(metadata["tables"].keys())


@handle_errors
def help() -> str:
    print(
        "Функции:\n"
        "<command> create table <имя_таблицы> <столбец1:тип> <столбец2:тип> .. - создать таблицу\n" # NOQA E501
        "<command> list tables - показать список всех таблиц\n"
        "<command> drop table <имя_таблицы> - удалить таблицу\n"
        "<command> insert into <имя_таблицы> values (<v1>, <v2>, ...), (...) - создать запись (без ID)\n"  # NOQA E501
        "<command> select from <имя_таблицы> [where <столбец>=<значение>] - прочитать записи\n"   # NOQA E501
        "<command> update <имя_таблицы> set <столбец>=<значение>[, ...] where <столбец>=<значение> - обновить\n"    # NOQA E501
        "<command> delete from <имя_таблицы> where <столбец>=<значение> - удалить\n"  # NOQA E501
        "<command> info <имя_таблицы> - информация о таблице\n"
        "<command> exit - выход из программы\n"
        "<command> help - справочная информация\n"
        "Значения строк необходимо писать в кавычках, а названия таблиц и столбцов - без"   # NOQA E501
    )


# ===== CRUD =====

@log_time
@handle_errors
def insert(
    metadata: Dict[str, Any],
    table_name: str,
    rows: List[Dict[str, Any]],
    values_list: List[List[Any]]
) -> List[Dict[str, Any]]:
    schema = _get_schema(metadata, table_name)
    non_id_columns = [n for n in schema if n["name"] != "ID"]
    
    # Проверяем все группы значений
    for values in values_list:
        if len(values) != len(non_id_columns):
            raise ValueError(
                f"Ожидалось {len(non_id_columns)} значений, "
                f"получено {len(values)}"
            )
    
    for values in values_list:
        # Валидация типов
        for val, col in zip(values, non_id_columns):
            _validate_value(val, col["type"])
        
        new_row = {"ID": _next_id(rows)}
        for val, col in zip(values, non_id_columns):
            new_row[col["name"]] = val
        rows.append(new_row)
    
    return rows



def match(
    row: Dict[str, Any], 
    where: Optional[Dict[str, Any]]
) -> bool:
    if not where:
        return True
    for k, v in where.items():
        if row.get(k) != v:
            return False
    return True


@handle_errors
@log_time
def select(
    rows: List[Dict[str, Any]], 
    where: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Возвращает все записи или фильтрует по where_clause (равенство, AND).
    """
    if not where:
        return list(rows)
    return [r for r in rows if match(r, where)]


@handle_errors
def update(
    metadata: Dict[str, Any], 
    table_name: str,
    rows: List[Dict[str, Any]],
    set_clause: Dict[str, Any],
    where: Dict[str, Any]
) -> int:
    """
    Обновляет записи по where_clause значениями из set_clause.
    Возвращает количество обновлённых строк.
    """
    schema = _get_schema(metadata, table_name)  
    col_types = {c["name"]: c["type"] for c in schema}
    if "ID" in set_clause:
        raise ValueError("Нельзя изменять столбец ID")
    # Валидация set значений
    for k, v in set_clause.items():
        if k not in col_types:
            raise ValueError(f'Неизвестный столбец: {k}')
        _validate_value(v, col_types[k])
    count = 0
    for r in rows:
        if match(r, where):
            for k, v in set_clause.items():
                r[k] = v
            count += 1
    return count


@confirm_action("удаление записей")
@handle_errors
def delete(
    rows: List[Dict[str, Any]], 
    where: Dict[str, Any]
) -> int:
    """
    Удаляет записи по where_clause.
    Возвращает количество удаленных строк.
    """
    before = len(rows)
    remaining = [r for r in rows if not match(r, where)]
    deleted = before - len(remaining)
    rows.clear()
    rows.extend(remaining)
    return deleted
