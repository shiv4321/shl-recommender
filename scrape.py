import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.shl.com"
CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"


def scrape_page(start):
    params = {"start": start, "type": "1"}  # type=1 = Individual Test Solutions
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(CATALOG_URL, params=params, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("tr[data-entity-id]")
    results = []

    for row in rows:
        # Name and URL
        a = row.select_one("td.custom__table-heading__title a")
        if not a:
            continue
        name = a.get_text(strip=True)
        url = BASE_URL + a["href"]

        # Test types (A, E, B, C, D, P etc.)
        keys = row.select("span.product-catalogue__key")
        test_types = [k.get_text(strip=True) for k in keys]

        # Remote testing (green dot = yes)
        tds = row.select("td.custom__table-heading__general")
        remote = "yes" if tds[0].select_one("span.catalogue__circle") else "no"
        adaptive = "yes" if len(tds) > 1 and tds[1].select_one("span.catalogue__circle") else "no"

        results.append({
            "name": name,
            "url": url,
            "test_types": test_types,
            "remote_testing": remote,
            "adaptive_irt": adaptive
        })

    return results


# Scrape all 32 pages (12 items per page)
all_assessments = []
for start in range(0, 32 * 12, 12):
    print(f"Scraping start={start}...")
    page_data = scrape_page(start)
    if not page_data:
        break
    all_assessments.extend(page_data)
    time.sleep(0.5)  # be polite

print(f"Total: {len(all_assessments)} assessments")

with open("shl_catalog.json", "w") as f:
    json.dump(all_assessments, f, indent=2)

print("Saved to shl_catalog.json")