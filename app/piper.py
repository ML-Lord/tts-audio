import asyncio
import subprocess
import uuid
from pathlib import Path

from app.config import Settings


class PiperError(RuntimeError):
    pass


class PiperSynthesizer:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def synthesize_to_wav(self, text: str) -> tuple[str, Path]:
        return await asyncio.to_thread(self._synthesize_to_wav_sync, text)

    def _synthesize_to_wav_sync(self, text: str) -> tuple[str, Path]:
        audio_id = uuid.uuid4().hex
        output_path = self.settings.generated_audio_dir / f"{audio_id}.wav"
        self.settings.generated_audio_dir.mkdir(parents=True, exist_ok=True)

        command = [
            self.settings.piper_executable,
            "--model",
            str(self.settings.piper_model),
            "--output_file",
            str(output_path),
        ]

        if self.settings.piper_config:
            command.extend(["--config", str(self.settings.piper_config)])

        if self.settings.piper_speaker is not None:
            command.extend(["--speaker", str(self.settings.piper_speaker)])

        try:
            completed = subprocess.run(
                command,
                input=text,
                capture_output=True,
                check=False,
                encoding="utf-8",
                timeout=self.settings.piper_timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise PiperError(
                f"Piper executable not found: {self.settings.piper_executable}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            output_path.unlink(missing_ok=True)
            raise PiperError("Piper synthesis timed out") from exc

        if completed.returncode != 0:
            output_path.unlink(missing_ok=True)
            stderr = completed.stderr.strip() or "unknown Piper error"
            raise PiperError(stderr)

        if not output_path.exists() or output_path.stat().st_size == 0:
            output_path.unlink(missing_ok=True)
            raise PiperError("Piper did not create a WAV file")

        return audio_id, output_path

