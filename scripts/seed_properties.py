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
from backend.models import Property

SAMPLE_PROPERTIES = [
    {
        "title": "Sunlit Urban Studio Loft",
        "location": "Downtown",
        "price": 280000.0,
        "bhk_config": "1 BHK",
        "description": "Modern open-concept loft with floor-to-ceiling windows, exposed brick, and rapid transit access.",
        "amenities": ["Fitness Center", "Rooftop Terrace", "Bike Storage", "In-unit Laundry", "Pet Friendly"],
    },
    {
        "title": "Midtown Modern High-Rise Apartment",
        "location": "Midtown",
        "price": 420000.0,
        "bhk_config": "2 BHK",
        "description": "Sleek 2-bedroom corner unit with panoramic city skyline views, quartz countertops, and stainless appliances.",
        "amenities": ["24/7 Concierge", "Swimming Pool", "Covered Parking", "Co-working Lounge", "High-speed Internet"],
    },
    {
        "title": "Spacious Downtown Executive Suite",
        "location": "Downtown",
        "price": 550000.0,
        "bhk_config": "2 BHK",
        "description": "Luxurious 2 BHK near corporate hubs and fine dining. Features hardwood flooring and a master ensuite with soaking tub.",
        "amenities": ["24/7 Security", "Gym", "Valet Parking", "Dry Cleaning Service", "Balcony"],
    },
    {
        "title": "Parkside Family Garden Apartment",
        "location": "Uptown",
        "price": 680000.0,
        "bhk_config": "3 BHK",
        "description": "Sprawling 3-bedroom residence facing Central Park. Ideal for families with children and quiet suburban feel within the city.",
        "amenities": ["Children Play Area", "Private Garden Patio", "Reserved Parking", "Storage Locker", "Jogging Track"],
    },
    {
        "title": "West End Contemporary Waterfront Condo",
        "location": "West End",
        "price": 750000.0,
        "bhk_config": "3 BHK",
        "description": "Breathtaking waterfront views with oversized terrace, chef's kitchen, wine cooler, and designer finishes.",
        "amenities": ["Marina Access", "Infinity Pool", "Sauna & Steam", "EV Charging Station", "Clubhouse"],
    },
    {
        "title": "Silicon Hills Tech Corridor Smart Home",
        "location": "Silicon Hills",
        "price": 820000.0,
        "bhk_config": "3 BHK",
        "description": "Fully integrated smart home with solar panels, automated lighting, climate control, and home office nook.",
        "amenities": ["Smart Home Automation", "Solar Power", "High-speed Fiber", "2-Car Garage", "Private Backyard"],
    },
    {
        "title": "Suburban Oaks Luxury Estate",
        "location": "Suburban Oaks",
        "price": 950000.0,
        "bhk_config": "4 BHK",
        "description": "Spacious 4 BHK family villa on a half-acre lot featuring an expansive backyard, home theater room, and dual master suites.",
        "amenities": ["Private Swimming Pool", "Home Theater", "Gated Security", "Lush Lawn", "Fireplace"],
    },
    {
        "title": "Financial District Penthouse Haven",
        "location": "Financial District",
        "price": 1450000.0,
        "bhk_config": "4 BHK",
        "description": "Spectacular dual-level penthouse with private elevator access, 360-degree glass walls, and wraparound sky deck.",
        "amenities": ["Private Elevator", "360 Sky Deck", "Wine Cellar", "24/7 Doorman", "Spa Facility"],
    },
    {
        "title": "Marina Bay Coastal Luxury Villa",
        "location": "Marina Bay",
        "price": 1850000.0,
        "bhk_config": "5 BHK",
        "description": "Ultra-luxury waterfront estate with private boat slip, heated infinity pool, and custom outdoor kitchen.",
        "amenities": ["Private Boat Slip", "Heated Pool", "Outdoor Kitchen", "Smart Security", "Staff Quarters"],
    },
    {
        "title": "Skyline Heights Royal Penthouse",
        "location": "Downtown",
        "price": 3200000.0,
        "bhk_config": "5 BHK",
        "description": "The pinnacle of urban elegance. Triplex penthouse featuring private helipad access, marble interiors, and private spa.",
        "amenities": ["Private Helipad", "Private Spa", "Butler Service", "4-Car Covered Garage", "Smart Home Automation"],
    },
    {
        "title": "Old Town Heritage Courtyard Residence",
        "location": "Old Town",
        "price": 390000.0,
        "bhk_config": "2 BHK",
        "description": "Charming colonial-style apartment with restored original woodwork, high ceilings, and landscaped community courtyard.",
        "amenities": ["Central Courtyard", "Antique Fireplace", "Covered Carport", "Library", "Community Garden"],
    },
    {
        "title": "Riverfront Terrace Condo",
        "location": "Riverfront",
        "price": 490000.0,
        "bhk_config": "2 BHK",
        "description": "Peaceful river view apartment with a spacious morning coffee balcony and walking trail right outside your door.",
        "amenities": ["River Trail Access", "Kayak Storage", "Fitness Center", "Barbecue Grills", "Covered Parking"],
    },
    {
        "title": "Cambridge Scholar Garden Flat",
        "location": "Cambridge",
        "price": 340000.0,
        "bhk_config": "1 BHK",
        "description": "Quiet, light-filled 1 BHK adjacent to university campuses and tech research hubs. Perfect for academics and young professionals.",
        "amenities": ["Study Lounge", "High-speed Internet", "Bicycle Parking", "Community Garden", "Security Surveillance"],
    },
    {
        "title": "Sunnyvale Greenbelt Family Residence",
        "location": "Sunnyvale",
        "price": 620000.0,
        "bhk_config": "3 BHK",
        "description": "Eco-friendly 3-bedroom residence with energy-efficient appliances, bamboo flooring, and close proximity to top-rated schools.",
        "amenities": ["LEED Certified", "Children Playground", "Community Solar", "Attached Garage", "Dog Park"],
    },
    {
        "title": "Lakeside Breeze Duplex",
        "location": "Lakeside",
        "price": 710000.0,
        "bhk_config": "3 BHK",
        "description": "Spacious two-level duplex overlooking Lakeview Park, featuring a cathedral ceiling living room and private patio.",
        "amenities": ["Lake View", "Private Patio", "Tennis Court", "Attached 2-Car Garage", "Clubhouse"],
    },
    {
        "title": "Brooklyn Heights Brownstone Suite",
        "location": "Brooklyn Heights",
        "price": 890000.0,
        "bhk_config": "3 BHK",
        "description": "Refined classic brownstone floor-through with modern European kitchen, crown molding, and private landscaped garden.",
        "amenities": ["Private Garden", "Washer/Dryer", "Original Details", "Fireplace", "Storage Cellar"],
    },
    {
        "title": "Uptown Elegance Boutique Residence",
        "location": "Uptown",
        "price": 580000.0,
        "bhk_config": "2 BHK",
        "description": "Designer 2 BHK in an exclusive 12-unit boutique building with custom cabinetry, radiant floor heating, and quiet tree-lined street.",
        "amenities": ["Radiant Floor Heating", "Private Elevator", "Security Monitoring", "Balcony", "Dedicated Parking"],
    },
    {
        "title": "Silicon Hills Executive Townhouse",
        "location": "Silicon Hills",
        "price": 670000.0,
        "bhk_config": "2 BHK",
        "description": "Modern multi-level townhouse equipped for hybrid work with dual master suites and private rooftop patio.",
        "amenities": ["Rooftop Patio", "EV Ready Garage", "Cat-6 Cabling", "Gated Entry", "Fitness Room"],
    },
    {
        "title": "Downtown Compact Metro Pod",
        "location": "Downtown",
        "price": 240000.0,
        "bhk_config": "1 BHK",
        "description": "Efficient modern micro-apartment with smart multi-functional furniture, steps away from central subway and restaurants.",
        "amenities": ["Concierge", "Lounge", "Laundry Facility", "Bike Share", "24/7 Security"],
    },
    {
        "title": "Suburban Oaks Serene Manor",
        "location": "Suburban Oaks",
        "price": 1150000.0,
        "bhk_config": "4 BHK",
        "description": "Stately 4-bedroom brick manor with grand entryway, gourmet chef's kitchen, swimming pool, and screened sunroom.",
        "amenities": ["Swimming Pool", "Screened Sunroom", "3-Car Garage", "Gourmet Kitchen", "Full Basement"],
    },
    {
        "title": "West End Designer Loft",
        "location": "West End",
        "price": 630000.0,
        "bhk_config": "2 BHK",
        "description": "Industrial chic 2 BHK with 14-foot timber ceilings, polished concrete floors, and custom steel-and-glass partitions.",
        "amenities": ["High Ceilings", "Dog Run", "Fitness Center", "Secured Parking", "Freight Elevator"],
    },
    {
        "title": "Midtown Grand Family Duplex",
        "location": "Midtown",
        "price": 1050000.0,
        "bhk_config": "4 BHK",
        "description": "Expansive 4-bedroom dual-level residence combining prime location with privacy, high security, and premier amenities.",
        "amenities": ["24/7 Doorman", "Indoor Heated Pool", "Kids Club", "Valet Parking", "Fitness Center & Spa"],
    },
]


def seed_database(reset: bool = True):
    """Creates tables if necessary and populates sample properties."""
    print("Creating tables if not present...")
    Base.metadata.create_all(bind=sync_engine)

    with SyncSessionLocal() as session:
        if reset:
            print("Resetting existing properties...")
            session.execute(delete(Property))
            session.commit()

        print(f"Seeding {len(SAMPLE_PROPERTIES)} properties...")
        for prop_data in SAMPLE_PROPERTIES:
            prop = Property(**prop_data)
            session.add(prop)

        session.commit()
        print(f"Successfully seeded {len(SAMPLE_PROPERTIES)} properties into the database!")


if __name__ == "__main__":
    seed_database(reset=True)
