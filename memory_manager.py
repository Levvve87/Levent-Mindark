 

import json
from datetime import datetime
from typing import List, Dict, Any

class MemoryManager:
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.debug_info: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str, timestamp: str = None) -> None:
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        self.messages.append(message)
    
    def add_debug_info(self, info: Dict[str, Any]) -> None:
        info["timestamp"] = datetime.now().isoformat()
        self.debug_info.append(info)
        
        if len(self.debug_info) > 50:
            self.debug_info.pop(0)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def clear_messages(self) -> None:
        self.messages.clear()
    
    def clear_debug_info(self) -> None:
        self.debug_info.clear()
    
    def export_messages(self, format: str = "json") -> str:
        if format == "json":
            return json.dumps(self.messages, ensure_ascii=False, indent=2)
        elif format == "txt":
            result = []
            for msg in self.messages:
                timestamp = msg.get("timestamp", "Okänt tid")
                role = msg["role"].upper()
                content = msg["content"]
                result.append(f"[{timestamp}] {role}: {content}")
            return "\n".join(result)
        else:
            raise ValueError(f"Okänt format: {format}")
    
    def get_latest_debug_info(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.debug_info[-limit:] if self.debug_info else []
