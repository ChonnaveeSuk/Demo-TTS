import os
import boto3

def aws_polly_tts(text):  # เพิ่มพารามิเตอร์ text
    output_dir = "C:\\Demo_TTS\\audio_File"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "AWS_output.mp3")

    polly = boto3.client(
        "polly",
        region_name="ap-southeast-1",
    )

    response = polly.synthesize_speech(
        Text=text,  
        OutputFormat="mp3",
        VoiceId="Joanna", 
        LanguageCode="en-US"
    )

    with open(output_file, "wb") as file:
        file.write(response["AudioStream"].read())

    print(f"Saved output to {output_file}")

aws_polly_tts("Hello, welcome to AWS Polly Text-to-Speech system.")