import gzip
from pathlib import Path
import pandas as pd
import pytest

@pytest.fixture
def sample_columns():
    return ["action_taken", "state_abbr", "respondent_id", "loan_amount_000s", "applicant_income_000s"]

@pytest.fixture
def good_df(sample_columns):
    data = [
        [1, "NY", "r1", 100, 50],
        [2, "CA", "r2", 200, 80],
        [3, "TX", "r3", 300, 0],
    ]
    return pd.DataFrame(data, columns=sample_columns)

@pytest.fixture
def bad_df_neg_income(sample_columns):
    data = [
        [1, "NY", "r1", 100, -1],
        [2, "CA", "r2", 200, -5],
        [3, "TX", "r3", 300, 0],
        [4, "FL", "r4", 400, -2],
        [5, "WA", "r5", 500, -3],
        [6, "OR", "r6", 600, -10],
        [7, "IL", "r7", 700, -20],
        [8, "AZ", "r8", 800, -30],
        [1, "NV", "r9", 900, -40],
        [2, "UT", "r10", 1000, -50],
    ]
    return pd.DataFrame(data, columns=sample_columns)

@pytest.fixture
def make_gz_csv(tmp_path):
    """Write a DataFrame to gzipped CSV and return the path."""
    import gzip
    def _writer(df, name="part.csv.gz"):
        out = tmp_path / name
        with gzip.open(out, "wt", encoding="utf-8") as f:
            df.to_csv(f, index=False)
        return out
    return _writer
