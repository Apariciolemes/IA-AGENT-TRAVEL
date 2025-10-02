from typing import List
from datetime import datetime, timedelta
import uuid
import structlog

from providers.base_provider import BaseProvider
from schemas.flight import SearchParams, Offer, Segment, MilesPrice, OfferType, MilesProgram
from config import settings

logger = structlog.get_logger()


class SmilesProvider(BaseProvider):
    """
    Smiles (Gol) loyalty program provider.

    This STUB returns mock miles offers.
    Real implementation would either:
    1. Use official API if available (preferred)
    2. Use controlled scraping with Playwright (respecting ToS)

    Note: Scraping should only be used if no API is available and
    within legal/ToS boundaries.
    """

    def is_available(self) -> bool:
        return settings.SCRAPING_ENABLED

    async def search_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        if not self.is_available():
            return []

        logger.info(
            "smiles_search_mock",
            origin=params.origin,
            destination=params.destination,
            trace_id=trace_id
        )

        # Mock miles offer
        offer_id = f"smiles_{uuid.uuid4().hex[:12]}"

        # Direct flight segment
        depart = datetime.combine(params.out_date, datetime.min.time()).replace(hour=10, minute=45)
        duration = 175

        segments = [
            Segment(
                carrier="G3",
                flight_number="1234",
                origin=params.origin,
                destination=params.destination,
                depart=depart,
                arrive=depart + timedelta(minutes=duration),
                duration_minutes=duration,
                fare_class="S",
                equipment="737"
            )
        ]

        # Add return if round-trip
        if params.ret_date:
            ret_depart = datetime.combine(params.ret_date, datetime.min.time()).replace(hour=14, minute=20)
            segments.append(
                Segment(
                    carrier="G3",
                    flight_number="1235",
                    origin=params.destination,
                    destination=params.origin,
                    depart=ret_depart,
                    arrive=ret_depart + timedelta(minutes=duration),
                    duration_minutes=duration,
                    fare_class="S",
                    equipment="737"
                )
            )

        total_duration = sum(s.duration_minutes for s in segments)

        offer = Offer(
            id=offer_id,
            source="smiles",
            offer_type=OfferType.MILES,
            cabin=params.cabin,
            miles=MilesPrice(
                program=MilesProgram.SMILES,
                points=15000 if params.ret_date else 7500,
                taxes_cents=12800  # R$ 128.00
            ),
            baggage_included=True,
            segments=segments,
            out_date=params.out_date,
            ret_date=params.ret_date,
            total_duration_minutes=total_duration,
            stops_count=0,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=4)
        )

        logger.info("smiles_mock_complete", trace_id=trace_id)
        return [offer]
