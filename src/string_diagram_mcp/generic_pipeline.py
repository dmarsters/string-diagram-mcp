"""
String Diagram Generator - Generic Pipeline
=============================================

Layout, routing, and rendering for GenericComposition.
Reads visual hints from Node.visual and Edge.visual instead of
domain-specific structures like Lushy layers/grades.

All operations are Grade 0 (deterministic, 0 tokens).
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import math

from foundation import (
    GenericComposition, Node, Edge, NodeVisual, EdgeVisual,
    Point, Layout, BrickPosition, Wire, WireRouting,
    CostSummary, Annotation, StringDiagram
)


# ============================================================================
# SIZE LOOKUP
# ============================================================================

SIZE_RADIUS = {
    'small':  25,
    'medium': 35,
    'large':  42,
}

SHAPE_ASPECT = {
    'circle':  1.0,
    'pill':    1.8,   # wider than tall
    'diamond': 1.0,
    'square':  1.0,
    'point':   0.3,
}


# ============================================================================
# GENERIC LAYOUT COMPUTER
# ============================================================================

class GenericLayoutComputer:
    """
    Topological layout for GenericComposition.
    
    Same Kahn's algorithm as the Lushy LayoutComputer but operates
    on Node/Edge instead of Brick/Connection. Node sizes come from
    visual.size hints.
    """
    
    GRID_SPACING_X = 160
    GRID_SPACING_Y = 140
    MARGIN_TOP = 100
    MARGIN_BOTTOM = 120
    MARGIN_X = 80
    
    def compute_layout(self, composition: GenericComposition) -> Layout:
        """Compute spatial layout from generic composition."""
        graph = self._build_graph(composition)
        layers = self._topological_layers(graph)
        positions = self._assign_positions(layers, composition)
        canvas_w, canvas_h = self._compute_canvas_size(positions)
        
        return Layout(
            brick_positions=positions,
            canvas_width=canvas_w,
            canvas_height=canvas_h,
            layers_depth=len(layers)
        )
    
    def _build_graph(self, composition: GenericComposition) -> Dict[str, List[str]]:
        graph = {node.id: [] for node in composition.nodes}
        for edge in composition.edges:
            if edge.source in graph:
                graph[edge.source].append(edge.target)
        return graph
    
    def _topological_layers(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        layers = []
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1
        
        remaining = set(graph.keys())
        while remaining:
            current = [n for n in remaining if in_degree[n] == 0]
            if not current:
                current = [min(remaining, key=lambda n: in_degree[n])]
            layers.append(current)
            for node in current:
                remaining.remove(node)
                for neighbor in graph[node]:
                    if neighbor in in_degree:
                        in_degree[neighbor] -= 1
        
        return layers
    
    def _assign_positions(
        self,
        layers: List[List[str]],
        composition: GenericComposition
    ) -> List[BrickPosition]:
        node_map = {n.id: n for n in composition.nodes}
        positions = []
        max_layer_width = max((len(layer) for layer in layers), default=1)
        
        for layer_idx, layer in enumerate(layers):
            y = self.MARGIN_TOP + layer_idx * self.GRID_SPACING_Y
            layer_width = len(layer)
            total_w = (layer_width - 1) * self.GRID_SPACING_X
            start_x = self.MARGIN_X + (max_layer_width - 1) * self.GRID_SPACING_X / 2 - total_w / 2
            
            for idx, node_id in enumerate(layer):
                node = node_map.get(node_id)
                r = SIZE_RADIUS.get(
                    node.visual.size if node and node.visual else 'medium',
                    35
                )
                x = start_x + idx * self.GRID_SPACING_X
                
                positions.append(BrickPosition(
                    brick_id=node_id,
                    position=Point(x, y),
                    width=int(r * 2),
                    height=int(r * 2)
                ))
        
        return positions
    
    def _compute_canvas_size(self, positions: List[BrickPosition]) -> Tuple[int, int]:
        if not positions:
            return 600, 400
        max_x = max(p.position.x + p.width for p in positions)
        max_y = max(p.position.y + p.height for p in positions)
        return max(int(max_x + self.MARGIN_X), 600), int(max_y + self.MARGIN_BOTTOM)


# ============================================================================
# GENERIC WIRE ROUTER
# ============================================================================

class GenericWireRouter:
    """
    Routes wires between generic nodes using visual hints.
    
    Wire thickness comes from Edge.visual.weight.
    Wire style from Edge.visual.style.
    Wire color from Edge.visual.color (or defaults from source node color).
    """
    
    WIRE_BASE_WIDTH = 2.5
    
    def route_wires(
        self,
        layout: Layout,
        composition: GenericComposition
    ) -> WireRouting:
        pos_map = {bp.brick_id: bp for bp in layout.brick_positions}
        node_map = {n.id: n for n in composition.nodes}
        wires = []
        
        for edge in composition.edges:
            src_pos = pos_map.get(edge.source)
            tgt_pos = pos_map.get(edge.target)
            if not src_pos or not tgt_pos:
                continue
            
            src_r = src_pos.width / 2
            tgt_r = tgt_pos.width / 2
            
            source_pt = Point(src_pos.position.x, src_pos.position.y + src_r)
            target_pt = Point(tgt_pos.position.x, tgt_pos.position.y - tgt_r)
            
            # Control points for Bezier S-curve
            dy = target_pt.y - source_pt.y
            dx = target_pt.x - source_pt.x
            c1 = Point(source_pt.x + dx * 0.15, source_pt.y + dy * 0.45)
            c2 = Point(target_pt.x - dx * 0.15, target_pt.y - dy * 0.45)
            
            # Wire type from visual hints
            ev = edge.visual or EdgeVisual()
            weight = ev.weight if ev.weight else 1.0
            
            # Map edge style to wire_type for marker selection
            if ev.style == 'dashed':
                wire_type = 'llm'
            elif weight > 1.3:
                wire_type = 'composite'
            else:
                wire_type = 'deterministic'
            
            cost = int(edge.cost) if edge.cost else 0
            
            wires.append(Wire(
                source_brick=edge.source,
                target_brick=edge.target,
                source_point=source_pt,
                target_point=target_pt,
                control_points=[c1, c2],
                wire_type=wire_type,
                cost_tokens=cost
            ))
        
        crossings = self._count_crossings(wires)
        return WireRouting(wires=wires, total_crossings=crossings)
    
    def _count_crossings(self, wires: List[Wire]) -> int:
        crossings = 0
        for i, w1 in enumerate(wires):
            for w2 in wires[i+1:]:
                if self._segments_cross(
                    w1.source_point, w1.target_point,
                    w2.source_point, w2.target_point
                ):
                    crossings += 1
        return crossings
    
    @staticmethod
    def _segments_cross(a1: Point, a2: Point, b1: Point, b2: Point) -> bool:
        def ccw(a, b, c):
            return (c.y - a.y) * (b.x - a.x) > (b.y - a.y) * (c.x - a.x)
        return (ccw(a1, b1, b2) != ccw(a2, b1, b2) and
                ccw(a1, a2, b1) != ccw(a1, a2, b2))


# ============================================================================
# GENERIC COMPACT RENDERER
# ============================================================================

class GenericCompactRenderer:
    """
    ZX-style compact SVG renderer for GenericComposition.
    
    Reads all visual decisions from Node.visual and Edge.visual hints.
    Domain-agnostic: works for any category that provides nodes + edges.
    
    Node shapes:
      circle  → <circle>
      pill    → <rect rx=r>
      diamond → <polygon> (rotated square)
      square  → <rect>
      point   → tiny <circle>
    
    Node decorations (all from visual hints):
      fill color    → visual.color
      glow filter   → visual.glow
      badge         → visual.badge + visual.badge_color
      ring arcs     → visual.ring [{color, weight}]
    
    Wire rendering (from Edge.visual):
      color         → visual.color (fallback: source node color)
      dash pattern  → visual.style
      thickness     → visual.weight × base width
    """
    
    COLORS = {
        'bg':             '#0f172a',
        'bg_grid':        '#1e293b',
        'text_primary':   '#f1f5f9',
        'text_secondary': '#94a3b8',
        'text_on_node':   '#ffffff',
        'default_node':   '#64748b',
        'default_wire':   '#94a3b8',
        'accent':         '#f59e0b',
        'cost_bg':        '#1e293b',
    }
    
    WIRE_BASE_WIDTH = 2.5
    
    def render(
        self,
        layout: Layout,
        routing: WireRouting,
        composition: GenericComposition
    ) -> str:
        """
        Render complete diagram to SVG.
        
        Args:
            layout: Computed positions from GenericLayoutComputer
            routing: Wire routes from GenericWireRouter
            composition: The GenericComposition (for node metadata)
        """
        node_map = {n.id: n for n in composition.nodes}
        pos_map = {bp.brick_id: bp for bp in layout.brick_positions}
        
        # Collect unique wire colors for marker defs
        wire_colors = set()
        for wire in routing.wires:
            edge = self._find_edge(composition, wire.source_brick, wire.target_brick)
            color = self._wire_color(edge, node_map.get(wire.source_brick))
            wire_colors.add(color)
        
        parts = []
        parts.append(self._header(layout.canvas_width, layout.canvas_height))
        parts.append(self._defs(wire_colors))
        parts.append(self._background(layout.canvas_width, layout.canvas_height))
        
        title = composition.metadata.get('name', 'String Diagram')
        category = composition.metadata.get('category', '')
        parts.append(self._title(title, category, layout.canvas_width))
        
        # Wires (behind nodes)
        for wire in routing.wires:
            edge = self._find_edge(composition, wire.source_brick, wire.target_brick)
            parts.append(self._render_wire(wire, edge, node_map))
        
        # Nodes (on top)
        for bp in layout.brick_positions:
            node = node_map.get(bp.brick_id)
            if node:
                parts.append(self._render_node(node, bp))
        
        parts.append(self._footer(layout.canvas_width, layout.canvas_height))
        parts.append('</svg>')
        return '\n'.join(parts)
    
    # ------------------------------------------------------------------
    # SVG building blocks
    # ------------------------------------------------------------------
    
    def _header(self, w, h):
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"
     xmlns="http://www.w3.org/2000/svg"
     font-family="'SF Mono', 'Fira Code', 'JetBrains Mono', monospace">'''
    
    def _defs(self, wire_colors: set) -> str:
        parts = ['  <defs>']
        
        # Glow filter
        parts.append('''    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>''')
        
        # Shadow filter
        parts.append('''    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.4"/>
    </filter>''')
        
        # Arrow markers for each wire color
        for color in wire_colors:
            marker_id = self._color_to_marker_id(color)
            parts.append(
                f'    <marker id="{marker_id}" markerWidth="4" markerHeight="3" '
                f'refX="3.5" refY="1.5" orient="auto">\n'
                f'      <polygon points="0 0, 4 1.5, 0 3" fill="{color}" opacity="0.9"/>\n'
                f'    </marker>'
            )
        
        parts.append('  </defs>')
        return '\n'.join(parts)
    
    def _background(self, w, h):
        C = self.COLORS
        lines = [f'  <rect width="{w}" height="{h}" fill="{C["bg"]}"/>']
        lines.append('  <g opacity="0.15">')
        for x in range(0, w, 40):
            for y in range(0, h, 40):
                lines.append(f'    <circle cx="{x}" cy="{y}" r="0.8" fill="{C["bg_grid"]}"/>')
        lines.append('  </g>')
        return '\n'.join(lines)
    
    def _title(self, name, category, canvas_w):
        C = self.COLORS
        cx = canvas_w / 2
        subtitle = category.upper() if category else 'STRING DIAGRAM'
        return f'''  <text x="{cx}" y="35" text-anchor="middle"
        font-size="16" font-weight="700" fill="{C['text_primary']}" letter-spacing="0.05em">{name}</text>
  <text x="{cx}" y="55" text-anchor="middle"
        font-size="10" fill="{C['text_secondary']}" letter-spacing="0.1em">{subtitle}</text>'''
    
    def _render_wire(self, wire: Wire, edge: Optional[Edge], node_map: Dict[str, Node]) -> str:
        source_node = node_map.get(wire.source_brick)
        color = self._wire_color(edge, source_node)
        marker_id = self._color_to_marker_id(color)
        
        ev = edge.visual if edge and edge.visual else EdgeVisual()
        weight = ev.weight if ev.weight else 1.0
        thickness = self.WIRE_BASE_WIDTH * weight
        
        dash = ''
        if ev.style == 'dashed':
            dash = ' stroke-dasharray="6,4"'
        elif ev.style == 'dotted':
            dash = ' stroke-dasharray="2,3"'
        
        if len(wire.control_points) >= 2:
            c1, c2 = wire.control_points[0], wire.control_points[1]
            path_d = (
                f"M {wire.source_point.x:.1f} {wire.source_point.y:.1f} "
                f"C {c1.x:.1f} {c1.y:.1f}, {c2.x:.1f} {c2.y:.1f}, "
                f"{wire.target_point.x:.1f} {wire.target_point.y:.1f}"
            )
        else:
            path_d = (
                f"M {wire.source_point.x:.1f} {wire.source_point.y:.1f} "
                f"L {wire.target_point.x:.1f} {wire.target_point.y:.1f}"
            )
        
        parts = []
        
        # Glow layer for thick/costly wires
        if weight > 1.2 or (edge and edge.cost and edge.cost > 0):
            parts.append(
                f'  <path d="{path_d}" fill="none" stroke="{color}" '
                f'stroke-width="{thickness + 4:.1f}" opacity="0.12" stroke-linecap="round"/>'
            )
        
        # Main wire
        parts.append(
            f'  <path d="{path_d}" fill="none" stroke="{color}" '
            f'stroke-width="{thickness:.1f}" opacity="0.75" '
            f'stroke-linecap="round"{dash} marker-end="url(#{marker_id})"/>'
        )
        
        # Cost label
        if edge and edge.cost and edge.cost > 0:
            label_color = ev.label_color or self.COLORS['accent']
            mid_x = (wire.source_point.x + wire.target_point.x) / 2 + 12
            mid_y = (wire.source_point.y + wire.target_point.y) / 2
            parts.append(
                f'  <text x="{mid_x:.1f}" y="{mid_y:.1f}" '
                f'font-size="9" fill="{label_color}" font-weight="600" '
                f'opacity="0.9">{int(edge.cost)}t</text>'
            )
        
        # Wire label (object type)
        if edge and edge.label:
            mid_x = (wire.source_point.x + wire.target_point.x) / 2 - 12
            mid_y = (wire.source_point.y + wire.target_point.y) / 2 - 8
            parts.append(
                f'  <text x="{mid_x:.1f}" y="{mid_y:.1f}" '
                f'font-size="8" fill="{self.COLORS["text_secondary"]}" '
                f'opacity="0.6" text-anchor="end">{edge.label}</text>'
            )
        
        return '\n'.join(parts)
    
    def _render_node(self, node: Node, bp: BrickPosition) -> str:
        C = self.COLORS
        v = node.visual or NodeVisual()
        
        cx = bp.position.x
        cy = bp.position.y
        r = bp.width / 2
        
        color = v.color or C['default_node']
        node_filter = 'filter="url(#glow)"' if v.glow else 'filter="url(#shadow)"'
        
        parts = [f'  <g class="node" data-id="{node.id}">']
        
        # Input type (above)
        if node.input_type:
            parts.append(
                f'    <text x="{cx}" y="{cy - r - 14}" text-anchor="middle" '
                f'font-size="8" fill="{C["text_secondary"]}" opacity="0.7">{node.input_type}</text>'
            )
        
        # Ring arcs (if provided)
        if v.ring:
            ring_r = r + 6
            n_arcs = len(v.ring)
            arc_span = 360 / n_arcs - 5  # 5° gap between arcs
            
            for i, arc_spec in enumerate(v.ring):
                start_angle = i * (360 / n_arcs) - 90
                end_angle = start_angle + arc_span
                arc_color = arc_spec.get('color', '#6b7280')
                arc_width = '5' if arc_spec.get('weight') == 'thick' else '3'
                
                x1 = cx + ring_r * math.cos(math.radians(start_angle))
                y1 = cy + ring_r * math.sin(math.radians(start_angle))
                x2 = cx + ring_r * math.cos(math.radians(end_angle))
                y2 = cy + ring_r * math.sin(math.radians(end_angle))
                
                large_arc = 1 if arc_span > 180 else 0
                parts.append(
                    f'    <path d="M {x1:.1f} {y1:.1f} A {ring_r} {ring_r} 0 {large_arc} 1 {x2:.1f} {y2:.1f}" '
                    f'fill="none" stroke="{arc_color}" stroke-width="{arc_width}" stroke-linecap="round"/>'
                )
        
        # Node shape
        if v.shape == 'circle' or v.shape == 'point':
            effective_r = r * SHAPE_ASPECT.get(v.shape, 1.0)
            parts.append(
                f'    <circle cx="{cx}" cy="{cy}" r="{effective_r:.1f}" '
                f'fill="{color}" stroke="{C["bg"]}" stroke-width="2" {node_filter}/>'
            )
        elif v.shape == 'square':
            side = r * 1.4
            parts.append(
                f'    <rect x="{cx - side/2:.1f}" y="{cy - side/2:.1f}" '
                f'width="{side:.1f}" height="{side:.1f}" rx="4" '
                f'fill="{color}" stroke="{C["bg"]}" stroke-width="2" {node_filter}/>'
            )
        elif v.shape == 'diamond':
            pts = (
                f"{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}"
            )
            parts.append(
                f'    <polygon points="{pts}" '
                f'fill="{color}" stroke="{C["bg"]}" stroke-width="2" {node_filter}/>'
            )
        elif v.shape == 'pill':
            pw = r * SHAPE_ASPECT['pill']
            ph = r
            parts.append(
                f'    <rect x="{cx - pw/2:.1f}" y="{cy - ph/2:.1f}" '
                f'width="{pw:.1f}" height="{ph:.1f}" rx="{ph/2:.1f}" '
                f'fill="{color}" stroke="{C["bg"]}" stroke-width="2" {node_filter}/>'
            )
        
        # Name label (center)
        if v.shape != 'point':
            name = node.name
            font_size = 9 if len(name) > 10 else 11
            if len(name) > 14:
                words = name.split()
                if len(words) >= 2:
                    mid = len(words) // 2
                    line1 = ' '.join(words[:mid])
                    line2 = ' '.join(words[mid:])
                    parts.append(
                        f'    <text x="{cx}" y="{cy - 4}" text-anchor="middle" '
                        f'font-size="{font_size}" font-weight="700" fill="{C["text_on_node"]}">{line1}</text>'
                    )
                    parts.append(
                        f'    <text x="{cx}" y="{cy + 8}" text-anchor="middle" '
                        f'font-size="{font_size}" font-weight="700" fill="{C["text_on_node"]}">{line2}</text>'
                    )
                else:
                    parts.append(
                        f'    <text x="{cx}" y="{cy + 4}" text-anchor="middle" '
                        f'font-size="8" font-weight="700" fill="{C["text_on_node"]}">{name[:16]}</text>'
                    )
            else:
                parts.append(
                    f'    <text x="{cx}" y="{cy + 4}" text-anchor="middle" '
                    f'font-size="{font_size}" font-weight="700" fill="{C["text_on_node"]}">{name}</text>'
                )
        
        # Badge (top-right)
        if v.badge:
            badge_x = cx + r * 0.65
            badge_y = cy - r * 0.65
            badge_color = v.badge_color or color
            parts.append(
                f'    <circle cx="{badge_x:.1f}" cy="{badge_y:.1f}" r="10" '
                f'fill="{C["bg"]}" stroke="{badge_color}" stroke-width="1.5"/>'
            )
            parts.append(
                f'    <text x="{badge_x:.1f}" y="{badge_y + 3.5:.1f}" text-anchor="middle" '
                f'font-size="8" font-weight="700" fill="{badge_color}">{v.badge}</text>'
            )
        
        # Output type (below)
        if node.output_type:
            parts.append(
                f'    <text x="{cx}" y="{cy + r + 20}" text-anchor="middle" '
                f'font-size="8" fill="{C["text_secondary"]}" opacity="0.7">{node.output_type}</text>'
            )
        
        # Token cost from properties (domain-specific, optional)
        tokens = node.properties.get('total_tokens', 0)
        if tokens and tokens > 0:
            parts.append(
                f'    <text x="{cx}" y="{cy + r + 32}" text-anchor="middle" '
                f'font-size="8" fill="{C["accent"]}" font-weight="600">{tokens}t</text>'
            )
        
        parts.append('  </g>')
        return '\n'.join(parts)
    
    def _footer(self, w, h):
        C = self.COLORS
        return f'''  <text x="{w/2}" y="{h - 8}" text-anchor="middle"
        font-size="8" fill="{C['text_secondary']}" opacity="0.5" letter-spacing="0.1em">
    LUSHY STRING DIAGRAM · GENERIC VIEW
  </text>'''
    
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    
    def _find_edge(self, composition: GenericComposition, source_id: str, target_id: str) -> Optional[Edge]:
        for edge in composition.edges:
            if edge.source == source_id and edge.target == target_id:
                return edge
        return None
    
    def _wire_color(self, edge: Optional[Edge], source_node: Optional[Node]) -> str:
        if edge and edge.visual and edge.visual.color:
            return edge.visual.color
        if source_node and source_node.visual and source_node.visual.color:
            return source_node.visual.color
        return self.COLORS['default_wire']
    
    @staticmethod
    def _color_to_marker_id(color: str) -> str:
        """Generate a stable marker ID from a color hex."""
        clean = color.replace('#', '')
        return f"arrow-{clean}"


# ============================================================================
# GENERIC DIAGRAM GENERATOR (convenience class)
# ============================================================================

class GenericDiagramGenerator:
    """
    Complete generic pipeline: layout → route → render.
    
    Accepts GenericComposition, returns StringDiagram with SVG.
    
    For Lushy bricks, use the LushyBrickAdapter first:
        adapter = LushyBrickAdapter()
        generic = adapter.adapt(brick_composition)
        diagram = GenericDiagramGenerator().generate(generic)
    """
    
    def __init__(self):
        self.layout_computer = GenericLayoutComputer()
        self.wire_router = GenericWireRouter()
        self.renderer = GenericCompactRenderer()
    
    def generate(
        self,
        composition: GenericComposition,
        validate: bool = True
    ) -> StringDiagram:
        """
        Generate string diagram from generic composition.
        
        Args:
            composition: Generic node/edge composition with visual hints
            validate: Run structural validation first
            
        Returns:
            StringDiagram with SVG and metadata
        """
        if validate:
            from .foundation import validate_generic_composition
            errors = validate_generic_composition(composition)
            if errors:
                raise ValueError(f"Invalid composition: {', '.join(errors)}")
        
        layout = self.layout_computer.compute_layout(composition)
        routing = self.wire_router.route_wires(layout, composition)
        svg = self.renderer.render(layout, routing, composition)
        
        # Build a minimal cost summary from edge costs
        total_cost = sum(e.cost for e in composition.edges if e.cost)
        
        return StringDiagram(
            svg=svg,
            layout=layout,
            routing=routing,
            annotations=[],
            cost_summary=CostSummary(
                total_tokens=int(total_cost),
                deterministic_layers=0,
                llm_layers=0,
                vs_pure_llm=0,
                savings_pct=0.0
            ),
            metadata={
                'source_schema': composition.metadata.get('source_schema', 'GenericComposition'),
                'category': composition.metadata.get('category', ''),
                'name': composition.metadata.get('name', 'String Diagram'),
                'node_count': len(composition.nodes),
                'edge_count': len(composition.edges),
                'layers_depth': layout.layers_depth,
                'wire_crossings': routing.total_crossings
            }
        )
