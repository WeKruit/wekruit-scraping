from __future__ import annotations

from copy import deepcopy


PRESET_FAMILIES = {
    "venue": {
        "neurips": {
            "family": "venue",
            "slug": "neurips",
            "label": "Neural Information Processing Systems",
            "query": "NeurIPS",
            "search": None,
            "filter": {"primary_location.source.id": "S4306420609"},
            "entity": "works",
        },
        "iclr": {
            "family": "venue",
            "slug": "iclr",
            "label": "International Conference on Learning Representations",
            "query": "ICLR",
            "search": None,
            "filter": {"primary_location.source.id": "S4306419637"},
            "entity": "works",
        },
    },
    "concept": {
        "artificial-intelligence": {
            "family": "concept",
            "slug": "artificial-intelligence",
            "label": "Artificial intelligence",
            "query": "Artificial intelligence",
            "search": None,
            "filter": {"concepts.id": "C154945302"},
            "entity": "works",
        },
        "machine-learning": {
            "family": "concept",
            "slug": "machine-learning",
            "label": "Machine learning",
            "query": "Machine learning",
            "search": None,
            "filter": {"concepts.id": "C119857082"},
            "entity": "works",
        },
    },
    "keyword": {
        "transformer": {
            "family": "keyword",
            "slug": "transformer",
            "label": "Transformer",
            "query": "transformer",
            "search": "transformer",
            "filter": {},
            "entity": "works",
        },
        "attention": {
            "family": "keyword",
            "slug": "attention",
            "label": "Attention",
            "query": "attention",
            "search": "attention",
            "filter": {},
            "entity": "works",
        },
    },
}


def list_presets(family: str) -> list[str]:
    if family not in PRESET_FAMILIES:
        raise KeyError(f"Unknown preset family: {family}")
    return list(PRESET_FAMILIES[family])


def get_preset(family: str, slug: str) -> dict[str, object]:
    try:
        return deepcopy(PRESET_FAMILIES[family][slug])
    except KeyError as error:
        raise KeyError(f"Unknown AI/ML preset: {family}/{slug}") from error
