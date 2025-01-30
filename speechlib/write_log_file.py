import os
from datetime import datetime
from pydub import AudioSegment
import uuid

def write_log_file(common_segments, log_folder, file_name, language):

    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    #---------------------log file part-------------------------
        
    current_time = datetime.now().strftime('%H%M%S')
    
    og_file_name = file_name
    file_name = os.path.splitext(os.path.basename(file_name))[0]

    log_file = os.path.join(log_folder, f"{file_name}_{current_time}_{language}.txt")
    
    lf = open(log_file, "wb")

    entry = ""
    
    # Ensure the unidentified_speakers subfolder exists
    unidentified_speakers_folder = os.path.join(log_folder, "unidentified_speakers")
    os.makedirs(unidentified_speakers_folder, exist_ok=True)

    # Dictionary to store unique SPEAKER_XX → UUID mappings
    speaker_uuid_map = {}

    for segment in common_segments:
        start = segment[0]
        end = segment[1]
        text = segment[2]
        speaker = segment[3]
        
        # if speaker begins with 'SPEAKER_', assign a UUID
        if speaker.startswith("SPEAKER_"):

            # Generate a UUID if the speaker hasn't been seen before
            if speaker not in speaker_uuid_map:
                speaker_uuid_map[speaker] = str(uuid.uuid4())

            # Use the mapped UUID for this speaker
            speaker_uuid = speaker_uuid_map[speaker]

            # Ensure the folder for this UUID exists
            speaker_folder = os.path.join(unidentified_speakers_folder, speaker_uuid)
            os.makedirs(speaker_folder, exist_ok=True)
            
            # Check if the folder already has 4 files
            existing_files = [
                f for f in os.listdir(speaker_folder) if os.path.isfile(os.path.join(speaker_folder, f))
            ]
            
            if len(existing_files) < 4:  # Only add if less than 4 files exist
                # Extract the audio segment
                audio = AudioSegment.from_file(og_file_name, format="wav")
                clip = audio[start * 1000 : end * 1000]
                
                # Save the segment in the correct UUID folder
                clip.export(os.path.join(speaker_folder, f"{start}_{end}_{file_name}.wav"), format="wav")
        
        if text:
            entry += f"{speaker_uuid_map[speaker]} ({start} : {end}) : {text}\n"
        
    lf.write(entry.encode('utf-8'))      
    lf.close()

    # -------------------------log file end-------------------------