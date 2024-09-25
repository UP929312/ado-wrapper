import time

import pytest

if __name__ == "__main__":
    __import__('sys').path.insert(0, __import__('os').path.abspath(__import__('os').path.dirname(__file__) + '/..'))

from ado_wrapper.resources.groups import Group
from tests.setup_client import setup_client


class TestGroup:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        group = Group.from_request_payload(
            {
                "url": "https://vssps.dev.azure.com/ado-org/_apis/Graph/Groups/123",
                "displayName": "test-Group",
                "description": "test-Group",
                "domain": "vstfs:///Classification/TeamProject/ado-project",
                "originId": "0000000000-000000000-000000000-0000000000",
            }
        )
        assert isinstance(group, Group)
        assert group.group_descriptor == "123"
        assert group.name == "test-Group"
        assert group.description == "test-Group"
        assert group.to_json() == Group.from_json(group.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_group(self) -> None:
        group_created = Group.create(self.ado_client, "ado_wrapper-test-group")
        time.sleep(3)
        group_created.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        group_created = Group.create(self.ado_client, "ado_wrapper-get-by-id")
        group = Group.get_by_id(self.ado_client, group_created.group_descriptor)
        assert group_created.group_descriptor == group.group_descriptor
        group_created.delete(self.ado_client)

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        group_created = Group.create(self.ado_client, "ado_wrapper-get-all")
        groups = Group.get_all(self.ado_client)
        assert len(groups) > 1
        assert all(isinstance(group, Group) for group in groups)
        group_created.delete(self.ado_client)

    def test_get_by_name(self) -> None:
        group_created = Group.create(self.ado_client, "ado_wrapper-for-get-by-name")
        group = Group.get_by_name(self.ado_client, group_created.name)
        assert group is not None
        assert group.name == group_created.name
        group_created.delete(self.ado_client)

    # def test_get_members(self) -> None:
    #     members = Group.get_by_name(self.ado_client, existing_group_name).get_members(self.ado_client)
    #     assert len(members) > 1
    #     assert all(isinstance(member, GroupMember) for member in members)


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
