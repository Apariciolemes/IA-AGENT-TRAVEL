from typing import List, Dict, Optional
import structlog
import json
from config import settings

logger = structlog.get_logger()


class LLMClient:
    """
    Unified LLM client supporting multiple providers (OpenAI, Anthropic, Azure).
    Configurable via environment variables.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL

        if self.provider == "openai":
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.provider == "anthropic":
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        elif self.provider == "azure":
            from openai import AsyncAzureOpenAI
            self.client = AsyncAzureOpenAI(
                api_key=settings.OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
        elif self.provider == "ollama":
            from openai import AsyncOpenAI
            # Ollama usa API compatível com OpenAI
            self.client = AsyncOpenAI(
                base_url=settings.OLLAMA_BASE_URL,
                api_key="ollama"  # Ollama não precisa de key real
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        logger.info("llm_client_initialized", provider=self.provider, model=self.model)

    async def chat_completion(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7
    ) -> Dict:
        """
        Get chat completion from LLM.

        Returns:
            {
                "content": str,
                "function_call": {
                    "name": str,
                    "arguments": str (JSON)
                } (optional)
            }
        """
        try:
            if self.provider in ["openai", "azure", "ollama"]:
                return await self._openai_completion(messages, tools, temperature)
            elif self.provider == "anthropic":
                return await self._anthropic_completion(messages, tools, temperature)

        except Exception as e:
            logger.error("llm_error", error=str(e), provider=self.provider)
            raise

    async def _openai_completion(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]],
        temperature: float
    ) -> Dict:
        """OpenAI-compatible completion"""
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**params)
        message = response.choices[0].message

        result = {
            "content": message.content or ""
        }

        # Check for function call
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            result["function_call"] = {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments
            }

        return result

    async def _anthropic_completion(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]],
        temperature: float
    ) -> Dict:
        """Anthropic Claude completion"""
        # Extract system message
        system_message = None
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                filtered_messages.append(msg)

        params = {
            "model": self.model,
            "messages": filtered_messages,
            "temperature": temperature,
            "max_tokens": 2048
        }

        if system_message:
            params["system"] = system_message

        if tools:
            # Convert OpenAI tool format to Anthropic format
            params["tools"] = self._convert_tools_to_anthropic(tools)

        response = await self.client.messages.create(**params)

        result = {
            "content": ""
        }

        # Parse response content
        for block in response.content:
            if block.type == "text":
                result["content"] += block.text
            elif block.type == "tool_use":
                result["function_call"] = {
                    "name": block.name,
                    "arguments": json.dumps(block.input)
                }

        return result

    def _convert_tools_to_anthropic(self, tools: List[Dict]) -> List[Dict]:
        """Convert OpenAI tool format to Anthropic format"""
        anthropic_tools = []
        for tool in tools:
            if tool["type"] == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                })
        return anthropic_tools
