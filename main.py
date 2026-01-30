"""
🛫 Flight Booking System with Claude + LangChain
A complete booking system demonstrating strict tool use, multi-step workflows,
and proper error handling.
"""

from langchain_anthropic import ChatAnthropic
from typing import Literal, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

model = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    temperature=0.1,  # Low temperature for consistent booking operations
)

# ============================================================================
# DATABASE SIMULATION (In real app, this would be actual database)
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
    "LON-PAR": [
        {"id": "AF318", "price": 180, "departure": "09:15", "arrival": "11:45", "seats": 89},
        {"id": "BA304", "price": 195, "departure": "16:00", "arrival": "18:30", "seats": 67},
    ],
}

BOOKINGS = {}  # Store confirmed bookings
BOOKING_COUNTER = 1000

# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

def search_flights(
    origin: Literal["NYC", "LAX", "LON", "PAR", "TYO"],
    destination: Literal["NYC", "LAX", "LON", "PAR", "TYO"],
    departure_date: str,
) -> str:
    """Search for available flights between two cities.
    
    Args:
        origin: Departure city code (NYC, LAX, LON, PAR, TYO)
        destination: Arrival city code (NYC, LAX, LON, PAR, TYO)
        departure_date: Date in YYYY-MM-DD format
    
    Returns:
        JSON string with available flights
    """
    if origin == destination:
        return json.dumps({"error": "Origin and destination cannot be the same"})
    
    route = f"{origin}-{destination}"
    flights = FLIGHTS_DB.get(route, [])
    
    if not flights:
        return json.dumps({
            "error": f"No flights available for route {origin} to {destination}",
            "suggestion": "Try a different route or check connecting flights"
        })
    
    result = {
        "route": f"{origin} → {destination}",
        "date": departure_date,
        "flights": flights,
        "count": len(flights)
    }
    
    return json.dumps(result, indent=2)


def check_flight_availability(
    flight_id: str,
    passengers: int,
) -> str:
    """Check if a specific flight has enough seats available.
    
    Args:
        flight_id: The flight number (e.g., "BA001", "JL005")
        passengers: Number of passengers (must be integer between 1-9)
    
    Returns:
        JSON string with availability status
    """
    if passengers < 1 or passengers > 9:
        return json.dumps({"error": "Passengers must be between 1 and 9"})
    
    # Search for flight in database
    for route, flights in FLIGHTS_DB.items():
        for flight in flights:
            if flight["id"] == flight_id:
                available = flight["seats"]
                is_available = available >= passengers
                
                return json.dumps({
                    "flight_id": flight_id,
                    "route": route,
                    "passengers_requested": passengers,
                    "seats_available": available,
                    "can_book": is_available,
                    "price_per_person": flight["price"],
                    "total_price": flight["price"] * passengers if is_available else None,
                    "departure": flight["departure"],
                    "arrival": flight["arrival"]
                }, indent=2)
    
    return json.dumps({"error": f"Flight {flight_id} not found"})


def book_flight(
    flight_id: str,
    passengers: int,
    cabin_class: Literal["economy", "business", "first"],
    passenger_name: str,
    passenger_email: str,
) -> str:
    """Book a flight for passengers.
    
    Args:
        flight_id: The flight number (e.g., "BA001")
        passengers: Number of passengers (must be integer)
        cabin_class: Cabin class for the booking
        passenger_name: Lead passenger full name
        passenger_email: Contact email for booking confirmation
    
    Returns:
        JSON string with booking confirmation or error
    """
    global BOOKING_COUNTER
    
    # Validate email format (basic check)
    if "@" not in passenger_email or "." not in passenger_email:
        return json.dumps({"error": "Invalid email format"})
    
    # Find the flight
    for route, flights in FLIGHTS_DB.items():
        for flight in flights:
            if flight["id"] == flight_id:
                if flight["seats"] < passengers:
                    return json.dumps({
                        "error": "Insufficient seats available",
                        "requested": passengers,
                        "available": flight["seats"]
                    })
                
                # Calculate price (cabin class multiplier)
                base_price = flight["price"]
                multiplier = {"economy": 1.0, "business": 2.5, "first": 4.0}[cabin_class]
                total_price = base_price * passengers * multiplier
                
                # Create booking
                booking_id = f"BK{BOOKING_COUNTER}"
                BOOKING_COUNTER += 1
                
                booking = {
                    "booking_id": booking_id,
                    "flight_id": flight_id,
                    "route": route,
                    "passengers": passengers,
                    "cabin_class": cabin_class,
                    "passenger_name": passenger_name,
                    "passenger_email": passenger_email,
                    "total_price": round(total_price, 2),
                    "departure": flight["departure"],
                    "arrival": flight["arrival"],
                    "status": "CONFIRMED",
                    "booking_date": datetime.now().isoformat()
                }
                
                BOOKINGS[booking_id] = booking
                
                # Update available seats
                flight["seats"] -= passengers
                
                return json.dumps({
                    "success": True,
                    "message": "Flight booked successfully!",
                    "booking": booking
                }, indent=2)
    
    return json.dumps({"error": f"Flight {flight_id} not found"})


def cancel_booking(
    booking_id: str,
    passenger_email: str,
) -> str:
    """Cancel an existing flight booking.
    
    Args:
        booking_id: The booking reference number (e.g., "BK1000")
        passenger_email: Email address for verification
    
    Returns:
        JSON string with cancellation confirmation
    """
    if booking_id not in BOOKINGS:
        return json.dumps({"error": f"Booking {booking_id} not found"})
    
    booking = BOOKINGS[booking_id]
    
    # Verify email
    if booking["passenger_email"] != passenger_email:
        return json.dumps({"error": "Email does not match booking records"})
    
    if booking["status"] == "CANCELLED":
        return json.dumps({"error": "Booking already cancelled"})
    
    # Return seats to inventory
    flight_id = booking["flight_id"]
    for route, flights in FLIGHTS_DB.items():
        for flight in flights:
            if flight["id"] == flight_id:
                flight["seats"] += booking["passengers"]
    
    # Update booking status
    booking["status"] = "CANCELLED"
    booking["cancellation_date"] = datetime.now().isoformat()
    
    # Calculate refund (90% refund)
    refund_amount = booking["total_price"] * 0.9
    
    return json.dumps({
        "success": True,
        "message": "Booking cancelled successfully",
        "booking_id": booking_id,
        "refund_amount": round(refund_amount, 2),
        "original_amount": booking["total_price"],
        "cancellation_fee": round(booking["total_price"] * 0.1, 2)
    }, indent=2)


def view_booking(
    booking_id: str,
) -> str:
    """View details of an existing booking.
    
    Args:
        booking_id: The booking reference number (e.g., "BK1000")
    
    Returns:
        JSON string with booking details
    """
    if booking_id not in BOOKINGS:
        return json.dumps({"error": f"Booking {booking_id} not found"})
    
    return json.dumps(BOOKINGS[booking_id], indent=2)


# ============================================================================
# BIND TOOLS TO MODEL
# ============================================================================

tools = [search_flights, check_flight_availability, book_flight, cancel_booking, view_booking]

model_with_tools = model.bind_tools(
    tools,
    strict=True,  # Enforce type safety
)

# ============================================================================
# BOOKING ASSISTANT
# ============================================================================

def run_booking_assistant(user_message: str, conversation_history: list = None):
    """
    Run the booking assistant with tool calling capability.
    Handles multi-turn conversations and tool execution.
    """
    if conversation_history is None:
        conversation_history = []
    
    # Add system message at the start
    if not conversation_history:
        system_msg = {
            "role": "system",
            "content": """You are a helpful flight booking assistant. You can:
1. Search for flights between cities
2. Check flight availability
3. Book flights for passengers
4. Cancel existing bookings
5. View booking details

Always confirm important details before booking. Be clear about prices and policies.
Use tools to help users with their booking needs."""
        }
        conversation_history.append(system_msg)
    
    # Add user message
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    print(f"\n{'='*70}")
    print(f"USER: {user_message}")
    print(f"{'='*70}")
    
    # Maximum iterations to prevent infinite loops
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Get response from Claude
        response = model_with_tools.invoke(conversation_history)
        
        # Add response to history
        conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        # Check if Claude wants to use tools
        if response.tool_calls:
            print(f"\n🔧 CLAUDE IS USING TOOLS:")
            
            # Execute each tool call
            tool_results = []
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                print(f"\n   Tool: {tool_name}")
                print(f"   Args: {json.dumps(tool_args, indent=6)}")
                
                # Execute the tool
                tool_function = {
                    "search_flights": search_flights,
                    "check_flight_availability": check_flight_availability,
                    "book_flight": book_flight,
                    "cancel_booking": cancel_booking,
                    "view_booking": view_booking,
                }[tool_name]
                
                result = tool_function(**tool_args)
                
                print(f"\n   Result: {result[:200]}..." if len(result) > 200 else f"\n   Result: {result}")
                
                # Add tool result to history
                tool_results.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call["id"],
                            "content": result
                        }
                    ]
                })
            
            # Add all tool results to history
            for tool_result in tool_results:
                conversation_history.append(tool_result)
            
            # Continue loop to get Claude's response to tool results
            continue
        
        else:
            # No more tool calls, Claude has final response
            print(f"\n💬 CLAUDE: {response.content}")
            print(f"\n{'='*70}\n")
            return response.content, conversation_history
    
    print(f"\n⚠️  Maximum iterations reached. Ending conversation.")
    return "I apologize, but I need to end this conversation. Please start a new booking.", conversation_history


# ============================================================================
# EXAMPLE USAGE / DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("✈️  FLIGHT BOOKING SYSTEM - DEMO")
    print("="*70)
    
    # Example 1: Search and Book
    print("\n\n📌 EXAMPLE 1: Search and Book a Flight")
    print("-" * 70)
    
    conversation = []
    
    # Step 1: Search
    response, conversation = run_booking_assistant(
        "I want to fly from NYC to Tokyo on 2025-02-15. Show me available flights.",
        conversation
    )
    
    # Step 2: Check availability
    response, conversation = run_booking_assistant(
        "Check if flight JL005 has seats for 2 passengers",
        conversation
    )
    
    # Step 3: Book
    response, conversation = run_booking_assistant(
        "Book that flight for 2 passengers, business class. Name: John Smith, Email: john@email.com",
        conversation
    )
    
    
    # Example 2: View Booking
    print("\n\n📌 EXAMPLE 2: View Booking")
    print("-" * 70)
    
    response, _ = run_booking_assistant(
        "Show me details for booking BK1000"
    )
    
    
    # Example 3: Cancel Booking
    print("\n\n📌 EXAMPLE 3: Cancel Booking")
    print("-" * 70)
    
    response, _ = run_booking_assistant(
        "Cancel booking BK1000 for john@email.com"
    )
    
    
    # Example 4: Complex Query
    print("\n\n📌 EXAMPLE 4: Complex Multi-Step Query")
    print("-" * 70)
    
    response, _ = run_booking_assistant(
        "I need to book a flight from LAX to Tokyo for 3 people in economy class on March 1st. "
        "My name is Sarah Johnson and email is sarah.j@email.com. "
        "Please search for flights and book the cheapest option if available."
    )
    
    print("\n\n✅ DEMO COMPLETE!")
    print("\n📊 FINAL DATABASE STATE:")
    print(f"\nTotal Bookings: {len(BOOKINGS)}")
    print(f"Active Bookings: {sum(1 for b in BOOKINGS.values() if b['status'] == 'CONFIRMED')}")
    print(f"Cancelled Bookings: {sum(1 for b in BOOKINGS.values() if b['status'] == 'CANCELLED')}")