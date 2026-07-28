import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
<<<<<<< Updated upstream
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY")
=======
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
>>>>>>> Stashed changes

OPENAI_MODEL = "gpt-4.1-mini"