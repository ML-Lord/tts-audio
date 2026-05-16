import httpx

from app.config import Settings


class VoximplantError(RuntimeError):
    pass


class VoximplantClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def start_scenario(self, script_custom_data: str) -> dict:
        endpoint = f"{self.settings.voximplant_api_base_url}/StartScenarios/"
        payload = {
            "account_id": self.settings.voximplant_account_id,
            "api_key": self.settings.voximplant_api_key,
            "rule_id": self.settings.voximplant_rule_id,
            "script_custom_data": script_custom_data,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.request_timeout_seconds
            ) as client:
                response = await client.post(endpoint, data=payload)
        except httpx.HTTPError as exc:
            raise VoximplantError(f"Voximplant request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}

        if response.is_error:
            raise VoximplantError(f"Voximplant HTTP {response.status_code}: {data}")

        if data.get("error") or data.get("error_code"):
            raise VoximplantError(f"Voximplant API error: {data}")

        return data

