import google.generativeai as genai
from gtts import gTTS
import os

# Load your Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")

# Text translation using Gemini
def translate_text(text, target_language):

    prompt = f"""
    Translate the following text into {target_language}.
    Only return the translated text.

    Text:
    {text}
    """

    response = model.generate_content(prompt)

    return response.text


# Convert translated text to audio
def text_to_audio(text, lang_code):

    audio_file = "translated_audio.mp3"

    tts = gTTS(text=text, lang=lang_code)
    tts.save(audio_file)

    return audio_file