"""
Generic Composition Schema
===========================

Universal input schema for string diagram generation.
Accepts any category's objects and morphisms as nodes and edges.

Three tiers of input quality:
  Bare:   id + name on nodes, source + target on edges
  Typed:  + input_type/output_type on nodes, label on edges
  Styled: + visual hints (color, shape, size, badge, wire weight)

Domain-specific adapters map from concrete types
(BrickComposition, ZX circuits, etc.) into this schema.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Literal


# ============================================================================
# VISUAL HINTS
# ============================================================================

# Valid node shapes the renderer supports
NodeShape = Literal['circle', 'pill', 'diamond', 'square', 'point']


@dataclass
class NodeVisual:
    """
    Renderer-facing visual hints for a node.
    
    All fields optional — renderer picks sensible defaults.
    """
    color: Optional[str] = None           # Fill color (hex). Default: #10b981
    shape: NodeShape = 'circle'           # Node shape
    size: Literal['small', 'medium', 'large'] = 'medium'
    badge: Optional[str] = None           # Small label in top-right (e.g. "G1", "π/4")
    badge_color: Optional[str] = None     # Badge ring color. Default: same as color
    opacity: float = 1.0                  # Node opacity [0-1]
    glow: bool = False                    # Apply glow filter (for emphasis)
    ring_colors: Optional[List[str]] = None  # Layer ring arc colors (up to 8)
    ring_weights: Optional[List[float]] = None  # Ring arc stroke widths


@dataclass
class EdgeVisual:
    """
    Renderer-facing visual hints for an edge.
    
    All fields optional — renderer picks sensible defaults.
    """
    color: Optional[str] = None           # Wire color (hex). Default: from source node
    style: Literal['solid', 'dashed', 'dotted'] = 'solid'
    weight: float = 1.0                   # Thickness multiplier [0.5 - 3.0]
    opacity: float = 0.8
    show_label: bool = True               # Show edge label on wire


# ============================================================================
# CORE SCHEMA
# ============================================================================

@dataclass
class GenericNode:
    """
    A node (morphism) in a composition.
    
    Bare minimum: id, name
    Typed: + input_type, output_type
    Styled: + visual, properties
    """
    id: str
    name: str
    
    # Typing (optional)
    input_type: Optional[str] = None      # Type flowing in (e.g. "Qubit", "CSV")
    output_type: Optional[str] = None     # Type flowing out
    
    # Domain-specific properties (opaque to renderer)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Visual hints (renderer contract)
    visual: Optional[NodeVisual] = field(default_factory=NodeVisual)
    
    # Free-form metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenericEdge:
    """
    An edge (wire / object) connecting two nodes.
    
    Bare minimum: source, target
    Typed: + label
    Styled: + visual
    """
    source: str                           # Source node id
    target: str                           # Target node id
    
    # Typing (optional)
    label: Optional[str] = None           # Object type label on wire
    
    # Visual hints
    visual: Optional[EdgeVisual] = field(default_factory=EdgeVisual)
    
    # Free-form metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenericComposition:
    """
    Complete composition graph — the universal input schema.
    
    This is the contract between any domain and the renderer.
    """
    nodes: List[GenericNode]
    edges: List[GenericEdge]
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    # metadata typically includes:
    #   name: str          — diagram title
    #   category: str      — domain hint ("quantum", "lushy", "workflow")
    #   description: str   — subtitle or description


# ============================================================================
# VALIDATION
# ============================================================================

def validate_generic_composition(composition: GenericComposition) -> List[str]:
    """
    Validate a generic composition.
    
    Checks:
    - No duplicate node IDs
    - All edges reference valid nodes
    - Node shapes are valid
    
    Returns: List of error messages (empty if valid)
    """
    errors = []
    
    # Check for duplicate IDs
    node_ids = [n.id for n in composition.nodes]
    if len(node_ids) != len(set(node_ids)):
        dupes = [nid for nid in node_ids if node_ids.count(nid) > 1]
        errors.append(f"Duplicate node IDs: {set(dupes)}")
    
    # Check edges reference valid nodes
    node_id_set = set(node_ids)
    for edge in composition.edges:
        if edge.source not in node_id_set:
            errors.append(f"Edge references unknown source: {edge.source}")
        if edge.target not in node_id_set:
            errors.append(f"Edge references unknown target: {edge.target}")
    
    # Check valid shapes
    valid_shapes = {'circle', 'pill', 'diamond', 'square', 'point'}
    for node in composition.nodes:
        if node.visual and node.visual.shape not in valid_shapes:
            errors.append(f"Node {node.id} has invalid shape: {node.visual.shape}")
    
    return errors


# ============================================================================
# JSON PARSING
# ============================================================================

def parse_generic_composition(data: dict) -> GenericComposition:
    """
    Parse a JSON dict into GenericComposition.
    
    Handles all three tiers gracefully — missing fields get defaults.
    """
    nodes = []
    for node_data in data.get('nodes', []):
        # Parse visual hints
        visual = NodeVisual()
        if 'visual' in node_data and node_data['visual']:
            v = node_data['visual']
            visual = NodeVisual(
                color=v.get('color'),
                shape=v.get('shape', 'circle'),
                size=v.get('size', 'medium'),
                badge=v.get('badge'),
                badge_color=v.get('badge_color'),
                opacity=v.get('opacity', 1.0),
                glow=v.get('glow', False),
                ring_colors=v.get('ring_colors'),
                ring_weights=v.get('ring_weights'),
            )
        
        nodes.append(GenericNode(
            id=node_data['id'],
            name=node_data['name'],
            input_type=node_data.get('input_type'),
            output_type=node_data.get('output_type'),
            properties=node_data.get('properties', {}),
            visual=visual,
            metadata=node_data.get('metadata', {})
        ))
    
    edges = []
    for edge_data in data.get('edges', []):
        visual = EdgeVisual()
        if 'visual' in edge_data and edge_data['visual']:
            v = edge_data['visual']
            visual = EdgeVisual(
                color=v.get('color'),
                style=v.get('style', 'solid'),
                weight=v.get('weight', 1.0),
                opacity=v.get('opacity', 0.8),
                show_label=v.get('show_label', True),
            )
        
        edges.append(GenericEdge(
            source=edge_data['source'],
            target=edge_data['target'],
            label=edge_data.get('label'),
            visual=visual,
            metadata=edge_data.get('metadata', {})
        ))
    
    return GenericComposition(
        nodes=nodes,
        edges=edges,
        metadata=data.get('metadata', {})
    )


# ============================================================================
# SAMPLE COMPOSITIONS
# ============================================================================

def create_sample_generic_sequential() -> GenericComposition:
    """Sample: simple 3-node sequential pipeline"""
    return GenericComposition(
        nodes=[
            GenericNode("parse", "Parse", input_type="RawData", output_type="Structured",
                       visual=NodeVisual(color="#10b981", badge="G0")),
            GenericNode("transform", "Transform", input_type="Structured", output_type="Processed",
                       visual=NodeVisual(color="#3b82f6", badge="G0")),
            GenericNode("synthesize", "Synthesize", input_type="Processed", output_type="Output",
                       visual=NodeVisual(color="#8b5cf6", badge="G1", glow=True)),
        ],
        edges=[
            GenericEdge("parse", "transform", label="Structured"),
            GenericEdge("transform", "synthesize", label="Processed",
                       visual=EdgeVisual(style="dashed", weight=1.5)),
        ],
        metadata={"name": "Sample Sequential Pipeline", "category": "generic"}
    )


def create_sample_generic_quantum() -> GenericComposition:
    """Sample: Bell state preparation circuit"""
    return GenericComposition(
        nodes=[
            GenericNode("q0_init", "|0⟩", output_type="Qubit",
                       visual=NodeVisual(color="#6b7280", shape="point", size="small")),
            GenericNode("q1_init", "|0⟩", output_type="Qubit",
                       visual=NodeVisual(color="#6b7280", shape="point", size="small")),
            GenericNode("h", "H", input_type="Qubit", output_type="Qubit",
                       properties={"spider_type": "H", "phase": 0.0},
                       visual=NodeVisual(color="#f59e0b", shape="square", badge="H")),
            GenericNode("cx", "CNOT", input_type="Qubit×Qubit", output_type="Qubit×Qubit",
                       properties={"spider_type": "Z", "is_entangling": True},
                       visual=NodeVisual(color="#ef4444", shape="circle", badge="CX", size="large")),
            GenericNode("q0_out", "β₀₀", input_type="Qubit",
                       visual=NodeVisual(color="#6b7280", shape="point", size="small")),
            GenericNode("q1_out", "β₀₀", input_type="Qubit",
                       visual=NodeVisual(color="#6b7280", shape="point", size="small")),
        ],
        edges=[
            GenericEdge("q0_init", "h", label="Qubit"),
            GenericEdge("h", "cx", label="Qubit"),
            GenericEdge("q1_init", "cx", label="Qubit"),
            GenericEdge("cx", "q0_out", label="Qubit"),
            GenericEdge("cx", "q1_out", label="Qubit"),
        ],
        metadata={"name": "Bell State Preparation", "category": "quantum"}
    )


def create_sample_generic_branching() -> GenericComposition:
    """Sample: branching workflow with merge"""
    return GenericComposition(
        nodes=[
            GenericNode("input", "Input Parser", input_type="CSV", output_type="ParsedData",
                       visual=NodeVisual(color="#10b981", badge="G0")),
            GenericNode("path_a", "Analysis A", input_type="ParsedData", output_type="ResultA",
                       visual=NodeVisual(color="#8b5cf6", badge="G1", glow=True)),
            GenericNode("path_b", "Analysis B", input_type="ParsedData", output_type="ResultB",
                       visual=NodeVisual(color="#8b5cf6", badge="G1", glow=True)),
            GenericNode("merge", "Merge", input_type="ResultA,ResultB", output_type="Final",
                       visual=NodeVisual(color="#f59e0b", shape="diamond", badge="⊗")),
        ],
        edges=[
            GenericEdge("input", "path_a", label="ParsedData"),
            GenericEdge("input", "path_b", label="ParsedData"),
            GenericEdge("path_a", "merge", label="ResultA",
                       visual=EdgeVisual(style="dashed", weight=1.5)),
            GenericEdge("path_b", "merge", label="ResultB",
                       visual=EdgeVisual(style="dashed", weight=1.5)),
        ],
        metadata={"name": "Branching Workflow", "category": "generic"}
    )
