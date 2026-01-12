import os
import subprocess
from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn
import uuid

app = FastAPI()

# Path to piper executable and model
PIPER_EXE = "/usr/bin/piper"
PIPER_MODEL = os.getenv("PIPER_MODEL", "/app/data/models/en_US-lessac-medium.onnx")
OUTPUT_DIR = "/app/data/outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/say")
async def say(text: str):
    filename = f"{uuid.uuid4()}.wav"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Execute piper command
    # echo "text" | piper --model model.onnx --output_file file.wav
    command = f'echo "{text}" | {PIPER_EXE} --model {PIPER_MODEL} --output_file {filepath}'
    
    try:
        subprocess.run(command, shell=True, check=True)
        return FileResponse(filepath, media_type="audio/wav")
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
