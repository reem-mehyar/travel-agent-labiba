from api.currency_api import convert_amount, get_exchange_rate


class CurrencySkill:
    """
    Converts prices in hotel/flight search results into the user's requested currency.
    """
    def convert_results(self, search_results: dict, target_currency: str, source_currency: str = "USD") -> dict:
        
        if not target_currency or target_currency.upper() == source_currency.upper():
            return search_results

        try:
            get_exchange_rate(source_currency, target_currency)
        except Exception:
            result = dict(search_results)
            result["currency_note"] = (f"'{target_currency}' is not a recognized currency. "
            f"Showing prices in {source_currency} instead.")
            return result

        converted = dict(search_results)

        if "hotels" in converted:
            converted["hotels"] = [
                self._convert_hotel(h, source_currency, target_currency)
                for h in converted["hotels"]
            ]

        if "flights" in converted:
            converted["flights"] = [
                self._convert_flight(f, source_currency, target_currency)
                for f in converted["flights"]
            ]

        converted["currency"] = target_currency.upper()
        return converted

    def _convert_hotel(self, hotel: dict, source: str, target: str) -> dict:
        
        hotel = dict(hotel)
        for field in ("price_per_night", "total_price"):
            if hotel.get(field) is not None:
                try:
                    hotel[field] = convert_amount(hotel[field], source, target)
                except (ValueError, Exception):
                    pass  
        return hotel

    def _convert_flight(self, flight: dict, source: str, target: str) -> dict:

        flight = dict(flight)
        if flight.get("price") is not None:
            try:
                flight["price"] = convert_amount(flight["price"], source, target)
            except Exception:
                flight["conversion_failed"] = True
        return flight