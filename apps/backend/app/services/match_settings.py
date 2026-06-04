from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.settings_service import get_org_settings

MATCH_PRESETS: dict[str, float] = {
    "high_security": 0.80,
    "balanced": 0.70,
    "convenience": 0.65,
}


async def get_effective_match_threshold(db: AsyncSession | None = None) -> float:
    settings = get_settings()
    if db is not None:
        org = await get_org_settings(db)
        if org.match_threshold is not None:
            return float(org.match_threshold)
        if org.match_threshold_preset and org.match_threshold_preset in MATCH_PRESETS:
            return MATCH_PRESETS[org.match_threshold_preset]
    return settings.match_threshold
