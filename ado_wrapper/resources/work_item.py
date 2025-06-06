import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.errors import UnknownError
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Member
from ado_wrapper.utils import build_hierarchy_payload, extract_json_from_html, find_key_path

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

WorkItemType = Literal["Bug", "Task", "User Story", "Feature", "Epic"]

DEFAULT_REQUESTED_FIELDS = [
    "System.Id", "System.Title", "System.Description", "System.AreaPath", "System.IterationPath", "System.State", "System.Reason",
    "System.AssignedTo", "System.CreatedBy", "System.CreatedDate", "System.ChangedBy", "System.ChangedDate", "System.BoardColumn",
    "System.Tags", # "Microsoft.VSTS.Common.Priority", "System.WorkItemType","Microsoft.VSTS.Scheduling.StoryPoints",
    # "Microsoft.VSTS.Common.ClosedDate", "Microsoft.VSTS.Common.StackRank", # "Microsoft.VSTS.Common.AcceptanceCriteria",
]


@dataclass
class WorkItem(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items?view=azure-devops-rest-7.1"""
    work_item_id: str = field(metadata={"is_id_field": True})
    title: str
    description: str = field(repr=False)
    area: str
    iteration_path: str
    state: str
    reason: str = field(repr=False)
    assigned_to: Member | None = field(repr=False)
    created_by: Member | None = field(repr=False)
    created_datetime: datetime = field(repr=False)
    changed_by: Member | None = field(repr=False)
    changed_datetime: datetime = field(repr=False)
    board_column: str = field(repr=False)
    tags: list[str] = field(default_factory=list, repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "WorkItem":
        return cls(
            data["id"], data["fields"]["System.Title"], data["fields"].get("System.Description", ""),
            data["fields"]["System.AreaPath"], data["fields"]["System.IterationPath"],
            data["fields"]["System.State"], data["fields"]["System.Reason"],
            Member.from_request_payload(data["fields"].get("System.AssignedTo")) if data["fields"].get("System.AssignedTo") else None,
            Member.from_request_payload(data["fields"].get("System.CreatedBy")) if data["fields"].get("System.CreatedBy") else None,
            datetime.fromisoformat(data["fields"]["System.CreatedDate"]),
            Member.from_request_payload(data["fields"].get("System.ChangedBy")) if data["fields"].get("System.ChangedBy") else None,
            datetime.fromisoformat(data["fields"]["System.ChangedDate"]),
            data["fields"].get("System.BoardColumn", ""),
            data["fields"].get("System.Tags", "").split(";") if data["fields"].get("System.Tags") else [],
        )

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", work_item_id: str) -> "WorkItem":
        """Doesn't need the board name"""
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        )

    def link(self, ado_client: "AdoClient") -> str:
        board_name = self.area.removeprefix(ado_client.ado_project_name+'\\')
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_boards/board/t/{board_name}/Stories/?workitem={self.work_item_id}"

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
            headers={"Content-Type": "application/json-patch+json"},  # This header stops us doing the normal route ):
            json=payload,
        )
        if request.status_code > 204:
            raise UnknownError(request.text)
        resource = cls.from_request_payload(request.json())
        ado_client.state_manager.add_resource_to_state(resource)
        return resource

    def edit(
        self, ado_client: "AdoClient", work_item_id: str,
        ticket_title: str | None = None, ticket_description: str | None = None, iteration_path: str | None = None,
    ) -> None:
        raise NotImplementedError("Editing work items is not implemented in this library yet")
        # {"contributionIds":["ms.vss-work-web.update-work-items-data-provider"],"dataProviderContext":{"properties":{"updatePackage":"[{\"id\":20357,\"rev\":6,\"projectId\":\"d94fd7fa-81be-46c2-9b11-b618a6509557\",\"isDirty\":true,\"fields\":{\"52\":\"<div>####################################################################################################################################################################################################################################################################################</div>\"},\"links\":{}}]","sourcePage":{"url":"https://dev.azure.com/VFCloudEngineering/Cloud%20Engineering/_boards/board/t/Platform%20Engineering-UK/Features?workitem=20357","routeId":"ms.vss-work-web.new-boards-content-route","routeValues":{"project":"Cloud Engineering","pivot":"board","teamName":"Platform Engineering-UK","backlogLevel":"Features","viewname":"team-board-content"}}}}}

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", work_item_id: str) -> None:
        super()._delete_by_id(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/wit/workitems/{work_item_id}?api-version=7.1",
            work_item_id,
        )

    @staticmethod
    def _get_payload(ado_client: "AdoClient", board_name: str) -> dict[str, Any]:
        json_data = extract_json_from_html(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_boards/board/t/{board_name}/Stories",
        )
        if "ms.vss-work-web.kanban-board-content-data-provider" not in json_data["data"]:
            raise UnknownError("This board probably doesn't exist, or it's not a task board")
        payload = json_data['data']['ms.vss-work-web.kanban-board-content-data-provider']['boardModel']['itemSource']['payload']
        return payload

    @classmethod
    def get_all_work_item_ids(cls, ado_client: "AdoClient", board_name: str) -> list[str]:
        """Get all work item IDs in the same area as this one"""
        payload = cls._get_payload(ado_client, board_name)
        original = [x[0] for x in payload["rows"]]  # Original IDs (visible)
        incoming_ids, outgoing_ids = payload['orderedIncomingIds'], payload['orderedOutgoingIds']  # Ones retrieved when "show more" is clicked
        return original+incoming_ids+outgoing_ids

    @classmethod
    def get_all_by_board(cls, ado_client: "AdoClient", board_name: str) -> list["WorkItem"]:
        all_work_items = []
        all_ids = cls.get_all_work_item_ids(ado_client, board_name)
        ids_chunked = [all_ids[i:i+50] for i in range(0, len(all_ids), 50)]
        for chunk in ids_chunked:
            request = ado_client.session.post(
                f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wit/workitemsbatch?api-version=7.1",
                json={"ids": chunk, "expand": "relations", "errorPolicy": 2, "fields": DEFAULT_REQUESTED_FIELDS},
            )
            work_items = [cls.from_request_payload(x) for x in request.json()["value"]]
            all_work_items.extend(work_items)
        return all_work_items

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", work_item_title: str, board_name: str) -> "WorkItem | None":
        return [x for x in cls.get_all_by_board(ado_client, board_name) if x.title == work_item_title][0]

    @classmethod
    def get_all_by_sub_name(cls, ado_client: "AdoClient", work_item_title: str, board_name: str) -> list["WorkItem"]:
        return [x for x in cls.get_all_by_board(ado_client, board_name) if work_item_title in x.title]

    @classmethod
    def get_related_items(cls, ado_client: "AdoClient", work_item_id: str) -> list["RelatedWorkItem"]:
        PAYLOAD = build_hierarchy_payload(
            ado_client, "work-web.work-item-data-provider", "work-web.new-boards-content-route",
            additional_properties={"id": int(work_item_id)},
        )
        request = ado_client.session.post(
            f"https://dev.azure.com/VFCloudEngineering/_apis/Contribution/HierarchyQuery?api-version=7.1-preview.1",
            json=PAYLOAD
        )
        # if request.json()["dataProviders"]["ms.vss-work-web.work-item-data-provider"] is None:
        #     raise UnknownError(f"Could not fetch related work items for item {work_item_id}")
        return [
            RelatedWorkItem.from_request_payload(x)
            for x in request.json()["dataProviders"]["ms.vss-work-web.work-item-data-provider"]["work-item-data"]["relations"]
        ]

    @classmethod
    def get_comments(
        cls, ado_client: "AdoClient", work_item_id: str, include_deleted: bool = False, strip_html: bool = True, replace_linebreaks: bool = True
    ) -> list["WorkItemComment"]:
        """Strip HTML removes all <div> and such from the comment.
        Replace linebreaks replaces all <br> with \n.
        """
        count = 200
        assert count <= 200, "Count must be less than or equal to 200"
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wit/workItems/{work_item_id}/comments?$top={count}&includeDeleted={include_deleted}",  # &$expand=-17&order=2
        )
        return [WorkItemComment.from_request_payload(x, strip_html, replace_linebreaks) for x in request.json()["comments"]]

    @staticmethod
    def create_comment(ado_client: "AdoClient", work_item_id: str, comment_text: str, auto_add_html_tags: bool = True) -> "WorkItemComment":
        return WorkItemComment.create(ado_client, ado_client.ado_project_name, work_item_id, comment_text, auto_add_html_tags)

    # TODO:
    # Set relationships, delete comments

# ============================================================================

RelationshipType = Literal["Parent", "Child", "Related", "Successor", "Predecessor"]
RELATION_VALUE_TO_TYPE: dict[int, RelationshipType] = {
    -3: "Predecessor",
    -2: "Parent",
    # -1: "???",
    # 0: "???",
    1: "Related",
    2: "Child",
}

@dataclass
class RelatedWorkItem:
    """A class to represent a related work item"""
    work_item_id: str = field(metadata={"is_id_field": True})
    relation_type: RelationshipType

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "RelatedWorkItem":
        return cls(data["ID"], RELATION_VALUE_TO_TYPE[data["LinkType"]])


# ============================================================================

@dataclass
class WorkItemComment:
    """A class to represent a work item comment"""
    comment_id: str = field(metadata={"is_id_field": True})
    text: str
    created_by: Member | None = field(repr=False)
    created_datetime: datetime = field(repr=False)
    modified_by: Member | None = field(repr=False)
    modified_datetime: datetime | None = field(repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any], strip_html: bool = True, replace_linebreaks: bool = True) -> "WorkItemComment":
        data["text"] = data["text"].replace("&quot;", "\"")
        if replace_linebreaks:
            data["text"] = data["text"].replace("<br>", "\n").replace("</br>", "")
        if strip_html:
            data["text"] = re.sub(r'<[^>]*>', '', data["text"])
        return cls(
            data["id"], data["text"],
            Member.from_request_payload(data["createdBy"]) if data["createdBy"] else None,
            datetime.fromisoformat(data["createdDate"]),
            Member.from_request_payload(data["modifiedBy"]) if data["modifiedBy"] else None,
            datetime.fromisoformat(data["modifiedDate"]) if data["modifiedDate"] else None,
        )

    @classmethod
    def create(cls, ado_client: "AdoClient", board_name: str, work_item_id: str, comment_text: str, auto_add_html_tags: bool = True) -> "WorkItemComment":
        PAYLOAD = build_hierarchy_payload(
            ado_client, "work-web.workitem-add-comment-data-provider", "work-web.new-boards-content-route",
            additional_properties={"addComment": {"id": int(work_item_id), "format": 1, "text": comment_text, "projectId": ado_client.ado_project_id}},  # Project ID is required
        )
        if auto_add_html_tags:
            PAYLOAD["dataProviderContext"]["properties"]["addComment"]["text"] = f"<div>{comment_text}</div>"  # This is added through the UI, immitating here.
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=7.1-preview.1",
            json=PAYLOAD,
        )
        return cls.from_request_payload(request.json()["dataProviders"]["ms.vss-work-web.workitem-add-comment-data-provider"]["data"])
