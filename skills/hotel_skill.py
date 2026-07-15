from api.serpapi_api import search_hotels
from skills.date_validation import validate_dates


class HotelSkill:

    REQUIRED_FIELDS = ["location", "check_in", "check_out"]

    def execute(self, intent_data:dict) -> dict:

        missing = {
            field: None
            for field in self.REQUIRED_FIELDS
            if intent_data.get(field) is None
        }
        if missing:
            return missing
        
        location = intent_data["location"]
        check_in = intent_data["check_in"]
        check_out = intent_data["check_out"]
        adults = intent_data.get("adults") or 2

        validation_error = validate_dates(check_in, check_out)
        if validation_error:
            return {"hotels": [], "note": validation_error}

        raw_results = search_hotels(location, check_in, check_out, adults)

        cleaned_hotels = [
            {
                "name": h.get("name"),
                "price_per_night": h.get("rate_per_night", {}).get("lowest"),
                "total_price": h.get("total_rate", {}).get("lowest"),
                "rating": h.get("overall_rating"),
                "property_token": h.get("property_token"),
            }
            for h in raw_results
        ]
        
        return {"hotels": cleaned_hotels}