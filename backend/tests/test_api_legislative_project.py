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
        number="500",
        year=2022,
        full_citation="500/2022 Z. z.",
        title="Testovací zákon (API test)",
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
        label="§12",
        hierarchical_path="paragraf:12",
    )
    session.add(provision)
    session.flush()
    session.add(
        ProvisionVersion(
            provision_id=provision.id,
            text="(1) Orgán poskytuje údaje do 30 dní.",
            text_hash="e" * 64,
            effective_from=date(2022, 1, 1),
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


def test_legislative_project_endpoint_returns_package_with_disclaimer() -> None:
    client = _make_client()
    payload = {
        "title": "Novela zákona č. 500/2022 Z. z.",
        "user_instruction": "Skráť lehotu na 15 dní.",
        "target_instrument_number": "500",
        "target_instrument_year": 2022,
        "target_provision_reference": "§ 12",
        "amendment_instructions": [
            {"operation": "nahradit", "target_text": "do 30 dní", "new_text": "do 15 dní"}
        ],
        "as_of": "2024-01-01",
    }
    response = client.post("/api/v1/legislative-project", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "do 15 dní" in body["consolidated_text"]
    assert "Strojovo vytvorený pracovný legislatívny materiál" in body["disclaimer"]
    assert body["as_of_was_default"] is False
