from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import structlog
import uuid

from database.db import get_db
from schemas.chat import ChatRequest, ChatResponse
from agents.travel_agent import TravelAgent

router = APIRouter()
logger = structlog.get_logger()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_req: ChatRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Conversational endpoint for the travel agent.

    The agent understands natural language queries about flights
    and can search for offers, compare prices, and help with booking.

    Example messages:
    - "Quero voar de GRU para REC no dia 12 de novembro"
    - "Mostre opções em milhas também"
    - "Qual a mais barata?"
    - "Reservar a opção 2"
    """
    trace_id = chat_req.trace_id or request.state.trace_id
    conversation_id = chat_req.conversation_id or str(uuid.uuid4())

    logger.info(
        "chat_request",
        conversation_id=conversation_id,
        message_preview=chat_req.message[:100],
        trace_id=trace_id
    )

    try:
        # Initialize travel agent
        agent = TravelAgent(db=db, trace_id=trace_id)

        # Process message
        response = await agent.process_message(
            message=chat_req.message,
            conversation_id=conversation_id,
            history=chat_req.history
        )

        logger.info(
            "chat_response",
            conversation_id=conversation_id,
            has_offers=response.offers is not None,
            needs_clarification=response.needs_clarification,
            trace_id=trace_id
        )

        return response

    except Exception as e:
        logger.error("chat_error", error=str(e), trace_id=trace_id)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/chat/conversations/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    request: Request
):
    """
    Retrieve conversation history (for future implementation with user sessions).
    """
    trace_id = request.state.trace_id
    logger.info("get_conversation", conversation_id=conversation_id, trace_id=trace_id)

    # TODO: Implement conversation storage and retrieval
    return {
        "conversation_id": conversation_id,
        "messages": [],
        "message": "Conversation history not yet implemented"
    }
