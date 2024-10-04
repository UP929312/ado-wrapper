from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient
    from ado_wrapper.resources.runs import RunState, RunResult


BuildTimelineItemTypeType = Literal["Checkpoint", "Task", "Container", "Job", "Phase", "Stage"]
# Stage -> Phase/Job -> Task


# ========================================================================================================


@dataclass
class BuildTimeline(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/build/timeline?view=azure-devops-rest-7.1"""

    build_timeline_id: str
    records: list["BuildTimelineGenericItem"] = field(repr=False)
    last_changed_by: str = field(repr=False)
    last_changed_on: datetime
    change_id: int = field(repr=False)
    url: str = field(repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildTimeline":
        records = [BuildTimelineGenericItem.from_request_payload(x) for x in data["records"]]
        for record in records:
            record.add_parents(records)
        return cls(data["id"], records, data["lastChangedBy"], from_ado_date_string(data["lastChangedOn"]), data["changeId"], data["url"])

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", build_id: str, timeline_id: str) -> "BuildTimeline":
        build_timeline = super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds/{build_id}/timeline/{timeline_id}?api-version=7.1-preview.2",
        )
        return build_timeline

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", build_id: str) -> None:
        # Can't remove this because calling .delete() will call this.
        raise NotImplementedError

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_build_timeline(cls, ado_client: "AdoClient", build_id: str, fetch_retries: bool = False) -> "BuildTimeline":
        """Fetches the whole base timeline, fetch_retries converts the list of timeline ids into BuildTimeline instances
        WARNING: Fetching replies is an incredibly expensive operation, especially if there are many retried items."""
        base_build_timeline = super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds/{build_id}/Timeline?api-version=7.1-preview.2",
        )
        if fetch_retries:
            for item_index, item in enumerate(base_build_timeline.records):
                for previous_attempt_index, previous_attempt_dict in enumerate(item.previous_attempts):
                    retry_timeline = cls.get_by_id(ado_client, build_id, previous_attempt_dict["timelineId"])
                    base_build_timeline.records[item_index].previous_attempts[previous_attempt_index] = retry_timeline  # type: ignore[call-overload]
        return base_build_timeline

    @classmethod
    def get_all_by_type(
        cls, ado_client: "AdoClient", build_id: str, item_type: BuildTimelineItemTypeType, fetch_retries: bool = False
    ) -> "BuildTimeline":
        timeline = cls.get_build_timeline(ado_client, build_id, fetch_retries)
        filtered_records = [x for x in timeline.records if x.item_type == item_type]
        timeline.records = filtered_records
        return timeline

    @classmethod
    def get_all_by_types(
        cls, ado_client: "AdoClient", build_id: str, item_types: list[BuildTimelineItemTypeType], fetch_retries: bool = False
    ) -> dict[BuildTimelineItemTypeType, list["BuildTimelineGenericItem"]]:
        timeline_records = cls.get_build_timeline(ado_client, build_id, fetch_retries).records
        item_types_mapping: dict[BuildTimelineItemTypeType, list[BuildTimelineGenericItem]] = {
            item_type: [item for item in timeline_records if item.item_type == item_type]
            for item_type in item_types  # fmt: skip
        }
        return item_types_mapping

    @classmethod
    def get_tasks_by_name(cls, ado_client: "AdoClient", build_id: str, task_name: str) -> list["BuildTimelineGenericItem"]:
        return [x for x in cls.get_all_by_type(ado_client, build_id, "Task").records if x.name == task_name]

    get_build_timeline_by_id = get_by_id
    get_by_build_id = get_build_timeline


# ========================================================================================================


class TaskType(TypedDict):
    """Certain pre-made tasks have this set, e.g. using bash or Python"""

    id: str  # e.g. 33c63b11-352b-45a2-ba1b-54cb568a29ca == UsePythonVersion
    name: str  # e.g. UsePythonVersion
    version: str  # e.g. 0.245.1


class LogType(TypedDict):
    id: int  # Local id of the container, incremented (e.g. 5)
    type: str  # e.g. container
    url: str  # Url of the container or log destination type


class PreviousAttemptType(TypedDict):
    attempt: int  # e.g. 1
    timelineId: str  # e.g. 'a905943e-2a6d-5859-93e4-a09337347fa5'
    recordId: str  # e.g. 'a905943e-2a6d-5859-93e4-a09337347fa5'


class IssueDataType(TypedDict):
    type: Literal["error", "warning"]
    logFileLineNumber: str


class IssueType(TypedDict):
    type: Literal["error", "warning"]
    category: str  # Maybe Literal["General"]
    message: str  # Reason for failure, e.g. `'message': "Error: The process '/usr/bin/bash' failed with exit code 1"`
    data: IssueDataType  # E.g. 'data': {'type': 'error', 'logFileLineNumber': '133'}


@dataclass
class BuildTimelineGenericItem:
    item_type: BuildTimelineItemTypeType
    item_id: str
    previous_attempts: list[PreviousAttemptType]
    parent_id: str | None
    name: str
    start_time: datetime = field(repr=False)
    end_time: datetime = field(repr=False)
    current_operation: str | None = field(repr=False)  # Maybe?
    percent_complete: int | None = field(repr=False)
    state: "RunState"
    result: "RunResult"
    # V E.g. Evaluating: ne(variables['input_variables.apply_flag'], False)\nExpanded: ne('false', False)\nResult: False\n
    result_code: str | None = field(repr=False)
    change_id: int = field(repr=False)
    last_modified: datetime = field(repr=False)
    worker_name: str | None = field(repr=False)
    order: int | None
    defaults: None = field(repr=False)  # Not sure
    error_count: int
    warning_count: int
    url: str | None = field(repr=False)  # Also not sure
    log: LogType | None = field(repr=False)
    task: TaskType | None = field(repr=False)
    attempt: int
    internal_name: str = field(repr=False)  # Previously identifier
    issues: list[IssueType]
    # These are set after:
    parent_job_name: str | None = None
    parent_job_id: str | None = None
    parent_stage_name: str | None = None
    parent_stage_id: str | None = None
    # "type": "(?!Checkpoint|Task|Container|Job|Phase|Stage)
    # "order": "(?!null)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildTimelineGenericItem":
        return cls(
            data["type"], data["id"], data["previousAttempts"], data["parentId"], data["name"], from_ado_date_string(data["startTime"]),
            from_ado_date_string(data["finishTime"]), data["currentOperation"], data["percentComplete"], data["state"],
            data["result"], data["resultCode"], data["changeId"], from_ado_date_string(data["lastModified"]), data["workerName"],
            data.get("order"), None, data.get("error_count", 0), data.get("warning_count", 0), data["url"], data["log"], data["task"],
            data["attempt"], data["identifier"], data.get("issues", []), None, None, None, None,
        )  # fmt: skip

    @staticmethod
    def get_parent_item(item: "BuildTimelineGenericItem", all_items: list["BuildTimelineGenericItem"]) -> "BuildTimelineGenericItem":
        return [x for x in all_items if x.item_id == item.parent_id][0]

    def add_parents(self, all_items: list["BuildTimelineGenericItem"]) -> None:
        if self.parent_id is None:
            return
        if self.item_type == "Job":
            parent_phase = BuildTimelineGenericItem.get_parent_item(self, all_items)  # Job -> Phase
            parent_stage = BuildTimelineGenericItem.get_parent_item(parent_phase, all_items)  # Phase -> Stage
            self.parent_stage_id = parent_stage.item_id
            self.parent_stage_name = parent_stage.name
        if self.item_type == "Task":
            parent_job = BuildTimelineGenericItem.get_parent_item(self, all_items)  # Task -> Job
            self.parent_job_id = parent_job.item_id
            self.parent_job_name = parent_job.name

            if parent_job.parent_id is not None:  # TODO: Try parent_job.add_parents?
                parent_phase = BuildTimelineGenericItem.get_parent_item(parent_job, all_items)  # Job -> Phase
                parent_stage = BuildTimelineGenericItem.get_parent_item(parent_phase, all_items)  # Phase -> Stage
                self.parent_stage_id = parent_stage.item_id
                self.parent_stage_name = parent_stage.name

    def get_log_content(self, ado_client: "AdoClient", build_id: str, remove_prefixed_timestamp: bool = True, remove_colours: bool = False) -> str:  # fmt: skip
        """Utility function to get a tasks function without needing to pass in the tasks parent job and stage, and it's own name."""
        from ado_wrapper.resources.runs import Run  # To prevent circular imports

        if self.item_type != "Task":
            raise TypeError("Error! This can only be run on Tasks, not any other item type!")
        assert self.parent_stage_name is not None and self.parent_job_name is not None
        return Run.get_run_log_content(
            ado_client, build_id, self.parent_stage_name, self.parent_job_name, self.name, remove_prefixed_timestamp, remove_colours
        )
