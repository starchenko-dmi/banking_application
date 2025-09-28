import json

from src.reports import spending_by_category, report_to_file
from src.utils import process_excel, get_operations_file_path
from src.views import generate_financial_report, generate_services_report

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


    excel_path = get_operations_file_path()
    df = process_excel(excel_path)


    result = my_report(df, "Супермаркеты", "2020-04-01")