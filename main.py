"""
Точка входа для запуска финансовых отчётов.

Файл main.py находится в корне проекта.

Примеры запуска:

    python main.py main
    python main.py main --date "2020-08-25 15:30:00"

    python main.py cashback --year 2020 --month 11

    python main.py spending --category "Супермаркеты" --date "2020-04-01"
"""

import argparse
import json
import sys
from typing import Optional

from src.reports import report_to_file, spending_by_category
from src.services import generate_services_report
from src.utils import get_operations_file_path, process_excel
from src.views import generate_financial_report


DEFAULT_EXCEL_FILE = "operations.xlsx"
DEFAULT_MAIN_DATE = "2020-08-25 15:30:00"
DEFAULT_SPENDING_DATE = "2020-04-01"
DEFAULT_CATEGORY = "Супермаркеты"


def build_parser() -> argparse.ArgumentParser:
    """
    Создаёт парсер аргументов командной строки.
    """
    parser = argparse.ArgumentParser(
        prog="banking_application",
        description="Запуск финансовых отчётов проекта",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Доступные команды",
    )

    # Команда main
    main_parser = subparsers.add_parser(
        "main",
        help="Главный финансовый отчёт: карты, топ-5 транзакций, валюты, акции",
    )
    main_parser.add_argument(
        "--date",
        default=DEFAULT_MAIN_DATE,
        help="Дата в формате YYYY-MM-DD HH:MM:SS",
    )
    main_parser.add_argument(
        "--file",
        default=DEFAULT_EXCEL_FILE,
        help="Имя Excel-файла в папке data",
    )

    # Команда cashback
    cashback_parser = subparsers.add_parser(
        "cashback",
        help="Отчёт по кешбэку за указанный год и месяц",
    )
    cashback_parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Год, например 2020",
    )
    cashback_parser.add_argument(
        "--month",
        type=int,
        required=True,
        help="Месяц, например 11",
    )
    cashback_parser.add_argument(
        "--file",
        default=DEFAULT_EXCEL_FILE,
        help="Имя Excel-файла в папке data",
    )

    # Команда spending
    spending_parser = subparsers.add_parser(
        "spending",
        help="Траты по категории за последние 3 месяца",
    )
    spending_parser.add_argument(
        "--category",
        default=DEFAULT_CATEGORY,
        help="Категория расходов",
    )
    spending_parser.add_argument(
        "--date",
        default=DEFAULT_SPENDING_DATE,
        help="Дата окончания периода в формате YYYY-MM-DD",
    )
    spending_parser.add_argument(
        "--file",
        default=DEFAULT_EXCEL_FILE,
        help="Имя Excel-файла в папке data",
    )
    spending_parser.add_argument(
        "--output",
        default=None,
        help="Имя JSON-файла для сохранения отчёта",
    )

    return parser


def run_main_report(file_name: str, target_date: str) -> None:
    """
    Запускает главный финансовый отчёт.
    """
    excel_path = get_operations_file_path(file_name)
    report = generate_financial_report(excel_path, target_date)

    print(json.dumps(report, ensure_ascii=False, indent=2))


def run_cashback_report(file_name: str, year: int, month: int) -> None:
    """
    Запускает отчёт по кешбэку за выбранный месяц.
    """
    excel_path = get_operations_file_path(file_name)
    report = generate_services_report(excel_path, year, month)

    print(report)


def run_spending_report(
    file_name: str,
    category: str,
    date: Optional[str],
    output: Optional[str],
) -> None:
    """
    Запускает отчёт по тратам по категории.

    Результат автоматически сохраняется в JSON через декоратор @report_to_file.
    """
    excel_path = get_operations_file_path(file_name)
    df = process_excel(excel_path)

    date_value = date if date else None

    @report_to_file(filename=output)
    def spending_report(transactions):
        return spending_by_category(
            transactions=transactions,
            category=category,
            date=date_value,
        )

    result = spending_report(df)

    if result is None or getattr(result, "empty", True):
        print("По заданным условиям операции не найдены.")
    else:
        print(result.to_string(index=False))


def main() -> int:
    """
    Главная функция приложения.
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "main":
            run_main_report(
                file_name=args.file,
                target_date=args.date,
            )

        elif args.command == "cashback":
            run_cashback_report(
                file_name=args.file,
                year=args.year,
                month=args.month,
            )

        elif args.command == "spending":
            run_spending_report(
                file_name=args.file,
                category=args.category,
                date=args.date,
                output=args.output,
            )

        return 0

    except FileNotFoundError as exc:
        print(f"❌ Файл не найден: {exc}", file=sys.stderr)
        return 1

    except ValueError as exc:
        print(f"❌ Ошибка формата данных: {exc}", file=sys.stderr)
        return 1

    except Exception as exc:
        print(f"❌ Ошибка при формировании отчёта: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())