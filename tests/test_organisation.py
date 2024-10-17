import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources.organisations import Organisation
from tests.setup_client import setup_client, ado_org_name


class TestOrganisation:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        organisation = Organisation.from_request_payload(
            {
                "id": "123",
                "name": "test-organisation",
            }
        )
        assert isinstance(organisation, Organisation)
        assert organisation.organisation_id == "123"
        assert organisation.name == "test-organisation"
        assert organisation.to_json() == Organisation.from_json(organisation.to_json()).to_json()

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        organisations = Organisation.get_all(self.ado_client)
        assert len(organisations) > 0

    @pytest.mark.get_all_by_name
    def test_get_by_name(self) -> None:
        organisation = Organisation.get_by_name(self.ado_client, ado_org_name)
        assert organisation is not None
        assert organisation.name == ado_org_name


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vvvv"])
    # pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
