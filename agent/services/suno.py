"""Suno music generation client — API key auth."""
import asyncio
import logging
from typing import Optional

import httpx

from agent.config import (
    SUNO_API_KEY, SUNO_BASE_URL, SUNO_MODEL,
    SUNO_POLL_INTERVAL, SUNO_POLL_TIMEOUT,
)

logger = logging.getLogger(__name__)


class SunoClient:
    """Async client for the Suno music generation API."""

    def __init__(self, api_key: str = "", base_url: str = ""):
        self.api_key = api_key or SUNO_API_KEY
        self.base_url = (base_url or SUNO_BASE_URL).rstrip("/")

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _check_key(self):
        if not self.api_key:
            raise RuntimeError(
                "SUNO_API_KEY not configured. "
                "Set it via environment variable or apply at https://suno.com/api"
            )

    async def generate(
        self,
        prompt: str = "",
        tags: str = "",
        title: str = "",
        make_instrumental: bool = False,
        model: str = "",
        gpt_description_prompt: str = "",
    ) -> list[dict]:
        """Submit a music generation request.

        Two modes:
        - Custom: provide `prompt` (lyrics with [Verse]/[Chorus] tags) + `tags` (style)
        - Description: provide `gpt_description_prompt` (natural language)

        Returns list of clip dicts with `id` and `status`.
        """
        self._check_key()
        payload = {
            "mv": model or SUNO_MODEL,
            "make_instrumental": make_instrumental,
        }

        if gpt_description_prompt and not prompt:
            payload["gpt_description_prompt"] = gpt_description_prompt
            payload["prompt"] = ""
        else:
            payload["prompt"] = prompt
            if tags:
                payload["tags"] = tags
            if title:
                payload["title"] = title

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self.base_url}/api/generate/v2/",
                json=payload,
                headers=self._headers,
            )
            r.raise_for_status()
            data = r.json()

        clips = data.get("clips", [])
        logger.info("Suno generate: %d clips submitted", len(clips))
        return clips

    async def get_clip(self, clip_id: str) -> dict:
        """Get current status of a clip."""
        self._check_key()
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self.base_url}/api/clip/{clip_id}",
                headers=self._headers,
            )
            r.raise_for_status()
            return r.json()

    async def get_clips(self, clip_ids: list[str]) -> list[dict]:
        """Get status of multiple clips."""
        self._check_key()
        ids_str = ",".join(clip_ids)
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self.base_url}/api/clips/",
                params={"ids": ids_str},
                headers=self._headers,
            )
            r.raise_for_status()
            return r.json()

    async def poll_clip(
        self,
        clip_id: str,
        interval: float = 0,
        timeout: float = 0,
    ) -> dict:
        """Poll a clip until complete or error."""
        interval = interval or SUNO_POLL_INTERVAL
        timeout = timeout or SUNO_POLL_TIMEOUT
        elapsed = 0.0

        while elapsed < timeout:
            clip = await self.get_clip(clip_id)
            status = clip.get("status", "")
            logger.info("Suno clip %s: %s (%.0fs)", clip_id[:8], status, elapsed)

            if status in ("complete", "error"):
                return clip

            await asyncio.sleep(interval)
            elapsed += interval

        raise TimeoutError(f"Suno clip {clip_id} did not complete in {timeout}s")

    async def generate_lyrics(self, prompt: str) -> dict:
        """Generate lyrics from a natural language prompt."""
        self._check_key()
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self.base_url}/api/generate/lyrics/",
                json={"prompt": prompt},
                headers=self._headers,
            )
            r.raise_for_status()
            return r.json()

    async def get_credits(self) -> dict:
        """Get billing/credit info."""
        self._check_key()
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self.base_url}/api/billing/info/",
                headers=self._headers,
            )
            r.raise_for_status()
            return r.json()


# Singleton
_suno_client: Optional[SunoClient] = None


def get_suno_client() -> SunoClient:
    global _suno_client
    if _suno_client is None:
        _suno_client = SunoClient()
    return _suno_client
