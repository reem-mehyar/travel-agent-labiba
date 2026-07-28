import requests

from config import RAPIDAPI_KEY


class VisaAPI:

    BASE_URL = "https://visa-requirement.p.rapidapi.com/v2/visa/check"

    def __init__(self):

        self.headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "visa-requirement.p.rapidapi.com",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def get_visa_requirements(
        self,
        passport_code: str,
        destination_code: str,
    ) -> dict:

        payload = {
            "passport": passport_code,
            "destination": destination_code,
        }

        response = requests.post(
            self.BASE_URL,
            headers=self.headers,
            data=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()