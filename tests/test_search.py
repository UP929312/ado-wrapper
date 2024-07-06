import pytest

from ado_wrapper.resources.searches import Search, CodeSearchHit
from tests.setup_client import setup_client  # fmt: skip


class TestSearch:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        search = Search.from_request_payload(
            {
                "repository": {"name": "test-repo", "id": "123456789"},
                "path": "test/path/here.txt",
                "fileName": "here.txt",
                "project": {"name": "my-test-project"},
                "versions": [{"branchName": "test-branch"}],
                "matches": {
                    "content": [
                        {
                            "charOffset": 0,
                            "length": 1,
                            "line": 1,
                            "column": 1,
                            "codeSnippet": None,
                            "type": "content",
                        },
                    ],
                },
            }
        )
        assert search.repository_name == "test-repo"
        assert search.repository_id == "123456789"
        assert search.path == "test/path/here.txt"
        assert search.file_name == "here.txt"
        assert search.project == "my-test-project"
        assert search.branch_name == "test-branch"
        assert search.matches == [CodeSearchHit(0, 1, 1, 1, None, "content")]

    # @pytest.mark.create_delete
    # def test_create_delete_run(self) -> None:
    #     with RepoContextManager(self.ado_client, "create-delete-runs") as repo:
    #         Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": BUILD_YAML_FILE}, "add", "Update")
    #         build_definition = BuildDefinition.create(
    #             self.ado_client, "ado_wrapper-test-run-for-create-delete-run", repo.repo_id, repo.name, "run.yaml",
    #             f"Please contact {email} if you see this run definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
    #         )
    #         run = Run.create(self.ado_client, build_definition.build_definition_id, {}, "my-branch")
    #         assert run.run_id == Run.get_by_id(self.ado_client, build_definition.build_definition_id, run.run_id).run_id  # THIS LINE HERE
    #         assert len(Run.get_all_by_definition(self.ado_client, build_definition.build_definition_id)) == 1
    #         build_definition.delete(self.ado_client)
    #         run.delete(self.ado_client)

    # @pytest.mark.get_by_id
    # def test_get_by_id(self) -> None:
    #     with RepoContextManager(self.ado_client, "get-runs-by-id") as repo:
    #         Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": BUILD_YAML_FILE}, "add", "Update")
    #         build_definition = BuildDefinition.create(
    #             self.ado_client, "ado_wrapper-test-run-for-get-by-id", repo.repo_id, repo.name, "run.yaml",
    #             f"Please contact {email} if you see this run definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
    #         )
    #         run = Run.create(self.ado_client, build_definition.build_definition_id, {}, "my-branch")
    #         fetched_run = Run.get_by_id(self.ado_client, build_definition.build_definition_id, run.run_id)
    #         assert fetched_run.run_id == run.run_id
    #         build_definition.delete(self.ado_client)

    # @pytest.mark.skip(reason="This requires waiting for run agents, and running for a whole run")
    # def test_run_and_wait_until_completion(self) -> None:
    #     with RepoContextManager(self.ado_client, "create-and-wait-runs") as repo:
    #         Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": BUILD_YAML_FILE}, "add", "Update")
    #         run_definition = BuildDefinition.create(
    #             self.ado_client, "ado_wrapper-test-run-for-wait-until-completion", repo.repo_id, repo.name, "run.yaml",
    #             f"Please contact {email} if you see this run definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
    #         )
    #         run = Run.run_and_wait_until_completion(self.ado_client, run_definition.build_definition_id, {}, "my-branch")
    #         assert run.status == "completed"
    #         run_definition.delete(self.ado_client)  # Can't delete run_definitions without deleting runs first
    #         run.delete(self.ado_client)
