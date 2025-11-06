import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_TEMPERATURE = 0.7
    ENABLE_DANGEROUS_ACTIONS = os.getenv("ENABLE_DANGEROUS_ACTIONS", "false").lower() == "true"
