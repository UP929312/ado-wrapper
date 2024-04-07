from typing import Any, TYPE_CHECKING, Literal
from dataclasses import dataclass, fields
from datetime import datetime

import requests

from ado_wrapper.utils import (
    get_resource_variables, extract_id, get_internal_field_names,
    ResourceAlreadyExists, DeletionFailed, ResourceNotFound, UpdateFailed,  # fmt: skip
)

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


def recursively_convert_to_json(attribute_name: str, attribute_value: Any) -> tuple[str, Any]:
    if isinstance(attribute_value, dict):
        return attribute_name, {key: recursively_convert_to_json("", value)[1] for key, value in attribute_value.items()}
    if isinstance(attribute_value, list):
        return attribute_name, [recursively_convert_to_json(attribute_name, value)[1] for value in attribute_value]
    if isinstance(attribute_value, datetime):
        return f"{attribute_name}::datetime", attribute_value.isoformat()
    if type(attribute_value) in get_resource_variables().values():
        class_name = str(type(attribute_value)).rsplit(".", maxsplit=1)[-1].removesuffix("'>")
        return attribute_name + "::" + class_name, attribute_value.to_json()
    return attribute_name, str(attribute_value)


def recursively_convert_from_json(dictionary: dict[str, Any]) -> Any:
    data_copy = dict(dictionary.items())  # Deep copy
    for key, value in dictionary.items():
        if isinstance(key, str) and "::" in key and key.split("::")[-1] != "datetime":
            instance_name, class_type = key.split("::")
            class_ = get_resource_variables()[class_type]
            del data_copy[key]
            data_copy[instance_name] = class_.from_json(value)
        elif isinstance(key, str) and key.endswith("::datetime"):
            del data_copy[key]
            data_copy[key.split("::")[0]] = datetime.fromisoformat(value)
    return data_copy


# ==========================================================================================


@dataclass
class StateManagedResource:
    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "StateManagedResource":
        raise NotImplementedError

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "StateManagedResource":
        return cls(**recursively_convert_from_json(data))

    def to_json(self) -> dict[str, Any]:
        attribute_names = [field_obj.name for field_obj in fields(self)]
        attribute_values = [getattr(self, field_obj.name) for field_obj in fields(self)]
        combined = zip(attribute_names, attribute_values)
        return dict(recursively_convert_to_json(attribute_name, attribute_value) for attribute_name, attribute_value in combined) ####

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", url: str) -> "StateManagedResource":
        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org}{url}"
        request = requests.get(url, auth=ado_client.auth)
        if request.status_code == 404:
            raise ResourceNotFound(f"No {cls.__name__} found with that identifier!")
        if request.status_code >= 300:
            raise ValueError(f"Error getting {cls.__name__} by id: {request.text}")
        if "value" in request.json():
            return cls.from_request_payload(request.json()["value"][0])
        return cls.from_request_payload(request.json())

    @classmethod
    def create(cls, ado_client: "AdoClient", url: str, payload: dict[str, Any] | None = None) -> "StateManagedResource":
        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org}" + url
        request = requests.post(url, json=payload or {}, auth=ado_client.auth)  # Create a brand new dict
        if request.status_code == 401:
            raise PermissionError(f"You do not have permission to create this {cls.__name__}!")
        if request.status_code == 409:
            raise ResourceAlreadyExists(f"The {cls.__name__} with that identifier already exist!")
        resource = cls.from_request_payload(request.json())
        ado_client.state_manager.add_resource_to_state(cls.__name__, extract_id(resource), resource.to_json())  # type: ignore[arg-type]
        return resource

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", url: str, resource_id: str) -> None:
        """Deletes an object by its id. The id is passed so it can be removed from state"""
        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org}{url}"
        request = requests.delete(url, auth=ado_client.auth)
        if request.status_code != 204:
            if request.status_code == 404:
                print("[ADO_WRAPPER] Resource not found, probably already deleted, removing from state")
            else:
                raise DeletionFailed(f"[ADO_WRAPPER] Error deleting {cls.__name__} ({resource_id}): {request.json()['message']}")
        ado_client.state_manager.remove_resource_from_state(cls.__name__, resource_id)  # type: ignore[arg-type]

    def update(self, ado_client: "AdoClient", update_action: Literal["put", "patch"], url: str,  # pylint: disable=too-many-arguments
               attribute_name: str, attribute_value: Any, params: dict[str, Any]) -> None:  # fmt: skip
        """The params should be a dictionary which will be combined with the internal name and value of the attribute to be updated."""
        interal_names = get_internal_field_names(self.__class__)
        if attribute_name not in get_internal_field_names(self.__class__):
            raise ValueError(f"The attribute `{attribute_name}` is not editable!  Editable attributes are: {list(interal_names.keys())}")
        params |= {interal_names[attribute_name]: attribute_value}

        func = requests.put if update_action == "put" else requests.patch
        # request = requests.request(update_action, url, json=params, auth=ado_client.auth)
        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org}{url}"
        request = func(url, json=params, auth=ado_client.auth)
        if request.status_code != 200:
            raise UpdateFailed(
                f"Failed to update {self.__class__.__name__} with id {extract_id(self)} and attribute {attribute_name} to {attribute_value}. \nReason:\n{request.text}"
            )
        setattr(self, attribute_name, attribute_value)
        ado_client.state_manager.update_resource_in_state(self.__class__.__name__, extract_id(self), self.to_json())  # type: ignore[arg-type]

    @classmethod
    def get_all(cls, ado_client: "AdoClient", url: str) -> list["StateManagedResource"]:
        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org}{url}"
        request = requests.get(url, auth=ado_client.auth)
        if request.status_code >= 300:
            raise ValueError(f"Error getting all {cls.__name__}: {request.text}")
        return [cls.from_request_payload(resource) for resource in request.json()["value"]]
