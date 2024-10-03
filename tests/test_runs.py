import time

import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.errors import ConfigurationError, UnknownError
from ado_wrapper.resources.runs import Run
from ado_wrapper.resources.build_definitions import BuildDefinition
from ado_wrapper.resources.commits import Commit

from tests.build_definition_templates import (
    MOST_BASIC_BUILD_YAML_FILE, MULTIPLE_STAGES_BUILD_YAML_FILE, TEMPLATE_PARAMS_YAML_FILE,
    TEMPLATE_VARIABLES_YAML_FILE, MULTIPLE_STAGES_WITH_DEPENDENCIES_BUILD_YAML_FILE  # fmt: skip
)
from tests.setup_client import RepoContextManager, email, setup_client


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
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-for-create-delete-run", repo.repo_id, "run.yaml",
                f"Please contact {email} if you see this run definition!", branch_name="my-branch",  # fmt: skip
            )
            run = Run.create(self.ado_client, build_definition.build_definition_id, branch_name="my-branch")
            assert run.run_id == Run.get_by_id(self.ado_client, build_definition.build_definition_id, run.run_id).run_id  # THIS LINE HERE
            assert len(Run.get_all_by_definition(self.ado_client, build_definition.build_definition_id)) == 1
            build_definition.delete(self.ado_client)
            run.delete(self.ado_client)

    @pytest.mark.get_by_id
    def test_get_by_id(self) -> None:
        with RepoContextManager(self.ado_client, "get-runs-by-id") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-for-get-by-id", repo.repo_id, "run.yaml",
                f"Please contact {email} if you see this run definition!", branch_name="my-branch",  # fmt: skip
            )
            run = Run.create(self.ado_client, build_definition.build_definition_id, branch_name="my-branch")
            fetched_run = Run.get_by_id(self.ado_client, build_definition.build_definition_id, run.run_id)
            assert fetched_run.run_id == run.run_id
            run.delete(self.ado_client)
            build_definition.delete(self.ado_client)

    @pytest.mark.skip(reason="This requires waiting for run agents, and running for a whole run")
    def test_run_and_wait_until_completion(self) -> None:
        with RepoContextManager(self.ado_client, "create-and-wait-runs") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            run_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-for-wait-until-completion", repo.repo_id, "run.yaml",
                f"Please contact {email} if you see this run definition!", branch_name="my-branch",  # fmt: skip
            )
            run = Run.run_and_wait_until_completion(self.ado_client, run_definition.build_definition_id, branch_name="my-branch")
            assert run.status == "completed"
            run_definition.delete(self.ado_client)  # Can't delete run_definitions without deleting runs first
            run.delete(self.ado_client)

    @pytest.mark.skip(reason="Takes a whole run, spams console")
    def test_run_and_wait_until_completion_with_printing(self) -> None:
        with RepoContextManager(self.ado_client, "create-and-wait-runs-with-printing") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            run_definition = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-for-wait-until-completion_with_printing", repo.repo_id, "run.yaml",
                f"Please contact {email} if you see this run definition!", branch_name="my-branch",  # fmt: skip
            )
            run = Run.run_and_wait_until_completion(
                self.ado_client,
                run_definition.build_definition_id,
                branch_name="my-branch",
                send_updates_function=lambda run: print(f"Status={run.status}, Result={run.result}"),
            )
            run_definition.delete(self.ado_client)  # Can't delete run_definitions without deleting runs first
            run.delete(self.ado_client)

    @pytest.mark.skip(reason="This requires waiting for run agents, and running for multiple runs")
    def test_run_all_and_capture_results_simultaneously(self) -> None:
        with RepoContextManager(self.ado_client, "run-all-and-capture-results-simu") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MOST_BASIC_BUILD_YAML_FILE}, "add", "Update")
            run_definition_1 = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-all-and-capture-results-simu-1", repo.repo_id, "run.yaml",
                f"Please contact {email} if you see this run definition!", branch_name="my-branch",  # fmt: skip
            )
            run_definition_2 = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-all-and-capture-results-simu-2", repo.repo_id, "run.yaml",
                f"Please contact {email} if you see this run definition!", branch_name="my-branch",  # fmt: skip
            )
            runs = Run.run_all_and_capture_results_simultaneously(
                self.ado_client,
                {
                    run_definition_1.build_definition_id: {"branch_name": "my-branch"},
                    run_definition_2.build_definition_id: {"branch_name": "my-branch"},
                },
            )
            assert runs[run_definition_1.build_definition_id].status == "completed"
            assert runs[run_definition_2.build_definition_id].status == "completed"
            run_definition_1.delete(self.ado_client)  # Can't delete run_definitions without deleting runs first
            run_definition_2.delete(self.ado_client)  # Can't delete run_definitions without deleting runs first
            for run_obj in runs.values():
                run_obj.delete(self.ado_client)

    @pytest.mark.hierarchy
    @pytest.mark.create_delete
    def test_create_delete_multiple_stages(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-multiple-stages") as repo:
            Commit.create(
                self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MULTIPLE_STAGES_BUILD_YAML_FILE}, "add", "Update"
            )
            build_definition = BuildDefinition.create_with_hierarchy(
                self.ado_client, repo.repo_id, repo.name, "run.yaml", branch_name="my-branch"
            )
            run = Run.create(
                self.ado_client,
                build_definition.build_definition_id,
                branch_name="my-branch",
                stages_to_run=["StageOne"],
            )
            time.sleep(2)
            results = run.get_run_stage_results(self.ado_client, run.run_id)
            assert results[0].jobs[0].result == "Skipped" or results[1].jobs[0].result
            build_definition.delete(self.ado_client)
            run.delete(self.ado_client)

    @pytest.mark.hierarchy
    @pytest.mark.create_delete
    def test_run_with_stages_only_working_with_hierarchy_built_build_defs(self) -> None:
        with RepoContextManager(self.ado_client, "-with-stages-only-sometimes-working") as repo:
            Commit.create(
                self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MULTIPLE_STAGES_BUILD_YAML_FILE}, "add", "Update"
            )
            # =============================================================================
            # Make both build defs
            build_def_regular = BuildDefinition.create(
                self.ado_client, "ado_wrapper-test-run-for-create-delete-run", repo.repo_id, "run.yaml",
                f"Please contact {email} if you see this run definition!", branch_name="my-branch",  # fmt: skip
            )
            build_def_hierarchy = BuildDefinition.create_with_hierarchy(
                self.ado_client, repo.repo_id, f"{repo.name}-regular", "run.yaml", "my-branch"
            )
            # Regular way fails
            with pytest.raises(UnknownError):
                run = Run.create(
                    self.ado_client, build_def_regular.build_definition_id, stages_to_run=["StageOne"], branch_name="my-branch"
                )
                run.delete(self.ado_client)

            # Normal way doesn't...
            run = Run.create(self.ado_client, build_def_hierarchy.build_definition_id, stages_to_run=["StageOne"], branch_name="my-branch")

            # Cleanup
            run.delete(self.ado_client)
            build_def_regular.delete(self.ado_client)
            build_def_hierarchy.delete(self.ado_client)

    @pytest.mark.hierarchy
    @pytest.mark.create_delete
    def test_create_run_with_template_parameters(self) -> None:
        with RepoContextManager(self.ado_client, "create_run_with_template_parameters") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": TEMPLATE_PARAMS_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create_with_hierarchy(
                self.ado_client, repo.repo_id, repo.name, "run.yaml", branch_name="my-branch"
            )
            run = Run.create(
                self.ado_client, build_definition.build_definition_id, template_parameters={"toggle": "stage2"}, branch_name="my-branch"
            )
            stages = Run.get_run_stage_results(self.ado_client, run.run_id)
            assert len(stages) == 1
            assert stages[0].stage_name == "Stage 2"
            run.delete(self.ado_client)
            build_definition.delete(self.ado_client)

    @pytest.mark.skip("Requires a run")
    @pytest.mark.create_delete
    def test_create_run_with_template_variables(self) -> None:
        with RepoContextManager(self.ado_client, "create_run_with_template_variables", delete_on_exit=False) as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": TEMPLATE_VARIABLES_YAML_FILE}, "add", "Update")
            build_definition = BuildDefinition.create(self.ado_client, repo.name, repo.repo_id, "run.yaml", branch_name="my-branch")
            with pytest.raises(ConfigurationError):
                run = Run.run_and_wait_until_completion(
                    self.ado_client, build_definition.build_definition_id, run_variables={"my_var": "bbb"}, branch_name="my-branch"
                )
                log = Run.get_run_log_content(self.ado_client, run.run_id, "Stage1", "Job1", "Print Pipeline Variable")
                assert "aaa" not in log
                assert "bbb" in log
                run.delete(self.ado_client)
                build_definition.delete(self.ado_client)

    @pytest.mark.hierarchy
    def test_run_stage_results(self) -> None:
        with RepoContextManager(self.ado_client, "run-stage-results") as repo:
            Commit.create(
                self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MULTIPLE_STAGES_BUILD_YAML_FILE}, "add", "Update"
            )
            build_definition = BuildDefinition.create_with_hierarchy(
                self.ado_client, repo.repo_id, repo.name, "run.yaml", branch_name="my-branch"
            )
            run = Run.create(self.ado_client, build_definition.build_definition_id, branch_name="my-branch")
            results = run.get_run_stage_results(self.ado_client, run.run_id)
            assert len(results) == 2
            build_definition.delete(self.ado_client)
            run.delete(self.ado_client)

    @pytest.mark.skip("Requires a run")
    @pytest.mark.hierarchy
    def test_get_stages_jobs_tasks(self) -> None:
        with RepoContextManager(self.ado_client, "get-task-parents") as repo:
            Commit.create(self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MULTIPLE_STAGES_BUILD_YAML_FILE}, "add", "Update")  # fmt: skip
            build_definition = BuildDefinition.create_with_hierarchy(self.ado_client, repo.repo_id, repo.name, "run.yaml", "my-branch")
            run = Run.run_and_wait_until_completion(self.ado_client, build_definition.build_definition_id, branch_name="my-branch")
            stages_jobs_steps = Run.get_stages_jobs_tasks(self.ado_client, run.run_id)
            task_id = stages_jobs_steps["StageOne"]["jobs"]["JobOne"]["tasks"]["Task1"]  # Check nesting
            assert task_id
            run.delete(self.ado_client)
            build_definition.delete(self.ado_client)

    @pytest.mark.skip("Requires a run")
    @pytest.mark.hierarchy
    def test_get_build_log_contents(self) -> None:
        with RepoContextManager(self.ado_client, "get-build-log-contents") as repo:
            Commit.create(
                self.ado_client, repo.repo_id, "main", "my-branch", {"run.yaml": MULTIPLE_STAGES_BUILD_YAML_FILE}, "add", "Update"
            )
            build_definition = BuildDefinition.create_with_hierarchy(
                self.ado_client, repo.repo_id, repo.name, "run.yaml", branch_name="my-branch"
            )
            run = Run.run_and_wait_until_completion(self.ado_client, build_definition.build_definition_id, branch_name="my-branch")
            log = Run.get_run_log_content(self.ado_client, run.run_id, "StageOne", "JobOne", "Task1")
            assert "Hello, world!" in log
            run.delete(self.ado_client)
            build_definition.delete(self.ado_client)

    @pytest.mark.skip("Requires a run")
    @pytest.mark.hierarchy
    def test_get_root_stage_names(self) -> None:
        with RepoContextManager(self.ado_client, "get-root-stage-names") as repo:
            Commit.create(
                self.ado_client, repo.repo_id, "main", "my-branch",
                {"run.yaml": MULTIPLE_STAGES_WITH_DEPENDENCIES_BUILD_YAML_FILE}, "add", "Update",
            )  # fmt: skip
            build_definition = BuildDefinition.create_with_hierarchy(self.ado_client, repo.repo_id, repo.name, "run.yaml", "my-branch")
            run = Run.run_and_wait_until_completion(self.ado_client, build_definition.build_definition_id, branch_name="my-branch")
            root_stage_name = Run.get_root_stage_names(self.ado_client, run.run_id)
            assert root_stage_name == ["StageOne"]
            run.delete(self.ado_client)
            build_definition.delete(self.ado_client)


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
