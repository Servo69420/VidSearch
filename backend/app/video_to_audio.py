import os
import tempfile
from abc import ABC, abstractmethod

import ffmpeg


def _ffmpeg_cmd() -> str:
    from app.config import settings
    return settings.FFMPEG_PATH or "ffmpeg"


class BaseAudioExtractor(ABC):
    @abstractmethod
    def extract(self, video_path: str) -> str:
        pass

    @abstractmethod
    def cleanup(self, audio_path: str) -> None:
        pass


class FFmpegAudioExtractor(BaseAudioExtractor):
    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.__sample_rate = sample_rate
        self.__channels = channels

    @property
    def sample_rate(self) -> int:
        return self.__sample_rate

    @property
    def channels(self) -> int:
        return self.__channels

    def extract(self, video_path: str) -> str:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        try:
            (
                ffmpeg
                .input(video_path)
                .output(tmp.name, ac=self.__channels, ar=self.__sample_rate,
                        format="mp3", audio_bitrate="64k")
                .overwrite_output()
                .run(cmd=_ffmpeg_cmd(), capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            stderr = e.stderr.decode(errors='replace') if e.stderr else "(empty)"
            raise RuntimeError(f"FFmpeg failed: {stderr}") from e
        return tmp.name

    def cleanup(self, audio_path: str) -> None:
        if os.path.exists(audio_path):
            os.remove(audio_path)


_extractor = FFmpegAudioExtractor()


def video_to_audio(video_path: str) -> str:
    return _extractor.extract(video_path)


def delete_temporary_audio_file(audio_path: str) -> None:
    _extractor.cleanup(audio_path)
