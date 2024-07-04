import pytest

from ado_wrapper.resources.runs import Run
from ado_wrapper.resources.builds import BuildDefinition
from ado_wrapper.resources.commits import Commit
from tests.setup_client import RepoContextManager, email, existing_agent_pool_id, setup_client  # fmt: skip

BUILD_YAML_FILE = """---
trigger:
  - main

pool:
  vmImage: ubuntu-latest

steps:
  - script: echo Hello, world!
    displayName: 'Run a one-line script'"""


class TestRun:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        run = Run.from_request_payload(
            {
                "id": "123",
                "name": "456",
                "state": "completed",
                "repository": {"id": "123", "name": "test-repo"},
                "templateParameters": {"test": "data"},
                "createdDate": "2021-10-01T00:00:00Z",
                "finishedDate": "2021-10-01T00:00:00Z",
            }
        )
        assert run.run_id == "123"
        # assert run.bu == "456"
        assert run.status == "completed"
        assert run.to_json() == Run.from_json(run.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_run(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-runs") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-for-create-delete-run", repo.repo_id, repo.name, "run.yaml",
                f"Please contact {email} if you see this run definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
            )
            run = Run.create(self.ado_client, build_definition.build_definition_id, {}, "my-branch")
            assert run.run_id == Run.get_by_id(self.ado_client, build_definition.build_definition_id, run.run_id).run_id  # THIS LINE HERE
            assert len(Run.get_all_by_definition(self.ado_client, build_definition.build_definition_id)) == 1
            build_definition.delete(self.ado_client)
            run.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        with RepoContextManager(self.ado_client, "get-runs-by-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-for-get-by-id", repo.repo_id, repo.name, "run.yaml",
                f"Please contact {email} if you see this run definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
            )
            run = Run.create(self.ado_client, build_definition.build_definition_id, {}, "my-branch")
            fetched_run = Run.get_by_id(self.ado_client, build_definition.build_definition_id, run.run_id)
            assert fetched_run.run_id == run.run_id
            build_definition.delete(self.ado_client)

    @pytest.mark.skip(reason="This requires waiting for run agents, and running for a whole run")
    def test_run_and_wait_until_completion(self) -> None:
        with RepoContextManager(self.ado_client, "create-and-wait-runs") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": BUILD_YAML_FILE}, "add", "Update")
            run_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-for-wait-until-completion", repo.repo_id, repo.name, "run.yaml",
                f"Please contact {email} if you see this run definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
            )
            run = Run.run_and_wait_until_completion(self.ado_client, run_definition.build_definition_id, {}, "my-branch")
            assert run.status == "completed"
            run_definition.delete(self.ado_client)  # Can't delete run_definitions without deleting runs first
            run.delete(self.ado_client)

    @pytest.mark.skip(reason="This requires waiting for run agents, and running for multiple runs")
    def test_run_all_and_capture_results_simultaneously(self) -> None:
        with RepoContextManager(self.ado_client, "run-all-and-capture-results-simu") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": BUILD_YAML_FILE}, "add", "Update")
            run_definition_1 = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-all-and-capture-results-simu-1", repo.repo_id, repo.name, "run.yaml",
                f"Please contact {email} if you see this run definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
            )
            run_definition_2 = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-all-and-capture-results-simu-2", repo.repo_id, repo.name, "run.yaml",
                f"Please contact {email} if you see this run definition!", existing_agent_pool_id, "my-branch",  # fmt: skip
            )
            runs = Run.run_all_and_capture_results_simultaneously(
                self.ado_client, {
                    run_definition_1.build_definition_id: {"template_variables": {}, "branch_name": "main"},
                    run_definition_2.build_definition_id: {"template_variables": {}, "branch_name": "main"},
                }
            )
            assert runs[run_definition_1.build_definition_id].status == "completed"
            assert runs[run_definition_2.build_definition_id].status == "completed"
            run_definition_1.delete(self.ado_client)  # Can't delete run_definitions without deleting runs first
            run_definition_2.delete(self.ado_client)  # Can't delete run_definitions without deleting runs first
            for run_obj in runs.values():
                run_obj.delete(self.ado_client)
