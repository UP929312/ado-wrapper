import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources.build_definitions import BuildDefinition
from ado_wrapper.resources.builds import Build
from ado_wrapper.resources.commits import Commit
from ado_wrapper.resources.repo import Repo
from ado_wrapper.utils import TemporaryResource

from tests.build_definition_templates import MOST_BASIC_BUILD_YAML_FILE
from tests.setup_client import email, setup_client, REPO_PREFIX


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
                "sourceBranch": "refs/heads/main",
                "startTime": "2021-10-01T00:00:00Z",
                "finishTime": "2021-10-01T00:00:00Z",
                "queueTime": "2021-10-01T00:00:00Z",
                "reason": "test",
                "priority": "test",
                "queue": {"pool": {"id": 123}},
            }
        )
        assert build.build_id == "123"
        assert build.build_number == "456"
        assert build.status == "completed"
        assert build.to_json() == Build.from_json(build.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_build(self) -> None:
        with TemporaryResource(self.ado_client, Repo, name=REPO_PREFIX + "create-delete-builds") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-create-delete-build", repo.repo_id, "build.yaml",
                f"Please contact {email} if you see this build definition!", branch_name="my-branch",  # fmt: skip
            )
            build = Build.create(self.ado_client, build_definition.build_definition_id, "my-branch")
            assert build.build_id == Build.get_by_id(self.ado_client, build.build_id).build_id
            assert len(Build.get_all_by_definition(self.ado_client, build_definition.build_definition_id)) == 1

            build_definition.delete(self.ado_client)
            build.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        with TemporaryResource(self.ado_client, Repo, name=REPO_PREFIX + "get-builds-by-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-get-by-id", repo.repo_id, "build.yaml",
                f"Please contact {email} if you see this build definition!", branch_name="my-branch",  # fmt: skip
            )
            build = Build.create(self.ado_client, build_definition.build_definition_id, "my-branch")
            fetched_build = Build.get_by_id(self.ado_client, build.build_id)
            assert fetched_build.build_id == build.build_id
            build_definition.delete(self.ado_client)

    @pytest.mark.update
    def test_update(self) -> None:
        with TemporaryResource(self.ado_client, Repo, name=REPO_PREFIX + "update-builds") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-update", repo.repo_id, "build.yaml",
                f"Please contact {email} if you see this build definition!", branch_name="my-branch",  # fmt: skip
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
        with TemporaryResource(self.ado_client, Repo, name=REPO_PREFIX + "create-and-wait-builds") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"build.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-build-for-wait-until-completion", repo.repo_id, "build.yaml",
                f"Please contact {email} if you see this build definition!", branch_name="my-branch",  # fmt: skip
            )
            build = Build.create_and_wait_until_completion(self.ado_client, build_definition.build_definition_id, "my-branch")
            assert build.status == "completed"
            build_definition.delete(self.ado_client)  # Can't delete build_definitions without deleting builds first
            build.delete(self.ado_client)


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
