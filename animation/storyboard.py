# -*- coding: utf-8 -*-
"""
Generate storyboard scenes from Knowledge Graph for Manim animation.
Supports multiple scene types for visualizing entities and relations.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class SceneType(Enum):
    """Types of animation scenes."""
    TITLE = "title"                    # 标题场景
    ENTITY_INTRO = "entity_intro"      # 实体介绍
    RELATION = "relation"              # 关系展示
    COMPARISON = "comparison"          # 对比场景
    GRAPH_OVERVIEW = "graph_overview"  # 图谱总览
    FINDING = "finding"                # 研究发现
    TIMELINE = "timeline"              # 时间线


@dataclass
class Scene:
    """A single scene in the storyboard."""
    scene_type: SceneType
    title: str
    duration: float = 3.0  # seconds
    entities: List[Dict] = field(default_factory=list)
    relations: List[Dict] = field(default_factory=list)
    narration: str = ""
    style: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_type": self.scene_type.value,
            "title": self.title,
            "duration": self.duration,
            "entities": self.entities,
            "relations": self.relations,
            "narration": self.narration,
            "style": self.style
        }


# Relation type to visual style mapping
RELATION_STYLES = {
    "uses": {"color": "#3498db", "arrow": "->", "label": "使用"},
    "evaluated_on": {"color": "#2ecc71", "arrow": "->", "label": "评估于"},
    "achieves": {"color": "#f1c40f", "arrow": "->", "label": "达成"},
    "supports": {"color": "#9b59b6", "arrow": "->", "label": "支持"},
    "contradicts": {"color": "#e74c3c", "arrow": "<->", "label": "矛盾"},
    "outperform": {"color": "#e67e22", "arrow": ">>", "label": "优于"},
}

# Entity type to visual style mapping
ENTITY_STYLES = {
    "Method": {"color": "#3498db", "shape": "rectangle", "icon": "⚙️"},
    "Dataset": {"color": "#2ecc71", "shape": "cylinder", "icon": "📊"},
    "Metric": {"color": "#f1c40f", "shape": "diamond", "icon": "📏"},
    "Task": {"color": "#9b59b6", "shape": "hexagon", "icon": "🎯"},
    "Finding": {"color": "#e74c3c", "shape": "star", "icon": "💡"},
    "Paper": {"color": "#34495e", "shape": "document", "icon": "📄"},
    "Hypothesis": {"color": "#1abc9c", "shape": "cloud", "icon": "🔮"},
}


class StoryboardGenerator:
    """Generate storyboard from Knowledge Graph."""
    
    def __init__(self, kg_dict: Dict[str, Any]):
        self.kg = kg_dict
        self.nodes = {n["id"]: n for n in kg_dict.get("nodes", [])}
        self.edges = kg_dict.get("edges", [])
        self.scenes: List[Scene] = []
    
    def generate(self, 
                 include_title: bool = True,
                 include_overview: bool = True,
                 group_by_relation: bool = True,
                 max_scenes: int = 10) -> List[Scene]:
        """
        Generate complete storyboard from KG.
        
        Args:
            include_title: Add title scene at the beginning
            include_overview: Add graph overview scene
            group_by_relation: Group relations by type
            max_scenes: Maximum number of scenes to generate
        
        Returns:
            List of Scene objects
        """
        self.scenes = []
        
        # 1. Title scene
        if include_title:
            self._add_title_scene()
        
        # 2. Entity introduction scenes (key entities only)
        key_entities = self._identify_key_entities()
        for entity in key_entities[:3]:  # Top 3 entities
            self._add_entity_scene(entity)
        
        # 3. Relation scenes
        if group_by_relation:
            self._add_grouped_relation_scenes()
        else:
            for edge in self.edges[:max_scenes - len(self.scenes)]:
                self._add_relation_scene(edge)
        
        # 4. Overview scene
        if include_overview and len(self.nodes) > 2:
            self._add_overview_scene()
        
        # 5. Finding/Conclusion scenes
        findings = [n for n in self.nodes.values() if n.get("type") == "Finding"]
        for finding in findings[:2]:
            self._add_finding_scene(finding)
        
        return self.scenes[:max_scenes]
    
    def _add_title_scene(self):
        """Add title scene."""
        # Try to find paper entity for title
        papers = [n for n in self.nodes.values() if n.get("type") == "Paper"]
        if papers:
            title = papers[0].get("name", "Research Overview")
        else:
            title = "Knowledge Graph Visualization"
        
        self.scenes.append(Scene(
            scene_type=SceneType.TITLE,
            title=title,
            duration=2.0,
            narration=f"欢迎观看：{title}"
        ))
    
    def _add_entity_scene(self, entity: Dict):
        """Add entity introduction scene."""
        etype = entity.get("type", "Unknown")
        name = entity.get("name", "")
        props = entity.get("props", {})
        
        style = ENTITY_STYLES.get(etype, ENTITY_STYLES["Method"])
        
        self.scenes.append(Scene(
            scene_type=SceneType.ENTITY_INTRO,
            title=f"{style['icon']} {name}",
            duration=2.5,
            entities=[entity],
            narration=f"{etype}: {name}",
            style=style
        ))
    
    def _add_relation_scene(self, edge: Dict):
        """Add relation scene."""
        rel_type = edge.get("type", "relates_to")
        source_id = edge.get("source")
        target_id = edge.get("target")
        
        source = self.nodes.get(source_id, {"id": source_id, "name": source_id})
        target = self.nodes.get(target_id, {"id": target_id, "name": target_id})
        
        style = RELATION_STYLES.get(rel_type, RELATION_STYLES["uses"])
        
        # Generate narration
        narration = f"{source.get('name', source_id)} {style['label']} {target.get('name', target_id)}"
        
        self.scenes.append(Scene(
            scene_type=SceneType.RELATION,
            title=f"{style['label']}: {source.get('name', '')} → {target.get('name', '')}",
            duration=3.0,
            entities=[source, target],
            relations=[edge],
            narration=narration,
            style=style
        ))
    
    def _add_grouped_relation_scenes(self):
        """Add scenes grouped by relation type."""
        # Group edges by type
        by_type: Dict[str, List[Dict]] = {}
        for edge in self.edges:
            rel_type = edge.get("type", "other")
            by_type.setdefault(rel_type, []).append(edge)
        
        # Prioritize important relations
        priority = ["outperform", "contradicts", "achieves", "supports", "evaluated_on", "uses"]
        
        for rel_type in priority:
            if rel_type in by_type:
                edges = by_type[rel_type]
                if len(edges) == 1:
                    self._add_relation_scene(edges[0])
                else:
                    self._add_comparison_scene(rel_type, edges)
    
    def _add_comparison_scene(self, rel_type: str, edges: List[Dict]):
        """Add comparison scene for multiple relations of same type."""
        style = RELATION_STYLES.get(rel_type, RELATION_STYLES["uses"])
        
        entities = []
        for edge in edges[:4]:  # Max 4 relations per comparison
            source = self.nodes.get(edge["source"], {"id": edge["source"], "name": edge["source"]})
            target = self.nodes.get(edge["target"], {"id": edge["target"], "name": edge["target"]})
            if source not in entities:
                entities.append(source)
            if target not in entities:
                entities.append(target)
        
        self.scenes.append(Scene(
            scene_type=SceneType.COMPARISON,
            title=f"对比: {style['label']}",
            duration=4.0,
            entities=entities,
            relations=edges[:4],
            narration=f"对比分析: {len(edges)} 组 {style['label']} 关系",
            style=style
        ))
    
    def _add_overview_scene(self):
        """Add graph overview scene."""
        self.scenes.append(Scene(
            scene_type=SceneType.GRAPH_OVERVIEW,
            title="知识图谱总览",
            duration=4.0,
            entities=list(self.nodes.values())[:10],
            relations=self.edges[:15],
            narration=f"共 {len(self.nodes)} 个实体，{len(self.edges)} 个关系"
        ))
    
    def _add_finding_scene(self, finding: Dict):
        """Add finding/conclusion scene."""
        self.scenes.append(Scene(
            scene_type=SceneType.FINDING,
            title="研究发现",
            duration=3.5,
            entities=[finding],
            narration=finding.get("name", ""),
            style=ENTITY_STYLES["Finding"]
        ))
    
    def _identify_key_entities(self) -> List[Dict]:
        """Identify key entities based on connection count."""
        # Count connections for each node
        connection_count = {n: 0 for n in self.nodes}
        for edge in self.edges:
            if edge["source"] in connection_count:
                connection_count[edge["source"]] += 1
            if edge["target"] in connection_count:
                connection_count[edge["target"]] += 1
        
        # Sort by connection count
        sorted_ids = sorted(connection_count.keys(), 
                          key=lambda x: connection_count[x], reverse=True)
        
        return [self.nodes[nid] for nid in sorted_ids if nid in self.nodes]


def storyboard_from_kg(kg_dict: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
    """
    Generate storyboard scenes from Knowledge Graph.
    
    Args:
        kg_dict: Knowledge graph dict with "nodes" and "edges"
        **kwargs: Options passed to StoryboardGenerator.generate()
    
    Returns:
        List of scene dicts
    """
    generator = StoryboardGenerator(kg_dict)
    scenes = generator.generate(**kwargs)
    return [s.to_dict() for s in scenes]


# Convenience function for simple use case
def quick_storyboard(kg_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a quick 5-scene storyboard."""
    return storyboard_from_kg(kg_dict, max_scenes=5, include_overview=False)
