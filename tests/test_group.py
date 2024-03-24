import pytest

from client import AdoClient
from resources.groups import Group
# from resources.users import GroupMember

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    (
        ado_org, ado_project, email, pat_token, _, _, _, _, _, _, _, _,
        existing_group_descriptor, existing_group_name, *_  # fmt: skip
    ) = test_data.read().splitlines()  # type: ignore[assignment]


class TestGroup:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

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
        with pytest.raises(NotImplementedError):
            Group.create(self.ado_client, "ado-api-test-Group")
        with pytest.raises(NotImplementedError):
            Group.delete_by_id(self.ado_client, "abc")

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        group = Group.get_by_id(self.ado_client, existing_group_descriptor)
        assert group.group_descriptor == existing_group_descriptor

    def test_get_all(self) -> None:
        groups = Group.get_all(self.ado_client)
        assert len(groups) > 1
        assert all(isinstance(group, Group) for group in groups)

    def test_get_by_name(self) -> None:
        group = Group.get_by_name(self.ado_client, existing_group_name)
        assert group.name == existing_group_name

    # def test_get_members(self) -> None:
    #     members = Group.get_by_name(self.ado_client, existing_group_name).get_members(self.ado_client)
    #     assert len(members) > 1
    #     assert all(isinstance(member, GroupMember) for member in members)
