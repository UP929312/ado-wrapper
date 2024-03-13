from datetime import datetime

from client import AdoClient
from repository import Repo
from builds import Build, BuildDefinition
from users import Member

with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, existing_repo_name, existing_repo_id, *_ = test_data.read().splitlines()


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
        build_definition = BuildDefinition.from_request_payload({
            "id": "123",
            "name": "test-repo",
            "description": "test-repo",
            "process": {"yamlFilename": "test-repo"},
            "authoredBy": {"displayName": "test", "uniqueName": "test", "id": "123"},
            "createdDate": "2021-10-01T00:00:00Z",
            "repository": {"id": "123", "name": "test-repo"},
            "variables": {},
            "variableGroups": [],
        })
        assert build_definition.build_definition_id == "123"
        assert build_definition.name == "test-repo"
        assert isinstance(build_definition.created_by, Member)
        assert isinstance(build_definition.created_date, datetime)

    # def test_create_delete_build(self) -> None:
    #     build = Build.create(self.ado_client, "ado-api-test-repo")
    #     assert repo.name == "ado-api-test-repo"
    #     repo.delete(self.ado_client)

    # def test_get_all_repos(self) -> None:
    #     repos = Repo.get_all(self.ado_client)
    #     assert len(repos) > 10
    #     assert all([isinstance(repo, Repo) for repo in repos])

    # def test_get_by_name(self) -> None:
    #     repo = Repo.get_by_name(self.ado_client, existing_repo_name)
    #     assert repo.name == existing_repo_name

    # def test_get_by_id(self) -> None:
    #     repo = Repo.get_by_id(self.ado_client, existing_repo_id)
    #     assert repo.repo_id == existing_repo_id

    # def test_get_file(self) -> None:
    #     repo = Repo.get_by_name(self.ado_client, existing_repo_name)
    #     file = repo.get_file(self.ado_client, "README.md")
    #     assert len(file) > 10

    # def test_get_repo_contents(self) -> None:
    #     repo = Repo.get_by_name(self.ado_client, existing_repo_name)
    #     contents = repo.get_repo_contents(self.ado_client)
    #     assert len(contents) > 10
    #     assert isinstance(contents, dict)
