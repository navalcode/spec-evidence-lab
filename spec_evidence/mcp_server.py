"""Optional stdio MCP adapter. Inputs are contents, never filesystem paths."""

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from typing import Any
from .contracts import ContractError, load_json
from .evidence import check_results
from .proposals import review_proposal

server = MCPServer("Spec Evidence Lab")
read_only = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)


@server.tool(annotations=read_only, structured_output=True)
def check_acceptance(spec_json: str, junit_xml: str) -> dict[str, Any]:
    """Relate a feature contract to supplied JUnit results. Requires meaning/provenance review."""
    try:
        return check_results(load_json(spec_json), junit_xml)
    except ContractError as error:
        raise ToolError(str(error)) from None


@server.tool(annotations=read_only, structured_output=True)
def review_ai_proposal(spec_json: str, proposal_json: str) -> dict[str, Any]:
    """Check a proposal against the current specification. Never executes or approves changes."""
    try:
        return review_proposal(load_json(spec_json), load_json(proposal_json))
    except ContractError as error:
        raise ToolError(str(error)) from None


if __name__ == "__main__":
    server.run(transport="stdio")
