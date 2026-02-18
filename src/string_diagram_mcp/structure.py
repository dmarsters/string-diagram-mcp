"""
String Diagram Generator Brick - Structure Layer
=================================================

Layer 2: Structure (Grade 0 - Deterministic)
Computes spatial layout of bricks using topological sorting.

Zero LLM cost - pure graph algorithms.
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict, deque

from foundation import (
    BrickComposition, Brick, Layout, BrickPosition, Point, 
    DiagramPrimitives
)


class LayoutComputer:
    """
    Structure layer: Deterministic layout computation
    
    Uses topological sorting to arrange bricks in layers,
    then distributes them spatially to minimize visual clutter.
    """
    
    def __init__(self, primitives: DiagramPrimitives):
        self.primitives = primitives
    
    def compute_layout(self, composition: BrickComposition) -> Layout:
        """
        Compute spatial layout from brick composition
        
        Algorithm:
        1. Build dependency DAG from connections
        2. Topological sort into layers
        3. Assign y-positions based on layer depth
        4. Distribute x-positions within each layer
        5. Calculate canvas dimensions
        
        Args:
            composition: The brick composition to layout
            
        Returns:
            Layout with brick positions and canvas size
        """
        
        # Step 1: Build dependency graph
        graph = self._build_dependency_graph(composition)
        
        # Step 2: Compute topological layers
        layers = self._topological_layers(graph, composition.bricks)
        
        # Step 3: Assign positions
        positions = self._assign_positions(layers, composition.bricks)
        
        # Step 4: Calculate canvas size
        canvas_width, canvas_height = self._compute_canvas_size(positions)
        
        return Layout(
            brick_positions=positions,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            layers_depth=len(layers)
        )
    
    def _build_dependency_graph(self, composition: BrickComposition) -> Dict[str, List[str]]:
        """
        Build directed acyclic graph (DAG) from brick connections
        
        Returns: Adjacency list where graph[brick_id] = [dependent_brick_ids]
        """
        graph = {brick.id: [] for brick in composition.bricks}
        
        for connection in composition.connections:
            source = connection.source_brick_id
            target = connection.target_brick_id
            graph[source].append(target)
        
        return graph
    
    def _topological_layers(
        self, 
        graph: Dict[str, List[str]],
        bricks: List[Brick]
    ) -> List[List[str]]:
        """
        Compute topological layers using Kahn's algorithm
        
        Groups bricks into layers where each layer contains bricks
        that can be executed in parallel (no dependencies within layer).
        
        Args:
            graph: Dependency adjacency list
            bricks: List of bricks
            
        Returns:
            List of layers, where each layer is a list of brick IDs
        """
        layers = []
        
        # Calculate in-degrees (number of incoming edges)
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
        
        # Find all nodes with no incoming edges (input nodes)
        remaining = set(graph.keys())
        
        while remaining:
            # Current layer = nodes with in-degree 0
            current_layer = [node for node in remaining if in_degree[node] == 0]
            
            if not current_layer:
                # Cycle detected - break it by taking node with minimum in-degree
                # This shouldn't happen with valid compositions, but handle gracefully
                current_layer = [min(remaining, key=lambda n: in_degree[n])]
            
            layers.append(current_layer)
            
            # Remove current layer nodes and update in-degrees
            for node in current_layer:
                remaining.remove(node)
                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
        
        return layers
    
    def _assign_positions(
        self,
        layers: List[List[str]],
        bricks: List[Brick]
    ) -> List[BrickPosition]:
        """
        Assign (x, y) coordinates to each brick
        
        Strategy:
        - Y position determined by layer depth
        - X position distributed evenly within layer
        - Special handling for single-brick layers (center them)
        
        Args:
            layers: Topological layers
            bricks: List of bricks
            
        Returns:
            List of brick positions
        """
        positions = []
        brick_map = {b.id: b for b in bricks}
        
        brick_height = self.primitives.brick_box['default_height']
        brick_width = self.primitives.brick_box['default_width']
        spacing_y = self.primitives.constraints['min_brick_spacing_y']
        spacing_x = self.primitives.constraints['min_brick_spacing_x']
        margin_top = self.primitives.constraints['margin_top']
        
        for layer_idx, layer in enumerate(layers):
            # Y position based on layer depth
            y_pos = margin_top + layer_idx * (brick_height + spacing_y)
            
            # Calculate total width needed for this layer
            layer_brick_count = len(layer)
            total_layer_width = (
                layer_brick_count * brick_width + 
                (layer_brick_count - 1) * spacing_x
            )
            
            # Start X position (centered on canvas)
            canvas_center = self.primitives.constraints['max_diagram_width'] / 2
            start_x = canvas_center - (total_layer_width / 2)
            
            # Distribute bricks evenly in layer
            for brick_idx, brick_id in enumerate(layer):
                x_pos = start_x + brick_idx * (brick_width + spacing_x)
                
                positions.append(BrickPosition(
                    brick_id=brick_id,
                    position=Point(x_pos, y_pos),
                    width=brick_width,
                    height=brick_height
                ))
        
        return positions
    
    def _compute_canvas_size(self, positions: List[BrickPosition]) -> Tuple[int, int]:
        """
        Compute minimum canvas size to fit all bricks with margins
        
        Args:
            positions: List of brick positions
            
        Returns:
            Tuple of (width, height)
        """
        if not positions:
            return 800, 600
        
        # Find bounds
        max_x = max(p.position.x + p.width for p in positions)
        max_y = max(p.position.y + p.height for p in positions)
        
        # Add margins
        margin_right = self.primitives.constraints['margin_right']
        margin_bottom = self.primitives.constraints['margin_bottom']
        
        width = int(max_x + margin_right)
        height = int(max_y + margin_bottom)
        
        return width, height
    
    def get_brick_center(self, brick_pos: BrickPosition) -> Point:
        """Get the center point of a brick"""
        return Point(
            brick_pos.position.x + brick_pos.width / 2,
            brick_pos.position.y + brick_pos.height / 2
        )
    
    def get_brick_top_center(self, brick_pos: BrickPosition) -> Point:
        """Get the top-center attachment point of a brick"""
        return Point(
            brick_pos.position.x + brick_pos.width / 2,
            brick_pos.position.y
        )
    
    def get_brick_bottom_center(self, brick_pos: BrickPosition) -> Point:
        """Get the bottom-center attachment point of a brick"""
        return Point(
            brick_pos.position.x + brick_pos.width / 2,
            brick_pos.position.y + brick_pos.height
        )


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Testing Structure Layer...")
    
    from .foundation import (
        create_sample_composition, DiagramPrimitives, Connection
    )
    
    # Load primitives
    primitives = DiagramPrimitives.load_defaults()
    layout_computer = LayoutComputer(primitives)
    
    # Test 1: Simple sequential composition
    print("\n1. Testing sequential composition...")
    composition = create_sample_composition()
    layout = layout_computer.compute_layout(composition)
    
    print(f"   ✓ Canvas size: {layout.canvas_width} x {layout.canvas_height}")
    print(f"   ✓ Layers depth: {layout.layers_depth}")
    print(f"   ✓ Brick positions: {len(layout.brick_positions)}")
    
    # Verify positions
    for pos in layout.brick_positions:
        print(f"   - {pos.brick_id}: ({pos.position.x:.0f}, {pos.position.y:.0f})")
    
    # Test 2: Branching composition
    print("\n2. Testing branching composition...")
    from .foundation import create_sample_brick
    
    brick1 = create_sample_brick("input", "Input Processor", "RawData", "ProcessedData")
    brick2 = create_sample_brick("branch1", "Branch A", "ProcessedData", "ResultA")
    brick3 = create_sample_brick("branch2", "Branch B", "ProcessedData", "ResultB")
    
    branching_composition = BrickComposition(
        bricks=[brick1, brick2, brick3],
        connections=[
            Connection("input", "branch1", is_branching=True),
            Connection("input", "branch2", is_branching=True)
        ],
        metadata={"name": "Branching Test"}
    )
    
    branching_layout = layout_computer.compute_layout(branching_composition)
    print(f"   ✓ Canvas size: {branching_layout.canvas_width} x {branching_layout.canvas_height}")
    print(f"   ✓ Layers depth: {branching_layout.layers_depth}")
    
    for pos in branching_layout.brick_positions:
        print(f"   - {pos.brick_id}: ({pos.position.x:.0f}, {pos.position.y:.0f})")
    
    # Test 3: Determinism check
    print("\n3. Testing determinism...")
    layout1 = layout_computer.compute_layout(composition)
    layout2 = layout_computer.compute_layout(composition)
    
    # Check that positions are identical
    positions_match = all(
        p1.position.x == p2.position.x and p1.position.y == p2.position.y
        for p1, p2 in zip(layout1.brick_positions, layout2.brick_positions)
    )
    
    if positions_match:
        print("   ✓ Layout is deterministic (same input → same output)")
    else:
        print("   ✗ Layout is non-deterministic!")
    
    # Test 4: Attachment points
    print("\n4. Testing attachment point helpers...")
    test_pos = layout.brick_positions[0]
    top_center = layout_computer.get_brick_top_center(test_pos)
    bottom_center = layout_computer.get_brick_bottom_center(test_pos)
    center = layout_computer.get_brick_center(test_pos)
    
    print(f"   ✓ Brick {test_pos.brick_id}:")
    print(f"     - Top center: ({top_center.x:.0f}, {top_center.y:.0f})")
    print(f"     - Center: ({center.x:.0f}, {center.y:.0f})")
    print(f"     - Bottom center: ({bottom_center.x:.0f}, {bottom_center.y:.0f})")
    
    print("\nStructure layer test complete!")
