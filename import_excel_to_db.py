"""
Импорт полного экспорта Excel (все вкладки) в SQLite config_bd/open21vpn.db.
Запуск из корня проекта:
  python import_excel_to_db.py [путь_к_xlsx]
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type

import pandas as pd
from sqlalchemy import delete, inspect as sa_inspect
from sqlalchemy.orm import DeclarativeBase

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config_bd.models import (  # noqa: E402
    Base,
    Gifts,
    Online,
    Payments,
    PaymentsCards,
    PaymentsCryptobot,
    PaymentsFkSBP,
    PaymentsPlategaCrypto,
    PaymentsStars,
    PaymentsWataCard,
    PaymentsWataSBP,
    PaymentsYoukassa,
    Users,
    WhiteCounter,
    create_tables,
    engine,
    AsyncSessionLocal,
)

DEFAULT_XLSX = Path(r"c:\Users\nusht\OneDrive\Desktop\open21_2905full.xlsx")

SHEET_MODEL_MAP: Tuple[Tuple[str, Type[DeclarativeBase]], ...] = (
    ("users", Users),
    ("payments_sbp", Payments),
    ("payments_fk_sbp", PaymentsFkSBP),
    ("payments_youkassa", PaymentsYoukassa),
    ("payments_cards", PaymentsCards),
    ("payments_stars", PaymentsStars),
    ("payments_platega_crypto", PaymentsPlategaCrypto),
    ("payments_wata_sbp", PaymentsWataSBP),
    ("payments_wata_card", PaymentsWataCard),
    ("payments_cryptobot", PaymentsCryptobot),
    ("gifts", Gifts),
    ("online", Online),
    ("white_counter", WhiteCounter),
)

# Поля модели, которых нет в Excel — значения по умолчанию при импорте
MODEL_ONLY_DEFAULTS: Dict[Type[DeclarativeBase], Dict[str, Any]] = {
    Users: {
        "password_hash": None,
        "linked_telegram_id": None,
    },
}

# Явные дефолты для NULL в Excel (колонка -> значение)
NULL_DEFAULTS: Dict[Type[DeclarativeBase], Dict[str, Any]] = {
    Users: {
        "stamp": "",
        "is_delete": False,
        "in_panel": False,
        "is_connect": False,
        "in_chanel": False,
        "reserve_field": False,
        "field_bool_1": False,
        "field_bool_2": False,
        "field_bool_3": False,
        "yookassa_autopay_enabled": False,
        "partner_balance": 0,
        "partner_pay": 0,
        "partner_flag": False,
    },
    PaymentsFkSBP: {
        "method": "fksbp",
    },
    PaymentsStars: {
        "status": "confirmed",
    },
    PaymentsCryptobot: {
        "status": "pending",
        "currency": "RUB",
    },
}


def _is_na(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _to_datetime(value: Any) -> Optional[datetime]:
    if _is_na(value):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    ts = pd.to_datetime(value, errors="coerce")
    if _is_na(ts):
        return None
    if hasattr(ts, "to_pydatetime"):
        return ts.to_pydatetime()
    return datetime.fromisoformat(str(ts))


def _to_date(value: Any) -> Optional[date]:
    if _is_na(value):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    ts = pd.to_datetime(value, errors="coerce")
    if _is_na(ts):
        return None
    return ts.date() if hasattr(ts, "date") else None


def _to_bool(value: Any, default: bool = False) -> bool:
    if _is_na(value):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(int(value))
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "да")
    return default


def _to_int(value: Any, default: int = 0) -> int:
    if _is_na(value):
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        return int(value)
    return int(value)


def _to_bigint(value: Any) -> Optional[int]:
    if _is_na(value):
        return None
    if isinstance(value, float):
        return int(value)
    return int(value)


def _to_float(value: Any, default: float = 0.0) -> float:
    if _is_na(value):
        return default
    return float(value)


def _to_str(value: Any) -> Optional[str]:
    if _is_na(value):
        return None
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return str(value)
    return str(value).strip() if str(value).strip() else None


def _coerce_column(model: Type[DeclarativeBase], col_name: str, raw: Any) -> Any:
    col = sa_inspect(model).columns[col_name]
    python_type = col.type.python_type

    null_defaults = NULL_DEFAULTS.get(model, {})
    if _is_na(raw):
        if col_name in null_defaults:
            return null_defaults[col_name]
        if col_name in MODEL_ONLY_DEFAULTS.get(model, {}):
            return MODEL_ONLY_DEFAULTS[model][col_name]
        if col.nullable:
            return None
        if col.default is not None and not callable(col.default.arg if hasattr(col.default, "arg") else col.default):
            arg = getattr(col.default, "arg", col.default)
            return arg() if callable(arg) else arg
        if python_type is bool:
            return False
        if python_type is int:
            return 0
        if python_type is float:
            return 0.0
        if python_type is str:
            return ""
        return None

    if col_name == "ref" or col_name == "partner":
        return _to_str(raw)
    if python_type is bool:
        return _to_bool(raw, null_defaults.get(col_name, False))
    if python_type is int and col_name not in ("amount", "duration", "partner_balance", "partner_pay"):
        if col_name in ("user_id", "giver_id", "recepient_id", "linked_telegram_id", "nonce", "fk_order_id"):
            return _to_bigint(raw)
        return _to_int(raw)
    if python_type is int:
        return _to_int(raw)
    if python_type is float:
        return _to_float(raw)
    if python_type is datetime:
        return _to_datetime(raw)
    if python_type is date:
        return _to_date(raw)
    if python_type is str:
        return _to_str(raw) if raw is not None else None
    return raw


def _model_column_names(model: Type[DeclarativeBase]) -> List[str]:
    return [c.key for c in sa_inspect(model).mapper.column_attrs]


def _row_from_series(model: Type[DeclarativeBase], series: pd.Series, excel_cols: set) -> Tuple[Dict[str, Any], List[str]]:
    missing_in_excel: List[str] = []
    data: Dict[str, Any] = {}
    for col_name in _model_column_names(model):
        if col_name in excel_cols:
            data[col_name] = _coerce_column(model, col_name, series.get(col_name))
        elif col_name in MODEL_ONLY_DEFAULTS.get(model, {}):
            missing_in_excel.append(col_name)
            data[col_name] = MODEL_ONLY_DEFAULTS[model][col_name]
        else:
            missing_in_excel.append(col_name)
            data[col_name] = _coerce_column(model, col_name, pd.NA)
    return data, missing_in_excel


async def _run_migrations() -> None:
    from config_bd.migrate_users_auth_fields import migrate as migrate_auth
    from config_bd.migrate_users_partner_fields import migrate as migrate_partner

    await migrate_auth()
    await migrate_partner()

    import sqlite3

    db_path = ROOT / "config_bd" / "open21vpn.db"
    if db_path.is_file():
        import migrate_users_extra_columns as muc

        conn = sqlite3.connect(str(db_path))
        try:
            cols = muc.existing_columns(conn)
            for name, ddl in muc.MIGRATIONS:
                if name not in cols:
                    conn.execute(ddl)
                    conn.commit()
                    print(f"migrate users column: {name}")
        finally:
            conn.close()


async def import_excel(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"Файл не найден: {path}")

    print(f"Чтение: {path}")
    xl = pd.ExcelFile(path)

    await create_tables()
    await _run_migrations()

    report_missing: Dict[str, List[str]] = {}
    stats: Dict[str, int] = {}

    async with AsyncSessionLocal() as session:
        for sheet_name, model in SHEET_MODEL_MAP:
            if sheet_name not in xl.sheet_names:
                print(f"SKIP: вкладка '{sheet_name}' отсутствует в файле")
                continue

            df = pd.read_excel(xl, sheet_name=sheet_name)
            excel_cols = set(df.columns.astype(str))

            await session.execute(delete(model))
            await session.commit()

            if df.empty or len(excel_cols) == 0:
                stats[sheet_name] = 0
                print(f"{sheet_name}: 0 строк (пустая вкладка)")
                continue

            extra_cols = excel_cols - set(_model_column_names(model))
            if extra_cols:
                print(f"{sheet_name}: лишние колонки в Excel (игнор): {sorted(extra_cols)}")

            batch: List[Any] = []
            missing_union: set = set()
            batch_size = 500

            for _, row in df.iterrows():
                data, missing = _row_from_series(model, row, excel_cols)
                missing_union.update(missing)
                batch.append(model(**data))
                if len(batch) >= batch_size:
                    session.add_all(batch)
                    await session.commit()
                    batch.clear()

            if batch:
                session.add_all(batch)
                await session.commit()

            if missing_union:
                report_missing[sheet_name] = sorted(missing_union)
            stats[sheet_name] = len(df)
            print(f"{sheet_name}: импортировано {len(df)} строк")

    from sqlalchemy import text

    id_tables = (
        ("users", "id"),
        ("payments", "id"),
        ("payments_fk_sbp", "id"),
        ("payments_youkassa", "id"),
        ("payments_cards", "id"),
        ("payments_stars", "id"),
        ("payments_platega_crypto", "id"),
        ("payments_wata_sbp", "id"),
        ("payments_wata_card", "id"),
        ("payments_cryptobot", "id"),
        ("online", "online_id"),
        ("white_counter", "id"),
    )
    async with engine.begin() as conn:
        seq_check = await conn.execute(
            text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
            )
        )
        if seq_check.scalar():
            for table, pk in id_tables:
                row = await conn.execute(text(f"SELECT MAX({pk}) FROM {table}"))
                max_id = row.scalar()
                if max_id is None:
                    continue
                await conn.execute(text("DELETE FROM sqlite_sequence WHERE name = :t"), {"t": table})
                await conn.execute(
                    text("INSERT INTO sqlite_sequence (name, seq) VALUES (:t, :s)"),
                    {"t": table, "s": int(max_id)},
                )

    print("\n=== Итог ===")
    for name, count in stats.items():
        print(f"  {name}: {count}")

    if report_missing:
        print("\n=== Поля отсутствовали в Excel (подставлены дефолты) ===")
        for sheet, cols in report_missing.items():
            print(f"  {sheet}: {', '.join(cols)}")
    else:
        print("\nВсе колонки модели присутствовали в Excel (или вкладки пустые).")

    print(f"\nБаза: {ROOT / 'config_bd' / 'open21vpn.db'}")


def main() -> None:
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_XLSX
    asyncio.run(import_excel(xlsx))


if __name__ == "__main__":
    main()
