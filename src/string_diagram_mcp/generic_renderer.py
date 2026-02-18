"""
Generic Compact Renderer
=========================

Renders any GenericComposition as a compact string diagram.
Handles all node shapes (circle, pill, diamond, square, point)
and reads visual hints from the generic schema.

No domain assumptions — works with any category's objects and morphisms.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math

from .generic import (
    GenericComposition, GenericNode, GenericEdge,
    NodeVisual, EdgeVisual
)
from .foundation import Point


# ============================================================================
# LAYOUT
# ============================================================================

@dataclass
class GenericNodePosition:
    """Computed position for a generic node"""
    node_id: str
    center: Point
    radius: float          # Bounding radius (for wire attachment)
    width: float           # Actual width (differs for pill/diamond)
    height: float          # Actual height


SIZE_MAP = {
    'small':  24,
    'medium': 35,
    'large':  44,
}

# Pill is wider than tall
PILL_WIDTH_FACTOR = 1.8


class GenericLayoutComputer:
    """
    Topological layout for generic compositions.
    
    Runs Kahn's algorithm on the edge list to determine layers,
    then distributes nodes spatially.
    """
    
    GRID_SPACING_X = 160
    GRID_SPACING_Y = 140
    MARGIN_TOP = 100
    MARGIN_BOTTOM = 120
    MARGIN_X = 80
    
    def compute(
        self,
        composition: GenericComposition
    ) -> Tuple[List[GenericNodePosition], int, int]:
        """
        Compute layout from generic composition.
        
        Returns: (positions, canvas_width, canvas_height)
        """
        node_map = {n.id: n for n in composition.nodes}
        
        # Build adjacency + in-degree
        graph = {n.id: [] for n in composition.nodes}
        in_degree = {n.id: 0 for n in composition.nodes}
        
        for edge in composition.edges:
            if edge.source in graph and edge.target in graph:
                graph[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        # Kahn's algorithm → layers
        layers = []
        remaining = set(graph.keys())
        
        while remaining:
            current = [n for n in remaining if in_degree[n] == 0]
            if not current:
                current = [min(remaining, key=lambda n: in_degree[n])]
            layers.append(current)
            for node in current:
                remaining.remove(node)
                for neighbor in graph.get(node, []):
                    in_degree[neighbor] -= 1
        
        # Assign positions
        positions = []
        max_layer_width = max((len(layer) for layer in layers), default=1)
        
        for layer_idx, layer in enumerate(layers):
            y = self.MARGIN_TOP + layer_idx * self.GRID_SPACING_Y
            
            total_w = (len(layer) - 1) * self.GRID_SPACING_X
            start_x = self.MARGIN_X + (max_layer_width - 1) * self.GRID_SPACING_X / 2 - total_w / 2
            
            for node_idx, node_id in enumerate(layer):
                node = node_map[node_id]
                x = start_x + node_idx * self.GRID_SPACING_X
                
                # Size from visual hints
                vis = node.visual or NodeVisual()
                base_r = SIZE_MAP.get(vis.size, SIZE_MAP['medium'])
                
                shape = vis.shape if vis else 'circle'
                if shape == 'pill':
                    width = base_r * PILL_WIDTH_FACTOR * 2
                    height = base_r * 2
                elif shape == 'diamond':
                    width = base_r * 1.6 * 2
                    height = base_r * 1.6 * 2
                elif shape == 'point':
                    width = 10
                    height = 10
                    base_r = 5
                elif shape == 'square':
                    width = base_r * 1.5 * 2
                    height = base_r * 1.5 * 2
                else:  # circle
                    width = base_r * 2
                    height = base_r * 2
                
                positions.append(GenericNodePosition(
                    node_id=node_id,
                    center=Point(x, y),
                    radius=base_r,
                    width=width,
                    height=height,
                ))
        
        # Canvas size
        if positions:
            max_x = max(p.center.x + p.width / 2 for p in positions)
            max_y = max(p.center.y + p.height / 2 for p in positions)
            canvas_w = int(max_x + self.MARGIN_X)
            canvas_h = int(max_y + self.MARGIN_BOTTOM)
        else:
            canvas_w, canvas_h = 600, 400
        
        canvas_w = max(canvas_w, 500)
        
        return positions, canvas_w, canvas_h


# ============================================================================
# WIRE ROUTING
# ============================================================================

@dataclass
class GenericWire:
    """Routed wire between two nodes"""
    source_id: str
    target_id: str
    source_point: Point
    target_point: Point
    path_d: str
    label: Optional[str]
    visual: EdgeVisual
    metadata: Dict


class GenericWireRouter:
    """Route wires between generic nodes with Bezier curves."""
    
    BASE_WIDTH = 2.0
    
    def route(
        self,
        positions: List[GenericNodePosition],
        composition: GenericComposition
    ) -> List[GenericWire]:
        pos_map = {p.node_id: p for p in positions}
        wires = []
        
        for edge in composition.edges:
            src_pos = pos_map.get(edge.source)
            tgt_pos = pos_map.get(edge.target)
            if not src_pos or not tgt_pos:
                continue
            
            # Attachment: bottom of source, top of target
            src = Point(src_pos.center.x, src_pos.center.y + src_pos.height / 2)
            tgt = Point(tgt_pos.center.x, tgt_pos.center.y - tgt_pos.height / 2)
            
            dy = tgt.y - src.y
            dx = tgt.x - src.x
            
            c1 = Point(src.x + dx * 0.15, src.y + dy * 0.45)
            c2 = Point(tgt.x - dx * 0.15, tgt.y - dy * 0.45)
            
            path_d = (
                f"M {src.x:.1f} {src.y:.1f} "
                f"C {c1.x:.1f} {c1.y:.1f}, "
                f"{c2.x:.1f} {c2.y:.1f}, "
                f"{tgt.x:.1f} {tgt.y:.1f}"
            )
            
            wires.append(GenericWire(
                source_id=edge.source,
                target_id=edge.target,
                source_point=src,
                target_point=tgt,
                path_d=path_d,
                label=edge.label,
                visual=edge.visual or EdgeVisual(),
                metadata=edge.metadata or {},
            ))
        
        return wires


# ============================================================================
# RENDERER
# ============================================================================

# Default palette
_DEFAULTS = {
    'node_color':      '#10b981',
    'bg':              '#0f172a',
    'bg_grid':         '#1e293b',
    'text_primary':    '#f1f5f9',
    'text_secondary':  '#94a3b8',
    'text_on_node':    '#ffffff',
    'accent':          '#f59e0b',
    'wire_default':    '#64748b',
}


class GenericCompactRenderer:
    """
    Renders any GenericComposition to SVG.
    
    Reads visual hints from nodes and edges.
    Supports all five node shapes.
    No domain assumptions.
    """
    
    def __init__(self):
        self.layout_computer = GenericLayoutComputer()
        self.wire_router = GenericWireRouter()
    
    def render(self, composition: GenericComposition) -> str:
        """
        Render generic composition to SVG string.
        
        Args:
            composition: The GenericComposition to render
            
        Returns:
            Complete SVG markup
        """
        node_map = {n.id: n for n in composition.nodes}
        
        positions, canvas_w, canvas_h = self.layout_computer.compute(composition)
        wires = self.wire_router.route(positions, composition)
        
        parts = []
        parts.append(self._header(canvas_w, canvas_h))
        parts.append(self._defs(composition))
        parts.append(self._background(canvas_w, canvas_h))
        
        title = composition.metadata.get('name', 'Composition')
        category = composition.metadata.get('category', '')
        parts.append(self._title(title, category, canvas_w))
        
        # Wires behind nodes
        for wire in wires:
            parts.append(self._render_wire(wire))
        
        # Nodes
        pos_map = {p.node_id: p for p in positions}
        for node in composition.nodes:
            pos = pos_map.get(node.id)
            if pos:
                parts.append(self._render_node(node, pos))
        
        parts.append(self._footer(canvas_w, canvas_h))
        parts.append('</svg>')
        
        return '\n'.join(parts)
    
    # ------------------------------------------------------------------
    # SVG scaffolding
    # ------------------------------------------------------------------
    
    def _header(self, w: int, h: int) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"
     xmlns="http://www.w3.org/2000/svg"
     font-family="'SF Mono', 'Fira Code', 'JetBrains Mono', monospace">'''
    
    def _defs(self, composition: GenericComposition) -> str:
        parts = ['  <defs>']
        
        parts.append('''    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.4"/>
    </filter>''')
        
        # Collect unique colors for arrow markers
        colors_seen = set()
        for edge in composition.edges:
            vis = edge.visual or EdgeVisual()
            color = vis.color or _DEFAULTS['wire_default']
            colors_seen.add(color)
        
        for color in colors_seen:
            safe_id = color.replace('#', 'c')
            parts.append(
                f'    <marker id="arrow-{safe_id}" markerWidth="4" markerHeight="3" '
                f'refX="3.5" refY="1.5" orient="auto">'
                f'<polygon points="0 0, 4 1.5, 0 3" fill="{color}" opacity="0.9"/>'
                f'</marker>'
            )
        
        # Radial gradients for unique node colors
        node_colors_seen = set()
        for node in composition.nodes:
            vis = node.visual or NodeVisual()
            color = vis.color or _DEFAULTS['node_color']
            node_colors_seen.add(color)
        
        for color in node_colors_seen:
            safe_id = color.replace('#', 'c')
            # Lighten for gradient highlight
            parts.append(
                f'    <radialGradient id="grad-{safe_id}" cx="40%" cy="35%">'
                f'<stop offset="0%" stop-color="{color}" stop-opacity="0.7"/>'
                f'<stop offset="100%" stop-color="{color}"/>'
                f'</radialGradient>'
            )
        
        parts.append('  </defs>')
        return '\n'.join(parts)
    
    def _background(self, w: int, h: int) -> str:
        bg = _DEFAULTS['bg']
        grid = _DEFAULTS['bg_grid']
        lines = [f'  <rect width="{w}" height="{h}" fill="{bg}"/>']
        lines.append('  <g opacity="0.15">')
        for x in range(0, w, 40):
            for y in range(0, h, 40):
                lines.append(f'    <circle cx="{x}" cy="{y}" r="0.8" fill="{grid}"/>')
        lines.append('  </g>')
        return '\n'.join(lines)
    
    def _title(self, name: str, category: str, canvas_w: int) -> str:
        cx = canvas_w / 2
        subtitle = category.upper() if category else 'STRING DIAGRAM'
        return f'''  <text x="{cx}" y="35" text-anchor="middle" 
        font-size="16" font-weight="700" fill="{_DEFAULTS['text_primary']}" letter-spacing="0.05em">{name}</text>
  <text x="{cx}" y="55" text-anchor="middle" 
        font-size="10" fill="{_DEFAULTS['text_secondary']}" letter-spacing="0.1em">{subtitle}</text>'''
    
    # ------------------------------------------------------------------
    # Wire rendering
    # ------------------------------------------------------------------
    
    def _render_wire(self, wire: GenericWire) -> str:
        vis = wire.visual
        color = vis.color or _DEFAULTS['wire_default']
        safe_id = color.replace('#', 'c')
        
        thickness = 2.0 * vis.weight
        dash = ''
        if vis.style == 'dashed':
            dash = ' stroke-dasharray="6,4"'
        elif vis.style == 'dotted':
            dash = ' stroke-dasharray="2,3"'
        
        parts = []
        
        # Glow behind heavy wires
        if vis.weight > 1.2:
            parts.append(
                f'  <path d="{wire.path_d}" fill="none" '
                f'stroke="{color}" stroke-width="{thickness + 4:.1f}" '
                f'opacity="0.1" stroke-linecap="round"/>'
            )
        
        # Wire
        parts.append(
            f'  <path d="{wire.path_d}" fill="none" '
            f'stroke="{color}" stroke-width="{thickness:.1f}" '
            f'opacity="{vis.opacity}" stroke-linecap="round"{dash} '
            f'marker-end="url(#arrow-{safe_id})"/>'
        )
        
        # Label on wire
        if wire.label and vis.show_label:
            mid_x = (wire.source_point.x + wire.target_point.x) / 2 + 14
            mid_y = (wire.source_point.y + wire.target_point.y) / 2
            parts.append(
                f'  <text x="{mid_x:.1f}" y="{mid_y:.1f}" '
                f'font-size="8" fill="{_DEFAULTS["text_secondary"]}" '
                f'opacity="0.7">{wire.label}</text>'
            )
        
        # Token cost from metadata (if present, Lushy adapter sets this)
        tokens = wire.metadata.get('tokens', 0)
        if tokens > 0:
            mid_x = (wire.source_point.x + wire.target_point.x) / 2 + 14
            mid_y = (wire.source_point.y + wire.target_point.y) / 2 + 12
            parts.append(
                f'  <text x="{mid_x:.1f}" y="{mid_y:.1f}" '
                f'font-size="8" fill="{_DEFAULTS["accent"]}" '
                f'font-weight="600" opacity="0.9">{tokens}t</text>'
            )
        
        return '\n'.join(parts)
    
    # ------------------------------------------------------------------
    # Node rendering (all shapes)
    # ------------------------------------------------------------------
    
    def _render_node(self, node: GenericNode, pos: GenericNodePosition) -> str:
        vis = node.visual or NodeVisual()
        cx, cy = pos.center.x, pos.center.y
        color = vis.color or _DEFAULTS['node_color']
        safe_color = color.replace('#', 'c')
        
        node_filter = 'filter="url(#glow)"' if vis.glow else 'filter="url(#shadow)"'
        
        parts = [f'  <g class="node" data-id="{node.id}">']
        
        # Input type label (above)
        if node.input_type:
            parts.append(
                f'    <text x="{cx}" y="{cy - pos.height/2 - 10}" text-anchor="middle" '
                f'font-size="8" fill="{_DEFAULTS["text_secondary"]}" opacity="0.7">'
                f'{node.input_type}</text>'
            )
        
        # Ring (if ring_colors provided)
        if vis.ring_colors:
            self._render_ring(parts, cx, cy, pos.radius, vis.ring_colors, vis.ring_weights)
        
        # Shape
        shape = vis.shape or 'circle'
        fill = f'url(#grad-{safe_color})'
        stroke = _DEFAULTS['bg_grid']
        
        if shape == 'circle':
            parts.append(
                f'    <circle cx="{cx}" cy="{cy}" r="{pos.radius}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="2" {node_filter}/>'
            )
        
        elif shape == 'pill':
            pw = pos.width
            ph = pos.height
            rx = ph / 2
            parts.append(
                f'    <rect x="{cx - pw/2}" y="{cy - ph/2}" width="{pw}" height="{ph}" '
                f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2" {node_filter}/>'
            )
        
        elif shape == 'diamond':
            s = pos.radius * 1.4
            points = f"{cx},{cy - s} {cx + s},{cy} {cx},{cy + s} {cx - s},{cy}"
            parts.append(
                f'    <polygon points="{points}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="2" {node_filter}/>'
            )
        
        elif shape == 'square':
            s = pos.radius * 1.3
            parts.append(
                f'    <rect x="{cx - s}" y="{cy - s}" width="{s*2}" height="{s*2}" '
                f'rx="4" fill="{fill}" stroke="{stroke}" stroke-width="2" {node_filter}/>'
            )
        
        elif shape == 'point':
            parts.append(
                f'    <circle cx="{cx}" cy="{cy}" r="4" '
                f'fill="{color}" stroke="{stroke}" stroke-width="1.5"/>'
            )
        
        # Name label (center, skip for points)
        if shape != 'point':
            name = node.name
            if len(name) > 14:
                words = name.split()
                if len(words) >= 2:
                    mid = len(words) // 2
                    line1 = ' '.join(words[:mid])
                    line2 = ' '.join(words[mid:])
                    parts.append(
                        f'    <text x="{cx}" y="{cy - 4}" text-anchor="middle" '
                        f'font-size="10" font-weight="700" fill="{_DEFAULTS["text_on_node"]}">{line1}</text>'
                    )
                    parts.append(
                        f'    <text x="{cx}" y="{cy + 8}" text-anchor="middle" '
                        f'font-size="10" font-weight="700" fill="{_DEFAULTS["text_on_node"]}">{line2}</text>'
                    )
                else:
                    parts.append(
                        f'    <text x="{cx}" y="{cy + 4}" text-anchor="middle" '
                        f'font-size="9" font-weight="700" fill="{_DEFAULTS["text_on_node"]}">{name[:16]}</text>'
                    )
            else:
                parts.append(
                    f'    <text x="{cx}" y="{cy + 4}" text-anchor="middle" '
                    f'font-size="11" font-weight="700" fill="{_DEFAULTS["text_on_node"]}">{name}</text>'
                )
        else:
            # Point nodes get a tiny label below
            parts.append(
                f'    <text x="{cx}" y="{cy + 14}" text-anchor="middle" '
                f'font-size="8" fill="{_DEFAULTS["text_secondary"]}" opacity="0.7">{node.name}</text>'
            )
        
        # Badge (top-right, skip for points)
        if vis.badge and shape != 'point':
            badge_x = cx + pos.radius * 0.65
            badge_y = cy - pos.radius * 0.65
            badge_color = vis.badge_color or color
            parts.append(
                f'    <circle cx="{badge_x:.1f}" cy="{badge_y:.1f}" r="10" '
                f'fill="{_DEFAULTS["bg"]}" stroke="{badge_color}" stroke-width="1.5"/>'
            )
            parts.append(
                f'    <text x="{badge_x:.1f}" y="{badge_y + 3.5:.1f}" text-anchor="middle" '
                f'font-size="8" font-weight="700" fill="{badge_color}">{vis.badge}</text>'
            )
        
        # Output type label (below)
        if node.output_type:
            parts.append(
                f'    <text x="{cx}" y="{cy + pos.height/2 + 18}" text-anchor="middle" '
                f'font-size="8" fill="{_DEFAULTS["text_secondary"]}" opacity="0.7">'
                f'{node.output_type}</text>'
            )
        
        parts.append('  </g>')
        return '\n'.join(parts)
    
    def _render_ring(
        self,
        parts: list,
        cx: float, cy: float,
        radius: float,
        colors: List[str],
        weights: Optional[List[float]]
    ):
        """Render colored arcs around node"""
        n = len(colors)
        if n == 0:
            return
        
        ring_r = radius + 6
        arc_span = 360 / n
        gap = 5  # degrees between arcs
        
        for i, color in enumerate(colors):
            start_angle = i * arc_span - 90
            end_angle = start_angle + arc_span - gap
            
            width = weights[i] if weights and i < len(weights) else 3.0
            
            x1 = cx + ring_r * math.cos(math.radians(start_angle))
            y1 = cy + ring_r * math.sin(math.radians(start_angle))
            x2 = cx + ring_r * math.cos(math.radians(end_angle))
            y2 = cy + ring_r * math.sin(math.radians(end_angle))
            
            # Large arc flag needed if span > 180
            large_arc = 1 if (arc_span - gap) > 180 else 0
            
            parts.append(
                f'    <path d="M {x1:.1f} {y1:.1f} A {ring_r} {ring_r} 0 {large_arc} 1 {x2:.1f} {y2:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="{width}" '
                f'stroke-linecap="round"/>'
            )
    
    def _footer(self, w: int, h: int) -> str:
        return f'''  <text x="{w/2}" y="{h - 8}" text-anchor="middle" 
        font-size="8" fill="{_DEFAULTS['text_secondary']}" opacity="0.4" letter-spacing="0.1em">
    LUSHY STRING DIAGRAM GENERATOR
  </text>'''
