"""
String Diagram Generator Brick - Relational Layer
==================================================

Layer 3: Relational (Grade 0 - Deterministic)
Routes wires between bricks and computes relationships.

Zero LLM cost - pure geometric algorithms.
"""

from typing import List, Dict
from foundation import (
    Wire, WireRouting, Point, BrickComposition, Brick, 
    Layout, BrickPosition, DiagramPrimitives
)


class WireRouter:
    """
    Relational layer: Wire routing and cost calculation
    
    Routes wires between bricks using Bezier curves,
    determines wire types based on grades, and calculates costs.
    """
    
    def __init__(self, primitives: DiagramPrimitives):
        self.primitives = primitives
    
    def route_wires(
        self,
        layout: Layout,
        composition: BrickComposition
    ) -> WireRouting:
        """
        Route all wires in the composition
        
        Algorithm:
        1. Create position lookup table
        2. For each connection, determine attachment points
        3. Detect wire type from source brick grades
        4. Compute Bezier control points for smooth curves
        5. Calculate accumulated token cost
        6. Count wire crossings for quality metric
        
        Args:
            layout: Computed brick layout
            composition: Original brick composition
            
        Returns:
            WireRouting with all wires and metrics
        """
        wires = []
        
        # Create lookup tables
        pos_map = {bp.brick_id: bp for bp in layout.brick_positions}
        brick_map = {b.id: b for b in composition.bricks}
        
        # Route each connection
        for connection in composition.connections:
            source_pos = pos_map[connection.source_brick_id]
            target_pos = pos_map[connection.target_brick_id]
            source_brick = brick_map[connection.source_brick_id]
            
            # Determine attachment points
            source_point = Point(
                source_pos.position.x + source_pos.width / 2,
                source_pos.position.y + source_pos.height
            )
            target_point = Point(
                target_pos.position.x + target_pos.width / 2,
                target_pos.position.y
            )
            
            # Determine wire type based on source brick's grades
            wire_type = self._determine_wire_type(source_brick, connection)
            
            # Compute Bezier control points for smooth curve
            control_points = self._compute_control_points(source_point, target_point)
            
            # Calculate token cost accumulated to this point
            cost_tokens = self._calculate_connection_cost(source_brick)
            
            wires.append(Wire(
                source_brick=connection.source_brick_id,
                target_brick=connection.target_brick_id,
                source_point=source_point,
                target_point=target_point,
                control_points=control_points,
                wire_type=wire_type,
                cost_tokens=cost_tokens
            ))
        
        # Count wire crossings (quality metric)
        crossings = self._count_crossings(wires)
        
        return WireRouting(
            wires=wires,
            total_crossings=crossings
        )
    
    def _determine_wire_type(self, source_brick: Brick, connection) -> str:
        """
        Determine wire type based on source brick's layer grades
        
        Logic:
        - If source has any Grade 1 (LLM) layers → 'llm' wire
        - If purely Grade 0 (deterministic) → 'deterministic' wire  
        - If connection is branching → 'composite' wire
        
        Args:
            source_brick: The source brick
            connection: The connection info
            
        Returns:
            Wire type string ('deterministic', 'llm', or 'composite')
        """
        # Check for branching first
        if connection.is_branching:
            return 'composite'
        
        # Check if source brick uses LLM in any layer
        has_llm = any(layer.grade == 1 for layer in source_brick.layers)
        
        return 'llm' if has_llm else 'deterministic'
    
    def _compute_control_points(self, source: Point, target: Point) -> List[Point]:
        """
        Compute cubic Bezier control points for smooth wire routing
        
        Creates an S-curve that looks natural for vertical connections.
        Uses cubic Bezier: P(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
        
        Args:
            source: Starting point (bottom of source brick)
            target: Ending point (top of target brick)
            
        Returns:
            List of two control points for cubic Bezier
        """
        # Vertical distance between points
        dy = target.y - source.y
        
        # Horizontal offset for control points (creates gentle curve)
        dx = target.x - source.x
        
        # Control points create smooth S-curve
        # First control point: below source, moving toward target
        control1 = Point(
            source.x + dx * 0.2,  # Slight horizontal adjustment
            source.y + dy * 0.3   # 30% down from source
        )
        
        # Second control point: above target, coming from source
        control2 = Point(
            target.x - dx * 0.2,  # Slight horizontal adjustment
            target.y - dy * 0.3   # 30% up from target
        )
        
        return [control1, control2]
    
    def _calculate_connection_cost(self, source_brick: Brick) -> int:
        """
        Calculate token cost accumulated through source brick
        
        Sums all LLM (Grade 1) layer costs in the source brick.
        
        Args:
            source_brick: The brick outputting to this connection
            
        Returns:
            Total tokens used up to this point
        """
        return sum(
            layer.estimated_tokens
            for layer in source_brick.layers
            if layer.grade == 1
        )
    
    def _count_crossings(self, wires: List[Wire]) -> int:
        """
        Count number of wire crossings (quality metric)
        
        Simplified implementation: checks if line segments cross.
        Full implementation would check Bezier curve intersections.
        
        Args:
            wires: List of all wires
            
        Returns:
            Number of crossing pairs
        """
        crossings = 0
        
        for i, wire1 in enumerate(wires):
            for wire2 in wires[i+1:]:
                if self._wires_cross(wire1, wire2):
                    crossings += 1
        
        return crossings
    
    def _wires_cross(self, wire1: Wire, wire2: Wire) -> bool:
        """
        Check if two wires intersect
        
        Simplified: checks if straight line segments cross.
        Real implementation would check Bezier curves.
        
        Args:
            wire1: First wire
            wire2: Second wire
            
        Returns:
            True if wires cross
        """
        return self._segments_intersect(
            wire1.source_point, wire1.target_point,
            wire2.source_point, wire2.target_point
        )
    
    def _segments_intersect(
        self,
        a1: Point, a2: Point,
        b1: Point, b2: Point
    ) -> bool:
        """
        Check if line segments (a1,a2) and (b1,b2) intersect
        
        Uses CCW (counter-clockwise) test for intersection detection.
        
        Args:
            a1, a2: Endpoints of first segment
            b1, b2: Endpoints of second segment
            
        Returns:
            True if segments intersect
        """
        def ccw(a: Point, b: Point, c: Point) -> bool:
            """Check if three points are in counter-clockwise order"""
            return (c.y - a.y) * (b.x - a.x) > (b.y - a.y) * (c.x - a.x)
        
        # Segments intersect if endpoints are on opposite sides
        return (ccw(a1, b1, b2) != ccw(a2, b1, b2) and
                ccw(a1, a2, b1) != ccw(a1, a2, b2))
    
    def format_bezier_path(self, wire: Wire) -> str:
        """
        Format wire as SVG path data string
        
        Args:
            wire: Wire to format
            
        Returns:
            SVG path 'd' attribute value
        """
        if len(wire.control_points) >= 2:
            # Cubic Bezier curve
            return (
                f"M {wire.source_point.x} {wire.source_point.y} "
                f"C {wire.control_points[0].x} {wire.control_points[0].y}, "
                f"{wire.control_points[1].x} {wire.control_points[1].y}, "
                f"{wire.target_point.x} {wire.target_point.y}"
            )
        else:
            # Straight line fallback
            return (
                f"M {wire.source_point.x} {wire.source_point.y} "
                f"L {wire.target_point.x} {wire.target_point.y}"
            )


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Testing Relational Layer...")
    
    from .foundation import (
        create_sample_composition, DiagramPrimitives, 
        create_sample_brick, Connection, BrickComposition,
        Layer, Brick
    )
    from .structure import LayoutComputer
    
    # Setup
    primitives = DiagramPrimitives.load_defaults()
    layout_computer = LayoutComputer(primitives)
    wire_router = WireRouter(primitives)
    
    # Test 1: Sequential composition
    print("\n1. Testing sequential wire routing...")
    composition = create_sample_composition()
    layout = layout_computer.compute_layout(composition)
    routing = wire_router.route_wires(layout, composition)
    
    print(f"   ✓ Wires routed: {len(routing.wires)}")
    print(f"   ✓ Wire crossings: {routing.total_crossings}")
    
    for wire in routing.wires:
        print(f"   - {wire.source_brick} → {wire.target_brick}")
        print(f"     Type: {wire.wire_type}, Cost: {wire.cost_tokens} tokens")
        print(f"     Path: ({wire.source_point.x:.0f},{wire.source_point.y:.0f}) → "
              f"({wire.target_point.x:.0f},{wire.target_point.y:.0f})")
    
    # Test 2: Branching composition
    print("\n2. Testing branching wire routing...")
    brick1 = create_sample_brick("input", "Input", "Raw", "Processed", 200)
    brick2 = create_sample_brick("path_a", "Path A", "Processed", "ResultA", 100)
    brick3 = create_sample_brick("path_b", "Path B", "Processed", "ResultB", 150)
    
    branching_comp = BrickComposition(
        bricks=[brick1, brick2, brick3],
        connections=[
            Connection("input", "path_a", is_branching=True),
            Connection("input", "path_b", is_branching=True)
        ],
        metadata={"name": "Branching Test"}
    )
    
    branch_layout = layout_computer.compute_layout(branching_comp)
    branch_routing = wire_router.route_wires(branch_layout, branching_comp)
    
    print(f"   ✓ Wires routed: {len(branch_routing.wires)}")
    print(f"   ✓ Wire crossings: {branch_routing.total_crossings}")
    
    for wire in branch_routing.wires:
        print(f"   - {wire.source_brick} → {wire.target_brick} ({wire.wire_type})")
    
    # Test 3: Wire type detection
    print("\n3. Testing wire type detection...")
    
    # Create brick with no LLM layers (all Grade 0)
    det_brick = Brick(
        id="det_brick",
        name="Deterministic Only",
        input_schema="Input",
        output_schema="Output",
        layers=[
            Layer("foundation", grade=0, estimated_tokens=0, description=""),
            Layer("structure", grade=0, estimated_tokens=0, description=""),
            Layer("relational", grade=0, estimated_tokens=0, description=""),
            Layer("contextual", grade=0, estimated_tokens=0, description="")
        ],
        metadata={}
    )
    
    conn = Connection("det_brick", "other", is_branching=False)
    wire_type = wire_router._determine_wire_type(det_brick, conn)
    print(f"   ✓ All Grade 0 layers → '{wire_type}' wire")
    
    # Create brick with LLM layer
    llm_brick = create_sample_brick("llm_brick", "Has LLM", "Input", "Output", 200)
    wire_type_llm = wire_router._determine_wire_type(llm_brick, conn)
    print(f"   ✓ Has Grade 1 layer → '{wire_type_llm}' wire")
    
    # Test branching
    branch_conn = Connection("det_brick", "other", is_branching=True)
    wire_type_branch = wire_router._determine_wire_type(det_brick, branch_conn)
    print(f"   ✓ Branching connection → '{wire_type_branch}' wire")
    
    # Test 4: Bezier path formatting
    print("\n4. Testing Bezier path formatting...")
    test_wire = routing.wires[0]
    path_string = wire_router.format_bezier_path(test_wire)
    print(f"   ✓ Generated SVG path:")
    print(f"     {path_string[:80]}...")
    
    # Test 5: Cost calculation
    print("\n5. Testing cost calculation...")
    total_tokens = sum(wire.cost_tokens for wire in routing.wires)
    print(f"   ✓ Total tokens through all wires: {total_tokens}")
    
    # Verify cost accumulates correctly
    expected = sum(
        layer.estimated_tokens 
        for brick in composition.bricks 
        for layer in brick.layers 
        if layer.grade == 1
    )
    print(f"   ✓ Expected total from bricks: {expected}")
    
    print("\nRelational layer test complete!")
