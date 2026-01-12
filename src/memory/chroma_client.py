"""
ChromaDB HTTP Client - connects to ChromaDB without needing the chromadb package.
Uses the v2 REST API directly.
"""
import urllib.request
import urllib.error
import json
import datetime
import uuid
from typing import List, Dict, Optional


class ChromaHttpMemory:
    """
    Connects to ChromaDB via HTTP REST API.
    No chromadb Python package required!
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.base_url = f"http://{host}:{port}/api/v2"
        self.tenant = "default_tenant"
        self.database = "default_database"
        self.collection_name = "beatrice_memories"
        self.collection_id = None
        self._ensure_collection()
    
    def _request(self, method: str, path: str, data: dict = None) -> dict:
        """Make HTTP request to ChromaDB."""
        url = f"{self.base_url}{path}"
        
        if data is not None:
            body = json.dumps(data).encode('utf-8')
        else:
            body = None
        
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header('Content-Type', 'application/json')
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
                return {}
        except urllib.error.HTTPError as e:
            if e.code == 409:  # Already exists
                return json.loads(e.read().decode('utf-8'))
            raise
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        path = f"/tenants/{self.tenant}/databases/{self.database}/collections"
        
        # List collections to find ours
        collections = self._request("GET", path)
        for col in collections:
            if col.get("name") == self.collection_name:
                self.collection_id = col.get("id")
                return
        
        # Create collection
        result = self._request("POST", path, {
            "name": self.collection_name,
            "metadata": {"description": "Beatrice conversation memories"}
        })
        self.collection_id = result.get("id")
    
    def store_memory(self, speaker: str, text: str):
        """Store a conversation snippet in memory."""
        if not self.collection_id:
            return
        
        timestamp = datetime.datetime.now().isoformat()
        doc_id = f"mem_{uuid.uuid4().hex[:12]}"
        
        path = f"/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_id}/add"
        
        self._request("POST", path, {
            "ids": [doc_id],
            "documents": [f"{speaker}: {text}"],
            "metadatas": [{"speaker": speaker, "timestamp": timestamp}]
        })
    
    def retrieve_memories(self, query: str, n_results: int = 5) -> List[str]:
        """Retrieve relevant memories based on a query."""
        if not self.collection_id:
            return []
        
        path = f"/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_id}/query"
        
        result = self._request("POST", path, {
            "query_texts": [query],
            "n_results": n_results,
            "include": ["documents", "metadatas"]
        })
        
        documents = result.get("documents", [[]])
        return documents[0] if documents else []
    
    def get_user_facts(self) -> List[str]:
        """Get facts the user has shared (searches for key phrases)."""
        facts = []
        
        # Search for common self-introduction patterns
        for query in ["my name is", "I am", "I like", "I love"]:
            memories = self.retrieve_memories(query, n_results=3)
            for mem in memories:
                if mem.startswith("User:") and mem not in facts:
                    facts.append(mem.replace("User: ", ""))
        
        return facts[:5]  # Limit to 5 facts
    
    def count(self) -> int:
        """Get number of memories."""
        if not self.collection_id:
            return 0
        
        path = f"/tenants/{self.tenant}/databases/{self.database}/collections/{self.collection_id}/count"
        result = self._request("GET", path)
        return result if isinstance(result, int) else 0


# Test connection on import
if __name__ == "__main__":
    try:
        memory = ChromaHttpMemory()
        print(f"✓ Connected to ChromaDB")
        print(f"✓ Collection: {memory.collection_name}")
        print(f"✓ Memories: {memory.count()}")
        
        # Test store
        memory.store_memory("User", "My name is Test User")
        print("✓ Store works")
        
        # Test retrieve
        results = memory.retrieve_memories("name")
        print(f"✓ Retrieve works: {results}")
    except Exception as e:
        print(f"✗ Error: {e}")
