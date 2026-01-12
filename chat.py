#!/usr/bin/env python3
"""
Simple terminal chat with Beatrice - WITH TOOL CALLING
Run: python chat.py
"""
import urllib.request
import json
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.brain.prompts import SYSTEM_PROMPT
from src.tools.registry import ToolRegistry

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:3b-instruct"

# Initialize shared tool registry
tool_registry = ToolRegistry()


def chat(user_input: str, history: list):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_input}
    ]
    
    data = json.dumps({
        "model": MODEL,
        "messages": messages,
        "tools": tool_registry.get_ollama_tools(),
        "stream": False
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            message = result["message"]
            
            # Check if there are tool calls
            if "tool_calls" in message and message["tool_calls"]:
                tool_results = []
                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    arguments = tool_call["function"].get("arguments", {})
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)
                    
                    # Use shared tool registry
                    tool_result = tool_registry.call_tool(tool_name, **arguments)
                    tool_results.append(f"[Tool: {tool_name}] {tool_result}")
                
                # Send tool results back to get final response
                messages.append(message)
                messages.append({
                    "role": "tool",
                    "content": "\n".join(tool_results)
                })
                
                data = json.dumps({
                    "model": MODEL,
                    "messages": messages,
                    "stream": False
                }).encode('utf-8')
                
                req = urllib.request.Request(
                    f"{OLLAMA_URL}/api/chat",
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=60) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result["message"]["content"]
            
            return message["content"]
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    print("\n" + "="*50)
    print("  Beatrice AI - Terminal Chat (with Tools!)")
    print("  Type 'quit' to exit")
    print("="*50 + "\n")
    
    history = []
    
    while True:
        try:
            user_input = input("\033[94mYou:\033[0m ")
        except (KeyboardInterrupt, EOFError):
            print("\n\n\033[95mBeatrice:\033[0m Leaving so soon? How typical, I suppose...")
            break
            
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\n\033[95mBeatrice:\033[0m Fine, leave then. Not that I care, I suppose...")
            break
        
        if not user_input.strip():
            continue
        
        print("\033[95mBeatrice:\033[0m ", end="", flush=True)
        response = chat(user_input, history)
        print(response)
        print()
        
        # Update history
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        
        # Keep only last 10 exchanges to avoid context overflow
        if len(history) > 20:
            history = history[-20:]


if __name__ == "__main__":
    main()
