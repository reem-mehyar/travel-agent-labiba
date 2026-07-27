

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

from skills.attractions_skill import AttractionSkill

skill = AttractionSkill()

# Test nearby search
result1 = skill.execute({
    "attraction_request_type": "search_nearby",
    "search_query": "coffee shops",
    "anchor_location": "Grand Hyatt Athens, Athens",
})
print(result1)

# Test distance
result2 = skill.execute({
    "attraction_request_type": "distance",
    "directions_origin": "Grand Hyatt Athens",
    "directions_destination": "Acropolis Museum",
    "travel_mode": "walking",
})
print(result2)