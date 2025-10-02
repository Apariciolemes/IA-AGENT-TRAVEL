from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional
import json
import hashlib
import structlog

from schemas.flight import SearchParams, Offer, OfferType
from database.db import get_redis
from config import settings
from providers.duffel_provider import DuffelProvider
from providers.amadeus_provider import AmadeusProvider
from providers.kiwi_provider import KiwiProvider

logger = structlog.get_logger()


class SearchService:
    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis()
        self.cache_ttl = settings.CACHE_TTL_MINUTES * 60

    def _generate_cache_key(self, params: SearchParams) -> str:
        """Generate unique cache key for search parameters"""
        key_data = f"{params.origin}:{params.destination}:{params.out_date}:{params.ret_date}:{params.pax.adults}:{params.pax.children}:{params.pax.infants}:{params.cabin}"
        return f"search:{hashlib.md5(key_data.encode()).hexdigest()}"

    async def get_cached_offers(self, params: SearchParams) -> Optional[List[Offer]]:
        """Retrieve cached offers if available and not stale"""
        cache_key = self._generate_cache_key(params)

        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                cached_at = datetime.fromisoformat(data["cached_at"])

                # Check if cache is still fresh
                age_minutes = (datetime.now() - cached_at).total_seconds() / 60
                if age_minutes < settings.LIVE_SEARCH_THRESHOLD_MINUTES:
                    logger.info("cache_hit", cache_key=cache_key, age_minutes=age_minutes)
                    return [Offer(**offer) for offer in data["offers"]]

                logger.info("cache_stale", cache_key=cache_key, age_minutes=age_minutes)

        except Exception as e:
            logger.warning("cache_retrieval_error", error=str(e))

        return None

    async def cache_offers(self, params: SearchParams, offers: List[Offer]):
        """Cache search results"""
        cache_key = self._generate_cache_key(params)

        try:
            cache_data = {
                "cached_at": datetime.now().isoformat(),
                "offers": [offer.model_dump(mode='json') for offer in offers]
            }
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(cache_data))
            logger.info("cache_stored", cache_key=cache_key, offers_count=len(offers))

        except Exception as e:
            logger.warning("cache_storage_error", error=str(e))

    def get_cache_age_minutes(self, params: SearchParams) -> Optional[int]:
        """Get age of cached data in minutes"""
        cache_key = self._generate_cache_key(params)

        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                cached_at = datetime.fromisoformat(data["cached_at"])
                return int((datetime.now() - cached_at).total_seconds() / 60)
        except Exception:
            pass

        return None

    async def search_cash_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        """Search for cash offers from multiple providers"""
        all_offers = []

        # Duffel (NDC aggregator)
        if settings.DUFFEL_API_KEY:
            try:
                duffel = DuffelProvider()
                offers = await duffel.search_offers(params, trace_id)
                all_offers.extend(offers)
                logger.info("duffel_search_complete", count=len(offers), trace_id=trace_id)
            except Exception as e:
                logger.error("duffel_search_error", error=str(e), trace_id=trace_id)

        # Amadeus
        if settings.AMADEUS_API_KEY:
            try:
                amadeus = AmadeusProvider()
                offers = await amadeus.search_offers(params, trace_id)
                all_offers.extend(offers)
                logger.info("amadeus_search_complete", count=len(offers), trace_id=trace_id)
            except Exception as e:
                logger.error("amadeus_search_error", error=str(e), trace_id=trace_id)

        # Kiwi/Tequila
        if settings.KIWI_API_KEY:
            try:
                kiwi = KiwiProvider()
                offers = await kiwi.search_offers(params, trace_id)
                all_offers.extend(offers)
                logger.info("kiwi_search_complete", count=len(offers), trace_id=trace_id)
            except Exception as e:
                logger.error("kiwi_search_error", error=str(e), trace_id=trace_id)

        # Deduplicate offers by hash
        seen_hashes = set()
        unique_offers = []
        for offer in all_offers:
            offer_hash = self._hash_offer(offer)
            if offer_hash not in seen_hashes:
                seen_hashes.add(offer_hash)
                unique_offers.append(offer)

        # Store offers in database
        await self._store_offers_in_db(unique_offers)

        return unique_offers

    async def search_miles_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        """Search for miles offers from loyalty programs"""
        # This will trigger Celery tasks for scraping
        # For MVP, we'll use stubs that return mock data

        from providers.smiles_provider import SmilesProvider
        from providers.latam_provider import LatamPassProvider
        from providers.tudoazul_provider import TudoAzulProvider

        all_offers = []

        # Smiles
        try:
            smiles = SmilesProvider()
            offers = await smiles.search_offers(params, trace_id)
            all_offers.extend(offers)
            logger.info("smiles_search_complete", count=len(offers), trace_id=trace_id)
        except Exception as e:
            logger.error("smiles_search_error", error=str(e), trace_id=trace_id)

        # LATAM Pass
        try:
            latam = LatamPassProvider()
            offers = await latam.search_offers(params, trace_id)
            all_offers.extend(offers)
            logger.info("latam_search_complete", count=len(offers), trace_id=trace_id)
        except Exception as e:
            logger.error("latam_search_error", error=str(e), trace_id=trace_id)

        # TudoAzul
        try:
            tudoazul = TudoAzulProvider()
            offers = await tudoazul.search_offers(params, trace_id)
            all_offers.extend(offers)
            logger.info("tudoazul_search_complete", count=len(offers), trace_id=trace_id)
        except Exception as e:
            logger.error("tudoazul_search_error", error=str(e), trace_id=trace_id)

        # Store offers in database
        await self._store_offers_in_db(all_offers)

        return all_offers

    def _hash_offer(self, offer: Offer) -> str:
        """Generate hash for offer deduplication"""
        segments_hash = hashlib.md5(
            json.dumps([s.model_dump() for s in offer.segments], sort_keys=True).encode()
        ).hexdigest()

        price_hash = ""
        if offer.cash:
            price_hash = f"cash_{offer.cash.amount_cents}"
        elif offer.miles:
            price_hash = f"miles_{offer.miles.program}_{offer.miles.points}"

        return f"{segments_hash}_{price_hash}"

    async def _store_offers_in_db(self, offers: List[Offer]):
        """Store offers in PostgreSQL"""
        try:
            from sqlalchemy import text

            for offer in offers:
                # Insert or update offer
                query = text("""
                    INSERT INTO offers (
                        id, source, offer_type, cabin, currency, price_cents,
                        miles, miles_program, taxes_cents, baggage_included,
                        segments, out_date, ret_date, origin, destination,
                        total_duration_minutes, stops_count, hash, expires_at
                    ) VALUES (
                        :id, :source, :offer_type, :cabin, :currency, :price_cents,
                        :miles, :miles_program, :taxes_cents, :baggage_included,
                        :segments, :out_date, :ret_date, :origin, :destination,
                        :total_duration_minutes, :stops_count, :hash, :expires_at
                    )
                    ON CONFLICT (hash) DO UPDATE SET
                        price_cents = EXCLUDED.price_cents,
                        miles = EXCLUDED.miles,
                        taxes_cents = EXCLUDED.taxes_cents,
                        expires_at = EXCLUDED.expires_at
                """)

                self.db.execute(query, {
                    "id": offer.id,
                    "source": offer.source,
                    "offer_type": offer.offer_type.value,
                    "cabin": offer.cabin.value,
                    "currency": offer.cash.currency if offer.cash else None,
                    "price_cents": offer.cash.amount_cents if offer.cash else None,
                    "miles": offer.miles.points if offer.miles else None,
                    "miles_program": offer.miles.program.value if offer.miles else None,
                    "taxes_cents": offer.miles.taxes_cents if offer.miles else None,
                    "baggage_included": offer.baggage_included,
                    "segments": json.dumps([s.model_dump(mode='json') for s in offer.segments]),
                    "out_date": offer.out_date,
                    "ret_date": offer.ret_date,
                    "origin": offer.segments[0].origin,
                    "destination": offer.segments[-1].destination,
                    "total_duration_minutes": offer.total_duration_minutes,
                    "stops_count": offer.stops_count,
                    "hash": self._hash_offer(offer),
                    "expires_at": offer.expires_at
                })

            self.db.commit()
            logger.info("offers_stored_in_db", count=len(offers))

        except Exception as e:
            self.db.rollback()
            logger.error("db_storage_error", error=str(e))

    async def get_offer_by_id(self, offer_id: str) -> Optional[Offer]:
        """Retrieve offer by ID from database"""
        try:
            from sqlalchemy import text

            query = text("""
                SELECT * FROM offers
                WHERE id = :offer_id AND expires_at > NOW()
            """)

            result = self.db.execute(query, {"offer_id": offer_id}).fetchone()

            if result:
                # Convert to Offer model
                return self._row_to_offer(result)

        except Exception as e:
            logger.error("get_offer_error", error=str(e))

        return None

    def _row_to_offer(self, row) -> Offer:
        """Convert database row to Offer model"""
        from schemas.flight import Segment, CashPrice, MilesPrice, CabinClass, MilesProgram

        segments = [Segment(**s) for s in json.loads(row.segments)]

        offer_data = {
            "id": row.id,
            "source": row.source,
            "offer_type": row.offer_type,
            "cabin": row.cabin,
            "baggage_included": row.baggage_included,
            "segments": segments,
            "out_date": row.out_date,
            "ret_date": row.ret_date,
            "total_duration_minutes": row.total_duration_minutes,
            "stops_count": row.stops_count,
            "created_at": row.created_at,
            "expires_at": row.expires_at
        }

        if row.offer_type == "cash":
            offer_data["cash"] = CashPrice(
                currency=row.currency,
                amount_cents=row.price_cents
            )
        else:
            offer_data["miles"] = MilesPrice(
                program=row.miles_program,
                points=row.miles,
                taxes_cents=row.taxes_cents
            )

        return Offer(**offer_data)
