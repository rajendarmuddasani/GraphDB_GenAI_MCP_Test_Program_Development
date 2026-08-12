FROM cgr.dev/chainguard/python:latest-dev@sha256:b08980b41611a3887dfca3823286a84b2b8557c70ec7f151265c1d53fd67c68e AS builder

WORKDIR /app

RUN python -m venv /venv

COPY requirements.txt ./
RUN /venv/bin/pip install --no-cache-dir --requirement requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
RUN /venv/bin/pip install --no-cache-dir --no-deps .

FROM cgr.dev/chainguard/python:latest@sha256:e2554b2ab18fc6d3a22f249245f8a8cf866687441b38273ffd5e0f3e37009e00

ENV GRAPH_BACKEND=fixture \
    PATH=/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /venv /venv
COPY fixtures/synthetic_graph.json ./fixtures/synthetic_graph.json

USER 65532:65532

ENTRYPOINT ["python", "-m", "graph_mcp.server"]