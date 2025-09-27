import json
import os
import tempfile
from datetime import datetime

import pandas as pd

from src.reports import report_to_file, spending_by_category


def test_report_to_file_with_default_name():
    """Тест: декоратор создаёт файл с именем по умолчанию и сохраняет результат."""

    @report_to_file()
    def dummy_report():
        return {"test": "data"}

    result = dummy_report()
    assert result == {"test": "data"}

    # Ищем файл, начинающийся с "report_" и заканчивающийся на ".json"
    files = [
        f for f in os.listdir(".") if f.startswith("report_") and f.endswith(".json")
    ]
    assert len(files) >= 1, "Файл отчёта не создан"

    # Читаем последний созданный файл (на случай, если запускали раньше)
    latest_file = max(files, key=os.path.getctime)
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {"test": "data"}

    # Удаляем файл после теста
    os.remove(latest_file)


def test_report_to_file_with_custom_name():
    """Тест: декоратор использует заданное имя файла."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        custom_name = tmp.name

    @report_to_file(filename=custom_name)
    def dummy_report():
        return [{"id": 1, "value": "ok"}]

    result = dummy_report()
    assert result == [{"id": 1, "value": "ok"}]

    assert os.path.exists(custom_name)
    with open(custom_name, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == [{"id": 1, "value": "ok"}]

    os.remove(custom_name)


def test_report_to_file_with_dataframe():
    """Тест: сохранение DataFrame в JSON через декоратор."""
    df = pd.DataFrame(
        {
            "Дата операции": ["01.01.2023 10:00:00", "02.01.2023 11:00:00"],
            "Категория": ["Еда", "Транспорт"],
            "Сумма": [100, 200],
        }
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        filename = tmp.name

    @report_to_file(filename=filename)
    def df_report():
        return df

    result = df_report()
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["Категория"] == "Еда"
    assert data[0]["Сумма"] == 100

    os.remove(filename)


def test_spending_by_category_basic():
    """Тест: фильтрация по категории и дате (3 месяца)."""
    df = pd.DataFrame(
        {
            "Дата операции": [
                "01.01.2023 10:00:00",
                "15.02.2023 12:00:00",
                "10.03.2023 09:00:00",
                "05.04.2023 14:00:00",  # в пределах 3 месяцев от 01.05.2023
            ],
            "Категория": ["Еда", "Еда", "Транспорт", "Еда"],
            "Сумма": [100, 150, 200, 80],
        }
    )

    result = spending_by_category(df, "Еда", "2023-05-01")
    assert len(result) == 2  # только февраль и апрель (январь — вне 3 месяцев)
    assert list(result["Сумма"]) == [150, 80]
    assert list(result["Категория"]) == ["Еда", "Еда"]


def test_spending_by_category_no_date():
    """Тест: если date=None, используется текущая дата."""
    # Создаём транзакцию "сегодня"
    today = datetime.today().strftime("%d.%m.%Y %H:%M:%S")
    df = pd.DataFrame(
        {"Дата операции": [today], "Категория": ["Подписки"], "Сумма": [500]}
    )

    result = spending_by_category(df, "Подписки")
    assert len(result) == 1
    assert result.iloc[0]["Сумма"] == 500


def test_spending_by_category_empty_result():
    """Тест: категория не найдена — возвращается пустой DataFrame."""
    df = pd.DataFrame(
        {"Дата операции": ["01.01.2023 10:00:00"], "Категория": ["Еда"], "Сумма": [100]}
    )

    result = spending_by_category(df, "Одежда", "2023-01-02")
    assert len(result) == 0


def test_spending_by_category_sorting():
    """Тест: результат отсортирован по дате."""
    df = pd.DataFrame(
        {
            "Дата операции": [
                "10.03.2023 10:00:00",
                "01.03.2023 09:00:00",
                "05.03.2023 11:00:00",
            ],
            "Категория": ["Еда", "Еда", "Еда"],
            "Сумма": [100, 200, 150],
        }
    )

    result = spending_by_category(df, "Еда", "2023-04-01")
    dates = result["Дата операции"].tolist()
    expected_dates = sorted(dates)
    assert dates == expected_dates
    assert list(result["Сумма"]) == [200, 150, 100]  # в порядке возрастания дат
