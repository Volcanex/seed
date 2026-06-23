#!/usr/bin/env python3
"""Seed sourcing report and East London locations from June 2026 research.
Safe to re-run — skips existing entries by name.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.db import get_conn, init_db

init_db()

LOCATIONS = [
    # --- CAR BOOTS ---
    dict(
        name="Princess May Car Boot Sale",
        type="carboot",
        address="Princess May School, Barretts Grove, Stoke Newington, London N16 8DF",
        area="Stoke Newington",
        lat=51.5586, lng=-0.0703,
        price_info="£5 early (7:30–9am), £1 from 9am",
        opening_hours="Sat & Sun 7:30am–2pm",
        notes="London's most fashion-focused boot (Time Out). Stoke Newington's stylish crowd — strong for vintage and branded womenswear. ~15–20 min from Homerton. Same operator as St Augustine's.",
        website="londoncarboot.com",
        best_find=1,
        score=5,
        active=1,
    ),
    dict(
        name="Chiswick Car Boot Sale",
        type="carboot",
        address="Chiswick School, Burlington Lane / Staveley Road, London W4 3UN",
        area="Chiswick",
        lat=51.4849, lng=-0.2503,
        price_info="Buyer £1 walk-in; sellers £5 car (+£1/passenger)",
        opening_hours="First Sunday only, 6:30am–12:30pm",
        notes="One of London's most upmarket boots — affluent West London donors mean designer clothing, vintage and quality homeware. Get there early. In-window: Sunday 5 July 2026. Run by Chiswick School PTA (charity).",
        website="chiswickcarbootsale.com",
        best_find=1,
        score=5,
        active=1,
    ),
    dict(
        name="Capital Carboot Sale",
        type="carboot",
        address="Pimlico Academy, 36 Lupus Street, London SW1V 3AT",
        area="Pimlico",
        lat=51.4866, lng=-0.1302,
        price_info="£1 general (11:30am), £7 early bird online",
        opening_hours="Sundays 11:30am–2:30pm (early birds 10:15am)",
        notes="One of London's biggest and most famous. Second-hand only (no new goods). In-window: 28 Jun, 5 Jul, 12 Jul 2026. Confirm on @capitalcarbootsalepimlico before term-end.",
        website="capitalcarboot.com",
        best_find=0,
        score=4,
        active=1,
    ),
    dict(
        name="Crystal Palace Car Boot",
        type="carboot",
        address="Crystal Palace Coach Park, off Anerley Hill, London SE19 2GA",
        area="Crystal Palace",
        lat=51.4076, lng=-0.0702,
        price_info="£3 (7–8am), £2 (8–9am), £1 after 9am",
        opening_hours="Wed & Sat from 7am",
        notes="Eclectic mix incl. preloved clothing and accessories. Stylists known to source here. Wednesday sale draws serious resellers.",
        website="crystalpalaceboot.co.uk",
        best_find=0,
        score=3,
        active=1,
    ),
    dict(
        name="St Augustine's Car Boot Sale",
        type="carboot",
        address="St Augustine's School, Kilburn Park Road, London NW6 5SN",
        area="Kilburn",
        lat=51.5342, lng=-0.1947,
        price_info="£5 early (7:30am), £1 from 10:30am",
        opening_hours="Every Saturday from 7:30am",
        notes="25+ years running. Clothing, collectibles, vintage. Same operator (London Car Boot Co.) as Princess May.",
        website="londoncarboot.com",
        best_find=0,
        score=3,
        active=1,
    ),
    dict(
        name="Battersea Boot Sale",
        type="carboot",
        address="Harris Academy, 401 Battersea Park Road, London SW11 5AP",
        area="Battersea",
        lat=51.4754, lng=-0.1521,
        price_info="N/A — closed",
        opening_hours="CLOSED",
        notes="TEMPORARILY CLOSED since 27 Jan 2025 due to building works. Reopening only 'estimated 2026' — unconfirmed. Famous for designer goods, vintage and antiques when open (est. 1999). Check batterseaboot.com before visiting.",
        website="batterseaboot.com",
        best_find=0,
        score=0,
        active=0,
    ),
    dict(
        name="Kingsland / Dalston Car Boot",
        type="carboot",
        address="Kingsland Market, Kingsland High Street, Dalston, London E8",
        area="Dalston",
        lat=51.5497, lng=-0.0749,
        price_info="Free buyer entry",
        opening_hours="Saturdays 7am–2pm",
        notes="Local Hackney market with Saturday car boot. Mixed stock. Very close to Homerton.",
        website="hackney.gov.uk/kingsland-market",
        best_find=0,
        score=2,
        active=1,
    ),

    # --- KILO / WEIGHT SALES ---
    dict(
        name="Thrift Factory",
        type="kgsale",
        address="Unit 2, Hare Row, London E2 9BY",
        area="Bethnal Green",
        lat=51.5270, lng=-0.0569,
        price_info="£15/kg standard; £12/kg with Ganddee app (£3 off per kilo). No entry fee.",
        opening_hours="Daily 10am–7pm",
        notes="Over 10,000kg of stock — vintage, Y2K, streetwear, shoes, bags, accessories. Nike, Adidas appear. ~10 min from Homerton. Best high-volume option nearby.",
        website="thriftfactorykilosale.co.uk",
        best_find=1,
        score=5,
        active=1,
    ),
    dict(
        name="Y2K Wholesale — TheBigThrift",
        type="kgsale",
        address="39 Gransden Avenue, London Fields, London E8 3QA",
        area="London Fields",
        lat=51.5392, lng=-0.0676,
        price_info="Items capped £15, outerwear capped £20 (flat caps, NOT per kg). Free entry.",
        opening_hours="26–28 June 2026, 10am–7pm (next event 18–19 July, outside window)",
        notes="Wholesale-grade vintage warehouse aimed at resellers. Very close to Homerton. Item-priced not per-kg — budget separately from kilo sales.",
        website="y2kwholesale.com",
        best_find=1,
        score=4,
        active=1,
    ),
    dict(
        name="East London Vintage Kilo Sale (Judy's / Glass Onion)",
        type="kgsale",
        address="York Hall, 5 Old Ford Road, Bethnal Green, London E2 9PJ",
        area="Bethnal Green",
        lat=51.5263, lng=-0.0548,
        price_info="£15/kg (drops to £10/kg for 10kg+). Entry: earlybird £3, general £1.50.",
        opening_hours="One-day events — check judysvintagefair.co.uk (no confirmed in-window date)",
        notes="Glass Onion is the world's leading vintage wholesaler (costumes for The Crown). Stock is 1970s–90s mens + womenswear. Don't confuse Eventbrite listings at E2 9BY — those are Thrift Factory.",
        website="judysvintagefair.co.uk",
        best_find=0,
        score=4,
        active=1,
    ),
    dict(
        name="Goldsmith Vintage Kilo Sale",
        type="kgsale",
        address="St Paul's Church, Covent Garden, London WC2E 9ED",
        area="Covent Garden",
        lat=51.5118, lng=-0.1228,
        price_info="£20/kg. Entry: VIP/earlybird £3, general £2.",
        opening_hours="Pop-up events — check Eventbrite (no confirmed in-window date as of Jun 2026)",
        notes="Curated vintage. Also has permanent stores at 196–198 Portobello Road W11 and Brick Lane Vintage Market for any-day sourcing.",
        website="eventbrite.com",
        best_find=0,
        score=3,
        active=1,
    ),
    dict(
        name="Preloved Kilo",
        type="kgsale",
        address="Round Chapel, 1d Glenham Road, Hackney E5 0LY",
        area="Hackney",
        lat=51.5547, lng=-0.0571,
        price_info="£20/kg headline; £12–18/kg advance kilo tickets (limited — buy ahead). Entry £1.50.",
        opening_hours="Pop-up events — Camden (Arlington) event advertised 'this July'; check prelovedkilo.com",
        notes="Handpicked, individually graded — higher quality than typical kilo sales. Branded sportswear (Converse, Fila, Adidas, Carhartt), retro blouses, leather. UK's biggest independent kilo company.",
        website="prelovedkilo.com",
        best_find=0,
        score=4,
        active=1,
    ),
    dict(
        name="Worth The Weight Vintage Kilo",
        type="kgsale",
        address="Copeland Park / Bussey Building, 133 Copeland Road, Peckham SE15 3SN",
        area="Peckham",
        lat=51.4707, lng=-0.0627,
        price_info="£20/kg (some venues £15); single items capped £20. Entry earlybird £3, general £2.",
        opening_hours="Travelling events — no confirmed in-window date; check worththeweightvintage.com",
        notes="One of UK's largest kilo sellers (founded Sheffield 2018). 60 rails, ladies & mens, denim, sportswear, outerwear. Also runs at Pop Brixton and Fairfield Halls Croydon.",
        website="worththeweightvintage.com",
        best_find=0,
        score=3,
        active=1,
    ),
    dict(
        name="Kilo Warehouse (West Drayton)",
        type="kgsale",
        address="West Drayton, London UB area",
        area="West Drayton",
        lat=51.5054, lng=-0.4733,
        price_info="£15/kg (from March 2026)",
        opening_hours="Mon–Wed 8am–7pm, Thu 8am–10pm, Fri–Sat 8am–7pm, Sun 8am–4pm",
        notes="~10,000kg stock incl. footwear, sportswear, womenswear. Brands: Nike, Adidas, Topshop, M&S. Network of UK donation vans = high-street/branded mix, not only vintage. Day trip — West London edge.",
        website="kilowarehouse.co.uk",
        best_find=0,
        score=3,
        active=1,
    ),
    dict(
        name="PicknWeight",
        type="kgsale",
        address="Covent Garden, London WC2",
        area="Covent Garden",
        lat=51.5120, lng=-0.1228,
        price_info="By weight, coloured-sticker grading (varies by grade). No entry fee.",
        opening_hours="Open daily",
        notes="Any-day kilo shopping without waiting for an event. Good for spontaneous sourcing when in central London.",
        website="picknweight.co.uk",
        best_find=0,
        score=3,
        active=1,
    ),

    # --- CHARITY SHOPS ---
    dict(
        name="Mary's Living & Giving (Blackheath)",
        type="charity",
        address="10 Montpelier Vale, Blackheath, London SE3 0TA",
        area="Blackheath",
        lat=51.4680, lng=0.0069,
        price_info="Variable — individually priced",
        opening_hours="Mon–Sat 10am–6pm, Sun 10am–4pm",
        notes="Beautifully merchandised. Mix of high street, designer and vintage. Exceptional donations — Hermès, COS, & Other Stories appear. Championed by Mary Portas. Also branches in Primrose Hill and Clapham.",
        website="savethechildren.org.uk",
        best_find=1,
        score=5,
        active=1,
    ),
    dict(
        name="Cancer Research UK (Marylebone)",
        type="charity",
        address="24 Marylebone High Street, London W1U 4PT",
        area="Marylebone",
        lat=51.5228, lng=-0.1525,
        price_info="Variable — individually priced",
        opening_hours="Mon–Sat ~9:30am–5:30pm",
        notes="Time Out's pick as one of London's finest. Premium boutique concept — fashion samples and end-of-line with tags on. 'Kate Moss and Sienna Miller have both been known to donate here.' Best for cashmere and cocktail dresses.",
        website="cancerresearchuk.org",
        best_find=1,
        score=5,
        active=1,
    ),
    dict(
        name="British Red Cross (Chelsea)",
        type="charity",
        address="69–71 Old Church Street, Chelsea, London SW3 5BS",
        area="Chelsea",
        lat=51.4872, lng=-0.1698,
        price_info="Higher prices but huge resale headroom (£1k dress may be £150–250 here)",
        opening_hours="Mon–Sat ~10am–5pm",
        notes="Among the very best for designer — Chanel, Gucci, Prada in good condition. Strong womenswear. Higher prices than typical charity shops but enormous margin potential.",
        website="redcross.org.uk",
        best_find=1,
        score=5,
        active=1,
    ),
    dict(
        name="British Red Cross (Notting Hill)",
        type="charity",
        address="Portobello Road, Notting Hill, London W11",
        area="Notting Hill",
        lat=51.5140, lng=-0.1967,
        price_info="Variable — individually priced",
        opening_hours="Mon–Sat ~10am–5pm",
        notes="Stylish donor base — Saint Laurent, heirloom jewels. Great for a charity-shop crawl (cluster of good shops nearby on Portobello Road).",
        website="redcross.org.uk",
        best_find=1,
        score=4,
        active=1,
    ),
    dict(
        name="Cancer Research UK (Islington / Upper Street)",
        type="charity",
        address="Upper Street, Islington, London N1",
        area="Islington",
        lat=51.5387, lng=-0.1030,
        price_info="Variable — individually priced",
        opening_hours="Mon–Sat ~9:30am–5:30pm",
        notes="A cut above. Acne, Saint Laurent, Jacquemus have appeared. Curated, Instagram-promoted edits.",
        website="cancerresearchuk.org",
        best_find=0,
        score=4,
        active=1,
    ),
    dict(
        name="Cancer Research UK (Hampstead)",
        type="charity",
        address="75 Hampstead High Street, London NW3 1QX",
        area="Hampstead",
        lat=51.5566, lng=-0.1787,
        price_info="Variable — individually priced",
        opening_hours="Mon–Sat 9:30am–5:30pm, Sun 12–6pm",
        notes="Tight edit of contemporary and designer fashions. Fair prices.",
        website="cancerresearchuk.org",
        best_find=0,
        score=4,
        active=1,
    ),
    dict(
        name="Barnardo's (Marylebone)",
        type="charity",
        address="Off Marylebone High Street, London W1",
        area="Marylebone",
        lat=51.5220, lng=-0.1520,
        price_info="Variable — reflects condition",
        opening_hours="Mon–Sat ~9:30am–5:30pm",
        notes="Small but exceptional stock — Bottega Veneta, Maje, Balenciaga have appeared. Worth the Marylebone crawl (Cancer Research, Oxfam, Barnardo's all within minutes).",
        website="barnardos.org.uk",
        best_find=0,
        score=4,
        active=1,
    ),
    dict(
        name="TRAID (Dalston)",
        type="charity",
        address="Kingsland High Street, Dalston, London E8",
        area="Dalston",
        lat=51.5497, lng=-0.0749,
        price_info="Variable — individually priced",
        opening_hours="Mon–Sat 10am–6pm, Sun 11am–5pm",
        notes="Sustainability-focused. Ever-rotating fashionable preloved. East London's style-conscious donor base. Close to Homerton.",
        website="traid.org.uk",
        best_find=0,
        score=3,
        active=1,
    ),
    dict(
        name="Lama's Pyjamas (London Buddhist Centre)",
        type="charity",
        address="Roman Road area, Bethnal Green, London E2",
        area="Bethnal Green",
        lat=51.5256, lng=-0.0485,
        price_info="Variable — reasonable/low prices",
        opening_hours="Check locally",
        notes="Colourful clothes, occasional designer goods, friendly staff, calm curated feel. Roman Road, close to Homerton.",
        website=None,
        best_find=0,
        score=3,
        active=1,
    ),
    dict(
        name="Octavia Foundation (Kensington)",
        type="charity",
        address="Brompton Road / Fulham Road area, Kensington, London SW3",
        area="Kensington",
        lat=51.4920, lng=-0.1780,
        price_info="Variable — higher for designer items",
        opening_hours="Mon–Sat ~10am–5:30pm",
        notes="High-quality donated designer and vintage. Accessories — Dolce & Gabbana, vintage It-bags have appeared. Also Marylebone Road branch.",
        website="octavia.org.uk",
        best_find=0,
        score=4,
        active=1,
    ),
]

REPORT_TITLE = "Where to Source Cheap, Good-Quality Branded Clothes for Vinted Reselling — East London & Beyond (22 June – 13 July 2026)"

REPORT_BODY = """## TL;DR

- **Your single best high-volume play is the East London kilo-sale cluster on your doorstep**: Thrift Factory (Unit 2, Hare Row, E2 9BY) runs daily at £15/kg (£12/kg with the Ganddee app), and Y2K Wholesale's "TheBigThrift" warehouse (39 Gransden Avenue, E8 3QA) runs 26–28 June with items capped at £15 and outerwear at £20 — both walkable or one bus from Homerton.
- **For recognisable branded womenswear you can value with confidence, charity shops in affluent areas beat kilo sales**: Mary's Living & Giving (Blackheath/Primrose Hill), Cancer Research & Oxfam (Marylebone), and the Notting Hill/Chelsea British Red Cross shops regularly rack Chanel, Gucci, Prada, Joseph, Cos and & Other Stories at a fraction of resale value.
- **Car boots are your cheapest per-item branded finds** — Princess May (Stoke Newington, Sat/Sun, ~15 min away) and Chiswick (Sun 5 July) are the standouts; note **Battersea Boot remains temporarily closed** for building works as of mid-2026.

## Strategy

Two sourcing models suit a beginner chasing branded womenswear:

1. **Charity shops in wealthy postcodes** — individually-priced, recognisable brands you can verify and resell with confidence. Lower volume, higher certainty. Ideal while learning values.
2. **Kilo sales and warehouse events** — bulk volume at very low per-item cost, but brand mix is luck-of-the-draw and skews vintage/Y2K. Start with charity shops and car boots for confidence, then layer in one kilo trip once you can eyeball value fast.

## Key Dates (22 Jun – 13 Jul 2026)

- **Battersea Boot (SW11) is CLOSED** — building works, no confirmed reopening.
- **Chiswick Car Boot** — first Sunday only → **Sunday 5 July 2026** is your one in-window date.
- **Capital Carboot (Pimlico)** — Sundays 28 Jun, 5 Jul, 12 Jul (likely open; confirm on Instagram the week before).
- **Y2K Wholesale TheBigThrift** — **26–28 June** at E8 3QA; next event 18–19 July falls just outside window.

## Staged Recommendations

**Stage 1 — This week (build confidence):** Charity-shop crawl in **Marylebone High Street** (Cancer Research, Oxfam, Barnardo's, Octavia all within minutes). Pair with **Princess May (N16)** on Saturday or Sunday. Benchmark: buy under ~25% of realistic Vinted sold price.

**Stage 2 — Within 10 days (test bulk):** **Y2K Wholesale TheBigThrift 26–28 June (E8 3QA)** and/or **Thrift Factory (E2 9BY) any day with Ganddee app for £12/kg**. Buy a small test haul (5–10kg), photograph, list, track sell-through and margin. Scale up if items sell within 3 weeks at 3x+ markup.

**Stage 3 — If margins justify:** **Chiswick (5 July)** designer run; **Preloved Kilo** advance-ticket event (£12–15/kg for handpicked, graded stock). Once moving steady volume, book a private handpick at a wholesaler (ToBeWornAgain, London Vintage Wholesale, Beyond Retro).

## Caveats

- Dates for one-off kilo sales shift constantly. Several organisers (Judy's/Glass Onion, Worth the Weight, Goldsmith, Preloved Kilo) did not confirm an in-window date — verify on Eventbrite/Instagram before travelling.
- **Battersea Boot is closed** — older guides still list it as active. Do not visit.
- **Capital Carboot summer status** — official messaging says 'every Sunday all year' but confirm on @capitalcarbootsalepimlico before term-end.
- **Y2K Wholesale is item-priced, not per-kg** (clothing ≤£15, outerwear ≤£20) — don't budget it as a kilo sale.
- Kilo sales are blind buys — skew vintage/Y2K, not current high-street. For a new reseller prioritising value certainty, charity shops and car boots remain lower-risk until you can value stock at a glance.
"""


def insert_locations():
    with get_conn() as conn:
        existing = {r[0] for r in conn.execute("SELECT name FROM locations").fetchall()}
        inserted = 0
        for loc in LOCATIONS:
            if loc["name"] in existing:
                print(f"  skip (exists): {loc['name']}")
                continue
            conn.execute(
                """INSERT INTO locations
                   (name, type, address, area, lat, lng, price_info, opening_hours,
                    notes, website, active, best_find, score, date_added, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'), 'report:sourcing-jun26')""",
                (
                    loc["name"], loc["type"], loc.get("address"), loc.get("area"),
                    loc.get("lat"), loc.get("lng"), loc.get("price_info"),
                    loc.get("opening_hours"), loc.get("notes"), loc.get("website"),
                    loc.get("active", 1), loc.get("best_find", 0), loc.get("score", 3),
                ),
            )
            inserted += 1
            print(f"  + {loc['name']} ({loc['type']})")
        print(f"Inserted {inserted} locations.")


def insert_report():
    with get_conn() as conn:
        existing = {r[0] for r in conn.execute("SELECT title FROM reports").fetchall()}
        if REPORT_TITLE in existing:
            print(f"  skip (exists): report already in DB")
            return
        conn.execute(
            "INSERT INTO reports (title, body, source) VALUES (?, ?, ?)",
            (REPORT_TITLE, REPORT_BODY, "deep-research:jun22-2026"),
        )
        print(f"  + report: {REPORT_TITLE[:60]}...")


if __name__ == "__main__":
    print("Inserting locations...")
    insert_locations()
    print("Inserting report...")
    insert_report()
    print("Done.")
