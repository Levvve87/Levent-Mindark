"""
Konfigurationsmodul
Översikt:
- Läser miljövariabler (.env) och tillgängliggör OPENAI_API_KEY
- Samlar standardinställningar (modell, temperatur, UI, debug, feltexter)
- Erbjuder enkel validering av konfiguration
"""

import os
from dotenv import load_dotenv

# Ladda miljövariabler
load_dotenv()

class Config:
    """Huvudkonfigurationsklass för applikationen"""
    
    # API-inställningar
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Modellinställningar (kan ändras i UI)
    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_TEMPERATURE = 0.7
    
    # UI-inställningar
    PAGE_TITLE = "AI-chat med debugpanel"
    PAGE_LAYOUT = "wide"
    
    # Debug-inställningar
    DEBUG_PANEL_WIDTH = 400
    MAX_DEBUG_ENTRIES = 50
    
    # Felmeddelanden
    ERROR_MESSAGES = {
        "no_api_key": "API-nyckel saknas! Kontrollera din .env-fil.",
        "api_error": "Fel vid API-anrop:",
        "network_error": "Nätverksfel: Kontrollera din internetanslutning.",
        "invalid_key": "Ogiltig API-nyckel. Kontrollera att nyckeln är korrekt."
    }
    
    @classmethod
    def validate_config(cls):
        """Validerar att all nödvändig konfiguration finns"""
        if not cls.OPENAI_API_KEY:
            return False, cls.ERROR_MESSAGES["no_api_key"]
        return True, "Konfiguration OK"
