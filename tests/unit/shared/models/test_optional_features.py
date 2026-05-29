import pytest
from factories.feature_factory import make_add_feature_payload

from api.shared.models.features import FeatureBase


@pytest.mark.unit
@pytest.mark.models
@pytest.mark.optional_features
class TestFeatureBase:
    """Unit tests for FeatureBase model validation."""

    @pytest.mark.parametrize(
        "featureA, featureB, should_equal",
        [
            # Testing two completely different features. Should not match.
            (make_add_feature_payload(), make_add_feature_payload(), False),
            # Testing two completely equal features. Should match.
            (
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=[],
                    namespaced=False,
                ),
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=[],
                    namespaced=False,
                ),
                True,
            ),
            # Testing feature A with None "dependencies" and feature B with a valid dependency. Should not match.
            (
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=None,
                    constraints=[],
                    namespaced=False,
                ),
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=["dependency"],
                    constraints=[],
                    namespaced=False,
                ),
                False,
            ),
            # Testing feature A with a valid dependency and feature B with None "dependencies". Should not match.
            (
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=["dependency"],
                    constraints=[],
                    namespaced=False,
                ),
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=None,
                    constraints=[],
                    namespaced=False,
                ),
                False,
            ),
            # Testing feature A with None "constraints" and feature B with a valid constraint. Should not match.
            (
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=None,
                    namespaced=False,
                ),
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=[{"key": "constraint_key", "operator": "equals", "value": "constraint_value"}],
                    namespaced=False,
                ),
                False,
            ),
            # Testing feature A with a valid constraint and feature B with None "constraints". Should not match.
            (
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=[{"key": "constraint_key", "operator": "equals", "value": "constraint_value"}],
                    namespaced=False,
                ),
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=None,
                    namespaced=False,
                ),
                False,
            ),
            # Testing two features with different dependencies count. Should not match.
            (
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=["dependencyA", "dependencyA", "dependencyB"],
                    constraints=[],
                    namespaced=False,
                ),
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=["dependencyA", "dependencyA"],
                    constraints=[],
                    namespaced=False,
                ),
                False,
            ),
            # Testing two equal features with dependencies. Should match.
            (
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=["dependencyA", "dependencyA", "dependencyB"],
                    constraints=[],
                    namespaced=False,
                ),
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=["dependencyA", "dependencyA", "dependencyB"],
                    constraints=[],
                    namespaced=False,
                ),
                True,
            ),
            # Testing two features with different constraints count. Should not match.
            (
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=[
                        {"key": "constraint_a_key", "operator": "equals", "value": "constraint_a_value"},
                        {"key": "constraint_b_key", "operator": "equals", "value": "constraint_b_value"},
                    ],
                    namespaced=False,
                ),
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=[
                        {"key": "constraint_a_key", "operator": "equals", "value": "constraint_a_value"},
                    ],
                    namespaced=False,
                ),
                False,
            ),
            # Testing two equal features with constraints. Should match.
            (
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=[
                        {"key": "constraint_a_key", "operator": "equals", "value": "constraint_a_value"},
                        {"key": "constraint_b_key", "operator": "equals", "value": "constraint_b_value"},
                    ],
                    namespaced=False,
                ),
                make_add_feature_payload(
                    name="nice-feature",
                    type="optional",
                    dependencies=[],
                    constraints=[
                        {"key": "constraint_a_key", "operator": "equals", "value": "constraint_a_value"},
                        {"key": "constraint_b_key", "operator": "equals", "value": "constraint_b_value"},
                    ],
                    namespaced=False,
                ),
                True,
            ),
        ],
    )
    def test_feature_base_model_equality(self, featureA: FeatureBase, featureB: FeatureBase, should_equal: bool):
        """Test equality comparison between FeatureBase instances."""
        if should_equal:
            assert featureA == featureB
        else:
            assert featureA != featureB

    def test_feature_base_not_implemented(self):
        """Test that FeatureBase.__eq__() returns NotImplemented for incompatible type comparisons."""

        class OtherClass:
            def __eq__(self, value):
                return "NotImplemented"

        featureA = make_add_feature_payload()
        other = OtherClass()
        match = featureA == other
        assert match == "NotImplemented"
