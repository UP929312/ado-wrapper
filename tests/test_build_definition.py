from datetime import datetime

import pytest

if __name__ == "__main__":
    __import__('sys').path.insert(0, __import__('os').path.abspath(__import__('os').path.dirname(__file__) + '/..'))

from ado_wrapper.resources.build_definitions import BuildDefinition, HierarchyCreatedBuildDefinition
from ado_wrapper.resources.commits import Commit
from ado_wrapper.resources.users import Member
from tests.build_definition_templates import MOST_BASIC_BUILD_YAML_FILE
from tests.setup_client import RepoContextManager, email, setup_client  # fmt: skip


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
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-create-delete", repo.repo_id, "build.yaml",
                f"Please contact {email} if you see this build definition!", branch_name="test-branch"  # fmt: skip
            )
            assert build_definition.description == f"Please contact {email} if you see this build definition!"
            build_definition.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        with RepoContextManager(self.ado_client, "get-build-defs-by-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-get-by-id", repo.repo_id, "build.yaml",
                f"Please contact {email} if you see this build definition!", branch_name="test-branch"  # fmt: skip
            )
            fetched_build_definition = BuildDefinition.get_by_id(self.ado_client, build_definition.build_definition_id)
            assert fetched_build_definition.build_definition_id == build_definition.build_definition_id
            build_definition.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_all_by_repo_id(self) -> None:
        with RepoContextManager(self.ado_client, "get-all-build-defs-by-repo-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-get-all-by-repo", repo.repo_id, "build.yaml",
                f"Please contact {email} if you see this build definition!", branch_name="test-branch"  # fmt: skip
            )
            build_definitions = BuildDefinition.get_all_by_repo_id(self.ado_client, repo.repo_id)
            assert len(build_definitions) == 1
            assert all(isinstance(x, BuildDefinition) for x in build_definitions)
            build_definition.delete(self.ado_client)

    @pytest.mark.update
    def test_update(self) -> None:
        with RepoContextManager(self.ado_client, "update-build-defs") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-update", repo.repo_id, "build.yaml",
                f"Please contact {email} if you see this build definition!", branch_name="test-branch"  # fmt: skip
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

    @pytest.mark.create_delete
    def test_create_delete_with_hierarchy(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-def-with-hierarchy") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "test-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            hierarchy_created_build_definition = BuildDefinition.create_with_hierarchy(
                self.ado_client, repo.repo_id, repo.name, "build.yaml", branch_name="test-branch"
            )
            build_def = HierarchyCreatedBuildDefinition.get_by_id(self.ado_client, hierarchy_created_build_definition.build_definition_id)
            assert build_def.build_definition_id == hierarchy_created_build_definition.build_definition_id
            assert hierarchy_created_build_definition.name in (
                f"{repo.name}",
                f"{repo.name} ({hierarchy_created_build_definition.build_definition_id})",
            )
            hierarchy_created_build_definition.delete(self.ado_client)


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
