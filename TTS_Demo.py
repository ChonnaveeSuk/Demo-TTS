import os
import json
import streamlit as st
import boto3
from google.cloud import texttospeech
from google.api_core.exceptions import InvalidArgument

# Import functions from LANGUAGES_ALL.py to use during Refresh.
from LANGUAGES_ALL import save_gcp_voices_to_json, save_polly_voices_to_json

# Load JSON file

LANG_DIR = r"C:\Demo_TTS\All_Lang"
gcp_json = os.path.join(LANG_DIR, "GCP_VOICES_ALL.json")
polly_json = os.path.join(LANG_DIR, "POLLY_VOICES_ALL.json")

def load_gcp_voices():
    with open(gcp_json, "r", encoding="utf-8") as f:
        return json.load(f)

def load_polly_voices():
    with open(polly_json, "r", encoding="utf-8") as f:
        return json.load(f)

if "GCP_VOICES_ALL" not in st.session_state:
    st.session_state.GCP_VOICES_ALL = load_gcp_voices()
if "POLLY_VOICES_ALL" not in st.session_state:
    st.session_state.POLLY_VOICES_ALL = load_polly_voices()

# Basic code 
OUTPUT_DIR = r"C:\Demo_TTS\audio_File"
os.makedirs(OUTPUT_DIR, exist_ok=True)

if "ssml_text" not in st.session_state:
    st.session_state.ssml_text = "<speak>Hello!</speak>"
st.title("TTS Demo: Google Cloud TTS & AWS Polly")

# REFRESH VOICES 
if st.button("Refresh Voices"):
    try:
        path_gcp = save_gcp_voices_to_json()
        path_polly = save_polly_voices_to_json()

        # โหลดกลับเข้า session_state ทันที
        st.session_state.GCP_VOICES_ALL = load_gcp_voices()
        st.session_state.POLLY_VOICES_ALL = load_polly_voices()

        st.success("Refreshed voices successfully!")
    except Exception as e:
        st.error(f"Failed to refresh voices: {e}")

text_mode = st.radio("Select Input Mode:", ("Plain Text", "SSML"))

if text_mode == "SSML":
    ssml_content = st.text_area("Enter SSML:", st.session_state.ssml_text, height=150)
    if ssml_content != st.session_state.ssml_text:
        st.session_state.ssml_text = ssml_content
    text_input = st.session_state.ssml_text
else:
    text_input = st.text_area("Enter Plain Text:", "Hello! This is a Text-to-Speech test.", height=150)

platform = st.radio("Select the platform:", ("Google Cloud TTS", "AWS Polly"))
audio_format = st.selectbox("Select Audio Format:", ["mp3", "wav", "ogg"])

if platform == "Google Cloud TTS":
    gcp_voices_dict = st.session_state.GCP_VOICES_ALL  # ดึงจาก session_state
    gcp_lang_codes = sorted(list(gcp_voices_dict.keys()))
    selected_lang_code = st.selectbox("Select Language Code (GCP):", gcp_lang_codes)

    gender = st.radio("Select Voice Gender:", ("Female", "Male"))
    voice_list = gcp_voices_dict[selected_lang_code].get(gender, [])
    if not voice_list:
        st.warning(f"No {gender} voices for {selected_lang_code} in GCP.")
        selected_voice = None
    else:
        selected_voice = st.selectbox("Select Voice (Google Cloud):", voice_list)
else:
    polly_voices_dict = st.session_state.POLLY_VOICES_ALL
    polly_lang_codes = sorted(list(polly_voices_dict.keys()))
    selected_lang_code = st.selectbox("Select Language Code (Polly):", polly_lang_codes)

    gender = st.radio("Select Voice Gender:", ("Female", "Male"))
    voice_list = polly_voices_dict[selected_lang_code].get(gender, [])
    if not voice_list:
        st.warning(f"No {gender} voices for {selected_lang_code} in AWS Polly.")
        selected_voice = None
    else:
        selected_voice = st.selectbox("Select Voice (AWS Polly):", voice_list)

def gcp_tts(text, voice_name, lang_code, is_ssml=False, file_format="mp3"):
    if file_format == "mp3":
        audio_encoding = texttospeech.AudioEncoding.MP3
        ext = ".mp3"
    elif file_format == "wav":
        audio_encoding = texttospeech.AudioEncoding.LINEAR16
        ext = ".wav"
    elif file_format == "ogg":
        audio_encoding = texttospeech.AudioEncoding.OGG_OPUS
        ext = ".ogg"
    else:
        # fallback
        audio_encoding = texttospeech.AudioEncoding.MP3
        ext = ".mp3"

    output_file = os.path.join(OUTPUT_DIR, f"GCP_output{ext}")
    client = texttospeech.TextToSpeechClient()

    if is_ssml:
        synthesis_input = texttospeech.SynthesisInput(ssml=text)
    else:
        synthesis_input = texttospeech.SynthesisInput(text=text)

    voice_params = texttospeech.VoiceSelectionParams(
        language_code=lang_code,
        name=voice_name
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=audio_encoding)

    try:
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )
    except InvalidArgument as e:
        st.error(f"Google Cloud TTS Error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected Error: {e}")
        return None

    with open(output_file, "wb") as out:
        out.write(response.audio_content)
    return output_file

def aws_polly_tts(text, voice_id, is_ssml=False, file_format="mp3"):
    polly_client = boto3.client("polly")

    if file_format == "mp3":
        output_format = "mp3"
        ext = ".mp3"
    elif file_format == "wav":
        # Polly ไม่มี "wav" ตรง ๆ มีแต่ "pcm"
        # จะได้เป็น raw PCM 16-bit => ผู้ใช้บางทีจะเปิดได้ บางทีอาจต้องแปลง
        output_format = "pcm"
        ext = ".wav"
    elif file_format == "ogg":
        output_format = "ogg_vorbis"
        ext = ".ogg"
    else:
        output_format = "mp3"
        ext = ".mp3"

    text_type = "ssml" if is_ssml else "text"
    output_file = os.path.join(OUTPUT_DIR, f"Polly_output{ext}")

    try:
        response = polly_client.synthesize_speech(
            Text=text,
            VoiceId=voice_id,
            OutputFormat=output_format,
            TextType=text_type
        )
        with open(output_file, "wb") as f:
            f.write(response["AudioStream"].read())
    except Exception as e:
        st.error(f"AWS Polly Error: {e}")
        return None

    return output_file

if st.button("Convert Text to Speech"):
    if not text_input.strip():
        st.error("Please enter text (or SSML) before converting.")
    else:
        if not selected_voice:
            st.error("No valid voice selected.")
        else:
            is_ssml_mode = (text_mode == "SSML")

            if platform == "Google Cloud TTS":
                audio_file = gcp_tts(
                    text=text_input,
                    voice_name=selected_voice,
                    lang_code=selected_lang_code,
                    is_ssml=is_ssml_mode,
                    file_format=audio_format
                )
            else:
                audio_file = aws_polly_tts(
                    text=text_input,
                    voice_id=selected_voice,
                    is_ssml=is_ssml_mode,
                    file_format=audio_format
                )

            if audio_file and os.path.exists(audio_file):
                if audio_format == "mp3":
                    st.audio(audio_file, format="audio/mp3")
                elif audio_format == "wav":
                    st.audio(audio_file, format="audio/wav")
                elif audio_format == "ogg":
                    st.audio(audio_file, format="audio/ogg")

                st.success(f"Audio file generated successfully: {audio_file}")

                with open(audio_file, "rb") as f:
                    audio_data = f.read()

                if audio_format == "mp3":
                    mime_type = "audio/mp3"
                elif audio_format == "wav":
                    mime_type = "audio/wav"
                elif audio_format == "ogg":
                    mime_type = "audio/ogg"
                else:
                    mime_type = "audio/mp3"

                st.download_button(
                    label=f"Download {audio_format.upper()}",
                    data=audio_data,
                    file_name=os.path.basename(audio_file),
                    mime=mime_type
                )
