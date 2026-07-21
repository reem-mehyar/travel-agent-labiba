

from api.serpapi_api import search_hotel_reviews, search_hotels, search_flights, search_places, search_flight_deals, autocomplete_flight_location
import json 

#result = search_flight_deals("AMM", outbound_date= "2026-08-01", return_date = "2026-08-05")
"""result = search_flight_deals(
    "AMM",
    outbound_date="2026-09-01,2026-09-30",
    travel_duration=5,
    stops=0,
    max_price=500,
)

#for deal in result["deals"]:
    print(deal.get("name"), deal.get("price"), deal.get("discount_percentage"))

"""

"""attractions = search_places(location="Athens", query="attractions")
for place in attractions:
    print(place.get("title"), "-", place.get("address"), "-", place.get("rating"))"""


from api.serpapi_api import search_flights

results = search_flights("NRT", "ICN", "2026-07-22")
print(results)