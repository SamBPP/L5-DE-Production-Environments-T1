from pathlib import Path

DATA_DIR = Path("../../Data/ingest")
PROCESSED_DIR = Path("../../Data/processed")
OUTPUT_DIR = Path("output")
MASTER_OUTPUT = OUTPUT_DIR / "hmda_master.csv.gz"

FILE_GLOB = "*.csv.gz" # only gzipped CSVs
CHUNK_SIZE = 100_000

KEEP_COLS = [
    "action_taken",
    "state_abbr",
    "respondent_id",
    "loan_amount_000s",
    "applicant_income_000s"
]

DTYPES = {
    "action_taken": "Int64",
    "state_abbr": "string",
    "respondent_id": "string",
    "loan_amount_000s": "Int64",
    "applicant_income_000s": "Int64",
}