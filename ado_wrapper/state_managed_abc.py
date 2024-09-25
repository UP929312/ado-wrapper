import json
from dataclasses import dataclass, fields
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Literal, Type, TypeVar

from ado_wrapper.errors import DeletionFailed, ResourceAlreadyExists, ResourceNotFound, UnknownError, UpdateFailed, InvalidPermissionsError  # fmt: skip
from ado_wrapper.utils import extract_id, get_internal_field_names, get_resource_variables

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

T = TypeVar("T", bound="StateManagedResource")


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
    def from_request_payload(cls: Type[T], data: dict[str, Any]) -> T:
        raise NotImplementedError

    @classmethod
    def from_json(cls: Type[T], data: dict[str, Any]) -> T:
        return cls(**recursively_convert_from_json(data))

    def to_json(self) -> dict[str, Any]:
        attribute_names = [field_obj.name for field_obj in fields(self)]
        attribute_values = [getattr(self, field_obj.name) for field_obj in fields(self)]
        combined = zip(attribute_names, attribute_values)
        return dict(recursively_convert_to_json(attribute_name, attribute_value) for attribute_name, attribute_value in combined)

    @classmethod
    def _get_by_id(cls: Type[T], ado_client: "AdoClient", resource_id: str) -> T:
        raise NotImplementedError

    @classmethod
    def _get_by_url(cls: Type[T], ado_client: "AdoClient", url: str) -> T:
        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org_name}{url}"
        request = ado_client.session.get(url)
        if request.status_code == 401:
            raise InvalidPermissionsError(f"You do not have permission to fetch {cls.__name__}(s)!")
        if request.status_code == 404:
            raise ResourceNotFound(f"No {cls.__name__} found with that identifier!")
        if request.status_code >= 300:
            raise ValueError(f"Error getting {cls.__name__} by id: {request.text}")
        if request.text == "":
            raise UnknownError(f"Error fetching {cls.__name__}, unknown error.")
        if "value" in request.json():
            return cls.from_request_payload(request.json()["value"][0])
        return cls.from_request_payload(request.json())

    @classmethod
    def _create(cls: Type[T], ado_client: "AdoClient", url: str, payload: dict[str, Any] | None = None, refetch: bool = False) -> T:
        """When creating, often the response doesn't contain all the data, refetching does a .get_by_id() after creation."""
        # If it already exists:
        # if cls.get_by_id(ado_client, extract_unique_name(payload)):
        #     raise ResourceAlreadyExists(f"The {cls.__name__} with that identifier already exist!")
        #     <update the resource>
        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org_name}{url}"
        request = ado_client.session.post(url, json=payload or {})  # Create a brand new dict
        if request.status_code >= 300:
            if request.status_code in [401, 403]:
                raise InvalidPermissionsError(f"You do not have permission to create this {cls.__name__}! {request.text}")
            if request.status_code == 409:
                raise ResourceAlreadyExists(f"The {cls.__name__} with that identifier already exist!")
            try:
                if request.status_code == 400 and "already exists" in request.json().get("message", ""):
                    raise ResourceAlreadyExists(f"The {cls.__name__} with that identifier already exist!")
            except json.JSONDecodeError:
                pass
            raise ValueError(f"Error creating {cls.__name__}: {request.status_code} - {request.text}")
        resource = cls.from_request_payload(request.json())
        if refetch:
            resource = cls.get_by_id(ado_client, extract_id(resource))  # type: ignore[attr-defined] # pylint: disable=no-member
        ado_client.state_manager.add_resource_to_state(cls.__name__, extract_id(resource), resource.to_json())  # type: ignore[arg-type]
        return resource  # [return-value]

    @classmethod
    def _delete_by_id(cls: Type[T], ado_client: "AdoClient", url: str, resource_id: str) -> None:
        """Deletes an object by its id. The id is passed so it can be removed from state"""
        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org_name}{url}"
        request = ado_client.session.delete(url)
        if request.status_code != 204:
            if request.status_code == 404:
                if not ado_client.suppress_warnings:
                    print("[ADO_WRAPPER] Resource not found, probably already deleted, removing from state")
            else:
                if "message" in request.json():
                    raise DeletionFailed(f"[ADO_WRAPPER] Error deleting {cls.__name__} ({resource_id}): {request.json()['message']}")
                raise DeletionFailed(f"[ADO_WRAPPER] Error deleting {cls.__name__} ({resource_id}): {request.text}")
        ado_client.state_manager.remove_resource_from_state(cls.__name__, resource_id)  # type: ignore[arg-type]

    def _update(self, ado_client: "AdoClient", update_action: Literal["put", "patch"], url: str,  # pylint: disable=too-many-arguments
                attribute_name: str, attribute_value: Any, params: dict[str, Any]) -> None:  # fmt: skip
        """The params should be a dictionary which will be combined with the internal name and value of the attribute to be updated."""
        interal_names = get_internal_field_names(self.__class__)
        if attribute_name not in get_internal_field_names(self.__class__):
            raise ValueError(f"The attribute `{attribute_name}` is not editable!  Editable attributes are: {list(interal_names.keys())}")
        params |= {interal_names[attribute_name]: attribute_value}

        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org_name}{url}"
        request = ado_client.session.request(update_action, url, json=params)
        if request.status_code != 200:
            raise UpdateFailed(
                f"Failed to update {self.__class__.__name__} with id {extract_id(self)} and attribute {attribute_name} to {attribute_value}. \nReason:\n{request.text}"
            )
        setattr(self, attribute_name, attribute_value)
        ado_client.state_manager.update_resource_in_state(self.__class__.__name__, extract_id(self), self.to_json())  # type: ignore[arg-type]

    def delete(self, ado_client: "AdoClient") -> None:
        return self.delete_by_id(ado_client, extract_id(self))  # type: ignore[attr-defined, no-any-return]  # pylint: disable=no-value-for-parameter, no-member

    @classmethod
    def _get_all(cls: Type[T], ado_client: "AdoClient", url: str) -> list[T]:
        if not url.startswith("https://"):
            url = f"https://dev.azure.com/{ado_client.ado_org_name}{url}"
        request = ado_client.session.get(url)
        if request.status_code == 401:
            raise InvalidPermissionsError(f"You do not have permission to get all {cls.__name__}(s)!")
        if request.status_code >= 300:
            raise ValueError(f"Error getting all {cls.__name__}: {request.status_code}, error={request.text}")
        return [cls.from_request_payload(resource) for resource in request.json()["value"]]

    @classmethod
    def _get_by_abstract_filter(cls: Type[T], ado_client: "AdoClient", func: Callable[[T], bool]) -> T | None:
        """Used internally for getting resources by a filter function. The function should return True if the resource is the one you want."""
        resources = cls.get_all(ado_client)  # type: ignore[attr-defined]  # pylint: disable=no-value-for-parameter, no-member
        for resource in resources:
            if func(resource):
                return resource  # type: ignore[no-any-return]
        return None

    # def set_lifecycle_policy(self, ado_client: "AdoClient", policy: Literal["prevent_destroy", "ignore_changes"]) -> None:
    #     self.life_cycle_policy = policy  # TODO
    #     ado_client.state_manager.update_lifecycle_policy(self.__class__.__name__, extract_id(self), policy)  # type: ignore[arg-type]

    # def __enter__(self) -> "StateManagedResource":
    #     return self

    # def __exit__(self, *_: Any) -> None:
    #     self.delete(self.ado_client)
