import os
import io
from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import uvicorn

app = FastAPI()

# Load model (tiny for low compute)
model_size = os.getenv("WHISPER_MODEL", "tiny.en")
model = WhisperModel(model_size, device="cpu", compute_type="int8")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # Read audio file
    audio_data = await file.read()
    
    # Transcribe
    segments, info = model.transcribe(io.BytesIO(audio_data), beam_size=5)
    
    text = " ".join([segment.text for segment in segments])
    return {"text": text.strip(), "language": info.language}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
