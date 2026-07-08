from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

KGI_REGISTRY_RDF_FILE = RAW_DATA_DIR / "kgi_registry.nt"

SHAPES_FILE = PROJECT_ROOT / "shapes" / "kgi_registry_shapes.ttl"

COMBINED_VALIDATION_REPORT_FILE = PROCESSED_DATA_DIR / "combined_validation_report.json"

FUSEKI_USERNAME = "admin"
FUSEKI_PASSWORD = "admin"


# Remote KGI4NFDI registry endpoint
KGI_REGISTRY_ENDPOINT = "https://sparql.kgi.services.base4nfdi.de/api/"


# Local Fuseki configuration
FUSEKI_BASE_URL = "http://localhost:3030"
FUSEKI_DATASET_NAME = "kg_registry"

FUSEKI_DATASET_URL = f"{FUSEKI_BASE_URL}/{FUSEKI_DATASET_NAME}"
FUSEKI_DATA_URL = f"{FUSEKI_DATASET_URL}/data"
FUSEKI_QUERY_URL = f"{FUSEKI_DATASET_URL}/query"
FUSEKI_UPDATE_URL = f"{FUSEKI_DATASET_URL}/update"
