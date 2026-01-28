# -*- coding: utf-8 -*-
"""LLM-driven entity and triplet extraction from text chunks.
Includes Schema validation via Pydantic and entity deduplication (synonym merging).
"""
import re
from typing import List, Dict, Optional
from pydantic import ValidationError
from utils.llm_client import LLMClient
from .schema import Entity, Triplet

SCHEMA_HINT = '{"entities": [{"id": "e1", "type": "Method|Dataset|Metric|Task|Finding|Paper", "name": "..."}], "triplets": [{"head": "e1", "relation": "uses|evaluated_on|achieves|supports|contradicts|outperform", "tail": "e2", "context": {}}]}'

VALID_ENTITY_TYPES = {"Method", "Dataset", "Metric", "Task", "Finding", "Paper"}
VALID_RELATION_TYPES = {"uses", "evaluated_on", "achieves", "supports", "contradicts", "outperform"}

PROMPT_TMPL = (
    "你是精准的信息抽取器。请从下面的科研文本中抽取实体与关系。\n"
    "要求：\n1) 严格JSON输出\n2) 实体类型仅限：Method, Dataset, Metric, Task, Finding, Paper\n"
    "3) Triplet关系仅限：uses, evaluated_on, achieves, supports, contradicts, outperform\n"
)

SYNONYM_PROMPT = (
    "你是实体归一化专家。给你一组实体名称，请识别其中的同义词/别名，返回JSON：\n"
    '{"synonyms": [{"canonical": "标准名", "aliases": ["别名1", "别名2"]}]}\n'
    "如果没有同义词，返回 {\"synonyms\": []}\n"
)


def extract_from_chunk(text: str) -> Dict:
    client = LLMClient()
    messages = [{"role": "user", "content": PROMPT_TMPL + "\n文本：\n" + text}]
    return client.chat_json(messages, schema_hint=SCHEMA_HINT, temperature=0.0)


def validate_entity(e: Dict) -> Optional[Entity]:
    """Validate entity dict against schema; return Entity or None if invalid."""
    try:
        ent = Entity(
            id=e.get("id", ""),
            type=e.get("type", ""),
            name=e.get("name", ""),
            props=e.get("props", {})
        )
        # Check type is valid
        if ent.type not in VALID_ENTITY_TYPES:
            return None
        if not ent.name.strip():
            return None
        return ent
    except ValidationError:
        return None


def validate_relation(rel_type: str) -> bool:
    return rel_type in VALID_RELATION_TYPES


def normalize_name(name: str) -> str:
    """Normalize entity name for comparison: lowercase, strip, collapse spaces."""
    return re.sub(r'\s+', ' ', name.lower().strip())


class EntityDeduplicator:
    """Manages entity deduplication using LLM-based synonym detection."""
    
    def __init__(self):
        self.canonical_map: Dict[str, str] = {}  # normalized_name -> canonical_id
        self.entities: Dict[str, Entity] = {}  # id -> Entity
        self.client = LLMClient()
    
    def detect_synonyms(self, entity_names: List[str]) -> Dict[str, str]:
        """Use LLM to detect synonyms among entity names.
        Returns: mapping from alias -> canonical name
        """
        if len(entity_names) < 2:
            return {}
        names_str = ", ".join(f'"{n}"' for n in entity_names)
        messages = [{"role": "user", "content": SYNONYM_PROMPT + f"实体列表: [{names_str}]"}]
        result = self.client.chat_json(messages, temperature=0.0)
        alias_map = {}
        for group in result.get("synonyms", []):
            canonical = group.get("canonical", "")
            for alias in group.get("aliases", []):
                alias_map[alias] = canonical
        return alias_map
    
    def add_entity(self, ent: Entity) -> Entity:
        """Add entity with deduplication. Returns canonical entity."""
        norm = normalize_name(ent.name)
        if norm in self.canonical_map:
            return self.entities[self.canonical_map[norm]]
        # Check for potential synonym with existing
        self.canonical_map[norm] = ent.id
        self.entities[ent.id] = ent
        return ent
    
    def batch_deduplicate(self, entities: List[Entity]) -> List[Entity]:
        """Batch process entities with LLM synonym detection."""
        if len(entities) < 2:
            return entities
        # Group by type for better synonym detection
        by_type: Dict[str, List[Entity]] = {}
        for e in entities:
            by_type.setdefault(e.type, []).append(e)
        
        result = []
        for etype, ents in by_type.items():
            names = [e.name for e in ents]
            alias_map = self.detect_synonyms(names)
            seen_canonical = {}
            for e in ents:
                canonical_name = alias_map.get(e.name, e.name)
                norm = normalize_name(canonical_name)
                if norm in seen_canonical:
                    # Merge: skip this duplicate
                    continue
                # Update name to canonical if it was an alias
                if e.name != canonical_name:
                    e = Entity(id=e.id, type=e.type, name=canonical_name, props=e.props)
                seen_canonical[norm] = e
                result.append(e)
        return result


def normalize(json_obj: Dict, deduplicate: bool = True) -> Dict:
    """Normalize extraction output to pydantic objects with validation and dedup."""
    # Validate entities
    valid_entities = []
    for e in json_obj.get("entities", []):
        ent = validate_entity(e)
        if ent:
            valid_entities.append(ent)
    
    # Deduplicate if requested
    if deduplicate and len(valid_entities) > 1:
        dedup = EntityDeduplicator()
        valid_entities = dedup.batch_deduplicate(valid_entities)
    
    # Build id map
    entities_map = {e.id: e for e in valid_entities}
    # Also map by normalized name for triplet resolution
    name_to_id = {normalize_name(e.name): e.id for e in valid_entities}
    
    # Validate triplets
    triplets: List[Triplet] = []
    for t in json_obj.get("triplets", []):
        rel = t.get("relation", "")
        if not validate_relation(rel):
            continue
        head = entities_map.get(t.get("head"))
        tail = entities_map.get(t.get("tail"))
        if head and tail:
            # Handle context: ensure it's a dict or convert
            raw_context = t.get("context")
            if raw_context is None:
                context_dict = None
            elif isinstance(raw_context, dict):
                context_dict = raw_context
            elif isinstance(raw_context, str):
                # LLM sometimes returns context as string - wrap it
                context_dict = {"description": raw_context} if raw_context else None
            else:
                context_dict = None
            
            # Handle evidence: ensure it's a list
            raw_evidence = t.get("evidence")
            if raw_evidence is None:
                evidence_list = None
            elif isinstance(raw_evidence, list):
                evidence_list = raw_evidence
            elif isinstance(raw_evidence, str):
                evidence_list = [raw_evidence] if raw_evidence else None
            else:
                evidence_list = None
            
            triplets.append(Triplet(
                head=head,
                relation=rel,
                tail=tail,
                context=context_dict,
                evidence=evidence_list
            ))
    
    return {"entities": valid_entities, "triplets": triplets}


class EntityExtractor:
    """High-level entity and relation extraction from text."""
    
    def __init__(self):
        self.client = LLMClient()
    
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract entities from text using LLM."""
        result = extract_from_chunk(text)
        entities = []
        for e in result.get("entities", []):
            entities.append({
                "type": e.get("type", "UNKNOWN"),
                "name": e.get("name", ""),
                "id": e.get("id", "")
            })
        return entities
    
    def extract_relations(self, text: str, entities: List[Dict]) -> List[Dict]:
        """Extract relations between entities from text using LLM."""
        result = extract_from_chunk(text)
        relations = []
        # Build entity id map
        entity_map = {e.get("id"): e.get("name") for e in entities}
        for t in result.get("triplets", []):
            head_id = t.get("head")
            tail_id = t.get("tail")
            relations.append({
                "source": entity_map.get(head_id, head_id),
                "relation": t.get("relation", ""),
                "target": entity_map.get(tail_id, tail_id)
            })
        return relations
    
    def extract_all(self, text: str, deduplicate: bool = True) -> Dict:
        """Extract and normalize entities and relations."""
        raw = extract_from_chunk(text)
        return normalize(raw, deduplicate=deduplicate)
