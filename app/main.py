import base64
import json
import re
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.config import Settings, get_settings
from app.models import CallRequest, CallResponse
from app.piper import PiperError, PiperSynthesizer
from app.voximplant import VoximplantClient, VoximplantError


AUDIO_ID_RE = re.compile(r"^[a-f0-9]{32}$")

app = FastAPI(
    title="Piper Voximplant Outbound Calls MVP",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/audio/{audio_id}.wav")
async def get_audio(
    audio_id: str,
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    if not AUDIO_ID_RE.fullmatch(audio_id):
        raise HTTPException(status_code=404, detail="Audio file not found")

    audio_path = Path(settings.generated_audio_dir) / f"{audio_id}.wav"
    if not audio_path.exists() or not audio_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=f"{audio_id}.wav",
    )


@app.post("/calls", response_model=CallResponse, status_code=201)
async def create_call(
    payload: CallRequest,
    settings: Settings = Depends(get_settings),
) -> CallResponse:
    synthesizer = PiperSynthesizer(settings)
    voximplant = VoximplantClient(settings)

    try:
        audio_id, _audio_path = await synthesizer.synthesize_to_wav(payload.text)
    except PiperError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    audio_url = f"{settings.public_base_url}/audio/{audio_id}.wav"
    if settings.github_token and settings.github_repo:
        try:
            content = base64.b64encode(_audio_path.read_bytes()).decode()
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.put(
                    f"https://api.github.com/repos/{settings.github_repo}/contents/{audio_id}.wav",
                    headers={
                        "Authorization": f"Bearer {settings.github_token}",
                        "Accept": "application/vnd.github+json",
                    },
                    json={"message": f"add {audio_id}", "content": content},
                )
            print(f"GitHub upload status: {resp.status_code} — {resp.text[:200]}")
            if resp.status_code in (200, 201):
                audio_url = f"https://raw.githubusercontent.com/{settings.github_repo}/main/{audio_id}.wav"
        except Exception as exc:
            print(f"GitHub upload error: {exc}")
    else:
        print(f"GitHub not configured: token={bool(settings.github_token)} repo={settings.github_repo}")

    script_custom_data = json.dumps(
        {
            "destination": payload.destination,
            "callerId": payload.caller_id,
            "audioUrl": audio_url,
        },
        separators=(",", ":"),
    )

    custom_data_size = len(script_custom_data.encode("utf-8"))
    if custom_data_size > settings.voximplant_custom_data_max_bytes:
        raise HTTPException(
            status_code=400,
            detail=(
                "Voximplant script_custom_data is too long "
                f"({custom_data_size} bytes). Use a shorter PUBLIC_BASE_URL."
            ),
        )

    try:
        start_response = await voximplant.start_scenario(script_custom_data)
    except VoximplantError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return CallResponse(
        id=audio_id,
        audio_url=audio_url,
        voximplant=start_response,
    )

