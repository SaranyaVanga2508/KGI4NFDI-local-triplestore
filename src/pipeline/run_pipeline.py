import json
from datetime import datetime, timezone

from src.downloader.download_dataset import download_dataset
from src.validation.validation_engine import run_validation_engine
from src.importer.importer import import_rdf_to_fuseki
from src.verification.verify_import import verify_import_completeness
from src.statistics.registry_statistics import generate_registry_statistics
from src.utils.config import PROCESSED_DATA_DIR


PIPELINE_REPORT_FILE = PROCESSED_DATA_DIR / "pipeline_report.json"


def run_pipeline() -> dict:
    print("\nKGI4NFDI Validated RDF Import Pipeline")
    print("======================================")

    pipeline_report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "RUNNING",
        "steps": {},
    }

    try:
        print("\n[1] Downloading dataset")
        download_dataset()
        pipeline_report["steps"]["download"] = {
            "status": "PASSED",
        }

        print("\n[2] Running validation engine")
        validation_report = run_validation_engine()
        pipeline_report["steps"]["validation"] = validation_report

        if not validation_report["can_import"]:
            pipeline_report["status"] = "FAILED"
            pipeline_report["reason"] = "Validation failed. Import was skipped."
            save_pipeline_report(pipeline_report)
            print("\nPipeline stopped: validation failed.")
            return pipeline_report

        print("\n[3] Importing RDF into Fuseki")
        import_report = import_rdf_to_fuseki()
        pipeline_report["steps"]["import"] = import_report

        if not import_report["imported"]:
            pipeline_report["status"] = "FAILED"
            pipeline_report["reason"] = "Import failed."
            save_pipeline_report(pipeline_report)
            return pipeline_report

        print("\n[4] Verifying import completeness")
        verification_report = verify_import_completeness()
        pipeline_report["steps"]["import_verification"] = verification_report

        if not verification_report["is_complete"]:
            pipeline_report["status"] = "FAILED"
            pipeline_report["reason"] = "Import completeness check failed."
        else:
            print("\n[5] Generating registry statistics")
            statistics_report = generate_registry_statistics()
            pipeline_report["steps"]["registry_statistics"] = statistics_report
            pipeline_report["status"] = "PASSED"

    except Exception as error:

        
        pipeline_report["status"] = "FAILED"
        pipeline_report["error"] = str(error)
        print(f"\nPipeline failed: {error}")

    pipeline_report["finished_at"] = datetime.now(timezone.utc).isoformat()
    save_pipeline_report(pipeline_report)
    print_pipeline_summary(pipeline_report)

    return pipeline_report


def save_pipeline_report(report: dict) -> None:
    PIPELINE_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    PIPELINE_REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )


def print_pipeline_summary(report: dict) -> None:
    print("\nPipeline Summary")
    print("================")
    print(f"Status: {report['status']}")

    validation = report["steps"].get("validation")
    if validation:
        print(f"Validation status: {validation['status']}")
        print(f"Can import: {validation['can_import']}")
        print(f"Triples: {validation['summary']['triple_count']}")

    verification = report["steps"].get("import_verification")
    if verification:
        print(f"Source triples: {verification['source_triples']}")
        print(f"Fuseki triples: {verification['fuseki_triples']}")
        print(f"Import complete: {verification['is_complete']}")

    print(f"Report: {PIPELINE_REPORT_FILE}")


if __name__ == "__main__":
    run_pipeline()