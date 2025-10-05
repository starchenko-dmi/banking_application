import json
from datetime import datetime

from src.utils import process_excel


def analyze_cashback(data, year: int, month: int) -> str:
    """
    Анализирует транзакции за указанный год и месяц,
    возвращает JSON с суммой кешбэка по каждой категории.

    data — список словарей с транзакциями.
    year, month — целые числа, например: 2020, 7
    """
    cashback_by_category = {}

    for transaction in data:
        # Извлекаем дату операции
        date_str = transaction.get("Дата операции", "")
        try:
            # Правильный формат: "31.07.2020 08:25:19" → '%d.%m.%Y %H:%M:%S'
            dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        except (ValueError, TypeError):
            continue  # Пропускаем, если дата не распарсилась

        # Фильтруем по году и месяцу
        if dt.year != year or dt.month != month:
            continue

        # Получаем категорию и сумму кешбэка
        category = transaction.get("Категория", "Неизвестно")
        cashback = transaction.get("Бонусы (включая кэшбэк)", 0)

        # Если кешбэк не число — пропускаем
        if not isinstance(cashback, (int, float)) or cashback < 0:
            continue

        # Накапливаем сумму по категории
        if category in cashback_by_category:
            cashback_by_category[category] += cashback
        else:
            cashback_by_category[category] = cashback

    # Округляем до 2 знаков
    cashback_by_category = {
        category: round(amount, 2) for category, amount in cashback_by_category.items()
    }

    # Возвращаем как JSON-строку
    return json.dumps(cashback_by_category, ensure_ascii=False, indent=4)


def generate_services_report(excel_file_path: str, year: int, month: int) -> str:
    """
    Возвращает JSON-строку с информацией о кешбэке по категориям за указанный год и месяц.
    """
    # 1. Обрабатываем Excel
    df = process_excel(excel_file_path)
    data = df.to_dict(orient="records")

    # 2. Получаем отчёт по кешбэку — используем переданные year и month
    cashback_result = analyze_cashback(data, year, month)

    # 3. Убеждаемся, что возвращаем именно строку JSON
    if isinstance(cashback_result, dict):
        return json.dumps(cashback_result, ensure_ascii=False, indent=4)

    # Если уже строка — возвращаем как есть
    return cashback_result