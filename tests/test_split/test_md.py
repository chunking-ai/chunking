from pathlib import Path

from chunking.controller import Controller
from chunking.split.md import MarkdownSplitByHeading

md_path1 = str(Path(__file__).parent.parent / "assets" / "lz.md")

ctrl = Controller()


def test_split_heading():
    root = ctrl.as_root_chunk(md_path1)
    with open(md_path1) as f:
        root.content = f.read()
    chunks = MarkdownSplitByHeading.run(root, min_chunk_size=100)
    assert len(chunks) > 0
