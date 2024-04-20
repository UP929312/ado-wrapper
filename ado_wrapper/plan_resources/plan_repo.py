from typing import TYPE_CHECKING, Any

from ado_wrapper.resources.repo import Repo

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

UNKNOWN_UNTIL_APPLY = "Unknown until apply"
BYPASS_CHECK = True


class PlanRepo:
    def get_by_id(self, ado_client: "AdoClient", repo_id: str) -> Repo:
        state_copy = ado_client.state_manager.load_state()["resources"][self.__class__.__name__].get(repo_id)  # type: ignore
        if state_copy:
            return Repo.from_json(state_copy)  # type: ignore[return-value]
        return Repo.get_by_id(ado_client, repo_id)

    @staticmethod
    def create(ado_client: "AdoClient", _: str, payload: dict[str, Any]) -> Repo:
        name = payload["name"]
        if not BYPASS_CHECK and Repo.get_by_name(ado_client, name):
            raise ValueError(f"Repo {name} already exists")
        return Repo(UNKNOWN_UNTIL_APPLY, name)

    def update(self, ado_client: "AdoClient", url: str, attribute_name: str, attribute_value: Any, payload: dict[str, Any]) -> Repo:
        return ""  # type: ignore[return-value]
