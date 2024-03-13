from datetime import datetime

from client import AdoClient
from repository import Repo
from builds import Build, BuildDefinition
from users import Member
from commits import Commit

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    (
        ado_org, ado_project, email, pat_token, existing_repo_name, existing_repo_id, _, _, _, _, _, existing_agent_pool_id,
        *_  # fmt: skip
    ) = test_data.read().splitlines()  # type: ignore[assignment]

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
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

    def test_from_request_payload(self) -> None:
        repo = Build.from_request_payload(
            {
                "requestedBy": {"displayName": "test", "uniqueName": "test", "id": "123"},
                "repository": {"id": "123", "name": "test-repo"},
                "id": "123",
                "buildNumber": "123",
                "status": "completed",
                "templateParameters": {},
                "startTime": "2021-10-01T00:00:00Z",
                "finishTime": "2021-10-01T00:00:00Z",
                "queueTime": "2021-10-01T00:00:00Z",
                "reason": "manual",
                "priority": "normal",
            }
        )
        assert repo.build_id == "123"
        assert repo.build_number == "123"


class TestBuildDefinition:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

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
            }
        )
        assert build_definition.build_definition_id == "123"
        assert build_definition.name == "test-repo"
        assert isinstance(build_definition.created_by, Member)
        assert isinstance(build_definition.created_date, datetime)

    def test_create_delete_build(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-builds")
        _ = (Commit.create(self.ado_client, repo.repo_id, "main", {"build.yaml": BUILD_YAML_FILE}, "add"),)
        build_definition = BuildDefinition.create(
            self.ado_client, "ado-api-test-build", repo.repo_id, "ado-api-test-repo", "build.yaml",
            "my-test-description", existing_agent_pool_id,  # fmt: skip
        )
        assert build_definition.description == "my-test-description"
        build_definition.delete(self.ado_client)
        repo.delete(self.ado_client)
