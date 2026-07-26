from skills.hotel_skill import HotelSkill
from skills.flight_skill import FlightSkill
from api.currency_api import convert_amount

class PlannerSkill:
    """
    Takes a total trip budget and selects flight + hotel combinations
    that fit within it, by composing HotelSkill and FlightSkill.
    """

    REQUIRED_FIELDS = [
        "departure_city", "destination_city", "departure_date",
        "check_in", "check_out", "budget",
    ]

    def __init__(self):
        self.hotel_skill = HotelSkill()
        self.flight_skill = FlightSkill()

    def execute(self, intent_data: dict) -> dict:
        missing = {
            field: None
            for field in self.REQUIRED_FIELDS
            if intent_data.get(field) is None
        }
        if missing:
            return missing

        budget = intent_data["budget"]
        user_currency = (intent_data.get("currency") or "USD").upper()

        if user_currency != "USD":
            try:
                budget_usd = convert_amount(budget, user_currency, "USD")
            except Exception:
                return {
                    "planned_trip": [],
                    "note": f"Could not process budget in '{user_currency}'. Please check the currency code.",
                }
        else:
            budget_usd = budget

        flight_result = self.flight_skill.execute(intent_data)
        hotel_result = self.hotel_skill.execute(intent_data)

        if "flights" not in flight_result or "hotels" not in hotel_result:
            combined_missing = {}
            combined_missing.update({k: v for k, v in flight_result.items() if v is None})
            combined_missing.update({k: v for k, v in hotel_result.items() if v is None})
            if combined_missing:
                return combined_missing

        flights = flight_result.get("flights", [])
        hotels = hotel_result.get("hotels", [])

        if not flights or not hotels:
            return {
                "planned_trip": [],
                "note": "Could not find enough flight or hotel options to build a plan within budget.",
            }

        combos = self._find_combos_within_budget(flights, hotels, budget_usd)

        if not combos:
            cheapest_total_usd = self._cheapest_possible_total(flights, hotels)
            cheapest_display = cheapest_total_usd
            if user_currency != "USD" and cheapest_total_usd is not None:
                try:
                    cheapest_display = convert_amount(cheapest_total_usd, "USD", user_currency)
                except Exception:
                    pass
            return {
                "planned_trip": [],
                "note": (
                    f"No flight + hotel combination fits within a budget of {budget} {user_currency}. "
                    f"The cheapest available combination costs approximately {cheapest_display} {user_currency}."
                ),
            }

        combos.sort(key=lambda c: c["total_price"])

        if user_currency != "USD":
            for c in combos:
                try:
                    c["total_price"] = convert_amount(c["total_price"], "USD", user_currency)
                    c["remaining_budget"] = round(budget - c["total_price"], 2)
                except Exception:
                    pass

        return {"planned_trip": combos[:5], "currency": user_currency}

    def _find_combos_within_budget(self, flights: list, hotels: list, budget: float) -> list:
        combos = []
        for flight in flights:
            flight_price = self._to_number(flight.get("price"))
            if flight_price is None:
                continue
            for hotel in hotels:
                hotel_price = self._to_number(hotel.get("total_price"))
                if hotel_price is None:
                    continue
                total = flight_price + hotel_price
                if total <= budget:
                    combos.append({
                        "flight": flight,
                        "hotel": {
                            "name": hotel.get("name"),
                            "total_price": hotel_price,
                            "rating": hotel.get("rating"),
                            "booking_url": hotel.get("booking_url"),
                        },
                        "total_price": round(total, 2),
                        "remaining_budget": round(budget - total, 2),
                    })
        return combos

    def _to_number(self, value) -> float | None:
        """Coerces a price value to a float, handling strings with currency symbols/commas."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    def _cheapest_possible_total(self, flights: list, hotels: list) -> float | None:
        valid_flight_prices = [p for p in (self._to_number(f.get("price")) for f in flights) if p is not None]
        valid_hotel_prices = [p for p in (self._to_number(h.get("total_price")) for h in hotels) if p is not None]
        if not valid_flight_prices or not valid_hotel_prices:
            return None
        return round(min(valid_flight_prices) + min(valid_hotel_prices), 2)