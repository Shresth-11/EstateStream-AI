"""
Interactive CLI for Real Estate Lead Qualification Voice Agent.
Allows testing the full qualification conversation and function calling in text.
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import AsyncSessionLocal
from backend.services.conversation_service import create_conversation, generate_llm_summary
from backend.models import ConversationOutcome
from voice.agent import AgentSession


async def run_cli_session():
    print("=" * 65)
    print("  Placeholder Realty - Lead Qualification Agent (CLI Mode)")
    print("  Persona: Riya | Type 'exit' or 'quit' to conclude call.")
    print("=" * 65)

    session_id = f"cli-{int(time.time())}"
    agent = AgentSession(session_id=session_id, caller_name="CLI Tester", caller_phone="+15551234567")

    start_time = time.time()
    greeting = await agent.get_initial_greeting()
    print(f"\nRiya: {greeting}")

    async with AsyncSessionLocal() as db:
        while True:
            try:
                user_text = input("\nYou: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nCall interrupted.")
                break

            if not user_text:
                continue

            if user_text.lower() in ["exit", "quit", "bye", "hang up"]:
                print("\nEnding call...")
                break

            result = await agent.process_user_turn(user_text, db)

            if result["tools_called"]:
                for tc in result["tools_called"]:
                    print(f"  [🔧 Tool Invoked: {tc['name']}({tc['arguments']})]")
                    if tc["name"] == "search_properties":
                        matches = tc["result"]
                        print(f"    ↳ Found {len(matches)} matching property listings in database.")
                    elif tc["name"] == "save_lead":
                        print(f"    ↳ Lead persisted into database: {tc['result']}")
                    elif tc["name"] == "escalate_to_human":
                        print(f"    ↳ Escalation triggered: {tc['result']}")

            print(f"\nRiya: {result['reply']}")

            if result["call_ended"]:
                print("\n[Call naturally concluded]")
                break

        # Call wrap-up & post-call persistence
        duration = int(time.time() - start_time)
        transcript = agent.get_transcript()
        print("\n" + "-" * 50)
        print("Generating Post-Call Summary & Storing Records...")
        
        summary_info = await generate_llm_summary(transcript)
        outcome = ConversationOutcome.QUALIFIED.value if agent.captured_lead else ConversationOutcome.INCOMPLETE.value
        if agent.escalated:
            outcome = ConversationOutcome.ESCALATED.value

        lead_id = agent.captured_lead.id if agent.captured_lead else None
        conv = await create_conversation(
            db=db,
            transcript=transcript,
            lead_id=lead_id,
            summary=summary_info.get("summary"),
            outcome=summary_info.get("outcome", outcome),
            duration_seconds=max(duration, 5),
        )
        await db.commit()

        print(f"Outcome:  {conv.outcome}")
        print(f"Duration: {conv.duration_seconds} seconds")
        print(f"Summary:\n{conv.summary}")
        if agent.captured_lead:
            print(f"Lead ID:  #{agent.captured_lead.id} ({agent.captured_lead.name} - {agent.captured_lead.status})")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(run_cli_session())
