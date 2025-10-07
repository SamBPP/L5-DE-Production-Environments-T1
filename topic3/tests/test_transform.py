import pandas as pd
import pytest

# The tests expect these functions in your package:
# from pipeline.transform import select_keep_cols, sanity_checks
# To avoid breaking import if running these tests standalone,
# we do a lazy import inside each test.
def _import():
    from pipeline.transform import select_keep_cols, sanity_checks
    return select_keep_cols, sanity_checks

def test_select_keep_cols_ok(good_df):
    select_keep_cols, _ = _import()
    keep = ["respondent_id", "action_taken"]
    trimmed = select_keep_cols(good_df, keep)
    assert list(trimmed.columns) == keep
    assert len(trimmed) == len(good_df)

def test_select_keep_cols_missing():
    select_keep_cols, _ = _import()
    df = pd.DataFrame({"a": [1], "b": [2]})
    with pytest.raises(ValueError) as e:
        select_keep_cols(df, ["a", "c"])
    assert "Missing columns" in str(e.value)

def test_sanity_checks_pass(good_df):
    _, sanity_checks = _import()
    sanity_checks(good_df)

def test_sanity_checks_fail_on_neg_income(bad_df_neg_income):
    _, sanity_checks = _import()
    with pytest.raises(ValueError) as e:
        sanity_checks(bad_df_neg_income)
    assert "applicant_income_000s" in str(e.value)

def test_sanity_checks_fail_on_nulls(good_df):
    _, sanity_checks = _import()
    bad = good_df.copy()
    bad.loc[0, "respondent_id"] = None
    with pytest.raises(ValueError) as e:
        sanity_checks(bad)
    assert "respondent_id" in str(e.value)

def test_sanity_checks_fail_on_invalid_action(good_df):
    _, sanity_checks = _import()
    bad = good_df.copy()
    bad.loc[0, "action_taken"] = 99
    with pytest.raises(ValueError) as e:
        sanity_checks(bad)
    assert "action_taken" in str(e.value)
