"""Benchmark warm official-MCP stdio calls against the bounded workflow."""

from __future__ import annotations

import asyncio
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence" / "mcp_benchmark.json"


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * fraction)]


def _request(index: int, unsafe: bool = False) -> str:
    config_path = "../private.toml" if unsafe else f"testtables/McpLoad{index}.toml"
    return (
        f"Create McpLoad{index}Workflow as a Java test workflow in generated.tests "
        f"backed by module mcp_load_{index} and config {config_path} for v1.0.0."
    )


def _payload(result):
    if result.structuredContent:
        return result.structuredContent
    return json.loads(result.content[0].text)


async def benchmark(request_count: int = 120, warmup_count: int = 10) -> dict:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    backend = environment.get("GRAPH_BACKEND", "fixture").casefold()
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "graph_mcp.server"],
        cwd=ROOT,
        env=environment,
    )

    launched = perf_counter_ns()
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            startup_ms = (perf_counter_ns() - launched) / 1_000_000
            tools = await session.list_tools()
            tool_names = sorted(tool.name for tool in tools.tools)

            for index in range(warmup_count):
                await session.call_tool(
                    "generate_java_test_from_intent",
                    arguments={"request": _request(index)},
                )

            latencies_ms = []
            successes = 0
            protocol_errors = 0
            supported_count = 0
            adversarial_count = 0
            observed_statuses: dict[str, int] = {}
            for index in range(request_count):
                unsafe = index % 4 == 3
                expected_status = "rejected" if unsafe else "generated"
                supported_count += int(not unsafe)
                adversarial_count += int(unsafe)
                started = perf_counter_ns()
                result = await session.call_tool(
                    "generate_java_test_from_intent",
                    arguments={"request": _request(index + warmup_count, unsafe)},
                )
                latencies_ms.append((perf_counter_ns() - started) / 1_000_000)
                protocol_errors += int(result.isError is True)
                payload = _payload(result)
                observed = payload.get("status", "missing")
                observed_statuses[observed] = observed_statuses.get(observed, 0) + 1
                success = observed == expected_status
                if unsafe:
                    success = (
                        success and payload.get("error", {}).get("code") == "unsafe_config_path"
                    )
                else:
                    success = (
                        success
                        and payload.get("validation", {}).get("valid") is True
                    )
                successes += int(success)

    if successes != request_count or protocol_errors:
        raise RuntimeError(
            f"MCP benchmark failed: {successes}/{request_count} tasks, "
            f"{protocol_errors} protocol errors"
        )

    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "transport": "official MCP stdio",
        "backend": backend,
        "concurrency": 1,
        "warmup_count": warmup_count,
        "request_count": request_count,
        "supported_request_count": supported_count,
        "adversarial_request_count": adversarial_count,
        "task_success_count": successes,
        "task_success_rate": round(successes / request_count, 6),
        "protocol_error_count": protocol_errors,
        "observed_statuses": dict(sorted(observed_statuses.items())),
        "latency_ms": {
            "p50": round(_percentile(latencies_ms, 0.50), 6),
            "p95": round(_percentile(latencies_ms, 0.95), 6),
            "p99": round(_percentile(latencies_ms, 0.99), 6),
            "max": round(max(latencies_ms), 6),
        },
        "startup_ms": round(startup_ms, 6),
        "tool_count": len(tool_names),
        "tools": tool_names,
        "external_model_calls": 0,
        "external_model_cost_usd": 0.0,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "scope": "single-process local sequential benchmark; not a production SLO",
        },
        "command": "python scripts/benchmark_mcp.py",
    }


def main() -> int:
    result = asyncio.run(benchmark())
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
