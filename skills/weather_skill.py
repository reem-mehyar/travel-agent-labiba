from api.weather_api import get_weather_forecast
from skills.date_validation import validate_dates


class WeatherSkill:

    REQUIRED_FIELDS = ["location", "start_date", "end_date"]

    def execute(self, intent_data: dict) -> dict:

        location = (
            intent_data.get("location")
            or intent_data.get("destination_city")
        )

        start_date = intent_data.get("start_date")
        end_date = intent_data.get("end_date")

        missing = {}

        if not location:
            missing["location"] = None

        if not start_date:
            missing["start_date"] = None

        if not end_date:
            missing["end_date"] = None

        if missing:
            return missing

        validation_error = validate_dates(start_date, end_date)
        if validation_error:
            return {
                "weather": [],
                "note": validation_error,
            }

        try:
            weather = get_weather_forecast(
                city_name=location,
                start_date=start_date,
                end_date=end_date,
            )

        except Exception:
            return {
                "weather": [],
                "note": f"Unable to retrieve weather information for '{location}'."
            }

        return {
            "weather": weather
        }