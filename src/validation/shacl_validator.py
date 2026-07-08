import json
from datetime import datetime, timezone

from pyshacl import validate
from rdflib.namespace import RDF, SH

from src.utils.config import (
    KGI_REGISTRY_RDF_FILE,
    SHAPES_FILE,
)


def short_uri(value) -> str:
    if value is None:
        return ""

    value = str(value)

    prefixes = {
        "http://kgi.services.base4nfdi.de/entity/": "kgi:",
        "http://purl.org/dc/terms/": "dcterms:",
        "http://www.w3.org/ns/dcat#": "dcat:",
        "http://www.w3.org/ns/shacl#": "sh:",
    }

    for namespace, prefix in prefixes.items():
        if value.startswith(namespace):
            return value.replace(namespace, prefix)

    return value


def extract_shacl_results(results_graph) -> list[dict]:
    results = []

    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        severity = results_graph.value(result, SH.resultSeverity)
        focus_node = results_graph.value(result, SH.focusNode)
        result_path = results_graph.value(result, SH.resultPath)
        message = results_graph.value(result, SH.resultMessage)
        source_shape = results_graph.value(result, SH.sourceShape)

        results.append(
            {
                "severity": short_uri(severity),
                "subject": short_uri(focus_node),
                "property": short_uri(result_path),
                "message": str(message) if message else "",
                "source_shape": short_uri(source_shape),
            }
        )

    return results


def validate_with_shacl(
    data_file=KGI_REGISTRY_RDF_FILE,
    shapes_file=SHAPES_FILE,
) -> dict:
    conforms, results_graph, results_text = validate(
        data_graph=str(data_file),
        shacl_graph=str(shapes_file),
        data_graph_format="nt",
        shacl_graph_format="turtle",
        inference="rdfs",
        debug=False,
    )

    structured_results = extract_shacl_results(results_graph)

    violations = [
        result for result in structured_results
        if result["severity"] == "sh:Violation"
    ]

    warnings = [
        result for result in structured_results
        if result["severity"] == "sh:Warning"
    ]

    infos = [
        result for result in structured_results
        if result["severity"] == "sh:Info"
    ]

    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "data_file": str(data_file),
        "shapes_file": str(shapes_file),
        "pyshacl_conforms": bool(conforms),
        "pyshacl_conforms_note": (
            "False when SHACL returns any result, including warnings. "
            "Import is blocked only by sh:Violation results."
        ),
        "has_shacl_results": len(structured_results) > 0,
        "has_blocking_violations": len(violations) > 0,
        "is_valid_for_import": len(violations) == 0,
        "summary": {
            "violation_count": len(violations),
            "warning_count": len(warnings),
            "info_count": len(infos),
            "total_results": len(structured_results),
        },
        "violations": violations,
        "warnings": warnings,
        "infos": infos,
    }

    return report


if __name__ == "__main__":
    report = validate_with_shacl()
    print(json.dumps(report, indent=2))
