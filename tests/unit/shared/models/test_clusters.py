from datetime import datetime
from unittest.mock import patch

import pytest
from factories.cluster_factory import make_add_cluster_payload

from api.shared.enums import Provider
from api.shared.models.clusters import Cluster


@pytest.fixture
def patch_datetime_now():
    def _patch(date_str: str):
        fake_dt = datetime.fromisoformat(date_str)
        patcher = patch("api.shared.models.clusters.datetime", wraps=datetime)
        mock_dt = patcher.start()
        mock_dt.now.return_value = fake_dt
        return patcher

    return _patch


@pytest.mark.unit
@pytest.mark.models
class TestClusterModel:
    """Unit tests for Cluster model"""

    @pytest.mark.parametrize(
        "uptime_period, fake_now, expected_outcome",
        [
            # No uptime_period set -> not in downtime
            (None, "2026-04-27T00:00:00+00", False),
            # Monday 20:00 -> outside 08:00-17:00 -> in downtime
            ("Mon-Fri 08:00-17:00 Europe/Lisbon", "2026-04-27T20:00:00+00", True),
            # Monday 12:00 -> inside 08:00-17:00 -> not in downtime
            ("Mon-Fri 08:00-17:00 Europe/Lisbon", "2026-04-27T12:00:00+00", False),
            # Saturday 12:00 -> outside Mon-Fri -> in downtime
            ("Mon-Fri 08:00-17:00 Europe/Lisbon", "2026-05-02T12:00:00+01:00", True),
            # Saturday 12:00 with Fri-Mon wrap-around -> inside range and hours -> not in downtime
            ("Fri-Mon 08:00-17:00 Europe/Lisbon", "2026-05-02T12:00:00+01:00", False),
            # Wednesday 12:00 with Fri-Mon wrap-around -> outside range -> in downtime
            ("Fri-Mon 08:00-17:00 Europe/Lisbon", "2026-04-29T12:00:00+01:00", True),
            # Monday 08:00 in Pacific/Auckland (Sunday 20:00 UTC) -> inside range and hours -> not in downtime
            ("Mon-Fri 08:00-17:00 Pacific/Auckland", "2026-04-27T08:00:00+12:00", False),
            # Sunday 20:00 in Pacific/Auckland -> outside Mon-Fri -> in downtime
            ("Mon-Fri 08:00-17:00 Pacific/Auckland", "2026-04-26T20:00:00+12:00", True),
            # Monday exactly at 17:00 -> end boundary (< end) -> in downtime
            ("Mon-Fri 08:00-17:00 Europe/Lisbon", "2026-04-27T17:00:00+01:00", True),
        ],
    )
    def test_downtime_window_evaluation(
        self, uptime_period: str, fake_now: str, expected_outcome: bool, patch_datetime_now
    ):
        """Test "is_downtime_window" metadata"""
        patch_datetime_now(fake_now)
        cluster_data = make_add_cluster_payload(Provider.AWS, uptime_period=uptime_period)
        cluster = Cluster().model_validate(cluster_data)
        assert cluster._is_in_downtime_window() == expected_outcome
