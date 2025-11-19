import json
import os
from typing import Any, Dict, List

from src.constants import DATA_DIR, META_PATH


def load_metadata(filepath: str = META_PATH) -> Dict[str, Any]:
    """
    Загрузить словарь метаданных из JSON-файла. Если файл не найден, вернуть {}.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str = META_PATH, data: Dict[str, Any] = None) -> None:
    """
    Сохранить словарь метаданных в JSON-файл с отступами.
    """
    if data is None:
        data = {}
    with open(filepath, "w", encoding="utf-8") as fpath:
        json.dump(data, fpath, ensure_ascii=False, indent=4)


def _table_path(table_name: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name: str) -> List[Dict[str, Any]]:
    """
    Загрузить данные таблицы из data/<table_name>.json.
    Если файла нет, вернуть пустой список.
    """
    path = _table_path(table_name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_table_data(table_name: str, data: List[Dict[str, Any]]) -> None:
    """
    Сохранить данные таблицы в data/<table_name>.json.
    """
    path = _table_path(table_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def delete_file(table_name: str) -> None:
    """
    Удалить файл базы данных.
    """
    path = _table_path(table_name)
    if not os.path.exists(path):
        return None
    os.remove(path)
    return None
