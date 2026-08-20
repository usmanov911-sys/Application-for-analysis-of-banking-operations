from src import services


def test_investment_bank():
    transactions = [
        {
            "Дата операции": "2026-08-01",
            "Сумма операции": -1712,
        },
        {
            "Дата операции": "2026-08-02",
            "Сумма операции": -1000,
        },
        {
            "Дата операции": "2026-07-31",
            "Сумма операции": -5000,
        },
    ]

    result = services.investment_bank(
        "2026-08",
        transactions,
        50,
    )

    # 1712 -> 1750, diff = 38
    # 1000 -> 1000, diff = 0
    assert result == 38.0


def test_simple_search_case_insensitive(sample_df):
    result = services.simple_search("лента", sample_df)

    assert len(result) >= 1
    assert any("Лента" in item["description"] for item in result)


def test_simple_search_by_category(sample_df):
    result = services.simple_search("СУПЕРМАРКЕТЫ", sample_df)

    assert len(result) >= 1
    assert all(item["category"].lower() == "супермаркеты" for item in result)


def test_search_by_phone():
    transactions = [
        {
            "Дата операции": "2026-08-01",
            "Категория": "Мобильная связь",
            "Описание": "Я МТС +7 921 11-22-33",
            "Сумма платежа": -100,
        },
        {
            "Дата операции": "2026-08-02",
            "Категория": "Мобильная связь",
            "Описание": "Тинькофф Мобайл +7 995 555-55-55",
            "Сумма платежа": -200,
        },
        {
            "Дата операции": "2026-08-03",
            "Категория": "Прочее",
            "Описание": "Без телефона",
            "Сумма платежа": -50,
        },
        {
            "Дата операции": "2026-08-04",
            "Категория": "Мобильная связь",
            "Описание": "МТС Mobile 89000000000",
            "Сумма платежа": -300,
        },
    ]

    result = services.search_by_phone(transactions)

    assert len(result) == 3


def test_search_transfers_to_individuals():
    transactions = [
        {
            "Дата операции": "2026-08-01",
            "Категория": "Переводы",
            "Описание": "Перевод Валерий А.",
            "Сумма платежа": -1000,
        },
        {
            "Дата операции": "2026-08-02",
            "Категория": "Переводы",
            "Описание": "Перевод ООО Ромашка",
            "Сумма платежа": -2000,
        },
        {
            "Дата операции": "2026-08-03",
            "Категория": "Оплата",
            "Описание": "Сергей З.",
            "Сумма платежа": -3000,
        },
    ]

    result = services.search_transfers_to_individuals(transactions)

    assert len(result) == 1
    assert result[0]["description"] == "Перевод Валерий А."


def test_cashback_categories_at_least_three(sample_df):
    result = services.cashback_categories(sample_df, 2026, 8)

    assert len(result) >= 3

    for category, cashback in result.items():
        assert isinstance(category, str)
        assert isinstance(cashback, float)
