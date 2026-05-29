#!/usr/bin/env python3
"""
Casa Alo's Bistro — MCP Server

Exposes the bistro's reservation tools as an MCP server so any
MCP-compatible client (Claude Desktop, other agents) can connect.

Usage (local):
  python mcp_server.py

Claude Desktop config (~/.config/claude/claude_desktop_config.json):
  {
    "mcpServers": {
      "casaalos-bistro": {
        "command": "python",
        "args": ["/absolute/path/to/casa_alos_bistro/mcp_server.py"]
      }
    }
  }
"""
import sys
from pathlib import Path

# Ensure project root is on the path so app.* imports resolve
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from app.tools.mock_db import init_db
from app.tools.handlers import (
    check_table_availability,
    book_reservation,
    get_todays_specials,
    check_reservation,
)

init_db()
mcp = FastMCP("Casa Alo's Bistro")


@mcp.tool()
def check_availability(date: str, party_size: int) -> dict:
    """Check open reservation times at Casa Alo's Bistro for a given date and party size."""
    return check_table_availability(date, party_size)


@mcp.tool()
def make_reservation(
    name: str,
    email: str,
    date: str,
    time: str,
    party_size: int,
    phone: str = "",
    notes: str = "",
) -> dict:
    """Book a table reservation at Casa Alo's Bistro. Returns a confirmation code."""
    return book_reservation(name, email, phone, date, time, party_size, notes)


@mcp.tool()
def todays_specials() -> dict:
    """Get today's featured dishes, prix fixe menus, and special offers."""
    return get_todays_specials()


@mcp.tool()
def lookup_reservation(lookup: str) -> dict:
    """Find an existing reservation by guest name, phone number, or email."""
    return check_reservation(lookup)


if __name__ == "__main__":
    mcp.run()
