from concurrent.futures import ProcessPoolExecutor

from img2table.document import PDF
from img2table.ocr.pdf import PdfOCR
from img2table.tables.image import TableImage

MIN_CONFIDENCE = 50


def detect_tables_single_page(img):
    try:
        table_image = TableImage(img=img, min_confidence=MIN_CONFIDENCE)
        output = table_image.extract_tables(
            implicit_rows=False,
            implicit_columns=False,
            borderless_tables=True,
        )
    except:  # noqa
        output = []
    return output


def img2table_get_tables(path: str, executor: ProcessPoolExecutor):
    # Extract tables from document
    doc = PDF(path)
    ocr = PdfOCR()

    futures = [executor.submit(detect_tables_single_page, img) for img in doc.images]
    detected_tables = [f.result() for f in futures]

    tables = {idx: table_list for idx, table_list in enumerate(detected_tables)}
    tables = doc.get_table_content(
        ocr=ocr, tables=tables, min_confidence=MIN_CONFIDENCE
    )

    output_tables = {}
    for page_idx, page_tables in tables.items():
        page_image_w, page_image_h = doc.images[page_idx].shape[:2]
        output_tables[page_idx] = [
            {
                "text": table.html,
                "title": table.title if table.title else "",
                "bbox": [
                    table.bbox.x1 / page_image_w,
                    table.bbox.y1 / page_image_h,
                    table.bbox.x2 / page_image_w,
                    table.bbox.y2 / page_image_h,
                ],
                "type": "table",
                "rows": [
                    [
                        [
                            cell.bbox.x1 / page_image_w,
                            cell.bbox.y1 / page_image_h,
                            cell.bbox.x2 / page_image_w,
                            cell.bbox.y2 / page_image_h,
                        ]
                        for cell in row
                    ]
                    for row in table.content.values()
                ],
            }
            for table in page_tables
        ]
    return output_tables
