"""
Domain Adapters
================

Convert domain-specific composition types into GenericComposition
for rendering by the generic compact renderer.

Each adapter maps domain ontology → visual hints:
  Lushy bricks:  grade → color, layers → ring arcs, tokens → wire weight
  ZX circuits:   spider_type → color, phase → badge, entangling → glow
  (future):      any domain → GenericComposition
"""

from typing import Optional
from .foundation import BrickComposition, Brick
from .generic import (
    GenericComposition, GenericNode, GenericEdge,
    NodeVisual, EdgeVisual
)


# ============================================================================
# LUSHY BRICK ADAPTER
# ============================================================================

# Brick layer colors (matches original renderer)
_LAYER_COLORS = {
    'foundation': '#6b7280',
    'structure':  '#10b981',
    'relational': '#3b82f6',
    'contextual': '#8b5cf6',
}

_GRADE_COLORS = {
    0: '#10b981',  # Green - deterministic
    1: '#8b5cf6',  # Purple - LLM
    2: '#ef4444',  # Red - human
}


def brick_to_generic(composition: BrickComposition) -> GenericComposition:
    """
    Convert a Lushy BrickComposition into a GenericComposition.
    
    Mapping:
      Brick           → GenericNode
      Connection       → GenericEdge
      max(grade)       → node color (green=G0, purple=G1)
      layer colors     → ring_colors
      layer grades     → ring_weights (thicker = LLM)
      grade badge      → node badge ("G0", "G1")
      LLM presence     → glow
      token cost       → edge weight
      has_llm wire     → dashed style
      branching wire   → composite color
    
    Args:
        composition: Lushy brick composition
        
    Returns:
        GenericComposition with full visual hints
    """
    nodes = []
    
    for brick in composition.bricks:
        # Compute grade summary
        det_layers = sum(1 for l in brick.layers if l.grade == 0)
        llm_layers = sum(1 for l in brick.layers if l.grade == 1)
        grade_max = max((l.grade for l in brick.layers), default=0)
        total_tokens = sum(l.estimated_tokens for l in brick.layers if l.grade == 1)
        has_llm = llm_layers > 0
        
        # Map to visual hints
        node_color = _GRADE_COLORS.get(grade_max, '#10b981')
        
        # Build layer ring
        ring_colors = [
            _LAYER_COLORS.get(l.name, '#6b7280')
            for l in brick.layers
        ]
        ring_weights = [
            5.0 if l.grade == 1 else 3.0
            for l in brick.layers
        ]
        
        # Size based on token cost
        if total_tokens > 200:
            size = 'large'
        elif total_tokens > 0:
            size = 'medium'
        else:
            size = 'small'
        
        visual = NodeVisual(
            color=node_color,
            shape='circle',
            size=size,
            badge=f"G{grade_max}",
            badge_color=node_color,
            glow=has_llm,
            ring_colors=ring_colors,
            ring_weights=ring_weights,
        )
        
        nodes.append(GenericNode(
            id=brick.id,
            name=brick.name,
            input_type=brick.input_schema,
            output_type=brick.output_schema,
            properties={
                'det_layers': det_layers,
                'llm_layers': llm_layers,
                'total_tokens': total_tokens,
                'grade_max': grade_max,
            },
            visual=visual,
            metadata=brick.metadata,
        ))
    
    # Convert connections to edges
    edges = []
    brick_map = {b.id: b for b in composition.bricks}
    
    # Find max tokens for weight normalization
    max_tokens = max(
        (sum(l.estimated_tokens for l in b.layers if l.grade == 1)
         for b in composition.bricks),
        default=1
    ) or 1
    
    for conn in composition.connections:
        source_brick = brick_map.get(conn.source_brick_id)
        if not source_brick:
            continue
        
        # Token cost from source brick
        source_tokens = sum(
            l.estimated_tokens for l in source_brick.layers if l.grade == 1
        )
        has_llm = any(l.grade == 1 for l in source_brick.layers)
        
        # Wire style from source grade
        if conn.is_branching:
            wire_color = '#667eea'
            wire_style = 'solid'
        elif has_llm:
            wire_color = '#8b5cf6'
            wire_style = 'dashed'
        else:
            wire_color = '#10b981'
            wire_style = 'solid'
        
        # Weight from token cost
        weight = 0.5 + 2.5 * (source_tokens / max_tokens) if source_tokens > 0 else 1.0
        
        # Label from output type
        label = source_brick.output_schema if source_brick else None
        
        edges.append(GenericEdge(
            source=conn.source_brick_id,
            target=conn.target_brick_id,
            label=label,
            visual=EdgeVisual(
                color=wire_color,
                style=wire_style,
                weight=weight,
                show_label=True,
            ),
            metadata={
                'tokens': source_tokens,
                'is_branching': conn.is_branching,
            }
        ))
    
    return GenericComposition(
        nodes=nodes,
        edges=edges,
        metadata={
            **composition.metadata,
            'category': 'lushy',
            'adapted_from': 'BrickComposition',
        }
    )
