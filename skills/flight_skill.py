from api.serpapi_api import search_flights, autocomplete_flight_location
from skills.date_validation import validate_dates

class FlightSkill:
    
    REQUIRED_FIELDS = ["departure_city", "destination_city", "departure_date"]

    def execute(self, intent_data: dict) -> dict:
        missing = {
            field: None
            for field in self.REQUIRED_FIELDS
            if intent_data.get(field) is None
        }
        if missing:
            return missing

        origin_code = self._resolve_airport_code(intent_data["departure_city"])
        destination_code = self._resolve_airport_code(intent_data["destination_city"])
        departure_date = intent_data["departure_date"]
        return_date = intent_data.get("return_date")

        validation_error = validate_dates(departure_date, return_date)
        if validation_error:
            return {"flights": [], "note": validation_error}

        if len(origin_code) != 3 or len(destination_code) !=3:
            return {"flights": [], "note": f"Could not find a specific airport for the given location. Please specify a city rather than a country or region."}

        raw_results = search_flights(origin_code, destination_code, departure_date, return_date)

        cleaned_flights = [
            {
                "airline": f.get("flights", [{}])[0].get("airline"),
                "price": f.get("price"),
                "duration": f.get("total_duration"),
                "stops": len(f.get("layovers", [])),
            }
            for f in raw_results
        ]

        return {"flights": cleaned_flights}

    def _resolve_airport_code(self, city_name: str) -> str:

        suggestions = autocomplete_flight_location(city_name)
        if suggestions:
            top_match = suggestions[0]
            airports = top_match.get("airports", [])
            if airports:
                return airports[0].get("id", city_name)  
        return city_name