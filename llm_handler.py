# IMPORTER
import time 
from typing import Dict, Any, Optional, Tuple  
from langchain_openai import ChatOpenAI  
from config import Config

# LLMHANDLER - OPENAI-INTEGRATION
class LLMHandler:
    
    def __init__(self, model_name: str = None, temperature: float = None):
        self.model_name = model_name or Config.DEFAULT_MODEL
        self.temperature = temperature or Config.DEFAULT_TEMPERATURE
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        try:
            self.model = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=Config.OPENAI_API_KEY
            )
        except Exception as e:
            raise Exception(f"Kunde inte initiera modell: {str(e)}")
    
    def update_model_settings(self, model_name: str = None, temperature: float = None) -> None:
        if model_name:
            self.model_name = model_name
        if temperature is not None:
            self.temperature = temperature
        
        self._initialize_model()
    
    def invoke(self, messages: list, system_message: str = None) -> Tuple[Any, Dict[str, Any]]:
        start_time = time.time()
        debug_info = {
            "model": self.model_name,
            "temperature": self.temperature,
            "timestamp": time.time(),
            "messages_count": len(messages)
        }
        
        try:
            full_messages = messages.copy()
            if system_message:
                full_messages.insert(0, {"role": "system", "content": system_message})
            
            debug_info["payload"] = {
                "messages": full_messages,
                "model": self.model_name,
                "temperature": self.temperature
            }
            
            response = self.model.invoke(full_messages)
            
            end_time = time.time()
            debug_info["response_time"] = end_time - start_time
            debug_info["success"] = True
            
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                debug_info["token_usage"] = {
                    "prompt_tokens": metadata.get("token_usage", {}).get("prompt_tokens", "N/A"),
                    "completion_tokens": metadata.get("token_usage", {}).get("completion_tokens", "N/A"),
                    "total_tokens": metadata.get("token_usage", {}).get("total_tokens", "N/A")
                }
            
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
        return [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo"
        ]
