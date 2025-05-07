from pathlib import Path

from chunking.base import Chunk
from chunking.controller import Controller
from chunking.parser.pandoc_engine import PandocEngine
from chunking.split.propositionizer import Propositionizer

docx_path = str(Path(__file__).parent.parent / "assets" / "with_image.docx")

ctrl = Controller()


def test_propositionizer():
    # parse the file
    root = ctrl.as_root_chunk(docx_path)
    chunks = PandocEngine.run(root)
    chunk = chunks[0]

    # run propositionizer
    temp = chunk.child.next.next.next.next.next.next.next.clone()
    output = Propositionizer.run(temp)

    assert isinstance(output[0], Chunk)
