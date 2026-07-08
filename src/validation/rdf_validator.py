import json
from collections import Counter
from datetime import datetime, timezone

from rdflib import Graph

from src.utils.config import KGI_REGISTRY_RDF_FILE


def check_duplicate_lines(file_path) -> list[str]:
    lines = [
        line.strip()
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    counts = Counter(lines)

    return [
        f"Duplicate RDF line appears {count} times: {line[:120]}..."
        for line, count in counts.items()
        if count > 1
    ]


def validate_rdf_file(file_path=KGI_REGISTRY_RDF_FILE, rdf_format="nt") -> dict:
    errors = []
    warnings = []

    if not file_path.exists():
        errors.append(f"RDF file not found: {file_path}")
        return build_report(file_path, 0, errors, warnings)

    if file_path.stat().st_size == 0:
        errors.append(f"RDF file is empty: {file_path}")
        return build_report(file_path, 0, errors, warnings)

    warnings.extend(check_duplicate_lines(file_path))

    graph = Graph()

    try:
        graph.parse(file_path, format=rdf_format)
    except Exception as error:
        errors.append(f"Invalid RDF syntax: {error}")
        return build_report(file_path, 0, errors, warnings)

    return build_report(file_path, len(graph), errors, warnings)


def build_report(file_path, triple_count: int, errors: list[str], warnings: list[str]) -> dict:
    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "file": str(file_path),
        "triple_count": triple_count,
        "is_valid": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }

    return report


if __name__ == "__main__":
    report = validate_rdf_file()
    print(json.dumps(report, indent=2))
