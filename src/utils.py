"""Утилиты для работы с транзакциями."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from src.logger import setup_logger

logger = setup_logger("utils")

# Названия колонок
DATE_COLUMN = "Дата операции"
PAYMENT_DATE_COLUMN = "Дата платежа"
CARD_COLUMN = "Номер карты"
STATUS_COLUMN = "Статус"
AMOUNT_COLUMN = "Сумма операции"
CURRENCY_COLUMN = "Валюта операции"
PAYMENT_AMOUNT_COLUMN = "Сумма платежа"
PAYMENT_CURRENCY_COLUMN = "Валюта платежа"
CASHBACK_COLUMN = "Кешбэк"
CATEGORY_COLUMN = "Категория"
MCC_COLUMN = "MCC"
DESCRIPTION_COLUMN = "Описание"
BONUS_COLUMN = "Бонусы (включая кешбэк)"
ROUNDING_COLUMN = "Округление на «Инвесткопилку»"
ROUNDED_COLUMN = "Сумма операции с округлением"

REQUIRED_COLUMNS = [
    DATE_COLUMN,
    PAYMENT_AMOUNT_COLUMN,
    CATEGORY_COLUMN,
    DESCRIPTION_COLUMN,
]

TRANSFER_CATEGORIES = {"Переводы", "Перевод"}
CASH_CATEGORIES = {"Наличные"}
TRANSFER_CASH_CATEGORIES = TRANSFER_CATEGORIES | CASH_CATEGORIES


def load_user_settings(path: Union[str, Path] = "user_settings.json") -> Dict[str, Any]:
    """Загружает пользовательские настройки."""
    logger.info(f"Загрузка настроек из: {path}")

    default_settings = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
    }

    path = Path(path)

    if not path.exists():
        logger.warning(f"Файл настроек не найден: {path}. Используются значения по умолчанию.")
        return default_settings

    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Ошибка при чтении настроек: {e}. Используются значения по умолчанию.")
        return default_settings

    if not isinstance(settings.get("user_currencies"), list):
        settings["user_currencies"] = default_settings["user_currencies"]

    if not isinstance(settings.get("user_stocks"), list):
        settings["user_stocks"] = default_settings["user_stocks"]

    logger.info("Настройки загружены успешно")
    return {**default_settings, **settings}


def ensure_dataframe(data: Union[pd.DataFrame, List[Dict[str, Any]]]) -> pd.DataFrame:
    """Преобразует входные данные в DataFrame."""
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        df = pd.DataFrame(data)

    df.columns = [str(column).strip() for column in df.columns]
    return df


def get_last_digits(value: Any) -> str:
    """Возвращает последние 4 цифры номера карты."""
    digits = re.sub(r"\D", "", str(value))
    return digits[-4:] if digits else "0000"


def normalize_transactions(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    strict: bool = False,
) -> pd.DataFrame:
    """Приводит транзакции к единому формату."""
    logger.debug("Нормализация транзакций")

    df = ensure_dataframe(data)

    if strict:
        missing_columns = [
            column for column in REQUIRED_COLUMNS if column not in df.columns
        ]
        if missing_columns:
            logger.error(f"Отсутствуют обязательные колонки: {missing_columns}")
            raise ValueError(f"Отсутствуют обязательные колонки: {missing_columns}")

    if DATE_COLUMN not in df.columns:
        if PAYMENT_DATE_COLUMN in df.columns:
            df[DATE_COLUMN] = df[PAYMENT_DATE_COLUMN]
        else:
            df[DATE_COLUMN] = pd.NaT

    if PAYMENT_AMOUNT_COLUMN not in df.columns:
        if AMOUNT_COLUMN in df.columns:
            df[PAYMENT_AMOUNT_COLUMN] = df[AMOUNT_COLUMN]
        else:
            df[PAYMENT_AMOUNT_COLUMN] = 0.0

    if CATEGORY_COLUMN not in df.columns:
        df[CATEGORY_COLUMN] = "Без категории"

    if DESCRIPTION_COLUMN not in df.columns:
        df[DESCRIPTION_COLUMN] = ""

    if CARD_COLUMN not in df.columns:
        df[CARD_COLUMN] = "0000"

    if CASHBACK_COLUMN not in df.columns:
        df[CASHBACK_COLUMN] = 0.0

    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], dayfirst=True, errors="coerce")

    if PAYMENT_DATE_COLUMN in df.columns:
        df[PAYMENT_DATE_COLUMN] = pd.to_datetime(
            df[PAYMENT_DATE_COLUMN],
            dayfirst=True,
            errors="coerce",
        )

    numeric_columns = [
        AMOUNT_COLUMN,
        PAYMENT_AMOUNT_COLUMN,
        CASHBACK_COLUMN,
        BONUS_COLUMN,
        ROUNDING_COLUMN,
        ROUNDED_COLUMN,
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)

    df[CARD_COLUMN] = df[CARD_COLUMN].apply(get_last_digits)
    df[CATEGORY_COLUMN] = df[CATEGORY_COLUMN].fillna("Без категории").astype(str).str.strip()
    df[DESCRIPTION_COLUMN] = df[DESCRIPTION_COLUMN].fillna("").astype(str).str.strip()

    df = df.sort_values(DATE_COLUMN, ignore_index=True, na_position="last")

    logger.debug(f"Нормализовано {len(df)} транзакций")
    return df


def read_transactions(path: Union[str, Path]) -> pd.DataFrame:
    """Читает Excel-файл с транзакциями."""
    path = Path(path)
    logger.info(f"Загрузка транзакций из файла: {path}")

    if not path.exists():
        logger.error(f"Файл не найден: {path}")
        raise FileNotFoundError(f"Файл не найден: {path}")

    try:
        df = pd.read_excel(path)
        logger.info(f"Загружено {len(df)} записей из файла")
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        raise

    return normalize_transactions(df, strict=True)


def parse_datetime(value: Union[str, datetime, pd.Timestamp]) -> datetime:
    """Разбирает дату в разных форматах."""
    if isinstance(value, datetime):
        return value

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    value = str(value).strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    try:
        return pd.to_datetime(value, dayfirst=True).to_pydatetime()
    except Exception as exc:
        logger.error(f"Не удалось разобрать дату: {value}")
        raise ValueError(f"Не удалось разобрать дату: {value}") from exc


def get_greeting(dt: Optional[datetime] = None) -> str:
    """Возвращает приветствие по времени."""
    dt = dt or datetime.now()
    hour = dt.hour

    if 6 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"

    return "Доброй ночи"


def get_default_range(dt: datetime) -> Tuple[datetime, datetime]:
    """Диапазон с начала месяца по входящую дату."""
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, dt


def get_range_by_period(dt: datetime, period: str = "M") -> Tuple[datetime, datetime]:
    """
    Возвращает диапазон для периодов:
    W - неделя, M - месяц, Y - год, ALL - все данные до даты.
    """
    period = period.upper()

    if period == "W":
        start = (dt - timedelta(days=dt.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        return start, dt

    if period == "M":
        start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, dt

    if period == "Y":
        start = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, dt

    if period == "ALL":
        return datetime(1900, 1, 1, 0, 0, 0), dt

    logger.error(f"Недопустимый период: {period}")
    raise ValueError("Недопустимый период. Допустимые значения: W, M, Y, ALL.")


def filter_by_date_range(
    df: pd.DataFrame,
    start: Union[datetime, pd.Timestamp],
    end: Union[datetime, pd.Timestamp],
) -> pd.DataFrame:
    """Фильтрует DataFrame по дате."""
    if df.empty:
        return df.copy()

    start = pd.Timestamp(start)
    end = pd.Timestamp(end)

    mask = (
        df[DATE_COLUMN].notna()
        & (df[DATE_COLUMN] >= start)
        & (df[DATE_COLUMN] <= end)
    )

    result = df.loc[mask].copy()
    logger.debug(f"Отфильтровано {len(result)} записей за период")
    return result


def get_spending_df(df: pd.DataFrame) -> pd.DataFrame:
    """Возвращает расходы."""
    if df.empty:
        return df.copy()

    df = df.copy()

    if PAYMENT_AMOUNT_COLUMN in df.columns and (df[PAYMENT_AMOUNT_COLUMN] < 0).any():
        expenses = df[df[PAYMENT_AMOUNT_COLUMN] < 0].copy()
        expenses["amount_abs"] = expenses[PAYMENT_AMOUNT_COLUMN].abs()
        return expenses

    if AMOUNT_COLUMN in df.columns and (df[AMOUNT_COLUMN] < 0).any():
        expenses = df[df[AMOUNT_COLUMN] < 0].copy()
        expenses["amount_abs"] = expenses[AMOUNT_COLUMN].abs()
        return expenses

    if PAYMENT_AMOUNT_COLUMN in df.columns and (df[PAYMENT_AMOUNT_COLUMN] > 0).any():
        expenses = df[df[PAYMENT_AMOUNT_COLUMN] > 0].copy()
        expenses["amount_abs"] = expenses[PAYMENT_AMOUNT_COLUMN].abs()
        return expenses

    return df.iloc[0:0].copy()


def get_income_df(df: pd.DataFrame) -> pd.DataFrame:
    """Возвращает поступления."""
    if df.empty:
        return df.copy()

    df = df.copy()

    if PAYMENT_AMOUNT_COLUMN in df.columns and (df[PAYMENT_AMOUNT_COLUMN] > 0).any():
        incomes = df[df[PAYMENT_AMOUNT_COLUMN] > 0].copy()
        incomes["amount_abs"] = incomes[PAYMENT_AMOUNT_COLUMN].abs()
        return incomes

    if AMOUNT_COLUMN in df.columns and (df[AMOUNT_COLUMN] > 0).any():
        incomes = df[df[AMOUNT_COLUMN] > 0].copy()
        incomes["amount_abs"] = incomes[AMOUNT_COLUMN].abs()
        return incomes

    return df.iloc[0:0].copy()


def round_int(value: Any) -> int:
    """Округляет значение до целого."""
    try:
        value = float(value)
        if pd.isna(value):
            return 0
        return int(round(value))
    except Exception:
        return 0


def transaction_to_dict(row: pd.Series) -> Dict[str, Any]:
    """Преобразует строку DataFrame в словарь для JSON."""
    date_value = row.get(DATE_COLUMN)

    if pd.isna(date_value):
        date_str = ""
    else:
        date_str = pd.Timestamp(date_value).strftime("%d.%m.%Y")

    amount = row.get(PAYMENT_AMOUNT_COLUMN, row.get(AMOUNT_COLUMN, 0.0))

    return {
        "date": date_str,
        "amount": float(amount or 0.0),
        "category": str(row.get(CATEGORY_COLUMN, "")),
        "description": str(row.get(DESCRIPTION_COLUMN, "")),
    }


def df_to_transactions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Преобразует DataFrame в список транзакций."""
    if df.empty:
        return []

    return [transaction_to_dict(row) for _, row in df.iterrows()]


def aggregate_categories(
    df: pd.DataFrame,
    exclude_categories: Optional[set] = None,
    top_n: Optional[int] = None,
    rest_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Агрегирует суммы по категориям."""
    if df.empty or "amount_abs" not in df.columns:
        return []

    exclude_categories = exclude_categories or set()

    grouped = (
        df.groupby(CATEGORY_COLUMN)["amount_abs"]
        .sum()
        .sort_values(ascending=False)
    )

    items = []

    for category, amount in grouped.items():
        category = str(category)

        if category in exclude_categories:
            continue

        items.append((category, float(amount)))

    if top_n is None:
        selected_items = items
        rest_sum = 0.0
    else:
        selected_items = items[:top_n]
        rest_sum = sum(amount for _, amount in items[top_n:])

    result = [
        {"category": category, "amount": round_int(amount)}
        for category, amount in selected_items
    ]

    if rest_label and rest_sum > 0:
        result.append({"category": rest_label, "amount": round_int(rest_sum)})

    return result