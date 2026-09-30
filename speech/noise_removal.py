import noisereduce as nr
import soundfile as sf


def remove_noise(input_file, output_file):

    audio, sample_rate = sf.read(input_file)

    cleaned = nr.reduce_noise(
        y=audio,
        sr=sample_rate
    )

    sf.write(output_file, cleaned, sample_rate)

    return output_file