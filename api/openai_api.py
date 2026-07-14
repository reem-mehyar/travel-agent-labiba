"""
OpenAI client responsible for all communication with the OpenAI API.
"""

from openai import OpenAI, OpenAIError

from config import OPENAI_API_KEY, OPENAI_MODEL


class OpenAIClient:
    """
    Handles all communication with the OpenAI API.
    """

    def __init__(self) -> None:
        """
        Initialize the OpenAI client.
        """
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    def generate_response(
        self,
        system_prompt: str,
        user_input: str,
        response_format: dict | None = None,
    ) -> str:
        """
        Send a request to the OpenAI Responses API and return the model output.

        Args:
            system_prompt:
                Instructions that define the model's behavior.

            user_input:
                The user's message.

            response_format:
                Optional structured output schema.

        Returns:
            Plain text response from the model.

        Raises:
            RuntimeError:
                If the OpenAI request fails.
        """

        request = {
            "model": self.model,
            "instructions": system_prompt,
            "input": user_input,
        }

        if response_format is not None:
            request["text"] = {
                "format": response_format
            }

        try:
            response = self.client.responses.create(**request)

        except OpenAIError as error:
            raise RuntimeError(
                f"OpenAI API request failed: {error}"
            ) from error

        return response.output_text