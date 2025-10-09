"""
LLM-hanteringsmodul
Översikt:
- Initierar och uppdaterar LLM-klienten (modell/temperatur)
- Tar emot meddelandelista och anropar modellen
- Returnerar svar samt debug-info (modell, tider, token, payload, rå-output)
"""

import time
from typing import Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from config import Config

class LLMHandler:
    """Publikt API för LLM-anrop och modellinställningar"""
    
    def __init__(self, model_name: str = None, temperature: float = None):
        """
        Initierar LLM-hanteraren
        
        Args:
            model_name: Namn på modell att använda
            temperature: Temperatur för modellen
        """
        self.model_name = model_name or Config.DEFAULT_MODEL
        self.temperature = temperature or Config.DEFAULT_TEMPERATURE
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initierar/återinitierar ChatOpenAI-klienten utifrån aktuella inställningar"""
        try:
            self.model = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=Config.OPENAI_API_KEY
            )
        except Exception as e:
            raise Exception(f"Kunde inte initiera modell: {str(e)}")
    
    def update_model_settings(self, model_name: str = None, temperature: float = None) -> None:
        """
        Uppdaterar modellinställningar
        
        Args:
            model_name: Nytt modellnamn
            temperature: Ny temperatur
        """
        if model_name:
            self.model_name = model_name
        if temperature is not None:
            self.temperature = temperature
        
        self._initialize_model()
    
    def invoke(self, messages: list, system_message: str = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Skickar meddelanden till LLM och returnerar svar
        
        Args:
            messages: Lista med meddelanden
            system_message: Systemmeddelande (läggs till först om angivet)
            
        Returns:
            Tuple med (response, debug_info)
        """
        start_time = time.time()
        debug_info = {
            "model": self.model_name,
            "temperature": self.temperature,
            "timestamp": time.time(),
            "messages_count": len(messages)
        }
        
        try:
            # Förbered meddelanden
            full_messages = messages.copy()
            if system_message:
                full_messages.insert(0, {"role": "system", "content": system_message})
            
            # Logga payload för debug
            debug_info["payload"] = {
                "messages": full_messages,
                "model": self.model_name,
                "temperature": self.temperature
            }
            
            # Skicka till API
            response = self.model.invoke(full_messages)
            
            # Beräkna tider
            end_time = time.time()
            debug_info["response_time"] = end_time - start_time
            debug_info["success"] = True
            
            # Lägg till token-statistik om tillgänglig
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                debug_info["token_usage"] = {
                    "prompt_tokens": metadata.get("token_usage", {}).get("prompt_tokens", "N/A"),
                    "completion_tokens": metadata.get("token_usage", {}).get("completion_tokens", "N/A"),
                    "total_tokens": metadata.get("token_usage", {}).get("total_tokens", "N/A")
                }
            
            # Lägg till rå output
            debug_info["raw_response"] = str(response)
            
            return response, debug_info
            
        except Exception as e:
            end_time = time.time()
            debug_info["response_time"] = end_time - start_time
            debug_info["success"] = False
            debug_info["error"] = str(e)
            debug_info["error_type"] = type(e).__name__
            
            raise Exception(f"LLM-anrop misslyckades: {str(e)}")
    
    def get_available_models(self) -> list:
        """
        Returnerar lista med tillgängliga modeller
        
        Returns:
            Lista med modellnamn
        """
        return [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo"
        ]
