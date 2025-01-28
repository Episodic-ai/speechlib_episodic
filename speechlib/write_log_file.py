import os
from datetime import datetime
from pydub import AudioSegment

def write_log_file(common_segments, log_folder, file_name, language):

    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    #---------------------log file part-------------------------
        
    current_time = datetime.now().strftime('%H%M%S')
    
    og_file_name = file_name

    file_name = os.path.splitext(os.path.basename(file_name))[0]

    log_file = log_folder + "/" + file_name + "_" + current_time + "_" + language + ".txt"
    
    lf=open(log_file,"wb")

    entry = ""
    
    # Ensure the unidentified_speakers subfolder exists
    unidentified_speakers_folder = os.path.join(log_folder, "unidentified_speakers")
    if not os.path.exists(unidentified_speakers_folder):
        os.makedirs(unidentified_speakers_folder)
    
    for segment in common_segments:
        start = segment[0]
        end = segment[1]
        text = segment[2]
        speaker = segment[3]
        
        # if speaker begins with 'SPEAKER_', extract segment from audio file and put into separate folder
        if speaker.startswith("SPEAKER_"):
            
            # Ensure the unidentified_speakers subfolder exists
            new_speaker_folder = os.path.join(unidentified_speakers_folder, speaker)
            if not os.path.exists(new_speaker_folder):
                os.makedirs(new_speaker_folder)
            
            audio = AudioSegment.from_file(og_file_name, format="wav")
            clip = audio[start*1000:end*1000]
            clip.export(new_speaker_folder + "/" + str(start) + "_" + str(end) + "_" + file_name + "_" + ".wav", format="wav")
        
        if text != "" and text != None:
            entry += f"{speaker} ({start} : {end}) : {text}\n"
        
    lf.write(bytes(entry.encode('utf-8')))      
    lf.close()

    # -------------------------log file end-------------------------
