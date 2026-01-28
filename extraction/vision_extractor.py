# -*- coding: utf-8 -*-
"""Vision semantic extraction via VLM: takes figure image and optional caption/context,
returns structured description useful for KG building.
Supports automatic association with Figure X references in main text.
"""
import re
import os
from typing import Dict, Optional, List, Tuple

# Use VLMClient for actual image understanding
from utils.vllm_client import VLMClient

SCHEMA_HINT = '{"entities": [{"type": "Concept|Object|Axis|Legend", "name": "..."}], "relations": [{"source": "...", "target": "...", "type": "trend|causal|correlates|part_of"}], "summary": "..."}'

PROMPT_TMPL = (
    "你是科研图像解析助手。请分析这张论文中的图，返回严格JSON格式：\n"
    "- entities: 图中关键对象或概念（如坐标轴名称、图例、数据系列等）\n"
    "- relations: 这些对象之间的关系（trend/causal/correlates/part_of）\n"
    "- summary: 用一句话概述该图的主要发现或意图\n"
)

# Regex patterns for Figure/Fig/图 references
FIGURE_PATTERNS = [
    r"(?:Figure|Fig\.?|图)\s*(\d+[a-zA-Z]?)",  # Figure 1, Fig. 2a, 图3
    r"(?:Figure|Fig\.?|图)\s*(\d+)\s*[\(\[]([a-zA-Z,\s]+)[\)\]]",  # Figure 1(a,b)
]

# Pattern to extract image tags from markdown
IMG_TAG_PATTERN = r'<img\s+src="([^"]+)"[^>]*>'


def extract_figure_references(text: str) -> List[Tuple[str, str, int, int]]:
    """Extract all Figure X references from text with their context sentences.
    Returns: list of (figure_id, context_sentence, start_pos, end_pos)
    """
    results = []
    # Split into sentences (simple heuristic)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    pos = 0
    for sent in sentences:
        for pattern in FIGURE_PATTERNS:
            for match in re.finditer(pattern, sent, re.IGNORECASE):
                fig_id = f"Figure_{match.group(1)}"
                results.append((fig_id, sent.strip(), pos, pos + len(sent)))
        pos += len(sent) + 1
    return results


def extract_image_paths_from_markdown(markdown: str) -> List[str]:
    """Extract image paths from markdown img tags.
    Returns: list of image paths (relative paths from the markdown)
    """
    matches = re.findall(IMG_TAG_PATTERN, markdown)
    return matches


def associate_figures_with_text(full_text: str, figure_captions: Dict[str, str]) -> Dict[str, Dict]:
    """Associate figure IDs with their captions and all referencing sentences.
    Args:
        full_text: The full paper text
        figure_captions: Dict mapping figure_id -> caption text (e.g., {"Figure_1": "Overview of..."})
    Returns:
        Dict mapping figure_id -> {"caption": str, "references": List[str], "context": str}
    """
    refs = extract_figure_references(full_text)
    associations = {}
    for fig_id, sent, _, _ in refs:
        if fig_id not in associations:
            associations[fig_id] = {
                "caption": figure_captions.get(fig_id, ""),
                "references": [],
            }
        if sent not in associations[fig_id]["references"]:
            associations[fig_id]["references"].append(sent)
    # Build combined context
    for fig_id in associations:
        cap = associations[fig_id]["caption"]
        refs_text = " ".join(associations[fig_id]["references"])
        associations[fig_id]["context"] = f"Caption: {cap}\nReferences: {refs_text}"
    return associations


def describe_figure(image_path: str, caption: Optional[str] = None, context_sentences: Optional[List[str]] = None) -> Dict:
    """Generate semantic description for a figure using VLM.
    
    ⚠️ This function actually sends the image to a Vision Language Model!
    
    Args:
        image_path: Path to figure image file
        caption: Figure caption text (optional context)
        context_sentences: Sentences from main text that reference this figure
        
    Returns:
        Dict with entities, relations, summary extracted from the figure
    """
    # Check if image exists
    if not os.path.exists(image_path):
        return {
            "error": f"Image not found: {image_path}",
            "entities": [],
            "relations": [],
            "summary": ""
        }
    
    # Build prompt with context
    prompt = PROMPT_TMPL
    if caption:
        prompt += f"\n图注: {caption}"
    if context_sentences:
        prompt += f"\n正文引用: {' '.join(context_sentences[:3])}"  # Limit context
    prompt += f"\n\n请返回JSON格式，Schema: {SCHEMA_HINT}"
    
    # Use VLMClient to actually analyze the image
    try:
        vlm = VLMClient()
        result = vlm.analyze_figure(image_path, caption=caption, context_sentences=context_sentences)
        return result
    except Exception as e:
        # Fallback: return error info
        return {
            "error": str(e),
            "entities": [],
            "relations": [],
            "summary": ""
        }


def describe_figure_with_association(image_path: str, fig_id: str, associations: Dict[str, Dict]) -> Dict:
    """Convenience: describe figure using pre-computed associations."""
    assoc = associations.get(fig_id, {})
    return describe_figure(
        image_path,
        caption=assoc.get("caption"),
        context_sentences=assoc.get("references", [])
    )
