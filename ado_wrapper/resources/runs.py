import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Literal, TypedDict, NotRequired, Any

from ado_wrapper.resources.builds import Build
from ado_wrapper.resources.build_definitions import BuildDefinition
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.errors import ResourceNotFound, ConfigurationError
from ado_wrapper.utils import from_ado_date_string, recursively_find_or_none, requires_initialisation

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

DEFAULT_TIMEOUT_FOR_BUILD = 900

RunResult = Literal["canceled", "failed", "succeeded", "unknown", "skipped"]
RunState = Literal["canceling", "completed", "inProgress", "unknown"]

# TODO: Should this include succeededWithErrors? VVV
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
    def get_by_id(cls, ado_client: "AdoClient", build_definition_id: str, run_id: str) -> "Run":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/pipelines/{build_definition_id}/runs/{run_id}?api-version=7.1-preview.1",
        )

    @classmethod
    def create(
        cls, ado_client: "AdoClient", definition_id: str, template_parameters: dict[str, Any] | None = None,
        run_variables: dict[str, Any] | None = None, branch_name: str = "main", stages_to_run: list[str] | None = None  # fmt: skip
    ) -> "Run":
        """Creates a `Run` in ADO and returns the object. If stages_to_run isn't set (or is set to None), all stages will be run."""
        if run_variables is not None:
            requires_initialisation(ado_client)  # Because ado_project_pipeline_settings is set in initialisation
            if ado_client.ado_project_pipeline_settings["enforceSettableVar"]:
                raise ConfigurationError("Run-time variables are disable project wide, please enable them to set run variables.")
        PAYLOAD: dict[str, Any] = {
            "templateParameters": template_parameters or {},
            "variables": {key: {"value": value} for key, value in run_variables.items()} if run_variables is not None else {},
            "resources": {"repositories": {"self": {"refName": f"refs/heads/{branch_name}"}}},
        }
        if stages_to_run is not None:
            _stages_to_run = list(stages_to_run)  # Shallow copy the stages to run to prevent overriding input
            build_stages = BuildDefinition.get_all_stages(ado_client, definition_id, template_parameters, branch_name)
            stage_mapping = {stage.stage_display_name: stage.stage_internal_name for stage in build_stages}

            for i, name in enumerate(_stages_to_run):
                if name in stage_mapping.keys():  # If it's a display name, not internal name
                    _stages_to_run[i] = stage_mapping[name]  # Replace it with the internal name
                    continue
                if name not in stage_mapping.values():
                    raise ValueError(f"The stage_name '{name}' in stages_to_run is not found in the stages.")

            PAYLOAD["stagesToSkip"] = [stage.stage_internal_name for stage in build_stages if stage.stage_internal_name not in _stages_to_run]  # fmt: skip
        try:
            return super()._create(
                ado_client,
                f"/{ado_client.ado_project_name}/_apis/pipelines/{definition_id}/runs?api-version=6.1-preview.1",
                PAYLOAD,
            )
        except ValueError as e:
            # {"$id":"1","innerException":null,"message":"See https://aka.ms/AzPipelines/SettingVariablesAtQueueTime - You can't set the following variables (my_var). If you want to be able to set these variables, then edit the pipeline and select Settable at queue time on the variables tab of the pipeline editor.","typeName":"Microsoft.Azure.Pipelines.WebApi.PipelineValidationException, Microsoft.Azure.Pipelines.WebApi","typeKey":"PipelineValidationException","errorCode":0,"eventId":3000}
            # raise ValueError(str(e))
            # try:
            #     data = json.loads(str(e))
            #     raise ValueError(
            #         e
            #     )
            # except:
            #     print(e)
            # TODO: Properly parse this message with json
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
        cls, ado_client: "AdoClient", definition_id: str, template_parameters: dict[str, Any] | None = None,
        run_variables: dict[str, Any] | None = None, branch_name: str = "main",
        stages_to_run: list[str] | None = None, max_timeout_seconds: int | None = DEFAULT_TIMEOUT_FOR_BUILD,
        send_updates_function: Callable[["Run"], None] = lambda run: None,  # fmt: skip
    ) -> "Run":
        """Creates a run and waits until it is completed, or raises a TimeoutError if it takes too long.
        WARNING: This is a blocking operation, it will not return until the run is completed or the timeout (default 15 mins) is reached.
        Send updates function is for dispatching events every time the build is fetched to check completion"""
        data: dict[str, RunAllDictionary] = {
            definition_id: {
                "template_parameters": template_parameters, "run_variables": run_variables,
                "branch_name": branch_name, "stages_to_run": stages_to_run
            }  # fmt: skip
        }
        return cls.run_all_and_capture_results_simultaneously(ado_client, data, max_timeout_seconds, send_updates_function)[0]

    @classmethod
    def run_all_and_capture_results_sequentially(
        cls,
        ado_client: "AdoClient",
        data: dict[str, RunAllDictionary],
        max_timeout_seconds: int | None = DEFAULT_TIMEOUT_FOR_BUILD,
        send_updates_function: Callable[["Run"], None] = lambda run: None,
    ) -> list["Run"]:
        """Takes a mapping of definition_id -> {template_parameters, run_variables, branch_name, stages_to_run}
        Once done, returns a list of `Run` objects, in the order they completed."""
        return_values: list[Run] = []
        for definition_id, run_data in data.items():
            run = cls.run_and_wait_until_completion(
                ado_client, definition_id, run_data.get("template_parameters", {}), run_data.get("run_variables", {}),
                run_data.get("branch_name", "main"), run_data.get("stages_to_run"), max_timeout_seconds,
                send_updates_function,  # fmt: skip
            )
            return_values.append(run)
        return return_values

    @classmethod
    def run_all_and_capture_results_simultaneously(
        cls,
        ado_client: "AdoClient",
        data: dict[str, RunAllDictionary],
        max_timeout_seconds: int | None = DEFAULT_TIMEOUT_FOR_BUILD,
        send_updates_function: Callable[["Run"], None] = lambda run: None,
    ) -> list["Run"]:
        """Takes a mapping of definition_id -> {template_parameters, run_variables, branch_name, stages_to_run}
        Once done, returns a list of `Run` objects, in the order they completed."""
        return_values: list[Run] = []
        runs: list[Run] = [
            cls.create(
                ado_client, definition_id, run_data.get("template_parameters", {}), run_data.get("run_variables", {}),
                run_data.get("branch_name", "main"), run_data.get("stages_to_run"),  # fmt: skip
            )
            for definition_id, run_data in data.items()
        ]
        start_time = datetime.now()
        # Then, slowly check on them, and remove the ones that are done
        while runs:
            for planned_run_obj in runs[:]:  # We do this to make a copy of the list
                try:
                    run = Run.get_by_id(ado_client, planned_run_obj.build_definition_id, planned_run_obj.run_id)  # type: ignore[arg-type]
                except Exception:
                    print(f"Failed to fetch run with id: {planned_run_obj.run_id}")
                    continue  # TODO: Error handling on this, in case it fails (will ruin all runs)
                send_updates_function(run)
                if run.status == "completed":
                    return_values.append(run)
                    runs = [x for x in runs if x.run_id != run.run_id]  # Remove the run from the list of ones to check
                if max_timeout_seconds is not None and (datetime.now() - start_time).seconds > max_timeout_seconds:
                    # TODO: What if only one run failed, maybe put the max_timeout_seconds in the run_data?
                    raise TimeoutError(f"The run did not complete within {max_timeout_seconds} seconds ({max_timeout_seconds//60} minutes)")
                time.sleep(ado_client.run_polling_interval_seconds)
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
        data = request.json()["fps"]["dataProviders"]["data"].get("ms.vss-build-web.run-details-data-provider")
        if data is None:
            raise ResourceNotFound("Could not find that build!")
        stages: dict[str, RunStageResult] = {}
        for job in data["jobs"]:
            if job["stageId"] not in stages:
                stages[job["stageId"]] = RunStageResult(job["stageId"], job["stageName"], [])
            stages[job["stageId"]].jobs.append(RunJobResult.from_request_payload(job))
        return list(stages.values())

    # ==================================================

    get_stages_jobs_tasks = Build.get_stages_jobs_tasks
    _get_all_logs_ids = Build._get_all_logs_ids  # pylint: disable=protected-access
    get_run_log_content = Build.get_build_log_content
    get_root_stage_names = Build.get_root_stage_names


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
