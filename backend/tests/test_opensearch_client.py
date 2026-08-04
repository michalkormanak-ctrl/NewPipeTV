"""Testy OpenSearchIndex wrapper logiky nad FALOŠNÝM klientom.

DÔLEŽITÉ: Reálny beh proti živej inštancii OpenSearch nebol v tomto
vývojovom sedení overiteľný - `docker pull opensearchproject/opensearch`
bol zablokovaný egress politikou prostredia (CONNECT na
`production.cloudfront.docker.com` vrátil 403, rovnaká kategória
obmedzenia ako pri Slov-Lex/EUR-Lex, pozri docs/risks.md). Tieto testy
preto overujú iba to, že `OpenSearchIndex` volá klienta so správnymi
parametrami a spracúva odpoveď správne - NIE skutočné správanie
OpenSearch/Lucene BM25 (relevancia, tokenizácia, škálovanie).

Pred produkčným nasadením je nutný živý smoke test proti bežiacej
inštancii (napr. cez `docker compose up -d opensearch` v prostredí, kde
je odchádzajúca sieť na Docker registry povolená)."""
from __future__ import annotations

from app.search.opensearch_client import PROVISION_INDEX, OpenSearchIndex


class _FakeIndicesClient:
    def __init__(self) -> None:
        self.created_with: dict | None = None
        self._exists = False

    def exists(self, index: str) -> bool:
        return self._exists

    def create(self, index: str, body: dict) -> None:
        self.created_with = {"index": index, "body": body}
        self._exists = True


class FakeOpenSearchClient:
    """Minimálna falošná implementácia rozhrania opensearch-py klienta
    použitá v OpenSearchIndex (indices.exists/create, index, search)."""

    def __init__(self) -> None:
        self.indices = _FakeIndicesClient()
        self._store: dict[str, dict] = {}

    def index(self, index: str, id: str, body: dict, refresh: bool = False) -> None:
        self._store[id] = body

    def search(self, index: str, body: dict) -> dict:
        query_text = body["query"]["match"]["text"].lower()
        hits = [
            {"_source": doc}
            for doc in self._store.values()
            if query_text in doc.get("text", "").lower()
        ]
        return {"hits": {"hits": hits[: body.get("size", 20)]}}


def test_ensure_index_creates_when_missing() -> None:
    fake_client = FakeOpenSearchClient()
    index = OpenSearchIndex(fake_client)
    index.ensure_index()
    assert fake_client.indices.created_with is not None
    assert fake_client.indices.created_with["index"] == PROVISION_INDEX
    assert "properties" in fake_client.indices.created_with["body"]["mappings"]


def test_ensure_index_is_noop_when_already_exists() -> None:
    fake_client = FakeOpenSearchClient()
    fake_client.indices._exists = True
    index = OpenSearchIndex(fake_client)
    index.ensure_index()
    assert fake_client.indices.created_with is None


def test_index_and_search_roundtrip() -> None:
    fake_client = FakeOpenSearchClient()
    index = OpenSearchIndex(fake_client)
    index.index_provision_version(
        "prov-1",
        {
            "instrument_full_citation": "500/2022 Z. z.",
            "provision_label": "§ 5",
            "text": "Orgán poskytuje údaje na základe žiadosti.",
        },
    )
    results = index.search_bm25("žiadosti")
    assert len(results) == 1
    assert results[0]["instrument_full_citation"] == "500/2022 Z. z."


def test_search_respects_size_limit() -> None:
    fake_client = FakeOpenSearchClient()
    index = OpenSearchIndex(fake_client)
    for i in range(5):
        index.index_provision_version(f"prov-{i}", {"text": "spoločný text na vyhľadanie"})
    results = index.search_bm25("spoločný", size=2)
    assert len(results) == 2
