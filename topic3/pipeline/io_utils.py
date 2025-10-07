import logging
import pandas as pd
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

def iter_chunks(
        path: Path,
        usecols: list[str],
        dtype: dict,
        chunksize: int
    ) -> Iterable[pd.DataFrame]:
    return pd.read_csv(
        path,
        compression="gzip",
        low_memory=False,
        chunksize=chunksize,
        usecols=usecols,
        dtype=dtype,
    )

def write_chunk(
        out_path: Path,
        df: pd.DataFrame,
        write_header: bool
    ) -> None:
    # Ensure parent exists
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(
        out_path,
        mode=("w" if write_header else "a"),
        index=False,
        header=write_header,
        compression="gzip",
    )
    logger.debug("Wrote %s rows to %s (header=%s)", len(df), out_path, write_header)

def move_file(src: Path, dest: Path) -> None:
    """Move a file from src to dest, creating parent directories as needed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dest)
    logger.debug("Moved %s to %s", src, dest)
