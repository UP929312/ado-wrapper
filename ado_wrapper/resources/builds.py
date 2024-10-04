import time
from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import TYPE_CHECKING, Any, Literal


from ado_wrapper.resources.environment import Environment, PipelineAuthorisation
from ado_wrapper.resources.repo import BuildRepository
from ado_wrapper.resources.users import Member
from ado_wrapper.resources.build_timeline import BuildTimeline
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.errors import ConfigurationError, UnknownError
from ado_wrapper.utils import from_ado_date_string, remove_ansi_codes, build_hierarchy_payload, DATETIME_RE_PATTERN

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient
    from ado_wrapper.resources.build_definitions import BuildDefinition

BuildStatus = Literal["notStarted", "inProgress", "completed", "cancelling", "postponed", "notSet", "none"]
QueuePriority = Literal["low", "belowNormal", "normal", "aboveNormal", "high"]


# ========================================================================================================


@dataclass
class Build(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds?view=azure-devops-rest-7.1"""

    build_id: str = field(metadata={"is_id_field": True})
    build_number: str
    status: BuildStatus = field(metadata={"editable": True})  # Only this is editable ):
    requested_by: Member = field(repr=False)
    build_repo: BuildRepository = field(repr=False)
    parameters: dict[str, str] = field(repr=False)
    definition: "BuildDefinition | None" = field(repr=False)
    pool_id: str | None
    start_time: datetime | None = field(repr=False)
    finish_time: datetime | None = field(repr=False)
    queue_time: datetime | None = field(repr=False, default=None)
    reason: str = field(default="An automated build created with the ado_wrapper Python library", repr=False)
    priority: QueuePriority = field(default="normal", repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Build":
        from ado_wrapper.resources.build_definitions import BuildDefinition

        requested_by = Member.from_request_payload(data["requestedBy"])
        build_repo = BuildRepository.from_request_payload(data["repository"])
        build_definition = BuildDefinition.from_request_payload(data["definition"]) if "definition" in data else None
        return cls(str(data["id"]), str(data["buildNumber"]), data["status"], requested_by, build_repo, data.get("templateParameters", {}),
                   build_definition, data.get("queue", {}).get("pool", {}).get("id"), from_ado_date_string(data.get("startTime")),
                   from_ado_date_string(data.get("finishTime")), from_ado_date_string(data.get("queueTime")), data["reason"],
                   data["priority"])  # fmt: skip

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", build_id: str) -> "Build":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds/{build_id}?api-version=7.1",
        )

    @classmethod
    def create(cls, ado_client: "AdoClient", definition_id: str, source_branch: str = "refs/heads/main") -> "Build":
        return super()._create(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds?definitionId={definition_id}&api-version=7.1",
            {"reason": "An automated build created with the ado_wrapper Python library", "sourceBranch": source_branch},
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", build_id: str) -> None:
        cls.delete_all_leases(ado_client, build_id)
        return super()._delete_by_id(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds/{build_id}?api-version=7.1",
            build_id,
        )

    def update(self, ado_client: "AdoClient", attribute_name: str, attribute_value: Any) -> None:
        return super()._update(
            ado_client, "patch",
            f"/{ado_client.ado_project_name}/_apis/build/builds/{self.build_id}?api-version=7.1",
            attribute_name, attribute_value, {attribute_name: attribute_value}  # fmt: skip
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient", limit: int = 1000, status: BuildStatus | Literal["all"] = "all") -> "list[Build]":
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds?api-version=7.1&queryOrder=finishTimeDescending&$top={limit}&statusFilter={status}",
        )  # pyright: ignore[reportReturnType]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def create_and_wait_until_completion(cls, ado_client: "AdoClient", definition_id: str, branch_name: str = "main",
                                         max_timeout_seconds: int = 300) -> "Build":  # fmt: skip
        """Creates a build and waits until it is completed, or raises a TimeoutError if it takes too long.
        WARNING: This is a blocking operation, it will not return until the build is completed or the timeout is reached."""
        build = cls.create(ado_client, definition_id, branch_name)
        start_time = datetime.now()
        while True:
            build = Build.get_by_id(ado_client, build.build_id)
            if build.status == "completed":
                break
            if (datetime.now() - start_time).seconds > max_timeout_seconds:
                raise TimeoutError(f"The build did not complete within {max_timeout_seconds} seconds ({max_timeout_seconds//60} minutes)")
            time.sleep(ado_client.run_polling_interval_seconds)
        return build

    @staticmethod
    def delete_all_leases(ado_client: "AdoClient", build_id: str) -> None:
        leases_request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/build/builds/{build_id}/leases?api-version=7.1",
        )
        if leases_request.status_code != 200:
            if not ado_client.suppress_warnings:
                print(f"[ADO_WRAPPER] Could not get a list of leases to delete!, {leases_request.status_code}, {leases_request.text}")
            return
        leases = leases_request.json()["value"]
        for lease in leases:
            lease_response = ado_client.session.delete(  # TODO: Rename "lease_response" to something better.
                f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/build/retention/leases?ids={lease['leaseId']}&api-version=6.1",
            )
            if lease_response.status_code >= 300:  # 204?
                print(f"[ADO_WRAPPER] Could not delete lease {lease['leaseId']}! {lease_response.status_code}, {lease_response.text}")

    @classmethod
    def get_all_by_definition(cls, ado_client: "AdoClient", definition_id: str) -> "list[Build]":
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds?definitions={definition_id}&api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    @classmethod
    def allow_on_environment(cls, ado_client: "AdoClient", definition_id: str, environment_id: str) -> PipelineAuthorisation:
        environment = Environment.get_by_id(ado_client, environment_id)
        return environment.add_pipeline_permission(ado_client, definition_id)

    @classmethod
    def get_latest(cls, ado_client: "AdoClient", definition_id: str) -> "Build | None":
        all_builds = cls.get_all_by_definition(ado_client, definition_id)
        builds_with_start = [x for x in all_builds if x.start_time is not None]
        return max(builds_with_start, key=lambda build: build.start_time) if builds_with_start else None  # type: ignore[return-value, arg-type]

    @staticmethod
    def get_stages_jobs_tasks(
        ado_client: "AdoClient", build_id: str
    ) -> dict[str, dict[str, dict[str, dict[str, dict[str, str]]]]]:  # This is really ridiculous...
        """Returns a nested dictionary of stages -> stage_id+jobs -> job_id+tasks -> task_name -> task_id,
        with each key being the name, and each value containing both a list of childen
        (e.g. stages has jobs, jobs has tasks) and an "id" key/value.
        The items are returned by their display name, not their internal name)"""
        items = BuildTimeline.get_all_by_types(ado_client, build_id, ["Stage", "Phase", "Job", "Task"])
        mapping = {stage.name: {"id": stage.item_id, "jobs": {}} for stage in items["Stage"]}
        for job in [x for x in items["Job"] if x.parent_id]:
            mapping[job.parent_stage_name]["jobs"][job.name] = {"id": job.item_id, "tasks": {}}  # type: ignore[index]
        for task in [x for x in items["Task"] if x.worker_name]:
            mapping[task.parent_stage_name]["jobs"][task.parent_job_name]["tasks"][task.name] = task.item_id  # type: ignore[index]
        return mapping  # type: ignore[return-value]

    @classmethod
    def _get_all_logs_ids(cls, ado_client: "AdoClient", build_id: str) -> dict[str, str]:
        """Returns a mapping of stage_name/job_name/task_name: log_id"""
        # Get all the individual task -> log_id mapping
        tasks = [
            x for x in BuildTimeline.get_all_by_type(ado_client, build_id, "Task").records
            if x.log  # All the ones with logs (removes skipped tasks)
        ]  # fmt: skip
        return {
            f"{stage_name}/{job_name}/{task_name}": [task for task in tasks if task.item_id == task_id][0].log["id"]  # type: ignore
            for stage_name, stage_data in cls.get_stages_jobs_tasks(ado_client, build_id).items()
            for job_name, job_data in stage_data["jobs"].items()
            for task_name, task_id in job_data["tasks"].items()
            if [task for task in tasks if task.item_id == task_id]
        }

    @classmethod
    def get_build_log_content(cls, ado_client: "AdoClient", build_id: str, stage_name: str, job_name: str, task_name: str,
                              remove_prefixed_timestamp: bool = True, remove_colours: bool = False) -> str:  # fmt: skip
        """Returns the text content of the log by stage name and job name"""
        mapping = cls._get_all_logs_ids(ado_client, build_id)
        log_id = mapping.get(f"{stage_name}/{job_name}/{task_name}")
        if log_id is None:
            raise ConfigurationError(
                f"Wrong stage name or job name combination (case sensitive), received {stage_name}/{job_name}/{task_name}"
                + "\nOptions were:\n" + "\n".join(list(mapping.keys()))  # fmt: skip
            )
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/build/builds/{build_id}/logs/{log_id}"
        ).text
        if remove_colours:
            request = remove_ansi_codes(request)
        if remove_prefixed_timestamp:
            request = "\n".join([DATETIME_RE_PATTERN.sub("", line) for line in request.split("\n")])  # TODO: Do what we do above???
        return request

    @staticmethod
    def get_root_stage_names(ado_client: "AdoClient", build_id: str) -> list[str]:
        """Returns a list of display names of stages that `don't` have previous dependencies"""
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_id}/_build/results?buildId={build_id}&view=results"
        ).text
        json_raw = request.split('"ms.vss-build-web.run-details-data-provider":')[1].split('"ms.vss-web.proof-of-presence-config-data":')[0].removesuffix(",")  # fmt: skip
        json_data = json.loads(json_raw)
        return [x["name"] for x in json_data["stages"] if not x.get("dependsOn")]

    @classmethod
    def _get_all_checks(cls, ado_client: "AdoClient", build_id: str) -> list[dict[str, Any]]:
        """Internal function for returning all of an "Approve Environment" and "Approve Variable Group"
        for a build"""
        non_dependant_stages = cls.get_root_stage_names(ado_client, build_id)
        stage_ids: list[str] = [
            stage_data["id"]  # type: ignore[misc]
            for stage_name, stage_data in Build.get_stages_jobs_tasks(ado_client, build_id).items()
            if stage_name in non_dependant_stages
        ]
        PAYLOAD = build_hierarchy_payload(
            ado_client, "build-web.checks-panel-data-provider", "build-web.ci-results-hub-route", additional_properties={"buildId": build_id, "stageIds": ",".join(stage_ids)}
        )  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery/project/{ado_client.ado_project_name}?api-version=6.1-preview",
            json=PAYLOAD,
        ).json()
        data: list[dict[str, Any]] = request["dataProviders"]["ms.vss-build-web.checks-panel-data-provider"]
        return data

    @classmethod
    def get_environment_approvals(cls, ado_client: "AdoClient", build_id: str) -> dict[str, str]:
        """Returns a mapping for the stage approvals for a build\n
        Returns {stage_name: approval_id}\n
        NOTE: This is the stage's display name, not it's internal name"""
        data = cls._get_all_checks(ado_client, build_id)
        # Already approved ones are here, but with no "approvals"
        return {approval["stageName"]: approval["approvals"][0]["id"] for approval in data if approval.get("approvals")}

    @classmethod
    def approve_environment_for_pipeline(cls, ado_client: "AdoClient", build_id: str, stage_name: str) -> None:
        """Approves a single stage environment approval.\n
        Takes the stage's `display_name`, not it's `internal_name`."""
        approval_ids = cls.get_environment_approvals(ado_client, build_id)
        if stage_name not in approval_ids:
            raise IndexError(
                "Stage name not found for those approvals, potentially because it was already approved, or you passed in the internal name, rather than the display name?"
                + f"\nInputted stage name: {stage_name}"
                + f"\nPossible stage names: {list(approval_ids.keys())}"
            )
        PAYLOAD = [{"approvalId": approval_ids[stage_name], "status": 4, "comment": "", "deferredTo": None}]
        request = ado_client.session.patch(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/pipelines/approvals?api-version=6.1-preview",
            json=PAYLOAD,
        )
        if request.status_code != 200:
            raise UnknownError(f"Approving that environment raised an error: {request.status_code}, {request.text}")


# ========================================================================================================
