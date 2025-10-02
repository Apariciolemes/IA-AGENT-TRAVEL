from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import structlog
import uuid

from schemas.flight import (
    BookingRequest, BookingResponse, AncillariesRequest,
    BookingStatus, Offer
)
from services.search_service import SearchService

logger = structlog.get_logger()


class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.search_service = SearchService(db)

    async def hold_or_create_booking(
        self,
        booking_req: BookingRequest,
        trace_id: str
    ) -> BookingResponse:
        """
        Hold a booking or generate deeplink.

        For MVP, this creates a booking record and generates a deeplink
        for the user to complete on the provider's website.
        """
        try:
            # Get offer details
            offer = await self.search_service.get_offer_by_id(booking_req.offer_id)
            if not offer:
                raise ValueError(f"Offer {booking_req.offer_id} not found or expired")

            # Generate booking reference
            booking_reference = self._generate_booking_reference()

            # Generate deeplink
            deeplink = self._generate_deeplink(offer, booking_req)

            # Create booking record
            query = text("""
                INSERT INTO bookings (
                    booking_reference, offer_id, status, passenger_data,
                    contact_email, contact_phone, payment_method, deeplink_url
                ) VALUES (
                    :booking_reference, :offer_id, :status, :passenger_data,
                    :contact_email, :contact_phone, :payment_method, :deeplink_url
                )
                RETURNING id
            """)

            result = self.db.execute(query, {
                "booking_reference": booking_reference,
                "offer_id": offer.id,
                "status": BookingStatus.PENDING.value,
                "passenger_data": [p.model_dump(mode='json') for p in booking_req.passengers],
                "contact_email": booking_req.contact_email,
                "contact_phone": booking_req.contact_phone,
                "payment_method": booking_req.payment_method,
                "deeplink_url": deeplink
            })

            booking_id = result.fetchone()[0]
            self.db.commit()

            logger.info(
                "booking_created",
                booking_id=booking_id,
                booking_reference=booking_reference,
                trace_id=trace_id
            )

            return BookingResponse(
                booking_id=booking_id,
                booking_reference=booking_reference,
                status=BookingStatus.PENDING,
                deeplink_url=deeplink,
                instructions=self._get_booking_instructions(offer),
                offer=offer
            )

        except Exception as e:
            self.db.rollback()
            logger.error("booking_creation_error", error=str(e), trace_id=trace_id)
            raise

    async def confirm_booking(
        self,
        booking_id: int,
        payment_details: dict,
        trace_id: str
    ) -> BookingResponse:
        """
        Confirm a held booking (for v1 with real provider integration).
        For MVP, this is a stub.
        """
        try:
            # Update booking status
            query = text("""
                UPDATE bookings
                SET status = :status, payment_status = :payment_status, updated_at = NOW()
                WHERE id = :booking_id
                RETURNING booking_reference, offer_id
            """)

            result = self.db.execute(query, {
                "booking_id": booking_id,
                "status": BookingStatus.CONFIRMED.value,
                "payment_status": "completed"
            })

            row = result.fetchone()
            if not row:
                raise ValueError(f"Booking {booking_id} not found")

            self.db.commit()

            booking_reference = row[0]
            offer_id = row[1]
            offer = await self.search_service.get_offer_by_id(offer_id)

            logger.info(
                "booking_confirmed",
                booking_id=booking_id,
                booking_reference=booking_reference,
                trace_id=trace_id
            )

            return BookingResponse(
                booking_id=booking_id,
                booking_reference=booking_reference,
                status=BookingStatus.CONFIRMED,
                pnr=f"MOCK{booking_reference[:6]}",  # Mock PNR
                offer=offer
            )

        except Exception as e:
            self.db.rollback()
            logger.error("booking_confirmation_error", error=str(e), trace_id=trace_id)
            raise

    async def add_ancillaries(
        self,
        ancillaries_req: AncillariesRequest,
        trace_id: str
    ) -> dict:
        """
        Add seats and baggage to a booking (stub for MVP).
        """
        try:
            if ancillaries_req.booking_id:
                # Update booking with ancillaries
                query = text("""
                    UPDATE bookings
                    SET selected_seats = :seats,
                        selected_baggage = :baggage,
                        updated_at = NOW()
                    WHERE id = :booking_id
                """)

                self.db.execute(query, {
                    "booking_id": ancillaries_req.booking_id,
                    "seats": [s.model_dump(mode='json') for s in ancillaries_req.seats] if ancillaries_req.seats else None,
                    "baggage": [b.model_dump(mode='json') for b in ancillaries_req.baggage] if ancillaries_req.baggage else None
                })

                self.db.commit()

                logger.info(
                    "ancillaries_added",
                    booking_id=ancillaries_req.booking_id,
                    has_seats=ancillaries_req.seats is not None,
                    has_baggage=ancillaries_req.baggage is not None,
                    trace_id=trace_id
                )

                return {
                    "success": True,
                    "message": "Ancillaries added successfully (simulated)",
                    "instructions": "Para confirmar assentos e bagagem, complete a reserva no site da companhia aérea usando o link fornecido."
                }

            else:
                # PNR-based ancillaries (not implemented in MVP)
                return {
                    "success": False,
                    "message": "PNR-based ancillaries not yet implemented",
                    "instructions": "Por favor, adicione assentos e bagagem diretamente no site da companhia aérea."
                }

        except Exception as e:
            self.db.rollback()
            logger.error("add_ancillaries_error", error=str(e), trace_id=trace_id)
            raise

    async def get_booking(self, booking_id: int) -> Optional[BookingResponse]:
        """Retrieve booking by ID"""
        try:
            query = text("""
                SELECT b.*, o.id as offer_id
                FROM bookings b
                JOIN offers o ON b.offer_id = o.id
                WHERE b.id = :booking_id
            """)

            result = self.db.execute(query, {"booking_id": booking_id})
            row = result.fetchone()

            if row:
                offer = await self.search_service.get_offer_by_id(row.offer_id)

                return BookingResponse(
                    booking_id=row.id,
                    booking_reference=row.booking_reference,
                    status=BookingStatus(row.status),
                    pnr=row.pnr,
                    deeplink_url=row.deeplink_url,
                    offer=offer
                )

        except Exception as e:
            logger.error("get_booking_error", error=str(e))

        return None

    async def get_booking_by_reference(self, booking_reference: str) -> Optional[BookingResponse]:
        """Retrieve booking by reference"""
        try:
            query = text("""
                SELECT b.id
                FROM bookings b
                WHERE b.booking_reference = :booking_reference
            """)

            result = self.db.execute(query, {"booking_reference": booking_reference})
            row = result.fetchone()

            if row:
                return await self.get_booking(row.id)

        except Exception as e:
            logger.error("get_booking_by_reference_error", error=str(e))

        return None

    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference"""
        return f"TA{uuid.uuid4().hex[:8].upper()}"

    def _generate_deeplink(self, offer: Offer, booking_req: BookingRequest) -> str:
        """
        Generate deeplink to complete booking on provider's website.
        This is a simplified stub - real implementation would use provider-specific URLs.
        """
        origin = offer.segments[0].origin
        destination = offer.segments[-1].destination
        out_date = offer.out_date.strftime("%Y-%m-%d")
        ret_date = offer.ret_date.strftime("%Y-%m-%d") if offer.ret_date else ""

        # Example deeplinks (these would be real provider URLs)
        if offer.source == "latam_pass":
            base_url = "https://www.latampass.com/pt_br/fly"
            return f"{base_url}?origin={origin}&destination={destination}&outbound={out_date}&inbound={ret_date}"

        elif offer.source == "smiles":
            base_url = "https://www.smiles.com.br/emission"
            return f"{base_url}?origin={origin}&destination={destination}&departure={out_date}&return={ret_date}"

        elif offer.source == "tudoazul":
            base_url = "https://www.tudoazul.com/voe-com-pontos"
            return f"{base_url}?from={origin}&to={destination}&outDate={out_date}&retDate={ret_date}"

        else:
            # Generic OTA/airline link
            base_url = "https://www.google.com/flights"
            return f"{base_url}?hl=pt-BR#flt={origin}.{destination}.{out_date}"

    def _get_booking_instructions(self, offer: Offer) -> str:
        """Get booking instructions based on offer source"""
        if offer.offer_type.value == "miles":
            return (
                f"1. Clique no link para acessar o site da {offer.source}\n"
                f"2. Faça login na sua conta de milhas\n"
                f"3. Confirme os dados do voo e passageiros\n"
                f"4. Pague as taxas de embarque\n"
                f"5. Receba seu código de reserva (PNR) por e-mail"
            )
        else:
            return (
                f"1. Clique no link para acessar o site da companhia/agência\n"
                f"2. Confirme os dados do voo\n"
                f"3. Preencha os dados dos passageiros\n"
                f"4. Escolha assentos e bagagem adicional (se desejar)\n"
                f"5. Efetue o pagamento\n"
                f"6. Receba seu bilhete por e-mail"
            )
