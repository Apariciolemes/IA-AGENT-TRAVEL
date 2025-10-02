from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import date, datetime
from enum import Enum


class CabinClass(str, Enum):
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


class OfferType(str, Enum):
    CASH = "cash"
    MILES = "miles"


class MilesProgram(str, Enum):
    SMILES = "smiles"
    LATAM_PASS = "latam_pass"
    TUDO_AZUL = "tudoazul"
    AZUL_FIDELIDADE = "azul_fidelidade"


class Pax(BaseModel):
    adults: int = Field(ge=1, le=9, default=1)
    children: int = Field(ge=0, le=9, default=0)
    infants: int = Field(ge=0, le=9, default=0)

    @field_validator("infants")
    @classmethod
    def validate_infants(cls, v, info):
        if "adults" in info.data and v > info.data["adults"]:
            raise ValueError("Number of infants cannot exceed number of adults")
        return v


class SearchParams(BaseModel):
    origin: str = Field(min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    destination: str = Field(min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    out_date: date
    ret_date: Optional[date] = None
    pax: Pax = Pax()
    cabin: CabinClass = CabinClass.ECONOMY
    bag_included: bool = True
    flexible_days: int = Field(ge=0, le=3, default=0)
    direct_only: bool = False
    max_price_cents: Optional[int] = None
    preferred_programs: Optional[list[MilesProgram]] = None

    @field_validator("ret_date")
    @classmethod
    def validate_return_date(cls, v, info):
        if v and "out_date" in info.data and v < info.data["out_date"]:
            raise ValueError("Return date must be after departure date")
        return v


class Segment(BaseModel):
    carrier: str = Field(min_length=2, max_length=2)
    flight_number: str
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    depart: datetime
    arrive: datetime
    duration_minutes: int
    fare_class: str
    equipment: Optional[str] = None
    operating_carrier: Optional[str] = None


class CashPrice(BaseModel):
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    amount_cents: int = Field(gt=0)

    @property
    def amount(self) -> float:
        return self.amount_cents / 100


class MilesPrice(BaseModel):
    program: MilesProgram
    points: int = Field(gt=0)
    taxes_cents: int = Field(ge=0)

    @property
    def taxes(self) -> float:
        return self.taxes_cents / 100


class Offer(BaseModel):
    id: str
    source: str
    offer_type: OfferType
    cabin: CabinClass

    cash: Optional[CashPrice] = None
    miles: Optional[MilesPrice] = None

    baggage_included: bool
    segments: list[Segment]
    out_date: date
    ret_date: Optional[date] = None
    total_duration_minutes: int
    stops_count: int

    fare_rules: Optional[dict] = None
    ancillaries_available: bool = False

    deeplink_url: Optional[str] = None

    score: Optional[float] = None
    score_explanation: Optional[str] = None

    created_at: datetime
    expires_at: datetime


class RankedOffersResponse(BaseModel):
    ranked: list[Offer]
    assumptions: dict = {
        "r_per_mile": 0.03,
        "max_stops": 1
    }
    cached: bool = False
    cache_age_minutes: Optional[int] = None


class CompareRequest(BaseModel):
    offers: list[Offer]
    user_prefs: Optional[dict] = None


class BookingStatus(str, Enum):
    PENDING = "pending"
    HELD = "held"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PassengerData(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Literal["M", "F", "X"]
    document_type: Literal["passport", "cpf", "rg"]
    document_number: str
    nationality: str = "BR"


class BookingRequest(BaseModel):
    offer_id: str
    passengers: list[PassengerData]
    contact_email: str
    contact_phone: str
    payment_method: Optional[str] = None


class SeatSelection(BaseModel):
    segment_index: int
    seat_number: str
    passenger_index: int
    price_cents: Optional[int] = None


class BaggageSelection(BaseModel):
    segment_index: int
    passenger_index: int
    pieces: int = Field(ge=1, le=3)
    weight_kg: int = Field(ge=23, le=32)
    price_cents: Optional[int] = None


class AncillariesRequest(BaseModel):
    booking_id: Optional[int] = None
    pnr: Optional[str] = None
    seats: Optional[list[SeatSelection]] = None
    baggage: Optional[list[BaggageSelection]] = None


class BookingResponse(BaseModel):
    booking_id: int
    booking_reference: str
    status: BookingStatus
    pnr: Optional[str] = None
    deeplink_url: Optional[str] = None
    instructions: Optional[str] = None
    offer: Offer
