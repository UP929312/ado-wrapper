from requests.auth import HTTPBasicAuth

from typing import Literal, Any, TypedDict
import json
import sys
from pathlib import Path


def get_resource_variables() -> list[str]:
    from branches import Branch
    from builds import Build, BuildDefinition
    from commits import Commit
    from members import Member
    from pull_requests import PullRequest
    from release import Release, ReleaseDefinition
    from repository import Repo
    from teams import Team

    ALL_RESOURCE_CLASSES = [Branch, Build, BuildDefinition, Commit, Member, PullRequest, Release, ReleaseDefinition, Repo, Team]
    return [resource.__name__ for resource in ALL_RESOURCE_CLASSES]


ActionType = Literal["created", "updated"]
ResourceType = Literal[
    "Branch", "Build", "BuildDefinition", "Commit", "Member", "PullRequest", "Release", "ReleaseDefinition", "Repo", "Team"
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

    @property
    def is_storing_state(self) -> bool:
        return self.state_file_name is not None

    def get_all_states(self) -> StateFileType:
        with open(self.state_file_name, "r", encoding="utf-8") as state_file:  # type: ignore[this-will-never-run-raw]
            return json.load(state_file)

    def write_state_file(self, state_data: StateFileType) -> None:
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:  # type: ignore[this-will-never-run-raw]
            return json.dump(state_data, state_file, ensure_ascii=False, indent=4)

    # =======================================================================================================

    def add_resource_to_state(self, resource_id: str, resource_type: ResourceType) -> None:
        if not self.is_storing_state:
            print("[ADO-API] Not storing state, so not adding resource to state")
            return None
        all_states = self.get_all_states()
        if resource_id in all_states["created"][resource_type]:
            self.remove_resource_from_state(resource_id, resource_type)
        all_states["created"][resource_type] |= {resource_id: resource_type}
        return self.write_state_file(all_states)

    def remove_resource_from_state(self, resource_id: str, resource_type: ResourceType) -> None:
        if not self.is_storing_state:
            return None
        all_states = self.get_all_states()
        if resource_id in all_states["created"][resource_type]:
            del all_states["created"][resource_type][resource_id]
        return self.write_state_file(all_states)

    # =======================================================================================================

    def wipe_state(self) -> None:
        if not self.is_storing_state:
            return None
        ALL_RESOURCE_STRINGS = get_resource_variables()
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:  # type: ignore[this-will-never-run-raw]
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
    ALL_RESOURCE_STRINGS = get_resource_variables()
    if len(sys.argv) == 2 and sys.argv[1] == "--delete-everything":
        ado_client = AdoClient("", "", "", "")
        for resource_type in ado_client.get_all_states()["created"]:
            for resource_id in ado_client.get_all_states()["created"][resource_type]:
                ado_client.remove_resource_from_state(resource_id, resource_type)
        print("[ADO-API] Successfully deleted every resource in state")
    if len(sys.argv) == 3 and sys.argv[1] == "--delete-resource-type":
        ado_client = AdoClient("", "", "", "")
        resource_type: ResourceType = sys.argv[2]  # type: ignore[assignment]
        if resource_type not in ALL_RESOURCE_STRINGS:
            print(f"[ADO-API] {resource_type} is not a valid resource type")
            sys.exit(1)
        for resource_id in ado_client.get_all_states()["created"][resource_type]:
            ado_client.remove_resource_from_state(resource_id, resource_type)

    ado_client = AdoClient("", "", "", "", state_file_name="main.json")
    # ado_client.wipe_state()
    ado_client.add_resource_to_state("12345", "Repo")
    # ado_client.remove_resource_from_state("12345", "Repo")
