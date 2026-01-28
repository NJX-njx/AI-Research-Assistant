#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 Demo 动画"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from animation import storyboard_from_kg, save_code

# 测试知识图谱
kg = {
    'nodes': [
        {'id': 'gpt4', 'type': 'Method', 'name': 'GPT-4'},
        {'id': 'llama3', 'type': 'Method', 'name': 'Llama-3'},
        {'id': 'claude3', 'type': 'Method', 'name': 'Claude-3'},
        {'id': 'mmlu', 'type': 'Dataset', 'name': 'MMLU'},
        {'id': 'acc', 'type': 'Metric', 'name': 'Accuracy 86.4%'},
        {'id': 'finding1', 'type': 'Finding', 'name': 'GPT-4 achieves best performance'},
    ],
    'edges': [
        {'source': 'gpt4', 'target': 'mmlu', 'type': 'evaluated_on'},
        {'source': 'llama3', 'target': 'mmlu', 'type': 'evaluated_on'},
        {'source': 'gpt4', 'target': 'llama3', 'type': 'outperform'},
        {'source': 'gpt4', 'target': 'claude3', 'type': 'outperform'},
        {'source': 'gpt4', 'target': 'acc', 'type': 'achieves'},
    ]
}

print("生成 Storyboard...")
scenes = storyboard_from_kg(kg, max_scenes=8)
print(f"生成了 {len(scenes)} 个场景:")
for i, s in enumerate(scenes):
    print(f"  {i+1}. [{s['scene_type']}] {s['title']}")

print("\n保存 Manim 代码...")
output_path = os.path.join(PROJECT_ROOT, 'output', 'generated_code', 'demo_animation.py')
media_dir = os.path.join(PROJECT_ROOT, 'output', 'media_files')
save_code(scenes, output_path)
print(f"代码已保存到: {output_path}")

print(f"\n要渲染动画，请运行：")
print(f"  cd {os.path.dirname(output_path)}")
print(f"  manim -ql --media_dir {media_dir} demo_animation.py KnowledgeGraphAnimation")
