import os
from datetime import datetime
from pydub import AudioSegment
import uuid

"""
This script processes speech segments extracted from an audio file, organizes them by speaker, 
saves corresponding audio clips, and logs transcriptions with timestamps. The key functionalities include:

1. **Organizing Speaker Audio Data:**
   - Each speaker is assigned a unique identifier (UUID for "SPEAKER_XX" labels, actual name otherwise).
   - Speaker-specific folders are created within the `unidentified_speakers` directory.

2. **Storing Speaker Audio Clips:**
   - For speakers whose names do *not* start with "SPEAKER_", up to 4 audio segments are stored if their folder has fewer than 4 files.
   - Segments are sorted by duration, and the longest one is saved as `verification_sample.wav`.
   - All saved segments are capped at a maximum length of 15 seconds.

3. **Generating a Log File:**
   - A structured log file is created with timestamps and transcriptions of each speaker.
   - Each speaker's speech segment, along with its start and end timestamps, is recorded in the log.

4. **File Handling and Storage Management:**
   - Ensures all necessary directories exist before storing files.
   - Prevents exceeding the 4-file limit for non-"SPEAKER_" speakers.
   - Writes speaker identifiers and their corresponding segments into a `.txt` log.

This system is designed to efficiently categorize and store speech data while maintaining constraints 
on the number of stored files per speaker.
"""

def write_log_file(common_segments, log_folder, file_name, language):

    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # ---------------------log file part-------------------------

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

    for speaker in set(segment[3] for segment in common_segments):
        if speaker.startswith("SPEAKER_"):
            if speaker not in speaker_uuid_map:
                speaker_uuid_map[speaker] = str(uuid.uuid4())
        else:
            # Use speaker's actual name instead of UUID
            speaker_uuid_map[speaker] = speaker

    for speaker in speaker_uuid_map:
        speaker_uuid = speaker_uuid_map[speaker]
        speaker_folder = os.path.join(unidentified_speakers_folder, speaker_uuid)
        os.makedirs(speaker_folder, exist_ok=True)

        # Filter and sort segments by duration (longest first)
        speaker_segments = [s for s in common_segments if s[3] == speaker]
        speaker_segments = sorted(speaker_segments, key=lambda s: (s[1] - s[0]), reverse=True)

        # Check how many files already exist
        existing_files = [
            f for f in os.listdir(speaker_folder) if os.path.isfile(os.path.join(speaker_folder, f))
        ]

        num_available_slots = max(0, 4 - len(existing_files))

        if num_available_slots == 0:
            continue  # Skip if folder already has 4 files

        audio = AudioSegment.from_file(og_file_name, format="wav")

        added_segments = 0  # Counter to track added segments for non-"SPEAKER_" speakers

        for i, segment in enumerate(speaker_segments):
            if added_segments >= num_available_slots:
                break  # Stop adding if we reach 4 files

            start, end, text, _ = segment
            
            # If audio length is greater than 15 seconds, shorten to 15 seconds
            if end - start > 15:
                end = start + 15

            clip = audio[start * 1000 : end * 1000]

            # Name the longest segment "verification_sample.wav"
            if i == 0:
                output_filename = "verification_sample.wav"
            else:
                output_filename = f"{start}_{end}_{file_name}.wav"

            clip.export(os.path.join(speaker_folder, output_filename), format="wav")
            added_segments += 1

            if text:
                entry += f"{speaker_uuid} ({start} : {end}) : {text}\n"

    lf.write(entry.encode('utf-8'))
    lf.close()

    # -------------------------log file end-------------------------