import pytest

if __name__ == "__main__":
    __import__('sys').path.insert(0, __import__('os').path.abspath(__import__('os').path.dirname(__file__) + '/..'))

from ado_wrapper.resources.variable_groups import VariableGroup
from tests.setup_client import setup_client


class TestVariableGroup:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
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

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        variable_group = VariableGroup.create(self.ado_client, "ado_wrapper-test-for-create-delete", {"a": "b"})
        variable_group.delete(self.ado_client)
        assert variable_group.variables == {"a": "b"}

    @pytest.mark.skip(reason="This test is flakey, and randomly fails, even with no changes")
    @pytest.mark.update
    def test_update(self) -> None:
        # Variable group updating is quite flakey, and randomly fails, even with no changes
        variable_group = VariableGroup.create(self.ado_client, "ado_wrapper-test-for-update", {"a": "b"})
        changed_variables = {"b": "c"}
        # =====
        variable_group.update(self.ado_client, "variables", changed_variables)  # For some reason, this only sometimes works
        assert variable_group.variables == changed_variables
        # =====
        fetch_variable_group = VariableGroup.get_by_id(self.ado_client, variable_group.variable_group_id)
        assert fetch_variable_group.variables == changed_variables
        # =====
        variable_group.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        variable_group_created = VariableGroup.create(self.ado_client, "ado_wrapper-test-for-get-by-id", {"a": "b"})
        variable_group = VariableGroup.get_by_id(self.ado_client, variable_group_created.variable_group_id)
        variable_group_created.delete(self.ado_client)
        assert variable_group.variable_group_id == variable_group_created.variable_group_id

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        variable_group_created = VariableGroup.create(self.ado_client, "ado_wrapper-test-for-get-all", {"a": "b"})
        variable_groups = VariableGroup.get_all(self.ado_client)
        variable_group_created.delete(self.ado_client)
        assert len(variable_groups) >= 1
        assert all(isinstance(user, VariableGroup) for user in variable_groups)

    @pytest.mark.get_all_by_name
    def test_get_by_name(self) -> None:
        variable_group_created = VariableGroup.create(self.ado_client, "ado_wrapper-test-for-get-by-name", {"a": "b"})
        variable_group = VariableGroup.get_by_name(self.ado_client, "ado_wrapper-test-for-get-by-name")
        variable_group_created.delete(self.ado_client)
        assert variable_group is not None
        assert variable_group.variable_group_id == variable_group_created.variable_group_id
        assert variable_group.name == variable_group_created.name

    @pytest.mark.skip(reason="This test takes 25-60 seconds (requires a build)")
    @pytest.mark.get_contents
    def test_get_variable_group_contents(self) -> None:
        mapping = {"a": "123", "b": "456"}
        variable_group = VariableGroup.create(self.ado_client, "ado_wrapper-test-for-get_variable_group_contents", mapping)
        contents = VariableGroup.get_variable_group_contents(self.ado_client, variable_group.name)
        variable_group.delete(self.ado_client)
        assert contents == mapping


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
