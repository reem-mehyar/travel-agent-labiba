"""
OpenAI client responsible for all communication with the OpenAI API.
"""

import json

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
        as_json: bool = False,
    ) -> str | dict:
        """
        Generate a response from the OpenAI model.

        Args:
            system_prompt:
                Instructions that define the model's behavior.

            user_input:
                The user's message.

            as_json:
                If True, the model response is parsed into a Python
                dictionary.

        Returns:
            The model response as a string or dictionary.

        Raises:
            RuntimeError:
                If the OpenAI request fails or an invalid JSON response
                is returned.
        """

        request = {
    "model": self.model,
    "instructions": system_prompt,
    "input": user_input,
    "text": {
        "format": {
            "type": "text"
        }
    }
}
      
        try:
            response = self.client.responses.create(**request)

        except OpenAIError as error:
            raise RuntimeError(
                f"OpenAI API request failed: {error}"
            ) from error

        output = response.output_text.strip()

        if not as_json:
            return output

        try:
            return json.loads(output)

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "OpenAI returned an invalid JSON response."
            ) from error