import importlib
import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials

import api.partner.auth
from api.partner.auth import (
    BASIC_CLOUD_API_PASSWORD,
    BASIC_CLOUD_API_USERNAME,
    BASIC_M4W_API_PASSWORD,
    BASIC_M4W_API_USERNAME,
    BASIC_SCP_API_PASSWORD,
    BASIC_SCP_API_USERNAME,
    BASIC_SOLAR_API_PASSWORD,
    BASIC_SOLAR_API_USERNAME,
    USERS_ROLES_MAPPING,
    Role,
    _authenticate_credentials,
    validate_credentials,
    validate_user_role,
)


@pytest.mark.unit
@pytest.mark.partner_app
@pytest.mark.authentication
class TestAuthentication:
    """Unit tests for authentication functions."""

    def test_authenticate_credentials_success(self):
        """Test that authentication succeeds with correct username and password."""
        credentials = HTTPBasicCredentials(username="testuser", password="testpass")
        result = _authenticate_credentials(credentials, "testuser", "testpass")
        assert result

    def test_authenticate_credentials_wrong_username(self):
        """Test that authentication fails with incorrect username."""
        credentials = HTTPBasicCredentials(username="wronguser", password="testpass")
        result = _authenticate_credentials(credentials, "testuser", "testpass")
        assert not result

    def test_authenticate_credentials_wrong_password(self):
        """Test that authentication fails with incorrect password."""
        credentials = HTTPBasicCredentials(username="testuser", password="wrongpass")
        result = _authenticate_credentials(credentials, "testuser", "testpass")
        assert not result

    def test_authenticate_credentials_empty_credentials(self):
        """Test that authentication fails with empty credentials."""
        credentials = HTTPBasicCredentials(username="", password="")
        result = _authenticate_credentials(credentials, "testuser", "testpass")
        assert not result

    def test_authenticate_credentials_case_sensitivity(self):
        """Test that authentication is case-sensitive."""
        credentials = HTTPBasicCredentials(username="TestUser", password="TestPass")
        result = _authenticate_credentials(credentials, "testuser", "testpass")
        assert not result

    @patch.dict(
        os.environ,
        {
            "BASIC_M4W_API_USERNAME": "m4w_user",
            "BASIC_M4W_API_PASSWORD": "m4w_pass",
        },
    )
    def test_validate_credentials_m4w_user_success(self):
        """Test that M4W user credentials are validated successfully."""
        # Re-import to get updated environment values
        importlib.reload(api.partner.auth)

        credentials = HTTPBasicCredentials(username="m4w_user", password="m4w_pass")
        result = api.partner.auth.validate_credentials(credentials)
        assert result == "m4w_user"

    @patch.dict(
        os.environ,
        {
            "BASIC_CLOUD_API_USERNAME": "cloud_user",
            "BASIC_CLOUD_API_PASSWORD": "cloud_pass",
        },
    )
    def test_validate_credentials_cloud_user_success(self):
        """Test that Cloud Foundation user credentials are validated successfully."""
        # Re-import to get updated environment values
        importlib.reload(api.partner.auth)

        credentials = HTTPBasicCredentials(username="cloud_user", password="cloud_pass")
        result = api.partner.auth.validate_credentials(credentials)
        assert result == "cloud_user"

    @patch.dict(
        os.environ,
        {
            "BASIC_SCP_API_USERNAME": "scp_user",
            "BASIC_SCP_API_PASSWORD": "scp_pass",
        },
    )
    def test_validate_credentials_scp_user_success(self):
        """Test that SCP user credentials are validated successfully."""
        # Re-import to get updated environment values
        importlib.reload(api.partner.auth)

        credentials = HTTPBasicCredentials(username="scp_user", password="scp_pass")
        result = api.partner.auth.validate_credentials(credentials)
        assert result == "scp_user"

    @patch.dict(
        os.environ,
        {
            "BASIC_SOLAR_API_USERNAME": "solar_user",
            "BASIC_SOLAR_API_PASSWORD": "solar_pass",
        },
    )
    def test_validate_credentials_solar_user_success(self):
        """Test that SOLAR user credentials are validated successfully."""
        # Re-import to get updated environment values
        importlib.reload(api.partner.auth)

        credentials = HTTPBasicCredentials(username="solar_user", password="solar_pass")
        result = api.partner.auth.validate_credentials(credentials)
        assert result == "solar_user"

    @patch.dict(
        os.environ,
        {
            "BASIC_CLOUD_API_USERNAME": "cloud_user",
            "BASIC_CLOUD_API_PASSWORD": "cloud_pass",
            "BASIC_SCP_API_USERNAME": "scp_user",
            "BASIC_SCP_API_PASSWORD": "scp_pass",
            "BASIC_SOLAR_API_USERNAME": "solar_user",
            "BASIC_SOLAR_API_PASSWORD": "solar_pass",
        },
    )
    def test_validate_credentials_invalid_user_raises_401(self):
        """Test that invalid credentials raise HTTP 401 Unauthorized."""
        # Re-import to get updated environment values
        importlib.reload(api.partner.auth)

        credentials = HTTPBasicCredentials(username="invalid", password="invalid")

        with pytest.raises(HTTPException) as exc_info:
            api.partner.auth.validate_credentials(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Incorrect username or password"
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

    def test_validate_credentials_default_values(self):
        """Test that credential validation works with default environment values."""
        importlib.reload(api.partner.auth)
        credentials = HTTPBasicCredentials(username="ctw", password="ctw")
        result = validate_credentials(credentials)
        assert result == BASIC_M4W_API_USERNAME

    @patch.dict(
        os.environ,
        {
            "BASIC_M4W_API_USERNAME": "testuser",
            "BASIC_M4W_API_PASSWORD": "testpass",
            "BASIC_CLOUD_API_USERNAME": "cf_user",
            "BASIC_CLOUD_API_PASSWORD": "cf_pass",
            "BASIC_SCP_API_USERNAME": "scp_testuser",
            "BASIC_SCP_API_PASSWORD": "scp_testpass",
            "BASIC_SOLAR_API_USERNAME": "solar_testuser",
            "BASIC_SOLAR_API_PASSWORD": "solar_testpass",
        },
    )
    def test_validate_credentials_partial_match_fails(self):
        """Test that partial credential matches (correct username, wrong password) are rejected."""
        importlib.reload(api.partner.auth)

        # Right username, wrong password for cloud
        credentials = HTTPBasicCredentials(username="testuser", password="wrongpass")

        with pytest.raises(HTTPException) as exc_info:
            api.partner.auth.validate_credentials(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
@pytest.mark.partner_app
@pytest.mark.authorization
class TestUserRoleValidation:
    """Unit tests for user role validation."""

    def test_validate_user_role_m4w_access_always_granted(self):
        """Test that M4W role automatically grants access to all endpoints.

        Validates the special authorization rule where 4Wheels Managed (M4W)
        users have universal access to all API endpoints regardless of the
        specific role requirements.

        Test setup:
        - Mocks user with M4W role only
        - Creates validator requiring SCP role

        Verifies:
        - M4W role is automatically added to required roles list
        - M4W users pass validation even for SCP-only endpoints
        - No HTTPException is raised

        This implements a superuser pattern where M4W acts as an admin role
        with unrestricted access across all partner API endpoints.
        """
        with patch("api.partner.auth.USERS_ROLES_MAPPING", {"cloud_user": [Role.M4W]}):
            validator = validate_user_role([Role.SCP])

            # M4W user should have access because M4W role is auto-added
            try:
                validator("cloud_user")
            except HTTPException:
                pytest.fail("M4W user should have access to all endpoints")

    def test_validate_user_role_specific_role_access(self):
        """Test authorization succeeds when user has the exact required role.

        Validates that role-based access control correctly grants access when
        a user's assigned role matches the endpoint's required role.

        Test setup:
        - Mocks user with SCP role
        - Creates validator requiring SCP role

        Verifies:
        - Users with matching role gain access
        - No HTTPException is raised for authorized access
        - Role matching is exact (SCP user accessing SCP endpoint)

        This ensures the standard case where users with appropriate roles
        can access their designated endpoints.
        """
        with patch("api.partner.auth.USERS_ROLES_MAPPING", {"scp_user": [Role.SCP]}):
            validator = validate_user_role([Role.SCP])

            # SCP user should have access
            try:
                validator("scp_user")
            except HTTPException:
                pytest.fail("SCP user should have access to SCP endpoints")

    def test_validate_user_role_multiple_roles_any_match(self):
        """Test that users with multiple roles gain access if ANY role matches.

        Validates authorization logic when users have multiple assigned roles
        and only need one of them to match the endpoint requirements.

        Test setup:
        - Mocks user with both SCP and SOLAR roles
        - Creates validator requiring only SOLAR role

        Verifies:
        - Access is granted when one of user's roles matches
        - Having additional roles doesn't interfere with authorization
        - OR logic for role matching (not AND)

        This supports flexible authorization where users may have multiple
        responsibilities and can access endpoints matching any of their roles.
        """
        with patch("api.partner.auth.USERS_ROLES_MAPPING", {"multi_role_user": [Role.SCP, Role.SOLAR]}):
            validator = validate_user_role([Role.SOLAR])

            # Multi-role user should have access
            try:
                validator("multi_role_user")
            except HTTPException:
                pytest.fail("User with SOLAR role should have access")

    def test_validate_user_role_no_permission_raises_403(self):
        """Test that users without required roles receive HTTP 403 Forbidden.

        Validates that authorization correctly denies access when a user's
        assigned roles don't match the endpoint's requirements, returning
        appropriate HTTP error status.

        Test setup:
        - Mocks user with only SCP role
        - Creates validator requiring SOLAR role

        Verifies:
        - HTTPException is raised for unauthorized access attempts
        - Status code is HTTP_403_FORBIDDEN (403)
        - Error detail explains lack of permissions
        - User has authenticated (401) but lacks authorization (403)

        This ensures proper separation between authentication (who you are)
        and authorization (what you can do), following HTTP security standards.
        """
        with patch("api.partner.auth.USERS_ROLES_MAPPING", {"scp_user": [Role.SCP]}):
            validator = validate_user_role([Role.SOLAR])

            with pytest.raises(HTTPException) as exc_info:
                validator("scp_user")  # SCP user trying SOLAR endpoint

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert exc_info.value.detail == ("You do not have the necessary permissions to access this resource.")

    def test_validate_user_role_unknown_user_denied(self):
        """Test that users not in the roles mapping are denied access.

        Validates that authorization fails for users that aren't configured
        in the system's role mapping, even if they somehow passed authentication.

        Test setup:
        - Mocks empty roles mapping (no users configured)
        - Attempts validation with an unknown username

        Verifies:
        - HTTPException is raised for unmapped users
        - Status code is HTTP_403_FORBIDDEN (403)
        - System denies access by default when user has no assigned roles

        This implements a secure default (deny by default) where users must
        be explicitly granted roles to access any protected endpoints.
        """
        with patch("api.partner.auth.USERS_ROLES_MAPPING", {}):
            validator = validate_user_role([Role.SCP])

            with pytest.raises(HTTPException) as exc_info:
                validator("unknown_user")

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_validate_user_role_multiple_required_roles(self):
        """Test authorization when endpoints accept multiple alternative roles.

        Validates that endpoints can specify multiple acceptable roles,
        and users need only ONE of those roles to gain access.

        Test setup:
        - Mocks two users: one with SCP role, one with SOLAR role
        - Creates validator accepting either SCP OR SOLAR

        Verifies:
        - SCP user gains access (has one of required roles)
        - SOLAR user gains access (has one of required roles)
        - OR logic works correctly for role lists
        - Multiple role requirements enable flexible access patterns

        This supports endpoints that serve multiple user types with different
        roles, such as shared administrative or reporting functions.
        """
        with patch("api.partner.auth.USERS_ROLES_MAPPING", {"scp_user": [Role.SCP], "solar_user": [Role.SOLAR]}):
            validator = validate_user_role([Role.SCP, Role.SOLAR])

            # Both SCP and SOLAR users should have access
            try:
                validator("scp_user")
                validator("solar_user")
            except HTTPException:
                pytest.fail("Users with any of the required roles should have access")

    def test_validate_user_role_decorator_returns_function(self):
        """Test that validate_user_role returns a callable validator function.

        Validates the factory pattern used by validate_user_role, which creates
        and returns a validator function that can be used as a FastAPI dependency.

        Verifies:
        - validate_user_role returns a function (not a validation result)
        - The returned object is callable
        - Follows dependency injection pattern for FastAPI route protection

        This tests the API design that allows validate_user_role to be used
        as a dependency factory: `Depends(validate_user_role([Role.SCP]))`
        """
        validator = validate_user_role([Role.M4W])

        assert callable(validator)

    def test_validate_user_role_m4w_always_added(self):
        """Test that M4W role is implicitly added to all endpoint role requirements.

        Validates the special authorization behavior where M4W (4Wheels Managed)
        role is automatically included in every endpoint's allowed roles list,
        effectively making M4W users superusers.

        Test setup:
        - Mocks user with only M4W role
        - Creates validator requiring only SCP role (M4W not explicitly listed)

        Verifies:
        - M4W user passes validation despite not having SCP role
        - M4W role is implicitly added to required_roles internally
        - This happens automatically without explicit configuration

        This implements a privileged access pattern where M4W acts as an
        administrative role with unrestricted access, useful for operations
        and support teams that need universal API access.
        """
        with patch("api.partner.auth.USERS_ROLES_MAPPING", {"cloud_user": [Role.M4W]}):
            validator = validate_user_role([Role.SCP])  # Only SCP required originally

            # M4W user should still have access because M4W is auto-added
            try:
                validator("cloud_user")
            except HTTPException:
                pytest.fail("M4W user should always have access due to auto-addition of M4W role")


@pytest.mark.unit
@pytest.mark.partner_app
@pytest.mark.roles
class TestRoleEnum:
    """Unit tests for Role enum."""

    def test_role_enum_values(self):
        """Test that Role enum constants have correct string values.

        Validates the Role enum definition contains the expected string values
        for each role type used in the partner API authorization system.

        Verifies each role constant maps to correct full name:
        - Role.M4W → "4Wheels Managed"
        - Role.CF → "Cloud Foundation"
        - Role.SCP → "Standard Cloud Platform"
        - Role.SOLAR → "Solution Landscape and Anomaly Reporter"

        These string values are used for logging, error messages, and potentially
        external integrations. They must remain consistent for backwards compatibility.
        """
        assert Role.M4W == "4Wheels Managed"
        assert Role.CF == "Cloud Foundation"
        assert Role.SCP == "Standard Cloud Platform"
        assert Role.SOLAR == "Solution Landscape and Anomaly Reporter"

    def test_role_enum_inheritance(self):
        """Test that Role enum values are string instances.

        Validates that the Role enum properly inherits from str, making each
        role constant an instance of string type. This is important for:
        - String comparisons in authorization logic
        - JSON serialization
        - Logging and display purposes
        - Type checking and validation

        Verifies that isinstance() checks pass for all role constants,
        confirming they can be used anywhere strings are expected.
        """
        assert isinstance(Role.M4W, str)
        assert isinstance(Role.CF, str)
        assert isinstance(Role.SCP, str)
        assert isinstance(Role.SOLAR, str)

    def test_default_mapping_contains_expected_users(self):
        """Test that the default users-to-roles mapping includes all configured user types.

        Validates that the USERS_ROLES_MAPPING dictionary contains entries for
        all partner API user types when using default environment configuration.

        Test behavior:
        - Reloads auth module to ensure default configuration is loaded

        Verifies presence of all user types:
        - M4W (4Wheels Managed) user from BASIC_M4W_API_USERNAME
        - Cloud Foundation user from BASIC_CLOUD_API_USERNAME
        - SCP user from BASIC_SCP_API_USERNAME
        - SOLAR user from BASIC_SOLAR_API_USERNAME

        This ensures all expected partner types can authenticate and have
        role assignments, preventing configuration gaps.
        """
        importlib.reload(api.partner.auth)

        assert BASIC_M4W_API_USERNAME in USERS_ROLES_MAPPING
        assert BASIC_CLOUD_API_USERNAME in USERS_ROLES_MAPPING
        assert BASIC_SCP_API_USERNAME in USERS_ROLES_MAPPING
        assert BASIC_SOLAR_API_USERNAME in USERS_ROLES_MAPPING

    def test_default_mapping_role_assignments(self):
        """Test that default users are assigned their correct corresponding roles.

        Validates that each user type in the default configuration is mapped
        to their appropriate role, ensuring correct authorization behavior.

        Test behavior:
        - Reloads auth module to ensure default configuration is loaded

        Verifies correct role assignments:
        - M4W username → Role.M4W
        - Cloud username → Role.CF (Cloud Foundation)
        - SCP username → Role.SCP
        - SOLAR username → Role.SOLAR

        This ensures the default role mapping matches the expected authorization
        model where each user type has access to their designated endpoints.
        """
        importlib.reload(api.partner.auth)

        assert Role.M4W in USERS_ROLES_MAPPING[BASIC_M4W_API_USERNAME]
        assert Role.SCP in USERS_ROLES_MAPPING[BASIC_SCP_API_USERNAME]
        assert Role.CF in USERS_ROLES_MAPPING[BASIC_CLOUD_API_USERNAME]
        assert Role.SOLAR in USERS_ROLES_MAPPING[BASIC_SOLAR_API_USERNAME]

    def test_default_environment_values(self):
        """Test that authentication system has default values for all required credentials.

        Validates that the auth module provides default credentials for all user
        types even when environment variables are not explicitly set, ensuring
        the system can function in development/testing without configuration.

        Test behavior:
        - Reloads auth module to load default environment configuration

        Verifies all credential pairs have non-None values:
        - BASIC_M4W_API_USERNAME and BASIC_M4W_API_PASSWORD
        - BASIC_CLOUD_API_USERNAME and BASIC_CLOUD_API_PASSWORD
        - BASIC_SCP_API_USERNAME and BASIC_SCP_API_PASSWORD
        - BASIC_SOLAR_API_USERNAME and BASIC_SOLAR_API_PASSWORD

        This ensures the application can start and function correctly in
        development environments without requiring environment variable setup,
        while production deployments override these with secure credentials.
        """
        importlib.reload(api.partner.auth)

        # These should have default values even if env vars not set
        assert BASIC_M4W_API_USERNAME is not None
        assert BASIC_M4W_API_PASSWORD is not None
        assert BASIC_CLOUD_API_USERNAME is not None
        assert BASIC_CLOUD_API_PASSWORD is not None
        assert BASIC_SCP_API_USERNAME is not None
        assert BASIC_SCP_API_PASSWORD is not None
        assert BASIC_SOLAR_API_USERNAME is not None
        assert BASIC_SOLAR_API_PASSWORD is not None


@pytest.mark.unit
@pytest.mark.partner_app
class TestCompleteAuthFlow:
    """Unit tests for complete authentication and authorization flows."""

    @patch.dict(
        os.environ,
        {
            "BASIC_CLOUD_API_USERNAME": "test_cloud",
            "BASIC_CLOUD_API_PASSWORD": "test_pass",
        },
    )
    def test_complete_auth_flow_success(self):
        """Test successful authentication and authorization flow."""
        importlib.reload(api.partner.auth)

        with patch("api.partner.auth.USERS_ROLES_MAPPING", {"test_cloud": [Role.CF]}):
            credentials = HTTPBasicCredentials(username="test_cloud", password="test_pass")

            # Step 1: Authenticate
            username = api.partner.auth.validate_credentials(credentials)
            assert username == "test_cloud"

            # Step 2: Authorize
            validator = api.partner.auth.validate_user_role([Role.CF])
            try:
                validator(username)
            except HTTPException:
                pytest.fail("Complete flow should work for CLOUD user")

    @patch.dict(
        os.environ,
        {
            "BASIC_M4W_API_USERNAME": "testuser",
            "BASIC_M4W_API_PASSWORD": "testpass",
            "BASIC_CLOUD_API_USERNAME": "test_cloud",
            "BASIC_CLOUD_API_PASSWORD": "test_pass",
            "BASIC_SCP_API_USERNAME": "scp_user",
            "BASIC_SCP_API_PASSWORD": "scp_pass",
            "BASIC_SOLAR_API_USERNAME": "solar_user",
            "BASIC_SOLAR_API_PASSWORD": "solar_pass",
        },
    )
    def test_auth_failure_at_credential_step(self):
        """Test that authentication failure returns HTTP 401."""
        importlib.reload(api.partner.auth)

        credentials = HTTPBasicCredentials(username="wrong", password="wrong")

        with pytest.raises(HTTPException) as exc_info:
            api.partner.auth.validate_credentials(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch.dict(
        os.environ,
        {
            "BASIC_SCP_API_USERNAME": "test_scp",
            "BASIC_SCP_API_PASSWORD": "test_pass",
        },
    )
    def test_auth_success_but_authorization_failure(self):
        """Test that authenticated users can still fail authorization (HTTP 403)."""
        importlib.reload(api.partner.auth)

        with patch(
            "src.api.partner.auth.USERS_ROLES_MAPPING",
            {
                "test_scp": [Role.SCP]  # Only SCP role, no M4W
            },
        ):
            credentials = HTTPBasicCredentials(username="test_scp", password="test_pass")

            # Step 1: Authenticate (should succeed)
            username = api.partner.auth.validate_credentials(credentials)
            assert username == "test_scp"

            # Step 2: Try to access SOLAR-only endpoint (should fail)
            validator = api.partner.auth.validate_user_role([Role.SOLAR])
            with pytest.raises(HTTPException) as exc_info:
                validator(username)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
