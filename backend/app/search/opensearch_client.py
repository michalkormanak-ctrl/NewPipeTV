"""Tenký klient nad OpenSearch pre BM25 fulltext a budúci reranking (sekcia 9).

Mimo automatizovaných testov - vyžaduje bežiaci OpenSearch (docker-compose.yml
služba `opensearch`). Postgres zostáva zdrojom pravdy (ADR-0001); tento
index je vždy možné znovu vybudovať z `provision_version`."""
from __future__ import annotations

from typing import Any

from opensearchpy import OpenSearch

PROVISION_INDEX = "provision_versions"

PROVISION_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "instrument_full_citation": {"type": "keyword"},
            "provision_label": {"type": "keyword"},
            "text": {"type": "text", "analyzer": "standard"},
            "effective_from": {"type": "date"},
            "effective_to": {"type": "date"},
            "provision_id": {"type": "keyword"},
        }
    }
}


class OpenSearchIndex:
    def __init__(self, client: OpenSearch) -> None:
        self._client = client

    def ensure_index(self) -> None:
        if not self._client.indices.exists(index=PROVISION_INDEX):
            self._client.indices.create(index=PROVISION_INDEX, body=PROVISION_INDEX_MAPPING)

    def index_provision_version(self, provision_id: str, document: dict[str, Any]) -> None:
        self._client.index(index=PROVISION_INDEX, id=provision_id, body=document, refresh=True)

    def search_bm25(self, query: str, size: int = 20) -> list[dict[str, Any]]:
        response = self._client.search(
            index=PROVISION_INDEX,
            body={"query": {"match": {"text": query}}, "size": size},
        )
        return [hit["_source"] for hit in response["hits"]["hits"]]
