import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, TypedDict, NotRequired

from ado_wrapper.errors import ResourceNotFound
from ado_wrapper.resources.builds import Build, BuildDefinition
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string, recursively_find_or_none

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

RunResult = Literal["canceled", "failed", "succeeded", "unknown", "skipped"]
RunState = Literal["canceling", "completed", "inProgress", "unknown"]

JobResultLiteral = Literal["Queued", "Successful", "Warning", "Failed", "Cancelled", "Skipped"]
JobStateLiteral = Literal["Queued", "In-Progress", "Complete"]


class RunAllDictionary(TypedDict):
    template_parameters: NotRequired[dict[str, Any] | None]
    run_variables: NotRequired[dict[str, Any] | None]
    branch_name: NotRequired[str]
    stages_to_run: NotRequired[list[str] | None]


# ========================================================================================================


@dataclass
class Run(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs?view=azure-devops-rest-7.1"""

    run_id: str = field(metadata={"is_id_field": True})
    run_name: str
    start_time: datetime = field(repr=False)
    finish_time: datetime | None = field(repr=False)
    repo_id: str
    build_definition_id: str | None
    status: RunState
    result: RunResult
    template_parameters: dict[str, Any]

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Run":
        potential_build_def_id = recursively_find_or_none(data, ["_links", "self", "href"])
        return cls(str(data["id"]), data["name"], from_ado_date_string(data["createdDate"]), from_ado_date_string(data.get("finishedDate")),
                   recursively_find_or_none(data, ["resources", "repositories", "self", "repository", "id"]),
                   potential_build_def_id.split("/")[7] if potential_build_def_id is not None else None,
                   data["state"], data.get("result", "unknown"), data["templateParameters"])  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", pipeline_id: str, run_id: str) -> "Run":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/pipelines/{pipeline_id}/runs/{run_id}?api-version=7.1-preview.1",
        )

    @classmethod
    def create(
        cls, ado_client: "AdoClient", definition_id: str, template_parameters: dict[str, Any] | None = None,
        run_variables: dict[str, Any] | None = None, branch_name: str = "main", stages_to_run: list[str] | None = None  # fmt: skip
    ) -> "Run":
        """Creates a `Run` in ADO and returns the object. If stages_to_run isn't set (or is set to None), all stages will be run."""

        PAYLOAD: dict[str, Any] = {
            "templateParameters": template_parameters or {},
            "variables": run_variables or {},
            "resources": {"repositories": {"self": {"refName": f"refs/heads/{branch_name}"}}},
        }
        if stages_to_run is not None:
            build_stages = BuildDefinition.get_all_stages(ado_client, definition_id, branch_name)

            for name in stages_to_run:
                if name not in {stage.stage_internal_name for stage in build_stages}:
                    raise ValueError(f"The stage_name '{name}' in stages_to_run is not found in the stages.")

            PAYLOAD["stagesToSkip"] = [stage.stage_internal_name for stage in build_stages if stage.stage_internal_name not in stages_to_run]  # fmt: skip
        try:
            return super()._create(
                ado_client,
                f"/{ado_client.ado_project_name}/_apis/pipelines/{definition_id}/runs?api-version=6.1-preview.1",
                PAYLOAD,
            )
        except ValueError as e:
            # TODO: Json parse and extract this properly?
            raise ValueError(
                f"A template parameter inputted is not allowed! {str(e).split('message')[1][3:].removesuffix(':').split('.')[0]}"  # fmt: skip
            ) from e

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", run_id: str) -> None:
        Build.delete_by_id(ado_client, run_id)
        ado_client.state_manager.remove_resource_from_state("Run", run_id)

    def update(self, ado_client: "AdoClient", attribute_name: str, attribute_value: Any) -> None:
        raise NotImplementedError("Use Build's update instead!")  # Override

    @classmethod
    def get_all_by_definition(cls, ado_client: "AdoClient", pipeline_id: str) -> "list[Run]":
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/pipelines/{pipeline_id}/runs?api-version=7.1-preview.1",
        )  # pyright: ignore[reportReturnType]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def run_and_wait_until_completion(
        cls, ado_client: "AdoClient", definition_id: str, template_parameters: dict[str, Any] | None = None, run_variables: dict[str, Any] | None = None,
        branch_name: str = "main", stages_to_run: list[str] | None = None, max_timeout_seconds: int | None = 900  # fmt: skip
    ) -> "Run":
        """Creates a run and waits until it is completed, or raises a TimeoutError if it takes too long.
        WARNING: This is a blocking operation, it will not return until the run is completed or the timeout (default 15 mins) is reached."""
        data: dict[str, RunAllDictionary] = {
            definition_id: {
                "template_parameters": template_parameters, "run_variables": run_variables,
                "branch_name": branch_name, "stages_to_run": stages_to_run
            }  # fmt: skip
        }
        return cls.run_all_and_capture_results_simultaneously(ado_client, data, max_timeout_seconds)[definition_id]

    @classmethod
    def run_all_and_capture_results_sequentially(
        cls, ado_client: "AdoClient", data: dict[str, RunAllDictionary], max_timeout_seconds: int | None = 1800
    ) -> dict[str, "Run"]:
        """Takes a mapping of definition_id -> {template_parameters, run_variables, branch_name, stages_to_run}
        Once done, returns a mapping of definition_id -> `Run` object"""
        return_values = {}
        for definition_id, run_data in data.items():
            run = cls.run_and_wait_until_completion(
                ado_client, definition_id, run_data.get("template_parameters", {}), run_data.get("run_variables", {}),
                run_data.get("branch_name", "main"), run_data.get("stages_to_run"), max_timeout_seconds  # fmt: skip
            )
            return_values[definition_id] = run
        return return_values

    @classmethod
    def run_all_and_capture_results_simultaneously(
        cls, ado_client: "AdoClient", data: dict[str, RunAllDictionary], max_timeout_seconds: int | None = 1800
    ) -> dict[str, "Run"]:
        """Takes a mapping of definition_id -> {template_parameters, run_variables, branch_name, stages_to_run}
        Once done, returns a mapping of definition_id -> `Run` object"""
        # Get a mapping of definition_id -> Run()
        runs: dict[str, Run] = {}
        for definition_id, run_data in data.items():
            run = cls.create(
                ado_client, definition_id, run_data.get("template_parameters", {}), run_data.get("run_variables", {}),
                run_data.get("branch_name", "main"), run_data.get("stages_to_run"),  # fmt: skip
            )
            runs[definition_id] = run
        # Then, slowly check on them, and remove the ones that are done
        start_time = datetime.now()
        return_values: dict[str, Run] = {}
        while runs:
            for definition_id, run_obj in dict(runs.items()).items():
                run = Run.get_by_id(ado_client, definition_id, run_obj.run_id)
                if run.status == "completed":
                    return_values[definition_id] = run
                    del runs[definition_id]
                if max_timeout_seconds is not None and (datetime.now() - start_time).seconds > max_timeout_seconds:
                    raise TimeoutError(f"The run did not complete within {max_timeout_seconds} seconds ({max_timeout_seconds//60} minutes)")
                time.sleep(5)
        # Returning a mapping of definition_id -> finished Run()
        return return_values

    @classmethod
    def get_latest(cls, ado_client: "AdoClient", definition_id: str) -> "Run | None":
        all_runs = cls.get_all_by_definition(ado_client, definition_id)
        runs_with_start = [x for x in all_runs if x.start_time is not None]
        return max(runs_with_start, key=lambda run: run.start_time) if runs_with_start else None

    @staticmethod
    def get_run_stage_results(ado_client: "AdoClient", build_id: str) -> list["RunStageResult"]:
        """Fetches a list of Stages: Jobs for a Run, returning each job's status/result"""
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_build/results?view=results&buildId={build_id}&__rt=fps&__ver=2",
        )
        assert request.status_code == 200
        data = request.json()["fps"]["dataProviders"]["data"].get("ms.vss-build-web.run-details-data-provider")
        if data is None:
            raise ResourceNotFound("Could not find that build!")
        stages: dict[str, RunStageResult] = {}
        for job in data["jobs"]:
            if job["stageId"] not in stages:
                stages[job["stageId"]] = RunStageResult(job["stageId"], job["stageName"], [])
            stages[job["stageId"]].jobs.append(RunJobResult.from_request_payload(job))
        return list(stages.values())

    @classmethod
    def get_task_parents(
        cls, ado_client: "AdoClient", build_id: str, task_id: str
    ) -> tuple[str, str, str, str, str, str]:  # fmt: skip
        """Returns the task's parent stage name & id, the task's parent job name & id, as well as the task itself's name & id
        e.g. my_stage, abc, my_job, def, my_task, ghi"""
        stages_jobs_tasks = Run.get_stages_jobs_tasks(ado_client, build_id)
        for stage_name, stage_data in stages_jobs_tasks.items():  # Try get the task's stage, job and own name
            for job_name, job_data in stage_data["jobs"].items():
                for task_name, fetched_task_id in job_data["tasks"].items():
                    if fetched_task_id == task_id:
                        return stage_name, stage_data["id"], job_name, job_data["id"], task_name, fetched_task_id  # type: ignore
        raise ResourceNotFound

    # ==================================================

    get_stages_jobs_tasks = Build.get_stages_jobs_tasks
    _get_all_logs_ids = Build._get_all_logs_ids  # pylint: disable=protected-access
    get_run_log_content = Build.get_build_log_content


# ============================================================================================== #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ============================================================================================== #

job_state_mapping: dict[int, JobStateLiteral] = {
    0: "Queued",
    1: "In-Progress",
    2: "Complete",
}
job_result_mapping: dict[int | None, JobResultLiteral] = {
    None: "Queued",
    0: "Successful",
    1: "Warning",
    2: "Failed",
    3: "Cancelled",
    4: "Skipped",
}


@dataclass
class RunStageResult:
    stage_id: str
    stage_name: str
    jobs: list["RunJobResult"]


@dataclass
class RunJobResult:
    job_id: str
    name: str
    image_name: str = field(repr=False)
    start_time: datetime = field(repr=False)
    end_time: datetime | None = field(repr=False)
    state: JobStateLiteral
    result: JobResultLiteral

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "RunJobResult":
        return cls(
            str(data["id"]), data["name"], data["imageName"],
            from_ado_date_string(data["startTime"]), from_ado_date_string(data.get("finishTime")),
            job_state_mapping[data["state"]], job_result_mapping[data["result"]]
        )  # fmt: skip
