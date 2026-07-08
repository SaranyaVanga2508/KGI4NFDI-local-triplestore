import json
from datetime import datetime, timezone

from src.utils.config import (
    KGI_REGISTRY_RDF_FILE,
    COMBINED_VALIDATION_REPORT_FILE,
)
from src.validation.rdf_validator import validate_rdf_file
from src.validation.shacl_validator import validate_with_shacl
from src.validation.quality_validator import validate_quality


def run_validation_engine(file_path=KGI_REGISTRY_RDF_FILE) -> dict:
    print("\n[Validation Engine] Starting validation")

    rdf_report = validate_rdf_file(file_path)

    if not rdf_report["is_valid"]:
        final_report = build_final_report(
            status="FAILED",
            can_import=False,
            rdf_report=rdf_report,
            shacl_report=None,
            quality_report=None,
        )
        save_report(final_report)
        print_summary(final_report)
        return final_report

    shacl_report = validate_with_shacl(data_file=file_path)
    quality_report = validate_quality(file_path)

    can_import = (
        rdf_report["is_valid"]
        and shacl_report["is_valid_for_import"]
    )

    has_warnings = (
        rdf_report["warning_count"] > 0
        or shacl_report["summary"]["warning_count"] > 0
        or quality_report["warning_count"] > 0
    )

    if can_import and has_warnings:
        status = "PASSED_WITH_WARNINGS"
    elif can_import:
        status = "PASSED"
    else:
        status = "FAILED"

    final_report = build_final_report(
        status=status,
        can_import=can_import,
        rdf_report=rdf_report,
        shacl_report=shacl_report,
        quality_report=quality_report,
    )

    save_report(final_report)
    print_summary(final_report)

    return final_report


def build_final_report(
    status: str,
    can_import: bool,
    rdf_report: dict,
    shacl_report: dict | None,
    quality_report: dict | None,
) -> dict:
    return {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "can_import": can_import,
        "summary": build_summary(
            rdf_report=rdf_report,
            shacl_report=shacl_report,
            quality_report=quality_report,
        ),
        "validation_layers": {
            "rdf_technical_validation": rdf_report,
            "shacl_semantic_validation": shacl_report,
            "extra_quality_validation": quality_report,
        },
    }


def build_summary(
    rdf_report: dict,
    shacl_report: dict | None,
    quality_report: dict | None,
) -> dict:
    return {
        "triple_count": rdf_report.get("triple_count", 0),
        "rdf_errors": rdf_report.get("error_count", 0),
        "rdf_warnings": rdf_report.get("warning_count", 0),
        "shacl_violations": (
            shacl_report["summary"]["violation_count"]
            if shacl_report else None
        ),
        "shacl_warnings": (
            shacl_report["summary"]["warning_count"]
            if shacl_report else None
        ),
        "quality_warnings": (
            quality_report["warning_count"]
            if quality_report else None
        ),
    }


def save_report(report: dict) -> None:
    COMBINED_VALIDATION_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    COMBINED_VALIDATION_REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )


def print_summary(report: dict) -> None:
    summary = report["summary"]

    print("\n[Validation Engine] Summary")
    print("===========================")
    print(f"Status: {report['status']}")
    print(f"Can import: {report['can_import']}")
    print(f"Triple count: {summary['triple_count']}")
    print(f"RDF errors: {summary['rdf_errors']}")
    print(f"RDF warnings: {summary['rdf_warnings']}")
    print(f"SHACL violations: {summary['shacl_violations']}")
    print(f"SHACL warnings: {summary['shacl_warnings']}")
    print(f"Quality warnings: {summary['quality_warnings']}")
    print(f"Report: {COMBINED_VALIDATION_REPORT_FILE}")


if __name__ == "__main__":
    run_validation_engine()