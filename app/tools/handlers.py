"""
Tool execution handlers for Casa Alo's Bistro.
Each function maps to one tool definition and returns a plain dict.
"""
from app.tools.mock_db import (
    get_available_slots,
    create_reservation,
    find_reservation,
    get_specials,
)


def check_table_availability(date: str, party_size: int) -> dict:
    slots = get_available_slots(date, party_size)
    if not slots:
        from datetime import date as _date
        try:
            d = _date.fromisoformat(date)
            if d.weekday() == 0:
                return {
                    "available": False,
                    "message": "Casa Alo's Bistro is closed on Mondays.",
                    "date": date,
                }
        except ValueError:
            return {"available": False, "message": "Invalid date format.", "date": date}
        return {
            "available": False,
            "message": "No availability for that date and party size.",
            "date": date,
            "party_size": party_size,
        }
    return {
        "available": True,
        "date": date,
        "party_size": party_size,
        "open_slots": slots,
        "note": "We're open Tuesday through Sunday, 5 PM to 9:30 PM.",
    }


def book_reservation(name: str, email: str, phone: str, date: str,
                     time: str, party_size: int, notes: str = "") -> dict:
    # Validate slot still open before booking
    slots = get_available_slots(date, party_size)
    if time not in slots:
        return {
            "success": False,
            "error": f"{time} on {date} is no longer available. Open slots: {slots or 'none'}.",
        }
    result = create_reservation(name, email, phone, date, time, party_size, notes)
    if result["success"]:
        result["message"] = (
            f"Reservation confirmed for {name} — {party_size} guest(s) on {date} at {time}. "
            f"Confirmation code: {result['confirmation_code']}. "
            "We look forward to seeing you at Casa Alo's Bistro!"
        )
    return result


def get_todays_specials() -> dict:
    specials = get_specials()
    if not specials:
        return {
            "open_today": False,
            "message": "Casa Alo's Bistro is closed today (Monday). We reopen Tuesday at 5 PM.",
        }
    return {"open_today": True, **specials}


def check_reservation(lookup: str) -> dict:
    results = find_reservation(lookup)
    if not results:
        return {
            "found": False,
            "message": f"No reservations found for '{lookup}'. Please check the spelling or try your email.",
        }
    return {"found": True, "count": len(results), "reservations": results}


def execute_tool(name: str, inputs: dict) -> dict:
    """Dispatch tool call by name."""
    if name == "check_table_availability":
        return check_table_availability(
            date=inputs["date"],
            party_size=inputs["party_size"],
        )
    if name == "book_reservation":
        return book_reservation(
            name=inputs["name"],
            email=inputs["email"],
            phone=inputs.get("phone", ""),
            date=inputs["date"],
            time=inputs["time"],
            party_size=inputs["party_size"],
            notes=inputs.get("notes", ""),
        )
    if name == "get_todays_specials":
        return get_todays_specials()
    if name == "check_reservation":
        return check_reservation(lookup=inputs["lookup"])
    return {"error": f"Unknown tool: {name}"}
