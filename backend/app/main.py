from fastapi import FastAPI

from app.api.routes_search import router as search_router

app = FastAPI(
    title="Slovenský AI legislatívny systém - pilot",
    description=(
        "Pilotné API. Pozri docs/ pre architektúru, bezpečnostný model a "
        "známe obmedzenia. NIE JE overené produkčné právne rozhranie."
    ),
    version="0.1.0-pilot",
)

app.include_router(search_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
