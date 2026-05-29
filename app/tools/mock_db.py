"""
SQLite mock database for Casa Alo's Bistro reservation system.
Initialized on first run; seeded with realistic demo data.
"""
import sqlite3
import random
import string
from datetime import date, datetime, timedelta
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent.parent / "bistro.db"

# Restaurant hours: Tue-Sun, 5pm-9:30pm, slots every 30 min
_OPEN_DAYS = {1, 2, 3, 4, 5, 6}  # 0=Mon (closed), 1=Tue ... 6=Sun
_SLOT_TIMES = [
    "17:00", "17:30", "18:00", "18:30", "19:00",
    "19:30", "20:00", "20:30", "21:00", "21:30",
]
_MAX_TABLES_PER_SLOT = 6

_SPECIALS = {
    0: None,  # Monday — closed
    1: {
        "title": "Tuesday Tasting Menu",
        "description": "Four-course prix fixe — $65 per person",
        "items": [
            "Amuse-bouche: seared scallop with truffle foam",
            "First: roasted beet and goat cheese salad",
            "Main: pan-seared duck breast with cherry gastrique",
            "Dessert: dark chocolate lava cake with vanilla bean ice cream",
        ],
    },
    2: {
        "title": "Wine Wednesday",
        "description": "Half off all bottles when you order an entree",
        "items": [
            "Featured pour: 2021 Malbec from Mendoza — $36 (normally $72)",
            "Sommelier's pick: Sancerre Sauvignon Blanc — $58 (normally $116)",
            "Chef's plate tonight: lamb chops with rosemary jus — $34",
        ],
    },
    3: {
        "title": "Chef's Night",
        "description": "Chef Marco showcases peak-season ingredients",
        "items": [
            "Heirloom tomato tartare with basil oil and fleur de sel",
            "Seared halibut over sweet corn succotash — $32",
            "Lavender crème brûlée — $11",
        ],
    },
    4: {
        "title": "Weekend Kickoff",
        "description": "Signature cocktails and small plates to share",
        "items": [
            "Featured cocktail: Elderflower Spritz — $14",
            "Charcuterie board for two — $22",
            "Truffle fries with parmesan and herbs — $12",
            "Short rib slider trio — $18",
        ],
    },
    5: {
        "title": "Date Night",
        "description": "Two-course dinner for two — $89",
        "items": [
            "Choose one starter each: burrata, soup du jour, or caesar",
            "Choose one entree each: filet mignon, lobster pasta, or mushroom wellington",
            "Complimentary prosecco on arrival",
        ],
    },
    6: {
        "title": "Sunday Supper",
        "description": "Family-style comfort dishes — served at the table",
        "items": [
            "Slow-roasted chicken with garlic mashed potatoes — $26",
            "Braised short rib with root vegetables — $34",
            "Whole roasted cauliflower with romesco — $19",
            "Seasonal fruit cobbler with whipped cream — $10",
        ],
    },
}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _gen_code() -> str:
    return "CAB" + "".join(random.choices(string.digits, k=4))


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT DEFAULT '',
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            party_size INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            confirmed_at TEXT NOT NULL,
            confirmation_code TEXT NOT NULL UNIQUE
        )
    """)
    if cur.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] == 0:
        _seed(cur)
    conn.commit()
    conn.close()


def _seed(cur) -> None:
    seed_data = [
        ("Martinez, Elena", "elena.m@email.com", "540-555-0181", 0, "18:00", 2, "Anniversary dinner"),
        ("Johnson, Robert", "rjohnson@email.com", "540-555-0142", 1, "19:30", 4, ""),
        ("Williams Family", "kwilliams@email.com", "540-555-0193", 1, "18:30", 6, "Birthday celebration"),
        ("Davis, Priya", "priya.d@email.com", "540-555-0127", 2, "20:00", 2, "Gluten-free required"),
        ("Thompson, James", "jthompson@email.com", "540-555-0165", 3, "19:00", 3, ""),
        ("Nguyen, Sophie", "snguyen@email.com", "540-555-0174", 4, "18:00", 2, "Window table preferred"),
    ]
    today = date.today()
    for name, email, phone, day_offset, time, party, notes in seed_data:
        target = today + timedelta(days=day_offset)
        # Skip if Monday (closed)
        if target.weekday() == 0:
            target += timedelta(days=1)
        cur.execute("""
            INSERT INTO reservations (name, email, phone, date, time, party_size, notes, confirmed_at, confirmation_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, target.isoformat(), time, party, notes,
              datetime.now().isoformat(), _gen_code()))


def get_available_slots(for_date: str, party_size: int) -> list[str]:
    """Return available time slots for a given date and party size."""
    try:
        d = date.fromisoformat(for_date)
    except ValueError:
        return []

    if d.weekday() not in _OPEN_DAYS:
        return []

    conn = get_conn()
    cur = conn.cursor()
    booked = cur.execute(
        "SELECT time FROM reservations WHERE date = ?", (for_date,)
    ).fetchall()
    conn.close()

    booked_times: dict[str, int] = {}
    for row in booked:
        booked_times[row["time"]] = booked_times.get(row["time"], 0) + 1

    return [
        t for t in _SLOT_TIMES
        if booked_times.get(t, 0) < _MAX_TABLES_PER_SLOT
    ]


def create_reservation(name: str, email: str, phone: str, for_date: str,
                        time: str, party_size: int, notes: str) -> dict:
    """Insert a new reservation. Returns confirmation dict."""
    code = _gen_code()
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO reservations (name, email, phone, date, time, party_size, notes, confirmed_at, confirmation_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, for_date, time, party_size, notes,
              datetime.now().isoformat(), code))
        conn.commit()
        return {"success": True, "confirmation_code": code, "date": for_date,
                "time": time, "party_size": party_size, "name": name}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Duplicate confirmation code — please retry."}
    finally:
        conn.close()


def find_reservation(lookup: str) -> list[dict]:
    """Find reservations by partial name or phone number match."""
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT name, date, time, party_size, notes, confirmation_code
        FROM reservations
        WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
        ORDER BY date, time
        LIMIT 5
    """, (f"%{lookup}%", f"%{lookup}%", f"%{lookup}%")).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_specials(for_date: str | None = None) -> dict | None:
    if for_date:
        try:
            d = date.fromisoformat(for_date)
        except ValueError:
            d = date.today()
    else:
        d = date.today()
    return _SPECIALS.get(d.weekday())
