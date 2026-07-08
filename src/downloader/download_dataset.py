import requests

from src.utils.config import KGI_REGISTRY_ENDPOINT, KGI_REGISTRY_RDF_FILE


CONSTRUCT_QUERY = """
CONSTRUCT {
  ?s ?p ?o .
}
WHERE {
  ?s ?p ?o .
}
"""


def download_dataset() -> dict:
    KGI_REGISTRY_RDF_FILE.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(
        KGI_REGISTRY_ENDPOINT,
        params={"query": CONSTRUCT_QUERY},
        headers={"Accept": "text/turtle"},
        timeout=60,
    )

    response.raise_for_status()

    # The endpoint fails for application/n-triples, but the Turtle response is
    # N-Triples-compatible. Store it as .nt and validate/import it as N-Triples.
    KGI_REGISTRY_RDF_FILE.write_bytes(response.content)

    print("Dataset downloaded successfully.")
    print(f"Saved to: {KGI_REGISTRY_RDF_FILE}")
    print(f"File size: {KGI_REGISTRY_RDF_FILE.stat().st_size} bytes")

    return {
        "downloaded": True,
        "file": str(KGI_REGISTRY_RDF_FILE),
        "file_size_bytes": KGI_REGISTRY_RDF_FILE.stat().st_size,
    }


if __name__ == "__main__":
    download_dataset()
