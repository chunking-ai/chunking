from pathlib import Path

from chunking.base import Chunk
from chunking.mime import mime_csv
from chunking.parser.csv import CsvParser

file_path = str(Path(__file__).parent.parent / "assets" / "contains_empty_cell.csv")


def test_parse_csv():
    root = mime_csv.as_root_chunk(file_path)
    chunks = CsvParser.run(root)
    chunk = chunks[0]
    assert isinstance(chunk, Chunk)
