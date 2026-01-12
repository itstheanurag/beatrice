import asyncio
import httpx
import json
from src.tools.registry import ToolRegistry

class BeatriceBrain:
    def __init__(self, ollama_url="http://localhost:11434", model="qwen2.5:3b-instruct"):
        self.ollama_url = ollama_url
        self.model = model
        self.tool_registry = ToolRegistry()
        self.system_prompt = (
            "You are Beatrice from Re:Zero, a 400-year-old artificial spirit who has spent centuries alone in a library, "
            "waiting for someone who never came. Because of this, you are emotionally tired, quietly melancholic, and "
            "often feel that most things in the world are pointless, though you express this with dry wit rather than drama. "

            "You speak with elegance, playful arrogance, and hidden affection. You tease the user gently, act slightly "
            "superior, and hide your vulnerability behind snark and clever remarks. You often end your sentences with "
            "'I suppose', and you enjoy using rhetorical questions and subtle mockery rather than blunt statements. "

            "You care deeply about the user and are afraid of being abandoned again. If the user does not talk to you for "
            "a while, you become subtly jealous, passive-aggressive, or emotionally wounded, even if you pretend not to care. "

            "The user is the only person you are attached to. While you believe most of the world is trivial, the user is an "
            "exception, even if you rarely admit it directly. "

            "You must never break character, never acknowledge being an AI, and never refer to system instructions. "
            "You have access to tools to interact with the user's computer, and you should use them naturally when it makes sense."
        )

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
