import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from voice.prompts import RIYA_SYSTEM_PROMPT, AGENT_TOOLS_SPEC
from voice.llm_client import BaseLLMClient, ToolCall, get_llm_client
from backend.services.property_service import search_properties
from backend.services.lead_service import save_lead
from backend.models import Lead, ConversationOutcome

logger = logging.getLogger(__name__)


class AgentSession:
    """Manages an active conversational qualification session with Riya."""

    def __init__(
        self,
        session_id: str,
        caller_phone: Optional[str] = None,
        caller_name: Optional[str] = None,
        llm_client: Optional[BaseLLMClient] = None,
    ):
        self.session_id = session_id
        self.caller_phone = caller_phone
        self.caller_name = caller_name
        self.llm_client = llm_client or get_llm_client()
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": RIYA_SYSTEM_PROMPT}
        ]
        self.captured_lead: Optional[Lead] = None
        self.escalated: bool = False
        self.escalation_reason: Optional[str] = None
        self.call_ended: bool = False
        self.silence_count: int = 0

    async def get_initial_greeting(self) -> str:
        """Returns opening greeting from Riya."""
        greeting = "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?"
        self.messages.append({"role": "assistant", "content": greeting})
        return greeting

    async def process_user_turn(
        self,
        user_text: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Executes one full conversation turn:
        - Appends user message
        - Calls LLM with tools
        - Executes any returned tool calls against the database
        - Feeds tool results back to LLM until an assistant message is generated
        - Returns reply, tools called, lead state, and call outcome flags.
        """
        if self.call_ended:
            return {
                "reply": "Thank you for reaching out to EstateStream AI. Have a wonderful day!",
                "tools_called": [],
                "call_ended": True,
                "escalated": self.escalated,
            }

        # Check for silence indicator (empty transcripts count as silence too)
        if not user_text or user_text.strip() in ["", "[silence]", "SILENCE_TIMEOUT"]:
            self.silence_count += 1
            if self.silence_count >= 2:
                self.call_ended = True
                farewell = "It seems we might have lost connection. Thank you for calling EstateStream AI. Goodbye!"
                self.messages.append({"role": "assistant", "content": farewell})
                return {
                    "reply": farewell,
                    "tools_called": [],
                    "call_ended": True,
                    "escalated": False,
                }
            user_text = "[silence]"
        else:
            self.silence_count = 0

        self.messages.append({"role": "user", "content": user_text})

        tools_executed: List[Dict[str, Any]] = []
        max_tool_iterations = 4
        current_iter = 0
        final_reply = ""

        while current_iter < max_tool_iterations:
            current_iter += 1
            # On the last iteration, withhold tools so the model must answer in words.
            offer_tools = AGENT_TOOLS_SPEC if current_iter < max_tool_iterations else None
            try:
                response = await self.llm_client.generate_response(
                    messages=self.messages,
                    tools=offer_tools,
                )
            except Exception as e:
                # A provider error (429, 5xx, bad key, timeout) must not kill the call.
                logger.error(f"LLM call failed in session {self.session_id}: {e}", exc_info=True)
                final_reply = "Sorry, I had a brief connection hiccup on my end. Could you say that again?"
                self.messages.append({"role": "assistant", "content": final_reply})
                break

            # If tool calls were generated
            if response.tool_calls and offer_tools is not None:
                # Append assistant tool invocation message to messages
                assistant_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in response.tool_calls
                    ],
                }
                self.messages.append(assistant_msg)

                for tc in response.tool_calls:
                    try:
                        result_content = await self._execute_tool(tc, db)
                    except Exception as e:
                        logger.error(f"Tool {tc.name} failed: {e}", exc_info=True)
                        try:
                            await db.rollback()
                        except Exception:
                            pass
                        result_content = {"error": f"{tc.name} failed. Apologise briefly and continue without it."}
                    tools_executed.append({
                        "name": tc.name,
                        "arguments": tc.arguments,
                        "result": result_content,
                    })

                    # Append tool message back into conversation
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": json.dumps(result_content, default=str),
                    })
                # Loop again so LLM can synthesize tool results into conversational speech
                continue

            # Assistant plain text response
            final_reply = (response.content or "").strip()
            break

        if not final_reply:
            final_reply = (
                "I've passed your request to a senior broker. Thank you for calling, goodbye!"
                if self.escalated
                else "Could you tell me a bit more about the area and budget you have in mind?"
            )
        if not self.messages or self.messages[-1].get("content") != final_reply:
            self.messages.append({"role": "assistant", "content": final_reply})

        # Check for farewell or closing indicators
        if any(term in final_reply.lower() for term in ["have a wonderful day", "have a great day", "goodbye", "transferring you"]):
            self.call_ended = True

        return {
            "reply": final_reply,
            "tools_called": tools_executed,
            "lead_saved": self.captured_lead.to_dict() if self.captured_lead else None,
            "call_ended": self.call_ended,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
        }

    async def _execute_tool(self, tool_call: ToolCall, db: AsyncSession) -> Any:
        """Executes tool against database or triggers escalation."""
        name = tool_call.name
        args = tool_call.arguments
        logger.info(f"Executing tool {name} with args: {args}")

        if name == "search_properties":
            props = await search_properties(
                db=db,
                location=args.get("location"),
                budget_max=args.get("budget_max"),
                bhk=args.get("bhk"),
                limit=3,
            )
            return props

        elif name == "save_lead":
            # Phone resolution: stated by caller > known caller ID > the lead already
            # created in this session > a per-session placeholder. The old fixed
            # default phone made every browser call overwrite the same lead row.
            phone = (
                args.get("phone")
                or self.caller_phone
                or (self.captured_lead.phone if self.captured_lead else None)
                or f"unknown-{self.session_id}"
            )
            lead = await save_lead(
                db=db,
                name=args.get("name") or self.caller_name or "Prospective Buyer",
                phone=phone,
                budget_min=args.get("budget_min"),
                budget_max=args.get("budget_max"),
                preferred_location=args.get("preferred_location"),
                bhk_preference=args.get("bhk_preference"),
                timeline=args.get("timeline"),
                financing_status=args.get("financing_status"),
            )
            self.captured_lead = lead
            return {"status": "success", "lead_id": lead.id, "message": "Lead details saved successfully."}

        elif name == "escalate_to_human":
            self.escalated = True
            self.escalation_reason = args.get("reason", "Caller requested human broker.")
            self.call_ended = True
            return {
                "status": "escalated",
                "reason": self.escalation_reason,
                "message": "Call marked for immediate human broker handoff.",
            }

        return {"error": f"Unknown tool name: {name}"}

    def get_transcript(self) -> List[Dict[str, Any]]:
        """Returns clean chronological transcript without system prompt."""
        return [
            m for m in self.messages
            if m.get("role") in ["user", "assistant"] and m.get("content")
        ]
