# -*- coding: utf-8 -*-
from typing import Dict, Any, List
import networkx as nx
from .schema import Entity, Relation, ContextEdge, Hypothesis, Triplet

class KnowledgeGraph:
    """NetworkX-backed KG with L1/L2/L3 logic.
    - L1: entities + bare relations
    - L2: context-aware edges as attributes
    - L3: hypothesis nodes
    """
    def __init__(self):
        self.G = nx.MultiDiGraph()

    # L1
    def add_entity(self, e: Entity):
        self.G.add_node(e.id, **{"type": e.type, "name": e.name, "props": e.props})

    def add_relation(self, r: Relation):
        self.G.add_edge(r.source, r.target, key=r.type, **{"type": r.type})

    # L2
    def add_context_edge(self, ce: ContextEdge):
        # store context attributes on the edge
        self.G.add_edge(
            ce.relation.source,
            ce.relation.target,
            key=ce.relation.type,
            **{"type": ce.relation.type, "context": ce.context, "evidence": ce.evidence, "confidence": ce.confidence}
        )

    # Convenience for Triplet
    def add_triplet(self, t: Triplet):
        self.add_entity(t.head)
        self.add_entity(t.tail)
        rel = Relation(source=t.head.id, target=t.tail.id, type=t.relation)
        if t.context or t.evidence:
            self.add_context_edge(ContextEdge(relation=rel, context=t.context or {}, evidence=t.evidence or [], confidence=None))
        else:
            self.add_relation(rel)

    # L3
    def add_hypothesis(self, h: Hypothesis):
        self.G.add_node(h.id, **{"type": "Hypothesis", "name": h.text, "rationale": h.rationale})
        # connect hypothesis to linked entities as dashed semantics (store style)
        for eid in h.links:
            if eid in self.G.nodes:
                self.G.add_edge(h.id, eid, key="suggests", **{"type": "suggests", "style": "dashed"})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [{"id": n, **self.G.nodes[n]} for n in self.G.nodes],
            "edges": [{"source": u, "target": v, "key": k, **data} for u, v, k, data in self.G.edges(keys=True, data=True)]
        }
