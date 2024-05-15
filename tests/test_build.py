from datetime import datetime

import pytest

from ado_wrapper.resources.builds import Build, BuildDefinition
from ado_wrapper.resources.commits import Commit
from ado_wrapper.resources.users import Member
from tests.setup_client import (
    RepoContextManager,
    email,
    existing_agent_pool_id,
    setup_client,
)

BUILD_YAML_FILE = """---
trigger:
  - main

pool:
  vmImage: ubuntu-latest

steps:
  - script: echo Hello, world!
    displayName: 'Run a one-line script'"""


class TestBuild:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        build = Build.from_request_payload(
            {
                "id": "123",
                "buildNumber": 456,
                "status": "completed",
                "requestedBy": {"displayName": "test", "uniqueName": "test", "id": "123"},
                "repository": {"id": "123", "name": "test-repo"},
                "templateParameters": "test",
                "startTime": "2021-10-01T00:00:00Z",
                "finishTime": "2021-10-01T00:00:00Z",
                "queueTime": "2021-10-01T00:00:00Z",
                "reason": "test",
                "priority": "test",
            }
        )
        assert build.build_id == "123"
        assert build.build_number == "456"
        assert build.status == "completed"
        assert build.to_json() == Build.from_json(build.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_build(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-builds") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-buildfor-create-delete-build", repo.repo_id, repo.name, "build.yaml",
                f"Please contact {email} if you see this build definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
            )
            build = Build.create(self.ado_client, build_definition.build_definition_id, "my-branch")
            assert build.build_id == Build.get_by_id(self.ado_client, build.build_id).build_id
            assert len(Build.get_all_by_definition(self.ado_client, build_definition.build_definition_id)) == 1
            build_definition.delete(self.ado_client)
            build.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        with RepoContextManager(self.ado_client, "get-builds-by-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-get-by-id", repo.repo_id, repo.name, "build.yaml",
                f"Please contact {email} if you see this build definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
            )
            build = Build.create(self.ado_client, build_definition.build_definition_id, "my-branch")
            fetched_build = Build.get_by_id(self.ado_client, build.build_id)
            assert fetched_build.build_id == build.build_id
            build_definition.delete(self.ado_client)

    @pytest.mark.update
    def test_update(self) -> None:
        with RepoContextManager(self.ado_client, "update-builds") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-update", repo.repo_id, repo.name, "build.yaml",
                f"Please contact {email} if you see this build definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
            )
            build = Build.create(self.ado_client, build_definition.build_definition_id, "my-branch")
            # ======
            build.update(self.ado_client, "status", "completed")
            assert build.status == "completed"
            # ======
            fetched_build = Build.get_by_id(self.ado_client, build.build_id)
            assert fetched_build.status == "completed"
            # ======
            build_definition.delete(self.ado_client)

    @pytest.mark.skip(reason="This requires waiting for build agents, and running a whole build")
    def test_create_and_wait_until_completion(self) -> None:
        with RepoContextManager(self.ado_client, "create-and-wait-builds") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-wait-until-completion", repo.repo_id, repo.name, "build.yaml",
                f"Please contact {email} if you see this build definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
            )
            build = Build.create_and_wait_until_completion(self.ado_client, build_definition.build_definition_id, "my-branch")
            assert build.status == "completed"
            build_definition.delete(self.ado_client)  # Can't delete build_definitions without deleting builds first
            build.delete(self.ado_client)


# ======================================================================================================================


class TestBuildDefinition:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        build_definition = BuildDefinition.from_request_payload(
            {
                "id": "123",
                "name": "test-repo",
                "description": "test-repo",
                "process": {"yamlFilename": "test-repo"},
                "authoredBy": {"displayName": "test", "uniqueName": "test", "id": "123"},
                "createdDate": "2021-10-01T00:00:00Z",
                "repository": {"id": "123", "name": "test-repo"},
                "variables": {},
                "variableGroups": [],
                "revision": 1,
            }
        )
        assert build_definition.build_definition_id == "123"
        assert build_definition.name == "test-repo"
        assert isinstance(build_definition.created_by, Member)
        assert isinstance(build_definition.created_date, datetime)
        assert build_definition.to_json() == BuildDefinition.from_json(build_definition.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-build-defs") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"build.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-create-delete", repo.repo_id, "ado_wrapper-test-repo", "build.yaml",
                f"Please contact {email} if you see this build definition!", existing_agent_pool_id, "test-branch"  # fmt: skip
            )
            assert build_definition.description == f"Please contact {email} if you see this build definition!"
            build_definition.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        with RepoContextManager(self.ado_client, "get-build-defs-by-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"build.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-get-by-id", repo.repo_id, "ado_wrapper-test-repo", "build.yaml",
                f"Please contact {email} if you see this build definition!", existing_agent_pool_id, "test-branch"  # fmt: skip
            )
            fetched_build_definition = BuildDefinition.get_by_id(self.ado_client, build_definition.build_definition_id)
            assert fetched_build_definition.build_definition_id == build_definition.build_definition_id
            build_definition.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_all_by_repo_id(self) -> None:
        with RepoContextManager(self.ado_client, "get-all-build-defs-by-repo-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"build.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-get-all-by-repo", repo.repo_id, "ado_wrapper-test-repo", "build.yaml",
                f"Please contact {email} if you see this build definition!", existing_agent_pool_id, "test-branch"  # fmt: skip
            )
            build_definitions = BuildDefinition.get_all_by_repo_id(self.ado_client, repo.repo_id)
            assert len(build_definitions) == 1
            assert all(isinstance(x, BuildDefinition) for x in build_definitions)
            build_definition.delete(self.ado_client)

    @pytest.mark.update
    def test_update(self) -> None:
        with RepoContextManager(self.ado_client, "update-build-defs") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"build.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-update", repo.repo_id, "ado_wrapper-test-repo", "build.yaml",
                f"Please contact {email} if you see this build definition!", existing_agent_pool_id, "test-branch"  # fmt: skip
            )
            # ======
            build_definition.update(self.ado_client, "name", "ado_wrapper-test-build-for-update-rename")
            assert build_definition.name == "ado_wrapper-test-build-for-update-rename"  # Test instance attribute is updated
            build_definition.update(self.ado_client, "description", "new-description")
            assert build_definition.description == "new-description"  # Test instance attribute is updated
            # ======
            fetched_build_definition = BuildDefinition.get_by_id(self.ado_client, build_definition.build_definition_id)
            assert fetched_build_definition.name == "ado_wrapper-test-build-for-update-rename"
            assert fetched_build_definition.description == "new-description"
            # ======
            build_definition.delete(self.ado_client)
