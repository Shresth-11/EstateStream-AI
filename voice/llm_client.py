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
        # Bounded latency: a voice caller can't wait on default 10-minute timeouts.
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=20.0, max_retries=2)

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        # Internal history tags tool results with "name" (the mock uses it);
        # strip it so the payload matches the Chat Completions tool-message schema.
        clean_messages = [
            {k: v for k, v in m.items() if not (m.get("role") == "tool" and k == "name")}
            for m in messages
        ]
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": clean_messages,
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
        if any(w in msg_lower for w in ESCALATION_PHRASES):
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
                content="EstateStream AI strictly ensures all transactions are compliant, but one of our licensed advisors can go through that with you directly. What area or budget were you thinking of for your home?"
            )

        # Guardrail 3: Off-topic inquiries (weather, sports, politics, recipe)
        if any(w in msg_lower for w in ["weather", "who won", "score", "recipe", "election", "president", "movie"]):
            return LLMResponse(
                content="Haha, that's outside my domain! I'm focused on finding your dream home at EstateStream AI. What location or property style are you searching for?"
            )

        bhk_val = parse_bhk(msg_lower)
        budget_val = parse_budget(msg_lower)
        found_loc = next((loc for loc in KNOWN_LOCATIONS if loc in msg_lower), None)
        name_val = parse_name(last_user_msg)
        phone_val = parse_phone(last_user_msg)

        # Guardrail 4: Impatient caller with no usable criteria
        if any(w in msg_lower for w in ["fluff", "hurry", "quick", "cut to the chase", "no small talk"]) and not (bhk_val or budget_val or found_loc):
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

        # Lead capture takes priority over search: a phone number is not a budget.
        if name_val or phone_val or any(w in msg_lower for w in ["yes please", "save my", "contact me", "call me"]):
            prefs = _collect_preferences(messages)
            args = {k: v for k, v in {
                "name": name_val,
                "phone": phone_val,
                "budget_max": prefs.get("budget_max"),
                "preferred_location": prefs.get("location"),
                "bhk_preference": prefs.get("bhk"),
                "timeline": parse_timeline(msg_lower) or prefs.get("timeline"),
            }.items() if v}
            if not args.get("name"):
                args["name"] = "Prospective Buyer"
            return LLMResponse(tool_calls=[ToolCall(id="call_mock_save", name="save_lead", arguments=args)])

        # Search when the caller gives at least one concrete criterion.
        absurd_loc = "Moon" if "moon" in msg_lower else None
        if bhk_val or budget_val or found_loc or absurd_loc:
            args = {}
            if found_loc or absurd_loc:
                args["location"] = absurd_loc or found_loc.title()
            if budget_val:
                args["budget_max"] = budget_val
            if bhk_val:
                args["bhk"] = bhk_val
            return LLMResponse(tool_calls=[ToolCall(id="call_mock_search", name="search_properties", arguments=args)])

        # Standard conversational opening / fallback
        if not messages or len(messages) <= 2:
            return LLMResponse(
                content="Hello! This is Riya with EstateStream AI. How can I help with your property search today?"
            )

        return LLMResponse(
            content="That sounds great! What price range are you comfortable with, and when are you looking to make a move?"
        )


# --- Mock parsing helpers (offline mode only) ---

ESCALATION_PHRASES = [
    "human", "real person", "manager", "representative", "speak to a broker",
    "talk to a broker", "human broker", "agent right now", "speak to someone", "talk to someone",
]

KNOWN_LOCATIONS = [
    "downtown", "midtown", "uptown", "west end", "brooklyn heights", "silicon hills", "suburban oaks",
    "marina bay", "sunnyvale", "cambridge", "financial district", "lakeside", "old town", "riverfront",
]

_WORD_NUMS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def parse_bhk(text: str) -> Optional[str]:
    m = re.search(r"\b(\d|one|two|three|four|five|six)\s*-?\s*(bhk|bed|bedroom|br)\b", text)
    if not m:
        return None
    n = m.group(1)
    n = _WORD_NUMS.get(n, n)
    return f"{n} BHK"


def parse_budget(text: str) -> Optional[float]:
    """Parses '$450k', '800,000', '$1.5 million', '1.2m'. Ignores BHK counts and phone numbers."""
    t = re.sub(r"\+?\d[\d\s\-().]{8,}\d", " ", text)  # drop phone numbers first
    t = t.replace(",", "")
    m = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(million|mil|m|k|thousand)\b", t)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        return val * (1_000_000 if unit in ("million", "mil", "m") else 1_000)
    m = re.search(r"\$\s*(\d{4,9})(?!\d)", t) or re.search(r"(?<![\d+])(\d{5,7})(?!\d)", t)
    if m:
        return float(m.group(1))
    return None


def parse_phone(text: str) -> Optional[str]:
    m = re.search(r"(\+?\d[\d\s\-().]{8,}\d)", text)
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    return ("+" if m.group(1).startswith("+") else "") + digits if len(digits) >= 10 else None


def parse_name(text: str) -> Optional[str]:
    m = re.search(r"(?:my name is|my name's|this is|i am|i'm)\s+([A-Za-z]+(?:\s+[A-Z][a-z]+)?)", text, re.IGNORECASE)
    if not m:
        return None
    name = m.group(1).strip()
    stop = {"looking", "interested", "not", "a", "an", "just", "calling", "here", "in", "searching",
            "planning", "thinking", "trying", "after", "from", "still", "the", "ready", "buying", "moving"}
    if name.split()[0].lower() in stop:
        return None
    # Drop a trailing non-name word captured by the optional second group (e.g. "Priya and")
    parts = [p for p in name.split() if p.lower() not in stop and p.lower() not in {"and", "my", "on", "at"}]
    name = " ".join(parts)
    if not name:
        return None
    return " ".join(p.capitalize() for p in name.split())


def parse_timeline(text: str) -> Optional[str]:
    m = re.search(r"(immediately|asap|right away|next year|this year|\d+\s*(?:months?|weeks?|years?))", text)
    return m.group(1) if m else None


def _collect_preferences(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Pulls the most recent search criteria the caller mentioned earlier in the call."""
    prefs: Dict[str, Any] = {}
    for m in messages:
        if m.get("role") != "user":
            continue
        t = (m.get("content") or "").lower()
        prefs["bhk"] = parse_bhk(t) or prefs.get("bhk")
        prefs["budget_max"] = parse_budget(t) or prefs.get("budget_max")
        prefs["location"] = next((l.title() for l in KNOWN_LOCATIONS if l in t), None) or prefs.get("location")
        prefs["timeline"] = parse_timeline(t) or prefs.get("timeline")
    return prefs


def get_llm_client() -> BaseLLMClient:
    """Factory returning OpenAILLMClient if API key is provided, else MockLLMClient."""
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip() and not settings.OPENAI_API_KEY.startswith("your_"):
        return OpenAILLMClient()
    return MockLLMClient()
