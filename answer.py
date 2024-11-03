import streamlit as st
import openai
import requests
import moviepy.editor as mp
from gtts import gTTS
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import time
import os

# Step 1: Transcribe audio using AssemblyAI API
def transcribing(video_file):
    # Your AssemblyAI API Key
    api_key = ""  # Replace with your AssemblyAI API key

    # Step 1: Upload the video file to AssemblyAI
    def upload_to_assemblyai(file_path):
        headers = {'authorization': api_key}
        with open(file_path, 'rb') as f:
            response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=f)
        response.raise_for_status()
        return response.json()['upload_url']

    # Step 2: Start transcription using the uploaded file URL
    def request_transcription(upload_url):
        endpoint = 'https://api.assemblyai.com/v2/transcript'
        json_data = {
            'audio_url': upload_url,
            'auto_highlights': False,
            'iab_categories': False
        }
        headers = {
            'authorization': api_key,
            'content-type': 'application/json'
        }
        response = requests.post(endpoint, json=json_data, headers=headers)
        response.raise_for_status()
        # st.write(response.json()['id'])
        return response.json()['id']
      

    # Step 3: Polling for transcription result
    def get_transcription_result(transcription_id):
        endpoint = f'https://api.assemblyai.com/v2/transcript/{transcription_id}'
        headers = {'authorization': api_key}
        
        while True:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            result = response.json()

            if result['status'] == 'completed':
                return result['text']
            elif result['status'] == 'failed':
                raise Exception("Transcription failed.")
            else:
                time.sleep(5)  # Wait 5 seconds before trying again

    # Upload the video file and request transcription
    upload_url = upload_to_assemblyai(video_file)
    transcription_id = request_transcription(upload_url)
    transcription_text = get_transcription_result(transcription_id)
    
    return transcription_text
# Function to filter filler words and silence them in audio
def silence_filler_words_in_audio(words_with_timestamps, audio_input_path, output_path):
    # Create a list of filler words for silencing
    filler_words = ['mama,','mama.','um.','um,','uh.','uh,', 'uh', 'like','mmm.','mmm,','ah?','ah,','ah.','huh,','huh?','mmm','huh','ahh,','ahh.','ahh?','haa','ha','uh','hmm','haha','haha.','haha,','hughaa']  # Define common filler words

    # List to store filler timestamps (start and end times)
    filler_timestamps = []
    
    # here i am using every single vocal in audio for silencing ,bacause it eliminates problems while overlaping audio with ai voice
    for word_info in words_with_timestamps:
        filler_words.append(word_info['text'].lower())
        filler_words.append(word_info['text'].lower()+'.')
        filler_words.append(word_info['text'].lower()+',')
        filler_words.append(word_info['text'].lower()+'?')

    # Iterate over the words array to find filler words and get their timestamps
    for word_info in words_with_timestamps:
        if word_info['text'].lower() in filler_words:
            start_time = word_info['start'] / 1000  # Convert to seconds
            end_time = word_info['end'] / 1000      # Convert to seconds
            filler_timestamps.append((start_time, end_time))

    # Check if there are any filler words to process
    if not filler_timestamps:
        print("No filler words found to silence.")
        return

    # Create individual volume filters for each filler word timestamp
    filters = []
    for start, end in filler_timestamps:
        filters.append(f"volume=enable='between(t,{start},{end})':volume=0")

    # Combine all filters by chaining them with commas
    filter_chain = ','.join(filters)

    # Debugging: print the constructed filter string

    # st.write("Constructed filter chain:", filter_chain)     

    # FFmpeg command to apply the filter chain to the audio
    command = f"ffmpeg -i \"{audio_input_path}\" -af \"{filter_chain}\" \"{output_path}\""

    # Debugging: print the command to ensure it's correct
    # print("Executing command:", command)

    # Execute the command
    os.system(command)


def extract_audio_from_video(video_file, audio_output_path):
    video = VideoFileClip(video_file)
    video.audio.write_audiofile(audio_output_path)
    return audio_output_path

def transcribe_audio(video_file):
    # Your AssemblyAI API Key
    api_key = ""  # Replace with your AssemblyAI API key  (This is my account api key)

    # Step 1: Upload the video file to AssemblyAI
    def upload_to_assemblyai(file_path):
        headers = {'authorization': api_key}
        with open(file_path, 'rb') as f:
            response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=f)
        response.raise_for_status()
        return response.json()['upload_url']

    # Step 2: Start transcription using the uploaded file URL
    def request_transcription(upload_url):
        endpoint = 'https://api.assemblyai.com/v2/transcript'
        json_data = {
            'audio_url': upload_url,
            'auto_highlights': False,
            'iab_categories': False,
            'word_boost': [],  # You can use this to prioritize words if needed
            'disfluencies': True,  # Optional: to detect fillers like "um", "uh"
            'punctuate': True  # Optional: to add punctuation
        }
        headers = {
            'authorization': api_key,
            'content-type': 'application/json'
        }
        response = requests.post(endpoint, json=json_data, headers=headers)
        response.raise_for_status()
        return response.json()['id']

    # Step 3: Polling for transcription result (this time we want words with timestamps)
    def get_transcription_result(transcription_id):
        endpoint = f'https://api.assemblyai.com/v2/transcript/{transcription_id}'
        headers = {'authorization': api_key}
        
        while True:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            result = response.json()

            if result['status'] == 'completed':
                return result['words']  # Returns the words with timestamps
            elif result['status'] == 'failed':
                raise Exception("Transcription failed.")
            else:
                time.sleep(5)  # Wait 5 seconds before trying again

    # Upload the video file and request transcription
    upload_url = upload_to_assemblyai(video_file)
    transcription_id = request_transcription(upload_url)
    words_with_timestamps = get_transcription_result(transcription_id)
    
    return words_with_timestamps  # Returning words with timestamps instead of just text

# Step 2: Correct transcription using OpenAI GPT-4o (no change here)
def correct_transcription(transcription):
    azure_openai_key = ""  # Replace with your Azure API key
    azure_openai_endpoint = "https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"  # Replace with your Azure endpoint URL
    
    if not azure_openai_key or not azure_openai_endpoint:
        raise ValueError("Azure OpenAI API key or endpoint is missing!")
    
    headers = {
        "Content-Type": "application/json",
        "api-key": azure_openai_key
    }
    
    data = {
        "messages": [
            {"role": "user", "content": f"Correct the following transcription by removing any grammatical errors, 'umms,' and 'hmms'and just give corrected transcription only ,don't include your explanation of what you have given at begging and ending of actual output,just give corrected transcription only:\n\n{transcription}"}
        ],
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(azure_openai_endpoint, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            corrected_text = result["choices"][0]["message"]["content"].strip()
            return corrected_text
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to correct transcription: {str(e)}")
        return None


# Step 3: Generate audio using gTTS
def generate_audio(corrected_transcription,audio_file):
    # Load the original audio
    original_audio = AudioSegment.from_file(audio_file)
    total_words=len(corrected_transcription)

    output_audios=[]
    filler_ids=[]
    for i in range(total_words):
        # Define the folder path where you want to save the file
         output_dir = r"C:\Users\HI\Desktop\python_programs\dsa\output_audios"   # create one folder to store ai voice chunks

        # Create the directory if it doesn't exist
         audio=f"{output_dir}\\audio{i+1}.mp3"
        
         fillers=['mmm.','mmm','mmm,','umm','un','huh']
         text=corrected_transcription[i]['text'].lower()
         
         if text not in fillers:
            tts = gTTS(text=text, lang='en',slow=True)
            tts.save(audio)  # Save audio as mp3
         else:
             filler_ids+=[i]
    
    # List of timestamps and AI-generated audio filenames
    timestamps_and_audio =[]
    for i in range(total_words):
        if i not in filler_ids:
            timestamps_and_audio+=[{
               "start":corrected_transcription[i]["start"],
               "end":corrected_transcription[i]["end"],
               "audio":output_dir+"\\audio"+str(i+1)+".mp3"
            }]
    # Create a copy of the original audio for editing
    edited_audio = original_audio

    # Replace segments in the audio
    for segment in timestamps_and_audio:
        start_time = segment["start"]
        end_time = segment["end"]
        ai_audio = AudioSegment.from_file(segment["audio"])

        # Adjust the duration of the AI audio to fit the original segment
        ai_audio = ai_audio[:end_time - start_time]

        # Overlay the AI audio on the original audio
        edited_audio = edited_audio.overlay(ai_audio, position=start_time)

    # Export the final edited audio
    final_audio_file = r"C:\Users\HI\Desktop\python_programs\dsa\final_audio.mp3"  # specify the  output file path in your pc

    edited_audio.export(final_audio_file, format="mp3")
    return final_audio_file
    
    
# Step 4: Replace audio in video
def replace_audio(video_file, new_audio_file):
    output_video_path = r"C:\Users\HI\Desktop\python_programs\dsa\output_video.mp4"  #  Specify the output video path in your pc
    video = mp.VideoFileClip(video_file)
    new_audio = mp.AudioFileClip(new_audio_file)
    final_video = video.set_audio(new_audio)
    final_video.write_videofile(output_video_path, codec="libx264")
    return output_video_path

# Streamlit app interface
def main():
    st.title("Video Audio Replacement using AI")
    
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "avi"])
    st.write("Try this video,name Whats eating giberts grape Youtube link :https://youtu.be/GmIGvynRMyU?si=2mqSlS7_ZwZ4_YRP")
    
    if uploaded_file is not None:
        with open("temp_video.mp4", "wb") as f:
            f.write(uploaded_file.read())
        
        st.header("Transcribing audio using AssemblyAI...")
        transcription = transcribe_audio("temp_video.mp4")
        st.markdown('<h2 style="color: green;">Transcribed the video  Successfully</h2>', unsafe_allow_html=True)
        st.write(transcription)
        st.write(len(transcription))

        transcribed_text=transcribing("temp_video.mp4")
        st.header("Transcribed text: ")
        st.write(transcribed_text)

        # Extract audio from the video
        st.header("Extracting the Audio from Video")
        audio_file = r"C:\Users\HI\Desktop\python_programs\dsa\extracted_audio.mp3"
        video_file="temp_video.mp4"
        extracted_audio_path = extract_audio_from_video(video_file, audio_file)
        st.markdown('<h2 style="color: green;">audio extracted from video Successfully</h2>', unsafe_allow_html=True)
        
        st.header("Removing fillers words from extracted audio")
        words_with_timestamps=transcription
        output_audio_no_fillers=r"C:\Users\HI\Desktop\python_programs\dsa\no_fillers.mp3"
        silence_filler_words_in_audio(words_with_timestamps,audio_file, output_audio_no_fillers)
        st.markdown('<h2 style="color: green;">fillers are Removed from  audio Successfully</h2>', unsafe_allow_html=True)


        st.header("synchronizing ai voice with original audio using Timestamps")
        final_audio=generate_audio(transcription,output_audio_no_fillers)
        st.markdown('<h2 style="color: green;">final synchronized Audio is generated successfully!</h2>', unsafe_allow_html=True)
        
        st.header("Replacing audio in the video...")
        st.write("please wait some time...")
        result=replace_audio("temp_video.mp4", final_audio)
        st.markdown('<h2 style="color: green;">Final video with new audio is ready!</h2>', unsafe_allow_html=True)
        st.video(result)
        



if __name__ == "__main__":
    main()




