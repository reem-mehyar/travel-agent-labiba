
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

from api.serpapi_api import serpapi_request
import json

data = serpapi_request({
    "engine": "google_maps_directions",
    "start_addr": "Revolver Hotel Glasgow",
    "end_addr": "Pineapple Espresso, Glasgow",
    "travel_mode": 2,  # walking
})

directions = data.get("directions", [])
print("directions count:", len(directions))
if directions:
    print("top-level keys:", list(directions[0].keys()))
    trips = directions[0].get("trips", [])
    print("trips count:", len(trips))
    if trips:
        print("trip keys:", list(trips[0].keys()))
        print("details count:", len(trips[0].get("details", [])))