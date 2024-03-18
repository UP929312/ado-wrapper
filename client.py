import argparse
import json
from pathlib import Path
from typing import Literal, Any, TypedDict
import requests

from requests.auth import HTTPBasicAuth

from utils import DeletionFailed, get_resource_variables, get_internal_field_names
from attribute_types import ResourceType


ActionType = Literal["created"]
StateFileEntryType = dict[str, Any]


class StateFileType(TypedDict):
    created: dict[ResourceType, StateFileEntryType]
    updated: dict[ResourceType, dict[str, tuple[Any, Any]]]


STATE_FILE_VERSION = "1.1"


class AdoClient:
    def __init__(  # pylint: disable=too-many-arguments
        self, ado_email: str, ado_pat: str, ado_org: str, ado_project: str, state_file_name: str | None = "main.state"  # fmt: skip
    ) -> None:
        self.auth = HTTPBasicAuth(ado_email, ado_pat)
        self.ado_org = ado_org
        self.ado_project = ado_project
        self.state_file_name = state_file_name

        # Verify Token is working (helps with setup for first time users):
        request = requests.get(f"https://dev.azure.com/{self.ado_org}/_apis/projects?api-version=6.0", auth=self.auth)
        assert request.status_code == 200, f"Failed to authenticate with ADO: {request.text}"

        from resources.projects import Project  # Stop circular import
        self.ado_project_id: str = Project.get_by_name(self, self.ado_project).project_id  # type: ignore[union-attr]

        # data = requests.get(f"https://dev.azure.com/{self.ado_org}/_apis/tokenadministration/tokens?api-version=6.0", auth=self.auth)
        # print(data.status_code)

        # If they have a state file, and it doesn't exist:
        if self.state_file_name is not None and not Path(self.state_file_name).exists():
            self.wipe_state()  # Will automatically create the file

    def get_all_states(self) -> StateFileType:
        assert self.state_file_name is not None
        with open(self.state_file_name, "r", encoding="utf-8") as state_file:
            try:
                return json.load(state_file)  # type: ignore[no-any-return]
            except json.JSONDecodeError as exc:
                raise json.JSONDecodeError("State file is not valid JSON", exc.doc, exc.pos)

    def write_state_file(self, state_data: StateFileType) -> None:
        assert self.state_file_name is not None
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            json.dump(state_data, state_file, indent=4)

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

    def update_resource_in_state(self, resource_type: ResourceType, resource_id: str, updated_data: dict[str, Any]) -> None:
        if self.state_file_name is None:
            print("[ADO-API] Not storing state, so not updating resource in state")
            return None
        all_states = self.get_all_states()
        all_states["created"][resource_type][resource_id] = updated_data
        return self.write_state_file(all_states)

    # =======================================================================================================

    def delete_resource(self, resource_type: ResourceType, resource_id: str) -> None:
        all_resource_classes = get_resource_variables()
        class_reference = [value for key, value in all_resource_classes.items() if key == resource_type][0]
        try:
            class_reference.delete_by_id(self, resource_id)  # type: ignore[call-arg]
        except DeletionFailed:
            print(f"[ADO-API] Error deleting {resource_type} {resource_id} from ADO")
        except (NotImplementedError, TypeError):
            print(f"[ADO-API] Cannot {resource_type} {resource_id} from state or real space, please delete this manually or using code.")
        else:
            print(f"[ADO-API] Deleted {resource_type} {resource_id} from ADO")
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
        all_resource_names = get_resource_variables().keys()
        with open(self.state_file_name, "w", encoding="utf-8") as state_file:
            json.dump(
                {
                    "state_file_version": STATE_FILE_VERSION,
                    "created": {resource: {} for resource in all_resource_names},
                    # "updated": {resource: {} for resource in all_resource_names},
                },
                state_file,
            )

    def generate_in_memory_state(self) -> StateFileType:
        """This method goes through every resource in state and updates it to the latest version in real world space"""
        all_states = ado_client.get_all_states()
        for resource_type in all_states["created"]:
            for resource_id in all_states["created"][resource_type]:
                instance = ALL_RESOURCES[resource_type].get_by_id(ado_client, resource_id)
                if instance.to_json() != all_states["created"][resource_type][resource_id]:
                    all_states["created"][resource_type][resource_id] = instance.to_json()
        return all_states


if __name__ == "__main__":
    ALL_RESOURCES = get_resource_variables()

    parser = argparse.ArgumentParser(
        prog="ADO-API", description="A tool to manage Azure DevOps resources and interface with the ADO API", usage=""
    )
    delete_group = parser.add_mutually_exclusive_group()
    delete_group.add_argument(
        "--delete-everything", help="Delete every resource in state and the real ADO resources", action="store_true", dest="delete_everything"  # fmt: skip
    )
    delete_group.add_argument(
        "--delete-resource-type", help="Delete every resource of a specific type in state & ADO", type=str, dest="delete_resource_type", choices=ALL_RESOURCES.keys(),  # fmt: skip
    )
    update_group = parser.add_mutually_exclusive_group()
    update_group.add_argument(
        "--refresh-state-on-startup", help="Decides whether to refresh state when ran", action="store_true", dest="refresh_state_on_startup", default=False,  # fmt: skip
    )
    update_group.add_argument(
        "--refresh-resources-on-startup", help="Decides whether to update ADO resources (from state)", action="store_true", dest="refresh_resources_on_startup", default=False,  # fmt: skip
    )
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--plan", help="Runs a plan for the resources, rather than making them", action="store_true", default=False, dest="plan"
    )
    action_group.add_argument("--apply", help="Applies the plan to the resources", action="store_true", default=False, dest="apply")
    parser.add_argument(
        "--purge-state", help="Deletes everything in the state file", action="store_true", default=False, dest="purge_state"
    )
    args = parser.parse_args()
    assert not (args.delete_everything and args.delete_resource_type is not None)
    if args.refresh_resources_on_startup:
        args.refresh_state_on_startup = False

    from secret import email, ado_access_token, ado_org, ado_project

    ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)  #  state_file_name="main.json"

    if args.purge_state:
        # Deletes everything in the state file
        print("[ADO-API] Purging state")
        ado_client.wipe_state()

    if args.delete_everything:
        # Deletes ADO resources and entries in the state file
        print("[ADO-API] Deleting every resource in state and the real ADO resources")
        for resource_type in ado_client.get_all_states()["created"]:
            for resource_id in ado_client.get_all_states()["created"][resource_type]:
                ado_client.delete_resource(resource_type, resource_id)
        print("[ADO-API] Finishing deleting resources in state")

    if args.delete_resource_type is not None:
        # Deletes ADO resources and entries in the state file of a specific type
        resource_type: ResourceType = args.delete_resource_type  # type: ignore[no-redef]
        for resource_id in ado_client.get_all_states()["created"][resource_type]:
            ado_client.delete_resource(resource_type, resource_id)
        print(f"[ADO-API] Successfully deleted every resource of type {resource_type} in state")

    if args.refresh_state_on_startup:
        # Updates the state file to the latest version of every resource in ADO space
        up_to_date_states = ado_client.generate_in_memory_state()
        ado_client.write_state_file(up_to_date_states)
        print("[ADO-API] Successfully updated state to latest version of ADO resources")

    if args.refresh_resources_on_startup:
        # Updates every resource in ADO space to the version found in state"""
        print("[ADO-API] Updating real world resources with data from state:")
        up_to_date_state = ado_client.generate_in_memory_state()
        internal_state = ado_client.get_all_states()
        for resource_type in up_to_date_state["created"]:  # For each class type (Repo, Build)
            for resource_id in up_to_date_state["created"][resource_type]:  # For each resource
                state_data = internal_state["created"][resource_type][resource_id]  # The data in state
                real_data = up_to_date_state["created"][resource_type][resource_id]  # The data in real world space
                if state_data != real_data:
                    print(f"[ADO-API] Updating ADO resource - {resource_type} ({resource_id}) to version found in state:")
                    instance = ALL_RESOURCES[resource_type].from_json(real_data)  # Create an instance from the real world data
                    internal_attribute_names = get_internal_field_names(instance.__class__)  # Mapping of internal->python
                    differences = {
                        internal_attribute_names[key]: value
                        for key, value in state_data.items()
                        if state_data[key] != real_data[key] and key in internal_attribute_names
                    }
                    for internal_attribute_name, attribute_value in differences.items():
                        instance.update(ado_client, internal_attribute_name, attribute_value)  # type: ignore[arg-type, call-arg]
                        print(f"____The {resource_type}'s `{internal_attribute_name}` value has been updated to {attribute_value}")
                    internal_state["created"][resource_type][resource_id] = instance.to_json()
        ado_client.write_state_file(internal_state)

    if args.plan:
        print("[ADO-API] Running plan for resources:")
        # Plan for resources
