import os
import json
import boto3
from google.cloud import texttospeech

OUTPUT_DIR = r"C:\Demo_TTS\All_Lang"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
            gender = v["Gender"]  
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
    gcp_path = os.path.join(OUTPUT_DIR, "GCP_VOICES_ALL.json")
    with open(gcp_path, "w", encoding="utf-8") as f:
        json.dump(gcp_voices, f, ensure_ascii=False, indent=2)
    return gcp_path

def save_polly_voices_to_json():
    polly_voices = build_polly_voices_dict()
    polly_path = os.path.join(OUTPUT_DIR, "POLLY_VOICES_ALL.json")
    with open(polly_path, "w", encoding="utf-8") as f:
        json.dump(polly_voices, f, ensure_ascii=False, indent=2)
    return polly_path

def main():
    gcp_path = save_gcp_voices_to_json()
    print(f"Generated {gcp_path}")

    polly_path = save_polly_voices_to_json()
    print(f"Generated {polly_path}")

if __name__ == "__main__":
    main()
