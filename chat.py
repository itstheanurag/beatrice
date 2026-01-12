#!/usr/bin/env python3
"""
Simple terminal chat with Beatrice - WITH STREAMING, TOOLS & PERSISTENT MEMORY
Run: python chat.py [model_name]
Examples:
  python chat.py                    # Uses default (gemma2:9b)
"""
import urllib.request
import json
import sys
import os
import time
import threading

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.brain.prompts import SYSTEM_PROMPT
from src.tools.registry import ToolRegistry
from src.memory.simple_memory import SimpleMemory

OLLAMA_URL = "http://localhost:11434"

# Model selection: CLI arg > env var > default
DEFAULT_MODEL = "qwen2.5:3b"
MODEL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BEATRICE_MODEL", DEFAULT_MODEL)

# Initialize shared components
tool_registry = ToolRegistry()
memory = SimpleMemory()

print(f"\033[92m✓ Model: {MODEL}\033[0m")
print(f"\033[92m✓ Memory: {len(memory.memories)} memories\033[0m")


class ThinkingIndicator:
    """Shows a thinking animation while waiting for response."""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def start(self, message="Thinking"):
        self.running = True
        self.thread = threading.Thread(target=self._animate, args=(message,))
        self.thread.start()
    
    def _animate(self, message):
        idx = 0
        while self.running:
            frame = self.frames[idx % len(self.frames)]
            print(f"\r\033[95m{frame} {message}...\033[0m", end="", flush=True)
            time.sleep(0.1)
            idx += 1
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        # Clear the thinking line
        print("\r" + " " * 40 + "\r", end="", flush=True)


def build_system_prompt_with_memories() -> str:
    """Enhance system prompt with user facts from memory."""
    user_facts = memory.get_user_facts()
    
    if user_facts:
        memory_context = "\n\nTHINGS YOU REMEMBER ABOUT YOUR CONTRACTOR:\n"
        for fact in user_facts:
            memory_context += f"- {fact}\n"
        memory_context += "\nUse these facts naturally. Address them by name if you know it!"
        return SYSTEM_PROMPT + memory_context
    
    return SYSTEM_PROMPT


def stream_chat(user_input: str, history: list):
    """Chat with streaming response - yields chunks as they arrive."""
    # Build prompt with memories
    enhanced_prompt = build_system_prompt_with_memories()
    
    messages = [
        {"role": "system", "content": enhanced_prompt},
        *history,
        {"role": "user", "content": user_input}
    ]
    
    # Tools disabled by default (3B model uses them incorrectly)
    # Set BEATRICE_TOOLS=1 to enable
    request_data = {
        "model": MODEL,
        "messages": messages,
        "stream": True
    }
    
    # Only add tools if explicitly enabled AND model supports them
    if os.environ.get("BEATRICE_TOOLS") == "1":
        if "qwen" in MODEL.lower() or "mistral" in MODEL.lower():
            request_data["tools"] = tool_registry.get_ollama_tools()
    
    data = json.dumps(request_data).encode('utf-8')
    
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    # First pass: collect response and check for tool calls
    # We buffer everything first to know if tools are involved
    initial_response = ""
    tool_calls = []
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            for line in response:
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    message = chunk.get("message", {})
                    
                    # Check for tool calls
                    if "tool_calls" in message and message["tool_calls"]:
                        tool_calls.extend(message["tool_calls"])
                    
                    # Buffer content (don't yield yet - we might have tool calls)
                    content = message.get("content", "")
                    if content:
                        initial_response += content
                    
                    if chunk.get("done", False):
                        break
        
        # If NO tool calls, stream the initial response
        if not tool_calls:
            yield initial_response
            return
        
        # If tool calls exist, execute them and get final response
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            arguments = tool_call["function"].get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            
            tool_result = tool_registry.call_tool(tool_name, **arguments)
            tool_results.append(f"{tool_result}")
        
        # Send tool results back to get final response
        messages.append({"role": "assistant", "content": initial_response, "tool_calls": tool_calls})
        messages.append({"role": "tool", "content": "\n".join(tool_results)})
        
        data = json.dumps({
            "model": MODEL,
            "messages": messages,
            "stream": True
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Stream the FINAL response (this is the only one user sees)
        with urllib.request.urlopen(req, timeout=120) as response:
            for line in response:
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done", False):
                        break
    
    except Exception as e:
        yield f"Error: {str(e)}"


def main():
    print("\n" + "="*50)
    print("  Beatrice AI - Terminal Chat")
    print("  Commands: 'quit', 'clear' (reset memory)")
    print("="*50 + "\n")
    
    history = []
    thinking = ThinkingIndicator()
    
    while True:
        try:
            user_input = input("\033[94mYou:\033[0m ")
        except (KeyboardInterrupt, EOFError):
            print("\n\n\033[95mBeatrice:\033[0m Leaving so soon? How typical, I suppose...")
            break
            
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\n\033[95mBeatrice:\033[0m Fine, leave then. Not that I care, I suppose...")
            break
        
        if user_input.lower() == 'clear':
            memory.clear()
            history = []
            print("\033[93m✓ Memory cleared\033[0m\n")
            continue
        
        if not user_input.strip():
            continue
        
        # Save user input to memory immediately
        memory.store("User", user_input)
        
        # Show thinking indicator
        thinking.start("Gathering thoughts")
        
        # Start streaming
        full_response = ""
        first_chunk = True
        
        for chunk in stream_chat(user_input, history):
            if first_chunk:
                thinking.stop()
                print("\033[95mBeatrice:\033[0m ", end="", flush=True)
                first_chunk = False
            
            print(chunk, end="", flush=True)
            if not chunk.startswith("\n\n\033[90m"):
                full_response += chunk
        
        print("\n")
        
        # Save response to memory
        memory.store("Beatrice", full_response)
        
        # Update session history
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": full_response})
        
        # Keep only last 10 exchanges to avoid context overflow
        if len(history) > 20:
            history = history[-20:]


if __name__ == "__main__":
    main()
