from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    CORS_ALLOW_ORIGINS: str = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,https://eventrelay.vercel.app",
    )
    CORS_ALLOW_ORIGIN_REGEX: str | None = os.getenv(
        "CORS_ALLOW_ORIGIN_REGEX",
        r"https://.*\.vercel\.app",
    )

    @property
    def cors_allow_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOW_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def cors_allow_origin_regex(self) -> str | None:
        return self.CORS_ALLOW_ORIGIN_REGEX or None


settings = Settings()
