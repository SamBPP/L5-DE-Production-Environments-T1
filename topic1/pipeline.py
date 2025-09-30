import os
import pandas as pd

FILE_PATH = '../input/'
KEEP_COLS = [
    "action_taken",
    "state_abbr",
    "respondent_id",
    "loan_amount_000s",
    "applicant_income_000s"
]

def _select_keep_cols(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in KEEP_COLS if c not in df.columns]
    if cols:
        raise ValueError(f"Missing columns: {cols}")
    return df[KEEP_COLS]

def _sanity_checks(df: pd.DataFrame) -> None:
    if (df["applicant_income_000s"] >= 0).mean() < 0.90:
        assert False, "More than 10% of applicant_income_000s is missing or negative"
    for col in ["action_taken", "respondent_id"]:
        if df[col].isna().sum() > 0:
            assert False, f"Some value in {col} are missing"
    if df["action_taken"].isin(range(1,9)).mean() < 1:
        assert False, "Unexpected value in action_taken"

def main():
    create_file = True
    for n, file in enumerate(os.listdir(FILE_PATH)):
        for i, df in enumerate(pd.read_csv(os.path.join(FILE_PATH, file),
                                        chunksize=100_000,
                                        compression='gzip',
                                        low_memory=False)):
            print(f"File {n+1} | Chunk {i+1} - {df.shape}")
            df_filt = _select_keep_cols(df)
            _sanity_checks(df_filt)

            df_filt.to_csv('output/clean_2010HMDA.csv.gz',
                        mode=('w' if create_file else 'a'),
                        index=False,
                        header=create_file,
                        compression='gzip')
            create_file = False

if __name__ == "__main__":
    main()