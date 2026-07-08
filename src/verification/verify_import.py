import json
from datetime import datetime, timezone

import requests

from src.utils.config import (
    FUSEKI_QUERY_URL,
    FUSEKI_USERNAME,
    FUSEKI_PASSWORD,
    COMBINED_VALIDATION_REPORT_FILE,
    PROCESSED_DATA_DIR,
)


IMPORT_VERIFICATION_REPORT_FILE = PROCESSED_DATA_DIR / "import_verification_report.json"


COUNT_QUERY = """
SELECT (COUNT(*) AS ?count)
WHERE {
  ?s ?p ?o .
}
"""


def get_fuseki_triple_count() -> int:
    response = requests.get(
        FUSEKI_QUERY_URL,
        params={"query": COUNT_QUERY},
        headers={"Accept": "application/sparql-results+json"},
        auth=(FUSEKI_USERNAME, FUSEKI_PASSWORD),
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()
    return int(result["results"]["bindings"][0]["count"]["value"])


def verify_import_completeness() -> dict:
    validation_report = json.loads(
        COMBINED_VALIDATION_REPORT_FILE.read_text(encoding="utf-8")
    )

    source_count = validation_report["summary"]["triple_count"]
    fuseki_count = get_fuseki_triple_count()
    difference = source_count - fuseki_count

    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "source_triples": source_count,
        "fuseki_triples": fuseki_count,
        "difference": difference,
        "is_complete": difference == 0,
        "status": "PASSED" if difference == 0 else "FAILED",
        "query": COUNT_QUERY.strip(),
    }

    IMPORT_VERIFICATION_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_VERIFICATION_REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\nImport Completeness Check")
    print("=========================")
    print(f"Source RDF triples: {source_count}")
    print(f"Fuseki triples:     {fuseki_count}")
    print(f"Difference:         {difference}")
    print(f"Status:             {report['status']}")
    print(f"Report:             {IMPORT_VERIFICATION_REPORT_FILE}")

    return report


if __name__ == "__main__":
    verify_import_completeness()