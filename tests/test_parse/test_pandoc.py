from pathlib import Path

from chunking.base import Chunk
from chunking.mime import mime_docx
from chunking.parse.pandoc_engine import PandocEngine

docx_path = str(Path(__file__).parent.parent / "assets" / "with_image.docx")


def test_pandoc_docx():
    root = mime_docx.as_root_chunk(docx_path)
    chunks = PandocEngine.run(root)
    chunk = list(chunks.iter_groups())[0][0]
    assert isinstance(chunk, Chunk)
