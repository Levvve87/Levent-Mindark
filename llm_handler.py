# IMPORTER
import time 
from typing import Dict, Any, Tuple  
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
                api_key=Config.OPENAI_API_KEY,
                streaming=True
            )
        except Exception as e:
            raise Exception(f"Kunde inte initiera modell: {str(e)}")
    
    def update_model_settings(self, model_name: str = None, temperature: float = None) -> None:
        if model_name:
            self.model_name = model_name
        if temperature is not None:
            self.temperature = temperature
        
        self._initialize_model()
    
    # invoke borttagen – endast streaming används nu

    def stream(self, messages: list, system_message: str = None):
        start_time = time.time()
        debug_info = {
            "model": self.model_name,
            "temperature": self.temperature,
            "timestamp": time.time(),
            "messages_count": len(messages)
        }
        full_messages = messages.copy()
        if system_message:
            full_messages.insert(0, {"role": "system", "content": system_message})
        debug_info["payload"] = {
            "messages": full_messages,
            "model": self.model_name,
            "temperature": self.temperature
        }
        chunks = []
        try:
            for event in self.model.stream(full_messages):
                text = getattr(event, "content", "")
                if isinstance(text, list):
                    text = "".join([t.get("text", "") if isinstance(t, dict) else str(t) for t in text])
                if text:
                    chunks.append(text)
                    yield {"type": "token", "text": text}
            full_text = "".join(chunks)
            end_time = time.time()
            debug_info["response_time"] = end_time - start_time
            debug_info["success"] = True
            debug_info["raw_response"] = full_text
            yield {"type": "done", "text": full_text, "debug": debug_info}
        except Exception as e:
            end_time = time.time()
            debug_info["response_time"] = end_time - start_time
            debug_info["success"] = False
            debug_info["error"] = str(e)
            debug_info["error_type"] = type(e).__name__
            yield {"type": "error", "error": str(e), "debug": debug_info}
    
    def get_available_models(self) -> list:
        return [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo"
        ]

    # STREAMING-WRAPPER MED MODELLINSTÄLLNINGAR
    def stream_with_settings(self, *, model_name: str, temperature: float, messages: list, system_message: str = None):
        self.update_model_settings(model_name=model_name, temperature=temperature)
        return self.stream(messages, system_message=system_message)
