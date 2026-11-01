# ERP Data Warehouse and Institutional Decision Support System

This Flask application uses the supplied demonstration warehouse package in
`erp_semester5_etl_package/`. The package is the authoritative development
source; the smaller CSVs under `data/` are legacy prototype data and are not
used by CSV mode.

## Dataset

The authoritative package contains 1,000 students, 5,000 attendance rows,
5,000 examination rows, and 1,000 fee rows. It represents Semester 5,
Academic Year 2025-2026, across CSE, ECE, EEE, IT, AIDS, and AIML. Values are
synthetic demonstration data as documented in the package README and quality
report.

## Run on macOS

```bash
cd erp-datawarehouse-design
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
export DATA_MODE=csv
export CSV_DATA_DIR=erp_semester5_etl_package
python3 app.py
```

Open http://127.0.0.1:5000. CSV mode does not connect to MySQL.

## API

Authenticated JSON endpoints include `/api/kpis`, `/api/students`,
`/api/student/<Enrollment_No>`, and `/api/data-quality`. Student collection
queries support `q`, `department`, `section`, `semester`, `page`, and
`page_size` (maximum 200).

## Tests

```bash
python3 -m unittest test_csv_mode.py
```

The MySQL scripts remain available for hosted-database verification but require
a configured MySQL server. Set `DATA_MODE=mysql` and the `MYSQL_*` environment
variables only when using that mode. The supplied schema is non-destructive;
review import scripts before running them against an existing database.

## Data architecture

`data_store.py` validates and caches the four package CSVs, enforces
`Enrollment_No` references and financial/marks reconciliation, and exposes
shared profile and KPI services. Raw CSVs are preserved. A future ETL command
should write cleaned and rejected outputs separately rather than overwrite raw
files. See [decisions.md](decisions.md) for design tradeoffs.
