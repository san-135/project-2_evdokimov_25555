import json
from typing import Any, Dict


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
