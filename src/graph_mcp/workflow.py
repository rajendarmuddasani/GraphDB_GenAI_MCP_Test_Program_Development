"""Constrained intent-to-Java generation backed by synthetic graph metadata."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import tree_sitter_java
from tree_sitter import Language, Parser

IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
CLASS_NAME = re.compile(r"^[A-Z][A-Za-z0-9]{0,63}$")
PACKAGE_NAME = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){1,5}$")
CONFIG_PATH = re.compile(r"^[A-Za-z0-9_./-]{1,160}\.toml$")
IMPORT_PATTERN = re.compile(r"^import\s+(synthetic\.framework\.[A-Za-z0-9_.]+);$", re.MULTILINE)

REQUIRED_SYMBOLS = (
    "BaseTestMethod",
    "ConfigBlock",
    "ConfigLoader",
    "LevelChangeAction",
    "TestCaseBase",
    "TestList",
    "TestListManager",
)

FORBIDDEN_SOURCE_PATTERNS = {
    "process_execution": re.compile(r"Runtime\s*\.\s*getRuntime|ProcessBuilder"),
    "process_exit": re.compile(r"System\s*\.\s*exit"),
    "filesystem_access": re.compile(r"java\.io\.|java\.nio\.file|\bFiles\."),
    "network_access": re.compile(r"java\.net\."),
    "native_code": re.compile(r"\bnative\s+"),
}

INTENT_PATTERNS = (
    re.compile(
        r"^Generate a configuration-driven Java test method named "
        r"(?P<class_name>\S+) in package (?P<package_name>\S+) for module "
        r"(?P<module_name>\S+) using (?P<config_path>\S+) on framework "
        r"(?P<version>v\d+\.\d+\.\d+)\.?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^Create (?P<class_name>\S+) as a Java test workflow in "
        r"(?P<package_name>\S+) backed by module (?P<module_name>\S+) and config "
        r"(?P<config_path>\S+) for (?P<version>v\d+\.\d+\.\d+)\.?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^For framework (?P<version>v\d+\.\d+\.\d+), generate class "
        r"(?P<class_name>\S+) under package (?P<package_name>\S+) from module "
        r"(?P<module_name>\S+) and config (?P<config_path>\S+)\.?$",
        re.IGNORECASE,
    ),
)


class WorkflowRejection(ValueError):
    """A fail-closed rejection with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class GraphSymbol:
    """One versioned symbol in the synthetic framework catalog."""

    name: str
    qualified_name: str
    kind: str
    methods: tuple[str, ...]


class GraphCatalog:
    """Read-only symbol catalog loaded from a provenance-labelled JSON fixture."""

    def __init__(
        self,
        fixture_id: str,
        version: str,
        provenance: str,
        license_name: str,
        fixture_hash: str,
        symbols: tuple[GraphSymbol, ...],
    ) -> None:
        self.fixture_id = fixture_id
        self.version = version
        self.provenance = provenance
        self.license = license_name
        self.fixture_hash = fixture_hash
        self._symbols = {symbol.name: symbol for symbol in symbols}

    @classmethod
    def from_path(cls, path: str | Path) -> "GraphCatalog":
        fixture_path = Path(path).resolve()
        fixture_bytes = fixture_path.read_bytes()
        payload = json.loads(fixture_bytes.decode("utf-8"))
        symbols = tuple(
            GraphSymbol(
                name=item["name"],
                qualified_name=item["qualified_name"],
                kind=item["kind"],
                methods=tuple(item["methods"]),
            )
            for item in payload["symbols"]
        )
        if len({symbol.qualified_name for symbol in symbols}) != len(symbols):
            raise ValueError("Graph fixture contains duplicate qualified symbols")
        return cls(
            fixture_id=payload["fixture_id"],
            version=payload["version"],
            provenance=payload["provenance"],
            license_name=payload["license"],
            fixture_hash=hashlib.sha256(fixture_bytes).hexdigest(),
            symbols=symbols,
        )

    @property
    def symbols(self) -> tuple[GraphSymbol, ...]:
        """Return the immutable symbols used for graph materialization."""
        return tuple(self._symbols.values())

    def get(self, name: str, version: str) -> GraphSymbol:
        if version != self.version:
            raise WorkflowRejection(
                "unsupported_version",
                f"Version {version!r} is not present in the graph fixture",
            )
        try:
            return self._symbols[name]
        except KeyError as exc:
            raise WorkflowRejection(
                "missing_graph_context",
                f"Required symbol {name!r} is not present in the graph fixture",
            ) from exc

    def search(self, query: str, version: str, limit: int = 8) -> list[dict[str, Any]]:
        if not query or len(query) > 80:
            raise WorkflowRejection("invalid_query", "Query must contain 1-80 characters")
        if not 1 <= limit <= 20:
            raise WorkflowRejection("invalid_limit", "Limit must be between 1 and 20")
        if version != self.version:
            raise WorkflowRejection(
                "unsupported_version",
                f"Version {version!r} is not present in the graph fixture",
            )
        needle = query.casefold()
        matches = [
            symbol
            for symbol in self._symbols.values()
            if needle in symbol.name.casefold()
            or needle in symbol.qualified_name.casefold()
            or any(needle in method.casefold() for method in symbol.methods)
        ]
        return [asdict(symbol) for symbol in sorted(matches, key=lambda item: item.name)[:limit]]


@dataclass(frozen=True)
class GenerationIntent:
    """Validated fields accepted by the deterministic generation policy."""

    class_name: str
    package_name: str
    module_name: str
    config_path: str
    version: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "GenerationIntent":
        allowed = {
            "class_name",
            "package_name",
            "module_name",
            "config_path",
            "version",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise WorkflowRejection(
                "unknown_fields", f"Unsupported intent fields: {', '.join(unknown)}"
            )

        required = sorted(allowed - set(value))
        if required:
            raise WorkflowRejection(
                "missing_fields", f"Missing intent fields: {', '.join(required)}"
            )

        fields = {name: value[name] for name in allowed}
        if not all(isinstance(field, str) for field in fields.values()):
            raise WorkflowRejection("invalid_type", "All intent fields must be strings")
        if not CLASS_NAME.fullmatch(fields["class_name"]):
            raise WorkflowRejection("invalid_class_name", "Class name is not allowed")
        if not PACKAGE_NAME.fullmatch(fields["package_name"]):
            raise WorkflowRejection("invalid_package_name", "Package name is not allowed")
        if not IDENTIFIER.fullmatch(fields["module_name"]):
            raise WorkflowRejection("invalid_module_name", "Module name is not allowed")
        if not CONFIG_PATH.fullmatch(fields["config_path"]):
            raise WorkflowRejection("invalid_config_path", "Config path is not allowed")

        config_path = PurePosixPath(fields["config_path"])
        if config_path.is_absolute() or ".." in config_path.parts:
            raise WorkflowRejection(
                "unsafe_config_path", "Config path must remain inside the project"
            )
        return cls(**fields)

    @classmethod
    def from_text(cls, request: str) -> "GenerationIntent":
        """Parse one of three explicit natural-language request forms."""
        if not isinstance(request, str) or not 20 <= len(request) <= 500:
            raise WorkflowRejection(
                "invalid_intent_length", "Intent must contain 20-500 characters"
            )
        if "\n" in request or "\r" in request or "\x00" in request:
            raise WorkflowRejection(
                "invalid_intent_control_character",
                "Intent must be a single non-binary line",
            )
        for pattern in INTENT_PATTERNS:
            match = pattern.fullmatch(request.strip())
            if match:
                return cls.from_mapping(match.groupdict())
        raise WorkflowRejection(
            "unrecognized_intent",
            "Intent does not match a supported configuration-driven workflow form",
        )


@dataclass(frozen=True)
class ValidationReport:
    """Syntax, contract, grounding, and security results for generated source."""

    valid: bool
    syntax_valid: bool
    contract_valid: bool
    security_valid: bool
    groundedness: float
    grounded_symbols: tuple[str, ...]
    ungrounded_symbols: tuple[str, ...]
    issues: tuple[str, ...]


class JavaValidator:
    """Parse Java and enforce the bounded synthetic framework contract."""

    def __init__(self) -> None:
        self._parser = Parser(Language(tree_sitter_java.language()))

    def validate(
        self,
        source: str,
        intent: GenerationIntent,
        citations: tuple[GraphSymbol, ...],
    ) -> ValidationReport:
        issues: list[str] = []
        root = self._parser.parse(source.encode("utf-8")).root_node
        syntax_valid = not root.has_error
        if not syntax_valid:
            issues.append("java_syntax_error")

        expected_contract = (
            f"package {intent.package_name};",
            f"public class {intent.class_name} extends BaseTestMethod",
            "protected void defineTestSequences(TestListManager testListManager)",
            "ConfigLoader.load(",
            f'"{intent.module_name}.ConditionsAndGradeables"',
        )
        missing_contract = [item for item in expected_contract if item not in source]
        contract_valid = not missing_contract
        issues.extend(f"missing_contract:{item}" for item in missing_contract)

        security_findings = [
            name for name, pattern in FORBIDDEN_SOURCE_PATTERNS.items() if pattern.search(source)
        ]
        security_valid = not security_findings
        issues.extend(f"forbidden_source:{name}" for name in security_findings)

        imported_symbols = set(IMPORT_PATTERN.findall(source))
        cited_symbols = {citation.qualified_name for citation in citations}
        grounded = imported_symbols & cited_symbols
        ungrounded = imported_symbols - cited_symbols
        groundedness = len(grounded) / len(imported_symbols) if imported_symbols else 0.0
        if ungrounded:
            issues.append("ungrounded_import")
        if groundedness < 1.0:
            issues.append("incomplete_grounding")

        valid = syntax_valid and contract_valid and security_valid and groundedness == 1.0
        return ValidationReport(
            valid=valid,
            syntax_valid=syntax_valid,
            contract_valid=contract_valid,
            security_valid=security_valid,
            groundedness=groundedness,
            grounded_symbols=tuple(sorted(grounded)),
            ungrounded_symbols=tuple(sorted(ungrounded)),
            issues=tuple(issues),
        )


class GenerationWorkflow:
    """Generate bounded Java source and validate it before returning success."""

    def __init__(self, catalog: GraphCatalog, validator: JavaValidator | None = None):
        self.catalog = catalog
        self.validator = validator or JavaValidator()

    def run(self, raw_intent: Mapping[str, Any]) -> dict[str, Any]:
        try:
            intent = GenerationIntent.from_mapping(raw_intent)
            return self._run_validated_intent(intent)
        except WorkflowRejection as exc:
            return self._rejection(exc)

    def run_text(self, request: str) -> dict[str, Any]:
        """Parse a bounded natural-language intent and run the generation policy."""
        try:
            intent = GenerationIntent.from_text(request)
            return self._run_validated_intent(intent)
        except WorkflowRejection as exc:
            return self._rejection(exc)

    def _run_validated_intent(self, intent: GenerationIntent) -> dict[str, Any]:
        try:
            citations = tuple(self.catalog.get(name, intent.version) for name in REQUIRED_SYMBOLS)
            source = self._render(intent, citations)
            validation = self.validator.validate(source, intent, citations)
            if not validation.valid:
                return {
                    "status": "validation_failed",
                    "source": None,
                    "citations": [asdict(item) for item in citations],
                    "validation": asdict(validation),
                    "error": {"code": "generated_source_rejected"},
                }
            return {
                "status": "generated",
                "source": source,
                "citations": [asdict(item) for item in citations],
                "validation": asdict(validation),
                "error": None,
            }
        except WorkflowRejection as exc:
            return self._rejection(exc)

    @staticmethod
    def _rejection(exc: WorkflowRejection) -> dict[str, Any]:
        return {
            "status": "rejected",
            "source": None,
            "citations": [],
            "validation": None,
            "error": {"code": exc.code, "message": str(exc)},
        }

    @staticmethod
    def _render(intent: GenerationIntent, citations: tuple[GraphSymbol, ...]) -> str:
        imports = "\n".join(f"import {citation.qualified_name};" for citation in citations)
        workflow_name = f"{intent.module_name}_workflow"
        return f"""package {intent.package_name};

{imports}
import java.util.List;

public class {intent.class_name} extends BaseTestMethod {{
  @Override
  protected void defineTestSequences(TestListManager testListManager) {{
    String paramFile = "{intent.config_path}";
    ConfigBlock config = ConfigLoader.load(
        paramFile,
        "{intent.module_name}.ConditionsAndGradeables"
    );
    String endCondition = config.getString("endCondition");
    String[] testConditions = config.getStringArray("testConditions");
    String[] groupNames = config.getStringArray("gradeableLists");
    TestList testList = testListManager.create("{workflow_name}");

    for (int index = 0; index < testConditions.length; index++) {{
      String condition = testConditions[index];
      testList.setupBegin(condition)
          .addAction(LevelChangeAction.class, "Begin_" + condition)
          .setLevel(condition);

      List<String> entries = config.getStringList(groupNames[index]);
      for (String entry : entries) {{
        String path = "{intent.module_name}." + entry;
        ConfigBlock testCaseConfig = ConfigLoader.load(paramFile, path);
        String testCaseType = testCaseConfig.getString("testCase");
        TestCaseBase testCase = testList.addTestCase(testCaseType, paramFile, path);
        testCase.defineTestSequence();
      }}

      testList.setupEnd(condition)
          .addAction(LevelChangeAction.class, "End_" + condition)
          .setLevel(endCondition);
    }}
  }}
}}
"""
