import requests
import os

API_KEY = os.getenv("EXCHANGERATE_API_KEY")
BASE_URL = "https://v6.exchangerate-api.com/v6"

def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """
    Returns the exchange rate to convert 1 unit of from_currency into to_currency.
    """
    url = f"{BASE_URL}/{API_KEY}/pair/{from_currency.upper()}/{to_currency.upper()}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()

    if data.get("result") != "success":
        raise ValueError(f"Exchange rate lookup failed: {data.get('error-type', 'unknown error')}")

    return data["conversion_rate"]

def convert_amount(amount: float, from_currency: str, to_currency: str) -> float:
    """
    Converts a specific amount from one currency to another.
    """
    if from_currency.upper() == to_currency.upper():
        return amount
    rate = get_exchange_rate(from_currency, to_currency)
    return round(amount * rate, 2)