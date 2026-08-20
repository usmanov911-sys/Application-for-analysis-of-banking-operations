from datetime import datetime

from src import utils


def test_greeting_morning():
    dt = datetime(2026, 8, 20, 7, 0, 0)
    assert utils.get_greeting(dt) == "Доброе утро"


def test_greeting_day():
    dt = datetime(2026, 8, 20, 14, 0, 0)
    assert utils.get_greeting(dt) == "Добрый день"


def test_greeting_evening():
    dt = datetime(2026, 8, 20, 20, 0, 0)
    assert utils.get_greeting(dt) == "Добрый вечер"


def test_greeting_night():
    dt = datetime(2026, 8, 20, 23, 30, 0)
    assert utils.get_greeting(dt) == "Доброй ночи"


def test_default_range():
    dt = datetime(2026, 8, 20, 15, 30, 0)
    start, end = utils.get_default_range(dt)

    assert start.year == 2026
    assert start.month == 8
    assert start.day == 1
    assert end == dt


def test_filter_by_date_range(sample_df):
    start = datetime(2026, 8, 1)
    end = datetime(2026, 8, 31)

    filtered = utils.filter_by_date_range(sample_df, start, end)

    assert not filtered.empty
    assert len(filtered) == len(sample_df)
