from pathlib import Path

from chunking.base import Chunk
from chunking.controller import Controller
from chunking.parser.pandoc_engine import PandocEngine
from chunking.split.agentic_chunker import AgenticChunker
from chunking.split.split import FlattenToMarkdown

docx_path = str(Path(__file__).parent.parent / "assets" / "with_image.docx")

ctrl = Controller()


def test_agentic_chunker():
    # parse the file
    root = ctrl.as_root_chunk(docx_path)
    chunks = PandocEngine.run(root)
    chunk = chunks[0]

    # flatten to markdown
    flattened = FlattenToMarkdown.run(chunk, max_size=512)
    output = AgenticChunker.run(flattened[0].clone(next=None))
    assert isinstance(output[0], Chunk)
