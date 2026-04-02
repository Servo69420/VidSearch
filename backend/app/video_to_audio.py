# audio extraction from video
import ffmpeg
import tempfile
import os


def video_to_audio(video_path: str) -> str:
    #extract audio and create wav file, return path to it
    temporary_audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temporary_audio_file.close()

    ffmpeg.input(video_path).output(temporary_audio_file.name, ac=1, ar=16000, format='wav').overwrite_output().run(quiet=True)

    return temporary_audio_file.name

def delete_temporary_audio_file(audio_path: str) -> None:
    #delet file after we transcribed it
    if os.path.exists(audio_path):
        os.remove(audio_path)
