import re

from src import views


def monkeypatch_external(monkeypatch):
    monkeypatch.setattr(
        "src.views.fetch_currency_rates",
        lambda currencies: [
            {"currency": currency, "rate": 1.0} for currency in currencies
        ],
    )

    monkeypatch.setattr(
        "src.views.fetch_stock_prices",
        lambda stocks: [{"stock": stock, "price": 100.0} for stock in stocks],
    )


def test_main_page_structure(sample_df, monkeypatch):
    monkeypatch_external(monkeypatch)

    result = views.main_page(
        "2026-08-20 14:00:00",
        transactions=sample_df,
    )

    assert result["greeting"] == "Добрый день"
    assert len(result["cards"]) >= 1
    assert len(result["top_transactions"]) <= 5
    assert "currency_rates" in result
    assert "stock_prices" in result

    for card in result["cards"]:
        assert "last_digits" in card
        assert "total_spent" in card
        assert "cashback" in card


def test_top_transactions_sorted_and_formatted(sample_df, monkeypatch):
    monkeypatch_external(monkeypatch)

    result = views.main_page(
        "2026-08-20 14:00:00",
        transactions=sample_df,
    )

    transactions = result["top_transactions"]

    amounts = [transaction["amount"] for transaction in transactions]
    assert amounts == sorted(amounts, reverse=True)

    for transaction in transactions:
        assert "date" in transaction
        assert "amount" in transaction
        assert "category" in transaction
        assert "description" in transaction
        assert re.match(r"\d{2}\.\d{2}\.\d{4}", transaction["date"])


def test_events_page_structure(sample_df, monkeypatch):
    monkeypatch_external(monkeypatch)

    result = views.events_page(
        "2026-08-20",
        "M",
        transactions=sample_df,
    )

    assert "expenses" in result
    assert "income" in result
    assert "currency_rates" in result
    assert "stock_prices" in result

    expenses = result["expenses"]

    assert "total_amount" in expenses
    assert "main" in expenses
    assert "transfers_and_cash" in expenses

    assert isinstance(expenses["total_amount"], int)

    main_categories = [item["category"] for item in expenses["main"]]

    # Исключены переводы и наличные из основных категорий.
    assert "Переводы" not in main_categories
    assert "Наличные" not in main_categories

    # Так как категорий больше 7, должно быть "Остальное".
    assert "Остальное" in main_categories


def test_events_transfers_and_cash(sample_df, monkeypatch):
    monkeypatch_external(monkeypatch)

    result = views.events_page(
        "2026-08-20",
        "M",
        transactions=sample_df,
    )

    transfers_and_cash = result["expenses"]["transfers_and_cash"]
    categories = [item["category"] for item in transfers_and_cash]

    assert set(categories) == {"Наличные", "Переводы"}

    amounts = [item["amount"] for item in transfers_and_cash]
    assert amounts == sorted(amounts, reverse=True)
