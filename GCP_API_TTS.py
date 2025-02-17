import os
from google.cloud import texttospeech

def gcp_tts(text):  # เพิ่มพารามิเตอร์ text
    output_dir = "C:\\Demo_TTS\\audio_File"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "GCP_output.mp3")

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)  
    voice = texttospeech.VoiceSelectionParams(
        language_code="th-TH", 
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    with open(output_file, "wb") as out:
        out.write(response.audio_content)

    print(f"Saved output to {output_file}")

gcp_tts("สวัสดีค่ะ ยินดีต้อนรับสู่ระบบแปลงข้อความเป็นเสียงของ Google Cloud. Hello, welcome to Google Cloud Text-to-Speech system.")