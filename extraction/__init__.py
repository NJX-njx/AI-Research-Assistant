# extraction module
from .text_extractor import chunk_text, extract_text_from_pdf
from .vision_extractor import (
    describe_figure,
    extract_figure_references,
    extract_image_paths_from_markdown,
    associate_figures_with_text,
    describe_figure_with_association,
)
from .paddleocr_mcp_client import (
    PaddleOCRVLClient,
    parse_pdf,
)
try:
    from .image_extractor import (
        PDFImageExtractor,
        extract_images_from_pdf,
        match_images_to_figures,
    )
except ImportError:  # Optional dependency (PyMuPDF)
    PDFImageExtractor = None
    extract_images_from_pdf = None
    match_images_to_figures = None

__all__ = [
    "chunk_text",
    "extract_text_from_pdf",
    "describe_figure",
    "extract_figure_references",
    "extract_image_paths_from_markdown",
    "associate_figures_with_text",
    "describe_figure_with_association",
    "PaddleOCRVLClient",
    "parse_pdf",
    "PDFImageExtractor",
    "extract_images_from_pdf",
    "match_images_to_figures",
]
