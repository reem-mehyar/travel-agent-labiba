from api.serpapi_api import search_places_near, get_directions


class AttractionSkill:

    """
    Handles:
    - finding places
    - getting distance/duration between two named places
    """

    def execute(self, intent_data: dict) -> dict:
        request_type = intent_data.get("attraction_request_type")

        if request_type == "search_nearby":
            return self._search_nearby(intent_data)
        
        elif request_type == "distance":
            return self._get_distance(intent_data)
        
        else:
            return {"attraction_request_type": None}
        
    def _search_nearby(self, intent_data: dict) -> dict:
        
        query = intent_data.get("search_query")
        anchor_location = intent_data.get("anchor_location")

        missing = {}
        if query is None:
            missing["search_query"] = None
        if anchor_location is None:
            missing["anchor_location"] = None
        if missing:
            return missing
        
        try:
            results = search_places_near(anchor_location, query)
        except Exception:
            return {"nearby_places": [], "note": f"Could not find results for '{query}' near '{anchor_location}'."}
    
        if not results:
            return {"nearby_places": [], "note": f"Could not locate '{anchor_location}' to search nearby."}

        cleaned = [
            {
                "name": p.get("title"),
                "address": p.get("address"),
                "rating": p.get("rating"),
                "type": p.get("type"),
            }
            for p in results[:8]
        ]

        return {"nearby_places": cleaned, "anchor_location": anchor_location}

    def _get_distance(self, intent_data: dict) -> dict:
        origin = intent_data.get("directions_origin")
        destination = intent_data.get("directions_destination")
        mode = intent_data.get("travel_mode") or "driving"

        missing = {}
        
        if origin is None: 
            missing["directions_origin"] = None
        
        if destination is None:
            missing["directions_destination"] = None

        if missing:
            return missing
        
        try: 
            result = get_directions(origin, destination, mode=mode)
        except Exception:
            return {"directions": {}, "note": f"Could not find directions from '{origin}' to '{destination}'."}

        if not result:
            return {"directions": {}, "note": f"No route found from '{origin}' to '{destination}'."}
        
        return {"directions": result}
    
