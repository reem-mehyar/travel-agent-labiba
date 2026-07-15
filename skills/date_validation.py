
from datetime import date, datetime


def validate_dates(start_date: str, end_date: str = None) -> str | None:
    """
    Validates a start date (and optional end date) aren't in the past,
    aren't malformed, and that end_date isn't before start_date.

    Args:
        start_date: departure_date or check_in, format "YYYY-MM-DD"
        end_date: return_date or check_out, format "YYYY-MM-DD", optional

    Returns:
        An error message string if invalid, otherwise None.
    """
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