from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_export import router as export_router
from app.api.routes_generator import router as generator_router
from app.api.routes_search import router as search_router

app = FastAPI(
    title="Slovenský AI legislatívny systém - pilot",
    description=(
        "Pilotné API. Pozri docs/ pre architektúru, bezpečnostný model a "
        "známe obmedzenia. NIE JE overené produkčné právne rozhranie."
    ),
    version="0.1.0-pilot",
)

# POZOR: povolené pre všetky originy iba kvôli lokálnemu vývojovému
# frontendu (frontend/index.html, otvorenému priamo zo súborového
# systému). V produkcii nahradiť konkrétnym zoznamom dôveryhodných
# originov (docs/security.md).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(export_router)
app.include_router(generator_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
