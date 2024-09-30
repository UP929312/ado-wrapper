from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.utils import from_ado_date_string

if TYPE_CHECKING:
    from ado_wrapper.resources.users import Member
    from ado_wrapper.client import AdoClient


@dataclass
class AgentPool(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask/pools?view=azure-devops-rest-7.1"""

    agent_pool_id: str = field(metadata={"is_id_field": True})
    agent_cloud_id: str | None
    name: str
    pool_size: int
    target_size: int | None
    auto_size: bool | None
    auto_update: bool
    auto_provision: bool
    is_hosted: bool
    scope: str = field(repr=False)
    created_on: datetime = field(repr=False)
    created_by: "Member" = field(repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "AgentPool":
        from ado_wrapper.resources.users import Member  # Stop circular imports

        created_by = Member.from_request_payload(data["createdBy"])
        return cls(
            str(data["id"]), data["agentCloudId"], data["name"], data["size"], data["targetSize"], data["autoSize"], data["autoUpdate"],
            data["autoProvision"], data["isHosted"], data["scope"], from_ado_date_string(data["createdOn"]), created_by  # fmt: skip
        )

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", agent_pool_id: str) -> "AgentPool":
        return super()._get_by_url(
            ado_client,
            f"/_apis/distributedtask/pools/{agent_pool_id}?api-version=7.1-preview.1",
        )

    @classmethod
    def create(
        cls, ado_client: "AdoClient", name: str, agent_cloud_id: str | None = None, auto_provision: bool = True, auto_size: bool = True,
        auto_update: bool = True, is_hosted: bool = False, size: int = 1, target_size: int | None = None,  # fmt: skip
    ) -> "AgentPool":
        PAYLOAD = {
            "name": name, "agentCloudId": agent_cloud_id, "autoProvision": auto_provision, "autoSize": auto_size,
            "autoUpdate": auto_update, "isHosted": is_hosted, "size": size, "targetSize": target_size,
        }  # fmt: skip
        return super()._create(
            ado_client,
            "/_apis/distributedtask/pools?api-version=7.1-preview.1",
            payload=PAYLOAD,
        )

    # def update(self) -> None:
    #     # PATCH https://dev.azure.com/{organization}/_apis/distributedtask/pools/{poolId}?api-version=7.1-preview.1

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", agent_pool_id: str) -> None:
        return super()._delete_by_id(
            ado_client,
            f"/_apis/distributedtask/pools/{agent_pool_id}?api-version=7.1-preview.1",
            agent_pool_id,
        )

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["AgentPool"]:
        return super()._get_all(
            ado_client,
            "/_apis/distributedtask/pools?api-version=7.1-preview.1",
        )  # pyright: ignore[reportReturnType]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", agent_pool_name: str) -> "AgentPool | None":
        return cls._get_by_abstract_filter(ado_client, lambda agent_pool: agent_pool.name == agent_pool_name)
