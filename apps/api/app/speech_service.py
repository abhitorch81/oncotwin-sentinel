"""High-quality, non-reasoning speech rendering for validated agent text."""


VOICE_NAME = "en-US-Chirp3-HD-Kore"


def synthesize_agent_speech(text: str) -> bytes:
    clean = " ".join(text.split()).strip()
    if not clean or len(clean) > 2_000:
        raise ValueError("Speech text must contain between 1 and 2000 characters")

    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    response = client.synthesize_speech(
        request={
            "input": texttospeech.SynthesisInput(text=clean),
            "voice": texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=VOICE_NAME,
            ),
            "audio_config": texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.04,
            ),
        }
    )
    return response.audio_content
