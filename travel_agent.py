import json

from api.openai_api import OpenAIClient
from datetime import date
from providers.service_provider import ServiceProvider
from skills.hotel_skill import HotelSkill
from skills.flight_skill import FlightSkill
from skills.planner_skill import PlannerSkill
from skills.attractions_skill import AttractionSkill
from skills.currency_skill import CurrencySkill
from skills.weather_skill import WeatherSkill
from skills.itinerary_skill import ItinerarySkill
from skills.visa_skill import VisaSkill
from skills.recommendation_skill import RecommendationSkill
from prompts import INTENT_PROMPT, SYSTEM_PROMPT, FINAL_RESPONSE_PROMPT, ITINERARY_PROMPT


RESET_PHRASES = {"start over", "new search", "reset", "forget that", "cancel"}
TOPIC_FIELDS = ["destination_city", "location"]


class TravelAgent:
    """
    Main workflow orchestrator for the AI Travel Agent.

    Responsibilities:
        - Receive user requests.
        - Detect user intent.
        - Execute the correct travel skill(s).
        - Generate the final response.
    """

    def __init__(self) -> None:

        self.openai_client = ServiceProvider.openai()

        self.skills = {
            "hotel": HotelSkill(),
            "flight": FlightSkill(),
            "weather": WeatherSkill(),
            "planner": PlannerSkill(),
            "visa": VisaSkill(),
            "attractions": AttractionSkill(),
            "recommendation": RecommendationSkill(),
        }
        self.currency_skill = ServiceProvider.currency_skill()

        # ItinerarySkill is never selected via intent — it's triggered
        # programmatically right after a successful "planner" run, so it
        # lives outside self.skills (which is only for intent-selectable skills).
        self.itinerary_skill = ItinerarySkill()

        self.conversation_history = []
        self.pending_intent = {}

        # Maps each skill name to the result key it returns
        self.SKILL_RESULT_KEYS = {
            "hotel": "hotels",
            "flight": "flights",
            "weather": "weather",
            "planner": "planned_trip",
            "visa": "visa",
        }

        self.pending_intent = {}
        self._skill_result_cache = {}

    def handle_request(self, user_message: str) -> str:
        """
        Handle a complete user request, with short-term memory across turns.
        """
        # 1. Explicit reset command
        if user_message.strip().lower() in RESET_PHRASES:
            self.pending_intent = {}
            self.conversation_history = []
            return "Sure, let's start fresh. Where would you like to go?"

        # 2. Detect intent from this message (with conversation context)
        new_intent = self._detect_intent(user_message)
        requested_skills = new_intent.get("skills", [])

        if "none" in requested_skills:
            response = (
                "I'm a travel assistant, so I can only help with flight, hotel, "
                "and weather-related requests. Is there a trip I can help you plan?"
            )
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        if "unclear" in requested_skills:
            response = (
                "I'd be happy to help with that trip! Are you looking for "
                "flights, hotels, weather, or a combination?"
            )
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        # 3. Topic-change guard (generalized across destination_city / location)
        if self._detect_topic_change(self.pending_intent, new_intent):
            self.pending_intent = {}

        # 4. Merge new info into whatever was already collected this session
        merged_intent = {
            **self.pending_intent,
            **{k: v for k, v in new_intent.items() if v is not None},
        }
        # skills requested should reflect the current message, not stale history
        merged_intent["skills"] = requested_skills

        # Handle visa advice without calling the Visa API
        if (
            "visa" in requested_skills
            and merged_intent.get("visa_intent") == "advice"
        ):
            self.pending_intent = {}

            response = self._generate_final_response(
                user_message=user_message,
                search_results={}
            )

            self.conversation_history.append(
                {"role": "assistant", "content": response}
            )

            return response

        # Handle recommendation workflow
        if "recommendation" in requested_skills:
            response = self._handle_recommendation(
                user_message=user_message,
                intent_data=merged_intent,
            )

            self.pending_intent = {}
            self.conversation_history.append(
                {"role": "assistant", "content": response}
            )

            return response

        # 5. Execute the requested skill(s)
        skill_result = self._execute_skill(merged_intent)

        # 6. Still missing fields -> remember progress, ask for the rest
        if self._missing_information(skill_result, requested_skills):
            self.pending_intent = merged_intent
            response = self._generate_missing_information_response(skill_result)
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        # 6.5 Apply currency conversion if requested
        requested_currency = merged_intent.get("currency")
        if requested_currency:
            skill_result = self.currency_skill.convert_results(skill_result, requested_currency)

        # 7. Completed successfully -> reset for next request
        self.pending_intent = {}

        # 7.5 If the planner produced a valid trip, automatically build
        # and generate a day-by-day itinerary from the remaining budget.
        if "planner" in requested_skills and "planned_trip" in skill_result:
            response = self._handle_planner_result(
                user_message=user_message,
                intent_data=merged_intent,
                planner_result=skill_result,
            )
        else:
            response = self._generate_final_response(
                user_message=user_message,
                search_results=skill_result,
            )

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _detect_intent(self, user_message: str) -> dict:

        self.conversation_history.append({"role": "user", "content": user_message})
        today_str = date.today().isoformat()

        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in self.conversation_history[-12:]
        )
        contextualized_input = (
            f"Today's date is {today_str}.\n\n"
            f"Conversation so far:\n{history_text}\n\n"
            f"Extract the current travel intent, using earlier turns to fill in "
            f"anything not repeated in the latest message."
        )

        intent = self.openai_client.generate_response(
            system_prompt=INTENT_PROMPT,
            user_input=contextualized_input,
            as_json=True,
        )
        print(intent)

        if not isinstance(intent, dict):
            raise RuntimeError("Intent detection did not return a dictionary.")
        if "skills" not in intent:
            raise RuntimeError("Intent data does not contain a skills list.")
        return intent

    def _execute_skill(self, intent_data: dict) -> dict:
        """
        Execute every requested skill and merge their results.
        """
        skill_names = intent_data.get("skills", [])
        combined_result = {}

        for skill_name in skill_names:
            skill = self.skills.get(skill_name)
            if skill is None:
                continue

            cached = self._skill_result_cache.get(skill_name)
            if cached and cached["snapshot"] == intent_data:
                combined_result.update(cached["result"])
                continue

            result = skill.execute(intent_data)
            self._skill_result_cache[skill_name] = {"snapshot": dict(intent_data), "result": result}
            combined_result.update(result)

        return combined_result

    def _generate_missing_information_response(self, missing_fields: dict) -> str:
        field_names = ", ".join(
            field.replace("_", " ")
            for field in missing_fields.keys()
        )

        return (
            "I need some additional information before I can continue.\n\n"
            f"Missing information: {field_names}."
        )

    def _missing_information(self, skill_result: dict, requested_skills: list) -> bool:
        """
        Determine whether any of the requested skills failed to return
        their expected result key.
        """
        expected_keys = set()
        for s in requested_skills:
            if s == "attractions":
                expected_keys.update({"nearby_places", "directions"})
            elif s in self.SKILL_RESULT_KEYS:
                expected_keys.add(self.SKILL_RESULT_KEYS[s])
       
        return not any(key in skill_result for key in expected_keys)

    def _detect_topic_change(self, old_intent: dict, new_intent: dict) -> bool:
        """
        Returns True if a core location/topic field changed between turns,
        signaling this is a new, unrelated request.
        """
        for field in TOPIC_FIELDS:
            old_value = old_intent.get(field)
            new_value = new_intent.get(field)
            if old_value and new_value and old_value != new_value:
                return True
        return False

    def _generate_final_response(self, user_message: str, search_results: dict) -> str:

        currency_note = (
            f"\n\nAll prices are in {search_results.get('currency', 'USD')}."
            if search_results.get("currency") else ""
        )

        final_prompt = (
            f"Original User Request:\n"
            f"{user_message}\n\n"
            f"Search Results:\n"
            f"{json.dumps(search_results, indent=2, ensure_ascii=False)}"
            f"{currency_note}"
        )

        return self.openai_client.generate_response(
            system_prompt=FINAL_RESPONSE_PROMPT,
            user_input=final_prompt,
        )



    def _handle_recommendation(
        self,
        user_message: str,
        intent_data: dict,
    ) -> str:

        recommendation_result = self.skills["recommendation"].execute(intent_data)

        destinations = recommendation_result.get(
            "recommended_destinations",
            []
        )

        if not destinations:
            return "I couldn't find suitable destinations."

        trips = []

        for destination in destinations:

            trip_intent = intent_data.copy()

            # -----------------------------
            # Prepare Flight + Hotel request
            # -----------------------------
            trip_intent["destination_city"] = destination
            trip_intent["location"] = destination
            trip_intent["check_in"] = intent_data["departure_date"]
            trip_intent["check_out"] = intent_data["return_date"]

            flight_result = self.skills["flight"].execute(trip_intent)
            hotel_result = self.skills["hotel"].execute(trip_intent)

            flights = flight_result.get("flights", [])
            hotels = hotel_result.get("hotels", [])

            if not flights or not hotels:
                continue

            cheapest_flight = flights[0]
            cheapest_hotel = hotels[0]

            flight_price = cheapest_flight.get("price") or 0

            raw_hotel_price = cheapest_hotel.get("total_price") or 0
            if isinstance(raw_hotel_price, str):
                hotel_price = float(
                    raw_hotel_price.replace("US$", "").replace("$", "").replace(",", "").strip() or 0
                )
            else:
                hotel_price = raw_hotel_price

            total_cost = flight_price + hotel_price
            budget = intent_data.get("budget")

            # -------- Display prices with currency --------
            hotel_display = cheapest_hotel.copy()

            if hotel_display.get("price_per_night") is not None:
                hotel_display["price_per_night"] = f"${hotel_display['price_per_night']}"

            if hotel_display.get("total_price") is not None:
                hotel_display["total_price"] = f"${hotel_display['total_price']}"

            flight_display = cheapest_flight.copy()

            if flight_display.get("price") is not None:
                flight_display["price"] = f"${flight_display['price']}"

            trips.append({
                "destination": destination,
                "flight": flight_display,
                "hotel": hotel_display,

                # formatted values for the LLM
                "total_cost": f"${total_cost}",
                "remaining_budget": (
                    f"${budget - total_cost}" if budget is not None else None
                ),
                "over_budget": (
                    f"${total_cost - budget}"
                    if budget is not None and total_cost > budget
                    else "$0"
                ),

                # numeric values if you ever need calculations
                "total_cost_value": total_cost,
                "fits_budget": (
                    total_cost <= budget
                    if budget is not None
                    else None
                ),
            })

        if not trips:
            return (
                "I couldn't find any destinations with available "
                "flights and hotels."
            )

        trips.sort(key=lambda x: x["total_cost_value"])

        # ---------------------------------
        # Choose Best Value recommendation
        # ---------------------------------
        best_trip = trips[0]

        planner_intent = intent_data.copy()
        planner_intent["destination_city"] = best_trip["destination"]
        planner_intent["location"] = best_trip["destination"]
        planner_intent["check_in"] = intent_data["departure_date"]
        planner_intent["check_out"] = intent_data["return_date"]

        planner_result = self.skills["planner"].execute(planner_intent)

        # ---------------------------------
        # Build itinerary for Best Value trip
        # ---------------------------------
        itinerary_result = self.itinerary_skill.execute(
            planner_intent,
            planner_result,
        )
        itinerary_payload = itinerary_result.get("itinerary_payload")

        # ---------------------------------
        # Generate final response
        # ---------------------------------
        search_results = {
            "recommended_trips": trips,
            "budget": intent_data.get("budget"),
            "currency": intent_data.get("currency", "USD"),
        }

        if planner_result.get("planned_trip"):
            search_results["planner_result"] = planner_result

        if itinerary_payload:
            search_results["itinerary"] = itinerary_payload

        return self._generate_final_response(
            user_message=user_message,
            search_results=search_results,
        )

    # ------------------------------------------------------------
    # Itinerary generation (triggered automatically after PlannerSkill)
    # ------------------------------------------------------------

    def _handle_planner_result(
        self,
        user_message: str,
        intent_data: dict,
        planner_result: dict,
    ) -> str:
        """
        Automatically builds and generates a day-by-day itinerary after a
        successful PlannerSkill run. Falls back to the standard
        FINAL_RESPONSE_PROMPT formatting if an itinerary cannot be built
        (e.g. missing dates, no valid combo), so the user still gets a
        useful response instead of an error.
        """

        itinerary_result = self.itinerary_skill.execute(intent_data, planner_result)
        itinerary_payload = itinerary_result.get("itinerary_payload")

        if itinerary_payload is None:
            return self._generate_final_response(
                user_message=user_message,
                search_results=planner_result,
            )

        return self._generate_itinerary_response(
            user_message=user_message,
            itinerary_payload=itinerary_payload,
        )

    def _generate_itinerary_response(
        self,
        user_message: str,
        itinerary_payload: dict,
    ) -> str:
        """
        Sends the structured itinerary payload to OpenAI using
        ITINERARY_PROMPT. This is the ONLY place ItinerarySkill's output
        ever reaches OpenAI — the Skill itself never calls it directly,
        preserving the "Skills never talk to OpenAI" architecture rule.
        """

        currency_note = (
            f"\n\nAll prices are in {itinerary_payload.get('currency', 'USD')}."
            if itinerary_payload.get("currency") else ""
        )

        prompt = (
            f"Original User Request:\n"
            f"{user_message}\n\n"
            f"Itinerary Data:\n"
            f"{json.dumps(itinerary_payload, indent=2, ensure_ascii=False)}"
            f"{currency_note}"
        )

        return self.openai_client.generate_response(
            system_prompt=ITINERARY_PROMPT,
            user_input=prompt,
        )