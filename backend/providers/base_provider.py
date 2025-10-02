from abc import ABC, abstractmethod
from typing import List
from schemas.flight import SearchParams, Offer


class BaseProvider(ABC):
    """Base class for all flight providers (APIs and scrapers)"""

    @abstractmethod
    async def search_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        """
        Search for flight offers based on parameters.

        Args:
            params: Search parameters
            trace_id: Trace ID for logging

        Returns:
            List of offers
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is properly configured and available.

        Returns:
            True if provider can be used
        """
        pass
