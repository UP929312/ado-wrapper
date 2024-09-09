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
    # "type": "(?!Checkpoint|Task|Container|Job|Phase|Stage)
    # "order": "(?!null)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildTimeline":
        records = [BuildTimelineGenericItem.from_request_payload(x) for x in data["records"]]
        return cls(data["id"], records, data["lastChangedBy"], from_ado_date_string(data["lastChangedOn"]), data["changeId"], data["url"])

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", build_id: str, timeline_id: str) -> "BuildTimeline":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds/{build_id}/timeline/{timeline_id}?api-version=7.1-preview.2",
        )

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", build_id: str) -> None:
        raise NotImplementedError

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_build_timeline(cls, ado_client: "AdoClient", build_id: str, fetch_retries: bool = False) -> "BuildTimeline":
        """Fetches the whole base timeline, fetch_retries converts the list of timeline ids into BuildTimeline instances
        WARNING: Fetching replies is an incredibly expensive operation, especially if there are many retried items."""
        # 1695144
        base_build_timeline = super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/build/builds/{build_id}/timeline?api-version=7.1-preview.2",
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
        timeline = cls.get_build_timeline(ado_client, build_id, fetch_retries)
        item_types_mapping: dict[BuildTimelineItemTypeType, list[BuildTimelineGenericItem]] = {item_type: [] for item_type in item_types}
        for item in timeline.records:
            if item.item_type in item_types:
                item_types_mapping[item.item_type].append(item)
        return item_types_mapping

    get_build_timeline_by_id = get_by_id


# ========================================================================================================


class TaskType(TypedDict):
    id: str
    name: str
    version: str


class LogType(TypedDict):
    id: int
    type: str
    url: str


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
    message: str
    data: IssueDataType


@dataclass
class BuildTimelineGenericItem:
    item_type: BuildTimelineItemTypeType
    item_id: str
    previous_attempts: list[PreviousAttemptType]
    parent_id: str | None
    name: str
    start_time: datetime
    end_time: datetime
    current_operation: str | None  # Maybe?
    percent_complete: int | None
    state: "RunState"
    result: "RunResult"
    result_code: str | None  # E.g. Evaluating: ne(variables['input_variables.apply_flag'], False)\nExpanded: ne('false', False)\nResult: False\n
    change_id: int
    last_modified: datetime
    worker_name: str | None
    order: int | None
    defaults: None  # Not sure
    error_count: int
    warning_count: int
    url: str | None  # Also not sure
    log: LogType | None
    task: TaskType | None
    attempt: int
    internal_name: str  # Previously identifier
    issues: list[IssueType]

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "BuildTimelineGenericItem":
        return cls(
            data["type"], data["id"], data["previousAttempts"], data["parentId"], data["name"], from_ado_date_string(data["startTime"]),
            from_ado_date_string(data["finishTime"]), data["currentOperation"], data["percentComplete"], data["state"],
            data["result"], data["resultCode"], data["changeId"], from_ado_date_string(data["lastModified"]), data["workerName"],
            data.get("order"), None, data.get("error_count", 0), data.get("warning_count", 0), data["url"], data["log"], data["task"],
            data["attempt"], data["identifier"], data.get("issues", [])
        )  # fmt: skip
