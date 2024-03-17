from datetime import datetime

import pytest

from client import AdoClient
from resources.branches import Branch
from resources.repo import Repo
from resources.users import Member
from resources.commits import Commit


with open("tests/test_data.txt", "r", encoding="utf-8") as test_data:
    ado_org, ado_project, email, pat_token, *_ = test_data.read().splitlines()


class TestBranch:
    def setup_method(self) -> None:
        self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

    def test_from_request_payload(self) -> None:
        branch = Branch.from_request_payload(
            {
                "name": "main",
                "isMain": True,
                "isDeleted": False,
                "isProtected": True,
                "objectId": "123",
                "url": "https://dev.azure.com/...",
                "repository": {"id": "123", "name": "test-repo"},
            }
        )
        assert branch.to_json() == Branch.from_json(branch.to_json()).to_json()


    def test_create_delete_branch(self) -> None:
        repo = Repo.create(self.ado_client, "ado-api-test-repo-for-branches")
        with pytest.raises(NotImplementedError):
            Branch.create(self.ado_client, "", "branch", "main")
        Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"text.txt": "Contents of the file"}, "add", "Test commmit 1")
        branch = Branch.get_all_by_repo(self.ado_client, repo.repo_id)
        assert branch[0].name == "refs/heads/test-branch" or branch[1].name == "refs/heads/test-branch"
        repo.delete(self.ado_client)

# ======================================================================================================================


# class TestBuildDefinition:
#     def setup_method(self) -> None:
#         self.ado_client = AdoClient(email, pat_token, ado_org, ado_project)

#     def test_from_request_payload(self) -> None:
#         build_definition = BuildDefinition.from_request_payload(
#             {
#                 "id": "123",
#                 "name": "test-repo",
#                 "description": "test-repo",
#                 "process": {"yamlFilename": "test-repo"},
#                 "authoredBy": {"displayName": "test", "uniqueName": "test", "id": "123"},
#                 "createdDate": "2021-10-01T00:00:00Z",
#                 "repository": {"id": "123", "name": "test-repo"},
#                 "variables": {},
#                 "variableGroups": [],
#             }
#         )
#         assert build_definition.build_definition_id == "123"
#         assert build_definition.name == "test-repo"
#         assert isinstance(build_definition.created_by, Member)
#         assert isinstance(build_definition.created_date, datetime)
#         assert build_definition.to_json() == BuildDefinition.from_json(build_definition.to_json()).to_json()

#     def test_create_delete_build(self) -> None:
#         repo = Repo.create(self.ado_client, "ado-api-test-repo-for-builds")
#         _ = (Commit.create(self.ado_client, repo.repo_id, "main", {"build.yaml": BUILD_YAML_FILE}, "add"),)
#         build_definition = BuildDefinition.create(
#             self.ado_client, "ado-api-test-build", repo.repo_id, "ado-api-test-repo", "build.yaml",
#             f"Please contact {email} if you see this build definition!", existing_agent_pool_id,  # fmt: skip
#         )
#         assert build_definition.description == f"Please contact {email} if you see this build definition!"
#         build_definition.delete(self.ado_client)
#         repo.delete(self.ado_client)

#     def test_get_all_by_repo_id(self) -> None:
#         build_definitions = BuildDefinition.get_all_by_repo_id(self.ado_client, existing_repo_id)
#         assert len(build_definitions) == 0
#         assert all(isinstance(x, BuildDefinition) for x in build_definitions)
