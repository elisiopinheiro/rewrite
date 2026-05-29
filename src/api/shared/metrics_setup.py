"""Clusters4WM metrics setup"""

from fastapi import FastAPI, Response
from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


def setup_metrics(app: FastAPI) -> MeterProvider:
    """Configures OpenTelemetry metrics for the app."""
    resource = Resource.create({"service.name": app.title})

    # Create Prometheus Metric Reader
    prometheus_reader = PrometheusMetricReader()

    # Set up Meter Provider with Prometheus reader
    meter_otel = MeterProvider(resource=resource, metric_readers=[prometheus_reader])

    # Register Meter Provider
    metrics.set_meter_provider(meter_otel)

    # Instrument FastAPI with OpenTelemetry
    FastAPIInstrumentor.instrument_app(app, meter_provider=meter_otel)

    @app.get("/metrics", include_in_schema=True)
    def get_metrics():
        """Export Prometheus Metrics"""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return meter_otel
