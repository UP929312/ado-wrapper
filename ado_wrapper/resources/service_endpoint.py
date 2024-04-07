from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from ado_wrapper.client import AdoClient
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.resources.users import Member

ServiceEndpointEditableAttribute = Literal["name"]


# ====================================================================

@dataclass
class ServiceEndpoint(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/serviceendpoint/endpoints?view=azure-devops-rest-7.1"""
    service_endpoint_id: str = field(metadata={"is_id_field": True})
    name: str = field(metadata={"editable": True})
    type: str  # = field(metadata={"editable": True})
    url: str
    created_by: Member
    description: str  # = field(metadata={"editable": True})
    authorization: dict[str, Any]
    is_shared: bool
    is_outdated: bool
    is_ready: bool
    owner: str
    service_endpoint_project_references: list[dict[str, Any]]
    # _raw_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> ServiceEndpoint:
        member = Member(data["createdBy"]["displayName"], data["createdBy"]["uniqueName"], data["createdBy"]["id"])
        return cls(
            data["id"], data["name"], data["type"], data["url"], member, data.get("description", ""),
            data["authorization"], data["isShared"], data["isOutdated"], data["isReady"],
            data["owner"], data["serviceEndpointProjectReferences"], # data
        )

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str) -> "ServiceEndpoint":
        return super().get_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/serviceendpoint/endpoints/{repo_id}",
        )  # type: ignore[return-value]

    @classmethod
    def create(cls, ado_client: AdoClient, name: str, service_endpoint_type: str, url: str,  # type: ignore[override]
               username: str = "", password: str = "",  access_token: str = "") -> ServiceEndpoint:  # fmt: skip
        """Creates a service endpoint, pass in either username and password or access_token."""
        assert ((username and password) and not access_token) or (access_token and not (username and password)), "Either username and password or access_token must be passed in."
        payload = {
            "name": name,
            "type": service_endpoint_type,
            "url": url,
            "isShared": True,
            "isReady": True,
            "serviceEndpointProjectReferences": [{
                "projectReference": {"id": ado_client.ado_project_id},  # fmt: skip
                "name": name,
            }]
        }
        if username and password:
            payload["authorization"] = {"scheme": "UsernamePassword", "parameters": {"Username": username, "Password": password}}
        elif access_token:
            payload["authorization"] = {"parameters": {"AccessToken": access_token}, "scheme": "Token"}
        return super().create(
            ado_client,
            "/_apis/serviceendpoint/endpoints?api-version=7.1",
            payload,
        )  # type: ignore[return-value]

    def update(self, ado_client: AdoClient, attribute_name: ServiceEndpointEditableAttribute, attribute_value: Any) -> None:  # type: ignore[override]
        raise NotImplementedError
        # self._raw_data[attribute_name] = attribute_value
        # return super().update(
        #     ado_client, "put",
        #     f"_apis/serviceendpoint/endpoints/{self.service_endpoint_id}?api-version=7.1",
        #     attribute_name, attribute_value, self._raw_data,  # fmt: skip
        # )

    @classmethod
    def delete_by_id(cls, ado_client: AdoClient, service_endpoint_id: str) -> None:  # type: ignore[override]
        return super().delete_by_id(
            ado_client,
            f"/_apis/serviceendpoint/endpoints/{service_endpoint_id}?projectIds={ado_client.ado_project_id}&api-version=7.1",
            service_endpoint_id,
        )

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["ServiceEndpoint"]:  # type: ignore[override]
        return super().get_all(
            ado_client,
            f"/{ado_client.ado_project}/_apis/serviceendpoint/endpoints?api-version=7.1",
        )  # type: ignore[return-value]

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    def delete(self, ado_client: AdoClient) -> None:
        return self.delete_by_id(ado_client, self.service_endpoint_id)

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, name: str) -> ServiceEndpoint:
        return super().get_by_id(
            ado_client,
            f"/{ado_client.ado_project}/_apis/serviceendpoint/endpoints?endpointNames={name}&api-version=7.1",
        )  # type: ignore[return-value]
