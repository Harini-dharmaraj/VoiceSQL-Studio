import os
import shutil
import numpy as np
import soundfile as sf

def is_audio_silent(file_path: str, threshold: float = 0.008) -> bool:
    """Check if the recorded audio file is silent or too faint to contain audible speech."""
    try:
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:
            return True
        audio, _ = sf.read(file_path)
        if len(audio) == 0:
            return True
        max_amp = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))
        return max_amp < threshold and rms < (threshold / 2.0)
    except Exception:
        return False

def remove_noise(input_file: str, output_file: str) -> str:
    """
    Preprocess and gently reduce background noise while normalizing audio gain
    so speech reaches Whisper at clear, optimal listening levels.
    """
    try:
        audio, sample_rate = sf.read(input_file)
        
        # Convert multi-channel (stereo) to mono
        if len(audio.shape) > 1 and audio.shape[1] > 1:
            audio = np.mean(audio, axis=1)

        # 1. Automatic Gain Control / Peak Normalization (boost faint microphone input)
        max_amp = np.max(np.abs(audio))
        if max_amp > 0.002:
            audio = audio * (0.90 / max_amp)

        # 2. Gentle Noise Reduction (gentle 0.25 decrease preserves crisp speech consonants)
        try:
            import noisereduce as nr
            cleaned = nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                prop_decrease=0.25,
                stationary=True
            )
            # Re-normalize after filtering
            clean_max = np.max(np.abs(cleaned))
            if clean_max > 0.002:
                cleaned = cleaned * (0.90 / clean_max)
        except Exception:
            cleaned = audio

        sf.write(output_file, cleaned, sample_rate)
        return output_file

    except Exception:
        try:
            shutil.copyfile(input_file, output_file)
            return output_file
        except Exception:
            return input_file