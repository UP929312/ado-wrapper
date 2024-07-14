import pytest

from ado_wrapper.resources.permissions import Permission, permissions
from tests.setup_client import setup_client


class TestPermission:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        permission = Permission.from_request_payload(
            {
                "securityNamespaceId": "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87",
                "permissions": 2,
                "value": True,
            }
        )
        assert permission.group == "Git Repositories"
        assert permission.group_namespace_id == "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        assert permission.name == "Read"
        assert permission.bit == 2
        assert permission.has_permission

    @pytest.mark.from_request_payload
    def test_get(self) -> None:
        perms = Permission.get_project_perms(self.ado_client)
        assert len(perms) > 5
        # assert len([x for x in perms if x.has_permission]) == len(perms)  # Should have all perms
        perms = Permission.get_project_perms_by_group(self.ado_client, "Git Repositories")
        assert len(perms) == len(permissions["Git Repositories"]["actions"])
        # assert len([x for x in perms if x.has_permission]) == len(perms)  # Should have all perms
