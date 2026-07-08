import json
from datetime import datetime, timezone

import requests

from src.utils.config import (
    FUSEKI_QUERY_URL,
    FUSEKI_USERNAME,
    FUSEKI_PASSWORD,
    PROCESSED_DATA_DIR,
)


REGISTRY_STATISTICS_REPORT_FILE = PROCESSED_DATA_DIR / "registry_statistics.json"


SPARQL_QUERIES = {
    "total_triples": """
        SELECT (COUNT(*) AS ?count)
        WHERE {
            ?s ?p ?o .
        }
    """,
    "datasets": """
        PREFIX dcat: <http://www.w3.org/ns/dcat#>

        SELECT (COUNT(DISTINCT ?dataset) AS ?count)
        WHERE {
            ?dataset a dcat:Dataset .
        }
    """,
    "data_services": """
        PREFIX dcat: <http://www.w3.org/ns/dcat#>

        SELECT (COUNT(DISTINCT ?service) AS ?count)
        WHERE {
            ?service a dcat:DataService .
        }
    """,
    "distributions": """
        PREFIX dcat: <http://www.w3.org/ns/dcat#>

        SELECT (COUNT(DISTINCT ?distribution) AS ?count)
        WHERE {
            ?distribution a dcat:Distribution .
        }
    """,
    "sparql_endpoints": """
        PREFIX dcat: <http://www.w3.org/ns/dcat#>

        SELECT (COUNT(DISTINCT ?endpoint) AS ?count)
        WHERE {
            ?service a dcat:DataService ;
                     dcat:endpointURL ?endpoint .
        }
    """,
    "datasets_missing_description": """
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dcterms: <http://purl.org/dc/terms/>

        SELECT (COUNT(DISTINCT ?dataset) AS ?count)
        WHERE {
            ?dataset a dcat:Dataset .
            FILTER NOT EXISTS { ?dataset dcterms:description ?description . }
        }
    """,
    "datasets_missing_creator": """
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dcterms: <http://purl.org/dc/terms/>

        SELECT (COUNT(DISTINCT ?dataset) AS ?count)
        WHERE {
            ?dataset a dcat:Dataset .
            FILTER NOT EXISTS { ?dataset dcterms:creator ?creator . }
        }
    """,
    "datasets_missing_publisher": """
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dcterms: <http://purl.org/dc/terms/>

        SELECT (COUNT(DISTINCT ?dataset) AS ?count)
        WHERE {
            ?dataset a dcat:Dataset .
            FILTER NOT EXISTS { ?dataset dcterms:publisher ?publisher . }
        }
    """,
}


def run_count_query(query: str) -> int:
    response = requests.get(
        FUSEKI_QUERY_URL,
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        auth=(FUSEKI_USERNAME, FUSEKI_PASSWORD),
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()
    return int(result["results"]["bindings"][0]["count"]["value"])


def generate_registry_statistics() -> dict:
    statistics = {}

    for name, query in SPARQL_QUERIES.items():
        statistics[name] = run_count_query(query)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "statistics": statistics,
    }

    REGISTRY_STATISTICS_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_STATISTICS_REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\nRegistry Statistics")
    print("===================")
    print(f"Total triples:                {statistics['total_triples']}")
    print(f"Datasets:                     {statistics['datasets']}")
    print(f"Data services:                {statistics['data_services']}")
    print(f"Distributions:                {statistics['distributions']}")
    print(f"SPARQL endpoints:             {statistics['sparql_endpoints']}")
    print(f"Datasets missing description: {statistics['datasets_missing_description']}")
    print(f"Datasets missing creator:     {statistics['datasets_missing_creator']}")
    print(f"Datasets missing publisher:   {statistics['datasets_missing_publisher']}")
    print(f"Report:                       {REGISTRY_STATISTICS_REPORT_FILE}")

    return report


if __name__ == "__main__":
    generate_registry_statistics()