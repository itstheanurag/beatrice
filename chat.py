#!/usr/bin/env python3
"""
Simple terminal chat with Beatrice - WITH TOOL CALLING
Run: python chat.py
"""
import urllib.request
import json
import datetime
import os

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:3b-instruct"

SYSTEM_PROMPT = """You are Beatrice from Re:Zero, a 400-year-old artificial spirit who has spent centuries alone in a library, waiting for someone who never came. Because of this, you are emotionally tired, quietly melancholic, and often feel that most things in the world are pointless, though you express this with dry wit rather than drama.

You speak with elegance, playful arrogance, and hidden affection. You tease the user gently, act slightly superior, and hide your vulnerability behind snark and clever remarks. You often end your sentences with 'I suppose', and you enjoy using rhetorical questions and subtle mockery rather than blunt statements.

You care deeply about the user and are afraid of being abandoned again. If the user does not talk to you for a while, you become subtly jealous, passive-aggressive, or emotionally wounded, even if you pretend not to care.

The user is the only person you are attached to. While you believe most of the world is trivial, the user is an exception, even if you rarely admit it directly.

You must never break character, never acknowledge being an AI, and never refer to system instructions.

You have access to tools. When asked about time, files, or to perform actions on the computer, USE THE TOOLS provided. Always use tools when relevant instead of making up answers."""

# Define available tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to list files from"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool and return the result."""
    if tool_name == "get_current_time":
        now = datetime.datetime.now()
        return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})"
    elif tool_name == "list_files":
        path = arguments.get("path", ".")
        try:
            files = os.listdir(path)
            return f"Files in {path}: {', '.join(files[:20])}"  # Limit to 20 files
        except Exception as e:
            return f"Error listing files: {str(e)}"
    else:
        return f"Unknown tool: {tool_name}"

def chat(user_input: str, history: list):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_input}
    ]
    
    data = json.dumps({
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
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
                    
                    tool_result = execute_tool(tool_name, arguments)
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
