from typing import Any, Dict, List, Tuple, Optional

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


def _schema_for_table(
    metadata: Dict[str, Any], 
    table_name: str,
) -> List[Tuple[str, str]]:
    """
    Возвращает схему таблицы в виде списка (name, type) в порядке колонок.
    """
    tables = metadata.get("tables", {})
    if table_name not in tables:
        raise ValueError(f'Таблица "{table_name}" не существует')
    structure = tables[table_name]["structure"]
    return [(c["name"], c["type"]) for c in structure]


def _cast_to_type(value: Any, type_name: str) -> Any:
    """
    Приведение value к типу type_name с валидацией.
    """
    t = ALLOWED_TYPES[type_name]
    # Специальные правила для bool: 
    # принимаем только истинный bool или строки 'true'/'false'
    if type_name == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in ("true", "false"):
            return value.strip().lower() == "true"
        raise ValueError(f"Ожидался тип bool, получено: {value!r}")
    # Для int: int или числовая строка
    if type_name == "int":
        if isinstance(value, bool):
            # Не считать bool валидным int
            raise ValueError(f"Ожидался тип int, получено: {value!r}")
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            v = value.strip()
            if v and (v.isdigit() or (v.startswith("-") and v[1:].isdigit())):
                return int(v)
        raise ValueError(f"Ожидался тип int, получено: {value!r}")
    # Для str: только строки
    if type_name == "str":
        if isinstance(value, str):
            return value
        raise ValueError(f"Ожидался тип str, получено: {value!r}")
    # Общий случай
    if isinstance(value, t):
        return value
    raise ValueError(f"Ожидался тип {type_name}, получено: {value!r}")


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
        "<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> .. - создать таблицу\n"                                     # NOQA E501
        "<command> list_tables - показать список всех таблиц\n"
        "<command> drop_table <имя_таблицы> - удалить таблицу\n"
        "<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...) - создать запись\n"                                 # NOQA E501
        "<command> select from <имя_таблицы> [where <столбец> = <значение>] - прочитать записи\n"                                       # NOQA E501
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1>[, ...] where <столбец> = <значение> - обновить запись(и)\n"  # NOQA E501
        "<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить запись(и)\n"                                        # NOQA E501
        "<command> info <имя_таблицы> - информация о таблице\n"
        "<command> exit - выход из программы\n"
        "<command> help - справочная информация"
    )


# ===== CRUD =====

def insert(
    metadata: Dict[str, Any],
    table_name: str,
    values: List[Any],
    table_data: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Добавляет запись и возвращает (обновлённые_данные, новый_id).
    """
    schema = _schema_for_table(metadata, table_name)  # включает ID
    non_id_schema = [(n, t) for n, t in schema if n != "ID"]

    if len(values) != len(non_id_schema):
        raise ValueError(
            f"Ожидалось {len(non_id_schema)} значений, получено {len(values)}"
        )

    casted: Dict[str, Any] = {}
    for (col_name, col_type), raw_val in zip(non_id_schema, values):
        casted[col_name] = _cast_to_type(raw_val, col_type)

    new_id = 1
    if table_data:
        max_id = max(int(rec.get("ID", 0)) for rec in table_data)
        new_id = max_id + 1

    record = {"ID": new_id, **casted}
    table_data.append(record)
    return table_data, new_id


def select(
    table_data: List[Dict[str, Any]],
    where_clause: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Возвращает все записи или фильтрует по where_clause (равенство, AND).
    """
    if not where_clause:
        return list(table_data)

    def match(rec: Dict[str, Any]) -> bool:
        for k, v in where_clause.items():
            if k not in rec:
                return False
            if rec[k] != v:
                return False
        return True

    return [rec for rec in table_data if match(rec)]


def update(
    metadata: Dict[str, Any],
    table_name: str,
    table_data: List[Dict[str, Any]],
    set_clause: Dict[str, Any],
    where_clause: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[int]]:
    """
    Обновляет записи по where_clause значениями из set_clause.
    Возвращает (обновлённые_данные, список_ID_обновлённых).
    """
    schema = dict(_schema_for_table(metadata, table_name))  # name -> type
    updated_ids: List[int] = []

    for rec in table_data:
        is_match = True
        for k, v in where_clause.items():
            if rec.get(k) != v:
                is_match = False
                break
        if not is_match:
            continue

        # Обновление с валидацией типа
        for k, v in set_clause.items():
            if k == "ID":
                raise ValueError("Нельзя изменять поле ID")
            if k not in schema:
                raise ValueError(f'Неизвестное поле "{k}"')
            rec[k] = _cast_to_type(v, schema[k])
        updated_ids.append(int(rec["ID"]))

    return table_data, updated_ids


def delete(
    table_data: List[Dict[str, Any]],
    where_clause: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[int]]:
    """
    Удаляет записи по where_clause.
    Возвращает (обновлённые_данные, список_ID_удалённых).
    """
    remaining: List[Dict[str, Any]] = []
    deleted_ids: List[int] = []

    for rec in table_data:
        is_match = True
        for k, v in where_clause.items():
            if rec.get(k) != v:
                is_match = False
                break
        if is_match:
            if "ID" in rec:
                deleted_ids.append(int(rec["ID"]))
            continue
        remaining.append(rec)

    return remaining, deleted_ids


def table_info(
    metadata: Dict[str, Any],
    table_name: str,
    table_data: List[Dict[str, Any]],
) -> Tuple[str, int]:
    """
    Возвращает (строка_со_столбцами, количество_записей).
    """
    schema = _schema_for_table(metadata, table_name)
    cols_str = ", ".join(f"{n}:{t}" for n, t in schema)
    return cols_str, len(table_data)
