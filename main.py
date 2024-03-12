from requests.auth import HTTPBasicAuth

from typing import Literal, Any, TypedDict
import json
import sys

ActionType = Literal["created", "updated"]
ResourceType = str
ResourceId = str
StateFileEntryType = dict[ResourceId, Any]

class StateFileType(TypedDict):
    created: dict[ResourceType, StateFileEntryType]
    updated: dict[ResourceType, dict[ResourceId, tuple[StateFileEntryType, StateFileEntryType]]]

class AdoClient:
    def __init__(self, ado_email: str, ado_pat: str, ado_org: str, ado_project: str, state_file_name: str | None="main.state") -> None:
        self.auth = HTTPBasicAuth(ado_email, ado_pat)
        self.ado_org = ado_org
        self.ado_project = ado_project
        self.state_file_name = state_file_name

        if self.state_file_name is not None:
            with open(self.state_file_name, "w", encoding="utf-8") as state_file:
                json.dump({"created": {}, "updated": {}}, state_file)

    @property
    def is_storing_state(self) -> bool:
        return self.state_file_name is not None

    def get_all_states(self) -> StateFileType:
        with open(self.state_file_name, "r", encoding="utf-8") as state_file:  # type: ignore[this-will-never-run-raw]
            return json.load(state_file)

    def write_state_file(self, state_data: StateFileType) -> None:
        if self.is_storing_state:
            return None
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:  # type: ignore[this-will-never-run-raw]
            return json.dump(state_data, state_file, ensure_ascii=False, indent=4)

    # =======================================================================================================

    def add_resource_to_state(self, resource_id: str, resource_type: str, action_type: ActionType) -> None:
        if self.is_storing_state:
            return None
        all_states = self.get_all_states()
        if resource_type not in all_states[action_type]:
            all_states[action_type][resource_type] = {}
        if resource_id in all_states[action_type][resource_type]:
            return None
        all_states[action_type][resource_type] |= {resource_id: resource_type}
        return self.write_state_file(all_states)

    def remove_resource_from_state(self, resource_id: str, resource_type: str) -> None:
        if self.is_storing_state:
            return None
        all_states = self.get_all_states()
        if resource_type not in resource_id in all_states["created"]:
            return None
        if resource_id in all_states["created"][resource_type]:
            del all_states["created"][resource_type][resource_id]
        return self.write_state_file(all_states)

    # =======================================================================================================

    def get_state(self, resource_id: str, resource_type: str) -> ActionType | None:
        all_states = self.get_all_states()
        if resource_type not in all_states["created"]:
            return None
        if resource_id in all_states["created"][resource_type]:
            return "created"
        return None

    def wipe_state(self) -> None:
        if self.state_file_name is None:
            return None
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            return json.dump({"created": {}, "updated": {}}, state_file)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--delete-everything":
        ado_client = AdoClient("", "", "", "")
        for resource_type in ado_client.get_all_states()["created"]:
            for resource_id in ado_client.get_all_states()["created"][resource_type]:
                ado_client.remove_resource_from_state(resource_id, resource_type)
        print("[ADO-API] Successfully deleted every resource in state")
    # ado_client = AdoClient("", "", "", "")
    # ado_client.wipe_state()
    # ado_client.add_resource_to_state("12345", "Repo", "created")
    # ado_client.remove_resource_from_state("12345", "Repo")