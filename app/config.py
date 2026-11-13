import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        self.groq_vision_model = os.getenv("GROQ_VISION_MODEL")
        self.openrouter_vision_model = os.getenv(
            "OPENROUTER_VISION_MODEL"
        )

        self.groq_nutrition_model = os.getenv(
            "GROQ_NUTRITION_MODEL"
        )