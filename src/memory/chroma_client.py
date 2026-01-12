import chromadb
import datetime

class BeatriceMemory:
    def __init__(self, host="localhost", port=8000):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection(name="beatrice_memories")

    def store_memory(self, speaker: str, text: str):
        """Stores a conversation snippet in memory."""
        timestamp = datetime.datetime.now().isoformat()
        self.collection.add(
            documents=[text],
            metadatas=[{"speaker": speaker, "timestamp": timestamp}],
            ids=[f"mem_{timestamp}"]
        )

    def retrieve_memories(self, query: str, n_results: int = 5):
        """Retrieves relevant memories based on a query."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results["documents"][0] if results["documents"] else []

# Example Usage
if __name__ == "__main__":
    memory = BeatriceMemory()
    # memory.store_memory("User", "I like tea, I suppose.")
    # print(memory.retrieve_memories("What does the user like?"))
