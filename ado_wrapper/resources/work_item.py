from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.errors import UnknownError
from ado_wrapper.state_managed_abc import StateManagedResource

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

WorkItemType = Literal["Bug", "Task", "User Story", "Feature", "Epic"]


@dataclass
class WorkItem(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items?view=azure-devops-rest-7.1"""
    work_item_id: str = field(metadata={"is_id_field": True})
    title: str
    description: str
    created_datetime: datetime
    area: str
    iteration_path: str
    state: str
    reason: str

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "WorkItem":
        return cls(data["id"], data["fields"]["System.Title"], data["fields"]["System.Description"],
                   datetime.fromisoformat(data["fields"]["System.CreatedDate"]),
                   data["fields"]["System.AreaPath"], data["fields"]["System.IterationPath"],
                   data["fields"]["System.State"], data["fields"]["System.Reason"])

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", work_item_id: str) -> "WorkItem":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        )

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_boards/board/t/{self.area.removeprefix(ado_client.ado_project_name+'\\')}/Stories/?workitem={self.work_item_id}"

    @classmethod
    def create(
        cls, ado_client: "AdoClient", ticket_title: str, ticket_description: str, work_item_type: WorkItemType, area: str, iteration_path: str
    ) -> "WorkItem":
        mapping = {
            "/fields/System.Title": ticket_title,
            "/fields/System.Description": ticket_description,
            "/fields/System.AreaPath": f"{ado_client.ado_project_name}\\\\{area}",
            "/fields/System.IterationPath": iteration_path,
            "/fields/System.State": "New",
            "/fields/System.Reason": "New",
        }
        payload = [{"op": "add", "path": key, "value": value} for key, value in mapping.items()]
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wit/workitems/${work_item_type}?api-version=7.1-preview.3",
            headers={"Content-Type": "application/json-patch+json"},  # this header stops us doing the normal route ):
            json=payload,
        )
        if request.status_code > 204:
            raise UnknownError(request.text)
        resource = cls.from_request_payload(request.json())
        ado_client.state_manager.add_resource_to_state(resource)
        return resource

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", work_item_id: str) -> None:
        super()._delete_by_id(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/wit/workitems/{work_item_id}?api-version=7.1",
            work_item_id,
        )

    # @classmethod
    # def get_all(cls, ado_client: "AdoClient") -> list["WorkItem"]:
    #     # THIS DOESN'T WORK, HAVE TO USE WORK ITEM QUERY LANGUAGE, YUCK
    #     request = ado_client.session.post(  # Post means we can't use the function
    #         f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wit/workitemsbatch?api-version=7.1",
    #     ).json()
    #     return [cls.from_request_payload(x) for x in request["values"]]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    # @classmethod
    # def get_by_name(cls, ado_client: "AdoClient", work_item_title: str) -> "WorkItem | None":
    #     return cls._get_by_abstract_filter(ado_client, lambda work_item: work_item.title == work_item_title)
