import json

from api.openai_api import OpenAIClient
from datetime import date
from skills.hotel_skill import HotelSkill
from skills.flight_skill import FlightSkill
from skills.currency_skill import CurrencySkill

from prompts import INTENT_PROMPT, SYSTEM_PROMPT, FINAL_RESPONSE_PROMPT


RESET_PHRASES = {"start over", "new search", "reset", "forget that", "cancel"}

class TravelAgent:
    """
    Main workflow orchestrator for the AI Travel Agent.

    Responsibilities:
        - Receive user requests.
        - Detect user intent.
        - Execute the correct travel skill.
        - Generate the final response.
    """

    def __init__(self) -> None:
        
        self.openai_client = OpenAIClient()

        self.skills = {"hotel": HotelSkill(), "flight": FlightSkill()}
        self.currency_skill = CurrencySkill()
        self.conversation_history = []
        self.pending_intent = {}

    def handle_request(self, user_message: str) -> str:
        """
        Handle a complete user request, with short-term memory across turns.

        Args:
            user_message:
                The user's original request.

        Returns:
            Final response returned to the user.
        """
        # 1. Explicit reset command
        if user_message.strip().lower() in RESET_PHRASES:
            self.pending_intent = {}
            self.conversation_history = []
            return "Sure, let's start fresh. Where would you like to go?"

        # 2. Detect intent from this message (with conversation context)
        new_intent = self._detect_intent(user_message)

        if new_intent.get("skill") == "none":
            response = ("I'm a travel assistant, so I can only help with travel related inquiries. Is there a trip I can help you plan?")
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        if new_intent.get("skill") == "unclear":
            response = ("I'd be happy to help with that trip! Are you looking for hotels, flights, or both?")
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
    
        # 3. Topic-change guard: if destination changed, discard old pending fields
        old_destination = self.pending_intent.get("destination_city")
        new_destination = new_intent.get("destination_city")
        if old_destination and new_destination and new_destination != old_destination:
            self.pending_intent = {}

        # 4. Merge new info into whatever was already collected this session
        merged_intent = {
            **self.pending_intent,
            **{k: v for k, v in new_intent.items() if v is not None},
        }

        # 5. Execute the matching skill
        skill_result = self._execute_skill(merged_intent)

        # 6. Still missing fields -> remember progress, ask for the rest
        if self._missing_information(skill_result):
            self.pending_intent = merged_intent
            response = self._generate_missing_information_response(skill_result)
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

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
                f"{m['role']}: {m['content']}" for m in self.conversation_history[-12:]  # last few turns
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
        if "skill" not in intent:
            raise RuntimeError("Intent data does not contain a skill.")
        return intent
        
    def _execute_skill(self, intent_data: dict) -> dict:
        """
        Execute the appropriate travel skill.

        Args:
            intent_data:
                Structured intent returned by OpenAI.

        Returns:
            Dictionary returned by the selected skill.

        Raises:
            RuntimeError:
                If the requested skill is not supported.
        """
        skill_name = intent_data.get("skill")

        if skill_name == "both":
            hotel_result = self.skills["hotel"].execute(intent_data)
            flight_result = self.skills["flight"].execute(intent_data)
            combined = {}
            combined.update(hotel_result)
            combined.update(flight_result)
            return combined
        
        skill = self.skills.get(skill_name)
        if skill is None:
            raise RuntimeError(f"Unsupported skill: {skill_name}")

        return skill.execute(intent_data)

    def _generate_missing_information_response(
        self,
        missing_fields: dict,
    ) -> str:
        """
        Generate a clarification request when required fields
        are missing.
        """
        field_names = ", ".join(
            field.replace("_", " ")
            for field in missing_fields.keys()
        )

        return (
            "I need some additional information before I can continue.\n\n"
            f"Missing information: {field_names}."
        )
    
    def _missing_information(
        self,
        skill_result: dict,
    ) -> bool:
        """
        Determine whether the selected skill is requesting
        additional information from the user.

        Args:
            skill_result:
                Result returned by the skill.

        Returns:
            True if required information is missing.
        """

        return not (
    "hotels" in skill_result
    or "flights" in skill_result
            )

    def _generate_final_response(self, user_message: str, search_results: dict,) -> str:
        """
        Generate the final natural-language response.
        """
        final_prompt = (
            f"Original User Request:\n"
            f"{user_message}\n\n"
            f"Search Results:\n"
            f"{json.dumps(search_results, indent=2, ensure_ascii=False)}")

        return self.openai_client.generate_response(
            system_prompt=FINAL_RESPONSE_PROMPT,user_input=final_prompt)
