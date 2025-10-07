import logging
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from .config import DATA_DIR, PROCESSED_DIR, MASTER_OUTPUT, FILE_GLOB, CHUNK_SIZE, KEEP_COLS, DTYPES
from .io_utils import iter_chunks, write_chunk
from .transform import select_keep_cols, sanity_checks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def list_unprocessed_files(in_dir: Path, processed_path: Path, pattern: str) -> list[Path]:
    """Return files in in_dir whose filenames are NOT present in processed_path."""
    processed_names = {p.name for p in processed_path.glob(pattern)}
    candidates = sorted(in_dir.glob(pattern))
    return [p for p in candidates if p.name not in processed_names]

def process_file_into_master(
        src_path: Path,
        master_path: Path,
        header_written: bool,
        chunk_size: int = CHUNK_SIZE
    ) -> bool:
    """Append-cleaned chunks from a single source file into the master file."""
    logger.info("→ %s → %s", src_path.name, master_path.name)
    rows = 0
    for i, chunk in enumerate(iter_chunks(src_path, usecols=KEEP_COLS, dtype=DTYPES, chunksize=chunk_size), start=1):
        logger.info("Chunk %d - %s rows", i, len(chunk))
        df = select_keep_cols(chunk, KEEP_COLS)
        sanity_checks(df)
        write_chunk(master_path, df, write_header=not header_written)
        header_written = True
        rows += len(df)
    
    return header_written, rows

def safe_move_to_processed(src: Path, processed_path: Path) -> Path:
    """Move src into processed_path; if name collides, add a timestamp suffix."""
    dest = processed_path / src.name
    if dest.exists():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        # Keep it simple: append .<ts> after the full name (works fine with .csv.gz)
        dest = processed_path / f"{src.name}.{ts}"
    shutil.move(str(src), str(dest))  # works across filesystems
    return dest

def process_all_to_master(
        in_dir: Path = DATA_DIR,
        processed_path: Path = PROCESSED_DIR,
        pattern: str = FILE_GLOB,
        master_path: Path = MASTER_OUTPUT,
        fresh_master: bool = False
    ):
    
    new_files = list_unprocessed_files(in_dir, processed_path, FILE_GLOB)
    if not new_files:
        logger.warning("No files found in %s matching %s", in_dir, pattern)
        return master_path

    # (Re)create the master if requested
    if fresh_master and master_path.exists():
        logger.info("Removing existing master %s for fresh build", master_path)
        master_path.unlink()

    header_written = master_path.exists()

    for idx, src in enumerate(new_files, start=1):
        logger.info("File %d/%d: %s", idx, len(new_files), src.name)
        header_written, rows = process_file_into_master(src, master_path, header_written)
        logger.info("   appended %s rows from %s", rows, src.name)
        moved = safe_move_to_processed(src, processed_path)
        logger.info("Moved to processed/: %s", moved.name)
    
    logger.info("Master ready at %s", master_path)
    return master_path

if __name__ == "__main__":
    # Minimal CLI: python -m pipeline.runner [optional: directory]
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--pattern", type=str, default=FILE_GLOB)
    parser.add_argument("--fresh-master", action="store_true", help="Start master from scratch")
    args = parser.parse_args()
    process_all_to_master(args.in_dir, args.processed_dir, args.pattern, MASTER_OUTPUT, fresh_master=args.fresh_master)
