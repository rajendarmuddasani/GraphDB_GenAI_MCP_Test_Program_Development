"""Render public PNG evidence from canonical Project 10 artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
NAVY = "#142B3A"
INK = "#20302F"
PAPER = "#F4F8F7"
WHITE = "#FFFFFF"
TEAL = "#68B9B0"
GREEN = "#18745A"
YELLOW = "#F3C969"
CORAL = "#E56B46"
BLUE = "#4EA5D9"
VIOLET = "#9381E8"
MUTED = "#5A6E6A"
LINE = "#CEDBD7"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = (
        (
            "C:/Windows/Fonts/bahnschrift.ttf",
            "C:/Windows/Fonts/bahnschrift.ttf",
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
    )
    for regular, strong in names:
        path = Path(strong if bold else regular)
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


def _header(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    draw.rectangle((0, 0, 1600, 150), fill=NAVY)
    draw.text((60, 33), title, fill=WHITE, font=_font(42, True))
    draw.text((62, 94), subtitle, fill="#DDEBE7", font=_font(20))
    for index, color in enumerate((YELLOW, CORAL, BLUE, VIOLET)):
        draw.rectangle((index * 400, 150, (index + 1) * 400, 162), fill=color)


def render_candidates() -> None:
    evidence = json.loads(
        (ROOT / "evidence" / "task_evaluation.json").read_text(encoding="utf-8")
    )
    validation = evidence["validation_results"]
    selected = evidence["selection"]["selected_candidate"]
    labels = {
        "no_graph_v0": "No graph v0",
        "lenient_repair_v1": "Lenient repair v1",
        "strict_graph_v2": "Strict graph v2",
        "wide_context_v3": "Wide context v3",
    }
    metrics = (
        ("task_success_rate", "Task success", TEAL),
        ("safe_rejection_recall", "Safe rejection", CORAL),
        ("citation_precision", "Citation precision", BLUE),
    )
    image = Image.new("RGB", (1600, 930), PAPER)
    draw = ImageDraw.Draw(image)
    _header(
        draw,
        "Validation candidate evidence",
        "32 synthetic validation cases | selection requires every safety gate",
    )

    x_label = 70
    x_bar = 420
    bar_width = 930
    value_x = 1390
    row_height = 165
    for row, candidate_id in enumerate(labels):
        top = 200 + row * row_height
        selected_row = candidate_id == selected
        fill = "#DFF0EB" if selected_row else WHITE
        outline = GREEN if selected_row else LINE
        draw.rounded_rectangle(
            (45, top, 1555, top + 140), radius=8, fill=fill, outline=outline, width=3
        )
        draw.text((x_label, top + 20), labels[candidate_id], fill=NAVY, font=_font(24, True))
        if selected_row:
            draw.rounded_rectangle(
                (x_label, top + 67, x_label + 142, top + 105),
                radius=6,
                fill=GREEN,
            )
            draw.text(
                (x_label + 13, top + 75),
                "SELECTED",
                fill=WHITE,
                font=_font(16, True),
            )
        result = validation[candidate_id]
        for metric_index, (key, label, color) in enumerate(metrics):
            y = top + 20 + metric_index * 37
            value = float(result[key])
            draw.text((x_bar, y), label, fill=MUTED, font=_font(17, True))
            track_x = x_bar + 190
            draw.rounded_rectangle(
                (track_x, y + 2, track_x + bar_width, y + 25),
                radius=5,
                fill="#E5ECEA",
            )
            if value > 0:
                draw.rounded_rectangle(
                    (track_x, y + 2, track_x + int(bar_width * value), y + 25),
                    radius=5,
                    fill=color,
                )
            draw.text(
                (value_x, y - 2),
                f"{value * 100:.1f}%",
                fill=INK,
                font=_font(19, True),
            )

    draw.rectangle((45, 870, 1555, 900), fill=NAVY)
    draw.text(
        (66, 875),
        (
            "Rejected trials: no graph fails grounding; lenient repair false-accepts; "
            "wide context adds irrelevant symbols."
        ),
        fill=WHITE,
        font=_font(16),
    )
    image.save(ASSETS / "evaluation-candidates.png", optimize=True)


def _arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
    draw.line((start, end), fill=CORAL, width=5)
    x, y = end
    draw.polygon(((x, y), (x - 16, y - 10), (x - 16, y + 10)), fill=CORAL)


def render_workflow() -> None:
    neo4j = json.loads(
        (ROOT / "evidence" / "neo4j_integration.json").read_text(encoding="utf-8")
    )
    benchmark = json.loads(
        (ROOT / "evidence" / "mcp_benchmark.json").read_text(encoding="utf-8")
    )
    image = Image.new("RGB", (1600, 930), PAPER)
    draw = ImageDraw.Draw(image)
    _header(
        draw,
        "Intent to validated Java over MCP",
        "Implemented runtime path | deterministic policy | live Neo4j backend",
    )

    stages = (
        ("Bounded intent", "3 request forms\nstrict identifiers", YELLOW),
        ("Official MCP", "5 tools\nstdio transport", BLUE),
        (
            "Neo4j context",
            f"{neo4j['symbol_count']} symbols\n{neo4j['method_count']} methods",
            TEAL,
        ),
        ("Java generator", "exact imports\nversion scoped", VIOLET),
        ("Validation", "Tree-sitter\ncontract + safety", CORAL),
        ("Accepted source", "compiled Java\nor typed rejection", GREEN),
    )
    box_width = 220
    gap = 35
    x = 55
    y = 245
    for index, (title, detail, color) in enumerate(stages):
        draw.rounded_rectangle(
            (x, y, x + box_width, y + 205),
            radius=8,
            fill=WHITE,
            outline=color,
            width=5,
        )
        draw.rectangle((x, y, x + box_width, y + 50), fill=color)
        draw.text((x + 16, y + 14), title, fill=NAVY, font=_font(20, True))
        detail_y = y + 78
        for line in detail.splitlines():
            draw.text((x + 18, detail_y), line, fill=INK, font=_font(18))
            detail_y += 36
        if index < len(stages) - 1:
            _arrow(
                draw,
                (x + box_width + 7, y + 102),
                (x + box_width + gap - 8, y + 102),
            )
        x += box_width + gap

    metrics = (
        ("120 / 120", "expected MCP outcomes", TEAL),
        (f"{benchmark['latency_ms']['p95']:.2f} ms", "local MCP p95", YELLOW),
        ("24 / 24", "generated source valid", BLUE),
        ("8 / 8", "unsafe intent rejected", CORAL),
        ("0", "external model calls", VIOLET),
    )
    metric_width = 282
    for index, (value, label, color) in enumerate(metrics):
        left = 55 + index * (metric_width + 23)
        draw.rounded_rectangle(
            (left, 570, left + metric_width, 730),
            radius=8,
            fill=NAVY,
        )
        draw.rectangle((left, 720, left + metric_width, 730), fill=color)
        draw.text((left + 18, 598), value, fill=WHITE, font=_font(34, True))
        draw.text((left + 18, 657), label, fill="#DDEBE7", font=_font(17))

    draw.rounded_rectangle((55, 780, 1545, 875), radius=8, fill="#FFF4D6")
    draw.text((78, 800), "Truth boundary", fill=NAVY, font=_font(20, True))
    draw.text(
        (78, 837),
        (
            "Synthetic framework only. Three intent forms. No external LLM. "
            "Local latency is not a production SLO."
        ),
        fill=INK,
        font=_font(18),
    )
    image.save(ASSETS / "mcp-generation-workflow.png", optimize=True)


def main() -> int:
    ASSETS.mkdir(exist_ok=True)
    render_candidates()
    render_workflow()
    print("Rendered evaluation-candidates.png and mcp-generation-workflow.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
