import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")
SIP_RE  = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+$")


class CallRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    destination: str = Field(
        ...,
        examples=["+43123456789", "testuser@app.account.voximplant.com"],
        description="Recipient: E.164 phone number or Voximplant SIP username.",
    )
    caller_id: str = Field(
        ...,
        examples=["+43111222333", "testcaller"],
        description="Verified Voximplant caller ID (E.164 or SIP username).",
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to synthesize with Piper.",
    )

    @field_validator("destination", "caller_id")
    @classmethod
    def validate_destination(cls, value: str) -> str:
        if E164_RE.fullmatch(value) or SIP_RE.fullmatch(value):
            return value
        raise ValueError(
            "must be an E.164 phone number (+43123456789) "
            "or a SIP address (user@domain)"
        )


class CallResponse(BaseModel):
    id: str
    audio_url: str
    voximplant: dict

