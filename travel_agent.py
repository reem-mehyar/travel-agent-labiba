import json

from api.openai_api import OpenAIClient
from datetime import date
from providers.service_provider import ServiceProvider
from skills.hotel_skill import HotelSkill
from skills.flight_skill import FlightSkill
from skills.currency_skill import CurrencySkill
from skills.weather_skill import WeatherSkill
from prompts import INTENT_PROMPT, SYSTEM_PROMPT, FINAL_RESPONSE_PROMPT


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
        }
        self.currency_skill = ServiceProvider.currency_skill()
        self.conversation_history = []
        self.pending_intent = {}

        # Maps each skill name to the result key it returns
        self.SKILL_RESULT_KEYS = {
            "hotel": "hotels",
            "flight": "flights",
            "weather": "weather",
        }

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
        response = self._generate_final_response(user_message=user_message, search_results=skill_result)
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
            result = skill.execute(intent_data)
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
        expected_keys = {
            self.SKILL_RESULT_KEYS[s]
            for s in requested_skills
            if s in self.SKILL_RESULT_KEYS
        }
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