from sqlalchemy.orm import Session
from typing import List
import structlog
import json
import uuid

from schemas.chat import ChatMessage, ChatResponse
from schemas.flight import SearchParams, Pax, CabinClass
from services.search_service import SearchService
from services.pricing_engine import PricingEngine
from services.booking_service import BookingService
from agents.llm_client import LLMClient
from agents.tools import TravelTools

logger = structlog.get_logger()


class TravelAgent:
    """
    Conversational travel agent using LLM with function calling.

    This agent:
    1. Understands natural language queries
    2. Extracts search parameters
    3. Calls appropriate tools (search, compare, book)
    4. Responds in natural Portuguese
    """

    def __init__(self, db: Session, trace_id: str):
        self.db = db
        self.trace_id = trace_id
        self.llm_client = LLMClient()
        self.tools = TravelTools(db, trace_id)
        self.search_service = SearchService(db)
        self.pricing_engine = PricingEngine()
        self.booking_service = BookingService(db)

        # Conversation state (in production, store in Redis or database)
        self.state = {}

    async def process_message(
        self,
        message: str,
        conversation_id: str,
        history: List[ChatMessage]
    ) -> ChatResponse:
        """Process user message and return agent response"""

        logger.info(
            "agent_processing",
            conversation_id=conversation_id,
            message_length=len(message),
            trace_id=self.trace_id
        )

        try:
            # Build system prompt
            system_prompt = self._build_system_prompt()

            # Build conversation history
            messages = [{"role": "system", "content": system_prompt}]
            for msg in history[-5:]:  # Keep last 5 messages for context
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            messages.append({"role": "user", "content": message})

            # Get LLM response with function calling
            llm_response = await self.llm_client.chat_completion(
                messages=messages,
                tools=self.tools.get_tool_definitions()
            )

            # Check if LLM wants to call a function
            if llm_response.get("function_call"):
                # Execute function
                function_result = await self._execute_function(
                    llm_response["function_call"]
                )

                # Get final response from LLM with function result
                messages.append({
                    "role": "assistant",
                    "content": llm_response.get("content"),
                    "function_call": llm_response["function_call"]
                })
                messages.append({
                    "role": "function",
                    "name": llm_response["function_call"]["name"],
                    "content": json.dumps(function_result)
                })

                final_response = await self.llm_client.chat_completion(
                    messages=messages
                )

                response_content = final_response.get("content", "")
                offers = function_result.get("offers") if isinstance(function_result, dict) else None

            else:
                # Direct response without function call
                response_content = llm_response.get("content", "")
                offers = None

            # Check if clarification is needed
            needs_clarification = self._check_needs_clarification(response_content)
            missing_fields = self._extract_missing_fields(response_content)

            # Suggest actions
            suggested_actions = self._suggest_actions(response_content, offers)

            return ChatResponse(
                message=response_content,
                conversation_id=conversation_id,
                offers=offers,
                suggested_actions=suggested_actions,
                needs_clarification=needs_clarification,
                missing_fields=missing_fields,
                trace_id=self.trace_id
            )

        except Exception as e:
            logger.error("agent_error", error=str(e), trace_id=self.trace_id)
            return ChatResponse(
                message="Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                conversation_id=conversation_id,
                trace_id=self.trace_id
            )

    def _build_system_prompt(self) -> str:
        """Build system prompt for the agent"""
        return """Você é um agente de viagens sênior especializado em encontrar as melhores ofertas de voos.

Você fala português do Brasil de forma natural, profissional e amigável.

SUAS CAPACIDADES:
- Buscar voos em dinheiro e em milhas (Smiles, LATAM Pass, TudoAzul)
- Comparar preços e recomendar melhores opções
- Ajudar com reservas e emissão de bilhetes
- Explicar políticas de bagagem, remarcação e cancelamento

INSTRUÇÕES:
1. Sempre peça confirmação de: origem, destino, datas (ida e opcional volta), número de passageiros
2. Se faltar alguma informação, pergunte de forma natural
3. Ao buscar voos, consulte SEMPRE dinheiro E milhas
4. Apresente no máximo 5 opções, ordenadas por melhor custo-benefício
5. Explique claramente: preço/milhas + taxas, duração, escalas, bagagem
6. Para emissão, tente criar booking; se não for possível, gere deeplink e explique o passo-a-passo
7. Seja transparente sobre limitações (ex: "não tenho disponibilidade em tempo real")
8. NUNCA invente disponibilidade ou preços

FORMATO DE RESPOSTA:
- Use listas e bullet points para clareza
- Destaque as melhores ofertas
- Seja conciso mas informativo

FERRAMENTAS DISPONÍVEIS:
- search_flights: Buscar voos em dinheiro e milhas
- compare_offers: Comparar ofertas específicas
- hold_booking: Criar reserva ou deeplink
- add_ancillaries: Adicionar assentos/bagagem

Use as ferramentas quando apropriado. Se o usuário pedir para buscar voos, chame search_flights.
Se pedir para reservar, chame hold_booking.
"""

    async def _execute_function(self, function_call: dict):
        """Execute tool/function called by LLM"""
        function_name = function_call["name"]
        arguments = json.loads(function_call["arguments"])

        logger.info(
            "executing_function",
            function=function_name,
            trace_id=self.trace_id
        )

        if function_name == "search_flights":
            return await self.tools.search_flights(arguments)
        elif function_name == "compare_offers":
            return await self.tools.compare_offers(arguments)
        elif function_name == "hold_booking":
            return await self.tools.hold_booking(arguments)
        elif function_name == "add_ancillaries":
            return await self.tools.add_ancillaries(arguments)
        else:
            return {"error": f"Unknown function: {function_name}"}

    def _check_needs_clarification(self, response: str) -> bool:
        """Check if agent needs clarification from user"""
        clarification_keywords = [
            "qual", "quando", "quantos", "confirme", "preciso saber",
            "me diga", "informe", "pode confirmar"
        ]
        return any(keyword in response.lower() for keyword in clarification_keywords)

    def _extract_missing_fields(self, response: str) -> List[str]:
        """Extract missing fields from response"""
        missing = []
        if "origem" in response.lower():
            missing.append("origin")
        if "destino" in response.lower():
            missing.append("destination")
        if "data" in response.lower():
            missing.append("date")
        if "passageiro" in response.lower():
            missing.append("passengers")
        return missing if missing else None

    def _suggest_actions(self, response: str, offers: List) -> List[str]:
        """Suggest quick action buttons for user"""
        suggestions = []

        if offers:
            suggestions.extend([
                "Mostrar mais detalhes",
                "Buscar com outras datas",
                "Ver opções só em milhas"
            ])
        elif "origem" in response.lower() or "destino" in response.lower():
            suggestions.extend([
                "GRU → REC",
                "GRU → SSA",
                "GRU → FOR"
            ])

        return suggestions if suggestions else None
