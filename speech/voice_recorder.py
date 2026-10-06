import os

def record_audio(filename="audio/audio.wav", duration=5, samplerate=16000):
    """
    Record audio from physical hardware microphone and save it as WAV.
    Gracefully handles headless cloud servers where no soundcard exists.
    """
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
    try:
        import sounddevice as sd
        import soundfile as sf

        print("Recording...")
        audio = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        sf.write(filename, audio, samplerate)
        print("Recording Saved!")
        return filename
    except Exception as e:
        err_msg = str(e)
        if "device -1" in err_msg or "querying device" in err_msg or "PortAudio" in err_msg:
            raise RuntimeError(
                "No hardware sound card detected on this machine. "
                "Because this app is running in the Cloud, the remote server has no physical microphone. "
                "Please use the Browser Microphone widget or click any sample prompt chip above!"
            ) from e
        raise RuntimeError(f"Microphone recording error: {e}") from e