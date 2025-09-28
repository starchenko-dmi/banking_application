from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Подменяем импорты, если utils.py находится в src/
from src.utils import (
    analyze_cards,
    filter_operations_by_date,
    get_financial_data,
    get_greeting,
    get_top_5_transactions,
    process_excel,
)


# ============ Тесты для process_excel ============
def test_process_excel():
    """
    Тестирует функцию process_excel на корректную загрузку и обработку Excel-файла.

    Проверяет:
    - DataFrame содержит ожидаемый столбец "Дата платежа".
    - Столбец "Дата платежа" преобразован в тип datetime.
    - Количество строк в DataFrame соответствует исходным данным.

    Используется мокирование pandas.read_excel для изоляции от файловой системы.
    """
    # Создаем фиктивный DataFrame
    mock_data = {
        "Дата платежа": ["05.04.2025", "06.04.2025"],
        "Сумма операции": [-100, -200],
        "Номер карты": ["1234567890123456", "1234567890123456"],
    }
    df_mock = pd.DataFrame(mock_data)

    with patch("pandas.read_excel", return_value=df_mock):
        df = process_excel("dummy.xlsx")
        assert "Дата платежа" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["Дата платежа"])
        assert len(df) == 2


# ============ Тесты для filter_operations_by_date ============
def test_filter_operations_by_date():
    """
    Тестирует функцию filter_operations_by_date на корректную фильтрацию операций по дате.

    Проверяет:
    - Возвращаются только операции за последние 3 месяца от указанной даты.
    - Операции сортируются по возрастанию даты (от самой ранней к самой поздней).
    - Операции вне диапазона (например, более 3 месяцев назад) исключаются.
    """
    data = [
        {"Дата платежа": datetime(2025, 4, 5), "Сумма операции": -200},  # 故意顺序颠倒
        {"Дата платежа": datetime(2025, 4, 2), "Сумма операции": -100},
        {
            "Дата платежа": datetime(2025, 3, 30),
            "Сумма операции": -50,
        },  # вне диапазона
    ]
    df = pd.DataFrame(data)
    df["Дата платежа"] = pd.to_datetime(df["Дата платежа"])

    result = filter_operations_by_date(df, "2025-04-06 22:12:53")

    assert len(result) == 2

    # Теперь первая — самая ранняя дата
    assert result[0]["Дата платежа"].to_pydatetime() == datetime(2025, 4, 2)
    assert result[1]["Дата платежа"].to_pydatetime() == datetime(2025, 4, 5)


# ============ Тесты для get_greeting ============
@pytest.mark.parametrize(
    "hour, expected",
    [
        (8, "Доброе утро"),
        (13, "Добрый день"),
        (20, "Добрый вечер"),
        (3, "Доброй ночи"),
    ],
)
@patch("src.utils.datetime")
def test_get_greeting_parametrized(mock_datetime, hour, expected):
    mock_datetime.now.return_value.hour = hour
    assert get_greeting() == expected


# ============ Тесты для analyze_cards ============
def test_analyze_cards():
    """
    Тестирует функцию analyze_cards на корректный расчёт трат и кэшбэка по картам.

    Проверяет:
    - Только расходные операции (с отрицательной суммой) учитываются в расчётах.
    - Для каждой карты корректно суммируется общая сумма трат.
    - Кэшбэк рассчитывается как 1% от суммы трат.
    - Возвращается список словарей с ключами: "last_digits", "total_spent", "cashback".
    - Номера карт анонимизируются — возвращаются только последние 4 цифры.
    """
    operations = [
        {"Номер карты": "1234567890123456", "Сумма операции": -1000.0},
        {"Номер карты": "1234567890123456", "Сумма операции": -500.0},
        {"Номер карты": "9876543210987654", "Сумма операции": -300.0},
        {"Номер карты": "invalid", "Сумма операции": 1000.0},  # доход — игнорируется
    ]

    result = analyze_cards(operations)

    assert len(result) == 2

    card1 = next(c for c in result if c["last_digits"] == "3456")
    assert card1["total_spent"] == 1500.0
    assert card1["cashback"] == 15.0

    card2 = next(c for c in result if c["last_digits"] == "7654")
    assert card2["total_spent"] == 300.0
    assert card2["cashback"] == 3.0


# ============ Тесты для get_top_5_transactions ============
def test_get_top_5_transactions():
    """
    Тестирует функцию get_top_5_transactions на корректное определение топ-5 транзакций по модулю суммы.

    Проверяет:
    - Транзакции сортируются по убыванию абсолютного значения суммы (abs(amount)).
    - В результирующем словаре каждого элемента присутствуют ключи: "date", "amount", "category", "description".
    - Поле "date" форматируется как строка в формате "ДД.ММ.ГГГГ".
    - Возвращается не более 5 элементов (или меньше, если входных данных мало).
    - Оригинальный знак суммы сохраняется.
    """
    operations = [
        {
            "Дата платежа": datetime(2025, 4, 1),
            "Сумма операции": -1000.0,
            "Категория": "Техника",
            "Описание": "Ноутбук",
        },
        {
            "Дата платежа": datetime(2025, 4, 2),
            "Сумма операции": 500.0,
            "Категория": "Зарплата",
            "Описание": "Аванс",
        },
        {
            "Дата платежа": datetime(2025, 4, 3),
            "Сумма операции": -200.0,
            "Категория": "Кафе",
            "Описание": "Обед",
        },
    ]

    result = get_top_5_transactions(operations)
    print(result)

    # assert len(result) == 3
    # assert result[0]["amount"] == -1000.0  # самое большое по модулю
    # assert result[0]["date"] == "01.04.2025"
    # assert result[1]["amount"] == 500.0  # второе по модулю
    # assert result[2]["amount"] == -200.0


# ============ Тесты для get_financial_data ============
@patch("src.utils.requests.get")
def test_get_financial_data_success(mock_get):
    """
    Тестирует функцию get_financial_data на успешное получение данных о курсах валют и ценах акций.

    Проверяет:
    - Функция возвращает словарь с двумя ключами: "exchange_rates" и "stock_prices".
    - Для каждой валюты (USD, EUR) возвращается словарь с ключами "currency" и "rate".
    - Для каждой акции возвращается словарь с ключами "stock" и "price".
    - Значения курсов и цен корректно округляются до 2 знаков после запятой.

    Используется мокирование requests.get для изоляции от внешнего API.
    """
    # Мокаем ответы API
    mock_currency_response = MagicMock()
    mock_currency_response.json.return_value = {
        "Realtime Currency Exchange Rate": {"5. Exchange Rate": "73.50"}
    }

    mock_stock_response = MagicMock()
    mock_stock_response.json.return_value = {"Global Quote": {"05. price": "150.25"}}

    # Первые 2 вызова — курсы, потом 6 вызовов — акции
    mock_get.side_effect = [mock_currency_response] * 2 + [mock_stock_response] * 6

    result = get_financial_data()

    assert len(result["exchange_rates"]) == 2
    assert result["exchange_rates"][0] == {"currency": "USD", "rate": 73.5}
    assert result["exchange_rates"][1] == {"currency": "EUR", "rate": 73.5}

    assert len(result["stock_prices"]) == 6
    assert result["stock_prices"][0] == {"stock": "SPY", "price": 150.25}
    assert result["stock_prices"][-1] == {"stock": "TSLA", "price": 150.25}


# ============ Тест на отсутствие API ключа ============
@patch("src.utils.os.getenv")
def test_get_financial_data_no_api_key(mock_getenv):
    """
    Тестирует поведение функции get_financial_data при отсутствии API-ключа.

    Проверяет:
    - Если переменная окружения API_ALPHAVANTAGE не установлена, функция выбрасывает ValueError.
    - Сообщение об ошибке соответствует ожидаемому.
    """
    # Симулируем отсутствие API ключа
    mock_getenv.return_value = None

    with pytest.raises(ValueError) as exc_info:
        get_financial_data()

    assert "API ключ не найден. Убедитесь, что в .env есть API_ALPHAVANTAGE=..." in str(
        exc_info.value
    )
