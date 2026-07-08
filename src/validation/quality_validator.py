import json
import re
from collections import defaultdict
from datetime import datetime, timezone

from rdflib import Graph, URIRef
from rdflib.namespace import RDF, DCAT, DCTERMS

from src.utils.config import KGI_REGISTRY_RDF_FILE


KGI_ENTITY_PREFIX = "http://kgi.services.base4nfdi.de/entity/"
WIKIDATA_ENTITY_PREFIX = "http://www.wikidata.org/entity/"
WIKIDATA_ENTITY_PATTERN = re.compile(r"^http://www\.wikidata\.org/entity/Q\d+$")


PLACEHOLDER_VALUES = {
    "n/a",
    "na",
    "none",
    "not available",
    "not available anymore",
    "null",
    "tba",
    "todo",
    "unknown",
    "work in progress",
}

PLACEHOLDER_PROPERTIES = [
    DCTERMS.title,
    DCTERMS.description,
    DCAT.landingPage,
    DCAT.endpointURL,
    DCAT.downloadURL,
    DCAT.accessURL,
    DCTERMS.conformsTo,
]

def validate_quality(file_path=KGI_REGISTRY_RDF_FILE) -> dict:
    graph = Graph()

    try:
        graph.parse(file_path, format="nt")
    except Exception as error:
        report = {
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "file": str(file_path),
            "is_valid_for_import": False,
            "error_count": 1,
            "warning_count": 0,
            "errors": [f"Quality validation could not parse RDF: {error}"],
            "warnings": [],
        }
        return report

    warnings = []

    warnings.extend(check_placeholder_values(graph))
    warnings.extend(check_duplicate_titles(graph))
    warnings.extend(check_duplicate_endpoint_urls(graph))
    warnings.extend(check_access_paths(graph))
    warnings.extend(check_unlinked_distributions(graph))
    warnings.extend(check_wikidata_iri_format(graph))

    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "file": str(file_path),
        "is_valid_for_import": True,
        "error_count": 0,
        "warning_count": len(warnings),
        "errors": [],
        "warnings": warnings,
    }

    return report


def check_placeholder_values(graph: Graph) -> list[dict]:
    warnings = []

    for predicate in PLACEHOLDER_PROPERTIES:
        for subject, _, obj in graph.triples((None, predicate, None)):
            normalized_value = str(obj).strip().lower()
            if normalized_value in PLACEHOLDER_VALUES:
                warnings.append(
                    {
                        "check": "placeholder_value",
                        "subject": short_uri(subject),
                        "property": short_uri(predicate),
                        "value": str(obj),
                        "message": "Value looks like a placeholder rather than curated registry data.",
                    }
                )

    return warnings


def check_duplicate_titles(graph: Graph) -> list[dict]:
    title_subjects = collect_value_subjects(graph, DCTERMS.title)

    return [
        {
            "check": "duplicate_dataset_title",
            "property": "dcterms:title",
            "value": title,
            "subjects": [short_uri(subject) for subject in subjects],
            "message": "Multiple datasets use the same title.",
        }
        for title, subjects in sorted(title_subjects.items())
        if len(subjects) > 1
    ]


def check_duplicate_endpoint_urls(graph: Graph) -> list[dict]:
    endpoint_subjects = collect_value_subjects(graph, DCAT.endpointURL)

    return [
        {
            "check": "duplicate_endpoint_url",
            "property": "dcat:endpointURL",
            "value": endpoint,
            "subjects": [short_uri(subject) for subject in subjects],
            "message": "Multiple data services use the same endpoint URL.",
        }
        for endpoint, subjects in sorted(endpoint_subjects.items())
        if len(subjects) > 1
    ]


def collect_value_subjects(graph: Graph, predicate) -> dict[str, list]:
    value_subjects = defaultdict(list)

    for subject, _, obj in graph.triples((None, predicate, None)):
        value_subjects[str(obj)].append(subject)

    return value_subjects


def check_access_paths(graph: Graph) -> list[dict]:
    warnings = []
    served_datasets = set(graph.objects(None, DCAT.servesDataset))

    for dataset in graph.subjects(RDF.type, DCAT.Dataset):
        has_distribution = (dataset, DCAT.distribution, None) in graph
        has_service = dataset in served_datasets
        has_landing_page = (dataset, DCAT.landingPage, None) in graph

        if not has_distribution and not has_service and not has_landing_page:
            warnings.append(
                {
                    "check": "dataset_without_access_path",
                    "subject": short_uri(dataset),
                    "message": "Dataset has no distribution, serving data service, or landing page.",
                }
            )

    return warnings


def check_unlinked_distributions(graph: Graph) -> list[dict]:
    warnings = []
    linked_distributions = set(graph.objects(None, DCAT.distribution))

    for distribution in graph.subjects(RDF.type, DCAT.Distribution):
        if distribution not in linked_distributions:
            warnings.append(
                {
                    "check": "unlinked_distribution",
                    "subject": short_uri(distribution),
                    "message": "Distribution is not linked from any dataset.",
                }
            )

    return warnings


def check_wikidata_iri_format(graph: Graph) -> list[dict]:
    warnings = []

    for _, _, obj in graph:
        if isinstance(obj, URIRef) and "wikidata.org/entity/" in str(obj):
            if not WIKIDATA_ENTITY_PATTERN.match(str(obj)):
                warnings.append(
                    {
                        "check": "wikidata_iri_format",
                        "value": str(obj),
                        "message": "Wikidata IRI should use the expected entity namespace and Q-number format.",
                    }
                )

    return warnings


def short_uri(value) -> str:
    value = str(value)

    prefixes = {
        "http://kgi.services.base4nfdi.de/entity/": "kgi:",
        "http://purl.org/dc/terms/": "dcterms:",
        "http://www.w3.org/ns/dcat#": "dcat:",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
        "http://www.wikidata.org/entity/": "wd:",
    }

    for namespace, prefix in prefixes.items():
        if value.startswith(namespace):
            return value.replace(namespace, prefix)

    return value


if __name__ == "__main__":
    report = validate_quality()
    print(json.dumps(report, indent=2))
