# -*- coding: utf-8 -*-
"""
Generate Manim Python code from storyboard scenes.
Dynamically creates Scene classes based on scene type and content.
"""
from typing import List, Dict, Any, Optional
import textwrap
import os
import subprocess
import tempfile


# Color mapping for Manim (hex to Manim color names where possible)
COLOR_MAP = {
    "#3498db": "BLUE",
    "#2ecc71": "GREEN", 
    "#f1c40f": "YELLOW",
    "#9b59b6": "PURPLE",
    "#e74c3c": "RED",
    "#e67e22": "ORANGE",
    "#34495e": "GRAY",
    "#1abc9c": "TEAL",
}


def hex_to_manim_color(hex_color: str) -> str:
    """Convert hex color to Manim color constant or ManimColor."""
    if hex_color in COLOR_MAP:
        return COLOR_MAP[hex_color]
    return f'"{hex_color}"'


class ManimCodeGenerator:
    """Generate Manim Python code from storyboard scenes."""
    
    def __init__(self, scenes: List[Dict[str, Any]]):
        self.scenes = scenes
        self.scene_classes = []
        self.imports_needed = set()
    
    def generate(self) -> str:
        """Generate complete Manim Python code."""
        self.scene_classes = []
        self.imports_needed = {"Scene", "Text", "Write", "Create", "FadeIn", "FadeOut", "Wait"}
        
        # Generate each scene class
        for i, scene in enumerate(self.scenes):
            scene_type = scene.get("scene_type", "relation")
            
            if scene_type == "title":
                self._generate_title_scene(i, scene)
            elif scene_type == "entity_intro":
                self._generate_entity_scene(i, scene)
            elif scene_type == "relation":
                self._generate_relation_scene(i, scene)
            elif scene_type == "comparison":
                self._generate_comparison_scene(i, scene)
            elif scene_type == "graph_overview":
                self._generate_overview_scene(i, scene)
            elif scene_type == "finding":
                self._generate_finding_scene(i, scene)
            else:
                self._generate_generic_scene(i, scene)
        
        # Generate main scene that combines all
        self._generate_main_scene()
        
        return self._assemble_code()
    
    def _generate_title_scene(self, idx: int, scene: Dict):
        """Generate title scene code."""
        self.imports_needed.update({"VGroup", "DOWN", "UP", "ORIGIN"})
        
        title = scene.get("title", "Title")
        # Escape quotes in title
        title = title.replace('"', '\\"')
        
        code = f'''
class TitleScene{idx}(Scene):
    def construct(self):
        # Title text
        title = Text("{title}", font_size=48)
        title.move_to(ORIGIN)
        
        # Animate
        self.play(Write(title), run_time=1.5)
        self.wait({scene.get("duration", 2.0) - 1.5})
        self.play(FadeOut(title))
'''
        self.scene_classes.append(("TitleScene" + str(idx), code))
    
    def _generate_entity_scene(self, idx: int, scene: Dict):
        """Generate entity introduction scene code."""
        self.imports_needed.update({"Rectangle", "RoundedRectangle", "VGroup", "DOWN", "UP", "ORIGIN", "LEFT", "RIGHT"})
        
        entities = scene.get("entities", [])
        if not entities:
            return
        
        entity = entities[0]
        name = entity.get("name", "Entity").replace('"', '\\"')
        etype = entity.get("type", "Unknown")
        style = scene.get("style", {})
        color = hex_to_manim_color(style.get("color", "#3498db"))
        
        code = f'''
class EntityScene{idx}(Scene):
    def construct(self):
        # Entity box
        box = RoundedRectangle(
            corner_radius=0.2,
            width=5,
            height=2,
            color={color},
            fill_opacity=0.3
        )
        
        # Entity name
        name = Text("{name}", font_size=36)
        name.move_to(box.get_center())
        
        # Type label
        type_label = Text("{etype}", font_size=20, color=GRAY)
        type_label.next_to(box, UP)
        
        group = VGroup(box, name, type_label)
        group.move_to(ORIGIN)
        
        # Animate
        self.play(Create(box), run_time=0.5)
        self.play(Write(name), Write(type_label), run_time=1.0)
        self.wait({scene.get("duration", 2.5) - 1.5})
        self.play(FadeOut(group))
'''
        self.scene_classes.append(("EntityScene" + str(idx), code))
    
    def _generate_relation_scene(self, idx: int, scene: Dict):
        """Generate relation scene code."""
        self.imports_needed.update({"Rectangle", "RoundedRectangle", "Arrow", "VGroup", 
                                   "DOWN", "UP", "ORIGIN", "LEFT", "RIGHT", "MathTex"})
        
        entities = scene.get("entities", [])
        relations = scene.get("relations", [])
        
        if len(entities) < 2:
            return
        
        source = entities[0]
        target = entities[1]
        source_name = source.get("name", "A").replace('"', '\\"')
        target_name = target.get("name", "B").replace('"', '\\"')
        
        rel_type = relations[0].get("type", "relates_to") if relations else "relates_to"
        style = scene.get("style", {})
        color = hex_to_manim_color(style.get("color", "#3498db"))
        label = style.get("label", rel_type)
        
        code = f'''
class RelationScene{idx}(Scene):
    def construct(self):
        # Source entity
        source_box = RoundedRectangle(
            corner_radius=0.15,
            width=3,
            height=1.2,
            color=BLUE,
            fill_opacity=0.3
        )
        source_box.shift(LEFT * 3.5)
        source_text = Text("{source_name}", font_size=24)
        source_text.move_to(source_box.get_center())
        source_group = VGroup(source_box, source_text)
        
        # Target entity
        target_box = RoundedRectangle(
            corner_radius=0.15,
            width=3,
            height=1.2,
            color=GREEN,
            fill_opacity=0.3
        )
        target_box.shift(RIGHT * 3.5)
        target_text = Text("{target_name}", font_size=24)
        target_text.move_to(target_box.get_center())
        target_group = VGroup(target_box, target_text)
        
        # Relation arrow
        arrow = Arrow(
            source_box.get_right(),
            target_box.get_left(),
            buff=0.1,
            color={color},
            stroke_width=4
        )
        
        # Relation label
        label = Text("{label}", font_size=18, color={color})
        label.next_to(arrow, UP, buff=0.1)
        
        # Animate
        self.play(Create(source_box), Create(target_box), run_time=0.5)
        self.play(Write(source_text), Write(target_text), run_time=0.5)
        self.play(Create(arrow), run_time=0.5)
        self.play(Write(label), run_time=0.3)
        self.wait({scene.get("duration", 3.0) - 1.8})
        self.play(FadeOut(VGroup(source_group, target_group, arrow, label)))
'''
        self.scene_classes.append(("RelationScene" + str(idx), code))
    
    def _generate_comparison_scene(self, idx: int, scene: Dict):
        """Generate comparison scene with multiple relations."""
        self.imports_needed.update({"Rectangle", "RoundedRectangle", "Arrow", "VGroup",
                                   "DOWN", "UP", "ORIGIN", "LEFT", "RIGHT", "Dot"})
        
        entities = scene.get("entities", [])
        relations = scene.get("relations", [])
        style = scene.get("style", {})
        color = hex_to_manim_color(style.get("color", "#e67e22"))
        title = scene.get("title", "Comparison").replace('"', '\\"')
        
        # Build entity positions
        num_entities = min(len(entities), 6)
        
        code = f'''
class ComparisonScene{idx}(Scene):
    def construct(self):
        # Title
        title = Text("{title}", font_size=32)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.5)
        
        # Entities
        entities = []
        positions = [
            LEFT * 4 + UP * 1,
            LEFT * 4 + DOWN * 1,
            RIGHT * 4 + UP * 1,
            RIGHT * 4 + DOWN * 1,
            UP * 2,
            DOWN * 2,
        ]
        
        entity_data = {[repr(e.get("name", f"E{i}")) for i, e in enumerate(entities[:6])]}
        
        for i, name in enumerate(entity_data[:{num_entities}]):
            box = RoundedRectangle(
                corner_radius=0.1,
                width=2.5,
                height=0.8,
                color={color},
                fill_opacity=0.2
            )
            box.move_to(positions[i])
            text = Text(name, font_size=18)
            text.move_to(box.get_center())
            group = VGroup(box, text)
            entities.append(group)
            self.play(FadeIn(group), run_time=0.3)
        
        self.wait({scene.get("duration", 4.0) - 1.5})
        self.play(*[FadeOut(e) for e in entities], FadeOut(title))
'''
        self.scene_classes.append(("ComparisonScene" + str(idx), code))
    
    def _generate_overview_scene(self, idx: int, scene: Dict):
        """Generate graph overview scene."""
        self.imports_needed.update({"Graph", "Dot", "Line", "VGroup", "ORIGIN", 
                                   "LEFT", "RIGHT", "UP", "DOWN", "np"})
        
        entities = scene.get("entities", [])
        relations = scene.get("relations", [])
        title = scene.get("title", "Knowledge Graph Overview").replace('"', '\\"')
        
        # Build vertex and edge lists
        vertices = [e.get("id", f"v{j}") for j, e in enumerate(entities[:8])]
        vertex_names = [e.get("name", f"V{j}")[:15] for j, e in enumerate(entities[:8])]
        
        edges = []
        for rel in relations[:12]:
            src = rel.get("source")
            tgt = rel.get("target")
            if src in vertices and tgt in vertices:
                edges.append((src, tgt))
        
        code = f'''
class OverviewScene{idx}(Scene):
    def construct(self):
        import numpy as np
        
        # Title
        title = Text("{title}", font_size=28)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.5)
        
        # Create nodes manually
        vertices = {repr(vertices)}
        vertex_names = {repr(vertex_names)}
        edges = {repr(edges)}
        
        # Position nodes in a circle
        n = len(vertices)
        radius = 2.5
        node_groups = []
        node_positions = {{}}
        
        for i, (vid, vname) in enumerate(zip(vertices, vertex_names)):
            angle = 2 * np.pi * i / n - np.pi / 2
            pos = np.array([radius * np.cos(angle), radius * np.sin(angle), 0])
            
            dot = Dot(pos, color=BLUE, radius=0.15)
            label = Text(vname, font_size=14)
            label.next_to(dot, DOWN, buff=0.1)
            group = VGroup(dot, label)
            node_groups.append(group)
            node_positions[vid] = pos
        
        # Create edges
        edge_lines = []
        for src, tgt in edges:
            if src in node_positions and tgt in node_positions:
                line = Line(
                    node_positions[src],
                    node_positions[tgt],
                    color=GRAY,
                    stroke_width=1.5
                )
                edge_lines.append(line)
        
        # Animate
        self.play(*[Create(line) for line in edge_lines], run_time=1.0)
        self.play(*[FadeIn(node) for node in node_groups], run_time=1.0)
        self.wait({scene.get("duration", 4.0) - 2.5})
        self.play(
            *[FadeOut(node) for node in node_groups],
            *[FadeOut(line) for line in edge_lines],
            FadeOut(title)
        )
'''
        self.scene_classes.append(("OverviewScene" + str(idx), code))
    
    def _generate_finding_scene(self, idx: int, scene: Dict):
        """Generate finding/conclusion scene."""
        self.imports_needed.update({"VGroup", "DOWN", "UP", "ORIGIN", "Star", "SurroundingRectangle"})
        
        entities = scene.get("entities", [])
        finding_text = entities[0].get("name", "Key Finding") if entities else "Key Finding"
        finding_text = finding_text.replace('"', '\\"')
        
        # Truncate if too long
        if len(finding_text) > 80:
            finding_text = finding_text[:77] + "..."
        
        code = f'''
class FindingScene{idx}(Scene):
    def construct(self):
        # Icon
        star = Star(n=5, outer_radius=0.5, color=YELLOW, fill_opacity=0.8)
        star.shift(UP * 1.5)
        
        # Finding text
        finding = Text("{finding_text}", font_size=24)
        finding.next_to(star, DOWN, buff=0.5)
        
        # Highlight box
        box = SurroundingRectangle(finding, color=YELLOW, buff=0.2)
        
        group = VGroup(star, finding, box)
        group.move_to(ORIGIN)
        
        # Animate
        self.play(Create(star), run_time=0.5)
        self.play(Write(finding), run_time=1.0)
        self.play(Create(box), run_time=0.5)
        self.wait({scene.get("duration", 3.5) - 2.0})
        self.play(FadeOut(group))
'''
        self.scene_classes.append(("FindingScene" + str(idx), code))
    
    def _generate_generic_scene(self, idx: int, scene: Dict):
        """Generate generic scene for unknown types."""
        title = scene.get("title", "Scene").replace('"', '\\"')
        
        code = f'''
class GenericScene{idx}(Scene):
    def construct(self):
        text = Text("{title}", font_size=36)
        self.play(Write(text))
        self.wait({scene.get("duration", 2.0)})
        self.play(FadeOut(text))
'''
        self.scene_classes.append(("GenericScene" + str(idx), code))
    
    def _generate_main_scene(self):
        """Generate main scene that combines all subscenes."""
        if not self.scene_classes:
            return
        
        # Build the construct method
        scene_calls = []
        for class_name, _ in self.scene_classes:
            scene_calls.append(f"        {class_name}().construct.__func__(self)")
        
        calls_code = "\n".join(scene_calls)
        
        code = f'''
class KnowledgeGraphAnimation(Scene):
    """Main scene combining all subscenes."""
    def construct(self):
        # Play all scenes in sequence
{calls_code}
'''
        self.scene_classes.append(("KnowledgeGraphAnimation", code))
    
    def _assemble_code(self) -> str:
        """Assemble all code into a single file."""
        # Add color constants to imports
        color_constants = {"BLUE", "GREEN", "YELLOW", "PURPLE", "RED", "ORANGE", "GRAY", "TEAL", "WHITE"}
        self.imports_needed.update(color_constants)
        
        # Imports
        imports = sorted(self.imports_needed)
        import_line = f"from manim import {', '.join(imports)}"
        
        header = f'''# -*- coding: utf-8 -*-
"""
Auto-generated Manim animation code from Knowledge Graph.
Generated scenes: {len(self.scene_classes)}
"""
{import_line}
import numpy as np
'''
        
        # Combine all scene classes
        scenes_code = "\n".join(code for _, code in self.scene_classes)
        
        # Main block
        main_block = '''

if __name__ == "__main__":
    # To render: manim -pql this_file.py KnowledgeGraphAnimation
    pass
'''
        
        return header + scenes_code + main_block


def generate_code(scenes: List[Dict[str, Any]]) -> str:
    """
    Generate Manim Python code from storyboard scenes.
    
    Args:
        scenes: List of scene dicts from storyboard
        
    Returns:
        Complete Python code string
    """
    generator = ManimCodeGenerator(scenes)
    return generator.generate()


def render_animation(
    scenes: List[Dict[str, Any]],
    output_path: str = "output/animation.mp4",
    quality: str = "medium_quality",  # low_quality, medium_quality, high_quality
    preview: bool = False
) -> Optional[str]:
    """
    Generate and render Manim animation.
    
    Args:
        scenes: List of scene dicts from storyboard
        output_path: Path for output video
        quality: Render quality
        preview: Open preview after rendering
        
    Returns:
        Path to rendered video, or None if failed
    """
    # Generate code
    code = generate_code(scenes)
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        # Prepare output directory - 统一使用 output/media_files
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 确定媒体输出目录 (统一到 output/media_files)
        if "output" in output_dir:
            # 找到 output 目录并使用 output/media_files
            output_base = output_dir
            while output_base and os.path.basename(output_base) != "output":
                output_base = os.path.dirname(output_base)
            if output_base:
                media_dir = os.path.join(output_base, "media_files")
            else:
                media_dir = os.path.join(output_dir, "media")
        else:
            media_dir = os.path.join(output_dir, "media")
        os.makedirs(media_dir, exist_ok=True)
        
        # Quality flags
        quality_flag = {
            "low_quality": "-ql",
            "medium_quality": "-qm", 
            "high_quality": "-qh",
            "production_quality": "-qk"
        }.get(quality, "-qm")
        
        # Build command
        cmd = ["manim", quality_flag]
        if preview:
            cmd.append("-p")
        cmd.extend([temp_path, "KnowledgeGraphAnimation"])
        cmd.extend(["-o", os.path.basename(output_path)])
        cmd.extend(["--media_dir", media_dir])
        
        # Run manim
        print(f"[Manim] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"[Manim] Success! Output: {output_path}")
            return output_path
        else:
            print(f"[Manim] Error: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("[Manim] Rendering timed out")
        return None
    except Exception as e:
        print(f"[Manim] Exception: {e}")
        return None
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


def save_code(scenes: List[Dict[str, Any]], output_path: str) -> str:
    """
    Save generated Manim code to a file.
    
    Args:
        scenes: List of scene dicts from storyboard
        output_path: Path to save the Python file
        
    Returns:
        Path to saved file
    """
    code = generate_code(scenes)
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"[Manim] Code saved to: {output_path}")
    return output_path
