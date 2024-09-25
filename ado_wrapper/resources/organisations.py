from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ado_wrapper.state_managed_abc import StateManagedResource

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


@dataclass
class Organisation(StateManagedResource):
    organisation_id: str
    name: str

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Organisation":
        return cls(data["id"], data["name"])

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["Organisation"]:
        # This is sketchy hierarchy stuff, so we can't use super()
        org_id_request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery?api-version=5.0-preview.1",
            json={"contributionIds": ["ms.vss-features.my-organizations-data-provider"]},
        ).json()["dataProviders"]["ms.vss-features.my-organizations-data-provider"]["organizations"]
        return [cls.from_request_payload(x) for x in org_id_request]

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", organisation_id: str) -> "Organisation | None":
        return cls._get_by_abstract_filter(ado_client, lambda x: x.organisation_id == organisation_id)

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", organisation_name: str) -> "Organisation | None":
        return cls._get_by_abstract_filter(ado_client, lambda organisation: organisation.name == organisation_name)
