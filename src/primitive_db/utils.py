import json
import os
from typing import Any, Dict, List

DATA_DIR = "data"


def _ensure_data_dir() -> None:
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def _table_path(table_name: str) -> str:
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_metadata(filepath: str) -> Dict[str, Any]:
    """
    Загрузить словарь метаданных из JSON-файла. Если файл не найден, вернуть {}.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str, data: Dict[str, Any]) -> None:
    """
    Сохранить словарь метаданных в JSON-файл с отступами.
    """
    with open(filepath, "w", encoding="utf-8") as fpath:
        json.dump(data, fpath, ensure_ascii=False, indent=4)


def load_table_data(table_name: str) -> List[Dict[str, Any]]:
    """
    Загрузить данные таблицы из data/<table_name>.json.
    Если файла нет, вернуть пустой список.
    """
    _ensure_data_dir()
    path = _table_path(table_name)
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_table_data(table_name: str, data: List[Dict[str, Any]]) -> None:
    """
    Сохранить данные таблицы в data/<table_name>.json.
    """
    _ensure_data_dir()
    path = _table_path(table_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
