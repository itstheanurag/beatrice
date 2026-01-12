import os
import datetime
import subprocess
from typing import Dict, Any, Callable

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.register_default_tools()

    def register(self, name: str, func: Callable):
        self.tools[name] = func

    def register_default_tools(self):
        self.register("get_time", self.get_time)
        self.register("list_files", self.list_files)
        self.register("execute_shell", self.execute_shell)

    def get_time(self, **kwargs) -> str:
        """Returns the current system time."""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def list_files(self, path: str = ".") -> str:
        """Lists files in a given directory."""
        try:
            files = os.listdir(path)
            return "\n".join(files)
        except Exception as e:
            return f"Error: {str(e)}"

    def execute_shell(self, command: str) -> str:
        """Executes a shell command (USE WITH CAUTION)."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return f"Stdout: {result.stdout}\nStderr: {result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"

    def call_tool(self, name: str, **kwargs) -> str:
        if name in self.tools:
            return self.tools[name](**kwargs)
        return f"Tool {name} not found."
