import pytest

from client import AdoClient
from resources.users import AdoUser

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    (
        ado_org, ado_project, email, pat_token, _, _, existing_user_name, existing_user_email, existing_user_id,
        *_  # fmt: skip
    ) = test_data.read().splitlines()  # type: ignore[assignment]


class TestAdoUser:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

    def test_from_request_payload(self) -> None:
        user = AdoUser.from_request_payload({"descriptor": "123", "displayName": "test-AdoUser", "mailAddress": "test@test.com",
                                             "origin": "aad", "originId": "123"})  # fmt: skip
        assert isinstance(user, AdoUser)
        assert user.descriptor_id == "123"
        assert user.display_name == "test-AdoUser"
        assert user.email == "test@test.com"
        assert user.origin == "aad"
        assert user.to_json() == AdoUser.from_json(user.to_json()).to_json()

    def test_create_delete(self) -> None:
        with pytest.raises(NotImplementedError):
            AdoUser.create(self.ado_client, "ado-api-test-user", "ado-api")
        with pytest.raises(NotImplementedError):
            AdoUser.delete_by_id(self.ado_client, "abc")

    def test_get_by_id(self) -> None:
        user = AdoUser.get_by_id(self.ado_client, existing_user_id)
        assert user.descriptor_id == existing_user_id

    def test_get_all(self) -> None:
        users = AdoUser.get_all(self.ado_client)
        assert len(users) > 1
        assert all(isinstance(user, AdoUser) for user in users)

    def test_get_by_name(self) -> None:
        user = AdoUser.get_by_name(self.ado_client, existing_user_name)
        assert user.descriptor_id == existing_user_id

    def test_get_by_email(self) -> None:
        user = AdoUser.get_by_email(self.ado_client, existing_user_email)
        assert user.descriptor_id == existing_user_id
