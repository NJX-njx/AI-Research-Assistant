# -*- coding: utf-8 -*-
"""Main pipeline: PDF -> Text/Figures -> Entities/Triplets -> KG -> Storyboard -> Manim code"""
import os
import json
from typing import List
from extraction.text_extractor import extract_text_from_pdf, chunk_text
from knowledge_graph.entity_extractor import extract_from_chunk, normalize
from knowledge_graph.graph_builder import KnowledgeGraph
from animation.storyboard import storyboard_from_kg
from animation.manim_generator import generate_code

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def build_kg_from_pdfs(pdf_paths: List[str]) -> KnowledgeGraph:
    kg = KnowledgeGraph()
    if not pdf_paths:
        raise ValueError("No PDF paths provided.")
    for pdf in pdf_paths:
        text = extract_text_from_pdf(pdf)
        for chunk in chunk_text(text):
            raw = extract_from_chunk(chunk)
            data = normalize(raw)
            for ent in data["entities"]:
                kg.add_entity(ent)
            for trip in data["triplets"]:
                kg.add_triplet(trip)
    return kg


def run_demo(pdf_paths: List[str]):
    ensure_dir(OUTPUT_DIR)
    # 1) Build KG
    kg = build_kg_from_pdfs(pdf_paths)
    kg_dict = kg.to_dict()
    with open(os.path.join(OUTPUT_DIR, "kg.json"), "w", encoding="utf-8") as f:
        json.dump(kg_dict, f, ensure_ascii=False, indent=2)

    # 2) Storyboard
    scenes = storyboard_from_kg(kg_dict)
    with open(os.path.join(OUTPUT_DIR, "storyboard.json"), "w", encoding="utf-8") as f:
        json.dump(scenes, f, ensure_ascii=False, indent=2)

    # 3) Manim code
    code = generate_code(scenes)
    with open(os.path.join(OUTPUT_DIR, "relation_scene.py"), "w", encoding="utf-8") as f:
        f.write(code)

    print("Demo finished. Outputs in", OUTPUT_DIR)


if __name__ == "__main__":
    # Example usage: place two small PDFs paths here
    sample_pdfs = []
    if sample_pdfs:
        run_demo(sample_pdfs)
    else:
        print("Please provide sample PDF paths to run the demo.")
