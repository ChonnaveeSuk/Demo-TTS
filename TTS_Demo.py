import os
import json
import streamlit as st
import boto3
from google.cloud import texttospeech
from google.api_core.exceptions import InvalidArgument

# ส่วนฟังก์ชันสำหรับดึง Voices ของ Google Cloud / AWS Polly มาเก็บเป็น JSON
ALL_LANG_DIR = r"C:\Demo_TTS\All_Lang"
os.makedirs(ALL_LANG_DIR, exist_ok=True)

def build_gcp_voices_dict():
    client = texttospeech.TextToSpeechClient()
    response = client.list_voices()

    voices_dict = {}
    for voice in response.voices:
        for lang_code in voice.language_codes:
            if lang_code not in voices_dict:
                voices_dict[lang_code] = {"Female": [], "Male": []}

            if voice.ssml_gender == texttospeech.SsmlVoiceGender.FEMALE:
                voices_dict[lang_code]["Female"].append(voice.name)
            elif voice.ssml_gender == texttospeech.SsmlVoiceGender.MALE:
                voices_dict[lang_code]["Male"].append(voice.name)
            else:
                pass

    return voices_dict

def build_polly_voices_dict():
    polly_client = boto3.client("polly")
    voices_dict = {}
    next_token = None

    while True:
        if next_token:
            resp = polly_client.describe_voices(NextToken=next_token)
        else:
            resp = polly_client.describe_voices()

        for v in resp["Voices"]:
            lang_code = v["LanguageCode"]
            gender = v["Gender"]  # "Female", "Male", 
            voice_name = v["Name"]

            if lang_code not in voices_dict:
                voices_dict[lang_code] = {"Female": [], "Male": []}

            if gender == "Female":
                voices_dict[lang_code]["Female"].append(voice_name)
            elif gender == "Male":
                voices_dict[lang_code]["Male"].append(voice_name)
            else:
                pass

        if "NextToken" in resp and resp["NextToken"]:
            next_token = resp["NextToken"]
        else:
            break

    return voices_dict

def save_gcp_voices_to_json():
    gcp_voices = build_gcp_voices_dict()
    gcp_path = os.path.join(ALL_LANG_DIR, "GCP_VOICES_ALL.json")
    with open(gcp_path, "w", encoding="utf-8") as f:
        json.dump(gcp_voices, f, ensure_ascii=False, indent=2)
    return gcp_path

def save_polly_voices_to_json():
    polly_voices = build_polly_voices_dict()
    polly_path = os.path.join(ALL_LANG_DIR, "POLLY_VOICES_ALL.json")
    with open(polly_path, "w", encoding="utf-8") as f:
        json.dump(polly_voices, f, ensure_ascii=False, indent=2)
    return polly_path

def load_gcp_voices():
    gcp_path = os.path.join(ALL_LANG_DIR, "GCP_VOICES_ALL.json")
    with open(gcp_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_polly_voices():
    polly_path = os.path.join(ALL_LANG_DIR, "POLLY_VOICES_ALL.json")
    with open(polly_path, "r", encoding="utf-8") as f:
        return json.load(f)

# เริ่มต้นส่วน Streamlit UI
OUTPUT_DIR = r"C:\Demo_TTS\audio_File"
os.makedirs(OUTPUT_DIR, exist_ok=True)

if "ssml_text" not in st.session_state:
    st.session_state.ssml_text = "<speak>Hello!</speak>"
if "GCP_VOICES_ALL" not in st.session_state:
    try:
        st.session_state.GCP_VOICES_ALL = load_gcp_voices()
    except:
        st.session_state.GCP_VOICES_ALL = {}

if "POLLY_VOICES_ALL" not in st.session_state:
    try:
        st.session_state.POLLY_VOICES_ALL = load_polly_voices()
    except:
        st.session_state.POLLY_VOICES_ALL = {}

st.title("TTS Demo: Google Cloud TTS & AWS Polly")

# ปุ่ม Refresh Voices
if st.button("Refresh Voices"):
    try:
        path_gcp = save_gcp_voices_to_json()
        path_polly = save_polly_voices_to_json()

        # โหลดกลับเข้า session_state
        st.session_state.GCP_VOICES_ALL = load_gcp_voices()
        st.session_state.POLLY_VOICES_ALL = load_polly_voices()
        st.success("Refreshed voices successfully!")
    except Exception as e:
        st.error(f"Failed to refresh voices: {e}")

# เลือกโหมด input: Plain Text หรือ SSML
text_mode = st.radio("Select Input Mode:", ("Plain Text", "SSML"))

if text_mode == "SSML":
    ssml_content = st.text_area("Enter SSML:", st.session_state.ssml_text, height=150)
    if ssml_content != st.session_state.ssml_text:
        st.session_state.ssml_text = ssml_content
    text_input = st.session_state.ssml_text
else:
    text_input = st.text_area("Enter Plain Text:", "Hello! This is a Text-to-Speech test.", height=150)

# เลือก Platform
platform = st.radio("Select the platform:", ("Google Cloud TTS", "AWS Polly"))

# เลือกformatไฟล์ [MP3 / WAV / OGG]
audio_format = st.selectbox("Select Audio Format:", ["mp3", "wav", "ogg"])

# เลือกภาษา / Voice
if platform == "Google Cloud TTS":
    gcp_voices_dict = st.session_state.GCP_VOICES_ALL
    gcp_lang_codes = sorted(list(gcp_voices_dict.keys()))

    if gcp_lang_codes:
        selected_lang_code = st.selectbox("Select Language Code (GCP):", gcp_lang_codes)
        gender = st.radio("Select Voice Gender:", ("Female", "Male"))

        voice_list = gcp_voices_dict[selected_lang_code].get(gender, [])
        if not voice_list:
            st.warning(f"No {gender} voices for {selected_lang_code} in GCP.")
            selected_voice = None
        else:
            selected_voice = st.selectbox("Select Voice (Google Cloud):", voice_list)
    else:
        st.warning("No GCP voices loaded yet. Click 'Refresh Voices' first.")
        selected_lang_code = None
        selected_voice = None

else:
    polly_voices_dict = st.session_state.POLLY_VOICES_ALL
    polly_lang_codes = sorted(list(polly_voices_dict.keys()))

    if polly_lang_codes:
        selected_lang_code = st.selectbox("Select Language Code (Polly):", polly_lang_codes)
        gender = st.radio("Select Voice Gender:", ("Female", "Male"))

        voice_list = polly_voices_dict[selected_lang_code].get(gender, [])
        if not voice_list:
            st.warning(f"No {gender} voices for {selected_lang_code} in AWS Polly.")
            selected_voice = None
        else:
            selected_voice = st.selectbox("Select Voice (AWS Polly):", voice_list)
    else:
        st.warning("No Polly voices loaded yet. Click 'Refresh Voices' first.")
        selected_lang_code = None
        selected_voice = None

# ฟังก์ชันสังเคราะห์เสียง Google Cloud TTS
def gcp_tts(text, voice_name, lang_code, is_ssml=False, file_format="mp3"):
    client = texttospeech.TextToSpeechClient()
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
        audio_encoding = texttospeech.AudioEncoding.MP3
        ext = ".mp3"

    output_file = os.path.join(OUTPUT_DIR, f"GCP_output{ext}")

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

# ฟังก์ชันสังเคราะห์เสียง AWS Polly
def aws_polly_tts(text, voice_id, is_ssml=False, file_format="mp3"):
    polly_client = boto3.client("polly")

    if file_format == "mp3":
        output_format = "mp3"
        ext = ".mp3"
    elif file_format == "wav":
        output_format = "pcm"
        ext = ".wav"
    elif file_format == "ogg":
        output_format = "ogg_vorbis"
        ext = ".ogg"
    else:
        output_format = "mp3"
        ext = ".mp3"

    output_file = os.path.join(OUTPUT_DIR, f"Polly_output{ext}")

    text_type = "ssml" if is_ssml else "text"

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

# ปุ่ม Convert Text -> Speech
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
                # แสดงเสียง (st.audio) + ปุ่มดาวน์โหลด
                if audio_format == "mp3":
                    st.audio(audio_file, format="audio/mp3")
                    mime_type = "audio/mp3"
                elif audio_format == "wav":
                    st.audio(audio_file, format="audio/wav")
                    mime_type = "audio/wav"
                elif audio_format == "ogg":
                    st.audio(audio_file, format="audio/ogg")
                    mime_type = "audio/ogg"
                else:
                    mime_type = "audio/mp3"

                st.success(f"Audio file generated successfully: {audio_file}")

                with open(audio_file, "rb") as f:
                    audio_data = f.read()

                st.download_button(
                    label=f"Download {audio_format.upper()}",
                    data=audio_data,
                    file_name=os.path.basename(audio_file),
                    mime=mime_type
                )

def get_gcp_voices():
    """Fetch available voices from Google Cloud TTS API."""
    client = texttospeech.TextToSpeechClient()
    response = client.list_voices()

    voices_dict = {}
    for voice in response.voices:
        for lang in voice.language_codes:
            if lang not in voices_dict:
                voices_dict[lang] = []
            voices_dict[lang].append({
                "name": voice.name,
                "gender": texttospeech.SsmlVoiceGender(voice.ssml_gender).name,
                "sample_rate": voice.natural_sample_rate_hertz
            })

    # Save voices to JSON for later use
    with open("GCP_VOICES_ALL.json", "w", encoding="utf-8") as f:
        json.dump(voices_dict, f, ensure_ascii=False, indent=4)

    return voices_dict
