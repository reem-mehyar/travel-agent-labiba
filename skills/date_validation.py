
from datetime import date, datetime


def validate_dates(start_date: str, end_date: str = None) -> str | None:

    today = date.today()

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return f"'{start_date}' is not a valid date format."

    if start < today:
        return f"The date {start_date} is in the past. Please provide a future date."

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return f"'{end_date}' is not a valid date format."

        if end < start:
            return f"The end date {end_date} is before the start date {start_date}."

    return None