import json
from datetime import datetime
from typing import Any, Callable, Optional

import pandas as pd


def report_to_file(filename: Optional[str] = None) -> Callable:
    """
    Декоратор для сохранения результата функции-отчёта в файл.

    - Если filename не задан — создаёт имя файла в формате: report_YYYYMMDD_HHMMSS.json
    - Поддерживает как JSON, так и DataFrame (сохраняется в JSON)
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)

            # Определяем имя файла
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"report_{timestamp}.json"
            else:
                output_filename = filename

            # Приводим результат к JSON-сериализуемому виду
            if isinstance(result, pd.DataFrame):
                # Сохраняем DataFrame как JSON (с датами в формате строки)
                data_to_save = result.to_dict(orient="records")
            elif (
                isinstance(result, (dict, list, str, int, float, bool))
                or result is None
            ):
                data_to_save = result
            else:
                data_to_save = str(result)

            # Записываем в файл
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4, default=str)

            return result

        return wrapper

    return decorator


def spending_by_category(
    transactions: pd.DataFrame, category: str, date: Optional[str] = None
) -> pd.DataFrame:
    """
    Возвращает траты по заданной категории за последние 3 месяца от указанной даты.

    Параметры:
    - transactions: DataFrame с колонками ['date', 'category', 'amount']
    - category: строка — название категории
    - date: опционально, строка в формате 'YYYY-MM-DD'. Если не задана — текущая дата.

    Возвращает:
    - DataFrame с транзакциями по категории за последние 3 месяца
    """
    # Копируем, чтобы не менять оригинал
    df = transactions.copy()

    # Преобразуем колонку 'date' в datetime, если ещё не сделано
    if not pd.api.types.is_datetime64_any_dtype(df["Дата операции"]):
        df["Дата операции"] = pd.to_datetime(
            df["Дата операции"], format="%d.%m.%Y %H:%M:%S"
        )

    # Определяем дату окончания
    if date is None:
        end_date = pd.Timestamp.today()
    else:
        end_date = pd.to_datetime(date)

    # Начало периода — 3 месяца назад
    start_date = end_date - pd.DateOffset(months=3)

    # Фильтруем по категории и дате
    filtered = df[
        (df["Категория"] == category)
        & (df["Дата операции"] > start_date)
        & (df["Дата операции"] <= end_date)
    ]

    # Сортируем по дате
    filtered = filtered.sort_values("Дата операции").reset_index(drop=True)

    return filtered
