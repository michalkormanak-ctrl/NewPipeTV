"""Golden dataset (sekcia 18.1) - syntetický, ale koherentný korpus
pokrývajúci všetkých 11 požadovaných scenárov. Modely `Citation`,
`LegalRelation`, `EuAct`, `CourtDecision`, `LegislativeProcess`, `Comment`
a `CommentEvaluation` doteraz nemali ani jeden test mimo `Base.metadata.
create_all` - tento súbor ich prvýkrát reálne precvičuje.

Pokrytie (mapované na zoznam v zadaní):
1. konkrétne vyhľadanie zákona     -> test_search_service.py (existuje)
2. konkrétne ustanovenie            -> test_search_service.py (existuje)
3. historická verzia                -> test_point_in_time.py (existuje)
4. novelizácia                      -> test_apply_amendment.py (existuje)
5. zrušené ustanovenie              -> test_repealed_provision_has_no_effective_version_after_repeal
6. rozdielna účinnosť               -> test_delayed_effectiveness_of_single_provision_within_amendment
7. prechodné ustanovenie            -> test_transitional_provision_is_only_effective_within_its_window
8. odkaz na iný predpis             -> test_citation_resolves_to_target_provision_in_another_instrument
9. vykonávací predpis               -> test_implementing_regulation_relation
10. právny akt EÚ                   -> test_eu_act_relation
11. pripomienka z legislatívneho procesu -> test_legislative_process_comment_lifecycle
"""
from __future__ import annotations

from datetime import date

from app.consolidation.point_in_time import NoEffectiveVersionError, ProvisionSnapshot, get_effective_version
from app.models.external import CourtDecision, EuAct
from app.models.legal import LegalInstrument
from app.models.process import Comment, CommentEvaluation, LegislativeProcess
from app.models.provisions import Provision, ProvisionVersion
from app.models.relations import Citation, LegalRelation


def _make_instrument(db_session, number: str, year: int, title: str, instrument_type: str = "zakon") -> LegalInstrument:
    instrument = LegalInstrument(
        number=number,
        year=year,
        full_citation=f"{number}/{year} Z. z.",
        title=f"{title} (syntetický golden dataset záznam)",
        instrument_type=instrument_type,
        legal_force="zakon" if instrument_type == "zakon" else "vyhlaska",
        issuing_authority="Národná rada SR",
        status="ucinny",
        source="slov-lex",
    )
    db_session.add(instrument)
    db_session.flush()
    return instrument


def _make_provision(db_session, instrument: LegalInstrument, label: str, order: int) -> Provision:
    provision = Provision(
        instrument_id=instrument.id,
        unit_type="paragraf",
        order_index=order,
        label=label,
        hierarchical_path=f"paragraf:{label}",
    )
    db_session.add(provision)
    db_session.flush()
    return provision


# --- 5. Zrušené ustanovenie ------------------------------------------------


def test_repealed_provision_has_no_effective_version_after_repeal(db_session) -> None:
    instrument = _make_instrument(db_session, "600", 2022, "Zákon o registri")
    provision = _make_provision(db_session, instrument, "§6", 1)

    original = ProvisionVersion(
        provision_id=provision.id,
        text="(1) Register vedie ministerstvo.",
        text_hash="1" * 64,
        effective_from=date(2022, 1, 1),
        effective_to=date(2023, 5, 31),
        is_repealed=False,
    )
    repealed_marker = ProvisionVersion(
        provision_id=provision.id,
        text="",
        text_hash="2" * 64,
        effective_from=date(2023, 6, 1),
        effective_to=None,
        is_repealed=True,
    )
    db_session.add_all([original, repealed_marker])
    db_session.commit()

    versions = [
        ProvisionSnapshot(
            provision_id=str(provision.id), label="§6", text=original.text,
            effective_from=original.effective_from, effective_to=original.effective_to,
        ),
        ProvisionSnapshot(
            provision_id=str(provision.id), label="§6", text=repealed_marker.text,
            effective_from=repealed_marker.effective_from, effective_to=repealed_marker.effective_to,
            is_repealed=True,
        ),
    ]

    before_repeal = get_effective_version(versions, date(2023, 1, 1))
    assert before_repeal.is_repealed is False
    assert "Register vedie" in before_repeal.text

    after_repeal = get_effective_version(versions, date(2024, 1, 1))
    assert after_repeal.is_repealed is True
    assert after_repeal.text == ""


# --- 6. Rozdielna (odložená) účinnosť jedného ustanovenia -----------------


def test_delayed_effectiveness_of_single_provision_within_amendment(db_session) -> None:
    """Bežný slovenský vzor: 'zákon nadobúda účinnosť 1.1., okrem § 7a,
    ktorý nadobúda účinnosť 1.7.' - dve ustanovenia toho istého predpisu
    s rôznym effective_from."""
    instrument = _make_instrument(db_session, "601", 2023, "Novela zákona o registri")
    provision_general = _make_provision(db_session, instrument, "§7", 1)
    provision_delayed = _make_provision(db_session, instrument, "§7a", 2)

    db_session.add_all(
        [
            ProvisionVersion(
                provision_id=provision_general.id, text="Všeobecné ustanovenie.",
                text_hash="3" * 64, effective_from=date(2023, 1, 1), effective_to=None,
            ),
            ProvisionVersion(
                provision_id=provision_delayed.id, text="Ustanovenie s odloženou účinnosťou.",
                text_hash="4" * 64, effective_from=date(2023, 7, 1), effective_to=None,
            ),
        ]
    )
    db_session.commit()

    general_versions = [
        ProvisionSnapshot(str(provision_general.id), "§7", "Všeobecné ustanovenie.", date(2023, 1, 1), None)
    ]
    delayed_versions = [
        ProvisionSnapshot(str(provision_delayed.id), "§7a", "Ustanovenie s odloženou účinnosťou.", date(2023, 7, 1), None)
    ]

    as_of = date(2023, 3, 1)
    assert get_effective_version(general_versions, as_of).text == "Všeobecné ustanovenie."
    try:
        get_effective_version(delayed_versions, as_of)
        assert False, "§7a by k 1.3.2023 ešte nemalo byť účinné"
    except NoEffectiveVersionError:
        pass

    later = date(2023, 8, 1)
    assert get_effective_version(delayed_versions, later).text == "Ustanovenie s odloženou účinnosťou."


# --- 7. Prechodné ustanovenie ----------------------------------------------


def test_transitional_provision_is_only_effective_within_its_window(db_session) -> None:
    instrument = _make_instrument(db_session, "602", 2023, "Novela s prechodným ustanovením")
    provision = _make_provision(db_session, instrument, "§9", 1)
    db_session.add(
        ProvisionVersion(
            provision_id=provision.id,
            text="Konania začaté pred 1. januárom 2023 sa dokončia podľa doterajších predpisov.",
            text_hash="5" * 64,
            effective_from=date(2023, 1, 1),
            effective_to=date(2025, 1, 1),  # prechodné obdobie sa skončí
        )
    )
    db_session.commit()

    versions = [
        ProvisionSnapshot(str(provision.id), "§9", "Konania začaté pred 1. januárom 2023 ...", date(2023, 1, 1), date(2025, 1, 1))
    ]

    assert get_effective_version(versions, date(2024, 1, 1)).text.startswith("Konania")
    try:
        get_effective_version(versions, date(2026, 1, 1))
        assert False, "prechodné ustanovenie po skončení prechodného obdobia už nemá byť účinné"
    except NoEffectiveVersionError:
        pass


# --- 8. Odkaz na iný predpis (Citation) ------------------------------------


def test_citation_resolves_to_target_provision_in_another_instrument(db_session) -> None:
    main_law = _make_instrument(db_session, "603", 2022, "Hlavný zákon")
    main_provision = _make_provision(db_session, main_law, "§5", 1)

    implementing_regulation = _make_instrument(
        db_session, "60", 2023, "Vykonávacia vyhláška", instrument_type="vyhlaska"
    )
    implementing_provision = _make_provision(db_session, implementing_regulation, "§1", 1)

    citation = Citation(
        source_provision_id=implementing_provision.id,
        raw_text="§ 5 zákona č. 603/2022 Z. z.",
        normalized_reference="§5 (603/2022 Z. z.)",
        target_instrument_id=main_law.id,
        target_provision_id=main_provision.id,
        resolved=True,
    )
    db_session.add(citation)
    db_session.commit()

    assert citation.resolved is True
    assert citation.target_instrument_id == main_law.id
    assert citation.target_provision_id == main_provision.id


# --- 9. Vykonávací predpis (LegalRelation "vykonava") ----------------------


def test_implementing_regulation_relation(db_session) -> None:
    main_law = _make_instrument(db_session, "604", 2022, "Zákon splnomocňujúci na vydanie vyhlášky")
    implementing_regulation = _make_instrument(
        db_session, "61", 2023, "Vykonávacia vyhláška k zákonu 604/2022", instrument_type="vyhlaska"
    )

    relation = LegalRelation(
        relation_type="vykonava",
        source_instrument_id=implementing_regulation.id,
        target_instrument_id=main_law.id,
        confidence="explicit",
        evidence_text="Táto vyhláška vykonáva § 20 zákona č. 604/2022 Z. z.",
    )
    db_session.add(relation)
    db_session.commit()

    assert relation.relation_type == "vykonava"
    assert relation.source_instrument_id == implementing_regulation.id
    assert relation.target_instrument_id == main_law.id
    assert relation.confidence == "explicit"


# --- 10. Právny akt EÚ ------------------------------------------------------


def test_eu_act_relation(db_session) -> None:
    national_law = _make_instrument(db_session, "605", 2022, "Zákon preberajúci právo EÚ")
    eu_act = EuAct(
        celex_number="32016R0679",
        title="Nariadenie o ochrane fyzických osôb (syntetický golden dataset záznam)",
        act_type="nariadenie",
        date_of_document=date(2016, 4, 27),
        date_entry_into_force=date(2018, 5, 25),
    )
    db_session.add(eu_act)
    db_session.flush()

    relation = LegalRelation(
        relation_type="preberá_pravo_eu",
        source_instrument_id=national_law.id,
        target_eu_act_id=eu_act.id,
        confidence="explicit",
    )
    db_session.add(relation)
    db_session.commit()

    assert relation.target_eu_act_id == eu_act.id
    assert eu_act.celex_number == "32016R0679"


def test_court_decision_relation(db_session) -> None:
    """Doplnkovo k sekcii 8 - 'bol predmetom súdneho preskúmania'."""
    law = _make_instrument(db_session, "606", 2022, "Zákon preskúmaný Ústavným súdom")
    decision = CourtDecision(
        court="Ústavný súd SR",
        case_number="PL. ÚS 1/2023",
        decision_date=date(2023, 9, 1),
        summary="Syntetický golden dataset záznam - nejde o reálne rozhodnutie.",
    )
    db_session.add(decision)
    db_session.flush()

    relation = LegalRelation(
        relation_type="bol_predmetom_sudneho_preskumania",
        source_instrument_id=law.id,
        target_court_decision_id=decision.id,
        confidence="explicit",
    )
    db_session.add(relation)
    db_session.commit()

    assert relation.target_court_decision_id == decision.id
    assert decision.case_number == "PL. ÚS 1/2023"


# --- 11. Pripomienka z legislatívneho procesu ------------------------------


def test_legislative_process_comment_lifecycle(db_session) -> None:
    process = LegislativeProcess(
        process_identifier="LP/2023/123",
        departmental_number="123/2023",
        title="Návrh novely zákona o registri (syntetický golden dataset záznam)",
        submitter="Ministerstvo vnútra SR",
        gestor="Ministerstvo vnútra SR",
        status="v pripomienkovom konaní",
        date_started=date(2023, 3, 1),
    )
    db_session.add(process)
    db_session.flush()

    comment = Comment(
        process_id=process.id,
        author="Ministerstvo financií SR",
        target_provision_label="§ 5 ods. 2",
        comment_type="zasadna",
        is_fundamental=True,
        text="Navrhujeme predĺžiť lehotu na vybavenie žiadosti.",
        proposed_wording="30 dní sa nahrádza slovami '60 dní'.",
        justification="Nedostatočná administratívna kapacita.",
        thematic_category="procesné lehoty",
    )
    db_session.add(comment)
    db_session.flush()

    evaluation = CommentEvaluation(
        comment_id=comment.id,
        result="ciastocne_akceptovana",
        resolution_method="Po rozporovom konaní sa lehota skrátila na 45 dní.",
        final_wording="45 dní",
    )
    db_session.add(evaluation)
    db_session.commit()

    assert comment.process_id == process.id
    assert evaluation.comment_id == comment.id
    assert evaluation.result == "ciastocne_akceptovana"
