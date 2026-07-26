"""
Seed data definitions for EstateStream AI.
Provides realistic property listings and buyer lead records with transcripts and call summaries.
"""

from typing import List, Dict, Any

SAMPLE_PROPERTIES: List[Dict[str, Any]] = [
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
        "description": "Sprawling two-level duplex overlooking Lakeview Park, featuring a cathedral ceiling living room and private patio.",
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

SAMPLE_LEADS: List[Dict[str, Any]] = [
    {
        "lead": {
            "name": "Marcus Vance",
            "phone": "+15558889999",
            "budget_min": 600000.0,
            "budget_max": 900000.0,
            "preferred_location": "West End",
            "bhk_preference": "3 BHK",
            "timeline": "Immediate",
            "financing_status": "Cash buyer",
            "status": "qualified",
        },
        "conversation": {
            "duration_seconds": 142,
            "outcome": "qualified",
            "summary": "Marcus is an active cash buyer seeking a luxury 3 BHK condo in West End with a budget up to $900,000. Matched listing 'West End Contemporary Waterfront Condo' ($750k). Full contact details verified. Scheduled in-person broker site visit.",
            "transcript": [
                {"role": "assistant", "content": "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?"},
                {"role": "user", "content": "Hey Riya, I'm looking for a 3 BHK in the West End area, budget around 800k to 900k."},
                {"role": "assistant", "content": "Got it! Let me search our inventory for available 3 BHK properties in West End under $900,000."},
                {"role": "tool", "name": "search_properties", "content": "[{'title': 'West End Contemporary Waterfront Condo', 'price': 750000, 'location': 'West End', 'bhk_config': '3 BHK'}]"},
                {"role": "assistant", "content": "I found a stunning 3 BHK West End Contemporary Waterfront Condo listed at $750,000 with marina access, an infinity pool, and an oversized terrace. Would you like to schedule an in-person viewing?"},
                {"role": "user", "content": "That sounds great! I have cash ready and want to move immediately. My name is Marcus Vance, +15558889999."},
                {"role": "tool", "name": "save_lead", "content": "{'status': 'success', 'lead_id': 1}"},
                {"role": "assistant", "content": "Excellent Marcus! I have saved your details and one of our licensed senior advisors will call you shortly to confirm your private walkthrough."}
            ]
        }
    },
    {
        "lead": {
            "name": "Alice Walker",
            "phone": "+15554321098",
            "budget_min": 400000.0,
            "budget_max": 650000.0,
            "preferred_location": "Midtown",
            "bhk_preference": "2 BHK",
            "timeline": "2 months",
            "financing_status": "Pre-approved",
            "status": "qualified",
        },
        "conversation": {
            "duration_seconds": 98,
            "outcome": "qualified",
            "summary": "Alice is pre-approved for $650,000 looking for a modern 2 BHK in Midtown. Matched 'Midtown Modern High-Rise Apartment' ($420k). Requested virtual tour link.",
            "transcript": [
                {"role": "assistant", "content": "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?"},
                {"role": "user", "content": "Hi Riya, I need a 2 bedroom apartment in Midtown under $650,000."},
                {"role": "assistant", "content": "Let me check available listings in Midtown for you right now."},
                {"role": "tool", "name": "search_properties", "content": "[{'title': 'Midtown Modern High-Rise Apartment', 'price': 420000, 'location': 'Midtown', 'bhk_config': '2 BHK'}]"},
                {"role": "assistant", "content": "We have a 2 BHK Midtown Modern High-Rise corner unit at $420,000 with skyline views and a pool. Are you pre-approved for financing?"},
                {"role": "user", "content": "Yes, fully pre-approved through Chase. Moving in 2 months. My name is Alice Walker, +15554321098."},
                {"role": "tool", "name": "save_lead", "content": "{'status': 'success', 'lead_id': 2}"},
                {"role": "assistant", "content": "Thank you Alice! Your file is qualified and our Midtown specialist will share the virtual tour link."}
            ]
        }
    },
    {
        "lead": {
            "name": "David Kumar",
            "phone": "+15557771234",
            "budget_min": 700000.0,
            "budget_max": 850000.0,
            "preferred_location": "Silicon Hills",
            "bhk_preference": "3 BHK",
            "timeline": "1 month",
            "financing_status": "Pre-approved",
            "status": "needs_followup",
        },
        "conversation": {
            "duration_seconds": 110,
            "outcome": "qualified",
            "summary": "David is relocating for a tech engineering position in Silicon Hills. Seeking a 3 BHK smart home with EV charging. Matched 'Silicon Hills Tech Corridor Smart Home' ($820k). Needs follow-up regarding school district details.",
            "transcript": [
                {"role": "assistant", "content": "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?"},
                {"role": "user", "content": "Hello, I'm relocating to Silicon Hills and need a 3 BHK smart home under 850k within a month."},
                {"role": "assistant", "content": "Welcome to the area! Let me find matching smart homes in Silicon Hills."},
                {"role": "tool", "name": "search_properties", "content": "[{'title': 'Silicon Hills Tech Corridor Smart Home', 'price': 820000, 'location': 'Silicon Hills', 'bhk_config': '3 BHK'}]"},
                {"role": "assistant", "content": "We have the Silicon Hills Tech Corridor Smart Home at $820,000 featuring full solar automation, EV charging, and high-speed fiber."},
                {"role": "user", "content": "Awesome, could you have someone send school district ratings? I'm David Kumar, +15557771234."},
                {"role": "tool", "name": "save_lead", "content": "{'status': 'success', 'lead_id': 3}"},
                {"role": "assistant", "content": "I've flagged that for follow-up, David! Our local neighborhood advisor will send over school ratings today."}
            ]
        }
    },
    {
        "lead": {
            "name": "Sophia Chen",
            "phone": "+15552345678",
            "budget_min": 250000.0,
            "budget_max": 350000.0,
            "preferred_location": "Downtown",
            "bhk_preference": "1 BHK",
            "timeline": "Flexible",
            "financing_status": "First-time buyer",
            "status": "new",
        },
        "conversation": {
            "duration_seconds": 65,
            "outcome": "incomplete",
            "summary": "Sophia is a first-time home buyer exploring 1 BHK starter lofts in Downtown. Matched 'Sunlit Urban Studio Loft' ($280k). Looking for mortgage pre-approval assistance.",
            "transcript": [
                {"role": "assistant", "content": "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?"},
                {"role": "user", "content": "Hi, I'm looking at first-time buyer starter homes, maybe a 1 BHK downtown for around 300k."},
                {"role": "assistant", "content": "Let me look up starter lofts in Downtown under $350,000 for you."},
                {"role": "tool", "name": "search_properties", "content": "[{'title': 'Sunlit Urban Studio Loft', 'price': 280000, 'location': 'Downtown', 'bhk_config': '1 BHK'}]"},
                {"role": "assistant", "content": "We have a Sunlit Urban Studio Loft in Downtown at $280,000 with exposed brick and rapid transit access."},
                {"role": "user", "content": "Nice! My name is Sophia Chen, +15552345678. I'll need some financing guidance."},
                {"role": "tool", "name": "save_lead", "content": "{'status': 'success', 'lead_id': 4}"},
                {"role": "assistant", "content": "I've connected your profile with our first-time buyer financing specialist, Sophia!"}
            ]
        }
    },
    {
        "lead": {
            "name": "Robert Torres",
            "phone": "+15559876543",
            "budget_min": 1200000.0,
            "budget_max": 1600000.0,
            "preferred_location": "Financial District",
            "bhk_preference": "4 BHK",
            "timeline": "Immediate",
            "financing_status": "Cash buyer",
            "status": "qualified",
        },
        "conversation": {
            "duration_seconds": 160,
            "outcome": "qualified",
            "summary": "Robert inquired about executive 4 BHK penthouses in Financial District. Matched 'Financial District Penthouse Haven' ($1.45M). Verified immediate cash closing capability.",
            "transcript": [
                {"role": "assistant", "content": "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?"},
                {"role": "user", "content": "I am looking for an executive 4 BHK penthouse in the Financial District, budget up to $1.6M."},
                {"role": "tool", "name": "search_properties", "content": "[{'title': 'Financial District Penthouse Haven', 'price': 1450000, 'location': 'Financial District', 'bhk_config': '4 BHK'}]"},
                {"role": "assistant", "content": "We have the Financial District Penthouse Haven at $1,450,000 with a private elevator, 360 sky deck, and wine cellar."},
                {"role": "user", "content": "Perfect. Robert Torres here, +15559876543. Ready to close this month with cash."},
                {"role": "tool", "name": "save_lead", "content": "{'status': 'success', 'lead_id': 5}"},
                {"role": "assistant", "content": "I have marked your profile as high priority, Robert. Our private client team will reach out directly."}
            ]
        }
    },
    {
        "lead": {
            "name": "Elena Rostova",
            "phone": "+15551112222",
            "budget_min": 500000.0,
            "budget_max": 750000.0,
            "preferred_location": "Uptown",
            "bhk_preference": "3 BHK",
            "timeline": "3 months",
            "financing_status": "Pre-approved",
            "status": "needs_followup",
        },
        "conversation": {
            "duration_seconds": 92,
            "outcome": "qualified",
            "summary": "Elena is searching for a family 3 BHK near Central Park with green space for pets. Matched 'Parkside Family Garden Apartment' ($680k).",
            "transcript": [
                {"role": "assistant", "content": "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?"},
                {"role": "user", "content": "Hi Riya, we want a 3 BHK family apartment near Uptown park areas with a budget of 700k."},
                {"role": "tool", "name": "search_properties", "content": "[{'title': 'Parkside Family Garden Apartment', 'price': 680000, 'location': 'Uptown', 'bhk_config': '3 BHK'}]"},
                {"role": "assistant", "content": "I found the Parkside Family Garden Apartment in Uptown at $680,000, facing Central Park with a private patio and playground."},
                {"role": "user", "content": "That is exactly what we need. Elena Rostova, +15551112222."},
                {"role": "tool", "name": "save_lead", "content": "{'status': 'success', 'lead_id': 6}"},
                {"role": "assistant", "content": "Splendid Elena! I have saved your details and our Uptown family coordinator will follow up shortly."}
            ]
        }
    },
    {
        "lead": {
            "name": "Jordan Miller",
            "phone": "+15553334455",
            "budget_min": 350000.0,
            "budget_max": 500000.0,
            "preferred_location": "Eastside",
            "bhk_preference": "2 BHK",
            "timeline": "Not actively looking",
            "financing_status": "Purchased elsewhere",
            "status": "not_interested",
        },
        "conversation": {
            "duration_seconds": 48,
            "outcome": "not_interested",
            "summary": "Jordan answered the callback but informed the agent they purchased another condo last month in Eastside and are no longer actively looking. Lead marked as not interested.",
            "transcript": [
                {"role": "assistant", "content": "Hi there! This is Riya with EstateStream AI following up on your real estate inquiry. Are you still looking for a property?"},
                {"role": "user", "content": "Hi Riya, thanks for following up! We actually closed on a condo last month, so we're all set for now."},
                {"role": "assistant", "content": "Congratulations on your new home, Jordan! Thank you for letting us know. I will update our records so you don't receive unnecessary calls."},
                {"role": "tool", "name": "save_lead", "content": "{'status': 'not_interested', 'lead_id': 7}"},
                {"role": "assistant", "content": "Have a wonderful week in your new place!"}
            ]
        }
    }
]
