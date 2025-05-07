from pathlib import Path

from chunking.base import Chunk
from chunking.controller import Controller
from chunking.parser.pandoc_engine import PandocEngine
from chunking.split.split import FlattenToMarkdown

docx_path = str(Path(__file__).parent.parent / "assets" / "with_image.docx")

ctrl = Controller()


def test_flatten():
    root = ctrl.as_root_chunk(docx_path)
    chunks = PandocEngine.run(root)
    flattened = FlattenToMarkdown.run(chunks[0], max_size=512)
    assert isinstance(flattened[0], Chunk)
