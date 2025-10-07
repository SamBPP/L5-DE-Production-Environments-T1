import pandas as pd

def select_keep_cols(df: pd.DataFrame,keep_cols: list[str]) -> pd.DataFrame:
    missing = [c for c in keep_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df[keep_cols]

def sanity_checks(df: pd.DataFrame) -> None:
    # applicant_income_000s should be >= 0 for >= 90% of rows
    share_nonneg = (df["applicant_income_000s"] >= 0).mean()
    if share_nonneg < 0.90:
        raise ValueError("More than 10% of applicant_income_000s is missing or negative")
    
    for col in ["action_taken", "respondent_id"]:
        if df[col].isna().sum() > 0:
            raise ValueError(f"Some value in {col} are missing")
    
    if not df["action_taken"].isin(range(1,9)).all():
        raise ValueError("Unexpected value in action_taken (not in 1-8)")