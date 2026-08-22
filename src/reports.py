"""Отчёты по транзакциям."""

from __future__ import annotations

import functools
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Union

import pandas as pd

from src import utils
from src.logger import setup_logger

logger = setup_logger("reports")

REPORTS_DIR = Path("reports")


def _write_report(filename: str, result: Any) -> None:
    """Записывает результат отчёта в файл."""
    path = Path(filename)

    if not path.is_absolute():
        path = REPORTS_DIR / path

    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Сохранение отчёта в файл: {path}")

    if isinstance(result, pd.DataFrame):
        result.to_json(
            path,
            orient="records",
            force_ascii=False,
            indent=2,
            date_format="iso",
        )
    else:
        path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    logger.info("Отчёт сохранён")


def save_report(
    _func: Optional[Callable] = None,
    *,
    filename: Optional[str] = None,
):
    """
    Декоратор для отчётов.

    Использование:

    @save_report
    def report(...):
        ...

    или:

    @save_report(filename="custom_report.json")
    def report(...):
        ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            report_filename = filename or f"{func.__name__}_report.json"
            _write_report(report_filename, result)
            return result

        return wrapper

    if callable(_func):
        return decorator(_func)

    return decorator


def _prepare_df(
    transactions: Union[pd.DataFrame, list],
    date: Optional[str] = None,
) -> tuple[pd.DataFrame, datetime, datetime]:
    """Подготавливает DataFrame и диапазон последних 3 месяцев."""
    df = utils.normalize_transactions(transactions, strict=False)

    if date is None:
        end_dt = datetime.now()
    else:
        end_dt = utils.parse_datetime(date)

    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)
    start_dt = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    start_dt = start_dt - pd.DateOffset(months=3)

    df = utils.filter_by_date_range(df, start_dt, end_dt)

    return df, start_dt, end_dt


@save_report
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """Траты по категории за последние 3 месяца."""
    logger.info(f"Отчёт: траты по категории '{category}'")

    df, _, _ = _prepare_df(transactions, date)

    if df.empty:
        return pd.DataFrame(columns=["date", "amount"])

    category_mask = df[utils.CATEGORY_COLUMN].str.lower() == str(category).lower()
    filtered_df = df[category_mask]

    spending = utils.get_spending_df(filtered_df)

    if spending.empty:
        return pd.DataFrame(columns=["date", "amount"])

    spending = spending.copy()
    spending["date"] = spending[utils.DATE_COLUMN].dt.strftime("%Y-%m-%d")

    result = (
        spending.groupby("date")["amount_abs"]
        .sum()
        .round(2)
        .reset_index()
    )

    result.columns = ["date", "amount"]

    return result.sort_values("date").reset_index(drop=True)


@save_report
def spending_by_weekday(
    transactions: pd.DataFrame,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """Средние траты по дням недели за последние 3 месяца."""
    logger.info("Отчёт: траты по дням недели")

    df, _, _ = _prepare_df(transactions, date)

    spending = utils.get_spending_df(df)

    if spending.empty:
        return pd.DataFrame(columns=["weekday", "weekday_name", "avg_spent"])

    spending = spending.copy()

    spending["day"] = spending[utils.DATE_COLUMN].dt.normalize()
    spending["weekday"] = spending[utils.DATE_COLUMN].dt.weekday

    daily = (
        spending.groupby(["day", "weekday"], as_index=False)["amount_abs"]
        .sum()
    )

    avg = (
        daily.groupby("weekday", as_index=False)["amount_abs"]
        .mean()
        .round(2)
    )

    weekday_names = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }

    avg["weekday_name"] = avg["weekday"].map(weekday_names)
    avg = avg.rename(columns={"amount_abs": "avg_spent"})

    return avg[["weekday", "weekday_name", "avg_spent"]].sort_values("weekday")


@save_report
def spending_by_workday(
    transactions: pd.DataFrame,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """Средние траты в рабочий и выходной день за последние 3 месяца."""
    logger.info("Отчёт: траты в рабочий/выходной день")

    df, _, _ = _prepare_df(transactions, date)

    spending = utils.get_spending_df(df)

    if spending.empty:
        return pd.DataFrame(columns=["day_type", "avg_spent"])

    spending = spending.copy()

    spending["day"] = spending[utils.DATE_COLUMN].dt.normalize()
    spending["weekday"] = spending[utils.DATE_COLUMN].dt.weekday

    daily = (
        spending.groupby(["day", "weekday"], as_index=False)["amount_abs"]
        .sum()
    )

    daily["day_type"] = daily["weekday"].apply(
        lambda weekday: "workday" if weekday < 5 else "weekend"
    )

    avg = (
        daily.groupby("day_type", as_index=False)["amount_abs"]
        .mean()
        .round(2)
    )

    avg = avg.rename(columns={"amount_abs": "avg_spent"})

    existing_types = set(avg["day_type"])

    for day_type in ["workday", "weekend"]:
        if day_type not in existing_types:
            avg = pd.concat(
                [
                    avg,
                    pd.DataFrame([{"day_type": day_type, "avg_spent": 0.0}]),
                ],
                ignore_index=True,
            )

    return avg.sort_values("day_type").reset_index(drop=True)