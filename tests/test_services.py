import json

from src.services import analyze_cashback


def test_normal_case():
    """Обычный случай: корректные транзакции за нужный месяц"""
    data = [
        {
            "Дата операции": "15.07.2020 12:30:00",
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": 50,
        },
        {
            "Дата операции": "20.07.2020 18:45:00",
            "Категория": "Такси",
            "Бонусы (включая кэшбэк)": 30,
        },
        {
            "Дата операции": "10.07.2020 09:15:00",
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": 20,
        },
    ]

    result_str = analyze_cashback(data, 2020, 7)
    result_dict = json.loads(result_str)

    expected = {"Супермаркеты": 70.0, "Такси": 30.0}

    assert result_dict == expected, f"Ожидалось {expected}, получено {result_dict}"


def test_no_matching_month():
    """Нет транзакций за указанный месяц"""
    data = [
        {
            "Дата операции": "15.06.2020 12:30:00",
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": 50,
        }
    ]

    result_str = analyze_cashback(data, 2020, 7)
    result_dict = json.loads(result_str)

    assert result_dict == {}, f"Ожидался пустой словарь, получено {result_dict}"


def test_invalid_date_format():
    """Некорректный формат даты — должна пропускаться"""
    data = [
        {
            "Дата операции": "31/07/2020",  # неправильный формат
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": 50,
        },
        {
            "Дата операции": "15.07.2020 10:00:00",
            "Категория": "Кафе",
            "Бонусы (включая кэшбэк)": 25,
        },
    ]

    result_str = analyze_cashback(data, 2020, 7)
    result_dict = json.loads(result_str)

    expected = {"Кафе": 25.0}
    assert result_dict == expected, f"Ожидалось {expected}, получено {result_dict}"


def test_missing_category_or_cashback():
    """Отсутствует категория или кешбэк — должно обрабатываться корректно"""
    data = [
        {
            "Дата операции": "15.07.2020 12:30:00",
            "Категория": "Супермаркеты",
            # отсутствует кешбэк → по умолчанию 0
        },
        {
            "Дата операции": "20.07.2020 18:45:00",
            # отсутствует категория → "Неизвестно"
            "Бонусы (включая кэшбэк)": 30,
        },
        {
            "Дата операции": "10.07.2020 09:15:00",
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": 20,
        },
    ]

    result_str = analyze_cashback(data, 2020, 7)
    result_dict = json.loads(result_str)

    expected = {"Супермаркеты": 20.0, "Неизвестно": 30.0}

    assert result_dict == expected, f"Ожидалось {expected}, получено {result_dict}"


def test_non_numeric_cashback():
    """Кешбэк не число — пропускаем транзакцию"""
    data = [
        {
            "Дата операции": "15.07.2020 12:30:00",
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": "пятьдесят",  # строка — не число
        },
        {
            "Дата операции": "20.07.2020 18:45:00",
            "Категория": "Такси",
            "Бонусы (включая кэшбэк)": 30,
        },
    ]

    result_str = analyze_cashback(data, 2020, 7)
    result_dict = json.loads(result_str)

    expected = {"Такси": 30.0}
    assert result_dict == expected, f"Ожидалось {expected}, получено {result_dict}"


def test_empty_data():
    """Пустой список транзакций"""
    data = []
    result_str = analyze_cashback(data, 2020, 7)
    result_dict = json.loads(result_str)
    assert result_dict == {}, "Ожидался пустой словарь"


def test_rounding():
    """Проверка округления до 2 знаков"""
    data = [
        {
            "Дата операции": "15.07.2020 12:30:00",
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": 33.33,
        },
        {
            "Дата операции": "20.07.2020 18:45:00",
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": 66.66,
        },
    ]

    result_str = analyze_cashback(data, 2020, 7)
    result_dict = json.loads(result_str)

    expected = {
        "Супермаркеты": 99.99
    }  # 33.333 + 66.666 = 99.999 → округляется до 99.99
    assert result_dict == expected, f"Ожидалось {expected}, получено {result_dict}"


def test_returns_json_string():
    """Проверяем, что возвращается именно строка JSON, а не словарь"""
    data = [
        {
            "Дата операции": "15.07.2020 12:30:00",
            "Категория": "Такси",
            "Бонусы (включая кэшбэк)": 25,
        }
    ]

    result = analyze_cashback(data, 2020, 7)
    assert isinstance(result, str), "Функция должна возвращать строку"

    # Убедимся, что строку можно распарсить
    parsed = json.loads(result)
    assert isinstance(parsed, dict), "Строка должна быть валидным JSON-объектом"
    assert parsed.get("Такси") == 25.0, "Неверное значение кешбэка"
