"""
Database seed script for Real Estate Lead Qualification Voice Agent.
Populates at least 20 realistic property listings across diverse budgets, locations,
and BHK configurations. Can be rerun to reset or update demo data.
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import delete
from backend.database import sync_engine, SyncSessionLocal, Base
from backend.models import Property, Lead, Conversation
from backend.seed_data import SAMPLE_PROPERTIES, SAMPLE_LEADS


def seed_database(reset: bool = True):
    """Creates tables if necessary and populates sample properties and leads."""
    print("Creating tables if not present...")
    Base.metadata.create_all(bind=sync_engine)

    with SyncSessionLocal() as session:
        if reset:
            print("Resetting existing properties, leads, and conversations...")
            session.execute(delete(Conversation))
            session.execute(delete(Lead))
            session.execute(delete(Property))
            session.commit()

        print(f"Seeding {len(SAMPLE_PROPERTIES)} properties...")
        for prop_data in SAMPLE_PROPERTIES:
            prop = Property(**prop_data)
            session.add(prop)

        print(f"Seeding {len(SAMPLE_LEADS)} buyer leads with call transcripts...")
        for item in SAMPLE_LEADS:
            lead_data = item["lead"]
            conv_data = item["conversation"]
            lead_obj = Lead(**lead_data)
            session.add(lead_obj)
            session.flush()

            conv_obj = Conversation(
                lead_id=lead_obj.id,
                duration_seconds=conv_data.get("duration_seconds", 60),
                outcome=conv_data.get("outcome", "qualified"),
                summary=conv_data.get("summary", ""),
                transcript=conv_data.get("transcript", []),
            )
            session.add(conv_obj)

        session.commit()
        print(f"Successfully seeded {len(SAMPLE_PROPERTIES)} properties and {len(SAMPLE_LEADS)} leads!")


if __name__ == "__main__":
    seed_database(reset=True)
