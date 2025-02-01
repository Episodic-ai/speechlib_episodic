"""
from speechbrain.pretrained import SpeakerRecognition
import os
from pydub import AudioSegment
from collections import defaultdict
import torch

if torch.cuda.is_available():
    verification = SpeakerRecognition.from_hparams(run_opts={"device":"cuda"}, source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained_models/spkrec-ecapa-voxceleb")
    print(f"Using CUDA for Speaker Recognition")
else:
    verification = SpeakerRecognition.from_hparams(run_opts={"device":"cpu"}, source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained_models/spkrec-ecapa-voxceleb")
    print(f"Using CPU for Speaker Recognition")

# recognize speaker name
def speaker_recognition(file_name, voices_folder, segments, wildcards):
    
    if torch.cuda.is_available():
        print(f"Using CUDA for Speaker Recognition")
    else:
        print(f"Using CPU for Speaker Recognition")

    speakers = os.listdir(voices_folder)

    Id_count = defaultdict(int)
    # Load the WAV file
    audio = AudioSegment.from_file(file_name, format="wav")

    folder_name = "temp"

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    i = 0
    
    '''
    iterate over segments and check speaker for increased accuracy.
    assign speaker name to arbitrary speaker tag 'SPEAKER_XX'
    '''

    limit = 60
    duration = 0

    for segment in segments:
        start = segment[0] * 1000   # start time in miliseconds
        end = segment[1] * 1000     # end time in miliseconds
        clip = audio[start:end]
        i = i + 1
        file = folder_name + "/" + file_name.split("/")[-1].split(".")[0] + "_segment"+ str(i) + ".wav"
        clip.export(file, format="wav")

        max_score = 0
        person = "unknown"      # if no match to any voice, then return unknown

        for speaker in speakers:

            #voices = os.listdir(voices_folder + "/" + speaker)
            speaker_path = os.path.join(voices_folder, speaker)

            # Ensure we only get files, avoiding directories
            voices = [
                v for v in os.listdir(speaker_path) 
                if os.path.isfile(os.path.join(speaker_path, v))
            ]

            for voice in voices:
                voice_file = voices_folder + "/" + speaker + "/" + voice

                try:
                    # compare voice file with audio file
                    score, prediction = verification.verify_files(voice_file, file)
                    prediction = prediction[0].item()
                    score = score[0].item()

                    if prediction == True:
                        if score >= max_score:
                            max_score = score
                            speakerId = speaker.split(".")[0]  
                            if speakerId not in wildcards:        # speaker_00 cannot be speaker_01
                                person = speakerId
                except Exception as err:
                    print("error occured while speaker recognition: ", err)

        Id_count[person] += 1

        # Delete the WAV file after processing
        os.remove(file)

        current_pred = max(Id_count, key=Id_count.get)

        duration += (end - start)
        if duration >= limit and current_pred != "unknown":
            break
    
    most_common_Id = max(Id_count, key=Id_count.get)
    return most_common_Id
"""

from speechbrain.pretrained import SpeakerRecognition
import os
from pydub import AudioSegment
from collections import defaultdict
import torch
import io
import torchaudio

# Initialize Speaker Recognition model
if torch.cuda.is_available():
    verification = SpeakerRecognition.from_hparams(run_opts={"device": "cuda"}, source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained_models/spkrec-ecapa-voxceleb")
    print("Using CUDA for Speaker Recognition")
else:
    verification = SpeakerRecognition.from_hparams(run_opts={"device": "cpu"}, source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained_models/spkrec-ecapa-voxceleb")
    print("Using CPU for Speaker Recognition")

# Cache speaker voice files to avoid repeated disk access
def cache_speaker_voices(voices_folder):
    speakers = {}
    for speaker in os.listdir(voices_folder):
        speaker_path = os.path.join(voices_folder, speaker)
        if os.path.isdir(speaker_path):
            speakers[speaker] = [os.path.join(speaker_path, v) for v in os.listdir(speaker_path) if os.path.isfile(os.path.join(speaker_path, v))]
    return speakers

# Recognize speaker name
def speaker_recognition(file_name, voices_folder, segments, wildcards):
    
    # Cache speaker voice files to avoid scanning directories multiple times
    speakers = cache_speaker_voices(voices_folder)
    Id_count = defaultdict(int)
    
    # Load the WAV file
    audio = AudioSegment.from_file(file_name, format="wav")
    
    limit = 60  # Limit the total duration processed
    duration = 0
    i = 0

    for segment in segments:
        start = segment[0] * 1000  # Convert start time to milliseconds
        end = segment[1] * 1000    # Convert end time to milliseconds
        clip = audio[start:end]
        i += 1
        
        # Use in-memory buffer instead of writing to disk
        buffer = io.BytesIO()
        clip.export(buffer, format="wav")
        buffer.seek(0)

        # Convert in-memory buffer to waveform tensor
        waveform, sample_rate = torchaudio.load(buffer)

        max_score = 0
        person = "unknown"  # Default to unknown if no match is found

        for speaker, voice_files in speakers.items():
            for voice_file in voice_files:
                try:
                    # Convert voice file to waveform tensor
                    voice_waveform, voice_sample_rate = torchaudio.load(voice_file)

                    # Ensure both sample rates match
                    if sample_rate != voice_sample_rate:
                        transform = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=voice_sample_rate)
                        waveform = transform(waveform)

                    # Pass waveforms directly to verify_batch()
                    score, prediction = verification.verify_batch(voice_waveform, waveform)
                    prediction = prediction[0].item()
                    score = score[0].item()

                    if prediction and score >= max_score:
                        max_score = score
                        speakerId = speaker.split(".")[0]
                        if speakerId not in wildcards:  # Ensure unique speaker tag
                            person = speakerId
                except Exception as err:
                    print("Error occurred while speaker recognition:", err)

        Id_count[person] += 1

        current_pred = max(Id_count, key=Id_count.get)
        duration += (end - start)
        if duration >= limit and current_pred != "unknown":
            break
    
    most_common_Id = max(Id_count, key=Id_count.get)
    return most_common_Id