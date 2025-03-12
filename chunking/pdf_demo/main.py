import time
from concurrent.futures import ProcessPoolExecutor
from pprint import pprint

import pymupdf4llm
from pdf_parser import parition_pdf
from plot import plot_blocks

if __name__ == "__main__":
    executor = ProcessPoolExecutor()

    # download from https://arxiv.org/pdf/1706.03762
    # or https://www.w3.org/WAI/WCAG20/Techniques/working-examples/PDF20/table.pdf
    input_path = "1706.03762.pdf"
    # input_path = "table.pdf"
    debug_path = "debug"

    start_time = time.time()
    pages = parition_pdf(input_path, executor=executor, extract_table=True)
    num_pages = len(pages)
    end_time = time.time()

    plot_blocks(input_path, pages, debug_path)
    pprint(pages)
    print("WIP parser")
    print(f"Average time per page: {(end_time - start_time) / num_pages:.2f}s")

    executor.shutdown()

    start_time = time.time()
    text = pymupdf4llm.to_markdown(input_path)
    end_time = time.time()
    print("PyMuPDF4LLM")
    print(f"Average time per page: {(end_time - start_time) / num_pages:.2f}s")
