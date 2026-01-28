# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Entity(BaseModel):
    id: str
    type: str  # Method, Dataset, Metric, Task, Finding, Paper
    name: str
    props: Dict[str, Any] = {}

class Relation(BaseModel):
    source: str
    target: str
    type: str  # uses, evaluated_on, achieves, supports, contradicts, outperform

class ContextEdge(BaseModel):
    relation: Relation
    context: Dict[str, Any]  # e.g., {"model_size": "7B", "setting": "zero-shot", "hardware": "A100"}
    evidence: List[str] = []  # sentences or figure captions
    confidence: Optional[float] = None

class Hypothesis(BaseModel):
    id: str
    text: str
    links: List[str]  # entity ids this hypothesis connects
    rationale: Optional[str] = None

class Triplet(BaseModel):
    head: Entity
    relation: str
    tail: Entity
    context: Optional[Dict[str, Any]] = None
    evidence: Optional[List[str]] = None
