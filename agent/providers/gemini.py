"""Gemini structured-output residual reasoner with bounded failure handling."""

from __future__ import annotations

from json import loads
from os import getenv
from pathlib import Path

import httpx
from pydantic import TypeAdapter, ValidationError
from reconra.evidence.builder import EvidencePacket

from agent.providers.disabled import DisabledReasoner
from agent.schemas.proposal import AgentProposal

_PROPOSALS = TypeAdapter(list[AgentProposal])
_DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiReasoner:
    """Use Gemini only for structured, non-authoritative residual hypotheses."""

    def __init__(
        self,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._api_key = getenv("GEMINI_API_KEY")
        self._model = getenv("GEMINI_MODEL", _DEFAULT_MODEL)
        self._transport = transport
        self._timeout_seconds = timeout_seconds
        self.execution_status = "NOT_REQUIRED"

    async def reason(self, cases: list[EvidencePacket]) -> list[AgentProposal]:
        if not cases:
            self.execution_status = "NO_RESIDUALS"
            return []
        if not self._api_key:
            self.execution_status = "DISABLED_NO_CREDENTIAL"
            return await DisabledReasoner().reason(cases)

        payload = self._request_payload(cases)
        for attempt in range(2):
            try:
                response = await self._request(payload)
                proposals = self._parse_proposals(response)
                self.execution_status = "LIVE_PROVIDER_INVOKED"
                return proposals
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError):
                if attempt == 0:
                    continue
            except (KeyError, TypeError, ValueError, ValidationError):
                break
        self.execution_status = "PROVIDER_UNAVAILABLE"
        return await DisabledReasoner().reason(cases)

    async def _request(self, payload: dict[str, object]) -> dict[str, object]:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent"
        )
        async with httpx.AsyncClient(
            transport=self._transport,
            timeout=httpx.Timeout(self._timeout_seconds),
        ) as client:
            response = await client.post(url, params={"key": self._api_key}, json=payload)
            response.raise_for_status()
            data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Gemini response must be an object")
        return data

    @staticmethod
    def _parse_proposals(response: dict[str, object]) -> list[AgentProposal]:
        candidates = response["candidates"]
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("Gemini response has no candidates")
        candidate = candidates[0]
        if not isinstance(candidate, dict):
            raise ValueError("Gemini candidate must be an object")
        content = candidate["content"]
        if not isinstance(content, dict):
            raise ValueError("Gemini content must be an object")
        parts = content["parts"]
        if not isinstance(parts, list) or not parts or not isinstance(parts[0], dict):
            raise ValueError("Gemini response has no text part")
        text = parts[0]["text"]
        if not isinstance(text, str):
            raise ValueError("Gemini response text must be a string")
        parsed = loads(text)
        return _PROPOSALS.validate_python(parsed)

    @staticmethod
    def _request_payload(cases: list[EvidencePacket]) -> dict[str, object]:
        prompt = (Path(__file__).parents[1] / "prompts" / "residual_reasoning.md").read_text(
            encoding="utf-8"
        )
        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"{prompt}\n\nEvidence packets:\n"
                                f"{[case.model_dump(mode='json') for case in cases]}"
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {"responseMimeType": "application/json"},
        }
