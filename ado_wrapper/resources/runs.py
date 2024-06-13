import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from ado_wrapper.resources.builds import Build
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string, recursively_find_or_none

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

RunResult = Literal["canceled", "failed", "succeeded", "unknown"]
RunState = Literal["canceling", "completed", "inProgress", "unknown"]


class RunAllDictionary(TypedDict):
    template_variables: dict[str, Any]
    branch_name: str


# ========================================================================================================


@dataclass
class Run(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs?view=azure-devops-rest-6.1"""

    run_id: str = field(metadata={"is_id_field": True})
    run_name: str
    start_time: datetime = field(repr=False)
    finish_time: datetime | None = field(repr=False)
    repo_id: str
    status: RunState
    result: RunResult
    template_parameters: dict[str, Any]

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Run":
        return cls(str(data["id"]), data["name"], from_ado_date_string(data["createdDate"]), from_ado_date_string(data.get("finishedDate")),
                   recursively_find_or_none(data, ["resources", "repositories", "self", "repository", "id"]),
                   data["state"], data.get("result", "unknown"), data["templateParameters"])  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", pipeline_id: str, run_id: str) -> "Run":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project}/_apis/pipelines/{pipeline_id}/runs/{run_id}?api-version=6.1-preview.1",
        )  # type: ignore[return-value]

    @classmethod
    def create(
        cls, ado_client: "AdoClient", definition_id: str, template_variables: dict[str, Any], source_branch: str = "main",  # fmt: skip
    ) -> "Run":
        try:
            return super()._create(
                ado_client,
                f"/{ado_client.ado_project}/_apis/pipelines/{definition_id}/runs?api-version=6.1-preview.1",
                {"templateParameters": template_variables, "repositories": {"refName": f"refs/heads/{source_branch}"}},
            )  # type: ignore[return-value]
        except ValueError as e:
            raise ValueError(
                f"A template variable inputted is not allowed! {str(e).split('message')[1][3:].removesuffix(':').split('.')[0]}"
            ) from e

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", run_id: str) -> None:
        return Build.delete_by_id(ado_client, run_id)

    def update(self, ado_client: "AdoClient", attribute_name: str, attribute_value: Any) -> None:
        raise NotImplementedError("Use Build's update instead!")

    @classmethod
    def get_all_by_definition(cls, ado_client: "AdoClient", pipeline_id: str) -> "list[Run]":
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/pipelines/{pipeline_id}/runs?api-version=6.1-preview.1",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def run_and_wait_until_completion(cls, ado_client: "AdoClient", definition_id: str, template_variables: dict[str, Any],
                                         branch_name: str = "main", max_timeout_seconds: int | None = 900) -> "Run":  # fmt: skip
        """Creates a run and waits until it is completed, or raises a TimeoutError if it takes too long.
        WARNING: This is a blocking operation, it will not return until the run is completed or the timeout (15 mins) is reached."""
        data: dict[str, RunAllDictionary] = {definition_id: {"template_variables": template_variables, "branch_name": branch_name}}
        return cls.run_all_and_capture_results_simultaneously(ado_client, data, max_timeout_seconds)[definition_id]

    @classmethod
    def run_all_and_capture_results_sequentially(
        cls, ado_client: "AdoClient", data: dict[str, RunAllDictionary], max_timeout_seconds: int | None = 1800
    ) -> dict[str, "Run"]:
        """Takes a mapping of definition_id -> {template_variables, branch_name}
        Once done, returns a mapping of definition_id -> `Run` object"""
        return_values = {}
        for definition_id, build_def_data in data.items():
            template_variables, branch_name = build_def_data["template_variables"], build_def_data["branch_name"]
            run = cls.run_and_wait_until_completion(ado_client, definition_id, template_variables, branch_name, max_timeout_seconds)
            return_values[definition_id] = run
        return return_values

    @classmethod
    def run_all_and_capture_results_simultaneously(
        cls, ado_client: "AdoClient", data: dict[str, RunAllDictionary], max_timeout_seconds: int | None = 1800
    ) -> dict[str, "Run"]:
        """Takes a mapping of definition_id -> {template_variables, branch_name}
        Once done, returns a mapping of definition_id -> `Run` object"""
        # Get a mapping of definition_id -> Run()
        runs: dict[str, Run] = {}
        for definition_id, build_def_data in data.items():
            template_variables, branch_name = build_def_data["template_variables"], build_def_data["branch_name"]
            run = cls.create(ado_client, definition_id, template_variables, branch_name)
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
