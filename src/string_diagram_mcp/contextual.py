"""
String Diagram Generator Brick - Contextual Layer + SVG Renderers
==================================================================

Layer 4: Contextual (Grade 0/1)

Contains:
- CostAnalyzer: Deterministic cost analysis (Grade 0)
- SVGRenderer: Original box-and-wire renderer
- CompactSVGRenderer: ZX-style compact node renderer

Both renderers share the same render() signature for drop-in swapping.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import math

from .foundation import (
    Annotation, CostSummary, Point, BrickComposition, Brick,
    Layout, WireRouting, Wire, BrickPosition, DiagramPrimitives
)


# ============================================================================
# COST ANALYZER (shared by both renderers)
# ============================================================================

class CostAnalyzer:
    """
    Deterministic cost analysis (Grade 0 subset of contextual layer)
    
    This part requires no LLM - pure computation.
    """
    
    @staticmethod
    def compute_cost_summary(
        composition: BrickComposition,
        routing: WireRouting
    ) -> CostSummary:
        """
        Compute detailed cost analysis without LLM
        
        Args:
            composition: The brick composition
            routing: Wire routing information
            
        Returns:
            CostSummary with token counts and savings calculation
        """
        total_tokens = 0
        deterministic_count = 0
        llm_count = 0
        breakdown = []
        
        for brick in composition.bricks:
            brick_cost = 0
            brick_det = 0
            brick_llm = 0
            
            for layer in brick.layers:
                if layer.grade == 0:
                    brick_det += 1
                    deterministic_count += 1
                elif layer.grade == 1:
                    brick_llm += 1
                    llm_count += 1
                    brick_cost += layer.estimated_tokens
                    total_tokens += layer.estimated_tokens
            
            breakdown.append({
                'brick_name': brick.name,
                'deterministic_layers': brick_det,
                'llm_layers': brick_llm,
                'tokens': brick_cost
            })
        
        # Estimate pure LLM cost (heuristic: 8x more tokens)
        total_layers = deterministic_count + llm_count
        vs_pure_llm = int(total_tokens * (total_layers / llm_count)) if llm_count > 0 else total_tokens * 8
        
        savings_pct = ((vs_pure_llm - total_tokens) / vs_pure_llm * 100) if vs_pure_llm > 0 else 0
        
        return CostSummary(
            total_tokens=total_tokens,
            deterministic_layers=deterministic_count,
            llm_layers=llm_count,
            vs_pure_llm=vs_pure_llm,
            savings_pct=savings_pct,
            breakdown=breakdown
        )


# ============================================================================
# ORIGINAL BOX-AND-WIRE RENDERER
# ============================================================================

class SVGRenderer:
    """
    Box-and-wire SVG rendering engine (original style)
    
    Generates publication-quality SVG diagrams with tall annotated
    brick boxes showing internal layer structure.
    """
    
    def __init__(self, primitives: DiagramPrimitives):
        self.primitives = primitives
    
    def render(
        self,
        layout: Layout,
        routing: WireRouting,
        cost_summary: CostSummary,
        composition: BrickComposition,
        annotations: Optional[List[Annotation]] = None
    ) -> str:
        """
        Render complete string diagram to SVG (box-and-wire style)
        """
        parts = []
        
        parts.append(self._render_header(layout))
        parts.append(self._render_defs())
        
        title = composition.metadata.get('name', 'Lushy Workflow')
        parts.append(self._render_title(title))
        parts.append(self._render_legend())
        parts.append(self._render_wires(routing))
        
        brick_map = {b.id: b for b in composition.bricks}
        for brick_pos in layout.brick_positions:
            brick = brick_map[brick_pos.brick_id]
            parts.append(self._render_brick(brick, brick_pos))
        
        if annotations:
            parts.append(self._render_annotations(annotations))
        
        parts.append(self._render_cost_summary(cost_summary, layout))
        parts.append(self._render_footer())
        parts.append('</svg>')
        
        return '\n'.join(parts)
    
    def _render_header(self, layout: Layout) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{layout.canvas_width}" height="{layout.canvas_height}" xmlns="http://www.w3.org/2000/svg">'''
    
    def _render_defs(self) -> str:
        return '''  <defs>
    <style>
      .brick-box { fill: white; stroke: #667eea; stroke-width: 3; }
      .layer-foundation { fill: #6b7280; }
      .layer-structure { fill: #10b981; }
      .layer-relational { fill: #3b82f6; }
      .layer-contextual { fill: #8b5cf6; }
      .wire-deterministic { stroke: #10b981; stroke-width: 4; fill: none; }
      .wire-llm { stroke: #8b5cf6; stroke-width: 6; fill: none; stroke-dasharray: 8,4; }
      .wire-composite { stroke: #667eea; stroke-width: 8; fill: none; }
      .text-title { font-family: Arial, sans-serif; font-size: 18px; font-weight: bold; fill: #333; }
      .text-label { font-family: Arial, sans-serif; font-size: 14px; fill: #666; }
      .text-cost { font-family: Arial, sans-serif; font-size: 12px; fill: #8b5cf6; font-weight: bold; }
      .text-layer { font-family: Arial, sans-serif; font-size: 11px; fill: white; font-weight: bold; }
      .grade-badge { font-family: Arial, sans-serif; font-size: 10px; fill: white; font-weight: bold; }
    </style>
    
    <marker id="arrowhead-det" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#10b981" />
    </marker>
    <marker id="arrowhead-llm" markerWidth="12" markerHeight="12" refX="11" refY="4" orient="auto">
      <polygon points="0 0, 12 4, 0 8" fill="#8b5cf6" />
    </marker>
    <marker id="arrowhead-composite" markerWidth="14" markerHeight="14" refX="13" refY="5" orient="auto">
      <polygon points="0 0, 14 5, 0 10" fill="#667eea" />
    </marker>
  </defs>'''
    
    def _render_title(self, name: str) -> str:
        return f'''  <text x="50%" y="30" text-anchor="middle" class="text-title" style="font-size: 24px; fill: #667eea;">{name}</text>
  <text x="50%" y="55" text-anchor="middle" class="text-label" style="font-size: 14px;">
    Graded Traced Symmetric Monoidal Category over Kleisli(LLM)
  </text>'''
    
    def _render_legend(self) -> str:
        return '''  <g transform="translate(50, 80)">
    <text x="0" y="0" class="text-label" style="font-weight: bold;">Legend:</text>
    <line x1="0" y1="15" x2="60" y2="15" class="wire-deterministic"/>
    <text x="70" y="20" class="text-label">Deterministic (Grade 0, 0 tokens)</text>
    <line x1="0" y1="35" x2="60" y2="35" class="wire-llm"/>
    <text x="70" y="40" class="text-label">LLM Synthesis (Grade 1, paid)</text>
  </g>'''
    
    def _render_brick(self, brick: Brick, position: BrickPosition) -> str:
        x, y = position.position.x, position.position.y
        w, h = position.width, position.height
        
        parts = []
        parts.append(f'  <g transform="translate({x}, {y})">')
        parts.append(f'    <rect x="0" y="0" width="{w}" height="{h}" rx="10" class="brick-box"/>')
        parts.append(f'    <text x="{w/2}" y="25" text-anchor="middle" class="text-title">{brick.name}</text>')
        parts.append(f'    <rect x="10" y="35" width="{w-20}" height="30" rx="5" style="fill: #e5e7eb; stroke: #9ca3af; stroke-width: 1;"/>')
        parts.append(f'    <text x="{w/2}" y="55" text-anchor="middle" class="text-label" style="font-weight: bold;">Input: {brick.input_schema}</text>')
        
        layer_y = 75
        for layer in brick.layers:
            layer_class = f"layer-{layer.name}"
            grade_color = self.primitives.get_grade_badge_color(layer.grade)
            grade_text = f"G{layer.grade}"
            
            parts.append(f'    <rect x="10" y="{layer_y}" width="{w-20}" height="40" rx="5" class="{layer_class}"/>')
            parts.append(f'    <text x="20" y="{layer_y+20}" class="text-layer">{layer.name.capitalize()} Layer</text>')
            
            desc = layer.description[:40] + "..." if len(layer.description) > 40 else layer.description
            parts.append(f'    <text x="20" y="{layer_y+35}" class="text-layer" style="font-size: 10px; opacity: 0.9;">{desc}</text>')
            parts.append(f'    <circle cx="{w-30}" cy="{layer_y+20}" r="12" fill="{grade_color}"/>')
            parts.append(f'    <text x="{w-30}" y="{layer_y+25}" text-anchor="middle" class="grade-badge">{grade_text}</text>')
            
            layer_y += 45
        
        parts.append(f'    <rect x="10" y="{layer_y}" width="{w-20}" height="20" rx="5" style="fill: #e5e7eb; stroke: #9ca3af; stroke-width: 1;"/>')
        parts.append(f'    <text x="{w/2}" y="{layer_y+15}" text-anchor="middle" class="text-label" style="font-size: 11px; font-weight: bold;">Output: {brick.output_schema}</text>')
        
        parts.append('  </g>')
        return '\n'.join(parts)
    
    def _render_wires(self, routing: WireRouting) -> str:
        parts = []
        
        for wire in routing.wires:
            wire_class = f"wire-{wire.wire_type}"
            marker_type = wire.wire_type if wire.wire_type != 'composite' else 'composite'
            marker = f"arrowhead-{marker_type.split('_')[0] if '_' in marker_type else marker_type}"
            
            if len(wire.control_points) >= 2:
                path_d = (
                    f"M {wire.source_point.x} {wire.source_point.y} "
                    f"C {wire.control_points[0].x} {wire.control_points[0].y}, "
                    f"{wire.control_points[1].x} {wire.control_points[1].y}, "
                    f"{wire.target_point.x} {wire.target_point.y}"
                )
            else:
                path_d = f"M {wire.source_point.x} {wire.source_point.y} L {wire.target_point.x} {wire.target_point.y}"
            
            parts.append(f'  <path d="{path_d}" class="{wire_class}" marker-end="url(#{marker})"/>')
            
            if wire.cost_tokens > 0:
                mid_x = (wire.source_point.x + wire.target_point.x) / 2
                mid_y = (wire.source_point.y + wire.target_point.y) / 2
                parts.append(f'  <text x="{mid_x + 10}" y="{mid_y}" class="text-cost">{wire.cost_tokens}t</text>')
        
        return '\n'.join(parts)
    
    def _render_cost_summary(self, cost_summary: CostSummary, layout: Layout) -> str:
        box_y = layout.canvas_height - 200
        box_width = min(layout.canvas_width - 100, 1100)
        
        parts = []
        parts.append(f'  <g transform="translate(50, {box_y})">')
        parts.append(f'    <rect x="0" y="0" width="{box_width}" height="150" rx="10" style="fill: #faf5ff; stroke: #8b5cf6; stroke-width: 3;"/>')
        parts.append(f'    <text x="{box_width/2}" y="30" text-anchor="middle" class="text-title" style="font-size: 20px; fill: #8b5cf6;">Cost Analysis: Graded Composition</text>')
        
        total_layers = cost_summary.deterministic_layers + cost_summary.llm_layers
        parts.append(f'    <text x="50" y="60" class="text-label" style="font-weight: bold;">Total Layers: {total_layers}</text>')
        parts.append(f'    <text x="50" y="85" class="text-label">Deterministic: {cost_summary.deterministic_layers} layers (Grade 0) = 0 tokens</text>')
        parts.append(f'    <text x="50" y="110" class="text-label">LLM: {cost_summary.llm_layers} layers (Grade 1) = {cost_summary.total_tokens} tokens</text>')
        
        right_x = box_width - 450
        parts.append(f'    <text x="{right_x}" y="60" class="text-label" style="font-weight: bold;">vs Pure LLM Approach</text>')
        parts.append(f'    <text x="{right_x}" y="85" class="text-label">Pure LLM: ~{cost_summary.vs_pure_llm} tokens</text>')
        parts.append(f'    <text x="{right_x}" y="110" class="text-label">Lushy Bricks: {cost_summary.total_tokens} tokens</text>')
        parts.append(f'    <text x="{right_x}" y="135" class="text-label" style="font-size: 18px; font-weight: bold; fill: #10b981;">{cost_summary.savings_pct:.1f}% Cost Reduction ✓</text>')
        
        parts.append('  </g>')
        return '\n'.join(parts)
    
    def _render_annotations(self, annotations: List[Annotation]) -> str:
        parts = []
        for ann in annotations:
            parts.append(f'  <text x="{ann.position.x}" y="{ann.position.y}" class="text-label" style="font-style: italic;">{ann.text}</text>')
        return '\n'.join(parts)
    
    def _render_footer(self) -> str:
        return '''  <text x="50%" y="98%" text-anchor="middle" class="text-label" style="font-size: 11px; font-style: italic;">
    Generated by Lushy String Diagram Brick • Category Theory for AI Workflows
  </text>'''


# ============================================================================
# COMPACT LAYOUT COMPUTER
# ============================================================================

@dataclass
class CompactPosition:
    """Position in the compact grid layout"""
    brick_id: str
    center: Point
    radius: float
    grade_max: int
    det_layers: int
    llm_layers: int
    total_tokens: int


class CompactLayoutComputer:
    """
    Recomputes layout for compact node style.
    
    Uses the same topological layers from structure.py but assigns
    compact circular positions instead of tall rectangles.
    """
    
    NODE_RADIUS_BASE = 35
    NODE_RADIUS_LLM = 42
    
    GRID_SPACING_X = 160
    GRID_SPACING_Y = 140
    MARGIN_TOP = 100
    MARGIN_BOTTOM = 180
    MARGIN_X = 80
    
    def recompute_compact(
        self,
        layout: Layout,
        composition: BrickComposition
    ) -> Tuple[List[CompactPosition], int, int]:
        """
        Convert existing layout to compact positions.
        
        Reuses the topological ordering from layout.brick_positions
        but reassigns coordinates for compact nodes.
        
        Returns: (compact_positions, canvas_width, canvas_height)
        """
        brick_map = {b.id: b for b in composition.bricks}
        
        # Group positions by Y coordinate to recover layers
        y_groups: Dict[float, List[BrickPosition]] = {}
        for bp in layout.brick_positions:
            y_key = round(bp.position.y, 1)
            y_groups.setdefault(y_key, []).append(bp)
        
        sorted_layers = sorted(y_groups.items(), key=lambda x: x[0])
        
        compact_positions = []
        max_layer_width = max((len(layer) for _, layer in sorted_layers), default=1)
        
        for layer_idx, (_, layer_bricks) in enumerate(sorted_layers):
            layer_width = len(layer_bricks)
            y = self.MARGIN_TOP + layer_idx * self.GRID_SPACING_Y
            
            total_w = (layer_width - 1) * self.GRID_SPACING_X
            start_x = self.MARGIN_X + (max_layer_width - 1) * self.GRID_SPACING_X / 2 - total_w / 2
            
            for brick_idx, bp in enumerate(layer_bricks):
                brick = brick_map[bp.brick_id]
                
                det_layers = sum(1 for l in brick.layers if l.grade == 0)
                llm_layers = sum(1 for l in brick.layers if l.grade == 1)
                grade_max = max(l.grade for l in brick.layers)
                total_tokens = sum(l.estimated_tokens for l in brick.layers if l.grade == 1)
                
                radius = self.NODE_RADIUS_LLM if llm_layers > 0 else self.NODE_RADIUS_BASE
                x = start_x + brick_idx * self.GRID_SPACING_X
                
                compact_positions.append(CompactPosition(
                    brick_id=bp.brick_id,
                    center=Point(x, y),
                    radius=radius,
                    grade_max=grade_max,
                    det_layers=det_layers,
                    llm_layers=llm_layers,
                    total_tokens=total_tokens
                ))
        
        if compact_positions:
            max_x = max(cp.center.x + cp.radius for cp in compact_positions)
            max_y = max(cp.center.y + cp.radius for cp in compact_positions)
            canvas_w = int(max_x + self.MARGIN_X)
            canvas_h = int(max_y + self.MARGIN_BOTTOM)
        else:
            canvas_w, canvas_h = 600, 400
        
        canvas_w = max(canvas_w, 600)
        
        return compact_positions, canvas_w, canvas_h


# ============================================================================
# COMPACT WIRE ROUTER
# ============================================================================

class CompactWireRouter:
    """
    Reroutes wires to connect compact node edges with
    smooth curves. Wire thickness encodes token flow.
    """
    
    WIRE_MIN_WIDTH = 2.0
    WIRE_MAX_WIDTH = 8.0
    
    @dataclass
    class CompactWire:
        source_id: str
        target_id: str
        source_point: Point
        target_point: Point
        wire_type: str
        thickness: float
        cost_tokens: int
        path_d: str
    
    def route_compact(
        self,
        compact_positions: List[CompactPosition],
        routing: WireRouting
    ) -> List['CompactWireRouter.CompactWire']:
        """
        Reroute wires between compact node edges.
        
        Wires exit from bottom of source node and enter top of target.
        """
        pos_map = {cp.brick_id: cp for cp in compact_positions}
        compact_wires = []
        
        max_tokens = max((w.cost_tokens for w in routing.wires), default=1) or 1
        
        for wire in routing.wires:
            source_cp = pos_map.get(wire.source_brick)
            target_cp = pos_map.get(wire.target_brick)
            if not source_cp or not target_cp:
                continue
            
            src = Point(source_cp.center.x, source_cp.center.y + source_cp.radius)
            tgt = Point(target_cp.center.x, target_cp.center.y - target_cp.radius)
            
            if wire.cost_tokens > 0:
                t = wire.cost_tokens / max_tokens
                thickness = self.WIRE_MIN_WIDTH + t * (self.WIRE_MAX_WIDTH - self.WIRE_MIN_WIDTH)
            else:
                thickness = self.WIRE_MIN_WIDTH
            
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
            
            compact_wires.append(self.CompactWire(
                source_id=wire.source_brick,
                target_id=wire.target_brick,
                source_point=src,
                target_point=tgt,
                wire_type=wire.wire_type,
                thickness=thickness,
                cost_tokens=wire.cost_tokens,
                path_d=path_d
            ))
        
        return compact_wires


# ============================================================================
# COMPACT ZX-STYLE RENDERER
# ============================================================================

class CompactSVGRenderer:
    """
    ZX-style SVG renderer for Lushy brick compositions.
    
    Visual encoding:
      Node fill    -> grade (green=deterministic, purple=has LLM)
      Node size    -> slightly larger for LLM-containing bricks
      Inner ring   -> layer composition (4 arcs, colored by layer type)
      Center label -> brick name (abbreviated)
      Wire width   -> token flow volume
      Wire style   -> deterministic (solid) vs LLM (dashed)
      Wire color   -> grade of source output
    
    Same render() signature as SVGRenderer for drop-in swapping.
    """
    
    COLORS = {
        'node_det':         '#10b981',
        'node_llm':         '#8b5cf6',
        'node_stroke':      '#1e293b',
        'wire_det':         '#10b981',
        'wire_llm':         '#8b5cf6',
        'wire_composite':   '#667eea',
        'bg':               '#0f172a',
        'bg_grid':          '#1e293b',
        'text_primary':     '#f1f5f9',
        'text_secondary':   '#94a3b8',
        'text_on_node':     '#ffffff',
        'layer_foundation': '#6b7280',
        'layer_structure':  '#10b981',
        'layer_relational': '#3b82f6',
        'layer_contextual': '#8b5cf6',
        'cost_bg':          '#1e293b',
        'cost_border':      '#8b5cf6',
        'accent':           '#f59e0b',
    }
    
    def __init__(self, primitives: DiagramPrimitives):
        self.primitives = primitives
        self.compact_layout = CompactLayoutComputer()
        self.compact_router = CompactWireRouter()
    
    def render(
        self,
        layout: Layout,
        routing: WireRouting,
        cost_summary: CostSummary,
        composition: BrickComposition,
        annotations: Optional[List[Annotation]] = None
    ) -> str:
        """
        Render compact string diagram to SVG.
        
        Same signature as SVGRenderer.render() - drop-in replacement.
        """
        brick_map = {b.id: b for b in composition.bricks}
        
        compact_positions, canvas_w, canvas_h = \
            self.compact_layout.recompute_compact(layout, composition)
        
        compact_wires = self.compact_router.route_compact(compact_positions, routing)
        
        parts = []
        
        parts.append(self._header(canvas_w, canvas_h))
        parts.append(self._defs())
        parts.append(self._background(canvas_w, canvas_h))
        
        title = composition.metadata.get('name', 'Lushy Workflow')
        parts.append(self._title(title, canvas_w))
        
        for cw in compact_wires:
            parts.append(self._render_wire(cw))
        
        for cp in compact_positions:
            brick = brick_map[cp.brick_id]
            parts.append(self._render_node(cp, brick))
        
        parts.append(self._legend(canvas_w))
        parts.append(self._cost_summary(cost_summary, canvas_w, canvas_h))
        parts.append(self._footer(canvas_w, canvas_h))
        
        parts.append('</svg>')
        return '\n'.join(parts)
    
    # ------------------------------------------------------------------
    # SVG BUILDING BLOCKS
    # ------------------------------------------------------------------
    
    def _header(self, w: int, h: int) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"
     xmlns="http://www.w3.org/2000/svg"
     font-family="'SF Mono', 'Fira Code', 'JetBrains Mono', monospace">'''
    
    def _defs(self) -> str:
        C = self.COLORS
        
        parts = ['  <defs>']
        
        parts.append('''    <filter id="glow-llm" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>''')
        
        parts.append('''    <filter id="node-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.4"/>
    </filter>''')
        
        for wire_type, color in [('det', C['wire_det']), ('llm', C['wire_llm']), ('composite', C['wire_composite'])]:
            parts.append(f'''    <marker id="arrow-{wire_type}" markerWidth="4" markerHeight="3" refX="3.5" refY="1.5" orient="auto">
      <polygon points="0 0, 4 1.5, 0 3" fill="{color}" opacity="0.9"/>
    </marker>''')
        
        parts.append(f'''    <radialGradient id="grad-det" cx="40%" cy="35%">
      <stop offset="0%" stop-color="#34d399"/>
      <stop offset="100%" stop-color="{C['node_det']}"/>
    </radialGradient>
    <radialGradient id="grad-llm" cx="40%" cy="35%">
      <stop offset="0%" stop-color="#a78bfa"/>
      <stop offset="100%" stop-color="{C['node_llm']}"/>
    </radialGradient>''')
        
        parts.append('  </defs>')
        return '\n'.join(parts)
    
    def _background(self, w: int, h: int) -> str:
        C = self.COLORS
        lines = [f'  <rect width="{w}" height="{h}" fill="{C["bg"]}"/>']
        
        lines.append(f'  <g opacity="0.15">')
        for x in range(0, w, 40):
            for y in range(0, h, 40):
                lines.append(f'    <circle cx="{x}" cy="{y}" r="0.8" fill="{C["bg_grid"]}"/>')
        lines.append('  </g>')
        
        return '\n'.join(lines)
    
    def _title(self, name: str, canvas_w: int) -> str:
        C = self.COLORS
        cx = canvas_w / 2
        return f'''  <text x="{cx}" y="35" text-anchor="middle" 
        font-size="16" font-weight="700" fill="{C['text_primary']}" letter-spacing="0.05em">{name}</text>
  <text x="{cx}" y="55" text-anchor="middle" 
        font-size="10" fill="{C['text_secondary']}" letter-spacing="0.1em">GRADED TRACED SYMMETRIC MONOIDAL CATEGORY</text>'''
    
    def _render_wire(self, cw: CompactWireRouter.CompactWire) -> str:
        C = self.COLORS
        
        color_map = {
            'deterministic': C['wire_det'],
            'llm': C['wire_llm'],
            'composite': C['wire_composite']
        }
        marker_map = {
            'deterministic': 'arrow-det',
            'llm': 'arrow-llm',
            'composite': 'arrow-composite'
        }
        
        color = color_map.get(cw.wire_type, C['wire_det'])
        marker = marker_map.get(cw.wire_type, 'arrow-det')
        dash = ' stroke-dasharray="6,4"' if cw.wire_type == 'llm' else ''
        opacity = '0.7' if cw.wire_type == 'deterministic' else '0.85'
        
        parts = []
        
        if cw.cost_tokens > 0:
            parts.append(
                f'  <path d="{cw.path_d}" fill="none" '
                f'stroke="{color}" stroke-width="{cw.thickness + 4:.1f}" '
                f'opacity="0.12" stroke-linecap="round"/>'
            )
        
        parts.append(
            f'  <path d="{cw.path_d}" fill="none" '
            f'stroke="{color}" stroke-width="{cw.thickness:.1f}" '
            f'opacity="{opacity}" stroke-linecap="round"{dash} '
            f'marker-end="url(#{marker})"/>'
        )
        
        if cw.cost_tokens > 0:
            mid_x = (cw.source_point.x + cw.target_point.x) / 2 + 12
            mid_y = (cw.source_point.y + cw.target_point.y) / 2
            parts.append(
                f'  <text x="{mid_x:.1f}" y="{mid_y:.1f}" '
                f'font-size="9" fill="{C["accent"]}" '
                f'font-weight="600" opacity="0.9">{cw.cost_tokens}t</text>'
            )
        
        return '\n'.join(parts)
    
    def _render_node(self, cp: CompactPosition, brick: Brick) -> str:
        C = self.COLORS
        cx, cy = cp.center.x, cp.center.y
        r = cp.radius
        
        is_llm = cp.llm_layers > 0
        fill = 'url(#grad-llm)' if is_llm else 'url(#grad-det)'
        node_filter = 'filter="url(#glow-llm)"' if is_llm else 'filter="url(#node-shadow)"'
        
        parts = [f'  <g class="node" data-brick="{cp.brick_id}">']
        
        # Input schema (above node)
        parts.append(
            f'    <text x="{cx}" y="{cy - r - 14}" text-anchor="middle" '
            f'font-size="8" fill="{C["text_secondary"]}" opacity="0.7">'
            f'{brick.input_schema}</text>'
        )
        
        # Layer ring (4 arcs)
        ring_r = r + 6
        layer_colors = [
            C['layer_foundation'],
            C['layer_structure'],
            C['layer_relational'],
            C['layer_contextual']
        ]
        
        for i, color in enumerate(layer_colors):
            start_angle = i * 90 - 90
            end_angle = start_angle + 85
            
            layer_grade = brick.layers[i].grade if i < len(brick.layers) else 0
            arc_width = '5' if layer_grade == 1 else '3'
            
            x1 = cx + ring_r * math.cos(math.radians(start_angle))
            y1 = cy + ring_r * math.sin(math.radians(start_angle))
            x2 = cx + ring_r * math.cos(math.radians(end_angle))
            y2 = cy + ring_r * math.sin(math.radians(end_angle))
            
            parts.append(
                f'    <path d="M {x1:.1f} {y1:.1f} A {ring_r} {ring_r} 0 0 1 {x2:.1f} {y2:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="{arc_width}" '
                f'stroke-linecap="round"/>'
            )
        
        # Main circle
        parts.append(
            f'    <circle cx="{cx}" cy="{cy}" r="{r}" '
            f'fill="{fill}" stroke="{C["node_stroke"]}" stroke-width="2" '
            f'{node_filter}/>'
        )
        
        # Brick name (center)
        name = brick.name
        if len(name) > 12:
            words = name.split()
            if len(words) >= 2:
                line1 = ' '.join(words[:len(words)//2])
                line2 = ' '.join(words[len(words)//2:])
                parts.append(
                    f'    <text x="{cx}" y="{cy - 4}" text-anchor="middle" '
                    f'font-size="10" font-weight="700" fill="{C["text_on_node"]}">{line1}</text>'
                )
                parts.append(
                    f'    <text x="{cx}" y="{cy + 8}" text-anchor="middle" '
                    f'font-size="10" font-weight="700" fill="{C["text_on_node"]}">{line2}</text>'
                )
            else:
                parts.append(
                    f'    <text x="{cx}" y="{cy + 4}" text-anchor="middle" '
                    f'font-size="9" font-weight="700" fill="{C["text_on_node"]}">{name[:14]}</text>'
                )
        else:
            parts.append(
                f'    <text x="{cx}" y="{cy + 4}" text-anchor="middle" '
                f'font-size="11" font-weight="700" fill="{C["text_on_node"]}">{name}</text>'
            )
        
        # Grade badge (top-right)
        badge_x = cx + r * 0.65
        badge_y = cy - r * 0.65
        badge_color = C['node_llm'] if is_llm else C['node_det']
        grade_text = f"G{cp.grade_max}"
        parts.append(
            f'    <circle cx="{badge_x:.1f}" cy="{badge_y:.1f}" r="10" '
            f'fill="{C["bg"]}" stroke="{badge_color}" stroke-width="1.5"/>'
        )
        parts.append(
            f'    <text x="{badge_x:.1f}" y="{badge_y + 3.5:.1f}" text-anchor="middle" '
            f'font-size="8" font-weight="700" fill="{badge_color}">{grade_text}</text>'
        )
        
        # Output schema (below node)
        parts.append(
            f'    <text x="{cx}" y="{cy + r + 20}" text-anchor="middle" '
            f'font-size="8" fill="{C["text_secondary"]}" opacity="0.7">'
            f'{brick.output_schema}</text>'
        )
        
        # Token cost (below output schema)
        if cp.total_tokens > 0:
            parts.append(
                f'    <text x="{cx}" y="{cy + r + 32}" text-anchor="middle" '
                f'font-size="8" fill="{C["accent"]}" font-weight="600">'
                f'{cp.total_tokens}t</text>'
            )
        
        parts.append('  </g>')
        return '\n'.join(parts)
    
    def _legend(self, canvas_w: int) -> str:
        C = self.COLORS
        x = canvas_w - 200
        y = 20
        
        return f'''  <g transform="translate({x}, {y})" opacity="0.8">
    <text x="0" y="0" font-size="9" font-weight="600" fill="{C['text_secondary']}" letter-spacing="0.08em">LEGEND</text>
    <circle cx="8" cy="14" r="5" fill="{C['node_det']}"/>
    <text x="18" y="18" font-size="8" fill="{C['text_secondary']}">Deterministic (G0)</text>
    <circle cx="8" cy="30" r="5" fill="{C['node_llm']}"/>
    <text x="18" y="34" font-size="8" fill="{C['text_secondary']}">LLM Synthesis (G1)</text>
    <line x1="2" y1="46" x2="14" y2="46" stroke="{C['wire_det']}" stroke-width="2"/>
    <text x="18" y="50" font-size="8" fill="{C['text_secondary']}">0-token wire</text>
    <line x1="2" y1="62" x2="14" y2="62" stroke="{C['wire_llm']}" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="18" y="66" font-size="8" fill="{C['text_secondary']}">Token-carrying wire</text>
  </g>'''
    
    def _cost_summary(self, cs: CostSummary, w: int, h: int) -> str:
        C = self.COLORS
        bar_y = h - 60
        bar_w = w - 60
        
        total_layers = cs.deterministic_layers + cs.llm_layers
        det_frac = cs.deterministic_layers / total_layers if total_layers > 0 else 1.0
        
        det_bar_w = max(bar_w * det_frac - 20, 0)
        llm_bar_w = max(bar_w * (1 - det_frac), 0)
        
        return f'''  <g transform="translate(30, {bar_y})">
    <rect x="0" y="0" width="{bar_w}" height="36" rx="6" 
          fill="{C['cost_bg']}" stroke="{C['cost_border']}" stroke-width="1" opacity="0.8"/>
    
    <rect x="10" y="22" width="{det_bar_w:.0f}" height="6" rx="3" fill="{C['node_det']}" opacity="0.7"/>
    <rect x="{det_bar_w + 10:.0f}" y="22" width="{llm_bar_w:.0f}" height="6" rx="3" fill="{C['node_llm']}" opacity="0.7"/>
    
    <text x="10" y="16" font-size="9" font-weight="600" fill="{C['text_primary']}">
      {cs.deterministic_layers}×G0 = 0t</text>
    <text x="{bar_w * 0.35:.0f}" y="16" font-size="9" font-weight="600" fill="{C['node_llm']}">
      {cs.llm_layers}×G1 = {cs.total_tokens}t</text>
    <text x="{bar_w * 0.65:.0f}" y="16" font-size="9" fill="{C['text_secondary']}">
      vs pure LLM ~{cs.vs_pure_llm}t</text>
    <text x="{bar_w - 10:.0f}" y="16" text-anchor="end" font-size="11" font-weight="700" fill="{C['node_det']}">
      {cs.savings_pct:.0f}% saved</text>
  </g>'''
    
    def _footer(self, w: int, h: int) -> str:
        C = self.COLORS
        return f'''  <text x="{w/2}" y="{h - 8}" text-anchor="middle" 
        font-size="8" fill="{C['text_secondary']}" opacity="0.5" letter-spacing="0.1em">
    LUSHY STRING DIAGRAM BRICK · COMPACT VIEW
  </text>'''
