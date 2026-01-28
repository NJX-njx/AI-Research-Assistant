# -*- coding: utf-8 -*-
"""
AI科研辅助智能体 - 完整 Demo 演示
===============================
展示核心流水线：PDF解析 → 实体抽取 → 知识图谱构建 → 可视化

使用方式：
    export AISTUDIO_API_KEY="your_api_key"
    python run_demo.py [pdf_path]
"""
import sys
import os
import json
import argparse
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extraction.paddleocr_mcp_client import PaddleOCRVLClient
from extraction.text_extractor import chunk_text
from extraction.vision_extractor import extract_figure_references
from knowledge_graph.entity_extractor import EntityExtractor
from knowledge_graph.graph_builder import KnowledgeGraph
from knowledge_graph.schema import Entity, Relation


def print_header(title: str):
    """Print formatted header."""
    width = 70
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_subheader(title: str):
    """Print formatted subheader."""
    print(f"\n--- {title} ---")


def run_demo(pdf_path: str, output_dir: str = "output", max_chunks: int = 5):
    """Run the complete demo pipeline.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory for output files
        max_chunks: Maximum number of chunks to process (for demo speed)
    """
    start_time = datetime.now()
    os.makedirs(output_dir, exist_ok=True)
    
    print_header("🧠 AI科研辅助智能体 Demo")
    print(f"PDF文件: {pdf_path}")
    print(f"输出目录: {output_dir}")
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # =========================================
    # Step 1: Document Parsing (PaddleOCR-VL)
    # =========================================
    print_header("📄 Step 1: 文档解析 (PaddleOCR-VL)")
    
    ocr_client = PaddleOCRVLClient()
    ocr_result = ocr_client.parse_document_sync(pdf_path)
    
    if not ocr_result['success']:
        print(f"❌ 解析失败: {ocr_result['error']}")
        return None
    
    markdown = ocr_result['markdown']
    print(f"✅ 解析成功")
    print(f"   - 总字符数: {len(markdown):,}")
    
    # Save markdown
    md_path = os.path.join(output_dir, "parsed_content.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"   - 保存到: {md_path}")
    
    # =========================================
    # Step 2: Text Chunking
    # =========================================
    print_header("📝 Step 2: 文本分块")
    
    chunks = chunk_text(markdown, max_chars=2000)
    print(f"✅ 分块完成")
    print(f"   - 总块数: {len(chunks)}")
    print(f"   - 处理块数: {min(max_chunks, len(chunks))} (Demo限制)")
    
    # =========================================
    # Step 3: Figure Reference Extraction
    # =========================================
    print_header("🖼️ Step 3: Figure引用提取")
    
    figure_refs = extract_figure_references(markdown)
    print(f"✅ 提取完成")
    print(f"   - Figure引用数量: {len(figure_refs)}")
    
    # Group by figure ID
    figure_map = {}
    for fig_id, context, start, end in figure_refs:
        if fig_id not in figure_map:
            figure_map[fig_id] = []
        figure_map[fig_id].append(context[:100] + "..." if len(context) > 100 else context)
    
    for fig_id, contexts in list(figure_map.items())[:5]:
        print(f"   - {fig_id}: {len(contexts)} 处引用")
    
    # =========================================
    # Step 4: Entity & Relation Extraction (LLM)
    # =========================================
    print_header("🔍 Step 4: 实体与关系抽取 (LLM)")
    
    entity_extractor = EntityExtractor()
    all_entities = []
    all_relations = []
    
    process_chunks = chunks[:max_chunks]
    for i, chunk in enumerate(process_chunks):
        print(f"   处理块 {i+1}/{len(process_chunks)}...", end=" ")
        
        entities = entity_extractor.extract_entities(chunk)
        relations = entity_extractor.extract_relations(chunk, entities)
        
        all_entities.extend(entities)
        all_relations.extend(relations)
        
        print(f"实体: {len(entities)}, 关系: {len(relations)}")
    
    # Deduplicate entities by name
    unique_entities = {}
    for e in all_entities:
        name = e.get("name", "").lower().strip()
        if name and name not in unique_entities:
            unique_entities[name] = e
    all_entities = list(unique_entities.values())
    
    print(f"\n✅ 抽取完成")
    print(f"   - 总实体数: {len(all_entities)}")
    print(f"   - 总关系数: {len(all_relations)}")
    
    # Show entity types
    print_subheader("实体类型分布")
    entity_types = {}
    for e in all_entities:
        t = e.get("type", "UNKNOWN")
        entity_types[t] = entity_types.get(t, 0) + 1
    for t, count in sorted(entity_types.items(), key=lambda x: -x[1]):
        print(f"   [{t}]: {count}")
    
    # Show sample entities
    print_subheader("实体样例")
    for e in all_entities[:10]:
        print(f"   • {e.get('name', 'N/A')} ({e.get('type', 'N/A')})")
    
    # =========================================
    # Step 5: Knowledge Graph Construction
    # =========================================
    print_header("🕸️ Step 5: 知识图谱构建")
    
    kg = KnowledgeGraph()
    
    # Add entities as nodes
    entity_id_counter = 0
    for e in all_entities:
        entity_id_counter += 1
        ent = Entity(
            id=f"e{entity_id_counter}",
            type=e.get("type", "Entity"),
            name=e.get("name", ""),
            props={}
        )
        kg.add_entity(ent)
    
    # Add relations as edges
    for r in all_relations:
        source = r.get("source", "")
        target = r.get("target", "")
        if source and target:
            # Find entity IDs
            source_id = None
            target_id = None
            for e in all_entities:
                if e.get("name", "").lower() == source.lower():
                    source_id = e.get("name")
                if e.get("name", "").lower() == target.lower():
                    target_id = e.get("name")
            if source_id and target_id:
                rel = Relation(
                    source=source_id,
                    target=target_id,
                    type=r.get("relation", "related_to")
                )
                kg.add_relation(rel)
    
    # Add Figure references as nodes
    for fig_id, contexts in figure_map.items():
        fig_ent = Entity(
            id=fig_id,
            type="Figure",
            name=fig_id,
            props={"context_count": len(contexts)}
        )
        kg.add_entity(fig_ent)
    
    # Get stats
    graph_data = kg.to_dict()
    num_nodes = len(graph_data["nodes"])
    num_edges = len(graph_data["edges"])
    
    # Count node types
    node_types = {}
    for n in graph_data["nodes"]:
        ntype = n.get("type", "Unknown")
        node_types[ntype] = node_types.get(ntype, 0) + 1
    
    print(f"✅ 图谱构建完成")
    print(f"   - 节点数: {num_nodes}")
    print(f"   - 边数: {num_edges}")
    
    # Show node types
    print_subheader("节点类型分布")
    for ntype, count in sorted(node_types.items(), key=lambda x: -x[1]):
        print(f"   [{ntype}]: {count}")
    
    # =========================================
    # Step 6: Export Results
    # =========================================
    print_header("💾 Step 6: 导出结果")
    
    # Export graph
    graph_path = os.path.join(output_dir, "knowledge_graph.json")
    # graph_data already computed above
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    print(f"   - 图谱JSON: {graph_path}")
    
    # Export entities
    entities_path = os.path.join(output_dir, "entities.json")
    with open(entities_path, "w", encoding="utf-8") as f:
        json.dump(all_entities, f, ensure_ascii=False, indent=2)
    print(f"   - 实体JSON: {entities_path}")
    
    # Export relations
    relations_path = os.path.join(output_dir, "relations.json")
    with open(relations_path, "w", encoding="utf-8") as f:
        json.dump(all_relations, f, ensure_ascii=False, indent=2)
    print(f"   - 关系JSON: {relations_path}")
    
    # =========================================
    # Summary
    # =========================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_header("📊 运行总结")
    print(f"   总耗时: {duration:.1f} 秒")
    print(f"   文档长度: {len(markdown):,} 字符")
    print(f"   处理块数: {len(process_chunks)}")
    print(f"   提取实体: {len(all_entities)}")
    print(f"   提取关系: {len(all_relations)}")
    print(f"   图谱节点: {num_nodes}")
    print(f"   图谱边数: {num_edges}")
    print(f"\n✅ Demo 运行完成!")
    
    return {
        "markdown": markdown,
        "chunks": chunks,
        "entities": all_entities,
        "relations": all_relations,
        "graph": graph_data,
        "figures": figure_map,
        "stats": {"num_nodes": num_nodes, "num_edges": num_edges, "node_types": node_types}
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI科研辅助智能体 Demo")
    parser.add_argument("pdf_path", nargs="?", 
                       default="test/541_OR_Bench_An_Over_Refusal_B.pdf",
                       help="PDF文件路径")
    parser.add_argument("--output", "-o", default="output",
                       help="输出目录")
    parser.add_argument("--max-chunks", "-n", type=int, default=5,
                       help="最大处理块数（加快Demo速度）")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"❌ 文件不存在: {args.pdf_path}")
        sys.exit(1)
    
    run_demo(args.pdf_path, args.output, args.max_chunks)
