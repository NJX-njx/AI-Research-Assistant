# -*- coding: utf-8 -*-
"""
完整提取流程测试
================
测试整个提取模块的功能，确保没有问题。
"""
import os
import sys

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from extraction.paddleocr_mcp_client import PaddleOCRVLClient
from extraction.text_extractor import chunk_text
from extraction.vision_extractor import extract_figure_references, extract_image_paths_from_markdown
from extraction.image_extractor import PDFImageExtractor, match_images_to_figures
from utils.vllm_client import VLMClient, analyze_figure_safe

# 测试数据路径
TEST_DATA_DIR = os.path.join(PROJECT_ROOT, "test_data")
TEST_PDF = os.path.join(TEST_DATA_DIR, "541_OR_Bench_An_Over_Refusal_B.pdf")


def test_extraction_pipeline(pdf_path: str = None):
    """Test the complete extraction pipeline."""
    
    if pdf_path is None:
        pdf_path = TEST_PDF
    
    print("=" * 60)
    print("🧪 完整提取流程测试")
    print("=" * 60)
    
    results = {
        "step1_ocr": False,
        "step2_chunk": False,
        "step3_figures": False,
        "step4_images": False,
        "step5_vlm": False,
    }
    
    # =========================================
    # Step 1: Document Parsing
    # =========================================
    print("\n📄 Step 1: PaddleOCR-VL 文档解析")
    try:
        ocr_client = PaddleOCRVLClient()
        ocr_result = ocr_client.parse_document_sync(pdf_path)
        
        if ocr_result['success']:
            markdown = ocr_result['markdown']
            print(f"   ✅ 成功 - {len(markdown):,} 字符")
            results["step1_ocr"] = True
        else:
            print(f"   ❌ 失败: {ocr_result['error']}")
            return results
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return results
    
    # =========================================
    # Step 2: Text Chunking
    # =========================================
    print("\n📝 Step 2: 文本分块")
    try:
        chunks = chunk_text(markdown, max_chars=2000)
        print(f"   ✅ 成功 - {len(chunks)} 个块")
        results["step2_chunk"] = True
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # =========================================
    # Step 3: Figure Reference Extraction
    # =========================================
    print("\n🖼️ Step 3: Figure 引用提取")
    try:
        figure_refs = extract_figure_references(markdown)
        print(f"   ✅ 成功 - {len(figure_refs)} 个引用")
        
        # Show unique figures
        unique_figs = sorted(set(ref[0] for ref in figure_refs))
        print(f"   识别的图: {', '.join(unique_figs[:5])}")
        
        # Extract image paths from markdown
        img_paths = extract_image_paths_from_markdown(markdown)
        print(f"   Markdown中的图片标签: {len(img_paths)} 个")
        
        results["step3_figures"] = True
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # =========================================
    # Step 4: Image Extraction from PDF
    # =========================================
    print("\n📷 Step 4: PDF 图片提取")
    try:
        extractor = PDFImageExtractor("output/images")
        
        # Try embedded images first
        images = extractor.extract_images(pdf_path)
        
        if len(images) == 0:
            print("   ⚠️ 无嵌入图片，渲染页面...")
            # Render pages with figures (typically first few pages)
            for page_num in [1, 2, 3]:
                page_img = extractor.extract_page_as_image(pdf_path, page_num, dpi=150)
                if page_img:
                    images.append({"path": page_img, "page": page_num, "type": "render"})
        
        print(f"   ✅ 成功 - {len(images)} 张图片")
        
        # Match images to figures
        if figure_refs and images:
            matches = match_images_to_figures(images, figure_refs, markdown)
            matched_count = sum(1 for v in matches.values() if v.get("image_path"))
            print(f"   Figure-图片匹配: {matched_count}/{len(matches)}")
        
        results["step4_images"] = True
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        import traceback
        traceback.print_exc()
    
    # =========================================
    # Step 5: VLM Figure Analysis (with fallback)
    # =========================================
    print("\n🔬 Step 5: VLM 图像分析 (含 Fallback)")
    try:
        vlm = VLMClient()
        vlm_available = vlm.is_available(force_check=True)
        print(f"   VLM 服务状态: {'✅ 可用' if vlm_available else '⚠️ 不可用 (将使用 Fallback)'}")
        
        # Test with a figure context
        if figure_refs:
            fig_id, context, _, _ = figure_refs[0]
            
            # Find corresponding image
            image_path = None
            if images:
                # Use first page render as test
                image_path = images[0].get("path")
            
            print(f"   测试分析: {fig_id}")
            result = analyze_figure_safe(
                image_path=image_path,
                caption=f"{fig_id}: Over-refusal benchmark results",
                context_sentences=[context[:200]]
            )
            
            if "_fallback" in result:
                print(f"   📎 使用 Fallback (纯文本分析)")
            
            if result.get("entities") or result.get("summary"):
                print(f"   ✅ 成功 - 实体: {len(result.get('entities', []))}, 关系: {len(result.get('relations', []))}")
                if result.get("summary"):
                    print(f"   摘要: {result['summary'][:80]}...")
                results["step5_vlm"] = True
            else:
                print(f"   ⚠️ 结果为空: {result.get('error', 'unknown')}")
        else:
            print("   ⚠️ 无 Figure 引用可测试")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        import traceback
        traceback.print_exc()
    
    # =========================================
    # Summary
    # =========================================
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for step, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {step}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 所有测试通过！提取模块工作正常。")
    else:
        print("⚠️ 部分测试未通过，请检查日志。")
    
    return results


if __name__ == "__main__":
    test_extraction_pipeline()
