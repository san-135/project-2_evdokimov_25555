import re
from typing import Any, Dict, List, Optional


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (len(s) >= 2) and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1]
    return s


def parse_scalar(token: str) -> Any:
    t = token.strip()
    # bool
    low = t.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    # int
    if re.fullmatch(r"[+-]?\d+", t):
        return int(t)
    # string (требуем кавычки для строк)
    if (len(t) >= 2) and (t[0] in ("'", '"') and t[-1] == t[0]):
        return _strip_quotes(t)
    # иначе — ошибка
    raise ValueError(f"Некорректное значение: {token} (строки должны быть в кавычках)")


def _split_commas(strin: str) -> List[str]:
    """
    Разделение по запятым с учётом кавычек.
    """
    parts: List[str] = []
    buf: List[str] = []
    quote: Optional[str] = None
    for ch in strin:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        else:
            if ch in ("'", '"'):
                quote = ch
                buf.append(ch)
            elif ch == ",":
                parts.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return parts


def parse_values_list(values_segment: str) -> List[Any]:
    # ожидаем "( ... )"
    s = values_segment.strip()
    if not (s.startswith("(") and s.endswith(")")):
        raise ValueError("Ожидался список значений в скобках: (v1, v2, ...)")
    inner = s[1:-1]
    raw_vals = _split_commas(inner)
    return [parse_scalar(rv) for rv in raw_vals]


def parse_where(where_segment: Optional[str]) -> Optional[Dict[str, Any]]:
    if not where_segment:
        return None
    # поддерживаем один предикат: <col> = <value>
    m = re.fullmatch(r"\s*(\w+)\s*=\s*(.+?)\s*$", where_segment)
    if not m:
        raise ValueError("Ожидалось условие вида: <колонка> = <значение>")
    col = m.group(1)
    val = parse_scalar(m.group(2))
    return {col: val}


def parse_set(set_segment: str) -> Dict[str, Any]:
    # поддерживаем несколько через запятую: a=1, b="x"
    assigns = _split_commas(set_segment)
    res: Dict[str, Any] = {}
    for item in assigns:
        m = item.split("=")
        if not (m[0] and m[1]):
            raise ValueError(f"Некорректное присваивание в set: {item}")
        col = m[0]
        val = parse_scalar(m[1])
        res[col] = val
    return res


# Командные парсеры

def parse_command(line: str) -> Dict[str, Any]:
    s = line.strip()
    low = s.lower()

    # insert into <table> values (...)
    m = re.fullmatch(r"\s*insert\s+into\s+(\w+)\s+values\s*(\(.+\))\s*$", s, 
                     flags=re.IGNORECASE)
    if m:
        return {"cmd": "insert", "table": m.group(1), 
                "values": parse_values_list(m.group(2))}

    # select from <table> [where ...]
    m = re.fullmatch(r"\s*select\s+from\s+(\w+)(?:\s+where\s+(.+))?\s*$", s, 
                     flags=re.IGNORECASE)
    if m:
        table = m.group(1)
        where = parse_where(m.group(2)) if m.group(2) else None
        return {"cmd": "select", "table": table, "where": where}

    # update <table> set ... where ...
    m = re.fullmatch(r"\s*update\s+(\w+)\s+set\s+(.+?)\s+where\s+(.+)\s*$", s, 
                     flags=re.IGNORECASE)
    if m:
        return {"cmd": "update", "table": m.group(1), "set": parse_set(m.group(2)), 
                "where": parse_where(m.group(3))}

    # delete from <table> where ...
    m = re.fullmatch(r"\s*delete\s+from\s+(\w+)\s+where\s+(.+)\s*$", s, 
                     flags=re.IGNORECASE)
    if m:
        return {"cmd": "delete", "table": m.group(1), 
                "where": parse_where(m.group(2))}

    # info <table>
    m = re.fullmatch(r"\s*info\s+(\w+)\s*$", s, flags=re.IGNORECASE)
    if m:
        return {"cmd": "info", "table": m.group(1)}

    # list tables
    if low.startswith("list tables"):
        return {"cmd": "list_tables"}

    # create table <name> <col:type> ...
    if low.startswith("create table"):
        parts = s.split()
        if len(parts) <= 3:
            raise ValueError("Некорректная команда. Ожидались имя таблицы и столбцы.")
        return {"cmd": "create_table", "table": parts[2], "columns": parts[3:]}

    # drop table <name>
    if low.startswith("drop table"):
        parts = s.split()
        if len(parts) != 3:
            raise ValueError("Некорректная команда. Ожидалось имя таблицы.")
        return {"cmd": "drop_table", "table": parts[2]}

    if low in ("help", "h"):
        return {"cmd": "help"}

    if low in ("exit", "quit", "q"):
        return {"cmd": "exit"}

    raise ValueError("Некорректная функция или формат команды")
