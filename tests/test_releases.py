from datetime import datetime

import pytest

from azuredevops.client import AdoClient
from azuredevops.resources.releases import Release, ReleaseDefinition
from azuredevops.resources.users import Member

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    (
        ado_org, ado_project, email, pat_token, _, _, _, _, _, existing_agent_pool_id, *_  # fmt: skip
    ) = test_data.read().splitlines()  # type: ignore[assignment]


class TestRelease:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project, state_file_name="tests/test_state.state")

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
        release_definition = ReleaseDefinition.create(
            self.ado_client, "azuredevops-test-releasefor-create-delete-release", [], existing_agent_pool_id
        )
        release = Release.create(self.ado_client, release_definition.release_definition_id)
        assert release.release_id == Release.get_by_id(self.ado_client, release.release_id).release_id
        assert len(Release.get_all(self.ado_client, release_definition.release_definition_id)) == 1
        release.delete(self.ado_client)
        release_definition.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        release_definition = ReleaseDefinition.create(self.ado_client, "azuredevops-test-release-for-get-by-id", [], existing_agent_pool_id)  # fmt: skip
        release = Release.create(self.ado_client, release_definition.release_definition_id)
        fetched_release = Release.get_by_id(self.ado_client, release.release_id)
        assert fetched_release.release_id == release.release_id
        release.delete(self.ado_client)
        release_definition.delete(self.ado_client)

    @pytest.mark.update
    @pytest.mark.skip("This test is skipped because it is not yet implemented")
    def test_update(self) -> None:
        release_definition = ReleaseDefinition.create(
            self.ado_client, "azuredevops-test-release-for-update", [], existing_agent_pool_id,  # fmt: skip
        )
        release = Release.create(self.ado_client, release_definition.release_definition_id)
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
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project, state_file_name="tests/test_state.state")

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
        # assert release_definition.to_json() == ReleaseDefinition.from_json(release_definition.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        release_definition = ReleaseDefinition.create(
            self.ado_client, "azuredevops-test-release-for-create-delete", [], existing_agent_pool_id,  # fmt: skip
        )
        release_definition.delete(self.ado_client)
        assert release_definition.description == ""
        assert release_definition.name == "azuredevops-test-release-for-create-delete"

    @pytest.mark.get_by_id
    def test_get_all_by_definition_id(self) -> None:
        release_definition = ReleaseDefinition.create(
            self.ado_client, "azuredevops-test-release-for-get-all-by-repo", [], existing_agent_pool_id  # fmt: skip
        )
        releases = ReleaseDefinition.get_all_releases_for_definition(self.ado_client, release_definition.release_definition_id)
        assert len(releases) == 0
        release_definition.delete(self.ado_client)

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        release_definition = ReleaseDefinition.create(
            self.ado_client, "azuredevops-test-release-for-get-all-by-repo", [], existing_agent_pool_id  # fmt: skip
        )
        release_definitions = ReleaseDefinition.get_all(self.ado_client)
        release_definition.delete(self.ado_client)
        assert len(release_definitions) >= 1
        assert all(isinstance(x, ReleaseDefinition) for x in release_definitions)

    @pytest.mark.update
    def test_update(self) -> None:
        release_definition = ReleaseDefinition.create(
            self.ado_client, "azuredevops-test-release-for-update", [], existing_agent_pool_id,  # fmt: skip
        )
        # ======
        release_definition.update(self.ado_client, "name", "azuredevops-test-release-for-update-rename")
        assert release_definition.name == "azuredevops-test-release-for-update-rename"  # Test instance attribute is updated
        # ======
        fetched_release_definition = ReleaseDefinition.get_by_id(self.ado_client, release_definition.release_definition_id)
        assert fetched_release_definition.name == "azuredevops-test-release-for-update-rename"
        # ======
        release_definition.delete(self.ado_client)
