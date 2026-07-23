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

        origin_info = self._resolve_airport_code(intent_data["departure_city"])
        destination_info = self._resolve_airport_code(intent_data["destination_city"])
        origin_code = origin_info["code"]
        destination_code = destination_info["code"]
        departure_date = intent_data["departure_date"]
        return_date = intent_data.get("return_date")
        
        invalid_cities = []
        if len(origin_code) != 3:
            invalid_cities.append(f"departure city '{intent_data['departure_city']}'")
        if len(destination_code) != 3:
            invalid_cities.append(f"destination city '{intent_data['destination_city']}'")

        if invalid_cities:
            return {"flights": [], "note": (f"Could not find a specific airport for the {', '.join(invalid_cities)}. "
            f"Please provide a valid city name.")}
        
        validation_error = validate_dates(departure_date, return_date)
        if validation_error:
            return {"flights": [], "note": validation_error}
        flight_data = search_flights(
           origin_code,
           destination_code,
           departure_date,
           return_date,
                         )
        
       
        raw_results = flight_data["flights"]
        
        google_flights_url = flight_data["google_flights_url"]
       

        cleaned_flights = [
            {
                "airline": f.get("flights", [{}])[0].get("airline"),
                "price": f.get("price"),
                "duration": f.get("total_duration"),
                "stops": len(f.get("layovers", [])),
            }
            for f in raw_results
        ]

        return {
        "flights": cleaned_flights,
        "google_flights_url": google_flights_url,
               }
    def _resolve_airport_code(self, city_name: str) -> str:

        try:
            suggestions = autocomplete_flight_location(city_name)
        except RuntimeError:
            return {"code": city_name, "resolved_name": None}
        
        if suggestions:
            top_match = suggestions[0]
            airports = top_match.get("airports", [])
            if airports:
                return {"code": airports[0].get("id", city_name), 
                        "resolved_name": top_match.get("name")}
        
        return {"code": city_name, "resolved_name": None,}