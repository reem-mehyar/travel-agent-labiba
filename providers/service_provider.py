from api.openai_api import OpenAIClient
from skills.hotel_skill import HotelSkill
from skills.flight_skill import FlightSkill
from skills.weather_skill import WeatherSkill
from skills.currency_skill import CurrencySkill


class ServiceProvider:

    @staticmethod
    def openai():
        return OpenAIClient()

    @staticmethod
    def hotel_skill():
        return HotelSkill()

    @staticmethod
    def flight_skill():
        return FlightSkill()

    @staticmethod
    def weather_skill():
        return WeatherSkill()

    @staticmethod
    def currency_skill():
        return CurrencySkill()
    