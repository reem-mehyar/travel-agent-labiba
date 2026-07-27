from datetime import datetime


class ItinerarySkill:
    """
    Prepares a structured payload describing the trip's remaining budget,
    duration, and selected flight/hotel, ready to be reasoned over by
    OpenAI to produce a day-by-day itinerary.

    This Skill NEVER calls OpenAI. It only validates, calculates, and
    organizes data — following the same "dumb Skill" pattern as
    HotelSkill and FlightSkill in this project.
    """

    REQUIRED_FIELDS = ["destination_city", "check_in", "check_out"]

    def execute(self, intent_data: dict, planner_result: dict) -> dict:
        """
        Args:
            intent_data:
                The structured intent extracted by OpenAI (same object
                already used by PlannerSkill/FlightSkill/HotelSkill).

            planner_result:
                The dict returned by PlannerSkill.execute(), expected to
                contain "planned_trip" (a list of combos) and "currency".

        Returns:
            {"itinerary_payload": {...}} on success, or
            {"itinerary_payload": None, "note": "..."} if an itinerary
            cannot be built (missing fields, invalid dates, no combo).
        """

        missing = self._get_missing_fields(intent_data)
        if missing:
            return {
                "itinerary_payload": None,
                "note": "Missing information required to build an itinerary.",
            }

        best_combo = self._get_best_combo(planner_result)
        if best_combo is None:
            return {
                "itinerary_payload": None,
                "note": "No valid flight + hotel combination available to build an itinerary.",
            }

        trip_duration_days = self._calculate_trip_duration(
            intent_data["check_in"],
            intent_data["check_out"],
        )

        if trip_duration_days is None:
            return {
                "itinerary_payload": None,
                "note": "Invalid or missing trip dates; cannot calculate itinerary duration.",
            }

        remaining_budget = best_combo.get("remaining_budget")
        if remaining_budget is None:
            return {
                "itinerary_payload": None,
                "note": "Remaining budget is not available for the selected combination.",
            }

        currency = planner_result.get("currency", "USD")
        daily_budget = round(remaining_budget / trip_duration_days, 2)

        payload = {
            "destination": intent_data.get("destination_city"),
            "trip_duration_days": trip_duration_days,
            "currency": currency,
            "total_trip_cost": best_combo.get("total_price"),
            "remaining_budget": remaining_budget,
            "daily_budget": daily_budget,
            "flight": {
                "airline": best_combo["flight"].get("airline"),
                "price": best_combo["flight"].get("price"),
                "duration": best_combo["flight"].get("duration"),
                "stops": best_combo["flight"].get("stops"),
            },
            "hotel": {
                "name": best_combo["hotel"].get("name"),
                "rating": best_combo["hotel"].get("rating"),
                "total_price": best_combo["hotel"].get("total_price"),
                "booking_url": best_combo["hotel"].get("booking_url"),
            },
        }

        return {"itinerary_payload": payload}

    # ------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------

    def _get_missing_fields(self, intent_data: dict) -> dict:
        return {
            field: None
            for field in self.REQUIRED_FIELDS
            if intent_data.get(field) is None
        }

    # ------------------------------------------------------------
    # Combo selection
    # ------------------------------------------------------------

    def _get_best_combo(self, planner_result: dict) -> dict | None:
        """
        PlannerSkill already sorts combos by total_price ascending and
        returns the top 5. The first entry is the cheapest valid combo,
        which we treat as "best" — no duplicate sorting logic here.
        """
        planned_trip = planner_result.get("planned_trip", [])
        return planned_trip[0] if planned_trip else None

    # ------------------------------------------------------------
    # Duration calculation
    # ------------------------------------------------------------

    def _calculate_trip_duration(self, check_in: str, check_out: str) -> int | None:
        try:
            start = datetime.strptime(check_in, "%Y-%m-%d")
            end = datetime.strptime(check_out, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None

        duration = (end - start).days
        return duration if duration > 0 else None