import os
from pathlib import Path
from gtts import gTTS

# Create output audio directory
AUDIO_DIR = Path(__file__).resolve().parent
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES = {
    "twi_reminder.mp3": ("Mema wo akye. Wo insurance premium bi nte hɔ. Yɛsrɛ wo, fa sika no kɔ wo agent nkyɛn.", "en"),
    "twi_confirm.mp3": ("Meda wo ase. Yɛbɛ bo w'adwuma ho ban.", "en"),
    "dagbani_reminder.mp3": ("N bɔri n lɔri. A insurance puuni bi ka. Shɛri ni fo agent ka amoonin.", "en"),
    "dagbani_confirm.mp3": ("Mpayi. Ti ni fa a tuma gbahin.", "en")
}

def generate_all_audio():
    print(f"[AUDIO GENERATOR] Output Directory: {AUDIO_DIR}")
    for filename, (text, lang) in TEMPLATES.items():
        output_path = AUDIO_DIR / filename
        print(f"[AUDIO GENERATOR] Generating {filename}...")
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(output_path))
        print(f" -> Saved: {output_path}")

if __name__ == "__main__":
    generate_all_audio()
