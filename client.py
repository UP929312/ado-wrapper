from typing import Literal, Any, TypedDict
import json
import sys
from pathlib import Path

from requests.auth import HTTPBasicAuth

from state_managed_abc import StateManagedResource
from utils import DeletionFailed


def get_resource_variables() -> tuple[list[str], list[type["StateManagedResource"]]]:  # We do this to avoid circular imports
    from branches import Branch
    from builds import Build, BuildDefinition
    from commits import Commit
    from users import AdoUser
    from pull_requests import PullRequest
    from release import Release, ReleaseDefinition
    from repository import Repo
    from teams import Team

    ALL_RESOURCE_CLASSES = [Branch, Build, BuildDefinition, Commit, AdoUser, PullRequest, Release, ReleaseDefinition, Repo, Team]
    return [resource.__name__ for resource in ALL_RESOURCE_CLASSES], ALL_RESOURCE_CLASSES


ActionType = Literal["created", "updated"]
ResourceType = Literal[
    "Branch", "Build", "BuildDefinition", "Commit", "AdoUser", "PullRequest", "Release", "ReleaseDefinition", "Repo", "Team"
]
StateFileEntryType = dict[str, Any]


class StateFileType(TypedDict):
    created: dict[ResourceType, StateFileEntryType]
    updated: dict[ResourceType, dict[str, tuple[Any, Any]]]


STATE_FILE_VERSION = 1


class AdoClient:
    def __init__(self, ado_email: str, ado_pat: str, ado_org: str, ado_project: str, state_file_name: str | None = "main.state") -> None:
        self.auth = HTTPBasicAuth(ado_email, ado_pat)
        self.ado_org = ado_org
        self.ado_project = ado_project

        self.state_file_name = state_file_name

        # If they have a state file, and it doesn't exist:
        if self.state_file_name is not None and not Path(self.state_file_name).exists():
            with open(self.state_file_name, "w", encoding="utf-8") as state_file:
                state_file.write("")
            self.wipe_state()

    def get_all_states(self) -> StateFileType:
        assert self.state_file_name is not None
        with open(self.state_file_name, "r", encoding="utf-8") as state_file:
            return json.load(state_file)  # type: ignore[no-any-return]

    def write_state_file(self, state_data: StateFileType) -> None:
        assert self.state_file_name is not None
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            json.dump(state_data, state_file, ensure_ascii=False, indent=4)

    # =======================================================================================================

    def add_resource_to_state(self, resource_type: ResourceType, resource_id: str, resource_data: dict[str, Any]) -> None:
        if self.state_file_name is None:
            print("[ADO-API] Not storing state, so not adding resource to state")
            return None
        all_states = self.get_all_states()
        if resource_id in all_states["created"][resource_type]:
            self.remove_resource_from_state(resource_type, resource_id)
        all_states["created"][resource_type] |= {resource_id: resource_data}
        return self.write_state_file(all_states)

    def remove_resource_from_state(self, resource_type: ResourceType, resource_id: str) -> None:
        if self.state_file_name is None:
            print("[ADO-API] Not storing state, so not removing resource to state")
            return
        all_states = self.get_all_states()
        all_states["created"][resource_type] = {k: v for k, v in all_states["created"][resource_type].items() if k != resource_id}
        return self.write_state_file(all_states)

    # =======================================================================================================

    def delete_resource(self, resource_type: ResourceType, resource_id: str) -> None:
        _, all_resource_classes = get_resource_variables()
        class_reference = [x for x in all_resource_classes if x.__name__ == resource_type][0]
        class_reference.delete_by_id(self, resource_id)
        self.remove_resource_from_state(resource_type, resource_id)

    def delete_all_resources(self, resource_type_filter: ResourceType | None = None) -> None:
        all_resources = (
            self.get_all_states()["created"]
            if resource_type_filter is None
            else {resource_type_filter: self.get_all_states()["created"][resource_type_filter]}
        )
        for resource_type, resources in all_resources.items():
            for resource_id in resources:
                try:
                    self.delete_resource(resource_type, resource_id)  # pyright: ignore[reportArgumentType]
                except DeletionFailed as e:
                    print(f"[ADO-API] Error deleting {resource_type} {resource_id}: {e}")

    def import_into_state(self, resource_type: ResourceType, resource_id: str) -> None:
        _, all_resource_classes = get_resource_variables()
        class_reference = [x for x in all_resource_classes if x.__name__ == resource_type][0]
        data = class_reference.get_by_id(self, resource_id).to_json()
        self.add_resource_to_state(resource_type, resource_id, data)

    def wipe_state(self) -> None:
        if self.state_file_name is None:
            return
        ALL_RESOURCE_STRINGS, _ = get_resource_variables()
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            return json.dump(
                {
                    "state_file_version": STATE_FILE_VERSION,
                    "created": {resource: {} for resource in ALL_RESOURCE_STRINGS},
                    "updated": {resource: {} for resource in ALL_RESOURCE_STRINGS},
                },
                state_file,
            )

    # def get_state(self, resource_id: str, resource_type: ResourceType) -> ActionType | None:
    #     all_states = self.get_all_states()
    #     if resource_id in all_states["created"][resource_type]:
    #         return "created"
    #     return None


if __name__ == "__main__":
    from secret import email, ado_access_token, ado_org, ado_project

    ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)  #  state_file_name="main.json"

    ALL_RESOURCE_STRINGS, _ = get_resource_variables()

    if len(sys.argv) == 2 and sys.argv[1] == "--delete-everything":
        for resource_type in ado_client.get_all_states()["created"]:
            for resource_id in ado_client.get_all_states()["created"][resource_type]:
                ado_client.delete_resource(resource_type, resource_id)
        print("[ADO-API] Successfully deleted every resource in state")
    if len(sys.argv) == 3 and sys.argv[1] == "--delete-resource-type":
        resource_type: ResourceType = sys.argv[2]  # type: ignore[no-redef]
        if resource_type not in ALL_RESOURCE_STRINGS:
            print(f"[ADO-API] {resource_type} is not a valid resource type")
            sys.exit(1)
        for resource_id in ado_client.get_all_states()["created"][resource_type]:
            ado_client.delete_resource(resource_type, resource_id)

    # ado_client.wipe_state()
    # ado_client.add_resource_to_state("Repo", "12345", {"name": "test-repo"})
    # ado_client.remove_resource_from_state("Repo", "12345")
