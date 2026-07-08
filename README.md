# KGI4NFDI Local Triplestore

This project sets up a local RDF triplestore for the KGI4NFDI Knowledge Graph
Registry, validates the downloaded RDF data, imports it into Apache Jena Fuseki,
and verifies that the import is complete.

The project was built for a programming task focused on RDF validation, local
triplestore setup, and SPARQL access.

## Features

- Downloads the KGI4NFDI Knowledge Graph Registry with a SPARQL `CONSTRUCT`
  query.
- Stores the registry locally as N-Triples.
- Validates RDF syntax and source triple count.
- Runs SHACL validation for dataset, data service, and distribution metadata.
- Runs additional quality checks for curation issues.
- Imports the validated RDF into a local Apache Jena Fuseki triplestore.
- Verifies import completeness by comparing source and Fuseki triple counts.
- Generates registry statistics with SPARQL queries.

## Technology Stack

- Python
- RDFLib
- pySHACL
- Apache Jena Fuseki
- Docker / Docker Compose
- SPARQL

## Project Structure

```text
data/
  raw/
    kgi_registry.nt                  Downloaded registry RDF data
  processed/
    combined_validation_report.json  Combined validation report
    import_verification_report.json  Import completeness report
    pipeline_report.json             End-to-end pipeline report
    registry_statistics.json         SPARQL statistics report

shapes/
  kgi_registry_shapes.ttl            SHACL shapes used for semantic validation

src/
  downloader/                        Dataset download logic
  validation/                        RDF, SHACL, and quality validation
  importer/                          Fuseki import logic
  verification/                      Import completeness check
  statistics/                        SPARQL-based registry statistics
  pipeline/                          End-to-end pipeline runner
  utils/                             Shared configuration and utilities
```

## RDF Format Decision

The remote KGI endpoint is requested with:

```text
Accept: text/turtle
```

because the endpoint returns an error when directly requested as
`application/n-triples`. The returned RDF is N-Triples-compatible
triple-per-line RDF, so the pipeline stores and processes it locally as:

```text
data/raw/kgi_registry.nt
```

The validators and Fuseki importer therefore use N-Triples locally.

## Setup

Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start Fuseki:

```powershell
docker compose up -d
```

Fuseki will run at:

```text
http://localhost:3030
```

The configured dataset is:

```text
kg_registry
```

## Run the Pipeline

Run the full validated import pipeline:

```powershell
python -m src.pipeline.run_pipeline
```

The pipeline performs these steps:

1. Download the KGI4NFDI registry RDF.
2. Run RDF, SHACL, and quality validation.
3. Import the RDF into Fuseki if validation has no blocking errors.
4. Verify import completeness by comparing source and Fuseki triple counts.
5. Generate registry statistics using SPARQL.

## Validation Layers

### RDF Validation

Implemented in `src/validation/rdf_validator.py`.

Checks:

- RDF file exists.
- RDF file is not empty.
- RDF file can be parsed as N-Triples.
- Duplicate RDF line warnings.
- Source triple count.

### SHACL Validation

Implemented in `src/validation/shacl_validator.py` using
`shapes/kgi_registry_shapes.ttl`.

Checks:

- Every `dcat:Dataset` has a literal title.
- Dataset description, publisher, and creator metadata are reported as warnings
  when missing.
- `dcat:DataService` resources have an endpoint URL and serve a dataset.
- `dcat:Distribution` resources have either `downloadURL` or `accessURL`.
- URL-like values should use `http` or `https`.
- Dataset, service, and distribution relationships point to the expected
  resource types.

Only `sh:Violation` results block import. `sh:Warning` results are reported but
do not prevent loading the dataset into Fuseki.

### Quality Validation

Implemented in `src/validation/quality_validator.py`.

Checks non-blocking curation issues:

- Placeholder values such as `work in progress` or `not available anymore`.
- Duplicate dataset titles.
- Duplicate endpoint URLs.
- Datasets without an access path.
- Distributions not linked from any dataset.
- Wikidata IRI consistency.

Quality validation is intentionally warning-only. It is used to identify data
curation issues, not to block import.

## Querying the Triplestore

After a successful import, open Fuseki in the browser:

```text
http://localhost:3030
```

Use the `kg_registry` dataset query interface, or send SPARQL queries to:

```text
http://localhost:3030/kg_registry/query
```

Example query:

```sparql
PREFIX dcat: <http://www.w3.org/ns/dcat#>

SELECT ?dataset
WHERE {
  ?dataset a dcat:Dataset .
}
LIMIT 10
```

## Generated Reports

The pipeline writes reports to `data/processed/`.

Important reports:

- `combined_validation_report.json` summarizes all validation layers.
- `import_verification_report.json` confirms whether the Fuseki import is
  complete.
- `pipeline_report.json` summarizes the full pipeline run.
- `registry_statistics.json` contains SPARQL-based summary statistics.

Example successful validation summary:

```text
Status: PASSED_WITH_WARNINGS
Can import: True
Triple count: 403
RDF errors: 0
SHACL violations: 0
SHACL warnings: 26
Quality warnings: 3
```

## Design Notes

The validation layer is separated into three stages:

```text
RDF validation     -> Is the file valid RDF?
SHACL validation   -> Does the graph follow the expected DCAT structure?
Quality validation -> Are there useful curation warnings?
```

This separation keeps import-blocking errors distinct from non-blocking data
quality issues.
