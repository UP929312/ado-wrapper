import argparse

from ado_wrapper.attribute_types import ResourceType
from ado_wrapper.client import AdoClient
from ado_wrapper.utils import get_internal_field_names, get_resource_variables


def main() -> None:
    ALL_RESOURCES = get_resource_variables()

    parser = argparse.ArgumentParser(
        prog="AdoWrapper", description="A tool to manage Azure DevOps resources and interface with the ADO API", usage=""
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
        "--refresh-internal-state", help="Decides whether to refresh state when ran", action="store_true", dest="refresh_internal_state", default=False,  # fmt: skip
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
        "--purge-state", "--wipe-state-", help="Deletes everything in the state file", action="store_true", default=False, dest="purge_state"
    )
    parser.add_argument("--state-file", help="The name of the state file to use", type=str, default="main.state", dest="state_file")
    args = parser.parse_args()

    from secret import email, ado_access_token, ado_org, ado_project
    ado_client = AdoClient(email, ado_access_token, ado_org, ado_project, state_file_name=args.state_file)

    if args.purge_state:
        # Deletes everything in the state file
        print("[ADO_WRAPPER] Purging state")
        ado_client.state_manager.wipe_state()

    if args.delete_everything:
        # Deletes ADO resources and entries in the state file
        print("[ADO_WRAPPER] Deleting every resource in state and the real ADO resources")
        ado_client.state_manager.delete_all_resources()
        print("[ADO_WRAPPER] Finishing deleting resources in state")

    if args.delete_resource_type is not None:
        # Deletes ADO resources and entries in the state file of a specific type
        resource_type: ResourceType = args.delete_resource_type
        ado_client.state_manager.delete_all_resources(resource_type_filter=resource_type)
        print(f"[ADO_WRAPPER] Successfully deleted every resource of type {resource_type} in state")

    if args.refresh_internal_state:
        # Updates the state file to the latest version of every resource in ADO space
        up_to_date_states = ado_client.state_manager.generate_in_memory_state()
        ado_client.state_manager.write_state_file(up_to_date_states)
        print("[ADO_WRAPPER] Successfully updated state to latest version of ADO resources")

    if args.refresh_resources_on_startup:
        # Updates every resource in ADO space to the version found in state"""
        print("[ADO_WRAPPER] Updating real world resources with data from state:")
        up_to_date_state = ado_client.state_manager.generate_in_memory_state()
        internal_state = ado_client.state_manager.load_state()
        for resource_type in up_to_date_state["resources"]:  # For each class type (Repo, Build)
            for resource_id in up_to_date_state["resources"][resource_type]:  # For each resource
                state_data = internal_state["resources"][resource_type][resource_id]  # The data in state
                real_data = up_to_date_state["resources"][resource_type][resource_id]  # The data in real world space
                if state_data != real_data:
                    print(f"[ADO_WRAPPER] Updating ADO resource - {resource_type} ({resource_id}) to version found in state:")
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
                    internal_state["resources"][resource_type][resource_id] = instance.to_json()
        ado_client.state_manager.write_state_file(internal_state)

    if args.plan:
        print("[ADO_WRAPPER] Running plan for resources:")
        # Plan for resources

if __name__ == "__main__":
    main()