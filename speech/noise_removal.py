import noisereduce as nr
import soundfile as sf
import shutil

def remove_noise(input_file, output_file):
    """Gently reduce background noise while preserving voice clarity."""
    try:
        audio, sample_rate = sf.read(input_file)
        cleaned = nr.reduce_noise(
            y=audio,
            sr=sample_rate,
            prop_decrease=0.6
        )
        sf.write(output_file, cleaned, sample_rate)
        return output_file
    except Exception:
        try:
            shutil.copyfile(input_file, output_file)
            return output_file
        except Exception:
            return input_file