import json
from pathlib import Path

from src.views import events_page, main_page
from src.services import (
    cashback_categories,
    investment_bank,
    simple_search,
    search_by_phone,
    search_transfers_to_individuals,
)
from src.reports import (
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)
from src.utils import read_transactions


def print_section(title: str):
    """Выводит заголовок секции."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def main():
    """Консольное приложение для анализа банковских транзакций."""

    # Путь к файлу данных
    data_path = Path("data/operations.xlsx")

    if not data_path.exists():
        print(f"Ошибка: файл {data_path} не найден.")
        print("Пожалуйста, положите файл с транзакциями в папку data/")
        return

    # Загрузка данных
    print("Загрузка данных из файла...")
    transactions = read_transactions(data_path)
    print(f"Загружено {len(transactions)} транзакций.")

    # ==================== ВЕБ-СТРАНИЦЫ ====================

    print_section("ГЛАВНАЯ СТРАНИЦА")
    main_result = main_page("2026-08-20 14:00:00", transactions=transactions)
    print(json.dumps(main_result, ensure_ascii=False, indent=2))

    print_section("СТРАНИЦА СОБЫТИЙ (за месяц)")
    events_result = events_page("2026-08-20", "M", transactions=transactions)
    print(json.dumps(events_result, ensure_ascii=False, indent=2))

    # ==================== СЕРВИСЫ ====================

    print_section("СЕРВИС: Выгодные категории повышенного кешбэка")
    cashback_result = cashback_categories(transactions, 2026, 8)
    print(json.dumps(cashback_result, ensure_ascii=False, indent=2))

    print_section("СЕРВИС: Инвесткопилка")
    investment_result = investment_bank(
        "2026-08",
        transactions.to_dict("records"),
        limit=50
    )
    print(f"Сумма для инвесткопилки: {investment_result:.2f} ₽")

    print_section("СЕРВИС: Простой поиск по запросу 'лента'")
    search_result = simple_search("лента", transactions)
    print(json.dumps(search_result, ensure_ascii=False, indent=2))

    print_section("СЕРВИС: Поиск по телефонным номерам")
    phone_result = search_by_phone(transactions)
    print(json.dumps(phone_result, ensure_ascii=False, indent=2))

    print_section("СЕРВИС: Поиск переводов физическим лицам")
    transfer_result = search_transfers_to_individuals(transactions)
    print(json.dumps(transfer_result, ensure_ascii=False, indent=2))

    # ==================== ОТЧЕТЫ ====================

    print_section("ОТЧЕТ: Траты по категории 'Супермаркеты'")
    category_report = spending_by_category(
        transactions,
        "Супермаркеты",
        "2026-08-20"
    )
    print(category_report.to_string(index=False))

    print_section("ОТЧЕТ: Траты по дням недели")
    weekday_report = spending_by_weekday(transactions, "2026-08-20")
    print(weekday_report.to_string(index=False))

    print_section("ОТЧЕТ: Траты в рабочий/выходной день")
    workday_report = spending_by_workday(transactions, "2026-08-20")
    print(workday_report.to_string(index=False))

    print("\n" + "=" * 80)
    print("  Анализ завершён успешно!")
    print("=" * 80)


if __name__ == "__main__":
    main()