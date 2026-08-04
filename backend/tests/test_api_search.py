"""Integračný test FastAPI endpointu /api/v1/search (TestClient + SQLite)."""
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Base
from app.models.legal import LegalInstrument
from app.models.provisions import Provision, ProvisionVersion


def _make_client():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    session = TestingSessionLocal()
    instrument = LegalInstrument(
        number="400",
        year=2015,
        full_citation="400/2015 Z. z.",
        title="Zákon (syntetický testovací záznam pre API test)",
        instrument_type="zakon",
        legal_force="zakon",
        issuing_authority="Národná rada SR",
        status="ucinny",
        source="slov-lex",
    )
    session.add(instrument)
    session.flush()
    provision = Provision(
        instrument_id=instrument.id,
        unit_type="paragraf",
        order_index=1,
        label="§7",
        hierarchical_path="paragraf:7",
    )
    session.add(provision)
    session.flush()
    session.add(
        ProvisionVersion(
            provision_id=provision.id,
            text="Znenie § 7 pre API test.",
            text_hash="c" * 64,
            effective_from=date(2015, 1, 1),
            effective_to=None,
        )
    )
    session.commit()
    session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_health_endpoint() -> None:
    client = _make_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_returns_citation_and_as_of_note_when_date_defaulted() -> None:
    client = _make_client()
    response = client.get("/api/v1/search", params={"q": "§ 7"})
    assert response.status_code == 200
    body = response.json()
    assert body["as_of_was_default"] is True
    assert body["as_of_note"] is not None
    assert len(body["results"]) == 1
    assert body["results"][0]["instrument_full_citation"] == "400/2015 Z. z."


def test_search_with_explicit_as_of_no_note() -> None:
    client = _make_client()
    response = client.get("/api/v1/search", params={"q": "§ 7", "as_of": "2020-01-01"})
    assert response.status_code == 200
    body = response.json()
    assert body["as_of_was_default"] is False
    assert body["as_of_note"] is None
