from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from scraper import scrape_books

app = FastAPI(title="DOAB Book Scraper API", version="1.0")

# Allow frontend (Next.js) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your Next.js domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "✅ DOAB Scraper API is running!"}


@app.get("/scrape")
def scrape(
    query: str = Query(..., description="Course/subject (e.g., Computer Science)"),
    start_year: int = Query(..., description="Start year"),
    end_year: int = Query(..., description="End year"),
    limit: int = Query(50, description="Number of books to fetch"),
):
    books = scrape_books(query, start_year, end_year, limit)
    return {"count": len(books), "books": books}
