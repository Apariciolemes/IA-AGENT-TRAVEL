from typing import List
import structlog
from providers.base_provider import BaseProvider
from schemas.flight import SearchParams, Offer
from config import settings

logger = structlog.get_logger()


class KiwiProvider(BaseProvider):
    """
    Kiwi (Tequila) API provider (STUB).

    Real implementation: https://tequila.kiwi.com/portal/docs
    """

    def __init__(self):
        self.api_key = settings.KIWI_API_KEY

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def search_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        if not self.is_available():
            return []

        logger.info("kiwi_search_stub", trace_id=trace_id)
        # Stub: return empty for now
        return []
