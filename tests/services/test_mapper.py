"""Unit tests for ClusterMapper computed fields."""

from datetime import UTC, datetime, timedelta

import app.services.clusters.mapper as mapper_module
from app.services.clusters.mapper import ClusterMapper


class TestIsInDowntimeWindow:
    """Test the _is_in_downtime_window static method."""

    def test_none_uptime_returns_false(self):
        assert ClusterMapper._is_in_downtime_window(None) is False

    def test_empty_string_returns_false(self):
        assert ClusterMapper._is_in_downtime_window("") is False

    def test_invalid_format_returns_false(self):
        assert ClusterMapper._is_in_downtime_window("garbage") is False

    def test_valid_format_returns_false_during_uptime_window(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2024, 1, 1, 9, 0, tzinfo=tz)

        monkeypatch.setattr(mapper_module, "datetime", FixedDateTime)

        assert ClusterMapper._is_in_downtime_window("MON-FRI 08:00-18:00 UTC") is False

    def test_valid_format_returns_true_outside_uptime_window(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2024, 1, 1, 19, 0, tzinfo=tz)

        monkeypatch.setattr(mapper_module, "datetime", FixedDateTime)

        assert ClusterMapper._is_in_downtime_window("MON-FRI 08:00-18:00 UTC") is True

    def test_weekday_range_wraps_across_week_boundary(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2024, 1, 6, 9, 0, tzinfo=tz)

        monkeypatch.setattr(mapper_module, "datetime", FixedDateTime)

        assert ClusterMapper._is_in_downtime_window("FRI-MON 08:00-18:00 UTC") is False

    def test_invalid_timezone_returns_false(self):
        assert ClusterMapper._is_in_downtime_window("MON-FRI 00:00-23:59 Not/AZone") is False

    def test_invalid_weekday_returns_false(self):
        assert ClusterMapper._is_in_downtime_window("XXX-FRI 00:00-23:59 UTC") is False


class TestIsLocked:
    """Test the _is_locked static method."""

    def test_no_lock_returns_false(self):
        class FakeCluster:
            cluster_lock = None

        assert ClusterMapper._is_locked(FakeCluster()) is False

    def test_unlocked_returns_false(self):
        class FakeLock:
            locked = False
            timeout_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1)

        class FakeCluster:
            cluster_lock = FakeLock()

        assert ClusterMapper._is_locked(FakeCluster()) is False

    def test_expired_lock_returns_false(self):
        class FakeLock:
            locked = True
            timeout_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)

        class FakeCluster:
            cluster_lock = FakeLock()

        assert ClusterMapper._is_locked(FakeCluster()) is False

    def test_active_lock_returns_true(self):
        class FakeLock:
            locked = True
            timeout_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1)

        class FakeCluster:
            cluster_lock = FakeLock()

        assert ClusterMapper._is_locked(FakeCluster()) is True

    def test_lock_expiring_now_returns_false(self, monkeypatch):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2024, 1, 1, 12, 0, tzinfo=tz)

        monkeypatch.setattr(mapper_module, "datetime", FixedDateTime)

        class FakeLock:
            locked = True
            timeout_at = datetime(2024, 1, 1, 12, 0)

        class FakeCluster:
            cluster_lock = FakeLock()

        assert ClusterMapper._is_locked(FakeCluster()) is False


class TestToPublicOtlpEndpoint:
    def test_maps_endpoint_and_auth_field_names(self):
        result = ClusterMapper._to_public_otlp_endpoint(
            {
                "name": "otel",
                "type": "otlp",
                "endpoint": "https://example.com/otlp",
                "signals": ["logs"],
                "auth": {
                    "type": "header",
                    "secret_name": "otel-headers",
                    "secret_namespace": "platform",
                },
                "config": {"required_attributes": ["k8s.cluster.name"]},
            }
        )

        assert result["endpoint_type"] == "otlp"
        assert "type" not in result
        assert result["auth"]["auth_type"] == "header"
        assert "type" not in result["auth"]
        assert result["config"] == {"required_attributes": ["k8s.cluster.name"]}
