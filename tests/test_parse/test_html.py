from pathlib import Path

from chunking.base import Chunk
from chunking.mime import mime_html
from chunking.parser.html import PandocHtmlParser

html_path = str(Path(__file__).parent.parent / "assets" / "long.html")


def test_pandoc_html():
    root = mime_html.as_root_chunk(html_path)
    chunks = PandocHtmlParser.run(root)
    chunk = chunks[0]
    assert isinstance(chunk, Chunk)
