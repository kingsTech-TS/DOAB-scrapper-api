import requests
import time
from datetime import datetime

# -------------------------------
# Safe request with retries
# -------------------------------
def safe_request(url, params, headers, retries=3, timeout=60):
    for attempt in range(retries):
        try:
            return requests.get(url, params=params, headers=headers, timeout=timeout)
        except requests.exceptions.Timeout:
            print(f"⚠️ Timeout... retrying ({attempt+1}/{retries})")
            time.sleep(5)
    raise Exception("❌ Failed after multiple retries due to timeout")


# -------------------------------
# DOAB API Search (per year, stop when global limit reached)
# -------------------------------
def search_doab_year(query, year, books_so_far, global_limit, expand="metadata", batch_size=100):
    base_url = "https://directory.doabooks.org/rest/search"
    offset = 0
    books = []

    while len(books_so_far) + len(books) < global_limit:
        params = {
            "query": f"{query} {year}",
            "expand": expand,
            "limit": batch_size,
            "offset": offset
        }

        headers = {"Accept": "application/json"}
        response = safe_request(base_url, params, headers, timeout=60)
        data = response.json()

        records = data if isinstance(data, list) else data.get("records", [])
        if not records:
            break

        for rec in records:
            # --- Title ---
            title = rec.get("title")
            if not title:
                for md in rec.get("metadata", []):
                    if md.get("key") == "dc.title":
                        title = md.get("value")
                        break
            title = title or "N/A"

            # --- Authors ---
            authors = []
            if "authors" in rec and rec["authors"]:
                for a in rec["authors"]:
                    if "fullName" in a:
                        authors.append(a["fullName"])
            else:
                for md in rec.get("metadata", []):
                    if md.get("key") == "dc.contributor.author":
                        authors.append(md.get("value"))

            if not authors:
                for md in rec.get("metadata", []):
                    if md.get("key", "").startswith("dc.contributor"):
                        authors.append(md.get("value"))

            authors_str = ", ".join(authors) if authors else "N/A"

            # --- Year ---
            pub_date = rec.get("publicationDate")
            if not pub_date:
                for md in rec.get("metadata", []):
                    if md.get("key") == "dc.date.issued":
                        pub_date = md.get("value")
                        break
            year_str = pub_date[:4] if pub_date else "N/A"

            # --- URL ---
            handle = rec.get("handle")
            url = f"https://directory.doabooks.org/handle/{handle}" if handle else "N/A"

            if year_str == str(year):
                books.append({
                    "Title": title,
                    "Author(s)/Contributors": authors_str,
                    "Year": year_str,
                    "URL": url
                })

            if len(books_so_far) + len(books) >= global_limit:
                return books

        offset += batch_size

    return books


# -------------------------------
# Wrapper Function (used by FastAPI)
# -------------------------------
def scrape_books(query: str, start_year: int, end_year: int, global_limit: int = 50):
    if start_year > end_year:
        start_year, end_year = end_year, start_year

    all_books = []
    for year in range(end_year, start_year - 1, -1):
        if len(all_books) >= global_limit:
            break
        year_books = search_doab_year(query, year, all_books, global_limit, batch_size=100)
        all_books.extend(year_books)

    return all_books[:global_limit]
