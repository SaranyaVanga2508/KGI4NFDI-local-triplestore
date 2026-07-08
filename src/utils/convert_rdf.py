from rdflib import Graph, Namespace

from src.utils.config import KGI_REGISTRY_RDF_FILE, PROCESSED_DATA_DIR


TURTLE_OUTPUT_FILE = PROCESSED_DATA_DIR / "kgi_registry.ttl"
KGI = Namespace("http://kgi.services.base4nfdi.de/entity/")


def convert_nt_to_turtle() -> None:
    graph = Graph()

    graph.parse(KGI_REGISTRY_RDF_FILE, format="nt")
    graph.bind("kgi", KGI)

    TURTLE_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    graph.serialize(
        destination=TURTLE_OUTPUT_FILE,
        format="turtle",
    )

    print("RDF conversion completed.")
    print(f"Input:  {KGI_REGISTRY_RDF_FILE}")
    print(f"Output: {TURTLE_OUTPUT_FILE}")
    print(f"Triples converted: {len(graph)}")


if __name__ == "__main__":
    convert_nt_to_turtle()
