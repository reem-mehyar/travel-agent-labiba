import requests

BASE_URL = "https://api.frankfurter.app/latest"

def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """
    Returns the exchange rate to convert 1 unit of from_currency into to_currency.
    """
    params = {"from": from_currency.upper(), "to": to_currency.upper()}
    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    rate = data.get("rates", {}).get(to_currency.upper())
    if rate is None:
        raise ValueError(f"Currency '{to_currency}' not supported.")
    return rate

def convert_amount(amount: float, from_currency: str, to_currency: str) -> float:
    """
    Converts a specific amount from one currency to another.
    """
    if from_currency.upper() == to_currency.upper():
        return amount
    rate = get_exchange_rate(from_currency, to_currency)
    return round(amount * rate, 2)