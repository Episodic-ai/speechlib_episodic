import os
from datetime import datetime
from pydub import AudioSegment
import uuid

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

    for speaker in set(segment[3] for segment in common_segments if segment[3].startswith("SPEAKER_")):
        if speaker not in speaker_uuid_map:
            speaker_uuid_map[speaker] = str(uuid.uuid4())

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

        for i, segment in enumerate(speaker_segments[:num_available_slots]):
            start, end, text, _ = segment
            clip = audio[start * 1000 : end * 1000]

            # Name the longest segment "verification_sample.wav"
            if i == 0:
                output_filename = "verification_sample.wav"
            else:
                output_filename = f"{start}_{end}_{file_name}.wav"

            clip.export(os.path.join(speaker_folder, output_filename), format="wav")

            if text:
                entry += f"{speaker_uuid} ({start} : {end}) : {text}\n"

    lf.write(entry.encode('utf-8'))
    lf.close()

    # -------------------------log file end-------------------------