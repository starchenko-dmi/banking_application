import json

from src.services import analyze_cashback
from src.utils import (
    analyze_cards,
    filter_operations_by_date,
    get_financial_data,
    get_greeting,
    get_top_5_transactions,
    process_excel,
)


def generate_financial_report(excel_file_path: str, target_date_str: str) -> dict:
    """
    Генерирует полный финансовый отчёт в формате JSON, включая:
    - Приветствие по времени суток
    - Анализ по картам
    - Топ-5 транзакций
    - Курсы валют и цены акций
    """
    # 1. Обрабатываем Excel
    df = process_excel(excel_file_path)

    # 2. Фильтруем операции по дате
    operations = filter_operations_by_date(df, target_date_str)

    # 3. Формируем приветствие
    greeting = get_greeting()

    # 4. Анализ по картам
    cards = analyze_cards(operations)

    # 5. Топ-5 транзакций
    top_transactions = get_top_5_transactions(operations)

    # 6. Получаем курсы и акции
    financial_data = get_financial_data()

    # 7. Собираем всё в один JSON-совместимый словарь
    report = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": financial_data.get("exchange_rates", []),
        "stock_prices": financial_data.get("stock_prices", []),
    }

    return report


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
