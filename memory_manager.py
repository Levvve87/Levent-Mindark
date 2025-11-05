# IMPORTER
from datetime import datetime
from typing import List, Dict, Any

# MEMORYMANAGER - DEBUG & FEEDBACK (BACKUP)
class MemoryManager:
    
    def __init__(self):
        self.debug_info: List[Dict[str, Any]] = []
        self.feedback_log: List[Dict[str, Any]] = []
    
    def add_debug_info(self, info: Dict[str, Any]) -> None:
        info["timestamp"] = datetime.now().isoformat()
        self.debug_info.append(info)
        
        if len(self.debug_info) > 50:
            self.debug_info.pop(0)
    
    def clear_debug_info(self) -> None:
        self.debug_info.clear()
    
    def get_latest_debug_info(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.debug_info[-limit:] if self.debug_info else []

    def add_feedback(self, message_index: int, rating: str, reason: str = "", message_content: str = "") -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message_index": message_index,
            "rating": rating,
            "reason": reason,
            "message_content": message_content,
        }
        self.feedback_log.append(entry)
        if len(self.feedback_log) > 200:
            self.feedback_log.pop(0)
