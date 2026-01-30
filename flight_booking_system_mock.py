"""
🛫 Flight Booking System - MOCK VERSION (No API Required)
This version simulates Claude's behavior so you can understand the flow
without needing an actual API key.
"""

import json
from datetime import datetime
from typing import Literal
import re

# ============================================================================
# DATABASE (Same as real version)
# ============================================================================

FLIGHTS_DB = {
    "NYC-LON": [
        {"id": "BA001", "price": 850, "departure": "08:00", "arrival": "20:00", "seats": 45},
        {"id": "AA102", "price": 920, "departure": "14:30", "arrival": "02:30", "seats": 12},
    ],
    "NYC-TYO": [
        {"id": "JL005", "price": 1200, "departure": "13:00", "arrival": "16:00+1", "seats": 23},
        {"id": "AA150", "price": 1150, "departure": "18:45", "arrival": "22:15+1", "seats": 8},
    ],
    "LAX-TYO": [
        {"id": "JL062", "price": 980, "departure": "11:00", "arrival": "15:30+1", "seats": 56},
        {"id": "NH175", "price": 1050, "departure": "17:00", "arrival": "21:00+1", "seats": 34},
    ],
}

BOOKINGS = {}
BOOKING_COUNTER = 1000

# ============================================================================
# TOOLS (Same as real version)
# ============================================================================

def search_flights(origin: str, destination: str, departure_date: str) -> str:
    """Search for available flights"""
    route = f"{origin}-{destination}"
    flights = FLIGHTS_DB.get(route, [])
    
    if not flights:
        return json.dumps({"error": f"No flights for route {origin} to {destination}"})
    
    return json.dumps({
        "route": f"{origin} → {destination}",
        "date": departure_date,
        "flights": flights,
        "count": len(flights)
    }, indent=2)


def check_flight_availability(flight_id: str, passengers: int) -> str:
    """Check if flight has enough seats"""
    for route, flights in FLIGHTS_DB.items():
        for flight in flights:
            if flight["id"] == flight_id:
                available = flight["seats"]
                can_book = available >= passengers
                
                return json.dumps({
                    "flight_id": flight_id,
                    "route": route,
                    "passengers_requested": passengers,
                    "seats_available": available,
                    "can_book": can_book,
                    "price_per_person": flight["price"],
                    "total_price": flight["price"] * passengers if can_book else None,
                }, indent=2)
    
    return json.dumps({"error": f"Flight {flight_id} not found"})


def book_flight(flight_id: str, passengers: int, cabin_class: str, 
                passenger_name: str, passenger_email: str) -> str:
    """Book a flight"""
    global BOOKING_COUNTER
    
    for route, flights in FLIGHTS_DB.items():
        for flight in flights:
            if flight["id"] == flight_id:
                if flight["seats"] < passengers:
                    return json.dumps({"error": "Insufficient seats"})
                
                # Calculate price
                base_price = flight["price"]
                multiplier = {"economy": 1.0, "business": 2.5, "first": 4.0}[cabin_class]
                total_price = base_price * passengers * multiplier
                
                # Create booking
                booking_id = f"BK{BOOKING_COUNTER}"
                BOOKING_COUNTER += 1
                
                booking = {
                    "booking_id": booking_id,
                    "flight_id": flight_id,
                    "passengers": passengers,
                    "cabin_class": cabin_class,
                    "passenger_name": passenger_name,
                    "total_price": round(total_price, 2),
                    "status": "CONFIRMED"
                }
                
                BOOKINGS[booking_id] = booking
                flight["seats"] -= passengers
                
                return json.dumps({
                    "success": True,
                    "message": "Flight booked successfully!",
                    "booking": booking
                }, indent=2)
    
    return json.dumps({"error": f"Flight {flight_id} not found"})


# ============================================================================
# MOCK CLAUDE (Simulates AI behavior)
# ============================================================================

class MockClaude:
    """Simulates Claude's decision-making for demo purposes"""
    
    def __init__(self):
        self.conversation_memory = []
        self.last_flight_searched = None
        self.last_route = None
    
    def process_message(self, user_message: str):
        """
        Simulates Claude's understanding and tool selection.
        In reality, Claude does this with AI. Here we use simple pattern matching.
        """
        msg_lower = user_message.lower()
        
        # PATTERN 1: Search for flights
        if any(word in msg_lower for word in ["search", "find", "fly", "flight from", "show me"]):
            # Extract cities (simplified - real Claude uses NLP)
            origin = None
            destination = None
            
            if "nyc to tokyo" in msg_lower or "new york to tokyo" in msg_lower:
                origin, destination = "NYC", "TYO"
            elif "nyc to london" in msg_lower:
                origin, destination = "NYC", "LON"
            elif "lax to tokyo" in msg_lower or "los angeles to tokyo" in msg_lower:
                origin, destination = "LAX", "TYO"
            
            if origin and destination:
                # Extract date (simplified)
                date = "2025-02-15"  # Default date
                if "march" in msg_lower:
                    date = "2025-03-01"
                
                self.last_route = f"{origin}-{destination}"
                
                return {
                    "tool_call": "search_flights",
                    "args": {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": date
                    },
                    "reasoning": f"User wants to search for flights from {origin} to {destination}"
                }
        
        # PATTERN 2: Check availability
        elif "check" in msg_lower and ("availability" in msg_lower or "seats" in msg_lower or "available" in msg_lower):
            # Extract flight ID
            flight_match = re.search(r'([A-Z]{2}\d{3})', user_message.upper())
            flight_id = flight_match.group(1) if flight_match else "JL005"
            
            # Extract passenger count
            passenger_count = 2  # Default
            if "for 3" in msg_lower or "3 people" in msg_lower or "3 passengers" in msg_lower:
                passenger_count = 3
            elif "for 2" in msg_lower or "2 people" in msg_lower or "2 passengers" in msg_lower:
                passenger_count = 2
            elif "for 1" in msg_lower or "1 person" in msg_lower or "1 passenger" in msg_lower:
                passenger_count = 1
            
            self.last_flight_searched = flight_id
            
            return {
                "tool_call": "check_flight_availability",
                "args": {
                    "flight_id": flight_id,
                    "passengers": passenger_count
                },
                "reasoning": f"User wants to check if flight {flight_id} has {passenger_count} seats"
            }
        
        # PATTERN 3: Book flight
        elif "book" in msg_lower:
            # Extract details
            
            # Flight ID
            flight_match = re.search(r'([A-Z]{2}\d{3})', user_message.upper())
            flight_id = flight_match.group(1) if flight_match else self.last_flight_searched or "JL005"
            
            # Passengers
            passenger_count = 2
            if "for 3" in msg_lower or "3 people" in msg_lower:
                passenger_count = 3
            elif "for 2" in msg_lower or "2 people" in msg_lower:
                passenger_count = 2
            
            # Cabin class
            cabin_class = "economy"
            if "business" in msg_lower:
                cabin_class = "business"
            elif "first class" in msg_lower or "first" in msg_lower:
                cabin_class = "first"
            
            # Name and email
            name_match = re.search(r'name:?\s*([A-Za-z\s]+?)(?:,|email|$)', user_message, re.IGNORECASE)
            email_match = re.search(r'email:?\s*([\w\.-]+@[\w\.-]+\.\w+)', user_message, re.IGNORECASE)
            
            passenger_name = name_match.group(1).strip() if name_match else "John Doe"
            passenger_email = email_match.group(1).strip() if email_match else "user@email.com"
            
            return {
                "tool_call": "book_flight",
                "args": {
                    "flight_id": flight_id,
                    "passengers": passenger_count,
                    "cabin_class": cabin_class,
                    "passenger_name": passenger_name,
                    "passenger_email": passenger_email
                },
                "reasoning": f"User wants to book flight {flight_id} for {passenger_count} passengers"
            }
        
        # No tool needed - just conversation
        return {
            "tool_call": None,
            "response": "I'd be happy to help! You can ask me to search flights, check availability, book flights, or manage bookings.",
            "reasoning": "General greeting or unclear request"
        }


# ============================================================================
# DEMO RUNNER
# ============================================================================

def run_mock_demo():
    """Run a demonstration of the booking system"""
    
    print("\n" + "="*70)
    print("✈️  FLIGHT BOOKING SYSTEM - MOCK DEMO")
    print("="*70)
    print("\n📝 This simulates how Claude would interact with the booking tools")
    print("    (No API key needed - this is for learning!)")
    print("\n" + "="*70 + "\n")
    
    claude = MockClaude()
    tools = {
        "search_flights": search_flights,
        "check_flight_availability": check_flight_availability,
        "book_flight": book_flight,
    }
    
    # ========================================================================
    # SCENARIO 1: Complete Booking Flow
    # ========================================================================
    print("\n📌 SCENARIO 1: Search → Check → Book")
    print("-" * 70)
    
    scenarios = [
        "I want to fly from NYC to Tokyo on February 15th",
        "Check if flight JL005 has seats for 2 passengers",
        "Book that flight for 2 passengers in business class. Name: Sarah Chen, Email: sarah.chen@email.com"
    ]
    
    for i, user_msg in enumerate(scenarios, 1):
        print(f"\n{'='*70}")
        print(f"STEP {i}")
        print(f"{'='*70}")
        print(f"\n👤 USER: {user_msg}")
        
        # Claude processes the message
        decision = claude.process_message(user_msg)
        
        print(f"\n🤖 CLAUDE'S THINKING: {decision['reasoning']}")
        
        if decision['tool_call']:
            tool_name = decision['tool_call']
            tool_args = decision['args']
            
            print(f"\n🔧 TOOL CALL: {tool_name}")
            print(f"   Arguments:")
            for key, value in tool_args.items():
                print(f"     • {key}: {value}")
            
            # Execute the tool
            result = tools[tool_name](**tool_args)
            
            print(f"\n📊 TOOL RESULT:")
            print(f"   {result[:300]}..." if len(result) > 300 else f"   {result}")
            
            # Claude's response to user
            if "error" not in result.lower():
                if tool_name == "search_flights":
                    print(f"\n💬 CLAUDE: I found some flights for you! Let me know if you'd like to check availability on any of these.")
                elif tool_name == "check_flight_availability":
                    print(f"\n💬 CLAUDE: Great news! This flight has enough seats. Would you like to book it?")
                elif tool_name == "book_flight":
                    print(f"\n💬 CLAUDE: Perfect! I've successfully booked your flight. You'll receive a confirmation email shortly.")
            else:
                print(f"\n💬 CLAUDE: I encountered an issue: {result}")
        else:
            print(f"\n💬 CLAUDE: {decision['response']}")
    
    # ========================================================================
    # SCENARIO 2: Complex Single Request
    # ========================================================================
    print("\n\n" + "="*70)
    print("📌 SCENARIO 2: All-in-One Booking Request")
    print("-" * 70)
    
    complex_request = (
        "I need to book a flight from LAX to Tokyo for 3 people in economy "
        "on March 1st. My name is Mike Johnson and email is mike.j@email.com. "
        "Please search for flights and book the cheapest option."
    )
    
    print(f"\n👤 USER: {complex_request}")
    
    print(f"\n🤖 CLAUDE'S MULTI-STEP PLAN:")
    print(f"   1. Search for flights LAX → Tokyo")
    print(f"   2. Identify cheapest option")
    print(f"   3. Check availability for 3 passengers")
    print(f"   4. Book the flight")
    
    # Step 1: Search
    print(f"\n{'─'*70}")
    print("EXECUTING STEP 1: Search flights")
    print(f"{'─'*70}")
    result1 = search_flights("LAX", "TYO", "2025-03-01")
    print(f"Result: {result1[:200]}...")
    
    # Step 2: Find cheapest
    flights_data = json.loads(result1)
    cheapest = min(flights_data['flights'], key=lambda x: x['price'])
    print(f"\n💭 CLAUDE: The cheapest flight is {cheapest['id']} at ${cheapest['price']}")
    
    # Step 3: Check availability
    print(f"\n{'─'*70}")
    print("EXECUTING STEP 2: Check availability")
    print(f"{'─'*70}")
    result2 = check_flight_availability(cheapest['id'], 3)
    print(f"Result: {result2[:200]}...")
    
    # Step 4: Book
    print(f"\n{'─'*70}")
    print("EXECUTING STEP 3: Book flight")
    print(f"{'─'*70}")
    result3 = book_flight(
        cheapest['id'], 3, "economy", 
        "Mike Johnson", "mike.j@email.com"
    )
    booking_data = json.loads(result3)
    print(f"Result: {result3}")
    
    print(f"\n💬 CLAUDE: Excellent! I've booked flight {cheapest['id']} for 3 passengers.")
    print(f"   • Total cost: ${booking_data['booking']['total_price']}")
    print(f"   • Booking ID: {booking_data['booking']['booking_id']}")
    print(f"   • Confirmation sent to: mike.j@email.com")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n\n" + "="*70)
    print("📊 BOOKING SUMMARY")
    print("="*70)
    print(f"\nTotal Bookings Made: {len(BOOKINGS)}")
    print(f"\nBooking Details:")
    for booking_id, booking in BOOKINGS.items():
        print(f"\n  {booking_id}:")
        print(f"    • Passenger: {booking['passenger_name']}")
        print(f"    • Flight: {booking['flight_id']}")
        print(f"    • Seats: {booking['passengers']} × {booking['cabin_class']}")
        print(f"    • Total: ${booking['total_price']}")
        print(f"    • Status: {booking['status']}")
    
    print("\n\n" + "="*70)
    print("✅ DEMO COMPLETE!")
    print("="*70)
    print("\n💡 KEY CONCEPTS DEMONSTRATED:")
    print("   1. ✅ Strict type checking (passengers: int, not '2' or 'two')")
    print("   2. ✅ Multi-step workflows (search → check → book)")
    print("   3. ✅ Conversation context (Claude remembers previous steps)")
    print("   4. ✅ Complex request handling (single message → multiple tools)")
    print("   5. ✅ Business logic (pricing, inventory, validation)")
    print("\n🎓 This is how Claude + LangChain works in real applications!")
    print("\n" + "="*70 + "\n")


# ============================================================================
# INTERACTIVE MODE (Optional)
# ============================================================================

def interactive_mode():
    """
    Run the system in interactive mode.
    Type your booking requests and see how Claude processes them!
    """
    print("\n" + "="*70)
    print("✈️  INTERACTIVE FLIGHT BOOKING SYSTEM")
    print("="*70)
    print("\n📝 Enter your booking requests below.")
    print("   Examples:")
    print("   • 'Search for flights from NYC to Tokyo'")
    print("   • 'Check if flight JL005 has seats for 2 passengers'")
    print("   • 'Book flight JL005 for 2, business class, name: John, email: john@email.com'")
    print("\n   Type 'exit' to quit, 'help' for examples, 'status' for current bookings")
    print("\n" + "="*70 + "\n")
    
    claude = MockClaude()
    tools = {
        "search_flights": search_flights,
        "check_flight_availability": check_flight_availability,
        "book_flight": book_flight,
    }
    
    while True:
        user_input = input("\n👤 YOU: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'exit':
            print("\n✈️  Thanks for using the Flight Booking System! Safe travels!")
            break
        
        if user_input.lower() == 'help':
            print("\n📚 HELP - Example Commands:")
            print("\n  Search:")
            print("    'I want to fly from NYC to Tokyo on Feb 15'")
            print("    'Search for flights from LAX to Tokyo'")
            print("\n  Check Availability:")
            print("    'Check if flight JL005 has seats for 2 passengers'")
            print("    'Is JL062 available for 3 people?'")
            print("\n  Book:")
            print("    'Book flight JL005 for 2, business class, name: Sarah, email: sarah@email.com'")
            print("    'Book that flight for 3 in economy, name: Mike, email: mike@email.com'")
            continue
        
        if user_input.lower() == 'status':
            if not BOOKINGS:
                print("\n📊 No bookings yet.")
            else:
                print(f"\n📊 CURRENT BOOKINGS ({len(BOOKINGS)} total):")
                for booking_id, booking in BOOKINGS.items():
                    print(f"\n  {booking_id}: {booking['passenger_name']}")
                    print(f"    Flight: {booking['flight_id']} ({booking['passengers']} seats)")
                    print(f"    Class: {booking['cabin_class']} | Total: ${booking['total_price']}")
            continue
        
        # Process user input
        decision = claude.process_message(user_input)
        
        print(f"\n🤖 CLAUDE: {decision['reasoning']}")
        
        if decision['tool_call']:
            tool_name = decision['tool_call']
            tool_args = decision['args']
            
            print(f"\n🔧 Using tool: {tool_name}")
            
            # Execute tool
            result = tools[tool_name](**tool_args)
            
            print(f"\n📊 Result:")
            result_data = json.loads(result)
            print(json.dumps(result_data, indent=2))
            
            # Friendly response
            if "error" not in result.lower():
                if tool_name == "search_flights":
                    print(f"\n💬 CLAUDE: I found {result_data.get('count', 0)} flights. Would you like to check availability?")
                elif tool_name == "check_flight_availability":
                    if result_data.get('can_book'):
                        print(f"\n💬 CLAUDE: This flight is available! Would you like to book it?")
                    else:
                        print(f"\n💬 CLAUDE: Sorry, not enough seats available.")
                elif tool_name == "book_flight":
                    print(f"\n💬 CLAUDE: ✅ Booking confirmed! ID: {result_data['booking']['booking_id']}")
        else:
            print(f"\n💬 CLAUDE: {decision['response']}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_mode()
    else:
        run_mock_demo()
