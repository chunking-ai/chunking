from chunking.base import BaseOperation, Chunk, ChunkGroup, CType


class RapidOCRImageText(BaseOperation):

    @classmethod
    def run(cls, chunk: Chunk | ChunkGroup, **kwargs) -> ChunkGroup:
        """OCR text in image with RapidOCR engine."""
        from rapidocr import RapidOCR

        engine = RapidOCR(params={"Global.lang_det": "en_mobile", "Global.lang_rec": "en_mobile"})

        # Resolve chunk
        if isinstance(chunk, Chunk):
            chunk = ChunkGroup(chunks=[chunk])

        output = ChunkGroup()
        for mc in chunk:
            ocr_result = engine(mc.origin.location)
            for idx, text in enumerate(ocr_result.txts):
                print("-", idx, text)
            import pdb; pdb.set_trace()
            print()

    @classmethod
    def py_dependency(cls) -> list[str]:
        return ["rapidocr"]
