from datetime import datetime

import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources.releases import Release, ReleaseDefinition
from ado_wrapper.resources.users import Member
from ado_wrapper.errors import ResourceNotFound
from tests.setup_client import setup_client


class TestRelease:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        release = Release.from_request_payload(
            {
                "id": "123",
                "name": "test-release",
                "status": "active",
                "createdOn": "2021-10-01T00:00:00Z",
                "createdBy": {"displayName": "test", "uniqueName": "test", "id": "123"},
                "description": "test-release",
                "keepForever": False,
                "variables": {},
                "variableGroups": [],
            }
        )
        assert release.release_id == "123"
        assert release.to_json() == Release.from_json(release.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_release(self) -> None:
        release_definition = ReleaseDefinition.create(self.ado_client, "ado_wrapper-test-release-for-create-delete-release")
        release = Release.create(self.ado_client, release_definition.release_definition_id)
        assert release.release_id == Release.get_by_id(self.ado_client, release.release_id).release_id
        assert len(Release.get_all(self.ado_client, release_definition.release_definition_id)) == 1

        release_definition.delete(self.ado_client)  # Should also delete the release
        with pytest.raises(ResourceNotFound):
            Release.get_by_id(self.ado_client, release.release_id)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        release_definition = ReleaseDefinition.create(self.ado_client, "ado_wrapper-test-release-for-get-by-id")  # fmt: skip
        release = Release.create(self.ado_client, release_definition.release_definition_id)
        fetched_release = Release.get_by_id(self.ado_client, release.release_id)
        assert fetched_release.release_id == release.release_id
        release.delete(self.ado_client)
        release_definition.delete(self.ado_client)

    @pytest.mark.update
    @pytest.mark.skip("This test is skipped because it is not yet implemented")
    def test_update(self) -> None:
        release_definition = ReleaseDefinition.create(self.ado_client, "ado_wrapper-test-release-for-update")
        Release.create(self.ado_client, release_definition.release_definition_id)  # release =
        # ======
        # release.update(self.ado_client, "status", "completed")
        # assert release.status == "completed"
        # ======
        # fetched_release = Release.get_by_id(self.ado_client, release.release_id)
        # assert fetched_release.status == "completed"
        # ======
        release_definition.delete(self.ado_client)


# ======================================================================================================================


class TestReleaseDefinition:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        release_definition = ReleaseDefinition.from_request_payload(
            {
                "id": "123",
                "name": "test-release-definition",
                "description": "test-release-definition",
                "createdBy": {"displayName": "test", "uniqueName": "test", "id": "123"},
                "createdOn": "2021-10-01T00:00:00Z",
                "releaseNameFormat": "Release-$(rev:r)",
                "variableGroups": [],
                "isDeleted": False,
                "variables": {},
                "environments": [{"deployPhases": [{"deploymentInput": {"queueId": "123"}}]}],
            }
        )
        assert release_definition.release_definition_id == "123"
        assert release_definition.name == "test-release-definition"
        assert isinstance(release_definition.created_by, Member)
        assert isinstance(release_definition.created_on, datetime)
        assert release_definition.to_json() == ReleaseDefinition.from_json(release_definition.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        release_definition = ReleaseDefinition.create(self.ado_client, "ado_wrapper-test-release-for-create-delete")
        release_definition.delete(self.ado_client)
        assert release_definition.description == ""
        assert release_definition.name == "ado_wrapper-test-release-for-create-delete"

    @pytest.mark.get_by_id
    def test_get_all_by_definition_id(self) -> None:
        release_definition = ReleaseDefinition.create(self.ado_client, "ado_wrapper-test-release-for-get-all-by-repo")
        releases = ReleaseDefinition.get_all_releases_for_definition(self.ado_client, release_definition.release_definition_id)
        assert len(releases) == 0
        release_definition.delete(self.ado_client)

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        release_definition = ReleaseDefinition.create(self.ado_client, "ado_wrapper-test-release-for-get-all-by-repo")
        release_definitions = ReleaseDefinition.get_all(self.ado_client)
        release_definition.delete(self.ado_client)
        assert len(release_definitions) >= 1
        assert all(isinstance(x, ReleaseDefinition) for x in release_definitions)

    @pytest.mark.update
    def test_update(self) -> None:
        release_definition = ReleaseDefinition.create(self.ado_client, "ado_wrapper-test-release-for-update")
        # ======
        release_definition.update(self.ado_client, "name", "ado_wrapper-test-release-for-update-rename")
        assert release_definition.name == "ado_wrapper-test-release-for-update-rename"  # Test instance attribute is updated
        # ======
        fetched_release_definition = ReleaseDefinition.get_by_id(self.ado_client, release_definition.release_definition_id)
        assert fetched_release_definition.name == "ado_wrapper-test-release-for-update-rename"
        # ======
        release_definition.delete(self.ado_client)


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
