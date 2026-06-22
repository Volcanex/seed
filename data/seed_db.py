#!/usr/bin/env python3
"""Populate brands and London clothing sourcing locations.
Run once: python3 data/seed_db.py
Safe to re-run — skips existing entries by name.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.db import get_conn, init_db

# (name, tier, min_gbp, max_gbp, notes, keywords)
BRANDS = [
    # S — top shelf
    ("Stone Island", "S", 60, 280, "Compass badge. Check stitching for fakes.", "stone island"),
    ("CP Company", "S", 50, 220, "Lens/goggle detail on sleeve.", "cp company,c.p. company"),
    ("Burberry", "S", 60, 350, "Nova check or equestrian logo.", "burberry,burberrys"),
    ("Supreme", "S", 40, 500, "Box logo tees most valuable. Check spelling.", "supreme"),
    ("Palace", "S", 40, 300, "Tri-ferg triangle logo.", "palace"),
    ("Off-White", "S", 60, 400, "Quotation mark branding, industrial belt.", "off-white,off white"),
    ("Stussy", "S", 30, 160, "OG and collab pieces most valuable.", "stussy,stüssy"),
    ("Arc'teryx", "S", 80, 450, "Bird logo. Technical shells command most.", "arcteryx,arc teryx,arc'teryx"),
    ("Vivienne Westwood", "S", 40, 320, "Orb logo. Bags also valuable.", "vivienne westwood,westwood"),
    ("Helmut Lang", "S", 40, 280, "Minimalist. Early 2000s archive pieces.", "helmut lang"),
    ("Raf Simons", "S", 60, 600, "Rare. Check for fakes carefully.", "raf simons"),
    ("Comme des Garçons", "S", 50, 400, "CDG Play heart is common; mainline rarer.", "comme des garcons,cdg,comme des garçons"),
    ("Maharishi", "S", 40, 200, "Camo + Eastern motifs.", "maharishi"),

    # A — good find
    ("Ralph Lauren", "A", 20, 90, "RLPC and rugby shirts command most.", "ralph lauren,polo ralph lauren,polo sport"),
    ("Tommy Hilfiger", "A", 15, 65, "90s colourblock pieces most desirable.", "tommy hilfiger,tommy"),
    ("Carhartt WIP", "A", 25, 80, "WIP label worth more than work line.", "carhartt wip,carhartt"),
    ("Patagonia", "A", 30, 140, "Fleeces and puffers. Synchilla is popular.", "patagonia"),
    ("Barbour", "A", 35, 140, "Wax jackets. Condition is everything.", "barbour"),
    ("Fred Perry", "A", 20, 65, "Laurel wreath. Twin-tip polos best.", "fred perry"),
    ("Lacoste", "A", 20, 75, "Croc logo. Polos and tracksuits.", "lacoste"),
    ("Levi's", "A", 15, 70, "501 vintage most valuable. Check tag era.", "levi's,levis,levi strauss"),
    ("Lee", "A", 12, 50, "Vintage denim. 70s-80s pieces best.", "lee jeans,lee"),
    ("Wrangler", "A", 10, 45, "Western shirts and raw denim.", "wrangler"),
    ("New Balance", "A", 20, 90, "990/993/2002r most sought after.", "new balance"),
    ("Fjallraven", "A", 25, 95, "Kanken bags + Greenland jacket.", "fjallraven,fjällräven"),
    ("Dickies", "A", 12, 45, "874 work pants and Eisenhower jacket.", "dickies"),
    ("Gramicci", "A", 20, 80, "Japanese outdoor. Nylon climbing shorts.", "gramicci"),

    # B — worth buying at the right price
    ("Nike", "B", 10, 45, "Jordan/ACG/SB lines command premium.", "nike"),
    ("Adidas", "B", 10, 40, "Originals over sportswear. Y-3 is A-tier.", "adidas"),
    ("The North Face", "B", 15, 55, "Technical shells best. Purple Label is A-tier.", "the north face,north face,tnf"),
    ("Columbia", "B", 10, 38, "Fleeces and waterproofs.", "columbia"),
    ("Timberland", "B", 10, 38, "Boots hold value; clothing less so.", "timberland"),
    ("Hugo Boss", "B", 10, 38, "Casualwear ok; suits less resale value.", "hugo boss,boss"),
    ("Calvin Klein", "B", 8, 32, "Denim and basics.", "calvin klein,ck"),
    ("Tommy Jeans", "B", 8, 30, "Not the same as Tommy Hilfiger. 90s pieces.", "tommy jeans"),
    ("Kappa", "B", 8, 32, "Track jackets most popular.", "kappa"),
    ("Fila", "B", 8, 30, "90s revival keeps demand up.", "fila"),
    ("Champion", "B", 8, 32, "Reverse weave sweatshirts premium.", "champion"),
    ("Reebok", "B", 8, 28, "Classic trainers hold value.", "reebok"),
    ("Ellesse", "B", 8, 28, "Italian sportwear. Puffers popular.", "ellesse"),
    ("Sergio Tacchini", "B", 10, 35, "Tennis heritage. Track tops.", "sergio tacchini"),
    ("Umbro", "B", 8, 28, "Football kits and retro training tops.", "umbro"),

    # C — depends on price and condition
    ("Vans", "C", 5, 20, "Basics saturated. Collabs worth more.", "vans"),
    ("Converse", "C", 5, 20, "Market flooded. Collabs only.", "converse"),
    ("GAP", "C", 4, 16, "Early 90s Gap has nostalgia value.", "gap"),
    ("Jack Wills", "C", 3, 12, "UK preppy. Limited demand.", "jack wills"),
    ("Fat Face", "C", 3, 12, "Casual. Middling.", "fat face"),
    ("White Stuff", "C", 3, 10, "Similar to Fat Face.", "white stuff"),
    ("Joules", "C", 3, 10, "Rural/garden party niche.", "joules"),
    ("Superdry", "C", 4, 14, "Very saturated. Only clean mint condition.", "superdry"),
    ("Jack & Jones", "C", 3, 10, "Budget menswear.", "jack and jones,jack & jones"),

    # F — not worth buying to resell
    ("Primark", "F", 0, 2, "Fast fashion. No resale value.", "primark"),
    ("H&M", "F", 0, 4, "Occasional designer collabs worth something.", "h&m,hm"),
    ("Zara", "F", 1, 5, "Condition must be new. Very thin margin.", "zara"),
    ("ASOS", "F", 0, 3, "Own-brand worth nothing.", "asos"),
    ("New Look", "F", 0, 3, "Budget high street.", "new look"),
    ("Boohoo", "F", 0, 2, "Ultra fast fashion.", "boohoo"),
    ("Shein", "F", 0, 1, "Ultra fast fashion.", "shein"),
    ("George", "F", 0, 2, "ASDA own brand.", "george at asda,george"),
    ("F&F", "F", 0, 2, "Tesco own brand.", "f&f"),
    ("Matalan", "F", 0, 2, "Budget.", "matalan"),
    ("Next", "F", 1, 4, "Mid-budget. Only premium lines.", "next"),
]

# (name, type, address, area, lat, lng, price_info, opening_hours, notes, website)
LOCATIONS = [
    # KG sale shops
    (
        "Traid Dalston", "kgsale",
        "106-108 Kingsland High St, E8 2NS", "East London",
        51.5455, -0.0748,
        "Women's ~£15/kg · Men's ~£10/kg",
        "Mon-Sat 10am-6pm · Sun 11am-5pm",
        "Large stock, well sorted. Good for menswear.", "https://traid.org.uk",
    ),
    (
        "Traid Tooting", "kgsale",
        "151 Upper Tooting Rd, SW17 7TJ", "South London",
        51.4284, -0.1638,
        "Women's ~£15/kg · Men's ~£10/kg",
        "Mon-Sat 10am-6pm · Sun 11am-5pm",
        "Good for kids and women's.", "https://traid.org.uk",
    ),
    (
        "Traid Hammersmith", "kgsale",
        "374 King St, W6 0RX", "West London",
        51.4930, -0.2253,
        "Women's ~£15/kg · Men's ~£10/kg",
        "Mon-Sat 10am-6pm · Sun 11am-5pm",
        "Smaller but well stocked.", "https://traid.org.uk",
    ),
    (
        "Traid Brixton", "kgsale",
        "2 Acre Lane, SW2 5SG", "South London",
        51.4627, -0.1142,
        "Women's ~£15/kg · Men's ~£10/kg",
        "Mon-Sat 10am-6pm · Sun 11am-5pm",
        "Busy location. Good footwear occasionally.", "https://traid.org.uk",
    ),
    # Car boot sales
    (
        "Battersea Car Boot Sale", "carboot",
        "Battersea Arts Centre, Lavender Hill, SW11 5TF", "South London",
        51.4741, -0.1657,
        "Buyer entry £1–2. Sellers from 6:30am.",
        "Sundays 11am–3pm (summer season, check dates)",
        "One of London's best. Arrive early for the good stuff.", None,
    ),
    (
        "Wimbledon Stadium Car Boot", "carboot",
        "Plough Lane, SW19 1ND", "South London",
        51.4221, -0.1851,
        "£1–2 entry",
        "Sat & Sun from 7am (sellers), 8am (buyers)",
        "Year-round. Large and busy. Mix of furniture and clothing.", None,
    ),
    (
        "Capital City Car Boot — Edmonton", "carboot",
        "Edmonton Green, N18", "North London",
        51.6160, -0.0617,
        "Entry charge applies — check on arrival",
        "Sat from 7am · Sun from 8am",
        "Year-round. One of the bigger ones in North London.", None,
    ),
    (
        "Wanstead Flats Car Boot", "carboot",
        "Wanstead Flats, E7", "East London",
        51.5553, 0.0264,
        "£1 entry approx",
        "Sunday mornings, seasonal",
        "Community feel. Good for vintage clothing finds.", None,
    ),
    (
        "Epsom Car Boot Sale", "carboot",
        "Epsom Racecourse, KT18 5LQ", "Surrey (40 min from central)",
        51.3227, -0.2681,
        "£1–2 entry",
        "Sundays from 6:30am (sellers), 8am (buyers)",
        "One of the best outside London. Worth the trip — huge.", None,
    ),
    # Fabric wholesale
    (
        "Goldhawk Road Fabric Strip", "fabric",
        "Goldhawk Rd, W12 (between stations)", "West London",
        51.5006, -0.2218,
        "Varies by shop — good prices. Bulk discounts available.",
        "Most shops: Mon-Sat 9am-6pm",
        "50+ fabric shops in one strip. Best fabric selection in London.", None,
    ),
    (
        "Shepherd's Bush Market (fabric)", "fabric",
        "Uxbridge Rd, W12 8LJ", "West London",
        51.5012, -0.2262,
        "Cheap stall prices. Negotiate.",
        "Mon-Sat 9am-6pm (closed Wed afternoons)",
        "Good for African prints, polyesters, and cheap textiles.", None,
    ),
    (
        "Berwick Street Cloth Shop", "fabric",
        "14 Berwick St, W1F 0PL", "Central London",
        51.5133, -0.1348,
        "Mid-range — quality over cheap",
        "Mon-Fri 9am-5:30pm · Sat 10am-5pm",
        "Soho institution. Good denim, wool, and suiting fabrics.", None,
    ),
    (
        "MacCulloch & Wallis", "fabric",
        "25-26 Poland St, W1F 8QN", "Central London",
        51.5147, -0.1380,
        "Mid to premium",
        "Mon-Fri 10am-6pm · Sat 10am-5pm",
        "Strong on haberdashery, lining, and fine fabrics.", "https://macculloch-wallis.co.uk",
    ),
]


def seed():
    init_db()
    with get_conn() as conn:
        existing_brands = {
            r[0].lower()
            for r in conn.execute("SELECT name FROM brands").fetchall()
        }
        existing_locs = {
            r[0].lower()
            for r in conn.execute("SELECT name FROM locations").fetchall()
        }

        added_b = added_l = 0

        for name, tier, lo, hi, notes, kw in BRANDS:
            if name.lower() in existing_brands:
                continue
            conn.execute(
                "INSERT INTO brands(name,tier,min_value_gbp,max_value_gbp,notes,keywords) VALUES(?,?,?,?,?,?)",
                (name, tier, lo, hi, notes, kw),
            )
            added_b += 1

        for row in LOCATIONS:
            name, typ, addr, area, lat, lng, price, hours, notes, website = row
            if name.lower() in existing_locs:
                continue
            conn.execute(
                """INSERT INTO locations
                   (name,type,address,area,lat,lng,price_info,opening_hours,notes,website,last_verified)
                   VALUES(?,?,?,?,?,?,?,?,?,?,'2026-06')""",
                (name, typ, addr, area, lat, lng, price, hours, notes, website),
            )
            added_l += 1

        print(f"Added {added_b} brands, {added_l} locations.")


if __name__ == "__main__":
    seed()
