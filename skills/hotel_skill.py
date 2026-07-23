from api.serpapi_api import search_hotels, search_hotel_details
from skills.date_validation import validate_dates

import requests


class HotelSkill:

    REQUIRED_FIELDS = ["location", "check_in", "check_out"]

    # How many top hotels to enrich with OTA booking providers.
    # Each lookup costs one extra SerpAPI call, so keep this small.
    MAX_DETAILS_LOOKUPS = 3

    def execute(self, intent_data: dict) -> dict:

        missing = self._get_missing_fields(intent_data)
        if missing:
            return missing

        location = intent_data["location"]
        check_in = intent_data["check_in"]
        check_out = intent_data["check_out"]
        adults = intent_data.get("adults") or 2

        validation_error = validate_dates(check_in, check_out)
        if validation_error:
            return {"hotels": [], "note": validation_error}

        raw_results = self._search_hotels_safe(location, check_in, check_out, adults)

        if raw_results is None:
            return {
                "hotels": [],
                "note": f"No hotels for '{location}' found. Please try another location.",
            }

        if not raw_results:
            return {
                "hotels": [],
                "note": f"No hotels available in '{location}' for the selected dates.",
            }

        cleaned_hotels = self._clean_hotels(raw_results)

        self._attach_booking_providers(
            cleaned_hotels,
            location=location,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
        )

        return {"hotels": cleaned_hotels}

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
    # Search
    # ------------------------------------------------------------

    def _search_hotels_safe(
        self,
        location: str,
        check_in: str,
        check_out: str,
        adults: int,
    ):
        """
        Wraps search_hotels with error handling.
        Returns None on failure, [] or a list of raw results otherwise.
        """
        try:
            return search_hotels(location, check_in, check_out, adults)

        except (RuntimeError, requests.RequestException):
            return None

    # ------------------------------------------------------------
    # Cleaning
    # ------------------------------------------------------------

    def _clean_hotels(self, raw_results: list[dict]) -> list[dict]:
        return [
            {
                "name": h.get("name"),
                "price_per_night": h.get("rate_per_night", {}).get("lowest"),
                "total_price": h.get("total_rate", {}).get("lowest"),
                "rating": h.get("overall_rating"),
                "property_token": h.get("property_token"),
                "booking_url": h.get("link"),
                "details_url": h.get("serpapi_property_details_link"),
            }
            for h in raw_results
        ]

    # ------------------------------------------------------------
    # OTA booking providers enrichment
    # ------------------------------------------------------------

    def _attach_booking_providers(
        self,
        cleaned_hotels: list[dict],
        location: str,
        check_in: str,
        check_out: str,
        adults: int,
    ) -> None:
        """
        Enrich the first N hotels with OTA booking providers
        (Booking.com, Expedia, Agoda, etc.) extracted from both
        'prices' and 'featured_prices' in the Property Details API.

        Failures on individual lookups are isolated per-hotel and
        never break the overall hotel search.
        """

        for hotel in cleaned_hotels[: self.MAX_DETAILS_LOOKUPS]:

            property_token = hotel.get("property_token")

            if not property_token:
                hotel["booking_providers"] = []
                continue

            details = self._get_hotel_details_safe(
                property_token=property_token,
                location=location,
                check_in=check_in,
                check_out=check_out,
                adults=adults,
            )

            if details is None:
                hotel["booking_providers"] = []
                continue

            hotel["booking_providers"] = self._extract_booking_providers(details)

    def _get_hotel_details_safe(
        self,
        property_token: str,
        location: str,
        check_in: str,
        check_out: str,
        adults: int,
    ):
        try:
            return search_hotel_details(
                property_token=property_token,
                location=location,
                check_in_date=check_in,
                check_out_date=check_out,
                adults=adults,
            )

        except (RuntimeError, requests.RequestException):
            return None

    def _extract_booking_providers(self, details: dict) -> list[dict]:
        """
        Merges 'prices' (simple) and 'featured_prices' (detailed) into
        a single deduplicated list of booking providers, keyed by source name.
        """

        providers = {}

        for p in details.get("prices", []):
            source = p.get("source")
            if not source:
                continue

            providers[source] = {
                "provider": source,
                "link": p.get("link"),
                "official": False,
                "price_per_night": p.get("rate_per_night", {}).get("lowest"),
                "total_price": p.get("total_rate", {}).get("lowest"),
                "free_cancellation": p.get("free_cancellation", False),
            }

        for f in details.get("featured_prices", []):
            source = f.get("source")
            if not source:
                continue

            providers[source] = {
                "provider": source,
                "link": f.get("link"),
                "official": f.get("official", False),
                "price_per_night": f.get("rate_per_night", {}).get("lowest"),
                "total_price": f.get("total_rate", {}).get("lowest"),
                "free_cancellation": f.get("free_cancellation", False),
            }

        return list(providers.values())