from api.visa_api import VisaAPI
import pycountry


class VisaSkill:
    """
    Handles visa requirement business logic.
    """

    REQUIRED_FIELDS = [
        "passport_country",
        "destination_country",
    ]

    def __init__(self):
        self.visa_api = VisaAPI()

    def execute(self, intent_data: dict) -> dict:

        missing = self._get_missing_fields(intent_data)

        if missing:
            return missing

        try:
            passport_code = self._country_to_code(
                intent_data["passport_country"]
            )

            destination_code = self._country_to_code(
                intent_data["destination_country"]
            )

            if passport_code is None:
                return {
                    "visa": None,
                    "error": (f"Could not resolve passport country." f"'{intent_data['passport_country']}'.")
                }

            if destination_code is None:
                return {
                    "visa": None,
                    "error": (f"Could not resolve destination country." f"'{intent_data['destination_country']}'.")
                }

            raw_response = self.visa_api.get_visa_requirements(
                passport_code=passport_code,
                destination_code=destination_code,
            )

            return {
                "visa": self._clean_visa_data(raw_response)
            }

        except Exception as e:
            return {
                "visa": None,
                "error": str(e),
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

    # ----------------------------------------------------
    # Country Conversion
    # ----------------------------------------------------

    def _country_to_code(self, country_name: str):

        try:
            country = pycountry.countries.lookup(country_name)
            return country.alpha_2
        except LookupError:
            return None

    # ----------------------------------------------------
    # Parsing
    # ----------------------------------------------------

    def _clean_visa_data(self, response: dict):

        data = response.get("data", {})

        passport = data.get("passport", {})
        destination = data.get("destination", {})
        mandatory_registration = data.get(
            "mandatory_registration", {}
        )

        visa_rules = data.get("visa_rules", {})
        primary_rule = visa_rules.get(
            "primary_rule", {}
        )

        embassy_url = destination.get("embassy_url")

        if embassy_url and "#titlePlaceholder" in embassy_url:
            embassy_url = embassy_url.split("#")[0]

        return {
            "passport_country": passport.get("name"),
            "destination_country": destination.get("name"),
            "visa_required": primary_rule.get("name"),
            "visa_status": primary_rule.get("color"),
            "passport_validity": destination.get("passport_validity"),
            "mandatory_registration": mandatory_registration.get("name"),
            "mandatory_registration_link": mandatory_registration.get("link"),
            "capital": destination.get("capital"),
            "currency": destination.get("currency"),
            "currency_code": destination.get("currency_code"),
            "exchange_rate": destination.get("exchange"),
            "phone_code": destination.get("phone_code"),
            "timezone": destination.get("timezone"),
            "population": destination.get("population"),
            "area_km2": destination.get("area_km2"),
            "embassy_directory_url": embassy_url,
        }