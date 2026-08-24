"""Сервисы для анализа транзакций."""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Union

import pandas as pd

from src import utils
from src.logger import setup_logger

logger = setup_logger("services")

PERSON_TRANSFER_REGEX = re.compile(
    r"\b[А-ЯЁA-Z][а-яёa-z]+\s+[А-ЯЁA-Z]\.",
    re.UNICODE,
)

PHONE_RAW_REGEX = re.compile(
    r"(?:\+7|8)[\s\-\(\)]*9(?:[\s\-\(\)]*\d){8,9}"
)

PHONE_DIGITS_REGEX = re.compile(r"(?:7|8)9\d{8,9}")


def cashback_categories(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    year: int,
    month: int,
) -> Dict[str, float]:
    """
    Сервис: выгодные категории повышенного кешбэка.

    Возвращает JSON с анализом, сколько кешбэка можно получить по категориям
    в указанном месяце.
    """
    logger.info(f"Анализ кешбэка за {month}/{year}")

    df = utils.normalize_transactions(data, strict=False)

    if df.empty:
        logger.warning("Данные пусты, возвращаются значения по умолчанию")
        return {"Категория 1": 0.0, "Категория 2": 0.0, "Категория 3": 0.0}

    df = df.dropna(subset=[utils.DATE_COLUMN])

    df = df[
        (df[utils.DATE_COLUMN].dt.year == int(year))
        & (df[utils.DATE_COLUMN].dt.month == int(month))
    ]

    if df.empty:
        logger.warning(f"Нет данных за {month}/{year}")
        return {"Категория 1": 0.0, "Категория 2": 0.0, "Категория 3": 0.0}

    cashback_column = pd.to_numeric(
        df.get(utils.CASHBACK_COLUMN, 0.0),
        errors="coerce",
    ).fillna(0.0)

    if cashback_column.abs().sum() > 0:
        grouped = df.groupby(utils.CATEGORY_COLUMN)[utils.CASHBACK_COLUMN].sum()
    else:
        expenses = utils.get_spending_df(df)

        if expenses.empty:
            grouped = pd.Series(dtype=float)
        else:
            grouped = expenses.groupby(utils.CATEGORY_COLUMN)["amount_abs"].sum() * 0.01

    grouped = grouped.round(2).sort_values(ascending=False)

    result = {
        str(category): float(amount)
        for category, amount in grouped.items()
    }

    # Гарантируем минимум 3 категории
    fallback_categories = [
        "Прочие",
        "Супермаркеты",
        "Переводы",
        "Транспорт",
        "Развлечения",
    ]

    for category in fallback_categories:
        if len(result) >= 3:
            break

        if category not in result:
            result[category] = 0.0

    logger.info(f"Анализ кешбэка завершён, найдено {len(result)} категорий")
    return result


def investment_bank(
    month: str,
    transactions: List[Dict[str, Any]],
    limit: int,
) -> float:
    """
    Сервис: Инвесткопилка.

    Рассчитывает сумму, которую можно было бы накопить за счёт округления трат.

    Args:
        month: Месяц в формате 'YYYY-MM'.
        transactions: Список транзакций.
        limit: Предел округления (10, 50 или 100).

    Returns:
        Сумма для инвесткопилки.
    """
    logger.info(f"Расчёт инвесткопилки за {month} с лимитом {limit}")

    year, month_number = map(int, month.split("-"))
    total = 0.0

    for transaction in transactions:
        date_value = (
            transaction.get("Дата операции")
            or transaction.get("date")
            or transaction.get("Дата платежа")
        )

        try:
            dt = utils.parse_datetime(str(date_value))
        except Exception:
            continue

        if dt.year != year or dt.month != month_number:
            continue

        amount_value = (
            transaction.get("Сумма операции")
            or transaction.get("amount")
            or transaction.get("Сумма платежа")
            or 0
        )

        try:
            amount = abs(float(amount_value))
        except Exception:
            continue

        if amount <= 0 or limit <= 0:
            continue

        rounded_amount = math.ceil(amount / limit) * limit
        total += rounded_amount - amount

    result = float(round(total, 2))
    logger.info(f"Инвесткопилка: {result}")
    return result


def _to_search_records(
    transactions: Union[pd.DataFrame, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Преобразует транзакции в список словарей для поиска."""
    df = utils.normalize_transactions(transactions, strict=False)
    return utils.df_to_transactions(df)


def simple_search(
    query: str,
    transactions: Union[pd.DataFrame, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Простой поиск по подстроке в категории или описании.
    Поиск нечувствителен к регистру.
    """
    logger.info(f"Поиск по запросу: '{query}'")

    query = str(query).lower()
    records = _to_search_records(transactions)

    result = []

    for record in records:
        category = str(record.get("category", "")).lower()
        description = str(record.get("description", "")).lower()

        if query in category or query in description:
            result.append(record)

    logger.info(f"Найдено {len(result)} записей")
    return result


def _contains_phone(text: str) -> bool:
    """
    Проверяет, есть ли мобильный номер.
    Поддерживает форматы:
    +7 (900) 000-00-00
    89000000000
    +7 921 11-22-33
    """
    text = str(text)

    if PHONE_RAW_REGEX.search(text):
        return True

    digits = re.sub(r"\D", "", text)
    return bool(PHONE_DIGITS_REGEX.search(digits))


def search_by_phone(
    transactions: Union[pd.DataFrame, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Поиск транзакций с мобильными номерами в описании."""
    logger.info("Поиск по телефонным номерам")

    records = _to_search_records(transactions)

    result = [
        record
        for record in records
        if _contains_phone(record.get("description", ""))
    ]

    logger.info(f"Найдено {len(result)} записей с телефонами")
    return result


def search_transfers_to_individuals(
    transactions: Union[pd.DataFrame, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Поиск переводов физическим лицам.

    Категория должна быть 'Переводы',
    в описании должно быть имя и первая буква фамилии с точкой.
    """
    logger.info("Поиск переводов физическим лицам")

    records = _to_search_records(transactions)

    result = []

    for record in records:
        category = str(record.get("category", "")).strip().lower()
        description = str(record.get("description", ""))

        if category != "переводы":
            continue

        if PERSON_TRANSFER_REGEX.search(description):
            result.append(record)

    logger.info(f"Найдено {len(result)} переводов физлицам")
    return result