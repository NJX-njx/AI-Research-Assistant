# -*- coding: utf-8 -*-
"""
PDF Image Extraction Module
===========================
Extracts images from PDF files using PyMuPDF (fitz).
Handles various image formats and provides fallback mechanisms.
"""
import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import fitz  # PyMuPDF


class PDFImageExtractor:
    """Extract images from PDF files."""
    
    def __init__(self, output_dir: str = "extracted_images"):
        """
        Initialize the image extractor.
        
        Args:
            output_dir: Directory to save extracted images
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def extract_images(self, pdf_path: str, min_width: int = 100, min_height: int = 100) -> List[Dict]:
        """
        Extract all images from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            min_width: Minimum image width to extract (filter out tiny images)
            min_height: Minimum image height to extract
            
        Returns:
            List of dicts with image info: {path, page, index, width, height, format}
        """
        if not os.path.exists(pdf_path):
            print(f"[ImageExtractor] PDF not found: {pdf_path}")
            return []
        
        extracted = []
        pdf_name = Path(pdf_path).stem
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]
                    
                    try:
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        width = base_image["width"]
                        height = base_image["height"]
                        
                        # Filter small images (icons, bullets, etc.)
                        if width < min_width or height < min_height:
                            continue
                        
                        # Generate unique filename
                        img_hash = hashlib.md5(image_bytes).hexdigest()[:8]
                        filename = f"{pdf_name}_page{page_num + 1}_img{img_index + 1}_{img_hash}.{image_ext}"
                        filepath = os.path.join(self.output_dir, filename)
                        
                        # Save image
                        with open(filepath, "wb") as f:
                            f.write(image_bytes)
                        
                        extracted.append({
                            "path": filepath,
                            "page": page_num + 1,
                            "index": img_index + 1,
                            "width": width,
                            "height": height,
                            "format": image_ext,
                            "size_bytes": len(image_bytes)
                        })
                        
                    except Exception as e:
                        print(f"[ImageExtractor] Failed to extract image {img_index} from page {page_num}: {e}")
                        continue
            
            doc.close()
            print(f"[ImageExtractor] Extracted {len(extracted)} images from {pdf_path}")
            
        except Exception as e:
            print(f"[ImageExtractor] Error processing PDF: {e}")
        
        return extracted
    
    def extract_page_as_image(self, pdf_path: str, page_num: int, dpi: int = 150) -> Optional[str]:
        """
        Render a PDF page as an image (useful for complex layouts).
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (1-indexed)
            dpi: Resolution for rendering
            
        Returns:
            Path to the saved image or None if failed
        """
        try:
            doc = fitz.open(pdf_path)
            if page_num < 1 or page_num > len(doc):
                return None
            
            page = doc[page_num - 1]
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            
            pdf_name = Path(pdf_path).stem
            filename = f"{pdf_name}_page{page_num}_full.png"
            filepath = os.path.join(self.output_dir, filename)
            
            pix.save(filepath)
            doc.close()
            
            return filepath
            
        except Exception as e:
            print(f"[ImageExtractor] Error rendering page {page_num}: {e}")
            return None


def extract_images_from_pdf(pdf_path: str, output_dir: str = "extracted_images") -> List[Dict]:
    """Convenience function to extract images from a PDF."""
    extractor = PDFImageExtractor(output_dir)
    return extractor.extract_images(pdf_path)


def match_images_to_figures(
    extracted_images: List[Dict],
    figure_refs: List[Tuple[str, str, int, int]],
    markdown_content: str
) -> Dict[str, Dict]:
    """
    Attempt to match extracted images to Figure references.
    
    This uses heuristics based on:
    - Page number (Figure 1 is likely on early pages)
    - Image size (figures tend to be larger than icons)
    - Order of appearance
    
    Args:
        extracted_images: List of extracted image info dicts
        figure_refs: List of (figure_id, context, start, end) from extract_figure_references
        markdown_content: The parsed markdown content
        
    Returns:
        Dict mapping figure_id -> {image_path, confidence, ...}
    """
    if not extracted_images:
        return {}
    
    # Get unique figure IDs
    figure_ids = sorted(set(ref[0] for ref in figure_refs), 
                       key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
    
    # Sort images by page and size (larger images first per page)
    # Handle both embedded images (with width/height) and page renders (without)
    def sort_key(x):
        page = x.get('page', 0)
        width = x.get('width', 1000)  # Default for page renders
        height = x.get('height', 1000)
        return (page, -(width * height))
    
    sorted_images = sorted(extracted_images, key=sort_key)
    
    # Filter to keep only larger images (likely figures, not icons)
    # For page renders, include all
    large_images = [
        img for img in sorted_images 
        if img.get('type') == 'render' or (img.get('width', 0) >= 200 and img.get('height', 0) >= 150)
    ]
    
    # Simple heuristic: assign images to figures in order
    matches = {}
    for i, fig_id in enumerate(figure_ids):
        if i < len(large_images):
            img = large_images[i]
            # Handle both embedded images (with width/height) and page renders (without)
            if 'width' in img and 'height' in img:
                size_str = f"{img['width']}x{img['height']}"
            else:
                size_str = "page_render"
            
            matches[fig_id] = {
                "image_path": img["path"],
                "page": img["page"],
                "size": size_str,
                "confidence": "heuristic",  # Not guaranteed to be correct
            }
        else:
            matches[fig_id] = {
                "image_path": None,
                "page": None,
                "size": None,
                "confidence": "no_match",
            }
    
    return matches


# Test function
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "test/541_OR_Bench_An_Over_Refusal_B.pdf"
    
    extractor = PDFImageExtractor("output/images")
    
    # First try embedded images
    images = extractor.extract_images(pdf_path)
    print(f"\nExtracted {len(images)} embedded images")
    
    # If no embedded images, render pages with figures
    if len(images) == 0:
        print("\nNo embedded images found. Rendering pages as images...")
        # Render first few pages (where figures typically appear)
        for page_num in [1, 2, 3, 4, 5]:
            page_img = extractor.extract_page_as_image(pdf_path, page_num, dpi=150)
            if page_img:
                print(f"  - Rendered page {page_num}: {page_img}")
                images.append({
                    "path": page_img,
                    "page": page_num,
                    "type": "page_render"
                })
    
    for img in images[:5]:
        if "width" in img:
            print(f"  - {img['path']} ({img['width']}x{img['height']}, page {img['page']})")
        else:
            print(f"  - {img['path']} (page {img['page']})")
