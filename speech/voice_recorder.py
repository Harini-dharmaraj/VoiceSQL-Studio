import sounddevice as sd
import soundfile as sf


def record_audio(filename="audio.wav", duration=5, samplerate=16000):
    """
    Record audio from microphone and save it as WAV.
    """

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