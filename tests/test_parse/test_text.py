from pathlib import Path

from chunking.base import Chunk
from chunking.parser.text import TextParser
from chunking.router import FileCoordinator

file_path = str(Path(__file__).parent.parent / "assets" / "long.txt")
_file = FileCoordinator()


def test_text():
    root = _file.as_root_chunk(file_path)
    chunks = TextParser.run(root)
    chunk = chunks[0]
    assert isinstance(chunk, Chunk)
