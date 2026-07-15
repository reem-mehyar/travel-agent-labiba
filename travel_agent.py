import json

from api.openai_api import OpenAIClient
from datetime import date
from skills.hotel_skill import HotelSkill
from skills.flight_skill import FlightSkill

from prompts import (
    SYSTEM_PROMPT,
    INTENT_PROMPT,
    FINAL_RESPONSE_PROMPT,
)

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

        self.skills = {
            "hotel": HotelSkill(),
            "flight": FlightSkill(),
        }

    def handle_request(self, user_message: str) -> str:
        """
        Handle a complete user request.

        Args:
            user_message:
                The user's original request.

        Returns:
            Final response returned to the user.
        """

        intent_data = self._detect_intent(user_message)

        skill_result = self._execute_skill(intent_data)

        if self._missing_information(skill_result):

            return self._generate_missing_information_response(
                skill_result
            )

        return self._generate_final_response(
            user_message=user_message,
            search_results=skill_result,
        )



    def _generate_missing_information_response(self, missing_fields: dict) -> str:
    
        field_names = ", ".join(
            field.replace("_", " ")
            for field in missing_fields.keys()
        )

        return (
            "I need some additional information before I can continue.\n\n"
            f"Missing information: {field_names}."
        )
    
    def _detect_intent(self, user_message: str) -> dict:
        today_str = date.today().isoformat()
        contextualized_input = f"Today's date is {today_str}.\n\nUser request: {user_message}"

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
        
    def _execute_skill(
        self,
        intent_data: dict,
    ) -> dict:
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

        skill_name = intent_data["skill"]

        skill = self.skills.get(skill_name)

        if skill is None:
            raise RuntimeError(
                f"Unsupported skill: {skill_name}"
            )

        return skill.execute(intent_data)

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
            f"{json.dumps(search_results, indent=2, ensure_ascii=False)}"
        )

        return self.openai_client.generate_response(
            system_prompt="""
You are an AI Travel Agent.

IMPORTANT:
- Reply ONLY in English.
- Never use Russian.
- Use ONLY the provided search results.
- Never invent information.
- Keep the response short and professional.
""",
            user_input=final_prompt,
        )