import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv


def process_excel(
    file_path: str, save_processed=False, output_path=None
) -> pd.DataFrame:
    """
    Читает Excel-файл, приводит столбец 'Дата операции' к формату datetime.
    Возвращает обработанный DataFrame.

    :param file_path: путь к исходному Excel-файлу
    :param save_processed: сохранить ли обработанный файл (по умолчанию False)
    :param output_path: путь для сохранения обработанного файла (если save_processed=True)
    :return: обработанный DataFrame
    """
    # Чтение файла
    df = pd.read_excel(file_path)

    # Приведение даты к datetime (предполагается формат ДД.ММ.ГГГГ, например 05.04.2025)
    df["Дата платежа"] = pd.to_datetime(
        df["Дата платежа"], format="%d.%m.%Y", errors="coerce"
    )
    return df


def filter_operations_by_date(df: pd.DataFrame, date_str: str) -> list:
    """
    Фильтрует операции от первого числа месяца до переданной даты (включительно весь день).
    Возвращает отсортированный список словарей с операциями.
    """
    # Преобразуем строку в datetime
    target_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    # Первый день месяца
    first_day = target_date.replace(day=1)

    # Включаем весь целевой день
    target_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Удаляем строки, где дата не распарсилась
    df_clean = df.dropna(subset=["Дата платежа"]).copy()

    # Фильтрация
    filtered_df = df_clean[
        (df_clean["Дата платежа"] >= first_day)
        & (df_clean["Дата платежа"] <= target_end)
    ]

    # Сортировка по дате + сброс индекса для гарантии порядка
    filtered_df = filtered_df.sort_values("Дата платежа", ignore_index=True)

    # Преобразуем в список словарей
    return filtered_df.to_dict("records")


def get_greeting() -> str:
    """
    Возвращает приветствие в зависимости от текущего времени суток:
    - 6:00–11:59 → "Доброе утро"
    - 12:00–17:59 → "Добрый день"
    - 18:00–23:59 → "Добрый вечер"
    - 00:00–5:59 → "Доброй ночи"
    """
    now = datetime.now()
    hour = now.hour

    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 24:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


# Пример использования:
print(f'"{get_greeting()}"')


def analyze_cards(operations: list) -> list:
    """
    Анализирует операции по картам и возвращает список словарей с данными:
    - last_digits: последние 4 цифры карты
    - total_spent: общая сумма расходов (по модулю)
    - cashback: кешбэк 1% от суммы расходов (т.е. 1 рубль на каждые 100 рублей = 0.01 * total_spent)

    :param operations: список словарей с операциями, с ключами 'Номер карты' и 'Сумма операции'
    :return: список словарей с анализом по каждой карте
    """
    from collections import defaultdict

    card_expenses = defaultdict(float)

    for op in operations:
        card_number = str(op.get("Номер карты", "")).strip()
        amount = op.get("Сумма операции", 0)

        # Пропускаем, если нет номера карты или сумма нечисловая
        if not card_number or not isinstance(amount, (int, float)):
            continue

        # Берем только расходы (отрицательные суммы)
        if amount < 0:
            last_4 = card_number[-4:] if len(card_number) >= 4 else card_number
            card_expenses[last_4] += abs(amount)  # суммируем по модулю

    # Формируем результат
    result = []
    for last_4, total_spent in card_expenses.items():
        cashback = round(total_spent * 0.01, 2)  # 1% кешбэка
        result.append(
            {
                "last_digits": last_4,
                "total_spent": round(total_spent, 2),
                "cashback": cashback,
            }
        )

    return result


def get_top_5_transactions(operations: list) -> list:
    """
    Возвращает Топ-5 транзакций по модулю суммы платежа (самые крупные по абсолютному значению).
    Формат каждой транзакции:
      {
        "date": "ДД.ММ.ГГГГ",
        "amount": число (оригинальное, с знаком),
        "category": строка,
        "description": строка
      }

    :param operations: список словарей с операциями
    :return: список из 5 (или меньше) словарей
    """
    transactions = []

    for op in operations:
        amount = op.get("Сумма операции")
        if not isinstance(amount, (int, float)):
            continue  # пропускаем, если сумма нечисловая

        date = op.get("Дата операции")

        if isinstance(date, str):
            # Попробуем распарсить строку с датой и временем
            try:
                # Формат под твой случай: "31.07.2020 08:25:19"
                date_obj = datetime.strptime(date, "%d.%m.%Y %H:%M:%S")
                date_str = date_obj.strftime("%d.%m.%Y")
            except ValueError:
                # Если не удалось — оставим как есть или поставим заглушку
                date_str = "Неизвестно"
        elif hasattr(date, "strftime"):
            date_str = date.strftime("%d.%m.%Y")
        else:
            date_str = "Неизвестно"

        transactions.append(
            {
                "date": date_str,
                "amount": amount,  # оставляем оригинальный знак
                "category": str(op.get("Категория", "—")).strip(),
                "description": str(op.get("Описание", "—")).strip(),
            }
        )

    # Сортируем по убыванию абсолютного значения суммы
    top_5 = sorted(transactions, key=lambda x: abs(x["amount"]), reverse=True)[:5]

    return top_5


def get_cbr_rates() -> dict:
    """Получает курсы USD и EUR к RUB с сайта ЦБ РФ"""
    try:
        response = requests.get(
            "https://www.cbr-xml-daily.ru/daily_json.js", timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return {
            "USD": data["Valute"]["USD"]["Value"],
            "EUR": data["Valute"]["EUR"]["Value"],
        }
    except Exception as e:
        print(f"Ошибка при получении курсов от ЦБ РФ: {e}")
        return {}


def get_financial_data() -> dict:
    """Получаем данные о валютах и акциях"""
    load_dotenv()
    API_KEY = os.getenv("API_ALPHAVANTAGE")

    if not API_KEY:
        raise ValueError(
            "API ключ не найден. Убедитесь, что в .env есть API_ALPHAVANTAGE=..."
        )

    BASE_URL = "https://www.alphavantage.co/query"

    result = {"exchange_rates": [], "stock_prices": []}

    currencies = [
        {"from": "USD", "to": "RUB", "key": "USD"},
        {"from": "EUR", "to": "RUB", "key": "EUR"},
    ]

    # Словарь для хранения полученных курсов
    obtained_currencies = set()

    for curr in currencies:
        try:
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": curr["from"],
                "to_currency": curr["to"],
                "apikey": API_KEY,
            }
            response = requests.get(BASE_URL, params=params, timeout=10)
            print(
                f"Статус Alpha Vantage для {curr['from']}/{curr['to']}: {response.status_code}"
            )
            print(f"Ответ: {response.text[:500]}")

            response.raise_for_status()
            data = response.json()

            rate_info = data.get("Realtime Currency Exchange Rate")
            if rate_info:
                rate = float(rate_info["5. Exchange Rate"])
                result["exchange_rates"].append(
                    {"currency": curr["key"], "rate": round(rate, 2)}
                )
                obtained_currencies.add(curr["key"])  # Запоминаем, что курс получен
            else:
                print(
                    f"Нет данных по курсу {curr['from']}/{curr['to']} в Alpha Vantage"
                )
        except Exception as e:
            print(f"Ошибка Alpha Vantage для {curr['from']}/{curr['to']}: {e}")

        # Если курс не был получен — попробуем через ЦБ РФ
        if curr["key"] not in obtained_currencies:
            print(f"Пробуем получить {curr['key']}/RUB из ЦБ РФ...")
            cbr_rates = get_cbr_rates()
            if curr["key"] in cbr_rates:
                rate = cbr_rates[curr["key"]]
                result["exchange_rates"].append(
                    {"currency": curr["key"], "rate": round(rate, 2)}
                )
                obtained_currencies.add(curr["key"])
                print(f"Успешно получено из ЦБ РФ: {curr['key']} = {rate}")
            else:
                print(f"Не удалось получить курс {curr['key']}/RUB даже из ЦБ РФ")

    # --- Акции ---
    stocks = ["SPY", "AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]

    for symbol in stocks:
        try:
            params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": API_KEY}
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            quote = data.get("Global Quote")
            if quote and "05. price" in quote:
                price = float(quote["05. price"])
                result["stock_prices"].append(
                    {"stock": symbol, "price": round(price, 2)}
                )
        except Exception as e:
            print(f"Ошибка при получении цены {symbol}: {e}")
            continue

    return result
