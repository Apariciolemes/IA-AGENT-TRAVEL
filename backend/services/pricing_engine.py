from typing import List, Optional
import structlog

from schemas.flight import Offer, SearchParams, OfferType
from config import settings

logger = structlog.get_logger()


class PricingEngine:
    def __init__(self, user_prefs: Optional[dict] = None):
        self.r_per_mile = settings.R_PER_MILE
        self.max_stops = settings.MAX_STOPS
        self.price_weight = settings.PRICE_WEIGHT
        self.duration_weight = settings.DURATION_WEIGHT
        self.stops_weight = settings.STOPS_WEIGHT
        self.ancillary_weight = settings.ANCILLARY_WEIGHT

        # Override with user preferences if provided
        if user_prefs:
            self.r_per_mile = user_prefs.get("r_per_mile", self.r_per_mile)
            self.max_stops = user_prefs.get("max_stops", self.max_stops)
            self.price_weight = user_prefs.get("price_weight", self.price_weight)
            self.duration_weight = user_prefs.get("duration_weight", self.duration_weight)
            self.stops_weight = user_prefs.get("stops_weight", self.stops_weight)

    def rank_offers(
        self,
        offers: List[Offer],
        params: Optional[SearchParams] = None
    ) -> List[Offer]:
        """
        Rank offers based on effective cost, duration, stops, and ancillaries.
        Returns sorted list with scores and explanations.
        """
        if not offers:
            return []

        # Calculate scores
        scored_offers = []
        for offer in offers:
            score, explanation = self._calculate_score(offer, params)
            offer.score = score
            offer.score_explanation = explanation
            scored_offers.append(offer)

        # Sort by score (higher is better)
        ranked = sorted(scored_offers, key=lambda x: x.score, reverse=True)

        logger.info(
            "offers_ranked",
            total_offers=len(ranked),
            top_score=ranked[0].score if ranked else None
        )

        return ranked

    def _calculate_score(
        self,
        offer: Offer,
        params: Optional[SearchParams] = None
    ) -> tuple[float, str]:
        """
        Calculate composite score for an offer.
        Returns (score, explanation) where score is 0-1 (higher is better).
        """
        # 1. Price component (normalized, inverted so lower price = higher score)
        effective_price = self._get_effective_price_brl(offer)
        price_score = self._normalize_price_score(effective_price)

        # 2. Duration component (normalized, inverted)
        duration_score = self._normalize_duration_score(offer.total_duration_minutes)

        # 3. Stops component (fewer stops = higher score)
        stops_score = 1.0 if offer.stops_count == 0 else (0.5 if offer.stops_count == 1 else 0.2)

        # 4. Ancillaries component
        ancillary_score = 1.0 if offer.baggage_included else 0.5

        # Apply filters from params
        if params:
            # Direct flights only
            if params.direct_only and offer.stops_count > 0:
                return (0.0, "Descartado: voo com escalas (filtro 'somente diretos')")

            # Max price filter
            if params.max_price_cents and effective_price > params.max_price_cents / 100:
                return (0.0, f"Descartado: preço efetivo R$ {effective_price:.2f} excede máximo")

            # Baggage filter
            if params.bag_included and not offer.baggage_included:
                return (0.0, "Descartado: bagagem não incluída")

        # Weighted composite score
        composite_score = (
            self.price_weight * price_score +
            self.duration_weight * duration_score +
            self.stops_weight * stops_score +
            self.ancillary_weight * ancillary_score
        )

        # Generate explanation
        explanation = self._generate_explanation(
            offer, effective_price, price_score, duration_score, stops_score, ancillary_score
        )

        return (composite_score, explanation)

    def _get_effective_price_brl(self, offer: Offer) -> float:
        """Convert offer to effective price in BRL"""
        if offer.offer_type == OfferType.CASH:
            # Cash offer
            if offer.cash.currency == "BRL":
                return offer.cash.amount
            else:
                # TODO: Add currency conversion
                return offer.cash.amount  # Assuming BRL for now

        elif offer.offer_type == OfferType.MILES:
            # Miles offer: convert to BRL using R$/mile rate + taxes
            miles_value_brl = offer.miles.points * self.r_per_mile
            taxes_brl = offer.miles.taxes
            return miles_value_brl + taxes_brl

        return float('inf')

    def _normalize_price_score(self, price_brl: float) -> float:
        """
        Normalize price to 0-1 score (lower price = higher score).
        Using typical range R$ 200 - R$ 2000 for domestic flights.
        """
        min_price = 200
        max_price = 2000

        if price_brl <= min_price:
            return 1.0
        elif price_brl >= max_price:
            return 0.1
        else:
            # Linear interpolation, inverted
            normalized = 1.0 - ((price_brl - min_price) / (max_price - min_price))
            return max(0.1, normalized)

    def _normalize_duration_score(self, duration_minutes: int) -> float:
        """
        Normalize duration to 0-1 score (shorter = higher score).
        Using typical range 60 min - 600 min for domestic flights.
        """
        min_duration = 60
        max_duration = 600

        if duration_minutes <= min_duration:
            return 1.0
        elif duration_minutes >= max_duration:
            return 0.1
        else:
            # Linear interpolation, inverted
            normalized = 1.0 - ((duration_minutes - min_duration) / (max_duration - min_duration))
            return max(0.1, normalized)

    def _generate_explanation(
        self,
        offer: Offer,
        effective_price: float,
        price_score: float,
        duration_score: float,
        stops_score: float,
        ancillary_score: float
    ) -> str:
        """Generate human-readable explanation of the score"""
        reasons = []

        # Price
        if offer.offer_type == OfferType.CASH:
            reasons.append(f"Preço R$ {effective_price:.2f}")
        else:
            reasons.append(
                f"{offer.miles.points:,} milhas "
                f"({offer.miles.program.value}) + R$ {offer.miles.taxes:.2f} taxas "
                f"(~R$ {effective_price:.2f} valor efetivo)"
            )

        # Duration & stops
        hours = offer.total_duration_minutes // 60
        minutes = offer.total_duration_minutes % 60
        duration_str = f"{hours}h{minutes:02d}m"

        if offer.stops_count == 0:
            reasons.append(f"voo direto, duração {duration_str}")
        else:
            reasons.append(f"{offer.stops_count} escala(s), duração total {duration_str}")

        # Baggage
        if offer.baggage_included:
            reasons.append("bagagem incluída")
        else:
            reasons.append("bagagem não incluída")

        # Top scorer indicators
        if price_score > 0.8:
            reasons.insert(0, "MELHOR PREÇO")
        if stops_score == 1.0 and duration_score > 0.7:
            reasons.insert(0, "VÔO DIRETO E RÁPIDO")

        return " | ".join(reasons)
