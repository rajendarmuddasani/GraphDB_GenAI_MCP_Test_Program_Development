"""Exercise the MCP protocol against a local command, including a container command."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


def _payload(result):
    if result.structuredContent:
        return result.structuredContent
    return json.loads(result.content[0].text)


async def smoke(command: str, command_args: list[str]) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    parameters = StdioServerParameters(
        command=command,
        args=command_args,
        cwd=ROOT,
        env=environment,
    )
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            if "generate_java_test_from_intent" not in names:
                raise RuntimeError("Expected MCP generation tool is not registered")
            result = await session.call_tool(
                "generate_java_test_from_intent",
                arguments={
                    "request": (
                        "Create ContainerSmokeWorkflow as a Java test workflow in "
                        "generated.tests backed by module container_smoke and config "
                        "testtables/ContainerSmoke.toml for v1.0.0."
                    )
                },
            )
            payload = _payload(result)
            if payload["status"] != "generated" or not payload["validation"]["valid"]:
                raise RuntimeError(json.dumps(payload, indent=2))
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "tool_count": len(names),
                        "groundedness": payload["validation"]["groundedness"],
                    },
                    indent=2,
                )
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    values = parser.parse_args()
    asyncio.run(smoke(values.command, values.args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
