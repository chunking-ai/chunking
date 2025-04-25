from pathlib import Path

from chunking.base import Chunk
from chunking.mime import mime_epub
from chunking.parse.pandoc_engine import PandocEngine

file_path = str(Path(__file__).parent.parent / "assets" / "long.epub")


def test_pandoc_epub():
    root = mime_epub.as_root_chunk(file_path)
    chunks = PandocEngine.run(root)
    chunk = chunks[0]
    assert isinstance(chunk, Chunk)
