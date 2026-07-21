import abc
import json
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.config import settings

logger = logging.getLogger(__name__)


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: List[ToolCall] = []
    finish_reason: Optional[str] = None


class BaseLLMClient(abc.ABC):
    """Abstract interface for LLM providers (OpenAI, Claude, etc.)."""

    @abc.abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        pass


class OpenAILLMClient(BaseLLMClient):
    """OpenAI GPT-4o client with native tool calling."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from openai import AsyncOpenAI
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        tool_calls: List[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
        )


class MockLLMClient(BaseLLMClient):
    """
    Intelligent heuristic fallback client.
    Allows complete qualification flow and adversarial guardrail testing
    without external API keys or network latency.
    """

    def __init__(self):
        logger.info("Using MockLLMClient for offline / testing mode.")

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        last_user_msg = ""
        last_tool_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user" and not last_user_msg:
                last_user_msg = m.get("content", "").strip()
            elif m.get("role") == "tool" and not last_tool_msg:
                last_tool_msg = m.get("content", "").strip()

        msg_lower = last_user_msg.lower()

        # If previous message was a tool result from search_properties
        if last_tool_msg and "search_properties" in str(messages[-1].get("name", "")):
            try:
                props = json.loads(last_tool_msg)
                if props:
                    top = props[0]
                    content = (
                        f"I found a fantastic match for you: {top.get('title')} in {top.get('location')} "
                        f"for ${top.get('price'):,.0f} ({top.get('bhk_config')}). Would you like me to save your details and arrange a viewing?"
                    )
                else:
                    content = "We don't currently have a listing matching those exact criteria, but I can keep your details on file and notify you the moment one hits the market. What's your target moving timeline?"
                return LLMResponse(content=content)
            except Exception:
                pass

        # If previous message was a tool result from save_lead
        if last_tool_msg and "save_lead" in str(messages[-1].get("name", "")):
            return LLMResponse(
                content="Thank you! I have saved your preferences and contact details. One of our advisors will be in touch shortly with detailed listings. Have a wonderful day!"
            )

        # If previous message was a tool result from escalate_to_human
        if last_tool_msg and "escalate_to_human" in str(messages[-1].get("name", "")):
            return LLMResponse(
                content="I have transferred your request to our senior broker team. An agent will connect with you immediately. Have a good day!"
            )

        # Guardrail 1: Demanding human broker or escalation
        if any(w in msg_lower for w in ["human", "real person", "manager", "representative", "broker", "agent right now"]):
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="call_mock_esc",
                        name="escalate_to_human",
                        arguments={"reason": "Caller requested human broker or manager"},
                    )
                ],
                content="I completely understand. I am transferring you directly to one of our senior brokers right away. Please stay on the line.",
            )

        # Guardrail 2: Legal / Tax / Financing guarantees
        if any(w in msg_lower for w in ["guarantee", "tax exempt", "interest rate", "3%", "legal deed", "warranty", "lawsuit"]):
            return LLMResponse(
                content="Placeholder Realty strictly ensures all transactions are compliant, but one of our licensed advisors can go through that with you directly. What area or budget were you thinking of for your home?"
            )

        # Guardrail 3: Off-topic inquiries (weather, sports, politics, recipe)
        if any(w in msg_lower for w in ["weather", "who won", "score", "recipe", "election", "president", "movie"]):
            return LLMResponse(
                content="Haha, that's outside my domain! I'm focused on finding your dream home at Placeholder Realty. What location or property style are you searching for?"
            )

        # Guardrail 4: Impatient caller ("cut the fluff", "hurry up", "quick")
        # Only ask for parameters if user didn't already provide them
        has_bhk = re.search(r"(\d+)\s*(bhk|bed|bedroom)", msg_lower)
        has_budget = re.search(r"(\$?\d+[\d,]*\s*(k|thousand|million|m)?|\d+\s*(lakh|cr))", msg_lower)
        locations = ["downtown", "midtown", "uptown", "west end", "brooklyn heights", "silicon hills", "suburban oaks", "marina bay", "sunnyvale", "cambridge"]
        found_loc = next((loc for loc in locations if loc in msg_lower), None)

        if any(w in msg_lower for w in ["fluff", "hurry", "quick", "cut to the chase", "no small talk"]) and not (has_bhk or has_budget or found_loc):
            return LLMResponse(
                content="Got it, straight to business! Tell me your target location, budget, and bedroom count, and I'll pull available listings immediately."
            )

        # Guardrail 5: Long silence check-in
        if "silence_timeout" in msg_lower or msg_lower == "[silence]":
            return LLMResponse(
                content="Are you still there? Let me know if you can hear me, or feel free to tell me what kind of property you're looking for."
            )

        # Guardrail 6: Hostile / vulgar / pushback
        if any(w in msg_lower for w in ["stupid", "idiot", "hate", "shut up"]):
            return LLMResponse(
                content="I apologize if I caused any frustration. I'm here to help you find real estate listings, or I can connect you with our client relations team."
            )

        # Tool Call Trigger: Search Properties if user mentions location, budget, or BHK
        if has_bhk or has_budget or found_loc or "show me" in msg_lower or "looking for" in msg_lower or "what" in msg_lower:
            budget_val = 800000.0
            if "50" in msg_lower or "50k" in msg_lower:
                budget_val = 50000.0
            elif "100" in msg_lower or "100k" in msg_lower:
                budget_val = 100000.0
            elif "300" in msg_lower or "280" in msg_lower:
                budget_val = 300000.0
            elif "450" in msg_lower or "400" in msg_lower:
                budget_val = 450000.0
            elif "600" in msg_lower:
                budget_val = 600000.0
            elif "700" in msg_lower or "750" in msg_lower:
                budget_val = 750000.0
            elif "million" in msg_lower or "1.5" in msg_lower:
                budget_val = 1500000.0

            bhk_val = "3 BHK"
            if "1" in msg_lower:
                bhk_val = "1 BHK"
            elif "2" in msg_lower:
                bhk_val = "2 BHK"
            elif "4" in msg_lower:
                bhk_val = "4 BHK"
            elif "5" in msg_lower:
                bhk_val = "5 BHK"

            loc_val = found_loc.title() if found_loc else "Downtown"
            if "moon" in msg_lower:
                loc_val = "Moon"

            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="call_mock_search",
                        name="search_properties",
                        arguments={
                            "location": loc_val,
                            "budget_max": budget_val,
                            "bhk": bhk_val,
                        },
                    )
                ]
            )

        # Lead saving trigger: if caller provides name, phone or confirms saving
        if any(w in msg_lower for w in ["my name is", "yes please", "save", "contact me", "phone", "email", "john", "sarah", "alex"]):
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="call_mock_save",
                        name="save_lead",
                        arguments={
                            "name": "Sarah Connor" if "sarah" in msg_lower else "John Doe",
                            "phone": "+15559876543",
                            "budget_min": 500000.0,
                            "budget_max": 800000.0,
                            "preferred_location": "Downtown",
                            "bhk_preference": "3 BHK",
                            "timeline": "3 months",
                            "financing_status": "Pre-approved",
                        },
                    )
                ]
            )

        # Standard conversational opening / fallback
        if not messages or len(messages) <= 2:
            return LLMResponse(
                content="Hello! This is Riya with Placeholder Realty. How can I help with your property search today?"
            )

        return LLMResponse(
            content="That sounds great! What price range are you comfortable with, and when are you looking to make a move?"
        )


def get_llm_client() -> BaseLLMClient:
    """Factory returning OpenAILLMClient if API key is provided, else MockLLMClient."""
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip() and not settings.OPENAI_API_KEY.startswith("your_"):
        return OpenAILLMClient()
    return MockLLMClient()
