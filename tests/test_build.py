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

    def test_create_delete_build(self) -> None:
        build_definition = BuildDefinition.create(
            self.ado_client, "ado-api-test-build", existing_repo_id, existing_repo_name, "build.yaml",
            f"Please contact {email} if you see this build definition!", existing_agent_pool_id,  # fmt: skip
        )
        build = Build.create(self.ado_client, build_definition.build_definition_id)
        assert build.build_id == Build.get_by_id(self.ado_client, build.build_id).build_id
        assert len(Build.get_all_by_definition(self.ado_client, build_definition.build_definition_id)) == 1
        build_definition.delete(self.ado_client)
        build.delete(self.ado_client)


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
            f"Please contact {email} if you see this build definition!", existing_agent_pool_id,  # fmt: skip
        )
        assert build_definition.description == f"Please contact {email} if you see this build definition!"
        build_definition.delete(self.ado_client)
        repo.delete(self.ado_client)

    def test_get_all_by_repo_id(self) -> None:
        build_definitions = BuildDefinition.get_all_by_repo_id(self.ado_client, existing_repo_id)
        assert len(build_definitions) == 0
        assert all(isinstance(x, BuildDefinition) for x in build_definitions)
