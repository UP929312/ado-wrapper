from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from datetime import datetime

import requests

from utils import get_resource_variables, extract_id, ResourceAlreadyExists, DeletionFailed, ResourceNotFound

if TYPE_CHECKING:
    from client import AdoClient


def recursively_convert_to_json(attribute_name: str, attribute_value: Any) -> tuple[str, Any]:
    if type(attribute_value) in get_resource_variables().values():
        class_name = str(type(attribute_value)).rsplit(".", maxsplit=1)[-1].removesuffix("'>")
        return attribute_name + "::" + class_name, attribute_value.to_json()
    if isinstance(attribute_value, dict):
        # print("In To JSON, it's a dict:", attribute_name, attribute_value)
        return attribute_name, {key: recursively_convert_to_json("", value)[1] for key, value in attribute_value.items()}
    if isinstance(attribute_value, list):
        return attribute_name, [recursively_convert_to_json(attribute_name, value) for value in attribute_value]
    if isinstance(attribute_value, datetime):
        return attribute_name + "::datetime", attribute_value.isoformat()
    return attribute_name, str(attribute_value)


def recursively_convert_from_json(dictionary: dict[str, Any]) -> Any:
    data_copy = dict(dictionary.items())
    for key, value in dictionary.items():
        if isinstance(key, str) and "::" in key and key.split("::")[-1] != "datetime":
            instance_name, class_type = key.split("::")
            class_ = [x for x in get_resource_variables().values() if x.__name__ == class_type][0]
            del data_copy[key]
            data_copy[instance_name] = class_.from_json(value)
        elif isinstance(key, str) and key.endswith("::datetime"):
            del data_copy[key]
            data_copy[key.split("::")[0]] = datetime.fromisoformat(value)
    return data_copy


# ==========================================================================================


@dataclass
class StateManagedResource(ABC):
    @classmethod
    @abstractmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "StateManagedResource":
        raise NotImplementedError

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "StateManagedResource":
        return cls(**recursively_convert_from_json(data))

    def to_json(self) -> dict[str, Any]:
        attribute_names = [field_obj.name for field_obj in fields(self)]
        attribute_values = [getattr(self, field_obj.name) for field_obj in fields(self)]
        combined = zip(attribute_names, attribute_values)
        return dict(recursively_convert_to_json(attribute_name, attribute_value) for attribute_name, attribute_value in combined)


    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", url: str) -> "StateManagedResource":
        request = requests.get(url, auth=ado_client.auth)
        if request.status_code == 404:
            raise ResourceNotFound(f"No {cls.__name__} found with that identifier!")
        return cls.from_request_payload(request.json())

    @classmethod
    def create(cls, ado_client: "AdoClient", url: str, payload: dict[str, Any] | None=None) -> "StateManagedResource":
        request = requests.post(url, json=payload if payload is not None else {}, auth=ado_client.auth)  # Create a brand new dict
        if request.status_code == 401:
            raise PermissionError(f"You do not have permission to create this {cls.__name__}!")
        if request.status_code == 409:
            raise ResourceAlreadyExists(f"The {cls.__name__} with that identifier already exist!")
        resource = cls.from_request_payload(request.json())
        ado_client.add_resource_to_state(cls.__name__, extract_id(resource), resource.to_json())  # type: ignore[arg-type]
        return resource

    @classmethod
    def delete_by_id(cls, ado_client: "AdoClient", url: str, resource_id: str) -> None:
        request = requests.delete(url, auth=ado_client.auth)
        if request.status_code != 204:
            raise DeletionFailed(f"Error deleting that {cls.__name__} ({resource_id}): {request.text}")
        ado_client.remove_resource_from_state(cls.__name__, resource_id)  # type: ignore[arg-type]

    def update(self, ado_client: "AdoClient", attribute_name: str, attribute_value: Any) -> None:
        raise NotImplementedError
