"""
String Diagram Generator MCP Server
====================================

Category-theoretic visualization for any composition.

Input schemas:
- GenericComposition: Universal — any category's objects and morphisms
- BrickComposition: Lushy-specific — 4-layer bricks with grades

Render styles:
- generic_compact: Universal renderer reading visual hints
- compact: ZX-style compact nodes (brick-specific)
- box: Original box-and-wire (brick-specific)
"""

from .foundation import (
    BrickComposition, Brick, Layer, Connection,
    StringDiagram, DiagramPrimitives,
    create_sample_brick, create_sample_composition,
    validate_composition
)
from .generic import (
    GenericComposition, GenericNode, GenericEdge,
    NodeVisual, EdgeVisual,
    parse_generic_composition, validate_generic_composition,
    create_sample_generic_sequential,
    create_sample_generic_quantum,
    create_sample_generic_branching,
)
from .generic_renderer import GenericCompactRenderer
from .adapters import brick_to_generic
from .brick import StringDiagramBrick, create_string_diagram
from .contextual import CostAnalyzer, SVGRenderer, CompactSVGRenderer

__version__ = "2.0.0"
