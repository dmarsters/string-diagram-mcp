# String Diagram Generator MCP Server

**Category-theoretic visualization of Lushy brick compositions**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io)

## Overview

The String Diagram Generator is a **meta-brick** MCP server that generates formal string diagram visualizations of Lushy workflow compositions. It demonstrates category theory foundations through recursive self-documentation capability.

### Key Features

- 🎨 **Zero-cost diagram generation** (0 tokens in deterministic mode)
- 🔄 **Recursive capability** (can diagram itself!)
- 📊 **Cost analysis** (visualize token usage across layers)
- ✅ **Validation** (catch composition errors before generation)
- 🎯 **Production-ready** (full test suite, comprehensive docs)

### Category Theory Foundation

**Graded Traced Symmetric Monoidal Category over Kleisli(LLM)**

- **Traced:** Feedback loops for versioning and validation
- **Graded:** Cost tracking (Grade 0 = free, Grade 1 = LLM, Grade 2 = human)
- **Symmetric Monoidal:** Sequential (∘) and parallel (⊗) composition
- **Over Kleisli(LLM):** Probabilistic composition with reproducibility bounds

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/lushy/string-diagram-mcp.git
cd string-diagram-mcp

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
./tests/run_tests.sh
```

### Usage as MCP Server

```bash
# Run locally
python src/string_diagram_mcp/server.py

# Or configure in Claude Desktop
# Add to claude_desktop_config.json:
{
  "mcpServers": {
    "string-diagram-generator": {
      "command": "python",
      "args": ["/path/to/string-diagram-mcp/src/string_diagram_mcp/server.py"]
    }
  }
}
```

## MCP Tools

### 1. `generate_string_diagram`
Generate a string diagram from brick composition (0 tokens)

### 2. `generate_meta_diagram`
Generate diagram of the generator itself (0 tokens)

### 3. `get_brick_layer_info`
Get four-layer architecture details (0 tokens)

### 4. `create_sample_diagram`
Generate sample diagrams for demos (0 tokens)

### 5. `validate_composition`
Validate brick compositions (0 tokens)

### 6. `get_server_info`
Get server metadata (0 tokens)

## Architecture

### Four-Layer Structure

```
┌─────────────────────────────────┐
│ Layer 4: Contextual (Grade 0/1)│  SVG rendering + cost analysis
├─────────────────────────────────┤
│ Layer 3: Relational (Grade 0)  │  Wire routing & crossing detection
├─────────────────────────────────┤
│ Layer 2: Structure (Grade 0)   │  Topological layout computation
├─────────────────────────────────┤
│ Layer 1: Foundation (Grade 0)  │  Primitives & validation
└─────────────────────────────────┘
```

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage documentation
- **[API Reference](docs/API_REFERENCE.md)** - Tool specifications
- **[Architecture](docs/ARCHITECTURE.md)** - Technical deep-dive
- **[Examples](examples/)** - Sample workflows and outputs

## Development

```bash
# Run tests with coverage
pytest --cov=string_diagram_mcp

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check (if you add type hints)
mypy src/
```

## Cost Analysis

**Typical Workflow Savings:**
- 3-brick workflow: 75% savings (450 vs 1800 tokens)
- 5-brick workflow: 80% savings (800 vs 4000 tokens)

**String Diagram Generator itself:**
- Deterministic mode: **0 tokens**
- With LLM annotations: ~200 tokens

## License

MIT License - see [LICENSE](LICENSE) file

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md)

## Support

- Issues: [GitHub Issues](https://github.com/lushy/string-diagram-mcp/issues)
- Discussions: [GitHub Discussions](https://github.com/lushy/string-diagram-mcp/discussions)
- Email: support@lushy.ai
