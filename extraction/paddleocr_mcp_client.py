# -*- coding: utf-8 -*-
"""
PaddleOCR-VL MCP Client using the official paddleocr-mcp package.
This uses the PaddleOCRVLHandler to call the PaddleOCR-VL service.
"""
import os
import asyncio
import base64
from typing import Dict, Optional, Any
from pathlib import Path

# Configuration
PADDLEOCR_MCP_SERVER_URL = os.getenv(
    "PADDLEOCR_MCP_SERVER_URL", 
    "https://d2kdt3p7v87ac6bf.aistudio-app.com"
)
PADDLEOCR_ACCESS_TOKEN = os.getenv(
    "PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN", 
    None
)


class MockContext:
    """Mock MCP Context for standalone usage without full MCP server."""
    
    async def info(self, msg: str) -> None:
        print(f"[INFO] {msg}")
    
    async def error(self, msg: str) -> None:
        print(f"[ERROR] {msg}")
    
    async def warning(self, msg: str) -> None:
        print(f"[WARN] {msg}")
    
    async def debug(self, msg: str) -> None:
        pass  # Silent debug
    
    async def report_progress(self, progress: float, total: float) -> None:
        pass


class PaddleOCRVLClient:
    """Client for PaddleOCR-VL using the official paddleocr-mcp package."""
    
    def __init__(self, server_url: Optional[str] = None, access_token: Optional[str] = None):
        self.server_url = server_url or PADDLEOCR_MCP_SERVER_URL
        self.access_token = access_token or PADDLEOCR_ACCESS_TOKEN
        self._handler = None
    
    def _get_handler(self):
        """Lazy initialization of the PaddleOCRVLHandler."""
        if self._handler is None:
            from paddleocr_mcp.pipelines import PaddleOCRVLHandler
            self._handler = PaddleOCRVLHandler(
                pipeline="PaddleOCR-VL",
                ppocr_source="aistudio",
                pipeline_config=None,
                device=None,
                server_url=self.server_url,
                aistudio_access_token=self.access_token,
                qianfan_api_key=None,
                timeout=180
            )
        return self._handler
    
    async def parse_document(self, file_path: str) -> Dict:
        """
        Parse a document using PaddleOCR-VL.
        
        Args:
            file_path: Path to PDF or image file
            
        Returns:
            Dict with markdown content and metadata
        """
        if not os.path.exists(file_path):
            return {
                "markdown": "",
                "raw": None,
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        try:
            handler = self._get_handler()
            
            # Start the handler if not started
            await handler.start()
            
            # Read file and encode to base64
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            file_data = base64.b64encode(file_bytes).decode("utf-8")
            
            # Determine file type
            ext = Path(file_path).suffix.lower()
            file_type_map = {
                ".pdf": "pdf",
                ".png": "image",
                ".jpg": "image",
                ".jpeg": "image",
            }
            file_type = file_type_map.get(ext, "pdf")
            
            # Create mock context
            ctx = MockContext()
            
            # Call process
            result = await handler.process(
                input_data=file_data,
                output_mode="simple",
                ctx=ctx,
                file_type=file_type,
            )
            
            # Extract text content
            if isinstance(result, str):
                markdown = result
            elif isinstance(result, list):
                # List of TextContent or ImageContent
                markdown_parts = []
                for item in result:
                    if hasattr(item, 'text'):
                        markdown_parts.append(item.text)
                markdown = "\n".join(markdown_parts)
            else:
                markdown = str(result) if result else ""
            
            return {
                "markdown": markdown,
                "raw": result,
                "success": bool(markdown),
                "error": None
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "markdown": "",
                "raw": None,
                "success": False,
                "error": str(e)
            }
    
    def parse_document_sync(self, file_path: str) -> Dict:
        """Synchronous wrapper for parse_document."""
        return asyncio.run(self.parse_document(file_path))


def parse_pdf(file_path: str) -> Dict:
    """Convenience function to parse a PDF file."""
    client = PaddleOCRVLClient()
    return client.parse_document_sync(file_path)


# Test function
async def test_paddleocr_mcp():
    """Test the PaddleOCR-VL MCP client."""
    test_pdf = Path(__file__).parent.parent / "test" / "541_OR_Bench_An_Over_Refusal_B.pdf"
    
    if not test_pdf.exists():
        # Try alternative path
        test_pdf = Path(__file__).parent / "test" / "541_OR_Bench_An_Over_Refusal_B.pdf"
    
    if not test_pdf.exists():
        print(f"Test file not found: {test_pdf}")
        return None
    
    print(f"Testing PaddleOCR-VL MCP with: {test_pdf}")
    print(f"Server URL: {PADDLEOCR_MCP_SERVER_URL}")
    
    client = PaddleOCRVLClient()
    result = await client.parse_document(str(test_pdf))
    
    if result["success"]:
        print(f"\n✓ Success! Got {len(result['markdown'])} characters")
        print(f"\nPreview:\n{result['markdown'][:800]}...")
        
        # Save output
        output_dir = Path(__file__).parent.parent / "outputs"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "paddleocr_vl_output.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["markdown"])
        print(f"\nSaved to: {output_path}")
    else:
        print(f"\n✗ Failed: {result['error']}")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_paddleocr_mcp())
