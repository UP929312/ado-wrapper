import pytest

if __name__ == "__main__":
    __import__('sys').path.insert(0, __import__('os').path.abspath(__import__('os').path.dirname(__file__) + '/..'))

from ado_wrapper.resources.users import AdoUser
from tests.setup_client import existing_user_descriptor, email, existing_user_name, setup_client  # fmt: skip


class TestAdoUser:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        user = AdoUser.from_request_payload({"descriptor": "123", "displayName": "test-AdoUser", "mailAddress": "test@test.com",
                                             "origin": "aad", "originId": "123"})  # fmt: skip
        assert isinstance(user, AdoUser)
        assert user.descriptor_id == "123"
        assert user.display_name == "test-AdoUser"
        assert user.email == "test@test.com"
        assert user.origin == "aad"
        assert user.to_json() == AdoUser.from_json(user.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        with pytest.raises(NotImplementedError):
            AdoUser.create(self.ado_client, "ado_wrapper-test-user", "ado_wrapper")
        with pytest.raises(NotImplementedError):
            AdoUser.delete_by_id(self.ado_client, "abc")

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        user = AdoUser.get_by_id(self.ado_client, existing_user_descriptor)
        assert user.descriptor_id == existing_user_descriptor

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        users = AdoUser.get_all(self.ado_client)
        assert len(users) > 1
        assert all(isinstance(user, AdoUser) for user in users)

    def test_get_by_name(self) -> None:
        user = AdoUser.get_by_name(self.ado_client, existing_user_name)
        assert user is not None
        assert user.descriptor_id == existing_user_descriptor

    def test_get_by_email(self) -> None:
        user = AdoUser.get_by_email(self.ado_client, email)
        assert user is not None
        assert user.descriptor_id == existing_user_descriptor


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
