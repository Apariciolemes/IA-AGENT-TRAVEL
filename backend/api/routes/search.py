from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog

from database.db import get_db, get_redis
from schemas.flight import SearchParams, RankedOffersResponse, CompareRequest
from services.search_service import SearchService
from services.pricing_engine import PricingEngine

router = APIRouter()
logger = structlog.get_logger()


@router.post("/search", response_model=RankedOffersResponse)
async def search_flights(
    params: SearchParams,
    request: Request,
    force_live: bool = False,
    db: Session = Depends(get_db)
):
    """
    Search for flights in both cash and miles.
    Returns ranked offers based on effective cost.

    - **origin**: IATA code (3 letters)
    - **destination**: IATA code (3 letters)
    - **out_date**: Departure date (YYYY-MM-DD)
    - **ret_date**: Return date (optional, for round-trip)
    - **pax**: Passenger counts
    - **cabin**: Cabin class
    - **bag_included**: Filter for baggage included
    - **force_live**: Skip cache and search in real-time
    """
    trace_id = request.state.trace_id
    logger.info(
        "search_request",
        origin=params.origin,
        destination=params.destination,
        out_date=str(params.out_date),
        force_live=force_live,
        trace_id=trace_id
    )

    try:
        search_service = SearchService(db)
        pricing_engine = PricingEngine()

        # Check cache first unless force_live is True
        if not force_live:
            cached_offers = await search_service.get_cached_offers(params)
            if cached_offers:
                logger.info("cache_hit", trace_id=trace_id, offers_count=len(cached_offers))
                ranked = pricing_engine.rank_offers(cached_offers, params)
                return RankedOffersResponse(
                    ranked=ranked[:5],
                    cached=True,
                    cache_age_minutes=search_service.get_cache_age_minutes(params)
                )

        # Execute live search
        logger.info("executing_live_search", trace_id=trace_id)

        # Search cash offers
        cash_offers = await search_service.search_cash_offers(params, trace_id)
        logger.info("cash_search_complete", count=len(cash_offers), trace_id=trace_id)

        # Search miles offers
        miles_offers = await search_service.search_miles_offers(params, trace_id)
        logger.info("miles_search_complete", count=len(miles_offers), trace_id=trace_id)

        # Combine and rank
        all_offers = cash_offers + miles_offers
        if not all_offers:
            raise HTTPException(status_code=404, detail="No offers found for the specified criteria")

        ranked = pricing_engine.rank_offers(all_offers, params)

        # Cache results
        await search_service.cache_offers(params, all_offers)

        return RankedOffersResponse(
            ranked=ranked[:5],
            cached=False,
            assumptions={
                "r_per_mile": pricing_engine.r_per_mile,
                "max_stops": pricing_engine.max_stops
            }
        )

    except Exception as e:
        logger.error("search_error", error=str(e), trace_id=trace_id)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/compare", response_model=RankedOffersResponse)
async def compare_offers(
    compare_req: CompareRequest,
    request: Request
):
    """
    Compare specific offers with custom user preferences.
    Returns re-ranked offers based on preferences.
    """
    trace_id = request.state.trace_id
    logger.info("compare_request", offers_count=len(compare_req.offers), trace_id=trace_id)

    try:
        pricing_engine = PricingEngine(user_prefs=compare_req.user_prefs)
        ranked = pricing_engine.rank_offers(compare_req.offers)

        return RankedOffersResponse(
            ranked=ranked,
            assumptions={
                "r_per_mile": pricing_engine.r_per_mile,
                "max_stops": pricing_engine.max_stops
            }
        )

    except Exception as e:
        logger.error("compare_error", error=str(e), trace_id=trace_id)
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/offers/{offer_id}")
async def get_offer_details(
    offer_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific offer.
    """
    trace_id = request.state.trace_id
    logger.info("get_offer_details", offer_id=offer_id, trace_id=trace_id)

    try:
        search_service = SearchService(db)
        offer = await search_service.get_offer_by_id(offer_id)

        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found or expired")

        return offer

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_offer_error", error=str(e), trace_id=trace_id)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve offer: {str(e)}")
