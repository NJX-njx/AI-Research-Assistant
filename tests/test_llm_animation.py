#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 LLM 增强动画生成
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from animation import llm_animation_pipeline

# 测试知识图谱 - 更丰富的内容
test_kg = {
    "nodes": [
        {"id": "gpt4", "type": "Method", "name": "GPT-4", "props": {"params": "1.8T", "company": "OpenAI"}},
        {"id": "llama3", "type": "Method", "name": "Llama-3", "props": {"params": "70B", "company": "Meta"}},
        {"id": "claude3", "type": "Method", "name": "Claude-3", "props": {"params": "Unknown", "company": "Anthropic"}},
        {"id": "mmlu", "type": "Dataset", "name": "MMLU", "props": {"tasks": "57", "domain": "Multi-domain"}},
        {"id": "humaneval", "type": "Dataset", "name": "HumanEval", "props": {"tasks": "164", "domain": "Coding"}},
        {"id": "acc_gpt4", "type": "Metric", "name": "86.4%", "props": {"metric": "Accuracy"}},
        {"id": "acc_llama", "type": "Metric", "name": "79.2%", "props": {"metric": "Accuracy"}},
        {"id": "finding1", "type": "Finding", "name": "GPT-4 在多领域推理任务上表现最佳，尤其在数学和代码生成方面领先"},
    ],
    "edges": [
        {"source": "gpt4", "target": "mmlu", "type": "evaluated_on"},
        {"source": "llama3", "target": "mmlu", "type": "evaluated_on"},
        {"source": "claude3", "target": "mmlu", "type": "evaluated_on"},
        {"source": "gpt4", "target": "humaneval", "type": "evaluated_on"},
        {"source": "gpt4", "target": "llama3", "type": "outperform"},
        {"source": "gpt4", "target": "claude3", "type": "outperform"},
        {"source": "gpt4", "target": "acc_gpt4", "type": "achieves"},
        {"source": "llama3", "target": "acc_llama", "type": "achieves"},
    ]
}

if __name__ == "__main__":
    output_path = os.path.join(PROJECT_ROOT, "output", "generated_code", "llm_animation.py")
    
    print("🚀 开始 LLM 增强动画生成测试")
    print(f"   知识图谱: {len(test_kg['nodes'])} 节点, {len(test_kg['edges'])} 边")
    print()
    
    # 运行完整流程
    result_path = llm_animation_pipeline(test_kg, output_path, max_scenes=6)
    
    print()
    print("📹 要渲染动画，请运行：")
    media_dir = os.path.join(PROJECT_ROOT, "output", "media_files")
    print(f"   cd {os.path.dirname(output_path)}")
    print(f"   manim -ql --media_dir {media_dir} llm_animation.py KnowledgeGraphAnimation")
