from typing import List
from datetime import datetime, timedelta
import uuid
import structlog

from providers.base_provider import BaseProvider
from schemas.flight import SearchParams, Offer, Segment, MilesPrice, OfferType, MilesProgram
from config import settings

logger = structlog.get_logger()


class TudoAzulProvider(BaseProvider):
    """TudoAzul (Azul) loyalty program provider (STUB)"""

    def is_available(self) -> bool:
        return settings.SCRAPING_ENABLED

    async def search_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        if not self.is_available():
            return []

        logger.info("tudoazul_search_mock", trace_id=trace_id)

        offer_id = f"tudoazul_{uuid.uuid4().hex[:12]}"

        depart = datetime.combine(params.out_date, datetime.min.time()).replace(hour=7, minute=30)
        duration = 185

        segments = [
            Segment(
                carrier="AD",
                flight_number="4567",
                origin=params.origin,
                destination=params.destination,
                depart=depart,
                arrive=depart + timedelta(minutes=duration),
                duration_minutes=duration,
                fare_class="L",
                equipment="A320neo"
            )
        ]

        if params.ret_date:
            ret_depart = datetime.combine(params.ret_date, datetime.min.time()).replace(hour=19, minute=15)
            segments.append(
                Segment(
                    carrier="AD",
                    flight_number="4568",
                    origin=params.destination,
                    destination=params.origin,
                    depart=ret_depart,
                    arrive=ret_depart + timedelta(minutes=duration),
                    duration_minutes=duration,
                    fare_class="L",
                    equipment="A320neo"
                )
            )

        total_duration = sum(s.duration_minutes for s in segments)

        offer = Offer(
            id=offer_id,
            source="tudoazul",
            offer_type=OfferType.MILES,
            cabin=params.cabin,
            miles=MilesPrice(
                program=MilesProgram.TUDO_AZUL,
                points=16000 if params.ret_date else 8000,
                taxes_cents=14200
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

        return [offer]
