from typing import List
import structlog
from providers.base_provider import BaseProvider
from schemas.flight import SearchParams, Offer
from config import settings

logger = structlog.get_logger()


class AmadeusProvider(BaseProvider):
    """
    Amadeus Self-Service API provider (STUB).

    Real implementation: https://developers.amadeus.com/self-service/category/flights
    """

    def __init__(self):
        self.api_key = settings.AMADEUS_API_KEY
        self.api_secret = settings.AMADEUS_API_SECRET

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_secret)

    async def search_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        if not self.is_available():
            return []

        logger.info("amadeus_search_stub", trace_id=trace_id)
        # Stub: return empty for now
        return []
