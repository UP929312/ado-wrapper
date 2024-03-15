import pytest

from client import AdoClient

from resources.variable_groups import VariableGroup

import pytest

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, *_ = test_data.read().splitlines()


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
        assert variable_group.to_json() == VariableGroup.from_json(variable_group.to_json()).to_json()

    @pytest.mark.wip
    def test_create_delete(self) -> None:
        variable_group = VariableGroup.create(self.ado_client, "ado-api-test-for-create-delete", "my_description", {"a": "b"})
        variable_group.delete(self.ado_client)
        assert variable_group.name == "ado-api-test-for-create-delete"

    def test_get_by_id(self) -> None:
        variable_group_created = VariableGroup.create(self.ado_client, "ado-api-test-for-get-by-id", "my_description", {"a": "b"})
        variable_group = VariableGroup.get_by_id(self.ado_client, variable_group_created.variable_group_id)
        variable_group_created.delete(self.ado_client)
        assert variable_group.variable_group_id == variable_group_created.variable_group_id

    def test_get_all(self) -> None:
        variable_group_created = VariableGroup.create(self.ado_client, "ado-api-test-for-get-all", "my_description", {"a": "b"})
        variable_groups = VariableGroup.get_all(self.ado_client)
        variable_group_created.delete(self.ado_client)
        assert len(variable_groups) >= 1
        assert all(isinstance(user, VariableGroup) for user in variable_groups)

    def test_get_by_name(self) -> None:
        variable_group_created = VariableGroup.create(self.ado_client, "ado-api-test-for-get-by-name", "my_description", {"a": "b"})
        variable_group = VariableGroup.get_by_name(self.ado_client, "ado-api-test-for-get-by-name")
        variable_group_created.delete(self.ado_client)
        assert variable_group is not None
        assert variable_group.variable_group_id == variable_group_created.variable_group_id
        assert variable_group.name == variable_group_created.name
