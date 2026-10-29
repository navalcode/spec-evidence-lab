"""Exercise the actual stdio protocol using the official MCP client."""

import asyncio
import json
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "spec_evidence.mcp_server"], cwd=str(ROOT))
    spec = (ROOT / "examples/offline_catalog/spec.json").read_text()
    junit = (ROOT / "artifacts/demo.xml").read_text()
    plan = json.loads((ROOT / "examples/offline_catalog/proposal.json").read_text())
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            tools = await client.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == {"check_acceptance", "review_ai_proposal"}, names
            assert all(tool.output_schema and tool.annotations.read_only_hint for tool in tools.tools)
            accepted = await client.call_tool("check_acceptance", {"spec_json": spec, "junit_xml": junit})
            assert not accepted.is_error
            result = accepted.structured_content
            assert result["status"] == "passed" and result["meaning_review_required"]
            ready = await client.call_tool("review_ai_proposal", {"spec_json": spec, "proposal_json": json.dumps(plan)})
            assert not ready.is_error and ready.structured_content["status"] == "ready_for_human_review"
            plan["spec_sha256"] = "0" * 64
            stale = await client.call_tool("review_ai_proposal", {"spec_json": spec, "proposal_json": json.dumps(plan)})
            assert not stale.is_error and stale.structured_content["status"] == "needs_revision"
            invalid = await client.call_tool("check_acceptance", {"spec_json": "{}", "junit_xml": junit})
            assert invalid.is_error
            assert "missing required fields" in invalid.content[0].text
    print(json.dumps({"transport": "stdio", "tools": sorted(names), "checks": {
        "valid_acceptance": "passed", "valid_proposal": "ready_for_human_review",
        "stale_proposal": "needs_revision", "invalid_contract": "tool_error"}}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
