import pytest

from client import AdoClient
# from users import AdoUser
from variable_groups import VariableGroup

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    (
        ado_org, ado_project, email, pat_token, _, _, _, _, _, _, _, _, 
        existing_variable_group_name, existing_variable_group_id,
        *_  # fmt: skip
    ) = test_data.read().splitlines()  # type: ignore[assignment]


class TestVariableGroup:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

    def test_from_request_payload(self) -> None:
        variable_group = VariableGroup.from_request_payload(
            {
                "id": "123",
                "name": "test-variable-group",
                "description": "test-variable-group",
                "variables": {"key": "value"},
                "createdBy": {"displayName": "created_by_user", "uniqueName": "Created By User", "id": "123"},
                "modifiedBy": {"displayName": "modifying_user", "uniqueName": "Modifiying User", "id": "456"},
                "createdOn": "2023-10-01T00:00:00Z",
                "modifiedOn": "2024-10-01T00:00:00Z",
            }
        )
        assert isinstance(variable_group, VariableGroup)
        assert variable_group.variable_group_id == "123"
        assert variable_group.name == "test-variable-group"
        assert variable_group.description == "test-variable-group"
        assert variable_group.variables == {"key": "value"}
        assert variable_group.created_on.year == 2023
        assert variable_group.modified_on.year == 2024  # type: ignore[attr-defined]

    def test_create_delete(self) -> None:
        with pytest.raises(NotImplementedError):
            variable_group = VariableGroup.create(self.ado_client, "123", "main", "title", "description")
        with pytest.raises(NotImplementedError):
            variable_group = VariableGroup.get_by_name(self.ado_client, existing_variable_group_name)
            variable_group.delete(self.ado_client)

    def test_get_by_id(self) -> None:
        variable_group = VariableGroup.get_by_id(self.ado_client, existing_variable_group_id)
        assert variable_group.variable_group_id == existing_variable_group_id

    def test_get_all(self) -> None:
        variable_groups = VariableGroup.get_all(self.ado_client)
        assert len(variable_groups) > 1
        assert all([isinstance(user, VariableGroup) for user in variable_groups])

    def test_get_by_name(self) -> None:
        variable_group = VariableGroup.get_by_name(self.ado_client, existing_variable_group_name)
        assert variable_group.variable_group_id == existing_variable_group_id
        assert variable_group.name == existing_variable_group_name
