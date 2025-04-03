from pathlib import Path

from chunking.mime import mime_jpg
from chunking.parse.image import RapidOCRImageText

jpg01 = str(Path(__file__).parent.parent / "assets" / "with_table.jpg")


def test_jpg():
    root = mime_jpg.as_root_chunk(jpg01)
    chunks = RapidOCRImageText.run(root)
    # chunk = list(chunks.iter_groups())[0][0]
    # assert len(chunks) > 0


if __name__ == "__main__":
    test_jpg()
