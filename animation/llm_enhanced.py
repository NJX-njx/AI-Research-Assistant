# -*- coding: utf-8 -*-
"""
LLM-Enhanced Animation Generation Module
方案C: 智能故事板 + 混合代码生成
- 简单场景: 模板生成 (稳定)
- 复杂场景: LLM生成Manim代码 (灵活)
"""
import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_client import LLMClient


# ============================================================================
# Prompts
# ============================================================================

STORYBOARD_SYSTEM_PROMPT = """你是一个专业的教育动画设计专家，擅长将知识图谱转化为有吸引力的动画故事板。
你需要根据知识图谱的结构和内容，设计一个清晰、有逻辑的动画叙事流程。

设计原则：
1. 循序渐进：从简单概念到复杂关系
2. 突出重点：关键实体和重要关系需要强调
3. 叙事连贯：场景之间有自然的过渡
4. 视觉吸引：动画描述要具体、有画面感"""

STORYBOARD_USER_PROMPT = """请根据以下知识图谱设计动画故事板。

## 知识图谱内容
节点 (Entities):
{nodes_desc}

边 (Relations):
{edges_desc}

## 输出要求
请输出 JSON 格式的故事板，包含 {max_scenes} 个场景：

```json
{{
  "title": "整体动画标题",
  "summary": "一句话概括这个知识图谱的核心内容",
  "scenes": [
    {{
      "scene_type": "title|entity_intro|relation|comparison|graph_overview|finding",
      "title": "场景标题",
      "narration": "这个场景的解说词（2-3句话，生动形象）",
      "key_elements": ["要展示的关键元素"],
      "animation_hints": "动画效果建议（如：淡入、强调、连线等）",
      "duration": 3.0
    }}
  ]
}}
```

场景类型说明：
- title: 开场标题
- entity_intro: 介绍单个重要实体
- relation: 展示两个实体之间的关系
- comparison: 对比多个实体
- graph_overview: 展示整体图谱结构
- finding: 展示研究发现或结论

请确保：
1. 第一个场景是 title 类型
2. 最后一个场景是 graph_overview 或 finding 类型
3. 解说词要通俗易懂，有教学感
4. 每个场景的 key_elements 要与知识图谱中的实际节点/边对应"""


MANIM_CODE_SYSTEM_PROMPT = """你是一个 Manim Community v0.19.0 专家。
你需要根据场景描述生成高质量、可执行的 Manim 动画代码。

代码规范：
1. 使用 Manim Community 语法（不是 3b1b 的 manimlib）
2. 导入语句：from manim import *
3. 类名格式：Scene{idx}（如 Scene0, Scene1）
4. 颜色使用 Manim 内置颜色常量（BLUE, GREEN, RED, YELLOW 等）
5. 动画要流畅，使用 self.play() 和 self.wait()
6. 确保所有元素在画面内，注意布局

可用的 Manim 对象：
- Text, MathTex, Tex: 文字和公式
- Circle, Square, Rectangle, RoundedRectangle: 基本形状
- Arrow, Line, DashedLine: 连接线
- VGroup: 组合多个对象
- Graph: 图结构

可用的动画：
- Write, Create, FadeIn, FadeOut, GrowFromCenter
- Transform, ReplacementTransform
- MoveToTarget, ApplyMethod
- Indicate, Circumscribe, Flash"""


MANIM_CODE_USER_PROMPT = """请为以下场景生成 Manim 代码。

## 场景信息
- 类型: {scene_type}
- 标题: {title}
- 解说词: {narration}
- 关键元素: {key_elements}
- 动画提示: {animation_hints}
- 时长: {duration} 秒

## 实体详情（如适用）
{entities_detail}

## 关系详情（如适用）
{relations_detail}

## 要求
1. 生成完整的、可直接运行的 Manim Scene 类
2. 类名必须是 Scene{idx}
3. 动画要与解说词内容匹配
4. 确保代码语法正确，能够成功渲染
5. 使用合适的颜色和布局

请直接输出 Python 代码，用 ```python ``` 包裹。"""


# ============================================================================
# LLM Enhanced Storyboard Generator
# ============================================================================

class LLMStoryboardGenerator:
    """使用 LLM 生成智能故事板"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
    
    def generate(self, kg_dict: Dict[str, Any], max_scenes: int = 8) -> Dict[str, Any]:
        """
        从知识图谱生成智能故事板
        
        Args:
            kg_dict: 知识图谱 {"nodes": [...], "edges": [...]}
            max_scenes: 最大场景数
            
        Returns:
            故事板字典，包含 title, summary, scenes
        """
        # 构建节点描述
        nodes = kg_dict.get("nodes", [])
        edges = kg_dict.get("edges", [])
        
        nodes_desc = self._format_nodes(nodes)
        edges_desc = self._format_edges(edges, nodes)
        
        # 构建 prompt
        user_prompt = STORYBOARD_USER_PROMPT.format(
            nodes_desc=nodes_desc,
            edges_desc=edges_desc,
            max_scenes=max_scenes
        )
        
        messages = [
            {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        print("[LLM] 生成智能故事板...")
        response = self.llm.chat(messages, temperature=0.7, max_tokens=4096)
        
        # 解析 JSON
        storyboard = self._parse_json_response(response)
        
        # 后处理：添加原始 KG 数据引用
        storyboard = self._enrich_storyboard(storyboard, kg_dict)
        
        print(f"[LLM] 故事板生成完成，共 {len(storyboard.get('scenes', []))} 个场景")
        return storyboard
    
    def _format_nodes(self, nodes: List[Dict]) -> str:
        """格式化节点列表"""
        lines = []
        for n in nodes:
            node_type = n.get("type", "Unknown")
            name = n.get("name", n.get("id", ""))
            props = n.get("props", {})
            props_str = ", ".join(f"{k}={v}" for k, v in props.items()) if props else ""
            lines.append(f"- [{node_type}] {name}" + (f" ({props_str})" if props_str else ""))
        return "\n".join(lines) if lines else "（无节点）"
    
    def _format_edges(self, edges: List[Dict], nodes: List[Dict]) -> str:
        """格式化边列表"""
        node_map = {n.get("id"): n.get("name", n.get("id")) for n in nodes}
        lines = []
        for e in edges:
            src = node_map.get(e.get("source"), e.get("source"))
            tgt = node_map.get(e.get("target"), e.get("target"))
            rel_type = e.get("type", "relates_to")
            lines.append(f"- {src} --[{rel_type}]--> {tgt}")
        return "\n".join(lines) if lines else "（无关系）"
    
    def _parse_json_response(self, response: str) -> Dict:
        """解析 LLM 返回的 JSON"""
        # 尝试从 markdown 代码块提取
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = response.strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"[Warning] JSON 解析失败: {e}")
            # 返回默认结构
            return {
                "title": "Knowledge Graph Visualization",
                "summary": "知识图谱可视化",
                "scenes": []
            }
    
    def _enrich_storyboard(self, storyboard: Dict, kg_dict: Dict) -> Dict:
        """丰富故事板，添加原始 KG 数据引用"""
        nodes = {n.get("id"): n for n in kg_dict.get("nodes", [])}
        edges = kg_dict.get("edges", [])
        
        for scene in storyboard.get("scenes", []):
            # 根据 key_elements 匹配实际的节点和边
            key_elements = scene.get("key_elements", [])
            scene["entities"] = []
            scene["relations"] = []
            
            for elem in key_elements:
                # 尝试匹配节点
                for nid, node in nodes.items():
                    if elem.lower() in node.get("name", "").lower() or elem.lower() in nid.lower():
                        if node not in scene["entities"]:
                            scene["entities"].append(node)
                
                # 尝试匹配边类型
                for edge in edges:
                    if elem.lower() in edge.get("type", "").lower():
                        if edge not in scene["relations"]:
                            scene["relations"].append(edge)
        
        return storyboard


# ============================================================================
# LLM Enhanced Manim Code Generator
# ============================================================================

class LLMManimGenerator:
    """使用 LLM 生成复杂场景的 Manim 代码"""
    
    # 简单场景类型，使用模板生成
    SIMPLE_SCENE_TYPES = {"title", "entity_intro"}
    # 复杂场景类型，使用 LLM 生成
    COMPLEX_SCENE_TYPES = {"relation", "comparison", "graph_overview", "finding"}
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.imports_needed = set()
    
    def generate_code(self, storyboard: Dict[str, Any]) -> str:
        """
        从故事板生成完整的 Manim 代码
        
        Args:
            storyboard: LLM 生成的故事板
            
        Returns:
            完整的 Python 代码字符串
        """
        scenes = storyboard.get("scenes", [])
        scene_codes = []
        
        self.imports_needed = {
            "Scene", "Text", "Write", "Create", "FadeIn", "FadeOut", 
            "Wait", "VGroup", "DOWN", "UP", "LEFT", "RIGHT", "ORIGIN"
        }
        
        for idx, scene in enumerate(scenes):
            scene_type = scene.get("scene_type", "relation")
            
            if scene_type in self.SIMPLE_SCENE_TYPES:
                # 简单场景：模板生成
                code = self._generate_template_scene(idx, scene)
            else:
                # 复杂场景：LLM 生成
                code = self._generate_llm_scene(idx, scene)
            
            if code:
                scene_codes.append(code)
        
        # 生成主场景
        main_scene = self._generate_main_scene(len(scene_codes))
        scene_codes.append(main_scene)
        
        # 组装完整代码
        return self._assemble_code(scene_codes, storyboard.get("title", "Animation"))
    
    def _generate_template_scene(self, idx: int, scene: Dict) -> str:
        """使用模板生成简单场景"""
        scene_type = scene.get("scene_type", "title")
        title = scene.get("title", "").replace('"', '\\"')
        narration = scene.get("narration", "").replace('"', '\\"')
        
        if scene_type == "title":
            self.imports_needed.update({"Text", "Write", "FadeOut", "ORIGIN", "DOWN"})
            return f'''
class Scene{idx}(Scene):
    """标题场景: {title}"""
    def construct(self):
        # 主标题
        title = Text("{title}", font_size=48)
        title.move_to(ORIGIN)
        
        # 副标题/解说
        subtitle = Text("{narration[:50]}...", font_size=24, color=GRAY)
        subtitle.next_to(title, DOWN, buff=0.5)
        
        # 动画
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(subtitle), run_time=1.0)
        self.wait(1.0)
        self.play(FadeOut(title), FadeOut(subtitle))
'''
        
        elif scene_type == "entity_intro":
            self.imports_needed.update({
                "Text", "RoundedRectangle", "Create", "Write", "FadeOut",
                "VGroup", "ORIGIN", "UP", "BLUE", "GRAY"
            })
            entities = scene.get("entities", [])
            if entities:
                entity = entities[0]
                name = entity.get("name", "Entity").replace('"', '\\"')
                etype = entity.get("type", "Unknown").replace('"', '\\"')
            else:
                name = title.replace('"', '\\"')
                etype = "Entity"
            
            return f'''
class Scene{idx}(Scene):
    """实体介绍: {name}"""
    def construct(self):
        # 实体框
        box = RoundedRectangle(
            corner_radius=0.2, width=5, height=2,
            color=BLUE, fill_opacity=0.3
        )
        
        # 实体名称
        name = Text("{name}", font_size=36)
        name.move_to(box.get_center())
        
        # 类型标签
        type_label = Text("{etype}", font_size=20, color=GRAY)
        type_label.next_to(box, UP, buff=0.3)
        
        group = VGroup(box, name, type_label)
        group.move_to(ORIGIN)
        
        # 动画
        self.play(Create(box), run_time=0.5)
        self.play(Write(name), Write(type_label), run_time=1.0)
        self.wait(1.5)
        self.play(FadeOut(group))
'''
        
        return ""
    
    def _generate_llm_scene(self, idx: int, scene: Dict) -> str:
        """使用 LLM 生成复杂场景"""
        scene_type = scene.get("scene_type", "relation")
        title = scene.get("title", "")
        narration = scene.get("narration", "")
        key_elements = scene.get("key_elements", [])
        animation_hints = scene.get("animation_hints", "")
        duration = scene.get("duration", 3.0)
        entities = scene.get("entities", [])
        relations = scene.get("relations", [])
        
        # 格式化实体和关系详情
        entities_detail = ""
        if entities:
            entities_detail = "\n".join([
                f"- {e.get('name', e.get('id'))} (类型: {e.get('type', 'Unknown')})"
                for e in entities
            ])
        
        relations_detail = ""
        if relations:
            relations_detail = "\n".join([
                f"- {r.get('source')} --[{r.get('type')}]--> {r.get('target')}"
                for r in relations
            ])
        
        user_prompt = MANIM_CODE_USER_PROMPT.format(
            scene_type=scene_type,
            title=title,
            narration=narration,
            key_elements=", ".join(key_elements),
            animation_hints=animation_hints,
            duration=duration,
            entities_detail=entities_detail or "无",
            relations_detail=relations_detail or "无",
            idx=idx
        )
        
        messages = [
            {"role": "system", "content": MANIM_CODE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        print(f"[LLM] 生成场景 {idx} ({scene_type}): {title[:30]}...")
        response = self.llm.chat(messages, temperature=0.3, max_tokens=2048)
        
        # 提取代码
        code = self._extract_code(response, idx)
        
        # 更新 imports
        self._update_imports_from_code(code)
        
        return code
    
    def _extract_code(self, response: str, idx: int) -> str:
        """从 LLM 响应中提取代码"""
        # 尝试从 markdown 代码块提取
        code_match = re.search(r'```python\s*([\s\S]*?)```', response)
        if code_match:
            code = code_match.group(1).strip()
        else:
            code = response.strip()
        
        # 移除可能的 import 语句（我们会统一添加）
        lines = code.split('\n')
        filtered_lines = []
        for line in lines:
            if line.strip().startswith('from manim import') or line.strip().startswith('import manim'):
                continue
            filtered_lines.append(line)
        code = '\n'.join(filtered_lines)
        
        # 确保类名正确
        code = re.sub(r'class\s+\w+Scene\s*\(', f'class Scene{idx}(', code)
        code = re.sub(r'class\s+Scene\d*\s*\(', f'class Scene{idx}(', code)
        
        return code
    
    def _update_imports_from_code(self, code: str):
        """从代码中提取需要的 imports"""
        # 常见的 Manim 对象和动画
        manim_objects = [
            "Circle", "Square", "Rectangle", "RoundedRectangle", "Dot", "Line",
            "Arrow", "DashedLine", "CurvedArrow", "DoubleArrow",
            "Text", "Tex", "MathTex", "Paragraph",
            "VGroup", "Group", "Graph",
            "Star", "Triangle", "Polygon", "RegularPolygon",
            "Brace", "BraceBetweenPoints",
            "SurroundingRectangle", "BackgroundRectangle",
            "NumberPlane", "Axes", "ThreeDAxes",
        ]
        
        manim_animations = [
            "Write", "Create", "FadeIn", "FadeOut", "GrowFromCenter",
            "Transform", "ReplacementTransform", "MoveToTarget",
            "Indicate", "Circumscribe", "Flash", "ShowPassingFlash",
            "DrawBorderThenFill", "Uncreate", "Unwrite",
            "GrowArrow", "ShowCreation", "ApplyMethod",
            "AnimationGroup", "Succession", "LaggedStart",
            "Wait", "Rotating", "Wiggle",
        ]
        
        manim_constants = [
            "UP", "DOWN", "LEFT", "RIGHT", "ORIGIN", "UL", "UR", "DL", "DR",
            "BLUE", "GREEN", "RED", "YELLOW", "ORANGE", "PURPLE", "PINK",
            "WHITE", "BLACK", "GRAY", "GREY", "GOLD", "TEAL",
            "PI", "TAU", "DEGREES",
            "SMALL_BUFF", "MED_SMALL_BUFF", "MED_LARGE_BUFF", "LARGE_BUFF",
        ]
        
        all_items = manim_objects + manim_animations + manim_constants
        
        for item in all_items:
            if re.search(rf'\b{item}\b', code):
                self.imports_needed.add(item)
    
    def _generate_main_scene(self, num_scenes: int) -> str:
        """生成主场景，组合所有子场景"""
        scene_calls = []
        for i in range(num_scenes):
            scene_calls.append(f"        Scene{i}.construct(self)")
            scene_calls.append(f"        self.clear()")
        
        return f'''
class KnowledgeGraphAnimation(Scene):
    """主场景：组合所有子场景"""
    def construct(self):
{chr(10).join(scene_calls)}
'''
    
    def _assemble_code(self, scene_codes: List[str], title: str) -> str:
        """组装完整代码"""
        # 添加 numpy 如果需要
        self.imports_needed.add("np")
        
        imports_list = sorted(self.imports_needed - {"np"})
        imports_str = ", ".join(imports_list)
        
        header = f'''# -*- coding: utf-8 -*-
"""
Auto-generated Manim animation code
Title: {title}
Generated with LLM enhancement
"""
from manim import {imports_str}
import numpy as np

'''
        
        return header + "\n".join(scene_codes)


# ============================================================================
# Convenience Functions
# ============================================================================

def llm_storyboard_from_kg(kg_dict: Dict[str, Any], max_scenes: int = 8) -> Dict[str, Any]:
    """
    使用 LLM 从知识图谱生成智能故事板
    
    Args:
        kg_dict: 知识图谱 {"nodes": [...], "edges": [...]}
        max_scenes: 最大场景数
        
    Returns:
        故事板字典
    """
    generator = LLMStoryboardGenerator()
    return generator.generate(kg_dict, max_scenes)


def llm_generate_code(storyboard: Dict[str, Any]) -> str:
    """
    从 LLM 故事板生成 Manim 代码
    
    Args:
        storyboard: 故事板字典
        
    Returns:
        完整的 Python 代码
    """
    generator = LLMManimGenerator()
    return generator.generate_code(storyboard)


def llm_animation_pipeline(kg_dict: Dict[str, Any], output_path: str, max_scenes: int = 8) -> str:
    """
    完整的 LLM 增强动画生成流程
    
    Args:
        kg_dict: 知识图谱
        output_path: 输出代码文件路径
        max_scenes: 最大场景数
        
    Returns:
        生成的代码文件路径
    """
    print("=" * 60)
    print("🎬 LLM 增强动画生成流程")
    print("=" * 60)
    
    # Step 1: 生成智能故事板
    print("\n📋 Step 1: 生成智能故事板...")
    storyboard = llm_storyboard_from_kg(kg_dict, max_scenes)
    print(f"   标题: {storyboard.get('title', 'N/A')}")
    print(f"   摘要: {storyboard.get('summary', 'N/A')}")
    
    # Step 2: 生成 Manim 代码
    print("\n🎥 Step 2: 生成 Manim 代码...")
    code = llm_generate_code(storyboard)
    print(f"   生成代码: {len(code)} 字符")
    
    # Step 3: 保存代码
    print("\n💾 Step 3: 保存代码...")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"   已保存到: {output_path}")
    
    # 保存故事板 JSON
    storyboard_path = output_path.replace('.py', '_storyboard.json')
    with open(storyboard_path, 'w', encoding='utf-8') as f:
        json.dump(storyboard, f, ensure_ascii=False, indent=2)
    print(f"   故事板已保存到: {storyboard_path}")
    
    print("\n" + "=" * 60)
    print("✅ 生成完成！")
    print(f"   运行命令: manim -ql {output_path} KnowledgeGraphAnimation")
    print("=" * 60)
    
    return output_path


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    # 测试知识图谱
    test_kg = {
        "nodes": [
            {"id": "gpt4", "type": "Method", "name": "GPT-4"},
            {"id": "llama3", "type": "Method", "name": "Llama-3"},
            {"id": "claude3", "type": "Method", "name": "Claude-3"},
            {"id": "mmlu", "type": "Dataset", "name": "MMLU Benchmark"},
            {"id": "acc", "type": "Metric", "name": "准确率 86.4%"},
            {"id": "finding", "type": "Finding", "name": "GPT-4在推理任务上表现最佳"},
        ],
        "edges": [
            {"source": "gpt4", "target": "mmlu", "type": "evaluated_on"},
            {"source": "llama3", "target": "mmlu", "type": "evaluated_on"},
            {"source": "gpt4", "target": "llama3", "type": "outperform"},
            {"source": "gpt4", "target": "claude3", "type": "outperform"},
            {"source": "gpt4", "target": "acc", "type": "achieves"},
        ]
    }
    
    output_path = "output/generated_code/llm_animation.py"
    llm_animation_pipeline(test_kg, output_path, max_scenes=6)
