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

MASTER_PROMPT_EXAMPLE = (
    "Doplň do zákona č. 500/2022 Z. z. oprávnenie Vojenského spravodajstva "
    "získavať údaje z určeného registra. Nastav účel, rozsah údajov, spôsob "
    "poskytovania, evidenciu prístupov, kontrolu a ochranu údajov. Priprav "
    "kompletný legislatívny materiál."
)


def _make_client():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    session = TestingSessionLocal()
    instrument = LegalInstrument(
        number="500", year=2022, full_citation="500/2022 Z. z.",
        title="Testovací zákon (API from-text test)", instrument_type="zakon",
        legal_force="zakon", issuing_authority="Národná rada SR", status="ucinny", source="slov-lex",
    )
    session.add(instrument)
    session.flush()
    provision = Provision(
        instrument_id=instrument.id, unit_type="paragraf", order_index=1,
        label="§12", hierarchical_path="paragraf:12",
    )
    session.add(provision)
    session.flush()
    session.add(
        ProvisionVersion(
            provision_id=provision.id, text="(1) Pôvodné znenie.", text_hash="a" * 64,
            effective_from=date(2022, 1, 1), effective_to=None,
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


def test_master_prompt_example_returns_open_question_not_invented_change() -> None:
    client = _make_client()
    response = client.post(
        "/api/v1/legislative-project/from-text",
        json={"instruction": MASTER_PROMPT_EXAMPLE, "as_of": "2024-01-01"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["current_legal_state"] == "Neurčené - vyžaduje odpoveď na otvorenú otázku nižšie."
    assert any("ustanovenie" in q for q in body["open_questions"])


def test_clear_instruction_proceeds_end_to_end() -> None:
    client = _make_client()
    response = client.post(
        "/api/v1/legislative-project/from-text",
        json={"instruction": "Zmeň § 12 zákona č. 500/2022 Z. z.", "as_of": "2024-01-01"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "500/2022 Z. z." in body["current_legal_state"]
    assert body["open_questions"] == []
