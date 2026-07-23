# Serpapi code includes:
# Google Places
# Google Flights Deals
# Google Hotels
# Google Hotel Reviews
# Google Flights
# Google Flights Autocomplete

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
BASE_URL = "https://serpapi.com/search"


# ----------------------------------------------------
# General Request
# ----------------------------------------------------
def serpapi_request(params: dict) -> dict:
    params["api_key"] = SERPAPI_API_KEY

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    return data


# ----------------------------------------------------
# Flights
# ----------------------------------------------------
def search_flights(
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str = None,
) -> dict:

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

    return {
        "flights": data.get("best_flights", []),
        "google_flights_url": data.get("search_metadata", {}).get("google_flights_url"),
    }


# ----------------------------------------------------
# Flight Deals
# ----------------------------------------------------
def search_flight_deals(
    departure_id: str,
    currency: str = "JOD",
    **kwargs,
) -> dict:

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


# ----------------------------------------------------
# Flight Autocomplete
# ----------------------------------------------------
def autocomplete_flight_location(query: str) -> list[dict]:

    params = {
        "engine": "google_flights_autocomplete",
        "q": query,
    }

    data = serpapi_request(params)

    return data.get("suggestions", [])


# ----------------------------------------------------
# Google Places
# ----------------------------------------------------
def search_places(
    location: str,
    query: str = "attractions",
) -> list[dict]:

    params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "location": location,
        "m": 10000,
    }

    data = serpapi_request(params)

    return data.get("local_results", [])


# ----------------------------------------------------
# Hotel Reviews
# ----------------------------------------------------
def search_hotel_reviews(property_token: str) -> list[dict]:

    params = {
        "engine": "google_hotels_reviews",
        "property_token": property_token,
    }

    data = serpapi_request(params)

    return data.get("reviews", [])


# ----------------------------------------------------
# Hotels Search
# ----------------------------------------------------
def search_hotels(
    location: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 2,
    vacation_rentals: bool = False,
) -> list[dict]:

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

    if vacation_rentals:
        return [
            p
            for p in properties
            if p.get("type") != "hotel"
        ]

    return [
        p
        for p in properties
        if p.get("type") == "hotel"
    ]


# ----------------------------------------------------
# Hotel Details
# ----------------------------------------------------
def search_hotel_details(
    property_token: str,
    location: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 2,
) -> dict:
    """
    Fetch full property details, including:
      - 'prices': simple list of OTA booking providers
      - 'featured_prices': detailed list of OTA providers with
        per-room breakdown, images, and official/non-official flag
    """

    params = {
        "engine": "google_hotels",
        "property_token": property_token,
        "q": location,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": adults,
        "currency": "USD",
        "hl": "en",
        "gl": "us",
    }

    data = serpapi_request(params)

    return data