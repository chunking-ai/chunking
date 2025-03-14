"""Convert any document to Markdown."""

import re
import time
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from functools import wraps
from pathlib import Path
from typing import Any

import numpy as np
from pdf_table import img2table_get_tables
from pdftext.extraction import dictionary_output
from sklearn.cluster import KMeans


def elapsed_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"Elapsed time for {func.__name__}: {elapsed:.4f} seconds")
        return result

    return wrapper


def scale_bbox(bbox: list[float], width: float, height: float) -> list[float]:
    return [bbox[0] / width, bbox[1] / height, bbox[2] / width, bbox[3] / height]


def parsed_pdf_to_markdown(
    pages: list[dict[str, Any]],
) -> list[str]:  # noqa: C901, PLR0915
    """Convert a PDF parsed with pdftext to Markdown."""

    # @elapsed_time
    def add_heading_level_metadata(
        pages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:  # noqa: C901
        """Add heading level metadata to a PDF parsed with pdftext."""

        def extract_font_size(span: dict[str, Any]) -> float:
            """Extract the font size from a text span."""
            font_size: float = 1.0
            if (
                span["font"]["size"] > 1
            ):  # A value of 1 appears to mean "unknown" in pdftext.
                font_size = span["font"]["size"]
            elif digit_sequences := re.findall(r"\d+", span["font"]["name"] or ""):
                font_size = float(digit_sequences[-1])
            elif (
                "\n" not in span["text"]
            ):  # Occasionally a span can contain a newline character.
                if round(span["rotation"]) in (0.0, 180.0, -180.0):
                    font_size = span["bbox"][3] - span["bbox"][1]
                elif round(span["rotation"]) in (90.0, -90.0, 270.0, -270.0):
                    font_size = span["bbox"][2] - span["bbox"][0]
            return font_size

        # Copy the pages.
        pages = deepcopy(pages)
        # Extract an array of all font sizes used by the text spans.
        font_sizes = np.asarray(
            [
                extract_font_size(span)
                for page in pages
                for block in page["blocks"]
                for line in block["lines"]
                for span in line["spans"]
            ]
        )
        font_sizes = np.round(font_sizes * 2) / 2
        unique_font_sizes, counts = np.unique(font_sizes, return_counts=True)
        # Determine the paragraph font size as the mode font size.
        tiny = unique_font_sizes < min(5, np.max(unique_font_sizes))
        counts[tiny] = -counts[tiny]
        mode = np.argmax(counts)
        counts[tiny] = -counts[tiny]
        mode_font_size = unique_font_sizes[mode]
        # Determine (at most) 6 heading font sizes
        # by clustering font sizes larger than the mode.
        heading_font_sizes = unique_font_sizes[mode + 1 :]
        if len(heading_font_sizes) > 0:
            heading_counts = counts[mode + 1 :]
            kmeans = KMeans(n_clusters=min(6, len(heading_font_sizes)), random_state=42)
            kmeans.fit(heading_font_sizes[:, np.newaxis], sample_weight=heading_counts)
            heading_font_sizes = np.sort(np.ravel(kmeans.cluster_centers_))[::-1]
        # Add heading level information to the text spans and lines.
        for page in pages:
            for block in page["blocks"]:
                for line in block["lines"]:
                    if "md" not in line:
                        line["md"] = {}
                    heading_level = np.zeros(8)  # 0-5: <h1>-<h6>, 6: <p>, 7: <small>
                    for span in line["spans"]:
                        if "md" not in span:
                            span["md"] = {}
                        span_font_size = extract_font_size(span)
                        if span_font_size < mode_font_size:
                            idx = 7
                        elif span_font_size == mode_font_size:
                            idx = 6
                        else:
                            idx = np.argmin(
                                np.abs(heading_font_sizes - span_font_size)
                            )  # type: ignore[assignment]
                        span["md"]["heading_level"] = idx + 1
                        heading_level[idx] += len(span["text"])
                    line["md"]["heading_level"] = np.argmax(heading_level) + 1
        return pages

    # @elapsed_time
    def add_emphasis_metadata(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add emphasis metadata such as
        bold and italic to a PDF parsed with pdftext."""
        # Copy the pages.
        pages = deepcopy(pages)
        # Add emphasis metadata to the text spans.
        for page in pages:
            for block in page["blocks"]:
                for line in block["lines"]:
                    if "md" not in line:
                        line["md"] = {}
                    for span in line["spans"]:
                        if "md" not in span:
                            span["md"] = {}
                        span["md"]["bold"] = (
                            span["font"]["weight"] > 500
                        )  # noqa: PLR2004
                        span["md"]["italic"] = (
                            "ital" in (span["font"]["name"] or "").lower()
                        )
                    line["md"]["bold"] = all(
                        span["md"]["bold"]
                        for span in line["spans"]
                        if span["text"].strip()
                    )
                    line["md"]["italic"] = all(
                        span["md"]["italic"]
                        for span in line["spans"]
                        if span["text"].strip()
                    )
        return pages

    def strip_page_numbers(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Strip page numbers from a PDF parsed with pdftext."""
        # Copy the pages.
        pages = deepcopy(pages)
        # Remove lines that only contain a page number.
        for page in pages:
            for block in page["blocks"]:
                block["lines"] = [
                    line
                    for line in block["lines"]
                    if not re.match(
                        r"^\s*[#0]*\d+\s*$",
                        "".join(span["text"] for span in line["spans"]),
                    )
                ]
        return pages

    # @elapsed_time
    def convert_to_markdown(
        pages: list[dict[str, Any]], return_blocks=True
    ) -> list[str]:  # noqa: C901, PLR0912
        """Convert a list of pages to Markdown."""
        pages_md = []
        output_pages = []

        for page in pages:
            page_md = ""
            output_blocks = []

            page_w, page_h = page["width"], page["height"]
            for block in page["blocks"]:
                block_text = ""
                is_block_has_header = False
                for line in block["lines"]:
                    # Build the line text and style the spans.
                    line_text = ""
                    for span in line["spans"]:
                        if (
                            not line["md"]["bold"]
                            and not line["md"]["italic"]
                            and span["md"]["bold"]
                            and span["md"]["italic"]
                        ):
                            line_text += f"***{span['text']}***"
                        elif not line["md"]["bold"] and span["md"]["bold"]:
                            line_text += f"**{span['text']}**"
                        elif not line["md"]["italic"] and span["md"]["italic"]:
                            line_text += f"*{span['text']}*"
                        else:
                            line_text += span["text"]
                    # Add emphasis to the line (if it's not a heading or whitespace).
                    line_text = line_text.rstrip()
                    line_is_whitespace = not line_text.strip()
                    if "heading_level" in line["md"]:
                        line_is_heading = (
                            line["md"]["heading_level"] <= 6
                        )  # noqa: PLR2004
                        if line_is_heading:
                            is_block_has_header = True
                    else:
                        line_is_heading = False

                    if not line_is_heading and not line_is_whitespace:
                        if line["md"]["bold"] and line["md"]["italic"]:
                            line_text = f"***{line_text}***"
                        elif line["md"]["bold"]:
                            line_text = f"**{line_text}**"
                        elif line["md"]["italic"]:
                            line_text = f"*{line_text}*"
                    # Set the heading level.
                    if line_is_heading and not line_is_whitespace:
                        line_text = f"{'#' * line['md']['heading_level']} {line_text}"
                    line_text += "\n"
                    block_text += line_text
                block_text = block_text.rstrip()
                page_md += block_text + "\n\n"

                output_blocks.append(
                    {
                        "text": block_text,
                        "bbox": scale_bbox(block["bbox"], page_h, page_w),
                        "type": "header" if is_block_has_header else "text",
                    }
                )

            page["blocks"] = output_blocks
            # page.pop("bbox")
            output_pages.append(page)
            pages_md.append(page_md.strip())
        return output_pages

    def merge_split_headings(pages: list[str]) -> list[str]:
        """Merge headings that are split across lines."""

        def _merge_split_headings(match: re.Match[str]) -> str:
            atx_headings = [
                line.strip("# ").strip() for line in match.group().splitlines()
            ]
            return f"{match.group(1)} {' '.join(atx_headings)}\n\n"

        pages_md = [
            re.sub(
                r"^(#+)[ \t]+[^\n]+\n+(?:^\1[ \t]+[^\n]+\n+)+",
                _merge_split_headings,
                page,
                flags=re.MULTILINE,
            )
            for page in pages
        ]
        return pages_md

    # Add heading level metadata.
    pages = add_heading_level_metadata(pages)
    # Add emphasis metadata.
    pages = add_emphasis_metadata(pages)
    # Convert the pages to Markdown.
    pages = convert_to_markdown(pages)
    # Merge headings that are split across lines.
    # pages_md = merge_split_headings(pages_md)
    return pages


def parition_pdf(
    doc_path: Path, executor: ProcessPoolExecutor, extract_table=False
) -> str:
    """Convert any document to GitHub Flavored Markdown."""
    # Parse the PDF with pdftext and convert it to Markdown.
    pages = dictionary_output(
        doc_path,
        sort=True,
        keep_chars=False,
        workers=None,
    )
    pages = parsed_pdf_to_markdown(pages)

    # Improve Markdown quality.
    # doc = mdformat.text(doc)

    if extract_table:
        tables = img2table_get_tables(doc_path, executor=executor)

    for idx, page in enumerate(pages):
        if extract_table:
            text_blocks = page["blocks"]
            table_blocks = tables.get(idx, [])

            # filter blocks overlap with tables base on bbox
            for table in table_blocks:
                table_bbox = table["bbox"]
                text_blocks = [
                    block
                    for block in text_blocks
                    if (
                        block["bbox"][0] >= table_bbox[2]
                        or block["bbox"][1] >= table_bbox[3]
                        or block["bbox"][2] <= table_bbox[0]
                        or block["bbox"][3] <= table_bbox[1]
                    )
                ]
            page["blocks"] = text_blocks + table_blocks

    return pages


def pages_to_markdown(pages: list[dict[str, Any]]) -> list[str]:
    """Convert a list of pages to Markdown."""
    md_text = ""
    for page in pages:
        for block in page["blocks"]:
            md_text += block["text"] + "\n\n"
    return md_text
