import asyncio
import httpx
import json
from src.tools.registry import ToolRegistry
from src.brain.prompts import SYSTEM_PROMPT

class BeatriceBrain:
    def __init__(self, ollama_url="http://localhost:11434", model="qwen2.5:3b-instruct"):
        self.ollama_url = ollama_url
        self.model = model
        self.tool_registry = ToolRegistry()
        self.system_prompt = SYSTEM_PROMPT

    async def chat(self, user_input: str, history: list = None):
        if history is None:
            history = []

        messages = [
            {"role": "system", "content": self.system_prompt},
            *history,
            {"role": "user", "content": user_input}
        ]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"]
            else:
                return f"Error: {response.text}"

# Example Usage (Placeholder)
if __name__ == "__main__":
    brain = BeatriceBrain()
    # print(asyncio.run(brain.chat("Who are you?")))
