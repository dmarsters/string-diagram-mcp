"""
String Diagram Generator MCP Server
====================================

FastMCP server wrapping the String Diagram Generator Brick.
Provides tools for generating category-theoretic visualizations of Lushy workflows.

Render styles:
- 'box': Original box-and-wire with internal layer structure
- 'compact': ZX-style compact nodes with topology-focused layout (default)

Usage:
    # As MCP server
    python -m string_diagram_mcp
    
    # Test locally
    python -m string_diagram_mcp --test
"""

from fastmcp import FastMCP
from typing import Optional, Literal
import json

from string_diagram_mcp.brick import StringDiagramBrick
from string_diagram_mcp.foundation import (
    BrickComposition, Brick, Layer, Connection,
    create_sample_brick, create_sample_composition
)
from string_diagram_mcp.generic import (
    GenericComposition, parse_generic_composition,
    validate_generic_composition,
    create_sample_generic_sequential,
    create_sample_generic_quantum,
    create_sample_generic_branching,
)
from string_diagram_mcp.generic_renderer import GenericCompactRenderer
from string_diagram_mcp.adapters import brick_to_generic

# Initialize FastMCP server
mcp = FastMCP("string-diagram-generator")

# Initialize the brick (singleton, default to compact style)
diagram_brick = StringDiagramBrick(render_style='compact')


# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool()
def generate_string_diagram(
    composition_json: str,
    render_style: str = "compact",
    include_annotations: bool = False,
    save_path: Optional[str] = None
) -> str:
    """
    Generate a string diagram from a brick composition.
    
    This is the main tool for creating category-theoretic visualizations
    of Lushy workflows. Returns SVG markup and detailed cost analysis.
    
    Args:
        composition_json: JSON string representing BrickComposition with:
            - bricks: List of brick objects
            - connections: List of connection objects
            - metadata: Dict with name, description, etc.
        render_style: Diagram visual style:
            - "compact": ZX-style compact nodes with layer ring (default)
            - "box": Original box-and-wire with internal layer structure
        include_annotations: Generate LLM annotations (~200 tokens extra cost)
        save_path: Optional path to save SVG file
        
    Returns:
        JSON string containing:
        - svg: Complete SVG markup
        - cost_summary: Token costs and savings
        - metadata: Generation metadata including render_style
        - layout_info: Canvas size and brick positions
        
    Example composition_json:
    {
        "bricks": [
            {
                "id": "brick1",
                "name": "Parser",
                "input_schema": "CSV",
                "output_schema": "Data",
                "layers": [
                    {"name": "foundation", "grade": 0, "estimated_tokens": 0, "description": "Schema"},
                    {"name": "structure", "grade": 0, "estimated_tokens": 0, "description": "Mapping"},
                    {"name": "relational", "grade": 0, "estimated_tokens": 0, "description": "Conversion"},
                    {"name": "contextual", "grade": 1, "estimated_tokens": 150, "description": "Synthesis"}
                ],
                "metadata": {}
            }
        ],
        "connections": [
            {"source_brick_id": "brick1", "target_brick_id": "brick2"}
        ],
        "metadata": {"name": "My Workflow"}
    }
    
    Cost:
        - Deterministic mode (include_annotations=False): 0 tokens
        - With annotations (include_annotations=True): ~200 tokens
    """
    try:
        # Validate render_style
        if render_style not in ('box', 'compact'):
            render_style = 'compact'
        
        # Parse JSON to composition object
        composition_data = json.loads(composition_json)
        composition = _json_to_composition(composition_data)
        
        # Generate diagram with specified style
        diagram = diagram_brick.generate(
            composition,
            include_annotations=include_annotations,
            render_style=render_style
        )
        
        # Save if requested
        if save_path:
            with open(save_path, 'w') as f:
                f.write(diagram.svg)
        
        # Return results as JSON
        return json.dumps({
            'svg': diagram.svg,
            'cost_summary': {
                'total_tokens': diagram.cost_summary.total_tokens,
                'deterministic_layers': diagram.cost_summary.deterministic_layers,
                'llm_layers': diagram.cost_summary.llm_layers,
                'vs_pure_llm': diagram.cost_summary.vs_pure_llm,
                'savings_pct': round(diagram.cost_summary.savings_pct, 1),
                'breakdown': diagram.cost_summary.breakdown
            },
            'metadata': diagram.metadata,
            'layout_info': {
                'canvas_width': diagram.layout.canvas_width,
                'canvas_height': diagram.layout.canvas_height,
                'layers_depth': diagram.layout.layers_depth,
                'brick_count': len(diagram.layout.brick_positions),
                'wire_crossings': diagram.routing.total_crossings
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': str(e),
            'error_type': type(e).__name__
        })


@mcp.tool()
def generate_meta_diagram(
    render_style: str = "compact",
    save_path: Optional[str] = None
) -> str:
    """
    Generate a string diagram of the String Diagram Generator itself!
    
    This demonstrates the recursive beauty of the meta-brick - it can
    visualize its own four-layer compositional structure.
    
    Args:
        render_style: "compact" (default) or "box"
        save_path: Optional path to save SVG file
        
    Returns:
        JSON string containing SVG and metadata showing the String Diagram
        Generator's own four-layer structure (Foundation, Structure, 
        Relational, Contextual)
        
    Cost: 0 tokens (deterministic)
    """
    try:
        if render_style not in ('box', 'compact'):
            render_style = 'compact'
        
        diagram = diagram_brick.generate_meta_diagram(render_style=render_style)
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(diagram.svg)
        
        return json.dumps({
            'svg': diagram.svg,
            'cost_summary': {
                'total_tokens': diagram.cost_summary.total_tokens,
                'savings_pct': round(diagram.cost_summary.savings_pct, 1)
            },
            'metadata': diagram.metadata,
            'message': 'This diagram shows the String Diagram Generator diagramming itself - pure recursion!'
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': str(e),
            'error_type': type(e).__name__
        })


@mcp.tool()
def get_brick_layer_info() -> str:
    """
    Get detailed information about the String Diagram Generator's layer structure.
    
    Returns detailed breakdown of the four-layer architecture showing
    what each layer does, its computational cost, and available render styles.
    
    Returns:
        JSON string describing the four layers (Foundation, Structure,
        Relational, Contextual) with their grades, costs, and render options
        
    Cost: 0 tokens (pure metadata retrieval)
    """
    layer_info = diagram_brick.get_layer_info()
    return json.dumps(layer_info, indent=2)


@mcp.tool()
def create_sample_diagram(
    workflow_type: str = "sequential",
    render_style: str = "compact",
    save_path: Optional[str] = None
) -> str:
    """
    Generate a sample string diagram for demonstration purposes.
    
    Useful for testing, demos, and understanding how string diagrams work.
    
    Args:
        workflow_type: Type of sample workflow to generate
            - "sequential": Simple 3-brick sequential workflow
            - "branching": 4-brick workflow with parallel composition
            - "meta": String Diagram Generator diagramming itself
        render_style: "compact" (default) or "box"
        save_path: Optional path to save SVG file
        
    Returns:
        JSON string with SVG and metadata
        
    Cost: 0 tokens (uses pre-defined samples)
    """
    try:
        if render_style not in ('box', 'compact'):
            render_style = 'compact'
        
        if workflow_type == "sequential":
            composition = create_sample_composition()
            composition.metadata = {
                "name": "Sample Sequential Workflow",
                "description": "3-brick sequential composition for demonstration"
            }
        
        elif workflow_type == "branching":
            brick1 = create_sample_brick("input", "Input Parser", "CSV", "ParsedData", 150)
            brick2 = create_sample_brick("process1", "Processor A", "ParsedData", "ProcessedA", 300)
            brick3 = create_sample_brick("process2", "Processor B", "ParsedData", "ProcessedB", 200)
            brick4 = create_sample_brick("merge", "Merge Results", "ProcessedA,ProcessedB", "FinalOutput", 100)
            
            composition = BrickComposition(
                bricks=[brick1, brick2, brick3, brick4],
                connections=[
                    Connection("input", "process1"),
                    Connection("input", "process2"),
                    Connection("process1", "merge"),
                    Connection("process2", "merge")
                ],
                metadata={
                    "name": "Branching Workflow",
                    "description": "Parallel processing with merge"
                }
            )
        
        elif workflow_type == "meta":
            return generate_meta_diagram(render_style, save_path)
        
        else:
            return json.dumps({
                'error': f'Unknown workflow type: {workflow_type}',
                'valid_types': ['sequential', 'branching', 'meta']
            })
        
        # Generate diagram with specified style
        diagram = diagram_brick.generate(
            composition,
            render_style=render_style
        )
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(diagram.svg)
        
        return json.dumps({
            'svg': diagram.svg,
            'cost_summary': {
                'total_tokens': diagram.cost_summary.total_tokens,
                'savings_pct': round(diagram.cost_summary.savings_pct, 1)
            },
            'metadata': diagram.metadata,
            'layout_info': {
                'canvas_width': diagram.layout.canvas_width,
                'canvas_height': diagram.layout.canvas_height,
                'brick_count': len(diagram.layout.brick_positions)
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': str(e),
            'error_type': type(e).__name__
        })


@mcp.tool()
def validate_composition(composition_json: str) -> str:
    """
    Validate a brick composition before generating a diagram.
    
    Checks for common errors like:
    - Duplicate brick IDs
    - Invalid connections (referencing non-existent bricks)
    - Wrong number of layers (must be exactly 4)
    - Invalid layer names
    
    Args:
        composition_json: JSON string representing BrickComposition
        
    Returns:
        JSON string with validation results:
        - valid: Boolean indicating if composition is valid
        - errors: List of error messages (empty if valid)
        
    Cost: 0 tokens (pure validation logic)
    """
    try:
        from string_diagram_mcp.foundation import validate_composition as validate_comp
        
        composition_data = json.loads(composition_json)
        composition = _json_to_composition(composition_data)
        
        errors = validate_comp(composition)
        
        return json.dumps({
            'valid': len(errors) == 0,
            'errors': errors,
            'brick_count': len(composition.bricks),
            'connection_count': len(composition.connections)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'valid': False,
            'errors': [f'Parse error: {str(e)}'],
            'error_type': type(e).__name__
        })


# ============================================================================
# GENERIC COMPOSITION TOOLS
# ============================================================================

# Singleton generic renderer
_generic_renderer = GenericCompactRenderer()


@mcp.tool()
def generate_generic_diagram(
    composition_json: str,
    save_path: Optional[str] = None
) -> str:
    """
    Generate a string diagram from any category's composition.
    
    Accepts the universal GenericComposition schema — works with
    quantum circuits, workflow DAGs, arbitrary monoidal categories,
    or any graph of objects and morphisms.
    
    No domain assumptions. Visual hints are read from the optional
    'visual' field on nodes and edges.
    
    Args:
        composition_json: JSON string with:
            - nodes: List of {id, name, input_type?, output_type?, properties?, visual?, metadata?}
            - edges: List of {source, target, label?, visual?, metadata?}
            - metadata: {name?, category?, description?}
            
        Node visual options:
            color: hex fill color (default: #10b981)
            shape: circle | pill | diamond | square | point
            size: small | medium | large
            badge: text for top-right badge (e.g. "G1", "H", "π/4")
            badge_color: hex badge ring color
            glow: true for emphasis glow
            ring_colors: list of hex colors for arcs around node
            ring_weights: list of stroke widths for ring arcs
            
        Edge visual options:
            color: hex wire color
            style: solid | dashed | dotted
            weight: thickness multiplier (0.5 - 3.0)
            show_label: show label on wire (default: true)
            
        save_path: Optional path to save SVG file
        
    Returns:
        JSON string with svg, metadata, and layout_info
        
    Cost: 0 tokens (deterministic rendering)
    
    Example (bare minimum):
    {
        "nodes": [
            {"id": "a", "name": "Start"},
            {"id": "b", "name": "End"}
        ],
        "edges": [
            {"source": "a", "target": "b"}
        ]
    }
    
    Example (quantum circuit):
    {
        "nodes": [
            {"id": "h", "name": "H", "visual": {"color": "#f59e0b", "shape": "square", "badge": "H"}},
            {"id": "cx", "name": "CNOT", "visual": {"color": "#ef4444", "size": "large", "badge": "CX"}}
        ],
        "edges": [
            {"source": "h", "target": "cx", "label": "Qubit"}
        ],
        "metadata": {"name": "Bell State", "category": "quantum"}
    }
    """
    try:
        data = json.loads(composition_json)
        composition = parse_generic_composition(data)
        
        # Validate
        errors = validate_generic_composition(composition)
        if errors:
            return json.dumps({
                'error': f"Validation failed: {', '.join(errors)}",
                'errors': errors
            })
        
        # Render
        svg = _generic_renderer.render(composition)
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(svg)
        
        return json.dumps({
            'svg': svg,
            'metadata': {
                'name': composition.metadata.get('name', 'Composition'),
                'category': composition.metadata.get('category', 'generic'),
                'node_count': len(composition.nodes),
                'edge_count': len(composition.edges),
                'render_style': 'generic_compact',
            },
            'layout_info': {
                'node_count': len(composition.nodes),
                'edge_count': len(composition.edges),
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': str(e),
            'error_type': type(e).__name__
        })


@mcp.tool()
def generate_generic_sample(
    sample_type: str = "sequential",
    save_path: Optional[str] = None
) -> str:
    """
    Generate a sample generic string diagram for demonstration.
    
    Args:
        sample_type: Type of sample to generate
            - "sequential": Simple 3-node pipeline
            - "quantum": Bell state preparation circuit
            - "branching": Branching workflow with merge
        save_path: Optional path to save SVG file
        
    Returns:
        JSON string with SVG and metadata
        
    Cost: 0 tokens (deterministic)
    """
    try:
        samples = {
            'sequential': create_sample_generic_sequential,
            'quantum': create_sample_generic_quantum,
            'branching': create_sample_generic_branching,
        }
        
        factory = samples.get(sample_type)
        if not factory:
            return json.dumps({
                'error': f'Unknown sample type: {sample_type}',
                'valid_types': list(samples.keys())
            })
        
        composition = factory()
        svg = _generic_renderer.render(composition)
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(svg)
        
        return json.dumps({
            'svg': svg,
            'metadata': {
                'name': composition.metadata.get('name'),
                'category': composition.metadata.get('category'),
                'sample_type': sample_type,
                'node_count': len(composition.nodes),
                'edge_count': len(composition.edges),
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': str(e),
            'error_type': type(e).__name__
        })


@mcp.tool()
def generate_brick_diagram_generic(
    composition_json: str,
    save_path: Optional[str] = None
) -> str:
    """
    Generate a string diagram from a Lushy BrickComposition via the
    generic rendering pipeline.
    
    Same input format as generate_string_diagram, but routes through
    the brick→generic adapter and generic renderer. Produces the same
    compact visual style with automatic visual hint mapping from
    grades, layers, and token costs.
    
    Args:
        composition_json: JSON string in BrickComposition format
        save_path: Optional path to save SVG file
        
    Returns:
        JSON string with SVG and metadata
        
    Cost: 0 tokens (deterministic)
    """
    try:
        data = json.loads(composition_json)
        brick_composition = _json_to_composition(data)
        
        # Validate brick composition
        from string_diagram_mcp.foundation import validate_composition as validate_brick
        errors = validate_brick(brick_composition)
        if errors:
            return json.dumps({
                'error': f"Validation failed: {', '.join(errors)}",
                'errors': errors
            })
        
        # Adapt brick → generic
        generic_composition = brick_to_generic(brick_composition)
        
        # Render via generic pipeline
        svg = _generic_renderer.render(generic_composition)
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(svg)
        
        return json.dumps({
            'svg': svg,
            'metadata': {
                'name': generic_composition.metadata.get('name'),
                'category': 'lushy',
                'adapted_from': 'BrickComposition',
                'node_count': len(generic_composition.nodes),
                'edge_count': len(generic_composition.edges),
                'render_pipeline': 'brick → adapter → generic_renderer',
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': str(e),
            'error_type': type(e).__name__
        })


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _json_to_composition(data: dict) -> BrickComposition:
    """Convert JSON dict to BrickComposition object"""
    
    bricks = []
    for brick_data in data['bricks']:
        layers = [
            Layer(
                name=layer['name'],
                grade=layer['grade'],
                estimated_tokens=layer['estimated_tokens'],
                description=layer['description']
            )
            for layer in brick_data['layers']
        ]
        
        bricks.append(Brick(
            id=brick_data['id'],
            name=brick_data['name'],
            input_schema=brick_data['input_schema'],
            output_schema=brick_data['output_schema'],
            layers=layers,
            metadata=brick_data.get('metadata', {})
        ))
    
    connections = []
    for conn_data in data['connections']:
        connections.append(Connection(
            source_brick_id=conn_data['source_brick_id'],
            target_brick_id=conn_data['target_brick_id'],
            source_output=conn_data.get('source_output', 'output'),
            target_input=conn_data.get('target_input', 'input'),
            is_branching=conn_data.get('is_branching', False)
        ))
    
    return BrickComposition(
        bricks=bricks,
        connections=connections,
        metadata=data.get('metadata', {})
    )


# ============================================================================
# SERVER INFO
# ============================================================================

@mcp.tool()
def get_server_info() -> str:
    """
    Get information about the String Diagram Generator MCP server.
    
    Returns:
        JSON with server capabilities, version, and usage information
    """
    return json.dumps({
        'name': 'String Diagram Generator MCP Server',
        'version': '2.0.0',
        'description': 'Category-theoretic visualization of compositions — any category, any domain',
        'brick_type': 'meta-brick',
        'architecture': 'Four-layer (Foundation, Structure, Relational, Contextual)',
        'category_theory': 'Graded Traced Symmetric Monoidal Category over Kleisli(LLM)',
        'input_schemas': {
            'GenericComposition': 'Universal schema — nodes + edges with optional visual hints. Works with any category.',
            'BrickComposition': 'Lushy-specific schema — 4-layer bricks with grades and token costs. Adapted to generic via brick_to_generic().'
        },
        'render_styles': {
            'compact': 'ZX-style compact nodes with layer ring (default for brick tools)',
            'box': 'Original box-and-wire with internal layer structure',
            'generic_compact': 'Generic renderer reading visual hints from GenericComposition'
        },
        'node_shapes': ['circle', 'pill', 'diamond', 'square', 'point'],
        'cost': {
            'deterministic_mode': '0 tokens',
            'with_annotations': '~200 tokens',
            'typical_savings': '60-85% vs pure LLM'
        },
        'capabilities': [
            'Render any category as a string diagram (generic schema)',
            'Render Lushy brick compositions (brick schema)',
            'Five node shapes: circle, pill, diamond, square, point',
            'Visual hints: color, badge, glow, ring arcs, wire weight/style',
            'Automatic adaptation from Lushy bricks to generic schema',
            'Two brick render styles: compact (ZX) and box (original)',
            'Meta-diagram generation (diagram of itself)',
            'Cost analysis and optimization visualization',
            'Sample diagrams for demos (sequential, branching, quantum)'
        ],
        'available_tools': [
            'generate_generic_diagram',
            'generate_generic_sample',
            'generate_brick_diagram_generic',
            'generate_string_diagram',
            'generate_meta_diagram',
            'get_brick_layer_info',
            'create_sample_diagram',
            'validate_composition',
            'get_server_info'
        ],
        'repository': 'https://github.com/lushy/string-diagram-brick',
        'documentation': 'See STRING_DIAGRAM_README.md'
    }, indent=2)
