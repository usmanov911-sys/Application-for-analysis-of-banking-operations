from src import reports


def test_spending_by_category(sample_df, tmp_path, monkeypatch):
    monkeypatch.setattr(reports, "REPORTS_DIR", tmp_path)

    result = reports.spending_by_category(
        sample_df,
        "Супермаркеты",
        "2026-08-20",
    )

    assert not result.empty
    assert list(result.columns) == ["date", "amount"]
    assert (tmp_path / "spending_by_category_report.json").exists()


def test_spending_by_weekday(sample_df, tmp_path, monkeypatch):
    monkeypatch.setattr(reports, "REPORTS_DIR", tmp_path)

    result = reports.spending_by_weekday(
        sample_df,
        "2026-08-20",
    )

    assert not result.empty
    assert set(result.columns) == {"weekday", "weekday_name", "avg_spent"}
    assert (tmp_path / "spending_by_weekday_report.json").exists()


def test_spending_by_workday(sample_df, tmp_path, monkeypatch):
    monkeypatch.setattr(reports, "REPORTS_DIR", tmp_path)

    result = reports.spending_by_workday(
        sample_df,
        "2026-08-20",
    )

    assert not result.empty
    assert set(result.columns) == {"day_type", "avg_spent"}
    assert (tmp_path / "spending_by_workday_report.json").exists()
