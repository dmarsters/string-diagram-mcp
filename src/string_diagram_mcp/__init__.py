"""
String Diagram Generator MCP Server v2.0
=========================================

Category-theoretic visualization for any composition.

Two input schemas:
  GenericComposition — any category (nodes + edges + visual hints)
  BrickComposition  — Lushy-specific (4-layer bricks with grades)

Three pipelines:
  Generic   — GenericComposition → GenericCompactRenderer
  Brick     — BrickComposition → SVGRenderer | CompactSVGRenderer  
  Adapted   — BrickComposition → LushyBrickAdapter → GenericCompactRenderer
"""

from foundation import (
    # Core types
    Point, Annotation, CostSummary, StringDiagram,
    Layout, BrickPosition, Wire, WireRouting,
    # Generic schema
    GenericComposition, Node, Edge, NodeVisual, EdgeVisual,
    validate_generic_composition,
    # Lushy schema
    BrickComposition, Brick, Layer, Connection,
    validate_composition,
    create_sample_brick, create_sample_composition,
)
from brick import StringDiagramBrick, create_string_diagram
from contextual import CostAnalyzer, SVGRenderer, CompactSVGRenderer
from generic_pipeline import (
    GenericDiagramGenerator,
    GenericLayoutComputer, GenericWireRouter, GenericCompactRenderer,
)
from adapters import LushyBrickAdapter, ZXCalculusAdapter

__version__ = "2.0.0"
