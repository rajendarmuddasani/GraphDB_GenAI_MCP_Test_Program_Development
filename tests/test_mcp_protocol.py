import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


def _payload(result):
    if result.structuredContent:
        return result.structuredContent
    return json.loads(result.content[0].text)


async def _exercise_server() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["GRAPH_BACKEND"] = os.getenv("MCP_TEST_GRAPH_BACKEND", "fixture")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "graph_mcp.server"],
        cwd=ROOT,
        env=environment,
    )

    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            assert names == {
                "generate_java_test",
                "generate_java_test_from_intent",
                "get_fixture_metadata",
                "search_graph",
                "validate_java_source",
            }

            result = await session.call_tool(
                "generate_java_test",
                arguments={
                    "class_name": "FrequencySweepWorkflow",
                    "package_name": "generated.tests",
                    "module_name": "frequency_sweep",
                    "config_path": "testtables/FrequencySweep.toml",
                    "version": "v1.0.0",
                },
            )
            assert result.isError is not True
            payload = _payload(result)
            assert payload["status"] == "generated"
            assert payload["validation"]["groundedness"] == 1.0

            rejected = await session.call_tool(
                "generate_java_test",
                arguments={
                    "class_name": "UnsafeWorkflow",
                    "package_name": "generated.tests",
                    "module_name": "unsafe",
                    "config_path": "../../private.toml",
                    "version": "v1.0.0",
                },
            )
            rejected_payload = _payload(rejected)
            assert rejected_payload["status"] == "rejected"
            assert rejected_payload["error"]["code"] == "unsafe_config_path"


def test_official_mcp_stdio_round_trip():
    asyncio.run(_exercise_server())
