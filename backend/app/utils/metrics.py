"""Prometheus metrics, served at /metrics (Fly scrapes it via fly.toml [metrics]).

Labels are bounded: routes are the matched route template, never the raw path.
"""
from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"])
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "route"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 15, 30),
)
CHAT_TURNS = Counter("chat_turns_total", "Chat turns by resolved action", ["action"])
CHAT_STAGE = Histogram(
    "chat_stage_duration_seconds", "Time per chat stage", ["stage"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8),
)
LLM_CALLS = Counter("llm_calls_total", "LLM calls by kind and outcome", ["kind", "outcome"])
CHAT_EMPTY = Counter("chat_empty_results_total", "Chat turns that found no products")
