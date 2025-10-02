"""
Minneshanteringsmodul för AI-chattapplikationen
Hanterar konversationshistorik och meddelanden
"""

import json
from datetime import datetime
from typing import List, Dict, Any

class MemoryManager:
    """Hanterar konversationsminne och meddelanden"""
    
    def __init__(self):
        """Initierar minneshanteraren"""
        self.messages: List[Dict[str, Any]] = []
        self.debug_info: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str, timestamp: str = None) -> None:
        """
        Lägger till ett meddelande i konversationshistoriken
        
        Args:
            role: Meddelandets roll (user, assistant, system)
            content: Meddelandets innehåll
            timestamp: Tidsstämpel (genereras automatiskt om None)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        self.messages.append(message)
    
    def add_debug_info(self, info: Dict[str, Any]) -> None:
        """
        Lägger till debug-information
        
        Args:
            info: Dictionary med debug-information
        """
        info["timestamp"] = datetime.now().isoformat()
        self.debug_info.append(info)
        
        # Begränsa antal debug-entries för prestanda
        if len(self.debug_info) > 50:
            self.debug_info.pop(0)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Hämtar konversationshistorik i format som LangChain förväntar sig
        
        Returns:
            Lista med meddelanden i LangChain-format
        """
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def clear_messages(self) -> None:
        """Rensar alla meddelanden"""
        self.messages.clear()
    
    def clear_debug_info(self) -> None:
        """Rensar all debug-information"""
        self.debug_info.clear()
    
    def export_messages(self, format: str = "json") -> str:
        """
        Exporterar meddelanden i önskat format
        
        Args:
            format: Exportformat ("json" eller "txt")
            
        Returns:
            Exporterad data som sträng
        """
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
        """
        Hämtar senaste debug-informationen
        
        Args:
            limit: Maximalt antal entries att returnera
            
        Returns:
            Lista med senaste debug-informationen
        """
        return self.debug_info[-limit:] if self.debug_info else []
