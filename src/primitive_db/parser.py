import re
from typing import Any, Dict, List, Optional, Tuple


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (len(s) >= 2) and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1]
    return s


def _cast_literal(token: str) -> Any:
    t = token.strip()
    low = t.lower()
    if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
        return _strip_quotes(t)
    if low == "true":
        return True
    if low == "false":
        return False
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    raise ValueError(f"Не удалось распознать литерал: {token!r}. "
                     f'Строки должны быть в кавычках, логические — "true"/"false".')


def _split_commas(s: str) -> List[str]:
    """
    Разделение по запятым с учётом кавычек.
    """
    parts: List[str] = []
    buf: List[str] = []
    q: Optional[str] = None
    i = 0
    while i < len(s):
        ch = s[i]
        if q:
            buf.append(ch)
            if ch == q:
                q = None
        else:
            if ch in ("'", '"'):
                q = ch
                buf.append(ch)
            elif ch == ",":
                parts.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
        i += 1
    if buf:
        parts.append("".join(buf).strip())
    return parts


def parse_values_segment(cmd: str) -> List[Any]:
    m = re.search(r"values\s*\((.*)\)\s*$", cmd, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        raise ValueError("Не найдены значения в скобках после VALUES")
    inner = m.group(1).strip()
    if not inner:
        return []
    tokens = _split_commas(inner)
    return [_cast_literal(tok) for tok in tokens]


def parse_condition(cond: str) -> Dict[str, Any]:
    """
    'col = value' -> {'col': cast(value)}
    """
    if "=" not in cond:
        raise ValueError("Ожидалось выражение вида <столбец> = <значение>")
    left, right = cond.split("=", 1)
    col = left.strip()
    val = _cast_literal(right.strip())
    if not col:
        raise ValueError("Пустое имя столбца в условии")
    return {col: val}


def parse_set_clause(s: str) -> Dict[str, Any]:
    """
    'a = 1, b = "x"' -> {'a': 1, 'b': 'x'}
    """
    parts = _split_commas(s)
    result: Dict[str, Any] = {}
    for p in parts:
        kv = parse_condition(p)
        result.update(kv)
    return result


def parse_insert(cmd: str) -> Tuple[str, List[Any]]:
    m = re.match(r"^\s*insert\s+into\s+(\w+)\s+values\s*\(", cmd, flags=re.IGNORECASE)
    if not m:
        raise ValueError("Некорректная команда INSERT")
    table = m.group(1)
    values = parse_values_segment(cmd)
    return table, values


def parse_select(cmd: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    m = re.match(
        r"^\s*select\s+from\s+(\w+)(?:\s+where\s+(.*))?\s*$",
        cmd,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        raise ValueError("Некорректная команда SELECT")
    table = m.group(1)
    where_raw = m.group(2)
    where = parse_condition(where_raw) if where_raw else None
    return table, where


def parse_update(cmd: str) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    m = re.match(
        r"^\s*update\s+(\w+)\s+set\s+(.*?)(?:\s+where\s+(.*))?\s*$",
        cmd,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        raise ValueError("Некорректная команда UPDATE")
    table = m.group(1)
    set_raw = m.group(2)
    where_raw = m.group(3)
    if not where_raw:
        raise ValueError("Для UPDATE требуется выражение WHERE")
    set_clause = parse_set_clause(set_raw)
    where = parse_condition(where_raw)
    return table, set_clause, where


def parse_delete(cmd: str) -> Tuple[str, Dict[str, Any]]:
    m = re.match(
        r"^\s*delete\s+from\s+(\w+)\s+where\s+(.*)\s*$",
        cmd,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        raise ValueError("Некорректная команда DELETE")
    table = m.group(1)
    where = parse_condition(m.group(2))
    return table, where


def parse_info(cmd: str) -> str:
    m = re.match(r"^\s*info\s+(\w+)\s*$", cmd, flags=re.IGNORECASE)
    if not m:
        raise ValueError("Некорректная команда INFO")
    return m.group(1)
