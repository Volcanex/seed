#!/usr/bin/env python3
"""Populate days_open, event_start, event_end for existing locations.
Safe to re-run — uses UPDATE by name.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.db import get_conn, init_db

init_db()

# days_open: comma-separated day abbreviations (mon tue wed thu fri sat sun)
# or "daily" for every day.
# event_start / event_end: ISO date strings for one-off date-range events.
SCHEDULE = [
    # --- CAR BOOTS ---
    ("Princess May Car Boot Sale",              "sat,sun",                      None,         None),
    ("Chiswick Car Boot Sale",                  "sun",         "2026-07-05", "2026-07-05"),
    ("Capital Carboot Sale",                    "sun",                          None,         None),
    ("Crystal Palace Car Boot",                 "wed,sat",                      None,         None),
    ("St Augustine's Car Boot Sale",            "sat",                          None,         None),
    ("Battersea Boot Sale",                     None,                           None,         None),
    ("Kingsland / Dalston Car Boot",            "sat",                          None,         None),
    # --- KILO / WEIGHT SALES ---
    ("Thrift Factory",                          "daily",                        None,         None),
    ("Y2K Wholesale — TheBigThrift",            None,          "2026-06-26", "2026-06-28"),
    ("East London Vintage Kilo Sale (Judy's / Glass Onion)", None,             None,         None),
    ("Goldsmith Vintage Kilo Sale",             None,                           None,         None),
    ("Preloved Kilo",                           None,                           None,         None),
    ("Worth The Weight Vintage Kilo",           None,                           None,         None),
    ("Kilo Warehouse (West Drayton)",           "daily",                        None,         None),
    ("PicknWeight",                             "daily",                        None,         None),
    # --- CHARITY SHOPS ---
    ("Mary's Living & Giving (Blackheath)",     "daily",                        None,         None),
    ("Cancer Research UK (Marylebone)",         "mon,tue,wed,thu,fri,sat",      None,         None),
    ("British Red Cross (Chelsea)",             "mon,tue,wed,thu,fri,sat",      None,         None),
    ("British Red Cross (Notting Hill)",        "mon,tue,wed,thu,fri,sat",      None,         None),
    ("Cancer Research UK (Islington / Upper Street)", "mon,tue,wed,thu,fri,sat", None,        None),
    ("Cancer Research UK (Hampstead)",          "daily",                        None,         None),
    ("Barnardo's (Marylebone)",                 "mon,tue,wed,thu,fri,sat",      None,         None),
    ("TRAID (Dalston)",                         "daily",                        None,         None),
    ("Lama's Pyjamas (London Buddhist Centre)", None,                           None,         None),
    ("Octavia Foundation (Kensington)",         "mon,tue,wed,thu,fri,sat",      None,         None),
    # --- EXISTING SEED LOCATIONS ---
    ("Traid Dalston",                           "daily",                        None,         None),
    ("Traid Tooting",                           "daily",                        None,         None),
    ("Traid Hammersmith",                       "daily",                        None,         None),
    ("Traid Brixton",                           "daily",                        None,         None),
    ("Battersea Car Boot Sale",                 "sun",                          None,         None),
    ("Wimbledon Stadium Car Boot",              "sat,sun",                      None,         None),
    ("Capital City Car Boot — Edmonton",        "sat,sun",                      None,         None),
    ("Wanstead Flats Car Boot",                 "sat,sun",                      None,         None),
    ("Epsom Car Boot Sale",                     "sat,sun",                      None,         None),
    ("Goldhawk Road Fabric Strip",              "mon,tue,wed,thu,fri,sat",      None,         None),
    ("Shepherd's Bush Market (fabric)",         "mon,tue,wed,thu,fri,sat",      None,         None),
    ("Berwick Street Cloth Shop",               "mon,tue,wed,thu,fri,sat",      None,         None),
    ("MacCulloch & Wallis",                     "mon,tue,wed,thu,fri,sat",      None,         None),
]

with get_conn() as conn:
    updated = 0
    skipped = 0
    for name, days_open, event_start, event_end in SCHEDULE:
        rowcount = conn.execute(
            "UPDATE locations SET days_open=?, event_start=?, event_end=? WHERE name=?",
            (days_open, event_start, event_end, name),
        ).rowcount
        if rowcount:
            updated += 1
        else:
            skipped += 1
            print(f"  ! not found: {name}")
    print(f"Updated {updated} locations, {skipped} not found.")
