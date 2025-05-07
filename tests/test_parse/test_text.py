from pathlib import Path

from chunking.base import Chunk
from chunking.controller import Controller
from chunking.parser.text import TextParser

file_path = str(Path(__file__).parent.parent / "assets" / "long.txt")
ctrl = Controller()


def test_text():
    root = ctrl.as_root_chunk(file_path)
    chunks = TextParser.run(root)
    chunk = chunks[0]
    assert isinstance(chunk, Chunk)
