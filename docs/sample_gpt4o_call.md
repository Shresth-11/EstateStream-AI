# EstateStream AI — Sample Qualification Call Transcript

**Agent**: Riya (EstateStream AI Voice Agent)  
**Caller**: Priya  
**Mode**: Voice / Real Estate Qualification Pipeline  
**Outcome**: Qualified Lead (`needs_followup`)  

---

### Turn-by-Turn Transcript

**[Assistant] Riya**:  
"Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?"

**[User] Caller**:  
"I am looking for a 2 BHK apartment in Midtown under $450,000."

**[Tool Execution] `search_properties`**:  
- **Arguments**: `{"location": "Midtown", "budget_max": 450000.0, "bhk": "2 BHK"}`  
- **Result**: Matched *Midtown Modern High-Rise Apartment* ($420,000, 2 BHK, Midtown)

**[Assistant] Riya**:  
"I found a fantastic match for you: Midtown Modern High-Rise Apartment in Midtown for $420,000 (2 BHK). Would you like me to save your details and arrange a viewing?"

**[User] Caller**:  
"Sounds great! My name is Priya and my number is +1-555-XXX-0199."

**[Tool Execution] `save_lead`**:  
- **Arguments**: `{"name": "Priya", "phone": "+1-555-XXX-0199", "budget_max": 450000.0, "preferred_location": "Midtown", "bhk_preference": "2 BHK"}`  
- **Result**: `{"status": "success", "lead_id": 9, "message": "Lead details saved successfully."}`

**[Assistant] Riya**:  
"Thank you! I have saved your preferences and contact details. One of our advisors will be in touch shortly with detailed listings. Have a wonderful day!"

---

### Structured Summary
- **Lead Name**: Priya
- **Contact**: +1-555-XXX-0199 (masked)
- **Preferences**: 2 BHK in Midtown, budget up to $450,000
- **Matched Inventory**: Midtown Modern High-Rise Apartment ($420,000)
- **Outcome**: `qualified`
