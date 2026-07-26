from skills.hotel_skill import HotelSkill
from skills.flight_skill import FlightSkill


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

        flight_result = self.flight_skill.execute(intent_data)
        hotel_result = self.hotel_skill.execute(intent_data)

        # If either sub-skill itself returned missing-field info, propagate that
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

        combos = self._find_combos_within_budget(flights, hotels, budget)

        if not combos:
            cheapest_total = self._cheapest_possible_total(flights, hotels)
            return {
                "planned_trip": [],
                "note": (
                    f"No flight + hotel combination fits within a budget of {budget}. "
                    f"The cheapest available combination costs approximately {cheapest_total}."
                ),
            }

        # Sort combos by total price, return the best few options
        combos.sort(key=lambda c: c["total_price"])
        return {"planned_trip": combos[:5]}

    def _find_combos_within_budget(self, flights: list, hotels: list, budget: float) -> list:
        combos = []
        for flight in flights:
            flight_price = flight.get("price")
            if flight_price is None:
                continue
            for hotel in hotels:
                hotel_price = hotel.get("total_price")
                if hotel_price is None:
                    continue
                total = flight_price + hotel_price
                if total <= budget:
                    combos.append({
                        "flight": flight,
                        "hotel": hotel,
                        "total_price": round(total, 2),
                        "remaining_budget": round(budget - total, 2),
                    })
        return combos

    def _cheapest_possible_total(self, flights: list, hotels: list) -> float:
        valid_flight_prices = [f["price"] for f in flights if f.get("price") is not None]
        valid_hotel_prices = [h["total_price"] for h in hotels if h.get("total_price") is not None]
        if not valid_flight_prices or not valid_hotel_prices:
            return None
        return round(min(valid_flight_prices) + min(valid_hotel_prices), 2)