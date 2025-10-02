from sqlalchemy.orm import Session
from typing import Dict, List
import structlog
from datetime import date

from services.search_service import SearchService
from services.pricing_engine import PricingEngine
from services.booking_service import BookingService
from schemas.flight import SearchParams, Pax, CabinClass, BookingRequest, PassengerData

logger = structlog.get_logger()


class TravelTools:
    """
    Tools/functions exposed to the LLM for function calling.
    Each tool performs a specific action and returns structured data.
    """

    def __init__(self, db: Session, trace_id: str):
        self.db = db
        self.trace_id = trace_id
        self.search_service = SearchService(db)
        self.pricing_engine = PricingEngine()
        self.booking_service = BookingService(db)

    def get_tool_definitions(self) -> List[Dict]:
        """Return OpenAI-compatible tool definitions"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_flights",
                    "description": "Buscar voos disponíveis em dinheiro e milhas. Use esta função quando o usuário pedir para buscar voos ou passagens.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "Código IATA do aeroporto de origem (3 letras, ex: GRU)"
                            },
                            "destination": {
                                "type": "string",
                                "description": "Código IATA do aeroporto de destino (3 letras, ex: REC)"
                            },
                            "out_date": {
                                "type": "string",
                                "description": "Data de ida no formato YYYY-MM-DD"
                            },
                            "ret_date": {
                                "type": "string",
                                "description": "Data de volta no formato YYYY-MM-DD (opcional, para ida e volta)"
                            },
                            "adults": {
                                "type": "integer",
                                "description": "Número de adultos (padrão: 1)"
                            },
                            "cabin": {
                                "type": "string",
                                "enum": ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
                                "description": "Classe da cabine (padrão: ECONOMY)"
                            },
                            "bag_included": {
                                "type": "boolean",
                                "description": "Filtrar apenas opções com bagagem incluída (padrão: true)"
                            },
                            "direct_only": {
                                "type": "boolean",
                                "description": "Buscar apenas voos diretos (padrão: false)"
                            }
                        },
                        "required": ["origin", "destination", "out_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "hold_booking",
                    "description": "Criar reserva ou gerar link para finalizar compra. Use quando o usuário quiser reservar ou comprar um voo específico.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "offer_id": {
                                "type": "string",
                                "description": "ID da oferta selecionada"
                            },
                            "passenger_first_name": {
                                "type": "string",
                                "description": "Primeiro nome do passageiro principal"
                            },
                            "passenger_last_name": {
                                "type": "string",
                                "description": "Sobrenome do passageiro principal"
                            },
                            "contact_email": {
                                "type": "string",
                                "description": "E-mail de contato"
                            },
                            "contact_phone": {
                                "type": "string",
                                "description": "Telefone de contato"
                            }
                        },
                        "required": ["offer_id", "contact_email"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_offers",
                    "description": "Comparar ofertas específicas com preferências customizadas do usuário.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "offer_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de IDs de ofertas para comparar"
                            },
                            "prefer_miles": {
                                "type": "boolean",
                                "description": "Preferir ofertas em milhas"
                            },
                            "prefer_direct": {
                                "type": "boolean",
                                "description": "Preferir voos diretos"
                            }
                        },
                        "required": ["offer_ids"]
                    }
                }
            }
        ]

    async def search_flights(self, params: Dict) -> Dict:
        """Execute flight search"""
        try:
            # Parse parameters
            search_params = SearchParams(
                origin=params["origin"].upper(),
                destination=params["destination"].upper(),
                out_date=date.fromisoformat(params["out_date"]),
                ret_date=date.fromisoformat(params["ret_date"]) if params.get("ret_date") else None,
                pax=Pax(adults=params.get("adults", 1)),
                cabin=CabinClass(params.get("cabin", "ECONOMY")),
                bag_included=params.get("bag_included", True),
                direct_only=params.get("direct_only", False)
            )

            logger.info("tool_search_flights", params=params, trace_id=self.trace_id)

            # Search cash offers
            cash_offers = await self.search_service.search_cash_offers(search_params, self.trace_id)

            # Search miles offers
            miles_offers = await self.search_service.search_miles_offers(search_params, self.trace_id)

            # Combine and rank
            all_offers = cash_offers + miles_offers
            ranked = self.pricing_engine.rank_offers(all_offers, search_params)

            # Return top 5
            top_offers = ranked[:5]

            return {
                "success": True,
                "offers": [self._serialize_offer(offer) for offer in top_offers],
                "total_found": len(all_offers)
            }

        except Exception as e:
            logger.error("tool_search_error", error=str(e), trace_id=self.trace_id)
            return {
                "success": False,
                "error": str(e)
            }

    async def hold_booking(self, params: Dict) -> Dict:
        """Create booking or generate deeplink"""
        try:
            # Create minimal passenger data
            passengers = [
                PassengerData(
                    first_name=params.get("passenger_first_name", "Passageiro"),
                    last_name=params.get("passenger_last_name", "Principal"),
                    date_of_birth=date(1990, 1, 1),  # Mock
                    gender="M",
                    document_type="cpf",
                    document_number="00000000000"
                )
            ]

            booking_req = BookingRequest(
                offer_id=params["offer_id"],
                passengers=passengers,
                contact_email=params["contact_email"],
                contact_phone=params.get("contact_phone", "")
            )

            logger.info("tool_hold_booking", offer_id=params["offer_id"], trace_id=self.trace_id)

            result = await self.booking_service.hold_or_create_booking(booking_req, self.trace_id)

            return {
                "success": True,
                "booking_reference": result.booking_reference,
                "status": result.status.value,
                "deeplink_url": result.deeplink_url,
                "instructions": result.instructions
            }

        except Exception as e:
            logger.error("tool_booking_error", error=str(e), trace_id=self.trace_id)
            return {
                "success": False,
                "error": str(e)
            }

    async def compare_offers(self, params: Dict) -> Dict:
        """Compare specific offers"""
        try:
            offer_ids = params["offer_ids"]
            offers = []

            for offer_id in offer_ids:
                offer = await self.search_service.get_offer_by_id(offer_id)
                if offer:
                    offers.append(offer)

            if not offers:
                return {"success": False, "error": "No valid offers found"}

            # Custom preferences
            user_prefs = {}
            if params.get("prefer_miles"):
                user_prefs["r_per_mile"] = 0.02  # Lower value = prefer miles
            if params.get("prefer_direct"):
                user_prefs["stops_weight"] = 0.4  # Higher weight for stops

            pricing_engine = PricingEngine(user_prefs=user_prefs)
            ranked = pricing_engine.rank_offers(offers)

            return {
                "success": True,
                "ranked_offers": [self._serialize_offer(offer) for offer in ranked]
            }

        except Exception as e:
            logger.error("tool_compare_error", error=str(e), trace_id=self.trace_id)
            return {
                "success": False,
                "error": str(e)
            }

    async def add_ancillaries(self, params: Dict) -> Dict:
        """Add seats/baggage (stub)"""
        return {
            "success": True,
            "message": "Ancillaries feature not yet fully implemented in MVP"
        }

    def _serialize_offer(self, offer) -> Dict:
        """Serialize offer for JSON response"""
        return {
            "id": offer.id,
            "source": offer.source,
            "type": offer.offer_type.value,
            "price": {
                "cash": {
                    "amount": offer.cash.amount,
                    "currency": offer.cash.currency
                } if offer.cash else None,
                "miles": {
                    "program": offer.miles.program.value,
                    "points": offer.miles.points,
                    "taxes": offer.miles.taxes
                } if offer.miles else None
            },
            "segments": [
                {
                    "carrier": seg.carrier,
                    "flight_number": seg.flight_number,
                    "from": seg.origin,
                    "to": seg.destination,
                    "depart": seg.depart.isoformat(),
                    "arrive": seg.arrive.isoformat()
                }
                for seg in offer.segments
            ],
            "duration_minutes": offer.total_duration_minutes,
            "stops": offer.stops_count,
            "baggage_included": offer.baggage_included,
            "score": offer.score,
            "explanation": offer.score_explanation
        }
