"""
Local execution entry point.

For FastMCP Cloud deployment, the entry point is server.py:mcp
which returns the server object without calling run().

For local execution:
    python -m string_diagram_mcp
"""

from server import mcp

if __name__ == "__main__":
    mcp.run()
