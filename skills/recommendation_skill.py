from api.openai_api import OpenAIClient
from providers.service_provider import ServiceProvider
from prompts import RECOMMENDATION_PROMPT
import json


class RecommendationSkill:
    """
    Suggests travel destinations based on the user's budget,
    trip duration, and departure city.
    """

    REQUIRED_FIELDS = [
        "budget",
        "departure_city",
        "departure_date",
        "return_date",
    ]

    def __init__(self):
        self.openai_client = ServiceProvider.openai()

    def execute(self, intent_data: dict) -> dict:

        missing = self._get_missing_fields(intent_data)

        if missing:
            return missing

        user_input = json.dumps(
            {
                "departure_city": intent_data["departure_city"],
                "budget": intent_data["budget"],
                "currency": intent_data.get("currency", "USD"),
                "departure_date": intent_data["departure_date"],
                "return_date": intent_data["return_date"],
            },
            indent=2,
        )

        response = self.openai_client.generate_response(
            system_prompt=RECOMMENDATION_PROMPT,
            user_input=user_input,
            as_json=True,
        )

        return {
            "recommended_destinations": response.get(
                "recommended_destinations",
                []
            )
        }

    # ----------------------------------------------------
    # Validation
    # ----------------------------------------------------

    def _get_missing_fields(self, intent_data: dict):

        return {
            field: None
            for field in self.REQUIRED_FIELDS
            if not intent_data.get(field)
        }