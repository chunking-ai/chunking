from pathlib import Path

from chunking.base import Chunk
from chunking.parser.directory import DirectoryParser
from chunking.router import FileCoordinator

path = str(Path(__file__).parent.parent)
_file = FileCoordinator()


def test_directory():
    root = _file.as_root_chunk(path)
    chunks = DirectoryParser.run(root)
    chunk = chunks[0]
    assert isinstance(chunk, Chunk)
