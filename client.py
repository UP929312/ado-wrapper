import argparse
import json
from pathlib import Path
from typing import Literal, Any, TypedDict

from requests.auth import HTTPBasicAuth

from utils import DeletionFailed, get_resource_variables, ResourceType


ActionType = Literal["created", "updated"]
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

        from resources.projects import Project
        self.ado_project_id: str = Project.get_by_name(self, self.ado_project).project_id  # type: ignore[union-attr]

        # If they have a state file, and it doesn't exist:
        if self.state_file_name is not None and not Path(self.state_file_name).exists():
            self.wipe_state()  # Will automatically create the file

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
            return None
        all_states = self.get_all_states()
        all_states["created"][resource_type] = {k: v for k, v in all_states["created"][resource_type].items() if k != resource_id}
        return self.write_state_file(all_states)

    # =======================================================================================================

    def delete_resource(self, resource_type: ResourceType, resource_id: str) -> None:
        all_resource_classes = get_resource_variables()
        class_reference = [value for key, value in all_resource_classes.items() if key == resource_type][0]
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
        all_resource_classes = get_resource_variables()
        class_reference = [value for key, value in all_resource_classes.items() if key == resource_type][0]
        data = class_reference.get_by_id(self, resource_id).to_json()
        self.add_resource_to_state(resource_type, resource_id, data)

    def wipe_state(self) -> None:
        if self.state_file_name is None:
            return
        ALL_RESOURCE_STRINGS = get_resource_variables().keys()
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            json.dump(
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
    ALL_RESOURCES = get_resource_variables()

    parser = argparse.ArgumentParser(prog="ADO-API", description="A tool to manage Azure DevOps resources and interface with the ADO API")
    parser.add_argument("--delete-everything", help="Delete every resource in state & ADO", action="store_true", dest="delete_everything")
    parser.add_argument(
        "--delete-resource-type", help="Delete every resource of a specific type in state & ADO", type=str, dest="delete_resource_type", choices=ALL_RESOURCES.keys(),  # fmt: skip
    )
    parser.add_argument("--refresh-state-on-startup", help="Decided whether to refresh state when ran", action="store_true", dest="refresh_state_on_startup", default=True)
    args = parser.parse_args()
    from secret import email, ado_access_token, ado_org, ado_project

    ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)  #  state_file_name="main.json"

    if args.delete_everything:
        for resource_type in ado_client.get_all_states()["created"]:
            for resource_id in ado_client.get_all_states()["created"][resource_type]:
                ado_client.delete_resource(resource_type, resource_id)
        print("[ADO-API] Successfully deleted every resource in state")
    if args.delete_resource_type is not None:
        resource_type: ResourceType = args.delete_resource_type  # type: ignore[no-redef]
        for resource_id in ado_client.get_all_states()["created"][resource_type]:
            ado_client.delete_resource(resource_type, resource_id)
    if args.refresh_state_on_startup:
        all_states = ado_client.get_all_states()
        for resource_type in all_states["created"]:
            for resource_id in all_states["created"][resource_type]:
                instance = ALL_RESOURCES[resource_type].get_by_id(ado_client, resource_id)
                if instance.to_json() != all_states["created"][resource_type][resource_id]:
                    print("[ADO-API] Resource has been updated in ADO, updating state file")
                    all_states["created"][resource_type][resource_id] = instance.to_json()
        ado_client.write_state_file(all_states)

    # ado_client.wipe_state()
    # ado_client.add_resource_to_state("Repo", "12345", {"name": "test-repo"})
    # ado_client.remove_resource_from_state("Repo", "12345")
