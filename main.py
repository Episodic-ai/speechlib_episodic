from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import shutil
from speechlib import Transcriptor
import torch
import requests

# Check GPU availability
if not torch.cuda.is_available():
    print("GPU not available. Ensure the instance has GPU support and the correct CUDA libraries are installed.")
else:
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")

app = FastAPI()

load_dotenv()

# Set your configurations
LANGUAGE = "en"
LOG_FOLDER = "logs"
MODEL_SIZE = "large"
QUANTIZATION = False
VOICES_FOLDER = "voices/"

# Retrieve sensitive keys from environment variables
ACCESS_TOKEN = os.getenv("HF_ACCESS_TOKEN")
AAI_API_KEY = os.getenv("AAI_API_KEY")

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Endpoint to transcribe an audio file using the Transcriptor class.
    Accepts a WAV file and returns the transcription as text.
    """
    
    '''
    url = "https://firebasestorage.googleapis.com:443/v0/b/psychic-cascade-427812-e6.firebasestorage.app/o/audio%2F48266D10-64E4-4172-9C70-ABC1F6A1DE47.wav?alt=media&token=3eb2ddc9-acc0-4826-a8b8-87f0b98f2bfd"
    
    if "https://firebasestorage.googleapis.com" not in url:
        raise ValueError("Invalid Firebase Storage URL")
    
    # download the wav file from the firebase storage url
    response = requests.get(url, stream=True)
    with open("firebase.wav", "wb") as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response
    '''
    
    # Validate the file type
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .wav file.")

    # Save the uploaded file temporarily
    file_path = f"temp/{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as temp_file:
        shutil.copyfileobj(file.file, temp_file)

    try:
        # Initialize the Transcriptor
        transcriptor = Transcriptor(file_path, LOG_FOLDER, LANGUAGE, MODEL_SIZE, ACCESS_TOKEN, VOICES_FOLDER, QUANTIZATION)

        # Run the diarized transcriptor
        result = transcriptor.assemby_ai_model(AAI_API_KEY)

        # Dynamically find the correct log file in the logs folder
        base_filename = os.path.splitext(file.filename)[0]  # e.g., 'compressed'
        matching_files = [
            f for f in os.listdir(LOG_FOLDER)
            if f.startswith(base_filename) and f.endswith("_en.txt")
        ]

        if not matching_files:
            raise HTTPException(status_code=500, detail="Transcription log file not found.")

        # Assuming the latest log file is the one we need
        log_file_path = os.path.join(LOG_FOLDER, matching_files[-1])  # Pick the most recent file
        print(f"Using log file: {log_file_path}")

        # Read the transcription from the log file
        with open(log_file_path, "r") as log_file:
            transcription = log_file.read()

        # Clean up temporary files
        os.remove(file_path)

        return JSONResponse(content={"transcription": transcription}, status_code=200)

    except Exception as e:
        # Clean up temporary files in case of error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))