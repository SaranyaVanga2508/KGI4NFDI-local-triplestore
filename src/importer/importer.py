import requests

from src.utils.config import (
    FUSEKI_DATA_URL,
    FUSEKI_USERNAME,
    FUSEKI_PASSWORD,
    KGI_REGISTRY_RDF_FILE,
)


def import_rdf_to_fuseki(file_path=KGI_REGISTRY_RDF_FILE) -> dict:
    with open(file_path, "rb") as rdf_file:
        response = requests.put(
            FUSEKI_DATA_URL,
            data=rdf_file,
            headers={"Content-Type": "application/n-triples"},
            auth=(FUSEKI_USERNAME, FUSEKI_PASSWORD),
            timeout=60,
        )

    response.raise_for_status()

    print("\nImport completed successfully.")
    print(f"Imported file: {file_path}")
    print(f"Fuseki endpoint: {FUSEKI_DATA_URL}")

    return {
        "imported": True,
        "file": str(file_path),
        "fuseki_endpoint": FUSEKI_DATA_URL,
        "status_code": response.status_code,
    }


if __name__ == "__main__":
    import_rdf_to_fuseki()
