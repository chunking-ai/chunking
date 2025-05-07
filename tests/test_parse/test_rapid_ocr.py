from pathlib import Path

from chunking.base import Chunk
from chunking.mime import mime_jpg
from chunking.parser.image import RapidOCRImageText

jpg_path1 = str(Path(__file__).parent.parent / "assets" / "with_table.jpg")


def test_parse_jpg():
    root = mime_jpg.as_root_chunk(jpg_path1)
    chunks = RapidOCRImageText.run(root)
    chunk = chunks[0]
    chunk.print_graph()
    assert isinstance(chunk, Chunk)
