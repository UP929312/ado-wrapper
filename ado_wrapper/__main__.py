import argparse

from ado_wrapper.client import AdoClient
from ado_wrapper.utils import ResourceType, get_internal_field_names, get_resource_variables


def main() -> None:  # pylint: disable=too-many-branches, too-many-statements
    ALL_RESOURCES = get_resource_variables()

    parser = argparse.ArgumentParser(
        prog="AdoWrapper", description="A tool to manage Azure DevOps resources and interface with the ADO API", usage=""
    )

    parser.add_argument("--ado-org", dest="ado_org_name", required=False)
    parser.add_argument("--ado-project", dest="ado_project", required=False)
    parser.add_argument("--email", dest="email", required=False)
    parser.add_argument("--token", dest="token", required=False)
    parser.add_argument("--creds_file", dest="creds_file", required=False)

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
    parser.add_argument(
        "--purge-state", "--wipe-state-", help="Deletes everything in the state file", action="store_true", default=False, dest="purge_state"  # fmt: skip
    )
    parser.add_argument("--state-file", help="The name of the state file to use", type=str, default="main.state", dest="state_file")
    args = parser.parse_args()

    if args.email is None and args.token is None and args.ado_org_name is None and args.ado_project is None and args.creds_file is None:
        raise ValueError("You must provide either --email and --token or --creds_file")

    if args.email is not None and args.token is not None and args.ado_org_name is not None and args.ado_project is not None:
        ado_client = AdoClient(args.email, args.token, args.ado_org_name, args.ado_project, state_file_name=args.state_file)
    elif args.creds_file:
        with open(args.creds_file, encoding="utf-8") as f:
            creds = f.read().split("\n")
            ado_client = AdoClient(creds[0], creds[1], creds[2], creds[3], state_file_name=args.state_file)

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
                        instance.update(ado_client, internal_attribute_name, attribute_value)  # type: ignore[attr-defined]
                        print(f"____The {resource_type}'s `{internal_attribute_name}` value has been updated to {attribute_value}")
                    internal_state["resources"][resource_type][resource_id] = instance.to_json()
        ado_client.state_manager.write_state_file(internal_state)


if __name__ == "__main__":
    main()
