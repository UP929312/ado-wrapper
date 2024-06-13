from typing import TYPE_CHECKING, Any

from ado_wrapper.utils import extract_id

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient
    from ado_wrapper.state_managed_abc import StateManagedResource

UNKNOWN_UNTIL_APPLY = "Unknown until apply"


class PlannedStateManagedResource:
    @staticmethod
    def get_plan_resource(class_name: str) -> "StateManagedResource":
        from ado_wrapper.plan_resources.mapping import get_resource_variables_plans

        return get_resource_variables_plans()["Plan" + class_name]  # type: ignore[no-any-return]

    @staticmethod
    def create(
        class_: type["StateManagedResource"], ado_client: "AdoClient", url: str, payload: dict[str, Any] | None = None
    ) -> "PlannedStateManagedResource":
        plan_resource = PlannedStateManagedResource.get_plan_resource(class_.__name__)
        resource_object = plan_resource.create(ado_client, url, payload)  # type: ignore[attr-defined]
        ado_client.state_manager.add_resource_to_state("Plan" + class_.__name__, extract_id(resource_object), resource_object.to_json())  # type: ignore[arg-type]
        return plan_resource.create(ado_client, url, payload)  # type: ignore[no-any-return, attr-defined]

    @staticmethod
    def update(
        class_: "StateManagedResource", ado_client: "AdoClient", url: str, attribute_name: str, attribute_value: Any, params: dict[str, Any]
    ) -> None:
        pass
        # plan_resource = PlannedStateManagedResource.get_plan_resource(class_.__name__)  # type: ignore[attr-defined]
        # resource_object = plan_resource.get_by_id(ado_client, extract_id(url))
        # resource_object.update(ado_client, url, attribute_name, attribute_value, params)

        # ado_client.state_manager.add_resource_to_state("Plan" + class_.__name__, extract_id(resource_object), resource_object.to_json())
