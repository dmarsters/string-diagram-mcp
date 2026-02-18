"""
String Diagram Generator Brick - Complete Implementation
=========================================================

Integrates all four layers into a complete meta-brick that generates
string diagrams for other Lushy brick compositions.

Architecture:
- Layer 1: Foundation (primitives, data structures) - Grade 0
- Layer 2: Structure (layout computation) - Grade 0
- Layer 3: Relational (wire routing) - Grade 0  
- Layer 4: Contextual (cost analysis, SVG rendering) - Grade 0/1

Render styles:
- 'box': Original box-and-wire with internal layer structure
- 'compact': ZX-style compact nodes with layer ring

Total cost: 0 tokens (deterministic) or ~200 tokens (with LLM annotations)
"""

from typing import Optional, Literal
from datetime import datetime

from .foundation import (
    BrickComposition, StringDiagram, DiagramPrimitives,
    validate_composition, Annotation
)
from .structure import LayoutComputer
from .relational import WireRouter
from .contextual import CostAnalyzer, SVGRenderer, CompactSVGRenderer


# Valid render style values
RenderStyle = Literal['box', 'compact']


class StringDiagramBrick:
    """
    Complete String Diagram Generator Brick
    
    A meta-brick that generates formal string diagram visualizations
    of Lushy brick compositions. Demonstrates Lushy's compositional
    architecture by being itself a four-layer brick.
    
    Four-layer structure:
    1. Foundation: Diagram primitives and constraints
    2. Structure: Topological layout computation
    3. Relational: Wire routing and cost calculation
    4. Contextual: Cost analysis and SVG rendering
    
    Render styles:
    - 'box': Tall annotated rectangles showing internal layer structure
    - 'compact': ZX-style compact nodes with topology-focused layout
    
    Cost: ~0 tokens (all layers deterministic except optional LLM annotations)
    """
    
    def __init__(
        self,
        render_style: RenderStyle = 'compact',
        llm_client: Optional[object] = None
    ):
        """
        Initialize the String Diagram Generator Brick
        
        Args:
            render_style: 'box' for original style, 'compact' for ZX-style
            llm_client: Optional LLM client for generating annotations
                       If None, operates in fully deterministic mode (0 tokens)
        """
        # Layer 1: Foundation - Load primitives
        self.primitives = DiagramPrimitives.load_defaults()
        
        # Layer 2: Structure - Layout computer
        self.layout_computer = LayoutComputer(self.primitives)
        
        # Layer 3: Relational - Wire router
        self.wire_router = WireRouter(self.primitives)
        
        # Layer 4: Contextual - Cost analyzer and renderer
        self.cost_analyzer = CostAnalyzer()
        self._set_renderer(render_style)
        
        # Optional LLM for annotations
        self.llm_client = llm_client
    
    def _set_renderer(self, render_style: RenderStyle):
        """Set the active renderer based on style choice."""
        self.render_style = render_style
        if render_style == 'compact':
            self.renderer = CompactSVGRenderer(self.primitives)
        else:
            self.renderer = SVGRenderer(self.primitives)
    
    def set_render_style(self, render_style: RenderStyle):
        """
        Switch render style at runtime.
        
        Args:
            render_style: 'box' or 'compact'
        """
        self._set_renderer(render_style)
    
    def generate(
        self,
        composition: BrickComposition,
        include_annotations: bool = False,
        validate: bool = True,
        render_style: Optional[RenderStyle] = None
    ) -> StringDiagram:
        """
        Generate string diagram from brick composition
        
        This is the main entry point that orchestrates all four layers.
        
        Cost breakdown:
        - Layer 1 (Foundation): 0 tokens - primitives already loaded
        - Layer 2 (Structure): 0 tokens - pure graph algorithms
        - Layer 3 (Relational): 0 tokens - pure geometry
        - Layer 4 (Contextual): 0 tokens base + ~200 if include_annotations
        
        Args:
            composition: The brick composition to visualize
            include_annotations: Generate LLM annotations (costs ~200 tokens)
            validate: Validate composition before processing
            render_style: Override instance render style for this call only.
                         None uses the instance default.
            
        Returns:
            StringDiagram with SVG and complete metadata
            
        Raises:
            ValueError: If composition is invalid
        """
        # Validate composition
        if validate:
            errors = validate_composition(composition)
            if errors:
                raise ValueError(f"Invalid composition: {', '.join(errors)}")
        
        # Select renderer (per-call override or instance default)
        if render_style is not None:
            if render_style == 'compact':
                renderer = CompactSVGRenderer(self.primitives)
            else:
                renderer = SVGRenderer(self.primitives)
        else:
            renderer = self.renderer
        
        # Layer 2: Structure - Compute spatial layout
        layout = self.layout_computer.compute_layout(composition)
        
        # Layer 3: Relational - Route wires between bricks
        routing = self.wire_router.route_wires(layout, composition)
        
        # Layer 4: Contextual - Analyze costs and generate SVG
        cost_summary = self.cost_analyzer.compute_cost_summary(composition, routing)
        
        # Generate annotations if requested (LLM optional)
        annotations = []
        if include_annotations and self.llm_client:
            annotations = self._generate_annotations_with_llm(
                layout, routing, cost_summary, composition
            )
        
        # Render to SVG using selected renderer
        svg = renderer.render(
            layout, routing, cost_summary, composition, annotations
        )
        
        # Determine effective style
        effective_style = render_style if render_style is not None else self.render_style
        
        # Return complete diagram
        return StringDiagram(
            svg=svg,
            layout=layout,
            routing=routing,
            annotations=annotations,
            cost_summary=cost_summary,
            metadata={
                'generated_at': datetime.now().isoformat(),
                'generator_version': '1.1.0',
                'render_style': effective_style,
                'included_annotations': include_annotations,
                'layers_depth': layout.layers_depth,
                'brick_count': len(composition.bricks),
                'connection_count': len(composition.connections),
                'wire_crossings': routing.total_crossings
            }
        )
    
    def _generate_annotations_with_llm(
        self,
        layout,
        routing,
        cost_summary,
        composition
    ) -> list[Annotation]:
        """
        Generate annotations using LLM (Grade 1 operation)
        
        Cost: ~200 tokens
        
        This is the only part that uses LLM. If llm_client is None,
        the brick operates in fully deterministic mode at 0 tokens.
        """
        # Placeholder for LLM integration
        return []
    
    def generate_meta_diagram(
        self,
        render_style: Optional[RenderStyle] = None
    ) -> StringDiagram:
        """
        Generate a string diagram of the String Diagram Generator itself!
        
        This demonstrates the recursive beauty of the meta-brick.
        The diagram generator can diagram its own structure.
        
        Args:
            render_style: Override render style for this call
        
        Returns:
            StringDiagram showing the four-layer structure of this brick
        """
        from .foundation import Brick, Layer, BrickComposition
        
        meta_composition = BrickComposition(
            bricks=[
                Brick(
                    id="string_diagram_generator",
                    name="String Diagram Generator",
                    input_schema="BrickComposition",
                    output_schema="StringDiagram",
                    layers=[
                        Layer(
                            "foundation",
                            grade=0,
                            estimated_tokens=0,
                            description="Diagram primitives & constraints"
                        ),
                        Layer(
                            "structure",
                            grade=0,
                            estimated_tokens=0,
                            description="Topological layout computation"
                        ),
                        Layer(
                            "relational",
                            grade=0,
                            estimated_tokens=0,
                            description="Wire routing & cost calculation"
                        ),
                        Layer(
                            "contextual",
                            grade=1,
                            estimated_tokens=200,
                            description="Cost analysis & SVG rendering"
                        )
                    ],
                    metadata={}
                )
            ],
            connections=[],
            metadata={
                "name": "String Diagram Generator (Meta-Brick)",
                "description": "A meta-brick that generates diagrams of other bricks"
            }
        )
        
        return self.generate(
            meta_composition,
            validate=False,
            render_style=render_style
        )
    
    def get_layer_info(self) -> dict:
        """
        Get information about this brick's layers
        
        Returns:
            Dictionary describing the four-layer structure
        """
        return {
            "brick_name": "String Diagram Generator",
            "brick_type": "meta-brick",
            "total_layers": 4,
            "render_styles": {
                "box": "Tall annotated rectangles with internal layer structure",
                "compact": "ZX-style compact nodes with layer ring and topology focus"
            },
            "current_style": self.render_style,
            "layers": [
                {
                    "name": "foundation",
                    "grade": 0,
                    "cost": 0,
                    "description": "Diagram primitives, colors, constraints (immutable taxonomy)"
                },
                {
                    "name": "structure", 
                    "grade": 0,
                    "cost": 0,
                    "description": "Topological sorting and spatial layout (graph algorithms)"
                },
                {
                    "name": "relational",
                    "grade": 0,
                    "cost": 0,
                    "description": "Wire routing with Bezier curves (pure geometry)"
                },
                {
                    "name": "contextual",
                    "grade": "0/1",
                    "cost": "0 or ~200 tokens",
                    "description": "Cost analysis (deterministic) + optional LLM annotations"
                }
            ],
            "cost_deterministic": 0,
            "cost_with_llm": 200,
            "savings_vs_pure_llm": "~87%"
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_string_diagram(
    composition: BrickComposition,
    render_style: RenderStyle = 'compact',
    save_path: Optional[str] = None
) -> StringDiagram:
    """
    Convenience function to generate a string diagram
    
    Args:
        composition: Brick composition to visualize
        render_style: 'box' or 'compact'
        save_path: Optional path to save SVG file
        
    Returns:
        StringDiagram object
    """
    brick = StringDiagramBrick(render_style=render_style)
    diagram = brick.generate(composition)
    
    if save_path:
        with open(save_path, 'w') as f:
            f.write(diagram.svg)
    
    return diagram
