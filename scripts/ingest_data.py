"""
One-time ingestion script.
Run this before starting the server:

    python scripts/ingest_data.py

Reads data/menu.json, data/faqs.json, and data/restaurant_info.json,
converts each entry to a searchable text chunk, and indexes them into ChromaDB.
"""
import json
import sys
import os

# Make sure we can import from the app package when run from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.embedder import get_collection

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_json(filename: str) -> dict:
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


# ── Chunk builders ──────────────────────────────────────────────────────────

def chunks_from_menu(menu: dict) -> list[tuple[str, dict]]:
    """Convert each menu item into a text chunk with metadata."""
    chunks = []
    restaurant = menu.get("restaurant", "Casa Alo's Bistro")

    for category in menu.get("categories", []):
        cat_name = category["name"]
        note = category.get("note", "")

        # Handle top-level items list
        for item in category.get("items", []):
            dietary = ", ".join(item.get("dietary", [])) or "not specified"
            popular = " [POPULAR DISH]" if item.get("popular") else ""
            availability = f" | Availability: {item['availability']}" if item.get("availability") else ""
            text = (
                f"Restaurant: {restaurant}\n"
                f"Menu Category: {cat_name}\n"
                f"Item: {item['name']}{popular}\n"
                f"Price: ${item['price']}\n"
                f"Description: {item['description']}\n"
                f"Dietary Info: {dietary}"
                f"{availability}"
            )
            if note:
                text += f"\nCategory Note: {note}"
            chunks.append((text, {"source": f"menu/{cat_name}"}))

        # Handle subsections (e.g., Drinks → Non-Alcoholic, Wine, Beer)
        for subsection in category.get("subsections", []):
            sub_name = subsection["name"]
            for item in subsection.get("items", []):
                price = f"${item['price']}" if "price" in item else "see menu"
                desc = item.get("description", item.get("origin", item.get("type", "")))
                size = f" ({item['size']})" if "size" in item else ""
                text = (
                    f"Restaurant: {restaurant}\n"
                    f"Menu Category: {cat_name} — {sub_name}\n"
                    f"Item: {item['name']}{size}\n"
                    f"Price: {price}\n"
                    f"Details: {desc}"
                )
                chunks.append((text, {"source": f"menu/{cat_name}/{sub_name}"}))

    return chunks


def chunks_from_faqs(faqs_data: dict) -> list[tuple[str, dict]]:
    """Convert each FAQ Q&A pair into a text chunk."""
    chunks = []
    for section in faqs_data.get("faqs", []):
        category = section["category"]
        for qa in section.get("questions", []):
            text = (
                f"FAQ Category: {category}\n"
                f"Question: {qa['q']}\n"
                f"Answer: {qa['a']}"
            )
            chunks.append((text, {"source": f"faqs/{category}"}))
    return chunks


def chunks_from_restaurant_info(info: dict) -> list[tuple[str, dict]]:
    """Convert restaurant info sections into text chunks."""
    chunks = []
    name = info.get("name", "Casa Alo's Bistro")

    # Basic identity
    chunks.append((
        f"Restaurant: {name}\n"
        f"Tagline: {info.get('tagline', '')}\n"
        f"About: {info.get('description', '')}",
        {"source": "info/about"}
    ))

    # Contact
    c = info.get("contact", {})
    chunks.append((
        f"Restaurant: {name}\n"
        f"Phone: {c.get('phone', '')}\n"
        f"Email: {c.get('email', '')}\n"
        f"Events Email: {c.get('events_email', '')}\n"
        f"Website: {c.get('website', '')}\n"
        f"Instagram: {c.get('instagram', '')}\n"
        f"Facebook: {c.get('facebook', '')}",
        {"source": "info/contact"}
    ))

    # Address & location
    addr = info.get("address", {})
    landmarks = ", ".join(addr.get("nearby_landmarks", []))
    chunks.append((
        f"Restaurant: {name}\n"
        f"Address: {addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}\n"
        f"Neighborhood: {addr.get('neighborhood', '')}\n"
        f"Nearby: {landmarks}",
        {"source": "info/location"}
    ))

    # Hours
    hours = info.get("hours", {})
    hours_lines = [f"  {day.capitalize()}: {v['open']} – {v['close']}" + (f" ({v['note']})" if "note" in v else "")
                   for day, v in hours.items()]
    special = info.get("special_hours", {})
    chunks.append((
        f"Restaurant: {name}\n"
        f"Hours:\n" + "\n".join(hours_lines) + "\n"
        f"Happy Hour: {special.get('happy_hour', 'N/A')}\n"
        f"Sunday Brunch: {special.get('sunday_brunch', 'N/A')}\n"
        f"Live Music: {special.get('live_music', 'N/A')}",
        {"source": "info/hours"}
    ))

    # Parking
    parking = info.get("parking", {})
    chunks.append((
        f"Restaurant: {name}\n"
        f"Parking — Street: {parking.get('street_parking', '')}\n"
        f"Parking — Private Lot: {parking.get('private_lot', '')}\n"
        f"Tip: {parking.get('tip', '')}",
        {"source": "info/parking"}
    ))

    # Policies
    policies = info.get("policies", {})
    policy_lines = "\n".join(f"  {k.replace('_', ' ').title()}: {v}" for k, v in policies.items())
    chunks.append((
        f"Restaurant: {name}\n"
        f"Policies:\n{policy_lines}",
        {"source": "info/policies"}
    ))

    # Delivery & takeout
    delivery = info.get("delivery_and_takeout", {})
    chunks.append((
        f"Restaurant: {name}\n"
        f"Takeout: {delivery.get('takeout', '')}\n"
        f"Delivery Platforms: {', '.join(delivery.get('delivery_platforms', []))}\n"
        f"Delivery Radius: {delivery.get('delivery_radius', '')}",
        {"source": "info/delivery"}
    ))

    # Sourcing
    sourcing = info.get("sourcing", {})
    partners = "\n".join(f"  - {p}" for p in sourcing.get("local_partners", []))
    chunks.append((
        f"Restaurant: {name}\n"
        f"Sourcing Philosophy: {sourcing.get('philosophy', '')}\n"
        f"Local Partners:\n{partners}",
        {"source": "info/sourcing"}
    ))

    return chunks


# ── Main ingestion ───────────────────────────────────────────────────────────

def main():
    print("Loading data files...")
    menu = load_json("menu.json")
    faqs = load_json("faqs.json")
    info = load_json("restaurant_info.json")

    print("Building document chunks...")
    all_chunks: list[tuple[str, dict]] = []
    all_chunks.extend(chunks_from_menu(menu))
    all_chunks.extend(chunks_from_faqs(faqs))
    all_chunks.extend(chunks_from_restaurant_info(info))

    print(f"Total chunks to index: {len(all_chunks)}")

    collection = get_collection()

    # Wipe and re-index for idempotency
    existing_ids = collection.get()["ids"]
    if existing_ids:
        print(f"Clearing {len(existing_ids)} existing documents...")
        collection.delete(ids=existing_ids)

    documents = [chunk[0] for chunk in all_chunks]
    metadatas = [chunk[1] for chunk in all_chunks]
    ids = [f"doc_{i}" for i in range(len(all_chunks))]

    print("Embedding and indexing (this takes ~30s on first run while the model downloads)...")
    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    print(f"\nDone. {collection.count()} documents indexed into ChromaDB.")
    print("You can now start the server:  uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
