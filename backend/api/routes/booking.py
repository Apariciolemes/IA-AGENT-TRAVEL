from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import structlog

from database.db import get_db
from schemas.flight import BookingRequest, BookingResponse, AncillariesRequest
from services.booking_service import BookingService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/booking/hold", response_model=BookingResponse)
async def hold_booking(
    booking_req: BookingRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Hold a booking (if supported by provider) or generate deeplink for checkout.

    This endpoint attempts to hold/reserve the offer. If the provider doesn't
    support holding, it returns a deeplink URL for the user to complete booking
    on the provider's website.
    """
    trace_id = request.state.trace_id
    logger.info(
        "hold_booking_request",
        offer_id=booking_req.offer_id,
        passengers_count=len(booking_req.passengers),
        trace_id=trace_id
    )

    try:
        booking_service = BookingService(db)
        result = await booking_service.hold_or_create_booking(booking_req, trace_id)

        logger.info(
            "hold_booking_response",
            booking_id=result.booking_id,
            status=result.status,
            has_deeplink=result.deeplink_url is not None,
            trace_id=trace_id
        )

        return result

    except Exception as e:
        logger.error("hold_booking_error", error=str(e), trace_id=trace_id)
        raise HTTPException(status_code=500, detail=f"Hold booking failed: {str(e)}")


@router.post("/booking/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: int,
    payment_details: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Confirm a held booking with payment details.

    Only applicable when the provider supports booking API.
    For deeplink flows, the user completes payment on the provider's site.
    """
    trace_id = request.state.trace_id
    logger.info("confirm_booking_request", booking_id=booking_id, trace_id=trace_id)

    try:
        booking_service = BookingService(db)
        result = await booking_service.confirm_booking(booking_id, payment_details, trace_id)

        logger.info(
            "confirm_booking_response",
            booking_id=result.booking_id,
            status=result.status,
            pnr=result.pnr,
            trace_id=trace_id
        )

        return result

    except Exception as e:
        logger.error("confirm_booking_error", error=str(e), trace_id=trace_id)
        raise HTTPException(status_code=500, detail=f"Confirm booking failed: {str(e)}")


@router.post("/booking/ancillaries")
async def add_ancillaries(
    ancillaries_req: AncillariesRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Add ancillaries (seats, baggage) to a booking.

    Supports both booking_id (for our internal bookings) and PNR
    (for bookings completed on provider sites).
    """
    trace_id = request.state.trace_id
    logger.info(
        "add_ancillaries_request",
        booking_id=ancillaries_req.booking_id,
        pnr=ancillaries_req.pnr,
        has_seats=ancillaries_req.seats is not None,
        has_baggage=ancillaries_req.baggage is not None,
        trace_id=trace_id
    )

    try:
        booking_service = BookingService(db)
        result = await booking_service.add_ancillaries(ancillaries_req, trace_id)

        logger.info("add_ancillaries_response", success=True, trace_id=trace_id)

        return result

    except Exception as e:
        logger.error("add_ancillaries_error", error=str(e), trace_id=trace_id)
        raise HTTPException(status_code=500, detail=f"Add ancillaries failed: {str(e)}")


@router.get("/booking/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Retrieve booking details by booking ID.
    """
    trace_id = request.state.trace_id
    logger.info("get_booking_request", booking_id=booking_id, trace_id=trace_id)

    try:
        booking_service = BookingService(db)
        result = await booking_service.get_booking(booking_id)

        if not result:
            raise HTTPException(status_code=404, detail="Booking not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_booking_error", error=str(e), trace_id=trace_id)
        raise HTTPException(status_code=500, detail=f"Get booking failed: {str(e)}")


@router.get("/booking/reference/{booking_reference}", response_model=BookingResponse)
async def get_booking_by_reference(
    booking_reference: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Retrieve booking details by booking reference.
    """
    trace_id = request.state.trace_id
    logger.info("get_booking_by_reference", reference=booking_reference, trace_id=trace_id)

    try:
        booking_service = BookingService(db)
        result = await booking_service.get_booking_by_reference(booking_reference)

        if not result:
            raise HTTPException(status_code=404, detail="Booking not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_booking_by_reference_error", error=str(e), trace_id=trace_id)
        raise HTTPException(status_code=500, detail=f"Get booking failed: {str(e)}")
