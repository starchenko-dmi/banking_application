import json
from pathlib import Path

from src.reports import report_to_file, spending_by_category
from src.services import analyze_cashback
from src.utils import (analyze_cards, filter_operations_by_date,
                       get_financial_data, get_greeting,
                       get_top_5_transactions, process_excel)

df = None


def get_operations_file_path(filename: str = "operations.xlsx") -> str:
    """
    Возвращает абсолютный путь к файлу в папке 'data',
    находящейся на одном уровне с папкой 'src'.
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # поднимаемся из src в корень
    file_path = project_root / "data" / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    return str(file_path)


def generate_financial_report(excel_file_path: str, target_date_str: str) -> dict:
    """
    Генерирует полный финансовый отчёт в формате JSON, включая:
    - Приветствие по времени суток
    - Анализ по картам
    - Топ-5 транзакций
    - Курсы валют и цены акций
    """
    # 1. Обрабатываем Excel
    global df
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


if __name__ == "__main__":
    try:
        # Получаем путь только при запуске скрипта
        excel_path = get_operations_file_path()

        # Генерируем отчёт
        report = generate_financial_report(excel_path, "2020-08-25 15:30:00")

        # Выводим красиво в консоль
        print(json.dumps(report, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"❌ Ошибка: {e}")


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


if __name__ == "__main__":
    try:
        # Получаем путь только при запуске скрипта
        excel_path = get_operations_file_path()

        # Генерируем отчёт (возвращает строку JSON)
        cashback_result = generate_services_report(excel_path, 2020, 11)

        # Выводим как есть — это уже красиво отформатированный JSON
        print(cashback_result)

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":

    @report_to_file()
    def my_report(transactions, category, date=None):
        return spending_by_category(transactions, category, date)

    result = my_report(df, "Супермаркеты", "2020-04-01")
