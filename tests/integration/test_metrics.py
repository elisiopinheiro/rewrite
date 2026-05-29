import pytest

EXPECTED_METRICS = [
    "process_virtual_memory_bytes",
    "process_resident_memory_bytes",
    "process_start_time_seconds",
    "process_cpu_seconds_total",
    "process_open_fds",
    "process_max_fds",
    "target_info",
    "http_server_active_requests",
]


def check_export_metrics(client):
    """Helper function to verify metrics endpoint exports expected metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert all(metric in response.text for metric in EXPECTED_METRICS)


@pytest.mark.integration
@pytest.mark.clusters4wm_app
class TestM4WMetrics:
    """Integration tests for clusters-4wm API metrics endpoint."""

    def test_metrics(self, client):
        """Test that clusters-4wm API exports Prometheus metrics."""
        check_export_metrics(client)


@pytest.mark.integration
@pytest.mark.partner_app
class TestPartnerMetrics:
    """Integration tests for partner API metrics endpoint."""

    def test_partner_metrics(self, partner_client):
        """Test that partner API exports Prometheus metrics."""
        check_export_metrics(partner_client)
