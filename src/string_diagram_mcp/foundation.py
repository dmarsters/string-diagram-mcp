"""
String Diagram Generator Brick - Foundation Layer
==================================================

Layer 1: Foundation (Grade 0 - Deterministic)
Defines core diagram primitives, constraints, and data structures.

Zero LLM cost - pure taxonomy and configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Point:
    """2D point for positioning"""
    x: float
    y: float


@dataclass
class Layer:
    """Represents one layer of a Lushy brick"""
    name: str  # 'foundation', 'structure', 'relational', 'contextual'
    grade: int  # 0 = deterministic, 1 = LLM, 2 = human
    estimated_tokens: int
    description: str


@dataclass
class Brick:
    """Represents a Lushy brick in a composition"""
    id: str
    name: str
    input_schema: str  # Schema type name (e.g., "CSV", "SentimentData")
    output_schema: str
    layers: List[Layer]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Connection:
    """Represents a wire between bricks"""
    source_brick_id: str
    target_brick_id: str
    source_output: str = "output"  # Output field name
    target_input: str = "input"    # Input field name
    is_branching: bool = False     # True if source splits to multiple targets


@dataclass
class BrickComposition:
    """Complete workflow composition (INPUT SCHEMA)"""
    bricks: List[Brick]
    connections: List[Connection]
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# LAYOUT DATA STRUCTURES
# ============================================================================

@dataclass
class BrickPosition:
    """Position of a brick in the diagram"""
    brick_id: str
    position: Point
    width: int
    height: int


@dataclass
class Layout:
    """Computed spatial layout"""
    brick_positions: List[BrickPosition]
    canvas_width: int
    canvas_height: int
    layers_depth: int  # Maximum composition depth


# ============================================================================
# WIRE DATA STRUCTURES
# ============================================================================

@dataclass
class Wire:
    """A wire connecting two bricks"""
    source_brick: str
    target_brick: str
    source_point: Point
    target_point: Point
    control_points: List[Point]
    wire_type: str  # 'deterministic', 'llm', 'composite'
    cost_tokens: int


@dataclass
class WireRouting:
    """Complete wire routing information"""
    wires: List[Wire]
    total_crossings: int


# ============================================================================
# ANNOTATION DATA STRUCTURES
# ============================================================================

@dataclass
class Annotation:
    """Human-readable annotation"""
    text: str
    position: Point
    annotation_type: str  # 'cost', 'description', 'suggestion'


@dataclass
class CostSummary:
    """Detailed cost analysis"""
    total_tokens: int
    deterministic_layers: int
    llm_layers: int
    vs_pure_llm: int
    savings_pct: float
    breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================================
# OUTPUT SCHEMA
# ============================================================================

@dataclass
class StringDiagram:
    """Complete string diagram output (OUTPUT SCHEMA)"""
    svg: str  # Rendered SVG markup
    layout: Layout
    routing: WireRouting
    annotations: List[Annotation]
    cost_summary: CostSummary
    metadata: Dict[str, Any]
    interactive_data: Optional[Dict[str, Any]] = None


# ============================================================================
# FOUNDATION: DIAGRAM PRIMITIVES
# ============================================================================

@dataclass
class DiagramPrimitives:
    """
    Foundation layer: Immutable diagram primitives and constraints
    
    This is the taxonomy that defines how diagrams are structured.
    Zero LLM cost - pure configuration data.
    """
    
    brick_box: Dict[str, Any]
    layer_dimensions: Dict[str, int]
    wire_styles: Dict[str, Dict[str, Any]]
    colors: Dict[str, str]
    constraints: Dict[str, int]
    
    @classmethod
    def load_defaults(cls) -> 'DiagramPrimitives':
        """
        Load default primitive definitions
        
        Returns: DiagramPrimitives with standard configuration
        """
        return cls(
            brick_box={
                'default_width': 400,
                'default_height': 280,
                'border_radius': 10,
                'stroke_width': 3
            },
            
            layer_dimensions={
                'title_height': 25,
                'input_schema_height': 30,
                'layer_height': 40,
                'output_schema_height': 20,
                'padding': 10
            },
            
            wire_styles={
                'deterministic': {
                    'stroke': '#10b981',
                    'stroke_width': 4,
                    'marker': 'arrowhead-det',
                    'grade': 0,
                    'dash_array': None
                },
                'llm': {
                    'stroke': '#8b5cf6',
                    'stroke_width': 6,
                    'marker': 'arrowhead-llm',
                    'grade': 1,
                    'dash_array': '8,4'
                },
                'composite': {
                    'stroke': '#667eea',
                    'stroke_width': 8,
                    'marker': 'arrowhead-composite',
                    'grade': None,
                    'dash_array': None
                }
            },
            
            colors={
                'layer_foundation': '#6b7280',
                'layer_structure': '#10b981',
                'layer_relational': '#3b82f6',
                'layer_contextual': '#8b5cf6',
                'grade_0_badge': '#10b981',
                'grade_1_badge': '#8b5cf6',
                'grade_2_badge': '#ef4444',
                'background': '#ffffff',
                'border': '#667eea',
                'text': '#333333',
                'text_secondary': '#666666'
            },
            
            constraints={
                'max_diagram_width': 2000,
                'max_diagram_height': 3000,
                'min_brick_spacing_x': 50,
                'min_brick_spacing_y': 100,
                'wire_control_point_offset': 50,
                'margin_top': 150,
                'margin_bottom': 250,
                'margin_left': 50,
                'margin_right': 50
            }
        )
    
    def get_layer_color(self, layer_name: str) -> str:
        """Get color for a specific layer"""
        color_key = f'layer_{layer_name}'
        return self.colors.get(color_key, self.colors['layer_foundation'])
    
    def get_grade_badge_color(self, grade: int) -> str:
        """Get badge color for a grade level"""
        grade_key = f'grade_{grade}_badge'
        return self.colors.get(grade_key, self.colors['grade_0_badge'])
    
    def get_wire_style(self, wire_type: str) -> Dict[str, Any]:
        """Get complete wire style configuration"""
        return self.wire_styles.get(wire_type, self.wire_styles['deterministic'])


# ============================================================================
# VALIDATION
# ============================================================================

def validate_composition(composition: BrickComposition) -> List[str]:
    """
    Validate brick composition for common errors
    
    Returns: List of error messages (empty if valid)
    """
    errors = []
    
    # Check for duplicate brick IDs
    brick_ids = [b.id for b in composition.bricks]
    if len(brick_ids) != len(set(brick_ids)):
        errors.append("Duplicate brick IDs found")
    
    # Check connections reference valid bricks
    brick_id_set = set(brick_ids)
    for conn in composition.connections:
        if conn.source_brick_id not in brick_id_set:
            errors.append(f"Connection references unknown source brick: {conn.source_brick_id}")
        if conn.target_brick_id not in brick_id_set:
            errors.append(f"Connection references unknown target brick: {conn.target_brick_id}")
    
    # Check each brick has 4 layers
    for brick in composition.bricks:
        if len(brick.layers) != 4:
            errors.append(f"Brick {brick.id} has {len(brick.layers)} layers (expected 4)")
    
    # Check layer names are correct
    expected_layer_names = {'foundation', 'structure', 'relational', 'contextual'}
    for brick in composition.bricks:
        layer_names = {layer.name for layer in brick.layers}
        if layer_names != expected_layer_names:
            errors.append(f"Brick {brick.id} has invalid layer names: {layer_names}")
    
    return errors


# ============================================================================
# TESTING UTILITIES
# ============================================================================

def create_sample_brick(
    brick_id: str,
    name: str,
    input_schema: str = "InputData",
    output_schema: str = "OutputData",
    llm_layer_tokens: int = 200
) -> Brick:
    """Create a sample brick for testing"""
    return Brick(
        id=brick_id,
        name=name,
        input_schema=input_schema,
        output_schema=output_schema,
        layers=[
            Layer("foundation", grade=0, estimated_tokens=0, description="Taxonomy and rules"),
            Layer("structure", grade=0, estimated_tokens=0, description="Mapping logic"),
            Layer("relational", grade=0, estimated_tokens=0, description="Relationships"),
            Layer("contextual", grade=1, estimated_tokens=llm_layer_tokens, description="LLM synthesis")
        ],
        metadata={}
    )


def create_sample_composition() -> BrickComposition:
    """Create a simple 3-brick composition for testing"""
    brick1 = create_sample_brick("brick1", "Parse Input", "RawData", "StructuredData", 100)
    brick2 = create_sample_brick("brick2", "Transform", "StructuredData", "ProcessedData", 150)
    brick3 = create_sample_brick("brick3", "Generate Output", "ProcessedData", "FinalOutput", 200)
    
    return BrickComposition(
        bricks=[brick1, brick2, brick3],
        connections=[
            Connection("brick1", "brick2", "output", "input", False),
            Connection("brick2", "brick3", "output", "input", False)
        ],
        metadata={
            "name": "Sample Workflow",
            "description": "A simple 3-brick sequential workflow"
        }
    )


if __name__ == "__main__":
    # Test foundation layer
    print("Testing Foundation Layer...")
    
    # Load primitives
    primitives = DiagramPrimitives.load_defaults()
    print(f"✓ Loaded primitives: {len(primitives.colors)} colors defined")
    
    # Create sample composition
    composition = create_sample_composition()
    print(f"✓ Created composition: {len(composition.bricks)} bricks")
    
    # Validate
    errors = validate_composition(composition)
    if errors:
        print(f"✗ Validation errors: {errors}")
    else:
        print("✓ Composition is valid")
    
    # Test color lookups
    foundation_color = primitives.get_layer_color('foundation')
    print(f"✓ Foundation layer color: {foundation_color}")
    
    grade_color = primitives.get_grade_badge_color(1)
    print(f"✓ Grade 1 badge color: {grade_color}")
    
    print("\nFoundation layer test complete!")
