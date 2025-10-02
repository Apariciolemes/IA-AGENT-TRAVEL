from typing import List
from datetime import datetime, timedelta
import uuid
import structlog

from providers.base_provider import BaseProvider
from schemas.flight import SearchParams, Offer, Segment, CashPrice, OfferType, CabinClass
from config import settings

logger = structlog.get_logger()


class DuffelProvider(BaseProvider):
    """
    Duffel API provider for cash offers (NDC aggregator).

    This is a STUB implementation that returns mock data.
    Real implementation would use Duffel's REST API.

    Docs: https://duffel.com/docs/api
    """

    def __init__(self):
        self.api_key = settings.DUFFEL_API_KEY
        self.base_url = "https://api.duffel.com"

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def search_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        """
        Search for cash offers via Duffel API (STUB).

        In production, this would:
        1. Call POST /air/offer_requests with search params
        2. Poll for results or use webhook
        3. Transform Duffel's offer format to our Offer schema
        """
        if not self.is_available():
            logger.warning("duffel_not_configured", trace_id=trace_id)
            return []

        logger.info(
            "duffel_search_mock",
            origin=params.origin,
            destination=params.destination,
            trace_id=trace_id
        )

        # Mock data
        mock_offers = []

        # Generate 2-3 mock offers
        base_price = 45000  # R$ 450.00
        for i in range(2):
            offer_id = f"duffel_{uuid.uuid4().hex[:12]}"

            # Create segments
            segments = self._create_mock_segments(params, i == 0)

            # Calculate duration
            total_duration = sum(seg.duration_minutes for seg in segments)
            if len(segments) > 1:
                # Add connection time
                total_duration += (len(segments) - 1) * 60

            offer = Offer(
                id=offer_id,
                source="duffel",
                offer_type=OfferType.CASH,
                cabin=params.cabin,
                cash=CashPrice(
                    currency="BRL",
                    amount_cents=base_price + (i * 5000)
                ),
                baggage_included=True if i == 1 else False,
                segments=segments,
                out_date=params.out_date,
                ret_date=params.ret_date,
                total_duration_minutes=total_duration,
                stops_count=len(segments) - 1,
                ancillaries_available=True,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=6)
            )

            mock_offers.append(offer)

        logger.info("duffel_mock_complete", count=len(mock_offers), trace_id=trace_id)
        return mock_offers

    def _create_mock_segments(self, params: SearchParams, direct: bool) -> List[Segment]:
        """Create mock flight segments"""
        segments = []

        if direct:
            # Direct flight
            depart = datetime.combine(params.out_date, datetime.min.time()).replace(hour=8, minute=30)
            duration = 180  # 3 hours

            segments.append(Segment(
                carrier="LA",
                flight_number="3261",
                origin=params.origin,
                destination=params.destination,
                depart=depart,
                arrive=depart + timedelta(minutes=duration),
                duration_minutes=duration,
                fare_class="Y",
                equipment="A321"
            ))
        else:
            # Flight with connection
            depart1 = datetime.combine(params.out_date, datetime.min.time()).replace(hour=6, minute=15)
            duration1 = 120

            segments.append(Segment(
                carrier="G3",
                flight_number="1842",
                origin=params.origin,
                destination="CGH",
                depart=depart1,
                arrive=depart1 + timedelta(minutes=duration1),
                duration_minutes=duration1,
                fare_class="Y",
                equipment="737"
            ))

            # Connection
            depart2 = depart1 + timedelta(minutes=duration1 + 75)  # 75 min layover
            duration2 = 150

            segments.append(Segment(
                carrier="G3",
                flight_number="1567",
                origin="CGH",
                destination=params.destination,
                depart=depart2,
                arrive=depart2 + timedelta(minutes=duration2),
                duration_minutes=duration2,
                fare_class="Y",
                equipment="737"
            ))

        # Add return flights if round-trip
        if params.ret_date:
            if direct:
                depart = datetime.combine(params.ret_date, datetime.min.time()).replace(hour=18, minute=0)
                duration = 180

                segments.append(Segment(
                    carrier="LA",
                    flight_number="3262",
                    origin=params.destination,
                    destination=params.origin,
                    depart=depart,
                    arrive=depart + timedelta(minutes=duration),
                    duration_minutes=duration,
                    fare_class="Y",
                    equipment="A321"
                ))
            else:
                # Return with connection
                depart1 = datetime.combine(params.ret_date, datetime.min.time()).replace(hour=16, minute=30)
                duration1 = 150

                segments.append(Segment(
                    carrier="G3",
                    flight_number="1568",
                    origin=params.destination,
                    destination="CGH",
                    depart=depart1,
                    arrive=depart1 + timedelta(minutes=duration1),
                    duration_minutes=duration1,
                    fare_class="Y",
                    equipment="737"
                ))

                depart2 = depart1 + timedelta(minutes=duration1 + 60)
                duration2 = 120

                segments.append(Segment(
                    carrier="G3",
                    flight_number="1843",
                    origin="CGH",
                    destination=params.origin,
                    depart=depart2,
                    arrive=depart2 + timedelta(minutes=duration2),
                    duration_minutes=duration2,
                    fare_class="Y",
                    equipment="737"
                ))

        return segments
