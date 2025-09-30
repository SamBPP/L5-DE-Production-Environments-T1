import gzip
from pathlib import Path
import pandas as pd

def _import():
    from pipeline.runner import list_unprocessed_files, process_all_to_master
    return list_unprocessed_files, process_all_to_master

def _write_gz_csv(path: Path, df: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        df.to_csv(f, index=False)

def test_list_unprocessed_files(tmp_path):
    list_unprocessed_files, _ = _import()
    in_dir = tmp_path / "ingest"
    proc_dir = tmp_path / "processed"
    in_dir.mkdir()
    proc_dir.mkdir()

    a = in_dir / "a.csv.gz"
    b = in_dir / "b.csv.gz"
    a.write_text("x")
    b.write_text("y")
    (proc_dir / "b.csv.gz").write_text("done")  # simulate processed

    found = list_unprocessed_files(in_dir, proc_dir, "*.csv.gz")
    assert [p.name for p in found] == ["a.csv.gz"]

def test_process_all_to_master_happy_path(tmp_path):
    _, process_all_to_master = _import()
    in_dir = tmp_path / "ingest"
    proc_dir = tmp_path / "processed"
    out_dir = tmp_path / "out"
    in_dir.mkdir(); proc_dir.mkdir(); out_dir.mkdir()

    cols = ["action_taken","state_abbr","respondent_id","loan_amount_000s","applicant_income_000s"]
    df1 = pd.DataFrame([[1,"NY","r1",100,50],[2,"CA","r2",200,30]], columns=cols)
    df2 = pd.DataFrame([[3,"TX","r3",300,10]], columns=cols)

    _write_gz_csv(in_dir / "part1.csv.gz", df1)
    _write_gz_csv(in_dir / "part2.csv.gz", df2)

    master_path = out_dir / "master.csv.gz"
    res = process_all_to_master(
        in_dir=in_dir,
        processed_path=proc_dir,
        pattern="*.csv.gz",
        master_path=master_path,
        fresh_master=True
    )

    assert res == master_path
    with gzip.open(master_path, "rt", encoding="utf-8") as f:
        master_df = pd.read_csv(f)

    assert master_df.shape == (3, len(cols))
    assert sorted(p.name for p in proc_dir.glob("*.csv.gz")) == ["part1.csv.gz","part2.csv.gz"]

def test_process_all_to_master_idempotent_when_no_new_files(tmp_path):
    _, process_all_to_master = _import()
    in_dir = tmp_path / "ingest"; in_dir.mkdir()
    proc_dir = tmp_path / "processed"; proc_dir.mkdir()
    out_dir = tmp_path / "out"; out_dir.mkdir()

    cols = ["action_taken","state_abbr","respondent_id","loan_amount_000s","applicant_income_000s"]
    df = pd.DataFrame([[1,"NY","r1",100,50]], columns=cols)
    _write_gz_csv(in_dir / "file.csv.gz", df)

    master_path = out_dir / "master.csv.gz"
    process_all_to_master(in_dir, proc_dir, "*.csv.gz", master_path, fresh_master=True)
    process_all_to_master(in_dir, proc_dir, "*.csv.gz", master_path, fresh_master=False)

    with gzip.open(master_path, "rt", encoding="utf-8") as f:
        master_df = pd.read_csv(f)
    assert master_df.shape == (1, len(cols))
