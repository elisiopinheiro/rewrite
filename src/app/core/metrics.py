"""OpenTelemetry metrics and Prometheus exporter setup."""

from fastapi import FastAPI
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from prometheus_client import make_asgi_app

_METRICS_PATH = "/metrics"
_EXCLUDED_URLS = r"^/healthz$,^/readyz$,^/metrics$"


def setup_metrics(app: FastAPI, *, service_name: str) -> None:
    """Instrument the FastAPI app with OpenTelemetry and expose /metrics."""
    if getattr(app.state, "metrics_configured", False):
        return

    provider = MeterProvider(
        resource=Resource(attributes={SERVICE_NAME: service_name}),
        metric_readers=[PrometheusMetricReader()],
    )

    FastAPIInstrumentor.instrument_app(app, meter_provider=provider, excluded_urls=_EXCLUDED_URLS)

    if not any(getattr(route, "path", None) == _METRICS_PATH for route in app.routes):
        app.mount(_METRICS_PATH, make_asgi_app())

    app.state.metrics_configured = True
