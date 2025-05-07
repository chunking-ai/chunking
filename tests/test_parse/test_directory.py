from pathlib import Path

from chunking.base import Chunk
from chunking.controller import Controller
from chunking.parser.directory import DirectoryParser

path = str(Path(__file__).parent.parent)
ctrl = Controller()


def test_directory():
    root = ctrl.as_root_chunk(path)
    chunks = DirectoryParser.run(root)
    chunk = chunks[0]
    assert isinstance(chunk, Chunk)
