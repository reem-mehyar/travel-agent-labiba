#Serpapi code includes 6 separate serpapis;
#Google Places Sites, Google Flights Deals, Google Hotels, Google Hotel Reviews, Google Flights, Google Flights Autocomplete

import requests
from dotenv import load_dotenv
import os

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
BASE_URL = "https://serpapi.com/search"


#General request function
def serpapi_request(params: dict) -> dict:

    params["api_key"] = SERPAPI_API_KEY
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])
    return data


#Flights API 
def search_flights(origin: str, destination: str, outbound_date: str, return_date: str = None) -> list[dict]:
    params = {
        "engine": "google_flights", 
        "departure_id": origin,
        "arrival_id": destination, 
        "outbound_date": outbound_date,
        "currency": "USD",
    }

    if return_date:
        params["return_date"] = return_date
        params["type"] = 1
    else: 
        params["type"] = 2

    data = serpapi_request(params)
    return data.get("best_flights", [])


#Flights Deals API
def search_flight_deals(departure_id: str, currency: str = "JOD", **kwargs) -> dict:
    #Optional kwargs are outbound/return date, travel duration, stops, max price
    params = {
        "engine": "google_flights_deals",
        "departure_id": departure_id,
        "currency": currency, 
    }

    params.update(kwargs)
    data = serpapi_request(params)
    return {
        "departure_informations": data.get("departure_informations", {}),
        "deals": data.get("deals", []),
    }
    

#Flights Autocomplete API
def autocomplete_flight_location(query: str) -> list[dict]:
    params = {"engine": "google_flights_autocomplete",
              "q": query,
            }
    
    data = serpapi_request(params)
    return data.get("suggestions", [])


#Places Sites API
def search_places(location: str, query: str = "attractions") -> list[dict]:
    params = {"engine": "google_maps",
              "q": query,
              "type": "search",
              "location": location,
              "m": 10000
              }
    
    data = serpapi_request(params)
    return data.get("local_results", [])
    

#Hotel Reviews API 
def search_hotel_reviews(property_token: str) -> list[dict]:
    params = {
        "engine": "google_hotels_reviews",
        "property_token": property_token,
    }
    data = serpapi_request(params)
    return data.get("reviews", [])


#Hotel API
def search_hotels(location: str, check_in_date: str, check_out_date: str, adults: int = 2, vacation_rentals: bool = False) -> list[dict]:
    params = {
        "engine": "google_hotels",
        "q": location,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date, 
        "adults": adults, 
        "vacation_rentals": "true" if vacation_rentals else "false",
    }

    data = serpapi_request(params)
    properties = data.get("properties", [])

    if not vacation_rentals:
        properties = [p for p in properties if p.get("type") == "hotel"]
    else:
        properties = [p for p in properties if p.get("type") != "hotel"]
    return properties
    