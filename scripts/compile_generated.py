"""Compile one accepted generated Java workflow against synthetic framework stubs."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_mcp.workflow import GenerationWorkflow, GraphCatalog  # noqa: E402

REQUEST = (
    "Create AcceptedGeneratedWorkflow as a Java test workflow in generated.tests "
    "backed by module accepted_generated and config testtables/AcceptedGenerated.toml "
    "for v1.0.0."
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compiler_command(
    java_files: list[Path],
    classes_dir: Path,
    ecj_jar: Path | None,
) -> tuple[list[str] | None, dict]:
    javac = shutil.which("javac")
    if javac:
        return (
            [
                javac,
                "-encoding",
                "UTF-8",
                "--release",
                "17",
                "-Xlint:all",
                "-Werror",
                "-d",
                str(classes_dir),
                *map(str, java_files),
            ],
            {"compiler": "javac", "executable": Path(javac).name},
        )
    java = shutil.which("java")
    if java and ecj_jar and ecj_jar.is_file():
        return (
            [
                java,
                "-jar",
                str(ecj_jar),
                "-encoding",
                "UTF-8",
                "-source",
                "1.8",
                "-target",
                "1.8",
                "-proc:none",
                "-d",
                str(classes_dir),
                *map(str, java_files),
            ],
            {
                "compiler": "eclipse-ecj",
                "executable": Path(java).name,
                "compiler_jar": ecj_jar.name,
                "compiler_jar_sha256": _sha256(ecj_jar),
            },
        )
    return None, {"compiler": "unavailable"}


def compile_generated(ecj_jar: Path | None = None) -> dict:
    catalog = GraphCatalog.from_path(ROOT / "fixtures" / "synthetic_graph.json")
    generated = GenerationWorkflow(catalog).run_text(REQUEST)
    if generated["status"] != "generated":
        raise RuntimeError("Accepted workflow did not pass generation validation")

    source = generated["source"]
    with tempfile.TemporaryDirectory(prefix="project10-java-") as temp_value:
        temp = Path(temp_value)
        source_root = temp / "src"
        classes_dir = temp / "classes"
        shutil.copytree(ROOT / "fixtures" / "java_framework" / "src", source_root)
        generated_path = source_root / "generated" / "tests" / "AcceptedGeneratedWorkflow.java"
        generated_path.parent.mkdir(parents=True, exist_ok=True)
        generated_path.write_text(source, encoding="utf-8")
        classes_dir.mkdir()
        java_files = sorted(source_root.rglob("*.java"))
        command, compiler = _compiler_command(java_files, classes_dir, ecj_jar)
        if command is None:
            return {
                "schema_version": "1.0",
                "status": "compiler_unavailable",
                "generated_source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                "source_file_count": len(java_files),
                **compiler,
            }

        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        class_files = sorted(classes_dir.rglob("*.class"))
        report = {
            "schema_version": "1.0",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "passed" if completed.returncode == 0 else "failed",
            "return_code": completed.returncode,
            "generated_source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "graph_fixture_sha256": catalog.fixture_hash,
            "source_file_count": len(java_files),
            "class_file_count": len(class_files),
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "environment": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
            },
            **compiler,
        }
        if completed.returncode != 0:
            raise RuntimeError(json.dumps(report, indent=2))
        return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ecj-jar", type=Path)
    parser.add_argument("--require-compiler", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evidence" / "java_compile.json",
    )
    args = parser.parse_args()
    report = compile_generated(args.ecj_jar)
    if report["status"] == "compiler_unavailable" and args.require_compiler:
        print(json.dumps(report, indent=2))
        return 2
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
