import gzip
import pandas as pd
from pathlib import Path

def _import():
    from pipeline.io_utils import write_chunk, move_file, iter_chunks
    return write_chunk, move_file, iter_chunks

def test_write_chunk_header_and_append(tmp_path):
    write_chunk, _, _ = _import()
    df1 = pd.DataFrame({"a": [1,2], "b": [3,4]})
    df2 = pd.DataFrame({"a": [5], "b": [6]})
    out = tmp_path / "out.csv.gz"

    write_chunk(out, df1, write_header=True)
    write_chunk(out, df2, write_header=False)

    with gzip.open(out, "rt", encoding="utf-8") as f:
        back = pd.read_csv(f)

    assert list(back.columns) == ["a", "b"]
    assert back.shape == (3, 2)

def test_move_file(tmp_path):
    _, move_file, _ = _import()
    src = tmp_path / "src.txt"
    src.write_text("hello")
    dest = tmp_path / "nested" / "dest.txt"

    move_file(src, dest)
    assert not src.exists()
    assert dest.read_text() == "hello"

def test_iter_chunks_roundtrip(tmp_path):
    _, _, iter_chunks = _import()
    data = pd.DataFrame({"x":[1,2,3,4], "y":[10,20,30,40]})
    src = tmp_path / "data.csv.gz"
    with gzip.open(src, "wt", encoding="utf-8") as f:
        data.to_csv(f, index=False)

    chunks = list(iter_chunks(src, usecols=["x","y"], dtype={"x":"Int64","y":"Int64"}, chunksize=2))
    assert len(chunks) == 2
    assert chunks[0].shape == (2,2)
    assert chunks[1].shape == (2,2)
