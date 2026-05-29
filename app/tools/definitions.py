"""Anthropic tool_use schemas for Casa Alo's Bistro."""

TOOLS = [
    {
        "name": "check_table_availability",
        "description": (
            "Check available reservation time slots at Casa Alo's Bistro for a specific date "
            "and party size. Returns a list of open times or a message if the restaurant is closed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to check in YYYY-MM-DD format.",
                },
                "party_size": {
                    "type": "integer",
                    "description": "Number of guests (1 to 12).",
                },
            },
            "required": ["date", "party_size"],
        },
    },
    {
        "name": "book_reservation",
        "description": (
            "Book a table reservation at Casa Alo's Bistro. Returns a confirmation code. "
            "Always check availability first to confirm the time slot is open."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Guest's full name."},
                "email": {"type": "string", "description": "Guest's email address."},
                "phone": {"type": "string", "description": "Guest's phone number (optional)."},
                "date": {"type": "string", "description": "Reservation date YYYY-MM-DD."},
                "time": {"type": "string", "description": "Reservation time HH:MM (24-hour)."},
                "party_size": {"type": "integer", "description": "Number of guests."},
                "notes": {
                    "type": "string",
                    "description": "Special requests, dietary needs, or occasion notes.",
                },
            },
            "required": ["name", "email", "date", "time", "party_size"],
        },
    },
    {
        "name": "get_todays_specials",
        "description": "Get today's featured dishes, prix fixe menus, and special offers at Casa Alo's Bistro.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "check_reservation",
        "description": "Look up an existing reservation by guest name, phone number, or email address.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lookup": {
                    "type": "string",
                    "description": "Guest name, phone number, or email to search by.",
                },
            },
            "required": ["lookup"],
        },
    },
]
