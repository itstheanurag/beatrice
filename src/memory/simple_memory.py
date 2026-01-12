"""
Simple JSON-based persistent memory for Beatrice.
No external dependencies required - uses just the standard library.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memories.json")


class SimpleMemory:
    """Lightweight JSON-based memory that persists across restarts."""
    
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.memories: List[Dict] = self._load()
    
    def _load(self) -> List[Dict]:
        """Load memories from file."""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save(self):
        """Save memories to file."""
        try:
            with open(MEMORY_FILE, 'w') as f:
                json.dump(self.memories, f, indent=2)
        except IOError:
            pass
    
    def store(self, speaker: str, text: str):
        """Store a conversation snippet."""
        self.memories.append({
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 100 memories to prevent file bloat
        if len(self.memories) > 100:
            self.memories = self.memories[-100:]
        self._save()
    
    def get_recent(self, n: int = 10) -> List[Dict]:
        """Get the n most recent memories."""
        return self.memories[-n:]
    
    def search(self, query: str, n: int = 5) -> List[str]:
        """Simple keyword search through memories."""
        query_lower = query.lower()
        matches = []
        
        for mem in reversed(self.memories):
            text = mem.get("text", "")
            if any(word in text.lower() for word in query_lower.split()):
                matches.append(f"{mem['speaker']}: {text}")
                if len(matches) >= n:
                    break
        
        return matches
    
    def get_user_facts(self) -> List[str]:
        """Extract key facts the user has shared (name, preferences, etc.)."""
        facts = []
        keywords = ["my name is", "i am ", "i'm ", "call me", "i like", "i love", "i hate"]
        
        for mem in self.memories:
            if mem.get("speaker") == "User":
                text_lower = mem["text"].lower()
                for keyword in keywords:
                    if keyword in text_lower:
                        facts.append(mem["text"])
                        break
        
        return facts[-5:]  # Return last 5 facts
    
    def clear(self):
        """Clear all memories."""
        self.memories = []
        self._save()
